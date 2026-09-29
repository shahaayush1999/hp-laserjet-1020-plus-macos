#!/usr/bin/env python3
"""EP0 packet descriptors through actual TinyUSB in synthetic RAM.

No physical USB, MMIO, upload, cache operation, controller settlement or printing.
"""
import argparse
import importlib.util
import itertools
import json
from pathlib import Path
import runpy
import select
import shutil
import struct
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('ep0_continuous', ROOT/'scripts/validate-hp1020-continuous-printer.py')
continuous = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = continuous
spec.loader.exec_module(continuous)
base, core = continuous.base, continuous.core
SRC = ROOT/'open-firmware/udc-ep0-test'
COMPONENT = ROOT/'open-firmware/udc-ep0'
OUT = ROOT/'analysis/usb-path/udc-ep0'
OK, WAIT, STALE, INVALID, FAULT, ADAPTER_ERROR = range(6)
FREE, PREPARED, EXPOSED = range(3)
DESC_DMA = (0x13579bd0, 0xa468ace0)
PACKET_DMA = (0x3579bdf0, 0xb68ace00)
ALL_FACTS = 0x01010101
ALL_PUBLISH = 0x010101


def descriptor(status, dma, reserved=0, next_pointer=0):
    return struct.pack('>4I', status, reserved, dma, next_pointer)


def device_id(length):
    return struct.pack('>H', length)+bytes(65+i % 26 for i in range(length-2))


class Host(continuous.Host):
    def __init__(self, executable, directory, fill, capacity, interface):
        self.ep0_rows, self.controls, self.descriptor_oracles = [], {}, []
        self.publications, self.fill = [0, 0], fill
        super().__init__(executable, directory, fill, capacity, interface)
        self.ep0_initial = self.ep0.copy()
        assert self.ep0[1:5] == [1, 0, 1, 1] and self.ep0[7] == 400
        for i in (0, 1):
            p = self.slot(i)
            assert p[0] == FREE and p[14:18] == [fill*0x01010101]*4
            assert p[11:14] == [DESC_DMA[i], PACKET_DMA[i], 64]

    def read_row(self):
        if not select.select([self.process.stdout], [], [], 30)[0]:
            self.process.kill(); self.process.wait()
            raise AssertionError('host timed out: '+str(self.directory))
        raw = self.process.stdout.readline()
        with (self.directory/'raw-stdout').open('ab') as saved:
            saved.write(raw)
        assert raw, ('fixture ended early', self.directory)
        row = json.loads(raw)
        assert len(row) == 200, row
        self.ep0 = row[96:]
        return row[:96]

    def slot(self, i):
        return self.ep0[8+48*i:56+48*i]

    def step(self, op, a=0, b=0, c=0, d=0, data=b'', result=OK, expect=None):
        row = super().step(op, a, b, c, d, data, result, expect)
        self.ep0_rows.append(self.ep0.copy())
        with (self.directory/'host-ep0-steps.jsonl').open('a') as saved:
            saved.write(json.dumps(self.ep0)+'\n')
        assert self.ep0[2:5] == [0, 1, 1], ('EP0 ownership/guards', op, self.ep0)
        for i in (0, 1):
            p = self.slot(i)
            token = p[6]
            if token and token not in self.controls:
                expected_cookie = [row[21], row[3], row[32], 0, i*0x80]
                assert p[6:11] == expected_cookie and row[22:24] == [i*0x80, p[5]]
                wanted = descriptor(0x08000000 | p[5], PACKET_DMA[i])
                assert struct.pack('>4I', *p[14:18]) == wanted
                assert p[46] == int(p[5] == 0)
                self.controls[token] = dict(cookie=p[6:11], slot=i, requested=p[5], descriptor=wanted.hex())
                self.descriptor_oracles.append(dict(step=len(self.rows)-1, kind='prepare', **self.controls[token]))
            if p[32] != self.publications[i]:
                assert p[32] == self.publications[i]+1
                record = self.controls[p[22]]
                assert p[22:27] == record['cookie'] and p[27:31] == [DESC_DMA[i], PACKET_DMA[i], record['requested'], 64]
                assert struct.pack('>4I', *p[18:22]).hex() == record['descriptor']
                assert p[47] == int(record['requested'] == 0)
                self.publications[i] = p[32]
                self.descriptor_oracles.append(dict(step=len(self.rows)-1, kind='publish', **record))
        return row

    def observe(self, token, status, *, facts=ALL_FACTS, actual=None, fault=0,
                mutant=0, reserved=0, dma=None, next_pointer=0, write=False, result=OK):
        record = self.controls[token]
        actual = record['requested'] if actual is None else actual
        raw = descriptor(status, PACKET_DMA[record['slot']] if dma is None else dma, reserved, next_pointer)
        if write:
            self.step(46, token, 0, 0, 16, data=raw)
        return self.step(44, token, facts, fault, mutant, data=raw+struct.pack('>I', actual), result=result)

    def complete(self, token, length, usb_result=0, result=OK, service=True):
        if token not in self.controls:
            return super().complete(token, length, usb_result, result, service)
        assert usb_result == 0, 'endpoint errors are explicit fault observations'
        # IN low16 is deliberately unrelated to the actual supplied count.
        status = 0x8800ffff if self.controls[token]['slot'] else 0x88000000
        self.observe(token, status, actual=length, write=result != STALE, result=result)
        if service:
            self.service()

    def start_role(self, role, publish=True):
        self.setup(base.packet(0x80, 6, value=0x100, length=18))
        if role == 'in':
            if publish:
                self.wire(base.DEVICE, 'device-IN-data')
            return self.row[28]
        self.wire(base.DEVICE, 'device-before-OUT-status')
        self.complete(self.row[28], 18)
        assert self.row[26] and self.row[27] == 0
        return self.row[26]

    def finish_role(self, role, token, already_settled=False):
        if already_settled:
            self.service()
        else:
            self.complete(token, self.controls[token]['requested'])
        if role == 'in':
            assert self.row[26] and not self.row[28]
            self.complete(self.row[26], 0)
        assert not self.row[26] and not self.row[28]

    def reset_retained(self, token):
        self.setup(base.packet(0x21, 2, index=self.interface), service_result=base.WAIT)
        self.step(43, token, 1)
        self.service()
        assert self.row[44] == 1 and self.row[47] == 1
        self.step(10)
        self.finish_reset()

    def fresh_page(self, document, images):
        generation = self.row[32]
        self.send(document(['small']), 64)
        self.expected_pixels += images['small'][1]
        self.notification(generation, 1, 0, 1)
        self.repeat_pump()

    def finish(self):
        captures = super().finish()
        raw = (self.directory/'output.ep0-descriptors').read_bytes()
        assert len(raw) == 240
        for at in (0, 32, 64, 144, 224):
            assert raw[at:at+16] == bytes([self.fill])*16
        for i, (desc_at, packet_at) in enumerate(((16, 80), (48, 160))):
            p = self.slot(i)
            assert raw[desc_at:desc_at+16] == struct.pack('>4I', *p[14:18])
            assert core.fnv(raw[packet_at:packet_at+64]) == p[42]
        captures['ep0'] = raw
        return captures


