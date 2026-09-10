#!/usr/bin/env python3
"""Differential streaming JBIG checks; host files and optional synthetic QEMU RAM only."""
from __future__ import annotations
import argparse
import functools
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import struct
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'open-firmware/image-core'
VENDOR=ROOT/'vendor/jbigkit-2.1'
OUT=ROOT/'analysis/open-firmware-model/image-core'
PREFIX=os.environ.get('XTENSA_PREFIX','/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf')

def sha(data): return hashlib.sha256(data).hexdigest()
@functools.lru_cache(maxsize=16)
def fnv(data):
    h=2166136261
    for b in data: h=(h^b)*16777619&0xffffffff
    return h
def command(args):
    r=subprocess.run(list(map(str,args)),capture_output=True,text=True,
        env={**os.environ,'ASAN_OPTIONS':'detect_leaks='+('0' if sys.platform=='darwin' else '1'),
             'UBSAN_OPTIONS':'halt_on_error=1'},timeout=60)
    assert r.returncode==0 and not r.stderr,(args,r.returncode,r.stdout,r.stderr)
    return r.stdout

def verify_vendor(temp):
    p=json.loads((VENDOR/'provenance.json').read_text())
    for name,h in p['files'].items(): assert sha((VENDOR/name).read_bytes())==h['local_sha256'],name
    copy=temp/'original'; shutil.copytree(VENDOR,copy)
    command(['patch','--batch','-R','-p1','-d',copy,'-i',VENDOR/'LOCAL-CHANGES.patch'])
    for name,h in p['files'].items(): assert sha((copy/name).read_bytes())==h['upstream_sha256'],name
    return p

def sample_bie(path):
    raw=path.read_bytes(); pos=raw.index(b'JZJZ')+4; parts=[]
    while pos+16<=len(raw):
        size,kind,count,reserved,sig=struct.unpack_from('>IIIHH',raw,pos)
        assert size>=16 and pos+size<=len(raw) and sig==0x5a5a
        if kind in (4,5): parts.append(raw[pos+16:pos+size])
        pos+=size
        if kind==1: break
    assert len(parts)>=2 and len(parts[0])==20
    return b''.join(parts)

