#!/usr/bin/env python3
"""Independent stop-prefix and post-reset RAM-tail checks, never hardware execution."""
import hashlib
import json
import os
from pathlib import Path

from hp1020_stock_stop import EngineStop, VideoStopTail, ENGINE_HOST, VIDEO_HOST, MESSAGE
from hp1020_stock_printmgr_harness import PrintMgrHarness, HOST as PRINT_HOST
from hp1020_qemu_task import run_task
from hp1020_qemu_ram import QemuRAM
from hp1020_xtensa_call0 import Program

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'analysis/open-firmware-model/stock-execution'


def video_qemu(state,q):
    return run_task(state,q,VIDEO_HOST,args=[1],prologue=0x10013d4c,stack_words=((8,0),(12,0)))


def main():
    program = Program(ROOT/'analysis/sihp1020.elf',os.environ.get('XTENSA_PREFIX','/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf'))
    cases = []
    with QemuRAM() as q:
        for fill in (0,0x5a):
            for reason in (1,2,3,4):
                for active,deferred in ((0,0),(0x22000100,0),(0,0x22000200),(0x22000100,0x22000200)):
                    a = EngineStop(program,reason,fill,active,deferred)
                    b = EngineStop(program,reason,fill,active,deferred)
                    expected = bytearray(a.bytes_at(a.state,112))
                    expected[40] = 1
                    expected[104:112] = bytes(8)
                    a.run([MESSAGE])
                    run_task(b,q,ENGINE_HOST,args=[MESSAGE])
                    assert a.sent == b.sent == [dict(queue=1,words=[37,0,0,0])]
                    assert a.stop_before_hardware and b.stop_before_hardware
                    assert a.bytes_at(a.state,112) == b.bytes_at(b.state,112) == expected
                    assert 0x1001619e in b.visited and 0x100161a1 in b.visited
                    assert 0x10016098 not in b.visited
                    cases.append(dict(kind='engine_stop_prefix',reason=reason,fill=fill,active=bool(active),deferred=bool(deferred),status='pass'))
        for sign in (0,1):
            patterns = ((),(3,),(1,2,0,1,3)) if not sign else ((),(1,),(3,))
            for chains in patterns:
                for refs in (0,1,2):
                    for cursor in (0,16,32):
                        a = VideoStopTail(program,sign,refs,cursor,chains)
                        b = VideoStopTail(program,sign,refs,cursor,chains)
                        expected = bytearray(a.bytes_at(MESSAGE,4096))
                        for _,payload in a.nodes:
                            off = payload-MESSAGE
                            expected[off+78:off+80] = max(0,refs-1).to_bytes(2,'big')
                            if sign and refs and cursor:
                                expected[off+84:off+88] = (cursor-16).to_bytes(4,'big')
                        a.run([1])
                        video_qemu(b,q)
                        assert a.bytes_at(MESSAGE,4096) == b.bytes_at(MESSAGE,4096) == expected
                        assert a.sent == b.sent == [dict(queue=1,words=[37,0,0,0])]
                        events = [[a.read(0x100062dc,4),8,0]]*(len(a.nodes) if sign and refs else 0)
                        assert a.events == b.events == events
                        for offset in (0x60,0x64,0x68,0x6c,0xa0,0xa4,0xa8,0xac,0xb0,0xb4):
                            assert a.read(a.video+offset,4) == b.read(b.video+offset,4) == 0
                        assert a.bytes_at(a.video,256) == b.bytes_at(b.video,256)
                        cases.append(dict(kind='video_post_reset_tail',sign=sign,chains=chains,refs=refs,cursor=cursor,status='pass'))
        for reason in (1,2,3,4):
            engine = EngineStop(program,reason)
            run_task(engine,q,ENGINE_HOST,args=[MESSAGE])
            video = VideoStopTail(program,0,1,16,(3,))
            video_qemu(video,q)
            # Explicit queue relay; engine stop and Video reset are not executed.
            manager = PrintMgrHarness(program,[[15,reason,0,0],engine.sent[0]['words'],video.sent[0]['words']],pending=2,active=1)
            run_task(manager,q,PRINT_HOST)
            assert [s['state'] for s in manager.snapshots] == [0,1,2,0]
            assert sum(m['queue']==3 and m['words'][0]==37 for m in manager.sent) == 1
            assert all(manager.allocations[n]['freed'] for n in manager.nodes)
            cases.append(dict(kind='acknowledgement_packet_relay',reason=reason,status='pass'))
        blocked = VideoStopTail(program,0,1,16)
        blocked.pc = 0x10013d4c
        blocked.code_ranges += [(0x10013d4c,0x10013d4f)]
        try:
            run_task(blocked,q,VIDEO_HOST,args=[1])
        except ValueError as error:
            assert 'left selected code: 0x10013d4f' in str(error)
            gate = dict(status='blocked',pc='0x10013d4f',reason='Omitted reset prefix cannot execute without an explicit fragment-entry precondition.')
        else:
            raise AssertionError('unselected video reset prefix executed')
        for independent in (False,True):
            partial = EngineStop(program)
            partial.code_ranges = [(0x10016164,0x1001619f)]  # Ends inside a 3-byte CALL8.
            try:
                if independent:
                    run_task(partial,q,ENGINE_HOST,args=[MESSAGE])
                else:
                    partial.run([MESSAGE])
            except ValueError as error:
                assert '0x1001619e' in str(error)
                assert not partial.sent and not partial.stop_before_hardware
            else:
                raise AssertionError('instruction crossing selected-code end executed')
        span_gate = dict(status='blocked',pc='0x1001619e',end='0x1001619f')
    report = dict(status='pass',total_cases=len(cases),cases=cases,prefix_gate=gate,instruction_span_gate=span_gate,
                  elf_sha256=hashlib.sha256(program.path.read_bytes()).hexdigest(),
                  source_sha256={name:hashlib.sha256((ROOT/'scripts'/name).read_bytes()).hexdigest() for name in
                    ('validate-hp1020-stock-stop.py','hp1020_stock_stop.py','hp1020_stock_printmgr_harness.py',
                     'hp1020_qemu_task.py','hp1020_qemu_ram.py','hp1020_qemu_stock_parser.py')},
                  findings=[
                    'Engine message 15 clears the active/deferred work slots, sets state byte +0x28 and queues acknowledgement 37 to PrintMgr before calling hardware stop at 0x10016098. This acknowledgement cannot by itself establish completed hardware stopping.',
                    'After the explicitly omitted video reset/wait prefix, the original RAM tail decrements nonzero raster references and clears owned list/state slots. The sign-selected linked-list branch additionally subtracts 16 from nonzero cursors and emits release events; the five-slot branch preserves those cursors.',
                    'Video reset selector 1 emits acknowledgement 37 to PrintMgr. Relaying the selected original engine/video packets through original PrintMgr reproduces its two-stage handshake and final JobMgr acknowledgement.'
                  ],
                  limits='The engine hardware-stop call is a terminal boundary. The entire Video reset/wait prefix is omitted: QEMU executes its original ENTRY, then enters 0x10013e00 with explicitly seeded stack words and video-owned lists. These tests establish conditional RAM bookkeeping and packet content only. They do not prove that reset reaches the tail, which raster lists are owned at cancellation time, DMA quiescence, interrupt scheduling, safe physical stop or recovery.')
    (OUT/'stop.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    (OUT/'stop.md').write_text('# Original stop acknowledgements and post-reset RAM tail\n\n'
        +f'{len(cases)} cases agree between QEMU, the instruction interpreter and explicit packet/field oracles.\n\n'
        +'\n'.join('- '+f for f in report['findings'])+'\n\n'+report['limits']+'\n')
    print(f'Original stop boundaries: {len(cases)} cases, omitted prefix remains blocked')


if __name__ == '__main__':
    main()