def scenario(h, name, document, images):
    if name == 'direct-address':
        h.step(5); h.service()
        h.setup(base.packet(0, 5, value=37))
        token = h.row[28]
        h.wire(b'', 'address-status-proposal')
        assert h.row[64:66] == [0, 37]
        h.observe(token, 0x88001234, facts=0x01000101, result=WAIT)
        h.service()
        assert h.row[64:66] == [0, 37] and h.row[28] == token
        h.complete(token, 0)
        assert h.row[64] == 37 and not h.row[28]
        return
    if name == 'older-generation-fault':
        h.step(5); h.service()
        h.setup(base.packet(0, 9, 1))
        old = h.row[28]
        h.wire(b'', 'retained-configuration-status')
        assert h.controls[old]['cookie'][2] == h.row[32] == 1
        h.step(10)
        h.finish_reset(ack=False)
        assert h.row[32] == 2 and h.row[28] == old and not h.row[7]
        small = document(['small'])
        bulk = h.arm_write(small[:31])
        epoch = h.row[4]
        h.observe(old, 0x48000000, fault=0x80, facts=0, result=FAULT)
        assert h.slot(1)[4] == base.STALE
        assert h.row[4] == epoch and h.row[32] == 2
        assert h.row[7] == h.row[9] == h.row[36] == h.row[14] == 0
        assert h.slot(1)[:3] == [EXPOSED, 1, 1] and h.row[28] == old
        h.step(43, old, 1); h.service()
        assert not h.row[28] and not h.row[7] and h.row[30] == bulk
        h.request(base.packet(0x80, 6, value=0x100, length=18), base.DEVICE)
        h.complete(bulk, 31); h.step(7)
        h.send(small[31:], 64)
        h.expected_pixels = images['small'][1]
        h.notification(2, 1, 0, 1)
        h.repeat_pump()
        return
    if name == 'data-zlp':
        h.step(49, 64)
    h.configure()
    initial_generation = h.row[32]
    if name in ('protocol', 'data-zlp'):
        h.request(base.packet(0x80, 6, value=0x100, length=256), base.DEVICE, label='device')
        length = 64 if name == 'data-zlp' else 400
        requested = (65, 128, 65535) if name == 'data-zlp' else (1, 2, 18, 63, 64, 65, 255, 400, 65535)
        for count in requested:
            h.request(base.packet(0xa1, 0, index=h.interface << 8, length=count),
                      device_id(length)[:count], label='device-ID')
        h.request(base.packet(0xa1, 1, index=h.interface, length=1), b'\x18', label='unknown-physical-status')
        h.send(document(['small'])+document([])+document(['slim']), 64)
        h.expected_pixels = images['small'][1]+images['slim'][1]
        h.expected_documents = [(initial_generation, 1, 0, 1, 0), (initial_generation, 2, 1, 0, 0)]
        h.notification(initial_generation, 3, 1, 1)
        h.repeat_pump()
        h.recover()
        h.fresh_page(document, images)
        assert self_free(h)
        return
    if name.startswith('status/'):
        _, role, owner = name.split('/')
        owner = int(owner)
        counts = (0, 18, 65535) if role == 'in' else (0, 1, 64, 65535)
        for result_bits, last, count in itertools.product(range(4), (0, 1), counts):
            token = h.start_role(role)
            status = owner << 30 | result_bits << 28 | last << 27 | count
            result = WAIT if owner != 2 else OK if result_bits == 0 and last and (role == 'in' or not count) else FAULT
            before = h.row.copy()
            h.observe(token, status, write=True, result=result)
            if result == OK:
                assert h.slot(h.controls[token]['slot'])[0] == FREE
                h.finish_role(role, token, already_settled=True)
                h.recover()
            else:
                assert h.slot(h.controls[token]['slot'])[0] == EXPOSED
                assert h.row[50] == before[50] and h.row[32] == before[32]
                if result == FAULT:
                    assert h.row[7] == h.row[9] == h.row[36] == 1
                    epoch = h.row[4]
                    h.observe(token, status, result=FAULT)
                    assert h.row[4] == epoch
                h.reset_retained(token)
        h.fresh_page(document, images)
        return
    if name.startswith('facts/'):
        role = name.split('/')[1]
        token = h.start_role(role)
        slot = h.controls[token]['slot']
        requested = h.controls[token]['requested']
        status = 0x8800ffff if slot else 0x88000000
        for values in itertools.product((0, 1), repeat=4 if slot else 3):
            if all(values):
                continue
            facts = values if slot else (*values, 0)
            packed = int.from_bytes(bytes(facts), 'big')
            h.observe(token, status, facts=packed, result=WAIT)
            h.service()
            assert h.slot(slot)[0] == EXPOSED and h.row[26+2*slot] == token
            assert h.row[50] == h.row[56] == 0
        for values in ((2, 1, 1, 1), (1, 2, 1, 1), (1, 1, 2, 1), (1, 1, 1, 2), (255, 1, 1, 1)):
            h.observe(token, status, facts=int.from_bytes(bytes(values), 'big'), result=INVALID)
            assert h.slot(slot)[0] == EXPOSED
        busy = descriptor(0x48000000, PACKET_DMA[slot])
        done = descriptor(status, PACKET_DMA[slot])
        h.step(46, token, 0, 0, 16, data=busy); h.step(47, token, 0)
        h.step(46, token, 0, 0, 16, data=done)
        h.step(48, 0, ALL_FACTS, data=struct.pack('>I', requested), result=WAIT)
        h.service()
        assert h.slot(slot)[0] == EXPOSED and h.row[26+2*slot] == token
        h.step(47, token, 1)
        h.step(46, token, 0, 0, 16, data=busy)
        h.step(48, 1, ALL_FACTS, data=struct.pack('>I', requested))
        h.finish_role(role, token, already_settled=True)
        h.fresh_page(document, images)
        return
    if name.startswith('publication/'):
        role = name.split('/')[1]; endpoint = 0x80 if role == 'in' else 0
        h.step(40, endpoint, 0, ALL_PUBLISH)
        token = h.start_role(role, publish=False)
        slot = h.controls[token]['slot']
        assert h.slot(slot)[0] == PREPARED
        for values in itertools.product((0, 1), repeat=3):
            if all(values):
                continue
            h.step(41, token, int.from_bytes(bytes(values), 'big'), result=WAIT)
            assert h.slot(slot)[0] == PREPARED
        for values in ((2, 1, 1), (1, 2, 1), (1, 1, 255)):
            h.step(41, token, int.from_bytes(bytes(values), 'big'), result=INVALID)
        h.step(41, token, ALL_PUBLISH)
        if role == 'in':
            h.wire(base.DEVICE, 'delayed-publication')
        h.step(41, token, ALL_PUBLISH, result=WAIT)
        h.finish_role(role, token)
        h.step(40, endpoint, 1, ALL_PUBLISH)
        h.fresh_page(document, images)
        return
    if name.startswith('cancel/'):
        role = name.split('/')[1]; endpoint = 0x80 if role == 'in' else 0
        for kind in ('prepared', 'exposed', 'late-success'):
            h.step(40, endpoint, int(kind != 'prepared'), ALL_PUBLISH)
            token = h.start_role(role, publish=kind != 'prepared')
            slot = h.controls[token]['slot']
            phase = PREPARED if kind == 'prepared' else EXPOSED
            h.step(43, token, 1, result=INVALID)
            h.step(42, token)
            for settled in (0, 2, 255):
                h.step(43, token, settled, result=WAIT if not settled else INVALID)
                assert h.slot(slot)[0] == phase and h.row[26+2*slot] == token
            h.step(41, token, ALL_PUBLISH, result=WAIT)
            h.step(40, endpoint, 1, ALL_PUBLISH)
            if kind == 'late-success':
                h.finish_role(role, token)
                h.recover()
            else:
                h.reset_retained(token)
            h.fresh_page(document, images)
        return
    if name.startswith('fault/'):
        role = name.split('/')[1]
        mutations = [('reserved', 1), ('dma', 0x24681340), ('next_pointer', 0x12345670),
                     ('fault', 0x80), ('fault', 0x200), ('fault', 0x80000000)]
        if role == 'in':
            mutations += [('actual', 0), ('actual', 17), ('actual', 19), ('actual', 0xffffffff)]
        for key, value in mutations:
            token = h.start_role(role)
            slot = h.controls[token]['slot']
            status = 0x8800ffff if slot else 0x88000000
            flags = 0 if key == 'fault' else ALL_FACTS
            before = h.row.copy()
            h.observe(token, status, facts=flags, result=FAULT, **{key: value})
            assert h.row[4] == before[4]+1 and h.row[7] == h.row[9] == h.row[36] == 1
            assert h.slot(slot)[0:3] == [EXPOSED, 1, 1]
            epoch = h.row[4]
            h.observe(token, status, result=FAULT)
            assert h.row[4] == epoch and h.row[26+2*slot] == token
            submissions = h.row[17]
            h.step(43, token, 1); h.service()
            assert h.row[17] == submissions and not h.row[26] and not h.row[28]
            h.recover()
        h.fresh_page(document, images)
        return
    if name == 'initial-spans':
        baseline = h.row.copy(), h.ep0.copy()
        for region in range(4):
            for kind in (*range(11), 12):
                h.step(50, region, kind, result=OK if not kind else INVALID)
                assert h.row[2:96] == baseline[0][2:96]
                assert h.ep0[8:] == baseline[1][8:]
            needed = 16 if region < 2 else 64
            h.step(50, region, 11, 0x100000000-needed, needed)
            h.step(50, region, 11, 0xfffffff0, 64, result=INVALID)
            h.step(50, region, 11, 0x12345670, needed-1, result=INVALID)
        h.fresh_page(document, images)
        return
    if name == 'prepare-rejection':
        for kind in range(1, 13):
            h.step(45, 0x80, kind)
            h.setup(base.packet(0x80, 6, value=0x100, length=18),
                    service_result=base.ERROR if kind in (11, 12) else base.OK)
            if kind in (11, 12):
                token = h.row[28]
                assert token and h.slot(1)[0] == (PREPARED if kind == 11 else EXPOSED)
                if kind == 12:
                    h.wire(base.DEVICE, 'rejected-after-publication')
                assert h.row[7] == h.row[9] == h.row[36] == 1
                h.step(43, token, 1); h.service(); h.recover()
            else:
                assert not h.row[26] and not h.row[28] and h.slot(1)[0] == FREE
                h.request(base.packet(0x80, 6, value=0x100, length=18), base.DEVICE)
        h.fresh_page(document, images)
        return
    if name == 'old-cookie':
        old = h.start_role('in')
        h.step(46, old, 0, 0, 16, data=descriptor(0x88000012, PACKET_DMA[1]))
        h.step(47, old, 0)
        h.finish_role('in', old)
        current = h.start_role('in')
        before = h.row.copy(), h.slot(1)
        for fault in (0, 0x80):
            h.step(48, 0, ALL_FACTS, fault, data=struct.pack('>I', 18), result=STALE)
        for mutant in range(1, 6):
            h.observe(current, 0x88000012, mutant=mutant, result=STALE)
            h.step(42, current, d=mutant, result=STALE)
            h.step(43, current, 1, d=mutant, result=STALE)
        assert h.row[2:20] == before[0][2:20] and h.row[24:96] == before[0][24:96]
        assert h.slot(1)[:35] == before[1][:35]
        h.finish_role('in', current)
        h.fresh_page(document, images)
        return
    if name == 'superseded-fault':
        h.setup(base.packet(0xa1, 0, index=h.interface << 8, length=400))
        old = h.row[28]
        h.wire(device_id(400)[:64], 'old-device-ID')
        h.setup(base.packet(0x80, 6, value=0x100, length=18), service_result=base.WAIT)
        epoch, generation = h.row[4], h.row[32]
        h.observe(old, 0x48000000, fault=0x80, facts=0, result=FAULT)
        assert h.row[4] == epoch and h.row[32] == generation and not h.row[7] and not h.row[36]
        h.step(43, old, 1); h.service()
        current = h.row[28]
        assert current and current != old
        h.observe(old, 0x88000040, fault=0x80, result=STALE)
        h.control_in(base.DEVICE, 'new-request-after-old-fault')
        h.fresh_page(document, images)
        return
    raise AssertionError('unimplemented profile: '+name)


