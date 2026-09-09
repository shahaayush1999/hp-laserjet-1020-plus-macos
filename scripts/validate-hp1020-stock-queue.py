#!/usr/bin/env python3
"""Differential original queue execution against a bounded FIFO oracle."""
from collections import deque
import hashlib
import json
import os
from pathlib import Path
import random

from hp1020_stock_queue import QueueRAM, QueueWaitRace, QUEUE, BUFFER, SOURCE, DEST, THREAD
from hp1020_stock_notifications import invoke
from hp1020_xtensa_call0 import Program
from hp1020_qemu_ram import QemuRAM

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'analysis/open-firmware-model/stock-execution'


def snapshot(s):
    return {a:s.bytes_at(a,b-a) for a,b in s.program.write_ranges}|{QUEUE:s.bytes_at(QUEUE,0x4000)}


def fifo_case(program,engine,width,capacity,fill):
    s = QueueRAM(program,fill)
    size = width*4
    # Unusable trailing bytes are deliberate; capacity rounds down.
    assert invoke(s,0x10017f18,[QUEUE,SOURCE,width,BUFFER,size*capacity+3],engine)==0
    assert [s.read(QUEUE+i*4,4) for i in range(14)] == [
        0x51554555,SOURCE,width,capacity,0,capacity,BUFFER,BUFFER+size*capacity,
        BUFFER,BUFFER,0,0,QUEUE,QUEUE]
    assert invoke(s,0x100135e0,[3,QUEUE],engine)==0
    fifo = deque()
    rng = random.Random(1020+width*capacity)
    operations = ['receive']
    operations += (['send']*(capacity+1)+['receive']*(capacity+1))*3
    operations += [rng.choice(('send','receive')) for _ in range(12)]
    operations += ['receive']*(capacity+1)
    sent = received = 0
    for i,op in enumerate(operations):
        before_queue = s.bytes_at(QUEUE,56)
        if op == 'send':
            message = bytes(rng.randrange(256) for _ in range(size))
            s.put(SOURCE,message)
            # Original indexed wrapper maps nonzero RTOS errors to -1.
            indexed = i%2==1
            target,args = (0x10013668,[3,SOURCE,0]) if indexed else (0x100180dc,[QUEUE,SOURCE,0])
            result = invoke(s,target,args,engine)
            if len(fifo)==capacity:
                assert result==(0xffffffff if indexed else 11)
                assert s.bytes_at(QUEUE,56)==before_queue
            else:
                assert result==0
                fifo.append(message)
                sent += 1
            assert s.bytes_at(SOURCE,size)==message
        else:
            s.put(DEST,bytes([0x5a])*(size+8))
            result = invoke(s,0x1001809c,[QUEUE,DEST,0],engine)
            if fifo:
                assert result==0 and s.bytes_at(DEST,size)==fifo.popleft()
                received += 1
            else:
                assert result==10 and s.bytes_at(DEST,size)==bytes([0x5a])*size
                assert s.bytes_at(QUEUE,56)==before_queue
            assert s.bytes_at(DEST+size,8)==bytes([0x5a])*8
        assert s.read(QUEUE+16,4)==len(fifo)
        assert s.read(QUEUE+20,4)==capacity-len(fifo)
        assert s.read(QUEUE+32,4)==BUFFER+(received%capacity)*size
        assert s.read(QUEUE+36,4)==BUFFER+(sent%capacity)*size
        assert s.bytes_at(BUFFER+size*capacity,3)==bytes([fill])*3
    assert not fifo and sent==received
    return snapshot(s),len(operations)



