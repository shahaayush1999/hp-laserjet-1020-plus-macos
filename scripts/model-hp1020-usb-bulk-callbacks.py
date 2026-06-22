#!/usr/bin/env python3
"""Model the stock USB bulk receive callbacks exported from Ghidra."""

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
ELF_PATH = ROOT_DIR / "analysis/sihp1020.elf"
SOURCE_DIR = ROOT_DIR / "analysis/usb-path/bulk-callbacks-decompiled"
GHIDRA_REPORT = ROOT_DIR / "analysis/usb-path/usb-bulk-callbacks.md"
OUT_JSON = ROOT_DIR / "analysis/usb-path/usb-bulk-callbacks-model.json"
OUT_MD = ROOT_DIR / "analysis/usb-path/usb-bulk-callbacks-model.md"


SOURCES = {
    "prepare": SOURCE_DIR / "1000807c_hp1020_usb_transfer_prepare_callback_candidate.c",
    "callback_a": SOURCE_DIR / "100080f0_hp1020_usb_transfer_callback_a_candidate.c",
    "callback_b": SOURCE_DIR / "100081f4_hp1020_usb_transfer_callback_b_candidate.c",
    "bulk_rx_read": SOURCE_DIR / "100087b8_hp1020_usb_bulk_rx_callback_a_candidate.c",
    "bulk_rx_complete": SOURCE_DIR / "10008bac_hp1020_usb_bulk_rx_callback_b_candidate.c",
}


LITERALS = {
    "usb_status_register": 0x10005E00,
    "pending_transfer_list": 0x10005E10,
    "bulk_completion_state": 0x10005E14,
    "completion_event_flags": 0x10005E18,
    "bulk_done_byte": 0x10005E20,
    "bulk_destination_alias": 0x10005E34,
    "bulk_available_size_word": 0x10005E38,
    "bulk_source_offset_word": 0x10005E3C,
    "bulk_rearm_word": 0x10005E40,
    "bulk_source_base_word": 0x10005E44,
    "bulk_suppress_copy_byte": 0x10005E48,
    "bulk_remaining_request_word": 0x10005E4C,
    "bulk_threshold_word": 0x10005E50,
    "bulk_next_pointer_word": 0x10005E54,
    "bulk_destination_offset_word": 0x10005E5C,
    "usb_setup_status_register": 0x10005E68,
    "usb_setup_status_mask": 0x10005E6C,
    "usb_endpoint_ack_register": 0x10005E70,
    "bulk_event_bit": 0x10005E74,
    "bulk_rearm_flag_byte": 0x10005E78,
    "bulk_completion_lock": 0x10005E8C,
}


class ElfImage:
    def __init__(self, data: bytes, load_segments: list[tuple[int, int, int]]) -> None:
        self.data = data
        self.load_segments = load_segments

    @classmethod
    def load(cls, path: Path) -> "ElfImage":
        data = path.read_bytes()
        if data[:4] != b"\x7fELF" or data[5] != 2:
            raise ValueError(f"{path} is not a big-endian ELF")
        phoff = struct.unpack(">I", data[28:32])[0]
        phentsize = struct.unpack(">H", data[42:44])[0]
        phnum = struct.unpack(">H", data[44:46])[0]
        load_segments = []
        for index in range(phnum):
            off = phoff + index * phentsize
            p_type, p_offset, p_vaddr, _p_paddr, p_filesz, _p_memsz, _p_flags, _p_align = struct.unpack(
                ">IIIIIIII", data[off : off + 32]
            )
            if p_type == 1:
                load_segments.append((p_offset, p_vaddr, p_filesz))
        return cls(data, load_segments)

    def read_u32(self, addr: int) -> int:
        for p_offset, p_vaddr, p_filesz in self.load_segments:
            if p_vaddr <= addr <= p_vaddr + p_filesz - 4:
                off = p_offset + (addr - p_vaddr)
                return struct.unpack(">I", self.data[off : off + 4])[0]
        raise ValueError(f"address 0x{addr:08x} is not file-backed")


def fmt32(value: int) -> str:
    return f"0x{value:08x}"


def contains(source: str, needle: str, evidence: Path, name: str) -> dict[str, str]:
    return {
        "name": name,
        "status": "present" if needle in source else "missing",
        "needle": needle,
        "evidence": str(evidence.relative_to(ROOT_DIR)),
    }


