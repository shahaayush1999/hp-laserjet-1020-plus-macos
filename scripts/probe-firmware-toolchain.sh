#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

find_tool() {
  local tool="$1"
  local found
  found="$(command -v "$tool" 2>/dev/null || true)"
  if [[ -n "$found" ]]; then
    printf '%s' "$found"
    return
  fi
  for candidate in \
    "/opt/homebrew/opt/binutils/bin/$tool" \
    "/usr/local/opt/binutils/bin/$tool" \
    "/opt/homebrew/bin/$tool" \
    "/usr/local/bin/$tool"
  do
    if [[ -x "$candidate" ]]; then
      printf '%s' "$candidate"
      return
    fi
  done
}

have_tool() {
  if [[ -n "$(find_tool "$1")" ]]; then
    printf 'yes'
  else
    printf 'no'
  fi
}

binutils_objdump=""
for candidate in \
  /opt/homebrew/opt/binutils/bin/gobjdump \
  /usr/local/opt/binutils/bin/gobjdump \
  gobjdump \
  objdump
do
  if command -v "$candidate" >/dev/null 2>&1; then
    binutils_objdump="$(command -v "$candidate")"
    break
  elif [[ -x "$candidate" ]]; then
    binutils_objdump="$candidate"
    break
  fi
done

printf '# Firmware Toolchain Probe\n'
printf '\n'
printf 'Repo: `%s`\n' "$ROOT_DIR"
printf '\n'
printf '## Analysis/Container Tools\n'
printf '\n'
printf '| Tool | Present | Path |\n'
printf '| --- | --- | --- |\n'
for tool in gobjdump gobjcopy greadelf objdump objcopy readelf rabin2 r2; do
  printf '| `%s` | `%s` | `%s` |\n' "$tool" "$(have_tool "$tool")" "$(find_tool "$tool")"
done

printf '\n'
printf '## Build Tools\n'
printf '\n'
printf '| Tool | Present | Path |\n'
printf '| --- | --- | --- |\n'
for tool in \
  xtensa-lx106-elf-gcc \
  xtensa-lx106-elf-as \
  xtensa-esp32-elf-gcc \
  xtensa-esp32-elf-as \
  xtensa-esp-elf-gcc \
  xtensa-esp-elf-as \
  llvm-mc \
  llvm-objcopy \
  llvm-readobj \
  llvm-objdump \
  clang
do
  printf '| `%s` | `%s` | `%s` |\n' "$tool" "$(have_tool "$tool")" "$(find_tool "$tool")"
done

printf '\n'
printf '## Xtensa ELF Format Support\n'
printf '\n'
if [[ -n "$binutils_objdump" ]]; then
  printf 'objdump used: `%s`\n\n' "$binutils_objdump"
  objdump_targets="$("$binutils_objdump" -i)"
  if grep -q 'elf32-xtensa-be' <<<"$objdump_targets"; then
    printf '%s\n' '- `elf32-xtensa-be`: present'
  else
    printf '%s\n' '- `elf32-xtensa-be`: missing'
  fi
  if grep -q 'elf32-xtensa-le' <<<"$objdump_targets"; then
    printf '%s\n' '- `elf32-xtensa-le`: present'
  else
    printf '%s\n' '- `elf32-xtensa-le`: missing'
  fi
else
  printf 'No usable objdump found.\n'
fi

printf '\n'
printf '## Homebrew Search\n'
printf '\n'
if command -v brew >/dev/null 2>&1; then
  brew search xtensa 2>/dev/null | sed 's/^/- /'
else
  printf 'Homebrew not found.\n'
fi
