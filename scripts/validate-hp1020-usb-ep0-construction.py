#!/usr/bin/env python3
"""Bounded offline experiment for original EP0 descriptor-construction slices.

Explicit mid-function register/RAM cuts; no original ENTRY, setup, copy, cache,
controller, event wait, completion or USB lifecycle is executed. No MMIO is
redirected or allowed. Raw captures are retained below a new /tmp directory.
The separate initialization pointer ADD cut does not execute HOST_BUSY setup.
"""
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import sys
import tempfile
from types import SimpleNamespace

DEFAULT_ROOT = Path(__file__).resolve().parents[1] if Path(__file__).parent.name == 'scripts' else Path.cwd()
ROOT = Path(os.environ.get('HP1020_ROOT', str(DEFAULT_ROOT))).resolve()
OUT = ROOT/'analysis/usb-path/ep0-construction'
sys.path.insert(0, str(ROOT/'scripts'))
from hp1020_xtensa_call0 import Program, Machine, STOP, STACK, STACK_SIZE
from hp1020_xtensa_properties import properties, section_bytes
from hp1020_stock_stop import StopRAM
from hp1020_qemu_multitask import NativeTasks
from hp1020_qemu_stock_parser import guard_memory
from hp1020_qemu_ram import QemuRAM, STACK_TOP

