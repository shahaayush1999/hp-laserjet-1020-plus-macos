"""Original timer wheel/task and timed waits under native RTOS scheduling.

A native lowest-priority clock task calls the stock tick routine explicitly;
INTENABLE remains zero. This exercises software timeouts, not IRQ delivery or
wall-clock accuracy. The original tick's CCOUNT/CCOMPARE instructions execute in
QEMU, but no automatically delivered timer interrupt is enabled or relied on.
"""
import hashlib
from pathlib import Path
import subprocess
import tempfile
from hp1020_xtensa_call0 import Program
from hp1020_stock_stop import StopRAM
from hp1020_qemu_scheduler import A,B,AS,BS,Q,ACK,OUT,RANGES,native_source as queue_source
from hp1020_qemu_ram import RETURN,STACK_TOP
from hp1020_qemu_multitask import NativeTasks

TIMER_STACK = 0x22300000
TIMER_CODE = RANGES+[(0x100175f4,0x100176c8),(0x1001788c,0x10017988),
    (0x100186a8,0x10018750),(0x1001a590,0x1001a5f4),
    (0x1001ace4,0x1001ad74),(0x1001ae8c,0x1001b058),
    (0x1001bac4,0x1001bb08)]


def native_source(delay,mode,early,current,system):
    # Reuse the proven two-thread/queue bootstrap, adding the original timer
    # initializer. It creates the timer task suspended, with its stock input
    # magic and entry point; only its stack/size/priority globals are seeded.
    source = queue_source(1,1,1,(5,31),current,system).split('.align 4\ntask_a:',1)[0]
    needle = f' movi a10,{A:#x}\n'
    source = source.replace(needle,' movi a8,0\n wsr.intenable a8\n movi a8,0x100175f4\n callx8 a8\n'+needle,1)
    if mode=='send':
        source = source.replace(f' movi a10,{ACK:#x}\n',f''' movi a9,77
 s32i a9,a1,0
 movi a10,{Q:#x}
 mov a11,a1
 movi a12,0
 movi a8,0x100180dc
 callx8 a8
 bnez a10,bad
 movi a10,{ACK:#x}
''',1)
    wait = f' movi a10,{delay}\n movi a8,0x1001766c' if mode=='sleep' else f''' movi a9,55
 s32i a9,a1,0
 movi a10,{Q:#x}
 mov a11,a1
 movi a12,{delay}
 movi a8,{0x1001809c if mode=='receive' else 0x100180dc:#x}'''
    satisfy = '' if not early else f''' bnei a3,1,after_satisfy
 movi a9,99
 s32i a9,a1,0
 movi a10,{Q:#x}
 mov a11,a1
 movi a12,0
 movi a8,{0x100180dc if mode=='receive' else 0x1001809c:#x}
 callx8 a8
 bnez a10,bad
after_satisfy:
'''
    return source+f'''
.align 4
task_a:
 entry a1,64
{wait}
 callx8 a8
 movi a8,{OUT:#x}
 s32i a10,a8,8
 l32i a9,a8,0
 s32i a9,a8,4
 l32i a9,a1,0
 s32i a9,a8,12
 movi a9,1
 s32i a9,a8,16
 movi a10,{ACK:#x}
 mov a11,a1
 movi a12,-1
 movi a8,0x1001809c
 callx8 a8
 bnez a10,bad
.global finish
finish:
 j finish
.align 4
task_b:
 entry a1,64
 movi a3,0
again_b:
 addi a3,a3,1
 movi a8,{OUT:#x}
 s32i a3,a8,0
 movi a8,{system:#x}
 movi a9,1
 s32i a9,a8,0
 movi a8,0x100186a8
 callx8 a8
 movi a8,{system:#x}
 movi a9,0
 s32i a9,a8,0
 movi a8,0x10018750
 callx8 a8
{satisfy}
 rsr.intenable a8
 bnez a8,bad
 movi a8,{delay+2}
 bltu a3,a8,again_b
 movi a10,{ACK:#x}
 mov a11,a1
 movi a12,0
 movi a8,0x100180dc
 callx8 a8
 bnez a10,bad
 j bad
bad:
 break 1,1
 j bad
'''


