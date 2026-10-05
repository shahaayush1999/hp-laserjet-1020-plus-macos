#!/usr/bin/env python3
"""IN1 register publication through recording hooks and the real bounded DCD."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('in_publish_base', ROOT/'scripts/validate-hp1020-udc-in.py')
staging = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = staging
spec.loader.exec_module(staging)
base, core = staging.base, staging.core
SOURCE = ROOT/'open-firmware/udc-in-publish'
CASES = ('already-clear-full', 'clear-nak-short-concurrent-rx', 'explicit-zlp',
         'missing-facts', 'unsupported-register-state', 'cnak-not-observed',
         *('failed-hook-'+str(i) for i in range(6, 18)),
         'read-errors-can-retry', 'controller-binding-not-ready',
         'stale-or-reset-before-publication', 'dma-done-is-not-fifo-empty')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', action='store_true')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='hp1020-in-publish-') as directory:
        temp = Path(directory)
        tested = base.sources(temp)
        for path in [*SOURCE.glob('*.[ch]'), *staging.SOURCE.glob('*.[ch]'), Path(__file__),
                     ROOT/'scripts/validate-hp1020-udc-in.py', ROOT/'scripts/validate-hp1020-bulk-in.py']:
            tested[str(path.relative_to(ROOT))] = core.sha(path.read_bytes())
        core.command(['python3', ROOT/'scripts/prepare-hp1020-tinyusb.py', '--output', temp/'effective', '--patched'])
        base.compile_host(temp, temp/'effective', SOURCE/'test.c', SOURCE/'test-main.c')
        for index, name in enumerate(CASES):
            for fill in (0, 204):
                core.command([temp/'host', str(index), str(fill)])
            print('IN publication host: '+name, flush=True)
        target = None
        if args.target:
            os.environ['HP1020_TUSB_FIXTURE'] = str(SOURCE/'test.c')
            os.environ['HP1020_TUSB_TARGET_DIR'] = str(temp/'target')
            core.command(['bash', ROOT/'scripts/build-hp1020-tinyusb-printer-target.sh'])
            elf = temp/'target/target-check.elf'
            program, audit = core.audit_target(elf)
            from hp1020_qemu_ram import QemuRAM
            with QemuRAM() as q:
                for index, name in enumerate(CASES):
                    for fill in (0, 204):
                        q.load(elf)
                        failure = q.call0(program.symbols['hp1020_udc_in_publish_check'], [index, fill])
                        assert not failure, (name, fill, 'udc-in-publish/test.c or included fixture', failure)
                    print('IN publication target: '+name, flush=True)
                target = dict(status='pass', elf_sha256=core.sha(elf.read_bytes()), audit=audit, qemu_version=q.version)
        assert all(core.sha((ROOT/n).read_bytes()) == h for n, h in tested.items())
        if args.target:
            (ROOT/'analysis/usb-path/udc-in-publish-validation.json').write_text(json.dumps(dict(
                status='pass', source_sha256=tested, cases=CASES, fills=[0, 204], target=target,
                limits='Recording I/O; independent register reads and supplied controller binding, cache/mapping, FIFO-empty and stability leases. No physical controller, host receipt or printing.'),
                indent=2, sort_keys=True)+'\n')


if __name__ == '__main__':
    main()
