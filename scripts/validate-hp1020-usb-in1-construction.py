#!/usr/bin/env python3
"""Guarded original bulk-IN1 arithmetic, never descriptor publication or USB.

Enter after the original ENTRY and stop before the publication tail. The normal
instruction bytes and all literal words stay original. Only CPU registers and
mutable RAM are supplied. No cache, queue, interrupt, controller or engine call
is executed. Neutral capture plumbing follows the existing EP0 construction
probe; the IN1 byte/write oracle is independently transcribed from original
instructions before execution. Zero-length arithmetic does not prove stock ZLPs.
"""
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
from types import SimpleNamespace

DEFAULT_ROOT = Path(__file__).resolve().parents[1] if Path(__file__).parent.name == 'scripts' else Path.cwd()
ROOT = Path(os.environ.get('HP1020_ROOT', str(DEFAULT_ROOT))).resolve()
OUT = ROOT/'analysis/usb-path/in1-construction'
sys.path.insert(0, str(ROOT/'scripts'))
from hp1020_xtensa_call0 import Program, Machine, STOP, STACK, STACK_SIZE
from hp1020_xtensa_properties import properties, section_bytes
from hp1020_stock_stop import StopRAM
from hp1020_qemu_multitask import NativeTasks
from hp1020_qemu_stock_parser import guard_memory
from hp1020_qemu_ram import QemuRAM, STACK_TOP

STOCK_SHA = '2111560068db47ceca21fa550db4c7c34f5595b5a5d137ae4a19631e40e3601d'
ENTRY, LIMIT = 0x1000899f, 0x10008b41
CODE = [(ENTRY,LIMIT)]
CODE_SHA = {(ENTRY,LIMIT): 'af1c30e9998c5abe000121111bebe7e4efc31d1543d361d5996056e0f47d8a34'}
ARENA, ARENA_SIZE = 0x22a00000, 0x1000
DESCRIPTOR, RECORD = ARENA+0x100, ARENA+0x300
DESC_CELL, CAP_CELL = 0x1001bc5c, 0x10021590
INITIAL_SP = STACK_TOP-0x100
EMPTY_FIXTURE = SimpleNamespace(path=None, execute_ranges=[])
LITERALS = {0x10005e50:CAP_CELL,0x10005e7c:DESC_CELL,
            0x10005e34:0x80000000,0x10005e80:0x08000000}
EXCLUDED = (0x1000899c, LIMIT, 0x10008b54, 0x10008b63, 0x10008b72,
            0x10008b78, 0x10008bac, 0x10008bcc, 0x100173c8, 0x10008208)
STORE_PCS = {
    'small_buffer':(0x10008a6b,0x10008a71,0x10008a77,0x10008a7a),
    'small_next':(0x10008a83,0x10008a86,0x10008a89,0x10008a8c),
    'small_status':(0x10008aa7,0x10008ab6,0x10008ac5,0x10008ad4),
    'capped_buffer':(0x100089c6,0x100089cc,0x100089d2,0x100089d5),
    'capped_status':(0x100089f0,0x100089ff,0x10008a0e,0x10008a1d),
    'capped_next':(0x10008a2b,0x10008a31,0x10008a37,0x10008a3a),
    'last_status':(0x10008b11,0x10008b20,0x10008b2f,0x10008b3e),
}

def sha(data):
    return hashlib.sha256(data).hexdigest()


def access(pc, kind, address, size, value):
    return dict(pc=hex(pc), kind=kind, address=hex(address), size=size, value=hex(value))


def patterned(seed, address, size):
    # Nonuniform/asymmetric guard and payload canaries, never all-zero structs.
    return bytes((seed + (address >> 8) + i*17 + (i >> 4)*3) & 255 for i in range(size))


def case_specs():
    for seed in (0x31,0xcc):
        for pointer in (0x01234567,0xb3000400):
            for length in (0,1,63,64,65,128,129):
                yield dict(name=f'in1-n{length}-q64-p{pointer:08x}-s{seed:02x}',
                    seed=seed,length=length,pointer=pointer,cap=64,effect='descriptor')
        yield dict(name=f'in1-pointer-wrap-s{seed:02x}',seed=seed,length=65,
            pointer=0xfffffffc,cap=64,effect='descriptor')
        for length in (511,512,513):
            yield dict(name=f'in1-n{length}-q512-s{seed:02x}',seed=seed,
                length=length,pointer=0x91b2c3d0,cap=512,effect='descriptor')
        for mode,stop in (('record',0x100089a2),('descriptor',0x10008a6b)):
            yield dict(name=f'in1-mmio-{mode}-s{seed:02x}',seed=seed,length=1,
                pointer=0x01234567,cap=64,effect='none',reject_mmio=mode,stop=stop)


