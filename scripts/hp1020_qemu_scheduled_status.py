"""Original StatusMgr receives completed notices under original RTOS scheduling.

A synthetic native producer submits the saved JobMgr-generated packet words;
the status task blocks and wakes through original priority/queue/context code.
Only allocation/free, constructor thread creation and startup readiness remain
hosted; actual scheduled tasks use original semaphores and mutexes.
"""
from pathlib import Path
from types import SimpleNamespace
import hashlib
import json
import subprocess
import tempfile
from hp1020_stock_status_queue import QueuedStatusReceiver, HOST as OLD_HOST
from hp1020_xtensa_stock import StockMachine
from hp1020_stock_notifications import invoke
from hp1020_xtensa_call0 import Program
from hp1020_qemu_ram import RETURN, STACK_TOP
from hp1020_qemu_scheduler import RANGES
from hp1020_qemu_multitask import NativeTasks

A = 0x22800000
B = A+256
PARK = A+512
PARKBUFFER = A+768
INPUT = 0x22700000
AS = 0x22900000
BS = 0x22a00000
SYNC_SERVICES = {0x10017dd8,0x10017e64,0x10017ed8,0x100181a4,0x10018214}
HOST = OLD_HOST-{0x100176c8}-SYNC_SERVICES
SYNC_CODE = [(0x10010d7c,0x10010db3),(0x10017dd8,0x10017e2c),
             (0x10017e64,0x10017e9c),(0x10017ed8,0x10017ef5),
             (0x1001811c,0x1001816c),(0x100181a4,0x100181dc),
             (0x10018214,0x10018234),(0x10019538,0x10019580),
             (0x10019634,0x10019860),(0x1001a380,0x1001a3c4),
             (0x1001a478,0x1001a590)]
ROOT = Path(__file__).resolve().parents[1]


class ScheduledStatus(QueuedStatusReceiver):
    def extension(self,op,args,nxt):
        if getattr(self,'receiver_mode',False) and op=='call8' and args[0] in SYNC_SERVICES|{0x100176c8}:
            return StockMachine.extension(self,op,args,nxt)
        return super().extension(op,args,nxt)


