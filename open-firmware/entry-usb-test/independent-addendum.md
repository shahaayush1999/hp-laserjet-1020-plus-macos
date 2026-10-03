# Additive independent acceptance: public RAM provider and natural drain stops

2026-10-03, author `/root/usb_reference_contract`. Frozen before any new runtime
or RAM-provider C implementation. This is static acceptance material, not a
passing target. No candidate/oracle import, parse, build, validation or execution
was performed. Source copying, hashing and manual ABI/interval arithmetic only.
The first independent plan and literal source remain **byte-identical** at
SHA256 `7818a09ed83fbfedc1b39b35524e1fc0f11a3b4480d0a5a8e2fe1970e84adac4`
and `13194a8d608de407cf9c513f59cf5b1a80a1c3cdeac4ea08b71ebb9602272b95`.

## Approval and scope

I found **no blocking disagreement** between the root-approved public package
and the independently frozen two-document schedule. The approved header is
`25f5e76cff3633d6e3ab85f4e9adfc2e94edcc02e2cfe0b7d7d2bafea2e82995`,
CONTRACT.md is `18864eee6bb95581e99429da8d2fac039e635ef365ce02f91a8d1d122c17a123`,
and its package manifest is
`679e4c2e4f27a4a8da578a00f5b8642ed81f56d9501583fe6e4bd9c1a76ae0a4`.
Every package member hash matched. Full public input copies, original independent
material and the private-core derivation are retained in `inputs/`.

This addendum resolves the formerly pending provider details: explicit DMA
labels, source padding/CPU poison/copy effects, stationary object schema,
original-image identity, actual-core status bytes and natural additional drain
observations. It does not replace the first oracle's identities, raw request,
input352, outputs, command words or startup assumptions. It introduces no
hardware implementation, new queue, recovery shortcut or per-document EOF.

`literal-addendum.py` contains independent future-checker helper source. It uses
only stdlib hashing and its own frozen constants, never producer imports or a
runtime-generated expected array. **It has not been parsed/imported/executed.**
`expected-layout.json` freezes all16 object and101 field rows after the manual
derivation below, plus supplemental source-derived offsets needed for original
image identity. A future const-only compiled witness must be compared against
all457 expected BE words before its offsets are used; actual object addresses
and extents must come separately from the audited ELF.

## Manual layout cross-check, independent of future compiler output

The arithmetic uses the already pinned target32 ABI: pointer/function pointer,
enum/uint32/size_t four-byte size/alignment; uint16 two; byte/bool one; explicitly
aligned16 receive/descriptor memory. I checked every named TSV offset against
the copied actual public headers, not a forthcoming implementation/result.

- Existing document/memory derivation remains13496/114704. Receive92 precedes
  output13380. Output stream13192 puts its ring at document13284; ring copied,
  accepted/completed rows therefore13316/13320/13324, error13328 and four16-byte
  slots13332. Parser documents are4720, stream pages13248. Final document flags
  are13492/13493/13494; all corresponding rows agree with the earlier independent
  nested-structure arithmetic. Output stream memory begins4096 and its32768-byte
  slots begin81936.
- Cookie is20 (four words, endpoint byte, three padding); adapter owner40
  (cookie20, pointer4, actual4, length2, eight flags, two trailing padding).
  Adapter begins pointer4/config6/padding2/ops8, so owners begin20, bulk owner100
  and states50/90/130. Delivering140, prepared ticket180, buffer188, response192,
  two status records204, class request208, raw requests216/224, typed records
  232/240 and failure ticket248 lead to last ID260 and epochs264 onward. Last
  result enums304/308 precede flags312..328 and final padding to332. In
  particular input_closed318/fenced317 and owner cookie100 are correct.
- Printer is56: pointer4/config12/ticket8 before request counters24..40,
  requested length44 and flags46..55. Thus reset_active50/reset_parts51 and
  last_recovery_id36 are independent reads.
