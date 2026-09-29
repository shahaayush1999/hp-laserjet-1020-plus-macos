#!/usr/bin/env python3
"""Generate the explicit USB MMIO contract for the bulk/parser probe."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ENDPOINT0_MAP = ROOT / "analysis/usb-path/usb-mmio-map.json"
INTERRUPT_MODEL = ROOT / "analysis/usb-path/usb-interrupt-events.json"
REARM_MODEL = ROOT / "analysis/usb-path/usb-bulk-rearm-model.json"
CALLBACK_MODEL = ROOT / "analysis/usb-path/usb-bulk-callbacks-model.json"
STOCK_ELF = ROOT / "analysis/sihp1020.elf"
USB2THREAD_DECOMPILE = ROOT / "analysis/usb-path/decompiled-neighbors/10008ff0_hp1020_usb2_thread.c"
INTERRUPT_DECOMPILE = ROOT / "analysis/tasks/task-decompiled/10008208_hp1020_task_entry_10008208.c"
REARM_DECOMPILE = ROOT / "analysis/call-clusters/seed-decompiled/100086f4_FUN_100086f4.c"
CALLBACK_DECOMPILE = ROOT / "analysis/usb-path/bulk-callbacks-decompiled/100087b8_hp1020_usb_bulk_rx_callback_a_candidate.c"
PARSER_DECOMPILE = ROOT / "analysis/zjs-parser-boundary/decompiled/10009d34_hp1020_zjs_parser_entry_candidate.c"
OUT_JSON = ROOT / "analysis/usb-path/usb-bulk-probe-contract.json"
OUT_MD = ROOT / "analysis/usb-path/usb-bulk-probe-contract.md"


BULK_REGISTERS: dict[str, dict[str, Any]] = {
    "0xb3000200": {
        "role": "EP0 OUT control (CNAK request)",
        "access": ["read", "write"],
        "allowed_write_masks": ["or 0x00000100"],
        "evidence": "stock USB2Thread sets CNAK bit 8; this is endpoint control, not interrupt acknowledgement",
    },
    "0xb3000220": {
        "role": "EP1 OUT control (SNAK/CNAK requests)",
        "access": ["read", "write"],
        "allowed_write_masks": ["or 0x00000080", "or 0x00000100"],
        "evidence": "stock interrupt path requests SNAK 0x80; the bulk callback requests CNAK 0x100; neither proves DMA quiescence",
    },
    "0xb3000224": {
        "role": "bank-1 lane-1 bulk OUT status",
        "access": ["read", "write"],
        "allowed_write_values": ["0x00000400"],
        "evidence": "stock interrupt task acknowledges latched TDC status 0x400; successful completion still needs ownership/error validation",
    },
    "0xb300022c": {
        "role": "bulk OUT endpoint maximum-packet/config word",
        "access": ["write"],
        "allowed_write_values": ["0x00000040", "0x00000200"],
        "evidence": "stock USB2Thread selects 64-byte full-speed or 512-byte high-speed receive packets",
    },
    "0xb3000234": {
        "role": "bulk OUT receive descriptor submit register",
        "access": ["write"],
        "allowed_write_values": ["0x90021370"],
        "evidence": "stock re-arm helper submits descriptor pool 0x90021370",
    },
    "0xb3000404": {
        "role": "USB device control (DEVCTL), transmit-DMA enable request",
        "access": ["read", "write"],
        "allowed_write_masks": ["or 0x00000008"],
        "evidence": "stock sets bit 0x8, named TDE by the pinned family header; RDE is the separate bit 0x4",
    },
    "0xb3000418": {
        "role": "USB event-lane mask word",
        "access": ["write"],
        "allowed_write_values": ["0xfffcfffe"],
        "evidence": "stock USB2Thread leaves endpoint-0 and bank-1 service lanes unmasked",
    },
    "0xb3010000": {
        "role": "HP USB wrapper control; bit meanings incompletely established",
        "access": ["read", "write"],
        "allowed_write_masks": ["or 0x00000005"],
        "evidence": "stock USB2Thread tests bit 0 and sets bits 0/2; the family UDC header does not define this wrapper register",
    },
}


def load(path: Path) -> Any:
    return json.loads(path.read_text())


def check(name: str, ok: bool, detail: str) -> dict[str, str]:
    return {"name": name, "status": "present" if ok else "missing", "detail": detail}


def contains_all(path: Path, needles: list[str]) -> tuple[bool, list[str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    missing = [needle for needle in needles if needle not in text]
    return not missing, missing


def build() -> dict[str, Any]:
    endpoint0 = load(ENDPOINT0_MAP)
    interrupt = load(INTERRUPT_MODEL)
    rearm = load(REARM_MODEL)
    callbacks = load(CALLBACK_MODEL)
    registers = dict(endpoint0["registers"])
    registers.update(BULK_REGISTERS)

    lane = interrupt.get("event_scan", {}).get("bulk_receive_lane", {})
    rearm_constants = rearm.get("constants", {})
    callback_constants = callbacks.get("constants", {})
    stock_bytes = STOCK_ELF.read_bytes()
    direct_stock_values = (
        0x00020000,
        0xB3000220,
        0xB3000234,
        0x90021370,
        0x900216F0,
    )
    stock_literals = {
        f"0x{value:08x}": stock_bytes.count(value.to_bytes(4, "big"))
        for value in (
            *direct_stock_values,
            0xB3000224,
        )
    }
    evidence_specs = {
        "usb2thread_descriptor_initialization": (
            USB2THREAD_DECOMPILE,
            [
                "*DAT_10005edc = 0x40;",
                "uVar13 = 0x200;",
                "*(char *)(iVar18 + 8)",
                "*(undefined1 *)(iVar18 + 0xc) = 0;",
                "*puVar15 = 8;",
                "*DAT_10005e70 = *DAT_10005e70 | 0x100;",
            ],
        ),
        "interrupt_bank_lane_completion": (
            INTERRUPT_DECOMPILE,
            [
                "puVar10 = (uint *)(uVar8 * 0x20 + iVar11);",
                "if ((uVar9 & 0x400) != 0)",
                "*puVar10 = 0x400;",
                "if (uVar7 == 1)",
                "if ((uVar8 == 1)",
            ],
        ),
        "bulk_rearm_descriptor_shape": (
            REARM_DECOMPILE,
            [
                "((uVar7 & 0xf) != 0)",
                "*(char *)(iVar6 + 8)",
                "*(undefined1 *)(iVar6 + 0xc) = 0;",
                "*piVar2 = iVar6;",
                "*puVar4 = 8;",
            ],
        ),
        "bulk_callback_wait_copy_rearm": (
            CALLBACK_DECOMPILE,
            [
                "FUN_10017d28(PTR_DAT_10005e18,DAT_10005e74,1",
                "FUN_1001b38c(",
                "FUN_100086f4(0);",
                "*DAT_10005e70 = *DAT_10005e70 | 0x100;",
            ],
        ),
        "parser_callback_boundary": (
            PARSER_DECOMPILE,
            [
                "(**(code **)(param_1 + 0xc))",
                "uStack_70 = 0x10;",
                "uVar2 < 0xd",
            ],
        ),
    }
    evidence_results = []
    for name, (path, needles) in evidence_specs.items():
        ok, missing = contains_all(path, needles)
        evidence_results.append(
            {
                "name": name,
                "source": str(path.relative_to(ROOT)),
                "status": "present" if ok else "missing",
                "missing_needles": missing,
            }
        )
    checks = [
        check(
            "bulk_lane_matches_interrupt_model",
            lane.get("lane_status_register") == "0xb3000224"
            and lane.get("lane_control_register") == "0xb3000220"
            and lane.get("event_bit") == "0x00020000"
            and lane.get("control_snak_mask") == "0x80"
            and interrupt.get("event_scan", {}).get("wake_is_successful_completion") is False,
            "bank-1/lane-1 status and control addresses remain fixed; wake hints do not assert success",
        ),
        check(
            "descriptor_submit_matches_rearm_model",
            rearm_constants.get("descriptor_pool") == "0x90021370"
            and rearm_constants.get("descriptor_submit_register") == "0xb3000234"
            and rearm_constants.get("bulk_buffer_base") == "0x900216f0",
            "descriptor pool, buffer, and submit register remain fixed",
        ),
        check(
            "callback_ack_matches_contract",
            callback_constants.get("usb_endpoint_ack_register") == "0xb3000220"
            and callback_constants.get("usb_status_register") == "0xb3000418",
            "legacy callback field usb_endpoint_ack_register denotes OUT1 control; its address and the lane mask remain in the unchanged probe allowlist",
        ),
        check(
            "all_bulk_registers_are_usb_only",
            all(register.startswith(("0xb300", "0xb301")) for register in BULK_REGISTERS),
            "all additions stay in the mapped USB controller families",
        ),
        check(
            "stock_elf_contains_resolved_bulk_literals",
            all(stock_bytes.count(value.to_bytes(4, "big")) > 0 for value in direct_stock_values),
            "raw stock ELF contains the direct literals; byte-gated interrupt evidence derives lane EPSTS 0xb3000224 independently of EPCTL 0xb3000220",
        ),
        check(
            "saved_decompilation_preserves_bulk_contract",
            all(item["status"] == "present" for item in evidence_results),
            "USB2Thread, interrupt task, re-arm helper, callback, and parser boundary evidence all remain present",
        ),
    ]
    status = "pass" if all(item["status"] == "present" for item in checks) else "fail"
    return {
        "summary": "Combined endpoint-0 and bulk OUT USB MMIO contract for the mechanically inert parser probe.",
        "status": status,
        "semantic_correction_only": True,
        "registers": registers,
        "bulk_registers": sorted(BULK_REGISTERS),
        "allowed_memory": {
            "bulk_descriptor": {"start": "0x90021370", "end": "0x9002137f"},
            "bulk_buffer": {"start": "0x900216f0", "end": "0x90021aef"},
            "setup_packet": {"start": "0x90021348", "end": "0x9002134f"},
            "control_in_descriptor": {"start": "0x900226f0", "end": "0x900226ff"},
            "control_in_staging": {"start": "0x90022bd0", "end": "0x90022c4b"},
            "open_marker_descriptor": {"start": "0x90003200", "end": "0x90003225"},
            "open_standard_descriptors": {"start": "0x90003300", "end": "0x90003377"},
            "probe_status_descriptor_hardware_alias": {"start": "0x90003400", "end": "0x9000347b"},
            "probe_status_descriptor": {"start": "0x10003400", "end": "0x1000347b"},
            "probe_runtime_state": {"start": "0x1001d498", "end": "0x1001d557"},
            "stock_control_response_state": {"start": "0x100212d4", "end": "0x10021314"},
        },
        "independent_stock_evidence": {
            "elf": str(STOCK_ELF.relative_to(ROOT)),
            "big_endian_literal_counts": stock_literals,
            "derived_registers": {
                "0xb3000224": "lane status word at 0xb3000220 + 0x4; not stored as a standalone stock ELF literal"
            },
            "saved_decompilation_checks": evidence_results,
            "interrupt_original_byte_checks": interrupt.get("original_byte_checks", []),
        },
        "checks": checks,
    }


def render(report: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 USB Bulk Probe Contract",
        "",
        "This generated allowlist combines the existing endpoint-0 map with only the stock-evidenced bulk OUT registers needed by the non-printing parser probe.",
        "",
        f"- status: `{report['status']}`",
        f"- total allowed USB registers: `{len(report['registers'])}`",
        f"- bulk-specific registers: `{len(report['bulk_registers'])}`",
        "",
        "## Bulk Registers",
        "",
        "| Register | Access | Role | Permitted writes | Evidence |",
        "|---:|---|---|---|---|",
    ]
    for register in report["bulk_registers"]:
        item = report["registers"][register]
        writes = item.get("allowed_write_values", []) + item.get("allowed_write_masks", [])
        lines.append(
            f"| `{register}` | `{', '.join(item['access'])}` | {item['role']} | "
            f"`{', '.join(writes)}` | {item['evidence']} |"
        )
    lines.extend(["", "## Allowed Memory", "", "| Region | Start | End |", "|---|---:|---:|"])
    for name, item in report["allowed_memory"].items():
        lines.append(f"| `{name}` | `{item['start']}` | `{item['end']}` |")
    evidence = report["independent_stock_evidence"]
    lines.extend(["", "## Independent Stock Evidence", ""])
    lines.append(f"- stock ELF: `{evidence['elf']}`")
    for literal, count in evidence["big_endian_literal_counts"].items():
        lines.append(f"- `{literal}` big-endian literal occurrences: `{count}`")
    for register, derivation in evidence["derived_registers"].items():
        lines.append(f"- `{register}` derivation: {derivation}")
    lines.extend(["", "| Status | Check | Source | Missing needles |", "|---|---|---|---|"])
    for item in evidence["saved_decompilation_checks"]:
        missing = ", ".join(item["missing_needles"]) or "none"
        lines.append(f"| `{item['status']}` | `{item['name']}` | `{item['source']}` | `{missing}` |")
    lines.extend(["", "## Checks", "", "| Status | Check | Detail |", "|---|---|---|"])
    for item in report["checks"]:
        lines.append(f"| `{item['status']}` | `{item['name']}` | {item['detail']} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-output", type=Path, default=OUT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=OUT_MD)
    args = parser.parse_args()
    report = build()
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.markdown_output.write_text(render(report))
    print(f"status={report['status']} registers={len(report['registers'])} checks={len(report['checks'])}")
    print(args.markdown_output)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
