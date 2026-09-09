#!/usr/bin/env python3
"""Original status publication against datastore, history, queue and lifetime oracles."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path

from hp1020_stock_status_publication import FullStatusReceiver, HOST
from hp1020_stock_notifications import invoke
from hp1020_xtensa_call0 import Program
from hp1020_qemu_ram import QemuRAM

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'analysis/open-firmware-model/stock-execution'
spec = importlib.util.spec_from_file_location('stock_helper',ROOT/'scripts/validate-hp1020-stock-execution.py')
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


def descriptor_value(state,key):
    table = state.read(0x1000647c,4)
    record = table+key*24
    kind = state.read(record+8,4)
    assert kind in (0,1,2)
    return state.read(state.read(record+4,4),1<<kind)


def defined_packets(state):
    result = []
    for packet in state.sent:
        queue,words = packet['queue'],packet['words']
        assert (queue,words[0]) in ((1,45),(3,15))
        # Cancel words 2/3 are not initialized by this producer; JobMgr uses
        # the selector in word 1. Datastore notifications define all four words.
        result.append((queue,words if queue==1 else words[:2]))
    return result


def initialize(state,engine,subscribe=True):
    state.initialize_receiver()
    invoke(state,0x10010504,qemu=engine,host=HOST)
    ptr = state.read(0x100063d8,4)
    assert state.read(ptr,1)==1 and state.read(ptr+4,4)==2
    assert state.read(ptr+8,4)==0x04800100 and state.read(ptr+20,4)==10
    assert state.read(ptr+24,1)==0
    assert state.read(state.read(0x100066f0,4)+10*4,4)==state.read(0x100063b4,4)
    queue = next(x for x in state.creates if x['function']=='0x10017f18')['args']
    assert queue[0]==state.read(0x100063b4,4) and queue[2]==4 and queue[4]==400
    if subscribe:
        invoke(state,0x1001135c,[24,1],engine,HOST)
    return ptr


def main():
    program = Program(ROOT/'analysis/sihp1020.elf',os.environ.get('XTENSA_PREFIX','/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf'))
    base = helper.chunks((ROOT/'analysis/samples/generated/matrix-a4_default.zjs').read_bytes())[0]
    normal = helper.stream(base)
    empty = helper.stream(base[:1]+base[-1:])
    multiple = helper.stream(base[:1]+base[1:6]*3+base[-1:])
    cases = []
    with QemuRAM() as q:
        for name,data,documents in [('one_document',normal,1),('three_documents',normal*3,3),
                                    ('three_pages',multiple,1),('empty',empty,1)]:
            for fill in (0,0xcc):
                results = []
                for engine in (None,q):
                    state = FullStatusReceiver(program,data,fill=fill).replay()
                    assert state.input_pos==len(data)
                    assert sum(n['words'][0]==47 for n in state.notifications)==documents
                    ptr = initialize(state,engine)
                    invoke(state,0x10010590,qemu=engine,host=HOST)
                    assert state.receive_index==len(state.notifications)
                    assert state.read(state.read(0x100063e0,4),4)==documents
                    assert state.read(state.read(0x10006408,4),4)==documents
                    assert state.read(ptr+24,1)==0
                    live = {p:a for p,a in state.allocations.items() if not a['freed']}
                    subscriber = state.read(state.read(0x10006490,4)+24*4,4)
                    assert live=={subscriber:dict(size=20,kind=1,freed=False)}
                    assert descriptor_value(state,24)==0 and descriptor_value(state,25)==0xe6101100
                    assert defined_packets(state)==[(1,[45,24,0,2]),(3,[15,1])]
                    invoke(state,0x10010838,[0x04800100,1],engine,HOST)
                    assert state.read(ptr,1)==1 and state.read(ptr+4,4)==2
                    assert descriptor_value(state,24)==1 and descriptor_value(state,25)==0x04800100
                    assert defined_packets(state)==[(1,[45,24,0,2]),(3,[15,1]),(1,[45,24,1,2])]
                    cursor = state.read(0x1000642c,4)
                    history = state.read(0x10006428,4)
                    assert state.read(cursor,4)==2
                    assert state.read(history,4)==0xe6101100 and state.read(history+4,4)==0x04800100
                    before = {a:state.bytes_at(a,b-a) for a,b in program.write_ranges}
                    invoke(state,0x10010838,[0x04800100,1],engine,HOST)
                    assert before=={a:state.bytes_at(a,b-a) for a,b in program.write_ranges}
                    results.append((defined_packets(state),state.bytes_at(ptr,28),live))
                assert results[0]==results[1]
                cases.append(dict(kind='completed_lifecycle_and_status_clear',name=name,documents=documents,fill=fill,status='pass'))
        for event,reason in ((0x02000800,4),(0x02000a00,3),(0x02100800,1)):
            for fill in (0,0xcc):
                results = []
                for engine in (None,q):
                    state = FullStatusReceiver(program,b'',fill=fill)
                    ptr = initialize(state,engine)
                    # Explicit cached-status / active-document precondition.
                    state.write(ptr+8,4,0x100)
                    state.write(ptr+24,1,1)
                    invoke(state,0x10010838,[event,10],engine,HOST)
                    assert defined_packets(state)==[(3,[15,reason])]
                    assert state.read(ptr,1)==1 and state.read(ptr+4,4)==2
                    assert descriptor_value(state,24)==0 and descriptor_value(state,25)==event
                    assert state.read(state.read(0x1000642c,4),4)==1
                    results.append((defined_packets(state),state.bytes_at(ptr,28)))
                assert results[0]==results[1]
                cases.append(dict(kind='cancel_producer_with_publication',event=hex(event),reason=reason,fill=fill,status='pass'))
        results = []
        for engine in (None,q):
            state = FullStatusReceiver(program,b'')
            initialize(state,engine,subscribe=False)
            history = state.read(0x10006428,4)
            cursor = state.read(0x1000642c,4)
            assert state.read(cursor,4)==0
            expected = [0]*100
            for i in range(105):
                value = (0xa5a50000+i)&0xffffffff
                invoke(state,0x10010a8c,[value],engine,HOST)
                expected[i%100] = value
            actual = [state.read(history+i*4,4) for i in range(100)]
            assert actual==expected and state.read(cursor,4)==5
            results.append(actual)
        assert results[0]==results[1]
        cases.append(dict(kind='history_wrap',writes=105,capacity=100,status='pass'))
    report = dict(status='pass',total_cases=len(cases),cases=cases,
                  elf_sha256=hashlib.sha256(program.path.read_bytes()).hexdigest(),
                  source_sha256={name:hashlib.sha256((ROOT/'scripts'/name).read_bytes()).hexdigest() for name in
                    ('validate-hp1020-stock-status-publication.py','hp1020_stock_status_publication.py',
                     'hp1020_stock_notifications.py','hp1020_stock_lifecycle_harness.py','hp1020_qemu_task.py')},
                  findings=[
                    'Original StatusMgr constructor registers queue 10 and initializes status state 2, online byte 1, cached event 0x04800100 and source 10; RTOS object creation is an explicit host service.',
                    'Original startup/publication, datastore lock/read/write, ONLINE subscriber dispatch and 100-word event history all execute. Selected lifecycle notices balance counters and free every transient allocation, leaving only the persistent 20-byte ONLINE subscription.',
                    'The numeric preflight event sets ONLINE to zero; the tested matching-source clear event restores ONLINE and state 2. Duplicate clear events leave all original writable globals unchanged. The history ring agrees with a circular-array oracle across wraparound.',
                    'Cancel selectors 1, 3 and 4 are produced with original publication effects included under the recorded cached-status/active-document fixture. These events contain cancel bit 0x02000000 but lack offline bit 0x80000000: cached status/history/datastore 25 change while the online byte and ONLINE subscription stay unchanged.'
                  ],
                  limits='Completed parser/JobMgr inputs still rely on injected FIFO completion. Engine events and source IDs are numeric fixtures, not physical calibration. RTOS object creation, scheduling, synchronization, allocation and queue delivery remain host services. The constructor initializes an empty language-context table, so optional outward status callbacks do not execute. No hardware, USB response or physical recovery is demonstrated.')
    (OUT/'status-publication.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    (OUT/'status-publication.md').write_text('# Original status publication and history\n\n'
        +f'{len(cases)} cases agree between QEMU, the instruction interpreter and explicit state/datastore/history/lifetime oracles.\n\n'
        +'\n'.join('- '+f for f in report['findings'])+'\n\n'+report['limits']+'\n')
    print(f'Original status publication: {len(cases)} independent cases')


if __name__ == '__main__':
    main()
