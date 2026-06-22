#!/usr/bin/env python3
"""Model the stock pointer chain that hands page work to VideoThread.

This is offline analysis only. It clarifies which object reaches
0x10014910 hp1020_video_prepare_page_candidate.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT_DIR / "analysis/hardware-boundary/video-queue-payload-chain.json"
OUT_MD = ROOT_DIR / "analysis/hardware-boundary/video-queue-payload-chain.md"

SOURCES = {
    "job_record_create": ROOT_DIR
    / "analysis/jobmgr-producer-boundary/decompiled/10010338_hp1020_job_record_create_and_enqueue_candidate.c",
    "child_page_create": ROOT_DIR
    / "analysis/jobmgr-producer-boundary/decompiled/10010398_hp1020_child_page_record_create_candidate.c",
    "work_create": ROOT_DIR / "analysis/video-work-object/decompiled/1000f228_hp1020_video_work_create_candidate.c",
    "work_populate": ROOT_DIR
    / "analysis/video-work-object/decompiled/100104c8_hp1020_work_populate_from_page_params_candidate.c",
    "job_mgr": ROOT_DIR / "analysis/video-work-object/decompiled/1000e414_hp1020_job_mgr_thread_candidate.c",
    "engine_dispatch": ROOT_DIR / "analysis/dispatch-mmio/decompiled/10016164_hp1020_engine_message_dispatch_candidate.c",
    "print_mgr_schedule": ROOT_DIR
    / "analysis/queue-send-census/decompiled/1000f574_hp1020_print_mgr_schedule_or_advance_candidate.c",
    "queue_wrapper": ROOT_DIR / "analysis/queue-send-census/decompiled/10010218_hp1020_queue_send_message4_candidate.c",
    "video_thread": ROOT_DIR / "analysis/dispatch-mmio/decompiled/10013c18_hp1020_video_thread_candidate.c",
    "prepare": ROOT_DIR / "analysis/dispatch-mmio/decompiled/10014910_hp1020_video_prepare_page_candidate.c",
    "page_param_builder": ROOT_DIR / "analysis/jobmgr-producer-boundary/decompiled/10009b4c_FUN_10009b4c.c",
}


def read_text(path: Path) -> str:
    return path.read_text(errors="replace")


def check(name: str, ok: bool, detail: str) -> dict[str, str]:
    return {"name": name, "status": "present" if ok else "missing", "detail": detail}


def find_write_hits(sources: dict[str, str], offset: str) -> list[dict[str, Any]]:
    pattern = re.compile(rf"\+\s*{re.escape(offset)}\b|\+{re.escape(offset)}\b")
    hits = []
    for source, text in sources.items():
        for line_no, line in enumerate(text.splitlines(), start=1):
            if pattern.search(line):
                compact = line.strip()
                if "=" in compact:
                    hits.append({"source": source, "line": line_no, "text": compact})
    return hits


def build_report() -> dict[str, Any]:
    sources = {name: read_text(path) for name, path in SOURCES.items()}
    write_26_hits = find_write_hits(sources, "0x26")
    work_geometry_writes = [
        hit
        for offset in ("0x84", "0x88", "0x8c", "0x90")
        for hit in find_write_hits({"job_mgr": sources["job_mgr"], "work_create": sources["work_create"]}, offset)
    ]

    stages = [
        {
            "stage": "page_parameter_block",
            "function": "0x10009b4c",
            "object": "page parameter block",
            "evidence": "builder writes ZJI item 0x12 into page-param +0x26",
            "confidence": "high for page-param object only",
        },
        {
            "stage": "work_object_creation",
            "function": "0x10010398 -> 0x1000f228 -> 0x100104c8",
            "object": "0x94-byte video/page work object",
            "evidence": "child-page creator allocates work, copies selected fields, then sends JobMgr message 5 with the work pointer",
            "confidence": "high",
        },
        {
            "stage": "raster_geometry_fill",
            "function": "0x1000e414",
            "object": "same work object",
            "evidence": "JobMgr writes BIH/runtime block values into work +0x84/+0x88/+0x8c/+0x90",
            "confidence": "high",
        },
        {
            "stage": "engine_queue_handoff",
            "function": "0x1000e414 -> queue 1 message 0x0b",
            "object": "work pointer in message word 4",
            "evidence": "JobMgr stores iVar9 in iStack_84 and sends engine queue message 0x0b",
            "confidence": "medium-high",
        },
        {
            "stage": "engine_active_work",
            "function": "0x10016164",
            "object": "engine state +0x68 active work pointer",
            "evidence": "engine dispatch stores param_1[3] into engine state +0x68 for message 0x0b/0x40",
            "confidence": "high",
        },
        {
            "stage": "print_mgr_video_send",
            "function": "0x1000f574 -> 0x10010218",
            "object": "work pointer in message word 4",
            "evidence": "PrintMgr sends queue 8 message 0x0b with uVar10, and wrapper places param_5 into uStack_24",
            "confidence": "medium-high",
        },
        {
            "stage": "video_thread_prepare",
            "function": "0x10013c18 -> 0x10014910",
            "object": "VideoThread active work pointer",
            "evidence": "VideoThread receives message 0x0b, stores uStack_24 at video state +0x60, and calls prepare(piVar3)",
            "confidence": "high",
        },
    ]

    checks = [
        check(
            "work_object_is_allocated_before_jobmgr_message_5",
            "iVar2 = FUN_1000f228()" in sources["child_page_create"]
            and "FUN_100104c8(iVar2,param_1)" in sources["child_page_create"]
            and "local_30[0] = 5" in sources["child_page_create"],
            "child-page create path creates a 0x94 work object and sends it to JobMgr as message 5",
        ),
        check(
            "work_create_allocates_0x94_and_clears_video_fields",
            "hp1020_alloc_with_retry_candidate(0x94,1)" in sources["work_create"]
            and "*(undefined4 *)(iVar1 + 0x84) = 0" in sources["work_create"]
            and "*(undefined1 *)(iVar1 + 0x90) = 0" in sources["work_create"],
            "work creator allocates the object that later gets video geometry fields",
        ),
        check(
            "work_populate_does_not_copy_page_param_0x26",
            "((int)param_2 + 0x26)" not in sources["work_populate"]
            and "((int)param_1 + 0x26)" not in sources["work_populate"]
            and "(param_1 + 0x26)" not in sources["work_populate"],
            "selected page-param copier still does not copy +0x26 into the work object",
        ),
        check(
            "jobmgr_fills_work_video_geometry",
            "*(undefined4 *)(iVar9 + 0x84) = *(undefined4 *)(PTR_DAT_10006304 + 4)" in sources["job_mgr"]
            and "*(undefined4 *)(iVar9 + 0x88) = *(undefined4 *)(puVar4 + 8)" in sources["job_mgr"]
            and "*(undefined4 *)(iVar9 + 0x8c) = *(undefined4 *)(puVar4 + 0xc)" in sources["job_mgr"]
            and "*(undefined *)(iVar9 + 0x90) = puVar4[0x13]" in sources["job_mgr"],
            "JobMgr fills the same work object fields consumed by video prepare/render",
        ),
        check(
            "jobmgr_sends_engine_0x0b_with_work_pointer",
            "uStack_90 = 0xb" in sources["job_mgr"]
            and "iStack_84 = iVar9" in sources["job_mgr"]
            and "hp1020_queue_send_candidate(1,&uStack_90)" in sources["job_mgr"],
            "JobMgr sends engine queue 0x0b with the candidate work pointer in the fourth message word",
        ),
        check(
            "engine_dispatch_stores_active_work_pointer",
            "case 0xb:" in sources["engine_dispatch"]
            and "*(undefined4 *)(puVar2 + 0x68) = param_1[3]" in sources["engine_dispatch"],
            "engine dispatch stores queue message word 4 as active work pointer",
        ),
        check(
            "printmgr_sends_video_queue_payload_word",
            "hp1020_queue_send_message4_candidate(8,0xb,0,0,uVar10)" in sources["print_mgr_schedule"]
            and "uStack_24 = param_5" in sources["queue_wrapper"],
            "PrintMgr sends Video Queue 0x0b with the same payload slot shape",
        ),
        check(
            "video_thread_uses_payload_as_prepare_argument",
            "*(undefined4 *)(puVar1 + 0x60) = uStack_24" in sources["video_thread"]
            and "piVar3 = *(int **)(puVar1 + 0x60)" in sources["video_thread"]
            and "hp1020_video_prepare_page_candidate(piVar3)" in sources["video_thread"],
            "VideoThread stores message word 4 as active work and passes it to prepare",
        ),
        check(
            "prepare_reads_both_geometry_and_0x26_from_same_argument",
            "(*(int *)(param_1 + 0x84) + 0x1fU & 0xffffffe0) >> 3" in sources["prepare"]
            and "*(uint *)(puVar15 + 0xd0) = (uint)*(ushort *)(param_1 + 0x26)" in sources["prepare"],
            "prepare reads +0x84 geometry and +0x26 remaining-units field from the same argument",
        ),
    ]

    status = "pass" if all(item["status"] == "present" for item in checks) else "fail"
    return {
        "summary": "Static queue/pointer chain for the object consumed by VideoThread prepare.",
        "status": status,
        "stages": stages,
        "write_hits": {
            "plus_0x26": write_26_hits,
            "video_geometry": work_geometry_writes,
        },
        "conclusion": {
            "prepare_argument_identity": "0x94-byte video/page work object",
            "effect_on_remaining_units": "current static evidence weakens the earlier page-param +0x26 -> work +0x26 alias theory; the active work +0x26 source remains unresolved",
            "plain_english": "The video code is almost certainly receiving the work object whose geometry is filled by JobMgr. The page-height value is proven in the earlier page-param block, but this chain does not show it being copied into the work object field that prepare reads.",
        },
        "checks": checks,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 Video Queue Payload Chain",
        "",
        "This generated report is offline only. It does not contact the printer.",
        "",
        "## Result",
        "",
        f"- status: `{report['status']}`",
        f"- prepare argument identity: `{report['conclusion']['prepare_argument_identity']}`",
        f"- remaining-unit impact: {report['conclusion']['effect_on_remaining_units']}",
        "",
        "## Plain-English Meaning",
        "",
        report["conclusion"]["plain_english"],
        "",
        "## Pointer Chain",
        "",
        "| Stage | Function | Object | Confidence | Evidence |",
        "|---|---|---|---|---|",
    ]
    for stage in report["stages"]:
        lines.append(
            f"| `{stage['stage']}` | `{stage['function']}` | {stage['object']} | `{stage['confidence']}` | {stage['evidence']} |"
        )

    lines.extend(["", "## `+0x26` Write Hits", "", "| Source | Line | Text |", "|---|---:|---|"])
    for hit in report["write_hits"]["plus_0x26"]:
        lines.append(f"| `{hit['source']}` | `{hit['line']}` | `{hit['text']}` |")

    lines.extend(["", "## Work Geometry Writes", "", "| Source | Line | Text |", "|---|---:|---|"])
    for hit in report["write_hits"]["video_geometry"]:
        lines.append(f"| `{hit['source']}` | `{hit['line']}` | `{hit['text']}` |")

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
    print(f"status={report['status']} checks={len(report['checks'])} stages={len(report['stages'])}")
    print(f"wrote {OUT_MD.relative_to(ROOT_DIR)}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
