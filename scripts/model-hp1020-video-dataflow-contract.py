#!/usr/bin/env python3
"""Generate the normal first-page video dataflow contract for HP 1020.

This is offline analysis only. It stitches the host/raster field model,
video-prepare projection, and transfer/refill helper models into one concrete
normal-path contract for the first page.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT_DIR / "analysis/hardware-boundary/video-dataflow-contract.json"
OUT_MD = ROOT_DIR / "analysis/hardware-boundary/video-dataflow-contract.md"

INPUTS = {
    "raster_fields": ROOT_DIR / "analysis/open-firmware-model/raster-field-semantics.json",
    "prepare_projection": ROOT_DIR / "analysis/hardware-boundary/video-prepare-projection.json",
    "transfer_ring": ROOT_DIR / "analysis/hardware-boundary/video-transfer-ring.json",
    "band_queue": ROOT_DIR / "analysis/hardware-boundary/video-band-queue.json",
    "refill_topology": ROOT_DIR / "analysis/hardware-boundary/video-refill-topology.json",
    "chunk_sizing": ROOT_DIR / "analysis/hardware-boundary/video-chunk-sizing.json",
    "remaining_units": ROOT_DIR / "analysis/hardware-boundary/video-remaining-units.json",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def check(name: str, ok: bool, detail: str) -> dict[str, str]:
    return {"name": name, "status": "present" if ok else "missing", "detail": detail}


def by_name(items: list[dict[str, Any]], key: str = "name") -> dict[str, dict[str, Any]]:
    return {item.get(key): item for item in items if isinstance(item, dict)}


def find_case(rows: list[dict[str, Any]], case: str) -> dict[str, Any]:
    for row in rows:
        if row.get("case") == case:
            return row
    return {}


def find_prepare_default(prepare: dict[str, Any], case: str) -> dict[str, Any]:
    projection = find_case(prepare.get("projections", []), case)
    for scenario in projection.get("scenarios", []):
        if (
            scenario.get("datastore_0x20_zero") is True
            and scenario.get("lane_selector") == 0
            and scenario.get("secondary_output_state_plus_0xec_nonzero") is False
        ):
            return scenario
    return {}


def split_work_fields(value: str) -> dict[str, Any]:
    parts = value.split("/")
    return {
        "+0x84": int(parts[0]),
        "+0x88": int(parts[1]),
        "+0x8c": int(parts[2]),
        "+0x90": int(parts[3], 16),
    }


def build_report() -> dict[str, Any]:
    raster_fields = read_json(INPUTS["raster_fields"])
    prepare_projection = read_json(INPUTS["prepare_projection"])
    transfer_ring = read_json(INPUTS["transfer_ring"])
    band_queue = read_json(INPUTS["band_queue"])
    refill_topology = read_json(INPUTS["refill_topology"])
    chunk_sizing = read_json(INPUTS["chunk_sizing"])
    remaining_units = read_json(INPUTS["remaining_units"])

    case = "a4_default"
    raster_case = find_case(raster_fields.get("case_matrix", []), case)
    work_fields = split_work_fields(raster_case.get("work_0x84_0x88_0x8c_0x90", "0/0/0/0x00"))
    prepare_default = find_prepare_default(prepare_projection, case)
    derived_state = prepare_default.get("derived_state", {})
    transfer_sequences = by_name(transfer_ring.get("ownership_sequences", []))
    queue_sequences = by_name(band_queue.get("queue_sequences", []))
    topology = by_name(refill_topology.get("topology", []))
    normal_refill = topology.get("normal_descriptor_queue_refill", {})

    stride = derived_state.get("stride_plus_0xb8")
    window = derived_state.get("state_plus_0xbc")
    bid_bytes = raster_case.get("payload_0x48")
    chunk_case = find_case(chunk_sizing.get("case_matrix", []), case)
    max_chunk_units = chunk_case.get("max_chunk_units_plus_0xcc")
    remaining_case = find_case(remaining_units.get("case_matrix_if_alias_holds", []), case)
    remaining_candidate = remaining_case.get("video_y_candidate_from_zji_0x12")
    candidate_channel_b_len = remaining_case.get("candidate_first_channel_b_length_if_alias_holds")

    stages = [
        {
            "stage": "host_raster_fields",
            "function": "ZjStream parser + JobMgr",
            "known_values": {
                "work +0x84": work_fields["+0x84"],
                "work +0x88": work_fields["+0x88"],
                "work +0x8c": work_fields["+0x8c"],
                "work +0x90": f"0x{work_fields['+0x90']:02x}",
                "payload +0x48": bid_bytes,
                "payload +0x54": "pointer to the same compressed BID bytes",
            },
            "meaning": "Host BIH/BID data is already enough to define page geometry and the first compressed raster payload.",
            "remaining_unknown": "exact physical meaning of every BIH option bit",
        },
        {
            "stage": "video_prepare_geometry",
            "function": "0x10014910 hp1020_video_prepare_page_candidate",
            "known_values": {
                "video state +0xb8 stride": stride,
                "video state +0xbc dual-output window": window,
                "video state +0xc4": derived_state.get("state_plus_0xc4"),
                "video state +0xf4": derived_state.get("state_plus_0xf4"),
                "video state +0xc8 / 200": derived_state.get("state_plus_0xc8_state_200"),
            },
            "meaning": "The current host cases land in the normal 600dpi setup family.",
            "remaining_unknown": "hardware-calibrated meaning of datastore 0x20 and less common prepare branches",
        },
        {
            "stage": "render_initial_transfer",
            "function": "0x10015214 hp1020_video_render_or_dma_candidate",
            "known_values": {
                "0xb2000008": work_fields["+0x84"],
                "0xb200000c": work_fields["+0x88"],
                "0xb2000024": work_fields["+0x8c"],
                "0xb2000000": "derived from work +0x90, then OR 0x400",
                "0xb2040004": "payload +0x54 compressed raster pointer",
                "0xb2040008": bid_bytes,
            },
            "meaning": "Render arms the first transfer using the host-derived geometry and first compressed raster buffer.",
            "remaining_unknown": "live completion timing for channel A progress",
        },
        {
            "stage": "helper_channel_b_refill",
            "function": "0x10014244 hp1020_video_band_done_or_irq_helper_candidate",
            "known_values": {
                "video state +0xcc max chunk units": max_chunk_units,
                "video state +0xd0 candidate if alias holds": remaining_candidate,
                "chunk_units": f"min({max_chunk_units}, video state +0xd0)",
                "0xb2080004": "slot pointer from video state + slot*4",
                "0xb2080008": f"min({max_chunk_units}, +0xd0) * stride({stride})",
                "0xb2080008 candidate if alias holds": candidate_channel_b_len,
                "final_flag": "set when remaining units become zero",
            },
            "meaning": "The helper keeps channel B fed from the modulo-4 descriptor side.",
            "remaining_unknown": "active work +0x26 remains unsourced; ZJI_VIDEO_Y reaches page-param +0x26 upstream, but the queue payload chain weakens that alias/copy theory",
        },
        {
            "stage": "raw_band_queue_feed",
            "function": "0x10013f34 hp1020_video_band_queue_or_list_candidate",
            "known_values": {
                "0xb1000008": "descriptor pointer/control source",
                "0xb1000108": f"A pointer plus dual-output window({window}) when dual-block mode is active",
                "0xb100000c": "encoded descriptor units plus final flag bit 0x18",
                "0xb100010c": "encoded descriptor units plus secondary output bit 0x19",
                "queue index +0xdc": "advances modulo 4 unless it would collide with +0xe0 without final flag",
            },
            "meaning": "This is the normal raw-band/channel feed boundary after render and refill helper setup.",
            "remaining_unknown": "exact encoding performed by 0x1001b668",
        },
        {
            "stage": "irq_refill_loop",
            "function": "0x100144d0 hp1020_video_irq_or_band_done_candidate",
            "known_values": {
                "band_done_bit": "0x20",
                "normal_path": "clear ring record, advance +0xd8, call helper, then queue/list next band",
                "alternate_path": "raw linked-list refresh when video state +0xfc is negative",
            },
            "meaning": "Actual printing depends on the video IRQ/band-done loop continuing this refill safely.",
            "remaining_unknown": "live interrupt cadence and exact stop/completion condition",
        },
    ]

    checks = [
        check("raster_fields_status_pass", raster_fields.get("status") == "pass", "raster field model is pass"),
        check("prepare_projection_status_pass", prepare_projection.get("status") == "pass", "prepare projection model is pass"),
        check("transfer_ring_status_pass", transfer_ring.get("status") == "pass", "transfer ring model is pass"),
        check("band_queue_status_pass", band_queue.get("status") == "pass", "band queue model is pass"),
        check("refill_topology_status_pass", refill_topology.get("status") == "pass", "refill topology model is pass"),
        check("chunk_sizing_status_pass", chunk_sizing.get("status") == "pass", "chunk sizing model is pass"),
        check("remaining_units_status_pass", remaining_units.get("status") == "pass", "remaining-units model is pass"),
        check(
            "a4_default_values_projected",
            work_fields == {"+0x84": 9600, "+0x88": 6824, "+0x8c": 128, "+0x90": 0x5C}
            and bid_bytes == 6364
            and stride == 1200
            and window == 2400
            and max_chunk_units == 4,
            "a4_default work/raster/prepare/chunk values match the current generated model",
        ),
        check(
            "normal_refill_path_preserved",
            "0xb2080004" in normal_refill.get("unsafe_registers", [])
            and "band_helper_refills_channel_b" in transfer_sequences
            and "raw_band_dual_block_write" in queue_sequences,
            "normal descriptor refill still connects channel-B helper and raw-band queue writes",
        ),
    ]

    status = "pass" if all(item["status"] == "present" for item in checks) else "fail"
    return {
        "summary": "Normal first-page video dataflow contract from host fields to render/refill hardware boundary.",
        "status": status,
        "source_case": case,
        "source_reports": {name: str(path.relative_to(ROOT_DIR)) for name, path in INPUTS.items()},
        "contract_stages": stages,
        "checks": checks,
        "current_conclusion": [
            "The host-to-render dataflow is now concrete for the generated a4_default case.",
            "The remaining unknowns are not parser fields; they are the active work +0x26 source, raw-band helper divide confirmation, video timing, and live IRQ completion behavior.",
            "This report is still not a reason to upload custom printing firmware; it is the static contract a future implementation must satisfy.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 Video Dataflow Contract",
        "",
        "This is a generated offline model. It does not contact the printer.",
        "",
        "## Result",
        "",
        f"- status: `{report['status']}`",
        f"- source case: `{report['source_case']}`",
        "- scope: normal first-page path from host raster fields through video render/refill hardware boundary",
        "",
        "## Source Reports",
        "",
    ]
    for name, source in report["source_reports"].items():
        lines.append(f"- `{name}`: `{source}`")

    lines.extend(["", "## Contract Stages", ""])
    for stage in report["contract_stages"]:
        lines.extend(
            [
                f"### `{stage['stage']}`",
                "",
                f"- function: `{stage['function']}`",
                f"- meaning: {stage['meaning']}",
                f"- remaining unknown: {stage['remaining_unknown']}",
                "",
                "| Field/Register | Value/Formula |",
                "|---|---|",
            ]
        )
        for key, value in stage["known_values"].items():
            lines.append(f"| `{key}` | `{value}` |")
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
    print(f"status={report['status']} checks={len(report['checks'])} stages={len(report['contract_stages'])}")
    print(OUT_MD)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
