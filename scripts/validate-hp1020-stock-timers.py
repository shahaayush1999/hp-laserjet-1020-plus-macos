#!/usr/bin/env python3
"""Check original timed waits against explicit software-tick oracles."""
import hashlib
import json
import os
from pathlib import Path
from hp1020_xtensa_call0 import Program
from hp1020_qemu_ram import QemuRAM
from hp1020_qemu_timers import run_timers

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'analysis/open-firmware-model/stock-execution'


def main():
    p = Program(ROOT/'analysis/sihp1020.elf',os.environ.get('XTENSA_PREFIX','/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf'))
    cases = []
    with QemuRAM() as q:
        for delay in (1,2,31,32,33,65):
            for mode in ('sleep','receive','send'):
                for fill in (0,0xcc):
                    cases.append(run_timers(q,p,delay,mode,False,fill))
        for delay in (2,33):
            for mode in ('receive','send'):
                for fill in (0,0xcc):
                    cases.append(run_timers(q,p,delay,mode,True,fill))
    report = dict(status='pass',total_cases=len(cases),cases=cases,
        elf_sha256=hashlib.sha256(p.path.read_bytes()).hexdigest(),
        source_sha256={name:hashlib.sha256((ROOT/'scripts'/name).read_bytes()).hexdigest() for name in
            ('validate-hp1020-stock-timers.py','hp1020_qemu_timers.py','hp1020_qemu_scheduler.py',
             'hp1020_qemu_multitask.py','hp1020_qemu_stock_parser.py','hp1020_qemu_ram.py')},
        findings=[
            'Original timer initialization builds its 32-slot wheel and creates the original timer task, initially suspended. Its original entry, input magic and thread control block are checked; only stack address, stack size and priority are fixture inputs.',
            'A native low-priority clock task invokes the original tick function. Original timer-task wakeup, bucket processing, callback invocation, requeue beyond 32 ticks and priority scheduling execute without whole-function host services.',
            'Sleep wakes on the requested software tick with result 0. Empty receive and full send expire on that tick with results 10 and 11, respectively. Cases cross the 31/32/33 and 64/65 wheel boundaries.',
            'When another native task satisfies a queued send or receive on tick 1, original queue/resume code removes its pending timer. Continuing beyond the old deadline produces no timeout callback and preserves the delivered message.',
            'Independent oracles check wake tick, result, callback count, queue contents and wait lists, task states/run counts, preemption balance, clock count, empty timer buckets and the exact final wheel cursor.'
        ],
        limits='These are original software timeouts under explicitly supplied ticks, not physical elapsed-time or interrupt-delivery proof. The original tick routine executes QEMU CCOUNT/CCOMPARE operations, while INTENABLE stays zero; the clock task explicitly marks its call as system context and yields afterward. Worker, clock and timer priorities are fixed at 5, 31 and 0 with zero time slices. No hardware/MMIO, USB, boot clock calibration, automatic IRQ entry/return, time slicing, periodic application callbacks, or original printing-task integration is demonstrated.')
    (OUT/'timers.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    (OUT/'timers.md').write_text('# Original timer task and timed waits\n\n'+f'{len(cases)} QEMU cases pass explicit tick, queue and task-state oracles.\n\n'+'\n'.join('- '+x for x in report['findings'])+'\n\n'+report['limits']+'\n')
    print(f'Original timed waits: {len(cases)} cases')


if __name__=='__main__':
    main()
