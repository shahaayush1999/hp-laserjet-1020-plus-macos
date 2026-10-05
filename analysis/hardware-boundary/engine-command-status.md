# HP 1020 Engine Command/Status Model

This is a generated offline model. It does not contact the printer.

## Result

- status: `pass`
- scope: stock firmware engine command/status boundary for print start and status polling

## Key Literal Values

| Name | Value |
|---|---:|
| `engine_command_preserve_mask` | `0xffff0000` |
| `engine_start_status_bit` | `0x00002000` |
| `status_0x20_0x800_mask` | `0x00000800` |
| `fallback_error_event` | `0x80000000` |
| `preflight_start_bit` | `0x00020000` |
| `dispatch_ready_mask` | `0x00008000` |
| `engine_ready_submit_bit` | `0x00010000` |
| `status_2_0x4000_mask` | `0x00004000` |
| `status_2_0x1000_mask` | `0x00001000` |
| `default_primary_event` | `0x04800100` |
| `low16_0x0a04` | `0x00000a04` |
| `event_preflight_or_status_1100` | `0xe6101100` |
| `event_status_1607` | `0x20001607` |
| `status_all_ones` | `0x0000ffff` |
| `engine_status_register` | `0xb050000c` |
| `engine_state_base` | `0x1002f0c4` |
| `engine_clear_mask` | `0xfeffffff` |
| `engine_command_register` | `0xb0500004` |
| `timeout_event` | `0xfe001401` |
| `primary_0x4040_mask` | `0x00004040` |
| `event_f6000300` | `0xf6000300` |
| `event_f6000400` | `0xf6000400` |
| `event_e6100b0a` | `0xe6100b0a` |
| `event_e6100b0b` | `0xe6100b0b` |
| `switch_table_0x13` | `0x100059c0` |
| `event_ready_ok` | `0xe6100a01` |
| `event_e6000d03` | `0xe6000d03` |
| `event_e6000d06` | `0xe6000d06` |
| `event_e6000d04` | `0xe6000d04` |
| `command_0x501a` | `0x0000501a` |
| `event_e6100800` | `0xe6100800` |
| `event_e6100e00` | `0xe6100e00` |
| `low16_0x0a01` | `0x00000a01` |
| `event_0x14000a04` | `0x14000a04` |
| `command_0x5043` | `0x00005043` |
| `primary_0x2e00_mask` | `0x00002e00` |
| `state_ptr_0x48_a` | `0x1001cd34` |
| `state_ptr_0x4c_b` | `0x1001cd3c` |
| `dispatch_queue_ptr` | `0x10030594` |
| `command_0x3a13` | `0x00003a13` |
| `command_0x6012` | `0x00006012` |

## Engine Status I/O Calls

| Source | Argument | Value | Kind | Role |
|---|---:|---:|---|---|
| `engine_poll` | `1` | `0x1` | `status_read` | primary engine status word |
| `engine_poll` | `0x20` | `0x20` | `status_read` | secondary status word for f600 status branch |
| `engine_poll` | `2` | `0x2` | `status_read` | tertiary status word for e610/20001607 branch |
| `engine_poll` | `0x16` | `0x16` | `status_read` | substatus word for e6000dxx and follow-up poll |
| `engine_poll` | `DAT_10006968` | `0x0000501a` | `engine_command` | side-effect command used in substatus 0x16 branch |
| `engine_poll` | `0x13` | `0x13` | `status_read` | substatus switch for e6100b0a/e6100b0b branch |
| `engine_poll` | `DAT_1000697c` | `0x00005043` | `engine_command` | side-effect command used when leaving e6100800 state family |
| `dispatch` | `DAT_100069a4` | `0x00006012` | `engine_command` | page/start command when no engine reset latch is active |
| `dispatch` | `DAT_100069a0` | `0x00003a13` | `engine_command` | page/start command when engine reset latch is active |

## Event Decisions

