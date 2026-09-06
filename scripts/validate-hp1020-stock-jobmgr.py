#!/usr/bin/env python3
"""Original parser -> JobMgr RAM execution versus C and input-byte oracles."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import struct
import subprocess
import tempfile
from hp1020_xtensa_call0 import Program
from hp1020_xtensa_stock import StockMachine
from hp1020_stock_jobmgr_harness import JobMgrHarness, JOB_BOUNDARIES, JOB_CODE
from hp1020_stock_parser_harness import BOUNDARIES

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'analysis/open-firmware-model/stock-execution/jobmgr'
SOURCE=ROOT/'open-firmware/semantic-core'
spec=importlib.util.spec_from_file_location('stock_validation',ROOT/'scripts/validate-hp1020-stock-execution.py')
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
chunks,stream,fnv=helper.chunks,helper.stream,helper.fnv


def edit_items(parts,edits):
    parts=list(parts);kind,payload,count,reserved=parts[1]
    xs=[payload[i:i+12] for i in range(0,len(payload),12)];found=set();out=[]
    for x in xs:
        key=struct.unpack_from('>H',x,4)[0];found.add(key)
        out.append(x[:8]+struct.pack('>I',edits[key]) if key in edits else x)
    for key in edits.keys()-found:out.append(struct.pack('>IHBBI',12,key,1,0,edits[key]))
    payload=b''.join(out);parts[1]=(kind,payload,len(out),len(payload))
    return parts


def linked(m,head,tail,limit):
    nodes=[];at=head
    while at:
        assert at not in nodes and len(nodes)<limit,'cycle or excess list nodes'
        nodes.append(at);at=m.read(at,4)
    assert (nodes[-1] if nodes else 0)==tail,'tail disagrees with linked list'
    return nodes


def main():
    program=Program(ROOT/'analysis/sihp1020.elf',os.environ.get('XTENSA_PREFIX','/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf'))
    cases=[];visited=set();total_steps=0;job_steps=0
    # Independently execute the original allocator after the poison-fill replay
    # exposes the marker dependency. A real single free block is seeded in RAM;
    # only its mutex operations are substituted. No assumed calloc behavior.
    class Allocator(StockMachine):
        def extension(self,op,args,nxt):
            if op=='call8' and args[0] in (0x100181a4,0x10018214):
                self.registers[10]=0;self.branch_taken=True;return nxt
            return super().extension(op,args,nxt)
    allocation_checks=[]
    for fill in (0,1,0xcc,0xff):
        for size in (1,2,3,4,8,16,120,148,4096):
            m=Allocator(program,0x10013140,[(0x10013140,0x10013408)],[(0x22000000,16384)])
            m.put(0x22000000,bytes([fill])*16384)
            m.write(0x22000000,4,m.read(0x100066a4,4))
            m.write(0x22000004,4,16384-12);m.write(0x22000008,4,0x40000000)
            for cell in (0x10006698,0x1000669c):m.write(m.read(cell,4),4,0x22000000)
            m.write(m.read(0x100066a8,4),4,16384-12)
            result=m.run([size,1])
            assert result==0x2200000c
            blob,off=m.span(result,size)
            assert blob[off:off+size]==bytes([fill])*size,'stock type-1 allocation unexpectedly clears payload'
            allocation_checks.append(dict(fill=fill,size=size,status='preserved',instructions=m.steps))
            visited.update(m.visited);total_steps+=m.steps
    # Execute complete render paths that do not reach MMIO: rejected state,
    # full ring, or queuing behind an already-running/nonempty transfer.
    class Render(StockMachine):
        def __init__(self):
            super().__init__(program,0x10015214,[(0x10015214,0x10015438)],[(0x22000000,512)])
            self.payload_reads=[]
        def read(self,address,size):
            self.payload_reads.append((address,size))
            return super().read(address,size)
        def extension(self,op,args,nxt):
            if op=='call8' and args[0]==0x1001b770:
                self.registers[10]=0;self.branch_taken=True;return nxt
            return super().extension(op,args,nxt)
    render_checks=[]
    for state in (0,1,2,3,0xffffffff):
        for head in range(4):
            for tail in range(4):
                busy=state not in (1,2) or (tail+1)&3==head
                if not busy and not(state==2 and head!=tail):continue
                for marker in (0,1,0xcccc,0xffff):
                    m=Render();work=0x22000000;node=work+160;payload=node+16
                    video=m.read(0x10006770,4)
                    m.write(work+0x50,4,node);m.write(node+12,4,payload)
                    m.write(payload+0x48,4,64);m.write(payload+0x54,4,work+320)
                    m.write(payload+0x4c,2,marker)
                    for off,value in [(0x6c,state),(0x94,head),(0x98,tail),(0x9c,0x12345678),(0xa0,0x87654321)]:m.write(video+off,4,value)
                    m.payload_reads=[]
                    result=m.run([work])
                    assert not any(a<payload+0x4e and payload+0x4c<a+n for a,n in m.payload_reads),'render unexpectedly reads raw marker'
                    assert result==(0x1003 if busy else 0)
                    assert m.read(video+0x98,4)==(tail if busy else (tail+1)&3)
                    assert m.read(video+0x9c,4)==node and m.read(video+0xa0,4)==0,'list pointers change even before busy return'
                    render_checks.append(dict(state=state,head=head,tail=tail,marker=marker,result=result,instructions=m.steps))
                    visited.update(m.visited);total_steps+=m.steps
    with tempfile.TemporaryDirectory(prefix='hp1020-jobmgr-') as tmp:
        binary=Path(tmp)/'host-check';inputfile=Path(tmp)/'input.zjs'
        subprocess.run([os.environ.get('CC','clang'),'-std=c11','-Wall','-Wextra','-Werror','-g','-fsanitize=address,undefined',
                        str(SOURCE/'hp1020_semantic.c'),str(SOURCE/'hp1020_page_plan.c'),str(SOURCE/'host-check.c'),'-o',str(binary)],check=True)
        def compare(name,data,fill=0xcc,duplex=0,credits=20):
            nonlocal total_steps,job_steps
            m=JobMgrHarness(program,data,fill,duplex,credits).replay()
            inputfile.write_bytes(data)
            native=json.loads(subprocess.check_output([str(binary),str(inputfile),'13','1048576'],text=True))
            assert native['result']==0,(name,native['result'])
            assert m.delivered==len(m.pending)==len(m.snapshots)
            base=m.read(0x100062e4,4)
            docs=linked(m,m.read(base,4),m.read(base+4,4),1)
            assert len(docs)==1
            doc=m.read(docs[0]+12,4)
            assert m.read(doc+0x68,1)==1 and m.read(doc+0x69,1)==0
            children=linked(m,m.read(doc+0x70,4),m.read(doc+0x74,4),16)
            assert len(children)==len(native['pages'])
            expected_schedule=[];budget=credits;raster_index=0
            expected_bids=[payload for kind,payload,_,_ in chunks(data)[0] if kind==5]
            for index,(node,page) in enumerate(zip(children,native['pages'])):
                child=m.read(node+12,4);work=m.read(child+0x48,4)
                assert work and m.read(child+0x4c,4)==0
                for key,off in [('copies',12),('nbie',18),('resolution_x',20),('resolution_y',22),
                                ('bpp',34),('video_x',36),('video_y',38),('work30',48),('work32',50)]:
                    assert m.read(work+off,2)==page[key]&65535,(name,index,key)
                assert tuple(m.read(work+off,4) for off in (0x84,0x88,0x8c))==(page['xd'],page['yd'],page['l0'])
                assert m.read(work+0x90,1)==page['options']
                assert m.read(work+0x78,1)==1 and m.read(work+0x7a,2)==index
                assert m.read(work+0x75,1)==duplex
                rasters=linked(m,m.read(work+0x50,4),m.read(work+0x54,4),128)
                expected=[r for r in native['rasters'] if r['page']==index]
                assert len(rasters)==len(expected)
                copies=page['copies']&65535
                # Queue 1 remains unconsumed in this fixture: credits only fall.
                scheduled=min(copies,budget);budget-=scheduled
                expected_schedule += [work]*scheduled
                assert m.read(work+0x48,2)==scheduled
                raster_copies=(copies*(2 if duplex==1 else 1))&65535
                assert m.read(work+0x4e,2)==raster_copies
                for ri,(rnode,raster) in enumerate(zip(rasters,expected)):
                    payload=m.read(rnode+12,4)
                    count=m.read(payload+0x48,4);ptr=m.read(payload+0x54,4)
                    actual=m.bytes_at(ptr,count)
                    assert actual==expected_bids[raster_index],(name,index,ri,'compressed bytes')
                    assert (len(actual),fnv(actual))==(raster['length'],raster['fnv1a'])
                    assert m.read(payload+0x4e,2)==raster_copies
                    expected_marker=1 if ri==len(rasters)-1 else fill*257
                    assert m.read(payload+0x4c,2)==expected_marker,'END_JBIG overwrites only the last node; earlier markers retain allocation contents'
                    raster_index+=1
            assert m.scheduled==expected_schedule,(name,m.scheduled,expected_schedule)
            assert m.read(m.read(0x100062e8,4),2)==budget
            # BIH messages are copied then freed; BID buffers remain owned by lists.
            for message in m.pending:
                if message[0]==41:assert m.allocations[message[3]]['freed']
                if message[0]==42:assert not m.allocations[message[3]]['freed']
            visited.update(m.visited);total_steps+=m.steps;job_steps+=m.steps-m.parser_steps
            cases.append(dict(name=name,status='pass',pages=len(children),rasters=raster_index,
                              scheduled_requests=len(m.scheduled),remaining_credits=budget,duplex_fixture=duplex,heap_fill=fill,
                              stock_instructions=m.steps,jobmgr_instructions=m.steps-m.parser_steps,
                              input_sha256=hashlib.sha256(data).hexdigest()))
        base=None
        for path in sorted((ROOT/'analysis/samples/generated').glob('*.zjs')):
            if 'logical_clip' in path.stem:continue
            data=path.read_bytes();data=data[data.index(b'JZJZ'):]
            for fill in (0,0xcc):compare(path.stem+f'/fill={fill}',data,fill)
            if path.stem=='matrix-a4_default':base=chunks(data)[0]
        assert base
        for pages in (2,3,8,16):
            for copies in (1,3,21):
                parts=edit_items(base,{4:copies})
                for credits in (0,1,5,20):
                    compare(f'pages={pages}/copies={copies}/credits={credits}',stream(parts[:1]+parts[1:6]*pages+parts[6:]),credits=credits)
        for pieces in (2,3,7,64):
            kind,payload,_,_=base[3];cuts=[len(payload)*i//pieces for i in range(pieces+1)]
            bids=[(kind,payload[cuts[i]:cuts[i+1]],0,0) for i in range(pieces)]
            for duplex in (0,1):
                for fill in (0,0xcc):compare(f'split={pieces}/duplex={duplex}/fill={fill}',stream(base[:3]+bids+base[4:]),duplex=duplex,fill=fill)
        for copies in (1,2,32767,32768,65535):
            for duplex in (0,1):compare(f'copy-width={copies}/duplex={duplex}',stream(edit_items(base,{4:copies})),duplex=duplex)
        rng=random.Random(102042)
        for i in range(24):
            parts=edit_items(base,{4:rng.randrange(1,40),22:rng.randrange(2),23:rng.randrange(2)})
            bih=bytearray(parts[2][1])
            for off in (4,8,12):struct.pack_into('>I',bih,off,rng.randrange(1,0x100000000))
            bih[19]=rng.randrange(256)
            parts[2]=(4,bytes(bih),0,0)
            compare(f'bih-field-preservation/{i}',stream(parts),duplex=i%2)
    report=dict(status='pass',scope='Serialized original parser, JobMgr, list append, memcpy, page scheduling and selected MMIO-free render paths in isolated RAM; queue 1 requests are captured, never delivered to hardware.',
        stock_sha256=hashlib.sha256((ROOT/'analysis/sihp1020.elf').read_bytes()).hexdigest(),
        case_count=len(cases),allocator_checks=allocation_checks,render_checks=render_checks,executed_instructions=total_steps,jobmgr_instructions=job_steps,distinct_instructions=len(visited),
        cases=cases,additional_code_ranges=[[hex(a),hex(b)] for a,b in JOB_CODE],
        isolated_allocator_range=['0x10013140','0x10013408'],isolated_render_range=['0x10015214','0x10015438'],
        host_boundaries={hex(k):v for k,v in (BOUNDARIES|JOB_BOUNDARIES).items()},
        evidence=['Page and raster fields agree with sanitizer-built C, and every compressed chunk agrees byte-for-byte with its input.',
                  'Original list links preserve page/raster ordering and correct head/tail; END_JBIG overwrites the last raster marker with 1.',
                  'Earlier raster markers retain allocator contents copied from payload +0x2c: zero in the zero-fill fixture, CCCC in the poison-fill fixture. The parser/JobMgr path does not establish zero initialization.',
                  'Separate original type-1 allocator execution preserves all requested payload bytes across 36 poisoned/zero-memory cases; a zero-fill guarantee cannot be attributed to that path.',
                  'BIH buffers are copied then freed; BID wrappers and payload bytes remain on page-owned lists.',
                  'Original scheduling emits at most available credits, preserving page order; no consumer replenishes credits in this fixture.',
                  'Complete MMIO-free render paths ignore the raw marker and change video +0x9c/+0xa0 even when returning busy. Earlier ring-model ordering incorrectly put these stores after rejection.',
                  'Duplex fixture doubles the raster copy halfword, wrapping at 16 bits. This is observed stock behavior; no duplex support is added to the narrow replacement.'],
        limitations=['Parser is run before serialized queue replay; concurrent production/consumption, interrupts, queue backpressure and allocation failure are not exercised.',
                     'Pipeline task startup, document publication, RTOS critical sections, allocation and queue delivery are host substitutes; the separate allocator experiment executes original allocation with only mutex substitutes.',
                     'Document publication substitute writes its bookkeeping flag; datastore/queue-10 effects are omitted.',
                     'Only MMIO-free rejection/queued render paths execute; initial hardware arming, decompression, custom raster instructions, USB and mechanical timing remain outside.',
                     'No empty documents, cancellation, malformed message ordering or multi-document lifecycle are claimed.'])
    OUT.with_suffix('.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    OUT.with_suffix('.md').write_text('\n'.join(['# Original JobMgr execution','',report['scope'],'',
        f'{len(cases)} pipeline, {len(allocation_checks)} allocator and {len(render_checks)} MMIO-free render cases; {job_steps} downstream instructions ({total_steps} including parser/allocator/render); {len(visited)} distinct original instruction addresses.','',
        *['- '+s for s in report['evidence']],'','## Explicit limits','',*['- '+s for s in report['limitations']],'']))
    print(f'stock JobMgr: {len(cases)} cases, {job_steps} downstream instructions, {len(visited)} distinct stock instructions')

if __name__=='__main__':main()
