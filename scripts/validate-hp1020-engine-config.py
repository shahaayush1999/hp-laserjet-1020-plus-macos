#!/usr/bin/env python3
"""Recover original page-setting commands, intercepting every engine operation.

Only original RAM lookup/configuration/dispatch instructions run. Supplied reply
words are boundary inputs, never hardware observations or a simulated engine.
"""
import hashlib
import json
import os
from pathlib import Path

from hp1020_qemu_ram import QemuRAM
from hp1020_qemu_task import run_task
from hp1020_xtensa_call0 import Program
from hp1020_xtensa_stock import StockMachine

ROOT = Path(__file__).resolve().parents[1]
STATE, TABLE, MESSAGE, WORK = 0x1002f0c4, 0x1001cd34, 0x22000000, 0x22000100
IO, POLL, GET = 0x10015c68, 0x10015df8, 0x10011178
RANGES = [(0x10015d14, 0x10015dd0), (0x10016164, 0x1001635c)]
RECORDS = [(1, 0), (2, 2), (0x102, 9), (0x104, 1), (0x105, 3),
           (0x106, 1), (0x107, 1), (0x109, 1), (0x10b, 5), (0x111, 0),
           (0x200, 0), (0x201, 0), (0x202, 0), (0x203, 0), (0x204, 0)]


class Configuration(StockMachine):
    def __init__(self, program, entry, replies=(), poll=0):
        super().__init__(program, entry, RANGES, [(MESSAGE, 512)])
        self.replies, self.poll = list(replies), poll
        self.commands, self.polls, self.gets = [], [], []
        self.put(STATE, b'\xa5'*0x70)
        for off, value in ((0x48, TABLE+16), (0x4c, TABLE), (0x50, 0),
                           (0x54, 3), (0x38, 0), (0x68, 0), (0x6c, 0)):
            self.write(STATE+off, 4, value)
        self.write(STATE+0x58, 1, 0xff)
        self.write(STATE+0x59, 1, 0x20)

    def bytes_at(self, address, size):
        data, offset = self.span(address, size)
        return bytes(data[offset:offset+size])

    def extension(self, op, args, nxt):
        if op == 'call8' and args[0] in (IO, POLL, GET):
            if args[0] == IO:
                self.commands.append(self.registers[10])
                assert self.replies, 'unexpected extra engine request'
                result = self.replies.pop(0)
            elif args[0] == POLL:
                self.polls.append(self.registers[10]);result = self.poll
            else:
                self.gets.append(self.registers[10]);result = 0xdeadbeef
            self.registers[10] = result
            self.branch_taken = True
            return nxt
        return super().extension(op, args, nxt)


