#!/usr/bin/env python3
"""Native software page lifecycles with explicitly supplied FIFO consumption."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from hp1020_xtensa_call0 import Program,Machine
from hp1020_qemu_ram import QemuRAM
from hp1020_qemu_page_pipeline import run_pages

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'analysis/open-firmware-model/stock-execution'
spec = importlib.util.spec_from_file_location('stock_helper',ROOT/'scripts/validate-hp1020-stock-execution.py')
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


def main():
    program = Program(ROOT/'analysis/sihp1020.elf',os.environ.get('XTENSA_PREFIX','/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf'))
    memory = Machine(program)
    expected = {
        0x1000f0ba: ('l32i',(6,5,12),'265203'),
        0x1000f0d4: ('l16ui',(8,6,78),'286127'),
        0x1000f0f6: ('l32i',(10,6,84),'2a6215'),
        0x1000f0fc: ('call8',(0x10013408,),'5810c2'),
        0x1000f0ff: ('or',(10,5,5),'055a02'),
        0x1000f108: ('call8',(0x10013408,),'5810bf'),
        0x10014329: ('l16ui',(8,9,78),'289127'),
        0x10014330: ('s16i',(8,9,78),'289527'),
        0x10014338: ('call8',(0x10017dac,),'580e9c'),
    }
    for pc,(op,args,raw) in expected.items():
        assert program.instruction(pc)==(op,args,bytes.fromhex(raw))
        span,offset=memory.span(pc,len(bytes.fromhex(raw)),execute=True)
        assert span[offset:offset+len(bytes.fromhex(raw))]==bytes.fromhex(raw)
    span,offset=memory.span(0x1000f068,0x3e,execute=True)
    cleanup_bytes=bytes(span[offset:offset+0x3e])
    assert hashlib.sha256(cleanup_bytes).hexdigest()=='7fd9c5680522f195bddb35c491bba94e87137e000f4cd260b4e26effcb05c009'
    pc=0x1000f068
    while pc<0x1000f0a6:
        op,args,raw=program.instruction(pc)
        assert op in ('entry','l32i.n','l32i','bnez.n','retw.n','bbci','addi','movi','or','call8','l16ui','s16i')
        if op=='call8':
            assert args==(0x1000f0a8,)
        pc+=len(raw)
    assert pc==0x1000f0a6
    base = helper.chunks((ROOT/'analysis/samples/generated/matrix-a4_default.zjs').read_bytes())[0]
    cases=[]
    with QemuRAM() as q:
        for documents,pages,data in (
            (1,1,helper.stream(base)),
            (1,3,helper.stream(base[:1]+base[1:6]*3+base[-1:])),
            (3,3,helper.stream(base)*3)):
            for fill in (0,0xcc):
                for ticks,consume_event in ((0,False),(2,False),(2,True)):
                    case=run_pages(q,program,data,documents,pages,fill,ticks,consume_event)
                    assert bool(case['timed_cleanup_calls'])==(ticks==2 and not consume_event)
                    cases.append(case)
                    print(f'native pages: documents={documents} pages={pages} fill={fill} ticks={ticks} consume_event={consume_event}: pass',flush=True)
    sources = ('validate-hp1020-native-pages.py','hp1020_qemu_page_pipeline.py','hp1020_qemu_retire.py',
        'hp1020_qemu_pipeline.py','hp1020_qemu_multitask.py','hp1020_qemu_scheduled_status.py',
        'hp1020_qemu_timers.py','hp1020_stock_pool.py','hp1020_stock_parser_harness.py',
        'hp1020_stock_jobmgr_harness.py','hp1020_stock_lifecycle_harness.py',
        'hp1020_qemu_stock_parser.py','hp1020_qemu_ram.py','validate-hp1020-stock-execution.py')
    findings = [
        'Eighteen native cases complete one page, three pages in one document, and three one-page documents, under both RAM fills. Original parser, JobMgr and StatusMgr use original allocation, queues, locks and scheduling. Runtime host services supply input bytes only.',
        'A synthetic fourth task waits until parsing finishes, consumes queue-1 work in FIFO order, supplies successful consumption to the bounded original retirement tail, and sends message 17 through the original JobMgr queue. Reference fields change from one to zero through original stores; original event-set calls execute.',
        'Original completion processing restores credits, updates page/document counters and releases all pool allocations apart from the persistent 20-byte ONLINE subscriber. All four tasks finish waiting on empty queues; JobMgr has a two-tick receive timeout armed. Zero-tick controls and explicitly delivered two-tick intervals are separate configurations.',
        'Two explicit ticks after retirement allow original JobMgr to call the byte-audited RAM cleanup helper and free retired nodes before supplied message 17. Consuming event bit 8 first through original event-get prevents that early cleanup despite the same two ticks. All three modes retain final FIFO ownership and reclamation.',
        'The first draft did not assemble because beqi cannot encode immediate 11. Replacing it with a register comparison allowed execution. The first executed draft then failed an incorrect descriptor-free oracle: stock cleanup frees the containing node (node+12 points to its embedded descriptor at node+16), not that descriptor address. Original bytes and pool partition evidence establish the correction.'
    ]
    limits = ('Software execution only. FIFO consumption, completion success, task priorities, parser wrapper, '
        'initial readiness and descriptor backing values are fixtures. No PrintMgr, engine, DMA, IRQ prefix, '
        'custom raster instructions, automatic interrupts, physical printing or recovery executes. '
        'The retirement next-transfer path remains excluded. There is no claim that event bit 8 wakes '
        'JobMgr directly: explicit ticks expire its queue receive, after which it polls the event and cleans RAM. Wall-clock timing remains unproven.')
    report=dict(status='pass',total_cases=len(cases),completed_lifecycles=len(cases),cases=cases,
        timed_cleanup_helper=dict(address='0x1000f068',bytes=cleanup_bytes.hex(),sha256=hashlib.sha256(cleanup_bytes).hexdigest()),
        instruction_audit={hex(pc):dict(op=op,args=args,bytes=raw) for pc,(op,args,raw) in expected.items()},
        elf_sha256=hashlib.sha256(program.path.read_bytes()).hexdigest(),
        source_sha256={name:hashlib.sha256((ROOT/'scripts'/name).read_bytes()).hexdigest() for name in sources},
        findings=findings,limits=limits)
    (OUT/'pages.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    (OUT/'pages.md').write_text('# Native page pipeline with supplied consumption\n\n'
        +f'{len(cases)} completed software lifecycles. No physical printing evidence.\n\n'
        +'\n'.join('- '+x for x in findings)+'\n\n'+limits+'\n')
    print(f'Original native pages: {len(cases)} completed lifecycles')


if __name__=='__main__':
    main()
