#!/usr/bin/env python3
"""Bounded offline experiment for original SETUP retirement and OUT0 rearm intent.

Explicit post-dispatch register/RAM cut, not a whole request or original ENTRY.
Four named peripheral-address literals may point to ordinary guarded RAM images.
No actual peripheral access, interrupt, controller behavior, stall clearing,
descriptor reuse permission or physical transfer settlement is established.
"""
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
from types import SimpleNamespace

DEFAULT_ROOT = Path(__file__).resolve().parents[1] if Path(__file__).parent.name == 'scripts' else Path.cwd()
ROOT = Path(os.environ.get('HP1020_ROOT', str(DEFAULT_ROOT))).resolve()
OUT = ROOT / 'analysis/usb-path/setup-retirement'
sys.path.insert(0, str(ROOT / 'scripts'))
from hp1020_xtensa_call0 import Program, Machine, STOP, STACK, STACK_SIZE
from hp1020_xtensa_properties import properties, section_bytes
from hp1020_stock_stop import StopRAM
from hp1020_qemu_multitask import NativeTasks
from hp1020_qemu_stock_parser import guard_memory
from hp1020_qemu_ram import QemuRAM, STACK_TOP

STOCK_SHA = '2111560068db47ceca21fa550db4c7c34f5595b5a5d137ae4a19631e40e3601d'
LINUX_COMMIT = 'adc218676eef25575469234709c2d87185ca223a'
REF = ROOT / 'analysis/usb-path/controller-reference/linux-v6.12'
REFERENCE_SHA = {
    'amd5536udc.h': '8dbf2ebffe7de042bdfea1c5e4e0d7e7ca334cb821fbfaa1cf9ccfeeae302648',
    'snps_udc_core.c': 'c1b09e8f69d3340f2afd3a033d77a42775b52716d45b1aceb211dcaab89127bf',
    'provenance.json': '023d10e246e4852c1b9415cdc3d591006edcedeba467a56b95b22b994d4a08e4',
}
START, END = 0x1000985c, 0x1000992e
CODE = [(START, END)]
CODE_SHA = '1de51b81705babf558e94f732621f10677f423c86a0a6bac3fe1c84e54eaf1b0'
ARENA, ARENA_SIZE = 0x22a00000, 0x2000
OUT0, IN0, OUT1, DESPTR_IMAGE = ARENA + 0x100, ARENA + 0x120, ARENA + 0x140, ARENA + 0x160
SETUP, OBSERVED, OTHER = ARENA + 0x300, ARENA + 0x400, ARENA + 0x500
SETUP_GLOBAL, OUT_GLOBAL, AVAILABLE, LATCH = 0x1001bbc0, 0x1001bc60, 0x1001bc50, 0x1001bc72
INITIAL_SP = STACK_TOP - 0x100
REDIRECTS = {
    0x10005e24: (0xb3000200, OUT0),
    0x10005e90: (0xb3000000, IN0),
    0x10005ef8: (0xb3000214, DESPTR_IMAGE),
    0x10005e70: (0xb3000220, OUT1),
}
LITERALS = {
    **{at: pair[0] for at, pair in REDIRECTS.items()},
    0x10005ee8: SETUP_GLOBAL, 0x10005eec: OUT_GLOBAL,
    0x10005e38: AVAILABLE, 0x10005e64: LATCH,
    0x10005e30: 0xc0000000, 0x10005e34: 0x80000000,
}
ANCHORS = {
    START: ('bnei', (2, 1, 0x10009884), '692124'),
    0x10009865: ('l32i.n', (8, 6, 0), '8860'),
    0x10009870: ('s32i.n', (8, 6, 0), '9860'),
    0x10009877: ('l32i.n', (8, 9, 0), '8890'),
    0x1000987f: ('s32i.n', (8, 9, 0), '9890'),
    0x10009881: ('movi', (2, 0), '220a00'),
    0x1000988d: ('s32i', (3, 8, 0), '238600'),
    0x10009896: ('l32i.n', (11, 8, 0), '8b80'),
    0x10009898: ('l8ui', (10, 11, 0), '2ab000'),
    0x100098bc: ('and', (8, 10, 8), '08a801'),
    0x100098bf: ('bne', (8, 9, 0x100098f9), '798936'),
    0x100098c5: ('l32i.n', (8, 8, 0), '8880'),
    0x100098ca: ('l8ui', (9, 8, 0), '298000'),
    0x100098d2: ('s8i', (9, 8, 0), '298400'),
    0x100098de: ('s8i', (3, 8, 1), '238401'),
    0x100098ea: ('s8i', (3, 8, 2), '238402'),
    0x100098f6: ('s8i', (3, 8, 3), '238403'),
    0x10009905: ('l32i.n', (8, 6, 0), '8860'),
    0x1000990f: ('s32i.n', (8, 6, 0), '9860'),
    0x10009914: ('bltu', (6, 9, 0x10009928), '796310'),
    0x1000991d: ('l32i.n', (8, 9, 0), '8890'),
    0x10009925: ('s32i', (8, 9, 0), '289600'),
    0x1000992b: ('s8i', (3, 8, 0), '238400'),
    END: ('j', (0x10009347,), '63fa15'),
    # Audited only: no initialization or zero-definition instructions execute.
    0x1000912d: ('movi.n', (7, 0), 'c070'),
    0x10009286: ('mov.n', (3, 7), 'd370'),
}
EXCLUDED = (0x10008ff0, 0x1000912d, 0x10009286, 0x10009347,
            0x10009358, 0x1000935b, 0x1000941d, 0x100096a9,
            0x10009859, END, 0x10008208, 0x10008f40,
            0x10009a10, 0x10009a70, 0x10008c24)
