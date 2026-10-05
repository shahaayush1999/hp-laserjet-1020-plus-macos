#!/usr/bin/env python3
"""Combined controller, OUT/IN and command gates; synthetic RAM only."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('service_base', ROOT/'scripts/validate-hp1020-tinyusb-printer.py')
base = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = base
spec.loader.exec_module(base)
core = base.core
SOURCE = ROOT/'open-firmware/usb-service'
PARTS = ('udc-ep0', 'udc-out', 'udc-setup', 'udc-program', 'udc-publish',
         'udc-in', 'udc-in-publish', 'pjl-command', 'usb-service')
FIXTURES = ('udc-ep0-test', 'udc-composed-test', 'udc-program-test', 'udc-publish-test')
CASES = ('echo-status-and-two-pages', 'captured-setup-blocks-both-directions',
         'original-result-reaped-without-input-or-status',
         'uncertain-in-poll-reset-drain-and-clear', 'programming-write-failure',
         'out-publication-failure-blocks-in', 'busy-cookie-and-graph-gates',
         'in-failure-binding-service-is-not-reset', 'interface-selection-service-only-to-ready')


def build(temp, effective, target):
    parts = [ROOT/'open-firmware'/name for name in PARTS]
    implementation = [SOURCE/'test.c']
    implementation += [p/('hp1020_'+p.name.replace('-', '_')+'.c') for p in parts]
    implementation += [base.ADAPTER/'hp1020_tusb_adapter.c', base.PRINTER/'hp1020_usb_printer.c',
                       base.RX/'hp1020_usb_receive.c', base.RX/'hp1020_usb_document.c']
    implementation += [base.IMG/name for name in ('hp1020_image.c', 'hp1020_image_page.c',
                       'hp1020_image_stream.c', 'hp1020_image_ring.c', 'hp1020_image_output.c')]
    implementation += [base.SEM/'hp1020_semantic.c', base.SEM/'hp1020_page_plan.c',
                       core.VENDOR/'libjbig/jbig85.c', core.VENDOR/'libjbig/jbig_ar.c']
    implementation += [effective/'src'/name for name in ('tusb.c', 'device/usbd.c', 'common/tusb_fifo.c')]
    include = ['-I'+str(p) for p in (*parts, ROOT/'open-firmware', base.SRC, base.ADAPTER,
               base.PROTOCOL, base.PRINTER, base.RX, base.IMG, base.SEM,
               core.VENDOR/'libjbig', effective/'src')]
    common = ['-Wall', '-Wextra', '-Werror', '-fno-common']
    if not target:
        flags = ['clang', '-std=c11', '-O1', '-g', '-fsanitize=address,undefined', *common]
        core.command(flags+include+implementation+[SOURCE/'test-main.c', '-o', temp/'host'])
        full = ROOT/'vendor/foo2zjs-source'
        core.command(flags+['-I'+str(full), base.IMG/'reference.c', full/'jbig.c',
                            full/'jbig_ar.c', '-o', temp/'reference'])
        return temp/'host'
    cc = os.environ.get('HP1020_GCC_PREFIX', '/tmp/hp1020-xtensa-gcc14/bin/xtensa-fsf-elf')+'-gcc'
    core.command(['python3', ROOT/'scripts/check-hp1020-c-compiler-profile.py', cc])
    destination = temp/'target'
    destination.mkdir()
    implementation += [base.IMG/'target-memory.c', base.SEM/'freestanding/memory.c']
    flags = ['-Os', '-ffreestanding', '-fno-builtin', '-fno-tree-loop-distribute-patterns',
             '-ffunction-sections', '-fdata-sections', '-mtext-section-literals',
             '-fstack-usage', '-DNDEBUG=', *common,
             '-I'+str(base.PROTOCOL/'freestanding'), '-I'+str(base.IMG/'freestanding'), *include]
    objects = []
    for index, source in enumerate(implementation):
        obj = destination/(str(index)+'.o')
        warning = ['-Wno-type-limits'] if source == effective/'src/device/usbd.c' else []
        core.command([cc, *flags, *warning, '-c', source, '-o', obj])
        objects.append(obj)
    elf = destination/'target-check.elf'
    core.command([cc, '-nostdlib', '-Wl,-T,'+str(ROOT/'open-firmware/udc-publish-test/target-check.ld'),
                  *objects, '-lgcc', '-o', elf])
    assert not core.command([core.PREFIX+'-nm', '-u', elf]).strip()
    return elf


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', action='store_true')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='hp1020-usb-service-') as directory:
        temp = Path(directory)
        tested = base.sources(temp)
        paths = [Path(__file__), ROOT/'open-firmware/udc-publish-test/target-check.ld']
        for name in PARTS:
            paths += list((ROOT/'open-firmware'/name).glob('hp1020_*.[ch]'))
        paths += [SOURCE/'test.c', SOURCE/'test-main.c']
        paths += [ROOT/'open-firmware'/name/'fixture.c' for name in FIXTURES]
        tested.update({str(p.relative_to(ROOT)): core.sha(p.read_bytes()) for p in paths})
        core.command(['python3', ROOT/'scripts/prepare-hp1020-tinyusb.py', '--output', temp/'effective', '--patched'])
        host = build(temp, temp/'effective', False)
        document, images, fixtures = base.image_documents(temp)
        job = document(['small', 'slim'])
        expected = images['small'][1]+images['slim'][1]
        assert len(expected) == 128 and len(job) < 4096
        (temp/'job').write_bytes(job)
        tested.update({str(p.relative_to(ROOT)): core.sha(p.read_bytes()) for p in fixtures})
        for index, name in enumerate(CASES):
            for fill in (0, 204):
                core.command([host, index, fill, temp/'job', temp/'pixels'])
                if not index:
                    assert (temp/'pixels').read_bytes() == expected
            print('USB service host: '+name, flush=True)
        target = None
        if args.target:
            elf = build(temp, temp/'effective', True)
            program, audit = core.audit_target(elf)
            from hp1020_qemu_ram import QemuRAM
            with QemuRAM() as q:
                for index, name in enumerate(CASES):
                    for fill in (0, 204):
                        q.load(elf)
                        q.put(program.symbols['hp1020_service_job'], job)
                        failure = q.call0(program.symbols['hp1020_usb_service_check'], [index, fill, len(job)])
                        assert not failure, (name, fill, 'usb-service/test.c or included fixture', failure)
                        if not index:
                            assert q.read(program.symbols['hp1020_bulk_fixture_pixels'], len(expected)) == expected
                    print('USB service target: '+name, flush=True)
                target = dict(status='pass', elf_sha256=core.sha(elf.read_bytes()), audit=audit, qemu_version=q.version)
        assert all(core.sha((ROOT/n).read_bytes()) == h for n, h in tested.items())
        if args.target:
            (ROOT/'analysis/usb-path/usb-service-validation.json').write_text(json.dumps(dict(
                status='pass', source_sha256=tested, cases=CASES, fills=[0, 204], target=target,
                job_sha256=core.sha(job), exact_pixels_sha256=core.sha(expected),
                limits='Real controller-program/OUT/IN/PJL/TinyUSB composition with supplied observations, cache leases, status and DMA settlement in RAM. Busy flags and binding-unready distinction are labeled gate-only mutations. No physical controller, status provider, host receipt, entry-loop backend or printing.'),
                indent=2, sort_keys=True)+'\n')


if __name__ == '__main__':
    main()
