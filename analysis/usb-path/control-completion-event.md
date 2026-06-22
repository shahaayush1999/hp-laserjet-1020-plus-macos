# HP 1020 USB Control Completion Event Model

This is an offline model. It does not contact the printer.

## Key Result

- The object at `0x10021318` is better modeled as an event-flag object, not a message queue.
- The stock control-IN sender waits for bit `0x00000001`, with clear-on-success behavior and infinite timeout.
- USB interrupt task `0x10008208` is the static source that sets bits on this same object.
- The main USB2Thread service loop waits on bit `0x00010000`, so the same event object carries multiple USB event lanes.

## Control-IN Wait

| Field | Value |
|---|---|
| `function` | `0x10008c24 hp1020_usb_control_tx_data_stage_candidate` |
| `wrapper` | `0x10017d28 event_flags_get_wrapper_candidate` |
| `core` | `0x10019408 event_flags_get_core_candidate` |
| `requested_bits` | `0x00000001` |
| `mode` | `0x00000001` |
| `mode_meaning` | `OR wait, clear matched bits on success` |
| `timeout` | `0xffffffff` |

## Event Setter

| Field | Value |
|---|---|
| `interrupt_task` | `0x10008208 hp1020_usb_interrupt_task_candidate` |
| `wrapper` | `0x10017dac event_flags_set_wrapper_candidate` |
| `core` | `0x1001896c event_flags_set_core_candidate` |
| `operation` | `event_state_word |= bits; wake suspended waiters whose masks now match` |
| `bit_source` | `1 << ((event_group_base + event_index) & 0x1f)` |

## Open-Firmware Meaning

- The stock path does not just poll a simple completion register after 0xb3000000 |= 0x108.
- It relies on USB interrupt 4 feeding an event-flag object at 0x10021318.
- The current marker draft submits the descriptor and idles; that might be enough for one host read, but it does not prove rearm/cleanup semantics.
- A standalone open implementation either needs a tiny interrupt/event path or a live-tested polling rule for the relevant 0xb300 registers.

## Evidence Checks

- status: `pass`

| Status | Evidence | Needle |
|---|---|---|
| `present` | `analysis/usb-path/decompiled-neighbors/10008c24_hp1020_usb_control_tx_data_stage_candidate.c` | `threadx_queue_receive_candidate(puVar1,1,1,auStack_30,0xffffffff)` |
| `present` | `analysis/usb-path/decompiled-neighbors/10019408_FUN_10019408.c` | `*(uint *)(param_1 + 8) = *(uint *)(param_1 + 8) & (param_2 ^ 0xffffffff)` |
| `present` | `analysis/tasks/task-decompiled/10008208_hp1020_task_entry_10008208.c` | `FUN_10017dac(PTR_DAT_10005e18,iVar11,0)` |
| `present` | `analysis/tasks/task-decompiled/10008208_hp1020_task_entry_10008208.c` | `FUN_10017dac(PTR_DAT_10005e18,1 << 0x20 - (0x20 - (uVar6 + uVar8 & 0x1f)),0)` |
| `present` | `analysis/message-producers/producer-decompiled/1001896c_FUN_1001896c.c` | `param_2 = *(uint *)(param_1 + 8) \| param_2` |
| `present` | `analysis/tasks/task-decompiled/10008ff0_hp1020_usb2_thread.c` | `threadx_queue_receive_candidate(PTR_DAT_10005e18,DAT_10005f20,1,auStack_50,0xffffffff)` |

