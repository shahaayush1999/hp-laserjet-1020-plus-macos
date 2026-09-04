#!/usr/bin/env bash
# Aggregate offline checks only. Never forward arguments to hardware harnesses.
set -euo pipefail

if [[ $# -eq 1 && "$1" == "--help" ]]; then
  echo 'Usage: scripts/validate.sh'
  echo 'Run offline analysis, probe audits, reproducibility and dry-run checks.'
  echo 'Requires existing research tools; does not install tools or contact USB.'
  exit 0
fi
if [[ $# -ne 0 ]]; then
  echo 'Unexpected arguments. Use --help; this command has no hardware mode.' >&2
  exit 2
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VALIDATION_LOG_DIR="$(mktemp -d "${TMPDIR:-/tmp}/hp1020-validation.XXXXXX")"
echo "Offline validation logs: $VALIDATION_LOG_DIR"
for suite in validate-hp1020-offline-analysis validate-open-firmware-probes; do
  echo "Running $suite..."
  if "$ROOT_DIR/scripts/$suite.sh" > "$VALIDATION_LOG_DIR/$suite.log" 2>&1; then
    echo "PASS: $suite"
  else
    echo "FAIL: $suite. Last output:" >&2
    tail -n 60 "$VALIDATION_LOG_DIR/$suite.log" >&2
    exit 1
  fi
done
echo 'All offline checks passed. No printer was contacted.'
