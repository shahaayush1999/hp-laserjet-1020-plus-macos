"""Original RTOS initialization, thread creation and priority-driven queue blocking.

Synthetic producer/consumer tasks use original queues and let the original
ready lists, priority selection, suspend/resume and context switches run.
No scheduling, queue or context function is replaced with a host service.
"""
import hashlib
from pathlib import Path
import subprocess
import tempfile
from hp1020_xtensa_call0 import Program
from hp1020_qemu_ram import RETURN, STACK_TOP
from hp1020_qemu_stock_parser import VECTORS, guard_memory
from hp1020_stock_stop import StopRAM
from hp1020_stock_queue import CODE
from hp1020_qemu_context import FLUSH, CONTEXT

A = 0x22000000
B = A+256
Q = A+512
ACK = A+640
BUFFER = A+768
OUT = A+1280
AS = 0x22100000
BS = 0x22200000
RANGES = VECTORS+CODE+FLUSH+CONTEXT+[
    (0x10017554,0x100175c0),(0x1001a610,0x1001a6d9),(0x1001ab7c,0x1001abcc),
    (0x100176c8,0x1001788a),(0x1001aac0,0x1001ab79),
    (0x1001ae2c,0x1001ae8b),(0x1001b0f0,0x1001b128)]


def native_source(count,width,capacity,priorities,current,system):
    extra_log = '' if width==1 else '\n'.join(
        f' l32i a9,a1,{offset}\n s32i a9,a8,{offset}' for offset in (4,8,12))
    return f'''
.text
.align 4
.global boot
boot:
 entry a1,64
 movi a8,0x10017554
 callx8 a8
 movi a8,{current:#x}
 movi a9,{A:#x}
 s32i a9,a8,0
 movi a10,{A:#x}
 movi a11,task_a
 movi a12,{AS:#x}
 movi a13,{priorities[0]}
 movi a14,{count}
 call8 make_thread
 movi a10,{B:#x}
 movi a11,task_b
 movi a12,{BS:#x}
 movi a13,{priorities[1]}
 movi a14,{count}
 call8 make_thread
 movi a10,{Q:#x}
 movi a11,0
 movi a12,{width}
 movi a13,{BUFFER:#x}
 movi a14,{capacity*width*4}
 movi a8,0x10017f18
 callx8 a8
 bnez a10,bad
 movi a10,{ACK:#x}
 movi a11,0
 movi a12,1
 movi a13,{BUFFER+256:#x}
 movi a14,4
 movi a8,0x10017f18
 callx8 a8
 bnez a10,bad
 movi a8,{system:#x}
 movi a9,1
 s32i a9,a8,0
 movi a10,{A:#x}
 movi a8,0x1001ab7c
 callx8 a8
 movi a10,{B:#x}
 movi a8,0x1001ab7c
 callx8 a8
 movi a8,{system:#x}
 movi a9,0
 s32i a9,a8,0
 movi a2,0
 retw
.align 4
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
 mov a13,a6
 mov a14,a4
 movi a15,0x10000
 movi a8,0x1001a610
 callx8 a8
 bnez a10,bad
 retw
.align 4
task_a:
 entry a1,64
 mov a3,a2
 movi a4,1
again_a:
 s32i a4,a1,0
 slli a2,a4,1
 s32i a2,a1,4
 movi a2,0x1020cafe
 s32i a2,a1,8
 neg a2,a4
 s32i a2,a1,12
 movi a10,{Q:#x}
 mov a11,a1
 movi a12,-1
 movi a8,0x100180dc
 callx8 a8
 bnez a10,bad
 addi a4,a4,1
 addi a3,a3,-1
 bnez a3,again_a
 movi a10,{ACK:#x}
 addi a11,a1,16
 movi a12,-1
 movi a8,0x1001809c
 callx8 a8
 bnez a10,bad
 l32i a2,a1,16
 movi a8,{OUT:#x}
 s32i a2,a8,0
.global finish
finish:
 j finish
.align 4
task_b:
 entry a1,64
 mov a3,a2
 movi a4,0
 movi a5,0
again_b:
 movi a10,{Q:#x}
 mov a11,a1
 movi a12,-1
 movi a8,0x1001809c
 callx8 a8
 bnez a10,bad
 movi a8,{OUT+64:#x}
 slli a9,a5,{2 if width==1 else 4}
 add a8,a8,a9
 l32i a2,a1,0
 s32i a2,a8,0
{extra_log}
 add a4,a4,a2
 addi a5,a5,1
 movi a8,{OUT:#x}
 s32i a5,a8,4
 s32i a4,a8,8
 addi a3,a3,-1
 bnez a3,again_b
 s32i a4,a1,16
 movi a10,{ACK:#x}
 addi a11,a1,16
 movi a12,-1
 movi a8,0x100180dc
 callx8 a8
 bnez a10,bad
 retw
bad:
 break 1,1
 j bad
'''


