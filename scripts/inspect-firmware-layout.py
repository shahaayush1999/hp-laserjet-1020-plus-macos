#!/usr/bin/env python3
"""Inspect and validate HP 1020 firmware upload/image/ELF layout."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


UEL = b"\x1b%-12345X"
PJL_ENTER_ACL = UEL + b"@PJL ENTER LANGUAGE=ACL\r\n"
ACL_MAGIC = bytes.fromhex("00 ac c0 de")
DATE_PREFIX_LEN = 8

EXPECTED_ELF = {
    "class": 1,
    "data": 2,
    "type": 2,
    "machine": 0xABC7,
    "entry": 0x100167A8,
    "program_header_count": 11,
    "section_header_count": 39,
}

EXPECTED_SECTIONS = {
    ".WindowVectors.text": {"addr": 0x10000000, "size": 0x180},
    ".sys_interface_table": {"addr": 0x10000370, "size": 0x12C},
    ".rodata": {"addr": 0x10003000, "size": 0x2C80},
    ".text": {"addr": 0x10005C80, "size": 0x15F0F},
    ".data": {"addr": 0x1001BB90, "size": 0x1AB0},
    ".bss": {"addr": 0x1001D640, "size": 0x17BA0},
    ".ResetVector.text": {"addr": 0x10100020, "size": 0x2E0},
}

EXPECTED_SYMBOLS = {
    "elf_entry": 0x100167A8,
    "reset_vector": 0x10100020,
    "sys_interface_table": 0x10000370,
    "threadx_queue_create_wrapper_candidate": 0x10017F18,
    "threadx_queue_receive_wrapper_candidate": 0x1001809C,
    "threadx_queue_send_wrapper_candidate": 0x100180DC,
    "threadx_thread_create_wrapper_candidate": 0x10018274,
    "queue_send_by_id_candidate": 0x10013668,
    "engine_thread_candidate": 0x100163B0,
    "video_thread_candidate": 0x10013C18,
    "print_mgr_thread_candidate": 0x1000F324,
}

SECTION_TYPE = {
    0: "NULL",
    1: "PROGBITS",
    2: "SYMTAB",
    3: "STRTAB",
    4: "RELA",
    8: "NOBITS",
    9: "REL",
}

PROGRAM_TYPE = {
    0: "NULL",
    1: "LOAD",
    2: "DYNAMIC",
    3: "INTERP",
    4: "NOTE",
}


class FirmwareError(ValueError):
    pass


@dataclass(frozen=True)
class LoadedFirmware:
    source_kind: str
    source_bytes: int
    image: bytes
    elf: bytes
    upload: dict[str, Any] | None


def u16(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 2], "big")


def u32(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 4], "big")


def cstr(table: bytes, offset: int) -> str:
    if offset < 0 or offset >= len(table):
        return f"<bad-name-offset-0x{offset:x}>"
    end = table.find(b"\x00", offset)
    if end == -1:
        end = len(table)
    return table[offset:end].decode("ascii", errors="replace")


def load_firmware(path: Path) -> LoadedFirmware:
    data = path.read_bytes()

    if data.startswith(PJL_ENTER_ACL):
        header_offset = len(PJL_ENTER_ACL)
        image_offset = header_offset + 8
        if len(data) < image_offset + DATE_PREFIX_LEN + 4 + len(UEL):
            raise FirmwareError("upload is too small to contain ACL header, image, and trailer")
        magic = data[header_offset : header_offset + 4]
        acl_elf_length = u32(data, header_offset + 4)
        trailer = data[-len(UEL) :]
        image = data[image_offset : -len(UEL)]
        upload = {
            "prefix_bytes": len(PJL_ENTER_ACL),
            "acl_magic": magic.hex(),
            "acl_elf_length": acl_elf_length,
            "image_offset": image_offset,
            "image_length": len(image),
            "trailer": trailer.hex(),
        }
        return LoadedFirmware("dl_upload", len(data), image, image_to_elf(image), upload)

    if data[:4] == b"\x7fELF":
        return LoadedFirmware("elf", len(data), b"20050309" + data, data, None)

    if len(data) >= DATE_PREFIX_LEN + 4 and data[DATE_PREFIX_LEN : DATE_PREFIX_LEN + 4] == b"\x7fELF":
        return LoadedFirmware("date_prefixed_image", len(data), data, data[DATE_PREFIX_LEN:], None)

    raise FirmwareError("input is not a .dl upload, date-prefixed .img, or raw ELF")


def image_to_elf(image: bytes) -> bytes:
    if len(image) < DATE_PREFIX_LEN + 4:
        raise FirmwareError("image is too small to contain date prefix plus ELF magic")
    if image[DATE_PREFIX_LEN : DATE_PREFIX_LEN + 4] != b"\x7fELF":
        raise FirmwareError("image does not contain ELF magic at offset 8")
    return image[DATE_PREFIX_LEN:]


def parse_elf(elf: bytes) -> dict[str, Any]:
    if len(elf) < 52:
        raise FirmwareError("ELF is too small to contain an ELF32 header")
    if elf[:4] != b"\x7fELF":
        raise FirmwareError("ELF magic missing")
    if elf[4] != 1:
        raise FirmwareError("expected ELFCLASS32")
    if elf[5] != 2:
        raise FirmwareError("expected big-endian ELF")

    phoff = u32(elf, 28)
    shoff = u32(elf, 32)
    phentsize = u16(elf, 42)
    phnum = u16(elf, 44)
    shentsize = u16(elf, 46)
    shnum = u16(elf, 48)
    shstrndx = u16(elf, 50)

    header = {
        "class": elf[4],
        "data": elf[5],
        "version": elf[6],
        "osabi": elf[7],
        "type": u16(elf, 16),
        "machine": u16(elf, 18),
        "entry": u32(elf, 24),
        "program_header_offset": phoff,
        "section_header_offset": shoff,
        "flags": u32(elf, 36),
        "elf_header_size": u16(elf, 40),
        "program_header_entry_size": phentsize,
        "program_header_count": phnum,
        "section_header_entry_size": shentsize,
        "section_header_count": shnum,
        "section_name_string_table_index": shstrndx,
    }

    if phoff + phentsize * phnum > len(elf):
        raise FirmwareError("program header table extends past end of ELF")
    if shoff + shentsize * shnum > len(elf):
        raise FirmwareError("section header table extends past end of ELF")

    program_headers = []
    for i in range(phnum):
        off = phoff + i * phentsize
        p_type = u32(elf, off)
        program_headers.append(
            {
                "index": i,
                "type": p_type,
                "type_name": PROGRAM_TYPE.get(p_type, f"0x{p_type:x}"),
                "offset": u32(elf, off + 4),
                "vaddr": u32(elf, off + 8),
                "paddr": u32(elf, off + 12),
                "filesz": u32(elf, off + 16),
                "memsz": u32(elf, off + 20),
                "flags": u32(elf, off + 24),
                "align": u32(elf, off + 28),
            }
        )

    raw_sections = []
    for i in range(shnum):
        off = shoff + i * shentsize
        raw_sections.append(
            {
                "index": i,
                "name_offset": u32(elf, off),
                "type": u32(elf, off + 4),
                "flags": u32(elf, off + 8),
                "addr": u32(elf, off + 12),
                "offset": u32(elf, off + 16),
                "size": u32(elf, off + 20),
                "link": u32(elf, off + 24),
                "info": u32(elf, off + 28),
                "addralign": u32(elf, off + 32),
                "entsize": u32(elf, off + 36),
            }
        )

    if shstrndx >= len(raw_sections):
        raise FirmwareError("section name string-table index is invalid")
    shstr = raw_sections[shstrndx]
    shstr_data = elf[shstr["offset"] : shstr["offset"] + shstr["size"]]

    sections = []
    for section in raw_sections:
        section = dict(section)
        section["name"] = cstr(shstr_data, section["name_offset"])
        section["type_name"] = SECTION_TYPE.get(section["type"], f"0x{section['type']:x}")
        section["flags_text"] = section_flags(section["flags"])
        sections.append(section)

    load_segments = [ph for ph in program_headers if ph["type"] == 1]
    alloc_sections = [s for s in sections if s["flags"] & 0x2]
    exec_sections = [s for s in sections if s["flags"] & 0x4]

    return {
        "header": header,
        "program_headers": program_headers,
        "sections": sections,
        "summary": {
            "elf_bytes": len(elf),
            "load_segment_file_bytes": sum(ph["filesz"] for ph in load_segments),
            "load_segment_memory_bytes": sum(ph["memsz"] for ph in load_segments),
            "alloc_section_bytes": sum(s["size"] for s in alloc_sections),
            "executable_section_bytes": sum(s["size"] for s in exec_sections),
        },
    }


def section_flags(flags: int) -> str:
    names = []
    if flags & 0x1:
        names.append("W")
    if flags & 0x2:
        names.append("A")
    if flags & 0x4:
        names.append("X")
    return "".join(names) or "-"


def addr_in_layout(addr: int, sections: list[dict[str, Any]]) -> str | None:
    for section in sections:
        start = section["addr"]
        end = start + section["size"]
        if section["size"] and start <= addr < end:
            return section["name"]
    return None


def validate(loaded: LoadedFirmware, elf_info: dict[str, Any]) -> tuple[list[str], list[str]]:
    failures = []
    warnings = []

    image = loaded.image
    if len(image) < DATE_PREFIX_LEN + 4:
        failures.append("image is too small")
    else:
        date_prefix = image[:DATE_PREFIX_LEN]
        if not date_prefix.isdigit():
            failures.append(f"date prefix is not 8 ASCII digits: {date_prefix!r}")
        if image[DATE_PREFIX_LEN : DATE_PREFIX_LEN + 4] != b"\x7fELF":
            failures.append("ELF magic is not at image offset 8")

    if loaded.upload is not None:
        if loaded.upload["acl_magic"] != ACL_MAGIC.hex():
            failures.append("ACL magic mismatch")
        if loaded.upload["acl_elf_length"] != len(loaded.elf):
            failures.append("ACL length does not equal embedded ELF length")
        if loaded.upload["image_length"] != len(loaded.image):
            failures.append("ACL image length mismatch")
        if loaded.upload["trailer"] != UEL.hex():
            failures.append("UEL trailer mismatch")

    header = elf_info["header"]
    for field, expected in EXPECTED_ELF.items():
        if header[field] != expected:
            failures.append(f"ELF {field} is 0x{header[field]:x}, expected 0x{expected:x}")

    sections_by_name = {section["name"]: section for section in elf_info["sections"]}
    for name, expected in EXPECTED_SECTIONS.items():
        section = sections_by_name.get(name)
        if section is None:
            failures.append(f"missing expected section {name}")
            continue
        if section["addr"] != expected["addr"]:
            failures.append(
                f"{name} address is 0x{section['addr']:08x}, expected 0x{expected['addr']:08x}"
            )
        if section["size"] != expected["size"]:
            failures.append(f"{name} size is 0x{section['size']:x}, expected 0x{expected['size']:x}")

    for name, addr in EXPECTED_SYMBOLS.items():
        section_name = addr_in_layout(addr, elf_info["sections"])
        if section_name is None:
            warnings.append(f"{name} 0x{addr:08x} is not inside any section")

    for ph in elf_info["program_headers"]:
        if ph["offset"] + ph["filesz"] > len(loaded.elf):
            failures.append(f"program header {ph['index']} extends past end of ELF")
        if ph["type"] == 1 and ph["filesz"] > ph["memsz"]:
            failures.append(f"LOAD program header {ph['index']} has filesz > memsz")

    return failures, warnings


def build_report(path: Path, loaded: LoadedFirmware, elf_info: dict[str, Any]) -> dict[str, Any]:
    failures, warnings = validate(loaded, elf_info)
    header = elf_info["header"]
    date_prefix = loaded.image[:DATE_PREFIX_LEN].decode("ascii", errors="replace")
    symbols = {
        name: {
            "addr": addr,
            "section": addr_in_layout(addr, elf_info["sections"]),
        }
        for name, addr in EXPECTED_SYMBOLS.items()
    }
    return {
        "input": str(path),
        "source_kind": loaded.source_kind,
        "source_bytes": loaded.source_bytes,
        "image_bytes": len(loaded.image),
        "date_prefix": date_prefix,
        "elf": {
            "header": header,
            "summary": elf_info["summary"],
            "program_headers": elf_info["program_headers"],
            "sections": elf_info["sections"],
        },
        "upload": loaded.upload,
        "expected_anchor_symbols": symbols,
        "validation": {
            "ok": not failures,
            "failures": failures,
            "warnings": warnings,
        },
    }


def hex32(value: int) -> str:
    return f"0x{value:08x}"


def render_markdown(report: dict[str, Any]) -> str:
    header = report["elf"]["header"]
    summary = report["elf"]["summary"]
    validation = report["validation"]
    lines = [
        "# Firmware Layout Report",
        "",
        "This is an offline structural check for HP LaserJet 1020/1020 Plus firmware blobs.",
        "It does not upload anything to the printer.",
        "",
        "## Result",
        "",
        f"- Input: `{report['input']}`",
        f"- Source kind: `{report['source_kind']}`",
        f"- Validation: `{'PASS' if validation['ok'] else 'FAIL'}`",
        f"- Source bytes: `{report['source_bytes']}`",
        f"- Date-prefixed image bytes: `{report['image_bytes']}`",
        f"- Raw ELF bytes: `{summary['elf_bytes']}`",
        f"- Date prefix: `{report['date_prefix']}`",
        "",
    ]

    if report["upload"] is not None:
        upload = report["upload"]
        lines.extend(
            [
                "## Upload Envelope",
                "",
                f"- PJL/ACL prefix bytes: `{upload['prefix_bytes']}`",
                f"- ACL magic: `{upload['acl_magic']}`",
                f"- ACL ELF length: `{upload['acl_elf_length']}`",
                f"- Embedded image offset: `{upload['image_offset']}`",
                f"- Embedded image length: `{upload['image_length']}`",
                f"- UEL trailer: `{upload['trailer']}`",
                "",
            ]
        )

    lines.extend(
        [
            "## ELF Header",
            "",
            f"- Class/data: `ELF32` / `big-endian`",
            f"- Type: `0x{header['type']:x}`",
            f"- Machine: `0x{header['machine']:x}`",
            f"- Entry point: `{hex32(header['entry'])}`",
            f"- Program headers: `{header['program_header_count']}`",
            f"- Section headers: `{header['section_header_count']}`",
            f"- LOAD segment file bytes: `{summary['load_segment_file_bytes']}`",
            f"- LOAD segment memory bytes: `{summary['load_segment_memory_bytes']}`",
            f"- Allocated section bytes: `{summary['alloc_section_bytes']}`",
            f"- Executable section bytes: `{summary['executable_section_bytes']}`",
            "",
            "## Critical Sections",
            "",
            "| Section | Address | Size | Flags |",
            "| --- | ---: | ---: | --- |",
        ]
    )

    sections_by_name = {section["name"]: section for section in report["elf"]["sections"]}
    for name in EXPECTED_SECTIONS:
        section = sections_by_name.get(name)
        if section is None:
            lines.append(f"| `{name}` | missing | missing | missing |")
            continue
        lines.append(
            f"| `{name}` | `{hex32(section['addr'])}` | `0x{section['size']:x}` | `{section['flags_text']}` |"
        )

    lines.extend(
        [
            "",
            "## Anchor Addresses",
            "",
            "| Name | Address | Section |",
            "| --- | ---: | --- |",
        ]
    )
    for name, item in report["expected_anchor_symbols"].items():
        section = item["section"] or "none"
        lines.append(f"| `{name}` | `{hex32(item['addr'])}` | `{section}` |")

    lines.extend(
        [
            "",
            "## Program Headers",
            "",
            "| # | Type | Offset | VAddr | File Size | Mem Size | Flags | Align |",
            "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for ph in report["elf"]["program_headers"]:
        lines.append(
            "| "
            f"{ph['index']} | `{ph['type_name']}` | `0x{ph['offset']:x}` | `{hex32(ph['vaddr'])}` | "
            f"`0x{ph['filesz']:x}` | `0x{ph['memsz']:x}` | `0x{ph['flags']:x}` | `0x{ph['align']:x}` |"
        )

    if validation["failures"]:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in validation["failures"])
    if validation["warnings"]:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in validation["warnings"])

    lines.extend(
        [
            "",
            "## Practical Meaning",
            "",
            "A replacement/prototype image has to preserve the upload envelope, date-prefixed image convention,",
            "ELF class/endianness/machine identity, entry/reset-vector placement, and the memory layout expected",
            "by the printer boot path. Passing this check would not prove a firmware is safe or useful, but failing",
            "it means the blob is structurally wrong before hardware testing even begins.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help=".dl upload, date-prefixed .img, or raw ELF")
    parser.add_argument("--json-output", type=Path, help="write full JSON report")
    parser.add_argument("--markdown-output", type=Path, help="write Markdown summary report")
    parser.add_argument("--sections", action="store_true", help="print all section headers")
    args = parser.parse_args()

    try:
        loaded = load_firmware(args.input)
        elf_info = parse_elf(loaded.elf)
        report = build_report(args.input, loaded, elf_info)
    except FirmwareError as exc:
        print(f"error: {exc}")
        return 2

    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(report))

    status = "PASS" if report["validation"]["ok"] else "FAIL"
    print(f"{status} {args.input}")
    print(f"kind={report['source_kind']} image_bytes={report['image_bytes']} elf_bytes={report['elf']['summary']['elf_bytes']}")
    print(
        "entry="
        f"{hex32(report['elf']['header']['entry'])} "
        f"machine=0x{report['elf']['header']['machine']:x} "
        f"phnum={report['elf']['header']['program_header_count']} "
        f"shnum={report['elf']['header']['section_header_count']}"
    )

    if args.sections:
        for section in report["elf"]["sections"]:
            print(
                f"{section['index']:02d} {section['name']:<28} "
                f"addr={hex32(section['addr'])} size=0x{section['size']:x} "
                f"flags={section['flags_text']} type={section['type_name']}"
            )

    for failure in report["validation"]["failures"]:
        print(f"failure: {failure}")
    for warning in report["validation"]["warnings"]:
        print(f"warning: {warning}")

    return 0 if report["validation"]["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
