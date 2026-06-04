#!/usr/bin/env python3
"""Inspect a Zenographics ZjStream file produced for the HP LaserJet 1020."""

from __future__ import annotations

import argparse
import struct
from pathlib import Path


ZJT_NAMES = {
    0x00: "ZJT_START_DOC",
    0x01: "ZJT_END_DOC",
    0x02: "ZJT_START_PAGE",
    0x03: "ZJT_END_PAGE",
    0x04: "ZJT_JBIG_BIH",
    0x05: "ZJT_JBIG_BID",
    0x06: "ZJT_END_JBIG",
    0x07: "ZJT_SIGNATURE",
    0x08: "ZJT_RAW_IMAGE",
    0x09: "ZJT_START_PLANE",
    0x0A: "ZJT_END_PLANE",
    0x0B: "ZJT_2600N_PAUSE",
    0x0C: "ZJT_2600N",
}

ZJI_NAMES = {
    0x00: "ZJI_PAGECOUNT",
    0x01: "ZJI_DMCOLLATE",
    0x02: "ZJI_DMDUPLEX",
    0x03: "ZJI_DMPAPER",
    0x04: "ZJI_DMCOPIES",
    0x05: "ZJI_DMDEFAULTSOURCE",
    0x06: "ZJI_DMMEDIATYPE",
    0x07: "ZJI_NBIE",
    0x08: "ZJI_RESOLUTION_X",
    0x09: "ZJI_RESOLUTION_Y",
    0x0A: "ZJI_OFFSET_X",
    0x0B: "ZJI_OFFSET_Y",
    0x0C: "ZJI_RASTER_X",
    0x0D: "ZJI_RASTER_Y",
    0x0E: "ZJI_COLLATE",
    0x0F: "ZJI_QUANTITY",
    0x10: "ZJI_VIDEO_BPP",
    0x11: "ZJI_VIDEO_X",
    0x12: "ZJI_VIDEO_Y",
    0x13: "ZJI_INTERLACE",
    0x14: "ZJI_PLANE",
    0x15: "ZJI_PALETTE",
    0x16: "ZJI_RET",
    0x17: "ZJI_ECONOMODE",
    0x63: "ZJI_PAD",
    0x66: "ZJI_JBIG_BIH",
    0x69: "ZJI_INCRY",
}

ITEM_TYPES = {
    0x01: "UINT32",
    0x02: "INT32",
    0x03: "STRING",
    0x04: "BYTELUT",
}


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from(">I", data, offset)[0]


def u16(data: bytes, offset: int) -> int:
    return struct.unpack_from(">H", data, offset)[0]


def parse_bih(data: bytes) -> dict[str, int | str]:
    result: dict[str, int | str] = {"hex": data.hex(" ")}
    if len(data) >= 20:
        dl = data[0]
        d = data[1]
        p = data[2]
        yd = u32(data, 8)
        l0 = u32(data, 12)
        stripe_mask = (1 << d) - 1 if d < 32 else 0
        stripes = ((yd >> d) + (1 if (stripe_mask & u32(data, 4)) != 0 else 0) + l0 - 1) // l0
        result.update(
            {
                "dl": dl,
                "d": d,
                "p": p,
                "unknown_3": data[3],
                "xd": u32(data, 4),
                "yd": yd,
                "l0": l0,
                "mx": data[16],
                "my": data[17],
                "order": data[18],
                "options": data[19],
                "stripes": stripes,
                "layers": d - dl,
                "planes": p,
            }
        )
    return result


def parse_items(payload: bytes) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    pos = 0
    while pos + 8 <= len(payload):
        size = u32(payload, pos)
        if size < 8 or pos + size > len(payload):
            break
        item_id = u16(payload, pos + 4)
        item_type = payload[pos + 6]
        param = payload[pos + 7]
        body = payload[pos + 8 : pos + size]
        item: dict[str, object] = {
            "offset": pos,
            "size": size,
            "id": item_id,
            "name": ZJI_NAMES.get(item_id, f"ZJI_0x{item_id:04x}"),
            "type": ITEM_TYPES.get(item_type, f"0x{item_type:02x}"),
            "param": param,
        }
        if item_type in (0x01, 0x02) and len(body) >= 4:
            item["value"] = u32(body, 0)
        elif item_type == 0x03:
            item["value"] = body.split(b"\0", 1)[0].decode("latin-1", errors="replace")
        elif item_type == 0x04 and len(body) >= 4:
            lut_len = u32(body, 0)
            item["length"] = lut_len
            if item_id == 0x66 and len(body) >= 4 + lut_len:
                item["bih"] = parse_bih(body[4 : 4 + lut_len])
        else:
            item["raw_hex"] = body[:64].hex(" ")
        items.append(item)
        pos += size
    return items


