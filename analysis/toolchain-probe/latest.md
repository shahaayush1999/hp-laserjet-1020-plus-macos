# Firmware Toolchain Probe

Repo: `/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos`

## Analysis/Container Tools

| Tool | Present | Path |
| --- | --- | --- |
| `gobjdump` | `yes` | `/opt/homebrew/opt/binutils/bin/gobjdump` |
| `gobjcopy` | `yes` | `/opt/homebrew/opt/binutils/bin/gobjcopy` |
| `greadelf` | `yes` | `/opt/homebrew/opt/binutils/bin/greadelf` |
| `objdump` | `yes` | `/usr/bin/objdump` |
| `objcopy` | `yes` | `/opt/homebrew/opt/binutils/bin/objcopy` |
| `readelf` | `yes` | `/opt/homebrew/opt/binutils/bin/readelf` |
| `rabin2` | `yes` | `/opt/homebrew/bin/rabin2` |
| `r2` | `yes` | `/opt/homebrew/bin/r2` |

## Build Tools

| Tool | Present | Path |
| --- | --- | --- |
| `xtensa-fsf-elf-as` | `yes` | `/tmp/hp1020-ctng-mnt/x-tools/xtensa-fsf-elf/bin/xtensa-fsf-elf-as` |
| `xtensa-fsf-elf-ld` | `yes` | `/tmp/hp1020-ctng-mnt/x-tools/xtensa-fsf-elf/bin/xtensa-fsf-elf-ld` |
| `xtensa-fsf-elf-readelf` | `yes` | `/tmp/hp1020-ctng-mnt/x-tools/xtensa-fsf-elf/bin/xtensa-fsf-elf-readelf` |
| `xtensa-fsf-elf-objdump` | `yes` | `/tmp/hp1020-ctng-mnt/x-tools/xtensa-fsf-elf/bin/xtensa-fsf-elf-objdump` |
| `xtensa-lx106-elf-gcc` | `no` | `` |
| `xtensa-lx106-elf-as` | `no` | `` |
| `xtensa-esp32-elf-gcc` | `no` | `` |
| `xtensa-esp32-elf-as` | `no` | `` |
| `xtensa-esp-elf-gcc` | `no` | `` |
| `xtensa-esp-elf-as` | `no` | `` |
| `llvm-mc` | `yes` | `/opt/homebrew/opt/llvm/bin/llvm-mc` |
| `llvm-objcopy` | `yes` | `/opt/homebrew/opt/llvm/bin/llvm-objcopy` |
| `llvm-readobj` | `yes` | `/opt/homebrew/opt/llvm/bin/llvm-readobj` |
| `llvm-objdump` | `yes` | `/opt/homebrew/opt/llvm/bin/llvm-objdump` |
| `clang` | `yes` | `/usr/bin/clang` |
| `ct-ng` | `yes` | `/opt/homebrew/bin/ct-ng` |

## Compiler Target Support

clang target probe: `/opt/homebrew/opt/llvm/bin/clang`

- clang/LLVM Xtensa target: missing

## Xtensa ELF Format Support

objdump used: `/opt/homebrew/opt/binutils/bin/gobjdump`

- `elf32-xtensa-be`: present
- `elf32-xtensa-le`: present

## Homebrew Search

- xtensor

## crosstool-NG Samples

ct-ng used: `/opt/homebrew/bin/ct-ng`

- [G..X]   xtensa-fsf-elf
- [G...]   xtensa-fsf-linux-uclibc