def run_scheduler(q,program,prefix,*,count=5,width=4,capacity=1,priorities=(1,2),fill=0):
    state = StopRAM(program,0,[],[(A,0x1000),(AS,0x10000),(BS,0x10000)])
    for address,size in ((A,0x1000),(AS,0x10000),(BS,0x10000)):
        state.put(address,bytes([fill])*size)
    current = state.read(0x10006a9c,4)
    selected = state.read(0x10006aa0,4)
    system = state.read(0x10005d80,4)
    source = native_source(count,width,capacity,priorities,current,system)
    with tempfile.TemporaryDirectory(prefix='hp1020-scheduler-') as temp:
        root = Path(temp)
        (root/'tasks.S').write_text(source)
        subprocess.run([prefix+'-as','--text-section-literals','tasks.S','-o','tasks.o'],cwd=root,check=True)
        subprocess.run([prefix+'-ld','-Ttext=0x20000000','-e','boot','tasks.o','-o','tasks.elf'],cwd=root,check=True)
        elf = root/'tasks.elf'
        fixture = Program(elf,prefix)
        state.segments += fixture.segments
        q.load(program.path)
        q.load(elf)
        for begin,end in state.write_ranges:
            q.put(begin,state.bytes_at(begin,end-begin))
        q.put(current,A.to_bytes(4,'big'))
        q.put(system,bytes(4))
        # Output counters and log are fixture-owned, never queue/scheduler state.
        q.put(OUT,bytes(64+count*width*4))
        word = lambda address:int.from_bytes(q.read(address,4),'big')
        selections = []
        blocked = []
        visited = set()

        def step_to(stop):
            steps = 0
            while (pc := q.reg(0)) != stop:
                if steps>=100000:
                    raise ValueError('scheduler instruction budget exhausted')
                if pc == fixture.symbols['bad']:
                    raise ValueError('original service returned an unexpected error')
                if pc == 0x10018904:
                    selections.append(word(selected))
                if pc == 0x100176c8:
                    thread = word(current)
                    blocked.append(dict(thread=thread,state=word(thread+48),queue=word(thread+108)))
                if pc == 0x10018901 and word(selected)==0:
                    raise ValueError('scheduler became idle before the fixture completed')
                if pc != RETURN-3:
                    if any(a<=pc<b for a,b in fixture.execute_ranges):
                        decoded,ranges = fixture,fixture.execute_ranges
                    else:
                        decoded,ranges = program,RANGES
                    op,args,raw = decoded.instruction(pc)
                    if not any(a<=pc and pc+len(raw)<=b for a,b in ranges):
                        raise ValueError(f'scheduler left selected code: {pc:#x}')
                    if op in ('excw','ill','break'):
                        raise ValueError(f'unsupported scheduler instruction: {pc:#x} {op}')
                    state.pc = pc
                    guard_memory(state,q,op,args)
                visited.add(pc)
                steps += 1
                reply = q.command('s')
                if not reply.startswith('T05'):
                    raise ValueError(f'scheduler step failed: {reply}')
            return steps

        top = STACK_TOP-0x100
        q.put(top-12,(top+64).to_bytes(4,'big'))
        q.put(RETURN-3,bytes.fromhex('0b8000'))
        q.reset_cpu(RETURN-3)
        q.set_reg(2,top)
        q.set_reg(42,0x40000)
        q.set_reg(111,0x10000000)
        q.set_reg(9,fixture.symbols['boot'])
        setup_steps = step_to(RETURN)
        # The original initializer must populate the priority-bit lookup table;
        # leaving its BSS zero falsely makes the scheduler idle with a ready task.
        lookup = state.read(0x10006ab0,4)
        expected_lookup = bytes([0]+[(i&-i).bit_length()-1 for i in range(1,256)])
        assert q.read(lookup,256)==expected_lookup
        assert word(selected)==(A if priorities[0]<=priorities[1] else B)
        assert word(state.read(0x10006aa4,4))==(1<<priorities[0])|(1<<priorities[1])
        assert word(state.read(0x10006ac0,4))==0
        for thread,priority,stack in ((A,priorities[0],AS),(B,priorities[1],BS)):
            assert word(thread)==0x54485244
            assert word(thread+44)==priority and word(thread+60)==priority
            assert word(thread+48)==0 and word(thread+68)==fixture.symbols['task_a' if thread==A else 'task_b']
            assert word(thread+72)==count and word(thread+12)==stack
            assert word(thread+16)==stack+0xffff
        # Begin the actual scheduler using the original frames just created.
        q.reset_cpu(0x100188f3)
        q.set_reg(42,0x40000)
        q.set_reg(111,0x10000000)
        task_steps = step_to(fixture.symbols['finish'])
        expected_sum = count*(count+1)//2
        assert [word(OUT+i*4) for i in range(3)]==[expected_sum,count,expected_sum]
        expected_log = b''.join(b''.join(value.to_bytes(4,'big') for value in
            ([i] if width==1 else [i,2*i,0x1020cafe,(-i)&0xffffffff])) for i in range(1,count+1))
        assert q.read(OUT+64,len(expected_log))==expected_log
        assert word(current)==A and word(A+48)==0
        # Equal/lower-priority consumers return and terminate through the
        # original thread shell. A higher-priority producer preempts the ACK send.
        expected_b_state = 0 if priorities[0]<priorities[1] else 1
        assert word(B+48)==expected_b_state
        assert word(state.read(0x10006ac0,4))==0
        for queue,slots in ((Q,capacity),(ACK,1)):
            assert word(queue+16)==0 and word(queue+20)==slots
            assert word(queue+40)==0 and word(queue+44)==0
        assert selections[0]==(A if priorities[0]<=priorities[1] else B)
        assert set(selections)=={A,B}
        assert any(item['state']==5 for item in blocked)
        assert all(item['state'] in (1,5) for item in blocked)
        assert word(A+4)==selections.count(A) and word(B+4)==selections.count(B)
        return dict(status='pass',count=count,width=width,capacity=capacity,priorities=priorities,fill=fill,
            setup_instructions=setup_steps,task_instructions=task_steps,distinct_instructions=len(visited),
            selections=['producer' if t==A else 'consumer' for t in selections],
            suspensions=[dict(task='producer' if x['thread']==A else 'consumer',state=x['state']) for x in blocked],
            consumer_final_state=expected_b_state,result=expected_sum,
            fixture_source_sha256=hashlib.sha256(source.encode()).hexdigest(),
            fixture_elf_sha256=hashlib.sha256(elf.read_bytes()).hexdigest())
