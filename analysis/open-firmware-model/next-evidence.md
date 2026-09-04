# Evidence required beyond the offline checkpoint

The offline work now has a byte-verified BE toolchain, corrected direct work
construction, instruction-tested framing and endpoint-0 staging, a bounded C
semantic parser, a page/band planner, and execution of the actual compiled C
components in synthetic RAM. The remaining questions concern device behavior or
core-specific operations absent from the available instruction definitions.

| Priority | Exact question | Existing evidence | Evidence that would resolve it |
|---|---|---|---|
| 1 | Does the corrected BE probe execute after the ROM loader, and can its own endpoint-0 path return its counter descriptor? | Stock-byte instruction fixtures and offline staging tests pass. The older quiet idle upload used incorrect instruction encoding. | A newly authorized cold-boot inert-probe test that returns the probe-specific descriptor. Stock USB identity alone is insufficient. |
| 2 | Does bulk OUT completion report the actual byte count and permit repeated acknowledgement/re-arm? | Static stock lane/descriptor/callback chain and offline framing tests. | The guarded 36-byte START_DOC/END_DOC transaction returns B=0x24, D=1, C=2, E=0, U=0; a later separately authorized repeat establishes re-arm. No page/raster input is needed. |
| 3 | What do the raster extension instructions do, including hidden state or memory effects? Can the stock-supported callback bypass produce acceptable output? | Exact four-argument callback contract, masks and complete instruction inventories. BPP2/600 has 16 unresolved extension instructions. | A core-specific ISA definition or controlled stock callback input/output trace; alternatively, measured stock behavior with its supported bypass setting. Custom opcodes are not assumed safe for a probe. |
| 4 | Do the two video channels implement the inferred compressed-input and row-output handshake, including length/progress units, cache visibility and descriptor ownership? | BIH/BID pointer chain, direct VIDEO_Y seed, corrected floor division, bounded host partitions and static channel writes. | A stock first-page trace showing channel lengths/status, buffer contents, ownership transitions and completion order. No custom video writes are authorized. |
| 5 | Which physical engine conditions correspond to the polled status bits/events, and what are safe timing, timeout and recovery boundaries for startup, page start and completion? | Executable status/IRQ decision models and ordered stock command sequences. | Calibrated stock behavior for idle, page acceptance, completion and relevant fault states. Numeric event values are not physical labels. |

The logical-clip metadata mismatch and BPP4 zero-refill case are already isolated
and rejected by the narrow page planner; they are not reasons to expand the
first hardware test. Other modes, malformed-input compatibility and optimization
are outside this first printing scope.

The immediate next experiment remains the existing non-printing USB ladder.
Further combined firmware integration cannot establish any of the device facts
above. Once boot/USB behavior is proven, the validated C component can be joined
to that transport; any later print-driving video/engine work still requires
explicit permission and the corresponding hardware evidence.

No printer was contacted for this checkpoint. This document is an evidence
request for future authorized work, not authorization to run a hardware test.
