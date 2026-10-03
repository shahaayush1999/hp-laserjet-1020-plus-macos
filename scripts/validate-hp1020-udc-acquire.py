#!/usr/bin/env python3
"""Offline original-owner OUT acquisition through recording visibility hooks."""
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
spec = importlib.util.spec_from_file_location('acquire_publish', ROOT/'scripts/validate-hp1020-udc-publish.py')
pub = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = pub
spec.loader.exec_module(pub)
pg, off, comp, ep0, base, core = pub.pg, pub.off, pub.comp, pub.ep0, pub.base, pub.core
bulk_reference, MODE_EVIDENCE = pub.bulk_reference, pub.MODE_EVIDENCE
SRC = ROOT/'open-firmware/udc-acquire-test'
OUT = ROOT/'analysis/usb-path/udc-acquire'
PROGRAM, PUBLISH = pub.PROGRAM, pub.PUBLISH
OK, WAIT, STALE, INVALID, FAULT, ADAPTER_ERROR = range(6)
ORACLES = SRC/'trace-oracles.py'
O = runpy.run_path(str(ORACLES))


def profiles():
    return O['profiles']()


def sources(temp):
    tested = pub.sources(temp)
    selected = set(SRC.glob('*.[ch]')) | set(SRC.glob('*.ld'))
    selected.add(ORACLES)
    selected.add(ROOT/'open-firmware/udc-out/hp1020_udc_acquire.h')
    selected.update(ROOT/'scripts'/name for name in (
        'validate-hp1020-udc-acquire.py', 'build-hp1020-udc-acquire-target.sh',
        'check-hp1020-udc-acquire.py'))
    for path in sorted(selected):
        if not path.is_file():
            continue
        name = str(path.relative_to(ROOT)); tested[name] = core.sha(path.read_bytes())
        destination = temp/'source'/name; destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
    (temp/'source-sha256.json').write_text(json.dumps(tested, indent=2)+'\n')
    return tested


def compile_host(temp, effective):
    ep0_src, out, setup = [ROOT/'open-firmware'/name for name in ('udc-ep0','udc-out','udc-setup')]
    implementation = [SRC/'fixture.c', SRC/'host-check.c', ep0_src/'hp1020_udc_ep0.c',
        out/'hp1020_udc_out.c', setup/'hp1020_udc_setup.c', PROGRAM/'hp1020_udc_program.c', PUBLISH/'hp1020_udc_publish.c',
        base.ADAPTER/'hp1020_tusb_adapter.c', base.PRINTER/'hp1020_usb_printer.c',
        base.RX/'hp1020_usb_receive.c', base.RX/'hp1020_usb_document.c']
    implementation += [base.IMG/name for name in ('hp1020_image.c','hp1020_image_page.c',
        'hp1020_image_stream.c','hp1020_image_ring.c','hp1020_image_output.c')]
    implementation += [base.SEM/'hp1020_semantic.c',base.SEM/'hp1020_page_plan.c',
        core.VENDOR/'libjbig/jbig85.c',core.VENDOR/'libjbig/jbig_ar.c']
    implementation += [effective/'src'/name for name in ('tusb.c','device/usbd.c','common/tusb_fifo.c')]
    flags = ['clang','-std=c11','-O1','-g','-fno-common','-Wall','-Wextra','-Werror',
        '-fsanitize=address,undefined']
    include = ['-I'+str(p) for p in (SRC,PUBLISH,PROGRAM,ep0_src,out,setup,ROOT/'open-firmware',
        base.SRC,base.ADAPTER,base.PROTOCOL,base.PRINTER,base.RX,base.IMG,base.SEM,
        core.VENDOR/'libjbig',effective/'src')]
    core.command(flags+include+implementation+['-o',temp/'host'])
    full = ROOT/'vendor/foo2zjs-source'
    core.command(flags+['-I'+str(full),base.IMG/'reference.c',full/'jbig.c',full/'jbig_ar.c',
        '-o',temp/'reference'])


def validate_event(words, data):
    pub.validate_event(words, data)
    op,a,b,c,d = words
    if op == 140: assert len(data) == 80
    if op == 141: assert len(data) == 3
    if op in (142,143): assert len(data) == 0


