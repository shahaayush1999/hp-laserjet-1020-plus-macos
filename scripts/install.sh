#!/bin/zsh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source "$ROOT/scripts/macos-common.sh"

if [[ "$(uname -s)" != Darwin || "$(sysctl -n hw.optional.arm64 2>/dev/null || true)" != 1 ]]; then
  print -u2 -- "This setup requires an Apple Silicon Mac (M1 or newer)."
  exit 1
fi
render_dir="$(mktemp -d -t hp1020-install.XXXXXX)"
trap 'rm -rf "$render_dir"' EXIT
if ! xcrun --find clang > /dev/null 2>&1; then
  xcode-select --install 2>/dev/null || true
  print -u2 -- "Finish Apple's Command Line Tools installation, then run this script again."
  exit 1
fi

# Stop before changing files if this queue still has work waiting.
if [[ -n "$(lpstat -W not-completed -o "$PRINTER_NAME" 2>/dev/null || true)" ]]; then
  print -u2 -- "Finish or cancel this printer's pending jobs, then run installation again."
  exit 1
fi

DEVICE_URI="${HP1020_DEVICE_URI:-}"
if [[ -z "$DEVICE_URI" ]]; then
  detected="$(lpinfo -v 2>/dev/null || true)"
  devices=("${(@f)$(printf '%s\n' "$detected" | awk '$1 == "direct" && $2 ~ /^usb:\/\/Hewlett-Packard\/HP%20LaserJet%201020([?]|%20|$)/ { print $2 }' | sort -u)}")
  devices=("${(@)devices:#}")
  if (( ${#devices} != 1 )); then
    print -u2 -- "Connect one HP LaserJet 1020 Plus by USB, turn it on, then run installation again."
    exit 1
  fi
  DEVICE_URI="$devices[1]"
fi
if [[ "$DEVICE_URI" != usb://Hewlett-Packard/HP%20LaserJet%201020* || "$DEVICE_URI" == *$'\n'* ]]; then
  print -u2 -- "HP1020_DEVICE_URI is not an HP LaserJet 1020 USB address."
  exit 1
fi

install_dependencies
print -- "Building the printer helper for this Mac..."
zsh "$ROOT/scripts/rebuild-runtime-from-vendor.sh" "$render_dir/runtime"

escape_sed() { printf '%s' "$1" | sed 's/[&|\\]/\\&/g'; }
device_shell="$(escape_sed "${(qq)DEVICE_URI}")"
brew_shell="$(escape_sed "${(qq)BREW_PREFIX}")"
sed -e "s|@@DEVICE_URI_SHELL@@|$device_shell|g" \
  -e "s|@@BREW_PREFIX_SHELL@@|$brew_shell|g" \
  "$ROOT/templates/hp1020-print.in" > "$render_dir/hp1020-print"
cat "$ROOT/templates/hp1020-root-spool-worker.in" > "$render_dir/hp1020-root-spool-worker"
sed -e "s|@@LABEL@@|$LABEL|g" \
  "$ROOT/templates/com.aayush.hp1020-root-spool-worker.plist.in" > "$render_dir/$LABEL.plist"
zsh -n "$render_dir/hp1020-print"
zsh -n "$render_dir/hp1020-root-spool-worker"
plutil -lint "$render_dir/$LABEL.plist" > /dev/null

admin_script="$render_dir/install-admin"
admin_variables > "$admin_script"
cat >> "$admin_script" <<'ADMIN'
BASE="/Library/Printers/hp1020"
PLIST="/Library/LaunchDaemons/$LABEL.plist"
PPD="$BASE/HP-LaserJet_1020-Plus-hp1020zjs.ppd"
umask 022
launchctl bootout system "$PLIST" 2>/dev/null || true
rm -rf "$BASE/runtime" "$BASE/Licenses"
mkdir -p "$BASE/runtime" "$BASE/Licenses" "$BASE/done" "$BASE/failed"
mkdir -p /private/var/spool/cups/tmp/hp1020queue
chown root:_lp /private/var/spool/cups/tmp/hp1020queue
chmod 2770 /private/var/spool/cups/tmp/hp1020queue

for name in foo2zjs foo2zjs-wrapper foo2zjs-pstops; do
  install -m 755 -o root -g wheel "$render_dir/runtime/$name" "$BASE/runtime/$name"
done
install -m 644 -o root -g wheel "$render_dir/runtime/sihp1020.dl" "$BASE/runtime/sihp1020.dl"
for license in "$ROOT/assets/licenses/"*; do
  install -m 644 -o root -g wheel "$license" "$BASE/Licenses/${license:t}"
done
install -m 755 -o root -g wheel "$ROOT/files/cups/backend/hp1020queue" /usr/libexec/cups/backend/hp1020queue
install -m 755 -o root -g wheel "$ROOT/files/cups/filter/hp1020passthrough" /usr/libexec/cups/filter/hp1020passthrough
install -m 644 -o root -g wheel "$ROOT/files/ppd/HP-LaserJet_1020-Plus-hp1020zjs.ppd" "$PPD"
install -m 755 -o root -g wheel "$render_dir/hp1020-print" "$BASE/hp1020-print"
install -m 755 -o root -g wheel "$render_dir/hp1020-root-spool-worker" "$BASE/hp1020-root-spool-worker"
install -m 644 -o root -g wheel "$render_dir/$LABEL.plist" "$PLIST"

lpadmin -p "$PRINTER_NAME" -E -v hp1020queue://localhost -P "$PPD" -L USB -D "HP LaserJet 1020 Plus"
lpadmin -p "$PRINTER_NAME" -o printer-error-policy=retry-job -o printer-is-shared=false
cupsaccept "$PRINTER_NAME"
cupsenable "$PRINTER_NAME"
launchctl bootstrap system "$PLIST"
launchctl enable "system/$LABEL"
launchctl kickstart -k "system/$LABEL"

# Retire the earlier per-user runtime only after the replacement is installed.
rm -f "$USER_HOME/bin/hp1020-print"
rm -rf "$USER_HOME/.local/share/hp1020"
ADMIN
chmod 700 "$admin_script"
zsh -n "$admin_script"
run_admin "$admin_script"
print -- "Installed. In any app, choose Print and select HP LaserJet 1020 Plus."
