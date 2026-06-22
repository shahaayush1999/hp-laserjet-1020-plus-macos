#!/usr/bin/env python3
"""Model the HP 1020 stock USB bulk receive handoff to the ZjStream parser."""

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
ELF_PATH = ROOT_DIR / "analysis/sihp1020.elf"
USB2_SOURCE = ROOT_DIR / "analysis/usb-path/decompiled-neighbors/10008ff0_hp1020_usb2_thread.c"
REGISTER_SOURCE = ROOT_DIR / "analysis/usb-path/decompiled-neighbors/10007c00_hp1020_usb_register_transfer_candidate.c"
ALLOC_SOURCE = ROOT_DIR / "analysis/usb-path/decompiled-neighbors/10008034_FUN_10008034.c"
PARSER_SOURCE = ROOT_DIR / "analysis/zjs-parser-boundary/decompiled/10009d34_hp1020_zjs_parser_entry_candidate.c"
OUT_JSON = ROOT_DIR / "analysis/usb-path/usb-bulk-receive-model.json"
OUT_MD = ROOT_DIR / "analysis/usb-path/usb-bulk-receive-model.md"


LITERALS = {
    "transfer_token_shift_word": 0x10005D98,
    "transfer_ring_index": 0x10005D9C,
    "transfer_ring_base": 0x10005DA0,
    "transfer_prepare_callback": 0x10005DD0,
    "transfer_callback_a": 0x10005DD4,
    "transfer_callback_b": 0x10005DD8,
    "pending_transfer_list": 0x10005E10,
    "completion_event_flags": 0x10005E18,
    "transfer_state": 0x10005E1C,
    "descriptor_pool_a": 0x10005E2C,
    "bulk_rx_size_word": 0x10005E38,
    "bulk_rx_token_word": 0x10005E44,
    "endpoint_config_word": 0x10005E50,
    "bulk_rx_done_flag": 0x10005E64,
    "descriptor_pool_b": 0x10005E98,
    "registered_callback_a": 0x10005EFC,
    "registered_callback_b": 0x10005F00,
    "bulk_rx_mask_word": 0x10005F04,
    "endpoint_ack_register": 0x10005F08,
    "usb2thread_event_bit": 0x10005F20,
    "usb2thread_descriptor_word0": 0x10005FC4,
    "usb2thread_name": 0x10005FD0,
    "parser_entry": 0x10005FDC,
    "zjs_magic": 0x10005FE0,
}


class ElfImage:
    def __init__(self, data: bytes, load_segments: list[tuple[int, int, int]]) -> None:
        self.data = data
        self.load_segments = load_segments

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

    def read_u32(self, addr: int) -> int:
        for p_offset, p_vaddr, p_filesz in self.load_segments:
            if p_vaddr <= addr <= p_vaddr + p_filesz - 4:
                off = p_offset + (addr - p_vaddr)
                return struct.unpack(">I", self.data[off : off + 4])[0]
        raise ValueError(f"address 0x{addr:08x} is not file-backed")


def fmt32(value: int) -> str:
    return f"0x{value:08x}"


def require_contains(source: str, needle: str, evidence: Path) -> dict[str, str]:
    return {
        "status": "present" if needle in source else "missing",
        "needle": needle,
        "evidence": str(evidence.relative_to(ROOT_DIR)),
    }


