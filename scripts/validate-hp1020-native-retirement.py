#!/usr/bin/env python3
"""Check a native entry into the original retirement tail, with a next-path gate.

Only this fixture supplies node consumption. Original reference decrement, event
set, CPU INTCLEAR helper and register-window return execute in QEMU. No peripheral
path is allowed; changing the pending cursor must stop before its excluded read.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from hp1020_xtensa_call0 import Program
from hp1020_stock_stop import StopRAM
from hp1020_stock_notifications import invoke
from hp1020_qemu_pipeline import start
from hp1020_qemu_ram import QemuRAM,RETURN
from hp1020_qemu_scheduler import RANGES
from hp1020_qemu_scheduled_status import READY_CODE
from hp1020_qemu_retire import RETIRE_CODE,retirement_source

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'analysis/open-firmware-model/stock-execution'
WORK,NODES = 0x22700000,0x22700100


def run_retirement(q,program,count,refs,fill,mutate=False):
    state = StopRAM(program,0,RETIRE_CODE+RANGES+READY_CODE,[(WORK,4096)])
    state.put(WORK,bytes([fill])*4096)
    video = state.read(0x10006770,4)
    event = state.read(0x100062dc,4)
    state.put(video,bytes([fill])*256)
    for cell in (0x10006a9c,0x10005d80,0x10006ac0):
        state.write(state.read(cell,4),4,0)
    invoke(state,0x10017554,qemu=q)
    assert invoke(state,0x10017ca0,[event,0],q)==19
    # Original public object creation rejects current==0/system==0. Supply an
    # ordinary, nonwaiting constructor caller after RTOS init clears current.
    state.put(WORK+0xf00,bytes(256))
    state.write(state.read(0x10006a9c,4),4,WORK+0xf00)
    assert invoke(state,0x10017ca0,[event,0],q)==0
    state.write(WORK+80,4,NODES if count else 0)
    nodes = []
    for i in range(count):
        node = NODES+i*128
        payload = node+16
        state.write(node,4,node+128 if i+1<count else 0)
        state.write(node+12,4,payload)
        state.write(payload+78,2,refs)
        nodes.append((node,payload))
    before = state.bytes_at(WORK,4096)
    before_video = state.bytes_at(video,256)
    source = f'''.text
.align 4
.global boot
boot:
 entry a1,64
 movi a8,0
 wsr.intenable a8
 movi a10,{WORK:#x}
 call8 retire_work
 mov a2,a10
 retw
'''+retirement_source(video)
    with tempfile.TemporaryDirectory(prefix='hp1020-native-retirement-') as temp:
        root = Path(temp)
        (root/'retirement.S').write_text(source)
        subprocess.run([program.prefix+'-as','--text-section-literals','retirement.S','-o','retirement.o'],cwd=root,check=True)
        subprocess.run([program.prefix+'-ld','-Ttext=0x20000000','-e','boot','retirement.o','-o','retirement.elf'],cwd=root,check=True)
        fixture = Program(root/'retirement.elf',program.prefix)
        state.segments += fixture.segments
        runner = start(q,state,fixture,fixture.symbols['boot'],())
        event_calls,clears,decrements = [],[],[]
        injected = False
        stopped = None
        while q.reg(0)!=RETURN:
            pc = q.reg(0)
            ar = lambda i:q.reg(((q.reg(38)*4+i)%32)+1)
            if mutate and not injected and pc==0x10014319:
                q.put(video+156,NODES.to_bytes(4,'big'))
                injected = True
            if pc==0x10017dac:
                event_calls.append([ar(i) for i in (10,11,12)])
            if pc==0x100171eb:
                clears.append(ar(3))
            if pc==0x10014330:
                decrements.append((ar(9),ar(8)&0xffff))
            try:
                runner.step()
            except ValueError as error:
                if not mutate:
                    raise
                assert pc==0x1001434b
                assert str(error)=='native tasks left selected code: 0x1001434b'
                stopped = str(error)
                break
        assert not any(0x1001434b<=pc<0x100143a5 for pc in runner.visited)
        assert runner.services==[]
        runner.synchronize(False)
        retired = 1 if mutate else count
        assert decrements==[(payload,(refs-1)&0xffff) for _,payload in nodes[:retired]]
        assert event_calls==[[event,8,0]]*retired
        assert state.read(event+8,4)==(8 if count else 0)
        expected = bytearray(before)
        for _,payload in nodes[:retired]:
            offset = payload+78-WORK
            expected[offset:offset+2] = ((refs-1)&0xffff).to_bytes(2,'big')
        assert state.bytes_at(WORK,4096)==expected,'retirement changed unrelated work/node bytes'
        if count:
            assert state.bytes_at(video+164,20)==bytes(20)
            assert state.read(video+248,4)==1
            changed = {156,157,158,159,*range(164,184),*range(248,252)}
            assert all(state.read(video+i,1)==before_video[i] for i in range(256) if i not in changed)
        else:
            assert state.bytes_at(video,256)==before_video
        if mutate:
            assert injected and stopped and state.read(video+156,4)==NODES
            assert clears==[] and 0x100143a5 not in runner.visited
        else:
            assert q.reg(38)==0 and q.reg(39)==1 and q.reg(11)==0
            assert clears==[1<<20]*count
            if count:
                assert state.read(video+156,4)==0
            assert stopped is None
        return dict(status='pass',nodes=count,initial_refs=refs,fill=fill,
            outcome='blocked_next_path' if mutate else 'returned',
            supplied_consumption=retired,event_calls=event_calls,intclear_values=clears,
            decrements=decrements,stop=stopped,instructions=runner.steps,host_services=[],
            fixture_source_sha256=hashlib.sha256(source.encode()).hexdigest(),
            fixture_elf_sha256=hashlib.sha256(fixture.path.read_bytes()).hexdigest())


def main():
    program = Program(ROOT/'analysis/sihp1020.elf',os.environ.get('XTENSA_PREFIX','/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf'))
    # Property-aligned original bytes, including the excluded branch destination.
    for pc,op,args,raw in (
        (0x10014329,'l16ui',(8,9,78),'289127'),
        (0x10014330,'s16i',(8,9,78),'289527'),
        (0x10014333,'s32i.n',(5,7,0),'9570'),
        (0x10014338,'call8',(0x10017dac,),'580e9c'),
        (0x10014348,'beqz',(8,0x100143a5),'648059'),
        (0x1001434b,'l32i.n',(8,8,0),'8880'),
        (0x100171eb,'wsr.intclear',(3,),'03e331')):
        assert program.instruction(pc)==(op,args,bytes.fromhex(raw))
    cases = []
    with QemuRAM() as q:
        for fill in (0,0xcc):
            cases.append(run_retirement(q,program,0,1,fill))
            for count in (1,5,6,13):
                for refs in (1,2,65535):
                    cases.append(run_retirement(q,program,count,refs,fill))
            cases.append(run_retirement(q,program,1,1,fill,mutate=True))
    assert len(cases)==28
    report = dict(status='pass',total_cases=len(cases),cases=cases,
        elf_sha256=hashlib.sha256(program.path.read_bytes()).hexdigest(),
        source_sha256={name:hashlib.sha256((ROOT/'scripts'/name).read_bytes()).hexdigest() for name in
            ('validate-hp1020-native-retirement.py','hp1020_qemu_retire.py','hp1020_qemu_pipeline.py',
             'hp1020_qemu_multitask.py','hp1020_qemu_scheduled_status.py','hp1020_qemu_ram.py')},
        findings=[
            'The native wrapper enters the original RAM retirement tail once per linked node, supplies completion flag 1 and a zero pending cursor, and executes original reference decrement, slot clearing, event-set and standard CPU INTCLEAR code before returning through a valid register window.',
            'Empty, one-, five-, six- and thirteen-node fixtures preserve every unrelated work/node byte. References 1, 2 and 65535 each decrease by one; event bit 8 is set through the original primitive. Each completed entry writes bit 20 to INTCLEAR. No runtime host service is used.',
            'Both RAM fills and both nonzero-pending-cursor mutations are checked. A mutated cursor stops at the excluded instruction 0x1001434b before it executes, with no next-transfer or MMIO instruction visited.'
        ],
        limits='Node consumption, no pending DMA and successful band completion are explicit fixture inputs. Original event creation rejects the initial null-caller/ordinary-system fixture with result 19; a separate nonwaiting constructor caller is then supplied. The hardware IRQ prefix, raster instructions, DMA, engine/PrintMgr tasks, automatic interrupt delivery and physical printing do not execute. The standalone event has no waiter; scheduled integration remains a separate check. INTCLEAR execution verifies its value and return, not a physical interrupt or its origin.')
    (OUT/'retirement.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    (OUT/'retirement.md').write_text('# Original native retirement tail\n\n'
        +f'{len(cases)} standalone QEMU cases pass, including two excluded-path mutations.\n\n'
        +'\n'.join('- '+s for s in report['findings'])+'\n\n'+report['limits']+'\n')
    print(f'Original native retirement: {len(cases)} cases')


if __name__=='__main__':
    main()
