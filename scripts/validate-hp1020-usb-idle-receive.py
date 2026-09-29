#!/usr/bin/env python3
"""Observe the original idle receive service against ordinary guarded RAM.

The complete original helper runs from its real ENTRY to return. Only three
register-address literals are privately redirected. Interrupt-mask and delay
calls are supplied services; the latter may replace a RAM DEVCTL image at its
return boundary. That is an explicit input, not a controller, timing model or
demonstration of a reachable stock race. No DMA cancellation is acknowledged.
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
OUT = ROOT / 'analysis/usb-path/idle-receive'
REF = ROOT / 'analysis/usb-path/controller-reference/linux-v6.12'
STOCK_SHA = '2111560068db47ceca21fa550db4c7c34f5595b5a5d137ae4a19631e40e3601d'
UPSTREAM_COMMIT = 'adc218676eef25575469234709c2d87185ca223a'
REFERENCE_SHA = {
    'amd5536udc.h': '8dbf2ebffe7de042bdfea1c5e4e0d7e7ca334cb821fbfaa1cf9ccfeeae302648',
    'snps_udc_core.c': 'c1b09e8f69d3340f2afd3a033d77a42775b52716d45b1aceb211dcaab89127bf',
}
ENTRY, END = 0x10008f40, 0x10008fb0
MASK, UNMASK, DELAY = 0x100171b0, 0x10017184, 0x100116ec
HOST = {MASK, UNMASK, DELAY}
CODE = [(ENTRY, END)]
CODE_SHA = {(ENTRY, END): 'c082efa9296f8adf16e80d90e0baa362b7db747721d25ef2608bcd9249ced74a'}
# The caller loop is anchored but never admitted for execution.
CALLER_RANGE = (0x10009934, 0x1000993d)
CALLER_SHA = '2d258a320ad617249848987f908e0f8013ada5733d0fbce3ca4a4ae7d1dcbb5f'
ARENA, ARENA_SIZE = 0x22800000, 0x1000
DEVSTS, OUT1, DEVCTL = ARENA + 0x100, ARENA + 0x200, ARENA + 0x300
DESCRIPTORS, PAYLOAD = ARENA + 0x400, ARENA + 0x800
LATCH = 0x1001bc72
INITIAL_SP = STACK_TOP - 0x100
REDIRECTS = {
    0x10005e68: (0xb3000408, DEVSTS),
    0x10005e70: (0xb3000220, OUT1),
    0x10005ea8: (0xb3000404, DEVCTL),
}
TRACKED = {DEVSTS: 4, OUT1: 4, DEVCTL: 4, LATCH: 1}
EMPTY_FIXTURE = SimpleNamespace(path=None, execute_ranges=[])
EXCLUDED = (MASK, UNMASK, DELAY, DELAY + 3, 0x1001bb5c,
            0x10009934, 0x10009937, 0x1000993a, END, 0x10008ff0,
            0x10008208, 0x100086f4, 0x10008c24, 0x10009a10, 0x10009a70)
LITERALS = {
    **{at: pair[0] for at, pair in REDIRECTS.items()},
    0x10005e64: LATCH, 0x10005e6c: 0x8000, 0x10005ea4: 0x6000,
    0x10005e2c: 0x1001bc48, 0x10005f18: CALLER_RANGE[0],
}
ANCHORS = {
    ENTRY: ('entry', (1, 32), '6c1004'),
    0x10008f43: ('movi.n', (10, 4), 'c0a4'),
    0x10008f48: ('call8', (MASK,), '583899'),
    0x10008f4b: ('l32r', (12, 0x10005e68), '1cf3c7'),
    0x10008f4e: ('l32r', (8, 0x10005e6c), '18f3c7'),
    0x10008f54: ('l32i.n', (9, 12, 0), '89c0'),
    0x10008f56: ('bany', (9, 8, 0x10008fa5), '78984b'),
    0x10008f59: ('l32r', (11, 0x10005e64), '1bf3c2'),
    0x10008f5c: ('l8ui', (8, 11, 0), '28b000'),
    0x10008f5f: ('bnez', (8, 0x10008fa5), '658042'),
    0x10008f62: ('l32r', (10, 0x10005e70), '1af3c3'),
    0x10008f68: ('l32i.n', (8, 10, 0), '88a0'),
    0x10008f6a: ('movi', (9, 128), '290a80'),
    0x10008f6d: ('or', (8, 8, 9), '098802'),
    0x10008f73: ('s32i.n', (8, 10, 0), '98a0'),
    0x10008f75: ('movi.n', (9, 1), 'c091'),
    0x10008f7a: ('l32i.n', (10, 12, 0), '8ac0'),
    0x10008f7c: ('l32r', (8, 0x10005ea4), '18f3ca'),
    0x10008f7f: ('s8i', (9, 11, 0), '29b400'),
    0x10008f82: ('bnone', (10, 8, 0x10008f8a), '78a004'),
    0x10008f85: ('movi.n', (10, 50), 'c3a2'),
    0x10008f87: ('j', (0x10008f8d,), '600002'),
    0x10008f8a: ('movi', (10, 5), '2a0a05'),
    0x10008f90: ('call8', (DELAY,), '5821d6'),
    0x10008f93: ('l32r', (8, 0x10005ea8), '18f3c5'),
    0x10008f99: ('l32i.n', (9, 8, 0), '8980'),
    0x10008f9b: ('movi.n', (10, 4), 'c0a4'),
    0x10008f9d: ('or', (9, 9, 10), '0a9902'),
    0x10008fa3: ('s32i.n', (9, 8, 0), '9980'),
    0x10008fa5: ('movi.n', (10, 4), 'c0a4'),
    0x10008faa: ('call8', (UNMASK,), '583876'),
    0x10008fad: ('retw', (), '060000'),
    CALLER_RANGE[0]: ('entry', (1, 32), '6c1004'),
    0x10009937: ('call8', (ENTRY,), '5bfd82'),
    0x1000993a: ('j', (0x10009937,), '63fff9'),
    0x10009338: ('l32r', (12, 0x10005f18), '1cf2f8'),
    0x10009344: ('call8', (0x10018274,), '583bcb'),
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
                  *(REF / name for name in REFERENCE_SHA)])
    return sorted(found)


def event(pc, kind, address, value, size=None):
    row = dict(pc=hex(pc), kind=kind, address=hex(address), value=hex(value))
    if size is not None:
        row['size'] = size
    return row


class IdleRAM(StopRAM):
    def __init__(self, program, fill, skip_literal=None):
        self.recording, self.events, self.delay_devctl = False, [], None
        super().__init__(program, ENTRY, CODE.copy(), [(ARENA, ARENA_SIZE)])
        # Poison every mutable range, including both sides of the one-byte
        # latch. Immutable stock code and literals retain their original bytes.
        for begin, end in self.write_ranges:
            self.put(begin, bytes([fill]) * (end - begin))
        self.write(0x1001bc48, 4, DESCRIPTORS)
        for index in range(4):
            at = DESCRIPTORS + index * 16
            for offset, value in ((0, (index << 30) | 0x08000025),
                                  (4, 0xabc00000 | index),
                                  (8, PAYLOAD + index * 64), (12, 0)):
                self.write(at + offset, 4, value)
        self.put(PAYLOAD, bytes((fill + index * 31) & 255 for index in range(256)))
        self.write(OUT1 + 20, 4, DESCRIPTORS + 16)
        for literal, (original, redirected) in REDIRECTS.items():
            assert self.read(literal, 4) == original
            if literal != skip_literal:
                self.write_ranges.append((literal, literal + 4))
                self.write(literal, 4, redirected)

    def read(self, address, size):
        value = super().read(address, size)
        if self.recording and address in TRACKED:
            assert size == TRACKED[address]
            self.events.append(event(self.pc, 'read', address, value, size))
        return value

    def write(self, address, size, value):
        super().write(address, size, value)
        if self.recording and address in TRACKED:
            assert size == TRACKED[address]
            self.events.append(event(self.pc, 'write', address,
                                     value & ((1 << (size * 8)) - 1), size))

    def extension(self, op, args, nxt):
        if op == 'call8' and args[0] in HOST:
            target, argument = args[0], self.registers[10]
            if target == DELAY:
                assert self.pc == 0x10008f90 and argument in (5, 50)
                self.events.append(event(self.pc, 'supplied_delay', target, argument))
                if self.delay_devctl is not None:
                    # A supplied environmental change, not an original store
                    # or a claim that this interleaving occurs on the printer.
                    super().write(DEVCTL, 4, self.delay_devctl)
                    self.events.append(event(self.pc, 'supplied_delay_return_word',
                                             DEVCTL, self.delay_devctl, 4))
            else:
                assert (self.pc, target, argument) in (
                    (0x10008f48, MASK, 4), (0x10008faa, UNMASK, 4))
                self.events.append(event(self.pc, 'supplied_interrupt_service', target, argument))
            # These services have no other memory, interrupt or timing effects.
            self.registers[10] = 0
            self.branch_taken = True
            return nxt
        return super().extension(op, args, nxt)


def snapshot(state):
    return {(a, b): state.bytes_at(a, b - a) for a, b in state.write_ranges
            if not (STACK <= a and b <= STACK + STACK_SIZE)}


def memory_manifest(memory):
    return [dict(begin=hex(a), end=hex(b), sha256=sha(data))
            for (a, b), data in sorted(memory.items())]


def oracle(before, delay_devctl, stop_before=None):
    """Independent bit/byte contract using inputs only, not executed results."""
    expected = {bounds: bytearray(data) for bounds, data in before.items()}
    events = []

    class Boundary(Exception):
        pass

    def locate(at, size):
        matches = [(a, b) for a, b in expected if a <= at and at + size <= b]
        assert len(matches) == 1
        return matches[0]

    def read(pc, at, size=4):
        if pc == stop_before:
            raise Boundary
        begin, end = locate(at, size)
        value = int.from_bytes(expected[(begin, end)][at - begin:at - begin + size], 'big')
        events.append(event(pc, 'read', at, value, size))
        return value

    def write(pc, at, value, size=4, kind='write'):
        if pc == stop_before:
            raise Boundary
        begin, end = locate(at, size)
        expected[(begin, end)][at - begin:at - begin + size] = value.to_bytes(size, 'big')
        events.append(event(pc, kind, at, value, size))

    try:
        events.append(event(0x10008f48, 'supplied_interrupt_service', MASK, 4))
        status = read(0x10008f54, DEVSTS)
        if not status & 0x8000 and read(0x10008f5c, LATCH, 1) == 0:
            write(0x10008f73, OUT1, read(0x10008f68, OUT1) | 0x80)
            speed_status = read(0x10008f7a, DEVSTS)
            write(0x10008f7f, LATCH, 1, 1)
            delay = 50 if speed_status & 0x6000 else 5
            events.append(event(0x10008f90, 'supplied_delay', DELAY, delay))
            if delay_devctl is not None:
                write(0x10008f90, DEVCTL, delay_devctl, kind='supplied_delay_return_word')
            write(0x10008fa3, DEVCTL, read(0x10008f99, DEVCTL) | 4)
        events.append(event(0x10008faa, 'supplied_interrupt_service', UNMASK, 4))
    except Boundary:
        assert stop_before is not None
    else:
        assert stop_before is None, ('oracle missed rejection boundary', hex(stop_before))
    return {bounds: bytes(data) for bounds, data in expected.items()}, events


def begin_qemu(q, state):
    q.load(state.program.path)
    runner = NativeTasks(q, state, EMPTY_FIXTURE, CODE, HOST, instruction_budget=200)
    runner.synchronize(True)
    q.put(INITIAL_SP - 12, (INITIAL_SP + 64).to_bytes(4, 'big'))
    q.put(RETURN - 3, bytes.fromhex('0b8000'))
    q.reset_cpu(RETURN - 3)
    q.set_reg(2, INITIAL_SP)
    q.set_reg(42, 0x40000)
    q.set_reg(111, 0x10000000)
    q.set_reg(9, ENTRY)
    return runner


def observe_qemu(state, q):
    pc = q.reg(0)
    if not ENTRY <= pc < END:
        return
    op, args, _ = state.program.instruction(pc)
    base = op.removesuffix('.n')
    sizes = {'l8ui': 1, 's8i': 1, 'l32i': 4, 's32i': 4}
    if base not in sizes:
        return
    ar = lambda index: q.reg(((q.reg(38) * 4 + index) % 32) + 1)
    address, size = (ar(args[1]) + args[2]) & 0xffffffff, sizes[base]
    if address in TRACKED:
        assert size == TRACKED[address]
        state.span(address, size)
        value = (int.from_bytes(q.read(address, size), 'big') if base.startswith('l')
                 else ar(args[0]) & ((1 << (size * 8)) - 1))
        state.events.append(event(pc, 'read' if base.startswith('l') else 'write',
                                  address, value, size))


def execute_phase(state, q, name, capture, delay_devctl=None, rejection=None):
    engine = 'interpreter' if q is None else 'qemu'
    before = snapshot(state)
    expected, expected_events = oracle(before, delay_devctl, rejection)
    stem = capture / f'{name}-{engine}'
    stem.with_suffix('.before.bin').write_bytes(b''.join(data for _, data in sorted(before.items())))
    stem.with_suffix('.expected.bin').write_bytes(b''.join(data for _, data in sorted(expected.items())))
    state.pc, state.steps, state.visited, state.events = ENTRY, 0, set(), []
    state.registers = [0] * 16
    state.registers[0], state.registers[1] = STOP, INITIAL_SP
    state.frames, state.loop, state.sar = [], None, 0
    state.delay_devctl = delay_devctl
    failure, runner = None, None
    try:
        if q is None:
            state.recording = True
            state.run(budget=200)
        else:
            runner = begin_qemu(q, state)
            while q.reg(0) != RETURN:
                observe_qemu(state, q)
                runner.step()
            assert q.reg(38) == 0 and q.reg(39) == 1
            state.pc = STOP
    except Exception as error:
        failure = dict(type=type(error).__name__, reason=str(error), pc=hex(state.pc))
    finally:
        state.recording = False
        if runner is not None:
            runner.synchronize(False)
    actual = snapshot(state)
    stem.with_suffix('.after.bin').write_bytes(b''.join(data for _, data in sorted(actual.items())))
    visited = state.visited if q is None or runner is None else runner.visited
    selected = sorted(pc for pc in visited if ENTRY <= pc < END and pc != rejection)
    result = dict(status='captured_unchecked', entry=hex(ENTRY), failure=failure,
                  supplied_delay_return_devctl=None if delay_devctl is None else hex(delay_devctl),
                  trace=state.events, expected_trace=expected_events,
                  nonstack_memory=memory_manifest(actual),
                  before_memory=memory_manifest(before), expected_memory=memory_manifest(expected),
                  original_instructions_visited=[hex(pc) for pc in selected],
                  steps=state.steps if runner is None else runner.steps)
    stem.with_suffix('.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    if rejection is None:
        assert failure is None and state.pc == STOP, (name, engine, failure)
        assert ENTRY in selected and 0x10008fad in selected
    else:
        assert failure == dict(type='ValueError', reason='MMIO forbidden', pc=hex(rejection)), (
            name, engine, failure)
        if q is not None:
            assert q.reg(0) == rejection and rejection not in runner.visited
    assert actual == expected, (name, engine, 'nonstack memory differs')
    assert state.events == expected_events, (name, engine, 'command/access trace differs')
    assert not (set(EXCLUDED) & set(selected))
    for (begin, end), digest in CODE_SHA.items():
        code = state.bytes_at(begin, end - begin)
        assert sha(code) == digest
        if q is not None:
            assert q.read(begin, end - begin) == code
    if runner is not None:
        expected_services = [int(item['address'], 16) for item in expected_events
                             if item['kind'] in ('supplied_delay', 'supplied_interrupt_service')]
        assert runner.services == expected_services
    result.update(status='pass', exact_nonstack_mutable_memory_equal=True,
                  descriptor_payload_and_latch_neighbors_preserved=True,
                  original_code_unchanged=True, actual_peripheral_accesses=0)
    stem.with_suffix('.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    return result


def supply(state, values):
    for address, value in values.items():
        assert address in TRACKED and 0 <= value < 1 << (8 * TRACKED[address])
        state.write(address, TRACKED[address], value)
    return {hex(address): hex(value) for address, value in values.items()}


def cases():
    for fill in (0, 204):
        for empty in (0, 1):
            for latch in (0, 1, 255):
                for speed in (0, 0x2000, 0x4000, 0x6000):
                    values = {DEVSTS: 0xa5a50021 | (empty << 15) | speed,
                              LATCH: latch, OUT1: 0x13570261,
                              DEVCTL: 0x5a5a0320 | (8 if fill else 0)}
                    yield dict(name=f'admission-f{fill}-empty{empty}-latch{latch}-speed{speed:x}',
                               kind='supplied_fifo_latch_and_speed_images', fill=fill,
                               phases=[dict(values=values, delay_devctl=None)])
        for enables in range(4):
            # Every case changes unrelated bits as well as RDE/TDE, exposing a
            # stale pre-delay value. Enables 0/2 explicitly supply RDE cleared.
            delayed = 0x6b6b8030 | (enables << 2)
            yield dict(name=f'delayed-devctl-f{fill}-enables{enables}',
                       kind='supplied_delay_return_replaces_devctl', fill=fill,
                       phases=[dict(values={DEVSTS: 0x12340000, LATCH: 0,
                                            OUT1: 0x87650120, DEVCTL: 0xa55a030c},
                                    delay_devctl=delayed)])
        yield dict(name=f'repeated-helper-f{fill}',
                   kind='fresh_calls_retain_latch_then_supplied_latch_clear', fill=fill,
                   phases=[dict(values={DEVSTS: 0x23450000, LATCH: 0,
                                        OUT1: 0x76540120, DEVCTL: 0x7654032c},
                                delay_devctl=0xabc00320),
                           dict(values={DEVCTL: 0xdef00320},
                                delay_devctl=0x11223344),
                           dict(values={LATCH: 0, DEVSTS: 0x23452000},
                                delay_devctl=0x55660020)])


def compare_phases(a, b, name):
    for key in ('entry', 'failure', 'supplied_delay_return_devctl', 'trace',
                'nonstack_memory', 'before_memory', 'expected_memory',
                'original_instructions_visited'):
        assert a[key] == b[key], (name, key)


def rejection_cases(program, q, capture):
    rows = []
    for fill in (0, 204):
        for literal, pc in ((0x10005e68, 0x10008f54),
                            (0x10005e70, 0x10008f68),
                            (0x10005ea8, 0x10008f99)):
            observations = []
            for engine in (None, q):
                state = IdleRAM(program, fill, skip_literal=literal)
                supplied = supply(state, {DEVSTS: 0x10000, LATCH: 0,
                                          OUT1: 0x23000420, DEVCTL: 0x8765032c})
                name = f'unredirected-{literal:x}-fill{fill}'
                observations.append(execute_phase(state, engine, name, capture,
                                                  delay_devctl=0x65430320, rejection=pc))
            compare_phases(*observations, name)
            rows.append(dict(fill=fill, unredirected_literal=hex(literal),
                             original_register=hex(REDIRECTS[literal][0]),
                             rejected_before_memory_access=hex(pc), supplied=supplied,
                             interpreter=observations[0], qemu=observations[1]))
    return rows


def reject_excluded_code(program, q):
    state = IdleRAM(program, 204)
    before = snapshot(state)
    runner = begin_qemu(q, state)
    runner.host.clear()  # Prove service bodies themselves are never admitted.
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
    capture = Path(tempfile.mkdtemp(prefix='hp1020-usb-idle-receive-', dir='/tmp'))
    print(f'USB idle receive captures: {capture}', flush=True)
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
    audited = []
    for (begin, end), digest in {**CODE_SHA, CALLER_RANGE: CALLER_SHA}.items():
        raw = section_bytes(blob, sections, begin, end - begin)
        assert sha(raw) == digest
        audited.append(dict(begin=hex(begin), end=hex(end), bytes=raw.hex(), sha256=digest,
                            executed=(begin, end) in CODE))
    for name, digest in REFERENCE_SHA.items():
        assert sha((REF / name).read_bytes()) == digest
    assert json.loads((REF / 'provenance.json').read_text())['commit'] == UPSTREAM_COMMIT
    definitions = {name: int(value, 0) for name, value in re.findall(
        r'^#define\s+(UDC_\w+)\s+(0x[0-9a-fA-F]+|[0-9]+)\s*(?:/\*.*)?$',
        (REF / 'amd5536udc.h').read_text(), re.M)}
    for name, value in (('UDC_DEVCTL_RDE', 2), ('UDC_DEVCTL_TDE', 3),
                        ('UDC_DEVSTS_RXFIFO_EMPTY', 15), ('UDC_EPCTL_SNAK', 7),
                        ('UDC_DEVSTS_ENUM_SPEED_MASK', 0x6000)):
        assert definitions[name] == value
    prefix = os.environ.get('XTENSA_PREFIX', '/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf')
    program = Program(stock, prefix)
    original = Machine(program)
    for at, value in LITERALS.items():
        assert original.read(at, 4) == value
    for pc, (op, args, encoded) in ANCHORS.items():
        assert program.instruction(pc) == (op, args, bytes.fromhex(encoded)), hex(pc)
        assert section_bytes(blob, sections, pc, len(bytes.fromhex(encoded))).hex() == encoded
    direct_calls = [hex(pc) for pc, (op, args, _) in program.instructions.items()
                    if op in ('call0', 'call4', 'call8', 'call12') and args == (ENTRY,)]
    assert direct_calls == ['0x10009937']
    results = []
    with QemuRAM() as q:
        version = q.version
        for case in cases():
            (capture / f'{case["name"]}.input.json').write_text(json.dumps(case, indent=2) + '\n')
            observations = []
            for engine in (None, q):
                state = IdleRAM(program, case['fill'])
                phases = []
                for index, phase in enumerate(case['phases']):
                    supplied = supply(state, phase['values'])
                    name = f'{case["name"]}-phase{index}'
                    result = execute_phase(state, engine, name, capture, phase['delay_devctl'])
                    phases.append(dict(supplied_before_call=supplied, observation=result))
                observations.append(phases)
            for index, (a, b) in enumerate(zip(*observations)):
                assert a['supplied_before_call'] == b['supplied_before_call']
                compare_phases(a['observation'], b['observation'], f'{case["name"]}/{index}')
            results.append(dict(name=case['name'], kind=case['kind'], fill=case['fill'],
                                interpreter=observations[0], qemu=observations[1]))
        rejected = rejection_cases(program, q, capture)
        excluded = reject_excluded_code(program, q)
    assert len(results) == 58 and len(rejected) == 6 and len(excluded) == 15
    assert sha(stock.read_bytes()) == STOCK_SHA
    assert all(sha((ROOT / name).read_bytes()) == digest for name, digest in sources.items())
    report = dict(status='pass', cases=results, unredirected_controls=rejected,
                  excluded_code_controls=excluded, source_sha256=sources,
                  stock_elf_sha256=STOCK_SHA, qemu_version=version,
                  original_byte_ranges=audited,
                  instruction_anchors={hex(pc): dict(op=op, args=args, bytes=encoded)
                                       for pc, (op, args, encoded) in ANCHORS.items()},
                  literal_anchors={hex(pc): hex(value) for pc, value in LITERALS.items()},
                  private_literal_redirects={hex(at): dict(original=hex(a), ram=hex(b))
                                            for at, (a, b) in REDIRECTS.items()},
                  supplied_services=[
                      dict(address=hex(MASK), argument=4, effects='record only; return zero'),
                      dict(address=hex(UNMASK), argument=4, effects='record only; return zero'),
                      dict(address=hex(DELAY), arguments=[5, 50],
                           effects='record; optionally replace RAM DEVCTL with the supplied word; return zero')],
                  direct_call_sites=direct_calls, upstream_commit=UPSTREAM_COMMIT,
                  completed_usb_control_transfers=0, completed_native_page_lifecycles=0,
                  actual_peripheral_accesses=0, controller_quiescence_established=False,
                  original_entry=hex(ENTRY), original_end_exclusive=hex(END),
                  omitted_startup_prefix=False, mid_function_pc_cuts=[],
                  scope='Original idle receive helper skips when supplied DEVSTS RXFIFO_EMPTY is set or its byte latch is nonzero. Otherwise it requests OUT1 SNAK, sets the latch, supplies delay 5/50, rereads DEVCTL and sets RDE bit 2. Independent expected access traces and every nonstack mutable byte agree in both engines.',
                  call_context='The original USB2IdleThread directly loops around this helper; its creation literal and caller bytes are checked but never executed. Each phase is a fresh original helper ENTRY with retained supplied RAM. IRQ mask and unmask services are substitutions, not actual interrupt operations.',
                  limits='Three register-address literals point to RAM, with no self-clearing bits or controller behavior. Delay-return DEVCTL changes are explicit synthetic inputs, not evidence of an actual stock scheduling race or completed stop. Delay/clock/interrupt bodies, the surrounding infinite loop, startup, IRQ, rearm, pause and reset paths are excluded. No owner transition, descriptor retirement, FIFO flush, DMA reset, pending-event drain or physical quiescence is established. Descriptor and payload preservation refers only to supplied RAM canaries. Family bit names do not identify HP silicon or authorize peripheral writes. Zero USB traffic or printing.')
    text = json.dumps(report, indent=2, sort_keys=True) + '\n'
    (capture / 'report.json').write_text(text)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.with_suffix('.json').write_text(text)
    OUT.with_suffix('.md').write_text('# Original USB idle receive intent\n\n'
        + f'{len(results)} conditional RAM cases agree in both engines; '
        + f'{len(rejected)} unredirected-register cases reject before peripheral access.\n\n'
        + report['scope'] + '\n\n' + report['call_context'] + '\n\n'
        + 'A supplied RDE-clear word at the delay boundary is followed by the original RDE-set operation. '
        + 'The original does not inspect a cancellation generation or descriptor ownership here. '
        + 'A future transport must settle or fence pending receive-enable work before acknowledging '
        + 'quiescence; this experiment does not supply that acknowledgement.\n\n'
        + report['limits'] + '\n')
    print(f'USB idle receive: {len(results)} conditional cases, {len(rejected)} MMIO rejections; no quiescence claim', flush=True)


if __name__ == '__main__':
    main()
