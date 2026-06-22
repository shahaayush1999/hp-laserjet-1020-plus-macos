# Xtensa Binutils Execution Status

This records the current local rebuild blocker for open-firmware artifacts.

## Result

The expected tool prefix exists:

```text
/tmp/hp1020-ctng-mnt/x-tools/xtensa-fsf-elf/bin/xtensa-fsf-elf
```

But the tools at that path do not execute on this macOS session.

Observed during `scripts/build-open-firmware-idle-probe.sh`:

```text
/tmp/hp1020-ctng-mnt/x-tools/xtensa-fsf-elf/bin/xtensa-fsf-elf-as: cannot execute binary file: Exec format error
```

`file` reports the current assembler/linker/objdump entries as generic `data`,
not runnable Mach-O binaries:

```text
/tmp/hp1020-ctng-mnt/x-tools/xtensa-fsf-elf/bin/xtensa-fsf-elf-as:      data
/tmp/hp1020-ctng-mnt/x-tools/xtensa-fsf-elf/bin/xtensa-fsf-elf-ld:      data
/tmp/hp1020-ctng-mnt/x-tools/xtensa-fsf-elf/bin/xtensa-fsf-elf-objdump: data
```

## Meaning

This is an environment/toolchain problem, not a firmware-logic finding. Existing
generated artifacts remain useful, but rebuilding them now needs a runnable
Xtensa big-endian binutils prefix.

`scripts/build-open-firmware-idle-probe.sh` now checks that each tool can run
before starting the build, so this fails early with a direct message.

## Next Fix

Set `XTENSA_PREFIX` to a runnable macOS toolchain prefix, or rebuild the
assembly-only Xtensa binutils toolchain for the current host before rebuilding
custom firmware probes.
