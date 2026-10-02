# First typed-offload execution capture

`first-58-cases.tar.gz` preserves all files from the first58 host/58 QEMU run,
its log, the independent transcript gate and archive-verification source.
The companion JSON records every member hash. Before archiving, all126 source
and six fixture hashes,5422 paired368-word event rows, event input bytes and
464 complete host/target capture pairs were independently checked. Only the
established architecture-dependent structure-size word differs across engines.
Archive contents were read back byte-for-byte after compression.

`unexecuted-proposals.tar.gz` preserves V1/V2 implementation and scenario drafts,
the earlier driver/gate drafts, ordinary-regression drafts and static reviews.
V1's repeated-configuration assumption was corrected before first execution.
These standalone drafts were never executed; the first-run archive holds the
actual integrated tested bytes, including the separately added connection-state
witness and comments-only integration corrections. No failed run preceded this
first paired run. Later report regeneration does not change these archives.
The first provenance metadata mislabeled zero-based PDF offsets as one-based
pages. Direct page extraction corrected the live reference to271/284/287 before
the full rerun; the original PDF bytes/sections and archived metadata are intact.

`independent-gate-review` preserves the later strengthened gate and its first
diagnostic. Four initial oracle assumptions were corrected against original
inputs, fixture/control flow and raw rows; production and tested-report bytes
were unchanged. The corrected gate rechecked the frozen first capture and all
raw inputs/outputs. Eight disposable report mutations independently test agreed
wrong pixels/document generations, missing ZLP, invented promises, retagged raw
failure, wrong-event grant, wrong effective core and wrong target identity.
All are rejected and the original evidence is restored and rechecked afterward.

This is synthetic RAM execution with supplied hardware facts. It establishes no
USB traffic, MMIO effects, native page lifecycle, physical printing or recovery
after a device power cycle.