STOCK_SHA = '2111560068db47ceca21fa550db4c7c34f5595b5a5d137ae4a19631e40e3601d'
ARENA, ARENA_SIZE = 0x22900000, 0x1000
DESC_CELL, BUFFER_CELL, MPS_CELL = ARENA+0x40, ARENA+0x44, ARENA+0x48
DESCRIPTOR, TRANSFER = ARENA+0x100, ARENA+0x300
OUT_DESC_CELL, OUT_BUFFER_CELL = 0x1001bc60, 0x1001bc68
INITIAL_SP = STACK_TOP-0x100
EMPTY_FIXTURE = SimpleNamespace(path=None, execute_ranges=[])
ZERO_CODE = [(0x10008c7e, 0x10008d0c)]
SMALL_CODE = [(0x10008d3f, 0x10008d48), (0x10008e04, 0x10008e9e), (0x10008f08, 0x10008f1b)]
OUT_CODE = [(0x10009136, 0x100091a5)]
POINTER_CODE = {
    'active-zero-pointer': [(0x10008d02, 0x10008d0c)],
    'active-small-pointer': [(0x10008f11, 0x10008f1b)],
    'initial-add-pointer': [(0x100092aa, 0x100092ba)],
}
CODE_SHA = {
    (0x10008c7e, 0x10008d0c): 'f3ccbef6ac98b155493bd134f6289d86bf623f2a6b9c119160236fe59f686c5c',
    (0x10008d3f, 0x10008d48): 'ee389efb73219f7b0dff87937a3a9a7097b817dd7e4a9c8ba4e1d02b3a84e768',
    (0x10008e04, 0x10008e9e): '00b5605c93b5eed7836f8eb9fb74cc5b4497994cc52c64f837c39a0fd58af16c',
    (0x10008f08, 0x10008f1b): 'aea219d04fa3b78d41df581b49439442b428292f2ae61212383b77473460ced1',
    (0x10009136, 0x100091a5): '36e017fbd4bc78745802045ba868efd3dee32aaa7fd648840bf2f574350d0394',
    (0x10008d02, 0x10008d0c): 'ddeca3b72238f6299a6dac1ae3e7d7071b347c3329129b783bd2c6b88b546b2a',
    (0x10008f11, 0x10008f1b): '832335e978449edd10c9bf43d3482ad835c3dac0ea19224045641c77c7f29de4',
    (0x100092aa, 0x100092ba): 'a05d02486bb6ca34fbe31d0af26edb2224bcb9f02f082fb9671fdd8f5afdf1a8',
    (0x10008c7c, 0x10008c7e): '7ea7187532e1d4da5a3063ae81b4f26f8856cec2209c5b638b6be2b4669475e6',
    (0x10008d0c, 0x10008d0e): '127f84f987ba91909a4312a9db2b2b8f7df2e74e06271eecc4d90e11fad7ea71',
    (0x10008f1b, 0x10008f1d): '127f84f987ba91909a4312a9db2b2b8f7df2e74e06271eecc4d90e11fad7ea71',
    (0x10009129, 0x1000912b): '09cd5286d20449d26118f49dea6130c4d172a47a12f8524fc7428ec594887d59',
    (0x100091b0, 0x100091b2): '127f84f987ba91909a4312a9db2b2b8f7df2e74e06271eecc4d90e11fad7ea71',
    (0x100091c7, 0x100091c9): 'f2ef6aa7be8d6cbb1e59c358b427205e1ed97121fb51b3df0a9641aa1a1de861',
    (0x100092ba, 0x100092bc): 'f2ef6aa7be8d6cbb1e59c358b427205e1ed97121fb51b3df0a9641aa1a1de861',
}
LITERALS = {
    0x10005e18: 0x10021318, 0x10005e34: 0x80000000,
    0x10005e80: 0x08000000, 0x10005ea0: 0xb3000014,
    0x10005eac: 0xb3010000, 0x10005eec: OUT_DESC_CELL,
    0x10005ef0: OUT_BUFFER_CELL,
}
ANCHORS = {
    0x10008c7e: ('l32i.n', (9, 12, 0), '89c0'),
    0x10008c97: ('mov.n', (15, 11), 'dfb0'),
    0x10008cc0: ('add.n', (9, 9, 8), 'a899'),
    0x10008cfc: ('s32i.n', (15, 7, 60), '9f7f'),
    0x10008d3f: ('movi', (15, 0), '2f0a00'),
    0x10008d42: ('bltu', (8, 9, 0x10008d48), '798302'),
    0x10008d45: ('j', (0x10008e04,), '6000bb'),
    0x10008e04: ('bnei', (15, 5, 0x10008e0a), '69f502'),
    0x10008e0f: ('l32i.n', (8, 6, 0), '8860'),
    0x10008e61: ('add.n', (9, 9, 8), 'a899'),
    0x10008e99: ('s32i.n', (2, 5, 60), '925f'),
    0x10008e9b: ('j', (0x10008f08,), '600069'),
    0x1000912d: ('movi.n', (7, 0), 'c070'),  # Static only: this zero definition is omitted.
    0x10009136: ('l32r', (8, 0x10005ef0), '18f36e'),
    0x10009139: ('l32r', (12, 0x10005eec), '1cf36c'),
    0x10009179: ('movi.n', (4, 8), 'c048'),
    0x100092aa: ('l32i.n', (8, 11, 0), '88b0'),
    0x100092ac: ('l32r', (9, 0x10005e34), '19f2e2'),
    0x100092b2: ('add.n', (8, 8, 9), 'a988'),
}
STORE_PCS = {
    'in-zero': [0x10008c83,0x10008c89,0x10008c8f,0x10008c92,
        0x10008c99,0x10008c9c,0x10008c9f,0x10008ca2,
        0x10008ca7,0x10008caa,0x10008cad,0x10008cb0,
        0x10008cc8,0x10008cd9,0x10008cea,0x10008cf9],
    'in-small': [0x10008e20,0x10008e26,0x10008e2c,0x10008e2f,
        0x10008e36,0x10008e39,0x10008e3c,0x10008e3f,
        0x10008e46,0x10008e49,0x10008e4c,0x10008e4f,
        0x10008e69,0x10008e78,0x10008e87,0x10008e96],
    'out-zero': [0x10009143,0x10009149,0x1000914f,0x10009152,
        0x10009157,0x1000915a,0x1000915d,0x10009160,
        0x10009165,0x10009168,0x1000916b,0x1000916e,
        0x1000917e,0x1000918a,0x10009196,0x100091a2],
}
STORE_OFFSETS = (8,9,10,11,4,5,6,7,12,13,14,15,0,1,2,3)
# None of these may be reached from any construction-only range.
EXCLUDED = (0x10008c24,0x10008c35,0x10008c44,0x10008c69,
    0x10008c7c,0x10008d0c,0x10008d25,0x10008d48,0x10008e9e,
    0x10008f1b,0x10008f30,0x10009129,0x10009132,0x10009134,
    0x100091a5,0x100091b0,0x100091c7,0x100092ba)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def access(pc, kind, address, size, value):
    return dict(pc=hex(pc), kind=kind, address=hex(address), size=size, value=hex(value))


def patterned(seed, address, size):
    # Nonuniform/asymmetric guard and payload canaries, never all-zero structs.
    return bytes((seed + (address >> 8) + i*17 + (i >> 4)*3) & 255 for i in range(size))


