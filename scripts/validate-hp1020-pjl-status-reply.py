#!/usr/bin/env python3
"""Execute original status reply builders against supplied RAM observations.

Only datastore locks, signed decimal formatting, allocation and the final
language callback are hosted. No status acquisition, printer or MMIO executes.
"""
import hashlib
import json
import os
from pathlib import Path

from hp1020_qemu_ram import QemuRAM
from hp1020_qemu_task import run_task
from hp1020_xtensa_call0 import Program, signed
from hp1020_xtensa_stock import StockMachine

ROOT = Path(__file__).resolve().parents[1]
ELF_SHA256 = '2111560068db47ceca21fa550db4c7c34f5595b5a5d137ae4a19631e40e3601d'
QUERY, INFO, DEVICE = 0x1000bfb0, 0x1000c568, 0x1000b6d8
LOCK, UNLOCK, FORMAT, ALLOCATE = 0x100111b4, 0x100111d8, 0x10007430, 0x1000dc00
DATA, CLIENT, OUTPUT, ALLOCATION, CALLBACK = (0x22000000, 0x22000020,
    0x22000060, 0x22000200, 0x220003f0)
HOST = {LOCK, UNLOCK, FORMAT, ALLOCATE, CALLBACK}
CODE = [(0x1000a280,0x1000a332), (0x1000b1c4,0x1000b1d2),
        (0x1000b290,0x1000b2a8), (0x1000b624,0x1000b774),
        (QUERY,0x1000bfc8), (INFO,0x1000c699), (0x1000cd44,0x1000cd62),
        (0x10011178,LOCK), (0x1001684c,0x10016a38), (0x1001b544,0x1001b56c)]
SOURCES = ('validate-hp1020-pjl-status-reply.py', 'hp1020_xtensa_call0.py',
    'hp1020_xtensa_stock.py', 'hp1020_xtensa_properties.py', 'hp1020_qemu_ram.py',
    'hp1020_qemu_task.py', 'hp1020_qemu_stock_parser.py')


def source_hashes():
    return {'scripts/'+name:hashlib.sha256((ROOT/'scripts'/name).read_bytes()).hexdigest()
            for name in SOURCES}


def reply_body(code, online):
    return f'CODE={signed(code)}\r\nDISPLAY=""\r\nONLINE={"TRUE" if online else "FALSE"}\r\n'.encode()


