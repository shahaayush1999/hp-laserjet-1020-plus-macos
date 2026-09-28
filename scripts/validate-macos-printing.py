#!/usr/bin/env python3
"""Exercise real macOS filters/encoder plus isolated backend/worker/mock USB.

No installed files, queue, USB devices, package managers or launchd jobs change.
The fake USB process uses the real fd-3/fd-4 interface and generated printer bytes.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import selectors
import shlex
import shutil
import signal
import struct
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent.parent
SERVICE = ROOT / 'files/macos/hp1020-service.py'
spec = importlib.util.spec_from_file_location('hpservice', SERVICE)
service = importlib.util.module_from_spec(spec)
spec.loader.exec_module(service)
INPUTS = [SERVICE, ROOT / 'files/macos/hp1020-usb-run.c', ROOT / 'files/cups/backend/hp1020queue',
          ROOT / 'files/cups/filter/hp1020passthrough', ROOT / 'files/ppd/HP-LaserJet_1020-Plus-hp1020zjs.ppd',
          ROOT / 'scripts/rebuild-runtime-from-vendor.sh', ROOT / 'assets/runtime/foo2zjs-wrapper',
          ROOT / 'assets/runtime/foo2zjs-pstops', ROOT / 'vendor/foo2zjs-source/foo2zjs.c', Path(__file__)]
INPUTS += [ROOT / 'vendor/foo2zjs-source' / name for name in ('zjs.h', 'jbig.c', 'jbig.h', 'jbig_ar.c', 'jbig_ar.h')]
INPUTS.append(ROOT / 'assets/runtime/sihp1020.dl')


def run(args, **kwargs):
    return subprocess.run([str(a) for a in args], check=True, capture_output=True, timeout=60, **kwargs)


def wait_for(condition, timeout=10):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if condition():
            return
        time.sleep(0.02)
    raise AssertionError('Timed out waiting for fixture state')


def chunks(data):
    pos = data.index(b'JZJZ') + 4
    pages, current, paper = [], None, []
    while pos + 16 <= len(data):
        size, kind, count, _, signature = struct.unpack_from('>IIIHH', data, pos)
        assert size >= 16 and signature == 0x5a5a and pos + size <= len(data)
        if kind == 2:
            current = bytearray()
            values, cursor = {}, pos + 16
            for _ in range(count):
                length, ident, typ, param = struct.unpack_from('>IHBB', data, cursor)
                if typ == 1:
                    values[ident] = struct.unpack_from('>I', data, cursor + 8)[0]
                cursor += length
            paper.append(values)
        if kind == 5:
            current.extend(data[pos + 16:pos + size])
        if kind == 3:
            pages.append(hashlib.sha256(current).hexdigest())
        pos += size
        if kind == 1:
            break
    assert len(pages) == len(paper)
    return pages, paper


MOCK_USB = r'''#!PYTHON
import json, os, pathlib, re, selectors, signal, socket, struct, sys, time
area = pathlib.Path(AREA)
state_file = area / 'device.json'
state = json.loads(state_file.read_text())
mode = state.get('mode', 'ok')
if mode == 'stubborn': signal.signal(signal.SIGTERM, signal.SIG_IGN)
def event(kind, **values):
    with (area / 'events').open('a') as log:
        log.write(json.dumps({'kind': kind, 'pid': os.getpid(), **values}) + '\n')
event('open', args=sys.argv[1:])
side = socket.socket(fileno=4)
selector = selectors.DefaultSelector()
selector.register(side, selectors.EVENT_READ, 'side')
selector.register(0, selectors.EVENT_READ, 'input')
buffer = bytearray()
cookie = None
completed = False
held = False
side_data = bytearray()
pending_ident = False
if mode == 'reconnect': os.write(2, b'STATE: +connecting-to-device\n')
def identify():
    ident = b'MFG:Hewlett-Packard;MDL:HP LaserJet 1020;'
    if state.get('loaded', True): ident += b'FWVER:20050309;'
    side.sendall(struct.pack('>BBH', 4, 1, len(ident)) + ident)
    os.write(2, b'STATE: -connecting-to-device\n')
    event('identified')
def response(text):
    raw = (text + '\r\n\x0c').encode()
    # Deliberately fragment every response across reads.
    for off in range(0, len(raw), 7): os.write(3, raw[off:off + 7])
def end_job():
    global completed
    pos = buffer.index(b'JZJZ') + 4
    pages = 0
    while pos + 16 <= len(buffer):
        size, kind = struct.unpack_from('>II', buffer, pos)
        if kind == 2: pages += 1
        pos += size
        if kind == 1: break
    if mode != 'silent':
        response('@PJL INFO STATUS\r\nCODE=10023\r\nONLINE=TRUE')
        response('@PJL USTATUS PAGE\r\n' + str(pages))
        response('@PJL USTATUS JOB\r\nEND\r\nNAME="' + cookie + '"\r\nPAGES=' + str(pages))
    completed = True
    event('end', pages=pages)
while True:
    if pending_ident and (area / 'connected').exists():
        identify()
        pending_ident = False
    if held and (area / 'release').exists():
        held = False
        end_job()
    for key, _ in selector.select(0.05):
        if key.data == 'side':
            raw = side.recv(8192)
            if not raw: sys.exit(0)
            side_data.extend(raw)
            if len(side_data) >= 4:
                cmd, status, length = struct.unpack('>BBH', side_data[:4])
                assert cmd in (1, 4) and status == 0 and length == 0
                side_data.clear()
                if cmd == 1:
                    side.sendall(struct.pack('>BBH', 1, 1, 0))
                    event('reset')
                    continue
                if mode == 'reconnect': pending_ident = True
                elif mode == 'no-id': os.write(2, b'STATE: -connecting-to-device\n')
                else: identify()
        else:
            if mode == 'stall':
                time.sleep(0.05)
                continue
            data = os.read(0, 32768)
            if not data:
                if buffer and not buffer.startswith(b'\x1b%-12345X@PJL JOB NAME='):
                    state['loaded'] = mode != 'bad-firmware'
                    state_file.write_text(json.dumps(state))
                    event('firmware', bytes=len(buffer))
                elif buffer:
                    (area / ('sent-' + str(os.getpid()) + '.zjs')).write_bytes(buffer)
                    event('document', bytes=len(buffer))
                event('closed')
                sys.exit(0)
            if mode == 'unplug':
                event('disconnected')
                sys.exit(7)
            buffer.extend(data)
            if buffer.startswith(b'\x1b%-12345X@PJL JOB NAME=') and cookie is None:
                found = re.search(rb'@PJL JOB NAME="([a-z0-9-]+)"', buffer)
                assert found
                cookie = found[1].decode()
                if mode != 'silent':
                    response('@PJL USTATUS JOB\r\nSTART\r\nNAME="' + cookie + '"')
            if cookie and not completed and not held and buffer.endswith(b'\x1b%-12345X') and b'@PJL EOJ NAME=' in buffer:
                event('received')
                if mode in ('paper', 'slow', 'stubborn'):
                    held = True
                    if mode in ('paper', 'stubborn'): response('@PJL USTATUS DEVICE\r\nCODE=41001\r\nONLINE=FALSE')
                else:
                    end_job()
'''


class Fixture:
    def __init__(self, parent, name, runtime, mode='ok', loaded=True):
        self.area = parent / name
        self.base, self.queue = self.area / 'base', self.area / 'queue'
        self.queue.mkdir(parents=True)
        self.base.mkdir()
        (self.base / 'runtime').symlink_to(runtime, target_is_directory=True)
        (self.area / 'device.json').write_text(json.dumps({'mode': mode, 'loaded': loaded}))
        self.usb = self.area / 'usb'
        self.usb.write_text(MOCK_USB.replace('PYTHON', sys.executable, 1).replace('AREA', repr(str(self.area)), 1))
        self.usb.chmod(0o755)
        self.backend = self.area / 'backend'
        self.backend.write_text((ROOT / 'files/cups/backend/hp1020queue').read_text().replace(str(service.QUEUE), str(self.queue)))
        self.processes = []
        self.worker_process = None

    def events(self):
        f = self.area / 'events'
        return [json.loads(line) for line in f.read_text().splitlines()] if f.exists() else []

    def worker(self):
        code = f'''import importlib.util, logging, signal
logging.basicConfig(level=logging.INFO)
s=importlib.util.spec_from_file_location('service',{str(SERVICE)!r}); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
c=m.Config({str(self.base)!r}, '/opt/homebrew', 'usb://Hewlett-Packard/HP%20LaserJet%201020?serial=OFFLINE', {str(self.queue)!r}, {str(self.usb)!r})
c.connect_timeout=1; c.close_timeout=0.5; c.transfer_timeout=0.5; c.status_grace=0.2; c.progress_timeout=2

def stop(*a): m.STOPPING=True
signal.signal(signal.SIGTERM,stop)
m.worker(c)
'''
        error = open(self.area / f'worker-{len(self.processes)}.log', 'wb')
        p = subprocess.Popen([sys.executable, '-I', '-c', code], stdout=error, stderr=error, start_new_session=True)
        error.close()
        self.processes.append(p)
        self.worker_process = p
        return p

    def job(self, data, copies=1, opts='PageSize=A4', job_id=1, stdin=False):
        document = self.area / f'input-{job_id}.dat'
        document.write_bytes(data)
        output = self.area / f'job-{job_id}.log'
        with output.open('wb') as log:
            args = ['/bin/zsh', str(self.backend), str(job_id), 'fixture', "Dad's $(touch UNEXPECTED)\nfile", str(copies), opts]
            p = subprocess.Popen(args if stdin else args + [str(document)], stdout=log, stderr=log,
                                 stdin=subprocess.PIPE if stdin else subprocess.DEVNULL, start_new_session=True)
        if stdin:
            p.stdin.write(data)
            p.stdin.close()
        self.processes.append(p)
        return p, output

    def completed(self, p, expected=0, timeout=15):
        result = p.wait(timeout=timeout)
        if result != expected:
            raise AssertionError(f'{self.area.name}: exit {result}, expected {expected}; logs ' +
                                 '\n'.join(f.read_text() for f in self.area.glob('*.log')))

    def close(self):
        for p in reversed(self.processes):
            if p.poll() is None:
                os.killpg(p.pid, signal.SIGTERM)
                try: p.wait(timeout=4)
                except subprocess.TimeoutExpired:
                    os.killpg(p.pid, signal.SIGKILL)
                    p.wait()


class Recorder:
    def __init__(self): self.messages = []
    def send(self, message): self.messages.append(message)
    def info(self, message): self.send('INFO: ' + service.clean_message(message))
    def tick(self): pass


def main():
    checks, conversions, fixtures = [], [], []
    def passed(name):
        checks.append(name)
        print('PASS:', name, flush=True)
    with tempfile.TemporaryDirectory(prefix='hp1020-printing-check-') as folder:
        area = Path(folder)
        runtime = area / 'runtime'
        try:
            run(['/bin/zsh', ROOT / 'scripts/rebuild-runtime-from-vendor.sh', runtime])
            ppd = ROOT / 'files/ppd/HP-LaserJet_1020-Plus-hp1020zjs.ppd'
            run(['cupstestppd', '-q', ppd])
            # Exercise the system CUPS library as the independent wire codec.
            wire_source, wire_binary = area / 'wire.c', area / 'wire'
            wire_source.write_text('''#include <cups/cups.h>
#include <cups/sidechannel.h>
#include <string.h>
#include <unistd.h>
int main(void) {
  char data[2048]; int length=sizeof(data); cups_sc_command_t cmd; cups_sc_status_t status;
  if (cupsSideChannelRead(&cmd,&status,data,&length,3.0) || cmd!=CUPS_SC_CMD_GET_DEVICE_ID || length) return 10;
  const char *id="MFG:Hewlett-Packard;MDL:HP LaserJet 1020;FWVER:fixture;";
  if (cupsSideChannelWrite(cmd,CUPS_SC_STATUS_OK,id,(int)strlen(id),3.0)) return 11;
  while (read(0,data,sizeof(data))>0) {}
  return 0;
}
''')
            run(['/usr/bin/clang', '-Wno-deprecated-declarations', wire_source, '-lcups', '-o', wire_binary])
            c = service.Config(area, '/opt/homebrew', 'usb://fixture', usb=wire_binary)
            r = Recorder()
            with service.Transport(c, r, 1, 'fixture', service.PJLStatus(r)) as usb:
                assert b'FWVER:fixture' in usb.device_id()
                usb.finish()
            passed('fd wiring and side-channel encoding interoperate with the system CUPS library')
            source = area / 'source.ps'
            source.write_text('%!PS-Adobe-3.0\n%%Pages: 3\n/Helvetica findfont 30 scalefont setfont\n' +
                              ''.join(f'%%Page: {i} {i}\n72 500 moveto (PAGE {i}) show showpage\n' for i in range(1, 4)) + '%%EOF\n')
            pdf = area / 'source.pdf'
            run(['/opt/homebrew/bin/gs', '-q', '-dBATCH', '-dNOPAUSE', '-sDEVICE=pdfwrite', f'-sOutputFile={pdf}', source])
            def prepared(copies=1, options=(), document=pdf):
                args = ['/usr/sbin/cupsfilter', '-p', ppd, '-i', 'application/pdf' if document.suffix == '.pdf' else 'application/postscript',
                        '-m', 'application/vnd.cups-postscript', '-n', str(copies)]
                for option in options: args += ['-o', option]
                ps = run([*args, document]).stdout
                capsule = run(['/bin/zsh', ROOT / 'files/cups/filter/hp1020passthrough', '1', 'fixture', 'test', str(copies), ' '.join(options)], input=ps).stdout
                assert capsule == service.MAGIC + ps
                return capsule
            def fixture(name, **kw):
                f = Fixture(area, name, runtime, **kw)
                fixtures.append(f)
                return f
            default = prepared()
            page_hashes = None
            for name, copies, options, expected, indices, doc in [
                    ('baseline', 1, [], 3, [0, 1, 2], pdf),
                    ('four-copies', 4, ['Collate=True'], 12, [0, 1, 2] * 4, pdf),
                    ('queue-copy-default', 3, ['multiple-document-handling=separate-documents-collated-copies'], 9, [0, 1, 2] * 3, pdf),
                    ('uncollated', 3, ['Collate=False', 'multiple-document-handling=separate-documents-uncollated-copies'], 9, [0] * 3 + [1] * 3 + [2] * 3, pdf),
                    ('postscript-copies', 2, ['Collate=True'], 6, [0, 1, 2] * 2, source),
                    ('page-range', 2, ['page-ranges=2-3', 'Collate=True'], 4, [1, 2] * 2, pdf),
                    ('reverse', 1, ['outputorder=reverse'], 3, [2, 1, 0], pdf),
                    ('odd-pages', 1, ['page-set=odd'], 2, [0, 2], pdf),
                    ('even-pages', 1, ['page-set=even'], 1, [1], pdf),
                    ('landscape', 1, ['orientation-requested=4'], 3, None, pdf),
                    ('two-up', 1, ['number-up=2'], 2, None, pdf),
                    ('letter', 2, ['PageSize=Letter', 'Collate=True'], 6, None, pdf)]:
                f = fixture(name)
                f.worker()
                p, log = f.job(prepared(copies, options, doc), copies, ' '.join(options))
                f.completed(p)
                wait_for(lambda: not list(f.queue.iterdir()))
                sent = list(f.area.glob('sent-*.zjs'))
                assert len(sent) == 1
                hashes, metadata = chunks(sent[0].read_bytes())
                assert len(hashes) == expected, (name, len(hashes), expected)
                if name == 'baseline': page_hashes = hashes
                if indices is not None and doc == pdf:
                    assert hashes == [page_hashes[i] for i in indices], name
                # ZJI_DMCOPIES=4 and ZJI_DMPAPER=3: inspect original header definitions below.
                assert all(values[4] == 1 for values in metadata), metadata
                assert all(values[3] == (1 if name == 'letter' else 9) for values in metadata), metadata
                assert 'Printer confirmed all pages' in log.read_text()
                assert not any(e['kind'] == 'firmware' for e in f.events())
                conversions.append({'case': name, 'rendered_pages': len(hashes), 'sha256': hashlib.sha256(sent[0].read_bytes()).hexdigest()})
                passed(name + ': native filters through worker and USB capture preserve selected pages/copies')
                f.close()

            f = fixture('stdin')
            f.worker()
            p, log = f.job(default, stdin=True)
            f.completed(p)
            assert chunks(next(f.area.glob('sent-*.zjs')).read_bytes())[0] == page_hashes
            passed('normal CUPS stdin delivery preserves every page')
            f.close()

            f = fixture('partial-capture')
            with (f.area / 'capture.log').open('wb') as log:
                p = subprocess.Popen(['/bin/zsh', str(f.backend), '1', 'fixture', 'partial', '1', ''],
                                     stdin=subprocess.PIPE, stdout=log, stderr=log, start_new_session=True)
            f.processes.append(p)
            p.stdin.write(service.MAGIC + b'%!PS\n')
            p.stdin.flush()
            wait_for(lambda: bool(list(f.queue.glob('.incoming.*'))))
            p.terminate()
            f.completed(p)
            p.stdin.close()
            assert not list(f.queue.iterdir()) and not f.events()
            passed('cancellation during stdin capture terminates the copy process and removes partial data')
            f.close()

            f = fixture('paper', mode='paper')
            f.worker()
            p, log = f.job(default)
            wait_for(lambda: 'STATE: +media-empty-error' in log.read_text())
            assert p.poll() is None
            (f.area / 'release').touch()
            f.completed(p)
            assert 'STATE: -media-empty-error' in log.read_text()
            passed('out-of-paper keeps job active, reports alert, clears on real status and waits for completion')
            f.close()

            for mode in ('unplug', 'stall', 'no-id'):
                f = fixture(mode, mode=mode)
                f.worker()
                p, log = f.job(default)
                f.completed(p, 3)
                assert 'RESULT 0' not in log.read_text()
                assert sum(e['kind'] == 'open' for e in f.events()) == 1
                passed(mode + ': failure holds the job without automatic replay')
                f.close()

            f = fixture('reconnect', mode='reconnect')
            f.worker()
            p, log = f.job(default)
            wait_for(lambda: 'STATE: +connecting-to-device' in log.read_text())
            time.sleep(1.3)  # Longer than the fixture's connected-device deadline.
            assert p.poll() is None and not list(f.area.glob('sent-*.zjs'))
            (f.area / 'connected').touch()
            f.completed(p)
            assert len(list(f.area.glob('sent-*.zjs'))) == 1
            passed('disconnected printer stays queued and continues on reconnection without resubmission')
            f.close()

            f = fixture('silent', mode='silent')
            f.worker()
            p, log = f.job(default)
            f.completed(p)
            assert 'not confirmed physical completion' in log.read_text()
            assert 'confirmed all pages' not in log.read_text()
            passed('missing feedback is explicitly unconfirmed, never presented as physical completion')
            f.close()

            for loaded_mode, expected in [('ok', 0), ('bad-firmware', 3)]:
                f = fixture('firmware-' + loaded_mode, mode=loaded_mode, loaded=False)
                f.worker()
                p, log = f.job(default)
                f.completed(p, expected)
                assert sum(e['kind'] == 'firmware' for e in f.events()) == 1
                if expected:
                    assert not list(f.area.glob('sent-*.zjs'))
                else:
                    p, _ = f.job(default, job_id=2)
                    f.completed(p)
                    assert sum(e['kind'] == 'firmware' for e in f.events()) == 1
                passed('firmware-' + loaded_mode + ': load only if missing; require FWVER before document transfer')
                f.close()

            for cancel_signal, mode in ((signal.SIGTERM, 'paper'), (signal.SIGKILL, 'paper'), (signal.SIGTERM, 'stubborn')):
                f = fixture('cancel-' + str(cancel_signal) + mode, mode=mode)
                f.worker()
                p, log = f.job(default)
                wait_for(lambda: 'STATE: +media-empty-error' in log.read_text())
                usb_pid = next(e['pid'] for e in f.events() if e['kind'] == 'open')
                p.send_signal(cancel_signal)
                p.wait(timeout=5)
                wait_for(lambda: not list(f.queue.iterdir()))
                try: os.kill(usb_pid, 0)
                except ProcessLookupError: pass
                else: raise AssertionError('USB process survived cancellation')
                assert any(e['kind'] == 'reset' for e in f.events()), (f.events(), (f.area / 'worker-0.log').read_text())
                passed(f'cancel {cancel_signal}/{mode}: reset requested, USB group killed and private documents removed')
                f.close()

            f = fixture('queued-cancel')
            p, log = f.job(default)
            wait_for(lambda: bool(list(f.queue.glob('job-*'))))
            p.terminate()
            p.wait(timeout=5)
            f.worker()
            wait_for(lambda: not list(f.queue.iterdir()))
            assert not f.events()
            passed('queued cancellation performs no USB operation')
            f.close()

            f = fixture('cancel-render')
            (f.base / 'runtime').unlink()
            (f.base / 'runtime').mkdir()
            for name in ('foo2zjs', 'foo2zjs-pstops', 'hp1020-usb-run'):
                (f.base / 'runtime' / name).symlink_to(runtime / name)
            child_pid = f.area / 'render-child'
            wrapper = f.base / 'runtime/foo2zjs-wrapper'
            wrapper.write_text('#!/bin/sh\nsleep 30 &\necho $! > ' + shlex.quote(str(child_pid)) + '\nwait\n')
            wrapper.chmod(0o755)
            f.worker()
            p, log = f.job(default)
            wait_for(child_pid.exists)
            pid = int(child_pid.read_text())
            p.terminate()
            p.wait(timeout=5)
            wait_for(lambda: not list(f.queue.iterdir()))
            try: os.kill(pid, 0)
            except ProcessLookupError: pass
            else: raise AssertionError('Renderer child survived cancellation')
            assert not f.events()
            passed('cancellation during conversion kills pipeline descendants before any USB contact')
            f.close()

            f = fixture('restart', mode='paper')
            old = f.worker()
            p, log = f.job(default)
            wait_for(lambda: 'STATE: +media-empty-error' in log.read_text())
            assert list((f.base / 'state/work').glob('job-*'))
            old.kill()
            old.wait()
            f.worker()
            f.completed(p, 3)
            assert sum(e['kind'] == 'open' for e in f.events()) == 1
            assert not list((f.base / 'state/work').glob('job-*'))
            passed('worker crash/restart removes temporary documents and holds started jobs without replay')
            f.close()

            f = fixture('five-jobs')
            f.worker()
            jobs = [f.job(default, job_id=i)[0] for i in range(1, 6)]
            for p in jobs: f.completed(p)
            assert len(list(f.area.glob('sent-*.zjs'))) == 5
            live = 0
            for e in f.events():
                if e['kind'] == 'open': live += 1; assert live == 1
                if e['kind'] == 'closed': live -= 1
            assert live == 0
            second = f.worker()
            assert second.wait(timeout=4) == 0
            passed('five jobs serialize; a second worker cannot steal the active worker lock')
            f.close()

            for name, data, opts in [('raw', pdf.read_bytes(), ''), ('paper-size', default, 'PageSize=A5'),
                                     ('duplex', default, 'sides=two-sided-long-edge'),
                                     ('conversion', service.MAGIC + b'%!PS\nundefined_HP1020_operator\n', '')]:
                f = fixture('reject-' + name)
                f.worker()
                p, log = f.job(data, opts=opts)
                f.completed(p, 3)
                assert not f.events()
                passed(name + ': reject before firmware or document transfer')
                f.close()

            f = fixture('symlink')
            p, log = f.job(default)
            wait_for(lambda: bool(list(f.queue.glob('job-*'))))
            job = next(f.queue.glob('job-*'))
            victim = area / 'unchanged-private-file'
            victim.write_bytes(default)
            (job / 'document').unlink()
            (job / 'document').symlink_to(victim)
            f.worker()
            f.completed(p, 3)
            assert victim.read_bytes() == default and not f.events()
            passed('symlinked input rejected without reading outside the spool or changing its target')
            f.close()

            recorder = Recorder()
            state = service.PJLStatus(recorder, 'current-job', 3)
            for code, reason in [(41001, 'media-empty-error'), (40021, 'cover-open-error'),
                                 (40022, 'media-jam-error'), (40600, 'toner-empty-error')]:
                frame = f'@PJL USTATUS DEVICE\r\nCODE={code}\r\nDISPLAY="fixture"\r\n\x0c'.encode()
                for byte in frame: state.feed(bytes([byte]))
                assert reason in state.reasons
            state.feed(b'@PJL USTATUS DEVICE\nCODE=malformed\n\x0c')
            assert 'toner-empty-error' in state.reasons
            state.feed(b'@PJL USTATUS JOB\nEND\nNAME="old-job"\nPAGES=3\n\x0c')
            state.feed(b'@PJL USTATUS JOB\nEND\nNAME="current-job"\nPAGES=2\n\x0c')
            assert not state.completed
            state.feed(b'@PJL INFO STATUS\nCODE=10001\n\x0c')
            assert not state.reasons
            state.feed(b'@PJL USTATUS JOB\nEND\nNAME="current-job"\nPAGES=3\n\x0c')
            assert state.completed
            state.feed(b'x' * 1000000)
            assert len(state.buffer) <= 16384
            passed('fragmented/malformed/stale status cannot fake completion or clear actual attention reasons')

            f = fixture('orphan')
            orphan = f.queue / '.incoming.orphan'
            orphan.mkdir()
            (orphan / 'document').write_text('abandoned confidential fixture')
            os.utime(orphan, (0, 0))
            active = f.queue / '.incoming.active'
            active.mkdir()
            (active / 'owner').write_text(str(os.getpid()))
            os.utime(active, (0, 0))
            c = service.Config(f.base, '/opt/homebrew', 'usb://fixture', queue=f.queue, usb=f.usb)
            service.clean_incoming(c)
            assert not orphan.exists() and active.exists()
            passed('abandoned incoming data is removed while live captures are preserved')

            f = fixture('worker-absent')
            p, log = f.job(default)
            f.completed(p, 3, timeout=70)  # Production 60-second timeout, not accelerated.
            assert 'worker stopped responding' in log.read_text()
            f.worker()
            wait_for(lambda: not list(f.queue.iterdir()))
            assert not f.events()
            passed('missing worker holds after the real timeout; later startup cannot print abandoned work')
            f.close()
            assert not (ROOT / 'UNEXPECTED').exists()
        finally:
            for f in fixtures: f.close()
    report = {'count': len(checks), 'checks': checks, 'conversions': conversions,
              'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in INPUTS},
              'real_macos_filters': True, 'real_ghostscript_and_encoder': True,
              'host_macos': run(['/usr/bin/sw_vers', '-productVersion']).stdout.decode().strip(),
              'ghostscript_version': run(['/opt/homebrew/bin/gs', '--version']).stdout.decode().strip(),
              'python_version': sys.version,
              'cups_scheduler_and_gui': False, 'usb_transport': 'simulated with real fd 3/4 wiring',
              'accelerated_worker_timeouts': True, 'actual_installation': False, 'printer_contact': False,
              'physical_print_test': False, 'device_status_compatibility': 'not yet hardware-verified'}
    (ROOT / 'assets/macos-printing-validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f'Passed {len(checks)} offline printing checks. No printer contact or installed changes.')


if __name__ == '__main__': main()
