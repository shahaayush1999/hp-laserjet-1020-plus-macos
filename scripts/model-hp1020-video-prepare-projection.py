#!/usr/bin/env python3
"""Project modeled print jobs onto the HP 1020 video-prepare setup path.

This is offline analysis only. It combines the generated ZjStream work-object
models with the lower-level video-prepare mode report so the normal host print
cases are tied to the dangerous 0xb100 setup path without touching hardware.
"""

from __future__ import annotations

import json
import struct
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
VARIANT_ROOT = ROOT_DIR / "analysis/open-firmware-model/variants"
PREPARE_MODES_JSON = ROOT_DIR / "analysis/hardware-boundary/video-prepare-modes.json"
SOURCE = ROOT_DIR / "analysis/dispatch-mmio/decompiled/10014910_hp1020_video_prepare_page_candidate.c"
ELF_PATH = ROOT_DIR / "analysis/sihp1020.elf"
OUT_JSON = ROOT_DIR / "analysis/hardware-boundary/video-prepare-projection.json"
OUT_MD = ROOT_DIR / "analysis/hardware-boundary/video-prepare-projection.md"

CHECKS = [
    ("stride_from_work_84", "uVar19 = (*(int *)(param_1 + 0x84) + 0x1fU & 0xffffffe0) >> 3"),
    ("callback_gate_datastore_and_work_36", "if ((iVar5 == 0) && (*(short *)(param_1 + 0x36) == 0))"),
    ("resolution_600_sets_two_output", "if (sVar18 == 600)"),
    ("resolution_1200_sets_four_output", "if (sVar18 != 0x4b0) goto LAB_10014ae0"),
    ("state_200_from_work_22", "*(uint *)(puVar15 + 200) = uVar7"),
    ("remaining_units_from_work_26", "*(uint *)(puVar15 + 0xd0) = (uint)*(ushort *)(param_1 + 0x26)"),
    ("mode_flag_from_work_74", "if (*(char *)(param_1 + 0x74) == '\\0')"),
    ("single_plane_600_secondary_branch", "if ((*(int *)PTR_DAT_100067c8 == 0) && (*(int *)(hp1020_video_state_ptr_word + 0xec) != 0))"),
    ("single_plane_600_two_output_table", "puVar11 = (undefined4 *)(PTR_DAT_100068b8 + *(int *)PTR_DAT_100067c8 * 0x10)"),
    ("vertical_pack_write", "*DAT_100068d8 = (uint)*(ushort *)(param_1 + 0x18) << 0x10 | uStack_2c"),
    ("stride_register_write", "*puVar1 = *puVar1 & uVar7 | uVar19"),
]


class ElfImage:
    def __init__(self, path: Path) -> None:
        self.data = path.read_bytes()
        if self.data[:4] != b"\x7fELF" or self.data[5] != 2:
            raise ValueError(f"{path} is not a big-endian ELF")
        phoff = struct.unpack(">I", self.data[28:32])[0]
        phentsize = struct.unpack(">H", self.data[42:44])[0]
        phnum = struct.unpack(">H", self.data[44:46])[0]
        self.load_segments: list[tuple[int, int, int]] = []
        for index in range(phnum):
            off = phoff + index * phentsize
            p_type, p_offset, p_vaddr, _p_paddr, p_filesz, _p_memsz, _p_flags, _p_align = struct.unpack(
                ">IIIIIIII", self.data[off : off + 32]
            )
            if p_type == 1:
                self.load_segments.append((p_offset, p_vaddr, p_filesz))

    def read_u32(self, addr: int) -> int:
        for p_offset, p_vaddr, p_filesz in self.load_segments:
            if p_vaddr <= addr <= p_vaddr + p_filesz - 4:
                offset = p_offset + (addr - p_vaddr)
                return struct.unpack(">I", self.data[offset : offset + 4])[0]
        raise ValueError(f"address 0x{addr:08x} is not file-backed")

    def read_words(self, addr: int, count: int) -> list[str]:
        return [fmt32(self.read_u32(addr + index * 4)) for index in range(count)]


def fmt32(value: int) -> str:
    return f"0x{value:08x}"


def align32(value: int) -> int:
    return (value + 0x1F) & ~0x1F


def read_variant(path: Path) -> dict[str, Any]:
    model = json.loads(path.read_text())
    work = model["objects"]["work_objects"][0]["fields"]
    page = model["objects"]["pages"][0]["zjs_items"]
    return {
        "case": path.parent.name,
        "work": work,
        "page": page,
    }


def timing_value(prepare_modes: dict[str, Any], *, lane_selector: int, datastore_zero: bool, resolution_x: int) -> dict[str, Any]:
    resolution_class = "300" if resolution_x == 300 else "not 300"
    for item in prepare_modes["timing_modes"]:
        if (
            item.get("lane_selector") == lane_selector
            and item.get("datastore_0x20_zero") is datastore_zero
            and item.get("resolution") == resolution_class
        ):
            return item
    raise KeyError((lane_selector, datastore_zero, resolution_class))


