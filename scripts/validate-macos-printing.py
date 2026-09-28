#!/usr/bin/env python3
"""Offline tests of native CUPS filters/backend; USB is a separate mock process.
No installed queue, files, packages or device are modified. Paths/timeouts are
changed only in test builds, never through production environment bypasses.
"""
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import struct
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent.parent
INPUTS = [*(ROOT / 'files/macos').glob('*.c'), *(ROOT / 'files/macos').glob('*.h'),
          ROOT / 'files/ppd/HP-LaserJet_1020-Plus-hp1020zjs.ppd', ROOT / 'scripts/rebuild-runtime-from-vendor.sh',
          ROOT / 'assets/runtime/sihp1020.dl', *(ROOT / 'scripts/tests').glob('*'), Path(__file__)]
INPUTS += [ROOT / 'vendor/foo2zjs-source' / n for n in ('foo2zjs.c','zjs.h','jbig.c','jbig.h','jbig_ar.c','jbig_ar.h')]
SYSTEM_PATH = '/usr/bin:/bin:/usr/sbin:/sbin'
FLAGS = ['-O2', '-Wall', '-Wextra', '-Werror', '-Wno-deprecated-declarations', '-Wno-unused-function']

def run(args, ok=True, **kw):
    r = subprocess.run([str(a) for a in args], capture_output=True, timeout=60, **kw)
    if ok and r.returncode: raise AssertionError(f'{args}: {r.stderr.decode(errors="replace")[-6000:]}')
    return r

def wait_for(condition, timeout=8):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if condition(): return
        time.sleep(.02)
    raise AssertionError('Timed out waiting for fixture')

def chunks(data):
    pos = data.index(b'JZJZ') + 4
    pages, metadata, bodies, current = [], [], [], bytearray()
    while pos + 16 <= len(data):
        size, kind, count, _, sig = struct.unpack_from('>IIIHH', data, pos)
        assert size >= 16 and pos + size <= len(data) and sig == 0x5a5a
        bodies.append(data[pos:pos+size])
        if kind == 2:
            current = bytearray()
            values, cursor = {}, pos + 16
            for _ in range(count):
                length, ident, typ, _ = struct.unpack_from('>IHBB', data, cursor)
                assert length >= 8 and cursor + length <= pos + size
                if typ == 1: values[ident] = struct.unpack_from('>I', data, cursor+8)[0]
                cursor += length
            metadata.append(values)
        if kind == 5: current.extend(data[pos+16:pos+size])
        if kind == 3: pages.append(hashlib.sha256(current).hexdigest())
        pos += size
        if kind == 1: break
    assert len(pages) == len(metadata) > 0
    return pages, metadata, bodies

def make_pdf(path, pages=3):
    # Small, deterministic PDF fixture; no third-party rendering dependency.
    objects = [b'<< /Type /Catalog /Pages 2 0 R >>', b'']
    kids = []
    for i in range(pages):
        page = len(objects) + 1
        kids.append(f'{page} 0 R')
        objects.append(f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595.2 841.92] /Resources << >> /Contents {page+1} 0 R >>'.encode())
        draw = f'0 g {72+i*50} 500 {20+i*10} 20 re f\n'.encode()
        objects.append(f'<< /Length {len(draw)} >>\nstream\n'.encode()+draw+b'endstream')
    objects[1] = f'<< /Type /Pages /Count {pages} /Kids [{" ".join(kids)}] >>'.encode()
    data, offsets = bytearray(b'%PDF-1.4\n'), [0]
    for i, obj in enumerate(objects, 1):
        offsets.append(len(data)); data.extend(f'{i} 0 obj\n'.encode()+obj+b'\nendobj\n')
    start=len(data)
    data.extend(f'xref\n0 {len(offsets)}\n0000000000 65535 f \n'.encode())
    for offset in offsets[1:]: data.extend(f'{offset:010d} 00000 n \n'.encode())
    data.extend(f'trailer << /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n'.encode())
    path.write_bytes(data)

