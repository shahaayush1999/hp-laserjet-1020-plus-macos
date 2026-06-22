#!/usr/bin/env python3
"""Model the HP 1020 USB interrupt task's event-flag producer path."""

from __future__ import annotations

import argparse
import json
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
ELF_PATH = ROOT_DIR / "analysis/sihp1020.elf"
SOURCE = ROOT_DIR / "analysis/tasks/task-decompiled/10008208_hp1020_task_entry_10008208.c"
OUT_JSON = ROOT_DIR / "analysis/usb-path/usb-interrupt-events.json"
OUT_MD = ROOT_DIR / "analysis/usb-path/usb-interrupt-events.md"

LITERAL_CELLS = {
    "irq_status": 0x10005DE4,
    "irq_pending_lanes": 0x10005DE8,
    "usb_global_status": 0x10005DEC,
    "control_setup_gate": 0x10005DF4,
    "masked_lane_word": 0x10005E00,
    "lane_bank0_base": 0x10005E04,
    "lane_bank1_base": 0x10005E08,
    "pending_transfer_list": 0x10005E10,
    "transfer_state": 0x10005E1C,
    "completion_event_flags": 0x10005E18,
    "event_ack_register": 0x10005E24,
    "event_signature_mask": 0x10005E30,
    "event_signature_value": 0x10005E34,
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

    def read_u32(self, addr: int) -> int:
        for p_offset, p_vaddr, p_filesz in self.load_segments:
            if p_vaddr <= addr <= p_vaddr + p_filesz - 4:
                off = p_offset + (addr - p_vaddr)
                return struct.unpack(">I", self.data[off : off + 4])[0]
        raise ValueError(f"address 0x{addr:08x} is not file-backed")


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
    source = SOURCE.read_text(errors="replace")
    constants = {name: elf.read_u32(addr) for name, addr in LITERAL_CELLS.items()}
    checks = [
        require_contains(source, "uVar7 = *DAT_10005de4"),
        require_contains(source, "uVar12 = *DAT_10005de8"),
        require_contains(source, "uVar13 = *DAT_10005e00"),
        require_contains(source, "puVar10 = (uint *)(uVar8 * 0x20 + iVar11)"),
        require_contains(source, "if ((uVar9 & 0x400) != 0)"),
        require_contains(source, "FUN_10017dac(PTR_DAT_10005e18,iVar11,0)"),
        require_contains(source, "FUN_10017dac(PTR_DAT_10005e18,1 << 0x20 - (0x20 - (uVar6 + uVar8 & 0x1f)),0)"),
    ]
    fail_count = sum(check["status"] != "present" for check in checks)
    return {
        "summary": "Static model of the USB interrupt task that feeds the endpoint-0 event flags.",
        "status": "pass" if fail_count == 0 else "fail",
        "source_function": "0x10008208 hp1020_usb_interrupt_task_candidate",
        "constants": {name: fmt32(value) for name, value in constants.items()},
        "event_scan": {
            "pending_word": fmt32(constants["irq_pending_lanes"]),
            "mask_word": fmt32(constants["masked_lane_word"]),
            "lane_banks": [
                {
                    "bank_index": 0,
                    "lane_base": fmt32(constants["lane_bank0_base"]),
                    "event_bits": "0x00000001..0x00008000",
                },
                {
                    "bank_index": 1,
                    "lane_base": fmt32(constants["lane_bank1_base"]),
                    "event_bits": "0x00010000..0x80000000",
                },
            ],
            "lane_stride": "0x20",
            "per_lane_status_bits": ["0x200", "0x80", "0x40", "0x30", "0x400"],
            "completion_status_bit": "0x400",
        },
        "event_flag_outputs": [
            {
                "condition": "per-lane status bit 0x400 and event bit != 0x2",
                "call": "event_flags_set(0x10021318, event_bit, 0)",
                "meaning": "normal completion wake for endpoint/control transfer lanes",
            },
            {
                "condition": "bank 1 transfer-service branch",
                "call": "event_flags_set(0x10021318, event_bit, 0)",
                "meaning": "main USB2Thread/service wake after transfer-buffer processing",
            },
        ],
        "special_cases": [
            "event bit 0x2 has a pending-transfer-list path instead of the direct completion event set",
            "bank 1 lane 1 processes 0x90022bc0-style descriptor/event records before setting its event bit",
            "USB2Thread separately waits on event bit 0x00010000",
            "control-IN data stage waits on event bit 0x00000001",
        ],
        "open_firmware_implication": [
            "A future polling loop should start by watching the interrupt pending word and the per-lane 0x400 completion bit pattern.",
            "The static map identifies candidate registers but not the live transition order after a custom upload.",
            "This report supports a bounded hardware observation plan; it is not enough by itself to remove all ThreadX/event logic.",
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
        "- Per-lane status bit `0x400` is the strongest static completion signal feeding `0x10021318` event flags.",
        "- This narrows a future open polling loop to a concrete register/lane map, but live transition order still needs hardware evidence.",
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
            f"- completion status bit: `{report['event_scan']['completion_status_bit']}`",
            "",
            "| Bank | Lane Base | Event Bits |",
            "|---:|---:|---|",
        ]
    )
    for bank in report["event_scan"]["lane_banks"]:
        lines.append(f"| `{bank['bank_index']}` | `{bank['lane_base']}` | `{bank['event_bits']}` |")

    lines.extend(["", "## Event Flag Outputs", "", "| Condition | Call | Meaning |", "|---|---|---|"])
    for item in report["event_flag_outputs"]:
        lines.append(f"| {item['condition']} | `{item['call']}` | {item['meaning']} |")

    lines.extend(["", "## Special Cases", ""])
    for item in report["special_cases"]:
        lines.append(f"- {item}")

    lines.extend(["", "## Open-Firmware Meaning", ""])
    for item in report["open_firmware_implication"]:
        lines.append(f"- {item}")

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
