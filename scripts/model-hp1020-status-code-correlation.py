#!/usr/bin/env python3
"""Model the boundary between engine event words and PJL CODE values."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
EVENTS_TSV = ROOT_DIR / "analysis/engine-events/engine-0x17-events.tsv"
OFFSET_TSV = ROOT_DIR / "analysis/status-path/status-code-offset-table.tsv"
OUT_JSON = ROOT_DIR / "analysis/status-path/status-code-correlation.json"
OUT_MD = ROOT_DIR / "analysis/status-path/status-code-correlation.md"


def parse_int(text: str) -> int:
    return int(text, 0)


def load_events(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = []
        for row in reader:
            event_word = parse_int(row["event_word1"])
            low16 = event_word & 0xFFFF
            rows.append(
                {
                    **row,
                    "event_word_int": event_word,
                    "event_word_hex": f"0x{event_word:08x}",
                    "low16": f"0x{low16:04x}",
                    "low16_high_byte": f"0x{low16 & 0xFF00:04x}",
                    "low16_low_byte": f"0x{low16 & 0x00FF:02x}",
                    "direct_converter_class": classify_direct_converter_path(event_word),
                }
            )
    return rows


def load_offsets(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = []
        for row in reader:
            normalized = {key.lstrip("# ").strip(): value for key, value in row.items()}
            rows.append(
                {
                    "index": int(normalized["index"]),
                    "entry_address": normalized["entry_address"],
                    "input_value": normalized["input_value"],
                    "offset": normalized["offset"],
                    "pjl_code": int(normalized["pjl_code_base_0xa028_plus_offset"]),
                }
            )
        return rows


def classify_direct_converter_path(status_word: int) -> str:
    low16 = status_word & 0xFFFF
    if (low16 & 0xFF00) == 0x0100:
        return "direct call would return default 10001 path"
    if (status_word & 0x00020000) and not (status_word & 0x80000000):
        return "direct call would return default 10001 path"
    if low16 == 0x1001:
        return "direct call would use datastore 0x1f 410xx lookup"
    return "not a proven direct input to CODE converter"


def build_report(events_path: Path, offsets_path: Path) -> dict[str, Any]:
    events = load_events(events_path)
    offsets = load_offsets(offsets_path)
    counts: dict[str, int] = {}
    for event in events:
        key = event["direct_converter_class"]
        counts[key] = counts.get(key, 0) + 1
    return {
        "summary": "Conservative correlation between engine queue 0x17 event words and PJL CODE generation.",
        "converter_function": "0x1000a2a4 hp1020_status_word_to_pjl_code_candidate",
        "status_update_bridge": "0x10010838 hp1020_status_state_update_candidate",
        "pjl_code_default": 10001,
        "pjl_code_table_base": 41000,
        "event_count": len(events),
        "direct_converter_class_counts": counts,
        "events": events,
        "pjl_410xx_table": offsets,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 Engine Event To PJL CODE Correlation",
        "",
        "This is an offline correlation model. It does not contact the printer.",
        "",
        "## Key Result",
        "",
        "- Engine queue `0x17` event words are not automatically final PJL `CODE=` values.",
        "- `0x1000a2a4` converts a status word to `CODE=`, but the mapped `410xx` path depends on data-store entry `0x1f`.",
        "- The bridge from engine/status events into user-visible status remains `0x10010838 hp1020_status_state_update_candidate` plus the status manager builders.",
        "- Therefore the safe conclusion is correlation, not one-to-one naming of every engine event as `PAPERLESS`, `FUSER`, or similar.",
        "",
        "## Converter Paths",
        "",
        f"- default code path: `{report['pjl_code_default']}`",
        f"- mapped paper/media code base: `{report['pjl_code_table_base']}`",
        "",
        "| Direct converter classification | Count |",
        "|---|---:|",
    ]
    for key, count in sorted(report["direct_converter_class_counts"].items()):
        lines.append(f"| {key} | `{count}` |")

    lines.extend(
        [
            "",
            "## Engine Event Words",
            "",
            "| Event Word | Low16 | Source | Condition | Direct CODE converter classification | Confidence |",
            "|---:|---:|---|---|---|---|",
        ]
    )
    for event in report["events"]:
        lines.append(
            f"| `{event['event_word_hex']}` | `{event['low16']}` | `{event['source_function']}` | "
            f"{event['path_or_condition']} | {event['direct_converter_class']} | `{event['confidence']}` |"
        )

    lines.extend(
        [
            "",
            "## 410xx Table",
            "",
            "This table is still useful, but it is selected through the converter's data-store lookup path, not by directly treating every engine event word as a table key.",
            "",
            "| Input/status index | Offset | PJL CODE |",
            "|---:|---:|---:|",
        ]
    )
    for row in report["pjl_410xx_table"]:
        lines.append(f"| `{row['input_value']}` | `{row['offset']}` | `{row['pjl_code']}` |")

    lines.extend(
        [
            "",
            "## Practical Meaning",
            "",
            "For open firmware, this means the non-printing status layer should first reproduce a small, known `CODE=`/`DISPLAY=` response shape. It should not pretend that raw engine event words are already stable user-facing errors.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", type=Path, default=EVENTS_TSV)
    parser.add_argument("--offsets", type=Path, default=OFFSET_TSV)
    parser.add_argument("--json-output", type=Path, default=OUT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=OUT_MD)
    args = parser.parse_args()

    report = build_report(args.events, args.offsets)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.markdown_output.write_text(render_markdown(report) + "\n")
    print(f"events={report['event_count']} classes={len(report['direct_converter_class_counts'])}")
    print(args.markdown_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
