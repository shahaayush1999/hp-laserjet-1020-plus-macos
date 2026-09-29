#!/usr/bin/env python3
"""Continuous document boundaries through a synthetic reusable USB adapter.

No physical USB/controller/output, firmware upload, or printing. Configuration,
transfer completion, and all three recovery promises are explicitly supplied.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import runpy
import shutil
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('continuous_printer_base', ROOT/'scripts/validate-hp1020-tinyusb-printer.py')
base = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = base
spec.loader.exec_module(base)
core, pages = base.core, base.pages
OUT = ROOT/'analysis/usb-path/continuous-printer'
OK, WAIT, STALE, INVALID, LIMIT, ERROR = range(6)
STOPPED, PAYLOAD = 3, 8
ORDER, TRUNCATED = 2, 5


class Host(base.Host):
    def __init__(self, executable, directory, fill, capacity, interface):
        self.directory, self.interface, self.capacity = directory, interface, capacity
        self.stderr = (directory/'stderr').open('wb')
        self.process = subprocess.Popen([str(executable), str(fill), str(capacity), str(interface), str(0xffffffff)] +
            [str(directory/name) for name in ('pixels', 'wire', 'receive', 'output', 'documents')],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.stderr)
        self.initial = self.row = self.read_row()
        assert self.initial[0:2] == [0, 0] and self.initial[15:17] == [0, 1], self.initial
        self.events, self.rows, self.packets = [], [], []
        self.expected_pixels, self.expected_documents = b'', []
        self.requested = 0

    def configure(self):
        self.step(5)
        self.service()
        self.request(base.packet(0, 9, 1))
        assert self.row[8] == self.row[10] == self.row[36] == self.row[44] == 1
        assert self.row[47] == self.row[80] == 0, 'configuration must not invent a class request'
        self.step(6, result=WAIT, expect={33: 0, 35: 0})
        self.step(10)
        packets = self.row[17]
        self.finish_reset(ack=False)
        assert self.row[17] == packets and self.row[80] == 0 and not self.row[13]

    def notification(self, generation, document_id, first_page, count, result=0):
        self.expected_documents.append((generation, document_id, first_page, count, result))
        accepted = sum(event[4] == 0 for event in self.expected_documents)
        assert self.row[90:92] == [len(self.expected_documents), accepted], self.row
        assert self.row[93] == generation and self.row[95] == document_id

    def repeat_pump(self, stopped=False):
        before = self.row.copy()
        for _ in range(3):
            self.step(7, result=STOPPED if stopped else OK)
            assert self.row[32:47] == before[32:47]
            assert self.row[50:62] == before[50:62] and self.row[69:77] == before[69:77]
            assert self.row[90:96] == before[90:96]
        assert self.row[40] == 0, 'normal document boundaries do not finalize input'

    def finish(self):
        captures = super().finish()
        observed = (self.directory/'documents').read_bytes()
        expected = b''.join(struct.pack('>5I', *record) for record in self.expected_documents)
        assert observed == expected, ('document notifications', self.directory, observed.hex(), expected.hex())
        captures['documents'] = observed
        return captures


def scenario(h, name, document, images):
    h.configure()
    generation = h.row[32]
    small, slim, empty = document(['small']), document(['slim']), document([])
    raw_small, raw_slim = images['small'][1], images['slim'][1]

    def next_small():
        assert h.row[32] == generation+1
        h.send(small, min(64, h.capacity))
        assert h.row[32] == generation+1
        h.expected_pixels += raw_small
        h.notification(generation+1, 1, 0, 1)
        h.repeat_pump()

    if name.startswith('continuous/adjacent/'):
        size = int(name.rsplit('/', 1)[1])
        h.send(small+empty+slim, min(size, h.capacity))
        h.expected_documents = [(generation, 1, 0, 1, 0), (generation, 2, 1, 0, 0)]
        h.notification(generation, 3, 1, 1)
        assert h.row[32] == generation and h.row[92] == 3 and h.row[58] == 2
        h.expected_pixels = raw_small+raw_slim
        h.repeat_pump()
        h.send(empty, min(size, h.capacity))
        h.notification(generation, 4, 2, 0)
        assert h.row[32] == generation and h.row[92] == 4 and h.row[58] == 2
    elif name == 'continuous/mixed-pages':
        names = ['medium', 'wide', 'small', 'partial']
        h.send(document(names), 19)
        h.expected_pixels = b''.join(images[n][1] for n in names)
        h.notification(generation, 1, 0, 4)
        assert h.row[58] == 4 and h.row[54] == 0 and h.row[73:77] == [0]*4
        h.repeat_pump()
        h.send(slim, 64)
        h.expected_pixels += raw_slim
        h.notification(generation, 2, 4, 1)
    elif name == 'continuous/page-before-document':
        assert small[-16:] == pages.pack([(1, b'', 0, 0)])
        h.send(small[:-16], 19)
        assert h.row[50] == len(raw_small) and h.row[58] == 1 and h.row[54] == 0
        assert h.row[90:93] == [0, 0, 0] and h.row[56] == 1
        h.repeat_pump()
        for piece in (b'', small[-16:-11], b'', small[-11:-1]):
            if piece:
                h.send(piece, 19, zlp=False)
            else:
                h.transfer(b'')
                h.step(7)
            assert h.row[90:93] == [0, 0, 0]
        h.send(small[-1:], 19)
        h.notification(generation, 1, 0, 1)
        h.expected_pixels = raw_small
        h.repeat_pump()
    elif name == 'continuous/empty-boundaries':
        h.send(b'', 19)
        assert h.row[56:59] == [0, 0, 0] and h.row[90:93] == [0, 0, 0]
        h.send(empty[:-1], 1)
        assert h.row[90:93] == [0, 0, 0]
        h.send(empty[-1:], 1)
        h.notification(generation, 1, 0, 0)
        h.send(empty+empty, 64)
        h.expected_documents.append((generation, 2, 0, 0, 0))
        h.notification(generation, 3, 0, 0)
        assert h.row[57:59] == [0, 0] and h.row[50] == h.row[55] == 0
    elif name == 'failure/truncated-document':
        h.send(document(['medium'])[:-16], 64)
        h.expected_pixels = images['medium'][1]
        assert h.row[50] == len(h.expected_pixels) and h.row[58] == 1 and h.row[54] == 0
        assert h.row[90:93] == [0, 0, 0]
        h.step(8)
        h.step(9, result=PAYLOAD, expect={39: TRUNCATED, 40: 0, 36: 1})
        h.repeat_pump(stopped=True)
        h.recover()
        next_small()
    elif name == 'failure/after-first-document':
        # A valid END_DOC is observed before the following malformed chunk.
        h.transfer(small+b'JZJZ'+bytes(16))
        h.transfer(slim)
        h.step(7, result=PAYLOAD, expect={35: 2, 36: 1, 40: 0})
        assert h.row[33:36] == [2, 0, 2] and h.row[69:73] == [1, 1, 0, 0]
        h.expected_pixels = raw_small
        h.notification(generation, 1, 0, 1)
        assert h.row[56] == 1 and h.row[58] == 1 and h.row[54] == 0
        h.repeat_pump(stopped=True)
        h.recover()
        next_small()
    elif name == 'failure/document-notification':
        h.step(17, 1)
        h.transfer(small+empty+slim)
        h.transfer(small)
        h.step(7, result=PAYLOAD, expect={35: 2, 36: 1, 39: ORDER, 40: 0})
        assert h.row[33:36] == [2, 0, 2] and h.row[69:73] == [1, 1, 0, 0]
        h.expected_pixels = raw_small
        h.expected_documents = [(generation, 1, 0, 1, 0)]
        h.notification(generation, 2, 1, 0, ORDER)
        assert h.row[56] == 2 and h.row[58] == 1 and h.row[92] == 1
        assert h.row[54] == 0 and h.row[73:77] == [0]*4
        h.repeat_pump(stopped=True)
        h.step(17, 0xffffffff)
        h.recover()
        next_small()
    elif name.startswith('failure/page-output/'):
        accepted = int(name.rsplit('/', 1)[1])
        h.step(16, accepted)
        h.transfer(small)
        h.transfer(slim)
        h.step(7, result=PAYLOAD, expect={35: 2, 36: 1, 39: ORDER, 40: 0})
        assert h.row[33:36] == [2, 0, 2] and h.row[69:73] == [1, 1, 0, 0]
        assert h.row[57:59] == [1, 0] and h.row[90:93] == [0, 0, 0]
        assert h.row[52:55] == [accepted, 0, accepted]
        assert h.row[73:77] == [2 if accepted else 1, 0, 0, 0]
        h.expected_pixels = raw_small if accepted else b''
        h.repeat_pump(stopped=True)
        h.step(16, 0xffffffff)
        h.recover()
        next_small()
    elif name == 'failure/completion-counter-limit':
        h.step(18, 0xfffffffe)
        h.transfer(empty+empty)
        h.step(7, result=PAYLOAD, expect={36: 1, 39: 3, 92: 0xffffffff})
        h.notification(generation, 0xffffffff, 0, 0)
        assert h.row[56] == 0xffffffff and h.row[50] == h.row[55] == 0
        h.repeat_pump(stopped=True)
        h.recover()
        next_small()
    elif name == 'continuous/copies-still-metadata':
        chunks = pages.chunks(small)
        items = bytearray(chunks[1][1])
        matches = 0
        for offset in range(0, len(items), 12):
            if struct.unpack_from('>H', items, offset+4)[0] == 4:
                struct.pack_into('>I', items, offset+8, 4)
                matches += 1
        assert matches == 1
        chunks[1] = (chunks[1][0], bytes(items), chunks[1][2], chunks[1][3])
        h.send(b'JZJZ'+pages.pack(chunks), 19)
        h.expected_pixels = raw_small
        h.notification(generation, 1, 0, 1)
        assert h.row[57:59] == [1, 1], 'copies are not replayed by this bounded output'
    else:
        raise AssertionError(name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', action='store_true')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix='hp1020-continuous-printer-', dir='/tmp'))
    print('Continuous printer captures: '+str(temp), flush=True)
    tested = base.sources(temp)
    own = 'scripts/validate-hp1020-continuous-printer.py'
    tested[own] = core.sha((ROOT/own).read_bytes())
    shutil.copyfile(ROOT/own, temp/'source'/own)
    (temp/'source-sha256.json').write_text(json.dumps(tested, indent=2)+'\n')
    effective = runpy.run_path(str(ROOT/'scripts/prepare-hp1020-tinyusb.py'))['prepare'](temp/'effective-source', True)
    base.compile_host(temp, temp/'effective-source')
    document, images, fixtures = base.image_documents(temp)
    profiles = []
    for fill in (0, 204):
        for interface in (0, 3):
            for name in ('continuous/adjacent/1', 'continuous/adjacent/1024',
                'continuous/page-before-document', 'continuous/empty-boundaries'):
                profiles.append((name, fill, 1024, interface))
        for name in ('continuous/mixed-pages', 'failure/truncated-document', 'failure/after-first-document',
            'failure/document-notification', 'failure/page-output/0', 'failure/page-output/1',
            'failure/completion-counter-limit', 'continuous/copies-still-metadata'):
            profiles.append((name, fill, 1024, 3))
        profiles.append(('continuous/adjacent/19', fill, 64, 0))
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
            expected_documents=h.expected_documents, expected_pixels_sha256=core.sha(h.expected_pixels),
            pixels_bytes=len(h.expected_pixels), capture_sha256={n: core.sha(data) for n, data in captures.items()}))
        replay.append((h, captures, directory))
        print(f'Continuous printer: {len(cases)}/{len(profiles)} host cases passed', flush=True)
    target = None
    if args.target:
        core.command(['bash', ROOT/'scripts/build-hp1020-tinyusb-printer-target.sh'])
        elf = base.OUT/'target/target-check.elf'
        assert json.loads((base.OUT/'target/effective-source.json').read_text()) == effective
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
                initial = list(struct.unpack('>96I', q.read(program.symbols['hp1020_bulk_fixture_stats'], 384)))
                assert initial[:59]+initial[60:] == h.initial[:59]+h.initial[60:]
                for index, (event, host_row) in enumerate(zip(h.events, h.rows)):
                    data = bytes.fromhex(event['data_hex'])
                    if data:
                        q.put(program.symbols['hp1020_bulk_fixture_input'], data)
                    result = q.call0(program.symbols['hp1020_bulk_fixture_step'], event['words'])
                    row = list(struct.unpack('>96I', q.read(program.symbols['hp1020_bulk_fixture_stats'], 384)))
                    with (directory/'target-steps.jsonl').open('a') as saved:
                        saved.write(json.dumps(row)+'\n')
                    assert result == row[0] == event['result'] and row[15:17] == [0, 1]
                    assert row[:59]+row[60:] == host_row[:59]+host_row[60:], (case['case'], index, row, host_row)
                observed = {}
                for name, symbol in (('pixels', 'hp1020_bulk_fixture_pixels'), ('wire', 'hp1020_bulk_fixture_wire'),
                                     ('documents', 'hp1020_bulk_fixture_documents')):
                    observed[name] = q.read(program.symbols[symbol], len(captures[name]))
                for name, function in (('receive', 'hp1020_bulk_fixture_receive_storage'), ('output', 'hp1020_bulk_fixture_output_storage')):
                    address = q.call0(program.symbols[function], [])
                    observed[name] = q.read(address, len(captures[name]))
                for name, data in observed.items():
                    (directory/('target-'+name)).write_bytes(data)
                    assert data == captures[name], (case['case'], name)
                native.append(dict(case=case['case'], status='pass', all_steps_equal=True,
                    all_pixels_wire_notifications_and_storage_equal=True, component_state_and_memory_bytes=row[59],
                    capture_sha256={n: core.sha(data) for n, data in observed.items()}))
                print(f'Continuous printer: {len(native)}/{len(cases)} target cases passed', flush=True)
        target = dict(status='pass', cases=native, qemu_version=version, elf_sha256=core.sha(elf.read_bytes()), audit=audit)
    assert all(core.sha((ROOT/n).read_bytes()) == h for n, h in tested.items()), 'source changed during execution'
    report = dict(status='pass', source_sha256=tested, effective_source=effective, cases=cases, target=target,
        fixture_sha256={str(p.relative_to(ROOT)): core.sha(p.read_bytes()) for p in fixtures},
        completed_native_page_lifecycles=0, usb_transfers=0,
        scope='Validated END_PAGE drains and exactly-once document observations through patched pinned TinyUSB, reusable receive and bounded JBIG/output, with independent document traces and exact pixels.',
        limits='Synthetic DCD and synchronous software output only. Startup recovery supplies all three quiescence promises; no fabricated SOFT_RESET is used for configuration. Normal documents need no EOF/reset. Explicit close still detects truncation. Notification errors stop current input and preserve earlier observations. Copies remain metadata. No controller/MMIO/boot/cache, physical status, USB traffic or printing.')
    name = 'validation' if args.target else 'host-validation'
    text = json.dumps(report, indent=2, sort_keys=True)+'\n'
    (temp/(name+'.json')).write_text(text)
    (OUT/(name+'.json')).write_text(text)
    (OUT/(name+'.md')).write_text('# Continuous printer document execution\n\n'+report['scope']+'\n\n'+
        f'{len(cases)} host cases; {len(target["cases"]) if target else 0} target cases. Exact pixels, notification tuples, retained storage and packet proposals checked.\n\n'+report['limits']+'\n')


if __name__ == '__main__':
    main()
