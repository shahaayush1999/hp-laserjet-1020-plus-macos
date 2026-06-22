#!/usr/bin/env python3
"""Synthesize the USB bulk parser-shim contract from generated reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
INPUTS = {
    "bulk_receive": ROOT_DIR / "analysis/usb-path/usb-bulk-receive-model.json",
    "bulk_callbacks": ROOT_DIR / "analysis/usb-path/usb-bulk-callbacks-model.json",
    "bulk_rearm": ROOT_DIR / "analysis/usb-path/usb-bulk-rearm-model.json",
    "interrupt_events": ROOT_DIR / "analysis/usb-path/usb-interrupt-events.json",
}
OUT_JSON = ROOT_DIR / "analysis/usb-path/usb-parser-shim-contract.json"
OUT_MD = ROOT_DIR / "analysis/usb-path/usb-parser-shim-contract.md"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def check(name: str, ok: bool, detail: str, evidence: str) -> dict[str, str]:
    return {
        "name": name,
        "status": "present" if ok else "missing",
        "detail": detail,
        "evidence": evidence,
    }


def build_contract() -> dict[str, Any]:
    bulk_receive = load_json(INPUTS["bulk_receive"])
    bulk_callbacks = load_json(INPUTS["bulk_callbacks"])
    bulk_rearm = load_json(INPUTS["bulk_rearm"])
    interrupt_events = load_json(INPUTS["interrupt_events"])

    receive_constants = bulk_receive.get("constants", {})
    callback_constants = bulk_callbacks.get("constants", {})
    rearm_constants = bulk_rearm.get("constants", {})
    interrupt_scan = interrupt_events.get("event_scan", {})
    bulk_lane = interrupt_scan.get("bulk_receive_lane", {})
    buffer_updates = interrupt_scan.get("bulk_buffer_updates", {})
    parser_handoff = bulk_receive.get("parser_handoff", {})
    transfer_record = bulk_receive.get("transfer_record", {})

    implementation_contract = {
        "parser_boundary": {
            "parser_entry": parser_handoff.get("parser_entry"),
            "parser_read_callback_slot": "param_1 + 0x0c",
            "stock_parser_output_queue": parser_handoff.get("parser_sends_jobmgr_queue"),
            "meaning": "The ZjStream parser is decoupled from USB hardware behind a read callback.",
        },
        "transfer_registration": {
            "record_stride": transfer_record.get("record_stride"),
            "ring_base": transfer_record.get("ring_base"),
            "ring_index_word": transfer_record.get("ring_index_word"),
            "buffer_allocation": transfer_record.get("buffer_allocation"),
            "registered_low_level_read_callback": receive_constants.get("registered_callback_a"),
            "registered_completion_callback": receive_constants.get("registered_callback_b"),
        },
        "bulk_read_state": {
            "event_flags_object": callback_constants.get("completion_event_flags"),
            "wait_event_bit": callback_constants.get("bulk_event_bit"),
            "available_size_word": buffer_updates.get("available_size_word"),
            "source_offset_word": buffer_updates.get("source_offset_word"),
            "destination_offset_word": buffer_updates.get("destination_offset_word"),
            "remaining_request_word": buffer_updates.get("remaining_request_word"),
            "threshold_word": buffer_updates.get("threshold_word"),
            "next_pointer_word": buffer_updates.get("next_pointer_word"),
            "buffer_base_word": buffer_updates.get("buffer_base_word"),
        },
        "hardware_receive_lane": {
            "event_bit": bulk_lane.get("event_bit"),
            "lane_status_register": bulk_lane.get("lane_status_register"),
            "lane_ack_register": bulk_lane.get("lane_ack_register"),
            "completion_status_bit": interrupt_scan.get("completion_status_bit"),
            "ack_bits": bulk_lane.get("ack_bits"),
        },
        "descriptor_rearm": {
            "descriptor_pool": rearm_constants.get("descriptor_pool"),
            "bulk_buffer_base": rearm_constants.get("bulk_buffer_base"),
            "descriptor_submit_register": rearm_constants.get("descriptor_submit_register"),
            "descriptor_target_bytes": "+0x08..+0x0b",
            "alignment_rule": "use next aligned pointer only when non-zero and 16-byte aligned; otherwise use bulk_buffer_base + offset",
            "done_flags": {
                "bulk_done_byte": rearm_constants.get("bulk_done_byte"),
                "bulk_rx_done_flag": rearm_constants.get("bulk_rx_done_flag"),
            },
        },
    }

    staged_plan = [
        {
            "stage": "bulk_counter_probe",
            "purpose": "Observe bank-1/lane-1 completion and buffer counters without printing.",
            "requires_printer": True,
            "risk": "low if it never sends engine/video commands",
        },
        {
            "stage": "bulk_echo_or_discard_firmware",
            "purpose": "Accept bulk OUT bytes, update a counter/state marker, and keep the printer mechanically idle.",
            "requires_printer": True,
            "risk": "low-to-medium until endpoint-0 marker execution is proven",
        },
        {
            "stage": "minimal_zjs_chunk_reader",
            "purpose": "Parse only enough ZjStream framing to count document/page/raster chunks, still without video or engine output.",
            "requires_printer": False,
            "risk": "software-only until connected to USB receive",
        },
        {
            "stage": "print_path_handoff",
            "purpose": "Only after USB receive and chunk parsing are proven, connect parsed raster/page objects to video/engine models.",
            "requires_printer": True,
            "risk": "high",
        },
    ]

    checks = [
        check(
            "bulk_receive_model_passes",
            bulk_receive.get("status") == "pass",
            "Bulk receive registration model must be green.",
            "analysis/usb-path/usb-bulk-receive-model.json",
        ),
        check(
            "bulk_callback_model_passes",
            bulk_callbacks.get("status") == "pass",
            "Bulk callback model must be green.",
            "analysis/usb-path/usb-bulk-callbacks-model.json",
        ),
        check(
            "bulk_rearm_model_passes",
            bulk_rearm.get("status") == "pass",
            "Bulk re-arm model must be green.",
            "analysis/usb-path/usb-bulk-rearm-model.json",
        ),
        check(
            "interrupt_model_has_bulk_lane",
            interrupt_events.get("status") == "pass"
            and bulk_lane.get("event_bit") == "0x00020000"
            and bulk_lane.get("lane_status_register") == "0xb3000224"
            and bulk_lane.get("lane_ack_register") == "0xb3000220",
            "USB interrupt model must preserve the bank-1/lane-1 bulk receive lane.",
            "analysis/usb-path/usb-interrupt-events.json",
        ),
        check(
            "descriptor_rearm_constants_resolved",
            rearm_constants.get("descriptor_pool") == "0x90021370"
            and rearm_constants.get("bulk_buffer_base") == "0x900216f0"
            and rearm_constants.get("descriptor_submit_register") == "0xb3000234",
            "Descriptor pool, buffer base, and submit register must be concrete.",
            "analysis/usb-path/usb-bulk-rearm-model.json",
        ),
    ]
    status = "pass" if all(item["status"] == "present" for item in checks) else "fail"

    return {
        "summary": "USB bulk parser-shim implementation contract for the narrow print path.",
        "status": status,
        "implementation_contract": implementation_contract,
        "staged_plan": staged_plan,
        "current_decision": "Do not drive video/engine hardware from open code until endpoint-0 execution, bulk receive, and non-printing chunk parsing are proven.",
        "checks": checks,
    }


def render_markdown(contract: dict[str, Any]) -> str:
    impl = contract["implementation_contract"]
    lines = [
        "# HP 1020 USB Parser Shim Contract",
        "",
        "This generated report combines the current USB receive models into one implementation contract. It does not contact the printer.",
        "",
        "## Plain-English Meaning",
        "",
        "The stock firmware keeps the print parser away from raw USB hardware. USB fills a buffer, wakes a read callback, and that callback feeds parser bytes. For open firmware, the next narrow software target is to reproduce that shim: accept bulk bytes, maintain the buffer counters, and provide a parser-facing read function.",
        "",
        "## Parser Boundary",
        "",
    ]
    for key, value in impl["parser_boundary"].items():
        lines.append(f"- `{key}`: {value}")

    lines.extend(["", "## Transfer Registration", ""])
    for key, value in impl["transfer_registration"].items():
        lines.append(f"- `{key}`: `{value}`")

    lines.extend(["", "## Bulk Read State", ""])
    for key, value in impl["bulk_read_state"].items():
        lines.append(f"- `{key}`: `{value}`")

    lines.extend(["", "## Hardware Receive Lane", ""])
    for key, value in impl["hardware_receive_lane"].items():
        if isinstance(value, list):
            value = ", ".join(f"`{item}`" for item in value)
            lines.append(f"- `{key}`: {value}")
        else:
            lines.append(f"- `{key}`: `{value}`")

    lines.extend(["", "## Descriptor Re-Arm", ""])
    for key, value in impl["descriptor_rearm"].items():
        if isinstance(value, dict):
            lines.append(f"- `{key}`:")
            for subkey, subvalue in value.items():
                lines.append(f"  - `{subkey}`: `{subvalue}`")
        else:
            lines.append(f"- `{key}`: `{value}`")

    lines.extend(["", "## Staged Plan", "", "| Stage | Purpose | Requires printer | Risk |", "|---|---|---:|---|"])
    for item in contract["staged_plan"]:
        lines.append(f"| `{item['stage']}` | {item['purpose']} | `{str(item['requires_printer']).lower()}` | `{item['risk']}` |")

    lines.extend(["", "## Current Decision", "", contract["current_decision"], "", "## Evidence Checks", "", f"- status: `{contract['status']}`", "", "| Status | Name | Evidence | Detail |", "|---|---|---|---|"])
    for item in contract["checks"]:
        lines.append(f"| `{item['status']}` | `{item['name']}` | `{item['evidence']}` | {item['detail']} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-output", type=Path, default=OUT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=OUT_MD)
    args = parser.parse_args()

    contract = build_contract()
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n")
    args.markdown_output.write_text(render_markdown(contract) + "\n")
    print(f"status={contract['status']} checks={len(contract['checks'])}")
    print(args.markdown_output)
    return 0 if contract["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
