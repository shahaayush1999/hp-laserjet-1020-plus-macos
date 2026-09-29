# Research map for agents

Read `../CURRENT_STATUS.md` first. This is a selective map, not a reading list.
The owner consumes progress through chat and is not expected to read these files.
Paths below are relative to the repository root unless linked explicitly.

## Where to work

| Question | Source or current evidence |
|---|---|
| What should be reused instead of reconstructed? | [Functional replacement and reuse](open-firmware-model/next-evidence.md#functional-replacement-and-reuse-2026-09-29): JBIG-KIT supplies decoding; [classic Synopsys USB family comparison](usb-path/controller-family.md) identifies a concrete Linux controller reference. TinyUSB enumeration/EP0 remains a reuse candidate after a controller adapter; its printer-class reset does not supply our asynchronous ownership gates. `open-firmware/usb-printer-class/README.md` pins that review and the USBX alternative. ThreadX remains optional. Original internal fidelity is evidence, not the implementation goal. |
| What is still unknown, and what would resolve it? | [Next evidence](open-firmware-model/next-evidence.md) |
| Which components are implemented? | `open-firmware/semantic-core/`, `open-firmware/image-core/`, `open-firmware/usb-receive-core/`, `open-firmware/usb-printer-class/`, `open-firmware/usb-bulk-parser-draft/`; each has its own README |
| Native pipeline and completion evidence? | [Current native handoff](open-firmware-model/next-evidence.md#in-progress-handoff-native-pipeline-2026-09-09), [completed lifecycles and conditional original null reads](open-firmware-model/stock-execution/pipeline.md), [bounded native retirement](open-firmware-model/stock-execution/retirement.md); [native pages with supplied consumption](open-firmware-model/stock-execution/pages.md); [split-raster native pages](open-firmware-model/stock-execution/page-fragments.md); 36 native page cases preserve datastore 32 before/after; see `CURRENT_STATUS.md` for the latest aggregate validation |
| Original binary as an oracle? | [Parser/libc differential execution](open-firmware-model/stock-execution/validation.md), [status decision execution](hardware-boundary/stock-status-execution.md), [JobMgr execution](open-firmware-model/stock-execution/jobmgr.md), [original memory pool](open-firmware-model/stock-execution/pool.md), [completion/cooperative lifecycle](open-firmware-model/stock-execution/lifecycle.md), [original stream admission](open-firmware-model/stock-execution/admission.md), [PrintMgr execution](open-firmware-model/stock-execution/printmgr.md), [notification ownership](open-firmware-model/stock-execution/notifications.md), [stop boundaries](open-firmware-model/stock-execution/stop.md), [conditional cancellation findings](open-firmware-model/stock-execution/cancellation.md), [status publication and history](open-firmware-model/stock-execution/status-publication.md), [original RTOS queues](open-firmware-model/stock-execution/queue.md), [status task with original queues](open-firmware-model/stock-execution/status-queue.md), [original context switching](open-firmware-model/stock-execution/context.md), [priority scheduling and blocking queues](open-firmware-model/stock-execution/scheduler.md), [original timed waits](open-firmware-model/stock-execution/timers.md), [scheduled original StatusMgr](open-firmware-model/stock-execution/scheduled-status.md); standard ISA only, explicit host substitutes |
| What proves current offline agreement? | [Consistency gate](offline-consistency/offline-consistency.md), [target C execution](open-firmware-model/semantic-target/validation.md), [independent QEMU](open-firmware-model/semantic-target/qemu.md), [page planning](open-firmware-model/page-plan.md) |
| Correct toolchain and old encoding failure? | [BE encoding audit](toolchain-probe/big-endian-encoding-audit.md), [C compiler](toolchain-probe/freestanding-c-compiler.md) |
| Boot wrapper and standalone handoff? | `analysis/upload-wrapper-report.md`, `analysis/boot-handoff/boot-handoff.md` |
| Direct page fields and raster data? | [START_PAGE construction](hardware-boundary/zjs-direct-work.md), [field semantics](open-firmware-model/raster-field-semantics.md), [metadata bounds](open-firmware-model/metadata-bounds.md) |
| USB control and bulk contracts? | [Controller family and executed descriptor fragments](usb-path/controller-family.md), `analysis/usb-path/usb-bulk-probe-contract.md`, `analysis/usb-path/usb-parser-shim-contract.md`; pinned upstream reference/license/provenance in `analysis/usb-path/controller-reference/linux-v6.12/`. Family agreement is not a working port. Supporting control/event/re-arm reports remain in the same directory |
| Bounded input and cancellation/restart ownership? | `open-firmware/usb-receive-core/README.md`, [receive/document execution](usb-path/receive-core/validation.md): FIFO consumption with out-of-order completion, stale-ticket rejection, endpoint-wide fault fencing, two external quiescence acknowledgements. This is compiled software with supplied observations, not a controller or physical reset implementation. |
| Standard printer-class requests and recovery? | `open-firmware/usb-printer-class/README.md`, [composed class/document execution](usb-path/printer-class/validation.md): ID/status/reset, immutable EP0 response ownership and three current reset promises; 73 host/73 QEMU cases. [Original reset dispatch](usb-path/class-reset.md) executes registration/list changes before transmission; supplied software frees are not hardware quiescence. |
| Does stock USB port status report paper state? | [Original GET_PORT_STATUS construction](usb-path/port-status.md): 28 interpreter/QEMU cases prepare a fixed zero byte before the sender. Original zero definitions execute through explicit cuts; no physical status read or USB transfer is established. Keep the replacement's unknown-status fallback explicit. |
| Internal message destinations? | [Stock constructor registration](queue-routing/registration.md); queue 0 engine, queue 1 PrintMgr. Earlier mapping narratives are superseded. |
| Open software image production? | `open-firmware/image-core/README.md`, [decoder checks](open-firmware-model/image-core/validation.md), [complete-file bridge](open-firmware-model/image-core/page-validation.md), [bounded stream bridge](open-firmware-model/image-core/stream-validation.md), [compiled decoder/output ring](open-firmware-model/image-core/ring-validation.md), [whole-document output](open-firmware-model/image-core/output-validation.md); exact pixels, reused input, changing page sizes and separate target checks. The C path preserves acceptance/completion ownership; its output consumer is supplied, with no engine integration |
| Can decoded buffers enter original output storage? | [Raw-buffer contract](hardware-boundary/raw-buffer-contract.md) owns separate dispatch/retirement fragments; [original producer and admission](hardware-boundary/raw-producer.md) executes one supplied completion with cleanup; [actual parser route](hardware-boundary/raw-parser.md) constructs owners, copies BIH fields and reaches original video allocation/preparation. [Software ring delivery](hardware-boundary/software-ring.md) compares decoded pixels through original buffer claim, publication, selection and release, including a full ring, delayed completion, continuous wrap and a partial final band. The host copy bridge, readiness/completions, task entries and pool capacity remain explicit. No native decoder-to-engine pipeline, raw IRQ reachability, repeated page submission or physical output is proven |
| What is submitted after ring selection? | [Original output pointer/count arithmetic](hardware-boundary/output-submission.md): 30 interpreter/QEMU cases stop before every peripheral access. Default single-output and conditional dual-output fragments are separate; pixel packing, readiness and physical acceptance remain open. |
| How does stock select output format? | [Original output-format fragments](hardware-boundary/output-format.md): 12 interpreter/QEMU cases construct BPP1/BPP2 tables and control/stride masks before peripheral access. Selector 0 and default 2 are both single-output but have different tables; physical sample meaning/polarity remains unresolved. |
| Custom raster opcodes and the preferred bypass? | [Executed stock bypass](hardware-boundary/raster-bypass.md), [conditional callback inventory](hardware-boundary/raster-callbacks.md), [whole-binary instruction annotations](hardware-boundary/instruction-properties.md); file-backed datastore 32 = 1 disables the callback in bounded original execution; live mode, raw-buffer production and output remain unproven |
| First-page video and engine behavior? | `analysis/hardware-boundary/first-page-hardware-sequence.md`, `video-dataflow-contract.md`, `engine-print-topology.md` in that directory |
| Future non-printing hardware experiment? | [Bulk probe test plan](open-firmware-probes/usb-bulk-parser-draft/hardware-test-plan.md), [safer staged ladder](open-firmware-probes/hardware-test-ladder.md) |
| Installed printing support? | `README.md` at the repository root; research tests are a separate workflow |

## Verification and recovery

Run from the repository root:

```sh
scripts/validate.sh
```

This runs the analysis suite followed by the probe suite, including native/target
execution, independent QEMU cross-checks, original stock parser/libc/status/JobMgr/
lifecycle/admission differential tests, instruction annotation audit, scanner negative
cases, reproducibility and dry-run harnesses. Logs
are saved outside the repo and printed on failure. It never opts into USB or
printing. Do not run suites in parallel: they regenerate shared files.
For a narrow edit, use its existing generator/check first; for documentation
alone, verify references and the diff. Do not rerun every check without a reason.

The aggregate command requires the existing local research dependencies. It does
not install anything automatically. Scratch tools may disappear after cleanup:

| Dependency | Recovery / location |
|---|---|
| BE Xtensa binutils | `scripts/build-xtensa-binutils-manual.sh`; default prefix `/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf`, override `XTENSA_PREFIX` |
| BE/call0 GCC 14.3.0 | `scripts/build-xtensa-gcc-manual.sh`; default prefix `/tmp/hp1020-xtensa-gcc14/bin/xtensa-fsf-elf`, component-build override `HP1020_GCC_PREFIX`. GCC was recovered again on 2026-09-28 through the pinned script and checksum/encoding/profile gates, including headers and libgcc; log `/tmp/hp1020-gcc-recovery-20260928.log`. Sandbox DNS failure required network permission for the same pinned download. Disposable files may still need recovery later. |
| Independent ISA engine | Homebrew `qemu` (verified 11.1.1); `qemu-system-xtensaeb`, override `HP1020_QEMU`. The harness uses `sim -cpu test_kc705_be`, synthetic RAM and a private Unix GDB socket; no network/USB/backend. `fsf` lacks GDB registers and is unsuitable. Recover with `brew install qemu`, then run the QEMU validator. |
| Host tools | Homebrew Bash (the suites use `mapfile`), Python 3, clang, Ghostscript/GNU sed and existing foo2zjs runtime; compiler rebuild additionally needs GNU make, GMP, MPFR and MPC |
| Optional deeper decoding | Saved Ghidra output is retained; refresh scripts require Ghidra and Homebrew `openjdk@21`. Pcode experiments use `/tmp/hp1020-astra-pcode-venv` (pypcode 4.0.0 and z3-solver) |

The corrected assembler overlay is pinned in its build script. Historical
crosstool-NG tools under `/tmp/hp1020-ctng-mnt/` were corrupt; a tool name or BE
ELF header is insufficient. Every probe build checks actual instruction bytes.
C target builds check the conservative compiler profile. The synthetic target
ELF at `0x20000000` must never be treated as a printer upload image.

## Evidence layout and trust

- `assets/firmware-source/` and the extracted stock ELF are the original input;
  `analysis/ghidra*`, disassembly directories, symbols and raw captures preserve
  investigation evidence. Locate exact files through the relevant generator.
- `scripts/model-*`, `extract-*`, `project-*` and `check-*` derive the reports.
  Find a report's producer with `rg` under `scripts/`. Change the producer first.
- `analysis/open-firmware-model/` holds executable parser/planning models and
  fixtures; `analysis/open-firmware-probes/` holds built artifacts and audits.
- `analysis/usb-path/`, `hardware-boundary/` and `status-path/` organize the current
  narrow path. Older top-level `*-report.md` files retain broader exploration;
  they are evidence from a point in time, not independent current roadmaps.
- Saved Ghidra C can omit switch arms and arguments. Check raw bytes/control flow
  before promoting a claim. Static models do not establish physical behavior.

The previous broad roadmap and early toolchain summaries were removed after
being superseded; Git retains them. The historical tool inventory remains as
raw evidence, explicitly labeled. Preserve other reports at stable paths because
scripts cross-reference or consume them. Do not duplicate the full inventory in
`AGENTS.md`, add per-session handoff files, or keep parallel lists of next steps.
