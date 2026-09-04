#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

run_step() {
  local label="$1"
  shift
  echo "==> $label"
  "$@"
}

run_step "Python syntax checks" \
  python3 -m py_compile \
    "$ROOT_DIR/scripts/model-hp1020-print-path.py" \
    "$ROOT_DIR/scripts/generate-zjs-model-matrix.py" \
    "$ROOT_DIR/scripts/normalize-zjs-sample-metadata.py" \
    "$ROOT_DIR/scripts/check-hp1020-print-model-invariants.py" \
    "$ROOT_DIR/scripts/project-hp1020-video-registers.py" \
    "$ROOT_DIR/scripts/model-hp1020-hardware-boundary.py" \
    "$ROOT_DIR/scripts/model-hp1020-video-engine-register-semantics.py" \
    "$ROOT_DIR/scripts/model-hp1020-video-prepare-modes.py" \
    "$ROOT_DIR/scripts/model-hp1020-engine-command-status.py" \
    "$ROOT_DIR/scripts/model-hp1020-engine-status-decisions.py" \
    "$ROOT_DIR/scripts/model-hp1020-engine-print-topology.py" \
    "$ROOT_DIR/scripts/model-hp1020-video-engine-feedback.py" \
    "$ROOT_DIR/scripts/model-hp1020-video-transfer-ring.py" \
    "$ROOT_DIR/scripts/model-hp1020-video-irq-decisions.py" \
    "$ROOT_DIR/scripts/model-hp1020-video-band-queue.py" \
    "$ROOT_DIR/scripts/model-hp1020-video-mode-flag.py" \
    "$ROOT_DIR/scripts/model-hp1020-video-refill-topology.py" \
    "$ROOT_DIR/scripts/model-hp1020-video-prepare-projection.py" \
    "$ROOT_DIR/scripts/model-hp1020-first-page-hardware-sequence.py" \
    "$ROOT_DIR/scripts/model-hp1020-raster-field-semantics.py" \
    "$ROOT_DIR/scripts/model-hp1020-video-dataflow-contract.py" \
    "$ROOT_DIR/scripts/model-hp1020-video-chunk-sizing.py" \
    "$ROOT_DIR/scripts/model-hp1020-video-helper-disassembly.py" \
    "$ROOT_DIR/scripts/model-hp1020-video-queue-payload-chain.py" \
    "$ROOT_DIR/scripts/model-hp1020-video-prepare-argument-fields.py" \
    "$ROOT_DIR/scripts/model-hp1020-video-sideband-write-census.py" \
    "$ROOT_DIR/scripts/model-hp1020-video-sideband-copy-direction.py" \
    "$ROOT_DIR/scripts/model-hp1020-video-sideband-default-impact.py" \
    "$ROOT_DIR/scripts/model-hp1020-video-zero-sideband-scenario.py" \
    "$ROOT_DIR/scripts/model-hp1020-video-remaining-units.py" \
    "$ROOT_DIR/scripts/model-hp1020-minimal-print-scope.py" \
    "$ROOT_DIR/scripts/model-hp1020-open-endpoint0.py" \
    "$ROOT_DIR/scripts/model-hp1020-usb-setup-source.py" \
    "$ROOT_DIR/scripts/model-hp1020-control-in-data-stage.py" \
    "$ROOT_DIR/scripts/model-hp1020-control-completion.py" \
    "$ROOT_DIR/scripts/model-hp1020-usb-interrupt-events.py" \
    "$ROOT_DIR/scripts/model-hp1020-usb-bulk-receive.py" \
    "$ROOT_DIR/scripts/model-hp1020-usb-bulk-callbacks.py" \
    "$ROOT_DIR/scripts/model-hp1020-usb-bulk-rearm.py" \
    "$ROOT_DIR/scripts/model-hp1020-usb-parser-shim-contract.py" \
    "$ROOT_DIR/scripts/model-hp1020-usb-bulk-probe-contract.py" \
    "$ROOT_DIR/scripts/model-hp1020-usb-bulk-parser-draft.py" \
    "$ROOT_DIR/scripts/check-hp1020-usb-bulk-parser-source.py" \
    "$ROOT_DIR/scripts/check-hp1020-usb-bulk-status-descriptor.py" \
    "$ROOT_DIR/scripts/check-hp1020-usb-bulk-config-descriptors.py" \
    "$ROOT_DIR/scripts/model-hp1020-status-code-correlation.py" \
    "$ROOT_DIR/scripts/model-hp1020-pjl-status-contract.py" \
    "$ROOT_DIR/scripts/analyze-hp1020-pjl-status-capture.py" \
    "$ROOT_DIR/scripts/check-hp1020-analysis-consistency.py"