def self_free(h):
    return h.slot(0)[0] == h.slot(1)[0] == FREE


def profiles():
    result = [('protocol', fill, interface) for fill in (0, 204) for interface in (0, 3)]
    for fill in (0, 204):
        result += [(name, fill, 3) for name in ('direct-address', 'older-generation-fault', 'data-zlp', 'initial-spans',
                                              'prepare-rejection', 'old-cookie', 'superseded-fault')]
        result += [(f'status/{role}/{owner}', fill, 3) for role in ('in', 'out') for owner in range(4)]
        result += [(f'{kind}/{role}', fill, 3) for kind in ('facts', 'publication', 'cancel', 'fault') for role in ('in', 'out')]
    return result


def compile_host(temp, effective):
    implementation = [SRC/'fixture.c', SRC/'host-check.c', COMPONENT/'hp1020_udc_ep0.c',
        base.ADAPTER/'hp1020_tusb_adapter.c', base.PRINTER/'hp1020_usb_printer.c',
        base.RX/'hp1020_usb_receive.c', base.RX/'hp1020_usb_document.c']
    implementation += [base.IMG/name for name in ('hp1020_image.c', 'hp1020_image_page.c', 'hp1020_image_stream.c',
        'hp1020_image_ring.c', 'hp1020_image_output.c')]
    implementation += [base.SEM/'hp1020_semantic.c', base.SEM/'hp1020_page_plan.c',
        core.VENDOR/'libjbig/jbig85.c', core.VENDOR/'libjbig/jbig_ar.c']
    implementation += [effective/'src'/name for name in ('tusb.c', 'device/usbd.c', 'common/tusb_fifo.c')]
    flags = ['clang', '-std=c11', '-O1', '-g', '-fno-common', '-Wall', '-Wextra', '-Werror', '-fsanitize=address,undefined']
    include = ['-I'+str(p) for p in (SRC, COMPONENT, ROOT/'open-firmware', base.SRC, base.ADAPTER, base.PROTOCOL,
        base.PRINTER, base.RX, base.IMG, base.SEM, core.VENDOR/'libjbig', effective/'src')]
    core.command(flags+include+implementation+['-o', temp/'host'])
    full = ROOT/'vendor/foo2zjs-source'
    core.command(flags+['-I'+str(full), base.IMG/'reference.c', full/'jbig.c', full/'jbig_ar.c', '-o', temp/'reference'])


