# HP 1020 Offline Analysis Consistency Check

This report cross-checks the generated reverse-engineering artifacts against the conclusions we are relying on.
It does not contact the printer.

## Result

- status: `pass`
- checks: `25`
- failures: `0`
- meaning: Offline analysis is internally consistent; the next decisive evidence is a guarded non-printing printer-side probe.

## Checks

| Check | Severity | Detail | Evidence |
|---|---|---|---|
| `engine_0x17_dispatch_is_default` | `watch` | Engine queue message 0x17 must remain modeled as a default-return receive path, not a direct command handler. | `analysis/engine-dispatch-cfg/engine-dispatch-cfg.md` |
| `queue_map_engine_0x17_matches_cfg` | `watch` | Queue-message map must preserve the current producer/default-consumer conclusion for engine 0x17. | `analysis/message-map/queue-message-map.tsv` |
| `status_correlation_event_count_matches_source` | `watch` | Status correlation must account for every currently cataloged engine 0x17 event word. | `analysis/status-path/status-code-correlation.json` |
| `engine_events_are_not_direct_pjl_codes` | `watch` | Raw engine event words must not be mislabeled as final PJL CODE values. | `analysis/status-path/status-code-correlation.json` |
| `print_model_invariants_have_no_failures` | `watch` | Offline ZjStream model invariants must remain green across generated print-path variants. | `analysis/open-firmware-model/model-invariants.json` |
| `print_model_variant_coverage` | `watch` | Invariant coverage must include paper size, resolution, copy, draft, source, media, and clip variants. | `analysis/open-firmware-model/model-invariants.json` |
| `hardware_boundary_keeps_engine_video_unsafe` | `watch` | The do-not-touch boundary for early custom firmware must still include video and engine paths. | `analysis/hardware-boundary/hardware-boundary.json` |
| `usb_family_remains_only_low_risk_target` | `watch` | USB 0xb300 must remain the only plausible early open-firmware hardware target. | `analysis/hardware-boundary/hardware-boundary.json` |
| `pjl_first_query_is_echo` | `watch` | The first stock/open comparison must remain the non-printing PJL ECHO probe. | `analysis/non-printing-status-probe/pjl-status-contract.json` |
| `pjl_contract_is_non_printing` | `watch` | The status query contract must stay outside print/video/engine execution. | `analysis/non-printing-status-probe/pjl-status-contract.json` |
| `usb_marker_descriptor_is_stable` | `watch` | The open marker descriptor bytes and length must remain fixed. | `analysis/open-firmware-probes/usb-marker-draft/marker-descriptor-check.json` |
| `usb_marker_length_flow_passes` | `watch` | The marker draft must keep host wLength clipping connected to the endpoint-0 response length. | `analysis/open-firmware-probes/usb-marker-draft/marker-length-flow-check.json` |
| `usb_marker_sequence_matches_endpoint0_contract` | `watch` | The marker draft's USB writes must remain limited to the extracted endpoint-0 sequence. | `analysis/open-firmware-probes/usb-marker-draft/endpoint0-sequence-scan.json` |
| `usb_marker_data_stage_submit_present` | `watch` | The marker draft must submit the control-IN descriptor ring and kick the transfer path. | `analysis/open-firmware-probes/usb-marker-draft/endpoint0-sequence-scan.json` |
| `usb_marker_contract_has_no_engine_video_mmio` | `watch` | The marker draft must stay USB-only and avoid engine/video MMIO. | `analysis/open-firmware-probes/usb-marker-draft/usb-contract-scan.json` |
| `usb_marker_memory_boundary_has_descriptor_ring` | `watch` | The memory boundary scan must show the marker copy into USB staging RAM and the four descriptor-ring writes. | `analysis/open-firmware-probes/usb-marker-draft/memory-boundary-scan.json` |
| `usb_marker_behavior_clips_and_uses_both_gates` | `watch` | The host-side marker model must cover both stock gates and clipped host length. | `analysis/open-firmware-probes/usb-marker-draft/behavior-model.json` |
| `usb_marker_behavior_models_data_stage` | `watch` | The marker behavior model must include the descriptor submit register and transfer kick, not just the setup decision. | `analysis/open-firmware-probes/usb-marker-draft/behavior-model.json` |
| `host_endpoint0_model_has_open_marker_product_string` | `watch` | The pure host endpoint-0 model must include the open marker string response case. | `analysis/usb-path/open-endpoint0-model.json` |
| `usb_setup_source_narrowed_to_direct_buffer` | `watch` | Static USB evidence must preserve the narrowed setup-buffer candidate and separate event pointer boundary. | `analysis/usb-path/usb-setup-source.json` |
| `usb_marker_reads_required_setup_fields` | `watch` | The open marker draft must read request type, request, descriptor selector, and host length before responding. | `analysis/usb-path/usb-setup-source.json` |
| `control_in_data_stage_constants_resolved` | `watch` | Control-IN data-stage constants must preserve descriptor ring, staging buffer, and submit register evidence. | `analysis/usb-path/control-in-data-stage.json` |
| `control_completion_event_model_resolved` | `watch` | The control completion path must remain modeled as event flags, with separate control-IN and USB2Thread wake bits. | `analysis/usb-path/control-completion-event.json` |
| `control_in_open_marker_descriptor_shape` | `watch` | A 38-byte open marker response should model as one flagged control-IN descriptor. | `analysis/usb-path/control-in-data-stage.json` |
| `control_in_large_response_batches` | `watch` | Large control-IN responses should preserve the modeled five-descriptor batch limit before another kick. | `analysis/usb-path/control-in-data-stage.json` |

## Practical Meaning

The offline work is now guarded well enough that the main unknown is no longer a missing script or stale note. The main unknown is whether the printer accepts, executes, and responds through the narrow non-printing USB/PJL path we modeled.

