#!/usr/bin/env python3
"""Model HP 1020 video chunk sizing and raw-band flag encoding.

This is offline analysis only. It tightens the static meaning of video state
+0xcc and the small 0x1001b668 helper used by prepare/raw-band paths.
"""

from __future__ import annotations

import json
import struct
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
ELF_PATH = ROOT_DIR / "analysis/sihp1020.elf"
OUT_JSON = ROOT_DIR / "analysis/hardware-boundary/video-chunk-sizing.json"
OUT_MD = ROOT_DIR / "analysis/hardware-boundary/video-chunk-sizing.md"

INPUTS = {
    "raster_fields": ROOT_DIR / "analysis/open-firmware-model/raster-field-semantics.json",
    "prepare_projection": ROOT_DIR / "analysis/hardware-boundary/video-prepare-projection.json",
}

SOURCES = {
    "prepare": ROOT_DIR / "analysis/dispatch-mmio/decompiled/10014910_hp1020_video_prepare_page_candidate.c",
    "band_queue": ROOT_DIR / "analysis/zjs-parser-boundary/decompiled/10013f34_hp1020_video_band_queue_or_list_candidate.c",
    "raw_refresh": ROOT_DIR / "analysis/zjs-parser-boundary/decompiled/100140f8_hp1020_video_refresh_raw_bands_candidate.c",
    "division_helper": ROOT_DIR / "analysis/message-producers/producer-decompiled/1001b668_FUN_1001b668.c",
}

