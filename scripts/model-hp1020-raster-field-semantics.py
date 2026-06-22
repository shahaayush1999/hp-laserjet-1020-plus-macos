#!/usr/bin/env python3
"""Generate host-to-raster-field semantics for the HP 1020 print path.

This is offline analysis only. It correlates the generated ZjStream print-path
models with the video consumer reports so the current replacement-firmware
boundary is stated as fields, not just function names.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
BASE_MODEL = ROOT_DIR / "analysis/open-firmware-model/print-path-model.json"
VARIANT_ROOT = ROOT_DIR / "analysis/open-firmware-model/variants"
OUT_JSON = ROOT_DIR / "analysis/open-firmware-model/raster-field-semantics.json"
OUT_MD = ROOT_DIR / "analysis/open-firmware-model/raster-field-semantics.md"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def fmt_value(value: Any) -> str:
    if isinstance(value, dict):
        if "byte_count" in value:
            return str(value["byte_count"])
        return json.dumps(value, sort_keys=True)
    if isinstance(value, list):
        return ", ".join(map(str, value))
    return str(value)


def model_paths() -> list[tuple[str, Path]]:
    paths: list[tuple[str, Path]] = [("base", BASE_MODEL)]
    for path in sorted(VARIANT_ROOT.glob("*/print-path-model.json")):
        paths.append((path.parent.name, path))
    return paths


def first_work(model: dict[str, Any]) -> dict[str, Any]:
    return model.get("objects", {}).get("work_objects", [{}])[0]


def first_raster(model: dict[str, Any]) -> dict[str, Any]:
    return model.get("objects", {}).get("raster_nodes", [{}])[0]


def first_runtime_block(model: dict[str, Any]) -> dict[str, Any]:
    blocks = model.get("runtime_blocks", {})
    if "0x10023e28" in blocks:
        return blocks["0x10023e28"]
    if blocks:
        return next(iter(blocks.values()))
    return {}


def collect_cases() -> list[dict[str, Any]]:
    rows = []
    for case, path in model_paths():
        model = read_json(path)
        work = first_work(model)
        work_fields = work.get("fields", {})
        raster = first_raster(model)
        payload = raster.get("payload_fields", {})
        runtime = first_runtime_block(model)
        decoded_bih = runtime.get("decoded_bih", {})
        rows.append(
            {
                "case": case,
                "source": str(path.relative_to(ROOT_DIR)),
                "file_bytes": model.get("file_bytes"),
                "page_items": work.get("host_page_items", {}),
                "runtime": runtime,
                "decoded_bih": decoded_bih,
                "work_fields": work_fields,
                "payload_fields": payload,
                "bid_bytes": payload.get("+0x54", {}).get("byte_count")
                if isinstance(payload.get("+0x54"), dict)
                else None,
            }
        )
    return rows


def values_for(rows: list[dict[str, Any]], section: str, field: str) -> list[Any]:
    return [row.get(section, {}).get(field) for row in rows]


def unique_values(values: list[Any]) -> list[Any]:
    unique: list[Any] = []
    for value in values:
        if value not in unique:
            unique.append(value)
    return unique


def check(name: str, ok: bool, detail: str) -> dict[str, str]:
    return {"name": name, "status": "present" if ok else "missing", "detail": detail}


def field_matrix(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        work = row["work_fields"]
        payload = row["payload_fields"]
        page = row["page_items"]
        bih = row["decoded_bih"]
        out.append(
            {
                "case": row["case"],
                "paper": page.get("ZJI_DMPAPER"),
                "resolution": f"{page.get('ZJI_RESOLUTION_X')}x{page.get('ZJI_RESOLUTION_Y')}",
                "video_xy": f"{page.get('ZJI_VIDEO_X')}/{page.get('ZJI_VIDEO_Y')}",
                "raster_xy": f"{page.get('ZJI_RASTER_X')}/{page.get('ZJI_RASTER_Y')}",
                "bih_xd_yd_l0_options": f"{bih.get('xd')}/{bih.get('yd')}/{bih.get('l0')}/0x{int(bih.get('options', 0)):02x}",
                "work_0x84_0x88_0x8c_0x90": f"{work.get('+0x84')}/{work.get('+0x88')}/{work.get('+0x8c')}/0x{int(work.get('+0x90', 0)):02x}",
                "payload_0x48": payload.get("+0x48"),
                "payload_0x4e": payload.get("+0x4e"),
                "payload_0x50": payload.get("+0x50"),
                "bid_bytes": row.get("bid_bytes"),
            }
        )
    return out


def build_report() -> dict[str, Any]:
    rows = collect_cases()
    work_84 = values_for(rows, "work_fields", "+0x84")
    work_88 = values_for(rows, "work_fields", "+0x88")
    payload_48 = values_for(rows, "payload_fields", "+0x48")
    payload_54_bytes = [row.get("bid_bytes") for row in rows]

    checks = [
        check("variant_models_present", len(rows) >= 11, f"{len(rows)} print-path model(s) loaded"),
        check(
            "bih_runtime_to_work_fields",
            all(
                row["runtime"].get("+0x04") == row["work_fields"].get("+0x84")
                and row["runtime"].get("+0x08") == row["work_fields"].get("+0x88")
                and row["runtime"].get("+0x0c") == row["work_fields"].get("+0x8c")
                and row["runtime"].get("+0x13") == row["work_fields"].get("+0x90")
                for row in rows
            ),
            "BIH runtime block +0x04/+0x08/+0x0c/+0x13 still maps to work +0x84/+0x88/+0x8c/+0x90",
        ),
        check(
            "bih_decoded_to_runtime_fields",
            all(
                row["decoded_bih"].get("xd") == row["runtime"].get("+0x04")
                and row["decoded_bih"].get("yd") == row["runtime"].get("+0x08")
                and row["decoded_bih"].get("l0") == row["runtime"].get("+0x0c")
                and row["decoded_bih"].get("options") == row["runtime"].get("+0x13")
                for row in rows
            ),
            "decoded JBIG BIH XD/YD/L0/options still matches the runtime block fields",
        ),
        check(
            "bid_payload_size_to_raster_fields",
            all(p48 == p54 for p48, p54 in zip(payload_48, payload_54_bytes)),
            "BID compressed byte count is present both at payload +0x48 and payload +0x54 byte_count",
        ),
        check(
            "host_variants_move_geometry",
            len(unique_values(work_84)) >= 4 and len(unique_values(work_88)) >= 3,
            "paper/resolution variants move the BIH-derived hardware geometry fields",
        ),
        check(
            "compressed_bytes_vary_by_host_case",
            len(unique_values(payload_48)) >= 4,
            "BID compressed payload size varies across generated host cases",
        ),
    ]

    status = "pass" if all(item["status"] == "present" for item in checks) else "fail"
    return {
        "summary": "Host ZjStream/JBIG fields that become firmware raster and video-hardware fields.",
        "status": status,
        "source_reports": [
            "analysis/open-firmware-model/print-path-model.json",
            "analysis/open-firmware-model/variants/*/print-path-model.json",
            "analysis/video-raster-consumer-report.md",
            "analysis/hardware-boundary/video-register-projection.json",
            "analysis/hardware-boundary/video-transfer-ring.json",
            "analysis/hardware-boundary/video-refill-topology.json",
        ],
        "field_semantics": [
            {
                "field": "work +0x84",
                "host_source": "JBIG BIH XD via runtime block 0x10023e28 +0x04",
                "stock_consumer": "0x10015214 video render writes 0xb2000008 and contributes to stride/window setup",
                "replacement_meaning": "horizontal raster/transfer geometry; must match host-generated compressed stream",
                "confidence": "high",
            },
            {
                "field": "work +0x88",
                "host_source": "JBIG BIH YD via runtime block 0x10023e28 +0x08",
                "stock_consumer": "0x10015214 video render writes 0xb200000c",
                "replacement_meaning": "vertical raster/page geometry",
                "confidence": "high",
            },
            {
                "field": "work +0x8c",
                "host_source": "JBIG BIH L0 via runtime block 0x10023e28 +0x0c",
                "stock_consumer": "0x10015214 video render writes 0xb2000024 and seeds band-height logic",
                "replacement_meaning": "JBIG stripe/band unit height used by the video transfer path",
                "confidence": "high",
            },
            {
                "field": "work +0x90",
                "host_source": "JBIG BIH options byte via runtime block 0x10023e28 +0x13",
                "stock_consumer": "0x10015214 video render derives 0xb2000000 control bits from it",
                "replacement_meaning": "mode/options bits for compressed raster transfer",
                "confidence": "medium-high",
            },
            {
                "field": "work +0x50",
                "host_source": "JobMgr list of ZJT_JBIG_BID raster nodes",
                "stock_consumer": "video render stores it at video state +0x9c; refill paths walk or derive from this raster stream",
                "replacement_meaning": "ordered compressed raster-band list for the page",
                "confidence": "high",
            },
            {
                "field": "payload +0x48",
                "host_source": "ZJT_JBIG_BID compressed payload byte count",
                "stock_consumer": "video render/refill uses it as transfer-length evidence",
                "replacement_meaning": "compressed-band byte length; bounds DMA/raw-band transfer",
                "confidence": "high",
            },
            {
                "field": "payload +0x4c",
                "host_source": "copied marker/ref flag candidate from parser payload +0x2c",
                "stock_consumer": "raw-band path turns nonzero into a hardware flag bit",
                "replacement_meaning": "per-band flag; exact semantics still need targeted evidence",
                "confidence": "medium",
            },
            {
                "field": "payload +0x4e",
                "host_source": "initialized from active work +0x0c",
                "stock_consumer": "cleanup/lifetime path decrements or forces this retain counter",
                "replacement_meaning": "raster node lifetime/reference count",
                "confidence": "medium-high",
            },
            {
                "field": "payload +0x50",
                "host_source": "initialized to zero for parser-owned BID data",
                "stock_consumer": "cleanup frees payload +0x54 unless this equals 2",
                "replacement_meaning": "source/ownership mode, not a print geometry field",
                "confidence": "medium-high",
            },
            {
                "field": "payload +0x54",
                "host_source": "pointer to ZJT_JBIG_BID compressed payload bytes",
                "stock_consumer": "video render/raw-band path writes or passes this pointer toward hardware transfer",
                "replacement_meaning": "compressed raster buffer pointer",
                "confidence": "high",
            },
        ],
        "case_matrix": field_matrix(rows),
        "checks": checks,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 Raster Field Semantics",
        "",
        "This is a generated offline model. It does not contact the printer.",
        "",
        "## Result",
        "",
        f"- status: `{report['status']}`",
        "- scope: host ZjStream/JBIG fields through firmware raster objects and into the video hardware boundary",
        "",
        "## Simple Readout",
        "",
        "The host-side print file already contains the page geometry and compressed raster bytes. The stock firmware mostly packages those values into work-object and raster-node fields, then the video path consumes those fields at the hardware boundary.",
        "",
        "For a narrow open replacement, these are the fields that matter before the dangerous engine/video timing work starts.",
        "",
        "## Source Reports",
        "",
    ]
    for source in report["source_reports"]:
        lines.append(f"- `{source}`")

    lines.extend(["", "## Field Semantics", "", "| Firmware field | Host source | Stock consumer | Replacement meaning | Confidence |", "|---|---|---|---|---|"])
    for item in report["field_semantics"]:
        lines.append(
            f"| `{item['field']}` | {item['host_source']} | {item['stock_consumer']} | {item['replacement_meaning']} | `{item['confidence']}` |"
        )

    lines.extend(["", "## Variant Matrix", "", "| Case | Paper | Res | Video X/Y | Raster X/Y | BIH XD/YD/L0/options | Work +0x84/+0x88/+0x8c/+0x90 | Payload +0x48 | Payload +0x4e | Payload +0x50 | BID bytes |", "|---|---:|---|---|---|---|---|---:|---:|---:|---:|"])
    for row in report["case_matrix"]:
        lines.append(
            "| `{case}` | `{paper}` | `{resolution}` | `{video_xy}` | `{raster_xy}` | `{bih_xd_yd_l0_options}` | `{work_0x84_0x88_0x8c_0x90}` | `{payload_0x48}` | `{payload_0x4e}` | `{payload_0x50}` | `{bid_bytes}` |".format(
                **row
            )
        )

    lines.extend(["", "## Checks", "", "| Check | Status | Detail |", "|---|---|---|"])
    for item in report["checks"]:
        lines.append(f"| `{item['name']}` | `{item['status']}` | {item['detail']} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    OUT_MD.write_text(render_markdown(report))
    print(f"status={report['status']} checks={len(report['checks'])} cases={len(report['case_matrix'])}")
    print(OUT_MD)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
