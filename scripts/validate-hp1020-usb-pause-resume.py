#!/usr/bin/env python3
"""Observe original USB pause/restore command intent against guarded RAM.

The two original functions execute with three peripheral-address literals
redirected in a private image. Their targets are ordinary RAM, not an emulated
USB controller. The delay is a supplied call boundary; no time passes. Register
images between invocations are explicit inputs, not simulated NAK completion.
No descriptor ownership, abort completion or physical quiescence is inferred.
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
OUT = ROOT / 'analysis/usb-path/pause-resume'
REF = ROOT / 'analysis/usb-path/controller-reference/linux-v6.12'
STOCK_SHA = '2111560068db47ceca21fa550db4c7c34f5595b5a5d137ae4a19631e40e3601d'
UPSTREAM_COMMIT = 'adc218676eef25575469234709c2d87185ca223a'
REFERENCE_SHA = {
    'amd5536udc.h': '8dbf2ebffe7de042bdfea1c5e4e0d7e7ca334cb821fbfaa1cf9ccfeeae302648',
    'snps_udc_core.c': 'c1b09e8f69d3340f2afd3a033d77a42775b52716d45b1aceb211dcaab89127bf',
}
PAUSE, RESUME, END = 0x10009a10, 0x10009a70, 0x10009abc
DELAY, DELAY_VALUE = 0x100116ec, 200000
CODE = [(PAUSE, RESUME), (RESUME, END)]
CODE_SHA = {
    (PAUSE, RESUME): 'b42ab81cbebfb6443c176acc82989d806416dd49d37be8c7436737379ab13dde',
    (RESUME, END): '0daa531c9b9cbe62e96deece426844d1972190e28170fc037010d3467c47f797',
}
ARENA, ARENA_SIZE = 0x22600000, 0x1000
DEVCTL, OUT1, OUT0 = ARENA + 0x100, ARENA + 0x200, ARENA + 0x300
DESCRIPTORS, PAYLOAD = ARENA + 0x400, ARENA + 0x800
SAVED1, SAVED0 = 0x10021588, 0x10021384
REDIRECTS = {
    0x10005ea8: (0xb3000404, DEVCTL),
    0x10005e70: (0xb3000220, OUT1),
    0x10005e24: (0xb3000200, OUT0),
}
TRACKED = {DEVCTL, OUT1, OUT0, SAVED1, SAVED0}
EMPTY_FIXTURE = SimpleNamespace(path=None, execute_ranges=[])
EXCLUDED = (DELAY, 0x1001bb5c, 0x100121e4, 0x1001658c, 0x10008208,
            0x100086f4, 0x10008c24, 0x10008fb0, 0x10008ff0)
LITERALS = {
    **{at: pair[0] for at, pair in REDIRECTS.items()},
    0x10005fd0: SAVED1, 0x10005fd4: SAVED0, 0x10005fd8: DELAY_VALUE,
    0x10005e2c: 0x1001bc48,
}
ANCHORS = {
    PAUSE: ('entry', (1, 32), '6c1004'),
    0x10009a16: ('movi.n', (9, -9), 'c797'),
    0x10009a1b: ('l32i.n', (8, 10, 0), '88a0'),
    0x10009a20: ('and', (8, 8, 9), '098801'),
    0x10009a26: ('s32i.n', (8, 10, 0), '98a0'),
    0x10009a31: ('l32i.n', (8, 10, 0), '88a0'),
    0x10009a33: ('movi.n', (13, 64), 'c4d0'),
    0x10009a38: ('l32i.n', (9, 11, 0), '89b0'),
    0x10009a3d: ('s32i.n', (8, 12, 0), '98c0'),
    0x10009a42: ('l32i.n', (8, 10, 0), '88a0'),
    0x10009a44: ('movi', (12, 128), '2c0a80'),
    0x10009a4d: ('s32i.n', (8, 10, 0), '98a0'),
    0x10009a55: ('l32i.n', (8, 11, 0), '88b0'),
    0x10009a5a: ('s32i.n', (9, 10, 0), '99a0'),
    0x10009a65: ('s32i.n', (8, 11, 0), '98b0'),
    0x10009a6a: ('call8', (DELAY,), '581f20'),
    0x10009a6d: ('retw', (), '060000'),
    RESUME: ('entry', (1, 32), '6c1004'),
    0x10009a79: ('l32i.n', (2, 4, 0), '8240'),
    0x10009a7b: ('movi.n', (3, 8), 'c038'),
    0x10009a83: ('s32i.n', (2, 4, 0), '9240'),
    0x10009a88: ('l32i.n', (2, 2, 0), '8220'),
    0x10009a8a: ('bnez.n', (2, 0x10009aa0), 'cd22'),
    0x10009a92: ('l32i.n', (3, 2, 0), '8320'),
    0x10009a94: ('movi', (4, 256), '241a00'),
    0x10009a9d: ('s32i', (3, 2, 0), '232600'),
    0x10009aa3: ('l32i.n', (2, 2, 0), '8220'),
    0x10009aa5: ('bnez.n', (2, 0x10009aba), 'cd21'),
    0x10009aad: ('l32i.n', (3, 2, 0), '8320'),
    0x10009aaf: ('movi', (4, 256), '241a00'),
    0x10009ab8: ('s32i.n', (3, 2, 0), '9320'),
    0x10009aba: ('retw.n', (), 'd10f'),
    0x100121f3: ('call8', (PAUSE,), '5bde07'),
    0x100121f9: ('call8', (0x1001658c,), '5810e4'),
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


def event(pc, kind, address, value):
    return dict(pc=hex(pc), kind=kind, address=hex(address), value=hex(value))


class PauseRAM(StopRAM):
    def __init__(self, program, fill, skip_literal=None):
        self.recording, self.events = False, []
        super().__init__(program, PAUSE, CODE.copy(), [(ARENA, ARENA_SIZE)])
        self.put(STACK, bytes([fill]) * STACK_SIZE)
        self.put(ARENA, bytes([fill]) * ARENA_SIZE)
        self.write(SAVED1, 4, 0x12345678)
        self.write(SAVED0, 4, 0x89abcdef)
        # Supplied RAM descriptors/payloads are canaries, not controller-owned
        # memory. The original bulk descriptor global points at these bytes,
        # while the redirected register neighborhoods carry their pointers.
        self.write(self.read(0x10005e2c, 4), 4, DESCRIPTORS)
        for index in range(4):
            at = DESCRIPTORS + index * 16
            for offset, value in ((0, (index << 30) | 0x08000025),
                                  (4, 0xabc00000 | index),
                                  (8, PAYLOAD + index * 64), (12, 0)):
                self.write(at + offset, 4, value)
        self.put(PAYLOAD, bytes((fill + index * 31) & 255 for index in range(256)))
        self.write(OUT1 + 20, 4, DESCRIPTORS + 16)
        self.write(OUT0 + 20, 4, DESCRIPTORS + 32)
        for literal, (original, redirected) in REDIRECTS.items():
            assert self.read(literal, 4) == original
            if literal != skip_literal:
                self.write_ranges.append((literal, literal + 4))
                self.write(literal, 4, redirected)

    def read(self, address, size):
        value = super().read(address, size)
        if self.recording and address in TRACKED:
            assert size == 4
            self.events.append(event(self.pc, 'read', address, value))
        return value

    def write(self, address, size, value):
        super().write(address, size, value)
        if self.recording and address in TRACKED:
            assert size == 4
            self.events.append(event(self.pc, 'write', address, value & 0xffffffff))

    def extension(self, op, args, nxt):
        if op == 'call8' and args == (DELAY,):
            self.events.append(event(self.pc, 'supplied_delay', DELAY, self.registers[10]))
            # No timer reads, waiting, interrupt masks or controller side
            # effects are supplied. This function is void to its caller.
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


def oracle(before, entry, stop_before=None):
    """Independent word/command contract; never examines executed results."""
    expected = {bounds: bytearray(data) for bounds, data in before.items()}
    events = []

    class Boundary(Exception):
        pass

    def locate(at):
        matches = [(a, b) for a, b in expected if a <= at and at + 4 <= b]
        assert len(matches) == 1
        return matches[0]

    def read(pc, at):
        if pc == stop_before:
            raise Boundary
        begin, end = locate(at)
        value = int.from_bytes(expected[(begin, end)][at - begin:at - begin + 4], 'big')
        events.append(event(pc, 'read', at, value))
        return value

    def write(pc, at, value):
        if pc == stop_before:
            raise Boundary
        begin, end = locate(at)
        expected[(begin, end)][at - begin:at - begin + 4] = value.to_bytes(4, 'big')
        events.append(event(pc, 'write', at, value))

    try:
        if entry == PAUSE:
            device = read(0x10009a1b, DEVCTL)
            write(0x10009a26, DEVCTL, device & 0xfffffff7)
            saved1 = read(0x10009a31, OUT1) & 0x40
            saved0 = read(0x10009a38, OUT0) & 0x40
            write(0x10009a3d, SAVED1, saved1)
            write(0x10009a4d, OUT1, read(0x10009a42, OUT1) | 0x80)
            out0 = read(0x10009a55, OUT0)
            write(0x10009a5a, SAVED0, saved0)
            write(0x10009a65, OUT0, out0 | 0x80)
            events.append(event(0x10009a6a, 'supplied_delay', DELAY, DELAY_VALUE))
        else:
            assert entry == RESUME
            write(0x10009a83, DEVCTL, read(0x10009a79, DEVCTL) | 8)
            if read(0x10009a88, SAVED1) == 0:
                write(0x10009a9d, OUT1, read(0x10009a92, OUT1) | 0x100)
            if read(0x10009aa3, SAVED0) == 0:
                write(0x10009ab8, OUT0, read(0x10009aad, OUT0) | 0x100)
    except Boundary:
        assert stop_before is not None
    else:
        assert stop_before is None, ('oracle missed rejection boundary', hex(stop_before))
    return {bounds: bytes(data) for bounds, data in expected.items()}, events


def begin_qemu(q, state, entry):
    # Same fresh CALL8 wrapper/ABI save area as the existing bounded runners.
    q.load(state.program.path)
    runner = NativeTasks(q, state, EMPTY_FIXTURE, CODE, {DELAY}, instruction_budget=200)
    runner.synchronize(True)
    top = STACK_TOP - 0x100
    q.put(top - 12, (top + 64).to_bytes(4, 'big'))
    q.put(RETURN - 3, bytes.fromhex('0b8000'))
    q.reset_cpu(RETURN - 3)
    q.set_reg(2, top)
    q.set_reg(42, 0x40000)
    q.set_reg(111, 0x10000000)
    q.set_reg(9, entry)
    return runner


def observe_qemu(state, q):
    pc = q.reg(0)
    if not any(a <= pc < b for a, b in CODE):
        return
    op, args, _ = state.program.instruction(pc)
    base = op.removesuffix('.n')
    if base not in ('l32i', 's32i'):
        return
    ar = lambda index: q.reg(((q.reg(38) * 4 + index) % 32) + 1)
    address = (ar(args[1]) + args[2]) & 0xffffffff
    if address in TRACKED:
        # Trace reads only already-allowed RAM. Unredirected peripheral
        # addresses are rejected by the shared pre-step memory guard.
        state.span(address, 4)
        value = int.from_bytes(q.read(address, 4), 'big') if base == 'l32i' else ar(args[0])
        state.events.append(event(pc, 'read' if base == 'l32i' else 'write', address, value))


def execute_phase(state, q, entry, name, capture, rejection=None):
    engine = 'interpreter' if q is None else 'qemu'
    before = snapshot(state)
    expected, expected_events = oracle(before, entry, rejection)
    stem = capture / f'{name}-{engine}'
    stem.with_suffix('.before.bin').write_bytes(b''.join(data for _, data in sorted(before.items())))
    stem.with_suffix('.expected.bin').write_bytes(b''.join(data for _, data in sorted(expected.items())))
    state.pc, state.steps, state.visited, state.events = entry, 0, set(), []
    state.registers = [0] * 16
    state.registers[0], state.registers[1] = STOP, STACK + STACK_SIZE - 16
    state.frames, state.loop, state.sar = [], None, 0
    failure, runner = None, None
    try:
        if q is None:
            state.recording = True
            state.run(budget=200)
        else:
            runner = begin_qemu(q, state, entry)
            while q.reg(0) != RETURN:
                observe_qemu(state, q)
                runner.step()
            assert q.reg(38) == 0 and q.reg(39) == 1
            state.pc = STOP
    except ValueError as error:
        failure = dict(reason=str(error), pc=hex(state.pc))
    finally:
        state.recording = False
        if runner is not None:
            runner.synchronize(False)
    actual = snapshot(state)
    stem.with_suffix('.after.bin').write_bytes(b''.join(data for _, data in sorted(actual.items())))
    selected = sorted(pc for pc in (state.visited if q is None else runner.visited)
                      if any(a <= pc < b for a, b in CODE) and pc != rejection)
    result = dict(status='captured_unchecked', entry=hex(entry), failure=failure,
                  trace=state.events, expected_trace=expected_events,
                  nonstack_memory=memory_manifest(actual),
                  before_memory=memory_manifest(before), expected_memory=memory_manifest(expected),
                  original_instructions_visited=[hex(pc) for pc in selected],
                  steps=state.steps if q is None else runner.steps)
    stem.with_suffix('.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    if rejection is None:
        assert failure is None and state.pc == STOP, (name, engine, failure)
    else:
        assert failure == dict(reason='MMIO forbidden', pc=hex(rejection)), (name, engine, failure)
        if q is not None:
            assert q.reg(0) == rejection and rejection not in runner.visited
    assert actual == expected, (name, engine, 'nonstack memory differs')
    assert state.events == expected_events, (name, engine, 'command/access trace differs')
    for begin, end in CODE:
        code = state.bytes_at(begin, end - begin)
        assert sha(code) == CODE_SHA[(begin, end)]
        if q is not None:
            assert q.read(begin, end - begin) == code
    result['status'] = 'pass'
    result['descriptor_payload_and_other_nonstack_bytes_preserved'] = True
    stem.with_suffix('.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    return result


def supply_words(state, words):
    for address, value in words.items():
        state.write(address, 4, value)
    return {hex(address): hex(value) for address, value in words.items()}


def cases():
    # Control images deliberately include unrelated bits. They are arithmetic
    # inputs, not a declaration that each image is a valid hardware state.
    for fill in (0, 204):
        for nak1 in (0, 1):
            for nak0 in (0, 1):
                for enables in range(4):
                    salt = 0xa5a50020 if fill else 0x5a5a0021
                    first = {DEVCTL: (salt & ~12) | (enables << 2),
                             OUT1: (0x13570221 & ~0x1c0) | (nak1 << 6),
                             OUT0: (0x24680302 & ~0x1c0) | (nak0 << 6)}
                    second = {DEVCTL: (salt ^ 0x00ff0034) & ~8,
                              OUT1: (0x98760423 & ~0x1c0) | ((1 - nak1) << 6),
                              OUT0: (0x76540501 & ~0x1c0) | ((1 - nak0) << 6)}
                    yield dict(name=f'pair-f{fill}-nak{nak1}{nak0}-en{enables}',
                               kind='pause_then_supplied_resume', fill=fill,
                               phases=[(PAUSE, first), (RESUME, second)])
        for saved1, saved0 in ((0, 1), (0x80000000, 0), (0xffffffff, 0xaaaaaaaa)):
            yield dict(name=f'noncanonical-saved-f{fill}-{saved1:x}-{saved0:x}',
                       kind='conditional_resume_with_supplied_saved_words', fill=fill,
                       phases=[(RESUME, {DEVCTL: 0x12340004, OUT1: 0x20, OUT0: 0,
                                         SAVED1: saved1, SAVED0: saved0})])
        for nak1 in (0, 1):
            for nak0 in (0, 1):
                yield dict(name=f'repeated-pause-f{fill}-nak{nak1}{nak0}',
                           kind='second_pause_overwrites_saved_state', fill=fill,
                           phases=[(PAUSE, {DEVCTL: 0x5a00aa0c, OUT1: 0x20 | (nak1 << 6),
                                            OUT0: nak0 << 6}),
                                   (PAUSE, {DEVCTL: 0x5a00aa04, OUT1: 0x60, OUT0: 0x40}),
                                   (RESUME, {DEVCTL: 0xaa550004, OUT1: 0x20, OUT0: 0})])


def compare_phases(a, b, name):
    for key in ('entry', 'failure', 'trace', 'nonstack_memory', 'before_memory',
                'expected_memory', 'original_instructions_visited'):
        assert a[key] == b[key], (name, key)


def rejection_cases(program, q, capture):
    # Each removed redirection independently reaches its first unmodified
    # peripheral read. Earlier original writes to the other RAM sinks must
    # match the independent prefix oracle; nothing is rolled back silently.
    rows = []
    for entry, first_reads in ((PAUSE, (0x10009a1b, 0x10009a31, 0x10009a38)),
                               (RESUME, (0x10009a79, 0x10009a92, 0x10009aad))):
        for literal, pc in zip(REDIRECTS, first_reads):
            observations = []
            for engine in (None, q):
                state = PauseRAM(program, 204, skip_literal=literal)
                supplied = supply_words(state, {DEVCTL: 0x1234567c, OUT1: 0x20, OUT0: 0,
                                                SAVED1: 0, SAVED0: 0})
                name = f'unredirected-{entry:x}-{literal:x}'
                observations.append(execute_phase(state, engine, entry, name, capture, rejection=pc))
            compare_phases(*observations, name)
            rows.append(dict(entry=hex(entry), unredirected_literal=hex(literal),
                             original_register=hex(REDIRECTS[literal][0]),
                             rejected_before_memory_access=hex(pc), supplied=supplied,
                             interpreter=observations[0], qemu=observations[1]))
    return rows


def reject_excluded_code(program, q):
    state = PauseRAM(program, 204)
    before = snapshot(state)
    runner = begin_qemu(q, state, PAUSE)
    runner.host.clear()  # Even the delay body must not execute as original code.
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
    capture = Path(tempfile.mkdtemp(prefix='hp1020-usb-pause-resume-', dir='/tmp'))
    print(f'USB pause/restore captures: {capture}', flush=True)
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
    for (begin, end), digest in CODE_SHA.items():
        raw = section_bytes(blob, sections, begin, end - begin)
        assert sha(raw) == digest
        audited.append(dict(begin=hex(begin), end=hex(end), bytes=raw.hex(), sha256=digest))
    for name, digest in REFERENCE_SHA.items():
        assert sha((REF / name).read_bytes()) == digest
    assert json.loads((REF / 'provenance.json').read_text())['commit'] == UPSTREAM_COMMIT
    definitions = {name: int(value, 0) for name, value in re.findall(
        r'^#define\s+(UDC_\w+)\s+(0x[0-9a-fA-F]+|[0-9]+)\s*(?:/\*.*)?$',
        (REF / 'amd5536udc.h').read_text(), re.M)}
    for name, bit in (('UDC_DEVCTL_TDE', 3), ('UDC_DEVCTL_RDE', 2),
                      ('UDC_EPCTL_NAK', 6), ('UDC_EPCTL_SNAK', 7), ('UDC_EPCTL_CNAK', 8)):
        assert definitions[name] == bit
    prefix = os.environ.get('XTENSA_PREFIX', '/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf')
    program = Program(stock, prefix)
    original = Machine(program)
    for at, value in LITERALS.items():
        assert original.read(at, 4) == value
    for pc, (op, args, encoded) in ANCHORS.items():
        assert program.instruction(pc) == (op, args, bytes.fromhex(encoded)), hex(pc)
        assert section_bytes(blob, sections, pc, len(bytes.fromhex(encoded))).hex() == encoded
    direct_calls = {hex(target): [hex(pc) for pc, (op, args, _) in program.instructions.items()
                                  if op in ('call0', 'call4', 'call8', 'call12') and args == (target,)]
                    for target in (PAUSE, RESUME)}
    assert direct_calls == {hex(PAUSE): ['0x100121f3'], hex(RESUME): []}
    pointer_literals = {hex(target): [] for target in (PAUSE, RESUME)}
    for sec in sections.values():
        if not sec['flags'] & 2 or sec['type'] == 8:
            continue
        data = blob[sec['offset']:sec['offset'] + sec['size']]
        for offset in range(0, len(data) - 3, 4):
            value = int.from_bytes(data[offset:offset + 4], 'big')
            if hex(value) in pointer_literals:
                pointer_literals[hex(value)].append(hex(sec['address'] + offset))
    assert all(not values for values in pointer_literals.values())
    results = []
    with QemuRAM() as q:
        version = q.version
        for case in cases():
            observations = []
            for engine in (None, q):
                state = PauseRAM(program, case['fill'])
                phases = []
                for index, (entry, words) in enumerate(case['phases']):
                    supplied = supply_words(state, words)
                    name = f'{case["name"]}-phase{index}'
                    result = execute_phase(state, engine, entry, name, capture)
                    phases.append(dict(supplied_before_call=supplied, observation=result))
                observations.append(phases)
            for index, (a, b) in enumerate(zip(*observations)):
                assert a['supplied_before_call'] == b['supplied_before_call']
                compare_phases(a['observation'], b['observation'], f'{case["name"]}/{index}')
            results.append(dict(name=case['name'], kind=case['kind'], fill=case['fill'],
                                interpreter=observations[0], qemu=observations[1]))
        rejected = rejection_cases(program, q, capture)
        excluded = reject_excluded_code(program, q)
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
                  supplied_services=[dict(address=hex(DELAY), argument=DELAY_VALUE,
                                          effects='record argument, return without delay or other side effects')],
                  direct_call_sites=direct_calls, aligned_function_pointer_literals=pointer_literals,
                  upstream_commit=UPSTREAM_COMMIT,
                  completed_usb_control_transfers=0, completed_native_page_lifecycles=0,
                  actual_peripheral_accesses=0, controller_quiescence_established=False,
                  scope='Original pause clears DEVCTL bit 3, saves OUT1/OUT0 NAK bit 6, issues SNAK bit 7, and requests a supplied delay. Original restore sets bit 3 and issues CNAK bit 8 only for a zero saved word. RDE bit 2 is preserved by both. Exact ordered RAM accesses and every nonstack mutable byte match separate oracles.',
                  call_context='One annotated direct pause call is present at 0x100121f3 in 0x100121e4; its enclosing interrupt service, 0x1001658c and indirect callback are not executed. No annotated direct call or aligned file-backed pointer to restore was found. Calling restore and supplying later control images are experiment preconditions, not a recovered reset lifecycle.',
                  limits='Three address literals are redirected to ordinary RAM; command bits do not self-clear and hardware readback is not emulated. Register images between calls are supplied, including the second pause NAK bits. The delay body/time and all caller context are excluded. No RDE disable, descriptor retirement, owner transition, FIFO flush, DMA reset, pending-IRQ drain or quiescence is established. Family bit names are reference-supported inferences, not HP silicon documentation or permission to issue these writes. Descriptor/payload preservation proves only the selected routines did not touch these supplied bytes. Zero physical USB transfers or printing.')
    text = json.dumps(report, indent=2, sort_keys=True) + '\n'
    (capture / 'report.json').write_text(text)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.with_suffix('.json').write_text(text)
    OUT.with_suffix('.md').write_text('# Original USB pause/restore intent\n\n'
        + f'{len(results)} conditional RAM cases agree in both engines; '
        + f'{len(rejected)} unredirected-register cases reject before peripheral access.\n\n'
        + report['scope'] + '\n\n' + report['call_context'] + '\n\n'
        + 'Repeated pause replaces the saved NAK state; it is not a nesting counter. '
        + 'Restore enables TDE even when it was disabled before pause. Noncanonical saved '
        + 'nonzero values also suppress CNAK. None of these observations is an abort acknowledgement.\n\n'
        + report['limits'] + '\n')
    print(f'USB pause/restore: {len(results)} conditional cases, {len(rejected)} MMIO rejections; no quiescence claim', flush=True)


if __name__ == '__main__':
    main()
