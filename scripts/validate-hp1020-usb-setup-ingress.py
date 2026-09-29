#!/usr/bin/env python3
"""Original SETUP descriptor admission and byte conversion, before dispatch.

A fresh original USB2Thread ENTRY is followed by an explicit PC cut. One
peripheral-address literal is redirected to a guarded RAM pointer word. The
supplied record status is not an observed USB/DMA completion. Neither request
dispatch, descriptor return, IRQ acknowledgement nor peripheral access runs.
"""
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from types import SimpleNamespace

from hp1020_xtensa_call0 import Program, Machine, STOP, STACK, STACK_SIZE
from hp1020_xtensa_properties import properties, section_bytes
from hp1020_stock_stop import StopRAM
from hp1020_qemu_multitask import NativeTasks
from hp1020_qemu_ram import QemuRAM, RETURN, STACK_TOP


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'analysis/usb-path/setup-ingress'
REF = ROOT / 'analysis/usb-path/controller-reference/linux-v6.12'
TINYUSB = ROOT / 'vendor/tinyusb-0.21.0'
STOCK_SHA = '2111560068db47ceca21fa550db4c7c34f5595b5a5d137ae4a19631e40e3601d'
UPSTREAM_COMMIT = 'adc218676eef25575469234709c2d87185ca223a'
REFERENCE_SHA = {
    'amd5536udc.h': '8dbf2ebffe7de042bdfea1c5e4e0d7e7ca334cb821fbfaa1cf9ccfeeae302648',
    'snps_udc_core.c': 'c1b09e8f69d3340f2afd3a033d77a42775b52716d45b1aceb211dcaab89127bf',
}
DCD_SHA = 'baf785f2d5d8e3f74bd6d6a04559fc606d341983aad35aa08e168b452c2750db'
ENTRY, START = 0x10008ff0, 0x1000935b
ACCEPT, OTHER_DESCRIPTOR = 0x1000941d, 0x10009890
CODE = [(ENTRY, ENTRY + 3), (START, ACCEPT)]
CODE_SHA = {
    (ENTRY, ENTRY + 3): 'abf2a2b8451f111b81b36ce18b7df8a89436112a69aaa87faeafea9fd7f5e989',
    (START, ACCEPT): 'e63fe132beeff99b0602625ec3f3d4a5f8fe3c5c048c0d2a5ceb65d8c5f175aa',
}
# These IRQ bytes are audited only. They never enter the execution allowlist.
WAKE_SHA = {
    (0x100083e3, 0x100084b7): '3a3e8e4be62e9b625b63ccbcac4f82a9e288147dd61b3f9f28b1338daf7f2505',
    (0x100084b7, 0x100084d7): '82f40be2914d95b4032e32b342fa144c3c228305be432d41635523bcaf209823',
    (0x100086b0, 0x100086c3): 'f9216a6249f033584294afcb67e72820e8c0ab45303465ac346960c57f2d545c',
}
ARENA, ARENA_SIZE = 0x22700000, 0x1000
POINTER_WORD, STATUS_RECORD, OTHER_RECORD = ARENA + 0x100, ARENA + 0x200, ARENA + 0x300
POINTER_LITERAL, SUBPTR, DESPTR = 0x10005ef4, 0xb3000210, 0xb3000214
SETUP_GLOBAL = 0x1001bbc0
INITIAL_SP, FRAME_SP = STACK_TOP - 0x100, STACK_TOP - 0x100 - 128
EMPTY_FIXTURE = SimpleNamespace(path=None, execute_ranges=[])
EXCLUDED = (ENTRY + 3, 0x100091b0, 0x100091c7, 0x10009347, 0x10009358,
            ACCEPT, 0x10009884, OTHER_DESCRIPTOR, 0x10009896,
            0x10008208, 0x100084b4, 0x100086c0, 0x100086f4, 0x10008c24)