def pattern(width,height,kind):
    stride=(width+7)//8; data=bytearray(stride*height)
    rng=random.Random(1020+width+height)
    for y in range(height):
        for x in range(width):
            if kind=='white': bit=0
            elif kind=='black': bit=1
            elif kind=='noise': bit=rng.randrange(2)
            elif kind=='repeat': bit=((x//7)^(x//31))&1
            else: bit=((x//11)^(y//3)^(x==y)^(x==width-1-y))&1
            if bit: data[y*stride+x//8]|=0x80>>(x%8)
    return bytes(data)

def audit_target(path):
    # Modern .xt.prop: BE address/size/flags triples; INSN=2, LITERAL=1.
    # Pinned binutils include/elf/xtensa.h property_table_entry and flags:
    # https://github.com/espressif/binutils-gdb/blob/0104f7d3c1/include/elf/xtensa.h
    # Keep this audit local; older stock .xt.insn interpretation is unchanged.
    from hp1020_xtensa_properties import properties,section_bytes
    from hp1020_xtensa_call0 import Program
    data=path.read_bytes(); sections,_=properties(data); sec=sections['.xt.prop']
    raw=data[sec['offset']:sec['offset']+sec['size']]; assert len(raw)%12==0
    entries=list(struct.iter_unpack('>III',raw)); ranges=[]; literals=[]
    for address,size,flags in sorted(entries):
        if size and flags&1: literals.append((address,address+size))
        if not size or not flags&2: continue
        assert not flags&5
        assert sections['.text']['address']<=address<address+size<=sections['.text']['address']+sections['.text']['size']
        if ranges and ranges[-1][0]+ranges[-1][1]==address:
            ranges[-1]=(ranges[-1][0],ranges[-1][1]+size)
        else:
            assert not ranges or ranges[-1][0]+ranges[-1][1]<=address
            ranges.append((address,size))
    assert ranges
    program=Program(path,PREFIX); program.instructions={}; program.annotated_code=ranges
    allowed=set('add add.n addi addi.n addmi addx2 addx4 addx8 and bbci bbsi beq beqi beqz beqz.n bge bgei bgeu bgeui bgez blt blti bltu bltui bltz bne bnei bnez bnez.n bnone bany ball bnall call0 callx0 extui j jx l16si l16ui l32i l32i.n l32r l8ui mov.n moveqz movgez movi movi.n movltz movnez mull neg nsau nop nop.n or ret ret.n s16i s32i s32i.n s8i sll slli sra srai srl srli ssl ssr sub subx2 subx4 subx8 xor'.split())
    listings=[]; traps=[]
    for address,size in ranges:
        assert not any(address<b and a<address+size for a,b in literals)
        listing=command([PREFIX+'-objdump','-d',f'--start-address={address}',f'--stop-address={address+size}',path])
        listings.append(listing)
        pc=address
        for at,(op,args,rawbytes) in Program.parse(listing):
            assert at==pc and rawbytes==section_bytes(data,sections,at,len(rawbytes))
            if op=='ill':
                assert at==program.symbols['__udivsi3']+0x41 and rawbytes==bytes(3)
                traps.append(hex(at))  # Original libgcc divide-by-zero trap, never image code.
            else: assert op in allowed,(hex(at),op)
            program.instructions[at]=(op,args,rawbytes); pc+=len(rawbytes)
        assert pc==address+size
    (path.parent/'annotated-disassembly.txt').write_text(''.join(listings))
    return program,dict(instructions=len(program.instructions),instruction_bytes=sum(n for _,n in ranges),
        division_by_zero_traps=traps,
        instruction_ranges=len(ranges),opcodes=sorted({v[0] for v in program.instructions.values()}),
        text_bytes=sections['.text']['size'],rodata_bytes=sections['.rodata']['size'],
        test_fixture_bss_bytes=sections['.bss']['size'],scope='All annotated code uses the conservative standard ISA; unused encoder code remains. Not a device instruction trace.')

def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('--target',action='store_true'); args=ap.parse_args()
    OUT.mkdir(parents=True,exist_ok=True); (OUT/'fixtures').mkdir(exist_ok=True)
    cases=[]; targets=[]; normalization=[]; consumed_by_input={}
    with tempfile.TemporaryDirectory(prefix='hp1020-image-') as directory:
        temp=Path(directory); provenance=verify_vendor(temp)
        cc=os.environ.get('CC','clang'); host=temp/'host'; reference=temp/'reference'
        flags=[cc,'-std=c11','-O1','-g','-fno-common','-Wall','-Wextra','-Werror','-fsanitize=address,undefined']
        command(flags+['-DHP1020_IMAGE_HOST_CHECK','-I'+str(SRC),'-I'+str(VENDOR/'libjbig'),
            SRC/'hp1020_image.c',SRC/'fixture.c',SRC/'host-check.c',VENDOR/'libjbig/jbig85.c',VENDOR/'libjbig/jbig_ar.c','-o',host])
        full=ROOT/'vendor/foo2zjs-source'
        command(flags+['-I'+str(full),SRC/'reference.c',full/'jbig.c',full/'jbig_ar.c','-o',reference])
        inputfile=temp/'input.jbg'; capture=temp/'capture'; oracle=temp/'oracle'; packed=temp/'packed'
        def run(name,data,fragment=7,rows=4,fill=204,error=None,expected=None,target=False):
            inputfile.write_bytes(data)
            actual=json.loads(command([host,inputfile,fragment,rows,fill,capture,1]))
            assert actual[0]==(2 if error is None else error),(name,actual,error)
            assert actual[10]==0,(name,'API/input invariant',actual)
            if len(data)>=20: assert actual[16:18]==[1,1],(name,'guards/error persistence',actual)
            observed=capture.read_bytes()
            if expected is not None:
                assert observed==expected,(name,'output bytes differ')
                assert actual[5]==consumed_by_input[sha(data)],(name,'different end-of-image boundary')
                assert actual[1]==struct.unpack_from('>I',data,8)[0]
                assert actual[4]==len(expected) and actual[3]==fnv(expected)
                assert actual[2]==(actual[1]+rows-1)//rows and actual[7]==1
                assert actual[8]==(actual[1]-1)%rows+1
            cases.append(dict(case=name,result=actual[0],input_sha256=sha(data),output_sha256=sha(observed),
                fragment=fragment,band_rows=rows,flags=fill,stats=actual,status='pass'))
            if target: targets.append((name,data,fragment,rows,fill,actual,observed))
            return actual
        def verify(name,bie,raw=None):
            inputfile.write_bytes(bie); info=json.loads(command([reference,'decode',inputfile,oracle]))
            original=oracle.read_bytes()
            if raw is not None: assert raw==original,(name,'full encoder/decoder round trip')
            h=bytearray(bie); assert h[18:20]==b'\x03\x5c';h[18:20]=b'\x00\x48'
            inputfile.write_bytes(h); norm=json.loads(command([reference,'decode',inputfile,oracle]))
            assert norm==info and oracle.read_bytes()==original,(name,'normalization changed data')
            normalization.append(dict(case=name,original_bih=bie[:20].hex(),normalized_bih=bytes(h[:20]).hex(),
                decoded_sha256=sha(original),consumed=info['consumed'],bytes=len(original)))
            consumed_by_input[sha(bie)]=info['consumed']
            return original,info['consumed']
        for p in sorted((ROOT/'analysis/samples/generated').glob('*.zjs')):
            bie=sample_bie(p); raw,consumed=verify(p.stem,bie)
            padding=bie[consumed:]; assert 16<=len(padding)<=19 and not any(padding)
            if struct.unpack_from('>I',bie,4)[0]>16384:
                run(p.stem+'/width-limit',bie,error=4,target=True);continue
            for fragment in (1,7,65536):
                run(p.stem+f'/fragment={fragment}',bie,fragment,expected=raw,
                    target=p.stem in ('matrix-a4_default','matrix-a4_600x600') and fragment==7)
        specs=[(1,1,1,'black'),(7,3,1,'white'),(13,5,4,'edges'),(32,8,4,'black'),
            (257,129,128,'noise'),(512,33,4,'noise'),(1024,129,128,'repeat'),
            (9600,132,128,'edges'),(16384,4,128,'edges')]
        fixtures={}
        for w,h,stripe,kind in specs:
            name=f'{w}x{h}-stripe{stripe}-{kind}'; raw=pattern(w,h,kind);packed.write_bytes(raw)
            encoded=OUT/'fixtures'/f'{name}.jbg'
            command([reference,'encode',packed,encoded,w,h,stripe]);bie=encoded.read_bytes()
            raw,consumed=verify(name,bie); assert consumed==len(bie)
            fixtures[name]=(bie,raw)
            for fragment in (1,7,64,65536):
                for fill in (0,204):
                    run(name+f'/fragment={fragment}/fill={fill}',bie,fragment,fill=fill,expected=raw,
                        target=fragment==7)
            # One row per band forces all row/stripe termination resumes.
            run(name+'/single-row-band',bie,1,rows=1,expected=raw,target=True)
        bie,raw=fixtures['257x129-stripe128-noise']
        for flag,label in ((0x100,'history-short'),(0x200,'band-short'),(0x400,'premature-release'),(0x800,'null-input')):
            run(label,bie,fill=204|flag,error=4 if flag<0x400 else 7,target=True)
        for rows in (0,8193,0xffffffff): run(f'band-limit/{rows}',bie,rows=rows,error=4,target=True)
        for offset,value in ((0,1),(1,1),(2,2),(3,1),(16,15),(17,1),(18,0),(19,0x48),(19,0x5e),(19,0x7c)):
            b=bytearray(bie);b[offset]=value
            run(f'unsupported-header/{offset}/{value}',bytes(b),error=5,target=True)
        for offset in (4,8,12):
            for value in (0,16385,0xffffffff):
                b=bytearray(bie);struct.pack_into('>I',b,offset,value)
                run(f'dimension/{offset}/{value}',bytes(b),error=3 if value==0 else 4,target=True)
        tiny,_=fixtures['13x5-stripe4-edges']
        for length in range(len(tiny)):
            run(f'truncated/{length}',tiny[:length],fragment=1,error=6,target=length in (19,20,len(tiny)-1))
        marker_cases=[('abort',b'\xff\x04',3),('unknown',b'\xff\x01',3),
            ('newlen-without-option',b'\xff\x05'+struct.pack('>I',1),3),
            ('atmove-invalid',b'\xff\x06'+struct.pack('>I',0)+b'\x01\x00',3),
            ('atmove-two', (b'\xff\x06'+struct.pack('>I',0)+b'\x08\x00')*2,5),
            ('comment-huge',b'\xff\x07'+struct.pack('>I',0xffffffff),6)]
        for name,marker,error in marker_cases:
            run('marker/'+name,tiny[:20]+marker,error=error,target=True)
        # Comments contain marker-looking bytes but must not change decoded rows.
        comment=b'\xff\x04\x00\xff\x06hello'
        with_comment=tiny[:20]+b'\xff\x07'+struct.pack('>I',len(comment))+comment+tiny[20:]
        verify('comment-fragmented',with_comment,fixtures['13x5-stripe4-edges'][1])
        run('comment-fragmented',with_comment,1,expected=fixtures['13x5-stripe4-edges'][1],target=True)
        # Syntax has no checksum: mutations may be valid images. Compare successful
        # outputs against the full oracle; do not label every mutation a rejection.
        rng=random.Random(1020); mutations=[]
        for i in range(32):
            b=bytearray(tiny); at=rng.randrange(20,len(b)); b[at]^=1<<rng.randrange(8)
            inputfile.write_bytes(b)
            actual=json.loads(command([host,inputfile,7,4,204,capture,1]))
            assert actual[10]==0 and actual[16:18]==[1,1]
            if actual[0]==2:
                info=json.loads(command([reference,'decode',inputfile,oracle]));assert capture.read_bytes()==oracle.read_bytes()
            else: assert actual[0] in (3,5,6)
            mutations.append(dict(index=i,offset=at,input_sha256=sha(b),result=actual[0],status='pass'))
        target_report=None
        if args.target:
            command([ROOT/'scripts/build-hp1020-image-target.sh'])
            elf=OUT/'target/target-check.elf'; first=sha(elf.read_bytes()); map_first=sha((elf.parent/'target-check.map').read_bytes())
            command([ROOT/'scripts/build-hp1020-image-target.sh'])
            assert first==sha(elf.read_bytes()) and map_first==sha((elf.parent/'target-check.map').read_bytes())
            program,audit=audit_target(elf)
            from hp1020_qemu_ram import QemuRAM
            from hp1020_xtensa_call0 import Machine
            native=[]
            with QemuRAM() as q:
                version=q.version;q.load(elf)
                for name,data,fragment,rows,fill,expected,observed in targets:
                    q.put(program.symbols['hp1020_image_input'],data)
                    returned=q.call0(program.symbols['hp1020_image_run'],[len(data),fragment,rows,fill])
                    actual=list(struct.unpack('>24I',q.read(program.symbols['hp1020_image_stats'],96)))
                    assert returned==actual[0]
                    # Only sizeof(state) differs between the 64-bit host and 32-bit target.
                    assert actual[:14]+actual[15:]==expected[:14]+expected[15:],(name,actual,expected)
                    captured=q.read(program.symbols['hp1020_image_capture'],min(len(observed),65536))
                    assert captured==observed[:65536],name
                    native.append(dict(case=name,status='pass',stats=actual,comparison='all output bytes' if len(observed)<=65536 else 'first 65536 bytes plus full FNV-1a and row/band counts'))
            # Independent strict instruction interpreter on a small nonblank page.
            small=next(t for t in targets if t[0]=='13x5-stripe4-edges/fragment=7/fill=204')
            name,data,fragment,rows,fill,expected,observed=small
            m=Machine(program);m.put(program.symbols['hp1020_image_input'],data)
            returned=m.run([len(data),fragment,rows,fill])
            actual=[m.read(program.symbols['hp1020_image_stats']+4*i,4) for i in range(24)]
            assert actual[:14]+actual[15:]==expected[:14]+expected[15:] and returned==2
            assert bytes(m.read(program.symbols['hp1020_image_capture']+i,1) for i in range(len(observed)))==observed
            target_report=dict(status='pass',qemu_version=version,elf_sha256=first,map_sha256=map_first,reproducible=True,
                cases=native,audit=audit,interpreter=dict(case=name,instructions=m.steps,status='pass'),
                state_bytes=actual[14],a4_history_and_band_bytes=7200,a4_state_history_band_bytes=actual[14]+7200)
        source_files=list(SRC.rglob('*.c'))+list(SRC.rglob('*.h'))+list(SRC.glob('*.ld'))+list((VENDOR/'libjbig').glob('*.c'))+list((VENDOR/'libjbig').glob('*.h'))
        source_files += [Path(__file__),ROOT/'scripts/build-hp1020-image-target.sh',full/'jbig.c',full/'jbig.h',full/'jbig_ar.c',full/'jbig_ar.h',ROOT/'scripts/hp1020_qemu_ram.py',ROOT/'scripts/hp1020_xtensa_call0.py',ROOT/'scripts/hp1020_xtensa_properties.py',ROOT/'open-firmware/semantic-core/freestanding/memory.c']
        source_files += list((ROOT/'open-firmware/semantic-core').glob('*.h')) + [ROOT/'open-firmware/semantic-core/hp1020_semantic.c',ROOT/'open-firmware/semantic-core/hp1020_page_plan.c']
        report=dict(status='pass',cases=cases,normalization=normalization,mutations=mutations,target=target_report,
            source_sha256={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sorted(source_files)},
            fixture_sha256={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sorted((OUT/'fixtures').glob('*.jbg'))},
            sample_sha256={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sorted((ROOT/'analysis/samples/generated').glob('*.zjs'))},
            vendor_archive_sha256=provenance['archive_sha256'],
            scope='Open streaming software JBIG decoding and packed-row bands. Full host byte comparisons against the existing full decoder and generated source pixels. No stock custom code, DMA, MMIO, USB, engine or printing.',
            limits='This report tests the decoder independently; the semantic-page bridge has separate validation. No stock raw queue integration. Physical pixel format, CPU throughput, printer RAM placement, cache visibility and output remain unproven. Existing parser still stores compressed input. Output before DONE is provisional; JBIG has no checksum.')
        name='validation' if args.target else 'host-validation'
        (OUT/f'{name}.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
        (OUT/f'{name}.md').write_text('# Open streaming image decoder validation\n\nStatus: pass. '+report['scope']+'\n\n'
            +f'{len(cases)} focused cases, {len(normalization)} original/normalized full-decoder comparisons and {len(mutations)} separately classified mutations. '
            +'Host runs use ASan and UBSan, row/band guards, input poisoning between feeds, paused-consumer checks and sticky error checks.\n\n'
            +(f"QEMU: {len(target_report['cases'])} cases; two identical target builds; {target_report['interpreter']['instructions']:,} instructions in the separate small-page interpreter check. A4 state/history/four-row band storage: {target_report['a4_state_history_band_bytes']:,} bytes, excluding code, stack, caller input and test fixtures.\n\n" if target_report else 'Target execution was not requested in this host-only report.\n\n')
            +report['limits']+'\n')
        print(f"image core: {len(cases)} cases, {len(normalization)} normalization comparisons, {len(mutations)} mutations; target={'pass' if target_report else 'not run'}")

if __name__=='__main__': main()
