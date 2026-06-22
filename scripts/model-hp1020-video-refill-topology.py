#!/usr/bin/env python3
"""Synthesize the HP 1020 video refill topology from generated models.

This is offline analysis only. It reads the lower-level generated reports and
emits one concise end-to-end view of the descriptor-queue refill path versus the
alternate raw linked-list refresh path.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
MODE_FLAG_JSON = ROOT_DIR / "analysis/hardware-boundary/video-mode-flag.json"
IRQ_JSON = ROOT_DIR / "analysis/hardware-boundary/video-irq-decisions.json"
TRANSFER_RING_JSON = ROOT_DIR / "analysis/hardware-boundary/video-transfer-ring.json"
BAND_QUEUE_JSON = ROOT_DIR / "analysis/hardware-boundary/video-band-queue.json"
OUT_JSON = ROOT_DIR / "analysis/hardware-boundary/video-refill-topology.json"
OUT_MD = ROOT_DIR / "analysis/hardware-boundary/video-refill-topology.md"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def require_status(name: str, data: dict[str, Any]) -> dict[str, str]:
    return {
        "name": f"{name}_status_pass",
        "status": "present" if data.get("status") == "pass" else "missing",
        "detail": f"{name} status is {data.get('status')!r}",
    }


def build_report() -> dict[str, Any]:
    mode_flag = read_json(MODE_FLAG_JSON)
    irq = read_json(IRQ_JSON)
    ring = read_json(TRANSFER_RING_JSON)
    band_queue = read_json(BAND_QUEUE_JSON)

    mode_cases = {item["mode"]: item for item in mode_flag.get("mode_cases", [])}
    irq_scenarios = {item["name"]: item for item in irq.get("scenarios", [])}
    ring_sequences = {item["name"]: item for item in ring.get("ownership_sequences", [])}
    queue_sequences = {item["name"]: item for item in band_queue.get("queue_sequences", [])}

    checks = [
        require_status("video_mode_flag", mode_flag),
        require_status("video_irq_decisions", irq),
        require_status("video_transfer_ring", ring),
        require_status("video_band_queue", band_queue),
        {
            "name": "descriptor_queue_mode_present",
            "status": "present" if "descriptor_queue_mode" in mode_cases else "missing",
            "detail": "mode-flag model has descriptor_queue_mode",
        },
        {
            "name": "raw_linked_list_mode_present",
            "status": "present" if "raw_linked_list_mode" in mode_cases else "missing",
            "detail": "mode-flag model has raw_linked_list_mode",
        },
        {
            "name": "irq_has_ring_and_raw_band_done_scenarios",
            "status": "present"
            if {"band_done_ring_refill", "band_done_raw_band_refresh"}.issubset(irq_scenarios)
            else "missing",
            "detail": "IRQ model keeps both 0x20 band-done branches",
        },
        {
            "name": "ring_has_helper_refill_sequence",
            "status": "present" if "band_helper_refills_channel_b" in ring_sequences else "missing",
            "detail": "transfer-ring model includes channel-B helper refill",
        },
        {
            "name": "queue_has_loop_gate_and_raw_band_writes",
            "status": "present"
            if {"queue_loop_gate", "raw_band_single_block_write", "raw_band_dual_block_write"}.issubset(
                queue_sequences
            )
            else "missing",
            "detail": "band-queue model includes loop gate and raw-band writes",
        },
    ]

    descriptor_mode = mode_cases.get("descriptor_queue_mode", {})
    raw_mode = mode_cases.get("raw_linked_list_mode", {})
    status = "pass" if all(item["status"] == "present" for item in checks) else "fail"
    return {
        "summary": "End-to-end topology of HP 1020 video refill paths after a video band-done event.",
        "status": status,
        "source_reports": [
            str(MODE_FLAG_JSON.relative_to(ROOT_DIR)),
            str(IRQ_JSON.relative_to(ROOT_DIR)),
            str(TRANSFER_RING_JSON.relative_to(ROOT_DIR)),
            str(BAND_QUEUE_JSON.relative_to(ROOT_DIR)),
        ],
        "topology": [
            {
                "name": "normal_descriptor_queue_refill",
                "entry_condition": "work object +0x74 == 0, so video state +0xfc is nonnegative",
                "evidence": [
                    "mode flag model selects descriptor_queue_mode",
                    "IRQ bit 0x20 branch clears +0xd8 ring record and advances +0xd8",
                    "0x10014244 fills a channel-B descriptor from remaining +0xd0 units",
                    "0x10013f34 advances +0xdc and writes raw-band A/B pointer/flag registers",
                ],
                "state_fields": ["+0xd0", "+0xd8", "+0xdc", "+0xe0", "+0xf0", "+0xf8", "+0xfc"],
                "unsafe_registers": ["0xb1000008", "0xb100000c", "0xb1000108", "0xb100010c", "0xb2080004", "0xb2080008"],
                "mode_case": descriptor_mode,
            },
            {
                "name": "alternate_raw_linked_list_refill",
                "entry_condition": "work object +0x74 != 0, so video state +0xfc is negative",
                "evidence": [
                    "mode flag model selects raw_linked_list_mode",
                    "IRQ bit 0x20 branch walks video state +0xa0 linked-list nodes",
                    "the branch may adjust child/page counters and send JobMgr queue message 8",
                    "0x100140f8 refreshes raw-band registers from video state +0x9c raster nodes",
                ],
                "state_fields": ["+0x9c", "+0xa0", "+0xf0", "+0xf8", "+0xfc"],
                "unsafe_registers": ["0xb1000008", "0xb100000c", "0xb1000108", "0xb100010c"],
                "mode_case": raw_mode,
            },
        ],
        "current_conclusion": [
            "For the currently mapped normal print path, +0x74 is initialized to zero and the descriptor-queue refill path is the stronger default hypothesis.",
            "The raw linked-list refresh path is real firmware behavior, but its normal print-path producer is not yet proven.",
            "Both paths remain inside unsafe video/raw-band hardware, so this is planning evidence, not a reason to run custom mechanical firmware yet.",
        ],
        "checks": checks,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 Video Refill Topology",
        "",
        "This is a generated synthesis from lower-level offline models. It does not contact the printer.",
        "",
        "## Result",
        "",
        f"- status: `{report['status']}`",
        "- scope: video band-done refill path after parser/render handoff",
        "",
        "## Source Reports",
        "",
    ]
    for source in report["source_reports"]:
        lines.append(f"- `{source}`")

    lines.extend(["", "## Topology", ""])
    for item in report["topology"]:
        lines.extend(
            [
                f"### `{item['name']}`",
                "",
                f"- entry condition: {item['entry_condition']}",
                "- state fields: " + ", ".join(f"`{field}`" for field in item["state_fields"]),
                "- unsafe registers: " + ", ".join(f"`{register}`" for register in item["unsafe_registers"]),
                "",
                "Evidence:",
            ]
        )
        for evidence in item["evidence"]:
            lines.append(f"- {evidence}")
        lines.append("")

    lines.extend(["## Current Conclusion", ""])
    for item in report["current_conclusion"]:
        lines.append(f"- {item}")

    lines.extend(["", "## Checks", "", "| Check | Status | Detail |", "|---|---|---|"])
    for item in report["checks"]:
        lines.append(f"| `{item['name']}` | `{item['status']}` | {item['detail']} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    OUT_MD.write_text(render_markdown(report))
    print(f"status={report['status']} checks={len(report['checks'])} paths={len(report['topology'])}")
    print(OUT_MD)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
