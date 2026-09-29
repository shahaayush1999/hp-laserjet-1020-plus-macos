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
pass, and the latest full sequential aggregate passed **105 consistency checks**
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

First remove whole-page compressed retention by adding an optional chunk
consumer to the existing parser, keeping its retained mode and grammar intact.
The goal is a fixed compressed-chunk buffer plus bounded decoder/output storage,
with detailed images larger than the current test input buffer as evidence.
The optional synchronous chunk consumer, `hp1020_image_stream.c` and an
incremental host/target fixture now pass **65 host and 43 QEMU cases**, owned by
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
- Multiple documents/images, 16 versus 17 pages, exact BIHs, padding errors,
  truncation and consumer failures are checked. A consumer failure leaves the
  pending band unreleased and errors sticky; it is not a retry mechanism.
  Output is provisional until finish, and copies stay metadata. Page metadata
  remains capped at 16. The callback is synchronous, without a scheduler or
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
`hp1020-validation.eIS7rL`). No research process remains running. A current open-target decode supplies four actual packed
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
All recorded sources and fixtures match; no validation process remains running.
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

Next use this software ring from the existing bounded ZjStream band's consumer,
then verify per-page draining and different image sizes across consecutive
pages/documents with reused input chunks. Keep output readiness/completion
explicit and check late input rejection separately from already emitted rows.
Original owner integration, native scheduling, live configuration, physical
packing, engine behavior and power-cycle recovery remain unproven. Do not repeat
the resolved metadata, selector or cancellation matrices.

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
No research process remains running after this checkpoint.

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
