#!/usr/bin/env python3
"""Execute bounded stock callback gates; never run custom code or peripherals.

These are separate RAM fragments, not a page lifecycle or firmware boot. The
band fragment receives explicit ring/buffer fixtures after prepare stops before
hardware setup. Positive controls stop BEFORE CALLX8, not after a fake callback.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace

from hp1020_xtensa_call0 import Program, Machine
from hp1020_stock_stop import StopRAM
from hp1020_qemu_ram import QemuRAM
from hp1020_qemu_pipeline import start
from hp1020_qemu_stock_parser import VECTORS

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'analysis/hardware-boundary/raster-bypass'
WORK, DESC, RAW, TRANSFORMED, BACKING = (0x22700000, 0x22700200,
                                      0x22704000, 0x22708000, 0x22710000)
PREPARE = [(0x10014910,0x10014ae0), (0x10011178,0x100111b4),
           (0x100171b0,0x100171d7), (0x1001b668,0x1001b6b0)]
# Exclude the indirect call itself as well as every custom callback.
BAND = [(0x10013f57,0x10013ff9), (0x10013ffc,0x10014014)]
RELOCATE = [(0x10010dcd,0x10010e80)]
MUTEX, ALLOCATE = 0x100181a4, 0x100131b8
RANGE_HASHES = {
    (0x10014910,0x10014ae0): 'bab3b1d954b7b5d9ae5ef9d38d71e9332884913abecf47d8b6efa9d84e48dd68',
    (0x10011178,0x100111b4): 'b1e4de8d5c53f5643490391fe5f6582a4690453608c3cba9ef923c91840dc033',
    (0x100171b0,0x100171d7): 'a35e075ed7d424019d812cc619101611efc9e3a3172302eac7cd0521406c3c2d',
    (0x1001b668,0x1001b6b0): '028e0472d3e3219fcfed48e69cb2d48c43e49df8458aa068134650f954e48a93',
    (0x10013f57,0x10014014): 'db4c21744a85b8403a84f861ba10209b94ee1703becdac3b8e632340706c843d',
    (0x10010dcd,0x10010e80): '636bbafba3c89881250be8a958d916759e896a9438e59ba0532e7141e656861c',
}
WRAPPER = '''
.text
.align 4
.global band
band:
 entry a1,48
 mov a11,a2
 mov a5,a3
 movi a9,256
 movi a8,0x10013f57
 jx a8
.align 4
.global relocate
relocate:
 entry a1,64
 movi a8,0x10010dcd
 jx a8
'''


def sha(data):
    return hashlib.sha256(data).hexdigest()


class BypassRAM(StopRAM):
    def extension(self,op,args,nxt):
        if op=='call8' and args==(MUTEX,):
            assert self.registers[10:12]==[self.read(0x10006810,4),0xffffffff]
            self.registers[10] = 0  # Supplied uncontended acquisition only.
        elif op=='call8' and args==(ALLOCATE,):
            table = self.read(0x1000647c,4)
            size = sum((self.read(table+i*24+16,2)+3)&~3 for i in range(23))
            assert self.registers[10:12]==[size,1] and size<=4096
            self.registers[10] = BACKING
        else:
            return super().extension(op,args,nxt)
        self.branch_taken = True
        return nxt


def ar(q,index):
    return q.reg(((q.reg(38)*4+index)%32)+1)


def stopped(runner,stops):
    while runner.q.reg(0) not in stops:
        runner.step()
    runner.synchronize(False)
    return runner.q.reg(0)


def rejected(runner,pc):
    runner.q.set_reg(0,pc)
    before = runner.steps
    try:
        runner.step()
    except ValueError as error:
        assert str(error)==f'native tasks left selected code: {pc:#x}'
    else:
        raise AssertionError(f'excluded code executed: {pc:#x}')
    assert runner.steps==before and runner.q.reg(0)==pc
    return hex(pc)


def memory(program,ranges,fill):
    state = BypassRAM(program,ranges[0][0],ranges+VECTORS,[(WORK,0x11000)])
    state.put(WORK,bytes([fill])*0x11000)
    return state


def relocation(q,program,fixture,fill):
    state = memory(program,RELOCATE,fill)
    state.segments += fixture.segments
    table = state.read(0x1000647c,4)
    before = state.bytes_at(table,38*24)
    value_before = state.bytes_at(0x1001ce10,4)
    runner = start(q,state,fixture,fixture.symbols['relocate'],{ALLOCATE})
    stopped(runner,{0x10010e80})
    changed = [i for i in range(38)
               if state.bytes_at(table+i*24,24)!=before[i*24:(i+1)*24]]
    assert changed==list(range(23))
    assert state.read(table+4,4)==BACKING
    assert state.bytes_at(0x1001ce10,4)==value_before==bytes.fromhex('00000001')
    assert runner.services==[ALLOCATE]
    return dict(fill=fill,steps=runner.steps,changed_entries=changed,
                entry_32_unchanged=True,value=state.read(0x1001ce10,4),
                stop_before_remaining_constructor=hex(q.reg(0)),
                host_services=[hex(x) for x in runner.services])


def run_case(q,program,fixture,bpp,resolution,config,bitmap_flag,fill,clear_pointer=False):
    state = memory(program,PREPARE,fill)
    video,callback = state.read(0x10006770,4),state.read(0x100067c4,4)
    state.put(video,bytes([fill])*256)
    state.write(video+0x6c,4,0)  # Explicit idle precondition, not a boot result.
    for offset,size,value in ((20,2,resolution),(34,2,bpp),
                              (54,2,bitmap_flag),(132,4,9600)):
        state.write(WORK+offset,size,value)
    state.write(callback,4,0x10015648)  # Deliberately stale valid callback.
    if config is not None:
        state.write(0x1001ce10,4,config)
    runner = start(q,state,SimpleNamespace(path=None,execute_ranges=[]),0x10014910,{MUTEX})
    q.set_reg(11,WORK)
    stopped(runner,{0x10014ae0})
    assert runner.services==[MUTEX]
    assert 0x100111aa in runner.visited  # Original type-2 getter dereference.
    gate = int(config==0 and bitmap_flag==0)
    ptr,window,scale,out_bpp,padding = 0x10015648,1200,1,bpp,0
    if gate and bpp==1:
        if resolution==300:
            ptr = 0
        elif resolution==600:
            ptr,window,out_bpp,padding = 0x100159b4,2400,2,2
        elif resolution==1200:
            ptr,window,scale,out_bpp,padding = 0x10015814,2400,2,4,4
    elif gate and bpp==2 and resolution==600:
        padding = 2
    fields = {hex(o):state.read(video+o,4) for o in (0xb8,0xbc,0xc0,0xc4,0xc8,0xcc,0xf4)}
    assert list(fields.values())==[1200,window,gate,scale,out_bpp,4,padding],fields
    assert state.read(callback,4)==ptr
    prepare = dict(steps=runner.steps,fields=fields,callback=hex(ptr),
                   host_services=[hex(x) for x in runner.services])
    rejected(runner,0x10014ae0)

    # A separately entered fragment, with an explicitly supplied non-final band.
    state.code_ranges = BAND+VECTORS
    state.segments += fixture.segments
    for offset,value in ((0,RAW),(0x10,TRANSFORMED),(0xdc,0),(0xe0,2),(0xd4,1024)):
        state.write(video+offset,4,value)
    state.put(DESC,bytes(16))
    state.write(DESC+8,4,8)
    if clear_pointer:
        ptr = 0
        state.write(callback,4,0)
    raw_before = state.bytes_at(RAW-4800,12000)
    output_before = state.bytes_at(TRANSFORMED,8192)
    runner = start(q,state,fixture,fixture.symbols['band'],set())
    q.set_reg(11,video)
    q.set_reg(12,DESC)
    stop = stopped(runner,{0x10013ff9,0x10014014})
    expected_call = bool(gate and ptr)
    assert (stop==0x10013ff9)==expected_call
    band = dict(steps=runner.steps,stop=hex(stop),host_services=[],
                outcome='custom_call_boundary' if expected_call else 'raw_buffer_selected')
    if expected_call:
        arguments = [ar(q,i) for i in range(10,14)]
        assert arguments==[RAW-padding*1200,TRANSFORMED,8,1200]
        assert ar(q,8)==ptr
        band.update(callback=hex(ptr),arguments=arguments,callback_executed=False)
    else:
        assert ar(q,12)==RAW
        assert 0x10014012 in runner.visited
        band.update(selected_pointer=hex(ar(q,12)))
    assert state.bytes_at(RAW-4800,12000)==raw_before
    assert state.bytes_at(TRANSFORMED,8192)==output_before
    assert runner.services==[]
    exclusions = [rejected(runner,pc) for pc in (0x10013f4c,0x10013ff9,0x10015648,0x10014014)]
    return dict(bpp=bpp,resolution=resolution,config_source='file_backed_stock' if config is None else 'explicit_mutation',
                config=state.read(0x1001ce10,4),bitmap_flag=bitmap_flag,fill=fill,
                clear_pointer_after_prepare=clear_pointer,prepare=prepare,band=band,
                raw_and_output_buffers_unchanged=True,rejected_pc_controls=exclusions)


def main():
    prefix = os.environ.get('XTENSA_PREFIX','/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf')
    program = Program(ROOT/'analysis/sihp1020.elf',prefix)
    original = Machine(program)
    audited = []
    for (begin,end),digest in RANGE_HASHES.items():
        data,offset = original.span(begin,end-begin,execute=True)
        raw = bytes(data[offset:offset+end-begin])
        assert sha(raw)==digest
        audited.append(dict(begin=hex(begin),end=hex(end),sha256=digest,bytes=raw.hex()))
    table = original.read(0x1000647c,4)
    record = table+32*24
    words = [original.read(record+i*4,4) for i in range(6)]
    assert table==0x1001ce14 and record==0x1001d114
    assert words==[32,0x1001ce10,2,0,0x40000,2]
    assert original.read(words[1],4)==1
    # Static limits, verified against original instructions rather than relying
    # on decompilation: flags != 1 bypass the writer's write-once condition;
    # the type-2 switch arm dereferences and writes caller backing. Work +0x36
    # separately guards the four BIH stores, so it is not a callback-only knob.
    limit_instructions = {
        0x10010fd3: ('movi.n',(10,1),'c0a1'),
        0x10010fe0: ('l32i.n',(8,7,20),'8875'),
        0x10010fe4: ('bnei',(8,1,0x10011031),'698149'),
        0x10011070: ('l32i.n',(8,2,4),'8821'),
        0x10011072: ('l32i.n',(9,7,4),'8971'),
        0x10011074: ('l32i.n',(8,8,0),'8880'),
        0x10011076: ('s32i.n',(8,9,0),'9890'),
        0x1000e64c: ('l16ui',(8,7,54),'28711b'),
        0x1000e64f: ('bnez.n',(8,0x1000e66a),'cd87'),
        0x1000e656: ('s32i',(8,7,132),'287621'),
        0x1000e65b: ('s32i',(8,7,136),'287622'),
        0x1000e661: ('s32i',(8,7,140),'287623'),
        0x1000e667: ('s8i',(8,7,144),'287490'),
    }
    for pc,(op,args,raw) in limit_instructions.items():
        assert program.instruction(pc)==(op,args,bytes.fromhex(raw))
        data,offset=original.span(pc,len(bytes.fromhex(raw)),execute=True)
        assert bytes(data[offset:offset+len(bytes.fromhex(raw))])==bytes.fromhex(raw)
    # Read-only audit of excluded hardware code. These are original byte facts,
    # not an MMIO simulation or executable writes added to either allowed range.
    pointer_flow = {
        0x1001521f: ('mov.n',(6,1),'d610'),
        0x10015261: ('l32i',(8,11,84),'28b215'),
        0x10015264: ('s32i.n',(8,1,0),'9810'),
        0x100153cf: ('l32r',(9,0x100067f4),'19c509'),
        0x100153d2: ('l32i.n',(8,6,0),'8860'),
        0x100153da: ('s32i.n',(8,9,0),'9890'),
        0x1001424a: ('l32i',(2,7,224),'227238'),
        0x10014258: ('addx4',(2,2,7),'07220a'),
        0x1001425b: ('l32i.n',(8,2,0),'8820'),
        0x1001428a: ('l32r',(5,0x100067e4),'15c956'),
        0x10014293: ('s32i.n',(8,5,0),'9850'),
        0x1001401f: ('l32r',(8,0x100067cc),'18c9eb'),
        0x1001402b: ('s32i.n',(12,8,0),'9c80'),
        0x100140a1: ('l32r',(8,0x100067cc),'18c9ca'),
        0x100140ac: ('s32i.n',(12,8,0),'9c80'),
    }
    for pc,(op,args,raw) in pointer_flow.items():
        assert program.instruction(pc)==(op,args,bytes.fromhex(raw))
        data,offset=original.span(pc,len(bytes.fromhex(raw)),execute=True)
        assert bytes(data[offset:offset+len(bytes.fromhex(raw))])==bytes.fromhex(raw)
    pointer_literals = {cell:original.read(cell,4) for cell in (0x100067f4,0x100067e4,0x100067cc)}
    assert list(pointer_literals.values())==[0xb2040004,0xb2080004,0xb1000008]
    cases=[]
    with tempfile.TemporaryDirectory(prefix='hp1020-raster-bypass-',dir='/tmp') as folder:
        path=Path(folder)
        (path/'wrapper.S').write_text(WRAPPER)
        subprocess.run([prefix+'-as','--text-section-literals','wrapper.S','-o','wrapper.o'],cwd=path,check=True)
        subprocess.run([prefix+'-ld','-Ttext=0x20000000','-e','band','wrapper.o','-o','wrapper.elf'],cwd=path,check=True)
        fixture=Program(path/'wrapper.elf',prefix)
        fixture_bytes=fixture.path.read_bytes()
        with QemuRAM() as q:
            relocations=[relocation(q,program,fixture,fill) for fill in (0,0xcc)]
            for bpp,resolution in ((1,300),(1,600),(1,1200),(2,600),(4,600)):
                for config in (None,0):
                    for bitmap_flag in (0,1):
                        for fill in (0,0xcc):
                            cases.append(run_case(q,program,fixture,bpp,resolution,config,bitmap_flag,fill))
                print(f'raster bypass: BPP{bpp}/{resolution} gate controls pass',flush=True)
            for fill in (0,0xcc):
                cases.append(run_case(q,program,fixture,2,600,0,0,fill,True))
            qemu_version=q.version
    raw_cases=[c for c in cases if c['band']['outcome']=='raw_buffer_selected']
    custom_cases=[c for c in cases if c['band']['outcome']=='custom_call_boundary']
    assert (len(cases),len(raw_cases),len(custom_cases))==(42,34,8)
    sources = ('validate-hp1020-raster-bypass.py','hp1020_xtensa_call0.py','hp1020_xtensa_stock.py',
               'hp1020_stock_stop.py','hp1020_qemu_ram.py','hp1020_qemu_pipeline.py',
               'hp1020_qemu_multitask.py','hp1020_qemu_stock_parser.py','hp1020_xtensa_properties.py')
    findings = [
        'The stock ELF stores u32 1 at the backing pointer for datastore entry 32 (type 2). The original getter reads it directly; no fixture overrides that getter.',
        'With that file-backed value, the original prepare prefix sets video +0xc0=0 and +0xf4=0. The separately entered original band gate chooses its raw slot pointer despite a deliberately stale custom callback pointer.',
        'Two constructor-fragment cases execute the dynamic-backing relocation loops. They change entries 0 through 22 only, preserving entry 32 and its value 1. The rest of initialization is excluded; this is not proof of the live boot value.',
        '42 prepare/band cases include 34 raw-buffer selections and eight stops before the custom call. Mutating entry 32 to zero enables callbacks only when work +0x36 is also zero; BPP1/300 clears the pointer, and a separately cleared pointer also suppresses the call.',
        'Unsupported BPP4/600 with both gates enabled retains the stale callback. This is a conditional finding, not support for that format. Stock configuration and nonzero work +0x36 suppress it in the tested fragments.',
        'A separate read-only byte audit distinguishes the raster payload pointer sent to channel A from the video slot pointer sent to channel B. The bypass-selected slot pointer is then written toward the video block in either lane branch. Skipping the custom callback does not provide or prove the hardware transformation between those buffers.',
        'No custom instruction, callback invocation, peripheral access, DMA or physical image processing executes. These fragment results are not completed page lifecycles or evidence of printable output.'
    ]
    limits = [
        'Prepare enters with an explicitly idle video context and supplied successful mutex acquisition, then stops before hardware/buffer setup.',
        'The band fragment is entered after the omitted peripheral-read prefix. Ring indices, descriptor units, non-final flag and both buffer addresses are synthetic; no producer filled the raw buffer.',
        'Constructor allocation returns synthetic RAM. Earlier RTOS setup, later default/persistence helpers and all remaining boot activity are excluded.',
        'The generic datastore writer can update type-2 backing; file value 1 is not a guarantee that every runtime path preserves it. A complete boot/writer audit or targeted stock observation remains needed.',
        'Work +0x36 also participates in JobMgr BIH-field handling. Changing a host bitmap item is not established as a callback-only switch.',
        'Usable image format, raw buffer production, output quality, engine timing, physical printing and recovery remain unproven.'
    ]
    report=dict(status='pass',scope='bounded RAM fragments; no completed page or boot claim',
                total_cases=len(cases),raw_buffer_selections=len(raw_cases),
                custom_call_boundary_stops=len(custom_cases),custom_callbacks_executed=0,
                completed_lifecycles=0,cases=cases,relocation_cases=relocations,
                stock_entry=dict(index=32,table=hex(table),record=hex(record),words=words,value=1),
                static_limit_instruction_audit={hex(pc):dict(op=op,args=args,bytes=raw)
                    for pc,(op,args,raw) in limit_instructions.items()},
                excluded_pointer_flow_audit={hex(pc):dict(op=op,args=args,bytes=raw)
                    for pc,(op,args,raw) in pointer_flow.items()},
                excluded_pointer_literals={hex(k):hex(v) for k,v in pointer_literals.items()},
                audited_stock_ranges=audited,fixture_source=WRAPPER,fixture_source_sha256=sha(WRAPPER.encode()),
                fixture_elf_sha256=sha(fixture_bytes),fixture_elf_bytes=fixture_bytes.hex(),
                source_sha256={name:sha((ROOT/'scripts'/name).read_bytes()) for name in sources},
                elf_sha256=sha(program.path.read_bytes()),qemu_version=qemu_version,findings=findings,limits=limits)
    OUT.with_suffix('.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    OUT.with_suffix('.md').write_text('# Stock raster callback bypass\n\n'
        +'\n'.join('- '+x for x in findings)+'\n\n## Limits and next evidence\n\n'
        +'\n'.join('- '+x for x in limits)+'\n')
    print(f'Raster bypass: {len(raw_cases)} raw selections, {len(custom_cases)} excluded custom-call boundaries; no page lifecycles')


if __name__=='__main__':
    main()
