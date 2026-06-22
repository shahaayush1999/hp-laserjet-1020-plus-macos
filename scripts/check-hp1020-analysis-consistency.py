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
            "usb_marker_contract_has_no_engine_video_mmio",
            severity_count(marker_contract, "fail") == 0
            and all(item.get("kind") == "mapped_usb_mmio" for item in marker_contract),
            "The marker draft must stay USB-only and avoid engine/video MMIO.",
            evidence="analysis/open-firmware-probes/usb-marker-draft/usb-contract-scan.json",
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

    open_endpoint0 = read_json("analysis/usb-path/open-endpoint0-model.json")
    setup_source = read_json("analysis/usb-path/usb-setup-source.json")
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
