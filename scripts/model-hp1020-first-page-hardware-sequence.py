#!/usr/bin/env python3
"""Generate the first-page hardware sequence model for HP 1020 printing.

This is an offline synthesis report. It does not contact the printer. It turns
the current parser, work-object, video projection, and hardware-boundary reports
into an ordered view of the part we still must understand before any real open
printing attempt.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT_DIR / "analysis/hardware-boundary/first-page-hardware-sequence.json"
OUT_MD = ROOT_DIR / "analysis/hardware-boundary/first-page-hardware-sequence.md"


def load_json(rel: str) -> Any:
    return json.loads((ROOT_DIR / rel).read_text())


def first_variant(projection: dict[str, Any], case: str = "a4_default") -> dict[str, Any]:
    variants = projection.get("variants", [])
    for item in variants:
        if item.get("case") == case:
            return item
    if variants:
        return variants[0]
    return {}


def actions_by_function(boundary: dict[str, Any], function: str) -> list[dict[str, Any]]:
    return [
        item
        for item in boundary.get("register_actions", [])
        if function in str(item.get("function", ""))
    ]


def build_model() -> dict[str, Any]:
    print_model = load_json("analysis/open-firmware-model/print-path-model.json")
    projection = load_json("analysis/hardware-boundary/video-register-projection.json")
    boundary = load_json("analysis/hardware-boundary/hardware-boundary.json")
    engine_topology = load_json("analysis/hardware-boundary/engine-print-topology.json")
    video_prepare_projection = load_json("analysis/hardware-boundary/video-prepare-projection.json")
    video_refill_topology = load_json("analysis/hardware-boundary/video-refill-topology.json")

    variant = first_variant(projection)
    projected_registers = variant.get("projected_registers", {})
    refill_paths = {
        item.get("name"): item
        for item in video_refill_topology.get("topology", [])
        if isinstance(item, dict)
    }
    normal_refill = refill_paths.get("normal_descriptor_queue_refill", {})
    prepare_projection = next(
        (item for item in video_prepare_projection.get("projections", []) if item.get("case") == variant.get("case")),
        {},
    )
    prepare_default_state = {}
    for scenario in prepare_projection.get("scenarios", []):
        if (
            scenario.get("datastore_0x20_zero") is True
            and scenario.get("lane_selector") == 0
            and scenario.get("secondary_output_state_plus_0xec_nonzero") is False
        ):
            prepare_default_state = scenario.get("derived_state", {})
            break

    work_objects = print_model.get("objects", {}).get("work_objects", [])
    work = work_objects[0] if work_objects else {"fields": {}}
    fields = work.get("fields", {})
    rasters = print_model.get("objects", {}).get("raster_nodes", [])
    raster = rasters[0] if rasters else {"payload_fields": {}}
    payload = raster.get("payload_fields", {})

    sequence = [
        {
            "step": 1,
            "stage": "host stream parsed",
            "firmware_area": "USB2Thread/ZjStream parser/JobMgr",
            "function": "0x10009d34 -> JobMgr queue 3",
            "evidence": "JZJZ chunks create document/page/work objects and raster list nodes.",
            "hardware_registers": [],
            "open_replacement_meaning": "Software parser state machine. Already mapped well enough for the controlled foo2zjs path.",
            "risk": "medium",
        },
        {
            "step": 2,
            "stage": "engine accepts page work",
            "firmware_area": "Engine Queue",
            "function": "0x10016164 hp1020_engine_message_dispatch_candidate",
            "evidence": "Engine topology models page work acceptance: status poll, active/deferred work pointers, config selection, and command 0x6012 or 0x3a13.",
            "hardware_registers": actions_by_function(boundary, "0x10015c68"),
            "topology_source": "analysis/hardware-boundary/engine-print-topology.md",
            "topology_stage": "page_work_acceptance",
            "open_replacement_meaning": "Mechanical gate: paper/fuser/motor state must be correct before video transfer.",
            "risk": "high",
        },
        {
            "step": 3,
            "stage": "PrintMgr sends work to video",
            "firmware_area": "PrintMgr -> Video Queue",
            "function": "0x1000f574 -> queue 8 message 0x0b",
            "evidence": "payload word 3 carries the 0x94 work pointer to VideoThread.",
            "hardware_registers": [],
            "open_replacement_meaning": "Scheduling bridge. Pure software, but it coordinates engine and video ownership.",
            "risk": "medium",
        },
        {
            "step": 4,
            "stage": "VideoThread stores active work",
            "firmware_area": "Video state",
            "function": "0x10013c18 hp1020_video_thread_candidate",
            "evidence": "work pointer lands in video state +0x60 or +0x64; render state lives around +0x6c.",
            "hardware_registers": [],
            "open_replacement_meaning": "State bookkeeping before touching video hardware.",
            "risk": "medium",
        },
        {
            "step": 5,
            "stage": "video page preparation",
            "firmware_area": "Video setup",
            "function": "0x10014910 hp1020_video_prepare_page_candidate",
            "evidence": "Consumes work fields and current generated variants project into the 600dpi/NBIE=1 setup family.",
            "hardware_registers": actions_by_function(boundary, "0x10014910"),
            "projected_state": {
                key: prepare_default_state.get(key)
                for key in (
                    "stride_plus_0xb8",
                    "state_plus_0xbc",
                    "state_plus_0xc4",
                    "state_plus_0xf4",
                    "state_plus_0xc8_state_200",
                )
            },
            "topology_source": "analysis/hardware-boundary/video-prepare-projection.md",
            "open_replacement_meaning": "Programs video block setup/timing. This is not safe to approximate blindly.",
            "risk": "high",
        },
        {
            "step": 6,
            "stage": "video transfer arm",
            "firmware_area": "Video DMA/transfer channels",
            "function": "0x10015214 hp1020_video_render_or_dma_candidate",
            "evidence": "Arms paired 0xb204/0xb208 channels, waits status, writes 0xb200 descriptors, starts transfer.",
            "hardware_registers": actions_by_function(boundary, "0x10015214"),
            "projected_registers": {
                key: projected_registers.get(key)
                for key in ("0xb2000008", "0xb200000c", "0xb2000024", "0xb2000000")
            },
            "open_replacement_meaning": "First direct bridge from host-controlled BIH/work fields into video transfer registers.",
            "risk": "high",
        },
        {
            "step": 7,
            "stage": "video refill / raw-band feed",
            "firmware_area": "Video refill and raw raster/video feed",
            "function": "normal hypothesis: 0x10014244 -> 0x10013f34 descriptor queue/list path",
            "evidence": "Video refill topology selects descriptor-queue refill when work +0x74 is zero; raw linked-list refresh via 0x100140f8 is real but alternate.",
            "hardware_registers": [
                {
                    "register": "0xb1000008 / 0xb1000108",
                    "action": "raw-band pointer/window write",
                    "evidence": "normal descriptor queue/list helper and alternate raw refresh both write raw-band pointer/window registers",
                    "function": "0x10013f34 / 0x100140f8",
                    "risk": "raw-band feed",
                },
                {
                    "register": "0xb100000c / 0xb100010c",
                    "action": "raw-band flags/count write",
                    "evidence": "normal descriptor queue/list helper and alternate raw refresh both write raw-band count/flag registers",
                    "function": "0x10013f34 / 0x100140f8",
                    "risk": "raw-band feed",
                },
                {
                    "register": "0xb2080004 / 0xb2080008",
                    "action": "channel-B refill descriptor write",
                    "evidence": "0x10014244 fills channel-B pointer and transfer length from remaining units",
                    "function": "0x10014244",
                    "risk": "video transfer refill",
                },
            ],
            "projected_registers": {
                "normal_refill_state_fields": {
                    "source": "analysis/hardware-boundary/video-refill-topology.md",
                    "value": ", ".join(normal_refill.get("state_fields", [])),
                    "consumer": "0x10014244 -> 0x10013f34",
                },
                "normal_refill_unsafe_registers": {
                    "source": "analysis/hardware-boundary/video-refill-topology.md",
                    "value": ", ".join(normal_refill.get("unsafe_registers", [])),
                    "consumer": "0x10014244 -> 0x10013f34",
                },
            },
            "topology_source": "analysis/hardware-boundary/video-refill-topology.md",
            "open_replacement_meaning": "Feeds compressed raster bytes to the hardware-side print path; normal/alternate mode selection matters for reproducing timing.",
            "risk": "high",
        },
        {
            "step": 8,
            "stage": "video done wakes engine",
            "firmware_area": "Video -> Engine Queue",
            "function": "VideoThread sends engine queue message 0x10",
            "evidence": "Video handoff report identifies engine queue message 0x10 after video work completes.",
            "hardware_registers": [],
            "open_replacement_meaning": "Completion coordination; needed so engine timing and status do not drift.",
            "risk": "high",
        },
    ]

    missing = [
        "Exact 0xb100 timing/setup register meanings in video_prepare_page.",
        "Exact 0xb204/0xb208 channel state machine and timeout/retry behavior.",
        "Exact 0xb050 engine command set and safe mechanical sequencing.",
        "Whether the hardware consumes JBIG-compressed BID bytes directly or through an undocumented assist path.",
    ]

    return {
        "summary": "Ordered first-page hardware sequence after the mapped parser/object boundary.",
        "source_case": variant.get("case", "unknown"),
        "modeled_work_fields": {
            "+0x50": fields.get("+0x50"),
            "+0x84": fields.get("+0x84"),
            "+0x88": fields.get("+0x88"),
            "+0x8c": fields.get("+0x8c"),
            "+0x90": fields.get("+0x90"),
        },
        "modeled_raster_payload": {
            "+0x48": payload.get("+0x48"),
            "+0x50": payload.get("+0x50"),
            "+0x54": payload.get("+0x54"),
        },
        "sequence": sequence,
        "remaining_unknowns": missing,
        "source_reports": {
            "engine_topology": "analysis/hardware-boundary/engine-print-topology.json",
            "video_prepare_projection": "analysis/hardware-boundary/video-prepare-projection.json",
            "video_refill_topology": "analysis/hardware-boundary/video-refill-topology.json",
        },
        "engine_topology_status": engine_topology.get("status"),
        "video_refill_topology_status": video_refill_topology.get("status"),
        "decision": "Do not attempt open printing until USB-only open code is proven and video/engine register sequencing is modeled more tightly.",
    }


def render_registers(registers: list[dict[str, Any]]) -> str:
    if not registers:
        return "none"
    parts = []
    for item in registers:
        reg = item.get("register", "?")
        action = item.get("action", "action")
        parts.append(f"`{reg}` {action}")
    return "<br>".join(parts)


def render_markdown(model: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 First-Page Hardware Sequence",
        "",
        "This is a generated offline model. It does not contact the printer.",
        "",
        "## Purpose",
        "",
        "The parser/object path is mapped well enough for the current foo2zjs sample. This report orders the next part: what the stock firmware appears to do when one page crosses from software objects into video and engine hardware.",
        "",
        f"- source projection case: `{model['source_case']}`",
        f"- decision: {model['decision']}",
        "",
        "## Modeled Inputs",
        "",
        "| Object field | Value | Meaning |",
        "|---:|---|---|",
    ]
    work_meanings = {
        "+0x50": "raster/list content",
        "+0x84": "BIH-derived horizontal/video field",
        "+0x88": "BIH-derived vertical/video field",
        "+0x8c": "BIH L0/band-height-like field",
        "+0x90": "BIH options/control source",
    }
    for key, value in model["modeled_work_fields"].items():
        lines.append(f"| `work {key}` | `{value}` | {work_meanings[key]} |")
    lines.append("")
    for key, value in model["modeled_raster_payload"].items():
        lines.append(f"- raster payload `{key}`: `{value}`")

    lines.extend(
        [
            "",
            "## Ordered Sequence",
            "",
            "| Step | Stage | Function/path | Hardware registers | Meaning for open firmware | Risk |",
            "|---:|---|---|---|---|---|",
        ]
    )
    for item in model["sequence"]:
        regs = render_registers(item.get("hardware_registers", []))
        lines.append(
            f"| `{item['step']}` | {item['stage']} | `{item['function']}` | {regs} | {item['open_replacement_meaning']} | `{item['risk']}` |"
        )
        projected = item.get("projected_registers") or {}
        if projected:
            for reg, detail in projected.items():
                if detail:
                    lines.append(
                        f"|  | projected `{reg}` | {detail.get('source', '')} | `{detail.get('value')}` | consumer `{detail.get('consumer')}` |  |"
                    )
        projected_state = item.get("projected_state") or {}
        if projected_state:
            for field, value in projected_state.items():
                lines.append(
                    f"|  | projected video state `{field}` | `analysis/hardware-boundary/video-prepare-projection.md` | `{value}` | setup projection |  |"
                )

    lines.extend(["", "## Remaining Unknowns", ""])
    for item in model["remaining_unknowns"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-output", type=Path, default=OUT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=OUT_MD)
    args = parser.parse_args()

    model = build_model()
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(model, indent=2, sort_keys=True) + "\n")
    args.markdown_output.write_text(render_markdown(model) + "\n")
    print(args.markdown_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
