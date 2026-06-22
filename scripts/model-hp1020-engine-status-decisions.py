#!/usr/bin/env python3
"""Model HP 1020 engine status-poll decisions.

This is offline analysis only. It converts the nested branch tree in
`0x10015df8 hp1020_engine_status_poll_candidate` into a small executable model
and a scenario table. The model is intentionally conservative: it predicts
stock firmware event words and side-effect engine commands, not human labels
such as "paper empty" or "cover open".
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
ENGINE_MODEL_JSON = ROOT_DIR / "analysis/hardware-boundary/engine-command-status.json"
OUT_JSON = ROOT_DIR / "analysis/hardware-boundary/engine-status-decisions.json"
OUT_MD = ROOT_DIR / "analysis/hardware-boundary/engine-status-decisions.md"
POLL_SOURCE = ROOT_DIR / "analysis/dispatch-mmio/decompiled/10015df8_hp1020_engine_status_poll_candidate.c"

CHECKS = [
    ("primary_read", "uVar4 = hp1020_engine_status_io_candidate(1)"),
    ("status_0x20_read", "uVar5 = hp1020_engine_status_io_candidate(0x20)"),
    ("status_2_read", "uVar5 = hp1020_engine_status_io_candidate(2)"),
    ("substatus_0x16_read", "uVar7 = hp1020_engine_status_io_candidate(0x16)"),
    ("substatus_0x13_read", "uVar9 = hp1020_engine_status_io_candidate(0x13)"),
    ("ready_rewrite", "if ((uVar6 & 0xffff) == DAT_10006974)"),
    ("previous_low16_transition", "((*(uint *)(PTR_DAT_10006920 + 0x60) & 0xffff) == 0x100)"),
    ("leave_e6100800_side_effect", "hp1020_engine_status_io_candidate(DAT_1000697c)"),
    ("substatus_side_effect", "hp1020_engine_status_io_candidate(DAT_10006968)"),
    ("video_reset_latch", "hp1020_video_reset_dispatch_candidate()"),
]


@dataclass(frozen=True)
class Inputs:
    primary: int
    status_20: int = 0
    status_2: int = 0
    substatus_16: int = 0
    substatus_13: int = 0
    previous_event: int = 0
    force_emit: bool = False


def load_literals(path: Path) -> dict[str, int]:
    model = json.loads(path.read_text())
    return {name: int(value, 16) for name, value in model["literal_values"].items()}


def fmt32(value: int) -> str:
    return f"0x{value:08x}"


def fmt16(value: int) -> str:
    return f"0x{value & 0xffff:04x}"


def select_engine_event(inputs: Inputs, c: dict[str, int]) -> dict[str, Any]:
    trace: list[str] = []
    side_effect_commands: list[int] = []
    extra_emitted_events: list[int] = []
    selected: int | None = None
    ready_branch = False
    reads = ["0x1"]

    primary = inputs.primary & 0xffff
    if primary == c["status_all_ones"]:
        return {
            "status": "no_update",
            "reason": "primary command 1 returned 0xffff",
            "selected_event": None,
            "stored_event": None,
            "emits_queue_0x17": False,
            "extra_emitted_events": [],
            "side_effect_commands": [],
            "reads": reads,
            "trace": ["primary_0xffff_short_circuit"],
        }

    selected = c["default_primary_event"]
    trace.append("primary_valid_default_0x04800100")
    if (primary & c["primary_0x4040_mask"]) != c["primary_0x4040_mask"]:
        reads.append("0x20")
        selected = c["event_f6000300"]
        trace.append("primary_missing_0x4040_read_0x20")
        if (inputs.status_20 & c["status_0x20_0x800_mask"]) == 0:
            selected = c["event_f6000400"]
            trace.append("status_0x20_no_0x800")
            if (inputs.status_20 & 0x400) == 0:
                reads.append("0x2")
                status_2 = inputs.status_2
                trace.append("status_0x20_no_0x400_read_0x2")
                if (status_2 & 0x100) == 0:
                    if (status_2 & 0xC0) == 0:
                        selected = c["event_e6100800"]
                        trace.append("status_2_no_0x100_no_0xc0_default_e6100800")
                        if (status_2 & c["status_2_0x4000_mask"]) == 0:
                            selected = c["event_status_1607"]
                            trace.append("status_2_no_0x4000")
                            if (status_2 & 0x424) == 0:
                                selected = c["event_preflight_or_status_1100"]
                                trace.append("status_2_no_0x424")
                                if (status_2 & c["status_2_0x1000_mask"]) == 0:
                                    selected = c["event_e6100e00"]
                                    trace.append("status_2_no_0x1000")
                                    if (status_2 & c["engine_start_status_bit"]) == 0:
                                        if (primary & 0x40) == 0 or (status_2 & 0x200) != 0:
                                            ready_branch = True
                                            selected = c["event_ready_ok"]
                                            trace.append("ready_ok_from_status_2")
                                        else:
                                            selected = c["fallback_error_event"]
                                            trace.append("fallback_error_primary_0x40_without_status_2_0x200")
                    else:
                        reads.append("0x16")
                        sub16 = inputs.substatus_16
                        selected = c["event_e6100800"]
                        trace.append("status_2_has_0xc0_read_0x16")
                        if sub16 == 0x40:
                            ready_branch = True
                            selected = c["event_ready_ok"]
                            trace.append("substatus_0x16_exact_0x40_ready")
                        else:
                            selected = c["event_e6000d03"]
                            if (sub16 & 0x10) == 0:
                                selected = c["event_e6000d06"]
                                if (sub16 & 0x08) == 0:
                                    selected = c["fallback_error_event"]
                                    if (sub16 & 0x04) != 0:
                                        selected = c["event_e6000d04"]
                            trace.append(f"substatus_0x16_bits_{fmt16(sub16)}")
                        if (sub16 & 0xFE) == 0:
                            side_effect_commands.append(c["command_0x501a"])
                            trace.append("send_0x501a_substatus_low_bits_clear")
                        elif (sub16 & 0x40) != 0 and (status_2 & c["status_2_0x4000_mask"]) != 0:
                            side_effect_commands.append(c["command_0x501a"])
                            selected = c["event_e6100800"]
                            trace.append("send_0x501a_and_force_e6100800")
                else:
                    reads.extend(["0x13", "0x16"])
                    subcase = (inputs.substatus_13 >> 1) & 0x3F
                    if subcase in {0x10, 0x14, 0x18}:
                        selected = c["event_e6100b0b"]
                        trace.append(f"status_0x13_special_subcase_{subcase:#x}")
                    else:
                        selected = c["event_e6100b0a"]
                        trace.append(f"status_0x13_default_subcase_{subcase:#x}")

    assert selected is not None
    selected_before_rewrite = selected
    if (selected & 0xFFFF) == c["low16_0x0a01"]:
        selected = c["event_0x14000a04"]
        trace.append("rewrite_low16_0x0a01_to_0x14000a04")

    if (inputs.previous_event & 0xFFFF) == 0x0100 and (selected & 0xFFFF) == c["low16_0x0a04"]:
        extra_emitted_events.append(c["event_ready_ok"])
        trace.append("previous_0x0100_to_0x0a04_extra_ready_emit")

    leave_mask = c["event_e6100800"]
    if (inputs.previous_event & leave_mask) == leave_mask and (selected & leave_mask) != leave_mask:
        side_effect_commands.append(c["command_0x5043"])
        trace.append("leave_e6100800_family_send_0x5043")

    emits = inputs.force_emit or selected != inputs.previous_event or bool(extra_emitted_events)
    return {
        "status": "selected",
        "reason": "engine status branch selected an event",
        "selected_event": fmt32(selected_before_rewrite),
        "stored_event": fmt32(selected),
        "ready_branch": ready_branch,
        "emits_queue_0x17": emits,
        "extra_emitted_events": [fmt32(value) for value in extra_emitted_events],
        "side_effect_commands": [fmt32(value) for value in side_effect_commands],
        "reads": reads,
        "trace": trace,
    }


def scenario_inputs(c: dict[str, int]) -> list[dict[str, Any]]:
    return [
        {
            "name": "primary_all_ones_no_update",
            "inputs": Inputs(primary=0xFFFF),
            "expected_stored": None,
            "expected_side_effects": [],
        },
        {
            "name": "primary_0x4040_default",
            "inputs": Inputs(primary=0x4040),
            "expected_stored": c["default_primary_event"],
            "expected_side_effects": [],
        },
        {
            "name": "status_0x20_0x800",
            "inputs": Inputs(primary=0, status_20=0x800),
            "expected_stored": c["event_f6000300"],
            "expected_side_effects": [],
        },
        {
            "name": "status_0x20_0x400",
            "inputs": Inputs(primary=0, status_20=0x400),
            "expected_stored": c["event_f6000400"],
            "expected_side_effects": [],
        },
        {
            "name": "status_2_0x4000",
            "inputs": Inputs(primary=0, status_2=0x4000),
            "expected_stored": c["event_e6100800"],
            "expected_side_effects": [],
        },
        {
            "name": "status_2_0x424",
            "inputs": Inputs(primary=0, status_2=0x004),
            "expected_stored": c["event_status_1607"],
            "expected_side_effects": [],
        },
        {
            "name": "status_2_0x1000",
            "inputs": Inputs(primary=0, status_2=0x1000),
            "expected_stored": c["event_preflight_or_status_1100"],
            "expected_side_effects": [],
        },
        {
            "name": "status_2_0x2000",
            "inputs": Inputs(primary=0, status_2=0x2000),
            "expected_stored": c["event_e6100e00"],
            "expected_side_effects": [],
        },
        {
            "name": "ready_rewrite",
            "inputs": Inputs(primary=0),
            "expected_stored": c["event_0x14000a04"],
            "expected_side_effects": [],
        },
        {
            "name": "primary_0x40_fallback_error",
            "inputs": Inputs(primary=0x40),
            "expected_stored": c["fallback_error_event"],
            "expected_side_effects": [],
        },
        {
            "name": "primary_0x40_status_2_0x200_ready",
            "inputs": Inputs(primary=0x40, status_2=0x200),
            "expected_stored": c["event_0x14000a04"],
            "expected_side_effects": [],
        },
        {
            "name": "substatus_0x16_ready_0x40_with_status_2_0x40",
            "inputs": Inputs(primary=0, status_2=0x40, substatus_16=0x40),
            "expected_stored": c["event_0x14000a04"],
            "expected_side_effects": [],
        },
        {
            "name": "substatus_0x16_ready_0x40_with_status_2_0x4040",
            "inputs": Inputs(primary=0, status_2=0x4040, substatus_16=0x40),
            "expected_stored": c["event_e6100800"],
            "expected_side_effects": [c["command_0x501a"]],
        },
        {
            "name": "substatus_0x16_low_clear_sends_0x501a",
            "inputs": Inputs(primary=0, status_2=0x40, substatus_16=0),
            "expected_stored": c["fallback_error_event"],
            "expected_side_effects": [c["command_0x501a"]],
        },
        {
            "name": "substatus_0x16_bit_0x10",
            "inputs": Inputs(primary=0, status_2=0x40, substatus_16=0x10),
            "expected_stored": c["event_e6000d03"],
            "expected_side_effects": [],
        },
        {
            "name": "substatus_0x16_bit_0x08",
            "inputs": Inputs(primary=0, status_2=0x40, substatus_16=0x08),
            "expected_stored": c["event_e6000d06"],
            "expected_side_effects": [],
        },
        {
            "name": "substatus_0x16_bit_0x04",
            "inputs": Inputs(primary=0, status_2=0x40, substatus_16=0x04),
            "expected_stored": c["event_e6000d04"],
            "expected_side_effects": [],
        },
        {
            "name": "status_0x13_default",
            "inputs": Inputs(primary=0, status_2=0x100, substatus_13=0),
            "expected_stored": c["event_e6100b0a"],
            "expected_side_effects": [],
        },
        {
            "name": "status_0x13_case_0x10",
            "inputs": Inputs(primary=0, status_2=0x100, substatus_13=0x20),
            "expected_stored": c["event_e6100b0b"],
            "expected_side_effects": [],
        },
        {
            "name": "previous_0x0100_to_ready_extra_emit",
            "inputs": Inputs(primary=0, previous_event=0x0100),
            "expected_stored": c["event_0x14000a04"],
            "expected_extra_events": [c["event_ready_ok"]],
            "expected_side_effects": [],
        },
        {
            "name": "leave_e6100800_sends_0x5043",
            "inputs": Inputs(primary=0x4040, previous_event=c["event_e6100800"]),
            "expected_stored": c["default_primary_event"],
            "expected_side_effects": [c["command_0x5043"]],
        },
    ]


def run_scenarios(c: dict[str, int]) -> list[dict[str, Any]]:
    rows = []
    for scenario in scenario_inputs(c):
        result = select_engine_event(scenario["inputs"], c)
        expected_stored = scenario["expected_stored"]
        expected_stored_text = None if expected_stored is None else fmt32(expected_stored)
        expected_side_effects = [fmt32(value) for value in scenario.get("expected_side_effects", [])]
        expected_extra_events = [fmt32(value) for value in scenario.get("expected_extra_events", [])]
        ok = (
            result["stored_event"] == expected_stored_text
            and result["side_effect_commands"] == expected_side_effects
            and result["extra_emitted_events"] == expected_extra_events
        )
        rows.append(
            {
                "name": scenario["name"],
                "status": "pass" if ok else "fail",
                "inputs": {
                    "primary": fmt16(scenario["inputs"].primary),
                    "status_20": fmt16(scenario["inputs"].status_20),
                    "status_2": fmt16(scenario["inputs"].status_2),
                    "substatus_16": fmt16(scenario["inputs"].substatus_16),
                    "substatus_13": fmt16(scenario["inputs"].substatus_13),
                    "previous_event": fmt32(scenario["inputs"].previous_event),
                },
                "expected_stored": expected_stored_text,
                "result": result,
            }
        )
    return rows


def evidence_checks(source: str) -> list[dict[str, str]]:
    return [
        {
            "name": name,
            "status": "present" if needle in source else "missing",
            "needle": needle,
        }
        for name, needle in CHECKS
    ]


def build_report(engine_model_json: Path) -> dict[str, Any]:
    constants = load_literals(engine_model_json)
    scenarios = run_scenarios(constants)
    checks = evidence_checks(POLL_SOURCE.read_text(errors="replace"))
    fail_count = sum(item["status"] != "pass" for item in scenarios) + sum(
        item["status"] != "present" for item in checks
    )
    return {
        "summary": "Executable offline model of hp1020_engine_status_poll_candidate branch decisions.",
        "status": "pass" if fail_count == 0 else "fail",
        "source_function": "0x10015df8 hp1020_engine_status_poll_candidate",
        "constants_source": str(engine_model_json.relative_to(ROOT_DIR)),
        "scenario_count": len(scenarios),
        "scenario_failures": sum(item["status"] != "pass" for item in scenarios),
        "scenarios": scenarios,
        "checks": checks,
        "open_firmware_implication": [
            "Later raw status captures can be fed into this model to classify the exact stock branch without rereading Ghidra output.",
            "This model predicts stock event words and side-effect commands only; physical labels still require printer-side calibration.",
            "The safe offline conclusion is that a printing replacement needs this branch behavior before it can reliably decide when to start, wait, recover, or surface errors.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 Engine Status Decision Model",
        "",
        "This is a generated offline model. It does not contact the printer.",
        "",
        "## Result",
        "",
        f"- status: `{report['status']}`",
        f"- function: `{report['source_function']}`",
        f"- scenarios: `{report['scenario_count']}`",
        f"- scenario failures: `{report['scenario_failures']}`",
        "",
        "## Scenario Table",
        "",
        "| Scenario | Status | Primary | Status 0x20 | Status 2 | Substatus 0x16 | Substatus 0x13 | Stored event | Side-effect commands | Extra events | Trace |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|---|---|",
    ]
    for item in report["scenarios"]:
        inputs = item["inputs"]
        result = item["result"]
        side_effects = ", ".join(f"`{value}`" for value in result["side_effect_commands"]) or "-"
        extra_events = ", ".join(f"`{value}`" for value in result["extra_emitted_events"]) or "-"
        trace = "<br>".join(f"`{value}`" for value in result["trace"])
        lines.append(
            f"| `{item['name']}` | `{item['status']}` | `{inputs['primary']}` | `{inputs['status_20']}` | "
            f"`{inputs['status_2']}` | `{inputs['substatus_16']}` | `{inputs['substatus_13']}` | "
            f"`{result['stored_event']}` | {side_effects} | {extra_events} | {trace} |"
        )

    lines.extend(["", "## Evidence Checks", "", "| Check | Status | Needle |", "|---|---|---|"])
    for check in report["checks"]:
        needle = check["needle"].replace("|", "\\|")
        lines.append(f"| `{check['name']}` | `{check['status']}` | `{needle}` |")

    lines.extend(["", "## Open Firmware Meaning", ""])
    for item in report["open_firmware_implication"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine-model-json", type=Path, default=ENGINE_MODEL_JSON)
    parser.add_argument("--json-output", type=Path, default=OUT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=OUT_MD)
    args = parser.parse_args()

    report = build_report(args.engine_model_json)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.markdown_output.write_text(render_markdown(report) + "\n")
    print(
        f"status={report['status']} scenarios={report['scenario_count']} "
        f"scenario_failures={report['scenario_failures']} checks={len(report['checks'])}"
    )
    print(args.markdown_output)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