class ConstructionRAM(StopRAM):
    def __init__(self,program,case):
        self.recording,self.events,self.pc_trace = False,[],[]
        super().__init__(program,ENTRY,CODE.copy(),[(ARENA,ARENA_SIZE)])
        self.stop,self.case = case.get('stop',LIMIT),case
        for begin,end in self.write_ranges:
            self.put(begin,patterned(case['seed'],begin,end-begin))
        self.write(DESC_CELL,4,0xb3000034 if case.get('reject_mmio')=='descriptor' else DESCRIPTOR)
        self.write(CAP_CELL,4,case['cap'])
        self.write(RECORD,4,case['pointer'])
        self.write(RECORD+4,4,0x5973bda1)
        self.write(RECORD+8,4,case['length'])
        self.write(RECORD+12,4,0x2e4c6a89)
        self.registers = [(0x13579bdf+i*0x10203+case['seed']*0x01010101)&0xffffffff for i in range(16)]
        self.registers[0],self.registers[1] = STOP,INITIAL_SP
        self.registers[2] = 0xb3000000 if case.get('reject_mmio')=='record' else RECORD
        self.supplied_registers = self.registers.copy()

    def read(self,address,size):
        value = super().read(address,size)
        if self.recording:
            self.events.append(access(self.pc,'read',address,size,value))
        return value

    def write(self,address,size,value):
        self.span(address,size)
        super().write(address,size,value)
        if self.recording:
            self.events.append(access(self.pc,'write',address,size,value & ((1 << (8*size))-1)))

    def after_instruction(self,pc,nxt):
        self.pc_trace.append(pc)
        return super().after_instruction(pc,nxt)


def memory_snapshot(state):
    # Include the entire original mutable RAM, stack and guarded synthetic arena.
    # These slices require no stack stores, so even the stack has an exact oracle.
    return {(a,b):state.bytes_at(a,b-a) for a,b in state.write_ranges}


def manifest(memory):
    return [dict(begin=hex(a),end=hex(b),bytes=len(data),sha256=sha(data))
            for (a,b),data in sorted(memory.items())]