class Host(pub.Host):
    def __init__(self, executable, directory, fill, capacity, interface):
        self.acquire_rows = []
        self.device_images = {}
        self.expected_receive = bytearray([fill])*4096
        self.expected_descriptor = bytes([fill])*16
        self.expected_device_storage = bytes([fill])*144
        super().__init__(executable,directory,fill,capacity,interface)
        self.acquire_initial = self.acquire.copy()
        assert self.acquire[1:3] == [1,0] and self.acquire[7:9] == [0,1]
        assert self.acquire[11] == 0x010101

    def read_row(self):
        if not select.select([self.process.stdout],[],[],30)[0]:
            self.process.kill(); self.process.wait()
            raise AssertionError('acquisition fixture timed out: '+str(self.directory))
        raw = self.process.stdout.readline()
        with (self.directory/'raw-stdout').open('ab') as saved: saved.write(raw)
        assert raw, ('fixture ended early',self.directory)
        row = json.loads(raw)
        assert len(row) == 576
        self.ep0,self.udc,self.ingress = row[96:200],row[200:248],row[248:288]
        self.offload,self.program,self.publish,self.acquire = row[288:368],row[368:432],row[432:496],row[496:576]
        return row[:96]

    def step(self,op,a=0,b=0,c=0,d=0,data=b'',result=OK,expect=None):
        validate_event([op,a,b,c,d],data)
        before_issued = self.row[33] if hasattr(self,'row') else 0
        before_preparations = self.udc[10]
        row = super().step(op,a,b,c,d,data,result,expect)
        self.acquire_rows.append(self.acquire.copy())
        assert self.acquire[7:9] == [0,1] and self.acquire[73:77] == [0]*4 and self.acquire[79] == 0
        assert self.acquire[63] == 1
        with (self.directory/'host-acquire-steps.jsonl').open('a') as saved:
            saved.write(json.dumps(self.acquire)+'\n')
        if op == 6 and self.udc[10] == before_preparations+1:
            slot = before_issued % 4
            self.expected_descriptor = O['words']((0x08000000,0,O['slot_dma'](slot),0))
        return row

    def io(self,expected,invoke,*,supplied=None):
        expected = tuple(expected)
        trace_start,read_start = len(self.expected_trace),len(self.expected_reads)
        reads = list(supplied if supplied is not None else pub.O['supplied_reads'](expected))
        assert len(reads) <= 85
        if reads:
            self.expected_reads.extend(tuple(r) for r in reads)
            self.step(120,len(reads),data=b''.join(struct.pack('>3I',*r) for r in reads))
        failures = [(i,r) for i,r in enumerate(expected) if r[0] != 1 and r[3]]
        assert len(failures) <= 1
        if failures:
            index,row = failures[0]
            op = 143 if row[0] in (6,7,8) else 131 if row[0] in (4,5) else 121
            self.step(op,row[0],trace_start+index+1,row[3])
        event_index = len(self.events)+1
        self.expected_trace.extend((event_index,trace_start+i+1,kind,offset,
            value if kind != 1 or outcome == 0 else 0,outcome)
            for i,(kind,offset,value,outcome) in enumerate(expected))
        value = invoke()
        assert len(self.events) == event_index
        assert self.program[25] == len(self.expected_reads) and self.program[35] == 0
        self.program_oracles.append(dict(event=event_index,trace_begin=trace_start,
            trace_end=len(self.expected_trace),read_begin=read_start,read_end=len(self.expected_reads),
            literal_trace=[list(r) for r in expected]))
        return value

    def acquire_facts(self,raw):
        assert len(raw) == 3
        self.step(141,data=bytes(raw))
        assert self.acquire[11] == int.from_bytes(bytes(raw),'big')

    def device_image(self,token,payload,*,done=True,false_done=False,result=OK):
        assert token in self.bulk and len(payload) <= 64
        original = self.bulk[token]
        slot = original['slot']
        descriptor,data = O['device_images'](slot,bytes(payload),done=done)
        before = self.row.copy(),self.udc.copy(),self.acquire.copy()
        self.step(140,token,int(false_done),data=descriptor+data,result=result)
        if result == OK:
            self.device_images[token] = dict(cookie=original['cookie'].copy(),slot=slot,
                descriptor=descriptor,payload=data,false_done=false_done,input=bytes(payload),done=done)
            poison_d,poison_p = O['cpu_poison'](slot,false_done=false_done)
            self.expected_descriptor = poison_d
            self.expected_receive[slot*1024:slot*1024+64] = poison_p
            guard = bytes([self.fill])*16
            self.expected_device_storage = guard+descriptor+guard+guard+data+guard
            assert self.acquire[9:11] == [before[2][9]+1,before[2][10]+1]
            assert self.acquire[12:14] == [slot,int(false_done)]
            assert self.acquire[19:25] == [1]+original['cookie']
            assert struct.pack('>4I',*self.acquire[69:73]) == descriptor
        else:
            assert self.row[2:96] == before[0][2:96]
            assert self.udc[2:46] == before[1][2:46]
            assert self.acquire[9:61] == before[2][9:61]
            assert self.acquire[69:79] == before[2][69:79]

    def arm_write(self,data):
        token = self.arm()
        self.device_image(token,bytes(data))
        return token

    @staticmethod
    def diagnostic(values):
        assert len(values) == 17
        return dict(cookie=values[:5],prefix=values[5],dma=values[6],bytes=values[7],
            io_result=values[8],reason=values[9],result=values[10],operation=values[11],
            snapshot_valid=values[12],snapshot_hex=struct.pack('>4I',*values[13:17]).hex())

    def acquire_packet(self,token,*,mutant=0,fault=0,result=OK,fail_kind=None,outcome=1):
        before = self.row.copy(),self.udc.copy(),self.acquire.copy()
        original = self.bulk[token]
        slot = original['slot']
        exact = not mutant and before[1][16:21] == original['cookie'] and ((before[1][44]>>16)&255) == 1
        work = exact and before[1][2] == 2 and not before[1][5] and not fault and before[2][11] == 0x010101
        assert fail_kind is None or work
        trace = O['acquire_trace'](slot,fail_kind=fail_kind,outcome=outcome) if work else ()
        self.io(trace,lambda:self.step(142,token,mutant,fault,result=result))
        if work:
            image = self.device_images[token]
            descriptor,payload = O['expected_visibility'](slot,image['descriptor'],image['payload'],
                false_done=image['false_done'],fail_kind=fail_kind,outcome=outcome)
            self.expected_descriptor = descriptor
            self.expected_receive[slot*1024:slot*1024+64] = payload
            assert self.acquire[14:19] == original['cookie']
            actual = self.diagnostic(self.acquire[25:42])
            wanted = O['failure_fields'](original['cookie'],slot,fail_kind,outcome) if fail_kind is not None else O['captured_fields'](original['cookie'],image['descriptor'],result)
            assert all(actual[key] == value for key,value in wanted.items()),(actual,wanted)
            if fail_kind is not None:
                retained = self.diagnostic(self.acquire[42:59])
                assert self.acquire[2] == 1
                assert all(retained[key] == value for key,value in wanted.items())
                assert self.udc[2] == 2 and self.row[30] == token
                assert self.row[33:36] == before[0][33:36]
            if result == OK:
                assert self.udc[2] == 0 and self.row[30] == 0 and ((self.udc[44]>>16)&255) == 2
                assert self.row[32:48] == before[0][32:48]
                assert self.row[69:73] == before[0][69:73]
                assert self.row[17:18]+self.row[24:26]+self.row[50:59]+self.row[90:96] == before[0][17:18]+before[0][24:26]+before[0][50:59]+before[0][90:96]
        else:
            assert self.acquire[3:7] == before[2][3:7]
            if result in (WAIT,INVALID,STALE):
                assert self.acquire[25:59] == before[2][25:59]
                # The fixture counts stale inputs independently; a rejected
                # API call cannot change retained ownership or reset state.
                assert all(self.row[i] == before[0][i] for i in range(1,96) if i != 20)
                assert all(self.udc[i] == before[1][i] for i in range(1,48) if i != 14)
                assert self.row[20] == before[0][20] + int(result == STALE)
                assert self.udc[14] == before[1][14] + int(result == STALE)
                assert self.acquire[9:25] == before[2][9:25]
                assert self.acquire[69:79] == before[2][69:79]
        if fail_kind is None:
            assert self.acquire[42:59] == before[2][42:59], 'later calls cannot erase first failure evidence'
        return self.row

    def complete(self,token,length,usb_result=0,result=OK,service=True):
        if token not in self.bulk:
            return super().complete(token,length,usb_result,result,service)
        assert usb_result == 0
        if result != STALE:
            assert len(self.device_images[token]['input']) == length
        self.acquire_packet(token,result=result)
        if service: self.service()

    def finish(self):
        captures = super().finish()
        raw = (self.directory/'output.acquire-device').read_bytes()
        assert len(raw) == 144 and raw == self.expected_device_storage
        assert captures['receive'] == self.expected_receive
        assert captures['bulk_descriptor'][16:32] == self.expected_descriptor
        captures['acquire_device'] = raw
        return captures


