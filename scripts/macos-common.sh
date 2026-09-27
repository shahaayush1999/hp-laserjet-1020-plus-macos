#!/bin/zsh
# Shared by the repository install/remove commands, not the installed runtime.
set -euo pipefail
export PATH=/usr/bin:/bin:/usr/sbin:/sbin

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
  for variable in ROOT render_dir PRINTER_NAME LABEL USER_HOME; do
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
