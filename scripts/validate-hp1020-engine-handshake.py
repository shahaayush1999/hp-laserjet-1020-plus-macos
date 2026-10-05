#!/usr/bin/env python3
"""Original engine reply/flag arithmetic in explicit RAM-only cuts.

No peripheral instruction, interrupt operation, scheduler or command submission
executes. Each supplied observation is independent; these are not transactions.
"""
import hashlib
import json
import os
from pathlib import Path

from hp1020_qemu_ram import QemuRAM
from hp1020_xtensa_call0 import Machine, Program, STACK, STOP

ROOT = Path(__file__).resolve().parents[1]
STATE = 0x1002f0c4
PREFIX = os.environ.get('XTENSA_PREFIX', '/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf')
OPS = {'movi', 'mov', 'l32r', 'l16ui', 'l32i', 's16i', 's32i', 'addi',
       'and', 'or', 'xor', 'sub', 'moveqz', 'movnez', 'beqz', 'bnez',
       'beqi', 'bnone', 'bbsi', 'j', 'memw'}


class Cut(Machine):
    def __init__(self, program, start, stops, cells):
        super().__init__(program)
        self.pc = start
        self.start, self.stops = start, stops
        self.write_ranges = [(a, a+len(v)) for a, v in cells.items()]
        self.stopped = None
        for a, value in cells.items():
            self.put(a, value)

    def after_instruction(self, pc, nxt):
        assert self.start <= pc < max(self.stops)
        assert self.program.instruction(pc)[0].removesuffix('.n') in OPS
        if nxt in self.stops:
            self.stopped = nxt
            return STOP
        return nxt


def execute(q, program, name, start, stops, regs=None, cells=None):
    cells = cells or {}
    state = Cut(program, start, stops, cells)
    for r, value in (regs or {}).items():
        state.registers[r] = value
    q.reset_cpu(start)
    for r, value in enumerate(state.registers):
        q.set_reg(r+1, value)
    for address, value in cells.items():
        q.put(address, value)
    state.run(budget=80)
    count = 0
    while q.reg(0) not in stops:
        pc = q.reg(0)
        op, args, raw = program.instruction(pc)
        base = op.removesuffix('.n')
        assert start <= pc < max(stops) and base in OPS, (name, hex(pc), op)
        assert q.read(pc, len(raw)) == raw
        if base in ('l16ui', 'l32i', 's16i', 's32i'):
            address = q.reg(args[1]+1)+args[2]
            size = 2 if '16' in base else 4
            assert any(a <= address and address+size <= a+len(v) for a, v in cells.items()), (name, hex(address))
        if base == 'l32r':
            assert 0x10005c80 <= args[1] < 0x10007000
        assert q.command('s').startswith('T05')
        count += 1
        assert count <= 80
    assert q.reg(0) == state.stopped and count == state.steps
    assert [q.reg(r+1) for r in range(16)] == state.registers, name
    for a, value in cells.items():
        assert q.read(a, len(value)) == bytes(state.read(a+i, 1) for i in range(len(value))), name
    return state


def memory(flags=0, command=0x1337, response=0x5aa5):
    value = bytearray(0x70)
    value[:4] = (0x4456444e).to_bytes(4, 'big')
    value[8:12] = flags.to_bytes(4, 'big')
    value[0x5a:0x5c] = command.to_bytes(2, 'big')
    value[0x5c:0x5e] = response.to_bytes(2, 'big')
    return {STATE: bytes(value), STACK: b'\xa5'*32}


def saved(state):
    return {a: bytes(state.read(a+i, 1) for i in range(n)) for a, n in ((STATE, 0x70), (STACK, 32))}


