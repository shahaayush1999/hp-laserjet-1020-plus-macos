#!/usr/bin/env python3
"""Bounded reply ownership through real TinyUSB and a synthetic DCD; offline only."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('bulk_in_base', ROOT/'scripts/validate-hp1020-tinyusb-printer.py')
base = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = base
spec.loader.exec_module(base)
core = base.core
CASES = ('bounded-payload-and-zlp', 'concurrent-out-and-setup', 'refused-before-bind',
         'failed-after-bind', 'reset-with-both-directions', 'result-survives-reset',
         'short-success', 'overrun', 'invalid-result', 'failure-and-reuse',
         'final-reply-after-input-finish', 'exhaustion-drain')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', action='store_true')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='hp1020-bulk-in-') as directory:
        temp = Path(directory)
        tested = base.sources(temp)
        tested[str(Path(__file__).relative_to(ROOT))] = core.sha(Path(__file__).read_bytes())
        core.command(['python3', ROOT/'scripts/prepare-hp1020-tinyusb.py', '--output', temp/'effective', '--patched'])
        base.compile_host(temp, temp/'effective', base.SRC/'bulk-in-check.c', base.SRC/'bulk-in-main.c')
        for index, name in enumerate(CASES):
            for fill in (0, 204):
                core.command([temp/'host', str(index), str(fill)])
            print('Bulk IN host: '+name, flush=True)
        target = None
        if args.target:
            os.environ['HP1020_TUSB_FIXTURE'] = str(base.SRC/'bulk-in-check.c')
            os.environ['HP1020_TUSB_TARGET_DIR'] = str(temp/'target')
            core.command(['bash', ROOT/'scripts/build-hp1020-tinyusb-printer-target.sh'])
            elf = temp/'target/target-check.elf'
            program, audit = core.audit_target(elf)
            from hp1020_qemu_ram import QemuRAM
            with QemuRAM() as q:
                for index, name in enumerate(CASES):
                    for fill in (0, 204):
                        q.load(elf)
                        failure = q.call0(program.symbols['hp1020_bulk_in_check'], [index, fill])
                        assert not failure, (name, fill, 'bulk-in-check.c', failure)
                    print('Bulk IN target: '+name, flush=True)
                target = dict(status='pass', elf_sha256=core.sha(elf.read_bytes()), audit=audit,
                              qemu_version=q.version)
        assert all(core.sha((ROOT/n).read_bytes()) == h for n, h in tested.items())
        report = dict(status='pass', source_sha256=tested, cases=CASES, fills=[0, 204], target=target,
                      limits='Supplied DCD settlement and reset, RAM only. No controller, host receipt, physical status or printing.')
        out = ROOT/'analysis/usb-path/tinyusb-printer/bulk-in-validation.json'
        # A host-only run must not silently replace the stronger target result.
        if args.target:
            out.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')


if __name__ == '__main__':
    main()
