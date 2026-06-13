#!/usr/bin/env python3
"""Generate an offline hardware-boundary model for HP 1020 firmware work."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "analysis/hardware-boundary"
OUT_JSON = OUT_DIR / "hardware-boundary.json"
OUT_MD = OUT_DIR / "hardware-boundary.md"


REGISTER_FAMILIES: list[dict[str, Any]] = [
    {
        "family": "0xb300....",
        "working_name": "USB controller",
        "risk": "lower",
        "why": "Needed for a non-printing boot/USB identity probe. It should not move paper or heat the fuser by itself.",
        "known_registers": [
            "0xb3000000",
            "0xb300000c",
            "0xb3000014",
            "0xb3000020",
            "0xb3000200",
            "0xb3000400",
            "0xb3010000",
        ],
        "main_sources": ["analysis/usb-path-report.md"],
    },
    {
        "family": "0xb100....",
        "working_name": "video/raster block control and raw-band feed",
        "risk": "high",
        "why": "Controls paired video/raster blocks, raw-band pointers, flags, reset/enable bits, and busy waits.",
        "known_registers": [
            "0xb1000000",
            "0xb1000004",
            "0xb1000008",
            "0xb100000c",
            "0xb1000010",
            "0xb1000014",
            "0xb100001c",
            "0xb1000020",
            "0xb1000024",
            "0xb1000100",
            "0xb1000104",
            "0xb1000108",
            "0xb100010c",
            "0xb1000110",
            "0xb1000114",
            "0xb100011c",
            "0xb1000120",
            "0xb1000124",
            "0xb1000400",
            "0xb1000410",
            "0xb1000420",
            "0xb1000430",
        ],
        "main_sources": [
            "analysis/dispatch-mmio/decompiled/10014910_hp1020_video_prepare_page_candidate.c",
            "analysis/dispatch-mmio/decompiled/100140f8_hp1020_video_refresh_raw_bands_candidate.c",
            "analysis/dispatch-mmio/decompiled/10015458_hp1020_video_reset_or_flush_candidate.c",
        ],
    },
    {
        "family": "0xb200....",
        "working_name": "video transfer descriptor/control block",
        "risk": "high",
        "why": "Receives page/raster geometry from the work object and starts/advances transfer.",
        "known_registers": ["0xb2000000", "0xb2000008", "0xb200000c", "0xb2000010", "0xb2000024"],
        "main_sources": ["analysis/dispatch-mmio/decompiled/10015214_hp1020_video_render_or_dma_candidate.c"],
    },
    {
        "family": "0xb204....",
        "working_name": "video transfer channel A",
        "risk": "high",
        "why": "Control/status channel toggled by video render before and during raster transfer.",
        "known_registers": ["0xb2040000", "0xb2040004", "0xb2040008", "0xb204000c"],
        "main_sources": ["analysis/dispatch-mmio/decompiled/10015214_hp1020_video_render_or_dma_candidate.c"],
    },
    {
        "family": "0xb208....",
        "working_name": "video transfer channel B",
        "risk": "high",
        "why": "Second video transfer channel toggled with the same enable/status pattern as channel A.",
        "known_registers": ["0xb2080000", "0xb2080004", "0xb2080008", "0xb208000c", "0xb2080010"],
        "main_sources": ["analysis/dispatch-mmio/decompiled/10015214_hp1020_video_render_or_dma_candidate.c"],
    },
    {
        "family": "0xb050....",
        "working_name": "engine command/status handshake",
        "risk": "high",
        "why": "Submits engine commands and polls mechanical/status responses through ready/submit bits.",
        "known_registers": ["0xb0500000", "0xb0500004", "0xb050000c", "0xb0501000"],
        "main_sources": [
            "analysis/dispatch-mmio/decompiled/10015c68_hp1020_engine_status_io_candidate.c",
            "analysis/dispatch-mmio/decompiled/10015df8_hp1020_engine_status_poll_candidate.c",
            "analysis/dispatch-mmio/decompiled/100160a8_hp1020_engine_preflight_candidate.c",
        ],
    },
    {
        "family": "0xb020....",
        "working_name": "engine/control hardware table family",
        "risk": "high",
        "why": "Appears in engine/control descriptor regions. Exact semantics are weaker than 0xb050, but it sits in the same unsafe hardware area.",
        "known_registers": ["0xb0200000", "0xb0200004", "0xb0200008", "0xb020000c"],
        "main_sources": ["analysis/engine-path-report.md"],
    },
    {
        "family": "0xb080.... / 0xb070.... / 0xb030....",
        "working_name": "early boot/timer/diagnostic hardware",
        "risk": "medium",
        "why": "Not on the normal print-raster path, but still MMIO. A boot probe should not write unknown hardware unless the original init sequence is understood.",
        "known_registers": ["0xb0800008", "0xb0800010", "0xb0800014", "0xb0700004", "0xb0700014", "0xb0300000"],
        "main_sources": ["analysis/boot-abi-report.md", "analysis/tasks/task-descriptors.md"],
    },
]


FUNCTION_BOUNDARIES: list[dict[str, Any]] = [
    {
        "function": "0x10009d34 hp1020_zjs_parser_entry_candidate",
        "layer": "input parser",
        "risk": "offline-safe when modeled only",
        "summary": "Parses JZJZ chunks and sends JobMgr messages. Safe in our host model because it does not run on the printer.",
        "must_avoid_in_custom_probe": False,
    },
    {
        "function": "0x10015214 hp1020_video_render_or_dma_candidate",
        "layer": "video transfer",
        "risk": "do-not-call in early custom firmware",
        "summary": "Uses work +0x84/+0x88/+0x8c/+0x90, arms 0xb204/0xb208 channels, writes 0xb200 descriptors, and starts transfer.",
        "must_avoid_in_custom_probe": True,
    },
    {
        "function": "0x100140f8 hp1020_video_refresh_raw_bands_candidate",
        "layer": "raw-band feed",
        "risk": "do-not-call in early custom firmware",
        "summary": "Walks video_state +0x9c raster nodes and writes payload pointers/flags to 0xb100 raw-band registers.",
        "must_avoid_in_custom_probe": True,
    },
    {
        "function": "0x10014910 hp1020_video_prepare_page_candidate",
        "layer": "video preparation",
        "risk": "do-not-call in early custom firmware",
        "summary": "Programs many 0xb100 control, timing, and setup registers before render.",
        "must_avoid_in_custom_probe": True,
    },
    {
        "function": "0x10015458 hp1020_video_reset_or_flush_candidate",
        "layer": "video reset/flush",
        "risk": "do-not-call until semantics are clearer",
        "summary": "Clears/sets 0x100 enable/reset bits and waits on 0x200 busy bits in 0xb100 pairs.",
        "must_avoid_in_custom_probe": True,
    },
    {
        "function": "0x10015c68 hp1020_engine_status_io_candidate",
        "layer": "engine command/status",
        "risk": "do-not-call in early custom firmware",
        "summary": "Writes 16-bit engine commands into 0xb0500004 and uses 0x00010000 submit/ready handshake.",
        "must_avoid_in_custom_probe": True,
    },
    {
        "function": "0x10015df8 hp1020_engine_status_poll_candidate",
        "layer": "engine status poll",
        "risk": "do-not-call in early custom firmware",
        "summary": "Chains multiple engine command/status reads and can trigger video reset dispatch.",
        "must_avoid_in_custom_probe": True,
    },
    {
        "function": "0x100160a8 hp1020_engine_preflight_candidate",
        "layer": "engine preflight",
        "risk": "do-not-call in early custom firmware",
        "summary": "Sets an engine command-register bit and waits for hardware state before publishing status.",
        "must_avoid_in_custom_probe": True,
    },
    {
        "function": "0x10016164 hp1020_engine_message_dispatch_candidate",
        "layer": "engine dispatcher",
        "risk": "do-not-feed page work in early custom firmware",
        "summary": "Engine message 0x0b/0x40 path stores work pointer and calls engine status I/O.",
        "must_avoid_in_custom_probe": True,
    },
]


REGISTER_ACTIONS: list[dict[str, Any]] = [
    {
        "register": "0xb050000c",
        "action": "clear/status wait",
        "function": "0x10015c68",
        "evidence": "clears with 0xfeffffff, waits for bit 0x00010000",
        "risk": "engine handshake",
    },
    {
        "register": "0xb0500004",
        "action": "engine command submit",
        "function": "0x10015c68",
        "evidence": "writes requested 16-bit command, then sets bit 0x00010000",
        "risk": "engine handshake",
    },
    {
        "register": "0xb2000008",
        "action": "video descriptor write",
        "function": "0x10015214",
        "evidence": "receives work +0x84, BIH-derived horizontal field",
        "risk": "video transfer",
    },
    {
        "register": "0xb200000c",
        "action": "video descriptor write",
        "function": "0x10015214",
        "evidence": "receives work +0x88, BIH-derived vertical field",
        "risk": "video transfer",
    },
    {
        "register": "0xb2000024",
        "action": "video descriptor write",
        "function": "0x10015214",
        "evidence": "receives work +0x8c, BIH L0/band-height-like field",
        "risk": "video transfer",
    },
    {
        "register": "0xb2000000",
        "action": "video transfer control write",
        "function": "0x10015214",
        "evidence": "writes computed control word from work +0x90 flags, OR 0x400",
        "risk": "video transfer start/control",
    },
    {
        "register": "0xb2040000 / 0xb2080000",
        "action": "paired channel enable/reset toggles",
        "function": "0x10015214",
        "evidence": "toggles bits 1 and 2 before descriptor writes",
        "risk": "video transfer channel control",
    },
    {
        "register": "0xb204000c / 0xb208000c",
        "action": "paired channel status waits",
        "function": "0x10015214",
        "evidence": "waits for bit 2 after channel toggles",
        "risk": "video transfer channel status",
    },
    {
        "register": "0xb1000008 / 0xb1000108",
        "action": "raw-band pointer/window write",
        "function": "0x100140f8",
        "evidence": "writes raster payload +0x54 pointer and pointer plus video_state +0xbc",
        "risk": "raw-band feed",
    },
    {
        "register": "0xb100000c / 0xb100010c",
        "action": "raw-band flags/count write",
        "function": "0x100140f8",
        "evidence": "writes count from payload +0x20 and flags from payload +0x4c/+0x50",
        "risk": "raw-band feed",
    },
    {
        "register": "0xb1000000 / 0xb1000100",
        "action": "video block reset/enable",
        "function": "0x10014910 / 0x10015458",
        "evidence": "clears and sets bit 0x100",
        "risk": "video block control",
    },
    {
        "register": "0xb1000004 / 0xb1000104",
        "action": "video block busy/status wait",
        "function": "0x10014910 / 0x10015458",
        "evidence": "waits while bit 0x200 remains set; tests bit 0x100 in raw-band loop",
        "risk": "video block status",
    },
]


def build_model() -> dict[str, Any]:
    return {
        "summary": "Offline safety map for the boundary between modeled host print input and physical printer hardware.",
        "register_families": REGISTER_FAMILIES,
        "function_boundaries": FUNCTION_BOUNDARIES,
        "register_actions": REGISTER_ACTIONS,
        "safe_custom_firmware_rule": [
            "A first custom firmware upload, if ever attempted, should initialize only the minimum CPU/runtime/USB path.",
            "It must not call video prepare/render/raw-band functions.",
            "It must not feed engine queue message 0x0b or 0x40.",
            "It must not write 0xb100, 0xb200, 0xb204, 0xb208, 0xb050, or 0xb020 registers.",
        ],
    }


def render_markdown(model: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 Hardware Boundary Safety Map",
        "",
        "This is an offline map of the boundary where reverse engineering stops being just bytes/objects and starts touching physical printer hardware.",
        "",
        "No printer is contacted by this model.",
        "",
        "## Register Families",
        "",
        "| Family | Working name | Risk | Why |",
        "|---|---|---|---|",
    ]
    for family in model["register_families"]:
        lines.append(
            f"| `{family['family']}` | {family['working_name']} | `{family['risk']}` | {family['why']} |"
        )

    lines.extend(["", "## Critical Functions", "", "| Function | Layer | Risk | Why it matters |", "|---|---|---|---|"])
    for function in model["function_boundaries"]:
        lines.append(
            f"| `{function['function']}` | {function['layer']} | `{function['risk']}` | {function['summary']} |"
        )

    lines.extend(["", "## Concrete Register Actions", "", "| Register | Action | Function | Evidence | Risk |", "|---|---|---:|---|---|"])
    for action in model["register_actions"]:
        lines.append(
            f"| `{action['register']}` | {action['action']} | `{action['function']}` | {action['evidence']} | {action['risk']} |"
        )

    lines.extend(
        [
            "",
            "## Safe Custom-Firmware Rule",
            "",
        ]
    )
    for rule in model["safe_custom_firmware_rule"]:
        lines.append(f"- {rule}")

    lines.extend(
        [
            "",
            "## Practical Readout",
            "",
            "The safe early target is not printing. It is a non-printing boot/USB identity probe that avoids engine and video MMIO entirely.",
            "",
            "The unsafe line is now concrete: do not touch the `0xb100`, `0xb200`, `0xb204`, `0xb208`, `0xb050`, or `0xb020` families until the exact register semantics are understood.",
            "",
            "The previous print-path model hands off at `work +0x50`. This map explains why that is the correct stop point: the next firmware functions program raw raster buffers, transfer channels, and engine handshakes.",
            "",
            "For the narrow custom-firmware target, see `analysis/non-printing-usb-probe-spec.md`.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    model = build_model()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(model, indent=2, sort_keys=True) + "\n")
    OUT_MD.write_text(render_markdown(model) + "\n")
    print(f"Wrote {OUT_MD.relative_to(REPO)}")
    print(f"Wrote {OUT_JSON.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