run_step "Generate base ZjStream sample" \
  "$ROOT_DIR/scripts/generate-zjs-sample.sh"

run_step "Regenerate base print-path model" \
  "$ROOT_DIR/scripts/model-hp1020-print-path.py" \
    "$ROOT_DIR/analysis/samples/generated/minimal-page-a4.zjs" \
    -o "$ROOT_DIR/analysis/open-firmware-model"

run_step "Generate ZjStream model matrix" \
  "$ROOT_DIR/scripts/generate-zjs-model-matrix.py"

mapfile -t model_paths < <(
  {
    printf '%s\n' "$ROOT_DIR/analysis/open-firmware-model/print-path-model.json"
    find "$ROOT_DIR/analysis/open-firmware-model/variants" -name print-path-model.json -print
  } | sort
)

run_step "Verify direct START_PAGE work construction against stock ELF" \
  "$ROOT_DIR/scripts/model-hp1020-zjs-direct-work.py"

run_step "Verify stock metadata allocation bounds" \
  "$ROOT_DIR/scripts/model-hp1020-metadata-bounds.py"

run_step "Validate portable semantic core under sanitizers" \
  python3 "$ROOT_DIR/scripts/validate-hp1020-semantic-core.py"

run_step "Validate portable page and band planner" \
  "$ROOT_DIR/scripts/validate-hp1020-page-plan.py"

run_step "Build and reproduce semantic core for synthetic Xtensa RAM" \
  "$ROOT_DIR/scripts/check-hp1020-semantic-target-reproducibility.sh"

run_step "Execute compiled semantic core and planner" \
  "$ROOT_DIR/scripts/validate-hp1020-semantic-target.py"

run_step "Print model invariant check" \
  "$ROOT_DIR/scripts/check-hp1020-print-model-invariants.py" \
    "${model_paths[@]}" \
    -o "$ROOT_DIR/analysis/open-firmware-model/model-invariants.md" \
    --json "$ROOT_DIR/analysis/open-firmware-model/model-invariants.json"

run_step "Project video register boundary" \
  "$ROOT_DIR/scripts/project-hp1020-video-registers.py"

run_step "Regenerate hardware boundary model" \
  "$ROOT_DIR/scripts/model-hp1020-hardware-boundary.py"

run_step "Regenerate video/engine register semantics" \
  "$ROOT_DIR/scripts/model-hp1020-video-engine-register-semantics.py"

run_step "Regenerate video prepare mode model" \
  "$ROOT_DIR/scripts/model-hp1020-video-prepare-modes.py"

run_step "Regenerate engine command/status model" \
  "$ROOT_DIR/scripts/model-hp1020-engine-command-status.py"

run_step "Regenerate engine status decision model" \
  "$ROOT_DIR/scripts/model-hp1020-engine-status-decisions.py"

run_step "Regenerate engine print topology model" \
  "$ROOT_DIR/scripts/model-hp1020-engine-print-topology.py"

run_step "Regenerate video-to-engine feedback model" \
  "$ROOT_DIR/scripts/model-hp1020-video-engine-feedback.py"

run_step "Regenerate video transfer ring model" \
  "$ROOT_DIR/scripts/model-hp1020-video-transfer-ring.py"

run_step "Regenerate video IRQ decision model" \
  "$ROOT_DIR/scripts/model-hp1020-video-irq-decisions.py"

run_step "Audit stock raster callback arguments and custom instructions" \
  "$ROOT_DIR/scripts/model-hp1020-raster-callbacks.py"

run_step "Regenerate video band queue/list model" \
  "$ROOT_DIR/scripts/model-hp1020-video-band-queue.py"

run_step "Regenerate video mode flag model" \
  "$ROOT_DIR/scripts/model-hp1020-video-mode-flag.py"

run_step "Regenerate video refill topology model" \
  "$ROOT_DIR/scripts/model-hp1020-video-refill-topology.py"

run_step "Regenerate video prepare projection model" \
  "$ROOT_DIR/scripts/model-hp1020-video-prepare-projection.py"

run_step "Regenerate first-page hardware sequence" \
  "$ROOT_DIR/scripts/model-hp1020-first-page-hardware-sequence.py"

run_step "Regenerate raster field semantics model" \
  "$ROOT_DIR/scripts/model-hp1020-raster-field-semantics.py"

run_step "Regenerate video chunk sizing model" \
  "$ROOT_DIR/scripts/model-hp1020-video-chunk-sizing.py"

