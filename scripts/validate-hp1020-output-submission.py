#!/usr/bin/env python3
"""Stock output pointer/count fragments, stopped before every peripheral access.

This is a deliberately separate, synthetic selected-pointer experiment. It does
not repeat parser/ring delivery, supply readiness, redirect a video register,
execute a video store, or establish pixel packing/polarity. Every phase starts
with the original ENTRY followed by an explicit register/cut precondition.
"""
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace

from hp1020_xtensa_call0 import Program, Machine, STOP, STACK, STACK_SIZE
from hp1020_stock_stop import StopRAM
from hp1020_qemu_pipeline import start
from hp1020_qemu_multitask import NativeTasks
from hp1020_qemu_ram import QemuRAM
from hp1020_qemu_stock_parser import VECTORS


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'analysis/hardware-boundary/output-submission'
STOCK_SHA = '2111560068db47ceca21fa550db4c7c34f5595b5a5d137ae4a19631e40e3601d'
ENTRY = 0x10013f34
DIVIDE = (0x1001b668, 0x1001b6b0)
DIVIDE_SHA = '028e0472d3e3219fcfed48e69cb2d48c43e49df8458aa068134650f954e48a93'
ARENA, ARENA_SIZE = 0x22700000, 0x10000
VIDEO, DESC, BUFFER = ARENA + 0x100, ARENA + 0x400, ARENA + 0x1000
EMPTY_FIXTURE = SimpleNamespace(path=None, execute_ranges=[])

# End addresses are exclusive and are themselves excluded instruction starts.
# In particular, no video store is executed even against a redirected RAM sink.
PHASES = {
    'single_pointer': (0x10014014, 0x100140ac,
                       [(0x10014014, 0x1001402b), (0x100140a1, 0x100140ac)]),
    'single_count': (0x100140ae, 0x100140c7, [(0x100140ae, 0x100140c7), DIVIDE]),
    'dual_pointer_a': (0x10014014, 0x1001402b, [(0x10014014, 0x1001402b)]),
    'dual_pointer_b': (0x1001402d, 0x10014037, [(0x1001402d, 0x10014037)]),
    'dual_quotient': (0x10014039, 0x10014052, [(0x10014039, 0x10014052), DIVIDE]),
    # The omitted instruction at 0x10014052 reads hardware. The following OR
    # consumes only the already-observed quotient and normalized terminal bits.
    # Stop before the readiness branch; no synthetic ready value is supplied.
    'dual_count': (0x10014054, 0x10014057, [(0x10014054, 0x10014057)]),
}
EXCLUDED = (0x10013f4c, 0x10013ff9, 0x1001402b, 0x10014037,
            0x10014052, 0x10014063, 0x10014071, 0x10014076,
            0x10014083, 0x1001409c, 0x100140ac, 0x100140c7,
            0x100140eb, 0x10015648)

