#!/usr/bin/env python3
"""Model the HP 1020 firmware's normal ZjStream print path offline.

This script does not talk to the printer. It parses a ZjStream file and emits a
firmware-shaped object/message trace for the path currently mapped in Ghidra:

USB ZjStream parser -> JobMgr messages -> page/work/raster objects -> video
handoff boundary.
"""

from __future__ import annotations

import argparse
import json
from hp1020_work_fields import direct_work_fields
from hp1020_metadata_bounds import metadata_bounds
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any


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

PARSER_TARGETS = {
    0x00: "0x10009efe",
    0x01: "0x1000a1b3",
    0x02: "0x10009f86",
    0x03: "0x1000a19e",
    0x04: "0x1000a006",
    0x05: "0x1000a014",
    0x06: "0x1000a053",
    0x07: "0x1000a1ef",
    0x08: "0x1000a1ef",
    0x09: "0x1000a1ef",
    0x0A: "0x1000a173",
    0x0B: "0x1000a1d6",
    0x0C: "0x1000a05d",
}


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from(">I", data, offset)[0]


def u16(data: bytes, offset: int) -> int:
    return struct.unpack_from(">H", data, offset)[0]


@dataclass
class Chunk:
    index: int
    offset: int
    size: int
    chunk_type: int
    item_count: int
    reserved: int
    signature: int
    payload: bytes

    @property
    def name(self) -> str:
        return ZJT_NAMES.get(self.chunk_type, f"ZJT_0x{self.chunk_type:08x}")

    @property
    def parser_target(self) -> str:
        return PARSER_TARGETS.get(self.chunk_type, "unmapped")


