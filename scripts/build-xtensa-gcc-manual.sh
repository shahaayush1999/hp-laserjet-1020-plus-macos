#!/usr/bin/env bash
# Rebuild the verified freestanding compiler in dedicated scratch directories.
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION=14.3.0
ARCHIVE="${HP1020_GCC_ARCHIVE:-/tmp/hp1020-gcc-14.3.0.tar.xz}"
SRC="${HP1020_GCC_SRC:-/tmp/gcc-14.3.0}"
BUILD="${HP1020_GCC_BUILD:-/tmp/hp1020-gcc14-build}"
PREFIX="${HP1020_GCC_INSTALL:-/tmp/hp1020-xtensa-gcc14}"
BIN_PREFIX="${XTENSA_PREFIX:-/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf}"
JOBS="${JOBS:-8}"
EXPECTED_SHA=e0dc77297625631ac8e50fa92fffefe899a4eb702592da5c32ef04e2293aca3a
if [[ ! -f "$ARCHIVE" ]]; then
  curl -fL --retry 2 "https://ftp.gnu.org/gnu/gcc/gcc-$VERSION/gcc-$VERSION.tar.xz" -o "$ARCHIVE"
fi
actual_sha="$(shasum -a 256 "$ARCHIVE" | awk '{print $1}')"
[[ "$actual_sha" == "$EXPECTED_SHA" ]] || { echo 'GCC source checksum mismatch' >&2; exit 1; }
python3 "$ROOT_DIR/scripts/check-xtensa-instruction-encoding.py" --prefix "$BIN_PREFIX"
mkdir -p "$SRC" "$BUILD"
# Restores the version-pinned upstream files before applying the configuration.
tar -xf "$ARCHIVE" --strip-components=1 -C "$SRC"
python3 - "$SRC/include/xtensa-config.h" <<'PY'
import re,sys
from pathlib import Path
p=Path(sys.argv[1]);s=p.read_text()
for name in ('DIV32','THREADPTR','RELEASE_SYNC','S32C1I','LOOPS','WINDOWED','ABS','MUL16','MINMAX','SEXT'):
    s,n=re.subn(r'(#define XCHAL_HAVE_'+name+r'\s+)1\b',r'\g<1>0',s)
    assert n==1,name
s,n=re.subn(r'(#define XSHAL_ABI\s+)XTHAL_ABI_WINDOWED',r'\g<1>XTHAL_ABI_CALL0',s)
assert n==1
assert re.search(r'#define XCHAL_HAVE_BE\s+1\b',s)
p.write_text(s)
PY
cd "$BUILD"
CC=clang CXX=clang++ "$SRC/configure" --target=xtensa-fsf-elf --prefix="$PREFIX" \
  --enable-languages=c --disable-bootstrap --disable-multilib --disable-nls \
  --disable-lto --disable-shared --disable-threads --disable-libssp \
  --disable-libquadmath --disable-libgomp --disable-libatomic --disable-libsanitizer \
  --disable-werror --without-headers --with-newlib --with-system-zlib --without-zstd \
  --with-gmp=/opt/homebrew/opt/gmp --with-mpfr=/opt/homebrew/opt/mpfr \
  --with-mpc=/opt/homebrew/opt/libmpc --with-as="$BIN_PREFIX-as" --with-ld="$BIN_PREFIX-ld"
gmake -j"$JOBS" all-gcc
gmake install-gcc
export PATH="$(dirname "$BIN_PREFIX"):$PATH"
# An incremental rebuild must not retain libgcc built for a previous ABI.
if [[ -f xtensa-fsf-elf/libgcc/Makefile ]]; then gmake clean-target-libgcc; fi
gmake -j"$JOBS" all-target-libgcc
gmake install-target-libgcc
macros="$("$PREFIX/bin/xtensa-fsf-elf-gcc" -dM -E -x c /dev/null)"
[[ "$macros" == *"__XTENSA_CALL0_ABI__"* && "$macros" == *"__XTENSA_EB__"* ]] || exit 1
printf 'Verified compiler: %s\n' "$PREFIX/bin/xtensa-fsf-elf-gcc"