def wait_race(program,engine,width,fill,send_wait):
    s = QueueWaitRace(program,fill)
    size = width*4
    assert invoke(s,0x10017f18,[QUEUE,0,width,BUFFER,size],engine)==0
    first,second = bytes(range(size)),bytes(range(64,64+size))
    s.put(SOURCE,first)
    if send_wait:
        assert invoke(s,0x100180dc,[QUEUE,SOURCE,0],engine)==0
        s.put(SOURCE,second)
    entry = 0x100180dc if send_wait else 0x1001809c
    address = SOURCE if send_wait else DEST
    invoke(s,entry,[QUEUE,address,0xffffffff],engine,{0x100176c8})
    assert s.suspensions==[THREAD]
    assert [s.read(THREAD+x,4) for x in (48,56,76,108,112,116,124)]==[
        5,1,0xffffffff,QUEUE,THREAD,THREAD,address]
    assert s.read(QUEUE+40,4)==THREAD and s.read(QUEUE+44,4)==1
    assert s.read(s.read(0x10006ac0,4),4)==1
    # Another operation satisfies the wait before actual suspension. Original
    # queue wakeup and resume helper clear the pending-suspend flag themselves.
    entry = 0x1001809c if send_wait else 0x100180dc
    assert invoke(s,entry,[QUEUE,DEST if send_wait else SOURCE,0],engine)==0
    assert s.bytes_at(DEST,size)==first
    assert all(s.read(THREAD+x,4)==0 for x in (48,56,76,104,132))
    assert s.read(QUEUE+40,4)==0 and s.read(QUEUE+44,4)==0
    assert s.read(s.read(0x10006ac0,4),4)==1
    if send_wait:
        assert s.read(QUEUE+16,4)==1 and s.read(QUEUE+20,4)==0
        assert invoke(s,0x1001809c,[QUEUE,DEST,0],engine)==0
        assert s.bytes_at(DEST,size)==second
    assert s.read(QUEUE+16,4)==0 and s.read(QUEUE+20,4)==1
    # Execute the original deferred helper as a fresh call, rather than claim
    # that this harness restored the paused caller's CPU context.
    s.cut_suspend = False
    invoke(s,0x100176c8,[THREAD],engine)
    assert s.read(s.read(0x10006ac0,4),4)==0
    return snapshot(s)


