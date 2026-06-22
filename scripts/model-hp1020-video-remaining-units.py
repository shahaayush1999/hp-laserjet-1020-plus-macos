#!/usr/bin/env python3
"""Model the source of HP 1020 video remaining-unit counters.

This is offline analysis only. It tracks the candidate source for video state
+0xd0/+0xd4 and deliberately records the unresolved gap between page-parameter
+0x26 and the active video work object's +0x26 field.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT_DIR / "analysis/hardware-boundary/video-remaining-units.json"
OUT_MD = ROOT_DIR / "analysis/hardware-boundary/video-remaining-units.md"

INPUTS = {
    "raster_fields": ROOT_DIR / "analysis/open-firmware-model/raster-field-semantics.json",
    "chunk_sizing": ROOT_DIR / "analysis/hardware-boundary/video-chunk-sizing.json",
}

SOURCES = {
    "page_param_builder": ROOT_DIR / "analysis/jobmgr-producer-boundary/decompiled/10009b4c_FUN_10009b4c.c",
    "work_populate": ROOT_DIR / "analysis/video-work-object/decompiled/100104c8_hp1020_work_populate_from_page_params_candidate.c",
    "work_init": ROOT_DIR / "analysis/video-work-object/decompiled/1000f204_hp1020_work_common_init_candidate.c",
    "work_create": ROOT_DIR / "analysis/video-work-object/decompiled/1000f228_hp1020_video_work_create_candidate.c",
    "prepare": ROOT_DIR / "analysis/dispatch-mmio/decompiled/10014910_hp1020_video_prepare_page_candidate.c",
    "jobmgr": ROOT_DIR / "analysis/video-work-object/decompiled/1000e414_hp1020_job_mgr_thread_candidate.c",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def check(name: str, ok: bool, detail: str) -> dict[str, str]:
    return {"name": name, "status": "present" if ok else "missing", "detail": detail}


def find_case(rows: list[dict[str, Any]], case_name: str) -> dict[str, Any]:
    for row in rows:
        if row.get("case") == case_name:
            return row
    return {}


def parse_video_y(row: dict[str, Any]) -> int | None:
    value = row.get("video_xy")
    if not isinstance(value, str) or "/" not in value:
        return None
    return int(value.split("/", 1)[1])


def build_case_rows(raster_fields: dict[str, Any], chunk_sizing: dict[str, Any]) -> list[dict[str, Any]]:
    chunk_by_case = {
        item.get("case"): item
        for item in chunk_sizing.get("case_matrix", [])
        if isinstance(item, dict)
    }
    rows = []
    for item in raster_fields.get("case_matrix", []):
        video_y = parse_video_y(item)
        chunk = chunk_by_case.get(item.get("case"), {})
        max_chunk = chunk.get("max_chunk_units_plus_0xcc")
        stride = chunk.get("stride_plus_0xb8")
        first_refill_units = min(max_chunk, video_y) if isinstance(max_chunk, int) and isinstance(video_y, int) else None
        rows.append(
            {
                "case": item.get("case"),
                "video_y_candidate_from_zji_0x12": video_y,
                "max_chunk_units_plus_0xcc": max_chunk,
                "stride_plus_0xb8": stride,
                "candidate_first_refill_units_if_alias_holds": first_refill_units,
                "candidate_first_channel_b_length_if_alias_holds": first_refill_units * stride
                if isinstance(first_refill_units, int) and isinstance(stride, int)
                else None,
            }
        )
    return rows


def explicit_work_26_writes(sources: dict[str, str]) -> list[dict[str, str]]:
    hits = []
    for name, text in sources.items():
        for line_no, line in enumerate(text.splitlines(), start=1):
            compact = line.strip()
            if "+ 0x26" in compact or "+0x26" in compact:
                if "=" in compact:
                    hits.append({"source": name, "line": line_no, "text": compact})
    return hits


def build_report() -> dict[str, Any]:
    raster_fields = read_json(INPUTS["raster_fields"])
    chunk_sizing = read_json(INPUTS["chunk_sizing"])
    sources = {name: path.read_text(errors="replace") for name, path in SOURCES.items()}
    rows = build_case_rows(raster_fields, chunk_sizing)
    work_26_hits = explicit_work_26_writes(sources)
    work_populate_text = sources["work_populate"]
    work_populate_copies_source_26 = "((int)param_2 + 0x26)" in work_populate_text
    work_populate_writes_dest_26 = "((int)param_1 + 0x26)" in work_populate_text or "(param_1 + 0x26)" in work_populate_text

    checks = [
        check(
            "page_param_builder_maps_zji_video_y_to_0x26",
            "case 0x12:" in sources["page_param_builder"]
            and "*(undefined2 *)(param_1 + 0x26) = *(undefined2 *)((int)param_2 + 10)" in sources["page_param_builder"],
            "page parameter builder stores item id 0x12, ZJI_VIDEO_Y, into page-param +0x26",
        ),
        check(
            "prepare_reads_work_0x26_to_remaining_counters",
            "*(uint *)(puVar15 + 0xd0) = (uint)*(ushort *)(param_1 + 0x26)" in sources["prepare"]
            and "*(uint *)(puVar15 + 0xd4) = (uint)*(ushort *)(param_1 + 0x26)" in sources["prepare"],
            "video prepare copies active parameter +0x26 into video state +0xd0/+0xd4",
        ),
        check(
            "simple_work_populate_does_not_copy_0x26",
            not work_populate_copies_source_26 and not work_populate_writes_dest_26,
            "0x100104c8 does not visibly copy page-param +0x26 into work +0x26",
        ),
        check(
            "work_common_init_clears_early_body",
            "FUN_1001b4c8(param_1,0,0x46)" in sources["work_init"],
            "common initializer clears the early work-object body, including +0x26 unless later populated",
        ),
        check(
            "current_search_keeps_gap_explicit",
            len(work_26_hits) >= 2,
            "explicit +0x26 hits are builder and prepare paths; no direct work-populate copy is currently visible",
        ),
        check(
            "candidate_values_match_generated_cases",
            find_case(rows, "a4_default").get("video_y_candidate_from_zji_0x12") == 6824
            and find_case(rows, "letter_default").get("video_y_candidate_from_zji_0x12") == 6408
            and find_case(rows, "legal_default").get("video_y_candidate_from_zji_0x12") == 8208,
            "candidate remaining-unit values follow generated page heights",
        ),
    ]

    status = "pass" if all(item["status"] == "present" for item in checks) else "fail"
    return {
        "summary": "Candidate source and unresolved copy gap for video state +0xd0/+0xd4 remaining-unit counters.",
        "status": status,
        "source_reports": {name: str(path.relative_to(ROOT_DIR)) for name, path in INPUTS.items()},
        "candidate_chain": [
            {
                "stage": "host_page_item",
                "field": "ZJI_VIDEO_Y / item id 0x12",
                "evidence": "generated ZjStream page item values and page-parameter builder switch case 0x12",
                "status": "candidate source",
            },
            {
                "stage": "page_parameter_builder",
                "field": "page-param +0x26",
                "evidence": "0x10009b4c writes item value at param_2 + 10 into param_1 +0x26",
                "status": "proven for page-parameter object",
            },
            {
                "stage": "active_video_parameter",
                "field": "prepare param_1 +0x26",
                "evidence": "0x10014910 reads param_1 +0x26 into video state +0xd0/+0xd4",
                "status": "proven consumer",
            },
            {
                "stage": "copy_or_alias_gap",
                "field": "page-param +0x26 -> active work/prepare +0x26",
                "evidence": "0x100104c8 simple copier does not visibly copy +0x26; current explicit-source scan finds no direct work-object writer",
                "status": "unresolved",
            },
        ],
        "case_matrix_if_alias_holds": rows,
        "explicit_0x26_write_hits": work_26_hits,
        "current_conclusion": [
            "The best static source candidate for +0xd0/+0xd4 is ZJI_VIDEO_Y through page-param +0x26.",
            "The direct copy or alias from page-param +0x26 into the active video prepare argument is not proven in current decompilation.",
            "Open firmware planning may use the generated candidate values, but implementation should keep this as a calibrated field until the copy/alias gap is closed.",
        ],
        "checks": checks,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 Video Remaining Units",
        "",
        "This is a generated offline model. It does not contact the printer.",
        "",
        "## Result",
        "",
        f"- status: `{report['status']}`",
        "- scope: candidate source for video state `+0xd0/+0xd4` remaining-unit counters",
        "",
        "## Candidate Chain",
        "",
        "| Stage | Field | Status | Evidence |",
        "|---|---|---|---|",
    ]
    for item in report["candidate_chain"]:
        lines.append(f"| `{item['stage']}` | `{item['field']}` | `{item['status']}` | {item['evidence']} |")

    lines.extend(
        [
            "",
            "## Projection If Alias Holds",
            "",
            "| Case | ZJI_VIDEO_Y candidate | +0xcc max chunk units | Stride +0xb8 | First refill units | First channel-B length |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in report["case_matrix_if_alias_holds"]:
        lines.append(
            "| `{case}` | `{video_y_candidate_from_zji_0x12}` | `{max_chunk_units_plus_0xcc}` | `{stride_plus_0xb8}` | `{candidate_first_refill_units_if_alias_holds}` | `{candidate_first_channel_b_length_if_alias_holds}` |".format(
                **row
            )
        )

    lines.extend(["", "## Explicit `+0x26` Write Hits", "", "| Source | Line | Text |", "|---|---:|---|"])
    for hit in report["explicit_0x26_write_hits"]:
        lines.append(f"| `{hit['source']}` | `{hit['line']}` | `{hit['text']}` |")

    lines.extend(["", "## Current Conclusion", ""])
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
    print(f"status={report['status']} checks={len(report['checks'])} cases={len(report['case_matrix_if_alias_holds'])}")
    print(OUT_MD)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
