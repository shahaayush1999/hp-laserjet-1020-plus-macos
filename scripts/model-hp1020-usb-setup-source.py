#!/usr/bin/env python3
"""Model byte-supported SETUP storage and stock/request wire representations."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from hp1020_xtensa_properties import properties, section_bytes


ROOT_DIR = Path(__file__).resolve().parents[1]
INTERNAL_BLOCKS = ROOT_DIR / "analysis/usb-path/internal-blocks.md"
HANDSHAKE_JSON = ROOT_DIR / "analysis/usb-path/endpoint0-handshake-contract.json"
MEMORY_SCAN_JSON = ROOT_DIR / "analysis/open-firmware-probes/usb-marker-draft/memory-boundary-scan.json"
OUT_JSON = ROOT_DIR / "analysis/usb-path/usb-setup-source.json"
OUT_MD = ROOT_DIR / "analysis/usb-path/usb-setup-source.md"
STOCK = ROOT_DIR / "analysis/sihp1020.elf"
STOCK_SHA256 = "2111560068db47ceca21fa550db4c7c34f5595b5a5d137ae4a19631e40e3601d"
INGRESS_SHA256 = "e63fe132beeff99b0602625ec3f3d4a5f8fe3c5c048c0d2a5ceb65d8c5f175aa"

REF_RE = re.compile(r"- `(?P<pc>[0-9a-f]{8})` `(?P<insn>[^`]+)` refs=`(?P<ref>[0-9a-f]+)`/(?P<kind>[A-Z_]+)")

SETUP_BASE = 0x90021348
SETUP_END = SETUP_BASE + 8
RAW_SETUP_FIELDS = {
    0: "bmRequestType",
    1: "bRequest",
    2: "wValue low / descriptor index",
    3: "wValue high / descriptor type",
    4: "wIndex low",
    5: "wIndex high",
    6: "wLength low",
    7: "wLength high",
}
STOCK_SETUP_FIELDS = {
    **RAW_SETUP_FIELDS,
    4: "wIndex high (after stock conversion)",
    5: "wIndex low (after stock conversion)",
    6: "wLength high (after stock conversion)",
    7: "wLength low (after stock conversion)",
}
LITERALS = {
    0x10005EE8: 0x1001BBC0, 0x10005EF4: 0xB3000210,
    0x10005EF8: 0xB3000214, 0x10005E30: 0xC0000000,
    0x10005E34: 0x80000000, 0x10005F24: 0x30000000,
    0x1001BBC0: 0x90021340, 0x1001BC60: 0x90022BC0,
    0x1001BC48: 0x90021370,
}
BYTE_ANCHORS = {
    0x10009123: ("1bf371", "l32r a11,0x10005ee8: SETUP-record global"),
    0x100091A5: ("19f353", "l32r a9,0x10005ef4: OUT0 SUBPTR address"),
    0x100091A8: ("88b0", "l32i.n a8,a11,0: initial SETUP-record pointer"),
    0x100091B0: ("9890", "s32i.n a8,a9,0: SETUP pointer submission"),
    0x100091BC: ("1bf34f", "l32r a11,0x10005ef8: distinct OUT0 DESPTR"),
    0x100091C7: ("98b0", "s32i.n a8,a11,0: ordinary OUT0 descriptor submission"),
    0x10009361: ("8b80", "l32i.n a11,a8,0: status pointer through SUBPTR"),
    0x1000938A: ("798102", "beq a8,a9,0x10009390: owner comparison"),
    0x10009393: ("78a002", "bnone a10,a8,0x10009399: RX mask must be zero"),
    0x1000939C: ("2c8200", "l32i a12,a8,0: independent SETUP-record global"),
    0x1000939F: ("24cc08", "addi a4,a12,8: request bytes follow two words"),
    0x100093C6: ("284406", "s8i a8,a4,6: stock wLength high byte"),
    0x100093D5: ("2a4407", "s8i a10,a4,7: stock wLength low byte"),
    0x100093FC: ("284404", "s8i a8,a4,4: stock wIndex high byte"),
    0x1000940B: ("2a4405", "s8i a10,a4,5: stock wIndex low byte"),
    0x10009890: ("18f19a", "l32r a8,0x10005ef8: subsequent ordinary OUT0 descriptor path"),
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def collect_stock_setup_refs() -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for match in REF_RE.finditer(INTERNAL_BLOCKS.read_text()):
        ref = int(match.group("ref"), 16)
        if SETUP_BASE <= ref < SETUP_END:
            offset = ref - SETUP_BASE
            pc = int(match.group("pc"), 16)
            if not 0x1000940E <= pc < 0x10009884:
                raise ValueError(f"SETUP reference is outside the established post-conversion dispatch: {pc:#x}")
            refs.append(
                {
                    "pc": f"0x{match.group('pc')}",
                    "instruction": match.group("insn"),
                    "address": f"0x{ref:08x}",
                    "offset": f"0x{offset:x}",
                    "field": STOCK_SETUP_FIELDS[offset],
                    "representation": "stock_after_wIndex_wLength_conversion",
                    "reference_kind": match.group("kind"),
                }
            )
    return refs


def collect_marker_setup_refs() -> list[dict[str, Any]]:
    refs = []
    for item in load_json(MEMORY_SCAN_JSON):
        if item.get("kind") == "setup_packet_buffer" and item.get("access") == "read":
            offset = int(item["offset"], 16)
            refs.append(
                {
                    "pc": item["pc"],
                    "instruction": item["instruction"],
                    "offset": item["offset"],
                    "field": RAW_SETUP_FIELDS[offset],
                    "representation": "raw_usb_wire",
                    "description": item["description"],
                }
            )
    return refs


def build_report() -> dict[str, Any]:
    blob = STOCK.read_bytes()
    if hashlib.sha256(blob).hexdigest() != STOCK_SHA256:
        raise ValueError("SETUP evidence differs from the pinned stock ELF")
    sections, _ = properties(blob)
    checks = []
    for address, value in LITERALS.items():
        raw = section_bytes(blob, sections, address, 4)
        if raw != value.to_bytes(4, "big"):
            raise ValueError(f"SETUP literal differs at {address:#x}")
        checks.append(dict(status="present", address=hex(address), bytes=raw.hex(), meaning="original literal/initializer"))
    for address, (encoded, meaning) in BYTE_ANCHORS.items():
        raw = bytes.fromhex(encoded)
        if section_bytes(blob, sections, address, len(raw)) != raw:
            raise ValueError(f"SETUP instruction differs at {address:#x}")
        checks.append(dict(status="present", address=hex(address), bytes=encoded, meaning=meaning))
    ingress = section_bytes(blob, sections, 0x1000935B, 0x1000941D - 0x1000935B)
    if hashlib.sha256(ingress).hexdigest() != INGRESS_SHA256:
        raise ValueError("SETUP admission/conversion body differs")
    stock_refs = collect_stock_setup_refs()
    marker_refs = collect_marker_setup_refs()
    handshake = load_json(HANDSHAKE_JSON)
    stock_offsets = sorted({item["offset"] for item in stock_refs}, key=lambda x: int(x, 16))
    marker_offsets = sorted({item["offset"] for item in marker_refs}, key=lambda x: int(x, 16))
    admission = dict(owner_mask="0xc0000000", owner_value="0x80000000",
                     rx_mask="0x30000000", rx_value="0x00000000")
    if not (handshake["setup_descriptor_pointer_register"] == "0xb3000210"
            and handshake["out0_data_descriptor_pointer_register"] == "0xb3000214"
            and handshake["setup_admission"] == admission):
        raise ValueError("authored handshake contract disagrees with original SETUP evidence")

    return {
        "summary": "Original-byte SETUP storage/admission and separate raw-wire/post-conversion field views.",
        "status": "pass",
        "stock_elf_sha256": STOCK_SHA256,
        "original_byte_checks": checks,
        "ingress_code_sha256": INGRESS_SHA256,
        "execution_evidence": "analysis/usb-path/setup-ingress.json",
        "setup_packet_base_candidate": f"0x{SETUP_BASE:08x}",
        "setup_record_initial": "0x90021340",
        "setup_packet_record_pointer_global": "0x1001bbc0",
        "setup_descriptor_pointer_register": "0xb3000210",
        "out0_data_descriptor_pointer_register": "0xb3000214",
        "out0_data_descriptor_initial": "0x90022bc0",
        "setup_admission": admission,
        "raw_wire_fields": RAW_SETUP_FIELDS,
        "stock_post_conversion_fields": STOCK_SETUP_FIELDS,
        "stock_descriptor_branch_offsets_seen": stock_offsets,
        "open_marker_offsets_read": marker_offsets,
        "stock_setup_refs": stock_refs,
        "open_marker_setup_refs": marker_refs,
        "classification": {
            "direct_setup_buffer": (
                "Original initialization submits the SETUP record from global 0x1001bbc0 to OUT0 SUBPTR. "
                "The file-backed global is 0x90021340; request bytes are at record+8. Admission later "
                "reads status through SUBPTR but independently reloads the global for request fields. "
                "Pointer correspondence and stable ownership therefore need an explicit adapter contract."
            ),
            "descriptor_distinction": (
                "SETUP uses SUBPTR 0xb3000210 and requires owner 2 plus RX status 0. "
                "DESPTR 0xb3000214 belongs to the separate ordinary OUT0 data/status descriptor. "
                "The high status bits denote descriptor ownership, not an event signature."
            ),
            "field_representation": (
                "Raw USB wValue/wIndex/wLength are little-endian pairs. Original 0x10009399..0x1000940b "
                "reverses wIndex and wLength in place before the listed stock dispatch reads. "
                "It preserves wValue bytes. The open marker reads raw bytes; its labels remain wire order. "
                "TinyUSB dcd_event_setup_received needs the original eight wire bytes, not the stock converted record."
            ),
            "open_marker_choice": (
                "The current USB marker draft uses the direct 0x90021348 setup-buffer candidate and records "
                "bmRequestType, bRequest, wValue, and wLength before any USB writes."
            ),
            "remaining_live_unknown": (
                "Static analysis narrows the address, but cannot prove that the same RAM slot is populated after "
                "our uploaded firmware starts, or which controller gate sequence is live on real hardware."
            ),
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 USB Setup Source Model",
        "",
        "This is an offline model. It does not contact the printer.",
        "",
        "## Key Result",
        "",
        f"- file-backed initial request-byte address: `{report['setup_packet_base_candidate']}`",
        f"- stock descriptor branch reads offsets: `{', '.join(report['stock_descriptor_branch_offsets_seen'])}`",
        f"- open marker draft reads offsets: `{', '.join(report['open_marker_offsets_read'])}`",
        f"- SETUP descriptor pointer register (SUBPTR): `{report['setup_descriptor_pointer_register']}`",
        f"- ordinary OUT0 descriptor pointer register (DESPTR): `{report['out0_data_descriptor_pointer_register']}`",
        "",
        report["classification"]["direct_setup_buffer"],
        "",
        report["classification"]["field_representation"],
        "",
        "## Stock Firmware Setup Reads",
        "",
        "| PC | Address | Offset | Field | Instruction |",
        "|---:|---:|---:|---|---|",
    ]
    for item in report["stock_setup_refs"]:
        lines.append(
            f"| `{item['pc']}` | `{item['address']}` | `{item['offset']}` | {item['field']} | `{item['instruction']}` |"
        )
    lines.extend(
        [
            "",
            "## Open Marker Draft Reads",
            "",
            "| PC | Offset | Field | Instruction |",
            "|---:|---:|---|---|",
        ]
    )
    for item in report["open_marker_setup_refs"]:
        lines.append(f"| `{item['pc']}` | `{item['offset']}` | {item['field']} | `{item['instruction']}` |")

    lines.extend(
        [
            "",
            "## Descriptor Admission Boundary",
            "",
            f"- owner mask/value: `{report['setup_admission']['owner_mask']}` / `{report['setup_admission']['owner_value']}`",
            f"- RX mask/value: `{report['setup_admission']['rx_mask']}` / `{report['setup_admission']['rx_value']}`",
            "",
            report["classification"]["descriptor_distinction"],
            "",
            "Original literals, initialization stores and the full admission/conversion body are byte-gated. "
            "The separate `setup-ingress.json` execution report checks supplied records in RAM; this generator does not execute hardware or reproduce a USB lifecycle.",
            "",
            "## Practical Meaning",
            "",
            report["classification"]["open_marker_choice"],
            "",
            report["classification"]["remaining_live_unknown"],
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    OUT_MD.write_text(render_markdown(report) + "\n")
    print(f"stock_offsets={len(report['stock_descriptor_branch_offsets_seen'])} marker_offsets={len(report['open_marker_offsets_read'])}")
    print(OUT_MD)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
