#!/usr/bin/env python3
"""Analyze HP 1020 non-printing PJL/status back-channel captures."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
CONTRACT_SCRIPT = ROOT_DIR / "scripts/model-hp1020-pjl-status-contract.py"


def load_contract_builder():
    spec = importlib.util.spec_from_file_location("hp1020_pjl_status_contract", CONTRACT_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {CONTRACT_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_contract


def printable_ascii(data: bytes) -> str:
    chars = []
    for byte in data:
        if byte == 0x1B:
            chars.append("<ESC>")
        elif byte == 0x0D:
            chars.append("<CR>")
        elif byte == 0x0A:
            chars.append("<LF>\n")
        elif byte == 0x09:
            chars.append("\t")
        elif 0x20 <= byte <= 0x7E:
            chars.append(chr(byte))
        else:
            chars.append(".")
    return "".join(chars)


def ascii_text(data: bytes) -> str:
    return "".join(chr(byte) if byte in (9, 10, 13) or 32 <= byte <= 126 else "." for byte in data)


def find_query(contract: dict[str, Any], name: str) -> dict[str, Any]:
    for query in contract["queries"]:
        if query["name"] == name:
            return query
    raise ValueError(f"unsupported query: {name}")


def analyze_capture(data: bytes, query_name: str, *, stderr_text: str = "") -> dict[str, Any]:
    contract = load_contract_builder()()
    query = find_query(contract, query_name)
    text = ascii_text(data)
    marker_hits = [
        marker
        for marker in query["stock_response_markers"]
        if marker.encode("ascii") in data or marker in text
    ]
    pjl_like_tokens = [
        token
        for token in ("@PJL", "CODE=", "DISPLAY=", "USTATUS", "ONLINE=", "HP LaserJet", "Hewlett-Packard")
        if token.encode("ascii") in data or token in text
    ]
    cups_read_lines = [
        line.strip()
        for line in stderr_text.splitlines()
        if "back-channel" in line.lower() or "read " in line.lower()
    ]

    if not data:
        verdict = "no_backchannel_bytes"
        meaning = "No response bytes were captured on CUPS fd 3."
        next_step = "If this was stock firmware, try another query or lower-level USB capture. If this was open idle, this is expected."
    elif marker_hits:
        verdict = "expected_marker_seen"
        meaning = "Captured bytes contain the expected marker for this query."
        next_step = "Use this as the stock/open comparison baseline."
    elif pjl_like_tokens:
        verdict = "pjl_response_without_expected_marker"
        meaning = "Captured bytes look PJL/status-like but did not contain the expected marker."
        next_step = "Inspect the printable capture and retry with info-status or info-id if needed."
    else:
        verdict = "bytes_without_pjl_marker"
        meaning = "The backend returned bytes, but they do not match the current PJL/status contract."
        next_step = "Keep the raw capture and compare with USB/backend logs before changing firmware."

    return {
        "query": query_name,
        "capture_bytes": len(data),
        "expected_markers": query["stock_response_markers"],
        "marker_hits": marker_hits,
        "pjl_like_tokens": pjl_like_tokens,
        "cups_backchannel_log_lines": cups_read_lines,
        "verdict": verdict,
        "meaning": meaning,
        "next_step": next_step,
        "printable": printable_ascii(data),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 PJL Back-Channel Capture Analysis",
        "",
        f"- Query: `{report['query']}`",
        f"- Captured bytes: `{report['capture_bytes']}`",
        f"- Verdict: `{report['verdict']}`",
        f"- Meaning: {report['meaning']}",
        f"- Next step: {report['next_step']}",
        "",
        "## Marker Check",
        "",
        f"- Expected markers: `{', '.join(report['expected_markers'])}`",
        f"- Marker hits: `{', '.join(report['marker_hits']) if report['marker_hits'] else 'none'}`",
        f"- PJL-like tokens: `{', '.join(report['pjl_like_tokens']) if report['pjl_like_tokens'] else 'none'}`",
        "",
    ]
    if report["cups_backchannel_log_lines"]:
        lines.extend(["## CUPS Back-Channel Log Lines", ""])
        for line in report["cups_backchannel_log_lines"]:
            lines.append(f"- `{line}`")
        lines.append("")
    lines.extend(
        [
            "## Printable Capture",
            "",
            "```text",
            report["printable"] or "(empty)",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def run_self_test() -> int:
    cases = [
        ("echo", b"\x1b%-12345X@PJL ECHO HP1020_STATUS_PROBE\r\n", "expected_marker_seen"),
        ("info-status", b'CODE=10001\r\nDISPLAY="READY"\r\n', "expected_marker_seen"),
        ("info-id", b'"Hewlett-Packard HP LaserJet 1020"\r\n', "expected_marker_seen"),
        ("ustatus-device", b'USTATUS DEVICE\r\nCODE=10001\r\nDISPLAY="READY"\r\nONLINE=TRUE\r\n', "expected_marker_seen"),
        ("echo", b"", "no_backchannel_bytes"),
        ("echo", b"\x01\x02\x03", "bytes_without_pjl_marker"),
    ]
    failures = []
    for query, data, expected in cases:
        actual = analyze_capture(data, query)["verdict"]
        if actual != expected:
            failures.append({"query": query, "expected": expected, "actual": actual})
    print(f"self_test_cases={len(cases)} failures={len(failures)}")
    if failures:
        print(json.dumps(failures, indent=2))
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, help="Raw back-channel capture file")
    parser.add_argument("--stderr", type=Path, help="Optional CUPS backend stderr log")
    parser.add_argument("--query", default="echo", choices=["echo", "info-status", "info-id", "ustatus-device"])
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return run_self_test()
    if args.capture is None:
        parser.error("--capture is required unless --self-test is used")

    data = args.capture.read_bytes()
    stderr_text = args.stderr.read_text(errors="replace") if args.stderr and args.stderr.exists() else ""
    report = analyze_capture(data, args.query, stderr_text=stderr_text)

    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(report) + "\n")

    print(f"query={report['query']} bytes={report['capture_bytes']} verdict={report['verdict']}")
    if args.markdown_output:
        print(args.markdown_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
