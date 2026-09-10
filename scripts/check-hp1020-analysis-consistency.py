#!/usr/bin/env python3
"""Cross-check the current offline HP 1020 reverse-engineering conclusions."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT_DIR / "analysis/offline-consistency/offline-consistency.json"
OUT_MD = ROOT_DIR / "analysis/offline-consistency/offline-consistency.md"
USB_BULK_PROBE_DIR = "analysis/open-firmware-probes/usb-bulk-parser-draft"

EXPECTED_BULK_PROBE_REPORTS = {
    "combined_contract": "analysis/usb-path/usb-bulk-probe-contract.json",
    "parser_model": f"{USB_BULK_PROBE_DIR}/parser-model.json",
    "deterministic_results": f"{USB_BULK_PROBE_DIR}/deterministic-test-results.json",
    "safety_scan": f"{USB_BULK_PROBE_DIR}/safety-scan.json",
    "usb_contract_scan": f"{USB_BULK_PROBE_DIR}/usb-contract-scan.json",
    "usb_mmio_access_scan": f"{USB_BULK_PROBE_DIR}/usb-mmio-access-scan.json",
    "memory_boundary_scan": f"{USB_BULK_PROBE_DIR}/memory-boundary-scan.json",
    "source_contract_check": f"{USB_BULK_PROBE_DIR}/source-contract-check.json",
    "status_descriptor_check": f"{USB_BULK_PROBE_DIR}/status-descriptor-check.json",
    "config_descriptor_check": f"{USB_BULK_PROBE_DIR}/config-descriptor-check.json",
    "reproducibility_check": f"{USB_BULK_PROBE_DIR}/reproducibility-check.json",
}

EXPECTED_BULK_GENERATED_SAMPLES = {
    "generated::matrix-a4_2400x600",
    "generated::matrix-a4_600x600",
    "generated::matrix-a4_cardstock_media",
    "generated::matrix-a4_default",
    "generated::matrix-a4_draft",
    "generated::matrix-a4_logical_clip",
    "generated::matrix-a4_manual_feed",
    "generated::matrix-a4_two_copies",
    "generated::matrix-legal_default",
    "generated::matrix-letter_default",
    "generated::minimal-page-a4",
}

EXPECTED_BULK_MATRIX_CASES = {
    *(f"header_split_{index:02d}_of_16" for index in range(1, 16)),
    *(f"magic_split_{index:02d}_of_4" for index in range(1, 4)),
    "payload_split_across_four_boundaries",
    "multiple_chunks_single_transfer",
    "stock_types_outside_probe_scope_are_unknown",
    "valid_zero_payload_chunks",
    "zero_size_chunk_recovery",
    "oversize_chunk_policy_recovery",
    "bad_signature_recovery",
    "reserved_exceeds_payload_recovery",
    "unknown_chunk_is_counted_and_skipped",
    "ring_and_descriptor_wrap_boundary",
    "payload_crosses_ring_wrap_boundary",
    "three_repeated_documents",
    "truncated_chunk_header_at_eof",
    "truncated_chunk_payload_at_eof",
    "zero_byte_receive_descriptors",
}

EXPECTED_BULK_REPORT_STATUSES = {
    "config_descriptors",
    "layout",
    "safety",
    "usb_contract",
    "usb_mmio",
    "endpoint0_sequence",
    "memory_boundary",
    "endpoint0_length",
    "endpoint0_rearm",
    "source_contract",
    "status_descriptor",
    "parser_model",
}

EXPECTED_BULK_SIDE_EFFECTS = {
    "usb_device_opens": 0,
    "usb_transfers_submitted": 0,
    "mmio_reads": 0,
    "mmio_writes": 0,
    "video_commands": 0,
    "engine_commands": 0,
    "mechanical_actions": 0,
}

EXPECTED_BULK_REGISTERS = {
    "0xb3000200",
    "0xb3000220",
    "0xb3000224",
    "0xb300022c",
    "0xb3000234",
    "0xb3000404",
    "0xb3000418",
    "0xb3010000",
}

EXPECTED_STATUS_DESCRIPTOR = (
    "HP1020 B=00000000 D=00000000 C=00000000 E=00000000 U=00000000"
)


def read_json(rel: str) -> Any:
    return json.loads((ROOT_DIR / rel).read_text())


def read_text(rel: str) -> str:
    return (ROOT_DIR / rel).read_text()


def read_tsv(rel: str) -> list[dict[str, str]]:
    with (ROOT_DIR / rel).open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return [{key.lstrip("# ").strip(): value for key, value in row.items()} for row in reader]


def check(name: str, ok: bool, detail: str, *, evidence: str) -> dict[str, str]:
    return {
        "name": name,
        "severity": "watch" if ok else "fail",
        "detail": detail,
        "evidence": evidence,
    }


def severity_count(items: list[dict[str, Any]], severity: str) -> int:
    return sum(item.get("severity") == severity for item in items)


def nested_fail_count(value: Any) -> int:
    """Count explicit fail markers in dict- and list-shaped generated reports."""

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


def report_check_items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict) and isinstance(value.get("checks"), list):
        return [item for item in value["checks"] if isinstance(item, dict)]
    return []


def build_report() -> dict[str, Any]:
    checks: list[dict[str, str]] = []

    dispatch_md = read_text("analysis/engine-dispatch-cfg/engine-dispatch-cfg.md")
    registration = read_json("analysis/queue-routing/registration.json")
    registered = {r["queue"]: (r["name"], r["object"]) for r in registration["registrations"]}
    checks.append(check("engine_0x17_dispatch_is_default",
                        "| `0x17` | `100162aa` | default return/no-op |" in dispatch_md,
                        "Engine queue 0 has no 0x17 command case; actual status producers target PrintMgr queue 1.",
                        evidence="analysis/engine-dispatch-cfg/engine-dispatch-cfg.md"))
    checks.append(check("stock_queue_registration",
                        registered[0] == ("engMsgQ", "0x1002f134")
                        and registered[1] == ("PrintMgrQueue", "0x10028a74")
                        and registered[3] == ("Job Mgr Queue", "0x10023e40")
                        and len(registered) == 7 and len(registration["helper_cases"]) == 48
                        and registration["source_sha256"] == hashlib.sha256((ROOT_DIR/"scripts/audit-hp1020-queue-registration.py").read_bytes()).hexdigest(),
                        "Stock constructor control flow must preserve the corrected queue identities and independent registration-helper audit.",
                        evidence="analysis/queue-routing/registration.json"))

    pipeline = read_json("analysis/open-firmware-model/stock-execution/pipeline.json")
    checks.append(check("original_native_pipeline_execution",
                        pipeline["status"] == "pass" and pipeline["total_cases"] == 32
                        and pipeline["completed_lifecycles"] == 26
                        and pipeline["reproduced_conditional_stops"] == 6
                        and sum(c["status"] == "pass" for c in pipeline["cases"]) == 26
                        and sum(c["status"] == "reproduced_conditional_null_read"
                                and c["pc"] == "0x1000e9f4" and c["head"] == "0x0"
                                and c["cancel"] == 1 and not c["lifecycle_completed"]
                                for c in pipeline["cases"]) == 6
                        and all(hashlib.sha256((ROOT_DIR/"scripts"/p).read_bytes()).hexdigest() == h
                                for p,h in pipeline["source_sha256"].items()),
                        "Completed native lifecycles and conditional original null reads must remain separate, reproducible outcomes.",
                        evidence="analysis/open-firmware-model/stock-execution/pipeline.json"))

    for name, total in (("printmgr",40),("notifications",12),("stop",90),("cancellation",48),("status-publication",15),("queue",80),("status-queue",8),("context",180),("scheduler",80),("scheduled-status",30),("pool",93),("timers",44),("retirement",28)):
        execution = read_json(f"analysis/open-firmware-model/stock-execution/{name}.json")
        checks.append(check(f"original_{name}_execution",
                            execution["status"] == "pass" and execution["total_cases"] == total
                            and all(c["status"] == "pass" for c in execution["cases"])
                            and (name != "stop" or execution["prefix_gate"]["status"] == "blocked"
                                 and execution["instruction_span_gate"]["status"] == "blocked")
                            and (name != "retirement" or sum(c["outcome"] == "blocked_next_path"
                                 and c["stop"] == "native tasks left selected code: 0x1001434b"
                                 for c in execution["cases"]) == 2)
                            and all(hashlib.sha256((ROOT_DIR/"scripts"/p).read_bytes()).hexdigest() == h
                                    for p,h in execution["source_sha256"].items()),
                            "Original routing and allocation ownership must agree with QEMU and explicit fixture oracles.",
                            evidence=f"analysis/open-firmware-model/stock-execution/{name}.json"))

    pages = read_json("analysis/open-firmware-model/stock-execution/pages.json")
    checks.append(check("original_native_page_execution",
                        pages["status"] == "pass" and pages["total_cases"] == 18
                        and pages["completed_lifecycles"] == 18 and len(pages["cases"]) == 18
                        and {(c["documents"], c["pages"], c["fill"], c["ticks_per_page"],
                              c["consumed_cleanup_event"]) for c in pages["cases"]}
                            == {(d,p,f,t,e) for d,p in ((1,1),(1,3),(3,3))
                                for f in (0,204) for t,e in ((0,False),(2,False),(2,True))}
                        and all(c["status"] == "pass"
                                and c["scheduled_work"] == c["completed_work"]
                                and c["delivered_ticks"] == c["ticks_per_page"] * c["pages"]
                                and c["cleanup_before_completion"]
                                    == [bool(c["ticks_per_page"]) and not c["consumed_cleanup_event"]] * c["pages"]
                                and c["remaining_allocation_bytes"] == 20
                                for c in pages["cases"])
                        and all(hashlib.sha256((ROOT_DIR/"scripts"/p).read_bytes()).hexdigest() == h
                                for p,h in pages["source_sha256"].items()),
                        "Supplied FIFO consumption and controlled timed cleanup must retain separate causal controls and current source provenance.",
                        evidence="analysis/open-firmware-model/stock-execution/pages.json"))

    fragments = read_json("analysis/open-firmware-model/stock-execution/page-fragments.json")
    fragment_stop = read_json("analysis/open-firmware-model/stock-execution/page-fragment-limit.json")
    checks.append(check("original_native_fragment_execution",
                        fragments["status"] == "pass" and fragments["total_cases"] == 18
                        and fragments["completed_lifecycles"] == 18 and len(fragments["cases"]) == 18
                        and {(c["raster_chunks"],c["fill"],c["ticks_per_page"],c["consumed_cleanup_event"])
                             for c in fragments["cases"]}
                            == {(n,f,t,e) for n in (6,13,64) for f in (0,204)
                                for t,e in ((0,False),(2,False),(2,True))}
                        and all(c["status"] == "pass" and c["instructions"] < c["instruction_budget"]
                                and c["instruction_budget"] == (250000 if c["raster_chunks"] == 64 else 200000)
                                and len(c["reference_decrements"]) == len(c["event_calls"]) == c["raster_chunks"]
                                and c["remaining_allocation_bytes"] == 20 for c in fragments["cases"])
                        and fragment_stop["outcome"] == "instruction_budget_exhausted"
                        and fragment_stop["steps"] == 200000 and not fragment_stop["lifecycle_completed"]
                        and fragments["baseline_page_report_sha256"]
                            == hashlib.sha256((ROOT_DIR/"analysis/open-firmware-model/stock-execution/pages.json").read_bytes()).hexdigest()
                        and all(hashlib.sha256((ROOT_DIR/"scripts"/p).read_bytes()).hexdigest() == h
                                for p,h in fragments["source_sha256"].items()),
                        "Larger raster lists must retain explicit budgets, complete ownership checks and a separate historical budget stop.",
                        evidence="analysis/open-firmware-model/stock-execution/page-fragments.json"))

    event_rows = read_tsv("analysis/engine-events/engine-0x17-events.tsv")
    status_corr = read_json("analysis/status-path/status-code-correlation.json")
    direct_counts = status_corr.get("direct_converter_class_counts", {})
    checks.append(
        check(
            "status_correlation_event_count_matches_source",
            status_corr.get("event_count") == len(event_rows) == 21,
            "Status correlation must account for every currently cataloged engine 0x17 event word.",
            evidence="analysis/status-path/status-code-correlation.json",
        )
    )
    checks.append(
        check(
            "engine_events_are_not_direct_pjl_codes",
            direct_counts == {"not a proven direct input to CODE converter": 21},
            "Raw engine event words must not be mislabeled as final PJL CODE values.",
            evidence="analysis/status-path/status-code-correlation.json",
        )
    )

    invariants = read_json("analysis/open-firmware-model/model-invariants.json")
    invariant_cases = {item.get("case") for item in invariants}
    expected_cases = {
        "base",
        "a4_2400x600",
        "a4_600x600",
        "a4_cardstock_media",
        "a4_default",
        "a4_draft",
        "a4_logical_clip",
        "a4_manual_feed",
        "a4_two_copies",
        "legal_default",
        "letter_default",
    }
    checks.append(
        check(
            "print_model_invariants_have_no_failures",
            severity_count(invariants, "fail") == 0 and len(invariants) >= 200,
            "Offline ZjStream model invariants must remain green across generated print-path variants.",
            evidence="analysis/open-firmware-model/model-invariants.json",
        )
    )
    checks.append(
        check(
            "print_model_variant_coverage",
            expected_cases.issubset(invariant_cases),
            "Invariant coverage must include paper size, resolution, copy, draft, source, media, and clip variants.",
            evidence="analysis/open-firmware-model/model-invariants.json",
        )
    )

    minimal_scope = read_json("analysis/open-firmware-model/minimal-print-scope.json")
    usb_bulk_receive = read_json("analysis/usb-path/usb-bulk-receive-model.json")
    usb_bulk_callbacks = read_json("analysis/usb-path/usb-bulk-callbacks-model.json")
    usb_bulk_rearm = read_json("analysis/usb-path/usb-bulk-rearm-model.json")
    usb_parser_shim = read_json("analysis/usb-path/usb-parser-shim-contract.json")
    usb_interrupt_events_for_bulk = read_json("analysis/usb-path/usb-interrupt-events.json")
    bulk_probe_reports = {
        name: read_json(path) for name, path in EXPECTED_BULK_PROBE_REPORTS.items()
    }
    bulk_probe_contract = bulk_probe_reports["combined_contract"]
    bulk_parser_model = bulk_probe_reports["parser_model"]
    bulk_deterministic = bulk_probe_reports["deterministic_results"]
    bulk_safety = bulk_probe_reports["safety_scan"]
    bulk_usb_contract = bulk_probe_reports["usb_contract_scan"]
    bulk_usb_mmio = bulk_probe_reports["usb_mmio_access_scan"]
    bulk_memory = bulk_probe_reports["memory_boundary_scan"]
    bulk_source_contract = bulk_probe_reports["source_contract_check"]
    bulk_status_descriptor = bulk_probe_reports["status_descriptor_check"]
    bulk_config_descriptor = bulk_probe_reports["config_descriptor_check"]
    bulk_reproducibility = bulk_probe_reports["reproducibility_check"]
    bulk_summary = read_text(f"{USB_BULK_PROBE_DIR}/summary.md")
    bulk_hardware_plan = read_text(f"{USB_BULK_PROBE_DIR}/hardware-test-plan.md")
    bulk_report_statuses = {
        name: report_status(report) for name, report in bulk_probe_reports.items()
    }
    bulk_report_fail_counts = {
        name: nested_fail_count(report) for name, report in bulk_probe_reports.items()
    }
    usb_bulk_checks = usb_bulk_receive.get("checks", [])
    usb_bulk_callback_checks = usb_bulk_callbacks.get("checks", [])
    usb_bulk_rearm_checks = usb_bulk_rearm.get("checks", [])
    scope_components = {
        item.get("component"): item
        for item in minimal_scope.get("components", [])
        if isinstance(item, dict)
    }
    scope_evidence = minimal_scope.get("stock_evidence", {})
    open_probe_evidence = minimal_scope.get("open_probe_evidence", {})
    checks.append(
        check(
            "minimal_print_scope_keeps_parser_mapped_and_hardware_blocked",
            scope_evidence.get("missing_required_messages") == []
            and scope_evidence.get("model_invariant_failures") == 0
            and scope_evidence.get("endpoint0_data_cases") == 24
            and scope_evidence.get("usb_bulk_lane_event_bit") == "0x00020000"
            and scope_evidence.get("usb_bulk_lane_status_register") == "0xb3000224"
            and scope_evidence.get("usb_bulk_lane_ack_register") == "0xb3000220"
            and scope_evidence.get("usb_bulk_receive_status") == "pass"
            and scope_evidence.get("usb_bulk_transfer_record_stride") == "0x58"
            and scope_evidence.get("usb_bulk_receive_buffer_allocation") == "0x400 bytes"
            and scope_evidence.get("usb_bulk_parser_entry") == "0x10009d34"
            and scope_evidence.get("usb_bulk_parser_reads_via_callback") is True
            and scope_evidence.get("usb_bulk_callback_status") == "pass"
            and scope_evidence.get("usb_bulk_event_bit") == "0x00020000"
            and scope_evidence.get("usb_bulk_endpoint_ack_register") == "0xb3000220"
            and scope_evidence.get("usb_bulk_rearm_status") == "pass"
            and scope_evidence.get("usb_bulk_descriptor_pool") == "0x90021370"
            and scope_evidence.get("usb_bulk_descriptor_submit_register") == "0xb3000234"
            and scope_components.get("ZjStream parser and JobMgr object model", {}).get("current_status") == "mapped"
            and scope_components.get("USB bulk receive to ZjStream parser", {}).get("current_status")
            == "implemented and offline validated"
            and "no print handoff"
            in scope_components.get("USB bulk receive to ZjStream parser", {}).get("replacement_need", "")
            and scope_components.get("Video sideband policy", {}).get("current_status") == "direct START_PAGE source verified"
            and scope_components.get("Video sideband policy", {}).get("risk") == "high"
            and scope_components.get("Video/raw-band hardware feed", {}).get("risk") == "high"
            and scope_components.get("Engine paper/fuser/motor coordination", {}).get("risk") == "high"
            and scope_evidence.get("sideband_access_hits") == 19
            and scope_evidence.get("sideband_0x26_risk") == "critical"
            and scope_evidence.get("remaining_units_source_gap") is False
            and open_probe_evidence.get("status") == "implemented and offline validated"
            and open_probe_evidence.get("offline_validated") is True
            and open_probe_evidence.get("mechanically_inert_cases") is True
            and open_probe_evidence.get("hardware_contact") is False
            and open_probe_evidence.get("recognized_chunk_types")
            == ["0x00", "0x01", "0x02", "0x03", "0x04", "0x05", "0x06"]
            and open_probe_evidence.get("status_descriptor_address") == "0x10003400"
            and set(open_probe_evidence.get("generated_sample_cases", []))
            == EXPECTED_BULK_GENERATED_SAMPLES
            and set(open_probe_evidence.get("matrix_cases", [])) == EXPECTED_BULK_MATRIX_CASES
            and open_probe_evidence.get("report_statuses") == bulk_report_statuses
            and open_probe_evidence.get("report_fail_counts") == bulk_report_fail_counts
            and all(status == "pass" for status in open_probe_evidence.get("report_statuses", {}).values())
            and all(count == 0 for count in open_probe_evidence.get("report_fail_counts", {}).values())
            and "printing, semantic JobMgr/raster handoff, and all engine/video behavior remain unimplemented"
            in minimal_scope.get("current_decision", ""),
            "The generated narrow-scope report must mark only the inert USB bulk receive/framing component implemented offline, retain semantic parser and engine/video blockers, and carry exact probe evidence.",
            evidence="analysis/open-firmware-model/minimal-print-scope.json",
        )
    )
    checks.append(
        check(
            "usb_bulk_receive_model_preserves_parser_handoff",
            usb_bulk_receive.get("status") == "pass"
            and usb_bulk_receive.get("transfer_record", {}).get("record_stride") == "0x58"
            and usb_bulk_receive.get("transfer_record", {}).get("buffer_allocation") == "0x400 bytes"
            and usb_bulk_receive.get("parser_handoff", {}).get("usb2thread_descriptor") == "0x10005fc4"
            and usb_bulk_receive.get("parser_handoff", {}).get("parser_entry") == "0x10009d34"
            and usb_bulk_receive.get("parser_handoff", {}).get("parser_reads_via_param_0x0c_callback") is True
            and usb_bulk_receive.get("parser_handoff", {}).get("parser_sends_jobmgr_queue") == 3
            and all(item.get("status") == "present" for item in usb_bulk_checks),
            "The USB bulk receive model must keep the stock transfer-record registration, 0x400-byte receive buffer, and parser read-callback handoff mapped.",
            evidence="analysis/usb-path/usb-bulk-receive-model.json",
        )
    )
    checks.append(
        check(
            "usb_bulk_callback_model_preserves_event_and_rearm_path",
            usb_bulk_callbacks.get("status") == "pass"
            and usb_bulk_callbacks.get("constants", {}).get("bulk_event_bit") == "0x00020000"
            and usb_bulk_callbacks.get("constants", {}).get("usb_endpoint_ack_register") == "0xb3000220"
            and usb_bulk_callbacks.get("constants", {}).get("usb_status_register") == "0xb3000418"
            and usb_bulk_callbacks.get("constants", {}).get("pending_transfer_list") == "0x10022740"
            and any(item.get("address") == "0x100087b8" and item.get("name") == "bulk_rx_read" for item in usb_bulk_callbacks.get("callback_roles", []))
            and any(item.get("address") == "0x10008bac" and item.get("name") == "bulk_rx_complete" for item in usb_bulk_callbacks.get("callback_roles", []))
            and all(item.get("status") == "present" for item in usb_bulk_callback_checks),
            "The USB bulk callback model must preserve the read/copy callback, completion queue callback, event bit, endpoint ack register, and status-bit clear.",
            evidence="analysis/usb-path/usb-bulk-callbacks-model.json",
        )
    )
    checks.append(
        check(
            "usb_bulk_rearm_model_preserves_descriptor_submit",
            usb_bulk_rearm.get("status") == "pass"
            and usb_bulk_rearm.get("constants", {}).get("descriptor_pool") == "0x90021370"
            and usb_bulk_rearm.get("constants", {}).get("bulk_buffer_base") == "0x900216f0"
            and usb_bulk_rearm.get("constants", {}).get("descriptor_submit_register") == "0xb3000234"
            and usb_bulk_rearm.get("constants", {}).get("bulk_done_byte") == "0x1001bc70"
            and usb_bulk_rearm.get("constants", {}).get("bulk_rx_done_flag") == "0x1001bc72"
            and all(item.get("status") == "present" for item in usb_bulk_rearm_checks),
            "The USB bulk re-arm model must preserve descriptor pool, buffer base, submit register, and done-flag behavior.",
            evidence="analysis/usb-path/usb-bulk-rearm-model.json",
        )
    )
    shim_contract = usb_parser_shim.get("implementation_contract", {})
    checks.append(
        check(
            "usb_parser_shim_contract_preserves_next_software_target",
            usb_parser_shim.get("status") == "pass"
            and shim_contract.get("parser_boundary", {}).get("parser_entry") == "0x10009d34"
            and shim_contract.get("parser_boundary", {}).get("parser_read_callback_slot") == "param_1 + 0x0c"
            and shim_contract.get("bulk_read_state", {}).get("wait_event_bit") == "0x00020000"
            and shim_contract.get("hardware_receive_lane", {}).get("lane_status_register") == "0xb3000224"
            and shim_contract.get("descriptor_rearm", {}).get("descriptor_pool") == "0x90021370"
            and shim_contract.get("descriptor_rearm", {}).get("descriptor_submit_register") == "0xb3000234",
            "The synthesized USB parser-shim contract must keep the next target anchored to parser callback, bulk event bit, hardware lane, and descriptor re-arm facts.",
            evidence="analysis/usb-path/usb-parser-shim-contract.json",
        )
    )

    bulk_contract_checks = {
        item.get("name"): item
        for item in bulk_probe_contract.get("checks", [])
        if isinstance(item, dict)
    }
    bulk_source_checks = {
        item.get("name"): item for item in report_check_items(bulk_source_contract)
    }
    bulk_status_checks = {
        item.get("name"): item for item in report_check_items(bulk_status_descriptor)
    }
    bulk_config_checks = {
        item.get("name"): item for item in report_check_items(bulk_config_descriptor)
    }
    bulk_generated_samples = bulk_parser_model.get("generated_samples", [])
    bulk_matrix_cases = bulk_parser_model.get("test_matrix", [])
    bulk_all_cases = [*bulk_generated_samples, *bulk_matrix_cases]
    bulk_coverage = bulk_parser_model.get("coverage", {})
    bulk_probe_type_rows = bulk_parser_model.get("probe_recognized_chunk_types", [])
    bulk_probe_types = [
        (item.get("type"), item.get("type_hex"), item.get("name"))
        for item in bulk_probe_type_rows
        if isinstance(item, dict)
    ]
    bulk_mmio_accesses = {
        (item.get("register"), item.get("access"))
        for item in bulk_usb_mmio
        if isinstance(item, dict)
    }
    bulk_memory_accesses = {
        (item.get("kind"), item.get("access"))
        for item in bulk_memory
        if isinstance(item, dict)
    }
    interrupt_bulk_lane = (
        usb_interrupt_events_for_bulk.get("event_scan", {}).get("bulk_receive_lane", {})
    )
    probe_registers = bulk_probe_contract.get("registers", {})
    probe_allowed_memory = bulk_probe_contract.get("allowed_memory", {})
    deterministic_reports = bulk_deterministic.get("reports", {})
    deterministic_artifacts = bulk_deterministic.get("artifacts", {})
    reproduction_files = {
        item.get("file"): item
        for item in bulk_reproducibility.get("files", [])
        if isinstance(item, dict)
    }

    checks.append(
        check(
            "usb_bulk_probe_all_required_reports_pass",
            set(bulk_report_statuses) == set(EXPECTED_BULK_PROBE_REPORTS)
            and all(status == "pass" for status in bulk_report_statuses.values())
            and set(bulk_report_fail_counts) == set(EXPECTED_BULK_PROBE_REPORTS)
            and all(count == 0 for count in bulk_report_fail_counts.values())
            and bulk_deterministic.get("status") == "pass"
            and set(deterministic_reports) == EXPECTED_BULK_REPORT_STATUSES
            and all(status == "pass" for status in deterministic_reports.values())
            and bulk_deterministic.get("hardware_contact") is False
            and len(bulk_source_checks) == 43
            and all(item.get("severity") == "pass" for item in bulk_source_checks.values())
            and "mechanically inert" in bulk_summary
            and "was not uploaded to a printer" in bulk_summary
            and "guarded" in bulk_hardware_plan.lower(),
            "Every required bulk-parser report must exist, carry a passing status or zero fail markers, agree with the deterministic rollup, and retain offline-only handoff documents.",
            evidence=f"{USB_BULK_PROBE_DIR}/deterministic-test-results.json",
        )
    )
    checks.append(
        check(
            "usb_bulk_probe_lane_contract_matches_stock_models",
            bulk_probe_contract.get("status") == "pass"
            and set(bulk_probe_contract.get("bulk_registers", [])) == EXPECTED_BULK_REGISTERS
            and set(bulk_contract_checks)
            == {
                "bulk_lane_matches_interrupt_model",
                "descriptor_submit_matches_rearm_model",
                "callback_ack_matches_contract",
                "all_bulk_registers_are_usb_only",
                "stock_elf_contains_resolved_bulk_literals",
                "saved_decompilation_preserves_bulk_contract",
            }
            and all(item.get("status") == "present" for item in bulk_contract_checks.values())
            and interrupt_bulk_lane.get("event_bit") == "0x00020000"
            and interrupt_bulk_lane.get("lane_status_register") == "0xb3000224"
            and interrupt_bulk_lane.get("lane_ack_register") == "0xb3000220"
            and usb_bulk_callbacks.get("constants", {}).get("bulk_event_bit") == "0x00020000"
            and usb_bulk_callbacks.get("constants", {}).get("usb_endpoint_ack_register")
            == "0xb3000220"
            and shim_contract.get("bulk_read_state", {}).get("wait_event_bit") == "0x00020000"
            and shim_contract.get("hardware_receive_lane", {}).get("lane_status_register")
            == "0xb3000224"
            and shim_contract.get("hardware_receive_lane", {}).get("lane_ack_register")
            == "0xb3000220"
            and {"0xb3000220", "0xb3000224"}.issubset(probe_registers)
            and ("0xb3000224", "read") in bulk_mmio_accesses
            and ("0xb3000224", "write") in bulk_mmio_accesses
            and ("0xb3000220", "write") in bulk_mmio_accesses
            and all(
                bulk_source_checks.get(name, {}).get("severity") == "pass"
                for name in (
                    "bulk_completion_poll",
                    "bulk_completion_ack_and_control",
                    "bulk_rearm_paths",
                )
            ),
            "The combined allowlist and probe disassembly must preserve the stock bank-1/lane-1 event bit, status register, and acknowledgement register without substituting another USB lane.",
            evidence="analysis/usb-path/usb-bulk-probe-contract.json",
        )
    )
    checks.append(
        check(
            "usb_bulk_probe_descriptor_buffer_submit_contract_matches",
            usb_bulk_rearm.get("constants", {}).get("descriptor_pool") == "0x90021370"
            and usb_bulk_rearm.get("constants", {}).get("bulk_buffer_base") == "0x900216f0"
            and usb_bulk_rearm.get("constants", {}).get("descriptor_submit_register")
            == "0xb3000234"
            and shim_contract.get("descriptor_rearm", {}).get("descriptor_pool") == "0x90021370"
            and shim_contract.get("descriptor_rearm", {}).get("bulk_buffer_base") == "0x900216f0"
            and shim_contract.get("descriptor_rearm", {}).get("descriptor_submit_register")
            == "0xb3000234"
            and probe_allowed_memory.get("bulk_descriptor")
            == {"start": "0x90021370", "end": "0x9002137f"}
            and probe_allowed_memory.get("bulk_buffer")
            == {"start": "0x900216f0", "end": "0x90021aef"}
            and probe_registers.get("0xb3000234", {}).get("allowed_write_values")
            == ["0x90021370"]
            and ("0xb3000234", "write") in bulk_mmio_accesses
            and ("usb_bulk_transfer_descriptor", "write") in bulk_memory_accesses
            and ("usb_bulk_receive_buffer", "read") in bulk_memory_accesses
            and all(
                bulk_source_checks.get(name, {}).get("severity") == "pass"
                for name in (
                    "exact_16_byte_descriptor_construction",
                    "descriptor_alignment",
                    "descriptor_submit",
                )
            ),
            "The stock re-arm model, shim contract, combined allowlist, memory scan, and disassembly must agree on descriptor 0x90021370, buffer 0x900216f0, and submit register 0xb3000234.",
            evidence=f"{USB_BULK_PROBE_DIR}/memory-boundary-scan.json",
        )
    )
    checks.append(
        check(
            "usb_bulk_probe_exact_parser_scope_and_matrix_pass",
            bulk_parser_model.get("status") == "pass"
            and bulk_parser_model.get("failures") == []
            and bulk_coverage
            == {
                "assertions": 425,
                "assertions_passed": 425,
                "generated_samples_discovered": 11,
                "generated_samples_passed": 11,
                "synthetic_cases": 33,
                "synthetic_cases_passed": 33,
                "total_cases": 44,
                "total_cases_passed": 44,
            }
            and set(item.get("name") for item in bulk_generated_samples)
            == EXPECTED_BULK_GENERATED_SAMPLES
            and set(item.get("name") for item in bulk_matrix_cases) == EXPECTED_BULK_MATRIX_CASES
            and len(bulk_generated_samples) == len(EXPECTED_BULK_GENERATED_SAMPLES)
            and len(bulk_matrix_cases) == len(EXPECTED_BULK_MATRIX_CASES)
            and all(item.get("status") == "pass" for item in bulk_all_cases)
            and bulk_probe_types
            == [
                (0, "0x00", "ZJT_START_DOC"),
                (1, "0x01", "ZJT_END_DOC"),
                (2, "0x02", "ZJT_START_PAGE"),
                (3, "0x03", "ZJT_END_PAGE"),
                (4, "0x04", "ZJT_JBIG_BIH"),
                (5, "0x05", "ZJT_JBIG_BID"),
                (6, "0x06", "ZJT_END_JBIG"),
            ]
            and all(
                item.get("status") == "pass"
                for item in bulk_parser_model.get("evidence_checks", [])
            )
            and any(
                item.get("name") == "probe_scope_matches_controlled_sample_types_0x00_through_0x06"
                and item.get("status") == "pass"
                for item in bulk_parser_model.get("evidence_checks", [])
            )
            and bulk_source_checks.get("recognized_type_bound_7", {}).get("severity") == "pass"
            and all(
                bulk_source_checks.get(f"counter_update_{name}", {}).get("severity") == "pass"
                for name in (
                    "bytes_received",
                    "receive_descriptors_completed",
                    "recognized_chunks",
                    "parser_errors",
                    "unknown_chunks",
                )
            )
            and bulk_deterministic.get("parser_coverage") == bulk_coverage,
            "The executable model and deterministic rollup must preserve exactly 11 generated samples, 33 boundary/error cases, 425 assertions, and recognized types 0x00 through 0x06.",
            evidence=f"{USB_BULK_PROBE_DIR}/parser-model.json",
        )
    )
    checks.append(
        check(
            "usb_bulk_probe_has_no_mechanical_or_print_side_effects",
            bulk_parser_model.get("scope", {}).get("execution") == "offline host-side only"
            and bulk_parser_model.get("scope", {}).get("hardware_access")
            == "none; no USB device, MMIO, video, or engine path exists in this model"
            and bulk_parser_model.get("scope", {}).get("mechanical_behavior")
            == "none; payloads are length-counted and discarded"
            and bulk_all_cases
            and all(
                item.get("parser_state", {}).get("side_effects") == EXPECTED_BULK_SIDE_EFFECTS
                for item in bulk_all_cases
            )
            and bool(bulk_safety)
            and nested_fail_count(bulk_safety) == 0
            and all(item.get("kind") == "usb_mmio" for item in bulk_safety)
            and bool(bulk_usb_contract)
            and nested_fail_count(bulk_usb_contract) == 0
            and all(item.get("kind") == "mapped_usb_mmio" for item in bulk_usb_contract)
            and bool(bulk_usb_mmio)
            and nested_fail_count(bulk_usb_mmio) == 0
            and all(item.get("register") in probe_registers for item in bulk_usb_mmio)
            and bool(bulk_memory)
            and nested_fail_count(bulk_memory) == 0
            and all(item.get("kind") != "unclassified_hardware_alias" for item in bulk_memory)
            and bulk_source_checks.get("no_engine_video_mechanical_mmio", {}).get("severity")
            == "pass"
            and bulk_source_checks.get("hardware_alias_literal_allowlist", {}).get("severity")
            == "pass"
            and bulk_source_checks.get("no_alternate_xqx_magic", {}).get("severity") == "pass"
            and bulk_source_checks.get(
                "polling_masks_cpu_interrupts_before_usb_setup", {}
            ).get("severity")
            == "pass"
            and "never reaches engine, video, laser, fuser, motor, or paper-feed code"
            in bulk_summary,
            "Offline parser cases and every source/disassembly boundary scan must show zero USB-host contact, print dispatch, video, engine, or mechanical side effects.",
            evidence=f"{USB_BULK_PROBE_DIR}/safety-scan.json",
        )
    )
    checks.append(
        check(
            "usb_bulk_probe_status_descriptor_exposes_all_counters",
            bulk_status_descriptor.get("status") == "pass"
            and bulk_status_descriptor.get("descriptor_text") == EXPECTED_STATUS_DESCRIPTOR
            and bulk_status_descriptor.get("section", {}).get("address") == 0x10003400
            and bulk_status_descriptor.get("section", {}).get("size") == 0x7C
            and bulk_status_descriptor.get("section", {}).get("flags", 0) & 0x1 == 0x1
            and set(bulk_status_checks)
            == {
                "descriptor_bytes",
                "descriptor_address",
                "descriptor_writable",
                "length_constant",
                "local_pointer",
                "hardware_alias",
                "counter_patch_calls",
                "product_selects_status_alias",
            }
            and all(item.get("status") == "pass" for item in bulk_status_checks.values())
            and set(bulk_parser_model.get("counter_definitions", {}))
            == {
                "bytes_received",
                "receive_descriptors_completed",
                "recognized_chunks",
                "parser_errors",
                "unknown_chunks",
            }
            and bulk_source_checks.get("dynamic_status_counter_macro", {}).get("severity")
            == "pass"
            and bulk_source_checks.get("dynamic_product_status_counter_calls", {}).get("severity")
            == "pass",
            "The writable product string must expose B/D/C/E/U as the parser model's bytes, descriptors, recognized chunks, errors, and unknown chunks counters.",
            evidence=f"{USB_BULK_PROBE_DIR}/status-descriptor-check.json",
        )
    )
    checks.append(
        check(
            "usb_bulk_probe_config_descriptors_match_controller_speed",
            bulk_config_descriptor.get("status") == "pass"
            and set(bulk_config_checks)
            == {
                "descriptor_section_address",
                "descriptor_section_size",
                "high_speed_config_shape",
                "full_speed_config_shape",
                "high_speed_bulk_packets",
                "full_speed_bulk_packets",
                "high_speed_alias",
                "full_speed_alias",
                "speed_bit_branch",
            }
            and all(item.get("status") == "pass" for item in bulk_config_checks.values())
            and bulk_config_descriptor.get("section", {}).get("address") == 0x10003300
            and bulk_source_checks.get("speed_specific_config_alias_selection", {}).get("severity")
            == "pass"
            and probe_registers.get("0xb3010000", {}).get("allowed_write_masks")
            == ["or 0x00000005"],
            "The linked printer-class configurations must advertise 512-byte high-speed and 64-byte full-speed bulk endpoints, selected from the same b3010000 speed bit used by receive setup.",
            evidence=f"{USB_BULK_PROBE_DIR}/config-descriptor-check.json",
        )
    )
    checks.append(
        check(
            "usb_bulk_probe_rebuild_is_reproducible",
            bulk_reproducibility.get("status") == "pass"
            and bulk_reproducibility.get("clean_generated_output_between_builds") is True
            and bulk_reproducibility.get("required_missing") == []
            and bulk_reproducibility.get("compared_files") == len(reproduction_files)
            and len(reproduction_files) > 0
            and all(
                item.get("status") == "pass"
                and item.get("first_sha256") == item.get("second_sha256")
                and isinstance(item.get("first_sha256"), str)
                and len(item["first_sha256"]) == 64
                for item in reproduction_files.values()
            )
            and all(
                reproduction_files.get(f"hp1020-usb-bulk-parser-draft.{suffix}", {}).get(
                    "second_sha256"
                )
                == deterministic_artifacts.get(suffix, {}).get("sha256")
                and deterministic_artifacts.get(suffix, {}).get("bytes", 0) > 0
                for suffix in ("elf", "img", "dl", "map")
            ),
            "Two clean builds must produce byte-identical generated files, and the second-build firmware hashes must match the deterministic artifact rollup.",
            evidence=f"{USB_BULK_PROBE_DIR}/reproducibility-check.json",
        )
    )
    raster_fields = read_json("analysis/open-firmware-model/raster-field-semantics.json")
    raster_semantics = {
        item.get("field"): item
        for item in raster_fields.get("field_semantics", [])
        if isinstance(item, dict)
    }
    raster_cases = {
        item.get("case"): item
        for item in raster_fields.get("case_matrix", [])
        if isinstance(item, dict)
    }
    checks.append(
        check(
            "raster_field_semantics_keep_host_to_video_chain",
            raster_fields.get("status") == "pass"
            and len(raster_cases) >= 11
            and {"work +0x84", "work +0x88", "work +0x8c", "work +0x90", "payload +0x48", "payload +0x54"}.issubset(
                raster_semantics
            )
            and raster_cases.get("a4_default", {}).get("work_0x84_0x88_0x8c_0x90") == "9600/6824/128/0x5c"
            and raster_cases.get("a4_600x600", {}).get("work_0x84_0x88_0x8c_0x90") == "4864/6824/128/0x5c"
            and raster_cases.get("legal_default", {}).get("payload_0x48") == 6388
            and all(item.get("status") == "present" for item in raster_fields.get("checks", [])),
            "Raster field semantics must preserve the host ZjStream/JBIG to work/raster object chain consumed by video hardware.",
            evidence="analysis/open-firmware-model/raster-field-semantics.json",
        )
    )

    boundary = read_json("analysis/hardware-boundary/hardware-boundary.json")
    unsafe_functions = {
        item["function"]
        for item in boundary.get("function_boundaries", [])
        if item.get("must_avoid_in_custom_probe")
    }
    required_unsafe_tokens = [
        "0x10015214 hp1020_video_render_or_dma_candidate",
        "0x100140f8 hp1020_video_refresh_raw_bands_candidate",
        "0x10014910 hp1020_video_prepare_page_candidate",
        "0x10015c68 hp1020_engine_status_io_candidate",
        "0x10015df8 hp1020_engine_status_poll_candidate",
        "0x10016164 hp1020_engine_message_dispatch_candidate",
    ]
    checks.append(
        check(
            "hardware_boundary_keeps_engine_video_unsafe",
            all(token in unsafe_functions for token in required_unsafe_tokens),
            "The do-not-touch boundary for early custom firmware must still include video and engine paths.",
            evidence="analysis/hardware-boundary/hardware-boundary.json",
        )
    )

    first_page = read_json("analysis/hardware-boundary/first-page-hardware-sequence.json")
    register_semantics = read_json("analysis/hardware-boundary/video-engine-register-semantics.json")
    sequence_by_step = {
        item.get("step"): item
        for item in first_page.get("sequence", [])
        if isinstance(item, dict)
    }
    checks.append(
        check(
            "first_page_sequence_keeps_video_engine_registers_ordered",
            first_page.get("source_case") == "a4_default"
            and first_page.get("source_reports", {}).get("engine_topology")
            == "analysis/hardware-boundary/engine-print-topology.json"
            and first_page.get("source_reports", {}).get("video_prepare_projection")
            == "analysis/hardware-boundary/video-prepare-projection.json"
            and first_page.get("source_reports", {}).get("video_refill_topology")
            == "analysis/hardware-boundary/video-refill-topology.json"
            and sequence_by_step.get(2, {}).get("risk") == "high"
            and sequence_by_step.get(5, {}).get("projected_state", {}).get("stride_plus_0xb8") == 1200
            and sequence_by_step.get(5, {}).get("projected_state", {}).get("state_plus_0xbc") == 1200
            and sequence_by_step.get(5, {}).get("projected_state", {}).get("state_plus_0xc8_state_200") == 2
            and sequence_by_step.get(6, {}).get("projected_registers", {}).get("0xb2000008", {}).get("value") == 9600
            and "0x10014244 -> 0x10013f34" in sequence_by_step.get(7, {}).get("function", "")
            and "0xb2080004"
            in sequence_by_step.get(7, {}).get("projected_registers", {}).get("normal_refill_unsafe_registers", {}).get("value", "")
            and "+0xdc"
            in sequence_by_step.get(7, {}).get("projected_registers", {}).get("normal_refill_state_fields", {}).get("value", "")
            and len(first_page.get("remaining_unknowns", [])) >= 4,
            "The first-page hardware sequence must preserve the ordered engine/video/refill risk boundary.",
            evidence="analysis/hardware-boundary/first-page-hardware-sequence.json",
        )
    )
    video_dataflow = read_json("analysis/hardware-boundary/video-dataflow-contract.json")
    dataflow_stages = {
        item.get("stage"): item
        for item in video_dataflow.get("contract_stages", [])
        if isinstance(item, dict)
    }
    checks.append(
        check(
            "video_dataflow_contract_keeps_a4_default_path",
            video_dataflow.get("status") == "pass"
            and video_dataflow.get("source_case") == "a4_default"
            and dataflow_stages.get("host_raster_fields", {}).get("known_values", {}).get("work +0x84") == 9600
            and dataflow_stages.get("host_raster_fields", {}).get("known_values", {}).get("payload +0x48") == 6364
            and dataflow_stages.get("video_prepare_geometry", {}).get("known_values", {}).get("video state +0xb8 stride") == 1200
            and dataflow_stages.get("render_initial_transfer", {}).get("known_values", {}).get("0xb2040008") == 6364
            and dataflow_stages.get("helper_channel_b_refill", {}).get("known_values", {}).get("video state +0xcc max chunk units") == 4
            and dataflow_stages.get("helper_channel_b_refill", {}).get("known_values", {}).get("video state +0xd0") == 6824
            and dataflow_stages.get("helper_channel_b_refill", {}).get("remaining_unknown")
            == "live counter decrement/completion behavior; the VIDEO_Y source is statically proven"
            and dataflow_stages.get("helper_channel_b_refill", {}).get("known_values", {}).get("0xb2080008 first refill") == 4800
            and "min(4, +0xd0) * stride(1200)"
            == dataflow_stages.get("helper_channel_b_refill", {}).get("known_values", {}).get("0xb2080008")
            and "A pointer plus dual-output window(1200) when dual-block mode is active"
            == dataflow_stages.get("raw_band_queue_feed", {}).get("known_values", {}).get("0xb1000108")
            and all(item.get("status") == "present" for item in video_dataflow.get("checks", [])),
            "The video dataflow contract must preserve concrete a4_default values through render/refill boundary formulas.",
            evidence="analysis/hardware-boundary/video-dataflow-contract.json",
        )
    )
    direct_work = read_json("analysis/hardware-boundary/zjs-direct-work.json")
    semantic_core = read_json("analysis/open-firmware-model/semantic-core/validation.json")
    checks.append(check("direct_start_page_and_native_semantics_verified",
                        direct_work["status"] == "pass" and len(direct_work["checks"]) == 43
                        and all(c["status"] == "present" for c in direct_work["checks"])
                        and semantic_core["status"] == "pass" and semantic_core["total_cases"] >= 509
                        and semantic_core["sideband_source_known"] is True
                        and set(semantic_core["sanitizers"]) == {"address", "undefined"},
                        "Direct stock ELF work creation and native semantic parser must both pass.",
                        evidence="analysis/hardware-boundary/zjs-direct-work.json"))
    target_c = read_json("analysis/open-firmware-model/semantic-target/validation.json")
    checks.append(check("compiled_semantic_target_verified",
                        target_c["status"] == "pass" and target_c["total_cases"] == 78
                        and target_c["negative_control_payload_cases"] == 12
                        and read_json("analysis/open-firmware-model/semantic-target/reproducibility.json")["status"] == "pass"
                        and target_c["executed_instructions"] > 19000000
                        and target_c["negative_memory_checks"] == 4
                        and read_json("analysis/toolchain-probe/c-compiler-profile.json")["status"] == "pass"
                        and not {"quou","quos","loop","loopnez","entry","retw","retw.n","cust0","minu","maxu","min","max","sext","abs","mul16u","mul16s"}.intersection(target_c["executed_opcodes"]),
                        "Actual BE/call0 parser and planner must agree with native and independent model expectations in RAM-only execution.",
                        evidence="analysis/open-firmware-model/semantic-target/validation.json"))
    original = read_json("analysis/open-firmware-model/stock-execution/validation.json")
    checks.append(check("original_parser_differential_execution",
                        original["status"] == "pass" and original["totals"]["parser_agreement"] == 59
                        and sum(original["totals"].values()) == 9841
                        and all(c["status"] == "pass" for c in original["checks"])
                        and any(c["name"] == "be_bit_branch_regression" for c in original["checks"]),
                        "Original parser and libc bytes must agree with independent oracles, with environment substitutes explicit.",
                        evidence="analysis/open-firmware-model/stock-execution/validation.json"))
    qemu = read_json("analysis/open-firmware-model/semantic-target/qemu.json")
    checks.append(check("independent_qemu_execution",
                        qemu["status"] == "pass" and qemu["target_cases"] == target_c["total_cases"]
                        and qemu["libc_cases"] == {k: original["totals"][k] for k in ("memset","memcpy","memmove","strlen")}
                        and qemu["arithmetic_cases"] == {k:768 for k in ("signed_divide","signed_remainder","unsigned_divide","unsigned_remainder")}
                        and len(qemu["parser_cases"]) == original["totals"]["parser_agreement"]
                        and len(qemu["lifecycle_cases"]) == 12 and qemu["lifecycle_counterexample"]["status"] == "reproduced"
                        and qemu["windows"]["total_cases"] == 90 and all(qemu["windows"]["vector_entries"].values())
                        and qemu["windows"]["mutation"]["status"] == "detected"
                        and qemu["notification_receiver_word_indices"] == {"46":[2,3],"47":[3]}
                        and qemu["elf_sha256"] == target_c["elf_sha256"]
                        and all(hashlib.sha256((ROOT_DIR/"scripts"/p).read_bytes()).hexdigest() == h for p,h in qemu["source_sha256"].items()),
                        "Independent QEMU must agree on target C, original parser/lifecycle, arithmetic and six window handlers; source provenance must be current.",
                        evidence="analysis/open-firmware-model/semantic-target/qemu.json"))
    admission = read_json("analysis/open-firmware-model/stock-execution/admission.json")
    checks.append(check("original_stream_admission_execution",
                        admission["status"] == "pass" and admission["total_cases"] == 79
                        and admission["reproduced_counterexamples"] == 8
                        and all(c["status"] == "pass" for c in admission["cases"])
                        and all(len(c["parser_entries"]) == 2 and c["pc"] == "0x1000e7dd" for c in admission["counterexamples"])
                        and all(hashlib.sha256((ROOT_DIR/"scripts"/p).read_bytes()).hexdigest() == h for p,h in admission["source_sha256"].items()),
                        "Original language recognition and buffering must preserve normal admission and reproduce the conditional delayed-empty-document witness.",
                        evidence="analysis/open-firmware-model/stock-execution/admission.json"))
    original_status = read_json("analysis/hardware-boundary/stock-status-execution.json")
    checks.append(check("original_status_differential_execution",
                        original_status["status"] == "pass" and original_status["cases"] >= 133941
                        and not original_status["counterexamples"]
                        and original_status["all_instructions_covered"] and original_status["all_branch_outcomes_covered"],
                        "Original status decision instructions must agree with the model; I/O and command intent boundaries remain intercepted.",
                        evidence="analysis/hardware-boundary/stock-status-execution.json"))
    page_plan = read_json("analysis/open-firmware-model/page-plan.json")
    checks.append(check("portable_page_plan_boundary",
                        page_plan["status"] == "pass" and page_plan["total_cases"] == 1398
                        and page_plan["bands_checked"] > 5000000
                        and page_plan["generated_cases"]["a4_default"]["bands"] == 1706
                        and page_plan["generated_cases"]["a4_2400x600"]["result"] == 2
                        and page_plan["generated_cases"]["a4_logical_clip"]["result"] == 1,
                        "Native page planning must retain corrected window arithmetic and reject unsupported/mismatched fixtures.",
                        evidence="analysis/open-firmware-model/page-plan.json"))
    metadata = read_json("analysis/open-firmware-model/metadata-bounds.json")
    checks.append(check("stock_metadata_split_boundary_explicit",
                        metadata["status"] == "pass" and metadata["bounded_cases"] == 10 and metadata["invalid_cases"] == 1
                        and [c["case"] for c in metadata["cases"] if c["status"] == "invalid"] == ["matrix-a4_logical_clip"],
                        "The logical-clip full-payload model must not be mistaken for bounded stock metadata handling.",
                        evidence="analysis/open-firmware-model/metadata-bounds.json"))
    callbacks = read_json("analysis/hardware-boundary/raster-callbacks.json")
    bypass = read_json("analysis/hardware-boundary/raster-bypass.json")
    callback_scenario = dict(datastore_32=0,work_plus_0x36=0,lane_selector=0,secondary_output=False)
    page_config_cases = [c for name in ("pages","page-fragments")
                         for c in read_json(f"analysis/open-firmware-model/stock-execution/{name}.json")["cases"]]
    checks.append(check("stock_value_selects_bounded_raster_bypass",
                        bypass["status"] == "pass" and bypass["stock_entry"]["value"] == 1
                        and bypass["total_cases"] == 42 and bypass["raw_buffer_selections"] == 34
                        and bypass["custom_call_boundary_stops"] == 8
                        and bypass["custom_callbacks_executed"] == bypass["completed_lifecycles"] == 0
                        and len(bypass["relocation_cases"]) == 2
                        and all(c["entry_32_unchanged"] and c["changed_entries"] == list(range(23))
                                for c in bypass["relocation_cases"])
                        and all(c["band"]["outcome"] == "raw_buffer_selected"
                                for c in bypass["cases"] if c["config_source"] == "file_backed_stock")
                        and all(c["raw_and_output_buffers_unchanged"] and len(c["rejected_pc_controls"]) == 4
                                for c in bypass["cases"])
                        and all(hashlib.sha256((ROOT_DIR/"scripts"/name).read_bytes()).hexdigest() == digest
                                for name,digest in bypass["source_sha256"].items())
                        and len(page_config_cases) == 36
                        and all(c["stock_raster_config"] == dict(index=32,value_before=1,value_after=1,
                                                               descriptor_unchanged=True,boot_proven=False)
                                for c in page_config_cases)
                        and video_dataflow["assumed_runtime_config"] == first_page["assumed_runtime_config"] == callback_scenario
                        and callbacks["stock_datastore_32"]["file_value"] == 1
                        and callbacks["stock_datastore_32"]["live_value_proven"] is False,
                        "The file-backed bypass, excluded callback boundaries and conditional model configuration must remain distinct from boot, page lifecycles and physical printing.",
                        evidence="analysis/hardware-boundary/raster-bypass.json"))
    checks.append(check("raster_callback_argument_and_unknown_isa_boundary",
                        callbacks["status"] == "pass" and callbacks["call_contract"]["argument_count"] == 4
                        and [len(f["unknown_instructions"]) for f in callbacks["functions"]] == [16,40,84],
                        "Stock raster callbacks must preserve fourth stride argument and explicit unresolved ISA effects.",
                        evidence="analysis/hardware-boundary/raster-callbacks.json"))
    for variant in ("minimal-idle","usb-register-snapshot","usb-marker-draft","usb-bulk-parser-draft"):
        gate = read_json(f"analysis/open-firmware-probes/{variant}/instruction-gate.json")
        checks.append(check(f"{variant}_reachable_instructions_defined",
                            gate["status"] == "pass" and gate["unknown_instructions"] == 0
                            and len(gate["roots"]) == 7 and len(gate["rejected_mutations"]) == 5,
                            "Inert probes may execute only defined allowed instructions and proven constant trampolines.",
                            evidence=f"analysis/open-firmware-probes/{variant}/instruction-gate.json"))
    queue_payload_chain = read_json("analysis/hardware-boundary/video-queue-payload-chain.json")
    queue_chain_checks = {
        item.get("name"): item
        for item in queue_payload_chain.get("checks", [])
        if isinstance(item, dict)
    }
    checks.append(
        check(
            "video_queue_payload_chain_identifies_prepare_work_object",
            queue_payload_chain.get("status") == "pass"
            and queue_payload_chain.get("conclusion", {}).get("prepare_argument_identity")
            == "0x94-byte video/page work object"
            and "direct START_PAGE builder writes VIDEO_Y to active work +0x26"
            in queue_payload_chain.get("conclusion", {}).get("effect_on_remaining_units", "")
            and len(queue_payload_chain.get("stages", [])) == 10
            and queue_chain_checks.get("pending_node_payload_is_direct_param_2", {}).get("status") == "present"
            and queue_chain_checks.get("list_helpers_do_not_rewrite_payload_word", {}).get("status") == "present"
            and queue_chain_checks.get("printmgr_moves_same_node_pending_to_active", {}).get("status") == "present"
            and queue_chain_checks.get("video_thread_uses_payload_as_prepare_argument", {}).get("status") == "present"
            and queue_chain_checks.get("work_populate_does_not_copy_page_param_0x26", {}).get("status") == "present"
            and all(item.get("status") == "present" for item in queue_payload_chain.get("checks", [])),
            "The video queue payload chain must preserve that prepare receives the 0x94 work object, with VIDEO_Y written directly into work +0x26.",
            evidence="analysis/hardware-boundary/video-queue-payload-chain.json",
        )
    )
    prepare_fields = read_json("analysis/hardware-boundary/video-prepare-argument-fields.json")
    prepare_field_rows = {
        item.get("field"): item
        for item in prepare_fields.get("fields", [])
        if isinstance(item, dict)
    }
    checks.append(
        check(
            "video_prepare_argument_fields_resolve_direct_sources",
            prepare_fields.get("status") == "pass"
            and prepare_fields.get("prepare_argument_identity") == "0x94-byte video/page work object"
            and prepare_field_rows.get("+0x84/+0x88/+0x8c/+0x90", {}).get("source_status") == "sourced"
            and prepare_field_rows.get("+0x26", {}).get("source_status") == "sourced"
            and prepare_field_rows.get("+0x30", {}).get("source_status") == "sourced"
            and prepare_field_rows.get("+0x32", {}).get("source_status") == "sourced"
            and prepare_field_rows.get("+0x74", {}).get("source_status") == "default_zero_for_current_path"
            and prepare_fields.get("field_status_counts", {}).get("unsourced_active_work", 0) == 0
            and all(item.get("status") == "present" for item in prepare_fields.get("checks", [])),
            "The prepare argument field model must keep render geometry sourced with +0x26/+0x30/+0x32 sourced directly on active work.",
            evidence="analysis/hardware-boundary/video-prepare-argument-fields.json",
        )
    )
    sideband_census = read_json("analysis/hardware-boundary/video-sideband-write-census.json")
    census_checks = {
        item.get("name"): item
        for item in sideband_census.get("checks", [])
        if isinstance(item, dict)
    }
    census_roles = sideband_census.get("role_counts", {})
    overlap_roles = sideband_census.get("overlap_role_counts", {})
    checks.append(
        check(
            "video_sideband_write_census_rules_out_false_leads",
            sideband_census.get("status") == "pass"
            and sideband_census.get("corpus_summary", {}).get("files_scanned", 0) >= 600
            and census_roles.get("direct_work_writer") == 3
            and census_roles.get("active_work_consumer") == 4
            and census_roles.get("scaled_index_false_lead") == 1
            and census_roles.get("runtime_byte_to_work_0x90") == 2
            and len(sideband_census.get("active_work_writer_hits", [])) == 3
            and len(sideband_census.get("ghidra_sideband_overlap_store_scan", {}).get("hits", [])) == 103
            and overlap_roles.get("direct_work_exact_store") == 3
            and overlap_roles.get("video_state_ring_clear") == 1
            and census_checks.get("child_record_0x13_is_not_work_0x26", {}).get("status") == "present"
            and census_checks.get("runtime_byte_0x13_feeds_work_0x90_not_sideband", {}).get("status") == "present"
            and census_checks.get("ghidra_overlap_scan_finds_no_work_populate_or_jobmgr_sideband_writer", {}).get("status")
            == "present"
            and census_checks.get("direct_active_work_writers_found", {}).get("status") == "present"
            and all(item.get("status") == "present" for item in sideband_census.get("checks", [])),
            "The sideband write census must preserve that selected +0x26/+0x30/+0x32 hits and overlap hits include three direct active work-object writers alongside consumers and false leads.",
            evidence="analysis/hardware-boundary/video-sideband-write-census.json",
        )
    )
    sideband_copy = read_json("analysis/hardware-boundary/video-sideband-copy-direction.json")
    checks.append(
        check(
            "video_sideband_copy_direction_rules_out_hidden_source",
            sideband_copy.get("status") == "pass"
            and sideband_copy.get("helper", {}).get("argument_order") == "destination, source, length"
            and sideband_copy.get("sideband_call", {}).get("interpreted_as")
            == "memcpy(dst=PTR_DAT_10006304 runtime block, src=iStack_84 BIH payload, len=0x14)"
            and set(sideband_copy.get("effect_on_prepare_fields", {}).get("still_unsourced", []))
            == set()
            and all(item.get("status") == "present" for item in sideband_copy.get("checks", [])),
            "The sideband copy-direction model must preserve that case 0x29 copies BIH payload out to runtime block, not into work +0x26/+0x30/+0x32.",
            evidence="analysis/hardware-boundary/video-sideband-copy-direction.json",
        )
    )
    sideband_impact = read_json("analysis/hardware-boundary/video-sideband-default-impact.json")
    sideband_impacts = {
        item.get("work_field"): item
        for item in sideband_impact.get("field_impacts", [])
        if isinstance(item, dict)
    }
    sideband_access_hits = sideband_impact.get("ghidra_video_state_access_scan", {}).get("hits", [])
    sideband_access_roles = {item.get("role") for item in sideband_access_hits if isinstance(item, dict)}
    e8_access_hits = [
        item
        for item in sideband_access_hits
        if isinstance(item, dict) and item.get("offset") == "0xe8"
    ]
    checks.append(
        check(
            "video_sideband_default_impact_keeps_0x26_critical",
            sideband_impact.get("status") == "pass"
            and sideband_impacts.get("+0x26", {}).get("risk") == "critical"
            and sideband_impacts.get("+0x32", {}).get("risk") == "mode_critical"
            and sideband_impacts.get("+0x30", {}).get("risk") == "unknown_low_in_current_static_view"
            and len(sideband_access_hits) == 19
            and {"channel_b_refill_counter", "descriptor_final_accounting", "descriptor_b_flag", "raw_refresh_b_flag", "stack_local_false_positive"}.issubset(
                sideband_access_roles
            )
            and len(e8_access_hits) == 1
            and e8_access_hits[0].get("role") == "prepare_seed"
            and all(item.get("status") == "present" for item in sideband_impact.get("checks", [])),
            "The sideband default-impact model must keep +0x26 as print-path critical, +0x32 mode-critical, +0x30 lower priority, and classify the exact-offset Ghidra access scan.",
            evidence="analysis/hardware-boundary/video-sideband-default-impact.json",
        )
    )
    zero_sideband = read_json("analysis/hardware-boundary/video-zero-sideband-scenario.json")
    zero_steps = {
        item.get("step"): item
        for item in zero_sideband.get("scenario", [])
        if isinstance(item, dict)
    }
    checks.append(
        check(
            "video_zero_sideband_scenario_keeps_refill_blocker_narrow",
            zero_sideband.get("status") == "pass"
            and "initial_channel_a_still_arms" in zero_steps
            and "channel_b_refill_skipped" in zero_steps
            and "raw_band_final_logic_becomes_ambiguous" in zero_steps
            and any(
                "not an immediate proof that render setup cannot start" in item
                for item in zero_sideband.get("practical_conclusion", [])
            )
            and any(
                "channel B is not seeded" in item
                for item in zero_sideband.get("practical_conclusion", [])
            )
            and all(item.get("status") == "present" for item in zero_sideband.get("checks", [])),
            "The zero-sideband scenario must keep the refined conclusion: initial channel A can arm, but channel-B refill/descriptor state is not seeded.",
            evidence="analysis/hardware-boundary/video-zero-sideband-scenario.json",
        )
    )
    remaining_units = read_json("analysis/hardware-boundary/video-remaining-units.json")
    remaining_cases = {
        item.get("case"): item
        for item in remaining_units.get("case_matrix", [])
        if isinstance(item, dict)
    }
    copy_gap = {
        item.get("stage"): item
        for item in remaining_units.get("source_chain", [])
        if isinstance(item, dict)
    }
    checks.append(
        check(
            "video_remaining_units_direct_source_verified",
            remaining_units.get("status") == "pass"
            and copy_gap.get("direct_builder", {}).get("status") == "ELF-byte verified"
            and remaining_cases.get("a4_default", {}).get("video_y_from_zji_0x12") == 6824
            and remaining_cases.get("a4_default", {}).get("first_channel_b_length") == 4800
            and remaining_cases.get("letter_default", {}).get("video_y_from_zji_0x12") == 6408
            and remaining_cases.get("legal_default", {}).get("video_y_from_zji_0x12") == 8208
            and all(item.get("status") == "present" for item in remaining_units.get("checks", [])),
            "Video remaining-unit model must preserve the direct VIDEO_Y-to-work-to-counter chain.",
            evidence="analysis/hardware-boundary/video-remaining-units.json",
        )
    )
    chunk_sizing = read_json("analysis/hardware-boundary/video-chunk-sizing.json")
    chunk_cases = {
        item.get("case"): item
        for item in chunk_sizing.get("case_matrix", [])
        if isinstance(item, dict)
    }
    checks.append(
        check(
            "video_chunk_sizing_projects_stride_and_cc",
            chunk_sizing.get("status") == "pass"
            and chunk_sizing.get("helper_contract", {}).get("verified_behavior")
            == "for denominator >= 2, returns floor(numerator / denominator)"
            and chunk_sizing.get("constants", {}).get("chunk_budget_bytes_DAT_10005dc8") == 8192
            and chunk_cases.get("a4_default", {}).get("stride_plus_0xb8") == 1200
            and chunk_cases.get("a4_default", {}).get("max_chunk_units_plus_0xcc") == 4
            and chunk_cases.get("a4_600x600", {}).get("stride_plus_0xb8") == 608
            and chunk_cases.get("a4_600x600", {}).get("max_chunk_units_plus_0xcc") == 12
            and all(item.get("status") == "present" for item in chunk_sizing.get("checks", [])),
            "Video chunk sizing must preserve the stride-derived +0xcc projection and helper caveat.",
            evidence="analysis/hardware-boundary/video-chunk-sizing.json",
        )
    )
    helper_disassembly = read_json("analysis/hardware-boundary/video-helper-disassembly.json")
    checks.append(
        check(
            "video_helper_unsigned_division_instruction_verified",
            helper_disassembly.get("status") == "pass"
            and helper_disassembly.get("helper", {}).get("working_name") == "unsigned_divide"
            and helper_disassembly.get("conclusion", {}).get("status") == "instruction_verified"
            and helper_disassembly.get("validation", {}).get("executions", 0) >= 131072
            and all(item.get("status") == "present" for item in helper_disassembly.get("checks", [])),
            "Unsigned floor division must be verified against complete ELF-matched helper instructions, including loop execution.",
            evidence="analysis/hardware-boundary/video-helper-disassembly.json",
        )
    )
    semantic_sequences = {
        item.get("name"): item
        for item in register_semantics.get("semantic_sequences", [])
        if isinstance(item, dict)
    }
    semantic_registers = {
        item.get("register")
        for item in register_semantics.get("mmio_literals", [])
        if isinstance(item, dict)
    }
    semantic_registers.update(
        item.get("register")
        for item in register_semantics.get("manual_literal_cells", {}).values()
        if isinstance(item, dict) and item.get("register")
    )
    checks.append(
        check(
            "video_engine_register_semantics_resolved",
            register_semantics.get("status") == "pass"
            and {"0xb050000c", "0xb0500004", "0xb1000008", "0xb100010c", "0xb2000000", "0xb2040000", "0xb2080000"}.issubset(
                semantic_registers
            )
            and "engine_command_status_handshake" in semantic_sequences
            and "raw_band_feed" in semantic_sequences
            and all(check.get("status") == "present" for check in register_semantics.get("checks", [])),
            "The video/engine register-semantics report must keep the key engine, video, channel, and raw-band roles resolved.",
            evidence="analysis/hardware-boundary/video-engine-register-semantics.json",
        )
    )
    video_prepare_modes = read_json("analysis/hardware-boundary/video-prepare-modes.json")
    prepare_tables = {
        item.get("name"): item
        for item in video_prepare_modes.get("table_blocks", [])
        if isinstance(item, dict)
    }
    prepare_literal_values = video_prepare_modes.get("literal_values", {})
    checks.append(
        check(
            "video_prepare_modes_keep_timing_tables",
            video_prepare_modes.get("status") == "pass"
            and prepare_literal_values.get("setup_a_timing") == "0xb1000020"
            and prepare_literal_values.get("timing_table_0") == "0xb1000400"
            and len(video_prepare_modes.get("timing_modes", [])) == 8
            and len(prepare_tables.get("single_plane_1200_table", {}).get("words", [])) == 16
            and all(check.get("status") == "present" for check in video_prepare_modes.get("checks", [])),
            "The video-prepare mode model must preserve the branch-dependent 0xb100 timing/setup table evidence.",
            evidence="analysis/hardware-boundary/video-prepare-modes.json",
        )
    )
    engine_command_status = read_json("analysis/hardware-boundary/engine-command-status.json")
    engine_literals = engine_command_status.get("literal_values", {})
    engine_calls = {
        item.get("value"): item
        for item in engine_command_status.get("status_io_calls", [])
        if isinstance(item, dict)
    }
    engine_events = {
        item.get("event")
        for item in engine_command_status.get("event_decisions", [])
        if isinstance(item, dict)
    }
    engine_sequences = {
        item.get("name")
        for item in engine_command_status.get("command_sequences", [])
        if isinstance(item, dict)
    }
    checks.append(
        check(
            "engine_command_status_model_resolved",
            engine_command_status.get("status") == "pass"
            and engine_literals.get("engine_status_register") == "0xb050000c"
            and engine_literals.get("engine_command_register") == "0xb0500004"
            and engine_literals.get("engine_state_base") == "0x1002f0c4"
            and {
                "0x1",
                "0x20",
                "0x2",
                "0x16",
                "0x13",
                "0x0000501a",
                "0x00005043",
                "0x00003a13",
                "0x00006012",
            }.issubset(engine_calls)
            and {
                "0xe6100a01",
                "0xfe001401",
                "0x14000a04",
                "0xf6000300",
                "0xe6000d03",
            }.issubset(engine_events)
            and {
                "engine_status_io_handshake",
                "preflight_start",
                "print_dispatch_start_commands",
                "poll_transition_side_effects",
            }.issubset(engine_sequences)
            and all(check.get("status") == "present" for check in engine_command_status.get("checks", [])),
            "The engine command/status model must preserve the stock 0xb050 register pair, command IDs, state fields, and event branches.",
            evidence="analysis/hardware-boundary/engine-command-status.json",
        )
    )
    engine_decisions = read_json("analysis/hardware-boundary/engine-status-decisions.json")
    decision_scenarios = {
        item.get("name"): item
        for item in engine_decisions.get("scenarios", [])
        if isinstance(item, dict)
    }
    checks.append(
        check(
            "engine_status_decision_model_resolved",
            engine_decisions.get("status") == "pass"
            and engine_decisions.get("scenario_count") == 21
            and engine_decisions.get("scenario_failures") == 0
            and decision_scenarios.get("ready_rewrite", {}).get("result", {}).get("stored_event") == "0x14000a04"
            and decision_scenarios.get("substatus_0x16_ready_0x40_with_status_2_0x4040", {})
            .get("result", {})
            .get("side_effect_commands")
            == ["0x0000501a"]
            and decision_scenarios.get("leave_e6100800_sends_0x5043", {}).get("result", {}).get("side_effect_commands")
            == ["0x00005043"]
            and decision_scenarios.get("previous_0x0100_to_ready_extra_emit", {}).get("result", {}).get(
                "extra_emitted_events"
            )
            == ["0xe6100a01"]
            and all(check.get("status") == "present" for check in engine_decisions.get("checks", [])),
            "The executable engine status decision model must preserve ready rewrite, 0x501a/0x5043 side effects, and previous-event extra emit behavior.",
            evidence="analysis/hardware-boundary/engine-status-decisions.json",
        )
    )
    engine_topology = read_json("analysis/hardware-boundary/engine-print-topology.json")
    engine_topology_stages = {
        item.get("name")
        for item in engine_topology.get("topology", [])
        if isinstance(item, dict)
    }
    engine_topology_commands = engine_topology.get("important_commands", {})
    checks.append(
        check(
            "engine_print_topology_model_resolved",
            engine_topology.get("status") == "pass"
            and engine_topology.get("registers", {}).get("engine_status") == "0xb050000c"
            and engine_topology.get("registers", {}).get("engine_command") == "0xb0500004"
            and {
                "engine_thread_startup",
                "page_work_acceptance",
                "status_poll_and_recovery",
                "completion_and_deferred_work",
            }.issubset(engine_topology_stages)
            and engine_topology_commands.get("page_start_normal") == "0x00006012"
            and engine_topology_commands.get("page_start_reset_latch") == "0x00003a13"
            and engine_topology_commands.get("substatus_side_effect") == "0x0000501a"
            and engine_topology_commands.get("leave_e6100800_side_effect") == "0x00005043"
            and all(check.get("status") == "present" for check in engine_topology.get("checks", [])),
            "The engine print topology must preserve startup/preflight, page acceptance, polling/recovery, completion/deferred-work stages, and key stock engine commands.",
            evidence="analysis/hardware-boundary/engine-print-topology.json",
        )
    )
    video_feedback = read_json("analysis/hardware-boundary/video-engine-feedback.json")
    video_literals = video_feedback.get("literal_values", {})
    feedback_sequences = {
        item.get("name"): item
        for item in video_feedback.get("feedback_sequences", [])
        if isinstance(item, dict)
    }
    feedback_messages = [
        message
        for sequence in video_feedback.get("feedback_sequences", [])
        if isinstance(sequence, dict)
        for message in sequence.get("messages", [])
        if isinstance(message, dict)
    ]
    feedback_message_pairs = {(item.get("message"), item.get("payload")) for item in feedback_messages}
    checks.append(
        check(
            "video_engine_feedback_model_resolved",
            video_feedback.get("status") == "pass"
            and {
                "normal_video_done",
                "video_reset_or_flush",
                "reset_dispatch_complete_active",
                "reset_dispatch_event_words",
            }.issubset(feedback_sequences)
            and ("0x10", "original video queue payload") in feedback_message_pairs
            and ("0x25", "no event word in word 1") in feedback_message_pairs
            and ("0x11", "completion/advance") in feedback_message_pairs
            and ("0x0b", "deferred video work when present") in feedback_message_pairs
            and {"0xe6e01201", "0xe6e01202", "0xeee01b01", "0xeee01b02", "0xeee01b04"}.issubset(
                set(video_literals.values())
            )
            and all(check.get("status") == "present" for check in video_feedback.get("checks", [])),
            "The video-to-engine feedback model must preserve normal completion, reset/flush, requeue, and video event-word behavior.",
            evidence="analysis/hardware-boundary/video-engine-feedback.json",
        )
    )
    video_ring = read_json("analysis/hardware-boundary/video-transfer-ring.json")
    ring_literals = video_ring.get("literal_values", {})
    ring_sequences = {
        item.get("name")
        for item in video_ring.get("ownership_sequences", [])
        if isinstance(item, dict)
    }
    ring_scenarios = {
        item.get("name"): item
        for item in video_ring.get("ring_scenarios", [])
        if isinstance(item, dict)
    }
    checks.append(
        check(
            "video_transfer_ring_model_resolved",
            video_ring.get("status") == "pass"
            and ring_literals.get("video_state_base") == "0x1002efc0"
            and ring_literals.get("ring_descriptor_base") == "0x1002efe0"
            and ring_literals.get("channel_a_pointer") == "0xb2040004"
            and ring_literals.get("channel_b_pointer") == "0xb2080004"
            and {
                "prepare_initializes_ring",
                "render_claims_next_slot",
                "render_starts_first_transfer",
                "band_helper_refills_channel_b",
                "irq_band_done_advances_or_refills",
            }.issubset(ring_sequences)
            and ring_scenarios.get("producer_0_consumer_1", {}).get("render_result") == "busy_error_0x1003"
            and ring_scenarios.get("producer_0_consumer_0", {}).get("producer_after") == 1
            and all(check.get("status") == "present" for check in video_ring.get("checks", [])),
            "The video transfer ring model must preserve producer/consumer collision behavior, channel A/B descriptors, and IRQ refill evidence.",
            evidence="analysis/hardware-boundary/video-transfer-ring.json",
        )
    )
    video_irq = read_json("analysis/hardware-boundary/video-irq-decisions.json")
    irq_scenarios = {
        item.get("name"): item
        for item in video_irq.get("scenarios", [])
        if isinstance(item, dict)
    }
    checks.append(
        check(
            "video_irq_decision_model_resolved",
            video_irq.get("status") == "pass"
            and video_irq.get("scenario_count") == 11
            and video_irq.get("scenario_failures") == 0
            and video_irq.get("branch_priority", [None])[0] == "0x20 band done/refill"
            and irq_scenarios.get("priority_0x20_over_0x02", {}).get("decision", {}).get("category") == "band_done"
            and irq_scenarios.get("bit_0x02_reset_case_0", {}).get("decision", {}).get("reset_dispatch_param") == 0
            and irq_scenarios.get("bit_0x08_reset_case_3", {}).get("decision", {}).get("reset_dispatch_param") == 3
            and irq_scenarios.get("bit_0x10_reset_case_4", {}).get("decision", {}).get("reset_dispatch_param") == 4
            and irq_scenarios.get("bit_0x01_dispatch_case_7_when_idle", {}).get("decision", {}).get(
                "reset_dispatch_param"
            )
            == 7
            and all(check.get("status") == "present" for check in video_irq.get("checks", [])),
            "The video IRQ decision model must preserve branch priority, refill, and reset-dispatch cases 0/3/4/7.",
            evidence="analysis/hardware-boundary/video-irq-decisions.json",
        )
    )
    video_band_queue = read_json("analysis/hardware-boundary/video-band-queue.json")
    band_literals = video_band_queue.get("literal_values", {})
    band_sequences = {
        item.get("name")
        for item in video_band_queue.get("queue_sequences", [])
        if isinstance(item, dict)
    }
    band_scenarios = {
        item.get("name"): item
        for item in video_band_queue.get("loop_scenarios", [])
        if isinstance(item, dict)
    }
    checks.append(
        check(
            "video_band_queue_model_resolved",
            video_band_queue.get("status") == "pass"
            and band_literals.get("video_state_base") == "0x1002efc0"
            and band_literals.get("ring_descriptor_base") == "0x1002efe0"
            and band_literals.get("raw_band_a_pointer") == "0xb1000008"
            and band_literals.get("raw_band_b_pointer") == "0xb1000108"
            and band_literals.get("raw_band_a_flags") == "0xb100000c"
            and band_literals.get("raw_band_b_flags") == "0xb100010c"
            and {
                "queue_loop_gate",
                "optional_callback_and_padding",
                "raw_band_single_block_write",
                "raw_band_dual_block_write",
                "advance_queue_side",
            }.issubset(band_sequences)
            and band_scenarios.get("dc_0_e0_1_final_0", {}).get("loop_decision") == "stop_before_e0_collision"
            and band_scenarios.get("dc_0_e0_1_final_1", {}).get("loop_decision") == "queue_descriptor"
            and all(check.get("status") == "present" for check in video_band_queue.get("checks", [])),
            "The video band queue model must preserve +0xdc/+0xe0 collision behavior and raw-band A/B register writes.",
            evidence="analysis/hardware-boundary/video-band-queue.json",
        )
    )
    video_mode_flag = read_json("analysis/hardware-boundary/video-mode-flag.json")
    mode_literals = video_mode_flag.get("literal_values", {})
    mode_sequences = {
        item.get("name")
        for item in video_mode_flag.get("branch_sequences", [])
        if isinstance(item, dict)
    }
    mode_cases = {
        item.get("mode"): item
        for item in video_mode_flag.get("mode_cases", [])
        if isinstance(item, dict)
    }
    checks.append(
        check(
            "video_mode_flag_model_resolved",
            video_mode_flag.get("status") == "pass"
            and mode_literals.get("high_bit") == "0x80000000"
            and mode_literals.get("high_bit_clear_mask") == "0x7fffffff"
            and mode_literals.get("video_state_base") == "0x1002efc0"
            and mode_literals.get("work_object_mode_flag_offset") == "+0x74"
            and mode_literals.get("video_state_mode_flag_offset") == "+0xfc"
            and {
                "prepare_copies_work_flag_to_state_sign",
                "irq_band_done_selects_refill_family",
                "reset_dispatch_depends_on_same_sign_bit",
            }.issubset(mode_sequences)
            and mode_cases.get("descriptor_queue_mode", {}).get("work_object_plus_0x74") == 0
            and mode_cases.get("descriptor_queue_mode", {}).get("state_plus_0xfc_is_negative") is False
            and mode_cases.get("raw_linked_list_mode", {}).get("work_object_plus_0x74") == 1
            and mode_cases.get("raw_linked_list_mode", {}).get("state_plus_0xfc_is_negative") is True
            and all(check.get("status") == "present" for check in video_mode_flag.get("checks", [])),
            "The video mode-flag model must preserve the work +0x74 to state +0xfc sign-bit fork between descriptor queue and raw linked-list refill.",
            evidence="analysis/hardware-boundary/video-mode-flag.json",
        )
    )
    video_refill_topology = read_json("analysis/hardware-boundary/video-refill-topology.json")
    refill_paths = {
        item.get("name"): item
        for item in video_refill_topology.get("topology", [])
        if isinstance(item, dict)
    }
    refill_checks = video_refill_topology.get("checks", [])
    checks.append(
        check(
            "video_refill_topology_model_resolved",
            video_refill_topology.get("status") == "pass"
            and {
                "analysis/hardware-boundary/video-mode-flag.json",
                "analysis/hardware-boundary/video-irq-decisions.json",
                "analysis/hardware-boundary/video-transfer-ring.json",
                "analysis/hardware-boundary/video-band-queue.json",
            }.issubset(set(video_refill_topology.get("source_reports", [])))
            and "normal_descriptor_queue_refill" in refill_paths
            and "alternate_raw_linked_list_refill" in refill_paths
            and "+0xd8" in refill_paths.get("normal_descriptor_queue_refill", {}).get("state_fields", [])
            and "+0xdc" in refill_paths.get("normal_descriptor_queue_refill", {}).get("state_fields", [])
            and "0xb2080004" in refill_paths.get("normal_descriptor_queue_refill", {}).get("unsafe_registers", [])
            and "+0xa0" in refill_paths.get("alternate_raw_linked_list_refill", {}).get("state_fields", [])
            and all(check.get("status") == "present" for check in refill_checks),
            "The video refill topology must preserve the normal descriptor-queue path and the alternate raw linked-list path as separate unsafe video refills.",
            evidence="analysis/hardware-boundary/video-refill-topology.json",
        )
    )
    video_prepare_projection = read_json("analysis/hardware-boundary/video-prepare-projection.json")
    prepare_projection_rows = video_prepare_projection.get("projections", [])
    callback_states = []
    for projection in prepare_projection_rows:
        for scenario in projection.get("scenarios", []):
            if (
                scenario.get("datastore_0x20_zero") is True
                and scenario.get("lane_selector") == 0
                and scenario.get("secondary_output_state_plus_0xec_nonzero") is False
            ):
                callback_states.append(scenario.get("derived_state", {}))
    checks.append(
        check(
            "video_prepare_projection_narrows_generated_variants",
            video_prepare_projection.get("status") == "pass"
            and video_prepare_projection.get("projection_count") == 10
            and video_prepare_projection.get("scenario_count") == 80
            and all(projection.get("resolution") == "600x600" for projection in prepare_projection_rows)
            and all(state.get("nbie") == 1 for state in callback_states)
            and {state.get("video_bpp") for state in callback_states} == {1, 2, 4}
            and all(state.get("state_plus_0xc8_state_200") == (2 if state["video_bpp"] == 1 else state["video_bpp"]) for state in callback_states)
            and all(state.get("state_plus_0xf4") == (2 if state["video_bpp"] in (1, 2) else 0) for state in callback_states)
            and all(state.get("state_plus_0xbc") == state.get("stride_plus_0xb8") * (2 if state["video_bpp"] == 1 else 1) for state in callback_states)
            and all(check.get("status") == "present" for check in video_prepare_projection.get("checks", [])),
            "The video prepare projection must keep the generated host variants at 600dpi with distinct BPP1/2/4 setup branches, sourced independently of NBIE.",
            evidence="analysis/hardware-boundary/video-prepare-projection.json",
        )
    )
    checks.append(
        check(
            "usb_family_remains_only_low_risk_target",
            any(
                item.get("family") == "0xb300...." and item.get("risk") == "lower"
                for item in boundary.get("register_families", [])
            ),
            "USB 0xb300 must remain the only plausible early open-firmware hardware target.",
            evidence="analysis/hardware-boundary/hardware-boundary.json",
        )
    )

    pjl_contract = read_json("analysis/non-printing-status-probe/pjl-status-contract.json")
    queries = {query["name"]: query for query in pjl_contract.get("queries", [])}
    checks.append(
        check(
            "pjl_first_query_is_echo",
            pjl_contract.get("first_recommended_query") == "echo"
            and queries.get("echo", {}).get("payload_bytes") == 49
            and queries.get("echo", {}).get("stock_response_markers") == ["HP1020_STATUS_PROBE"],
            "The first stock/open comparison must remain the non-printing PJL ECHO probe.",
            evidence="analysis/non-printing-status-probe/pjl-status-contract.json",
        )
    )
    checks.append(
        check(
            "pjl_contract_is_non_printing",
            {"no PDF", "no PostScript", "no ZjStream raster", "no engine/video command from host", "no paper required"}.issubset(
                set(pjl_contract.get("safety_scope", []))
            ),
            "The status query contract must stay outside print/video/engine execution.",
            evidence="analysis/non-printing-status-probe/pjl-status-contract.json",
        )
    )

    marker_descriptor = read_json("analysis/open-firmware-probes/usb-marker-draft/marker-descriptor-check.json")
    marker_len = read_json("analysis/open-firmware-probes/usb-marker-draft/marker-length-flow-check.json")
    marker_rearm = read_json("analysis/open-firmware-probes/usb-marker-draft/marker-rearm-flow-check.json")
    marker_sequence = read_json("analysis/open-firmware-probes/usb-marker-draft/endpoint0-sequence-scan.json")
    marker_contract = read_json("analysis/open-firmware-probes/usb-marker-draft/usb-contract-scan.json")
    marker_behavior = read_json("analysis/open-firmware-probes/usb-marker-draft/behavior-model.json")
    marker_memory = read_json("analysis/open-firmware-probes/usb-marker-draft/memory-boundary-scan.json")
    checks.append(
        check(
            "usb_marker_descriptor_is_stable",
            marker_descriptor.get("descriptor_text") == "HP1020 OPEN MARKER"
            and marker_descriptor.get("section", {}).get("size") == 38
            and severity_count(marker_descriptor.get("checks", []), "fail") == 0,
            "The open marker descriptor bytes and length must remain fixed.",
            evidence="analysis/open-firmware-probes/usb-marker-draft/marker-descriptor-check.json",
        )
    )
    checks.append(
        check(
            "usb_marker_length_flow_passes",
            severity_count(marker_len, "fail") == 0
            and len(marker_len) == 6
            and any(item.get("name") == "descriptor_word_uses_clipped_length" for item in marker_len)
            and any(item.get("name") == "selected_descriptor_length_preserved" for item in marker_len),
            "The marker draft must keep host wLength clipping connected to the selected descriptor length, endpoint-0 response state, and descriptor word.",
            evidence="analysis/open-firmware-probes/usb-marker-draft/marker-length-flow-check.json",
        )
    )
    checks.append(
        check(
            "usb_marker_rearm_flow_passes",
            severity_count(marker_rearm, "fail") == 0
            and len(marker_rearm) == 5
            and any(item.get("name") == "rearm_returns_to_poll_loop" for item in marker_rearm),
            "The marker draft must wait for USB setup gates to clear and then return to polling after one response.",
            evidence="analysis/open-firmware-probes/usb-marker-draft/marker-rearm-flow-check.json",
        )
    )
    checks.append(
        check(
            "usb_marker_sequence_matches_endpoint0_contract",
            severity_count(marker_sequence, "fail") == 0
            and len([item for item in marker_sequence if item.get("kind") == "endpoint0_sequence_write"]) >= 17,
            "The marker draft's USB writes must remain limited to the extracted endpoint-0 sequence.",
            evidence="analysis/open-firmware-probes/usb-marker-draft/endpoint0-sequence-scan.json",
        )
    )
    checks.append(
        check(
            "usb_marker_data_stage_submit_present",
            any(
                item.get("register") == "0xb3000014"
                and item.get("value") == "0x900226f0"
                and item.get("sequence") == "data_stage_submit"
                for item in marker_sequence
            )
            and any(
                item.get("register") == "0xb3000000"
                and item.get("value") == "0x00000108"
                and item.get("kind") == "endpoint0_or_write"
                for item in marker_sequence
            ),
            "The marker draft must submit the control-IN descriptor ring and kick the transfer path.",
            evidence="analysis/open-firmware-probes/usb-marker-draft/endpoint0-sequence-scan.json",
        )
    )
    checks.append(
        check(
            "usb_marker_contract_has_no_engine_video_mmio",
            severity_count(marker_contract, "fail") == 0
            and all(item.get("kind") == "mapped_usb_mmio" for item in marker_contract),
            "The marker draft must stay USB-only and avoid engine/video MMIO.",
            evidence="analysis/open-firmware-probes/usb-marker-draft/usb-contract-scan.json",
        )
    )
    checks.append(
        check(
            "usb_marker_memory_boundary_has_descriptor_ring",
            len(
                [
                    item
                    for item in marker_memory
                    if item.get("kind") == "usb_transfer_descriptor_ring" and item.get("access") == "write"
                ]
            )
            == 4
            and any(
                item.get("kind") == "usb_staging_buffer" and item.get("access") == "write"
                for item in marker_memory
            ),
            "The memory boundary scan must show the marker copy into USB staging RAM and the four descriptor-ring writes.",
            evidence="analysis/open-firmware-probes/usb-marker-draft/memory-boundary-scan.json",
        )
    )
    marker_responses = [
        scenario
        for scenario in marker_behavior.get("scenarios", [])
        if scenario.get("decision", {}).get("result") == "marker_response"
    ]
    marker_poll_continue = [
        scenario
        for scenario in marker_behavior.get("scenarios", [])
        if scenario.get("decision", {}).get("result") == "poll_continue"
    ]
    marker_descriptors = {item["decision"].get("descriptor") for item in marker_responses}
    marker_product_responses = [
        item for item in marker_responses if item["decision"].get("descriptor") == "open marker product"
    ]
    checks.append(
        check(
            "usb_marker_behavior_models_descriptor_responder",
            {"device", "configuration", "language", "manufacturer", "open marker product"} <= marker_descriptors
            and {item["decision"].get("sequence") for item in marker_product_responses}
            == {"sequence_a", "sequence_b"}
            and any(
                item["decision"].get("descriptor") == "open marker product"
                and item["decision"].get("response_len") == 4
                for item in marker_responses
            )
            and any(
                item["decision"].get("descriptor") == "configuration"
                and item["decision"].get("response_len") == 9
                for item in marker_responses
            )
            and len(marker_poll_continue) >= 2,
            "The host-side marker model must cover standard USB descriptors, both stock product gates, clipped host length, and polling continuation for non-matching setup/gate states.",
            evidence="analysis/open-firmware-probes/usb-marker-draft/behavior-model.json",
        )
    )
    checks.append(
        check(
            "usb_marker_behavior_models_data_stage",
            all(
                scenario["decision"].get("data_stage", {}).get("descriptor_submit_register") == "0xb3000014"
                and scenario["decision"].get("data_stage", {}).get("descriptor_submit_value") == "0x900226f0"
                and scenario["decision"].get("data_stage", {}).get("transfer_kick_or") == "0x00000108"
                and scenario["decision"].get("post_response", {}).get("after_submit") == "wait_for_gate_clear"
                and scenario["decision"].get("post_response", {}).get("when_clear") == "return_to_poll_loop"
                for scenario in marker_responses
            ),
            "The marker behavior model must include the descriptor submit register, transfer kick, and post-response rearm plan, not just the setup decision.",
            evidence="analysis/open-firmware-probes/usb-marker-draft/behavior-model.json",
        )
    )

    open_endpoint0 = read_json("analysis/usb-path/open-endpoint0-model.json")
    setup_source = read_json("analysis/usb-path/usb-setup-source.json")
    control_in = read_json("analysis/usb-path/control-in-data-stage.json")
    control_completion = read_json("analysis/usb-path/control-completion-event.json")
    usb_interrupt_events = read_json("analysis/usb-path/usb-interrupt-events.json")
    open_marker_cases = [
        scenario
        for scenario in open_endpoint0.get("scenarios", [])
        if scenario.get("open_marker") and scenario.get("label") == "product string"
    ]
    checks.append(
        check(
            "host_endpoint0_model_has_open_marker_product_string",
            any(
                "HP1020 OPEN MARKER" in scenario.get("result", {}).get("response_text", "")
                or "48 00 50 00 31 00 30 00 32 00 30 00" in scenario.get("result", {}).get("response_hex", "")
                for scenario in open_marker_cases
            ),
            "The pure host endpoint-0 model must include the open marker string response case.",
            evidence="analysis/usb-path/open-endpoint0-model.json",
        )
    )
    checks.append(
        check(
            "usb_setup_source_narrowed_to_direct_buffer",
            setup_source.get("setup_packet_base_candidate") == "0x90021348"
            and {"0x2", "0x6", "0x7"}.issubset(set(setup_source.get("stock_descriptor_branch_offsets_seen", [])))
            and setup_source.get("event_pointer_register") == "0xb3000214",
            "Static USB evidence must preserve the narrowed setup-buffer candidate and separate event pointer boundary.",
            evidence="analysis/usb-path/usb-setup-source.json",
        )
    )
    checks.append(
        check(
            "usb_marker_reads_required_setup_fields",
            {"0x0", "0x1", "0x2", "0x3", "0x6", "0x7"}.issubset(
                set(setup_source.get("open_marker_offsets_read", []))
            ),
            "The open marker draft must read request type, request, descriptor selector, and host length before responding.",
            evidence="analysis/usb-path/usb-setup-source.json",
        )
    )
    control_constants = control_in.get("constants", {})
    scenarios_by_len = {item["response_len"]: item for item in control_in.get("scenarios", [])}
    checks.append(
        check(
            "control_in_data_stage_constants_resolved",
            control_constants.get("descriptor_flag") == "0x08000000"
            and control_constants.get("descriptor_base") == "0x900226f0"
            and control_constants.get("staging_buffer") == "0x90022bd0"
            and control_constants.get("descriptor_submit_register") == "0xb3000014",
            "Control-IN data-stage constants must preserve descriptor ring, staging buffer, and submit register evidence.",
            evidence="analysis/usb-path/control-in-data-stage.json",
        )
    )
    checks.append(
        check(
            "control_completion_event_model_resolved",
            control_completion.get("status") == "pass"
            and control_completion.get("event_object") == "0x10021318"
            and control_completion.get("control_in_wait", {}).get("requested_bits") == "0x00000001"
            and control_completion.get("usb2_thread_wait", {}).get("requested_bits") == "0x00010000",
            "The control completion path must remain modeled as event flags, with separate control-IN and USB2Thread wake bits.",
            evidence="analysis/usb-path/control-completion-event.json",
        )
    )
    checks.append(
        check(
            "usb_interrupt_event_model_resolved",
            usb_interrupt_events.get("status") == "pass"
            and usb_interrupt_events.get("constants", {}).get("completion_event_flags") == "0x10021318"
            and usb_interrupt_events.get("event_scan", {}).get("completion_status_bit") == "0x400"
            and usb_interrupt_events.get("event_scan", {}).get("lane_stride") == "0x20"
            and usb_interrupt_events.get("event_scan", {}).get("bulk_receive_lane", {}).get("event_bit")
            == "0x00020000"
            and usb_interrupt_events.get("event_scan", {}).get("bulk_receive_lane", {}).get("lane_status_register")
            == "0xb3000224"
            and usb_interrupt_events.get("event_scan", {}).get("bulk_receive_lane", {}).get("lane_ack_register")
            == "0xb3000220"
            and usb_interrupt_events.get("event_scan", {}).get("bulk_buffer_updates", {}).get(
                "available_size_word"
            )
            == "0x1001bc50",
            "The USB interrupt event model must keep the completion event object, per-lane stride, 0x400 completion status bit, and bank-1/lane-1 bulk receive event.",
            evidence="analysis/usb-path/usb-interrupt-events.json",
        )
    )
    checks.append(
        check(
            "control_in_open_marker_descriptor_shape",
            scenarios_by_len.get(38, {}).get("batches", [{}])[0].get("descriptor_count") == 1
            and scenarios_by_len.get(38, {}).get("batches", [{}])[0].get("descriptors", [{}])[0].get("control_word")
            == 0x08000026,
            "A 38-byte open marker response should model as one flagged control-IN descriptor.",
            evidence="analysis/usb-path/control-in-data-stage.json",
        )
    )
    checks.append(
        check(
            "control_in_large_response_batches",
            len(scenarios_by_len.get(321, {}).get("batches", [])) == 2
            and [batch.get("descriptor_count") for batch in scenarios_by_len.get(321, {}).get("batches", [])]
            == [5, 1],
            "Large control-IN responses should preserve the modeled five-descriptor batch limit before another kick.",
            evidence="analysis/usb-path/control-in-data-stage.json",
        )
    )

    fail_count = severity_count(checks, "fail")
    return {
        "summary": "Cross-report consistency gate for the current offline reverse-engineering state.",
        "status": "pass" if fail_count == 0 else "fail",
        "check_count": len(checks),
        "fail_count": fail_count,
        "high_level_result": (
            "The inert USB bulk receive/framing implementation is internally consistent offline; guarded hardware execution and controller behavior remain unproven, and printing is not implemented."
            if fail_count == 0
            else "Offline analysis has drifted; inspect failed checks before doing hardware work."
        ),
        "checks": checks,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 Offline Analysis Consistency Check",
        "",
        "This report cross-checks the generated reverse-engineering artifacts against the conclusions we are relying on.",
        "It does not contact the printer.",
        "",
        "## Result",
        "",
        f"- status: `{report['status']}`",
        f"- checks: `{report['check_count']}`",
        f"- failures: `{report['fail_count']}`",
        f"- meaning: {report['high_level_result']}",
        "",
        "## Checks",
        "",
        "| Check | Severity | Detail | Evidence |",
        "|---|---|---|---|",
    ]
    for item in report["checks"]:
        lines.append(
            f"| `{item['name']}` | `{item['severity']}` | {item['detail']} | `{item['evidence']}` |"
        )
    lines.extend(
        [
            "",
            "## Practical Meaning",
            "",
            "The mechanically inert USB bulk receive/framing implementation now passes the offline cross-report gate. The next USB unknown is guarded printer-side execution and real controller completion/re-arm behavior; semantic print dispatch, raster output, video transfer, and engine control remain unimplemented or unproven.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    OUT_MD.write_text(render_markdown(report) + "\n")
    print(f"checks={report['check_count']} fail={report['fail_count']}")
    print(OUT_MD)
    return 1 if report["fail_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
