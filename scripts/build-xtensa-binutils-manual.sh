#!/usr/bin/env bash
set -euo pipefail

SRC_DIR="${XTENSA_BINUTILS_SRC:-/tmp/hp1020-binutils-manual-src}"
BUILD_DIR="${XTENSA_BINUTILS_BUILD:-/tmp/hp1020-binutils-manual-build-systemz}"
PREFIX="${XTENSA_BINUTILS_PREFIX:-/tmp/hp1020-xtensa-manual-systemz}"
REVISION="${XTENSA_BINUTILS_REVISION:-0104f7d3}"
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

printf '%s\n' "$PREFIX/bin/xtensa-fsf-elf"
