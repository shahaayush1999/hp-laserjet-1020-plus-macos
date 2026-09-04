#!/usr/bin/env python3
"""Differentially check native RAM-only page/band planning, with sanitizers."""
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'open-firmware/semantic-core'

def expected(values):
    xd,yd,bpp,res,eco,ret,bounded,copies=values
    out=dict(result=0,stride=0,window=0,chunk_rows=0,bands=0,last_rows=0,bytes=0)
    if not bounded or not copies or copies>65535 or not xd or xd>0xffffffff-31 or not yd or yd>65535:out['result']=1;return out
    if res!=600 or bpp not in (1,2) or yd%4 or eco>1 or ret:out['result']=2;return out
    stride=((xd+31)//32)*4;chunk=(8192//stride)//4*4
    if not chunk:out['result']=2;return out
    out.update(stride=stride,window=stride*(2 if bpp==1 else 1),chunk_rows=chunk,
               bands=(yd+chunk-1)//chunk,last_rows=((yd-1)%chunk)+1,bytes=stride*yd)
    return out

def main():
    cases=[]
    def add(name,values):cases.append(dict(case=name,values=values,expected=expected(values)))
    for path in sorted((ROOT/'analysis/open-firmware-model/variants').glob('*/print-path-model.json')):
        m=json.loads(path.read_text());f=m['objects']['work_objects'][0]['fields'];p=m['objects']['pages'][0]
        add(path.parent.name,[f['+0x84'],f['+0x26'],f['+0x22'],f['+0x14'],f['+0x32'],f['+0x30'],int(p['stock_metadata_bounds']['status']=='bounded'),f['+0x0c']])
    for stride in (4,8,32,608,1200,1232,2048,2052,4096):
        for rows in (0,1,3,4,8,12,16,128,6824,65532,65535,65536,0xffffffff):
            for bpp in (1,2,4):add(f'boundary/{stride}/{rows}/{bpp}',[stride*8,rows,bpp,600,0,0,1,1])
    for xd in (0,1,31,32,0xffffffe0,0xffffffe1,0xffffffff):add(f'width/{xd}',[xd,4,2,600,0,0,1,1])
    for index,values in enumerate(([9600,6824,2,300,0,0,1,1],[9600,6824,2,600,2,0,1,1],[9600,6824,2,600,0,1,1,1],
                                    [9600,6824,2,600,0,0,0,1],[9600,6824,2,600,0,0,1,0],[9600,6824,2,600,0,0,1,65536])):add(f'policy/{index}',list(values))
    rng=random.Random(1020)
    for i in range(1024):add(f'partition/{i}',[rng.randrange(1,2053)*8,rng.randrange(1,16384)*4,rng.choice((1,2)),600,rng.randrange(2),0,1,1])
    with tempfile.TemporaryDirectory(prefix='hp1020-page-plan-') as tmp:
        binary=Path(tmp)/'check'
        subprocess.run([os.environ.get('CC','clang'),'-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',
                        str(SRC/'hp1020_page_plan.c'),str(SRC/'plan-check.c'),'-o',str(binary)],check=True)
        result=subprocess.run([str(binary)],input=''.join(' '.join(map(str,c['values']))+'\n' for c in cases),text=True,capture_output=True)
        assert result.returncode==0 and not result.stderr,(result.returncode,result.stderr)
        actual=[json.loads(x) for x in result.stdout.splitlines()]
        assert len(actual)==len(cases)
        for row,got in zip(cases,actual):assert row['expected']==got,(row,got)
    variants={c['case']:c['expected'] for c in cases[:10]}
    assert variants['a4_default']==dict(result=0,stride=1200,window=1200,chunk_rows=4,bands=1706,last_rows=4,bytes=8188800)
    assert variants['a4_2400x600']['result']==2 and variants['a4_logical_clip']['result']==1
    report=dict(status='pass',total_cases=len(cases),generated_cases=variants,
                bands_checked=sum(r['bands'] for r in actual),sanitizers=['address','undefined'],
                source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(SRC.glob('*page_plan.*'))},
                policy='RAM arithmetic only; complete page, bounded stock metadata, NBIE1, 600dpi BPP1/2, height divisible by four, RET0, ECONOMODE0/1; no hardware authorization',
                remaining='Custom callback transformations, asynchronous buffer ownership, USB/device execution, and physical engine/video sequencing remain outside this component.')
    out=ROOT/'analysis/open-firmware-model/page-plan'
    out.with_suffix('.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    out.with_suffix('.md').write_text(f"# Portable page and band plan\n\nStatus: pass. {len(cases)} native ASan/UBSan cases and {report['bands_checked']} band partitions checked.\n\n"
        +report['policy']+'.\n\nA4 default: stride/window 1200, four rows per band, 1706 bands, 8,188,800 row bytes per copy. '
        'BPP4 and the inconsistent logical-clip metadata fixture are rejected by this deliberately narrow planning policy. '
        'The semantic parser can still retain those inputs for analysis.\n\n'+report['remaining']+'\n')
    print(f"page plan: {len(cases)} cases, {report['bands_checked']} bands, ASan/UBSan")

if __name__=='__main__':main()
