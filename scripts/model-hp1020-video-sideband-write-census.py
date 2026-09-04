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
GHIDRA_WORK_POPULATE_PROBE = ROOT_DIR / "analysis/ghidra-probes/work-populate-instruction-probe.md"
GHIDRA_SIDEBAND_STORE_SCAN = ROOT_DIR / "analysis/ghidra-probes/sideband-store-scan.md"
GHIDRA_SIDEBAND_OVERLAP_STORE_SCAN = ROOT_DIR / "analysis/ghidra-probes/sideband-overlap-store-scan.md"

SIDEBAND_FIELDS = {"+0x26", "+0x30", "+0x32"}
DIRECT_PATH_FUNCTION_PREFIXES = {
    "10009b4c",  # page-parameter builder
    "1000e414",  # JobMgr thread
    "1000f204",  # work init/clear
    "1000f228",  # work create
    "10010398",  # child/page record create
    "100104c8",  # work populate from page params
    "10013f34",  # video descriptor queue/list helper
    "10014244",  # video refill helper
    "10014910",  # video prepare
}
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


def ghidra_work_populate_store_offsets() -> dict[str, Any]:
    text = read_text(GHIDRA_WORK_POPULATE_PROBE)
    halfword_offsets: list[str] = []
    word_offsets: list[str] = []
    for line in text.splitlines():
        if "`s16i " in line:
            match = re.search(r"s16i\s+[^,]+,[^,]+,(0x[0-9a-f]+)", line)
            if match:
                halfword_offsets.append(match.group(1))
        if "`s32i" in line:
            match = re.search(r"s32i(?:\.n)?\s+[^,]+,[^,]+,(0x[0-9a-f]+)", line)
            if match:
                word_offsets.append(match.group(1))
    return {
        "path": str(GHIDRA_WORK_POPULATE_PROBE.relative_to(ROOT_DIR)),
        "language": "Xtensa:BE:32:default" if "language: `Xtensa:BE:32:default`" in text else "unknown",
        "halfword_store_offsets": halfword_offsets,
        "word_store_offsets": word_offsets,
    }


def ghidra_sideband_store_hits() -> dict[str, Any]:
    text = read_text(GHIDRA_SIDEBAND_STORE_SCAN)
    hits = []
    in_table = False
    for line in text.splitlines():
        if line.startswith("| Address | Function | Offset |"):
            in_table = True
            continue
        if not in_table:
            continue
        if line.startswith("|---"):
            continue
        if not line.startswith("| `"):
            break
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 5:
            continue
        hits.append(
            {
                "address": cells[0].strip("`"),
                "function": cells[1].strip("`"),
                "offset": cells[2].strip("`"),
                "bytes": cells[3].strip("`"),
                "instruction": cells[4].strip("`"),
            }
        )
    return {
        "path": str(GHIDRA_SIDEBAND_STORE_SCAN.relative_to(ROOT_DIR)),
        "language": "Xtensa:BE:32:default" if "language: `Xtensa:BE:32:default`" in text else "unknown",
        "hits": hits,
    }


def ghidra_sideband_overlap_store_hits() -> dict[str, Any]:
    text = read_text(GHIDRA_SIDEBAND_OVERLAP_STORE_SCAN)
    hits = []
    in_table = False
    for line in text.splitlines():
        if line.startswith("| Address | Function | Mnemonic |"):
            in_table = True
            continue
        if not in_table:
            continue
        if line.startswith("|---"):
            continue
        if not line.startswith("| `"):
            break
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 8:
            continue
        hits.append(
            {
                "address": cells[0].strip("`"),
                "function": cells[1].strip("`"),
                "mnemonic": cells[2].strip("`"),
                "offset": cells[3].strip("`"),
                "width": int(cells[4].strip("`")),
                "overlaps": cells[5].strip("`").split(", "),
                "bytes": cells[6].strip("`"),
                "instruction": cells[7].strip("`"),
            }
        )

    direct_path_hits = [
        hit
        for hit in hits
        if any(hit["function"].startswith(prefix) for prefix in DIRECT_PATH_FUNCTION_PREFIXES)
    ]
    return {
        "path": str(GHIDRA_SIDEBAND_OVERLAP_STORE_SCAN.relative_to(ROOT_DIR)),
        "language": "Xtensa:BE:32:default" if "language: `Xtensa:BE:32:default`" in text else "unknown",
        "hits": hits,
        "direct_path_hits": direct_path_hits,
    }


