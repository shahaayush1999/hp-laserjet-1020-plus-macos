#!/usr/bin/env python3
"""Open C decoder-to-ring delivery, compared with original bounded ownership.

Software consumer readiness, acceptance/completion and interleaving are explicit.
The fixture is synthetic RAM, never a firmware upload or native page lifecycle.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import struct
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('image_checks_ring',ROOT/'scripts/validate-hp1020-image-core.py')
core=importlib.util.module_from_spec(spec);sys.modules[spec.name]=core;spec.loader.exec_module(core)
SRC=core.SRC;OUT=core.OUT
PHASES={'prepared':0,'fill_published':1,'nonfinal_withheld':2,'full_ring_producer_blocked':3,
    'output_accounted_still_owned':4,'accepted_without_completion_still_blocked':5,
    'descriptor_released':6,'no_remaining_data':7}


def original_trace(case):
    return [[PHASES[e['phase']],*e['indices'],*e['remaining'],
        *[value for descriptor in e['descriptors'] for value in descriptor]]
        for e in case['events'] if e['phase'] in PHASES]


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--target',action='store_true');args=ap.parse_args()
    oracle_path=ROOT/'analysis/hardware-boundary/software-ring.json'
    oracle_bytes=oracle_path.read_bytes();oracle=json.loads(oracle_bytes)
    assert oracle['status']=='pass' and oracle['completed_page_lifecycles']==0
    assert oracle['stock_elf_sha256']==core.sha((ROOT/'analysis/sihp1020.elf').read_bytes())
    if args.target:
        for name,digest in oracle['source_sha256'].items():
            assert core.sha((ROOT/name).read_bytes())==digest,('stale original ring oracle source',name)
    sources={Path(__file__),ROOT/'scripts/validate-hp1020-image-core.py',ROOT/'scripts/build-hp1020-image-target.sh'}
    sources.update(ROOT/'scripts'/name for name in ('hp1020_qemu_ram.py','hp1020_xtensa_call0.py',
        'hp1020_xtensa_properties.py','check-hp1020-c-compiler-profile.py'))
    sources.update(SRC.glob('*.c'));sources.update(SRC.glob('*.h'));sources.update(SRC.glob('*.ld'))
    sources.update((SRC/'freestanding').glob('*.h'))
    sources.update((ROOT/'open-firmware/semantic-core').rglob('*.c'))
    sources.update((ROOT/'open-firmware/semantic-core').rglob('*.h'))
    sources.update((core.VENDOR/'libjbig').glob('*.h'))
    sources.update(core.VENDOR/'libjbig'/name for name in ('jbig85.c','jbig_ar.c'))
    sources.update(ROOT/'vendor/foo2zjs-source'/name for name in ('jbig.c','jbig_ar.c','jbig.h','jbig_ar.h'))
    tested={str(p.relative_to(ROOT)):core.sha(p.read_bytes()) for p in sorted(sources)}
    cases,targets=[],[]
    fixtures=OUT/'ring-fixtures';fixtures.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='hp1020-image-ring-',dir='/tmp') as directory:
        temp=Path(directory);host=temp/'host';reference=temp/'reference'
        flags=['clang','-std=c11','-O1','-g','-fno-common','-Wall','-Wextra','-Werror','-fsanitize=address,undefined']
        core.command(flags+['-DHP1020_IMAGE_HOST_CHECK','-I'+str(SRC),'-I'+str(core.VENDOR/'libjbig'),
            SRC/'hp1020_image.c',SRC/'hp1020_image_ring.c',SRC/'ring-fixture.c',SRC/'host-ring-check.c',
            core.VENDOR/'libjbig/jbig85.c',core.VENDOR/'libjbig/jbig_ar.c','-o',host])
        full=ROOT/'vendor/foo2zjs-source'
        core.command(flags+['-I'+str(full),SRC/'reference.c',full/'jbig.c',full/'jbig_ar.c','-o',reference])
        short=fixtures/'9600x17-stripe128-edges.jbg'
        pixels=core.pattern(9600,17,'edges');(temp/'raw').write_bytes(pixels)
        assert core.sha(pixels)==oracle['sequence_image']['sha256']
        core.command([reference,'encode',temp/'raw',short,9600,17,128])
        specs=[(9600,17,'edges',short),(9600,132,'edges',OUT/'fixtures/9600x132-stripe128-edges.jbg'),
            (1024,129,'repeat',OUT/'fixtures/1024x129-stripe128-repeat.jbg'),
            (512,33,'noise',OUT/'fixtures/512x33-stripe4-noise.jbg'),
            (32,8,'black',OUT/'fixtures/32x8-stripe4-black.jbg'),
            (16384,4,'edges',OUT/'fixtures/16384x4-stripe128-edges.jbg')]
        for width,rows,kind,path in specs:
            bie=path.read_bytes();assert struct.unpack_from('>II',bie,4)==(width,rows)
            info=json.loads(core.command([reference,'decode',path,temp/'oracle']))
            expected=(temp/'oracle').read_bytes()
            assert expected==core.pattern(width,rows,kind)
            stride=width//8;capacity=(8192//stride)&~3;slot=capacity*stride
            total_bands=(rows+capacity-1)//capacity
            for fill in (0,204):
                for fragment in (1,7,65536):
                    data=json.loads(core.command([host,path,fragment,fill,temp/'capture',temp/'storage']))
                    stats,trace=data['stats'],data['trace']
                    assert stats[0:7]==[2,0,rows,rows,rows,total_bands,total_bands],(width,rows,fill,fragment,stats)
                    assert stats[7:9]==[len(expected),core.fnv(expected)]
                    assert stats[9]==max(0,total_bands-4)
                    assert stats[10:12]==[0,1] and stats[12]==info['consumed']
                    assert stats[13]==len(trace) and stats[17:21]==[0,1,capacity,slot]
                    assert stats[21:24]==[total_bands&3]*3
                    assert (temp/'capture').read_bytes()==expected
                    memory=bytearray([fill])*32800
                    for i,first in enumerate(range(0,rows,capacity)):
                        band=expected[first*stride:min(rows,first+capacity)*stride]
                        at=16+(i&3)*slot;memory[at:at+len(band)]=band
                    assert (temp/'storage').read_bytes()==memory
                    if rows==17 and width==9600:
                        original=next(c for c in oracle['sequences'] if c['fill']==fill)
                        assert trace==original_trace(original),('original ownership differs',fill,fragment,trace)
                    name=f'{width}x{rows}-{kind}/fill={fill}/fragment={fragment}'
                    cases.append(dict(case=name,status='pass',width_bits=width,rows=rows,fill=fill,fragment=fragment,
                        input_sha256=core.sha(bie),output_sha256=core.sha(expected),storage_sha256=core.sha(memory),
                        stats=stats,trace=trace,original_trace_equal=rows==17 and width==9600))
                    targets.append((name,bie,fragment,fill,stats,trace,expected,bytes(memory)))
        controls=[]
        for which in range(11):
            assert core.command([host,which]).strip()=='1',which
            controls.append(dict(case=which,status='pass',sticky_error=True,owned_storage_preserved=True))
        target_report=None
        if args.target:
            core.command([ROOT/'scripts/build-hp1020-image-target.sh'])
            elf=OUT/'target/target-check.elf';program,audit=core.audit_target(elf)
            from hp1020_qemu_ram import QemuRAM
            native=[]
            with QemuRAM() as q:
                q.load(elf);version=q.version
                for name,bie,fragment,fill,stats,trace,expected,memory in targets:
                    q.put(program.symbols['hp1020_ring_input'],bie)
                    assert q.call0(program.symbols['hp1020_ring_run'],[len(bie),fragment,fill,0])==2
                    actual=list(struct.unpack('>24I',q.read(program.symbols['hp1020_ring_stats'],96)))
                    assert actual[:14]+actual[16:]==stats[:14]+stats[16:],(name,actual,stats)
                    raw=q.read(program.symbols['hp1020_ring_trace'],len(trace)*72)
                    assert list(struct.iter_unpack('>18I',raw))==[tuple(t) for t in trace],name
                    assert q.read(program.symbols['hp1020_ring_capture'],len(expected))==expected,name
                    assert q.read(program.symbols['hp1020_ring_storage'],len(memory))==memory,name
                    native.append(dict(case=name,status='pass',stats=actual,all_output_bytes_equal=True,
                        all_storage_bytes_equal=True,ownership_trace_equal=True))
                for which in range(11):
                    assert q.call0(program.symbols['hp1020_ring_api_control'],[which])==1,which
            a4=next(c['stats'] for c in native if c['case']=='9600x17-edges/fill=0/fragment=7')
            target_report=dict(status='pass',cases=native,api_controls=11,qemu_version=version,
                elf_sha256=core.sha(elf.read_bytes()),audit=audit,
                a4_ring_state_bytes=a4[15],a4_component_storage_bytes=sum(a4[14:17]),
                memory_scope='Image state, ring state, two history rows, decoder band and four output slots; excludes code, stack, caller input and fixture arrays')
    assert all(core.sha((ROOT/name).read_bytes())==digest for name,digest in tested.items()),'source changed during execution'
    assert oracle_path.read_bytes()==oracle_bytes,'original oracle changed during execution'
    report=dict(status='pass',cases=cases,api_controls=controls,target=target_report,
        source_sha256=tested,stock_ring_report_sha256=core.sha(oracle_bytes),
        stock_ring_source_sha256=oracle['source_sha256'],completed_native_page_lifecycles=0,
        fixture_sha256={str(path.relative_to(ROOT)):core.sha(path.read_bytes()) for _,_,_,path in specs},
        scope='One compiled C call decodes original JBIG into its own four-slot software output ring. Every output and storage byte is checked; acceptance and completion are separate explicit consumer actions.',
        limits='Serialized RAM experiment, with an explicit simulated consumer. No original owner/allocator integration, native scheduling, interrupts, hardware writes, physical pixel-format proof, page cleanup or printing. Odd-row images remain outside the stricter ZjStream page planner; this does not broaden that grammar.')
    name='ring-validation' if args.target else 'ring-host-validation'
    (OUT/f'{name}.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    (OUT/f'{name}.md').write_text('# Compiled software decoder and output ring\n\nStatus: pass. '+report['scope']+'\n\n'
        +f'{len(cases)} sanitized host cases, {len(target_report["cases"]) if target_report else 0} target cases, 11 host API rejection controls and {11 if target_report else 0} target API controls. Six 17-row host cases match the original bounded ownership trace exactly.\n\n'
        +report['limits']+'\n')
    print(f'image ring: {len(cases)} host cases, target={len(target_report["cases"]) if target_report else "not run"}; 11 API controls; no native page lifecycles')


if __name__=='__main__':main()
