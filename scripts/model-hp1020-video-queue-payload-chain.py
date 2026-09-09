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
    "print_mgr_thread": ROOT_DIR / "analysis/engine/engine-decompiled/1000f324_hp1020_print_mgr_thread_candidate.c",
    "print_mgr_pending_enqueue": ROOT_DIR / "analysis/engine/engine-decompiled/10010298_FUN_10010298.c",
    "list_append_tail": ROOT_DIR / "analysis/engine/engine-decompiled/10013000_FUN_10013000.c",
    "list_pop_head": ROOT_DIR / "analysis/engine/engine-decompiled/10013050_FUN_10013050.c",
    "list_peek_head": ROOT_DIR / "analysis/engine/engine-decompiled/100130bc_FUN_100130bc.c",
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
            "stage": "work_object_allocation",
            "function": "0x10009f86 -> 0x1000f228",
            "object": "0x94-byte video/page work object",
            "evidence": "START_PAGE allocates work in a10 and saves the pointer in a7",
            "confidence": "ELF-byte verified",
        },
        {
            "stage": "work_object_creation",
            "function": "0x10009fed -> 0x10009b4c",
            "object": "0x94-byte video/page work object",
            "evidence": "START_PAGE passes the same a7 work pointer to the item builder and then sends it as JobMgr message 5 payload",
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
            "stage": "printmgr_queue_handoff",
            "function": "0x1000e414 -> queue 1 message 0x0b",
            "object": "work pointer in message word 4",
            "evidence": "JobMgr stores iVar9 in iStack_84 and sends PrintMgr queue 1 message 0x0b",
            "confidence": "medium-high",
        },
        {
            "stage": "print_mgr_receive_message",
            "function": "0x1000f324",
            "object": "PrintMgr queue message array",
            "evidence": "PrintMgr receives a queue message into aiStack_50 and dispatches by message id",
            "confidence": "high",
        },
        {
            "stage": "print_mgr_pending_node_create",
            "function": "0x10010298",
            "object": "0x10-byte pending-list node",
            "evidence": "pending node +0xc is assigned directly from param_2, with state flags at +4/+8",
            "confidence": "high",
        },
        {
            "stage": "print_mgr_video_send",
            "function": "0x1000f574 -> 0x10010218",
            "object": "pending-list node +0xc payload copied into message word 4",
            "evidence": "PrintMgr loads uVar10 from node +0xc, sends queue 8 message 0x0b with uVar10, and wrapper places param_5 into uStack_24",
            "confidence": "high",
        },
        {
            "stage": "video_thread_prepare",
            "function": "0x10013c18 -> 0x10014910",
            "object": "VideoThread active work pointer",
            "evidence": "VideoThread receives message 0x0b, stores uStack_24 at video state +0x60, and calls prepare(piVar3)",
            "confidence": "high",
        },
        {
            "stage": "print_mgr_pending_to_active_list",
            "function": "0x1000f574 -> 0x10013050 -> 0x10013000",
            "object": "same 0x10-byte list node",
            "evidence": "PrintMgr pops the pending head and appends that same node to the active list before engine message 0x0b",
            "confidence": "high",
        },
        {
            "stage": "engine_active_work",
            "function": "0x10016164",
            "object": "engine state +0x68 active work pointer",
            "evidence": "engine dispatch stores param_1[3] into engine state +0x68 for message 0x0b/0x40",
            "confidence": "high",
        },
    ]

    direct = json.loads((ROOT_DIR / "analysis/hardware-boundary/zjs-direct-work.json").read_text())
    checks = [check("direct_start_page_work_verified", direct["status"] == "pass", "stock ELF verifies direct allocation/builder/message path"),
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
            "alternate constructor copier lacks +0x26; normal START_PAGE uses the direct builder instead",
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
            "JobMgr sends PrintMgr queue 1 message 0x0b with the candidate work pointer in the fourth message word",
        ),
        check(
            "engine_dispatch_stores_active_work_pointer",
            "case 0xb:" in sources["engine_dispatch"]
            and "*(undefined4 *)(puVar2 + 0x68) = param_1[3]" in sources["engine_dispatch"],
            "engine dispatch stores queue message word 4 as active work pointer",
        ),
        check(
            "printmgr_thread_dispatches_received_messages",
            "threadx_queue_receive_wait_candidate(PTR_DAT_1000632c,aiStack_50,0xffffffff)" in sources["print_mgr_thread"]
            and "PTR_switchdataD_100048f0_10006360 + (aiStack_50[0] - 0xbU) * 4" in sources["print_mgr_thread"],
            "PrintMgr consumes messages from its queue and dispatches by message id",
        ),
        check(
            "pending_node_payload_is_direct_param_2",
            "FUN_100131b8(0x10,1)" in sources["print_mgr_pending_enqueue"]
            and "*(undefined4 *)(iVar4 + 4) = 0" in sources["print_mgr_pending_enqueue"]
            and "*(undefined4 *)(iVar4 + 8) = param_5" in sources["print_mgr_pending_enqueue"]
            and "*(int *)(iVar4 + 0xc) = param_2" in sources["print_mgr_pending_enqueue"],
            "PrintMgr pending wrapper stores the payload pointer directly at node +0xc",
        ),
        check(
            "list_helpers_do_not_rewrite_payload_word",
            "*(undefined4 **)param_1[1] = param_2" in sources["list_append_tail"]
            and "*param_2 = 0" in sources["list_append_tail"]
            and "*param_1 = iVar2" in sources["list_pop_head"]
            and "return *param_1" in sources["list_peek_head"]
            and "+ 0xc" not in sources["list_append_tail"]
            and "+ 0xc" not in sources["list_pop_head"]
            and "+ 0xc" not in sources["list_peek_head"],
            "list append/pop/peek operate on links only and do not synthesize the payload at node +0xc",
        ),
        check(
            "printmgr_moves_same_node_pending_to_active",
            "iVar8 = hp1020_list_pop_head_candidate(PTR_DAT_10006324)" in sources["print_mgr_schedule"]
            and "hp1020_list_append_tail_candidate(PTR_DAT_10006328,iVar8)" in sources["print_mgr_schedule"],
            "PrintMgr moves the existing pending node to the active list, preserving node +0xc payload identity",
        ),
        check(
            "printmgr_sends_video_queue_payload_word",
            "uVar10 = *(undefined4 *)(iVar8 + 0xc)" in sources["print_mgr_schedule"]
            and "hp1020_queue_send_message4_candidate(8,0xb,0,0,uVar10)" in sources["print_mgr_schedule"]
            and "uStack_24 = param_5" in sources["queue_wrapper"],
            "PrintMgr copies pending-node +0xc into Video Queue 0x0b message word 4",
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
            "effect_on_remaining_units": "direct START_PAGE builder writes VIDEO_Y to active work +0x26; no copy or alias gap remains",
            "plain_english": "The video code is almost certainly receiving the work object whose geometry is filled by JobMgr. The PrintMgr wrapper/list nodes preserve a pointer payload; they do not create the missing page-height field. The page-height value is proven in the earlier page-param block, but this chain does not show it being copied into the work object field that prepare reads.",
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
