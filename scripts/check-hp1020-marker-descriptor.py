#!/usr/bin/env python3
"""Verify the USB marker descriptor bytes, length, and hardware pointer alias."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path


EXPECTED_TEXT = "HP1020 OPEN MARKER"


@dataclass(frozen=True)
class Check:
    name: str
    severity: str
    expected: str
    actual: str
    description: str


def string_descriptor(text: str) -> bytes:
    body = text.encode("utf-16le")
    return bytes([len(body) + 2, 3]) + body


def parse_elf_sections(path: Path) -> dict[str, dict[str, int]]:
    data = path.read_bytes()
    if data[:4] != b"\x7fELF" or data[4] != 1 or data[5] != 2:
        raise SystemExit(f"expected ELF32 big-endian: {path}")

    shoff = int.from_bytes(data[32:36], "big")
    shentsize = int.from_bytes(data[46:48], "big")
    shnum = int.from_bytes(data[48:50], "big")
    shstrndx = int.from_bytes(data[50:52], "big")
    shstr_off = shoff + shstrndx * shentsize
    string_offset = int.from_bytes(data[shstr_off + 16 : shstr_off + 20], "big")
    string_size = int.from_bytes(data[shstr_off + 20 : shstr_off + 24], "big")
    strings = data[string_offset : string_offset + string_size]

    def section_name(offset: int) -> str:
        end = strings.index(0, offset)
        return strings[offset:end].decode("ascii")

    sections: dict[str, dict[str, int]] = {}
    for index in range(shnum):
        off = shoff + index * shentsize
        name_offset = int.from_bytes(data[off : off + 4], "big")
        name = section_name(name_offset) if name_offset else ""
        sections[name] = {
            "addr": int.from_bytes(data[off + 12 : off + 16], "big"),
            "offset": int.from_bytes(data[off + 16 : off + 20], "big"),
            "size": int.from_bytes(data[off + 20 : off + 24], "big"),
        }
    return sections


def parse_source_constants(path: Path) -> dict[str, int]:
    constants: dict[str, int] = {}
    current_label = None
    label_re = re.compile(r"^(?P<label>[A-Za-z0-9_]+):$")
    word_re = re.compile(r"^\s*\.word\s+(?P<value>0x[0-9a-fA-F]+|\d+)")
    for raw_line in path.read_text().splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if match := label_re.match(line):
            current_label = match.group("label")
            continue
        if current_label and (match := word_re.match(line)):
            constants[current_label] = int(match.group("value"), 0)
            current_label = None
    return constants


def render_markdown(checks: list[Check], descriptor: bytes, section: dict[str, int]) -> str:
    fail_count = sum(1 for check in checks if check.severity == "fail")
    lines = [
        "# HP 1020 Marker Descriptor Check",
        "",
        f"- fail hits: `{fail_count}`",
        f"- descriptor vaddr: `0x{section['addr']:08x}`",
        f"- descriptor bytes: `{len(descriptor)}`",
        f"- descriptor hex: `{descriptor.hex(' ')}`",
        "",
        "| Severity | Check | Expected | Actual | Description |",
        "|---|---|---:|---:|---|",
    ]
    for check in checks:
        lines.append(
            f"| `{check.severity}` | `{check.name}` | `{check.expected}` | `{check.actual}` | {check.description} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("elf", type=Path)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()

    expected = string_descriptor(EXPECTED_TEXT)
    sections = parse_elf_sections(args.elf)
    section = sections.get(".usb_marker_descriptor")
    if not section:
        raise SystemExit("missing .usb_marker_descriptor section")

    data = args.elf.read_bytes()
    descriptor = data[section["offset"] : section["offset"] + section["size"]]
    constants = parse_source_constants(args.source)

    alias = section["addr"] | 0x80000000
    checks = [
        Check(
            "descriptor_bytes",
            "watch" if descriptor == expected else "fail",
            expected.hex(" "),
            descriptor.hex(" "),
            "embedded USB string descriptor must equal HP1020 OPEN MARKER",
        ),
        Check(
            "descriptor_size",
            "watch" if section["size"] == len(expected) else "fail",
            str(len(expected)),
            str(section["size"]),
            "section size must match descriptor length",
        ),
        Check(
            "length_constant",
            "watch" if constants.get("hp1020_marker_len_00000026") == len(expected) else "fail",
            f"0x{len(expected):08x}",
            f"0x{constants.get('hp1020_marker_len_00000026', -1) & 0xFFFFFFFF:08x}",
            "firmware length constant must match descriptor length",
        ),
        Check(
            "hardware_alias_pointer",
            "watch" if constants.get("hp1020_marker_descriptor_hw_ptr_90003200") == alias else "fail",
            f"0x{alias:08x}",
            f"0x{constants.get('hp1020_marker_descriptor_hw_ptr_90003200', -1) & 0xFFFFFFFF:08x}",
            "USB response pointer should use the stock 0x90000000 hardware alias convention",
        ),
    ]

    report = render_markdown(checks, descriptor, section)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report)
    else:
        print(report, end="")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(
                {
                    "descriptor_hex": descriptor.hex(" "),
                    "descriptor_text": EXPECTED_TEXT,
                    "section": section,
                    "checks": [check.__dict__ for check in checks],
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )

    return 1 if any(check.severity == "fail" for check in checks) else 0


if __name__ == "__main__":
    raise SystemExit(main())
