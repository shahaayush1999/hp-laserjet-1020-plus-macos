#!/usr/bin/env python3
"""Generate the non-printing PJL/status query contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT_DIR / "analysis/non-printing-status-probe/pjl-status-contract.json"
OUT_MD = ROOT_DIR / "analysis/non-printing-status-probe/pjl-status-contract.md"
UEL = b"\x1b%-12345X"


QUERIES = [
    {
        "name": "echo",
        "command": b"@PJL ECHO HP1020_STATUS_PROBE\r\n",
        "purpose": "lowest-risk parser/response proof with a unique token",
        "stock_response_markers": ["HP1020_STATUS_PROBE"],
        "open_minimal_response": "return the same token through the USB back-channel",
    },
    {
        "name": "info-status",
        "command": b"@PJL INFO STATUS\r\n",
        "purpose": "exercise stock status response builders",
        "stock_response_markers": ["CODE=", "DISPLAY="],
        "open_minimal_response": "defer until a tiny CODE/DISPLAY builder exists",
    },
    {
        "name": "info-id",
        "command": b"@PJL INFO ID\r\n",
        "purpose": "read identity/model text without printing",
        "stock_response_markers": ["HP LaserJet 1020", "Hewlett-Packard"],
        "open_minimal_response": "return a conservative model string only after USB response path is proven",
    },
    {
        "name": "ustatus-device",
        "command": b"@PJL USTATUS DEVICE = ON\r\n",
        "purpose": "enable device status notifications for later stock calibration",
        "stock_response_markers": ["USTATUS", "CODE=", "DISPLAY=", "ONLINE="],
        "open_minimal_response": "not a first open-firmware target; stateful notifications can wait",
    },
]


def printable(data: bytes) -> str:
    return data.replace(b"\x1b", b"<ESC>").replace(b"\r", b"<CR>").replace(b"\n", b"<LF>\n").decode("ascii")


def build_contract() -> dict[str, Any]:
    queries = []
    for query in QUERIES:
        payload = payload_for_query(query["name"])
        queries.append(
            {
                "name": query["name"],
                "purpose": query["purpose"],
                "payload_bytes": len(payload),
                "payload_hex": payload.hex(" "),
                "payload_printable": printable(payload),
                "stock_response_markers": query["stock_response_markers"],
                "open_minimal_response": query["open_minimal_response"],
            }
        )
    return {
        "summary": "Exact non-printing PJL/status payload contract for stock/open firmware comparison.",
        "safety_scope": [
            "no PDF",
            "no PostScript",
            "no ZjStream raster",
            "no engine/video command from host",
            "no paper required",
        ],
        "first_recommended_query": "echo",
        "queries": queries,
    }


def payload_for_query(name: str) -> bytes:
    for query in QUERIES:
        if query["name"] == name:
            return UEL + query["command"] + UEL
    supported = ", ".join(query["name"] for query in QUERIES)
    raise SystemExit(f"unsupported query: {name}; supported: {supported}")


def render_markdown(contract: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 Non-Printing PJL/Status Contract",
        "",
        "This is an offline contract for the tiny PJL/status payloads used to compare stock HP firmware against future open firmware.",
        "It does not contact the printer.",
        "",
        "## Safety Scope",
        "",
    ]
    lines.extend(f"- {item}" for item in contract["safety_scope"])
    lines.extend(
        [
            "",
            f"- first recommended query: `{contract['first_recommended_query']}`",
            "",
            "## Payloads",
            "",
            "| Query | Bytes | Purpose | Stock response markers | Open minimal response |",
            "|---|---:|---|---|---|",
        ]
    )
    for query in contract["queries"]:
        markers = ", ".join(f"`{marker}`" for marker in query["stock_response_markers"])
        lines.append(
            f"| `{query['name']}` | `{query['payload_bytes']}` | {query['purpose']} | {markers} | {query['open_minimal_response']} |"
        )

    lines.extend(["", "## Exact Payload Text", ""])
    for query in contract["queries"]:
        lines.extend(
            [
                f"### `{query['name']}`",
                "",
                "```text",
                query["payload_printable"].rstrip(),
                "```",
                "",
            ]
        )

    lines.extend(
        [
            "## Practical Meaning",
            "",
            "The first useful stock calibration is `echo`: it has a unique token and should not change printer state.",
            "For open firmware, implementing only the echo response would be enough to prove USB/PJL back-channel execution without touching the print engine.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-output", type=Path, default=OUT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=OUT_MD)
    parser.add_argument("--write-payload", choices=[query["name"] for query in QUERIES])
    parser.add_argument("--payload-output", type=Path)
    parser.add_argument("--text-output", type=Path)
    args = parser.parse_args()

    if args.write_payload:
        if not args.payload_output or not args.text_output:
            parser.error("--write-payload requires --payload-output and --text-output")
        payload = payload_for_query(args.write_payload)
        args.payload_output.parent.mkdir(parents=True, exist_ok=True)
        args.text_output.parent.mkdir(parents=True, exist_ok=True)
        args.payload_output.write_bytes(payload)
        args.text_output.write_text(printable(payload), encoding="ascii")
        print(f"query={args.write_payload} bytes={len(payload)}")
        return 0

    contract = build_contract()
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n")
    args.markdown_output.write_text(render_markdown(contract) + "\n")
    print(f"queries={len(contract['queries'])}")
    print(args.markdown_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