def classify_overlap_hits(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    classified = []
    for hit in hits:
        function = hit["function"]
        address = hit["address"]
        if function.startswith("10009b4c "):
            role = "direct_work_exact_store"
            meaning = "real page-param sideband store; it is upstream of the active work object"
        elif function.startswith("10014910 ") and address == "10014a2a":
            role = "video_state_ring_clear"
            meaning = "32-bit clear at video state ring entry +0x24; overlaps +0x26 as bytes, but not an active-work field write"
        else:
            role = "unclassified_direct_path_overlap"
            meaning = "direct-path overlap hit needs manual review"
        classified.append({**hit, "role": role, "meaning": meaning})
    return classified


def classify_hits(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    classified = []
    for hit in hits:
        source = hit["source"]
        text = hit["text"]
        if source == "page_param_builder" and "(param_1 + 0x26)" in text:
            meaning = "real page-param +0x26 writer, not active work"
            role = "direct_work_writer"
            byte_offset = "+0x26"
        elif source == "page_param_builder" and "(param_1 + 0x30)" in text:
            meaning = "real page-param +0x30 writer, not active work"
            role = "direct_work_writer"
            byte_offset = "+0x30"
        elif source == "page_param_builder" and "(param_1 + 0x32)" in text:
            meaning = "real page-param +0x32 writer, not active work"
            role = "direct_work_writer"
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
    ghidra_probe = ghidra_work_populate_store_offsets()
    ghidra_store_scan = ghidra_sideband_store_hits()
    ghidra_overlap_scan = ghidra_sideband_overlap_store_hits()
    classified_overlap_hits = classify_overlap_hits(ghidra_overlap_scan["direct_path_hits"])
    by_role: dict[str, int] = {}
    for hit in hits:
        by_role[hit["role"]] = by_role.get(hit["role"], 0) + 1
    overlap_by_role: dict[str, int] = {}
    for hit in classified_overlap_hits:
        overlap_by_role[hit["role"]] = overlap_by_role.get(hit["role"], 0) + 1

    work_populate_text = read_text(SELECTED_SOURCES["work_populate"])
    unsourced_fields = [
        field.get("field")
        for field in prepare_fields.get("fields", [])
        if isinstance(field, dict) and field.get("source_status") == "unsourced_active_work"
    ]
    active_work_writer_hits = [
        hit
        for hit in hits
        if hit["role"] == "direct_work_writer"
    ]

    checks = [
        check(
            "selected_sideband_hits_classified",
            all(hit["role"] != "unclassified" for hit in hits),
            "selected sideband-looking hits are classified as direct work writers, consumers, or false leads",
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
            "ghidra_instruction_probe_excludes_sideband_stores",
            ghidra_probe["language"] == "Xtensa:BE:32:default"
            and set(ghidra_probe["halfword_store_offsets"])
            == {"0xc", "0xa", "0x10", "0x22", "0x1e", "0x14", "0x16", "0xe"}
            and set(ghidra_probe["word_store_offsets"]) == {"0x0"}
            and not ({ "0x26", "0x30", "0x32" } & set(ghidra_probe["halfword_store_offsets"])),
            "headless Ghidra instruction probe for 0x100104c8 has no stores to +0x26/+0x30/+0x32",
        ),
        check(
            "ghidra_whole_program_sideband_stores_are_page_param_only",
            ghidra_store_scan["language"] == "Xtensa:BE:32:default"
            and [hit["offset"] for hit in ghidra_store_scan["hits"]] == ["0x26", "0x30", "0x32"]
            and all(hit["function"].startswith("10009b4c ") for hit in ghidra_store_scan["hits"]),
            "whole-program Ghidra scan finds target-offset halfword stores only in the page-parameter builder",
        ),
        check(
            "ghidra_overlap_scan_is_broad_not_exact_sideband_proof",
            ghidra_overlap_scan["language"] == "Xtensa:BE:32:default"
            and len(ghidra_overlap_scan["hits"]) > len(ghidra_store_scan["hits"])
            and all(hit["mnemonic"] in {"s8i", "s16i", "s32i", "s32i.n"} for hit in ghidra_overlap_scan["hits"]),
            "whole-program overlap scan is intentionally broader than exact target stores and catches noisy wider stores",
        ),
        check(
            "ghidra_overlap_scan_finds_no_work_populate_or_jobmgr_sideband_writer",
            not any(
                hit["function"].startswith(("100104c8 ", "1000e414 ", "1000f204 ", "1000f228 ", "10010398 "))
                for hit in ghidra_overlap_scan["direct_path_hits"]
            ),
            "no overlapping store hit appears in the selected active-work create/populate/JobMgr functions",
        ),
        check(
            "ghidra_direct_path_overlap_hits_are_classified",
            classified_overlap_hits != []
            and all(hit["role"] != "unclassified_direct_path_overlap" for hit in classified_overlap_hits),
            "direct-path overlap hits are direct work stores or a separate video-state ring clear",
        ),
        check(
            "direct_active_work_writers_found",
            len(active_work_writer_hits) == 3,
            "three builder stores directly populate active work under START_PAGE",
        ),
        check(
            "prepare_field_model_resolves_sidebands",
            set(unsourced_fields) == set(),
            "prepare field model resolves all three sidebands through the direct builder",
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
        "ghidra_work_populate_probe": ghidra_probe,
        "ghidra_sideband_store_scan": ghidra_store_scan,
        "ghidra_sideband_overlap_store_scan": {
            **ghidra_overlap_scan,
            "direct_path_hits": classified_overlap_hits,
        },
        "role_counts": by_role,
        "overlap_role_counts": overlap_by_role,
        "selected_hits": hits,
        "active_work_writer_hits": active_work_writer_hits,
        "conclusion": [
            "The builder writes +0x26/+0x30/+0x32 directly into active work: START_PAGE supplies the allocated work as its destination.",
            "The child-page `puVar1[0x13] = 0` false lead is byte +0x4c because the pointer is `undefined4 *`.",
            "The JobMgr `puVar[0x13]` hits feed work +0x90 from runtime byte +0x13, not work +0x26.",
            "A headless Ghidra instruction probe confirms 0x100104c8 has no stores to active work +0x26/+0x30/+0x32.",
            "A whole-program Ghidra instruction scan finds `s16i` stores to offsets 0x26/0x30/0x32 only in the page-parameter builder.",
            "The broad scan includes the same three direct work stores; other selected hits remain classified as false leads or unrelated state writes.",
            "The old absence claim resulted from missing indirect-switch handlers in saved parser decompilation.",
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

    lines.extend(
        [
            "",
            "## Ghidra Work-Populate Probe",
            "",
            f"- path: `{report['ghidra_work_populate_probe']['path']}`",
            f"- language: `{report['ghidra_work_populate_probe']['language']}`",
            f"- halfword destination offsets: `{', '.join(report['ghidra_work_populate_probe']['halfword_store_offsets'])}`",
            f"- word destination offsets: `{', '.join(report['ghidra_work_populate_probe']['word_store_offsets'])}`",
        ]
    )

    lines.extend(["", "## Ghidra Whole-Program Sideband Store Scan", ""])
    lines.append(f"- path: `{report['ghidra_sideband_store_scan']['path']}`")
    lines.append(f"- language: `{report['ghidra_sideband_store_scan']['language']}`")
    lines.extend(["", "| Address | Function | Offset | Instruction |", "|---|---|---|---|"])
    for hit in report["ghidra_sideband_store_scan"]["hits"]:
        lines.append(
            f"| `{hit['address']}` | `{hit['function']}` | `{hit['offset']}` | `{hit['instruction']}` |"
        )

    overlap_scan = report["ghidra_sideband_overlap_store_scan"]
    lines.extend(["", "## Ghidra Whole-Program Overlap Store Scan", ""])
    lines.append(f"- path: `{overlap_scan['path']}`")
    lines.append(f"- language: `{overlap_scan['language']}`")
    lines.append(f"- overlapping stores found: `{len(overlap_scan['hits'])}`")
    lines.append(f"- selected direct-path overlap hits: `{len(overlap_scan['direct_path_hits'])}`")
    lines.extend(
        [
            "",
            "| Address | Function | Mnemonic | Offset | Width | Overlaps | Role | Meaning |",
            "|---|---|---|---:|---:|---|---|---|",
        ]
    )
    for hit in overlap_scan["direct_path_hits"]:
        lines.append(
            f"| `{hit['address']}` | `{hit['function']}` | `{hit['mnemonic']}` | `{hit['offset']}` | `{hit['width']}` | `{', '.join(hit['overlaps'])}` | `{hit['role']}` | {hit['meaning']} |"
        )

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
