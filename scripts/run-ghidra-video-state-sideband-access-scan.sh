#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GHIDRA_HOME="${GHIDRA_HOME:-/opt/homebrew/Cellar/ghidra/12.1.1/libexec}"
JAVA_HOME="${JAVA_HOME:-/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home}"
export JAVA_HOME

"$GHIDRA_HOME/support/analyzeHeadless" \
  /tmp hp1020-ghidra-video-state-sideband-access-scan \
  -import "$ROOT_DIR/analysis/sihp1020.elf" \
  -processor Xtensa:BE:32:default \
  -cspec default \
  -scriptPath "$ROOT_DIR/analysis/ghidra-scripts" \
  -postScript ProbeHp1020VideoStateSidebandAccessScan.java "$ROOT_DIR/analysis/ghidra-probes" \
  -deleteProject
