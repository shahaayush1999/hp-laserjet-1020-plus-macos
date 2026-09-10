"""Draft native page pipeline with explicitly supplied FIFO consumption.

No hardware task runs. A synthetic queue-1 consumer waits for the parser to finish,
executes the separately checked no-next-DMA retirement tail, and sends completion
through the original queue. All allocation, JobMgr/status and scheduling code is
original. This draft is outside the aggregate until its execution oracles pass.
"""
import hashlib
from pathlib import Path
import subprocess
import tempfile
from hp1020_xtensa_call0 import Program
from hp1020_qemu_ram import RETURN
from hp1020_qemu_pipeline import (
    P,J,S,PARK,OUT,PS,JS,SS,HOST,INPUT_HOST,prepare_pipeline,start,native_source,PipelineTrace)
from hp1020_qemu_retire import RETIRE_CODE,retirement_source
from hp1020_stock_pool import PoolRAM

C,CS = P+768,0x22d00000
Q1 = 0x10028a74


def page_source(documents,current,system,ready,video):
    source = native_source(documents,(5,2,31),current,system,ready)
    # Reuse the validated bootstrap, keeping each insertion anchored and unique.
    marker = f' movi a10,{PARK:#x}\n movi a11,0\n'
    assert source.count(marker)==1
    source = source.replace(marker,f''' movi a10,{C:#x}
 movi a11,completion
 movi a12,{CS:#x}
 movi a13,15
 call8 make_thread
'''+marker)
    marker = f' movi a8,{system:#x}\n movi a9,0\n'
    assert source.count(marker)==1
    source = source.replace(marker,f''' movi a10,{C:#x}
 movi a8,0x1001ab7c
 callx8 a8
'''+marker)
    marker = f' s32i a9,a8,4\n movi a10,{PARK:#x}\n'
    assert source.count(marker)==1
    source = source.replace(marker,f''' s32i a9,a8,4
 movi a10,{ready:#x}
 movi a11,8
 movi a12,0
 movi a8,0x10017dac
 callx8 a8
 bnez a10,bad
 movi a10,{PARK:#x}
''')
    source += f'''
.align 4
completion:
 entry a1,64
 movi a10,{ready:#x}
 movi a11,8
 movi a12,0
 addi a13,a1,16
 movi a14,-1
 movi a8,0x10017d28
 callx8 a8
 bnez a10,bad
completion_again:
 movi a10,{Q1:#x}
 mov a11,a1
 movi a12,-1
 movi a8,0x1001809c
 callx8 a8
 bnez a10,bad
completion_received:
 l32i a8,a1,0
 beqi a8,11,completion_work
 movi a9,45
 bne a8,a9,bad
 l32i a8,a1,4
 movi a9,24
 bne a8,a9,bad
 l32i a8,a1,8
 bnez a8,bad
 l32i a8,a1,12
 bnei a8,2,bad
 movi a8,{OUT:#x}
 l32i a9,a8,20
 addi a9,a9,1
 s32i a9,a8,20
 j completion_again
completion_work:
 l32i a3,a1,12
 mov a10,a3
 call8 retire_work
 bnez a10,bad
 movi a8,{OUT:#x}
 l32i a9,a8,16
 addi a9,a9,1
 s32i a9,a8,16
 movi a8,17
 s32i a8,a1,0
 movi a8,0
 s32i a8,a1,4
 s32i a8,a1,8
 s32i a3,a1,12
completion_send:
 movi a10,3
 mov a11,a1
 movi a8,0x10013658
 callx8 a8
 bnez a10,bad
 j completion_again
'''+retirement_source(video)
    return source


