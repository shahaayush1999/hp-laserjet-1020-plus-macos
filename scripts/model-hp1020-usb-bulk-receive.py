#!/usr/bin/env python3
"""Model the HP 1020 stock USB bulk receive handoff to the ZjStream parser."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
ELF_PATH = ROOT_DIR / "analysis/sihp1020.elf"
USB2_SOURCE = ROOT_DIR / "analysis/usb-path/decompiled-neighbors/10008ff0_hp1020_usb2_thread.c"
REGISTER_SOURCE = ROOT_DIR / "analysis/usb-path/decompiled-neighbors/10007c00_hp1020_usb_register_transfer_candidate.c"
ALLOC_SOURCE = ROOT_DIR / "analysis/usb-path/decompiled-neighbors/10008034_FUN_10008034.c"
PARSER_SOURCE = ROOT_DIR / "analysis/zjs-parser-boundary/decompiled/10009d34_hp1020_zjs_parser_entry_candidate.c"
OUT_JSON = ROOT_DIR / "analysis/usb-path/usb-bulk-receive-model.json"
OUT_MD = ROOT_DIR / "analysis/usb-path/usb-bulk-receive-model.md"
STOCK_SHA256 = "2111560068db47ceca21fa550db4c7c34f5595b5a5d137ae4a19631e40e3601d"
UDC_HEADER = ROOT_DIR / "analysis/usb-path/controller-reference/linux-v6.12/amd5536udc.h"
UDC_HEADER_SHA256 = "8dbf2ebffe7de042bdfea1c5e4e0d7e7ca334cb821fbfaa1cf9ccfeeae302648"


LITERALS = {
    "transfer_token_shift_word": 0x10005D98,
    "transfer_ring_index": 0x10005D9C,
    "transfer_ring_base": 0x10005DA0,
    "transfer_prepare_callback": 0x10005DD0,
    "transfer_callback_a": 0x10005DD4,
    "transfer_callback_b": 0x10005DD8,
    "pending_transfer_list": 0x10005E10,
    "completion_event_flags": 0x10005E18,
    "transfer_state": 0x10005E1C,
    "descriptor_pool_a": 0x10005E2C,
    "bulk_rx_size_word": 0x10005E38,
    "bulk_rx_token_word": 0x10005E44,
    "endpoint_config_word": 0x10005E50,
    "bulk_rx_done_flag": 0x10005E64,
    "descriptor_pool_b": 0x10005E98,
    "registered_callback_a": 0x10005EFC,
    "registered_callback_b": 0x10005F00,
    "bulk_rx_mask_word": 0x10005F04,
    "out1_max_packet_register": 0x10005F08,
    "usb2thread_event_bit": 0x10005F20,
    "usb2thread_control_block": 0x10005FC0,
    "usb2thread_name": 0x10005FC4,
    "usb2thread_entry": 0x10005FC8,
    "usb2thread_stack_start": 0x10005FCC,
    "usb_saved_out1_nak_word": 0x10005FD0,
    "usb_saved_out0_nak_word": 0x10005FD4,
    "usb_pause_delay_argument": 0x10005FD8,
    "parser_entry": 0x10005FDC,
    "zjs_magic": 0x10005FE0,
}

# These words are adjacent literal-pool entries. Original loads and their
# separate consumers establish the meanings; adjacency is not a structure.
CORRECTED_VALUES = {
    "out1_max_packet_register": 0xB300022C,
    "usb2thread_control_block": 0x10021598,
    "usb2thread_name": 0x10003530,
    "usb2thread_entry": 0x10008FF0,
    "usb2thread_stack_start": 0x10022768,
    "usb_saved_out1_nak_word": 0x10021588,
    "usb_saved_out0_nak_word": 0x10021384,
    "usb_pause_delay_argument": 200000,
    "parser_entry": 0x10009D34,
}
BYTE_ANCHORS = {
    0x100099F2: ("1af173", "l32r a10,0x10005fc0: thread control-block argument"),
    0x100099F7: ("1bf173", "l32r a11,0x10005fc4: thread name argument"),
    0x100099FA: ("1cf173", "l32r a12,0x10005fc8: thread entry argument"),
    0x100099FD: ("1ef173", "l32r a14,0x10005fcc: thread stack argument"),
    0x10009A02: ("2f4a00", "movi a15,0x400: thread stack size"),
    0x10009A08: ("583a1a", "call8 0x10018274: thread creation call"),
    0x10009B23: ("18f12e", "l32r a8,0x10005fdc: separate parser-entry literal"),
    0x10009B26: ("1af12e", "l32r a10,0x10005fe0: separate parser magic literal"),
    0x10009B29: ("9810", "s32i.n a8,a1,0: parser entry in registration record word zero"),
    0x10009B3E: ("da10", "mov.n a10,a1: pass parser registration record"),
    0x10009B45: ("5bf854", "call8 0x10007c98: parser registration call"),
    0x10009A1D: ("1cf16c", "l32r a12,0x10005fd0: saved OUT1 NAK destination"),
    0x10009A28: ("1af112", "l32r a10,0x10005e70: OUT1 control address"),
    0x10009A2B: ("1bf0fe", "l32r a11,0x10005e24: OUT0 control address"),
    0x10009A31: ("88a0", "l32i.n a8,a10,0: read OUT1 control"),
    0x10009A33: ("c4d0", "movi.n a13,64: NAK bit mask"),
    0x10009A38: ("89b0", "l32i.n a9,a11,0: read OUT0 control"),
    0x10009A3A: ("0d8801", "and a8,a8,a13: isolate OUT1 NAK"),
    0x10009A3D: ("98c0", "s32i.n a8,a12,0: save OUT1 NAK word"),
    0x10009A4F: ("1af161", "l32r a10,0x10005fd4: saved OUT0 NAK destination"),
    0x10009A57: ("0d9901", "and a9,a9,a13: isolate OUT0 NAK"),
    0x10009A5A: ("99a0", "s32i.n a9,a10,0: save OUT0 NAK word"),
    0x10009A5F: ("1af15e", "l32r a10,0x10005fd8: delay argument"),
    0x10009A6A: ("581f20", "call8 0x100116ec: delay-service call"),
    0x10009A85: ("12f152", "l32r a2,0x10005fd0: saved OUT1 NAK source"),
    0x10009A88: ("8220", "l32i.n a2,a2,0: read saved OUT1 NAK word"),
    0x10009A8A: ("cd22", "bnez.n a2,0x10009aa0: nonzero saved OUT1 word skips CNAK path"),
    0x10009AA0: ("12f14d", "l32r a2,0x10005fd4: saved OUT0 NAK source"),
    0x10009AA3: ("8220", "l32i.n a2,a2,0: read saved OUT0 NAK word"),
    0x10009AA5: ("cd21", "bnez.n a2,0x10009aba: nonzero saved OUT0 word skips CNAK path"),
    0x1000924E: ("1af32e", "l32r a10,0x10005f08: OUT1 max-packet register address"),
    0x10009262: ("18f2fb", "l32r a8,0x10005e50: packet-size global address"),
    0x10009268: ("8880", "l32i.n a8,a8,0: packet-size value"),
    0x1000926F: ("98a0", "s32i.n a8,a10,0: write packet-size value"),
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
            if p_vaddr <= addr <= p_vaddr + p_filesz - size:
                off = p_offset + (addr - p_vaddr)
                return self.data[off : off + size]
        raise ValueError(f"address 0x{addr:08x} is not file-backed")

    def read_u32(self, addr: int) -> int:
        return struct.unpack(">I", self.read_bytes(addr, 4))[0]


def fmt32(value: int) -> str:
    return f"0x{value:08x}"


def require_contains(source: str, needle: str, evidence: Path) -> dict[str, str]:
    return {
        "status": "present" if needle in source else "missing",
        "needle": needle,
        "evidence": str(evidence.relative_to(ROOT_DIR)),
    }


def build_report(elf_path: Path) -> dict[str, Any]:
    elf = ElfImage.load(elf_path)
    stock_sha256 = hashlib.sha256(elf.data).hexdigest()
    if stock_sha256 != STOCK_SHA256:
        raise ValueError("stock ELF differs from the pinned original-byte evidence")
    byte_checks = []

    def require_bytes(address: int, expected: bytes, meaning: str) -> None:
        actual = elf.read_bytes(address, len(expected))
        if actual != expected:
            raise ValueError(f"original bytes differ at {address:#x}: {meaning}")
        byte_checks.append({"status": "present", "address": fmt32(address),
                            "bytes": actual.hex(), "meaning": meaning})

    for name, value in CORRECTED_VALUES.items():
        require_bytes(LITERALS[name], value.to_bytes(4, "big"), name)
    for address, (encoded, meaning) in BYTE_ANCHORS.items():
        require_bytes(address, bytes.fromhex(encoded), meaning)
    require_bytes(0x10003530, b"USB2Thread\0", "actual thread-name string")
    require_bytes(0x10005E70, bytes.fromhex("b3000220"), "OUT1 control-address literal")
    require_bytes(0x10005E24, bytes.fromhex("b3000200"), "OUT0 control-address literal")
    header = UDC_HEADER.read_bytes()
    if hashlib.sha256(header).hexdigest() != UDC_HEADER_SHA256:
        raise ValueError("pinned controller-family header changed")
    definitions = {name: int(value, 0) for name, value in re.findall(
        r"^#define\s+(UDC_\w+)\s+(0x[0-9a-fA-F]+|[0-9]+)\s*(?:/\*.*)?$",
        header.decode("utf-8"), re.M)}
    if not (definitions["UDC_EPOUT_REGS_ADDR"] == 0x200
            and definitions["UDC_EP_MAX_PKT_SIZE_ADDR"] == 0x0C
            and definitions["UDC_EPCTL_NAK"] == 6):
        raise ValueError("controller-family fields differ from the selected mapping")
    constants = {name: elf.read_u32(addr) for name, addr in LITERALS.items()}
    usb2 = USB2_SOURCE.read_text(errors="replace")
    register = REGISTER_SOURCE.read_text(errors="replace")
    alloc = ALLOC_SOURCE.read_text(errors="replace")
    parser = PARSER_SOURCE.read_text(errors="replace")

    checks = [
        require_contains(usb2, "uStack_70 = 1;", USB2_SOURCE),
        require_contains(usb2, "puStack_68 = PTR_LAB_10005efc;", USB2_SOURCE),
        require_contains(usb2, "puStack_64 = PTR_LAB_10005f00;", USB2_SOURCE),
        require_contains(usb2, "uVar11 = hp1020_usb_register_transfer_candidate(&uStack_70);", USB2_SOURCE),
        require_contains(register, "puVar3 + iVar8 * 0x58", REGISTER_SOURCE),
        require_contains(register, "piVar6[1] = param_1[2];", REGISTER_SOURCE),
        require_contains(register, "piVar6[2] = param_1[3];", REGISTER_SOURCE),
        require_contains(register, "piVar6[0xb] = iVar5;", REGISTER_SOURCE),
        require_contains(alloc, "FUN_10013140(0x400,1)", ALLOC_SOURCE),
        require_contains(parser, "(**(code **)(param_1 + 0xc))", PARSER_SOURCE),
        require_contains(parser, "hp1020_queue_send_candidate(3,auStack_1d0)", PARSER_SOURCE),
    ]
    fail_count = sum(check["status"] != "present" for check in checks)
    return {
        "summary": "Static model of stock USB bulk receive registration and parser handoff.",
        "status": "pass" if fail_count == 0 else "fail",
        "stock_elf_sha256": stock_sha256,
        "original_byte_checks": byte_checks,
        "controller_reference": {
            "header": str(UDC_HEADER.relative_to(ROOT_DIR)),
            "sha256": UDC_HEADER_SHA256,
            "limit": "Family layout supports NAK/max-packet naming; it does not identify HP silicon or establish quiescence.",
        },
        "constants": {name: fmt32(value) for name, value in constants.items()},
        "independent_adjacent_literals": [
            {"address": fmt32(address), "name": name, "value": fmt32(constants[name])}
            for name, address in LITERALS.items() if 0x10005FC0 <= address <= 0x10005FE0
        ],
        "adjacent_literals_are_not_a_task_descriptor": True,
        "usb2thread_creation": {
            "call_site": "0x10009a08",
            "callee": "0x10018274",
            "control_block_literal": fmt32(LITERALS["usb2thread_control_block"]),
            "control_block": fmt32(constants["usb2thread_control_block"]),
            "name_literal": fmt32(LITERALS["usb2thread_name"]),
            "name_pointer": fmt32(constants["usb2thread_name"]),
            "name": "USB2Thread",
            "entry_literal": fmt32(LITERALS["usb2thread_entry"]),
            "entry": fmt32(constants["usb2thread_entry"]),
            "stack_start_literal": fmt32(LITERALS["usb2thread_stack_start"]),
            "stack_start": fmt32(constants["usb2thread_stack_start"]),
            "stack_bytes": 0x400,
            "interpretation": "Individually loaded creation arguments, not an inline task descriptor or parser registration.",
        },
        "transfer_record": {
            "ring_base": fmt32(constants["transfer_ring_base"]),
            "ring_index_word": fmt32(constants["transfer_ring_index"]),
            "record_stride": "0x58",
            "buffer_allocation": "0x400 bytes",
            "registered_param_words": [
                {"word": 0, "value": "0x00000001", "record_offset": "+0x2c", "meaning": "transfer kind/endpoint selector candidate"},
                {"word": 1, "value": "0x00000000", "record_offset": "+0x38", "meaning": "flags/timeout candidate"},
                {
                    "word": 2,
                    "value": fmt32(constants["registered_callback_a"]),
                    "record_offset": "+0x04",
                    "meaning": "registered callback/function pointer A",
                },
                {
                    "word": 3,
                    "value": fmt32(constants["registered_callback_b"]),
                    "record_offset": "+0x08",
                    "meaning": "registered callback/function pointer B",
                },
                {"word": 4, "value": "0x00000000", "record_offset": "+0x18", "meaning": "state/argument slot candidate"},
                {"word": 5, "value": "0x00000001", "record_offset": "+0x54", "meaning": "enable/ownership candidate"},
            ],
            "default_callbacks_from_allocator": {
                "+0x14": fmt32(constants["transfer_prepare_callback"]),
                "+0x0c": fmt32(constants["transfer_callback_a"]),
                "+0x10": fmt32(constants["transfer_callback_b"]),
            },
        },
        "parser_handoff": {
            "usb2thread_entry": fmt32(constants["usb2thread_entry"]),
            "parser_entry_literal": fmt32(LITERALS["parser_entry"]),
            "parser_entry": fmt32(constants["parser_entry"]),
            "parser_registration_function": "0x10009b20",
            "parser_registration_call": "0x10009b45",
            "parser_registration_callee": "0x10007c98",
            "zjs_magic": fmt32(constants["zjs_magic"]),
            "parser_reads_via_param_0x0c_callback": True,
            "parser_sends_jobmgr_queue": 3,
        },
        "open_firmware_implication": [
            "The stock path separates USB transfer registration from ZjStream parsing through a callback table passed as parser param_1.",
            "An open firmware can keep the host-side ZjStream parser model, but still needs a bulk OUT receiver that can present a blocking/read callback at param_1+0x0c.",
            "The immediate software target after endpoint-0 proof is not video hardware; it is a small bulk-receive/read-callback shim that feeds the already-modeled ZjStream chunk loop.",
        ],
        "checks": checks,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 USB Bulk Receive Model",
        "",
        "This is an offline static model. It does not contact the printer.",
        "",
        "## Key Result",
        "",
        "- USB2Thread registers a transfer record through `0x10007c00` using a `0x58` byte record stride.",
        "- The helper allocator seeds a `0x400` byte receive buffer.",
        "- USB2Thread creation loads separate control-block, name, entry and stack literals before calling `0x10018274`.",
        "- Parser entry `0x10009d34` is registered separately in `0x10009b20`; adjacent literals are not a task descriptor.",
        "- `0xb300022c` is the family-matched OUT1 max-packet register, not an endpoint acknowledgement register.",
        "- The parser consumes bytes through a callback at `param_1 + 0x0c`, then sends JobMgr queue `3` messages.",
        "",
        "## Constants",
        "",
        "| Name | Value |",
        "|---|---:|",
    ]
    for name, value in report["constants"].items():
        lines.append(f"| `{name}` | `{value}` |")

    creation = report["usb2thread_creation"]
    lines.extend([
        "", "## Thread Creation and Adjacent Literals", "",
        f"Original call `{creation['call_site']}` invokes `{creation['callee']}` with separately loaded values:",
        "", "| Argument | Literal | Value |", "|---|---|---|",
        f"| control block | `{creation['control_block_literal']}` | `{creation['control_block']}` |",
        f"| name | `{creation['name_literal']}` | `{creation['name_pointer']}` (`USB2Thread`) |",
        f"| entry | `{creation['entry_literal']}` | `{creation['entry']}` |",
        f"| stack start | `{creation['stack_start_literal']}` | `{creation['stack_start']}` |",
        "", f"The stack-size argument is `{creation['stack_bytes']:#x}` bytes.", "",
        "The following `0x10005fd0/0x10005fd4` literals point to saved OUT1/OUT0 NAK words, "
        "and `0x10005fd8` supplies delay argument 200000. The original pause helper writes the "
        "saved words; the restore helper tests them. They are not thread-name/descriptor fields, "
        "and their values do not acknowledge DMA cancellation or quiescence.",
    ])

    record = report["transfer_record"]
    lines.extend(
        [
            "",
            "## Transfer Record",
            "",
            f"- ring base: `{record['ring_base']}`",
            f"- ring index word: `{record['ring_index_word']}`",
            f"- record stride: `{record['record_stride']}`",
            f"- buffer allocation: `{record['buffer_allocation']}`",
            "",
            "| Param word | Value | Record offset | Meaning |",
            "|---:|---:|---:|---|",
        ]
    )
    for item in record["registered_param_words"]:
        lines.append(f"| `{item['word']}` | `{item['value']}` | `{item['record_offset']}` | {item['meaning']} |")

    handoff = report["parser_handoff"]
    lines.extend(
        [
            "",
            "## Parser Handoff",
            "",
            f"- USB2Thread entry: `{handoff['usb2thread_entry']}`",
            f"- independent parser-entry literal: `{handoff['parser_entry_literal']}`",
            f"- parser entry: `{handoff['parser_entry']}`",
            f"- parser registration: `{handoff['parser_registration_function']}`, call "
            f"`{handoff['parser_registration_call']}` to `{handoff['parser_registration_callee']}`",
            f"- ZjStream magic pointer: `{handoff['zjs_magic']}`",
            f"- parser read callback slot: `param_1 + 0x0c`",
            f"- parser output queue: `{handoff['parser_sends_jobmgr_queue']}`",
            "",
            "## Open-Firmware Meaning",
            "",
        ]
    )
    for item in report["open_firmware_implication"]:
        lines.append(f"- {item}")

    lines.extend(["", "## Evidence Checks", "", f"- status: `{report['status']}`", "", "| Status | Evidence | Needle |", "|---|---|---|"])
    for check in report["checks"]:
        needle = check["needle"].replace("|", "\\|")
        lines.append(f"| `{check['status']}` | `{check['evidence']}` | `{needle}` |")
    lines.extend(["", "## Original-byte Mapping Checks", "",
                  f"Stock ELF SHA256: `{report['stock_elf_sha256']}`.", "",
                  "| Address | Exact bytes | Meaning |", "|---|---|---|"])
    for check in report["original_byte_checks"]:
        lines.append(f"| `{check['address']}` | `{check['bytes']}` | {check['meaning']} |")
    lines.extend(["", report["controller_reference"]["limit"]])
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
