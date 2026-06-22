#!/usr/bin/env python3
"""Generate a focused video/engine register semantics model for HP 1020.

This is offline analysis only. It reads the stock ELF literal cells and the
current decompiled functions, then emits a register-role model for the dangerous
print hardware boundary: engine command/status, video setup, video transfer,
and raw-band feed.
"""

from __future__ import annotations

import argparse
import json
import re
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
ELF_PATH = ROOT_DIR / "analysis/sihp1020.elf"
OUT_JSON = ROOT_DIR / "analysis/hardware-boundary/video-engine-register-semantics.json"
OUT_MD = ROOT_DIR / "analysis/hardware-boundary/video-engine-register-semantics.md"


SOURCES = {
    "video_prepare": "analysis/dispatch-mmio/decompiled/10014910_hp1020_video_prepare_page_candidate.c",
    "video_render": "analysis/dispatch-mmio/decompiled/10015214_hp1020_video_render_or_dma_candidate.c",
    "raw_band": "analysis/zjs-parser-boundary/decompiled/100140f8_hp1020_video_refresh_raw_bands_candidate.c",
    "video_reset": "analysis/dispatch-mmio/decompiled/10015458_hp1020_video_reset_or_flush_candidate.c",
    "engine_io": "analysis/dispatch-mmio/decompiled/10015c68_hp1020_engine_status_io_candidate.c",
    "engine_poll": "analysis/dispatch-mmio/decompiled/10015df8_hp1020_engine_status_poll_candidate.c",
    "engine_dispatch": "analysis/dispatch-mmio/decompiled/10016164_hp1020_engine_message_dispatch_candidate.c",
}


MANUAL_LITERAL_CELLS = {
    "engine_status_reg": {
        "literal_cell": "0x1000691c",
        "register": "0xb050000c",
        "source": "analysis/status-masks/status-mask-map.md",
    },
    "engine_command_reg": {
        "literal_cell": "0x10006928",
        "register": "0xb0500004",
        "source": "analysis/status-masks/status-mask-map.md",
    },
    "engine_clear_mask": {
        "literal_cell": "0x10006924",
        "value": "0xfeffffff",
        "source": "analysis/status-masks/status-mask-map.md",
    },
    "engine_command_preserve_mask": {
        "literal_cell": "0x10005d04",
        "value": "0xffff0000",
        "source": "analysis/status-masks/status-mask-map.md",
    },
    "engine_ready_submit_bit": {
        "literal_cell": "0x10005f20",
        "value": "0x00010000",
        "source": "analysis/status-masks/status-mask-map.md",
    },
    "engine_failure_event": {
        "literal_cell": "0x1000692c",
        "value": "0xfe001401",
        "source": "analysis/status-masks/status-mask-map.md",
    },
}


CHECKS = [
    (
        "engine_status_clear",
        "engine_io",
        "*puVar3 = *puVar3 & uVar5",
        "engine status register is cleared with the clear mask before command submission",
    ),
    (
        "engine_wait_ready_bit",
        "engine_io",
        "(*hp1020_engine_status_reg_table_word & uVar2) == 0",
        "engine status register is polled for the ready/submit bit",
    ),
    (
        "engine_command_write_preserve_upper",
        "engine_io",
        "*puVar6 = *puVar6 & uVar1 | (uint)*(ushort *)(puVar4 + 0x5a)",
        "engine command register preserves upper bits and inserts the 16-bit command",
    ),
    (
        "engine_command_submit_bit",
        "engine_io",
        "*puVar6 = *puVar6 | uVar2",
        "engine command register sets the ready/submit bit after command write",
    ),
    (
        "video_prepare_block_a_enable",
        "video_prepare",
        "*puVar1 = *puVar1 | 0x100",
        "video prepare enables or releases video block A with bit 0x100",
    ),
    (
        "video_prepare_block_busy_wait",
        "video_prepare",
        "while ((uVar19 & 0x200) != 0)",
        "video prepare waits while the block busy bit 0x200 remains set",
    ),
    (
        "video_render_channel_a_wait",
        "video_render",
        "while ((uVar10 & 2) == 0)",
        "video render waits for channel status bit 0x2",
    ),
    (
        "video_render_descriptor_width",
        "video_render",
        "*puVar5 = uVar11",
        "video render writes work-derived descriptor words",
    ),
    (
        "video_render_start_control",
        "video_render",
        "*puVar2 = uVar10 | 0x400",
        "video render writes the start/control word with bit 0x400 set",
    ),
    (
        "raw_band_pointer_write",
        "raw_band",
        "*DAT_100067cc = iVar8",
        "raw-band feed writes the raster payload pointer",
    ),
    (
        "raw_band_flags_write",
        "raw_band",
        "*DAT_100067d4 =",
        "raw-band feed writes count and flag bits",
    ),
    (
        "engine_poll_can_reset_video",
        "engine_poll",
        "hp1020_video_reset_dispatch_candidate()",
        "engine status polling can trigger video reset dispatch",
    ),
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

    def read_u32(self, addr: int) -> int | None:
        for p_offset, p_vaddr, p_filesz in self.load_segments:
            if p_vaddr <= addr <= p_vaddr + p_filesz - 4:
                off = p_offset + (addr - p_vaddr)
                return struct.unpack(">I", self.data[off : off + 4])[0]
        return None


def fmt32(value: int) -> str:
    return f"0x{value:08x}"


def register_family(value: int) -> str | None:
    high = value >> 16
    if high in {0xB050, 0xB100, 0xB200, 0xB204, 0xB208}:
        return f"0x{high:04x}...."
    return None


def read_sources() -> dict[str, str]:
    return {name: (ROOT_DIR / rel).read_text(errors="replace") for name, rel in SOURCES.items()}


def extract_mmio_literals(elf: ElfImage, sources: dict[str, str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, int, int]] = set()
    for source_name, text in sources.items():
        for match in re.finditer(r"\b(?:PTR_)?DAT_([0-9a-fA-F]{8})\b|\bDAT_([0-9a-fA-F]{8})\b", text):
            cell_text = match.group(1) or match.group(2)
            cell = int(cell_text, 16)
            value = elf.read_u32(cell)
            if value is None:
                continue
            family = register_family(value)
            if not family:
                continue
            key = (source_name, cell, value)
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "source": source_name,
                    "source_file": SOURCES[source_name],
                    "literal_cell": fmt32(cell),
                    "register": fmt32(value),
                    "family": family,
                    "role": role_for_register(value, source_name),
                }
            )
    return sorted(rows, key=lambda row: (row["source"], row["register"], row["literal_cell"]))


