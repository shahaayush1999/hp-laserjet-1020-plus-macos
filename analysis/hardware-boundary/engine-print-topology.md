# HP 1020 Engine Print Topology

This is a generated offline synthesis. It does not contact the printer.

## Result

- status: `pass`
- engine status register: `0xb050000c`
- engine command register: `0xb0500004`

## Important Commands

| Name | Value |
|---|---:|
| `preflight_start_bit` | `0x00020000` |
| `page_start_normal` | `0x00006012` |
| `page_start_reset_latch` | `0x00003a13` |
| `substatus_side_effect` | `0x0000501a` |
| `leave_e6100800_side_effect` | `0x00005043` |

## Topology

### `engine_thread_startup`

- functions: `0x100163b0 engine thread`, `0x100160a8 preflight`, `0x10015df8 status poll`

1. clear active engine work pointer +0x68
2. run preflight, which emits engine message 0x17/e6101100 and sets command-register bit 0x20000
3. poll engine status until the high-bit event family clears
4. register engine datastore callbacks for density/media entries
5. enter receive-with-timeout loop; on timeout, poll status again

### `page_work_acceptance`

- functions: `0x10016164 engine message dispatch`, `0x10015c68 engine status I/O`

1. messages 0x0b and 0x40 poll status before accepting work
2. first work pointer is stored at engine state +0x68; a second pending pointer is stored at +0x6c
3. active work +0x80 selects an engine config through 0x100162b0 and stores it at +0x48
4. normal start submits command 0x6012; reset-latch start submits 0x3a13 and keeps the latch if the ready mask is absent

### `status_poll_and_recovery`

- functions: `0x10015df8 status poll`, `0x10015c68 engine status I/O`

1. poll reads status commands 1, 0x20, 2, 0x16, and 0x13 depending on branch conditions
2. selected event words are stored at engine state +0x60 and emitted as queue 1 message 0x17 when changed
3. side-effect commands 0x501a and 0x5043 are sent from specific status transitions
4. some transitions can call video reset dispatch before engine completion continues

### `completion_and_deferred_work`

- functions: `0x10016164 message 0x11 case`, `video completion feedback`

1. message 0x11 polls status after video/engine completion
2. when no high-bit error family remains, active work +0x68 is returned via message 0x11
3. if deferred work +0x6c exists, dispatch requeues message 0x0b and clears +0x6c

## Important Events

- `0x04800100`
- `0x14000a04`
- `0x20001607`
- `0x80000000`
- `0xe6000d03`
- `0xe6000d04`
- `0xe6000d06`
- `0xe6100800`
- `0xe6100a01`
- `0xe6100b0a`
- `0xe6100b0b`
- `0xe6100e00`
- `0xe6101100`
- `0xf6000300`
- `0xf6000400`
- `0xfe001401`

## Open Firmware Meaning

- This is the mechanical gate for printing: custom firmware cannot safely skip it and only drive video registers.
- The command IDs and event words are now organized as a page-start state machine, but physical labels still require printer-side calibration.
- The next printer-attached tests should capture non-printing status responses before any custom firmware tries to reproduce this path.

## Evidence Checks

| Check | Status | Source | Needle |
|---|---|---|---|
| `thread_clears_active_work` | `present` | `analysis/dispatch-mmio/decompiled/100163b0_hp1020_engine_thread_candidate.c` | `*(undefined4 *)(PTR_DAT_10006920 + 0x68) = 0` |
| `thread_runs_preflight` | `present` | `analysis/dispatch-mmio/decompiled/100163b0_hp1020_engine_thread_candidate.c` | `hp1020_engine_preflight_candidate();` |
| `thread_polls_until_not_high_bit` | `present` | `analysis/dispatch-mmio/decompiled/100163b0_hp1020_engine_thread_candidate.c` | `while (uVar3 = hp1020_engine_status_poll_candidate(0), (uVar3 & uVar1) == uVar1)` |
| `thread_receive_or_poll_loop` | `present` | `analysis/dispatch-mmio/decompiled/100163b0_hp1020_engine_thread_candidate.c` | `threadx_queue_receive_wait_candidate` |
| `dispatch_0b_40_accepts_work` | `present` | `analysis/dispatch-mmio/decompiled/10016164_hp1020_engine_message_dispatch_candidate.c` | `case 0x40:` |
| `dispatch_stores_active_work` | `present` | `analysis/dispatch-mmio/decompiled/10016164_hp1020_engine_message_dispatch_candidate.c` | `*(undefined4 *)(puVar2 + 0x68) = param_1[3]` |
| `dispatch_stores_deferred_work` | `present` | `analysis/dispatch-mmio/decompiled/10016164_hp1020_engine_message_dispatch_candidate.c` | `*(undefined4 *)(puVar2 + 0x6c) = param_1[3]` |
| `dispatch_maps_engine_config` | `present` | `analysis/dispatch-mmio/decompiled/10016164_hp1020_engine_message_dispatch_candidate.c` | `FUN_100162b0(*(undefined2 *)(*(int *)(PTR_DAT_10006920 + 0x68) + 0x80))` |
| `dispatch_start_command_6012` | `present` | `analysis/dispatch-mmio/decompiled/10016164_hp1020_engine_message_dispatch_candidate.c` | `hp1020_engine_status_io_candidate(DAT_100069a4)` |
| `dispatch_reset_command_3a13` | `present` | `analysis/dispatch-mmio/decompiled/10016164_hp1020_engine_message_dispatch_candidate.c` | `uVar4 = hp1020_engine_status_io_candidate(DAT_100069a0)` |
| `dispatch_completion_message_11` | `present` | `analysis/dispatch-mmio/decompiled/10016164_hp1020_engine_message_dispatch_candidate.c` | `case 0x11:` |
| `dispatch_requeues_deferred_work` | `present` | `analysis/dispatch-mmio/decompiled/10016164_hp1020_engine_message_dispatch_candidate.c` | `hp1020_send_or_raise_engine_msg_candidate(0,&local_40)` |
| `preflight_emits_1100` | `present` | `analysis/dispatch-mmio/decompiled/100160a8_hp1020_engine_preflight_candidate.c` | `uStack_3c = DAT_100063dc` |
| `preflight_sets_command_bit` | `present` | `analysis/dispatch-mmio/decompiled/100160a8_hp1020_engine_preflight_candidate.c` | `*hp1020_engine_command_reg_table_word = *hp1020_engine_command_reg_table_word \| DAT_10005e74` |
| `preflight_timeout_event` | `present` | `analysis/dispatch-mmio/decompiled/100160a8_hp1020_engine_preflight_candidate.c` | `uStack_2c = DAT_1000692c` |
| `engine_io_register_pair` | `present` | `analysis/dispatch-mmio/decompiled/10015c68_hp1020_engine_status_io_candidate.c` | `*puVar6 = *puVar6 & uVar1 \| (uint)*(ushort *)(puVar4 + 0x5a)` |
| `poll_status_decision_entry` | `present` | `analysis/dispatch-mmio/decompiled/10015df8_hp1020_engine_status_poll_candidate.c` | `uVar4 = hp1020_engine_status_io_candidate(1)` |