def projected_state(work: dict[str, Any], page: dict[str, Any], *, datastore_zero: bool, work_36_zero: bool) -> dict[str, Any]:
    work_84 = int(work.get("+0x84") or 0)
    resolution_x = int(page.get("ZJI_RESOLUTION_X") or 600)
    nbie = int(page.get("ZJI_NBIE") or work.get("+0x22") or 1)
    stride = align32(work_84) >> 3
    state_200 = nbie
    state_f4 = 0
    state_c4 = 1
    state_bc = stride
    callback_enabled = datastore_zero and work_36_zero
    callback_pointer = "unmodified"
    if callback_enabled and nbie == 1:
        if resolution_x == 300:
            callback_pointer = "cleared"
        elif resolution_x == 600:
            state_f4 = 2
            state_bc = stride << 1
            state_200 = 2
            callback_pointer = "600dpi callback table"
        elif resolution_x == 1200:
            state_f4 = 4
            state_bc = stride << 1
            state_c4 = 2
            state_200 = 4
            callback_pointer = "1200dpi callback table"
    return {
        "resolution_x": resolution_x,
        "resolution_y": int(page.get("ZJI_RESOLUTION_Y") or 600),
        "nbie": nbie,
        "work_plus_0x84": work_84,
        "stride_plus_0xb8": stride,
        "state_plus_0xbc": state_bc,
        "state_plus_0xc4": state_c4,
        "state_plus_0xf4": state_f4,
        "state_plus_0xc8_state_200": state_200,
        "callback_enabled": callback_enabled,
        "callback_pointer": callback_pointer,
        "unmodeled_inputs": ["work +0x18", "work +0x24", "work +0x26", "work +0x30", "work +0x32", "work +0x36"],
    }


def table_selection(
    elf: ElfImage,
    prepare_modes: dict[str, Any],
    state: dict[str, Any],
    *,
    lane_selector: int,
    secondary_output: bool,
) -> dict[str, Any]:
    literals = prepare_modes["literal_values"]
    resolution_x = state["resolution_x"]
    nbie = state["nbie"]
    state_200 = state["state_plus_0xc8_state_200"]
    if nbie == 1 and resolution_x == 300:
        if lane_selector == 0 and not secondary_output:
            name = "single_plane_300_default_table"
            base = int(literals[name], 16)
            words = elf.read_words(base, 2)
        else:
            name = "single_plane_300_lane1_table"
            base = int(literals[name], 16) + lane_selector * 8
            words = elf.read_words(base, 2)
    elif nbie == 1 and resolution_x == 600:
        if lane_selector == 0 and secondary_output:
            name = "single_plane_600_alt_table"
            base = int(literals[name], 16)
            words = elf.read_words(base, 4)
        elif state_200 == 2:
            name = "single_plane_600_two_output_table"
            base = int(literals[name], 16) + lane_selector * 0x10
            words = elf.read_words(base, 4)
        else:
            name = "single_plane_600_lane_table"
            base = int(literals[name], 16) + lane_selector * 8
            words = elf.read_words(base, 2)
    elif nbie == 1 and resolution_x == 1200:
        name = "single_plane_1200_table_sparse"
        base = int(literals["single_plane_1200_table"], 16)
        words = elf.read_words(base, 16)
    elif nbie == 2:
        if lane_selector == 0 and secondary_output:
            name = "two_plane_lane0_table"
            base = int(literals[name], 16)
        else:
            name = "two_plane_lane_table"
            base = int(literals[name], 16) + lane_selector * 0x10
        words = elf.read_words(base, 4)
    else:
        name = "no_table_branch_modeled"
        base = 0
        words = []
    return {
        "lane_selector": lane_selector,
        "secondary_output_state_plus_0xec_nonzero": secondary_output,
        "table": name,
        "base": fmt32(base) if base else "-",
        "words": words,
    }


def scenario_projection(elf: ElfImage, prepare_modes: dict[str, Any], variant: dict[str, Any]) -> dict[str, Any]:
    work = variant["work"]
    page = variant["page"]
    scenarios = []
    for datastore_zero in [True, False]:
        state = projected_state(work, page, datastore_zero=datastore_zero, work_36_zero=True)
        for lane_selector in [0, 1]:
            timing = timing_value(
                prepare_modes,
                lane_selector=lane_selector,
                datastore_zero=datastore_zero,
                resolution_x=state["resolution_x"],
            )
            for secondary_output in [False, True]:
                table = table_selection(
                    elf,
                    prepare_modes,
                    state,
                    lane_selector=lane_selector,
                    secondary_output=secondary_output,
                )
                scenarios.append(
                    {
                        "datastore_0x20_zero": datastore_zero,
                        "work_plus_0x36_assumed_zero": True,
                        "lane_selector": lane_selector,
                        "secondary_output_state_plus_0xec_nonzero": secondary_output,
                        "derived_state": state,
                        "timing_registers": timing,
                        "table_selection": table,
                    }
                )
    return {
        "case": variant["case"],
        "paper": page.get("ZJI_DMPAPER"),
        "resolution": f"{page.get('ZJI_RESOLUTION_X')}x{page.get('ZJI_RESOLUTION_Y')}",
        "raster_x": page.get("ZJI_RASTER_X"),
        "raster_y": page.get("ZJI_RASTER_Y"),
        "video_bpp": page.get("ZJI_VIDEO_BPP"),
        "work_plus_0x84": work.get("+0x84"),
        "scenarios": scenarios,
    }


