# Stopped full-suite stream-footprint gate

`stream-footprint-gate-20260929.tar.gz` preserves exactly the five files in
`/tmp/hp1020-full-continuous-recovery-failed-gate-20260929/`: the checker source
used by the stopped gate, its JSON and Markdown report, the measured stream
report and the untouched full-run log. This is selected failure evidence, not a
complete source closure or a new complete full-suite run. No absent sources or
results were reconstructed from the working tree.

The original checker expected 91028 bytes. The frozen passing stream report
measures 13192 bytes of state plus 77840 bytes of fixed memory, totaling 91032
bytes; every captured stream target case reports that same pair. The stopped
consistency report has 120 checks and one failure,
`open_bounded_stream_image_path_verified`, caused by the obsolete footprint gate.

The checker SHA-256 is
`712ce880e4b33a61092c6d26266385306741ea8241e5774b71078579a7984d95`.
The adjacent JSON records the archive SHA-256 and every member SHA-256; every
archived member was read back and verified against the frozen original bytes.
The saved checker, reports and log are not edited to reflect the correction.

At this archival checkpoint, the lead subsequently corrected the expected size
and observed 120 passing consistency checks. That later result is not present in
this stopped-run archive. The second probe suite did not run after the earlier
stop, so the latest completed full aggregate remains 118 checks and both suites.
A corrected consistency-only run does not establish a completed 120-check full
aggregate or physical printing.
