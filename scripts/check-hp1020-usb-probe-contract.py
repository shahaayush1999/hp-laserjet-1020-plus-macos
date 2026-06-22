#!/usr/bin/env python3
"""Check that an HP 1020 USB-only probe stays inside the mapped safe boundary."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


REPO = Path(__file__).resolve().parents[1]
DEFAULT_MMIO_MAP = REPO / "analysis/usb-path/usb-mmio-map.json"

BANNED_PATTERNS = [
    ("unsafe_mmio_video_raw", r"\b(?:0x)?b100[0-9a-fA-F]{4}\b", "video/raster raw-band MMIO family"),
    ("unsafe_mmio_video_transfer", r"\b(?:0x)?b200[0-9a-fA-F]{4}\b", "video transfer descriptor/control MMIO family"),
    ("unsafe_mmio_video_channel_a", r"\b(?:0x)?b204[0-9a-fA-F]{4}\b", "video transfer channel A MMIO family"),
    ("unsafe_mmio_video_channel_b", r"\b(?:0x)?b208[0-9a-fA-F]{4}\b", "video transfer channel B MMIO family"),
    ("unsafe_mmio_engine_status", r"\b(?:0x)?b050[0-9a-fA-F]{4}\b", "engine command/status MMIO family"),
    ("unsafe_mmio_engine_control", r"\b(?:0x)?b020[0-9a-fA-F]{4}\b", "engine/control MMIO family"),
    ("unsafe_func_video_render", r"\b(?:0x)?10015214\b|hp1020_video_render_or_dma_candidate", "video render/DMA path"),
    ("unsafe_func_raw_bands", r"\b(?:0x)?100140f8\b|hp1020_video_refresh_raw_bands_candidate", "raw-band feed path"),
    ("unsafe_func_video_prepare", r"\b(?:0x)?10014910\b|hp1020_video_prepare_page_candidate", "video prepare path"),
    ("unsafe_func_video_reset", r"\b(?:0x)?10015458\b|hp1020_video_reset_or_flush_candidate", "video reset/flush path"),
    ("unsafe_func_engine_io", r"\b(?:0x)?10015c68\b|hp1020_engine_status_io_candidate", "engine command/status path"),
    ("unsafe_func_engine_poll", r"\b(?:0x)?10015df8\b|hp1020_engine_status_poll_candidate", "engine status poll path"),
    ("unsafe_func_engine_preflight", r"\b(?:0x)?100160a8\b|hp1020_engine_preflight_candidate", "engine preflight path"),
    ("unsafe_func_engine_dispatch", r"\b(?:0x)?10016164\b|hp1020_engine_message_dispatch_candidate", "engine dispatch path"),
]

USB_MMIO_RE = re.compile(r"\b(?:0x)?b300[0-9a-fA-F]{4}\b")


@dataclass(frozen=True)
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
            yield from (p for p in sorted(path.rglob("*")) if p.is_file())
        else:
            yield path


def load_allowed_usb_registers(path: Path) -> set[str]:
    data = json.loads(path.read_text())
    registers = data.get("registers", {})
    if not registers:
        raise SystemExit(f"no registers found in {path}")
    return {reg.lower() for reg in registers}


def scan_file(path: Path, allowed_usb: set[str]) -> list[Hit]:
    hits: list[Hit] = []
    try:
        text = path.read_text(errors="replace")
    except UnicodeDecodeError:
        return hits

    for line_no, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        for kind, pattern, description in BANNED_PATTERNS:
            if re.search(pattern, line):
                hits.append(Hit(kind, "fail", description, str(path), line_no, stripped))

        for match in USB_MMIO_RE.finditer(line):
            raw_register = match.group(0).lower()
            register = raw_register if raw_register.startswith("0x") else f"0x{raw_register}"
            if register in allowed_usb:
                hits.append(
                    Hit(
                        "mapped_usb_mmio",
                        "watch",
                        f"mapped USB-controller register {register}",
                        str(path),
                        line_no,
                        stripped,
                    )
                )
            else:
                hits.append(
                    Hit(
                        "unmapped_usb_mmio",
                        "fail",
                        f"USB register {register} is not in the endpoint-0 static map",
                        str(path),
                        line_no,
                        stripped,
                    )
                )
    return hits


def render_text(hits: list[Hit], allowed_usb: set[str]) -> str:
    fail_count = sum(1 for hit in hits if hit.severity == "fail")
    watch_count = sum(1 for hit in hits if hit.severity == "watch")
    lines = [
        "# HP 1020 USB Probe Contract Scan",
        "",
        f"- allowed mapped USB registers: `{len(allowed_usb)}`",
        f"- fail hits: `{fail_count}`",
        f"- watch hits: `{watch_count}`",
        "",
    ]

    if not hits:
        lines.append("No USB, video, or engine MMIO/function references found.")
        return "\n".join(lines) + "\n"

    lines.extend(["| Severity | Kind | File:line | Description | Text |", "|---|---|---|---|---|"])
    for hit in hits:
        safe_text = hit.text.replace("|", "\\|")[:180]
        lines.append(
            f"| `{hit.severity}` | `{hit.kind}` | `{hit.path}:{hit.line}` | {hit.description} | `{safe_text}` |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="candidate source, assembly, map, or disassembly files/directories")
    parser.add_argument("--mmio-map", type=Path, default=DEFAULT_MMIO_MAP, help="USB MMIO map JSON")
    parser.add_argument("-o", "--output", type=Path, help="write markdown report")
    parser.add_argument("--json", type=Path, help="write JSON hit list")
    parser.add_argument("--allow-fail", action="store_true", help="exit 0 even if fail hits are found")
    args = parser.parse_args()

    allowed_usb = load_allowed_usb_registers(args.mmio_map)
    hits: list[Hit] = []
    for file_path in iter_files(args.paths):
        hits.extend(scan_file(file_path, allowed_usb))

    hits.sort(key=lambda hit: (hit.severity != "fail", hit.path, hit.line, hit.kind))
    report = render_text(hits, allowed_usb)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report)
    else:
        print(report, end="")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps([hit.__dict__ for hit in hits], indent=2, sort_keys=True) + "\n")

    has_fail = any(hit.severity == "fail" for hit in hits)
    return 1 if has_fail and not args.allow_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