EMPTY_FIXTURE = SimpleNamespace(path=None, execute_ranges=[])
ACCESS_SITES = (
    ('out0-stall-read', 0x10009865, 6, 0xb3000200),
    ('out0-stall-write', 0x10009870, 6, 0xb3000200),
    ('in0-stall-read', 0x10009877, 9, 0xb3000000),
    ('in0-stall-write', 0x1000987f, 9, 0xb3000000),
    ('out0-desptr-read', 0x10009896, 8, 0xb3000214),
    ('out0-cnak-read', 0x10009905, 6, 0xb3000200),
    ('out0-cnak-write', 0x1000990f, 6, 0xb3000200),
    ('out1-cnak-read', 0x1000991d, 9, 0xb3000220),
    ('out1-cnak-write', 0x10009925, 9, 0xb3000220),
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def patterned(seed, address, size):
    return bytes((seed + (address >> 8) + i * 17 + (i >> 4) * 3) & 255 for i in range(size))


def access(pc, kind, address, size, value):
    return dict(pc=hex(pc), kind=kind, address=hex(address), size=size, value=hex(value))


def base_case(name, seed, stall=0, owner=2, available=512):
    return dict(name=name, kind='primary_linked_records', seed=seed, stall=stall,
        owner=owner, rx=0, low_bits=0x08432105 if seed else 0, available=available,
        separate=False, other_status=0x4b654321,
        out0=0x13570220 | (owner & 1) | ((owner & 2) << 5),
        in0=0xa55a0210 | ((owner & 2) >> 1) | ((owner & 1) << 6),
        out1=0x96a50220 | (owner & 1) | ((owner & 2) << 5))


def case_specs():
    for seed in (0, 204):
        for stall in (0, 1):
            for owner in range(4):
                for available in (512, 513):
                    yield base_case(f'linked-f{seed}-s{stall}-o{owner}-n{available}', seed, stall, owner, available)
        for rx in range(4):
            case = base_case(f'rx-independent-f{seed}-rx{rx}', seed, 0, 2, 513)
            case.update(kind='owner_only_rx_and_low_bits_control', rx=rx, low_bits=0x0fffffff)
            yield case
        for available in (0, 0xffffffff):
            case = base_case(f'unsigned-count-f{seed}-n{available}', seed, 1, 2, available)
            case['kind'] = 'unsigned_available_boundary'
            yield case
        case = base_case(f'noncanonical-stall-f{seed}', seed, 2, 2)
        case['kind'] = 'noncanonical_stall_intent_is_not_one'
        yield case
        for owner, other_owner in ((2, 1), (1, 2)):
            case = base_case(f'mismatched-f{seed}-observed{owner}-target{other_owner}', seed, 1, owner)
            case.update(kind='conditional_mismatched_observed_and_target_records', separate=True,
                        other_status=(other_owner << 30) | 0x0b654321)
            yield case
        for label, literal, pc in (
            ('out0', 0x10005e24, 0x10009865), ('in0', 0x10005e90, 0x10009877),
            ('desptr', 0x10005ef8, 0x10009896), ('out1', 0x10005e70, 0x1000991d)):
            case = base_case(f'unredirected-{label}-f{seed}', seed, 1, 2)
            case.update(kind='removed_literal_redirect', skip_literal=literal, reject_pc=pc)
            yield case
        for label, field, pc in (
            ('setup-target', 'bad_setup', 0x1000988d),
            ('observed-header', 'bad_observed', 0x10009898),
            ('rearm-target', 'bad_target', 0x100098ca)):
            case = base_case(f'pointer-escape-{label}-f{seed}', seed, 1, 2)
            case.update(kind='peripheral_pointer_escape', reject_pc=pc, **{field: True})
            yield case
        for label, pc, register, address in ACCESS_SITES:
            case = base_case(f'guard-{label}-f{seed}', seed)
            case.update(kind='standalone_peripheral_instruction', entry=pc, reject_pc=pc,
                        registers={register: address})
            yield case


class RetirementRAM(StopRAM):
    def __init__(self, program, case):
        self.recording, self.events = False, []
        super().__init__(program, case.get('entry', START), CODE.copy(), [(ARENA, ARENA_SIZE)])
        self.case = case
        for begin, end in self.write_ranges:
            self.put(begin, patterned(case['seed'], begin, end - begin))
        for literal, (original, image) in REDIRECTS.items():
            assert self.read(literal, 4) == original
            if literal != case.get('skip_literal'):
                self.write_ranges.append((literal, literal + 4))
                self.write(literal, 4, image)
        self.write(OUT0, 4, case['out0'])
        self.write(IN0, 4, case['in0'])
        self.write(OUT1, 4, case['out1'])
        self.write(DESPTR_IMAGE, 4, 0xb3000300 if case.get('bad_observed') else OBSERVED)
        self.write(SETUP_GLOBAL, 4, 0xb3000300 if case.get('bad_setup') else SETUP)
        self.write(OUT_GLOBAL, 4, 0xb3000300 if case.get('bad_target') else (OTHER if case['separate'] else OBSERVED))
        self.write(AVAILABLE, 4, case['available'])
        self.write(LATCH, 1, 0xa5 ^ case['seed'])
        # No original admission/dispatch is claimed. All record contents are
        # supplied canaries; the post-dispatch packet bytes must remain intact.
        self.put(SETUP, bytes.fromhex('8e123456d3c2b1a0a100341256789abc'))
        self.put(OBSERVED, ((case['owner'] << 30) | (case['rx'] << 28) | case['low_bits']).to_bytes(4, 'big') +
                 bytes.fromhex('1234fedc81726354a5b6c7d8'))
        self.put(OTHER, case['other_status'].to_bytes(4, 'big') + bytes.fromhex('6789abcd9283746501b2c3d4'))
        self.registers = [(0x13579bdf + i * 0x10203 + case['seed'] * 0x01010101) & 0xffffffff for i in range(16)]
        self.registers[0], self.registers[1] = STOP, INITIAL_SP
        self.registers[2], self.registers[3] = case['stall'], 0
        for index, value in case.get('registers', {}).items():
            self.registers[index] = value
        self.supplied_registers = self.registers.copy()

    def read(self, address, size):
        value = super().read(address, size)
        if self.recording:
            self.events.append(access(self.pc, 'read', address, size, value))
        return value

    def write(self, address, size, value):
        self.span(address, size)  # Same pre-access peripheral rejection as QEMU.
        super().write(address, size, value)
        if self.recording:
            self.events.append(access(self.pc, 'write', address, size, value & ((1 << (8 * size)) - 1)))


def snapshot(state):
    # No ENTRY or stack operation is in this cut: stack is checked exactly too.
    return {(a, b): state.bytes_at(a, b - a) for a, b in state.write_ranges}


def manifest(memory):
    return [dict(begin=hex(a), end=hex(b), bytes=len(data), sha256=sha(data))
            for (a, b), data in sorted(memory.items())]


def oracle(before, case):
    """Literal independent record/control contract, using supplied bytes only.

    The explicit read list also prevents unrelated status/global reads from
    passing silently. No interpreter/QEMU register/result determines expectation.
    RAM image stores have no W1C, self-clearing command, timing or DMA semantics.
    """
    expected = {bounds: bytearray(data) for bounds, data in before.items()}
    events = []
    if case['kind'] == 'standalone_peripheral_instruction':
        return before.copy(), events

    class Boundary(Exception):
        pass

    def locate(address, size):
        matches = [(a, b) for a, b in expected if a <= address and address + size <= b]
        assert len(matches) == 1, (hex(address), size)
        return matches[0]

    def read(pc, address, size=4):
        if pc == case.get('reject_pc'):
            raise Boundary
        matches = [(a, b) for a, b in expected if a <= address and address + size <= b]
        if not matches and address in LITERALS and size == 4:
            # Unmodified code literals are immutable and outside the mutable
            # snapshot. Their original values are independently byte-pinned.
            value = LITERALS[address]
        else:
            a, b = locate(address, size)
            value = int.from_bytes(expected[(a, b)][address - a:address - a + size], 'big')
        events.append(access(pc, 'read', address, size, value))
        return value

    def write(pc, address, value, size=4):
        if pc == case.get('reject_pc'):
            raise Boundary
        a, b = locate(address, size)
        expected[(a, b)][address - a:address - a + size] = value.to_bytes(size, 'big')
        events.append(access(pc, 'write', address, size, value))

    try:
        if case['stall'] == 1:
            out = read(0x1000985f, 0x10005e24)
            out_value = read(0x10009865, out)
            inp = read(0x10009867, 0x10005e90)
            write(0x10009870, out, out_value | 1)
            write(0x1000987f, inp, read(0x10009877, inp) | 1)
        setup_cell = read(0x10009884, 0x10005ee8)
        setup = read(0x10009887, setup_cell)
        write(0x1000988d, setup, 0)
        desptr = read(0x10009890, 0x10005ef8)
        observed = read(0x10009896, desptr)
        status = 0
        for pc, offset in ((0x10009898, 0), (0x1000989b, 1), (0x100098a4, 2), (0x100098ad, 3)):
            status |= read(pc, observed + offset, 1) << (24 - offset * 8)
        assert read(0x100098b6, 0x10005e30) == 0xc0000000
        assert read(0x100098b9, 0x10005e34) == 0x80000000
        if status & 0xc0000000 == 0x80000000:
            target_cell = read(0x100098c2, 0x10005eec)
            target = read(0x100098c5, target_cell)
            for rd, wr, offset, value in (
                (0x100098ca, 0x100098d2, 0, 8), (0x100098d8, 0x100098de, 1, 0),
                (0x100098e4, 0x100098ea, 2, 0), (0x100098f0, 0x100098f6, 3, 0)):
                read(rd, target + offset, 1)
                write(wr, target + offset, value, 1)
        out = read(0x100098f9, 0x10005e24)
        count_cell = read(0x100098ff, 0x10005e38)
        out_value = read(0x10009905, out)
        count = read(0x10009907, count_cell)
        write(0x1000990f, out, out_value | 0x100)
        if count <= 512:
            bulk = read(0x10009917, 0x10005e70)
            write(0x10009925, bulk, read(0x1000991d, bulk) | 0x100)
        latch = read(0x10009928, 0x10005e64)
        write(0x1000992b, latch, 0, 1)
    except Boundary:
        assert 'reject_pc' in case
    else:
        assert 'reject_pc' not in case, ('unreached rejection boundary', case)
    return {bounds: bytes(data) for bounds, data in expected.items()}, events


def expected_registers(state):
    case = state.case
    registers = state.supplied_registers.copy()
    registers[2] = 0 if case['stall'] == 1 else case['stall']
    registers[6], registers[8], registers[10], registers[11] = 512, LATCH, 256, OBSERVED
    # The <=512 branch leaves a9 as the OUT1 address. The modified command
    # value is in a8, which the final LATCH literal load then overwrites.
    registers[9] = OUT1 if case['available'] <= 512 else case['available']
    return registers


def qemu_memory_event(state, q):
    pc = q.reg(0)
    if not START <= pc < END:
        return None  # The existing executor rejects before any instruction.
    op, args, raw = state.program.instruction(pc)
    guard_memory(state, q, op, args)
    base = op.removesuffix('.n')
    sizes = {'l8ui': 1, 'l32i': 4, 's8i': 1, 's32i': 4}
    ar = lambda n: q.reg(((q.reg(38) * 4 + n) % 32) + 1)
    if base == 'l32r':
        address, size, kind = args[1], 4, 'read'
    elif base in sizes:
        address, size = (ar(args[1]) + args[2]) & 0xffffffff, sizes[base]
        kind = 'read' if base.startswith('l') else 'write'
    else:
        return None
    value = int.from_bytes(q.read(address, size), 'big') if kind == 'read' else ar(args[0]) & ((1 << (8 * size)) - 1)
    return access(pc, kind, address, size, value)


def execute(program, case, q, capture):
    state = RetirementRAM(program, case)
    engine = 'interpreter' if q is None else 'qemu'
    directory = capture / case['name']
    directory.mkdir(exist_ok=True)
    stem = directory / engine
    before = snapshot(state)
    expected, expected_events = oracle(before, case)
    stop = case.get('reject_pc', END)
    supplied = dict(case=case, entry=hex(state.pc), stop_before=hex(stop),
        logical_registers={f'a{i}': hex(value) for i, value in enumerate(state.supplied_registers)},
        private_literal_redirects={hex(at): dict(original=hex(original), ram=hex(image))
            for at, (original, image) in REDIRECTS.items() if at != case.get('skip_literal')})
    stem.with_suffix('.input.json').write_text(json.dumps(supplied, indent=2, sort_keys=True) + '\n')
    for suffix, memory in (('before', before), ('expected', expected)):
        stem.with_suffix('.' + suffix + '.bin').write_bytes(b''.join(data for _, data in sorted(memory.items())))
    runner, failure = None, None
    try:
        if q is None:
            state.recording = True
            state.run(budget=160)
        else:
            q.load(program.path)
            runner = NativeTasks(q, state, EMPTY_FIXTURE, CODE, (), instruction_budget=160)
            runner.synchronize(True)
            q.reset_cpu(state.pc)
            for index, value in enumerate(state.supplied_registers, 1):
                q.set_reg(index, value)
            while True:
                state.pc = q.reg(0)
                event = qemu_memory_event(state, q)
                runner.step()
                if event is not None:
                    state.events.append(event)
    except Exception as error:
        failure = dict(type=type(error).__name__, reason=str(error), pc=hex(state.pc))
    finally:
        state.recording = False
        if runner is not None:
            runner.synchronize(False)
            state.registers = [q.reg(((q.reg(38) * 4 + i) % 32) + 1) for i in range(16)]
    actual = snapshot(state)
    stem.with_suffix('.after.bin').write_bytes(b''.join(data for _, data in sorted(actual.items())))
    visited = state.visited if runner is None else runner.visited
    result = dict(status='captured_unchecked', engine=engine, entry=hex(case.get('entry', START)),
        stop_before=hex(stop), failure=failure, registers=[hex(v) for v in state.registers],
        expected_registers=None if 'reject_pc' in case else [hex(v) for v in expected_registers(state)],
        before_memory=manifest(before), expected_memory=manifest(expected), actual_memory=manifest(actual),
        expected_accesses=expected_events, accesses=state.events,
        setup_record_hex=state.bytes_at(SETUP, 16).hex(), observed_record_hex=state.bytes_at(OBSERVED, 16).hex(),
        other_record_hex=state.bytes_at(OTHER, 16).hex(),
        original_instructions_retired=[hex(pc) for pc in sorted(visited - {stop})],
        engine_steps=state.steps if runner is None else runner.steps)
    # Preserve all available raw bytes/events before any success assertion.
    stem.with_suffix('.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    reason = 'MMIO forbidden' if 'reject_pc' in case else (
        'execution outside selected stock routines: ' if q is None else 'native tasks left selected code: ') + hex(END)
    assert failure == dict(type='ValueError', reason=reason, pc=hex(stop)), (case, engine, failure)
    if runner is not None:
        assert q.reg(0) == stop and stop not in runner.visited
        assert q.reg(38) == 0 and q.reg(39) == 1 and not runner.services
    assert actual == expected, (case['name'], engine, 'all mutable RAM including stack/guards')
    assert state.events == expected_events, (case['name'], engine, 'independent ordered reads/writes')
    if 'reject_pc' not in case:
        assert state.registers == expected_registers(state), (case, engine, 'independent final registers')
    assert not set(EXCLUDED) & (visited - {stop})
    assert sha(state.bytes_at(START, END - START)) == CODE_SHA
    if q is not None:
        assert q.read(START, END - START) == state.bytes_at(START, END - START)
    result.update(status='pass', all_mutable_and_guard_ram_equal=True,
        independent_ordered_read_and_write_trace_equal=True, original_code_unchanged=True,
        independent_final_registers_checked='reject_pc' not in case, actual_peripheral_accesses=0)
    stem.with_suffix('.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    return result


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
    return sorted(found | {ROOT / 'analysis/sihp1020.elf', *(REF / name for name in REFERENCE_SHA)})


def audit(program, blob):
    assert sha(blob) == STOCK_SHA
    sections, _ = properties(blob)
    raw = section_bytes(blob, sections, START, END - START)
    assert len(raw) == 210 and sha(raw) == CODE_SHA
    pc, instructions = START, {}
    allowed = {'l32i', 'l8ui', 's32i', 's8i', 'l32r', 'movi', 'mov',
               'slli', 'or', 'and', 'memw', 'bltu', 'bnei', 'bne'}
    while pc < END:
        op, args, encoded = program.instruction(pc)
        assert op.removesuffix('.n') in allowed and pc + len(encoded) <= END, (hex(pc), op)
        assert encoded == section_bytes(blob, sections, pc, len(encoded))
        instructions[hex(pc)] = dict(op=op, args=args, bytes=encoded.hex())
        pc += len(encoded)
    assert pc == END
    for pc, (op, args, encoded) in ANCHORS.items():
        assert program.instruction(pc) == (op, args, bytes.fromhex(encoded))
        assert section_bytes(blob, sections, pc, len(bytes.fromhex(encoded))).hex() == encoded
    original = Machine(program)
    for pc, value in LITERALS.items():
        assert original.read(pc, 4) == value
    for name, digest in REFERENCE_SHA.items():
        assert sha((REF / name).read_bytes()) == digest
    provenance = json.loads((REF / 'provenance.json').read_bytes())
    assert provenance['commit'] == LINUX_COMMIT
    header = (REF / 'amd5536udc.h').read_text()
    for name, value in (('UDC_EPCTL_S', 0), ('UDC_EPCTL_CNAK', 8),
                        ('UDC_DMA_STP_STS_BS_HOST_READY', 0), ('UDC_DMA_STP_STS_BS_DMA_DONE', 2)):
        assert re.search(r'^#define\s+' + name + r'\s+' + str(value) + r'\s*$', header, re.M)
    return dict(begin=hex(START), end=hex(END), bytes=raw.hex(), sha256=CODE_SHA,
        instructions=instructions, extra_anchors={hex(k): v for k, v in ANCHORS.items()},
        literal_originals={hex(k): hex(v) for k, v in LITERALS.items()},
        linux_commit=LINUX_COMMIT, linux_source_sha256=REFERENCE_SHA,
        linux_control_out_isr_url=f'https://github.com/torvalds/linux/blob/{LINUX_COMMIT}/drivers/usb/gadget/udc/snps_udc_core.c#L2422-L2610')


def reject_excluded(program, q, capture):
    state = RetirementRAM(program, base_case('excluded', 204))
    before = snapshot(state)
    q.load(program.path)
    runner = NativeTasks(q, state, EMPTY_FIXTURE, CODE, (), instruction_budget=1)
    runner.synchronize(True)
    q.reset_cpu(START)
    rows = []
    for pc in EXCLUDED:
        state.pc, state.steps, state.visited = pc, 0, set()
        try:
            state.run(budget=1)
        except ValueError as error:
            assert str(error) == f'execution outside selected stock routines: {pc:#x}'
        else:
            raise AssertionError(f'excluded interpreter instruction ran: {pc:#x}')
        assert state.steps == 0 and not state.visited
        q.set_reg(0, pc)
        try:
            runner.step()
        except ValueError as error:
            assert str(error) == f'native tasks left selected code: {pc:#x}'
        else:
            raise AssertionError(f'excluded QEMU instruction ran: {pc:#x}')
        assert runner.steps == 0 and not runner.visited and q.reg(0) == pc
        rows.append(dict(pc=hex(pc), status='rejected before instruction execution in both engines'))
    runner.synchronize(False)
    assert snapshot(state) == before
    (capture / 'excluded-code.json').write_text(json.dumps(rows, indent=2) + '\n')
    return rows


def main():
    stock = ROOT / 'analysis/sihp1020.elf'
    assert stock.is_file(), 'Run from the repository or set HP1020_ROOT explicitly.'
    capture = Path(tempfile.mkdtemp(prefix='hp1020-setup-retirement-', dir='/tmp'))
    print('SETUP retirement captures: ' + str(capture), flush=True)
    sources, origins = {}, {}
    for path in source_paths():
        try:
            name = str(path.relative_to(ROOT))
        except ValueError:
            name = 'draft/' + path.name
        assert name not in sources
        sources[name], origins[name] = sha(path.read_bytes()), str(path)
        saved = capture / 'source' / name
        saved.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, saved)
        assert sha(saved.read_bytes()) == sources[name]
    (capture / 'source-sha256.json').write_text(json.dumps(sources, indent=2, sort_keys=True) + '\n')
    (capture / 'source-origins.json').write_text(json.dumps(origins, indent=2, sort_keys=True) + '\n')
    program = Program(stock, os.environ.get('XTENSA_PREFIX', '/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf'))
    evidence = audit(program, stock.read_bytes())
    (capture / 'original-byte-audit.json').write_text(json.dumps(evidence, indent=2, sort_keys=True) + '\n')
    results = []
    with QemuRAM() as q:
        version = q.version
        for case in case_specs():
            a, b = execute(program, case, None, capture), execute(program, case, q, capture)
            for key in ('entry', 'stop_before', 'registers', 'expected_registers', 'before_memory',
                        'expected_memory', 'actual_memory', 'expected_accesses', 'accesses',
                        'setup_record_hex', 'observed_record_hex', 'other_record_hex', 'original_instructions_retired'):
                assert a[key] == b[key], (case['name'], key)
            results.append(dict(input=case, interpreter=a, qemu=b, status='pass'))
            print(f'SETUP retirement: {len(results)} conditional/control cases passed', flush=True)
        excluded = reject_excluded(program, q, capture)
    assert all(sha(Path(origins[name]).read_bytes()) == digest for name, digest in sources.items()), 'source changed during execution'
    counts = dict(primary_linked=32, rx_low_bits=8, unsigned_count=4, noncanonical_stall=2,
                  mismatched_records=4, removed_redirect=8, escaped_pointer=6, standalone_mmio=18)
    kinds = ('primary_linked_records', 'owner_only_rx_and_low_bits_control', 'unsigned_available_boundary',
             'noncanonical_stall_intent_is_not_one', 'conditional_mismatched_observed_and_target_records',
             'removed_literal_redirect', 'peripheral_pointer_escape', 'standalone_peripheral_instruction')
    assert [sum(row['input']['kind'] == kind for row in results) for kind in kinds] == list(counts.values())
    assert len(results) == 82 and len(excluded) == 15
    report = dict(status='pass', cases=results, counts=counts, excluded_code_controls=excluded,
        source_sha256=sources, source_origins=origins, stock_elf_sha256=STOCK_SHA, qemu_version=version,
        original_byte_audit=evidence, private_literal_redirects={hex(k): dict(original=hex(v[0]), ram=hex(v[1])) for k, v in REDIRECTS.items()},
        original_entry_executed=False, omitted_startup_admission_dispatch_and_sender=True, supplied_services=[],
        completed_usb_control_transfers=0, completed_native_page_lifecycles=0, actual_peripheral_accesses=0,
        hardware_stall_clear_established=False, controller_rearm_or_quiescence_established=False,
        scope='Original post-dispatch tail, conditional on supplied a2 stall intent, a3 zero, globals and ordinary RAM control images. Exact SETUP-status return, separate owner-only OUT0 header reset, CNAK command intent and idle-latch clear; all mutable RAM, registers and ordered reads/writes agree in both engines.',
        limits='No ENTRY, request admission/dispatch, sender, IRQ, event wait, timer, cache, controller or physical USB operation executes. Four original peripheral-address literals are redirected only in private executor RAM. Stores are plain RAM writes, not W1C or self-clearing hardware commands. This tail preserves an existing S bit; CNAK does not prove stall clearing or transfer settlement. Mismatched observed/target record controls expose a supplied original pointer assumption, not a recommended port policy. Owner-only OUT0 rearm does not validate RX/count or establish safe reuse. Current SETUP bytes and older EP0 packet ownership remain separate responsibilities. Physical mapping, event ordering, rearm, stalls/toggles, cancellation, boot and printing remain unproved.')
    text = json.dumps(report, indent=2, sort_keys=True) + '\n'
    markdown = '# Original SETUP retirement and OUT0 rearm intent\n\n' + report['scope'] + '\n\n' + (
        '50 conditional tail profiles and32 pre-peripheral guard profiles per engine;15 excluded PCs. '
        'These are zero completed physical transfers.\n\n') + report['limits'] + '\n'
    (capture / 'report.json').write_text(text)
    (capture / 'report.md').write_text(markdown)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.with_suffix('.json').write_text(text)
    OUT.with_suffix('.md').write_text(markdown)
    print('SETUP retirement capture complete: ' + str(capture), flush=True)


if __name__ == '__main__':
    main()
