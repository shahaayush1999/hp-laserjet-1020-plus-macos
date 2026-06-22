#!/usr/bin/env python3
"""Model the HP 1020 USB marker draft's setup/gate decision logic."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_JSON = ROOT_DIR / "analysis/open-firmware-probes/usb-marker-draft/behavior-model.json"
DEFAULT_MD = ROOT_DIR / "analysis/open-firmware-probes/usb-marker-draft/behavior-model.md"
MARKER_LEN = 0x26
SETUP_PRODUCT_STRING = bytes.fromhex("80 06 02 03 09 04 ff 00")
MARKER_SOURCE_POINTER = 0x90003200
STAGING_BUFFER = 0x90022BD0
DESCRIPTOR_BASE = 0x900226F0
DESCRIPTOR_SUBMIT_REGISTER = 0xB3000014
DESCRIPTOR_FINAL_FLAG = 0x08000000
TRANSFER_KICK_OR = 0x00000108


def data_stage_plan(response_len: int) -> dict[str, object]:
    return {
        "copy_source": f"0x{MARKER_SOURCE_POINTER:08x}",
        "staging_buffer": f"0x{STAGING_BUFFER:08x}",
        "copy_bytes": MARKER_LEN,
        "descriptor_base": f"0x{DESCRIPTOR_BASE:08x}",
        "descriptor_words": [
            f"0x{DESCRIPTOR_FINAL_FLAG | response_len:08x}",
            "0x00000000",
            f"0x{STAGING_BUFFER:08x}",
            "0x00000000",
        ],
        "descriptor_submit_register": f"0x{DESCRIPTOR_SUBMIT_REGISTER:08x}",
        "descriptor_submit_value": f"0x{DESCRIPTOR_BASE:08x}",
        "transfer_kick_or": f"0x{TRANSFER_KICK_OR:08x}",
    }


def marker_decision(setup: bytes, gate_0408: int, gate_0400: int) -> dict[str, object]:
    state: dict[str, object] = {
        "setup_hex": setup.hex(" "),
        "gate_0408": f"0x{gate_0408:08x}",
        "gate_0400": f"0x{gate_0400:08x}",
    }

    if len(setup) != 8:
        return {**state, "result": "no_match", "reason": "setup packet is not 8 bytes"}

    expected_prefix = SETUP_PRODUCT_STRING[:4]
    if setup[:4] != expected_prefix:
        return {
            **state,
            "result": "no_match",
            "reason": "not GET_DESCRIPTOR string index 2",
            "observed_prefix": setup[:4].hex(" "),
        }

    w_length = setup[6] | (setup[7] << 8)
    response_len = min(w_length, MARKER_LEN)
    if gate_0408 & 0x00006000:
        sequence = "sequence_a"
    elif gate_0400 & 0x00000003:
        sequence = "sequence_b"
    else:
        return {
            **state,
            "result": "no_match",
            "reason": "neither USB status gate is active",
            "w_length": w_length,
            "candidate_response_len": response_len,
        }

    return {
        **state,
        "result": "marker_response",
        "sequence": sequence,
        "w_length": w_length,
        "response_len": response_len,
        "response_pointer": f"0x{STAGING_BUFFER:08x}",
        "marker_source_pointer": f"0x{MARKER_SOURCE_POINTER:08x}",
        "response_text": "HP1020 OPEN MARKER",
        "data_stage": data_stage_plan(response_len),
    }


def scenarios() -> list[dict[str, object]]:
    return [
        {
            "name": "product string, sequence A gate, full host length",
            "decision": marker_decision(SETUP_PRODUCT_STRING, 0x00006000, 0),
        },
        {
            "name": "product string, sequence B gate, full host length",
            "decision": marker_decision(SETUP_PRODUCT_STRING, 0, 0x00000001),
        },
        {
            "name": "product string, both gates clear",
            "decision": marker_decision(SETUP_PRODUCT_STRING, 0, 0),
        },
        {
            "name": "product string, clipped host length",
            "decision": marker_decision(bytes.fromhex("80 06 02 03 09 04 04 00"), 0x00006000, 0),
        },
        {
            "name": "device descriptor request",
            "decision": marker_decision(bytes.fromhex("80 06 00 01 00 00 12 00"), 0x00006000, 0),
        },
        {
            "name": "class request",
            "decision": marker_decision(bytes.fromhex("21 0a 00 00 00 00 00 00"), 0x00006000, 0),
        },
    ]


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# HP 1020 USB Marker Draft Behavior Model",
        "",
        "This is a host-side model of the marker draft's own setup/gate logic.",
        "It mirrors the assembly-level decision boundary and does not touch hardware.",
        "",
        "## Scenario Matrix",
        "",
        "| Scenario | Result | Sequence | wLength | Response Bytes | Descriptor Word | Reason |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for scenario in report["scenarios"]:
        decision = scenario["decision"]
        descriptor_word = ""
        if data_stage := decision.get("data_stage"):
            descriptor_word = data_stage["descriptor_words"][0]
        lines.append(
            f"| {scenario['name']} | `{decision['result']}` | `{decision.get('sequence', '')}` | "
            f"{decision.get('w_length', '')} | {decision.get('response_len', '')} | "
            f"`{descriptor_word}` | "
            f"{decision.get('reason', '')} |"
        )
    lines.extend(
        [
            "",
            "## Meaning",
            "",
            "- Only `GET_DESCRIPTOR` string index 2 reaches the marker response path.",
            "- Response length is clipped to `min(wLength, 38)`.",
            "- `0xb3000408 & 0x6000` selects Sequence A.",
            "- `0xb3000400 & 0x3` selects Sequence B when Sequence A is not selected.",
            "- Matching requests copy the marker descriptor from `0x90003200` into the stock control-IN staging buffer `0x90022bd0`.",
            "- The draft builds one four-word descriptor at `0x900226f0`, submits it through `0xb3000014`, and kicks `0xb3000000 |= 0x108`.",
            "- If neither gate is active, the draft parks without programming endpoint-0.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MD)
    args = parser.parse_args()

    report = {"scenarios": scenarios()}
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.markdown_output.write_text(render_markdown(report) + "\n")

    marker = sum(1 for scenario in report["scenarios"] if scenario["decision"]["result"] == "marker_response")
    no_match = len(report["scenarios"]) - marker
    print(f"scenarios={len(report['scenarios'])} marker={marker} no_match={no_match}")
    print(args.markdown_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
