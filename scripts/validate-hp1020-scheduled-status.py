#!/usr/bin/env python3
"""Original StatusMgr under original queue blocking, wakeup and priority scheduling."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from hp1020_qemu_scheduled_status import run_scheduled_status
from hp1020_qemu_ram import QemuRAM
from hp1020_xtensa_call0 import Program

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'analysis/open-firmware-model/stock-execution'
spec = importlib.util.spec_from_file_location('stock_helper',ROOT/'scripts/validate-hp1020-stock-execution.py')
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


def main():
    p = Program(ROOT/'analysis/sihp1020.elf',os.environ.get('XTENSA_PREFIX','/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf'))
    base = helper.chunks((ROOT/'analysis/samples/generated/matrix-a4_default.zjs').read_bytes())[0]
    normal = helper.stream(base)
    cases = []
    with QemuRAM() as q:
        for name,data,documents in [('one_document',normal,1),('three_documents',normal*3,3),
                ('thirteen_documents',normal*13,13),
                ('three_pages',helper.stream(base[:1]+base[1:6]*3+base[-1:]),1),
                ('empty',helper.stream(base[:1]+base[-1:]),1)]:
            for priorities in ((1,2),(2,1),(7,7)):
                for fill in (0,0xcc):
                    cases.append(dict(name=name,**run_scheduled_status(q,p,data,documents,fill,priorities)))
    sources = ('validate-hp1020-scheduled-status.py','hp1020_qemu_scheduled_status.py',
               'hp1020_qemu_multitask.py','hp1020_qemu_scheduler.py','hp1020_stock_status_queue.py',
               'hp1020_stock_status_publication.py','hp1020_stock_notifications.py',
               'hp1020_stock_lifecycle_harness.py','hp1020_qemu_task.py','hp1020_qemu_ram.py',
               'hp1020_qemu_stock_parser.py','hp1020_stock_pool.py')
    report = dict(status='pass',total_cases=len(cases),cases=cases,
        elf_sha256=hashlib.sha256(p.path.read_bytes()).hexdigest(),
        source_sha256={name:hashlib.sha256((ROOT/'scripts'/name).read_bytes()).hexdigest() for name in sources},
        findings=[
            'The original StatusMgr task runs under original thread creation, priority selection, ready/suspension lists, queue sends/receives and context switching. A synthetic producer submits original completed JobMgr notice words; the receiver is no longer fed through a host queue substitute or manual task switch.',
            'Normal, repeated, multi-page and empty completed streams balance start/end counters and release every migrated transient notice through original free. Only the persistent 20-byte ONLINE subscriber remains; actual queue buffers contain the expected ONLINE and cancellation outputs.',
            'Both priority directions and equal priority agree. Thirteen documents create 26 notices, exceeding the original 25-message StatusMgr capacity; the higher-priority producer demonstrably blocks on the full queue, then resumes through original wakeup code.',
            'At the final idle boundary both tasks are truly suspended on empty queues and preemption bookkeeping balances. Idle is accepted only after complete notice processing, ownership and output checks.',
            'The original allocator/free and its additional semaphore execute on an explicitly seeded arena. END_DOC payload bytes are copied unchanged from replay into original allocations, relocating only their defined notice pointer. Partition, free-byte and actual free-call oracles leave only the 20-byte subscriber allocated.',
            'Original startup event-group creation, set and get replace the readiness service. When StatusMgr runs first it suspends on the unset readiness flag; the native producer sets flag 4 through original code and wakes it. After native scheduling starts, there are no whole-function host services.',
            'The original datastore constructor prefix creates 38 binary semaphores; the later datastore mutex creation is invoked separately with its observed arguments. Original StatusMgr construction creates its own mutex. All original lock/unlock operations execute, ending with semaphore counts restored and both mutexes unowned by count with no waiters.'
        ],
        limits='Notice contents come from prior parser/JobMgr replay with injected FIFO page completion; those tasks do not run concurrently in this experiment. Initial parser/JobMgr replay still uses a host allocator and tracked ownership. Its remaining notice storage is explicitly migrated into a separately seeded original pool; this is not original heap boot discovery or an end-to-end producer allocation proof. Constructor thread creation remains hosted during setup; runtime allocation/free/readiness services are original code. Pool partition and free-call oracles check ownership, while the whole arena remains mapped, including freed payload bytes. The native producer deliberately supplies startup readiness; it does not establish actual boot readiness timing. The datastore constructor stops before event-group/backing-value initialization, retaining the existing descriptor fixture. Lock contention is absent from this two-task workload. Optional outward-language callbacks are absent. Outgoing PrintMgr/JobMgr packets remain queued. Infinite waits and zero time slices avoid timer/interrupt delivery. No hardware, USB, DMA, custom raster instruction, printing or recovery is demonstrated.')
    (OUT/'scheduled-status.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    (OUT/'scheduled-status.md').write_text('# Original status task under original scheduling\n\n'
        +f'{len(cases)} QEMU cases pass scheduling, message, counter and lifetime oracles.\n\n'
        +'\n'.join('- '+x for x in report['findings'])+'\n\n'+report['limits']+'\n')
    print(f'Scheduled original StatusMgr: {len(cases)} cases')


if __name__=='__main__':
    main()