def case_specs():
    for seed in (0x31, 0xcc):
        for pointer in (0x11223340, 0x91b2c3d0, 0x01234567):
            for length in (0,1,18,63,64):
                kind = 'in-zero' if length == 0 else 'in-small'
                yield dict(name=f'{kind}-n{length}-p{pointer:08x}-s{seed:02x}',
                    kind=kind, seed=seed, length=length, pointer=pointer, effect='descriptor')
            yield dict(name=f'out-zero-p{pointer:08x}-s{seed:02x}', kind='out-zero',
                seed=seed, length=0, pointer=pointer, effect='descriptor')
        for kind in POINTER_CODE:
            for pointer in (0x100226f0,0x900226f0):
                yield dict(name=f'{kind}-p{pointer:08x}-s{seed:02x}', kind=kind,
                    seed=seed, length=0, pointer=pointer, effect='pointer')
        yield dict(name=f'excluded-multi-descriptor-n65-s{seed:02x}', kind='in-small',
            seed=seed, length=65, pointer=0x11223340, effect='none', stop=0x10008d48)
        for label, pc, regs in (
            ('zero-mps-read',0x10008c7c,{8:0xb300000c}),
            ('zero-submit',0x10008d0c,{8:DESCRIPTOR,9:0xb3000014}),
            ('small-submit',0x10008f1b,{8:DESCRIPTOR,9:0xb3000014}),
            ('out-mps-write',0x10009129,{5:64,8:0xb300020c}),
            ('out-setup-submit',0x100091b0,{8:DESCRIPTOR,9:0xb3000210}),
            ('out-normal-submit',0x100091c7,{8:DESCRIPTOR,11:0xb3000214}),
            ('initial-in-submit',0x100092ba,{8:0x100226f0,11:0xb3000014}),
        ):
            yield dict(name=f'mmio-{label}-s{seed:02x}', kind='mmio-instruction',
                seed=seed, length=0, pointer=0x11223340, effect='none',
                entry=pc, stop=pc, registers=regs, reject_mmio=True)
        yield dict(name=f'mmio-small-mps-read-s{seed:02x}', kind='in-small',
            seed=seed, length=18, pointer=0x11223340, effect='none',
            stop=0x10008e0f, registers={6:0xb300000c}, reject_mmio=True)


class ConstructionRAM(StopRAM):
    def __init__(self, program, case):
        self.recording, self.events = False, []
        kind = case['kind']
        if kind == 'in-zero':
            code, entry, stop = ZERO_CODE, ZERO_CODE[0][0], ZERO_CODE[-1][1]
        elif kind == 'in-small':
            code, entry, stop = SMALL_CODE, SMALL_CODE[0][0], SMALL_CODE[-1][1]
        elif kind == 'out-zero':
            code, entry, stop = OUT_CODE, OUT_CODE[0][0], OUT_CODE[-1][1]
        elif kind in POINTER_CODE:
            code = POINTER_CODE[kind]
            entry, stop = code[0][0], code[-1][1]
        else:
            assert kind == 'mmio-instruction'
            entry = case['entry']
            code = [(entry,entry+len(program.instruction(entry)[2]))]
            stop = entry
        super().__init__(program, entry, code.copy(), [(ARENA,ARENA_SIZE)])
        self.stop = case.get('stop',stop)
        self.case = case
        for begin,end in self.write_ranges:
            self.put(begin,patterned(case['seed'],begin,end-begin))
        self.write(DESC_CELL,4,DESCRIPTOR)
        self.write(BUFFER_CELL,4,case['pointer'])
        self.write(MPS_CELL,4,64)
        self.write(TRANSFER+60,4,case['length'])
        self.write(OUT_DESC_CELL,4,DESCRIPTOR)
        self.write(OUT_BUFFER_CELL,4,case['pointer'])
        self.registers = [(0x13579bdf+i*0x10203+case['seed']*0x01010101)&0xffffffff for i in range(16)]
        self.registers[0],self.registers[1] = STOP,INITIAL_SP
        if kind == 'in-zero':
            supplied = {2:BUFFER_CELL,7:TRANSFER,10:case['pointer'],11:0,12:DESC_CELL}
        elif kind == 'in-small':
            supplied = {2:0,3:BUFFER_CELL,5:TRANSFER,6:MPS_CELL,7:DESC_CELL,8:64,9:case['length']}
        elif kind == 'out-zero':
            supplied = {7:0}
        elif kind == 'active-zero-pointer':
            self.write(DESC_CELL,4,case['pointer'])
            supplied = {12:DESC_CELL,15:1}
        elif kind == 'active-small-pointer':
            self.write(DESC_CELL,4,case['pointer'])
            supplied = {7:DESC_CELL}
        elif kind == 'initial-add-pointer':
            self.write(DESC_CELL,4,case['pointer'])
            supplied = {11:DESC_CELL}
        else:
            supplied = {}
        supplied.update(case.get('registers',{}))
        for register,value in supplied.items():
            self.registers[register] = value
        self.supplied_registers = self.registers.copy()

    def read(self,address,size):
        value = super().read(address,size)
        if self.recording:
            self.events.append(access(self.pc,'read',address,size,value))
        return value

    def write(self,address,size,value):
        self.span(address,size)  # Uniform pre-access MMIO rejection in both engines.
        super().write(address,size,value)
        if self.recording:
            self.events.append(access(self.pc,'write',address,size,value & ((1 << (8*size))-1)))


