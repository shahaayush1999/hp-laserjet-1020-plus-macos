#!/usr/bin/env python3
"""Model the stock USB bulk receive descriptor re-arm function."""

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
ELF_PATH = ROOT_DIR / "analysis/sihp1020.elf"
SOURCE = ROOT_DIR / "analysis/call-clusters/seed-decompiled/100086f4_FUN_100086f4.c"
OUT_JSON = ROOT_DIR / "analysis/usb-path/usb-bulk-rearm-model.json"
OUT_MD = ROOT_DIR / "analysis/usb-path/usb-bulk-rearm-model.md"


LITERALS = {
    "descriptor_pool_pointer_word": 0x10005E2C,
    "bulk_buffer_base_word": 0x10005E44,
    "next_aligned_pointer_word": 0x10005E54,
    "descriptor_mode_flag_byte": 0x10005E28,
    "descriptor_submit_register": 0x10005E60,
    "descriptor_busy_flag_byte": 0x10005E58,
    "bulk_done_byte": 0x10005E20,
    "bulk_rx_done_flag": 0x10005E64,
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


def contains(source: str, needle: str, name: str) -> dict[str, str]:
    return {
        "name": name,
        "status": "present" if needle in source else "missing",
        "needle": needle,
        "evidence": str(SOURCE.relative_to(ROOT_DIR)),
    }


def build_report(elf_path: Path) -> dict[str, Any]:
    elf = ElfImage.load(elf_path)
    constants = {name: fmt32(elf.read_u32(addr)) for name, addr in LITERALS.items()}
    descriptor_pool = elf.read_u32(elf.read_u32(LITERALS["descriptor_pool_pointer_word"]))
    buffer_base = elf.read_u32(elf.read_u32(LITERALS["bulk_buffer_base_word"]))
    source = SOURCE.read_text(errors="replace")

    checks = [
        contains(source, "uVar7 = *(uint *)PTR_DAT_10005e54", "reads_next_aligned_pointer_candidate"),
        contains(source, "(uVar7 == 0) || ((uVar7 & 0xf) != 0)", "falls_back_when_next_pointer_absent_or_unaligned"),
        contains(source, "param_1 = *(int *)PTR_DAT_10005e44 + param_1", "falls_back_to_buffer_base_plus_offset"),
        contains(source, "*(char *)(iVar6 + 8)", "writes_descriptor_address_bytes"),
        contains(source, "*PTR_DAT_10005e28 = uVar5", "writes_descriptor_mode_flag"),
        contains(source, "*piVar2 = iVar6", "submits_descriptor_pointer_to_mmio"),
        contains(source, "*(undefined1 *)(iVar6 + 0xc) = 0", "zeros_descriptor_tail_bytes"),
        contains(source, "*puVar4 = 8", "writes_descriptor_first_status_byte"),
        contains(source, "*puVar1 = 1", "sets_bulk_done_byte"),
        contains(source, "*puVar3 = 0", "clears_bulk_rx_done_flag"),
    ]
    fail_count = sum(item["status"] != "present" for item in checks)

    return {
        "summary": "Static model of stock USB bulk receive descriptor re-arm.",
        "status": "pass" if fail_count == 0 else "fail",
        "constants": {
            **constants,
            "descriptor_pool": fmt32(descriptor_pool),
            "bulk_buffer_base": fmt32(buffer_base),
        },
        "descriptor_layout": [
            {"offset": "+0x08..+0x0b", "meaning": "big-endian receive target pointer"},
            {"offset": "+0x0c..+0x0f", "meaning": "zeroed next-descriptor word; family interpretation is audited separately in controller-family.json"},
            {"offset": "status[0]", "meaning": "byte 8 is the high byte of status word 0x08000000, not an instruction opcode"},
            {"offset": "status[1..3]", "meaning": "zeroed after submit; the controller-family comparison interprets bit 27 as the last-descriptor flag"},
        ],
        "branch_model": [
            {
                "condition": "next pointer is zero or not 16-byte aligned",
                "target_pointer": "bulk buffer base + caller offset",
                "mode_flag": 0,
            },
            {
                "condition": "next pointer is non-zero and 16-byte aligned",
                "target_pointer": "next aligned pointer",
                "mode_flag": 1,
            },
        ],
        "open_firmware_implication": [
            "Bulk receive is descriptor-based, not just a raw write to the USB data FIFO.",
            "The open shim needs to write the receive target pointer into descriptor bytes +0x08..+0x0b, submit descriptor 0x90021370 through 0xb3000234, and reset the visible done flags.",
            "The stock path uses a 16-byte alignment decision for the next receive pointer; an open implementation should preserve that alignment rule until hardware behavior is proven otherwise.",
        ],
        "checks": checks,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 USB Bulk Re-Arm Model",
        "",
        "This is an offline static model. It does not contact the printer.",
        "",
        "## Key Result",
        "",
        "- Stock receive re-arm writes a receive target pointer into descriptor bytes `+0x08..+0x0b`.",
        "- It submits descriptor pool pointer `0x90021370` through MMIO register `0xb3000234`.",
        "- It sets the visible bulk-done byte and clears the bulk RX done flag after descriptor setup.",
        "",
        "## Constants",
        "",
        "| Name | Value |",
        "|---|---:|",
    ]
    for name, value in report["constants"].items():
        lines.append(f"| `{name}` | `{value}` |")

    lines.extend(["", "## Descriptor Layout", "", "| Field | Meaning |", "|---|---|"])
    for item in report["descriptor_layout"]:
        lines.append(f"| `{item['offset']}` | {item['meaning']} |")

    lines.extend(["", "## Branch Model", "", "| Condition | Target pointer | Mode flag |", "|---|---|---:|"])
    for item in report["branch_model"]:
        lines.append(f"| {item['condition']} | {item['target_pointer']} | `{item['mode_flag']}` |")

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