def sources(temp):
    tested = base.sources(temp)
    selected = set(SRC.glob('*.[ch]')) | set(SRC.glob('*.ld')) | set(COMPONENT.glob('*.[ch]'))
    selected.update(ROOT/'scripts'/name for name in ('validate-hp1020-continuous-printer.py',
        'validate-hp1020-udc-ep0.py', 'build-hp1020-udc-ep0-target.sh'))
    reference = ROOT/'analysis/usb-path/ep0-construction.json'
    selected.add(reference)
    report = json.loads(reference.read_text())
    assert report['status'] == 'pass'
    selected.update(ROOT/name for name in report['source_sha256'])
    for p in sorted(selected):
        name = str(p.relative_to(ROOT))
        tested[name] = core.sha(p.read_bytes())
        dest = temp/'source'/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, dest)
    (temp/'source-sha256.json').write_text(json.dumps(tested, indent=2)+'\n')
    return tested


def original_reference():
    # Reuse the independently executed original cuts. These runs are evidence
    # for construction only; completion/visibility/settlement remain supplied.
    from hp1020_xtensa_properties import properties, section_bytes
    path = ROOT/'analysis/usb-path/ep0-construction.json'
    r = json.loads(path.read_text())
    stock = (ROOT/'analysis/sihp1020.elf').read_bytes()
    assert core.sha(stock) == r['stock_elf_sha256'] == '2111560068db47ceca21fa550db4c7c34f5595b5a5d137ae4a19631e40e3601d'
    assert r['status'] == 'pass' and r['counts'] == dict(
        construction=36, pointer_only=12, mmio_rejections=16, excluded_multi_descriptor=2)
    assert len(r['cases']) == 66 and len(r['excluded_code_controls']) == 18
    assert r['private_literal_redirects'] == r['supplied_services'] == []
    assert r['actual_peripheral_accesses'] == r['completed_usb_control_transfers'] == 0
    assert r['omitted_startup_prefix'] is True and r['original_entry_executed'] is False
    assert r['controller_quiescence_established'] is False
    assert all(core.sha((ROOT/n).read_bytes()) == h for n,h in r['source_sha256'].items())
    sections, _ = properties(stock)
    for anchor in r['original_byte_audit']['ranges']:
        begin, end = int(anchor['begin'],16), int(anchor['end'],16)
        raw = section_bytes(stock,sections,begin,end-begin)
        assert raw.hex() == anchor['bytes'] and core.sha(raw) == anchor['sha256']
    for address, raw in (
        (0x10008d02, '88c019f467dcf00c02009890'),
        (0x10008f11, '19f3e38870c7ef0c02009890'),
        (0x100092aa, '88b019f2e21bf2fca98819f2fe0c020098b0')):
        assert section_bytes(stock, sections, address, len(raw)//2).hex() == raw
    vectors = []
    for c in r['cases']:
        v, a, b = c['input'], c['interpreter'], c['qemu']
        assert c['status'] == a['status'] == b['status'] == 'pass'
        for result in (a,b):
            assert result['all_mutable_and_guard_ram_equal'] and result['ordered_write_trace_equal']
            assert result['original_code_unchanged'] and result['actual_peripheral_accesses'] == 0
            assert result['actual_memory'] == result['expected_memory']
            assert [e for e in result['accesses'] if e['kind'] == 'write'] == result['expected_writes']
        for key in ('registers','descriptor_hex','accesses','actual_memory','expected_memory','original_instructions_retired'):
            assert a[key] == b[key]
        if v['effect'] == 'descriptor':
            wanted = struct.pack('>4I',0x08000000 | v['length'],0,v['pointer'],0).hex()
            assert a['descriptor_hex'] == a['expected_descriptor_hex'] == wanted
            assert a['literal_descriptor_checked'] and b['literal_descriptor_checked']
            vectors.append(dict(kind=v['kind'], length=v['length'], pointer=v['pointer'], bytes=wanted))
        elif v['effect'] == 'pointer':
            wanted = ((v['pointer']+0x80000000)&0xffffffff) if v['kind']=='initial-add-pointer' else v['pointer']
            assert int(a['pointer_register_a8'],16) == int(b['pointer_register_a8'],16) == wanted
            assert a['pointer_oracle_checked'] and b['pointer_oracle_checked']
        else:
            assert a['actual_memory'] == a['before_memory'] and not a['expected_writes']
            if v.get('reject_mmio'):
                assert a['failure']['reason'] == b['failure']['reason'] == 'MMIO forbidden'
    return dict(report='analysis/usb-path/ep0-construction.json', report_sha256=core.sha(path.read_bytes()),
        stock_sha256=core.sha(stock), completed_construction_cases_reused=36,
        completed_pointer_cases_reused=12, pre_mmio_controls_reused=16,
        out_of_profile_controls_reused=2, excluded_pc_controls_reused=18,
        original_descriptor_vectors=vectors, active_pointer_preserved=True,
        initial_pointer_add_modulo32=True, physical_address_translation_established=False,
        original_entry_executed=False, newly_executed_stock_instructions=0,
        completion_count_visibility_and_settlement_supplied=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', action='store_true')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix='hp1020-udc-ep0-', dir='/tmp'))
    print('UDC EP0 captures: '+str(temp), flush=True)
    tested = sources(temp)
    evidence = original_reference()
    fixtures = [base.pages.OUT/name for name in (
        'fixtures/32x8-stripe4-black.jbg', 'fixtures/9600x132-stripe128-edges.jbg',
        'fixtures/16384x4-stripe128-edges.jbg', 'output-fixtures/1024x260-stripe128-repeat.jbg',
        'output-fixtures/64x12-stripe4-edges.jbg')]
    fixtures.append(ROOT/'analysis/samples/generated/matrix-a4_default.zjs')
    fixture_bytes = {str(p.relative_to(ROOT)): p.read_bytes() for p in fixtures}
    fixture_hashes = {n: core.sha(raw) for n, raw in fixture_bytes.items()}
    for name, raw in fixture_bytes.items():
        dest = temp/'tested-fixtures'/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw)
    (temp/'fixture-sha256.json').write_text(json.dumps(fixture_hashes, indent=2)+'\n')

    def unchanged():
        assert all(core.sha((ROOT/n).read_bytes()) == v for n,v in tested.items()), 'source changed during execution'
        assert all((ROOT/n).read_bytes() == raw for n,raw in fixture_bytes.items()), 'fixture changed during execution'

    effective = runpy.run_path(str(ROOT/'scripts/prepare-hp1020-tinyusb.py'))['prepare'](temp/'effective-source', True)
    compile_host(temp, temp/'effective-source')
    document, images, used = base.image_documents(temp)
    assert set(used) == set(fixtures)
    unchanged()
    cases, replay = [], []
    matrix = profiles()
    for index, (name, fill, interface) in enumerate(matrix):
        directory = temp/f'case-{index:03}'
        directory.mkdir()
        title = f'{name}/fill={fill}/capacity=64/interface={interface}'
        (directory/'case-name').write_text(title+'\n')
        h = Host(temp/'host', directory, fill, 64, interface)
        try:
            scenario(h, name, document, images)
            captures = h.finish()
        finally:
            h.abort()
        cases.append(dict(case=title, scenario=name, fill=fill, capacity=64, interface=interface,
            status='pass', initial=h.initial, initial_ep0=h.ep0_initial, steps=h.rows, ep0_steps=h.ep0_rows,
            events=h.events, packet_oracles=h.packets, descriptor_oracles=h.descriptor_oracles,
            expected_documents=h.expected_documents, expected_pixels_sha256=core.sha(h.expected_pixels),
            pixels_bytes=len(h.expected_pixels), capture_sha256={n: core.sha(raw) for n,raw in captures.items()}))
        replay.append((h, captures, directory))
        print(f'UDC EP0: {len(cases)}/{len(matrix)} host cases passed', flush=True)
    unchanged()
    target = None
    if args.target:
        core.command(['bash', ROOT/'scripts/build-hp1020-udc-ep0-target.sh'])
        built = OUT/'target'
        assert json.loads((built/'effective-source.json').read_text()) == effective
        saved = temp/'target'
        saved.mkdir()
        for path in built.iterdir():
            if path.is_file() and path.name != 'annotated-disassembly.txt':
                shutil.copyfile(path, saved/path.name)
        elf = saved/'target-check.elf'
        artifacts = {p.name: core.sha(p.read_bytes()) for p in saved.iterdir() if p.is_file()}
        program, audit = core.audit_target(elf)
        assert all(core.sha((saved/n).read_bytes()) == digest for n,digest in artifacts.items()), 'audit changed a build artifact'
        artifacts['annotated-disassembly.txt'] = core.sha((saved/'annotated-disassembly.txt').read_bytes())
        (temp/'target-sha256.json').write_text(json.dumps(artifacts,indent=2)+'\n')
        unchanged()
        from hp1020_qemu_ram import QemuRAM
        native = []
        with QemuRAM() as q:
            version = q.version
            for case, (h, captures, directory) in zip(cases, replay):
                q.load(elf)
                assert q.call0(program.symbols['hp1020_bulk_fixture_reset'], [case['fill'], 64, case['interface'], 0xffffffff]) == 0
                initial = list(struct.unpack('>96I', q.read(program.symbols['hp1020_bulk_fixture_stats'], 384)))
                initial_ep0 = list(struct.unpack('>104I', q.read(program.symbols['hp1020_ep0_fixture_stats'], 416)))
                assert initial[:59]+initial[60:] == h.initial[:59]+h.initial[60:] and initial_ep0 == h.ep0_initial
                for index, (event, host_row, host_ep0) in enumerate(zip(h.events, h.rows, h.ep0_rows)):
                    data = bytes.fromhex(event['data_hex'])
                    if data:
                        q.put(program.symbols['hp1020_bulk_fixture_input'], data)
                    result = q.call0(program.symbols['hp1020_bulk_fixture_step'], event['words'])
                    row = list(struct.unpack('>96I', q.read(program.symbols['hp1020_bulk_fixture_stats'], 384)))
                    ep0 = list(struct.unpack('>104I', q.read(program.symbols['hp1020_ep0_fixture_stats'], 416)))
                    with (directory/'target-steps.jsonl').open('a') as output:
                        output.write(json.dumps(row+ep0)+'\n')
                    assert result == row[0] == event['result'] and row[15:17] == [0,1] and ep0[2:5] == [0,1,1]
                    assert row[:59]+row[60:] == host_row[:59]+host_row[60:], (case['case'], index, row, host_row)
                    assert ep0 == host_ep0, (case['case'], index, ep0, host_ep0)
                observed = {}
                for name, symbol in (('pixels','hp1020_bulk_fixture_pixels'),('wire','hp1020_bulk_fixture_wire'),
                                     ('documents','hp1020_bulk_fixture_documents')):
                    observed[name] = q.read(program.symbols[symbol], len(captures[name]))
                for name, symbol in (('receive','hp1020_bulk_fixture_receive_storage'),
                                     ('output','hp1020_bulk_fixture_output_storage'),('ep0','hp1020_ep0_fixture_storage')):
                    address = q.call0(program.symbols[symbol], [])
                    observed[name] = q.read(address, len(captures[name]))
                assert q.call0(program.symbols['hp1020_ep0_fixture_storage_bytes'], []) == len(captures['ep0'])
                size = q.call0(program.symbols['hp1020_ep0_fixture_component_bytes'], [])
                for name, raw in observed.items():
                    (directory/('target-'+name)).write_bytes(raw)
                    assert raw == captures[name], (case['case'], name)
                native.append(dict(case=case['case'],status='pass',all_steps_equal=True,
                    all_pixels_wire_notifications_descriptors_and_storage_equal=True,
                    adapter_state_and_memory_bytes=row[59], descriptor_component_bytes=size,
                    capture_sha256={n:core.sha(raw) for n,raw in observed.items()}))
                print(f'UDC EP0: {len(native)}/{len(cases)} target cases passed', flush=True)
        assert all(core.sha((saved/n).read_bytes()) == v for n,v in artifacts.items()), 'captured target changed'
        target = dict(status='pass',cases=native,qemu_version=version,elf_sha256=core.sha(elf.read_bytes()),
                      audit=audit,captured_artifact_sha256=artifacts)
    unchanged()
    report = dict(status='pass',source_sha256=tested,fixture_sha256=fixture_hashes,effective_source=effective,
        original_reference=evidence,cases=cases,target=target,completed_native_page_lifecycles=0,
        usb_transfers=0,actual_peripheral_accesses=0,controller_quiescence_established=False,
        scope='Two original-cookie EP0 normal descriptors, separate 64-byte packet allocations, actual TinyUSB packetization and class/receive/JBIG output in RAM with independent byte/pixel/event oracles.',
        limits='No physical DCD, SETUP-buffer manager, MMIO, IRQ, cache, boot, USB traffic or printing. CPU/DMA mapping, packet64/BE mode, visibility, immutable observations and settlement remain supplied. IN actual length is separately supplied and never inferred from descriptor low16. Bulk input remains normalized synthetic transport in this experiment; the separate OUT-descriptor suite remains independent. Copies remain metadata and output is synchronous.')
    name = 'validation' if args.target else 'host-validation'
    raw = json.dumps(report,sort_keys=True,separators=(',',':'))+'\n'
    (temp/(name+'.json')).write_text(raw)
    (OUT/(name+'.json')).write_text(raw)
    (OUT/(name+'.md')).write_text('# EP0 descriptor execution\n\n'+report['scope']+'\n\n'+
        f'{len(cases)} host; {len(target["cases"]) if target else 0} QEMU cases. Exact packet proposals, bytes, retained storage, pixels and document notifications checked.\n\n'+report['limits']+'\n')


if __name__ == '__main__':
    main()
