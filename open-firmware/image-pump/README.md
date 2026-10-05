# Cooperative page decoding

This composition reuses the semantic ZjStream parser, page planner, JBIG-KIT
decoder and four-slot output ring. A call consumes at most64 input bytes or
advances one decoder step. Output pressure returns immediately with the decoded
band, compressed tail and outstanding slots retained. The outer loop can service
control/status/cancellation between calls; this component performs no I/O.

Initialize zeroed state and stationary memory once. Call `feed`, honor `used`,
and advance the ring through peek/accept/actual-complete. Ordinary EMPTY/BLOCKED
ring results require no action. MORE permits another bounded step; a pending
chunk can advance without more input. PAGE and DOCUMENT events remain until
acknowledged. Explicit `finish` checks true end-of-input, never a USB short packet.
`stop` fences work without discarding ownership or claiming cancellation.
After successful finish, feed/finish return DONE without consuming anything.
Reinitialization requires separately settling or abandoning all old ownership.

This is a successor to the synchronous output composition, not yet attached to
the USB command pump or entry loop. Its profile remains aligned, single-plane
600dpi BPP1/2 pages admitted by the existing planner. Copies are metadata. Software
PAGE/DOCUMENT events do not mean physical printing or engine completion.

`python3 scripts/validate-hp1020-image-pump.py --target` compares full pixels with
the independent full JBIG decoder and deterministic source, using sanitized host
execution and the compiled Xtensa path in QEMU RAM. It covers held output and
events, distinct acceptance/completion, poisoned input storage, stop, late errors
and successive documents. Exact tested sources are recorded in
`analysis/open-firmware-model/image-core/pump-validation.json`.
