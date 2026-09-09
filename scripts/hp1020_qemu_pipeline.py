"""Original parser, JobMgr and StatusMgr share native scheduling and an original pool.

The host supplies stream bytes only. The initial scope is empty documents:
no page completion, rendering, PrintMgr/VideoThread or physical output is inferred.
JobMgr's final two-tick wait is armed; no ticks or automatic IRQs are delivered.


UNFINISHED HANDOFF: equal-priority 11–13-document runs hit a guarded null read.
See analysis/open-firmware-model/next-evidence.md before extending this experiment.
"""
import hashlib
from pathlib import Path
from types import SimpleNamespace
import subprocess
import tempfile
from hp1020_xtensa_call0 import Program
from hp1020_stock_parser_harness import ParserHarness,CONTEXT,INPUT_CALLBACK,PUSHBACK_CALLBACK
from hp1020_stock_notifications import invoke
from hp1020_qemu_scheduled_status import ScheduledStatus,SYNC_CODE,READY_CODE,HOST
from hp1020_stock_pool import POOL,POOL_CODE,PoolRAM,seed_pool
from hp1020_qemu_timers import TIMER_CODE
from hp1020_qemu_multitask import NativeTasks
from hp1020_qemu_ram import RETURN,STACK_TOP

P = 0x22800000
J,S,PARK,BUFFER,OUT = P+256,P+512,P+1024,P+1536,P+2048
PS,JS,SS,TS = 0x22900000,0x22a00000,0x22b00000,0x22c00000
INPUT_HOST = {INPUT_CALLBACK,PUSHBACK_CALLBACK}


class Pipeline(ScheduledStatus):
    def extension(self,op,args,nxt):
        if getattr(self,'native_mode',False) and op=='call8' and args[0] in INPUT_HOST:
            return ParserHarness.extension(self,op,args,nxt)
        return super().extension(op,args,nxt)


def start(q,state,fixture,entry,host):
    q.load(state.program.path)
    if fixture.path:
        q.load(fixture.path)
    runner = NativeTasks(q,state,fixture,state.code_ranges,host)
    runner.synchronize(True)
    top = STACK_TOP-0x100
    q.put(top-12,(top+64).to_bytes(4,'big'))
    q.put(RETURN-3,bytes.fromhex('0b8000'))
    q.reset_cpu(RETURN-3)
    q.set_reg(2,top)
    q.set_reg(42,0x40000)
    q.set_reg(111,0x10000000)
    q.set_reg(9,entry)
    return runner


def native_source(documents,priorities,current,system,ready):
    source = f'''
.text
.align 4
.global boot
boot:
 entry a1,64
 movi a8,0
 wsr.intenable a8
 movi a8,0x10017554
 callx8 a8
 movi a8,{current:#x}
 movi a9,{P:#x}
 s32i a9,a8,0
 movi a8,0x100175f4
 callx8 a8
'''
    for thread,entry,stack,priority in zip((P,J,S),('parser','0x1000e414','0x10010590'),(PS,JS,SS),priorities):
        source += f' movi a10,{thread:#x}\n movi a11,{entry}\n movi a12,{stack:#x}\n movi a13,{priority}\n call8 make_thread\n'
    source += f''' movi a10,{PARK:#x}
 movi a11,0
 movi a12,1
 movi a13,{BUFFER:#x}
 movi a14,4
 movi a8,0x10017f18
 callx8 a8
 bnez a10,bad
 movi a8,{system:#x}
 movi a9,1
 s32i a9,a8,0
'''
    for thread in (P,J,S):
        source += f' movi a10,{thread:#x}\n movi a8,0x1001ab7c\n callx8 a8\n'
    source += f''' movi a8,{system:#x}
 movi a9,0
 s32i a9,a8,0
 retw
make_thread:
 entry a1,64
 s32i a5,a1,0
 s32i a5,a1,4
 movi a8,0
 s32i a8,a1,8
 s32i a8,a1,12
 mov a10,a2
 movi a11,0
 mov a12,a3
 movi a13,0
 mov a14,a4
 movi a15,0x10000
 movi a8,0x1001a610
 callx8 a8
 bnez a10,bad
 retw
parser:
 entry a1,64
 movi a10,{ready:#x}
 movi a11,4
 movi a12,0
 movi a8,0x10017dac
 callx8 a8
 bnez a10,bad
 movi a3,{documents}
again:
 movi a10,{CONTEXT:#x}
 movi a8,0x10009d34
 callx8 a8
 movi a8,{OUT:#x}
 s32i a10,a8,0
 addi a3,a3,-1
 bnez a3,again
 movi a9,1
 s32i a9,a8,4
 movi a10,{PARK:#x}
 mov a11,a1
 movi a12,-1
 movi a8,0x1001809c
 callx8 a8
bad:
 break 1,1
 j bad
'''
    return source


