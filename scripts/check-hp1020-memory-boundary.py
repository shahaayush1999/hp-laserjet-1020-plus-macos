#!/usr/bin/env python3
"""Classify non-MMIO memory reads/writes in HP 1020 open-firmware disassembly."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


INSN_RE = re.compile(r"^\s*(?P<pc>[0-9a-f]{8}):\s+(?P<bytes>[0-9a-f ]+)\s+(?P<insn>.+?)\s*$")
L32R_RE = re.compile(r"^l32r\s+(?P<dst>a\d+),\s*[0-9a-f]+(?:\s+<(?P<label>[^>]+)>)?$")
LOAD_RE = re.compile(r"^(?P<op>l(?:8ui|32i(?:\.n)?))\s+(?P<dst>a\d+),\s*(?P<base>a\d+),\s*(?P<offset>-?(?:0x)?[0-9a-f]+)")
STORE_RE = re.compile(r"^(?P<op>s(?:8i|32i(?:\.n)?))\s+(?P<src>a\d+),\s*(?P<base>a\d+),\s*(?P<offset>-?(?:0x)?[0-9a-f]+)")
ADDI_RE = re.compile(r"^addi(?:\.n)?\s+(?P<dst>a\d+),\s*(?P<src>a\d+),\s*-?(?:0x)?[0-9a-f]+\b")
DEST_RE = re.compile(r"^(?:movi(?:\.n)?|mov(?:\.n)?|add(?:\.n)?|addi(?:\.n)?|or|and|xor|slli|srli|extui)\s+(?P<dst>a\d+)\b")
CALL_RE = re.compile(r"^call\d?\b")


@dataclass(frozen=True)
class Event:
    severity: str
    kind: str
    pc: str
    access: str
    base: str
    offset: str
    instruction: str
    description: str


def parse_offset(value: str) -> int:
    value = value.lower()
    sign = -1 if value.startswith("-") else 1
    value = value[1:] if value.startswith("-") else value
    return sign * (int(value, 16) if value.startswith("0x") else int(value, 0))


def fmt_offset(value: int) -> str:
    if value < 0:
        return f"-0x{abs(value):x}"
    return f"0x{value:x}"


def iter_files(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        if path.is_dir():
            yield from (p for p in sorted(path.rglob("*")) if p.is_file())
        else:
            yield path


def classify_label(label: str | None) -> tuple[str, str, str] | None:
    if not label:
        return None
    low = label.lower()
    if "mmio_b300" in low:
        return None
    if "usb_marker_state_ptr" in low or "usb_snapshot_state_ptr" in low:
        return ("local_probe_state", "watch", "local probe state buffer")
    if "response_state_base_100212d4" in low:
        return ("stock_response_state", "watch", "stock USB response state object at 0x100212d4")
    if "setup_packet_base_90021348" in low:
        return ("setup_packet_buffer", "watch", "candidate USB setup packet buffer at 0x90021348")
    if "marker_descriptor_hw_ptr_90003200" in low:
        return ("marker_descriptor_source", "watch", "open marker descriptor hardware alias at 0x90003200")
    if "staging_buffer_ptr_90022bd0" in low:
        return ("usb_staging_buffer", "watch", "stock USB control-IN staging buffer at 0x90022bd0")
    if "descriptor_base_ptr_900226f0" in low:
        return ("usb_transfer_descriptor_ring", "watch", "stock USB control-IN transfer descriptor ring at 0x900226f0")
    return None


def scan_file(path: Path) -> list[Event]:
    events: list[Event] = []
    state: dict[str, tuple[str, str, str]] = {}

    for line in path.read_text(errors="replace").splitlines():
        match = INSN_RE.match(line)
        if not match:
            continue
        pc = f"0x{match.group('pc')}"
        insn = match.group("insn").strip()

        if m := L32R_RE.match(insn):
            dst = m.group("dst")
            classified = classify_label(m.group("label"))
            if classified:
                state[dst] = classified
            else:
                state.pop(dst, None)
            continue

        access_match = LOAD_RE.match(insn) or STORE_RE.match(insn)
        if access_match:
            base_reg = access_match.group("base")
            classified = state.get(base_reg)
            if classified:
                kind, severity, description = classified
                access = "write" if access_match.re is STORE_RE else "read"
                offset = fmt_offset(parse_offset(access_match.group("offset")))
                events.append(Event(severity, kind, pc, access, base_reg, offset, insn, description))
            if access_match.re is LOAD_RE:
                state.pop(access_match.group("dst"), None)
            continue

        if CALL_RE.match(insn):
            state.clear()
        elif m := ADDI_RE.match(insn):
            dst = m.group("dst")
            src = m.group("src")
            if dst != src:
                state.pop(dst, None)
        elif m := DEST_RE.match(insn):
            state.pop(m.group("dst"), None)

    return events


def render_markdown(events: list[Event]) -> str:
    fail_count = sum(1 for event in events if event.severity == "fail")
    counts: dict[tuple[str, str], int] = {}
    for event in events:
        key = (event.kind, event.access)
        counts[key] = counts.get(key, 0) + 1

    lines = [
        "# HP 1020 Memory Boundary Scan",
        "",
        f"- recovered classified memory accesses: `{len(events)}`",
        f"- fail hits: `{fail_count}`",
        "",
        "## Counts",
        "",
    ]
    if counts:
        for (kind, access), count in sorted(counts.items()):
            lines.append(f"- `{kind}` `{access}`: `{count}`")
    else:
        lines.append("- none")

    lines.extend(["", "## Events", "", "| Severity | Kind | Access | PC | Offset | Instruction | Description |", "|---|---|---|---:|---:|---|---|"])
    for event in events:
        safe_insn = event.instruction.replace("|", "\\|")
        lines.append(
            f"| `{event.severity}` | `{event.kind}` | `{event.access}` | `{event.pc}` | "
            f"`{event.offset}` | `{safe_insn}` | {event.description} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="Xtensa objdump text files")
    parser.add_argument("-o", "--output", type=Path, help="write markdown report")
    parser.add_argument("--json", type=Path, help="write JSON event list")
    parser.add_argument("--allow-fail", action="store_true", help="exit 0 even if fail hits are found")
    args = parser.parse_args()

    events: list[Event] = []
    for path in iter_files(args.paths):
        events.extend(scan_file(path))
    events.sort(key=lambda event: int(event.pc, 16))

    report = render_markdown(events)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report)
    else:
        print(report, end="")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps([event.__dict__ for event in events], indent=2, sort_keys=True) + "\n")

    has_fail = any(event.severity == "fail" for event in events)
    return 1 if has_fail and not args.allow_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
