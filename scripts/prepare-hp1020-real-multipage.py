#!/usr/bin/env python3
"""Freeze one complete, unmodified foo2zjs job from two literal PBM pages.

Host files only. Builds unchanged vendored encoder and independent full JBIG
decoder in a fresh directory. Never invokes a backend, device or normalizer.
The actual timestamp is retained; later target tests must reuse the saved bytes.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
PINS = {
    'vendor/foo2zjs-source/foo2zjs.c': '82a8acc1ffe81efbb372942d186e4fd9a5bb1ad7268f67bc1c8f6f1276cc3e3a',
    'vendor/foo2zjs-source/zjs.h': 'd62b56934283fdccfb9137bbf98d8faeab2c6b032b8b4a9732b963c8d5a9cc89',
    'vendor/foo2zjs-source/jbig.c': '835ce9b964a6735187b6e064562695063a65f35fe29924de1d60db660c3e21b3',
    'vendor/foo2zjs-source/jbig.h': '0c016a8c69e349c510630edbf5b96057be952c2ac19c1a9b8488ad8c9864d7a4',
    'vendor/foo2zjs-source/jbig_ar.c': 'a51552d2f839ce8b758400660bd423b95b4b25cde11e65cc4e7d6c63c1a19d6f',
    'vendor/foo2zjs-source/jbig_ar.h': '292c4c43c944e2573b558d89b7004cec6c59c70dbbfd7b9890868a2291d1250a',
    'open-firmware/image-core/reference.c': '4632dd64ca1df51f0a103f2d3acc54ec3dba500ce1803c21233cb13e6265dbac',
}
ARGS = ['-z1', '-P', '-L0', '-r600x600', '-n1', '-d1', '-u0x0', '-l0x0', '-p9', '-s7', '-m1']
# Frozen in the 2026-10-03 proposal before either encoder or candidate consumed it.
PAGE1 = bytes.fromhex('''
80 00 00 00 00 00 00 00 00 00 00 00 00 00 00 01
40 00 00 00 00 00 00 00 00 00 00 00 00 00 00 02
20 00 00 00 00 00 00 00 00 00 00 00 00 00 00 04
10 00 00 00 00 00 00 00 00 00 00 00 00 00 00 08
''')
PAGE2 = bytes.fromhex('''
a5 5a a5 5a a5 5a a5 5a a5 5a a5 5a a5 5a a5 5a a5 5a a5 5a a5 5a a5 5a a5 5a a5 5a a5 5a a5 5a
5a a5 5a a5 5a a5 5a a5 5a a5 5a a5 5a a5 5a a5 5a a5 5a a5 5a a5 5a a5 5a a5 5a a5 5a a5 5a a5
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff
ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
''')


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True)+'\n')


def run(argv, cwd, label, stdin=None, stdout=None):
    result = subprocess.run([str(x) for x in argv], cwd=cwd, input=stdin,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (cwd/(label+'.stderr')).write_bytes(result.stderr)
    (stdout or cwd/(label+'.stdout')).write_bytes(result.stdout)
    save(cwd/(label+'.command.json'), dict(argv=[str(x) for x in argv],
         returncode=result.returncode, stdout_sha256=sha(result.stdout), stderr_sha256=sha(result.stderr)))
    need(result.returncode == 0, 'failed '+label)
    return result.stdout


def inspect(raw):
    """Structural extraction only; no candidate parser/model/oracle imports."""
    magic = raw.index(b'JZJZ')
    need(raw.count(b'JZJZ') == 1, 'one actual document magic')
    prefix = raw[:magic]
    need(re.fullmatch(
        rb'\x1b%-12345X@PJL JOB\n@PJL SET JAMRECOVERY=OFF\n@PJL SET DENSITY=3\n'
        rb'@PJL SET ECONOMODE=OFF\n@PJL SET RET=MEDIUM\n@PJL INFO STATUS\n'
        rb'@PJL USTATUS DEVICE = ON\n@PJL USTATUS JOB = ON\n@PJL USTATUS PAGE = ON\n'
        rb'@PJL USTATUS TIMED = 30\n@PJL SET JOBATTR="JobAttr4=[0-9]{14}"\x00\x1b%-12345X', prefix),
        'complete original PJL prefix with actual timestamp')
    at = magic+4
    chunks, bies = [], []
    current = None
    while at < len(raw):
        need(at+16 <= len(raw), 'complete chunk header')
        size, kind, count, reserved, sig = struct.unpack_from('>IIIHH', raw, at)
        need(size >= 16 and at+size <= len(raw) and sig == 0x5a5a, 'bounded original chunk')
        payload = raw[at+16:at+size]
        items = []
        if kind in (0, 2):
            need(size == 16+12*count, 'only original uint32 metadata items')
            for off in range(0, len(payload), 12):
                length, ident, typ, param, value = struct.unpack_from('>IHBBI', payload, off)
                need((length, typ, param) == (12, 1, 0), 'uint32 metadata shape')
                items.append([ident, value])
        else:
            need(count == 0 and reserved == 0, 'unadorned non-metadata chunk')
        if kind == 4:
            need(current is None and len(payload) == 20, 'one original BIH')
            current = payload
        elif kind == 5:
            need(current is not None, 'BID follows BIH')
            current += payload
        elif kind == 6:
            need(current is not None and not payload, 'closed original BIE')
            bies.append(current)
            current = None
        chunks.append(dict(offset=at, bytes=size, kind=kind, count=count, reserved=reserved, items=items))
        at += size
        if kind == 1:
            break
    need([c['kind'] for c in chunks] == [0, 2, 4, 5, 6, 3, 2, 4, 5, 6, 3, 1], 'one two-page grammar')
    need(raw[at:] == b'\x1b%-12345X@PJL EOJ\n\x1b%-12345X', 'complete original PJL suffix')
    return dict(bytes=len(raw), sha256=sha(raw), magic_offset=magic, end_doc_offset=at,
                prefix_bytes=magic, suffix_bytes=len(raw)-at, chunks=chunks,
                packet_lengths=[min(64, len(raw)-i) for i in range(0, len(raw), 64)]), bies


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='fresh capture directory; never overwritten')
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    try:
        for name, expected in PINS.items():
            data = (ROOT/name).read_bytes()
            need(sha(data) == expected, 'original source pin: '+name)
            dest = out/'source'/name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
        (out/'generator.py').write_bytes(Path(__file__).read_bytes())
        save(out/'source-sha256.json', PINS)
        cc = Path(shutil.which('clang')).resolve()
        run([cc, '--version'], out, 'compiler-version')
        save(out/'compiler.json', dict(path=str(cc), sha256=sha(cc.read_bytes())))
        full = out/'source/vendor/foo2zjs-source'
        run([cc, '-O2', '-I'+str(full), full/'foo2zjs.c', full/'jbig.c', full/'jbig_ar.c',
             '-o', out/'foo2zjs'], out, 'build-encoder')
        run([cc, '-std=c11', '-O1', '-g', '-fsanitize=address,undefined', '-I'+str(full),
             out/'source/open-firmware/image-core/reference.c', full/'jbig.c', full/'jbig_ar.c',
             '-o', out/'reference'], out, 'build-reference')
        need(len(PAGE1) == 64 and len(PAGE2) == 128, 'literal source page lengths')
        pbm = b'P4\n128 4\n'+PAGE1+b'P4\n256 4\n'+PAGE2
        (out/'source.pbm').write_bytes(pbm)
        (out/'pixels.bin').write_bytes(PAGE1+PAGE2)
        raw = run([out/'foo2zjs', *ARGS], out, 'encode', stdin=pbm, stdout=out/'whole-job.zjs')
        # Seal unchanged encoder output before any parser/decoder inspection.
        save(out/'encoder-output.json', dict(input_sha256=sha(pbm), bytes=len(raw), sha256=sha(raw),
             argv=ARGS, encoder_sha256=sha((out/'foo2zjs').read_bytes()), normalized=False))
        info, bies = inspect(raw)
        pages = []
        for i, (bie, pixels, width) in enumerate(zip(bies, (PAGE1, PAGE2), (128, 256)), 1):
            path = out/f'page{i}.jbg'
            path.write_bytes(bie)
            decoded = out/f'page{i}.decoded'
            result = json.loads(run([out/'reference', 'decode', path, decoded], out, f'decode-{i}'))
            need(result['width'] == width and result['height'] == 4 and decoded.read_bytes() == pixels,
                 'original full JBIG decode differs from literal PBM pixels')
            padding = bie[result['consumed']:]
            need(16 <= len(padding) <= 19 and not any(padding), 'original final BID padding')
            pages.append(dict(index=i, bie_sha256=sha(bie), bie_bytes=len(bie), decode=result,
                              pixels_sha256=sha(pixels), padding_bytes=len(padding)))
        save(out/'validation.json', dict(status='pass', scope='host encoding and independent full-JBIG decoding only',
             stream=info, pages=pages, pixel_bytes=192, pixel_sha256=sha(PAGE1+PAGE2)))
        save(out/'manifest.json', {str(p.relative_to(out)): dict(bytes=p.stat().st_size, sha256=sha(p.read_bytes()))
             for p in sorted(out.rglob('*')) if p.is_file()})
        print(json.dumps(dict(status='pass', capture=str(out), bytes=len(raw), packets=len(info['packet_lengths']),
                              sha256=sha(raw), output_bytes=192)))
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc())
        raise


if __name__ == '__main__':
    main()
