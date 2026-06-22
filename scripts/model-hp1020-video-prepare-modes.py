#!/usr/bin/env python3
"""Model HP 1020 video-prepare mode/timing branches.

This is offline analysis only. It extracts literal constants and table blocks
used by `0x10014910 hp1020_video_prepare_page_candidate`, then documents the
current model for `0xb100....` setup registers before video transfer starts.
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
SOURCE = ROOT_DIR / "analysis/dispatch-mmio/decompiled/10014910_hp1020_video_prepare_page_candidate.c"
OUT_JSON = ROOT_DIR / "analysis/hardware-boundary/video-prepare-modes.json"
OUT_MD = ROOT_DIR / "analysis/hardware-boundary/video-prepare-modes.md"


LITERALS = {
    "block_a_status": 0x100067C0,
    "block_b_status": 0x100067D8,
    "block_a_control": 0x10006808,
    "block_b_control": 0x1000680C,
    "setup_a_timing": 0x10006854,
    "setup_a_constant": 0x10006868,
    "setup_b_timing": 0x10006874,
    "setup_b_constant": 0x10006880,
    "mode_a_register": 0x10006884,
    "mode_a_clear_mask": 0x10006888,
    "mode_b_register": 0x1000688C,
    "mode_ab_clear_mask": 0x10006890,
    "timing_table_0": 0x10006894,
    "control_pair_clear_mask": 0x10006898,
    "mode_control_mask": 0x1000689C,
    "timing_table_1": 0x100068A4,
    "timing_table_2": 0x100068B0,
    "timing_table_3": 0x100068B4,
    "vertical_a_register": 0x100068D8,
    "vertical_b_register": 0x100068DC,
    "stride_a_register": 0x100068E0,
    "stride_mask": 0x100068E4,
    "stride_b_register": 0x100068E8,
    "single_plane_300_lane1_table": 0x100068A8,
    "single_plane_300_default_table": 0x100068A0,
    "single_plane_600_alt_table": 0x100068AC,
    "single_plane_600_two_output_table": 0x100068B8,
    "single_plane_600_lane_table": 0x100068BC,
    "single_plane_1200_sparse_mask": 0x100068C0,
    "single_plane_1200_table": 0x100068C4,
    "two_plane_lane0_table": 0x100068C8,
    "two_plane_lane_table": 0x100068CC,
    "lane0_vertical_base": 0x100068D0,
    "lane1_vertical_base": 0x100068D4,
}

TABLE_POINTER_LITERALS = [
    "single_plane_300_lane1_table",
    "single_plane_300_default_table",
    "single_plane_600_alt_table",
    "single_plane_600_two_output_table",
    "single_plane_600_lane_table",
    "single_plane_1200_table",
    "two_plane_lane0_table",
    "two_plane_lane_table",
]

CHECKS = [
    ("stride_from_work_84", "uVar19 = (*(int *)(param_1 + 0x84) + 0x1fU & 0xffffffe0) >> 3"),
    ("lane_count_from_work_22", "uVar7 = (uint)*(ushort *)(param_1 + 0x22)"),
    ("resolution_600_mode", "if (sVar18 == 600)"),
    ("resolution_1200_mode", "if (sVar18 != 0x4b0) goto LAB_10014ae0"),
    ("block_control_clear", "*DAT_10006808 = *DAT_10006808 & 0xfffffeff"),
    ("block_status_busy_wait_a", "while ((uVar19 & 0x200) != 0)"),
    ("block_status_busy_wait_b", "} while ((*DAT_100067d8 & 0x200) != 0);"),
    ("timing_register_a_write", "*DAT_10006854 = uVar6"),
    ("mode_register_low_bits", "*DAT_10006884 = *DAT_10006884 & 0xffffffc0 | local_30"),
    ("table_zero_16_entries", "while (DAT_1000680c = puVar1, DAT_10006898 = uVar7, uVar19 < 0x10)"),
    ("single_plane_table_branch", "if (*(short *)(param_1 + 0x22) == 1)"),
    ("two_plane_table_branch", "else if (*(short *)(param_1 + 0x22) == 2)"),
    ("resolution_horizontal_mode", "if (*(short *)(param_1 + 0x16) == 300)"),
    ("vertical_packed_write_a", "*DAT_100068d8 = (uint)*(ushort *)(param_1 + 0x18) << 0x10 | uStack_2c"),
    ("final_enable_bit", "*puVar1 = *puVar1 | 0x100"),
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

    def read_words(self, addr: int, count: int) -> list[int]:
        return [self.read_u32(addr + index * 4) for index in range(count)]


def fmt32(value: int) -> str:
    return f"0x{value:08x}"


def literal_map(elf: ElfImage) -> dict[str, str]:
    return {name: fmt32(elf.read_u32(addr)) for name, addr in LITERALS.items()}


def table_blocks(elf: ElfImage, literals: dict[str, str]) -> list[dict[str, Any]]:
    blocks = []
    for name in TABLE_POINTER_LITERALS:
        ptr = int(literals[name], 16)
        count = 16 if name == "single_plane_1200_table" else 4
        blocks.append(
            {
                "name": name,
                "base": fmt32(ptr),
                "words": [fmt32(word) for word in elf.read_words(ptr, count)],
            }
        )
    return blocks


def timing_modes(literals: dict[str, str]) -> list[dict[str, Any]]:
    return [
        {
            "lane_selector": 0,
            "resolution": "300",
            "datastore_0x20_zero": True,
            "register": "0xb1000020",
            "value": "0x900236ca",
            "constant_registers": {"0xb1000024": "0x000000e5"},
        },
        {
            "lane_selector": 0,
            "resolution": "300",
            "datastore_0x20_zero": False,
            "register": "0xb1000020",
            "value": "0x90010598",
            "constant_registers": {"0xb1000024": "0x00000062"},
        },
        {
            "lane_selector": 0,
            "resolution": "not 300",
            "datastore_0x20_zero": True,
            "register": "0xb1000020",
            "value": "0x800236ca",
            "constant_registers": {"0xb1000024": "0x000000e5"},
        },
        {
            "lane_selector": 0,
            "resolution": "not 300",
            "datastore_0x20_zero": False,
            "register": "0xb1000020",
            "value": "0x80010598",
            "constant_registers": {"0xb1000024": "0x00000062"},
        },
        {
            "lane_selector": 1,
            "resolution": "300",
            "datastore_0x20_zero": True,
            "registers": ["0xb1000020", "0xb1000120"],
            "value": "0x90028688",
            "constant_registers": {"0xb1000024": "0x000000e5", "0xb1000124": "0x000000e5"},
        },
        {
            "lane_selector": 1,
            "resolution": "300",
            "datastore_0x20_zero": False,
            "registers": ["0xb1000020", "0xb1000120"],
            "value": "0x9001087d",
            "constant_registers": {"0xb1000024": "0x00000062", "0xb1000124": "0x00000062"},
        },
        {
            "lane_selector": 1,
            "resolution": "not 300",
            "datastore_0x20_zero": True,
            "registers": ["0xb1000020", "0xb1000120"],
            "value": "0x80028688",
            "constant_registers": {"0xb1000024": "0x000000e5", "0xb1000124": "0x000000e5"},
        },
        {
            "lane_selector": 1,
            "resolution": "not 300",
            "datastore_0x20_zero": False,
            "registers": ["0xb1000020", "0xb1000120"],
            "value": "0x8001087d",
            "constant_registers": {"0xb1000024": "0x00000062", "0xb1000124": "0x00000062"},
        },
    ]


def mode_register_rules() -> list[dict[str, Any]]:
    return [
        {
            "registers": ["0xb100001c", "0xb100011c"],
            "operation": "clear mask 0x00203f00, set bit 0x100, then replace low six bits",
            "lane0_datastore_zero": "0x0c",
            "lane0_datastore_nonzero": "0x05",
            "lane1_datastore_zero": "0x15",
            "lane1_datastore_nonzero": "0x08",
            "additional_bits": "clear 0x00180000 on both; set 0x00080000 on block B; set 0x00800000 on both",
        },
        {
            "registers": ["0xb1000000", "0xb1000100"],
            "operation": "clear 0x100, wait busy, apply lane/mode masks, then set 0x100",
            "state_200_1": "clear 0x03000000",
            "state_200_2": "write 0x01000000 under mask 0x03000000",
            "state_200_4": "write 0x02000000 under mask 0x03000000",
        },
        {
            "registers": ["0xb1000010", "0xb1000110"],
            "operation": "write packed vertical offset: work +0x18 in high 16 bits, lane offset in low 16 bits",
            "lane0_low_bits": "0x0068",
            "lane1_low_bits": "0x001e",
        },
    ]


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
    literals = literal_map(elf)
    checks = evidence_checks(source)
    fail_count = sum(check["status"] != "present" for check in checks)
    return {
        "summary": "Video-prepare mode/timing branches for 0x10014910.",
        "status": "pass" if fail_count == 0 else "fail",
        "literal_values": literals,
        "timing_modes": timing_modes(literals),
        "mode_register_rules": mode_register_rules(),
        "table_blocks": table_blocks(elf, literals),
        "checks": checks,
        "open_firmware_implication": [
            "Video prepare is not just a fixed register preamble; it branches on datastore entry 0x20, lane selector, plane count, and resolution.",
            "The 0xb1000400..0xb1000430 timing table writes are table-driven and must be understood before any printing firmware writes them.",
            "The safe current path remains USB-only; these tables are offline evidence for future hardware sequencing, not upload candidates.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 Video Prepare Mode Model",
        "",
        "This is a generated offline model. It does not contact the printer.",
        "",
        "## Result",
        "",
        f"- status: `{report['status']}`",
        "- function: `0x10014910 hp1020_video_prepare_page_candidate`",
        "",
        "## Key Literal Values",
        "",
        "| Name | Value |",
        "|---|---:|",
    ]
    for name, value in report["literal_values"].items():
        lines.append(f"| `{name}` | `{value}` |")

    lines.extend(["", "## Timing Register Modes", "", "| Lane selector | Resolution | Datastore 0x20 zero | Register(s) | Value | Constant register writes |", "|---:|---|---|---|---:|---|"])
    for item in report["timing_modes"]:
        registers = item.get("registers") or [item.get("register") or "0xb1000020"]
        constants = ", ".join(f"`{key}={value}`" for key, value in item["constant_registers"].items())
        lines.append(
            f"| `{item['lane_selector']}` | `{item['resolution']}` | `{item['datastore_0x20_zero']}` | "
            f"{', '.join(f'`{reg}`' for reg in registers)} | `{item['value']}` | {constants} |"
        )

    lines.extend(["", "## Mode Register Rules", ""])
    for item in report["mode_register_rules"]:
        lines.append(f"- registers {', '.join(f'`{reg}`' for reg in item['registers'])}: {item['operation']}")
        for key, value in item.items():
            if key not in {"registers", "operation"}:
                lines.append(f"  - `{key}`: `{value}`")
    lines.append("")

    lines.extend(["## Timing Table Blocks", "", "| Table | Base | Words |", "|---|---:|---|"])
    for item in report["table_blocks"]:
        lines.append(f"| `{item['name']}` | `{item['base']}` | {' '.join(f'`{word}`' for word in item['words'])} |")

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
    print(f"status={report['status']} checks={len(report['checks'])}")
    print(args.markdown_output)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
