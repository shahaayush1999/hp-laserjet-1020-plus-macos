#!/usr/bin/env python3
"""Model HP 1020 video IRQ/status branch decisions.

This is offline analysis only. It converts the visible branch order in
`0x100144d0 hp1020_video_irq_or_band_done_candidate` into an executable
decision table for video block status bits.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
SOURCE = ROOT_DIR / "analysis/zjs-parser-boundary/decompiled/100144d0_hp1020_video_irq_or_band_done_candidate.c"
OUT_JSON = ROOT_DIR / "analysis/hardware-boundary/video-irq-decisions.json"
OUT_MD = ROOT_DIR / "analysis/hardware-boundary/video-irq-decisions.md"

CHECKS = [
    ("bit_0x20_priority", "(*DAT_100067c0 & 0x20) != 0"),
    ("bit_0x20_ack_a", "*puVar2 = 0xffffffdf"),
    ("bit_0x20_ack_b", "*DAT_100067d8 = 0xffffffdf"),
    ("fc_negative_raw_band_path", "if (*(int *)(puVar1 + 0xfc) < 0)"),
    ("ring_done_index_advance", "*(uint *)(puVar1 + 0xd8) = *(int *)(puVar1 + 0xd8) + 1U & 3"),
    ("bit_0x02_reset_case_0", "uVar6 = 0"),
    ("bit_0x04_recovery_branch", "if ((*DAT_100067c0 & 4) != 0)"),
    ("bit_0x04_ack", "*DAT_100067c0 = 0xfffffffb"),
    ("bit_0x04_done_case_0", "FUN_10013d4c(0)"),
    ("bit_0x01_case_7", "FUN_10013d4c(7)"),
    ("bit_0x08_case_3", "uVar6 = 3"),
    ("bit_0x10_case_4", "uVar6 = 4"),
    ("bit_0x10_ack", "uVar4 = 0xffffffef"),
    ("dispatch_param", "FUN_10013d4c(uVar6)"),
    ("event_10_ack", "FUN_100171e0(10)"),
    ("event_0x0b_ack", "FUN_100171e0(0xb)"),
]


@dataclass(frozen=True)
class Inputs:
    block_a: int = 0
    block_b: int = 0
    state_70: bool = False
    state_6c: int = 0
    state_f0: bool = False
    fc_negative: bool = False
    dual_block_mode: bool = True
    in_b8: bool = False
    source_event: int = 0


def fmt_mask(value: int) -> str:
    return f"0x{value:02x}"


def decide(inputs: Inputs) -> dict[str, Any]:
    trace: list[str] = []
    actions: list[str] = []
    reset_dispatch: int | None = None
    ack_masks: list[str] = []

    if (inputs.block_a & 0x20) != 0 or (inputs.block_b & 0x20) != 0:
        trace.append("bit_0x20_band_done_priority")
        if (inputs.block_a & 0x20) != 0:
            ack_masks.append("block_a &= 0xffffffdf")
        if (inputs.block_b & 0x20) != 0:
            ack_masks.append("block_b &= 0xffffffdf")
        actions.extend(["increment video_state +0xf8", "set video_state +0xf0"])
        if inputs.fc_negative:
            trace.append("fc_negative_raw_band_refresh")
            actions.extend(["advance video_state +0xa0 list", "refresh raw bands"])
        else:
            trace.append("ring_record_complete_and_refill")
            actions.extend(
                [
                    "clear ring record at +0x20 + (+0xd8 * 0x0c)",
                    "advance +0xd8 modulo 4",
                    "refill channel-B descriptor",
                    "queue/list next band",
                ]
            )
        return result("band_done", reset_dispatch, ack_masks, actions, trace, inputs)

    if (inputs.block_a & 0x02) != 0:
        trace.append("block_a_bit_0x02_reset_case_0")
        ack_masks.extend(["block_a &= 0xfffffffd", "block_b &= 0xfffffffd"])
        reset_dispatch = 0
        return result("reset_dispatch", reset_dispatch, ack_masks, actions, trace, inputs)

    if (inputs.block_a & 0x04) != 0:
        trace.append("block_a_bit_0x04_recovery")
        ack_masks.extend(["block_a &= 0xfffffffb", "block_b &= 0xfffffffb"])
        if inputs.state_70:
            actions.append("clear video_state +0x70")
            if inputs.state_6c != 0:
                if not inputs.state_f0:
                    trace.append("rearm_video_blocks_without_reset_dispatch")
                    actions.extend(
                        [
                            "clear video_state +0xdc",
                            "toggle block control bit 0x100 after busy waits",
                            "refresh raw bands" if inputs.in_b8 else "queue/list next band",
                        ]
                    )
                else:
                    trace.append("state_f0_already_seen_dispatch_case_0")
                    reset_dispatch = 0
        else:
            trace.append("state_70_clear_no_followup")
        return result("recover_or_reset", reset_dispatch, ack_masks, actions, trace, inputs)

    if (inputs.block_a & 0x01) != 0 or (inputs.block_b & 0x01) != 0:
        trace.append("bit_0x01_latch_or_case_7")
        if (inputs.block_a & 0x01) != 0:
            ack_masks.append("block_a &= 0xfffffffe")
        if (inputs.block_b & 0x01) != 0:
            ack_masks.append("block_b &= 0xfffffffe")
        actions.append("set video_state +0x70")
        if inputs.state_6c == 0:
            reset_dispatch = 7
            actions.append("signal video event object")
        return result("latch_or_reset_case_7", reset_dispatch, ack_masks, actions, trace, inputs)

    if (inputs.block_a & 0x08) != 0 or (inputs.block_b & 0x08) != 0:
        trace.append("bit_0x08_reset_case_3")
        ack_masks.extend(["block_a &= 0xfffffff7", "block_b &= 0xfffffff7"])
        reset_dispatch = 3
        return result("reset_dispatch", reset_dispatch, ack_masks, actions, trace, inputs)

    bit_10_seen = (inputs.block_a & 0x10) != 0 or (inputs.dual_block_mode and (inputs.block_b & 0x10) != 0)
    if bit_10_seen:
        trace.append("bit_0x10_reset_case_4")
        ack_masks.extend(["block_a &= 0xffffffef", "block_b &= 0xffffffef"])
        reset_dispatch = 4
        return result("reset_dispatch", reset_dispatch, ack_masks, actions, trace, inputs)

    trace.append("no_modeled_status_bit")
    return result("no_action", reset_dispatch, ack_masks, actions, trace, inputs)


def result(
    category: str,
    reset_dispatch: int | None,
    ack_masks: list[str],
    actions: list[str],
    trace: list[str],
    inputs: Inputs,
) -> dict[str, Any]:
    event_ack = []
    if inputs.source_event == 10:
        event_ack.append("0x0a")
    if inputs.source_event == 0x0B:
        event_ack.append("0x0b")
    return {
        "category": category,
        "reset_dispatch_param": reset_dispatch,
        "ack_masks": ack_masks,
        "actions": actions,
        "trace": trace,
        "event_ack": event_ack,
    }


def scenario_inputs() -> list[dict[str, Any]]:
    return [
        {
            "name": "band_done_ring_refill",
            "inputs": Inputs(block_a=0x20, fc_negative=False),
            "expected": {"category": "band_done", "reset": None, "trace": "ring_record_complete_and_refill"},
        },
        {
            "name": "band_done_raw_band_refresh",
            "inputs": Inputs(block_b=0x20, fc_negative=True),
            "expected": {"category": "band_done", "reset": None, "trace": "fc_negative_raw_band_refresh"},
        },
        {
            "name": "bit_0x02_reset_case_0",
            "inputs": Inputs(block_a=0x02),
            "expected": {"category": "reset_dispatch", "reset": 0, "trace": "block_a_bit_0x02_reset_case_0"},
        },
        {
            "name": "bit_0x04_rearm_without_reset",
            "inputs": Inputs(block_a=0x04, state_70=True, state_6c=2, state_f0=False, in_b8=False),
            "expected": {"category": "recover_or_reset", "reset": None, "trace": "rearm_video_blocks_without_reset_dispatch"},
        },
        {
            "name": "bit_0x04_dispatch_case_0_after_done",
            "inputs": Inputs(block_a=0x04, state_70=True, state_6c=2, state_f0=True),
            "expected": {"category": "recover_or_reset", "reset": 0, "trace": "state_f0_already_seen_dispatch_case_0"},
        },
        {
            "name": "bit_0x01_dispatch_case_7_when_idle",
            "inputs": Inputs(block_a=0x01, state_6c=0),
            "expected": {"category": "latch_or_reset_case_7", "reset": 7, "trace": "bit_0x01_latch_or_case_7"},
        },
        {
            "name": "bit_0x01_latch_when_running",
            "inputs": Inputs(block_b=0x01, state_6c=2),
            "expected": {"category": "latch_or_reset_case_7", "reset": None, "trace": "bit_0x01_latch_or_case_7"},
        },
        {
            "name": "bit_0x08_reset_case_3",
            "inputs": Inputs(block_a=0x08),
            "expected": {"category": "reset_dispatch", "reset": 3, "trace": "bit_0x08_reset_case_3"},
        },
        {
            "name": "bit_0x10_reset_case_4",
            "inputs": Inputs(block_b=0x10, dual_block_mode=True),
            "expected": {"category": "reset_dispatch", "reset": 4, "trace": "bit_0x10_reset_case_4"},
        },
        {
            "name": "bit_0x10_ignored_without_dual_block",
            "inputs": Inputs(block_b=0x10, dual_block_mode=False),
            "expected": {"category": "no_action", "reset": None, "trace": "no_modeled_status_bit"},
        },
        {
            "name": "priority_0x20_over_0x02",
            "inputs": Inputs(block_a=0x22, fc_negative=False),
            "expected": {"category": "band_done", "reset": None, "trace": "bit_0x20_band_done_priority"},
        },
    ]


def run_scenarios() -> list[dict[str, Any]]:
    rows = []
    for scenario in scenario_inputs():
        decision = decide(scenario["inputs"])
        expected = scenario["expected"]
        ok = (
            decision["category"] == expected["category"]
            and decision["reset_dispatch_param"] == expected["reset"]
            and expected["trace"] in decision["trace"]
        )
        rows.append(
            {
                "name": scenario["name"],
                "status": "pass" if ok else "fail",
                "inputs": {
                    "block_a": fmt_mask(scenario["inputs"].block_a),
                    "block_b": fmt_mask(scenario["inputs"].block_b),
                    "state_70": scenario["inputs"].state_70,
                    "state_6c": scenario["inputs"].state_6c,
                    "state_f0": scenario["inputs"].state_f0,
                    "fc_negative": scenario["inputs"].fc_negative,
                    "dual_block_mode": scenario["inputs"].dual_block_mode,
                    "in_b8": scenario["inputs"].in_b8,
                },
                "decision": decision,
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


def build_report() -> dict[str, Any]:
    source = SOURCE.read_text(errors="replace")
    scenarios = run_scenarios()
    checks = evidence_checks(source)
    scenario_failures = sum(item["status"] != "pass" for item in scenarios)
    check_failures = sum(item["status"] != "present" for item in checks)
    return {
        "summary": "Executable branch model for video block IRQ/status decisions.",
        "status": "pass" if scenario_failures == 0 and check_failures == 0 else "fail",
        "source_function": "0x100144d0 hp1020_video_irq_or_band_done_candidate",
        "scenario_count": len(scenarios),
        "scenario_failures": scenario_failures,
        "scenarios": scenarios,
        "checks": checks,
        "branch_priority": [
            "0x20 band done/refill",
            "0x02 reset dispatch case 0",
            "0x04 recovery or reset dispatch case 0",
            "0x01 latch or reset dispatch case 7",
            "0x08 reset dispatch case 3",
            "0x10 reset dispatch case 4",
        ],
        "open_firmware_implication": [
            "The video IRQ path is not a single done bit; multiple block-status bits have different reset/recovery meanings.",
            "Bit 0x20 is the continue/refill path and has priority over reset bits.",
            "Reset dispatch cases 3, 4, and 7 become video reset event words through the video-to-engine feedback model.",
            "Hardware calibration is still needed to attach physical labels to these video block status bits.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 Video IRQ Decision Model",
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
        "## Branch Priority",
        "",
    ]
    for index, item in enumerate(report["branch_priority"], 1):
        lines.append(f"{index}. {item}")

    lines.extend(
        [
            "",
            "## Scenario Table",
            "",
            "| Scenario | Status | Block A | Block B | State +0x70 | State +0x6c | State +0xf0 | +0xfc negative | Category | Reset dispatch | Actions | Trace |",
            "|---|---|---:|---:|---|---:|---|---|---|---:|---|---|",
        ]
    )
    for item in report["scenarios"]:
        inputs = item["inputs"]
        decision = item["decision"]
        actions = "<br>".join(f"`{action}`" for action in decision["actions"]) or "-"
        trace = "<br>".join(f"`{step}`" for step in decision["trace"])
        reset = "-" if decision["reset_dispatch_param"] is None else str(decision["reset_dispatch_param"])
        lines.append(
            f"| `{item['name']}` | `{item['status']}` | `{inputs['block_a']}` | `{inputs['block_b']}` | "
            f"`{inputs['state_70']}` | `{inputs['state_6c']}` | `{inputs['state_f0']}` | `{inputs['fc_negative']}` | "
            f"`{decision['category']}` | `{reset}` | {actions} | {trace} |"
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
    parser.add_argument("--json-output", type=Path, default=OUT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=OUT_MD)
    args = parser.parse_args()

    report = build_report()
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
