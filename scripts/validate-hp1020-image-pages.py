#!/usr/bin/env python3
"""Parse complete ZjStream files and decode planned packed-row bands in open C."""
import argparse
import importlib.util
import json
from pathlib import Path
import struct
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('image_checks',ROOT/'scripts/validate-hp1020-image-core.py')
core=importlib.util.module_from_spec(spec);sys.modules[spec.name]=core;spec.loader.exec_module(core)
SRC=core.SRC;SEM=ROOT/'open-firmware/semantic-core';OUT=core.OUT

def chunks(data):
    pos=data.index(b'JZJZ')+4; out=[]
    while pos+16<=len(data):
        n,k,count,reserved,sig=struct.unpack_from('>IIIHH',data,pos)
        assert sig==0x5a5a and n>=16 and pos+n<=len(data)
        out.append((k,data[pos+16:pos+n],count,reserved));pos+=n
        if k==1:break
    return out
def pack(parts):
    return b''.join(struct.pack('>IIIHH',len(p)+16,k,count,reserved,0x5a5a)+p for k,p,count,reserved in parts)

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--target',action='store_true');args=ap.parse_args()
    cases=[];targets=[];base=chunks((ROOT/'analysis/samples/generated/matrix-a4_default.zjs').read_bytes())
    with tempfile.TemporaryDirectory(prefix='hp1020-image-pages-') as directory:
        temp=Path(directory);host=temp/'host';reference=temp/'reference';inputfile=temp/'input';capture=temp/'capture';oracle=temp/'oracle'
        flags=[core.os.environ.get('CC','clang'),'-std=c11','-O1','-g','-fno-common','-Wall','-Wextra','-Werror','-fsanitize=address,undefined']
        c_sources=[SRC/'hp1020_image.c',SRC/'hp1020_image_page.c',SRC/'page-fixture.c',SRC/'host-page-check.c',
            SEM/'hp1020_semantic.c',SEM/'hp1020_page_plan.c',core.VENDOR/'libjbig/jbig85.c',core.VENDOR/'libjbig/jbig_ar.c']
        core.command(flags+['-DHP1020_IMAGE_HOST_CHECK','-I'+str(SRC),'-I'+str(SEM),'-I'+str(core.VENDOR/'libjbig')]+c_sources+['-o',host])
        full=ROOT/'vendor/foo2zjs-source'
        core.command(flags+['-I'+str(full),SRC/'reference.c',full/'jbig.c',full/'jbig_ar.c','-o',reference])
        def original(bie):
            inputfile.write_bytes(bie);info=json.loads(core.command([reference,'decode',inputfile,oracle]));return oracle.read_bytes(),info['consumed']
        def run(name,data,expected=None,fragment=7,quantum=7,fill=204,image_error=None,parse_error=0,target=False):
            inputfile.write_bytes(data);a=json.loads(core.command([host,inputfile,fragment,quantum,fill,capture]))
            assert a[0]==parse_error,(name,a,parse_error)
            assert a[1]==(0 if parse_error else 2 if image_error is None else image_error),(name,a,image_error)
            assert a[10]==0,(name,'band order/pause',a)
            if not parse_error:assert a[11]==1,(name,'buffer guards',a)
            observed=capture.read_bytes()
            if expected is not None:
                assert observed==expected,(name,'packed image bytes differ')
                assert a[6]==len(expected) and a[7]==core.fnv(expected)
            if image_error is not None:assert a[17]==1,(name,'sticky errors',a)
            # Independently reconstruct original BIHs across all complete documents.
            if not parse_error and image_error is None:
                headers=[];left=data
                while b'JZJZ' in left:
                    start=left.index(b'JZJZ');parts=chunks(left)
                    headers += [p for k,p,_,_ in parts if k==4]
                    left=left[start+4+len(pack(parts)):]
                assert a[2]==len(headers) and a[13]==core.fnv(b''.join(headers))
            cases.append(dict(case=name,status='pass',input_sha256=core.sha(data),output_sha256=core.sha(observed),stats=a,
                fragment=fragment,decoder_quantum=quantum,flags=fill))
            if target:targets.append((name,data,fragment,quantum,fill,a,observed))
            return a
        for p in sorted((ROOT/'analysis/samples/generated').glob('*.zjs')):
            raw,_=original(core.sample_bie(p));data=p.read_bytes()
            error=3 if 'logical_clip' in p.stem else 5 if '2400x600' in p.stem else None
            for fragment,quantum in ((1,1),(7,7),(65536,65536)):
                run(p.stem+f'/fragment={fragment}',data,raw if error is None else None,fragment,quantum,
                    image_error=error,target=fragment==7)
        def body(bie,splits=1,tail=None):
            w,h=struct.unpack_from('>II',bie,4);items=bytearray(base[1][1])
            for off in range(0,len(items),12):
                ident=struct.unpack_from('>H',items,off+4)[0]
                if ident in (13,18):struct.pack_into('>I',items,off+8,h)
                if ident==12:struct.pack_into('>I',items,off+8,w)
                if ident==17:struct.pack_into('>I',items,off+8,w//2)
            bid=bie[20:]+(bytes(16+((-len(bie[20:]))&3)) if tail is None else tail)
            parts=[(2,bytes(items),base[1][2],base[1][3]),(4,bie[:20],0,0)]
            for i in range(splits):parts.append((5,bid[len(bid)*i//splits:len(bid)*(i+1)//splits],0,0))
            return parts+[(6,b'',0,0),(3,b'',0,0)]
        def doc(*pages):return b'JZJZ'+pack([base[0]]+sum(pages,[])+[base[-1]])
        small=(OUT/'fixtures/32x8-stripe4-black.jbg').read_bytes();smallraw,_=original(small)
        medium=(OUT/'fixtures/9600x132-stripe128-edges.jbg').read_bytes();mediumraw,_=original(medium)
        large=(OUT/'fixtures/16384x4-stripe128-edges.jbg').read_bytes();largeraw,_=original(large)
        for name,bie,raw in (('small',small,smallraw),('medium',medium,mediumraw),('max-width',large,largeraw)):
            for fill in (0,204):run('pattern/'+name+f'/fill={fill}',doc(body(bie)),raw,fill=fill,target=True)
        for n in (6,13,64):
            a=run(f'split-bid/{n}',doc(body(medium,n)),mediumraw,fragment=1,quantum=1,target=True)
            assert a[3]==n
        run('two-pages-one-document',doc(body(small),body(medium,13)),smallraw+mediumraw,target=True)
        run('two-documents',doc(body(medium,6))+doc(body(small)),mediumraw+smallraw,target=True)
        run('empty-document',doc(),b'',target=True)
        for flags,name in ((0x100,'unfinalized'),(0x200,'bad-offset'),(0x400,'bad-owner'),(0x800,'changed-bih')):
            run('state/'+name,doc(body(medium)),fill=204|flags,image_error=7,target=True)
        for name,tail in (('missing',b''),('short',bytes(15)),('long',bytes(20)),('nonzero',bytes(15)+b'\x01')):
            run('padding/'+name,doc(body(small,tail=tail)),image_error=3,target=True)
        b=bytearray(medium);b[16]=17
        run('retained-unsupported-bih',doc(body(bytes(b))),image_error=5,target=True)
        run('missing-final-marker',doc(body(medium[:-2])),image_error=3,target=True)
        run('missing-end-doc',doc(body(small))[:-16],parse_error=5,target=True)
        run('truncated-chunk-header',doc(body(small))[:-8],parse_error=5,target=True)
        target_report=None
        if args.target:
            core.command([ROOT/'scripts/build-hp1020-image-target.sh'])
            elf=OUT/'target/target-check.elf';program,audit=core.audit_target(elf)
            from hp1020_qemu_ram import QemuRAM
            native=[]
            with QemuRAM() as q:
                q.load(elf);version=q.version
                for name,data,fragment,quantum,fill,expected,observed in targets:
                    q.put(program.symbols['hp1020_page_input'],data)
                    returned=q.call0(program.symbols['hp1020_page_run'],[len(data),fragment,quantum,fill])
                    actual=list(struct.unpack('>24I',q.read(program.symbols['hp1020_page_stats'],96)))
                    assert returned==(actual[0] or actual[1])
                    assert actual[:14]+actual[15:]==expected[:14]+expected[15:],(name,actual,expected)
                    assert q.read(program.symbols['hp1020_page_capture'],min(len(observed),65536))==observed[:65536]
                    native.append(dict(case=name,status='pass',stats=actual,comparison='all output bytes' if len(observed)<=65536 else 'first 65536 bytes plus full FNV-1a and metadata/band counts'))
            target_report=dict(status='pass',qemu_version=version,cases=native,elf_sha256=core.sha(elf.read_bytes()),audit=audit)
        sources=set(c_sources+[Path(__file__),ROOT/'scripts/validate-hp1020-image-core.py',ROOT/'scripts/build-hp1020-image-target.sh',SRC/'reference.c',full/'jbig.c',full/'jbig_ar.c'])
        sources.update(SRC.rglob('*.h'));sources.update(SEM.glob('*.h'));sources.update((core.VENDOR/'libjbig').glob('*.h'))
        sources.update(SRC.glob('*.c'));sources.update(SRC.glob('*.ld'))
        sources.update([full/'jbig.h',full/'jbig_ar.h',SEM/'freestanding/memory.c',
            ROOT/'scripts/hp1020_qemu_ram.py',ROOT/'scripts/hp1020_xtensa_call0.py',ROOT/'scripts/hp1020_xtensa_properties.py'])
        report=dict(status='pass',cases=cases,target=target_report,
            source_sha256={str(p.relative_to(ROOT)):core.sha(p.read_bytes()) for p in sorted(sources)},
            sample_sha256={str(p.relative_to(ROOT)):core.sha(p.read_bytes()) for p in sorted((ROOT/'analysis/samples/generated').glob('*.zjs'))},
            fixture_sha256={str(p.relative_to(ROOT)):core.sha(p.read_bytes()) for p in sorted((OUT/'fixtures').glob('*.jbg'))},
            scope='Complete ZjStream files pass through the open semantic parser, narrow page planner and open streaming decoder into packed image bands. Host output matches every byte from the original full JBIG decoder.',
            limits='Software pages only, separate from original native lifecycles. Compressed input remains in the caller arena. One decode per page, with copy count retained as metadata. No stock raw queue, DMA, physical format proof, engine, USB, boot or printing.')
        name='page-validation' if args.target else 'page-host-validation'
        (OUT/f'{name}.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
        (OUT/f'{name}.md').write_text('# Open complete-file image path\n\nStatus: pass. '+report['scope']+'\n\n'
            +f"{len(cases)} host cases; {len(target_report['cases']) if target_report else 0} target cases. Complete-file fragmentation, 6/13/64 BID splits, differing images across pages/documents, exact retained BIHs, paused output and strict default padding are checked.\n\n"+report['limits']+'\n')
        print(f"image pages: {len(cases)} host cases; target={len(target_report['cases']) if target_report else 'not run'}")
if __name__=='__main__':main()
