#!/usr/bin/env python3
"""Composed SETUP/EP0/OUT records to exact documents in synthetic RAM.
No physical USB, MMIO, upload, cache operation or printing.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import runpy
import re
import select
import shutil
import struct
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('composed_ep0', ROOT/'scripts/validate-hp1020-udc-ep0.py')
ep0 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = ep0
spec.loader.exec_module(ep0)
base, core = ep0.base, ep0.core
spec = importlib.util.spec_from_file_location('composed_bulk', ROOT/'scripts/validate-hp1020-udc-out.py')
bulk_reference = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bulk_reference
spec.loader.exec_module(bulk_reference)
SRC = ROOT/'open-firmware/udc-composed-test'
SETUP = ROOT/'open-firmware/udc-setup'
BULK = ROOT/'open-firmware/udc-out'
OUT = ROOT/'analysis/usb-path/udc-composed'
OK, WAIT, STALE, INVALID, FAULT, ADAPTER_ERROR, LIMIT = range(7)
FREE, PREPARED, EXPOSED = range(3)
OUT_DMA, BUFFER_DMA, BUFFER_STEP, SETUP_DMA = 0x579bdf10, 0x24681340, 0x1000, 0x79bdf130
FACTS = 0x010101


# Reuse existing original-byte evidence; this adds no stock execution.
_REPORT = 'analysis/usb-path/setup-ingress.json'
_STOCK = '2111560068db47ceca21fa550db4c7c34f5595b5a5d137ae4a19631e40e3601d'
_LINUX = 'adc218676eef25575469234709c2d87185ca223a'
_TINYUSB = 'dae3f9a366bfcddbf9dcf1b48d7500286a849539'
_REF = 'analysis/usb-path/controller-reference/linux-v6.12/'
_TUSB = 'vendor/tinyusb-0.21.0/'
_SOURCE_PINS = {
    'analysis/sihp1020.elf': _STOCK,
    'scripts/validate-hp1020-usb-setup-ingress.py':
        'c60d332b1106eb72c836962f2f24e9319756922f946c6c318928513aa1dc5c1e',
    'scripts/hp1020_xtensa_properties.py':
        '8a98e5ba3ead469cd431a06260e78c836993348d878ae96595d0b622538d0280',
    _REF + 'amd5536udc.h':
        '8dbf2ebffe7de042bdfea1c5e4e0d7e7ca334cb821fbfaa1cf9ccfeeae302648',
    _REF + 'snps_udc_core.c':
        'c1b09e8f69d3340f2afd3a033d77a42775b52716d45b1aceb211dcaab89127bf',
    _REF + 'provenance.json':
        '023d10e246e4852c1b9415cdc3d591006edcedeba467a56b95b22b994d4a08e4',
    _TUSB + 'src/device/dcd.h':
        'baf785f2d5d8e3f74bd6d6a04559fc606d341983aad35aa08e168b452c2750db',
    _TUSB + 'PROVENANCE.json':
        '31ee172160e0c9e51cec7fa0e3e9348e4b20b92493743849fcba649542eae2e0',
}
_CODE = {
    (0x10008ff0, 0x10008ff3):
        'abf2a2b8451f111b81b36ce18b7df8a89436112a69aaa87faeafea9fd7f5e989',
    (0x1000935b, 0x1000941d):
        'e63fe132beeff99b0602625ec3f3d4a5f8fe3c5c048c0d2a5ceb65d8c5f175aa',
}
_EXCLUDED = (0x10008ff3, 0x100091b0, 0x100091c7, 0x10009347,
             0x10009358, 0x1000941d, 0x10009884, 0x10009890,
             0x10009896, 0x10008208, 0x100084b4, 0x100086c0,
             0x100086f4, 0x10008c24)
_WIRES = ('8006000100001200', 'a10034127856bc9a')


def _report(ROOT):
    ROOT = Path(ROOT)
    raw = (ROOT / _REPORT).read_bytes()
    report = json.loads(raw)
    assert report['status'] == 'pass'
    for name in report['source_sha256']:
        path = Path(name)
        assert not path.is_absolute() and '..' not in path.parts
        assert path.as_posix() == name
    return ROOT, raw, report


def setup_reference_source_paths(ROOT):
    """Paths to add to the caller's own frozen source closure, including report.

    Also capture the implementation containing these functions. This list does
    not include/rewrite old raw captures or synthesize a new execution report.
    """
    ROOT, _, report = _report(ROOT)
    return tuple(ROOT / name for name in sorted({_REPORT, *report['source_sha256']}))


def setup_original_reference(ROOT, sha):
    """Verify saved evidence/bytes and return a concise independent reference.

    This function does not reproduce the firmware's conversion as a driver API.
    The composed adapter must pass raw wire bytes, not the old converted buffer.
    """
    ROOT, raw_report, report = _report(ROOT)
    sources = report['source_sha256']
    assert len(sources) == 15
    for name, digest in sources.items():
        assert re.fullmatch(r'[0-9a-f]{64}', digest)
        assert sha((ROOT / name).read_bytes()) == digest, name
    for name, digest in _SOURCE_PINS.items():
        assert sources[name] == digest, name

    # This dependency is a read-only ELF section parser already in the captured
    # original experiment's verified closure. No instruction decoder is run.
    import hp1020_xtensa_properties as elf
    assert sha(Path(elf.__file__).read_bytes()) == sources['scripts/hp1020_xtensa_properties.py']
    properties, section_bytes = elf.properties, elf.section_bytes
    stock = (ROOT / 'analysis/sihp1020.elf').read_bytes()
    assert sha(stock) == report['stock_elf_sha256'] == _STOCK
    sections, _ = properties(stock)
    ranges = report['original_byte_ranges']
    assert {(int(a['begin'], 16), int(a['end'], 16)): a['sha256'] for a in ranges} == _CODE
    for anchor in ranges + report['static_only_irq_byte_ranges']:
        begin, end = int(anchor['begin'], 16), int(anchor['end'], 16)
        raw = section_bytes(stock, sections, begin, end - begin)
        assert raw.hex() == anchor['bytes'] and sha(raw) == anchor['sha256']
    for address, anchor in report['instruction_anchors'].items():
        pc, encoded = int(address, 16), bytes.fromhex(anchor['bytes'])
        assert section_bytes(stock, sections, pc, len(encoded)) == encoded
        assert anchor['executed_region'] == any(a <= pc < b for a, b in _CODE)
    required = {
        0x10008ff0: ('entry', [1, 128], '6c1010'),
        0x10009361: ('l32i.n', [11, 8, 0], '8b80'),
        0x10009387: ('and', [8, 10, 8], '08a801'),
        0x1000938a: ('beq', [8, 9, 0x10009390], '798102'),
        0x10009393: ('bnone', [10, 8, 0x10009399], '78a002'),
        0x10009399: ('l32r', [8, 0x10005ee8], '18f2d3'),
        0x1000939c: ('l32i', [12, 8, 0], '2c8200'),
        0x1000939f: ('addi', [4, 12, 8], '24cc08'),
        0x100093c6: ('s8i', [8, 4, 6], '284406'),
        0x100093d5: ('s8i', [10, 4, 7], '2a4407'),
        0x100093fc: ('s8i', [8, 4, 4], '284404'),
        0x1000940b: ('s8i', [10, 4, 5], '2a4405'),
    }
    for pc, (op, args, encoded) in required.items():
        anchor = report['instruction_anchors'][hex(pc)]
        assert (anchor['op'], anchor['args'], anchor['bytes']) == (op, args, encoded)
    for address, value in report['literal_anchors'].items():
        assert int.from_bytes(section_bytes(stock, sections, int(address, 16), 4), 'big') == int(value, 16)
    for address, value in ((0x10005e30, 0xc0000000), (0x10005e34, 0x80000000),
                           (0x10005f24, 0x30000000), (0x10005ee8, 0x1001bbc0),
                           (0x10005ef4, 0xb3000210), (0x10005ef8, 0xb3000214),
                           (0x1001bbc0, 0x90021340)):
        assert report['literal_anchors'][hex(address)] == hex(value)

    linux = json.loads((ROOT / (_REF + 'provenance.json')).read_bytes())
    tinyusb = json.loads((ROOT / (_TUSB + 'PROVENANCE.json')).read_bytes())
    assert report['upstream_commit'] == linux['commit'] == _LINUX
    assert tinyusb['commit'] == _TINYUSB
    linux_files = {p['path']: p for p in linux['files']}
    for name in ('amd5536udc.h', 'snps_udc_core.c'):
        item = linux_files['drivers/usb/gadget/udc/' + name]
        assert item['sha256'] == _SOURCE_PINS[_REF + name]
        assert item['url'] == f'https://raw.githubusercontent.com/torvalds/linux/{_LINUX}/drivers/usb/gadget/udc/{name}'
    assert tinyusb['upstream_files']['src/device/dcd.h']['sha256'] == _SOURCE_PINS[_TUSB + 'src/device/dcd.h']
    header = (ROOT / (_REF + 'amd5536udc.h')).read_text()
    definitions = {n: int(v, 0) for n, v in re.findall(
        r'^#define\s+(UDC_\w+)\s+(0x[0-9a-fA-F]+|[0-9]+)\s*(?:/\*.*)?$', header, re.M)}
    for name, value in (('UDC_DMA_STP_STS_BS_MASK', 0xc0000000),
                        ('UDC_DMA_STP_STS_BS_DMA_DONE', 2), ('UDC_DMA_STP_STS_BS_OFS', 30),
                        ('UDC_DMA_STP_STS_RX_MASK', 0x30000000), ('UDC_DMA_STP_STS_RX_OFS', 28),
                        ('UDC_EP_SUBPTR_ADDR', 0x10), ('UDC_EP_DESPTR_ADDR', 0x14)):
        assert definitions[name] == value
    shape = re.search(r'struct\s+udc_stp_dma\s*\{(.*?)\}\s*__attribute__\s*\(\(aligned\s*\(16\)\)\);', header, re.S)
    assert shape and re.findall(r'\bu32\s+(\w+)\s*;', shape[1]) == ['status', '_reserved', 'data12', 'data34']
    dcd = (ROOT / (_TUSB + 'src/device/dcd.h')).read_text()
    body = re.search(r'\bdcd_event_setup_received\s*\([^)]*\)\s*\{(.*?)\n\}', dcd, re.S)
    assert body
    compact = ''.join(body[1].split())
    assert 'memcpy(&event.setup_received,setup,sizeof(tusb_control_request_t))' in compact
    for field in ('wValue', 'wIndex', 'wLength'):
        assert f'event.setup_received.{field}=tu_le16toh(event.setup_received.{field});' in compact

    assert len(report['cases']) == 70 and len(report['peripheral_rejection_controls']) == 6
    assert tuple(int(c['pc'], 16) for c in report['excluded_code_controls']) == _EXCLUDED
    assert all(c['status'] == 'rejected before execution in both engines' for c in report['excluded_code_controls'])
    assert report['original_entry'] == '0x10008ff0' and report['explicit_cut_resume'] == '0x1000935b'
    assert report['stop_before'] == ['0x1000941d', '0x10009890']
    assert report['private_literal_redirect'] == dict(address='0x10005ef4', guarded_ram='0x22700100', original='0xb3000210')
    assert report['supplied_service_calls'] == []
    assert report['actual_peripheral_accesses'] == report['completed_usb_control_transfers'] == report['completed_native_page_lifecycles'] == 0
    assert report['controller_quiescence_established'] is False

    def records(case, transform):
        wire = bytes.fromhex(case['wire_hex'])
        other = bytes(b ^ 255 for b in wire)
        converted = wire[:4] + wire[4:6][::-1] + wire[6:8][::-1]
        status = ((case['owner'] << 30) | (case['rx'] << 28) | case['low_bits']).to_bytes(4, 'big')
        first = status + bytes.fromhex('5a1b2c3d') + (other if case['separate_pointer'] else wire)
        second = case['other_header'].to_bytes(4, 'big') + bytes.fromhex('e5d4c3b2') + (wire if case['separate_pointer'] else other)
        if transform:
            if case['separate_pointer']:
                second = second[:8] + converted
            else:
                first = first[:8] + converted
        return first.hex(), second.hex()

    def verify_pair(row, rejection=False):
        case, a, b = row['case'], row['interpreter'], row['qemu']
        admitted = case['owner'] == 2 and case['rx'] == 0
        wire = bytes.fromhex(case['wire_hex'])
        expected_records = records(case, admitted and not rejection)
        expected_fields = dict(bmRequestType=wire[0], bRequest=wire[1],
            wValue=int.from_bytes(wire[2:4], 'little'), wIndex=int.from_bytes(wire[4:6], 'little'),
            wLength=int.from_bytes(wire[6:8], 'little'))
        for observed in (a, b):
            assert observed['status'] == 'pass' and observed['case'] == case
            assert observed['descriptor_status_passes_oracle'] is admitted
            assert observed['raw_wire_fields'] == expected_fields
            assert (observed['status_record_after'], observed['other_record_after']) == expected_records
            assert observed['exact_nonstack_memory_equal'] and observed['original_code_unchanged']
            assert observed['actual_peripheral_accesses'] == 0
            assert observed['nonstack_memory'] == observed['expected_memory']
            visited = {int(pc, 16) for pc in observed['original_instructions_visited']}
            assert {0x10008ff0, 0x1000935b} <= visited and not set(_EXCLUDED) & visited
            cut = observed['explicit_cuts']
            assert len(cut) == 1 and cut[0]['after'] == '0x10008ff0' and cut[0]['resume'] == '0x1000935b'
            assert cut[0]['stack_pointer'] == observed['register_a1_to_a15'][0] == '0x2101fe70'
            assert cut[0]['supplied_a2_to_a15'] == [hex(0x5aa55aa5 ^ (case['fill'] * 0x01010101) ^ (i * 0x01020304)) for i in range(2, 16)]
            if rejection:
                assert observed['failure'] == dict(type='ValueError', reason='MMIO forbidden', pc=hex(case['reject_pc']))
                assert observed['stop_before'] is None and case['reject_pc'] not in visited
                assert observed['nonstack_memory'] == observed['before_memory']
            else:
                assert observed['failure'] is None
                assert observed['stop_before'] == ('0x1000941d' if admitted else '0x10009890')
                if admitted:
                    packet = 0x22700300 if case['separate_pointer'] else 0x22700200
                    assert int(observed['register_a1_to_a15'][3], 16) == packet + 8
                    assert int(observed['register_a1_to_a15'][11], 16) == packet
                    assert int(observed['register_a1_to_a15'][8], 16) == (wire[0] << 8) | wire[1]
                    assert {0x100093c6, 0x100093d5, 0x100093fc, 0x1000940b} <= visited
                else:
                    assert not {0x10009399, 0x100093a2, 0x100093c6, 0x100093fc} & visited
                    assert observed['nonstack_memory'] == observed['before_memory']
        for key in ('failure', 'stop_before', 'explicit_cuts', 'descriptor_status_passes_oracle',
                    'raw_wire_fields', 'status_record_after', 'other_record_after',
                    'register_a1_to_a15', 'before_memory', 'expected_memory', 'nonstack_memory',
                    'original_instructions_visited'):
            assert a[key] == b[key], (case['name'], key)

    primary, separate = set(), set()
    for row in report['cases']:
        case = row['case']
        assert case['fill'] in (0, 204) and case['low_bits'] == (0x0fffffff if case['fill'] else 0)
        if case['separate_pointer']:
            assert case['kind'] == 'conditional_independent_status_and_packet_pointers'
            assert case['wire_hex'] == _WIRES[1]
            key = (case['fill'], case['owner'], case['rx'], case['other_header'])
            assert key not in separate
            separate.add(key)
        else:
            assert case['kind'] == 'same_setup_descriptor_and_packet_record' and case['other_header'] == 0xffffffff
            key = (case['fill'], case['owner'], case['rx'], case['wire_hex'])
            assert key not in primary
            primary.add(key)
        verify_pair(row)
    assert primary == {(f, o, rx, wire) for f in (0, 204) for o in range(4) for rx in range(4) for wire in _WIRES}
    assert separate == {(f, o, rx, h) for f in (0, 204) for o, rx, h in ((2, 0, 0xffffffff), (1, 0, 0x80000000), (2, 1, 0x80000000))}
    rejected = set()
    for row in report['peripheral_rejection_controls']:
        case = row['case']
        assert case['kind'] == 'guard_rejection_before_peripheral_access'
        assert case['owner'] == 2 and case['rx'] == 0 and not case['separate_pointer']
        assert case['wire_hex'] == _WIRES[1] and case['other_header'] == 0xffffffff
        assert case['low_bits'] == (0x0fffffff if case['fill'] else 0)
        key = (case['fill'], case['reject_pc'], case['reject_address'])
        assert key not in rejected
        rejected.add(key)
        verify_pair(row, rejection=True)
    assert rejected == {(f, pc, hex(address)) for f in (0, 204) for pc, address in
                        ((0x10009361, 0xb3000210), (0x10009363, 0xb3000214), (0x100093a2, 0xb300000e))}

    return dict(
        report=_REPORT, report_sha256=sha(raw_report), stock_sha256=_STOCK,
        source_paths=[str(p.relative_to(ROOT)) for p in setup_reference_source_paths(ROOT)],
        source_closure_files=15, conditional_cases_reused=70,
        execution_engines_reused=['interpreter', 'qemu'],
        primary_same_record_cases_reused=64, primary_admitted_cases_reused=4,
        conditional_separate_pointer_cases_reused=6, pre_mmio_controls_reused=6,
        excluded_pc_controls_reused=14, newly_executed_stock_instructions=0,
        owner_done=2, owner_mask='0xc0000000', rx_success=0, rx_mask='0x30000000',
        setup_record_bytes=16, setup_status_offset=0, setup_reserved_offset=4,
        setup_wire_offset=8, setup_wire_bytes=8, subptr='0xb3000210', desptr='0xb3000214',
        stock_status_and_packet_pointers_independent=True,
        single_coherent_record_is_supplied_replacement_contract=True,
        wire_vectors=[dict(raw_wire_hex=w,
            stock_converted_hex=(bytes.fromhex(w)[:4] + bytes.fromhex(w)[4:6][::-1] + bytes.fromhex(w)[6:8][::-1]).hex()) for w in _WIRES],
        stock_swapped_fields=['wIndex', 'wLength'], stock_preserved_fields=['bmRequestType', 'bRequest', 'wValue'],
        adapter_must_pass_original_wire_bytes=True, tinyusb_converts_fields=['wValue', 'wIndex', 'wLength'],
        linux_commit=_LINUX, linux_setup_header_url=linux_files['drivers/usb/gadget/udc/amd5536udc.h']['url'],
        tinyusb_commit=_TINYUSB, tinyusb_dcd_url=f'https://github.com/hathach/tinyusb/blob/{_TINYUSB}/src/device/dcd.h',
        reused_original_entry_executed=True, reused_initialization_and_wait_omitted=True,
        reused_private_literal_redirect=report['private_literal_redirect'],
        controller_quiescence_established=False, physical_mapping_or_snapshot_stability_proved=False,
        completed_usb_control_transfers=0, completed_native_page_lifecycles=0,
        limitation='Reuses completed conditional admission/conversion cuts only; no new stock execution, request dispatch, physical SETUP, IRQ, rearm, cache/stall/settlement or printing proof.')


def setup_record(raw, status=0x87ff7fff, reserved=0xa5c33ca5):
    assert len(raw) == 8
    return struct.pack('>II', status, reserved)+raw


class Host(ep0.Host):
    def __init__(self, executable, directory, fill, capacity, interface):
        self.out_rows, self.setup_rows, self.bulk = [], [], {}
        self.bulk_oracles, self.ingress_oracles = [], []
        self.bulk_publications = 0
        self.sequence = 0
        super().__init__(executable, directory, fill, capacity, interface)
        self.out_initial, self.setup_initial = self.udc.copy(), self.ingress.copy()
        assert self.udc[1:3] == [1, FREE] and self.udc[7:10] == [0,1,1]
        assert self.udc[21] == OUT_DMA and self.ingress[1:3] == [1,0]
        assert self.ingress[12:15] == [0,1,3] and self.ingress[26] == SETUP_DMA

    def read_row(self):
        if not select.select([self.process.stdout], [], [], 30)[0]:
            self.process.kill(); self.process.wait()
            raise AssertionError('composed host timed out: '+str(self.directory))
        raw = self.process.stdout.readline()
        with (self.directory/'raw-stdout').open('ab') as saved:
            saved.write(raw)
        assert raw, ('fixture ended early', self.directory)
        row = json.loads(raw)
        assert len(row) == 288, row
        self.ep0, self.udc, self.ingress = row[96:200], row[200:248], row[248:]
        return row[:96]

    def next_sequence(self):
        self.sequence += 1
        assert 0 < self.sequence < 0xffffffff
        return self.sequence

    def configure(self):
        # Unlike the base fixture's fresh-only helper, reconnect can retain a
        # historical class identity and an aborted receive reservation. Neither
        # is a fabricated class request or permission to reclaim old storage.
        class_request = self.row[80]
        self.step(5); self.service()
        self.request(base.packet(0,9,1))
        assert self.row[8] == self.row[10] == self.row[36] == self.row[44] == 1
        assert self.row[47] == 0 and self.row[80] == class_request
        issued,owned = self.row[33],self.row[35]
        self.step(6,result=WAIT,expect={33:issued,35:owned})
        self.step(10)
        packets = self.row[17]
        self.finish_reset(ack=False)
        assert self.row[17] == packets and self.row[80] == class_request and not self.row[13]

    def step(self, op, a=0, b=0, c=0, d=0, data=b'', result=OK, expect=None):
        if op == 5:
            # Existing high-level configuration helper supplies an actual reset
            # observation. It must enter the same external ingress order.
            assert not any((a,b,c,d,data))
            op, a = 83, self.next_sequence()
        row = super().step(op,a,b,c,d,data,result,expect)
        self.out_rows.append(self.udc.copy()); self.setup_rows.append(self.ingress.copy())
        with (self.directory/'host-composed-steps.jsonl').open('a') as saved:
            saved.write(json.dumps(self.udc+self.ingress)+'\n')
        assert self.udc[7:10] == [0,1,1] and self.ingress[12:15] == [0,1,3]
        if op == 6 and row[30] and row[30] not in self.bulk:
            token, slot = row[30], (row[33]-1)%4
            cookie = [token,row[5],row[32],row[33],1]
            dma = BUFFER_DMA+slot*BUFFER_STEP
            wanted = ep0.descriptor(0x08000000,dma)
            assert self.udc[16:24] == cookie+[OUT_DMA,dma,64]
            assert self.udc[47] == slot and self.udc[2] in (PREPARED,EXPOSED)
            assert struct.pack('>4I',*self.udc[24:28]) == wanted
            self.bulk[token] = dict(cookie=cookie,dma=dma,slot=slot)
            self.bulk_oracles.append(dict(step=len(self.rows)-1,kind='prepare',descriptor_hex=wanted.hex(),**self.bulk[token]))
        if self.udc[11] != self.bulk_publications:
            assert self.udc[11] == self.bulk_publications+1
            original = self.bulk[self.udc[28]]
            wanted = ep0.descriptor(0x08000000,original['dma'])
            assert self.udc[28:33] == original['cookie']
            assert self.udc[37:40] == [OUT_DMA,original['dma'],64]
            assert struct.pack('>4I',*self.udc[33:37]) == wanted
            self.bulk_oracles.append(dict(step=len(self.rows)-1,kind='publish',descriptor_hex=wanted.hex(),**original))
            self.bulk_publications = self.udc[11]
        return row

    def capture(self, raw, *, sequence=None, status=0x87ff7fff, reserved=0xa5c33ca5,
                known=0, value=0, fault=0, dma=SETUP_DMA, result=OK):
        sequence = self.next_sequence() if sequence is None else sequence
        record = setup_record(raw,status,reserved)
        self.step(80,data=record)
        before = self.row.copy(),self.ingress.copy()
        self.step(81,sequence,dma,fault,(value<<8)|known,result=result)
        assert self.row[2:96] == before[0][2:96], 'offer cannot admit a protocol request'
        if result == OK:
            assert self.ingress[2:5] == [1,sequence,sequence]
            assert self.ingress[22:26] == [sequence,dma,fault,(value<<8)|known]
            assert struct.pack('>4I',*self.ingress[32:36]) == record
            self.ingress_oracles.append(dict(step=len(self.rows)-1,kind='capture',sequence=sequence,
                record_hex=record.hex(),printer_status=[value,known],record_dma=dma,endpoint_fault=fault))
        return sequence

    def dispatch(self, sequence, *, facts=FACTS, stalls=1, result=OK, service=False, service_result=OK):
        raw = struct.pack('>4I',*self.ingress[32:36])
        epoch = self.row[2]
        self.step(82,sequence,facts,stalls,result=result)
        if result == OK:
            self.requested = struct.unpack_from('<H',raw,14)[0]
            assert self.ingress[2:4] == [0,0] and self.ingress[6] == sequence
            assert self.row[2] == epoch+1 and self.ingress[7] == self.row[2]
            self.ingress_oracles.append(dict(step=len(self.rows)-1,kind='admit',sequence=sequence,record_hex=raw.hex()))
        if service:
            self.service(service_result)

    def setup(self, raw, known=0, status=0, service_result=OK):
        sequence = self.capture(raw,known=known,value=status)
        self.dispatch(sequence,service=True,service_result=service_result)

    def arm_write(self, data):
        assert len(data) <= 64
        self.step(6)
        token = self.row[30]
        assert token in self.bulk and self.row[31] == 64
        if data:
            self.step(65,token,1,0,len(data),data=data)
        return token

    def observe_bulk(self, token, status, *, facts=FACTS, fault=0, mutant=0,
                     write=False, result=OK):
        raw = ep0.descriptor(status,self.bulk[token]['dma'])
        if write:
            self.step(65,token,0,0,16,data=raw)
        return self.step(62,token,facts,fault,mutant,data=raw,result=result)

    def complete(self, token, length, usb_result=0, result=OK, service=True):
        if token not in self.bulk:
            return super().complete(token,length,usb_result,result,service)
        assert usb_result == 0, 'bulk endpoint fault has explicit observation ingress'
        self.observe_bulk(token,0x88000000|length,write=result!=STALE,result=result)
        if service:
            self.service()

    def forward_state(self):
        # Actual submission count, wire count/hash, pixel/output activity and
        # document notifications. Controller settlement is allowed to change
        # completion/cancellation counters, but cannot create forward work.
        return tuple(self.row[17:18]+self.row[24:26]+self.row[50:59]+self.row[90:96])

    def blocked(self):
        assert self.ingress[11] == 0
        before = self.row.copy()
        for op in (1,6,7):
            self.step(op,result=WAIT)
            assert self.row[2:96] == before[2:96]
        assert self.ingress[27] >= 3

    def cancel_retained(self):
        for token in (self.row[26],self.row[28]):
            if token:
                self.step(43,token,1)
        if self.row[30]:
            self.step(64,self.row[30],1)

    def finish(self):
        captures = super().finish()
        raw = (self.directory/'output.udc-descriptor').read_bytes()
        assert len(raw) == 48 and raw[:16] == raw[32:] == bytes([self.fill])*16
        assert raw[16:32] == struct.pack('>4I',*self.udc[24:28])
        captures['bulk_descriptor'] = raw
        raw = (self.directory/'output.setup-record').read_bytes()
        assert len(raw) == 48 and raw[:16] == raw[32:] == bytes([self.fill])*16
        assert raw[16:32] == struct.pack('>4I',*self.ingress[28:32])
        captures['setup_record'] = raw
        return captures


def _raw_si_transport(h):
    """Bulk/document facts a rejected control request has no right to change."""
    r = h.row
    return (tuple(r[4:6]), tuple(r[7:11]), r[12], r[13] & 4, r[14] & 4,
            tuple(r[30:46]), tuple(r[50:62]), tuple(r[69:77]),
            tuple(r[81:85]), r[11] & 12,
            tuple(h.udc[2:7]), tuple(h.udc[10:40]))


def _raw_si_reply_activity(h):
    # Cancellations are deliberately separate from completed status/data.
    return (h.row[17], h.row[18], tuple(h.row[24:26]),
            tuple(h.slot(0)[31:34]), tuple(h.slot(1)[31:34]))


def _raw_si_partial(h, document):
    data = document(['small'])
    assert len(data) > 62 and h.capacity == 64
    h.send(data[:31], 31, zlp=False)
    token = h.arm_write(data[31:62])
    cookie = h.bulk[token]['cookie'].copy()
    assert h.udc[16:21] == cookie and h.row[30] == token
    assert h.row[50] == 0 and h.row[90:92] == [0, 0]
    return data, token, cookie


def _raw_si_finish_partial(h, data, token, cookie, generation, images):
    assert h.row[30] == token and h.udc[16:21] == cookie
    assert h.bulk[token]['cookie'] == cookie and h.row[32] == generation
    h.complete(token, 31)
    h.step(7)
    h.send(data[62:], 64)
    h.expected_pixels += images['small'][1]
    h.notification(generation, 1, 0, 1)
    assert h.row[32] == generation and h.row[36] == 0
    h.repeat_pump()


def _raw_si_reject(h, raw, *, old_ep0=None):
    """Admit a real raw request; no invented callback or DCD settlement."""
    transport, activity = _raw_si_transport(h), _raw_si_reply_activity(h)
    control_epoch, class_id = h.row[2], h.row[80]
    sequence = h.capture(raw)
    h.dispatch(sequence)
    assert h.row[2] == control_epoch + 1 and h.row[80] == class_id
    assert _raw_si_transport(h) == transport
    assert h.row[47] == 0, 'new control identity suppresses an older deferred reply'
    if old_ep0 is not None:
        original = h.controls[old_ep0]['cookie'].copy()
        owned = h.slot(1)[14:18].copy(), h.slot(1)[42]
        h.service(base.WAIT)
        assert h.row[28] == old_ep0 and h.slot(1)[6:11] == original
        assert h.slot(1)[1] == 1 and h.row[11] & 3 == 0
        assert _raw_si_reply_activity(h) == activity
        h.step(43, old_ep0, 0, result=WAIT)
        assert (h.slot(1)[14:18], h.slot(1)[42]) == owned
        assert h.row[28] == old_ep0 and _raw_si_transport(h) == transport
        h.step(43, old_ep0, 1)  # Explicit original EP0 settlement supplied once.
        assert h.row[28] == 0 and h.slot(1)[0] == 0
        assert _raw_si_transport(h) == transport
    h.service()
    assert h.row[2] == h.row[3] and h.row[11] & 3 == 3
    assert not h.row[26] and not h.row[28] and h.row[77] == 0
    assert h.slot(0)[0] == h.slot(1)[0] == 0
    assert h.row[80] == class_id and h.row[47] == 0
    assert _raw_si_transport(h) == transport
    assert _raw_si_reply_activity(h) == activity, 'STALL is neither a status packet nor an ACK'
    for _ in range(2):
        h.service()
        assert _raw_si_transport(h) == transport
        assert _raw_si_reply_activity(h) == activity
    return dict(sequence=sequence, raw_hex=raw.hex(), control_epoch=h.row[2],
                transport_epoch=h.row[4], receive_generation=h.row[32],
                fixture_ep0_stall_mask=h.row[11] & 3, new_reply_packets=0)


def _raw_si_control_recovery(h):
    transport = _raw_si_transport(h)
    h.request(base.packet(0x81, 10, index=h.interface, length=1), b'\x00',
              label='fresh-GET_INTERFACE-after-raw-SI-rejection')
    assert h.row[11] & 3 == 0 and _raw_si_transport(h) == transport
    h.request(base.packet(0xa1, 1, index=h.interface, length=1), b'\x18',
              label='fresh-unknown-printer-status-after-raw-SI-rejection')
    assert _raw_si_transport(h) == transport


def raw_si_scenario(h, name, document, images):
    assert h.interface in (0, 3) and h.capacity == 64
    records = []
    if name == 'raw-si/unconfigured':
        h.step(5)
        h.service()
        generation = h.row[32]
        assert h.row[8] == h.row[10] == h.row[44] == 0
        records.append(_raw_si_reject(h, base.packet(1, 11, index=h.interface)))
        h.step(10, result=base.WAIT)
        h.step(6, result=base.WAIT)
        assert h.row[32] == generation
        h.request(base.packet(0x80, 8, length=1), b'\x00', label='still-unconfigured-after-rejected-SI')
        h.request(base.packet(0x80, 6, value=0x100, length=18), base.DEVICE,
                  label='fresh-device-request-after-unconfigured-SI')
        h.configure()
        _raw_si_control_recovery(h)
        h.fresh_page(document, images)
        return records

    h.configure()
    generation = h.row[32]
    if name in ('raw-si/live-partial', 'raw-si/retained-ep0', 'raw-si/field-controls'):
        data, bulk, cookie = _raw_si_partial(h, document)
        old_ep0 = None
        if name == 'raw-si/retained-ep0':
            h.setup(base.packet(0xa1, 0, index=h.interface << 8, length=400))
            old_ep0 = h.row[28]
            h.wire(base.DEVICE_ID[:64], 'old-ID-data-before-raw-SI-cancellation')
            assert h.row[77] == 1 and h.slot(1)[0] != 0
        if name == 'raw-si/field-controls':
            # The zero-length direction alias is allowed by 9.3.1; it uses
            # the same permitted sole-default rejection. Nonzero length is
            # conservatively rejected, not called specified Request Error.
            requests = (
                ('unsupported-alt1', base.packet(1, 11, value=1, index=h.interface)),
                ('unsupported-high-alt', base.packet(1, 11, value=0x100, index=h.interface)),
                ('wrong-low-interface', base.packet(1, 11, index=0 if h.interface else 1)),
                ('wrong-high-interface', base.packet(1, 11, index=0x100 | h.interface)),
                ('zero-length-direction-alias', base.packet(0x81, 11, index=h.interface)),
                ('nonzero-OUT-length', base.packet(1, 11, index=h.interface, length=1)),
                ('nonzero-IN-length', base.packet(0x81, 11, index=h.interface, length=1)),
            )
        else:
            requests = (('sole-default-alt0', base.packet(1, 11, index=h.interface)),)
        for reason, raw in requests:
            record = _raw_si_reject(h, raw, old_ep0=old_ep0)
            record['policy_case'] = reason
            records.append(record)
            old_ep0 = None
            _raw_si_control_recovery(h)
            assert h.row[30] == bulk and h.udc[16:21] == cookie
            assert h.row[32] == generation and h.row[7] == h.row[36] == 0
        _raw_si_finish_partial(h, data, bulk, cookie, generation, images)
        return records

    if name == 'raw-si/existing-fault':
        data, bulk, cookie = _raw_si_partial(h, document)
        h.observe_bulk(bulk, 0x48000000, facts=0, fault=0x80, result=FAULT)
        assert h.row[7] == h.row[36] == h.udc[3] == 1
        h.step(10, result=base.WAIT)
        records.append(_raw_si_reject(h, base.packet(1, 11, index=h.interface)))
        _raw_si_control_recovery(h)
        assert h.row[30] == bulk and h.udc[16:21] == cookie
        assert h.row[32] == generation and h.row[44] == 0
        h.step(6, result=base.WAIT)
        # Only a separately requested real reset may replace the old fault.
        h.setup(base.packet(0x21, 2, index=h.interface))
        # Class reset begins a deferred recovery before bulk settlement; it
        # does not alter endpoints like standard reconfiguration. Completion
        # must still wait on the retained original owner and all promises.
        assert h.row[30] == bulk and h.udc[16:21] == cookie
        assert h.row[44] == h.row[47] == 1 and not h.row[26] and not h.row[28]
        h.step(10)
        h.step(12, 0, result=base.WAIT)
        h.step(64, bulk, 0, result=WAIT)
        h.step(64, bulk, 1)
        h.service()
        h.step(10)
        h.finish_reset()
        assert h.row[32] == generation + 1
        h.fresh_page(document, images)
        return records

    if name == 'raw-si/pending-reset':
        h.begin_reset()
        h.step(11, 0, 1)
        h.step(11, 0, 2)
        h.step(15)
        h.step(11, 0, 4)
        assert h.row[44:48] == [1, 7, 0, 1]
        transport, activity = _raw_si_transport(h), _raw_si_reply_activity(h)
        sequence = h.capture(base.packet(1, 11, index=h.interface))
        before = h.row[2:96].copy()
        h.step(12, 0, result=base.WAIT)
        assert h.row[2:96] == before, 'held SI cannot release the old deferred reset ACK'
        h.dispatch(sequence, service=True)
        assert h.row[11] & 3 == 3 and h.row[47] == 0
        assert _raw_si_transport(h) == transport and _raw_si_reply_activity(h) == activity
        assert not h.row[26] and not h.row[28] and h.row[44:46] == [1, 7]
        # Finish the exact original recovery before any other new request;
        # this isolates raw SI's suppression of the older deferred ACK.
        h.step(12, 0, expect={32:generation+1, 7:0, 9:0, 36:0, 44:0, 45:0})
        assert _raw_si_reply_activity(h) == activity
        assert not h.row[26] and not h.row[28]
        records.append(dict(sequence=sequence, original_promises_preserved=7,
                            old_deferred_status_suppressed=True, original_recovery_finished=True,
                            receive_generation_before=generation, receive_generation_after=generation+1))
        _raw_si_control_recovery(h)
        h.fresh_page(document, images)
        return records

    if name == 'raw-si/bulk-halt':
        h.send(document(['small'])[:31], 31, zlp=False)
        h.request(base.packet(2, 3, index=1), label='supplied-OUT-Halt-before-raw-SI')
        h.request(base.packet(2, 3, index=0x81), label='supplied-IN-Halt-before-raw-SI')
        assert h.row[81:85] == [1, 1, 1, 1] and h.row[7] == h.row[36] == 1
        records.append(_raw_si_reject(h, base.packet(1, 11, index=h.interface)))
        _raw_si_control_recovery(h)
        h.request(base.packet(0x82, 0, index=1, length=2), b'\x01\x00', label='OUT-Halt-preserved-across-rejected-SI')
        h.request(base.packet(0x82, 0, index=0x81, length=2), b'\x01\x00', label='IN-Halt-preserved-across-rejected-SI')
        assert h.row[81:85] == [1, 1, 1, 1] and h.row[32] == generation
        h.step(10, result=base.WAIT)
        h.step(6, result=base.WAIT)
        h.begin_reset()
        h.finish_reset()  # Includes a new explicit op15 defaults promise.
        assert h.row[81:85] == [0, 0, 0, 0] and h.row[32] == generation + 1
        h.fresh_page(document, images)
        return records

    raise AssertionError('unknown raw SET_INTERFACE profile: ' + name)


def raw_si_profiles():
    names = ('raw-si/live-partial', 'raw-si/retained-ep0', 'raw-si/field-controls',
             'raw-si/existing-fault', 'raw-si/pending-reset', 'raw-si/bulk-halt',
             'raw-si/unconfigured')
    return [(name, fill, interface) for name in names for fill in (0, 204) for interface in (0, 3)]



def scenario(h,name,document,images):
    if name.startswith('raw-si/'):
        return raw_si_scenario(h,name,document,images)
    if name == 'reset-admission-wait':
        seq = h.next_sequence()
        before = h.row[2]
        h.step(83,seq,0,1,result=WAIT)
        assert h.ingress[2:4] == [2,seq] and h.row[2] == before
        newer = h.next_sequence()
        h.capture(base.packet(0x80,6,value=0x100,length=18),sequence=newer,result=WAIT)
        h.dispatch(seq,result=WAIT)
        h.blocked()
        h.step(83,seq)
        assert h.row[2] == before+1 and h.ingress[5] == seq
        h.step(83,seq,result=STALE)
        h.service()
        h.capture(base.packet(0x80,6,value=0x100,length=18),sequence=newer)
        h.dispatch(newer,service=True)
        h.control_in(base.DEVICE,'device-after-reset-retry')
        return
    h.configure()
    generation = h.row[32]
    if name == 'protocol':
        h.request(base.packet(0x80,6,value=0x100,length=0x123),base.DEVICE,label='device')
        h.request(base.packet(0xa1,0,index=h.interface<<8,length=0x102),base.DEVICE_ID[:0x102],label='asymmetric-ID')
        h.request(base.packet(0xa1,1,index=h.interface,length=1),b'\x38',known=1,status=0x38,label='supplied-paper-status')
        h.send(document(['small'])+document([])+document(['slim']),64)
        h.expected_pixels = images['small'][1]+images['slim'][1]
        h.expected_documents = [(generation,1,0,1,0),(generation,2,1,0,0)]
        h.notification(generation,3,1,1)
        h.repeat_pump()
        h.recover(); h.fresh_page(document,images)
        return
    if name == 'snapshot-replay':
        raw = base.packet(0xa1,1,index=h.interface,length=1)
        seq = h.capture(raw,known=1,value=0x38)
        saved = h.ingress.copy()
        h.step(80,data=setup_record(base.packet(0x80,6,value=0x100,length=18),0x40000000,0))
        assert h.ingress[22:26] == saved[22:26] and h.ingress[32:36] == saved[32:36]
        h.blocked(); h.dispatch(seq,service=True)
        h.control_in(b'\x38','immutable-status')
        epoch = h.row[2]
        h.capture(raw,sequence=seq,known=1,value=0x38,result=STALE)
        h.dispatch(seq,result=STALE)
        assert h.row[2] == epoch
        h.request(raw,b'\x38',known=1,status=0x38,label='identical-new-status')
        h.fresh_page(document,images)
        return
    if name == 'held-capture-blocks-publication':
        h.step(40,0x80,0,FACTS); h.step(60,0,FACTS)
        h.setup(base.packet(0x80,6,value=0x100,length=18))
        old = h.row[28]
        h.step(6); bulk = h.row[30]
        assert h.slot(1)[0] == h.udc[2] == PREPARED
        publications = h.slot(1)[32],h.udc[11]
        seq = h.capture(base.packet(0xa1,1,index=h.interface,length=1),known=1,value=0x38)
        before = h.row.copy()
        h.step(41,old,FACTS,result=WAIT); h.step(61,bulk,FACTS,result=WAIT)
        assert h.row[2:96] == before[2:96]
        assert (h.slot(1)[32],h.udc[11]) == publications
        h.blocked(); h.dispatch(seq,service=True,service_result=base.WAIT)
        assert h.slot(1)[1] == 1 and not h.udc[3]
        h.step(40,0x80,1,FACTS); h.step(60,1,FACTS)
        h.step(43,old,1); h.service()
        h.control_in(b'\x38','new-status-after-blocked-old-publication')
        h.step(61,bulk,FACTS)
        small = document(['small'])
        h.step(65,bulk,1,0,31,data=small[:31]); h.complete(bulk,31); h.step(7)
        h.send(small[31:],64)
        h.expected_pixels = images['small'][1]; h.notification(generation,1,0,1)
        return
    if name == 'capture-wait-newer-retry':
        old_raw = base.packet(0x80,6,value=0x100,length=18)
        new_raw = base.packet(0xa1,1,index=h.interface,length=1)
        quiet = h.forward_state()
        epoch = h.row[2]
        old = h.capture(old_raw)
        saved = h.ingress.copy()
        newer = h.next_sequence()  # Allocate once at the ORIGINAL new event.
        h.capture(new_raw,sequence=newer,known=1,value=0x38,result=WAIT)
        assert h.ingress[2:5] == [1,old,old]
        assert h.ingress[17] == saved[17] and h.ingress[22:26] == saved[22:26]
        assert struct.pack('>4I',*h.ingress[32:36]) == setup_record(old_raw)
        h.blocked()
        h.dispatch(old)  # Adapter admission only; do not service old request.
        assert h.forward_state() == quiet and h.row[2] == epoch+1
        # The caller retains the rejected event's exact raw bytes, status and
        # original sequence. No replacement identity or extra event is created.
        h.capture(new_raw,sequence=newer,known=1,value=0x38)
        assert h.ingress[22:26] == [newer,SETUP_DMA,0,0x3801]
        assert struct.pack('>4I',*h.ingress[32:36]) == setup_record(new_raw)
        h.dispatch(newer)
        assert h.ingress[6] == newer and h.ingress[19] == saved[19]+2
        assert h.row[2] == epoch+2 and h.forward_state() == quiet
        h.service()
        # Every IN byte is independently covered by finish(); an old device
        # descriptor proposal would be extra unaccounted wire data.
        h.control_in(b'\x38','original-newer-capture-after-WAIT')
        h.fresh_page(document,images)
        return
    if name == 'capture-facts':
        raw = base.packet(0x80,6,value=0x100,length=18)
        seq = h.capture(raw)
        for facts,stalls,result in ((0,1,WAIT),(0x000101,1,WAIT),(0x010001,1,WAIT),
                                  (0x010100,1,WAIT),(FACTS,0,WAIT),
                                  (0x020101,1,INVALID),(0x010201,1,INVALID),
                                  (0x0101ff,1,INVALID),(FACTS,2,INVALID)):
            h.dispatch(seq,facts=facts,stalls=stalls,result=result)
            h.blocked()
        h.dispatch(seq,service=True); h.control_in(base.DEVICE,'facts-established')
        h.fresh_page(document,images)
        return
    if name == 'raw-admission':
        raw = base.packet(0x80,6,value=0x100,length=18)
        for status,fault,result in ((0x08000000,0,WAIT),(0x48000000,0,WAIT),
                (0xc8000000,0,WAIT),(0x98000000,0,FAULT),(0xa8000000,0,FAULT),
                (0xb8000000,0,FAULT),(0x88000000,0x80,FAULT)):
            seq = h.capture(raw,status=status,fault=fault)
            h.dispatch(seq,result=result); h.blocked()
            h.configure()
        h.request(raw,base.DEVICE,label='after-invalid-raw-records')
        h.fresh_page(document,images)
        return
    if name == 'held-capture-blocks-reset-ack':
        h.begin_reset()
        h.step(11,0,1); h.step(11,0,2); h.step(15); h.step(11,0,4)
        seq = h.capture(base.packet(0x80,6,value=0x100,length=18))
        before = h.row.copy()
        h.step(12,0,result=WAIT)
        assert h.row[2:96] == before[2:96] and not h.row[28]
        h.blocked()
        h.dispatch(seq,service=True)
        h.control_in(base.DEVICE,'new-request-supersedes-deferred-reset-ack')
        count = h.row[17]
        h.step(12,0,expect={32:generation+1,7:0,9:0})
        assert h.row[17] == count and not h.row[26] and not h.row[28]
        h.fresh_page(document,images)
        return
    if name == 'superseded-control':
        small = document(['small'])
        h.setup(base.packet(0xa1,0,index=h.interface<<8,length=400))
        old = h.row[28]; h.wire(base.DEVICE_ID[:64],'old-ID-proposal')
        bulk = h.arm_write(small[:31])
        h.setup(base.packet(0xa1,1,index=h.interface,length=1),service_result=base.WAIT)
        assert h.slot(1)[1] == 1 and not h.udc[3] and not h.row[7]
        h.complete(old,64)
        h.control_in(b'\x18','new-status-only')
        h.complete(bulk,31); h.step(7); h.send(small[31:],64)
        h.expected_pixels = images['small'][1]; h.notification(generation,1,0,1)
        return
    if name == 'soft-reset-held':
        h.setup(base.packet(0xa1,0,index=h.interface<<8,length=400))
        old = h.row[28]; h.wire(base.DEVICE_ID[:64],'cancelled-ID')
        bulk = h.arm_write(document(['small'])[:31])
        h.setup(base.packet(0x21,2,index=h.interface),service_result=base.WAIT)
        assert h.slot(1)[1] == h.udc[3] == h.row[7] == h.row[36] == 1
        h.step(43,old,0,result=WAIT); h.step(64,bulk,0,result=WAIT)
        h.cancel_retained(); h.service(); h.step(10); h.finish_reset()
        h.fresh_page(document,images)
        return
    if name == 'bus-reset-retained-capture':
        h.setup(base.packet(0xa1,0,index=h.interface<<8,length=400))
        old = h.row[28]; h.wire(base.DEVICE_ID[:64],'old-ID-before-reset')
        h.arm_write(document(['small'])[:31])
        pre = h.capture(base.packet(0xa1,1,index=h.interface,length=1))
        h.step(5)
        seq = h.capture(base.packet(0x80,6,value=0x100,length=18))
        h.dispatch(seq,result=WAIT)
        assert h.ingress[2:4] == [1,seq] and h.ingress[11] == 1
        h.step(80,data=setup_record(base.packet(0,5,value=73),0,0))
        h.service(base.WAIT)
        h.cancel_retained(); h.service()
        assert h.ingress[2:4] == [1,seq] and h.ingress[11] == 0
        h.dispatch(seq,service=True); h.control_in(base.DEVICE,'retained-post-reset-device')
        h.capture(base.packet(0xa1,1,index=h.interface,length=1),sequence=pre,result=STALE)
        h.configure(); h.fresh_page(document,images)
        return
    if name == 'terminal-drains-admitted-reset':
        h.setup(base.packet(0x80,6,value=0x100,length=18))
        old = h.row[28]; h.wire(base.DEVICE,'retained-before-reset-terminal')
        bulk = h.arm_write(document(['small'])[:31])
        quiet = h.forward_state()
        # OUT stats44 packs actual adapter owner states: OUT0, IN0, bulk OUT.
        # NONE=0, DCD=1, PENDING=2; it is independent of fixture live flags.
        assert h.udc[44] == 0x010100
        h.step(5)
        reset_sequence, reset_epoch = h.ingress[5], h.row[2]
        assert h.ingress[11] == 1 and h.row[3] != reset_epoch
        raw = base.packet(0xa1,1,index=h.interface,length=1)
        h.capture(raw,sequence=0xffffffff,result=LIMIT)
        assert h.ingress[2:5] == [1,0xffffffff,0xffffffff]
        assert h.ingress[10:12] == [1,1]
        assert h.ingress[5] == reset_sequence and h.row[2] == reset_epoch
        assert struct.pack('>4I',*h.ingress[32:36]) == setup_record(raw)
        h.dispatch(0xffffffff,result=LIMIT)
        # Only service needed to drain the admitted reset is allowed. Arming,
        # pumping, finishing, reset-ACK production and delayed publication stop.
        before = h.row.copy()
        for op,a,b in ((6,0,0),(7,0,0),(8,0,0),(9,0,0),(12,0,0),
                       (41,old,FACTS),(61,bulk,FACTS)):
            h.step(op,a,b,result=WAIT)
            assert h.row[2:96] == before[2:96]
        h.service(base.WAIT)
        assert h.forward_state() == quiet and h.udc[44] == 0x010100
        h.step(43,old,0,result=WAIT); h.step(64,bulk,0,result=WAIT)
        h.cancel_retained()
        assert not h.slot(1)[0] and not h.udc[2]
        assert not any(h.row[i] for i in (26,28,30))
        assert h.udc[44] == 0x020200 and h.ingress[11] == 1
        assert h.forward_state() == quiet
        # Separately supplied settlement freed the descriptor records, but the
        # adapter still owns pending notifications until this permitted drain.
        h.service()
        assert h.udc[44] == 0 and h.ingress[11] == 0
        assert h.row[2] == h.row[3] == reset_epoch
        assert h.ingress[2:5] == [1,0xffffffff,0xffffffff]
        assert h.ingress[5] == reset_sequence and h.ingress[10] == 1
        assert struct.pack('>4I',*h.ingress[32:36]) == setup_record(raw)
        assert h.forward_state() == quiet
        h.blocked()
        assert h.udc[44] == 0 and h.forward_state() == quiet
        return
    if name.startswith('sequence-limit/'):
        h.setup(base.packet(0x80,6,value=0x100,length=18))
        old = h.row[28]; h.wire(base.DEVICE,'retained-before-sequence-limit')
        bulk = h.arm_write(document(['small'])[:31])
        before = h.row.copy()
        if name.endswith('/capture'):
            h.capture(base.packet(0xa1,1,index=h.interface,length=1),sequence=0xffffffff,result=LIMIT)
        else:
            h.step(83,0xffffffff,result=LIMIT)
        assert h.ingress[10] and h.row[2:96] == before[2:96]
        h.blocked()
        h.capture(base.packet(0xa1,1,index=h.interface,length=1),sequence=1,result=LIMIT)
        # Local exhaustion does not fabricate cancellation. Explicit component
        # cancellation requests do not mark adapter cancellation expected; the
        # settled ABORTED notification may therefore fence the adapter. It still
        # cannot dispatch a callback or advance protocol/output while blocked.
        quiet = h.forward_state()
        assert h.udc[44] == 0x010100
        h.step(42,old); h.step(63,bulk)
        h.step(43,old,1); h.step(64,bulk,1)
        assert not h.slot(1)[0] and not h.udc[2]
        assert not any(h.row[i] for i in (26,28,30))
        assert h.udc[44] == 0x020200 and h.forward_state() == quiet
        # Controller ownership was supplied as settled; adapter notifications
        # remain PENDING because no admitted reset allows service. No recovery
        # or complete adapter retirement is claimed at this terminal boundary.
        h.blocked()
        assert h.udc[44] == 0x020200 and h.forward_state() == quiet
        return
    if name.startswith('descriptor-fault/'):
        h.setup(base.packet(0x80,6,value=0x100,length=18))
        old = h.row[28]; h.wire(base.DEVICE,'retained-before-descriptor-fault')
        bulk = h.arm_write(document(['small'])[:31])
        if name.endswith('/in'):
            h.observe(old,0x48000000,fault=0x80,facts=0,result=FAULT)
        else:
            h.observe_bulk(bulk,0x48000000,fault=0x80,facts=0,result=FAULT)
        assert h.row[7] == h.row[36] == 1 and h.udc[3] == 1
        h.setup(base.packet(0x21,2,index=h.interface),service_result=base.WAIT)
        h.cancel_retained(); h.service(); h.step(10); h.finish_reset()
        h.fresh_page(document,images)
        return
    raise AssertionError('unimplemented composed profile: '+name)


def profiles():
    names = ('snapshot-replay','capture-wait-newer-retry','capture-facts','raw-admission','held-capture-blocks-reset-ack',
             'held-capture-blocks-publication','superseded-control',
             'soft-reset-held','bus-reset-retained-capture','reset-admission-wait',
             'terminal-drains-admitted-reset',
             'sequence-limit/capture','sequence-limit/reset','descriptor-fault/in','descriptor-fault/bulk')
    return [('protocol',fill,interface) for fill in (0,204) for interface in (0,3)]+[
        (name,fill,3) for fill in (0,204) for name in names]+raw_si_profiles()


def compile_host(temp, effective):
    src = ROOT / 'open-firmware/udc-composed-test'
    ep0 = ROOT / 'open-firmware/udc-ep0'
    out = ROOT / 'open-firmware/udc-out'
    setup = ROOT / 'open-firmware/udc-setup'
    implementation = [src/'fixture.c', src/'host-check.c', ep0/'hp1020_udc_ep0.c',
        out/'hp1020_udc_out.c', setup/'hp1020_udc_setup.c',
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
    include = ['-I'+str(p) for p in (src, ep0, out, setup, ROOT/'open-firmware',
        base.SRC, base.ADAPTER, base.PROTOCOL, base.PRINTER, base.RX, base.IMG, base.SEM,
        core.VENDOR/'libjbig', effective/'src')]
    core.command(flags+include+implementation+['-o', temp/'host'])
    full = ROOT/'vendor/foo2zjs-source'
    core.command(flags+['-I'+str(full), base.IMG/'reference.c', full/'jbig.c', full/'jbig_ar.c',
        '-o', temp/'reference'])


def sources(temp):
    tested = ep0.sources(temp)
    other = bulk_reference.sources(temp)
    assert all(tested[n] == digest for n,digest in other.items() if n in tested)
    tested.update(other)
    selected = set(SRC.glob('*.[ch]')) | set(SRC.glob('*.ld')) | set(SETUP.glob('*.[ch]'))
    selected.update(ROOT/'scripts'/name for name in (
        'validate-hp1020-udc-composed.py', 'build-hp1020-udc-composed-target.sh'))
    selected.update(setup_reference_source_paths(ROOT))
    for path in sorted(selected):
        name = str(path.relative_to(ROOT))
        tested[name] = core.sha(path.read_bytes())
        destination = temp/'source'/name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
    (temp/'source-sha256.json').write_text(json.dumps(tested, indent=2)+'\n')
    return tested


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', action='store_true')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix='hp1020-udc-composed-', dir='/tmp'))
    print('Composed UDC captures: '+str(temp), flush=True)
    tested = sources(temp)
    evidence = dict(setup=setup_original_reference(ROOT, core.sha),
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
            raw_si_oracles = scenario(h,name,document,images) or []
            captures = h.finish()
        finally:
            h.abort()
        assert len(h.events) == len(h.rows) == len(h.ep0_rows) == len(h.out_rows) == len(h.setup_rows)
        cases.append(dict(case=title, scenario=name, fill=fill, capacity=64, interface=interface,
            status='pass', initial=h.initial, initial_ep0=h.ep0_initial,
            initial_bulk=h.out_initial, initial_setup=h.setup_initial,
            steps=h.rows, ep0_steps=h.ep0_rows, bulk_steps=h.out_rows, setup_steps=h.setup_rows,
            events=h.events, packet_oracles=h.packets, descriptor_oracles=h.descriptor_oracles,
            bulk_descriptor_oracles=h.bulk_oracles, setup_oracles=h.ingress_oracles, raw_si_oracles=raw_si_oracles,
            expected_documents=h.expected_documents, expected_pixels_sha256=core.sha(h.expected_pixels),
            pixels_bytes=len(h.expected_pixels), capture_sha256={n:core.sha(raw) for n,raw in captures.items()}))
        replay.append((h,captures,directory))
        print(f'Composed UDC: {len(cases)}/{len(matrix)} host cases passed', flush=True)
    unchanged()
    target = None
    if args.target:
        core.command(['bash', ROOT/'scripts/build-hp1020-udc-composed-target.sh'])
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
                                  ('hp1020_composed_out_stats',48),('hp1020_composed_setup_stats',40)):
                result.append(list(struct.unpack('>'+str(length)+'I',q.read(program.symbols[symbol],length*4))))
            return result

        with QemuRAM() as q:
            version = q.version
            for case,(h,captures,directory) in zip(cases,replay):
                q.load(elf)
                assert q.call0(program.symbols['hp1020_bulk_fixture_reset'],[case['fill'],64,case['interface'],0xffffffff]) == 0
                initial,e,b,s = rows(q)
                assert initial[:59]+initial[60:] == h.initial[:59]+h.initial[60:]
                assert (e,b,s) == (h.ep0_initial,h.out_initial,h.setup_initial)
                for index,(event,host_row,host_ep0,host_bulk,host_setup) in enumerate(zip(
                        h.events,h.rows,h.ep0_rows,h.out_rows,h.setup_rows)):
                    data = bytes.fromhex(event['data_hex'])
                    if data:
                        q.put(program.symbols['hp1020_bulk_fixture_input'],data)
                    result = q.call0(program.symbols['hp1020_bulk_fixture_step'],event['words'])
                    row,e,b,s = rows(q)
                    with (directory/'target-steps.jsonl').open('a') as output:
                        output.write(json.dumps(row+e+b+s)+'\n')
                    assert result == row[0] == event['result'] and row[15:17] == [0,1]
                    assert e[2:5] == [0,1,1] and b[7:10] == [0,1,1] and s[12:15] == [0,1,3]
                    assert row[:59]+row[60:] == host_row[:59]+host_row[60:], (case['case'],index,row,host_row)
                    assert (e,b,s) == (host_ep0,host_bulk,host_setup), (case['case'],index,e,b,s)
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
                    adapter_state_and_memory_bytes=row[59],component_and_allocation_bytes=sizes,
                    capture_sha256={n:core.sha(raw) for n,raw in observed.items()}))
                print(f'Composed UDC: {len(native)}/{len(cases)} target cases passed',flush=True)
        assert all(core.sha((saved/n).read_bytes()) == digest for n,digest in artifacts.items()), 'captured target changed'
        target = dict(status='pass',cases=native,qemu_version=version,elf_sha256=core.sha(elf.read_bytes()),
                      audit=audit,captured_artifact_sha256=artifacts)
    unchanged()
    report = dict(status='pass',source_sha256=tested,fixture_sha256=fixture_hashes,effective_source=effective,
        original_reference=evidence,cases=cases,target=target,completed_native_page_lifecycles=0,
        usb_transfers=0,actual_peripheral_accesses=0,controller_quiescence_established=False,
        scope='Immutable SETUP records plus exact-cookie EP0 and bulk OUT descriptors through actual TinyUSB, class/receive/JBIG output in synthetic RAM with independent wire, descriptor, pixel and document oracles.',
        limits='No physical DCD, MMIO, IRQ, cache, boot, USB traffic or printing. CPU/DMA mapping, event sequencing, packet64/BE mode, visibility, hardware stall clearing and controller settlement remain supplied. IN actual length is separately supplied, never inferred from descriptor low16. Terminal sequence exhaustion settles controller ownership only; adapter notifications can remain pending and are not completed recovery. Copies remain metadata and output is synchronous.')
    name = 'validation' if args.target else 'host-validation'
    raw = json.dumps(report,sort_keys=True,separators=(',',':'))+'\n'
    (temp/(name+'.json')).write_text(raw)
    (OUT/(name+'.json')).write_text(raw)
    (OUT/(name+'.md')).write_text('# Composed USB descriptor execution\n\n'+report['scope']+'\n\n'+
        f'{len(cases)} host; {len(target["cases"]) if target else 0} QEMU cases. Every retained snapshot, original cookie, exact packet proposal, pixel, document event and guarded allocation is compared.\n\n'+report['limits']+'\n')


if __name__ == '__main__':
    main()
