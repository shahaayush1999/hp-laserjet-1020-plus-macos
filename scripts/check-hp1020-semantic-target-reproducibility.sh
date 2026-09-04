#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT_DIR/analysis/open-firmware-model/semantic-target"
REPRO_TMP="$(mktemp -d /tmp/hp1020-semantic-repro.XXXXXX)"
trap 'rm -rf "$REPRO_TMP"' EXIT
"$ROOT_DIR/scripts/build-hp1020-semantic-target.sh"
cp "$OUT/target-check.elf" "$OUT/target-check.map" "$REPRO_TMP/"
"$ROOT_DIR/scripts/build-hp1020-semantic-target.sh"
python3 - "$REPRO_TMP" "$OUT" <<'PY'
import hashlib,json,sys
from pathlib import Path
first,out=map(Path,sys.argv[1:]);checks=[]
for name in ('target-check.elf','target-check.map'):
    a=hashlib.sha256((first/name).read_bytes()).hexdigest()
    b=hashlib.sha256((out/name).read_bytes()).hexdigest()
    checks.append(dict(file=name,first_sha256=a,second_sha256=b,status='pass' if a==b else 'fail'))
status='pass' if all(c['status']=='pass' for c in checks) else 'fail'
(out/'reproducibility.json').write_text(json.dumps(dict(status=status,files=checks),indent=2,sort_keys=True)+'\n')
(out/'reproducibility.md').write_text('# Compiled semantic target reproducibility\n\nStatus: '+status+'. Two successive builds produce byte-identical ELF and map files. No printer contact.\n')
print('semantic target reproducibility:',status)
raise SystemExit(status!='pass')
PY
