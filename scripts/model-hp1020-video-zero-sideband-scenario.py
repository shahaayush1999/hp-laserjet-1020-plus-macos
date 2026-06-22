#!/usr/bin/env python3
"""Model what happens if active work sideband fields stay at their defaults.

This is offline analysis only. It narrows the earlier risk statement: zero
``work +0x26`` does not stop the initial channel-A render setup, but it does
leave the channel-B refill descriptor unseeded.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT_DIR / "analysis/hardware-boundary/video-zero-sideband-scenario.json"
OUT_MD = ROOT_DIR / "analysis/hardware-boundary/video-zero-sideband-scenario.md"

SOURCES = {
    "prepare": ROOT_DIR / "analysis/dispatch-mmio/decompiled/10014910_hp1020_video_prepare_page_candidate.c",
    "render": ROOT_DIR / "analysis/dispatch-mmio/decompiled/10015214_hp1020_video_render_or_dma_candidate.c",
    "band_helper": ROOT_DIR
    / "analysis/zjs-parser-boundary/decompiled/10014244_hp1020_video_band_done_or_irq_helper_candidate.c",
    "band_queue": ROOT_DIR
    / "analysis/zjs-parser-boundary/decompiled/10013f34_hp1020_video_band_queue_or_list_candidate.c",
}

INPUTS = {
    "sideband_census": ROOT_DIR / "analysis/hardware-boundary/video-sideband-write-census.json",
    "dataflow_contract": ROOT_DIR / "analysis/hardware-boundary/video-dataflow-contract.json",
    "transfer_ring": ROOT_DIR / "analysis/hardware-boundary/video-transfer-ring.json",
}


def read_text(path: Path) -> str:
    return path.read_text(errors="replace")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def check(name: str, ok: bool, detail: str) -> dict[str, str]:
    return {"name": name, "status": "present" if ok else "missing", "detail": detail}


def build_report() -> dict[str, Any]:
    sources = {name: read_text(path) for name, path in SOURCES.items()}
    inputs = {name: read_json(path) for name, path in INPUTS.items()}
    dataflow_stages = {
        item.get("stage"): item
        for item in inputs["dataflow_contract"].get("contract_stages", [])
        if isinstance(item, dict)
    }

    scenario = [
        {
            "step": "prepare_defaults",
            "function": "0x10014910",
            "if_work_0x26_is_zero": "video state +0xd0 and +0xd4 are seeded to zero",
            "effect": "remaining-unit counters start empty",
        },
        {
            "step": "initial_channel_a_still_arms",
            "function": "0x10015214",
            "if_work_0x26_is_zero": "no direct gate before channel-A pointer/length setup",
            "effect": "render can still write channel-A pointer and length from the raster payload",
        },
        {
            "step": "channel_b_refill_skipped",
            "function": "0x10014244",
            "if_work_0x26_is_zero": "helper condition `+0xd0 != 0` is false",
            "effect": "no channel-B pointer/length descriptor is written by the helper",
        },
        {
            "step": "raw_band_final_logic_becomes_ambiguous",
            "function": "0x10013f34",
            "if_work_0x26_is_zero": "+0xd4 starts at zero while descriptor units can still be consumed later",
            "effect": "final/high-bit and remaining decrement logic no longer has a proven sane seed",
        },
    ]

    checks = [
        check(
            "sideband_census_passes",
            inputs["sideband_census"].get("status") == "pass"
            and inputs["sideband_census"].get("active_work_writer_hits") == [],
            "sideband census found no selected active-work writer and whole-program target-offset stores are page-param only",
        ),
        check(
            "prepare_seeds_d0_d4_from_work_0x26",
            "*(uint *)(puVar15 + 0xd0) = (uint)*(ushort *)(param_1 + 0x26)" in sources["prepare"]
            and "*(uint *)(puVar15 + 0xd4) = (uint)*(ushort *)(param_1 + 0x26)" in sources["prepare"],
            "prepare copies active argument +0x26 into both remaining counters",
        ),
        check(
            "render_channel_a_does_not_depend_on_d0",
            "*DAT_100067f4 = uVar9" in sources["render"]
            and "*piVar4 = iVar8" in sources["render"]
            and "FUN_10014244()" in sources["render"],
            "render sets channel-A pointer/length and then calls the channel-B helper",
        ),
        check(
            "helper_requires_nonzero_d0",
            "uVar3 = *(uint *)(PTR_DAT_10006770 + 0xd0), uVar3 != 0" in sources["band_helper"]
            and "*DAT_100067e4 = uVar7" in sources["band_helper"]
            and "*piVar2 = iVar4 * iVar5" in sources["band_helper"],
            "channel-B helper writes pointer/length only when remaining +0xd0 is nonzero",
        ),
        check(
            "band_queue_uses_d4_for_final_and_decrement",
            "if (*(uint *)(puVar2 + 0xd4) <= (uint)(*(int *)(puVar6 + 8) << 2))" in sources["band_queue"]
            and "*(int *)(puVar2 + 0xd4) = *(int *)(puVar2 + 0xd4) - *(int *)(puVar6 + 8)" in sources["band_queue"],
            "raw-band queue logic uses +0xd4 for final/high-bit decisions and decrements it by descriptor units",
        ),
        check(
            "a4_channel_a_payload_is_modeled",
            dataflow_stages.get("render_initial_transfer", {})
            .get("known_values", {})
            .get("0xb2040008")
            == 6364,
            "a4_default channel-A payload length remains concretely modeled",
        ),
    ]

    status = "pass" if all(item["status"] == "present" for item in checks) else "fail"
    return {
        "summary": "Consequence model for default-zero active work sideband fields.",
        "status": status,
        "source_reports": {name: str(path.relative_to(ROOT_DIR)) for name, path in INPUTS.items()},
        "scenario": scenario,
        "practical_conclusion": [
            "Zero active work +0x26 is not an immediate proof that render setup cannot start.",
            "It is a refill/descriptor-path blocker: channel A can be armed, but channel B is not seeded by 0x10014244.",
            "For a narrow print-only replacement, this means a trivial first-transfer probe might appear alive while still being far from a complete page-printing implementation.",
            "Treat +0x26/+0x30/+0x32 as a deliberate policy decision to resolve with hardware traces, not as page-height fields we can blindly copy.",
        ],
        "checks": checks,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 Zero Sideband Scenario",
        "",
        "This generated report is offline only. It does not contact the printer.",
        "",
        "## Result",
        "",
        f"- status: `{report['status']}`",
        "",
        "## Scenario",
        "",
        "| Step | Function | If work +0x26 is zero | Effect |",
        "|---|---|---|---|",
    ]
    for item in report["scenario"]:
        lines.append(
            f"| `{item['step']}` | `{item['function']}` | {item['if_work_0x26_is_zero']} | {item['effect']} |"
        )

    lines.extend(["", "## Practical Conclusion", ""])
    for item in report["practical_conclusion"]:
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
    print(f"status={report['status']} checks={len(report['checks'])}")
    print(OUT_MD.relative_to(ROOT_DIR))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
