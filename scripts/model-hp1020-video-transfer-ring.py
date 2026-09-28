#!/usr/bin/env python3
"""Model HP 1020 video transfer ring ownership.

This is offline analysis only. It records how video prepare, render, and the
video interrupt/band-done helper coordinate the small ring indices and transfer
descriptor writes around the dangerous video hardware boundary.
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
OUT_JSON = ROOT_DIR / "analysis/hardware-boundary/video-transfer-ring.json"
OUT_MD = ROOT_DIR / "analysis/hardware-boundary/video-transfer-ring.md"

SOURCES = {
    "prepare": ROOT_DIR / "analysis/dispatch-mmio/decompiled/10014910_hp1020_video_prepare_page_candidate.c",
    "render": ROOT_DIR / "analysis/dispatch-mmio/decompiled/10015214_hp1020_video_render_or_dma_candidate.c",
    "irq": ROOT_DIR / "analysis/zjs-parser-boundary/decompiled/100144d0_hp1020_video_irq_or_band_done_candidate.c",
    "band_helper": ROOT_DIR / "analysis/zjs-parser-boundary/decompiled/10014244_hp1020_video_band_done_or_irq_helper_candidate.c",
    "raw_band": ROOT_DIR / "analysis/zjs-parser-boundary/decompiled/100140f8_hp1020_video_refresh_raw_bands_candidate.c",
}

LITERALS = {
    "video_state_base": 0x10006770,
    "ring_descriptor_base": 0x100067BC,
    "channel_b_pointer": 0x100067E4,
    "channel_b_length": 0x100067E8,
    "channel_a_pointer": 0x100067F4,
    "channel_a_progress": 0x100067F8,
    "transfer_status_control": 0x10006790,
    "channel_a_control": 0x10006798,
    "channel_a_status": 0x1000679C,
    "channel_b_control": 0x10006794,
    "channel_b_status": 0x100067A0,
    "video_error_busy": 0x1000683C,
    "scratch_control_word": 0x100068EC,
    "descriptor_width": 0x100068F0,
    "descriptor_height": 0x100068F4,
    "descriptor_band_height": 0x100068F8,
    "clear_0x2000_mask": 0x100068FC,
    "transfer_start_control": 0x10006900,
    "block_a_status": 0x100067C0,
    "block_b_status": 0x100067D8,
}

CHECKS = [
    ("prepare_clears_ring_slots", "prepare", "*(undefined4 *)(puVar15 + iVar8 * 4 + 0xa4) = 0"),
    ("prepare_clears_transfer_indices", "prepare", "*(undefined4 *)(puVar9 + 0x98) = 0"),
    ("prepare_clears_consumer_index", "prepare", "*(undefined4 *)(puVar9 + 0x94) = 0"),
    ("prepare_clears_done_index", "prepare", "*(undefined4 *)(puVar9 + 0xd8) = 0"),
    ("prepare_initializes_ring_records", "prepare", "*(undefined4 *)(puVar9 + *puVar1 * 0xc + 0x20) = 0"),
    ("render_next_index_mod4", "render", "uVar7 = *(int *)(hp1020_video_state_ptr_word + 0x98) + 1U & 3"),
    ("render_stores_raster_list", "render", "*(int *)(puVar1 + 0x9c) = iVar8"),
    ("render_clears_a0", "render", "*(undefined4 *)(puVar1 + 0xa0) = 0"),
    ("render_rejects_full_ring", "render", "if (*(uint *)(puVar1 + 0x94) == uVar7)"),
    ("render_descriptor_width", "render", "*puVar5 = uVar11"),
    ("render_descriptor_height", "render", "*DAT_100068f4 = *(undefined4 *)(param_1 + 0x88)"),
    ("render_descriptor_band_height", "render", "uVar11 = *(undefined4 *)(param_1 + 0x8c)"),
    ("render_start_bit_0x400", "render", "*puVar2 = uVar10 | 0x400"),
    ("render_channel_a_pointer", "render", "*DAT_100067f4 = uVar9"),
    ("render_channel_a_progress", "render", "*piVar4 = iVar8"),
    ("render_saves_raster_pointer", "render", "*(undefined4 *)(puVar1 + 0xa4) = uVar9"),
    ("render_advances_producer_index", "render", "*(uint *)(puVar1 + 0x98) = uVar7"),
    ("render_calls_band_helper", "render", "FUN_10014244()"),
    ("render_waits_channel_a_progress", "render", "} while ((uint)(iVar8 - *DAT_100067f8) < 8);"),
    ("render_sets_transfer_go", "render", "*DAT_10006790 = *DAT_10006790 | 1"),
    ("render_sets_state_running", "render", "*(undefined4 *)(hp1020_video_state_ptr_word + 0x6c) = 2"),
    ("band_helper_uses_e0_slot", "band_helper", "*(int *)(PTR_DAT_10006770 + 0xe0) * 0xc"),
    ("band_helper_caps_chunk", "band_helper", "if (*(uint *)(PTR_DAT_10006770 + 0xcc) < uVar3)"),
    ("band_helper_decrements_remaining", "band_helper", "*(uint *)(puVar1 + 0xd0) = iVar4 - uVar3"),
    ("band_helper_marks_descriptor_busy", "band_helper", "*piVar6 = 1"),
    ("band_helper_writes_channel_b_pointer", "band_helper", "*DAT_100067e4 = uVar7"),
    ("band_helper_writes_channel_b_length", "band_helper", "*piVar2 = iVar4 * iVar5"),
    ("irq_ack_0x20", "irq", "*puVar2 = 0xffffffdf"),
    ("irq_counts_band_done", "irq", "*(int *)(PTR_DAT_10006770 + 0xf8) = *(int *)(PTR_DAT_10006770 + 0xf8) + 1"),
    ("irq_clears_ring_record", "irq", "*(undefined4 *)(puVar1 + *(int *)(puVar1 + 0xd8) * 0xc + 0x20) = 0"),
    ("irq_advances_done_index", "irq", "*(uint *)(puVar1 + 0xd8) = *(int *)(puVar1 + 0xd8) + 1U & 3"),
    ("irq_refills_band_helper", "irq", "hp1020_video_band_done_or_irq_helper_candidate()"),
    ("irq_refreshes_raw_bands", "irq", "hp1020_video_refresh_raw_bands_candidate()"),
    ("irq_reset_case_7", "irq", "FUN_10013d4c(7)"),
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


def read_sources() -> dict[str, str]:
    return {name: path.read_text(errors="replace") for name, path in SOURCES.items()}


def literal_values(elf: ElfImage) -> dict[str, str]:
    return {name: fmt32(elf.read_u32(addr)) for name, addr in LITERALS.items()}


def ring_state_fields() -> list[dict[str, str]]:
    return [
        {"offset": "+0x20 + slot*0x0c", "field": "output descriptor owned flag", "meaning": "0x10014283 claims it before pixels are filled; 0x10014569 releases it after supplied completion; it is not a ready-pixels flag"},
        {"offset": "+0x24 + slot*0x0c", "field": "final output band flag", "meaning": "0x1001427e..0x10014281 sets it when remaining +0xd0 reaches zero; 0x10013f6f..0x10013f72 permits the otherwise-withheld final slot"},
        {"offset": "+0x28 + slot*0x0c", "field": "output band row/unit count", "meaning": "0x1001426e stores min(+0xcc,+0xd0); 0x100140cc reads it for output accounting"},
        {"offset": "+0x94", "field": "consumer/read index candidate", "meaning": "render treats equality with next producer index as ring full"},
        {"offset": "+0x98", "field": "producer/write index candidate", "meaning": "render advances `(value + 1) & 3` after descriptor setup"},
        {"offset": "+0x9c", "field": "active raster-list pointer", "meaning": "set from work +0x50 and walked by raw-band refresh"},
        {"offset": "+0xa0", "field": "pending/active raster node pointer", "meaning": "cleared by render, walked by reset/IRQ paths when +0xfc is negative"},
        {"offset": "+0xa4", "field": "saved raster pointer for current transfer", "meaning": "set when render snapshots channel-A pointer/progress"},
        {"offset": "+0xb8", "field": "stride bytes candidate", "meaning": "used by band helper as transfer length multiplier"},
        {"offset": "+0xcc", "field": "maximum chunk lines/units", "meaning": "caps helper chunk size"},
        {"offset": "+0xd0", "field": "remaining transfer units", "meaning": "helper decrements this by the chosen chunk"},
        {"offset": "+0xd4", "field": "remaining output units", "meaning": "0x100140c9..0x100140d7 subtracts the selected descriptor count after the output-write boundary"},
        {"offset": "+0xd8", "field": "IRQ done index candidate", "meaning": "advanced `(value + 1) & 3` when band-done bit 0x20 arrives"},
        {"offset": "+0xdc", "field": "next output-selection index", "meaning": "0x10013f60 selects it; 0x100140e2 advances it modulo four after output accounting; recovery also clears it"},
        {"offset": "+0xe0", "field": "next fill/publication index", "meaning": "chooses `descriptor_base + slot*0x0c` and buffer at state + slot*4; 0x10014468 advances it modulo four at the fill-completion RAM tail"},
        {"offset": "+0xf0", "field": "band-done happened flag", "meaning": "set by IRQ path after handling block status"},
        {"offset": "+0xf8", "field": "band-done counter", "meaning": "incremented when block status bit 0x20 is seen"},
        {"offset": "+0xfc", "field": "raw-band/reset mode sign field", "meaning": "negative path drains +0xa0 and refreshes raw bands; nonnegative path advances descriptor ring"},
    ]


def ownership_sequences(literals: dict[str, str]) -> list[dict[str, Any]]:
    return [
        {
            "name": "prepare_initializes_ring",
            "function": "0x10014910 hp1020_video_prepare_page_candidate",
            "steps": [
                "clear five saved pointer slots beginning at video_state +0xa4",
                "clear input producer index +0x98, input consumer index +0x94, output done index +0xd8, and output-selection index +0xdc",
                "clear four 0x0c-byte ring records beginning at video_state +0x20",
                "derive stride +0xb8 from work +0x84 and derive maximum chunk +0xcc",
            ],
            "registers": [],
        },
        {
            "name": "render_claims_next_slot",
            "function": "0x10015214 hp1020_video_render_or_dma_candidate",
            "steps": [
                "compute next producer slot as `(video_state +0x98 + 1) & 3`",
                "store work +0x50 raster list at +0x9c and clear +0xa0 before checking busy; rejection therefore changes these pointers",
                "return busy/error 0x1003 if state +0x6c is outside the accepted range or next slot equals +0x94",
                "arm channel A/B if not already in running state +0x6c == 2",
                "write work +0x84/+0x88/+0x8c/+0x90 into 0xb200 descriptor/control registers",
                "advance +0x98 to the claimed next slot",
            ],
            "registers": [
                literals["descriptor_width"],
                literals["descriptor_height"],
                literals["descriptor_band_height"],
                literals["transfer_start_control"],
            ],
        },
        {
            "name": "render_starts_first_transfer",
            "function": "0x10015214 hp1020_video_render_or_dma_candidate",
            "steps": [
                "when producer and consumer indices are equal, snapshot raster pointer/length into channel-A registers",
                "call 0x10014244 helper to fill channel-B descriptor from remaining units",
                "wait until `raster_end - 0xb2040008 >= 8` before setting transfer status/control bit 0",
                "raise internal event 0x13 and set video state +0x6c to 2",
            ],
            "registers": [
                literals["channel_a_pointer"],
                literals["channel_a_progress"],
                literals["channel_b_pointer"],
                literals["channel_b_length"],
                literals["transfer_status_control"],
            ],
        },
        {
            "name": "band_helper_refills_channel_b",
            "function": "0x10014244 hp1020_video_band_done_or_irq_helper_candidate",
            "steps": [
                "select descriptor record at `0x1002efe0 + (video_state +0xe0) * 0x0c`",
                "if the descriptor record is free and +0xd0 remaining is nonzero, choose `min(+0xcc, +0xd0)` units",
                "decrement +0xd0, mark whether this was the final chunk, and mark the descriptor busy",
                "write source pointer to 0xb2080004 and transfer length `chunk * stride(+0xb8)` to 0xb2080008",
            ],
            "registers": [literals["channel_b_pointer"], literals["channel_b_length"]],
        },
        {
            "name": "irq_band_done_advances_or_refills",
            "function": "0x100144d0 hp1020_video_irq_or_band_done_candidate",
            "steps": [
                "status bit 0x20 on either video block is acknowledged and increments +0xf8",
                "if +0xfc is negative, walk +0xa0, decrement child/page counters, advance +0xa0, then refresh raw bands",
                "otherwise clear ring record at `+0x20 + (+0xd8 * 0x0c)`, advance +0xd8 modulo 4, refill helper, and queue/list the next band",
                "set +0xf0 after handling the band-done status",
            ],
            "registers": [literals["block_a_status"], literals["block_b_status"]],
        },
    ]


def scenario_model() -> list[dict[str, Any]]:
    scenarios = []
    for producer, consumer in [(0, 0), (0, 1), (1, 2), (2, 3), (3, 0)]:
        next_slot = (producer + 1) & 3
        full = next_slot == consumer
        scenarios.append(
            {
                "name": f"producer_{producer}_consumer_{consumer}",
                "producer_before": producer,
                "consumer": consumer,
                "next_slot": next_slot,
                "render_result": "busy_error_0x1003" if full else "slot_claimed",
                "producer_after": producer if full else next_slot,
                "meaning": "render refuses to overrun consumer" if full else "render may claim the next modulo-4 slot",
            }
        )
    return scenarios


def evidence_checks(sources: dict[str, str]) -> list[dict[str, str]]:
    return [
        {
            "name": name,
            "status": "present" if needle in sources[source_name] else "missing",
            "source": str(SOURCES[source_name].relative_to(ROOT_DIR)),
            "needle": needle,
        }
        for name, source_name, needle in CHECKS
    ]


def build_report(elf_path: Path) -> dict[str, Any]:
    elf = ElfImage.load(elf_path)
    sources = read_sources()
    literals = literal_values(elf)
    checks = evidence_checks(sources)
    missing = [check for check in checks if check["status"] != "present"]
    return {
        "summary": "Video transfer ring ownership and descriptor handoff model.",
        "status": "pass" if not missing else "fail",
        "literal_values": literals,
        "state_fields": ring_state_fields(),
        "ownership_sequences": ownership_sequences(literals),
        "ring_scenarios": scenario_model(),
        "checks": checks,
        "open_firmware_implication": [
            "A printing replacement needs the ring ownership rules, not just the 0xb200 descriptor writes.",
            "The normal render path protects the input ring at +0x94/+0x98 and returns 0x1003 when the next slot would collide with the consumer index. This differs from the four output descriptors controlled by +0xe0/+0xdc/+0xd8.",
            "Output ownership, completed fill publication, output acceptance and completed consumption are separate stages. The RAM cuts and exact byte comparisons are owned by analysis/hardware-boundary/software-ring.json; they omit physical readiness and transfer operations.",
            "The interrupt/band-done path is responsible for clearing completed ring records and refilling channel-B descriptors.",
            "The remaining hard unknown is the exact interrupt/event timing that advances the consumer side under live hardware.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 Video Transfer Ring Model",
        "",
        "This is a generated offline model. It does not contact the printer.",
        "",
        "## Result",
        "",
        f"- status: `{report['status']}`",
        "- scope: video transfer ring indices, descriptor ownership, and band-done refill path",
        "",
        "## Key Literal Values",
        "",
        "| Name | Value |",
        "|---|---:|",
    ]
    for name, value in report["literal_values"].items():
        lines.append(f"| `{name}` | `{value}` |")

    lines.extend(["", "## State Fields", "", "| Offset | Field | Meaning |", "|---:|---|---|"])
    for item in report["state_fields"]:
        lines.append(f"| `{item['offset']}` | {item['field']} | {item['meaning']} |")

    lines.extend(["", "## Ownership Sequences", ""])
    for sequence in report["ownership_sequences"]:
        lines.extend(
            [
                f"### `{sequence['name']}`",
                "",
                f"- function: `{sequence['function']}`",
                "- registers: "
                + (", ".join(f"`{register}`" for register in sequence["registers"]) if sequence["registers"] else "-"),
                "",
            ]
        )
        for index, step in enumerate(sequence["steps"], 1):
            lines.append(f"{index}. {step}")
        lines.append("")

    lines.extend(["## Ring Scenarios", "", "| Scenario | Producer before | Consumer | Next slot | Result | Producer after | Meaning |", "|---|---:|---:|---:|---|---:|---|"])
    for item in report["ring_scenarios"]:
        lines.append(
            f"| `{item['name']}` | `{item['producer_before']}` | `{item['consumer']}` | `{item['next_slot']}` | "
            f"`{item['render_result']}` | `{item['producer_after']}` | {item['meaning']} |"
        )

    lines.extend(["", "## Evidence Checks", "", "| Check | Status | Source | Needle |", "|---|---|---|---|"])
    for check in report["checks"]:
        needle = check["needle"].replace("|", "\\|")
        lines.append(f"| `{check['name']}` | `{check['status']}` | `{check['source']}` | `{needle}` |")

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
        f"sequences={len(report['ownership_sequences'])} scenarios={len(report['ring_scenarios'])}"
    )
    print(args.markdown_output)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
