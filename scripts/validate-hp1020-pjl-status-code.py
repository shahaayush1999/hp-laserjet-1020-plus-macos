#!/usr/bin/env python3
"""Recover the omitted stock PJL CODE lookup; execute only numeric conversion."""
import hashlib
import json
import os
from pathlib import Path

from hp1020_xtensa_call0 import Machine, Program
from hp1020_xtensa_stock import StockMachine
from hp1020_qemu_ram import QemuRAM
from hp1020_qemu_task import run_task

ROOT = Path(__file__).resolve().parents[1]
ENTRY, MEDIA, LOCK, UNLOCK = 0x1000a2a4, 0x1000a280, 0x100111b4, 0x100111d8
DATA = 0x22000000


class Converter(StockMachine):
    def __init__(self, program, media, source, fill=0):
        super().__init__(program, ENTRY, [(MEDIA, 0x1000a332)], [(DATA, 32)])
        self.put(DATA, bytes([fill])*32)
        self.write(DATA+8, 4, media)
        self.write(DATA+16, 4, source)
        self.lock_calls = []

    def bytes_at(self, address, size):
        data, offset = self.span(address, size)
        return bytes(data[offset:offset+size])

    def extension(self, op, args, nxt):
        if op != 'call8' or args[0] not in (LOCK, UNLOCK):
            return super().extension(op, args, nxt)
        assert self.registers[10] == 31
        self.lock_calls.append(args[0])
        self.registers[10] = DATA+8 if args[0] == LOCK else 0
        self.branch_taken = True
        return nxt


def first(rows, key):
    return next((value for item, value in rows if item == key), 0)


def reference(word, media, source, codes, offsets):
    low = word & 0xffff
    if low & 0xff00 == 0x100 or word & 0x20000 and not word & 0x80000000:
        return 10001
    if low == 0x1001:
        return (41000+first(offsets, media)+(100*(source+1) if source else 0)) & 0xffffffff
    code = first(codes, low)
    return code if code or word & 0x80000000 else 10001


def main():
    program = Program(ROOT/'analysis/sihp1020.elf', os.environ.get('XTENSA_PREFIX',
        '/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf'))
    memory = Machine(program)
    # Critical bounds/stride are actual instructions, not the truncated Ghidra
    # output or inferred C array sizes. Both loops read beyond their usual rows.
    expected = {
        0x1000a28a: ('movi', (3, 40), '230a28'),
        0x1000a29e: ('addi.n', (4, 4, 4), 'b444'),
        0x1000a307: ('movi', (8, 222), '280ade'),
        0x1000a316: ('addi.n', (9, 9, 4), 'b499'),
        0x1000a2b1: ('call8', (LOCK,), '581bc0'),
        0x1000a32d: ('call8', (UNLOCK,), '581baa'),
    }
    for pc, (op, operands, raw) in expected.items():
        assert program.instruction(pc) == (op, operands, bytes.fromhex(raw))
    assert [memory.read(a, 4) for a in (0x10006014, 0x10006018, 0x1000601c, 0x10006020)] == [0x1001be40,10001,41000,0x1001bc84]
    codes = [(memory.read(0x1001bc84+i*4, 2), memory.read(0x1001bc86+i*4, 2)) for i in range(222)]
    offsets = [(memory.read(0x1001be40+i*4, 2), memory.read(0x1001be42+i*4, 2)) for i in range(40)]
    ordinary = codes[:111]
    assert len({key for key, _ in ordinary}) == 111
    # Every normal table row, the direct/default precedence, unknown keys,
    # both adjacent-data lookup tails and bounded media arithmetic.
    inputs = {(flags|key, 1, 0) for key, _ in ordinary for flags in (0,0x80000000,0x20000,0x80020000)}
    inputs |= {(flags|key, 1, 0) for key in (0,1,0x100,0x1ff,0xffff,0x4050,0x504a)
               for flags in (0,0x80000000,0x20000,0x80020000)}
    inputs |= {(0x80001001, media, source) for media, _ in offsets for source in (0,1,2,0xffffffff)}
    inputs |= {(0x80001001, 0xffff, 0), (0x1001, 1, 2), (0x21001, 1, 2)}
    visited = set(); steps = 0; observations = []
    for word, media, source in sorted(inputs):
        state = Converter(program, media, source, 0xcc)
        before = state.bytes_at(DATA, 32)
        actual = state.run([word])
        wanted = reference(word, media, source, codes, offsets)
        assert actual == wanted, (hex(word), media, source, actual, wanted)
        assert state.lock_calls == [LOCK, UNLOCK] and state.bytes_at(DATA, 32) == before
        observations.append([word,media,source,actual]);visited |= state.visited;steps += state.steps
    # Independent real windowed execution covers first/last/middle table rows,
    # precedence, the over-read aliases, unknown offline suppression and media.
    selected = [(0x80000000|ordinary[i][0],1,0) for i in (0,15,55,90,110)]
    selected += [(v,1,0) for v in (0x100,0x800001ff,0x21100,0x80021100,0xffff,
                                  0x8000ffff,0x80000001,0x80004050,0x8000504a)]
    selected += [(0x80001001,k,s) for k,s in ((1,0),(1,2),(0x100,1),(0x4050,0),(0xffff,0),(1,0xffffffff))]
    native = []
    with QemuRAM() as q:
        for word, media, source in selected:
            state = Converter(program,media,source,0xcc)
            before = state.bytes_at(DATA,32)
            value = run_task(state,q,{LOCK,UNLOCK},args=[word])
            assert value == reference(word,media,source,codes,offsets)
            assert state.lock_calls == [LOCK,UNLOCK] and state.bytes_at(DATA,32) == before
            native.append(dict(word=f'0x{word:08x}',media=media,source=source,code=value))
            print(f'Original CODE: {word:#010x} -> {value}',flush=True)
        version = q.version
    sources = ('validate-hp1020-pjl-status-code.py','hp1020_xtensa_call0.py','hp1020_xtensa_stock.py',
        'hp1020_xtensa_properties.py','hp1020_qemu_ram.py','hp1020_qemu_task.py','hp1020_qemu_stock_parser.py')
    report = dict(status='pass', elf_sha256=hashlib.sha256(program.path.read_bytes()).hexdigest(),
        source_sha256={'scripts/'+n:hashlib.sha256((ROOT/'scripts'/n).read_bytes()).hexdigest() for n in sources},
        interpreted_cases=len(inputs), interpreted_instructions=steps, distinct_instructions=len(visited),
        observations_sha256=hashlib.sha256(json.dumps(observations).encode()).hexdigest(),
        qemu_version=version, native_cases=native,
        code_table_address='0x1001bc84',code_loop_entries=222,ordinary_code_rows=ordinary,
        offset_table_address='0x1001be40',offset_loop_entries=40,ordinary_offset_rows=offsets[:20],
        adjacent_data_aliases=dict(code_rows=codes[111:],offset_rows=offsets[20:]),
        limits='Original converter and lookup execute, with datastore31 lock/unlock and its values supplied. No StatusMgr delivery, language callback, DISPLAY/ONLINE sampling or physical sensor state is proved. The oversized stock loop bounds are findings, not requirements for a replacement.')
    (ROOT/'analysis/status-path/status-code-execution.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(f'Original CODE conversion: {len(inputs)} interpreter, {len(native)} QEMU cases passed')


if __name__ == '__main__':
    main()
