#!/usr/bin/env python3
"""Census writes that look related to active video sideband fields.

This is offline analysis only. It exists to prevent a common false lead:
decompiler output such as ``puVar1[0x13] = 0`` may look like a ``+0x26``
halfword write, but the inferred pointer type decides the real byte offset.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT_DIR / "analysis/hardware-boundary/video-sideband-write-census.json"
OUT_MD = ROOT_DIR / "analysis/hardware-boundary/video-sideband-write-census.md"

SELECTED_SOURCES = {
    "page_param_builder": ROOT_DIR / "analysis/jobmgr-producer-boundary/decompiled/10009b4c_FUN_10009b4c.c",
    "child_page_create": ROOT_DIR
    / "analysis/jobmgr-producer-boundary/decompiled/10010398_hp1020_child_page_record_create_candidate.c",
    "work_populate": ROOT_DIR
    / "analysis/video-work-object/decompiled/100104c8_hp1020_work_populate_from_page_params_candidate.c",
    "job_mgr": ROOT_DIR / "analysis/video-work-object/decompiled/1000e414_hp1020_job_mgr_thread_candidate.c",
    "prepare": ROOT_DIR / "analysis/dispatch-mmio/decompiled/10014910_hp1020_video_prepare_page_candidate.c",
}

PREPARE_FIELDS_JSON = ROOT_DIR / "analysis/hardware-boundary/video-prepare-argument-fields.json"
QUEUE_CHAIN_JSON = ROOT_DIR / "analysis/hardware-boundary/video-queue-payload-chain.json"

SIDEBAND_FIELDS = {"+0x26", "+0x30", "+0x32"}
LINE_PATTERNS = [
    re.compile(r"\+\s*0x26\b|\+0x26\b"),
    re.compile(r"\+\s*0x30\b|\+0x30\b"),
    re.compile(r"\+\s*0x32\b|\+0x32\b"),
    re.compile(r"\[0x13\]"),
]


def read_text(path: Path) -> str:
    return path.read_text(errors="replace")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def check(name: str, ok: bool, detail: str) -> dict[str, str]:
    return {"name": name, "status": "present" if ok else "missing", "detail": detail}


def all_decompiled_c_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT_DIR.glob("analysis/**/*.c")
        if "decompiled" in path.as_posix() or "decompiled-neighbors" in path.as_posix()
    )


def interesting_lines(path: Path) -> list[dict[str, Any]]:
    hits = []
    for line_no, line in enumerate(read_text(path).splitlines(), start=1):
        compact = line.strip()
        if not compact:
            continue
        if any(pattern.search(compact) for pattern in LINE_PATTERNS):
            hits.append({"path": str(path.relative_to(ROOT_DIR)), "line": line_no, "text": compact})
    return hits


def selected_hits() -> list[dict[str, Any]]:
    hits = []
    for name, path in SELECTED_SOURCES.items():
        for hit in interesting_lines(path):
            hit["source"] = name
            hits.append(hit)
    return hits


def corpus_hit_summary() -> dict[str, Any]:
    hits = []
    unique_texts = set()
    for path in all_decompiled_c_files():
        for hit in interesting_lines(path):
            hits.append(hit)
            unique_texts.add(hit["text"])
    return {
        "files_scanned": len(all_decompiled_c_files()),
        "raw_hit_count": len(hits),
        "unique_text_count": len(unique_texts),
        "unique_texts": sorted(unique_texts),
    }


def classify_hits(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    classified = []
    for hit in hits:
        source = hit["source"]
        text = hit["text"]
        if source == "page_param_builder" and "(param_1 + 0x26)" in text:
            meaning = "real page-param +0x26 writer, not active work"
            role = "upstream_page_param_writer"
            byte_offset = "+0x26"
        elif source == "page_param_builder" and "(param_1 + 0x30)" in text:
            meaning = "real page-param +0x30 writer, not active work"
            role = "upstream_page_param_writer"
            byte_offset = "+0x30"
        elif source == "page_param_builder" and "(param_1 + 0x32)" in text:
            meaning = "real page-param +0x32 writer, not active work"
            role = "upstream_page_param_writer"
            byte_offset = "+0x32"
        elif source == "child_page_create" and "puVar1[0x13]" in text:
            meaning = "undefined4* index 0x13 means child/page record byte offset +0x4c"
            role = "scaled_index_false_lead"
            byte_offset = "+0x4c"
        elif source == "job_mgr" and "[0x13]" in text and "+ 0x90" in text:
            meaning = "undefined* index 0x13 is runtime block byte +0x13 copied into work +0x90"
            role = "runtime_byte_to_work_0x90"
            byte_offset = "source +0x13, destination +0x90"
        elif source == "prepare" and "(param_1 + 0x26)" in text:
            meaning = "consumer: prepare reads active argument +0x26 into video state counters"
            role = "active_work_consumer"
            byte_offset = "+0x26"
        elif source == "prepare" and "(param_1 + 0x30)" in text:
            meaning = "consumer: prepare reads active argument +0x30 into video state +0xe8"
            role = "active_work_consumer"
            byte_offset = "+0x30"
        elif source == "prepare" and "(param_1 + 0x32)" in text:
            meaning = "consumer: prepare reads active argument +0x32 into video state +0xec"
            role = "active_work_consumer"
            byte_offset = "+0x32"
        else:
            meaning = "tracked sideband-looking hit"
            role = "unclassified"
            byte_offset = "unknown"
        classified.append({**hit, "role": role, "byte_offset": byte_offset, "meaning": meaning})
    return classified


def build_report() -> dict[str, Any]:
    prepare_fields = read_json(PREPARE_FIELDS_JSON)
    queue_chain = read_json(QUEUE_CHAIN_JSON)
    hits = classify_hits(selected_hits())
    corpus_summary = corpus_hit_summary()
    by_role: dict[str, int] = {}
    for hit in hits:
        by_role[hit["role"]] = by_role.get(hit["role"], 0) + 1

    work_populate_text = read_text(SELECTED_SOURCES["work_populate"])
    unsourced_fields = [
        field.get("field")
        for field in prepare_fields.get("fields", [])
        if isinstance(field, dict) and field.get("source_status") == "unsourced_active_work"
    ]
    active_work_writer_hits = [
        hit
        for hit in hits
        if hit["role"] not in {"upstream_page_param_writer", "scaled_index_false_lead", "runtime_byte_to_work_0x90", "active_work_consumer"}
    ]

    checks = [
        check(
            "selected_sideband_hits_classified",
            all(hit["role"] != "unclassified" for hit in hits),
            "selected sideband-looking hits are classified as upstream writers, consumers, or false leads",
        ),
        check(
            "child_record_0x13_is_not_work_0x26",
            any(hit["role"] == "scaled_index_false_lead" and hit["byte_offset"] == "+0x4c" for hit in hits),
            "0x10010398 puVar1[0x13] is a 32-bit child/page record slot at byte +0x4c",
        ),
        check(
            "runtime_byte_0x13_feeds_work_0x90_not_sideband",
            by_role.get("runtime_byte_to_work_0x90", 0) >= 1,
            "JobMgr puVar[0x13] references are BIH/runtime byte +0x13 copied to work +0x90",
        ),
        check(
            "work_populate_still_lacks_sideband_copy",
            "0x26" not in work_populate_text and "0x30" not in work_populate_text and "0x32" not in work_populate_text,
            "simple page-param to work-object copier has no visible +0x26/+0x30/+0x32 copy",
        ),
        check(
            "no_selected_active_work_writer_found",
            active_work_writer_hits == [],
            "the selected print-path corpus still has no direct active work sideband writer",
        ),
        check(
            "prepare_field_model_keeps_sidebands_unsourced",
            set(unsourced_fields) == SIDEBAND_FIELDS,
            "prepare field model still marks +0x26/+0x30/+0x32 as unsourced on active work",
        ),
        check(
            "queue_chain_keeps_prepare_argument_as_work_object",
            queue_chain.get("conclusion", {}).get("prepare_argument_identity") == "0x94-byte video/page work object",
            "queue chain still identifies the active prepare argument as the 0x94 work object",
        ),
    ]
    status = "pass" if all(item["status"] == "present" for item in checks) else "fail"
    return {
        "summary": "Sideband-looking write/read census for active video work fields +0x26/+0x30/+0x32.",
        "status": status,
        "selected_sources": {name: str(path.relative_to(ROOT_DIR)) for name, path in SELECTED_SOURCES.items()},
        "corpus_summary": corpus_summary,
        "role_counts": by_role,
        "selected_hits": hits,
        "active_work_writer_hits": active_work_writer_hits,
        "conclusion": [
            "The obvious page-param writes for +0x26/+0x30/+0x32 are upstream page-parameter fields, not active work-object writes.",
            "The child-page `puVar1[0x13] = 0` false lead is byte +0x4c because the pointer is `undefined4 *`.",
            "The JobMgr `puVar[0x13]` hits feed work +0x90 from runtime byte +0x13, not work +0x26.",
            "Within the selected print-path corpus, active work +0x26/+0x30/+0x32 remain unsourced.",
        ],
        "checks": checks,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 Video Sideband Write Census",
        "",
        "This generated report is offline only. It does not contact the printer.",
        "",
        "## Result",
        "",
        f"- status: `{report['status']}`",
        f"- decompiled files scanned for raw sideband-looking hits: `{report['corpus_summary']['files_scanned']}`",
        f"- raw corpus hits: `{report['corpus_summary']['raw_hit_count']}`",
        "",
        "## Conclusion",
        "",
    ]
    for item in report["conclusion"]:
        lines.append(f"- {item}")

    lines.extend(["", "## Selected Hit Classification", "", "| Source | Line | Role | Byte offset | Text | Meaning |", "|---|---:|---|---|---|---|"])
    for hit in report["selected_hits"]:
        lines.append(
            f"| `{hit['source']}` | `{hit['line']}` | `{hit['role']}` | `{hit['byte_offset']}` | `{hit['text']}` | {hit['meaning']} |"
        )

    lines.extend(["", "## Raw Unique Corpus Texts", ""])
    for text in report["corpus_summary"]["unique_texts"]:
        lines.append(f"- `{text}`")

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
    print(
        "status={status} checks={checks} selected_hits={hits} raw_hits={raw}".format(
            status=report["status"],
            checks=len(report["checks"]),
            hits=len(report["selected_hits"]),
            raw=report["corpus_summary"]["raw_hit_count"],
        )
    )
    print(OUT_MD.relative_to(ROOT_DIR))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
