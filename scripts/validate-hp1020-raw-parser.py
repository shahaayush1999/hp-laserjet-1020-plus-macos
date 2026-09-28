#!/usr/bin/env python3
"""Execute original chunk-12 construction and admission without a raw IRQ.

The parser, allocator, queues and owner hierarchy run from stock bytes. Input,
document notification/publication and readiness remain explicit host boundaries.
Admission-only cases stop before the queued page/document endings. Separate
serialized continuations stop before VideoThread's first peripheral access.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import struct
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'analysis/hardware-boundary/raw-parser'
spec = importlib.util.spec_from_file_location('hp1020_raw_producer_validation',
    ROOT/'scripts/validate-hp1020-raw-producer.py')
raw = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = raw
spec.loader.exec_module(raw)

from hp1020_stock_parser_harness import CONTEXT, INPUT_CALLBACK, PUSHBACK_CALLBACK
from hp1020_stock_jobmgr_harness import JOB_CODE
from hp1020_stock_notifications import invoke
from hp1020_stock_queue import THREAD, BUFFER
from hp1020_xtensa_call0 import Program, Machine
from hp1020_qemu_ram import QemuRAM, RETURN
from hp1020_qemu_pipeline import start
import hp1020_raw_handoff as handoff
import hp1020_video_buffers as video_buffers

INPUT_HOST = {INPUT_CALLBACK,PUSHBACK_CALLBACK,0x1001262c,0x100126b0}
HOST = INPUT_HOST|{raw.READY,0x1000f164}
STOCK_SHA = '2111560068db47ceca21fa550db4c7c34f5595b5a5d137ae4a19631e40e3601d'
IMAGE = bytes(range(16))
BIH = bytes.fromhex('00000100')+struct.pack('>III',32,4,4)+bytes.fromhex('1000035c')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def item(key,value):
    return struct.pack('>IHBBI',12,key,1,0,value)


def chunk(kind,items=(),data=b''):
    metadata = b''.join(items)
    return struct.pack('>IIIHH',16+len(metadata)+len(data),kind,len(items),len(metadata),0x5a5a)+metadata+data


def stream(bitmap,copies,fallback,empty,page_bitmap,bih_chunk):
    page = [item(k,v) for k,v in [(4,copies),(8,600),(9,600),(12,32),(13,4),
                                 (16,1),(17,32),(18,4),(0x65,page_bitmap)]]
    band = [item(k,v) for k,v in [(20,4),(0x65,bitmap),(16,1),(0x67,1)]]
    if not fallback:
        band += [item(0x68,32),item(0x69,4)]
    band += [struct.pack('>IHBBI',32,0x66,4,0,20)+BIH]
    return (b'JZJZ'+chunk(0,[item(0,1),item(2,1)])+chunk(2,page)
            +(chunk(4,data=BIH) if bih_chunk else b'')
            +chunk(12,band,b'' if empty else IMAGE)+chunk(3)+chunk(1))


class Parser(raw.RawProducer):
    def __init__(self,program,fill,data,pool_size=16384):
        super().__init__(program,fill,pool_size=pool_size)
        self.code_ranges += JOB_CODE+[(0x10009b4c,0x1000a264),(0x1000f1c4,0x1000f280),
            (0x100111b4,0x100111ec),(0x100130c4,0x100130d4),
            (0x100169d4,0x10016a38),(0x1001b56c,0x1001b59c)]
        self.data,self.pos = data,0
        self.data_allocations,self.publications,self.boundaries = [],[],[]

    def observe(self,pc,register):
        if pc == 0x10009e40:
            self.data_allocations.append(dict(size=register(10),kind=register(11)))
        elif pc == 0x10009e43:
            self.data_allocations[-1]['pointer'] = register(10)

    def extension(self,op,args,nxt):
        if op == 'mul16u':
            # Standard unsigned low-halfword product. QEMU executes the original
            # opcode independently; this does not define any custom instruction.
            self.registers[args[0]] = (self.registers[args[1]]&65535)*(self.registers[args[2]]&65535)
            return nxt
        if op in ('call8','callx8'):
            target = self.registers[args[0]] if op == 'callx8' else args[0]
            a = self.registers[10:14]
            result = 0
            if target == INPUT_CALLBACK:
                assert a[0] == CONTEXT and a[3] == 0
                result = min(a[2],len(self.data)-self.pos)
                self.put(a[1],self.data[self.pos:self.pos+result])
                self.pos += result
                event = dict(service='read',requested=a[2],returned=result)
            elif target == PUSHBACK_CALLBACK:
                assert a[0] == CONTEXT and 0 <= a[2] <= self.pos
                assert self.bytes_at(a[1],a[2]) == self.data[self.pos-a[2]:self.pos]
                self.pos -= a[2]
                event = dict(service='pushback',size=a[2])
            elif target in (0x1001262c,0x100126b0):
                assert a[0] == 0
                event = dict(service='document_begin' if target == 0x1001262c else 'document_end')
            elif target == 0x1000f164:
                self.publications.append(a[0])
                self.write(a[0]+0x6b,1,1)
                event = dict(service='document_publish',document=a[0])
            else:
                return super().extension(op,args,nxt)
            self.boundaries.append(event)
            self.registers[10] = result
            self.branch_taken = True
            return nxt
        return super().extension(op,args,nxt)

    def after_instruction(self,pc,nxt):
        self.observe(nxt,lambda i:self.registers[i])
        return super().after_instruction(pc,nxt)


def execute(program,engine,*,bitmap=0,copies=1,fill=0,fallback=False,empty=False,
            page_bitmap=None,bih_chunk=False,state_class=Parser,return_state=False):
    if page_bitmap is None:
        page_bitmap = bitmap
    data = stream(bitmap,copies,fallback,empty,page_bitmap,bih_chunk)
    state = state_class(program,fill,data)
    invoke(state,0x10017554,qemu=engine)
    state.put(THREAD,bytes(256))
    state.write(state.read(0x10006a9c,4),4,THREAD)
    state.write(state.read(0x10005d80,4),4,0)
    assert invoke(state,0x1001811c,[state.read(0x100066ac,4),0,1],engine) == 0
    queue = state.read(0x100062d0,4)
    assert invoke(state,0x10017f18,[queue,0,4,BUFFER,256],engine) == 0
    assert invoke(state,0x100135e0,[3,queue],engine) == 0
    state.put(CONTEXT,bytes(512))
    state.write(CONTEXT+12,4,INPUT_CALLBACK)
    state.write(CONTEXT+20,4,PUSHBACK_CALLBACK)
    fixture = SimpleNamespace(path=None,execute_ranges=[])
    if engine is None:
        invoke(state,0x10009d34,[CONTEXT])
        visited = state.visited.copy()
    else:
        runner = start(engine,state,fixture,0x10009d34,HOST)
        engine.set_reg(11,CONTEXT)
        while engine.reg(0) != RETURN:
            pc = engine.reg(0)
            if pc in (0x10009e40,0x10009e43):
                wb = engine.reg(38)
                state.observe(pc,lambda i:engine.reg(((wb*4+i)%32)+1))
            runner.step()
        runner.synchronize(False)
        visited = runner.visited.copy()
    assert state.pos == len(data)
    assert 0x1000a05d in visited
    assert not any(0x10010420 <= pc < 0x10010501 for pc in visited)
    count = state.read(queue+16,4)
    packets = [[state.read(BUFFER+i*16+j*4,4) for j in range(4)] for i in range(count)]
    expected_types = [1,3,5]+([41] if bih_chunk else [])+([] if empty else [9])+[6,2]
    assert [v[0] for v in packets] == expected_types
    # Only defined words are interpreted. Several unused packet suffixes retain
    # stack contents and cannot be assumed to contain zero or stable addresses.
    result = dict(status='pass',bitmap=bitmap,copies=copies,fill=fill,
        fallback_dimensions=fallback,empty_data=empty,page_bitmap=page_bitmap,
        separate_bih_chunk=bih_chunk,input_bytes=len(data),
        input_hex=data.hex(),input_sha256=sha(data),consumed_bytes=state.pos,
        message_types=[v[0] for v in packets],data_allocations=state.data_allocations,
        standalone_helper_entered=False,completed_lifecycles=0)
    if empty:
        assert not bih_chunk and state.data_allocations == [] and 0x1000a0df not in visited
        result.update(outcome='metadata_only_no_raw_message',admission_executed=False,
            pool_blocks=state.blocks(),host_boundaries=state.boundaries)
        assert not return_state, 'handoff requires an admitted data band'
        return result
    raw_packet = packets[4 if bih_chunk else 3]
    work,node = packets[2][3],raw_packet[3]
    payload = state.read(node+12,4)
    pointer = state.read(payload+84,4)
    assert len(state.data_allocations) == (2 if bih_chunk else 1)
    assert state.data_allocations[-1] == dict(size=16,kind=0,pointer=pointer)
    if bih_chunk:
        assert state.data_allocations[0] == dict(size=20,kind=0,pointer=packets[3][3])
        assert state.bytes_at(packets[3][3],20) == BIH
    assert payload == node+16 and raw_packet[1] == 3
    assert state.read(payload+72,4) == len(IMAGE)
    assert state.read(payload+80,4) == (1 if bitmap == 0 else 0)
    assert state.read(payload+30,2) == state.read(payload+88,4) == 32
    assert state.read(payload+32,2) == 4 and state.read(payload+34,2) == 1
    assert state.read(payload+76,2) == 1 and state.read(payload+78,2) == fill*257
    assert state.read(work+116,1) == 0
    assert state.read(work+54,2) == (1 if page_bitmap == 0 else 0)
    assert state.bytes_at(pointer,len(IMAGE)) == IMAGE
    # Document and child initialization are inline parser arms; only the work
    # constructor is a separate call. Do not infer use of the other initializer.
    required = {0x10009efe,0x10009f86,0x1000a0df,0x1000a16d,0x1000f228}
    assert required.issubset(visited),[hex(pc) for pc in required-visited]
    before = state.bytes_at(payload,104)
    for cell,size in [(0x100062e4,8),(0x100062fc,1),(0x10006308,4)]:
        state.put(state.read(cell,4),bytes(size))
    state.write(state.read(0x100062e8,4),2,20)
    table = state.read(0x1000647c,4)
    state.write(table+36*24+4,4,CONTEXT+0x100)
    state.write(table+36*24+8,4,0)
    state.write(CONTEXT+0x100,1,0)
    state.admitting = True
    if engine is None:
        state.visited.clear()
        invoke(state,0x1000e414)
        job_visited = state.visited.copy()
    else:
        runner = start(engine,state,fixture,0x1000e414,HOST)
        while engine.reg(0) not in raw.ADMISSION_STOPS:
            runner.step()
        runner.synchronize(False)
        state.admission_stop = engine.reg(0)
        job_visited = runner.visited.copy()
    state.admitting = False
    docs = state.read(0x100062e4,4)
    doc_node = state.read(docs+4,4)
    doc = state.read(doc_node+12,4)
    child_node = state.read(doc+116,4)
    child = state.read(child_node+12,4)
    assert state.read(docs,4) == doc_node and doc == packets[0][3]
    assert child == packets[1][3] and state.read(child+72,4) == work
    assert state.publications == [doc] and state.ready_calls == 1
    assert state.read(work+80,4) == state.read(work+84,4) == node
    assert state.read(payload+78,2) == state.read(work+78,2) == copies
    assert state.read(work+116,1) == 0 and state.read(payload+84,4) == pointer
    job_bih = state.bytes_at(state.read(0x10006304,4),20)
    assert job_bih == (BIH if bih_chunk else bytes(20))
    blocks = state.blocks()
    if bih_chunk:
        bih_pointer = state.data_allocations[0]['pointer']
        assert {0x1001b38c,0x10013408}.issubset(job_visited)
        assert any(not flags&0x80000000 and base+12 <= bih_pointer
                   and bih_pointer+20 <= base+12+size for base,size,flags in blocks)
    expected_work_bih = BIH[4:16] if bih_chunk and page_bitmap == 1 else bytes(12)
    assert state.bytes_at(work+132,12) == expected_work_bih
    assert state.read(work+144,1) == (BIH[19] if bih_chunk and page_bitmap == 1 else 0)
    after = state.bytes_at(payload,104)
    expected = bytearray(before)
    expected[78:80] = copies.to_bytes(2,'big')
    assert after == expected and state.bytes_at(pointer,len(IMAGE)) == IMAGE
    assert state.read(queue+16,4) == 2
    pending = state.read(queue+32,4)
    assert [state.read(pending+i*16,4) for i in range(2)] == [6,2]
    result.update(outcome='raw_message_admitted',admission_executed=True,
        source_kind=state.read(payload+80,4),message_selector=raw_packet[1],
        node=node,payload=payload,input_pointer=pointer,pointer_delta_from_allocation=0,
        producer_references=fill*257,admitted_references=copies,raw_irq_flag=0,
        payload_before=before.hex(),payload_after=after.hex(),work_bytes=state.bytes_at(work,148).hex(),
        owner_hierarchy=dict(document_node=doc_node,document=doc,child_node=child_node,child=child,work=work),
        owner_hierarchy_origin='original queued document/page/work messages',
        pool_blocks=blocks,host_boundaries=state.boundaries,
        image_sha256=sha(state.bytes_at(pointer,len(IMAGE))),admission_stop=hex(state.admission_stop),
        job_bih_cache=job_bih.hex(),
        bih_source_freed=True if bih_chunk else None,
        work_bih_fields=[state.read(work+i,4) for i in (132,136,140)],
        pending_message_types=[6,2])
    return (state,result) if return_state else result


def main():
    tested_sources = raw.source_hashes()
    prefix = os.environ.get('XTENSA_PREFIX','/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf')
    program = Program(ROOT/'analysis/sihp1020.elf',prefix)
    assert sha(program.path.read_bytes()) == STOCK_SHA
    memory = Machine(program)
    audited = []
    for begin,end in [(0x10009e36,0x10009e45),(0x1000a05d,0x1000a170),
                      (0x1000f228,0x1000f280),(0x1000e6b0,0x1000e749),
                      (0x1000ed90,0x1000ee6c),(0x10013c48,0x10013cc7),
                      (0x10014910,0x10014baf),(0x10016164,0x100162b0)]+video_buffers.AUDIT:
        block,off = memory.span(begin,end-begin,execute=True)
        data = bytes(block[off:off+end-begin])
        pc,decoded = begin,bytearray()
        while pc < end:
            encoded = program.instruction(pc)[2]
            decoded.extend(encoded)
            pc += len(encoded)
        assert pc == end and decoded == data
        audited.append(dict(begin=hex(begin),end=hex(end),bytes=data.hex(),sha256=sha(data)))
    block,off = memory.span(0x100036f0,13*4)
    dispatch = bytes(block[off:off+13*4])
    assert int.from_bytes(dispatch[12*4:13*4],'big') == 0x1000a05d
    parameters = [dict(fill=fill,bitmap=bitmap,copies=copies)
                  for fill in (0,204) for bitmap in (0,1) for copies in (1,2)]
    parameters += [dict(fill=fill,fallback=True) for fill in (0,204)]
    parameters += [dict(fill=fill,empty=True) for fill in (0,204)]
    parameters += [dict(fill=fill,page_bitmap=page_bitmap,bitmap=bitmap,bih_chunk=True)
                   for fill in (0,204) for page_bitmap in (0,1) for bitmap in (0,1)]
    parameters += [dict(fill=fill,page_bitmap=page_bitmap,bitmap=1-page_bitmap)
                   for fill in (0,204) for page_bitmap in (0,1)]
    observations = []
    handoffs = []
    buffer_cases = []
    with QemuRAM() as engine:
        for parameter in parameters:
            expected = execute(program,None,**parameter)
            actual = execute(program,engine,**parameter)
            assert actual == expected,(parameter,actual,expected)
            actual['engines'] = ['bounded_interpreter','independent_qemu']
            observations.append(actual)
            print(f'original chunk-12 parser/admission {parameter}: {actual["outcome"]}',flush=True)
        handoff_parameters = [dict(fill=fill,bitmap=bitmap,copies=copies,
                                   page_bitmap=1,bih_chunk=True)
                              for fill in (0,204) for bitmap in (0,1) for copies in (1,2)]
        handoff_parameters += [dict(fill=fill,bitmap=0,page_bitmap=page_bitmap,
                                    bih_chunk=bool(page_bitmap == 0))
                               for fill in (0,204) for page_bitmap in (0,1)]
        extended = handoff.state_class(Parser)
        for parameter in handoff_parameters:
            results = []
            for target in (None,engine):
                state,admission = execute(program,target,**parameter,
                    state_class=extended,return_state=True)
                results.append(handoff.run(state,target,admission))
            assert results[0] == results[1],(parameter,results)
            result = results[1]
            result['engines'] = ['bounded_interpreter','independent_qemu']
            handoffs.append(result)
            print(f'original chunk-12 handoff {parameter}: {result["outcome"]}',flush=True)
        for size in (131072,16384,65536):
            for fill in (0,204):
                results = []
                for target in (None,engine):
                    state,admission = execute(program,target,fill=fill,bitmap=0,
                        page_bitmap=1,bih_chunk=True,
                        state_class=handoff.state_class(Parser,pool_size=size),return_state=True)
                    before = state.blocks()
                    work,payload = admission['owner_hierarchy']['work'],admission['payload']
                    owners = state.bytes_at(work,148),state.bytes_at(payload,104)
                    result = video_buffers.initialize(state,target,fill,handoff.bounded)
                    if size == 131072:
                        result['release_and_reuse'] = video_buffers.release_and_reuse(state,target,result,before)
                    else:
                        assert result['outcome'] == 'allocation_failed_before_retry'
                    assert owners == (state.bytes_at(work,148),state.bytes_at(payload,104))
                    assert state.bytes_at(admission['input_pointer'],len(IMAGE)) == IMAGE
                    result.update(status='pass',fill=fill,completed_lifecycles=0,
                        parser_owners_and_image_unchanged=True,
                        rejected_before_execution=handoff.reject_excluded(state,target,video_buffers.EXCLUDED))
                    results.append(result)
                assert results[0] == results[1],(size,fill,results)
                result = results[1]
                result['engines'] = ['bounded_interpreter','independent_qemu']
                buffer_cases.append(result)
                print(f'original video buffers pool={size} fill={fill}: {result["outcome"]}',flush=True)
        version = engine.version
    mode_stores = [dict(pc=hex(pc),bytes=encoded.hex(),operands=list(args))
                   for pc,(op,args,encoded) in program.instructions.items()
                   if op == 's8i' and args[2] == 116]
    assert mode_stores == [dict(pc='0x1000f271',bytes='292474',operands=[9,2,116])]
    # The census is intentionally limited to immediate byte stores at base+116.
    # It does not rule out aliases, wider writes, dynamic code or external input.
    assert raw.source_hashes() == tested_sources, 'research sources changed during execution'
    findings = [
        'Twenty-two nonempty chunk-12 inputs run through the full original parser, real allocator/queue and JobMgr admission. Original document/page/work packets construct the owner hierarchy; input callbacks, readiness and document notification/publication remain host boundaries.',
        'Each band data allocation requests exactly 16 bytes with allocator kind 0. The parser stores the returned pointer unchanged in payload+0x54, and admission preserves it. This route does not supply the 16-byte image prefix used in the separate raw-retirement fixtures.',
        'Band bitmap metadata 0 selects source kind 1; value 1 selects source kind 0. Independent page bitmap metadata controls work+0x36. Both source variants send selector 3, append to work+0x50 and receive one or two references from copy metadata. Work raw-IRQ flag +0x74 is zero after construction and admission.',
        'Eight cases deliver a separate chunk-4 BIH through original message 41, original memcpy and actual allocator release. That fills the JobMgr BIH cache, which is distinct from the parser item-0x66 cache. Work dimensions become 32/4/4 only when page bitmap metadata is 1; page bitmap 0 skips that copy even with a populated cache. Four crossed page/band controls without chunk 4 retain zero work dimensions.',
        'Two fills with page bitmap 1, band bitmap 0 and separate BIH delivery combine source kind 1 with populated work dimensions, while still retaining raw-IRQ flag zero and the unadvanced allocation pointer. These explicit mixed-metadata fixtures establish software branch behavior, not supported physical input or a complete raw-output contract.',
        'Payload source size is 16, dimensions are 32 by 4, bpp is 1 and the terminal flag is 1. Two controls omit explicit band width/height: original BIH/cache fallback produces the same dimensions. No physical packing or support for arbitrary metadata is inferred.',
        'Two metadata-only chunk-12 controls allocate no data and emit no message 9. All twenty-four comparisons agree between the bounded interpreter and independent QEMU, including pool partitions, bytes and explicit host boundaries.',
        'The original standalone helper at 0x10010420 is never entered by this parser route. This establishes a separate software producer, not that helper\'s caller, raw-mode reachability, completion, second-copy cursor restoration or physical output.'
    ]
    handoff_findings = [
        'Eight additional serialized continuations retain actual parser-owned allocations through END_PAGE/END_DOC, original queue-1 scheduling, PrintMgr/media selection, original engine message-13-to-14 acknowledgement, queue-8 receipt and the RAM prefix of VideoThread prepare. Copies 1/2 and source kinds 0/1 are crossed with both allocation fills. These are not scheduled native page lifecycles.',
        'All eight reach 0x10014baf before the first video peripheral access. The original prepare computes stride 4 and clears the video IRQ high bit from the still-zero work+0x74. Source kind 1 has selected the alternate-render branch, but that later render call and every peripheral instruction remain excluded.',
        'No original store in these continuations changes work+0x74 or payload+0x54. The image pointer remains the original allocator return, references remain 1/2 and all image bytes remain unchanged. This path does not supply a late 16-byte prefix or establish the raw IRQ family.',
        'Four missing-work-dimension controls reach the call at 0x10014a51 with zero stride. They stop before original division; neither a divide failure nor a hardware fault is executed. Page metadata that suppresses the BIH copy and absent separate BIH delivery remain distinct causes.',
        'The byte-verified whole-decoded-image census finds one immediate S8I at base+116, the work constructor\'s zero store at 0x1000f271. This limited census does not cover aliases, wider stores, dynamic code or external writers.',
        'Original queues, allocator, media matching and acknowledgement execute. Ready/online/media RAM and a 128-KiB pool remain explicit inputs. Original video initialization now allocates both output buffers, clears 260 state bytes, creates its embedded semaphore and registers handlers in RAM before its peripheral boundary. PrintMgr resumes and VideoThread entry still use specified cuts in fresh synthetic contexts; no original task schedule or complete hardware preparation is inferred.',
        'The original video helpers request 39168 and 65536 bytes with allocator kind 2. The first is filled with 0xff, the second retains allocation-fill bytes. All four prepared source slots and four secondary slots fit inside the real allocations; at stride 4 their capacities are 8192 and 16384 bytes per slot, with 6400 unused bytes after the first ring. These output buffers are distinct from the parser source image and do not establish its missing prefix.',
        'Two isolated idle allocation/release/reuse cases preserve parser owners and image bytes. Repeated allocation returns 0 without allocating; original frees clear both globals, repeated empty frees return 0, and later allocation reuses both addresses. Free marks the split blocks reusable without eagerly coalescing the partition. Four smaller-pool controls stop before either original retry sleep, preserving zero or one successful buffer allocation.'
    ]
    limits = ('Synthetic single-thread RAM and seeded allocator/queue state; input callbacks, document begin/end, '
              'document publication and task readiness are explicit boundaries. Nonempty runs stop immediately '
              'after the first raw-list admission, with END_PAGE/END_DOC still queued. The raw IRQ flag is not '
              'forced, and those admission-only cases execute no raw retirement/VideoThread/PrintMgr/engine/custom instruction/MMIO/USB path. '
              'Zero completed page lifecycles or physical printing are claimed. Numeric chunk 12 exists in '
              'this stock ELF; its host header name is not proof of another model\'s support. The open parser grammar is unchanged.')
    handoff_limits = ('The additional continuations are serialized compositions of original routines with explicit '
        'task-entry cuts, supplied ready/media state and synthetic pool capacity. Engine startup message 24 is observed '
        'without executing its hardware handler; only the pure message-13 acknowledgement runs. '
        'No device readiness, mechanical operation, output packing, raw IRQ reachability, retirement, '
        'second-copy cursor restoration, native scheduling or completed page lifecycle is proved. '
        'Thirteen code-boundary controls reject omitted peripheral, render, raw-retirement, retry and custom-code entries '
        'before execution in each engine. The buffer-only controls reject six initialization/retry boundaries. '
        'The constructor prefix does not prove firmware boot, registered-handler behavior or device memory availability.')
    report = dict(status='pass',cases=observations,admission_cases=22,metadata_only_controls=2,
        handoff_cases=handoffs,handoff_prepare_cases=8,handoff_dimension_controls=4,
        video_buffer_cases=buffer_cases,video_buffer_release_cases=2,video_buffer_capacity_controls=4,
        immediate_raw_mode_byte_stores=mode_stores,handoff_findings=handoff_findings,
        handoff_limits=handoff_limits,
        completed_lifecycles=0,stock_elf_sha256=STOCK_SHA,qemu_version=version,
        source_sha256=tested_sources,
        audited_stock_ranges=audited,dispatch_table_bytes=dispatch.hex(),
        dispatch_table_sha256=sha(dispatch),findings=findings,limits=limits)
    OUT.with_suffix('.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    OUT.with_suffix('.md').write_text('# Original chunk-12 parser and raw-list admission\n\n'
        +'22 parser/admission cases and 2 metadata-only controls agree in the interpreter and independent QEMU. Zero completed page lifecycles.\n\n'
        +'\n'.join('- '+finding for finding in findings)+'\n\n'+limits+'\n\n'
        +'## Serialized continuation to preparation (2026-09-28)\n\n'
        +'8 preparation cases and 4 pre-division controls agree between both engines.\n\n'
        +'Original buffer initialization replaces supplied output pointers in those continuations. Two separate idle release/reuse cases and four pre-retry capacity controls also agree.\n\n'
        +'\n'.join('- '+finding for finding in handoff_findings)+'\n\n'+handoff_limits+'\n')
    print('original chunk-12: 22 admissions, 2 non-emitting controls, 8 prepare continuations, 4 dimension controls; video buffers: 2 idle release/reuse, 4 capacity controls; no completed page lifecycles')


if __name__ == '__main__':
    main()