def native_source(notices,priorities,current,system):
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
 movi a11,0x10010590
 movi a12,{AS:#x}
 movi a13,{priorities[0]}
 call8 make_thread
 movi a10,{B:#x}
 movi a11,producer
 movi a12,{BS:#x}
 movi a13,{priorities[1]}
 call8 make_thread
 movi a10,{PARK:#x}
 movi a11,0
 movi a12,4
 movi a13,{PARKBUFFER:#x}
 movi a14,16
 movi a8,0x10017f18
 callx8 a8
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
 retw
producer:
 entry a1,64
 movi a3,{notices}
 movi a4,{INPUT:#x}
again:
 movi a10,10
 mov a11,a4
 movi a12,-1
 movi a8,0x10013668
 callx8 a8
 bnez a10,bad
 addi a4,a4,16
 addi a3,a3,-1
 bnez a3,again
 movi a10,{PARK:#x}
 mov a11,a1
 movi a12,-1
 movi a8,0x1001809c
 callx8 a8
bad:
 break 1,1
 j bad
'''


def run_scheduled_status(q,program,data,documents,fill,priorities):
    state = ScheduledStatus(program,data,fill=fill).replay()
    assert state.input_pos==len(data)
    assert len(state.notifications)==documents*2
    state.initialize_receiver()
    for address,size in ((A,0x1000),(AS,0x10000),(BS,0x10000),(INPUT,0x1000)):
        state.segments.append((address,bytearray([fill])*size,6))
        state.write_ranges.append((address,address+size))
    state.code_ranges += RANGES+SYNC_CODE
    current = state.read(0x10006a9c,4)
    system = state.read(0x10005d80,4)
    selected = state.read(0x10006aa0,4)
    source = native_source(len(state.notifications),priorities,current,system)
    invoke(state,0x10010504,qemu=q,host=HOST)
    # Execute only the original constructor's semaphore-initialization prefix.
    # Stop before event-group creation or datastore backing-value initialization;
    # those later effects are not needed for the existing descriptor fixture.
    init_runner = NativeTasks(q,state,SimpleNamespace(execute_ranges=[]),state.code_ranges,HOST)
    q.load(program.path)
    init_runner.synchronize(True)
    top = STACK_TOP-0x100
    q.put(top-12,(top+64).to_bytes(4,'big'))
    q.put(RETURN-3,bytes.fromhex('0b8000'))
    q.reset_cpu(RETURN-3)
    q.set_reg(2,top)
    q.set_reg(42,0x40000)
    q.set_reg(111,0x10000000)
    q.set_reg(9,0x10010d7c)
    while q.reg(0)!=0x10010db3:
        init_runner.step()
    init_runner.synchronize(False)
    locks = state.read(0x10006464,4)
    for i in range(38):
        assert state.read(locks+i*28,4)==state.read(0x100065bc,4)
        assert state.read(locks+i*28+8,4)==1
    # The same constructor later creates this datastore-wide mutex. Execute
    # that exact primitive with its observed arguments as a separate call.
    assert invoke(state,0x10017dd8,[state.read(0x10006474,4),state.read(0x10006478,4),1],q,HOST)==0
    invoke(state,0x1001135c,[24,1],q,HOST)
    registration = json.loads((ROOT/'analysis/queue-routing/registration.json').read_text())['registrations']
    objects = {r['queue']:int(r['object'],16) for r in registration}
    for i,index in enumerate((1,3)):
        assert invoke(state,0x10017f18,[objects[index],0,4,0x22600000+i*512,400],q,HOST)==0
        assert invoke(state,0x100135e0,[index,objects[index]],q,HOST)==0
    for n,notice in enumerate(state.notifications):
        for i,value in enumerate(notice['words']):
            state.write(INPUT+n*16+i*4,4,value)
    with tempfile.TemporaryDirectory(prefix='hp1020-scheduled-status-') as temp:
        root = Path(temp)
        (root/'status.S').write_text(source)
        prefix = program.prefix
        subprocess.run([prefix+'-as','--text-section-literals','status.S','-o','status.o'],cwd=root,check=True)
        subprocess.run([prefix+'-ld','-Ttext=0x20000000','-e','boot','status.o','-o','status.elf'],cwd=root,check=True)
        elf = root/'status.elf'
        fixture = Program(elf,prefix)
        state.segments += fixture.segments
        runner = NativeTasks(q,state,fixture,state.code_ranges,HOST)
        q.load(program.path)
        q.load(elf)
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
            if q.reg(0)==fixture.symbols['bad']:
                raise ValueError('scheduled status fixture service error')
            runner.step()
        q.reset_cpu(0x100188f3)
        q.set_reg(42,0x40000)
        q.set_reg(111,0x10000000)
        word = lambda a:int.from_bytes(q.read(a,4),'big')
        selections = []
        blocked = []
        while not(q.reg(0)==0x10018901 and word(selected)==0):
            pc = q.reg(0)
            if pc==fixture.symbols['bad']:
                raise ValueError('scheduled status producer failed or unexpectedly resumed')
            if pc==0x10018904:
                selections.append(word(selected))
            if pc==0x100176c8:
                thread = word(current)
                blocked.append((thread,word(thread+108)))
            runner.step()
        runner.synchronize(False)
        assert state.read(current,4)==0 and state.read(selected,4)==0
        assert state.read(state.read(0x10006ac0,4),4)==0
        assert state.read(A+48,4)==5 and state.read(B+48,4)==5
        for queue,thread,capacity in ((objects[10],A,25),(PARK,B,1)):
            assert state.read(queue+16,4)==0 and state.read(queue+20,4)==capacity
            assert state.read(queue+40,4)==thread and state.read(queue+44,4)==1
            assert state.read(thread+108,4)==queue
        assert state.read(state.read(0x100063e0,4),4)==documents
        assert state.read(state.read(0x10006408,4),4)==documents
        ptr = state.read(0x100063d8,4)
        assert state.read(ptr,1)==0 and state.read(ptr+24,1)==0
        live = {address:record for address,record in state.allocations.items() if not record['freed']}
        subscriber = state.read(state.read(0x10006490,4)+24*4,4)
        assert live=={subscriber:dict(size=20,kind=1,freed=False)}
        output = []
        for index in (1,3):
            queue = objects[index]
            assert state.read(queue+16,4)==1 and state.read(queue+44,4)==0
            read = state.read(queue+32,4)
            words = [state.read(read+i*4,4) for i in range(4 if index==1 else 2)]
            output.append((index,words))
        assert output==[(1,[45,24,0,2]),(3,[15,1])]
        assert set(selections)=={A,B}
        assert state.read(A+4,4)==selections.count(A) and state.read(B+4,4)==selections.count(B)
        producer_full_waits = blocked.count((B,objects[10]))
        if documents==13 and priorities[1]<priorities[0]:
            assert producer_full_waits>0
        for i in range(38):
            sem = locks+i*28
            assert state.read(sem+8,4)==1 and state.read(sem+12,4)==0 and state.read(sem+16,4)==0
        for cell in (0x100063d0,0x10006474):
            mutex = state.read(cell,4)
            assert state.read(mutex,4)==state.read(0x100065d0,4)
            assert state.read(mutex+8,4)==0 and state.read(mutex+28,4)==0 and state.read(mutex+32,4)==0
        assert all(service in HOST for service in runner.services)
        assert not (SYNC_SERVICES&set(runner.services))
        assert not ({0x10013658,0x1001809c,0x100176c8,0x10018750}&set(runner.services))
        return dict(status='pass',documents=documents,fill=fill,priorities=priorities,
            notices=len(state.notifications),instructions=runner.steps,producer_full_waits=producer_full_waits,
            selections=['status' if thread==A else 'producer' for thread in selections],
            remaining_allocation_bytes=20,packets=output,original_semaphores=38,original_mutexes=2,
            host_services=sorted({hex(service) for service in runner.services}),
            fixture_source_sha256=hashlib.sha256(source.encode()).hexdigest(),
            fixture_elf_sha256=hashlib.sha256(elf.read_bytes()).hexdigest())
