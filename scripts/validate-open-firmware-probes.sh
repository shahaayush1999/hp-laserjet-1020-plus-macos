#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Validating HP 1020 open firmware probes"
echo "Repository: $ROOT_DIR"
echo

run_step() {
  local name="$1"
  shift
  echo "==> $name"
  "$@"
  echo
}

run_step "Xtensa binutils smoke test" "$ROOT_DIR/scripts/probe-xtensa-binutils.sh"
run_step "Build minimal idle probe" "$ROOT_DIR/scripts/build-open-firmware-idle-probe.sh"
run_step "Build USB register snapshot probe" "$ROOT_DIR/scripts/build-open-firmware-usb-snapshot-probe.sh"
run_step "Build USB marker draft" "$ROOT_DIR/scripts/build-open-firmware-usb-marker-draft.sh"

run_step "Idle probe layout" \
  python3 "$ROOT_DIR/scripts/inspect-firmware-layout.py" \
    --profile boot-probe \
    "$ROOT_DIR/analysis/open-firmware-probes/minimal-idle/hp1020-idle-probe.dl"

run_step "USB snapshot layout" \
  python3 "$ROOT_DIR/scripts/inspect-firmware-layout.py" \
    --profile boot-probe \
    "$ROOT_DIR/analysis/open-firmware-probes/usb-register-snapshot/hp1020-usb-snapshot-probe.dl"

run_step "USB marker draft layout" \
  python3 "$ROOT_DIR/scripts/inspect-firmware-layout.py" \
    --profile boot-probe \
    "$ROOT_DIR/analysis/open-firmware-probes/usb-marker-draft/hp1020-usb-marker-draft.dl"

run_step "USB marker behavior model" \
  python3 "$ROOT_DIR/scripts/model-hp1020-usb-marker-draft.py"

run_step "USB marker length-flow check" \
  python3 "$ROOT_DIR/scripts/check-hp1020-marker-length-flow.py" \
    "$ROOT_DIR/open-firmware/usb-marker-draft/usb-marker.S"

run_step "JSON scanner fail-count audit" \
  python3 - "$ROOT_DIR" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
reports = [
    "analysis/open-firmware-probes/minimal-idle/safety-scan.json",
    "analysis/open-firmware-probes/minimal-idle/usb-contract-scan.json",
    "analysis/open-firmware-probes/usb-register-snapshot/safety-scan.json",
    "analysis/open-firmware-probes/usb-register-snapshot/usb-contract-scan.json",
    "analysis/open-firmware-probes/usb-register-snapshot/usb-mmio-access-scan.json",
    "analysis/open-firmware-probes/usb-marker-draft/safety-scan.json",
    "analysis/open-firmware-probes/usb-marker-draft/usb-contract-scan.json",
    "analysis/open-firmware-probes/usb-marker-draft/usb-mmio-access-scan.json",
    "analysis/open-firmware-probes/usb-marker-draft/endpoint0-sequence-scan.json",
    "analysis/open-firmware-probes/usb-marker-draft/memory-boundary-scan.json",
    "analysis/open-firmware-probes/usb-marker-draft/marker-descriptor-check.json",
    "analysis/open-firmware-probes/usb-marker-draft/marker-length-flow-check.json",
]

for rel in reports:
    path = root / rel
    items = json.loads(path.read_text())
    if isinstance(items, dict) and "checks" in items:
        check_items = items["checks"]
    else:
        check_items = items
    fail = sum(item.get("severity") == "fail" for item in check_items)
    print(f"{rel}: items={len(check_items)} fail={fail}")
    if fail:
        raise SystemExit(1)
PY

tmp_dir="$(mktemp -d /tmp/hp1020-probe-validation.XXXXXX)"
trap 'rm -rf "$tmp_dir"' EXIT

run_step "Idle hardware harness dry-run" \
  "$ROOT_DIR/scripts/run-idle-probe-hardware-test.sh" --dry-run

run_step "USB snapshot hardware harness dry-run" \
  "$ROOT_DIR/scripts/run-usb-snapshot-probe-hardware-test.sh" --dry-run

run_step "USB marker hardware harness dry-run" \
  "$ROOT_DIR/scripts/run-usb-marker-draft-hardware-test.sh" --dry-run

run_step "USB identity capture dry-run/baseline" \
  "$ROOT_DIR/scripts/capture-hp1020-usb-identity.sh" --output-dir "$tmp_dir/usb-identity"

echo "All open firmware probe validations completed."
