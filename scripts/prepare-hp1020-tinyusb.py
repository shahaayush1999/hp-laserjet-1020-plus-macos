#!/usr/bin/env python3
"""Materialize pinned TinyUSB, optionally applying a verified local patch offline."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / 'vendor/tinyusb-0.21.0'
PATCHES = ROOT / 'open-firmware/tinyusb-device/patches'
PIN = 'dae3f9a366bfcddbf9dcf1b48d7500286a849539'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(output, patched=False):
    provenance = json.loads((VENDOR / 'PROVENANCE.json').read_text())
    assert provenance['commit'] == PIN and not provenance['local_changes']
    assert len(provenance['upstream_files']) == 19
    output.mkdir(parents=True, exist_ok=True)
    assert not any(output.iterdir()), 'source destination must be empty'
    expected = {}
    for name, record in provenance['upstream_files'].items():
        assert not Path(name).is_absolute() and '..' not in Path(name).parts
        assert sha(VENDOR / name) == record['sha256'], name
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(VENDOR / name, target)
        expected[name] = record['sha256']
    patch_manifest = None
    if patched:
        patch_manifest = json.loads((PATCHES / 'manifest.json').read_text())
        assert patch_manifest['upstream_commit'] == PIN
        patch = PATCHES / 'protocol-compatibility.patch'
        assert sha(patch) == patch_manifest['patch_sha256']
        for name, record in patch_manifest['files'].items():
            assert expected[name] == record['original_sha256']
            expected[name] = record['result_sha256']
        result = subprocess.run(['patch', '--batch', '--fuzz=0', '-p1', '-d', str(output)],
                                input=patch.read_bytes(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert result.returncode == 0 and not result.stderr, (result.stdout, result.stderr)
    observed = {str(p.relative_to(output)): sha(p) for p in output.rglob('*') if p.is_file()}
    assert observed == expected, 'effective source set or bytes differ from the pinned manifest'
    report = dict(upstream_commit=PIN, patched=patched, effective_sha256=observed,
                  patch_manifest=patch_manifest)
    (output / 'effective-source.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--patched', action='store_true')
    args = parser.parse_args()
    result = prepare(args.output, args.patched)
    print(f"Verified {len(result['effective_sha256'])} effective source files; patched={args.patched}")
