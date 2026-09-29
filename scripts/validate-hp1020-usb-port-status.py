#!/usr/bin/env python3
"""Original GET_PORT_STATUS response construction; bounded offline experiment.

Original ENTRY, two isolated zero-definition instructions and request dispatch
execute through explicit cuts. Hardware initialization/admission do not execute.
Both engines stop before the control sender or stall handling. This observes
prepared RAM bytes/count only, not USB delivery or physical printer status.
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
from hp1020_qemu_ram import QemuRAM, RETURN, STACK_TOP


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'analysis/usb-path/port-status'
STOCK_SHA = '2111560068db47ceca21fa550db4c7c34f5595b5a5d137ae4a19631e40e3601d'
ENTRY, ZERO, COPY_ZERO, RESUME = 0x10008ff0, 0x1000912d, 0x10009286, 0x10009399
TX_BOUNDARY, STALL_BOUNDARY = 0x100096a9, 0x1000985c
ARENA, ARENA_SIZE = 0x22500000, 0x4000
SETUP, STATUS_VALUE = ARENA + 0x100, ARENA + 0x200
INITIAL_SP = STACK_TOP - 0x100
FRAME_SP, RESPONSE = INITIAL_SP - 128, INITIAL_SP - 128 + 80
EMPTY_FIXTURE = SimpleNamespace(path=None, execute_ranges=[])
RANGES = [(ENTRY, ENTRY + 3), (ZERO, ZERO + 2), (COPY_ZERO, COPY_ZERO + 2),
          (RESUME, 0x1000945c), (0x100097f5, 0x100097fe),
          (0x1000984f, STALL_BOUNDARY)]
EXCLUDED = (ENTRY + 3, 0x10008fff, ZERO + 2, COPY_ZERO + 2,
            TX_BOUNDARY, 0x10008c24, 0x10008c35, STALL_BOUNDARY,
            0x10009865, 0x10009870, 0x10009877, 0x1000987f,
            0x10010838, 0x10011178, 0x100140ac, 0x10015648)
ANCHORS = {
    ENTRY: ('entry', (1, 128), '6c1010'),
    ZERO: ('movi.n', (7, 0), 'c070'),
    COPY_ZERO: ('mov.n', (3, 7), 'd370'),
    RESUME: ('l32r', (8, 0x10005ee8), '18f2d3'),
    0x1000940e: ('l8ui', (8, 12, 8), '28c008'),
    0x10009414: ('l8ui', (9, 4, 1), '294001'),
    0x10009417: ('slli', (8, 8, 8), '088811'),
    0x1000941a: ('or', (9, 8, 9), '098902'),
    0x10009444: ('l32r', (8, 0x10005f90), '18f2d3'),
    0x10009447: ('bne', (9, 8, 0x1000944d), '789902'),
    0x1000944a: ('j', (0x100097f5,), '6003a7'),
    0x100097f5: ('s8i', (3, 1, 80), '231450'),
    0x100097f8: ('addi', (8, 1, 80), '281c50'),
    0x100097fb: ('j', (0x1000984f,), '600050'),
    0x1000984f: ('s32i', (8, 5, 64), '285610'),
    0x10009852: ('movi.n', (6, 1), 'c061'),
    0x10009854: ('s32i.n', (6, 5, 60), '965f'),
    0x10009856: ('j', (TX_BOUNDARY,), '63fe4f'),
    0x10009859: ('movi', (2, 1), '220a01'),
    TX_BOUNDARY: ('call8', (0x10008c24,), '5bfd5e'),
    0x10008c35: ('l32i.n', (8, 4, 0), '8840'),
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
    return sorted(found)


def initial_registers(control, poison):
    registers = [0] * 14
    registers[3 - 2] = poison
    registers[5 - 2] = control
    registers[7 - 2] = poison ^ 0xffffffff
    return registers


def cut_record(pc, target, a3, a7):
    return dict(after=hex(pc), resume=hex(target), a3=hex(a3), a7=hex(a7))


class PortStatusRAM(StopRAM):
    def __init__(self, program, case):
        super().__init__(program, ENTRY, RANGES.copy(), [(ARENA, ARENA_SIZE)])
        self.case, self.cuts = case, []
        self.boundary = TX_BOUNDARY if case['port_status'] else STALL_BOUNDARY
        self.control = self.read(0x10005e1c, 4)
        self.status = self.read(0x100063d8, 4)
        self.table = self.read(0x1000647c, 4)
        self.registers[1] = INITIAL_SP
        self.put(STACK, bytes([case['fill']]) * STACK_SIZE)
        self.put(ARENA, bytes([case['fill']]) * ARENA_SIZE)
        self.put(self.control, bytes([case['fill']]) * 0x70)
        self.write(self.control + 60, 4, 0x99aabbcc)
        self.write(self.control + 64, 4, 0x11223344)
        self.write(self.read(0x10005ee8, 4), 4, SETUP)
        # Descriptor ownership/admission is supplied, not executed. Only the
        # eight-byte packet at this record's +8 is used by the chosen dispatch.
        self.write(SETUP, 4, 0x80000000)
        self.put(SETUP + 8, bytes.fromhex(case['setup_hex']))
        # Deliberately unrelated status RAM varies independently of packet/fill.
        # These are numeric fixtures, not real sensor or lifecycle states.
        self.put(self.status, case['status_seed'].to_bytes(4, 'big') * 7)
        self.write(self.table + 25 * 24 + 4, 4, STATUS_VALUE)
        self.write(self.table + 25 * 24 + 8, 4, 2)
        self.write(STATUS_VALUE, 4, case['status_seed'])

    def after_instruction(self, pc, nxt):
        nxt = super().after_instruction(pc, nxt)
        if pc == ENTRY:
            assert self.registers[1] == FRAME_SP
            self.registers[2:] = initial_registers(self.control, self.case['poison'])
            nxt = ZERO
        elif pc == ZERO:
            assert self.registers[7] == 0 and self.registers[3] == self.case['poison']
            nxt = COPY_ZERO
        elif pc == COPY_ZERO:
            assert self.registers[3] == self.registers[7] == 0
            nxt = RESUME
        if pc in (ENTRY, ZERO, COPY_ZERO):
            self.cuts.append(cut_record(pc, nxt, self.registers[3], self.registers[7]))
        if nxt == self.boundary:
            self.stopped_at = nxt
            return STOP
        return nxt


def snapshot(state):
    return {(a, b): state.bytes_at(a, b - a) for a, b in state.write_ranges
            if not (STACK <= a and b <= STACK + STACK_SIZE)}


def expected_memory(state, before, case):
    expected = {bounds: bytearray(data) for bounds, data in before.items()}
    def put(at, data):
        matches = [(a, b) for a, b in expected if a <= at and at + len(data) <= b]
        assert len(matches) == 1
        begin, end = matches[0]
        expected[(begin, end)][at - begin:at - begin + len(data)] = data
    packet = bytearray.fromhex(case['setup_hex'])
    packet[4:6] = packet[4:6][::-1]
    packet[6:8] = packet[6:8][::-1]
    put(SETUP + 8, packet)
    if case['port_status']:
        put(state.control + 60, (1).to_bytes(4, 'big'))
        put(state.control + 64, RESPONSE.to_bytes(4, 'big'))
    return {bounds: bytes(data) for bounds, data in expected.items()}


def reject_boundaries(state, q):
    before = snapshot(state)
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
            assert state.steps == 0 and state.visited == prior
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
    assert snapshot(state) == before


def memory_manifest(memory):
    return [dict(begin=hex(a), end=hex(b), sha256=sha(data))
            for (a, b), data in sorted(memory.items())]


def execute(program, q, case, capture):
    state = PortStatusRAM(program, case)
    before = snapshot(state)
    expected = expected_memory(state, before, case)
    expected_frame = bytearray([case['fill']]) * 32
    if case['port_status']:
        expected_frame[16] = 0
    engine = 'interpreter' if q is None else 'qemu'
    stem = capture / f'{case["name"]}-{engine}'
    stem.with_suffix('.before.bin').write_bytes(b''.join(data for _, data in sorted(before.items())))
    if q is None:
        state.run(budget=1000)
        assert state.stopped_at == state.boundary
        visited, steps, stalled = state.visited.copy(), state.steps, state.registers[2]
        final_sp, a3, a7 = state.registers[1], state.registers[3], state.registers[7]
        cuts = state.cuts
    else:
        runner = start(q, state, EMPTY_FIXTURE, ENTRY, (), instruction_budget=1000)
        phase, cuts = 0, []
        def reg(index):
            return q.reg(((q.reg(38) * 4 + index) % 32) + 1)
        while q.reg(0) != state.boundary:
            if phase == 0 and q.reg(0) == ENTRY + 3:
                assert ENTRY in runner.visited and reg(1) == FRAME_SP
                for index, value in enumerate(initial_registers(state.control, case['poison']), 2):
                    q.set_reg(((q.reg(38) * 4 + index) % 32) + 1, value)
                cuts.append(cut_record(ENTRY, ZERO, reg(3), reg(7)))
                q.set_reg(0, ZERO)
                phase = 1
                continue
            if phase == 1 and q.reg(0) == ZERO + 2:
                assert ZERO in runner.visited and reg(7) == 0 and reg(3) == case['poison']
                cuts.append(cut_record(ZERO, COPY_ZERO, reg(3), reg(7)))
                q.set_reg(0, COPY_ZERO)
                phase = 2
                continue
            if phase == 2 and q.reg(0) == COPY_ZERO + 2:
                assert COPY_ZERO in runner.visited and reg(3) == reg(7) == 0
                cuts.append(cut_record(COPY_ZERO, RESUME, reg(3), reg(7)))
                q.set_reg(0, RESUME)
                phase = 3
                continue
            runner.step()
        assert phase == 3 and not runner.services
        final_sp, stalled, a3, a7 = reg(1), reg(2), reg(3), reg(7)
        runner.synchronize(False)
        visited, steps = runner.visited.copy(), runner.steps
    actual = snapshot(state)
    frame = state.bytes_at(FRAME_SP + 64, 32)
    observations = dict(status='captured_unchecked', case=case, stop_before=hex(state.boundary),
                        explicit_cuts=cuts, steps=steps, stack_pointer=hex(final_sp),
                        constant_a3=a3, constant_a7=a7, stall_intent=bool(stalled),
                        control_pointer=hex(state.read(state.control + 64, 4)),
                        control_count=state.read(state.control + 60, 4),
                        prepared_byte=state.read(RESPONSE, 1), response_frame=frame.hex(),
                        packet_after=state.bytes_at(SETUP + 8, 8).hex(),
                        nonstack_before=memory_manifest(before), nonstack_memory=memory_manifest(actual),
                        selected_visited=[hex(pc) for pc in sorted(visited - {RETURN - 3})])
    stem.with_suffix('.after.bin').write_bytes(b''.join(data for _, data in sorted(actual.items())))
    stem.with_suffix('.frame.bin').write_bytes(frame)
    stem.with_suffix('.json').write_text(json.dumps(observations, indent=2) + '\n')
    assert {ENTRY, ZERO, COPY_ZERO, RESUME} <= visited
    assert state.boundary not in visited and not (set(EXCLUDED) & visited)
    assert final_sp == FRAME_SP and a3 == a7 == 0
    assert actual == expected, (case['name'], 'unexpected nonstack RAM change')
    assert frame == expected_frame, (case['name'], 'unexpected response frame change')
    assert stalled == (0 if case['port_status'] else 1)
    if case['port_status']:
        assert {0x100097f5, 0x1000984f, 0x10009854} <= visited
        assert state.read(state.control + 64, 4) == RESPONSE
        assert state.read(state.control + 60, 4) == 1 and state.read(RESPONSE, 1) == 0
    else:
        assert not ({0x100097f5, 0x1000984f} & visited)
    reject_boundaries(state, q)
    observations.update(status='pass', exact_nonstack_ram_equal=True,
                        response_frame_matches_independent_oracle=True,
                        rejected_before_execution=[hex(pc) for pc in EXCLUDED],
                        peripheral_instructions_executed=0, supplied_service_calls=[])
    stem.with_suffix('.json').write_text(json.dumps(observations, indent=2) + '\n')
    return observations


def cases():
    packets = (('canonical', 'a101000000000100'),
               ('noncanonical', 'a10134127856bc9a'),
               ('zero-length', 'a101000000000000'),
               ('all-fields', 'a101ffffffffffff'))
    for fill in (0, 204):
        poison = 0x5aa55aa5 ^ (fill * 0x01010101)
        for status_seed in (0, 0xffffffff, 0xe6101100):
            for name, packet in packets:
                yield dict(name=f'{name}-status{status_seed:08x}-fill{fill}',
                           fill=fill, poison=poison, status_seed=status_seed,
                           setup_hex=packet, port_status=True,
                           noncanonical_fields=name != 'canonical')
        for name, packet in (('wrong-type', 'a001000000000100'),
                             ('wrong-request', 'a102000000000100')):
            yield dict(name=f'{name}-fill{fill}', fill=fill, poison=poison,
                       status_seed=0xe6101100, setup_hex=packet,
                       port_status=False, noncanonical_fields=False)


def main():
    capture = Path(tempfile.mkdtemp(prefix='hp1020-usb-port-status-', dir='/tmp'))
    print(f'USB port-status captures: {capture}', flush=True)
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
    literals = {0x10005f90: 0xa101, 0x10005e1c: 0x100212d4,
                0x10005e90: 0xb3000000, 0x100063d8: 0x1002adb4,
                0x1000647c: 0x1001ce14}
    for at, expected in literals.items():
        assert original.read(at, 4) == expected, hex(at)
    for pc, (op, args, encoded) in ANCHORS.items():
        raw = bytes.fromhex(encoded)
        assert program.instruction(pc) == (op, args, raw), hex(pc)
        data, offset = original.span(pc, len(raw), execute=True)
        assert bytes(data[offset:offset + len(raw)]) == raw
    audited = []
    for begin, end in RANGES:
        data, offset = original.span(begin, end - begin, execute=True)
        raw = bytes(data[offset:offset + end - begin])
        audited.append(dict(begin=hex(begin), end=hex(end), sha256=sha(raw), bytes=raw.hex()))
    results = []
    with QemuRAM() as q:
        version = q.version
        for case in cases():
            interpreted = execute(program, None, case, capture)
            native = execute(program, q, case, capture)
            for field in ('stop_before', 'explicit_cuts', 'stack_pointer', 'constant_a3',
                          'constant_a7', 'stall_intent', 'control_pointer', 'control_count',
                          'prepared_byte', 'response_frame', 'packet_after', 'nonstack_memory',
                          'selected_visited'):
                assert interpreted[field] == native[field], (case['name'], field)
            for audit in audited:
                raw = bytes.fromhex(audit['bytes'])
                assert q.read(int(audit['begin'], 16), len(raw)) == raw
            results.append(dict(case=case, interpreter=interpreted, qemu=native))
    assert sha(stock.read_bytes()) == STOCK_SHA
    assert all(sha((ROOT / name).read_bytes()) == digest for name, digest in sources.items())
    report = dict(status='pass', cases=results, source_sha256=sources,
                  stock_elf_sha256=STOCK_SHA, qemu_version=version,
                  original_byte_ranges=audited,
                  instruction_anchors={hex(pc): dict(op=op, args=args, bytes=encoded)
                                       for pc, (op, args, encoded) in ANCHORS.items()},
                  literal_anchors={hex(pc): hex(value) for pc, value in literals.items()},
                  original_entry=hex(ENTRY), explicit_cut_resumes=[hex(ZERO), hex(COPY_ZERO), hex(RESUME)],
                  setup_admission='supplied; owner/status prefix omitted',
                  supplied_registers='After ENTRY: a2=0, a5=control-state address, a3/a7 poisoned, remaining a2..a15 zero. Original isolated movi a7,0 and mov a3,a7 execute before dispatch.',
                  completed_usb_control_transfers=0, usb_transfers=0,
                  completed_native_page_lifecycles=0, peripheral_instructions_executed=0,
                  scope='Original GET_PORT_STATUS dispatch prepares a zero byte at stack+80, a response pointer and length one, independent of supplied unrelated status RAM. Unsupported request pairs select stall intent. Both stop before their control/peripheral handlers.',
                  limits='The two zero-definition instructions are isolated by explicit PC cuts; surrounding initialization, setup admission, event waiting and all hardware are omitted. No claim of a continuous boot or USB lifecycle is made. Numeric status/global fixtures are not physical calibration. Noncanonical field acceptance describes original response preparation only, not recommended policy or bytes actually transferred. The replacement should retain explicit unknown status until a real sensor/status adapter exists.')
    OUT.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(report, indent=2, sort_keys=True) + '\n'
    (capture / 'report.json').write_text(text)
    OUT.with_suffix('.json').write_text(text)
    OUT.with_suffix('.md').write_text('# Original USB GET_PORT_STATUS boundary\n\n'
        + f'{len(results)} original-byte cases agree between the interpreter and QEMU. Zero completed control transfers or page lifecycles.\n\n'
        + report['scope'] + '\n\n' + report['limits'] + '\n')
    print(f'USB port status: {len(results)} cases passed; no peripheral instruction executed', flush=True)


if __name__ == '__main__':
    main()
