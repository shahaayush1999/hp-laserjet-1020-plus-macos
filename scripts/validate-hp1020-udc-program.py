#!/usr/bin/env python3
"""Endpoint-register command construction through recording I/O in RAM only.

Experimental runner. Every register observation is supplied, never computed from
writes. No physical controller, USB, DMA, ACK or printing evidence is claimed.
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
spec = importlib.util.spec_from_file_location('program_offload', ROOT/'scripts/validate-hp1020-udc-offload.py')
off = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = off
spec.loader.exec_module(off)
comp, ep0, base, core = off.comp, off.ep0, off.base, off.core
bulk_reference = off.bulk_reference
SRC = ROOT/'open-firmware/udc-program-test'
OUT = ROOT/'analysis/usb-path/udc-program'
PROGRAM = ROOT/'open-firmware/udc-program'
MODE_EVIDENCE = off.MODE_EVIDENCE
OK, WAIT, STALE, INVALID, FAULT, ADAPTER_ERROR = range(6)
ORACLES = ROOT/'open-firmware/udc-program-test/trace-oracles.py'

def compile_host(temp, effective):
    ep0_src = ROOT/'open-firmware/udc-ep0'
    out = ROOT/'open-firmware/udc-out'
    setup = ROOT/'open-firmware/udc-setup'
    implementation = [SRC/'fixture.c', SRC/'host-check.c', ep0_src/'hp1020_udc_ep0.c',
        out/'hp1020_udc_out.c', setup/'hp1020_udc_setup.c', PROGRAM/'hp1020_udc_program.c',
        base.ADAPTER/'hp1020_tusb_adapter.c', base.PRINTER/'hp1020_usb_printer.c',
        base.RX/'hp1020_usb_receive.c', base.RX/'hp1020_usb_document.c']
    implementation += [base.IMG/name for name in ('hp1020_image.c', 'hp1020_image_page.c',
        'hp1020_image_stream.c', 'hp1020_image_ring.c', 'hp1020_image_output.c')]
    implementation += [ROOT/'open-firmware/image-pump/hp1020_image_pump.c']
    implementation += [base.SEM/'hp1020_semantic.c', base.SEM/'hp1020_page_plan.c',
        core.VENDOR/'libjbig/jbig85.c', core.VENDOR/'libjbig/jbig_ar.c']
    implementation += [effective/'src'/name for name in ('tusb.c', 'device/usbd.c', 'common/tusb_fifo.c')]
    flags = ['clang', '-std=c11', '-O1', '-g', '-fno-common', '-Wall', '-Wextra', '-Werror',
        '-fsanitize=address,undefined']
    include = ['-I'+str(p) for p in (SRC, PROGRAM, ep0_src, out, setup, ROOT/'open-firmware',
        base.SRC, base.ADAPTER, base.PROTOCOL, base.PRINTER, base.RX, base.IMG, base.SEM,
        core.VENDOR/'libjbig', effective/'src')]
    core.command(flags+include+implementation+['-o', temp/'host'])
    full = ROOT/'vendor/foo2zjs-source'
    core.command(flags+['-I'+str(full), base.IMG/'reference.c', full/'jbig.c', full/'jbig_ar.c',
        '-o', temp/'reference'])


def sources(temp):
    tested = off.sources(temp)
    selected = set(SRC.glob('*.[ch]')) | set(SRC.glob('*.ld')) | set(PROGRAM.glob('*.[ch]'))
    selected.add(ORACLES)
    selected.update(ROOT/'scripts'/name for name in (
        'validate-hp1020-udc-program.py', 'build-hp1020-udc-program-target.sh',
        'check-hp1020-udc-program.py'))
    for path in sorted(selected):
        if not path.is_file():
            continue
        name = str(path.relative_to(ROOT)); tested[name] = core.sha(path.read_bytes())
        destination = temp/'source'/name; destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
    (temp/'source-sha256.json').write_text(json.dumps(tested, indent=2)+'\n')
    return tested


O = runpy.run_path(str(ORACLES))
INITIAL = O['PROGRAM_OUT_INITIAL'] + O['PROGRAM_IN_INITIAL']
RESELECT = O['PROGRAM_OUT_RESELECT'] + O['PROGRAM_IN_RESELECT']
SI = O['PROGRAM_OUT_SI'] + O['PROGRAM_IN_SI']
CLOSE, GRANT = O['PROGRAM_CLOSE_UNHALTED'], O['PROGRAM_GRANT']


def profiles():
    return O['programming_profiles']() + [(name, fill, 64, 0)
        for name in ('program/raw-configuration-field-guards', 'program/raw-sc0-after-reset')
        for fill in (0, 204)]


# Host wrapper for the independent recording-I/O fixture ABI.
PROGRAM_WORDS = 64


class Host(off.Host):
    def __init__(self, executable, directory, fill, capacity, interface):
        self.program_rows = []
        self.expected_trace, self.expected_reads = [], []
        self.program_oracles = []
        self.current_grant_facts = bytes([1]*5)
        super().__init__(executable, directory, fill, capacity, interface)
        self.program_initial = self.program.copy()
        assert self.program[1:8] == [1, 0, 0, 0, 0, 0, 0]
        assert self.program[24:32] == [0, 0, 0, 0, 0, 0, 1, 0]

    def read_row(self):
        if not select.select([self.process.stdout], [], [], 30)[0]:
            self.process.kill(); self.process.wait()
            raise AssertionError('program fixture timed out: '+str(self.directory))
        raw = self.process.stdout.readline()
        with (self.directory/'raw-stdout').open('ab') as saved:
            saved.write(raw)
        assert raw, ('fixture ended early', self.directory)
        row = json.loads(raw)
        assert len(row) == 432, row
        self.ep0, self.udc, self.ingress = row[96:200], row[200:248], row[248:288]
        self.offload, self.program = row[288:368], row[368:432]
        return row[:96]

    def step(self, op, a=0, b=0, c=0, d=0, data=b'', result=OK, expect=None):
        row = super().step(op, a, b, c, d, data, result, expect)
        self.program_rows.append(self.program.copy())
        p = self.program
        assert p[2:4] == [0, 0] and p[30:32] == [1, 0], ('program guards', op, p)
        assert p[26] == len(self.expected_trace), ('unexpected hook access', op, p, self.expected_trace)
        assert p[24] == len(self.expected_reads)
        assert p[27:30] == [sum(row[2] == k for row in self.expected_trace) for k in (1, 2, 3)]
        with (self.directory/'host-program-steps.jsonl').open('a') as saved:
            saved.write(json.dumps(p)+'\n')
        return row

    def facts(self, values):
        assert len(values) == 7
        self.step(122, data=bytes(values))
        assert self.program[36:43] == values

    def grant_facts(self, values):
        assert len(values) == 5
        self.current_grant_facts = bytes(values)

    def program_ready(self):
        return self.program[7] == 1

    def program_failed(self):
        return self.program[4] == 1

    def completed_mask(self):
        return self.program[5]

    def failure_ticket(self):
        return self.program[16:19].copy()

    def failure_consumed(self):
        return self.program[23]

    def complete_selection(self, result=OK):
        return self.step(123, result=result)

    def grant(self, sequence, token, *, mutant=0, result=OK):
        before_wire = off._offload_wire_state(self)
        grants = self.offload[7]
        was_granted = self.offload[33]
        self.step(124, sequence, token, mutant, data=self.current_grant_facts, result=result)
        off._offload_no_wire(self, before_wire)
        consumed = int(not was_granted and self.offload[33] == 1)
        assert self.offload[7] == grants+consumed
        if consumed:
            original = self.auto_owners[token]
            assert self.offload[37:42] == original['original']
            assert self.offload[42:47] == original['cookie']
        if result == OK:
            assert consumed == 1 and self.offload[13] == 1
        if result == FAULT:
            assert self.program_failed()

    def cleanup(self, ticket, *, fact=1, result=OK):
        before = self.row[32:48].copy()
        self.step(126, *ticket, fact, result=result)
        assert self.row[32:48] == before, 'programming cleanup cannot recover a document'
        if result == OK:
            assert self.program[4:8] == [0, 0, 0, 0]
            assert self.program[10:13] == [0, 0, 0]
            assert self.offload[59] == 0 and self.row[8] == self.row[10] == 0

    def io(self, expected, invoke):
        """Supply literal observations, then compare the complete attempted trace."""
        expected = tuple(expected)
        trace_start, read_start = len(self.expected_trace), len(self.expected_reads)
        reads = [tuple(entry[1:]) for entry in expected if entry[0] == 1]
        assert len(reads) <= 85
        if reads:
            self.expected_reads.extend(reads)
            self.step(120, len(reads), data=b''.join(struct.pack('>3I', *row) for row in reads))
        failures = [(i, row) for i, row in enumerate(expected) if row[0] != 1 and row[3]]
        assert len(failures) <= 1
        if failures:
            index, row = failures[0]
            self.step(121, row[0], trace_start+index+1, row[3])
        event_index = len(self.events)+1
        self.expected_trace.extend((event_index, trace_start+i+1, kind, offset,
                                    value if kind != 1 or outcome == 0 else 0, outcome)
                                   for i, (kind, offset, value, outcome) in enumerate(expected))
        value = invoke()
        assert len(self.events) == event_index, 'a trace belongs to one actual API event'
        assert self.program[25] == len(self.expected_reads), 'every supplied prefix read is consumed once'
        assert self.program[35] == 0, 'write/order failure injection must be consumed'
        self.program_oracles.append(dict(event=event_index, trace_begin=trace_start,
            trace_end=len(self.expected_trace), read_begin=read_start,
            read_end=len(self.expected_reads), literal_trace=[list(r) for r in expected]))
        return value

    def finish(self):
        captures = super().finish()
        storage = bytearray()
        for name, suffix, rows, width in (
                ('program_reads', '.program-read-script', self.expected_reads, 3),
                ('program_trace', '.program-trace', self.expected_trace, 6)):
            raw = (self.directory/('output'+suffix)).read_bytes()
            expected = b''.join(struct.pack('>'+str(width)+'I', *row) for row in rows)
            assert raw == expected, (self.directory, name, len(raw), len(expected))
            captures[name] = raw
            capacity = 256 if width == 3 else 1024
            storage += bytes([self.fill])*16 + expected
            storage += bytes([self.fill])*((capacity-len(rows))*width*4+16)
        raw = (self.directory/'output.program-storage').read_bytes()
        assert len(raw) == 27712 and raw == storage
        captures['program_storage'] = raw
        assert self.program[24:26] == [len(self.expected_reads)]*2
        assert self.program[26] == len(self.expected_trace)
        return captures


# Scenarios use the actual fixture APIs and independently supplied traces.

def activate(h, sequence, trace, kind=1, cfg=1):
    return h.io(trace, lambda: off._offload_activate(h, sequence, kind, cfg))


def configure(h, *, recover=False, grant=False, trace=None):
    n = off._offload_offer_dispatch(h)
    token = activate(h, n, trace if trace is not None else INITIAL)
    assert h.program_ready() and h.row[44:46] == [1, 0]
    if grant:
        h.io(GRANT, lambda: h.grant(n, token))
    if recover:
        off._offload_recovery(h, token)
    return n, token


def reset_and_cleanup(h, ticket, *, test_pending=False):
    generation = h.row[32]
    h.step(5)
    assert h.failure_ticket() == ticket and h.program_failed()
    if any(h.row[i] for i in (26, 28, 30)):
        h.service(WAIT)
        h.cleanup(ticket, result=WAIT)
        h.cancel_retained()
        if test_pending:
            h.cleanup(ticket, result=WAIT)
    h.service()
    assert h.row[8] == h.row[10] == 0 and h.row[36] == 1
    assert h.row[32] == generation and h.failure_ticket() == ticket
    h.cleanup(ticket, fact=0, result=WAIT)
    h.cleanup([ticket[0], ticket[1]+1, ticket[2]], result=STALE)
    h.cleanup(ticket)
    assert not h.program_failed() and not h.program_ready()
    assert h.row[32] == generation and h.row[44] == 0
    h.cleanup(ticket, result=STALE)


def failed_configuration(h, trace):
    n = off._offload_offer_dispatch(h)
    ticket = [n, h.row[2], h.row[4]]
    h.io(trace, lambda: h.service(FAULT))
    assert h.failure_ticket() == ticket and h.program_failed()
    assert h.row[28] == h.offload[13] == 0
    assert h.row[8] == h.row[10] == h.row[44] == 0
    assert h.offload[59:63] == [1]+ticket
    assert h.row[4] > ticket[2]
    h.step(6, result=WAIT)
    h.service(WAIT)
    return ticket


def scenario(h, name, document, images):
    h.facts([1]*7)
    h.grant_facts([1]*5)
    off._offload_reset(h)
    # Direct old fixture routes must not bypass the command backend.
    for op in (102, 106, 107):
        h.step(op, result=INVALID)
    name = name.removeprefix('program/')

    if name == 'raw-configuration-field-guards':
        # Canonical fresh cfg0 needs no invented close callback; direction is
        # ignored when wLength is zero. Both use genuine ordinary IN status.
        for direction in (0, 0x80):
            h.setup(base.packet(direction, 9))
            h.control_status('fresh-clean-raw-SC0')
        h.dispatch(h.capture(base.packet(0, 9, value=1)))
        h.io(INITIAL, lambda: h.service())
        h.control_status('ordinary-raw-SC1')
        h.step(10)
        h.finish_reset(ack=False)
        assert h.row[32] == 2
        h.dispatch(h.capture(base.packet(0, 9)))
        h.io(CLOSE, lambda: h.service())
        h.control_status('ordinary-raw-SC0-after-close')
        assert h.completed_mask() == 0 and h.row[44] == 0
        for value, index in ((0, 1), (0x100, 0)):
            _, owner = configure(h)
            raw = h.capture(base.packet(0, 9, value=value, index=index))
            h.dispatch(raw)
            ticket = [0, h.row[2], h.row[4]]
            h.service(WAIT)
            off._offload_settle_auto(h, owner, service=False)
            h.service(FAULT)
            assert h.program_failed() and h.failure_ticket() == ticket
            assert h.program[58:62] == ticket+[4], 'genuine void-close entry owns the failure'
            assert not h.offload[13] and h.row[26] == h.row[28] == 0
            reset_and_cleanup(h, ticket)
        # From cfg0 these aliases reach the genuine first-open callback, rather
        # than first failing the previous configuration's void-close callback.
        for value, index in ((1, 1), (0x101, 0)):
            raw = h.capture(base.packet(0, 9, value=value, index=index))
            h.dispatch(raw)
            ticket = [0, h.row[2], h.row[4]]
            h.service(FAULT)
            assert h.program_failed() and h.failure_ticket() == ticket
            assert h.program[58:62] == ticket+[2]
            assert h.offload[59:63] == [1]+ticket
            assert h.row[26] == h.row[28] == 0
            reset_and_cleanup(h, ticket)
        # Also cover the cfg0 aliases for which the core emits no close call.
        for value, index in ((0, 1), (0x100, 0)):
            raw = h.capture(base.packet(0, 9, value=value, index=index))
            h.dispatch(raw)
            ticket = [0, h.row[2], h.row[4]]
            h.service(FAULT)
            assert h.failure_ticket() == ticket and h.completed_mask() == 0
            assert h.program[58:62] == ticket+[7]
            assert h.row[26] == h.row[28] == 0
            reset_and_cleanup(h, ticket)
        assert h.row[32] == 2 and not h.row[50] and not h.row[90]
        return

    if name == 'fifo-mismatch-cleanup':
        ticket = failed_configuration(h, O['PROGRAM_FIFO_MISMATCH'])
        reset_and_cleanup(h, ticket)
        _, token = configure(h, recover=True, grant=True)
        h.fresh_page(document, images)
        return

    if name == 'read-then-partial-write-failure':
        first = failed_configuration(h, O['PROGRAM_FIRST_READ_FAILURE'])
        reset_and_cleanup(h, first)
        second = failed_configuration(h, O['PROGRAM_IN_MPS_UNCERTAIN'])
        assert first != second
        h.cleanup(first, result=STALE)
        reset_and_cleanup(h, second)
        configure(h, recover=True, grant=True)
        h.fresh_page(document, images)
        return

    n, token = configure(h)
    if name == 'sc1-grant-and-page':
        before = h.row[32:48].copy()
        for i in range(5):
            facts = [1]*5; facts[i] = 0
            h.grant_facts(facts)
            h.grant(n, token, result=WAIT)
            facts[i] = 2
            h.grant_facts(facts)
            h.grant(n, token, result=INVALID)
        h.grant_facts([1]*5)
        h.io(O['PROGRAM_GRANT_RDE_WAIT'], lambda: h.grant(n, token, result=WAIT))
        assert h.offload[33] == 0 and not h.program_failed()
        h.io(GRANT, lambda: h.grant(n, token))
        assert h.row[32:48] == before, 'permission is not a recovery promise'
        h.grant(n, token, result=STALE)
        off._offload_recovery(h, token)
        assert h.offload[16:21] == h.auto_owners[token]['cookie']
        assert h.offload[18] == 1 and h.row[32] == 2
        h.fresh_page(document, images)
        return

    if name.startswith('grant-'):
        traces = {'grant-pre-order-failure':'PROGRAM_GRANT_PRE_ORDER_FAILURE',
                  'grant-write-uncertain':'PROGRAM_GRANT_WRITE_UNCERTAIN',
                  'grant-post-order-failure':'PROGRAM_GRANT_POST_ORDER_FAILURE'}
        ticket = [n, h.row[3], h.row[4]]
        h.io(O[traces[name]], lambda: h.grant(n, token, result=FAULT))
        consumed = int(name != 'grant-pre-order-failure')
        assert h.failure_ticket() == ticket and h.program_failed()
        assert h.offload[33] == consumed and h.failure_consumed() == consumed
        h.grant(n, token, result=FAULT)
        h.step(6, result=WAIT)
        reset_and_cleanup(h, ticket, test_pending=True)
        return

    off._offload_recovery(h, token)
    if name == 'stale-held-grant':
        h.grant(n+1, token, result=STALE)
        for mutant in range(1, 6):
            h.grant(n, token, mutant=mutant, result=STALE)
        pending = h.capture(base.packet(0x80, 6, value=0x0100, length=18))
        h.dispatch(pending, facts=0x010001, result=WAIT)
        h.grant(n, token, result=WAIT)
        h.dispatch(pending, service=True, service_result=WAIT)
        h.grant(n, token, result=STALE)
        off._offload_settle_auto(h, token, service=False)
        h.service()
        h.requested = 18
        h.control_in(base.DEVICE, 'device-after-held-original-auto-owner')
        h.grant(n, token, result=STALE)
        assert h.row[32] == 2
        return

    h.io(GRANT, lambda: h.grant(n, token))
    if name == 'raw-sc0-after-reset':
        off._offload_reset(h)
        assert h.completed_mask() == 3 and not h.program_ready()
        raw = h.capture(base.packet(0, 9))
        h.dispatch(raw)
        ticket = [0, h.row[2], h.row[4]]
        h.service(FAULT)
        assert h.failure_ticket() == ticket and h.completed_mask() == 3
        assert h.program[58:62] == ticket+[7]
        assert h.row[26] == h.row[28] == 0 and not h.offload[13]
        h.step(125)
        assert h.program[48:51] == ticket and h.program[56] == OK
        reset_and_cleanup(h, ticket)
        h.setup(base.packet(0, 9))
        h.control_status('new-raw-SC0-after-explicit-cleanup')
        assert h.row[32] == 2 and h.completed_mask() == 0
        return
    if name == 'repeated-sc1-owned':
        data = document(['small'])
        h.send(data[:31], 31, zlp=False)
        bulk = h.arm_write(data[31:62])
        cookie = h.bulk[bulk]['cookie'].copy()
        repeat = off._offload_offer_dispatch(h)
        h.service(WAIT)
        off._offload_settle_auto(h, token, service=False)
        h.service(WAIT)
        h.step(64, bulk, 0, result=WAIT)
        assert h.udc[16:21] == cookie and h.row[50] == h.row[90] == 0
        h.step(64, bulk, 1)
        current = activate(h, repeat, CLOSE+RESELECT)
        off._offload_recovery(h, current)
        h.io(GRANT, lambda: h.grant(repeat, current))
        assert h.auto_owners[current]['cookie'][2] == 2 and h.row[32] == 3
        h.fresh_page(document, images)
        return

    if name in ('si-explicit-programming', 'si-write-failure'):
        halt = name == 'si-explicit-programming'
        if halt:
            h.setup(base.packet(2, 3, index=1), service_result=WAIT)
            off._offload_settle_auto(h, token, service=False)
            h.service()
            h.control_status('ordinary-OUT-HALT')
            h.request(base.packet(2, 3, index=0x81), label='ordinary-IN-HALT')
            assert h.row[81:85] == [1, 1, 1, 1]
        selected = off._offload_offer_dispatch(h, kind=2)
        if not halt:
            h.service(WAIT)
            off._offload_settle_auto(h, token, service=False)
        current = activate(h, selected, (), kind=2)
        assert not h.program_ready()
        h.step(6, result=WAIT)
        h.step(7, result=WAIT)
        h.step(10)
        h.step(12, result=WAIT)
        if not halt:
            ticket = [selected, h.row[3], h.row[4]]
            h.io(O['PROGRAM_SI_IN_MASK_NOT_PERFORMED'], lambda: h.complete_selection(result=FAULT))
            assert h.failure_ticket() == ticket and h.offload[33] == 0
            reset_and_cleanup(h, ticket, test_pending=True)
            return
        for i in (3, 4, 6):
            facts = [1]*7; facts[i] = 0
            h.facts(facts); h.complete_selection(result=WAIT)
            facts[i] = 2
            h.facts(facts); h.complete_selection(result=INVALID)
        h.facts([1]*7)
        h.io(SI, lambda: h.complete_selection())
        h.complete_selection(result=STALE)
        h.grant(selected, current, result=WAIT)
        assert h.row[81:85] == [1, 1, 1, 1]
        h.step(15)
        h.io(GRANT, lambda: h.grant(selected, current))
        off._offload_recovery(h, current)
        assert h.row[32] == 3
        h.fresh_page(document, images)
        return

    if name == 'void-close-failure':
        off_seq = off._offload_offer_dispatch(h, cfg=0)
        h.service(WAIT)
        off._offload_settle_auto(h, token, service=False)
        ticket = [off_seq, h.row[2], h.row[4]]
        h.io(O['PROGRAM_CLOSE_POINTER_UNCERTAIN'], lambda: h.service(FAULT))
        assert h.program_failed() and h.failure_ticket() == ticket
        assert h.offload[13] == 0 and h.row[28] == 0
        reset_and_cleanup(h, ticket)
        return

    if name == 'sc0-and-reset-history':
        off_seq = off._offload_offer_dispatch(h, cfg=0)
        h.service(WAIT)
        off._offload_settle_auto(h, token, service=False)
        zero = activate(h, off_seq, CLOSE, cfg=0)
        h.complete_selection()
        h.io(GRANT, lambda: h.grant(off_seq, zero))
        again = off._offload_offer_dispatch(h, cfg=0)
        h.service(WAIT)
        off._offload_settle_auto(h, zero, service=False)
        zero = activate(h, again, (), cfg=0)
        h.complete_selection()
        h.io(GRANT, lambda: h.grant(again, zero))
        on = off._offload_offer_dispatch(h)
        h.service(WAIT)
        off._offload_settle_auto(h, zero, service=False)
        current = activate(h, on, RESELECT)
        off._offload_recovery(h, current)
        off._offload_reset(h)
        assert h.completed_mask() == 3 and not h.program_ready()
        off_seq = off._offload_offer_dispatch(h, cfg=0)
        zero = activate(h, off_seq, (), cfg=0)
        h.grant(off_seq, zero, result=WAIT)
        h.io(CLOSE, lambda: h.complete_selection())
        h.io(GRANT, lambda: h.grant(off_seq, zero))
        assert h.completed_mask() == 0 and h.row[8] == h.row[10] == h.row[44] == 0
        return
    raise AssertionError('unknown program profile: '+name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', action='store_true')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix='hp1020-udc-program-', dir='/tmp'))
    print('Register program captures: '+str(temp), flush=True)
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
    for index,(name,fill,capacity,interface) in enumerate(matrix):
        assert capacity == 64 and interface == 0
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
        assert len(h.events) == len(h.rows) == len(h.ep0_rows) == len(h.out_rows) == len(h.setup_rows) == len(h.offload_rows) == len(h.program_rows)
        cases.append(dict(case=title, scenario=name, fill=fill, capacity=64, interface=interface,
            status='pass', initial=h.initial, initial_ep0=h.ep0_initial,
            initial_bulk=h.out_initial, initial_setup=h.setup_initial, initial_offload=h.offload_initial, initial_program=h.program_initial,
            steps=h.rows, ep0_steps=h.ep0_rows, bulk_steps=h.out_rows, setup_steps=h.setup_rows, offload_steps=h.offload_rows, program_steps=h.program_rows,
            events=h.events, packet_oracles=h.packets, descriptor_oracles=h.descriptor_oracles,
            bulk_descriptor_oracles=h.bulk_oracles, setup_oracles=h.ingress_oracles, offload_oracles=h.offload_oracles, program_oracles=h.program_oracles,
            expected_program_trace=h.expected_trace, supplied_reads=h.expected_reads,
            expected_documents=h.expected_documents, expected_pixels_sha256=core.sha(h.expected_pixels),
            pixels_bytes=len(h.expected_pixels), capture_sha256={n:core.sha(raw) for n,raw in captures.items()}))
        replay.append((h,captures,directory))
        print(f'Register program: {len(cases)}/{len(matrix)} host cases passed', flush=True)
    unchanged()
    target = None
    if args.target:
        core.command(['bash', ROOT/'scripts/build-hp1020-udc-program-target.sh'])
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
                                  ('hp1020_offload_fixture_stats',80), ('hp1020_program_fixture_stats',64)):
                result.append(list(struct.unpack('>'+str(length)+'I',q.read(program.symbols[symbol],length*4))))
            return result

        with QemuRAM() as q:
            version = q.version
            for case,(h,captures,directory) in zip(cases,replay):
                q.load(elf)
                assert q.call0(program.symbols['hp1020_bulk_fixture_reset'],[case['fill'],64,case['interface'],0xffffffff]) == 0
                initial,e,b,s,o,p = rows(q)
                assert initial[:59]+initial[60:] == h.initial[:59]+h.initial[60:]
                assert (e,b,s,o) == (h.ep0_initial,h.out_initial,h.setup_initial,h.offload_initial)
                assert p[:57]+p[58:] == h.program_initial[:57]+h.program_initial[58:]
                for index,(event,host_row,host_ep0,host_bulk,host_setup,host_offload,host_program) in enumerate(zip(
                        h.events,h.rows,h.ep0_rows,h.out_rows,h.setup_rows,h.offload_rows,h.program_rows)):
                    data = bytes.fromhex(event['data_hex'])
                    if data:
                        q.put(program.symbols['hp1020_bulk_fixture_input'],data)
                    result = q.call0(program.symbols['hp1020_bulk_fixture_step'],event['words'])
                    row,e,b,s,o,p = rows(q)
                    with (directory/'target-steps.jsonl').open('a') as output:
                        output.write(json.dumps(row+e+b+s+o+p)+'\n')
                    assert result == row[0] == event['result'] and row[15:17] == [0,1]
                    assert e[2:5] == [0,1,1] and b[7:10] == [0,1,1] and s[12:15] == [0,1,3] and o[11:13] == [0,1]
                    assert row[:59]+row[60:] == host_row[:59]+host_row[60:], (case['case'],index,row,host_row)
                    assert (e,b,s,o) == (host_ep0,host_bulk,host_setup,host_offload), (case['case'],index,e,b,s,o)
                    assert p[:57]+p[58:] == host_program[:57]+host_program[58:], (case['case'],index,p,host_program)
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
                observed['program_reads'] = q.read(program.symbols['hp1020_program_fixture_reads']+16, p[24]*12)
                observed['program_trace'] = q.read(program.symbols['hp1020_program_fixture_trace']+16, p[26]*24)
                observed['program_storage'] = (q.read(program.symbols['hp1020_program_fixture_reads'],3104) +
                    q.read(program.symbols['hp1020_program_fixture_trace'],24608))
                sizes = {'program':p[57]}
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
                    complete_recorded_io_and_explicit_read_script_equal=True,
                    adapter_state_and_memory_bytes=row[59],component_and_allocation_bytes=sizes,
                    capture_sha256={n:core.sha(raw) for n,raw in observed.items()}))
                print(f'Register program: {len(native)}/{len(cases)} target cases passed',flush=True)
        assert all(core.sha((saved/n).read_bytes()) == digest for n,digest in artifacts.items()), 'captured target changed'
        target = dict(status='pass',cases=native,qemu_version=version,elf_sha256=core.sha(elf.read_bytes()),
                      audit=audit,captured_artifact_sha256=artifacts)
    unchanged()
    assert len(cases) == len(matrix) == len(replay)
    if target:
        assert len(target['cases']) == len(cases)
    report = dict(status='pass',source_sha256=tested,fixture_sha256=fixture_hashes,effective_source=effective,
        original_reference=evidence,offload_mode_evidence={n:tested[n] for n in MODE_EVIDENCE},
        hp_dynamic_csr_capability_established=False,automatic_grants_are_acknowledgments=False,
        cases=cases,target=target,completed_native_page_lifecycles=0,
        usb_transfers=0,actual_peripheral_accesses=0,controller_quiescence_established=False,
        scope='Freestanding endpoint-programming and immediate status-command construction through injected recording I/O, actual TinyUSB callbacks, existing original owners and independently supplied register observations. Exact traces, failures, pixels, documents, packets and retained storage are compared in synthetic RAM.',
        limits='No physical register backend, IRQ, cache, boot, USB traffic or printing. Dynamic mode, coherent complete table, fixed FIFO geometry, safe IN SNAK, stable DEVCTL, defaults, original event order, visibility, physical gate and settlement remain supplied. Writes do not emulate hardware effects. CSR_DONE issuance is not wire completion/ACK or a document-recovery promise. Close is bounded NAK/mask/old-pointer-clear intent, not proof of logical endpoint disable. First profile is full-speed64, config0/1, interface0/alt0; copies remain metadata and output synchronous.')
    name = 'validation' if args.target else 'host-validation'
    raw = json.dumps(report,sort_keys=True,separators=(',',':'))+'\n'
    (temp/(name+'.json')).write_text(raw)
    (OUT/(name+'.json')).write_text(raw)
    (OUT/(name+'.md')).write_text('# Recorded controller-programming execution\n\n'+report['scope']+'\n\n'+
        f'{len(cases)} host; {len(target["cases"]) if target else 0} QEMU cases. Every explicit read, attempted register command and ordering hook, original cleanup/grant identity, packet, pixel, document event and guarded allocation is compared.\n\n'+report['limits']+'\n')


if __name__ == '__main__':
    main()