def main():
    program = Program(ROOT/'analysis/sihp1020.elf', PREFIX)
    digest = hashlib.sha256(program.path.read_bytes()).hexdigest()
    assert digest == '2111560068db47ceca21fa550db4c7c34f5595b5a5d137ae4a19631e40e3601d'
    # These original sites connect the cuts; NONE executes in this validator.
    excluded = {
        0x10015bd4: ('l32i.n', (8, 11, 0)), 0x10015bdc: ('s32i.n', (8, 11, 0)),
        0x10015be1: ('l32i.n', (9, 11, 0)), 0x10015bec: ('l32i.n', (9, 11, 0)),
        0x10015c0f: ('l32i.n', (8, 11, 0)), 0x10015c19: ('call8', (0x10017dac,)),
        0x10015c58: ('call8', (0x100171b0,)), 0x10015c61: ('call8', (0x100171e0,)),
        0x10015cad: ('s32i', (8, 6, 0)), 0x10015cbd: ('s32i.n', (8, 6, 0)),
        0x10015cc2: ('call8', (0x10017184,)), 0x10015cd4: ('call8', (0x10017d28,)),
        0x10015ce4: ('call8', (0x1001766c,)), 0x10015d04: ('call8', (0x10013658,)),
        0x100164f8: ('call8', (0x1001716c,)), 0x10017dd0: ('call8', (0x1001896c,)),
        0x10017d6d: ('call8', (0x10019408,)),
    }
    for pc, expected in excluded.items():
        assert program.instruction(pc)[:2] == expected
    rows = []
    with QemuRAM() as q:
        q.load(program.path)

        def run(name, start, stops, regs=None, cells=None):
            state = execute(q, program, name, start, stops, regs, cells)
            rows.append(dict(name=name, start=hex(start), stop=hex(state.stopped), instructions=state.steps))
            return state

        registration = run('register-response-handler', 0x100164f0, {0x100164f8})
        assert registration.registers[10:12] == [6, 0x10015bc8]
        for pc, stop in ((0x10015c50, 0x10015c58), (0x10015c5b, 0x10015c61)):
            tail = run('irq6-tail-argument', pc, {stop}, {7: 6})
            assert tail.registers[10] == 6

        for flags in (0, 0x01000000, 0x08000000, 0x09000000):
            gate = run(f'reply-present-{flags:x}', 0x10015be3, {0x10015be9, 0x10015c34}, {9: flags})
            assert gate.stopped == (0x10015be9 if flags & 0x01000000 else 0x10015c34)
            if flags & 0x01000000:
                valid = run(f'reply-accept-{flags:x}', 0x10015bee, {0x10015bf6, 0x10015c0c}, {9: flags})
                assert valid.stopped == (0x10015bf6 if flags & 0x08000000 else 0x10015c0c)
                if not flags & 0x08000000:
                    # This is a THIRD supplied register read, not a coherent
                    # hardware snapshot inferred from the earlier two reads.
                    valid.registers[8] = 0xabcd918f
                    capture = run('capture-low16-and-post-one', 0x10015c11, {0x10015c19},
                                  dict(enumerate(valid.registers)), memory())
                    assert capture.read(STATE+0x5c, 2) == 0x918f
                    assert capture.registers[10:13] == [STATE, 1, 0]
        for flags in (0, 0x04000000):
            gate = run(f'other-flag-{flags:x}', 0x10015c39, {0x10015c3f, 0x10015c50}, {9: flags})
            assert gate.stopped == (0x10015c3f if flags else 0x10015c50)

        for flags in (0, 2, 0xa0000002):
            posted = run(f'event-or-{flags:x}', 0x10018972, {0x10018b79},
                         {2: STATE, 3: 1, 4: 0}, memory(flags))
            assert posted.read(STATE+8, 4) == flags | 1
        for flags in (0, 1, 2, 3, 0xa0000003):
            take = run(f'event-and-clear-{flags:x}', 0x10019410, {0x10019450, 0x100194cc},
                       {3: 1, 4: 3, 5: STACK, 10: STATE}, memory(flags))
            assert take.registers[2] == (0 if flags & 1 else 7)
            assert take.read(STATE+8, 4) == flags & ~1
            assert take.read(STACK, 4) == (flags if flags & 1 else 0xa5a5a5a5)

        # Conditional stale-event path: a pre-existing flag and old response
        # survive a new command latch. No hardware submission or IRQ occurs in
        # these cuts; this is NOT a reproduced device fault or timing claim.
        staged = run('stage-command-with-old-event', 0x10015c6b, {0x10015c85},
                     {2: 0x13}, memory(1))
        assert staged.read(STATE+0x5a, 2) == 0x13 and staged.read(STATE+8, 4) == 1
        args = run('wait-one-and-clear-200-ticks', 0x10015cc5, {0x10015cd4}, {1: STACK, 2: STATE})
        assert args.registers[10:15] == [STATE, 1, 3, STACK, 200]
        consumed = run('consume-old-event', 0x10019410, {0x100194cc},
                       {3: 1, 4: 3, 5: STACK, 10: STATE}, saved(staged))
        returned = run('success-returns-old-response', 0x10015cd7, {0x10015d12},
                       {2: STATE, 7: 4, 10: consumed.registers[2]}, saved(consumed))
        assert returned.registers[2] == 0x5aa5 and returned.read(STATE+0x5a, 2) == 0

        for attempts in (4, 3, 2, 1):
            failed = run(f'failed-wait-attempts-{attempts}', 0x10015cd7, {0x10015c91, 0x10015d04},
                         {1: STACK, 2: STATE, 7: attempts, 10: 7}, memory())
            assert failed.registers[7] == attempts-1
            assert failed.read(STATE+0x5a, 2) == 0x1337
            if attempts == 1:
                assert failed.registers[10:12] == [1, STACK+16]
                assert [failed.read(STACK+i, 4) for i in (16, 20, 24, 28)] == [0x17, 0xfe001401, 0, 0]
        timeout = run('timeout-sentinel', 0x10015d07, {0x10015d0a})
        assert timeout.registers[2] == 0xffff
        version = q.version
    sources = [Path(__file__), ROOT/'scripts/hp1020_xtensa_call0.py',
               ROOT/'scripts/hp1020_xtensa_properties.py', ROOT/'scripts/hp1020_qemu_ram.py']
    output = dict(stock_elf_sha256=digest, qemu=version, paired_cuts=len(rows), cases=rows,
                  source_sha256={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
                  limits=['All MMIO, IRQ changes, event scheduling, waiting and command publication are omitted.',
                          'Flag values, individual register reads and pending-event RAM are supplied.',
                          'Old-event acceptance is conditional software behavior, not a demonstrated printer fault.',
                          'No physical response identity, deadlines, sensor meanings or safe recovery are established.'])
    (ROOT/'analysis/hardware-boundary/engine-handshake-execution.json').write_text(json.dumps(output, indent=2)+'\n')
    print(f'PASS: {len(rows)} original RAM cuts agree with QEMU; no engine or IRQ access.')


if __name__ == '__main__':
    main()
