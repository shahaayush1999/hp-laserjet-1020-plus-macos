#!/usr/bin/env python3
"""Independent saved-evidence gate for the 28-case program experiment.

Standard library only. No producer imports, decoder/firmware execution, hardware
I/O or use of program_oracles/expected_program_trace as the oracle. The latter
is checked against an independently reconstructed trace, never trusted as input.

Public helper: check_program_report(report, capture_root=None, source_root=None)
returns (passed, detail). A capture root seals raw stdin/stdout, binary I/O logs,
all storage, source/fixture snapshots and target replay; without it, the gate
checks report rows and independently computed capture digests. A source root
option additionally checks current repository source/target bytes.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

U32 = 0xffffffff
DEVICE = bytes.fromhex('1201000200000040feca0040000100000001')
# Audited literal contracts, independent of production constants and of the
# producer's imported trace-oracles.py. Row = kind, offset, logical word, result.
OUT_INITIAL = (
    (1,0x220,0x51,0),(2,0x220,0xa0,0),
    (1,0x22c,0x80,0),(2,0x22c,0x40,0),
    (1,0x508,0x100000c1,0),(2,0x508,0x020000c1,0),
    (1,0x418,0x00a700a7,0),(2,0x418,0x00a500a7,0),(3,U32,0,0))
IN_INITIAL = (
    (1,0x028,0x40,0),(1,0x020,0x51,0),(2,0x020,0xa0,0),
    (1,0x02c,0x80,0),(2,0x02c,0x40,0),
    (1,0x50c,0x100000d1,0),(2,0x50c,0x020000d1,0),
    (1,0x418,0x00a500a7,0),(2,0x418,0x00a500a5,0),(3,U32,0,0))
OUT_RESELECT = (
    (1,0x220,0x61,0),(2,0x220,0xa0,0),
    (1,0x22c,0x40,0),(2,0x22c,0x40,0),
    (1,0x508,0x020000c1,0),(2,0x508,0x020000c1,0),
    (1,0x418,0x00a700a7,0),(2,0x418,0x00a500a7,0),(3,U32,0,0))
IN_RESELECT = (
    (1,0x028,0x40,0),(1,0x020,0x61,0),(2,0x020,0xa0,0),
    (1,0x02c,0x40,0),(2,0x02c,0x40,0),
    (1,0x50c,0x020000d1,0),(2,0x50c,0x020000d1,0),
    (1,0x418,0x00a500a7,0),(2,0x418,0x00a500a5,0),(3,U32,0,0))
OUT_SI = OUT_RESELECT[:6] + (
    (1,0x418,0x00a500a5,0),(2,0x418,0x00a500a5,0),(3,U32,0,0))
IN_SI = IN_RESELECT[:7] + (
    (1,0x418,0x00a500a5,0),(2,0x418,0x00a500a5,0),(3,U32,0,0))
CLOSE = (
    (1,0x418,0x00a500a5,0),(2,0x418,0x00a700a7,0),
    (1,0x220,0x60,0),(2,0x220,0xa0,0),(2,0x234,0,0),
    (1,0x020,0x60,0),(2,0x020,0xa0,0),(2,0x034,0,0),(3,U32,0,0))
GRANT = ((1,0x404,0x34120320,0),(3,U32,0,0),
         (2,0x404,0x34122320,0),(3,U32,0,0))
INITIAL, RESELECT, SI = OUT_INITIAL+IN_INITIAL, OUT_RESELECT+IN_RESELECT, OUT_SI+IN_SI
# Each pair is the one actual API opcode permitted to emit this entire block.
BLOCKS = {
 'sc1-grant-and-page': [(1,INITIAL),(124,((1,0x404,0x34120324,0),)),(124,GRANT)],
 'repeated-sc1-owned': [(1,INITIAL),(124,GRANT),(1,CLOSE+RESELECT),(124,GRANT)],
 'si-explicit-programming': [(1,INITIAL),(124,GRANT),(123,SI),(124,GRANT)],
 'sc0-and-reset-history': [(1,INITIAL),(124,GRANT),(1,CLOSE),(124,GRANT),
     (124,GRANT),(1,RESELECT),(123,CLOSE),(124,GRANT)],
 'stale-held-grant': [(1,INITIAL)],
 'fifo-mismatch-cleanup': [(1,OUT_INITIAL+((1,0x028,0x20,0),)),(1,INITIAL),(124,GRANT)],
 'read-then-partial-write-failure': [(1,((1,0x220,0,1),)),
     (1,OUT_INITIAL+IN_INITIAL[:4]+((2,0x02c,0x40,2),)),(1,INITIAL),(124,GRANT)],
 'void-close-failure': [(1,INITIAL),(124,GRANT),(1,CLOSE[:4]+((2,0x234,0,2),))],
 'si-write-failure': [(1,INITIAL),(124,GRANT),(123,OUT_SI+IN_SI[:8]+((2,0x418,0x00a500a5,1),))],
 'grant-pre-order-failure': [(1,INITIAL),(124,GRANT[:1]+((3,U32,0,1),))],
 'grant-write-uncertain': [(1,INITIAL),(124,GRANT[:2]+((2,0x404,0x34122320,2),))],
 'grant-post-order-failure': [(1,INITIAL),(124,GRANT[:3]+((3,U32,0,2),))],
 'raw-configuration-field-guards': [(1,INITIAL),(1,CLOSE)]+[(1,INITIAL)]*2,
 'raw-sc0-after-reset': [(1,INITIAL),(124,GRANT)],
}
# Independent callback-entry witness kind for each newly failed attempt.
FAILURES = {
 'fifo-mismatch-cleanup': [3], 'read-then-partial-write-failure': [2,3],
 'void-close-failure': [4], 'si-write-failure': [5],
 'grant-pre-order-failure': [6], 'grant-write-uncertain': [6],
 'grant-post-order-failure': [6], 'raw-configuration-field-guards': [4,4,2,2,7,7],
 'raw-sc0-after-reset': [7],
}
PAGE_GENERATION = {'sc1-grant-and-page':2, 'fifo-mismatch-cleanup':2,
    'read-then-partial-write-failure':2, 'repeated-sc1-owned':3,
    'si-explicit-programming':3}
FINAL_GENERATION = {name: (1 if name.startswith('grant-') else
    3 if name in ('repeated-sc1-owned','si-explicit-programming','sc0-and-reset-history') else 2)
    for name in BLOCKS}
AUTO_BINDS = {'sc1-grant-and-page':1,'repeated-sc1-owned':2,'si-explicit-programming':2,
    'sc0-and-reset-history':5,'stale-held-grant':1,'fifo-mismatch-cleanup':1,
    'read-then-partial-write-failure':1,'void-close-failure':1,'si-write-failure':2,
    'grant-pre-order-failure':1,'grant-write-uncertain':1,'grant-post-order-failure':1,
    'raw-configuration-field-guards':2,'raw-sc0-after-reset':1}
RAW_REQUESTS = {
    'si-explicit-programming': ['0203000001000000','0203000081000000'],
    'stale-held-grant': ['8006000100001200'],
    'raw-sc0-after-reset': ['0009000000000000']*2,
    'raw-configuration-field-guards': [
        '0009000000000000','8009000000000000','0009010000000000','0009000000000000',
        '0009000001000000','0009000100000000','0009010001000000','0009010100000000',
        '0009000001000000','0009000100000000'],
}
CAPTURE_NAMES = {'pixels':'pixels','wire':'wire','documents':'documents',
    'receive':'receive','output':'output','ep0':'output.ep0-descriptors',
    'bulk_descriptor':'output.udc-descriptor','setup_record':'output.setup-record',
    'program_reads':'output.program-read-script','program_trace':'output.program-trace',
    'program_storage':'output.program-storage'}
WIDTHS = (96,104,48,40,80,64)
KEYS = ('steps','ep0_steps','bulk_steps','setup_steps','offload_steps','program_steps')
INITIAL_KEYS = ('initial','initial_ep0','initial_bulk','initial_setup','initial_offload','initial_program')


class EvidenceError(ValueError):
    pass


def need(condition, message):
    if not condition:
        raise EvidenceError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def packed(words):
    return b''.join(v.to_bytes(4,'big') for v in words)


def flat(rows):
    return b''.join(packed(row) for row in rows)


def fnv(raw):
    value = 2166136261
    for byte in raw:
        value = ((value ^ byte)*16777619)&U32
    return value


def uints(row, size, where):
    need(isinstance(row,list) and len(row)==size and
         all(type(v) is int and 0<=v<=U32 for v in row), where+': expected unsigned words')


def sealed_file(root, name, digest, where):
    path = Path(name)
    need(not path.is_absolute() and '..' not in path.parts and path.as_posix()==name,
         where+': unsafe saved path '+str(name))
    need(isinstance(digest,str) and re.fullmatch('[0-9a-f]{64}',digest), where+': malformed digest '+name)
    if root is not None:
        need(sha((root/path).read_bytes())==digest,where+': bytes differ '+name)


def decode_events(raw, where):
    events, at = [], 0
    while at < len(raw):
        need(len(raw)-at>=24,where+': truncated event header')
        *words, length = struct.unpack_from('>6I',raw,at)
        at += 24
        need(length<=1024 and len(raw)-at>=length,where+': bad input payload extent')
        events.append((words,raw[at:at+length])); at += length
    return events


def split_row(row):
    parts, at = [], 0
    for size in WIDTHS:
        parts.append(row[at:at+size]); at += size
    return parts


def wire_signature(base, ep0, offload):
    # Includes zero-length publication counters and descriptor/staging witnesses.
    return (base[17],base[24:26],offload[57],
        ep0[8+14:8+22],ep0[8+31:8+35],ep0[8+42],
        ep0[56+14:56+22],ep0[56+31:56+35],ep0[56+42])


def source_contract(report, capture, source):
    sources, fixtures = report['source_sha256'], report['fixture_sha256']
    required = {
        'scripts/validate-hp1020-udc-program.py','scripts/build-hp1020-udc-program-target.sh',
        'open-firmware/udc-program/hp1020_udc_program.c','open-firmware/udc-program/hp1020_udc_program.h',
        'open-firmware/udc-program-test/fixture.c','open-firmware/udc-program-test/host-check.c',
        'open-firmware/udc-program-test/target-check.ld','open-firmware/udc-program-test/trace-oracles.py',
        'open-firmware/udc-composed-test/fixture.c','open-firmware/tinyusb-printer-test/fixture.c',
        'open-firmware/udc-ep0-test/fixture.c','open-firmware/udc-offload-test/fixture.c',
        'open-firmware/tinyusb-device/patches/manifest.json',
        'open-firmware/tinyusb-device/patches/protocol-compatibility.patch',
        'scripts/validate-hp1020-udc-offload.py','scripts/validate-hp1020-udc-composed.py',
        'scripts/validate-hp1020-udc-ep0.py','scripts/validate-hp1020-tinyusb-printer.py',
        'scripts/hp1020_qemu_ram.py','scripts/check-hp1020-c-compiler-profile.py',
        'scripts/prepare-hp1020-tinyusb.py','analysis/sihp1020.elf',
        'vendor/tinyusb-0.21.0/src/device/usbd.c'}
    components = {'tinyusb-printer-adapter':['tusb_adapter'], 'udc-setup':['udc_setup'],
        'udc-ep0':['udc_ep0'],'udc-out':['udc_out'],'usb-printer-class':['usb_printer'],
        'usb-receive-core':['usb_receive','usb_document'],
        'image-core':['image','image_page','image_stream','image_ring','image_output'],
        'semantic-core':['semantic','page_plan']}
    required |= {'open-firmware/'+directory+'/hp1020_'+stem+'.'+ext
        for directory,stems in components.items() for stem in stems for ext in ('c','h')}
    need(required<=sources.keys(),'source closure: required implementation/fixture/tool missing')
    for name,digest in sources.items():
        sealed_file(source,name,digest,'current source')
        if capture is not None: sealed_file(capture/'source',name,digest,'saved source')
    expected_fixtures = {
        'analysis/open-firmware-model/image-core/fixtures/32x8-stripe4-black.jbg',
        'analysis/open-firmware-model/image-core/fixtures/9600x132-stripe128-edges.jbg',
        'analysis/open-firmware-model/image-core/fixtures/16384x4-stripe128-edges.jbg',
        'analysis/open-firmware-model/image-core/output-fixtures/1024x260-stripe128-repeat.jbg',
        'analysis/open-firmware-model/image-core/output-fixtures/64x12-stripe4-edges.jbg',
        'analysis/samples/generated/matrix-a4_default.zjs'}
    need(set(fixtures)==expected_fixtures,'source closure: exact six document fixtures')
    for name,digest in fixtures.items():
        sealed_file(source,name,digest,'current fixture')
        if capture is not None: sealed_file(capture/'tested-fixtures',name,digest,'saved fixture')
    need(sources['analysis/sihp1020.elf']=='2111560068db47ceca21fa550db4c7c34f5595b5a5d137ae4a19631e40e3601d',
         'source closure: original stock bytes changed')
    effective = report['effective_source']; manifest = effective['patch_manifest']
    prefix = 'open-firmware/tinyusb-device/patches/'
    need(effective['patched'] is True and effective['upstream_commit']==manifest['upstream_commit']==
         'dae3f9a366bfcddbf9dcf1b48d7500286a849539','effective source: pinned TinyUSB identity')
    need(manifest['patch_sha256']==sources[prefix+'protocol-compatibility.patch'],
         'effective source: patch identity')
    originals = {n[len('vendor/tinyusb-0.21.0/'):]:d for n,d in sources.items()
        if n.startswith('vendor/tinyusb-0.21.0/') and not n.endswith('/PROVENANCE.json')}
    need(len(originals)==19 and set(manifest['files'])=={'src/device/usbd.c','src/device/usbd_pvt.h'},
         'effective source: exact upstream closure')
    wanted = originals.copy()
    for name,item in manifest['files'].items():
        need(originals[name]==item['original_sha256'],'effective source: patch input '+name)
        wanted[name]=item['result_sha256']
    need(effective['effective_sha256']==wanted,'effective source: patched file hashes')
    for root in ([source] if source is not None else [])+([capture/'source'] if capture is not None else []):
        need(json.loads((root/(prefix+'manifest.json')).read_bytes())==manifest,'saved/current patch manifest')
    for ref in report['original_reference'].values():
        need(ref['newly_executed_stock_instructions']==0 and ref['stock_sha256']==sources['analysis/sihp1020.elf']
             and ref['report_sha256']==sources[ref['report']],'original reference: exact reused bytes/report')
    need(all(n in sources and d==sources[n] for n,d in report['offload_mode_evidence'].items()),
         'mode evidence: exact source binding')
    if capture is not None:
        need(json.loads((capture/'source-sha256.json').read_bytes())==sources,'saved source manifest')
        need(json.loads((capture/'fixture-sha256.json').read_bytes())==fixtures,'saved fixture manifest')


def check_case(case, native, directory):
    name = case['scenario'].removeprefix('program/'); fill=case['fill']
    where = case['case']
    def ck(value, message): need(value,where+': '+message)
    ck(name in BLOCKS and fill in (0,204) and case['capacity']==64 and case['interface']==0,'profile inputs')
    ck(where==f'program/{name}/fill={fill}/capacity=64/interface=0','canonical case identity')
    ck(case['status']==native['status']=='pass' and native['case']==where,'paired case identity/status')
    for flag in ('all_steps_equal','all_pixels_wire_notifications_descriptors_and_storage_equal',
                 'typed_captures_original_cookies_and_grants_equal','complete_recorded_io_and_explicit_read_script_equal'):
        ck(native.get(flag) is True,'missing target comparison '+flag)
    events = case['events']; count=len(events)
    ck(count>0 and all(len(case[k])==count for k in KEYS),'parallel event/row lengths')
    old=[]
    for key,size in zip(INITIAL_KEYS,WIDTHS):
        uints(case[key],size,where+'/'+key); old.append(case[key])
    ck(old[0][32]==1 and old[5][1:8]==[1,0,0,0,0,0,0] and old[5][24:32]==[0,0,0,0,0,0,1,0],
       'initial generation, fresh backend and empty I/O ledger')
    ck(old[5][57]>0 and old[5][36:43]==[1]*7,'measured host component and supplied initial facts')
    raw_events=b''; reads=[]; trace=[]; cursor=0; block_index=0; failed_count=0
    injection=None; facts=[1]*7; offers={}; auto={}; ep0_owners={}; publications=[]
    raw_requests=[]; raw_offers={}; live_record=None; ingress_sequence=0
    active_input=None; raw_admissions={}; typed_admissions={}
    seen_failures=[]; grant_count=0; cleanup_count=0; missing_grants=set(); malformed_grants=set()
    successful_recoveries=[]; reset_tickets={}; failures=FAILURES.get(name,[])
    wire_expected=DEVICE if name=='stale-held-grant' else b''
    packet_lengths = ([0,0] if name=='si-explicit-programming' else
        [18] if name=='stale-held-grant' else [0]*4 if name=='raw-configuration-field-guards' else
        [0] if name=='raw-sc0-after-reset' else [])
    expected_publications = [(0x80,n) for n in packet_lengths]
    if name=='stale-held-grant': expected_publications.append((0,0))
    for index,event in enumerate(events,1):
        words=event['words']; uints(words,5,where+f'/event{index}')
        data=bytes.fromhex(event['data_hex']); op,a,b,c,d=words
        ck(len(data)<=1024,'event payload bound')
        raw_events += packed(words+[len(data)])+data
        current=[case[k][index-1] for k in KEYS]
        for row,size in zip(current,WIDTHS): uints(row,size,where+f'/event{index}')
        r,e,u,s,o,p=current; pr,pe,pu,ps,po,pp=old
        ck(r[0]==event['result'],f'event{index} result differs from row')
        ck(r[15:17]==[0,1] and e[2:5]==[0,1,1] and u[7:10]==[0,1,1]
           and s[12:15]==[0,1,3] and o[11:13]==[0,1] and p[1:4]==[1,0,0]
           and p[30:32]==[1,0],f'event{index} ownership/guard witness')
        ck(r[86]==s[10]==0,'unexpected exhaustion/terminal in bounded matrix')
        ck(p[57]==case['initial_program'][57],'fixed measured host component size')
        ck(r[80]==0 and r[47]==0,'no fabricated printer class reset/reply permission')
        if op in (0,2,3,4,5,102,106,107):
            ck(op in (102,106,107) and r[0]==3,'forbidden bypass operation')
        if op==120:
            ck(0<a<=85 and len(data)==12*a and b==c==d==0 and r[0]==0,'read script admission')
            rows=[list(struct.unpack_from('>3I',data,j)) for j in range(0,len(data),12)]
            ck(all(x[2]<=2 for x in rows),'read script result domain')
            reads.extend(rows)
        if op==121:
            ck(a in (2,3) and c in (1,2) and b>len(trace) and not data and r[0]==0 and injection is None,
               'one-shot write/order injection')
            injection=(a,b,c)
        if op==122:
            ck(len(data)==7 and r[0]==0,'program facts input'); facts=list(data)
        ck(p[36:43]==facts,'program facts retained exactly, without truthiness normalization')
        if op==124:
            ck(len(data)==5,'grant facts input'); ck(p[43:48]==list(data),'grant facts retained exactly')
            if 0 in data: missing_grants.update(i for i,v in enumerate(data) if v==0)
            if 2 in data: malformed_grants.update(i for i,v in enumerate(data) if v==2)
        delta=p[26]-len(trace)
        ck(delta>=0,'attempt trace count cannot go backwards')
        block=()
        if delta:
            ck(block_index<len(BLOCKS[name]),f'event{index} unexpected extra I/O block')
            wanted_op,block=BLOCKS[name][block_index]; block_index+=1
            ck(op==wanted_op and delta==len(block),f'event{index} API/complete literal block length')
            for kind,offset,value,outcome in block:
                ordinal=len(trace)+1
                if kind==1:
                    ck(cursor<len(reads),f'event{index} unsupplied read')
                    sample=reads[cursor]; cursor+=1
                    ck(sample==[offset,value,outcome],f'event{index} independent read observation at{offset:x}')
                else:
                    expected_outcome=0
                    if injection is not None and injection[1]==ordinal:
                        ck(injection[0]==kind,'failure injector hook kind')
                        expected_outcome=injection[2]; injection=None
                    ck(outcome==expected_outcome,'attempt outcome must come from exact original injection')
                trace.append([index,ordinal,kind,offset,0 if kind==1 and outcome else value,outcome])
        ck(p[24:27]==[len(reads),cursor,len(trace)],f'event{index} queue/cursor/attempt counts')
        ck(p[27:30]==[sum(x[2]==k for x in trace) for k in (1,2,3)],'R/W/order counters')
        ck(p[35]==int(injection is not None),'injector consumed exactly once')
        if injection is not None: ck(p[32:35]==list(injection),'retained failure injection identity')
        if op in (81,83,100):
            ck(a==ingress_sequence+1,'new ingress keeps one external nonwrapping order')
            ingress_sequence=a
        if op==80:
            ck(r[0]==0 and len(data)==16 and data[:8]==bytes.fromhex('87ff7fffa5c33ca5'),
               'exact original supplied SETUP record envelope')
            live_record=data; raw_requests.append(data[8:].hex())
            ck(packed(s[28:32])==data,'live record equals supplied immutable bytes')
        if op==81:
            ck(r[0]==0 and b==0x79bdf130 and c==d==0 and live_record is not None,'raw capture identity/profile')
            raw_offers[a]=live_record
            ck(s[22:26]==[a,b,0,0] and packed(s[32:36])==live_record
               and r[2:96]==pr[2:96],'raw capture copies exact original without dispatch')
        if op==82:
            ck(a in raw_offers,'raw dispatch has an original retained capture')
            if r[0]==0:
                ck(b==0x010101 and c==1 and s[6]==a and r[2]==pr[2]+1,
                   'raw admission requires every exact supplied fact')
                raw_admissions[a]=raw_offers[a][8:]; active_input=('raw',a)
            else:
                ck(name=='stale-held-grant' and b==0x010001 and r[0]==1
                   and r[2:96]==pr[2:96],'missing capture fact cannot supersede current ownership')
        if op==83:
            ck(r[0]==0 and b==c==d==0 and r[2]==pr[2]+1 and s[5]==a and s[8]==r[2],
               'actual reset preserves original event, with no supplied cleanup')
            ck(p[5:7]==pp[5:7] and r[32]==pr[32],'reset does not erase command history or recover document')
            active_input=('reset',a)
        if op==100:
            ck(r[0]==0 and not data and 0<a<U32 and a not in offers,'typed original event admission')
            offers[a]=[a,b,c>>16,(c>>8)&255,c&255]
            ck(o[21:26]==offers[a] and r[2:96]==pr[2:96] and s[32:36]==ps[32:36],
               'typed offer cannot dispatch, fabricate raw bytes or mutate transport')
        if op==101:
            ck(a in offers and b==0x01010101 and c==d==0 and r[0]==0
               and s[6]==a and r[2]==pr[2]+1,'typed admission of exact original with separate facts')
            typed_admissions[a]=offers[a]; active_input=('typed',a)
        if o[6]!=po[6]:
            ck(o[6]==po[6]+1 and o[26] in offers,'one original typed owner per actual bind')
            cookie=[r[21],r[3],r[32],0,0x80]
            ck(cookie[0] not in auto and o[16:21]==cookie and o[26:31]==offers[o[26]],'original auto-owner identity')
            ck(o[13]==1 and o[32:35]==[1,0,1] and r[28:30]==[cookie[0],0] and r[77]==0,
               'retained NULL/0 owner has no class response')
            ck(e[8]==e[56]==0 and wire_signature(r,e,o)[1:]==wire_signature(pr,pe,po)[1:],
               'typed owner creates no descriptor, packet, wire bytes or ACK')
            canonical=bytes([0,9,offers[o[26]][2],0,0,0,0,0]) if offers[o[26]][1]==1 else bytes([1,11,0,0,0,0,0,0])
            ck(packed(o[64:66])==canonical,'typed canonical input separate from raw capture')
            auto[cookie[0]]=(cookie,offers[o[26]].copy())
        if o[13]: ck(o[16] in auto and o[16:21]==auto[o[16]][0],'held auto cookie cannot be retagged')
        for slot in (0,1):
            cur=e[8+48*slot:56+48*slot]; before=pe[8+48*slot:56+48*slot]
            token=cur[6]
            if token and token not in ep0_owners:
                cookie=[r[21],r[3],r[32],0,slot*128]
                ck(cur[6:11]==cookie and token not in auto,'ordinary EP0 original cookie')
                ep0_owners[token]=(cookie,cur[5])
                ck(cur[5] in packet_lengths+[0],'ordinary EP0 packet length in independent profile')
                ck(cur[14:18]==[0x08000000|cur[5],0,(0x3579bdf0,0xb68ace00)[slot],0],
                   'ordinary EP0 descriptor construction')
                ck(cur[46]==int(cur[5]==0),'ZLP original NULL identity')
            if cur[32]!=before[32]:
                ck(cur[32]==before[32]+1 and cur[22] in ep0_owners,'one ordinary publication')
                cookie,length=ep0_owners[cur[22]]
                ck(cur[22:27]==cookie and cur[27:31]==[(0x13579bd0,0xa468ace0)[slot],
                    (0x3579bdf0,0xb68ace00)[slot],length,64],'actual submitted ordinary pointers/span/cookie')
                ck(cur[18:22]==[0x08000000|length,0,(0x3579bdf0,0xb68ace00)[slot],0]
                   and cur[47]==int(length==0),'ordinary immutable published descriptor/ZLP')
                publications.append((slot*128,length))
        consumed=int(any(x[0]==2 and x[1]==0x404 for x in block))
        if op==124:
            ck(wire_signature(r,e,o)==wire_signature(pr,pe,po),'grant created submission/descriptor/wire/status ACK')
            ck(r[32:48]==pr[32:48] and r[90:96]==pr[90:96],'grant supplied document recovery or notification')
            ck(o[7]==po[7]+consumed and o[33]==po[33]+consumed,'exact one-shot grant consumption')
            if consumed:
                ck(a in offers and b in auto and not c and auto[b][1]==offers[a],'grant original event/token')
                ck(o[37:42]==offers[a] and o[42:47]==auto[b][0],'consumed grant retains original cookie/generation')
                ck(o[13]==1 and r[28]==b,'consumed grant is not settlement')
            grant_count+=consumed
        else: ck(o[7]==po[7],'grant count changed outside actual backend grant')
        if p[4] and not pp[4]:
            ck(failed_count<len(failures),'unexpected newly failed attempt')
            witness=failures[failed_count]; failed_count+=1
            typed_sequence=(active_input[1] if op==1 and active_input and active_input[0]=='typed'
                else po[26] if op in (123,124) else 0)
            ticket=[typed_sequence,pr[2] if op==1 else pr[3],pr[4]]
            ck(p[16:19]==p[58:61]==ticket and p[61]==witness and p[62]==pp[62]+1,
               'first failure must match independently captured original entry identity/kind')
            ck(o[68]==1 and o[69:72]==ticket,'independent old-ledger failed-attempt witness')
            seen_failures.append(ticket)
            if block and block[-1][3]:
                kind,offset,value,outcome=block[-1]
                wanted=[kind,offset,0 if kind==1 else value,outcome,consumed]
            elif block and block[-1]==(1,0x028,0x20,0): wanted=[4,0x028,0x20,1,0]
            else: wanted=[5,U32,0,1,0]
            ck(p[19:24]==wanted,'failure operation/offset/attempt/outcome/consumption')
            ck(p[7]==0 and r[0]==4,'failure blocks binding and propagates after void callback')
            if o[59]: ck(o[60:63]==ticket,'adapter dirty ticket agrees before later fence')
        elif pp[4] and not (op==126 and r[0]==0):
            ck(p[4]==1 and p[16:24]==pp[16:24] and p[58:63]==pp[58:63],'first failure retained across reset/refusal')
        if op==126:
            ck(not block and r[32:48]==pr[32:48] and wire_signature(r,e,o)==wire_signature(pr,pe,po),
               'cleanup cannot perform I/O/forward traffic/recovery')
            if r[0]==0:
                cleanup_count+=1
                ck(pp[4]==1 and [a,b,c]==pp[16:19] and d==1,'exact supplied clean promise for original failure')
                ck(pr[7]==pr[36]==1 and not any(pr[x] for x in (8,10,26,28,30,77,85)) and pu[44]==0,
                   'cleanup needs stopped/unmounted and no DCD/PENDING/prepared/response owner')
                ck(p[4:8]==[0,0,0,0] and p[10:13]==[0,0,0] and not o[59],
                   'cleanup only clears barriers and command history')
            else: ck(p[4:8]==pp[4:8] and p[16:24]==pp[16:24],'failed cleanup mutated original failure')
        if op==10 and r[0]==0: reset_tickets[a]=pr[42:44]
        if r[32]!=pr[32]:
            ck(op==12 and r[0]==0 and r[32]==pr[32]+1 and a in reset_tickets
               and reset_tickets[a]==pr[42:44] and pr[44]==1 and pr[45]==7,
               'generation advances only after same three-promise recovery')
            successful_recoveries.append(r[32])
            ck(r[17]==pr[17] and r[24:26]==pr[24:26] and o[57]==po[57],
               'internal recovery cannot send class/automatic status ACK')
        if op==11 and r[0]==0:
            ck(a in reset_tickets and reset_tickets[a]==pr[42:44] and b in (1,2,4)
               and r[45]==(pr[45]|b) and r[32]==pr[32],'individual current recovery promise')
        if op==125 and r[0]==0:
            ck(p[48:51]==p[16:19] and p[51:56]==[p[20],p[21],p[19],p[22],p[23]] and p[56]==0,
               'queried failure original identity and fields')
        if p[4]: ck(p[8] in (0,1),'failed backend grants no ARM/PUMP permission')
        if not pp[8] and op in (1,6,7,8,9,12,41,61):
            ck(r[0]==1 and r[17]==pr[17] and r[24:26]==pr[24:26] and r[50:59]==pr[50:59],
               'blocked forward operation altered submissions/output')
        old=current
    r,e,u,s,o,p=old
    ck(block_index==len(BLOCKS[name]) and cursor==len(reads) and injection is None,'all independent trace blocks/reads consumed')
    ck(raw_requests==RAW_REQUESTS.get(name,[]),'exact raw request inputs, including low-byte aliases')
    ck(failed_count==len(failures) and cleanup_count==len(failures),'each expected failure explicitly cleaned once')
    ck(o[6]==AUTO_BINDS[name] and o[7]==grant_count,'exact original-owner/grant totals')
    ck(publications==expected_publications,'exact ordinary control publication sequence, including ZLPs')
    ck(o[57]==len(packet_lengths),'exact genuine TinyUSB status callback count')
    ck([bytes.fromhex(x['expected_hex']) for x in case['packet_oracles']]==
       ([DEVICE] if name=='stale-held-grant' else [b'']*len(packet_lengths)),
       'ordinary packet byte oracles including empty packets')
    ck(r[32]==FINAL_GENERATION[name] and successful_recoveries==list(range(2,r[32]+1)),
       'exact generation/recovery schedule')
    if name=='sc1-grant-and-page': ck(missing_grants==malformed_grants==set(range(5)),'all five independent grant facts')
    generation=PAGE_GENERATION.get(name)
    pixels=b'\xff'*32 if generation is not None else b''
    documents=[[generation,1,0,1,0]] if generation is not None else []
    ck(case['pixels_bytes']==len(pixels) and case['expected_pixels_sha256']==sha(pixels)
       and case['expected_documents']==documents,'independent exact image/document oracle')
    ck(r[50:52]==[len(pixels),fnv(pixels)] and r[90:93]==[len(documents)]*3,'actual pixels/notifications')
    ck(r[24:26]==[len(wire_expected),fnv(wire_expected)],'actual ordinary reply bytes')
    ck(r[40]==0,'normal END_DOC must not fabricate input EOF')
    trace_raw,reads_raw=flat(trace),flat(reads)
    # Cross-check these untrusted report summaries only after independent rebuild.
    ck(case['expected_program_trace']==trace and case['supplied_reads']==reads,'trace/read summaries differ from independent rebuild')
    ck(len(reads)<=256 and len(trace)<=1024,'fixed recording allocation bounds')
    guard=bytes([fill])*16
    storage=guard+reads_raw+bytes([fill])*(3072-len(reads_raw))+guard
    storage+=guard+trace_raw+bytes([fill])*(24576-len(trace_raw))+guard
    expected={'pixels':pixels,'wire':wire_expected,'documents':flat(documents),
              'program_reads':reads_raw,'program_trace':trace_raw,'program_storage':storage}
    captures=case['capture_sha256']
    ck(set(captures)==set(CAPTURE_NAMES) and native['capture_sha256']==captures,'full paired capture closure')
    for key,raw in expected.items(): ck(captures[key]==sha(raw),'independent capture digest '+key)
    if directory is not None:
        ck((directory/'case-name').read_text().strip()==where,'saved case name')
        raw=(directory/'events.bin').read_bytes()
        ck(raw==raw_events and decode_events(raw,where)==[(x['words'],bytes.fromhex(x['data_hex'])) for x in events],
           'raw input framing/bytes differ from report')
        observed=[json.loads(line) for line in (directory/'raw-stdout').read_bytes().splitlines()]
        host_rows=[sum([case[k] for k in INITIAL_KEYS],[])]+[
            sum([case[k][i] for k in KEYS],[]) for i in range(count)]
        ck(observed==host_rows,'raw host initial/event rows differ from report')
        target_rows=[json.loads(line) for line in (directory/'target-steps.jsonl').read_bytes().splitlines()]
        ck(len(target_rows)==count,'target raw row count')
        for i,(actual,wanted) in enumerate(zip(target_rows,host_rows[1:]),1):
            uints(actual,432,where+f'/target{i}')
            ck(actual[:59]+actual[60:425]+actual[426:]==wanted[:59]+wanted[60:425]+wanted[426:],
               f'target event{i} differs outside measured footprint words')
            ck(actual[59]==native['adapter_state_and_memory_bytes'] and
               actual[425]==native['component_and_allocation_bytes']['program'],'target measured footprint binding')
        raw_captures={}
        for key,path in CAPTURE_NAMES.items():
            raw=(directory/path).read_bytes(); raw_captures[key]=raw
            ck(sha(raw)==captures[key],f'raw host capture hash {key}')
            ck((directory/('target-'+key)).read_bytes()==raw,f'raw target capture {key}')
            if key in expected: ck(raw==expected[key],f'raw independent expected bytes {key}')
        ck(fnv(raw_captures['receive'])==r[60] and fnv(raw_captures['output'])==r[61],'full retained memory witness')
        for key,words in (('bulk_descriptor',u[24:28]),('setup_record',s[28:32])):
            ck(raw_captures[key]==guard+packed(words)+guard,'full guarded '+key)
        ep=raw_captures['ep0']; ck(len(ep)==240,'full EP0 guarded storage length')
        for at in (0,32,64,144,224): ck(ep[at:at+16]==guard,'EP0 guard retention')
        for slot,(at,payload_at) in enumerate(((16,80),(48,160))):
            sl=e[8+slot*48:56+slot*48]
            ck(ep[at:at+16]==packed(sl[14:18]) and fnv(ep[payload_at:payload_at+64])==sl[42],
               'full retained EP0 descriptor/staging bytes')
    return count


def validate_program_report(report, capture_root=None, source_root=None):
    """Raise EvidenceError with one precise reason; no subprocesses or imports."""
    capture=Path(capture_root) if capture_root is not None else None
    source=Path(source_root) if source_root is not None else None
    need(report['status']=='pass' and report['target']['status']=='pass','paired host/target status required')
    for key in ('hp_dynamic_csr_capability_established','automatic_grants_are_acknowledgments','controller_quiescence_established'):
        need(report.get(key) is False,'must not claim hardware proof: '+key)
    for key in ('completed_native_page_lifecycles','usb_transfers','actual_peripheral_accesses'):
        need(type(report.get(key)) is int and report[key]==0,'must remain zero: '+key)
    source_contract(report,capture,source)
    cases=report['cases']; target=report['target']; natives=target['cases']
    need(len(cases)==len(natives)==28,'exact 28-case paired matrix')
    seen=set(); total=0
    for i,(case,native) in enumerate(zip(cases,natives)):
        pair=(case['scenario'].removeprefix('program/'),case['fill'])
        need(pair not in seen,'duplicate profile/fill'); seen.add(pair)
        total+=check_case(case,native,None if capture is None else capture/f'case-{i:03}')
    need(seen=={(name,fill) for name in BLOCKS for fill in (0,204)},'missing/extra profile/fill')
    artifacts=target['captured_artifact_sha256']
    need({'target-check.elf','target-check.map','effective-source.json','disassembly.txt','symbols.txt','annotated-disassembly.txt'}<=artifacts.keys(),
         'exact target artifact closure')
    need(target['elf_sha256']==artifacts['target-check.elf'] and target.get('audit'),'target ELF/audit binding')
    for name,digest in artifacts.items():
        need(Path(name).name==name,'target artifact must be a basename')
        sealed_file(None,name,digest,'target artifact')
        if capture is not None: sealed_file(capture/'target',name,digest,'saved target artifact')
        if source is not None and name!='annotated-disassembly.txt':
            sealed_file(source/'analysis/usb-path/udc-program/target',name,digest,'current target artifact')
    for root in ([capture/'target'] if capture is not None else [])+(
            [source/'analysis/usb-path/udc-program/target'] if source is not None else []):
        need(json.loads((root/'effective-source.json').read_bytes())==report['effective_source'],'target effective source exact equality')
    sizes=[n['component_and_allocation_bytes'] for n in natives]
    need(all(s==sizes[0] for s in sizes) and sizes[0]['ep0']==296 and sizes[0]['bulk']==80
         and sizes[0]['setup']==96 and type(sizes[0]['program']) is int and sizes[0]['program']>0,
         'consistent separately measured fixed target components')
    if capture is not None:
        need(json.loads((capture/'validation.json').read_bytes())==report,'saved report exact equality')
        need(json.loads((capture/'target-sha256.json').read_bytes())==artifacts,'saved target manifest')
    return f'28 paired cases; {total} raw event rows; independent command/pixel/owner/cleanup contracts'+(
        '; raw captures sealed' if capture is not None else '; report-only capture digests checked')


def check_program_report(report, capture_root=None, source_root=None):
    try:
        return True,validate_program_report(report,capture_root,source_root)
    except (EvidenceError,KeyError,TypeError,ValueError,IndexError,OSError,OverflowError) as error:
        return False,str(error)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report',type=Path)
    parser.add_argument('--capture-root',type=Path)
    parser.add_argument('--source-root',type=Path)
    args=parser.parse_args()
    passed,detail=check_program_report(json.loads(args.report.read_bytes()),args.capture_root,args.source_root)
    print(('PASS: ' if passed else 'FAIL: ')+detail)
    raise SystemExit(0 if passed else 1)


if __name__=='__main__':
    main()
