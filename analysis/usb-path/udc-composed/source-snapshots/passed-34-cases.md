# Composed UDC: 34 host and 34 QEMU cases

`passed-34-cases.tar.gz` preserves `/tmp/hp1020-udc-composed-ql5zodos` and the
untouched `/tmp/hp1020-udc-composed-reconnect-helper-20260929.log` as `run.log`.
The captured `validation.json` records 34 sanitized host profiles and 34 QEMU
replays. This is the focused composed-boundary result, not an aggregate suite
or physical-printing checkpoint. The earlier 12-host stop remains separately
preserved in `first-host12-reconfigure-stop.*`.

All 117 recorded source files, six exact fixtures, 19 materialized TinyUSB files,
all 34 host/target case captures, all 28 target artifacts and the original report
are preserved. Each case includes events, original host stdout/stderr, separate
base/EP0/OUT+SETUP step rows, target rows, exact wire/pixels/document events,
receive/output storage and complete guarded EP0, OUT and SETUP captures. The
archive also retains the ELF, both disassembly listings, symbols, map, stack-use
files and effective-source metadata. Disposable host executables and their
`.dSYM` bundles alone are omitted and listed in the adjacent manifest.

All saved source/fixture/effective-source hashes match their recorded bytes and
report. Every reported host and target capture hash, target artifact hash and
ELF hash was checked against the saved files. Event/step records match the saved
report; host/target rows differ only at the measured native structure-size word.
All case bytes and document notifications match their recorded counterparts.
Every archived member was reread and hashed after compression. These are archive
integrity checks; no validator, builder or firmware execution was repeated.

Compared with the first stopped source closure, file sets, all C sources,
fixtures and effective TinyUSB bytes are identical. The sole changed source is
`scripts/validate-hp1020-udc-composed.py`: its reconnect helper keeps the previous
class request id and reservation counts, then requires the normal three recovery
promises. The reported target adapter state/allocation is 128536 bytes, plus
EP0 296, bulk 80 and SETUP 88 bytes; fixture/capture storage is separate.

- Validator SHA256: `982f4680fe409521b982b1d25eb77daead763672a5977e19fef7f45d65dcd720`.
- Captured report SHA256: `aacd93d073cc5d7f8431621d2d97e6aaddb2b6bd64f9883e516240ccb795b26b`.
- Target ELF SHA256: `7b6cdb1bb10d89135270b8262430a5d2fca6543bab67882ed889a0c1b60bc4e2`.
- Archive SHA256: `52fd98cb37ab866c280ae394d3668a6502e7fa7ae8d3e76f5adcd47bc3d96377`.

The report preserves zero new stock-instruction execution, zero native-page
lifecycles, zero peripheral accesses and zero physical USB transfers. Event
ordering, CPU/DMA mapping, packet mode, visibility, hardware stall clearing and
controller settlement remain supplied facts. IN length is separately supplied.
Terminal descriptor settlement can leave adapter notifications pending; it is
not completed recovery. No physical DCD, printing or power-cycle recovery is
established, and the installed printing setup was untouched.