def memory_snapshot(state):
    # Include the entire original mutable RAM, stack and guarded synthetic arena.
    # These slices require no stack stores, so even the stack has an exact oracle.
    return {(a,b):state.bytes_at(a,b-a) for a,b in state.write_ranges}


def manifest(memory):
    return [dict(begin=hex(a),end=hex(b),bytes=len(data),sha256=sha(data))
            for (a,b),data in sorted(memory.items())]


def expected_memory(state,before):
    expected = {span:bytearray(data) for span,data in before.items()}
    def replace(address,data):
        found = [(a,b) for a,b in expected if a <= address and address+len(data) <= b]
        assert len(found) == 1
        a,b = found[0]
        expected[a,b][address-a:address-a+len(data)] = data
    writes = []
    if state.case['effect'] == 'descriptor':
        case = state.case
        # Literal independent byte oracle; no decoded instruction or model output
        # supplies the expected flag, count, reserved/next or byte ordering.
        wanted = struct.pack('>4I',0x08000000+case['length'],0,case['pointer'],0)
        replace(DESCRIPTOR,wanted)
        for pc,offset in zip(STORE_PCS[case['kind']],STORE_OFFSETS):
            writes.append(access(pc,'write',DESCRIPTOR+offset,1,wanted[offset]))
        if case['kind'] != 'out-zero':
            replace(TRANSFER+60,bytes(4))
            writes.append(access(0x10008cfc if case['kind']=='in-zero' else 0x10008e99,
                                 'write',TRANSFER+60,4,0))
    return {span:bytes(data) for span,data in expected.items()},writes


def qemu_memory_event(state,q):
    pc = q.reg(0)
    op,args,raw = state.program.instruction(pc)
    if not any(a <= pc and pc+len(raw) <= b for a,b in state.code_ranges):
        return None  # NativeTasks rejects the PC before it can access anything.
    guard_memory(state,q,op,args)
    base = op.removesuffix('.n')
    sizes = {'l8ui':1,'l32i':4,'s8i':1,'s32i':4}
    ar = lambda index:q.reg(((q.reg(38)*4+index)%32)+1)
    if base == 'l32r':
        address,size,kind = args[1],4,'read'
    elif base in sizes:
        address,size = (ar(args[1])+args[2])&0xffffffff,sizes[base]
        kind = 'read' if base.startswith('l') else 'write'
    else:
        return None
    value = int.from_bytes(q.read(address,size),'big') if kind=='read' else ar(args[0])&((1 << (8*size))-1)
    return access(pc,kind,address,size,value)


