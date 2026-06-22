#!/usr/bin/env python3
"""Model the HP 1020 video work-object mode flag.

This is offline analysis only. It records the path from work object `+0x74` to
video state `+0xfc` and the later IRQ/refill branch that chooses between the
raw linked-list refresher and the descriptor queue/list helper.
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
PREPARE_SOURCE = ROOT_DIR / "analysis/dispatch-mmio/decompiled/10014910_hp1020_video_prepare_page_candidate.c"
IRQ_SOURCE = ROOT_DIR / "analysis/zjs-parser-boundary/decompiled/100144d0_hp1020_video_irq_or_band_done_candidate.c"
RESET_SOURCE = ROOT_DIR / "analysis/dispatch-mmio/decompiled/10013d4c_hp1020_video_reset_dispatch_candidate.c"
CREATE_SOURCE = ROOT_DIR / "analysis/video-work-object/decompiled/1000f228_hp1020_video_work_create_candidate.c"
REPORT_SOURCE = ROOT_DIR / "analysis/video-work-object-report.md"
OUT_JSON = ROOT_DIR / "analysis/hardware-boundary/video-mode-flag.json"
OUT_MD = ROOT_DIR / "analysis/hardware-boundary/video-mode-flag.md"

LITERALS = {
    "high_bit": 0x10005E34,
    "high_bit_clear_mask": 0x1000628C,
    "video_state_base": 0x10006770,
}

CHECKS = [
    (
        "work_flag_initialized_zero",
        CREATE_SOURCE,
        "*(undefined1 *)(iVar1 + 0x74) = 0",
    ),
    (
        "work_flag_documented",
        REPORT_SOURCE,
        "| `+0x74` | cleared flag byte |",
    ),
    (
        "prepare_reads_work_flag",
        PREPARE_SOURCE,
        "if (*(char *)(param_1 + 0x74) == '\\0')",
    ),
    (
        "prepare_clears_state_high_bit",
        PREPARE_SOURCE,
        "uVar7 = *(uint *)(puVar15 + 0xfc) & DAT_1000628c",
    ),
    (
        "prepare_sets_state_high_bit",
        PREPARE_SOURCE,
        "uVar7 = *(uint *)(puVar15 + 0xfc) | DAT_10005e34",
    ),
    (
        "prepare_stores_state_flag",
        PREPARE_SOURCE,
        "*(uint *)(puVar15 + 0xfc) = uVar7",
    ),
    (
        "irq_tests_state_flag_negative",
        IRQ_SOURCE,
        "if (*(int *)(puVar1 + 0xfc) < 0)",
    ),
    (
        "irq_negative_calls_raw_refresh",
        IRQ_SOURCE,
        "hp1020_video_refresh_raw_bands_candidate();",
    ),
    (
        "irq_nonnegative_calls_band_done",
        IRQ_SOURCE,
        "hp1020_video_band_done_or_irq_helper_candidate();",
    ),
    (
        "irq_nonnegative_calls_band_queue",
        IRQ_SOURCE,
        "hp1020_video_band_queue_or_list_candidate();",
    ),
    (
        "irq_nonnegative_clears_descriptor_done_slot",
        IRQ_SOURCE,
        "*(undefined4 *)(puVar1 + *(int *)(puVar1 + 0xd8) * 0xc + 0x20) = 0",
    ),
    (
        "irq_nonnegative_advances_d8",
        IRQ_SOURCE,
        "*(uint *)(puVar1 + 0xd8) = *(int *)(puVar1 + 0xd8) + 1U & 3",
    ),
    (
        "reset_dispatch_has_state_flag_gate",
        RESET_SOURCE,
        "-(*(int *)(hp1020_video_state_ptr_word + 0xfc) >> 0x1f)",
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

    def read_u32(self, addr: int) -> int:
        for p_offset, p_vaddr, p_filesz in self.load_segments:
            if p_vaddr <= addr <= p_vaddr + p_filesz - 4:
                off = p_offset + (addr - p_vaddr)
                return struct.unpack(">I", self.data[off : off + 4])[0]
        raise ValueError(f"address 0x{addr:08x} is not file-backed")


def fmt32(value: int) -> str:
    return f"0x{value:08x}"


def literal_values(elf: ElfImage) -> dict[str, str]:
    values = {name: fmt32(elf.read_u32(addr)) for name, addr in LITERALS.items()}
    values["work_object_mode_flag_offset"] = "+0x74"
    values["video_state_mode_flag_offset"] = "+0xfc"
    return values


def evidence_checks() -> list[dict[str, str]]:
    rows = []
    for name, path, needle in CHECKS:
        source = path.read_text(errors="replace")
        rows.append(
            {
                "name": name,
                "status": "present" if needle in source else "missing",
                "source": str(path.relative_to(ROOT_DIR)),
                "needle": needle,
            }
        )
    return rows


def model_mode(work_flag: int, previous_state_fc: int = 0) -> dict[str, Any]:
    high_bit = 0x80000000
    clear_mask = 0x7FFFFFFF
    if work_flag == 0:
        state_fc = previous_state_fc & clear_mask
        mode = "descriptor_queue_mode"
        irq_band_done_path = [
            "clear descriptor done slot at video_state +0x20 + (+0xd8 * 0x0c)",
            "advance +0xd8 modulo 4",
            "call hp1020_video_band_done_or_irq_helper_candidate",
            "call hp1020_video_band_queue_or_list_candidate",
        ]
    else:
        state_fc = previous_state_fc | high_bit
        mode = "raw_linked_list_mode"
        irq_band_done_path = [
            "use video_state +0xa0 linked-list entry",
            "optionally decrement work/raster counters and send JobMgr queue message 8",
            "advance +0xa0 to next linked-list node",
            "call hp1020_video_refresh_raw_bands_candidate",
        ]
    return {
        "work_object_plus_0x74": work_flag,
        "previous_state_plus_0xfc": fmt32(previous_state_fc),
        "state_plus_0xfc_after_prepare": fmt32(state_fc),
        "state_plus_0xfc_is_negative": bool(state_fc & high_bit),
        "mode": mode,
        "irq_band_done_path": irq_band_done_path,
    }


def build_report(elf_path: Path) -> dict[str, Any]:
    elf = ElfImage.load(elf_path)
    checks = evidence_checks()
    missing = [item for item in checks if item["status"] != "present"]
    return {
        "summary": "Video work-object +0x74 to video state +0xfc mode-flag model.",
        "status": "pass" if not missing else "fail",
        "literal_values": literal_values(elf),
        "mode_cases": [
            model_mode(0, 0x80000000),
            model_mode(1, 0),
        ],
        "branch_sequences": [
            {
                "name": "prepare_copies_work_flag_to_state_sign",
                "function": "0x10014910 hp1020_video_prepare_page_candidate",
                "steps": [
                    "read work object byte +0x74",
                    "when zero, clear high bit in video state +0xfc with 0x7fffffff",
                    "when nonzero, set high bit in video state +0xfc with 0x80000000",
                ],
            },
            {
                "name": "irq_band_done_selects_refill_family",
                "function": "0x100144d0 hp1020_video_irq_or_band_done_candidate",
                "steps": [
                    "on video status bit 0x20, acknowledge block status and increment state +0xf8",
                    "if state +0xfc is negative, follow +0xa0 linked-list/raw-band refresh path",
                    "if state +0xfc is nonnegative, follow descriptor ring +0xd8 and band queue/list path",
                ],
            },
            {
                "name": "reset_dispatch_depends_on_same_sign_bit",
                "function": "0x10013d4c hp1020_video_reset_dispatch_candidate",
                "steps": [
                    "reset/flush path also tests the sign of video state +0xfc",
                    "Ghidra truncates the nonnegative branch as bad data, so this report records only the proven gate, not a full reset model",
                ],
            },
        ],
        "open_firmware_implication": [
            "The normal created video work object initializes +0x74 to zero in currently mapped evidence.",
            "A zero +0x74 selects the descriptor queue/list path, which matches the transfer-ring and band-queue models.",
            "The nonzero +0x74 raw linked-list path remains mapped enough to recognize, but no normal print-path producer has been proven yet.",
        ],
        "checks": checks,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 Video Mode Flag Model",
        "",
        "This is a generated offline model. It does not contact the printer.",
        "",
        "## Result",
        "",
        f"- status: `{report['status']}`",
        "- scope: work object `+0x74`, video state `+0xfc`, and the video IRQ refill fork",
        "",
        "## Key Values",
        "",
        "| Name | Value |",
        "|---|---:|",
    ]
    for name, value in report["literal_values"].items():
        lines.append(f"| `{name}` | `{value}` |")

    lines.extend(["", "## Mode Cases", "", "| Work +0x74 | State +0xfc after prepare | Sign bit | Mode | IRQ band-done path |", "|---:|---:|---|---|---|"])
    for case in report["mode_cases"]:
        path = "<br>".join(case["irq_band_done_path"])
        lines.append(
            f"| `{case['work_object_plus_0x74']}` | `{case['state_plus_0xfc_after_prepare']}` | "
            f"`{case['state_plus_0xfc_is_negative']}` | `{case['mode']}` | {path} |"
        )

    lines.extend(["", "## Branch Sequences", ""])
    for sequence in report["branch_sequences"]:
        lines.extend([f"### `{sequence['name']}`", "", f"- function: `{sequence['function']}`", ""])
        for index, step in enumerate(sequence["steps"], 1):
            lines.append(f"{index}. {step}")
        lines.append("")

    lines.extend(["## Evidence Checks", "", "| Check | Status | Source | Needle |", "|---|---|---|---|"])
    for item in report["checks"]:
        needle = item["needle"].replace("|", "\\|")
        lines.append(f"| `{item['name']}` | `{item['status']}` | `{item['source']}` | `{needle}` |")

    lines.extend(["", "## Open Firmware Meaning", ""])
    for item in report["open_firmware_implication"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--elf", type=Path, default=ELF_PATH)
    args = parser.parse_args()

    report = build_report(args.elf)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    OUT_MD.write_text(render_markdown(report))
    print(
        f"status={report['status']} checks={len(report['checks'])} "
        f"cases={len(report['mode_cases'])}"
    )
    print(OUT_MD)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
