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
            and sequence_by_step.get(5, {}).get("projected_state", {}).get("state_plus_0xbc") == 2400
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
            and dataflow_stages.get("helper_channel_b_refill", {}).get("known_values", {}).get("video state +0xd0 candidate if alias holds") == 6824
            and dataflow_stages.get("helper_channel_b_refill", {}).get("remaining_unknown")
            == "active work +0x26 remains unsourced; ZJI_VIDEO_Y reaches page-param +0x26 upstream, but the queue payload chain weakens that alias/copy theory"
            and dataflow_stages.get("helper_channel_b_refill", {}).get("known_values", {}).get("0xb2080008 candidate if alias holds") == 4800
            and "min(4, +0xd0) * stride(1200)"
            == dataflow_stages.get("helper_channel_b_refill", {}).get("known_values", {}).get("0xb2080008")
            and "A pointer plus dual-output window(2400) when dual-block mode is active"
            == dataflow_stages.get("raw_band_queue_feed", {}).get("known_values", {}).get("0xb1000108")
            and all(item.get("status") == "present" for item in video_dataflow.get("checks", [])),
            "The video dataflow contract must preserve concrete a4_default values through render/refill boundary formulas.",
            evidence="analysis/hardware-boundary/video-dataflow-contract.json",
        )
    )
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
            and "weakens the earlier page-param +0x26 -> work +0x26 alias theory"
            in queue_payload_chain.get("conclusion", {}).get("effect_on_remaining_units", "")
            and len(queue_payload_chain.get("stages", [])) == 7
            and queue_chain_checks.get("video_thread_uses_payload_as_prepare_argument", {}).get("status") == "present"
            and queue_chain_checks.get("work_populate_does_not_copy_page_param_0x26", {}).get("status") == "present"
            and all(item.get("status") == "present" for item in queue_payload_chain.get("checks", [])),
            "The video queue payload chain must preserve that prepare receives the 0x94 work object, while work +0x26 remains unsourced.",
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
            "video_prepare_argument_fields_separate_sourced_and_unsourced",
            prepare_fields.get("status") == "pass"
            and prepare_fields.get("prepare_argument_identity") == "0x94-byte video/page work object"
            and prepare_field_rows.get("+0x84/+0x88/+0x8c/+0x90", {}).get("source_status") == "sourced"
            and prepare_field_rows.get("+0x26", {}).get("source_status") == "unsourced_active_work"
            and prepare_field_rows.get("+0x30", {}).get("source_status") == "unsourced_active_work"
            and prepare_field_rows.get("+0x32", {}).get("source_status") == "unsourced_active_work"
            and prepare_field_rows.get("+0x74", {}).get("source_status") == "default_zero_for_current_path"
            and prepare_fields.get("field_status_counts", {}).get("unsourced_active_work") == 3
            and all(item.get("status") == "present" for item in prepare_fields.get("checks", [])),
            "The prepare argument field model must keep render geometry sourced while +0x26/+0x30/+0x32 remain unsourced on active work.",
            evidence="analysis/hardware-boundary/video-prepare-argument-fields.json",
        )
    )
    remaining_units = read_json("analysis/hardware-boundary/video-remaining-units.json")
    remaining_cases = {
        item.get("case"): item
        for item in remaining_units.get("case_matrix_if_alias_holds", [])
        if isinstance(item, dict)
    }
    copy_gap = {
        item.get("stage"): item
        for item in remaining_units.get("candidate_chain", [])
        if isinstance(item, dict)
    }
    checks.append(
        check(
            "video_remaining_units_keeps_alias_gap_explicit",
            remaining_units.get("status") == "pass"
            and copy_gap.get("copy_or_alias_gap", {}).get("status") == "unresolved and weakened"
            and remaining_cases.get("a4_default", {}).get("video_y_candidate_from_zji_0x12") == 6824
            and remaining_cases.get("a4_default", {}).get("candidate_first_channel_b_length_if_alias_holds") == 4800
            and remaining_cases.get("letter_default", {}).get("video_y_candidate_from_zji_0x12") == 6408
            and remaining_cases.get("legal_default", {}).get("video_y_candidate_from_zji_0x12") == 8208
            and all(item.get("status") == "present" for item in remaining_units.get("checks", [])),
            "Video remaining-unit model must preserve ZJI_VIDEO_Y upstream values while keeping active work +0x26 unsourced.",
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
            and chunk_sizing.get("helper_hypothesis", {}).get("strong_hypothesis")
            == "for denominator >= 2, returns ceil(numerator / denominator)"
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
    helper_checks = {
        item.get("name"): item
        for item in helper_disassembly.get("checks", [])
        if isinstance(item, dict)
    }
    checks.append(
        check(
            "video_helper_disassembly_keeps_divide_path_bounded",
            helper_disassembly.get("status") == "pass"
            and helper_disassembly.get("helper", {}).get("working_name") == "ceil_div_or_units_encode_candidate"
            and helper_disassembly.get("helper", {})
            .get("confirmed_behavior", {})
            .get("denominator_0")
            == "returns 0"
            and helper_disassembly.get("helper", {})
            .get("confirmed_behavior", {})
            .get("denominator_1")
            == "returns numerator"
            and helper_disassembly.get("helper", {})
            .get("unconfirmed_behavior", {})
            .get("denominator_ge_2")
            == "caller-fit hypothesis remains ceil(numerator / denominator)"
            and helper_disassembly.get("conclusion", {}).get("status") == "bounded_hypothesis"
            and len(helper_disassembly.get("ghidra_pcode_error_hits", [])) >= 1
            and helper_checks.get("local_objdump_does_not_confirm_divide_path", {}).get("status") == "present"
            and all(item.get("status") == "present" for item in helper_disassembly.get("checks", [])),
            "The helper disassembly report must preserve the confirmed 0/1 edge cases while keeping the divide path bounded as a hypothesis.",
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
            and all(state.get("state_plus_0xc8_state_200") == 2 for state in callback_states)
            and all(state.get("state_plus_0xf4") == 2 for state in callback_states)
            and all(state.get("state_plus_0xbc") == state.get("stride_plus_0xb8") * 2 for state in callback_states)
            and all(check.get("status") == "present" for check in video_prepare_projection.get("checks", [])),
            "The video prepare projection must keep the generated host variants narrowed to 600dpi/NBIE=1 setup scenarios with the expected two-output callback state.",
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