def evidence_checks() -> list[dict[str, str]]:
    source = SOURCE.read_text(errors="replace")
    return [
        {
            "name": name,
            "status": "present" if needle in source else "missing",
            "needle": needle,
        }
        for name, needle in CHECKS
    ]


def build_report() -> dict[str, Any]:
    prepare_modes = json.loads(PREPARE_MODES_JSON.read_text())
    elf = ElfImage(ELF_PATH)
    variants = [read_variant(path) for path in sorted(VARIANT_ROOT.glob("*/print-path-model.json"))]
    projections = [scenario_projection(elf, prepare_modes, variant) for variant in variants]
    checks = evidence_checks()
    return {
        "summary": "Projection from generated print-path variants into video prepare 0xb100 setup choices.",
        "status": "pass" if all(item["status"] == "present" for item in checks) else "fail",
        "source_reports": [
            "analysis/open-firmware-model/variants/*/print-path-model.json",
            "analysis/hardware-boundary/video-prepare-modes.json",
        ],
        "projection_count": len(projections),
        "scenario_count": sum(len(item["scenarios"]) for item in projections),
        "projections": projections,
        "normal_path_summary": [
            "All current generated host variants use ZJI_NBIE=1 and 600x600 declared resolution.",
            "For datastore 0x20 == 0 and work +0x36 == 0, the prepare code promotes the video state to a two-output 600dpi setup: state +0xc8/200 = 2, +0xf4 = 2, and +0xbc = stride*2.",
            "The exact vertical offset and remaining-unit fields still depend on work offsets not yet included in the print-path model.",
        ],
        "checks": checks,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 Video Prepare Projection",
        "",
        "This is a generated offline projection. It does not contact the printer.",
        "",
        "## Result",
        "",
        f"- status: `{report['status']}`",
        f"- variants projected: `{report['projection_count']}`",
        f"- scenario rows: `{report['scenario_count']}`",
        "",
        "## Normal Path Summary",
        "",
    ]
    for item in report["normal_path_summary"]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## Variant Summary",
            "",
            "| Case | Resolution | Raster X/Y | Video BPP | Work +0x84 | Stride +0xb8 | Callback 600dpi state |",
            "|---|---|---|---:|---:|---:|---|",
        ]
    )
    for projection in report["projections"]:
        first_callback = next(
            row
            for row in projection["scenarios"]
            if row["datastore_0x20_zero"] and row["lane_selector"] == 0 and not row["secondary_output_state_plus_0xec_nonzero"]
        )
        state = first_callback["derived_state"]
        callback_state = (
            f"+0xc8/200={state['state_plus_0xc8_state_200']}, "
            f"+0xf4={state['state_plus_0xf4']}, +0xbc={state['state_plus_0xbc']}"
        )
        lines.append(
            f"| `{projection['case']}` | `{projection['resolution']}` | `{projection['raster_x']}`/`{projection['raster_y']}` | "
            f"`{projection['video_bpp']}` | `{projection['work_plus_0x84']}` | `{state['stride_plus_0xb8']}` | `{callback_state}` |"
        )

    lines.extend(
        [
            "",
            "## Setup Scenario Matrix",
            "",
            "| Case | Datastore 0x20 zero | Lane | Secondary +0xec | Timing register value | Table | Table words |",
            "|---|---|---:|---|---:|---|---|",
        ]
    )
    for projection in report["projections"]:
        for row in projection["scenarios"]:
            timing = row["timing_registers"]
            table = row["table_selection"]
            value = timing["value"]
            words = " ".join(f"`{word}`" for word in table["words"]) if table["words"] else "-"
            lines.append(
                f"| `{projection['case']}` | `{row['datastore_0x20_zero']}` | `{row['lane_selector']}` | "
                f"`{row['secondary_output_state_plus_0xec_nonzero']}` | `{value}` | `{table['table']}` | {words} |"
            )

    lines.extend(["", "## Evidence Checks", "", "| Check | Status | Needle |", "|---|---|---|"])
    for item in report["checks"]:
        needle = item["needle"].replace("|", "\\|")
        lines.append(f"| `{item['name']}` | `{item['status']}` | `{needle}` |")

    lines.extend(
        [
            "",
            "## Open Firmware Meaning",
            "",
            "- This narrows the normal host-generated print cases to a small set of 600dpi setup scenarios instead of the whole firmware branch space.",
            "- It still does not make 0xb100 safe to drive: vertical offsets, remaining-unit counts, and live status timing remain partly unmapped.",
            "- The practical use is planning and comparison, not upload.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    OUT_MD.write_text(render_markdown(report))
    print(f"status={report['status']} variants={report['projection_count']} scenarios={report['scenario_count']}")
    print(OUT_MD)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
