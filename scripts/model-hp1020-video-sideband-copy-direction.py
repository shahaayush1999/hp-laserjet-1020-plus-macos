#!/usr/bin/env python3
"""Model the copy direction for the JobMgr sideband/runtime-block memcpy.

This is offline analysis only. The goal is to rule in/out one possible hidden
source for active work +0x26/+0x30/+0x32.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT_DIR / "analysis/hardware-boundary/video-sideband-copy-direction.json"
OUT_MD = ROOT_DIR / "analysis/hardware-boundary/video-sideband-copy-direction.md"

SOURCES = {
    "memcpy_helper": ROOT_DIR / "analysis/message-producers/producer-decompiled/1001b38c_FUN_1001b38c.c",
    "job_mgr": ROOT_DIR / "analysis/video-work-object/decompiled/1000e414_hp1020_job_mgr_thread_candidate.c",
    "datastore_write": ROOT_DIR / "analysis/data-store/data-store-decompiled/10010fd0_hp1020_datastore_write_notify_unlock_candidate.c",
    "datastore_read": ROOT_DIR / "analysis/data-store/data-store-decompiled/10010f54_hp1020_datastore_read_locked_candidate.c",
    "prepare_fields": ROOT_DIR / "analysis/hardware-boundary/video-prepare-argument-fields.json",
}


def read_text(path: Path) -> str:
    return path.read_text(errors="replace")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def check(name: str, ok: bool, detail: str) -> dict[str, str]:
    return {"name": name, "status": "present" if ok else "missing", "detail": detail}


def build_report() -> dict[str, Any]:
    sources = {name: read_text(path) for name, path in SOURCES.items() if name != "prepare_fields"}
    prepare_fields = read_json(SOURCES["prepare_fields"])

    memcpy_direction_evidence = [
        {
            "snippet": "uVar1 = *param_2;",
            "meaning": "read one byte from second argument",
            "present": "uVar1 = *param_2;" in sources["memcpy_helper"],
        },
        {
            "snippet": "*param_1 = uVar1;",
            "meaning": "write one byte to first argument",
            "present": "*param_1 = uVar1;" in sources["memcpy_helper"],
        },
        {
            "snippet": "param_2 = param_2 + 1;",
            "meaning": "advance source pointer",
            "present": "param_2 = param_2 + 1;" in sources["memcpy_helper"],
        },
        {
            "snippet": "param_1 = param_1 + 1;",
            "meaning": "advance destination pointer",
            "present": "param_1 = param_1 + 1;" in sources["memcpy_helper"],
        },
    ]

    sideband_call = {
        "function": "0x1000e414 hp1020_job_mgr_thread_candidate",
        "call": "FUN_1001b38c(PTR_DAT_10006304,iStack_84,0x14)",
        "interpreted_as": "memcpy(dst=PTR_DAT_10006304 runtime block, src=iStack_84 BIH payload, len=0x14)",
        "effect": "copies the 20-byte BIH payload out to the runtime block; does not fill active work +0x26/+0x30/+0x32",
        "present": "FUN_1001b38c(PTR_DAT_10006304,iStack_84,0x14)" in sources["job_mgr"],
    }

    direction_comparators = [
        {
            "function": "0x10010fd0 datastore write",
            "call": "FUN_1001b38c(piVar3[1],param_1[1],*(undefined2 *)(piVar3 + 4))",
            "interpreted_as": "copy caller data into datastore slot",
            "present": "FUN_1001b38c(piVar3[1],param_1[1],*(undefined2 *)(piVar3 + 4))"
            in sources["datastore_write"],
        },
        {
            "function": "0x10010f54 datastore read",
            "call": "FUN_1001b38c(param_1[1],*(undefined4 *)(puVar1 + iVar2 * 0x18 + 4)",
            "interpreted_as": "copy datastore slot into caller buffer",
            "present": "FUN_1001b38c(param_1[1],*(undefined4 *)(puVar1 + iVar2 * 0x18 + 4)"
            in sources["datastore_read"],
        },
    ]

    unsourced_fields = [
        field.get("field")
        for field in prepare_fields.get("fields", [])
        if isinstance(field, dict) and field.get("source_status") == "unsourced_active_work"
    ]

    checks = [
        check(
            "memcpy_helper_direction_is_dest_src_len",
            all(item["present"] for item in memcpy_direction_evidence),
            "0x1001b38c decompile shows reads from param_2 and writes to param_1 before the bad-instruction tail",
        ),
        check(
            "jobmgr_sideband_copy_is_work_to_runtime_block",
            sideband_call["present"],
            "JobMgr case 0x29 call copies iStack_84 BIH payload into PTR_DAT_10006304 when interpreted with dest,src,len order",
        ),
        check(
            "datastore_comparators_match_direction",
            all(item["present"] for item in direction_comparators),
            "datastore read/write callers agree with dest,src,len direction",
        ),
        check(
            "sidebands_resolved_by_direct_builder",
            set(unsourced_fields) == set(),
            "direct START_PAGE item builder sources +0x26/+0x30/+0x32; the BIH copy is separate",
        ),
    ]

    status = "pass" if all(item["status"] == "present" for item in checks) else "fail"
    return {
        "summary": "Copy direction for JobMgr runtime-block sideband memcpy candidate.",
        "status": status,
        "helper": {
            "function": "0x1001b38c",
            "working_name": "memcpy_candidate",
            "argument_order": "destination, source, length",
            "limitation": "decompiler still truncates later optimized copy loop on old Xtensa instructions, but the byte prologue and callers are enough to pin argument direction",
        },
        "memcpy_direction_evidence": memcpy_direction_evidence,
        "sideband_call": sideband_call,
        "direction_comparators": direction_comparators,
        "effect_on_prepare_fields": {
            "ruled_out_hidden_source": "0x1000e414 case 0x29 memcpy does not copy PTR_DAT_10006304 into the active work object",
            "still_unsourced": unsourced_fields,
        },
        "checks": checks,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 Video Sideband Copy Direction",
        "",
        "This generated report is offline only. It does not contact the printer.",
        "",
        "## Result",
        "",
        f"- status: `{report['status']}`",
        f"- helper: `{report['helper']['function']}` `{report['helper']['working_name']}`",
        f"- argument order: `{report['helper']['argument_order']}`",
        f"- limitation: {report['helper']['limitation']}",
        "",
        "## Sideband Copy Call",
        "",
        f"- call: `{report['sideband_call']['call']}`",
        f"- interpreted as: `{report['sideband_call']['interpreted_as']}`",
        f"- effect: {report['sideband_call']['effect']}",
        "",
        "## Direction Evidence",
        "",
        "| Snippet | Present | Meaning |",
        "|---|---|---|",
    ]
    for item in report["memcpy_direction_evidence"]:
        lines.append(f"| `{item['snippet']}` | `{item['present']}` | {item['meaning']} |")

    lines.extend(["", "## Comparator Calls", "", "| Function | Present | Interpretation |", "|---|---|---|"])
    for item in report["direction_comparators"]:
        lines.append(f"| `{item['function']}` | `{item['present']}` | {item['interpreted_as']} |")

    lines.extend(["", "## Effect On Prepare Fields", ""])
    lines.append(f"- ruled out hidden source: {report['effect_on_prepare_fields']['ruled_out_hidden_source']}")
    lines.append(f"- still unsourced: `{', '.join(report['effect_on_prepare_fields']['still_unsourced'])}`")

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
    print(f"status={report['status']} checks={len(report['checks'])}")
    print(f"wrote {OUT_MD.relative_to(ROOT_DIR)}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
