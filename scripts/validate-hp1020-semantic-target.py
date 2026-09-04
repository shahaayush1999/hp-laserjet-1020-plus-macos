#!/usr/bin/env python3
"""Execute actual GCC BE/call0 semantic and planning code in synthetic host RAM."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from hp1020_xtensa_call0 import Program,Machine

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'analysis/open-firmware-model/semantic-target'
SRC=ROOT/'open-firmware/semantic-core'


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m;spec.loader.exec_module(m);return m


def fnv(data):
    h=2166136261
    for byte in data:h=(h^byte)*16777619&0xffffffff
    return h


def main():
    program=Program(OUT/'target-check.elf',os.environ.get('XTENSA_PREFIX','/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf'))
    model=module('target_print_model',ROOT/'scripts/model-hp1020-print-path.py')
    framing=module('target_framing_cases',ROOT/'scripts/model-hp1020-usb-bulk-parser-draft.py')
    cases=[];all_visited=set();opcodes=set();total=0
    with tempfile.TemporaryDirectory(prefix='hp1020-target-oracle-') as tmp:
        temp=Path(tmp);bridge=temp/'bridge.c';binary=temp/'oracle';inputfile=temp/'input'
        bridge.write_text('''#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
extern uint8_t hp1020_test_input[65536];
extern uint32_t hp1020_test_output[32];
extern uint32_t hp1020_target_run(uint32_t,uint32_t);
int main(int argc,char **argv) {
 if(argc!=3)return 2;FILE *f=fopen(argv[1],"rb");if(!f)return 3;
 size_t n=fread(hp1020_test_input,1,65536,f);if(ferror(f))return 4;fclose(f);
 hp1020_target_run((uint32_t)n,(uint32_t)strtoul(argv[2],0,10));
 putchar('[');for(unsigned i=0;i<32;i++)printf("%s%u",i?",":"",hp1020_test_output[i]);puts("]");return 0;
}
''')
        subprocess.run([os.environ.get('CC','clang'),'-O2','-fno-common','-fsanitize=address,undefined','-I'+str(SRC),
                        str(SRC/'hp1020_semantic.c'),str(SRC/'hp1020_page_plan.c'),str(SRC/'freestanding/target-check.c'),str(bridge),'-o',str(binary)],check=True)
        def run(name,data,fragment,expected=None):
            nonlocal total
            assert len(data)<=65536
            machine=Machine(program);machine.put(program.symbols['hp1020_test_input'],data)
            returned=machine.run([len(data),fragment])
            actual=[machine.read(program.symbols['hp1020_test_output']+i*4,4) for i in range(32)]
            inputfile.write_bytes(data)
            oracle=subprocess.run([str(binary),str(inputfile),str(fragment)],text=True,capture_output=True)
            assert oracle.returncode==0 and not oracle.stderr,(name,oracle.stderr)
            assert actual==json.loads(oracle.stdout),(name,actual,oracle.stdout)
            assert returned==actual[0]
            if expected is not None:assert actual==expected,(name,actual,expected)
            total+=machine.steps;all_visited.update(machine.visited);opcodes.update(machine.opcodes)
            cases.append(dict(case=name,fragment=fragment,instructions=machine.steps,result=returned,status='pass'))
        for path in sorted((ROOT/'analysis/samples/generated').glob('*.zjs')):
            data,_,chunks,_=model.parse_chunks(path);objects=model.build_model(path)['objects']
            f=objects['work_objects'][0]['fields'];p=objects['pages'][0];items=p['zjs_items']
            payload=b''.join(c.payload for c in chunks if c.chunk_type==5)
            bounded=int(p['stock_metadata_bounds']['status']=='bounded');bpp=items['ZJI_VIDEO_BPP']
            plan_result=1 if not bounded else 2 if bpp==4 else 0
            expected=[0,1,1,1,len(payload),fnv(payload),items['ZJI_DMCOPIES'],items['ZJI_NBIE'],items['ZJI_RESOLUTION_X'],items['ZJI_RESOLUTION_Y'],
                      items['ZJI_VIDEO_X'],items['ZJI_VIDEO_Y'],bpp,f['+0x84'],f['+0x88'],f['+0x8c'],f['+0x90'],len(payload),1,f['+0x26'],f['+0x30'],f['+0x32'],bounded,plan_result]+[0]*8
            if plan_result==0:
                stride=((f['+0x84']+31)//32)*4;rows=f['+0x26'];n=(8192//stride)//4*4
                expected[24:30]=[stride,stride*(2 if bpp==1 else 1),n,(rows+n-1)//n,rows*stride,1]
            for fragment in (1,7,1024):run(path.stem,data,fragment,expected)
        for c in framing.synthetic_cases():run('boundary/'+c.name,b''.join(c.transfers),7)
    # Explicitly fail closed on MMIO, unaligned loads and code writes.
    machine=Machine(program);rejected=0
    for action in (lambda:machine.read(0xb1000000,4),lambda:machine.read(0x21000001,4),lambda:machine.write(program.entry,4,0),lambda:machine.span(program.symbols["hp1020_test_input"],3,True)):
        try:action()
        except ValueError:rejected+=1
    assert rejected==4
    report=dict(status='pass',total_cases=len(cases),executed_instructions=total,distinct_instructions=len(all_visited),
                executed_opcodes=sorted(opcodes),cases=cases,negative_memory_checks=rejected,
                elf_sha256=hashlib.sha256((OUT/'target-check.elf').read_bytes()).hexdigest(),
                target='GCC 14.3.0, big-endian Xtensa call0, synthetic RAM at 0x20000000',
                scope='The real compiled C parser, memory helpers, software unsigned division and page planner execute without a peripheral model. No upload image is produced.',
                limits='This tests compiler/ABI/CPU arithmetic and RAM behavior. It does not prove boot-ROM state, USB behavior, cache coherency, custom raster instructions or mechanical safety.',
                source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(SRC.rglob('*')) if p.suffix in ('.c','.h','.ld')})
    (OUT/'validation.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    (OUT/'validation.md').write_text(f"# Compiled semantic target validation\n\nStatus: pass. {len(cases)} cases, {total:,} executed instructions, {len(all_visited)} distinct reached instructions.\n\n"
        +report['scope']+'\n\nAll generated fixtures match independent Python field/payload/planning expectations at three fragmentation sizes. '
        'All cases also match an ASan/UBSan native oracle. MMIO, misaligned word loads, code writes and execution from data sections are rejected.\n\n'+report['limits']+'\n')
    print(f'target C: {len(cases)} cases, {total} instructions, {len(all_visited)} distinct, zero MMIO')

if __name__=='__main__':main()
