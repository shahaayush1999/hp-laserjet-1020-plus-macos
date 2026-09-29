#!/usr/bin/env python3
"""Original printer-class reset bookkeeping, cut before any control transfer.

The setup-ready prefix is omitted. A supplied packet and registered handle
enter the original request dispatch; original registry/list changes execute.
Free and outer interrupt-mask services are explicitly supplied. No controller,
physical reset, DMA cancellation or safety of the frees is established.
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
OUT = ROOT / 'analysis/usb-path/class-reset'
STOCK_SHA = '2111560068db47ceca21fa550db4c7c34f5595b5a5d137ae4a19631e40e3601d'
ENTRY, RESUME = 0x10008ff0, 0x10009399
TX_BOUNDARY, STALL_BOUNDARY = 0x100096a9, 0x1000985c
ARENA, ARENA_SIZE = 0x22600000, 0x10000
DESCRIPTOR, SETUP = ARENA + 0x100, ARENA + 0x200
HOST = {0x100171b0, 0x10017184, 0x10013408}
CRITICAL = 0x1001b770
EMPTY_FIXTURE = SimpleNamespace(path=None, execute_ranges=[])
RANGES = [(ENTRY, ENTRY + 3), (RESUME, 0x1000945c),
          (0x100097fe, 0x1000980f), (0x10009859, STALL_BOUNDARY),
          (0x10007c70, 0x10007c95), (0x10008fb0, 0x10008ff0),
          (0x10013050, 0x1001307c), (0x100130bc, 0x100130c4)]
EXCLUDED = (0x10008fff, 0x10008c35, 0x10008214, 0x10009865, 0x10009870,
            0x10009877, 0x1000987f, 0x10009896, 0x100140ac, 0x10015648)
ANCHORS = {
    ENTRY: ('entry', (1, 128), '6c1010'),
    0x10009399: ('l32r', (8, 0x10005ee8), '18f2d3'),
    0x1000940e: ('l8ui', (8, 12, 8), '28c008'),
    0x10009414: ('l8ui', (9, 4, 1), '294001'),
    0x10009417: ('slli', (8, 8, 8), '088811'),
    0x1000941a: ('or', (9, 8, 9), '098902'),
    0x10009426: ('l32r', (8, 0x10005f84), '18f2d7'),
    0x10009429: ('bne', (9, 8, 0x1000942f), '789902'),
    0x1000942c: ('j', (0x100097fe,), '6003ce'),
    0x100097fe: ('l32i.n', (10, 5, 0), '8a50'),
    0x10009803: ('call8', (0x10007c70,), '5bf91b'),
    0x10009806: ('call8', (0x10008fb0,), '5bfdea'),
    0x10009809: ('s32i', (3, 5, 60), '23560f'),
    0x1000980c: ('j', (TX_BOUNDARY,), '63fe99'),
    0x10007c7b: ('srli', (2, 2, 1), '021214'),
    0x10007c81: ('addi.n', (5, 5, -1), 'b055'),
    0x10007c83: ('l32r', (3, 0x10005da8), '13f849'),
    0x10007c91: ('s32i.n', (3, 4, 0), '9340'),
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


class ResetRAM(StopRAM):
    def __init__(self, program, case):
        super().__init__(program, ENTRY, RANGES.copy(), [(ARENA, ARENA_SIZE)])
        self.events = []
        self.control = self.read(0x10005e1c, 4)
        self.queue = self.read(0x10005e10, 4)
        self.registry = self.read(0x10005da8, 4)
        self.slot = self.registry + (case['handle'].bit_length() - 1) * 88
        self.boundary = TX_BOUNDARY if case['reset'] else STALL_BOUNDARY
        self.put(ARENA, bytes([case['fill']]) * ARENA_SIZE)
        self.put(self.control, bytes([case['fill']]) * 0x70)
        self.put(self.registry, bytes([case['fill']]) * 176)
        self.write(self.control, 4, case['handle'])
        self.write(self.control + 60, 4, 0x11223344)
        self.write(self.registry, 4, 1)
        self.write(self.registry + 88, 4, 2)
        self.write(self.read(0x10005ee8, 4), 4, SETUP)
        self.write(self.read(0x10005e2c, 4), 4, DESCRIPTOR)
        self.write(DESCRIPTOR, 4, 0x48000025)
        # Setup admission/owner status is supplied, not executed. The dispatch
        # starts after that prefix and reads the packet at setup record + 8.
        self.write(SETUP, 4, 0x80000000)
        self.put(SETUP + 8, bytes.fromhex(case['setup_hex']))
        self.nodes = [ARENA + 0x400 + i * 64 for i in range(case['nodes'])]
        self.buffers = [ARENA + 0x1000 + i * 128 for i in range(case['nodes'])]
        self.write(self.queue, 4, self.nodes[0] if self.nodes else 0)
        self.write(self.queue + 4, 4, self.nodes[-1] if self.nodes else 0)
        for index, node in enumerate(self.nodes):
            self.write(node, 4, self.nodes[index + 1] if index + 1 < len(self.nodes) else 0)
            self.write(node + 12, 4, node + 16)
            self.write(node + 20, 4, self.buffers[index])
            self.put(self.buffers[index], bytes((j * 29 + index + case['fill']) & 255 for j in range(128)))

    def extension(self, op, args, nxt):
        if op == 'call8' and args[0] in HOST | {CRITICAL}:
            if args[0] != CRITICAL:
                assert self.read(self.slot, 4) == 0, 'registry must clear before draining'
                self.events.append([hex(args[0]), hex(self.registers[10])])
            self.registers[10] = 0
            self.branch_taken = True
            return nxt
        return super().extension(op, args, nxt)

    def after_instruction(self, pc, nxt):
        nxt = super().after_instruction(pc, nxt)
        if pc == ENTRY:
            self.registers[2:] = [0] * 14
            self.registers[5] = self.control
            nxt = RESUME
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
        candidates = [(a, b) for a, b in expected if a <= at and at + len(data) <= b]
        assert len(candidates) == 1
        begin, end = candidates[0]
        expected[(begin, end)][at - begin:at - begin + len(data)] = data
    packet = bytearray.fromhex(case['setup_hex'])
    packet[4:6] = packet[4:6][::-1]
    packet[6:8] = packet[6:8][::-1]
    put(SETUP + 8, packet)
    if case['reset']:
        for at, size in ((state.slot, 4), (state.queue, 8), (state.control + 60, 4)):
            put(at, bytes(size))
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


def execute(program, q, case, capture):
    state = ResetRAM(program, case)
    before = snapshot(state)
    expected = expected_memory(state, before, case)
    if q is None:
        state.run(budget=3000)
        assert state.stopped_at == state.boundary
        visited, steps, stalled = state.visited.copy(), state.steps, state.registers[2]
    else:
        state.code_ranges += VECTORS + [(CRITICAL, 0x1001b788)]
        runner = start(q, state, EMPTY_FIXTURE, ENTRY, HOST, instruction_budget=3000)
        cut_pending = True
        while q.reg(0) != state.boundary:
            if cut_pending and q.reg(0) == ENTRY + 3:
                assert ENTRY in runner.visited
                for reg in range(2, 16):
                    q.set_reg(((q.reg(38) * 4 + reg) % 32) + 1, state.control if reg == 5 else 0)
                q.set_reg(0, RESUME)
                cut_pending = False
                continue
            runner.step()
        assert not cut_pending
        stalled = q.reg(((q.reg(38) * 4 + 2) % 32) + 1)
        runner.synchronize(False)
        visited, steps = runner.visited.copy(), runner.steps
    assert ENTRY in visited and RESUME in visited and state.boundary not in visited
    assert not (set(EXCLUDED) & visited)
    assert snapshot(state) == expected, (case['name'], 'unexpected nonstack RAM change')
    events = []
    if case['reset']:
        events = [['0x100171b0', '0x4']]
        for node, buffer in zip(state.nodes, state.buffers):
            events += [['0x10013408', hex(buffer)], ['0x10013408', hex(node)]]
        events += [['0x10017184', '0x4']]
        assert {0x10007c70, 0x10007c91, 0x10008fb0, 0x10009809} <= visited
        assert stalled == 0
    else:
        assert not ({0x10007c70, 0x10008fb0} & visited) and stalled == 1
    assert state.events == events
    assert state.read(DESCRIPTOR, 4) == 0x48000025
    result = dict(status='pass', stop_before=hex(state.boundary), steps=steps,
                  registry_slot=hex(state.slot), supplied_service_calls=state.events,
                  original_registry_and_drain_executed=case['reset'], stall_intent=bool(stalled),
                  exact_nonstack_ram_equal=True, supplied_busy_status_word_unchanged=True,
                  packet_after=state.bytes_at(SETUP + 8, 8).hex(),
                  control_count=state.read(state.control + 60, 4),
                  queue_empty=state.read(state.queue, 4) == state.read(state.queue + 4, 4) == 0,
                  visited=[hex(pc) for pc in sorted(visited)],
                  rejected_before_execution=[hex(pc) for pc in EXCLUDED],
                  peripheral_instructions_executed=0)
    engine = 'interpreter' if q is None else 'qemu'
    result['nonstack_memory'] = [dict(begin=hex(a), end=hex(b), sha256=sha(data))
                                 for (a, b), data in sorted(expected.items())]
    (capture / f'{case["name"]}-{engine}.bin').write_bytes(b''.join(
        data for bounds, data in sorted(expected.items())))
    reject_boundaries(state, q)
    (capture / f'{case["name"]}-{engine}.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def cases():
    for fill in (0, 204):
        for handle in (1, 2):
            for nodes in (0, 1, 4):
                yield dict(name=f'reset-h{handle}-nodes{nodes}-fill{fill}', fill=fill,
                           handle=handle, nodes=nodes, reset=True, setup_hex='2102000000000000',
                           noncanonical_fields=False)
            yield dict(name=f'reset-noncanonical-h{handle}-fill{fill}', fill=fill,
                       handle=handle, nodes=1, reset=True, setup_hex='210234127856bc9a',
                       noncanonical_fields=True)
        for name, packet in (('wrong-type', '2002000000000000'), ('wrong-request', '2103000000000000')):
            yield dict(name=f'{name}-fill{fill}', fill=fill, handle=2, nodes=4,
                       reset=False, setup_hex=packet, noncanonical_fields=False)


def main():
    capture = Path(tempfile.mkdtemp(prefix='hp1020-usb-class-reset-', dir='/tmp'))
    print(f'USB class reset captures: {capture}', flush=True)
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
    assert original.read(0x10005f84, 4) == 0x2102
    assert original.read(0x10005da8, 4) == 0x1001ec40
    assert original.read(0x10005e1c, 4) == 0x100212d4
    for pc, (op, args, encoded) in ANCHORS.items():
        raw = bytes.fromhex(encoded)
        assert program.instruction(pc) == (op, args, raw), hex(pc)
        data, offset = original.span(pc, len(raw), execute=True)
        assert bytes(data[offset:offset + len(raw)]) == raw
    audited = []
    for begin, end in RANGES + [(CRITICAL, 0x1001b788)]:
        data, offset = original.span(begin, end - begin, execute=True)
        raw = bytes(data[offset:offset + end - begin])
        audited.append(dict(begin=hex(begin), end=hex(end), sha256=sha(raw), bytes=raw.hex()))
    results = []
    with QemuRAM() as q:
        version = q.version
        for case in cases():
            interpreted = execute(program, None, case, capture)
            native = execute(program, q, case, capture)
            for field in ('supplied_service_calls', 'stop_before', 'stall_intent', 'packet_after',
                          'control_count', 'queue_empty', 'nonstack_memory'):
                assert interpreted[field] == native[field], (case['name'], field)
            for audit in audited:
                raw = bytes.fromhex(audit['bytes'])
                assert q.read(int(audit['begin'], 16), len(raw)) == raw
            results.append(dict(case=case, interpreter=interpreted, qemu=native))
    assert sha(stock.read_bytes()) == STOCK_SHA
    assert all(sha((ROOT / name).read_bytes()) == digest for name, digest in sources.items())
    report = dict(status='pass', cases=results, source_sha256=sources, stock_elf_sha256=STOCK_SHA,
                  qemu_version=version, original_byte_ranges=audited,
                  instruction_anchors={hex(pc): dict(op=op, args=args, bytes=encoded)
                                       for pc, (op, args, encoded) in ANCHORS.items()},
                  original_entry=hex(ENTRY), resume=hex(RESUME), setup_admission='supplied',
                  supplied_registers='a3=0 and a5=original control-state address; other a2..a15 zero',
                  completed_usb_control_transfers=0, usb_transfers=0, completed_native_page_lifecycles=0,
                  peripheral_instructions_executed=0,
                  scope='Original class request 0x21/0x02 dispatch clears the supplied handle registration, drains pending software nodes and selects a zero-length control response, stopped before its sender. Nearby unsupported requests select stall intent before any stall register access.',
                  limits='The ready/owner prefix, actual control response, physical reset, interrupt scheduling, DMA and cache behavior are omitted. Two one-hot handles and bounded queues are supplied. Free and outer mask services are substituted; original list and registration routines execute, and QEMU also executes the original short list critical helper. Neither those frees nor their device safety are proven. A standalone supplied busy status word stays unchanged; no live descriptor/buffer relationship to the drained list is modeled. Noncanonical reset fields demonstrate original dispatch behavior, not recommended acceptance policy.')
    OUT.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(report, indent=2, sort_keys=True) + '\n'
    (capture / 'report.json').write_text(text)
    OUT.with_suffix('.json').write_text(text)
    OUT.with_suffix('.md').write_text('# Original USB printer-class reset boundary\n\n'
        + f'{len(results)} original-byte cases agree between the interpreter and QEMU. Zero completed control transfers or page lifecycles.\n\n'
        + report['scope'] + '\n\n' + report['limits'] + '\n')
    print(f'USB class reset: {len(results)} cases passed; no peripheral instruction executed', flush=True)


if __name__ == '__main__':
    main()
