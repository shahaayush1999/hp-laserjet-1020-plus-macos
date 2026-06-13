#!/usr/bin/env python3
"""Scan candidate HP 1020 custom-firmware text for known unsafe hardware paths."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


BANNED_PATTERNS = [
    ("unsafe_mmio_video_raw", r"0xb100[0-9a-fA-F]{4}", "video/raster raw-band MMIO family"),
    ("unsafe_mmio_video_transfer", r"0xb200[0-9a-fA-F]{4}", "video transfer descriptor/control MMIO family"),
    ("unsafe_mmio_video_channel_a", r"0xb204[0-9a-fA-F]{4}", "video transfer channel A MMIO family"),
    ("unsafe_mmio_video_channel_b", r"0xb208[0-9a-fA-F]{4}", "video transfer channel B MMIO family"),
    ("unsafe_mmio_engine_status", r"0xb050[0-9a-fA-F]{4}", "engine command/status MMIO family"),
    ("unsafe_mmio_engine_control", r"0xb020[0-9a-fA-F]{4}", "engine/control MMIO family"),
    ("unsafe_func_video_render", r"\b(?:0x)?10015214\b|hp1020_video_render_or_dma_candidate", "video render/DMA path"),
    ("unsafe_func_raw_bands", r"\b(?:0x)?100140f8\b|hp1020_video_refresh_raw_bands_candidate", "raw-band feed path"),
    ("unsafe_func_video_prepare", r"\b(?:0x)?10014910\b|hp1020_video_prepare_page_candidate", "video prepare path"),
    ("unsafe_func_video_reset", r"\b(?:0x)?10015458\b|hp1020_video_reset_or_flush_candidate", "video reset/flush path"),
    ("unsafe_func_engine_io", r"\b(?:0x)?10015c68\b|hp1020_engine_status_io_candidate", "engine command/status path"),
    ("unsafe_func_engine_poll", r"\b(?:0x)?10015df8\b|hp1020_engine_status_poll_candidate", "engine status poll path"),
    ("unsafe_func_engine_preflight", r"\b(?:0x)?100160a8\b|hp1020_engine_preflight_candidate", "engine preflight path"),
    ("unsafe_func_engine_dispatch", r"\b(?:0x)?10016164\b|hp1020_engine_message_dispatch_candidate", "engine dispatch path"),
]

WATCH_PATTERNS = [
    ("medium_mmio_boot_timer", r"0xb0(?:30|70|80)[0-9a-fA-F]{4}", "boot/timer/diagnostic MMIO family"),
    ("usb_mmio", r"0xb30[0-9][0-9a-fA-F]{4}", "USB-controller MMIO family; allowed only for a USB-only probe"),
    ("engine_queue_page_message", r"queue\s*1.*(?:0x0b|11)|(?:0x0b|11).*queue\s*1", "possible engine queue page-work message"),
]


@dataclass
class Hit:
    kind: str
    severity: str
    description: str
    path: str
    line: int
    text: str


def iter_files(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        if path.is_dir():
            yield from (p for p in path.rglob("*") if p.is_file())
        else:
            yield path


def scan_file(path: Path) -> list[Hit]:
    hits: list[Hit] = []
    try:
        text = path.read_text(errors="replace")
    except UnicodeDecodeError:
        return hits
    for line_no, line in enumerate(text.splitlines(), 1):
        for kind, pattern, description in BANNED_PATTERNS:
            if re.search(pattern, line):
                hits.append(Hit(kind, "fail", description, str(path), line_no, line.strip()))
        for kind, pattern, description in WATCH_PATTERNS:
            if re.search(pattern, line, flags=re.IGNORECASE):
                hits.append(Hit(kind, "watch", description, str(path), line_no, line.strip()))
    return hits


def render_text(hits: list[Hit]) -> str:
    fail_count = sum(1 for hit in hits if hit.severity == "fail")
    watch_count = sum(1 for hit in hits if hit.severity == "watch")
    lines = [
        "# HP 1020 Custom Firmware Safety Scan",
        "",
        f"- fail hits: `{fail_count}`",
        f"- watch hits: `{watch_count}`",
        "",
    ]
    if not hits:
        lines.append("No known unsafe hardware-boundary patterns found.")
        return "\n".join(lines) + "\n"

    lines.extend(["| Severity | Kind | File:line | Description | Text |", "|---|---|---|---|---|"])
    for hit in hits:
        safe_text = hit.text.replace("|", "\\|")[:160]
        lines.append(
            f"| `{hit.severity}` | `{hit.kind}` | `{hit.path}:{hit.line}` | {hit.description} | `{safe_text}` |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="candidate source, assembly, map, or disassembly files/directories")
    parser.add_argument("-o", "--output", type=Path, help="write markdown report")
    parser.add_argument("--json", type=Path, help="write JSON hit list")
    parser.add_argument("--allow-unsafe", action="store_true", help="exit 0 even if fail hits are found")
    args = parser.parse_args()

    hits: list[Hit] = []
    for file_path in iter_files(args.paths):
        hits.extend(scan_file(file_path))

    hits.sort(key=lambda hit: (hit.severity != "fail", hit.path, hit.line, hit.kind))
    report = render_text(hits)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report)
    else:
        print(report, end="")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps([hit.__dict__ for hit in hits], indent=2, sort_keys=True) + "\n")

    has_fail = any(hit.severity == "fail" for hit in hits)
    return 1 if has_fail and not args.allow_unsafe else 0


if __name__ == "__main__":
    raise SystemExit(main())
