#!/usr/bin/env python3
"""Cooperative decoding with real backpressure; supplied software output only."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import struct
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pump_pages', ROOT/'scripts/validate-hp1020-image-pages.py')
pages = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = pages
spec.loader.exec_module(pages)
core, IMG, SEM = pages.core, pages.SRC, pages.SEM
SRC = ROOT/'open-firmware/image-pump'
CASES = ('two-page-stream', 'full-ring-pauses-without-waiting', 'multiple-outstanding-slots',
         'stop-retains-owned-output', 'late-padding-error', 'missing-end-doc',
         'retained-page-and-document-events', 'one-byte-fragments', 'wrong-event-ack',
         'empty-and-successive-documents')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', action='store_true')
    args = parser.parse_args()
    implementation = [SRC/'hp1020_image_pump.c', SRC/'test.c', IMG/'hp1020_image.c',
                      IMG/'hp1020_image_ring.c', SEM/'hp1020_semantic.c', SEM/'hp1020_page_plan.c',
                      core.VENDOR/'libjbig/jbig85.c', core.VENDOR/'libjbig/jbig_ar.c']
    includes = ['-I'+str(p) for p in (SRC, IMG, SEM, core.VENDOR/'libjbig')]
    warnings = ['-Wall', '-Wextra', '-Werror', '-fno-common']
    full = ROOT/'vendor/foo2zjs-source'
    source_paths = [*implementation, SRC/'test-main.c', SRC/'target-check.ld', Path(__file__),
                    IMG/'target-memory.c', SEM/'freestanding/memory.c', IMG/'reference.c']
    source_paths += list(SRC.glob('*.h'))+list(IMG.glob('*.h'))+list(SEM.glob('*.h'))
    source_paths += list((IMG/'freestanding').glob('*.h'))+list((core.VENDOR/'libjbig').glob('*.h'))
    source_paths += [full/n for n in ('jbig.c', 'jbig_ar.c', 'jbig.h', 'jbig_ar.h')]
    source_paths += [ROOT/'scripts'/n for n in ('validate-hp1020-image-pages.py',
                     'validate-hp1020-image-core.py', 'check-hp1020-c-compiler-profile.py',
                     'hp1020_xtensa_call0.py', 'hp1020_xtensa_properties.py', 'hp1020_qemu_ram.py')]
    tested = {str(p.relative_to(ROOT)): core.sha(p.read_bytes()) for p in source_paths}
    with tempfile.TemporaryDirectory(prefix='hp1020-image-pump-') as directory:
        temp = Path(directory)
        flags = ['clang', '-std=c11', '-O1', '-g', '-fsanitize=address,undefined', *warnings]
        core.command(flags+includes+implementation+[SRC/'test-main.c', '-o', temp/'host'])
        core.command(flags+['-I'+str(full), IMG/'reference.c', full/'jbig.c', full/'jbig_ar.c', '-o', temp/'reference'])
        images = {}
        for name, w, h, stripe, kind in (('small', 32, 8, 4, 'black'), ('medium', 9600, 132, 128, 'edges')):
            fixture = core.OUT/'fixtures'/f'{w}x{h}-stripe{stripe}-{kind}.jbg'
            raw = core.pattern(w, h, kind)
            info = json.loads(core.command([temp/'reference', 'decode', fixture, temp/'reference-pixels']))
            assert (temp/'reference-pixels').read_bytes() == raw and info['consumed'] == fixture.stat().st_size
            images[name] = fixture.read_bytes(), raw
            tested[str(fixture.relative_to(ROOT))] = core.sha(fixture.read_bytes())
        fixture = ROOT/'analysis/samples/generated/matrix-a4_default.zjs'
        tested[str(fixture.relative_to(ROOT))] = core.sha(fixture.read_bytes())
        base = pages.chunks(fixture.read_bytes())

        def body(name, bad_padding=False):
            bie, _ = images[name]
            w, h = struct.unpack_from('>II', bie, 4)
            items = bytearray(base[1][1])
            for off in range(0, len(items), 12):
                ident = struct.unpack_from('>H', items, off+4)[0]
                value = {4: 1, 12: w, 13: h, 17: w//2, 18: h}.get(ident)
                if value is not None:
                    struct.pack_into('>I', items, off+8, value)
            payload = bie[20:]+bytes(16+((-len(bie[20:])) & 3))
            if bad_padding:
                payload = payload[:-1]+b'\x01'
            # Real chunk boundaries split compressed data and trailing padding.
            cuts = sorted({0, min(7, len(payload)), len(payload)-5, len(payload)})
            return [(2, bytes(items), base[1][2], base[1][3]), (4, bie[:20], 0, 0)]+[
                (5, payload[a:b], 0, 0) for a, b in zip(cuts, cuts[1:]) if a < b]+[(6, b'', 0, 0), (3, b'', 0, 0)]

        def doc(names, bad=False):
            return b'JZJZ'+pages.pack([base[0]]+sum((body(name, bad and i == len(names)-1)
                for i, name in enumerate(names)), [])+[base[-1]])

        normal = doc(['medium', 'small'])
        expected = images['medium'][1]+images['small'][1]
        inputs = [normal]*len(CASES)
        inputs[4] = doc(['medium', 'small'], True)
        inputs[5] = normal[:-16]
        inputs[9] = doc([])+doc(['medium'])+doc([])+doc(['small'])
        observed = {}
        rows = []
        for mode, name in enumerate(CASES):
            (temp/'job').write_bytes(inputs[mode])
            for fill in (0, 204):
                stats = json.loads(core.command([temp/'host', mode, fill, temp/'job', temp/'pixels']))
                pixels = (temp/'pixels').read_bytes()
                assert pixels == expected[:len(pixels)], (name, 'pixel prefix')
                if mode not in (3, 4, 8):
                    assert pixels == expected and stats[1] == 2
                    assert stats[2] == (0 if mode == 5 else 4 if mode == 9 else 1)
                observed[mode, fill] = stats, pixels
                rows.append(dict(case=name, fill=fill, input_sha256=core.sha(inputs[mode]),
                                 pixels_sha256=core.sha(pixels), host_stats=stats))
            print('Image pump host: '+name, flush=True)
        target = None
        if args.target:
            cc = os.environ.get('HP1020_GCC_PREFIX', '/tmp/hp1020-xtensa-gcc14/bin/xtensa-fsf-elf')+'-gcc'
            core.command(['python3', ROOT/'scripts/check-hp1020-c-compiler-profile.py', cc])
            flags = ['-Os', '-ffreestanding', '-fno-builtin', '-fno-tree-loop-distribute-patterns',
                     '-ffunction-sections', '-fdata-sections', '-mtext-section-literals',
                     '-fstack-usage', '-DNDEBUG=', *warnings, '-I'+str(IMG/'freestanding'), *includes]
            objects = []
            for i, source in enumerate(implementation+[IMG/'target-memory.c', SEM/'freestanding/memory.c']):
                obj = temp/f'{i}.o'
                core.command([cc, *flags, '-c', source, '-o', obj])
                objects.append(obj)
            elf = temp/'target.elf'
            core.command([cc, '-nostdlib', '-Wl,-T,'+str(SRC/'target-check.ld'), *objects, '-lgcc', '-o', elf])
            assert not core.command([core.PREFIX+'-nm', '-u', elf]).strip()
            program, audit = core.audit_target(elf)
            from hp1020_qemu_ram import QemuRAM
            with QemuRAM() as q:
                for mode, name in enumerate(CASES):
                    for fill in (0, 204):
                        q.load(elf)
                        q.put(program.symbols['hp1020_pump_job'], inputs[mode])
                        failure = q.call0(program.symbols['hp1020_image_pump_check'], [mode, fill, len(inputs[mode])])
                        assert not failure, (name, fill, 'image-pump/test.c', failure)
                        stats = list(struct.unpack('>8I', q.read(program.symbols['hp1020_pump_stats'], 32)))
                        host, pixels = observed[mode, fill]
                        assert stats[:7] == host[:7], (name, 'target counters', stats, host)
                        assert q.read(program.symbols['hp1020_pump_pixels'], len(pixels)) == pixels
                        rows[mode*2+(fill != 0)]['target_stats'] = stats
                    print('Image pump target: '+name, flush=True)
                target = dict(elf_sha256=core.sha(elf.read_bytes()), audit=audit, qemu_version=q.version)
        assert all(core.sha((ROOT/n).read_bytes()) == digest for n, digest in tested.items())
        if args.target:
            (ROOT/'analysis/open-firmware-model/image-core/pump-validation.json').write_text(json.dumps(dict(
                status='pass', source_sha256=tested, cases=rows, target=target,
                limits='One bounded decoder/input step and externally advanced RAM output. Original full JBIG decoder supplies independent pixel oracle. No USB integration, hardware output, physical status/cancellation, copy replay or throughput proof.'),
                indent=2, sort_keys=True)+'\n')


if __name__ == '__main__':
    main()
