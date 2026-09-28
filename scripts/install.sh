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
if [[ "$DEVICE_URI" != usb://Hewlett-Packard/HP%20LaserJet%201020\?* || "$DEVICE_URI" == *$'\n'* || "$DEVICE_URI" == *$'\r'* ]]; then
  print -u2 -- "HP1020_DEVICE_URI is not an HP LaserJet 1020 USB address."
  exit 1
fi

print -- "Building the native Mac printer driver..."
zsh "$ROOT/scripts/rebuild-runtime-from-vendor.sh" "$render_dir/runtime"

escape_sed() { printf '%s' "$1" | sed 's/[&|\\]/\\&/g'; }
printer_shell="$(escape_sed "${(qq)PRINTER_NAME}")"
sed -e "s|@@PRINTER_NAME_SHELL@@|$printer_shell|g" \
  "$ROOT/templates/hp1020-print.in" > "$render_dir/hp1020-print"
zsh -n "$render_dir/hp1020-print"
# Filter files are checked with their installed ownership in the admin stage.
cupstestppd -q -I filters "$ROOT/files/ppd/HP-LaserJet_1020-Plus-hp1020zjs.ppd"

# Elevated AppleScript cannot read protected Documents folders. Stage every
# input before elevation; the administrator step never reads the repository.
cp "$ROOT/files/ppd/HP-LaserJet_1020-Plus-hp1020zjs.ppd" "$render_dir/printer.ppd"
cp "$ROOT/assets/licenses/foo2zjs-COPYING" "$render_dir/foo2zjs-COPYING"
admin_script="$render_dir/install-admin"
admin_variables > "$admin_script"
printf 'DEVICE_URI=%q\n' "$DEVICE_URI" >> "$admin_script"
cat >> "$admin_script" <<'ADMIN'
BASE="/Library/Printers/hp1020"
PLIST="/Library/LaunchDaemons/$LABEL.plist"
PPD="$BASE/HP-LaserJet_1020-Plus-hp1020zjs.ppd"
QUEUE_PPD="/private/etc/cups/ppd/$PRINTER_NAME.ppd"
umask 022
queue_existed=0
lpstat -p "$PRINTER_NAME" >/dev/null 2>&1 && queue_existed=1
queue_accepted=0
if LC_ALL=C lpstat -a "$PRINTER_NAME" 2>/dev/null | grep -q ' accepting requests'; then queue_accepted=1; fi
queue_enabled=1
if LC_ALL=C lpstat -p "$PRINTER_NAME" 2>/dev/null | grep -q ' disabled '; then queue_enabled=0; fi
old_uri=""
if (( queue_existed )); then
  old_uri="$(LC_ALL=C lpstat -v "$PRINTER_NAME" | sed 's/^[^:]*: //')"
  [[ -n "$old_uri" ]] || { print -u2 -- "Cannot save the existing queue address."; exit 1; }
fi
restore_acceptance() {
  (( queue_existed )) || return 0
  if (( queue_accepted )); then cupsaccept "$PRINTER_NAME" 2>/dev/null
  else cupsreject "$PRINTER_NAME" 2>/dev/null; fi
}
backup=""
before_replacement() {
  restore_acceptance || print -u2 -- "Could not restore the queue acceptance setting."
  [[ -z "$backup" ]] || rm -rf -- "$backup"
}
trap before_replacement EXIT
if (( queue_existed )); then cupsreject "$PRINTER_NAME"; fi
if [[ -n "$(lpstat -W not-completed -o "$PRINTER_NAME" 2>/dev/null || true)" ]]; then
  print -u2 -- "A print job arrived during setup. Finish or cancel it, then rerun installation."
  exit 1
fi
legacy_jobs=(/private/var/spool/cups/tmp/hp1020queue/*(N) /private/var/spool/cups/tmp/hp1020queue/.incoming.*(N))
if (( ${#legacy_jobs} )); then
  print -u2 -- "The previous printer worker still has queued work. Finish it before updating."
  exit 1
fi
backup="$(mktemp -d -t hp1020-rollback.XXXXXXXX)"
managed=("$BASE" /usr/libexec/cups/backend/hp1020queue
         /usr/libexec/cups/filter/hp1020passthrough /usr/libexec/cups/filter/hp1020zjs
         /usr/libexec/cups/backend/hp1020 "$PLIST" "$QUEUE_PPD")
for (( index=1; index<=${#managed}; index++ )); do
  [[ ! -e "$managed[$index]" ]] || cp -pR "$managed[$index]" "$backup/$index"
done
rollback() {
  trap - EXIT
  launchctl bootout system "$PLIST" 2>/dev/null || true
  restore_failed=0
  for (( index=1; index<=${#managed}; index++ )); do
    rm -rf -- "$managed[$index]" || restore_failed=1
    [[ ! -e "$backup/$index" ]] || cp -pR "$backup/$index" "$managed[$index]" || restore_failed=1
  done
  if (( queue_existed )); then
    lpadmin -p "$PRINTER_NAME" -v "$old_uri" -P "$QUEUE_PPD" 2>/dev/null || restore_failed=1
    restore_acceptance || restore_failed=1
    if (( queue_enabled )); then cupsenable "$PRINTER_NAME" 2>/dev/null || restore_failed=1
    else cupsdisable "$PRINTER_NAME" 2>/dev/null || restore_failed=1; fi
    [[ ! -f "$PLIST" ]] || launchctl bootstrap system "$PLIST" 2>/dev/null || restore_failed=1
  else
    lpadmin -x "$PRINTER_NAME" 2>/dev/null || restore_failed=1
  fi
  if (( restore_failed )); then
    print -u2 -- "Restoring the printer failed. The backup is preserved at $backup."
  else
    rm -rf -- "$backup"
    print -u2 -- "Installation failed; the previous printer setup was restored."
  fi
}
trap rollback EXIT
# A parent trap also catches fatal shell expansion errors in the child.
(
trap - EXIT
launchctl bootout system "$PLIST" 2>/dev/null || true
rm -rf "$BASE"
mkdir -p "$BASE/runtime" "$BASE/Licenses"
for name in rastertohp1020; do
  install -m 755 -o root -g wheel "$render_dir/runtime/$name" "$BASE/runtime/$name"
done
install -m 755 -o root -g wheel "$render_dir/runtime/hp1020" /usr/libexec/cups/backend/hp1020
install -m 644 -o root -g wheel "$render_dir/runtime/sihp1020.dl" "$BASE/runtime/sihp1020.dl"
install -m 644 -o root -g wheel "$render_dir/foo2zjs-COPYING" "$BASE/Licenses/foo2zjs-COPYING"
install -m 644 -o root -g wheel "$render_dir/printer.ppd" "$PPD"
install -m 755 -o root -g wheel "$render_dir/hp1020-print" "$BASE/hp1020-print"
for binary in "$BASE/runtime/rastertohp1020" /usr/libexec/cups/backend/hp1020; do
  codesign --verify --strict "$binary"
  "$binary" --version > /dev/null
done
cupstestppd -q "$PPD"
queue_uri="hp1020:${DEVICE_URI#usb:}"
lpadmin -p "$PRINTER_NAME" -v "$queue_uri" -P "$PPD" -L USB -D "HP LaserJet 1020 Plus"
lpadmin -p "$PRINTER_NAME" -o printer-error-policy=stop-printer -o printer-is-shared=false
lpadmin -p "$PRINTER_NAME" -o multiple-document-handling-default=separate-documents-collated-copies
cupsenable "$PRINTER_NAME"
cupsaccept "$PRINTER_NAME"
)
trap - EXIT
rm -rf -- "$backup"
# Remove the retired bridge only after native components and queue are ready.
rm -f "$PLIST" /usr/libexec/cups/backend/hp1020queue
rm -f /usr/libexec/cups/filter/hp1020passthrough /usr/libexec/cups/filter/hp1020zjs
rmdir /private/var/spool/cups/tmp/hp1020queue 2>/dev/null || true
launchctl bootout "gui/$(id -u "$USER_NAME")/com.aayush.hp1020-spool-worker" 2>/dev/null || true
rm -f "$USER_HOME/Library/LaunchAgents/com.aayush.hp1020-spool-worker.plist"
rm -f "$USER_HOME/bin/hp1020-print"
rm -rf "$USER_HOME/.local/share/hp1020"
ADMIN
chmod 700 "$admin_script"
zsh -n "$admin_script"
run_admin "$admin_script"
# New installations need no Homebrew packages. Clean only ownership recorded
# by earlier versions, preserving pre-existing packages and other dependents.
if ! remove_dependencies; then
  print -u2 -- "Driver installed. Earlier package cleanup needs a retry; rerun installation later."
fi
print -- "Installed. In any app, choose Print and select HP LaserJet 1020 Plus."
