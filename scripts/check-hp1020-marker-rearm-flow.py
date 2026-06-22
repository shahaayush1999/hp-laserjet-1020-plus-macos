#!/usr/bin/env python3
"""Check that the USB marker draft can re-enter polling after one response."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Check:
    name: str
    severity: str
    detail: str


def source_without_comments(path: Path) -> list[str]:
    return [line.split("#", 1)[0].rstrip() for line in path.read_text().splitlines()]


def find_line(lines: list[str], needle: str) -> int | None:
    for index, line in enumerate(lines):
        if needle in line:
            return index
    return None


def find_line_after(lines: list[str], needle: str, start: int | None) -> int | None:
    if start is None:
        return None
    for index, line in enumerate(lines[start + 1 :], start=start + 1):
        if needle in line:
            return index
    return None


def label_line(lines: list[str], label: str) -> int | None:
    exact = f"{label}:"
    for index, line in enumerate(lines):
        if line.strip() == exact:
            return index
    return None


def check_rearm_flow(lines: list[str]) -> list[Check]:
    checks: list[Check] = []
    done_store = find_line(lines, "s32i a3, a4, 0x44")
    wait_label = label_line(lines, "hp1020_usb_marker_wait_gate_clear")
    poll_label = label_line(lines, "hp1020_usb_marker_poll_loop")
    idle_jump = find_line(lines, "jump_abs hp1020_probe_idle_loop")
    rearm_store = find_line_after(lines, "s32i a3, a4, 0x48", wait_label)
    gate_a_read = find_line_after(lines, "hp1020_mmio_b3000408", wait_label)
    gate_a_mask = find_line_after(lines, "hp1020_gate_mask_00006000", wait_label)
    gate_b_read = find_line_after(lines, "hp1020_mmio_b3000400", wait_label)
    gate_b_mask = find_line_after(lines, "hp1020_gate_mask_00000003", wait_label)
    rearm_jump = find_line_after(lines, "j hp1020_usb_marker_poll_loop", wait_label)

    checks.append(
        Check(
            "response_enters_rearm_wait",
            "watch" if done_store is not None and wait_label is not None and done_store < wait_label else "fail",
            "after submitting one descriptor response, marker should enter a gate-clear wait path",
        )
    )
    checks.append(
        Check(
            "no_idle_after_successful_response",
            "watch" if idle_jump is None or (wait_label is not None and idle_jump < wait_label) else "fail",
            "successful marker response must not immediately park in the idle loop",
        )
    )
    checks.append(
        Check(
            "rearm_state_recorded",
            "watch" if rearm_store is not None and wait_label is not None and rearm_store > wait_label else "fail",
            "rearm wait should leave a RAM breadcrumb for postmortem diagnosis",
        )
    )
    checks.append(
        Check(
            "waits_for_both_setup_gates",
            "watch"
            if (
                wait_label is not None
                and gate_a_read is not None
                and gate_a_mask is not None
                and gate_b_read is not None
                and gate_b_mask is not None
                and wait_label < gate_a_read < gate_b_read
            )
            else "fail",
            "rearm wait must read and mask both USB setup/status gates before polling again",
        )
    )
    checks.append(
        Check(
            "rearm_returns_to_poll_loop",
            "watch" if wait_label is not None and poll_label is not None and rearm_jump is not None and rearm_jump > wait_label else "fail",
            "after both gates clear, marker should return to the setup polling loop",
        )
    )
    return checks


def render_markdown(checks: list[Check]) -> str:
    fail_count = sum(check.severity == "fail" for check in checks)
    lines = [
        "# HP 1020 Marker Rearm Flow Check",
        "",
        f"- fail hits: `{fail_count}`",
        "",
        "| Severity | Check | Detail |",
        "|---|---|---|",
    ]
    for check in checks:
        lines.append(f"| `{check.severity}` | `{check.name}` | {check.detail} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()

    checks = check_rearm_flow(source_without_comments(args.source))
    report = render_markdown(checks)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report)
    else:
        print(report, end="")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps([check.__dict__ for check in checks], indent=2, sort_keys=True) + "\n")
    return 1 if any(check.severity == "fail" for check in checks) else 0


if __name__ == "__main__":
    raise SystemExit(main())
