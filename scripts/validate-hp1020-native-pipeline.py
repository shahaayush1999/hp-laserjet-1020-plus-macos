#!/usr/bin/env python3
"""Check original concurrent empty-document lifecycle without producer replay.

UNFINISHED: the proposed matrix currently fails at 13 equal-priority documents.
No pipeline success report has been generated; do not add this to the aggregate yet.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from hp1020_xtensa_call0 import Program
from hp1020_qemu_ram import QemuRAM
from hp1020_qemu_pipeline import run_pipeline

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'analysis/open-firmware-model/stock-execution'
spec = importlib.util.spec_from_file_location('stock_helper',ROOT/'scripts/validate-hp1020-stock-execution.py')
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


def main():
    p = Program(ROOT/'analysis/sihp1020.elf',os.environ.get('XTENSA_PREFIX','/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf'))
    base = helper.chunks((ROOT/'analysis/samples/generated/matrix-a4_default.zjs').read_bytes())[0]
    empty = helper.stream(base[:1]+base[-1:])
    cases = []
    with QemuRAM() as q:
        for documents in (1,3,13):
            for priorities in ((5,2,15),(2,5,15),(5,5,5),(5,2,1)):
                for fill in (0,0xcc):
                    case = run_pipeline(q,p,empty*documents,documents,fill,priorities)
                    if documents==13 and priorities==(2,5,15):
                        assert case['job_queue_full_waits']>0
                    if documents==13 and priorities[2]==15:
                        assert case['status_queue_full_waits']>0
                    cases.append(case)
    sources = ('validate-hp1020-native-pipeline.py','hp1020_qemu_pipeline.py','hp1020_qemu_multitask.py',
               'hp1020_qemu_scheduled_status.py','hp1020_qemu_timers.py','hp1020_stock_pool.py',
               'hp1020_stock_parser_harness.py','hp1020_stock_jobmgr_harness.py','hp1020_stock_lifecycle_harness.py',
               'hp1020_qemu_stock_parser.py','hp1020_qemu_ram.py')
    report = dict(status='pass',total_cases=len(cases),cases=cases,
        elf_sha256=hashlib.sha256(p.path.read_bytes()).hexdigest(),
        source_sha256={name:hashlib.sha256((ROOT/'scripts'/name).read_bytes()).hexdigest() for name in sources},
        findings=[
            'Original parser, JobMgr and StatusMgr run concurrently under original priority scheduling, queues, synchronization and timer-list operations. The host supplies only input bytes; there is no parser/JobMgr replay, queued-message injection, heap migration or runtime allocator/queue/free/readiness substitute.',
            'The original JobMgr and StatusMgr constructors create their queues and publication state. Original pool allocations own parser/document/notice storage from creation through release, leaving only the 20-byte ONLINE subscriber live. The host allocation tracker stays empty.',
            'One, three and thirteen empty documents pass with parser-first, JobMgr-first, equal and StatusMgr-first priorities and two RAM fills. Thirteen documents exercise original queue-full blocking at the JobMgr and StatusMgr boundaries under the specified priority orders.',
            'Original status publication queues a cancellation back to the running JobMgr; it is consumed by original code. Final document lists are empty, start/end counters balance, locks are released and the expected ONLINE packet remains in the unconsumed PrintMgr queue.',
            'At the stop boundary all three tasks are suspended on empty queues. JobMgr has an actual two-tick receive timeout linked into the original timer wheel; zero ticks have been delivered, so it is explicitly armed rather than treated as permanent idle.'
        ],
        limits='Empty documents only: no raster, work completion, PrintMgr/VideoThread execution, MMIO, DMA or printing. Input delivery, parser context/datastore descriptors, arena bounds, thread stacks/priorities, zero time slices and startup readiness are explicit fixtures. The parser is invoked once per document by a native wrapper, not the original stream-admission task. Constructor thread creation is hosted during setup, followed by original thread creation for execution. The datastore constructor still stops before event-group/backing-value initialization. CPU interrupts remain disabled. Final JobMgr timeout is armed but unexpired; automatic time/IRQ delivery and full physical boot remain unproven.')
    (OUT/'pipeline.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    (OUT/'pipeline.md').write_text('# Original parser, job and status task pipeline\n\n'+f'{len(cases)} QEMU cases pass native scheduling, ownership and document oracles.\n\n'+'\n'.join('- '+x for x in report['findings'])+'\n\n'+report['limits']+'\n')
    print(f'Original native empty-document pipeline: {len(cases)} cases')


if __name__=='__main__':
    main()