def execute(case,program,q,capture):
    state = ConstructionRAM(program,case)
    engine = 'interpreter' if q is None else 'qemu'
    directory = capture/case['name']
    directory.mkdir(exist_ok=True)
    stem = directory/engine
    before = memory_snapshot(state)
    expected,writes = expected_memory(state,before)
    supplied = dict(case=case,entry=hex(state.pc),stop_before=hex(state.stop),
        code_ranges=[[hex(a),hex(b)] for a,b in state.code_ranges],
        logical_registers={f'a{i}':hex(v) for i,v in enumerate(state.supplied_registers)},
        ram_inputs=dict(descriptor_cpu=hex(DESCRIPTOR),descriptor_pointer_cell=hex(DESC_CELL),
            buffer_pointer_cell=hex(BUFFER_CELL),mps_cell=hex(MPS_CELL),mps_value=64,
            transfer_state=hex(TRANSFER),out_descriptor_pointer_cell=hex(OUT_DESC_CELL),
            out_buffer_pointer_cell=hex(OUT_BUFFER_CELL)))
    stem.with_suffix('.input.json').write_text(json.dumps(supplied,indent=2,sort_keys=True)+'\n')
    for suffix,data in (('before',before),('expected',expected)):
        stem.with_suffix('.'+suffix+'.bin').write_bytes(b''.join(v for _,v in sorted(data.items())))
    runner,failure = None,None
    try:
        if q is None:
            state.recording = True
            state.run(budget=256)
        else:
            q.load(program.path)
            runner = NativeTasks(q,state,EMPTY_FIXTURE,state.code_ranges,(),instruction_budget=256)
            runner.synchronize(True)
            # Direct mid-function register window. No synthetic CALL8 or original
            # ENTRY is claimed; these slices contain no calls/returns/window ops.
            q.reset_cpu(state.pc)
            for index,value in enumerate(state.supplied_registers,1):
                q.set_reg(index,value)
            while True:
                state.pc = q.reg(0)
                observed = qemu_memory_event(state,q)
                runner.step()
                if observed is not None:
                    state.events.append(observed)
    except Exception as error:
        failure = dict(type=type(error).__name__,reason=str(error),pc=hex(state.pc))
    finally:
        state.recording = False
        if runner is not None:
            runner.synchronize(False)
            state.registers = [q.reg(((q.reg(38)*4+i)%32)+1) for i in range(16)]
    actual = memory_snapshot(state)
    stem.with_suffix('.after.bin').write_bytes(b''.join(v for _,v in sorted(actual.items())))
    attempted = state.visited if q is None or runner is None else runner.visited
    retired = sorted(pc for pc in attempted if pc != state.stop)
    result = dict(status='captured_unchecked',engine=engine,entry=hex(state.code_ranges[0][0]),
        stop_before=hex(state.stop),failure=failure,registers=[hex(x) for x in state.registers],
        descriptor_hex=state.bytes_at(DESCRIPTOR,16).hex(),
        expected_descriptor_hex=(struct.pack('>4I',0x08000000+case['length'],0,case['pointer'],0).hex()
                                 if case['effect']=='descriptor' else None),
        pointer_register_a8=hex(state.registers[8]),
        before_memory=manifest(before),expected_memory=manifest(expected),actual_memory=manifest(actual),
        expected_writes=writes,accesses=state.events,
        original_instructions_retired=[hex(pc) for pc in retired],
        engine_steps=state.steps if runner is None else runner.steps)
    stem.with_suffix('.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    if case.get('reject_mmio'):
        reason = 'MMIO forbidden'
    else:
        reason = ('execution outside selected stock routines: ' if q is None else
                  'native tasks left selected code: ')+hex(state.stop)
    assert failure == dict(type='ValueError',reason=reason,pc=hex(state.stop)), (case,engine,failure)
    if q is not None:
        assert q.reg(0) == state.stop and state.stop not in runner.visited
        assert q.reg(38) == 0 and q.reg(39) == 1
    assert actual == expected, (case,engine,'mutable/guard RAM differs')
    assert [e for e in state.events if e['kind']=='write'] == writes, (case,engine,'write trace differs')
    if case['effect'] == 'descriptor':
        assert state.bytes_at(DESCRIPTOR,16) == struct.pack('>4I',0x08000000+case['length'],0,case['pointer'],0)
        assert state.registers[8] == DESCRIPTOR
    elif case['effect'] == 'pointer':
        wanted = ((case['pointer']+0x80000000)&0xffffffff) if case['kind']=='initial-add-pointer' else case['pointer']
        assert state.registers[8] == wanted, (case,engine,'independent pointer oracle')
    for begin,end in state.code_ranges:
        raw = state.bytes_at(begin,end-begin)
        assert sha(raw) == CODE_SHA[begin,end]
        if q is not None:
            assert q.read(begin,end-begin) == raw
    result.update(status='pass',all_mutable_and_guard_ram_equal=True,
        literal_descriptor_checked=case['effect']=='descriptor',ordered_write_trace_equal=True,
        pointer_oracle_checked=case['effect']=='pointer',original_code_unchanged=True,
        actual_peripheral_accesses=0)
    stem.with_suffix('.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    return result


def source_paths():
    pending,found = [Path(__file__).resolve()],set()
    while pending:
        path = pending.pop()
        if path in found:
            continue
        found.add(path)
        for node in ast.walk(ast.parse(path.read_text())):
            names = [x.name for x in node.names] if isinstance(node,ast.Import) else (
                [node.module] if isinstance(node,ast.ImportFrom) and node.module else [])
            for name in names:
                candidate = ROOT/'scripts'/(name.split('.')[0]+'.py')
                if candidate.is_file() and candidate not in found:
                    pending.append(candidate)
    return sorted(found | {ROOT/'analysis/sihp1020.elf'})


def audit(program,blob):
    assert sha(blob) == STOCK_SHA
    sections,_ = properties(blob)
    allowed = {'l32i','l8ui','s32i','s8i','l32r','movi','mov','add','addi',
               'slli','mull','extui','memw','bltu','bnei','j'}
    ranges,instructions = [],{}
    for (begin,end),digest in CODE_SHA.items():
        raw = section_bytes(blob,sections,begin,end-begin)
        assert sha(raw) == digest
        ranges.append(dict(begin=hex(begin),end=hex(end),bytes=raw.hex(),sha256=digest))
        pc = begin
        while pc < end:
            op,args,encoded = program.instruction(pc)
            assert op.removesuffix('.n') in allowed, (hex(pc),op)
            assert pc+len(encoded) <= end
            assert encoded == section_bytes(blob,sections,pc,len(encoded))
            instructions[hex(pc)] = dict(op=op,args=args,bytes=encoded.hex())
            pc += len(encoded)
        assert pc == end
    for pc,(op,args,encoded) in ANCHORS.items():
        assert program.instruction(pc) == (op,args,bytes.fromhex(encoded))
        assert section_bytes(blob,sections,pc,len(bytes.fromhex(encoded))).hex() == encoded
    original = Machine(program)
    for pc,value in LITERALS.items():
        assert original.read(pc,4) == value
    return dict(ranges=ranges,instructions=instructions,
                static_extra_anchors={hex(k):v for k,v in ANCHORS.items()},
                literals={hex(k):hex(v) for k,v in LITERALS.items()})


def reject_excluded(program,q,capture):
    case = dict(name='excluded-code',kind='in-zero',seed=0xcc,length=0,pointer=0x11223340,effect='none')
    state = ConstructionRAM(program,case)
    # Use the union of positive construction ranges, but none of the deliberately
    # admitted standalone MMIO instructions used for access-gate controls.
    state.code_ranges = ZERO_CODE+SMALL_CODE+OUT_CODE
    before = memory_snapshot(state)
    q.load(program.path)
    runner = NativeTasks(q,state,EMPTY_FIXTURE,state.code_ranges,(),instruction_budget=32)
    runner.synchronize(True)
    q.reset_cpu(ZERO_CODE[0][0])
    rows = []
    for pc in EXCLUDED:
        state.pc,state.steps,state.visited = pc,0,set()
        try:
            state.run(budget=1)
        except ValueError as error:
            assert str(error) == f'execution outside selected stock routines: {pc:#x}'
        else:
            raise AssertionError(f'excluded interpreter code ran: {pc:#x}')
        assert state.steps == 0 and not state.visited
        q.set_reg(0,pc)
        old_steps,old_visited = runner.steps,runner.visited.copy()
        try:
            runner.step()
        except ValueError as error:
            assert str(error) == f'native tasks left selected code: {pc:#x}'
        else:
            raise AssertionError(f'excluded QEMU code ran: {pc:#x}')
        assert runner.steps == old_steps and runner.visited == old_visited and q.reg(0) == pc
        rows.append(dict(pc=hex(pc),status='rejected before instruction execution in both engines'))
    runner.synchronize(False)
    assert memory_snapshot(state) == before
    (capture/'excluded-code.json').write_text(json.dumps(rows,indent=2)+'\n')
    return rows


def main():
    stock = ROOT/'analysis/sihp1020.elf'
    assert stock.is_file(), 'Run from the repository or set HP1020_ROOT explicitly.'
    capture = Path(tempfile.mkdtemp(prefix='hp1020-ep0-construction-',dir='/tmp'))
    print('EP0 construction captures: '+str(capture),flush=True)
    paths = source_paths()
    origins,sources = {},{}
    for path in paths:
        try:
            name = str(path.relative_to(ROOT))
        except ValueError:
            name = 'draft/'+path.name
        assert name not in origins
        origins[name] = str(path)
        sources[name] = sha(path.read_bytes())
        saved = capture/'source'/name
        saved.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,saved)
        assert sha(saved.read_bytes()) == sources[name]
    (capture/'source-sha256.json').write_text(json.dumps(sources,indent=2,sort_keys=True)+'\n')
    (capture/'source-origins.json').write_text(json.dumps(origins,indent=2,sort_keys=True)+'\n')
    prefix = os.environ.get('XTENSA_PREFIX','/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf')
    program = Program(stock,prefix)
    evidence = audit(program,stock.read_bytes())
    (capture/'original-byte-audit.json').write_text(json.dumps(evidence,indent=2,sort_keys=True)+'\n')
    results = []
    with QemuRAM() as q:
        version = q.version
        for case in case_specs():
            a = execute(case,program,None,capture)
            b = execute(case,program,q,capture)
            for key in ('entry','stop_before','registers','descriptor_hex','expected_descriptor_hex',
                        'pointer_register_a8','before_memory','expected_memory',
                        'actual_memory','expected_writes','accesses','original_instructions_retired'):
                assert a[key] == b[key], (case['name'],key)
            results.append(dict(input=case,interpreter=a,qemu=b,status='pass'))
            print(f'EP0 construction: {len(results)} conditional cases passed',flush=True)
        excluded = reject_excluded(program,q,capture)
    assert all(sha(Path(origins[n]).read_bytes()) == value for n,value in sources.items()), 'source changed during execution'
    counts = dict(construction=sum(c['input']['effect']=='descriptor' for c in results),
                  pointer_only=sum(c['input']['effect']=='pointer' for c in results),
                  mmio_rejections=sum(c['input'].get('reject_mmio',False) for c in results),
                  excluded_multi_descriptor=sum(c['input'].get('stop')==0x10008d48 for c in results))
    assert counts == dict(construction=36,pointer_only=12,mmio_rejections=16,excluded_multi_descriptor=2)
    assert len(results) == 66 and len(excluded) == 18
    report = dict(status='pass',cases=results,counts=counts,excluded_code_controls=excluded,
        source_sha256=sources,source_origins=origins,stock_elf_sha256=STOCK_SHA,qemu_version=version,
        original_byte_audit=evidence,private_literal_redirects=[],supplied_services=[],
        completed_usb_control_transfers=0,completed_native_page_lifecycles=0,
        actual_peripheral_accesses=0,controller_quiescence_established=False,
        omitted_startup_prefix=True,original_entry_executed=False,
        scope='Explicit original IN0 zero/single-packet and ordinary OUT0 construction cuts, plus distinct active pointer passthrough and initialization ADD-only cuts; literal BE descriptor, ordered writes, every mutable RAM byte and independent pointer arithmetic compared in both engines.',
        limits='All logical registers, pointer cells, nonzero-path MPS RAM word and preexisting RAM are supplied. Original ENTRY/control setup, copy/cache helper, SETUP initialization/publication, multi-descriptor path, controller accesses, kick, event wait and completion are excluded. Numeric encoded buffer pointers are never dereferenced; no CPU/DMA mapping or alias is inferred. OUT zero count proves no allocation capacity or completed status packet. The initialization ADD-only cut asserts no HOST_BUSY construction. Mode, cache/publication order, immutable hardware events, success/count/settlement, boot and printing remain unproved.')
    text = json.dumps(report,indent=2,sort_keys=True)+'\n'
    markdown = ('# Original EP0 construction cuts\n\n'+report['scope']+'\n\n'+
        f'{counts["construction"]} descriptor-construction and {counts["pointer_only"]} pointer-only profiles; '
        f'{counts["mmio_rejections"]} pre-MMIO and {counts["excluded_multi_descriptor"]} out-of-profile controls; '
        f'{len(excluded)} excluded PCs. Counts are per engine and establish no USB lifecycle.\n\n'+report['limits']+'\n')
    (capture/'report.json').write_text(text)
    (capture/'report.md').write_text(markdown)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.with_suffix('.json').write_text(text)
    OUT.with_suffix('.md').write_text(markdown)
    print('EP0 construction capture complete: '+str(capture),flush=True)


if __name__ == '__main__':
    main()
