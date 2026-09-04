#!/usr/bin/env python3
"""Audit raster callback selection/arguments and explicitly unresolved ISA bytes."""
import collections
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import struct
import subprocess

ROOT=Path(__file__).resolve().parents[1]
read=runpy.run_path(str(ROOT/'scripts/recover-hp1020-division-decode.py'))['elf_range']
OUT=ROOT/'analysis/hardware-boundary/raster-callbacks'


def word(address): return struct.unpack('>I',read(address,4))[0]


def main():
    prefix=os.environ.get('XTENSA_PREFIX','/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf')
    functions=[];checks=[]
    for name,cell,start,end in [('bpp2_600',0x1000684c,0x10015648,0x10015811),
                              ('bpp1_1200',0x10006848,0x10015814,0x100159b4),
                              ('bpp1_600',0x10006844,0x100159b4,0x10015bc5)]:
        assert word(cell)==start,(cell,word(cell))
        text=subprocess.check_output([prefix+'-objdump','-d',f'--start-address={start}',f'--stop-address={end}',str(ROOT/'analysis/sihp1020.elf')],text=True)
        rows=[];unknown=[];user=[];pc=start
        for line in text.splitlines():
            m=re.match(r'\s*([0-9a-f]{8}):\s+([0-9a-f]{4,6})\s+(\S+)\s*(.*)',line)
            if not m:continue
            address=int(m[1],16);raw=bytes.fromhex(m[2])
            assert address==pc and raw==read(address,len(raw))
            pc+=len(raw)
            row=dict(address=f'0x{address:08x}',bytes=raw.hex(),mnemonic=m[3],operands=m[4].strip())
            if m[3]=='excw':
                if raw[0]>>4==0 and raw[2]==0x3f:
                    # WUR is standard, but user-register definitions are core-specific.
                    register=raw[1];row.update(classification='user_register_write',user_register=register,source_register=f'a{raw[0]&15}')
                    user.append(row)
                else:
                    row.update(classification='unresolved_extension',encoding_group=f'0x{raw[2]:02x}')
                    unknown.append(row)
            rows.append(row)
        assert pc==end and rows[-1]['mnemonic'] in ('retw','retw.n')
        functions.append(dict(name=name,literal_cell=f'0x{cell:08x}',start=f'0x{start:08x}',end=f'0x{end:08x}',
                              sha256=hashlib.sha256(read(start,end-start)).hexdigest(),instructions=rows,
                              unknown_instructions=unknown,user_register_writes=user,
                              unknown_groups=dict(collections.Counter(x['encoding_group'] for x in unknown))))
        checks.append(dict(name=name+'_complete_byte_matched_decode',status='present',instructions=len(rows)))
    expected={0x10013fd9:'2a723d',0x10013fdc:'2d722e',0x10013fe2:'8c52',
              0x10013fe4:'0daa28',0x10013fea:'2b8204',0x10013fed:'0c2c14',
              0x10013ff0:'0ecc11',0x10013ff3:'282200',0x10013ff6:'0a6a0c',0x10013ff9:'0b8000'}
    for address,raw in expected.items():
        assert read(address,len(bytes.fromhex(raw))).hex()==raw
        checks.append(dict(name=f'callback_arg_bytes_{address:08x}',address=f'0x{address:08x}',bytes=raw,status='present'))
    masks={f'0x{x:08x}':f'0x{word(x):08x}' for x in (0x10006908,0x1000690c,0x10006910)}
    assert list(masks.values())==['0xeeeeeeee','0xbbbbbbbb','0x55555555']
    checks.append(dict(name='bpp2_masks_verified',status='present'))
    assert len(functions[0]['unknown_instructions'])==16
    report=dict(status='pass',scope='offline stock-byte audit; unresolved instructions are not executed or treated as safe',
                functions=functions,checks=checks,masks=masks,
                call_contract={'callsite':'0x10013ff9 callx8 a8','argument_count':4,
                    'a10_to_a2':'source = slot pointer - video +0xf4 * stride',
                    'a11_to_a3':'destination = transformed slot pointer at video +0x10 + slot*4',
                    'a12_to_a4':'rows = descriptor units & ~3',
                    'a13_to_a5':'stride = video +0xb8 (omitted by saved decompilation)'},
                findings=['Default BPP2/600 selects 0x10015648, BPP1/600 selects 0x100159b4, BPP1/1200 selects 0x10015814.',
                          'The indirect call has four arguments. Saved Ghidra C showed only three and lost the stride argument.',
                          'BPP2 writes user registers 0 and 1 with EEEEEEEE and BBBBBBBB, and uses 55555555 in ordinary Boolean preparation.',
                          'BPP2 has 16 custom encodings (groups 0x69, 0x60, 0x6d, 0x6e). BPP1 callbacks also contain unresolved groups 0x8e, 0x8f, 0x7f.',
                          'Ghidra generic WUR output names LBEG/LEND/LCOUNT here are misleading: these are user-register numbers 0/1/2, not proof of loop-register writes.',
                          'The callback gate is video +0xc0 and nonzero callback pointer. Stock can bypass this stage, but acceptable image quality and timing of that configuration are uncalibrated.'],
                unresolved=['Exact value transformation and side effects of each extension encoding, including hidden state and possible memory accesses.',
                            'Whether the stock-supported bypass can meet the narrow replacement print-quality requirement.',
                            'Safe physical interpretation of the transformed output buffers and engine/video timing.'],
                next_evidence='Obtain this core-specific ISA definition, or compare controlled inputs and outputs while stock firmware executes these callbacks. No custom opcode probe is authorized or claimed safe.')
    OUT.with_suffix('.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    lines=['# Stock raster callbacks','',report['scope'],'','## Verified findings','']+['- '+x for x in report['findings']]
    lines+=['','## Callback arguments','', '| Register window mapping | Value |','|---|---|']
    lines += [f'| {k} | {v} |' for k,v in report['call_contract'].items() if '_to_' in k]
    lines+=['','## Exact unresolved encodings','', '| Function | Instructions | Unresolved groups | User registers |','|---|---:|---|---|']
    for f in functions:lines.append(f"| {f['name']} ({f['start']}) | {len(f['instructions'])} | {f['unknown_groups']} | {[x['user_register'] for x in f['user_register_writes']]} |")
    lines+=['','Full byte-matched instruction listings and every unresolved address are in the JSON report.','', '## Remaining questions','']+['- '+x for x in report['unresolved']]+['',report['next_evidence'],'']
    OUT.with_suffix('.md').write_text('\n'.join(lines))
    print('raster callbacks:',[(f['name'],len(f['instructions']),len(f['unknown_instructions'])) for f in functions])

if __name__=='__main__':main()