def role_for_register(value: int, source_name: str) -> str:
    roles = {
        0xB050000C: "engine status/ready handshake register",
        0xB0500004: "engine command/control submit register",
        0xB1000000: "video block A control/reset/enable register",
        0xB1000004: "video block A status/busy/readiness register",
        0xB1000008: "raw-band A raster pointer register",
        0xB100000C: "raw-band A count/flag register",
        0xB1000100: "video block B control/reset/enable register",
        0xB1000104: "video block B status/busy/readiness register",
        0xB1000108: "raw-band B raster window/pointer register",
        0xB100010C: "raw-band B count/flag register",
        0xB1000010: "video setup A vertical/offset packed register",
        0xB1000110: "video setup B vertical/offset packed register",
        0xB1000014: "video setup A stride/window mask register",
        0xB1000114: "video setup B stride/window mask register",
        0xB100001C: "video setup A mode/timing register",
        0xB100011C: "video setup B mode/timing register",
        0xB1000020: "video timing/setup A table register",
        0xB1000024: "video timing/setup A constant register",
        0xB1000120: "video timing/setup B table register",
        0xB1000124: "video timing/setup B constant register",
        0xB1000400: "video timing table register 0",
        0xB1000410: "video timing table register 1",
        0xB1000420: "video timing table register 2",
        0xB1000430: "video timing table register 3",
        0xB2000010: "video transfer status/control register",
        0xB2000008: "video transfer descriptor field from work +0x84",
        0xB200000C: "video transfer descriptor field from work +0x88",
        0xB2000024: "video transfer descriptor field from work +0x8c",
        0xB2000000: "video transfer start/control register",
        0xB2040000: "video transfer channel A control register",
        0xB2040004: "video channel A raster pointer register",
        0xB2040008: "video channel A transfer length/progress register",
        0xB204000C: "video transfer channel A status register",
        0xB2080000: "video transfer channel B control register",
        0xB208000C: "video transfer channel B status register",
    }
    return roles.get(value, f"{source_name} MMIO literal")


def evidence_checks(sources: dict[str, str]) -> list[dict[str, str]]:
    checks = []
    for name, source_name, needle, detail in CHECKS:
        source = sources[source_name]
        checks.append(
            {
                "name": name,
                "status": "present" if needle in source else "missing",
                "source": SOURCES[source_name],
                "needle": needle,
                "detail": detail,
            }
        )
    return checks


