#!/usr/bin/env python3
"""Bounded PJL ECHO/INFO STATUS through OUT and recorded bulk-IN publication."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pjl_base', ROOT/'scripts/validate-hp1020-udc-in-publish.py')
publication = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = publication
spec.loader.exec_module(publication)
base, core = publication.base, publication.core
SOURCE = ROOT/'open-firmware/pjl-command'
CASES = ('echo-whole', 'echo-one-byte', 'echo-split-seven', 'magic-inside-echo',
         'two-replies-backpressure', 'out-zlp-is-not-eof', 'largest-short-reply',
         'oversized-echo-rejected', 'unhandled-long-pjl-line', 'partial-command-reset',
         'borrowed-reply-reset', 'published-reply-late-success', 'refusal-before-bind',
         'failure-after-bind', 'binary-text-is-not-a-command', 'echo-around-two-decoded-pages',
         'unsent-reply-reset', 'uncertain-publication-recovery',
         'status-online', 'status-offline', 'status-zero-direct-query',
         'status-stale-epoch', 'status-stale-generation', 'status-unavailable',
         'status-invalid-online', 'status-out-of-profile-code', 'status-no-provider',
         'status-sampled-after-backpressure', 'status-reset-retains-original-reply',
         'status-one-byte-query', 'status-exact-command-profile', 'status-code-limit',
         'reap-does-not-pump-or-resubmit')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', action='store_true')
    args = parser.parse_args()
    stock_path = ROOT/'analysis/status-path/status-reply-execution.json'
    stock = json.loads(stock_path.read_text())
    assert stock['status']=='pass' and stock['elf_sha256']==core.sha((ROOT/'analysis/sihp1020.elf').read_bytes())
    assert all(core.sha((ROOT/n).read_bytes())==h for n,h in stock['source_sha256'].items())
    stock_replies = {r['name']:bytes.fromhex(r['expected_hex']) for r in stock['observations'] if r['expected_hex']}
    oracles = {18:stock_replies['info_ready'],19:stock_replies['info_cover_code'],
               20:stock_replies['info_zero'],27:stock_replies['info_ready'],
               28:stock_replies['info_ready'],29:stock_replies['info_ready']}
    with tempfile.TemporaryDirectory(prefix='hp1020-pjl-command-') as directory:
        temp = Path(directory)
        tested = base.sources(temp)
        paths = [*SOURCE.glob('*.[ch]'), *publication.SOURCE.glob('*.[ch]'),
                 *publication.staging.SOURCE.glob('*.[ch]'), Path(__file__)]
        paths += [ROOT/'scripts'/('validate-hp1020-'+name+'.py')
                  for name in ('bulk-in', 'udc-in', 'udc-in-publish')]
        tested.update({str(p.relative_to(ROOT)): core.sha(p.read_bytes()) for p in paths})
        tested[str(stock_path.relative_to(ROOT))] = core.sha(stock_path.read_bytes())
        core.command(['python3', ROOT/'scripts/prepare-hp1020-tinyusb.py', '--output', temp/'effective', '--patched'])
        base.compile_host(temp, temp/'effective', SOURCE/'test.c', SOURCE/'test-main.c')
        document, images, fixtures = base.image_documents(temp)
        job = document(['small', 'slim'])
        expected = images['small'][1]+images['slim'][1]
        assert len(expected) == 128 and len(job) < 4096
        (temp/'job').write_bytes(job)
        tested.update({str(p.relative_to(ROOT)): core.sha(p.read_bytes()) for p in fixtures})
        for index, name in enumerate(CASES):
            for fill in (0, 204):
                core.command([temp/'host', str(index), str(fill), temp/'job', temp/'pixels'])
                if index == 15:
                    assert (temp/'pixels').read_bytes() == expected
                if index in oracles:
                    assert (temp/'pixels').read_bytes() == oracles[index], (name, 'stock reply mismatch')
            print('PJL command host: '+name, flush=True)
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
                        q.put(program.symbols['hp1020_command_job'], job)
                        failure = q.call0(program.symbols['hp1020_pjl_command_check'], [index, fill, len(job)])
                        assert not failure, (name, fill, 'pjl-command/test.c or included fixture', failure)
                        if index == 15:
                            assert q.read(program.symbols['hp1020_bulk_fixture_pixels'], len(expected)) == expected
                        if index in oracles:
                            count = int.from_bytes(q.read(program.symbols['hp1020_command_last_length'],4),'big')
                            assert q.read(program.symbols['hp1020_command_last_reply'],count)==oracles[index], (name,'stock reply mismatch')
                    print('PJL command target: '+name, flush=True)
                target = dict(status='pass', elf_sha256=core.sha(elf.read_bytes()), audit=audit, qemu_version=q.version)
        assert all(core.sha((ROOT/n).read_bytes()) == h for n, h in tested.items())
        if args.target:
            (ROOT/'analysis/usb-path/pjl-command-validation.json').write_text(json.dumps(dict(
                status='pass', source_sha256=tested, cases=CASES, fills=[0, 204], target=target,
                job_sha256=core.sha(job), exact_pixels_sha256=core.sha(expected),
                limits='Bounded uppercase ECHO and INFO STATUS. ECHO text at most50 bytes; status CODE=0..99999, ONLINE supplied, DISPLAY empty. Stale/unavailable/invalid status gives no reply. Synthetic OUT/DCD, recorded IN publication and supplied physical facts. No physical status provider, host receipt, entry-loop integration or printing.'),
                indent=2, sort_keys=True)+'\n')


if __name__ == '__main__':
    main()
