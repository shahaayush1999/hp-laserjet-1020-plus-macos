# One-packet IN1 publication

This extends the real TinyUSB/`udc-in` path with injected logical register and
visibility hooks. There is no physical backend. Call after DCD preparation, in
one serialized event loop, with the exact original cookie. It supports a single
0..64-byte normal BE descriptor. The application still collects the adapter's
result; publication does not manufacture one.

Original bytes `0x10008b41..0x10008b75` store the descriptor at UDC+0x34,
unmask bit1 at+0x418 and set Poll Demand at+0x20, with MEMW ordering. The pinned
Linux `amd5536udc.h`/`snps_udc_core.c` provide the matching family register names
and next-request path. Our configured endpoint begins NAKed. This implementation
adds the necessary safe CNAK command/readback before POLL and never replays the
read-only NAK bit or unrelated command bits.

The family [Sony manual](https://www.sony-semicon.com/files/62/pdf/p-28_CXD5602_user_manual.pdf)
pages1153–1154 and1222 describe CNAK's RX-empty condition, POLL before/after IN
tokens, and DMA reaching the FIFO before a later host transfer. The exact pinned
PDF hash is in `analysis/usb-path/controller-reference/manuals/README.md`.
Do not import its newer XFERDONE_TXEMPTY bit into HP: it is unproved here. Instead
the caller must independently supply TX idle/empty (including a previous short
packet's boundary), the safe CNAK interval and stable controller binding. A DMA
completion alone cannot supply those facts. This component acknowledges no IRQ.

Nonmutating preflight accepts packet64/BE with transmit DMA enabled, either state
of receive DMA, bulk IN with POLL clear, MPS64 and at least16 allocated FIFO words.
`ready` must check the existing programming/ingress/OUT-publisher gates and the
actual allocation; a mounted TinyUSB device alone is insufficient. Visibility
hooks cover the full owned64-byte staging and16-byte descriptor allocations.
Mapping/cache and register leases must remain valid across the whole operation.

Once cache work starts, any hook failure poisons this attempt and requests
ordinary cancellation. Even an uncertain POLL write is never retried. The exact
old-cookie owner and buffers survive until supplied settlement; clearing the
local failure additionally requires completed physical endpoint cleanup and
drained DCD/callback/result ownership. Other reset/programming failures stay
independent. The integration must gate all new programming/publication on this
failure state; this narrow component is not yet installed into the entry loop.

Run `python3 scripts/validate-hp1020-udc-in-publish.py --target`. Its independent
literal read/write trace covers NAKed/clear endpoints, simultaneous receive DMA,
short/full/ZLP packets, every mutating failure prefix, stale/reset identities,
cleanup/reuse and the gap between source release and FIFO readiness. Reads are
supplied independently; recorded writes never update them. Current results go to
`analysis/usb-path/udc-in-publish-validation.json` without per-run archives.
