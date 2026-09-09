#!/usr/bin/env python3
"""Validate original flush/context code on independent QEMU physical windows."""
import hashlib
import json
import os
from pathlib import Path
from hp1020_qemu_context import validate_context
from hp1020_qemu_switch import validate_switch
from hp1020_qemu_ram import QemuRAM
from hp1020_xtensa_call0 import Program

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'analysis/open-firmware-model/stock-execution'


def main():
    p = Program(ROOT/'analysis/sihp1020.elf',os.environ.get('XTENSA_PREFIX','/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf'))
    with QemuRAM() as q:
        same = validate_context(q,p,p.prefix)
        different = validate_switch(q,p,p.prefix)
    cases = same.pop('cases')+[dict(mode='two_tasks',**case) for case in different.pop('cases')]
    sources = ('validate-hp1020-stock-context.py','hp1020_qemu_context.py','hp1020_qemu_switch.py',
               'hp1020_qemu_ram.py','hp1020_qemu_stock_parser.py','hp1020_qemu_task.py',
               'hp1020_xtensa_call0.py','hp1020_xtensa_stock.py','hp1020_stock_stop.py',
               'hp1020_stock_notifications.py')
    report = dict(status='pass',total_cases=len(cases),cases=cases,same_thread=same,two_tasks=different,
                  elf_sha256=hashlib.sha256(p.path.read_bytes()).hexdigest(),
                  source_sha256={name:hashlib.sha256((ROOT/'scripts'/name).read_bytes()).hexdigest() for name in sources})
    (OUT/'context.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    (OUT/'context.md').write_text('# Original context construction, save and switching\n\n'
        +f'{len(cases)} QEMU cases match independent arithmetic/frame/bookkeeping oracles. The initial stack builder also agrees with the instruction interpreter.\n\n'
        +'\n'.join('- '+finding for finding in same['findings']+different['findings'])
        +'\n\n'+same['limits']+'\n\n'+different['limits']+'\n')
    print(f'Original context code: {len(cases)} cases and detected continuation mutation')


if __name__=='__main__':
    main()