- OUT is64: adapter pointer4, two12-byte spans, cookie20, result/fault words and
  five flags; buffer.cpu16, descriptor.cpu4, cookie28, phase58. EP0 slots are64
  each (two spans24, cookie20, original pointer/result/fault12, requested2,
  three flags, padding); adapter pointer4 puts phases62/126 and whole object136.
  EP0 memory160 has OUT descriptor0, IN descriptor16, OUT sink32, IN staging96.
- SETUP observation32 (three words, record16, status2, padding2) follows its
  adapter pointer. Offload8, seven scalar words and result/flags make80;
  record capture16, last_sequence48, last_admitted_sequence68, pending_kind78.
- Program is88: pointer4/IO16/layout12/failure24/selection12, three scalar
  words and seven flags. Failed83/completed84/selection85/binding_ready86.
  Publisher is140: pointers8/mapping16/cache12/failure44/preflight12, saved
  values/prefix12, identity fields16, result enums12, six flags and padding;
  prefix100/failed137. Acquisition is152: pointer4/hooks16/two64-byte diagnostics
  plus flags. Last prefix40, first failure84..148, failure_valid149. These agree
  with existing unchanged component extents, not a compressed fixture.
- Provider retained record32: cookie20, original pointer4, requested4, four
  flags. Two records64 + reset ticket8 + ten words40 + four flags4 + callback
  snapshot64 + separate image cookie20 + image slot4 =204. Thus current bulk
  cookie32, original52, live60; callback_depth88, steps100, closing114,
  callback snapshot116, **independent image cookie180/slot200**. The last fields
  are supplemental raw reads under the exact sealed header, not a second cookie
  allocator. Scope changes must not relabel those image bytes.
- Witness:16 +240*24 +16 +65*36 +12+16 +14*36 +8+16 +144 +64 +2*20
  +280 =9216, type alignment4. All listed starts/widths match. Mailbox is256*4
  =1024; setup array is16/type alignment1, but its actual allocation must still
  be16-aligned. Type alignment and object-placement alignment are distinct.

The separate immutable facts object is40 bytes/alignment4: program-init3,
program7, publish7, acquire3, setup3, EP0-publish3, two alignment bytes,
EP0-completion8, stall-clear1 and three promise bytes. Its specified fields are
all1 except the independent IN actual word0. The literal helper includes these
named facts/zero padding as an expected40-byte source; no descriptor/register
observation may manufacture them.

## Six ordered stops, seven paired captures, no hidden repair

Six cases remain three dirty/admissible CPU profiles by two paints. The ordered
stop labels are:

1. `after-normalization`: new normalizer has established privileged PS15,
   INTENABLE0, WINDOWBASE0/WINDOWSTART1, loops0/SAR0 and SP10016020; no zero store
   or C call yet. Preserve all loaded/painted RAM.
2. `pre-c`: after four exact clears, before the actual CALL0. All actual state,
   mailbox, full memory and witness bytes zero; generic initialized data and
   all sentinel/stack/guard/gap/island bytes unchanged from the loaded image.
3. `pre-close`: first actual `hp1020_tusb_adapter_close_input` entry, before its
   first instruction. Both END_DOC events and64 actual FF bytes already exist;
   final `(14,3,2,13,1)` still DCD-owned, OUT EXPOSED, receive13/12/count1.
4. `pre-final-service`: **the next actual publisher-service entry after close**,
   reached only after original-cookie acquisition13 succeeds. OUT FREE, adapter
   PENDING, same receive13/12/count1. No service poll is allowed between close
   and this acquisition; earlier ordinary service entries are legitimate.
5. `pre-finish`: first actual adapter-finish entry after service and empty pump.
   Owner absent, receive13/13/count0, document/output still unfinished/stopped0.
6. `park`: after the only finish returns and C returns. Finished/stopped/fenced1,
   count0, original G2/epochs/IDs unchanged, no new output or packet.

Initial capture plus these six is **seven paired model/native snapshots**.
Native additionally captures two actual self-park steps, for nine native
snapshots; the model must likewise execute those self-jumps with unchanged state.
Entry transitions count actual target addresses, including tail jumps, and
record PC/instruction/SP/a2..a7. Do not count only CALL opcodes, add C marker
functions, force PC forward, call getters through GDB or let a mailbox phase
label decide which production entry was observed. Check actual argument identity
against the correct linked adapter/publisher instance.

