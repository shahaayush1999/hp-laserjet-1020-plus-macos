#!/usr/bin/env python3
"""Original priority scheduler and blocking queues with two synthetic tasks."""
import hashlib
import json
import os
from pathlib import Path
from hp1020_qemu_scheduler import run_scheduler
from hp1020_qemu_ram import QemuRAM
from hp1020_xtensa_call0 import Program

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'analysis/open-firmware-model/stock-execution'


def main():
    p = Program(ROOT/'analysis/sihp1020.elf',os.environ.get('XTENSA_PREFIX','/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf'))
    cases = []
    with QemuRAM() as q:
        for priorities in ((1,2),(2,1),(7,7),(0,31),(31,0)):
            for count in (1,7):
                for width in (1,4):
                    for capacity in (1,3):
                        for fill in (0,0xcc):
                            cases.append(run_scheduler(q,p,p.prefix,priorities=priorities,count=count,
                                                       width=width,capacity=capacity,fill=fill))
    sources = ('validate-hp1020-stock-scheduler.py','hp1020_qemu_scheduler.py','hp1020_qemu_context.py',
               'hp1020_stock_queue.py','hp1020_qemu_ram.py','hp1020_qemu_stock_parser.py',
               'hp1020_xtensa_call0.py','hp1020_xtensa_stock.py','hp1020_stock_stop.py')
    report = dict(status='pass',total_cases=len(cases),cases=cases,
        elf_sha256=hashlib.sha256(p.path.read_bytes()).hexdigest(),
        source_sha256={name:hashlib.sha256((ROOT/'scripts'/name).read_bytes()).hexdigest() for name in sources},
        findings=[
            'Original RTOS RAM initialization builds the full 256-byte lowest-set-bit lookup table against an independent integer oracle. Omitting initialization left this BSS table zero and caused an invalid fixture to idle despite a ready thread.',
            'Original thread-create core, initial-stack builder, resume, ready lists, priority selection, suspend, voluntary context switch, thread shell and queue create/send/receive execute without any whole-function host service.',
            'A synthetic producer sends complete one-word or four-word records, blocks on full queues and waits for an acknowledgement. A synthetic consumer receives every record in order, validates via an external complete-byte oracle, and acknowledges the arithmetic sum. Queue capacity, priority order/equality/extremes and initial RAM fills vary.',
            'The scheduler chooses the initially highest-priority ready task, with FIFO creation order for the tested equal-priority pair. Run counters match observed scheduler selections and preemption bookkeeping balances. Both queues finish empty without suspended waiters.',
            'When the producer has higher priority, acknowledgement delivery preempts the consumer. Otherwise the consumer returns and the original thread shell terminates it before the producer finishes; the corresponding final thread states agree.'
        ],
        limits='Only two synthetic tasks and explicit initial system state are tested. The original thread-create core receives known-valid arguments; its outer validation wrapper is not exercised here. Waits are infinite and time slices zero, so no timer expiry or interrupt-driven preemption occurs. The workload has no parser, JobMgr, PrintMgr, DMA, custom raster instruction or hardware. This removes scheduling substitutes from this kernel experiment, not from the existing printing-lifecycle harnesses. The producer is observed at its final sentinel, and the consumer may remain paused at acknowledgement delivery.')
    (OUT/'scheduler.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    (OUT/'scheduler.md').write_text('# Original priority scheduling and blocking queues\n\n'
        +f'{len(cases)} QEMU cases pass complete-message, arithmetic, priority, queue and thread-state oracles.\n\n'
        +'\n'.join('- '+x for x in report['findings'])+'\n\n'+report['limits']+'\n')
    print(f'Original priority scheduler: {len(cases)} blocking-queue cases')


if __name__=='__main__':
    main()
