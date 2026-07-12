#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT_DIR/analysis/open-firmware-probes/usb-bulk-parser-draft"
BUILD="$ROOT_DIR/scripts/build-open-firmware-usb-bulk-parser-draft.sh"
TMP_DIR="$(mktemp -d /tmp/hp1020-usb-bulk-repro.XXXXXX)"
trap 'rm -rf "$TMP_DIR"' EXIT

clean_generated() {
  mkdir -p "$OUT_DIR"
  find "$OUT_DIR" -mindepth 1 -maxdepth 1 -type f \
    ! -name hardware-test-plan.md \
    -delete
}

clean_generated
"$BUILD" >/dev/null
mkdir -p "$TMP_DIR/first"
find "$OUT_DIR" -mindepth 1 -maxdepth 1 -type f \
  ! -name hardware-test-plan.md \
  ! -name reproducibility-check.md \
  ! -name reproducibility-check.json \
  -exec cp {} "$TMP_DIR/first/" \;

clean_generated
"$BUILD" >/dev/null

python3 - "$TMP_DIR/first" "$OUT_DIR" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

first = Path(sys.argv[1])
second = Path(sys.argv[2])
excluded = {"hardware-test-plan.md", "reproducibility-check.md", "reproducibility-check.json"}

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

first_files = {path.name: path for path in first.iterdir() if path.is_file()}
second_files = {
    path.name: path for path in second.iterdir() if path.is_file() and path.name not in excluded
}
names = sorted(set(first_files) | set(second_files))
items = []
for name in names:
    left = first_files.get(name)
    right = second_files.get(name)
    left_hash = digest(left) if left else None
    right_hash = digest(right) if right else None
    items.append(
        {
            "file": name,
            "first_sha256": left_hash,
            "second_sha256": right_hash,
            "status": "pass" if left_hash is not None and left_hash == right_hash else "fail",
        }
    )

required = {
    "hp1020-usb-bulk-parser-draft.elf",
    "hp1020-usb-bulk-parser-draft.img",
    "hp1020-usb-bulk-parser-draft.dl",
    "hp1020-usb-bulk-parser-draft.map",
    "disassembly.txt",
}
missing = sorted(required - set(second_files))
status = "pass" if items and not missing and all(item["status"] == "pass" for item in items) else "fail"
payload = {
    "status": status,
    "clean_generated_output_between_builds": True,
    "compared_files": len(items),
    "required_missing": missing,
    "files": items,
}
(second / "reproducibility-check.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

lines = [
    "# HP 1020 USB Bulk Parser Reproducibility Check",
    "",
    f"- status: `{status}`",
    "- generated output removed before each build: `yes`",
    f"- byte-identical files: `{sum(item['status'] == 'pass' for item in items)}/{len(items)}`",
    f"- missing required artifacts: `{len(missing)}`",
    "",
    "| File | First SHA-256 | Second SHA-256 | Status |",
    "|---|---|---|---|",
]
for item in items:
    lines.append(
        f"| `{item['file']}` | `{item['first_sha256'] or 'missing'}` | `{item['second_sha256'] or 'missing'}` | `{item['status']}` |"
    )
lines.append("")
(second / "reproducibility-check.md").write_text("\n".join(lines))
if status != "pass":
    raise SystemExit("bulk parser probe rebuild was not byte-for-byte reproducible")
PY

printf '%s\n' "$OUT_DIR/reproducibility-check.md"
