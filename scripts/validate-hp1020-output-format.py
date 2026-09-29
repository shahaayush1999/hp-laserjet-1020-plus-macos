#!/usr/bin/env python3
"""Original bypass table and mask arithmetic, stopped before video accesses.

This is a conditional format-value experiment, not a video-register emulator.
No peripheral instruction, redirected video access, readiness result, custom
opcode, output submission, or physical pixel interpretation is included. Each
fragment executes a fresh original ENTRY before an explicit register/PC cut.
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
OUT = ROOT / 'analysis/hardware-boundary/output-format'
STOCK_SHA = '2111560068db47ceca21fa550db4c7c34f5595b5a5d137ae4a19631e40e3601d'
ENTRY = 0x10014910
ARENA, ARENA_SIZE = 0x22700000, 0x10000
WORK, BUFFER = ARENA + 0x100, ARENA + 0x1000
VIDEO, SELECTOR, COUNTER = 0x1002efc0, 0x1001cdac, 0x1001eac8
EMPTY_FIXTURE = SimpleNamespace(path=None, execute_ranges=[])

# These numeric expectations are independent of the executed address arithmetic.
# In particular, selector 2 must not reuse selector 0's table merely because
# both selectors take the separate single-output submission branch.
TABLE_WORDS = {
    (1, 0): (0, 0xffffffff),
    (1, 1): (0, 0xffffffff),
    (1, 2): (0, 0x1f),
    (2, 0): (0, 0x1f, 0x1ff, 0x1fff),
    (2, 1): (0, 0x7f80, 0x7fff8, 0x3fffff),
    (2, 2): (0, 7, 0x1f, 0x7f),
}
TABLE_ADDRESSES = (0xb1000400, 0xb1000410, 0xb1000420, 0xb1000430)
LITERALS = {
    0x10006770: VIDEO, 0x100067c8: SELECTOR, 0x10006840: COUNTER,
    0x10006894: TABLE_ADDRESSES[0], 0x100068a4: TABLE_ADDRESSES[1],
    0x100068cc: 0x10005550, 0x100068bc: 0x10005540,
    0x10006898: 0xfcffffff, 0x1000689c: 0x03000000,
    0x10006808: 0xb1000000, 0x1000680c: 0xb1000100,
    0x10005c88: 0x01000000, 0x100068e0: 0xb1000014,
    0x100068e4: 0xffff, 0x100068e8: 0xb1000114,
}
BYTE_RANGES = (
    (ENTRY, ENTRY + 3, True,
     'f089ca09d7f9ed1d307b86358078f267a098a8fbd704a7e6fb151c193605d923'),
    (0x10014e18, 0x1001506d, True,
     '14df5c493a590caf66db9692f0f0408ecd45f9a2ad75d498dfdd38999e941b32'),
    (0x100151aa, 0x100151d8, True,
     '5b8d647f6b33836d9752cf26e5367cafe0334254acdcd685c65d093e3323ff7b'),
    (0x10005540, 0x10005580, False,
     'c2168bb176b035baf70f17ecc7963005e8feb323065a152639bc9a455cb8a21e'),
)

# Every end is exclusive. The 600 dpi table paths below include RAM loads and
# the original RAM scratch-counter stores, but contain no peripheral access.
TABLE_RANGES = [(0x10014e89, 0x10014e9b), (0x10014ebd, 0x10014ed5),
                (0x10014ef9, 0x10014f1c), (0x10014f30, 0x10014f48),
                (0x10014fb8, 0x10014fcf), (0x1001501c, 0x10015057)]
TABLE_CONTINUE = [(0x10015059, 0x1001506d), (0x10015039, 0x10015057)]
MASK_PREFIX = [(0x10014e18, 0x10014e2a), (0x10014e49, 0x10014e66)]
EXCLUDED = (0x10014bb8, 0x10014bd8, 0x10014bf3,
            0x10014e01, 0x10014e2a, 0x10014e35, 0x10014e3a, 0x10014e43,
            0x10014e66, 0x10014e77, 0x10014e7c, 0x10014e87,
            0x10014ee5, 0x10014eea, 0x10014f1c, 0x10014f21,
            0x10014f48, 0x10014f4e, 0x10014f9f, 0x10015001, 0x10015057,
            0x10015076, 0x100151a8, 0x100151c1, 0x100151c7, 0x100151d6,
            0x100151eb, 0x10013ff9, 0x10015648)
ANCHORS = {
    ENTRY: ('entry', (1, 48), '6c1006'),
    0x10014e1b: ('l32i', (8, 8, 200), '288232'),
    0x10014e1e: ('bnei', (8, 1, 0x10014e49), '698127'),
    0x10014e2a: ('l32i.n', (8, 10, 0), '88a0'),
    0x10014e2f: ('and', (8, 8, 11), '0b8801'),
    0x10014e35: ('s32i.n', (8, 10, 0), '98a0'),
    0x10014e4f: ('l32r', (12, 0x10005c88), '1cc38e'),
    0x10014e66: ('l32i.n', (8, 11, 0), '88b0'),
    0x10014e68: ('xor', (9, 9, 10), '0a9903'),
    0x10014e6e: ('and', (8, 8, 9), '098801'),
    0x10014e71: ('or', (8, 8, 12), '0c8802'),
    0x10014e77: ('s32i.n', (8, 11, 0), '98b0'),
    0x10014e89: ('l16ui', (8, 4, 34), '284111'),
    0x10014ec6: ('l32r', (8, 0x100067c8), '18c640'),
    0x10014eff: ('bnei', (8, 2, 0x10014f30), '69822d'),
    0x10014f33: ('l32r', (9, 0x100068bc), '19c662'),
    0x10014f3b: ('addx8', (8, 8, 9), '09880b'),
    0x10014f3e: ('l32i.n', (9, 8, 0), '8980'),
    0x10014f43: ('l32i.n', (8, 8, 4), '8881'),
    0x10014f48: ('s32i', (9, 11, 0), '29b600'),
    0x10014f4e: ('s32i', (8, 10, 0), '28a600'),
    0x10015024: ('s32i.n', (8, 10, 0), '98a0'),
    0x10015033: ('l32r', (13, 0x100068cc), '1dc626'),
    0x10015048: ('slli', (9, 9, 4), '0c9911'),
    0x1001504b: ('addx4', (8, 8, 9), '09880a'),
    0x10015050: ('l32i.n', (8, 8, 0), '8880'),
    0x10015057: ('s32i.n', (8, 10, 0), '98a0'),
    0x10015063: ('s32i.n', (8, 11, 0), '98b0'),
    0x1001506a: ('bltui', (8, 4, 0x10015039), '6e84cb'),
    0x10015176: ('l32r', (12, 0x100068e0), '1cc5da'),
    0x10015179: ('l32r', (13, 0x10006770), '1dc57d'),
    0x100151a8: ('l32i.n', (8, 12, 0), '88c0'),
    0x100151af: ('l16ui', (11, 13, 190), '2bd15f'),
    0x100151b2: ('xor', (9, 9, 10), '0a9903'),
    0x100151b5: ('and', (8, 8, 9), '098801'),
    0x100151b8: ('or', (8, 8, 11), '0b8802'),
    0x100151c1: ('s32i', (8, 12, 0), '28c600'),
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def source_paths():
    """Preserve the exact local Python dependency closure, including lazies."""
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
    return sorted(found)


class FormatRAM(StopRAM):
    def after_instruction(self, pc, nxt):
        nxt = super().after_instruction(pc, nxt)
        if pc == ENTRY:
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
    state = FormatRAM(program, ENTRY, [(ENTRY, ENTRY + 3)], [(ARENA, ARENA_SIZE)])
    state.put(ARENA, bytes([case['fill']]) * ARENA_SIZE)
    state.put(BUFFER, bytes(((i * 29 + 17) ^ case['fill']) & 255 for i in range(8192)))
    state.put(VIDEO, bytes([case['fill']]) * 260)
    for offset, size, value in ((0x14, 2, 600), (0x16, 2, 600),
                                (0x22, 2, case['bpp']), (0x36, 1, 0),
                                (0x84, 4, 9600)):
        state.write(WORK + offset, size, value)
    # Executed bypass preparation already establishes these values elsewhere.
    # Here they are explicit inputs, never a claim that prepare ran end to end.
    for offset, value in ((0xb8, 1200), (0xbc, 1200), (0xc0, 0), (0xc4, 1),
                          (0xc8, case['bpp']), (0xec, 0), (0xf4, 0)):
        state.write(VIDEO + offset, 4, value)
    assert state.read(SELECTOR, 4) == 2
    if case['selector'] != 2:
        state.write(SELECTOR, 4, case['selector'])
    state.write(COUNTER, 4, 0xcccccccc)
    return state


def protected_memory(state):
    return [(begin, end, state.bytes_at(begin, end - begin))
            for begin, end in state.write_ranges
            if not (STACK <= begin and end <= STACK + STACK_SIZE)]


def assert_memory(state, before, changed_words):
    """Compare all nonstack bytes with exact independently expected mutations."""
    found = set()
    for begin, end, original in before:
        expected = bytearray(original)
        for address, value in changed_words.items():
            if begin <= address and address + 4 <= end:
                expected[address - begin:address - begin + 4] = value.to_bytes(4, 'big')
                found.add(address)
        assert state.bytes_at(begin, end - begin) == expected, (hex(begin), 'unexpected RAM mutation')
    assert found == set(changed_words)


def run_fragment(state, q, name, resume, boundary, ranges, inputs, observations, changed_words=None):
    changed_words = {} if changed_words is None else changed_words
    state.code_ranges = [(ENTRY, ENTRY + 3)] + ranges + VECTORS
    state.cut_registers = dict(inputs)
    state.resume, state.boundary, state.stopped_at = resume, boundary, None
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
    assert_memory(state, before, changed_words)
    return dict(phase=name, original_entry=hex(ENTRY), resume=hex(resume),
                stop_before=hex(boundary), supplied_registers={f'a{r}': v for r, v in sorted(inputs.items())},
                other_a2_through_a15_zero=True, observed=observed, steps=steps,
                visited=[hex(pc) for pc in sorted(visited)],
                exact_nonstack_memory_match=True,
                permitted_post_words={hex(a): v for a, v in changed_words.items()})


def reject_boundaries(state, q):
    rejected, before = [], protected_memory(state)
    # Check against the union of every permitted fragment, so a boundary cannot
    # pass merely because the last individual phase happened to exclude it.
    state.code_ranges = [(ENTRY, ENTRY + 3)] + VECTORS + TABLE_RANGES + TABLE_CONTINUE + MASK_PREFIX + [
        (0x10014e2c, 0x10014e35), (0x10014e68, 0x10014e77), (0x100151aa, 0x100151c1)]
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
    assert_memory(state, before, {})
    return rejected


def execute(program, q, case, captures):
    state = memory(program, case)
    before, phases = protected_memory(state), []
    if case['bpp'] == 1:
        first = run_fragment(state, q, 'table_pair', 0x10014e89, 0x10014f48,
                             TABLE_RANGES, {4: WORK},
                             dict(address_0=11, word_0=9, address_1=10, word_1=8))
        phases.append(first)
        values = first['observed']
        tables = [dict(address=values[f'address_{i}'], word=values[f'word_{i}']) for i in range(2)]
        final_words = {}
    else:
        first = run_fragment(state, q, 'table_0', 0x10014e89, 0x10015057,
                             TABLE_RANGES, {4: WORK},
                             dict(address=10, word=8, counter_cell=11, selector_cell=12,
                                  source_table=13, destination_table=14), {COUNTER: 0})
        phases.append(first)
        values = first['observed']
        assert {key: values[key] for key in ('counter_cell', 'selector_cell', 'source_table', 'destination_table')} == {
            'counter_cell': COUNTER, 'selector_cell': SELECTOR,
            'source_table': 0x10005550, 'destination_table': TABLE_ADDRESSES[0]}
        tables = [dict(address=values['address'], word=values['word'])]
        # These registers were observed before the omitted first video store.
        # That store has no CPU-register effect; no target or RAM sink receives it.
        continuation = {11: values['counter_cell'], 12: values['selector_cell'],
                        13: values['source_table'], 14: values['destination_table']}
        for index in (1, 2, 3):
            phase = run_fragment(state, q, f'table_{index}', 0x10015059, 0x10015057,
                                 TABLE_CONTINUE, continuation, dict(address=10, word=8), {COUNTER: index})
            phases.append(phase)
            tables.append(phase['observed'])
        phases.append(run_fragment(state, q, 'table_counter_end', 0x10015059, 0x1001506d,
                                   TABLE_CONTINUE, continuation, dict(counter=8), {COUNTER: 4}))
        assert phases[-1]['observed']['counter'] == 4
        final_words = {COUNTER: 4}
    expected_tables = [dict(address=address, word=word)
                       for address, word in zip(TABLE_ADDRESSES, TABLE_WORDS[case['bpp'], case['selector']])]
    assert tables == expected_tables, (case, tables, expected_tables)

    if case['bpp'] == 1:
        prefix = run_fragment(state, q, 'bpp_mask_prefix', 0x10014e18, 0x10014e2a,
                              MASK_PREFIX, {}, dict(address=10, mask=11))
        assert prefix['observed'] == dict(address=0xb1000000, mask=0xfcffffff)
        values = prefix['observed']
        masked = run_fragment(state, q, 'bpp_mask_value', 0x10014e2c, 0x10014e35,
                              [(0x10014e2c, 0x10014e35)],
                              {8: case['old_word'], 10: values['address'], 11: values['mask']},
                              dict(address=10, value=8, preserved_mask=11, other_address=9))
    else:
        prefix = run_fragment(state, q, 'bpp_mask_prefix', 0x10014e18, 0x10014e66,
                              MASK_PREFIX, {}, dict(address=11, replace_mask=10, initial_xor=9, set_bits=12))
        assert prefix['observed'] == dict(address=0xb1000000, replace_mask=0x03000000,
                                          initial_xor=0xffffffff, set_bits=0x01000000)
        values = prefix['observed']
        masked = run_fragment(state, q, 'bpp_mask_value', 0x10014e68, 0x10014e77,
                              [(0x10014e68, 0x10014e77)],
                              {8: case['old_word'], 9: values['initial_xor'], 10: values['replace_mask'],
                               11: values['address'], 12: values['set_bits']},
                              dict(address=11, value=8, preserved_mask=9, other_address=10))
    phases.extend((prefix, masked))
    expected_control = (case['old_word'] & 0xfcffffff) | (0x01000000 if case['bpp'] == 2 else 0)
    assert masked['observed'] == dict(address=0xb1000000, value=expected_control,
                                      preserved_mask=0xfcffffff, other_address=0xb1000100)
    stride = run_fragment(state, q, 'stride_mask_value', 0x100151aa, 0x100151c1,
                          [(0x100151aa, 0x100151c1)],
                          {8: case['old_word'], 12: LITERALS[0x100068e0], 13: VIDEO},
                          dict(address=12, value=8, preserved_mask=9, stride=11, other_address=10))
    phases.append(stride)
    expected_stride = (case['old_word'] & 0xffff0000) | 1200
    assert stride['observed'] == dict(address=0xb1000014, value=expected_stride,
                                      preserved_mask=0xffff0000, stride=1200, other_address=0xb1000114)
    assert_memory(state, before, final_words)
    rejected = reject_boundaries(state, q)
    assert_memory(state, before, final_words)
    observed = dict(table_words=tables, control_mask_value=masked['observed'], stride_mask_value=stride['observed'])
    name = 'interpreter' if q is None else 'qemu'
    regions = protected_memory(state)
    blob = b''.join(data for _, _, data in regions)
    (captures / f'{case["name"]}-{name}-ram.bin').write_bytes(blob)
    record = dict(engine=name, status='pass', observed=observed, phases=phases,
                  final_nonstack_ram_sha256=sha(blob),
                  memory_regions=[dict(begin=hex(a), end=hex(b), sha256=sha(data)) for a, b, data in regions],
                  exact_nonstack_memory_match=True,
                  only_permitted_final_ram_words={hex(a): v for a, v in final_words.items()},
                  rejected_before_execution=rejected, peripheral_instructions_executed=0)
    (captures / f'{case["name"]}-{name}.json').write_text(json.dumps(record, indent=2) + '\n')
    return record


def cases():
    for selector in (2, 0, 1):
        for bpp in (1, 2):
            for old_word, fill in ((0, 0), (0xffffffff, 204)):
                yield dict(name=f'bpp-{bpp}-selector-{selector}-old-{old_word:08x}',
                           bpp=bpp, selector=selector, old_word=old_word, fill=fill,
                           resolution=600, width_bits=9600, stride_bytes=1200,
                           selector_source='file_backed_value_2' if selector == 2 else 'explicit_conditional_RAM_override',
                           old_word_source='supplied_control_and_stride_arithmetic_seed',
                           geometry_source='supplied_bypass_profile_secondary_zero')


def main():
    capture = Path(tempfile.mkdtemp(prefix='hp1020-output-format-', dir='/tmp'))
    print(f'Output format captures: {capture}', flush=True)
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
    original, audited = Machine(program), []
    for begin, end, executable, expected_sha in BYTE_RANGES:
        data, offset = original.span(begin, end - begin, execute=executable)
        raw = bytes(data[offset:offset + end - begin])
        assert sha(raw) == expected_sha, hex(begin)
        audited.append(dict(begin=hex(begin), end=hex(end), executable_section=executable,
                            sha256=expected_sha, bytes=raw.hex()))
    for pc, (op, args, encoded) in ANCHORS.items():
        raw = bytes.fromhex(encoded)
        assert program.instruction(pc) == (op, args, raw), hex(pc)
        data, offset = original.span(pc, len(raw), execute=True)
        assert bytes(data[offset:offset + len(raw)]) == raw
    assert {pc: original.read(pc, 4) for pc in LITERALS} == LITERALS
    assert original.read(SELECTOR, 4) == 2
    rows = []
    with QemuRAM() as q:
        version = q.version
        for case in cases():
            interpreted = execute(program, None, case, capture)
            native = execute(program, q, case, capture)
            assert interpreted['observed'] == native['observed']
            assert interpreted['final_nonstack_ram_sha256'] == native['final_nonstack_ram_sha256']
            assert [p['observed'] for p in interpreted['phases']] == [p['observed'] for p in native['phases']]
            for audit in audited:
                raw = bytes.fromhex(audit['bytes'])
                assert q.read(int(audit['begin'], 16), len(raw)) == raw
            assert all(int.from_bytes(q.read(pc, 4), 'big') == value for pc, value in LITERALS.items())
            rows.append(dict(case=case, interpreter=interpreted, qemu=native))
            print(f'Output format: {len(rows)} cases agree', flush=True)
    assert sha(stock.read_bytes()) == STOCK_SHA
    assert all(sha((ROOT / name).read_bytes()) == digest for name, digest in sources.items()), 'source changed during execution'
    report = dict(status='pass', cases=rows, stock_elf_sha256=STOCK_SHA,
                  source_sha256=sources, qemu_version=version, original_byte_ranges=audited,
                  instruction_anchors={hex(pc): dict(op=op, args=args, bytes=encoded)
                                       for pc, (op, args, encoded) in ANCHORS.items()},
                  literals={hex(pc): hex(value) for pc, value in LITERALS.items()},
                  independent_table_oracle={f'bpp{bpp}-selector{selector}': list(words)
                                            for (bpp, selector), words in TABLE_WORDS.items()},
                  completed_native_page_lifecycles=0, usb_transfers=0, peripheral_instructions_executed=0,
                  scope='Original 600 dpi BPP1/2 bypass table selection, BPP control-field mask and stride-field mask. File-backed selector 2 is primary; 0/1 are explicit conditional RAM overrides. All destination addresses and values are observed before excluded video stores.',
                  limits='Fresh ENTRY and explicit register/PC cuts omit the prepare prefix, every video access and every readiness path. Old control/stride values, bypass geometry, output BPP and secondary=0 are supplied. The stride cut also supplies its destination/video registers, anchored to the original omitted L32R instructions. The BPP2 scratch counter alone changes in nonstack RAM; omitted video stores have no sink. BPP1 captures two pending words and does not execute the earlier table-zeroing loop. No complete hardware configuration, live engine selector, pixel polarity/bit order/lane order, decoded-DMA byte layout, padding interpretation, cache visibility, submission or printing is proven. These numeric tables must not be assigned physical sample meanings without independent hardware evidence.')
    OUT.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(report, indent=2, sort_keys=True) + '\n'
    (capture / 'report.json').write_text(text)
    OUT.with_suffix('.json').write_text(text)
    OUT.with_suffix('.md').write_text('# Original output-format arithmetic\n\n'
        + f'{len(rows)} original-byte cases agree between the bounded interpreter and independent QEMU. Zero completed page lifecycles.\n\n'
        + report['scope'] + '\n\n' + report['limits'] + '\n')
    print(f'Output format: {len(rows)} cases passed; no peripheral instruction executed', flush=True)


if __name__ == '__main__':
    main()
