#!/usr/bin/env python3
"""Reproduce conditional JobMgr cancellation findings with original stop-tail effects."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path

from hp1020_stock_cancellation import Cancellation, StatusCancelRequest, StatusCancelRelay, REQUEST_HOST, RELAY_HOST
from hp1020_stock_printmgr_harness import PrintMgrHarness, HOST as PRINT_HOST
from hp1020_stock_parser_harness import CONTEXT
from hp1020_qemu_lifecycle import QemuLifecycle
from hp1020_qemu_task import run_task
from hp1020_qemu_ram import QemuRAM
from hp1020_xtensa_call0 import Program, STACK, STACK_SIZE

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'analysis/open-firmware-model/stock-execution'
spec = importlib.util.spec_from_file_location('stock_helper',ROOT/'scripts/validate-hp1020-stock-execution.py')
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class QemuCancellation(Cancellation,QemuLifecycle):
    pass


def nonstack_references(state, target):
    references = []
    word = target.to_bytes(4,'big')
    for begin,end in state.write_ranges:
        if STACK <= begin < STACK+STACK_SIZE:
            continue
        data = state.bytes_at(begin,end-begin)
        for offset in range(0,len(data)-3,4):
            if data[offset:offset+4] == word:
                references.append(hex(begin+offset))
    return references


def main():
    program = Program(ROOT/'analysis/sihp1020.elf',os.environ.get('XTENSA_PREFIX','/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf'))
    base = helper.chunks((ROOT/'analysis/samples/generated/matrix-a4_default.zjs').read_bytes())[0]
    cases = []
    producers = []
    with QemuRAM() as q:
        packets = []
        for engine in (None,q):
            media = PrintMgrHarness(program,[],media=3)
            media.pc = 0x1000fcb0
            ptr = CONTEXT+0x100
            for i,value in enumerate((50,0,0,0)):
                media.write(ptr+i*4,4,value)
            media.run([ptr]) if engine is None else run_task(media,q,PRINT_HOST,args=[ptr])
            assert media.sent == [dict(queue=10,words=[15,2,0,0])]
            relay = StatusCancelRelay(program,media.sent[0]['words'])
            relay.run() if engine is None else run_task(relay,q,RELAY_HOST)
            assert relay.sent == [dict(queue=3,words=[15,2,0,0])]
            request = StatusCancelRequest(program)
            request.run([0x02000800,10]) if engine is None else run_task(request,q,REQUEST_HOST,args=[0x02000800,10])
            assert request.sent == [dict(queue=3,words=[15,4,0,0])]
            packets.append((relay.sent,request.sent))
        assert packets[0] == packets[1]
        producers = [dict(reason=2,trigger='PrintMgr media state 3, message 50 word 1 zero, followed by StatusMgr active-document relay',status='pass'),
                     dict(reason=4,trigger='Status update 0x02000800 with state 2, prior event 0x100 and one active document; publication callbacks omitted',status='pass')]
        for pieces in (1,5):
            kind,payload,_,_ = base[3]
            bids = [(kind,payload[len(payload)*i//pieces:len(payload)*(i+1)//pieces],0,0) for i in range(pieces)]
            data = helper.stream(base[:3]+bids+base[4:])
            for reason in (2,4):
                for timing in ('before_document_end','after_document'):
                    for fill in (0,0xcc):
                        for flags in (None,(1,0),(0,1)):
                            observations = []
                            for factory in (Cancellation,QemuCancellation):
                                state = factory(program,data,reason=reason,timing=timing,flags=flags,fill=fill,credits=1)
                                try:
                                    state.replay() if factory is Cancellation else state.replay_qemu(q)
                                except ValueError as error:
                                    assert reason==4 and timing=='after_document'
                                    assert state.pc==0x1000eb6a and str(error)=='unmapped RAM 0xc+4'
                                    observations.append(dict(outcome='invalid_read',pc=hex(state.pc),error=str(error)))
                                else:
                                    assert not(reason==4 and timing=='after_document')
                                    live = {ptr:a for ptr,a in state.allocations.items() if not a['freed']}
                                    expected_sizes = [120] if reason==2 else [16,80]
                                    assert sorted(a['size'] for a in live.values()) == expected_sizes
                                    retained = next(ptr for ptr,a in live.items() if a['size'] in (80,120))
                                    references = nonstack_references(state,retained)
                                    assert references == []
                                    assert state.delivered==len(state.pending)
                                    doc_list = state.read(0x100062e4,4)
                                    assert state.read(doc_list,4)==state.read(doc_list+4,4)==0
                                    observations.append(dict(outcome='retained_allocation',sizes=expected_sizes,nonstack_word_references=references))
                                assert state.original_flags == [0,0]
                            assert observations[0] == observations[1]
                            cases.append(dict(reason=reason,timing=timing,fill=fill,flag_override=flags,raster_chunks=pieces,status='pass',**observations[0]))
    report = dict(status='pass',total_cases=len(cases),cases=cases,producers=producers,
                  elf_sha256=hashlib.sha256(program.path.read_bytes()).hexdigest(),
                  source_sha256={name:hashlib.sha256((ROOT/'scripts'/name).read_bytes()).hexdigest() for name in
                    ('validate-hp1020-stock-cancellation.py','hp1020_stock_cancellation.py','hp1020_stock_stop.py',
                     'hp1020_qemu_lifecycle.py','hp1020_qemu_task.py','hp1020_stock_lifecycle_harness.py','hp1020_stock_jobmgr_harness.py')},
                  findings=[
                    'Original producers can send cancel reasons 2 and 4 to JobMgr under the recorded media/status fixtures; these selectors were not invented solely to trigger cleanup branches.',
                    'Reason 2 leaves a 120-byte document allocation at quiescence after either tested cancellation ordering. Reason 4 before END_DOC leaves an 80-byte child allocation plus its 16-byte completion notice. The retained document/child has no aligned pointer reference in tested non-stack writable RAM; this is bounded reachability evidence, not proof against arbitrary encoded references.',
                    'Reason 4 after END_DOC attempts a read through null at 0x1000eb6a. The same fixture avoids that invalid read when the acknowledgement is processed before END_DOC. Both CPU engines agree across fills, raster splits and overrides of the two work-release flags.',
                  ],
                  limits='These are conditional stock-software findings, not observed printer faults. The single scheduled work is assumed to own the seeded video raster chain, reset is assumed to reach the original RAM tail, and the tested coordinator handshake is summarized as a queue relay. JobMgr executes independently in QEMU; its host stop boundary runs the tail through the separately QEMU-checked interpreter component. Engine stop, DMA ownership, interrupts, physical fault meaning and actual cancellation timing remain unverified. Status publication callbacks are omitted in the producer fixtures.')
    (OUT/'cancellation.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    (OUT/'cancellation.md').write_text('# Conditional original cancellation findings\n\n'
        +f'{len(cases)} fixture cases and two original producer paths agree across both execution engines.\n\n'
        +'\n'.join('- '+f for f in report['findings'])+'\n\n'+report['limits']+'\n')
    print(f'Original cancellation: {len(cases)} conditional outcomes, two producer paths')


if __name__ == '__main__':
    main()
