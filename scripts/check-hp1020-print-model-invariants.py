#!/usr/bin/env python3
"""Validate offline HP 1020 ZjStream print-path model invariants."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


EXPECTED_CHUNKS = [
    "ZJT_START_DOC",
    "ZJT_START_PAGE",
    "ZJT_JBIG_BIH",
    "ZJT_JBIG_BID",
    "ZJT_END_JBIG",
    "ZJT_END_PAGE",
    "ZJT_END_DOC",
]
EXPECTED_MESSAGES = ["1", "3", "5", "0x29", "0x2a", "0x2b", "6", "2"]
EXPECTED_BOUNDARY_FUNCTIONS = {
    "0x10015214 hp1020_video_render_or_dma_candidate",
    "0x100140f8 hp1020_video_refresh_raw_bands_candidate",
    "0x10015c68 hp1020_engine_status_io_candidate",
}


@dataclass(frozen=True)
class Check:
    case: str
    name: str
    severity: str
    detail: str


def model_case(path: Path) -> str:
    if path.parent.name == "open-firmware-model":
        return "base"
    return path.parent.name


def message_text(value: Any) -> str:
    return str(value)


def flattened_messages(model: dict[str, Any]) -> list[str]:
    messages: list[str] = []
    for entry in model["trace"]:
        for message in entry["jobmgr_messages"]:
            messages.append(message_text(message["message"]))
    return messages


def check_equal(case: str, checks: list[Check], name: str, expected: Any, actual: Any, detail: str) -> None:
    checks.append(
        Check(
            case,
            name,
            "watch" if expected == actual else "fail",
            detail if expected == actual else f"{detail}; expected {expected!r}, got {actual!r}",
        )
    )


def validate_model(path: Path) -> list[Check]:
    model = json.loads(path.read_text())
    case = model_case(path)
    checks: list[Check] = []

    objects = model["objects"]
    docs = objects["documents"]
    pages = objects["pages"]
    works = objects["work_objects"]
    rasters = objects["raster_nodes"]
    runtime = model["runtime_blocks"].get("0x10023e28", {})
    trace = model["trace"]
    chunk_names = [entry["chunk_name"] for entry in trace]

    check_equal(case, checks, "chunk_sequence", EXPECTED_CHUNKS, chunk_names, "parser must follow the daily print-path skeleton")
    check_equal(
        case,
        checks,
        "jobmgr_message_sequence",
        EXPECTED_MESSAGES,
        flattened_messages(model),
        "parser-to-JobMgr messages must preserve the modeled order",
    )
    check_equal(case, checks, "document_count", 1, len(docs), "single-page fixture should create one document")
    check_equal(case, checks, "page_count", 1, len(pages), "single-page fixture should create one page")
    check_equal(case, checks, "work_count", 1, len(works), "single-page fixture should create one video work object")
    check_equal(case, checks, "raster_count", 1, len(rasters), "single-page fixture should create one raster node")

    if pages and works:
        page_items = pages[0]["zjs_items"]
        work = works[0]
        fields = work["fields"]
        check_equal(case, checks, "work_copy_count", page_items.get("ZJI_DMCOPIES", 1), fields.get("+0x0c"), "work +0x0c tracks page copy count")
        check_equal(case, checks, "work_plane_count", page_items.get("ZJI_NBIE"), fields.get("+0x22"), "work +0x22 tracks page NBIE/plane count")
        check_equal(case, checks, "page_work_link", work["id"], pages[0].get("work_object"), "page object points at the modeled work object")

    if runtime and works:
        fields = works[0]["fields"]
        mappings = [
            ("+0x04", "+0x84"),
            ("+0x08", "+0x88"),
            ("+0x0c", "+0x8c"),
            ("+0x13", "+0x90"),
        ]
        for runtime_field, work_field in mappings:
            check_equal(
                case,
                checks,
                f"runtime_{runtime_field}_to_work_{work_field}",
                runtime.get(runtime_field),
                fields.get(work_field),
                f"BIH runtime {runtime_field} must seed work {work_field}",
            )

    if rasters and works:
        raster = rasters[0]
        payload = raster["payload_fields"]
        payload_ref = payload["+0x54"]
        work_rasters = works[0]["fields"].get("+0x50", [])
        check_equal(case, checks, "raster_owner", works[0]["id"], raster["owner_work"], "raster node owner matches active work")
        check_equal(case, checks, "raster_list_link", [raster["id"]], work_rasters, "work +0x50 contains the raster list node")
        check_equal(case, checks, "raster_payload_size", payload["+0x48"], payload_ref["byte_count"], "payload +0x48 matches compressed BID byte count")
        check_equal(case, checks, "raster_retain_count", works[0]["fields"].get("+0x0c"), payload["+0x4e"], "raster payload +0x4e tracks work copy/reference count")

    boundary = model["hardware_boundary"]
    boundary_functions = set(boundary.get("next_firmware_functions", []))
    check_equal(
        case,
        checks,
        "hardware_boundary_functions",
        EXPECTED_BOUNDARY_FUNCTIONS,
        boundary_functions,
        "safe-stop boundary must name the known unsafe video/engine consumers",
    )
    check_equal(
        case,
        checks,
        "hardware_boundary_rasters",
        works[0]["fields"].get("+0x50", []) if works else [],
        boundary.get("raster_nodes_ready_for_video", []),
        "hardware boundary raster list matches work +0x50",
    )

    return checks


def render_markdown(checks: list[Check]) -> str:
    fail_count = sum(check.severity == "fail" for check in checks)
    cases = sorted({check.case for check in checks})
    lines = [
        "# HP 1020 Print Model Invariant Check",
        "",
        f"- cases checked: `{len(cases)}`",
        f"- checks: `{len(checks)}`",
        f"- fail hits: `{fail_count}`",
        "",
        "## Case Summary",
        "",
        "| Case | Checks | Failures |",
        "|---|---:|---:|",
    ]
    for case in cases:
        subset = [check for check in checks if check.case == case]
        failures = sum(check.severity == "fail" for check in subset)
        lines.append(f"| `{case}` | `{len(subset)}` | `{failures}` |")

    lines.extend(["", "## Checks", "", "| Severity | Case | Check | Detail |", "|---|---|---|---|"])
    for check in checks:
        lines.append(f"| `{check.severity}` | `{check.case}` | `{check.name}` | {check.detail} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("models", nargs="+", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()

    checks: list[Check] = []
    for model_path in args.models:
        checks.extend(validate_model(model_path))

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(render_markdown(checks))
    else:
        print(render_markdown(checks), end="")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps([check.__dict__ for check in checks], indent=2, sort_keys=True) + "\n")
    return 1 if any(check.severity == "fail" for check in checks) else 0


if __name__ == "__main__":
    raise SystemExit(main())
