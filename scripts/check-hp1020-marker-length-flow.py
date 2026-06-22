#!/usr/bin/env python3
"""Check that the USB marker draft preserves clipped wLength into endpoint-0."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path


WRITE_A6_RE = re.compile(
    r"^\s*(?:abs|add|addi|and|extui|l16ui|l32i|l32r|l8ui|mov|movi|or|slli|srli|sub|xor)\s+a6\b"
)
WRITE_A7_RE = re.compile(
    r"^\s*(?:abs|add|addi|and|extui|l16ui|l32i|l32r|l8ui|mov|movi|or|slli|srli|sub|xor)\s+a7\b"
)


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


def label_line(lines: list[str], label: str) -> int | None:
    exact = f"{label}:"
    for index, line in enumerate(lines):
        if line.strip() == exact:
            return index
    return None


def check_length_flow(lines: list[str]) -> list[Check]:
    checks: list[Check] = []
    clipped_store = find_line(lines, "s32i a6, a4, 0x20")
    response_store = find_line(lines, "s32i a6, a4, 0x3c")
    descriptor_or = find_line(lines, "or a7, a7, a6")
    descriptor_store = find_line(lines, "s32i a7, a4, 0")
    branch_b = find_line(lines, "bnez a7, hp1020_usb_marker_sequence_b")
    kick_label = label_line(lines, "hp1020_usb_marker_kick_control_in")
    clip_label = label_line(lines, "hp1020_usb_marker_clip_and_dispatch")
    clip_branch = find_line(lines, "bltu a6, a7, 1f")

    checks.append(
        Check(
            "clipped_length_saved",
            "watch" if clipped_store is not None else "fail",
            "clipped host wLength must be saved in local probe state at +0x20",
        )
    )
    checks.append(
        Check(
            "response_length_uses_a6",
            "watch" if response_store is not None else "fail",
            "endpoint-0 response length must be programmed from the clipped-length register",
        )
    )
    checks.append(
        Check(
            "descriptor_word_uses_clipped_length",
            "watch" if descriptor_or is not None and descriptor_store is not None and descriptor_or < descriptor_store else "fail",
            "transfer descriptor word must OR the final flag with the clipped-length register before descriptor submission",
        )
    )

    if clipped_store is None or branch_b is None:
        checks.append(Check("a6_not_clobbered_before_sequence", "fail", "could not locate flow range"))
    else:
        clobbers = [
            (index + 1, line.strip())
            for index, line in enumerate(lines[clipped_store + 1 : branch_b + 1], start=clipped_store + 1)
            if WRITE_A6_RE.match(line)
        ]
        checks.append(
            Check(
                "a6_not_clobbered_before_sequence",
                "watch" if not clobbers else "fail",
                "no writes to a6 are allowed between clipped-length calculation and sequence dispatch"
                if not clobbers
                else "; ".join(f"line {line_no}: {text}" for line_no, text in clobbers),
            )
        )

    if clip_label is None or clip_branch is None:
        checks.append(Check("selected_descriptor_length_preserved", "fail", "could not locate descriptor-length clip range"))
    else:
        clobbers = [
            (index + 1, line.strip())
            for index, line in enumerate(lines[clip_label + 1 : clip_branch], start=clip_label + 1)
            if WRITE_A7_RE.match(line)
        ]
        checks.append(
            Check(
                "selected_descriptor_length_preserved",
                "watch" if not clobbers else "fail",
                "selected descriptor length in a7 must reach the wLength clip unchanged"
                if not clobbers
                else "; ".join(f"line {line_no}: {text}" for line_no, text in clobbers),
            )
        )

    if response_store is None or kick_label is None:
        checks.append(Check("response_store_in_kick_path", "fail", "could not locate kick path"))
    else:
        checks.append(
            Check(
                "response_store_in_kick_path",
                "watch" if response_store > kick_label else "fail",
                "the response length write must live in hp1020_usb_marker_kick_control_in",
            )
        )

    return checks


def render_markdown(checks: list[Check]) -> str:
    fail_count = sum(check.severity == "fail" for check in checks)
    lines = [
        "# HP 1020 Marker Length Flow Check",
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

    checks = check_length_flow(source_without_comments(args.source))
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