Limits remain exactly10,000,000 interpreter instructions per case,120 seconds
QEMU,4096 GDB commands and16MiB ledger; no silent widening. Outer schedule/API
transitions are bounded256, with callbacks/hooks excluded from the outer count.
The necessary reset/config/status/bulk service sequence is fixed; harmless
additional service/step totals are not invented as literal outcomes. Require
their counters to match actual entry/call evidence, their ordering to match the
contract, and the shared bounded limits. An unexpected WAIT in this fully
supplied initial schedule is a failure, not permission for unbounded retries.

All32 incoming physical ARs remain independently distinct; WB is seeded before
them in QEMU, then physical/current logical aliases are read back. Verified
11.1.1 mapping remains INTENABLE110, PS42, WB38/WS39, loops33..35, SAR36; do not
touch37/PREFCTL or83/DBREAKC0. Dirty loop endpoints350a0/350e0 remain outside
normalizer/entry and above the witness budget. The same protected loaded image
is followed continuously through the complete loop. No helper CPU reset,
call0/call8 wrapper, SP reseed, hidden BSS/data repair or post-entry write occurs.

## Independent bytes, identities and ownership at the drain

Receive admission/binding remains generation2 and bulk cookie sequence k is
`(k+1,3,2,k,1)`. Each real callback must copy its actual original cookie once;
fixed literal values are comparison expectations, not values to synthesize.
The initial standard IN0 status retains `(1,2,1,0,0x80)` with original NULL/0 and
distinct64-byte staging. Its exact completed descriptor is8800ffff/0/b68ace00/0;
all other160-byte EP0 memory is zero. IN actual length0 remains separately
supplied; lowffff is deliberately not an actual length.

Every device payload consists of the actual specified source fragment followed
by **new contract padding** `80 | ((69 ^ slot*1d ^ i*7) &7f)` (hex constants).
All padding bytes are nonzero, including sequence13's whole64-byte ZLP backing
allocation. Poison is descriptor `(c35a0000|slot,13579bdf,fedcba90,2468ace0)` and
CPU prefix byte `(d3 ^ slot*29 ^ i*17)&ff`, where29 and17 here are hexadecimal,
as in the approved header's `0x29/0x17` formula. No padding from this contract
is retroactively attributed to earlier acquisition reports.

Before acquisition, poison only the actual16-byte OUT descriptor and selected
64-byte CPU prefix. Then the hooks copy16, copy64, order; the component reads its
actual resulting descriptor. Snapshot source cookie/slot independently from the
current owner. Before close, source image still belongs to sequence12/slot3,
while the newly armed current owner is13/slot0 and device_valid is0. The source
identity must not be silently retagged to13. Installing the final supplied image
replaces it only after exact-owner checks; then source13/slot0/device_valid1.

The complete4096-byte receive oracle is constructed by starting with zeros and
applying each permitted64-byte copy to `(k-1)%4*1024`. Before close, latest slot
contents come from sequences9,10,11,12; after final acquisition slot0 is replaced
by sequence13's nonzero padding. Every unused960-byte tail remains zero. The
prepared final descriptor08000000/0/RX0/0 becomes88000000/0/RX0/0 only through the
final hook. OUT retirement clears its cookie/buffer metadata, **not its bytes**;
adapter PENDING retains the original14 cookie/buffer/length64 until service.
The provider then clears only its live flag and retains the original record.
Its last publication callback snapshot remains the old slot0 sequence9 prefix.

The actual receive slot0 metadata remains `(sequence13,capacity64,length0,ready0)`
at close and the post-acquisition service entry; other slots are zero. Only real
TinyUSB service calls the class completion to make it READY. The empty pump then
zeros that metadata and increments consumed13 without feeding the parser.
Before finish/park all four metadata slots are zero. A current descriptor bit,
provider live flag or mailbox count cannot substitute for these component reads.