LITERALS = {
    0x10005de8: 0xb3000414, 0x10005e00: 0xb3000418,
    0x10005e04: 0xb3000004, 0x10005e08: 0xb3000204,
    0x10005e18: 0x10021318, 0x10005e30: 0xc0000000,
    0x10005e34: 0x80000000, 0x10005ee8: SETUP_GLOBAL,
    0x10005eec: 0x1001bc60, 0x10005ef0: 0x1001bc68,
    POINTER_LITERAL: SUBPTR, 0x10005ef8: DESPTR,
    0x10005f20: 0x10000, 0x10005f24: 0x30000000, 0x10005f80: 0xa100,
    SETUP_GLOBAL: 0x90021340, 0x1001bc48: 0x90021370,
    0x1001bc58: 0x900226f0, 0x1001bc60: 0x90022bc0,
    0x1001bc68: 0x90021360,
}
ANCHORS = {
    ENTRY: ('entry', (1, 128), '6c1010'),
    START: ('l32r', (8, POINTER_LITERAL), '18f2e6'),
    0x10009361: ('l32i.n', (11, 8, 0), '8b80'),
    0x10009363: ('l8ui', (10, 11, 0), '2ab000'),
    0x10009366: ('l8ui', (9, 11, 1), '29b001'),
    0x10009369: ('slli', (10, 10, 24), '08aa10'),
    0x1000936c: ('slli', (9, 9, 16), '009911'),
    0x1000936f: ('l8ui', (8, 11, 2), '28b002'),
    0x10009375: ('slli', (8, 8, 8), '088811'),
    0x10009378: ('l8ui', (10, 11, 3), '2ab003'),
    0x10009381: ('l32r', (8, 0x10005e30), '18f2ab'),
    0x10009384: ('l32r', (9, 0x10005e34), '19f2ac'),
    0x10009387: ('and', (8, 10, 8), '08a801'),
    0x1000938a: ('beq', (8, 9, 0x10009390), '798102'),
    0x1000938d: ('j', (OTHER_DESCRIPTOR,), '6004ff'),
    0x10009390: ('l32r', (8, 0x10005f24), '18f2e5'),
    0x10009393: ('bnone', (10, 8, 0x10009399), '78a002'),
    0x10009396: ('j', (OTHER_DESCRIPTOR,), '6004f6'),
    0x10009399: ('l32r', (8, 0x10005ee8), '18f2d3'),
    0x1000939c: ('l32i', (12, 8, 0), '2c8200'),
    0x1000939f: ('addi', (4, 12, 8), '24cc08'),
    0x100093a2: ('l8ui', (10, 4, 6), '2a4006'),
    0x100093bd: ('extui', (10, 10, 0, 16), '0a0a4f'),
    0x100093c6: ('s8i', (8, 4, 6), '284406'),
    0x100093d5: ('s8i', (10, 4, 7), '2a4407'),
    0x100093d8: ('l8ui', (10, 4, 4), '2a4004'),
    0x100093f3: ('extui', (10, 10, 0, 16), '0a0a4f'),
    0x100093fc: ('s8i', (8, 4, 4), '284404'),
    0x1000940b: ('s8i', (10, 4, 5), '2a4405'),
    0x1000940e: ('l8ui', (8, 12, 8), '28c008'),
    0x10009414: ('l8ui', (9, 4, 1), '294001'),
    0x10009417: ('slli', (8, 8, 8), '088811'),
    0x1000941a: ('or', (9, 8, 9), '098902'),
    ACCEPT: ('bne', (9, 10, 0x10009423), '7a9902'),
    # Initialization and next-descriptor anchors are inspected, not executed.
    0x10009123: ('l32r', (11, 0x10005ee8), '1bf371'),
    0x1000912b: ('l32i.n', (8, 11, 0), '88b0'),
    0x10009132: ('s32i.n', (7, 8, 0), '9780'),
    0x10009134: ('s32i.n', (7, 8, 4), '9781'),
    0x10009139: ('l32r', (12, 0x10005eec), '1cf36c'),
    0x100091a5: ('l32r', (9, POINTER_LITERAL), '19f353'),
    0x100091a8: ('l32i.n', (8, 11, 0), '88b0'),
    0x100091b0: ('s32i.n', (8, 9, 0), '9890'),
    0x100091bc: ('l32r', (11, 0x10005ef8), '1bf34f'),
    0x100091bf: ('l32i.n', (8, 12, 0), '88c0'),
    0x100091c7: ('s32i.n', (8, 11, 0), '98b0'),
    0x10009358: ('call8', (0x10017d28,), '583a73'),
    OTHER_DESCRIPTOR: ('l32r', (8, 0x10005ef8), '18f19a'),
    0x10009896: ('l32i.n', (11, 8, 0), '8b80'),
    # IRQ wake hints must not be translated one-for-one into completions.
    0x1000839b: ('s32i.n', (14, 9, 0), '9e90'),
    0x100083eb: ('l32i.n', (6, 7, 0), '8670'),
    0x100083f6: ('s32i.n', (8, 7, 0), '9870'),
    0x10008401: ('s32i', (8, 7, 0), '287600'),
    0x1000840c: ('s32i.n', (8, 7, 0), '9870'),
    0x10008443: ('s32i', (8, 7, 0), '287600'),
    0x10008449: ('bnone', (6, 8, 0x100084b7), '78606a'),
    0x1000844f: ('s32i.n', (8, 7, 0), '9870'),
    0x10008459: ('bnei', (7, 2, 0x100084a9), '69724c'),
    0x100084a9: ('l32r', (10, 0x10005e18), '1af65b'),
    0x100084ac: ('mov.n', (11, 7), 'db70'),
    0x100084ae: ('movi', (12, 0), '2c0a00'),
    0x100084b4: ('call8', (0x10017dac,), '583e3d'),
    0x100084b7: ('beqi', (3, 1, 0x100084bd), '683102'),
    0x100084ba: ('j', (0x100086c3,), '600205'),
    0x100084c8: ('beqi', (5, 1, 0x100084ce), '685102'),
    0x100084cb: ('j', (0x100086b0,), '6001e1'),
    0x100084d4: ('beqz', (8, 0x100086b0), '6481d8'),
    0x100086b0: ('l32r', (10, 0x10005e18), '1af5da'),
    0x100086b3: ('add.n', (11, 4, 5), 'a54b'),
    0x100086b5: ('ssl', (11,), '00b104'),
    0x100086b8: ('sll', (11, 2), '002b1a'),
    0x100086bb: ('movi.n', (12, 0), 'c0c0'),
    0x100086c0: ('call8', (0x10017dac,), '583dba'),
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def source_paths():
    pending, found = [Path(__file__).resolve()], set()
    while pending:
        path = pending.pop()
        if path in found:
            continue
        found.add(path)
        for node in ast.walk(ast.parse(path.read_text())):
            names = [item.name for item in node.names] if isinstance(node, ast.Import) else (
                [node.module] if isinstance(node, ast.ImportFrom) and node.module else [])
            for name in names:
                candidate = ROOT / 'scripts' / (name.split('.')[0] + '.py')
                if candidate.is_file() and candidate not in found:
                    pending.append(candidate)
    found.update([ROOT / 'analysis/sihp1020.elf', REF / 'provenance.json',
                  *(REF / name for name in REFERENCE_SHA),
                  TINYUSB / 'src/device/dcd.h', TINYUSB / 'PROVENANCE.json'])
    return sorted(found)


def cut_registers(fill):
    return [(0x5aa55aa5 ^ (fill * 0x01010101) ^ (index * 0x01020304)) & 0xffffffff
            for index in range(2, 16)]


def cut_record(fill):
    return dict(after=hex(ENTRY), resume=hex(START), stack_pointer=hex(FRAME_SP),
                supplied_a2_to_a15=[hex(value) for value in cut_registers(fill)])


def admitted(case):
    return case['owner'] == 2 and case['rx'] == 0


def wire_fields(packet):
    assert len(packet) == 8
    return dict(bmRequestType=packet[0], bRequest=packet[1],
                wValue=int.from_bytes(packet[2:4], 'little'),
                wIndex=int.from_bytes(packet[4:6], 'little'),
                wLength=int.from_bytes(packet[6:8], 'little'))


class SetupRAM(StopRAM):
    def __init__(self, program, case):
        super().__init__(program, ENTRY, CODE.copy(), [(ARENA, ARENA_SIZE)])
        self.case, self.cuts, self.stopped_at = case, [], None
        self.registers[1] = INITIAL_SP
        self.put(STACK, bytes([case['fill']]) * STACK_SIZE)
        self.put(ARENA, bytes([case['fill']]) * ARENA_SIZE)
        packet = bytes.fromhex(case['wire_hex'])
        other = bytes(value ^ 0xff for value in packet)
        self.write(STATUS_RECORD, 4, (case['owner'] << 30) | (case['rx'] << 28) | case['low_bits'])
        self.write(STATUS_RECORD + 4, 4, 0x5a1b2c3d)
        self.put(STATUS_RECORD + 8, other if case['separate_pointer'] else packet)
        self.write(OTHER_RECORD, 4, case['other_header'])
        self.write(OTHER_RECORD + 4, 4, 0xe5d4c3b2)
        self.put(OTHER_RECORD + 8, packet if case['separate_pointer'] else other)
        self.packet_record = OTHER_RECORD if case['separate_pointer'] else STATUS_RECORD
        self.write(POINTER_WORD, 4, DESPTR if case.get('bad_status_pointer') else STATUS_RECORD)
        self.write(SETUP_GLOBAL, 4, 0xb3000000 if case.get('bad_packet_pointer') else self.packet_record)
        assert self.read(POINTER_LITERAL, 4) == SUBPTR
        if not case.get('unredirected'):
            self.write_ranges.append((POINTER_LITERAL, POINTER_LITERAL + 4))
            self.write(POINTER_LITERAL, 4, POINTER_WORD)

    def after_instruction(self, pc, nxt):
        nxt = super().after_instruction(pc, nxt)
        if pc == ENTRY:
            assert self.registers[1] == FRAME_SP
            self.registers[2:] = cut_registers(self.case['fill'])
            self.cuts.append(cut_record(self.case['fill']))
            return START
        if nxt in (ACCEPT, OTHER_DESCRIPTOR):
            self.stopped_at = nxt
            return STOP
        return nxt


def snapshot(state):
    return {(a, b): state.bytes_at(a, b - a) for a, b in state.write_ranges
            if not (STACK <= a and b <= STACK + STACK_SIZE)}


def memory_manifest(memory):
    return [dict(begin=hex(a), end=hex(b), sha256=sha(data))
            for (a, b), data in sorted(memory.items())]


def expected_memory(before, case):
    """Independent eight-byte transformation; no executed state is consulted."""
    expected = {bounds: bytearray(data) for bounds, data in before.items()}
    if admitted(case) and 'reject_pc' not in case:
        packet = bytes.fromhex(case['wire_hex'])
        transformed = packet[:4] + packet[4:6][::-1] + packet[6:8][::-1]
        at = (OTHER_RECORD if case['separate_pointer'] else STATUS_RECORD) + 8
        matches = [(a, b) for a, b in expected if a <= at and at + 8 <= b]
        assert len(matches) == 1
        a, b = matches[0]
        expected[(a, b)][at - a:at - a + 8] = transformed
    return {bounds: bytes(data) for bounds, data in expected.items()}


def begin_qemu(q, state):
    q.load(state.program.path)
    runner = NativeTasks(q, state, EMPTY_FIXTURE, CODE, (), instruction_budget=200)
    runner.synchronize(True)
    q.put(INITIAL_SP - 12, (INITIAL_SP + 64).to_bytes(4, 'big'))
    q.put(RETURN - 3, bytes.fromhex('0b8000'))
    q.reset_cpu(RETURN - 3)
    q.set_reg(2, INITIAL_SP)
    q.set_reg(42, 0x40000)
    q.set_reg(111, 0x10000000)
    q.set_reg(9, ENTRY)
    return runner


def execute(program, q, case, capture):
    state = SetupRAM(program, case)
    before = snapshot(state)
    expected = expected_memory(before, case)
    engine = 'interpreter' if q is None else 'qemu'
    stem = capture / f'{case["name"]}-{engine}'
    stem.with_suffix('.input.json').write_text(json.dumps(case, indent=2) + '\n')
    for suffix, data in (('before', before), ('expected', expected)):
        stem.with_suffix(f'.{suffix}.bin').write_bytes(b''.join(value for _, value in sorted(data.items())))
    runner, failure, cuts, stop = None, None, [], None
    try:
        if q is None:
            state.run(budget=200)
            stop = state.stopped_at
        else:
            runner = begin_qemu(q, state)
            while q.reg(0) not in (ACCEPT, OTHER_DESCRIPTOR):
                if q.reg(0) == ENTRY + 3:
                    assert not cuts and ENTRY in runner.visited
                    wb = q.reg(38)
                    assert q.reg(((wb * 4 + 1) % 32) + 1) == FRAME_SP
                    for index, value in enumerate(cut_registers(case['fill']), 2):
                        q.set_reg(((wb * 4 + index) % 32) + 1, value)
                    cuts.append(cut_record(case['fill']))
                    q.set_reg(0, START)
                    continue
                runner.step()
            stop = q.reg(0)
    except Exception as error:
        failure = dict(type=type(error).__name__, reason=str(error), pc=hex(state.pc))
    finally:
        if runner is not None:
            runner.synchronize(False)
    if q is None:
        registers = state.registers.copy()
        cuts, visited, steps = state.cuts, state.visited.copy(), state.steps
    else:
        wb = q.reg(38)
        registers = [q.reg(((wb * 4 + index) % 32) + 1) for index in range(16)]
        visited, steps = runner.visited.copy(), runner.steps
    actual = snapshot(state)
    selected = sorted(visited - {RETURN - 3, case.get('reject_pc')})
    result = dict(status='captured_unchecked', case=case, failure=failure,
                  stop_before=None if stop is None else hex(stop), explicit_cuts=cuts,
                  descriptor_status_passes_oracle=admitted(case),
                  raw_wire_fields=wire_fields(bytes.fromhex(case['wire_hex'])),
                  status_record_after=state.bytes_at(STATUS_RECORD, 16).hex(),
                  other_record_after=state.bytes_at(OTHER_RECORD, 16).hex(),
                  register_a1_to_a15=[hex(value) for value in registers[1:]],
                  before_memory=memory_manifest(before), expected_memory=memory_manifest(expected),
                  nonstack_memory=memory_manifest(actual),
                  original_instructions_visited=[hex(pc) for pc in selected], steps=steps)
    stem.with_suffix('.after.bin').write_bytes(b''.join(value for _, value in sorted(actual.items())))
    stem.with_suffix('.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    assert cuts == [cut_record(case['fill'])] and registers[1] == FRAME_SP
    assert {ENTRY, START} <= visited and not (set(EXCLUDED) & visited)
    assert actual == expected, (case['name'], engine, 'unexpected nonstack RAM change')
    if 'reject_pc' in case:
        assert failure == dict(type='ValueError', reason='MMIO forbidden', pc=hex(case['reject_pc'])), result
        assert stop is None
        if q is not None:
            assert q.reg(0) == case['reject_pc'] and case['reject_pc'] not in visited
        else:
            assert state.pc == case['reject_pc']
    else:
        assert failure is None, result
        assert stop == (ACCEPT if admitted(case) else OTHER_DESCRIPTOR)
        if admitted(case):
            packet = bytes.fromhex(case['wire_hex'])
            assert registers[4] == state.packet_record + 8 and registers[12] == state.packet_record
            assert registers[9] == (packet[0] << 8) | packet[1]
            assert {0x100093c6, 0x100093d5, 0x100093fc, 0x1000940b} <= visited
        else:
            assert not ({0x10009399, 0x100093a2, 0x100093c6, 0x100093fc} & visited)
    for (a, b), digest in CODE_SHA.items():
        raw = state.bytes_at(a, b - a)
        assert sha(raw) == digest
        if q is not None:
            assert q.read(a, b - a) == raw
    assert runner is None or not runner.services
    result.update(status='pass', exact_nonstack_memory_equal=True,
                  original_code_unchanged=True, actual_peripheral_accesses=0)
    stem.with_suffix('.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    return result


def base_case(name, fill, owner=2, rx=0, packet='a10034127856bc9a'):
    return dict(name=name, fill=fill, owner=owner, rx=rx, low_bits=0x0fffffff if fill else 0,
                wire_hex=packet, separate_pointer=False, other_header=0xffffffff,
                kind='same_setup_descriptor_and_packet_record')


def cases():
    for fill in (0, 204):
        for owner in range(4):
            for rx in range(4):
                for name, packet in (('device-descriptor', '8006000100001200'),
                                     ('asymmetric-fields', 'a10034127856bc9a')):
                    yield base_case(f'{name}-owner{owner}-rx{rx}-fill{fill}', fill, owner, rx, packet)
        # The original takes status through SUBPTR but fields through a global.
        # These deliberately inconsistent pointers expose that precondition;
        # they are not claimed reachable controller states or safe port policy.
        for owner, rx, header in ((2, 0, 0xffffffff), (1, 0, 0x80000000), (2, 1, 0x80000000)):
            case = base_case(f'separate-records-owner{owner}-rx{rx}-fill{fill}', fill, owner, rx)
            case.update(separate_pointer=True, other_header=header,
                        kind='conditional_independent_status_and_packet_pointers')
            yield case


def rejection_cases():
    for fill in (0, 204):
        for name, flag, pc, address in (
                ('unredirected-subptr', 'unredirected', 0x10009361, SUBPTR),
                ('peripheral-status-pointer', 'bad_status_pointer', 0x10009363, DESPTR),
                ('peripheral-packet-pointer', 'bad_packet_pointer', 0x100093a2, 0xb300000e)):
            case = base_case(f'{name}-fill{fill}', fill)
            case.update({flag: True, 'reject_pc': pc, 'reject_address': hex(address),
                         'kind': 'guard_rejection_before_peripheral_access'})
            yield case


def compare(a, b, name):
    for key in ('failure', 'stop_before', 'explicit_cuts', 'descriptor_status_passes_oracle',
                'raw_wire_fields', 'status_record_after', 'other_record_after',
                'register_a1_to_a15', 'before_memory', 'expected_memory',
                'nonstack_memory', 'original_instructions_visited'):
        assert a[key] == b[key], (name, key)


def reject_excluded_code(program, q):
    state = SetupRAM(program, base_case('excluded-code', 204))
    before = snapshot(state)
    runner = begin_qemu(q, state)
    rows = []
    for pc in EXCLUDED:
        state.pc, state.steps, state.visited = pc, 0, set()
        try:
            state.run(budget=1)
        except ValueError as error:
            assert str(error) == f'execution outside selected stock routines: {pc:#x}'
        else:
            raise AssertionError(f'excluded interpreter instruction executed: {pc:#x}')
        assert state.steps == 0 and not state.visited
        q.set_reg(0, pc)
        steps, visited = runner.steps, runner.visited.copy()
        try:
            runner.step()
        except ValueError as error:
            assert str(error) == f'native tasks left selected code: {pc:#x}'
        else:
            raise AssertionError(f'excluded QEMU instruction executed: {pc:#x}')
        assert runner.steps == steps and runner.visited == visited and q.reg(0) == pc
        rows.append(dict(pc=hex(pc), status='rejected before execution in both engines'))
    runner.synchronize(False)
    assert snapshot(state) == before
    return rows


def main():
    capture = Path(tempfile.mkdtemp(prefix='hp1020-usb-setup-ingress-', dir='/tmp'))
    print(f'USB SETUP ingress captures: {capture}', flush=True)
    sources = {str(path.relative_to(ROOT)): sha(path.read_bytes()) for path in source_paths()}
    for name in sources:
        saved = capture / 'source' / name
        saved.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, saved)
    (capture / 'source-sha256.json').write_text(json.dumps(sources, indent=2) + '\n')
    stock = ROOT / 'analysis/sihp1020.elf'
    blob = stock.read_bytes()
    assert sha(blob) == STOCK_SHA
    sections, _ = properties(blob)
    audited, static_ranges = [], []
    for selected, collection in ((CODE_SHA, audited), (WAKE_SHA, static_ranges)):
        for (begin, end), digest in selected.items():
            raw = section_bytes(blob, sections, begin, end - begin)
            assert sha(raw) == digest
            collection.append(dict(begin=hex(begin), end=hex(end), bytes=raw.hex(), sha256=digest))
    for name, digest in REFERENCE_SHA.items():
        assert sha((REF / name).read_bytes()) == digest
    assert json.loads((REF / 'provenance.json').read_text())['commit'] == UPSTREAM_COMMIT
    assert sha((TINYUSB / 'src/device/dcd.h').read_bytes()) == DCD_SHA
    assert json.loads((TINYUSB / 'PROVENANCE.json').read_text())['commit'] == 'dae3f9a366bfcddbf9dcf1b48d7500286a849539'
    definitions = {name: int(value, 0) for name, value in re.findall(
        r'^#define\s+(UDC_\w+)\s+(0x[0-9a-fA-F]+|[0-9]+)\s*(?:/\*.*)?$',
        (REF / 'amd5536udc.h').read_text(), re.M)}
    for name, value in (('UDC_DMA_STP_STS_BS_MASK', 0xc0000000),
                        ('UDC_DMA_STP_STS_BS_DMA_DONE', 2), ('UDC_DMA_STP_STS_RX_MASK', 0x30000000),
                        ('UDC_EP_SUBPTR_ADDR', 0x10), ('UDC_EP_DESPTR_ADDR', 0x14),
                        ('UDC_EPINT_IN_EP0', 0), ('UDC_EPINT_IN_EP1', 1),
                        ('UDC_EPINT_OUT_EP0', 16), ('UDC_EPINT_OUT_EP1', 17)):
        assert definitions[name] == value
    prefix = os.environ.get('XTENSA_PREFIX', '/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf')
    program = Program(stock, prefix)
    original = Machine(program)
    for at, value in LITERALS.items():
        assert original.read(at, 4) == value, hex(at)
    for pc, (op, args, encoded) in ANCHORS.items():
        raw = bytes.fromhex(encoded)
        assert program.instruction(pc) == (op, args, raw), hex(pc)
        assert section_bytes(blob, sections, pc, len(raw)) == raw
    results, rejected = [], []
    with QemuRAM() as q:
        version = q.version
        for supplied, collection in ((cases(), results), (rejection_cases(), rejected)):
            for case in supplied:
                interpreted = execute(program, None, case, capture)
                native = execute(program, q, case, capture)
                compare(interpreted, native, case['name'])
                collection.append(dict(case=case, interpreter=interpreted, qemu=native))
        excluded = reject_excluded_code(program, q)
    assert len(results) == 70 and len(rejected) == 6
    assert sha(stock.read_bytes()) == STOCK_SHA
    assert all(sha((ROOT / name).read_bytes()) == digest for name, digest in sources.items())
    report = dict(status='pass', cases=results, peripheral_rejection_controls=rejected,
                  excluded_code_controls=excluded, source_sha256=sources,
                  stock_elf_sha256=STOCK_SHA, qemu_version=version,
                  original_byte_ranges=audited, static_only_irq_byte_ranges=static_ranges,
                  instruction_anchors={hex(pc): dict(op=op, args=args, bytes=encoded,
                                       executed_region=any(a <= pc < b for a, b in CODE))
                                       for pc, (op, args, encoded) in ANCHORS.items()},
                  literal_anchors={hex(pc): hex(value) for pc, value in LITERALS.items()},
                  private_literal_redirect=dict(address=hex(POINTER_LITERAL), original=hex(SUBPTR),
                                                guarded_ram=hex(POINTER_WORD)),
                  original_entry=hex(ENTRY), explicit_cut_resume=hex(START),
                  stop_before=[hex(ACCEPT), hex(OTHER_DESCRIPTOR)], supplied_service_calls=[],
                  upstream_commit=UPSTREAM_COMMIT, actual_peripheral_accesses=0,
                  completed_usb_control_transfers=0, completed_native_page_lifecycles=0,
                  controller_quiescence_established=False,
                  scope='Under supplied stable record bytes, the original SETUP prefix admits owner 2 and RX status 0 only. It obtains the status pointer through OUT0 SUBPTR, then independently obtains the request pointer from global 0x1001bbc0 and adds 8. Only wIndex and wLength byte pairs are reversed in place; bmRequestType, bRequest and both wValue bytes are preserved. Every mutable nonstack byte is compared against an independent oracle.',
                  wire_contract='The eight supplied packet bytes are USB wire order. Initial stock global 0x1001bbc0 is 0x90021340, so its packet starts at 0x90021348. SUBPTR 0xb3000210 is distinct from ordinary OUT0 data/status DESPTR 0xb3000214. The latter initially points to 0x90022bc0; the bulk OUT descriptor global initially points to 0x90021370. These initializers and submission stores are static evidence only.',
                  tinyusb_requirement='Pass a retained copy of the original eight wire bytes to dcd_event_setup_received. Its pinned implementation converts wValue, wIndex and wLength itself; passing the stock post-conversion buffer would reverse wIndex/wLength twice on the big-endian target. Preserve descriptor/request identity and ownership until copying is safe. The mismatched-pointer controls demonstrate an original assumption, not a recommended adapter allowance.',
                  static_irq_caution='Audited but unexecuted IRQ bytes acknowledge the sampled EPINT word before lane status reads. A latched OUT TDC condition can call event-set at 0x100084b4 and again at 0x100086c0; a non-TDC OUT path can reach the latter call too. HE/BNA status clearing does not itself prevent these later wake paths. These are task wake hints, not one-to-one successful transfer completions or quiescence promises. Endpoint event bits are IN n / OUT 16+n; a DCD adapter must explicitly translate USB endpoint addresses into these bit positions.',
                  limits='Fresh original ENTRY is followed by an explicit cut omitting initialization and event wait. After ENTRY every a2..a15 register is independently poisoned; selected instructions define their own input pointers. Status/header bytes, packet bytes, pointer correspondence and stability are supplied. One original address literal is privately redirected to RAM; no peripheral is modeled. Primary cases cover all 4 owner and 4 RX values with two packets and two fills; six separate-pointer controls are deliberately inconsistent arithmetic states. No hardware SETUP arrival, IRQ execution, DMA byte order, cache coherency, concurrent overwrite, descriptor return, dispatch, status stage, reset, abort, physical status or printing is established. Reaching the admitted boundary does not mean the request is protocol-valid.')
    text = json.dumps(report, indent=2, sort_keys=True) + '\n'
    (capture / 'report.json').write_text(text)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.with_suffix('.json').write_text(text)
    OUT.with_suffix('.md').write_text('# Original USB SETUP ingress\n\n'
        + f'{len(results)} conditional cases agree in both engines; {len(rejected)} controls reject before peripheral access. Zero USB transfers or page lifecycles.\n\n'
        + report['scope'] + '\n\n' + report['wire_contract'] + '\n\n'
        + report['tinyusb_requirement'] + '\n\n' + report['static_irq_caution']
        + '\n\n' + report['limits'] + '\n')
    print(f'USB SETUP ingress: {len(results)} conditional cases, {len(rejected)} pre-MMIO rejections; no physical USB execution', flush=True)


if __name__ == '__main__':
    main()