def build_report(elf_path: Path) -> dict[str, Any]:
    elf = ElfImage.load(elf_path)
    constants = {name: elf.read_u32(addr) for name, addr in LITERALS.items()}
    usb2 = USB2_SOURCE.read_text(errors="replace")
    register = REGISTER_SOURCE.read_text(errors="replace")
    alloc = ALLOC_SOURCE.read_text(errors="replace")
    parser = PARSER_SOURCE.read_text(errors="replace")

    descriptor_words = [elf.read_u32(0x10005FC4 + offset) for offset in range(0, 0x20, 4)]
    checks = [
        require_contains(usb2, "uStack_70 = 1;", USB2_SOURCE),
        require_contains(usb2, "puStack_68 = PTR_LAB_10005efc;", USB2_SOURCE),
        require_contains(usb2, "puStack_64 = PTR_LAB_10005f00;", USB2_SOURCE),
        require_contains(usb2, "uVar11 = hp1020_usb_register_transfer_candidate(&uStack_70);", USB2_SOURCE),
        require_contains(register, "puVar3 + iVar8 * 0x58", REGISTER_SOURCE),
        require_contains(register, "piVar6[1] = param_1[2];", REGISTER_SOURCE),
        require_contains(register, "piVar6[2] = param_1[3];", REGISTER_SOURCE),
        require_contains(register, "piVar6[0xb] = iVar5;", REGISTER_SOURCE),
        require_contains(alloc, "FUN_10013140(0x400,1)", ALLOC_SOURCE),
        require_contains(parser, "(**(code **)(param_1 + 0xc))", PARSER_SOURCE),
        require_contains(parser, "hp1020_queue_send_candidate(3,auStack_1d0)", PARSER_SOURCE),
    ]
    fail_count = sum(check["status"] != "present" for check in checks)
    return {
        "summary": "Static model of stock USB bulk receive registration and parser handoff.",
        "status": "pass" if fail_count == 0 else "fail",
        "constants": {name: fmt32(value) for name, value in constants.items()},
        "usb2thread_descriptor_words": [fmt32(value) for value in descriptor_words],
        "transfer_record": {
            "ring_base": fmt32(constants["transfer_ring_base"]),
            "ring_index_word": fmt32(constants["transfer_ring_index"]),
            "record_stride": "0x58",
            "buffer_allocation": "0x400 bytes",
            "registered_param_words": [
                {"word": 0, "value": "0x00000001", "record_offset": "+0x2c", "meaning": "transfer kind/endpoint selector candidate"},
                {"word": 1, "value": "0x00000000", "record_offset": "+0x38", "meaning": "flags/timeout candidate"},
                {
                    "word": 2,
                    "value": fmt32(constants["registered_callback_a"]),
                    "record_offset": "+0x04",
                    "meaning": "registered callback/function pointer A",
                },
                {
                    "word": 3,
                    "value": fmt32(constants["registered_callback_b"]),
                    "record_offset": "+0x08",
                    "meaning": "registered callback/function pointer B",
                },
                {"word": 4, "value": "0x00000000", "record_offset": "+0x18", "meaning": "state/argument slot candidate"},
                {"word": 5, "value": "0x00000001", "record_offset": "+0x54", "meaning": "enable/ownership candidate"},
            ],
            "default_callbacks_from_allocator": {
                "+0x14": fmt32(constants["transfer_prepare_callback"]),
                "+0x0c": fmt32(constants["transfer_callback_a"]),
                "+0x10": fmt32(constants["transfer_callback_b"]),
            },
        },
        "parser_handoff": {
            "usb2thread_descriptor": fmt32(0x10005FC4),
            "usb2thread_entry": fmt32(descriptor_words[1]),
            "parser_entry": fmt32(constants["parser_entry"]),
            "zjs_magic": fmt32(constants["zjs_magic"]),
            "parser_reads_via_param_0x0c_callback": True,
            "parser_sends_jobmgr_queue": 3,
        },
        "open_firmware_implication": [
            "The stock path separates USB transfer registration from ZjStream parsing through a callback table passed as parser param_1.",
            "An open firmware can keep the host-side ZjStream parser model, but still needs a bulk OUT receiver that can present a blocking/read callback at param_1+0x0c.",
            "The immediate software target after endpoint-0 proof is not video hardware; it is a small bulk-receive/read-callback shim that feeds the already-modeled ZjStream chunk loop.",
        ],
        "checks": checks,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 USB Bulk Receive Model",
        "",
        "This is an offline static model. It does not contact the printer.",
        "",
        "## Key Result",
        "",
        "- USB2Thread registers a transfer record through `0x10007c00` using a `0x58` byte record stride.",
        "- The helper allocator seeds a `0x400` byte receive buffer.",
        "- The task descriptor at `0x10005fc4` wires USB2Thread to parser entry `0x10009d34`.",
        "- The parser consumes bytes through a callback at `param_1 + 0x0c`, then sends JobMgr queue `3` messages.",
        "",
        "## Constants",
        "",
        "| Name | Value |",
        "|---|---:|",
    ]
    for name, value in report["constants"].items():
        lines.append(f"| `{name}` | `{value}` |")

    record = report["transfer_record"]
    lines.extend(
        [
            "",
            "## Transfer Record",
            "",
            f"- ring base: `{record['ring_base']}`",
            f"- ring index word: `{record['ring_index_word']}`",
            f"- record stride: `{record['record_stride']}`",
            f"- buffer allocation: `{record['buffer_allocation']}`",
            "",
            "| Param word | Value | Record offset | Meaning |",
            "|---:|---:|---:|---|",
        ]
    )
    for item in record["registered_param_words"]:
        lines.append(f"| `{item['word']}` | `{item['value']}` | `{item['record_offset']}` | {item['meaning']} |")

    handoff = report["parser_handoff"]
    lines.extend(
        [
            "",
            "## Parser Handoff",
            "",
            f"- USB2Thread descriptor: `{handoff['usb2thread_descriptor']}`",
            f"- USB2Thread entry: `{handoff['usb2thread_entry']}`",
            f"- parser entry: `{handoff['parser_entry']}`",
            f"- ZjStream magic pointer: `{handoff['zjs_magic']}`",
            f"- parser read callback slot: `param_1 + 0x0c`",
            f"- parser output queue: `{handoff['parser_sends_jobmgr_queue']}`",
            "",
            "## Open-Firmware Meaning",
            "",
        ]
    )
    for item in report["open_firmware_implication"]:
        lines.append(f"- {item}")

    lines.extend(["", "## Evidence Checks", "", f"- status: `{report['status']}`", "", "| Status | Evidence | Needle |", "|---|---|---|"])
    for check in report["checks"]:
        needle = check["needle"].replace("|", "\\|")
        lines.append(f"| `{check['status']}` | `{check['evidence']}` | `{needle}` |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--elf", type=Path, default=ELF_PATH)
    parser.add_argument("--json-output", type=Path, default=OUT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=OUT_MD)
    args = parser.parse_args()

    report = build_report(args.elf)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.markdown_output.write_text(render_markdown(report) + "\n")
    print(f"status={report['status']} checks={len(report['checks'])}")
    print(args.markdown_output)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
