#!/usr/bin/env python3
"""Model the boundary between engine event words and PJL CODE values."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
EVENTS_TSV = ROOT_DIR / "analysis/engine-events/engine-0x17-events.tsv"
OFFSET_TSV = ROOT_DIR / "analysis/status-path/status-code-offset-table.tsv"
OUT_JSON = ROOT_DIR / "analysis/status-path/status-code-correlation.json"
OUT_MD = ROOT_DIR / "analysis/status-path/status-code-correlation.md"
EXECUTION_JSON = ROOT_DIR / "analysis/status-path/status-code-execution.json"


def parse_int(text: str) -> int:
    return int(text, 0)


def load_events(path: Path, codes: list[list[int]]) -> list[dict[str, Any]]:
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
                    **classify_direct_converter_path(event_word, codes),
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


def classify_direct_converter_path(status_word: int, codes: list[list[int]]) -> dict[str, Any]:
    low16 = status_word & 0xFFFF
    if (low16 & 0xFF00) == 0x0100:
        return dict(direct_converter_class="default 10001", direct_code=10001)
    if (status_word & 0x00020000) and not (status_word & 0x80000000):
        return dict(direct_converter_class="default 10001", direct_code=10001)
    if low16 == 0x1001:
        return dict(direct_converter_class="datastore31 media lookup", direct_code=None)
    found = next(((i,value) for i,(key,value) in enumerate(codes) if key == low16), None)
    code = found[1] if found else 0
    if not code and not status_word & 0x80000000:
        return dict(direct_converter_class="default 10001", direct_code=10001)
    kind = "zero result" if not code else "ordinary code table" if found[0] < 111 else "adjacent-data alias"
    return dict(direct_converter_class=kind, direct_code=code,
                table_match_index=found[0] if found else None)


def build_report(events_path: Path, offsets_path: Path, execution_path: Path) -> dict[str, Any]:
    execution = json.loads(execution_path.read_bytes())
    assert execution["status"] == "pass"
    assert execution["elf_sha256"] == hashlib.sha256((ROOT_DIR/"analysis/sihp1020.elf").read_bytes()).hexdigest()
    assert all(hashlib.sha256((ROOT_DIR/name).read_bytes()).hexdigest() == value
               for name,value in execution["source_sha256"].items()), "rerun original CODE execution after source edits"
    codes = execution["ordinary_code_rows"]+execution["adjacent_data_aliases"]["code_rows"]
    assert len(codes) == execution["code_loop_entries"] == 222
    events = load_events(events_path, codes)
    offsets = load_offsets(offsets_path)
    assert [(parse_int(row["input_value"]),parse_int(row["offset"])) for row in offsets] == [
        tuple(row) for row in execution["ordinary_offset_rows"]]
    counts: dict[str, int] = {}
    for event in events:
        key = event["direct_converter_class"]
        counts[key] = counts.get(key, 0) + 1
    return {
        "summary": "Byte-backed, executed numeric conversion; event delivery and physical meaning remain separate.",
        "converter_function": "0x1000a2a4 hp1020_status_word_to_pjl_code_candidate",
        "status_update_bridge": "0x10010838 hp1020_status_state_update_candidate",
        "pjl_code_default": 10001,
        "pjl_code_table_base": 41000,
        "event_count": len(events),
        "direct_converter_class_counts": counts,
        "events": events,
        "pjl_410xx_table": offsets,
        "execution_sha256": hashlib.sha256(execution_path.read_bytes()).hexdigest(),
        "code_rows_before_media_table": 111,
        "stock_code_scan_rows": 222,
        "media_rows_before_following_data": 20,
        "stock_media_scan_rows": 40,
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
        "- The truncated decompilation omitted the ordinary numeric lookup in `0x1000a2a4`. Original bytes and interpreter/QEMU execution now recover it; `status-code-execution.json` contains the current evidence.",
        "- The separate `410xx` path depends on datastore `0x1f`'s media key and word at+8: a nonzero word adds `(word+1)*100` with native32-bit arithmetic.",
        "- The ordinary scan executes222 four-byte rows, continuing past111 code pairs into the media table and following strings/data. The media scan similarly executes40 rows although the next object follows20 pairs. Tested adjacent-data aliases are original behavior, not replacement requirements.",
        "- The values below are direct converter results. StatusMgr priority/source filtering, subscription and physical calibration still determine whether/why a notification is emitted. Names such as `PAPERLESS` and `FUSER` remain configuration-table names, not evidence of a raw event's meaning.",
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
            "| Event Word | Low16 | Source | Condition | Direct CODE | Path |",
            "|---:|---:|---|---|---:|---|",
        ]
    )
    for event in report["events"]:
        lines.append(
            f"| `{event['event_word_hex']}` | `{event['low16']}` | `{event['source_function']}` | "
            f"{event['path_or_condition']} | `{event['direct_code']}` | {event['direct_converter_class']} |"
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
            "Use the recovered ordinary mappings when connecting known engine observations to compatible status replies. Do not copy the adjacent-data aliases, turn a supplied numeric fixture into a sensed condition, or manufacture ready/job completion from input decoding. The open command path provides ECHO and INFO STATUS from an explicitly supplied current CODE/ONLINE observation; no physical status provider is implemented.",
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
    parser.add_argument("--execution", type=Path, default=EXECUTION_JSON)
    args = parser.parse_args()

    report = build_report(args.events, args.offsets, args.execution)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.markdown_output.write_text(render_markdown(report) + "\n")
    print(f"events={report['event_count']} classes={len(report['direct_converter_class_counts'])}")
    print(args.markdown_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