"""UNEXECUTED acquisition scenario fragment:16 independent profiles x two fills.

Concatenate after the lead-owned header/Host and before its main. Globals O,
pub, pg, off, base, core, struct and the result constants come from that header. O is
the independently frozen acquisition oracle; pub.O remains the independently
frozen publication oracle. No production C is imported or decoded here.
"""


def _acq_record(h, records, kind, label, **expected):
    records.append(dict(kind=kind, label=label, event=len(h.events), **expected))


def _acq_no_effect(h, records, label, invoke):
    """A rejection may count the attempted stale event; it may not change work."""
    before = h.row.copy(), h.udc.copy(), h.acquire.copy()
    traces = len(h.expected_trace)
    result = invoke()
    # Base20 is the historical stale-event diagnostic, not an owner/queue field.
    assert [h.row[i] for i in range(1, 96) if i != 20] == [
        before[0][i] for i in range(1, 96) if i != 20], label
    assert h.udc[2:14] == before[1][2:14], label
    assert h.udc[16:40] == before[1][16:40] and h.udc[44:46] == before[1][44:46], label
    assert h.acquire[3:7] == before[2][3:7], label
    assert h.acquire[9:25] == before[2][9:25], label
    assert h.acquire[25:59] == before[2][25:59], label
    assert h.acquire[69:73] == before[2][69:73] and h.acquire[77:79] == before[2][77:79]
    assert len(h.expected_trace) == traces, label
    _acq_record(h, records, 'no-effect-refusal', label, result=h.row[0],
        owner_states=before[1][44], generation=before[0][32],
        issued=before[0][33], consumed=before[0][34], count=before[0][35])
    return result


def _acq_accept(h, records, token, label, *, service=True, pump=False):
    """Observe the DCD->PENDING boundary before any TinyUSB service/consumption."""
    before = h.row.copy()
    original = h.bulk[token]['cookie'].copy()
    image = h.device_images[token]
    assert image['cookie'] == original and image['done']
    assert image['descriptor'] == O['literal_descriptor'](image['slot'], len(image['input']))
    assert ((h.udc[44] >> 16) & 255) == 1
    h.acquire_packet(token)
    actual = h.diagnostic(h.acquire[25:42])
    wanted = O['captured_fields'](original, image['descriptor'], OK)
    assert all(actual[k] == value for k, value in wanted.items()) and actual['reason'] == 0
    assert h.row[18] == before[18]+1 and h.row[19] == before[19]
    assert h.row[30] == 0 and h.udc[2] == 0 and ((h.udc[44] >> 16) & 255) == 2
    assert h.row[32:48] == before[32:48] and h.row[69:73] == before[69:73]
    assert h.row[17:18]+h.row[24:26]+h.row[50:59]+h.row[90:96] == (
        before[17:18]+before[24:26]+before[50:59]+before[90:96])
    _acq_record(h, records, 'acquired-before-service', label, original_cookie=original,
        descriptor_hex=image['descriptor'].hex(), payload_hex=image['payload'].hex(),
        input_hex=image['input'].hex(), expected_diagnostic=wanted,
        owner_states=h.udc[44], generation=before[32], count=before[35])
    if service:
        h.service()
    if pump:
        h.step(7)


