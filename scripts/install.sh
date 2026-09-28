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

install_dependencies
print -- "Building the printer helper for this Mac..."
zsh "$ROOT/scripts/rebuild-runtime-from-vendor.sh" "$render_dir/runtime"

escape_sed() { printf '%s' "$1" | sed 's/[&|\\]/\\&/g'; }
device_shell="$(escape_sed "${(qq)DEVICE_URI}")"
brew_shell="$(escape_sed "${(qq)BREW_PREFIX}")"
python_shell="$(escape_sed "${(qq)PYTHON}")"
printer_shell="$(escape_sed "${(qq)PRINTER_NAME}")"
sed -e "s|@@PRINTER_NAME_SHELL@@|$printer_shell|g" \
  "$ROOT/templates/hp1020-print.in" > "$render_dir/hp1020-print"
sed -e "s|@@DEVICE_URI_SHELL@@|$device_shell|g" \
  -e "s|@@BREW_PREFIX_SHELL@@|$brew_shell|g" \
  -e "s|@@PYTHON_SHELL@@|$python_shell|g" \
  "$ROOT/templates/hp1020-root-spool-worker.in" > "$render_dir/hp1020-root-spool-worker"
sed -e "s|@@LABEL@@|$LABEL|g" \
  "$ROOT/templates/com.aayush.hp1020-root-spool-worker.plist.in" > "$render_dir/$LABEL.plist"
zsh -n "$render_dir/hp1020-print"
zsh -n "$render_dir/hp1020-root-spool-worker"
plutil -lint "$render_dir/$LABEL.plist" > /dev/null
cupstestppd -q "$ROOT/files/ppd/HP-LaserJet_1020-Plus-hp1020zjs.ppd"

# macOS privacy permissions for this user do not transfer to the elevated
# AppleScript helper. Stage every repository input before asking it to install.
cp "$ROOT/files/cups/backend/hp1020queue" "$render_dir/hp1020queue"
cp "$ROOT/files/cups/filter/hp1020passthrough" "$render_dir/hp1020passthrough"
cp "$ROOT/files/ppd/HP-LaserJet_1020-Plus-hp1020zjs.ppd" "$render_dir/printer.ppd"
cp "$ROOT/files/macos/hp1020-service.py" "$render_dir/hp1020-service.py"
cp "$ROOT/assets/licenses/foo2zjs-COPYING" "$render_dir/foo2zjs-COPYING"

admin_script="$render_dir/install-admin"
admin_variables > "$admin_script"
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
restore_acceptance() {
  (( ! queue_accepted )) || cupsaccept "$PRINTER_NAME" 2>/dev/null || true
}
backup=""
# Also restore acceptance if a preflight or backup operation fails.
before_replacement() {
  restore_acceptance
  [[ -z "$backup" ]] || rm -rf -- "$backup"
}
trap before_replacement EXIT
if (( queue_existed )); then cupsreject "$PRINTER_NAME"; fi
if [[ -n "$(lpstat -W not-completed -o "$PRINTER_NAME" 2>/dev/null || true)" ]]; then
  print -u2 -- "A print job arrived during setup. Finish or cancel it, then rerun installation."
  exit 1