The independently derived private core is68 bytes; ep_status starts52 and OUT1
is byte54. The full endpoint array is `00000500000000000000000000000000` at both
close and PENDING-service checkpoints; allzero only at finish/park. Mask1 is BUSY,
mask4 CLAIMED, ordinary bytes confirmed by existing target getter instructions.
The new target must bind its own private symbol size/address and getter's actual
load52/mask1 before raw reads. Getter diagnostics are secondary. Full private
state is not otherwise guessed to be allzero after USB initialization.

Two output callbacks provide two actual32-byte views and original events
`(2,1,0,1)`/`(2,2,1,1)` with callback result0. The separate64-byte witness is allFF;
full production output storage is32 FF plus32736 zeros, because slot0 is reused.
The last ring has copied/accepted/completed8 rows; slots are `(FREE,0,8,1)` then
three zero slots. Later close/ZLP/pump/finish cannot add output or notifications.
Both callbacks must reject recursion and any invocation once provider.closing1.

## Exact witness and initialization checks

The original programming19 rows and each publication14/acquisition3 rows are
unchanged. New trace framing adds only independent scope and global ordinal:
scope0 for programming, then1..13, ordinal1..240. Each read value comes from an
immutable source independent of writes. There are237 rows before close and240
after acquisition; kind counts remain74/47/54/13/13/13/13/13. There is no CSR_DONE,
automatic status owner or endpoint-close operation in this raw configuration
plus ordinary input-close profile.

For each actual kind4..8 hook, derive the expected original cookie from its
sequence, actual owner buffer from the independently verified linked memory
symbol plus slot*1024, and descriptor pointer from its own linked allocation.
Range rows number62 before close/65 afterward. Kind4/7 span points to that CPU
prefix,5/6 to descriptor16,8 to0; owner pointer/length remain original/64.
Their matching trace row carries the literal asymmetric DMA/length. All14 bind
rows are present before close: initial NULL/0 IN0 with separate staging, then
13 original bulk reservations. Log labels/counters do not select memory.

`witness_storage()` independently builds every9216 byte from those literals,
actual validated symbol addresses, true output/events and separate device image.
Guards are exactly sixteenA7 at0,5776,8144,8672 plus device-relative0/32/48/128;
range/bind padding and280-byte reserved tail stayzero. Unused last trace/range
rows at pre-close stayzero. No actual output/trace from a candidate is copied
into the allowed oracle. Source/data hashes are secondary to full byte checks.

Startup zeros actual BSS end,1024 mailbox,114704 memory and9216 witness once.
With witness start10032830 its used end is10034c30, leaving960 bytes untouched
before witness cap10034ff0. Preserve every other protected byte. C must scan
all four zero spans and256 sentinel bytes before any initializer/guard/mailbox
write, retaining errors in locals. It may hash loaded initialized .data, but
the independent pre-C checker compares actual bytes directly to the linked ELF
file bytes (including relocated pointers/padding), never to a producer hash.
Generic .data becomes runtime-writable only after C begins; sentinel never does.

Mailbox fixed indices and runtime/provider counters are witnesses, not ownership
authority. Require unused words128..255 zero, errors/cancellations0, exact
12/13 acquisition and row counts,704 actual input bytes,832 payload/208 descriptor
bytes copied,64 actual output bytes/two events and one close/finish. Recompute
all FNV values from independently checked full ranges. Before-C evidence must
survive even if a later component initializer would clear incorrect memory.

The later raw-only gate must bind full input/source/ELF/layout/audit hashes and
replay actual model instruction/access records and native command/reply ledger.
Reject paired resealed corruptions of generation, cumulative page, pixels,
source-image cookie, PENDING ownership/core byte, missing final ZLP, skipped
range/order, initialized-data corruption, early close or debugger repair. Passing
two engines or matching producer labels alone is insufficient.

No physical USB/cache/mapping/settlement, interrupts, boot/loader, page engine,
copies replay or printing claim follows from this acceptance contract. The new
runtime C and complete emitted closure/stack bound remain unexecuted future work.

