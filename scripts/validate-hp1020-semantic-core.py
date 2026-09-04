#!/usr/bin/env python3
"""Compile and exercise the MMIO-free semantic C core under ASan and UBSan."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import struct
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'analysis/open-firmware-model/semantic-core'
SOURCE=ROOT/'open-firmware/semantic-core'


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m


def chunk(kind,payload=b'',items=0,reserved=0):
    return struct.pack('>IIIHH',16+len(payload),kind,items,reserved,0x5a5a)+payload


def fnv(data):
    result=2166136261
    for b in data: result=((result^b)*16777619)&0xffffffff
    return result


def main():
    model=module('hp1020_semantic_reference',ROOT/'scripts/model-hp1020-print-path.py')
    cases=[]
    samples=sorted((ROOT/'analysis/samples/generated').glob('*.zjs'))
    with tempfile.TemporaryDirectory(prefix='hp1020-semantic-') as tmp:
        temp=Path(tmp);binary=temp/'host-check';casefile=temp/'input.zjs'
        subprocess.run([os.environ.get('CC','clang'),'-std=c11','-Wall','-Wextra','-Werror','-g','-fsanitize=address,undefined',
                        str(SOURCE/'hp1020_semantic.c'),str(SOURCE/'host-check.c'),'-o',str(binary)],check=True)
        def run(name,data,fragment=1024,capacity=1048576,error=None,expected=None):
            casefile.write_bytes(data)
            result=subprocess.run([str(binary),str(casefile),str(fragment),str(capacity)],capture_output=True,text=True)
            if result.returncode or result.stderr: raise AssertionError((name,result.returncode,result.stderr))
            actual=json.loads(result.stdout)
            if error is not None: assert actual['result']==error,(name,actual,error)
            else:
                assert actual['result']==0,(name,actual)
                if expected is not None: assert actual==expected,(name,actual,expected)
            cases.append({'case':name,'status':'pass','result':actual['result']})
            return actual
        for sample in samples:
            data,_,chunks,_=model.parse_chunks(sample)
            work=model.build_model(sample)['objects']['work_objects'][0]
            items=work['host_page_items'];fields=work['fields']
            bids=[c.payload for c in chunks if c.chunk_type==5]
            rasters=[];offset=0
            for bid in bids:
                rasters.append({'page':0,'offset':offset,'length':len(bid),'fnv1a':fnv(bid)});offset+=len(bid)
            expected={'result':0,'documents':1,'arena_used':offset,'pages':[{
                'copies':items['ZJI_DMCOPIES'],'nbie':items['ZJI_NBIE'],'resolution_x':items['ZJI_RESOLUTION_X'],
                'resolution_y':items['ZJI_RESOLUTION_Y'],'video_x':items['ZJI_VIDEO_X'],'video_y':items['ZJI_VIDEO_Y'],
                'bpp':items['ZJI_VIDEO_BPP'],'xd':fields['+0x84'],'yd':fields['+0x88'],'l0':fields['+0x8c'],
                'options':fields['+0x90'],'rasters':len(bids),'compressed_bytes':offset,'complete':1,'sideband_known':1,'work26':fields['+0x26'],'work30':fields['+0x30'],'work32':fields['+0x32']}],
                'rasters':rasters}
            for fragment in (1,7,64,1024,65536): run(sample.stem+f'/fragment={fragment}',data,fragment,expected=expected)
            run(sample.stem+'/exact-arena',data,capacity=offset,expected=expected)
            run(sample.stem+'/arena-short',data,capacity=offset-1,error=3)
        _,_,parts,_=model.parse_chunks(ROOT/'analysis/samples/generated/matrix-a4_default.zjs')
        def raw(c): return chunk(c.chunk_type,c.payload,c.item_count,c.reserved)
        start,page,bih,bid,endb,endp,endd=map(raw,parts)
        prefix=b'JZJZ'
        valid=prefix+start+page+bih+bid+endb+endp+endd
        # Structural transitions, integer/buffer boundaries, and malformed items.
        bad=[('empty',b'',5),('no-magic',b'noise',5),('missing-end-doc',valid[:-16],5),
             ('nested-doc',prefix+start+start,2),('page-before-doc',prefix+page,2),
             ('bih-before-page',prefix+start+bih,2),('bid-before-bih',prefix+start+page+bid,2),
             ('end-jbig-before-bid',prefix+start+page+bih+endb,2),
             ('end-page-before-jbig',prefix+start+page+bih+bid+endp,2),
             ('unknown-chunk',prefix+chunk(0xffffffff),4),('zero-arena',valid,3),
             ('bih-short',prefix+start+page+chunk(4,bytes(19)),1),
             ('end-doc-item-count',prefix+start+chunk(1,items=1),4),
             ('chunk-size-underflow',prefix+struct.pack('>IIIHH',15,0,0,0,0x5a5a),1),
             ('chunk-size-overflow',prefix+struct.pack('>IIIHH',0xffffffff,0,0,0,0x5a5a),3),
             ('bad-signature',prefix+start[:14]+b'XX'+start[16:],1),
             ('metadata-too-large',prefix+chunk(0,bytes(4097)),3),
             ('item-count-too-large',prefix+chunk(0,parts[0].payload,0xffffffff,len(parts[0].payload)),1),
             ('item-size-zero',prefix+chunk(0,bytes(4)+parts[0].payload[4:],3,36),4),
             ('item-size-overflow',prefix+chunk(0,b'\xff'*4+parts[0].payload[4:],3,36),4),
             ('reserved-overflow',prefix+chunk(0,parts[0].payload,3,37),1),
             ('duplicate-item',prefix+chunk(0,parts[0].payload[:12]*2,2,24),1),
             ('item-count-short',prefix+chunk(0,parts[0].payload,2,36),1),
             ('empty-bid',prefix+start+page+bih+chunk(5),1),
             ('duplicate-bih',prefix+start+page+bih+bih,2)]
        for name,data,error in bad: run(name,data,fragment=7,capacity=0 if name=='zero-arena' else 1048576,error=error)
        run('reserved-zero-is-opaque',prefix+chunk(0,parts[0].payload,3,0)+endd)
        for ret,economode,height in [(0,0,6824),(65537,65538,65539),(65535,65535,65535)]:
            changed=[]
            for pos in range(0,len(parts[1].payload),12):
                item=bytearray(parts[1].payload[pos:pos+12]);ident=struct.unpack_from('>H',item,4)[0]
                if ident==18: struct.pack_into('>I',item,8,height)
                if ident==23: struct.pack_into('>I',item,8,economode)
                changed.append(bytes(item))
            changed.append(struct.pack('>IHBBI',12,22,1,0,ret))
            metadata=b''.join(changed)
            result=run(f'sideband-low16/{ret}',prefix+start+chunk(2,metadata,len(changed),len(metadata))+bih+bid+endb+endp+endd)
            assert [result['pages'][0][f'work{x}'] for x in ('26','30','32')]==[height&65535,ret&65535,economode&65535]
        # BIH field errors and unsupported layers/planes.
        for offset,value,error in [(0,1,4),(1,1,4),(2,2,4),(3,1,4)]:
            b=bytearray(parts[2].payload);b[offset]=value
            run('BIH-byte-'+str(offset),prefix+start+page+chunk(4,b),error=error)
        for offset in (4,8,12):
            b=bytearray(parts[2].payload);b[offset:offset+4]=bytes(4)
            run('BIH-zero-word-'+str(offset),prefix+start+page+chunk(4,b),error=1)
        # Test all cuts before the end of a short but semantically complete page.
        small=prefix+start+page+bih+chunk(5,b'abc')+endb+endp+endd
        for cut in range(len(small)):
            run('truncated/'+str(cut),small[:cut],fragment=7,error=5)
        multi=prefix+start+(page+bih+chunk(5,b'abc')+endb+endp)*2+endd
        two=run('two-pages',multi,fragment=1)
        assert len(two['pages'])==2 and [r['page'] for r in two['rasters']]==[0,1]
        split=prefix+start+page+bih+chunk(5,b'abc')+chunk(5,b'defg')+endb+endp+endd
        split_result=run('two-raster-nodes',split,fragment=1)
        assert split_result['pages'][0]['compressed_bytes']==7 and len(split_result['rasters'])==2
        run('page-limit',prefix+start+(page+bih+chunk(5,b'x')+endb+endp)*17+endd,error=3)
        run('raster-limit',prefix+start+page+bih+chunk(5,b'x')*129,error=3)
        rng=random.Random(1020)
        for i in range(64):
            payload=rng.randbytes(rng.randrange(1,1024))
            fuzz=prefix+start+page+bih+chunk(5,payload)+endb+endp+endd
            result=run('binary-payload/'+str(i),fuzz,fragment=rng.randrange(1,65))
            assert result['rasters'][0]['fnv1a']==fnv(payload)
    OUT.mkdir(parents=True,exist_ok=True)
    report={'status':'pass','scope':'portable host-only semantic core; no firmware upload or hardware output',
            'cases':cases,'total_cases':len(cases),'generated_samples':len(samples),
            'sanitizers':['address','undefined'],'sideband_source_known':True,
            'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(SOURCE.glob('*')) if p.suffix in ('.c', '.h')},
            'limits':{'pages':16,'raster_nodes':128,'metadata_bytes':4096,'chunk_bytes':16777216}}
    (OUT/'validation.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    (OUT/'validation.md').write_text('\n'.join(['# Portable semantic core validation','',
        f"Status: pass; {len(cases)} cases; {len(samples)} generated streams; AddressSanitizer and UndefinedBehaviorSanitizer enabled.",'',
        'The C implementation incrementally constructs page metadata and raster records in a caller-supplied bounded RAM arena. '
        'Generated sample geometry and raster byte hashes agree with the existing Python print-path model at five fragment sizes. '
        'Exact-capacity, short-capacity, malformed item/header, ordering, every short-stream truncation, object limit, multi-page, '
        'multi-BID and seeded binary-payload cases are checked.','',
        'The retained compressed bytes are opaque: no JBIG decompression or printing occurs. '
        'Active-work VIDEO_Y/RET/ECONOMODE sources match the ELF-verified direct START_PAGE builder. This code is native-host tested, is not linked into a probe, '
        'and contains no USB, hardware address, or output callback.','']))
    print(f'semantic core: {len(cases)} cases passed, ASan/UBSan, {len(samples)} generated streams')

if __name__=='__main__': main()
