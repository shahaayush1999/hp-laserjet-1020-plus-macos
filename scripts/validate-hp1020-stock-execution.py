#!/usr/bin/env python3
"""Differential execution of original stock bytes against host memory/C oracles."""
import hashlib
import copy
import json
import os
from pathlib import Path
import random
import struct
import subprocess
import tempfile
from hp1020_xtensa_call0 import Program
from hp1020_xtensa_stock import StockMachine
from hp1020_stock_parser_harness import ParserHarness,CONTEXT,BOUNDARIES

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'analysis/open-firmware-model/stock-execution'
SOURCE=ROOT/'open-firmware/semantic-core'
RAM=0x22000000


def chunks(data):
    offset=data.index(b'JZJZ')+4;out=[]
    while True:
        size,kind,count,reserved,signature=struct.unpack_from('>IIIHH',data,offset)
        assert signature==0x5a5a and size>=16
        out.append((kind,data[offset+16:offset+size],count,reserved))
        offset+=size
        if kind==1:return out,offset


def chunk(kind,payload=b'',count=0,reserved=0):
    return struct.pack('>IIIHH',16+len(payload),kind,count,reserved,0x5a5a)+payload


def stream(parts):return b'JZJZ'+b''.join(chunk(*c) for c in parts)

def fnv(data):
    value=2166136261
    for b in data:value=(value^b)*16777619&0xffffffff
    return value


