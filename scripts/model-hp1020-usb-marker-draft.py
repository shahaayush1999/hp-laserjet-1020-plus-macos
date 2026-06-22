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
DEVICE_DESCRIPTOR = bytes.fromhex("12 01 00 02 00 00 00 40 f0 03 17 2b 00 01 01 02 00 01")
CONFIG_DESCRIPTOR = bytes.fromhex(
    "09 02 20 00 01 01 00 c0 31 09 04 00 00 02 07 01 02 00 "
    "07 05 01 02 40 00 00 07 05 81 02 40 00 00"
)
LANG_DESCRIPTOR = bytes.fromhex("04 03 09 04")
MANUFACTURER_DESCRIPTOR = bytes.fromhex(
    "20 03 48 00 65 00 77 00 6c 00 65 00 74 00 74 00 2d 00 "
    "50 00 61 00 63 00 6b 00 61 00 72 00 64 00"
)
MARKER_DESCRIPTOR = bytes.fromhex(
    "26 03 48 00 50 00 31 00 30 00 32 00 30 00 20 00 4f 00 "
    "50 00 45 00 4e 00 20 00 4d 00 41 00 52 00 4b 00 45 00 52 00"
)
MARKER_SOURCE_POINTER = 0x90003200
DEVICE_SOURCE_POINTER = 0x90003300
CONFIG_SOURCE_POINTER = 0x90003314
LANG_SOURCE_POINTER = 0x90003334
MANUFACTURER_SOURCE_POINTER = 0x90003338
STAGING_BUFFER = 0x90022BD0
DESCRIPTOR_BASE = 0x900226F0
DESCRIPTOR_SUBMIT_REGISTER = 0xB3000014
DESCRIPTOR_FINAL_FLAG = 0x08000000
TRANSFER_KICK_OR = 0x00000108


def post_response_rearm_plan() -> dict[str, object]:
    return {
        "after_submit": "wait_for_gate_clear",
        "gate_0408_mask": "0x00006000",
        "gate_0400_mask": "0x00000003",
        "when_clear": "return_to_poll_loop",
    }


