# Bounded open image decoder

This experimental, hardware-free component decodes the narrow foo2zjs JBIG
profile into consecutive packed image rows. It uses the GPL-2.0-or-later
JBIG-KIT 2.1 streaming implementation, with provenance, license and a small
local undefined-behavior patch in `vendor/jbigkit-2.1/`.
It does not print or drive any device. A separate `hp1020_image_page` bridge
connects the existing semantic parser and planner to this decoder. Stock
raw-buffer queue, engine, cache and USB integration remain separate work.

`hp1020_image_ring.c` now adds bounded software output ownership, independently
of the original firmware's structure layout. The compiled RAM fixture connects
the decoder directly to this ring; no host pixel copy bridges these components.
Acceptance/completion come from an explicit software consumer, not an engine.

## Contract

`hp1020_image.h` defines a caller-owned state, two-row history buffer and one
output band. There is no allocator and no retained page bitmap. Input buffers
can be reused as soon as `feed` returns. A4 default data uses 1200 bytes per row;
four output rows and two history rows occupy 7200 bytes, in addition to the
decoder state and stack. The target test report records the actual 32-bit
state size. Test-only arrays and host reference images are not component RAM.

1. Initialize with the original 20-byte BIH, separate history/output buffers
   and an explicit positive band-row limit.
2. Feed concatenated BID payloads. Honor the consumed-byte count and retain or
   resubmit the remainder. ZjStream chunk headers never enter this API.
3. On `BAND`, consume `band_rows * stride` bytes from `band`, starting at
   `band_first`; then release the band. Feeding while paused consumes zero
   bytes and preserves the pending band. A final partial band is supported.
4. Signal end of input with `finish`, releasing any pending bands until `DONE`
   or an error. Released image rows are provisional until successful completion.
   The format contains no checksum; a corrupted stream can decode successfully
   into different pixels. This is not a corruption-detection guarantee.

Errors are sticky until reinitialization. The state and all buffers must be
valid, nonoverlapping and stationary. Output is packed most-significant-bit
first, with `ceil(BIH.XD/8)` bytes per row. The component does not scale, invert,
repack host BPP2 samples, add engine padding or assert a physical pixel format.

## Deliberately narrow input

The accepted BIH has `DL=D=0`, one plane, zero reserved byte, `MX=16`, `MY=0`,
order `3`, and options `0x5c`. Width, height and stripe height must be positive,
bounded by 16384; output bands are capped at 8192 bytes. BPP4 sample width exceeds
this component's limit. A logical-clip sample can decode, but the existing page
planner still rejects its inconsistent stock metadata; decoding is not planning.

Only a private BIH copy changes: order becomes 0 and options become `0x48`.
In the original full `vendor/foo2zjs-source/jbig.c`, base-layer decoding at
`if (layer == 0)` uses TPBON/LRLTWO; TPDON and DPON are used in the differential
branch. There are no differential layers or competing planes in this profile.
The differential tests compare original and normalized headers using the full
decoder, then compare streaming output with every original output byte and
generated source pixels. Private tables, variable height and other profiles
are rejected, not normalized speculatively.

The core stops at the BIE end and returns the unconsumed tail to the caller.
The existing foo2zjs `write_plane` adds its configured extra padding plus
four-byte alignment to the last BID. Saved fixtures have 16–19 zero bytes.
The decoder does not silently accept, discard or validate transport padding.

## Reproduce

```sh
python3 scripts/validate-hp1020-image-core.py --target
python3 scripts/validate-hp1020-image-pages.py --target
python3 scripts/validate-hp1020-image-stream.py --target
```

This runs sanitized host comparisons, builds the target twice with the pinned
BE/call0 compiler/profile gate, audits actual instruction regions, and executes
the result in isolated QEMU RAM. A small nonblank image also runs in the strict
independent instruction interpreter. Small target images compare every output
byte; larger pages compare the first 65536 bytes plus the full FNV-1a and row/
band counts. Host comparisons cover every output byte even on the large pages.
No timing result is treated as printer throughput.

Reports and compact encoded pixel fixtures are generated under
`analysis/open-firmware-model/image-core/`. Host-only mode writes its separate
`host-validation` report; it cannot replace the target report. Source and fixture
hashes record the tested files. The preserved upstream-pointer finding is a
historical failing case, not a validated version of the current implementation.

The synthetic ELF retains unused streaming-encoder functions so that old
binutils retains its instruction annotations. Prefer `annotated-disassembly.txt`
over linear decoding of literal pools. A known libgcc divide-by-zero trap is
identified separately; image geometry rejects zero divisors before division.
The target is a RAM fixture with test arrays, not an uploadable firmware image.

## Software output ring

The ring accepts aligned image widths and uses the recovered callback-disabled
slot capacity `(8192 / stride) & ~3` rows. Supply four nonoverlapping output slots
and configure the decoder with that row capacity. A4-width input uses four
4800-byte slots. This is a single-context API; it does not provide locks, IRQ
handling, cache maintenance, original pool allocation or physical output.

- Push one full decoder band, or the final shorter band, in row order. A full
  ring returns `BLOCKED` without copying or changing ownership. Retain the
  pending decoder band and retry; release it only after a successful copy.
- Peek exposes a published slot, preserving the original one-slot delay for
  the newest nonfinal band. Accept records output submission but keeps storage
  owned. Complete releases it later, in order. Acceptance alone never permits
  producer reuse. Mutating API errors are sticky; views are read-only.
- Drained means all image rows have been consumed by this software fixture.
  Require successful decoder/framing completion separately. Previously emitted
  rows remain provisional on a late decode error. Reinitialization discards
  ownership and therefore requires the caller to drain or abandon the old image.