# These are independent byte anchors, including excluded stores/reads. Auditing
# an instruction is not permission to put it in an executable range.
ANCHORS = {
    ENTRY: ('entry', (1, 32), '6c1004'),
    0x10013f5c: ('movi.n', (4, 0), 'c040'),
    0x10014014: ('l32r', (8, 0x100067c8), '18c9ed'),
    0x10014019: ('beqi', (6, 1, 0x1001401f), '686102'),
    0x1001401f: ('l32r', (8, 0x100067cc), '18c9eb'),
    0x10014025: ('l32r', (9, 0x100067d0), '19c9ea'),
    0x1001402b: ('s32i.n', (12, 8, 0), '9c80'),
    0x1001402d: ('l32i', (8, 7, 188), '28722f'),
    0x10014037: ('s32i.n', (8, 9, 0), '9890'),
    0x10014039: ('srli', (10, 10, 1), '0a1a14'),
    0x1001403f: ('call8', (DIVIDE[0],), '581d8a'),
    0x10014047: ('moveqz', (6, 4, 8), '084638'),
    0x10014052: ('l32i.n', (9, 11, 0), '89b0'),
    0x10014054: ('or', (10, 10, 8), '08aa02'),
    0x10014068: ('l32r', (8, 0x100067d4), '18c9db'),
    0x10014071: ('s32i.n', (10, 8, 0), '9a80'),
    0x100140a1: ('l32r', (8, 0x100067cc), '18c9ca'),
    0x100140ac: ('s32i.n', (12, 8, 0), '9c80'),
    0x100140b1: ('call8', (DIVIDE[0],), '581d6d'),
    0x100140b8: ('moveqz', (8, 4, 9), '094838'),
    0x100140be: ('l32r', (9, 0x100067d4), '19c9c5'),
    0x100140c1: ('or', (10, 10, 8), '08aa02'),
    0x100140c7: ('s32i.n', (10, 9, 0), '9a90'),
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def source_paths():
    """Snapshot this script and the local Python dependency closure, lazies too."""
    pending = [Path(__file__).resolve()]
    found = set()
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
    return sorted(found)


class SubmissionRAM(StopRAM):
    def after_instruction(self, pc, nxt):
        nxt = super().after_instruction(pc, nxt)
        if pc == ENTRY:
            # Registers a0/a1 belong to the original prologue/ABI. Every other
            # logical register is initialized explicitly, then required inputs
            # are supplied. The omitted prefix is never claimed as executed.
            self.registers[2:] = [0] * 14
            for reg, value in self.cut_registers.items():
                self.registers[reg] = value
            nxt = self.resume
        if nxt == self.boundary:
            self.stopped_at = nxt
            return STOP
        return nxt


def ar(q, index):
    return q.reg(((q.reg(38) * 4 + index) % 32) + 1)


def memory(program, case):
    state = SubmissionRAM(program, ENTRY, [(ENTRY, ENTRY + 3)], [(ARENA, ARENA_SIZE)])
    state.put(ARENA, bytes([case['fill']]) * ARENA_SIZE)
    pointer = BUFFER + case['pointer_offset']
    # Distinct nonuniform bytes make unintended writes/repacking observable,
    # without assigning any physical or decoded-pixel meaning to this fixture.
    state.put(pointer, bytes(((i * 29 + 17) ^ case['fill']) & 255 for i in range(8192)))
    for address, value in ((VIDEO + 0xb8, case['stride']),
                           (VIDEO + 0xbc, case['window']),
                           (VIDEO + 0xc4, case['divisor']),
                           (DESC, 1), (DESC + 4, case['final']), (DESC + 8, case['rows'])):
        state.write(address, 4, value)
    selector_cell = state.read(0x100067c8, 4)
    assert selector_cell == 0x1001cdac and state.read(selector_cell, 4) == 2
    if case['dual']:
        state.write(selector_cell, 4, 1)  # Explicit conditional control, RAM only.
    return state, pointer


def protected_memory(state):
    # Stack frames legitimately differ between the abstract interpreter and
    # QEMU's register windows. Every other mutable byte must remain unchanged.
    return [(begin, end, state.bytes_at(begin, end - begin))
            for begin, end in state.write_ranges
            if not (STACK <= begin and end <= STACK + STACK_SIZE)]


def run_fragment(state, q, name, inputs, observations):
    resume, boundary, ranges = PHASES[name]
    state.code_ranges = [(ENTRY, ENTRY + 3)] + ranges + VECTORS
    state.cut_registers = dict(inputs)
    state.resume, state.boundary = resume, boundary
    before = protected_memory(state)
    if q is None:
        state.pc, state.steps = ENTRY, 0
        state.registers = [0] * 16
        state.registers[0], state.registers[1] = STOP, STACK + STACK_SIZE - 16
        state.frames, state.loop, state.sar = [], None, 0
        state.visited.clear()
        state.run(budget=1000)
        assert state.stopped_at == boundary
        observed = {key: state.registers[reg] for key, reg in observations.items()}
        visited, steps = state.visited.copy(), state.steps
    else:
        runner = start(q, state, EMPTY_FIXTURE, ENTRY, (), instruction_budget=1000)
        cut_pending = True
        while q.reg(0) != boundary:
            if cut_pending and q.reg(0) == ENTRY + 3:
                assert ENTRY in runner.visited
                for reg in range(2, 16):
                    q.set_reg(((q.reg(38) * 4 + reg) % 32) + 1, inputs.get(reg, 0))
                q.set_reg(0, resume)
                cut_pending = False
                continue
            runner.step()
        assert not cut_pending and not runner.services
        observed = {key: ar(q, reg) for key, reg in observations.items()}
        runner.synchronize(False)
        visited, steps = runner.visited.copy(), runner.steps
    assert ENTRY in visited and resume in visited and boundary not in visited
    assert not (visited & set(EXCLUDED))
    for begin, end, original in before:
        assert state.bytes_at(begin, end - begin) == original, (name, hex(begin), 'memory changed')
    return dict(phase=name, original_entry=hex(ENTRY), resume=hex(resume), stop_before=hex(boundary),
                supplied_registers={f'a{r}': v for r, v in sorted(inputs.items())},
                other_a2_through_a15_zero=True, observed=observed, steps=steps,
                divide_executed=DIVIDE[0] in visited,
                visited=[hex(pc) for pc in sorted(visited)], all_nonstack_ram_unchanged=True)


def reject_boundaries(state, q):
    rejected = []
    before = protected_memory(state)
    for pc in EXCLUDED:
        if q is None:
            state.pc, state.steps = pc, 0
            prior = state.visited.copy()
            try:
                state.run(budget=1)
            except ValueError as error:
                assert str(error) == f'execution outside selected stock routines: {pc:#x}'
            else:
                raise AssertionError(f'excluded instruction executed: {pc:#x}')
            assert state.steps == 0 and state.pc == pc and state.visited == prior
        else:
            q.set_reg(0, pc)
            runner = NativeTasks(q, state, EMPTY_FIXTURE, state.code_ranges, instruction_budget=1)
            try:
                runner.step()
            except ValueError as error:
                assert str(error) == f'native tasks left selected code: {pc:#x}'
            else:
                raise AssertionError(f'QEMU executed excluded instruction: {pc:#x}')
            assert runner.steps == 0 and q.reg(0) == pc
        rejected.append(hex(pc))
    for begin, end, original in before:
        assert state.bytes_at(begin, end - begin) == original
    return rejected


def oracle(case, pointer):
    numerator = case['rows'] // 2 if case['dual'] else case['rows']
    # Original helper's documented divisor-zero result, not a recommended
    # production policy. An eventual adapter should reject invalid geometry.
    quotient = numerator // case['divisor'] if case['divisor'] else 0
    result = dict(pointer_a=pointer, count_flags=quotient | (0x1000000 if case['final'] else 0))
    if case['dual']:
        result['pointer_b'] = pointer + case['window']
    return result


def execute(program, q, case, captures):
    state, pointer = memory(program, case)
    arena_before = state.bytes_at(ARENA, ARENA_SIZE)
    phases = []
    inputs = {4: 0, 5: DESC, 7: VIDEO, 12: pointer}
    if not case['dual']:
        first = run_fragment(state, q, 'single_pointer', inputs,
                             dict(address=8, pointer=12, rows=10, divisor=11))
        phases.append(first)
        values = first['observed']
        assert values == dict(address=0xb1000008, pointer=pointer,
                              rows=case['rows'], divisor=case['divisor'])
        second = run_fragment(state, q, 'single_count',
                              {4: 0, 5: DESC, 10: values['rows'], 11: values['divisor']},
                              dict(address=9, count_flags=10))
        phases.append(second)
        assert second['divide_executed'] and second['observed']['address'] == 0xb100000c
        observed = dict(pointer_a=values['pointer'], count_flags=second['observed']['count_flags'])
    else:
        first = run_fragment(state, q, 'dual_pointer_a', inputs,
                             dict(address_a=8, pointer_a=12, address_b=9, divisor=11, selector=6))
        phases.append(first)
        values = first['observed']
        assert values == dict(address_a=0xb1000008, pointer_a=pointer, address_b=0xb1000108,
                              divisor=case['divisor'], selector=1)
        second = run_fragment(state, q, 'dual_pointer_b',
                              {5: DESC, 7: VIDEO, 9: values['address_b'], 12: values['pointer_a']},
                              dict(address=9, pointer=8, rows=10))
        phases.append(second)
        assert second['observed']['address'] == 0xb1000108
        assert second['observed']['rows'] == case['rows']
        third = run_fragment(state, q, 'dual_quotient',
                             {4: 0, 5: DESC, 6: values['selector'],
                              10: second['observed']['rows'], 11: values['divisor']},
                             dict(quotient=10, terminal_bits=8))
        phases.append(third)
        assert third['divide_executed']
        fourth = run_fragment(state, q, 'dual_count',
                              {8: third['observed']['terminal_bits'], 10: third['observed']['quotient']},
                              dict(count_flags=10))
        phases.append(fourth)
        observed = dict(pointer_a=values['pointer_a'], pointer_b=second['observed']['pointer'],
                        count_flags=fourth['observed']['count_flags'])
    expected = oracle(case, pointer)
    assert observed == expected, (case, observed, expected)
    assert state.bytes_at(ARENA, ARENA_SIZE) == arena_before
    rejected = reject_boundaries(state, q)
    name = 'interpreter' if q is None else 'qemu'
    (captures / f'{case["name"]}-{name}.bin').write_bytes(state.bytes_at(ARENA, ARENA_SIZE))
    record = dict(engine=name, status='pass', observed=observed, oracle=expected, phases=phases,
                  arena_sha256=sha(arena_before), all_nonstack_ram_unchanged=True,
                  rejected_before_execution=rejected, peripheral_instructions_executed=0)
    (captures / f'{case["name"]}-{name}.json').write_text(json.dumps(record, indent=2) + '\n')
    return record


def cases():
    # rows, divisor, final, stride/window, selected buffer offset. These are
    # supplied geometry controls, not proven model/media support or lifecycles.
    single = [(1, 1, 1, 1200, 0), (4, 1, 0, 1200, 8192),
              (4, 1, 7, 1200, 24576), (17, 1, 1, 4, 0),
              (3, 2, 1, 2400, 8192), (3, 0, 1, 1200, 0), (0, 1, 0, 1200, 0),
              (0x1000001, 1, 1, 1200, 0)]
    dual = [(4, 1, 0, 1200, 0), (4, 1, 7, 1200, 8192),
            (1, 1, 1, 1200, 24576), (3, 2, 1, 2400, 0),
            (17, 2, 1, 4, 8192), (4, 0, 1, 1200, 0), (0x2000002, 1, 1, 1200, 0)]
    for is_dual, controls in ((False, single), (True, dual)):
        for index, (rows, divisor, final, window, offset) in enumerate(controls):
            for fill in (0, 204):
                yield dict(name=f'{"dual" if is_dual else "single"}-{index}-fill-{fill}',
                           dual=is_dual, rows=rows, divisor=divisor, final=final,
                           stride=window, window=window, pointer_offset=offset, fill=fill,
                           selector_source='explicit_RAM_value_1' if is_dual else 'file_backed_value_2',
                           geometry_source='supplied_arithmetic_controls',
                           zero_divisor_control=divisor == 0,
                           count_flag_overlap_control=rows >= 0x1000000)


def main():
    capture = Path(tempfile.mkdtemp(prefix='hp1020-output-submission-', dir='/tmp'))
    print(f'Output submission captures: {capture}', flush=True)
    sources = {str(path.relative_to(ROOT)): sha(path.read_bytes()) for path in source_paths()}
    for name in sources:
        saved = capture / 'source' / name
        saved.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, saved)
    (capture / 'source-sha256.json').write_text(json.dumps(sources, indent=2) + '\n')
    stock = ROOT / 'analysis/sihp1020.elf'
    assert sha(stock.read_bytes()) == STOCK_SHA
    prefix = os.environ.get('XTENSA_PREFIX', '/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf')
    program = Program(stock, prefix)
    original = Machine(program)
    audited = []
    for begin, end in ((ENTRY, ENTRY + 3), (0x10014014, 0x100140f8), DIVIDE):
        data, offset = original.span(begin, end - begin, execute=True)
        raw = bytes(data[offset:offset + end - begin])
        if (begin, end) == DIVIDE:
            assert sha(raw) == DIVIDE_SHA
        audited.append(dict(begin=hex(begin), end=hex(end), sha256=sha(raw), bytes=raw.hex()))
    for pc, (op, args, encoded) in ANCHORS.items():
        raw = bytes.fromhex(encoded)
        assert program.instruction(pc) == (op, args, raw), hex(pc)
        data, offset = original.span(pc, len(raw), execute=True)
        assert bytes(data[offset:offset + len(raw)]) == raw
    literals = {pc: original.read(pc, 4) for pc in (0x100067c8, 0x100067cc, 0x100067d0, 0x100067d4)}
    assert literals == {0x100067c8: 0x1001cdac, 0x100067cc: 0xb1000008,
                        0x100067d0: 0xb1000108, 0x100067d4: 0xb100000c}
    assert original.read(literals[0x100067c8], 4) == 2
    rows = []
    with QemuRAM() as q:
        version = q.version
        for case in cases():
            interpreted = execute(program, None, case, capture)
            native = execute(program, q, case, capture)
            assert interpreted['observed'] == native['observed']
            assert interpreted['arena_sha256'] == native['arena_sha256']
            assert [p['observed'] for p in interpreted['phases']] == [p['observed'] for p in native['phases']]
            for audit in audited:
                raw = bytes.fromhex(audit['bytes'])
                assert q.read(int(audit['begin'], 16), len(raw)) == raw
            rows.append(dict(case=case, interpreter=interpreted, qemu=native))
            if len(rows) % 10 == 0:
                print(f'Output submission: {len(rows)} cases agree', flush=True)
    assert sha(stock.read_bytes()) == STOCK_SHA
    assert all(sha((ROOT / name).read_bytes()) == digest for name, digest in sources.items()), 'source changed during execution'
    report = dict(status='pass', cases=rows, stock_elf_sha256=STOCK_SHA,
                  source_sha256=sources, qemu_version=version, original_byte_ranges=audited,
                  instruction_anchors={hex(pc): dict(op=op, args=args, bytes=encoded)
                                       for pc, (op, args, encoded) in ANCHORS.items()},
                  literals={hex(pc): hex(value) for pc, value in literals.items()},
                  completed_native_page_lifecycles=0, usb_transfers=0, peripheral_instructions_executed=0,
                  scope='Original pointer/count construction after an explicitly supplied selected-pointer boundary. Single-output pointer and flags stop before their stores; dual pointers and common count are conditional cuts before readiness handling.',
                  limits='No readiness result, video-store redirect, peripheral instruction, pixel transform, packing/polarity, cache visibility, engine operation, hardware acceptance or physical completion is supplied or proven. Each phase has a fresh original ENTRY and explicit a-register inputs; omitted stores/prefixes do not execute. Geometry and buffer ownership are supplied. Divisor-zero results describe the original helper only and are not recommended adapter behavior. Dual lane-B flags/readiness remain excluded.')
    OUT.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(report, indent=2, sort_keys=True) + '\n'
    (capture / 'report.json').write_text(text)
    OUT.with_suffix('.json').write_text(text)
    OUT.with_suffix('.md').write_text('# Original output-submission arithmetic\n\n'
        + f'{len(rows)} original-byte cases agree between the bounded interpreter and independent QEMU. Zero completed page lifecycles.\n\n'
        + report['scope'] + '\n\n' + report['limits'] + '\n')
    print(f'Output submission: {len(rows)} cases passed; no peripheral instruction executed', flush=True)


if __name__ == '__main__':
    main()