CONSTANT_ADDRS = {
    "chunk_budget_bytes_DAT_10005dc8": 0x10005DC8,
    "secondary_budget_DAT_10005ddc": 0x10005DDC,
    "high_bit_DAT_10005e34": 0x10005E34,
    "clear_high_bit_DAT_1000628c": 0x1000628C,
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def read_u32_from_elf(addr: int) -> int:
    data = ELF_PATH.read_bytes()
    phoff = struct.unpack(">I", data[28:32])[0]
    phentsize = struct.unpack(">H", data[42:44])[0]
    phnum = struct.unpack(">H", data[44:46])[0]
    for index in range(phnum):
        off = phoff + index * phentsize
        p_type, p_offset, p_vaddr, _p_paddr, p_filesz, _p_memsz, _p_flags, _p_align = struct.unpack(
            ">IIIIIIII", data[off : off + 32]
        )
        if p_type == 1 and p_vaddr <= addr <= p_vaddr + p_filesz - 4:
            file_off = p_offset + addr - p_vaddr
            return struct.unpack(">I", data[file_off : file_off + 4])[0]
    raise ValueError(f"address 0x{addr:08x} is not file-backed")


def unsigned_divide(numerator: int, denominator: int) -> int:
    if denominator == 0:
        return 0
    if denominator == 1:
        return numerator
    return numerator // denominator


def round_down_to_four(value: int) -> int:
    return value & 0xFFFFFFFC


def check(name: str, ok: bool, detail: str) -> dict[str, str]:
    return {"name": name, "status": "present" if ok else "missing", "detail": detail}


def find_case(rows: list[dict[str, Any]], case: str) -> dict[str, Any]:
    for row in rows:
        if row.get("case") == case:
            return row
    return {}


def build_case_rows(raster_fields: dict[str, Any], constants: dict[str, int]) -> list[dict[str, Any]]:
    rows = []
    budget = constants["chunk_budget_bytes_DAT_10005dc8"]
    for case in raster_fields.get("case_matrix", []):
        work = case.get("work_0x84_0x88_0x8c_0x90", "0/0/0/0x00").split("/")
        width = int(work[0])
        stride = ((width + 0x1F) & 0xFFFFFFE0) >> 3
        quotient_units = unsigned_divide(budget, stride)
        max_chunk_units = round_down_to_four(quotient_units)
        rows.append(
            {
                "case": case.get("case"),
                "work_plus_0x84": width,
                "stride_plus_0xb8": stride,
                "floor_div_8192_by_stride": quotient_units,
                "max_chunk_units_plus_0xcc": max_chunk_units,
                "channel_b_length_formula": f"min(+0xcc,+0xd0) * {stride}",
                "payload_0x48": case.get("payload_0x48"),
            }
        )
    return rows


def flag_scenarios() -> list[dict[str, Any]]:
    scenarios = []
    for units, c4, final_flag, secondary in [(4, 1, 0, 0), (4, 1, 1, 0), (4, 1, 1, 1), (5, 2, 0, 1), (7, 2, 1, 1)]:
        encoded = unsigned_divide(units, c4)
        flags = encoded | (int(bool(final_flag)) << 24) | (int(bool(secondary)) << 25)
        scenarios.append(
            {
                "units": units,
                "state_plus_0xc4": c4,
                "final_flag": final_flag,
                "secondary_or_source_flag": secondary,
                "encoded_units": encoded,
                "raw_band_flag_word": f"0x{flags:08x}",
            }
        )
    return scenarios


def evidence_checks(sources: dict[str, str], constants: dict[str, int], rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    a4_default = find_case(rows, "a4_default")
    return [
        check(
            "division_helper_zero_one_cases_visible",
            "if (param_2 < 2)" in sources["division_helper"]
            and "return param_1;" in sources["division_helper"]
            and "return 0;" in sources["division_helper"],
            "0x1001b668 exposes exact divisor 0/1 behavior despite bad decompiler flow after that",
        ),
        check(
            "prepare_computes_stride_from_work_0x84",
            "(*(int *)(param_1 + 0x84) + 0x1fU & 0xffffffe0) >> 3" in sources["prepare"],
            "prepare derives stride +0xb8 from work +0x84 rounded to 32 then divided by 8",
        ),
        check(
            "prepare_computes_cc_from_budget_and_stride",
            "uVar7 = FUN_1001b668(uVar6,uVar19)" in sources["prepare"]
            and "*(uint *)(puVar15 + 0xcc) = uVar7 & 0xfffffffc" in sources["prepare"],
            "prepare computes +0xcc from helper(chunk budget, stride) rounded down to a multiple of 4",
        ),
        check(
            "prepare_copies_remaining_units_from_work_0x26",
            "*(uint *)(puVar15 + 0xd0) = (uint)*(ushort *)(param_1 + 0x26)" in sources["prepare"]
            and "*(uint *)(puVar15 + 0xd4) = (uint)*(ushort *)(param_1 + 0x26)" in sources["prepare"],
            "prepare copies work +0x26 into remaining counters +0xd0/+0xd4",
        ),
        check(
            "raw_band_uses_helper_for_flag_encoding",
            "FUN_1001b668(uVar8 >> 1,uVar11)" in sources["band_queue"]
            and "FUN_1001b668(uVar11,uVar12)" in sources["band_queue"]
            and "FUN_1001b668(uVar1 >> 1,uVar10)" in sources["raw_refresh"]
            and "FUN_1001b668(uVar2,uVar10)" in sources["raw_refresh"],
            "normal queue and alternate raw refresh both use the helper before raw-band flag writes",
        ),
        check(
            "known_constants_read",
            constants["chunk_budget_bytes_DAT_10005dc8"] == 8192
            and constants["secondary_budget_DAT_10005ddc"] == 2048
            and constants["high_bit_DAT_10005e34"] == 0x80000000
            and constants["clear_high_bit_DAT_1000628c"] == 0x7FFFFFFF,
            "ELF constants for chunk budget and high-bit masks match current reports",
        ),
        check(
            "a4_default_chunk_projection",
            a4_default.get("stride_plus_0xb8") == 1200 and a4_default.get("max_chunk_units_plus_0xcc") == 4,
            "a4_default projects to stride 1200 and +0xcc max chunk units 4 under verified unsigned floor division",
        ),
    ]


def build_report() -> dict[str, Any]:
    raster_fields = read_json(INPUTS["raster_fields"])
    prepare_projection = read_json(INPUTS["prepare_projection"])
    sources = {name: path.read_text(errors="replace") for name, path in SOURCES.items()}
    constants = {name: read_u32_from_elf(addr) for name, addr in CONSTANT_ADDRS.items()}
    rows = build_case_rows(raster_fields, constants)
    checks = evidence_checks(sources, constants, rows)
    status = "pass" if all(item["status"] == "present" for item in checks) else "fail"
    return {
        "summary": "Video chunk sizing and raw-band flag encoding model.",
        "status": status,
        "source_reports": {
            "raster_fields": str(INPUTS["raster_fields"].relative_to(ROOT_DIR)),
            "prepare_projection": str(INPUTS["prepare_projection"].relative_to(ROOT_DIR)),
        },
        "source_status": {
            "raster_fields": raster_fields.get("status"),
            "prepare_projection": prepare_projection.get("status"),
        },
        "helper_contract": {
            "function": "0x1001b668",
            "working_name": "unsigned_divide",
            "exact_cases": {"denominator_0": 0, "denominator_1": "numerator"},
            "verified_behavior": "for denominator >= 2, returns floor(numerator / denominator)",
            "evidence": "Complete ELF-matched decode and independent instruction execution are recorded in video-helper-disassembly.md.",
        },
        "constants": constants,
        "case_matrix": rows,
        "flag_encoding_scenarios": flag_scenarios(),
        "field_conclusions": [
            "+0xb8 is stride bytes: ((work +0x84 + 31) & ~31) >> 3.",
            "+0xcc is a maximum chunk-unit cap: floor_div(8192, stride) rounded down to a multiple of 4.",
            "+0xd0/+0xd4 are copied from work +0x26 and then decremented by the refill helper.",
            "Raw-band flag words use unsigned floor-divided units ORed with final/secondary bits; physical interpretation remains uncalibrated.",
        ],
        "checks": checks,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 Video Chunk Sizing",
        "",
        "This is a generated offline model. It does not contact the printer.",
        "",
        "## Result",
        "",
        f"- status: `{report['status']}`",
        "- scope: video state `+0xcc/+0xd0` sizing and raw-band flag helper behavior",
        "",
        "## Verified Helper",
        "",
    ]
    helper = report["helper_contract"]
    lines.extend(
        [
            f"- function: `{helper['function']}`",
            f"- working name: `{helper['working_name']}`",
            f"- exact denominator 0 case: `{helper['exact_cases']['denominator_0']}`",
            f"- exact denominator 1 case: `{helper['exact_cases']['denominator_1']}`",
            f"- verified behavior: {helper['verified_behavior']}",
            f"- evidence: {helper['evidence']}",
            "",
            "## Constants",
            "",
            "| Name | Value |",
            "|---|---:|",
        ]
    )
    for name, value in report["constants"].items():
        lines.append(f"| `{name}` | `{value}` / `0x{value:08x}` |")

    lines.extend(["", "## Chunk Projection", "", "| Case | Work +0x84 | Stride +0xb8 | floor(8192/stride) | +0xcc max chunk units | Channel-B length formula | Payload +0x48 |", "|---|---:|---:|---:|---:|---|---:|"])
    for row in report["case_matrix"]:
        lines.append(
            "| `{case}` | `{work_plus_0x84}` | `{stride_plus_0xb8}` | `{floor_div_8192_by_stride}` | `{max_chunk_units_plus_0xcc}` | `{channel_b_length_formula}` | `{payload_0x48}` |".format(
                **row
            )
        )

    lines.extend(["", "## Flag Encoding Scenarios", "", "| Units | +0xc4 | Final | Secondary | Encoded units | Flag word |", "|---:|---:|---:|---:|---:|---:|"])
    for row in report["flag_encoding_scenarios"]:
        lines.append(
            "| `{units}` | `{state_plus_0xc4}` | `{final_flag}` | `{secondary_or_source_flag}` | `{encoded_units}` | `{raw_band_flag_word}` |".format(
                **row
            )
        )

    lines.extend(["", "## Field Conclusions", ""])
    for item in report["field_conclusions"]:
        lines.append(f"- {item}")

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
