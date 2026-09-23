#!/usr/bin/env python3
"""Execute original chunk-12 construction and admission without a raw IRQ.

The parser, allocator, queues and owner hierarchy run from stock bytes. Input,
document notification/publication and readiness remain explicit host boundaries.
The JobMgr run stops after admission, before the queued page/document endings.
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


def stream(bitmap,copies,fallback,empty):
    page = [item(k,v) for k,v in [(4,copies),(8,600),(9,600),(12,32),(13,4),
                                 (16,1),(17,32),(18,4),(0x65,bitmap)]]
    band = [item(k,v) for k,v in [(20,4),(0x65,bitmap),(16,1),(0x67,1)]]
    if not fallback:
        band += [item(0x68,32),item(0x69,4)]
    band += [struct.pack('>IHBBI',32,0x66,4,0,20)+BIH]
    return (b'JZJZ'+chunk(0,[item(0,1),item(2,1)])+chunk(2,page)
            +chunk(12,band,b'' if empty else IMAGE)+chunk(3)+chunk(1))


class Parser(raw.RawProducer):
    def __init__(self,program,fill,data):
        super().__init__(program,fill)
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


def execute(program,engine,*,bitmap=0,copies=1,fill=0,fallback=False,empty=False):
    data = stream(bitmap,copies,fallback,empty)
    state = Parser(program,fill,data)
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
    assert [v[0] for v in packets] == ([1,3,5,6,2] if empty else [1,3,5,9,6,2])
    # Only defined words are interpreted. Several unused packet suffixes retain
    # stack contents and cannot be assumed to contain zero or stable addresses.
    result = dict(status='pass',bitmap=bitmap,copies=copies,fill=fill,
        fallback_dimensions=fallback,empty_data=empty,input_bytes=len(data),
        input_hex=data.hex(),input_sha256=sha(data),consumed_bytes=state.pos,
        message_types=[v[0] for v in packets],data_allocations=state.data_allocations,
        standalone_helper_entered=False,completed_lifecycles=0)
    if empty:
        assert state.data_allocations == [] and 0x1000a0df not in visited
        result.update(outcome='metadata_only_no_raw_message',admission_executed=False,
            pool_blocks=state.blocks(),host_boundaries=state.boundaries)
        return result
    work,node = packets[2][3],packets[3][3]
    payload = state.read(node+12,4)
    pointer = state.read(payload+84,4)
    assert state.data_allocations == [dict(size=16,kind=0,pointer=pointer)]
    assert payload == node+16 and packets[3][1] == 3
    assert state.read(payload+72,4) == len(IMAGE)
    assert state.read(payload+80,4) == (1 if bitmap == 0 else 0)
    assert state.read(payload+30,2) == state.read(payload+88,4) == 32
    assert state.read(payload+32,2) == 4 and state.read(payload+34,2) == 1
    assert state.read(payload+76,2) == 1 and state.read(payload+78,2) == fill*257
    assert state.read(work+116,1) == 0
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
        invoke(state,0x1000e414)
    else:
        runner = start(engine,state,fixture,0x1000e414,HOST)
        while engine.reg(0) not in raw.ADMISSION_STOPS:
            runner.step()
        runner.synchronize(False)
        state.admission_stop = engine.reg(0)
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
    after = state.bytes_at(payload,104)
    expected = bytearray(before)
    expected[78:80] = copies.to_bytes(2,'big')
    assert after == expected and state.bytes_at(pointer,len(IMAGE)) == IMAGE
    assert state.read(queue+16,4) == 2
    pending = state.read(queue+32,4)
    assert [state.read(pending+i*16,4) for i in range(2)] == [6,2]
    result.update(outcome='raw_message_admitted',admission_executed=True,
        source_kind=state.read(payload+80,4),message_selector=packets[3][1],
        node=node,payload=payload,input_pointer=pointer,pointer_delta_from_allocation=0,
        producer_references=fill*257,admitted_references=copies,raw_irq_flag=0,
        payload_before=before.hex(),payload_after=after.hex(),work_bytes=state.bytes_at(work,148).hex(),
        owner_hierarchy=dict(document_node=doc_node,document=doc,child_node=child_node,child=child,work=work),
        owner_hierarchy_origin='original queued document/page/work messages',
        pool_blocks=state.blocks(),host_boundaries=state.boundaries,
        image_sha256=sha(state.bytes_at(pointer,len(IMAGE))),admission_stop=hex(state.admission_stop),
        pending_message_types=[6,2])
    return result


def main():
    prefix = os.environ.get('XTENSA_PREFIX','/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf')
    program = Program(ROOT/'analysis/sihp1020.elf',prefix)
    assert sha(program.path.read_bytes()) == STOCK_SHA
    memory = Machine(program)
    audited = []
    for begin,end in [(0x10009e36,0x10009e45),(0x1000a05d,0x1000a170)]:
        block,off = memory.span(begin,end-begin,execute=True)
        data = bytes(block[off:off+end-begin])
        assert sum(len(v[2]) for pc,v in program.instructions.items() if begin <= pc < end) == len(data)
        audited.append(dict(begin=hex(begin),end=hex(end),bytes=data.hex(),sha256=sha(data)))
    block,off = memory.span(0x100036f0,13*4)
    dispatch = bytes(block[off:off+13*4])
    assert int.from_bytes(dispatch[12*4:13*4],'big') == 0x1000a05d
    parameters = [dict(fill=fill,bitmap=bitmap,copies=copies)
                  for fill in (0,204) for bitmap in (0,1) for copies in (1,2)]
    parameters += [dict(fill=fill,fallback=True) for fill in (0,204)]
    parameters += [dict(fill=fill,empty=True) for fill in (0,204)]
    observations = []
    with QemuRAM() as engine:
        for parameter in parameters:
            expected = execute(program,None,**parameter)
            actual = execute(program,engine,**parameter)
            assert actual == expected,(parameter,actual,expected)
            actual['engines'] = ['bounded_interpreter','independent_qemu']
            observations.append(actual)
            print(f'original chunk-12 parser/admission {parameter}: {actual["outcome"]}',flush=True)
        version = engine.version
    sources = {Path(__file__).resolve()}
    for module in list(sys.modules.values()):
        path = getattr(module,'__file__',None)
        if path:
            path = Path(path).resolve()
            if path.is_relative_to(ROOT/'scripts') and path.is_file():
                sources.add(path)
    findings = [
        'Ten nonempty chunk-12 inputs run through the full original parser, real allocator/queue and JobMgr admission. Original document/page/work packets construct the owner hierarchy; input callbacks, readiness and document notification/publication remain host boundaries.',
        'The actual data allocation requests exactly 16 bytes with allocator kind 0. The parser stores the returned pointer unchanged in payload+0x54, and admission preserves it. This route does not supply the 16-byte image prefix used in the separate raw-retirement fixtures.',
        'Explicit bitmap metadata 0 selects source kind 1; bitmap metadata 1 selects source kind 0. Both tested variants send selector 3, append to work+0x50 and receive one or two references from the original copy metadata. Work raw-IRQ flag +0x74 is zero after construction and after admission.',
        'Payload source size is 16, dimensions are 32 by 4, bpp is 1 and the terminal flag is 1. Two controls omit explicit band width/height: original BIH/cache fallback produces the same dimensions. No physical packing or support for arbitrary metadata is inferred.',
        'Two metadata-only chunk-12 controls allocate no data and emit no message 9. All twelve comparisons agree between the bounded interpreter and independent QEMU, including pool partitions, bytes and explicit host boundaries.',
        'The original standalone helper at 0x10010420 is never entered by this parser route. This establishes a separate software producer, not that helper\'s caller, raw-mode reachability, completion, second-copy cursor restoration or physical output.'
    ]
    limits = ('Synthetic single-thread RAM and seeded allocator/queue state; input callbacks, document begin/end, '
              'document publication and task readiness are explicit boundaries. Nonempty runs stop immediately '
              'after the first raw-list admission, with END_PAGE/END_DOC still queued. The raw IRQ flag is not '
              'forced, no raw retirement/VideoThread/PrintMgr/engine/custom instruction/MMIO/USB path executes, '
              'and zero completed page lifecycles or physical printing are claimed. Numeric chunk 12 exists in '
              'this stock ELF; its host header name is not proof of another model\'s support. The open parser grammar is unchanged.')
    report = dict(status='pass',cases=observations,admission_cases=10,metadata_only_controls=2,
        completed_lifecycles=0,stock_elf_sha256=STOCK_SHA,qemu_version=version,
        source_sha256={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sorted(sources)},
        audited_stock_ranges=audited,dispatch_table_bytes=dispatch.hex(),
        dispatch_table_sha256=sha(dispatch),findings=findings,limits=limits)
    OUT.with_suffix('.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    OUT.with_suffix('.md').write_text('# Original chunk-12 parser and raw-list admission\n\n'
        +'10 parser/admission cases and 2 metadata-only controls agree in the interpreter and independent QEMU. Zero completed page lifecycles.\n\n'
        +'\n'.join('- '+finding for finding in findings)+'\n\n'+limits+'\n')
    print('original chunk-12: 10 admission cases, 2 non-emitting controls; no completed page lifecycles')


if __name__ == '__main__':
    main()