def run_pages(q,program,data,documents,pages,fill):
    state = prepare_pipeline(q,program,data,fill)
    state.segments.append((CS,bytearray([fill])*65536,6))
    state.write_ranges.append((CS,CS+65536))
    state.code_ranges += RETIRE_CODE
    video = state.read(0x10006770,4)
    state.put(video,bytes(256))
    current,system,selected,ready = [state.read(a,4) for a in
        (0x10006a9c,0x10005d80,0x10006aa0,0x10006530)]
    source = page_source(documents,current,system,ready,video)
    with tempfile.TemporaryDirectory(prefix='hp1020-page-pipeline-') as temp:
        root = Path(temp)
        (root/'pages.S').write_text(source)
        subprocess.run([program.prefix+'-as','--text-section-literals','pages.S','-o','pages.o'],cwd=root,check=True)
        subprocess.run([program.prefix+'-ld','-Ttext=0x20000000','-e','boot','pages.o','-o','pages.elf'],cwd=root,check=True)
        fixture = Program(root/'pages.elf',program.prefix)
        state.segments += fixture.segments
        runner = start(q,state,fixture,fixture.symbols['boot'],HOST)
        while q.reg(0)!=RETURN:
            runner.step()
        state.native_mode = True
        runner.host = INPUT_HOST
        q.reset_cpu(0x100188f3)
        q.set_reg(42,0x40000)
        q.set_reg(111,0x10000000)
        trace = PipelineTrace(runner)
        word,ar = trace.word,trace.ar
        selections,blocked,frees,scheduled,completed,retired,events = [],[],[],[],[],[],[]
        nodes_by_work = []
        while not(q.reg(0)==0x10018901 and word(selected)==0):
            pc = q.reg(0)
            if pc==0x10018904:
                selections.append(word(selected))
            if pc==0x100176c8:
                thread = word(current)
                blocked.append((thread,word(thread+108),word(thread+76)))
            if pc==0x10013408:
                frees.append(ar(10))
            if pc==0x10013658:
                queue,packet = ar(10),ar(11)
                kind = word(packet)
                if queue==1 and kind==11:
                    assert word(current)==J
                    scheduled.append(word(packet+12))
            if pc==fixture.symbols['completion_work']:
                assert word(OUT+4)==1 and state.input_pos==len(data)
                work = word(ar(1)+12)
                assert work==scheduled[len(completed)]
                node = word(work+80)
                nodes = []
                while node:
                    assert node not in [n for n,_,_ in nodes] and len(nodes)<128
                    payload = word(node+12)
                    ref = int.from_bytes(q.read(payload+78,2),'big')
                    assert ref==1
                    nodes.append((node,payload,ref))
                    node = word(node)
                assert nodes
                nodes_by_work.append((work,nodes))
            if pc==0x10014330:
                retired.append((ar(9),ar(8)&0xffff))
            if pc==0x10017dac and word(current)==C:
                events.append([ar(i) for i in (10,11,12)])
            if pc==fixture.symbols['completion_send']:
                completed.append(word(ar(1)+12))
            trace.observe()
            try:
                runner.step()
            except ValueError as error:
                raise ValueError(f'page pipeline documents={documents} pages={pages} fill={fill} '
                                 f'pc={pc:#x} thread={word(current):#x}: {error}') from error
        runner.synchronize(False)
        assert state.input_pos==len(data) and state.read(OUT+4,4)==1
        assert state.allocations=={} and set(runner.services)=={0x30000000}
        assert len(scheduled)==pages and completed==scheduled
        assert state.read(OUT+16,4)==pages and state.read(OUT+20,4)==1
        assert retired==[(payload,0) for _,nodes in nodes_by_work for _,payload,_ in nodes]
        assert events==[[state.read(0x100062dc,4),8,0]]*len(retired)
        assert not any(0x1001434b<=pc<0x100143a5 for pc in runner.visited)
        assert state.bytes_at(state.read(0x100062e4,4),8)==bytes(8)
        assert [state.read(state.read(cell,4),4) for cell in (0x100063e0,0x10006408)]==[documents]*2
        assert state.read(state.read(0x100062e8,4),2)==20
        table = state.read(0x1000647c,4)
        counters = [state.read(state.read(table+key*24+4,4),4) for key in (5,6)]
        assert counters==[pages,pages]
        blocks = PoolRAM.blocks(state)
        subscriber = state.read(state.read(0x10006490,4)+24*4,4)
        assert [(a,n) for a,n,f in blocks if f&0x80000000]==[(subscriber-12,20)]
        assert all(state.pool+12<=p<state.pool+state.pool_size for p in frees)
        for payload,_ in retired:
            assert payload in frees
        q3,q10 = state.read(0x100062d0,4),state.read(0x100063b4,4)
        for queue,thread,capacity in ((PARK,P,1),(q3,J,20),(q10,S,25),(Q1,C,25)):
            assert state.read(queue+16,4)==0 and state.read(queue+20,4)==capacity
            assert state.read(queue+40,4)==thread and state.read(queue+44,4)==1
            assert state.read(thread+48,4)==5 and state.read(thread+108,4)==queue
            assert state.read(thread+4,4)==selections.count(thread)
        assert state.read(current,4)==0 and state.read(selected,4)==0
        locks = state.read(0x10006464,4)
        for sem in [locks+i*28 for i in range(38)]+[state.read(0x100066ac,4),state.read(0x10006624,4)]:
            assert state.read(sem+8,4)==1 and state.read(sem+12,4)==0 and state.read(sem+16,4)==0
        for cell in (0x100063d0,0x10006474):
            mutex = state.read(cell,4)
            assert state.read(mutex+8,4)==0 and state.read(mutex+28,4)==0 and state.read(mutex+32,4)==0
        assert state.read(J+76,4)==2
        return dict(status='pass',documents=documents,pages=pages,fill=fill,
            instructions=runner.steps,input_bytes=len(data),original_frees=len(frees),
            remaining_allocation_bytes=20,scheduled_work=scheduled,completed_work=completed,
            retired_nodes=nodes_by_work,reference_decrements=retired,event_calls=events,
            page_counters=counters,online_notifications=1,job_timeout_armed=2,
            delivered_ticks=0,host_services=sorted(hex(x) for x in set(runner.services)),
            task_runs={name:selections.count(thread) for name,thread in
                (('parser',P),('job',J),('status',S),('completion',C))},
            input_sha256=hashlib.sha256(data).hexdigest(),
            fixture_source_sha256=hashlib.sha256(source.encode()).hexdigest(),
            fixture_elf_sha256=hashlib.sha256(fixture.path.read_bytes()).hexdigest(),
            trace=trace.records)
