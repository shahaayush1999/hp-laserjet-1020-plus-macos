#!/usr/bin/env python3
"""Bounded receive ownership and full software documents; no USB/device access."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import struct
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('rx_pages',ROOT/'scripts/validate-hp1020-image-pages.py')
pages=importlib.util.module_from_spec(spec);sys.modules[spec.name]=pages;spec.loader.exec_module(pages)
core=pages.core;IMG=pages.SRC;SEM=pages.SEM;SRC=ROOT/'open-firmware/usb-receive-core'
OUT=ROOT/'analysis/usb-path/receive-core'
OK,WAIT,STALE,STOPPED,ORDER,LIMIT,STATUS,ENDPOINT,PAYLOAD=range(9)
DONE=0x88000000

def event(op,a=0,b=0,c=0,d=0,data=b'',result=OK,expect=None,unchanged=False):
    return dict(words=[op,a,b,c,d],data=data,result=result,expect=expect or {},unchanged=unchanged)
def reserve(data,slot=0,capacity=1024,result=OK):
    return event(0,capacity,len(data),slot,data=data,result=result)
def complete(slot,count,status=DONE,fault=0,result=OK):
    return event(1,slot,status|count,fault,result=result)
def restart(generation,reverse=False):
    ack=[event(5,generation),event(6,generation)]
    if reverse:ack.reverse()
    return [event(7,result=ORDER,unchanged=True),ack[0],event(7,result=ORDER,unchanged=True),ack[1],event(7)]

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--target',action='store_true');args=ap.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    temp=Path(tempfile.mkdtemp(prefix='hp1020-usb-receive-',dir='/tmp'))
    print('Receive validation captures: '+str(temp),flush=True)
    sources=set(SRC.glob('*.[ch]'))|set(SRC.glob('*.ld'))
    sources.update(IMG/n for n in ('hp1020_image.c','hp1020_image.h','hp1020_image_page.c','hp1020_image_page.h',
        'hp1020_image_stream.c','hp1020_image_stream.h','hp1020_image_ring.c','hp1020_image_ring.h',
        'hp1020_image_output.c','hp1020_image_output.h','target-memory.c','reference.c'))
    sources.update((IMG/'freestanding').glob('*.h'));sources.update(SEM.rglob('*.c'));sources.update(SEM.rglob('*.h'))
    sources.update((core.VENDOR/'libjbig').glob('*.h'))
    sources.update(core.VENDOR/'libjbig'/n for n in ('jbig85.c','jbig_ar.c'))
    sources.update(ROOT/'vendor/foo2zjs-source'/n for n in ('jbig.c','jbig_ar.c','jbig.h','jbig_ar.h'))
    sources.update(ROOT/'scripts'/n for n in ('validate-hp1020-usb-receive.py','build-hp1020-usb-receive-target.sh',
        'validate-hp1020-image-pages.py','validate-hp1020-image-core.py','check-hp1020-c-compiler-profile.py',
        'hp1020_qemu_ram.py','hp1020_xtensa_call0.py','hp1020_xtensa_properties.py'))
    tested={str(p.relative_to(ROOT)):core.sha(p.read_bytes()) for p in sorted(sources)}
    for name in tested:
        saved=temp/'source'/name;saved.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,saved)
    (temp/'source-sha256.json').write_text(json.dumps(tested,indent=2)+'\n')
    flags=['clang','-std=c11','-O1','-g','-fno-common','-Wall','-Wextra','-Werror','-fsanitize=address,undefined']
    implementation=[SRC/n for n in ('hp1020_usb_receive.c','hp1020_usb_document.c','fixture.c','host-check.c')]
    implementation += [IMG/n for n in ('hp1020_image.c','hp1020_image_page.c','hp1020_image_stream.c',
        'hp1020_image_ring.c','hp1020_image_output.c')]
    implementation += [SEM/'hp1020_semantic.c',SEM/'hp1020_page_plan.c',
        core.VENDOR/'libjbig/jbig85.c',core.VENDOR/'libjbig/jbig_ar.c']
    core.command(flags+['-I'+str(SRC),'-I'+str(IMG),'-I'+str(SEM),'-I'+str(core.VENDOR/'libjbig')]+
        implementation+['-o',temp/'host'])
    full=ROOT/'vendor/foo2zjs-source'
    core.command(flags+['-I'+str(full),IMG/'reference.c',full/'jbig.c',full/'jbig_ar.c','-o',temp/'reference'])
    fixture_paths=[];images={}
    for name,w,h,stripe,kind,path in (
        ('small',32,8,4,'black','fixtures/32x8-stripe4-black.jbg'),
        ('medium',9600,132,128,'edges','fixtures/9600x132-stripe128-edges.jbg'),
        ('wide',16384,4,128,'edges','fixtures/16384x4-stripe128-edges.jbg'),
        ('partial',1024,260,128,'repeat','output-fixtures/1024x260-stripe128-repeat.jbg'),
        ('slim',64,12,4,'edges','output-fixtures/64x12-stripe4-edges.jbg')):
        path=pages.OUT/path;raw=core.pattern(w,h,kind)
        info=json.loads(core.command([temp/'reference','decode',path,temp/'oracle']))
        assert (temp/'oracle').read_bytes()==raw and info['consumed']==path.stat().st_size
        images[name]=(path.read_bytes(),raw);fixture_paths.append(path)
    base_path=ROOT/'analysis/samples/generated/matrix-a4_default.zjs';base=pages.chunks(base_path.read_bytes())
    def body(name):
        bie=images[name][0];w,h=struct.unpack_from('>II',bie,4);items=bytearray(base[1][1])
        for off in range(0,len(items),12):
            ident=struct.unpack_from('>H',items,off+4)[0]
            value={4:1,12:w,13:h,17:w//2,18:h}.get(ident)
            if value is not None:struct.pack_into('>I',items,off+8,value)
        payload=bie[20:]+bytes(16+((-len(bie[20:]))&3))
        return [(2,bytes(items),base[1][2],base[1][3]),(4,bie[:20],0,0),
            (5,payload,0,0),(6,b'',0,0),(3,b'',0,0)]
    def doc(names):return b'JZJZ'+pages.pack([base[0]]+sum((body(n) for n in names),[])+[base[-1]])
    def transfers(data,packet=512,reverse=False,zlp=False):
        chunks=[data[i:i+packet] for i in range(0,len(data),packet)]
        if zlp:chunks=[b'']+chunks[:1]+[b'']+chunks[1:]+[b'']
        events=[]
        for at in range(0,len(chunks),4):
            batch=chunks[at:at+4]
            events += [reserve(p,i) for i,p in enumerate(batch)]
            if len(batch)==4:events.append(reserve(b'',7,result=WAIT))
            events.append(event(2,result=WAIT,unchanged=True))
            for i in (list(range(len(batch)))[::-1] if reverse else range(len(batch))):
                events.append(complete(i,len(batch[i])))
                if reverse and i:events.append(event(2,result=WAIT,unchanged=True))
            events.append(event(2))
        return events

    candidates=[]
    def add(name,events,expected=b'',raw=b'',fill=204,mode=1,fail_at=0xffffffff,prefix=False):
        candidates.append(dict(name=name,events=events,expected=expected,raw=raw,fill=fill,mode=mode,fail_at=fail_at,prefix=prefix))
    # Matrix includes unsupported receive-status values without inventing their meaning.
    for owner in range(4):
        for rx in range(4):
            for last in (0,1):
                result=WAIT if owner!=2 else STATUS if rx or not last else OK
                events=[reserve(bytes(range(37))),complete(0,37,status=(owner<<30)|(rx<<28)|(last<<27),result=result)]
                if result==OK:events.append(event(10,expect={27:37,29:37}))
                else:events.append(event(2,result=STOPPED if result==STATUS else WAIT,unchanged=True))
                add(f'status/owner={owner}/rx={rx}/last={last}',events,raw=bytes(range(37)) if result==OK else b'')
    for count in (0,1,64,512,1024,1025,65535):
        data=bytes(i&255 for i in range(min(count,1024)));r=OK if count<=1024 else LIMIT
        events=[reserve(data),complete(0,count,result=r)]
        events.append(event(10,expect={27:count,29:count}) if r==OK else event(2,result=STOPPED,unchanged=True))
        add(f'count/{count}',events,raw=data if r==OK else b'')
    for capacity in (0,1025,0xffffffff):add(f'capacity/{capacity}',[reserve(b'',capacity=capacity,result=LIMIT)])
    add('short-reservation-overrun',[reserve(b'ab',capacity=2),complete(0,3,result=LIMIT),event(2,result=STOPPED,unchanged=True)])
    for owner in (0,2):
        for fault in (0x80,0x200):
            add(f'completion-fault/{owner}/{fault}',[reserve(b'ab'),
                complete(0,2,status=(owner<<30)|0x08000000,fault=fault,result=ENDPOINT),
                event(2,result=STOPPED,unchanged=True)])
    for point in ('empty','pending','ready','consumed'):
        events=[]
        if point!='empty':events+=[reserve(b'ab')]
        if point in ('ready','consumed'):events+=[complete(0,2)]
        if point=='consumed':events+=[event(10)]
        events += [event(11,1,0,result=OK,unchanged=True),event(11,1,0x200,result=ENDPOINT),
            event(2,result=STOPPED,unchanged=True),event(0,1024,0,7,result=STOPPED,unchanged=True)]
        add('endpoint-wide-fault/'+point,events,raw=b'ab' if point=='consumed' else b'')
    for fill in (0,204):
        events=[reserve(bytes([i])*31,i) for i in range(4)]
        events+=[reserve(b'',7,result=WAIT),complete(3,31),complete(2,31),complete(1,31),
            event(9,3,result=ORDER,unchanged=True),event(10,result=WAIT,unchanged=True),complete(0,31)]
        events += [event(10) for _ in range(4)]
        events += [reserve(b'new',4),complete(0,31,result=STALE),complete(4,3),
            complete(4,3,result=STALE),event(10),event(10,result=WAIT)]
        add(f'fifo-full-late-head-slot-reuse/fill={fill}',events,raw=b''.join(bytes([i])*31 for i in range(4))+b'new',fill=fill)
    for point in ('empty','pending','ready'):
        for reverse in (False,True):
            events=[event(5,1,result=ORDER),event(6,1,result=ORDER)]
            if point!='empty':events+=[reserve(b'old')]
            if point=='ready':events+=[complete(0,3)]
            events += [event(4),event(2,result=STOPPED,unchanged=True),event(3,result=STOPPED,unchanged=True)]
            events += restart(1,reverse)
            events += [event(5,1,result=STALE,unchanged=True),event(6,1,result=STALE,unchanged=True),
                event(11,1,0x200,result=STALE,unchanged=True),complete(0,3,result=STALE),
                reserve(b'new',1),complete(1,3),event(10,expect={1:2,27:3})]
            add(f'cancel/{point}/ack-reverse={reverse}',events,raw=b'new')
    add('sequence-exhaustion',[event(8,1,0xfffffffe),reserve(b'x'),complete(0,1),event(10),
        reserve(b'',1,result=LIMIT),event(2,result=STOPPED,unchanged=True)],raw=b'x')
    add('generation-exhaustion',[event(8,0xffffffff),event(4),event(5,0xffffffff),event(6,0xffffffff),
        event(7,result=LIMIT),event(0,1024,0,0,result=STOPPED,unchanged=True)])

    mixed=['medium','wide','small','partial'];stream=doc(mixed);pixels=b''.join(images[n][1] for n in mixed)
    for packet,reverse in ((19,False),(512,True),(1024,True)):
        for fill in (0,204):
            events=transfers(stream,packet,reverse,zlp=True)+[event(3,expect={10:1,17:1,18:4,19:4}),event(3,unchanged=True)]
            add(f'document/mixed/packet={packet}/reverse={reverse}/fill={fill}',events,pixels,fill=fill)
    many=['small' if i%2==0 else 'slim' for i in range(65)]
    add('document/65-changing-pages',transfers(doc(many),1024,True)+[event(3,expect={18:65,19:65})],
        b''.join(images[n][1] for n in many))
    add('document/consecutive',transfers(doc(['small'])+doc([])+doc(['slim']),64,True)+[
        event(3,expect={17:3,18:2,19:2})],images['small'][1]+images['slim'][1])
    add('document/zero-transfer-is-not-eof',[reserve(b''),complete(0,0),event(2,expect={10:0,17:0})]+
        transfers(doc(['small']),64,True)+[event(3,expect={17:1,18:1})],images['small'][1])
    add('document/truncated',transfers(doc(['medium'])[:-16],512,True)+[
        event(3,result=PAYLOAD,expect={9:5,10:0}),event(2,result=STOPPED,unchanged=True)],images['medium'][1],prefix=True)
    # The parser intentionally searches past arbitrary preamble for JZJZ. An
    # invalid chunk header after that magic is an actual framing error.
    add('document/parser-error-preserves-later-ready',[reserve(b'JZJZ'+bytes(16)),reserve(doc(['small']),1),
        complete(1,len(doc(['small']))),complete(0,20),event(2,result=PAYLOAD,expect={3:0,4:2,5:1}),
        event(2,result=STOPPED,unchanged=True)])
    # Consumer failure after one acceptance must retain both incoming ownership
    # and already accepted image output until separately supplied quiescence.
    first=transfers(doc(['medium']),1024,True)
    # Use complete document in one reservation when possible; otherwise stop
    # event construction at the first failing pump, determined explicitly below.
    for reverse in (False,True):
        add(f'document/output-failure-recovery/reverse={reverse}',first,images['medium'][1],fail_at=1,prefix=True)
    add('document/cancel-mid-header-recovery',transfers(doc(['medium'])[:11],7,True)+[event(4)]+restart(1,True)+
        [complete(0,7,result=STALE),event(11,1,0x80,result=STALE,unchanged=True)]+
        transfers(doc(['small']),64,True)+[event(3,expect={1:2,10:1,17:1,18:1})],images['small'][1])

    cases=[];target_inputs=[]
    def execute(candidate,events):
        wire=b''.join(struct.pack('>6I',*e['words'],len(e['data']))+e['data'] for e in events)
        path=temp/'events';path.write_bytes(wire)
        observed=json.loads(core.command([temp/'host',path,candidate['fill'],candidate['mode'],candidate['fail_at'],
            temp/'capture',temp/'receive',temp/'output',temp/'received']))
        return wire,observed,[(temp/name).read_bytes() for name in ('capture','receive','output','received')]
    for candidate in candidates:
        events=candidate['events']
        wire,observed,captures=execute(candidate,events)
        if candidate['name'].startswith('document/output-failure-recovery/'):
            failed=next(i for i,row in enumerate(observed) if row[0]==PAYLOAD)
            events=events[:failed+1];events[-1]={**events[-1],'result':PAYLOAD,'expect':{5:1,9:3,13:1,14:0,15:1}}
            acknowledgements=[event(5,1),event(6,1)]
            if candidate['name'].endswith('True'):acknowledgements.reverse()
            events += [event(2,result=STOPPED,unchanged=True),event(3,result=STOPPED,unchanged=True),
                acknowledgements[0],event(7,result=ORDER,unchanged=True),acknowledgements[1],event(7),
                complete(0,1,result=STALE)]+transfers(doc(['small']),64,True)+[event(3,expect={1:2,10:1,17:1,18:1})]
            wire,observed,captures=execute(candidate,events)
            candidate['expected']=images['medium'][1][:4800]+images['small'][1];candidate['prefix']=False
        assert len(observed)==len(events)
        for i,(e,row) in enumerate(zip(events,observed)):
            assert row[0]==e['result'],(candidate['name'],i,e,row)
            assert row[23:25]==[0,1],(candidate['name'],i,'guard or ownership violation',row)
            assert all(row[int(at)]==v for at,v in e['expect'].items()),(candidate['name'],i,e,row)
            if e['unchanged'] and i:assert row[1:]==observed[i-1][1:],(candidate['name'],i,'state changed')
        capture,receive,output,received=captures;expected=candidate['expected']
        assert capture==(expected[:len(capture)] if candidate['prefix'] else expected),(candidate['name'],'pixels')
        assert received==candidate['raw'],(candidate['name'],'received order')
        final=observed[-1]
        assert final[11:13]==[len(capture),core.fnv(capture)]
        assert final[21:23]==[core.fnv(receive),core.fnv(output)]
        if candidate['name'].startswith('cancel/'):
            assert final[4:8]==[0,0,0,0] and final[8:11]==[0,0,0]
        record=dict(case=candidate['name'],status='pass',event_count=len(events),
            events_sha256=core.sha(wire),steps=observed,output_sha256=core.sha(capture),output_bytes=len(capture),
            receive_storage_sha256=core.sha(receive),output_storage_sha256=core.sha(output),
            raw_received_sha256=core.sha(received),fill=candidate['fill'],consumer_mode=candidate['mode'],
            fail_at=candidate['fail_at'],source_prefix_only=candidate['prefix'])
        cases.append(record);target_inputs.append((candidate,events,observed,captures))
    print(f'USB receive: {len(cases)} sanitized host cases passed',flush=True)
    target=None
    if args.target:
        core.command(['bash',ROOT/'scripts/build-hp1020-usb-receive-target.sh'])
        elf=OUT/'target/target-check.elf';program,audit=core.audit_target(elf)
        shutil.copyfile(elf,temp/'target-check.elf')
        from hp1020_qemu_ram import QemuRAM
        native=[]
        with QemuRAM() as q:
            q.load(elf);version=q.version
            for candidate,events,observed,captures in target_inputs:
                assert q.call0(program.symbols['hp1020_rx_fixture_reset'],
                    [candidate['fill'],candidate['mode'],candidate['fail_at']])==0
                target_steps=[]
                for i,(e,host_row) in enumerate(zip(events,observed)):
                    if e['data']:q.put(program.symbols['hp1020_rx_fixture_input'],e['data'])
                    r=q.call0(program.symbols['hp1020_rx_fixture_step'],e['words'])
                    row=list(struct.unpack('>48I',q.read(program.symbols['hp1020_rx_fixture_stats'],192)))
                    assert r==row[0] and row[:30]+row[32:]==host_row[:30]+host_row[32:],(candidate['name'],i,row,host_row)
                    target_steps.append(row)
                for symbol,capture in (('hp1020_rx_fixture_capture',captures[0]),('hp1020_rx_fixture_received',captures[3])):
                    assert q.read(program.symbols[symbol],len(capture))==capture,candidate['name']
                for function,capture in (('hp1020_rx_fixture_storage',captures[1]),('hp1020_rx_fixture_output',captures[2])):
                    address=q.call0(program.symbols[function],[]);assert q.read(address,len(capture))==capture,candidate['name']
                native.append(dict(case=candidate['name'],status='pass',all_steps_equal=True,
                    all_pixels_and_storage_equal=True,state_and_memory_bytes=sum(target_steps[-1][30:32])))
                if len(native)%10==0:print(f'USB receive: {len(native)}/{len(cases)} QEMU cases passed',flush=True)
        sizes={c['state_and_memory_bytes'] for c in native};assert len(sizes)==1
        target=dict(status='pass',cases=native,qemu_version=version,elf_sha256=core.sha(elf.read_bytes()),
            state_and_memory_bytes=sizes.pop(),audit=audit)
    assert all(core.sha((ROOT/n).read_bytes())==h for n,h in tested.items()),'source changed during execution'
    report=dict(status='pass',cases=cases,target=target,source_sha256=tested,
        fixture_sha256={str(p.relative_to(ROOT)):core.sha(p.read_bytes()) for p in fixture_paths},
        sample_sha256={str(base_path.relative_to(ROOT)):core.sha(base_path.read_bytes())},
        completed_native_page_lifecycles=0,usb_transfers=0,
        scope='Compiled fixed receive queue feeding the bounded ZjStream/JBIG/output composition, with explicit synthetic transfer observations and separately supplied quiescence.',
        limits='No USB controller, device descriptor scheduling, DMA/cache synchronization, endpoint configuration, physical abort/reset, boot or printing is implemented or proven. RX==0 and L==1 are a conservative single-descriptor policy, not HP success semantics. The caller must serialize events and truthfully establish receive/output quiescence; this code cannot prove it. Copies remain metadata.')
    name='validation' if args.target else 'host-validation'
    (OUT/f'{name}.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    (OUT/f'{name}.md').write_text('# Bounded USB receive/document software\n\n'+report['scope']+'\n\n'
        +f'{len(cases)} sanitized host cases; {len(target["cases"]) if target else 0} independent QEMU cases.\n\n'
        +(f'Target state and fixed memory: {target["state_and_memory_bytes"]} bytes, excluding code, stack and fixture captures.\n\n' if target else '')
        +report['limits']+'\n')
    print(f'USB receive: {len(cases)} host cases; target={len(target["cases"]) if target else "not run"}',flush=True)

if __name__=='__main__':main()