def find_magic(data: bytes) -> int:
    candidates = [idx for marker in (b"JZJZ", b",XQX") if (idx := data.find(marker)) >= 0]
    if not candidates:
        raise ValueError("No ZjStream magic marker found")
    return min(candidates)


def inspect(path: Path) -> str:
    data = path.read_bytes()
    magic_offset = find_magic(data)
    pos = magic_offset + 4
    lines = [
        f"# ZjStream Inspection: {path}",
        "",
        f"- file bytes: `{len(data)}`",
        f"- magic offset: `0x{magic_offset:x}`",
        f"- prefix bytes before magic: `{magic_offset}`",
        f"- magic: `{data[magic_offset:magic_offset + 4].decode('latin-1')}`",
        "",
        "## Chunks",
        "",
        "| # | Offset | Type | Name | Size | Items | Reserved | Signature | Notes |",
        "|---:|---:|---:|---|---:|---:|---:|---:|---|",
    ]
    chunk_index = 0
    detailed: list[str] = []
    bid_count = 0
    bid_bytes = 0
    while pos + 16 <= len(data):
        offset = pos
        size, chunk_type, items, reserved, signature = struct.unpack_from(">IIIHH", data, pos)
        if size < 16 or pos + size > len(data):
            lines.append(
                f"| `{chunk_index}` | `0x{offset:x}` | `?` | `invalid` | `{size}` | | | | stops parse |"
            )
            break
        payload = data[pos + 16 : pos + size]
        name = ZJT_NAMES.get(chunk_type, f"ZJT_0x{chunk_type:08x}")
        notes: list[str] = []
        if signature != 0x5A5A:
            notes.append("bad signature")
        if chunk_type == 0x04:
            bih = parse_bih(payload)
            notes.append(f"BIH XD={bih.get('xd')} YD={bih.get('yd')}")
        if chunk_type == 0x05:
            bid_count += 1
            bid_bytes += len(payload)
            notes.append(f"BID bytes={len(payload)}")
        lines.append(
            f"| `{chunk_index}` | `0x{offset:x}` | `0x{chunk_type:02x}` | `{name}` | `{size}` | `{items}` | `0x{reserved:04x}` | `0x{signature:04x}` | {'; '.join(notes)} |"
        )
        if items:
            detailed.extend(render_items(chunk_index, name, parse_items(payload)))
        elif chunk_type == 0x04:
            detailed.extend(render_bih(chunk_index, parse_bih(payload)))
        pos += size
        chunk_index += 1
        if chunk_type == 0x01:
            break
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- parsed chunks: `{chunk_index}`",
            f"- trailing bytes after parsed stream: `{len(data) - pos}`",
            f"- JBIG_BID chunks: `{bid_count}`",
            f"- total JBIG_BID payload bytes: `{bid_bytes}`",
        ]
    )
    if detailed:
        lines.extend(["", "## Decoded Details", "", *detailed])
    return "\n".join(lines) + "\n"


def render_items(chunk_index: int, name: str, items: list[dict[str, object]]) -> list[str]:
    lines = [
        f"### Chunk {chunk_index} `{name}` Items",
        "",
        "| Offset | Item | Type | Value |",
        "|---:|---|---|---|",
    ]
    for item in items:
        value = item.get("value", item.get("length", item.get("raw_hex", "")))
        lines.append(
            f"| `0x{int(item['offset']):x}` | `{item['name']}` (`0x{int(item['id']):04x}`) | `{item['type']}` | `{value}` |"
        )
        if "bih" in item:
            lines.extend(["", *render_bih(chunk_index, item["bih"]), ""])
    lines.append("")
    return lines


def render_bih(chunk_index: int, bih: dict[str, object]) -> list[str]:
    return [
        f"### Chunk {chunk_index} JBIG BIH",
        "",
        f"- raw: `{bih.get('hex')}`",
        f"- dl/d/p/unknown3: `{bih.get('dl')}` / `{bih.get('d')}` / `{bih.get('p')}` / `{bih.get('unknown_3')}`",
        f"- XD/YD: `{bih.get('xd')}` x `{bih.get('yd')}`",
        f"- L0: `{bih.get('l0')}`",
        f"- MX/MY: `{bih.get('mx')}` / `{bih.get('my')}`",
        f"- Order: `0x{int(bih.get('order', 0)):02x}`",
        f"- Options: `0x{int(bih.get('options', 0)):02x}`",
        f"- stripes/layers/planes: `{bih.get('stripes')}` / `{bih.get('layers')}` / `{bih.get('planes')}`",
        "",
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zjs", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()

    report = inspect(args.zjs)
    if args.output:
        args.output.write_text(report)
    else:
        print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