| Event | Source | Condition | Confidence |
|---:|---|---|---|
| `0x04800100` | `poll` | primary status command 1 passes all-ones check and has mask 0x4040 set | `medium` |
| `0xf6000300` | `poll` | command 0x20 response has mask 0x800 set | `medium` |
| `0xf6000400` | `poll` | command 0x20 response has bit 0x400 set while 0x800 is clear | `medium` |
| `0xe6100a01` | `poll` | nested command 2/0x16 status checks settle into normal-looking branch | `medium` |
| `0xe6100800` | `poll` | command 2 status 0x4000 branch, or substatus 0x16 plus 0x40 transition | `medium` |
| `0x20001607` | `poll` | command 2 response has any of mask 0x424 set | `medium` |
| `0xe6101100` | `preflight/poll` | preflight start event, or command 2 response has bit 0x1000 set | `medium` |
| `0xe6100e00` | `poll` | command 2 response has bit 0x2000 set | `medium` |
| `0x80000000` | `poll` | fallback when primary bit 0x40 is set and command 2 bit 0x200 is clear | `low` |
| `0xe6000d03` | `poll` | substatus command 0x16 bit 0x10 branch | `medium` |
| `0xe6000d06` | `poll` | substatus command 0x16 bit 0x08 branch | `medium` |
| `0xe6000d04` | `poll` | substatus command 0x16 bit 0x04 branch | `medium` |
| `0xe6100b0a` | `poll` | command 0x13 switch default for (status >> 1) & 0x3f | `medium` |
| `0xe6100b0b` | `poll` | command 0x13 switch cases 0x10, 0x14, 0x18 | `medium` |
| `0x14000a04` | `poll` | selected event low16 0x0a01 is rewritten before storage/send | `medium` |
| `0xfe001401` | `engine_io/preflight` | status I/O retries or preflight wait loop exhaust | `high` |

## State Fields

| Offset | Field | Meaning |
|---:|---|---|
| `+0x24` | preflight wait latch | breaks preflight wait loop when nonzero |
| `+0x28` | dispatch busy flag | set/cleared around engine dispatch cases |
| `+0x2c` | paper/engine latch candidate | used with primary status bit 0x2000 and bit 0x80 |
| `+0x30` | engine-needs-service flag candidate | set by normal/ready branch and reset-trigger branch |
| `+0x34` | previous primary 0x2e00 mask flag | tracks whether stored primary status had any 0x2e00 bits |
| `+0x38` | video reset / page transition latch | can trigger hp1020_video_reset_dispatch_candidate |
| `+0x3c` | deferred latch clear flag | cleared when primary status 0x2e00 mask clears |
| `+0x48` | active engine config pointer | points at preflight config or page mode config |
| `+0x4c` | secondary engine config pointer | paired pointer written by preflight |
| `+0x54` | preflight config scalar | zeroed during successful preflight |
| `+0x58` | preflight byte flag | set to 0xff during successful preflight |
| `+0x5a` | command latch | 16-bit command argument staged before register write |
| `+0x5c` | returned status value | 16-bit engine response returned by status IO helper |
| `+0x60` | selected event/status word | last event word emitted as engine queue message 0x17 |
| `+0x64` | primary status low16 | last primary command 1 status word |
| `+0x68` | active page work pointer | current page/job work pointer used by dispatch |
| `+0x6c` | deferred page work pointer | second pending work pointer if engine is busy |
| `base` | engine state object | state base pointer is 0x1002f0c4 |

## Command Sequences

### `engine_status_io_handshake`

- function: `0x10015c68 hp1020_engine_status_io_candidate`
- registers: `status=0xb050000c`, `command=0xb0500004`

1. stage the 16-bit command at engine state +0x5a
2. clear the status register with 0xfeffffff
3. wait for status register bit 0x00010000
4. write the staged command into the command register low 16 bits while preserving upper 16 bits
5. set command register bit 0x00010000, enable IRQ6, and wait for event mask0x1 with option3 (AND_CLEAR) and timeout200 ticks
6. on success, clear the command latch and return state+0x5c; four failed iterations (not necessarily four submissions) emit queue1 message0x17/event0xfe001401 and return0xffff

### `preflight_start`

- function: `0x100160a8 hp1020_engine_preflight_candidate`
- registers: `command=0xb0500004`

1. emit queue 1 message 0x17 with event 0xe6101100
2. OR bit 0x00020000 into the engine command register
3. poll for that bit to clear, sleeping 0x14 ticks between checks
4. after success, write config pointers at engine state +0x48/+0x4c and send message 0x18
5. after 0x1e failed loops or latch +0x24, emit timeout event 0xfe001401