def build_report(elf_path: Path) -> dict[str, Any]:
    elf = ElfImage.load(elf_path)
    constants = {name: fmt32(elf.read_u32(addr)) for name, addr in LITERALS.items()}
    sources = {name: path.read_text(errors="replace") for name, path in SOURCES.items()}
    ghidra_report = GHIDRA_REPORT.read_text(errors="replace")

    checks = [
        contains(ghidra_report, "100087b8` `hp1020_usb_bulk_rx_callback_a_candidate", GHIDRA_REPORT, "ghidra_export_has_read_callback"),
        contains(ghidra_report, "10008bac` `hp1020_usb_bulk_rx_callback_b_candidate", GHIDRA_REPORT, "ghidra_export_has_completion_callback"),
        contains(sources["prepare"], "FUN_10013140(*(int *)(param_1 + 0x24) + param_3 + 0x100,1)", SOURCES["prepare"], "prepare_callback_expands_cache"),
        contains(sources["callback_a"], "(**(code **)(param_1 + 4))", SOURCES["callback_a"], "callback_a_invokes_read_slot"),
        contains(sources["callback_a"], "FUN_10013140(0x400,1)", SOURCES["callback_a"], "callback_a_resets_to_0x400_buffer"),
        contains(sources["callback_b"], "(**(code **)(param_1 + 8))(param_2,param_3,200)", SOURCES["callback_b"], "callback_b_invokes_second_slot"),
        contains(sources["bulk_rx_read"], "FUN_10017d28(PTR_DAT_10005e18,DAT_10005e74,1,auStack_30,param_3)", SOURCES["bulk_rx_read"], "bulk_read_waits_on_event_bit"),
        contains(sources["bulk_rx_read"], "FUN_1001b38c(iVar4 + *(int *)PTR_DAT_10005e5c,*(int *)PTR_DAT_10005e44 + *(int *)puVar2", SOURCES["bulk_rx_read"], "bulk_read_copies_from_usb_buffer_to_destination"),
        contains(sources["bulk_rx_read"], "*DAT_10005e70 = *DAT_10005e70 | 0x100", SOURCES["bulk_rx_read"], "bulk_read_acks_endpoint_condition"),
        contains(sources["bulk_rx_read"], "FUN_100086f4(0)", SOURCES["bulk_rx_read"], "bulk_read_rearms_receive_path"),
        contains(sources["bulk_rx_complete"], "FUN_10013140(0x20,1)", SOURCES["bulk_rx_complete"], "completion_allocates_pending_node"),
        contains(sources["bulk_rx_complete"], "FUN_10013000(puVar1)", SOURCES["bulk_rx_complete"], "completion_appends_pending_transfer"),
        contains(sources["bulk_rx_complete"], "*DAT_10005e00 = *DAT_10005e00 & 0xfffffffd", SOURCES["bulk_rx_complete"], "completion_clears_usb_status_bit"),
        contains(sources["bulk_rx_complete"], "*(undefined4 *)puVar1 = 1", SOURCES["bulk_rx_complete"], "completion_sets_state_if_idle"),
    ]
    fail_count = sum(item["status"] != "present" for item in checks)

    return {
        "summary": "Static model of the stock USB bulk receive callback layer.",
        "status": "pass" if fail_count == 0 else "fail",
        "constants": constants,
        "callback_roles": [
            {
                "address": "0x100087b8",
                "name": "bulk_rx_read",
                "role": "blocking/read-style copy path",
                "meaning": "Copies bytes from the stock USB receive buffer into the caller destination, waits on event bit 0x20000 when empty, and re-arms/acks the endpoint path.",
            },
            {
                "address": "0x10008bac",
                "name": "bulk_rx_complete",
                "role": "completion/queue path",
                "meaning": "Allocates a 0x20 byte pending-transfer node, appends it to list 0x10022740, clears bit 1 in USB status register 0xb3000418, and marks completion state 0x100212d0 active when idle.",
            },
            {
                "address": "0x100080f0",
                "name": "transfer_callback_a",
                "role": "cached read wrapper",
                "meaning": "Serves cached bytes first, then calls the param_1+4 read slot with timeout policy.",
            },
            {
                "address": "0x100081f4",
                "name": "transfer_callback_b",
                "role": "secondary read wrapper",
                "meaning": "Calls the param_1+8 slot with a fixed timeout of 200.",
            },
        ],
        "open_firmware_implication": [
            "The parser does not need direct USB MMIO access if an open replacement provides the same read-callback behavior.",
            "The real USB work is a bulk OUT producer that fills a buffer, sets event bit 0x20000, tracks remaining bytes, and re-arms endpoint receive.",
            "The next open-code prototype target after endpoint-0 proof is a small bulk-receive ring plus parser callback shim, not the print engine.",
        ],
        "checks": checks,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 USB Bulk Callback Model",
        "",
        "This is an offline static model built from saved Ghidra decompilation. It does not contact the printer.",
        "",
        "## Key Result",
        "",
        "- `0x100087b8` is the stock read/copy callback: it drains USB receive bytes into the caller buffer and waits for more when empty.",
        "- `0x10008bac` is the stock completion/queue callback: it creates a pending-transfer node, clears a USB status bit, and wakes the receive state.",
        "- The ZjStream parser can be kept behind a read-callback shim; the missing open-code piece is the USB bulk OUT producer that feeds that shim.",
        "",
        "## Constants",
        "",
        "| Name | Value |",
        "|---|---:|",
    ]
    for name, value in report["constants"].items():
        lines.append(f"| `{name}` | `{value}` |")

    lines.extend(["", "## Callback Roles", "", "| Address | Name | Role | Meaning |", "|---:|---|---|---|"])
    for item in report["callback_roles"]:
        lines.append(f"| `{item['address']}` | `{item['name']}` | {item['role']} | {item['meaning']} |")

    lines.extend(["", "## Open-Firmware Meaning", ""])
    for item in report["open_firmware_implication"]:
        lines.append(f"- {item}")

    lines.extend(["", "## Evidence Checks", "", f"- status: `{report['status']}`", "", "| Status | Name | Evidence | Needle |", "|---|---|---|---|"])
    for check in report["checks"]:
        needle = check["needle"].replace("|", "\\|")
        lines.append(f"| `{check['status']}` | `{check['name']}` | `{check['evidence']}` | `{needle}` |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--elf", type=Path, default=ELF_PATH)
    parser.add_argument("--json-output", type=Path, default=OUT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=OUT_MD)
    args = parser.parse_args()

    report = build_report(args.elf)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.markdown_output.write_text(render_markdown(report) + "\n")
    print(f"status={report['status']} checks={len(report['checks'])}")
    print(args.markdown_output)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