def main():
    program = Program(ROOT/'analysis/sihp1020.elf', os.environ.get(
        'XTENSA_PREFIX', '/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf'))
    digest = hashlib.sha256(program.path.read_bytes()).hexdigest()
    assert digest == '2111560068db47ceca21fa550db4c7c34f5595b5a5d137ae4a19631e40e3601d'
    seed = Configuration(program, 0x100162b0)
    assert [(seed.read(TABLE+i*8, 4), seed.read(TABLE+i*8+4, 4))
            for i in range(15)] == RECORDS
    assert program.instruction(0x100162d4)[:2] == ('call8', (GET,))
    rows = []
    sources = [Path(__file__), program.path]+[ROOT/'scripts'/n for n in (
        'hp1020_xtensa_call0.py', 'hp1020_xtensa_stock.py', 'hp1020_xtensa_properties.py',
        'hp1020_qemu_task.py', 'hp1020_qemu_stock_parser.py', 'hp1020_qemu_ram.py')]
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    with QemuRAM() as q:
        def check(name, entry, args=(), replies=(), changes=(), expected=(), commands=(),
                  result=None, table_change=None, polls=(), gets=()):
            a, b = (Configuration(program, entry, replies) for _ in range(2))
            for address, size, value in changes:
                a.write(address, size, value);b.write(address, size, value)
            before = bytearray(a.bytes_at(STATE, 0x70))
            table = bytearray(a.bytes_at(TABLE, 120))
            message = a.bytes_at(MESSAGE, 512)
            for off, size, value in expected:
                before[off:off+size] = value.to_bytes(size, 'big')
            if table_change:
                off, value = table_change
                table[off:off+4] = value.to_bytes(4, 'big')
            ar = a.run(args)
            br = run_task(b, q, {IO, POLL, GET}, args=args, budget=1200)
            assert a.commands == b.commands == list(commands), (name, a.commands, b.commands, commands)
            assert a.polls == b.polls == list(polls) and a.gets == b.gets == list(gets), name
            assert not a.replies and not b.replies, name
            assert ar == br and (result is None or ar == result), (name, ar, br, result)
            for s in (a, b):
                assert s.bytes_at(STATE, 0x70) == before, (name, 'state')
                assert s.bytes_at(TABLE, 120) == table, (name, 'table')
                assert s.bytes_at(MESSAGE, 512) == message, (name, 'input mutation')
                assert not s.visited.intersection((IO, POLL, GET)), name
            rows.append(dict(case=name, commands=[hex(c) for c in commands], result=hex(ar),
                             state_sha256=hashlib.sha256(before).hexdigest()))

        for i, (key, value) in enumerate(RECORDS):
            check(f'lookup-{key:x}', 0x100162b0, [key], result=TABLE+8*i)
        for key in (0, 0xffff):
            check(f'lookup-missing-{key:x}', 0x100162b0, [key], result=0)

        for density, value in enumerate((0, 16, 32, 48, 63), 1):
            check(f'density-{density}', 0x10016318, [15, density], expected=[(0x59, 1, value)])
        for key, density in ((15, 0), (15, 6), (14, 3)):
            check(f'density-ignored-{key}-{density}', 0x10016318, [key, density])
        for key, record in zip(range(16, 21), (2, 4, 8, 1, 0)):
            check(f'media-alias-{key}', 0x100162cc, [key, RECORDS[record][0]],
                  table_change=((10+key-16)*8+4, RECORDS[record][1]), gets=[key])

        media, density, scalar = 0x5492, 0x5340, 0x3306
        check('config-all-accepted', 0x10015d14, replies=[0x4000, 0, 0, 0],
              commands=[1, media, density, scalar], expected=[(0x4c, 4, TABLE+16), (0x50, 4, 3)], result=1)
        check('config-media-rejected', 0x10015d14, replies=[0x4000, 0x8000, 0, 0],
              commands=[1, media, density, scalar], expected=[(0x50, 4, 3)], result=1)
        check('config-scalar-rejected', 0x10015d14, replies=[0x4000, 0, 0, 0x8000],
              commands=[1, media, density, scalar], expected=[(0x4c, 4, TABLE+16)], result=1)
        check('config-density-reply-not-cached', 0x10015d14, replies=[0x4000, 0, 0xffff, 0],
              commands=[1, media, density, scalar], expected=[(0x4c, 4, TABLE+16), (0x50, 4, 3)], result=1)
        for primary in (0, 0x4400, 0x6000, 0xffff):
            check(f'config-ineligible-{primary:x}', 0x10015d14, [0x12345678], replies=[primary],
                  commands=[1], result=0x12345678 if primary == 0xffff else 1)
        check('config-unchanged', 0x10015d14, replies=[0x4000], commands=[1], result=1,
              changes=[(STATE+0x4c, 4, TABLE+16), (STATE+0x58, 1, 0x20), (STATE+0x50, 4, 3)])
        check('config-full-word-compare-low16-command', 0x10015d14, replies=[0x4000, 0, 0, 0],
              commands=[1, media, density, scalar], result=1,
              changes=[(STATE+0x54, 4, 0x12340003)],
              expected=[(0x4c, 4, TABLE+16), (0x50, 4, 0x12340003)])

        # Execute the genuine dispatcher, lookup and configuration chain. Only
        # status polling and the command primitive are supplied boundaries.
        for name, message_kind, work_kind, responses, cmds, latch in (
            ('normal-page-start', 11, 6, [0x4000, 0, 0, 0, 0], [1, media, density, scalar, 0x6012], 0),
            ('message40-start', 64, 6, [0x4000, 0, 0, 0, 0x8000], [1, media, density, scalar, 0x3a13], 1),
            ('kind7-start', 11, 7, [0x4000, 0, 0, 0, 0], [1, media, density, scalar, 0x3a13], 1),
            ('start-after-config-primary-timeout', 11, 6, [0xffff, 0], [1, 0x6012], 0),
            ('start-after-config-rejections', 11, 6, [0x4000, 0x8000, 0, 0x8000, 0], [1, media, density, scalar, 0x6012], 0)):
            expected = [(0x28, 1, 0), (0x68, 4, WORK), (0x38, 4, latch)]
            if responses[0] != 0xffff and responses[1] == 0:
                expected += [(0x4c, 4, TABLE+16), (0x50, 4, 3)]
            check(name, 0x10016164, [MESSAGE], replies=responses, commands=cmds, result=0, polls=[0],
                  changes=[(MESSAGE, 4, message_kind), (MESSAGE+12, 4, WORK),
                           (WORK, 4, work_kind), (WORK+0x80, 2, 0x102)], expected=expected)
        version = q.version
    assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest() == h for n, h in hashes.items())
    report = dict(status='pass', source_sha256=hashes, qemu_version=version,
                  records=[dict(key=hex(k), value=hex(v)) for k, v in RECORDS], cases=rows,
                  limits='Original RAM lookup, callbacks, configuration and page-start dispatch only. Status polling, datastore reads and every engine command are intercepted. Reply values are supplied independently; there is no physical engine, command transmission, timing, status freshness, sensor calibration or successful printing.')
    (ROOT/'analysis/hardware-boundary/engine-config-execution.json').write_text(json.dumps(report, indent=2)+'\n')
    print(f'PASS: {len(rows)} original configuration cases agree with QEMU; all engine operations excluded.')


if __name__ == '__main__':
    main()
