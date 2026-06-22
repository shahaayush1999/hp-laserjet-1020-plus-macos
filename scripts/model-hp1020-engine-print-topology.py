#!/usr/bin/env python3
"""Synthesize the HP 1020 engine-side print topology.

This is offline analysis only. It ties the generated command/status model and
status-decision model to the engine thread and message dispatcher so the
mechanical boundary is described as an ordered control path.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
COMMAND_MODEL_JSON = ROOT_DIR / "analysis/hardware-boundary/engine-command-status.json"
DECISIONS_JSON = ROOT_DIR / "analysis/hardware-boundary/engine-status-decisions.json"
FIRST_PAGE_JSON = ROOT_DIR / "analysis/hardware-boundary/first-page-hardware-sequence.json"
OUT_JSON = ROOT_DIR / "analysis/hardware-boundary/engine-print-topology.json"
OUT_MD = ROOT_DIR / "analysis/hardware-boundary/engine-print-topology.md"

SOURCES = {
    "engine_thread": ROOT_DIR / "analysis/dispatch-mmio/decompiled/100163b0_hp1020_engine_thread_candidate.c",
    "dispatch": ROOT_DIR / "analysis/dispatch-mmio/decompiled/10016164_hp1020_engine_message_dispatch_candidate.c",
    "preflight": ROOT_DIR / "analysis/dispatch-mmio/decompiled/100160a8_hp1020_engine_preflight_candidate.c",
    "engine_io": ROOT_DIR / "analysis/dispatch-mmio/decompiled/10015c68_hp1020_engine_status_io_candidate.c",
    "poll": ROOT_DIR / "analysis/dispatch-mmio/decompiled/10015df8_hp1020_engine_status_poll_candidate.c",
}

CHECKS = [
    ("thread_clears_active_work", "engine_thread", "*(undefined4 *)(PTR_DAT_10006920 + 0x68) = 0"),
    ("thread_runs_preflight", "engine_thread", "hp1020_engine_preflight_candidate();"),
    ("thread_polls_until_not_high_bit", "engine_thread", "while (uVar3 = hp1020_engine_status_poll_candidate(0), (uVar3 & uVar1) == uVar1)"),
    ("thread_receive_or_poll_loop", "engine_thread", "threadx_queue_receive_wait_candidate"),
    ("dispatch_0b_40_accepts_work", "dispatch", "case 0x40:"),
    ("dispatch_stores_active_work", "dispatch", "*(undefined4 *)(puVar2 + 0x68) = param_1[3]"),
    ("dispatch_stores_deferred_work", "dispatch", "*(undefined4 *)(puVar2 + 0x6c) = param_1[3]"),
    ("dispatch_maps_engine_config", "dispatch", "FUN_100162b0(*(undefined2 *)(*(int *)(PTR_DAT_10006920 + 0x68) + 0x80))"),
    ("dispatch_start_command_6012", "dispatch", "hp1020_engine_status_io_candidate(DAT_100069a4)"),
    ("dispatch_reset_command_3a13", "dispatch", "uVar4 = hp1020_engine_status_io_candidate(DAT_100069a0)"),
    ("dispatch_completion_message_11", "dispatch", "case 0x11:"),
    ("dispatch_requeues_deferred_work", "dispatch", "hp1020_send_or_raise_engine_msg_candidate(0,&local_40)"),
    ("preflight_emits_1100", "preflight", "uStack_3c = DAT_100063dc"),
    ("preflight_sets_command_bit", "preflight", "*hp1020_engine_command_reg_table_word = *hp1020_engine_command_reg_table_word | DAT_10005e74"),
    ("preflight_timeout_event", "preflight", "uStack_2c = DAT_1000692c"),
    ("engine_io_register_pair", "engine_io", "*puVar6 = *puVar6 & uVar1 | (uint)*(ushort *)(puVar4 + 0x5a)"),
    ("poll_status_decision_entry", "poll", "uVar4 = hp1020_engine_status_io_candidate(1)"),
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def source_checks() -> list[dict[str, str]]:
    source_text = {name: path.read_text(errors="replace") for name, path in SOURCES.items()}
    return [
        {
            "name": name,
            "status": "present" if needle in source_text[source] else "missing",
            "source": str(SOURCES[source].relative_to(ROOT_DIR)),
            "needle": needle,
        }
        for name, source, needle in CHECKS
    ]


def build_report() -> dict[str, Any]:
    command_model = read_json(COMMAND_MODEL_JSON)
    decisions = read_json(DECISIONS_JSON)
    first_page = read_json(FIRST_PAGE_JSON)
    literals = command_model.get("literal_values", {})
    checks = source_checks()
    check_status = "pass" if all(item["status"] == "present" for item in checks) else "fail"

    event_decisions = {item.get("event") for item in command_model.get("event_decisions", [])}
    side_effect_commands = {
        item.get("value")
        for item in command_model.get("status_io_calls", [])
        if item.get("kind") == "engine_command"
    }
    return {
        "summary": "Engine-side topology for startup/preflight, page dispatch, polling, completion, and deferred work.",
        "status": "pass"
        if check_status == "pass"
        and command_model.get("status") == "pass"
        and decisions.get("status") == "pass"
        else "fail",
        "source_reports": [
            str(COMMAND_MODEL_JSON.relative_to(ROOT_DIR)),
            str(DECISIONS_JSON.relative_to(ROOT_DIR)),
            str(FIRST_PAGE_JSON.relative_to(ROOT_DIR)),
        ],
        "registers": {
            "engine_status": literals.get("engine_status_register"),
            "engine_command": literals.get("engine_command_register"),
        },
        "important_commands": {
            "preflight_start_bit": literals.get("preflight_start_bit"),
            "page_start_normal": literals.get("command_0x6012"),
            "page_start_reset_latch": literals.get("command_0x3a13"),
            "substatus_side_effect": literals.get("command_0x501a"),
            "leave_e6100800_side_effect": literals.get("command_0x5043"),
        },
        "important_events": sorted(event for event in event_decisions if event),
        "side_effect_commands_seen": sorted(command for command in side_effect_commands if command),
        "topology": [
            {
                "name": "engine_thread_startup",
                "functions": ["0x100163b0 engine thread", "0x100160a8 preflight", "0x10015df8 status poll"],
                "steps": [
                    "clear active engine work pointer +0x68",
                    "run preflight, which emits engine message 0x17/e6101100 and sets command-register bit 0x20000",
                    "poll engine status until the high-bit event family clears",
                    "register engine datastore callbacks for density/media entries",
                    "enter receive-with-timeout loop; on timeout, poll status again",
                ],
            },
            {
                "name": "page_work_acceptance",
                "functions": ["0x10016164 engine message dispatch", "0x10015c68 engine status I/O"],
                "steps": [
                    "messages 0x0b and 0x40 poll status before accepting work",
                    "first work pointer is stored at engine state +0x68; a second pending pointer is stored at +0x6c",
                    "active work +0x80 selects an engine config through 0x100162b0 and stores it at +0x48",
                    "normal start submits command 0x6012; reset-latch start submits 0x3a13 and keeps the latch if the ready mask is absent",
                ],
            },
            {
                "name": "status_poll_and_recovery",
                "functions": ["0x10015df8 status poll", "0x10015c68 engine status I/O"],
                "steps": [
                    "poll reads status commands 1, 0x20, 2, 0x16, and 0x13 depending on branch conditions",
                    "selected event words are stored at engine state +0x60 and emitted as queue 1 message 0x17 when changed",
                    "side-effect commands 0x501a and 0x5043 are sent from specific status transitions",
                    "some transitions can call video reset dispatch before engine completion continues",
                ],
            },
            {
                "name": "completion_and_deferred_work",
                "functions": ["0x10016164 message 0x11 case", "video completion feedback"],
                "steps": [
                    "message 0x11 polls status after video/engine completion",
                    "when no high-bit error family remains, active work +0x68 is returned via message 0x11",
                    "if deferred work +0x6c exists, dispatch requeues message 0x0b and clears +0x6c",
                ],
            },
        ],
        "open_firmware_implication": [
            "This is the mechanical gate for printing: custom firmware cannot safely skip it and only drive video registers.",
            "The command IDs and event words are now organized as a page-start state machine, but physical labels still require printer-side calibration.",
            "The next printer-attached tests should capture non-printing status responses before any custom firmware tries to reproduce this path.",
        ],
        "checks": checks,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 Engine Print Topology",
        "",
        "This is a generated offline synthesis. It does not contact the printer.",
        "",
        "## Result",
        "",
        f"- status: `{report['status']}`",
        f"- engine status register: `{report['registers']['engine_status']}`",
        f"- engine command register: `{report['registers']['engine_command']}`",
        "",
        "## Important Commands",
        "",
        "| Name | Value |",
        "|---|---:|",
    ]
    for name, value in report["important_commands"].items():
        lines.append(f"| `{name}` | `{value}` |")

    lines.extend(["", "## Topology", ""])
    for item in report["topology"]:
        lines.extend([f"### `{item['name']}`", "", "- functions: " + ", ".join(f"`{fn}`" for fn in item["functions"]), ""])
        for index, step in enumerate(item["steps"], 1):
            lines.append(f"{index}. {step}")
        lines.append("")

    lines.extend(["## Important Events", ""])
    for event in report["important_events"]:
        lines.append(f"- `{event}`")

    lines.extend(["", "## Open Firmware Meaning", ""])
    for item in report["open_firmware_implication"]:
        lines.append(f"- {item}")

    lines.extend(["", "## Evidence Checks", "", "| Check | Status | Source | Needle |", "|---|---|---|---|"])
    for item in report["checks"]:
        needle = item["needle"].replace("|", "\\|")
        lines.append(f"| `{item['name']}` | `{item['status']}` | `{item['source']}` | `{needle}` |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    OUT_MD.write_text(render_markdown(report))
    print(f"status={report['status']} checks={len(report['checks'])} stages={len(report['topology'])}")
    print(OUT_MD)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
