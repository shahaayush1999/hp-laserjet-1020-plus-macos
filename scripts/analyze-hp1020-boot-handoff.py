#!/usr/bin/env python3
"""Generate an offline HP 1020 boot/upload handoff report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


UEL = b"\x1b%-12345X"
PJL_ENTER_ACL = UEL + b"@PJL ENTER LANGUAGE=ACL\r\n"
DATE_PREFIX_LEN = 8


def u16(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 2], "big")


def u32(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 4], "big")


def cstr_from(data: bytes, offset: int) -> str:
    if offset < 0 or offset >= len(data):
        return ""
    end = data.find(b"\x00", offset)
    if end == -1:
        end = len(data)
    return data[offset:end].decode("ascii", errors="replace")


def load_elf(path: Path) -> tuple[bytes, dict[str, Any]]:
    data = path.read_bytes()
    upload = None
    if data.startswith(PJL_ENTER_ACL):
        header_offset = len(PJL_ENTER_ACL)
        image_offset = header_offset + 8
        image = data[image_offset : -len(UEL)]
        elf = image[DATE_PREFIX_LEN:]
        upload = {
            "kind": "dl",
            "source_bytes": len(data),
            "acl_magic": data[header_offset : header_offset + 4].hex(),
            "acl_elf_length": u32(data, header_offset + 4),
            "image_offset": image_offset,
            "image_bytes": len(image),
            "date_prefix": image[:DATE_PREFIX_LEN].decode("ascii", errors="replace"),
            "trailer": data[-len(UEL) :].hex(),
        }
    elif len(data) >= DATE_PREFIX_LEN + 4 and data[DATE_PREFIX_LEN : DATE_PREFIX_LEN + 4] == b"\x7fELF":
        elf = data[DATE_PREFIX_LEN:]
        upload = {
            "kind": "date-prefixed-image",
            "source_bytes": len(data),
            "image_bytes": len(data),
            "date_prefix": data[:DATE_PREFIX_LEN].decode("ascii", errors="replace"),
        }
    else:
        elf = data
        upload = {"kind": "elf", "source_bytes": len(data)}
    if elf[:4] != b"\x7fELF":
        raise ValueError(f"{path} does not contain an ELF payload")
    return elf, upload


def parse_elf(elf: bytes) -> dict[str, Any]:
    if elf[4] != 1 or elf[5] != 2:
        raise ValueError("expected ELF32 big-endian")
    phoff = u32(elf, 28)
    shoff = u32(elf, 32)
    phentsize = u16(elf, 42)
    phnum = u16(elf, 44)
    shentsize = u16(elf, 46)
    shnum = u16(elf, 48)
    shstrndx = u16(elf, 50)

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
            }
        )

    shstr = raw_sections[shstrndx]
    names = elf[shstr["offset"] : shstr["offset"] + shstr["size"]]
    for section in raw_sections:
        section["name"] = cstr_from(names, section["name_offset"])
        section["flags_text"] = section_flags(section["flags"])

    program_headers = []
    for i in range(phnum):
        off = phoff + i * phentsize
        program_headers.append(
            {
                "index": i,
                "type": u32(elf, off),
                "offset": u32(elf, off + 4),
                "vaddr": u32(elf, off + 8),
                "paddr": u32(elf, off + 12),
                "filesz": u32(elf, off + 16),
                "memsz": u32(elf, off + 20),
                "flags": u32(elf, off + 24),
                "align": u32(elf, off + 28),
            }
        )

    return {
        "header": {
            "type": u16(elf, 16),
            "machine": u16(elf, 18),
            "entry": u32(elf, 24),
            "flags": u32(elf, 36),
            "program_header_count": phnum,
            "section_header_count": shnum,
        },
        "sections": raw_sections,
        "program_headers": program_headers,
    }


def section_flags(flags: int) -> str:
    out = []
    if flags & 1:
        out.append("W")
    if flags & 2:
        out.append("A")
    if flags & 4:
        out.append("X")
    return "".join(out) or "-"


def read_addr(
    elf: bytes,
    sections: list[dict[str, Any]],
    addr: int,
    size: int,
    program_headers: list[dict[str, Any]] | None = None,
) -> bytes | None:
    for section in sections:
        start = section["addr"]
        end = start + section["size"]
        if section["type"] != 8 and start <= addr and addr + size <= end:
            offset = section["offset"] + addr - start
            return elf[offset : offset + size]
    for ph in program_headers or []:
        if ph["type"] != 1:
            continue
        start = ph["vaddr"]
        end = start + ph["filesz"]
        if start <= addr and addr + size <= end:
            offset = ph["offset"] + addr - start
            return elf[offset : offset + size]
    return None


def section_for(sections: list[dict[str, Any]], addr: int) -> str | None:
    if addr == 0:
        return None
    for section in sections:
        if section["size"] and (section["flags"] & 0x2) and section["addr"] <= addr < section["addr"] + section["size"]:
            return section["name"]
    return None


def read_word(
    elf: bytes,
    sections: list[dict[str, Any]],
    program_headers: list[dict[str, Any]],
    addr: int,
) -> int | None:
    data = read_addr(elf, sections, addr, 4, program_headers)
    if data is None:
        return None
    return int.from_bytes(data, "big")


def read_cstr_at_addr(elf: bytes, sections: list[dict[str, Any]], addr: int) -> str:
    data = read_addr(elf, sections, addr, 96)
    if data is None:
        return ""
    return cstr_from(data, 0)


def load_labels(path: Path) -> dict[int, dict[str, str]]:
    labels: dict[int, dict[str, str]] = {}
    if not path.exists():
        return labels
    for line in path.read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        try:
            addr = int(parts[0], 16)
        except ValueError:
            continue
        labels[addr] = {
            "name": parts[1],
            "kind": parts[2] if len(parts) > 2 else "",
            "confidence": parts[3] if len(parts) > 3 else "",
            "description": parts[4] if len(parts) > 4 else "",
        }
    return labels


def summarize_firmware(path: Path, label_path: Path) -> dict[str, Any]:
    elf, upload = load_elf(path)
    parsed = parse_elf(elf)
    sections = parsed["sections"]
    program_headers = parsed["program_headers"]
    labels = load_labels(label_path)

    sys_table_addr = 0x10000370
    sys_words = []
    raw_table = read_addr(elf, sections, sys_table_addr, 75 * 4, program_headers)
    if raw_table is not None:
        for i in range(75):
            ptr = int.from_bytes(raw_table[i * 4 : i * 4 + 4], "big")
            label = labels.get(ptr, {})
            sys_words.append(
                {
                    "index": i,
                    "table_addr": sys_table_addr + i * 4,
                    "ptr": ptr,
                    "section": section_for(sections, ptr),
                    "label": label.get("name", ""),
                    "description": label.get("description", ""),
                }
            )

    entry_vector = []
    for addr in (0x10006A14, 0x10006A18, 0x10006A1C, 0x10006A58, 0x10006A60, 0x10006A64):
        value = read_word(elf, sections, program_headers, addr)
        entry_vector.append(
            {
                "addr": addr,
                "value": value,
                "section": section_for(sections, value) if value is not None else None,
                "label": labels.get(value or -1, {}).get("name", ""),
                "description": labels.get(value or -1, {}).get("description", ""),
            }
        )

    acl_descriptor = []
    base = 0x1001BE90
    raw_acl = read_addr(elf, sections, base, 0x70, program_headers)
    if raw_acl is not None:
        for i in range(0, len(raw_acl), 4):
            value = int.from_bytes(raw_acl[i : i + 4], "big")
            text = ""
            if 0x10000000 <= value <= 0x10110000:
                text = read_cstr_at_addr(elf, sections, value)
            elif value:
                word = value.to_bytes(4, "big")
                if all((32 <= b < 127) or b == 0 for b in word):
                    text = word.rstrip(b"\x00").decode("ascii", errors="replace")
            acl_descriptor.append(
                {
                    "index": i // 4,
                    "addr": base + i,
                    "value": value,
                    "section": section_for(sections, value),
                    "text": text,
                    "label": labels.get(value, {}).get("name", ""),
                }
            )

    special_addrs = []
    for addr in (0x10000350, 0x10000370, 0x10005C80, 0x100167A8, 0x10100020):
        special_addrs.append(
            {
                "addr": addr,
                "section": section_for(sections, addr),
                "bytes": (read_addr(elf, sections, addr, 16, program_headers) or b"").hex(" "),
            }
        )

    unique_sys_targets = sorted({item["ptr"] for item in sys_words})
    return {
        "path": str(path),
        "upload": upload,
        "elf": parsed["header"],
        "sections": [
            {
                "name": s["name"],
                "addr": s["addr"],
                "size": s["size"],
                "flags": s["flags_text"],
            }
            for s in sections
            if s["flags"] & 0x2
        ],
        "entry_vector": entry_vector,
        "system_interface_table": sys_words,
        "system_interface_unique_targets": unique_sys_targets,
        "acl_descriptor_at_1001be90": acl_descriptor,
        "special_addresses": special_addrs,
    }


def hx(value: int | None) -> str:
    if value is None:
        return "none"
    return f"0x{value:08x}"


def render_report(stock: dict[str, Any], probe: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 Boot/Upload Handoff Analysis",
        "",
        "This is an offline analysis. It does not contact the printer.",
        "",
        "## Plain Result",
        "",
        "The open idle probe now matches the outer firmware shape well enough for a controlled boot experiment:",
        "",
        "- HP-style PJL/ACL wrapper",
        "- 8-byte date prefix",
        "- big-endian old-Xtensa ELF machine id `0xabc7`",
        "- HP entry address `0x100167a8`",
        "- HP vector/interface/reset anchor addresses",
        "",
        "The remaining unknown is not packaging anymore. It is whether the printer's resident boot/ACL code expects the uploaded firmware to provide more of HP's runtime ABI than our idle probe currently provides.",
        "",
        "## Stock vs Idle Probe",
        "",
        "| Item | Stock HP firmware | Open idle probe |",
        "| --- | ---: | ---: |",
        f"| Source bytes | `{stock['upload']['source_bytes']}` | `{probe['upload']['source_bytes']}` |",
        f"| Image bytes | `{stock['upload'].get('image_bytes')}` | `{probe['upload'].get('image_bytes')}` |",
        f"| Date prefix | `{stock['upload'].get('date_prefix', '')}` | `{probe['upload'].get('date_prefix', '')}` |",
        f"| ELF machine | `{hx(stock['elf']['machine'])}` | `{hx(probe['elf']['machine'])}` |",
        f"| ELF entry | `{hx(stock['elf']['entry'])}` | `{hx(probe['elf']['entry'])}` |",
        f"| Program headers | `{stock['elf']['program_header_count']}` | `{probe['elf']['program_header_count']}` |",
        f"| Section headers | `{stock['elf']['section_header_count']}` | `{probe['elf']['section_header_count']}` |",
        f"| System-interface unique targets | `{len(stock['system_interface_unique_targets'])}` | `{len(probe['system_interface_unique_targets'])}` |",
        "",
        "## Entry/Runtime Vector Words",
        "",
        "These words are important in the stock firmware because the ELF entry jumps into low-level CPU/runtime setup through them.",
        "",
        "| Address | Stock value | Stock label/section | Probe value | Probe label/section |",
        "| ---: | ---: | --- | ---: | --- |",
    ]
    probe_by_addr = {item["addr"]: item for item in probe["entry_vector"]}
    for item in stock["entry_vector"]:
        other = probe_by_addr.get(item["addr"], {})
        stock_desc = item["label"] or item["section"] or ""
        probe_desc = other.get("label") or other.get("section") or ""
        lines.append(
            f"| `{hx(item['addr'])}` | `{hx(item['value'])}` | {stock_desc} | `{hx(other.get('value'))}` | {probe_desc} |"
        )

    lines.extend(
        [
            "",
            "## ACL Module Descriptor",
            "",
            "The stock firmware has a descriptor-like table at `0x1001be90`. The first word points at `0x10000350`, which is exactly the boundary after `.DoubleExceptionVector.text`; the next word is ASCII `ACL`.",
            "",
            "| # | Address | Value | Decoded text / target |",
            "| ---: | ---: | ---: | --- |",
        ]
    )
    for item in stock["acl_descriptor_at_1001be90"][:20]:
        lines.append(
            f"| `{item['index']}` | `{hx(item['addr'])}` | `{hx(item['value'])}` | {item['text'] or item['label'] or item['section'] or ''} |"
        )

    lines.extend(
        [
            "",
            "## System Interface Strategy",
            "",
            "The stock table has 75 mostly distinct runtime-service function pointers. The idle probe intentionally does not copy those HP routines. Instead, every interface slot points to one local trap loop.",
            "",
            "| Firmware | Table behavior | Practical meaning |",
            "| --- | --- | --- |",
            f"| Stock | `{len(stock['system_interface_unique_targets'])}` unique targets | full HP/ThreadX runtime services |",
            f"| Idle probe | `{len(probe['system_interface_unique_targets'])}` unique target: `{hx(probe['system_interface_unique_targets'][0] if probe['system_interface_unique_targets'] else None)}` | unexpected interface call hangs in our code instead of jumping through null or touching hardware |",
            "",
            "## Hardware-Test Readiness",
            "",
            "A first hardware test is now technically defined, but still optional:",
            "",
            "1. Power-cycle printer.",
            "2. Upload only `analysis/open-firmware-probes/minimal-idle/hp1020-idle-probe.dl`.",
            "3. Send no document and no ZjStream data.",
            "4. Watch whether the USB device disappears, re-enumerates, or hangs until power-cycle.",
            "",
            "This would answer one narrow question: does the printer accept and branch into our uploaded code at all?",
            "",
            "## Remaining Offline Unknowns",
            "",
            "- Whether the resident boot/ACL code validates the exact HP section table or only the loadable program headers.",
            "- Whether `0x10000350` is patched or treated specially by resident boot code during ACL module handling.",
            "- Whether the ELF entry is reached directly after upload, or whether the boot path expects the HP CPU/TLB init sequence first.",
            "- Whether an idle-only payload leaves USB in a recoverable-but-non-enumerating state until power-cycle.",
            "",
            "## Recommendation",
            "",
            "There is still offline value in tightening the upload harness and documenting expected observations, but the core packaging/shape question is now mostly answered. The next truly decisive question requires a hardware upload of the idle probe.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stock", type=Path, default=Path("assets/runtime/sihp1020.dl"))
    parser.add_argument(
        "--probe",
        type=Path,
        default=Path("analysis/open-firmware-probes/minimal-idle/hp1020-idle-probe.dl"),
    )
    parser.add_argument("--labels", type=Path, default=Path("analysis/symbols/hp1020-labels.tsv"))
    parser.add_argument("--markdown-output", type=Path, default=Path("analysis/boot-handoff/boot-handoff.md"))
    parser.add_argument("--json-output", type=Path, default=Path("analysis/boot-handoff/boot-handoff.json"))
    args = parser.parse_args()

    stock = summarize_firmware(args.stock, args.labels)
    probe = summarize_firmware(args.probe, args.labels)
    report = {"stock": stock, "probe": probe}

    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.write_text(render_report(stock, probe))
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    print(args.markdown_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
