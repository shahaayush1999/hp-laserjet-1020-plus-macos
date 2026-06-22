#!/usr/bin/env python3
"""Classify USB MMIO reads/writes in Xtensa objdump output for HP 1020 probes."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


REPO = Path(__file__).resolve().parents[1]
DEFAULT_MMIO_MAP = REPO / "analysis/usb-path/usb-mmio-map.json"

INSN_RE = re.compile(r"^\s*(?P<pc>[0-9a-f]{8}):\s+(?P<bytes>[0-9a-f ]+)\s+(?P<insn>.+?)\s*$")
L32R_RE = re.compile(r"^l32r\s+(?P<dst>a\d+),\s*[0-9a-f]+(?:\s+<(?P<label>[^>]+)>)?$")
L32I_RE = re.compile(r"^l32i(?:\.n)?\s+(?P<dst>a\d+),\s*(?P<base>a\d+),\s*(?P<offset>-?(?:0x)?[0-9a-f]+)")
S32I_RE = re.compile(r"^s32i(?:\.n)?\s+(?P<src>a\d+),\s*(?P<base>a\d+),\s*(?P<offset>-?(?:0x)?[0-9a-f]+)")
DEST_RE = re.compile(r"^(?:movi(?:\.n)?|mov(?:\.n)?|add(?:\.n)?|addi(?:\.n)?|or|and|xor|slli|srli|extui)\s+(?P<dst>a\d+)\b")
CALL_RE = re.compile(r"^call\d?\b")
USB_REG_RE = re.compile(r"b300[0-9a-f]{4}", re.IGNORECASE)


@dataclass(frozen=True)
class Access:
    severity: str
    access: str
    register: str
    pc: str
    path: str
    instruction: str
    description: str


def iter_files(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        if path.is_dir():
            yield from (p for p in sorted(path.rglob("*")) if p.is_file())
        else:
            yield path


def load_allowed_usb_registers(path: Path) -> set[str]:
    data = json.loads(path.read_text())
    registers = data.get("registers", {})
    if not registers:
        raise SystemExit(f"no registers found in {path}")
    return {reg.lower() for reg in registers}


def register_from_label(label: str | None) -> str | None:
    if not label:
        return None
    match = USB_REG_RE.search(label)
    if not match:
        return None
    return f"0x{match.group(0).lower()}"


def classify_file(path: Path, allowed_usb: set[str], allow_writes: bool) -> list[Access]:
    accesses: list[Access] = []
    reg_values: dict[str, str] = {}

    for line in path.read_text(errors="replace").splitlines():
        match = INSN_RE.match(line)
        if not match:
            continue
        pc = f"0x{match.group('pc')}"
        insn = match.group("insn").strip()

        if m := L32R_RE.match(insn):
            dst = m.group("dst")
            register = register_from_label(m.group("label"))
            if register:
                reg_values[dst] = register
            else:
                reg_values.pop(dst, None)
            continue

        for access_kind, access_re in (("read", L32I_RE), ("write", S32I_RE)):
            m = access_re.match(insn)
            if not m:
                continue
            base = m.group("base")
            register = reg_values.get(base)
            if not register:
                continue
            if register not in allowed_usb:
                severity = "fail"
                description = "USB register is not in the endpoint-0 static map"
            elif access_kind == "write" and not allow_writes:
                severity = "fail"
                description = "USB MMIO write is blocked for this probe/access profile"
            else:
                severity = "watch"
                description = f"mapped USB MMIO {access_kind}"
            accesses.append(Access(severity, access_kind, register, pc, str(path), insn, description))
            if access_kind == "read":
                reg_values.pop(m.group("dst"), None)
            break
        else:
            if CALL_RE.match(insn):
                reg_values.clear()
            elif m := DEST_RE.match(insn):
                reg_values.pop(m.group("dst"), None)

    return accesses


def render_markdown(accesses: list[Access], allowed_usb: set[str]) -> str:
    read_count = sum(1 for access in accesses if access.access == "read")
    write_count = sum(1 for access in accesses if access.access == "write")
    fail_count = sum(1 for access in accesses if access.severity == "fail")
    lines = [
        "# HP 1020 USB MMIO Access Scan",
        "",
        f"- allowed mapped USB registers: `{len(allowed_usb)}`",
        f"- read accesses: `{read_count}`",
        f"- write accesses: `{write_count}`",
        f"- fail hits: `{fail_count}`",
        "",
    ]
    if not accesses:
        lines.append("No USB MMIO reads or writes were recovered from the disassembly.")
        return "\n".join(lines) + "\n"

    lines.extend(["| Severity | Access | Register | PC | Instruction | Description |", "|---|---|---:|---:|---|---|"])
    for access in accesses:
        safe_insn = access.instruction.replace("|", "\\|")
        lines.append(
            f"| `{access.severity}` | `{access.access}` | `{access.register}` | `{access.pc}` | "
            f"`{safe_insn}` | {access.description} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="Xtensa objdump text files")
    parser.add_argument("--mmio-map", type=Path, default=DEFAULT_MMIO_MAP, help="USB MMIO map JSON")
    parser.add_argument("--allow-usb-writes", action="store_true", help="do not fail mapped USB writes")
    parser.add_argument("-o", "--output", type=Path, help="write markdown report")
    parser.add_argument("--json", type=Path, help="write JSON access list")
    args = parser.parse_args()

    allowed_usb = load_allowed_usb_registers(args.mmio_map)
    accesses: list[Access] = []
    for file_path in iter_files(args.paths):
        accesses.extend(classify_file(file_path, allowed_usb, args.allow_usb_writes))

    accesses.sort(key=lambda access: (access.path, int(access.pc, 16), access.access))
    report = render_markdown(accesses, allowed_usb)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report)
    else:
        print(report, end="")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps([access.__dict__ for access in accesses], indent=2, sort_keys=True) + "\n")

    has_fail = any(access.severity == "fail" for access in accesses)
    return 1 if has_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
