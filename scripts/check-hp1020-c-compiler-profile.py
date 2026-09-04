#!/usr/bin/env python3
"""Check the actual compiler's BE/call0 conservative feature profile."""
import argparse
import json
from pathlib import Path
import re
import runpy
import subprocess

ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('compiler');a=p.parse_args()
    version=subprocess.check_output([a.compiler,'--version'],text=True).splitlines()[0]
    assert '14.3.0' in version,version
    text=subprocess.check_output([a.compiler,'-dM','-E','-x','c','/dev/null'],text=True)
    macros=dict(re.findall(r'^#define (\S+) (.*)$',text,re.M))
    required={'__XTENSA_EB__':'1','__XTENSA_CALL0_ABI__':'1','__XSHAL_ABI':'1'}
    for name in ('BE','DENSITY','ADDX','L32R','MUL32','NSA'):required['__XCHAL_HAVE_'+name]='1'
    disabled=('DIV32','THREADPTR','RELEASE_SYNC','S32C1I','LOOPS','WINDOWED','ABS','MUL16','MINMAX','SEXT','FP','MUL32_HIGH')
    for name in disabled:required['__XCHAL_HAVE_'+name]='0'
    for name,value in required.items():assert macros.get(name)==value,(name,macros.get(name),value)
    read=runpy.run_path(str(ROOT/'scripts/recover-hp1020-division-decode.py'))['elf_range']
    fixtures=[('call0',0x100187b1,'500a5d'),('ret.n',0x1001b1fa,'d00f'),
              ('mull',0x10013f8e,'098828'),('nsau',0x1001b670,'056f04'),
              ('addx4',0x10013f75,'07a80a')]
    evidence=[]
    for name,address,raw in fixtures:
        assert read(address,len(bytes.fromhex(raw))).hex()==raw
        evidence.append(dict(instruction=name,address=f'0x{address:08x}',bytes=raw))
    report=dict(status='pass',compiler=version,macros=required,stock_instruction_evidence=evidence,
                scope='Compiler feature and static stock-byte compatibility gate; not a boot/CPU-state hardware test')
    out=ROOT/'analysis/toolchain-probe/c-compiler-profile'
    out.with_suffix('.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    lines=['# Conservative C compiler profile','',version,'',report['scope'],'', '| Macro | Required and observed |','|---|---|']
    lines += [f'| {k} | {v} |' for k,v in required.items()]
    lines += ['', '| Stock counterpart | Address | Bytes |','|---|---|---|']
    lines += [f"| {x['instruction']} | {x['address']} | {x['bytes']} |" for x in evidence]
    out.with_suffix('.md').write_text('\n'.join(lines)+'\n')
    print(f'C compiler profile: {len(required)} macros and {len(evidence)} stock-byte counterparts verified')

if __name__=='__main__':main()
