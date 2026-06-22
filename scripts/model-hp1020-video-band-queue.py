#!/usr/bin/env python3
"""Model HP 1020 video band queue/list helper.

This is offline analysis only. It records how `0x10013f34` consumes the
descriptor ring selected by video state `+0xdc`, writes raw-band registers, and
advances the queue/list side of the video transfer path.
"""

from __future__ import annotations

import argparse
import json
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
ELF_PATH = ROOT_DIR / "analysis/sihp1020.elf"
SOURCE = ROOT_DIR / "analysis/zjs-parser-boundary/decompiled/10013f34_hp1020_video_band_queue_or_list_candidate.c"
OUT_JSON = ROOT_DIR / "analysis/hardware-boundary/video-band-queue.json"
OUT_MD = ROOT_DIR / "analysis/hardware-boundary/video-band-queue.md"

LITERALS = {
    "high_bit": 0x10005E34,
    "high_bit_clear_mask": 0x1000628C,
    "video_state_base": 0x10006770,
    "ring_descriptor_base": 0x100067BC,
    "callback_ptr_cell": 0x100067C4,
    "dual_block_mode_ptr": 0x100067C8,
    "raw_band_a_pointer": 0x100067CC,
    "raw_band_b_pointer": 0x100067D0,
    "raw_band_a_flags": 0x100067D4,
    "block_a_status": 0x100067C0,
    "block_b_status": 0x100067D8,
    "raw_band_b_flags": 0x100067DC,
}

CHECKS = [
    ("descriptor_base_dc", "PTR_DAT_100067bc + *(int *)(PTR_DAT_10006770 + 0xdc) * 0xc"),
    ("loop_requires_ready_0x100", "while (((uVar8 & 0x100) != 0"),
    ("loop_stops_at_e0_unless_final", "(*(int *)(puVar2 + 0xdc) + 1U & 3) != *(uint *)(puVar2 + 0xe0)"),
    ("source_pointer_from_slot", "iVar7 = *(int *)(puVar2 + *(int *)(puVar2 + 0xdc) * 4)"),
    ("callback_enabled_by_c0", "if (*(int *)(puVar2 + 0xc0) != 0)"),
    ("callback_pointer_present", "if (*(int *)puVar4 != 0)"),
    ("final_padding_zero", "if (*(int *)(puVar6 + 4) != 0)"),
    ("high_bit_set_on_last_units", "*(uint *)(puVar2 + *(int *)(puVar2 + 0xdc) * 4 + 0x10) + DAT_10005e34"),
    ("callback_call", "(**(code **)puVar4)"),
    ("dual_block_branch", "if (*(int *)PTR_DAT_100067c8 == 1)"),
    ("raw_band_a_pointer_write", "*DAT_100067cc = iVar7"),
    ("raw_band_b_pointer_write", "*piVar5 = iVar7 + *(int *)(puVar2 + 0xbc)"),
    ("raw_band_a_ready_wait", "while ((uVar8 & 0x100) == 0)"),
    ("raw_band_a_flags_write", "*DAT_100067d4 = uVar9"),
    ("raw_band_b_flags_write", "*DAT_100067dc = uVar9 | (uint)(*(int *)(puVar2 + 0xec) != 0) << 0x19"),
    ("single_block_flags_write", "*DAT_100067d4 = uVar8 | (uint)(*(int *)(puVar6 + 4) != 0) << 0x18"),
    ("remaining_d4_decrement", "*(int *)(puVar2 + 0xd4) = *(int *)(puVar2 + 0xd4) - *(int *)(puVar6 + 8)"),
    ("dc_advance_mod4", "uVar9 = *(int *)(puVar2 + 0xdc) + 1U & 3"),
]


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

    def read_u32(self, addr: int) -> int:
        for p_offset, p_vaddr, p_filesz in self.load_segments:
            if p_vaddr <= addr <= p_vaddr + p_filesz - 4:
                off = p_offset + (addr - p_vaddr)
                return struct.unpack(">I", self.data[off : off + 4])[0]
        raise ValueError(f"address 0x{addr:08x} is not file-backed")


def fmt32(value: int) -> str:
    return f"0x{value:08x}"


def literal_values(elf: ElfImage) -> dict[str, str]:
    return {name: fmt32(elf.read_u32(addr)) for name, addr in LITERALS.items()}


def descriptor_fields() -> list[dict[str, str]]:
    return [
        {"offset": "+0x00", "field": "descriptor busy/owned flag", "meaning": "set by 0x10014244 helper; cleared by IRQ band-done path"},
        {"offset": "+0x04", "field": "final/secondary flag", "meaning": "allows one more queue iteration when next +0xdc would meet +0xe0; contributes raw-band flag bit 0x18"},
        {"offset": "+0x08", "field": "band units/count", "meaning": "fed to callback, raw-band flag encoding, remaining +0xd4 decrement, and dual-block half-count"},
    ]


