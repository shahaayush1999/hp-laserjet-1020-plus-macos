#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

SRC_DIR="${XTENSA_BINUTILS_SRC:-/tmp/hp1020-binutils-manual-src}"
BUILD_DIR="${XTENSA_BINUTILS_BUILD:-/tmp/hp1020-binutils-manual-build-systemz}"
PREFIX="${XTENSA_BINUTILS_PREFIX:-/tmp/hp1020-xtensa-manual-systemz}"
REVISION="${XTENSA_BINUTILS_REVISION:-0104f7d3c1}"
# Matching BE ISA overlay, before the 2010 default module switched to LE.
BE_ISA_REVISION="1e225492405c82b0b7b9973d8f549e1411168e3d"
JOBS="${JOBS:-$(sysctl -n hw.ncpu)}"

if ! command -v git >/dev/null 2>&1; then
  printf 'missing git\n' >&2
  exit 1
fi
if ! command -v gmake >/dev/null 2>&1; then
  printf 'missing gmake; install Homebrew make\n' >&2
  exit 1
fi
if ! command -v makeinfo >/dev/null 2>&1; then
  if [[ -x /opt/homebrew/opt/texinfo/bin/makeinfo ]]; then
    export PATH="/opt/homebrew/opt/texinfo/bin:$PATH"
  else
    printf 'missing makeinfo; install Homebrew texinfo\n' >&2
    exit 1
  fi
fi

if [[ ! -d "$SRC_DIR/.git" ]]; then
  rm -rf "$SRC_DIR"
  git clone --filter=blob:none https://github.com/espressif/binutils-gdb.git "$SRC_DIR"
fi

git -C "$SRC_DIR" fetch --depth=1 origin "$REVISION" >/dev/null 2>&1 || true
git -C "$SRC_DIR" checkout "$REVISION"

# The chosen tree has BE xtensa-config.h but an LE bfd/xtensa-modules.c.
# ELF endianness flags cannot repair instruction encoding. Install the matching
# upstream BE overlay, not a one-bit edit of the LE tables.
git -C "$SRC_DIR" show "$BE_ISA_REVISION:bfd/xtensa-modules.c" > "$SRC_DIR/bfd/xtensa-modules.c"

rm -rf "$BUILD_DIR" "$PREFIX"
mkdir -p "$BUILD_DIR" "$PREFIX"

cd "$BUILD_DIR"
"$SRC_DIR/configure" \
  --target=xtensa-fsf-elf \
  --prefix="$PREFIX" \
  --disable-nls \
  --disable-werror \
  --disable-gdb \
  --disable-sim \
  --disable-libdecnumber \
  --disable-readline \
  --disable-gprof \
  --with-system-zlib

gmake -j"$JOBS" all-binutils all-gas all-ld
gmake install-binutils install-gas install-ld

for tool in as ld readelf objdump objcopy; do
  "$PREFIX/bin/xtensa-fsf-elf-$tool" --version >/dev/null
done

python3 "$ROOT_DIR/scripts/check-xtensa-instruction-encoding.py" --prefix "$PREFIX/bin/xtensa-fsf-elf"

printf '%s\n' "$PREFIX/bin/xtensa-fsf-elf"
