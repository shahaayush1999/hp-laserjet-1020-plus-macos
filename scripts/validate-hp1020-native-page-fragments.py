#!/usr/bin/env python3
"""Focused native split-raster cases using the validated page runtime unchanged."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from hp1020_xtensa_call0 import Program
from hp1020_qemu_ram import QemuRAM
from hp1020_qemu_page_pipeline import run_pages

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'analysis/open-firmware-model/stock-execution'
spec=importlib.util.spec_from_file_location('helper',ROOT/'scripts/validate-hp1020-stock-execution.py')
helper=importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


def main():
    # Reuse the byte-audited runtime only when every source and original binary
    # still matches the aggregate's executed page report. Do not relabel hashes.
    baseline=json.loads((OUT/'pages.json').read_text())
    assert baseline['status']=='pass' and baseline['total_cases']==18
    for name,digest in baseline['source_sha256'].items():
        assert hashlib.sha256((ROOT/'scripts'/name).read_bytes()).hexdigest()==digest
    program=Program(ROOT/'analysis/sihp1020.elf',os.environ.get('XTENSA_PREFIX','/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf'))
    assert hashlib.sha256(program.path.read_bytes()).hexdigest()==baseline['elf_sha256']
    source_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    base=helper.chunks((ROOT/'analysis/samples/generated/matrix-a4_default.zjs').read_bytes())[0]
    cases=[]
    with QemuRAM() as q:
        for pieces in (6,13,64):
            kind,payload,_,_=base[3]
            cuts=[len(payload)*i//pieces for i in range(pieces+1)]
            chunks=[(kind,payload[cuts[i]:cuts[i+1]],0,0) for i in range(pieces)]
            assert b''.join(c[1] for c in chunks)==payload
            data=helper.stream(base[:3]+chunks+base[4:])
            for fill in (0,0xcc):
                for ticks,consume_event in ((0,False),(2,False),(2,True)):
                    case=run_pages(q,program,data,1,1,fill,ticks,consume_event,instruction_budget=250000 if pieces==64 else 200000)
                    assert len(case['retired_nodes'])==1 and len(case['retired_nodes'][0][1])==pieces
                    assert len(case['reference_decrements'])==len(case['event_calls'])==pieces
                    assert bool(case['timed_cleanup_calls'])==(ticks==2 and not consume_event)
                    case['raster_chunks']=pieces
                    cases.append(case)
                    print(f'Native raster chunks={pieces}, fill={fill}, ticks={ticks}, consume_event={consume_event}: pass',flush=True)
    assert len(cases)==18
    assert source_hash==hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    sources=dict(baseline['source_sha256'])
    sources[Path(__file__).name]=source_hash
    findings=[
        'Eighteen additional focused software lifecycles pass with six, thirteen and 64 raster chunks in one page, both RAM fills, and zero-tick, two-tick and consumed-event controls. The concatenated raster payload is unchanged by chunking.',
        'Every chunk creates a distinct original linked node. The native retirement wrapper supplies consumption once per node; original reference stores reach zero and original event-set runs once per node. No five-slot hardware batching or real DMA is inferred.',
        'With two explicit ticks, original JobMgr cleans every retired node before supplied completion. Consuming the event first prevents early cleanup despite those ticks. All controls retain complete final reclamation apart from the ONLINE subscriber, restored credits, page/document counters and empty waiting queues.',
        'Six- and thirteen-chunk cases keep the 200,000-instruction budget. The first 64-chunk case stopped at that cap during StatusMgr notification bookkeeping after all references were retired and completion was supplied; its raw capture is preserved separately, not counted as a lifecycle. The 64-chunk matrix uses an explicit 250,000-instruction budget. The byte-audited page runtime is unchanged from the aggregate baseline; the larger fixtures retain all memory, instruction and excluded-next-transfer gates.'
    ]
    report=dict(status='pass',total_cases=18,completed_lifecycles=18,cases=cases,
        elf_sha256=baseline['elf_sha256'],source_sha256=sources,
        budget_stop_evidence='analysis/open-firmware-model/stock-execution/page-fragment-limit.json',
        baseline_page_report_sha256=hashlib.sha256((OUT/'pages.json').read_bytes()).hexdigest(),
        findings=findings,limits=baseline['limits'])
    (OUT/'page-fragments.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    (OUT/'page-fragments.md').write_text('# Native pages with split raster data\n\n'
        +'18 completed software lifecycles, additional to the aggregate page matrix.\n\n'
        +'\n'.join('- '+x for x in findings)+'\n\n'+baseline['limits']+'\n')
    print('Original native split-raster pages: 18 completed lifecycles')


if __name__=='__main__':
    main()
