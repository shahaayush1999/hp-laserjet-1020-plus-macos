#!/usr/bin/env python3
"""Extract a focused USB MMIO map from the HP 1020 USB static-analysis notes."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "analysis/usb-path/internal-blocks.md"
OUT_JSON = REPO / "analysis/usb-path/usb-mmio-map.json"
OUT_MD = REPO / "analysis/usb-path/usb-mmio-map.md"

INSTRUCTION_RE = re.compile(
    r"^- `(?P<pc>[0-9a-f]{8})` `(?P<insn>[^`]+)`(?: refs=(?P<refs>.*))?$"
)
TARGET_RE = re.compile(r"^## Target `(?P<target>[0-9a-f]{8})`$")
BLOCK_RE = re.compile(r"^### Depth (?P<depth>\d+) Block `(?P<start>[0-9a-f]{8})` - `(?P<end>[0-9a-f]{8})`$")
REF_RE = re.compile(r"`(?P<addr>[0-9a-f]{8})`/(?P<kind>[A-Z_]+)")
MOVI_RE = re.compile(r"^movi(?:\.n)? (?P<dst>a\d+),(?P<value>-?0x[0-9a-f]+|-?\d+)$")
L32R_RE = re.compile(r"^l32r (?P<dst>a\d+),0x(?P<literal>[0-9a-f]{8})$")
OR_RE = re.compile(r"^or (?P<dst>a\d+),(?P<left>a\d+),(?P<right>a\d+)$")
S32I_RE = re.compile(r"^s32i(?:\.n)? (?P<src>a\d+),(?P<base>a\d+),0x[0-9a-f]+$")
L32I_RE = re.compile(r"^l32i(?:\.n)? (?P<dst>a\d+),(?P<base>a\d+),0x[0-9a-f]+$")


REGISTER_NOTES: dict[str, dict[str, str]] = {
    "0xb3000000": {
        "working_name": "main USB command/status kick",
        "role": "Read/modify/write control bits. Evidence includes bit 0x2 before control-IN staging and bit 0x1 after setup completion; decompiler also shows 0x108 to start transfer descriptors.",
        "open_firmware_relevance": "core endpoint-0 bring-up and transmit kick",
    },
    "0xb300000c": {
        "working_name": "endpoint/request ack register",
        "role": "Written with 0x40 during descriptor request paths.",
        "open_firmware_relevance": "likely needed to acknowledge/advance setup handling",
    },
    "0xb3000014": {
        "working_name": "control-IN descriptor submit register",
        "role": "Written with the transfer descriptor ring pointer before the 0x108 control-IN kick.",
        "open_firmware_relevance": "needed to submit endpoint-0 transfer descriptors without the stock helper",
    },
    "0xb3000028": {
        "working_name": "post-response ack/kick register",
        "role": "Written after descriptor-specific setup and before calling the control-IN sender.",
        "open_firmware_relevance": "likely needed after preparing a descriptor response",
    },
    "0xb300002c": {
        "working_name": "endpoint/request ack register",
        "role": "Written with 0x40 or 0x200 in descriptor request paths.",
        "open_firmware_relevance": "likely tied to full-speed/high-speed or direction-specific completion",
    },
    "0xb3000200": {
        "working_name": "USB event/interrupt ack register",
        "role": "Read/modify/write with event bits 0x1 and 0x100.",
        "open_firmware_relevance": "needed to acknowledge controller events without the stock interrupt/thread queue",
    },
    "0xb300020c": {
        "working_name": "endpoint/request ack register",
        "role": "Written with 0x40 in descriptor request paths.",
        "open_firmware_relevance": "likely needed to clear/advance control endpoint state",
    },
    "0xb3000214": {
        "working_name": "USB event/setup buffer pointer",
        "role": "Read as a pointer, then dereferenced as bytes that are compared against an event signature.",
        "open_firmware_relevance": "plausible source of setup/event packet metadata",
    },
    "0xb300022c": {
        "working_name": "endpoint/request ack register",
        "role": "Written with 0x40 or 0x200 in descriptor request paths.",
        "open_firmware_relevance": "likely tied to endpoint request acknowledgement",
    },
    "0xb3000400": {
        "working_name": "control/setup status gate",
        "role": "Read before choosing descriptor response source. Low two bits are tested.",
        "open_firmware_relevance": "likely tells whether a setup/status condition is ready",
    },
    "0xb3000408": {
        "working_name": "control/setup status gate",
        "role": "Read and tested against a mask before choosing descriptor response source.",
        "open_firmware_relevance": "likely selects the active descriptor/config branch",
    },
    "0xb3000504": {
        "working_name": "control endpoint descriptor/config register",
        "role": "Written with a constant/pointer-like value during one descriptor branch.",
        "open_firmware_relevance": "part of stock setup response register programming",
    },
    "0xb3000508": {
        "working_name": "control endpoint descriptor/config register",
        "role": "Written during both device/config descriptor branches.",
        "open_firmware_relevance": "part of stock setup response register programming",
    },
    "0xb300050c": {
        "working_name": "control endpoint descriptor/config register",
        "role": "Written during descriptor branches and passed into the control-IN sender path.",
        "open_firmware_relevance": "part of stock setup response register programming",
    },
    "0xb3000510": {
        "working_name": "control endpoint descriptor/config register",
        "role": "Written during descriptor branches and passed into the control-IN sender path.",
        "open_firmware_relevance": "part of stock setup response register programming",
    },
}


def parse_int(value: str) -> int:
    return int(value, 0)


def normalize_addr(addr: str) -> str:
    return f"0x{addr.lower()}"


def split_operands(insn: str) -> list[str]:
    if " " not in insn:
        return []
    return [part.strip() for part in insn.split(" ", 1)[1].split(",")]


def extract_refs(refs_text: str | None) -> list[dict[str, str]]:
    if not refs_text:
        return []
    return [{"addr": normalize_addr(m.group("addr")), "kind": m.group("kind")} for m in REF_RE.finditer(refs_text)]


def update_symbolic_state(
    insn: str,
    constants: dict[str, int],
    pointer_literals: dict[str, str],
    last_or: dict[str, dict[str, Any]],
) -> None:
    if m := MOVI_RE.match(insn):
        constants[m.group("dst")] = parse_int(m.group("value"))
        pointer_literals.pop(m.group("dst"), None)
        last_or.pop(m.group("dst"), None)
        return

    if m := L32R_RE.match(insn):
        dst = m.group("dst")
        pointer_literals[dst] = normalize_addr(m.group("literal"))
        constants.pop(dst, None)
        last_or.pop(dst, None)
        return

    if m := OR_RE.match(insn):
        dst = m.group("dst")
        left = m.group("left")
        right = m.group("right")
        known = []
        for reg in (left, right):
            if reg in constants:
                known.append(constants[reg])
        constants.pop(dst, None)
        pointer_literals.pop(dst, None)
        if known:
            last_or[dst] = {
                "operation": "or_with_immediate",
                "immediates": sorted(set(known)),
                "instruction": insn,
            }
        else:
            last_or.pop(dst, None)
        return

    if m := L32I_RE.match(insn):
        dst = m.group("dst")
        constants.pop(dst, None)
        pointer_literals.pop(dst, None)
        last_or.pop(dst, None)


def infer_write_value(insn: str, constants: dict[str, int], last_or: dict[str, dict[str, Any]]) -> dict[str, Any]:
    m = S32I_RE.match(insn)
    if not m:
        return {}
    src = m.group("src")
    out: dict[str, Any] = {"source_register": src}
    if src in constants:
        out["immediate"] = constants[src]
    if src in last_or:
        out["operation"] = last_or[src]
    return out


def parse_internal_blocks() -> dict[str, Any]:
    target = None
    block = None
    constants: dict[str, int] = {}
    pointer_literals: dict[str, str] = {}
    last_or: dict[str, dict[str, Any]] = {}
    registers: dict[str, dict[str, Any]] = {}
    pointer_symbols: dict[str, Counter[str]] = defaultdict(Counter)

    for line in SOURCE.read_text().splitlines():
        if m := TARGET_RE.match(line):
            target = normalize_addr(m.group("target"))
            block = None
            constants = {}
            pointer_literals = {}
            last_or = {}
            continue

        if m := BLOCK_RE.match(line):
            block = {
                "depth": int(m.group("depth")),
                "start": normalize_addr(m.group("start")),
                "end": normalize_addr(m.group("end")),
            }
            constants = {}
            pointer_literals = {}
            last_or = {}
            continue

        m = INSTRUCTION_RE.match(line)
        if not m:
            continue

        pc = normalize_addr(m.group("pc"))
        insn = m.group("insn")
        refs = extract_refs(m.group("refs"))

        for ref in refs:
            addr = ref["addr"]
            if not addr.startswith("0xb300"):
                continue
            access = ref["kind"].lower()
            reg = registers.setdefault(
                addr,
                {
                    "register": addr,
                    "working_name": REGISTER_NOTES.get(addr, {}).get("working_name", "unknown USB register"),
                    "role": REGISTER_NOTES.get(addr, {}).get("role", "Uninterpreted USB-controller register from static references."),
                    "open_firmware_relevance": REGISTER_NOTES.get(addr, {}).get("open_firmware_relevance", "unknown"),
                    "counts": {"read": 0, "write": 0, "param": 0, "other": 0},
                    "events": [],
                    "write_values": [],
                    "pointer_symbols": {},
                },
            )
            if access in reg["counts"]:
                reg["counts"][access] += 1
            else:
                reg["counts"]["other"] += 1

            event: dict[str, Any] = {
                "pc": pc,
                "access": access,
                "instruction": insn,
                "target": target,
                "block": block,
            }
            write_value = infer_write_value(insn, constants, last_or) if access == "write" else {}
            if write_value:
                event["write_value"] = write_value
                reg["write_values"].append({"pc": pc, **write_value})

            operands = split_operands(insn)
            base_reg = operands[1] if len(operands) >= 2 else None
            if base_reg in pointer_literals:
                pointer_symbols[addr][pointer_literals[base_reg]] += 1
                event["pointer_literal"] = pointer_literals[base_reg]

            reg["events"].append(event)

        update_symbolic_state(insn, constants, pointer_literals, last_or)

    for reg_addr, symbols in pointer_symbols.items():
        registers[reg_addr]["pointer_symbols"] = dict(sorted(symbols.items()))

    add_manual_control_in_submit_register(registers)

    ordered = dict(sorted(registers.items()))
    summary = {
        "source": str(SOURCE.relative_to(REPO)),
        "register_count": len(ordered),
        "access_totals": dict(
            sorted(
                Counter(
                    access
                    for reg in ordered.values()
                    for access, count in reg["counts"].items()
                    for _ in range(count)
                ).items()
            )
        ),
        "registers": ordered,
    }
    return summary


def add_manual_control_in_submit_register(registers: dict[str, dict[str, Any]]) -> None:
    """Add evidence from the decompiled 0x10008c24 tail not present in internal-blocks.md."""

    addr = "0xb3000014"
    reg = registers.setdefault(
        addr,
        {
            "register": addr,
            "working_name": REGISTER_NOTES[addr]["working_name"],
            "role": REGISTER_NOTES[addr]["role"],
            "open_firmware_relevance": REGISTER_NOTES[addr]["open_firmware_relevance"],
            "counts": {"read": 0, "write": 0, "param": 0, "other": 0},
            "events": [],
            "write_values": [],
            "pointer_symbols": {},
        },
    )
    for pc in ("0x10008ce4", "0x10008e50"):
        if any(event["pc"] == pc for event in reg["events"]):
            continue
        reg["counts"]["write"] += 1
        event = {
            "pc": pc,
            "access": "write",
            "instruction": "*DAT_10005ea0 = *(undefined4 *)PTR_DAT_10005e98",
            "target": "0x10008c24",
            "block": {"depth": 0, "start": "0x10008c24", "end": "0x10008eef"},
            "pointer_literal": "0x10005ea0",
            "note": "manual evidence from analysis/usb-path/decompiled-neighbors/10008c24_hp1020_usb_control_tx_data_stage_candidate.c",
        }
        reg["events"].append(event)
        reg["write_values"].append(
            {
                "pc": pc,
                "source_register": "DAT_10005ea0",
                "pointer_value": "0x900226f0",
            }
        )
    reg["pointer_symbols"] = {"0x10005ea0": reg["counts"]["write"]}


def format_hex(value: int) -> str:
    return f"0x{value:x}"


def write_markdown(data: dict[str, Any]) -> None:
    lines = [
        "# HP 1020 USB MMIO Register Map",
        "",
        "This is a generated map of USB-controller register evidence from",
        "`analysis/usb-path/internal-blocks.md`. It narrows the open-firmware",
        "USB-marker problem to the registers the stock endpoint-0 path actually",
        "touches.",
        "",
        "## Plain-English Summary",
        "",
        "The descriptor bytes are no longer the mystery. The remaining USB work is",
        "figuring out the small controller handshake around setup packets and",
        "control-IN responses.",
        "",
        "The important register family is `0xb300....`. Static evidence clusters it",
        "into four groups:",
        "",
        "- setup/status gates: `0xb3000400`, `0xb3000408`",
        "- descriptor/control register programming: `0xb3000504`, `0xb3000508`, `0xb300050c`, `0xb3000510`",
        "- event/ack/kick registers: `0xb3000000`, `0xb300000c`, `0xb3000028`, `0xb300002c`, `0xb3000200`, `0xb300020c`, `0xb300022c`",
        "- setup/event buffer pointer: `0xb3000214`",
        "",
        "## Register Summary",
        "",
        "| Register | Working Name | Reads | Writes | Params | Main Meaning |",
        "|---:|---|---:|---:|---:|---|",
    ]

    for reg in data["registers"].values():
        counts = reg["counts"]
        lines.append(
            f"| `{reg['register']}` | {reg['working_name']} | {counts['read']} | "
            f"{counts['write']} | {counts['param']} | {reg['role']} |"
        )

    lines.extend(
        [
            "",
            "## Write Constants and Bit Operations",
            "",
            "| Register | Evidence |",
            "|---:|---|",
        ]
    )
    for reg in data["registers"].values():
        write_bits = []
        for value in reg["write_values"]:
            if "immediate" in value:
                write_bits.append(f"`{value['pc']}` writes `{format_hex(value['immediate'])}`")
            if "pointer_value" in value:
                write_bits.append(f"`{value['pc']}` submits pointer `{value['pointer_value']}`")
            op = value.get("operation")
            if op:
                immediates = ", ".join(f"`{format_hex(v)}`" for v in op["immediates"])
                write_bits.append(f"`{value['pc']}` ORs {immediates} before write")
        if not write_bits:
            write_bits.append("no immediate constant inferred from local block")
        lines.append(f"| `{reg['register']}` | {'; '.join(write_bits)} |")

    lines.extend(
        [
            "",
            "## Per-Register Details",
            "",
        ]
    )
    for reg in data["registers"].values():
        lines.extend(
            [
                f"### `{reg['register']}` - {reg['working_name']}",
                "",
                reg["role"],
                "",
                f"Open-firmware relevance: {reg['open_firmware_relevance']}.",
                "",
            ]
        )
        if reg["pointer_symbols"]:
            rendered = ", ".join(f"`{symbol}` ({count})" for symbol, count in reg["pointer_symbols"].items())
            lines.extend(["Pointer/literal sources seen before access:", "", f"- {rendered}", ""])
        lines.extend(["Representative events:", ""])
        for event in reg["events"][:8]:
            block = event["block"]
            block_text = f"{block['start']}..{block['end']}" if block else "unknown block"
            lines.append(f"- `{event['pc']}` {event['access'].upper()} in {block_text}: `{event['instruction']}`")
        if len(reg["events"]) > 8:
            lines.append(f"- ... {len(reg['events']) - 8} more events in JSON")
        lines.append("")

    lines.extend(
        [
            "## What This Changes",
            "",
            "This does not make a printer-side USB marker automatic, but it turns the",
            "unknown from \"reverse engineer USB\" into a smaller checklist:",
            "",
            "1. Poll/read `0xb3000400` and `0xb3000408` to identify setup readiness.",
            "2. Confirm whether `0xb3000214` exposes an event/setup buffer after host enumeration.",
            "3. Program the `0xb3000504..0xb3000510` group only after matching stock conditions.",
            "4. Kick/ack with the observed `0x40`, `0x200`, `0x1`, `0x100`, and `0x108` patterns.",
            "",
            "Until those register semantics are tested on hardware, an open USB marker is",
            "still a controller-handshake problem rather than a descriptor-payload problem.",
            "",
        ]
    )

    OUT_MD.write_text("\n".join(lines))


def main() -> None:
    data = parse_internal_blocks()
    missing = sorted(set(REGISTER_NOTES) - set(data["registers"]))
    if missing:
        raise SystemExit(f"expected registers missing from static map: {missing}")
    for required in ("0xb3000000", "0xb3000200", "0xb3000400", "0xb3000408", "0xb3000508"):
        counts = data["registers"][required]["counts"]
        if counts["read"] + counts["write"] + counts["param"] == 0:
            raise SystemExit(f"{required} has no access evidence")

    OUT_JSON.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    write_markdown(data)
    print(f"wrote {OUT_JSON.relative_to(REPO)}")
    print(f"wrote {OUT_MD.relative_to(REPO)}")


if __name__ == "__main__":
    main()