def run_pipeline(q,program,data,documents,fill,priorities):
    state = Pipeline(program,data,fill=fill)
    # Existing descriptor/context fixtures only: no parser/JobMgr replay occurs.
    state.initialize_job()
    state.initialize_receiver()
    for address,size in ((P,4096),(PS,65536),(JS,65536),(SS,65536),(TS,65536)):
        state.segments.append((address,bytearray([fill])*size,6))
        state.write_ranges.append((address,address+size))
    state.put(OUT,bytes(32))
    state.code_ranges += SYNC_CODE+READY_CODE+POOL_CODE+TIMER_CODE+[
        (0x1000e3ac,0x1000e414),(0x1001b770,0x1001b788)]
    state.pool,state.pool_size = POOL,65536
    seed_pool(state,POOL,state.pool_size,fill)
    for cell,value in ((0x10006af8,TS),(0x10006afc,65536),(0x10006b00,0)):
        state.write(state.read(cell,4),4,value)
    for cell in (0x100066ac,0x10006624):
        assert invoke(state,0x1001811c,[state.read(cell,4),0,1],q,HOST)==0
    invoke(state,0x10010504,qemu=q,host=HOST)
    invoke(state,0x1000e3ac,qemu=q,host=HOST)
    runner = start(q,state,SimpleNamespace(path=None,execute_ranges=[]),0x10010d7c,HOST)
    while q.reg(0)!=0x10010db3:
        runner.step()
    runner.synchronize(False)
    assert invoke(state,0x10017dd8,[state.read(0x10006474,4),state.read(0x10006478,4),1],q,HOST)==0
    invoke(state,0x1001135c,[24,1],q,HOST)
    # Audited queue-1 object, retaining the output packets as evidence. No
    # PrintMgr consumer or downstream engine/video task is started.
    q1 = 0x10028a74
    assert invoke(state,0x10017f18,[q1,0,4,0x22600000,400],q,HOST)==0
    assert invoke(state,0x100135e0,[1,q1],q,HOST)==0
    ready = state.read(0x10006530,4)
    assert invoke(state,0x10017ca0,[ready,0],q,HOST)==0
    current,system,selected = [state.read(a,4) for a in (0x10006a9c,0x10005d80,0x10006aa0)]
    source = native_source(documents,priorities,current,system,ready)
    with tempfile.TemporaryDirectory(prefix='hp1020-pipeline-') as temp:
        root = Path(temp)
        (root/'pipeline.S').write_text(source)
        subprocess.run([program.prefix+'-as','--text-section-literals','pipeline.S','-o','pipeline.o'],cwd=root,check=True)
        subprocess.run([program.prefix+'-ld','-Ttext=0x20000000','-e','boot','pipeline.o','-o','pipeline.elf'],cwd=root,check=True)
        fixture = Program(root/'pipeline.elf',program.prefix)
        state.segments += fixture.segments
        runner = start(q,state,fixture,fixture.symbols['boot'],HOST)
        while q.reg(0)!=RETURN:
            runner.step()
        state.native_mode = True
        runner.host = INPUT_HOST
        q.reset_cpu(0x100188f3)
        q.set_reg(42,0x40000)
        q.set_reg(111,0x10000000)
        word = lambda address:int.from_bytes(q.read(address,4),'big')
        selections,blocked,frees = [],[],[]
        while not(q.reg(0)==0x10018901 and word(selected)==0):
            pc = q.reg(0)
            if pc==0x10018904:
                selections.append(word(selected))
            if pc==0x100176c8:
                thread = word(current)
                blocked.append((thread,word(thread+108),word(thread+76)))
            if pc==0x10013408:
                frees.append(q.reg(((q.reg(38)*4+10)%32)+1))
            try:
                runner.step()
            except ValueError as error:
                raise ValueError(f'pipeline documents={documents} priorities={priorities} fill={fill} pc={q.reg(0):#x} thread={word(current):#x}: {error}') from error
        runner.synchronize(False)
        assert state.input_pos==len(data) and state.read(OUT+4,4)==1
        assert state.allocations=={},'host allocator was unexpectedly used'
        assert set(runner.services)<=INPUT_HOST and INPUT_CALLBACK in runner.services
        assert state.bytes_at(state.read(0x100062e4,4),8)==bytes(8)
        assert state.read(state.read(0x100063e0,4),4)==documents
        assert state.read(state.read(0x10006408,4),4)==documents
        blocks = PoolRAM.blocks(state)
        subscriber = state.read(state.read(0x10006490,4)+24*4,4)
        assert [(a,n) for a,n,f in blocks if f&0x80000000]==[(subscriber-12,20)]
        assert len(frees)>documents and all(state.pool+12<=p<state.pool+state.pool_size for p in frees)
        q3,q10 = state.read(0x100062d0,4),state.read(0x100063b4,4)
        for queue,thread,capacity in ((PARK,P,1),(q3,J,20),(q10,S,25)):
            assert state.read(queue+16,4)==0 and state.read(queue+20,4)==capacity
            assert state.read(queue+40,4)==thread and state.read(queue+44,4)==1
            assert state.read(thread+48,4)==5 and state.read(thread+108,4)==queue
            assert state.read(thread+4,4)==selections.count(thread)
        assert state.read(J+76,4)==2
        wheel = state.read(0x10006ad4,4)
        assert state.read(J+100,4)==wheel+4 and state.read(wheel+4,4)==J+76
        assert state.read(state.read(0x10006ac4,4),4)==0
        assert state.read(state.read(0x10006ae8,4)+48,4)==3
        assert state.read(current,4)==0 and state.read(selected,4)==0
        assert state.read(state.read(0x10006ac0,4),4)==0
        locks = state.read(0x10006464,4)
        for sem in [locks+i*28 for i in range(38)]+[state.read(0x100066ac,4),state.read(0x10006624,4)]:
            assert state.read(sem+8,4)==1 and state.read(sem+12,4)==0 and state.read(sem+16,4)==0
        for cell in (0x100063d0,0x10006474):
            mutex = state.read(cell,4)
            assert state.read(mutex+8,4)==0 and state.read(mutex+28,4)==0 and state.read(mutex+32,4)==0
        assert state.read(q1+16,4)==1
        output = [state.read(state.read(q1+32,4)+i*4,4) for i in range(4)]
        assert output==[45,24,0,2]
        names = {P:'parser',J:'job',S:'status'}
        return dict(status='pass',documents=documents,fill=fill,priorities=priorities,
            instructions=runner.steps,input_bytes=len(data),original_frees=len(frees),
            remaining_allocation_bytes=20,job_timeout_armed=2,delivered_ticks=0,
            output=output,host_services=sorted(hex(x) for x in set(runner.services)),
            task_runs={names[t]:selections.count(t) for t in names},
            job_queue_full_waits=sum(t==P and queue==q3 for t,queue,_ in blocked),
            status_queue_full_waits=sum(t==J and queue==q10 for t,queue,_ in blocked),
            input_sha256=hashlib.sha256(data).hexdigest(),
            fixture_source_sha256=hashlib.sha256(source.encode()).hexdigest(),
            fixture_elf_sha256=hashlib.sha256(fixture.path.read_bytes()).hexdigest())
