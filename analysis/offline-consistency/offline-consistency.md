# HP 1020 Offline Analysis Consistency Check

This report cross-checks the generated reverse-engineering artifacts against the conclusions we are relying on.
It does not contact the printer.

## Result

- status: `pass`
- checks: `51`
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
| `minimal_print_scope_keeps_parser_mapped_and_hardware_blocked` | `watch` | The generated narrow-scope report must preserve the current split: parser/object path mapped, video/engine hardware still high risk. | `analysis/open-firmware-model/minimal-print-scope.json` |
| `raster_field_semantics_keep_host_to_video_chain` | `watch` | Raster field semantics must preserve the host ZjStream/JBIG to work/raster object chain consumed by video hardware. | `analysis/open-firmware-model/raster-field-semantics.json` |
| `hardware_boundary_keeps_engine_video_unsafe` | `watch` | The do-not-touch boundary for early custom firmware must still include video and engine paths. | `analysis/hardware-boundary/hardware-boundary.json` |
| `first_page_sequence_keeps_video_engine_registers_ordered` | `watch` | The first-page hardware sequence must preserve the ordered engine/video/refill risk boundary. | `analysis/hardware-boundary/first-page-hardware-sequence.json` |
| `video_dataflow_contract_keeps_a4_default_path` | `watch` | The video dataflow contract must preserve concrete a4_default values through render/refill boundary formulas. | `analysis/hardware-boundary/video-dataflow-contract.json` |
| `video_queue_payload_chain_identifies_prepare_work_object` | `watch` | The video queue payload chain must preserve that prepare receives the 0x94 work object, while work +0x26 remains unsourced. | `analysis/hardware-boundary/video-queue-payload-chain.json` |
| `video_prepare_argument_fields_separate_sourced_and_unsourced` | `watch` | The prepare argument field model must keep render geometry sourced while +0x26/+0x30/+0x32 remain unsourced on active work. | `analysis/hardware-boundary/video-prepare-argument-fields.json` |
| `video_sideband_write_census_rules_out_false_leads` | `watch` | The sideband write census must preserve that selected +0x26/+0x30/+0x32 hits are upstream writers or consumers, not active work-object writers. | `analysis/hardware-boundary/video-sideband-write-census.json` |
| `video_sideband_copy_direction_rules_out_hidden_source` | `watch` | The sideband copy-direction model must preserve that case 0x29 copies active work out to runtime block, not into work +0x26/+0x30/+0x32. | `analysis/hardware-boundary/video-sideband-copy-direction.json` |
| `video_sideband_default_impact_keeps_0x26_critical` | `watch` | The sideband default-impact model must keep +0x26 as print-path critical, +0x32 mode-critical, and +0x30 lower priority. | `analysis/hardware-boundary/video-sideband-default-impact.json` |
| `video_zero_sideband_scenario_keeps_refill_blocker_narrow` | `watch` | The zero-sideband scenario must keep the refined conclusion: initial channel A can arm, but channel-B refill/descriptor state is not seeded. | `analysis/hardware-boundary/video-zero-sideband-scenario.json` |
| `video_remaining_units_keeps_alias_gap_explicit` | `watch` | Video remaining-unit model must preserve ZJI_VIDEO_Y upstream values while keeping active work +0x26 unsourced. | `analysis/hardware-boundary/video-remaining-units.json` |
| `video_chunk_sizing_projects_stride_and_cc` | `watch` | Video chunk sizing must preserve the stride-derived +0xcc projection and helper caveat. | `analysis/hardware-boundary/video-chunk-sizing.json` |
| `video_helper_disassembly_keeps_divide_path_bounded` | `watch` | The helper disassembly report must preserve the confirmed 0/1 edge cases while keeping the divide path bounded as a hypothesis. | `analysis/hardware-boundary/video-helper-disassembly.json` |
| `video_engine_register_semantics_resolved` | `watch` | The video/engine register-semantics report must keep the key engine, video, channel, and raw-band roles resolved. | `analysis/hardware-boundary/video-engine-register-semantics.json` |
| `video_prepare_modes_keep_timing_tables` | `watch` | The video-prepare mode model must preserve the branch-dependent 0xb100 timing/setup table evidence. | `analysis/hardware-boundary/video-prepare-modes.json` |
| `engine_command_status_model_resolved` | `watch` | The engine command/status model must preserve the stock 0xb050 register pair, command IDs, state fields, and event branches. | `analysis/hardware-boundary/engine-command-status.json` |
| `engine_status_decision_model_resolved` | `watch` | The executable engine status decision model must preserve ready rewrite, 0x501a/0x5043 side effects, and previous-event extra emit behavior. | `analysis/hardware-boundary/engine-status-decisions.json` |
| `engine_print_topology_model_resolved` | `watch` | The engine print topology must preserve startup/preflight, page acceptance, polling/recovery, completion/deferred-work stages, and key stock engine commands. | `analysis/hardware-boundary/engine-print-topology.json` |
| `video_engine_feedback_model_resolved` | `watch` | The video-to-engine feedback model must preserve normal completion, reset/flush, requeue, and video event-word behavior. | `analysis/hardware-boundary/video-engine-feedback.json` |
| `video_transfer_ring_model_resolved` | `watch` | The video transfer ring model must preserve producer/consumer collision behavior, channel A/B descriptors, and IRQ refill evidence. | `analysis/hardware-boundary/video-transfer-ring.json` |
| `video_irq_decision_model_resolved` | `watch` | The video IRQ decision model must preserve branch priority, refill, and reset-dispatch cases 0/3/4/7. | `analysis/hardware-boundary/video-irq-decisions.json` |
| `video_band_queue_model_resolved` | `watch` | The video band queue model must preserve +0xdc/+0xe0 collision behavior and raw-band A/B register writes. | `analysis/hardware-boundary/video-band-queue.json` |
| `video_mode_flag_model_resolved` | `watch` | The video mode-flag model must preserve the work +0x74 to state +0xfc sign-bit fork between descriptor queue and raw linked-list refill. | `analysis/hardware-boundary/video-mode-flag.json` |
| `video_refill_topology_model_resolved` | `watch` | The video refill topology must preserve the normal descriptor-queue path and the alternate raw linked-list path as separate unsafe video refills. | `analysis/hardware-boundary/video-refill-topology.json` |
| `video_prepare_projection_narrows_generated_variants` | `watch` | The video prepare projection must keep the generated host variants narrowed to 600dpi/NBIE=1 setup scenarios with the expected two-output callback state. | `analysis/hardware-boundary/video-prepare-projection.json` |
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
| `usb_interrupt_event_model_resolved` | `watch` | The USB interrupt event model must keep the completion event object, per-lane stride, and 0x400 completion status bit. | `analysis/usb-path/usb-interrupt-events.json` |
| `control_in_open_marker_descriptor_shape` | `watch` | A 38-byte open marker response should model as one flagged control-IN descriptor. | `analysis/usb-path/control-in-data-stage.json` |
| `control_in_large_response_batches` | `watch` | Large control-IN responses should preserve the modeled five-descriptor batch limit before another kick. | `analysis/usb-path/control-in-data-stage.json` |

## Practical Meaning

The offline work is now guarded well enough that the main unknown is no longer a missing script or stale note. The main unknown is whether the printer accepts, executes, and responds through the narrow non-printing USB/PJL path we modeled.

