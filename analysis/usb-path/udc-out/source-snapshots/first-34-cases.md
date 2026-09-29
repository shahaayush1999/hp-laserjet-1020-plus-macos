# First bounded descriptor composition: 34 cases per engine

`first-34-cases.tar.gz` preserves the first execution from
`/tmp/hp1020-udc-out-kp273xzi`, plus the untouched log from
`/tmp/hp1020-udc-out-first-20260929.log` as `run.log`. The frozen report records
34 sanitized host and 34 Xtensa/QEMU cases passing with the tested source
unchanged during that run. This is RAM-only descriptor/adapter composition,
including independent exact pixels and document notifications; it is not
physical USB or printing evidence.

The archive includes the original full `validation.json`, all 97 recorded source
files with `source-sha256.json`, the patched effective TinyUSB source and its
manifest, all six copied fixture byte files with `fixture-sha256.json`, every
case's raw inputs/events, host and target captures (including descriptors), the
independent pixel oracle bytes, the target ELF and the log. Only disposable host
and reference executables and their host debug-symbol bundles are excluded.
No source or fixture was recovered from a later working-tree revision.

The adjacent JSON records the archive SHA-256 and every member SHA-256. Archive
members were read back and compared with the original bytes. All source,
effective-source, fixture, host/target capture and target-ELF hashes recorded in
the frozen report/manifests were independently checked against those saved bytes.

- Validator SHA-256: `360eed98d904d34d2e972c1c09c19330c1d91f109b8d833cc251f32152ffd944`.
- Frozen report SHA-256: `21d3889eadc6dbced80a26bda6ce3645cb979061dbbec5eafb54bbd816c3e625`.
- Target ELF SHA-256: `f6ac421b19f0845619a0da74a28969483a78115f21cfe29bd017773aa2863478`.
- Measured target adapter state and memory: 128536 bytes; descriptor component
  and descriptor overhead: 80 additional bytes.

The stock-byte/controller evidence named by the report is included in its source
closure. This run reuses prior original-code observations and executes zero new
stock instructions. Packet size/BE mode, CPU/DMA mapping, cache visibility and
publication order, immutable completion observations and transfer settlement
remain supplied. Descriptor ownership bits do not establish DMA settlement or
satisfy the three global recovery promises. The report adds zero native page
lifecycles, zero physical USB transfers and zero peripheral accesses. It proves
no real controller quiescence, boot, cache, engine, physical status, printing or
power-cycle recovery. Copies remain metadata and output is synchronous software.
