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

detect_device_uri() {
  lpinfo -v 2>/dev/null | awk '$1 == "direct" && $2 ~ /^usb:\/\/Hewlett-Packard\/HP%20LaserJet%201020/ { print $2; exit }'
}

DEVICE_URI="${HP1020_DEVICE_URI:-$(detect_device_uri)}"
if [[ -z "$DEVICE_URI" ]]; then
  DEVICE_URI="usb://Hewlett-Packard/HP%20LaserJet%201020?serial=S43VYTP"
  print "HP LaserJet 1020 was not visible over USB; using fallback URI: $DEVICE_URI" >&2
fi

missing=()
for file in \
  "$ROOT/assets/runtime/foo2zjs" \
  "$ROOT/assets/runtime/foo2zjs-wrapper" \
  "$ROOT/assets/runtime/foo2zjs-pstops" \
  "$ROOT/assets/runtime/sihp1020.dl" \
  "$ROOT/files/cups/backend/hp1020queue" \
  "$ROOT/files/cups/filter/hp1020passthrough" \
  "$ROOT/files/ppd/HP-LaserJet_1020-Plus-hp1020zjs.ppd" \
  "$ROOT/templates/hp1020-print.in" \
  "$ROOT/templates/hp1020-root-spool-worker.in" \
  "$ROOT/templates/com.aayush.hp1020-root-spool-worker.plist.in"; do
  [[ -f "$file" ]] || missing+=("$file")
done

if (( ${#missing[@]} > 0 )); then
  print "Missing required repo files:" >&2
  printf '  %s\n' "${missing[@]}" >&2
  exit 1
fi

if ! command -v gs >/dev/null 2>&1 || ! command -v gsed >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1 && [[ "${HP1020_SKIP_BREW:-0}" != "1" ]]; then
    print "Installing missing runtime dependencies with Homebrew..."
    brew install ghostscript gnu-sed
  else
    print "Missing runtime dependencies." >&2
    print "Install them with: brew install ghostscript gnu-sed" >&2
    exit 1
  fi
fi

if ! command -v gs >/dev/null 2>&1 || ! command -v gsed >/dev/null 2>&1; then
  print "Runtime dependency install did not make gs and gsed available on PATH." >&2
  exit 1
fi

BREW_PREFIX="$(brew --prefix 2>/dev/null || printf '/opt/homebrew')"

escape_sed_replacement() {
  printf '%s' "$1" | sed 's/[&|\\]/\\&/g'
}

render_dir="$(mktemp -d -t hp1020-render.XXXXXX)"
trap 'rm -rf "$render_dir"' EXIT

user_home_sed="$(escape_sed_replacement "$USER_HOME")"
user_name_sed="$(escape_sed_replacement "$USER_NAME")"
device_uri_sed="$(escape_sed_replacement "$DEVICE_URI")"
label_sed="$(escape_sed_replacement "$LABEL")"
brew_prefix_sed="$(escape_sed_replacement "$BREW_PREFIX")"

sed \
  -e "s|@@USER_HOME@@|$user_home_sed|g" \
  -e "s|@@USER_NAME@@|$user_name_sed|g" \
  -e "s|@@DEVICE_URI@@|$device_uri_sed|g" \
  -e "s|@@BREW_PREFIX@@|$brew_prefix_sed|g" \
  "$ROOT/templates/hp1020-print.in" > "$render_dir/hp1020-print"

sed \
  -e "s|@@USER_HOME@@|$user_home_sed|g" \
  "$ROOT/templates/hp1020-root-spool-worker.in" > "$render_dir/hp1020-root-spool-worker"

sed \
  -e "s|@@LABEL@@|$label_sed|g" \
  "$ROOT/templates/com.aayush.hp1020-root-spool-worker.plist.in" > "$render_dir/$LABEL.plist"

chmod 755 "$render_dir/hp1020-print" "$render_dir/hp1020-root-spool-worker"
chmod 644 "$render_dir/$LABEL.plist"

runtime_dir="$USER_HOME/.local/share/hp1020"
bin_dir="$USER_HOME/bin"
mkdir -p "$runtime_dir" "$bin_dir"
install -m 755 "$ROOT/assets/runtime/foo2zjs" "$runtime_dir/foo2zjs"
install -m 755 "$ROOT/assets/runtime/foo2zjs-wrapper" "$runtime_dir/foo2zjs-wrapper"
install -m 755 "$ROOT/assets/runtime/foo2zjs-pstops" "$runtime_dir/foo2zjs-pstops"
install -m 644 "$ROOT/assets/runtime/sihp1020.dl" "$runtime_dir/sihp1020.dl"
install -m 755 "$render_dir/hp1020-print" "$bin_dir/hp1020-print"

if [[ "$(id -u)" -eq 0 ]]; then
  chown -R "$USER_NAME":staff "$runtime_dir" "$bin_dir/hp1020-print" 2>/dev/null || true
fi

admin_script="$(mktemp -t hp1020-install-admin.XXXXXX.sh)"
cat > "$admin_script" <<EOF
#!/bin/sh
set -eu
ROOT="$ROOT"
RENDER_DIR="$render_dir"
PRINTER_NAME="$PRINTER_NAME"
LABEL="$LABEL"
PLIST="/Library/LaunchDaemons/$LABEL.plist"
PPD="/Library/Printers/hp1020/HP-LaserJet_1020-Plus-hp1020zjs.ppd"

mkdir -p /Library/Printers/hp1020 /private/var/spool/cups/tmp/hp1020queue
mkdir -p /Library/Printers/hp1020/done /Library/Printers/hp1020/failed
chown root:_lp /private/var/spool/cups/tmp/hp1020queue
chmod 2770 /private/var/spool/cups/tmp/hp1020queue

install -m 755 -o root -g wheel "\$ROOT/files/cups/backend/hp1020queue" /usr/libexec/cups/backend/hp1020queue
install -m 755 -o root -g wheel "\$ROOT/files/cups/filter/hp1020passthrough" /usr/libexec/cups/filter/hp1020passthrough
install -m 644 -o root -g wheel "\$ROOT/files/ppd/HP-LaserJet_1020-Plus-hp1020zjs.ppd" "\$PPD"
install -m 755 -o root -g wheel "\$RENDER_DIR/hp1020-root-spool-worker" /Library/Printers/hp1020/hp1020-root-spool-worker
install -m 644 -o root -g wheel "\$RENDER_DIR/$LABEL.plist" "\$PLIST"

launchctl bootout system "\$PLIST" 2>/dev/null || true
launchctl bootstrap system "\$PLIST"
launchctl enable "system/\$LABEL" 2>/dev/null || true
launchctl kickstart -k "system/\$LABEL" 2>/dev/null || true

lpadmin -x "\$PRINTER_NAME" 2>/dev/null || true
lpadmin -p "\$PRINTER_NAME" -E -v hp1020queue://localhost -P "\$PPD" -L USB -D "HP LaserJet 1020 Plus"
lpadmin -p "\$PRINTER_NAME" -o printer-error-policy=retry-job
cupsaccept "\$PRINTER_NAME" 2>/dev/null || true
cupsenable "\$PRINTER_NAME" 2>/dev/null || true
cupsctl --no-debug-logging 2>/dev/null || true
EOF
chmod 700 "$admin_script"

osascript \
  -e 'on run argv' \
  -e 'do shell script quoted form of item 1 of argv with administrator privileges' \
  -e 'end run' \
  "$admin_script"

rm -f "$admin_script"

print "Installed $PRINTER_NAME."
print "Device URI: $DEVICE_URI"
print "Try: $ROOT/scripts/print-test.sh"
