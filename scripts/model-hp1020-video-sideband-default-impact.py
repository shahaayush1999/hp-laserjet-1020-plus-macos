#!/usr/bin/env python3
"""Model the impact if active work sideband fields remain default/zero.

This is offline analysis only. It answers whether the currently unsourced
active work +0x26/+0x30/+0x32 fields look harmless or print-path critical.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT_DIR / "analysis/hardware-boundary/video-sideband-default-impact.json"
OUT_MD = ROOT_DIR / "analysis/hardware-boundary/video-sideband-default-impact.md"
GHIDRA_VIDEO_STATE_ACCESS_SCAN = ROOT_DIR / "analysis/ghidra-probes/video-state-sideband-access-scan.md"

SOURCES = {
    "prepare_fields": ROOT_DIR / "analysis/hardware-boundary/video-prepare-argument-fields.json",
    "prepare": ROOT_DIR / "analysis/dispatch-mmio/decompiled/10014910_hp1020_video_prepare_page_candidate.c",
    "band_helper": ROOT_DIR / "analysis/zjs-parser-boundary/decompiled/10014244_hp1020_video_band_done_or_irq_helper_candidate.c",
    "band_queue": ROOT_DIR / "analysis/zjs-parser-boundary/decompiled/10013f34_hp1020_video_band_queue_or_list_candidate.c",
    "raw_refresh": ROOT_DIR / "analysis/zjs-parser-boundary/decompiled/100140f8_hp1020_video_refresh_raw_bands_candidate.c",
}

SELECTED_CORPUS = [
    ROOT_DIR / "analysis/dispatch-mmio/decompiled/10014910_hp1020_video_prepare_page_candidate.c",
    ROOT_DIR / "analysis/dispatch-mmio/decompiled/10015214_hp1020_video_render_or_dma_candidate.c",
    ROOT_DIR / "analysis/zjs-parser-boundary/decompiled/10014244_hp1020_video_band_done_or_irq_helper_candidate.c",
    ROOT_DIR / "analysis/zjs-parser-boundary/decompiled/10013f34_hp1020_video_band_queue_or_list_candidate.c",
    ROOT_DIR / "analysis/zjs-parser-boundary/decompiled/100140f8_hp1020_video_refresh_raw_bands_candidate.c",
    ROOT_DIR / "analysis/zjs-parser-boundary/decompiled/100144d0_hp1020_video_irq_or_band_done_candidate.c",
]


def read_text(path: Path) -> str:
    return path.read_text(errors="replace")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def check(name: str, ok: bool, detail: str) -> dict[str, str]:
    return {"name": name, "status": "present" if ok else "missing", "detail": detail}


def references_for(token: str) -> list[dict[str, Any]]:
    hits = []
    for path in SELECTED_CORPUS:
        for line_no, line in enumerate(read_text(path).splitlines(), start=1):
            if token in line:
                hits.append(
                    {
                        "source": str(path.relative_to(ROOT_DIR)),
                        "line": line_no,
                        "text": line.strip(),
                    }
                )
    return hits


def ghidra_video_state_access_hits() -> dict[str, Any]:
    text = GHIDRA_VIDEO_STATE_ACCESS_SCAN.read_text(errors="replace")
    hits = []
    in_table = False
    for line in text.splitlines():
        if line.startswith("| Address | Function | Access |"):
            in_table = True
            continue
        if not in_table:
            continue
        if line.startswith("|---"):
            continue
        if not line.startswith("| `"):
            break
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 7:
            continue
        hit = {
            "address": cells[0].strip("`"),
            "function": cells[1].strip("`"),
            "access": cells[2].strip("`"),
            "offset": cells[3].strip("`"),
            "meaning": cells[4],
            "bytes": cells[5].strip("`"),
            "instruction": cells[6].strip("`"),
        }
        hits.append({**hit, **classify_ghidra_access(hit)})
    return {
        "path": str(GHIDRA_VIDEO_STATE_ACCESS_SCAN.relative_to(ROOT_DIR)),
        "language": "Xtensa:BE:32:default" if "language: `Xtensa:BE:32:default`" in text else "unknown",
        "hits": hits,
    }


def classify_ghidra_access(hit: dict[str, Any]) -> dict[str, str]:
    function = hit["function"]
    offset = hit["offset"]
    access = hit["access"]
    if function.startswith("10014910 ") and access == "store" and offset in {"0xd0", "0xd4", "0xe8", "0xec"}:
        return {"role": "prepare_seed", "classification": "video state seed from active work argument"}
    if function.startswith("10014910 ") and access == "load" and offset == "0xec":
        return {"role": "prepare_mode_consumer", "classification": "prepare setup branch/table consumer"}
    if function.startswith("10014244 ") and offset == "0xd0":
        return {"role": "channel_b_refill_counter", "classification": "channel-B refill amount and decrement path"}
    if function.startswith("10013f34 ") and offset == "0xd4":
        return {"role": "descriptor_final_accounting", "classification": "descriptor queue final/high-bit accounting"}
    if function.startswith("10013f34 ") and offset == "0xec":
        return {"role": "descriptor_b_flag", "classification": "B-side raw-band flag bit source"}
    if function.startswith("100140f8 ") and offset == "0xec":
        return {"role": "raw_refresh_b_flag", "classification": "alternate raw-refresh B-side flag source"}
    if function.startswith("100165a4 "):
        return {"role": "stack_local_false_positive", "classification": "same numeric stack offset, not video state"}
    return {"role": "unclassified_access", "classification": "needs manual review"}


def build_report() -> dict[str, Any]:
    prepare_fields = read_json(SOURCES["prepare_fields"])
    sources = {name: read_text(path) for name, path in SOURCES.items() if name != "prepare_fields"}
    unsourced = {
        field.get("field")
        for field in prepare_fields.get("fields", [])
        if isinstance(field, dict) and field.get("source_status") == "unsourced_active_work"
    }

    field_impacts = [
        {
            "work_field": "+0x26",
            "state_fields": ["+0xd0", "+0xd4"],
            "if_zero": [
                "0x10014244 band helper sees +0xd0 == 0 and skips channel-B pointer/length writes",
                "0x10013f34 sees +0xd4 <= descriptor_units<<2 immediately, setting the final/high-bit condition early",
                "after queue/list consumption, +0xd4 subtracts descriptor units and can underflow as an unsigned-looking counter",
            ],
            "risk": "critical",
            "current_interpretation": "not safe to assume zero for a printing path",
        },
        {
            "work_field": "+0x30",
            "state_fields": ["+0xe8"],
            "if_zero": [
                "prepare copies zero into +0xe8",
                "no downstream +0xe8 consumer was recovered in the selected video prepare/render/refill corpus",
            ],
            "risk": "unknown_low_in_current_static_view",
            "current_interpretation": "keep tracked, but it is not currently a first blocker compared with +0x26/+0x32",
        },
        {
            "work_field": "+0x32",
            "state_fields": ["+0xec"],
            "if_zero": [
                "prepare takes non-secondary timing/table branches when +0xec == 0",
                "0x10013f34 does not OR secondary-output bit 0x19 into B raw-band flags",
                "0x100140f8 reads +0xec in the alternate raw-refresh path",
            ],
            "risk": "mode_critical",
            "current_interpretation": "zero may be correct for generated normal cases, but must be deliberately chosen rather than accidentally defaulted",
        },
    ]

    refs = {
        "+0xd0": references_for("+ 0xd0") + references_for("+0xd0"),
        "+0xd4": references_for("+ 0xd4") + references_for("+0xd4"),
        "+0xe8": references_for("+ 0xe8") + references_for("+0xe8"),
        "+0xec": references_for("+ 0xec") + references_for("+0xec"),
    }
    ghidra_access_scan = ghidra_video_state_access_hits()
    ghidra_hits = ghidra_access_scan["hits"]
    roles = {hit["role"] for hit in ghidra_hits}
    e8_hits = [hit for hit in ghidra_hits if hit["offset"] == "0xe8"]

    checks = [
        check(
            "unsourced_fields_are_expected_three",
            unsourced == {"+0x26", "+0x30", "+0x32"},
            "prepare field model still exposes exactly the three unsourced active work sideband fields",
        ),
        check(
            "zero_d0_skips_channel_b_refill",
            "if ((*piVar6 == 0) && (uVar3 = *(uint *)(PTR_DAT_10006770 + 0xd0), uVar3 != 0))"
            in sources["band_helper"]
            and "*DAT_100067e4 = uVar7" in sources["band_helper"]
            and "*piVar2 = iVar4 * iVar5" in sources["band_helper"],
            "+0xd0 nonzero gates channel-B pointer/length writes",
        ),
        check(
            "zero_d4_triggers_final_condition_early",
            "if (*(uint *)(puVar2 + 0xd4) <= (uint)(*(int *)(puVar6 + 8) << 2))" in sources["band_queue"]
            and "*(int *)(puVar2 + 0xd4) = *(int *)(puVar2 + 0xd4) - *(int *)(puVar6 + 8)" in sources["band_queue"],
            "+0xd4 participates in final/high-bit logic and is decremented by descriptor units",
        ),
        check(
            "ec_controls_secondary_paths",
            "*(int *)(hp1020_video_state_ptr_word + 0xec) != 0" in sources["prepare"]
            and "*DAT_100067dc = uVar9 | (uint)(*(int *)(puVar2 + 0xec) != 0) << 0x19" in sources["band_queue"]
            and "iVar11 = *(int *)(puVar3 + 0xec)" in sources["raw_refresh"],
            "+0xec controls prepare secondary branches and raw-band B flag behavior",
        ),
        check(
            "e8_has_no_selected_downstream_consumer",
            len(refs["+0xe8"]) == 1 and "param_1 + 0x30" in refs["+0xe8"][0]["text"],
            "+0xe8 is only seen in the prepare assignment within the selected video corpus",
        ),
        check(
            "ghidra_state_access_scan_classified",
            ghidra_access_scan["language"] == "Xtensa:BE:32:default"
            and ghidra_hits != []
            and all(hit["role"] != "unclassified_access" for hit in ghidra_hits),
            "Ghidra exact-offset state access scan is forced to Xtensa BE and every hit is classified",
        ),
        check(
            "ghidra_state_access_scan_covers_critical_consumers",
            {"channel_b_refill_counter", "descriptor_final_accounting", "descriptor_b_flag", "raw_refresh_b_flag"}.issubset(roles),
            "Ghidra exact-offset scan independently sees the critical +0xd0/+0xd4/+0xec consumers",
        ),
        check(
            "ghidra_e8_has_prepare_store_only",
            len(e8_hits) == 1 and e8_hits[0]["function"].startswith("10014910 ") and e8_hits[0]["access"] == "store",
            "Ghidra exact-offset scan finds +0xe8 only as the prepare-side seed store",
        ),
        check(
            "ghidra_stack_local_false_positive_is_not_video_state",
            any(hit["role"] == "stack_local_false_positive" for hit in ghidra_hits),
            "scan records and classifies numeric +0xd0 stack-local false positives separately from video-state accesses",
        ),
    ]

    status = "pass" if all(item["status"] == "present" for item in checks) else "fail"
    return {
        "summary": "Impact model for default/zero active work sideband fields.",
        "status": status,
        "field_impacts": field_impacts,
        "reference_hits": refs,
        "ghidra_video_state_access_scan": ghidra_access_scan,
        "conclusion": [
            "The unsourced sideband fields are not all equal: +0x26 is immediately critical for channel-B refill and remaining/final accounting.",
            "+0x32 is mode-critical: zero may be correct for normal generated cases, but it affects setup tables and B-side raw-band flags.",
            "+0x30 currently has no selected downstream consumer beyond prepare copying it to +0xe8, so it is tracked but lower priority.",
            "The next useful static target is still the hidden source or intended default policy for active work +0x26.",
        ],
        "checks": checks,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 Video Sideband Default Impact",
        "",
        "This generated report is offline only. It does not contact the printer.",
        "",
        "## Result",
        "",
        f"- status: `{report['status']}`",
        "",
        "## Field Impact",
        "",
        "| Work field | State fields | Risk | Current interpretation |",
        "|---|---|---|---|",
    ]
    for item in report["field_impacts"]:
        state_fields = ", ".join(f"`{field}`" for field in item["state_fields"])
        lines.append(
            f"| `{item['work_field']}` | {state_fields} | `{item['risk']}` | {item['current_interpretation']} |"
        )
    for item in report["field_impacts"]:
        lines.extend(["", f"### `{item['work_field']}` If Zero", ""])
        for effect in item["if_zero"]:
            lines.append(f"- {effect}")

    lines.extend(["", "## Current Conclusion", ""])
    for item in report["conclusion"]:
        lines.append(f"- {item}")

    scan = report["ghidra_video_state_access_scan"]
    lines.extend(
        [
            "",
            "## Ghidra Exact State Access Scan",
            "",
            f"- path: `{scan['path']}`",
            f"- language: `{scan['language']}`",
            f"- access hits: `{len(scan['hits'])}`",
            "",
            "| Address | Function | Access | Offset | Role | Classification | Instruction |",
            "|---|---|---|---:|---|---|---|",
        ]
    )
    for hit in scan["hits"]:
        lines.append(
            f"| `{hit['address']}` | `{hit['function']}` | `{hit['access']}` | `{hit['offset']}` | `{hit['role']}` | {hit['classification']} | `{hit['instruction']}` |"
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
    print(f"status={report['status']} fields={len(report['field_impacts'])} checks={len(report['checks'])}")
    print(f"wrote {OUT_MD.relative_to(ROOT_DIR)}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
