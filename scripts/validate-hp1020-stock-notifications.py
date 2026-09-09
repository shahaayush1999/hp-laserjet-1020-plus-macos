#!/usr/bin/env python3
"""Verify stock ONLINE notification routing and final notice ownership."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path

from hp1020_stock_notifications import NotificationProducer, StatusReceiver, invoke, PRODUCER_HOST, RECEIVER_HOST
from hp1020_stock_parser_harness import CONTEXT
from hp1020_qemu_ram import QemuRAM
from hp1020_xtensa_call0 import Program

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'analysis/open-firmware-model/stock-execution'
spec = importlib.util.spec_from_file_location('job_validation', ROOT/'scripts/validate-hp1020-stock-jobmgr.py')
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


def main():
    program = Program(ROOT/'analysis/sihp1020.elf',os.environ.get('XTENSA_PREFIX','/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf'))
    cases = []
    with QemuRAM() as q:
        for value in (0,1):
            for fill in (0,0xcc):
                results = []
                for engine in (None,q):
                    producer = NotificationProducer(program,[],fill=fill)
                    invoke(producer,0x1000f324,qemu=engine,host=PRODUCER_HOST)
                    request,buffer = CONTEXT+0x100,CONTEXT+0x120
                    producer.write(request,4,24)
                    producer.write(request+4,4,buffer)
                    invoke(producer,0x10010f54,[request],engine,PRODUCER_HOST)
                    producer.write(buffer,1,value)
                    invoke(producer,0x10010fd0,[request],engine,PRODUCER_HOST)
                    packet = producer.sent[-1]
                    assert packet == dict(queue=1,words=[45,24,value,2])
                    table = producer.read(0x1000647c,4)
                    destination = producer.read(table+24*24+4,4)
                    assert producer.read(destination,1) == value
                    # Explicit task cut: packet plus committed datastore byte.
                    consumer = NotificationProducer(program,[packet['words']],fill=fill)
                    consumer.write(destination,1,producer.read(destination,1))
                    invoke(consumer,0x1000f324,qemu=engine,host=PRODUCER_HOST)
                    observed = consumer.read(consumer.read(0x10006338,4)+1,1)
                    assert observed == value and 0x1000f497 in consumer.visited
                    results.append((packet,observed,consumer.sent))
                assert results[0] == results[1]
                cases.append(dict(kind='ONLINE_notification',value=value,fill=fill,status='pass'))
        base = helper.chunks((ROOT/'analysis/samples/generated/matrix-a4_default.zjs').read_bytes())[0]
        normal = helper.stream(base)
        empty = helper.stream(base[:1]+base[-1:])
        multiple = helper.stream(base[:1]+base[1:6]*3+base[-1:])
        for name,data,documents in [('one_document',normal,1),('three_documents',normal*3,3),
                                    ('three_pages',multiple,1),('empty',empty,1)]:
            for fill in (0,0xcc):
                results = []
                for engine in (None,q):
                    receiver = StatusReceiver(program,data,fill=fill).replay()
                    assert receiver.input_pos == len(data)
                    notices = [m for m in receiver.notifications if m['words'][0]==47]
                    assert len(notices) == documents
                    owned = {n['words'][3] for n in notices}
                    assert {ptr for ptr,a in receiver.allocations.items() if not a['freed']} == owned
                    receiver.initialize_receiver()
                    invoke(receiver,0x10010590,qemu=engine,host=RECEIVER_HOST)
                    assert receiver.receive_index == len(receiver.notifications)
                    assert all(a['freed'] for a in receiver.allocations.values())
                    assert receiver.read(receiver.read(0x100063d8,4)+24,1) == 0
                    started = receiver.read(receiver.read(0x100063e0,4),4)
                    completed = receiver.read(receiver.read(0x10006408,4),4)
                    assert started == completed == documents
                    # Freed notice memory must become inaccessible to execution.
                    for ptr in owned:
                        try:
                            receiver.read(ptr,4)
                        except ValueError as error:
                            assert 'unmapped RAM' in str(error)
                        else:
                            raise AssertionError('released completion notice remains mapped')
                    results.append((receiver.status_updates,receiver.allocations))
                assert results[0] == results[1]
                cases.append(dict(kind='completion_ownership',name=name,documents=documents,fill=fill,status='pass'))
    report = dict(status='pass',total_cases=len(cases),cases=cases,
                  elf_sha256=hashlib.sha256(program.path.read_bytes()).hexdigest(),
                  source_sha256={name:hashlib.sha256((ROOT/'scripts'/name).read_bytes()).hexdigest() for name in
                     ('validate-hp1020-stock-notifications.py','hp1020_stock_notifications.py','hp1020_stock_printmgr_harness.py',
                      'hp1020_stock_lifecycle_harness.py','hp1020_qemu_task.py','hp1020_qemu_ram.py','hp1020_qemu_stock_parser.py')},
                  findings=[
                    'Original PrintMgr subscriber creation followed by original datastore lock/read/write emits [45,24,value,2] to queue 1. Relaying that packet and committed ONLINE byte to original PrintMgr updates its online state for both zero and one.',
                    'Original StatusMgr consumes JobMgr begin/end notices, balances document counters and releases the final 16-byte completion allocations. All parser/job/page/raster/notice allocations are freed in the selected completed lifecycles.'
                  ],
                  limits='Original parser/JobMgr fixture supplies completion notices after injected FIFO completion. QEMU independently executes the producer and receiver instruction ranges. Queue relay and initialized task state are explicit composition boundaries. Status publication at 0x10010838 remains a host callback; optional host-language callbacks are disabled by original context flags. No USB, mechanical stop, DMA, RTOS schedule or physical printing is proved.')
    (OUT/'notifications.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    (OUT/'notifications.md').write_text('# Original notification routing and ownership\n\n'
        +f'{len(cases)} cases agree between interpreter, QEMU and explicit packet/counter/lifetime expectations.\n\n'
        +'\n'.join('- '+f for f in report['findings'])+'\n\n'+report['limits']+'\n')
    print(f'Original notifications: {len(cases)} QEMU/interpreter cases')


if __name__ == '__main__':
    main()
