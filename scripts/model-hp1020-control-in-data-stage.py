#!/usr/bin/env python3
"""Model the HP 1020 stock USB endpoint-0 control-IN data stage."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
ELF_PATH = ROOT_DIR / "analysis/sihp1020.elf"
OUT_JSON = ROOT_DIR / "analysis/usb-path/control-in-data-stage.json"
OUT_MD = ROOT_DIR / "analysis/usb-path/control-in-data-stage.md"


@dataclass(frozen=True)
class ElfImage:
    data: bytes
    load_segments: list[tuple[int, int, int]]

    @classmethod
    def load(cls, path: Path) -> "ElfImage":
        data = path.read_bytes()
        if data[:4] != b"\x7fELF" or data[5] != 2:
            raise ValueError(f"{path} is not a big-endian ELF")
        phoff = struct.unpack(">I", data[28:32])[0]
        phentsize = struct.unpack(">H", data[42:44])[0]
        phnum = struct.unpack(">H", data[44:46])[0]
        load_segments = []
        for index in range(phnum):
            off = phoff + index * phentsize
            p_type, p_offset, p_vaddr, _p_paddr, p_filesz, _p_memsz, _p_flags, _p_align = struct.unpack(
                ">IIIIIIII", data[off : off + 32]
            )
            if p_type == 1:
                load_segments.append((p_offset, p_vaddr, p_filesz))
        return cls(data, load_segments)

    def read_bytes(self, addr: int, size: int) -> bytes:
        for p_offset, p_vaddr, p_filesz in self.load_segments:
            if p_vaddr <= addr <= p_vaddr + p_filesz - size:
                offset = p_offset + (addr - p_vaddr)
                return self.data[offset : offset + size]
        raise ValueError(f"address 0x{addr:08x} is not file-backed")

    def read_u32(self, addr: int) -> int:
        return struct.unpack(">I", self.read_bytes(addr, 4))[0]


def fmt32(value: int) -> str:
    return f"0x{value:08x}"


def resolve_constants(elf_path: Path) -> dict[str, int]:
    elf = ElfImage.load(elf_path)
    constants = {
        "transfer_state_base": elf.read_u32(0x10005E1C),
        "completion_event_flags": elf.read_u32(0x10005E18),
        "descriptor_flag": elf.read_u32(0x10005E80),
        "descriptor_base_ptr_cell": elf.read_u32(0x10005E98),
        "staging_buffer_ptr_cell": elf.read_u32(0x10005E94),
        "descriptor_base": elf.read_u32(elf.read_u32(0x10005E98)),
        "staging_buffer": elf.read_u32(elf.read_u32(0x10005E94)),
        "usb_main_control": elf.read_u32(0x10005E90),
        "chunk_size_register": elf.read_u32(0x10005E9C),
        "descriptor_submit_register": elf.read_u32(0x10005EA0),
        "initial_descriptor_pointer_addend": elf.read_u32(0x10005E34),
    }
    constants["descriptor_submit_value"] = constants["descriptor_base"]
    constants["initial_descriptor_submit_value"] = (
        constants["descriptor_base"] + constants["initial_descriptor_pointer_addend"]
    ) & 0xffffffff
    return constants


def pointer_evidence(elf_path: Path) -> dict[str, Any]:
    elf = ElfImage.load(elf_path)
    # Contiguous slices include each load-to-store dataflow. They distinguish
    # active submission from the separate HOST_BUSY initialization sequence.
    anchors = (
        (0x10008D02, "88c019f467dcf00c02009890", "active zero-length pointer unchanged"),
        (0x10008F11, "19f3e38870c7ef0c02009890", "active nonzero pointer unchanged"),
        (0x100092AA, "88b019f2e21bf2fca98819f2fe0c020098b0", "initial pointer plus literal modulo 2^32"),
    )
    records = []
    for address, expected, meaning in anchors:
        actual = elf.read_bytes(address, len(expected) // 2).hex()
        if actual != expected:
            raise ValueError(f"changed pointer dataflow at {address:#x}: {actual}")
        records.append({"address": fmt32(address), "bytes": actual, "meaning": meaning})
    return {
        "kind": "byte-anchored static dataflow, not original-code execution",
        "anchors": records,
        "active_operation": "supplied pointer unchanged",
        "initial_operation": "(supplied pointer + 0x80000000) modulo 2^32",
        "initial_descriptor_status": "0xc0000000",
        "physical_address_translation_established": False,
        "pointer_controls": [
            {"supplied": fmt32(pointer), "active": fmt32(pointer),
             "initial": fmt32((pointer + elf.read_u32(0x10005E34)) & 0xffffffff)}
            for pointer in (0x100226f0, 0x900226f0)
        ],
    }


def descriptor_word(length: int, *, flagged: bool, flag: int) -> int:
    return length | (flag if flagged else 0)


def model_batches(response_len: int, *, chunk_size: int, descriptor_base: int, staging_base: int, flag: int) -> list[dict[str, Any]]:
    remaining = response_len
    batches = []

    while True:
        descriptors = []
        index = 0
        if remaining == 0:
            descriptors.append(
                {
                    "index": 0,
                    "byte_count": 0,
                    "control_word": descriptor_word(0, flagged=True, flag=flag),
                    "source_pointer": staging_base,
                    "next_descriptor": 0,
                    "flagged": True,
                }
            )
            remaining_after = 0
        else:
            while chunk_size < remaining:
                if index > 4:
                    break
                descriptors.append(
                    {
                        "index": index,
                        "byte_count": chunk_size,
                        "control_word": descriptor_word(chunk_size, flagged=False, flag=flag),
                        "source_pointer": staging_base + index * chunk_size,
                        "next_descriptor": descriptor_base + (index + 1) * 0x10,
                        "flagged": False,
                    }
                )
                remaining -= chunk_size
                index += 1

            if index == 5:
                descriptors[-1]["control_word"] = descriptor_word(
                    descriptors[-1]["byte_count"], flagged=True, flag=flag
                )
                descriptors[-1]["flagged"] = True
                remaining_after = remaining
            else:
                descriptors.append(
                    {
                        "index": index,
                        "byte_count": remaining,
                        "control_word": descriptor_word(remaining, flagged=True, flag=flag),
                        "source_pointer": staging_base + index * chunk_size,
                        "next_descriptor": 0,
                        "flagged": True,
                    }
                )
                remaining = 0
                remaining_after = 0

        batch = {
            "batch_index": len(batches),
            "descriptor_count": len(descriptors),
            "descriptors": descriptors,
            "descriptor_submit_pointer": descriptor_base,
            "control_kick_or_value": 0x108,
            "remaining_after_batch": remaining_after,
        }
        batches.append(batch)
        if remaining_after == 0:
            break
    return batches


def build_report(elf_path: Path) -> dict[str, Any]:
    constants = resolve_constants(elf_path)
    scenarios = []
    for response_len in (0, 1, 18, 32, 34, 38, 64, 65, 255, 320, 321):
        scenarios.append(
            {
                "response_len": response_len,
                "batches": model_batches(
                    response_len,
                    chunk_size=0x40,
                    descriptor_base=constants["descriptor_base"],
                    staging_base=constants["staging_buffer"],
                    flag=constants["descriptor_flag"],
                ),
            }
        )

    return {
        "summary": "Offline model of stock endpoint-0 control-IN transfer descriptor construction.",
        "source_function": "0x10008c24 hp1020_usb_control_tx_data_stage_candidate",
        "constants": {key: fmt32(value) for key, value in constants.items()},
        "pointer_dataflow": pointer_evidence(elf_path),
        "source_sha256": {
            "analysis/sihp1020.elf": hashlib.sha256(elf_path.read_bytes()).hexdigest(),
            "scripts/model-hp1020-control-in-data-stage.py": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
        "assumed_chunk_size_for_scenarios": "0x00000040",
        "evidence": [
            "analysis/usb-path/decompiled-neighbors/10008c24_hp1020_usb_control_tx_data_stage_candidate.c",
            "analysis/usb-path/internal-blocks.md",
            "analysis/usb-path-report.md",
        ],
        "algorithm": [
            "set 0xb3000000 bit 0x2 before staging the control-IN response",
            "copy response bytes into the staging buffer at 0x90022bd0; cache visibility is not established here",
            "build one to five 0x10-byte transfer descriptors at 0x900226f0",
            "descriptor word +0x00 is byte_count OR 0x08000000 on the final descriptor of each hardware kick",
            "descriptor word +0x08 is the source pointer into the staging buffer",
            "descriptor word +0x0c is the next descriptor pointer or zero",
            "write the unchanged active descriptor base through 0xb3000014, then OR 0xb3000000 with 0x108",
            "wait on the USB completion event flag and repeat if bytes remain",
        ],
        "scenarios": scenarios,
        "remaining_live_unknown": [
            "whether the open payload inherits initialized USB transfer-state RAM after ACL upload",
            "whether the control-IN completion event flag can be replaced with a safe polling loop",
            "which live register transition confirms the 0x108 kick completed without ThreadX",
        ],
    }


def render_descriptor(desc: dict[str, Any]) -> str:
    next_text = fmt32(desc["next_descriptor"]) if desc["next_descriptor"] else "0"
    return (
        f"`{desc['index']}` len `{desc['byte_count']}` word `{fmt32(desc['control_word'])}` "
        f"src `{fmt32(desc['source_pointer'])}` next `{next_text}`"
    )


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 Control-IN Data Stage Model",
        "",
        "This is an offline model of the stock USB endpoint-0 data sender. It does not contact the printer.",
        "",
        "## Key Result",
        "",
        "- This static model covers descriptor construction and submission intent, not controller acceptance or successful transfers.",
        "- The stock path uses a staging buffer, a 0x10-byte descriptor ring, a per-descriptor `0x08000000` flag, `0xb3000014` descriptor submission, and `0xb3000000 |= 0x108` transfer kick.",
        "- Active submissions preserve the supplied descriptor pointer. Separate initialization adds `0x80000000` modulo 32 bits; the former pointer-OR model was incorrect.",
        "- Cache/DMA behavior, real completion and settlement remain unproved.",
        "",
        "## Resolved Constants",
        "",
        "| Name | Value |",
        "|---|---:|",
    ]
    for key, value in report["constants"].items():
        lines.append(f"| `{key}` | `{value}` |")

    lines.extend(["", "## Pointer dataflow correction", "",
                  "Each contiguous byte slice is checked against the stock ELF. This is static evidence, not new stock execution.", ""])
    for anchor in report["pointer_dataflow"]["anchors"]:
        lines.append(f"- `{anchor['address']}` (`{anchor['bytes']}`): {anchor['meaning']}.")
    lines.extend(["", "The initialized descriptor has HOST_BUSY status `0xc0000000`. With the file-backed pointer, initialization wraps `0x900226f0` to `0x100226f0`; active submission stays `0x900226f0`. Neither operation establishes a physical alias or address translation rule.", "",
                  "| Supplied pointer | Active submission | Initialization ADD |", "|---|---|---|"])
    for row in report["pointer_dataflow"]["pointer_controls"]:
        lines.append(f"| `{row['supplied']}` | `{row['active']}` | `{row['initial']}` |")

    lines.extend(
        [
            "",
            "## Algorithm",
            "",
        ]
    )
    for item in report["algorithm"]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## Scenario Matrix",
            "",
            "Scenarios assume the normal 64-byte endpoint chunk value, matching the descriptor path's `0x40` setup writes.",
            "",
            "| Response bytes | Batches | Descriptor counts | Flagged descriptor words |",
            "|---:|---:|---|---|",
        ]
    )
    for scenario in report["scenarios"]:
        counts = ", ".join(str(batch["descriptor_count"]) for batch in scenario["batches"])
        flagged = []
        for batch in scenario["batches"]:
            for desc in batch["descriptors"]:
                if desc["flagged"]:
                    flagged.append(f"batch {batch['batch_index']} desc {desc['index']} `{fmt32(desc['control_word'])}`")
        lines.append(
            f"| `{scenario['response_len']}` | `{len(scenario['batches'])}` | `{counts}` | {', '.join(flagged)} |"
        )

    lines.extend(["", "## Descriptor Details", ""])
    for scenario in report["scenarios"]:
        if scenario["response_len"] not in (18, 38, 65, 321):
            continue
        lines.append(f"### Response `{scenario['response_len']}` bytes")
        lines.append("")
        for batch in scenario["batches"]:
            lines.append(
                f"- batch `{batch['batch_index']}`, remaining after batch `{batch['remaining_after_batch']}`:"
            )
            for desc in batch["descriptors"]:
                lines.append(f"  - {render_descriptor(desc)}")
        lines.append("")

    lines.extend(["## Remaining Live Unknowns", ""])
    for item in report["remaining_live_unknown"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def run_self_test() -> int:
    constants = resolve_constants(ELF_PATH)
    pointers = pointer_evidence(ELF_PATH)
    failures = []
    expected_pointers = [
        {"supplied": "0x100226f0", "active": "0x100226f0", "initial": "0x900226f0"},
        {"supplied": "0x900226f0", "active": "0x900226f0", "initial": "0x100226f0"},
    ]
    if pointers["pointer_controls"] != expected_pointers:
        failures.append({"pointer_controls": pointers["pointer_controls"]})
    expected = {
        0: (1, [1], [0x08000000]),
        18: (1, [1], [0x08000012]),
        38: (1, [1], [0x08000026]),
        65: (1, [2], [0x08000001]),
        321: (2, [5, 1], [0x08000040, 0x08000001]),
    }
    for response_len, (batch_count, descriptor_counts, flagged_words) in expected.items():
        batches = model_batches(
            response_len,
            chunk_size=0x40,
            descriptor_base=constants["descriptor_base"],
            staging_base=constants["staging_buffer"],
            flag=constants["descriptor_flag"],
        )
        actual_counts = [batch["descriptor_count"] for batch in batches]
        actual_flagged = [
            desc["control_word"]
            for batch in batches
            for desc in batch["descriptors"]
            if desc["flagged"]
        ]
        if len(batches) != batch_count or actual_counts != descriptor_counts or actual_flagged != flagged_words:
            failures.append(
                {
                    "response_len": response_len,
                    "expected": [batch_count, descriptor_counts, [fmt32(v) for v in flagged_words]],
                    "actual": [len(batches), actual_counts, [fmt32(v) for v in actual_flagged]],
                }
            )
    print(f"self_test_cases={len(expected) + len(expected_pointers)} failures={len(failures)}")
    if failures:
        print(json.dumps(failures, indent=2))
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--elf", type=Path, default=ELF_PATH)
    parser.add_argument("--json-output", type=Path, default=OUT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=OUT_MD)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return run_self_test()

    report = build_report(args.elf)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.markdown_output.write_text(render_markdown(report) + "\n")
    print(f"scenarios={len(report['scenarios'])} function={report['source_function'].split()[0]}")
    print(args.markdown_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
