#!/bin/zsh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source "$ROOT/scripts/macos-common.sh"

render_dir="$(mktemp -d -t hp1020-remove.XXXXXX)"
trap 'rm -rf "$render_dir"' EXIT
admin_script="$render_dir/remove-admin"
admin_variables > "$admin_script"
cat >> "$admin_script" <<'ADMIN'
PLIST="/Library/LaunchDaemons/$LABEL.plist"
queue_existed=0
lpstat -p "$PRINTER_NAME" >/dev/null 2>&1 && queue_existed=1
if (( queue_existed )); then cupsreject "$PRINTER_NAME"; fi
cancel -a "$PRINTER_NAME" 2>/dev/null || true
launchctl bootout system "$PLIST" 2>/dev/null || true
launchctl bootout "gui/$(id -u "$USER_NAME")/com.aayush.hp1020-spool-worker" 2>/dev/null || true
if (( queue_existed )); then lpadmin -x "$PRINTER_NAME"; fi
rm -f "$PLIST"
rm -f /usr/libexec/cups/backend/hp1020queue
rm -f /usr/libexec/cups/filter/hp1020passthrough
rm -f "/private/etc/cups/ppd/$PRINTER_NAME.ppd"
rm -rf /Library/Printers/hp1020
rm -rf /private/var/spool/cups/tmp/hp1020queue
rm -f "$USER_HOME/bin/hp1020-print"
rm -rf "$USER_HOME/.local/share/hp1020"
rm -f "$USER_HOME/Library/LaunchAgents/com.aayush.hp1020-spool-worker.plist"
ADMIN
chmod 700 "$admin_script"
zsh -n "$admin_script"
run_admin "$admin_script"
if ! remove_dependencies; then
  print -u2 -- "Printer files removed. Package cleanup did not finish; run this uninstall script again."
  exit 1
fi
print -- "Removed HP LaserJet 1020 Plus and cleaned up the packages added by this setup."
