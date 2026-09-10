#!/usr/bin/env python3
"""Bounded ZjStream consumption: reused packets/chunks and synchronous row bands."""
import argparse
import importlib.util
import json
from pathlib import Path
import random
import struct
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('image_pages', ROOT/'scripts/validate-hp1020-image-pages.py')
pages = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = pages
spec.loader.exec_module(pages)
core = pages.core
SRC, SEM, OUT = pages.SRC, pages.SEM, pages.OUT
MAX_PACKET = 65552
NO_REJECTION = 0xffffffff


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--target', action='store_true')
    args = ap.parse_args()
    cases, targets, controls = [], [], []
    base = pages.chunks((ROOT/'analysis/samples/generated/matrix-a4_default.zjs').read_bytes())

    def body(bie, splits=1, tail=None, max_bid=None):
        w, h = struct.unpack_from('>II', bie, 4)
        items = bytearray(base[1][1])
        for off in range(0, len(items), 12):
            ident = struct.unpack_from('>H', items, off+4)[0]
            if ident in (13, 18): struct.pack_into('>I', items, off+8, h)
            if ident == 12: struct.pack_into('>I', items, off+8, w)
            if ident == 17: struct.pack_into('>I', items, off+8, w//2)
        compressed = bie[20:]
        padding = bytes(16+((-len(compressed)) & 3)) if tail is None else tail
        if max_bid:
            # Match foo2zjs: the final compressed chunk also owns the padding.
            bids = [compressed[i:i+max_bid] for i in range(0, len(compressed), max_bid)]
            bids[-1] += padding
        else:
            bid = compressed+padding
            bids = [bid[len(bid)*i//splits:len(bid)*(i+1)//splits] for i in range(splits)]
        assert all(bids)
        return [(2, bytes(items), base[1][2], base[1][3]), (4, bie[:20], 0, 0)] + [
            (5, bid, 0, 0) for bid in bids] + [(6, b'', 0, 0), (3, b'', 0, 0)]

    def doc(*images):
        return b'JZJZ'+pages.pack([base[0]]+sum(images, [])+[base[-1]])

    with tempfile.TemporaryDirectory(prefix='hp1020-image-stream-') as directory:
        temp = Path(directory)
        host, reference, legacy = temp/'host', temp/'reference', temp/'legacy'
        inputfile, capture, oracle, packed = temp/'input', temp/'capture', temp/'oracle', temp/'packed'
        flags = [core.os.environ.get('CC', 'clang'), '-std=c11', '-O1', '-g', '-fno-common',
                 '-Wall', '-Wextra', '-Werror', '-fsanitize=address,undefined']
        c_sources = [SRC/'hp1020_image.c', SRC/'hp1020_image_page.c', SRC/'hp1020_image_stream.c',
                     SRC/'stream-fixture.c', SRC/'host-stream-check.c', SEM/'hp1020_semantic.c',
                     SEM/'hp1020_page_plan.c', core.VENDOR/'libjbig/jbig85.c', core.VENDOR/'libjbig/jbig_ar.c']
        core.command(flags+['-DHP1020_IMAGE_HOST_CHECK', '-I'+str(SRC), '-I'+str(SEM),
                     '-I'+str(core.VENDOR/'libjbig')]+c_sources+['-o', host])
        full = ROOT/'vendor/foo2zjs-source'
        core.command(flags+['-I'+str(full), SRC/'reference.c', full/'jbig.c', full/'jbig_ar.c', '-o', reference])
        core.command(flags+['-I'+str(SEM), SEM/'host-check.c', SEM/'hp1020_semantic.c',
                            SEM/'hp1020_page_plan.c', '-o', legacy])

        def original(bie, expected=None):
            inputfile.write_bytes(bie)
            info = json.loads(core.command([reference, 'decode', inputfile, oracle]))
            decoded = oracle.read_bytes()
            if expected is not None: assert decoded == expected, 'original encoder/decoder differs from source pixels'
            return decoded, info

        def run(name, data, expected=None, fragment=7, packet=4096, fill=204,
                error=0, reject_after=NO_REJECTION, target=False):
            inputfile.write_bytes(data)
            a = json.loads(core.command([host, inputfile, fragment, packet, fill, reject_after, capture, 1]))
            observed = capture.read_bytes()
            assert a[0] == error, (name, a, error)
            assert a[10] == 0 and a[11] == a[19] == 1, (name, 'guards/order/retention/sticky error', a)
            assert a[5] == len(observed) and a[6] == core.fnv(observed), (name, 'capture accounting')
            assert a[8] <= MAX_PACKET and a[15] == MAX_PACKET+4096+8192
            if expected is not None: assert observed == expected, (name, 'full output differs')
            if not error:
                assert a[9] == a[16] == 0 and a[7] == a[21], (name, 'unreleased chunk or band', a)
                assert a[22] == (7 if a[2] else 0), (name, 'retained-mode bridge accepted streaming state')
                headers, left, documents, rows, bands, raster_count = [], data, 0, 0, 0, 0
                while b'JZJZ' in left:
                    start = left.index(b'JZJZ')
                    parts = pages.chunks(left)
                    headers += [p for k, p, _, _ in parts if k == 4]
                    documents += 1
                    raster_count += sum(k == 5 for k, _, _, _ in parts)
                    left = left[start+4+len(pages.pack(parts)):]
                for header in headers:
                    width, height = struct.unpack_from('>II', header, 4)
                    chunk_rows = (8192//(width//8)) & ~3
                    rows += height
                    bands += (height+chunk_rows-1)//chunk_rows
                assert a[1:5] == [documents, len(headers), rows, bands] and a[7] == raster_count
                assert a[20] == core.fnv(b''.join(headers)), (name, 'exact BIH bytes')
            if reject_after != NO_REJECTION:
                assert a[13] == 3 and a[16] == 1 and a[4] == reject_after, (name, 'consumer failure not retained', a)
            cases.append(dict(case=name, status='pass', input_sha256=core.sha(data),
                              input_bytes=len(data), output_sha256=core.sha(observed), stats=a,
                              fragment=fragment, packet=packet, fill=fill, reject_after=reject_after))
            if target: targets.append((name, data, fragment, packet, fill, reject_after, a, observed))
            return a

        for p in sorted((ROOT/'analysis/samples/generated').glob('*.zjs')):
            raw, _ = original(core.sample_bie(p))
            error = 1 if 'logical_clip' in p.stem else 4 if '2400x600' in p.stem else 0
            for fragment, packet in ((1, 19), (7, 4096), (MAX_PACKET, MAX_PACKET)):
                run(p.stem+f'/fragment={fragment}/packet={packet}', p.read_bytes(),
                    raw if not error else None, fragment, packet, error=error, target=fragment == 7)
        print('stream: saved sample matrix passed', flush=True)
        small = (OUT/'fixtures/32x8-stripe4-black.jbg').read_bytes()
        medium = (OUT/'fixtures/9600x132-stripe128-edges.jbg').read_bytes()
        wide = (OUT/'fixtures/16384x4-stripe128-edges.jbg').read_bytes()
        smallraw, _ = original(small)
        mediumraw, _ = original(medium)
        wideraw, _ = original(wide)
        for name, bie, raw in (('small', small, smallraw), ('medium', medium, mediumraw), ('max-width', wide, wideraw)):
            for fill in (0, 204):
                run('pattern/'+name+f'/fill={fill}', doc(body(bie)), raw, fill=fill, target=True)
        for count in (6, 13, 64, 129, 257):
            data = doc(body(medium, count))
            a = run(f'split-bid/{count}', data, mediumraw, fragment=1, target=True)
            assert a[7] == count
            if count >= 129:
                inputfile.write_bytes(data)
                old = json.loads(core.command([legacy, inputfile, 7, 65552]))
                assert old['result'] == 3 and len(old['rasters']) == 128
                controls.append(dict(case=f'retained-mode/{count}', status='expected limit',
                                     result=old['result'], retained_rasters=len(old['rasters']),
                                     input_sha256=core.sha(data)))
        run('two-pages-one-document', doc(body(small), body(medium, 13)), smallraw+mediumraw, target=True)
        run('two-documents', doc(body(medium, 6))+doc(body(small)), mediumraw+smallraw, target=True)
        run('empty-document', doc(), b'', target=True)
        run('empty-before-page', doc()+doc(body(small)), smallraw, packet=19, target=True)
        run('page-metadata-limit/16', doc(*[body(small) for _ in range(16)]), smallraw*16, target=True)
        run('page-metadata-limit/17', doc(*[body(small) for _ in range(17)]), smallraw*16, error=3, target=True)
        for name, tail in (('missing', b''), ('short', bytes(15)), ('long', bytes(20)), ('nonzero', bytes(15)+b'\x01')):
            run('padding/'+name, doc(body(small, tail=tail)), error=1, target=True)
        run('missing-final-marker', doc(body(medium[:-2])), error=1, target=True)
        run('missing-end-doc', doc(body(small))[:-16], smallraw, error=5, target=True)
        run('truncated-chunk-header', doc(body(small))[:-8], smallraw, error=5, target=True)
        for stop in (0, 1, 32):
            run(f'consumer-error/after={stop}', doc(body(medium)), mediumraw[:stop*4800],
                error=3, reject_after=stop, target=True)
        # Exercise the legal final BID maximum using a standard COMMENT marker.
        # This transports real image data after a large, ignorable byte span.
        comment_size = 65536-6-len(small[20:])
        commented = small[:20]+b'\xff\x07'+struct.pack('>I', comment_size)+bytes(comment_size)+small[20:]
        original(commented, smallraw)
        assert len(commented)-20 == 65536
        for packet in (4096, MAX_PACKET):
            a = run(f'max-final-bid/packet={packet}', doc(body(commented)), smallraw,
                    fragment=7, packet=packet, target=True)
            assert a[8] == MAX_PACKET
        run('oversize-bid', doc(body(commented, tail=bytes(17))), b'', error=3, target=True)

        print('stream: boundaries, reuse and consumer errors passed; generating detailed page', flush=True)
        width, height, seed = 9856, 8208, 102020260910
        raw = random.Random(seed).randbytes(width//8*height)
        packed.write_bytes(raw)
        core.command([reference, 'encode', packed, inputfile, width, height, 128])
        bie = inputfile.read_bytes()
        decoded, info = original(bie, raw)
        assert info['consumed'] == len(bie)
        data = doc(body(bie, max_bid=65536))
        large_cases = []
        for fragment, fill in ((7, 0), (MAX_PACKET, 204)):
            a = run(f'detailed-legal/fragment={fragment}/fill={fill}', data, decoded,
                    fragment=fragment, packet=MAX_PACKET, fill=fill, target=True)
            assert a[7] > 128 and a[8] <= MAX_PACKET and a[9] == 0
            large_cases.append(cases[-1]['case'])
        generated = dict(width_bits=width, rows=height, pattern='Python random.Random(seed).randbytes',
                         seed=seed, stripe_rows=128, raw_bytes=len(raw), raw_sha256=core.sha(raw),
                         bie_bytes=len(bie), bie_sha256=core.sha(bie), zjs_bytes=len(data),
                         zjs_sha256=core.sha(data), cases=large_cases,
                         original_full_decoder=info,
                         scope='Deterministically generated host fixture; never retained whole in target RAM. Host compares every byte to original full decoding and source pixels.')
        print(f'stream: {len(cases)} host cases passed; detailed page uses {a[7]} BID chunks', flush=True)
        target_report = None
        if args.target:
            core.command([ROOT/'scripts/build-hp1020-image-target.sh'])
            elf = OUT/'target/target-check.elf'
            program, audit = core.audit_target(elf)
            from hp1020_qemu_ram import QemuRAM
            native = []
            with QemuRAM() as q:
                q.load(elf)
                version = q.version
                for name, data, fragment, packet, fill, reject_after, expected, observed in targets:
                    assert q.call0(program.symbols['hp1020_stream_reset'], [fill, reject_after]) == 0
                    feeds = 0
                    for pos in range(0, len(data), packet):
                        payload = data[pos:pos+packet]
                        q.put(program.symbols['hp1020_stream_input'], payload)
                        returned = q.call0(program.symbols['hp1020_stream_feed'], [len(payload), fragment])
                        feeds += 1
                        if returned: break
                    returned = q.call0(program.symbols['hp1020_stream_finish'], [])
                    actual = list(struct.unpack('>32I', q.read(program.symbols['hp1020_stream_stats'], 128)))
                    assert returned == actual[0]
                    assert actual[:14]+actual[15:] == expected[:14]+expected[15:], (name, actual, expected)
                    assert q.read(program.symbols['hp1020_stream_capture'], min(len(observed), 65536)) == observed[:65536]
                    native.append(dict(case=name, status='pass', stats=actual, feed_calls=feeds,
                                       packet_limit=packet, comparison='all output bytes' if len(observed) <= 65536 else
                                       'first 65536 bytes plus full FNV-1a and metadata/band counts'))
                    if len(native) % 10 == 0 or name.startswith('detailed-legal/'):
                        print(f'stream target: {len(native)}/{len(targets)} cases passed ({name})', flush=True)
            totals = {c['stats'][14]+c['stats'][15] for c in native}
            assert len(totals) == 1
            target_report = dict(status='pass', qemu_version=version, cases=native,
                                 state_and_memory_bytes=totals.pop(), elf_sha256=core.sha(elf.read_bytes()), audit=audit)
        sources = set(c_sources+[Path(__file__), ROOT/'scripts/validate-hp1020-image-core.py',
                      ROOT/'scripts/validate-hp1020-image-pages.py', ROOT/'scripts/build-hp1020-image-target.sh',
                      SRC/'reference.c', SEM/'host-check.c', full/'jbig.c', full/'jbig_ar.c'])
        sources.update(SRC.rglob('*.h'))
        sources.update(SEM.glob('*.h'))
        sources.update((core.VENDOR/'libjbig').glob('*.h'))
        sources.update(SRC.glob('*.c'))
        sources.update(SRC.glob('*.ld'))
        sources.update([full/'jbig.h', full/'jbig_ar.h', SEM/'freestanding/memory.c',
                        ROOT/'scripts/hp1020_qemu_ram.py', ROOT/'scripts/hp1020_xtensa_call0.py',
                        ROOT/'scripts/hp1020_xtensa_properties.py'])
        report = dict(status='pass', cases=cases, target=target_report, retained_mode_controls=controls,
                      generated_detailed_page=generated,
                      source_sha256={str(p.relative_to(ROOT)):core.sha(p.read_bytes()) for p in sorted(sources)},
                      sample_sha256={str(p.relative_to(ROOT)):core.sha(p.read_bytes()) for p in sorted((ROOT/'analysis/samples/generated').glob('*.zjs'))},
                      fixture_sha256={str(p.relative_to(ROOT)):core.sha(p.read_bytes()) for p in sorted((OUT/'fixtures').glob('*.jbg'))},
                      scope='The existing open parser consumes complete ZjStream input through a fixed compressed chunk, a bounded decoder and a synchronous band consumer. No complete compressed or decoded page is kept in component memory.',
                      limits='16 retained page metadata slots, narrow planner/profile, default padding and a 65552-byte BID limit. Output remains provisional until finish. Consumer errors abort rather than retry. State/memory totals exclude code, stack, caller packets and test captures. No asynchronous scheduler, raw queue, cache, engine, USB, boot or printing.')
        name = 'stream-validation' if args.target else 'stream-host-validation'
        (OUT/f'{name}.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
        (OUT/f'{name}.md').write_text('# Open bounded ZjStream image consumption\n\nStatus: pass. '+report['scope']+'\n\n'
            +f"{len(cases)} host cases and {len(target_report['cases']) if target_report else 0} QEMU cases. Reused packets and compressed chunks, fragmented input, 129/257 BID partitions, consumer failures and final padding boundaries are checked.\n\n"
            +f"The deterministic detailed page contains {generated['raw_bytes']} packed source bytes and {generated['zjs_bytes']} serialized bytes. Host output equals every original-decoder/source byte; larger target output uses a prefix plus full FNV-1a and counts.\n\n"
            +(f"The 32-bit component state and fixed memory total {target_report['state_and_memory_bytes']} bytes.\n\n" if target_report else '')
            +report['limits']+'\n')
        print(f"image stream: {len(cases)} host cases; target={len(target_report['cases']) if target_report else 'not run'}")


if __name__ == '__main__':
    main()
