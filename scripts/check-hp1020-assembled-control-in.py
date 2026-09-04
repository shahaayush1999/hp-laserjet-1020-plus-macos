#!/usr/bin/env python3
"""Exercise compiled endpoint-0 selection/clipping/copy code with zero MMIO.

Controller gates and submit operations are skipped at explicit instruction
boundaries. Register clobbers at the gate/sequence boundary are injected.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('assembled_parser',ROOT/'scripts/check-hp1020-assembled-parser.py')
ram=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=ram
spec.loader.exec_module(ram)


def first_instruction(program,start,op,args):
    return next(pc for pc,(name,operands,size) in sorted(program.items()) if pc>=start and name==op and operands==args)


def run_variant(variant,prefix):
    directory=ROOT/'analysis/open-firmware-probes'/variant
    stem='hp1020-usb-bulk-parser-draft' if variant=='usb-bulk-parser-draft' else 'hp1020-usb-marker-draft'
    elf=directory/(stem+'.elf')
    template=ram.decode(prefix,elf,False)
    memory,program,symbols,state=template
    clip=symbols['hp1020_usb_marker_clip_and_dispatch']
    gate=first_instruction(program,clip,'l32r',(2,symbols['hp1020_mmio_b3000408']))
    kick=symbols['hp1020_usb_marker_kick_control_in']
    submit=first_instruction(program,kick,'l32r',(8,symbols['hp1020_mmio_b3000000']))
    def read_initial(address,size): return bytes(memory[(address&0x7fffffff)+i] for i in range(size))
    cases=[]
    descriptors=[('device',0x90003300,18),('config_high',0x90003314,32)]
    if variant=='usb-bulk-parser-draft':
        descriptors += [('config_full',0x90003334,32),('lang',0x90003354,4),('manufacturer',0x90003358,32),('product',0x90003400,124)]
    else:
        descriptors += [('lang',0x90003334,4),('manufacturer',0x90003338,32),('product',0x90003200,38)]
    values=[(0,0,0,0,0),(36,1,2,0,0),(0xffffffff,0xdeadbeef,0x12345678,9,10)]
    descriptors.sort(key=lambda row: row[0]!='product')
    for name,pointer,length in descriptors:
        for counters in (values if name=='product' and variant=='usb-bulk-parser-draft' else [values[0]]):
            for wlength in sorted({0,1,2,7,length-1,length,255,65535}):
                machine=ram.Machine(*template)
                machine.allowed_writes += [(0x10003400,0x1000347c),(0x100212d4,0x10021318),
                                           (0x100226f0,0x10022700),(0x10022bd0,0x10022c4c)]
                for base,size in [(0x10021348,8),(0x100212d4,0x44),(0x100226f0,16),(0x10022bd0,124)]:
                    for i in range(size): machine.memory[base+i]=0xa5
                setup=bytes([0x80,6,2,3,0,0,wlength&255,wlength>>8])
                for i,b in enumerate(setup): machine.memory[0x10021348+i]=b
                for i,value in enumerate(counters): machine.write(state+0x60+i*4,4,value)
                expected=read_initial(pointer,length)
                if name=='product' and variant=='usb-bulk-parser-draft':
                    text='HP1020 '+' '.join(f'{letter}={value:08X}' for letter,value in zip('BDCEU',counters))
                    expected=bytes([124,3])+text.encode('utf-16le')
                    if len(expected)!=124: raise AssertionError('bad expected status string')
                r=[0]*16
                r[2],r[4],r[7],r[9],r[11]=pointer,state,length,0,0x90021348
                entry=symbols['hp1020_usb_marker_select_'+name] if name in ('device','lang','manufacturer','product') else clip
                machine.run(r,entry,gate)
                clipped=min(wlength,length)
                assert r[6]==clipped,(name,wlength,r[6])
                assert machine.read(state+0x18,4)==(wlength&255)
                assert machine.read(state+0x1c,4)==(wlength>>8)
                assert machine.read(state+0x20,4)==clipped
                actual_descriptor=bytes(machine.read(pointer+i,1) for i in range(length))
                assert actual_descriptor==expected,(name,'descriptor bytes differ')
                # Gate and sequence macros use a2/a3/a5/a7/a8/a9/a10. Model
                # these clobbers, but perform no reads or writes to controller MMIO.
                for reg in (2,3,5,7,8,9,10): r[reg]=0xb3000408
                machine.run(r,kick,submit)
                actual=bytes(machine.read(0x90022bd0+i,1) for i in range(clipped))
                assert actual==expected[:clipped],(name,wlength,'wrong staged payload')
                assert machine.read(0x100212d4+0x3c,4)==clipped
                assert machine.read(0x100212d4+0x40,4)==0x90022bd0
                assert machine.read(0x900226f0,4)==0x08000000|clipped
                assert machine.read(0x900226f4,4)==0
                assert machine.read(0x900226f8,4)==0x90022bd0
                assert machine.read(0x900226fc,4)==0
                assert machine.read(0x90022bd0+clipped,1)==0xa5 if clipped<124 else True
                cases.append({'descriptor':name,'wLength':wlength,'bytes_staged':clipped,'status':'pass'})
    report={'status':'pass','variant':variant,'elf_sha256':hashlib.sha256(elf.read_bytes()).hexdigest(),
            'cases':cases,'total_cases':len(cases),'mmio_accesses':0,
            'scope':'RAM-only descriptor selection, clipped length and staging/transfer-record construction; gate/submit hardware skipped',
            'regression':'State pointer must survive hex formatting; selected descriptor pointer must survive gate and sequence clobbers.'}
    (directory/'assembled-control-in-check.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    (directory/'assembled-control-in-check.md').write_text('\n'.join([
        '# Assembled control-IN RAM execution check','',f"Status: pass; {len(cases)} cases; zero MMIO accesses.",'',
        'Executes compiled selection/clipping and response-copy instructions. Tests device/config/language/manufacturer/product '
        'descriptors at zero, odd, short, exact and oversized host lengths; bulk status tests include zero, live-test and mixed hexadecimal counters.', '',
        'All controller reads and writes are skipped at explicit boundaries. The test injects the register clobbers from '
        'gate/sequence code, then checks exact staged bytes, response length/pointer and all four transfer-record words. '
        'It rejects out-of-range RAM writes and every MMIO access. USB completion, status-stage behavior and physical timing remain untested.','',
        'Regressions caught: `a4` must be restored after counter formatting, and the selected descriptor pointer must survive '
        'the `a2` gate-register loads. Both failures reproduced against checkpoint `16cec37` before the fixes.','']))
    print(f'{variant}: {len(cases)} compiled control-IN RAM cases passed')
    return report


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--variant',choices=['usb-marker-draft','usb-bulk-parser-draft'],required=True)
    args=parser.parse_args()
    run_variant(args.variant,os.environ.get('XTENSA_PREFIX','/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf'))

if __name__=='__main__': main()
