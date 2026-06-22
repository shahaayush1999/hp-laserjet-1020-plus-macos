#!/usr/bin/env python3
"""Model HP 1020 USB GET_DESCRIPTOR responses from extracted firmware descriptors."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]


def parse_hex(text: str) -> bytes:
    return bytes.fromhex(text)


def string_descriptor(text: str) -> bytes:
    body = text.encode("utf-16le")
    if len(body) + 2 > 255:
        raise ValueError("USB string descriptor too long")
    return bytes([len(body) + 2, 3]) + body


def langid_descriptor(langid: int = 0x0409) -> bytes:
    return bytes([4, 3]) + langid.to_bytes(2, "little")


def clip(data: bytes, length: int) -> bytes:
    return data[:length]


def hexbytes(data: bytes) -> str:
    return data.hex(" ")


def descriptor_cases(extraction: dict[str, Any]) -> list[dict[str, Any]]:
    devices = [parse_hex(item["raw_hex"]) for item in extraction["device_descriptors"]]
    configs = [parse_hex(item["raw_hex"]) for item in extraction["config_descriptors"]]
    strings = {item["text"]: item for item in extraction["known_strings"]}

    cases: list[dict[str, Any]] = []
    if devices:
        cases.append(
            {
                "name": "GET_DESCRIPTOR DEVICE",
                "setup": "80 06 00 01 00 00 12 00",
                "source": f"stock device descriptor at 0x{extraction['device_descriptors'][0]['vaddr']:08x}",
                "response": devices[0],
            }
        )
    if configs:
        cases.append(
            {
                "name": "GET_DESCRIPTOR CONFIG high-speed-style",
                "setup": "80 06 00 02 00 00 20 00",
                "source": f"stock config descriptor at 0x{extraction['config_descriptors'][0]['vaddr']:08x}",
                "response": configs[0],
            }
        )
        if len(configs) > 1:
            cases.append(
                {
                    "name": "GET_DESCRIPTOR CONFIG full-speed-style",
                    "setup": "80 06 00 02 00 00 20 00",
                    "source": f"stock config descriptor at 0x{extraction['config_descriptors'][1]['vaddr']:08x}",
                    "response": configs[1],
                }
            )

    if "Hewlett-Packard" in strings:
        cases.append(
            {
                "name": "GET_DESCRIPTOR STRING index 1 manufacturer",
                "setup": "80 06 01 03 09 04 ff 00",
                "source": "stock ASCII identity string",
                "response": string_descriptor("Hewlett-Packard"),
            }
        )
    if "HP LaserJet 1020" in strings:
        cases.append(
            {
                "name": "GET_DESCRIPTOR STRING index 2 product",
                "setup": "80 06 02 03 09 04 ff 00",
                "source": "stock ASCII identity string",
                "response": string_descriptor("HP LaserJet 1020"),
            }
        )

    cases.append(
        {
            "name": "GET_DESCRIPTOR STRING index 0 language",
            "setup": "80 06 00 03 00 00 04 00",
            "source": "standard USB English language descriptor model",
            "response": langid_descriptor(),
        }
    )
    cases.append(
        {
            "name": "FUTURE OPEN MARKER STRING example",
            "setup": "80 06 02 03 09 04 ff 00",
            "source": "not stock firmware; byte model for a future open marker",
            "response": string_descriptor("HP1020 OPEN MARKER"),
        }
    )
    return cases


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 USB Descriptor Response Model",
        "",
        "This is a byte-level model of standard USB `GET_DESCRIPTOR` responses using",
        "the descriptors extracted from the stock firmware. It does not emulate USB",
        "controller state, interrupts, DMA, endpoint setup, or timing.",
        "",
        "## Response Cases",
        "",
        "| Case | Setup Packet | Response Bytes | Source |",
        "| --- | --- | ---: | --- |",
    ]
    for case in report["cases"]:
        response = case["response"]
        lines.append(
            f"| {case['name']} | `{case['setup']}` | `{len(response)}` | {case['source']} |"
        )
        lines.append(f"|  | response | `{hexbytes(response)}` |  |")

    lines.extend(
        [
            "",
            "## Meaning",
            "",
            "This narrows the future open USB marker target to a simple byte contract:",
            "",
            "- receive a standard control request on endpoint 0",
            "- recognize descriptor type/index",
            "- return one of these byte strings, clipped to host `wLength`",
            "- avoid all engine/video hardware",
            "",
            "The hard part remains the USB controller plumbing around those bytes, not the",
            "descriptor payload itself.",
            "",
            "## Current Use",
            "",
            "Use this model as a reference when reading the stock USB setup-handler blocks",
            "or when designing a future open firmware USB-only marker. Do not treat it as",
            "a hardware-ready firmware implementation.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--extraction-json",
        type=Path,
        default=ROOT_DIR / "analysis/usb-path/usb-descriptor-extraction.json",
    )
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    args = parser.parse_args()

    extraction = json.loads(args.extraction_json.read_text())
    cases = descriptor_cases(extraction)
    report = {
        "extraction_json": str(args.extraction_json),
        "cases": [
            {
                "name": case["name"],
                "setup": case["setup"],
                "source": case["source"],
                "response_hex": hexbytes(case["response"]),
                "response_bytes": len(case["response"]),
            }
            for case in cases
        ],
    }
    renderable = {
        "extraction_json": str(args.extraction_json),
        "cases": cases,
    }

    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(renderable) + "\n")

    print(f"response_cases={len(cases)}")
    for case in cases:
        print(f"{case['name']}: {len(case['response'])} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
