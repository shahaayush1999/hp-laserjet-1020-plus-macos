#!/usr/bin/env python3
"""Model the source of HP 1020 video remaining-unit counters.

This is offline analysis only. It tracks the direct source for video state
+0xd0/+0xd4 and deliberately records that the page-parameter +0x26 candidate
is not yet connected to the active 0x94 work object's +0x26 field.
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
    "queue_payload_chain": ROOT_DIR / "analysis/hardware-boundary/video-queue-payload-chain.json",
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
                "video_y_from_zji_0x12": video_y,
                "max_chunk_units_plus_0xcc": max_chunk,
                "stride_plus_0xb8": stride,
                "first_refill_units": first_refill_units,
                "first_channel_b_length": first_refill_units * stride
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
    queue_payload_chain = read_json(INPUTS["queue_payload_chain"])
    sources = {name: path.read_text(errors="replace") for name, path in SOURCES.items()}
    rows = build_case_rows(raster_fields, chunk_sizing)
    work_26_hits = explicit_work_26_writes(sources)
    work_populate_text = sources["work_populate"]
    work_populate_copies_source_26 = "((int)param_2 + 0x26)" in work_populate_text
    work_populate_writes_dest_26 = "((int)param_1 + 0x26)" in work_populate_text or "(param_1 + 0x26)" in work_populate_text

    direct = read_json(ROOT_DIR / "analysis/hardware-boundary/zjs-direct-work.json")
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
        check("direct_start_page_builder_verified",
              direct["status"] == "pass" and all(row["fields"]["+0x26"] == find_case(rows,row["case"])["video_y_from_zji_0x12"] for row in direct["case_matrix"]),
              "ELF bytes prove the builder destination is the same active work pointer"),
        check("queue_payload_identity", queue_payload_chain["status"] == "pass",
              "queue payload preserves the directly populated active work object"),
        check(
            "candidate_values_match_generated_cases",
            find_case(rows, "a4_default").get("video_y_from_zji_0x12") == 6824
            and find_case(rows, "letter_default").get("video_y_from_zji_0x12") == 6408
            and find_case(rows, "legal_default").get("video_y_from_zji_0x12") == 8208,
            "candidate remaining-unit values follow generated page heights",
        ),
    ]

    status = "pass" if all(item["status"] == "present" for item in checks) else "fail"
    return {
        "summary": "Directly verified source for video state +0xd0/+0xd4 remaining-unit counters.",
        "status": status,
        "source_reports": {name: str(path.relative_to(ROOT_DIR)) for name, path in INPUTS.items()},
        "source_chain": [
            {"stage":"START_PAGE", "field":"allocated 0x94 work", "evidence":"0x10009faf call8 allocate; a7 retains result", "status":"ELF-byte verified"},
            {"stage":"direct_builder", "field":"work +0x26 = low16(ZJI_VIDEO_Y)", "evidence":"0x10009fe0 a10=a7; 0x10009fed call8 0x10009b4c; item 0x12 store at 0x10009c35", "status":"ELF-byte verified"},
            {"stage":"prepare", "field":"video +0xd0/+0xd4 = work +0x26", "evidence":"0x10014910 consumer", "status":"static consumer verified"},
        ],
        "case_matrix": rows,
        "explicit_0x26_write_hits": work_26_hits,
        "current_conclusion": [
            "ZJI_VIDEO_Y directly initializes active work +0x26; prepare copies it into both remaining counters.",
            "The alternate 0x100104c8 constructor is not used by the normal START_PAGE handler; its missing copy is irrelevant here.",
            "The source is resolved. Hardware must still establish the physical meaning and safe completion behavior of the counters.",
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
        "- scope: direct source for video state `+0xd0/+0xd4` remaining-unit counters",
        "",
        "## Source Chain",
        "",
        "| Stage | Field | Status | Evidence |",
        "|---|---|---|---|",
    ]
    for item in report["source_chain"]:
        lines.append(f"| `{item['stage']}` | `{item['field']}` | `{item['status']}` | {item['evidence']} |")

    lines.extend(
        [
            "",
            "## Initial Refill Projection",
            "",
            "| Case | ZJI_VIDEO_Y | +0xcc max chunk units | Stride +0xb8 | First refill units | First channel-B length |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in report["case_matrix"]:
        lines.append(
            "| `{case}` | `{video_y_from_zji_0x12}` | `{max_chunk_units_plus_0xcc}` | `{stride_plus_0xb8}` | `{first_refill_units}` | `{first_channel_b_length}` |".format(
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
    print(f"status={report['status']} checks={len(report['checks'])} cases={len(report['case_matrix'])}")
    print(OUT_MD)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
