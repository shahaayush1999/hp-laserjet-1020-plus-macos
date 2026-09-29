#!/usr/bin/env python3
"""Generate the minimum printing-only replacement scope for HP 1020 firmware.

This is an offline synthesis model. It does not contact the printer. It reads
the generated print-path, USB, and hardware-boundary reports and turns the
current reverse-engineering state into an explicit "what remains" checklist for
the narrow goal: print PDFs using the existing host-side ZjStream path, without
cloning unrelated firmware features.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT_DIR / "analysis/open-firmware-model/minimal-print-scope.json"
OUT_MD = ROOT_DIR / "analysis/open-firmware-model/minimal-print-scope.md"
USB_BULK_PROBE_DIR = ROOT_DIR / "analysis/open-firmware-probes/usb-bulk-parser-draft"


INPUTS = {
    "print_model": ROOT_DIR / "analysis/open-firmware-model/print-path-model.json",
    "model_invariants": ROOT_DIR / "analysis/open-firmware-model/model-invariants.json",
    "hardware_boundary": ROOT_DIR / "analysis/hardware-boundary/hardware-boundary.json",
    "video_projection": ROOT_DIR / "analysis/hardware-boundary/video-register-projection.json",
    "endpoint0": ROOT_DIR / "analysis/usb-path/open-endpoint0-model.json",
    "control_data_stage": ROOT_DIR / "analysis/usb-path/control-in-data-stage.json",
    "control_completion": ROOT_DIR / "analysis/usb-path/control-completion-event.json",
    "usb_interrupt_events": ROOT_DIR / "analysis/usb-path/usb-interrupt-events.json",
    "usb_bulk_receive": ROOT_DIR / "analysis/usb-path/usb-bulk-receive-model.json",
    "usb_bulk_callbacks": ROOT_DIR / "analysis/usb-path/usb-bulk-callbacks-model.json",
    "usb_bulk_rearm": ROOT_DIR / "analysis/usb-path/usb-bulk-rearm-model.json",
    "usb_bulk_probe_contract": ROOT_DIR / "analysis/usb-path/usb-bulk-probe-contract.json",
    "usb_bulk_parser_model": USB_BULK_PROBE_DIR / "parser-model.json",
    "usb_bulk_deterministic": USB_BULK_PROBE_DIR / "deterministic-test-results.json",
    "usb_bulk_safety": USB_BULK_PROBE_DIR / "safety-scan.json",
    "usb_bulk_usb_contract": USB_BULK_PROBE_DIR / "usb-contract-scan.json",
    "usb_bulk_usb_mmio": USB_BULK_PROBE_DIR / "usb-mmio-access-scan.json",
    "usb_bulk_memory": USB_BULK_PROBE_DIR / "memory-boundary-scan.json",
    "usb_bulk_source_contract": USB_BULK_PROBE_DIR / "source-contract-check.json",
    "usb_bulk_status_descriptor": USB_BULK_PROBE_DIR / "status-descriptor-check.json",
    "usb_bulk_config_descriptor": USB_BULK_PROBE_DIR / "config-descriptor-check.json",
    "usb_bulk_reproducibility": USB_BULK_PROBE_DIR / "reproducibility-check.json",
    "marker_rearm": ROOT_DIR / "analysis/open-firmware-probes/usb-marker-draft/marker-rearm-flow-check.json",
    "sideband_default_impact": ROOT_DIR / "analysis/hardware-boundary/video-sideband-default-impact.json",
    "remaining_units": ROOT_DIR / "analysis/hardware-boundary/video-remaining-units.json",
}

TEXT_INPUTS = {
    "usb_bulk_summary": USB_BULK_PROBE_DIR / "summary.md",
    "usb_bulk_hardware_test_plan": USB_BULK_PROBE_DIR / "hardware-test-plan.md",
}

EXPECTED_SIDE_EFFECT_COUNTERS = {
    "usb_device_opens": 0,
    "usb_transfers_submitted": 0,
    "mmio_reads": 0,
    "mmio_writes": 0,
    "video_commands": 0,
    "engine_commands": 0,
    "mechanical_actions": 0,
}


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise SystemExit(f"missing input report: {path}") from exc


def fail_count(items: Any) -> int:
    if not isinstance(items, list):
        return 0
    return sum(isinstance(item, dict) and item.get("severity") == "fail" for item in items)


def nested_fail_count(value: Any) -> int:
    """Count explicit fail markers in either object-style or list-style reports."""

    if isinstance(value, list):
        return sum(nested_fail_count(item) for item in value)
    if not isinstance(value, dict):
        return 0
    count = int(value.get("severity") == "fail" or value.get("status") == "fail")
    return count + sum(
        nested_fail_count(item)
        for key, item in value.items()
        if key not in {"severity", "status"}
    )


def report_status(value: Any) -> str:
    if isinstance(value, dict) and value.get("status") in {"pass", "fail"}:
        return value["status"]
    return "fail" if nested_fail_count(value) else "pass"


def load_text(path: Path) -> str:
    try:
        return path.read_text()
    except FileNotFoundError as exc:
        raise SystemExit(f"missing input report: {path}") from exc


def status_from_bool(ok: bool) -> str:
    return "mapped" if ok else "gap"


def build_scope() -> dict[str, Any]:
    print_model = load_json(INPUTS["print_model"])
    invariants = load_json(INPUTS["model_invariants"])
    hardware_boundary = load_json(INPUTS["hardware_boundary"])
    video_projection = load_json(INPUTS["video_projection"])
    endpoint0 = load_json(INPUTS["endpoint0"])
    control_data_stage = load_json(INPUTS["control_data_stage"])
    control_completion = load_json(INPUTS["control_completion"])
    usb_interrupt_events = load_json(INPUTS["usb_interrupt_events"])
    usb_bulk_receive = load_json(INPUTS["usb_bulk_receive"])
    usb_bulk_callbacks = load_json(INPUTS["usb_bulk_callbacks"])
    usb_bulk_rearm = load_json(INPUTS["usb_bulk_rearm"])
    usb_bulk_probe_contract = load_json(INPUTS["usb_bulk_probe_contract"])
    usb_bulk_parser_model = load_json(INPUTS["usb_bulk_parser_model"])
    usb_bulk_deterministic = load_json(INPUTS["usb_bulk_deterministic"])
    usb_bulk_safety = load_json(INPUTS["usb_bulk_safety"])
    usb_bulk_usb_contract = load_json(INPUTS["usb_bulk_usb_contract"])
    usb_bulk_usb_mmio = load_json(INPUTS["usb_bulk_usb_mmio"])
    usb_bulk_memory = load_json(INPUTS["usb_bulk_memory"])
    usb_bulk_source_contract = load_json(INPUTS["usb_bulk_source_contract"])
    usb_bulk_status_descriptor = load_json(INPUTS["usb_bulk_status_descriptor"])
    usb_bulk_config_descriptor = load_json(INPUTS["usb_bulk_config_descriptor"])
    usb_bulk_reproducibility = load_json(INPUTS["usb_bulk_reproducibility"])
    usb_bulk_summary = load_text(TEXT_INPUTS["usb_bulk_summary"])
    usb_bulk_hardware_test_plan = load_text(TEXT_INPUTS["usb_bulk_hardware_test_plan"])
    marker_rearm = load_json(INPUTS["marker_rearm"])
    sideband_default_impact = load_json(INPUTS["sideband_default_impact"])
    remaining_units = load_json(INPUTS["remaining_units"])

    work_objects = print_model.get("objects", {}).get("work_objects", [])
    raster_nodes = print_model.get("objects", {}).get("raster_nodes", [])
    trace = print_model.get("trace", [])
    job_messages = []
    for entry in trace:
        for message in entry.get("jobmgr_messages", []):
            job_messages.append(message.get("message"))

    required_messages = {1, 2, 3, 5, 6, "0x29", "0x2a", "0x2b"}
    optional_messages = {8}
    seen_messages = set(job_messages)
    missing_messages = sorted(required_messages - seen_messages, key=str)
    optional_seen = sorted(optional_messages & seen_messages, key=str)

    hardware_register_families = hardware_boundary.get("register_families") or hardware_boundary.get("families") or []
    high_risk_families = []
    if isinstance(hardware_register_families, list):
        for item in hardware_register_families:
            if isinstance(item, dict) and item.get("risk") == "high":
                high_risk_families.append(item.get("family") or item.get("prefix"))

    projection_rows = (
        video_projection.get("projection_rows")
        or video_projection.get("projections")
        or video_projection.get("variants")
        or []
    )
    projected_cases = len(projection_rows) if isinstance(projection_rows, list) else 0

    endpoint_scenarios = endpoint0.get("scenarios", [])
    endpoint_data_cases = sum(
        1
        for item in endpoint_scenarios
        if isinstance(item, dict) and item.get("result", {}).get("status") == "data"
    )
    endpoint_stall_cases = sum(
        1
        for item in endpoint_scenarios
        if isinstance(item, dict) and item.get("result", {}).get("status") == "stall"
    )
    sideband_impacts = {
        item.get("work_field"): item
        for item in sideband_default_impact.get("field_impacts", [])
        if isinstance(item, dict)
    }
    sideband_access_hits = sideband_default_impact.get("ghidra_video_state_access_scan", {}).get("hits", [])
    direct_work = load_json(ROOT_DIR / "analysis/hardware-boundary/zjs-direct-work.json")
    sideband_unsourced_gap = direct_work["status"] != "pass"


    bulk_probe_reports = {
        "combined_contract": usb_bulk_probe_contract,
        "parser_model": usb_bulk_parser_model,
        "deterministic_results": usb_bulk_deterministic,
        "safety_scan": usb_bulk_safety,
        "usb_contract_scan": usb_bulk_usb_contract,
        "usb_mmio_access_scan": usb_bulk_usb_mmio,
        "memory_boundary_scan": usb_bulk_memory,
        "source_contract_check": usb_bulk_source_contract,
        "status_descriptor_check": usb_bulk_status_descriptor,
        "config_descriptor_check": usb_bulk_config_descriptor,
        "reproducibility_check": usb_bulk_reproducibility,
    }
    bulk_probe_report_statuses = {
        name: report_status(report) for name, report in bulk_probe_reports.items()
    }
    bulk_probe_report_failures = {
        name: nested_fail_count(report) for name, report in bulk_probe_reports.items()
    }
    bulk_probe_coverage = usb_bulk_parser_model.get("coverage", {})
    bulk_probe_generated_samples = [
        item.get("name")
        for item in usb_bulk_parser_model.get("generated_samples", [])
        if isinstance(item, dict)
    ]
    bulk_probe_matrix_cases = [
        item.get("name")
        for item in usb_bulk_parser_model.get("test_matrix", [])
        if isinstance(item, dict)
    ]
    bulk_probe_recognized_types = [
        item.get("type_hex")
        for item in usb_bulk_parser_model.get("probe_recognized_chunk_types", [])
        if isinstance(item, dict)
    ]
    bulk_probe_cases = [
        *usb_bulk_parser_model.get("generated_samples", []),
        *usb_bulk_parser_model.get("test_matrix", []),
    ]
    bulk_probe_mechanically_inert = bool(bulk_probe_cases) and all(
        isinstance(item, dict)
        and item.get("parser_state", {}).get("side_effects") == EXPECTED_SIDE_EFFECT_COUNTERS
        for item in bulk_probe_cases
    )
    bulk_probe_coverage_passes = (
        bulk_probe_coverage.get("generated_samples_discovered")
        == bulk_probe_coverage.get("generated_samples_passed")
        == len(bulk_probe_generated_samples)
        and bulk_probe_coverage.get("synthetic_cases")
        == bulk_probe_coverage.get("synthetic_cases_passed")
        == len(bulk_probe_matrix_cases)
        and bulk_probe_coverage.get("total_cases")
        == bulk_probe_coverage.get("total_cases_passed")
        == len(bulk_probe_cases)
        and bulk_probe_coverage.get("assertions")
        == bulk_probe_coverage.get("assertions_passed")
    )
    bulk_probe_offline_validated = (
        all(status == "pass" for status in bulk_probe_report_statuses.values())
        and all(count == 0 for count in bulk_probe_report_failures.values())
        and bulk_probe_coverage_passes
        and bulk_probe_recognized_types
        == ["0x00", "0x01", "0x02", "0x03", "0x04", "0x05", "0x06"]
        and bulk_probe_mechanically_inert
        and usb_bulk_deterministic.get("hardware_contact") is False
        and bool(usb_bulk_summary.strip())
        and bool(usb_bulk_hardware_test_plan.strip())
    )
    bulk_probe_component_status = (
        "implemented and offline validated"
        if bulk_probe_offline_validated
        else "implemented; offline validation failed"
    )
    status_descriptor_address = usb_bulk_status_descriptor.get("section", {}).get("address")
    bulk_probe_evidence = {
        "status": bulk_probe_component_status,
        "offline_validated": bulk_probe_offline_validated,
        "execution_scope": usb_bulk_parser_model.get("scope", {}).get("execution"),
        "hardware_access": usb_bulk_parser_model.get("scope", {}).get("hardware_access"),
        "mechanical_behavior": usb_bulk_parser_model.get("scope", {}).get("mechanical_behavior"),
        "mechanically_inert_cases": bulk_probe_mechanically_inert,
        "hardware_contact": usb_bulk_deterministic.get("hardware_contact"),
        "report_statuses": bulk_probe_report_statuses,
        "report_fail_counts": bulk_probe_report_failures,
        "coverage": bulk_probe_coverage,
        "generated_sample_cases": bulk_probe_generated_samples,
        "matrix_cases": bulk_probe_matrix_cases,
        "recognized_chunk_types": bulk_probe_recognized_types,
        "status_descriptor_text": usb_bulk_status_descriptor.get("descriptor_text"),
        "status_descriptor_address": (
            f"0x{status_descriptor_address:08x}"
            if isinstance(status_descriptor_address, int)
            else status_descriptor_address
        ),
        "reproducibility_status": usb_bulk_reproducibility.get("status"),
        "summary_report": str(TEXT_INPUTS["usb_bulk_summary"].relative_to(ROOT_DIR)),
        "hardware_test_plan": str(TEXT_INPUTS["usb_bulk_hardware_test_plan"].relative_to(ROOT_DIR)),
    }

    components = [
        {
            "component": "Host PDF-to-ZjStream conversion",
            "current_status": "available",
            "evidence": "assets/runtime/foo2zjs-wrapper and generated ZjStream matrix",
            "replacement_need": "reuse existing GPL foo2zjs path; not firmware work",
            "risk": "low",
        },
        {
            "component": "USB upload envelope",
            "current_status": "available",
            "evidence": "PJL/ACL wrapper and open probes build date-prefixed ELF uploads",
            "replacement_need": "keep ACL/PJL upload wrapper for volatile firmware load",
            "risk": "low",
        },
        {
            "component": "USB endpoint-0 descriptor/control path",
            "current_status": "partially implemented",
            "evidence": f"{endpoint_data_cases} modeled data scenarios, {endpoint_stall_cases} modeled stall scenarios; control-IN descriptor/kick model present",
            "replacement_need": "live prove marker descriptor; marker now has a tiny gate-clear rearm loop, but not full stock ThreadX/event completion handling",
            "risk": "medium",
        },
        {
            "component": "USB bulk receive to ZjStream parser",
            "current_status": bulk_probe_component_status,
            "evidence": (
                "mechanically inert open probe; "
                f"{bulk_probe_coverage.get('generated_samples_passed')}/{bulk_probe_coverage.get('generated_samples_discovered')} generated samples, "
                f"{bulk_probe_coverage.get('synthetic_cases_passed')}/{bulk_probe_coverage.get('synthetic_cases')} deterministic matrix cases, "
                f"{bulk_probe_coverage.get('assertions_passed')}/{bulk_probe_coverage.get('assertions')} assertions; "
                f"recognized scope {', '.join(bulk_probe_recognized_types)}"
            ),
            "replacement_need": "guarded hardware execution must prove custom-code execution and real controller completion, length, acknowledgement, and repeated descriptor re-arm behavior; this probe discards payloads and has no print handoff",
            "risk": "medium",
        },
        {
            "component": "ZjStream parser and JobMgr object model",
            "current_status": status_from_bool(not missing_messages and fail_count(invariants) == 0),
            "evidence": f"stock-path model has {len(trace)} parsed chunks, {len(work_objects)} work object(s), {len(raster_nodes)} raster node(s), invariant failures={fail_count(invariants)}; the inert probe only frames/counts 0x00..0x06 and discards payloads",
            "replacement_need": "portable C semantic construction is native-tested separately; integrate on-device only after boot/USB proof, and keep any print handoff explicitly gated",
            "risk": "medium",
        },
        {
            "component": "JBIG compressed raster handling",
            "current_status": "mapped to handoff boundary",
            "evidence": "BID chunks become work +0x50 raster nodes with payload +0x48 length and +0x54 buffer pointer",
            "replacement_need": "likely no full JBIG decode in firmware if hardware consumes the compressed stream like stock firmware",
            "risk": "high until hardware consumer semantics are proven",
        },
        {
            "component": "Video sideband policy",
            "current_status": "direct START_PAGE source verified",
            "evidence": f"{len(sideband_access_hits)} exact-offset state access hits classified; active work +0x26 source is {'unresolved' if sideband_unsourced_gap else 'verified by stock ELF'}",
            "replacement_need": "use VIDEO_Y and ECONOMODE from the verified direct builder; calibrate physical counter/completion behavior before print output",
            "risk": "high",
        },
        {
            "component": "Raster processing callbacks",
            "current_status": "call contract verified; custom ISA semantics unresolved",
            "evidence": "four-argument callback call verified in stock ELF; BPP2/600 has 16 unresolved extension instructions, BPP1/600 has 84",
            "replacement_need": "recover custom instruction effects from core-specific ISA definitions or stock input/output traces, or validate the stock-supported callback bypass",
            "risk": "unknown custom instruction side effects; not approved for probe inclusion",
        },
        {
            "component": "Video/raw-band hardware feed",
            "current_status": "danger boundary mapped, semantics incomplete",
            "evidence": f"{projected_cases} generated print variants project host fields into video registers",
            "replacement_need": "reproduce page timing, raw-band pointers, channel enable/reset/wait sequence",
            "risk": "high",
        },
        {
            "component": "Engine paper/fuser/motor coordination",
            "current_status": "dispatch/status paths mapped, behavior incomplete",
            "evidence": "engine/status MMIO families are classified high risk in hardware boundary model",
            "replacement_need": "coordinate mechanical state before and during video transfer",
            "risk": "high",
        },
        {
            "component": "Scanner/fax/network/multi-product features",
            "current_status": "out of scope",
            "evidence": "HP 1020 target is print-only USB path",
            "replacement_need": "none for Aayush's narrow goal",
            "risk": "none",
        },
    ]

    blockers = [
        {
            "blocker": "Guarded hardware execution and USB controller behavior",
            "why": "The bulk receive/framing probe is implemented and validated offline, but hardware has not proved that custom code executes, that boot-ROM controller state is sufficient, or that real completion length/ack/re-arm behavior matches the static contract.",
            "next_test": "Follow the probe hardware test plan only after a fresh power cycle: prove the status descriptor, send the inert START_DOC/END_DOC stream, and verify counters. Do not send raster or invoke engine/video paths.",
        },
        {
            "blocker": "Video and engine hardware sequencing",
            "why": "The mapped print model reaches raster handoff, but real printing needs synchronized video transfer and mechanical engine control.",
            "next_test": "Do not test this until USB-only open code is proven; continue static mapping of video/engine semantics first.",
        },
        {
            "blocker": "Video sideband values for the first print path",
            "why": "Static analysis now shows +0x26 is critical for channel-B refill/final accounting, but its active-work source is still not proven.",
            "next_test": "After USB-only execution is proven, use a non-printing or tightly gated trace/probe to distinguish whether stock leaves +0x26 zero or seeds it from page height/runtime state.",
        },
    ]

    return {
        "summary": "Minimum HP 1020 replacement-firmware scope for printing only.",
        "goal": "Print PDFs by reusing host-side ZjStream generation and implementing only the firmware path required to receive, parse, and print that stream.",
        "cross_platform_boundary": {
            "host_side": "PDF/PostScript to ZjStream conversion is host/platform packaging work.",
            "device_side": "Open firmware would be platform-independent after bytes reach USB.",
            "macos_repo_scope": "This repo's current production print path is macOS glue around HP firmware plus foo2zjs.",
        },
        "stock_evidence": {
            "parser_entry": print_model.get("parser_entry"),
            "jobmgr_queue": print_model.get("jobmgr_queue"),
            "required_job_messages_seen": sorted(seen_messages, key=str),
            "missing_required_messages": missing_messages,
            "optional_job_messages_seen": optional_seen,
            "work_objects": len(work_objects),
            "raster_nodes": len(raster_nodes),
            "model_invariant_failures": fail_count(invariants),
            "endpoint0_data_cases": endpoint_data_cases,
            "endpoint0_stall_cases": endpoint_stall_cases,
            "control_completion_event_object": control_completion.get("event_object"),
            "usb_tdc_status_bit": usb_interrupt_events.get("event_scan", {}).get("tdc_status_bit"),
            "usb_bulk_lane_event_bit": usb_interrupt_events.get("event_scan", {})
            .get("bulk_receive_lane", {})
            .get("event_bit"),
            "usb_bulk_lane_status_register": usb_interrupt_events.get("event_scan", {})
            .get("bulk_receive_lane", {})
            .get("lane_status_register"),
            "usb_bulk_lane_control_register": usb_interrupt_events.get("event_scan", {})
            .get("bulk_receive_lane", {})
            .get("lane_control_register"),
            "usb_wake_is_successful_completion": usb_interrupt_events.get("event_scan", {}).get("wake_is_successful_completion"),
            "marker_rearm_checks": len(marker_rearm),
            "marker_rearm_failures": fail_count(marker_rearm),
            "usb_bulk_receive_status": usb_bulk_receive.get("status"),
            "usb_bulk_transfer_record_stride": usb_bulk_receive.get("transfer_record", {}).get("record_stride"),
            "usb_bulk_receive_buffer_allocation": usb_bulk_receive.get("transfer_record", {}).get("buffer_allocation"),
            "usb_bulk_parser_entry": usb_bulk_receive.get("parser_handoff", {}).get("parser_entry"),
            "usb_bulk_parser_reads_via_callback": usb_bulk_receive.get("parser_handoff", {}).get(
                "parser_reads_via_param_0x0c_callback"
            ),
            "usb_bulk_callback_status": usb_bulk_callbacks.get("status"),
            "usb_bulk_event_bit": usb_bulk_callbacks.get("constants", {}).get("bulk_event_bit"),
            "usb_bulk_endpoint_ack_register": usb_bulk_callbacks.get("constants", {}).get(
                "usb_endpoint_ack_register"
            ),
            "usb_bulk_rearm_status": usb_bulk_rearm.get("status"),
            "usb_bulk_descriptor_pool": usb_bulk_rearm.get("constants", {}).get("descriptor_pool"),
            "usb_bulk_descriptor_submit_register": usb_bulk_rearm.get("constants", {}).get(
                "descriptor_submit_register"
            ),
            "sideband_0x26_risk": sideband_impacts.get("+0x26", {}).get("risk"),
            "sideband_0x32_risk": sideband_impacts.get("+0x32", {}).get("risk"),
            "sideband_0x30_risk": sideband_impacts.get("+0x30", {}).get("risk"),
            "sideband_access_hits": len(sideband_access_hits),
            "remaining_units_source_gap": sideband_unsourced_gap,
        },
        "open_probe_evidence": bulk_probe_evidence,
        "components": components,
        "blockers": blockers,
        "current_decision": "The USB bulk receive/framing component is ready only for its guarded mechanically inert hardware test; printing, semantic JobMgr/raster handoff, and all engine/video behavior remain unimplemented or unproven.",
    }


def render_markdown(scope: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 Minimal Printing-Only Replacement Scope",
        "",
        "This is a generated offline scope report. It does not contact the printer.",
        "",
        "## Goal",
        "",
        scope["goal"],
        "",
        "## Simple Readout",
        "",
        "For the narrow goal, we do not need to clone every HP firmware feature. We need:",
        "",
        "1. USB upload and USB identity/control handling.",
        "2. USB bulk receive of the host-generated ZjStream print file.",
        "3. A small ZjStream parser for the chunk types foo2zjs actually emits.",
        "4. Raster handoff into the video/raw-band hardware path.",
        "5. Engine coordination for paper, fuser, motor, and page timing.",
        "",
        "USB bulk receive and framing now have an offline-validated inert implementation. That does not implement semantic print dispatch, raster output, video transfer, or engine control.",
        "",
        "## Platform Boundary",
        "",
    ]
    boundary = scope["cross_platform_boundary"]
    for key, value in boundary.items():
        lines.append(f"- `{key}`: {value}")

    evidence = scope["stock_evidence"]
    lines.extend(
        [
            "",
            "## Current Evidence",
            "",
            f"- parser entry: `{evidence['parser_entry']}`",
            f"- JobMgr queue: `{evidence['jobmgr_queue']}`",
            f"- work objects modeled: `{evidence['work_objects']}`",
            f"- raster nodes modeled: `{evidence['raster_nodes']}`",
            f"- print-model invariant failures: `{evidence['model_invariant_failures']}`",
            f"- required JobMgr messages missing: `{', '.join(map(str, evidence['missing_required_messages'])) or 'none'}`",
            f"- endpoint-0 modeled data/stall cases: `{evidence['endpoint0_data_cases']}` / `{evidence['endpoint0_stall_cases']}`",
            f"- control completion event object: `{evidence['control_completion_event_object']}`",
            f"- USB TDC status bit: `{evidence['usb_tdc_status_bit']}`; wake alone establishes success: `{str(evidence['usb_wake_is_successful_completion']).lower()}`",
            f"- USB bulk interrupt lane: event bit `{evidence['usb_bulk_lane_event_bit']}`, status register `{evidence['usb_bulk_lane_status_register']}`, control register `{evidence['usb_bulk_lane_control_register']}`",
            f"- marker rearm-flow checks/failures: `{evidence['marker_rearm_checks']}` / `{evidence['marker_rearm_failures']}`",
            f"- USB bulk receive model: `{evidence['usb_bulk_receive_status']}`, record stride `{evidence['usb_bulk_transfer_record_stride']}`, receive buffer `{evidence['usb_bulk_receive_buffer_allocation']}`",
            f"- USB bulk parser handoff: parser `{evidence['usb_bulk_parser_entry']}`, read callback slot present `{str(evidence['usb_bulk_parser_reads_via_callback']).lower()}`",
            f"- USB bulk callback model: `{evidence['usb_bulk_callback_status']}`, event bit `{evidence['usb_bulk_event_bit']}`, OUT1 control register `{evidence['usb_bulk_endpoint_ack_register']}` (legacy callback field name)",
            f"- USB bulk re-arm model: `{evidence['usb_bulk_rearm_status']}`, descriptor pool `{evidence['usb_bulk_descriptor_pool']}`, submit register `{evidence['usb_bulk_descriptor_submit_register']}`",
            f"- sideband access hits classified: `{evidence['sideband_access_hits']}`",
            f"- sideband risk split: `+0x26={evidence['sideband_0x26_risk']}`, `+0x32={evidence['sideband_0x32_risk']}`, `+0x30={evidence['sideband_0x30_risk']}`",
            f"- remaining-unit active-work source gap: `{str(evidence['remaining_units_source_gap']).lower()}`",
            "",
            "## Open Bulk Parser Probe Evidence",
            "",
        ]
    )
    probe = scope["open_probe_evidence"]
    coverage = probe["coverage"]
    lines.extend(
        [
            f"- component status: `{probe['status']}`",
            f"- offline validated: `{str(probe['offline_validated']).lower()}`",
            f"- generated samples passed: `{coverage.get('generated_samples_passed')}/{coverage.get('generated_samples_discovered')}`",
            f"- deterministic matrix cases passed: `{coverage.get('synthetic_cases_passed')}/{coverage.get('synthetic_cases')}`",
            f"- total cases passed: `{coverage.get('total_cases_passed')}/{coverage.get('total_cases')}`",
            f"- assertions passed: `{coverage.get('assertions_passed')}/{coverage.get('assertions')}`",
            f"- recognized chunk scope: `{', '.join(probe['recognized_chunk_types'])}`",
            f"- generated sample cases: `{', '.join(probe['generated_sample_cases'])}`",
            f"- deterministic matrix cases: `{', '.join(probe['matrix_cases'])}`",
            f"- mechanically inert across all cases: `{str(probe['mechanically_inert_cases']).lower()}`",
            f"- printer/USB contacted during validation: `{str(probe['hardware_contact']).lower()}`",
            f"- report statuses: `{', '.join(f'{name}={status}' for name, status in probe['report_statuses'].items())}`",
            f"- report fail counts: `{', '.join(f'{name}={count}' for name, count in probe['report_fail_counts'].items())}`",
            f"- status descriptor: `{probe['status_descriptor_text']}` at `{probe['status_descriptor_address']}`",
            f"- reproducibility: `{probe['reproducibility_status']}`",
            "",
            "## Component Scope",
            "",
            "| Component | Status | Replacement need | Risk |",
            "|---|---|---|---|",
        ]
    )
    for item in scope["components"]:
        lines.append(
            f"| {item['component']} | `{item['current_status']}` | {item['replacement_need']} | `{item['risk']}` |"
        )

    lines.extend(["", "## Main Blockers", "", "| Blocker | Why | Next test/work |", "|---|---|---|"])
    for item in scope["blockers"]:
        lines.append(f"| {item['blocker']} | {item['why']} | {item['next_test']} |")

    lines.extend(
        [
            "",
            "## Current Decision",
            "",
            scope["current_decision"],
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-output", type=Path, default=OUT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=OUT_MD)
    args = parser.parse_args()

    scope = build_scope()
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(scope, indent=2, sort_keys=True) + "\n")
    args.markdown_output.write_text(render_markdown(scope) + "\n")
    print(args.markdown_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