MOCK_USB = (ROOT / "scripts/tests/hp1020-usb-fixture.py.in").read_text()

class Fixture:
    def __init__(self, parent, name, mode='ok', loaded=True, usb=None):
        self.area = parent / name
        self.area.mkdir()
        (self.area / 'device.json').write_text(json.dumps({'mode': mode, 'loaded': loaded}))
        self.usb = usb or self.area / 'usb'
        if usb is None:
            self.usb.write_text(MOCK_USB.replace('PYTHON', sys.executable, 1).replace('AREA', repr(str(self.area)), 1))
            self.usb.chmod(0o755)
        self.backend = self.area / 'backend'
        run(['clang', *FLAGS, f'-DHP1020_BASE={json.dumps(str(parent))}', f'-DHP1020_USB={json.dumps(str(self.usb))}',
             '-DHP1020_CONNECT_TIMEOUT=0.5', '-DHP1020_TRANSFER_TIMEOUT=0.5', '-DHP1020_CLOSE_TIMEOUT=0.5',
             '-DHP1020_STATUS_GRACE=0.2', '-DHP1020_PROGRESS_TIMEOUT=2', ROOT / 'files/macos/hp1020-backend.c', '-lcups', '-o', self.backend])
        self.processes = []
    def events(self):
        file=self.area/'events'
        return [json.loads(line) for line in file.read_text().splitlines()] if file.exists() else []
    def job(self, data, opts='PageSize=A4', stdin=False, uri=None):
        document = self.area / 'document.zjs'; document.write_bytes(data)
        log = self.area / f'job-{len(self.processes)}.log'
        env={'PATH': SYSTEM_PATH, 'TMPDIR': str(self.area), 'DEVICE_URI': uri or 'hp1020://Hewlett-Packard/HP%20LaserJet%201020?serial=OFFLINE', 'LC_ALL': 'C'}
        args=[self.backend, '1', 'fixture', 'test', '1', opts]
        if not stdin: args.append(document)
        with log.open('wb') as output:
            p=subprocess.Popen([str(a) for a in args], stdin=subprocess.PIPE if stdin else subprocess.DEVNULL,
                               stdout=subprocess.DEVNULL, stderr=output, env=env, start_new_session=True)
        self.processes.append(p)
        if stdin and data: p.stdin.write(data); p.stdin.close()
        return p, log
    def completed(self, process, expected=0):
        assert process.wait(timeout=8)==expected, (self.area, list(self.area.glob('job-*.log'))[-1].read_text())
    def close(self):
        for p in self.processes:
            if p.poll() is None:
                try: os.killpg(p.pid, signal.SIGKILL)
                except ProcessLookupError: pass
            p.wait()