class Reply(StockMachine):
    def __init__(self, program, case):
        entry = {'query':QUERY, 'info':INFO, 'device':DEVICE}[case['kind']]
        super().__init__(program, entry, CODE, [(DATA,1024)])
        self.case = case
        self.put(DATA, b'\xcc'*1024)
        self.output = OUTPUT+case.get('alignment',0)
        self.put(self.output, b'\0')
        self.write(CLIENT+16,4,CALLBACK)
        self.write(self.read(0x100060bc,4),4,CLIENT)
        self.table = self.read(0x1000647c,4)
        self.display = self.read(self.table+26*24+4,4)
        assert self.display == 0x1001cdbc
        assert self.read(self.table+26*24+16,2) == 68
        assert self.bytes_at(self.display,68) == bytes(68)
        self.write(self.value_pointer(25),4,case['event'])
        self.write(self.value_pointer(24),1,case['online'])
        self.write(self.value_pointer(31),4,case.get('media',1))
        self.write(self.value_pointer(31)+8,4,case.get('source',0))
        self.values_before = self.bytes_at(0x1001cdb0,0x64)
        self.scratch = self.read(0x100060d4,4)
        self.put(self.scratch,b'\xcc'*256)
        self.locks = []
        self.locked = set()
        self.formats = []
        self.allocations = []
        self.delivered = []
        self.arguments = ([self.output] if case['kind']=='query' else
                          [0x100040ac] if case['kind']=='info' else [CLIENT,case['event']])

    def bytes_at(self, address, size):
        data, offset = self.span(address,size)
        return bytes(data[offset:offset+size])

    def string(self, address, limit=256):
        result = bytearray()
        for index in range(limit):
            value = self.read(address+index,1)
            if value == 0:
                return bytes(result)
            result.append(value)
        raise ValueError('unterminated fixture string')

    def value_pointer(self, key):
        return self.read(self.table+key*24+4,4)

    def extension(self, op, args, nxt):
        target = self.registers[args[0]] if op=='callx8' else args[0] if op=='call8' else None
        if target not in HOST:
            return super().extension(op,args,nxt)
        a,b,c = self.registers[10:13]
        if target == LOCK:
            assert a in (26,31) and a not in self.locked
            self.locked.add(a)
            self.locks.append(['lock',a])
            result = self.value_pointer(a)
        elif target == UNLOCK:
            assert a in self.locked
            self.locked.remove(a)
            self.locks.append(['unlock',a])
            result = 0
        elif target == FORMAT:
            # Original call and original "%d" literal; printf internals are
            # outside this check. The caller does not use the return value.
            assert b == self.read(0x10006090,4) == 0x100040c8
            assert self.string(b) == b'%d' and c == self.case['code']
            start = self.output if self.case['kind']=='query' else self.scratch
            assert a == start+len(self.string(start))
            assert self.string(start).endswith(b'CODE=')
            value = str(signed(c)).encode()
            self.put(a,value+b'\0')
            self.formats.append(dict(format='%d',argument=c,text=value.decode()))
            result = len(value)
        elif target == ALLOCATE:
            assert not self.allocations and 0 < a < 256
            assert a == len(self.string(self.scratch))+1
            self.allocations.append(a)
            result = 0 if self.case.get('allocation_failure') else ALLOCATION
        else:
            assert a == CLIENT and b == ALLOCATION and not self.delivered
            value = self.string(b)
            assert c == len(value) and self.allocations == [c+1]
            self.delivered.append(value)
            result = 0
        self.registers[10] = result
        self.branch_taken = True
        return nxt

    def check(self, returned):
        kind, code = self.case['kind'], self.case['code']
        body = reply_body(code,self.case['online'])
        suppressed = kind=='device' and code==0
        expected = body if kind=='query' else (b'@PJL INFO STATUS\r\n' if kind=='info'
                   else b'@PJL USTATUS DEVICE\r\n')+body+b'\x0c'
        if suppressed:
            assert self.bytes_at(self.scratch,256) == b'\xcc'*256
            assert self.formats == self.allocations == self.delivered == []
            expected = None
        else:
            assert self.formats == [dict(format='%d',argument=code,text=str(signed(code)))], (self.case,self.formats)
            if kind=='query':
                assert returned == 1 and self.string(self.output) == expected
                assert self.bytes_at(self.output+len(expected)+1,8) == b'\xcc'*8
                assert not self.allocations and not self.delivered
            else:
                assert self.string(self.scratch) == expected
                assert self.bytes_at(self.scratch+len(expected)+1,8) == b'\xcc'*8
                if self.case.get('allocation_failure'):
                    assert self.allocations == [len(expected)+1] and not self.delivered
                else:
                    assert self.delivered == [expected]
                    assert self.bytes_at(ALLOCATION+len(expected)+1,8) == b'\xcc'*8
                if kind=='info':
                    assert returned == 1
        wanted_locks = [['lock',31],['unlock',31]]
        if kind=='device' and not suppressed:
            wanted_locks *= 2
        if not suppressed:
            wanted_locks += [['lock',26],['unlock',26]]
        assert self.locks == wanted_locks and not self.locked
        assert self.bytes_at(0x1001cdb0,0x64) == self.values_before
        return dict(**self.case, expected_text=None if expected is None else expected.decode(),
                    expected_hex=None if expected is None else expected.hex(),
                    delivered=len(self.delivered),lock_calls=self.locks,
                    allocation_sizes=self.allocations,format_calls=self.formats)