`python3 scripts/validate-hp1020-image-ring.py --target` runs 36 sanitized host
cases and the same 36 in QEMU, with 11 API-rejection controls per engine. Every
pixel and every output-storage byte is compared, including unused space and
the previous contents of reused partial slots. Six 17-row cases match the
original bounded ring ownership trace exactly. A 132-row image cycles through
33 bands with 29 full-ring pauses. Input fragments are poisoned after use.
The simulated consumer checks that an accepted but uncompleted slot still
blocks reuse, while the pending decoder band survives the pause.

The measured 32-bit target state and minimum buffers use **30824 bytes** for
A4-width input: 4312 bytes of decoder state, 112 bytes of ring state, two history
rows, one decoder band and four output slots. This excludes code, stack, caller
input and test captures. It is not the RAM budget of a complete printer firmware.
Reports are `analysis/open-firmware-model/image-core/ring-validation.json/.md`;
host-only runs write separate reports. Odd-row image controls do not broaden the
stricter ZjStream page planner's accepted grammar. Full stream/owner integration,
native scheduling, page cleanup and physical packing remain separate questions.

## Complete-file bridge

The semantic parser retains each exact BIH alongside its existing fields.
`hp1020_image_page_init` accepts only a successful finalized parse, valid raster
spans and a page accepted by the existing narrow planner. It requires 32-bit
aligned image widths so packed decoder rows match the planner's stride. The
bridge uses the planner's row/storage geometry; it never invokes the conditional
callback or interprets its window as proven engine output.

Call `hp1020_image_page_next` with a positive feed quantum, consume each returned
band, and release it. BID boundaries can split compressed bytes or padding.
Completion also requires the exact default foo2zjs padding formula:
16 zero bytes plus alignment to four bytes after the compressed payload.
Other `foo2zjs -X` settings are outside this bridge's profile. It decodes each
page once and retains copies as metadata, without replaying an output engine.

The complete-file path still holds compressed input in the semantic parser's
caller-owned arena. It therefore does not claim an entire print pipeline in
the decoder's roughly 12 KB of state/history/band storage. Differing page BIHs,
multiple documents, fragmented input and 6/13/64 BID partitions are checked in
`page-validation`; those software pages are not added to native lifecycle counts.

## Bounded complete-stream bridge

`hp1020_image_stream` uses the semantic parser's optional synchronous chunk
consumer. A fixed 65552-byte compressed buffer covers foo2zjs's largest default
final BID: 65536 compressed bytes plus padding. History uses 4096 bytes and the
output band uses 8192 bytes, sized for the supported maximum width. The stream
state contains the parser, decoder and plan; the target report measures it
separately. Component storage never grows with the compressed or decoded page.
The caller's input packet, stack, code and test capture are outside that total.

Initialize with stationary caller-owned state/memory and a band consumer; then
feed packet fragments and finish the stream. The callback consumes/copies each
band before returning success. Only then is that band released. A consumer
error aborts without releasing its pending band. There is no scheduler, retry
or asynchronous queue protocol here. Reinitialization starts a fresh stream.
All emitted output remains provisional until finish succeeds; missing END_DOC
and late padding errors can follow valid image bands.

Planning happens when BIH arrives, using a local metadata copy marked complete
for geometry admission. The actual parser page remains incomplete until
END_PAGE. The same narrow planner, aligned widths, coding profile and exact
default padding apply. Up to 16 page metadata records remain in the parser.
Copies are metadata, without compressed replay or physical output scheduling.

`stream-validation` compares every host image byte against the original full
decoder and deterministic source pixels. Target calls feed bounded packets into
persistent synthetic RAM; complete large inputs never occupy a target array.
The fixture poisons both caller packets and consumed compressed chunks to test
reuse, checks band order and guards, and verifies the raster-record array stays
empty. Separate controls show that 129/257 BID partitions still hit the default
retained parser's 128-record limit while streaming consumes the same bytes.
These are open software cases, not original stock lifecycles or printer tests.

## Bounded document output

`hp1020_image_output` composes the bounded stream parser/decoder and the
four-slot software ring in ordinary compiled C. Input is copied only into the
fixed compressed chunk, and each decoded band is copied into an available
output slot before the decoder can reuse it. The caller supplies a synchronous
progress callback operating through ring peek/accept/complete. It must wait for
real progress or return an error; returning success without progress is an
error. No scheduler, transfer submission or hardware completion is invented.

The previous page drains with its original geometry before the ring is reused
for a differently sized page, even when the next page's decoder has already
produced a pending band. Final success requires valid end-of-document framing,
successful image decoding and completion of all published rows. A late syntax
error or consumer failure retains outstanding ownership and cannot turn into
successful completion. Previously consumed pixels cannot be retracted. Before
reinitializing after an error, the caller must quiesce any external consumer and
explicitly abandon or finish old transfers; resetting C state is not cancellation.
Copies are passed to the consumer as plan metadata and are not replayed here.

`python3 scripts/validate-hp1020-image-output.py --target` passes 39 sanitized
host and 39 QEMU cases. The explicit consumer uses three acceptance/completion
orders, including several outstanding slots. Full pixels and all 32768 bytes
of output storage are compared across changing sizes, consecutive documents,
257 compressed fragments, final partial slots, late input errors and consumer
failures. Input packets and consumed compressed chunks are poisoned after use.
An accepted slot's bytes are checked again at its separate completion.

The component's target state and fixed memory total **123968 bytes**, excluding
code, stack, caller packets and fixture captures. There is no full-page buffer.
Reports are `analysis/open-firmware-model/image-core/output-validation.json/.md`.
The shared target ELF remains synthetic RAM, never an uploadable image. The
16-page metadata bound still applies at this checkpoint and is the next useful
restriction to remove from streaming mode. No physical output, firmware copy
handling, cancellation/recovery or native page lifecycle is established.
