# Controller-family manual evidence

Reviewed 2026-09-29/30. These official manuals describe other implementations;
they do not identify HP silicon or establish physical controller behavior.
`provenance.json` records exact URLs, revisions, PDF hashes and page locators.
PDFs are not redistributed. Recover from those URLs and verify hashes before
reuse; the reviewed downloads are under `/tmp/hp1020-udc-manual-review-20260929/`.
Page numbers below are printed and one-based PDF pages.

[Sony CXD5602 manual, revision1.1.0](https://www.sony-semicon.com/files/62/pdf/p-28_CXD5602_user_manual.pdf),
2022-10-24:

- Section3.18.8.2, p1183: SETUP DMA ignores descriptor ownership; the16-byte
  record has no unique capture counter. HOST_BUSY/DMA_DONE cannot protect it.
- Section3.18.8.6, p1190: an OUT interrupt disables RX DMA. Interrupt timing
  depends on mode; BFILL waits for a short packet (p1196).
- Page1209 orders SETUP copying before descriptor reinitialization and RDE.
  It does not promise that manually clearing RDE settles an outstanding write.
- Pages1205–1207 describe global slave/PIO operation with MODE0 and TDE/RDE off,
  reading SETUP8 through RxFIFO (+0x800, p1165). Mixed EP0 PIO/bulk DMA is not
  established. Packet boundaries and FIFO side effects still matter.
- Page1218's conditional CNAK enhancement addresses consecutive SETUPs; p1199's
  little-endian CSR/descriptor requirement must not replace HP's observed BE
  profile.

[AMD CS5536 Data Book33238G](https://www.amd.com/content/dam/amd/en/documents/archived-tech-docs/datasheets/33238G_cs5536_db.pdf),
May2007: sections6.4.5.1/7 (pp313/317) describe both EP0 stall bits clearing on
successful SETUP reception, with both NAKs set. NAK does not exclude SETUP.
SUBPTR/DESPTR register reset values (p320), whole-controller/DMA resets (p321)
and USB reset detection (p325) are distinct; none supplies an external-memory
ownership or bus-write settlement guarantee.

[Micrel KSZ9692MPB/XPB manual](https://ww1.microchip.com/downloads/en/DeviceDoc/ksz9692mpb_xpb_reg_descp_v1.0.pdf),
M9999-102008-1.0, October2008: pp137/140 corroborate SETUP acceptance during
pending USB reset and the stall/NAK behavior. Generic BNA wording must not erase
the specific SETUP ownership exception above.

Implementation implication: serialize every receive-enable writer and capture
completed, CPU-visible bytes before reopening input. The executed original
[idle worker](../../idle-receive.md) demonstrates why a separate deferred RDE
writer matters. IRQ bits, repeated reads and identical packet bytes supply
neither event identity nor coherent acquisition. Current external sequence,
visibility, stall-clear and settlement preconditions remain required.

## Stock applicability of PIO

The bounded static review on2026-09-30 found no positive stock FIFO/PIO path.
All five direct loads of DEVCTL's literal cover seven stores:

| Store PC | Byte-derived operation |
| --- | --- |
| `0x1000904a` | AND `0x00ffffff` |
| `0x1000905d` | OR `0x00030000` |
| `0x1000906d` | OR `0x320`: family MODE, burst and BE bits |
| `0x100092ef` | OR `8`: TDE intent |
| `0x10008fa3` | OR `4`: RDE intent |
| `0x10009a26` | AND `~8`: TDE pause intent |
| `0x10009a83` | OR `8`: TDE restore intent |

The alternative startup branch to `0x100090fd` skips mode programming; it does
not establish MODE0. Both branches share later descriptor setup. No inspected
write clears MODE/TDE/RDE together. Annotated L32R references contain no FIFO
address; the apparent `0xb30013be` byte match crosses unrelated instructions at
`0x10016ea4/0x10016ea6`. This is not whole-program pointer analysis: computed
addresses, unannotated code, runtime values and boot ROM remain outside it.
Hardware PIO support is therefore still possible, but changing to it would add
an unverified FIFO/completion backend for both control and bulk. Continue the
better-supported DMA path. Source authority is the pinned stock ELF; detailed
static search/recovery notes are `/tmp/hp1020-pio-applicability-20260930.md` and
`/tmp/hp1020-pio-annotated-20260930.{json,txt}`. Exact copies are preserved in
`static-review.tar.gz`; `static-review.json` pins every member. It also preserves
the two independent reviews summarized below. No new execution occurred.

## IN memory release versus USB completion

AMD p314 §6.4.5.2, Micrel p141 §2.17.10 and Sony pp1158–1159 describe TDC as
memory-to-TxFIFO completion. Sony p1125 Figure USB-39 separates this DMA branch
from USB transmission/ACK/retry. Its pp1192–1193 Figures USB-52/53 update
DMA_DONE/TX-success after copying to FIFO; p1174 retains FIFO data for retries
until a successful USB transaction. The control-IN and bulk-IN flows explicitly
place TDC before IN token/DATA/ACK (p1217 steps9–12; p1222 steps5–8).

Sony pp1186–1187 describe TXBYTES as a programmed count, but p1208 §3.18.11.2.2
also describes it as transferred packet size in descriptor-update mode. Preserve
this refinement: a mode-dependent DMA packet count is possible; a successful-wire
count is not established. Do not import OUT's aggregate-count rule into IN.
Sony's newer XFERDONE_TXEMPTY bit27 and optional TXEMPTY bit24 (pp1154–1157,
p1122) are reserved in the older AMD/Micrel layouts and absent from the pinned
Linux header. They are not available HP facts.

Under justified mode, visibility, identity and terminal-access conditions,
source/descriptor memory can be reusable while the FIFO still owns retry data.
That family rule does not settle arbitrary cancellation, reset or stale events.
Keep three distinct meanings: memory may be reused; FIFO/USB transaction has
finished; upper software may advance or invoke its status callback.

Pinned `snps_udc_core.c:2282–2332` gives data-IN back at TDC and sets actual to
requested length. Its last-descriptor walk at994–1002 checks L/next, not owner,
TX status or TXBYTES. Control-IN at2652–2660/2683–2704 clears TDC separately and
gives back immediately after publication. The ZLP shortcut1094–1120 completes
before CSR_DONE/CNAK. These are Linux API conventions, not wire observations.

Original sender bytes `[0x10008c24,0x10008f40)`, SHA256
`b179a25b722a2a7ed2e602df5befc3481f38ce11d969600c7b6abbfff4061c92`,
wait on event bit1 after publication; the nonzero resume at`0x10008f33` checks
software remaining length, not completed TX/count. The IRQ's saved TDC snapshot
selects a task wake, even after separately acknowledging error bits. This is
not an original-cookie-tagged ACK record.

Current `open-firmware/udc-ep0/hp1020_udc_ep0.c:165–202` keeps `in_actual` and
settlement supplied separately. TinyUSB `usbd.c:900–949` advances data packets or
invokes status-complete/CONTROL_STAGE_ACK on the supplied completion. A physical
DCD must define these stage-specific meanings before mapping DMA notifications;
neither blindly filling actual=requested nor inventing a required ACK counter
resolves the contract. Existing tested component sources remain unchanged.

## Standard-request offload and the TinyUSB boundary

Sony p1114 §3.18.1.2 assigns standard requests other than GET_DESCRIPTOR,
SET_DESCRIPTOR and SYNCH_FRAME to hardware. In this documented mode SET_ADDRESS
needs no extra software status response or address write. SET_CONFIGURATION and
SET_INTERFACE require software state updates through SC/SI (p1146 bits0/1),
with sampled DEVSTS CFG[3:0], INTF[7:4], ALT[11:8] (p1143). These are decoded
four-bit fields, not the original eight SETUP bytes or immutable event history.
Pending notifications still permit SETUP arrival.

DEVCFG.CSR_PRG bit17 enables the extra software programming gate (Sony p1134,
AMD p321); DEVCTL.CSR_DONE bit13 grants status permission (Sony p1138, AMD p323,
which specifies read-as-zero). Sony p1212 shows endpoint programming, grant,
hardware status ZLP, then host ACK. Permission does not establish completion.
The diagram labels both notifications SI; the register table distinguishes SC
and SI. Micrel pp133/135–137 corroborate the register fields and permission.
Static CSR mode is a separate policy; CSR_PRG does not mean all requests become
raw application SETUP records.

Pinned Linux's header32–50 explains reconstructed requests. Its core enables
CSR_PRG at1455–1485 and unmasks SC/SI/UR at256–274. SC2751–2798 and SI2800–2858
sample DEVSTS, reconstruct canonical requests and notify the gadget after CSR
updates. Endpoint enable318–432 programs type/MPS/FIFO and logical endpoint
mapping. The queued ZLP shortcut1088–1120 grants hardware status for SC/SI.
UR2860–2918 resets software state; endpoint-first IRQ order2980–3021 and saved
SC/SI/UR scan order are not physical chronology or HP settlement evidence.

Original-byte applicability is bounded:

- Dispatcher`0x1000940e..0x10009459` compares literals
  `0000a100 00002102 00008006 0000c100 0000a101 0000c101`. Standard address,
  configuration and interface tuples are absent and reach rejection`0x10009859`.
- Startup`0x1000902d..0x1000903a` ORs8 into DEVCFG, preserving inherited CSR_PRG.
  Its device mask write`0x100090b8` ORs0x77, masking SC/SI under family positions.
- Stores`0x100090bd/ce/d9/de` program static endpoint CSR words at offsets
  `0x504/508/510/50c` as `02000000/100000c1/100080c1/100000d1`.
  These fit EP0/64 and EP1 bulk configuration1 with OUT alternate0/1, IN alt0.
- SC/SI IRQ branches`0x1000833c..0x10008354` only acknowledge their bits; they
  do not reconstruct requests or program CSRs. Their physical reachability is
  not proved when the inspected startup masks them.

These anchors fit a static-offload design but do not establish HP's initial
CSR_PRG value or dynamic-mode capability. A further bounded review on2026-10-02
resolved the preceding startup call: `0x1001214c` invokes an event barrier with
argument3; its helper waits on event`0x1002c6f8`, mask4, mode0, infinite timeout.
It does not configure the USB registers. The inspected thread creator supplies
entry argument0. All seven direct DEVCFG literal references are accounted for:
five stores preserve bit17 (OR8 or low-two-bit speed changes), and two only read
speed. All seven direct DEVCTL stores preserve bit13; under the documented
read-zero CSR_DONE rule they issue no permission. DEVCTL's OR`0x30000` is a
different register's burst-length field, not DEVCFG.CSR_PRG.

Startup also pulses bit1 of the undocumented wrapper`0xb3010000` before DEVCFG.
Those bytes do not prove reset semantics or transfer family reset defaults to
HP. The negative search covers annotation-bounded direct L32R references and
aligned PT_LOAD words, not synthesized addresses, indirect pointers, aliases,
earlier resident firmware or hardware side effects. Exact review,13 raw regions,
245 instruction rows and seven literal words are preserved in
`offload-mode-review.tar.gz` with a member manifest. The lead rechecked every
retained byte against the original ELF. No additional instruction ran, and a
RAM test of these preserving masks would not resolve the hardware question.
The new software fixture must require a separately supplied dynamic-status-gate
capability; neither stock startup nor an observed configuration proves it.

TinyUSB requires configuration/interface
notification to open classes (`usbd.c:983–1019,1154–1180`). A future adapter needs
explicit typed offload provenance, sampled fields and original external sequence;
do not disguise reconstructed requests as raw16-byte captures. Its status action
must bind the current control owner and grant exactly one hardware response,
without an extra DMA descriptor/ZLP. Existing binding recovery requires an
accepted status owner; merely returning true is insufficient.

A held no-buffer auto-status owner is a conservative software candidate until
justified completion or supersession/cancellation. A narrower Linux-like early
handoff convention would require explicit semantics and callback review. Neither
can fabricate ACK or recovery promises. The bounded next experiment and remaining
mode/order/rejection questions are owned by
[next-evidence](../../../open-firmware-model/next-evidence.md#next-implementation-seam-hardware-handled-standard-requests-2026-09-30).
The archived reviews retain exact source hashes, instruction anchors and detailed
manual locators; the original ELF and official PDFs remain the primary evidence.

## Repeated configuration correction (2026-10-02)

The official USB2.0 specification requires affected endpoint defaults, including
DATA0, when selecting a configuration or alternate setting (§9.1.1.5, printed
p243/PDF271). Endpoint halt must clear even when SET_CONFIGURATION or
SET_INTERFACE repeats the current value (§9.4.5, printed p256/PDF284).
A sole default interface may instead reject SET_INTERFACE (§9.4.10, printed
p259/PDF287). Download/member hashes and official URLs are recorded in
`usb2-spec-provenance.json`; the PDFs remain disposable local references.

The earlier model and unexecuted first offload draft followed pinned TinyUSB's
same-configuration shortcut. Their idempotence checks do not establish this
USB requirement. The revised local patch reinitializes repeated nonzero
configuration through its ordinary close/reset/open path. Adapter admission
must drain original owners first. Preserve the control request, connection and
address flags across configuration-only reset; actual bus reset remains distinct.
Typed interface reselection separately needs its affected endpoint defaults
restored before status permission. All physical programming remains supplied.