def main():
    sources = source_hashes()
    path = ROOT/'analysis/sihp1020.elf'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == ELF_SHA256
    program = Program(path,os.environ.get('XTENSA_PREFIX',
        '/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf'))
    for pc, op, args, raw in (
        (0x1000bfb8,'call8',(0x10011178,),'58146f'),
        (0x1000bfbf,'call8',(0x1000b624,),'5bfd99'),
        (0x1000b650,'call8',(FORMAT,),'5bef77'),
        (0x1000b6e3,'bnez.n',(10,0x1000b6e8),'cca1'),
        (0x1000c63d,'call8',(QUERY,),'5bfe5c'),
        (0x1000b2a3,'callx8',(8,),'0b8000'),
        (0x1000cd5d,'callx8',(8,),'0b8000')):
        assert program.instruction(pc) == (op,args,bytes.fromhex(raw))
    cases = [
        dict(name='direct_ready_online',kind='query',event=0x100,online=1,code=10001),
        dict(name='direct_ready_offline',kind='query',event=0x100,online=0,code=10001,alignment=1),
        dict(name='direct_cover_code',kind='query',event=0xe6100800,online=0,code=40021),
        dict(name='direct_cartridge_code',kind='query',event=0xe6100e00,online=0,code=40600),
        dict(name='direct_timeout',kind='query',event=0xfe001401,online=0,code=50021),
        dict(name='direct_zero',kind='query',event=0xe6100a01,online=0,code=0),
        dict(name='direct_media',kind='query',event=0x80001001,online=0,media=1,source=2,code=41302),
        dict(name='info_ready',kind='info',event=0x100,online=255,code=10001),
        dict(name='info_zero',kind='info',event=0xe6100a01,online=0,code=0),
        dict(name='info_cover_code',kind='info',event=0xe6100800,online=0,code=40021),
        dict(name='device_cover_code',kind='device',event=0xe6100800,online=0,code=40021),
        dict(name='device_ready',kind='device',event=0x100,online=1,code=10001),
        dict(name='device_zero_suppressed',kind='device',event=0xe6100a01,online=0,code=0),
        dict(name='device_allocation_failure',kind='device',event=0xe6100800,online=0,
             code=40021,allocation_failure=True),
    ]
    observations = []
    visited = set()
    steps = 0
    for case in cases:
        state = Reply(program,case)
        observations.append(state.check(state.run(state.arguments,budget=30000)))
        visited |= state.visited
        steps += state.steps
    chosen = {'direct_ready_online','direct_ready_offline','direct_zero','info_ready','info_zero',
              'device_cover_code','device_zero_suppressed','device_allocation_failure'}
    native = []
    with QemuRAM() as q:
        for case in cases:
            if case['name'] not in chosen:
                continue
            state = Reply(program,case)
            result = state.check(run_task(state,q,HOST,args=state.arguments,budget=30000))
            assert result == next(item for item in observations if item['name']==case['name'])
            native.append(dict(name=case['name'],instructions=state.qemu_steps,
                               vector_entries=state.vector_entries))
            print('Original status reply: '+case['name'],flush=True)
        version = q.version
    assert source_hashes() == sources
    report = dict(status='pass',elf_sha256=ELF_SHA256,source_sha256=sources,
        interpreted_cases=len(cases),interpreted_instructions=steps,
        distinct_instructions=len(visited),observations=observations,qemu_version=version,
        native_cases=native,display=dict(address='0x1001cdbc',length=68,initial_hex=bytes(68).hex()),
        limits=['Original INFO envelope dispatcher, direct query, common reply builder, DEVICE builder, numeric converter, datastore integer getter, append, strcmp, strcpy, strlen and final language-dispatch wrappers execute.',
                'Datastore24 ONLINE,25 event and31 numeric metadata are supplied RAM observations. DISPLAY keeps its original empty bytes; its writer and physical interpretation are not proved.',
                'Datastore lock/unlock are hosted without semaphore contention. Decimal formatting is a shared host boundary asserting original %d literal and signed32 argument; original printf internals do not execute.',
                'Allocation and final language callbacks are supplied. This checks bytes and callback length, not USB transfer or allocation ownership after callback.',
                'DEVICE subscription, StatusMgr delivery and priority filtering are outside this check. No command parser stream, sensors, MMIO, printer, boot or physical output executes.'])
    output = ROOT/'analysis/status-path/status-reply-execution.json'
    output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(f'Original status replies: {len(cases)} interpreter, {len(native)} QEMU cases passed')


if __name__ == '__main__':
    main()
