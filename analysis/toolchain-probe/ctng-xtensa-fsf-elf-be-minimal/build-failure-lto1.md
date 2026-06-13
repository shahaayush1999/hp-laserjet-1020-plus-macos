# crosstool-NG Minimal GCC Build Failure

This is the current blocker after binutils successfully installed.

## Build Shape

- Target: `xtensa-fsf-elf`
- Endian: big-endian
- Host compiler route: Homebrew GCC 15 shim
- crosstool-NG: 1.28.0
- Working volume: case-sensitive APFS sparsebundle under `/tmp/hp1020-ctng-mnt`

## Relevant Error

```text
aarch64-build_apple-darwin25.5.0-g++ ... -framework CoreFoundation -o lto1 ...
ld: warning: ignoring duplicate libraries: '../libcpp/libcpp.a', '../libdecnumber/libdecnumber.a', 'libcommon.a'
Undefined symbols for architecture arm64:
  "_host_hooks", referenced from:
      gt_pch_restore(__sFILE*) in libbackend.a[95](ggc-common.o)
      gt_pch_save(__sFILE*) in libbackend.a[95](ggc-common.o)
      toplev::main(int, char**) in libbackend.a[282](toplev.o)
ld: symbol(s) not found for architecture arm64
collect2: error: ld returned 1 exit status
make[3]: *** [lto1] Error 1
make[2]: *** [all-gcc] Error 2
```

## Current Hypothesis

This is a host-side GCC build issue on macOS, not evidence that Xtensa output is impossible. The binutils stage already completed and produced working tools.

The next config attempt disables GCC LTO:

```text
# CT_CC_GCC_USE_LTO is not set
```

For the immediate open-firmware spike, full GCC is optional because the first payload can be assembly-only.