def queue_sequences(literals: dict[str, str]) -> list[dict[str, Any]]:
    return [
        {
            "name": "queue_loop_gate",
            "steps": [
                "select descriptor at `0x1002efe0 + (video_state +0xdc) * 0x0c`",
                "continue only while block A status bit 0x100 is set",
                "stop when the next +0xdc slot would equal +0xe0 unless the current descriptor final flag is nonzero",
            ],
            "registers": [literals["block_a_status"]],
        },
        {
            "name": "optional_callback_and_padding",
            "steps": [
                "when state +0xc0 and callback pointer are nonzero, optionally zero padding after the descriptor band",
                "if remaining +0xd4 is within the current descriptor size, set high bit 0x80000000 on the per-slot control word",
                "call the callback with adjusted pointer, per-slot control word, and descriptor units masked to a multiple of four",
                "after callback, use the per-slot control word as the raw-band pointer/control source",
            ],
            "registers": [],
        },
        {
            "name": "raw_band_single_block_write",
            "steps": [
                "write descriptor pointer/control to 0xb1000008",
                "encode descriptor units using the firmware helper and state +0xc4",
                "OR descriptor final flag into bit 0x18 and write 0xb100000c",
            ],
            "registers": [literals["raw_band_a_pointer"], literals["raw_band_a_flags"]],
        },
        {
            "name": "raw_band_dual_block_write",
            "steps": [
                "write A pointer/control to 0xb1000008",
                "write B pointer/control as A plus state +0xbc to 0xb1000108",
                "encode half descriptor units for both blocks",
                "wait for A and B status bit 0x100 before writing flags",
                "OR descriptor final flag into A bit 0x18 and state +0xec into B bit 0x19",
            ],
            "registers": [
                literals["raw_band_a_pointer"],
                literals["raw_band_b_pointer"],
                literals["raw_band_a_flags"],
                literals["raw_band_b_flags"],
            ],
        },
        {
            "name": "advance_queue_side",
            "steps": [
                "subtract descriptor units from state +0xd4",
                "advance state +0xdc modulo 4",
                "load the next 0x0c-byte descriptor record and re-read block A status",
            ],
            "registers": [literals["block_a_status"]],
        },
    ]


def scenario_model() -> list[dict[str, Any]]:
    rows = []
    for dc, e0, final_flag in [(0, 2, 0), (0, 1, 0), (0, 1, 1), (3, 0, 0)]:
        next_slot = (dc + 1) & 3
        can_continue = next_slot != e0 or final_flag != 0
        rows.append(
            {
                "name": f"dc_{dc}_e0_{e0}_final_{final_flag}",
                "dc": dc,
                "e0": e0,
                "descriptor_final_flag": final_flag,
                "next_slot": next_slot,
                "loop_decision": "queue_descriptor" if can_continue else "stop_before_e0_collision",
                "dc_after": next_slot if can_continue else dc,
            }
        )
    return rows


def evidence_checks(source: str) -> list[dict[str, str]]:
    return [
        {
            "name": name,
            "status": "present" if needle in source else "missing",
            "needle": needle,
        }
        for name, needle in CHECKS
    ]


def build_report(elf_path: Path) -> dict[str, Any]:
    elf = ElfImage.load(elf_path)
    source = SOURCE.read_text(errors="replace")
    literals = literal_values(elf)
    checks = evidence_checks(source)
    missing = [check for check in checks if check["status"] != "present"]
    return {
        "summary": "Video band queue/list helper model for raw-band register feed and +0xdc ownership.",
        "status": "pass" if not missing else "fail",
        "literal_values": literals,
        "descriptor_fields": descriptor_fields(),
        "queue_sequences": queue_sequences(literals),
        "loop_scenarios": scenario_model(),
        "checks": checks,
        "open_firmware_implication": [
            "This helper is the queue/list side paired with IRQ band-done refill; it explains how +0xdc advances.",
            "The helper will not blindly overrun +0xe0 unless the current descriptor carries its final/secondary flag.",
            "It is also a raw-band MMIO writer, so it remains unsafe for early custom firmware until live video timing is proven.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 Video Band Queue/List Model",
        "",
        "This is a generated offline model. It does not contact the printer.",
        "",
        "## Result",
        "",
        f"- status: `{report['status']}`",
        "- scope: `0x10013f34` descriptor queue/list helper and raw-band register feed",
        "",
        "## Key Literal Values",
        "",
        "| Name | Value |",
        "|---|---:|",
    ]
    for name, value in report["literal_values"].items():
        lines.append(f"| `{name}` | `{value}` |")

    lines.extend(["", "## Descriptor Fields", "", "| Offset | Field | Meaning |", "|---:|---|---|"])
    for item in report["descriptor_fields"]:
        lines.append(f"| `{item['offset']}` | {item['field']} | {item['meaning']} |")

    lines.extend(["", "## Queue Sequences", ""])
    for sequence in report["queue_sequences"]:
        lines.extend(
            [
                f"### `{sequence['name']}`",
                "",
                "- registers: "
                + (", ".join(f"`{register}`" for register in sequence["registers"]) if sequence["registers"] else "-"),
                "",
            ]
        )
        for index, step in enumerate(sequence["steps"], 1):
            lines.append(f"{index}. {step}")
        lines.append("")

    lines.extend(["## Loop Scenarios", "", "| Scenario | +0xdc | +0xe0 | Final flag | Next slot | Decision | +0xdc after |", "|---|---:|---:|---:|---:|---|---:|"])
    for item in report["loop_scenarios"]:
        lines.append(
            f"| `{item['name']}` | `{item['dc']}` | `{item['e0']}` | `{item['descriptor_final_flag']}` | "
            f"`{item['next_slot']}` | `{item['loop_decision']}` | `{item['dc_after']}` |"
        )

    lines.extend(["", "## Evidence Checks", "", "| Check | Status | Needle |", "|---|---|---|"])
    for check in report["checks"]:
        needle = check["needle"].replace("|", "\\|")
        lines.append(f"| `{check['name']}` | `{check['status']}` | `{needle}` |")

    lines.extend(["", "## Open Firmware Meaning", ""])
    for item in report["open_firmware_implication"]:
        lines.append(f"- {item}")
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
    args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.markdown_output.write_text(render_markdown(report) + "\n")
    print(
        f"status={report['status']} checks={len(report['checks'])} "
        f"sequences={len(report['queue_sequences'])} scenarios={len(report['loop_scenarios'])}"
    )
    print(args.markdown_output)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
