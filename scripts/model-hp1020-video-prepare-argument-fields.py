#!/usr/bin/env python3
"""Model the fields read from the object passed into video prepare.

This is offline analysis only. It separates fields that are copied from page
parameters, fields that are filled by JobMgr, and fields that currently appear
to be defaults or unsourced on the active 0x94 work object.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT_DIR / "analysis/hardware-boundary/video-prepare-argument-fields.json"
OUT_MD = ROOT_DIR / "analysis/hardware-boundary/video-prepare-argument-fields.md"

SOURCES = {
    "queue_payload_chain": ROOT_DIR / "analysis/hardware-boundary/video-queue-payload-chain.json",
    "work_init": ROOT_DIR / "analysis/video-work-object/decompiled/1000f204_hp1020_work_common_init_candidate.c",
    "work_create": ROOT_DIR / "analysis/video-work-object/decompiled/1000f228_hp1020_video_work_create_candidate.c",
    "work_populate": ROOT_DIR
    / "analysis/video-work-object/decompiled/100104c8_hp1020_work_populate_from_page_params_candidate.c",
    "job_mgr": ROOT_DIR / "analysis/video-work-object/decompiled/1000e414_hp1020_job_mgr_thread_candidate.c",
    "page_param_builder": ROOT_DIR / "analysis/jobmgr-producer-boundary/decompiled/10009b4c_FUN_10009b4c.c",
    "prepare": ROOT_DIR / "analysis/dispatch-mmio/decompiled/10014910_hp1020_video_prepare_page_candidate.c",
    "render": ROOT_DIR / "analysis/dispatch-mmio/decompiled/10015214_hp1020_video_render_or_dma_candidate.c",
}

FIELD_MODEL = [
    {
        "field": "+0x14",
        "prepare_use": "timing/resolution branch input",
        "source": "copied by 0x100104c8 from page-param +0x1a",
        "source_status": "sourced",
        "evidence_needles": ["*(undefined2 *)(param_1 + 5) = *(undefined2 *)((int)param_2 + 0x1a)"],
    },
    {
        "field": "+0x16",
        "prepare_use": "timing/resolution branch input",
        "source": "copied by 0x100104c8 from page-param +0x1e",
        "source_status": "sourced",
        "evidence_needles": ["*(undefined2 *)((int)param_1 + 0x16) = *(undefined2 *)((int)param_2 + 0x1e)"],
    },
    {
        "field": "+0x18",
        "prepare_use": "computed/adjusted vertical timing value",
        "source": "cleared by common init, then written inside prepare",
        "source_status": "computed_default",
        "evidence_needles": ["FUN_1001b4c8(param_1,0,0x46)", "*(ushort *)(param_1 + 0x18) ="],
    },
    {
        "field": "+0x22",
        "prepare_use": "mode/setup branch selector",
        "source": "copied by 0x100104c8 from page-param +0x12",
        "source_status": "sourced",
        "evidence_needles": ["*(undefined2 *)((int)param_1 + 0x22) = *(undefined2 *)((int)param_2 + 0x12)"],
    },
    {
        "field": "+0x24",
        "prepare_use": "offset/centering input",
        "source": "cleared by common init; no visible work-object writer in current static corpus",
        "source_status": "default_or_unsourced",
        "evidence_needles": ["FUN_1001b4c8(param_1,0,0x46)", "*(ushort *)(param_1 + 0x24)"],
    },
    {
        "field": "+0x26",
        "prepare_use": "remaining-unit seed copied to video state +0xd0/+0xd4",
        "source": "page-param +0x26 is built upstream, but not copied into active 0x94 work object by visible code",
        "source_status": "unsourced_active_work",
        "evidence_needles": [
            "*(undefined2 *)(param_1 + 0x26) = *(undefined2 *)((int)param_2 + 10)",
            "*(uint *)(puVar15 + 0xd0) = (uint)*(ushort *)(param_1 + 0x26)",
        ],
    },
    {
        "field": "+0x30",
        "prepare_use": "copied to video state +0xe8",
        "source": "page-param +0x30 is built upstream, but not copied into active 0x94 work object by visible code",
        "source_status": "unsourced_active_work",
        "evidence_needles": [
            "*(undefined2 *)(param_1 + 0x30) = *(undefined2 *)((int)param_2 + 10)",
            "*(uint *)(puVar15 + 0xe8) = (uint)*(ushort *)(param_1 + 0x30)",
        ],
    },
    {
        "field": "+0x32",
        "prepare_use": "copied to video state +0xec",
        "source": "page-param +0x32 is built upstream, but not copied into active 0x94 work object by visible code",
        "source_status": "unsourced_active_work",
        "evidence_needles": [
            "*(undefined2 *)(param_1 + 0x32) = *(undefined2 *)((int)param_2 + 10)",
            "*(uint *)(puVar15 + 0xec) = (uint)*(ushort *)(param_1 + 0x32)",
        ],
    },
    {
        "field": "+0x36",
        "prepare_use": "normal setup branch gate",
        "source": "cleared by common init for active work; page-param +0x36 case exists but is not visibly copied",
        "source_status": "default_zero_for_current_path",
        "evidence_needles": ["FUN_1001b4c8(param_1,0,0x46)", "*(short *)(param_1 + 0x36) == 0"],
    },
    {
        "field": "+0x74",
        "prepare_use": "descriptor-queue versus raw-linked-list mode flag",
        "source": "set to zero by work create for descriptor-queue path",
        "source_status": "default_zero_for_current_path",
        "evidence_needles": ["*(undefined1 *)(iVar1 + 0x74) = 0", "if (*(char *)(param_1 + 0x74) == '\\0')"],
    },
    {
        "field": "+0x84/+0x88/+0x8c/+0x90",
        "prepare_use": "host raster geometry and render descriptor controls",
        "source": "filled by JobMgr from runtime BIH block before engine/video handoff",
        "source_status": "sourced",
        "evidence_needles": [
            "*(undefined4 *)(iVar9 + 0x84) = *(undefined4 *)(PTR_DAT_10006304 + 4)",
            "*(undefined4 *)(iVar9 + 0x88) = *(undefined4 *)(puVar4 + 8)",
            "*(undefined4 *)(iVar9 + 0x8c) = *(undefined4 *)(puVar4 + 0xc)",
            "*(undefined *)(iVar9 + 0x90) = puVar4[0x13]",
        ],
    },
]


def read_text(path: Path) -> str:
    return path.read_text(errors="replace")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def all_sources_text(sources: dict[str, str]) -> str:
    return "\n".join(sources.values())


def check(name: str, ok: bool, detail: str) -> dict[str, str]:
    return {"name": name, "status": "present" if ok else "missing", "detail": detail}


def evidence_for_field(field: dict[str, Any], sources_text: str) -> list[dict[str, str]]:
    evidence = []
    for needle in field["evidence_needles"]:
        evidence.append(
            {
                "needle": needle,
                "status": "present" if needle in sources_text else "missing",
            }
        )
    return evidence


def build_report() -> dict[str, Any]:
    queue_chain = read_json(SOURCES["queue_payload_chain"])
    sources = {name: read_text(path) for name, path in SOURCES.items() if name != "queue_payload_chain"}
    text = all_sources_text(sources)

    fields = []
    for field in FIELD_MODEL:
        item = dict(field)
        item["evidence"] = evidence_for_field(field, text)
        item["status"] = "present" if all(ev["status"] == "present" for ev in item["evidence"]) else "missing"
        fields.append(item)

    by_status: dict[str, int] = {}
    for field in fields:
        by_status[field["source_status"]] = by_status.get(field["source_status"], 0) + 1

    checks = [
        check(
            "prepare_argument_is_work_object",
            queue_chain.get("status") == "pass"
            and queue_chain.get("conclusion", {}).get("prepare_argument_identity")
            == "0x94-byte video/page work object",
            "queue payload chain identifies the prepare argument as the active 0x94 work object",
        ),
        check(
            "all_field_evidence_present",
            all(field["status"] == "present" for field in fields),
            "all modeled prepare-argument fields have current source/use evidence",
        ),
        check(
            "unsourced_sideband_fields_preserved",
            {field["field"] for field in fields if field["source_status"] == "unsourced_active_work"}
            == {"+0x26", "+0x30", "+0x32"},
            "active work +0x26/+0x30/+0x32 remain unsourced in current visible code",
        ),
        check(
            "jobmgr_geometry_fields_sourced",
            any(field["field"] == "+0x84/+0x88/+0x8c/+0x90" and field["source_status"] == "sourced" for field in fields),
            "JobMgr-sourced geometry fields are separated from low sideband defaults",
        ),
    ]

    status = "pass" if all(item["status"] == "present" for item in checks) else "fail"
    return {
        "summary": "Field source model for the active 0x94 work object consumed by video prepare.",
        "status": status,
        "prepare_argument_identity": queue_chain.get("conclusion", {}).get("prepare_argument_identity"),
        "field_status_counts": by_status,
        "fields": fields,
        "conclusion": [
            "Video prepare reads a mix of sourced fields, default/computed fields, and currently unsourced active-work sideband fields.",
            "The critical sourced render geometry is still strong: JobMgr fills +0x84/+0x88/+0x8c/+0x90 from the BIH/runtime block.",
            "The weak fields are active work +0x26/+0x30/+0x32: page-param values exist upstream, but current visible code does not copy them into the work object passed to prepare.",
        ],
        "checks": checks,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 Video Prepare Argument Fields",
        "",
        "This generated report is offline only. It does not contact the printer.",
        "",
        "## Result",
        "",
        f"- status: `{report['status']}`",
        f"- prepare argument identity: `{report['prepare_argument_identity']}`",
        f"- sourced/default/unsourced counts: `{report['field_status_counts']}`",
        "",
        "## Field Sources",
        "",
        "| Field | Prepare use | Source status | Source |",
        "|---|---|---|---|",
    ]
    for field in report["fields"]:
        lines.append(
            f"| `{field['field']}` | {field['prepare_use']} | `{field['source_status']}` | {field['source']} |"
        )

    lines.extend(["", "## Current Conclusion", ""])
    for item in report["conclusion"]:
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
    print(f"status={report['status']} fields={len(report['fields'])} checks={len(report['checks'])}")
    print(f"wrote {OUT_MD.relative_to(ROOT_DIR)}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