def _acq_fault_only(h, records, token, reason, *, supplied=0, label='retained fault'):
    before = h.row.copy(), h.udc.copy(), h.acquire.copy()
    trace_count = len(h.expected_trace)
    original = h.bulk[token]['cookie'].copy()
    h.acquire_packet(token, fault=supplied, result=FAULT)
    wanted = original + [0, 0, 0, 0, reason, FAULT, 0, 0] + [0]*4
    assert h.acquire[25:42] == wanted
    assert h.acquire[42:59] == before[2][42:59]
    assert h.acquire[3:7] == before[2][3:7] and len(h.expected_trace) == trace_count
    assert h.udc[2:6] == [2, 1, 1, reason]
    assert h.row[30] == token and ((h.udc[44] >> 16) & 255) == 1
    assert h.row[33:36] == before[0][33:36] and h.row[18] == before[0][18]
    assert h.row[7] == h.row[9] == h.row[36] == 1
    assert h.row[24:26] == before[0][24:26] and h.row[50:59] == before[0][50:59]
    assert h.row[90:96] == before[0][90:96]
    _acq_record(h, records, 'fault-without-acquisition', label,
        original_cookie=original, supplied_reason=supplied, retained_reason=reason,
        expected_diagnostic=wanted)


def _acq_fault_barrier(h, records, token, reason):
    """The adapter is fenced; this is not a fabricated publisher failure."""
    before = h.row.copy()
    failure = h.acquire[42:59].copy()
    trace_count = len(h.expected_trace)
    h.arm((), result=WAIT)
    assert h.row[2:96] == before[2:96]
    h.service()  # Harmless poll is allowed: no new dispatch or cache retry.
    assert h.row[2:96] == before[2:96]
    h.step(7, result=base.STOPPED)
    assert h.row[32:48] == before[32:48]
    assert h.row[50:59] == before[50:59] and h.row[90:96] == before[90:96]
    assert h.row[30] == token and h.udc[3:6] == [1, 1, reason]
    assert h.acquire[42:59] == failure and len(h.expected_trace) == trace_count
    assert h.publish[6] == 0, 'an acquisition fault is not a publication-I/O failure'
    _acq_record(h, records, 'fenced-no-retry', 'arm WAIT, service OK, pump STOPPED',
        original_cookie=h.bulk[token]['cookie'].copy(), reason=reason,
        first_failure=failure, count=before[35])


def _acq_reset_recover(h, records, token, auto_owner, *, already_reset=False,
                       already_settled=False, publication_failure=None):
    """Real reset + original settlement, then separate program/document recovery."""
    original = h.bulk[token]['cookie'].copy()
    generation, count = h.row[32], h.row[35]
    failure = h.acquire[42:59].copy()
    wire = off._offload_wire_state(h)
    assert count > 0 and generation == 2
    if not already_reset:
        h.step(5)
    assert h.ingress[11] == 1 and h.row[2] != h.row[3]
    assert h.row[32] == generation and h.row[35] == count
    if publication_failure is not None:
        assert h.publish[6] == 1 and h.publish[22:36] == publication_failure
        h.publication_cleanup(token, result=WAIT)
    h.service(WAIT)  # At least the original automatic-status owner is retained.
    if not already_settled:
        h.step(64, token, 0, result=WAIT)
        assert h.row[30] == token and h.udc[16:21] == original
        h.step(64, token, 1)
        assert h.row[30] == 0 and h.udc[2] == 0
        assert ((h.udc[44] >> 16) & 255) == 2
    if publication_failure is not None:
        h.publication_cleanup(token, result=WAIT)
    assert h.row[28] == auto_owner
    off._offload_settle_auto(h, auto_owner, service=False)
    if publication_failure is not None:
        h.publication_cleanup(token, result=WAIT)  # PENDING owner is not free.
    h.service()
    assert h.row[8] == h.row[10] == h.row[13] == h.row[77] == h.row[85] == 0
    assert h.udc[44] == 0 and h.row[7] == h.row[36] == 1
    assert h.row[32] == generation and h.row[35] == count
    assert h.row[44:46] == [0, 0] and h.row[50] == h.row[90] == 0
    assert h.acquire[42:59] == failure
    if publication_failure is not None:
        h.publication_cleanup(token, fact=0, result=WAIT)
        h.publication_cleanup(token)
        assert h.publish[56:58] == [count, count]
        assert h.publish[22:36] == publication_failure
        assert h.row[32] == generation and h.row[35] == count and h.row[44:46] == [0, 0]
    _acq_record(h, records, 'settled-before-restart', 'retained receive accounting',
        original_cookie=original, generation=generation, count=count,
        first_failure=failure, publication_failure=publication_failure,
        no_reset_promises=True)
    _acq_no_effect(h, records, 'old packet after reset drainage',
        lambda: h.acquire_packet(token, result=STALE))
    off._offload_no_wire(h, wire)
    h.acquire_facts(O['DEFAULT_FACTS'])
    sequence, owner = pg.configure(h, recover=True, grant=True)
    assert h.row[32] == 3 and h.acquire[42:59] == failure
    return sequence, owner


def _acq_finish_page(h, records, name, small, images, offset=0):
    generation = O['expected_generation'](name)
    assert h.row[32] == generation
    expected = O['EXPECTED_BLACK_PIXELS']
    assert expected == bytes.fromhex('ff'*32) and images['small'][1] == expected
    h.send(small[offset:], 64)
    h.expected_pixels = expected
    h.notification(generation, 1, 0, 1)
    h.repeat_pump()
    assert h.row[50] == 32 and h.row[56:59] == [1, 1, 1]
    assert h.row[90:93] == [1, 1, 1]
    assert h.row[35] == h.row[36] == h.row[40] == h.row[44] == 0
    assert h.publish[6] == h.program[4] == 0
    ordinary = int(name == 'acquire/held-setup-settlement')
    wire = b'\x01' if ordinary else b''
    assert h.row[24:26] == [len(wire), core.fnv(wire)]
    assert h.slot(0)[31] == h.slot(1)[31] == h.offload[57] == ordinary
    assert [packet['expected_hex'] for packet in h.packets] == (['01'] if ordinary else [])
    assert b''.join(struct.pack('>5I', *row) for row in h.expected_documents) == O['document_event'](generation)
    assert h.acquire[60] == h.publish[54] and h.acquire[60] > 0
    assert h.acquire[61] == sum(h.acquire[3:6]) and h.acquire[61] > 0
    assert h.acquire[62:64] == [WAIT, 1]
    _acq_record(h, records, 'complete-document', name, generation=generation,
        pixels_hex=expected.hex(), document=[generation, 1, 0, 1, 0],
        ordinary_wire_hex=wire.hex(), callback_probes=h.acquire[60], hook_probes=h.acquire[61])


