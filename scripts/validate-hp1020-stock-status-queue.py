#!/usr/bin/env python3
"""Completed stock notices traverse original queues into original status task."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path

from hp1020_stock_status_queue import QueuedStatusReceiver, HOST, RAM, THREAD
from hp1020_stock_notifications import invoke
from hp1020_xtensa_call0 import Program
from hp1020_qemu_ram import QemuRAM

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'analysis/open-firmware-model/stock-execution'
spec = importlib.util.spec_from_file_location('stock_helper',ROOT/'scripts/validate-hp1020-stock-execution.py')
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


def replay(program,data,documents,fill,engine):
    s = QueuedStatusReceiver(program,data,fill=fill).replay()
    assert s.input_pos==len(data)
    notices = s.notifications.copy()
    assert len(notices)==documents*2
    s.initialize_receiver()
    invoke(s,0x10010504,qemu=engine,host=HOST)
    registrations = json.loads((ROOT/'analysis/queue-routing/registration.json').read_text())['registrations']
    objects = {r['queue']:int(r['object'],16) for r in registrations}
    for i,index in enumerate((1,3)):
        assert invoke(s,0x10017f18,[objects[index],0,4,RAM+i*512,400],engine,HOST)==0
        assert invoke(s,0x100135e0,[index,objects[index]],engine,HOST)==0
    invoke(s,0x1001135c,[24,1],engine,HOST)
    for notice in notices:
        for i,value in enumerate(notice['words']):
            s.write(RAM+0x1000+i*4,4,value)
        assert invoke(s,0x10013668,[10,RAM+0x1000,0],engine,HOST)==0
    queue = objects[10]
    assert s.read(queue+16,4)==len(notices)
    invoke(s,0x10010590,qemu=engine,host=HOST)
    assert s.suspended==[THREAD]
    assert s.read(queue+16,4)==0 and s.read(queue+20,4)==25
    assert s.read(queue+40,4)==THREAD and s.read(queue+44,4)==1
    assert s.read(THREAD+108,4)==queue
    assert s.read(THREAD+112,4)==THREAD and s.read(THREAD+116,4)==THREAD
    assert s.read(THREAD+48,4)==5 and s.read(THREAD+56,4)==1
    assert s.read(THREAD+76,4)==0xffffffff
    assert s.read(s.read(0x10006ac0,4),4)==1
    assert s.read(s.read(0x100063e0,4),4)==documents
    assert s.read(s.read(0x10006408,4),4)==documents
    live = {p:a for p,a in s.allocations.items() if not a['freed']}
    subscriber = s.read(s.read(0x10006490,4)+24*4,4)
    assert live=={subscriber:dict(size=20,kind=1,freed=False)}
    packets = []
    for index in (1,3):
        assert s.read(objects[index]+16,4)==1
        assert invoke(s,0x1001809c,[objects[index],RAM+0x2000,0],engine,HOST)==0
        words = [s.read(RAM+0x2000+i*4,4) for i in range(4 if index==1 else 2)]
        packets.append((index,words))
        assert invoke(s,0x1001809c,[objects[index],RAM+0x2000,0],engine,HOST)==10
    assert packets==[(1,[45,24,0,2]),(3,[15,1])]
    ptr = s.read(0x100063d8,4)
    assert s.read(ptr,1)==0 and s.read(ptr+24,1)==0
    return dict(packets=packets,state=s.bytes_at(ptr,28).hex(),live=live,
                consumed=len(notices),suspension_state=5)


def main():
    p = Program(ROOT/'analysis/sihp1020.elf',os.environ.get('XTENSA_PREFIX','/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf'))
    base = helper.chunks((ROOT/'analysis/samples/generated/matrix-a4_default.zjs').read_bytes())[0]
    normal = helper.stream(base)
    cases = []
    with QemuRAM() as q:
        for name,data,documents in [('one_document',normal,1),('three_documents',normal*3,3),
                ('three_pages',helper.stream(base[:1]+base[1:6]*3+base[-1:]),1),
                ('empty',helper.stream(base[:1]+base[-1:]),1)]:
            for fill in (0,0xcc):
                original = replay(p,data,documents,fill,None)
                independent = replay(p,data,documents,fill,q)
                assert original==independent
                cases.append(dict(name=name,fill=fill,documents=documents,result=original,status='pass'))
    report = dict(status='pass',total_cases=len(cases),cases=cases,
        elf_sha256=hashlib.sha256(p.path.read_bytes()).hexdigest(),
        source_sha256={name:hashlib.sha256((ROOT/'scripts'/name).read_bytes()).hexdigest() for name in
            ('validate-hp1020-stock-status-queue.py','hp1020_stock_status_queue.py','hp1020_stock_queue.py',
             'hp1020_stock_status_publication.py','hp1020_stock_notifications.py','hp1020_qemu_task.py')},
        findings=[
            'Original completed JobMgr notices are pre-enqueued through original indexed send. Original StatusMgr creates queue 10, receives the queued notices, updates counters/status and frees every transient notice allocation; only the persistent ONLINE subscription remains.',
            'Original status publication queues ONLINE [45,24,0,2] to PrintMgr queue 1 and cancel [15,1] to JobMgr queue 3. Original receive retrieves both from actual queue buffers; no whole queue function is substituted.',
            'After draining all notices, original infinite-wait receive inserts the current thread into the queue suspension ring, records its destination and wait state, and reaches the explicit scheduler boundary. The test stops before thread suspension/context switching.'
        ],
        limits='Parser/JobMgr notice production still uses injected FIFO page completion. Notices are pre-enqueued; this is not a concurrent task schedule. RTOS semaphore/thread creation, locks, allocation and final task suspension remain host services. Empty language-context table omits outward callbacks. PrintMgr/JobMgr do not consume the emitted packets in this combined test. No printer, DMA, hardware stop, IRQ or recovery evidence is claimed.')
    (OUT/'status-queue.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    (OUT/'status-queue.md').write_text('# Original status task with original queues\n\n'+f'{len(cases)} combined cases agree between QEMU and the interpreter.\n\n'+'\n'.join('- '+x for x in report['findings'])+'\n\n'+report['limits']+'\n')
    print(f'Original queued status task: {len(cases)} independent cases')


if __name__=='__main__':
    main()
