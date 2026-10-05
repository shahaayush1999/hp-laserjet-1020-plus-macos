#!/usr/bin/env python3
"""Reusable USB printer composition with synthetic transfers and exact pixels.

No physical controller, device access, firmware upload or printing is performed.
All ownership settlement and reset promises are explicitly supplied.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import runpy
import select
import shutil
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('tusb_printer_pages', ROOT/'scripts/validate-hp1020-image-pages.py')
pages = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = pages
spec.loader.exec_module(pages)
core = pages.core
SRC = ROOT/'open-firmware/tinyusb-printer-test'
ADAPTER = ROOT/'open-firmware/tinyusb-printer-adapter'
PROTOCOL = ROOT/'open-firmware/tinyusb-device'
PRINTER = ROOT/'open-firmware/usb-printer-class'
RX = ROOT/'open-firmware/usb-receive-core'
IMG = ROOT/'open-firmware/image-core'
SEM = ROOT/'open-firmware/semantic-core'
VENDOR = ROOT/'vendor/tinyusb-0.21.0'
OUT = ROOT/'analysis/usb-path/tinyusb-printer'
OK, WAIT, STALE, INVALID, LIMIT, ERROR = range(6)
STOPPED, PAYLOAD = 3, 8
STATS = 96
DEVICE_ID = b'\x01\x90' + bytes(65+i % 26 for i in range(398))
DEVICE = bytes.fromhex('1201000200000040feca0040000100000001')


def packet(kind, request, value=0, index=0, length=0):
    return struct.pack('<BBHHH', kind, request, value, index, length)


class Host:
    def __init__(self, executable, directory, fill, capacity, interface, fail_at=0xffffffff):
        self.directory, self.interface, self.capacity = directory, interface, capacity
        self.stderr = (directory/'stderr').open('wb')
        self.process = subprocess.Popen([str(executable), str(fill), str(capacity), str(interface), str(fail_at)] +
            [str(directory/name) for name in ('pixels', 'wire', 'receive', 'output')],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.stderr)
        self.initial = self.row = self.read_row()
        assert self.initial[0:2] == [0, 0] and self.initial[15:17] == [0, 1], self.initial
        self.events, self.rows, self.packets = [], [], []
        self.expected_pixels = b''
        self.requested = 0

    def read_row(self):
        if not select.select([self.process.stdout], [], [], 30)[0]:
            self.process.kill()
            self.process.wait()
            raise AssertionError('host timed out: '+str(self.directory))
        raw = self.process.stdout.readline()
        with (self.directory/'raw-stdout').open('ab') as saved:
            saved.write(raw)
        assert raw, ('fixture ended early', self.directory)
        row = json.loads(raw)
        assert len(row) == STATS, row
        return row

    def step(self, op, a=0, b=0, c=0, d=0, data=b'', result=OK, expect=None):
        words = [op, a, b, c, d]
        wire = struct.pack('>6I', *words, len(data)) + data
        with (self.directory/'events.bin').open('ab') as saved:
            saved.write(wire)
        self.process.stdin.write(wire)
        self.process.stdin.flush()
        self.row = self.read_row()
        self.events.append(dict(words=words, data_hex=data.hex(), result=result))
        self.rows.append(self.row.copy())
        with (self.directory/'host-steps.jsonl').open('a') as saved:
            saved.write(json.dumps(self.row)+'\n')
        assert self.row[15:17] == [0, 1], ('ownership/guard', len(self.rows)-1, words, self.row)
        assert self.row[0] == result, ('result', len(self.rows)-1, words, result, self.row)
        assert all(self.row[int(i)] == value for i, value in (expect or {}).items()), (words, expect, self.row)
        return self.row

    def service(self, result=OK):
        return self.step(1, result=result)

    def setup(self, raw, known=0, status=0, service_result=OK):
        self.requested = struct.unpack_from('<H', raw, 6)[0]
        self.step(0, 8, known, status, data=raw)
        self.service(service_result)

    def wire(self, expected, label):
        # A bulk submission may have happened since this retained IN packet.
        # Use its still-owned EP0 identity/length, not the last endpoint globally.
        assert self.row[28] and self.row[29] == len(expected), (label, self.row)
        self.packets.append(dict(step=len(self.rows)-1, offset=self.row[24]-len(expected),
                                 expected_hex=expected.hex(), label=label))

    def complete(self, token, length, usb_result=0, result=OK, service=True):
        self.step(2, token, usb_result, length, result=result)
        if service:
            self.service()

    def control_in(self, expected, label):
        assert 0 < self.requested and len(expected) <= self.requested
        lengths = [min(64, len(expected)-at) for at in range(0, len(expected), 64)]
        if len(expected) < self.requested and len(expected) % 64 == 0:
            lengths.append(0)
        at = 0
        for length in lengths:
            assert self.row[28] and self.row[29] == length, self.row
            self.wire(expected[at:at+length], label)
            self.complete(self.row[28], length)
            at += length
        assert self.row[26] and not self.row[28] and self.row[27] == 0
        self.complete(self.row[26], 0)
        assert not self.row[26] and not self.row[28]

    def control_status(self, label='status'):
        assert self.row[28] and self.row[29] == 0, self.row
        self.wire(b'', label)
        self.complete(self.row[28], 0)

    def request(self, raw, expected=None, known=0, status=0, label='control'):
        self.setup(raw, known, status)
        if expected is None:
            self.control_status(label)
        else:
            self.control_in(expected, label)

    def begin_reset(self, kind=0x21, slot=0):
        self.setup(packet(kind, 2, index=self.interface))
        assert self.row[36] == self.row[44] == self.row[47] == 1 and not self.row[28]
        self.step(10, slot)

    def finish_reset(self, slot=0, ack=True, already_output=False):
        generation = self.row[32]
        self.step(12, slot, result=WAIT)
        self.step(11, slot, 1)
        if not already_output:
            self.step(11, slot, 2)
        self.step(15)
        self.step(11, slot, 4)
        self.step(12, slot, expect={32: generation+1, 35: 0, 36: 0, 7: 0, 9: 0})
        if ack:
            self.control_status('class-reset-status')

    def recover(self):
        self.begin_reset()
        self.finish_reset()

    def configure(self):
        self.step(5)
        self.service()
        self.request(packet(0, 9, 1))
        assert self.row[8] == self.row[10] == self.row[36] == 1
        self.step(6, result=WAIT, expect={33: 0, 35: 0})
        self.recover()

    def arm_write(self, data):
        assert len(data) <= self.capacity
        self.step(6)
        token = self.row[30]
        assert token and self.row[31] == self.capacity
        self.step(3, token, len(data), data=data)
        return token

    def transfer(self, data):
        token = self.arm_write(data)
        self.complete(token, len(data))
        return token

    def send(self, data, size=512, zlp=True):
        fragments = [data[i:i+size] for i in range(0, len(data), size)]
        if zlp:
            fragments = [b''] + fragments[:1] + [b''] + fragments[1:] + [b'']
        for at in range(0, len(fragments), 4):
            group = fragments[at:at+4]
            for fragment in group:
                self.transfer(fragment)
            if len(group) == 4:
                self.step(6, result=WAIT, expect={35: 4})
            self.step(7)
            assert self.row[40] == 0 and self.row[36] == 0, 'short/ZLP is not EOF'

    def close_finish(self, documents, page_count):
        self.step(9, result=WAIT)
        self.step(8)
        self.step(6, result=WAIT)
        self.step(9, expect={40: 1, 56: documents, 57: page_count, 58: page_count, 54: 0})
        self.step(9)

    def finish(self):
        self.process.stdin.close()
        assert self.process.wait(timeout=30) == 0, self.directory
        captures = {name: (self.directory/name).read_bytes() for name in ('pixels', 'wire', 'receive', 'output')}
        assert captures['pixels'] == self.expected_pixels, ('pixels', self.directory, len(captures['pixels']), len(self.expected_pixels))
        assert len(captures['wire']) == self.row[24] and core.fnv(captures['wire']) == self.row[25]
        assert len(captures['pixels']) == self.row[50] and core.fnv(captures['pixels']) == self.row[51]
        assert core.fnv(captures['receive']) == self.row[60] and core.fnv(captures['output']) == self.row[61]
        covered = bytearray(len(captures['wire']))
        for item in self.packets:
            expected = bytes.fromhex(item['expected_hex'])
            start, end = item['offset'], item['offset'] + len(expected)
            assert captures['wire'][start:end] == expected, item
            assert not any(covered[start:end]), item
            covered[start:end] = b'\x01' * len(expected)
        assert all(covered), 'every proposed IN byte needs an independent wire oracle'
        return captures

    def abort(self):
        if not self.process.stdin.closed:
            self.process.stdin.close()
        try:
            self.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
        self.process.stdout.close()
        self.stderr.close()


def sources(temp):
    selected = set(SRC.glob('*.[ch]')) | set(SRC.glob('*.ld')) | set(ADAPTER.glob('*.[ch]'))
    selected.add(PROTOCOL/'tusb_config.h')
    selected.update((PROTOCOL/'freestanding').glob('*.h'))
    selected.update((PROTOCOL/'patches').glob('*'))
    provenance = json.loads((VENDOR/'PROVENANCE.json').read_text())
    selected.add(VENDOR/'PROVENANCE.json')
    for name, record in provenance['upstream_files'].items():
        path = VENDOR/name
        assert core.sha(path.read_bytes()) == record['sha256']
        selected.add(path)
    selected.update(PRINTER/name for name in ('hp1020_usb_printer.c', 'hp1020_usb_printer.h'))
    selected.update(RX/name for name in ('hp1020_usb_receive.c', 'hp1020_usb_receive.h', 'hp1020_usb_document.c', 'hp1020_usb_document.h'))
    selected.update(IMG/(name+ext) for name in ('hp1020_image', 'hp1020_image_page', 'hp1020_image_stream',
        'hp1020_image_ring', 'hp1020_image_output') for ext in ('.c', '.h'))
    selected.update(IMG/name for name in ('target-memory.c', 'reference.c'))
    selected.update((IMG/'freestanding').glob('*.h'))
    selected.update(SEM.rglob('*.c'))
    selected.update(SEM.rglob('*.h'))
    selected.update((core.VENDOR/'libjbig').glob('*.h'))
    selected.update(core.VENDOR/'libjbig'/name for name in ('jbig85.c', 'jbig_ar.c'))
    selected.update(ROOT/'vendor/foo2zjs-source'/name for name in ('jbig.c', 'jbig_ar.c', 'jbig.h', 'jbig_ar.h'))
    selected.update(ROOT/'scripts'/name for name in ('validate-hp1020-tinyusb-printer.py',
        'build-hp1020-tinyusb-printer-target.sh', 'prepare-hp1020-tinyusb.py', 'validate-hp1020-image-pages.py',
        'validate-hp1020-image-core.py', 'check-hp1020-c-compiler-profile.py',
        'hp1020_qemu_ram.py', 'hp1020_xtensa_call0.py', 'hp1020_xtensa_properties.py'))
    tested = {str(p.relative_to(ROOT)): core.sha(p.read_bytes()) for p in sorted(selected)}
    for name in tested:
        path = temp/'source'/name
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT/name, path)
    (temp/'source-sha256.json').write_text(json.dumps(tested, indent=2)+'\n')
    return tested


def compile_host(temp, effective, fixture=None, main=None):
    implementation = [fixture or SRC/'fixture.c', main or SRC/'host-check.c', ADAPTER/'hp1020_tusb_adapter.c',
        PRINTER/'hp1020_usb_printer.c', RX/'hp1020_usb_receive.c', RX/'hp1020_usb_document.c']
    implementation += [IMG/name for name in ('hp1020_image.c', 'hp1020_image_page.c', 'hp1020_image_stream.c',
        'hp1020_image_ring.c', 'hp1020_image_output.c')]
    implementation += [SEM/'hp1020_semantic.c', SEM/'hp1020_page_plan.c',
        core.VENDOR/'libjbig/jbig85.c', core.VENDOR/'libjbig/jbig_ar.c']
    implementation += [effective/'src'/name for name in ('tusb.c', 'device/usbd.c', 'common/tusb_fifo.c')]
    flags = ['clang', '-std=c11', '-O1', '-g', '-fno-common', '-Wall', '-Wextra', '-Werror', '-fsanitize=address,undefined']
    include = ['-I'+str(p) for p in (SRC, ADAPTER, PROTOCOL, PRINTER, RX, IMG, SEM, core.VENDOR/'libjbig', effective/'src')]
    core.command(flags+include+implementation+['-o', temp/'host'])
    full = ROOT/'vendor/foo2zjs-source'
    core.command(flags+['-I'+str(full), IMG/'reference.c', full/'jbig.c', full/'jbig_ar.c', '-o', temp/'reference'])


def image_documents(temp):
    images, paths = {}, []
    for name, width, height, kind, path in (
        ('small', 32, 8, 'black', 'fixtures/32x8-stripe4-black.jbg'),
        ('medium', 9600, 132, 'edges', 'fixtures/9600x132-stripe128-edges.jbg'),
        ('wide', 16384, 4, 'edges', 'fixtures/16384x4-stripe128-edges.jbg'),
        ('partial', 1024, 260, 'repeat', 'output-fixtures/1024x260-stripe128-repeat.jbg'),
        ('slim', 64, 12, 'edges', 'output-fixtures/64x12-stripe4-edges.jbg')):
        path = pages.OUT/path
        raw = core.pattern(width, height, kind)
        info = json.loads(core.command([temp/'reference', 'decode', path, temp/'oracle']))
        assert (temp/'oracle').read_bytes() == raw and info['consumed'] == path.stat().st_size
        images[name] = path.read_bytes(), raw
        paths.append(path)
    base_path = ROOT/'analysis/samples/generated/matrix-a4_default.zjs'
    base = pages.chunks(base_path.read_bytes())

    def body(name):
        bie = images[name][0]
        width, height = struct.unpack_from('>II', bie, 4)
        items = bytearray(base[1][1])
        for offset in range(0, len(items), 12):
            ident = struct.unpack_from('>H', items, offset+4)[0]
            value = {4: 1, 12: width, 13: height, 17: width//2, 18: height}.get(ident)
            if value is not None:
                struct.pack_into('>I', items, offset+8, value)
        payload = bie[20:] + bytes(16 + ((-len(bie[20:])) & 3))
        return [(2, bytes(items), base[1][2], base[1][3]), (4, bie[:20], 0, 0),
                (5, payload, 0, 0), (6, b'', 0, 0), (3, b'', 0, 0)]

    def document(names):
        return b'JZJZ' + pages.pack([base[0]]+sum((body(name) for name in names), [])+[base[-1]])

    return document, images, paths+[base_path]


def initial_standard_profiles():
    cases = []
    for fill in (0, 204):
        for request in ('descriptor', 'device-status', 'remote-wakeup'):
            for phase in ('active-input', 'pending-recovery'):
                cases.append((f'initial-standard/{request}/{phase}', fill, 1024, 3))
        cases += [('initial-standard/success-and-unsupported', fill, 1024, 3),
                  ('initial-standard/direct-address-owner', fill, 1024, 3)]
    return cases


def initial_standard_scenario(h, name, document, images):
    if name == 'initial-standard/direct-address-owner':
        # SET_ADDRESS delegates its status directly to this synthetic DCD. The
        # core has not set its EP0 BUSY bit when that valid owner binds. This
        # must not be confused with a rejected core-submitted status packet.
        h.step(5)
        h.service()
        epoch, generation = h.row[4], h.row[32]
        h.setup(packet(0, 5, value=37))
        token = h.row[28]
        assert token and h.row[29] == 0 and h.row[17] == 1, h.row
        assert h.row[64] == 0 and h.row[65] == 37 and not h.row[14], h.row
        for _ in range(3):
            h.service()
            assert h.row[28] == token and h.row[4] == epoch and h.row[32] == generation
            assert h.row[17] == 1 and h.row[66] == 0
        h.control_status('direct-DCD-address-status')
        assert h.row[64] == 37 and not h.row[28] and h.row[4] == epoch, h.row
        h.complete(token, 0, result=STALE, service=False)
        h.request(packet(0x80, 6, value=0x100, length=18), DEVICE)
        return

    h.configure()
    small = document(['small'])

    def fresh():
        h.send(small, min(64, h.capacity))
        h.close_finish(1, 1)
        h.expected_pixels += images['small'][1]

    if name == 'initial-standard/success-and-unsupported':
        # Successful standard DATA and STATUS while OUT remains borrowed must
        # keep its identity/bytes. Unsupported requests have no submitted owner;
        # their normal STALL must not be interpreted as a submission failure.
        out = h.arm_write(small[:31])
        saved = tuple(h.row[i] for i in (4, 5, 30, 31, 32, 33, 34, 35))
        h.request(packet(0x80, 6, value=0x100, length=18), DEVICE)
        h.request(packet(0x80, 0, length=2), b'\x01\x00')
        h.request(packet(0, 3, value=1), label='set-remote-wakeup')
        h.request(packet(0x80, 0, length=2), b'\x03\x00')
        h.request(packet(0, 1, value=1), label='clear-remote-wakeup')
        submitted = h.row[17]
        h.setup(packet(0x80, 0xff, length=2))
        assert h.row[11] == 3 and h.row[17] == submitted, h.row
        assert h.row[13] == 4 and not h.row[26] and not h.row[28], h.row
        for _ in range(3):
            h.service()
            assert tuple(h.row[i] for i in (4, 5, 30, 31, 32, 33, 34, 35)) == saved
            assert h.row[7] == h.row[9] == h.row[14] == h.row[36] == 0, h.row
        h.request(packet(0x80, 0, length=2), b'\x01\x00')
        h.complete(out, 31)
        h.step(7)
        h.send(small[31:], 64)
        h.close_finish(1, 1)
        h.expected_pixels = images['small'][1]
        return

    _, request, phase = name.split('/')
    raw, proposal, initial_stall = {
        # GET_DESCRIPTOR propagates false and TinyUSB issues a DCD STALL. The
        # other two handlers swallow false. All three must retain their owner.
        'descriptor': (packet(0x80, 6, value=0x100, length=18), DEVICE, 3),
        'device-status': (packet(0x80, 0, length=2), b'\x01\x00', 0),
        'remote-wakeup': (packet(0, 3, value=1), b'', 0),
    }[request]
    generation = h.row[32]
    old_out = 0
    if phase == 'active-input':
        h.transfer(small[:11])  # READY bytes must not be pumped after the fault.
        old_out = h.arm_write(small[11:31])
        assert h.row[34] == 0 and h.row[35] == 2 and h.row[50] == 0
    else:
        assert phase == 'pending-recovery'
        h.begin_reset(slot=1)
        for part in (1, 2, 4):
            if part == 4:
                h.step(15)
            h.step(11, 1, part)
        assert h.row[44:46] == [1, 7], h.row

    class_request = h.row[80]
    h.step(14, 2)  # Bind the exact cookie, then return false to the core.
    h.setup(raw, service_result=ERROR)
    ep0 = h.row[28]
    assert ep0 and h.row[29] == len(proposal) and not h.row[26], h.row
    h.wire(proposal, 'retained-initial-standard-proposal')
    assert h.row[11] == initial_stall and h.row[14] == (6 if old_out else 2), h.row
    assert h.row[7] == h.row[9] == h.row[36] == 1, h.row
    assert h.row[32] == generation and h.row[44] == h.row[45] == h.row[47] == 0, h.row
    assert h.row[80] == class_request, h.row
    submitted, cancel_requests, epoch = h.row[17], h.row[66], h.row[4]
    for _ in range(3):
        h.service()
        assert h.row[28] == ep0 and h.row[30] == old_out, h.row
        assert (h.row[17], h.row[66], h.row[4]) == (submitted, cancel_requests, epoch)
        h.step(6, result=WAIT)
        h.step(7, result=STOPPED)
        assert h.row[34] == h.row[50] == 0, h.row
    if phase == 'pending-recovery':
        # Before the fix this already-current recovery can finish and restart
        # input despite the known rejected EP0 owner. No new-generation repair
        # may be inferred from old promises or absence of a bulk owner.
        h.step(11, 1, 1, result=STALE)
        h.step(12, 1, result=STALE)
        assert h.row[32] == generation and h.row[17] == submitted and h.row[28] == ep0

    # Superseding SETUP still waits for explicit original EP0 settlement. A
    # hardware/software STALL and a cancellation request never release it.
    h.setup(packet(0x80, 0, length=2), service_result=WAIT)
    assert h.row[28] == ep0 and h.row[17] == submitted, h.row
    h.step(4, ep0)
    h.service()
    status = b'\x03\x00' if request == 'remote-wakeup' else b'\x01\x00'
    h.control_in(status, 'status-after-explicit-old-EP0-settlement')
    assert h.row[36] == 1 and h.row[32] == generation, h.row
    h.complete(ep0, 0, result=STALE, service=False)
    if old_out:
        h.step(4, old_out)
        h.service()
        h.complete(old_out, 0, result=STALE, service=False)
    h.recover()
    fresh()


AUTOMATIC_RECOVERY_SCENARIOS = (
    'automatic/first-document',
    'automatic/repeated-config-settles-owned-out',
    'automatic/independent-request-identity',
    'automatic/config-status-completion-fault',
    'automatic/superseded-deconfiguration',
    'automatic/wire-and-bus-reset-supersession',
    'automatic/config-status-rejected/1',
    'automatic/config-status-rejected/2',
)


def automatic_recovery_profiles():
    # Interface zero and nonzero both bootstrap; other new contracts need only
    # the nonzero interface. Existing cases retain the broader transfer matrix.
    profiles = []
    for fill in (0, 204):
        profiles += [(name, fill, 1024, 3) for name in AUTOMATIC_RECOVERY_SCENARIOS]
        profiles.append(('automatic/first-document', fill, 1024, 0))
    return profiles


def automatic_recovery_scenario(h, name, document, images):
    small = document(['small'])

    def snapshot(indices):
        return tuple(h.row[i] for i in indices)

    def no_new_wire_or_owner(before):
        assert snapshot((17, 24, 25, 26, 28, 46, 47, 77)) == before, h.row

    def pending(recovery, generation, slot):
        assert h.row[42:46] == [recovery, generation, 1, 0], h.row
        assert h.row[36] == 1 and h.row[47] == 0, h.row
        h.step(10, slot)

    def initial_configuration(settle_status=True):
        h.step(5)
        h.service()
        h.step(10, 0, result=WAIT)
        h.setup(packet(0, 9, 1))
        # One ordinary SET_CONFIGURATION ZLP; no internal class request/packet.
        assert h.row[17] == 1 and h.row[24] == 0 and h.row[80] == 0, h.row
        assert h.row[8] == h.row[10] == h.row[36] == 1, h.row
        pending(1, 1, 0)
        if settle_status:
            h.control_status('initial-set-configuration')
        else:
            h.wire(b'', 'initial-set-configuration-will-fail')
        h.step(6, result=WAIT, expect={33: 0, 35: 0})

    def finish_automatic(recovery, generation, slot=0):
        assert h.row[42:44] == [recovery, generation], h.row
        before = snapshot((17, 24, 25, 26, 28, 46, 47, 77))
        h.step(12, slot, result=WAIT)
        parts = 0
        for part in (1, 2, 4):
            if part == 4:
                h.step(15)  # Explicit supplied transport reset, not inferred.
            parts |= part
            h.step(11, slot, part, expect={45: parts})
            h.step(11, slot, part, expect={45: parts})
            if parts != 7:
                h.step(12, slot, result=WAIT, expect={32: generation, 36: 1})
            no_new_wire_or_owner(before)
        h.step(12, slot, expect={32: generation + 1, 35: 0, 36: 0,
                                7: 0, 9: 0, 44: 0, 45: 0, 47: 0})
        no_new_wire_or_owner(before)
        h.step(12, slot, result=STALE)
        h.step(10, 7, result=WAIT)

    def fresh_document():
        h.send(small, min(64, h.capacity))
        h.close_finish(1, 1)
        h.expected_pixels += images['small'][1]

    def request_probe(expected_request):
        h.request(packet(0xa1, 1, index=h.interface, length=1), b'\x18')
        assert h.row[80] == expected_request, ('real request counter', h.row)

    def rebind(recovery, generation, slot):
        h.request(packet(0, 9, 0), label='real-deconfiguration')
        assert h.row[8] == h.row[10] == 0, h.row
        h.step(10, slot, result=WAIT)
        h.request(packet(0, 9, 1), label='real-reconfiguration')
        pending(recovery, generation, slot)

    if name.startswith('automatic/config-status-rejected/'):
        mode = int(name.rsplit('/', 1)[1])
        h.step(5)
        h.service()
        h.step(14, mode)
        h.setup(packet(0, 9, 1), service_result=ERROR)
        assert h.row[7] == h.row[36] == 1 and h.row[32] == 1, h.row
        # This configuration attempt must allocate no recovery identity. The
        # endpoint binding exists, but status was never accepted for submission.
        assert h.row[42] == h.row[44] == h.row[80] == 0, h.row
        h.step(10, 0, result=WAIT)
        h.step(6, result=WAIT)
        if mode == 2:
            retained = h.row[28]
            assert retained and h.row[14] == 2 and h.row[17] == 1, h.row
            h.wire(b'', 'rejected-but-retained-config-status')
            h.service()
            assert h.row[28] == retained and h.row[44] == 0, h.row
            h.step(4, retained)
            h.service()
            h.complete(retained, 0, result=STALE, service=False)
        else:
            assert h.row[28] == h.row[17] == 0, h.row
        h.request(packet(0, 9, 1), label='repeated-configuration-recovers-rejected-status')
        pending(1, 1, 1)
        assert h.row[68] == 1, 'configuration-only reset must preserve connection'
        for _ in range(3):
            h.service()
            h.step(10, 1)
            assert h.row[42:46] == [1,1,1,0]
        finish_automatic(1, 1, 1)
        request_probe(1)
        fresh_document()
        return

    initial_configuration(settle_status=name != 'automatic/config-status-completion-fault')

    if name == 'automatic/first-document':
        pending_before = snapshot((17, 24, 25, 32, 42, 43, 44, 45, 80))
        for _ in range(3):
            h.service()
            h.step(10, 0)
            assert snapshot((17, 24, 25, 32, 42, 43, 44, 45, 80)) == pending_before
        finish_automatic(1, 1)
        request_probe(1)  # Any fabricated internal SETUP would shift this ID.
        fresh_document()
        # All actual host class requests were the single status probe. Internal
        # recovery is separately observed through its independent ticket above.
        class_setups = [bytes.fromhex(e['data_hex']) for e in h.events
                        if e['words'][0] == 0 and e['data_hex'] and
                        (bytes.fromhex(e['data_hex'])[0] & 0x60) == 0x20]
        assert class_setups == [packet(0xa1, 1, index=h.interface, length=1)]
        return

    if name == 'automatic/config-status-completion-fault':
        token = h.row[28]
        assert token
        for part in (1, 2, 4):
            if part == 4:
                h.step(15)
            h.step(11, 0, part)
        assert h.row[45] == 7
        h.complete(token, 0, usb_result=1, service=False)
        h.step(11, 0, 1, result=STALE)
        h.step(12, 0, result=STALE)
        h.service()
        h.step(10, 0, result=WAIT)
        for _ in range(3):
            h.service()
            assert h.row[42] == 1 and not h.row[44] and h.row[36] == 1
        h.request(packet(0, 9, 1), label='repeated-configuration-after-fault')
        pending(2, 1, 1)
        assert h.row[68] == 1
        # Same generation, different recovery; all old supplied promises stale.
        h.step(11, 0, 4, result=STALE)
        h.step(12, 0, result=STALE)
        finish_automatic(2, 1, 1)
        request_probe(1)
        fresh_document()
        return

    if name == 'automatic/wire-and-bus-reset-supersession':
        h.step(11, 0, 1)
        h.step(11, 0, 2)
        h.begin_reset(slot=1)
        assert h.row[42] == 2 and h.row[80] == 1, h.row
        h.step(11, 0, 4, result=STALE)
        h.step(12, 0, result=STALE)
        h.finish_reset(slot=1)
        h.begin_reset(slot=2)
        assert h.row[42] == 3 and h.row[80] == 2 and h.row[32] == 2
        for part in (1, 2, 4):
            h.step(11, 2, part)
        submitted = h.row[17]
        h.step(5)  # Admission itself must invalidate this wire-reset ticket.
        h.step(11, 2, 1, result=STALE)
        h.step(12, 2, result=STALE)
        h.step(10, 7, result=WAIT)
        assert h.row[17] == submitted
        h.service()
        assert not h.row[8] and not h.row[10]
        h.request(packet(0, 9, 1), label='configuration-after-bus-reset')
        pending(4, 2, 3)
        assert h.row[17] == submitted + 1 and h.row[80] == 2
        h.step(12, 2, result=STALE)
        finish_automatic(4, 2, 3)
        request_probe(3)
        fresh_document()
        return

    finish_automatic(1, 1)

    if name == 'automatic/repeated-config-settles-owned-out':
        out = h.arm_write(small[:31])
        before = snapshot((17,24,25,30,31,32,33,34,35,42,43))
        h.setup(packet(0, 9, 1), service_result=WAIT)
        assert snapshot((17,24,25,30,31,32,33,34,35,42,43)) == before
        assert h.row[14] == 4 and h.row[44] == 0 and h.row[7] == h.row[36] == 1
        for _ in range(3):
            h.service(WAIT)
            h.step(10, 7, result=WAIT)
            h.step(6, result=WAIT)
            h.step(7, result=STOPPED)
            assert snapshot((17,24,25,30,31,32,33,34,35,42,43)) == before
        # Cancellation request is not settlement. Only the original retained
        # owner can be explicitly retired before endpoints are reinitialized.
        h.step(4, out)
        h.service()
        h.control_status('repeated-configuration-after-original-settlement')
        pending(2, 2, 1)
        assert h.row[68] == 1
        h.step(12, 0, result=STALE)
        finish_automatic(2, 2, 1)
        h.complete(out, 31, result=STALE, service=False)
        fresh_document()
        return

    if name == 'automatic/independent-request-identity':
        h.request(packet(0xa1, 0, index=h.interface << 8, length=12), DEVICE_ID[:12])
        assert h.row[80] == 1
        request_probe(2)
        h.begin_reset(slot=1)
        assert h.row[42] == 2 and h.row[80] == 3, h.row
        h.step(12, 0, result=STALE)
        submitted = h.row[17]
        h.finish_reset(slot=1)
        assert h.row[17] == submitted + 1 and h.row[80] == 3
        request_probe(4)
        fresh_document()
        return

    if name == 'automatic/superseded-deconfiguration':
        old_out = h.arm_write(b'old')
        h.setup(packet(0xa1, 0, index=h.interface << 8, length=400))
        old_ep0 = h.row[28]
        h.wire(DEVICE_ID[:64], 'retained-id-before-superseded-deconfiguration')
        h.setup(packet(0, 9, 0), service_result=WAIT)
        h.setup(packet(0x80, 0, length=2), service_result=WAIT)
        assert h.row[10] == 1 and h.row[36] == 1
        h.step(4, old_ep0)
        h.service()
        h.control_in(b'\x01\x00', 'status-after-superseded-deconfiguration')
        h.step(10, 7, result=WAIT)
        h.step(4, old_out)
        h.service()
        h.request(packet(0, 9, 1), label='repeated-config-replaces-superseded-deconfiguration')
        pending(2, 2, 1)
        assert h.row[10] == h.row[36] == h.row[7] == h.row[68] == 1
        for _ in range(3):
            h.service()
            h.step(10, 1)
            h.step(6, result=WAIT)
            assert h.row[42:46] == [2,2,1,0]
        h.step(12, 0, result=STALE)
        finish_automatic(2, 2, 1)
        h.complete(old_out, 0, result=STALE, service=False)
        request_probe(2)
        fresh_document()
        return

    raise AssertionError('unknown automatic recovery scenario: ' + name)


def scenario(h, name, document, images):
    if name.startswith("initial-standard/"):
        initial_standard_scenario(h, name, document, images)
        return
    if name.startswith("automatic/"):
        automatic_recovery_scenario(h, name, document, images)
        return
    h.configure()
    small = document(['small'])
    def fresh():
        h.send(small, min(64, h.capacity))
        h.close_finish(1, 1)
        h.expected_pixels += images['small'][1]

    if name.startswith('document/mixed/'):
        size = int(name.rsplit('/', 1)[1])
        names = ['medium', 'wide', 'small', 'partial']
        h.send(document(names), size)
        h.close_finish(1, 4)
        h.expected_pixels = b''.join(images[n][1] for n in names)
    elif name == 'document/consecutive':
        h.send(small+document([])+document(['slim']), min(64, h.capacity))
        h.close_finish(3, 2)
        h.expected_pixels = images['small'][1]+images['slim'][1]
    elif name == 'status-and-id-during-owned-out':
        token = h.arm_write(small[:31])
        epoch, generation, sequence = h.row[87:90]
        h.request(packet(0xa1, 1, index=h.interface, length=1), b'\x38', known=1, status=0x38)
        h.request(packet(0xa1, 0, index=h.interface << 8, length=401), DEVICE_ID)
        assert h.row[30] == token and h.row[32] == generation and h.row[5] == epoch
        h.complete(token, 31)
        assert h.row[33] == sequence
        h.step(7)
        h.send(small[31:], min(64, h.capacity))
        h.close_finish(1, 1)
        h.expected_pixels = images['small'][1]
    elif name == 'stale-completion-after-slot-reuse':
        old = h.transfer(small[:7])
        h.step(7)
        token = h.arm_write(small[7:14])
        before = h.row[32:42]
        h.complete(old, 7, result=STALE, service=False)
        assert h.row[32:42] == before and h.row[30] == token
        h.complete(token, 7)
        h.step(7)
        h.send(small[14:], 64)
        h.close_finish(1, 1)
        h.expected_pixels = images['small'][1]
    elif name == 'reset-retains-bulk-and-ep0':
        h.transfer(small[:11]); h.step(7)
        old = h.arm_write(small[11:42])
        h.setup(packet(0xa1, 0, index=h.interface << 8, length=400))
        ep0 = h.row[28];h.wire(DEVICE_ID[:64], 'cancelled-id')
        h.setup(packet(0x21, 2, index=h.interface), service_result=WAIT)
        assert h.row[36] == 1 and h.row[14] == 6
        h.step(4, ep0);h.service()
        h.step(10)
        h.step(11, 0, 1, result=WAIT)
        h.step(11, 0, 2)
        h.step(12, result=WAIT)
        h.step(4, old)
        h.step(11, 0, 1, result=WAIT)
        h.service()
        assert h.row[81] == 0 and h.row[45] == 2
        h.finish_reset(already_output=True)
        h.complete(old, 0, usb_result=1, result=STALE, service=False)
        h.step(13, old, 0x200, result=STALE)
        fresh()
    elif name == 'superseded-deconfiguration-keeps-fence':
        old = h.arm_write(small[:31])
        h.setup(packet(0xa1, 0, index=h.interface << 8, length=400))
        ep0 = h.row[28];h.wire(DEVICE_ID[:64], 'cancelled-id')
        h.setup(packet(0, 9), service_result=WAIT)
        h.setup(packet(0x80, 0, length=2), service_result=WAIT)
        assert h.row[36] == h.row[10] == 1
        h.step(4, ep0);h.service();h.control_in(b'\x01\x00', 'standard-status')
        h.step(6, result=WAIT)
        h.step(4, old);h.service()
        assert h.row[10] == 1
        h.recover();fresh()
    elif name in ('deconfigure-with-owned-out', 'bus-reset-with-owned-out'):
        old = h.arm_write(small[:31])
        if name.startswith('deconfigure'):
            h.setup(packet(0, 9), service_result=WAIT)
        else:
            h.step(5);h.service(WAIT)
            h.step(0, 8, data=packet(0x80, 0, length=2), result=WAIT)
        h.step(6, result=WAIT)
        h.step(4, old);h.service()
        assert h.row[10] == h.row[8] == h.row[81] == 0
        if name.startswith('deconfigure'):
            h.control_status('deconfigure')
        h.request(packet(0, 9, 1))
        h.recover();fresh()
    elif name.startswith('halt-owned-out/'):
        address = int(name.rsplit('/', 1)[1])
        old = h.arm_write(small[:31])
        h.setup(packet(2, 3, index=address), service_result=WAIT)
        assert h.row[36] == 1 and h.row[11] == 0
        h.step(4, old);h.service();h.control_status('halt-out')
        assert h.row[82] == 1
        h.begin_reset();h.step(11, 0, 4, result=WAIT)
        h.finish_reset();fresh()
    elif name.startswith('failed-submit/'):
        mode = int(name.rsplit('/', 1)[1])
        h.step(14, mode);h.step(6, result=ERROR)
        assert h.row[36] == 1 and h.row[33:36] == [1, 0, 1]
        if mode == 2:
            old = h.row[30]
            assert old and h.row[14] == 4
            h.step(4, old);h.service()
        else:
            assert not h.row[30]
        h.recover();fresh()
    elif name.startswith('failed-completion/'):
        result = int(name.rsplit('/', 1)[1])
        h.transfer(small[:7])
        old = h.arm_write(small[7:31])
        h.complete(old, 24, usb_result=result, service=False)
        assert h.row[36] == 1 and h.row[34] == h.row[56] == 0
        h.step(7, result=STOPPED)
        h.service();h.recover();fresh()
    elif name in ('invalid-completion-result', 'oversized-completion'):
        old = h.arm_write(small[:31])
        h.complete(old, h.capacity+1 if name.startswith('oversized') else 31,
                   usb_result=0 if name.startswith('oversized') else 5, result=INVALID, service=False)
        assert h.row[30] == old and h.row[14] == 4 and h.row[36] == 1
        h.step(4, old);h.service();h.recover();fresh()
    elif name == 'close-waits-for-owned-out':
        assert len(small) <= h.capacity
        old = h.arm_write(small)
        h.step(8);h.step(9, result=WAIT);h.step(6, result=WAIT)
        h.complete(old, len(small));h.step(7);h.step(9, expect={40: 1, 57: 1, 58: 1})
        h.expected_pixels = images['small'][1]
    elif name == 'malformed-keeps-later-ready':
        h.transfer(b'JZJZ'+bytes(16))
        h.transfer(small[:31])
        h.step(7, result=PAYLOAD, expect={35: 2, 36: 1, 40: 0})
        h.step(7, result=STOPPED)
        h.recover();fresh()
    elif name.startswith('malformed-control-out/'):
        request = name.rsplit('/', 1)[1]
        raw = {
            'device-status': packet(0, 0, length=2),
            'configuration': packet(0, 8, length=1),
            'interface': packet(1, 10, index=h.interface, length=1),
            'descriptor': packet(0, 6, value=0x100, length=18),
            'endpoint-status': packet(2, 0, index=1, length=2),
            'class-reset': packet(0x21, 2, index=h.interface, length=1),
        }[request]
        old = h.arm_write(small[:31])
        before = h.row[32:42]
        h.setup(raw)
        assert h.row[32:42] == before and h.row[11] == 3 and h.row[13] == 4
        assert not h.row[26] and not h.row[28]
        h.request(packet(0xa1, 1, index=h.interface, length=1), b'\x18')
        h.complete(old, 31);h.step(7)
        h.send(small[31:], 64);h.close_finish(1, 1)
        h.expected_pixels = images['small'][1]
    elif name == 'malformed-out-waits-for-old-ep0':
        h.setup(packet(0xa1, 0, index=h.interface << 8, length=400))
        old = h.row[28];h.wire(DEVICE_ID[:64], 'cancelled-id')
        h.setup(packet(0, 0, length=2), service_result=WAIT)
        assert h.row[28] == old and h.row[11] == 0
        h.step(4, old);h.service()
        assert h.row[11] == 3 and not h.row[13] and not h.row[77]
        h.request(packet(0xa1, 1, index=h.interface, length=1), b'\x18')
        fresh()
    elif name.startswith('failed-follow-on/'):
        _, point, mode = name.split('/')
        mode = int(mode)
        after_recovery = point == 'after-recovery'
        if after_recovery:
            h.begin_reset()
        raw, data = (packet(0x80, 6, value=0x100, length=18), DEVICE) if point == 'standard-status' else (
            packet(0xa1, 0, index=h.interface << 8, length=400), DEVICE_ID)
        h.setup(raw)
        if after_recovery:
            old_ep0 = h.row[28]
            h.finish_reset(ack=False)
            assert h.row[28] == old_ep0 and h.row[88] < h.row[32]
        old_bulk = h.arm_write(small[:31])
        offset = 0
        if point in ('out-status', 'standard-status'):
            while len(data)-offset > 64:
                h.wire(data[offset:offset+64], 'completed-data')
                h.complete(h.row[28], 64)
                offset += 64
        length = min(64, len(data)-offset)
        h.wire(data[offset:offset+length], 'data-before-rejected-next-submission')
        token = h.row[28]
        h.step(14, mode)
        h.complete(token, length, service=False)
        h.service(ERROR)
        assert h.row[36] == 1 and h.row[14] & 4
        if mode == 2:
            pending = h.row[28] or h.row[26]
            assert pending and pending != token
            if h.row[28]:
                h.wire(data[offset+length:offset+length+64], 'accepted-but-rejected-next-data')
            h.step(4, pending);h.service()
        else:
            assert not h.row[26] and not h.row[28]
        h.step(4, old_bulk);h.service()
        h.recover();fresh()
    else:
        raise AssertionError(name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', action='store_true')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix='hp1020-tinyusb-printer-', dir='/tmp'))
    print('Reusable printer captures: '+str(temp), flush=True)
    tested = sources(temp)
    effective = runpy.run_path(str(ROOT/'scripts/prepare-hp1020-tinyusb.py'))['prepare'](temp/'effective-source', True)
    compile_host(temp, temp/'effective-source')
    document, images, fixtures = image_documents(temp)
    profiles = []
    for fill in (0, 204):
        for interface in (0, 3):
            for name in ('document/mixed/19', 'document/mixed/1024', 'document/consecutive',
                'status-and-id-during-owned-out', 'stale-completion-after-slot-reuse', 'reset-retains-bulk-and-ep0'):
                profiles.append((name, fill, 1024, interface))
        for name in ('superseded-deconfiguration-keeps-fence', 'deconfigure-with-owned-out', 'bus-reset-with-owned-out',
            'halt-owned-out/1', 'halt-owned-out/17', 'failed-submit/1', 'failed-submit/2',
            'failed-completion/1', 'failed-completion/2', 'failed-completion/3', 'failed-completion/4',
            'invalid-completion-result', 'oversized-completion', 'close-waits-for-owned-out', 'malformed-keeps-later-ready'):
            profiles.append((name, fill, 1024, 0))
        profiles.append(('document/consecutive', fill, 64, 3))
        for interface in (0, 3):
            profiles += [(f'malformed-control-out/{name}', fill, 1024, interface) for name in
                ('device-status', 'configuration', 'interface', 'descriptor', 'endpoint-status', 'class-reset')]
        profiles.append(('malformed-out-waits-for-old-ep0', fill, 1024, 3))
        profiles += [(f'failed-follow-on/{point}/{mode}', fill, 1024, 3) for point in
            ('middle-in', 'out-status', 'standard-status', 'after-recovery') for mode in (1, 2)]
    profiles.extend(automatic_recovery_profiles())
    profiles.extend(initial_standard_profiles())
    cases, replay = [], []
    for index, (name, fill, capacity, interface) in enumerate(profiles):
        directory = temp/f'case-{index:03}'
        directory.mkdir()
        title = f'{name}/fill={fill}/capacity={capacity}/interface={interface}'
        (directory/'case-name').write_text(title+'\n')
        h = Host(temp/'host', directory, fill, capacity, interface)
        try:
            scenario(h, name, document, images)
            captures = h.finish()
        finally:
            h.abort()
        cases.append(dict(case=title, scenario=name, fill=fill, capacity=capacity, interface=interface,
            status='pass', initial=h.initial, steps=h.rows, events=h.events, packet_oracles=h.packets,
            expected_pixels_sha256=core.sha(h.expected_pixels), pixels_bytes=len(h.expected_pixels),
            capture_sha256={n: core.sha(data) for n, data in captures.items()}))
        replay.append((h, captures, directory))
        print(f'Reusable printer: {len(cases)}/{len(profiles)} host cases passed', flush=True)
    target = None
    if args.target:
        core.command(['bash', ROOT/'scripts/build-hp1020-tinyusb-printer-target.sh'])
        elf = OUT/'target/target-check.elf'
        assert json.loads((OUT/'target/effective-source.json').read_text()) == effective
        shutil.copyfile(elf, temp/'target-check.elf')
        program, audit = core.audit_target(elf)
        from hp1020_qemu_ram import QemuRAM
        native = []
        with QemuRAM() as q:
            version = q.version
            for case, (h, captures, directory) in zip(cases, replay):
                q.load(elf)
                assert q.call0(program.symbols['hp1020_bulk_fixture_reset'],
                    [case['fill'], case['capacity'], case['interface'], 0xffffffff]) == 0
                initial = list(struct.unpack(f'>{STATS}I', q.read(program.symbols['hp1020_bulk_fixture_stats'], STATS*4)))
                assert initial[:59]+initial[60:] == h.initial[:59]+h.initial[60:]
                for index, (event, host_row) in enumerate(zip(h.events, h.rows)):
                    data = bytes.fromhex(event['data_hex'])
                    if data:
                        q.put(program.symbols['hp1020_bulk_fixture_input'], data)
                    result = q.call0(program.symbols['hp1020_bulk_fixture_step'], event['words'])
                    row = list(struct.unpack(f'>{STATS}I', q.read(program.symbols['hp1020_bulk_fixture_stats'], STATS*4)))
                    with (directory/'target-steps.jsonl').open('a') as saved:
                        saved.write(json.dumps(row)+'\n')
                    assert result == row[0] == event['result'] and row[15:17] == [0, 1]
                    assert row[:59]+row[60:] == host_row[:59]+host_row[60:], (case['case'], index, row, host_row)
                observed = {}
                for name, symbol in (('pixels', 'hp1020_bulk_fixture_pixels'), ('wire', 'hp1020_bulk_fixture_wire')):
                    observed[name] = q.read(program.symbols[symbol], len(captures[name]))
                for name, function in (('receive', 'hp1020_bulk_fixture_receive_storage'), ('output', 'hp1020_bulk_fixture_output_storage')):
                    address = q.call0(program.symbols[function], [])
                    observed[name] = q.read(address, len(captures[name]))
                for name, data in observed.items():
                    (directory/('target-'+name)).write_bytes(data)
                    assert data == captures[name], (case['case'], name)
                native.append(dict(case=case['case'], status='pass', all_steps_equal=True,
                    all_pixels_wire_and_storage_equal=True, component_state_and_memory_bytes=row[59],
                    capture_sha256={n: core.sha(data) for n, data in observed.items()}))
                print(f'Reusable printer: {len(native)}/{len(cases)} target cases passed', flush=True)
        target = dict(status='pass', cases=native, qemu_version=version, elf_sha256=core.sha(elf.read_bytes()), audit=audit)
    assert all(core.sha((ROOT/n).read_bytes()) == h for n, h in tested.items()), 'source changed during execution'
    report = dict(status='pass', source_sha256=tested, effective_source=effective, cases=cases, target=target,
        fixture_sha256={str(p.relative_to(ROOT)): core.sha(p.read_bytes()) for p in fixtures},
        completed_native_page_lifecycles=0, usb_transfers=0,
        scope='Patched pinned TinyUSB, reusable class/receive adapter and bounded document/JBIG/output composition under synthetic DCD events, with independent USB packet and decoded pixel oracles.',
        limits='No controller/MMIO/boot/cache implementation, physical status, USB traffic or printing. New configuration recovery requires three supplied promises without a fabricated class request. Legacy explicit reset and close paths remain covered. Cancellation, transfer settlement and output progress are synthetic; copies remain metadata. The separate continuous-printer experiment checks ordinary document boundaries without input closure.')
    name = 'validation' if args.target else 'host-validation'
    text = json.dumps(report, indent=2, sort_keys=True)+'\n'
    (temp/(name+'.json')).write_text(text)
    (OUT/(name+'.json')).write_text(text)
    (OUT/(name+'.md')).write_text('# Reusable USB printer execution\n\n'+report['scope']+'\n\n'+
        f'{len(cases)} host cases; {len(target["cases"]) if target else 0} target cases. Exact decoded pixels, retained buffers and packet proposals checked.\n\n'+report['limits']+'\n')


if __name__ == '__main__':
    main()
