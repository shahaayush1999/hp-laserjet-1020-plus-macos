#!/usr/bin/env python3
"""Model the HP 1020 USB interrupt task's event-flag producer path."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
ELF_PATH = ROOT_DIR / "analysis/sihp1020.elf"
SOURCE = ROOT_DIR / "analysis/tasks/task-decompiled/10008208_hp1020_task_entry_10008208.c"
OUT_JSON = ROOT_DIR / "analysis/usb-path/usb-interrupt-events.json"
OUT_MD = ROOT_DIR / "analysis/usb-path/usb-interrupt-events.md"
STOCK_SHA256 = "2111560068db47ceca21fa550db4c7c34f5595b5a5d137ae4a19631e40e3601d"
UDC_HEADER = ROOT_DIR / "analysis/usb-path/controller-reference/linux-v6.12/amd5536udc.h"
UDC_HEADER_SHA256 = "8dbf2ebffe7de042bdfea1c5e4e0d7e7ca334cb821fbfaa1cf9ccfeeae302648"

LITERAL_CELLS = {
    "irq_status": 0x10005DE4,
    "irq_pending_lanes": 0x10005DE8,
    "usb_global_status": 0x10005DEC,
    "device_config_register": 0x10005DF4,
    "masked_lane_word": 0x10005E00,
    "lane_bank0_base": 0x10005E04,
    "lane_bank1_base": 0x10005E08,
    "pending_transfer_list": 0x10005E10,
    "transfer_state": 0x10005E1C,
    "usb_event_flags": 0x10005E18,
    "out0_control_register": 0x10005E24,
    "bulk_descriptor_pointer_global": 0x10005E2C,
    "descriptor_owner_mask": 0x10005E30,
    "descriptor_owner_done": 0x10005E34,
    "bulk_available_size_word": 0x10005E38,
    "bulk_source_offset_word": 0x10005E3C,
    "bulk_next_offset_word": 0x10005E40,
    "bulk_buffer_base_word": 0x10005E44,
    "bulk_suppress_copy_byte": 0x10005E48,
    "bulk_remaining_request_word": 0x10005E4C,
    "bulk_threshold_word": 0x10005E50,
    "bulk_next_pointer_word": 0x10005E54,
    "bulk_destination_offset_word": 0x10005E5C,
}
CORRECTED_VALUES = {
    "irq_pending_lanes": 0xB3000414, "masked_lane_word": 0xB3000418,
    "device_config_register": 0xB3000400, "lane_bank0_base": 0xB3000004,
    "lane_bank1_base": 0xB3000204, "usb_event_flags": 0x10021318,
    "out0_control_register": 0xB3000200, "bulk_descriptor_pointer_global": 0x1001BC48,
    "descriptor_owner_mask": 0xC0000000, "descriptor_owner_done": 0x80000000,
}
BYTE_ANCHORS = {
    0x10008219: ("8880", "l32i.n a8,a8,0: sample EPINT pending word"),
    0x1000821D: ("9810", "s32i.n a8,a1,0: preserve sampled pending word"),
    0x1000837E: ("c030", "movi.n a3,0: start IN bank"),
    0x10008380: ("c021", "movi.n a2,1: event-bit source"),
    0x10008382: ("d430", "mov.n a4,a3: event-bit bank offset starts zero"),
    0x1000838D: ("8a80", "l32i.n a10,a8,0: read endpoint mask"),
    0x1000838F: ("8e10", "l32i.n a14,a1,0: reload sampled EPINT"),
    0x1000839B: ("9e90", "s32i.n a14,a9,0: acknowledge sampled EPINT before lane reads"),
    0x100083C9: ("19f68e", "l32r a9,0x10005e04: IN status base"),
    0x100083E0: ("19f68a", "l32r a9,0x10005e08: OUT status base"),
    0x100083E3: ("0b5811", "slli a8,a5,5: lane stride 32 bytes"),
    0x100083EB: ("8670", "l32i.n a6,a7,0: sample lane status once"),
    0x100083ED: ("282a00", "movi a8,0x200: HE acknowledgement mask"),
    0x100083F0: ("786004", "bnone a6,a8,0x100083f8: HE absent skips its store only"),
    0x100083F6: ("9870", "s32i.n a8,a7,0: HE status acknowledgement"),
    0x100083F8: ("280a80", "movi a8,128: BNA acknowledgement mask"),
    0x100083FB: ("786005", "bnone a6,a8,0x10008404: BNA absent skips its store only"),
    0x10008401: ("287600", "s32i a8,a7,0: BNA status acknowledgement"),
    0x10008404: ("c480", "movi.n a8,64: IN status mask"),
    0x1000840C: ("9870", "s32i.n a8,a7,0: IN status acknowledgement"),
    0x10008439: ("c380", "movi.n a8,48: OUT type mask"),
    0x1000843B: ("086801", "and a8,a6,a8: retain sampled OUT status bits"),
    0x10008443: ("287600", "s32i a8,a7,0: OUT type status acknowledgement"),
    0x10008446: ("284a00", "movi a8,0x400: TDC acknowledgement mask"),
    0x10008449: ("78606a", "bnone a6,a8,0x100084b7: no TDC still reaches OUT service"),
    0x1000844F: ("9870", "s32i.n a8,a7,0: TDC status acknowledgement"),
    0x10008459: ("69724c", "bnei a7,2,0x100084a9: IN1 is the special list path"),
    0x100084A9: ("1af65b", "l32r a10,0x10005e18: first wake event object"),
    0x100084AC: ("db70", "mov.n a11,a7: first wake uses lane event bit"),
    0x100084B4: ("583e3d", "call8 0x10017dac: TDC-associated wake before OUT processing"),
    0x100084B7: ("683102", "beqi a3,1,0x100084bd: OUT service path"),
    0x100084C8: ("685102", "beqi a5,1,0x100084ce: OUT1 special receive processing"),
    0x100084CB: ("6001e1", "j 0x100086b0: other OUT lanes still wake"),
    0x100084D4: ("6481d8", "beqz a8,0x100086b0: inactive bulk path still wakes"),
    0x100084D7: ("18f653", "l32r a8,0x10005e24: OUT0 control base"),
    0x100084DA: ("0b3911", "slli a9,a3,5: OUT bank value 1 selects control+0x20"),
    0x100084DD: ("2a0a80", "movi a10,128: SNAK control request mask"),
    0x100084E0: ("a899", "add.n a9,a9,a8: OUT1 control address"),
    0x100084EA: ("0a8802", "or a8,a8,a10: add SNAK request"),
    0x100084F3: ("289600", "s32i a8,a9,0: SNAK request, not EPSTS acknowledgement"),
    0x100084F9: ("18f64c", "l32r a8,0x10005e2c: bulk descriptor global"),
    0x100084FC: ("8b80", "l32i.n a11,a8,0: bulk descriptor pointer"),
    0x100086AD: ("580011", "call8 0x100086f4: rearm on applicable path before common OUT wake"),
    0x100086B0: ("1af5da", "l32r a10,0x10005e18: common OUT wake object"),
    0x100086B3: ("a54b", "add.n a11,a4,a5: bank offset plus lane"),
    0x100086B5: ("00b104", "ssl a11: select event-bit position"),
    0x100086B8: ("002b1a", "sll a11,a2: event bit"),
    0x100086C0: ("583dba", "call8 0x10017dac: common OUT wake"),
    0x100086DB: ("244c10", "addi a4,a4,16: OUT event offset 16"),
    0x100086DE: ("233c01", "addi a3,a3,1: advance bank"),
}


@dataclass(frozen=True)
class ElfImage:
    data: bytes
    load_segments: list[tuple[int, int, int]]

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


def require_contains(text: str, needle: str) -> dict[str, str]:
    return {
        "needle": needle,
        "status": "present" if needle in text else "missing",
        "evidence": str(SOURCE.relative_to(ROOT_DIR)),
    }


def build_report(elf_path: Path) -> dict[str, Any]:
    elf = ElfImage.load(elf_path)
    if hashlib.sha256(elf.data).hexdigest() != STOCK_SHA256:
        raise ValueError("interrupt evidence differs from the pinned stock ELF")
    byte_checks = []
    required = {LITERAL_CELLS[name]: (value.to_bytes(4, "big").hex(), name)
                for name, value in CORRECTED_VALUES.items()}
    required.update(BYTE_ANCHORS)
    required[0x1001BC48] = ("90021370", "file-backed initial bulk descriptor pointer")
    for address, (encoded, meaning) in required.items():
        raw = bytes.fromhex(encoded)
        if elf.read_bytes(address, len(raw)) != raw:
            raise ValueError(f"interrupt evidence differs at {address:#x}")
        byte_checks.append(dict(status="present", address=hex(address), bytes=encoded, meaning=meaning))
    header = UDC_HEADER.read_bytes()
    if hashlib.sha256(header).hexdigest() != UDC_HEADER_SHA256:
        raise ValueError("pinned controller-family header changed")
    definitions = {name: int(value, 0) for name, value in re.findall(
        r"^#define\s+(UDC_\w+)\s+(0x[0-9a-fA-F]+|[0-9]+)\s*(?:/\*.*)?$", header.decode(), re.M)}
    for name, value in (("UDC_EPCTL_SNAK", 7), ("UDC_EPCTL_CNAK", 8),
                        ("UDC_EPSTS_ADDR", 4), ("UDC_EPSTS_HE", 9), ("UDC_EPSTS_BNA", 7),
                        ("UDC_EPSTS_TDC", 10), ("UDC_EPINT_IN_OFS", 0), ("UDC_EPINT_OUT_OFS", 16)):
        if definitions[name] != value:
            raise ValueError(f"controller-family field differs: {name}")
    source = SOURCE.read_text(errors="replace")
    constants = {name: elf.read_u32(addr) for name, addr in LITERAL_CELLS.items()}
    checks = [
        require_contains(source, "uVar7 = *DAT_10005de4"),
        require_contains(source, "uVar12 = *DAT_10005de8"),
        require_contains(source, "uVar13 = *DAT_10005e00"),
        require_contains(source, "puVar10 = (uint *)(uVar8 * 0x20 + iVar11)"),
        require_contains(source, "if ((uVar9 & 0x400) != 0)"),
        require_contains(source, "FUN_10017dac(PTR_DAT_10005e18,iVar11,0)"),
        require_contains(source, "if ((uVar8 == 1) && (*PTR_DAT_10005e20 != '\\0'))"),
        require_contains(source, "*(uint *)(DAT_10005e24 + 0x20) = *(uint *)(DAT_10005e24 + 0x20) | 0x80"),
        require_contains(source, "*(uint *)PTR_DAT_10005e38 = *(int *)PTR_DAT_10005e38 + uVar9"),
        require_contains(source, "FUN_100086f4(*(undefined4 *)PTR_DAT_10005e40)"),
        require_contains(source, "FUN_10017dac(PTR_DAT_10005e18,1 << 0x20 - (0x20 - (uVar6 + uVar8 & 0x1f)),0)"),
    ]
    fail_count = sum(check["status"] != "present" for check in checks)
    return {
        "summary": "Static model of the USB interrupt task that feeds the endpoint-0 event flags.",
        "status": "pass" if fail_count == 0 else "fail",
        "source_function": "0x10008208 hp1020_usb_interrupt_task_candidate",
        "stock_elf_sha256": STOCK_SHA256,
        "original_byte_checks": byte_checks,
        "controller_reference": {"header": str(UDC_HEADER.relative_to(ROOT_DIR)),
                                 "sha256": UDC_HEADER_SHA256,
                                 "limit": "Family names interpret original command intent; no live controller timing, DMA completion or quiescence is established."},
        "constants": {name: fmt32(value) for name, value in constants.items()},
        "event_scan": {
            "pending_word": fmt32(constants["irq_pending_lanes"]),
            "mask_word": fmt32(constants["masked_lane_word"]),
            "lane_banks": [
                {
                    "bank_index": 0,
                    "direction": "IN",
                    "lane_base": fmt32(constants["lane_bank0_base"]),
                    "event_bits": "0x00000001..0x00008000",
                },
                {
                    "bank_index": 1,
                    "direction": "OUT",
                    "lane_base": fmt32(constants["lane_bank1_base"]),
                    "event_bits": "0x00010000..0x80000000",
                },
            ],
            "lane_stride": "0x20",
            "per_lane_status_bits": ["0x200", "0x80", "0x40", "0x30", "0x400"],
            "tdc_status_bit": "0x400",
            "wake_hints_may_repeat": True,
            "wake_without_tdc_possible": True,
            "wake_is_successful_completion": False,
            "acknowledgement_order": {
                "pending_sample_pc": "0x10008219",
                "pending_ack_pc": "0x1000839b",
                "lane_status_sample_pc": "0x100083eb",
                "lane_status_acknowledgements": [
                    {"pc": "0x100083f6", "mask": "0x200", "family_name": "HE"},
                    {"pc": "0x10008401", "mask": "0x80", "family_name": "BNA"},
                    {"pc": "0x1000840c", "mask": "0x40", "family_name": "IN"},
                    {"pc": "0x10008443", "mask": "0x30", "family_name": "latched OUT type bits"},
                    {"pc": "0x1000844f", "mask": "0x400", "family_name": "TDC"},
                ],
                "limit": "Conditional stores use the sampled lane word. HE/BNA acknowledgement alone does not suppress later wake paths. IRQ code is statically checked, never executed by this generator.",
            },
            "bulk_receive_lane": {
                "bank_index": 1,
                "lane_index": 1,
                "event_bit": "0x00020000",
                "lane_status_register": fmt32(constants["lane_bank1_base"] + 0x20),
                "lane_control_register": fmt32(constants["out0_control_register"] + 0x20),
                "control_snak_mask": "0x80",
                "status_ack_masks": ["0x200", "0x80", "0x40", "0x30", "0x400"],
                "descriptor_pointer_global": fmt32(constants["bulk_descriptor_pointer_global"]),
                "descriptor_initial": fmt32(elf.read_u32(constants["bulk_descriptor_pointer_global"])),
                "guard": "additional receive processing: bank 1 lane 1 and bulk_done_byte != 0; common OUT wake does not require this guard",
            },
            "bulk_buffer_updates": {
                "available_size_word": fmt32(constants["bulk_available_size_word"]),
                "source_offset_word": fmt32(constants["bulk_source_offset_word"]),
                "next_offset_word": fmt32(constants["bulk_next_offset_word"]),
                "buffer_base_word": fmt32(constants["bulk_buffer_base_word"]),
                "suppress_copy_byte": fmt32(constants["bulk_suppress_copy_byte"]),
                "remaining_request_word": fmt32(constants["bulk_remaining_request_word"]),
                "threshold_word": fmt32(constants["bulk_threshold_word"]),
                "next_pointer_word": fmt32(constants["bulk_next_pointer_word"]),
                "destination_offset_word": fmt32(constants["bulk_destination_offset_word"]),
            },
        },
        "event_flag_outputs": [
            {
                "condition": "per-lane status bit 0x400 and event bit != 0x2",
                "pc": "0x100084b4",
                "call": "event_flags_set(0x10021318, event_bit, 0)",
                "meaning": "TDC-associated task wake before OUT processing; not a successful-transfer or ownership assertion",
            },
            {
                "condition": "bank 1 transfer-service branch",
                "pc": "0x100086c0",
                "call": "event_flags_set(0x10021318, event_bit, 0)",
                "meaning": "common OUT task wake, including paths with no TDC or receive processing; may repeat the earlier lane wake",
            },
        ],
        "special_cases": [
            "event bit 0x2 has a pending-transfer-list path instead of the direct completion event set",
            "bank 1 lane 1 processes the bulk descriptor global 0x1001bc48, initially 0x90021370; 0x90022bc0 instead belongs to ordinary OUT0",
            "bank 1 lane 1 is bulk OUT: event bit 0x00020000, EPSTS 0xb3000224, EPCTL 0xb3000220",
            "USB2Thread separately waits on event bit 0x00010000",
            "control-IN data stage waits on event bit 0x00000001",
        ],
        "open_firmware_implication": [
            "Separate EPSTS acknowledgements at 0xb3000224 from SNAK control requests at 0xb3000220; the masks are not interchangeable.",
            "The first TDC-associated wake at 0x100084b4 precedes OUT processing. On applicable bulk paths, counter updates and rearm at 0x100086ad precede the later common OUT wake at 0x100086c0.",
            "A TinyUSB DCD must validate descriptor identity, ownership, count and errors, then forward at most one completion per original transfer. Stock event flags are wake hints that can coalesce or repeat.",
            "No IRQ execution, cache/DMA behavior, hardware ownership transition, abort completion or physical quiescence is established. Existing hardware access permissions are unchanged.",
        ],
        "checks": checks,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 USB Interrupt Event Model",
        "",
        "This is an offline model of the interrupt-side producer for USB event flags. It does not contact the printer.",
        "",
        "## Key Result",
        "",
        "- USB interrupt task `0x10008208` scans two groups of 16 event lanes.",
        "- Each lane uses a `0x20`-byte hardware/status stride.",
        "- Per-lane TDC status `0x400` can issue one wake; the OUT path can issue another with or without TDC.",
        "- These event flags request another software check. They do not establish successful completion, buffer reuse or quiescence.",
        "- Exact stock byte anchors and the pinned family header distinguish status acknowledgement from endpoint control requests. No IRQ or hardware path executes here.",
        "",
        "## Resolved Constants",
        "",
        "| Name | Value |",
        "|---|---:|",
    ]
    for name, value in report["constants"].items():
        lines.append(f"| `{name}` | `{value}` |")

    lines.extend(
        [
            "",
            "## Event Scan",
            "",
            f"- pending word: `{report['event_scan']['pending_word']}`",
            f"- mask word: `{report['event_scan']['mask_word']}`",
            f"- lane stride: `{report['event_scan']['lane_stride']}`",
            f"- per-lane status bits: {', '.join(f'`{bit}`' for bit in report['event_scan']['per_lane_status_bits'])}",
            f"- TDC status bit: `{report['event_scan']['tdc_status_bit']}`",
            "- sampled EPINT is acknowledged at `0x1000839b` before lane status is sampled at `0x100083eb`",
            "",
            "| Bank | Lane Base | Event Bits |",
            "|---:|---:|---|",
        ]
    )
    for bank in report["event_scan"]["lane_banks"]:
        lines.append(f"| `{bank['bank_index']}` | `{bank['lane_base']}` | `{bank['event_bits']}` |")

    bulk_lane = report["event_scan"]["bulk_receive_lane"]
    buffer_updates = report["event_scan"]["bulk_buffer_updates"]
    lines.extend(
        [
            "",
            "## Bulk Receive Lane",
            "",
            f"- bank/lane: `{bulk_lane['bank_index']}` / `{bulk_lane['lane_index']}`",
            f"- event bit: `{bulk_lane['event_bit']}`",
            f"- lane status register: `{bulk_lane['lane_status_register']}`",
            f"- lane control register: `{bulk_lane['lane_control_register']}`; SNAK request mask `{bulk_lane['control_snak_mask']}`",
            f"- status acknowledgement masks at the status register: {', '.join(f'`{bit}`' for bit in bulk_lane['status_ack_masks'])}",
            f"- bulk descriptor global/initial pointer: `{bulk_lane['descriptor_pointer_global']}` / `{bulk_lane['descriptor_initial']}`",
            f"- guard: {bulk_lane['guard']}",
            "",
            "Bulk buffer fields updated by this branch:",
            "",
            "| Field | Address |",
            "|---|---:|",
        ]
    )
    for name, value in buffer_updates.items():
        lines.append(f"| `{name}` | `{value}` |")

    lines.extend(["", "## Event Flag Outputs", "", "| Condition | Call | Meaning |", "|---|---|---|"])
    for item in report["event_flag_outputs"]:
        lines.append(f"| {item['condition']} | `{item['call']}` | {item['meaning']} |")

    lines.extend(["", "## Special Cases", ""])
    for item in report["special_cases"]:
        lines.append(f"- {item}")

    lines.extend(["", "## Open-Firmware Meaning", ""])
    for item in report["open_firmware_implication"]:
        lines.append(f"- {item}")

    lines.extend(["", "## Original Byte Checks", "", "| Address | Bytes | Meaning |", "|---:|---|---|"])
    for item in report["original_byte_checks"]:
        lines.append(f"| `{item['address']}` | `{item['bytes']}` | {item['meaning']} |")

    lines.extend(["", "## Evidence Checks", "", f"- status: `{report['status']}`", "", "| Status | Needle |", "|---|---|"])
    for check in report["checks"]:
        needle = check["needle"].replace("|", "\\|")
        lines.append(f"| `{check['status']}` | `{needle}` |")
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