run_step "Regenerate video helper disassembly limit model" \
  "$ROOT_DIR/scripts/model-hp1020-video-helper-disassembly.py"

run_step "Regenerate video queue payload chain model" \
  "$ROOT_DIR/scripts/model-hp1020-video-queue-payload-chain.py"

run_step "Regenerate video prepare argument field model" \
  "$ROOT_DIR/scripts/model-hp1020-video-prepare-argument-fields.py"

run_step "Regenerate video sideband write census" \
  "$ROOT_DIR/scripts/model-hp1020-video-sideband-write-census.py"

run_step "Regenerate video sideband copy-direction model" \
  "$ROOT_DIR/scripts/model-hp1020-video-sideband-copy-direction.py"

run_step "Regenerate video sideband default-impact model" \
  "$ROOT_DIR/scripts/model-hp1020-video-sideband-default-impact.py"

run_step "Regenerate video remaining-units model" \
  "$ROOT_DIR/scripts/model-hp1020-video-remaining-units.py"

run_step "Regenerate video dataflow contract" \
  "$ROOT_DIR/scripts/model-hp1020-video-dataflow-contract.py"

run_step "Regenerate video zero-sideband scenario model" \
  "$ROOT_DIR/scripts/model-hp1020-video-zero-sideband-scenario.py"

run_step "Regenerate open endpoint-0 model" \
  "$ROOT_DIR/scripts/model-hp1020-open-endpoint0.py"

run_step "Regenerate USB setup-source model" \
  "$ROOT_DIR/scripts/model-hp1020-usb-setup-source.py"

run_step "Regenerate USB control-IN data-stage model" \
  "$ROOT_DIR/scripts/model-hp1020-control-in-data-stage.py"

run_step "Self-test USB control-IN data-stage model" \
  "$ROOT_DIR/scripts/model-hp1020-control-in-data-stage.py" --self-test

run_step "Regenerate USB control completion event model" \
  "$ROOT_DIR/scripts/model-hp1020-control-completion.py"

run_step "Regenerate USB interrupt event model" \
  "$ROOT_DIR/scripts/model-hp1020-usb-interrupt-events.py"

run_step "Regenerate USB bulk receive model" \
  "$ROOT_DIR/scripts/model-hp1020-usb-bulk-receive.py"

run_step "Regenerate USB bulk callback model" \
  "$ROOT_DIR/scripts/model-hp1020-usb-bulk-callbacks.py"

run_step "Regenerate USB bulk re-arm model" \
  "$ROOT_DIR/scripts/model-hp1020-usb-bulk-rearm.py"

run_step "Regenerate USB parser shim contract" \
  "$ROOT_DIR/scripts/model-hp1020-usb-parser-shim-contract.py"

run_step "Regenerate USB bulk probe contract" \
  "$ROOT_DIR/scripts/model-hp1020-usb-bulk-probe-contract.py"

run_step "Regenerate USB bulk/parser host model" \
  "$ROOT_DIR/scripts/model-hp1020-usb-bulk-parser-draft.py"

run_step "Regenerate minimal print-only replacement scope" \
  "$ROOT_DIR/scripts/model-hp1020-minimal-print-scope.py"

run_step "Regenerate status CODE correlation model" \
  "$ROOT_DIR/scripts/model-hp1020-status-code-correlation.py"

run_step "Regenerate PJL/status query contract" \
  "$ROOT_DIR/scripts/model-hp1020-pjl-status-contract.py"

run_step "Self-test PJL/status capture analyzer" \
  "$ROOT_DIR/scripts/analyze-hp1020-pjl-status-capture.py" --self-test

run_step "Cross-check offline analysis consistency" \
  "$ROOT_DIR/scripts/check-hp1020-analysis-consistency.py"

run_step "JSON fail-count audit" \
  python3 - "$ROOT_DIR" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
reports = [
    "analysis/open-firmware-model/model-invariants.json",
    "analysis/hardware-boundary/safety-scanner-known-unsafe-report.json",
]

for rel in reports:
    path = root / rel
    items = json.loads(path.read_text())
    if "known-unsafe" in rel:
        fail = sum(item.get("severity") == "fail" for item in items)
        print(f"{rel}: known unsafe scanner exercise fail hits={fail}")
        if fail == 0:
            raise SystemExit(1)
        continue
    fail = sum(item.get("severity") == "fail" for item in items)
    print(f"{rel}: items={len(items)} fail={fail}")
    if fail:
        raise SystemExit(1)
PY

echo "Offline analysis validation completed."