def main(libc_observer=None):
    program=Program(ROOT/'analysis/sihp1020.elf',os.environ.get('XTENSA_PREFIX','/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf'))
    totals={};steps=0;visited=set();opcodes=set();checks=[]
    def account(kind,m):
        nonlocal steps
        totals[kind]=totals.get(kind,0)+1;steps+=m.steps
        visited.update(m.visited);opcodes.update(m.opcodes)
    def memory(entry,ranges):
        return StockMachine(program,entry,ranges,[(RAM,1024)])
    def dump(m):
        data,off=m.span(RAM,1024);return bytes(data[off:off+1024])
    # Independent bytearray expectations, not reimplementations of the stock loops.
    for offset in range(8):
        for n in range(97):
            for value in (0,0x1234,0xffffffff):
                m=memory(0x1001b4c8,[(0x1001b4c8,0x1001b542)])
                initial=bytes([0xcc])*1024;m.put(RAM,initial)
                assert m.run([RAM+16+offset,value,n])==RAM+16+offset
                expected=bytearray(initial);expected[16+offset:16+offset+n]=bytes([value&255])*n
                assert dump(m)==expected,('memset',offset,n,value)
                if libc_observer:libc_observer('memset',0x1001b4c8,[RAM+16+offset,value,n],initial,bytes(expected),RAM+16+offset)
                account('memset',m)
    rng=random.Random(102006)
    for dest in range(8):
        for src in range(8):
            for n in range(97):
                m=memory(0x1001b38c,[(0x1001b34d,0x1001b485)])
                initial=rng.randbytes(1024);m.put(RAM,initial)
                assert m.run([RAM+512+dest,RAM+16+src,n])==RAM+512+dest
                expected=bytearray(initial);expected[512+dest:512+dest+n]=initial[16+src:16+src+n]
                assert dump(m)==expected,('memcpy',dest,src,n)
                if libc_observer:libc_observer('memcpy',0x1001b38c,[RAM+512+dest,RAM+16+src,n],initial,bytes(expected),RAM+512+dest)
                account('memcpy',m)
    for dest in (0,1,2,3,8,16):
        for src in (0,1,2,3,8,16):
            for n in (0,1,2,3,4,7,8,15,16,17,31,32,65):
                m=memory(0x1001b488,[(0x1001b488,0x1001b4c8)])
                initial=rng.randbytes(1024);m.put(RAM,initial)
                assert m.run([RAM+dest,RAM+src,n])==RAM+dest
                expected=bytearray(initial);expected[dest:dest+n]=initial[src:src+n]
                assert dump(m)==expected,('memmove',dest,src,n)
                if libc_observer:libc_observer('memmove',0x1001b488,[RAM+dest,RAM+src,n],initial,bytes(expected),RAM+dest)
                account('memmove',m)
    for offset in range(8):
        for n in range(97):
            m=memory(0x100169d4,[(0x100169d4,0x10016a38)])
            m.put(RAM,b'\xff'*1024);m.put(RAM+16+offset,bytes(rng.randrange(1,256) for _ in range(n))+b'\0')
            assert m.run([RAM+16+offset])==n,('strlen',offset,n)
            if libc_observer:libc_observer('strlen',0x100169d4,[RAM+16+offset],dump(m),dump(m),n)
            account('strlen',m)
    print('original libc cases:',totals,flush=True)
    cases=[]
    with tempfile.TemporaryDirectory(prefix='hp1020-stock-oracle-') as tmp:
        binary=Path(tmp)/'host-check';inputfile=Path(tmp)/'input.zjs'
        subprocess.run([os.environ.get('CC','clang'),'-std=c11','-Wall','-Wextra','-Werror','-g','-fsanitize=address,undefined',
                        str(SOURCE/'hp1020_semantic.c'),str(SOURCE/'hp1020_page_plan.c'),str(SOURCE/'host-check.c'),'-o',str(binary)],check=True)
        def native(data):
            inputfile.write_bytes(data)
            p=subprocess.run([str(binary),str(inputfile),'7','1048576'],text=True,capture_output=True)
            assert p.returncode==0 and not p.stderr,p.stderr
            return json.loads(p.stdout)
        def compare(name,data,fill=0xcc):
            m=ParserHarness(program,data,fill=fill)
            assert m.run([CONTEXT])==0
            parts,end=chunks(data)
            assert m.input_pos==end,(name,m.input_pos,end)
            c=native(data);assert c['result']==0,(name,c)
            messages=m.messages;ids=[x['words'][0] for x in messages]
            expected_ids=[]
            for kind,_,_,_ in parts:expected_ids.extend({0:[1],1:[2],2:[3,5],3:[6],4:[41],5:[42],6:[43]}[kind])
            assert ids==expected_ids,(name,ids,expected_ids)
            page_index=-1;raster_index=0
            for message in messages:
                kind=message['words'][0]
                raw=bytes.fromhex(message.get('payload',''))
                if kind==5:
                    page_index+=1;p=c['pages'][page_index]
                    for key,offset in [('copies',12),('nbie',18),('resolution_x',20),('resolution_y',22),
                                       ('bpp',34),('video_x',36),('video_y',38),('work26',38),('work30',48),('work32',50)]:
                        assert struct.unpack_from('>H',raw,offset)[0]==p[key]&65535,(name,key)
                elif kind==41:
                    p=c['pages'][page_index]
                    assert tuple(struct.unpack_from('>III',raw,4))==(p['xd'],p['yd'],p['l0'])
                    assert raw[19]==p['options']
                elif kind==42:
                    payload_size=struct.unpack_from('>I',raw,16+0x48)[0]
                    pointer=struct.unpack_from('>I',raw,16+0x54)[0]
                    actual=m.bytes_at(pointer,payload_size)
                    raster=c['rasters'][raster_index];raster_index+=1
                    assert (raster['page'],raster['length'],raster['fnv1a'])==(page_index,len(actual),fnv(actual))
            assert page_index+1==len(c['pages']) and raster_index==len(c['rasters'])
            account('parser_agreement',m)
            cases.append(dict(case=name,status='pass',fill=fill,instructions=m.steps,pages=page_index+1,rasters=raster_index,
                              message_ids=ids,consumed_bytes=m.input_pos,input_sha256=hashlib.sha256(data).hexdigest()))
            return m,c
        base=None
        for path in sorted((ROOT/'analysis/samples/generated').glob('*.zjs')):
            data=path.read_bytes();data=data[data.index(b'JZJZ'):]
            if 'logical_clip' in path.stem:
                m=ParserHarness(program,data)
                try:m.run([CONTEXT])
                except ValueError as error:
                    assert 'unmapped RAM' in str(error),str(error)
                    assert m.pc==0x10009d24,hex(m.pc)
                    checks.append(dict(name='logical_clip_actual_stock_out_of_bounds',status='pass',pc=hex(m.pc),error=str(error)))
                else:raise AssertionError('stock logical clip must escape declared metadata allocation')
                assert native(data)['pages'][0]['plan_result']==1
                continue
            for fill in (0,0xcc):compare(path.stem+f'/fill={fill}',data,fill)
            if path.stem=='matrix-a4_default':base=chunks(data)[0]
        assert base is not None
        for iteration in range(32):
            parts=list(base);kind,payload,count,reserved=parts[1]
            items=[payload[i:i+12] for i in range(0,len(payload),12)];rng.shuffle(items)
            # Known metadata boundary variations, retained full 32-bit host words.
            edits={4:rng.randrange(1,100),18:rng.randrange(1,65536),22:rng.randrange(65536),23:rng.randrange(65536)}
            found=set();changed=[]
            for item in items:
                key=struct.unpack_from('>H',item,4)[0];found.add(key)
                changed.append(item[:8]+struct.pack('>I',edits[key]) if key in edits else item)
            for key in edits.keys()-found:changed.append(struct.pack('>IHBBI',12,key,1,0,edits[key]))
            payload=b''.join(changed);parts[1]=(kind,payload,len(changed),len(payload))
            compare(f'permuted-fields/{iteration}',stream(parts))
        for pages in (2,3,8,16):
            compare(f'multipage/{pages}',stream([base[0]]+base[1:6]*pages+[base[6]]))
        for pieces in (2,3,7):
            kind,payload,_,_=base[3];cuts=[len(payload)*i//pieces for i in range(pieces+1)]
            bids=[(kind,payload[cuts[i]:cuts[i+1]],0,0) for i in range(pieces)]
            compare(f'split-raster/{pieces}',stream(base[:3]+bids+base[4:]))
        # Explicit differences: strict replacement policy versus observed stock behavior.
        for name,change in [('zero-copies',lambda xs:[x[:8]+bytes(4) if x[4:6]==b'\0\x04' else x for x in xs]),
                            ('duplicate-copies',lambda xs:xs+[struct.pack('>IHBBI',12,4,1,0,3)])]:
            parts=list(base);xs=[parts[1][1][i:i+12] for i in range(0,len(parts[1][1]),12)]
            payload=b''.join(change(xs));parts[1]=(2,payload,len(payload)//12,len(payload));data=stream(parts)
            m=ParserHarness(program,data);m.run([CONTEXT]);actual=native(data)
            page=next(bytes.fromhex(x['payload']) for x in m.messages if x['words'][0]==5)
            copies=struct.unpack_from('>H',page,12)[0]
            assert actual['result']==(4 if name=='zero-copies' else 1) and copies==(1 if name=='zero-copies' else 3)
            checks.append(dict(name=name,status='pass',stock_copies=copies,replacement_error=actual['result']))
            account('parser_policy_difference',m)
        m=ParserHarness(program,stream(base),read_limit=1);m.run([CONTEXT])
        assert not m.messages and m.input_pos==0
        assert native(stream(base))['result']==0
        checks.append(dict(name='stock_requires_complete_callback_reads',status='pass',stock_messages=0,
                           note='Replacement accepts fragmented feed; stock callback boundary must assemble each requested read.'))
    # Deliberately corrupt just decoded bit indices to reproduce the old mistake.
    bad_program=copy.copy(program);bad_program.instructions=program.instructions.copy()
    for pc,(op,args,raw) in list(bad_program.instructions.items()):
        if op in ('bbci','bbsi'):
            bad_program.instructions[pc]=(op,(args[0],31-args[1],args[2]),raw)
    wrong=StockMachine(bad_program,0x1001b4c8,[(0x1001b4c8,0x1001b542)],[(RAM,1024)])
    wrong.put(RAM,b'\xcc'*1024);wrong.run([RAM,0,6])
    assert dump(wrong)!=bytes(6)+b'\xcc'*1018
    checks.append(dict(name='be_bit_branch_regression',status='pass',witness='Reintroducing reversed bit indices makes original memset(length=6) disagree with the bytearray oracle.'))
    report=dict(status='pass',scope='Original stock routines execute in isolated host RAM; no printer contact or hardware model.',
                original_elf_sha256=hashlib.sha256((ROOT/'analysis/sihp1020.elf').read_bytes()).hexdigest(),
                totals=totals,executed_instructions=steps,distinct_instructions=len(visited),executed_opcodes=sorted(opcodes),
                cases=cases,checks=checks,boundary_substitutes={hex(k):v for k,v in BOUNDARIES.items()},
                limits=['Abstract unlimited register windows; no spill/interrupt/cache/RTOS/USB/engine execution.',
                        'Tray lookup uses an explicitly seeded empty record; its physical mapping is not established.',
                        'Queue delivery is captured, not consumed. Comparisons cover page fields, BIH and compressed records, not printing.',
                        'Passing results are conditional on standard ISA semantics and the listed environment substitutes.'],
                isa_references=['https://github.com/qemu/qemu/blob/master/target/xtensa/translate.c (translate_bbi, gen_brcond)',
                                'Ghidra 12.1.1 xtensaInstructions.sinc extract_bit macro'])
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'validation.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    lines=['# Original firmware execution checkpoint','',report['scope'],'',
           f"Status: pass. {sum(totals.values()):,} cases, {steps:,} executed instructions; {len(visited)} distinct instructions.",'',
           '## Results','']+[f'- {key}: {value} cases.' for key,value in totals.items()]
    lines+=['','The original parser, item builder, page constructor, list initialization and libc routines run unchanged. '
            'Generated print streams, reordered metadata, multiple pages and split raster records are compared with the sanitizer-built C replacement. '
            'The stock queue emits document/page/BIH/BID records matching the checked fields and byte payloads.', '',
            'The test exposed a reversed BE bit-branch interpretation in the earlier target interpreter. '
            'Bit branch 31 tests the least significant bit. The stock memset/memcpy/strlen routines now validate that interpretation across alignments and lengths. '
            'A taken branch to LOOP end exits rather than repeating; the original strlen routine exercises this distinction.', '',
            'The logical-clip stream now demonstrably reads outside its declared allocation during actual stock item-builder execution. '
            'Zero/duplicate copies show deliberate stricter replacement policy. A one-byte callback read shows that the stock parser requires its lower input layer to assemble a full requested read.', '',
            '## Explicit host substitutes','']+[f'- `{hex(k)}`: {v}.' for k,v in BOUNDARIES.items()]
    lines+=['','## Limits','']+['- '+x for x in report['limits']]
    lines+=['','Standard bit-branch and loop-edge semantics are cross-checked against [QEMU Xtensa translation](https://github.com/qemu/qemu/blob/master/target/xtensa/translate.c) and the local Ghidra ISA source. '
            'These references define ordinary CPU behavior, not printer-specific custom instructions.','']
    (OUT/'validation.md').write_text('\n'.join(lines))
    print('stock execution:',totals,'instructions',steps,'distinct',len(visited))

if __name__=='__main__':main()
