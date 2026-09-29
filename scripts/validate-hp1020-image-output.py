#!/usr/bin/env python3
"""Bounded document-to-output composition with an explicit software consumer."""
import argparse
import importlib.util
import json
from pathlib import Path
import struct
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('output_pages',ROOT/'scripts/validate-hp1020-image-pages.py')
pages=importlib.util.module_from_spec(spec);sys.modules[spec.name]=pages;spec.loader.exec_module(pages)
core=pages.core;SRC=pages.SRC;SEM=pages.SEM;OUT=pages.OUT


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--target',action='store_true');args=ap.parse_args()
    sources={Path(__file__),ROOT/'scripts/validate-hp1020-image-pages.py',ROOT/'scripts/validate-hp1020-image-core.py',
        ROOT/'scripts/build-hp1020-image-target.sh',ROOT/'scripts/check-hp1020-c-compiler-profile.py'}
    sources.update(ROOT/'scripts'/n for n in ('hp1020_qemu_ram.py','hp1020_xtensa_call0.py','hp1020_xtensa_properties.py'))
    sources.update(SRC.glob('*.c'));sources.update(SRC.glob('*.h'));sources.update(SRC.glob('*.ld'))
    sources.update((SRC/'freestanding').glob('*.h'));sources.update(SEM.rglob('*.c'));sources.update(SEM.rglob('*.h'))
    sources.update((core.VENDOR/'libjbig').glob('*.h'))
    sources.update(core.VENDOR/'libjbig'/n for n in ('jbig85.c','jbig_ar.c'))
    sources.update(ROOT/'vendor/foo2zjs-source'/n for n in ('jbig.c','jbig_ar.c','jbig.h','jbig_ar.h'))
    tested={str(p.relative_to(ROOT)):core.sha(p.read_bytes()) for p in sorted(sources)}
    base_path=ROOT/'analysis/samples/generated/matrix-a4_default.zjs';base_bytes=base_path.read_bytes()
    base=pages.chunks(base_bytes)
    fixtures=OUT/'output-fixtures';fixtures.mkdir(exist_ok=True)
    cases=[];targets=[];fixture_paths=[]
    with tempfile.TemporaryDirectory(prefix='hp1020-image-output-',dir='/tmp') as directory:
        temp=Path(directory);host=temp/'host';reference=temp/'reference';full=ROOT/'vendor/foo2zjs-source'
        flags=['clang','-std=c11','-O1','-g','-fno-common','-Wall','-Wextra','-Werror','-fsanitize=address,undefined']
        implementation=[SRC/n for n in ('hp1020_image.c','hp1020_image_page.c','hp1020_image_stream.c',
            'hp1020_image_ring.c','hp1020_image_output.c','output-fixture.c','host-output-check.c')]
        implementation += [SEM/'hp1020_semantic.c',SEM/'hp1020_page_plan.c',
            core.VENDOR/'libjbig/jbig85.c',core.VENDOR/'libjbig/jbig_ar.c']
        core.command(flags+['-DHP1020_IMAGE_HOST_CHECK','-I'+str(SRC),'-I'+str(SEM),
            '-I'+str(core.VENDOR/'libjbig')]+implementation+['-o',host])
        core.command(flags+['-I'+str(full),SRC/'reference.c',full/'jbig.c',full/'jbig_ar.c','-o',reference])
        images={}
        for name,w,h,stripe,kind in (('small',32,8,4,'black'),('medium',9600,132,128,'edges'),
                ('wide',16384,4,128,'edges'),('partial',1024,260,128,'repeat'),('slim',64,12,4,'edges')):
            path=OUT/'fixtures'/f'{w}x{h}-stripe{stripe}-{kind}.jbg'
            raw=core.pattern(w,h,kind)
            if name in ('partial','slim'):
                path=fixtures/path.name;(temp/'pixels').write_bytes(raw)
                core.command([reference,'encode',temp/'pixels',path,w,h,stripe])
            info=json.loads(core.command([reference,'decode',path,temp/'oracle']))
            assert (temp/'oracle').read_bytes()==raw and info['consumed']==path.stat().st_size
            images[name]=(path.read_bytes(),raw);fixture_paths.append(path)

        def body(bie,splits=1,copies=1,tail=None):
            width,height=struct.unpack_from('>II',bie,4);items=bytearray(base[1][1])
            for off in range(0,len(items),12):
                ident=struct.unpack_from('>H',items,off+4)[0]
                values={4:copies,12:width,13:height,17:width//2,18:height}
                if ident in values:struct.pack_into('>I',items,off+8,values[ident])
            payload=bie[20:]+(bytes(16+((-len(bie[20:]))&3)) if tail is None else tail)
            chunks=[payload[len(payload)*i//splits:len(payload)*(i+1)//splits] for i in range(splits)]
            assert all(chunks)
            return [(2,bytes(items),base[1][2],base[1][3]),(4,bie[:20],0,0)]+[
                (5,p,0,0) for p in chunks]+[(6,b'',0,0),(3,b'',0,0)]

        def doc(parts):return b'JZJZ'+pages.pack([base[0]]+sum(parts,[])+[base[-1]])

        def run(name,data,image_names,fragment=7,packet=4096,fill=204,mode=0,error=0,reject=0xffffffff,copies=None,seed_counter=0):
            raw_pages=[images[n][1] for n in image_names];expected=b''.join(raw_pages)
            (temp/'input').write_bytes(data)
            observed=json.loads(core.command([host,temp/'input',fragment,packet,fill,mode,reject,temp/'capture',temp/'storage',seed_counter]))
            stats,writes,plans=observed['stats'],observed['writes'],observed['pages']
            capture=(temp/'capture').read_bytes();storage=(temp/'storage').read_bytes()
            assert stats[0]==error,(name,stats,error)
            assert stats[10:12]==[0,1] and stats[19]==1,(name,'guards/invariants/sticky error',stats)
            assert len(capture)<=262144 and stats[5:7]==[len(capture),core.fnv(capture)]
            assert stats[7]==stats[25] and stats[8]<=stats[7] and stats[20]==len(writes)==stats[4]
            assert capture==expected[:len(capture)],(name,'output is not the exact source prefix')
            memory=bytearray([fill])*32768
            for index,first,rows,slot,stride in writes:
                at=slot*((8192//stride)&~3)*stride
                band=raw_pages[index][first*stride:(first+rows)*stride]
                assert len(band)==rows*stride
                memory[at:at+len(band)]=band
            assert storage==memory,(name,'unpublished storage changed')
            if not error:
                assert capture==expected and stats[2]==stats[17]==stats[28]==len(image_names)
                assert stats[7]==stats[8]==stats[4] and stats[16]==stats[18]==stats[22]==0 and stats[23]==1
                assert stats[27]==stats[4]
                for index,(p,key) in enumerate(zip(plans,image_names)):
                    width,height=struct.unpack_from('>II',images[key][0],4);stride=width//8;capacity=(8192//stride)&~3
                    assert p==[stride,height,(copies or [1]*len(plans))[index],capacity,
                        (height+capacity-1)//capacity,height,height],(name,index,p)
            else:
                assert stats[23]==0 and stats[26]==1
                if reject!=0xffffffff or mode==3:assert stats[18]>0,'consumer failure released owned buffers'
            if name.startswith('missing-end-doc'):
                assert stats[18]==4 and stats[17]==0 and stats[5]==(33-4)*4800
            if name=='consumer/after=1':
                assert stats[7:9]==[1,0] and stats[18]==4,(name,stats)
            cases.append(dict(case=name,status='pass',expected_result=error,stats=stats,pages=plans,writes=writes,
                fragment=fragment,packet=packet,fill=fill,consumer_mode=mode,reject_after=reject,seed_counter=seed_counter,
                input_sha256=core.sha(data),input_bytes=len(data),output_sha256=core.sha(capture),
                storage_sha256=core.sha(storage),full_output_equal=not error,source_prefix_equal=True))
            targets.append((name,data,fragment,packet,fill,mode,reject,seed_counter,observed,capture,storage))

        order=['medium','wide','small','partial','small']
        mixed=doc([body(images[n][0],splits=13 if n=='medium' else 1) for n in order])
        for fill in (0,204):
            for mode in (0,1,2):
                for fragment,packet in ((1,19),(7,4096),(65552,65552)):
                    run(f'mixed/fill={fill}/consumer={mode}/fragment={fragment}',mixed,order,fragment,packet,fill,mode)
        for mode in (0,1,2):
            order=['partial','small','medium','wide']
            data=doc([body(images[n][0]) for n in order[:2]])+doc([])+doc([body(images[n][0]) for n in order[2:]])
            run(f'documents/consumer={mode}',data,order,mode=mode)
        run('empty-document',doc([]),[])
        run('copies-are-forwarded-metadata',doc([body(images['partial'][0],copies=3)]),['partial'],copies=[3])
        run('many-bid-boundaries',doc([body(images['medium'][0],splits=257)]),['medium'],fragment=1)
        run('page-metadata-reuse/16',doc([body(images['small'][0])]*16),['small']*16)
        run('page-metadata-reuse/17',doc([body(images['small'][0])]*17),['small']*17)
        many=['small' if i%2==0 else 'slim' for i in range(65)]
        run('page-metadata-reuse/65-mixed',doc([body(images[n][0]) for n in many]),many,mode=1)
        run('page-metadata-reuse/65-documents',b''.join(doc([body(images[n][0])]) for n in many),many,mode=2)
        for which in (1,2,3,4):
            run(f'counter-overflow/{which}',doc([body(images['small'][0])]),['small'],error=3,seed_counter=which)
        for mode in (0,1,2):run(f'partial-final-band/consumer={mode}',doc([body(images['partial'][0])]),['partial'],mode=mode)
        run('missing-end-doc',doc([body(images['medium'][0])])[:-16],['medium'],error=5)
        run('nonzero-padding',doc([body(images['medium'][0],tail=bytes(15)+b'\x01')]),['medium'],error=1)
        run('truncated-header',mixed[:-8],['medium','wide','small','partial','small'],error=5)
        for stop in (0,1,2,15):
            run(f'consumer/after={stop}',doc([body(images['medium'][0])]),['medium'],error=3,reject=stop)
        run('consumer/no-progress',doc([body(images['medium'][0])]),['medium'],mode=3,error=2)
        for stop in (0,1):run(f'final-drain/after={stop}',doc([body(images['small'][0])]),['small'],error=3,reject=stop)
        print(f'image output: {len(cases)} sanitized host cases passed',flush=True)
        target=None
        if args.target:
            core.command([ROOT/'scripts/build-hp1020-image-target.sh'])
            elf=OUT/'target/target-check.elf';program,audit=core.audit_target(elf)
            from hp1020_qemu_ram import QemuRAM
            native=[]
            with QemuRAM() as q:
                q.load(elf);version=q.version
                for name,data,fragment,packet,fill,mode,reject,seed_counter,observed,capture,storage in targets:
                    assert q.call0(program.symbols['hp1020_output_reset'],[fill,mode,reject])==0
                    assert q.call0(program.symbols['hp1020_output_seed_counter'],[seed_counter])==0
                    for pos in range(0,len(data),packet):
                        payload=data[pos:pos+packet];q.put(program.symbols['hp1020_output_input'],payload)
                        if q.call0(program.symbols['hp1020_output_feed'],[len(payload),fragment]):break
                    returned=q.call0(program.symbols['hp1020_output_finish'],[])
                    stats=list(struct.unpack('>40I',q.read(program.symbols['hp1020_output_stats'],160)))
                    assert returned==stats[0] and stats[:14]+stats[15:]==observed['stats'][:14]+observed['stats'][15:],(name,stats,observed)
                    for symbol,rows,width in (('hp1020_output_writes',observed['writes'],5),('hp1020_output_pages',observed['pages'],7)):
                        raw=q.read(program.symbols[symbol],len(rows)*width*4)
                        assert list(struct.iter_unpack('>'+str(width)+'I',raw))==[tuple(r) for r in rows],name
                    assert q.read(program.symbols['hp1020_output_capture'],len(capture))==capture,name
                    address=q.call0(program.symbols['hp1020_output_storage'],[])
                    assert q.read(address,32768)==storage,name
                    native.append(dict(case=name,status='pass',stats=stats,all_output_bytes_equal=True,
                        all_storage_bytes_equal=True,page_and_write_traces_equal=True))
                    if len(native)%10==0:print(f'image output: {len(native)}/{len(targets)} QEMU cases passed',flush=True)
            sizes={c['stats'][14]+c['stats'][15] for c in native};assert len(sizes)==1
            target=dict(status='pass',cases=native,qemu_version=version,elf_sha256=core.sha(elf.read_bytes()),
                state_and_memory_bytes=sizes.pop(),audit=audit)
    assert all(core.sha((ROOT/n).read_bytes())==h for n,h in tested.items()),'source changed during execution'
    report=dict(status='pass',cases=cases,target=target,source_sha256=tested,
        fixture_sha256={str(p.relative_to(ROOT)):core.sha(p.read_bytes()) for p in fixture_paths},
        sample_sha256={str(base_path.relative_to(ROOT)):core.sha(base_bytes)},completed_native_page_lifecycles=0,
        scope='Compiled bounded ZjStream parser, JBIG decoder and four-slot output ring with synchronous consumer progress. Exact pixels and entire output storage compared, with differing pages/documents and explicit completion ownership.',
        limits='Explicit software consumer supplies all output acceptance/completion. No device operations, scheduler, interrupt/cache integration, physical packing, printing or native lifecycle proof. Copies are forwarded metadata, not replayed output. Streaming page metadata is reused, with checked 32-bit counts; the retained-file parser keeps its independent 16-page limit. Late errors may follow already consumed rows and leave outstanding storage owned; caller must quiesce output before reuse.')
    name='output-validation' if args.target else 'output-host-validation'
    (OUT/f'{name}.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    (OUT/f'{name}.md').write_text('# Bounded document-to-output composition\n\nStatus: pass. '+report['scope']+'\n\n'
        +f'{len(cases)} sanitized host cases and {len(target["cases"]) if target else 0} QEMU cases.\n\n'
        +(f'Target state and fixed memory: {target["state_and_memory_bytes"]} bytes, excluding code, stack, caller packets and fixture captures.\n\n' if target else '')
        +report['limits']+'\n')
    print(f'image output: {len(cases)} host cases; target={len(target["cases"]) if target else "not run"}')


if __name__=='__main__':main()
