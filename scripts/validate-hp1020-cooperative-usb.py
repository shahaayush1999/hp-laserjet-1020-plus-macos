#!/usr/bin/env python3
"""Cooperative pages through real software USB/PJL ownership; no device I/O."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import struct
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('cooperative_pjl', ROOT/'scripts/validate-hp1020-pjl-command.py')
pjl = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = pjl
spec.loader.exec_module(pjl)
base, core, SOURCE = pjl.base, pjl.core, pjl.SOURCE
CASES = ('control-and-replies-while-output-paused', 'reset-retains-output-and-original-reply',
         'late-invalid-padding', 'explicit-eof-without-end-doc', 'document-consumer-failure',
         'ordinary-document-pump-also-yields')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', action='store_true')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='hp1020-cooperative-usb-') as directory:
        temp = Path(directory)
        tested = base.sources(temp)
        paths = [*SOURCE.glob('*.[ch]'), *pjl.publication.SOURCE.glob('*.[ch]'),
                 *pjl.publication.staging.SOURCE.glob('*.[ch]'), Path(__file__)]
        paths += [ROOT/'scripts'/('validate-hp1020-'+name+'.py')
                  for name in ('bulk-in', 'udc-in', 'udc-in-publish', 'pjl-command')]
        tested.update({str(p.relative_to(ROOT)): core.sha(p.read_bytes()) for p in paths})
        core.command(['python3', ROOT/'scripts/prepare-hp1020-tinyusb.py', '--output', temp/'effective', '--patched'])
        base.compile_host(temp, temp/'effective', SOURCE/'cooperative-test.c', SOURCE/'cooperative-main.c')
        document, images, fixtures = base.image_documents(temp)
        job = document(['medium', 'small'])
        expected = images['medium'][1]+images['small'][1]
        chunks = base.pages.chunks(job)
        last = max(i for i, c in enumerate(chunks) if c[0] == 5)
        kind, payload, items, reserved = chunks[last]
        chunks[last] = (kind, payload[:-1]+b'\x01', items, reserved)
        invalid = b'JZJZ'+base.pages.pack(chunks)
        inputs = [job, job, invalid, job[:-16], job, job]
        tested.update({str(p.relative_to(ROOT)): core.sha(p.read_bytes()) for p in fixtures})
        observed, rows = {}, []
        for mode, name in enumerate(CASES):
            (temp/'job').write_bytes(inputs[mode])
            for fill in (0, 204):
                stats = json.loads(core.command([temp/'host', mode, fill, temp/'job', temp/'pixels']))
                pixels = (temp/'pixels').read_bytes()
                wanted = expected[:4800]+expected if mode == 1 else expected
                assert pixels == wanted[:len(pixels)], (name, 'independent pixels')
                if mode != 2:
                    assert pixels == wanted and stats[2] == 2, (name, 'whole pages', stats)
                assert stats[3] == (0 if mode in (2, 3, 4) else 1)
                observed[mode, fill] = stats, pixels
                rows.append(dict(case=name, fill=fill, input_sha256=core.sha(inputs[mode]),
                                 pixel_sha256=core.sha(pixels), host=stats))
            print('Cooperative USB host: '+name, flush=True)
        target = None
        if args.target:
            os.environ['HP1020_TUSB_FIXTURE'] = str(SOURCE/'cooperative-test.c')
            os.environ['HP1020_TUSB_TARGET_DIR'] = str(temp/'target')
            core.command(['bash', ROOT/'scripts/build-hp1020-tinyusb-printer-target.sh'])
            elf = temp/'target/target-check.elf'
            program, audit = core.audit_target(elf)
            from hp1020_qemu_ram import QemuRAM
            with QemuRAM() as q:
                for mode, name in enumerate(CASES):
                    for fill in (0, 204):
                        q.load(elf)
                        q.put(program.symbols['hp1020_cooperative_job'], inputs[mode])
                        failure = q.call0(program.symbols['hp1020_cooperative_check'], [mode, fill, len(inputs[mode])])
                        assert not failure, (name, fill, 'cooperative-test.c/included fixture', failure)
                        stats = list(struct.unpack('>8I', q.read(program.symbols['hp1020_cooperative_stats'], 32)))
                        host, pixels = observed[mode, fill]
                        assert stats == host, (name, stats, host)
                        assert q.read(program.symbols['hp1020_bulk_fixture_pixels'], len(pixels)) == pixels
                        rows[mode*2+(fill != 0)]['target'] = stats
                    print('Cooperative USB target: '+name, flush=True)
                target = dict(elf_sha256=core.sha(elf.read_bytes()), audit=audit, qemu_version=q.version)
        assert all(core.sha((ROOT/n).read_bytes()) == h for n, h in tested.items())
        if args.target:
            (ROOT/'analysis/usb-path/cooperative-validation.json').write_text(json.dumps(dict(
                status='pass', source_sha256=tested, cases=rows, target=target,
                limits='Existing TinyUSB/adapter/PJL/IN publication with synthetic DCD and separately advanced RAM rows. EP0 service during output waits, retained ownership and explicit supplied reset quiescence. Full pixels independently decoded; cancelled-generation prefix is retained separately. No physical controller, output completion, status sensors, throughput, entry-loop integration or printing.'),
                indent=2, sort_keys=True)+'\n')


if __name__ == '__main__':
    main()
