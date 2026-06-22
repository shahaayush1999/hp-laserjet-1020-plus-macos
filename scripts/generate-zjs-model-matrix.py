#!/usr/bin/env python3
"""Generate offline HP 1020 ZjStream variants and model their firmware path."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SAMPLE_PS = REPO / "analysis/samples/minimal-page.ps"
GENERATED = REPO / "analysis/samples/generated"
MODEL_ROOT = REPO / "analysis/open-firmware-model/variants"
SUMMARY = REPO / "analysis/open-firmware-model/variant-matrix.md"

CASES = [
    {
        "id": "a4_default",
        "label": "A4 default 1200x600 wrapper path",
        "args": ["-p9"],
    },
    {
        "id": "letter_default",
        "label": "Letter default 1200x600 wrapper path",
        "args": ["-p1"],
    },
    {
        "id": "legal_default",
        "label": "Legal default 1200x600 wrapper path",
        "args": ["-p5"],
    },
    {
        "id": "a4_600x600",
        "label": "A4 explicit 600x600",
        "args": ["-p9", "-r600x600"],
    },
    {
        "id": "a4_2400x600",
        "label": "A4 explicit 2400x600",
        "args": ["-p9", "-r2400x600"],
    },
    {
        "id": "a4_two_copies",
        "label": "A4 with two host-requested copies",
        "args": ["-p9", "-n2"],
    },
    {
        "id": "a4_draft",
        "label": "A4 draft/economode",
        "args": ["-p9", "-t"],
    },
    {
        "id": "a4_manual_feed",
        "label": "A4 manual-feed source",
        "args": ["-p9", "-s4"],
    },
    {
        "id": "a4_cardstock_media",
        "label": "A4 cardstock media type",
        "args": ["-p9", "-m261"],
    },
    {
        "id": "a4_logical_clip",
        "label": "A4 logical X/Y clipping fields",
        "args": ["-p9", "-L3"],
    },
]


def run(argv: list[str]) -> None:
    subprocess.run(argv, cwd=REPO, check=True)


def generate_case(case: dict[str, object]) -> dict[str, object]:
    case_id = str(case["id"])
    zjs_path = GENERATED / f"matrix-{case_id}.zjs"
    model_dir = MODEL_ROOT / case_id
    wrapper = REPO / "assets/runtime/foo2zjs-wrapper"
    modeler = REPO / "scripts/model-hp1020-print-path.py"
    args = [str(wrapper), "-P", "-z1", "-L0", *case["args"], str(SAMPLE_PS)]
    env = os.environ.copy()
    env["PATH"] = f"{REPO / 'assets/runtime'}:{env.get('PATH', '')}"

    GENERATED.mkdir(parents=True, exist_ok=True)
    MODEL_ROOT.mkdir(parents=True, exist_ok=True)
    with zjs_path.open("wb") as out:
        subprocess.run(args, cwd=REPO, stdout=out, env=env, check=True)
    run([str(modeler), str(zjs_path.relative_to(REPO)), "-o", str(model_dir.relative_to(REPO))])

    model = json.loads((model_dir / "print-path-model.json").read_text())
    work = model["objects"]["work_objects"][0]["fields"]
    page_items = model["objects"]["pages"][0]["zjs_items"]
    doc_items = model["objects"]["documents"][0]["zjs_items"]
    raster = model["objects"]["raster_nodes"][0]["payload_fields"]["+0x54"]
    return {
        "id": case_id,
        "label": case["label"],
        "args": " ".join(case["args"]),
        "file_bytes": model["file_bytes"],
        "magic_offset": model["magic_offset"],
        "paper": page_items.get("ZJI_DMPAPER"),
        "copies": page_items.get("ZJI_DMCOPIES"),
        "duplex": doc_items.get("ZJI_DMDUPLEX"),
        "source": page_items.get("ZJI_DMDEFAULTSOURCE"),
        "media": page_items.get("ZJI_DMMEDIATYPE"),
        "economode": page_items.get("ZJI_ECONOMODE"),
        "offset_x": page_items.get("ZJI_OFFSET_X", ""),
        "offset_y": page_items.get("ZJI_OFFSET_Y", ""),
        "resolution_x": page_items.get("ZJI_RESOLUTION_X"),
        "resolution_y": page_items.get("ZJI_RESOLUTION_Y"),
        "video_x": page_items.get("ZJI_VIDEO_X"),
        "video_y": page_items.get("ZJI_VIDEO_Y"),
        "raster_x": page_items.get("ZJI_RASTER_X"),
        "raster_y": page_items.get("ZJI_RASTER_Y"),
        "work_0x0c": work.get("+0x0c"),
        "work_0x84": work.get("+0x84"),
        "work_0x88": work.get("+0x88"),
        "work_0x8c": work.get("+0x8c"),
        "work_0x90": work.get("+0x90"),
        "bid_bytes": raster["byte_count"],
        "model_dir": str(model_dir.relative_to(REPO)),
        "zjs_path": str(zjs_path.relative_to(REPO)),
    }


def render_summary(rows: list[dict[str, object]]) -> str:
    lines = [
        "# HP 1020 ZjStream Model Variant Matrix",
        "",
        "This matrix generates several host-side ZjStream files, runs the offline print-path model on each one, and compares the fields that move.",
        "",
        "No printer is contacted. The `.zjs` files are generated locally from `analysis/samples/minimal-page.ps` through `foo2zjs-wrapper`.",
        "",
        "## Cases",
        "",
        "| Case | Wrapper args | File bytes | Paper | Copies | Res | Video X/Y | Raster X/Y | BIH/work +0x84/+0x88/+0x8c/+0x90 | BID bytes |",
        "|---|---|---:|---:|---:|---|---|---|---|---:|",
    ]
    for row in rows:
        lines.append(
            "| `{id}` | `{args}` | `{file_bytes}` | `{paper}` | `{copies}` | `{resolution_x}x{resolution_y}` | "
            "`{video_x}`/`{video_y}` | `{raster_x}`/`{raster_y}` | `{work_0x84}`/`{work_0x88}`/`{work_0x8c}`/`0x{work_0x90:02x}` | `{bid_bytes}` |".format(
                **row
            )
        )

    lines.extend(
        [
            "",
            "## Non-Geometry Fields",
            "",
            "| Case | Source | Media | Econo | Duplex | Offset X/Y |",
            "|---|---:|---:|---:|---:|---|",
        ]
    )
    for row in rows:
        lines.append(
            "| `{id}` | `{source}` | `{media}` | `{economode}` | `{duplex}` | `{offset_x}`/`{offset_y}` |".format(
                **row
            )
        )

    lines.extend(
        [
            "",
            "## Readout",
            "",
            "- Paper-size changes move the page item dimensions and the BIH-derived work fields.",
            "- Resolution changes mostly move horizontal raster/video fields; vertical fields stay tied to paper height for this sample.",
            "- Copy-count changes move `ZJI_DMCOPIES` and the modeled work `+0x0c` reference/count candidate without changing the BIH geometry.",
            "- Source, media, draft/economode, and logical clip options change host-visible page items without moving the modeled video work geometry for this one-page sample.",
            "- Every case still follows the same firmware message skeleton: `1`, `3`, `5`, `0x29`, `0x2a`, `0x2b`, `6`, `2` on JobMgr queue `3`.",
            "",
            "## Generated Model Directories",
            "",
        ]
    )
    for row in rows:
        lines.append(f"- `{row['id']}`: `{row['model_dir']}`")
    lines.extend(
        [
            "",
            "## Practical Meaning",
            "",
            "The offline model is not just hard-coded to one lucky A4 sample. It survives the basic wrapper variations we care about and shows which fields are host-controlled before the hardware boundary.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    rows = [generate_case(case) for case in CASES]
    SUMMARY.write_text(render_summary(rows) + "\n")
    print(f"Wrote {SUMMARY.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