def scenario(h, name, document, images):
    assert name in {profile[0] for profile in O['profiles']()}
    records = []
    short = name.removeprefix('acquire/')
    small = document(['small'])
    assert len(small) > 71 and images['small'][0] == O['SMALL_BIE']
    assert core.sha(images['small'][0]) == O['SMALL_BIE_SHA256']
    assert images['small'][1] == O['EXPECTED_BLACK_PIXELS']
    h.facts([1]*7)
    h.grant_facts([1]*5)
    h.publish_facts(pub.O['FACTS_ALL'])
    h.acquire_facts(O['DEFAULT_FACTS'])
    off._offload_reset(h)
    sequence, owner = pg.configure(h, recover=True, grant=True)
    assert h.row[32] == 2 and h.publish[6] == h.acquire[2] == 0

    if short == 'visibility-packets':
        for label, fragment in (('zero is not EOF', b''), ('short7', small[:7]),
                                ('full64', small[7:71])):
            token = h.arm_write(fragment)
            _acq_accept(h, records, token, label)
            assert h.row[36] == h.row[40] == 0
        h.step(7)
        _acq_finish_page(h, records, name, small, images, 71)
        assert {row[3] for row in h.expected_trace if row[2] == 7} == set(O['RECEIVE_DMAS'])

    elif short == 'facts-and-identities':
        token = h.arm_write(small[:31])
        for label, facts, expected in O['fact_probes']():
            h.acquire_facts(facts)
            _acq_no_effect(h, records, label,
                lambda expected=expected: h.acquire_packet(token, result=expected))
        h.acquire_facts(O['DEFAULT_FACTS'])
        for mutant in range(1, 6):
            _acq_no_effect(h, records, 'cookie-field-'+str(mutant),
                lambda mutant=mutant: h.acquire_packet(token, mutant=mutant, result=STALE))
        # All old snapshot/direct-write paths stay disabled in this variant.
        for op, args, raw in ((62, (token, 0x010101), bytes(16)),
                              (65, (token, 0, 0, 16), bytes(16)),
                              (66, (token, 0), b''), (67, (0, 0x010101), b'')):
            _acq_no_effect(h, records, 'disabled-'+str(op),
                lambda op=op, args=args, raw=raw: h.step(op, *args, data=raw, result=INVALID))
        _acq_accept(h, records, token, 'pending packet', service=False)
        _acq_no_effect(h, records, 'PENDING image cannot poison bytes',
            lambda: h.device_image(token, small[:31], result=STALE))
        _acq_no_effect(h, records, 'PENDING duplicate acquisition',
            lambda: h.acquire_packet(token, result=STALE))
        h.service()
        _acq_no_effect(h, records, 'FREE image cannot poison bytes',
            lambda: h.device_image(token, small[:31], result=STALE))
        _acq_no_effect(h, records, 'FREE duplicate acquisition',
            lambda: h.acquire_packet(token, result=STALE))
        h.step(7)
        _acq_finish_page(h, records, name, small, images, 31)

    elif short == 'callback-authority':
        callback_probes, hook_probes = h.acquire[60], h.acquire[61]
        token = h.arm_write(small[:31])
        assert h.acquire[60] == callback_probes+1 and h.acquire[61] == hook_probes
        assert h.acquire[62:64] == [WAIT, 1]
        _acq_accept(h, records, token, 'natural callback and three hook probes', pump=True)
        assert h.acquire[61] == hook_probes+3 and h.acquire[62:64] == [WAIT, 1]
        _acq_record(h, records, 'natural-reentry-refusals', short,
            callback_delta=1, hook_delta=3, result=WAIT, unchanged=True)
        _acq_finish_page(h, records, name, small, images, 31)

    elif short == 'held-setup-settlement':
        token = h.arm_write(small[:31])
        held = h.capture(O['GET_CONFIGURATION'])
        h.dispatch(held, facts=0, result=WAIT)
        assert h.ingress[2:5] == [1, held, held] and h.ingress[11] == 0
        h.arm((), result=WAIT)
        _acq_accept(h, records, token, 'settlement while raw capture held', service=False)
        forward = h.forward_state()
        h.service(WAIT)
        h.step(7, result=WAIT)
        assert h.forward_state() == forward and ((h.udc[44] >> 16) & 255) == 2
        h.dispatch(held)
        h.service(WAIT)
        assert h.row[28] == owner and h.offload[14] == 1
        off._offload_settle_auto(h, owner, service=False)
        h.service()
        h.control_in(b'\x01', 'GET_CONFIGURATION after held acquire')
        h.step(7)
        _acq_record(h, records, 'ordinary-control-after-held-capture', short,
            original_sequence=held, request_hex=O['GET_CONFIGURATION'].hex(),
            in_hex='01', status_endpoint=0, status_length=0)
        _acq_finish_page(h, records, name, small, images, 31)

    elif short == 'admitted-reset-settlement':
        token = h.arm_write(small[:31])
        original = h.bulk[token]['cookie'].copy()
        h.step(5)
        assert h.ingress[11] == 1 and h.row[2] != h.row[3]
        assert h.row[4] != original[1] and h.udc[3] == 1
        h.arm((), result=WAIT)
        _acq_accept(h, records, token, 'old packet after actual reset admission', service=False)
        sequence, owner = _acq_reset_recover(h, records, token, owner,
            already_reset=True, already_settled=True)
        _acq_finish_page(h, records, name, small, images)

    elif short == 'same-address-reuse':
        token = h.arm_write(small[:31])
        original = h.bulk[token]['cookie'].copy()
        old_dma = h.bulk[token]['dma']
        _acq_accept(h, records, token, 'old incomplete input', pump=True)
        assert h.row[50] == h.row[90] == 0
        off._offload_reset(h)
        sequence, owner = pg.configure(h, recover=True, grant=True)
        new = h.arm_write(small[:31])
        current = h.bulk[new]['cookie'].copy()
        assert current[2] == 3 and original[2] == 2 and current != original
        assert h.bulk[token]['slot'] == h.bulk[new]['slot'] == 0
        assert h.bulk[new]['dma'] == old_dma and h.udc[21] == O['DESCRIPTOR_DMA']
        _acq_no_effect(h, records, 'reused address rejects old image',
            lambda: h.device_image(token, small[:31], result=STALE))
        _acq_no_effect(h, records, 'reused address rejects old acquire',
            lambda: h.acquire_packet(token, result=STALE))
        _acq_no_effect(h, records, 'reused address rejects old cancel request',
            lambda: h.step(63, token, result=STALE))
        _acq_no_effect(h, records, 'reused address rejects old cancel settlement',
            lambda: h.step(64, token, 1, result=STALE))
        _acq_record(h, records, 'same-address-new-owner', short, old_cookie=original,
            new_cookie=current, descriptor_dma=O['DESCRIPTOR_DMA'], buffer_dma=old_dma)
        _acq_accept(h, records, new, 'new original owner', pump=True)
        _acq_finish_page(h, records, name, small, images, 31)

    elif short in ('prepared-publication-failure', 'exposed-publication-failure'):
        prepared = short == 'prepared-publication-failure'
        vector = pub.O['post_bind_failure'](
            'rx-cache-failure' if prepared else 'desptr-write-uncertain', h.row[33] % 4)
        token, original, wanted = pub._publication_failure(h, records, short, vector)
        assert h.acquire[2] == 0
        if prepared:
            _acq_no_effect(h, records, 'PREPARED image refuses before mutation',
                lambda: h.device_image(token, small[:31], result=INVALID))
            _acq_no_effect(h, records, 'PREPARED acquisition refuses before hooks',
                lambda: h.acquire_packet(token, result=INVALID))
            pub._publication_reset_cleanup(h, records, token, owner, wanted)
            sequence, owner = pg.configure(h, recover=True, grant=True)
        else:
            h.device_image(token, small[:31])
            _acq_accept(h, records, token, 'settled EXPOSED publication failure', service=False)
            assert h.publish[6] == 1 and h.publish[22:36] == wanted
            pub._publication_failed_barrier(h, records, token, sequence, owner)
            sequence, owner = _acq_reset_recover(h, records, token, owner,
                already_settled=True, publication_failure=wanted)
        assert h.row[32] == 3 and h.acquire[2] == 0 and h.publish[22:36] == wanted
        _acq_finish_page(h, records, name, small, images)
        assert h.acquire[2] == 0 and h.publish[22:36] == wanted

    elif short == 'endpoint-fault-only':
        token = h.arm_write(small[:31])
        h.acquire_facts(bytes(3))
        _acq_fault_only(h, records, token, 0x5a17, supplied=0x5a17, label='fault without settlement')
        _acq_fault_only(h, records, token, 0x5a17, supplied=0x6b28, label='first reason survives')
        _acq_fault_only(h, records, token, 0x5a17, label='clean retry cannot erase fault')
        assert h.acquire[2] == 0, 'endpoint fault is not an acquisition-I/O failure'
        _acq_fault_barrier(h, records, token, 0x5a17)
        sequence, owner = _acq_reset_recover(h, records, token, owner)
        _acq_finish_page(h, records, name, small, images)
        assert h.acquire[2] == 0

    elif short == 'not-done-fresh-retry':
        token = h.arm()
        h.device_image(token, small[:31], done=False, false_done=True)
        before = h.row.copy()
        hooks = h.acquire[3:6].copy()
        h.acquire_packet(token, result=WAIT)
        image = h.device_images[token]
        actual = h.diagnostic(h.acquire[25:42])
        wanted = O['captured_fields'](h.bulk[token]['cookie'], image['descriptor'], WAIT)
        assert all(actual[k] == value for k, value in wanted.items())
        assert actual['reason'] == 0 and h.acquire[2] == 0
        assert h.udc[2] == 2 and h.row[30] == token and ((h.udc[44] >> 16) & 255) == 1
        assert h.row[18] == before[18] and h.row[32:48] == before[32:48]
        assert h.row[69:73] == before[69:73]
        assert h.acquire[3:6] == [value+1 for value in hooks]
        _acq_record(h, records, 'not-done-authority', 'CPU false DONE is not evidence',
            original_cookie=h.bulk[token]['cookie'].copy(),
            device_descriptor_hex=image['descriptor'].hex(), expected_diagnostic=wanted)
        h.device_image(token, small[:31], done=True, false_done=False)
        _acq_accept(h, records, token, 'whole fresh acquisition after WAIT', pump=True)
        assert h.acquire[3:6] == [value+2 for value in hooks]
        _acq_finish_page(h, records, name, small, images, 31)

    else:
        selected = [entry for entry in O['HOOK_FAILURE_PROFILES'] if entry[0] == short]
        assert len(selected) == 1
        _, kind, outcome = selected[0]
        token = h.arm_write(small[:31])
        original = h.bulk[token]['cookie'].copy()
        slot = h.bulk[token]['slot']
        image = h.device_images[token]
        before = h.row.copy()
        h.acquire_packet(token, fail_kind=kind, outcome=outcome, result=FAULT)
        fields = O['failure_fields'](original, slot, kind, outcome)
        wanted = original + [fields['prefix'], fields['dma'], fields['bytes'], outcome,
                             O['REASON_IO'], FAULT, fields['operation'], 0] + [0]*4
        assert h.acquire[25:42] == wanted and h.acquire[42:59] == wanted and h.acquire[2] == 1
        assert h.row[18] == before[18] and h.row[33:36] == before[33:36]
        assert h.row[69:73] == before[69:73] and h.row[50] == h.row[90] == 0
        assert h.udc[2:6] == [2, 1, 1, O['REASON_IO']]
        cpu_d, cpu_p = O['expected_visibility'](slot, image['descriptor'], image['payload'],
            fail_kind=kind, outcome=outcome)
        assert struct.pack('>4I', *h.udc[24:28]) == cpu_d
        _acq_record(h, records, 'hook-failure', short, original_cookie=original,
            expected_failure=wanted, descriptor_hex=cpu_d.hex(), payload_hex=cpu_p.hex(),
            trace=[list(row) for row in O['acquire_trace'](slot, fail_kind=kind, outcome=outcome)])
        _acq_fault_only(h, records, token, O['REASON_IO'], label='same fault retry, no cache tail')
        _acq_fault_only(h, records, token, O['REASON_IO'], supplied=0x5a17,
            label='endpoint reason cannot overwrite first acquisition failure')
        _acq_fault_barrier(h, records, token, O['REASON_IO'])
        sequence, owner = _acq_reset_recover(h, records, token, owner)
        _acq_finish_page(h, records, name, small, images)
        assert h.acquire[2] == 1 and h.acquire[42:59] == wanted
        assert h.acquire[44] == 2 and h.acquire[27] == 3, 'original failed G2 survives successful G3'
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', action='store_true')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix='hp1020-udc-acquire-', dir='/tmp'))
    print('Bulk acquisition captures: '+str(temp), flush=True)
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
            acquisition_oracles = scenario(h,name,document,images)
            captures = h.finish()
        finally:
            h.abort()
        assert len(h.events) == len(h.rows) == len(h.ep0_rows) == len(h.out_rows) == len(h.setup_rows) == len(h.offload_rows) == len(h.program_rows) == len(h.publish_rows) == len(h.acquire_rows)
        cases.append(dict(case=title, scenario=name, fill=fill, capacity=64, interface=interface,
            status='pass', initial=h.initial, initial_ep0=h.ep0_initial,
            initial_bulk=h.out_initial, initial_setup=h.setup_initial, initial_offload=h.offload_initial, initial_program=h.program_initial, initial_publish=h.publish_initial, initial_acquire=h.acquire_initial,
            steps=h.rows, ep0_steps=h.ep0_rows, bulk_steps=h.out_rows, setup_steps=h.setup_rows, offload_steps=h.offload_rows, program_steps=h.program_rows, publish_steps=h.publish_rows, acquire_steps=h.acquire_rows,
            events=h.events, packet_oracles=h.packets, descriptor_oracles=h.descriptor_oracles,
            bulk_descriptor_oracles=h.bulk_oracles, setup_oracles=h.ingress_oracles, offload_oracles=h.offload_oracles, program_oracles=h.program_oracles,
            expected_program_trace=h.expected_trace, supplied_reads=h.expected_reads,
            acquisition_oracles=acquisition_oracles,
            expected_documents=h.expected_documents, expected_pixels_sha256=core.sha(h.expected_pixels),
            pixels_bytes=len(h.expected_pixels), capture_sha256={n:core.sha(raw) for n,raw in captures.items()}))
        replay.append((h,captures,directory))
        print(f'Bulk acquisition: {len(cases)}/{len(matrix)} host cases passed', flush=True)
    unchanged()
    target = None
    if args.target:
        core.command(['bash', ROOT/'scripts/build-hp1020-udc-acquire-target.sh'])
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
                                  ('hp1020_offload_fixture_stats',80), ('hp1020_program_fixture_stats',64), ('hp1020_publish_fixture_stats',64), ('hp1020_acquire_fixture_stats',80)):
                result.append(list(struct.unpack('>'+str(length)+'I',q.read(program.symbols[symbol],length*4))))
            return result

        with QemuRAM() as q:
            version = q.version
            for case,(h,captures,directory) in zip(cases,replay):
                q.load(elf)
                assert q.call0(program.symbols['hp1020_bulk_fixture_reset'],[case['fill'],64,case['interface'],0xffffffff]) == 0
                initial,e,b,s,o,p,u,a = rows(q)
                assert initial[:59]+initial[60:] == h.initial[:59]+h.initial[60:]
                assert (e,b,s,o) == (h.ep0_initial,h.out_initial,h.setup_initial,h.offload_initial)
                assert p[:57]+p[58:] == h.program_initial[:57]+h.program_initial[58:]
                assert u[:58]+u[59:] == h.publish_initial[:58]+h.publish_initial[59:]
                assert a[:59]+a[60:] == h.acquire_initial[:59]+h.acquire_initial[60:]
                for index,(event,host_row,host_ep0,host_bulk,host_setup,host_offload,host_program,host_publish,host_acquire) in enumerate(zip(
                        h.events,h.rows,h.ep0_rows,h.out_rows,h.setup_rows,h.offload_rows,h.program_rows,h.publish_rows,h.acquire_rows)):
                    validate_event(event['words'], bytes.fromhex(event['data_hex']))
                    data = bytes.fromhex(event['data_hex'])
                    if data:
                        q.put(program.symbols['hp1020_bulk_fixture_input'],data)
                    result = q.call0(program.symbols['hp1020_bulk_fixture_step'],event['words'])
                    row,e,b,s,o,p,u,a = rows(q)
                    with (directory/'target-steps.jsonl').open('a') as output:
                        output.write(json.dumps(row+e+b+s+o+p+u+a)+'\n')
                    assert result == row[0] == event['result'] and row[15:17] == [0,1]
                    assert e[2:5] == [0,1,1] and b[7:10] == [0,1,1] and s[12:15] == [0,1,3] and o[11:13] == [0,1]
                    assert row[:59]+row[60:] == host_row[:59]+host_row[60:], (case['case'],index,row,host_row)
                    assert (e,b,s,o) == (host_ep0,host_bulk,host_setup,host_offload), (case['case'],index,e,b,s,o)
                    assert p[:57]+p[58:] == host_program[:57]+host_program[58:], (case['case'],index,p,host_program)
                    assert u[:58]+u[59:] == host_publish[:58]+host_publish[59:], (case['case'],index,u,host_publish)
                    assert a[:59]+a[60:] == host_acquire[:59]+host_acquire[60:], (case['case'],index,a,host_acquire)
                observed = {}
                for name,symbol in (('pixels','hp1020_bulk_fixture_pixels'),('wire','hp1020_bulk_fixture_wire'),
                                    ('documents','hp1020_bulk_fixture_documents')):
                    observed[name] = q.read(program.symbols[symbol],len(captures[name]))
                for name,symbol in (('receive','hp1020_bulk_fixture_receive_storage'),
                        ('output','hp1020_bulk_fixture_output_storage'),('ep0','hp1020_ep0_fixture_storage'),
                        ('bulk_descriptor','hp1020_composed_fixture_out_storage'),
                        ('setup_record','hp1020_composed_fixture_setup_storage'),
                        ('acquire_device','hp1020_acquire_fixture_device_storage')):
                    observed[name] = q.read(q.call0(program.symbols[symbol],[]),len(captures[name]))
                for name,symbol in (('ep0','hp1020_ep0_fixture_storage_bytes'),
                        ('bulk_descriptor','hp1020_composed_fixture_out_storage_bytes'),
                        ('setup_record','hp1020_composed_fixture_setup_storage_bytes'),
                        ('acquire_device','hp1020_acquire_fixture_device_storage_bytes')):
                    assert q.call0(program.symbols[symbol],[]) == len(captures[name])
                observed['program_reads'] = q.read(program.symbols['hp1020_program_fixture_reads']+16, p[24]*12)
                observed['program_trace'] = q.read(program.symbols['hp1020_program_fixture_trace']+16, p[26]*24)
                observed['program_storage'] = (q.read(program.symbols['hp1020_program_fixture_reads'],3104) +
                    q.read(program.symbols['hp1020_program_fixture_trace'],24608))
                sizes = {'program':p[57], 'publisher':u[58], 'acquisition':a[59]}
                assert q.call0(program.symbols['hp1020_acquire_fixture_component_bytes'],[]) == a[59]
                assert q.call0(program.symbols['hp1020_publish_fixture_component_bytes'],[]) == u[58]
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
                print(f'Bulk acquisition: {len(native)}/{len(cases)} target cases passed',flush=True)
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
        cases=cases,target=target,target_publisher_bytes=target['cases'][0]['component_and_allocation_bytes']['publisher'] if target else None,
        target_acquisition_bytes=target['cases'][0]['component_and_allocation_bytes']['acquisition'] if target else None,completed_native_page_lifecycles=0,
        usb_transfers=0,actual_peripheral_accesses=0,controller_quiescence_established=False,
        scope='Synchronous post-device acquisition of the original retained OUT descriptor16 and payload64 through mandatory recording hooks, actual CPU copies and the shared existing observer. Separate synthetic device images and poisoned CPU storage, original cookies, partial visibility failures, bounded hook ordering and exact page/document output are compared on host and audited Xtensa RAM.',
        limits='No physical register/cache backend, DMA/IRQ producer, boot, USB traffic or printing. Transfer settlement, stationary exclusive CPU/DMA mappings, safe cache-line envelopes and real acquire/compiler ordering remain supplied. Fixture hook effects are explicit synthetic input copies, not a cache/DMA model. No speculative-load or device-visibility proof follows. Tests add zero native or physical page lifecycles; first profile is full-speed64, configuration0/1, interface0/alt0.')
    name = 'validation' if args.target else 'host-validation'
    raw = json.dumps(report,sort_keys=True,separators=(',',':'))+'\n'
    (temp/(name+'.json')).write_text(raw)
    (OUT/(name+'.json')).write_text(raw)
    (OUT/(name+'.md')).write_text('# Retained bulk-OUT acquisition execution\n\n'+report['scope']+'\n\n'+
        f'{len(cases)} host; {len(target["cases"]) if target else 0} QEMU cases. Every explicit read, attempted register/cache/acquire hook, original identity, device image, CPU visibility effect, packet, pixel, document event and guarded allocation is compared.\n\n'+report['limits']+'\n')


if __name__ == '__main__':
    main()
