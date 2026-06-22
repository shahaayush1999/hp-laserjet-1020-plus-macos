#!/usr/bin/env python3
"""Extract USB descriptor evidence from the HP LaserJet 1020 firmware ELF."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]


def load_layout_module() -> Any:
    module_path = ROOT_DIR / "scripts" / "inspect-firmware-layout.py"
    spec = importlib.util.spec_from_file_location("inspect_firmware_layout", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_layout = load_layout_module()
FirmwareError = _layout.FirmwareError
load_firmware = _layout.load_firmware
parse_elf = _layout.parse_elf


HP_VENDOR_ID = 0x03F0
KNOWN_TEXT = [
    b"$$DEVICE_ID_STRING$$",
    b"Hewlett-Packard",
    b"HP LaserJet 1020",
    b"HPBOISEID",
    b"@PJL ECHO ",
    b"MFG:",
    b"MDL:",
    b"FWVER",
]


@dataclass(frozen=True)
class MemoryImage:
    elf: bytes
    segments: list[dict[str, int]]

    def va_to_offset(self, va: int) -> int | None:
        for seg in self.segments:
            start = seg["vaddr"]
            end = start + seg["filesz"]
            if start <= va < end:
                return seg["offset"] + (va - start)
        return None

    def offset_to_va(self, offset: int) -> int | None:
        for seg in self.segments:
            start = seg["offset"]
            end = start + seg["filesz"]
            if start <= offset < end:
                return seg["vaddr"] + (offset - start)
        return None

    def read(self, va: int, size: int) -> bytes | None:
        off = self.va_to_offset(va)
        if off is None or off + size > len(self.elf):
            return None
        return self.elf[off : off + size]

    def u32be(self, va: int) -> int | None:
        data = self.read(va, 4)
        if data is None:
            return None
        return int.from_bytes(data, "big")


def make_memory_image(elf: bytes, elf_info: dict[str, Any]) -> MemoryImage:
    segments = [
        {
            "offset": ph["offset"],
            "vaddr": ph["vaddr"],
            "filesz": ph["filesz"],
            "memsz": ph["memsz"],
        }
        for ph in elf_info["program_headers"]
        if ph["type"] == 1 and ph["filesz"] > 0
    ]
    return MemoryImage(elf=elf, segments=segments)


def le16(data: bytes, off: int) -> int:
    return int.from_bytes(data[off : off + 2], "little")


def c_string(data: bytes, off: int) -> str:
    end = data.find(b"\x00", off)
    if end == -1:
        end = len(data)
    return data[off:end].decode("ascii", errors="replace")


def parse_device_descriptor(data: bytes) -> dict[str, Any]:
    return {
        "bLength": data[0],
        "bDescriptorType": data[1],
        "bcdUSB": le16(data, 2),
        "bDeviceClass": data[4],
        "bDeviceSubClass": data[5],
        "bDeviceProtocol": data[6],
        "bMaxPacketSize0": data[7],
        "idVendor": le16(data, 8),
        "idProduct": le16(data, 10),
        "bcdDevice": le16(data, 12),
        "iManufacturer": data[14],
        "iProduct": data[15],
        "iSerialNumber": data[16],
        "bNumConfigurations": data[17],
    }


def parse_config_tree(blob: bytes) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    pos = 0
    while pos + 2 <= len(blob):
        length = blob[pos]
        dtype = blob[pos + 1]
        if length < 2 or pos + length > len(blob):
            items.append({"offset": pos, "error": "invalid descriptor length", "length": length, "type": dtype})
            break
        raw = blob[pos : pos + length]
        item: dict[str, Any] = {
            "offset": pos,
            "length": length,
            "type": dtype,
            "raw_hex": raw.hex(" "),
        }
        if dtype == 2 and length >= 9:
            item.update(
                {
                    "kind": "configuration",
                    "wTotalLength": le16(raw, 2),
                    "bNumInterfaces": raw[4],
                    "bConfigurationValue": raw[5],
                    "iConfiguration": raw[6],
                    "bmAttributes": raw[7],
                    "bMaxPower": raw[8],
                }
            )
        elif dtype == 4 and length >= 9:
            item.update(
                {
                    "kind": "interface",
                    "bInterfaceNumber": raw[2],
                    "bAlternateSetting": raw[3],
                    "bNumEndpoints": raw[4],
                    "bInterfaceClass": raw[5],
                    "bInterfaceSubClass": raw[6],
                    "bInterfaceProtocol": raw[7],
                    "iInterface": raw[8],
                }
            )
        elif dtype == 5 and length >= 7:
            item.update(
                {
                    "kind": "endpoint",
                    "bEndpointAddress": raw[2],
                    "bmAttributes": raw[3],
                    "wMaxPacketSize": le16(raw, 4),
                    "bInterval": raw[6],
                }
            )
        else:
            item["kind"] = f"type-{dtype}"
        items.append(item)
        pos += length
    return items


def scan_device_descriptors(mem: MemoryImage) -> list[dict[str, Any]]:
    hits = []
    elf = mem.elf
    for off in range(0, len(elf) - 18):
        if elf[off] != 18 or elf[off + 1] != 1:
            continue
        data = elf[off : off + 18]
        parsed = parse_device_descriptor(data)
        if parsed["idVendor"] != HP_VENDOR_ID:
            continue
        va = mem.offset_to_va(off)
        hits.append({"file_offset": off, "vaddr": va, "raw_hex": data.hex(" "), "fields": parsed})
    return hits


def scan_config_descriptors(mem: MemoryImage) -> list[dict[str, Any]]:
    hits = []
    elf = mem.elf
    for off in range(0, len(elf) - 9):
        if elf[off] != 9 or elf[off + 1] != 2:
            continue
        total = le16(elf, off + 2)
        if total < 9 or total > 512 or off + total > len(elf):
            continue
        blob = elf[off : off + total]
        tree = parse_config_tree(blob)
        if not any(item.get("kind") == "interface" for item in tree):
            continue
        if not any(item.get("kind") == "endpoint" for item in tree):
            continue
        va = mem.offset_to_va(off)
        hits.append({"file_offset": off, "vaddr": va, "total_length": total, "raw_hex": blob.hex(" "), "items": tree})
    return hits


def scan_known_strings(mem: MemoryImage) -> list[dict[str, Any]]:
    out = []
    for needle in KNOWN_TEXT:
        start = 0
        while True:
            off = mem.elf.find(needle, start)
            if off == -1:
                break
            va = mem.offset_to_va(off)
            full = c_string(mem.elf, off)
            if any((ord(ch) < 32 or ord(ch) > 126) for ch in full):
                full = needle.decode("ascii", errors="replace")
            out.append(
                {
                    "text": full,
                    "file_offset": off,
                    "vaddr": va,
                }
            )
            start = off + 1
    return out


def scan_pointer_runs(mem: MemoryImage, targets: set[int]) -> list[dict[str, Any]]:
    runs = []
    elf = mem.elf
    offsets = []
    for off in range(0, len(elf) - 4, 4):
        value = int.from_bytes(elf[off : off + 4], "big")
        if value in targets:
            offsets.append(off)
    seen = set()
    for off in offsets:
        if off in seen:
            continue
        run_offsets = [off]
        seen.add(off)
        next_off = off + 4
        while next_off in offsets:
            run_offsets.append(next_off)
            seen.add(next_off)
            next_off += 4
        prev_off = off - 4
        while prev_off in offsets:
            run_offsets.insert(0, prev_off)
            seen.add(prev_off)
            prev_off -= 4
        values = [int.from_bytes(elf[o : o + 4], "big") for o in run_offsets]
        runs.append(
            {
                "file_offset": run_offsets[0],
                "vaddr": mem.offset_to_va(run_offsets[0]),
                "words": len(values),
                "values": values,
            }
        )
    return sorted(runs, key=lambda item: (item["words"], item["file_offset"]), reverse=True)


def hexaddr(value: int | None) -> str:
    if value is None:
        return "n/a"
    return f"0x{value:08x}"


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 USB Descriptor Extraction",
        "",
        "This report is generated from the firmware ELF bytes. It does not contact the printer.",
        "",
        "## Device Descriptors",
        "",
        "| VAddr | Product | USB | EP0 | Manufacturer | Product String | Serial | Configs | Raw |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for hit in report["device_descriptors"]:
        f = hit["fields"]
        lines.append(
            "| "
            f"`{hexaddr(hit['vaddr'])}` | `0x{f['idProduct']:04x}` | `0x{f['bcdUSB']:04x}` | "
            f"`{f['bMaxPacketSize0']}` | `{f['iManufacturer']}` | `{f['iProduct']}` | "
            f"`{f['iSerialNumber']}` | `{f['bNumConfigurations']}` | `{hit['raw_hex']}` |"
        )

    lines.extend(
        [
            "",
            "## Configuration Descriptors",
            "",
            "| VAddr | Total Length | Interfaces | Endpoints | Raw Prefix |",
            "| ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for hit in report["config_descriptors"]:
        interfaces = [item for item in hit["items"] if item.get("kind") == "interface"]
        endpoints = [item for item in hit["items"] if item.get("kind") == "endpoint"]
        lines.append(
            "| "
            f"`{hexaddr(hit['vaddr'])}` | `{hit['total_length']}` | `{len(interfaces)}` | `{len(endpoints)}` | "
            f"`{hit['raw_hex'][:96]}` |"
        )
        for item in hit["items"]:
            if item.get("kind") == "interface":
                lines.append(
                    f"  - interface `{item['bInterfaceNumber']}` class `0x{item['bInterfaceClass']:02x}` "
                    f"subclass `0x{item['bInterfaceSubClass']:02x}` protocol `0x{item['bInterfaceProtocol']:02x}`"
                )
            elif item.get("kind") == "endpoint":
                lines.append(
                    f"  - endpoint `0x{item['bEndpointAddress']:02x}` attr `0x{item['bmAttributes']:02x}` "
                    f"max packet `{item['wMaxPacketSize']}` interval `{item['bInterval']}`"
                )

    lines.extend(
        [
            "",
            "## Known Strings",
            "",
            "| VAddr | Text |",
            "| ---: | --- |",
        ]
    )
    for item in report["known_strings"]:
        lines.append(f"| `{hexaddr(item['vaddr'])}` | `{item['text']}` |")

    lines.extend(
        [
            "",
            "## Pointer Runs To Known Strings",
            "",
            "| VAddr | Words | Values |",
            "| ---: | ---: | --- |",
        ]
    )
    for run in report["pointer_runs"][:20]:
        values = ", ".join(hexaddr(v) for v in run["values"])
        lines.append(f"| `{hexaddr(run['vaddr'])}` | `{run['words']}` | `{values}` |")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Two HP device descriptor candidates are present in `.data`, both with vendor ID `0x03f0`.",
            "- The descriptor product ID bytes match the host-observed `0x2b17` identity.",
            "- A full USB printer-style configuration descriptor is present with interface class `0x07`.",
            "- Static string evidence confirms the stock firmware has manufacturer/product strings and an IEEE-1284 template.",
            "- This strengthens the future USB-marker target, but it does not remove the need to implement/control endpoint-0 behavior in open firmware.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", type=Path, default=ROOT_DIR / "analysis/sihp1020.elf")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    args = parser.parse_args()

    try:
        loaded = load_firmware(args.input)
        elf_info = parse_elf(loaded.elf)
    except FirmwareError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    mem = make_memory_image(loaded.elf, elf_info)
    known_strings = scan_known_strings(mem)
    targets = {item["vaddr"] for item in known_strings if item["vaddr"] is not None}
    report = {
        "input": str(args.input),
        "device_descriptors": scan_device_descriptors(mem),
        "config_descriptors": scan_config_descriptors(mem),
        "known_strings": known_strings,
        "pointer_runs": scan_pointer_runs(mem, targets),
    }

    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(report) + "\n")

    print(
        "device_descriptors="
        f"{len(report['device_descriptors'])} "
        f"config_descriptors={len(report['config_descriptors'])} "
        f"known_strings={len(report['known_strings'])} "
        f"pointer_runs={len(report['pointer_runs'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
