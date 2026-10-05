# Bounded bulk-IN descriptor

One reply packet passes from the TinyUSB adapter through a DCD callback into a
separate 64-byte staging allocation and one 16-byte big-endian descriptor.
The original source stays borrowed until the application collects the adapter's
result. Cancellation retains both allocations until explicit settlement.

The construction follows the bounded case in
`analysis/usb-path/in1-construction.json`: last|length, source address, next0.
The replacement initializes the reserved word to zero, supplies an explicit
mapping for its own staging buffer and never treats HP's numeric alias addition
as address translation. NULL/0 is an explicit replacement ZLP request; the stock
construction experiment does not establish stock queue ZLP transmission.

`take_submission` returns a RAM proposal after supplied mode and visibility
facts. It cannot publish a stale prepared packet after a transport fence, even
before the queued cancellation reaches this component. Register publication is
still missing. A copied proposal remains the external caller's responsibility.

Descriptor DMA_DONE and a transfer interrupt do not establish FIFO settlement or
host receipt. Completion requires separately supplied terminal memory access and
exact DMA count; descriptor low count bits are not used as actual length. Memory
may be reusable while FIFO retry bytes remain inside the controller. A future
publisher/reset path must establish FIFO capacity/drain separately. Malformed
descriptors and bad counts fault the original owner without clearing or reusing bytes.

Run `python3 scripts/validate-hp1020-udc-in.py --target`. Nine scenarios with two
memory fills pass sanitizers and audited big-endian QEMU execution through real
TinyUSB calls. They compare descriptor/staging bytes, guards and original results,
including publication refusal, late success, cancellation and reuse. The current
source-bound result is `analysis/usb-path/udc-in-validation.json`. No cache, IRQ,
physical USB, PJL command producer or printer output is established.
