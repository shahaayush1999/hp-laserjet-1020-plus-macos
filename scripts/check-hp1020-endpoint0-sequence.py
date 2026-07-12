#!/usr/bin/env python3
"""Validate endpoint-0 USB MMIO write sequences recovered from Xtensa disassembly."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


REPO = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = REPO / "analysis/usb-path/endpoint0-handshake-contract.json"

INSN_RE = re.compile(r"^\s*(?P<pc>[0-9a-f]{8}):\s+(?P<bytes>[0-9a-f ]+)\s+(?P<insn>.+?)\s*$")
L32R_RE = re.compile(r"^l32r\s+(?P<dst>a\d+),\s*[0-9a-f]+(?:\s+<(?P<label>[^>]+)>)?$")
MOVI_RE = re.compile(r"^movi(?:\.n)?\s+(?P<dst>a\d+),\s*(?P<value>-?(?:0x)?[0-9a-f]+)")
L32I_RE = re.compile(r"^l32i(?:\.n)?\s+(?P<dst>a\d+),\s*(?P<base>a\d+),\s*-?(?:0x)?[0-9a-f]+")
S32I_RE = re.compile(r"^s32i(?:\.n)?\s+(?P<src>a\d+),\s*(?P<base>a\d+),\s*-?(?:0x)?[0-9a-f]+")
OR_RE = re.compile(r"^or\s+(?P<dst>a\d+),\s*(?P<left>a\d+),\s*(?P<right>a\d+)")
DEST_RE = re.compile(r"^(?:mov(?:\.n)?|add(?:\.n)?|addi(?:\.n)?|and|xor|slli|srli|extui)\s+(?P<dst>a\d+)\b")
CALL_RE = re.compile(r"^call\d?\b")
USB_REG_RE = re.compile(r"b30[01][0-9a-f]{4}", re.IGNORECASE)
HEX8_RE = re.compile(r"(?<![0-9a-f])(?:0x)?(?P<value>[0-9a-f]{8})(?![0-9a-f])", re.IGNORECASE)


@dataclass(frozen=True)
class Event:
    severity: str
    kind: str
    pc: str
    register: str
    value: str | None
    operation: str
    sequence: str | None
    instruction: str
    description: str


def parse_int(value: str) -> int:
    value = value.lower()
    return int(value, 16) if value.startswith("0x") else int(value, 0)


def fmt32(value: int) -> str:
    return f"0x{value & 0xFFFFFFFF:08x}"


def label_usb_register(label: str | None) -> str | None:
    if not label:
        return None
    if match := USB_REG_RE.search(label):
        return f"0x{match.group(0).lower()}"
    return None


def label_const(label: str | None) -> int | None:
    if not label:
        return None
    matches = list(HEX8_RE.finditer(label))
    if not matches:
        return None
    return int(matches[-1].group("value"), 16)


def iter_files(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        if path.is_dir():
            yield from (p for p in sorted(path.rglob("*")) if p.is_file())
        else:
            yield path


def load_contract(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text())
    allowed_const: dict[tuple[str, str], list[str]] = {}
    for seq_name, writes in raw["usb_write_sequences"].items():
        for write in writes:
            allowed_const.setdefault((write["register"].lower(), write["value"].lower()), []).append(seq_name)
    allowed_or = {
        (item["register"].lower(), item["or_value"].lower()): item["meaning"]
        for item in raw.get("usb_or_writes", [])
    }
    return {"raw": raw, "allowed_const": allowed_const, "allowed_or": allowed_or}


def load_additional_contract(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {"allowed_const": {}, "allowed_or": {}, "roles": {}}
    raw = json.loads(path.read_text())
    allowed_const: dict[tuple[str, str], str] = {}
    allowed_or: dict[tuple[str, str], str] = {}
    roles: dict[str, str] = {}
    for register, item in raw.get("registers", {}).items():
        register = register.lower()
        roles[register] = item.get("role") or item.get("working_name") or "additional USB contract"
        for value in item.get("allowed_write_values", []):
            allowed_const[(register, value.lower())] = roles[register]
        for value in item.get("allowed_write_masks", []):
            normalized = value.lower().removeprefix("or ")
            allowed_or[(register, normalized)] = roles[register]
    return {"allowed_const": allowed_const, "allowed_or": allowed_or, "roles": roles}


def classify_write(
    register: str,
    value_state: dict[str, Any] | None,
    instruction: str,
    pc: str,
    contract: dict[str, Any],
) -> Event:
    if not value_state:
        return Event("fail", "unknown_usb_write", pc, register, None, "unknown", None, instruction, "USB write value is unknown")

    if value_state["kind"] == "const":
        value = fmt32(value_state["value"])
        key = (register, value)
        sequences = contract["allowed_const"].get(key)
        if sequences:
            sequence = ",".join(sorted(sequences))
            return Event("watch", "endpoint0_sequence_write", pc, register, value, "const", sequence, instruction, "expected endpoint-0 sequence write")
        if key in contract["additional"]["allowed_const"]:
            return Event(
                "watch",
                "additional_contract_write",
                pc,
                register,
                value,
                "const",
                "bulk_contract",
                instruction,
                contract["additional"]["allowed_const"][key],
            )
        return Event("fail", "unexpected_usb_write", pc, register, value, "const", None, instruction, "USB write is not in endpoint-0 contract")

    if value_state["kind"] == "mmio_or":
        value = fmt32(value_state["or_value"])
        source_register = value_state["register"]
        key = (register, value)
        if source_register == register and key in contract["allowed_or"]:
            return Event("watch", "endpoint0_or_write", pc, register, value, "or", None, instruction, contract["allowed_or"][key])
        if source_register == register and key in contract["additional"]["allowed_or"]:
            return Event(
                "watch",
                "additional_contract_or_write",
                pc,
                register,
                value,
                "or",
                "bulk_contract",
                instruction,
                contract["additional"]["allowed_or"][key],
            )
        return Event("fail", "unexpected_usb_or_write", pc, register, value, "or", None, instruction, "USB OR write is not in endpoint-0 contract")

    return Event("fail", "unknown_usb_write", pc, register, None, "unknown", None, instruction, "USB write value state is unsupported")


def scan_file(path: Path, contract: dict[str, Any]) -> list[Event]:
    events: list[Event] = []
    state: dict[str, Any] = {}

    for line in path.read_text(errors="replace").splitlines():
        match = INSN_RE.match(line)
        if not match:
            continue
        pc = f"0x{match.group('pc')}"
        insn = match.group("insn").strip()

        if m := L32R_RE.match(insn):
            dst = m.group("dst")
            label = m.group("label")
            if register := label_usb_register(label):
                state[dst] = {"kind": "mmio_ptr", "register": register}
            elif (value := label_const(label)) is not None:
                state[dst] = {"kind": "const", "value": value}
            else:
                state.pop(dst, None)
            continue

        if m := MOVI_RE.match(insn):
            state[m.group("dst")] = {"kind": "const", "value": parse_int(m.group("value"))}
            continue

        if m := L32I_RE.match(insn):
            dst = m.group("dst")
            base = state.get(m.group("base"))
            if base and base["kind"] == "mmio_ptr":
                state[dst] = {"kind": "mmio_value", "register": base["register"]}
            else:
                state.pop(dst, None)
            continue

        if m := OR_RE.match(insn):
            left = state.get(m.group("left"))
            right = state.get(m.group("right"))
            dst = m.group("dst")
            pairs = ((left, right), (right, left))
            for maybe_mmio, maybe_const in pairs:
                if (
                    maybe_mmio
                    and maybe_const
                    and maybe_mmio["kind"] == "mmio_value"
                    and maybe_const["kind"] == "const"
                ):
                    state[dst] = {
                        "kind": "mmio_or",
                        "register": maybe_mmio["register"],
                        "or_value": maybe_const["value"],
                    }
                    break
            else:
                state.pop(dst, None)
            continue

        if m := S32I_RE.match(insn):
            base = state.get(m.group("base"))
            if base and base["kind"] == "mmio_ptr":
                events.append(classify_write(base["register"], state.get(m.group("src")), insn, pc, contract))
            continue

        if CALL_RE.match(insn):
            state.clear()
        elif m := DEST_RE.match(insn):
            state.pop(m.group("dst"), None)

    return events


def render_markdown(events: list[Event], contract: dict[str, Any]) -> str:
    fail_count = sum(1 for event in events if event.severity == "fail")
    sequence_counts: dict[str, int] = {}
    for event in events:
        if event.sequence:
            sequence_counts[event.sequence] = sequence_counts.get(event.sequence, 0) + 1

    lines = [
        "# HP 1020 Endpoint-0 USB Write Sequence Scan",
        "",
        f"- recovered USB writes: `{len(events)}`",
        f"- fail hits: `{fail_count}`",
        "",
        "## Sequence Counts",
        "",
    ]
    if sequence_counts:
        for sequence, count in sorted(sequence_counts.items()):
            lines.append(f"- `{sequence}`: `{count}`")
    else:
        lines.append("- none")

    lines.extend(["", "## Events", "", "| Severity | Kind | PC | Register | Value | Sequence | Instruction | Description |", "|---|---|---:|---:|---:|---|---|---|"])
    for event in events:
        safe_insn = event.instruction.replace("|", "\\|")
        lines.append(
            f"| `{event.severity}` | `{event.kind}` | `{event.pc}` | `{event.register}` | "
            f"`{event.value or ''}` | `{event.sequence or ''}` | `{safe_insn}` | {event.description} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="Xtensa objdump text files")
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument(
        "--additional-mmio-map",
        type=Path,
        help="optional generated USB map whose explicit write values/masks are accepted alongside endpoint 0",
    )
    parser.add_argument("-o", "--output", type=Path, help="write markdown report")
    parser.add_argument("--json", type=Path, help="write JSON event list")
    parser.add_argument("--allow-fail", action="store_true", help="exit 0 even if fail hits are found")
    args = parser.parse_args()

    contract = load_contract(args.contract)
    contract["additional"] = load_additional_contract(args.additional_mmio_map)
    events: list[Event] = []
    for path in iter_files(args.paths):
        events.extend(scan_file(path, contract))
    events.sort(key=lambda event: int(event.pc, 16))

    report = render_markdown(events, contract)
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
