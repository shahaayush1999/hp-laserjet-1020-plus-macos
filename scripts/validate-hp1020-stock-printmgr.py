#!/usr/bin/env python3
"""Compare original PrintMgr RAM transitions with explicit routing/lifetime oracles."""
import hashlib
import json
import os
from pathlib import Path

from hp1020_stock_printmgr_harness import PrintMgrHarness, HOST
from hp1020_qemu_task import run_task
from hp1020_qemu_ram import QemuRAM
from hp1020_xtensa_call0 import Program

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'analysis/open-firmware-model/stock-execution'


def compare(expected, actual):
    assert actual.sent == expected.sent
    assert actual.snapshots == expected.snapshots
    assert actual.allocations == expected.allocations
    for begin,end in expected.program.write_ranges:
        assert actual.bytes_at(begin,end-begin) == expected.bytes_at(begin,end-begin), hex(begin)
    for ptr, record in expected.allocations.items():
        if not record['freed']:
            assert actual.bytes_at(ptr,record['size']) == expected.bytes_at(ptr,record['size'])


def subscriptions(state):
    result = []
    for key in (1,24):
        ptr = state.read(state.read(0x10006490,4)+key*4,4)
        assert state.allocations[ptr] == dict(size=20,kind=1,freed=False)
        words = [state.read(ptr+i*4,4) for i in range(5)]
        assert words == [key,1,0,ptr+12,ptr+12]
        result.append(dict(entry=key,queue=words[1],callback=words[2]))
    return result


def main():
    program = Program(ROOT/'analysis/sihp1020.elf',os.environ.get('XTENSA_PREFIX','/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf'))
    cases = []
    with QemuRAM() as q:
        for fill in (0,0xcc):
            for reason in (1,2,3,4):
                for media in range(4):
                    # Alternate empty/populated queues across the matrix. The
                    # work buffers are sentinels and must not be read or freed.
                    pending,active = (3,2) if (reason+media)%2 else (0,0)
                    args = dict(fill=fill,media=media,pending=pending,active=active)
                    messages = [[15,reason,0,0],[37,0,0,0],[37,0,0,0]]
                    expected = PrintMgrHarness(program,messages,**args)
                    expected.run()
                    actual = PrintMgrHarness(program,messages,**args)
                    run_task(actual,q,HOST)
                    compare(expected,actual)
                    assert [s['state'] for s in actual.snapshots] == [0,1,2,0]
                    assert [s['nodes_freed'] for s in actual.snapshots] == [0,0,pending+active,pending+active]
                    assert [(m['queue'],m['words'][0]) for m in actual.sent] == [(0,24),(0,15),(8,15),(3,37),(0,24)]
                    assert actual.sent[1]['words'][1] == reason
                    assert all(actual.allocations[w]['freed'] is False and actual.bytes_at(w,0x94) == bytes([fill])*0x94 for w in actual.works)
                    assert all(actual.allocations[n]['freed'] for n in actual.nodes)
                    cases.append(dict(kind='cancel',reason=reason,media=media,fill=fill,pending=pending,active=active,
                                      subscriptions=subscriptions(actual),instructions=actual.qemu_steps,status='pass'))
        for event in (0xe6100a01,0xfe001401,0x02000800,0x80000000):
            for fill in (0,0xcc):
                messages = [[23,event,0,0]]
                expected = PrintMgrHarness(program,messages,fill=fill)
                expected.run()
                actual = PrintMgrHarness(program,messages,fill=fill)
                run_task(actual,q,HOST)
                compare(expected,actual)
                assert any(m['queue']==10 and m['words'][:3]==[44,event,1] for m in actual.sent)
                assert 0x1000f4c2 in actual.visited and 0x1000f538 in actual.visited
                cases.append(dict(kind='status_event',event=hex(event),fill=fill,instructions=actual.qemu_steps,status='pass'))
    report = dict(status='pass',total_cases=len(cases),cases=cases,
                  elf_sha256=hashlib.sha256(program.path.read_bytes()).hexdigest(),
                  source_sha256={name:hashlib.sha256((ROOT/'scripts'/name).read_bytes()).hexdigest() for name in
                                 ('validate-hp1020-stock-printmgr.py','hp1020_stock_printmgr_harness.py','hp1020_qemu_task.py','hp1020_qemu_ram.py','hp1020_qemu_stock_parser.py')},
                  findings=[
                      'Original PrintMgr startup creates 20-byte circular subscriber records for entries 1 and 24, queue 1, null callback.',
                      'Cancel message 15 enters state 1 and forwards the reason to engine queue 0. First injected acknowledgement 37 drains both PrintMgr node lists, enters state 2 and sends stop 15 to Video queue 8. Second acknowledgement returns state 0 and forwards 37 to JobMgr queue 3.',
                      'PrintMgr frees only its 16-byte list nodes in these stop paths; referenced 148-byte work allocations remain byte-identical and owned elsewhere.',
                      'Engine/video event 23 is consumed by PrintMgr and selected numeric events produce StatusMgr queue 10 message 44. The old default-engine-consumer interpretation was wrong.'
                  ],
                  limits='Both stop acknowledgements are injected queue inputs. Engine stop, Video reset, real queue scheduling and work-buffer retirement are outside this test. Empty/seeded RAM list and media-state fixtures are explicit. RTOS locks/startup and allocator share host services across engines. QEMU independently executes the selected CPU instructions, original register-window vectors and critical-mask helpers; it is not the printer CPU or hardware proof.')
    (OUT/'printmgr.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    (OUT/'printmgr.md').write_text('# Original PrintMgr execution\n\n'
        +f"{len(cases)} cases agree between the instruction interpreter, QEMU and explicit routing/ownership expectations.\n\n"
        +'\n'.join('- '+x for x in report['findings'])+'\n\n'+report['limits']+'\n')
    print(f'Original PrintMgr: {len(cases)} independent QEMU/interpreter cases')


if __name__ == '__main__':
    main()
