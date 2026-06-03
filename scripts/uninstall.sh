#!/bin/zsh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PRINTER_NAME="${HP1020_PRINTER_NAME:-HP_LaserJet_1020_Plus}"
LABEL="${HP1020_LABEL:-com.aayush.hp1020-root-spool-worker}"
USER_NAME="${HP1020_USER:-${SUDO_USER:-$USER}}"
USER_HOME="${HP1020_HOME:-$(dscl . -read "/Users/$USER_NAME" NFSHomeDirectory 2>/dev/null | awk '{print $2}')}"

if [[ -z "$USER_HOME" || ! -d "$USER_HOME" ]]; then
  print "Could not determine a valid home directory for user '$USER_NAME'." >&2
  exit 1
fi

admin_script="$(mktemp -t hp1020-uninstall-admin.XXXXXX.sh)"
cat > "$admin_script" <<EOF
#!/bin/sh
set -eu
PRINTER_NAME="$PRINTER_NAME"
LABEL="$LABEL"
USER_HOME="$USER_HOME"
PLIST="/Library/LaunchDaemons/$LABEL.plist"

cancel -a "\$PRINTER_NAME" 2>/dev/null || true
lpadmin -x "\$PRINTER_NAME" 2>/dev/null || true

launchctl bootout system "\$PLIST" 2>/dev/null || true
rm -f "\$PLIST"

rm -f /usr/libexec/cups/backend/hp1020queue
rm -f /usr/libexec/cups/filter/hp1020passthrough
rm -f "/private/etc/cups/ppd/\$PRINTER_NAME.ppd"
rm -rf /Library/Printers/hp1020
rm -rf /private/var/spool/cups/tmp/hp1020queue

rm -f "\$USER_HOME/bin/hp1020-print"
rm -rf "\$USER_HOME/.local/share/hp1020"
rm -f "\$USER_HOME/Library/LaunchAgents/com.aayush.hp1020-spool-worker.plist"

cupsctl --no-debug-logging 2>/dev/null || true
EOF
chmod 700 "$admin_script"

osascript \
  -e 'on run argv' \
  -e 'do shell script quoted form of item 1 of argv with administrator privileges' \
  -e 'end run' \
  "$admin_script"

rm -f "$admin_script"
print "Removed $PRINTER_NAME and hp1020 helper files."
