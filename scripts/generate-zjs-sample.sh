#!/bin/zsh
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
sample_ps="$repo_root/analysis/samples/minimal-page.ps"
out_dir="$repo_root/analysis/samples/generated"
out_zjs="$out_dir/minimal-page-a4.zjs"
out_report="$out_dir/minimal-page-a4-zjs-report.md"

mkdir -p "$out_dir"

export PATH="$repo_root/assets/runtime:$PATH"

(
  cd "$repo_root"
  assets/runtime/foo2zjs-wrapper -P -z1 -L0 -p9 "analysis/samples/minimal-page.ps" > "analysis/samples/generated/minimal-page-a4.zjs"
  scripts/inspect-zjs-stream.py "analysis/samples/generated/minimal-page-a4.zjs" -o "analysis/samples/generated/minimal-page-a4-zjs-report.md"
)

print "Generated $out_zjs"
print "Wrote $out_report"
