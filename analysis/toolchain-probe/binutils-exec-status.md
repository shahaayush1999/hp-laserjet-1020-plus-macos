# Xtensa Binutils Execution Status

This records the local rebuild blocker that was found, and the replacement
toolchain path now used for open-firmware artifacts.

## Broken Prefix

The crosstool-NG prefix exists:

```text
/tmp/hp1020-ctng-mnt/x-tools/xtensa-fsf-elf/bin/xtensa-fsf-elf
```

But the tools at that path do not execute on this macOS session. They were
later found to be zero-filled/corrupt entries, not usable host binaries.

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

## Recovery

A manual assembly-only binutils build now works:

```text
/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf
```

Rebuild it with:

```sh
scripts/build-xtensa-binutils-manual.sh
```

The build uses Espressif's `binutils-gdb` source at revision `0104f7d3`,
configures `--target=xtensa-fsf-elf --with-system-zlib`, and installs assembler,
linker, readelf, objdump, and objcopy. The generated tools are runnable macOS
Mach-O binaries and pass `scripts/probe-xtensa-binutils.sh`.

## Meaning

This is an environment/toolchain problem, not a firmware-logic finding. Existing
generated artifacts remain useful, but rebuilding them now needs a runnable
Xtensa big-endian binutils prefix.

The open-firmware build scripts now prefer the recovered manual prefix when it
exists. `XTENSA_PREFIX` can still override this for another toolchain.