def parse_bih(data: bytes) -> dict[str, Any]:
    result: dict[str, Any] = {"hex": data.hex(" ")}
    if len(data) < 20:
        result["error"] = f"short BIH: {len(data)} bytes"
        return result

    dl = data[0]
    d = data[1]
    p = data[2]
    xd = u32(data, 4)
    yd = u32(data, 8)
    l0 = u32(data, 12)
    stripe_mask = (1 << d) - 1 if d < 32 else 0
    stripes = ((yd >> d) + (1 if (stripe_mask & xd) != 0 else 0) + l0 - 1) // l0 if l0 else 0
    result.update(
        {
            "dl": dl,
            "d": d,
            "p": p,
            "unknown_3": data[3],
            "xd": xd,
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


def parse_items(payload: bytes) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    pos = 0
    while pos + 8 <= len(payload):
        size = u32(payload, pos)
        if size < 8 or pos + size > len(payload):
            break
        item_id = u16(payload, pos + 4)
        item_type = payload[pos + 6]
        param = payload[pos + 7]
        body = payload[pos + 8 : pos + size]
        item: dict[str, Any] = {
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


def parse_chunks(path: Path) -> tuple[bytes, int, list[Chunk], int]:
    data = path.read_bytes()
    magic_offset = find_magic(data)
    pos = magic_offset + 4
    chunks: list[Chunk] = []

    while pos + 16 <= len(data):
        offset = pos
        size, chunk_type, item_count, reserved, signature = struct.unpack_from(">IIIHH", data, pos)
        if size < 16 or pos + size > len(data):
            raise ValueError(f"Invalid ZjStream chunk at 0x{offset:x}: size={size}")
        chunks.append(
            Chunk(
                index=len(chunks),
                offset=offset,
                size=size,
                chunk_type=chunk_type,
                item_count=item_count,
                reserved=reserved,
                signature=signature,
                payload=data[pos + 16 : pos + size],
            )
        )
        pos += size
        if chunk_type == 0x01:
            break
    return data, magic_offset, chunks, len(data) - pos


def item_map(items: list[dict[str, Any]]) -> dict[str, Any]:
    mapped: dict[str, Any] = {}
    for item in items:
        if "value" in item:
            mapped[item["name"]] = item["value"]
        elif "length" in item:
            mapped[item["name"]] = {"length": item["length"], "bih": item.get("bih")}
    return mapped


def append_trace(trace: list[dict[str, Any]], chunk: Chunk, action: str, messages: list[dict[str, Any]], effects: list[str]) -> None:
    trace.append(
        {
            "chunk_index": chunk.index,
            "chunk_offset": f"0x{chunk.offset:x}",
            "chunk_type": f"0x{chunk.chunk_type:02x}",
            "chunk_name": chunk.name,
            "parser_target": chunk.parser_target,
            "action": action,
            "jobmgr_messages": messages,
            "effects": effects,
        }
    )


def build_model(path: Path) -> dict[str, Any]:
    data, magic_offset, chunks, trailing = parse_chunks(path)
    model: dict[str, Any] = {
        "source": str(path),
        "file_bytes": len(data),
        "magic_offset": magic_offset,
        "trailing_bytes": trailing,
        "parser_entry": "0x10009d34",
        "jobmgr_queue": 3,
        "objects": {
            "documents": [],
            "pages": [],
            "work_objects": [],
            "raster_nodes": [],
        },
        "runtime_blocks": {},
        "trace": [],
        "hardware_boundary": {},
    }
    active_doc: dict[str, Any] | None = None
    active_page: dict[str, Any] | None = None
    active_work: dict[str, Any] | None = None
    raster_index = 0

    for chunk in chunks:
        messages: list[dict[str, Any]] = []
        effects: list[str] = []

        if chunk.chunk_type == 0x00:
            items = parse_items(chunk.payload)
            active_doc = {
                "id": f"doc{len(model['objects']['documents'])}",
                "firmware_source": "ZJT_START_DOC parser case 0x10009efe",
                "zjs_items": item_map(items),
            }
            model["objects"]["documents"].append(active_doc)
            messages.append({"queue": 3, "message": 1, "meaning": "start document"})
            effects.append(f"created document object {active_doc['id']} from {len(items)} ZjStream items")

        elif chunk.chunk_type == 0x02:
            items = parse_items(chunk.payload)
            active_page = {
                "id": f"page{len(model['objects']['pages'])}",
                "size": "0x50",
                "firmware_source": "ZJT_START_PAGE parser case 0x10009f86",
                "stock_metadata_bounds": metadata_bounds(chunk.payload, chunk.item_count, chunk.reserved),
                "zjs_items": item_map(items),
            }
            active_work = {
                "id": f"work{len(model['objects']['work_objects'])}",
                "size": "0x94",
                "firmware_source": "0x1000f228 hp1020_video_work_create_candidate",
                "owner_page": active_page["id"],
                "host_page_items": active_page["zjs_items"],
                "stock_metadata_status": active_page["stock_metadata_bounds"]["status"],
                "fields": {
                    **direct_work_fields(active_page["zjs_items"]),
                    "+0x50": [],
                    "+0x84": None,
                    "+0x88": None,
                    "+0x8c": None,
                    "+0x90": None,
                },
            }
            active_page["work_object"] = active_work["id"]
            model["objects"]["pages"].append(active_page)
            model["objects"]["work_objects"].append(active_work)
            messages.extend(
                [
                    {"queue": 3, "message": 3, "meaning": "start page / child page object"},
                    {"queue": 3, "message": 5, "meaning": "video work object ready"},
                ]
            )
            if active_page["stock_metadata_bounds"]["status"] != "bounded":
                effects.append("CAUTION: full-payload semantic model differs from stock declared-metadata allocation; paper/media values are not established on stock for this fixture")
            effects.append(f"created page object {active_page['id']} and work object {active_work['id']}")

        elif chunk.chunk_type == 0x04:
            bih = parse_bih(chunk.payload)
            runtime_block = {
                "source_chunk": chunk.index,
                "source_offset": f"0x{chunk.offset + 16:x}",
                "bytes": chunk.payload[:20].hex(" "),
                "+0x04": bih.get("xd"),
                "+0x08": bih.get("yd"),
                "+0x0c": bih.get("l0"),
                "+0x13": bih.get("options"),
                "decoded_bih": bih,
            }
            model["runtime_blocks"]["0x10023e28"] = runtime_block
            if active_work:
                active_work["fields"]["+0x84"] = runtime_block["+0x04"]
                active_work["fields"]["+0x88"] = runtime_block["+0x08"]
                active_work["fields"]["+0x8c"] = runtime_block["+0x0c"]
                active_work["fields"]["+0x90"] = runtime_block["+0x13"]
            messages.append({"queue": 3, "message": "0x29", "meaning": "JBIG BIH runtime setup"})
            effects.append("copied 20-byte BIH into runtime block 0x10023e28")
            if active_work:
                effects.append(f"seeded late video fields on {active_work['id']} at +0x84/+0x88/+0x8c/+0x90")

        elif chunk.chunk_type == 0x05:
            raster_node = {
                "id": f"raster{raster_index}",
                "node_size": "0x78",
                "firmware_source": "ZJT_JBIG_BID parser case 0x1000a014",
                "owner_work": active_work["id"] if active_work else None,
                "node_fields": {
                    "+0x00": None,
                    "+0x0c": "embedded payload at node +0x10",
                },
                "payload_fields": {
                    "+0x20": "unknown band/unit count candidate",
                    "+0x48": len(chunk.payload),
                    "+0x4c": "copied marker/ref flag candidate",
                    "+0x4e": active_work["fields"].get("+0x0c", 1) if active_work else 1,
                    "+0x50": 0,
                    "+0x54": {
                        "source": "ZJT_JBIG_BID payload",
                        "zjs_payload_offset": f"0x{chunk.offset + 16:x}",
                        "byte_count": len(chunk.payload),
                        "sha256_hint": "not stored; payload bytes are kept in the source .zjs",
                    },
                },
            }
            model["objects"]["raster_nodes"].append(raster_node)
            if active_work:
                active_work["fields"]["+0x50"].append(raster_node["id"])
            raster_index += 1
            messages.append({"queue": 3, "message": "0x2a", "meaning": "append raster/list node to active work +0x50"})
            effects.append(f"created raster list node {raster_node['id']} for {len(chunk.payload)} compressed bytes")
            if active_work:
                effects.append(f"appended {raster_node['id']} to {active_work['id']} field +0x50")

        elif chunk.chunk_type == 0x06:
            messages.append({"queue": 3, "message": "0x2b", "meaning": "end JBIG stream"})
            effects.append("closed current JBIG stream")

        elif chunk.chunk_type == 0x03:
            messages.append({"queue": 3, "message": 6, "meaning": "end page"})
            effects.append("marked active page complete")

        elif chunk.chunk_type == 0x01:
            messages.append({"queue": 3, "message": 2, "meaning": "end document"})
            effects.append("closed active document")

        elif chunk.chunk_type == 0x0A:
            messages.append({"queue": 3, "message": 8, "meaning": "end plane"})
            effects.append("handled plane end marker")

        else:
            effects.append("chunk type is outside the currently modeled HP 1020 daily print path")

        append_trace(model["trace"], chunk, f"{chunk.name} handled by parser target {chunk.parser_target}", messages, effects)

    active_work_objects = model["objects"]["work_objects"]
    final_work = active_work_objects[-1] if active_work_objects else None
    raster_list = final_work["fields"]["+0x50"] if final_work else []
    model["hardware_boundary"] = {
        "boundary": "VideoThread consumes work +0x50 and writes video/engine MMIO registers",
        "status": "offline model stops before MMIO",
        "next_firmware_functions": [
            "0x10015214 hp1020_video_render_or_dma_candidate",
            "0x100140f8 hp1020_video_refresh_raw_bands_candidate",
            "0x10015c68 hp1020_engine_status_io_candidate",
        ],
        "raster_nodes_ready_for_video": raster_list,
        "reason_to_stop": "From this point the original firmware touches motor/fuser/video hardware registers.",
    }
    return model


def render_markdown(model: dict[str, Any]) -> str:
    objects = model["objects"]
    docs = objects["documents"]
    pages = objects["pages"]
    works = objects["work_objects"]
    rasters = objects["raster_nodes"]
    runtime = model["runtime_blocks"].get("0x10023e28", {})

    lines = [
        "# HP 1020 Offline Print-Path Model",
        "",
        "This is an executable offline model of the normal HP LaserJet 1020/1020 Plus print path mapped from the firmware.",
        "It parses host-side ZjStream bytes and builds firmware-shaped document, page, work, and raster-list objects.",
        "",
        "It does not send data to the printer and it stops before any hardware register writes.",
        "",
        "## Input",
        "",
        f"- source: `{model['source']}`",
        f"- file bytes: `{model['file_bytes']}`",
        f"- ZjStream magic offset: `0x{model['magic_offset']:x}`",
        f"- parser entry modeled: `{model['parser_entry']}`",
        f"- JobMgr queue id: `{model['jobmgr_queue']}`",
        f"- trailing bytes after parsed stream: `{model['trailing_bytes']}`",
        "",
        "## Object Graph",
        "",
        f"- document objects: `{len(docs)}`",
        f"- page objects: `{len(pages)}`",
        f"- `0x94` video work objects: `{len(works)}`",
        f"- raster/list nodes under work `+0x50`: `{len(rasters)}`",
        "",
    ]

    if docs:
        lines.extend(["### Document Items", "", "| Item | Value |", "|---|---:|"])
        for key, value in docs[0]["zjs_items"].items():
            lines.append(f"| `{key}` | `{value}` |")
        lines.append("")

    if pages:
        lines.extend(["### Page Items", "", "| Item | Value |", "|---|---:|"])
        for key, value in pages[0]["zjs_items"].items():
            lines.append(f"| `{key}` | `{value}` |")
        lines.append("")

    if runtime:
        bih = runtime.get("decoded_bih", {})
        lines.extend(
            [
                "### BIH Runtime Block",
                "",
                "Firmware case `ZJT_JBIG_BIH -> JobMgr 0x29` copies the 20-byte BIH into runtime block `0x10023e28`.",
                "",
                "| Runtime field | Modeled value | Later work field |",
                "|---:|---:|---:|",
                f"| `+0x04` | `{runtime.get('+0x04')}` | `work +0x84` |",
                f"| `+0x08` | `{runtime.get('+0x08')}` | `work +0x88` |",
                f"| `+0x0c` | `{runtime.get('+0x0c')}` | `work +0x8c` |",
                f"| `+0x13` | `0x{int(runtime.get('+0x13', 0)):02x}` | `work +0x90` |",
                "",
                f"- decoded BIH: `XD={bih.get('xd')}`, `YD={bih.get('yd')}`, `L0={bih.get('l0')}`, `MX={bih.get('mx')}`, `MY={bih.get('my')}`, `options=0x{int(bih.get('options', 0)):02x}`",
                f"- raw BIH: `{runtime.get('bytes')}`",
                "",
            ]
        )

    if works:
        work = works[0]
        fields = work["fields"]
        lines.extend(
            [
                "### Video Work Object",
                "",
                f"- object id: `{work['id']}`",
                f"- size: `{work['size']}`",
                f"- owner page: `{work['owner_page']}`",
                "",
                "| Work offset | Modeled value | Meaning |",
                "|---:|---|---|",
                f"| `+0x0c` | `{fields.get('+0x0c')}` | copy/reference count candidate |",
                f"| `+0x22` | `{fields.get('+0x22')}` | VIDEO_BPP (NBIE is +0x12) |",
                f"| `+0x50` | `{', '.join(fields.get('+0x50', []))}` | raster list head/list content |",
                f"| `+0x84` | `{fields.get('+0x84')}` | BIH-derived video setup field |",
                f"| `+0x88` | `{fields.get('+0x88')}` | BIH-derived video setup field |",
                f"| `+0x8c` | `{fields.get('+0x8c')}` | BIH-derived video setup field |",
                f"| `+0x90` | `0x{int(fields.get('+0x90') or 0):02x}` | BIH options/mode byte |",
                "",
            ]
        )

    if rasters:
        lines.extend(["### Raster Nodes", "", "| Node | Compressed bytes | Source offset | Owner work |", "|---|---:|---:|---|"])
        for node in rasters:
            payload = node["payload_fields"]["+0x54"]
            lines.append(
                f"| `{node['id']}` | `{payload['byte_count']}` | `{payload['zjs_payload_offset']}` | `{node['owner_work']}` |"
            )
        lines.extend(
            [
                "",
                "Each modeled raster node uses the firmware shape identified from parser and video consumers:",
                "",
                "- node `+0x00`: next pointer",
                "- node `+0x0c`: payload pointer",
                "- payload `+0x48`: compressed raster byte count",
                "- payload `+0x4e`: retain/release counter",
                "- payload `+0x50`: source/retention mode",
                "- payload `+0x54`: compressed raster buffer pointer",
                "",
            ]
        )

    lines.extend(
        [
            "## Message Trace",
            "",
            "| Chunk | Type | Parser target | JobMgr messages | Object/model effects |",
            "|---:|---|---:|---|---|",
        ]
    )
    for entry in model["trace"]:
        messages = ", ".join(
            f"q{msg['queue']}:`{msg['message']}`" for msg in entry["jobmgr_messages"]
        )
        effects = "<br>".join(entry["effects"])
        lines.append(
            f"| `{entry['chunk_index']}` | `{entry['chunk_name']}` | `{entry['parser_target']}` | {messages or ''} | {effects} |"
        )

    boundary = model["hardware_boundary"]
    lines.extend(
        [
            "",
            "## Safe Stop Boundary",
            "",
            f"- boundary: {boundary['boundary']}",
            f"- model status: {boundary['status']}",
            f"- why stop here: {boundary['reason_to_stop']}",
            "",
            "Next firmware functions after this boundary:",
            "",
        ]
    )
    for function in boundary["next_firmware_functions"]:
        lines.append(f"- `{function}`")
    lines.extend(
        [
            "",
            "## What This Proves",
            "",
            "- The normal host print stream has been reduced to a concrete, replayable object/message model.",
            "- The model reaches the exact point where the original firmware would hand raster data to video/engine code.",
            "- The remaining replacement-firmware risk is no longer finding the print input path; it is safely reproducing the video/engine hardware side.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(model: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "print-path-model.json").write_text(json.dumps(model, indent=2, sort_keys=True) + "\n")
    (output_dir / "print-path-model.md").write_text(render_markdown(model) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zjs", type=Path, help="ZjStream input produced by foo2zjs-wrapper")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("analysis/open-firmware-model"),
        help="directory for print-path-model.md and print-path-model.json",
    )
    args = parser.parse_args()

    model = build_model(args.zjs)
    write_outputs(model, args.output_dir)
    print(f"Wrote {args.output_dir / 'print-path-model.md'}")
    print(f"Wrote {args.output_dir / 'print-path-model.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
