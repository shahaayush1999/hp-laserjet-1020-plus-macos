#!/usr/bin/env python3
"""Model the likely USB setup-packet source for the HP 1020 endpoint-0 path."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
INTERNAL_BLOCKS = ROOT_DIR / "analysis/usb-path/internal-blocks.md"
HANDSHAKE_JSON = ROOT_DIR / "analysis/usb-path/endpoint0-handshake-contract.json"
MEMORY_SCAN_JSON = ROOT_DIR / "analysis/open-firmware-probes/usb-marker-draft/memory-boundary-scan.json"
OUT_JSON = ROOT_DIR / "analysis/usb-path/usb-setup-source.json"
OUT_MD = ROOT_DIR / "analysis/usb-path/usb-setup-source.md"

REF_RE = re.compile(r"- `(?P<pc>[0-9a-f]{8})` `(?P<insn>[^`]+)` refs=`(?P<ref>[0-9a-f]+)`/(?P<kind>[A-Z_]+)")

SETUP_BASE = 0x90021348
SETUP_END = SETUP_BASE + 8
SETUP_FIELDS = {
    0: "bmRequestType",
    1: "bRequest",
    2: "wValue low / descriptor index",
    3: "wValue high / descriptor type",
    4: "wIndex low",
    5: "wIndex high",
    6: "wLength low",
    7: "wLength high",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def collect_stock_setup_refs() -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for match in REF_RE.finditer(INTERNAL_BLOCKS.read_text()):
        ref = int(match.group("ref"), 16)
        if SETUP_BASE <= ref < SETUP_END:
            offset = ref - SETUP_BASE
            refs.append(
                {
                    "pc": f"0x{match.group('pc')}",
                    "instruction": match.group("insn"),
                    "address": f"0x{ref:08x}",
                    "offset": f"0x{offset:x}",
                    "field": SETUP_FIELDS[offset],
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
                    "field": SETUP_FIELDS[offset],
                    "description": item["description"],
                }
            )
    return refs


def build_report() -> dict[str, Any]:
    stock_refs = collect_stock_setup_refs()
    marker_refs = collect_marker_setup_refs()
    handshake = load_json(HANDSHAKE_JSON)
    stock_offsets = sorted({item["offset"] for item in stock_refs}, key=lambda x: int(x, 16))
    marker_offsets = sorted({item["offset"] for item in marker_refs}, key=lambda x: int(x, 16))

    return {
        "summary": "Static model of where endpoint-0 setup request bytes appear to come from.",
        "setup_packet_base_candidate": f"0x{SETUP_BASE:08x}",
        "stock_descriptor_branch_offsets_seen": stock_offsets,
        "open_marker_offsets_read": marker_offsets,
        "stock_setup_refs": stock_refs,
        "open_marker_setup_refs": marker_refs,
        "event_pointer_register": handshake["event_pointer_register"],
        "event_signature": handshake["event_signature"],
        "classification": {
            "direct_setup_buffer": (
                "The stock descriptor branch reads setup-like request fields from 0x90021348 + offset. "
                "The strongest direct evidence is descriptor index/type and wLength reads."
            ),
            "event_pointer_register": (
                "0xb3000214 is better treated as an event/envelope pointer. The stock code reads a pointer, "
                "then checks a high-bit event signature, rather than using it as the 8-byte setup packet itself."
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
        f"- likely direct setup-packet base: `{report['setup_packet_base_candidate']}`",
        f"- stock descriptor branch reads offsets: `{', '.join(report['stock_descriptor_branch_offsets_seen'])}`",
        f"- open marker draft reads offsets: `{', '.join(report['open_marker_offsets_read'])}`",
        f"- separate event/envelope pointer register: `{report['event_pointer_register']}`",
        "",
        "The vague blocker is now split in two: the direct setup-byte address is probably `0x90021348`, while live hardware still has to prove that this slot is populated after our uploaded firmware starts.",
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
            "## Event Pointer Boundary",
            "",
            f"- event pointer register: `{report['event_pointer_register']}`",
            f"- signature mask/value: `{report['event_signature']['mask']}` / `{report['event_signature']['value']}`",
            "",
            report["classification"]["event_pointer_register"],
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
