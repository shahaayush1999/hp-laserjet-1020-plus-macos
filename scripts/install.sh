#!/bin/zsh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source "$ROOT/scripts/macos-common.sh"

if [[ "$(uname -s)" != Darwin || "$(sysctl -n hw.optional.arm64 2>/dev/null || true)" != 1 ]]; then
  print -u2 -- "This setup requires an Apple Silicon Mac (M1 or newer)."
  exit 1
fi
os_version="$(sw_vers -productVersion)"
if (( ${os_version%%.*} < 11 )); then
  print -u2 -- "This setup requires macOS 11 or newer."
  exit 1
fi

runtime="$ROOT/assets/macos-arm64"
for file in gs gsed foo2zjs foo2zjs-wrapper foo2zjs-pstops sihp1020.dl SHA256SUMS; do
  [[ -s "$runtime/$file" ]] || { print -u2 -- "Missing $file. Download the complete repository again."; exit 1; }
done
print -- "Checking the included files..."
(cd "$ROOT" && shasum -a 256 -c assets/macos-arm64/SHA256SUMS > /dev/null)
render_dir="$(mktemp -d -t hp1020-install.XXXXXX)"
trap 'rm -rf "$render_dir"' EXIT
mkdir "$render_dir/runtime"
# After checksum verification, prepare only these bundled executables for use.
# Remove downloaded-file quarantine from the temporary copies, never globally.
stage_executable() {
  install -m 755 "$1" "$2"
  if xattr -p com.apple.quarantine "$2" > /dev/null 2>&1; then
    xattr -d com.apple.quarantine "$2"
  fi
}
for name in gs gsed foo2zjs foo2zjs-wrapper foo2zjs-pstops; do
  stage_executable "$runtime/$name" "$render_dir/runtime/$name"
done
stage_executable "$ROOT/files/cups/backend/hp1020queue" "$render_dir/hp1020queue"
stage_executable "$ROOT/files/cups/filter/hp1020passthrough" "$render_dir/hp1020passthrough"
env -i PATH=/usr/bin:/bin:/usr/sbin:/sbin "$render_dir/runtime/gs" --version > /dev/null
"$render_dir/runtime/gsed" --version > /dev/null
"$render_dir/runtime/foo2zjs" -V > /dev/null

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

escape_sed() { printf '%s' "$1" | sed 's/[&|\\]/\\&/g'; }
device_shell="$(escape_sed "${(qq)DEVICE_URI}")"
sed -e "s|@@DEVICE_URI_SHELL@@|$device_shell|g" \
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
mkdir -p "$BASE/runtime" "$BASE/Licenses" "$BASE/done" "$BASE/failed"
mkdir -p /private/var/spool/cups/tmp/hp1020queue
chown root:_lp /private/var/spool/cups/tmp/hp1020queue
chmod 2770 /private/var/spool/cups/tmp/hp1020queue

for name in gs gsed foo2zjs foo2zjs-wrapper foo2zjs-pstops; do
  install -m 755 -o root -g wheel "$render_dir/runtime/$name" "$BASE/runtime/$name"
done
install -m 644 -o root -g wheel "$ROOT/assets/macos-arm64/sihp1020.dl" "$BASE/runtime/sihp1020.dl"
install -m 644 -o root -g wheel "$ROOT/assets/macos-arm64/build-info.json" "$BASE/runtime/build-info.json"
for license in "$ROOT/assets/licenses/"*; do
  install -m 644 -o root -g wheel "$license" "$BASE/Licenses/${license:t}"
done
install -m 755 -o root -g wheel "$render_dir/hp1020queue" /usr/libexec/cups/backend/hp1020queue
install -m 755 -o root -g wheel "$render_dir/hp1020passthrough" /usr/libexec/cups/filter/hp1020passthrough
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
