#!/bin/zsh
# Shared by the repository install/remove commands, not the installed runtime.
set -euo pipefail
export PATH=/usr/bin:/bin:/usr/sbin:/sbin
if [[ "$(id -u)" == 0 ]]; then
  print -u2 -- "Run this script without sudo; it will ask for administrator access when needed."
  exit 1
fi

PRINTER_NAME="${HP1020_PRINTER_NAME:-HP_LaserJet_1020_Plus}"
LABEL="${HP1020_LABEL:-com.aayush.hp1020-root-spool-worker}"
USER_NAME="${HP1020_USER:-${SUDO_USER:-$USER}}"
USER_HOME="${HP1020_HOME:-$(dscl . -read "/Users/$USER_NAME" NFSHomeDirectory 2>/dev/null | sed 's/^NFSHomeDirectory: //')}"

if [[ -z "$USER_HOME" || "$USER_HOME" != /* || "$USER_HOME" == / || ! -d "$USER_HOME" ]]; then
  print -u2 -- "Could not determine a valid home directory for '$USER_NAME'."
  exit 1
fi
if [[ -z "$PRINTER_NAME" || "$PRINTER_NAME" == *[^a-zA-Z0-9_]* ||
      -z "$LABEL" || "$LABEL" == *[^a-zA-Z0-9.-]* ]]; then
  print -u2 -- "Invalid HP1020_PRINTER_NAME or HP1020_LABEL."
  exit 1
fi

# zsh's quoted output prevents paths, names and USB serials becoming shell code.
admin_variables() {
  print '#!/bin/zsh'
  print 'set -euo pipefail'
  print 'export PATH=/usr/bin:/bin:/usr/sbin:/sbin'
  local variable
  for variable in ROOT render_dir PRINTER_NAME LABEL USER_HOME USER_NAME; do
    printf '%s=%q\n' "$variable" "${(P)variable}"
  done
}

run_admin() {
  osascript \
    -e 'on run argv' \
    -e 'do shell script quoted form of item 1 of argv with administrator privileges' \
    -e 'end run' \
    "$1"
}

# Formula ownership is recorded per operation, not by comparing against an old
# machine-wide snapshot that might include software installed later by the user.
STATE="$USER_HOME/.local/state/hp1020"
BREW=/opt/homebrew/bin/brew
export HOMEBREW_NO_INSTALL_CLEANUP=1 HOMEBREW_NO_AUTOREMOVE=1
export HOMEBREW_NO_INSTALL_UPGRADE=1

record_dependencies() {
  [[ -f "$STATE/before" && -f "$STATE/expected" ]] || return 0
  "$BREW" list --formula -1 | LC_ALL=C sort -u > "$render_dir/after" || return 1
  touch "$STATE/formulae"
  LC_ALL=C comm -13 "$STATE/before" "$render_dir/after" > "$render_dir/added"
  LC_ALL=C comm -12 "$render_dir/added" "$STATE/expected" >> "$STATE/formulae"
  LC_ALL=C sort -u "$STATE/formulae" -o "$STATE/formulae"
  rm -f "$STATE/before" "$STATE/expected"
}

remove_dependencies() {
  [[ -d "$STATE" ]] || return 0
  if [[ ! -x "$BREW" ]]; then
    if [[ ! -e /opt/homebrew ]]; then
      rm -rf "$STATE"
      return 0
    fi
    print -u2 -- "Homebrew is incomplete or unavailable; its cleanup record is kept in $STATE."
    return 1
  fi
  record_dependencies || return 1
  local -a remaining next
  local formula dependents installed progress
  remaining=()
  [[ ! -f "$STATE/formulae" ]] || remaining=("${(@f)$(cat "$STATE/formulae")}")
  remaining=("${(@)remaining:#}")
  while (( ${#remaining} )); do
    next=()
    progress=0
    installed="$("$BREW" list --formula -1)" || return 1
    for formula in "${remaining[@]}"; do
      [[ "$formula" == [a-zA-Z0-9]* && "$formula" != *[^a-zA-Z0-9@+_.-]* ]] || return 1
      if ! printf '%s\n' "$installed" | grep -Fxq "$formula"; then
        progress=1
        continue
      fi
      dependents="$("$BREW" uses --installed --recursive --include-build --include-optional "$formula")" || return 1
      if [[ -n "$dependents" ]]; then
        next+=("$formula")
      else
        "$BREW" uninstall --formula "$formula" || return 1
        progress=1
      fi
    done
    remaining=("${next[@]}")
    (( progress )) || break
  done
  if (( ${#remaining} )); then
    print -- "Keeping packages now needed by other software: ${remaining[*]}"
  fi
  if [[ -f "$STATE/created-homebrew" ]]; then
    installed="$("$BREW" list --formula -1)" || return 1
    local casks
    casks="$("$BREW" list --cask -1)" || return 1
    if [[ -z "$installed" && -z "$casks" ]]; then
      print -- "Removing the Homebrew installation added by this setup..."
      curl --fail --location --proto '=https' --tlsv1.2 \
        https://raw.githubusercontent.com/Homebrew/install/HEAD/uninstall.sh \
        -o "$render_dir/homebrew-uninstall.sh" || return 1
      /bin/bash "$render_dir/homebrew-uninstall.sh" --force --path=/opt/homebrew || return 1
    else
      print -- "Keeping Homebrew because other software now uses it."
    fi
  fi
  rm -rf "$STATE"
}
