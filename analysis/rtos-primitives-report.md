# HP 1020 RTOS Primitive Map

This pass labels the runtime layer beneath the printer-specific task code.

## Main Result

The firmware carries a recognizable RTOS-style object model. Several object type checks use ASCII magic values:

| Address | Value | Meaning |
|---:|---|---|
| `0x100065bc` | `SEMA` | semaphore object signature |
| `0x100065d0` | `MUTE` | mutex object signature |
| `0x100065e8` | `QUEU` | queue object signature |
| `0x10006b0c` | `BLOC` | block pool / block object signature |
| `0x10006b10` | `BYTE` | byte pool object signature |
| `0x10006b14` | `THRD` | thread object signature |

That makes the firmware's queue/task behavior much more grounded: these are not arbitrary HP structures, they are RTOS objects with validation headers.

## System Interface Table Slots

Known useful `.sys_interface_table` slots:

| Index | Wrapper | Lower routine | Working name |
|---:|---:|---:|---|
| `22` | `0x1001809c` | `0x10019eb4` | queue receive |
| `23` | `0x100180dc` | `0x1001a130` | queue send |
| `28` | `0x100181a4` | `0x1001a478` | memory/block service |
| `46` | `0x1001766c` | `0x1001a590`, `0x100176c8` | sleep / timed suspend |
| `59` | `0x100131b8` | `0x100181a4`, `0x10018214` | allocator / runtime memory service |
| `62` | `0x10010f54` | data-store helpers | indexed data-store read/lock candidate |
| `63` | `0x10010fd0` | data-store helpers | indexed data-store write/notify/unlock candidate |

## Queue Receive

Wrapper:

- `0x1001809c` `threadx_queue_receive_wait_candidate`

Validation behavior:

- rejects null queue object
- checks object signature against `QUEU`
- rejects null destination pointer
- rejects blocking waits from interrupt/system contexts
- calls lower routine `0x10019eb4`

Lower routine:

- `0x10019eb4` `threadx_queue_receive_core_candidate`

Observed behavior:

- if queue empty and wait requested, suspends current thread on queue wait list
- copies queued message words into destination
- advances ring buffer read pointer
- if senders are waiting, moves one sender's message into the queue and wakes that thread
- returns ThreadX-style numeric status codes

## Queue Send

Wrapper:

- `0x100180dc` `threadx_queue_send_candidate`

Validation behavior:

- rejects null queue object
- checks object signature against `QUEU`
- rejects null source pointer
- rejects blocking waits from interrupt/system contexts
- calls lower routine `0x1001a130`

Lower routine:

- `0x1001a130` `threadx_queue_send_core_candidate`

Observed behavior:

- if no queue space and wait requested, suspends current thread on queue wait list
- if a receiver is waiting, copies message directly into receiver destination and wakes receiver
- otherwise copies message words into queue ring buffer
- updates queue counts and ring write pointer

## Sleep / Timed Suspend

Wrapper:

- `0x1001766c` `threadx_sleep_candidate`

Observed behavior:

- only allows sleep from normal thread context
- marks current thread state as sleep/timed wait
- sets timeout counter at thread offset `0x4c`
- inserts timer record through `0x1001a590`
- calls scheduler helper `0x100176c8`

Timer insertion:

- `0x1001a590` `rtos_timer_insert_candidate`

Observed behavior:

- maps timeout values into timer buckets
- links timer records into bucket lists
- stores a back-pointer to the owning bucket

## Thread Ready / Scheduler Helpers

Ready insertion:

- `0x1001aac0` `rtos_thread_ready_insert_candidate`

Observed behavior:

- moves a thread into ready state
- inserts it into a priority-indexed ready list
- updates ready bitmaps/current best priority
- returns whether the scheduler should switch threads

Context / scheduler paths:

- `0x1001861c` saves low-level CPU context and enters interrupt dispatch on first entry
- `0x100187e0` is a scheduler/return path candidate
- `0x100188f0` restores a thread context and uses `rfe()`
- `0x1001788c` is the system timer thread

## Why This Matters

For reverse engineering, this is useful because it separates generic RTOS behavior from printer-specific behavior.

For a custom firmware prototype, it suggests two possible strategies:

1. Preserve the existing RTOS-like object layout and build after the scheduler starts.
2. Build a smaller firmware that imitates enough of the expected vector/interface table shape to boot, but does not reuse the full RTOS object model.

The first strategy is easier to reason about from this firmware but depends on reusing/replicating more structure. The second is cleaner long-term but requires proving the boot ROM only needs ELF/section/vector shape and not HP-specific runtime table semantics.

## Next Useful Step

The next pass should map task creation and queue creation:

- find where `QUEU` object headers are initialized
- find where `THRD` object headers are initialized
- connect those creation calls to the descriptor blocks for `USB2Thread`, `PrintMgrQueue`, `Job Mgr Queue`, `Video Queue`, `engMsgQ`, and `StatusMgrQueue`
- resolve queue `8` from creation/registration rather than inference