def data_stage_plan(response_len: int, source_pointer: int) -> dict[str, object]:
    return {
        "copy_source": f"0x{source_pointer:08x}",
        "staging_buffer": f"0x{STAGING_BUFFER:08x}",
        "copy_bytes": response_len,
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


def response_candidate(setup: bytes) -> dict[str, object] | None:
    descriptor_type = setup[3]
    descriptor_index = setup[2]
    candidates = {
        (0x01, 0x00): ("device", DEVICE_DESCRIPTOR, DEVICE_SOURCE_POINTER),
        (0x02, 0x00): ("configuration", CONFIG_DESCRIPTOR, CONFIG_SOURCE_POINTER),
        (0x03, 0x00): ("language", LANG_DESCRIPTOR, LANG_SOURCE_POINTER),
        (0x03, 0x01): ("manufacturer", MANUFACTURER_DESCRIPTOR, MANUFACTURER_SOURCE_POINTER),
        (0x03, 0x02): ("open marker product", MARKER_DESCRIPTOR, MARKER_SOURCE_POINTER),
    }
    selected = candidates.get((descriptor_type, descriptor_index))
    if not selected:
        return None
    name, response, source_pointer = selected
    return {
        "descriptor": name,
        "descriptor_type": descriptor_type,
        "descriptor_index": descriptor_index,
        "response": response,
        "source_pointer": source_pointer,
    }


def marker_decision(setup: bytes, gate_0408: int, gate_0400: int) -> dict[str, object]:
    state: dict[str, object] = {
        "setup_hex": setup.hex(" "),
        "gate_0408": f"0x{gate_0408:08x}",
        "gate_0400": f"0x{gate_0400:08x}",
    }

    if len(setup) != 8:
        return {**state, "result": "poll_continue", "reason": "setup packet is not 8 bytes"}

    if setup[0] != 0x80 or setup[1] != 0x06:
        return {
            **state,
            "result": "poll_continue",
            "reason": "not a standard IN GET_DESCRIPTOR request; probe keeps polling",
            "observed_prefix": setup[:2].hex(" "),
        }

    candidate = response_candidate(setup)
    if not candidate:
        return {
            **state,
            "result": "poll_continue",
            "reason": "unsupported descriptor type/index; probe keeps polling",
            "descriptor_type": setup[3],
            "descriptor_index": setup[2],
        }

    w_length = setup[6] | (setup[7] << 8)
    response_len = min(w_length, len(candidate["response"]))
    if gate_0408 & 0x00006000:
        sequence = "sequence_a"
    elif gate_0400 & 0x00000003:
        sequence = "sequence_b"
    else:
        return {
            **state,
            "result": "poll_continue",
            "reason": "neither USB status gate is active; probe keeps polling",
            "w_length": w_length,
            "candidate_response_len": response_len,
        }

    return {
        **state,
        "result": "marker_response",
        "descriptor": candidate["descriptor"],
        "descriptor_type": candidate["descriptor_type"],
        "descriptor_index": candidate["descriptor_index"],
        "sequence": sequence,
        "w_length": w_length,
        "response_len": response_len,
        "response_pointer": f"0x{STAGING_BUFFER:08x}",
        "source_pointer": f"0x{candidate['source_pointer']:08x}",
        "response_text": "HP1020 OPEN MARKER" if candidate["descriptor"] == "open marker product" else "",
        "response_hex": candidate["response"][:response_len].hex(" "),
        "data_stage": data_stage_plan(response_len, candidate["source_pointer"]),
        "post_response": post_response_rearm_plan(),
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
            "name": "configuration descriptor clipped to first 9 bytes",
            "decision": marker_decision(bytes.fromhex("80 06 00 02 00 00 09 00"), 0x00006000, 0),
        },
        {
            "name": "language string descriptor",
            "decision": marker_decision(bytes.fromhex("80 06 00 03 00 00 04 00"), 0x00006000, 0),
        },
        {
            "name": "manufacturer string descriptor",
            "decision": marker_decision(bytes.fromhex("80 06 01 03 09 04 ff 00"), 0x00006000, 0),
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
        "| Scenario | Result | Descriptor | Sequence | wLength | Response Bytes | Descriptor Word | Reason |",
        "|---|---|---|---|---:|---:|---:|---|",
    ]
    for scenario in report["scenarios"]:
        decision = scenario["decision"]
        descriptor_word = ""
        if data_stage := decision.get("data_stage"):
            descriptor_word = data_stage["descriptor_words"][0]
        lines.append(
            f"| {scenario['name']} | `{decision['result']}` | `{decision.get('descriptor', '')}` | `{decision.get('sequence', '')}` | "
            f"{decision.get('w_length', '')} | {decision.get('response_len', '')} | "
            f"`{descriptor_word}` | "
            f"{decision.get('reason', '')} |"
        )
    lines.extend(
        [
            "",
            "## Meaning",
            "",
            "- Standard `GET_DESCRIPTOR` requests for device, configuration, language, manufacturer, and product descriptors reach the response path.",
            "- Product string index 2 returns `HP1020 OPEN MARKER` instead of the stock product string.",
            "- Response length is clipped to `min(wLength, descriptor length)`.",
            "- `0xb3000408 & 0x6000` selects Sequence A.",
            "- `0xb3000400 & 0x3` selects Sequence B when Sequence A is not selected.",
            "- Matching requests copy the selected descriptor into the stock control-IN staging buffer `0x90022bd0`.",
            "- The draft builds one four-word descriptor at `0x900226f0`, submits it through `0xb3000014`, and kicks `0xb3000000 |= 0x108`.",
            "- After submitting a response, the draft waits for both USB setup/status gates to clear, then returns to the poll loop.",
            "- If the setup packet or gate state does not match, the draft keeps polling without programming endpoint-0.",
            "- This avoids the old one-shot false negative where an early non-product request could park the probe forever.",
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
    poll_continue = sum(1 for scenario in report["scenarios"] if scenario["decision"]["result"] == "poll_continue")
    print(f"scenarios={len(report['scenarios'])} marker={marker} poll_continue={poll_continue}")
    print(args.markdown_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
