#!/usr/bin/env python3
"""IN1 staging and descriptor settlement through real TinyUSB; supplied RAM only."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('udc_in_base', ROOT/'scripts/validate-hp1020-bulk-in.py')
bulk = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bulk
spec.loader.exec_module(bulk)
base, core = bulk.base, bulk.core
SOURCE = ROOT/'open-firmware/udc-in'
CASES = ('explicit-zlp', 'short-packet', 'full-packet', 'cancel-before-publication',
         'cancel-after-publication-and-reuse', 'corrupt-descriptor', 'wrong-actual',
         'failed-bound-submission', 'late-success-after-reset')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', action='store_true')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='hp1020-udc-in-') as directory:
        temp = Path(directory)
        tested = base.sources(temp)
        for path in [*SOURCE.glob('*.[ch]'), Path(__file__), ROOT/'scripts/validate-hp1020-bulk-in.py']:
            tested[str(path.relative_to(ROOT))] = core.sha(path.read_bytes())
        core.command(['python3', ROOT/'scripts/prepare-hp1020-tinyusb.py', '--output', temp/'effective', '--patched'])
        base.compile_host(temp, temp/'effective', SOURCE/'test.c', SOURCE/'test-main.c')
        for index, name in enumerate(CASES):
            for fill in (0, 204):
                core.command([temp/'host', str(index), str(fill)])
            print('IN descriptor host: '+name, flush=True)
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
                        failure = q.call0(program.symbols['hp1020_udc_in_check'], [index, fill])
                        assert not failure, (name, fill, 'udc-in/test.c or included bulk-in-check.c', failure)
                    print('IN descriptor target: '+name, flush=True)
                target = dict(status='pass', elf_sha256=core.sha(elf.read_bytes()), audit=audit,
                              qemu_version=q.version)
        assert all(core.sha((ROOT/n).read_bytes()) == h for n, h in tested.items())
        if args.target:
            out = ROOT/'analysis/usb-path/udc-in-validation.json'
            out.write_text(json.dumps(dict(status='pass', source_sha256=tested, cases=CASES,
                fills=[0, 204], target=target,
                limits='Supplied packet64/BE mode, CPU/DMA mappings, visibility, exact DMA count and terminal memory accesses. No FIFO-drain/capacity proof, register publication, hardware access or host receipt.'),
                indent=2, sort_keys=True)+'\n')


if __name__ == '__main__':
    main()