def main():
    checks, conversions, fixtures = [], [], []
    def passed(name): checks.append(name); print('PASS:', name, flush=True)
    with tempfile.TemporaryDirectory(prefix='hp1020-native-check-') as temp:
        area = Path(temp); runtime = area / 'runtime'
        run(['zsh', ROOT / 'scripts/rebuild-runtime-from-vendor.sh', runtime])
        ppd = area / 'printer.ppd'
        ppd.write_text((ROOT / 'files/ppd/HP-LaserJet_1020-Plus-hp1020zjs.ppd').read_text().replace('/Library/Printers/hp1020', str(area)))
        run(['cupstestppd', '-q', '-I', 'filters', ppd])  # Test binaries are intentionally user-owned.
        for name in ('hp1020', 'rastertohp1020'):
            run(['codesign', '--verify', '--strict', runtime/name])
            assert run(['lipo', '-archs', runtime/name]).stdout.strip()==b'arm64'
            libs=run(['otool', '-L', runtime/name]).stdout.decode()
            assert '/opt/' not in libs and '/usr/local/' not in libs
        passed('native arm64 components link only macOS libraries; PPD validates')
        pdf=area/'pages.pdf'; make_pdf(pdf)
        ps=area/'pages.ps'; ps.write_text('%!PS-Adobe-3.0\n%%Pages: 3\n'+''.join(f'%%Page: {i+1} {i+1}\n0 setgray {72+i*50} 500 {20+i*10} 20 rectfill showpage\n' for i in range(3))+'%%EOF\n')
        def prepared(copies=1, options=(), document=pdf, ok=True):
            options = ['PageSize=A4', *options]
            args=['/usr/sbin/cupsfilter', '-p', ppd, '-d', 'offline', '-e', '-i', 'application/pdf' if document.suffix=='.pdf' else 'application/postscript', '-m', 'printer/offline', '-n', str(copies)]
            for option in options: args += ['-o', option]
            return run([*args, document], ok=ok, env=dict(os.environ, PATH=SYSTEM_PATH, TMPDIR=str(area))).stdout
        def fixture(name, **kwargs):
            f=Fixture(area, name, **kwargs); fixtures.append(f); return f
        try:
            baseline = None
            default = None
            for name, copies, options, expected, indices, document in [
                ('baseline',1,[],3,[0,1,2],pdf),
                ('four-copies',4,['Collate=True'],12,[0,1,2]*4,pdf),
                ('queue-copy-default',3,['multiple-document-handling=separate-documents-collated-copies'],9,[0,1,2]*3,pdf),
                ('uncollated',3,['Collate=False','multiple-document-handling=separate-documents-uncollated-copies'],9,[0]*3+[1]*3+[2]*3,pdf),
                ('page-range',2,['page-ranges=2-3','Collate=True'],4,[1,2]*2,pdf),
                ('reverse',1,['outputorder=reverse'],3,[2,1,0],pdf),
                ('odd-pages',1,['page-set=odd'],2,[0,2],pdf),
                ('even-pages',1,['page-set=even'],1,[1],pdf),
                ('landscape',1,['orientation-requested=4'],3,None,pdf),
                ('two-up',1,['number-up=2'],2,None,pdf),
                ('letter',2,['PageSize=Letter','Collate=True'],6,None,pdf)]:
                data=prepared(copies,options,document)
                hashes,metadata,_=chunks(data)
                if baseline is None: baseline=hashes; default=data
                assert len(hashes)==expected,(name,len(hashes),expected)
                if indices is not None: assert hashes==[baseline[i] for i in indices],name
                if name=='postscript-copies': assert hashes[:3]==hashes[3:]
                assert all(v[4]==1 and v[3]==(1 if name=='letter' else 9) for v in metadata)
                f=fixture(name); p,log=f.job(data,opts='PageSize=Letter' if name=='letter' else 'PageSize=A4'); f.completed(p)
                sent=next(f.area.glob('sent-*.zjs')).read_bytes()
                assert chunks(sent)[2]==chunks(data)[2]
                assert 'Printer confirmed all pages' in log.read_text()
                assert not any(e['kind']=='firmware' for e in f.events())
                conversions.append({'case':name,'rendered_pages':len(hashes),'chunk_sha256':hashlib.sha256(b''.join(chunks(data)[2])).hexdigest()})
                passed(name+': real native filter chain and captured transport preserve pages, order, paper and single encoder copies')
                f.close()
            f=fixture('stdin'); p,log=f.job(default,stdin=True); f.completed(p)
            passed('CUPS stdin delivery preserves the complete job')
            f=fixture('partial-input'); p,log=f.job(b'',stdin=True)
            p.stdin.write(default[:40]); p.stdin.flush(); wait_for(lambda:'Preparing the document.' in log.read_text()); p.terminate(); f.completed(p); p.stdin.close()
            assert not f.events() and not list(f.area.glob('cups*'))
            passed('cancel during filter input performs no USB access and leaves no document temporary files')
            f=fixture('paper',mode='paper'); p,log=f.job(default)
            wait_for(lambda:'STATE: +media-empty-error' in log.read_text()); assert p.poll() is None
            (f.area/'release').touch(); f.completed(p)
            assert 'STATE: -media-empty-error' in log.read_text()
            passed('paper-out retains the active job until a valid clear and matching completion')
            for mode in ('unplug','stall','no-id'):
                f=fixture(mode,mode=mode); p,log=f.job(default); f.completed(p,3)
                assert sum(e['kind']=='open' for e in f.events())==1
                passed(mode+': hold without automatic replay')
            f=fixture('reconnect',mode='reconnect'); p,log=f.job(default)
            wait_for(lambda:'STATE: +connecting-to-device' in log.read_text()); time.sleep(.7); assert p.poll() is None
            (f.area/'connected').touch(); f.completed(p)
            passed('unplugged printer waits for reconnection without resubmission')
            f=fixture('silent',mode='silent'); p,log=f.job(default); f.completed(p)
            assert 'not confirmed physical completion' in log.read_text() and 'confirmed all pages' not in log.read_text()
            passed('missing device feedback reports transmission with unconfirmed physical completion')
            for mode,expected in [('ok',0),('bad-firmware',3)]:
                f=fixture('firmware-'+mode,mode=mode,loaded=False); p,log=f.job(default); f.completed(p,expected)
                assert sum(e['kind']=='firmware' for e in f.events())==1
                if expected: assert not list(f.area.glob('sent-*.zjs'))
                else:
                    p,log=f.job(default); f.completed(p)
                    assert sum(e['kind']=='firmware' for e in f.events())==1
                passed('firmware-'+mode+': load only when absent and require new FWVER before printing')
            for mode in ('paper','stubborn'):
                f=fixture('cancel-'+mode,mode=mode); p,log=f.job(default)
                wait_for(lambda:'STATE: +media-empty-error' in log.read_text())
                pid=next(e['pid'] for e in f.events() if e['kind']=='open')
                p.terminate(); f.completed(p)
                assert any(e['kind']=='reset' for e in f.events())
                try: os.kill(pid,0)
                except ProcessLookupError: pass
                else: raise AssertionError('USB child survived')
                assert not list(f.area.glob('cups*'))
                passed('cancel-'+mode+': standard reset requested, child reaped, anonymous documents released')
            for name,data,opts,uri in [
                ('raw',pdf.read_bytes(),'PageSize=A4',None),
                ('truncated',default[:-50],'PageSize=A4',None),
                ('bad-chunk',default.replace(b'JZJZ',b'JZJZ\x00\x00\x00\x01',1),'PageSize=A4',None),
                ('paper-size',default,'PageSize=A5',None),
                ('duplex',default,'sides=two-sided-long-edge',None),
                ('wrong-device',default,'','hp1020://different-device')]:
                f=fixture('reject-'+name); p,log=f.job(data,opts=opts,uri=uri); f.completed(p,3); assert not f.events()
                passed(name+': reject before USB or firmware')
            wire=area/'wire.c'; binary=area/'wire'
            wire.write_text('#include <cups/sidechannel.h>\n#include <unistd.h>\n#include <string.h>\nint main(void){char b[32768];int n=sizeof(b);cups_sc_command_t c;cups_sc_status_t s;if(cupsSideChannelRead(&c,&s,b,&n,3)||c!=CUPS_SC_CMD_GET_DEVICE_ID||n)return 10;const char *id="MFG:Hewlett-Packard;MDL:HP LaserJet 1020;FWVER:fixture;";if(cupsSideChannelWrite(c,CUPS_SC_STATUS_OK,id,strlen(id),3))return 11;while(read(0,b,sizeof(b))>0){}return 0;}\n')
            run(['clang','-Wno-deprecated-declarations',wire,'-lcups','-o',binary])
            f=fixture('libcups-codec',usb=binary); p,log=f.job(default); f.completed(p)
            passed('native descriptor mapping and side-channel frames interoperate with independent system libcups')
            # Native macOS no longer converts PostScript: reject explicitly.
            # Truncated raster must never produce a valid end.
            bad=area/'bad.ps'; bad.write_text('%!PS\nundefined_HP1020_operator\n')
            assert b'JZJZ' not in prepared(document=bad,ok=False)
            ras=run(['/usr/sbin/cupsfilter','-p',ppd,'-i','application/pdf','-m','application/vnd.cups-raster','-o','PageSize=A4',pdf]).stdout
            r=run([runtime/'rastertohp1020','1','fixture','test','1','PageSize=A4'],input=ras[:-5000],ok=False)
            assert r.returncode and not r.stdout.endswith(b'@PJL EOJ\n\x1b%-12345X')
            passed('invalid PostScript and truncated raster cannot produce complete printer jobs')
            # Independent libcups extraction compared with the unchanged CLI.
            reader_bin=area/'raster-reader'
            run(['clang','-Wno-deprecated-declarations',ROOT/'scripts/tests/hp1020-raster-read.c','-lcups','-o',reader_bin])
            pbm=run([reader_bin],input=ras).stdout
            header,dimensions,pixels=pbm.split(b'\n',2)
            assert header==b'P4' and dimensions==b'9536 6824'
            width,height=map(int,dimensions.split());stride=width//8
            nonempty=[i for i in range(height) if any(pixels[i*stride:(i+1)*stride])]
            assert abs(nonempty[0]-2587)<=1 and abs(nonempty[-1]-2753)<=1, (nonempty[0],nonempty[-1])
            row=pixels[nonempty[len(nonempty)//2]*stride:][:stride]
            columns=[x for x in range(width) if row[x//8] & (128>>(x%8))]
            assert abs(columns[0]-1008)<=1 and abs(columns[-1]-1340)<=1, (columns[0],columns[-1])
            original=area/'original-foo2zjs';vendor=ROOT/'vendor/foo2zjs-source'
            run(['clang','-O2','-I',vendor,vendor/'foo2zjs.c',vendor/'jbig.c',vendor/'jbig_ar.c','-o',original])
            single_pdf=area/'single.pdf';make_pdf(single_pdf,1)
            actual=prepared(document=single_pdf)
            expected=run([original,'-P','-z1','-L0','-u0','-l0','-n1','-p9','-r1200x600'],input=pbm).stdout
            assert chunks(actual)[2]==chunks(expected)[2]
            passed('native page origin matches known PDF marks and every encoded chunk matches original foo2zjs')
            text_file=area/'direct.txt';text_file.write_text('HP LaserJet 1020 native text fixture\n')
            text_output=run(['/usr/sbin/cupsfilter','-p',ppd,'-d','offline','-e','-i','text/plain','-m','printer/offline','-o','PageSize=A4',text_file]).stdout
            assert len(chunks(text_output)[0])==1
            passed('plain-text files use the native Mac document path, including the test-page format')
            parser_bin=area/'parser'
            run(['clang',*FLAGS,ROOT/'scripts/tests/hp1020-status-test.c','-lcups','-o',parser_bin]);run([parser_bin])
            passed('fragmented, oversized, malformed, stale and wrong-page feedback cannot falsely finish jobs or clear errors')

        finally:
            for f in fixtures:f.close()
    report={'count':len(checks),'checks':checks,'conversions':conversions,
            'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in INPUTS},
            'host_macos':run(['sw_vers','-productVersion']).stdout.decode().strip(),
            'real_native_filters':True,'extra_rendering_packages':False,'usb_transport':'separate fd 3/4 mock process',
            'accelerated_test_timeouts':True,'cups_scheduler_and_gui':False,'actual_installation':False,
            'printer_contact':False,'physical_print_test':False,'device_status_compatibility':'not yet hardware verified'}
    (ROOT/'assets/macos-printing-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'Passed {len(checks)} offline native printing checks; no printer contact.')

if __name__=='__main__':main()