fi
legacy_jobs=(/private/var/spool/cups/tmp/hp1020queue/*(N))
if (( ${#legacy_jobs} )); then
  print -u2 -- "The printer worker still has queued work. Finish it before updating."
  exit 1
fi

# Preserve every replaced component until the new service and queue are ready.
# A failed update restores the old runtime instead of leaving half an install.
backup="$(mktemp -d -t hp1020-rollback.XXXXXXXX)"
managed=("$BASE/runtime" "$BASE/Licenses" "$BASE/hp1020-print" "$BASE/hp1020-root-spool-worker"
         "$BASE/hp1020-service.py" "$PPD" /usr/libexec/cups/backend/hp1020queue
         /usr/libexec/cups/filter/hp1020passthrough "$PLIST" "$BASE/spool-worker.lock" "$QUEUE_PPD")
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
    [[ ! -f "$QUEUE_PPD" ]] || lpadmin -p "$PRINTER_NAME" -P "$QUEUE_PPD" 2>/dev/null || true
    restore_acceptance
    [[ ! -f "$PLIST" ]] || launchctl bootstrap system "$PLIST" 2>/dev/null || true
  else
    lpadmin -x "$PRINTER_NAME" 2>/dev/null || true
  fi
  if (( restore_failed )); then
    print -u2 -- "Restoring printer files failed. The backup is preserved at $backup."
  else
    rm -rf -- "$backup"
    print -u2 -- "Installation failed; the previous printer files were restored."
  fi
}
trap rollback EXIT
# Keep rollback in the parent: zsh fatal expansion errors can bypass an EXIT
# trap in the shell that encounters them. The parent still sees a failed child.
(
trap - EXIT
launchctl bootout system "$PLIST" 2>/dev/null || true
rm -rf "$BASE/runtime" "$BASE/Licenses"
mkdir -p "$BASE/runtime" "$BASE/Licenses" "$BASE/state"
chown _lp:_lp "$BASE/state"
chmod 700 "$BASE/state"
# Retire the old empty-directory lock. The new service holds an OS file lock.
rmdir "$BASE/spool-worker.lock" 2>/dev/null || true
mkdir -p /private/var/spool/cups/tmp/hp1020queue
chown root:_lp /private/var/spool/cups/tmp/hp1020queue
chmod 2770 /private/var/spool/cups/tmp/hp1020queue

for name in foo2zjs foo2zjs-wrapper foo2zjs-pstops hp1020-usb-run; do
  install -m 755 -o root -g wheel "$render_dir/runtime/$name" "$BASE/runtime/$name"
done
install -m 644 -o root -g wheel "$render_dir/runtime/sihp1020.dl" "$BASE/runtime/sihp1020.dl"
install -m 644 -o root -g wheel "$render_dir/foo2zjs-COPYING" "$BASE/Licenses/foo2zjs-COPYING"
install -m 755 -o root -g wheel "$render_dir/hp1020queue" /usr/libexec/cups/backend/hp1020queue
install -m 755 -o root -g wheel "$render_dir/hp1020passthrough" /usr/libexec/cups/filter/hp1020passthrough
install -m 644 -o root -g wheel "$render_dir/printer.ppd" "$PPD"
install -m 755 -o root -g wheel "$render_dir/hp1020-print" "$BASE/hp1020-print"
install -m 755 -o root -g wheel "$render_dir/hp1020-root-spool-worker" "$BASE/hp1020-root-spool-worker"
install -m 644 -o root -g wheel "$render_dir/hp1020-service.py" "$BASE/hp1020-service.py"
install -m 644 -o root -g wheel "$render_dir/$LABEL.plist" "$PLIST"

lpadmin -p "$PRINTER_NAME" -v hp1020queue://localhost -P "$PPD" -L USB -D "HP LaserJet 1020 Plus"
lpadmin -p "$PRINTER_NAME" -o printer-error-policy=stop-printer -o printer-is-shared=false
lpadmin -p "$PRINTER_NAME" -o multiple-document-handling-default=separate-documents-collated-copies
rm -f "$BASE/state/ready"
launchctl bootstrap system "$PLIST"
launchctl enable "system/$LABEL"
launchctl kickstart -k "system/$LABEL"
ready=0
for attempt in {1..15}; do
  sleep 1
  if [[ -f "$BASE/state/ready" ]]; then
    IFS=' ' read -r signature service_pid < "$BASE/state/ready"
    if [[ "$signature" == HP1020-SERVICE-2 && "$service_pid" == <1-> ]] && kill -0 "$service_pid" 2>/dev/null; then
      ready=1
      break
    fi
  fi
done
if (( ! ready )); then
  print -u2 -- "The new printer service could not start. Restoring the previous setup."
  exit 1
fi
cupsaccept "$PRINTER_NAME"
cupsenable "$PRINTER_NAME"
)
trap - EXIT
rm -rf -- "$backup"

# Retire the earlier per-user runtime only after the replacement is installed.
launchctl bootout "gui/$(id -u "$USER_NAME")/com.aayush.hp1020-spool-worker" 2>/dev/null || true
rm -f "$USER_HOME/Library/LaunchAgents/com.aayush.hp1020-spool-worker.plist"
rm -f "$USER_HOME/bin/hp1020-print"
rm -rf "$USER_HOME/.local/share/hp1020"
ADMIN
chmod 700 "$admin_script"
zsh -n "$admin_script"
run_admin "$admin_script"
print -- "Installed. In any app, choose Print and select HP LaserJet 1020 Plus."