### `print_dispatch_start_commands`

- function: `0x10016164 hp1020_engine_message_dispatch_candidate`
- registers: `command=0xb0500004`

1. message 0x0b/0x40 stores active page work pointer at engine state +0x68
2. if no reset latch is active, send engine command 0x6012
3. if reset latch is active, send engine command 0x3a13 and keep latch when returned status has 0x8000 clear

### `poll_transition_side_effects`

- function: `0x10015df8 hp1020_engine_status_poll_candidate`
- registers: `command=0xb0500004`

1. command 0x501a is sent from the substatus 0x16 branch
2. command 0x5043 is sent when the previous event family was e6100800 and the new event leaves that family
3. state +0x60 is updated with the selected event and queue 1 message 0x17 is emitted when it changes
4. primary status low16 is stored at state +0x64 after each successful poll

## Original reply interrupt and freshness boundary

`scripts/validate-hp1020-engine-handshake.py` executes29 original RAM cuts
in the interpreter and QEMU; its current source-bound result is
`engine-handshake-execution.json`. All peripheral access, IRQ changes,
scheduler/wait behavior and command publication are excluded.

Initialization at0x100164f0–f8 registers0x10015bc8 for IRQ6 through
0x1001716c. The handler reads0xb050000c separately at each decision:

1. It first writes a read-modify-write value clearing bit28.
2. With bit24 set, a second observation of bit27 decides acceptance.
   Bit27 set only clears that bit; no response is captured or event posted.
   Otherwise a third read supplies low16 to state+0x5c at0x10015c11,
   then0x10017dac receives `(state,1,0)` (event OR). The hidden third
   argument is zero from the earlier AND, not an omitted unknown value.
   Both paths then write a value clearing bit24.
3. Without bit24, bit26 selects another clear-only path.
4. Every path calls0x100171b0(6) then0x100171e0(6): disable IRQ6 and
   write its mask to INTCLEAR. Those CPU operations are statically read,
   never executed by this experiment.

These are values computed by the original code, not established register
acknowledgement semantics or meanings of the error bits. Successive reads
are independent observations; the test does not manufacture a snapshot.

The caller stages a16-bit command, checks ready bit16, preserves the command
register's upper16 bits, writes the command and sets bit16. Not-ready
iterations sleep1 tick; submitted iterations enable IRQ6 then wait200 ticks.
Both consume the same four-iteration budget. Tick duration is not established.

The event core0x10019408 tests requested flags and option3 clears mask0x1 on
success. The command helper does not clear a pending software event before
a new command, and the IRQ producer does not tag its response with a command
identity. Supplied old event-mask0x1/response RAM therefore survives a new command
latch and is accepted by the success tail in the isolated cuts. This is a
conditional freshness finding, not an observed printer fault: physical
command submission, interrupt timing and the blocking scheduler are absent.

The replacement need not copy ThreadX or these retries. It needs one serialized
transaction with a deadline and a justified post-timeout drain/reset boundary
before another command can accept an untagged response. An IRQ occurrence,
a changed USB generation or a nonzero cached word alone cannot establish
engine response freshness. Physical recovery and sensor calibration remain open.

## Evidence Checks

