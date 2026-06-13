#!/usr/bin/env python3
"""Project modeled HP 1020 work-object fields onto unsafe video registers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
VARIANT_ROOT = REPO / "analysis/open-firmware-model/variants"
OUT_DIR = REPO / "analysis/hardware-boundary"
OUT_JSON = OUT_DIR / "video-register-projection.json"
OUT_MD = OUT_DIR / "video-register-projection.md"


def load_variant(path: Path) -> dict[str, Any]:
    model = json.loads(path.read_text())
    work = model["objects"]["work_objects"][0]["fields"]
    page = model["objects"]["pages"][0]["zjs_items"]
    raster = model["objects"]["raster_nodes"][0]["payload_fields"]
    return {
        "case": path.parent.name,
        "source": model["source"],
        "file_bytes": model["file_bytes"],
        "paper": page.get("ZJI_DMPAPER"),
        "copies": page.get("ZJI_DMCOPIES"),
        "resolution": f"{page.get('ZJI_RESOLUTION_X')}x{page.get('ZJI_RESOLUTION_Y')}",
        "video_x": page.get("ZJI_VIDEO_X"),
        "video_y": page.get("ZJI_VIDEO_Y"),
        "raster_x": page.get("ZJI_RASTER_X"),
        "raster_y": page.get("ZJI_RASTER_Y"),
        "projected_registers": {
            "0xb2000008": {
                "value": work.get("+0x84"),
                "source": "work +0x84 from BIH runtime block +0x04",
                "consumer": "0x10015214 hp1020_video_render_or_dma_candidate",
            },
            "0xb200000c": {
                "value": work.get("+0x88"),
                "source": "work +0x88 from BIH runtime block +0x08",
                "consumer": "0x10015214 hp1020_video_render_or_dma_candidate",
            },
            "0xb2000024": {
                "value": work.get("+0x8c"),
                "source": "work +0x8c from BIH runtime block +0x0c",
                "consumer": "0x10015214 hp1020_video_render_or_dma_candidate",
            },
            "0xb2000000": {
                "value": f"control derived from work +0x90=0x{int(work.get('+0x90') or 0):02x}, then OR 0x400",
                "source": "work +0x90 from BIH runtime block +0x13",
                "consumer": "0x10015214 hp1020_video_render_or_dma_candidate",
            },
            "0xb1000008/0xb1000108": {
                "value": "raster payload pointer plus video_state +0xbc window",
                "source": f"payload +0x54 points at {raster['+0x54']['byte_count']} compressed bytes",
                "consumer": "0x100140f8 hp1020_video_refresh_raw_bands_candidate",
            },
            "0xb100000c/0xb100010c": {
                "value": "flags/count from payload +0x20/+0x4c/+0x50",
                "source": "raster payload node under work +0x50",
                "consumer": "0x100140f8 hp1020_video_refresh_raw_bands_candidate",
            },
        },
    }


def build_projection() -> dict[str, Any]:
    variants = []
    for path in sorted(VARIANT_ROOT.glob("*/print-path-model.json")):
        variants.append(load_variant(path))
    return {
        "summary": "Projected unsafe hardware register writes from the offline print-path work-object model.",
        "status": "projection only; no printer contact and no MMIO writes",
        "variants": variants,
    }


def render_markdown(model: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 Video Register Projection",
        "",
        "This report projects the offline print-path model onto the first unsafe video register writes.",
        "",
        "It does not contact the printer. It answers: if the original firmware continued past our safe stop, which host-controlled values would reach video registers?",
        "",
        "## Projection Table",
        "",
        "| Case | Paper | Copies | Resolution | Raster X/Y | `0xb2000008` | `0xb200000c` | `0xb2000024` | `0xb2000000` control source |",
        "|---|---:|---:|---|---|---:|---:|---:|---|",
    ]
    for variant in model["variants"]:
        regs = variant["projected_registers"]
        lines.append(
            f"| `{variant['case']}` | `{variant['paper']}` | `{variant['copies']}` | `{variant['resolution']}` | "
            f"`{variant['raster_x']}`/`{variant['raster_y']}` | "
            f"`{regs['0xb2000008']['value']}` | `{regs['0xb200000c']['value']}` | `{regs['0xb2000024']['value']}` | "
            f"`{regs['0xb2000000']['value']}` |"
        )

    lines.extend(
        [
            "",
            "## Register Mapping",
            "",
            "| Register | Source in modeled object | Firmware consumer | Meaning |",
            "|---:|---|---:|---|",
            "| `0xb2000008` | `work +0x84` | `0x10015214` | BIH-derived horizontal/video descriptor field |",
            "| `0xb200000c` | `work +0x88` | `0x10015214` | BIH-derived vertical/video descriptor field |",
            "| `0xb2000024` | `work +0x8c` | `0x10015214` | BIH `L0`/band-height-like field |",
            "| `0xb2000000` | `work +0x90` | `0x10015214` | control word bits; firmware ORs `0x400` before writing |",
            "| `0xb1000008` / `0xb1000108` | raster payload `+0x54` | `0x100140f8` | raw-band buffer pointer/window writes |",
            "| `0xb100000c` / `0xb100010c` | raster payload `+0x20/+0x4c/+0x50` | `0x100140f8` | raw-band count and flag writes |",
            "",
            "## Safety Meaning",
            "",
            "The host print stream already controls values that flow directly into video transfer descriptors. That is fine inside HP's firmware because the surrounding state machines gate timing and hardware state. It is not safe to reproduce blindly in custom firmware.",
            "",
            "For a first custom firmware experiment, the rule remains: do not reach these projected writes. Stay on boot/USB identity only.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    model = build_projection()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(model, indent=2, sort_keys=True) + "\n")
    OUT_MD.write_text(render_markdown(model) + "\n")
    print(f"Wrote {OUT_MD.relative_to(REPO)}")
    print(f"Wrote {OUT_JSON.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
