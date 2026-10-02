#!/usr/bin/env python3
"""Typed hardware-offload notifications in synthetic RAM.

No controller access or physical USB. Reconstructed requests, automatic status
permission and original-cookie cancellation are distinct from wire completion.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import runpy
import select
import shutil
import struct
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('offload_composed', ROOT/'scripts/validate-hp1020-udc-composed.py')
comp = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = comp
spec.loader.exec_module(comp)
ep0, base, core = comp.ep0, comp.base, comp.core
bulk_reference = comp.bulk_reference
SRC = ROOT/'open-firmware/udc-offload-test'
OUT = ROOT/'analysis/usb-path/udc-offload'
OK, WAIT, STALE, INVALID, FAULT, ADAPTER_ERROR, LIMIT = range(7)
CAPTURE_FACTS, GRANT_FACTS = 0x01010101, 0x0101
MODE_EVIDENCE = ('analysis/usb-path/controller-reference/manuals/README.md',
    'analysis/usb-path/controller-reference/manuals/offload-mode-review.json',
    'analysis/usb-path/controller-reference/manuals/offload-mode-review.tar.gz',
    'analysis/usb-path/controller-reference/manuals/usb2-spec-provenance.json')
CANONICAL = {('SC', 1): bytes.fromhex('0009010000000000'),
             ('SC', 0): bytes.fromhex('0009000000000000'),
             ('SI', 0): bytes.fromhex('010b000000000000')}


class Host(comp.Host):
    def __init__(self, executable, directory, fill, capacity, interface):
        self.offload_rows, self.offload_oracles = [], []
        self.auto_owners, self.typed_offers = {}, {}
        super().__init__(executable, directory, fill, capacity, interface)
        self.offload_initial = self.offload.copy()

    def read_row(self):
        if not select.select([self.process.stdout], [], [], 30)[0]:
            self.process.kill(); self.process.wait()
            raise AssertionError('offload fixture timed out: '+str(self.directory))
        raw = self.process.stdout.readline()
        with (self.directory/'raw-stdout').open('ab') as saved:
            saved.write(raw)
        assert raw, ('fixture ended early', self.directory)
        row = json.loads(raw)
        assert len(row) == 368, row
        self.ep0, self.udc, self.ingress = row[96:200], row[200:248], row[248:288]
        self.offload = row[288:368]
        return row[:96]

    def step(self, op, a=0, b=0, c=0, d=0, data=b'', result=OK, expect=None):
        row = super().step(op, a, b, c, d, data, result, expect)
        self.offload_rows.append(self.offload.copy())
        o = self.offload
        assert o[11:13] == [0,1], ('offload ownership/capture', op, o)
        if o[6] > len(self.auto_owners):
            assert o[6] == len(self.auto_owners)+1
            token = o[16]
            assert token and token not in self.auto_owners and o[13] == 1
            expected_cookie = [row[21], row[3], row[32], 0, 0x80]
            assert o[16:21] == expected_cookie and row[28:30] == [token,0]
            original = self.typed_offers[o[26]]
            assert o[26:31] == original and o[32:35] == [1,0,1]
            assert o[35] in (0,1), 'core BUSY can clear after a retained bind is rejected'
            expected_raw = CANONICAL[('SC',original[2])] if original[1] == 1 else CANONICAL[('SI',0)]
            assert struct.pack('>2I', *o[64:66]) == expected_raw
            assert row[77] == 0, 'automatic status cannot borrow a class response'
            assert self.slot(1)[0] == 0, 'automatic status has no packet descriptor'
            self.auto_owners[token] = dict(cookie=expected_cookie, original=original.copy())
            self.offload_oracles.append(dict(step=len(self.rows)-1, kind='auto_bind',
                canonical_hex=expected_raw.hex(), **self.auto_owners[token]))
        if o[13]:
            assert o[16:21] == self.auto_owners[o[16]]['cookie'], 'original cookie changed'
        with (self.directory/'host-offload-steps.jsonl').open('a') as saved:
            saved.write(json.dumps(self.offload)+'\n')
        return row

    def offer_offload(self, kind=1, cfg=1, interface=0, alt=0, *, sequence=None, result=OK):
        sequence = self.next_sequence() if sequence is None else sequence
        raw_capture = self.ingress[32:36].copy()
        before = self.row[2:96].copy()
        self.step(100, sequence, kind, (cfg<<16)|(interface<<8)|alt, result=result)
        assert self.row[2:96] == before, 'capture cannot dispatch a protocol request'
        assert self.ingress[32:36] == raw_capture, 'typed capture is not a raw SETUP record'
        if result == OK or (result == LIMIT and sequence == 0xffffffff):
            self.typed_offers[sequence] = [sequence,kind,cfg,interface,alt]
            assert self.offload[21:26] == self.typed_offers[sequence]
            self.offload_oracles.append(dict(step=len(self.rows)-1, kind='typed_capture',
                original=self.typed_offers[sequence].copy(), previous_raw_capture=raw_capture))
        return sequence

    def dispatch_offload(self, sequence, *, facts=CAPTURE_FACTS, busy=0, result=OK):
        self.step(101, sequence, facts, busy, result=result)

    def grant(self, sequence, token, *, facts=GRANT_FACTS, mutant=0, result=OK):
        before = self.offload[7]
        self.step(102, sequence, token, facts, mutant, result=result)
        if result == OK:
            original = self.auto_owners[token]
            assert self.offload[7] == before+1
            assert self.offload[37:42] == original['original']
            assert self.offload[42:47] == original['cookie']
            self.offload_oracles.append(dict(step=len(self.rows)-1, kind='auto_grant', **original))
        else:
            assert self.offload[7] == before

    def cancel_retained(self):
        for token in (self.row[26],self.row[28]):
            if token in self.auto_owners:
                self.cancel_auto(token)
            elif token:
                self.step(43,token,1)
        if self.row[30]:
            self.step(64,self.row[30],1)

    def cancel_auto(self, token, *, settled=1, mutant=0, result=OK):
        self.step(103, token, settled, 0, mutant, result=result)


def compile_host(temp, effective):
    ep0_src = ROOT/'open-firmware/udc-ep0'
    out = ROOT/'open-firmware/udc-out'
    setup = ROOT/'open-firmware/udc-setup'
    implementation = [SRC/'fixture.c', SRC/'host-check.c', ep0_src/'hp1020_udc_ep0.c',
        out/'hp1020_udc_out.c', setup/'hp1020_udc_setup.c',
        base.ADAPTER/'hp1020_tusb_adapter.c', base.PRINTER/'hp1020_usb_printer.c',
        base.RX/'hp1020_usb_receive.c', base.RX/'hp1020_usb_document.c']
    implementation += [base.IMG/name for name in ('hp1020_image.c', 'hp1020_image_page.c',
        'hp1020_image_stream.c', 'hp1020_image_ring.c', 'hp1020_image_output.c')]
    implementation += [base.SEM/'hp1020_semantic.c', base.SEM/'hp1020_page_plan.c',
        core.VENDOR/'libjbig/jbig85.c', core.VENDOR/'libjbig/jbig_ar.c']
    implementation += [effective/'src'/name for name in ('tusb.c', 'device/usbd.c', 'common/tusb_fifo.c')]
    flags = ['clang', '-std=c11', '-O1', '-g', '-fno-common', '-Wall', '-Wextra', '-Werror',
        '-fsanitize=address,undefined']
    include = ['-I'+str(p) for p in (SRC, ep0_src, out, setup, ROOT/'open-firmware',
        base.SRC, base.ADAPTER, base.PROTOCOL, base.PRINTER, base.RX, base.IMG, base.SEM,
        core.VENDOR/'libjbig', effective/'src')]
    core.command(flags+include+implementation+['-o', temp/'host'])
    full = ROOT/'vendor/foo2zjs-source'
    core.command(flags+['-I'+str(full), base.IMG/'reference.c', full/'jbig.c', full/'jbig_ar.c',
        '-o', temp/'reference'])


def sources(temp):
    tested = comp.sources(temp)
    selected = set(SRC.glob('*.[ch]')) | set(SRC.glob('*.ld'))
    selected.update(ROOT/'scripts'/name for name in (
        'validate-hp1020-udc-offload.py', 'build-hp1020-udc-offload-target.sh'))
    selected.update(ROOT/name for name in MODE_EVIDENCE)
    for path in sorted(selected):
        name = str(path.relative_to(ROOT)); tested[name] = core.sha(path.read_bytes())
        destination = temp/'source'/name; destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
    (temp/'source-sha256.json').write_text(json.dumps(tested, indent=2)+'\n')
    return tested


def _offload_wire_state(h):
    """Things an automatic status permission may never manufacture."""
    return (tuple(h.row[24:26]), h.offload[57], tuple(h.slot(0)[31:35]),
            tuple(h.slot(1)[31:35]), tuple(h.slot(0)[14:18]),
            tuple(h.slot(1)[14:18]), h.slot(0)[42], h.slot(1)[42])


def _offload_no_wire(h, before):
    assert _offload_wire_state(h) == before, 'automatic status is not an EP0 packet or ACK'


def _offload_owner(h, sequence, kind=1, cfg=1):
    o = h.offload
    token = o[16]
    assert o[13] == 1 and token in h.auto_owners
    assert o[16:21] == h.auto_owners[token]['cookie']
    assert o[26:31] == [sequence, kind, cfg, 0, 0]
    assert o[32:37] == [1, 0, 1, 1, 0]
    assert h.row[28:30] == [token, 0] and h.row[77] == 0
    assert h.slot(0)[0] == h.slot(1)[0] == 0
    return token


def _offload_offer_dispatch(h, kind=1, cfg=1, *, sequence=None):
    epoch = h.row[2]
    n = h.offer_offload(kind, cfg, sequence=sequence)
    assert h.ingress[2:5] == [3, n, n] and h.ingress[11] == 0
    assert h.offload[21:26] == [n, kind, cfg, 0, 0]
    h.dispatch_offload(n)
    assert h.ingress[2:4] == [0, 0] and h.ingress[6] == n
    assert h.row[2] == epoch + 1 and h.ingress[7] == epoch + 1
    assert h.row[3] != h.row[2], 'admission is distinct from service'
    return n


def _offload_activate(h, sequence, kind=1, cfg=1):
    wire = _offload_wire_state(h)
    submissions, last_id, binds = h.row[17], h.row[21], h.offload[6]
    h.service()
    token = _offload_owner(h, sequence, kind, cfg)
    assert token == last_id + 1 and h.row[17] == submissions + 1
    assert h.offload[6] == binds + 1
    assert h.row[2] == h.row[3] and h.row[6] == 0
    assert h.offload[66] == cfg and h.row[68] == 1
    _offload_no_wire(h, wire)
    return token


def _offload_reset(h):
    """Explicit actual-reset input; cancellation is supplied separately."""
    wire = _offload_wire_state(h)
    generation = h.row[32]
    h.step(5)
    assert h.ingress[11] == 1 and h.row[2] != h.row[3]
    if any(h.row[i] for i in (26, 28, 30)):
        h.service(base.WAIT)
        h.cancel_retained()
    h.service()
    assert h.row[2] == h.row[3] and h.ingress[11] == 7
    assert h.row[8] == h.row[10] == h.row[68] == 0 and h.row[32] == generation
    assert h.row[36] == 1 and not any(h.row[i] for i in (26, 28, 30))
    _offload_no_wire(h, wire)


def _offload_recovery(h, token, *, slot=0, order=(1, 2, 4)):
    """Each missing promise must block restart; a held status keeps old G."""
    assert sorted(order) == [1, 2, 4]
    wire = _offload_wire_state(h)
    generation, recovery, cookie = h.row[32], h.row[42], h.auto_owners[token]['cookie'].copy()
    assert h.row[44:48] == [1, 0, 0, 0] and h.row[43] == generation
    h.step(10, slot)
    h.step(12, slot, result=base.WAIT)
    h.step(6, result=base.WAIT)
    parts = 0
    for part in order:
        if part == 4:
            h.step(15)  # Separately modeled bulk/stall/toggle cleanup, never EP0 settlement.
        h.step(11, slot, part)
        parts |= part
        assert h.row[45] == parts and h.row[32] == generation
        assert h.row[42:44] == [recovery, generation]
        if parts != 7:
            h.step(12, slot, result=base.WAIT)
    h.step(12, slot, expect={32: generation + 1, 7: 0, 9: 0, 35: 0, 36: 0, 44: 0, 45: 0})
    assert h.offload[13] == 1 and h.offload[16:21] == cookie
    assert h.row[28] == token and h.row[77] == 0 and h.row[47] == 0
    h.step(10, slot, result=base.WAIT)
    _offload_no_wire(h, wire)
    return generation + 1


def _offload_configured(h, *, recover=True, grant=True):
    _offload_reset(h)
    assert h.offload[49:56] == [0] * 7 and h.offload[67] == 3
    n = _offload_offer_dispatch(h)
    token = _offload_activate(h, n)
    assert h.offload[49:56] == [1, 1, 1, 1, 0, 0, 0]
    assert h.offload[67] == 15 and h.offload[72:76] == [1, 2, 0, 2]
    assert h.row[8] == h.row[10] == h.row[36] == h.row[44] == 1
    assert h.row[45] == h.row[47] == h.row[80] == 0
    if recover:
        _offload_recovery(h, token)
    if grant:
        wire = _offload_wire_state(h)
        h.grant(n, token)
        assert h.offload[13:16] == [1, 0, 1] and h.offload[32:36] == [1, 1, 1, 1]
        _offload_no_wire(h, wire)
    return n, token


def _offload_settle_auto(h, token, *, service=True, result=base.OK):
    wire = _offload_wire_state(h)
    h.cancel_auto(token, settled=0, result=base.WAIT)
    assert h.offload[13] == 1 and h.row[28] == token
    h.cancel_auto(token, result=result)
    if result == base.OK:
        assert h.offload[13] == 0 and h.row[28] == 0
        assert h.offload[34] == 2, 'settled controller owner is still a pending adapter notification'
        assert h.offload[35] == 1, 'do not fake a TinyUSB completion to clear BUSY'
    if service:
        h.service()
    _offload_no_wire(h, wire)


def _offload_grant_rejected(h, n, token, *, facts=GRANT_FACTS, mutant=0, result=STALE):
    before = h.row[2:96].copy()
    owner = h.offload[13:47].copy()
    wire = _offload_wire_state(h)
    h.grant(n, token, facts=facts, mutant=mutant, result=result)
    assert h.row[2:96] == before and h.offload[13:47] == owner
    _offload_no_wire(h, wire)


def _offload_held_block(h):
    h.blocked()
    before = h.row[2:96].copy()
    for op in (8, 9, 12):
        h.step(op, result=base.WAIT)
        assert h.row[2:96] == before


def _offload_cleanup(h, ticket, *, fact=1, result=OK):
    before = h.row[2:96].copy()
    dirty = h.offload[59:63].copy()
    old_cleanups = h.offload[58]
    h.step(107, *ticket, fact, result=result)
    if result == OK:
        assert h.offload[58] == old_cleanups + 1 and h.offload[59] == h.offload[68] == 0
        assert h.offload[60:63] == ticket and h.offload[69:72] == ticket
        assert h.offload[67] == 3 and h.row[12] == 3
        assert h.row[7] == h.row[36] == 1 and h.row[8] == h.row[10] == 0
        assert h.row[32:48] == before[30:46], 'cleanup is not document recovery'
    else:
        assert h.row[2:96] == before and h.offload[59:63] == dirty


def _offload_failed_open(h, slot):
    """Independent first/second open ordering and partial programmed map."""
    assert slot in (1, 2)
    wire = _offload_wire_state(h)
    before = h.offload.copy()
    h.step(106, slot)
    n = _offload_offer_dispatch(h)
    ticket = [n, h.row[2], h.row[4]]  # Original attempt, before any failure fence.
    h.service(base.ERROR)
    wanted = [before[49] + 1, before[50] + (slot == 2),
              before[51] + (slot == 2), before[52]]
    assert h.offload[49:53] == wanted
    assert h.offload[53:56] == before[53:56]
    assert h.offload[72] == before[75] + 1
    assert h.offload[73] == (before[75] + 2 if slot == 2 else before[73])
    assert h.offload[75] == before[75] + slot
    assert h.offload[67] == (7 if slot == 2 else 3)
    assert h.offload[59:63] == [1] + ticket and h.offload[68:72] == [1] + ticket
    assert h.offload[6:8] == before[6:8] and not h.offload[13]
    assert h.row[8] == h.row[10] == h.row[44] == h.offload[66] == 0
    assert h.row[7] == h.row[36] == 1 and h.row[11] & 3 == 3
    assert h.row[4] > ticket[2], 'failure fencing must not restamp the original cleanup ticket'
    h.step(10, result=base.WAIT)
    h.step(6, result=base.WAIT)
    _offload_no_wire(h, wire)
    return n, ticket


def scenario(h, name, document, images):
    assert h.interface == 0 and h.capacity == 64
    assert len(h.offload) == 80 and h.offload[76:80] == [0] * 4

    if name == 'capture-facts':
        _offload_reset(h)
        n = h.offer_offload()
        saved = h.offload[21:26].copy()
        before = h.row[2:96].copy()
        for shift in (24, 16, 8, 0):
            h.dispatch_offload(n, facts=CAPTURE_FACTS & ~(0xff << shift), result=WAIT)
            h.dispatch_offload(n, facts=(CAPTURE_FACTS & ~(0xff << shift)) | (2 << shift), result=INVALID)
            assert h.row[2:96] == before and h.offload[21:26] == saved
        h.dispatch_offload(n, busy=1, result=WAIT)
        h.dispatch_offload(n + 1, result=STALE)
        assert h.row[2:96] == before
        newer = h.next_sequence()
        h.offer_offload(1, 0, sequence=newer, result=WAIT)
        assert h.offload[21:26] == saved
        _offload_held_block(h)
        # The later physical event is already known, though still caller-owned.
        # Free the one bridge slot, then immediately retry that ORIGINAL event
        # before servicing the superseded SC1 or proposing any old status grant.
        h.dispatch_offload(n)
        h.offer_offload(1, 0, sequence=newer)
        h.dispatch_offload(newer)
        assert h.offload[6:8] == [0, 0] and h.row[28] == 0
        token = _offload_activate(h, newer, cfg=0)
        assert h.offload[49:56] == [0] * 7 and h.offload[67] == 3
        assert h.row[8] == h.row[10] == h.row[44] == 0 and h.row[68] == 1
        assert all(owner['original'][0] != n for owner in h.auto_owners.values())
        _offload_grant_rejected(h, n, token)
        h.grant(newer, token)
        on = _offload_offer_dispatch(h)
        h.service(base.WAIT)
        _offload_settle_auto(h, token, service=False)
        current = _offload_activate(h, on)
        _offload_recovery(h, current)
        h.grant(on, current)
        h.fresh_page(document, images)
        return

    if name.startswith('unsupported/'):
        unconfigured = name.endswith('/unconfigured-SI')
        if unconfigured:
            _offload_reset(h)
            old = None
        else:
            old = _offload_configured(h)
        values = {
            'unsupported/config2': (1, 2, 0, 0),
            'unsupported/alt1': (2, 1, 0, 1),
            'unsupported/interface1': (2, 1, 1, 0),
            'unsupported/unconfigured-SI': (2, 1, 0, 0),
            'unsupported/out-of-domain': (1, 0xff, 0, 0),
        }
        kind, cfg, interface, alt = values[name]
        n = h.offer_offload(kind, cfg, interface, alt)
        before, opened = h.row[2:96].copy(), h.offload[49:56].copy()
        h.dispatch_offload(n, result=FAULT)
        assert h.row[2:96] == before and h.offload[49:56] == opened
        assert h.ingress[2:5] == [3, n, n]
        if old:
            _offload_grant_rejected(h, *old, result=WAIT)
        _offload_held_block(h)
        saved = h.offload[21:26].copy()
        _offload_reset(h)
        assert h.offload[21:26] == saved, 'reset supersedes permission, not captured evidence'
        h.offer_offload(kind, cfg, interface, alt, sequence=n, result=STALE)
        n2 = _offload_offer_dispatch(h)
        token = _offload_activate(h, n2)
        _offload_recovery(h, token)
        h.grant(n2, token)
        h.fresh_page(document, images)
        return

    if name.startswith('programming-failure/'):
        _offload_reset(h)
        _, ticket = _offload_failed_open(h, 1 if name.endswith('/OUT') else 2)
        partial = h.offload[67]
        for field in range(3):
            bad = ticket.copy()
            bad[field] ^= 0x80000000
            _offload_cleanup(h, bad, result=STALE)
        _offload_cleanup(h, ticket, fact=2, result=INVALID)
        _offload_cleanup(h, ticket, fact=0, result=WAIT)
        # A new supported request is copied but cannot retry an open while dirty.
        newer = h.offer_offload()
        opens = h.offload[49:56].copy()
        h.dispatch_offload(newer, result=WAIT)
        assert h.offload[49:56] == opens and h.offload[67] == partial
        # Actual reset changes the control epoch, not the failed-attempt identity.
        saved = h.offload[21:26].copy()
        _offload_reset(h)
        assert h.offload[59:63] == [1] + ticket and h.offload[67] == partial
        assert h.offload[21:26] == saved and h.row[2] != ticket[1]
        n = h.offer_offload()
        h.dispatch_offload(n, result=WAIT)
        _offload_cleanup(h, ticket)
        assert h.ingress[2:5] == [3, n, n] and h.ingress[11] == 0
        h.dispatch_offload(n)
        token = _offload_activate(h, n)
        _offload_recovery(h, token)
        h.grant(n, token)
        h.fresh_page(document, images)
        return

    if name == 'cleanup-replay-new-failure':
        _offload_reset(h)
        _, first = _offload_failed_open(h, 2)
        _offload_cleanup(h, first)
        _, second = _offload_failed_open(h, 2)
        assert second != first and second[0] > first[0] and second[1] > first[1]
        _offload_cleanup(h, first, result=STALE)
        assert h.offload[67] == 7 and h.offload[68:72] == [1] + second
        _offload_cleanup(h, second)
        n = _offload_offer_dispatch(h)
        token = _offload_activate(h, n)
        _offload_recovery(h, token)
        h.grant(n, token)
        h.fresh_page(document, images)
        return

    if name.startswith('status-submission-failure/'):
        _offload_reset(h)
        fail = 1 if name.endswith('/before-bind') else 2
        h.step(14, fail)
        n = _offload_offer_dispatch(h)
        wire = _offload_wire_state(h)
        h.service(base.ERROR)
        assert h.offload[49:56] == [1, 1, 1, 1, 0, 0, 0]
        assert h.offload[67] == 15 and h.offload[59] == 0
        assert h.row[7] == h.row[36] == 1 and h.row[44] == 0
        assert h.offload[35] == 0 and h.offload[7] == 0
        if fail == 1:
            assert h.offload[6] == h.offload[13] == h.row[28] == 0
        else:
            token = h.offload[16]
            assert h.offload[13:16] == [1, 1, 0]
            assert h.offload[32:36] == [1, 0, 1, 0]
            _offload_grant_rejected(h, n, token)
            h.cancel_auto(token)
            assert h.offload[34] == 2 and h.row[28] == 0
            h.service()
        h.step(10, result=base.WAIT)
        _offload_no_wire(h, wire)
        _offload_reset(h)
        n = _offload_offer_dispatch(h)
        token = _offload_activate(h, n)
        _offload_recovery(h, token)
        h.grant(n, token)
        h.fresh_page(document, images)
        return

    if name in ('configuration-delayed-grant', 'grant-before-recovery'):
        n, token = _offload_configured(h, recover=False, grant=False)
        wire, before = _offload_wire_state(h), h.row[2:96].copy()
        for _ in range(3):
            h.service()
            assert h.row[2:96] == before
        for facts, result in ((0, WAIT), (1, WAIT), (0x100, WAIT), (0x201, INVALID), (0x102, INVALID)):
            _offload_grant_rejected(h, n, token, facts=facts, result=result)
        if name == 'grant-before-recovery':
            h.grant(n, token)
            assert h.row[44:46] == [1, 0] and h.row[36] == 1
            h.step(6, result=base.WAIT)
            _offload_recovery(h, token, order=(4, 1, 2))
        else:
            _offload_recovery(h, token, order=(2, 4, 1))
            assert h.offload[18] + 1 == h.row[32]
            h.grant(n, token)
        _offload_grant_rejected(h, n, token)
        _offload_no_wire(h, wire)
        h.fresh_page(document, images)
        return

    if name == 'raw-programming-failure-IN':
        _offload_reset(h)
        h.step(106, 2)
        raw = base.packet(0, 9, 1)
        raw_sequence = h.capture(raw)
        h.dispatch(raw_sequence)
        ticket = [0, h.row[2], h.row[4]]  # Raw attempt has no typed sequence.
        wire = _offload_wire_state(h)
        h.service()  # Raw core rejection is observed via EP0 STALL/no owner.
        assert h.offload[49:56] == [1, 1, 1, 0, 0, 0, 0]
        assert h.offload[59:63] == [1] + ticket and h.offload[68:72] == [1] + ticket
        assert h.offload[67] == 7 and h.row[12] == 7
        assert h.offload[72:76] == [1, 2, 0, 2]
        assert h.row[8] == h.row[10] == h.row[44] == h.row[28] == 0
        assert h.row[7] == h.row[36] == h.row[68] == 1 and h.row[11] & 3 == 3
        assert h.offload[5:8] == [0, 0, 0]
        _offload_no_wire(h, wire)
        h.setup(raw)
        assert h.offload[49:56] == [1, 1, 1, 0, 0, 0, 0]
        assert h.offload[59:63] == [1] + ticket and h.offload[67] == 7
        assert h.row[28] == h.row[44] == 0
        _offload_cleanup(h, ticket, fact=0, result=WAIT)
        _offload_cleanup(h, [1, ticket[1], ticket[2]], result=STALE)
        _offload_cleanup(h, ticket)
        h.setup(raw)
        assert h.offload[49:56] == [2, 2, 2, 1, 0, 0, 0]
        assert h.offload[67] == 15 and h.offload[72:76] == [3, 4, 0, 4]
        assert h.row[8] == h.row[10] == h.row[44] == h.row[68] == 1
        assert h.row[28] and h.row[28] not in h.auto_owners
        h.control_status('raw-config-after-explicit-programming-cleanup')
        _offload_cleanup(h, ticket, result=STALE)
        h.step(10)
        h.finish_reset(ack=False)
        h.fresh_page(document, images)
        return

    n, token = _offload_configured(h, grant=False)
    generation = h.row[32]

    if name == 'grant-cookie-identity':
        _offload_grant_rejected(h, n + 1, token)
        for mutation in range(1, 6):
            _offload_grant_rejected(h, n, token, mutant=mutation)
            before = h.row[2:96].copy()
            h.cancel_auto(token, mutant=mutation, result=base.STALE)
            h.step(104, token, 0x80, 0, mutation, result=base.STALE)
            h.step(105, token, 0, 0, mutation, result=base.STALE)
            assert h.row[2:96] == before
        h.grant(n, token)
        _offload_grant_rejected(h, n, token)
        new = _offload_offer_dispatch(h)
        h.service(base.WAIT)
        _offload_settle_auto(h, token, service=False)
        current = _offload_activate(h, new)
        assert current != token and h.auto_owners[token]['cookie'][1] < h.auto_owners[current]['cookie'][1]
        before = h.row[2:96].copy()
        h.cancel_auto(token, result=base.STALE)
        h.step(104, token, 0x80, result=base.STALE)
        h.step(105, token, 0, result=base.STALE)
        _offload_grant_rejected(h, new, token)
        assert h.row[2:96] == before
        h.grant(new, current)
        _offload_recovery(h, current)
        h.fresh_page(document, images)
        return

    if name == 'repeat-configuration-recovery':
        small, empty, slim = document(['small']), document([]), document(['slim'])
        h.send(small[:31], 19, zlp=False)
        bulk = h.arm_write(small[31:62])
        assert h.row[50] == 0 and h.row[90:93] == [0, 0, 0]
        memory = h.row[60:62].copy()
        recovery = h.row[42]
        wire = _offload_wire_state(h)
        repeat = _offload_offer_dispatch(h)
        assert h.row[7] == h.row[36] == 1 and h.row[14] & 6 == 6
        h.service(base.WAIT)
        assert h.offload[55] == 0 and h.row[60:62] == memory
        _offload_settle_auto(h, token, service=False)
        h.service(base.WAIT)
        assert h.offload[55] == 0 and h.row[60:62] == memory
        h.step(64, bulk, 0, result=WAIT)
        h.step(64, bulk, 1)
        current = _offload_activate(h, repeat)
        assert h.offload[49:56] == [2, 2, 2, 2, 0, 0, 1]
        assert h.offload[72:76] == [4, 5, 3, 5] and h.offload[67] == 15
        assert h.row[42] == recovery + 1 and h.row[44:46] == [1, 0]
        assert h.row[32] == generation and h.row[60:62] == memory and h.row[68] == 1
        stable = h.row[2:96].copy(), h.offload[49:76].copy()
        for _ in range(3):
            h.service()
            assert (h.row[2:96], h.offload[49:76]) == stable
        _offload_recovery(h, current)
        h.grant(repeat, current)
        h.send(small + empty + slim, 64)
        h.expected_pixels = images['small'][1] + images['slim'][1]
        h.expected_documents += [(generation + 1, 1, 0, 1, 0), (generation + 1, 2, 1, 0, 0)]
        h.notification(generation + 1, 3, 1, 1)
        assert h.row[32] == generation + 1 and h.row[57:59] == [2, 2]
        h.repeat_pump()
        _offload_no_wire(h, wire)
        # Identical canonical bytes from RAW provenance must use ordinary EP0.
        h.setup(base.packet(0, 9, 1), service_result=base.WAIT)
        _offload_settle_auto(h, current, service=False)
        h.service()
        assert h.offload[26:31] == [0] * 5 and h.slot(1)[0] != 0
        assert h.row[28] not in h.auto_owners
        assert h.offload[49:56] == [3, 3, 3, 3, 0, 0, 2]
        assert h.offload[72:76] == [7, 8, 6, 8] and h.row[68] == 1
        assert h.row[42] == recovery + 2 and h.row[44:46] == [1, 0]
        h.control_status('raw-repeat-configuration-status')
        assert h.offload[57] == wire[1] + 1 and h.row[32] == generation + 1
        h.step(10)
        packets = h.row[17]
        h.finish_reset(ack=False)
        assert h.row[17] == packets and h.row[32] == generation + 2
        h.fresh_page(document, images)
        return

    if name == 'deconfigure-repeat-reconfigure':
        bulk = h.arm_write(document(['small'])[:31])
        memory = h.row[60:62].copy()
        off = _offload_offer_dispatch(h, cfg=0)
        assert h.row[7] == h.row[36] == 1 and h.row[14] & 6 == 6
        assert h.offload[55] == 0 and h.row[8] == h.row[10] == 1
        h.service(base.WAIT)
        _offload_settle_auto(h, token, service=False)
        h.service(base.WAIT)
        assert h.offload[55] == 0 and h.row[60:62] == memory
        h.step(64, bulk, 0, result=WAIT)
        h.step(64, bulk, 1)
        current = _offload_activate(h, off, cfg=0)
        assert h.offload[55] == 1 and h.offload[67] == 3
        assert h.offload[72:76] == [1, 2, 3, 3]
        assert h.row[8] == h.row[10] == h.row[44] == 0 and h.row[32] == generation
        assert h.row[60:62] == memory
        h.step(10, result=base.WAIT)
        h.grant(off, current)
        repeated = _offload_offer_dispatch(h, cfg=0)
        h.service(base.WAIT)
        _offload_settle_auto(h, current, service=False)
        current = _offload_activate(h, repeated, cfg=0)
        assert h.offload[55] == 1 and h.offload[75] == 3 and h.row[44] == 0
        h.grant(repeated, current)
        on = _offload_offer_dispatch(h)
        h.service(base.WAIT)
        _offload_settle_auto(h, current, service=False)
        current = _offload_activate(h, on)
        assert h.offload[49:56] == [2, 2, 2, 2, 0, 0, 1]
        assert h.offload[72:76] == [4, 5, 3, 5]
        _offload_recovery(h, current)
        h.grant(on, current)
        h.fresh_page(document, images)
        return

    if name in ('interface-reselection', 'interface-halt-reselection'):
        h.fresh_page(document, images)
        halted = name == 'interface-halt-reselection'
        if halted:
            h.setup(base.packet(2, 3, index=1), service_result=base.WAIT)
            _offload_settle_auto(h, token, service=False)
            h.service()
            h.control_status('halt-OUT-before-interface-reselection')
            h.request(base.packet(2, 3, index=0x81), label='halt-IN-before-interface-reselection')
            assert h.row[81:85] == [1, 1, 1, 1] and h.row[7] == h.row[36] == 1
        keep = h.offload[49:56].copy(), h.offload[67:76].copy()
        recovery = h.row[42]
        selected = _offload_offer_dispatch(h, kind=2)
        assert h.row[7] == h.row[36] == 1
        if not halted:
            h.service(base.WAIT)
            _offload_settle_auto(h, token, service=False)
        current = _offload_activate(h, selected, kind=2)
        assert (h.offload[49:56], h.offload[67:76]) == keep
        assert h.row[42] == recovery + 1 and h.row[44:46] == [1, 0]
        if halted:
            _offload_grant_rejected(h, selected, current, result=WAIT)
            assert h.row[81:85] == [1, 1, 1, 1] and h.row[45] == 0
            h.step(15)  # Explicit supplied affected-endpoint defaults, not a document promise.
            assert h.row[81:85] == [0, 0, 0, 0] and h.row[44:46] == [1, 0]
            assert h.row[32] == generation and h.row[7] == h.row[36] == 1
            h.grant(selected, current)
        _offload_recovery(h, current)
        if not halted:
            h.grant(selected, current)
        h.fresh_page(document, images)
        return

    if name == 'new-raw-held-blocks-grant':
        raw = base.packet(0x80, 8, length=1)
        epoch, cookie = h.row[2], h.auto_owners[token]['cookie'].copy()
        new = h.capture(raw)
        h.dispatch(new, facts=0x010001, result=WAIT)
        assert h.row[2] == epoch and h.offload[16:21] == cookie
        _offload_grant_rejected(h, n, token, result=WAIT)
        _offload_held_block(h)
        h.dispatch(new, service=True, service_result=base.WAIT)
        _offload_grant_rejected(h, n, token)
        _offload_settle_auto(h, token, service=False)
        h.service()
        h.control_in(b'\x01', 'configuration-after-automatic-owner')
        assert h.row[32] == generation and h.offload[57] == 1
        h.fresh_page(document, images)
        return

    if name == 'reset-retry-held-offload':
        held = h.offer_offload(2, 1)
        h.dispatch_offload(held, facts=0x00010101, result=WAIT)
        _offload_grant_rejected(h, n, token, result=WAIT)
        snapshot, epoch = h.offload[21:26].copy(), h.row[2]
        reset = h.next_sequence()
        h.step(83, reset, 0, 1, result=WAIT)
        assert h.ingress[2:4] == [2, reset] and h.row[2] == epoch
        newer = h.next_sequence()
        h.offer_offload(1, 1, sequence=newer, result=WAIT)
        h.step(83, newer, result=WAIT)
        h.step(83, held, result=STALE)
        h.dispatch_offload(held, result=WAIT)
        _offload_held_block(h)
        h.step(83, reset)
        assert h.ingress[5] == reset and h.ingress[11] == 1
        assert h.offload[21:26] == snapshot
        _offload_grant_rejected(h, n, token, result=WAIT)
        h.service(base.WAIT)
        _offload_settle_auto(h, token, service=False)
        h.service()
        assert h.row[8] == h.row[10] == 0 and h.ingress[11] == 7
        h.offer_offload(2, 1, sequence=held, result=STALE)
        h.offer_offload(1, 1, sequence=newer)
        h.dispatch_offload(newer)
        current = _offload_activate(h, newer)
        _offload_recovery(h, current)
        h.grant(newer, current)
        h.fresh_page(document, images)
        return

    if name == 'reset-after-grant':
        h.grant(n, token)
        h.step(5)
        reset = h.ingress[5]
        saved = h.auto_owners[token]['cookie'].copy()
        h.service(base.WAIT)
        assert h.offload[13:16] == [1, 1, 1] and h.offload[16:21] == saved
        newer = h.offer_offload()
        h.dispatch_offload(newer, result=WAIT)
        assert h.ingress[11] == 1
        _offload_grant_rejected(h, n, token, result=WAIT)
        _offload_settle_auto(h, token, service=False)
        h.service()
        assert h.ingress[11] == 0 and h.ingress[5] == reset
        _offload_held_block(h)
        h.dispatch_offload(newer)
        current = _offload_activate(h, newer)
        _offload_recovery(h, current)
        h.grant(newer, current)
        h.fresh_page(document, images)
        return

    if name == 'old-generation-fault-and-success':
        before = h.row[2:96].copy()
        assert h.auto_owners[token]['cookie'][2] + 1 == generation
        h.step(104, token, 0x80, result=base.STALE)
        assert h.row[2:96] == before
        wire = _offload_wire_state(h)
        h.step(105, token, 0, result=base.INVALID)
        assert h.offload[13:16] == [1, 1, 0] and h.offload[34] == 1
        assert h.row[7] == h.row[36] == 0 and h.row[32] == generation
        _offload_grant_rejected(h, n, token)
        _offload_settle_auto(h, token)
        assert h.offload[34] == 0 and h.offload[35] == 1
        assert h.row[7] == h.row[36] == 0
        _offload_no_wire(h, wire)
        h.fresh_page(document, images)
        return

    if name in ('current-owner-fault', 'current-owner-success-rejected', 'same-config-recovers-fault'):
        # A repeat binds a fresh current-G owner and starts a new recovery, but
        # cannot restart the document before the three separately supplied facts.
        fresh = _offload_offer_dispatch(h)
        h.service(base.WAIT)
        _offload_settle_auto(h, token, service=False)
        token = _offload_activate(h, fresh)
        wire = _offload_wire_state(h)
        assert h.auto_owners[token]['cookie'][2] == generation
        if name == 'current-owner-success-rejected':
            h.step(105, token, 0, result=base.INVALID)
        else:
            h.step(104, token, 0x80)
            fenced = h.row[2:96].copy()
            h.step(104, token, 0x80)
            assert h.row[2:96] == fenced, 'same unsettled packet fault is idempotent'
        assert h.row[7] == h.row[36] == 1 and h.offload[13:15] == [1, 1]
        assert h.row[28] == token and h.offload[34] == 1
        _offload_grant_rejected(h, fresh, token)
        _offload_settle_auto(h, token)
        _offload_no_wire(h, wire)
        if name == 'same-config-recovers-fault':
            recovery, opened = h.row[42], h.offload[49:56].copy()
            repeated = _offload_offer_dispatch(h)
            token = _offload_activate(h, repeated)
            assert h.row[42] == recovery + 1 and h.row[44:46] == [1, 0]
            assert h.offload[49:56] == [opened[0]+1, opened[1]+1,
                opened[2]+1, opened[3]+1, opened[4], opened[5], opened[6]+1]
            assert h.row[7] == h.row[36] == 1 and h.row[68] == 1
            stable = h.row[2:96].copy(), h.offload[49:76].copy()
            for _ in range(3):
                h.service()
                assert (h.row[2:96], h.offload[49:76]) == stable
            h.grant(repeated, token)
            h.step(6, result=base.WAIT)
            _offload_recovery(h, token)
            h.fresh_page(document, images)
            return
        _offload_reset(h)
        on = _offload_offer_dispatch(h)
        token = _offload_activate(h, on)
        _offload_recovery(h, token)
        h.grant(on, token)
        h.fresh_page(document, images)
        return

    if name == 'held-offload-blocks-deferred-reset':
        h.setup(base.packet(0x21, 2, index=0), service_result=base.WAIT)
        _offload_settle_auto(h, token, service=False)
        h.service()
        assert h.row[44] == h.row[47] == 1 and h.row[28] == 0
        h.step(10)
        epoch, recovery = h.row[2], h.row[42]
        held = h.offer_offload()
        h.dispatch_offload(held, facts=0x01000101, result=WAIT)
        _offload_held_block(h)
        for part in (1, 2, 4):
            if part == 4:
                h.step(15)
            h.step(11, 0, part)
        assert h.row[45] == 7 and h.row[32] == generation
        before = h.row[2:96].copy()
        h.step(12, result=base.WAIT)
        assert h.row[2:96] == before and h.row[2] == epoch and h.row[28] == 0
        h.dispatch_offload(held)
        current = _offload_activate(h, held)
        assert h.row[42] == recovery + 1 and h.row[44:48] == [1, 0, 0, 0]
        wire = _offload_wire_state(h)
        h.step(11, 0, 4, result=base.STALE)
        h.step(12, 0, result=base.STALE)
        assert h.row[32] == generation and h.row[45] == 0
        _offload_recovery(h, current, slot=1)
        assert h.row[28] == current and h.row[77] == 0
        _offload_no_wire(h, wire)
        h.grant(held, current)
        h.fresh_page(document, images)
        return

    if name == 'sequence-exhaustion':
        last = _offload_offer_dispatch(h, sequence=0xfffffffe)
        h.service(base.WAIT)
        _offload_settle_auto(h, token, service=False)
        token = _offload_activate(h, last)
        before = h.row[2:96].copy()
        h.offer_offload(sequence=0xffffffff, result=LIMIT)
        assert h.row[2:96] == before
        assert h.ingress[2:5] == [3, 0xffffffff, 0xffffffff]
        assert h.ingress[10:12] == [1, 0] and h.offload[13:15] == [1, 0]
        _offload_grant_rejected(h, last, token, result=LIMIT)
        h.dispatch_offload(0xffffffff, result=LIMIT)
        h.offer_offload(sequence=0, result=LIMIT)
        h.offer_offload(sequence=last, result=LIMIT)
        _offload_held_block(h)
        wire = _offload_wire_state(h)
        _offload_settle_auto(h, token, service=False)
        assert h.offload[34] == 2 and h.udc[44] == 0x200
        _offload_held_block(h)
        _offload_no_wire(h, wire)
        # This is terminally held adapter notification, not a completed lifecycle.
        return

    if name == 'transport-identity-exhaustion':
        h.step(20, 0, 0xffffffff)
        failed = h.offer_offload(1, 0)
        h.dispatch_offload(failed, result=LIMIT)
        assert h.row[86] == 1 and h.row[4] == 0xffffffff
        assert h.ingress[10] == 2 and h.ingress[11] == 0
        assert h.row[7] == h.row[36] == 1 and h.offload[13:15] == [1, 1]
        _offload_grant_rejected(h, n, token, result=LIMIT)
        _offload_settle_auto(h, token, service=False)
        assert h.offload[34] == 2
        _offload_held_block(h)
        return

    raise AssertionError('unimplemented typed offload profile: ' + name)


def profiles():
    names = (
        'capture-facts',
        'configuration-delayed-grant', 'grant-before-recovery', 'grant-cookie-identity',
        'repeat-configuration-recovery', 'deconfigure-repeat-reconfigure',
        'interface-reselection', 'interface-halt-reselection', 'new-raw-held-blocks-grant',
        'reset-retry-held-offload', 'reset-after-grant',
        'held-offload-blocks-deferred-reset',
        'unsupported/config2', 'unsupported/alt1', 'unsupported/interface1',
        'unsupported/unconfigured-SI', 'unsupported/out-of-domain',
        'programming-failure/OUT', 'programming-failure/IN', 'cleanup-replay-new-failure',
        'raw-programming-failure-IN',
        'status-submission-failure/before-bind', 'status-submission-failure/after-bind',
        'current-owner-fault', 'current-owner-success-rejected',
        'same-config-recovers-fault', 'old-generation-fault-and-success',
        'sequence-exhaustion', 'transport-identity-exhaustion',
    )
    return [(name, fill, 0) for fill in (0, 204) for name in names]


# Deliberate first-draft exclusions (do not advertise them as tested):
# - No actual CSR_DONE/register write, wire ACK, controller-mode discovery,
#   IRQ sampling or physical rejection/STALL policy.
# - Unsupported values remain held until actual reset; no generic recovery.
# - No automatic-owner success-completion contract is proposed.
# - No auto-bind argument-forging API exists in this fixture; the real SC/SI
#   path checks the legal IN0/NULL/0 form and raw-vs-typed provenance instead.
# - Only transport-identity saturation has an existing test-only seed; control,
#   submission and class-recovery MAX seeds are not invented here.
# - Cleanup token mutation/replay and reset supersession are covered; inducing
#   every impossible internal prepared/delivering state is not an external test.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', action='store_true')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix='hp1020-udc-offload-', dir='/tmp'))
    print('Typed offload captures: '+str(temp), flush=True)
    tested = sources(temp)
    evidence = dict(setup=comp.setup_original_reference(ROOT, core.sha),
                    ep0=ep0.original_reference(), bulk=bulk_reference.original_reference())
    fixtures = [base.pages.OUT/name for name in (
        'fixtures/32x8-stripe4-black.jbg', 'fixtures/9600x132-stripe128-edges.jbg',
        'fixtures/16384x4-stripe128-edges.jbg', 'output-fixtures/1024x260-stripe128-repeat.jbg',
        'output-fixtures/64x12-stripe4-edges.jbg')]
    fixtures.append(ROOT/'analysis/samples/generated/matrix-a4_default.zjs')
    fixture_bytes = {str(p.relative_to(ROOT)): p.read_bytes() for p in fixtures}
    fixture_hashes = {n: core.sha(raw) for n,raw in fixture_bytes.items()}
    for name,raw in fixture_bytes.items():
        destination = temp/'tested-fixtures'/name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
    (temp/'fixture-sha256.json').write_text(json.dumps(fixture_hashes, indent=2)+'\n')

    def unchanged():
        assert all(core.sha((ROOT/n).read_bytes()) == digest for n,digest in tested.items()), 'source changed during execution'
        assert all((ROOT/n).read_bytes() == raw for n,raw in fixture_bytes.items()), 'fixture changed during execution'

    effective = runpy.run_path(str(ROOT/'scripts/prepare-hp1020-tinyusb.py'))['prepare'](temp/'effective-source', True)
    compile_host(temp, temp/'effective-source')
    document, images, used = base.image_documents(temp)
    assert set(used) == set(fixtures)
    unchanged()
    cases, replay = [], []
    matrix = profiles()
    for index,(name,fill,interface) in enumerate(matrix):
        directory = temp/f'case-{index:03}'
        directory.mkdir()
        title = f'{name}/fill={fill}/capacity=64/interface={interface}'
        (directory/'case-name').write_text(title+'\n')
        h = Host(temp/'host', directory, fill, 64, interface)
        try:
            scenario(h,name,document,images)
            captures = h.finish()
        finally:
            h.abort()
        assert len(h.events) == len(h.rows) == len(h.ep0_rows) == len(h.out_rows) == len(h.setup_rows) == len(h.offload_rows)
        cases.append(dict(case=title, scenario=name, fill=fill, capacity=64, interface=interface,
            status='pass', initial=h.initial, initial_ep0=h.ep0_initial,
            initial_bulk=h.out_initial, initial_setup=h.setup_initial, initial_offload=h.offload_initial,
            steps=h.rows, ep0_steps=h.ep0_rows, bulk_steps=h.out_rows, setup_steps=h.setup_rows, offload_steps=h.offload_rows,
            events=h.events, packet_oracles=h.packets, descriptor_oracles=h.descriptor_oracles,
            bulk_descriptor_oracles=h.bulk_oracles, setup_oracles=h.ingress_oracles, offload_oracles=h.offload_oracles,
            expected_documents=h.expected_documents, expected_pixels_sha256=core.sha(h.expected_pixels),
            pixels_bytes=len(h.expected_pixels), capture_sha256={n:core.sha(raw) for n,raw in captures.items()}))
        replay.append((h,captures,directory))
        print(f'Typed offload: {len(cases)}/{len(matrix)} host cases passed', flush=True)
    unchanged()
    target = None
    if args.target:
        core.command(['bash', ROOT/'scripts/build-hp1020-udc-offload-target.sh'])
        built = OUT/'target'
        assert json.loads((built/'effective-source.json').read_text()) == effective
        saved = temp/'target'
        saved.mkdir()
        for path in built.iterdir():
            if path.is_file() and path.name != 'annotated-disassembly.txt':
                shutil.copyfile(path, saved/path.name)
        elf = saved/'target-check.elf'
        artifacts = {p.name:core.sha(p.read_bytes()) for p in saved.iterdir() if p.is_file()}
        program, audit = core.audit_target(elf)
        assert all(core.sha((saved/n).read_bytes()) == digest for n,digest in artifacts.items()), 'audit changed a build artifact'
        artifacts['annotated-disassembly.txt'] = core.sha((saved/'annotated-disassembly.txt').read_bytes())
        (temp/'target-sha256.json').write_text(json.dumps(artifacts, indent=2)+'\n')
        unchanged()
        from hp1020_qemu_ram import QemuRAM
        native = []

        def rows(q):
            result = []
            for symbol,length in (('hp1020_bulk_fixture_stats',96),('hp1020_ep0_fixture_stats',104),
                                  ('hp1020_composed_out_stats',48),('hp1020_composed_setup_stats',40),
                                  ('hp1020_offload_fixture_stats',80)):
                result.append(list(struct.unpack('>'+str(length)+'I',q.read(program.symbols[symbol],length*4))))
            return result

        with QemuRAM() as q:
            version = q.version
            for case,(h,captures,directory) in zip(cases,replay):
                q.load(elf)
                assert q.call0(program.symbols['hp1020_bulk_fixture_reset'],[case['fill'],64,case['interface'],0xffffffff]) == 0
                initial,e,b,s,o = rows(q)
                assert initial[:59]+initial[60:] == h.initial[:59]+h.initial[60:]
                assert (e,b,s,o) == (h.ep0_initial,h.out_initial,h.setup_initial,h.offload_initial)
                for index,(event,host_row,host_ep0,host_bulk,host_setup,host_offload) in enumerate(zip(
                        h.events,h.rows,h.ep0_rows,h.out_rows,h.setup_rows,h.offload_rows)):
                    data = bytes.fromhex(event['data_hex'])
                    if data:
                        q.put(program.symbols['hp1020_bulk_fixture_input'],data)
                    result = q.call0(program.symbols['hp1020_bulk_fixture_step'],event['words'])
                    row,e,b,s,o = rows(q)
                    with (directory/'target-steps.jsonl').open('a') as output:
                        output.write(json.dumps(row+e+b+s+o)+'\n')
                    assert result == row[0] == event['result'] and row[15:17] == [0,1]
                    assert e[2:5] == [0,1,1] and b[7:10] == [0,1,1] and s[12:15] == [0,1,3] and o[11:13] == [0,1]
                    assert row[:59]+row[60:] == host_row[:59]+host_row[60:], (case['case'],index,row,host_row)
                    assert (e,b,s,o) == (host_ep0,host_bulk,host_setup,host_offload), (case['case'],index,e,b,s,o)
                observed = {}
                for name,symbol in (('pixels','hp1020_bulk_fixture_pixels'),('wire','hp1020_bulk_fixture_wire'),
                                    ('documents','hp1020_bulk_fixture_documents')):
                    observed[name] = q.read(program.symbols[symbol],len(captures[name]))
                for name,symbol in (('receive','hp1020_bulk_fixture_receive_storage'),
                        ('output','hp1020_bulk_fixture_output_storage'),('ep0','hp1020_ep0_fixture_storage'),
                        ('bulk_descriptor','hp1020_composed_fixture_out_storage'),
                        ('setup_record','hp1020_composed_fixture_setup_storage')):
                    observed[name] = q.read(q.call0(program.symbols[symbol],[]),len(captures[name]))
                for name,symbol in (('ep0','hp1020_ep0_fixture_storage_bytes'),
                        ('bulk_descriptor','hp1020_composed_fixture_out_storage_bytes'),
                        ('setup_record','hp1020_composed_fixture_setup_storage_bytes')):
                    assert q.call0(program.symbols[symbol],[]) == len(captures[name])
                sizes = {}
                for name,symbol in (('ep0','hp1020_ep0_fixture_component_bytes'),
                        ('bulk','hp1020_composed_fixture_out_component_bytes'),
                        ('setup','hp1020_composed_fixture_setup_component_bytes')):
                    sizes[name] = q.call0(program.symbols[symbol],[])
                assert sizes['ep0'] == 296 and sizes['bulk'] == 80
                for name,raw in observed.items():
                    (directory/('target-'+name)).write_bytes(raw)
                    assert raw == captures[name], (case['case'],name)
                native.append(dict(case=case['case'],status='pass',all_steps_equal=True,
                    all_pixels_wire_notifications_descriptors_and_storage_equal=True,
                    typed_captures_original_cookies_and_grants_equal=True,
                    adapter_state_and_memory_bytes=row[59],component_and_allocation_bytes=sizes,
                    capture_sha256={n:core.sha(raw) for n,raw in observed.items()}))
                print(f'Typed offload: {len(native)}/{len(cases)} target cases passed',flush=True)
        assert all(core.sha((saved/n).read_bytes()) == digest for n,digest in artifacts.items()), 'captured target changed'
        target = dict(status='pass',cases=native,qemu_version=version,elf_sha256=core.sha(elf.read_bytes()),
                      audit=audit,captured_artifact_sha256=artifacts)
    unchanged()
    report = dict(status='pass',source_sha256=tested,fixture_sha256=fixture_hashes,effective_source=effective,
        original_reference=evidence,offload_mode_evidence={n:tested[n] for n in MODE_EVIDENCE},
        hp_dynamic_csr_capability_established=False,automatic_grants_are_acknowledgments=False,
        cases=cases,target=target,completed_native_page_lifecycles=0,
        usb_transfers=0,actual_peripheral_accesses=0,controller_quiescence_established=False,
        scope='Typed configuration/interface notifications and one-shot automatic status proposals through actual TinyUSB plus ordered raw SETUP, EP0 and bulk descriptors to exact continuous documents in synthetic RAM. Reconstructed canonical requests, original cookies, partial programming and cleanup identities have independent oracles.',
        limits='No physical DCD, MMIO, IRQ, cache, boot, USB traffic or printing. Dynamic CSR capability/mode, original event order, request validation, current coherent status, endpoint programming, stall clearing and settlement remain supplied. The original startup does not establish HP dynamic status gating. A status grant is neither a CSR write nor wire completion/ACK and never invokes TinyUSB completion. Only configuration0/1 and interface0/alternate0 are supported here; unsupported notifications remain held until an actual ordered reset. Cleanup is an explicitly supplied original-attempt fact, not a reset promise. Copies remain metadata and output is synchronous.')
    name = 'validation' if args.target else 'host-validation'
    raw = json.dumps(report,sort_keys=True,separators=(',',':'))+'\n'
    (temp/(name+'.json')).write_text(raw)
    (OUT/(name+'.json')).write_text(raw)
    (OUT/(name+'.md')).write_text('# Typed USB offload execution\n\n'+report['scope']+'\n\n'+
        f'{len(cases)} host; {len(target["cases"]) if target else 0} QEMU cases. Every typed/raw capture, original cookie, automatic grant proposal, partial programming state, exact packet, pixel, document event and guarded allocation is compared.\n\n'+report['limits']+'\n')


if __name__ == '__main__':
    main()
