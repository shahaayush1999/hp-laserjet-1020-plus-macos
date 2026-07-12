#!/usr/bin/env python3
"""Verify the bulk-parser probe's writable USB counter string descriptor."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


EXPECTED_TEXT = "HP1020 B=00000000 D=00000000 C=00000000 E=00000000 U=00000000"
SECTION_NAME = ".usb_status_descriptor"
EXPECTED_ADDRESS = 0x10003400
EXPECTED_ALIAS = 0x90003400
COUNTER_OFFSETS = (0x14, 0x2A, 0x40, 0x56, 0x6C)


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    expected: str
    actual: str
    description: str


def descriptor_bytes() -> bytes:
    body = EXPECTED_TEXT.encode("utf-16le")
    return bytes((len(body) + 2, 0x03)) + body


def parse_sections(path: Path) -> dict[str, dict[str, int]]:
    data = path.read_bytes()
    if data[:4] != b"\x7fELF" or data[4:6] != b"\x01\x02":
        raise SystemExit(f"expected ELF32 big-endian: {path}")
    shoff = int.from_bytes(data[32:36], "big")
    shentsize = int.from_bytes(data[46:48], "big")
    shnum = int.from_bytes(data[48:50], "big")
    shstrndx = int.from_bytes(data[50:52], "big")
    shstr_header = shoff + shstrndx * shentsize
    str_offset = int.from_bytes(data[shstr_header + 16 : shstr_header + 20], "big")
    str_size = int.from_bytes(data[shstr_header + 20 : shstr_header + 24], "big")
    strings = data[str_offset : str_offset + str_size]

    sections: dict[str, dict[str, int]] = {}
    for index in range(shnum):
        off = shoff + index * shentsize
        name_offset = int.from_bytes(data[off : off + 4], "big")
        if name_offset:
            end = strings.index(0, name_offset)
            name = strings[name_offset:end].decode("ascii")
        else:
            name = ""
        sections[name] = {
            "flags": int.from_bytes(data[off + 8 : off + 12], "big"),
            "address": int.from_bytes(data[off + 12 : off + 16], "big"),
            "offset": int.from_bytes(data[off + 16 : off + 20], "big"),
            "size": int.from_bytes(data[off + 20 : off + 24], "big"),
        }
    return sections


def parse_words(source: str) -> dict[str, int]:
    words: dict[str, int] = {}
    label: str | None = None
    for raw in source.splitlines():
        line = raw.split("#", 1)[0].strip()
        if match := re.fullmatch(r"([A-Za-z0-9_]+):", line):
            label = match.group(1)
            continue
        if label and (match := re.match(r"\.word\s+(0x[0-9a-fA-F]+|\d+)", line)):
            words[label] = int(match.group(1), 0)
            label = None
    return words


def make_check(name: str, passed: bool, expected: object, actual: object, description: str) -> Check:
    return Check(name, "pass" if passed else "fail", str(expected), str(actual), description)


def render(checks: list[Check], section: dict[str, int], actual: bytes) -> str:
    failed = sum(check.status == "fail" for check in checks)
    lines = [
        "# HP 1020 USB Bulk Parser Status Descriptor Check",
        "",
        f"- status: `{'pass' if failed == 0 else 'fail'}`",
        f"- fail checks: `{failed}`",
        f"- descriptor address: `0x{section['address']:08x}`",
        f"- descriptor bytes: `{len(actual)}`",
        "",
        "| Check | Expected | Actual | Status | Description |",
        "|---|---|---|---|---|",
    ]
    for check in checks:
        lines.append(
            f"| `{check.name}` | `{check.expected}` | `{check.actual}` | `{check.status}` | {check.description} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("elf", type=Path)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()

    sections = parse_sections(args.elf)
    if SECTION_NAME not in sections:
        raise SystemExit(f"missing {SECTION_NAME}")
    section = sections[SECTION_NAME]
    elf_data = args.elf.read_bytes()
    actual = elf_data[section["offset"] : section["offset"] + section["size"]]
    expected = descriptor_bytes()
    source = args.source.read_text(encoding="utf-8")
    words = parse_words(source)

    calls = [f"write_hex_counter 0x{state:02x}, 0x{offset:02x}" for state, offset in zip((0x60, 0x64, 0x68, 0x6C, 0x70), COUNTER_OFFSETS)]
    checks = [
        make_check("descriptor_bytes", actual == expected, expected.hex(" "), actual.hex(" "), "ELF contains the exact counter template"),
        make_check("descriptor_address", section["address"] == EXPECTED_ADDRESS, f"0x{EXPECTED_ADDRESS:08x}", f"0x{section['address']:08x}", "local writable descriptor address is fixed"),
        make_check("descriptor_writable", bool(section["flags"] & 0x1), "SHF_WRITE", f"flags=0x{section['flags']:x}", "counter digits are patched before each product-string response"),
        make_check("length_constant", words.get("hp1020_marker_len_0000007c") == len(expected), f"0x{len(expected):x}", f"0x{words.get('hp1020_marker_len_0000007c', -1) & 0xffffffff:x}", "control response length matches the descriptor"),
        make_check("local_pointer", words.get("hp1020_status_descriptor_local_ptr_10003400") == EXPECTED_ADDRESS, f"0x{EXPECTED_ADDRESS:08x}", f"0x{words.get('hp1020_status_descriptor_local_ptr_10003400', -1) & 0xffffffff:08x}", "formatter patches the local RAM mapping"),
        make_check("hardware_alias", words.get("hp1020_status_descriptor_hw_ptr_90003400") == EXPECTED_ALIAS, f"0x{EXPECTED_ALIAS:08x}", f"0x{words.get('hp1020_status_descriptor_hw_ptr_90003400', -1) & 0xffffffff:08x}", "USB DMA reads the hardware alias"),
        make_check("counter_patch_calls", all(call in source for call in calls), "all five state/descriptor offsets", str([call for call in calls if call in source]), "B/D/C/E/U counters are rendered as eight hexadecimal digits"),
        make_check("product_selects_status_alias", "hp1020_usb_marker_select_product:" in source and "l32r a2, hp1020_status_descriptor_hw_ptr_90003400" in source, "dynamic status alias", "present" if "l32r a2, hp1020_status_descriptor_hw_ptr_90003400" in source else "missing", "GET_DESCRIPTOR product string exposes current counters"),
    ]

    report = render(checks, section, actual)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
    else:
        print(report, end="")
    payload = {
        "status": "pass" if all(check.status == "pass" for check in checks) else "fail",
        "descriptor_text": EXPECTED_TEXT,
        "descriptor_hex": actual.hex(" "),
        "section": section,
        "checks": [asdict(check) for check in checks],
    }
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
