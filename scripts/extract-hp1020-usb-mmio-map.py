#!/usr/bin/env python3
"""Extract a focused USB MMIO map from the HP 1020 USB static-analysis notes."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from hp1020_xtensa_properties import properties, section_bytes


REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "analysis/usb-path/internal-blocks.md"
OUT_JSON = REPO / "analysis/usb-path/usb-mmio-map.json"
OUT_MD = REPO / "analysis/usb-path/usb-mmio-map.md"
STOCK = REPO / "analysis/sihp1020.elf"
STOCK_SHA256 = "2111560068db47ceca21fa550db4c7c34f5595b5a5d137ae4a19631e40e3601d"
UDC_HEADER = REPO / "analysis/usb-path/controller-reference/linux-v6.12/amd5536udc.h"
UDC_HEADER_SHA256 = "8dbf2ebffe7de042bdfea1c5e4e0d7e7ca334cb821fbfaa1cf9ccfeeae302648"

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
        "working_name": "EP0 IN control (EPCTL)",
        "role": "Original control requests include 0x2 and 0x108. Family names are F/flush and CNAK plus P/poll demand; bit 0 is S/stall. These are not interrupt acknowledgements.",
        "open_firmware_relevance": "separate endpoint control intent from actual completion and safe buffer reuse",
    },
    "0xb300000c": {
        "working_name": "EP0 IN maximum-packet word",
        "role": "Written with 0x40 during descriptor request paths.",
        "open_firmware_relevance": "packet-size configuration, not acknowledgement",
    },
    "0xb3000014": {
        "working_name": "control-IN descriptor submit register",
        "role": "Written with the transfer descriptor pointer before the 0x108 CNAK/poll-demand request. Original stores are 0x10008d0c and 0x10008f1b.",
        "open_firmware_relevance": "needed to submit endpoint-0 transfer descriptors without the stock helper",
    },
    "0xb3000028": {
        "working_name": "EP1 IN buffer-size word",
        "role": "Endpoint 1 IN +0x08 is buffer-size configuration under the family layout; the stock path writes 0x40.",
        "open_firmware_relevance": "buffer configuration, not acknowledgement or completion",
    },
    "0xb300002c": {
        "working_name": "EP1 IN maximum-packet word",
        "role": "Written with 0x40 or 0x200 in descriptor request paths.",
        "open_firmware_relevance": "full/high-speed packet-size configuration",
    },
    "0xb3000200": {
        "working_name": "EP0 OUT control (EPCTL)",
        "role": "Read/modify/write control requests include S/stall bit 0 and CNAK bit 8. CNAK does not acknowledge an interrupt or establish DMA quiescence.",
        "open_firmware_relevance": "OUT0 endpoint control is separate from OUT0 status/interrupt acknowledgement",
    },
    "0xb300020c": {
        "working_name": "EP0 OUT maximum-packet/buffer word",
        "role": "Written with 0x40 in descriptor request paths.",
        "open_firmware_relevance": "packet-size/buffer configuration, not acknowledgement",
    },
    "0xb3000214": {
        "working_name": "EP0 OUT ordinary data/status descriptor pointer (DESPTR)",
        "role": "At 0x10009890 the original reads DESPTR and checks descriptor ownership. SETUP instead uses the distinct SUBPTR register 0xb3000210.",
        "open_firmware_relevance": "do not confuse ordinary OUT0 descriptor completion with SETUP storage",
    },
    "0xb300022c": {
        "working_name": "EP1 OUT maximum-packet/buffer word",
        "role": "Written with 0x40 or 0x200 in descriptor request paths.",
        "open_firmware_relevance": "full/high-speed receive packet-size configuration",
    },
    "0xb3000400": {
        "working_name": "device configuration (DEVCFG)",
        "role": "Read before choosing descriptor response source. Low two bits are tested.",
        "open_firmware_relevance": "low two bits select configured speed in the family layout; not SETUP readiness",
    },
    "0xb3000408": {
        "working_name": "device status (DEVSTS)",
        "role": "Read and tested against 0x6000 before choosing descriptor response source; the family layout calls these enumerated-speed bits.",
        "open_firmware_relevance": "speed-dependent descriptor/configuration selection, not SETUP ownership",
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

# This map is also consumed by an existing hardware allowlist. New semantic
# evidence is separate metadata; do not add registers or write permissions.
PRESERVED_REGISTERS = frozenset((
    "0xb3000000", "0xb300000c", "0xb3000014", "0xb3000028", "0xb300002c",
    "0xb3000200", "0xb300020c", "0xb3000214", "0xb300022c", "0xb3000400",
    "0xb3000408", "0xb3000504", "0xb3000508", "0xb300050c", "0xb3000510",
))
LITERAL_ANCHORS = {
    0x10005DF4: 0xB3000400, 0x10005E68: 0xB3000408, 0x10005EA4: 0x6000,
    0x10005E90: 0xB3000000, 0x10005E24: 0xB3000200, 0x10005EA0: 0xB3000014,
    0x10005E98: 0x1001BC58, 0x1001BC58: 0x900226F0,
    0x10005E9C: 0xB300000C, 0x10005EE0: 0xB300002C,
    0x10005EE4: 0xB300020C, 0x10005F08: 0xB300022C, 0x10005EDC: 0xB3000028,
    0x10005EF4: 0xB3000210, 0x10005EF8: 0xB3000214,
}
BYTE_ANCHORS = {
    0x10009476: ("18f27c", "load DEVSTS address literal"),
    0x1000947C: ("8980", "sample DEVSTS"),
    0x1000947E: ("18f289", "load enumerated-speed mask 0x6000"),
    0x10009484: ("18f25c", "load DEVCFG address literal"),
    0x1000948A: ("8880", "sample DEVCFG"),
    0x1000948C: ("080841", "extract configured-speed low two bits"),
    0x100094E2: ("19f289", "load OUT1 maximum-packet address"),
    0x100094E5: ("c460", "movi.n a6,64: packet-size value"),
    0x100094EC: ("9690", "write OUT1 packet size"),
    0x100094EE: ("18f27d", "load OUT0 maximum-packet address"),
    0x100094F1: ("19f26a", "load IN0 maximum-packet address"),
    0x100094F7: ("9680", "write OUT0 packet size"),
    0x100094FC: ("9690", "write IN0 packet size"),
    0x100094FE: ("18f278", "load IN1 maximum-packet address"),
    0x10009501: ("19f276", "load IN1 buffer-size address"),
    0x10009507: ("9680", "write IN1 packet size"),
    0x10009597: ("9690", "write IN1 buffer size"),
    0x1000935B: ("18f2e6", "SETUP admission loads SUBPTR address"),
    0x10009890: ("18f19a", "ordinary OUT0 admission loads DESPTR address"),
    0x100098F9: ("16f14a", "load OUT0 control address"),
    0x100098FC: ("2a1a00", "movi a10,0x100: CNAK request mask"),
    0x10009909: ("0a8802", "add CNAK to sampled control"),
    0x1000990F: ("9860", "write OUT0 control request"),
    0x10008C2A: ("14f499", "load IN0 control address"),
    0x10008C37: ("c022", "movi.n a2,2: F/flush request mask"),
    0x10008C3F: ("9840", "write IN0 F request"),
    0x10008C74: ("1cf489", "load IN0 descriptor global for zero-length path"),
    0x10008D02: ("88c0", "load descriptor pointer through global"),
    0x10008D04: ("19f467", "load IN0 DESPTR address"),
    0x10008D0C: ("9890", "actual zero-length descriptor submission store"),
    0x10008D13: ("291a08", "movi a9,0x108: CNAK and poll demand"),
    0x10008D30: ("17f45a", "load IN0 descriptor global for nonempty path"),
    0x10008F11: ("19f3e3", "load IN0 DESPTR address"),
    0x10008F14: ("8870", "load descriptor pointer through global"),
    0x10008F1B: ("9890", "actual nonempty descriptor submission store"),
    0x10008F22: ("291a08", "movi a9,0x108: CNAK and poll demand"),
}


def corrected_byte_evidence() -> dict[str, Any]:
    blob = STOCK.read_bytes()
    if hashlib.sha256(blob).hexdigest() != STOCK_SHA256:
        raise ValueError("USB register evidence differs from the pinned stock ELF")
    sections, _ = properties(blob)
    required = {address: (value.to_bytes(4, "big").hex(), "original address/value literal")
                for address, value in LITERAL_ANCHORS.items()}
    required.update(BYTE_ANCHORS)
    checks = []
    for address, (encoded, meaning) in required.items():
        raw = bytes.fromhex(encoded)
        if section_bytes(blob, sections, address, len(raw)) != raw:
            raise ValueError(f"USB register evidence differs at {address:#x}")
        checks.append(dict(status="present", address=hex(address), bytes=encoded, meaning=meaning))
    header = UDC_HEADER.read_bytes()
    if hashlib.sha256(header).hexdigest() != UDC_HEADER_SHA256:
        raise ValueError("pinned controller-family header changed")
    definitions = {name: int(value, 0) for name, value in re.findall(
        r"^#define\s+(UDC_\w+)\s+(0x[0-9a-fA-F]+|[0-9]+)\s*(?:/\*.*)?$", header.decode(), re.M)}
    for name, value in (("UDC_DEVCFG_SPD_MASK", 3), ("UDC_DEVSTS_ENUM_SPEED_MASK", 0x6000),
                        ("UDC_EP_MAX_PKT_SIZE_ADDR", 0x0c), ("UDC_EPIN_BUFF_SIZE_ADDR", 8),
                        ("UDC_EP_SUBPTR_ADDR", 0x10), ("UDC_EP_DESPTR_ADDR", 0x14),
                        ("UDC_EPCTL_CNAK", 8), ("UDC_EPCTL_F", 1), ("UDC_EPCTL_P", 3)):
        if definitions[name] != value:
            raise ValueError(f"controller-family field differs: {name}")
    return dict(stock_elf_sha256=STOCK_SHA256, original_byte_checks=checks,
                controller_reference=dict(header=str(UDC_HEADER.relative_to(REPO)), sha256=UDC_HEADER_SHA256),
                setup_descriptor_pointer_register="0xb3000210",
                setup_register_is_added_to_allowlist=False,
                semantic_limit="Family names describe original register intent, not verified HP hardware effects. SUBPTR is documented separately and does not expand the existing register/write allowlist.")


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
    corrected = corrected_byte_evidence()
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
    if set(ordered) != PRESERVED_REGISTERS:
        raise ValueError("semantic correction must preserve the existing register allowlist")
    summary = {
        "source": str(SOURCE.relative_to(REPO)),
        "corrected_evidence": corrected,
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
    """Add exact original stores omitted by the saved internal-block extract."""

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
    for pc in ("0x10008d0c", "0x10008f1b"):
        if any(event["pc"] == pc for event in reg["events"]):
            continue
        reg["counts"]["write"] += 1
        event = {
            "pc": pc,
            "access": "write",
            "instruction": "s32i.n a8,a9,0",
            "target": "0x10008c24",
            "block": {"depth": 0, "start": "0x10008c24", "end": "0x10008f39"},
            "pointer_literal": "0x10005ea0",
            "note": "Original instruction/literal anchors resolve IN0 DESPTR and global 0x1001bc58. Its file-backed initializer is 0x900226f0; no runtime transfer is observed.",
        }
        reg["events"].append(event)
        reg["write_values"].append(
            {
                "pc": pc,
                "source_register": "a8",
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
        "This generated map retains saved static references and verifies corrected",
        "meanings against original bytes and the pinned controller-family header.",
        "Its 15-register allowlist and permitted writes are unchanged; no hardware",
        "operation or controller timing is validated here.",
        "",
        "## Plain-English Summary",
        "",
        "Separate endpoint control requests, status acknowledgement, descriptor",
        "ownership and speed/packet-size configuration. Similar numeric masks at",
        "different addresses are not interchangeable operations.",
        "",
        "The important register family is `0xb300....`. Static evidence clusters it",
        "into four groups:",
        "",
        "- configured/enumerated speed fields: `0xb3000400`, `0xb3000408`",
        "- descriptor/control register programming: `0xb3000504`, `0xb3000508`, `0xb300050c`, `0xb3000510`",
        "- EP0 IN/OUT control: `0xb3000000`, `0xb3000200`; maximum-packet/buffer words: `0xb300000c`, `0xb3000028`, `0xb300002c`, `0xb300020c`, `0xb300022c`",
        "- ordinary OUT0 descriptor pointer (DESPTR): `0xb3000214`",
        "",
        "SETUP uses distinct SUBPTR `0xb3000210`, proven by original initialization",
        "and admission bytes. It is documentation metadata here, not an addition",
        "to this existing hardware allowlist. `setup-ingress.json` records the",
        "separate RAM-only admission/conversion experiment.",
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
            "A controller adapter still needs distinct ownership and event contracts:",
            "",
            "1. Keep configured/enumerated speed fields separate from SETUP ownership.",
            "2. Preserve the original eight wire bytes and distinguish SETUP SUBPTR from ordinary OUT0 DESPTR.",
            "3. Separate endpoint packet-size/buffer configuration from command/status masks.",
            "4. Validate original transfer identity, descriptor completion and errors before publishing a completion event.",
            "",
            "The original submission stores are `0x10008d0c` and `0x10008f1b`; older",
            "manual PCs `0x10008ce4`/`0x10008e50` were not the submission stores.",
            "Command intent, wake flags and supplied RAM completion do not establish",
            "DMA/cache behavior, abort completion or safe physical buffer reuse.",
            "Hardware tests still require the existing explicit owner authorization.",
            "",
        ]
    )

    lines.extend(["## Original Byte Checks", "", "| Address | Bytes | Meaning |", "|---:|---|---|"])
    for item in data["corrected_evidence"]["original_byte_checks"]:
        lines.append(f"| `{item['address']}` | `{item['bytes']}` | {item['meaning']} |")
    lines.append("")

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
