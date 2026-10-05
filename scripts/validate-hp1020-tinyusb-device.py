#!/usr/bin/env python3
"""Synthetic TinyUSB device/control compatibility experiment; no USB hardware.

Unchanged and patched profiles are separate aggregate checks; upstream bytes stay pinned.
Submitted packet captures are not observed USB transfers or printing evidence.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import select
import runpy
import shutil
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('tusb_image_core', ROOT/'scripts/validate-hp1020-image-core.py')
core = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = core
spec.loader.exec_module(core)
SRC = ROOT/'open-firmware/tinyusb-device'
PRINTER = ROOT/'open-firmware/usb-printer-class'
RX = ROOT/'open-firmware/usb-receive-core'
IMG = ROOT/'open-firmware/image-core'
SEM = ROOT/'open-firmware/semantic-core'
UPSTREAM = ROOT/'vendor/tinyusb-0.21.0'
OUT = ROOT/'analysis/usb-path/tinyusb-device'
PIN = 'dae3f9a366bfcddbf9dcf1b48d7500286a849539'
OK, WAIT, STALE, INVALID, LIMIT, FAIL = range(6)
STATS = 72
DEVICE = bytes.fromhex('1201000200000040feca0040000100000001')
DEVICE_ID = b'\x01\x90' + bytes(65 + i % 26 for i in range(398))


def config_descriptor(interface, powered=1):
    total = 32 + 9 * interface
    return bytes([9, 2, total, 0, interface + 1, 1, 0, 0xe0 if powered else 0xa0, 50]) + b''.join(
        bytes([9, 4, i, 0, 0, 0xff, 0, 0, 0]) for i in range(interface)) + bytes(
        [9, 4, interface, 0, 2, 7, 1, 2, 0]) + bytes.fromhex('07050102400000 07058102400000')


def packet(kind, request, value=0, index=0, length=0):
    return struct.pack('<BBHHH', kind, request, value, index, length)


class Host:
    def __init__(self, executable, directory, fill, interface, id_length, powered, patched):
        self.directory = directory
        self.stderr = (directory/'stderr').open('wb')
        self.powered, self.patched = powered, patched
        self.process = subprocess.Popen([str(executable), str(fill), str(interface), str(id_length), str(powered), str(directory/'capture')],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.stderr)
        self.row = self.read_row()
        self.initial = self.row.copy()
        assert self.row[11:13] == [0, 1], self.row
        self.requested = 0
        self.events, self.rows, self.packets, self.findings = [], [], [], []

    def read_row(self):
        ready, _, _ = select.select([self.process.stdout], [], [], 20)
        if not ready:
            self.process.kill()
            self.process.wait()
            raise AssertionError('host protocol fixture timed out; ' + str(self.directory))
        raw = self.process.stdout.readline()
        with (self.directory/'raw-stdout').open('ab') as saved:
            saved.write(raw)
        if not raw:
            raise AssertionError('host fixture ended early; ' + str(self.directory))
        row = json.loads(raw)
        assert len(row) == STATS, row
        return row

    def step(self, op, a=0, b=0, c=0, d=0, data=b'', result=OK, expect=None):
        values = [op, a, b, c, d]
        wire = struct.pack('>6I', *values, len(data)) + data
        before = self.row.copy()
        with (self.directory/'events.bin').open('ab') as saved:
            saved.write(wire)
        self.process.stdin.write(wire)
        self.process.stdin.flush()
        self.row = self.read_row()
        self.events.append(dict(words=values, data_hex=data.hex(), result=result))
        self.rows.append(self.row.copy())
        # Preserve raw observations even if the fixture or expectation is wrong.
        (self.directory/'host-steps.json').write_text(json.dumps(self.rows) + '\n')
        assert self.row[11:13] == [0, 1] and self.row[61] == self.initial[61], ('ownership/memory', self.row)
        assert self.row[0] == result, (len(self.rows) - 1, values, self.row, result)
        assert all(self.row[int(at)] == value for at, value in (expect or {}).items()), (values, self.row, expect)
        assert before[5] <= self.row[5] <= before[5] + 1, ('unmodeled multiple submissions', self.row)
        if op == 0 and result in (OK, WAIT):
            self.requested = struct.unpack_from('<H', data, 6)[0]
        return self.row

    def expected_submission(self, data, label, upstream_be=None):
        """Record an independent expected packet at the latest submitted offset."""
        row = self.row
        assert row[15] == 0x80 and row[16] == len(data)
        assert row[13] >= len(data)
        item = dict(step=len(self.rows)-1, offset=row[13]-len(data), length=len(data),
                    expected_hex=data.hex(), label=label, upstream_be_hex=None if upstream_be is None else upstream_be.hex())
        self.packets.append(item)

    def complete(self, endpoint, result=OK, usb_result=0, token=None, length=None):
        at = 23 if endpoint == 0x80 else 20
        token = self.row[at] if token is None else token
        length = self.row[at + 1] if length is None else length
        assert token
        return self.step(1, endpoint, token, length, usb_result, result=result)

    def settle_in(self, expected, label, upstream_be=None):
        """Drain an IN DATA request and its OUT status packet using original tokens."""
        assert 0 < self.requested == self.row[52] and len(expected) <= self.requested
        lengths = [min(64, len(expected) - at) for at in range(0, len(expected), 64)]
        if len(expected) < self.requested and len(expected) % 64 == 0:
            lengths.append(0)  # Exactly one terminating data ZLP is required.
        offset = 0
        for length in lengths:
            assert self.row[23] and self.row[24] == length, ('packet-length sequence', lengths, self.row)
            fragment = expected[offset:offset + length]
            alternate = None if upstream_be is None else upstream_be[offset:offset + length]
            self.expected_submission(fragment, label, alternate)
            offset += length
            self.complete(0x80)
            assert offset <= len(expected)
        assert offset == len(expected) and not self.row[23] and self.row[20] and self.row[21] == 0
        self.complete(0)
        assert not self.row[20] and not self.row[23]

    def no_data_status(self, label):
        assert self.row[23] and self.row[24] == 0
        self.expected_submission(b'', label)
        self.complete(0x80)
        assert not self.row[20] and not self.row[23]

    def request(self, raw, expected=None, label='control', upstream_be=None, known=0, status=0, status_request_override=None):
        before = self.row[5]
        self.step(0, 8, known, status, data=raw)
        assert self.row[5] == before + 1
        if expected is None or struct.unpack_from('<H', raw, 6)[0] == 0:
            self.no_data_status(label)
        else:
            self.settle_in(expected, label, upstream_be)
        request_fields = list(struct.unpack('<BBHHH', raw)) if status_request_override is None else status_request_override
        assert self.row[64:69] == request_fields, ('completed request changed', self.row[64:69], request_fields)

    def finish(self):
        self.process.stdin.close()
        assert self.process.wait(timeout=20) == 0
        self.process.stdout.close()
        self.stderr.close()
        capture = (self.directory/'capture').read_bytes()
        assert len(capture) == self.row[13] and core.fnv(capture) == self.row[14]
        covered = bytearray(len(capture))
        for p in self.packets:
            begin, end = p['offset'], p['offset'] + p['length']
            expected = bytes.fromhex(p['expected_hex'])
            assert capture[begin:end] == expected, (p, capture[begin:end].hex())
            assert not any(covered[begin:end])
            covered[begin:end] = bytes([1]) * p['length']
        assert all(covered), 'Every submitted IN byte needs a separate wire oracle'
        return capture

    def abort(self):
        if self.process.stdin and not self.process.stdin.closed:
            self.process.stdin.close()
        try:
            self.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
        self.process.stdout.close()
        self.stderr.close()


def upstream_sources():
    provenance = json.loads((UPSTREAM/'PROVENANCE.json').read_text())
    assert provenance['commit'] == PIN and not provenance['local_changes']
    assert len(provenance['upstream_files']) == 19
    paths = []
    for name, record in provenance['upstream_files'].items():
        path = UPSTREAM/name
        assert core.sha(path.read_bytes()) == record['sha256'], name
        paths.append(path)
    return provenance, paths


def source_snapshot(temp, paths):
    paths = set(paths) | set(SRC.glob('*.[ch]')) | set(SRC.glob('*.ld'))
    paths.update((SRC/'freestanding').glob('*.h'))
    paths.update((SRC/'patches').glob('*'))
    paths.update((UPSTREAM/'PROVENANCE.json',))
    paths.update(PRINTER/n for n in ('hp1020_usb_printer.c', 'hp1020_usb_printer.h'))
    paths.update(RX/n for n in ('hp1020_usb_receive.c', 'hp1020_usb_receive.h', 'hp1020_usb_document.c', 'hp1020_usb_document.h'))
    paths.update(IMG/(stem + suffix) for stem in ('hp1020_image', 'hp1020_image_page', 'hp1020_image_stream',
                 'hp1020_image_ring', 'hp1020_image_output') for suffix in ('.c', '.h'))
    paths.add(IMG/'target-memory.c')
    paths.update((IMG/'freestanding').glob('*.h'))
    paths.update(SEM.rglob('*.c'))
    paths.update(SEM.rglob('*.h'))
    paths.update((core.VENDOR/'libjbig').glob('*.h'))
    paths.update(core.VENDOR/'libjbig'/n for n in ('jbig85.c', 'jbig_ar.c'))
    paths.update(ROOT/'scripts'/n for n in ('validate-hp1020-tinyusb-device.py', 'build-hp1020-tinyusb-target.sh',
        'prepare-hp1020-tinyusb.py',
        'validate-hp1020-image-core.py', 'check-hp1020-c-compiler-profile.py', 'hp1020_qemu_ram.py',
        'hp1020_xtensa_call0.py', 'hp1020_xtensa_properties.py'))
    paths.update(ROOT/'open-firmware/image-pump'/('hp1020_image_pump'+ext) for ext in ('.c', '.h'))
    hashes = {str(p.relative_to(ROOT)): core.sha(p.read_bytes()) for p in sorted(paths)}
    for name in hashes:
        saved = temp/'source'/name
        saved.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT/name, saved)
    (temp/'source-sha256.json').write_text(json.dumps(hashes, indent=2) + '\n')
    return hashes


def compile_host(temp, source, patched):
    sources = [SRC/'fixture.c', SRC/'host-check.c', PRINTER/'hp1020_usb_printer.c',
               RX/'hp1020_usb_receive.c', RX/'hp1020_usb_document.c']
    sources += [IMG/n for n in ('hp1020_image.c', 'hp1020_image_page.c', 'hp1020_image_stream.c',
                              'hp1020_image_ring.c', 'hp1020_image_output.c')]
    sources += [ROOT/'open-firmware/image-pump/hp1020_image_pump.c']
    sources += [SEM/'hp1020_semantic.c', SEM/'hp1020_page_plan.c',
                core.VENDOR/'libjbig/jbig85.c', core.VENDOR/'libjbig/jbig_ar.c']
    sources += [source/'src'/n for n in ('tusb.c', 'device/usbd.c', 'common/tusb_fifo.c')]
    flags = ['clang', '-std=c11', '-O1', '-g', '-fno-common', '-Wall', '-Wextra', '-Werror',
             '-fsanitize=address,undefined', f'-DHP1020_TUSB_PATCHED={int(patched)}']
    includes = ['-I' + str(p) for p in (SRC, PRINTER, RX, IMG, SEM, core.VENDOR/'libjbig', source/'src')]
    core.command(flags + includes + sources + ['-o', temp/'host'])


def configure(h):
    h.step(3)
    h.request(packet(0, 9, 1), label='set-configuration')
    assert h.row[46] == 1 and h.row[50] == 15


def reset_request(h, interface, kind=0x21):
    previous = h.row[5]
    h.step(0, 8, data=packet(kind, 2, index=interface), expect={34: 1, 35: 0, 37: 1, 41: 1})
    assert h.row[5] == previous and h.row[40] == h.row[2]


def ack_reset(h):
    generation = h.row[36]
    h.step(6, result=WAIT)
    for part in (1, 4):
        h.step(5, part)
        h.step(6, result=WAIT)
    h.step(5, 2)
    h.step(6, expect={36: generation + 1, 37: 0, 41: 0})
    h.no_data_status('deferred-reset-status')


def scenario(h, name, interface):
    if name == 'enumeration-and-standard-status':
        h.step(3)
        h.request(packet(0x80, 6, 0x100, length=8), DEVICE[:8], 'device-first-eight')
        h.request(packet(0x80, 6, 0x100, length=256), DEVICE, 'device-descriptor')
        h.request(packet(0, 5, 7), label='set-address')
        assert h.row[47] == 7
        descriptor = config_descriptor(interface, h.powered)
        h.request(packet(0x80, 6, 0x200, length=9), descriptor[:9], 'configuration-header')
        h.request(packet(0x80, 6, 0x200, length=255), descriptor, 'configuration-descriptor')
        h.request(packet(0, 9, 1), label='set-configuration')
        assert h.row[46] == 1 and h.row[50] == 15
        h.request(packet(0x80, 8, length=1), b'\x01', 'get-configuration')
        h.request(packet(0x80, 6, 0x300, length=255), bytes.fromhex('04030904'), 'language-string-descriptor')
        h.request(packet(0x80, 0, length=2), bytes([h.powered, 0]), 'self-powered-status', bytes([0, 0x80 if h.powered else 0]))
        h.request(packet(0, 3, 1), label='enable-remote-wakeup')
        h.request(packet(0x80, 0, length=2), bytes([h.powered | 2, 0]), 'remote-wakeup-status', bytes([0, 0xc0 if h.powered else 0x40]))
        h.request(packet(0, 1, 1), label='disable-remote-wakeup')
        h.request(packet(0x80, 0, length=2), bytes([h.powered, 0]), 'cleared-remote-wakeup-status', bytes([0, 0x80 if h.powered else 0]))
        h.request(packet(2, 3, index=0x81), label='halt-bulk-in')
        assert h.row[10] & 8
        h.request(packet(0x82, 0, index=0x81, length=2), b'\x01\x00', 'halted-endpoint-status', b'\x00\x01')
        h.request(packet(2, 1, index=0x81), label='clear-bulk-halt')
        assert not h.row[10] & 8
        h.request(packet(0x82, 0, index=0x81, length=2), bytes(2), 'unhalted-endpoint-status')
        h.request(packet(2, 3, index=1), label='halt-bulk-out')
        assert h.row[10] & 4
        h.request(packet(0x82, 0, index=1, length=2), b'\x01\x00', 'halted-out-endpoint-status', b'\x00\x01')
        h.request(packet(2, 1, index=1), label='clear-bulk-out-halt')
        assert not h.row[10] & 4
        h.request(packet(0x82, 0, index=1, length=2), bytes(2), 'unhalted-out-endpoint-status')
        return

    if name == 'cancel-address-status':
        h.step(3)
        h.step(0, 8, data=packet(0, 5, 7), expect={47: 0, 48: 7})
        h.expected_submission(b'', 'cancelled-address-status')
        old_token = h.row[23]
        h.step(0, 8, data=packet(0x80, 6, 0x100, length=9), result=WAIT, expect={47: 0})
        h.step(2, 0x80, old_token, expect={47: 0, 48: 0})
        h.step(4)
        h.settle_in(DEVICE[:9], 'descriptor-after-address-cancel')
        h.request(packet(0, 5, 9), label='new-address-status')
        assert h.row[47] == 9
        h.complete(0x80, token=old_token, length=0, result=STALE)
        assert h.row[47] == 9
        return

    configure(h)
    if name == 'configuration-reset-preserves-control-request':
        h.request(packet(0, 9, 0), label='deconfigure', status_request_override=None if h.patched else [0]*5)
        assert not h.row[46] and h.row[37]
        if not h.patched:
            h.findings.append(dict(kind='configuration_reset_erases_control_request',
                expected='status completion retains SET_CONFIGURATION request 00/09/0000/0000/0000',
                observed='configuration reset zeroes the current request before status completion'))
        h.request(packet(0, 9, 1), label='reconfigure')
        assert h.row[46] and h.row[37]
        # A nonzero SET_CONFIGURATION is an endpoint-default reset even when
        # selecting the current value (USB2 sections9.1.1.5 and9.4.5). Both
        # endpoint halts are established through ordinary core requests first.
        h.request(packet(2, 3, index=1), label='halt-out-before-same-configuration')
        h.request(packet(2, 3, index=0x81), label='halt-in-before-same-configuration')
        assert h.row[10] == 12 and h.row[50] == 15 and not h.row[9]
        resets_before = h.row[49]
        h.request(packet(0, 9, 1), label='same-configuration')
        # printer_reset increments49 and resets openmap50 to literal3. Reaching
        # map15 again therefore requires actual endpoint open callbacks. No
        # clear-halt request is injected between the selection and these checks.
        assert h.row[46] == 1 and h.row[50] == 15 and not h.row[9]
        if h.patched:
            assert h.row[49] == resets_before+1 and h.row[10] == 0
        else:
            assert h.row[49] == resets_before and h.row[10] == 12
            h.findings.append(dict(kind='repeated_nonzero_configuration_preserves_endpoint_halt',
                expected='same nonzero SET_CONFIGURATION resets/reopens endpoints and clears both Halt features',
                observed='unchanged core skips reset/reopen and retains both bulk Halt features',
                driver_resets_before=resets_before, driver_resets_after=h.row[49],
                open_endpoint_mask=h.row[50], halt_mask_after=h.row[10]))
        # Query the core's own two-byte endpoint status, independently of the
        # synthetic DCD mask. Preserve the explicit unchanged-core BE defect;
        # the patched target must return the exact little-endian USB bytes.
        status = bytes(2) if h.patched else b'\x01\x00'
        upstream_be = None if h.patched else b'\x00\x01'
        h.request(packet(0x82, 0, index=1, length=2), status,
            'out-status-after-same-configuration', upstream_be)
        h.request(packet(0x82, 0, index=0x81, length=2), status,
            'in-status-after-same-configuration', upstream_be)
        h.request(packet(0x80, 8, length=1), b'\x01', 'configuration-after-reconfigure')
        return

    if name == 'id-multiple-of-packet-shorter-than-request':
        device_id = b'\x01\x80' + bytes(65 + i % 26 for i in range(382))
        for length in (384, 512, 65535):
            h.request(packet(0xa1, 0, length=length), device_id, f'multiple-id-{length}')
        return

    if name in ('running-document-soft-reset-admission', 'running-document-bus-reset-admission'):
        reset_request(h, interface)
        ack_reset(h)
        generation = h.row[36]
        h.step(0, 8, data=packet(0xa1, 1, index=interface, length=1), b=1, c=8)
        h.expected_submission(b'\x08', 'held-status-before-reset-admission')
        old_token, submissions = h.row[23], h.row[5]
        assert not h.row[37]
        if name == 'running-document-soft-reset-admission':
            h.step(0, 8, data=packet(0x21, 2, index=interface), result=WAIT,
                   expect={37: 1, 36: generation, 3: 1, 5: submissions, 23: old_token})
            h.complete(0x80, token=old_token, length=1, result=STALE)
            assert h.row[34] and h.row[41] and h.row[36] == generation
            ack_reset(h)
        else:
            h.step(3, result=WAIT,
                   expect={37: 1, 36: generation, 3: 2, 5: submissions, 23: old_token})
            h.complete(0x80, token=old_token, length=1, result=STALE)
            assert not h.row[46] and h.row[37] and h.row[36] == generation
            h.request(packet(0, 9, 1), label='reconfigure-after-running-reset')
            reset_request(h, interface)
            ack_reset(h)
        return

    if name == 'queued-reset-invalidates-old-promises':
        reset_request(h, interface)
        for part in (1, 2, 4):
            h.step(5, part)
        assert h.row[35] == 7
        h.step(0, 8, data=packet(0x80, 6, 0x100, length=9))
        h.expected_submission(DEVICE[:9], 'held-standard-request-between-resets')
        old_token, submissions = h.row[23], h.row[5]
        h.step(0, 8, data=packet(0x21, 2, index=interface), result=WAIT,
               expect={34: 0, 35: 0, 37: 1, 3: 1, 5: submissions, 23: old_token})
        h.step(6, result=STALE, expect={37: 1, 5: submissions})
        h.step(2, 0x80, old_token)
        assert h.row[34] and h.row[41] and not h.row[35]
        ack_reset(h)
        return

    if name == 'class-routing-and-packetization':
        h.request(packet(0xa1, 1, index=interface, length=1), b'\x38', 'known-printer-status', known=1, status=0x38)
        assert h.row[56:61] == [0xa1, 1, 0, interface, 1]
        if interface == 0 or h.patched:
            for length in (0, 1, 64, 128, 400, 65535):
                h.request(packet(0xa1, 0, index=interface << 8, length=length), DEVICE_ID[:length], f'device-id-{length}')
                assert h.row[56:61] == [0xa1, 0, 0, interface << 8, length]
        else:
            before = h.row.copy()
            h.step(0, 8, data=packet(0xa1, 0, index=interface << 8, length=400))
            assert h.row[26] == before[26] and h.row[29] == before[29] + 1
            assert h.row[5] == before[5] and h.row[10] & 3 == 3 and not h.row[9]
            h.findings.append(dict(kind='unsupported_custom_driver_high_byte_interface',
                expected='GET_DEVICE_ID reaches printer interface 3', observed='dummy interface 0 selected, EP0 stalled'))
        if h.patched:
            reset_request(h, interface, 0x23)
            assert h.row[56:61] == [0x23, 2, 0, interface, 0]
            ack_reset(h)
        else:
            before = h.row.copy()
            h.step(0, 8, data=packet(0x23, 2, index=interface))
            assert h.row[26] == before[26] and h.row[5] == before[5] and h.row[10] & 3 == 3
            h.findings.append(dict(kind='unsupported_legacy_reset_recipient',
                expected='legacy 0x23 reset reaches printer class', observed='no printer callback, EP0 stalled'))
        h.request(packet(0xa1, 1, index=interface, length=1), b'\x18', 'unknown-printer-status')
        reset_request(h, interface)
        ack_reset(h)
        return

    if name == 'deferred-reset':
        reset_request(h, interface)
        ack_reset(h)
        assert h.row[43] == 1 and not h.row[32]
        return

    if name == 'reset-superseded-by-standard-setup':
        reset_request(h, interface)
        generation = h.row[36]
        h.step(5, 1)
        h.step(5, 2)
        h.step(0, 8, data=packet(0x80, 6, 0x100, length=9), expect={41: 0, 42: 1})
        submissions = h.row[5]
        h.step(5, 4)
        h.step(6, expect={36: generation + 1, 37: 0, 41: 0})
        assert h.row[5] == submissions, 'reset submitted status into a newer standard control transfer'
        h.settle_in(DEVICE[:9], 'new-standard-request-survives-old-reset')
        h.request(packet(0x80, 8, length=1), b'\x01', 'configuration-after-superseded-reset')
        return

    if name == 'held-packet-new-setup-and-late-completion':
        h.step(0, 8, data=packet(0xa1, 1, index=interface, length=1), b=1, c=8)
        h.expected_submission(b'\x08', 'old-held-status')
        old_token, submissions = h.row[23], h.row[5]
        h.step(0, 8, data=packet(0xa1, 1, index=interface, length=1), b=1, c=0x30,
               result=WAIT, expect={3: 1, 23: old_token, 5: submissions})
        h.step(4, result=WAIT)
        h.complete(0x80, token=old_token + 1000, length=1, result=STALE)
        h.complete(0x80, token=old_token, length=1, result=STALE)
        h.step(4)
        new_token = h.row[23]
        assert new_token and new_token != old_token
        h.complete(0x80, token=old_token, length=1, result=STALE)
        assert h.row[23] == new_token
        h.settle_in(b'\x30', 'new-status-after-old-reads-settle')
        return

    if name == 'superseded-multipacket-id' or name == 'bus-reset-with-held-packet':
        assert interface == 0
        h.step(0, 8, data=packet(0xa1, 0, length=400))
        h.expected_submission(DEVICE_ID[:64], 'old-id-first-packet')
        old_token, submissions = h.row[23], h.row[5]
        if name == 'superseded-multipacket-id':
            h.step(0, 8, data=packet(0x80, 6, 0x100, length=9), result=WAIT, expect={5: submissions, 3: 1})
            h.step(2, 0x80, old_token)
            h.step(4)
            h.complete(0x80, token=old_token, length=64, result=STALE)
            h.settle_in(DEVICE[:9], 'descriptor-after-cancelled-multipacket-id')
        else:
            h.step(3, result=WAIT, expect={5: submissions, 3: 2})
            epoch = h.row[2]
            h.step(0, 8, data=packet(0x80, 6, 0x100, length=8), result=INVALID,
                   expect={2: epoch, 3: 2, 5: submissions})
            h.complete(0x80, token=old_token, length=64, result=STALE)
            h.step(4, expect={46: 0, 47: 0, 50: 3, 37: 1, 32: 0})
            h.request(packet(0x80, 6, 0x100, length=18), DEVICE, 'descriptor-after-bus-reset')
        return

    if name == 'upstream-ignored-failed-ep0-result':
        h.step(0, 8, data=packet(0xa1, 1, index=interface, length=1), b=1, c=0x28)
        h.expected_submission(b'\x28', 'failed-status-data-packet')
        before = h.row.copy()
        h.complete(0x80, usb_result=1, length=0)
        if h.patched:
            assert not h.row[9] and h.row[10] & 3 == 3 and h.row[5] == before[5]
            assert h.row[28] == before[28] and h.row[32]
        else:
            assert h.row[20] and h.row[21] == 0 and h.row[5] == before[5] + 1
            h.complete(0)
            assert h.row[28] == before[28] + 1 and not h.row[32]
            h.findings.append(dict(kind='ignored_current_ep0_failure',
                expected='failed data stage must not advance to successful control status',
                observed='upstream schedules OUT status and invokes class ACK after failed IN result with zero reported bytes'))
        return

    if name == 'claimed-routing-rejection-is-final':
        assert h.patched
        for raw in (packet(0xa1, 0, value=1, index=interface<<8, length=20),
                    packet(0xa1, 0, index=(interface<<8)|1, length=20),
                    packet(0x23, 2, value=1, index=interface),
                    packet(0x23, 2, index=interface, length=1)):
            before = h.row.copy()
            h.step(0, 8, data=raw)
            assert h.row[26] == before[26]+1 and h.row[29] == before[29]
            assert h.row[71] == before[71]+1 and h.row[5] == before[5] and h.row[10] & 3 == 3
            assert h.row[56:61] == list(struct.unpack('<BBHHH', raw))
        # No route or successful callback for unrelated recipients/types.
        for raw in (packet(0xa3, 1, index=interface, length=1), packet(0xc1, 0, index=interface, length=1)):
            before = h.row.copy()
            h.step(0, 8, data=raw)
            assert h.row[26] == before[26] and h.row[71] == before[71]
            assert h.row[5] == before[5] and h.row[10] & 3 == 3
        h.request(packet(0, 9, 0), label='deconfigure-before-class-request')
        before = h.row.copy()
        h.step(0, 8, data=packet(0xa1, 0, index=interface<<8, length=20))
        assert h.row[26] == before[26] and h.row[29] == before[29]
        assert h.row[71] == before[71]+1 and h.row[5] == before[5] and h.row[10] & 3 == 3
        return

    if name == 'late-failure-does-not-stop-current-generation':
        assert h.patched
        reset_request(h, interface)
        ack_reset(h)
        h.step(0, 8, data=packet(0xa1, 1, index=interface, length=1), b=1, c=8)
        h.expected_submission(b'\x08', 'old-status-before-late-failure')
        token, fences = h.row[23], h.row[70]
        h.step(0, 8, data=packet(0xa1, 1, index=interface, length=1), b=1, c=0x30, result=WAIT)
        h.complete(0x80, token=token, length=0, usb_result=1, result=STALE)
        new_token = h.row[23]
        assert new_token != token and not h.row[37] and h.row[70] == fences
        h.complete(0x80, token=token, length=0, usb_result=5, result=STALE)
        assert h.row[23] == new_token and not h.row[37] and h.row[70] == fences
        h.settle_in(b'\x30', 'current-request-survives-old-failure')
        return

    if name.startswith('failed-ep0/'):
        assert h.patched
        _, stage, result_text = name.split('/')
        usb_result = int(result_text)
        reset_request(h, interface)
        ack_reset(h)
        if stage in ('first-in', 'out-status'):
            h.step(0, 8, data=packet(0xa1, 1, index=interface, length=1), b=1, c=0x28)
            h.expected_submission(b'\x28', 'status-before-failure')
            if stage == 'out-status':
                h.complete(0x80)
        elif stage == 'middle-in':
            h.step(0, 8, data=packet(0xa1, 0, index=interface<<8, length=400))
            h.expected_submission(DEVICE_ID[:64], 'successful-first-id-packet')
            h.complete(0x80)
            h.expected_submission(DEVICE_ID[64:128], 'failed-second-id-packet')
        elif stage == 'in-status':
            h.step(0, 8, data=packet(0, 5, 7))
            h.expected_submission(b'', 'failed-address-status')
        elif stage == 'reset-status':
            reset_request(h, interface)
            for part in (1, 2, 4):
                h.step(5, part)
            h.step(6)
            assert h.row[36] == h.row[45]+1 and not h.row[37]
            h.expected_submission(b'', 'failed-reset-status-after-generation-advance')
        else:
            raise AssertionError(stage)
        before = h.row.copy()
        h.complete(0 if stage == 'out-status' else 0x80, usb_result=usb_result, length=0)
        assert not h.row[9] and h.row[10] & 3 == 3 and h.row[5] == before[5]
        assert h.row[27:29] == before[27:29] and h.row[64:69] == before[64:69]
        assert h.row[37] and h.row[69] == before[36] and h.row[70] == before[70]+1
        if stage == 'in-status':
            assert h.row[47] == 0
        h.step(7, result=WAIT, expect={5: before[5]})
        h.step(7, 1, result=WAIT, expect={5: before[5]})
        if stage == 'reset-status':
            h.step(6, result=STALE)
        h.request(packet(0x80, 6, 0x100, length=18), DEVICE, 'fresh-setup-after-failure')
        assert h.row[37], 'new control request must not erase the document stop fence'
        reset_request(h, interface)
        ack_reset(h)
        return
    raise AssertionError(name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', action='store_true')
    parser.add_argument('--patched', action='store_true')
    args = parser.parse_args()
    assert sys.byteorder == 'little', 'baseline host oracle expects this checked little-endian build'
    OUT.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix='hp1020-tinyusb-', dir='/tmp'))
    print(f'TinyUSB {"patched" if args.patched else "upstream-baseline"} captures: {temp}', flush=True)
    provenance, upstream = upstream_sources()
    tested = source_snapshot(temp, upstream)
    effective = runpy.run_path(str(ROOT/'scripts/prepare-hp1020-tinyusb.py'))['prepare'](temp/'effective-source', args.patched)
    compile_host(temp, temp/'effective-source', args.patched)
    cases = []
    profiles = []
    for fill in (0, 204):
        for interface in (0, 3):
            profiles += [(name, fill, interface, 400, 1) for name in (
                'enumeration-and-standard-status', 'class-routing-and-packetization', 'deferred-reset',
                'configuration-reset-preserves-control-request',
                'reset-superseded-by-standard-setup', 'held-packet-new-setup-and-late-completion',
                'running-document-soft-reset-admission', 'running-document-bus-reset-admission',
                'queued-reset-invalidates-old-promises',
                'upstream-ignored-failed-ep0-result')]
            profiles.append(('enumeration-and-standard-status', fill, interface, 400, 0))
            if args.patched:
                profiles += [(name, fill, interface, 400, 1) for name in (
                    'claimed-routing-rejection-is-final', 'late-failure-does-not-stop-current-generation')]
                profiles += [(f'failed-ep0/{stage}/{result}', fill, interface, 400, 1)
                    for stage in ('first-in', 'middle-in', 'out-status', 'in-status', 'reset-status')
                    for result in range(1, 6)]
        profiles += [(name, fill, 0, 400, 1) for name in ('cancel-address-status', 'superseded-multipacket-id', 'bus-reset-with-held-packet')]
        profiles.append(('id-multiple-of-packet-shorter-than-request', fill, 0, 384, 1))
    replay = []
    for index, (name, fill, interface, id_length, powered) in enumerate(profiles):
        directory = temp/f'case-{index:02}'
        directory.mkdir()
        title = f'{name}/interface={interface}/fill={fill}/id_length={id_length}/self_powered={powered}'
        (directory/'case-name').write_text(title + '\n')
        h = Host(temp/'host', directory, fill, interface, id_length, powered, args.patched)
        try:
            assert h.initial[0:2] == [0, 0]
            scenario(h, name, interface)
            captured = h.finish()
        finally:
            h.abort()
        cases.append(dict(case=title, scenario=name, fill=fill, interface=interface, id_length=id_length, self_powered=powered,
            host_status='observed_upstream_limitation' if h.findings else 'pass',
            initial=h.initial, steps=h.rows, events=h.events, packet_oracles=h.packets,
            source_based_limitations=h.findings, capture_bytes=len(captured), capture_sha256=core.sha(captured)))
        replay.append((h, captured, directory))
    print(f'TinyUSB: {len(cases)} host scenarios checked; patched={args.patched}', flush=True)
    target = None
    if args.target:
        core.command(['bash', ROOT/'scripts/build-hp1020-tinyusb-target.sh'] + (['--patched'] if args.patched else []))
        target_dir = OUT/('patched-target' if args.patched else 'target')
        assert json.loads((target_dir/'effective-source.json').read_text()) == effective
        elf = target_dir/'target-check.elf'
        shutil.copyfile(elf, temp/'target-check.elf')
        program, audit = core.audit_target(elf)
        from hp1020_qemu_ram import QemuRAM
        native = []
        with QemuRAM() as q:
            version = q.version
            for case, (h, host_capture, directory) in zip(cases, replay):
                q.load(elf)  # A fresh synthetic world, matching the fresh host process.
                assert q.call0(program.symbols['hp1020_tusb_fixture_reset'], [case['fill'], case['interface'], case['id_length'], case['self_powered']]) == 0
                initial = list(struct.unpack(f'>{STATS}I', q.read(program.symbols['hp1020_tusb_fixture_stats'], STATS*4)))
                assert initial[:55] + initial[56:] == h.initial[:55] + h.initial[56:]
                steps = []
                for index, (event, host_row) in enumerate(zip(h.events, h.rows)):
                    data = bytes.fromhex(event['data_hex'])
                    if data:
                        q.put(program.symbols['hp1020_tusb_fixture_input'], data)
                    result = q.call0(program.symbols['hp1020_tusb_fixture_step'], event['words'])
                    row = list(struct.unpack(f'>{STATS}I', q.read(program.symbols['hp1020_tusb_fixture_stats'], STATS*4)))
                    steps.append(row)
                    (directory/'target-steps.json').write_text(json.dumps(steps) + '\n')
                    assert result == row[0] == event['result'] and row[11:13] == [0, 1]
                    assert row[61] == initial[61], ('target document storage changed', case['case'], index)
                    # Capture/packet hashes may differ only at explicitly specified
                    # upstream BE wire defects. Exact packet bytes are checked below.
                    assert all(row[i] == host_row[i] for i in range(STATS) if i not in (14, 19, 55)), (case['case'], index, row, host_row)
                capture = q.read(program.symbols['hp1020_tusb_fixture_capture'], steps[-1][13])
                (directory/'target-capture').write_bytes(capture)
                assert core.fnv(capture) == steps[-1][14]
                findings = []
                for p in h.packets:
                    observed = capture[p['offset']:p['offset'] + p['length']]
                    expected = bytes.fromhex(p['expected_hex'])
                    if observed != expected:
                        assert not args.patched, ('patched target must match USB wire oracle', case['case'], p, observed.hex())
                        assert p['upstream_be_hex'] is not None and observed.hex() == p['upstream_be_hex'], (case['case'], p, observed.hex())
                        findings.append(dict(kind='upstream_big_endian_wire_mismatch', label=p['label'],
                                             expected_hex=expected.hex(), observed_hex=observed.hex()))
                if not findings:
                    assert capture == host_capture
                native.append(dict(case=case['case'], status='observed_upstream_limitation' if findings or h.findings else 'pass',
                    all_nonwire_states_equal=True, capture_bytes=len(capture), capture_sha256=core.sha(capture),
                    wire_mismatches=findings, component_state_and_memory_bytes=steps[-1][55]))
                print(f'TinyUSB: {len(native)}/{len(cases)} target scenarios checked; patched={args.patched}', flush=True)
        target = dict(cases=native, qemu_version=version, elf_sha256=core.sha(elf.read_bytes()), audit=audit)
    assert all(core.sha((ROOT/name).read_bytes()) == digest for name, digest in tested.items()), 'tested source changed'
    limitations = [dict(case=c['case'], **finding) for c in cases for finding in c['source_based_limitations']]
    mismatches = [] if not target else [dict(case=c['case'], **f) for c in target['cases'] for f in c['wire_mismatches']]
    assert not args.patched or not (limitations or mismatches)
    report = dict(status='upstream_compatibility_findings' if limitations or mismatches else 'pass',
        upstream_commit=PIN, upstream_provenance=provenance, effective_source=effective,
        patched=args.patched, source_sha256=tested, cases=cases, target=target,
        observed_protocol_limitations=limitations, observed_big_endian_mismatches=mismatches,
        usb_transfers=0, completed_usb_control_transfers=0, completed_native_page_lifecycles=0,
        scope=('Locally patched' if args.patched else 'Unchanged pinned') + ' TinyUSB generic device/EP0 core plus the existing class/document component and a synthetic event/DCD fixture. Actual descriptor parsing, control packetization and application-driver dispatch execute; all controller and cancellation observations are supplied.',
        limits='This is a synthetic protocol fixture, not a production controller adapter. Packet captures represent submissions, including cancelled transfers, not USB wire delivery. Unchanged upstream limitations remain in the separate baseline. No controller port, bulk data, physical reset, sensor status, boot or printing is established.')
    text = json.dumps(report, indent=2, sort_keys=True) + '\n'
    name = ('patched-validation' if args.target else 'patched-host-validation') if args.patched else ('upstream-baseline' if args.target else 'upstream-host-baseline')
    (temp/(name + '.json')).write_text(text)
    (OUT/(name + '.json')).write_text(text)
    (OUT/(name + '.md')).write_text('# TinyUSB protocol execution\n\n' + report['scope'] + '\n\n'
        + f'{len(cases)} host scenarios; {len(target["cases"]) if target else 0} target scenarios. '
        + f'{len(limitations)} routing/result observations and {len(mismatches)} target wire mismatches remain explicit limitations.\n\n'
        + report['limits'] + '\n')
    print(f'TinyUSB: {len(limitations)} protocol limitations; {len(mismatches)} BE wire mismatches; patched={args.patched}', flush=True)


if __name__ == '__main__':
    main()
