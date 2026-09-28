#!/usr/bin/env python3
"""CUPS job worker. No USB discovery; the installer supplies one exact URI.

Only worker mode contacts the configured printer. The CUPS backend stays alive
on a private reply FIFO; losing that reader cancels the process group. Documents
are rendered as _lp, never root. Tests import this module with isolated paths and
a fake USB backend; there are no environment-based test bypasses in production.
"""
import argparse
import contextlib
import fcntl
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import re
import selectors
import shlex
import shutil
import signal
import socket
import stat
import struct
import subprocess
import tempfile
import time
import uuid

QUEUE = Path('/private/var/spool/cups/tmp/hp1020queue')
USB_BACKEND = Path('/usr/libexec/cups/backend/usb')
MAGIC = b'HP1020-CUPS-PS-2\n'
SYSTEM_PATH = '/usr/bin:/bin:/usr/sbin:/sbin'
STOPPING = False


class Held(Exception):
    """Output may have occurred: hold, never automatically replay."""


class Cancelled(Exception):
    pass


def clean_message(value):
    return ''.join(c if 32 <= ord(c) < 127 else ' ' for c in str(value))[:700]


class Reporter:
    def __init__(self, fd, directory):
        self.fd, self.directory, self.last_ping = fd, directory, 0.0

    def send(self, message):
        packet = (message + '\n').encode('ascii', 'replace')
        if len(packet) > 2048:
            raise ValueError('Oversized worker message')
        try:
            if os.write(self.fd, packet) != len(packet):
                raise Cancelled('Reply reader stopped')
        except (BrokenPipeError, BlockingIOError):
            raise Cancelled('CUPS no longer owns this job') from None

    def info(self, message):
        self.send('INFO: ' + clean_message(message))

    def tick(self):
        if STOPPING:
            raise Held('Printer worker stopped. Check the printer before resuming this job.')
        try:
            os.stat('cancel', dir_fd=self.directory, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise Cancelled('Cancelled by CUPS')
        now = time.monotonic()
        if now - self.last_ping >= 1:
            self.send('HEARTBEAT')
            self.last_ping = now


def stop_process(process):
    # Kill the entire conversion/USB process group, including pipeline children.
    with contextlib.suppress(ProcessLookupError):
        os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        pass
    with contextlib.suppress(ProcessLookupError):
        os.killpg(process.pid, signal.SIGKILL)
    process.wait()


def safe_open(directory, name, flags=os.O_RDONLY, kind=stat.S_ISREG):
    fd = os.open(name, flags | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    st = os.fstat(fd)
    if not kind(st.st_mode) or st.st_nlink != 1:
        os.close(fd)
        raise Held('Invalid spool file. Job held.')
    return fd


def ticket_options(raw):
    # CUPS uses shell-like quoting for option values. We only consume paper and
    # unsupported hardware settings; Apple's filters have already applied layout.
    try:
        return {key.lower(): value for item in shlex.split(raw)
                for key, sep, value in [item.partition('=')] if sep}
    except ValueError as error:
        raise Held('Invalid print options.') from error


def paper_code(raw):
    options = ticket_options(raw)
    for key, allowed in [('sides', {'one-sided'}), ('duplex', {'none', 'false', 'off'}),
                         ('inputslot', {'auto', 'automatic'})]:
        if key in options and options[key].lower() not in allowed:
            raise Held('This printer supports single-sided printing from its normal paper tray.')
    name = options.get('pagesize', options.get('media', 'A4')).split(',')[0].lower()
    code = {'a4': 9, 'iso_a4_210x297mm': 9, 'letter': 1, 'na_letter_8.5x11in': 1}.get(name)
    if code is None:
        raise Held('Unsupported paper size. Choose A4 or US Letter.')
    return code


# Status meanings are documented by HP PJL and the preserved foo2zjs
# hplj10xx_gui.tcl code2str table. A parser match is not a physical device test.
STATUS = {
    10001: (set(), 'Printer ready.'),
    10002: ({'offline-report'}, 'Printer is offline.'),
    10003: (set(), 'Printer is warming up.'),
    10004: (set(), 'Printer is performing a self-test.'),
    10005: (set(), 'Printer is resetting.'),
    10006: ({'toner-low-warning'}, 'Printer reports low toner.'),
    10023: (set(), 'Printer is printing.'),
    30119: ({'media-jam-error'}, 'Paper jam. Clear the jam to continue.'),
    40021: ({'cover-open-error'}, 'Printer cover is open.'),
    40022: ({'media-jam-error'}, 'Paper jam. Clear the jam to continue.'),
    40038: ({'toner-low-warning'}, 'Printer reports low toner.'),
    40600: ({'toner-empty-error'}, 'Printer reports no toner cartridge.'),
}
MANAGED_REASONS = set().union(*(value[0] for value in STATUS.values()), {'media-empty-error'})


class PJLStatus:
    def __init__(self, report, token='', pages=0):
        self.report, self.token, self.pages = report, token, pages
        self.buffer = bytearray()
        self.reasons = set()
        self.started = self.completed = self.cancelled = False
        self.last_progress = time.monotonic()
        self.last_page = 0

    @property
    def attention(self):
        return any(r.endswith('-error') or r == 'offline-report' for r in self.reasons)

    def feed(self, data):
        self.buffer.extend(data)
        while b'\x0c' in self.buffer:
            frame, _, rest = self.buffer.partition(b'\x0c')
            self.buffer[:] = rest
            self.frame(bytes(frame))
        if len(self.buffer) > 16384:
            # Keep bounded state and resynchronize on the next complete header.
            self.buffer.clear()

    def frame(self, frame):
        text = frame.decode('ascii', 'replace').replace('\r', '')
        begin = text.rfind('@PJL ')
        if begin < 0 or len(text) > 16384:
            return
        lines = [line.strip() for line in text[begin:].split('\n') if line.strip()]
        header, body = lines[0], lines[1:]
        fields = dict(line.split('=', 1) for line in body if '=' in line)
        if header in ('@PJL INFO STATUS', '@PJL USTATUS DEVICE', '@PJL USTATUS TIMED'):
            raw = fields.get('CODE', '')
            if not re.fullmatch(r'[0-9]{5}', raw):
                return
            code = int(raw)
            known = STATUS.get(code)
            if 41000 <= code <= 41999:
                known = ({'media-empty-error'}, 'Out of paper. Add paper to continue.')
            if known is None:
                self.report.info('Printer reported status ' + raw + '. ' + fields.get('DISPLAY', '').strip('"'))
                return  # Unknown/malformed status must not clear a known error.
            reasons, message = known
            # Clear persisted CUPS reasons only after a valid device status.
            for reason in sorted(MANAGED_REASONS - reasons):
                self.report.send('STATE: -' + reason)
            for reason in sorted(reasons - self.reasons):
                self.report.send('STATE: +' + reason)
            if reasons != self.reasons or code == 10023:
                self.last_progress = time.monotonic()
            self.reasons = set(reasons)
            self.report.info(message)
        elif header == '@PJL USTATUS JOB' and self.token:
            if fields.get('NAME', '').strip('"') != self.token:
                return  # A previous/other job is never completion for this one.
            if 'START' in body:
                self.started = True
                self.last_progress = time.monotonic()
            elif 'CANCELED' in body:
                self.cancelled = True
            elif 'END' in body:
                raw = fields.get('PAGES', '')
                if raw.isdigit() and int(raw) == self.pages:
                    self.completed = True
                    self.last_progress = time.monotonic()
        elif header == '@PJL USTATUS PAGE' and self.started:
            if len(body) == 1 and body[0].isdigit():
                page = int(body[0])
                if self.last_page < page <= self.pages:
                    self.last_page = page
                    self.last_progress = time.monotonic()
                    self.report.info(f'Printer reports page {page} of {self.pages} printed.')


class Transport:
    """One system USB backend, with live back-channel and side-channel pipes."""
    def __init__(self, config, report, job_id, user, parser):
        self.config, self.report, self.parser = config, report, parser
        self.selector = selectors.DefaultSelector()
        self.log_buffer = bytearray()
        self.side_buffer = bytearray()
        self.replies = []
        self.connected_at = None
        back_read, back_write = os.pipe()
        self.side, child_side = socket.socketpair()
        args = [str(config.base / 'runtime/hp1020-usb-run'), str(back_write), str(child_side.fileno()),
                str(config.usb), str(job_id), user, 'HP LaserJet 1020 job', '1', '']
        try:
            self.process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                                            stderr=subprocess.PIPE, env=config.environment(),
                                            pass_fds=(back_write, child_side.fileno()), start_new_session=True)
        except BaseException:
            os.close(back_read)
            self.side.close()
            raise
        finally:
            os.close(back_write)
            child_side.close()
        self.back = os.fdopen(back_read, 'rb', buffering=0)
        for obj, tag in [(self.process.stderr, 'log'), (self.back, 'back'), (self.side, 'side')]:
            os.set_blocking(obj.fileno(), False)
            self.selector.register(obj, selectors.EVENT_READ, tag)
        os.set_blocking(self.process.stdin.fileno(), False)
        self.closed_input = False

    def pump(self, timeout=0.1):
        self.report.tick()
        for key, _ in self.selector.select(timeout):
            try:
                data = os.read(key.fd, 8192)
            except BlockingIOError:
                continue
            if not data:
                self.selector.unregister(key.fileobj)
                continue
            if key.data == 'back':
                self.parser.feed(data)
            elif key.data == 'side':
                self.side_buffer.extend(data)
                while len(self.side_buffer) >= 4:
                    cmd, result, length = struct.unpack('>BBH', self.side_buffer[:4])
                    if length > 8192:
                        raise Held('Invalid printer side-channel response.')
                    if len(self.side_buffer) < 4 + length:
                        break
                    self.replies.append((cmd, result, bytes(self.side_buffer[4:4 + length])))
                    del self.side_buffer[:4 + length]
            else:
                self.log_buffer.extend(data)
                while b'\n' in self.log_buffer:
                    line, _, rest = self.log_buffer.partition(b'\n')
                    self.log_buffer[:] = rest
                    line = line.decode('utf-8', 'replace')
                    # PAGE from USB means bytes sent, not sheets physically printed.
                    if line.startswith(('INFO:', 'ERROR:', 'WARNING:')):
                        self.report.send(clean_message(line))
                    elif line.startswith('STATE:') and re.fullmatch(r'STATE: [+-][a-z0-9, -]+', line):
                        self.report.send(line)
                        if line == 'STATE: -connecting-to-device':
                            self.connected_at = time.monotonic()
                if len(self.log_buffer) > 16384:
                    self.log_buffer.clear()
        if self.parser.cancelled:
            raise Held('The printer cancelled this job. Check it before resuming.')

    def device_id(self):
        self.side.sendall(struct.pack('>BBH', 4, 0, 0))  # CUPS GET_DEVICE_ID
        # While unplugged, the native backend waits for the selected device.
        # Keep the job queued and cancellable so reconnecting needs no resubmit.
        # Once connected, a missing side-channel response is a bounded failure.
        while True:
            self.pump()
            for cmd, result, payload in self.replies:
                if cmd == 4:
                    self.replies.clear()
                    if result != 1 or b'LaserJet 1020' not in payload:
                        raise Held('Could not identify the configured HP 1020. No document was sent.')
                    self.connected_at = self.connected_at or time.monotonic()
                    return payload
            if self.process.poll() is not None:
                break
            if self.connected_at is not None and time.monotonic() - self.connected_at >= self.config.connect_timeout:
                break
        raise Held('Printer did not connect. Check power and USB, then resume the job.')

    def send_file(self, document):
        last_write = time.monotonic()
        with open(document, 'rb') as data:
            block = data.read(32768)
            while block:
                self.pump(0.02)
                if self.process.poll() is not None:
                    raise Held('USB connection ended during transfer. Check the printer before resuming.')
                try:
                    count = os.write(self.process.stdin.fileno(), block)
                except BlockingIOError:
                    count = 0
                except BrokenPipeError:
                    raise Held('USB connection was lost. Check the printer before resuming.') from None
                if count:
                    last_write = time.monotonic()
                    block = block[count:] or data.read(32768)
                elif not self.parser.attention and time.monotonic() - last_write > self.config.transfer_timeout:
                    raise Held('Printer transfer stalled. Check the printer before resuming.')

    def finish(self, timeout=None):
        if not self.closed_input:
            self.process.stdin.close()
            self.closed_input = True
        deadline = time.monotonic() + (timeout or self.config.close_timeout)
        while self.process.poll() is None:
            self.pump()
            if time.monotonic() >= deadline:
                raise Held('USB transfer did not finish. Check the printer before resuming.')
        self.pump(0)
        if self.process.returncode:
            raise Held('USB transfer failed. Check the printer before resuming.')

    def wait_for_pages(self):
        started_wait = time.monotonic()
        while not self.parser.completed:
            self.pump()
            if self.process.poll() is not None:
                raise Held('USB connection closed before completion was checked.')
            if self.parser.attention:
                continue  # Keep paper/cover/jam conditions visible until resolved or cancelled.
            if not self.parser.started and time.monotonic() - started_wait >= self.config.status_grace:
                self.report.send('STATE: +com.hp1020.status-unavailable-warning')
                self.report.info('Document sent; the printer has not confirmed physical completion.')
                return
            if self.parser.started and time.monotonic() - self.parser.last_progress > self.config.progress_timeout:
                raise Held('Printer stopped reporting progress. Check it before resuming this job.')
        self.report.send('STATE: -com.hp1020.status-unavailable-warning')
        self.report.info('Printer confirmed all pages in this job.')

    def close(self):
        if self.process.poll() is None:
            stop_process(self.process)
        for obj in (self.process.stdin, self.process.stderr, self.back, self.side):
            obj.close()
        self.selector.close()

    def __enter__(self):
        return self

    def reset_cancelled_job(self):
        # The native USB backend ignores SIGTERM while reading stdin. Ask its
        # standard CUPS soft-reset interface to discard an incomplete stream
        # before closing it; never send guessed reset bytes into raster data.
        if self.process.poll() is not None or self.connected_at is None:
            return
        try:
            self.side.sendall(struct.pack('>BBH', 1, 0, 0))
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                for key, _ in self.selector.select(0.1):
                    try:
                        data = os.read(key.fd, 8192)
                    except BlockingIOError:
                        continue
                    if not data:
                        self.selector.unregister(key.fileobj)
                        continue
                    if key.data != 'side':
                        continue
                    self.side_buffer.extend(data)
                    while len(self.side_buffer) >= 4:
                        cmd, result, length = struct.unpack('>BBH', self.side_buffer[:4])
                        if length > 8192:
                            return
                        if len(self.side_buffer) < 4 + length:
                            break
                        del self.side_buffer[:4 + length]
                        if cmd == 1:
                            if result == 1:
                                logging.info('cancel: USB soft-reset confirmed')
                                return
                            raise OSError('USB reset rejected')
        except OSError:
            pass
        logging.warning('cancel: USB reset not confirmed; printer may need a power cycle')

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            if exc_type is not None and issubclass(exc_type, Cancelled):
                self.reset_cancelled_job()
        finally:
            self.close()


class Config:
    def __init__(self, base, prefix, uri, queue=QUEUE, usb=USB_BACKEND):
        self.base, self.prefix, self.uri = Path(base), Path(prefix), uri
        self.state = self.base / 'state'
        self.queue, self.usb = Path(queue), Path(usb)
        self.connect_timeout, self.transfer_timeout = 30, 180
        self.close_timeout, self.status_grace, self.progress_timeout = 30, 8, 300
        self.render_timeout = 300

    def environment(self, work=None):
        return {'PATH': f'{self.base}/runtime:{self.prefix}/bin:{SYSTEM_PATH}',
                'HOME': str(work or self.state), 'TMPDIR': str(work or self.state),
                'LC_ALL': 'C', 'USER': '_lp', 'GSBIN': 'gs', 'DEVICE_URI': self.uri}


def render(config, report, source, output, code, work):
    scratch = work / 'scratch'
    scratch.mkdir(mode=0o700)
    report.info('Preparing the selected pages and copies.')
    with open(output, 'wb') as target:
        process = subprocess.Popen([str(config.base / 'runtime/foo2zjs-wrapper'), '-P', '-z1', '-L0',
                                    f'-p{code}', '-n1', str(source)], stdout=target,
                                   stderr=subprocess.PIPE, env=config.environment(scratch), cwd=scratch,
                                   start_new_session=True)
        os.set_blocking(process.stderr.fileno(), False)
        selector = selectors.DefaultSelector()
        selector.register(process.stderr, selectors.EVENT_READ)
        deadline = time.monotonic() + config.render_timeout
        try:
            while process.poll() is None:
                report.tick()
                for key, _ in selector.select(0.1):
                    if not os.read(key.fd, 8192):
                        selector.unregister(key.fileobj)
                    else:
                        deadline = time.monotonic() + config.render_timeout
                if time.monotonic() >= deadline:
                    raise Held('Document conversion took too long. Nothing was sent to the printer.')
            if process.returncode:
                raise Held('Document conversion failed. Nothing was sent to the printer.')
        finally:
            stop_process(process)
            process.stderr.close()
            selector.close()


def name_stream(source, target, token):
    """Check chunk bounds/count, change only the PJL JOB/EOJ names, keep image bytes."""
    prefix = b'\x1b%-12345X@PJL JOB\n'
    suffix = b'\x1b%-12345X@PJL EOJ\n\x1b%-12345X'
    length = source.stat().st_size
    pages = 0
    with open(source, 'rb') as data:
        head = data.read(4096)
        if not head.startswith(prefix) or b'JZJZ' not in head:
            raise Held('Conversion did not produce a supported HP 1020 stream.')
        pos = head.index(b'JZJZ') + 4
        first, in_page, ended = True, False, False
        while pos + 16 <= length:
            data.seek(pos)
            size, kind, items, reserved, signature = struct.unpack('>IIIHH', data.read(16))
            if size < 16 or pos + size > length or signature != 0x5a5a or (first and kind != 0):
                raise Held('Conversion produced invalid printer data.')
            first = False
            if kind == 2:
                if in_page:
                    raise Held('Invalid page boundaries in printer data.')
                in_page = True
                pages += 1
            elif kind == 3:
                if not in_page:
                    raise Held('Invalid page boundaries in printer data.')
                in_page = False
            pos += size
            if kind == 1:
                ended = True
                break
        data.seek(pos)
        if not ended or in_page or data.read() != suffix:
            raise Held('Conversion produced an incomplete document.')
        data.seek(len(prefix))
        remaining = length - len(prefix) - len(suffix)
        with open(target, 'wb') as out:
            out.write(prefix[:-1] + f' NAME="{token}"\n'.encode('ascii'))
            while remaining:
                block = data.read(min(32768, remaining))
                if not block:
                    raise Held('Printer data was truncated.')
                out.write(block)
                remaining -= len(block)
            out.write(suffix.replace(b'@PJL EOJ\n', f'@PJL EOJ NAME="{token}"\n'.encode('ascii')))
    return pages


def print_document(config, report, source, code, job_id, user, work):
    converted, named = work / 'converted.zjs', work / 'job.zjs'
    render(config, report, source, converted, code, work)
    token = 'hp1020-' + str(job_id) + '-' + uuid.uuid4().hex[:16]
    pages = name_stream(converted, named, token)
    if pages == 0:
        report.info('No pages selected; nothing was sent to the printer.')
        return
    parser = PJLStatus(report, token, pages)
    with Transport(config, report, job_id, user, parser) as usb:
        ident = usb.device_id()
        if re.search(rb'(?:^|;)FWVER:[^;\x00]+', ident):
            report.info(f'Sending {pages} prepared pages to the printer.')
            usb.send_file(named)
            usb.wait_for_pages()
            usb.finish()
            return
        # The preserved upstream loader uses FWVER in the IEEE-1284 ID to
        # distinguish loaded stock firmware. Never reload on every document.
        report.info('Loading printer firmware after power-on.')
        usb.send_file(config.base / 'runtime/sihp1020.dl')
        try:
            usb.finish()
        except Held:
            # Loading firmware can disconnect USB. Only a fresh FWVER response
            # below permits document transfer; timeout alone is never success.
            pass
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        report.tick()
        time.sleep(0.1)
    with Transport(config, report, job_id, user, parser) as usb:
        ident = usb.device_id()
        if not re.search(rb'(?:^|;)FWVER:[^;\x00]+', ident):
            raise Held('Printer firmware did not become ready. No document was sent.')
        report.info(f'Sending {pages} prepared pages to the printer.')
        usb.send_file(named)
        usb.wait_for_pages()
        usb.finish()


def process_request(config, request):
    directory = os.open(request, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    identity = os.fstat(directory)
    reply = None
    try:
        reply = safe_open(directory, 'reply', os.O_WRONLY, stat.S_ISFIFO)
        report = Reporter(reply, directory)
        report.tick()  # Reject cancelled work before any rendering/USB.
        if 'started' in os.listdir(directory):
            raise Held('A previous worker stopped during this job. Check the printer before resuming.')
        with os.fdopen(safe_open(directory, 'ticket'), 'rb') as ticket:
            raw = ticket.read(65537)
        fields = raw.split(b'\0')
        if len(raw) > 65536 or len(fields) != 7 or fields[-1] or fields[0] != b'HP1020-TICKET-2':
            raise Held('Invalid job ticket.')
        _, job_id, user, title, copies, options, _ = [f.decode('utf-8', 'surrogateescape') for f in fields]
        if not re.fullmatch(r'[1-9][0-9]{0,9}', job_id) or not re.fullmatch(r'[1-9][0-9]{0,3}', copies):
            raise Held('Invalid job number or copy count.')
        code = paper_code(options)
        fd = os.open('started', os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600, dir_fd=directory)
        os.close(fd)
        work_root = config.state / 'work'
        work_root.mkdir(mode=0o700, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='job-', dir=work_root) as folder:
            work = Path(folder)
            source = work / 'document.ps'
            with os.fdopen(safe_open(directory, 'document'), 'rb') as data, open(source, 'wb') as output:
                if data.read(len(MAGIC)) != MAGIC:
                    raise Held('Raw jobs are unsupported. Print through the HP LaserJet 1020 Plus queue.')
                start = data.read(4)
                if start != b'%!PS':
                    raise Held('The macOS print filters did not produce PostScript.')
                output.write(start)
                while block := data.read(65536):
                    report.tick()
                    output.write(block)
            # CUPS pstops supplies collated pages or PostScript NumCopies for
            # uncollated output. Our renderer applies those settings. Applying
            # copies to foo2zjs/USB again would multiply the output twice.
            print_document(config, report, source, code, job_id, user, work)
        report.send('RESULT 0')
        logging.info('job %s: transfer completed', job_id)
    except Cancelled:
        logging.info('job cancelled or CUPS client disconnected')
    except (Held, OSError, ValueError) as error:
        logging.error('job held: %s', clean_message(error))
        if reply is not None:
            with contextlib.suppress(Cancelled, OSError):
                report.send('ERROR: ' + clean_message(error))
                report.send('RESULT 3')
    except Exception:
        logging.exception('unexpected worker error; job held')
        if reply is not None:
            with contextlib.suppress(Cancelled, OSError):
                report.send('ERROR: Printer software encountered an error. Job held; check before resuming.')
                report.send('RESULT 3')
    finally:
        if reply is not None:
            os.close(reply)
        os.close(directory)
        # Never retain extra copies of personal documents after processing.
        try:
            current = request.lstat()
            if (current.st_dev, current.st_ino) == (identity.st_dev, identity.st_ino):
                shutil.rmtree(request)
        except FileNotFoundError:
            pass


def clean_incoming(config):
    """Remove abandoned captures, never an active backend's partial document."""
    for request in config.queue.glob('.incoming.*'):
        try:
            st = request.lstat()
            if not stat.S_ISDIR(st.st_mode) or time.time() - st.st_mtime < 60:
                continue
            directory = os.open(request, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                try:
                    with os.fdopen(safe_open(directory, 'owner'), 'rb') as source:
                        owner = source.read(32).strip()
                    if owner.isdigit() and 0 < int(owner) < 2147483647:
                        try:
                            os.kill(int(owner), 0)
                            continue
                        except PermissionError:
                            continue  # An inaccessible process may still own it.
                        except ProcessLookupError:
                            pass
                except FileNotFoundError:
                    pass
            finally:
                os.close(directory)
            current = request.lstat()
            if (current.st_dev, current.st_ino) == (st.st_dev, st.st_ino):
                shutil.rmtree(request)
        except (OSError, Held):
            continue


def worker(config):
    config.state.mkdir(mode=0o700, parents=True, exist_ok=True)
    lock = os.open(config.state / 'worker.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    owned = False
    try:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return  # Never remove another running worker's lock.
        owned = True
        # No other worker can be rendering while we own the lock. A killed
        # worker cannot run TemporaryDirectory cleanup; discard its private
        # copies before accepting new work. CUPS still owns held-job originals.
        for abandoned in (config.state / 'work').glob('job-*'):
            if abandoned.is_symlink():
                abandoned.unlink()
            elif abandoned.is_dir():
                shutil.rmtree(abandoned)
        if not config.queue.is_dir():
            raise RuntimeError('Printer spool directory is missing')
        for name in ('foo2zjs-wrapper', 'foo2zjs', 'foo2zjs-pstops', 'hp1020-usb-run'):
            if not os.access(config.base / 'runtime' / name, os.X_OK):
                raise RuntimeError('Printer runtime is incomplete: ' + name)
        ready = config.state / 'ready'
        ready.write_text(f'HP1020-SERVICE-2 {os.getpid()}\n')
        while not STOPPING:
            clean_incoming(config)
            requests = []
            for request in config.queue.glob('job-*'):
                try:
                    st = request.lstat()
                    if stat.S_ISDIR(st.st_mode):
                        requests.append((st.st_mtime_ns, request.name, request))
                except FileNotFoundError:
                    pass
            requests.sort()
            if not requests:
                time.sleep(0.25)
                continue
            for _, _, request in requests:
                if STOPPING:
                    break
                try:
                    process_request(config, request)
                except OSError as error:
                    logging.error('could not open job: %s', clean_message(error))
    finally:
        if owned:
            with contextlib.suppress(FileNotFoundError):
                (config.state / 'ready').unlink()
        os.close(lock)


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--brew-prefix', required=True)
    parser.add_argument('--device-uri', required=True)
    parser.add_argument('mode', choices=['worker'])
    args = parser.parse_args()
    if os.geteuid() == 0:
        parser.error('Run the printer service as _lp, not root.')
    if not args.device_uri.startswith('usb://Hewlett-Packard/HP%20LaserJet%201020?') or any(c in args.device_uri for c in '\r\n\0'):
        parser.error('An exact HP LaserJet 1020 USB URI is required.')
    config = Config(Path(__file__).resolve().parent, args.brew_prefix, args.device_uri)
    def stop(signum, frame):
        global STOPPING
        STOPPING = True
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s',
                        handlers=[RotatingFileHandler(config.state / 'spool-worker.log', maxBytes=1048576, backupCount=2)])
    worker(config)


if __name__ == '__main__':
    main()
