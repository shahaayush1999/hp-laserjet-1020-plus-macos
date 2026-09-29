#!/usr/bin/env python3
"""One-slot USB OUT descriptor composition in synthetic RAM only.

No USB, MMIO, hardware cancellation, firmware upload or physical output.
Visibility, controller mode and settlement are separately supplied assertions.
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
spec = importlib.util.spec_from_file_location('udc_continuous', ROOT/'scripts/validate-hp1020-continuous-printer.py')
continuous = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = continuous
spec.loader.exec_module(continuous)
base, core = continuous.base, continuous.core
SRC = ROOT/'open-firmware/udc-out-test'
COMPONENT = ROOT/'open-firmware/udc-out'
OUT = ROOT/'analysis/usb-path/udc-out'
OK, WAIT, STALE, INVALID, FAULT, ADAPTER_ERROR = range(6)
DESC_DMA, BUFFER_DMA, BUFFER_STRIDE = 0x13579bd0, 0x24681340, 0x1000
FREE, PREPARED, EXPOSED = range(3)


def descriptor(status, buffer, reserved=0, next_pointer=0):
    return struct.pack('>4I', status, reserved, buffer, next_pointer)


class Host(continuous.Host):
    def __init__(self, executable, directory, fill, capacity, interface):
        self.udc_rows, self.bulk, self.descriptor_oracles = [], {}, []
        self.fill = fill
        super().__init__(executable, directory, fill, capacity, interface)
        self.udc_initial = self.udc.copy()
        assert self.udc[1:3] == [1, FREE] and self.udc[7:10] == [0, 1, 1], self.udc
        assert self.udc[21] == DESC_DMA and self.udc[24:28] == [fill*0x01010101]*4

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
        assert len(row) == 144, row
        self.udc = row[96:]
        return row[:96]

    def step(self, op, a=0, b=0, c=0, d=0, data=b'', result=OK, expect=None):
        row = super().step(op, a, b, c, d, data, result, expect)
        self.udc_rows.append(self.udc.copy())
        with (self.directory/'host-udc-steps.jsonl').open('a') as saved:
            saved.write(json.dumps(self.udc)+'\n')
        assert self.udc[7:10] == [0, 1, 1], ('descriptor guards', op, self.udc)
        if op == 6 and row[30] and self.udc[16] == row[30]:
            self.bulk[row[30]] = dict(cookie=self.udc[16:21], dma=self.udc[22], slot=self.udc[47])
            self.publication_oracle(row[30], published=self.udc[2] == EXPOSED)
        return row

    def publication_oracle(self, token, published=True):
        record = self.bulk[token]
        wanted = descriptor(0x08000000, BUFFER_DMA + record['slot']*BUFFER_STRIDE)
        assert record['cookie'] == [token, self.row[5], self.row[32], self.row[33], 1]
        assert record['slot'] == (self.row[33]-1) % 4
        assert record['dma'] == BUFFER_DMA + record['slot']*BUFFER_STRIDE and record['slot'] < 4
        assert struct.pack('>4I', *self.udc[24:28]) == wanted, self.udc
        assert self.udc[21:24] == [DESC_DMA, record['dma'], 64]
        if published:
            assert self.udc[28:33] == record['cookie'], self.udc
            assert struct.pack('>4I', *self.udc[33:37]) == wanted
            assert self.udc[37:40] == [DESC_DMA, record['dma'], 64]
        self.descriptor_oracles.append(dict(step=len(self.rows)-1, cookie=record['cookie'],
            slot=record['slot'], descriptor_hex=wanted.hex(), published=published))

    def observe(self, token, status, *, facts=7, fault=0, mutation=0,
                reserved=0, buffer=None, next_pointer=0, write=False, result=OK):
        raw = descriptor(status, self.bulk[token]['dma'] if buffer is None else buffer,
                         reserved, next_pointer)
        if write:
            self.step(26, token, 0, 16, data=raw)
        return self.step(22, token, facts, fault, mutation, data=raw, result=result)

    def complete(self, token, length, usb_result=0, result=OK, service=True):
        if token not in self.bulk:
            return super().complete(token, length, usb_result, result, service)
        assert usb_result == 0, 'USB error is an explicit endpoint fault, not a fabricated status'
        self.observe(token, 0x88000000 | length, write=result != STALE, result=result)
        if service:
            self.service()

    def recover_owned(self):
        self.begin_reset()
        token = self.row[30]
        if token:
            self.step(24, token, 1)
            self.service()
        self.finish_reset()

    def fresh_page(self, document, images, generation):
        assert self.row[32] == generation
        self.send(document(['small']), 64)
        self.expected_pixels += images['small'][1]
        self.notification(generation, 1, 0, 1)
        self.repeat_pump()

    def finish(self):
        captures = super().finish()
        data = (self.directory/'output.udc-descriptor').read_bytes()
        assert len(data) == 48
        assert data[16:32] == struct.pack('>4I', *self.udc[24:28]), 'exact final descriptor'
        assert data[:16] == data[32:] == bytes([self.fill])*16, 'complete descriptor canaries'
        captures['descriptor'] = data
        return captures


def scenario(h, name, document, images):
    h.configure()
    initial_generation = h.row[32]
    if name.startswith('document/'):
        size = int(name.rsplit('/', 1)[1])
        h.send(document(['small'])+document([])+document(['slim']), size)
        h.expected_pixels = images['small'][1]+images['slim'][1]
        h.expected_documents = [(initial_generation, 1, 0, 1, 0),
                                (initial_generation, 2, 1, 0, 0)]
        h.notification(initial_generation, 3, 1, 1)
        h.repeat_pump()
        assert h.row[32] == initial_generation and h.udc[2] == FREE
        assert h.udc[10] == h.udc[11] == h.udc[12] and h.udc[13] == 0
        return
    if name.startswith('status-owner/'):
        owner = int(name.rsplit('/', 1)[1])
        for rx, last, count in itertools.product(range(4), (0, 1), (0, 1, 63, 64, 65, 65535)):
            token = h.arm_write(bytes(range(64)))
            status = (owner << 30) | (rx << 28) | (last << 27) | count
            result = WAIT if owner != 2 else OK if rx == 0 and last == 1 and count <= 64 else FAULT
            before = h.row.copy()
            prepared = h.udc.copy()
            h.observe(token, status, write=True, result=result)
            assert h.row[34] == before[34] and h.row[50] == before[50], 'no implicit pump'
            if result == OK:
                assert h.udc[2] == FREE and h.row[30] == 0 and h.row[69:73] == [0]*4
                h.service()
                assert sum(h.row[69:73]) == 1 and h.row[36] == 0
            else:
                assert h.udc[2] == EXPOSED and h.udc[16:21] == prepared[16:21]
                assert h.row[30] == token
                h.observe(token, status, result=result)
                if result == FAULT:
                    assert h.row[7] == h.row[9] == h.row[36] == h.udc[3] == h.udc[4] == 1
                    h.step(7, result=base.STOPPED)
                else:
                    assert h.row[36] == 0 and h.udc[3:5] == [0, 0]
            old_generation = h.row[32]
            h.recover_owned()
            assert h.row[32] == old_generation+1 and h.udc[2] == FREE
        h.fresh_page(document, images, h.row[32])
        return
    if name == 'completion-facts':
        token = h.arm_write(document(['small'])[:31])
        original = h.udc[16:28]
        for facts in range(7):
            h.observe(token, 0x8800001f, facts=facts, result=WAIT)
            assert h.udc[16:28] == original and h.row[30] == token and h.row[69:73] == [0]*4
            h.service()
            assert h.row[69:73] == [0]*4 and h.udc[2] == EXPOSED and h.row[30] == token
            h.step(7, result=base.WAIT)
            assert h.row[33:36] == [1, 0, 1]
            assert h.row[50] == h.row[56] == 0
        raw = descriptor(0x8800001f, h.bulk[token]['dma'])
        for flags in ((2, 1, 1), (1, 2, 1), (1, 1, 2), (255, 1, 1)):
            packed = (flags[0] << 16) | (flags[1] << 8) | flags[2]
            h.step(30, token, packed, data=raw, result=INVALID)
            h.service()
            assert h.row[69:73] == [0]*4 and h.udc[2] == EXPOSED and h.row[30] == token
        # The event's immutable snapshot, not recycled/live descriptor storage,
        # is authoritative even while the original cookie is still current.
        busy = descriptor(0x4800001f, h.bulk[token]['dma'])
        h.step(26, token, 0, 16, data=busy)
        h.step(27, token, 1)
        h.step(26, token, 0, 16, data=raw)
        h.step(28, 1, 7, result=WAIT)
        h.service()
        assert h.row[69:73] == [0]*4 and h.row[30] == token and h.udc[2] == EXPOSED
        h.step(7, result=base.WAIT)
        assert h.row[33:36] == [1, 0, 1] and h.row[50] == h.row[56] == 0
        h.step(27, token, 2)
        h.step(26, token, 0, 16, data=busy)
        h.step(28, 2, 7)
        assert h.udc[2] == FREE and h.row[30] == 0 and h.row[69:73] == [0]*4
        h.service()
        assert sum(h.row[69:73]) == 1
        h.step(7)
        h.send(document(['small'])[31:], 64)
        h.expected_pixels = images['small'][1]
        h.notification(initial_generation, 1, 0, 1)
        return
    if name == 'publication-facts':
        h.step(20, 0, 1, 1, 1)
        h.step(6)
        token = h.row[30]
        assert h.udc[2] == PREPARED and h.udc[11] == 0
        before = h.udc[16:28]
        for flags in itertools.product((0, 1), repeat=3):
            if flags == (1, 1, 1):
                continue
            h.step(21, token, *flags, result=WAIT)
            assert h.udc[16:28] == before and h.udc[11] == 0
            assert h.row[30] == token and h.row[69:73] == [0]*4
        for flags in ((2, 1, 1), (1, 2, 1), (1, 1, 2), (255, 0, 0)):
            h.step(21, token, *flags, result=INVALID)
            assert h.udc[16:28] == before and h.udc[11] == 0
        h.step(21, token, 1, 1, 1)
        h.publication_oracle(token)
        h.step(21, token, 1, 1, 1, result=WAIT)
        h.step(3, token, 31, data=document(['small'])[:31])
        h.complete(token, 31)
        h.step(7)
        h.step(20, 1, 1, 1, 1)
        h.send(document(['small'])[31:], 64)
        h.expected_pixels = images['small'][1]
        h.notification(initial_generation, 1, 0, 1)
        return
    if name.startswith('cancel/'):
        prepared = name.endswith('prepared')
        h.step(20, 0 if prepared else 1, 1, 1, 1)
        h.step(6)
        token = h.row[30]
        if not prepared:
            h.step(3, token, 31, data=document(['small'])[:31])
        before = h.udc[16:28]
        h.step(24, token, 1, result=INVALID)
        assert h.udc[16:28] == before and h.row[30] == token and h.udc[3] == 0
        h.begin_reset()
        assert h.udc[3] == 1 and h.row[30] == token and h.row[36] == 1
        h.step(23, token)
        h.step(21, token, 1, 1, 1, result=WAIT)
        h.step(24, token, 0, result=WAIT)
        h.step(24, token, 2, result=INVALID)
        for mutation in range(1, 6):
            h.step(23, token, d=mutation, result=STALE)
            h.step(24, token, 1, d=mutation, result=STALE)
        assert h.udc[16:28] == before and h.row[30] == token
        if name.endswith('late-success'):
            h.complete(token, 31)
            assert sum(h.row[69:73]) == 0, 'cancelled input never enters READY queue'
        else:
            h.step(24, token, 1)
            h.service()
        assert h.udc[2] == FREE and h.row[30] == 0 and h.row[32] == initial_generation
        assert [h.row[i] for i in (37, 41, 45)] == [0, 0, 0], 'local settlement grants no global promise'
        h.finish_reset()
        h.step(20, 1, 1, 1, 1)
        h.fresh_page(document, images, initial_generation+1)
        return
    if name == 'body-and-endpoint-faults':
        for field in ('reserved', 'buffer', 'next', 'swapped-buffer'):
            token = h.arm_write(b'')
            supplied = dict(reserved=1) if field == 'reserved' else dict(next_pointer=0x12345670) if field == 'next' else dict(
                buffer=0x87654320 if field == 'buffer' else int.from_bytes(h.bulk[token]['dma'].to_bytes(4, 'big'), 'little'))
            h.observe(token, 0x88000000, write=True, result=FAULT, **supplied)
            before = h.udc[16:28]
            epoch = h.row[4]
            h.observe(token, 0x88000000, result=FAULT)
            assert h.row[4] == epoch and h.udc[16:28] == before and h.row[30] == token
            h.step(24, token, 0, result=WAIT)
            h.recover_owned()
        for prepared, fault in itertools.product((False, True), (0x80, 0x200, 0x80000000)):
            h.step(20, 0 if prepared else 1, 1, 1, 1)
            h.step(6)
            token = h.row[30]
            before = h.udc[16:28]
            h.observe(token, 0, facts=0, fault=fault, result=FAULT)
            assert h.udc[3:6] == [1, 1, fault] and h.udc[16:28] == before
            epoch = h.row[4]
            h.observe(token, 0x88000000, facts=7, result=FAULT)
            assert h.row[4] == epoch and h.row[36] == 1
            h.recover_owned()
        h.step(20, 1, 1, 1, 1)
        h.fresh_page(document, images, h.row[32])
        return
    if name == 'submission-rejections':
        for injection in (*range(1, 16), 17):
            before = h.udc[24:28]
            submitted, proposals = h.row[17], h.udc[11]
            h.step(25, injection)
            h.step(6, result=base.ERROR)
            assert h.row[7] == h.row[9] == h.row[36] == 1
            assert h.row[33:36] == [1, 0, 1] and h.row[69:73] == [0]*4
            if injection in (13, 14):
                assert h.row[17] == submitted+1 and h.row[30]
                assert h.udc[2] == (PREPARED if injection == 13 else EXPOSED)
                assert h.udc[3] == 1 and h.udc[11] == proposals+(injection == 14)
                token, retained, counters = h.row[30], h.udc[16:28], h.udc[10:14]
                for _ in range(2):
                    h.step(6, result=base.WAIT)
                    h.step(21, token, 1, 1, 1, result=WAIT)
                    assert h.udc[16:28] == retained and h.udc[10:14] == counters
                    assert h.row[30] == token and h.row[33:36] == [1, 0, 1]
            else:
                assert h.row[17] == submitted and not h.row[30] and h.udc[2] == FREE
                assert h.udc[24:28] == before and h.udc[11] == proposals
            h.recover_owned()
        for dma, size in ((BUFFER_DMA, 0), (BUFFER_DMA, 63), (0xfffffff0, 64), (BUFFER_DMA, 0xffffffff)):
            before = h.udc[24:28]
            h.step(25, 16, dma, size)
            h.step(6, result=base.ERROR)
            assert not h.row[30] and h.udc[24:28] == before and h.udc[2] == FREE
            assert h.row[33:36] == [1, 0, 1] and h.row[69:73] == [0]*4
            h.recover_owned()
        h.fresh_page(document, images, h.row[32])
        return
    if name == 'initial-span-probes':
        original = h.row.copy(), h.udc.copy()
        for kind in (*range(9), 10):
            h.step(29, kind, result=OK if kind == 0 else INVALID)
            assert h.row[2:59] == original[0][2:59]
            assert h.udc[1:44] == original[1][1:44]
        for dma, size, wanted in ((0xfffffff0, 16, OK), (0xfffffff0, 32, INVALID),
                                 (DESC_DMA, 15, INVALID), (DESC_DMA, 0, INVALID)):
            h.step(29, 9, dma, size, result=wanted)
            assert h.row[2:59] == original[0][2:59]
            assert h.udc[1:44] == original[1][1:44]
        h.fresh_page(document, images, initial_generation)
        return
    if name == 'original-cookie-after-reuse':
        old = h.arm_write(b'')
        raw = descriptor(0x88000000, h.bulk[old]['dma'])
        h.step(26, old, 0, 16, data=raw)
        h.step(27, old, 0)
        h.observe(old, 0x88000000)
        h.service()
        h.step(7)
        for _ in range(3):
            h.transfer(b'')
            h.step(7)
        current = h.arm_write(document(['small'])[:31])
        assert h.bulk[old]['slot'] == h.bulk[current]['slot']
        assert h.bulk[old]['dma'] == h.bulk[current]['dma']

        def stale_observations(token):
            baseline = h.row.copy(), h.udc.copy()
            for fault in (0, 0x80):
                h.step(28, 0, 7, fault, result=STALE)
                h.observe(old, 0x88000000, fault=fault, result=STALE)
            h.step(23, old, result=STALE)
            h.step(24, old, 1, result=STALE)
            for mutant in range(1, 6):
                h.observe(token, 0x8800001f, mutation=mutant, result=STALE)
            assert h.row[2:20] == baseline[0][2:20]
            assert h.row[26:63] == baseline[0][26:63]
            assert h.row[69:77] == baseline[0][69:77] and h.row[90:96] == baseline[0][90:96]
            assert h.udc[16:40] == baseline[1][16:40]
            assert h.udc[2] == EXPOSED and h.udc[3:6] == [0, 0, 0]
        stale_observations(current)
        h.complete(current, 31)
        h.step(7)
        h.send(document(['small'])[31:], 64)
        h.expected_pixels = images['small'][1]
        h.notification(initial_generation, 1, 0, 1)
        h.recover()
        current = h.arm_write(document(['small'])[:31])
        stale_observations(current)
        h.complete(current, 31)
        h.step(7)
        h.send(document(['small'])[31:], 64)
        h.expected_pixels += images['small'][1]
        h.notification(initial_generation+1, 1, 0, 1)
        return
    raise AssertionError('unimplemented scenario: '+name)


def original_reference():
    # Reuse completed fragment evidence; do not execute a new stock lifecycle or
    # promote stricter replacement acceptance rules into original behavior.
    from hp1020_xtensa_properties import properties, section_bytes
    stock = ROOT/'analysis/sihp1020.elf'
    blob = stock.read_bytes()
    assert core.sha(blob) == '2111560068db47ceca21fa550db4c7c34f5595b5a5d137ae4a19631e40e3601d'
    sections, _ = properties(blob)
    fragment = section_bytes(blob, sections, 0x100086f4, 0xc4)
    assert core.sha(fragment) == '44aeebdd192f1f632caae561daba16438239e3cc12e8594af7ed6a8aeb7d9b84'
    path = ROOT/'analysis/usb-path/controller-family.json'
    evidence = json.loads(path.read_text())
    assert evidence['status'] == 'pass' and len(evidence['rearm_cases']) == 12
    assert len(evidence['status_decoding_cases']) == 51
    assert all(core.sha((ROOT/name).read_bytes()) == digest for name, digest in evidence['source_sha256'].items())
    assert evidence['upstream_commit'] == 'adc218676eef25575469234709c2d87185ca223a'
    for anchor in evidence['instructions']:
        raw = bytes.fromhex(anchor['bytes'])
        assert section_bytes(blob, sections, int(anchor['address'], 16), len(raw)) == raw
    for case in evidence['rearm_cases']:
        captured = bytes.fromhex(case['descriptor_hex'])
        assert case['status'] == 'pass' and case['entire_guarded_arena_equal']
        assert captured == descriptor(0x08000000, int(case['buffer_pointer'], 16),
                                      reserved=case['fill']*0x01010101)
    for case in evidence['status_decoding_cases']:
        word = int(case['descriptor_status'], 16)
        assert case['owner_admitted'] == (word >> 30 == 2)
        if case['owner_admitted']:
            assert case['decoded_count'] == word & 0xffff
    return dict(report='analysis/usb-path/controller-family.json', report_sha256=core.sha(path.read_bytes()),
        stock_sha256=core.sha(blob), rearm_fragment_sha256=core.sha(fragment),
        completed_rearm_cases_reused=12, completed_status_cases_reused=51,
        original_reserves_bytes_4_to_7=True, replacement_initializes_reserved_to_zero=True,
        replacement_rx_last_capacity_body_policy_is_stricter=True,
        newly_executed_stock_instructions=0)


def sources(temp):
    tested = base.sources(temp)
    selected = set(SRC.glob('*.[ch]')) | set(SRC.glob('*.ld')) | set(COMPONENT.glob('*.[ch]'))
    selected.update(ROOT/'scripts'/name for name in ('validate-hp1020-continuous-printer.py',
        'validate-hp1020-udc-out.py', 'build-hp1020-udc-out-target.sh'))
    selected.add(ROOT/'analysis/usb-path/controller-family.json')
    reference = json.loads((ROOT/'analysis/usb-path/controller-family.json').read_text())
    selected.update(ROOT/name for name in reference['source_sha256'])
    for p in sorted(selected):
        name = str(p.relative_to(ROOT))
        tested[name] = core.sha(p.read_bytes())
        dest = temp/'source'/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, dest)
    (temp/'source-sha256.json').write_text(json.dumps(tested, indent=2)+'\n')
    return tested


def compile_host(temp, effective):
    implementation = [SRC/'fixture.c', SRC/'host-check.c', COMPONENT/'hp1020_udc_out.c',
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', action='store_true')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix='hp1020-udc-out-', dir='/tmp'))
    print('UDC OUT captures: '+str(temp), flush=True)
    tested = sources(temp)
    evidence = original_reference()
    effective = runpy.run_path(str(ROOT/'scripts/prepare-hp1020-tinyusb.py'))['prepare'](temp/'effective-source', True)
    compile_host(temp, temp/'effective-source')
    fixtures = [base.pages.OUT/name for name in (
        'fixtures/32x8-stripe4-black.jbg', 'fixtures/9600x132-stripe128-edges.jbg',
        'fixtures/16384x4-stripe128-edges.jbg', 'output-fixtures/1024x260-stripe128-repeat.jbg',
        'output-fixtures/64x12-stripe4-edges.jbg')]
    fixtures.append(ROOT/'analysis/samples/generated/matrix-a4_default.zjs')
    fixture_hashes = {str(p.relative_to(ROOT)): core.sha(p.read_bytes()) for p in fixtures}
    for p in fixtures:
        dest = temp/'tested-fixtures'/p.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, dest)
    (temp/'fixture-sha256.json').write_text(json.dumps(fixture_hashes, indent=2)+'\n')
    document, images, used_fixtures = base.image_documents(temp)
    assert set(used_fixtures) == set(fixtures)
    profiles = [(name, fill, interface) for fill in (0, 204) for interface in (0, 3)
                for name in ('document/64', 'document/1')]
    profiles += [(name, fill, 3) for fill in (0, 204) for name in
                 ('status-owner/0', 'status-owner/1', 'status-owner/2', 'status-owner/3', 'completion-facts', 'publication-facts', 'cancel/prepared',
                  'cancel/exposed', 'cancel/late-success', 'body-and-endpoint-faults', 'submission-rejections',
                  'initial-span-probes', 'original-cookie-after-reuse')]
    cases, replay = [], []
    for index, (name, fill, interface) in enumerate(profiles):
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
            status='pass', initial=h.initial, initial_udc=h.udc_initial, steps=h.rows, udc_steps=h.udc_rows,
            events=h.events, packet_oracles=h.packets, descriptor_oracles=h.descriptor_oracles,
            expected_documents=h.expected_documents, expected_pixels_sha256=core.sha(h.expected_pixels),
            pixels_bytes=len(h.expected_pixels), capture_sha256={n: core.sha(data) for n, data in captures.items()}))
        replay.append((h, captures, directory))
        print(f'UDC OUT: {len(cases)}/{len(profiles)} host cases passed', flush=True)
    target = None
    if args.target:
        core.command(['bash', ROOT/'scripts/build-hp1020-udc-out-target.sh'])
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
                    [case['fill'], 64, case['interface'], 0xffffffff]) == 0
                initial = list(struct.unpack('>96I', q.read(program.symbols['hp1020_bulk_fixture_stats'], 384)))
                initial_udc = list(struct.unpack('>48I', q.read(program.symbols['hp1020_udc_fixture_stats'], 192)))
                assert initial[:59]+initial[60:] == h.initial[:59]+h.initial[60:]
                assert initial_udc == h.udc_initial
                for index, (event, host_row, host_udc) in enumerate(zip(h.events, h.rows, h.udc_rows)):
                    data = bytes.fromhex(event['data_hex'])
                    if data:
                        q.put(program.symbols['hp1020_bulk_fixture_input'], data)
                    result = q.call0(program.symbols['hp1020_bulk_fixture_step'], event['words'])
                    row = list(struct.unpack('>96I', q.read(program.symbols['hp1020_bulk_fixture_stats'], 384)))
                    udc = list(struct.unpack('>48I', q.read(program.symbols['hp1020_udc_fixture_stats'], 192)))
                    with (directory/'target-steps.jsonl').open('a') as saved:
                        saved.write(json.dumps(row+udc)+'\n')
                    assert result == row[0] == event['result'] and row[15:17] == [0, 1] and udc[7:10] == [0, 1, 1]
                    assert row[:59]+row[60:] == host_row[:59]+host_row[60:], (case['case'], index, row, host_row)
                    assert udc == host_udc, (case['case'], index, udc, host_udc)
                overhead = q.call0(program.symbols['hp1020_udc_fixture_component_bytes'], [])
                observed = {}
                for name, symbol in (('pixels', 'hp1020_bulk_fixture_pixels'), ('wire', 'hp1020_bulk_fixture_wire'),
                                     ('documents', 'hp1020_bulk_fixture_documents')):
                    observed[name] = q.read(program.symbols[symbol], len(captures[name]))
                for name, function in (('receive', 'hp1020_bulk_fixture_receive_storage'),
                    ('output', 'hp1020_bulk_fixture_output_storage'), ('descriptor', 'hp1020_udc_fixture_descriptor_storage')):
                    address = q.call0(program.symbols[function], [])
                    observed[name] = q.read(address, len(captures[name]))
                for name, data in observed.items():
                    (directory/('target-'+name)).write_bytes(data)
                    assert data == captures[name], (case['case'], name)
                native.append(dict(case=case['case'], status='pass', all_steps_equal=True,
                    all_pixels_wire_notifications_descriptors_and_storage_equal=True,
                    adapter_state_and_memory_bytes=row[59], descriptor_component_bytes=overhead,
                    capture_sha256={n: core.sha(data) for n, data in observed.items()}))
                print(f'UDC OUT: {len(native)}/{len(cases)} target cases passed', flush=True)
        target = dict(status='pass', cases=native, qemu_version=version, elf_sha256=core.sha(elf.read_bytes()), audit=audit)
    assert all(core.sha((ROOT/n).read_bytes()) == value for n, value in tested.items()), 'source changed during execution'
    assert all(core.sha((ROOT/n).read_bytes()) == value for n, value in fixture_hashes.items()), 'fixtures changed during execution'
    report = dict(status='pass', original_reference=evidence, source_sha256=tested, effective_source=effective, cases=cases, target=target,
        fixture_sha256=fixture_hashes, completed_native_page_lifecycles=0, usb_transfers=0,
        actual_peripheral_accesses=0, controller_quiescence_established=False,
        scope='One original-cookie RAM descriptor per 64-byte OUT submission, actual patched TinyUSB dispatch and existing bounded receive/JBIG/output with independent byte, packet, notification and pixel oracles.',
        limits='No physical DCD, controller/MMIO/boot/cache/IRQ implementation or printing. Packet64/BE mode, exact CPU/DMA mapping, cache visibility/publication order, immutable original-cookie observations and transfer settlement remain supplied. Descriptor owner bits do not settle DMA or acknowledge global reset promises. Synchronous software output; copies remain metadata.')
    name = 'validation' if args.target else 'host-validation'
    text = json.dumps(report, separators=(',', ':'), sort_keys=True)+'\n'
    (temp/(name+'.json')).write_text(text)
    (OUT/(name+'.json')).write_text(text)
    (OUT/(name+'.md')).write_text('# One-descriptor USB OUT execution\n\n'+report['scope']+'\n\n'+
        f'{len(cases)} host cases; {len(target["cases"]) if target else 0} target cases. Exact bytes, notifications, ownership and storage checked.\n\n'+report['limits']+'\n')


if __name__ == '__main__':
    main()
