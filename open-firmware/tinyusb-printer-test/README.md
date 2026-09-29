# Reusable printer adapter experiment

**132 sanitized host and 132 QEMU scenarios pass** through the patched, pinned
TinyUSB core, reusable printer adapter and existing document/image components.
This fixture supplies synthetic controller completions, cancellation and reset
promises. It contains no controller implementation or physical USB operations.

Original submission cookies are retained by value. OUT shadows change only on
explicit fixture writes; IN buffers remain immutable until settlement. Decode
and output run outside TinyUSB callbacks. Exact pixels are compared with known
source images and the separate full JBIG decoder; every proposed control IN byte
has an independent wire oracle. Final receive/output storage and every portable
observation match the target. The target also audits all annotated instructions.

Automatic configuration recovery is separate from genuine wire class resets.
Both require all three supplied promises; automatic recovery creates no extra
packet/request. A separate 34-case continuous experiment checks normal validated
document boundaries without close/finish. Short packets and ZLPs never mean EOF.

`scripts/validate-hp1020-tinyusb-printer.py --target` runs sequentially. Reports
and preserved earlier source/captures: `analysis/usb-path/tinyusb-printer/`.
The adapter README owns integration obligations and limits.

## Fixture protocol

Host arguments: fill, OUT capacity, printer interface, output-failure threshold,
then pixel/wire/receive/output capture paths and an optional document-event path. Each stdin command is six big-endian
32-bit words: operation, a, b, c, d, following-byte count; then those bytes.
Initial state and each command return a JSON array of 96 observations. Target
calls use the same five command words and a separate input array. Reset requires
a fresh process or ELF load. Test memory and DCD state are isolated from devices.

| Operation | Meaning |
| --- | --- |
| 0 | SETUP: a byte length, b status-known, c status value |
| 1 | Service only protocol events |
| 2 | Complete original cookie a, result b, count c |
| 3 | Explicit DCD write: cookie a, byte count b, offset c |
| 4 | Settle cancellation of original cookie a |
| 5 | Admit bus reset at speed a |
| 6 / 7 | Arm one OUT / pump decoded document data |
| 8 / 9 | Close admission / finish explicitly closed input |
| 10 | Cache current reset ticket at slot a |
| 11 / 12 | Supply reset part b / finish ticket at slot a |
| 13 | Fault using saved bulk cookie a and reason b |
| 14 | Reject next submission before binding (1) or after binding (2) |
| 15 | Supply synthetic cleared bulk endpoint state after ownership settles |
| 16 | Change synchronous output-failure threshold |
| 17 | Change document-notification failure threshold |
| 18 | Before first input, seed parser/completion document counters together for saturation controls |

The fixture's old cookie ledger is separate from the adapter's current owners.
No late event is retagged using current state. Captures describe proposed packets
and consumed software pixels, including cancelled IN proposals; they are not USB
wire delivery or physical output evidence.

Words 90..95 expose attempted/accepted notifications, current output document
count, last event generation, callback failure threshold and last document ID.
The optional event file contains five big-endian words per attempt: original
receive generation, document ID, first encoded page, page count and callback
result. Attempts and successful observations are intentionally separate. These
are synchronous software observations, not physical job-completion messages.