def expected_memory(state,before):
    expected = {span:bytearray(data) for span,data in before.items()}
    writes = []
    def replace(address,data):
        found = [(a,b) for a,b in expected if a <= address and address+len(data) <= b]
        assert len(found)==1
        a,b=found[0]
        expected[a,b][address-a:address-a+len(data)] = data
    def word(pc,address,value):
        replace(address,struct.pack('>I',value))
        writes.append(access(pc,'write',address,4,value))
    def bytes4(key,offset,value):
        data=struct.pack('>I',value)
        replace(DESCRIPTOR+offset,data)
        for pc,index in zip(STORE_PCS[key],range(4)):
            writes.append(access(pc,'write',DESCRIPTOR+offset+index,1,data[index]))
    case=state.case
    if case['effect']=='descriptor':
        n,q,p=case['length'],case['cap'],case['pointer']
        # This literal oracle is independent of both execution engines. Neither
        # descriptor reserved word nor software original/done sentinels change.
        if n<=q:
            bytes4('small_buffer',8,(p+0x80000000)&0xffffffff)
            bytes4('small_next',12,0)
            bytes4('small_status',0,0x08000000|n)
            word(0x10008ad7,RECORD+8,0)
        else:
            bytes4('capped_buffer',8,(p+0x80000000)&0xffffffff)
            word(0x100089e0,RECORD,(p+q)&0xffffffff)
            bytes4('capped_status',0,q)
            bytes4('capped_next',12,DESCRIPTOR+16)
            word(0x10008a48,RECORD+8,n-q)
            bytes4('last_status',0,0x08000000|q)
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
            cap_cell=hex(CAP_CELL),cap=case['cap'],software_record=hex(RECORD),
            source_numeric_only=hex(case['pointer']),source_is_not_dereferenced=True))
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
                retired_pc=state.pc
                runner.step()
                state.pc_trace.append(retired_pc)
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
    def span_bytes(memory,address,size):
        matches=[(a,b) for a,b in memory if a<=address and address+size<=b]
        assert len(matches)==1
        a,b=matches[0]
        return memory[a,b][address-a:address-a+size]
    result = dict(status='captured_unchecked',engine=engine,entry=hex(ENTRY),
        stop_before=hex(state.stop),failure=failure,registers=[hex(x) for x in state.registers],
        descriptor_hex=state.bytes_at(DESCRIPTOR,16).hex(),
        expected_descriptor_hex=span_bytes(expected,DESCRIPTOR,16).hex(),
        record_hex=state.bytes_at(RECORD,16).hex(),
        expected_record_hex=span_bytes(expected,RECORD,16).hex(),
        before_memory=manifest(before),expected_memory=manifest(expected),actual_memory=manifest(actual),
        expected_writes=writes,accesses=state.events,
        original_instructions_retired=[hex(pc) for pc in state.pc_trace],
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
    # Exact read admission: the numeric source is never touched; only original
    # literal words, supplied cells, record and first descriptor may be read.
    read_spans=[(p,p+4) for p in LITERALS]+[(DESC_CELL,DESC_CELL+4),
        (CAP_CELL,CAP_CELL+4),(RECORD,RECORD+16),(DESCRIPTOR,DESCRIPTOR+16)]
    assert all(any(a<=int(e['address'],16) and int(e['address'],16)+e['size']<=b
        for a,b in read_spans) for e in state.events if e['kind']=='read')
    assert len(state.pc_trace)==len(set(state.pc_trace)), 'unexpected loop or second descriptor'
    assert not set(state.pc_trace)&set(EXCLUDED)
    assert state.registers[0:2]==state.supplied_registers[0:2], 'unexpected call or stack use'
    for begin,end in state.code_ranges:
        raw = state.bytes_at(begin,end-begin)
        assert sha(raw) == CODE_SHA[begin,end]
        if q is not None:
            assert q.read(begin,end-begin) == raw
    result.update(status='pass',all_mutable_and_guard_ram_equal=True,
        literal_descriptor_checked=case['effect']=='descriptor',ordered_write_trace_equal=True,
        source_never_dereferenced=True,original_code_unchanged=True,
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
    assert sha(blob)==STOCK_SHA
    sections,_=properties(blob)
    raw=section_bytes(blob,sections,ENTRY,LIMIT-ENTRY)
    assert sha(raw)==CODE_SHA[ENTRY,LIMIT]
    allowed={'l32i','l8ui','s32i','s8i','l32r','movi','mov','add','addi','sub',
             'or','slli','extui','memw','blt','bge','beqz','bnei','j'}
    pc,instructions=ENTRY,{}
    while pc<LIMIT:
        op,args,encoded=program.instruction(pc)
        assert op.removesuffix('.n') in allowed,(hex(pc),op)
        assert pc+len(encoded)<=LIMIT
        assert encoded==section_bytes(blob,sections,pc,len(encoded))
        instructions[hex(pc)]=dict(op=op,args=args,bytes=encoded.hex())
        pc+=len(encoded)
    assert pc==LIMIT
    original=Machine(program)
    for pc,value in LITERALS.items():
        assert original.read(pc,4)==value
    assert original.read(DESC_CELL,4)==0x900216d0
    return dict(ranges=[dict(begin=hex(ENTRY),end=hex(LIMIT),bytes=raw.hex(),sha256=sha(raw))],
        instructions=instructions,literals={hex(k):hex(v) for k,v in LITERALS.items()},
        original_descriptor_pointer='0x900216d0',entry_after_original_ENTRY=True)


def reject_excluded(program,q,capture):
    case = dict(name='excluded-code',seed=0xcc,length=0,pointer=0x01234567,cap=64,effect='none')
    state = ConstructionRAM(program,case)
    # Original entry, queue/cache, publication and interrupt paths are all
    # outside the sole construction-only admission range.
    state.code_ranges = CODE.copy()
    before = memory_snapshot(state)
    q.load(program.path)
    runner = NativeTasks(q,state,EMPTY_FIXTURE,state.code_ranges,(),instruction_budget=32)
    runner.synchronize(True)
    q.reset_cpu(ENTRY)
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
    capture = Path(tempfile.mkdtemp(prefix='hp1020-in1-construction-',dir='/tmp'))
    print('IN1 construction captures: '+str(capture),flush=True)
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
    executables = {}
    for name in ('nm','objdump'):
        path = Path(prefix+'-'+name).resolve()
        executables[name] = dict(path=str(path),sha256=sha(path.read_bytes()),
            version=subprocess.check_output([str(path),'--version'],text=True).splitlines()[0])
    (capture/'tool-identities.json').write_text(json.dumps(executables,indent=2,sort_keys=True)+'\n')
    program = Program(stock,prefix)
    evidence = audit(program,stock.read_bytes())
    (capture/'original-byte-audit.json').write_text(json.dumps(evidence,indent=2,sort_keys=True)+'\n')
    results = []
    with QemuRAM() as q:
        version = q.version
        qemu_identity = dict(path=q.binary,sha256=sha(Path(q.binary).read_bytes()))
        for case in case_specs():
            a = execute(case,program,None,capture)
            b = execute(case,program,q,capture)
            for key in ('entry','stop_before','registers','descriptor_hex','expected_descriptor_hex',
                        'record_hex','expected_record_hex','before_memory','expected_memory',
                        'actual_memory','expected_writes','accesses','original_instructions_retired'):
                assert a[key] == b[key], (case['name'],key)
            results.append(dict(input=case,interpreter=a,qemu=b,status='pass'))
            print(f'IN1 construction: {len(results)} conditional cases passed',flush=True)
        excluded = reject_excluded(program,q,capture)
    assert all(sha(Path(row['path']).read_bytes())==row['sha256'] for row in executables.values()), 'binutils changed during execution'
    assert sha(Path(qemu_identity['path']).read_bytes())==qemu_identity['sha256'], 'QEMU changed during execution'
    assert all(sha(Path(origins[n]).read_bytes()) == value for n,value in sources.items()), 'source changed during execution'
    counts = dict(construction=sum(c['input']['effect']=='descriptor' for c in results),
                  mmio_rejections=sum(bool(c['input'].get('reject_mmio')) for c in results))
    assert counts==dict(construction=36,mmio_rejections=4)
    assert len(results)==40 and len(excluded)==10
    report = dict(status='pass',cases=results,counts=counts,excluded_code_controls=excluded,
        source_sha256=sources,source_origins=origins,stock_elf_sha256=STOCK_SHA,
        qemu_version=version,qemu_identity=qemu_identity,binutils_identities=executables,original_byte_audit=evidence,
        private_literal_redirects=[],supplied_services=[],completed_bulk_in_transfers=0,
        actual_peripheral_accesses=0,controller_quiescence_established=False,
        original_entry_executed=False,
        scope='Original IN1 arithmetic cut: independent BE descriptor and record oracle, exact ordered writes/reads/PCs, every mutable RAM byte and guards agree in the interpreter and QEMU.',
        limits='Registers, pointer cells, positive cap and guarded RAM are supplied. Original ENTRY, queue, source/cache publication, controller accesses, interrupt completion, terminal external memory access, FIFO settlement and host receipt are excluded. Numeric source aliases are never dereferenced. Zero-length cases prove only construction arithmetic; stock queue selection ignores zero remaining. This is no completed USB, document or physical print lifecycle.')
    text = json.dumps(report,indent=2,sort_keys=True)+'\n'
    markdown = ('# Original bulk-IN1 construction cut\n\n'+report['scope']+'\n\n'+
        f'{counts["construction"]} construction profiles; {counts["mmio_rejections"]} access-gate controls; '
        f'{len(excluded)} excluded PCs. Counts are per engine and establish no USB lifecycle.\n\n'+report['limits']+'\n')
    (capture/'report.json').write_text(text)
    (capture/'report.md').write_text(markdown)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.with_suffix('.json').write_text(text)
    OUT.with_suffix('.md').write_text(markdown)
    print('IN1 construction capture complete: '+str(capture),flush=True)


if __name__ == '__main__':
    main()
