# Bounded PJL commands in the input pipeline

This component takes over the document input pump and bulk-IN reply ownership.
It consumes actual completed OUT reservations, retains a ticket/cursor when
reply storage is busy, and sends ECHO/INFO STATUS through the real TinyUSB adapter. DCD
staging and recording-I/O publication remain separate, using the checked IN
components. No physical USB backend or entry-loop integration is supplied.

The first profile recognizes `@PJL ECHO ` followed by at most50 printable ASCII
bytes, with CR or LF termination. It preserves that line and replies with
CR/LF/form-feed. The maximum63-byte reply is a short USB packet, so this profile
does not need an automatic trailing ZLP. An oversized ECHO stops the stream
explicitly; it is never silently truncated. Exact uppercase `@PJL INFO STATUS`
uses an optional read-only provider for a coherent CODE/ONLINE observation tagged
with the current transport epoch and document generation. The provider must
establish freshness and physical meaning; this component cannot acquire sensors.
Unavailable, stale or invalid observations consume the query without replying,
so absent status cannot block pages or become a fabricated ready response.
CODE0..99999 and ONLINE0/1 are admitted; DISPLAY is empty. No START, PAGE, END
or unsolicited DEVICE notification is generated. Other PJL lines are ignored.

UEL and commands may split across receive packets. At an envelope line's start,
JZJZ enters the existing binary parser; inside ECHO text it remains text. Binary
header/payload spans are sized from that parser's current state and bypass the
command lexer completely. Valid pages/documents retain the existing decoder,
output consumer and original-generation notifications. A short OUT or ZLP
neither finishes a document nor discards a partial command.

With a cooperatively initialized document, each binary pump step returns to the
outer loop. A busy output ring retains the receive ticket and exact consumed-byte
cursor; pending decoder work is handled before reading more text or binary data.
The outer loop services control traffic and advances output acceptance/completion.
Reset retains the same receive, output and transport quiescence requirements.

Initialize a zeroed stationary instance once. After normal controller-gated
control service, call this pump instead of `hp1020_tusb_adapter_pump` or
`hp1020_usb_document_pump`. Keep their existing OUT admission, completion and
printer reset APIs. This component must be the only bulk-IN producer/result
consumer. It calls no controller hook itself and cannot grant a controller
readiness/reset promise. All calls and callbacks remain serialized; output and
document callbacks must not re-enter the pipeline or mutate its adapter.

Status is sampled only when reply storage becomes available, then copied to the
owned packet. Later provider changes cannot mutate that snapshot. Reset discards
partial text and unsent replies. A borrowed reply stays immutable
until its exact original result is collected, including after a failed DCD bind,
uncertain publication or late success. A second ECHO holds its receive cursor
until the first reply's storage is released. This memory release is not host
receipt; the IN publisher independently requires FIFO readiness for the next
packet. A refusal before DCD binding gets at most one attempt per pump call.

`hp1020_pjl_command_reap` collects a returned original reply without consuming
input, sampling status or sending anything. Recovery may call it when controller
failure gates prohibit pumping: otherwise the retained result could prevent the
very cleanup needed to reopen those gates. It does not cause completion or
release storage while a result remains absent.

Run `python3 scripts/validate-hp1020-pjl-command.py --target`. Host sanitizers and
audited BE QEMU execute the same real receive/adapter/staging/publication path.
Literal replies, descriptor bytes and register traces are checked independently.
Tests include one-byte fragments, text/binary separation, backpressure, reset
and publication failure recovery. The mixed case decodes two existing JBIG
fixtures to exact independent128-byte pixels between ECHOs; it is a synthetic
ZjStream document, not a new stock lifecycle or physical printing test.
Status tests compare actual staged bytes to executed original INFO replies in
`analysis/status-path/status-reply-execution.json`, including direct CODE0.
That original check supplies datastore values, locks, decimal formatting,
allocation and final callbacks; it is a byte-format oracle, not sensed status.
The open path intentionally accepts only positive bounded arithmetic and a
Boolean ONLINE. Original `%d` overflow and arbitrary nonzero ONLINE bytes are
outside this profile. The current result is
`analysis/usb-path/pjl-command-validation.json`.

`scripts/validate-hp1020-cooperative-usb.py --target` exercises cooperative mode
with full independent page pixels, control service during output pressure,
retained replies across reset, gated restart and late stream/consumer failures.
It uses the real software USB path with supplied controller observations; entry
integration and physical USB/engine operation remain absent.
