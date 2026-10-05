#!/usr/bin/env python3
"""Execute original memory-boundary arithmetic; never boot or read peripherals.

Each slice starts after a supplied observation or stops before a side effect.
QEMU checks the same original instructions independently in synthetic RAM.
This establishes what stock computes, not the installed RAM or its bus mapping.
"""
import hashlib
import json
import os
from pathlib import Path

from hp1020_qemu_ram import QemuRAM
from hp1020_xtensa_call0 import Machine, Program, STOP
from hp1020_xtensa_stock import StockMachine

ROOT = Path(__file__).resolve().parents[1]
PREFIX = os.environ.get('XTENSA_PREFIX', '/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf')
FIRST = 0x100391e0
OPS = {'extui', 'movi', 'movi.n', 'mov.n', 'beq', 'beqi', 'beqz.n',
       'bnez.n', 'j', 'l32r', 'add.n', 'addi', 'addi.n', 'sub', 'srli',
       'slli', 'and', 'or', 'l32i.n', 's32i.n', 'memw'}


class Slice(StockMachine):
    def __init__(self, program, start, end, writable):
        super().__init__(program, start, [(start, end)], [(FIRST, 12)])
        self.end = end
        self.write_ranges = [(a, a+n) for a, n in writable]

    def after_instruction(self, pc, nxt):
        assert self.program.instruction(pc)[0] in OPS
        return STOP if nxt == self.end else nxt


def execute(q, program, start, end, registers, writable=(), outputs=()):
    state = Slice(program, start, end, writable)
    for r, value in registers.items():
        state.registers[r] = value
    for address, size in writable:
        state.put(address, b'\xa5'*size)
    state.run(budget=100)

    q.reset_cpu(start)
    for r, value in registers.items():
        q.set_reg(r+1, value)
    for address, size in writable:
        q.put(address, b'\xa5'*size)
    count = 0
    while q.reg(0) != end:
        pc = q.reg(0)
        op, args, raw = program.instruction(pc)
        assert start <= pc and pc+len(raw) <= end and op in OPS
        assert q.read(pc, len(raw)) == raw
        if op in ('l32i.n', 's32i.n'):
            address = q.reg(args[1]+1)+args[2]
            # Every data access in these cuts is an explicit output cell.
            assert any(a <= address and address+4 <= a+n for a, n in writable)
        if op == 'l32r':
            assert 0x10005c80 <= args[1] < 0x1001b718
        assert q.command('s').startswith('T05')
        count += 1
        assert count <= 100
    assert count == state.steps
    for r in outputs:
        assert q.reg(r+1) == state.registers[r]
    for address, size in writable:
        assert q.read(address, size) == bytes(state.read(address+i, 1) for i in range(size))
    return state


def main():
    program = Program(ROOT/'analysis/sihp1020.elf', PREFIX)
    elf_hash = hashlib.sha256(program.path.read_bytes()).hexdigest()
    assert elf_hash == '2111560068db47ceca21fa550db4c7c34f5595b5a5d137ae4a19631e40e3601d'
    memory = Machine(program)
    # Original call sites/literals connect the independently executed cuts.
    for pc, target in ((0x1001750c, 0x1001b718), (0x10017522, 0x10011ffc),
                       (0x10012007, 0x10012208), (0x10012084, 0x100130d0)):
        assert program.instruction(pc)[:2] == ('call8', (target,))
    for address, value in ((0x10005c80, 0xb0800008), (0x10005cac, 0x100351e0),
                           (0x10005cdc, 0x10006bb0), (0x10006a98, 0x10034ec4)):
        assert memory.read(address, 4) == value
    assert program.instruction(0x10006bc8)[:2] == ('l32i.n', (6, 4, 0))
    assert program.instruction(0x1001220e)[:2] == ('l32i', (2, 2, 0))
    assert program.instruction(0x1001751b)[:2] == ('l32i.n', (10, 8, 0))

    rows = []
    with QemuRAM() as q:
        q.load(program.path)
        # Skip PS setup, stop before interrupt/timer installation. The saved
        # boot SP and timer-stack reservation are RAM writes only.
        cells = [(a, 4) for a in (0x10034f50, 0x100351a0, 0x1003519c,
                                  0x100350f8, 0x10034ec4)]
        state = execute(q, program, 0x1001b724, 0x1001b749,
                        {1: 0x101fffb0}, cells)
        assert state.read(0x10034f50, 4) == 0x101fffb0
        assert state.read(0x100351a0, 4) == 0x100351e0
        assert state.read(0x1003519c, 4) == 0x4000
        assert state.read(0x10034ec4, 4) == FIRST

        for selector, capacity in enumerate((0x200000, 0x800000, 0x1000000, 0x2000000)):
            # Include nonzero low bits: both original selectors ignore them.
            observed = (selector << 30) | 0x13579bdf
            state = execute(q, program, 0x10006bca, 0x10006bf8,
                            {6: observed}, outputs=(1, 13))
            stack = state.registers[1]
            assert stack == 0x10000000+capacity-0x50
            state = execute(q, program, 0x10012211, 0x10012237,
                            {2: observed}, outputs=(2,))
            assert state.registers[2] == capacity
            state = execute(q, program, 0x1001200a, 0x10012017,
                            {2: FIRST, 10: capacity, 7: 0x1002c6ec},
                            [(0x1002c6ec, 4)], outputs=(10,))
            size = state.read(0x1002c6ec, 4)
            assert size == 0x10000000+capacity-FIRST
            cells = [(a, 4) for a in (0x1002c900, 0x1002c914, 0x1002c910, 0x1002c904)]
            # Stop before semaphore creation. Only the actual aligned boot
            # inputs matter here; this is not another allocator investigation.
            state = execute(q, program, 0x100130d3, 0x1001312e,
                            {2: FIRST, 3: size}, [*cells, (FIRST, 12)])
            assert state.read(0x1002c900, 4) == size
            assert state.read(0x1002c914, 4) == state.read(0x1002c904, 4) == FIRST
            assert state.read(0x1002c910, 4) == state.read(FIRST+4, 4) == size-12
            assert state.read(FIRST, 4) == 0x2e3d4c5a
            assert state.read(FIRST+8, 4) == ((0xa5a5a5a5 & 0x5fffffff) | 0x40000000)
            rows.append(dict(selector=selector, capacity=capacity, boot_sp=hex(stack),
                             pool_bytes=size, first_payload_bytes=size-12))
        version = q.version

    sources = [Path(__file__), *[ROOT/'scripts'/name for name in
               ('hp1020_xtensa_call0.py', 'hp1020_xtensa_properties.py',
                'hp1020_xtensa_stock.py', 'hp1020_qemu_ram.py')]]
    result = dict(stock_elf_sha256=elf_hash,
                  sources={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in sources},
                  qemu=version, paired_slices=17, first_pool_address=hex(FIRST),
                  reserved_after_bss=0x4000, cases=rows,
                  limits=['Register 0xb0800008 is supplied, never read.',
                          'No boot, MMIO, cache, TLB, interrupt or semaphore operation executes.',
                          'Installed capacity, physical mapping and loader ABI remain unproved.',
                          'Stock pool extent includes the boot SP and reset/debug sections; '
                          'it is not a safe replacement allocator layout.'])
    (ROOT/'analysis/boot-handoff/memory-contract.json').write_text(json.dumps(result, indent=2)+'\n')
    print('PASS: 17 original memory-arithmetic slices agree with QEMU; no boot or hardware evidence.')


if __name__ == '__main__':
    main()
