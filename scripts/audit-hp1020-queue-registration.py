#!/usr/bin/env python3
"""Recover queue IDs from stock constructor control flow, without executing it.

Constant propagation joins both branch successors, including the StatusMgr loop.
Calls conservatively destroy a8..a15 according to CALL8 ABI; memory effects are
not simulated. Only immutable ELF literal words are read. In particular, engine
constructor MMIO is inspected as bytes, never executed or supplied fake values.
The separate registration helper runs in bounded synthetic RAM and QEMU.
"""
from collections import deque
import hashlib
import json
import os
from pathlib import Path

from hp1020_xtensa_call0 import Program
from hp1020_xtensa_stock import StockMachine
from hp1020_qemu_ram import QemuRAM

ROOT = Path(__file__).resolve().parents[1]
REGISTER = 0x100135e0
CREATE = 0x10017f18


def propagate(program, memory, start, stop):
    incoming = {start: (None,) * 16}
    pending = deque([start])
    while pending:
        pc = pending.popleft()
        if pc == stop:
            continue
        op, args, raw = program.instruction(pc)
        op = op.removesuffix('.n')
        r = list(incoming[pc])
        successors = [pc + len(raw)]
        if op == 'movi':
            r[args[0]] = args[1] & 0xffffffff
        elif op == 'l32r':
            address = args[1]
            assert not any(a <= address < b for a, b in program.write_ranges)
            r[args[0]] = memory.read(address, 4)
        elif op == 'mov':
            r[args[0]] = r[args[1]]
        elif op in ('or', 'addx4', 'addi', 'extui'):
            dst, src = args[:2]
            x = r[src]
            y = r[args[2]] if op in ('or', 'addx4') else args[2]
            if x is None or y is None:
                r[dst] = None
            elif op == 'or':
                r[dst] = x | y
            elif op == 'addx4':
                r[dst] = (x * 4 + y) & 0xffffffff
            elif op == 'addi':
                r[dst] = (x + y) & 0xffffffff
            else:
                r[dst] = (x >> y) & ((1 << args[3]) - 1)
        elif op == 'bgeu':
            # Explore both paths even when a local constant chooses one.
            successors.append(args[2])
        elif op == 'call8':
            r[8:] = [None] * 8
        elif op == 'l32i':
            r[args[0]] = None
        elif op == 'entry':
            r[args[0]] = None
        elif op not in ('s32i', 's8i', 'memw'):
            raise ValueError(f'unhandled constructor instruction {pc:#x}: {op}')
        for target in successors:
            assert start <= target <= stop, (hex(pc), hex(target))
            old = incoming.get(target)
            merged = tuple(r) if old is None else tuple(a if a == b else None for a, b in zip(old, r))
            if old != merged:
                incoming[target] = merged
                pending.append(target)
    return incoming


def build_report():
    program = Program(ROOT / 'analysis/sihp1020.elf', os.environ.get('XTENSA_PREFIX', '/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf'))
    memory = StockMachine(program, REGISTER, [(REGISTER, 0x10013600)])
    table = memory.read(0x100066f0, 4)
    sites = sorted(pc for pc, (op, args, _) in program.instructions.items() if op == 'call8' and args == (REGISTER,))
    rows = []
    for site in sites:
        start = max(pc for pc, (op, _, _) in program.instructions.items() if op == 'entry' and pc < site)
        states = propagate(program, memory, start, site)
        queue, obj = states[site][10:12]
        assert queue is not None and obj is not None
        creates = [(pc, state[10:15]) for pc, state in states.items()
                   if program.instruction(pc)[:2] == ('call8', (CREATE,)) and state[10] == obj]
        assert len(creates) == 1
        create, (_, name, words, buffer, size) = creates[0]
        assert None not in (name, words, buffer, size)
        text = bytearray()
        while (c := memory.read(name + len(text), 1)) != 0:
            text.append(c)
            assert len(text) < 80
        rows.append(dict(queue=queue, object=hex(obj), name=text.decode('ascii'),
                         constructor=hex(start), registration=hex(site), create=hex(create),
                         message_words=words, buffer=hex(buffer), buffer_bytes=size,
                         instruction_count=len(states)))
    assert {r['queue']: r['object'] for r in rows} == {
        0:'0x1002f134', 1:'0x10028a74', 3:'0x10023e40', 4:'0x1002c9f8',
        8:'0x1002ee38', 10:'0x10028adc', 15:'0x1001d694'}
    cases = []
    with QemuRAM() as q:
        q.load(program.path)
        for index in list(range(22)) + [0xffffffff, 0x80000000]:
            for occupied in (0, 0x22000100):
                initial = b''.join(occupied.to_bytes(4, 'big') for _ in range(19))
                expected = bytearray(initial)
                result = 0xffffffff
                if index <= 18 and not occupied:
                    expected[index*4:index*4+4] = (0x22000200).to_bytes(4, 'big')
                    result = 0
                model = StockMachine(program, REGISTER, [(REGISTER, 0x10013600)])
                model.put(table, initial)
                assert model.run([index, 0x22000200]) == result
                data, off = model.span(table, len(expected))
                assert data[off:off+len(expected)] == expected
                q.put(table, initial)
                assert q.call8(REGISTER, [index, 0x22000200]) == result
                assert q.read(table, len(expected)) == expected
                cases.append(dict(index=index, occupied=bool(occupied), result=result))
    return dict(status='pass', table=hex(table), registrations=sorted(rows, key=lambda r:r['queue']),
                helper_cases=cases, elf_sha256=hashlib.sha256(program.path.read_bytes()).hexdigest(),
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                scope='All seven annotated direct CALL8 registration sites. Conservative control-flow constant propagation, with explicit CALL8 preservation of a0..a7. Registration helper separately agrees with a table-update oracle in both interpreter and QEMU.',
                limits='Constructors and their MMIO are never executed. This does not prove boot order, successful RTOS creation, indirect registrations or queue delivery on hardware.')


def main():
    report = build_report()
    out = ROOT / 'analysis/queue-routing'
    (out / 'registration.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    lines = ['# Stock queue registration audit', '', report['scope'], '',
             '| ID | Original queue name | Object | Constructor | Registration call |',
             '|---:|---|---|---|---|']
    for r in report['registrations']:
        lines.append(f"| {r['queue']} | {r['name']} | `{r['object']}` | `{r['constructor']}` | `{r['registration']}` |")
    lines += ['', f"Registration bounds and occupied-slot behavior agree in {len(report['helper_cases'])} independent QEMU/interpreter cases.", '',
              'Correction: older queue maps reversed IDs 0 and 1 and mistook the JobMgr task object for its queue. Queue 1 is PrintMgr; queue 0 is engine. Datastore notifications to queue 1 therefore do reach the PrintMgr dispatch path.', '', report['limits'], '']
    (out / 'registration.md').write_text('\n'.join(lines))
    print(f"Queue registration: {len(report['registrations'])} recovered IDs, {len(report['helper_cases'])} helper cases")


if __name__ == '__main__':
    main()
