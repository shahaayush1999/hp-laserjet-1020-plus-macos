#!/usr/bin/env python3
"""Check speed-matched printer-class USB configuration descriptors in the probe."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    expected: str
    actual: str
    description: str


def check(name: str, passed: bool, expected: object, actual: object, description: str) -> Check:
    return Check(name, "pass" if passed else "fail", str(expected), str(actual), description)


def sections(path: Path) -> dict[str, dict[str, int]]:
    data = path.read_bytes()
    if data[:4] != b"\x7fELF" or data[4:6] != b"\x01\x02":
        raise SystemExit(f"expected ELF32 big-endian: {path}")
    shoff = int.from_bytes(data[32:36], "big")
    shentsize = int.from_bytes(data[46:48], "big")
    shnum = int.from_bytes(data[48:50], "big")
    shstrndx = int.from_bytes(data[50:52], "big")
    shstr = shoff + shstrndx * shentsize
    string_offset = int.from_bytes(data[shstr + 16 : shstr + 20], "big")
    string_size = int.from_bytes(data[shstr + 20 : shstr + 24], "big")
    names = data[string_offset : string_offset + string_size]
    result: dict[str, dict[str, int]] = {}
    for index in range(shnum):
        off = shoff + index * shentsize
        name_off = int.from_bytes(data[off : off + 4], "big")
        if name_off:
            end = names.index(0, name_off)
            name = names[name_off:end].decode("ascii")
        else:
            name = ""
        result[name] = {
            "address": int.from_bytes(data[off + 12 : off + 16], "big"),
            "offset": int.from_bytes(data[off + 16 : off + 20], "big"),
            "size": int.from_bytes(data[off + 20 : off + 24], "big"),
        }
    return result


def source_words(text: str) -> dict[str, int]:
    values: dict[str, int] = {}
    label: str | None = None
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if match := re.fullmatch(r"([A-Za-z0-9_]+):", line):
            label = match.group(1)
        elif label and (match := re.match(r"\.word\s+(0x[0-9a-fA-F]+|\d+)", line)):
            values[label] = int(match.group(1), 0)
            label = None
    return values


def max_packets(config: bytes) -> list[int]:
    packets: list[int] = []
    offset = 0
    while offset + 2 <= len(config):
        length = config[offset]
        if length == 0 or offset + length > len(config):
            break
        if config[offset + 1] == 0x05 and length >= 7:
            packets.append(int.from_bytes(config[offset + 4 : offset + 6], "little") & 0x7FF)
        offset += length
    return packets


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("elf", type=Path)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()

    table = sections(args.elf)
    section = table.get(".usb_standard_descriptors")
    if section is None:
        raise SystemExit("missing .usb_standard_descriptors")
    blob = args.elf.read_bytes()[section["offset"] : section["offset"] + section["size"]]
    high = blob[0x14:0x34]
    full = blob[0x34:0x54]
    source = args.source.read_text(encoding="utf-8")
    words = source_words(source)

    checks = [
        check("descriptor_section_address", section["address"] == 0x10003300, "0x10003300", f"0x{section['address']:08x}", "fixed local descriptor table address"),
        check("descriptor_section_size", section["size"] == 0x78, "0x78", f"0x{section['size']:x}", "device, two configurations, language, and manufacturer descriptors fit exactly"),
        check("high_speed_config_shape", high[:4] == b"\x09\x02\x20\x00" and len(high) == 0x20, "09 02 20 00 / 32 bytes", f"{high[:4].hex(' ')} / {len(high)} bytes", "high-speed configuration is complete"),
        check("full_speed_config_shape", full[:4] == b"\x09\x02\x20\x00" and len(full) == 0x20, "09 02 20 00 / 32 bytes", f"{full[:4].hex(' ')} / {len(full)} bytes", "full-speed configuration is complete"),
        check("high_speed_bulk_packets", max_packets(high) == [512, 512], "[512, 512]", max_packets(high), "both high-speed bulk endpoints advertise 512 bytes"),
        check("full_speed_bulk_packets", max_packets(full) == [64, 64], "[64, 64]", max_packets(full), "both full-speed bulk endpoints advertise 64 bytes"),
        check("high_speed_alias", words.get("hp1020_config_high_speed_descriptor_hw_ptr_90003314") == 0x90003314, "0x90003314", f"0x{words.get('hp1020_config_high_speed_descriptor_hw_ptr_90003314', -1) & 0xffffffff:08x}", "DMA alias matches high-speed descriptor"),
        check("full_speed_alias", words.get("hp1020_config_full_speed_descriptor_hw_ptr_90003334") == 0x90003334, "0x90003334", f"0x{words.get('hp1020_config_full_speed_descriptor_hw_ptr_90003334', -1) & 0xffffffff:08x}", "DMA alias matches full-speed descriptor"),
        check("speed_bit_branch", all(needle in source for needle in ("hp1020_usb_marker_select_config:", "l32r a2, hp1020_mmio_b3010000", "bnez a3, hp1020_usb_marker_select_full_speed_config")), "b3010000 bit 0 chooses full speed", "present" if "bnez a3, hp1020_usb_marker_select_full_speed_config" in source else "missing", "configuration response follows the same speed bit as bulk endpoint setup"),
    ]
    status = "pass" if all(item.status == "pass" for item in checks) else "fail"
    payload = {
        "status": status,
        "section": section,
        "high_speed_hex": high.hex(" "),
        "full_speed_hex": full.hex(" "),
        "checks": [asdict(item) for item in checks],
    }
    lines = [
        "# HP 1020 USB Bulk Configuration Descriptor Check",
        "",
        f"- status: `{status}`",
        f"- fail checks: `{sum(item.status == 'fail' for item in checks)}`",
        "",
        "| Check | Expected | Actual | Status | Description |",
        "|---|---|---|---|---|",
    ]
    for item in checks:
        lines.append(f"| `{item.name}` | `{item.expected}` | `{item.actual}` | `{item.status}` | {item.description} |")
    lines.append("")
    report = "\n".join(lines)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
    else:
        print(report, end="")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