def semantic_sequences() -> list[dict[str, Any]]:
    return [
        {
            "name": "engine_command_status_handshake",
            "function": "0x10015c68 hp1020_engine_status_io_candidate",
            "registers": ["0xb050000c", "0xb0500004"],
            "steps": [
                "store requested 16-bit engine command in firmware state +0x5a",
                "clear status register with mask 0xfeffffff",
                "wait until status register bit 0x00010000 is set",
                "write command into low 16 bits of command register while preserving upper 16 bits",
                "set command register bit 0x00010000 to submit",
                "wait for event response; timeout sends engine queue message 0x17 with event 0xfe001401",
            ],
            "meaning": "This is the mechanical engine command door. An open printer path cannot safely fake it without knowing command meanings and response timing.",
        },
        {
            "name": "video_block_prepare_and_enable",
            "function": "0x10014910 hp1020_video_prepare_page_candidate",
            "registers": ["0xb1000000", "0xb1000004", "0xb1000100", "0xb1000104"],
            "steps": [
                "clear block control bit 0x100 on both video blocks",
                "wait while status bit 0x200 remains set",
                "program mode/timing registers from resolution, planes, and work fields",
                "set block control bit 0x100 to enable/release the prepared block",
            ],
            "meaning": "This is video hardware setup before transfer. It is register-heavy and timing-sensitive.",
        },
        {
            "name": "video_transfer_channel_arm",
            "function": "0x10015214 hp1020_video_render_or_dma_candidate",
            "registers": ["0xb2040000", "0xb204000c", "0xb2080000", "0xb208000c"],
            "steps": [
                "toggle channel A control bit 0x2 and wait for channel A status bit 0x2",
                "set channel A control bit 0x1 and high/control bit 0x80000000",
                "repeat the same arm/wait pattern for channel B",
            ],
            "meaning": "The two transfer channels have a handshake before descriptor registers are started.",
        },
        {
            "name": "video_descriptor_start",
            "function": "0x10015214 hp1020_video_render_or_dma_candidate",
            "registers": ["0xb2000008", "0xb200000c", "0xb2000024", "0xb2000000", "0xb2000010"],
            "steps": [
                "clear transfer-control bit 0 in 0xb2000010",
                "write work +0x84 to 0xb2000008",
                "write work +0x88 to 0xb200000c",
                "write work +0x8c to 0xb2000024",
                "derive a control word from work +0x90, then set bit 0x400 and write 0xb2000000",
                "later set bit 0 in 0xb2000010 after transfer-progress checks",
            ],
            "meaning": "This is the first direct path from host-controlled BIH fields into video transfer hardware.",
        },
        {
            "name": "raw_band_feed",
            "function": "0x100140f8 hp1020_video_refresh_raw_bands_candidate",
            "registers": ["0xb1000008", "0xb100000c", "0xb1000108", "0xb100010c"],
            "steps": [
                "walk video_state +0x9c raster-list nodes",
                "write payload +0x54 raster pointer to 0xb1000008",
                "in two-lane mode write pointer + video_state +0xbc to 0xb1000108",
                "derive count from payload +0x20 and video_state +0xc4",
                "OR flag bits from payload +0x4c, payload +0x50, and video_state +0xec",
                "write count/flags to 0xb100000c and 0xb100010c",
            ],
            "meaning": "This path feeds compressed raster payload pointers and flags into the raw-band side of the video block.",
        },
    ]


def build_report(elf_path: Path) -> dict[str, Any]:
    elf = ElfImage.load(elf_path)
    sources = read_sources()
    literals = extract_mmio_literals(elf, sources)
    checks = evidence_checks(sources)
    missing = [check for check in checks if check["status"] != "present"]
    return {
        "summary": "Focused model of dangerous video/engine register roles used by first-page printing.",
        "status": "pass" if not missing else "fail",
        "manual_literal_cells": MANUAL_LITERAL_CELLS,
        "mmio_literals": literals,
        "semantic_sequences": semantic_sequences(),
        "checks": checks,
        "open_firmware_implication": [
            "USB-only probes remain the correct next hardware tests.",
            "A printing firmware cannot jump straight from the parsed raster list to these registers without reproducing engine and video state-machine ordering.",
            "The most useful next offline target is extracting exact bit semantics and timing for the 0xb100 setup path and the 0xb050 engine command set.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 Video/Engine Register Semantics",
        "",
        "This is a generated offline model. It does not contact the printer.",
        "",
        "## Result",
        "",
        f"- status: `{report['status']}`",
        "- scope: first-page print hardware boundary after ZjStream parsing",
        "",
        "## Engine Handshake Constants",
        "",
        "| Name | Literal cell | Value/register | Source |",
        "|---|---:|---:|---|",
    ]
    for name, item in report["manual_literal_cells"].items():
        value = item.get("register") or item.get("value")
        lines.append(f"| `{name}` | `{item['literal_cell']}` | `{value}` | `{item['source']}` |")

    lines.extend(["", "## MMIO Literal Map", "", "| Source | Literal cell | Register | Role |", "|---|---:|---:|---|"])
    for item in report["mmio_literals"]:
        lines.append(
            f"| `{item['source']}` | `{item['literal_cell']}` | `{item['register']}` | {item['role']} |"
        )

    lines.extend(["", "## Semantic Sequences", ""])
    for sequence in report["semantic_sequences"]:
        lines.extend(
            [
                f"### `{sequence['name']}`",
                "",
                f"- function: `{sequence['function']}`",
                f"- registers: {', '.join(f'`{reg}`' for reg in sequence['registers'])}",
                f"- meaning: {sequence['meaning']}",
                "",
            ]
        )
        for index, step in enumerate(sequence["steps"], 1):
            lines.append(f"{index}. {step}")
        lines.append("")

    lines.extend(["## Evidence Checks", "", "| Check | Status | Detail | Source |", "|---|---|---|---|"])
    for check in report["checks"]:
        lines.append(f"| `{check['name']}` | `{check['status']}` | {check['detail']} | `{check['source']}` |")

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
