# Evidence required beyond the offline checkpoint

The offline work now has a byte-verified BE toolchain, corrected direct work
construction, instruction-tested framing and endpoint-0 staging, a bounded C
semantic parser, a page/band planner, and execution of the actual compiled C
components in synthetic RAM. The remaining live questions concern device behavior or
core-specific operations absent from the available instruction definitions.

## Functional replacement and reuse (2026-09-29)

The owner explicitly prioritizes a working printer over reproducing HP's
implementation. The replacement may use a different runtime, buffer layout and
task structure. Original-code lifecycles and ownership traces remain useful
evidence about dependencies and hardware-facing behavior, not a specification
requiring us to clone every internal step or reproduce original bugs.

The intended approach resembles hardware enablement for an existing operating
system: reuse portable code and implement the device-specific boundary. This
does not imply installing Linux on the printer. Choose the smallest useful
runtime after assessing its porting cost; a simple event loop remains an option.

Primary-source review identified these concrete reuse boundaries:

| Component | What it supplies | Status and remaining work |
|---|---|---|
| [foo2zjs](https://github.com/OpenPrinting/foo2zjs/blob/main-fixes/INSTALL.in) | Host-side page preparation and ZjStream generation | Already used by the separate Mac driver. Upstream still loads HP firmware for the 1020; it is not a replacement for the code inside the device. Keep the installed setup intact. |
| [JBIG-KIT](https://www.cl.cam.ac.uk/~mgk25/jbigkit/) | Portable image decompression, including the bounded streaming variant | Already retained and used by `open-firmware/image-core/`, with provenance, a local patch and executed host/target comparisons. Continue using this path instead of recovering the custom compressed-image accelerator unless evidence requires it. |
| [Eclipse ThreadX](https://github.com/eclipse-threadx/threadx) | An open embedded OS with queues, timers and scheduling | Candidate, not selected or tested here. Its [Xtensa port](https://github.com/eclipse-threadx/threadx/blob/master/ports/xtensa/xcc/readme_threadx.txt) describes Call0 support but requires Xtensa Tools/HAL and suitable exception/timer configuration. Its [support table](https://threadx.io/releases/6.5.1/home/main/hardware-support.html) lists XCC. This does not establish compatibility with our pinned GCC toolchain or the HP core. Assess that gap before importing a runtime. |
| [TinyUSB](https://docs.tinyusb.org/en/latest/porting.html) | Portable USB protocol handling above a controller driver | Candidate, not selected or tested here. Its documented port interface still requires board startup, endpoint setup and interrupt/transfer handling. Compare those requirements with the recovered USB controller contract; no compatible HP1020 controller port was established in this review. |

The review did not identify a ready-made open firmware replacement for this
printer. This is a scoped search result, not proof that none exists. Host driver
frameworks such as [PAPPL](https://openprinting.github.io/documentation/02-designing-printer-drivers)
can reuse printing services but do not by themselves supply this printer's
internal engine-control implementation. None of the candidate dependencies was
downloaded, installed, integrated or executed during this documentation review.

The hardware-specific work remains boot/memory/interrupt setup, USB transfers,
pixel packing and output transfer/ownership/cache behavior, plus the engine's
page-start, status, completion, timeout and recovery contract. Determine what the
existing engine controller handles before assuming our firmware must directly
regulate individual mechanisms. Generic library APIs do not establish timing,
physical status meanings or safe command ordering on this hardware.

Continue connecting the bounded ZjStream consumer to the independent C output
ring, including page/document transitions: that produces directly reusable code.
Before further stock scheduler/owner reconstruction, identify the unresolved
hardware-facing or external behavior it would settle. Assess reusable USB/runtime
code against those contracts before implementing more generic infrastructure;
do not turn porting an unnecessary OS into a new prerequisite. Preserve existing
reports and regression coverage. All hardware restrictions remain in force.

## Remaining hardware evidence

| Priority | Exact question | Existing evidence | Evidence that would resolve it |
|---|---|---|---|
| 1 | Does the corrected BE probe execute after the ROM loader, and can its own endpoint-0 path return its counter descriptor? | Stock-byte instruction fixtures and offline staging tests pass. The older quiet idle upload used incorrect instruction encoding. | A newly authorized cold-boot inert-probe test that returns the probe-specific descriptor. Stock USB identity alone is insufficient. |
| 2 | Does bulk OUT completion report the actual byte count and permit repeated acknowledgement/re-arm? | Static stock lane/descriptor/callback chain and offline framing tests. | The guarded 36-byte START_DOC/END_DOC transaction returns B=0x24, D=1, C=2, E=0, U=0; a later separately authorized repeat establishes re-arm. No page/raster input is needed. |
| 3 | Can the stock-supported callback bypass produce acceptable output? | File-backed datastore 32 = 1 disables the gate in original prepare execution; a separate original band fragment selects the raw slot buffer. Conditional zero-setting controls stop before the custom call. See the raster-bypass section below. | Establish the live configuration and buffer format/production/consumption contract, then eventual measured output. Recover the custom ISA only if the bypass proves insufficient. No custom opcode is assumed safe. |
| 4 | Do the two video channels implement the inferred compressed-input and row-output handshake, including length/progress units, cache visibility and descriptor ownership? | Original parser/JobMgr execution verifies BIH/BID lists and scheduling; direct VIDEO_Y seed, corrected floor division, bounded host partitions and static channel writes. | A stock first-page trace showing channel lengths/status, buffer contents, ownership transitions and completion order. No custom video writes are authorized. |
| 5 | Which physical engine conditions correspond to the polled status bits/events, and what are safe timing, timeout and recovery boundaries for startup, page start and completion? | Executable status/IRQ decision models and ordered stock command sequences. | Calibrated stock behavior for idle, page acceptance, completion and relevant fault states. Numeric event values are not physical labels. |

The logical-clip metadata mismatch and BPP4 zero-refill case are already isolated
and rejected by the narrow page planner; they are not reasons to expand the
first hardware test. Other modes, malformed-input compatibility and optimization
are outside this first printing scope.

## Open software image path (2026-09-10)

A second concrete shortcut now avoids the compressed-image hardware for offline
image production. `open-firmware/image-core/` contains a bounded streaming JBIG
wrapper and a bridge from the existing semantic parser/planner to packed row
bands. The parser now retains each exact 20-byte BIH. Current focused checks
pass, and the full sequential aggregate for that checkpoint passed **105 consistency checks**
in `/tmp/hp1020-full-image-ring-20260928.log` (child logs `hp1020-validation.WTCBMK`), including
the bounded complete-stream, raw-contract, original producer, parser/handoff and
video-buffer initialization, original ring delivery and the direct compiled
decoder/output-ring integrations below. All
tested source/fixture hashes match. No validation process remains running at this
checkpoint. Later drafts are separate from this executed result.

- `validate-hp1020-image-core.py --target`: 176 cases, 21 comparisons of original
  versus normalized headers through the original full decoder, 32 separately
  classified mutations, 66 QEMU cases and a small nonblank page through the
  independent instruction interpreter. This is decoded software image output,
  not a stock native page lifecycle or physical output.
- `validate-hp1020-image-pages.py --target`: 57 complete-file host cases, of which
  39 accept the file and 18 reject an invalid/unsupported condition; 35 QEMU
  cases. Tests include differently sized images across pages/documents, input
  fragments, 6/13/64 BID partitions, exact retained BIHs, stalled consumers,
  invalid raster spans/owners and default foo2zjs padding. The host compares
  every output byte. Large QEMU outputs compare the first 65536 bytes plus the
  complete FNV-1a, row/band and metadata counts; small outputs compare every byte.
- The private BIH copy changes only order `3 -> 0` and options `0x5c -> 0x48`,
  after requiring DL=D=0, P=1, zero reserved, MX=16 and MY=0. Original full
  `jbig.c` uses TPBON/LRLTWO in the base-layer branch; TPDON/DPON belong to the
  absent differential layer. Source pixels, original full decoding, normalized
  full decoding and streaming output agree on nonblank/noise/edge fixtures.
  Other profiles are rejected, not generalized from this result.
- The A4 decoder state is 4312 bytes on the emulated 32-bit target; history and
  four-row output band use another 7200 bytes. Total **11512 bytes** excludes
  code, stack, caller input and test arrays. The complete-file bridge retains
  compressed input in the existing arena, so this is not whole-pipeline RAM.
- The core returns the unconsumed BIE tail to its caller. The page bridge checks
  exactly 16 zero bytes plus four-byte alignment, matching default ExtraPad=16
  and `write_plane` in original foo2zjs. Other -X settings are outside its scope.
  Copies remain metadata: each page image is decoded once, without engine replay.
- The streaming JBIG-KIT 2.1 subset is retained with GPL notices, archive/file
  content pins and a complete local patch. Host UBSan reproduced invalid
  absent-history pointer construction in upstream `jbig85.c`. The patch keeps
  unused row pointers inside the buffer and assembles byte fields unsigned for
  32-bit targets. The original failing capture and matching harness snapshots
  remain separate under `image-core/source-snapshots/upstream-pointer/`.
- The synthetic target ELF retains instruction annotations and unused encoder
  code. The validator audits positive `.xt.prop` instruction regions, excluding
  literal pools from instruction decoding. The single libgcc divide-by-zero
  trap is identified separately. No custom ISA, MMIO, peripheral, USB or engine
  function is part of the open execution path.

Whole-page compressed retention is removed through an optional chunk consumer
in the existing parser, keeping retained mode and grammar intact. A fixed
compressed-chunk buffer plus bounded decoder/output storage handles detailed
images larger than the test input buffer. The synchronous chunk consumer,
`hp1020_image_stream.c` and incremental fixture now pass **66 host and 44 QEMU
cases** after the streaming metadata-reuse change detailed below, owned by
`validate-hp1020-image-stream.py` and `image-core/stream-validation.json/.md`.
The initial streaming aggregate passed in `/tmp/hp1020-full-stream.log`
(child logs `hp1020-validation.0D3y3e`), with 97 consistency checks and both suites passing.
The later raw-contract aggregate above passes 98 with the same open C sources.

- A deterministic 9856x8208 detailed/noise page has 10,112,256 decoded bytes,
  10,546,072 BIE bytes and 161 BID chunks. Host output equals every generated
  source pixel and original full-decoder byte. Two target cases use bounded
  packets with input fragments 7/65552, both fills, a complete FNV-1a/count check
  and the first 65536 output bytes. Large files exist only in temporary host
  storage; generator seed, dimensions and exact content hashes are preserved.
- Target state 13,188 bytes plus fixed compressed/history/band memory 77,840
  bytes totals **91,028 bytes**, excluding code/stack/caller packets/test capture.
  The 65552-byte BID limit covers the original foo2zjs default final chunk.
  A standard COMMENT marker tests that exact maximum, and 65553 is rejected.
- The fixture poisons caller packets after feed and consumed BID storage after
  callback return. The compressed arena is empty after success, and no raster
  records are kept. 129/257 BID partitions pass while default retained-mode
  controls reject at 128. The retained image bridge rejects streaming state.
- Multiple documents/images, 16/17/65 pages, exact BIHs, padding errors,
  truncation and consumer failures are checked. A consumer failure leaves the
  pending band unreleased and errors sticky; it is not a retry mechanism.
  Output is provisional until finish, and copies stay metadata. Streaming now
  reuses the current page record; retained inspection still caps metadata at 16.
  The callback is synchronous, without a scheduler or
  asynchronous stock queue integration. Software image cases remain separate
  from native lifecycle, physical format and printing evidence.

Then pursue the raw-output contract: establish whether these exact
packed rows can occupy stock raw slots or linked-list buffers, and which
software ownership/count/terminal fields are required before any hardware
boundary. The bridge currently requires 32-bit aligned widths and existing
narrow page-plan admission. BPP1/2 metadata does not prove physical pixel order
or an engine-ready packing format; callback/window projections remain conditional.
Do not start recovering the custom image ISA merely because it is unknown: the
stock-supported callback bypass plus software image output is now an implemented
offline alternative. Actual printer throughput, cache visibility, boot, live
configuration, engine sequencing and observed printing are still unresolved.

### Raw-route preconditions: byte audit and bounded execution

Original-byte inspection identifies **independent selectors** that must agree
in a future raw-output integration. The bounded RAM fragments below now execute
those selections, while every peripheral-output operation remains excluded.

1. VideoThread loads the first raster payload through `work+0x50 -> node+0x0c`,
   then reads **payload+0x50** at `0x10013c8d` (`288214`). Zero dispatches prepare
   then compressed render `0x10015214`; 1 or 2 dispatches prepare then alternate
   render `0x10015438`. Other values skip both render calls. Work type 7 also
   skips rendering. This is not selected by work+0x74 at this dispatch point.
2. Prepare separately reads **work+0x74** at `0x10014b92` (`284074`) and sets or
   clears video+0xfc's high bit. That chooses the later IRQ/refill family. Merely
   toggling work+0x74 does not select alternate render; conversely source-kind
   1/2 alone does not establish the matching raw IRQ mode.
3. Alternate render `0x10015438` copies `work+0x50` to both video+0x9c and +0xa0,
   then calls raw refresh at `0x10015450`. The refresh's first peripheral read
   is `0x10014126`, after logging; it cannot be run wholesale as a RAM fragment.
4. Raw refresh reads payload+0x54 as the pointer, +0x20 as a 16-bit unit count,
   +0x4c as a terminal flag, and +0x50 again. **Source kind 2 contributes bit 25
   to the hardware count/flag word**, in addition to changing the known release
   policy. It must not be chosen just to avoid freeing a borrowed buffer.
5. The separate engine-derived output selector at `0x1001cdac` still chooses
   single versus dual output handling. On its value-1 branch, B's pointer is
   A+video+0xbc and the count uses half the payload units before dividing by
   video+0xc4. Neither physical lane meaning nor required pixel/row interleave
   is established by this arithmetic.

Byte audit anchors (exclusive ends; original stock ELF SHA-256 ranges):

| Range | SHA-256 |
|---|---|
| `0x10013c7d..0x10013cc4` dispatch | `b545933c73cc711d6fdea6e8c8d20c1401680e0caafd9a40cf12084b8042845d` |
| `0x10015438..0x10015458` alternate render | `16bf6cec843b78f2b0eb2e241ac3b5b3f73e62af4a903b28eba3fef82edd53d8` |
| `0x100140f8..0x10014244` raw refresh | `3bf597a8e0e58bc27c4e257053235ddb6aa56e6471e7ca79b4f7add578b1d1f8` |
| `0x10014b92..0x10014baf` raw IRQ flag selection | `ddd48969e3737ca5453451a05d6b548e8413da48bf701afa08acd6003188f275` |

A related correction: the historical parser-boundary note says it supports
chunk types 0..12, but its table is not proof that each type performs work.
Original table `0x100036f0` entries 7, **8 (RAW_IMAGE)** and 9 all point directly
to common cleanup `0x1000a1ef`. The cleanup frees metadata when present and loops;
it contains no raster-node creation or render dispatch. Its original bytes
`0x1000a1ef..0x1000a211` hash to
`38e38e296645db7512d1560c0ffbbae9cd9b18e34427d5a8786166b6b7c2c13c`.
Do not use ZJT_RAW_IMAGE as a presumed shortcut into the stock raw queue.
The current open bridge likewise does not emit that unsupported chunk type.

`scripts/validate-hp1020-raw-buffer-contract.py` now owns focused execution and
`analysis/hardware-boundary/raw-buffer-contract.json/.md`: **68 fragments plus
two boundary controls pass**. The full sequential aggregate passed with 98 checks
and both suites in `/tmp/hp1020-full-raw-contract.log` (child logs
`hp1020-validation.eIS7rL`). Research processes for that checkpoint finished. A current open-target decode supplies four actual packed
rows (4800 bytes), compared with the original full host decoder before being
copied into separate stock RAM fixtures. This is compositional execution, not
a producer/consumer schedule or physical output.

- Eight producer selections enter `0x10010448..0x10010460` after omitted
  allocation/reset. Input descriptor kind 1 preserves its pointer and sets
  payload source kind 1; kinds 0/2/UINT32_MAX instead set source kind 2 and zero
  the pointer, even when the descriptor supplies a nonzero address. The producer
  is not a generic borrowed-buffer adapter. Remaining construction/send is excluded.
- Twenty-two dispatch/flag cases vary source kind, work raw flag and both fills
  independently. Type 7 also skips a deliberately null raster head. Eight
  separately entered alternate-render fragments initialize both raw list heads
  and stop before raw refresh. Existing prepare and custom calls remain excluded.
- Fourteen raw-pointer selections enter `0x10014138` after the omitted readiness
  and peripheral prefix. Source kind 1 loads the decoded-band pointer; kind 2
  uses the supplied null pointer. The file selector is 2; mutations 0/1 choose
  their corresponding excluded output branch. Two empty heads reach the return
  boundary. No pointer or count is written to a peripheral.
- Twenty-four conditional raw completion/cleanup cases enter
  `0x1001451c..0x1001455a` after the omitted IRQ prefix. With references nonzero,
  the original tail subtracts 16 from a nonzero payload+0x54, decrements +0x4e,
  sets the original JobMgr event and advances video+0xa0. Both source kinds do
  this. Original RTOS init/event creation/set execute with an explicit nonwaiting
  caller; no event implementation is supplied. Raw refresh remains excluded.
- Generic list cleanup then executes separately, observing **free requests**
  at a supplied allocator boundary. After references reach zero, kind 1 requests
  buffer and node frees; kind 2 requests only the node. No actual reclamation or
  ownership across tasks is claimed. An intentionally unprefixed kind-1 buffer
  with one reference yields a request 16 bytes before the buffer in both fills:
  two conditional fixture findings, not stock faults or completed lifecycles.
- Two raw-flag-clear controls branch to the excluded ordinary refill path before
  raw retirement. All fragments check decoded bytes remain unchanged and reject
  prepare, raw-refresh, peripheral-read/write and custom-code boundaries before
  execution. They are separate from the 42 bypass cases, 28 old retirement cases,
  36 native pages and open image-case totals.

Next resolve the actual producer's input-buffer allocation and cursor convention,
supported raw metadata and consumption timing before building
an adapter. `0x10010420` is the enclosing original producer; the tested selection
passes kind-1 pointers through unchanged. Do not conflate its node's embedded
payload at node+16 with the image pointer's 16-byte retirement adjustment. The
current read-only census finds no direct CALL target or exact file-backed BE
32-bit pointer to `0x10010420` in the decoded ELF; its positive control finds
the `0x1001373e -> 0x10010398` call. This is not proof of unreachability: computed
references and external entry are not covered. Establish a real producer root
or retain an explicitly supplied replacement entry, rather than assuming this
helper is used by the normal ZjStream path. The
source-kind-2 null-pointer producer and hardware flag also need interpretation;
skipping a free request alone does not establish suitability. The full decoder
has bounded storage, but real throughput, cache visibility and engine-ready
packing still need independent evidence. Do not repeat the now-executed selector
matrix as a substitute for those unresolved contracts.

The older `video-raster-consumer-report.md` chain from normal compressed BID to
raw refresh omits the separate dispatch/refill choices above; do not take it as
proof that compressed data is normally sent straight to the raw output block.

### Original raw producer and admission (2026-09-23)

`scripts/validate-hp1020-raw-producer.py` owns
`analysis/hardware-boundary/raw-producer.json/.md`. Focused execution passes
**52 interpreter/QEMU comparisons and eight additional QEMU release cases**.
The full sequential aggregate passed **99 consistency checks and both suites** in
`/tmp/hp1020-full-raw-producer-20260923.log` (child logs `hp1020-validation.eEx0Qz`).
All tested source/fixture hashes match. Both disposable toolchains were rebuilt through
their pinned scripts; the source checksum and actual encoding gates passed.

- The complete original `0x10010420..0x100104c6` producer executes, including
  allocation, reset, metadata copy and real queue-3 delivery. Original JobMgr
  receives that actual packet and runs its selected admission arm. The owner
  hierarchy and ready-state boundary remain fixtures; no task scheduler runs.
- Descriptor `+12` values 0/1/2/3 become message selectors 3/0/1/2. Only the
  first appends to the tested work `+0x50` list. The remaining selectors still
  receive references without entering this list. No physical channel meaning
  or support for other printer models is inferred.
- Producer reset covers 70 bytes, leaving payload `+0x4e` at the allocation
  fill. Admission overwrites it from work `+0x0c`, normalizing zero to one;
  `work+0x75 == 1 && document+0x60 != 1` doubles the count, and
  `work+0x72 == 1` overrides it to one. The result is also stored at work+0x4e.
  Doubling is 16-bit: explicit 32768/65535 inputs yield 0/65534. Those arithmetic
  controls are not supported-copy claims or observed stock faults.
- Work+0x74 is unchanged. Admission copies BIH fields only for the appending
  selector when work+0x36 is zero. The producer's source kind alone does not
  establish the raw work metadata or matching IRQ family.
- A fixture allocates a buffer using the original pool, explicitly supplies a
  16-byte prefix, and passes base+16 to the producer. After one supplied raw
  completion, original cleanup really frees the kind-1 image and node when
  references reach zero. Kind 2 frees the node while the unused fixture buffer
  remains allocated. With two references, one completion retains both blocks
  but changes the image cursor to its base. A second submission/cursor reset
  is still unproven. No hardware IRQ prefix or raw refresh runs.
- The host interpreter abstracts interrupt-mask state; QEMU independently
  executes the original mask instructions. Both compare the actual payload,
  queue/list effects and pool partition. Six excluded hardware/custom-code
  entries are rejected before execution in every release fixture. These are
  serialized construction/admission and conditional cleanup observations,
  with **zero completed page lifecycles**.

A subsequent read-only pointer-store census highlights an existing, distinct
parser producer at `0x1000a0d1..0x1000a16d`. Original table `0x100036f0` entry 12
targets `0x1000a05d`; unlike chunk 8, it can build message 9. The old parser
boundary report already noted this compatibility-looking arm. It does not call
`0x10010420`; its execution is now recorded below.
Do not assume the host header's `ZJT_2600N` label proves physical support on this
device. Normal foo2zjs JBIG traffic and the open parser's supported grammar stay
unchanged. Continue to distinguish any new parser evidence from the supplied
standalone producer root and the unresolved raw-mode/output contract.

### Actual chunk-12 parser admission (2026-09-23)

`scripts/validate-hp1020-raw-parser.py` owns `hardware-boundary/raw-parser.json/.md`.
Focused execution passes **22 parser/admission comparisons and two metadata-only
controls** in the interpreter and independent QEMU. Full sequential validation
passed **100 consistency checks and both suites** in
`/tmp/hp1020-full-raw-parser-bih-20260923.log` (child logs `hp1020-validation.9CdiDF`).
At that checkpoint all recorded source and fixture hashes matched. The initial
10-admission baseline and its source hashes remain preserved in commit `b015edd`.
The September 28 continuation below supersedes the admission-only next action.

- The complete parser consumes explicit START_DOC, START_PAGE, chunk 12,
  END_PAGE and END_DOC input. Original allocation and queue code send messages
  1/3/5/9/6/2, with message 41 before 9 when a separate BIH chunk is supplied.
  JobMgr receives through message 9 and constructs the document,
  child and work ownership hierarchy. No owner hierarchy or raw packet is seeded.
  Input, document begin/end/publication and task readiness remain host boundaries.
  The original allocator/queues are explicitly initialized in single-thread RAM.
- For the band, at `0x10009e40` the parser requests exactly 16 data bytes with allocator kind
  0. Its return at `0x10009e43` is passed unchanged to payload+0x54 by the store
  at `0x1000a0df`. Admission preserves it. The observed producer has not advanced
  the pointer past a 16-byte image prefix. This is distinct from node+16 embedding
  and from any internal allocator header; no forced raw-completion fault is tested.
- Band bitmap item `0x65 = 0` gives payload source kind 1; value 1 gives kind 0.
  Both tested variants send selector 3 and append the actual node. Copy metadata
  1/2 gives one/two references, replacing allocation-fill bytes. Work+0x74 is
  zero after construction and after admission. Do not force that flag and infer
  that this input route naturally reaches the raw IRQ retirement branch.
- Explicit band dimensions are 32 by 4, BPP 1 and terminal flag 1. Two controls
  omit band width/height and obtain the same values through original BIH/cache
  fallback. Two zero-data controls parse metadata but allocate no data and send
  no message 9. All checks use both zero and nonzero allocation fills.
- Original document/child initialization is inline at `0x10009efe` and
  `0x10009f86`; work construction calls `0x1000f228`. The distinct `0x1000f1c4`
  initializer is not entered by this route.
- Runs stop at raw admission with messages 6/2 still queued. No page completion,
  raster-list cleanup, consumer, MMIO, custom instruction or printing is included. These are
  **zero completed page lifecycles**, separate from the existing 36 native pages.

The initial ten admitted cases keep work+0x84/+0x88/+0x8c zero despite nonzero
dimensions in each band.
Original literals distinguish the parser's BIH cache (`0x10005ff4 -> 0x10022c80`)
from JobMgr's (`0x10006304 -> 0x10023e28`). The tested item `0x66` populates the
former. At `0x1000e64c..0x1000e667`, message-9 admission skips its JobMgr-cache copy
when work+0x36 is nonzero; otherwise these fixtures copy the still-zero JobMgr
cache. Prepare later reads work+0x84 at `0x10014a3b` and derives its stride at
`0x10014a40..0x10014a49`. Therefore band metadata agreement alone does not supply
a complete preparation contract. No division failure or hardware fault was run.

The expanded experiment now varies page bitmap metadata independently of the
band's. Eight additional cases precede chunk 12 with a real chunk-4 BIH. Original
message 41 copies the 20-byte BIH to the JobMgr cache and frees its actual source
allocation; both engines execute those original functions and compare the free
pool partition. With page bitmap 1, later message-9 admission copies work fields
32/4/4 and options 0x5c. Page bitmap 0 skips that copy even with a populated cache.
Four crossed page/band controls without chunk 4 leave the work dimensions zero.

In two fills, page bitmap 1 plus band bitmap 0 and separate BIH delivery now yield
source kind 1 **and** populated work dimensions. Their raw IRQ flag remains zero
and the band pointer still equals its allocator return. This resolves the cache
connection for explicit mixed-metadata fixtures, not physical protocol support,
the cursor prefix, raw-mode reachability or a complete output contract.

### Serialized raw handoff to preparation (2026-09-28)

The same generator and `scripts/hp1020_raw_handoff.py` continue actual parser
owners, allocations and pending END_PAGE/END_DOC packets. **Eight preparation
continuations and four missing-dimension controls** agree in the interpreter and
independent QEMU. The initial focused run used supplied output buffers; log
`/tmp/hp1020-raw-handoff-final-20260928.log`, matching sources/reports preserved
in `/tmp/hp1020-raw-handoff-tested-20260928/`. Current source executes original
buffer initialization, as described below; do not substitute that earlier log
for the expanded validation. The final full sequential run passed **102 checks
and both suites** in `/tmp/hp1020-full-raw-handoff-20260928.log` (child logs
`hp1020-validation.a6RCMj`). Current hashes match; both raw validators snapshot
loaded sources before execution and reject any changed source before reporting.
The initial execution agreed in both engines but failed a report byte-range gate
because its constructor range ended inside an instruction. The final generator
audits the complete original constructor before executing cases. This was a
test-boundary error, not a stock execution failure; no report hash was patched.

- JobMgr executes the queued endings and schedules one/two copies. Original
  PrintMgr queueing, allocations and media matching send engine message 13;
  the original RAM-only dispatcher transforms it into message 14. Original
  PrintMgr then delivers message 11 to the VideoThread queue. Engine startup
  message 24 is observed but its hardware handler is never executed.
- Explicit ready/online and one-tray wildcard-media RAM supply prerequisites.
  Datastore 1's null backing pointer needs a separately allocated 16-byte options
  fixture; the original media matcher otherwise reaches a guarded null read.
  That incomplete-fixture observation is not classified as a stock defect.
  Original task scheduling, engine readiness and sensor behavior are not proved.
- Fresh synthetic task contexts execute the original ENTRY and then cut to the
  specified PrintMgr receive-loop prefix or VideoThread receive boundary. The
  VideoThread hardware startup is excluded. The independent constructor prefix
  now creates idle video state and output storage through the original allocator;
  pool capacity remains explicit and separate from the parser-owned image.
- Both source kinds 0/1 and copies 1/2 reach `0x10014baf`, before the first video
  peripheral access, with valid work dimensions. Original preparation computes
  stride 4 and clears the high IRQ-selection bit in video+0xfc because work+0x74
  is still zero. Source kind 1 selects the alternate-render branch, but the later
  call at `0x10015438` is not executed. Dispatch kind and IRQ family are distinct.
- Executed-store observation and before/after bytes agree: work+0x74 remains
  zero, payload+0x54 remains the actual allocator return, references remain 1/2,
  and image bytes are unchanged. There is no late prefix or mode transition on
  this path. Four absent/suppressed BIH-copy controls reach `0x10014a51` with
  zero stride and stop before the division call; no divide failure is executed.
- The byte-verified decoded-image census has exactly one immediate `s8i` at
  base+116: the work constructor's zero store at `0x1000f271`. This deliberately
  limited census does not exclude aliases, wider writes, dynamic code or external
  input. Thirteen excluded-code controls reject before execution in both engines,
  including the constructor's peripheral prefix and allocation retry calls.

These are **zero additional native page lifecycles**, separate from the existing
36 native pages. The continuation rules out a late transition in this tested
software route; it does not prove that raw IRQ mode is globally unreachable or
that arbitrary mixed metadata is supported physically.

`scripts/hp1020_video_buffers.py` executes the original constructor from
`0x10014738` to `0x100147e3`, before its peripheral tail. The actual helpers
`0x10014838` and `0x1001488c` request `0x1900 + 0x8000` (39168) and `0x10000`
(65536) bytes, both allocator kind 2. The first is filled with 0xff; the second
retains pool-fill bytes. The constructor clears 260 video-state bytes, sets two
sentinels, creates the embedded semaphore at video+0x74, and registers five IRQ
handlers in RAM. This embedded semaphore is distinct from **work**+0x74's mode
byte. No registered handler, retry sleep or peripheral tail executes. No boot
memory discovery is inferred from the explicit 128-KiB synthetic pool.

At the tested stride 4, preparation derives four first-buffer slots of 8192 bytes
and four second-buffer slots of 16384 bytes. All spans fit their real allocated
blocks; 6400 first-buffer bytes remain beyond the ring. Both output buffers still
contain only their initialization bytes: **the source image has not been copied
or decoded into them**. This recovers output storage and preparation, not image
delivery or physical packing, and cannot explain a prefix on the distinct source
image allocation.

Two isolated idle buffer cases, with both fills, execute repeated allocation,
release, empty release and reallocation. Existing buffers return 0 without a
new allocation; original releases return 1 and clear both globals; empty releases
return 0 without freeing. Reallocation reuses the same two addresses and original
live parser allocations never change. Free marks the split blocks reusable rather
than eagerly merging them; this is observed allocator behavior, not a leak.
Four smaller-pool controls stop before retry calls: 16 KiB cannot allocate the
first buffer (`0x1001486c`), while 64 KiB retains the first allocation but cannot
allocate the second (`0x100148ad`). No sleep, retry or eventual recovery is run.
Six excluded-code checks per buffer case also reject before execution in both
engines. These idle allocation cycles are not completed page lifecycles.

The next connection was inspected directly in the original bytes after that full
run, then executed in the separate bounded delivery experiment below. Literal
`0x100067bc` is `video+0x20 = 0x1002efe0`, the four embedded
12-byte descriptors. Original producer `0x10014244` selects index video+0xe0,
requires descriptor+0 == 0 and remaining video+0xd0 != 0, then stores
`min(remaining, video+0xcc)` at descriptor+8 (`9362` at `0x1001426e`). It subtracts
that count from remaining (`227634` at `0x10014279`), sets descriptor+4 when the
remaining count becomes zero (`9561` at `0x10014281`), and sets descriptor+0 to 1
(`9360` at `0x10014283`). **This flag claims the buffer before it is filled; it
does not prove ready pixels.** Stop this prefix at `0x10014290`: following stores
at `0x10014293/0x10014298` target `0xb2080004/0xb2080008` and remain excluded.

After an omitted peripheral-completion prefix, `0x1001445d..0x1001446b` advances
video+0xe0 modulo four (`289638` at `0x10014468`), then would re-arm the producer
and enter the band queue. The existing band gate at `0x10013f6c..0x10013f72`
withholds a nonfinal descriptor when `(video+0xdc+1)&3 == video+0xe0`; a final
descriptor may pass that collision. Therefore publication/consumer ordering must
preserve this one-buffer delay, even with the custom callback disabled. Following
an independently supplied output completion, normal-mode retirement clears the
descriptor at video+0x20+12*(video+0xd8) (`9988` at `0x10014569`) and advances
video+0xd8 modulo four (`28a636` at `0x10014573`). Stop before the re-arm call at
`0x10014576`; the raw-list pointer-subtraction path is a different branch.

For aligned strides 4..2048 in the narrow image profile, the original prepared
cap `(8192 // stride) & ~3` equals `4 * (2048 // stride)`: its byte span exactly
matches one first-buffer slot. This arithmetic identity was checked for all 512
aligned strides; it is not additional original execution or a physical format
claim. A software decoder emitting four rows at a time may need to accumulate
multiple bands before publishing the original descriptor's larger count.

### Software-decoded pixels in original output storage (2026-09-28)

`scripts/validate-hp1020-software-ring.py` generates
`hardware-boundary/software-ring.json/.md`. Focused execution passes **eight
isolated buffer transfers and two continuous five-transfer sequences** in both
the bounded interpreter and independent QEMU. Log:
`/tmp/hp1020-software-ring-final-20260928.log`; prerequisite parser log
`/tmp/hp1020-raw-parser-delivery-20260928.log`. The consistency gate passes **104
checks**. That full sequential aggregate passed both suites at checkpoint
`7fe51be`, logged in `/tmp/hp1020-full-software-ring-20260928.log`, child logs
`hp1020-validation.Rqozd4`. Its report was subsequently refreshed for the shared
target in the 105-check run below; all current source hashes match. The earlier
four-case report with exact matching sources is preserved in
`/tmp/hp1020-software-ring-four-20260928/`; subsequent
source changes were executed again, never relabeled by manually editing hashes.

- The compiled open decoder runs in QEMU on the existing
  `9600x132-stripe128-edges.jbg` fixture. Its first 17 rows agree byte for byte
  with the original full decoder built under ASan/UBSan and the generated source
  pattern. The host crops one/four/17 rows and declares them as a short raw input;
  this is an explicit adapter, not native streaming integration or a new claim
  that the original chunk-12 grammar accepts the normal JBIG stream.
- Actual chunk-12 parsing, owner allocation, JobMgr/PrintMgr handoff and video
  initialization/preparation run with width 9600 and the chosen height. At
  stride 1200 the first-ring slot capacity is four rows/4800 bytes. Source
  allocation, work and payload remain unchanged throughout delivery. The work
  raw flag stays zero; no source prefix is inserted or subtracted.
- The original claim prefix stops at `0x10014290` before peripheral writes.
  Its descriptor already says owned while pixels are still the old contents.
  The supplied software adapter invokes original `memcpy` with an explicit
  source offset; it is not a recovered stock caller. Every intended pixel and
  every byte of both actual allocated output buffers are compared after copying.
- After explicit copied-data completion, a fresh original IRQ entry cuts to
  `0x1001445d` and runs the RAM publication tail through `0x10014468`. A fresh
  band-queue entry cuts past physical readiness to `0x10013f57`, with the real
  video/descriptor pointers, and stops at `0x10014014`. Callback-disabled
  selection returns the populated first-ring pointer. Output acceptance is
  supplied at `0x100140c9`; it decrements +0xd4 and advances +0xdc, stopping at
  `0x100140e5`. Output completion is separately supplied through the original
  normal-mode classification/release at `0x1001451c..0x10014576`.
- The eight isolated cases vary zero/nonzero pool fill, first/last ring slot,
  and one/four rows. Last-slot index three is an explicit fixture in this matrix.
  Temporarily clearing the final flag reaches the one-slot withholding branch;
  restoring the actual final flag permits selection. Occupied and zero-remaining
  producer controls return without writes. Unwritten final-slot bytes stay 0xff.
- The two continuous cases vary pool fill and retain constructor-zero indices.
  Five publications/acceptances/releases use slots **0,1,2,3,0** and row counts
  **4,4,4,4,1**, with all index advances performed by original instructions.
  The first actual nonfinal band is withheld before the second publication.
  Four published slots block the next producer claim. Accepting slot zero
  advances +0xdc but leaves it owned, so a second claim still stops. Only the
  separately supplied completion releases it for the fifth band. The final
  one-row reuse leaves earlier bytes outside that row exactly intact. Concatenated
  selected bands equal all 20400 source bytes; final indices are 1/1/1, both
  remaining counts zero, and all four ownership flags clear. No final flag or
  index is patched in these continuous cases; interleaving is host-selected.
- Thirteen excluded-code controls per case reject before execution. The source
  pool and owner references remain live: retiring output descriptors does not
  establish page/source cleanup. These observations are **zero additional native
  page lifecycles**, zero hardware transfers, and no physical-format or throughput
  proof. No compressed-image DMA, output writes, status read, custom callback,
  native asynchronous task scheduling or automatic completion runs.

The transfer-ring generator now separates input-ring indices +0x94/+0x98 from
output claim/publication/selection/release indices +0xe0/+0xdc/+0xd8. Its earlier
description of +0xdc as only a recovery latch was incomplete, and descriptor+4
is now identified as the final-band flag against original bytes/execution.

The direct compiled connection that removes the host pixel-copy bridge is now
executed below. The original and software structures remain separate; this does
not turn the chunk-12 fixture into a native decoder/engine pipeline or supply its
source-owner cleanup. Follow the normal descriptor family and do not force the
raw flag. Live configuration, physical packing, repeated page submission and
eventual hardware behavior remain unresolved.

### Direct compiled decoder and software output ring (2026-09-28)

`open-firmware/image-core/hp1020_image_ring.c/.h` implements bounded software
ownership based on the recovered ring contract. `ring-fixture.c` connects the
existing C decoder to it within a single compiled call. The implementation does
not share the original firmware's structure ABI or assume a hardware address.
The image is initialized with the recovered per-slot row capacity, so each
decoder band fits one slot; no host pixel copy or raw-parser admission is used
inside this compiled connection.

`scripts/validate-hp1020-image-ring.py --target` passes **36 sanitized host and 36
QEMU cases**, plus **11 API-rejection controls per engine**. Reports:
`image-core/ring-validation.json/.md`; log
`/tmp/hp1020-image-ring-target-20260928.log`. Original bounded ownership was
refreshed against the shared target in
`/tmp/hp1020-software-ring-shared-target-20260928.log`, after the decoder's 176
cases/66 target checks passed in `/tmp/hp1020-image-core-ring-build-20260928.log`.
Full sequential validation passed **105 consistency checks and both suites** in
`/tmp/hp1020-full-image-ring-20260928.log` (child logs `hp1020-validation.WTCBMK`).
Recorded sources and fixtures matched when that checkpoint finished.
The initial host build stopped on a Darwin common-section alignment warning;
using the existing host checks'
`-fno-common` flag resolved it. That was a build diagnostic, not a pixel/ownership
failure. Its log and initial unexecuted draft remain outside the current evidence.
The initial host-only report and every exact tested source were preserved in
`/tmp/hp1020-image-ring-host-first-20260928/`; only the stronger current host/target
report remains at the maintained evidence path. No report hashes were patched.

- Width/height cases are 9600x17, 9600x132, 1024x129, 512x33, 32x8 and 16384x4,
  each with fills 0/204 and input fragments 1/7/65536. Original full JBIG decoding
  and source patterns agree with every output byte. Both engines compare the
  entire 32800-byte guarded storage, preserving all bytes outside intended copies.
  A new original full-decoder encode supplies the actual 9600x17 BIE, rather than
  cropping decoded pixels on the host. Its source pixels equal the earlier
  bounded original sequence's first 17 rows.
- Every 17-row case matches all 20 comparable original state snapshots: indices,
  both remaining counts, all owned/final/count descriptor fields and ordering.
  The intermediate original claim-before-copy snapshot is deliberately absent
  from the C call comparison: software push is a serialized copy/publication
  operation, not an emulated DMA claim/interrupt. Six host and six target
  comparisons establish the same observable publication/acceptance/release
  contract under the supplied consumer ordering.
- The longest image emits 33 bands, pauses on a full ring 29 times, and wraps
  repeatedly. A blocked push copies nothing and retains the pending decoder
  band. Feed/finish while paused consume no new input. Acceptance advances the
  selection index but retains ownership; another push remains blocked and
  byte-identical until explicit completion releases the slot. Input fragments
  are poisoned after every feed, proving that caller input can be reused.
- Invalid geometry/capacity, wrong band order/size, premature or duplicate
  acceptance/completion and an out-of-range completion index return sticky
  errors without releasing owned storage. This is API rejection evidence, not
  printer fault recovery. Caller storage/nonoverlap and a single execution
  context remain API preconditions; no lock or native IRQ interleaving is tested.
- Target component state plus minimum buffers totals **30824 bytes** at
  9600-bit width: image state 4312, ring state 112, history 2400, decoder band 4800,
  output slots 19200. Code, stack, compressed caller input and large fixture
  captures are excluded. This is not a full printer memory requirement.
- The target is the same byte-audited BE/call0 RAM ELF, with a simulated consumer.
  **Zero additional native page lifecycles or hardware transfers** are claimed.
  Decoded rows remain provisional until decoder/framing success. Draining the
  software ring does not retire stock work/source owners or acknowledge a page.
  Odd-row image cases do not broaden the existing stricter ZjStream planner.

The next section now connects this ring to complete documents. Original owner
integration is not a requirement of the independent replacement. Hardware
scheduling requirements, live configuration, physical packing, engine behavior
and power-cycle recovery remain unproven. Do not repeat resolved metadata,
selector or cancellation matrices.

### Compiled bounded document output (2026-09-29)

`hp1020_image_output.c/.h` now composes the existing bounded ZjStream parser,
streaming JBIG decoder and independent software ring. Its synchronous consumer
must explicitly advance acceptance or completion, or return an error. A full
ring retains the decoder's pending band. Different page geometries cannot reuse
output storage until the old page has drained, and finish requires valid
document framing and completion of all published rows. Copies remain plan
metadata; this component does not replay images for multiple copies.

The first `validate-hp1020-image-output.py --target` checkpoint passed **39
sanitized host and 39 QEMU cases** (28 successful software streams and 11
expected rejections), preserved at `02a858a`, in
`/tmp/hp1020-image-output-target-20260929-permitted.log`. The initial host run
exposed an overly broad test-name prefix matching both rejection numbers 1 and
15; fixing the assertion selector resolved that harness error. A subsequent
target invocation passed host checks but could not create QEMU's debugger socket
inside the sandbox; the same RAM-only test passed with socket permission. No
printer transport was opened. Full sequential validation passed **106 consistency
checks and both suites** in `/tmp/hp1020-full-image-output-20260929.log` (child
logs `hp1020-validation.3BfPNL`). That checkpoint's tested source hashes match; the private
page-metadata-reuse draft was not applied or executed during that run.

- Mixed sequences switch among 9600x132, 16384x4, 32x8 and 1024x260. A new
  original full-JBIG encode/decode of the last geometry independently verifies
  its source pattern and final short output slot. Three consumer orderings,
  two memory fills and three input packet/fragment schedules preserve every
  output byte, every output storage byte and the exact page/write traces.
- Input packets and successfully consumed compressed chunks are poisoned after
  use. Output accepted earlier is hashed again at actual simulated completion,
  proving it survives in-flight ownership. Several accepted slots can remain
  outstanding simultaneously. The pending decoder band remains unchanged while
  the consumer makes space, including when the previous page is draining.
- Missing END_DOC after a 132-row image reports truncation after emitting an
  exact source prefix, retaining four owned slots rather than claiming success.
  An error immediately after acceptance retains that accepted slot. Padding,
  truncated headers, no-progress consumers, mid-page failures and final-drain
  failures remain sticky and preserve memory on subsequent calls.
- Target component state plus fixed storage is **123968 bytes**, excluding code,
  stack, caller packets and captures. Captures belong only to the RAM fixture.
  The initial 16-page parser limit is removed for streaming in the next section;
  retained whole-file inspection keeps its own bound. No added native page
  lifecycle, physical output, asynchronous IRQ,
  cache, boot or hardware recovery evidence is claimed.

USB reuse review confirms that a portable stack still needs setup/reset,
endpoint transfer and completion reporting from our controller-specific layer.
The existing evidence is in `analysis/usb-path/usb-bulk-probe-contract.md` and
`usb-parser-shim-contract.md`; TinyUSB's [port interface](https://docs.tinyusb.org/en/latest/porting.html)
does not supply those missing hardware observations. Retain the existing inert
probe route while assessing a compatible controller driver. Adding an RTOS or a
USB stack is not a prerequisite for the bounded software document path.
TinyUSB also provides a [printer-class example](https://docs.tinyusb.org/en/latest/examples/device/printer_to_cdc.html)
with bidirectional endpoints and an IEEE 1284 device-ID response, so reuse can
cover the printer-class layer as well as generic USB requests. This is upstream
capability evidence only; no HP controller port or dependency integration was
executed in this review. Do not run that example's device-access instructions.

### Streaming page metadata reuse (2026-09-29)

The preceding document-output checkpoint was fully validated and saved at
`02a858a` before applying the next change. Streaming parser mode now reuses
`pages[0]` for each page; `hp1020_semantic_current_page` supplies the current view
while `page_count` remains cumulative across documents. Whole-file retained mode
keeps its previous 16-page/128-raster limits. Image output owns a separate copy
of its active plan and drains old output before reinitializing the ring, so the
new parser record cannot change an outstanding page's geometry. Count overflow
fails before incrementing page/document or image band/row totals.

Focused output validation passes **45 sanitized host and 45 QEMU cases**:
31 successful software streams and 14 expected rejections. Both a 65-page
mixed-size document and 65 consecutive mixed-size documents match every source
pixel and every output-storage byte. Four explicitly seeded uint32-boundary
controls reject page, document, row or band count overflow before emitting any
output. Fixture captures are bounded separately from component memory. Unused
parser page slots stay zero. The component still uses **123968 bytes** of target
state/fixed storage, with the same exclusions as above. Log:
`/tmp/hp1020-image-output-page-reuse-fixed-20260929.log`.

The bounded stream regression separately passes **66 host and 44 QEMU cases**,
including its detailed 10 MB source image, compressed-buffer reuse, 65 pages and
a same-input retained-mode rejection at page 17. Log:
`/tmp/hp1020-image-stream-page-reuse-20260929.log`. Full sequential validation
passed **106 consistency checks and both suites** in
`/tmp/hp1020-full-page-reuse-20260929.log` (child logs `hp1020-validation.1RndJc`).
All 309 source/fixture/sample hash entries in the five current image reports match.
Validation processes for that checkpoint finished.

The first page-reuse build passed 45 sanitized host cases but its instruction
audit rejected `break 1,15` at `0x200004d9` (bytes `0f1400`) before any QEMU
execution. The annotated code's cold branch copied a null current-page pointer;
the compiler had inserted a trap after that undefined path. Explicit missing-page
checks in the image consumer and parser's BID admission remove that path and
return an ordinary order error. The instruction allowlist was not broadened.
The rejected ELF/map, exact source snapshot and failure log are retained at
`/tmp/hp1020-page-reuse-null-trap-20260929/` and durably archived in
`image-core/source-snapshots/page-reuse-null-trap.tar.gz` with a sibling member-hash
manifest. This is a compiler-gate finding in
new code, not one of the six original conditional null reads. The earlier private
draft directory preserves pre-fix text only; it is not the latest implementation.

The next useful integration question is the consumer/transport boundary: how
to preserve queued output and quiesce it on cancellation or a USB reset before
reusing memory. The controller-family finding below now gives a concrete open
reference for the USB side. Keep that separate from physical transfer
abort/recovery and genuine engine completion. Copies, media/quality breadth,
live status, startup and physical printing remain open feature-parity work.

### Classic Synopsys USB controller family (2026-09-29)

`scripts/validate-hp1020-usb-controller-family.py` compares the original ELF
with unmodified Linux v6.12 `amd5536udc.h`, `snps_udc_core.c` and platform glue,
pinned to `adc218676eef25575469234709c2d87185ca223a`. The source, hashes, origin
and GPL license are retained under `analysis/usb-path/controller-reference/`;
they are research inputs, not compiled or installed driver dependencies.
Reports: `analysis/usb-path/controller-family.json/.md`.

- **24 literal/layout matches and 18 instruction anchors** establish a strong
  match to the classic Synopsys device-only UDC family. Global registers,
  both endpoint banks, 32-byte register stride, 16-byte descriptors, ownership,
  packet counts and endpoint masks agree. The Linux filename does not identify
  an AMD chip in this printer. This is not the DWC2 high-speed OTG layout or
  proof that an existing platform port can run unchanged.
- **12 original re-arm cases** agree between the bounded interpreter,
  independent QEMU and a separate byte oracle. Supplied globals point to RAM;
  the submission-address literal alone is redirected to a guarded RAM sink.
  Zero, unaligned and aligned next pointers, offsets 0/37 and fills 0/204
  preserve the entire arena except expected descriptor/sink writes. The helper
  leaves descriptor bytes 4..7 untouched, writes +8 and clears +12. Its leading
  bytes `08 00 00 00` match last-descriptor bit 27 with host-ready ownership;
  the old re-arm report's opcode wording is corrected in its generator.
- **51 separately entered status fragments** verify all four owner states,
  both last-flag values and six low-16-bit counts. Only owner 2 reaches count
  admission. Three nonzero receive-status controls also reach admission: this
  small original fragment does not itself validate those bits. It is not an
  oracle for successful transfer, nor does encoded zero prove a real zero-length
  or 65536-byte transfer. The IRQ/NAK prefix and both downstream paths are cut.
- Both unredirected submission controls reject **before** the peripheral store.
  Original code bytes remain unchanged; the ELF on disk is never patched.
  The separately inspected startup branch's `0x320` device-control mask matches
  BE/burst/mode positions. Its peripheral instructions never execute. Real bus
  ordering, aliases/cache, reset/cancel, PHY/wrapper registers at `0xb3010000/4`,
  actual USB traffic and startup remain unproved. These are **zero USB transfers
  and zero additional native page lifecycles**.

Focused validation passed in `/tmp/hp1020-usb-controller-family-status-20260929.log`.
The first static expectation omitted OUT endpoint 0 from the mask; original
`0xfffcfffe` actually unmasks IN0, OUT0 and OUT1. The assertion stopped before
QEMU. Its exact failed script/log are at
`/tmp/hp1020-usb-family-mask-audit-20260929/`. The first successful re-arm-only
report and every hashed source were saved at
`/tmp/hp1020-usb-family-rearm-first-20260929/` before adding status execution.
Both captures are also byte-preserved under `analysis/usb-path/source-snapshots/`
as `controller-family-mask-audit.tar.gz` and `controller-family-rearm-first.tar.gz`,
with member-hash manifests. Neither report hashes nor raw captures were patched.
Full sequential validation passed **107 consistency checks and both suites** in
`/tmp/hp1020-full-usb-family-20260929.log` (child logs `hp1020-validation.atqz2B`).
Tested source hashes match and all validation processes have finished. The
preceding complete 106-check document checkpoint is saved at `35e3f07`.

Use this family-specific driver as the controller reference, rather than
starting with a generic DWC2 port. The first bounded receive/document adapter
is now implemented below; real controller reset/abort remains unresolved.
Physical quiescence is not supplied by clearing C state or by this RAM sink.
TinyUSB remains useful above that adapter for standard USB/printer-class work;
no RTOS or Linux port is required merely to reuse these contracts. Retain the
inert hardware-test ladder and all separate opt-ins; do not add engine/video
operations or broaden the probe allowlist from this family inference.

The pinned upstream source gives two concrete port limits. Its `udc_soft_reset`
skips the nominal reset bit for the Broadcom variant because that bit is reserved
there; family resemblance cannot authorize that write on HP. Its receive-enable
control is shared across OUT endpoints, so queue/cancellation handling must keep
control traffic and bulk ownership consistent. `udc_dequeue` also distinguishes
a host-ready descriptor from one already touched by DMA. These are upstream
design observations, not tested HP reset/abort semantics. The existing stock
bulk callback names are only candidates. The software drain has now been
checked against original instructions and executed as described below.

### Receive ownership and restart composition (2026-09-29)

The independent pinned-source review exposed two constraints that family layout
agreement alone did not provide. `snps_udc_core.c:2071-2092` handles endpoint
BNA/HE separately before normal completion; endpoint errors cannot be tied only
to an outstanding descriptor ticket. The header declares RX bits 29:28 but the
driver never interprets their values. RX zero is therefore a conservative policy,
not established HP success semantics. `udc_dequeue` (1250-1300) temporarily stops
global RDE, inspects descriptor ownership, restores RDE and gives the request
back without a separate quiescence poll. The dummy helper's HOST_BUSY comments
conflict with its actual DMA_DONE expression (606-618). Neither behavior is a
portable HP memory-reuse contract.

The controller-family generator now adds 11 exact instruction anchors and six
dual-engine software-list drain cases at `0x10008fb0`: lengths 0/1/4, fills 0/204.
Original list peek/pop execute; free and outer mask calls are explicit supplied
services. QEMU executes the original short list critical helper, while the
interpreter abstracts PS save/restore. Buffer/node free calls match the separate
oracle, the list becomes empty, and a supplied busy descriptor plus the entire
guarded arena remain unchanged. This is conditional software bookkeeping, not
proof that those frees would be safe during device DMA. No peripheral literal
is redirected for these drain cases. The original IRQ checks mask 8, consistent
with the reference's UR bit 3, but also consults HP wrapper status
`0xb3010004` bit 4. The complete reset path and physical quiescence remain open.
Focused log: `/tmp/hp1020-usb-family-ownership-20260929.log`.

`open-firmware/usb-receive-core/` implements a fixed four-slot receive queue and
composes it with the existing image-output pipeline. Reservation sequence and
generation reject old or duplicate callbacks; later completions wait behind
the head. A full queue returns backpressure. Owner 2, RX zero, last set and a
bounded count are the conservative single-descriptor profile. Count zero is
an empty transfer, never EOF. A separate generation-scoped endpoint-fault API
fences pending, ready, consumed and empty queue states. A review caught the
initial design's ticket-only fault path before execution and prompted that API.

Stop or error preserves input and output ownership. Restart requires separate
current-generation receive and output quiescence acknowledgements, fences all
production before either acknowledgement and increments generation before reuse.
These are explicit external promises, not an implemented DMA/engine abort. The
composition must not reinitialize or restart its embedded receive queue alone.
All APIs are serialized and nonreentrant; the eventual port owns interrupts,
stable completion observations, barriers/cache and actual controller state.

Focused validation passes **75 sanitized host and 75 QEMU cases**, including
all owner/RX/last combinations, count bounds, endpoint-wide faults, a late head,
full queues, slot wrap, stale generations, sequence/generation exhaustion,
mixed-size documents, 65 pages, zero transfers between real bytes and explicit
EOF. Independently decoded patterns verify exact source pixels. A malformed
chunk preserves later ready input. Failure after output acceptance retains that
slot; both acknowledgement orders then permit a fresh exact-pixel document.
Exact pre-operation snapshots compare memory and ownership across stop/fault,
each acknowledgement and rejected restart. Accepted output is rechecked at
every observation, not only on normal completion. This stronger retention check
was added after independent review of the first 74-case host-only run.

Target component state/fixed memory is **128168 bytes**, excluding code, stack
and test captures. Conservative target instruction audit passes unchanged.
Report: `analysis/usb-path/receive-core/validation.json/.md`; log
`/tmp/hp1020-usb-receive-target-20260929.log`; exact run sources/captures:
`/tmp/hp1020-usb-receive-y0ycbwlh/`. These are **zero real USB transfers and zero
additional native page lifecycles**. Input/output callbacks are supplied.

The first host assertion incorrectly expected an arbitrary `BAD!` preamble to
fail, but the existing parser intentionally searches for `JZJZ`. Original source
inspection confirmed that behavior; the fixture now uses an invalid chunk after
valid magic. Failed run/source: `/tmp/hp1020-usb-receive-0_c8nray/`, log
`/tmp/hp1020-usb-receive-host-20260929.log`. The successful earlier 74-case host
report and exact sources remain at `/tmp/hp1020-usb-receive-asdrun5m/`; neither
that report nor its hashes were patched after strengthening the tests. Both
captures are byte-preserved under `analysis/usb-path/receive-core/source-snapshots/`
as `preamble-oracle.tar.gz` and `first-host-retention-review.tar.gz`, with
member-hash manifests. The current report contains both host and target results.

Full sequential validation passed **108 consistency checks and both suites**,
in `/tmp/hp1020-full-usb-receive-20260929.log` (child `hp1020-validation.SAqbeg`).
All validation processes finished; tested sources still match. The preceding
107-check checkpoint is `89863e9`. No installed printing files or probe allowlists
were changed. This checkpoint is committed as `2e0a986`. The then-unexecuted
output-submission draft was excluded from that full validation; its later
focused result is recorded below. Real controller ownership/reset and physical
output contracts remain open; this queue cannot infer either from its own
success.

### Original output-submission arithmetic (2026-09-29)

`scripts/validate-hp1020-output-submission.py` now passes **30 cases in both the
bounded interpreter and independent QEMU**. Report:
`analysis/hardware-boundary/output-submission.json/.md`; focused log:
`/tmp/hp1020-output-submission-20260929.log`; exact source snapshots and captures:
`/tmp/hp1020-output-submission-c3744u4t/`. The report pins the stock ELF, the
recursive local Python dependency closure, three original byte ranges and
23 individual instruction anchors. All sources still match. This adds zero
native page lifecycles, zero USB transfers and zero peripheral instructions.

Each fragment executes original ENTRY at `0x10013f34`, then uses explicit
register cuts. The already-proven ring selection is not repeated. The
file-backed selector cell `0x1001cdac = 2` chooses the single-output arm:
the selected pointer is unchanged, the computed destination is `0xb1000008`,
and the count for `0xb100000c` is `floor(rows / divisor) OR (final != 0 << 24)`.
No store to either destination executes. The original unsigned division helper
executes in both engines. Separate conditional controls override the selector
to one in private RAM and observe a second pointer at `pointer + video[0xbc]`,
destination `0xb1000108`, and common count `floor((rows >> 1) / divisor)`.
That path stops before the readiness read, then a separate fragment executes
only the terminal-bit OR, without supplying a ready result. Second-lane flags,
ready branching and all actual submissions stay excluded.

Rows, divisor, terminal value, stride/window and selected pointer are supplied
arithmetic inputs. Divisor-zero controls record the original helper's zero
result, not a safe production policy. Large-count controls overlap bit 24 to
distinguish bitwise OR from addition; they do not claim legal page dimensions
or accessible pixel spans. These four controls were added, and the independent
oracle changed from addition to OR, before the draft's first execution.
Fourteen excluded peripheral/engine instruction boundaries are rejected before
execution in each engine. All nonstack writable RAM, including the nonuniform
selected buffer, remains byte-identical. This establishes arithmetic under the
cut preconditions, not a contiguous native output lifecycle or physical pixels.

The semantic planner's `window` and callback fields describe the callback
profile, whereas executed bypass preparation uses `video+0xbc = stride`,
`+0xc4 = 1`, `+0xf4 = 0`. The compiled image ring already uses `stride` and
does not inherit the callback window. Future submission code must choose the
bypass geometry explicitly. No physical polarity, bit order, two-bit sample
meaning or lane interleave is inferred from the pointer/count fragments.

Full sequential validation after this integration passed **109 consistency
checks and both suites** in
`/tmp/hp1020-full-output-submission-20260929.log`, child `hp1020-validation.2TjALV`.
All processes finished and the 23 tested local source hashes still match.
This checkpoint is committed and pushed as `9eb8ee3`. The then-unexecuted
class-reset and output-format drafts were excluded from that full run; their
later focused results follow. Do not add a device-driving adapter from
arithmetic alone.

### Original class reset and output format (2026-09-29)

`scripts/validate-hp1020-usb-class-reset.py` passes **20 interpreter/QEMU cases**:
two one-hot registered handles, 0/1/4 pending nodes and both initial fills,
noncanonical reset fields, and nearby unsupported request controls. Original
ENTRY `0x10008ff0` precedes an explicit register cut to `0x10009399`; setup
admission is supplied. Original byte swaps and dispatch select the `0x2102`
arm, registration clear at `0x10007c70` and list drain at `0x10008fb0`.
Free/outer mask calls are supplied, original peek/pop execute, and QEMU executes
the short critical helper. The response count becomes zero and execution stops
before sender `0x100096a9`; unsupported requests stop before stall MMIO.
Ten excluded peripheral/engine boundaries reject before execution. Exact allowed
nonstack changes agree, and a standalone supplied busy status word is unchanged.
It is not a descriptor linked to the drained buffers and adds no free-safety or
DMA quiescence proof. Noncanonical fields describe HP dispatch, not our policy.
Report: `analysis/usb-path/class-reset.json/.md`; log
`/tmp/hp1020-usb-class-reset-20260929.log`; exact source/captures:
`/tmp/hp1020-usb-class-reset-877t9h9g/`.

`scripts/validate-hp1020-output-format.py` passes **12 interpreter/QEMU cases**:
BPP1/BPP2 at supplied 600dpi bypass geometry, file-backed selector 2 versus
conditional RAM values 0/1, and old peripheral-word arithmetic seeds zero/all
ones. Fresh original ENTRY `0x10014910` precedes every explicitly marked cut.
The table fragments produce these words without writing them to peripherals:

| BPP | Selector 0 | Selector 1 | Default selector 2 |
|---|---|---|---|
| 1 | `0, ffffffff` | `0, ffffffff` | `0, 1f` |
| 2 | `0, 1f, 1ff, 1fff` | `0, 7f80, 7fff8, 3fffff` | `0, 7, 1f, 7f` |

Thus the two single-output selectors are not interchangeable. Control masks
preserve `old & 0xfcffffff`, adding bit 24 only for BPP2. The supplied stride
fragment preserves `old & 0xffff0000` and ORs 1200. BPP2 alone increments its
software table counter to four; all other nonstack RAM remains unchanged.
The report pins 37 instruction anchors, 15 literals and four original byte
ranges. Twenty-nine peripheral/custom/engine boundaries reject before execution.
Earlier zeroing/configuration and actual register reads/writes remain omitted;
table values do not establish physical polarity, sample meaning or packing.
Report: `analysis/hardware-boundary/output-format.json/.md`; log
`/tmp/hp1020-output-format-20260929.log`; exact source/captures:
`/tmp/hp1020-output-format-_n7nd1xr/`.

Both focused runs passed on their first executions with current source hashes.
They add zero peripheral instructions, USB/control transfers or native page
lifecycles. Their new consistency gates are integrated; full validation follows
the printer-class integration below.

### Printer-class/document composition (2026-09-29)

The independently implemented `open-firmware/usb-printer-class/` passes **73
sanitized host and 73 QEMU cases**. It implements the USB printer-class request
contract above the already-verified receive/document components: explicit
little-endian SETUP parsing, big-endian ID-length clipping, copied status snapshots
and asynchronous reset. `README.md` beside the source pins the USB-IF specification
and exact TinyUSB/USBX source reviews. No upstream class code was copied.

TinyUSB 0.21.0 can supply generic enumeration/EP0 after a controller port exists,
but its current printer callback acknowledges reset immediately and rearms OUT
without our old-event identity/quiescence contract. USBX's abort likewise does
not establish the controller toggle/ownership condition. A small independent
three-request layer therefore preserves these gates without requiring an RTOS.
This is not a TinyUSB/USBX port or implementation of USB endpoint traffic.

Each SETUP receives a nonwrapping identity. A newer request supersedes the reply,
not an unfinished document stop. Repeated reset replaces all local promises even
within the same receive generation. Finish requires three separate promises:
old OUT writes/events settled, old output settled, and bulk-IN/stalls/toggles
settled with endpoints unarmed. The adapter must establish those physical facts;
clearing C state cannot supply them. EP0 response storage has a separate exact
identity and cannot be overwritten until its own quiescence acknowledgement.
The test fixture independently tracks EP0 ownership so an erroneous early clear
cannot disable its retention oracle. Current faults invalidate reset promises;
old faults/completions cannot affect a new generation.

The cases include ID clipping across 255/256 bytes, nonzero configuration index/
interface/alternate, all defined status bits, unknown fallback metadata, malformed
fields, canonical/legacy reset, all six promise orders, superseding status/ID/
malformed requests, faults after all promises and both identity-exhaustion paths.
Actual composed decoding accepts 148800 bytes before the mid-page stop and holds
output. All six orders with both fills preserve storage until restart, then produce
an exact 32-byte new page of different width. A stale completion is delivered
after slot zero has been reused. Generation exhaustion retains accepted output.
An independent full JBIG decoder supplies expected pixels; every observed state,
pixel/control byte and retained storage byte agrees across host and QEMU.

Target component state/fixed memory is **128216 bytes**, excluding code, stack,
immutable ID storage and fixture captures. The focused run pins its 49-file closure;
subsequent shared-auditor edits require regeneration in the current full run.
Report: `analysis/usb-path/printer-class/validation.json/.md`; focused log:
`/tmp/hp1020-usb-printer-target-20260929-2.log`; exact captures/sources:
`/tmp/hp1020-usb-printer-uvb81b5c/`.

The first host run passed 73 cases, but the first target audit stopped before
execution because the test ID's `% 26` expression linked libgcc `__umodsi3`,
whose trap is outside the existing conservative allowance. Replacing only the
fixture generator with an explicit alphabet wrap removed that helper; the audit
was unchanged. The earlier host report, exact sources, failed ELF/build outputs
and logs are preserved under `analysis/usb-path/printer-class/source-snapshots/`
as `first-host-target-audit.tar.gz` plus a member-hash manifest. They are not
silently attributed to the later fixture. No production class change was needed.

Full sequential validation passed **113 consistency checks and both suites**,
including the original GET_PORT_STATUS experiment below, in
`/tmp/hp1020-full-printer-class-20260929.log` (child `hp1020-validation.tBubz6`).
That checkpoint is committed and pushed as `eff3611`. All control/receive additions remain zero actual USB
transfers and zero additional native page lifecycles. Copies are metadata; physical
status, controller cancellation, boot and output hardware remain open.

### Original USB port-status response (2026-09-29)

`scripts/validate-hp1020-usb-port-status.py` passes **28 interpreter/QEMU cases**:
24 accepted request patterns and four unsupported-pair controls. Canonical,
noncanonical, zero-length and all-fields patterns cross three unrelated status
RAM seeds and both initial fills. Fresh original ENTRY `0x10008ff0` precedes
three explicit cuts: isolated `movi.n a7,0` at `0x1000912d`, `mov.n a3,a7` at
`0x10009286`, then request dispatch at `0x10009399`. The fixture poisons a3/a7
first, so original instructions establish zero rather than receiving zero as
an unexplained input. Surrounding initialization and setup admission do not run.

The `0xa101` dispatch stores a3's low byte at stack+80 (`0x100097f5`), publishes
that pointer and count one (`0x1000984f..0x10009856`) and stops before sender
`0x100096a9`. No status-manager or datastore getter executes. Changing unrelated
status RAM and datastore entry 25 does not change the prepared zero byte. Exact
nonstack mutations and a guarded 32-byte response-frame slice agree in both
engines. Sixteen excluded sender/peripheral/status/custom boundaries reject
before execution. Unsupported pairs select stall intent before its handler.
Twenty-one instruction anchors, five literals and six original ranges are pinned.

This narrows the source of useful status: this original USB class reply is not
a measured paper/engine feed. Nearby datastore index-25 code belongs to the
GET_DEVICE_ID path, not GET_PORT_STATUS. The replacement keeps its explicit
unknown fallback until an actual status adapter exists. Noncanonical fields and
the fixed prepared byte describe original response construction, not recommended
policy, completed control transfer, physical calibration or observed wire bytes.

Focused log: `/tmp/hp1020-usb-port-status-20260929.log`; exact sources/captures:
`/tmp/hp1020-usb-port-status-0g08cm__/`; report:
`analysis/usb-path/port-status.json/.md`. The first execution passed, current
23-source closure hashes match, and zero control/USB transfers, native page
lifecycles or peripheral instructions were added.

### Executed reusable USB protocol integration (2026-09-29)

`open-firmware/tinyusb-device/` composes TinyUSB's generic device/EP0 core with
our existing class/document component and a synthetic DCD. The 19 upstream
MIT-licensed files remain byte-identical under `vendor/tinyusb-0.21.0/`, pinned
to `dae3f9a366bfcddbf9dcf1b48d7500286a849539`. No built-in class or hardware DCD
is imported. `scripts/prepare-hp1020-tinyusb.py` verifies every input, applies the
separate local patch without fuzz to disposable copies, then checks the entire
resulting source set against its manifest. Original bytes are never overwritten.

**Unchanged upstream: 52 host/52 QEMU scenarios.** Fourteen observations retain
unsupported legacy reset (4), GET_DEVICE_ID high-byte interface routing (2),
failed EP0 progressing to success (4), and SET_CONFIGURATION clearing its own
control request before status completion (4). Thirty-two BE wire mismatches
cover device self-power/remote-wakeup and both endpoint halt statuses. These
are executed compatibility findings, not successful USB transfers or a working
unmodified port. All expected packet lengths/bytes are independently specified;
known BE alternatives are accepted only in the baseline and recorded as findings.
Report: `analysis/usb-path/tinyusb-device/upstream-baseline.json/.md`;
log `/tmp/hp1020-tinyusb-upstream-expanded-20260929.log`; initial expanded captures
and exact source closure: `/tmp/hp1020-tinyusb-qyqzp2cv/`.

**Patched integration: 160 host/160 QEMU scenarios pass** with exact matching
wire proposals and no retained protocol findings. The narrow two-file patch:
- represents device status logically and serializes both two-byte replies in USB
  little-endian order, without normalizing captured bytes;
- supplies a private class routing hook for exceptional encodings, keeps the
  original request, requires an opened/configured interface and treats rejection
  as final instead of falling through to another driver;
- latches failed EP0 before data/status accounting or successful callbacks, stalls
  both directions, and rejects further submissions until a fresh SETUP;
- preserves active control context across configuration-only reset. Actual bus
  reset still clears that context.

The synthetic adapter owns a separate control epoch and original packet tokens.
Every new SETUP suppresses old deferred replies, including standard requests that
never reach the class. It settles independent borrowed EP0 storage before entering
new core state. Reset admission fences receive before a held packet can delay
dispatch and invalidates old reset promises. A current failure fences the receive
generation saved when that exact packet was submitted; reset status belongs to
the post-restart generation. Old/duplicate failures cannot borrow today's identity.
No stall or cleared C field is treated as physical cancellation acknowledgement.

Tests include interfaces 0/3, all four self-power/remote-wakeup combinations,
IN/OUT halt status, configuration 1→0→1, rejected route claims, address commit,
400-byte IDs, and 384-byte responses with exactly the required conditional DATA
ZLP. One hundred cases cover all five non-success results at first/middle IN data,
OUT status, address IN status and reset IN status, followed by fresh recovery.
Raw input and observations are saved before assertions. Each step checks owned
packet/class-response retention, document-memory guards and an unchanged full
storage hash. There are no bulk payloads or decoded pages in this protocol fixture.
Report: `analysis/usb-path/tinyusb-device/patched-validation.json/.md`;
log `/tmp/hp1020-tinyusb-patched-target-20260929.log`; first passing captures/source:
`/tmp/hp1020-tinyusb-jq4zqq27/`. Each current report pins 68 repository source files.

Three earlier target attempts stopped at build/audit gates: absent freestanding
`inttypes.h`, GCC's constant-false comparison when built-in class count is zero,
and SRC/MEMW outside the old auditor's emitted subset. The local include shim
supports only debug-disabled selected code; warning suppression is scoped to
upstream usbd.c. Exact original annotated SRC `0x10016f2b:054418` and MEMW
`0x10008211:0c0200` now guard admission of those standard instructions in both
compiler-profile and shared target audits. Custom opcodes, MMIO and divide-trap
allowances are unchanged. Exact failed sources/logs/builds, the earlier 44-case
baseline, expanded 52-case baseline and first patched 160-case run are retained
in `analysis/usb-path/tinyusb-device/source-snapshots/`, with member SHA manifests.
No report hash was patched to claim later source validation.

Full sequential validation passed **116 consistency checks and both suites** in
`/tmp/hp1020-full-tinyusb-20260929.log` (child `hp1020-validation.qvzwiA`). All
current source hashes in the new reports match. The previous pushed full baseline
was 113 checks at `eff3611`. Next connect bulk OUT to the existing bounded
document/decoder path through reusable C adapter code. Physical DCD cancellation, cache visibility, boot, bulk USB,
printer status and printing remain unproved. These scenarios add zero USB
transfers and zero native page lifecycles.

### Reusable protocol-to-document adapter (2026-09-29)

`open-firmware/tinyusb-printer-adapter/` now composes patched TinyUSB with the
existing class, four-slot receive queue and image output. Independent
`open-firmware/tinyusb-printer-test/` and
`scripts/validate-hp1020-tinyusb-printer.py --target` pass **98 sanitized host and
98 QEMU cases**, with exact known pixels, independently decoded JBIG fixtures,
wire packet oracles, retained ownership and byte-for-byte final receive/output
storage. Report/source closure: 76 hashes; target component state/fixed memory
128488 bytes, excluding code/stack/TinyUSB/test capture overhead. Target log:
`/tmp/hp1020-tinyusb-printer-target-20260929-run2.log`. No real DCD, USB transfer,
physical output or completed native page lifecycle is added.

The normalized receive API is applied; the raw descriptor wrapper keeps its
original checks and delegates only the validated count. Separate 75 host/75 QEMU
receive regression passed. The adapter retains original cookies through actual
TinyUSB dispatch; regular SETUP changes control identity without staling bulk.
Configuration/halt requests fence on admission before held EP0/bulk can delay
core dispatch; supersession does not erase a fence. Expected cancellation clears
BUSY without generating a new fault and erasing reset promises. Failed submission
retains its unconsumable reservation until explicit recovery. OUT shadow changes
require a fixture write, unlike immutable IN ownership.

Independent review found and corrected three pre-execution gaps: reserved endpoint
bits alias in the pinned core and must match admission; failed follow-on EP0
DATA/STATUS submission needs a fault even when the core drops its failure; and
unsupported control OUT data must be rejected before standard replies can become
expired stack receive targets. Sixteen follow-on failure cases include a
successful old-generation DATA packet that attempts a new-generation submission
following recovery. That new submission's generation owns the failure. Twenty-four
malformed OUT controls cover both interface positions/fills; no unsafe stack-write
execution was needed. The matrix also covers reset with retained EP0/bulk, stale
callbacks, deconfiguration replacement, four-slot backpressure, short/ZLP
fragments, consecutive documents, payload error, and initial/follow-on rejection.

Earlier 56-case host source, failed expanded-oracle attempt, first 98-case host
source and first target audit stop are preserved with member SHA manifests in
`analysis/usb-path/tinyusb-printer/source-snapshots/`. The oracle failure confused
a retained IN packet with a later bulk submission; it now uses the retained EP0
identity. Fixture alphabet modulus generated an extra libgcc trap and failed the
first target audit before execution. A simple alphabet loop removed that
test-only helper; the auditor was not loosened. Reports never have hashes patched
to claim that newer source was tested.

At that checkpoint, initial wire SOFT_RESET and explicit input close/finish were
still required. The continuous/recovery changes below remove those software
restrictions; three external settlement promises and synchronous output remain.
Full **118-check sequential integration and both suites pass** in
`/tmp/hp1020-full-reusable-printer-20260929.log` (child `hp1020-validation.quvweZ`).
The complete run regenerated all dependent reports and verified current source
hashes. No source was changed during execution. This completed aggregate predates
the continuous/recovery and descriptor changes below.

### Continuous-document and automatic-configuration work (2026-09-29)

The proposals following the 98-case checkpoint are now applied. Focused execution
passes **34 continuous host/34 QEMU, 132 adapter host/132 QEMU, 82 class host/82 QEMU,
45 output host/45 QEMU and 75 receive host/75 QEMU cases**. Unchanged/patched protocol
baselines also retain 52/52 and 160/160. The following full-suite attempt reran
all analysis execution with the final initial-standard guard, then stopped on
a stale memory-size gate described below. The second probe suite did not run.
Do not relabel the completed 118-check baseline as testing these changes:

- Existing semantic chunk callbacks run before subsequent bytes. Forward only
  validated END_PAGE/END_DOC through an optional image-stream boundary callback.
  Drain the final ring at END_PAGE using retained `output.plan`; do not wait for
  transport EOF or poll parser.document_open after a buffer. At END_DOC require
  all validated pages drained, then notify/count completion exactly once. Empty
  documents produce a zero-page event. Drain/notification errors retain ownership
  and stop before the next START_DOC. Explicit finish remains stream shutdown;
  it must not be invoked on ordinary END_DOC. Preserve callbacks on document
  restart and include original receive generation in external completion identity.
  Test adjacent boundaries in one buffer, new BIH geometry, fragmented boundaries,
  partial/malformed next documents, retained-output/notification failures and
  counter saturation. A valid END_PAGE before truncated END_DOC now drains pixels
  but must not report a completed document. Copies still remain metadata.
- Add one class-owned begin-transport-recovery path without fake SETUP or replies.
  Use independent nonwrapping recovery identity and optional real request linkage;
  reuse three current-ticket promises. A newly established configuration binding
  creates automatic recovery once; a generic fenced-and-mounted poll must not.
  Bus-reset admission invalidates old class reset/reply permission immediately;
  remain stopped until actual configuration opens endpoints. Same configuration
  must preserve current input. A superseded pending deconfiguration stays fenced.
  Real SOFT_RESET and automatic recovery supersede one another through recovery
  identities; only a current real request may produce an ACK. Test missing/stale
  promises, held EP0/bulk, post-binding faults, partial-open failure and independent
  identity exhaustion. Physical promises remain externally supplied.

Validated END_PAGE now drains all pixels even when explicit shutdown later
finds missing END_DOC. The medium truncation case captures 158400 exact bytes,
33 acceptances/completions and zero outstanding slots, but zero completed documents
and TRUNCATED. Output-progress failure at END_PAGE instead retains READY/ACCEPTED
slots and stops before END_DOC. Notification failure happens after validated
END_DOC but does not increment successful completion or parse following bytes.
Earlier successful notifications persist. New independent event tuples preserve
original receive generation through reset; coherent MAX-1 counter seeding permits
one MAX document then fails before wrap. Two-buffer failures retain both ready
receive slots, and explicit split-boundary ZLPs do not create completion.

The first continuous34 run and strengthened34 run retain exact reports/sources
and raw data under `analysis/usb-path/continuous-printer/source-snapshots/`.
The strengthened run adds actual split-END_DOC ZLP transfers, retained-slot
invariance and independently expected recovery generation. Automatic116 evidence
is under `analysis/usb-path/tinyusb-printer/source-snapshots/`. No source hash was
patched. Logs: `/tmp/hp1020-continuous-regression-{image-output,usb-receive,usb-printer,continuous-printer}-20260929.log`,
`/tmp/hp1020-automatic-printer-20260929-run1.log`, and
`/tmp/hp1020-continuous-protocol-{unchanged,patched}-20260929.log`.

A new configuration's first status proposal must be accepted before internal
recovery is allocated. Before-binding rejection creates no owner; after-binding
rejection retains/cancels the original owner. Polling or same-value configuration
cannot turn that failed attempt into recovery. A real rebind creates a new attempt.
The completed focused tests measure target state/fixed memory 128536 (adapter),
128256 (class), 128200 (receive/document) and 123988 (output); these exclude code,
stack and fixture capture overhead.

The initial standard EP0 submission gap is now reproduced and fixed. Adding the
16 regression profiles before the fix passed the preceding 116 host cases, then
failed at `initial-standard/descriptor/active-input`: service returned OK rather
than ERROR, retaining the failed original EP0 owner without fencing input. Log
`/tmp/hp1020-standard-submit-reproduction-20260929.log`, exact failed sources/events
`/tmp/hp1020-tinyusb-printer-4bdfwxef`. No target cases ran in that attempt.
The adapter now captures core BUSY at EP0 bind; a subsequent clear or software
STALL invalidates recovery promises and requests cancellation without releasing
the owner. Direct-DCD SET_ADDRESS has no BUSY transition and remains explicitly
outside that observation; normal direct-address ownership is tested. No-owner
rejection is not classified as a failed retained submission. The completed fixed
run passes **132 host/132 QEMU**, including all 16 new controls for active input,
promised recovery, successful/unsupported requests and direct SET_ADDRESS. Log
`/tmp/hp1020-standard-submit-fixed-20260929.log`, exact run
`/tmp/hp1020-tinyusb-printer-3m6u4fne`. Measured adapter state remains 128536 bytes.
Failed and fixed snapshots are preserved under the adapter's existing evidence
directory. This adds no USB transfers or physical recovery proof.

The full analysis attempt reached 120 consistency checks with one failure: the
stream gate retained an old 91028-byte expectation. The new boundary callback
adds four target bytes; the executed fixture measures state13192 + fixed
memory77840 = **91032**. All 66 host/44 target stream cases and exact hashes
passed. Updating the checker (not any report hash) gives 120/120 consistency,
but the stopped aggregate is not a completed 120-check run. Its exact old
checker/report/log evidence is preserved in
`analysis/offline-consistency/source-snapshots/stream-footprint-gate-20260929.*`.
Log: `/tmp/hp1020-full-continuous-recovery-20260929.log`, child
`hp1020-validation.5SQr6N`. The subsequent combined aggregate passes **121
consistency checks and both suites**, including the descriptor boundary and
pointer-model correction below. Log `/tmp/hp1020-full-udc-boundary-20260929.log`,
child `hp1020-validation.csAmPs`. This supersedes the118-check completed baseline
without changing the stopped120-check attempt into a success.

### Controller-facing RAM boundaries (2026-09-29)

`scripts/validate-hp1020-usb-idle-receive.py` now passes **58 conditional cases /
62 fresh helper invocations per engine**, six unredirected-MMIO controls per
engine and 15 excluded-code controls. Original helper `0x10008f40..0x10008fb0`
runs from real ENTRY to return; three register literals are privately redirected,
and interrupt-mask/unmask/delay services are supplied. Independent traces and
all nonstack mutable bytes agree. Original instructions/13-file closure remain
unchanged. It skips on RXFIFO_EMPTY or nonzero latch, otherwise requests SNAK,
sets the latch, supplies delay 5/50, then rereads DEVCTL and sets RDE. A supplied
RDE-clear at the delay boundary is followed by that fresh read/set; this is not
a proven reachable stock race or physical quiescence.

Report: `analysis/usb-path/idle-receive.json/.md`; exact passed and initial
pre-case socket-failure captures/source archives are in
`analysis/usb-path/idle-receive/source-snapshots/`. Passing log:
`/tmp/hp1020-usb-idle-receive-20260929-run2.log`; captures
`/tmp/hp1020-usb-idle-receive-57er5ibi`. No instruction-audit/guard expansion,
peripheral access or new hardware permission was required. A future controller
port must settle delayed receive-enable work before promising quiescence.

`open-firmware/udc-out/` and `scripts/validate-hp1020-udc-out.py` now connect one
stationary 16-byte OUT descriptor to the existing adapter and receive queue.
The first focused run passes **34 sanitized host/34 QEMU scenarios**, with
97 exact source files, six fixture inputs, independent BE descriptor/USB wire/
JBIG pixel/document event oracles and full retained-storage captures. Target
component plus descriptor uses **80 bytes** beyond adapter128536. Exact first
sources/report/captures remain under
`analysis/usb-path/udc-out/source-snapshots/first-34-cases.*`;
log `/tmp/hp1020-udc-out-first-20260929.log`, captures
`/tmp/hp1020-udc-out-kp273xzi`.

The boundary retains the original adapter cookie by value, never allocates a
new queue or transfer identity, and uses separately supplied CPU/DMA spans.
It supports one 64-byte OUT1 packet. Successful completion retires only the
descriptor record; actual TinyUSB dispatch and queue parsing remain separate.
Normal END_PAGE/END_DOC produces exact pages and consecutive document events
without EOF. The 384 owner/RX/L/count combinations, unknown/nonboolean facts,
span rejection, publication/submit failure, cancellation and original-cookie
replay after descriptor/receive-slot reuse all execute in both engines.

A review then strengthened the existing completion-facts profile in both
directions: replay a current busy snapshot after live bytes become complete,
then replay a saved complete snapshot after live bytes become busy. These require
the immutable observation to govern admission. The first34 archive remains the
unmodified earlier evidence; the stronger validator also passes all34/34
cases (log `/tmp/hp1020-udc-out-snapshot-authority-20260929.log`, captures
`/tmp/hp1020-udc-out-lrkw40ly`).
Neither run establishes the externally asserted mapping or settlement facts.

Original rearm writes buffer address big-endian (`0x10008708..0x1000871a`), clears
next (`0x10008766..0x1000876f`) and writes status `0x08000000`
(`0x1000877f..0x100087a6`). Pinned Linux `snps_udc_core.c:774..787,887..895` builds
max-packet descriptor chains in packet-per-buffer mode. OUT status low bits are
returned count, not requested capacity. Existing 1024-byte synthetic DCD cases
therefore do not prove one-descriptor hardware reception. Stock OR `0x320` does
not establish initial BF/DU state; mode selection (`:1890..1899`), DMA translation,
cache visibility/publication order, stable original-cookie snapshots, transfer
settlement, IRQ acknowledgement and queued-event retirement must remain supplied.
BNA/HE faults, owner/RX/L/count controls, rejected publication, stale snapshots
after descriptor reuse and cancellation without settlement are exercised, with
zero new original page lifecycles, physical USB transfers or peripheral accesses.
The component initializes reserved bytes to zero, whereas stock preserves them;
its acceptance policy is intentionally stricter than the original owner/count
fragment. It reuses the completed 12 rearm/51 status reference cases without
claiming new original execution.

The EP0 seam is now executed. `scripts/validate-hp1020-usb-ep0-construction.py`
passes66 conditional profiles in both the guarded interpreter and QEMU:
36 descriptor constructions,12 pointer-only,16 pre-MMIO and2 excluded-length65
controls, with18 excluded-PC controls. The10-source closure, literal BE16-byte
oracles, ordered writes, every read, registers and all mutable RAM including
stack agree. These are explicit mid-function register/RAM cuts, with no original
ENTRY, copy/cache helper, service substitutions or literal redirects. All
peripheral accesses stop before execution. Captures:
`/tmp/hp1020-ep0-construction-rzkl2u5c`; log
`/tmp/hp1020-ep0-construction-first-20260929.log`; durable report/snapshot:
`analysis/usb-path/ep0-construction.json/.md` and its `source-snapshots/` directory.

Active IN0 pointer submissions preserve the supplied low/high pointer. Separate
initialization adds0x80000000 modulo32; the earlier OR/physical-alias label was
wrong. Neither path proves a DMA address translation. The ADD-only execution
does not claim HOST_BUSY construction. The corrected legacy static model retains
its separate pre-correction snapshot and contiguous original byte anchors.

`hp1020_tusb_adapter_packet_fault` now uses an exact retained cookie and its
correct control/transport domain. A current fault fences input/recovery and
requests cancellation while retaining storage. A later real EP0 SUCCESS cannot
submit another packet or acknowledge the faulted request. Superseded/retired or
older-generation cookies are STALE, never permission to settle. Generation2 can
be active while generation1's configuration status is still borrowed; that old
fault must not stop generation2 bulk input. Actual settled cancellation still
retires the old owner. The20 host/20 QEMU focused profiles cover this, direct
SET_ADDRESS, data/status faults, promise invalidation, repeated/mutated cookies,
reentry, bulk behavior and terminal identity limits. Target state stays128536.
Report: `analysis/usb-path/tinyusb-printer/packet-fault-validation.json/.md`.

The first packet-fault run completed20 host and20 target profiles, then failed
its final artifact gate: a copied preexisting annotated-disassembly listing was
rewritten by the audit for the captured ELF/path. It emitted no success report.
The ELF and other build bytes were unchanged. The generator now omits that
stale derived file when copying build outputs, checks build hashes across audit,
then captures the freshly generated listing and checks every artifact through
replay. Failed `/tmp/hp1020-tinyusb-packet-fault-5v523_sg` and successful
`/tmp/hp1020-tinyusb-packet-fault-vs8yc_mm` sources/captures are archived separately;
logs `/tmp/hp1020-packet-fault-{first,fixed-capture}-20260929.log`.

`open-firmware/udc-ep0/` now passes50 sanitized host/50 QEMU scenarios. Each of
IN0/OUT0 has a stationary16-byte descriptor and separate64-byte packet allocation.
Actual TinyUSB submissions bind the original pointer/cookie; IN bytes copy only
into separate staging. Publication exposes that staging, preserving original
borrowed bytes and unused tails. OUT supports status ZLP only. Actual TinyUSB
handles response splitting, DATA ZLP and status direction. No new queue, cookie
allocator, fake completion, SETUP record parser or hardware action is added.
Target component/allocation overhead296 bytes beyond adapter128536;92 exact
sources/six fixtures. Report: `analysis/usb-path/udc-ep0/validation.json/.md`.

The50 profiles cover split responses, short and zero packets, direct SET_ADDRESS,
continuous documents, recovery,448 owner/status/count combinations, raw boolean
facts, delayed publication, malformed descriptors, explicit faults and settlement,
span/source alias rejection, cookie replay/reuse, superseded requests and an
old-generation retained status beside current bulk data. Both directions of
current saved-snapshot/live-storage disagreement are exercised. The original
borrowed buffer is checked immediately after each settling call, before the
fixture clears its independent live flag; staging/wire cannot mask corruption.
IN completion low16 deliberately differs from the independently supplied actual
count; descriptor fields alone never establish success, visibility or settlement.

The first EP0 run passed all50 host cases then stopped before target compilation
because the imported draft builder retained `/tmp`-specific paths. Exact capture
`/tmp/hp1020-udc-ep0-srkbp5vo`, log `/tmp/hp1020-udc-ep0-first-20260929.log`.
Only the build integration changed before the subsequent50/50 success, log
`/tmp/hp1020-udc-ep0-integrated-build-20260929.log`. Both source closures and raw
captures are preserved in the EP0 report's `source-snapshots/` directory.

The full sequential aggregate now passes124 consistency checks and both suites,
including the original construction, packet-fault and EP0 gates. Log
`/tmp/hp1020-full-ep0-boundary-20260929.log`; child `hp1020-validation.JolOPF`.
It follows the committed/pushed121-check baseline `bcec270`. Pre-aggregate checks
had exactly five stale source-closure failures; regenerating through the full
suite resolved them without changing reported hashes by hand. The bulk report
generator now writes compact JSON to avoid an unnecessarily large text artifact;
old report bytes remain preserved in the existing exact snapshots.

The following checkpoint implements the next practical seam: one immutable SETUP
capture into existing adapter dispatch, composed with EP0 and bulk descriptors.
Existing70-case
SETUP execution already owns the byte/admission evidence; do not repeat it.
A SETUP capture has no transfer cookie yet. Exactly-once ordered capture identity
must distinguish a replay from a genuinely identical new request and stale
pre-reset input from retained post-reset retry. Copying a stable CPU-visible
record does not settle old EP0 storage, clear hardware stalls/toggles or rearm
SETUP. Keep these caller-supplied facts explicit; no physical DCD exists.

The124-check checkpoint was committed/pushed as `a230fcc` before integration.
`open-firmware/udc-setup/` now holds one retained immutable observation and a
shared externally supplied monotonic SETUP/reset sequence. The composed fixture
is `open-firmware/udc-composed-test/`; generator
`scripts/validate-hp1020-udc-composed.py`. Its first completed focused run passes
34 sanitized host/34 QEMU cases, freezing117 source files and six fixtures before
execution. Report `analysis/usb-path/udc-composed/validation.json/.md`, log
`/tmp/hp1020-udc-composed-reconnect-helper-20260929.log`, captures
`/tmp/hp1020-udc-composed-ql5zodos`. Measured target component/allocation overhead
is EP0296 + bulk80 + SETUP88 beyond the adapter/document128536. All288 row values
except architecture-dependent base size, entire guarded storage, real TinyUSB
packet proposals, independent decoded pixels and document events agree.

The SETUP bridge copies raw wire bytes, original optional printer status, DMA
label, independent fault and sequence before admission. It never assigns packet
cookies or reinterprets raw wire fields as the original in-place converted bytes.
Exactly-once identities come from the future controller, not payload equality,
record addresses or the currently active control epoch. A held capture blocks a
newer one; rejected input remains caller-owned, with the same original sequence
retried after the old capture is admitted. Reset admission WAIT likewise retains
the exact original reset and prevents later requests bypassing it. Post-reset
captures can wait while an already admitted reset drains old owners.

Review identified that service/arm/pump gating alone is insufficient: finishing
an older class reset can emit a deferred ACK, and manual descriptor publication
can expose older prepared work. Both now require full progress permission in the
integration. Executed cases demonstrate those blocks and subsequent fresh page
success. Exact-cookie settlement remains independently allowed. At terminal
sequence exhaustion, component FREE and adapter PENDING states are observed
separately. The narrow service-only exception drains an already admitted reset
and then stops; no physical quiescence, implicit recovery or new USB completion
is inferred. Bulk and EP0 DMA labels are distinct across the combined allocation.

The first run passed12 host cases, then stopped in `bus-reset-retained-capture`
before target build: the inherited configuration helper required class request
identity0 and receive issued/count0, appropriate only for a fresh fixture. The
saved state instead retained prior class identity1 unchanged and one aborted
receive reservation until explicit recovery; deferred ACK was0 and guards passed.
Only the new validator's configure helper changed: it now checks unchanged prior
class identity, refused NEW reservations while fenced, all three recovery
promises and reclaimed ownership after restart. Failed captures
`/tmp/hp1020-udc-composed-dqriz2gg`, log
`/tmp/hp1020-udc-composed-first-20260929.log`. Failed/passed exact sources and raw
captures are preserved beside the report, never relabelled. Optional EP0 fixture
naming hooks subsequently passed50 host/50 QEMU standalone cases, log
`/tmp/hp1020-ep0-composition-hooks-20260929.log`; no old report hashes changed.

The composed independent consistency gate now passes, including event-derived
capture/sequence checks, literal descriptor/cookie oracles, every published IN
packet including ZLP, independent intended pixels/documents and terminal owner
states. Preflight `/tmp/hp1020-composed-preaggregate125-20260929.log` has exactly
one failure: the standalone EP0 report's prior fixture hash before the naming
hook rerun. That rerun and the independent retirement gate below now give a
passing126-check preflight, log
`/tmp/hp1020-composed-retirement-preaggregate126-20260929.log`. Full sequential
`scripts/validate.sh` subsequently passed both suites and126 consistency checks,
with zero failures: `/tmp/hp1020-full-composed-ingress-20260929.log`, child
`hp1020-validation.MPr6yY`. Research processes stopped at the owner's requested
checkpoint. Later saved drafts and static reviews below add no executed cases.

### Original post-dispatch SETUP retirement (2026-09-29)

`scripts/validate-hp1020-usb-setup-retirement.py` passed its first execution:
50 conditional tail cases and32 pre-peripheral guard cases in both engines,
plus15 excluded-PC controls. It uses the exact210-byte interval
`0x1000985c..0x1000992e`, SHA256
`1de51b81705babf558e94f732621f10677f423c86a0a6bac3fe1c84e54eaf1b0`.
This is a direct supplied-register/RAM cut after omitted request dispatch, with
`a2` as stall intent and `a3=0`; no original ENTRY, initialization, SETUP admission,
sender, IRQ, wait or cache path executes. Four peripheral-address literals point
only to private guarded RAM images. The existing MMIO guard remains active.

Report `analysis/usb-path/setup-retirement.json/.md`, log
`/tmp/hp1020-setup-retirement-first-20260929.log`, captures
`/tmp/hp1020-setup-retirement-2a9pf7bb`;13 source files preserved before execution.
All mutable RAM including stack, original instruction bytes, complete ordered
reads/writes and final registers agree with independent byte oracles and between
engines. Guard cases cover all nine direct controller-word instructions, four
removed redirects and three dynamic pointer escapes under both fills. Partial
legitimate writes before rejection are checked, not incorrectly assumed absent.

Exactly stall intent1 ORs bit0 into both EP0 control images and clears `a2`.
The global SETUP record's status word alone becomes0 at `0x1000988d`; its reserved
word and eight supplied post-dispatch bytes are untouched. The ordinary OUT0
status pointer is then independently read through DESPTR; owner2 alone permits
four byte stores of `08000000` through another global target. RX and all low
status bits are ignored in this original return fragment. Four mismatched-pointer
controls expose the supplied observed/target assumption and are not a proposed
replacement policy. Every other descriptor byte stays intact.

The tail then ORs `0x100` (pinned Linux CNAK bit) into the OUT0 control image.
The supplied bulk-size word at `0x1001bc50` selects the same OUT1 intent only when
unsigned value<=512; a latch byte at `0x1001bc72` becomes0. Existing S/NAK bits
are preserved. A register-oracle typo was caught by independent disassembly
before any execution: final `a9` holds the OUT1 image address, not the stored
value. The tested source already contains that correction; there was no failed
execution to relabel.

Pinned Linux copies SETUP words before returning its descriptor HOST_READY and
before gadget dispatch; the original tail has a different supplied cut/order.
Neither should be copied as a requirement of the independent replacement. The
executed tail proves command and RAM ownership-return intent only: CNAK does not
clear S in these RAM effects, and returning SETUP status does not settle an older
IN/OUT packet. Hardware automatic stall clearing/toggles, safe IRQ acknowledgement,
coherent capture, DMA visibility, physical rearm and cancellation remain open.
This adds zero completed USB transfers or native page lifecycles. Next inspect
IRQ/event order and overwrite protection; do not repeat SETUP70 or these82 cuts.

The independent aggregate gate reconstructs all82 supplied inputs, complete RAM
manifests, ordered accesses, every retired PC and all registers from fixed stock
byte/operand tables. It additionally checks the14 partially executed guard
prefixes against literal register outcomes, beyond the generator's paired-engine
comparison. Fifteen excluded PCs, all13 current source hashes and immutable
Linux provenance remain checked. Both full sequential suites and126 consistency
checks now pass, including this gate and the composed fixture above.

### Original IRQ capture cuts (2026-10-02)

`scripts/validate-hp1020-usb-irq-capture.py` passed its first execution:44 separate
conditional cuts and38 pre-MMIO guards in each engine, plus75 phase-specific
excluded-PC controls. Before execution only its obsolete UNEXECUTED docstring
label changed from the committed draft. Reports are
`analysis/usb-path/irq-capture.json/.md`; log
`/tmp/hp1020-usb-irq-capture-first-20261002.log`, capture
`/tmp/hp1020-usb-irq-capture-jsuu8up_`. All13 source files were frozen and checked.
The independent gate passed unchanged, then its function was integrated into
`scripts/check-hp1020-analysis-consistency.py`; the redundant draft file was
removed. Its exact original bytes and SHA256
`0334e8ef6f7f6689dac6ace424db292584a942af03fbfbcf02c0d70f0f6d30a7`
remain in `analysis/usb-path/irq-capture/source-snapshots/first-82-cases.tar.gz`.
That archive preserves every839 capture file, the log and gate, with all3636
reported memory-region digests checked against492 raw RAM files and all841
archive members rehashed. The prior `draft-review.tar.gz` preserves the exact
static integration note and original-byte review; each archive has its own
member manifest. Full sequential validation passed both suites and127 consistency
checks: `/tmp/hp1020-full-irq-capture-20261002.log`, child
`hp1020-validation.Q3TpQv`. The generator/report source hashes remain exact.

The three cuts remain separate: original sampling ENTRY stops before reset
configuration or later device processing; a supplied saved-EPINT frame enters
endpoint selection; a supplied post-helper OUT0 continuation reaches wake intent.
No omitted helper executes. Static review found suffix-mask selection, rather
than per-endpoint pending-and-enabled filtering: a masked OUT0 can be selected
when a higher OUT1 remains enabled. All acknowledgement stores are RAM intent,
not W1C or physical chronology. The independent original-byte review is archived
as `hp1020-irq-capture-independent-review-20260929.md`. Before execution the
draft was narrowed to exclude the unused IN1 prefix at`0x1000841a` and its
original ENTRY state corrected to WOE1/CALLINC0/WB0/WS1; both corrections are
in the exact tested source snapshot. No failed execution exists to relabel.
Complete mutable RAM, ordered accesses, all logical registers/SAR and native
PS/window/loop state match the oracles. Error and TDC acknowledgement values
derive from one saved status word; their RAM writes do not change that snapshot.
The separately supplied wake continuation reads no SETUP record/pointer and
returns no descriptor ownership. Do not stitch these cuts into a reset or IRQ
lifecycle, assign reset generation from scan order, or count them as native pages.

[Official family manuals](../usb-path/controller-reference/manuals/README.md)
now supply bounded stall-clear, SETUP-overwrite and receive-stop evidence with
exact download hashes/pages. SETUP ownership does not prevent overwrite; the
record has no event counter. RX stopping at a documented OUT interrupt still
requires serialized receive-enable writers and actual CPU-visible completion.
It cannot establish arbitrary cancellation settlement. A separate global PIO
backend remains possible, but the bounded stock search found only the better
supported DMA path. Do not switch from descriptor ownership to an unverified
FIFO implementation merely to avoid the capture question. No manual identifies
HP silicon/revision or discharges current external component facts.

### Next implementation seam: hardware-handled standard requests (2026-09-30)

Static manual/source reviews are complete, with exact notes and stock annotation
cache preserved in `analysis/usb-path/controller-reference/manuals/static-review.tar.gz`
and its member manifest. The neighboring README summarizes page and code anchors.
These are family-derived facts and design proposals; the static reviews add no
target execution or physical controller evidence. The separate IRQ experiment
above is now complete; do not repeat its sampling/selection investigation.

The controller-family references handle SET_ADDRESS internally, and expose
SET_CONFIGURATION/SET_INTERFACE through SC/SI notifications with4-bit sampled
CFG/INTF/ALT fields. In dynamic CSR mode, CSR_DONE grants a hardware status ZLP
after endpoint programming; it is not host ACK. Linux reconstructs canonical
requests because the raw application SETUP path does not carry these requests.
Original HP comparisons omit all three standard tuples; inspected startup masks
SC/SI and programs static endpoint CSRs. This fits static hardware offload, but
its DEVCFG write preserves the inherited CSR_PRG bit, so the initial mode and HP
dynamic-CSR capability remain unproved. Do not blindly transplant that mask.
The2026-10-02 startup review narrows this uncertainty: the omitted ready helper
only waits on an event, the creator passes argument0, all identified direct
DEVCFG stores preserve CSR_PRG and all identified direct DEVCTL stores preserve
CSR_DONE. Under the family read-zero rule they never grant status permission.
The undocumented wrapper pulse still does not prove a reset/default mode.
`manuals/offload-mode-review.tar.gz` (relative to the controller-reference
directory) preserves exact review/disassembly/anchor bytes. A dynamic-gate
fixture must require supplied capability/mode independently from the fact that
hardware decoded a request. Repeating these arithmetic operations in RAM would
not resolve the initial-state question.

Likewise, TDC/descriptor DMA_DONE describes data moved into TxFIFO. The controller
can retain that copy for USB retries after source memory is released. Sony's
PPBDU TXBYTES statement permits a mode-dependent DMA packet count, not a host-ACK
count; do not claim the field is always input-only or require an unavailable wire
counter. Newer Sony FIFO-empty bits are absent/reserved in the older references
and cannot be assumed on HP. TinyUSB's data continuation, status callback and
controller memory release require separately justified meanings. Keep supplied
`in_actual` and settlement unchanged until that API choice is explicit.

The revised typed fixture passed58 sanitized host/58 QEMU profiles (2026-10-02),
with126 frozen sources, six document fixtures and5422 paired368-word event rows.
Complete wire, pixels, document notifications and all guarded captures agree.
Target sizes are adapter/document128588, EP0296, bulk80 and SETUP96 bytes.
First captures, exact tested sources and the first independent gate are under
`analysis/usb-path/udc-offload/source-snapshots/first-58-cases.*`.
The neighboring `unexecuted-proposals` archive preserves the untouched V1/V2
proposals and source-derived reviews. These are zero physical/native lifecycles.
V1 incorrectly followed pinned TinyUSB's repeated-configuration shortcut. USB2.0
§9.1.1.5/§9.4.5 require affected endpoint defaults/toggle/halt reset even for the
same nonzero selection. Official provenance is in
`controller-reference/manuals/usb2-spec-provenance.json` relative to `usb-path/`.
The revised local protocol patch reinitializes that binding after admission
drains original owners, preserving control context and bus connection/address.
The raw adapter expectations and the unchanged/patched protocol comparison are
updated accordingly; old reports retain their exact historical source hashes.
Raw and typed partial-open failures now retain the original programming-cleanup
ticket through later requests/reset. Sequence0 denotes raw provenance, with its
nonzero original control/transport identity retained. No reset supplies cleanup.

The small **typed reconstructed offload-event** fixture is separate from
raw16-byte SETUP provenance but sharing one original external sequence with raw
SETUP and actual reset. It tests config1, same-config repeat, config0,
interface0/alt0, unsupported values, failed endpoint programming, delayed grant,
newer raw SETUP before grant, reset overlap and sequence exhaustion. It checks exact
TinyUSB config/open/close behavior and one grant for the exact accepted current
event, with no fabricated raw capture, extra EP0 DMA descriptor or second wire
ZLP. SC/SI must not impersonate reset or manufacture three recovery promises.
The58 profiles execute these controls at fills0/204 and interface0, including
raw IN-open failure, typed OUT/IN failure, cleanup replay after reset/new failure,
halt-sensitive SI grant, retained owner through generation restart and repeated
nonzero configuration close/reopen with exact fresh-document recovery. Only
external sequence and transport-epoch saturation are exercised in this fixture.
Unsupported notifications remain held until actual reset; no generic rejection
policy, auto-owner success completion, real CSR write or physical ACK is supplied.
Focused raw adapter132 and protocol52 unchanged/160 patched also pass. The
unchanged core now independently exposes18 protocol findings and40 BE status
mismatches; patched has zero. Exact regression sources/captures are archived
under the existing TinyUSB evidence directories. The full sequential suite passed
128 consistency checks and both suites on2026-10-02; log
`/tmp/hp1020-full-offload-20261002.log`, child `hp1020-validation.LBojdq`.
The full58/58 rerun and corrected PDF-locator source closure are preserved under
`udc-offload/source-snapshots/full-suite-58-cases.*` (relative to `usb-path/`).
The stronger independent gate passed; eight deliberately corrupted copies were
rejected for their intended reasons. The unchanged first captures and gate-review
archive retain the initial oracle corrections and exact historical bytes.

The existing adapter's configuration recovery expects an accepted status owner;
returning success without one is insufficient. The tested conditional path binds
a no-buffer auto-status owner, proposes status permission after supplied programming
facts, and retains that owner until explicit settled cancellation.
Existing recovery permits such a held configuration status while the document
path restarts. These are software observations, not proof that a new request/reset
settles HP hardware. A Linux-like early software giveback would need a distinct audited
completion contract, not silently weaker evidence. Stale handlers must never
grant a newer request's status. Four-bit state cannot recover malformed SETUP
high bits; sampling stability, rejection policy and controller mode stay explicit.

Ordinary raw SET_INTERFACE is now separately reproduced against the128-check
checkpoint: four sanitized host/four QEMU conditional observations and404 paired
288-word rows show raw SI0 fenced and given ordinary status without binding
recovery. Input stays stopped; a separately requested SOFT_RESET then establishes
new recovery and a fresh exact document. The observer reused the exact validated
composed ELF and117-source closure without rewriting its shared report/target.
Complete sources, captures and later-recovery distinction are preserved in
`analysis/usb-path/udc-composed/source-snapshots/raw-si-before-policy.*`.
The old core fallback ignoring alternate/high-index aliases remains source-derived.
USB2 §9.4.10 permits STALL for a sole-default interface. The corrected adapter
handles rejection through the normal request-state path without destructive
bulk fencing, preserving typed SI's separately conditional acceptance.
Returning false from the class callback alone causes TinyUSB's success fallback.
Preserve any old fault/recovery and settle original EP0 ownership; rejection
must not claim completion or clear bulk halt/default state. Direction is ignored
when wLength0, so its alias is not itself a malformed-direction finding.
The reviewed V2 policy and28 new composed cases passed focused62 host/62 QEMU
execution, followed by58/58 typed-offload regressions. They test uninterrupted exact document input across
corrected rejection, old EP0 settlement, aliases, fresh control recovery and
existing pending reset. Pre-integration source reviews and untouched
unexecuted C/scenario/observer proposals are archived under
`analysis/usb-path/udc-composed/source-snapshots/raw-si-unexecuted-proposals.*`.
V2 is a full patch against the current source, not an incremental V1 patch.
The first corrected matrix stopped after46 host cases: a scenario expected
SOFT_RESET service WAIT, although class reset can begin deferred recovery before
bulk settlement. Raw rows and existing control flow confirmed retained original
ownership, no status and an active recovery; only the scenario changed, adding
finish-WAIT before settlement. Production V2 stayed unchanged. The failed and
successful full-source captures are in `raw-si-first-oracle-failure.*` and
`raw-si-first-62-cases.*`; the unchanged independent gate passed and eight
negative controls were rejected (`raw-si-independent-gate.*`). The initial28-case
plan does not separately cover retained raw-SI STATUS/late SUCCESS or supersession
of an already pending destructive request; retain those coverage limits.
Root owns all execution. The raw-SI full sequential rerun passed128 consistency
checks and both suites in `/tmp/hp1020-full-raw-si-20261002.log`, child
`hp1020-validation.Kd7EIu`. Its62/62 composed and58/58 typed-offload sources,
raw captures and full-suite logs are preserved in their existing
`source-snapshots/raw-si-full-suite-62-cases.*` and
`source-snapshots/raw-si-full-suite-58-cases.*` archives. Preserve the generated linker
map fill-line whitespace as exact build evidence; source/prose checks are separate.

### Endpoint register-command backend (2026-10-02)

The first integrated `udc-program` run passed **28 sanitized host/28 QEMU cases**,
1876 paired rows, with134 exact source and six fixture identities. The freestanding
C backend connects real TinyUSB open/void-close callbacks and explicit typed-SI
selection to recorded logical register I/O. One-shot CSR_DONE permission is
consumed immediately before its write; no descriptor, status packet, completion
or ACK is manufactured. Measured target backend size is88 bytes. Five profiles
emit exact32-byte pixels and a single independently checked END_DOC record; all
other profiles emit neither. No new native page or physical USB lifecycle results.

The HP table is explicit: OUT1 +508, IN1 +50c; EP0 +504 and OUT1-alt1 +510 stay
untouched. Packet64/full-speed NE fields are independently derived. IN1's supplied
fixed64-word allocation is read and checked, never resized. Close records bounded
NAK, IRQ-mask and old-DESPTR-clear intent under prior quiescence; it does not prove
disable. Reads are queued independent observations, not simulated effects of
writes. No physical base address, register binding or mechanical operation exists.
The detailed contract and literal sequences live beside `open-firmware/udc-program/`.

Seven exact program facts retain logical I/O, mode, dynamic CSR, non-control
quiescence, complete table, geometry and safe IN-SNAK assumptions. Five grant
facts separately retain endpoint defaults, current physical gate and DEVCTL
stability. Even with them supplied, observed RDE1 waits before consuming
permission; it is never replayed through read/modify/write. Hardware can change
DEVCTL independently of a software lock. Cache/interconnect behavior, table and
FIFO validity, DATA0/halt, safe SNAK, actual status acceptance, enumeration and
printing remain unproved.

Failure latches the original sequence/control/transport ticket and exact uncertain
prefix, including sequence0 for raw requests. Actual reset can drain service but
does not erase failure or old open-command history. Explicit cleanup requires that
exact ticket, physical-clean promise and stopped/unmounted/owner-free software;
it supplies no document recovery promises. Stale/late cleanup cannot clear a new
failure. Consumed status permission is never replayed after a failed write/order.

Static V1 review found two holes before execution: malformed raw configuration
aliases can reach genuine callbacks, and raw SC0 after actual reset can skip close
while old programming history remains. Reviewed V2 latches the original failure
before I/O or status-owner creation. The first raw runner mistakenly wrapped a
multi-event helper in a single-event trace expectation; this was corrected and
its bytes preserved before execution. A separate review added cfg0 malformed-SC1
controls so first-open rejection is covered independently of void-close failure.
Production/scenario execution then passed on its first integrated run.

Durable archives under `analysis/usb-path/udc-program/source-snapshots/`:
`unexecuted-proposals.*` retains V1/V2, fixture/runner drafts and source reviews;
`first-28-cases.*` retains all first-tested sources, target, event streams and
eleven complete capture pairs per case; `independent-gate.*` retains a separately
frozen gate, its unchanged successful run and nine rejected corruption controls.
The first extra-ZLP negative control used the wrong IN-owner slot index; only that
mutation was corrected. It did not change production, the report or the gate.
First log: `/tmp/hp1020-udc-program-first-20261002.log`; raw scratch capture:
`/tmp/hp1020-udc-program-35ql5sej`.

Shared-suite integration and neutral source-comment edits followed the first run;
the runner now also captures the independent gate (135 sources). The full sequential
rerun passed **129 consistency checks and both suites**, with all28 paired case
rows/captures identical to the first run. Its raw-capture independent gate passed
again. Current report hashes were regenerated; the134-source first archive is
unchanged. Full log: `/tmp/hp1020-full-program-20261002.log`, child
`hp1020-validation.xVacWU`; program captures `/tmp/hp1020-udc-program-8hu8tsxd`.
`full-suite-28-cases.*` preserves all current sources, target, raw captures, logs
and the later integrated static review (no new actionable finding).
The existing adapter/OUT/EP0/composed/offload case rows and captures are unchanged
by optional fixture integration. Composed62/62 and offload58/58 full-run captures
are in their respective `source-snapshots/program-full-suite-62-cases.*` and
`program-full-suite-58-cases.*` archives. All archive members were read back.

### Synchronous OUT1 publication (2026-10-03)

The first complete focused experiment passed **40 sanitized host/40 audited QEMU
cases**,4784 paired event rows and440 paired raw captures. The independently
frozen gate passed unchanged in report-only and raw-capture modes. Measured target
publisher size is140 bytes; the reused backend88, adapter/document128588, EP0296,
OUT80 and SETUP96 remain separate. The first attempt had passed40 host cases before
missing disposable GCC headers stopped target compilation; no target image or
paired report existed for that attempt. Pinned binutils and GCC recovery restored
the tools, and the exact same144-source/six-fixture closure passed the retry.
No production/scenario execution correction was needed. Full sequential
`scripts/validate.sh` passed130 consistency checks and both suites. Full log:
`/tmp/hp1020-full-publication-20261003.log`, child `hp1020-validation.jisaBm`.
The full run's raw-capture gate passed again. Case arrays and capture identities
are unchanged for continuous34, class82, receive75, adapter132, composed62, EP050,
offload58, OUT34, program28 and publication40. Generated stack-usage path changes
remain recorded; no report hash was manually changed.

The wrapper checks the stopped/settled global-RX window BEFORE existing prepare
writes HOST_READY. It reuses actual adapter reservation and the original cookie,
explicit RX64/descriptor16 cache hooks and immediate DESPTR/CNAK/readback/RDE
commands. The full queue waits before any I/O. Direct, duplicate and out-of-window
callbacks cannot prepare or publish. A private duplicate probe runs inside the
original callback before unwind, after both successful and failed first calls.
There is no escaping proposal, second queue, replacement descriptor encoder or
physical register implementation.

Every post-bind failure retains its original cookie and exact successful prefix;
uncertain writes do not allow automatic reuse. Normal forward operations stay
blocked while exact-cookie cancellation and admitted actual-reset draining remain
available. Cleanup preserves nonzero fenced receive accounting and supplies no
recovery promise; only the later existing three-promise restart resets it.
Program selection keeps its necessary SERVICE-only readiness exception while
respecting the local publisher failure/active-call barrier.

The20 profiles x two fills cover both CNAK paths, fact/register/read refusals,
callback authority, progress barriers, original cleanup identity, cancellation/
reuse, NAK readback refusal and ten post-bind failures. Only measured size
words59/425/490 are omitted from496-word host/target equality. The gate rebuilds
the literal command/cache traces, retained failure/cookie state, complete receive
and descriptor memory and guarded27712-byte read/trace storage. Every case has one
independent32-byte FF page and END_DOC in G2/G3. USB/component cases add zero
native stock or physical page lifecycles.

Durable archives in `analysis/usb-path/udc-publish/source-snapshots/` retain
`first-host-toolchain-stop.*`, `first-paired-40-cases.*` and
`full-suite-40-cases.*`. Their sources and raw captures are separate; failed tool
recovery never relabels a tested source. `reviews-and-independent-gate.*` preserves
static reviews, both pre-execution gate versions, recovery logs and ten corruption
controls. Each control reseals an internally paired example; both report-only and
raw-capture modes reject its intended semantic violation. The archive stores
changed members plus hash-checked references into the first paired archive for
unchanged members. These controls are synthetic evidence mutations, not additional
firmware executions.
The older `udc-program/source-snapshots/unexecuted-publication-drafts.*` remains
unchanged and preserves pre-integration C/H, fixture, literal oracles, reviews and
runner fragments. The recovered nested baseline paths and historical README
template are described by that archive's metadata. Static fixture/runner review
preceded execution. Independent gate V1/V2 retain two pre-execution ABI corrections:
outer blocked-arm WAIT and existing EP0 descriptor-write op46. Neither correction
changed a publication literal or accommodated an execution result.

Classic full-speed64/BE DU0/BF0/THE0, complete global receive readiness, register
stability, exact mapping/cache-line isolation and physical settlement remain
supplied. Static primary/cache reviews and original-byte checks remain in the
previous stage's `source-snapshots/next-publication-reviews.*`. TinyUSB's weak cache
hooks are no-op success; stock DHWB/DHWBI helpers and initialization ADD do not
justify physical cache primitives or universal address translation. No command
trace establishes USB acceptance, hardware quiescence or printing.

The next useful boundary is post-device acquisition: acquire the original retained
descriptor16 and payload64 through mandatory hooks, order, copy actual CPU memory,
then reuse the existing OUT observer. Physical settlement remains separately
supplied. No caller snapshot/visibility flag should stand in for those operations.
Preserve old-cookie settlement while forward progress is blocked, original fault/
cancel ownership and historical observer tests. Earlier reviewed C/H V1/V2, the fixture/
codec/builder, independent32-profile plan and incomplete root runner fragments are
preserved in `udc-publish/source-snapshots/next-acquisition-proposals.*`. Its
`RESUME.md` records the remaining scenario/gate integration. V2 narrows init wording
only: adapter preparation and owners are checked; retained receive accounting is
never cleared. The completed integration and first execution are recorded below;
the earlier proposal archive remains an unexecuted historical snapshot.

### Retained OUT1 acquisition (2026-10-03)

The first focused experiment passed **32 sanitized host/32 audited QEMU cases**,
3372 paired event rows and384 paired raw captures. The independently frozen V2
gate passed unchanged in report-only and raw-capture modes. No production,
fixture, scenario or acquisition-checker correction followed execution. Full
sequential `scripts/validate.sh` retry passed131 consistency checks and both
offline suites. All eleven component host/target case arrays and raw capture
identities match their pre-run baselines.

`hp1020_udc_acquire.h` adds a152-byte target configuration/diagnostic object;
the original OUT object remains80 bytes, publisher140, backend88, EP0296,
SETUP96 and adapter/document128588. There is no second owner, queue, descriptor
decoder or cancellation implementation. The historical observer's locked policy
is shared, so old observer cases must remain separate regression evidence.

Normal acquisition checks the exact retained cookie AND actual adapter DCD owner
before mandatory descriptor16, payload64 and acquire-order hooks. It then copies
the real CPU descriptor once and uses the existing observer. The callback must
have unwound; private probes challenge actual callback/hook busy state without
writing a fabricated busy flag. Missing facts, malformed facts, PREPARED and
stale/FREE/PENDING identities leave the promised state/bytes untouched. Physical
settlement, stable mappings, safe complete cache-line envelopes and real acquire
primitives are still supplied; no hook return establishes them.

The fixture has separate immutable device images and deliberately poisoned CPU
storage. Every hook checks the actual original span and reconstructs allowed
visibility from independent input. NOT_PERFORMED changes no bytes; the chosen
UNKNOWN effect copies only half of that range. Failures retain the exact first
cookie/prefix and create no snapshot; retries report the latched fault without
running a cache tail. Later G3 success preserves the first G2 failure. A fully
acquired not-DONE descriptor instead returns WAIT and a later call acquires all
three operations afresh. This is explicit RAM behavior, not a simulated cache.

Exact old-cookie settlement remains possible while SETUP is held, after actual
reset admission or after an exposed publisher failure. Success ends only OUT
ownership; the adapter remains PENDING until service. Cancellation, owner
drainage, publisher cleanup and the three reset promises stay separate. Normal
acquisition protects all receive/recovery words before service and cannot parse,
consume, emit wire data, grant recovery or notify a document.

The16 fixed profiles use fills0/204, all four prefixes, zero/short/full packets,
nine fact refusals, five cookie mutations, real callback/hook reentry, same-
address reuse, both publication-failure phases and six acquisition-hook failures.
Each ends with exactly32 FF pixels and one independently reconstructed END_DOC
in its specified G2/G3. Only the held GET_CONFIGURATION profile emits IN01 and
OUT0 status. Its initial missing-facts dispatch WAIT retains the original request;
the later same-sequence full-facts retry admits once. These cases add zero native
stock or physical lifecycles. Four measured size words59/425/490/555 are excluded
from576-word equality and separately bound to actual measured target sizes.

`analysis/usb-path/udc-acquire/source-snapshots/pre-execution-integration.*`
preserves the completed scenario, root runner, independent reviews and gatesV1/V2.
V2 corrected the pre-execution held-dispatch ABI assumption, strengthened the
pre-service recovery invariant and seals actual materialized TinyUSB bytes in
raw mode. The independent literal oracle is unchanged. `first-paired-32-cases.*`
contains the exact152-source/six-fixture closure, target, inputs, full raw captures
and both gate logs. First log `/tmp/hp1020-acquisition-first-20261003.log`; captures
`/tmp/hp1020-udc-acquire-y7t6kkii`. All archive members were read back and checked.

The first full run completed execution but stopped at three stale exact source
counts among131 gates. The only new key was `hp1020_udc_acquire.h`: OUT97→98,
composed117→118, offload126→127. Independent static review confirmed that narrow
correction; OUT/offload gained explicit header membership, while composed's exact
union and all semantic/source/artifact checks stayed intact. No expected-result
or report-hash repair occurred. `first-full-consistency-stop.*` seals the first
acquisition run and aggregate failure; `legacy-count-consistency-stop.*` retains
all three affected raw captures and all eleven baseline reports. Successful
`full-suite-retry.*` seals the later capture `/tmp/hp1020-udc-acquire-4q8orm5x`,
both full logs, exact corrected generator, independent review and eleven-way
comparison. Full log `/tmp/hp1020-full-acquisition-retry-20261003.log`, child
`hp1020-validation.glwQ3y`; archive SHA256
`142c130b684e34d80b78960704ffb828d4fe64d4869759cc3e05a1c493055471`.

`copied-evidence-controls.*` preserves16 independently designed controls using
the unchanged V2 gate. Fifteen paired semantic corruptions fail both report/raw
modes; a sixteenth changes actual saved effective TinyUSB bytes and correctly
passes report-only but fails raw source sealing. Baseline raw checks pass before
and after. The delta archive verifies every unchanged reference against the
durable first-run archive. These controls execute no target firmware. Historical
UNEXECUTED comments in the frozen tested sources record drafting provenance;
the reports and exact saved source hashes establish their later tested state.

### One entry through a RAM document: unexecuted preparation (2026-10-03)

Current component tests link at synthetic20000000 and receive CPU/stack state
separately per call. The selected next experiment establishes its own standard
CPU state, call0 stack and all BSS, then runs the existing production RAM document
path continuously. No USB/MMIO/cache/TLB/engine operation or upload .dl is added.
This remains unbuilt/unexecuted; actual ROM entry, mappings and boot are unproved.

Root independently matched five saved original byte blocks,28 anchors,11 PT_LOAD
records and entry against the exact stock ELF. Original entry starts ENTRY before
normalization; the new entry instead uses a stack-free jump. Privilege, usable
owned loaded RAM, PC-relative literals and no asynchronous IRQ/NMI/debug event
are supplied. Dirty loop endpoints must not intercept the initial prefix before
LCOUNT is cleared. No original full cache/TLB initializer is admitted.

The proposed layout stays within original-declared main10003000..100351e0:
code/literals/input10007000..1000d000; initialized sentinel256 at1000d020;
state13496 at1000e000; owned stack8192 at10012000; mailbox1024 at10014040;
entry island10016780..100167e0 with entry100167a8; full production memory114704
at10016800..10032810. It deliberately reuses HP private runtime locations.
Six additional original-declared vector/interface islands hold new inert bytes.
Seven backing/capture envelopes do not replace the exact13 PT_LOAD/18 allocated
section permissions. Paint the whole envelopes, overlay file-backed bytes only,
then poison all three BSS spans and stack. Never zero NOBITS in the harness.

Independent literals were frozen before candidate review. Three supplied CPU
profiles and two nonzero BSS/stack paints yield six paired runs. Observe actual
after-normalization, pre-C, first production document-finish entry and own park;
full pre-C BSS scan/immutable checks, exact352-byte input, six64/32-byte fragments,
32 FF pixels and original event(1,1,0,1) are independent expectations. The event
must already exist before explicit finish. A const65-word compiler layout witness
must match separate hand-derived target32 offsets before state fields are read.
Compare all observed CPU fields/32 physical ARs/current aliases and full RAM,
including stack; two actual park self-jumps must produce no new effect.

The first stopped QEMU register-description probe executed zero instructions;
this binary does not provide the XML packet. Exact official QEMU11.1.1 source
pins establish INTENABLE110, logical aliases124..139, and no absolute-literal
mode. Binutils' optional-register map differs:37 is PREFCTL and83 is DBREAKC0
here, neither an admitted seed. Seed WB before all physical ARs and read back
aliases. The separate direct adapter allows one initial seed, then ordered
read-only captures/breakpoints/continues and two park steps. Preserve every
command/reply; no reset/call helper or addressed PC repair joins phases.

`udc-acquire/source-snapshots/next-entry-proposals.*` seals257 proposal/review
members, SHA256`8ebe9c82b7b75302268bbfed1c6c8684d1490b66bdd8a04db8f26a76792a5b26`.
Includes `/tmp/hp1020-entry-{startup,workload,layout-witness}-draft-20261003/`,
`/tmp/hp1020-entry-integration-20261003/`, audit V1/V2, literal plan/oracle,
original-byte/layout evidence and QEMU V1/reviews. Root runner V1/V2 and all
pre-execution corrections remain separate. Later QEMU V2 is frozen at
`/tmp/hp1020-entry-qemu-adapter-v2-20261003/`, correcting only cleanup,
partial-constructor identity and rejected-command logging; the capture-only
gate is still being drafted. Neither is claimed by the proposal archive.

Next: integrate/freeze the final drafts, first build and strict linked audit
only, then independently review actual call/callback/libgcc frames before any
execution.8KiB is a budget, not a proven all-input maximum. Preserve build/audit
failures and actual tool/header/libgcc closure. Run six profiles sequentially,
unchanged independent gate and frozen meaningful controls. Runtime must reject
accesses outside exact spans before effects. Source-only review and paired RAM
results add zero native HP or physical lifecycles.

### Original SETUP ingress and corrected legacy evidence (2026-09-29)

`scripts/validate-hp1020-usb-setup-ingress.py` passes **70 interpreter/QEMU cases**,
six pre-MMIO rejection controls per engine and 14 excluded-code controls. A fresh
original ENTRY is followed by an explicit PC cut and one private SUBPTR literal
redirect to guarded RAM; all live argument registers are poisoned at the cut.
64 primary cases cover four owner/four RX states, two asymmetric wire requests
and two fills. Six deliberately mismatched pointer cases expose distinct status
and packet pointer sources. Entire mutable nonstack memory and original code bytes
are checked. It stops before dispatch or ordinary OUT0 descriptor handling.

SETUP uses SUBPTR `0xb3000210`, distinct from DESPTR `0xb3000214`. Admission requires
owner 2 and RX zero. The original independently obtains packet storage through
`0x1001bbc0`, adds eight, and reverses only wIndex/wLength byte pairs. Raw wire bytes
must reach TinyUSB, which performs its own endian conversion. Static IRQ anchors
show repeated task wake hints, including paths without TDC; they are not successful
per-transfer completion or physical-quiescence evidence. Initial sandbox run
stopped at private socket creation; identical sources passed after socket approval
(`/tmp/hp1020-usb-setup-ingress-20260929-run2.log`).

Six old generators and the authored endpoint0 contract now distinguish raw/post-swap
fields, SUBPTR/DESPTR, EPCTL commands/EPSTS acknowledgements, packet-size words and
speed selection. SETUP/IRQ/MMIO mappings add 25/61/51 exact byte anchors. Original
control-IN descriptor submission PCs are corrected to actual stores. All 20 marker
and 30 bulk sequence classifications, 15/21-register allowlists and permitted
access/write masks remain unchanged; newly documented SUBPTR is still excluded.
Six focused scanner runs and five control-IN self-tests pass. Correction captures:
`/tmp/hp1020-usb-evidence-corrections-teaaomb4`. No hardware operation was added.

### Original controller pause/restore intent (2026-09-29)

`scripts/validate-hp1020-usb-pause-resume.py` passes **46 interpreter/QEMU cases**:
32 supplied pause/restore pairs, six noncanonical saved-word controls and eight
repeated-pause scenarios. Original functions `0x10009a10..0x10009a70` and
`0x10009a70..0x10009abc` run with only three address literals redirected to guarded
ordinary RAM. The delay call is a supplied boundary recording argument 200000,
without timer reads or elapsed time. Later register images are explicit inputs;
RAM command bits do not pretend to self-clear or acknowledge NAK.

Pause clears DEVCTL bit 3 (family TDE), preserves bit 2 (RDE), saves OUT1/OUT0
NAK bit 6, and requests SNAK bit 7. Restore always enables TDE and requests CNAK
bit 8 only when the saved word is zero. Noncanonical nonzero words also suppress
CNAK; repeated pause overwrites old saved state and is not nesting-safe. Exact
ordered reads/writes and all nonstack mutable memory agree with independent
oracles. Six removed-redirection controls per engine reject before peripheral
access; nine delay/caller/IRQ/other-code boundaries reject before execution.

This is command intent, not DMA quiescence. Neither routine disables RDE,
checks descriptor ownership, clears descriptor pointers, drains pending IRQs,
polls completion or resets DMA. Supplied descriptors/payloads are only canaries.
One direct pause call exists in `0x100121e4`; no direct restore call or aligned
file-backed pointer was found. The paired restore invocation remains a supplied
experiment condition, not an established stock reset lifecycle. Thirty-four
instruction anchors, seven literals and both whole function hashes are pinned.
Report: `analysis/usb-path/pause-resume.json/.md`; log
`/tmp/hp1020-usb-pause-resume-20260929-run2.log`; source/captures
`/tmp/hp1020-usb-pause-resume-7xx6l5wk/`. The initial sandbox socket failure
`/tmp/hp1020-usb-pause-resume-_3s25y3b/` executed no cases; retry used identical
sources with permission for the private local debugger socket.

The follow-up corrects the existing bulk-receive generator against 46 exact
byte checks: literals FC0/FC4/FC8/FCC are individual thread creation arguments,
not a descriptor extending into FD0/FD4/FD8. The latter words point to saved
OUT1/OUT0 NAK and the delay argument. The true thread name is `0x10003530`;
`0x10021588` stores OUT1's saved NAK. Parser registration is separate, using FDC
and the call at `0x10009b45`. `0xb300022c` is OUT1's family-matched max-packet
register, not an endpoint acknowledgement register. The generator and consistency
check now retain those separate meanings; no generated conclusions were hand-edited.

## Preferred raster bypass (2026-09-10)

After the owner asked for a faster approach and delegated the choice, research
shifted from expanding software matrices toward the stock-supported bypass.
`scripts/validate-hp1020-raster-bypass.py` owns the new evidence in
`analysis/hardware-boundary/raster-bypass.json` and `.md`. The preceding full baseline, including static byte audits and page-fixture
observations, passed **94 consistency checks** in `/tmp/hp1020-full-bypass.log`.
The software image/stream and raw-contract additions above subsequently passed the 98-check
aggregate; retain this older baseline as historical bypass evidence.

- Literal `0x1000647c` points to table `0x1001ce14`. Entry 32 at `0x1001d114`
  contains `[32,0x1001ce10,2,0,0x40000,2]`; backing u32 `0x1001ce10` is **1 in
  the stock ELF**. Original getter `0x10011178` executes and directly reads it.
- Original prepare `0x10014910..0x10014ae0` enables `video+0xc0` only when that
  getter returns zero and `work+0x36==0`. With the stock value it clears both
  the gate and `video+0xf4`. For BPP2/600, stride/window remain 1200, scale 1,
  output BPP 2 and chunk cap 4. A stale callback pointer remains harmless under
  the disabled gate in the tested fragment. Entry 32 is not assumed read-only:
  the generic writer's type-2 store can update it.
- 42 prepare/band cases cover BPP1 at 300/600/1200, BPP2/600 and an explicitly
  unsupported BPP4/600 control, stock 1 versus mutated 0, both `work+0x36` values
  and both RAM fills. There are 34 raw-buffer selections and **eight conditional
  stops before CALLX8**, never callback successes. BPP1/300 clears the pointer;
  separate pointer-zero controls also suppress calls. Enabled unsupported BPP4
  retains a stale pointer, which is not format support.
- The band fixture enters `0x10013f57` after the excluded peripheral-read prefix.
  It stops at `0x10014014` with the raw slot pointer in a12, or before the excluded
  custom call at `0x10013ff9`. Explicit ring indices, non-final descriptor and
  raw/transformed buffers are supplied. Both buffers stay unchanged. The first
  peripheral read, custom call, callback entry and downstream hardware branch
  are separately rejected before execution. No image data is produced.
- Two original constructor relocation fragments `0x10010dcd..0x10010e80` change
  entries 0..22 only and preserve entry 32/value 1. Allocation is supplied RAM;
  the rest of construction, persistence and boot are excluded. This is a useful
  narrowed boot question, not proof of live configuration.
- The alternate work flag is not an interchangeable host setting: the byte
  audit at `0x1000e64c` shows `work+0x36` also suppresses JobMgr's four BIH-field
  stores. Keep its normal zero value for the initial bypass candidate.

The static pointer audit distinguishes compressed payload `+0x54` sent to
channel A (`0xb2040004`) from the video-slot pointer sent to channel B
(`0xb2080004`). The bypass forwards the latter slot toward the video block
(`0xb1000008`). No hardware accesses execute in this audit. Actual transformation
between those buffers, cache visibility and physical consumption remain unknown;
the bypass does not turn the compressed stream into ready image rows by itself.

All 36 existing native page cases also preserve entry 32's full descriptor and
value before and after execution, without reseeding either. This is a before/after
observation of the selected software
tasks, not a trace of every write or an invariant over unexecuted boot/engine code.

The callback inventory's former "Default BPP2/600" wording was too broad.
Selection requires datastore 32 = 0; file-backed stock has 1. Existing prepare,
first-page and dataflow projections keep their zero-setting values as explicit
conditional scenarios. Do not silently substitute them for the bypass. Prefer
the narrow BPP2/600 bypass path and revisit custom decoding only if evidence
shows it is necessary. Exact custom encodings/masks remain preserved in the
callback and instruction-property reports, not reclassified as safe.

Next useful evidence: original initialization/writer reachability for entry 32,
and the raw-buffer hardware contract at the compressed-input/output boundary.
Do not repeat the callback inventory or empty-document cancellation ordering.
No permission for any printer contact or hardware operation was added.

A separate original-byte inspection found a concrete output-mode boundary:
literal `0x100067c8` points to selector `0x1001cdac`, whose file value is **2**.
Function `0x10016024` first passes command `0x92` to `0x10015c68`, then classifies
the returned value masked with `0x7e00`. Masked `0x3400` selects 1; `0x1a00` and
`0x3200` select 0; other values select 2. The literals are at `0x10006984..0x10006990`;
the selector stores are `0x10016049` (`2ac600`, a10 to a12) and `0x10016085`
(`289600`, a8 to a9). The value-1 branch first reads `0xb0500004` and later sets
its `0x10000000` bit, so it is not a safe complete RAM fragment. Whole original
bytes `0x10016024..0x1001608a` SHA-256:
`c3b538565dd5de4b2a05d9ea1b4e5dc916dd500608622671edbe2e3afa26c9f5`.
This is a static control-flow finding only; the command and engine initialization
were not executed. The physical meaning of the response and the selected live
mode remain unknown. Existing lane-0/1 projections are conditional examples,
not proof of the live selector. A future bounded classification test must supply
the response explicitly and stop before the value-1 branch's peripheral read.

The owner has reframed the task as an offline capability evaluation. Original
stock parser/libc and status routines now execute in isolated host harnesses and
challenge the inferred models directly. These harnesses intercept all device
I/O and record explicit environment substitutes; passing them does not answer
the live questions above. Continue looking for independent binary-derived
checks before requesting physical assistance.

Original JobMgr replay now preserves full page/raster lists, BIH fields and
credit-limited page scheduling against C/input oracles. Split-BID execution exposes
a marker-initialization question: nonfinal payload `+0x4c` inherits allocation
contents through `+0x2c`; END_JBIG overwrites only the final marker with 1.
Separate original type-1 allocator execution confirms it preserves payload bytes.
All 256 tested MMIO-free compressed-render paths ignore this marker; the known
nonzero-to-hardware-flag consumer is alternate raw refresh `0x100140f8`.
Do not infer a physical failure, a zero-fill guarantee, or a new first-printing
blocker. Original render also changes list pointers before busy rejection; the
ring model ordering is corrected. See `stock-execution/jobmgr.md` for boundaries.

Original completion/release and datastore bookkeeping now execute under
serialized and cooperative queue-boundary schedules. The host explicitly
injects successful FIFO completion; it does not model DMA/engine success.
Nonempty jobs drain and recover credits. A conditional counterexample exists:
queuing an empty document behind an unfinished page can make the empty-document
finalizer free the global head; later completion reads a missing child. Eager
completion avoids it. The parser itself locks a producer mutex without waiting
for the job list to drain. Original single-language recognition, pushback, buffered
reads and dispatcher now reproduce that admission and failure across input splits,
including cooperative execution. The broad software-admission question is reduced
to actual transport delivery, multi-language state and RTOS/engine ordering.
Exact scopes and assumptions: `stock-execution/lifecycle.md` and `stock-execution/admission.md`.
This is an offline correctness question, not evidence of a physical printer fault.

Independent QEMU now checks the same compiled C target, all original libc cases
and stock signed/unsigned division/remainder helpers. Original parser messages
and JobMgr lifetime/global RAM also agree, and QEMU reproduces the delayed-empty
cleanup fault. All six original window spill/fill handlers run under nested
CALL4/8/12; corrupting a saved return store is detected. These tests use a synthetic
ABI stack and a different core configuration, not stock boot/interrupt/cache
state. Original status ownership and selected interruption producers now execute
as described below; actual scheduling and hardware stopping remain unverified.

Original constructor analysis corrects a major inherited error: queue 0 is engine,
queue 1 is PrintMgr, and JobMgr queue 3 uses object `0x10023e40`. The former
missing-consumer conclusions for engine event `0x17` and datastore `0x2d` were
routing errors, not hardware blockers. PrintMgr now executes under both CPU
engines: cancellation advances states 0 -> 1 -> 2 -> 0 on two injected stop
acknowledgements and frees only its own list nodes. Its original subscriptions
and datastore writer emit ONLINE changes to queue 1; the original consumer
updates its online byte. StatusMgr releases the remaining JobMgr completion
notices, leaving no tracked live allocations in selected completed lifecycles.
See `stock-execution/printmgr.md` and `stock-execution/notifications.md`.
Original engine cancellation queues acknowledgement 37 before calling the
hardware-stop routine. The original video post-reset RAM tail decrements raster
references and clears its slots before sending 37. Both agree with QEMU under
explicit cut-point preconditions; the omitted hardware reset/wait prefix remains
blocked. See `stock-execution/stop.md`.

Cancellation selectors 2 and 4 now have executed original producer paths. Under
the single-work ownership/reset-tail fixture, selector 2 retains a 120-byte
document allocation; selector 4 after END_DOC reads through null at `0x1000eb6a`.
Acknowledgement before END_DOC avoids that read but leaves an 80-byte child plus
its completion notice. Two fills, raster splits and release-flag overrides agree
across both engines. No aligned reference to the retained document/child remains
in tested non-stack writable RAM. This does not rule out arbitrary encoded
references or prove real-world reachability. See `stock-execution/cancellation.md`.
The precise remaining questions are whether real cancellation reaches the tested
one-work video ownership state, whether reset reaches that RAM tail, and how RTOS
ordering places END_DOC versus acknowledgement. Original status construction and
publication now execute in both CPU engines, including datastore writes, ONLINE
subscriptions, duplicate suppression and a 100-word event-history ring across
wraparound. The numeric cancel-only events produce selectors 1/3/4 without
changing ONLINE; cancellation and offline bits are distinct. Completed lifecycle
notices plus a matching-source clear exercise actual offline/online transitions.
These runs use the constructor's empty language-context table; optional outward
status callbacks and RTOS thread/semaphore creation remain host boundaries.
See `stock-execution/status-publication.md`.

Original RTOS queue creation, indexed send and receive now execute in both CPU
engines against independent FIFO oracles: supported widths, capacity rounding,
full/empty returns, repeated wraparound and created-queue rings. Selected
interleavings also execute wait-list insertion, direct receiver delivery or
waiting-sender refill, and original pending-suspension cancellation. The deferred
suspend helper runs as a fresh call after the wait is satisfied; paused CPU context
restoration and real interrupt timing are not claimed. See `stock-execution/queue.md`.
The combined StatusMgr test pre-enqueues original completed JobMgr notices,
receives/releases them through original queues, publishes its actual queued
outputs, and stops after original empty-queue wait insertion before suspension.
It retains only the persistent ONLINE subscriber. FIFO completion and pre-enqueue
ordering remain fixture choices; outgoing PrintMgr/JobMgr packets are retrieved
but not consumed by those tasks in this test. This removes whole queue substitutes
from the selected status lifecycle while leaving scheduler timing, actual page
completion and optional language callbacks unresolved. See `stock-execution/status-queue.md`.

Original explicit window flushing, initial-stack construction and voluntary
context save/restore now execute in QEMU. The stack builder also agrees with the
interpreter. Saved return/stack and special-register fields match CPU snapshots;
untouched physical data-register slots may alias older windows until access
triggers spilling, so they are not assumed to be preserved incoming values.
Two synthetic tasks repeatedly switch stacks through the original scheduler and
RFE restore, preserving separate arithmetic accumulators and nested return chains.
Those fixture tasks explicitly select each other; timer expiry is covered by
the later timer experiment below, while interrupt-driven preemption remains untested. A saved-continuation mutation is detected. See
`stock-execution/context.md`.

The next kernel experiment now executes original RAM initialization, the
thread-create core, ready lists and priority-driven blocking/wakeup/context
switches for two synthetic producer/consumer tasks. Complete message bytes,
ordering, sum acknowledgement, lowest-set-bit lookup, initial priority choice,
run counts, queue occupancy and final thread states match independent oracles.
Priority equality/extremes, capacity, width and RAM fill vary. All queue/scheduling
services execute original code. Infinite waits and zero time slices avoid timers.
The original task shell also terminates a returned consumer when appropriate.
This kernel experiment uses synthetic tasks; original StatusMgr integration is
described below, while parser/JobMgr/PrintMgr scheduling remains separate. See `stock-execution/scheduler.md`.

Original StatusMgr now runs under actual queue blocking/wakeup and priority
scheduling alongside a native producer of previously generated JobMgr notices.
Thirty cases cover repeated/empty/multi-page streams, both priority orders and
equality. Thirteen documents exceed its 25-message queue and force the producer
to block. Final idle is accepted only after all counters/ownership/output checks
pass; both tasks are suspended on empty queues. The original datastore constructor
prefix initializes 38 binary semaphores, and two original mutexes protect status
and datastore publication. These locks all execute and finish released with no
waiters. Runtime now has no whole-function host services. Original allocation/free use
a seeded pool with an additional original semaphore; only the live 16-byte
END_DOC notice storage is explicitly migrated from prior replay. An original
event group starts unset, and the native producer sets readiness through original
code, waking the status task when it ran first. Constructor thread creation
still uses a setup substitute. The datastore
constructor is stopped before its event-group/backing-value initialization, so
existing descriptor fixtures remain. This removes task scheduling and lock
substitutes for the selected status lifecycle, not for page completion, producer
JobMgr replay, optional language callbacks or outgoing PrintMgr/JobMgr consumers.
See `stock-execution/scheduled-status.md`. Original allocation/free also pass 93 independent-engine cases covering alignment,
payload preservation, deferred coalescing, reserve admission, live ownership and
accounting. Repeated free of the first block reaches a read before the bounded
arena; this negative case is caught by both RAM gates, not a device fault claim.
See `stock-execution/pool.md`. Original pool boot discovery, end-to-end producer
allocation and more printing tasks under the native scheduler remain productive
next avenues. Timed waits now have a separate original-code proof below.

Original timer initialization, timer task, tick routine and timeout callbacks now
run under native priority scheduling. Forty-four QEMU cases cover sleep, empty
receive, full send and early queue satisfaction, including 31/32/33/65-tick wheel
boundaries. Exact wake ticks, results, canceled timers, callback counts, message
contents, task states and empty final buckets agree with independent oracles.
A native clock task explicitly invokes the tick routine with system context set,
then yields. INTENABLE stays zero; original CCOUNT/CCOMPARE operations execute in
QEMU, but actual elapsed time, automatic IRQ delivery/return and time slicing are
not claimed. See `stock-execution/timers.md`. This removes a software timed-wait
boundary for later native JobMgr integration, not a physical timing uncertainty.


## In-progress handoff: native pipeline (2026-09-09)

Resumed 2026-09-10. Pinned GCC recovery completed after an interrupted download
was resumed. The unchanged build script verified the source checksum, instruction
fixtures and BE/call0 profile, and restored target headers/libgcc. Those native sources
passed the native checkpoint's complete offline suite with **93 consistency checks**;
the image/stream/raw-contract sections above own the later 98-check baseline. This includes
26 completed empty-document lifecycles, six separately classified conditional
null reads, 28 retirement cases, 18 ordinary native page cases and 18 split-raster
page cases. Consumption and completion remain supplied, not device evidence.

`stock-execution/pages.json` and `page-fragments.json` retain execution traces,
source/input/fixture hashes and byte-audited cleanup/retirement evidence. The
initial page draft errors (invalid immediate comparison and an embedded descriptor
mistaken for the free pointer) were corrected against original instructions;
`pages.md` and its generator own those details. Historical failure captures and
exact previously tested source snapshots remain preserved. Do not rewrite their
hashes to match newer sources.

### Controlled timed cleanup (focused execution complete)

The expanded page matrix now passes **18 completed lifecycles**: each original
six-case stream/fill configuration runs without ticks, with two explicit ticks
after each retirement, and with those same ticks after consuming event bit 8
through original event-get. Original JobMgr calls `0x1000f068` with flag 8 only
in the non-consumed two-tick cases. It frees retired nodes and empties work+80
before supplied message 17. Zero-tick and consumed-event controls retain the
nodes until message 17; all final ownership/counter/queue checks still pass.

The first timed run stopped at the existing selected-code gate before
`0x1000f068`. Its complete 62-byte body was audited against stock bytes:
RAM list traversal, flag test, call to admitted cleanup `0x1000f0a8`, RAM status
store and return; padding is excluded. Its SHA-256 and bytes are in pages.json.
No MMIO or unknown instructions were added. The control's first wrapper used a
wrong BE bit-index check; original event-get had returned 0 and output flag 8.
An explicit numeric mask fixed the wrapper assertion. This is not a stock fault.

The completion task delivers ticks using the existing audited tick/context
fixture with INTENABLE zero. This expires JobMgr's two-tick queue receive;
JobMgr then polls the event and invokes cleanup. It is not direct event wakeup,
automatic IRQ delivery, wall-clock time or physical consumption evidence.
Pages are now wired into the aggregate with a separate matrix/provenance gate;
the 18 page cases are part of the current **93-check** fully validated baseline
alongside the split-raster matrix below.

### Native split-raster integration (fully validated)

The initial scratch matrix passed six and thirteen chunks, both fills, and all three
timing/event controls. The first 64-chunk zero-tick run hit the original
200,000-step budget in StatusMgr at `0x10018227`. A read-only rerun preserved
`stock-execution/page-fragment-limit.json`: all input consumed, 64 references
retired, message 17 sent, document list empty; StatusMgr had consumed notice 46
and was processing notice 47. Final lifecycle oracles were not reached, so the
budget stop is explicitly not a completed lifecycle or stock fault.

A measured larger run completed in 200,315 instructions under an explicit
250,000 cap. `NativeTasks` and `start` now accept a positive instruction budget,
with unchanged 200,000 default. Only 64-chunk page fixtures select 250,000. No
code/RAM/peripheral guard changed. `validate-hp1020-native-page-fragments.py`
checks six, thirteen and 64 chunks with both fills and all timing controls,
verifies unchanged concatenated raster bytes, every node/reference/event and
final ownership, and requires the executed page baseline's source/ELF hashes.
It generates page-fragments.json/.md only after all 18 cases pass.

Both the fragment validator and its independent matrix/budget/provenance gate
are in the aggregate. The full `scripts/validate.sh` run passed sequentially after
all shared source edits: **93 consistency checks**, 18 ordinary native page
lifecycles and 18 split-raster lifecycles, preserving the separate 26 empty-document
lifecycles, six conditional null reads and 28 retirement cases. Current reports
have their actual source hashes. The 64-chunk cases complete in 200,315–201,736
instructions under 250,000; the six/thirteen-chunk and baseline cases retain the
200,000 default. The old budget stop remains separate evidence, not a pass.
`/tmp/hp1020-full-fragments.log` records both suite passes and child log directory.
Research processes for that checkpoint finished; CURRENT_STATUS.md owns current execution state.

Native input admission instead of direct per-document parser invocation, and
active-work cancellation with a bounded software consumer, remain distinct
integration questions. Neither is executed by these page fixtures. The later
raster-bypass section above records the current research priority.
Do not repeat the resolved empty-document cancellation ordering. Physical DMA,
raster execution, engine behavior, output and power-cycle recovery remain unproven.

Recovery logs for this session are `/tmp/hp1020-gcc-recovery-resume.log`,
`/tmp/hp1020-gcc-download-resume.log`, `/tmp/hp1020-gcc-rebuild-resume.log`;
focused logs are `/tmp/hp1020-native-pipeline-resume.log`,
`/tmp/hp1020-native-retirement-resume.log`, `/tmp/hp1020-native-pages.log`.
Full suite log: `/tmp/hp1020-full-resume.log` (contains child log directory).
The earlier raw failure captures and exact old tested source snapshots remain
in `pipeline-investigation.txt` and `pipeline-boundary-capture.json`.
QEMU uses a permitted private Unix debugger socket and no printer connection.

### Resolved failure and fixture audit

At `0x1000e44f` the JobMgr receive trace resolves logical ARs through WINDOWBASE.
Original StatusMgr startup publishes literal `0xe6101100` from `0x100063dc`, then
original publication sends `[15,1]` from `0x10010a00`. This is not manual queue
injection or an invented cancellation selector. The original parser sends END_DOC
while JobMgr is runnable behind it. JobMgr consumes cancellation with a document
still present and END_DOC already queued, sets cancellation state 1, and sends
its own message 37 at `0x1000e9e1`. For eleven documents the remaining receive
sequence is `[15,2,37]`; for thirteen it is `[15,2,1,2,1,2,37]`.

Original END_DOC processing reaches list-pop store `0x1001306b`, removing the
last document while message 37 remains queued. The acknowledgement arm checks
cancellation state, loads the now-empty list head and attempts head+12 at
`0x1000e9f4`. The RAM gate stops before that instruction executes, with original
error `unmapped RAM 0xc+4`, cancellation 1 and status counters 11/10. This is a
conditional original-software hazard under this fixture, **not an observed
printer fault or a QEMU hardware exception**. Other execution errors still fail
the validator. This is distinct from the older `0x1000eb6a` cancellation and
`0x1000e7dd` delayed-empty-document findings.

Ten equal-priority documents pass with both fills: cancellation is consumed only
after the list is already empty, so it never becomes armed and no self-ack is
sent. Eleven is the observed boundary for this specific 72-byte repeated stream,
not a globally minimal reproducer. Both memory fills agree despite different
undefined packet suffixes. Original JobMgr/StatusMgr constructor bytes specify
priority/threshold 15 and time slice 10. Repeating ten/eleven with all three fixture
tasks set to 15 and slice 10 preserves the boundary. No ticks are delivered;
actual time slicing, input-task priority and device reachability remain unproven.

The native fixture uses original constructors, original allocation throughout,
original locks, queues and priority scheduling. Runtime host services supply only
input bytes; no producer replay or heap migration occurs. The parser wrapper calls
`0x10009d34` once per reconstructed document, not once per raw sample/trailer.
`prepare_pipeline` extracts this setup for the next experiment; that extraction
now passes the current-source native matrix. The datastore
constructor stops at `0x10010db3`; its backing-value/event initialization remains
omitted. PrintMgr is absent, with its ONLINE packet `[45,24,0,2]` retained. No
PrintMgr cancellation request occurs in these empty-document fault traces.
Successful cases still require the original ownership/queue/counter/lock oracles;
the only live allocation is the 20-byte ONLINE subscriber. Final JobMgr receive
has an original two-tick timeout armed, not expired or permanently idle.

### Native retirement tail

`hp1020_qemu_retire.py` is now exercised by
`validate-hp1020-native-retirement.py`: 28 standalone QEMU cases cover empty,
one/five/six/thirteen-node lists, three initial reference counts, both RAM fills,
and two deliberately nonzero pending-cursor mutations. Original instructions
inside `0x10014319..0x1001434b` decrement payload+78, clear the consumed video slot,
and set JobMgr event bit 8. The no-next path reaches `0x100143a5..0x100143b8`,
executes the standard CPU INTCLEAR helper and returns through the native fixture's
ENTRY frame. Work/node memory outside the two-byte reference fields is unchanged.
Both mutations stop at excluded PC `0x1001434b` before any next-transfer path.

An initial standalone setup failed the expected-zero event-creation assertion.
Static control flow identifies the null-current/ordinary-system caller check;
the corrected fixture supplies a nonwaiting constructor caller, after which all
28 cases passed. The added negative assertion now executes and confirms result 19 for the
original null-caller setup. No real task, engine, DMA or IRQ
prefix is inferred from this standalone setup.
The wrapper itself supplies consumed nodes, completion flag 1 and zero pending
cursor. `stock-execution/retirement.json`/`.md` own the execution evidence.

### Executed native page fixture

`hp1020_qemu_page_pipeline.py` reuses `prepare_pipeline` and the native bootstrap
with three asserted insertion anchors. A synthetic completion task runs with
JobMgr 2, parser 5, completion 15, StatusMgr 31. It waits for readiness bit 8
published by the parser after its final document, drains original queue-1 message
11, executes bounded `retire_work`, and sends initialized message 17 through the
original indexed queue. It also validates ONLINE `[45,24,0,2]`. Other consumer
packet types hit a guarded break. No active-work cancellation is modeled.

The executed streams rebuild `matrix-a4_default.zjs` via `helper.stream(base)`;
three pages use `base[:1]+base[1:6]*3+base[-1:]`, and three documents repeat the
rebuilt whole stream. All six cases fit the unchanged 200,000-instruction cap.
FIFO ownership, reference 1-to-0 stores, original events, page/document counters,
credit restoration, locks and pool reclamation pass. Four tasks wait on empty
queues, and only the 20-byte ONLINE subscriber remains allocated. Consumption
and message 17 are supplied; DMA, engine tasks and automatic IRQs do not execute.
The controlled-tick matrix now observes cleanup before message 17 explicitly,
with event-consumption controls, as described above.

Fixture map: parser TCB `0x22800000`, JobMgr +0x100, StatusMgr +0x200,
parking queue +0x400, buffer +0x600, output +0x800; pool `0x22400000`, 64 KiB;
parser/job/status/timer stacks `0x22900000` through `0x22c00000`, 64 KiB each.
A completion TCB can occupy +0x300 and a separate stack `0x22d00000`.
The original queues have capacities JobMgr 20 and StatusMgr 25. Queue 1 uses
its audited object `0x10028a74` and a synthetic buffer. Automatic CPU interrupts
remain masked; physical DMA, custom raster instructions, engine control, printing
and recovery remain unproven. No printer contact or installed-printing change
is authorized during this offline work.
