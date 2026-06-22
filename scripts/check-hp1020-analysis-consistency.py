#!/usr/bin/env python3
"""Cross-check the current offline HP 1020 reverse-engineering conclusions."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT_DIR / "analysis/offline-consistency/offline-consistency.json"
OUT_MD = ROOT_DIR / "analysis/offline-consistency/offline-consistency.md"


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


def build_report() -> dict[str, Any]:
    checks: list[dict[str, str]] = []

    dispatch_md = read_text("analysis/engine-dispatch-cfg/engine-dispatch-cfg.md")
    queue_map = read_tsv("analysis/message-map/queue-message-map.tsv")
    engine_017 = [
        row
        for row in queue_map
        if row.get("queue_id") == "1" and row.get("message_id") == "0x17"
    ]
    checks.append(
        check(
            "engine_0x17_dispatch_is_default",
            "| `0x17` | `100162aa` | default return/no-op |" in dispatch_md,
            "Engine queue message 0x17 must remain modeled as a default-return receive path, not a direct command handler.",
            evidence="analysis/engine-dispatch-cfg/engine-dispatch-cfg.md",
        )
    )
    checks.append(
        check(
            "queue_map_engine_0x17_matches_cfg",
            len(engine_017) == 1
            and "default return block 0x100162aa" in engine_017[0].get("consumer_or_handler", "")
            and "high producer" in engine_017[0].get("confidence", ""),
            "Queue-message map must preserve the current producer/default-consumer conclusion for engine 0x17.",
            evidence="analysis/message-map/queue-message-map.tsv",
        )
    )

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
    scope_components = {
        item.get("component"): item
        for item in minimal_scope.get("components", [])
        if isinstance(item, dict)
    }
    scope_evidence = minimal_scope.get("stock_evidence", {})
    checks.append(
        check(
            "minimal_print_scope_keeps_parser_mapped_and_hardware_blocked",
            scope_evidence.get("missing_required_messages") == []
            and scope_evidence.get("model_invariant_failures") == 0
            and scope_evidence.get("endpoint0_data_cases") == 24
            and scope_components.get("ZjStream parser and JobMgr object model", {}).get("current_status") == "mapped"
            and scope_components.get("Video/raw-band hardware feed", {}).get("risk") == "high"
            and scope_components.get("Engine paper/fuser/motor coordination", {}).get("risk") == "high",
            "The generated narrow-scope report must preserve the current split: parser/object path mapped, video/engine hardware still high risk.",
            evidence="analysis/open-firmware-model/minimal-print-scope.json",
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
            and sequence_by_step.get(2, {}).get("risk") == "high"
            and sequence_by_step.get(6, {}).get("projected_registers", {}).get("0xb2000008", {}).get("value") == 9600
            and sequence_by_step.get(7, {}).get("projected_registers", {}).get("0xb1000008/0xb1000108", {}).get("consumer")
            == "0x100140f8 hp1020_video_refresh_raw_bands_candidate"
            and len(first_page.get("remaining_unknowns", [])) >= 4,
            "The first-page hardware sequence must preserve the ordered engine/video/raw-band risk boundary.",
            evidence="analysis/hardware-boundary/first-page-hardware-sequence.json",
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
            severity_count(marker_len, "fail") == 0 and len(marker_len) == 4,
            "The marker draft must keep host wLength clipping connected to the endpoint-0 response length.",
            evidence="analysis/open-firmware-probes/usb-marker-draft/marker-length-flow-check.json",
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
    checks.append(
        check(
            "usb_marker_behavior_clips_and_uses_both_gates",
            len(marker_responses) == 3
            and {item["decision"].get("sequence") for item in marker_responses} == {"sequence_a", "sequence_b"}
            and any(item["decision"].get("response_len") == 4 for item in marker_responses),
            "The host-side marker model must cover both stock gates and clipped host length.",
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
                for scenario in marker_responses
            ),
            "The marker behavior model must include the descriptor submit register and transfer kick, not just the setup decision.",
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
            and usb_interrupt_events.get("event_scan", {}).get("lane_stride") == "0x20",
            "The USB interrupt event model must keep the completion event object, per-lane stride, and 0x400 completion status bit.",
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
            "Offline analysis is internally consistent; the next decisive evidence is a guarded non-printing printer-side probe."
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
            "The offline work is now guarded well enough that the main unknown is no longer a missing script or stale note. The main unknown is whether the printer accepts, executes, and responds through the narrow non-printing USB/PJL path we modeled.",
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
