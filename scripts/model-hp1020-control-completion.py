#!/usr/bin/env python3
"""Model the stock HP 1020 USB control-transfer completion event path."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT_DIR / "analysis/usb-path/control-completion-event.json"
OUT_MD = ROOT_DIR / "analysis/usb-path/control-completion-event.md"


EVIDENCE_FILES = {
    "control_sender": "analysis/usb-path/decompiled-neighbors/10008c24_hp1020_usb_control_tx_data_stage_candidate.c",
    "event_wait_wrapper": "analysis/object-creation/decompiled/10017d28_FUN_10017d28.c",
    "event_wait_core": "analysis/usb-path/decompiled-neighbors/10019408_FUN_10019408.c",
    "event_set_wrapper": "analysis/object-creation/decompiled/10017dac_FUN_10017dac.c",
    "event_set_core": "analysis/message-producers/producer-decompiled/1001896c_FUN_1001896c.c",
    "usb_interrupt_task": "analysis/tasks/task-decompiled/10008208_hp1020_task_entry_10008208.c",
    "usb2_thread": "analysis/tasks/task-decompiled/10008ff0_hp1020_usb2_thread.c",
}


def read(rel: str) -> str:
    return (ROOT_DIR / rel).read_text(errors="replace")


def require_contains(text: str, needle: str, evidence: str) -> dict[str, str]:
    return {
        "needle": needle,
        "evidence": evidence,
        "status": "present" if needle in text else "missing",
    }


def build_report() -> dict[str, Any]:
    sources = {name: read(path) for name, path in EVIDENCE_FILES.items()}
    checks = [
        require_contains(
            sources["control_sender"],
            "threadx_queue_receive_candidate(puVar1,1,1,auStack_30,0xffffffff)",
            EVIDENCE_FILES["control_sender"],
        ),
        require_contains(
            sources["event_wait_core"],
            "*(uint *)(param_1 + 8) = *(uint *)(param_1 + 8) & (param_2 ^ 0xffffffff)",
            EVIDENCE_FILES["event_wait_core"],
        ),
        require_contains(
            sources["usb_interrupt_task"],
            "FUN_10017dac(PTR_DAT_10005e18,iVar11,0)",
            EVIDENCE_FILES["usb_interrupt_task"],
        ),
        require_contains(
            sources["usb_interrupt_task"],
            "FUN_10017dac(PTR_DAT_10005e18,1 << 0x20 - (0x20 - (uVar6 + uVar8 & 0x1f)),0)",
            EVIDENCE_FILES["usb_interrupt_task"],
        ),
        require_contains(
            sources["event_set_core"],
            "param_2 = *(uint *)(param_1 + 8) | param_2",
            EVIDENCE_FILES["event_set_core"],
        ),
        require_contains(
            sources["usb2_thread"],
            "threadx_queue_receive_candidate(PTR_DAT_10005e18,DAT_10005f20,1,auStack_50,0xffffffff)",
            EVIDENCE_FILES["usb2_thread"],
        ),
    ]
    missing = [check for check in checks if check["status"] != "present"]
    return {
        "summary": "Static model of the stock USB event-flag object used by endpoint-0 completion.",
        "status": "pass" if not missing else "fail",
        "event_object": "0x10021318",
        "event_state_word_offset": "0x08",
        "control_in_wait": {
            "function": "0x10008c24 hp1020_usb_control_tx_data_stage_candidate",
            "wrapper": "0x10017d28 event_flags_get_wrapper_candidate",
            "core": "0x10019408 event_flags_get_core_candidate",
            "requested_bits": "0x00000001",
            "mode": "0x00000001",
            "mode_meaning": "OR wait, clear matched bits on success",
            "timeout": "0xffffffff",
        },
        "usb2_thread_wait": {
            "function": "0x10008ff0 hp1020_usb2_thread",
            "requested_bits": "0x00010000",
            "mode": "0x00000001",
            "meaning": "main USB service-loop wake event, distinct from the control-IN completion bit",
        },
        "event_setter": {
            "interrupt_task": "0x10008208 hp1020_usb_interrupt_task_candidate",
            "wrapper": "0x10017dac event_flags_set_wrapper_candidate",
            "core": "0x1001896c event_flags_set_core_candidate",
            "operation": "event_state_word |= bits; wake suspended waiters whose masks now match",
            "bit_source": "1 << ((event_group_base + event_index) & 0x1f)",
        },
        "open_firmware_implication": [
            "The stock path does not just poll a simple completion register after 0xb3000000 |= 0x108.",
            "It relies on USB interrupt 4 feeding an event-flag object at 0x10021318.",
            "The current marker draft submits the descriptor and idles; that might be enough for one host read, but it does not prove rearm/cleanup semantics.",
            "A standalone open implementation either needs a tiny interrupt/event path or a live-tested polling rule for the relevant 0xb300 registers.",
        ],
        "checks": checks,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 USB Control Completion Event Model",
        "",
        "This is an offline model. It does not contact the printer.",
        "",
        "## Key Result",
        "",
        "- The object at `0x10021318` is better modeled as an event-flag object, not a message queue.",
        "- The stock control-IN sender waits for bit `0x00000001`, with clear-on-success behavior and infinite timeout.",
        "- USB interrupt task `0x10008208` is the static source that sets bits on this same object.",
        "- The main USB2Thread service loop waits on bit `0x00010000`, so the same event object carries multiple USB event lanes.",
        "",
        "## Control-IN Wait",
        "",
        "| Field | Value |",
        "|---|---|",
    ]
    for key, value in report["control_in_wait"].items():
        lines.append(f"| `{key}` | `{value}` |")

    lines.extend(["", "## Event Setter", "", "| Field | Value |", "|---|---|"])
    for key, value in report["event_setter"].items():
        lines.append(f"| `{key}` | `{value}` |")

    lines.extend(["", "## Open-Firmware Meaning", ""])
    for item in report["open_firmware_implication"]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## Evidence Checks",
            "",
            f"- status: `{report['status']}`",
            "",
            "| Status | Evidence | Needle |",
            "|---|---|---|",
        ]
    )
    for check in report["checks"]:
        needle = check["needle"].replace("|", "\\|")
        lines.append(f"| `{check['status']}` | `{check['evidence']}` | `{needle}` |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-output", type=Path, default=OUT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=OUT_MD)
    args = parser.parse_args()

    report = build_report()
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.markdown_output.write_text(render_markdown(report) + "\n")
    print(f"status={report['status']} checks={len(report['checks'])}")
    print(args.markdown_output)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