| Check | Status | Source | Needle |
|---|---|---|---|
| `io_stores_command_latch` | `present` | `analysis/dispatch-mmio/decompiled/10015c68_hp1020_engine_status_io_candidate.c` | `*(undefined2 *)(PTR_DAT_10006920 + 0x5a) = param_1` |
| `io_clears_status_register` | `present` | `analysis/dispatch-mmio/decompiled/10015c68_hp1020_engine_status_io_candidate.c` | `*puVar3 = *puVar3 & uVar5` |
| `io_waits_ready_submit_bit` | `present` | `analysis/dispatch-mmio/decompiled/10015c68_hp1020_engine_status_io_candidate.c` | `(*hp1020_engine_status_reg_table_word & uVar2) == 0` |
| `io_writes_command_low16` | `present` | `analysis/dispatch-mmio/decompiled/10015c68_hp1020_engine_status_io_candidate.c` | `*puVar6 = *puVar6 & uVar1 \| (uint)*(ushort *)(puVar4 + 0x5a)` |
| `io_sets_submit_bit` | `present` | `analysis/dispatch-mmio/decompiled/10015c68_hp1020_engine_status_io_candidate.c` | `*puVar6 = *puVar6 \| uVar2` |
| `io_timeout_emits_0x17` | `present` | `analysis/dispatch-mmio/decompiled/10015c68_hp1020_engine_status_io_candidate.c` | `hp1020_queue_send_candidate(1,&uStack_30)` |
| `poll_reads_primary_status_1` | `present` | `analysis/dispatch-mmio/decompiled/10015df8_hp1020_engine_status_poll_candidate.c` | `uVar4 = hp1020_engine_status_io_candidate(1)` |
| `poll_reads_status_0x20` | `present` | `analysis/dispatch-mmio/decompiled/10015df8_hp1020_engine_status_poll_candidate.c` | `uVar5 = hp1020_engine_status_io_candidate(0x20)` |
| `poll_reads_status_2` | `present` | `analysis/dispatch-mmio/decompiled/10015df8_hp1020_engine_status_poll_candidate.c` | `uVar5 = hp1020_engine_status_io_candidate(2)` |
| `poll_reads_substatus_0x16` | `present` | `analysis/dispatch-mmio/decompiled/10015df8_hp1020_engine_status_poll_candidate.c` | `uVar7 = hp1020_engine_status_io_candidate(0x16)` |
| `poll_reads_substatus_0x13` | `present` | `analysis/dispatch-mmio/decompiled/10015df8_hp1020_engine_status_poll_candidate.c` | `uVar9 = hp1020_engine_status_io_candidate(0x13)` |
| `poll_command_0x501a_side_effect` | `present` | `analysis/dispatch-mmio/decompiled/10015df8_hp1020_engine_status_poll_candidate.c` | `hp1020_engine_status_io_candidate(DAT_10006968)` |
| `poll_command_0x5043_side_effect` | `present` | `analysis/dispatch-mmio/decompiled/10015df8_hp1020_engine_status_poll_candidate.c` | `hp1020_engine_status_io_candidate(DAT_1000697c)` |
| `poll_stores_selected_event` | `present` | `analysis/dispatch-mmio/decompiled/10015df8_hp1020_engine_status_poll_candidate.c` | `*(uint *)(PTR_DAT_10006920 + 0x60) = uVar6` |
| `poll_stores_primary_low16` | `present` | `analysis/dispatch-mmio/decompiled/10015df8_hp1020_engine_status_poll_candidate.c` | `*(short *)(puVar2 + 100) = (short)uVar4` |
| `poll_can_reset_video` | `present` | `analysis/dispatch-mmio/decompiled/10015df8_hp1020_engine_status_poll_candidate.c` | `hp1020_video_reset_dispatch_candidate()` |
| `preflight_sets_start_bit` | `present` | `analysis/dispatch-mmio/decompiled/100160a8_hp1020_engine_preflight_candidate.c` | `*hp1020_engine_command_reg_table_word = *hp1020_engine_command_reg_table_word \| DAT_10005e74` |
| `preflight_timeout_event` | `present` | `analysis/dispatch-mmio/decompiled/100160a8_hp1020_engine_preflight_candidate.c` | `uStack_2c = DAT_1000692c` |
| `preflight_datastore_source_0x0f` | `present` | `analysis/dispatch-mmio/decompiled/100160a8_hp1020_engine_preflight_candidate.c` | `hp1020_datastore_get_value_candidate(0xf)` |
| `dispatch_command_0x6012` | `present` | `analysis/dispatch-mmio/decompiled/10016164_hp1020_engine_message_dispatch_candidate.c` | `hp1020_engine_status_io_candidate(DAT_100069a4)` |
| `dispatch_command_0x3a13` | `present` | `analysis/dispatch-mmio/decompiled/10016164_hp1020_engine_message_dispatch_candidate.c` | `uVar4 = hp1020_engine_status_io_candidate(DAT_100069a0)` |

## Open Firmware Meaning

- For printing, this is the critical non-USB hardware conversation: it gates page start, readiness, error state, and video reset.
- The model identifies the stock command IDs and event words, but it still does not name every physical condition such as exact paper, cover, fuser, toner, or jam bit.
- The next printer-side test should still be non-printing status/PJL calibration before any custom firmware tries to drive these commands.

