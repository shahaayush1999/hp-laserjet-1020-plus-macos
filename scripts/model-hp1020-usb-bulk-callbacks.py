#!/usr/bin/env python3
"""Model stock USB receive and outgoing queue callbacks, with original-byte gates."""

from __future__ import annotations

import argparse
import hashlib
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
    "bulk_tx_queue": SOURCE_DIR / "10008bac_hp1020_usb_bulk_rx_callback_b_candidate.c",
}


LITERALS = {
    "usb_status_register": 0x10005E00,
    "pending_transfer_list": 0x10005E10,
    "bulk_tx_queue_state": 0x10005E14,
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
    "bulk_tx_queue_lock": 0x10005E8C,
}

STOCK_SHA256 = '2111560068db47ceca21fa550db4c7c34f5595b5a5d137ae4a19631e40e3601d'
# Literal, independently reviewed original ranges; all checks below are reads.
ORIGINAL_REGIONS = {
    'registration': (0x10007c00, 0x10007c5c, 'a95211a17b984e0982f03a4c3aa7571201a701918c975e81b08b02b25a46c89b'),
    'callback-vtable': (0x10008034, 0x1000807c, 'a3b5f788bc377c096152b8c9afc9756dad9c697c6b320a380d1e26d1e0cd09e1'),
    'send-wrapper': (0x100081f4, 0x10008208, '024738ef6ca3890068939fff7a2cbab6347a07679b8d7799469fc1565d7b6b91'),
    'in1-completed-list-drain': (0x10008b78, 0x10008bac, 'd5edb2ad7c4226debcf09c0d654cf6a8b102a5c857a454a6d9166baac5ca6e89'),
    'in1-submit-queue': (0x10008bac, 0x10008c24, '0a09bd940f8f77c5d4e0e5e8a9196ea94d5850ab412b65214873c91a20b3dbb8'),
    'startup-in1': (0x10008ff0, 0x100092f7, '541ae837b4b4c2867cafe53d2bc5dfdcdf61a5e944dd94e0d833784400ee7308'),
    'pjl-send': (0x1000cd44, 0x1000cd62, '892a453a06d26c3d5bb30b08041efe4edae314b6c3ec469f0687832b117e2cfc'),
    'cache-helper-call-boundary-only': (0x100173c8, 0x100173e6, '8acdf14c93008e303306a9eb7b53bb1a9d2fecfb2487c08acffb06defcc5a825'),
    'stock-config-hs': (0x100034b0, 0x100034d0, '5936c209497f97eba7032963007abc3b5d23c4e252463a53750d1f6130872ca0'),
    'stock-config-fs': (0x100034d0, 0x100034f0, 'b398ac7ccdf9da9b70542c7e47f51ecb0e669a967a584bdfa786c5c2481de5d9'),
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

    def read_bytes(self, addr: int, size: int) -> bytes:
        for p_offset, p_vaddr, p_filesz in self.load_segments:
            if p_vaddr <= addr and addr + size <= p_vaddr + p_filesz:
                off = p_offset + (addr - p_vaddr)
                return self.data[off:off + size]
        raise ValueError(f"address 0x{addr:08x}+{size} is not file-backed")

    def read_u32(self, addr: int) -> int:
        return struct.unpack(">I", self.read_bytes(addr, 4))[0]


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
    digest = hashlib.sha256(elf.data).hexdigest()
    original_checks = [{"name": "original_stock_elf", "status": "present" if digest == STOCK_SHA256 else "missing",
        "sha256": digest, "expected_sha256": STOCK_SHA256}]
    for name, (begin, end, expected) in ORIGINAL_REGIONS.items():
        actual = hashlib.sha256(elf.read_bytes(begin, end-begin)).hexdigest()
        original_checks.append({"name": name, "begin": fmt32(begin), "end_exclusive": fmt32(end),
            "sha256": actual, "expected_sha256": expected, "status": "present" if actual == expected else "missing"})
    for name, address, expected in (("registered_send", 0x10005f00, 0x10008bac),
                                  ("send_wrapper", 0x10005dd8, 0x100081f4)):
        actual = elf.read_u32(address)
        original_checks.append({"name": name, "address": fmt32(address), "value": fmt32(actual),
            "expected_value": fmt32(expected), "status": "present" if actual == expected else "missing"})
    constants = {name: fmt32(elf.read_u32(addr)) for name, addr in LITERALS.items()}
    sources = {name: path.read_text(errors="replace") for name, path in SOURCES.items()}
    ghidra_report = GHIDRA_REPORT.read_text(errors="replace")

    checks = [
        contains(ghidra_report, "100087b8` `hp1020_usb_bulk_rx_callback_a_candidate", GHIDRA_REPORT, "ghidra_export_has_read_callback"),
        contains(ghidra_report, "10008bac` `hp1020_usb_bulk_rx_callback_b_candidate", GHIDRA_REPORT, "ghidra_export_has_historically_rx_named_send_callback"),
        contains(sources["prepare"], "FUN_10013140(*(int *)(param_1 + 0x24) + param_3 + 0x100,1)", SOURCES["prepare"], "prepare_callback_expands_cache"),
        contains(sources["callback_a"], "(**(code **)(param_1 + 4))", SOURCES["callback_a"], "callback_a_invokes_read_slot"),
        contains(sources["callback_a"], "FUN_10013140(0x400,1)", SOURCES["callback_a"], "callback_a_resets_to_0x400_buffer"),
        contains(sources["callback_b"], "(**(code **)(param_1 + 8))(param_2,param_3,200)", SOURCES["callback_b"], "callback_b_invokes_second_slot"),
        contains(sources["bulk_rx_read"], "FUN_10017d28(PTR_DAT_10005e18,DAT_10005e74,1,auStack_30,param_3)", SOURCES["bulk_rx_read"], "bulk_read_waits_on_event_bit"),
        contains(sources["bulk_rx_read"], "FUN_1001b38c(iVar4 + *(int *)PTR_DAT_10005e5c,*(int *)PTR_DAT_10005e44 + *(int *)puVar2", SOURCES["bulk_rx_read"], "bulk_read_copies_from_usb_buffer_to_destination"),
        contains(sources["bulk_rx_read"], "*DAT_10005e70 = *DAT_10005e70 | 0x100", SOURCES["bulk_rx_read"], "bulk_read_acks_endpoint_condition"),
        contains(sources["bulk_rx_read"], "FUN_100086f4(0)", SOURCES["bulk_rx_read"], "bulk_read_rearms_receive_path"),
        contains(sources["bulk_tx_queue"], "FUN_10013140(0x20,1)", SOURCES["bulk_tx_queue"], "send_allocates_pending_node"),
        contains(sources["bulk_tx_queue"], "FUN_10013000(puVar1)", SOURCES["bulk_tx_queue"], "send_appends_pending_transfer"),
        contains(sources["bulk_tx_queue"], "*DAT_10005e00 = *DAT_10005e00 & 0xfffffffd", SOURCES["bulk_tx_queue"], "send_unmasks_in1_interrupt"),
        contains(sources["bulk_tx_queue"], "*(undefined4 *)puVar1 = 1", SOURCES["bulk_tx_queue"], "send_sets_queue_state_if_idle"),
    ]
    fail_count = sum(item["status"] != "present" for item in checks + original_checks)

    return {
        "summary": "Static model of separate stock USB receive and outgoing send/queue callbacks.",
        "status": "pass" if fail_count == 0 else "fail",
        "constants": constants,
        "stock_elf_sha256": digest,
        "original_byte_checks": original_checks,
        "direction_correction": {
            "old_label": "bulk_rx_complete", "corrected_role": "bulk_tx_queue",
            "historical_export_names_preserved": True,
            "basis": "Startup registers 0x10008bac at record+8; 0x100081f4 forwards source/length/timeout there. The queue retains source/length and returns length; 0x10008b78 later frees done heads' original sources.",
            "limits": "Static original instructions only. No semaphore/cache/MMIO/queue/completion executed. Current PJL transport pointer selection and host receipt remain unproved.",
        },
        "callback_roles": [
            {
                "address": "0x100087b8",
                "name": "bulk_rx_read",
                "role": "blocking/read-style copy path",
                "meaning": "Copies bytes from the stock USB receive buffer into the caller destination, waits on event bit 0x20000 when empty, and re-arms/acks the endpoint path.",
            },
            {
                "address": "0x10008bac",
                "name": "bulk_tx_queue",
                "role": "outgoing send/queue acceptance",
                "meaning": "On the normal queuing path, calls the cache-writeback helper and retains the caller source pointer and requested length in a 0x20-byte queue node, appends to list 0x10022740 and unmasks IN1 via bit1 of 0xb3000418. Returns accepted length before transmission; later done-head cleanup frees the retained source.",
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
                "role": "send wrapper",
                "meaning": "Calls the registered outgoing slot at record+8 with source, length and timeout200; its return is queue acceptance, not host receipt.",
            },
        ],
        "open_firmware_implication": [
            "The parser does not need direct USB MMIO access if an open replacement provides the same read-callback behavior.",
            "Bulk OUT feeds parser input; bulk IN separately carries outgoing replies. The return channel cannot be inferred from receive completion.",
            "Reuse bounded open ownership and buffers rather than HP heap queues. Keep queue acceptance, source/DMA release, FIFO settlement and host receipt distinct.",
        ],
        "checks": checks,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 USB Bulk Callback Model",
        "",
        "This offline static model checks saved decompilation against pinned original byte ranges. Historical RX-like export names are retained; the second callback is an outgoing send queue. No function or device is executed.",
        "",
        "## Key Result",
        "",
        "- `0x100087b8` is the stock read/copy callback: it drains USB receive bytes into the caller buffer and waits for more when empty.",
        "- `0x10008bac` queues outgoing bytes and returns accepted length. It retains the source for later DMA/completion cleanup; it is not a receive-completion callback.",
        "- `0x100081f4` calls that outgoing slot with timeout200. Queue acceptance is distinct from DMA release, FIFO settlement and host-visible receipt.",
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

    lines.extend(["", "## Corrected Direction and Original Bytes", "",
        report["direction_correction"]["basis"], "", report["direction_correction"]["limits"], "",
        "| Check | Status |", "|---|---|"])
    for item in report["original_byte_checks"]:
        lines.append(f"| `{item['name']}` | `{item['status']}` |")
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
