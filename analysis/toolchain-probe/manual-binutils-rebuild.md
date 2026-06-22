# Manual Xtensa Binutils Rebuild

This records the recovered build path for assembly-only open firmware probes.

## Result

Runnable tool prefix:

```text
/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf
```

Rebuild command:

```sh
scripts/build-xtensa-binutils-manual.sh
```

Smoke-test command:

```sh
scripts/probe-xtensa-binutils.sh
```

## What Failed Before This

The old crosstool-NG prefix under `/tmp/hp1020-ctng-mnt/x-tools/` existed but
its tool files were corrupt/zero-filled in this macOS session. They reported as
generic `data` and failed with `Exec format error`.

The crosstool-NG wrapper path also hit host-environment friction: normal `/tmp`
was not case-sensitive, and the case-sensitive mount carried bad build state and
logging failures. That made it the wrong place to spend more time for the
current assembly-only probes.

## Working Route

The successful route builds only binutils/gas/ld from Espressif's
`binutils-gdb` source at revision `0104f7d3`, with `--with-system-zlib` to avoid
the bundled zlib build issue and Homebrew `texinfo` for generated docs.

This does not provide GCC/newlib. That is fine for the current probes, which are
handwritten assembly and use no C runtime.

## Current Use

The open-firmware build scripts now prefer this prefix when it exists:

```text
/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf
```

Set `XTENSA_PREFIX=/path/to/xtensa-fsf-elf` to override it.