def run_timers(q,program,delay,mode,early,fill):
    assert mode in ('sleep','receive','send') and 1<=delay<=65 and not(early and (delay==1 or mode=='sleep'))
    regions = [(A,4096),(AS,65536),(BS,65536),(TIMER_STACK,65536)]
    state = StopRAM(program,0,TIMER_CODE,regions)
    for address,size in regions:
        state.put(address,bytes([fill])*size)
    state.put(OUT,bytes(32))
    current,system,selected = [state.read(a,4) for a in (0x10006a9c,0x10005d80,0x10006aa0)]
    state.write(system,4,0)
    for cell,value in ((0x10006af8,TIMER_STACK),(0x10006afc,65536),(0x10006b00,0)):
        state.write(state.read(cell,4),4,value)
    source = native_source(delay,mode,early,current,system)
    with tempfile.TemporaryDirectory(prefix='hp1020-timers-') as temp:
        root = Path(temp)
        (root/'timers.S').write_text(source)
        subprocess.run([program.prefix+'-as','--text-section-literals','timers.S','-o','timers.o'],cwd=root,check=True)
        subprocess.run([program.prefix+'-ld','-Ttext=0x20000000','-e','boot','timers.o','-o','timers.elf'],cwd=root,check=True)
        fixture = Program(root/'timers.elf',program.prefix)
        state.segments += fixture.segments
        runner = NativeTasks(q,state,fixture,TIMER_CODE)
        q.load(program.path)
        q.load(fixture.path)
        runner.synchronize(True)
        top = STACK_TOP-0x100
        q.put(top-12,(top+64).to_bytes(4,'big'))
        q.put(RETURN-3,bytes.fromhex('0b8000'))
        q.reset_cpu(RETURN-3)
        q.set_reg(2,top)
        q.set_reg(42,0x40000)
        q.set_reg(111,0x10000000)
        q.set_reg(9,fixture.symbols['boot'])
        while q.reg(0)!=RETURN:
            runner.step()
        timer = state.read(0x10006ae8,4)
        word = lambda address:int.from_bytes(q.read(address,4),'big')
        assert word(timer)==0x54485244 and word(timer+48)==3
        assert word(timer+68)==0x1001788c and word(timer+72)==0x4154494d
        assert word(timer+12)==TIMER_STACK and word(timer+44)==0
        q.reset_cpu(0x100188f3)
        q.set_reg(42,0x40000)
        q.set_reg(111,0x10000000)
        selections,suspensions,callbacks = [],[],[]
        while q.reg(0)!=fixture.symbols['finish']:
            pc = q.reg(0)
            if pc==0x10018904:
                selections.append(word(selected))
            if pc==0x100176c8:
                thread = word(current)
                suspensions.append((thread,word(thread+48),word(thread+76)))
            if pc==0x1001ace4:
                callbacks.append(word(OUT))
            runner.step()
        runner.synchronize(False)
        expected_tick = 1 if early else delay
        expected_result = 0 if early or mode=='sleep' else (10 if mode=='receive' else 11)
        assert [state.read(OUT+x,4) for x in (0,4,8,16)]==[delay+2,expected_tick,expected_result,1]
        if mode!='sleep':
            assert state.read(OUT+12,4)==(99 if early and mode=='receive' else 55)
        assert callbacks==([] if early else [delay])
        assert (A,4 if mode=='sleep' else 5,delay) in suspensions
        assert state.read(timer+48,4)==3 and state.read(A+48,4)==0
        assert state.read(current,4)==A and state.read(selected,4)==A
        assert state.read(state.read(0x10006ac0,4),4)==0
        assert state.read(state.read(0x10006ac4,4),4)==delay+2
        assert state.read(state.read(0x10006ad0,4),4)==0
        wheel = state.read(0x10006ad4,4)
        assert state.bytes_at(wheel,128)==bytes(128)
        assert state.read(state.read(0x10006adc,4),4)==wheel+4*((delay+2)%32)
        assert state.read(A+76,4)==0 and state.read(A+100,4)==0
        for queue,occupied in ((Q,int(mode=='send')),(ACK,0)):
            assert state.read(queue+16,4)==occupied and state.read(queue+20,4)==1-occupied
            assert state.read(queue+40,4)==0 and state.read(queue+44,4)==0
        if mode=='send':
            assert state.read(state.read(Q+32,4),4)==(55 if early else 77)
        for thread in (A,B,timer):
            assert state.read(thread+4,4)==selections.count(thread)
        assert runner.services==[]
        return dict(status='pass',delay=delay,mode=mode,early=early,fill=fill,
            ticks=delay+2,wake_tick=expected_tick,result=expected_result,timeout_callbacks=callbacks,
            instructions=runner.steps,timer_task_runs=selections.count(timer),host_services=[],
            fixture_source_sha256=hashlib.sha256(source.encode()).hexdigest(),
            fixture_elf_sha256=hashlib.sha256(fixture.path.read_bytes()).hexdigest())