def main():
    p = Program(ROOT/'analysis/sihp1020.elf',os.environ.get('XTENSA_PREFIX','/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf'))
    cases = []
    with QemuRAM() as q:
        for width in (1,2,4,8,16):
            for capacity in (1,2,5):
                for fill in (0,0xcc):
                    original,n = fifo_case(p,None,width,capacity,fill)
                    independent,m = fifo_case(p,q,width,capacity,fill)
                    assert original==independent and n==m
                    cases.append(dict(kind='fifo',width=width,capacity=capacity,fill=fill,operations=n,status='pass'))
        errors = [
            ('create_null',0x10017f18,[0,0,4,BUFFER,64],9),
            ('create_existing',0x10017f18,[QUEUE,0,4,BUFFER,64],9),
            ('create_no_buffer',0x10017f18,[QUEUE+128,0,4,0,64],3),
            ('create_bad_width',0x10017f18,[QUEUE+128,0,3,BUFFER+128,64],5),
            ('create_too_small',0x10017f18,[QUEUE+128,0,4,BUFFER+128,15],5),
            ('create_interrupt',0x10017f18,[QUEUE+128,0,4,BUFFER+128,64],19),
            ('receive_null',0x1001809c,[0,DEST,0],9),
            ('receive_invalid',0x1001809c,[QUEUE+128,DEST,0],9),
            ('receive_no_destination',0x1001809c,[QUEUE,0,0],3),
            ('receive_wait_interrupt',0x1001809c,[QUEUE,DEST,0xffffffff],4),
            ('send_null',0x100180dc,[0,SOURCE,0],9),
            ('send_invalid',0x100180dc,[QUEUE+128,SOURCE,0],9),
            ('send_no_source',0x100180dc,[QUEUE,0,0],3),
            ('send_wait_interrupt',0x100180dc,[QUEUE,SOURCE,0xffffffff],4),
        ]
        for name,entry,args,expected in errors:
            for fill in (0,0xcc):
                results = []
                for engine in (None,q):
                    s = QueueRAM(p,fill)
                    assert invoke(s,0x10017f18,[QUEUE,0,4,BUFFER,64],engine)==0
                    if 'interrupt' in name:
                        s.write(s.read(0x10005d80,4),4,1)
                    before = snapshot(s)
                    assert invoke(s,entry,args,engine)==expected
                    assert before==snapshot(s)
                    results.append(before)
                assert results[0]==results[1]
                cases.append(dict(kind='error_no_mutation',name=name,fill=fill,result=expected,status='pass'))
        for fill in (0,0xcc):
            results = []
            for engine in (None,q):
                s = QueueRAM(p,fill)
                for i in range(3):
                    assert invoke(s,0x10017f18,[QUEUE+i*128,0,4,BUFFER+i*128,64],engine)==0
                assert s.read(s.read(0x10006b70,4),4)==QUEUE
                assert s.read(s.read(0x10006b74,4),4)==3
                for i in range(3):
                    assert s.read(QUEUE+i*128+48,4)==QUEUE+((i+1)%3)*128
                    assert s.read(QUEUE+i*128+52,4)==QUEUE+((i-1)%3)*128
                results.append(snapshot(s))
            assert results[0]==results[1]
            cases.append(dict(kind='created_queue_ring',count=3,fill=fill,status='pass'))
        for width in (1,2,4,8,16):
            for fill in (0,0xcc):
                for send_wait in (False,True):
                    assert wait_race(p,None,width,fill,send_wait)==wait_race(p,q,width,fill,send_wait)
                    cases.append(dict(kind='pending_suspend_race',width=width,fill=fill,
                                      waiting_operation='send' if send_wait else 'receive',status='pass'))
    report = dict(status='pass',total_cases=len(cases),cases=cases,
        elf_sha256=hashlib.sha256(p.path.read_bytes()).hexdigest(),
        source_sha256={name:hashlib.sha256((ROOT/'scripts'/name).read_bytes()).hexdigest() for name in
            ('validate-hp1020-stock-queue.py','hp1020_stock_queue.py','hp1020_qemu_task.py','hp1020_stock_notifications.py')},
        findings=[
            'Original queue create, send, receive, registration and indexed send execute with no whole-function host replacements. All five supported message widths, capacity rounding, full/empty errors and repeated FIFO wraparound agree with a Python deque and independent QEMU.',
            'Queue layout: +8 words/message, +12 capacity, +16 occupied, +20 available, +24/+28 buffer bounds, +32 read cursor, +36 write cursor, +40/+44 suspended list/count, +48/+52 created-list links. Original creation builds the circular list and count.',
            'Four-word messages copy all 16 bytes, including producer-uninitialized words; queue code does not sanitize them. Nonblocking empty/full return 10/11; the indexed send wrapper maps any nonzero send result to 0xffffffff.',
            'Rejected arguments and forbidden interrupt-context waits leave all original writable globals and fixture RAM unchanged.',
            'An explicit interleaving satisfies an empty receive or full send before its suspend helper runs. Original queue code delivers directly to the receiver or replaces the consumed slot from the waiting sender; original resume clears pending suspension, and the subsequently invoked original suspend helper restores preemption bookkeeping without a task switch.'
        ],
        limits='A synthetic ordinary thread is current. FIFO cases have no waiters. Race cases cut before suspension and invoke the deferred helper as a fresh call; they do not restore the paused caller or simulate an actual task switch, interrupt, timer expiry, hardware or USB. The interpreter abstracts PS masking; QEMU executes the original critical-section instructions on a different Xtensa core. FIFO delivery under these preconditions does not establish actual cancellation timing.')
    (OUT/'queue.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    (OUT/'queue.md').write_text('# Original RTOS queue RAM operations\n\n'+f'{len(cases)} cases pass in both execution engines against independent oracles.\n\n'+'\n'.join('- '+x for x in report['findings'])+'\n\n'+report['limits']+'\n')
    print(f'Original queue RAM: {len(cases)} independent cases')


if __name__=='__main__':
    main()
