#!/usr/bin/env python3
"""Original raw producer, real queue and bounded JobMgr admission in offline RAM.

The raw helper's caller and image prefix remain supplied preconditions. These
serialized calls do not start a printer task, render a page or perform DMA.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace

from hp1020_xtensa_call0 import Program, Machine, STOP
from hp1020_stock_pool import PoolRAM
from hp1020_stock_queue import BUFFER, SOURCE, THREAD
from hp1020_stock_notifications import invoke
from hp1020_qemu_pipeline import start
from hp1020_qemu_ram import QemuRAM
from hp1020_qemu_stock_parser import VECTORS

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'analysis/hardware-boundary/raw-producer'
META, DESC = SOURCE, SOURCE+64
DOC_NODE, DOC = SOURCE+128, SOURCE+160
CHILD_NODE, CHILD, WORK = SOURCE+320, SOURCE+352, SOURCE+480
PRODUCER = [(0x10010420,0x100104c6),(0x100104c8,0x10010501),
            (0x1000f204,0x1000f228),(0x1001b4c8,0x1001b542)]
ADMISSION = [(0x1000e414,0x1000e42e),(0x1000e44f,0x1000e464),
             (0x1000e5a0,0x1000e67f),(0x10013000,0x10013050)]
ADMISSION_STOPS = {0x1000e670,0x1000e67c}
EVENT = [(0x10017554,0x100175c0),(0x10017ca0,0x10017cf0),
         (0x10017dac,0x10017dd8),(0x1001896c,0x10019138),
         (0x10019308,0x10019350)]
CLEANUP = [(0x1000f0a8,0x1000f128),(0x10013050,0x1001307c)]
READY = 0x1001214c
PREFIX = b'RAW-PREFIX-TEST!'
BAND = bytes((i*37+11)&255 for i in range(4800))
BIH = bytes(range(20))
WRAPPER = '''
.text
.align 4
.global retire
retire:
 entry a1,48
 mov a10,a2
 movi a8,0x1001451c
 jx a8
'''


def sha(data):
    return hashlib.sha256(data).hexdigest()


class RawProducer(PoolRAM):
    def __init__(self,program,fill):
        super().__init__(program,size=16384,fill=fill)
        self.code_ranges += PRODUCER+ADMISSION+EVENT+CLEANUP+VECTORS+[
            (0x1001b770,0x1001b788),(0x1001451c,0x1001455a)]
        self.admitting = False
        self.ready_calls = 0

    def extension(self,op,args,nxt):
        if op == 'rsr.ps':
            # Match the inherited interpreter's abstract mask state. QEMU
            # independently executes the original CPU control instructions.
            self.registers[args[0]] = self.ps
            return nxt
        if op == 'call8' and args == (READY,):
            assert self.admitting
            self.ready_calls += 1
            self.registers[10] = 0
            self.branch_taken = True
            return nxt
        return super().extension(op,args,nxt)

    def after_instruction(self,pc,nxt):
        if self.admitting and nxt in ADMISSION_STOPS:
            self.admission_stop = nxt
            return STOP
        return super().after_instruction(pc,nxt)


def setup(program,engine,fill):
    state = RawProducer(program,fill)
    # Known ordinary caller and one explicitly seeded pool; no boot discovery.
    invoke(state,0x10017554,qemu=engine)
    state.put(THREAD,bytes(256))
    state.write(state.read(0x10006a9c,4),4,THREAD)
    state.write(state.read(0x10005d80,4),4,0)
    assert invoke(state,0x1001811c,[state.read(0x100066ac,4),0,1],engine) == 0
    event = state.read(0x100062dc,4)
    assert invoke(state,0x10017ca0,[event,0],engine) == 0
    queue = state.read(0x100062d0,4)
    assert invoke(state,0x10017f18,[queue,0,4,BUFFER,64],engine) == 0
    assert invoke(state,0x100135e0,[3,queue],engine) == 0
    state.queue = queue
    state.buffer = invoke(state,0x10013140,[len(PREFIX)+len(BAND),2],engine)
    assert state.buffer and state.buffer%16 == 0 and len(PREFIX) == 16
    state.put(state.buffer,PREFIX+BAND)
    state.blocks()
    return state


def produce_and_admit(program,engine,*,fill=0,input_kind=1,selector=0,
                      terminal=1,copies=1,duplex=0,source=0,active=0,
                      skip_bih=1,raw_flag=1):
    state = setup(program,engine,fill)
    state.put(META,bytes(40))
    state.write(META,4,6)
    for offset,value in ((6,1),(10,256),(14,3),(26,600),(30,600),(34,7)):
        state.write(META+offset,2,value)
    state.write(META+16,4,9600)
    state.write(META+20,4,4)
    state.put(DESC,bytes(24))
    for offset,value in ((0,state.buffer+16),(4,input_kind),(8,terminal),(12,selector)):
        state.write(DESC+offset,4,value)
    state.write(DESC+18,2,4)
    inputs = state.bytes_at(META,40),state.bytes_at(DESC,24)
    invoke(state,0x10010420,[META,DESC],engine)
    assert state.read(state.queue+16,4) == 1
    words = [state.read(BUFFER+i*4,4) for i in range(4)]
    node,payload = words[3],words[3]+16
    assert words[0] == 9 and words[1] == (3,0,1,2)[selector]
    # Message word 2 and list linkage padding are not initialized by the
    # producer and not consumed by the selected JobMgr case. Do not infer zero.
    assert state.read(node,4) == 0 and state.read(node+12,4) == payload
    expected = bytearray([fill])*104
    expected[:70] = bytes(70)
    def put(offset,size,value):
        expected[offset:offset+size] = value.to_bytes(size,'big')
    put(12,2,1);put(14,2,3)
    for dst,src in ((12,34),(10,10),(16,6),(34,18),(30,22),(20,26),(22,30),(14,14)):
        put(dst,2,state.read(META+src,2))
    put(0,4,6)
    kind = 1 if input_kind == 1 else 2
    pointer = state.buffer+16 if kind == 1 else 0
    for offset,value in ((80,kind),(84,pointer),(88,4),(72,4800)):
        put(offset,4,value)
    put(32,2,4);put(76,2,int(terminal == 1))
    assert state.bytes_at(payload,104) == expected
    initial_refs = state.read(payload+78,2)
    assert initial_refs == fill*257
    assert inputs == (state.bytes_at(META,40),state.bytes_at(DESC,24))
    # Explicit owner hierarchy. Its creation, caller/root and scheduling are
    # not supplied by this raw helper and are not claimed by this experiment.
    state.put(DOC_NODE,bytes(352+148))
    docs = state.read(0x100062e4,4)
    state.write(docs,4,DOC_NODE);state.write(docs+4,4,DOC_NODE)
    state.write(DOC_NODE+12,4,DOC)
    state.write(DOC+116,4,CHILD_NODE)
    state.write(DOC+96,4,source)
    state.write(CHILD_NODE+12,4,CHILD)
    state.write(CHILD+72,4,WORK)
    state.write(WORK+12,2,copies)
    state.write(WORK+114,2,active)
    state.write(WORK+117,1,duplex)
    state.write(WORK+54,2,skip_bih)
    state.write(WORK+116,1,raw_flag)
    state.write(state.read(0x100062fc,4),1,0)
    state.put(state.read(0x10006304,4),BIH)
    state.admitting = True
    if engine is None:
        invoke(state,0x1000e414)
    else:
        runner = start(engine,state,SimpleNamespace(path=None,execute_ranges=[]),0x1000e414,{READY})
        while engine.reg(0) not in ADMISSION_STOPS:
            runner.step()
        runner.synchronize(False)
        state.admission_stop = engine.reg(0)
        assert runner.services == [READY]
    state.admitting = False
    effective_copies = copies or 1
    refs = (effective_copies*2)&65535 if duplex == 1 and source != 1 else effective_copies
    if active == 1: refs = 1
    assert state.ready_calls == 1
    assert state.read(state.queue+16,4) == 0
    assert state.read(WORK+12,2) == effective_copies
    assert state.read(payload+78,2) == state.read(WORK+78,2) == refs
    appended = selector == 0
    assert state.read(WORK+80,4) == state.read(WORK+84,4) == (node if appended else 0)
    assert state.read(WORK+116,1) == raw_flag
    assert state.read(payload+84,4) == pointer
    expected[78:80] = refs.to_bytes(2,'big')
    assert state.bytes_at(payload,104) == expected
    assert state.bytes_at(WORK+132,12) == (BIH[4:16] if appended and not skip_bih else bytes(12))
    assert state.read(WORK+144,1) == (BIH[19] if appended and not skip_bih else 0)
    assert inputs == (state.bytes_at(META,40),state.bytes_at(DESC,24))
    assert state.bytes_at(state.buffer,4816) == PREFIX+BAND
    assert len([b for b in state.blocks() if b[2]&0x80000000]) == 2
    observation = dict(status='pass',input_kind=input_kind,source_kind=kind,selector=selector,
        message_type=words[0],message_selector=words[1],terminal=terminal,fill=fill,
        source_pointer=pointer,buffer=state.buffer,node=node,payload_sha256=sha(bytes(expected)),
        producer_reference_bytes=initial_refs,copies=copies,duplex=duplex,document_source=source,
        active=active,result_references=refs,appended=appended,skip_bih=skip_bih,raw_flag=raw_flag,
        admission_stop=hex(state.admission_stop),pool_blocks=state.blocks(),
        image_and_inputs_unchanged=True,allocator_and_queue_executed=True,
        caller_and_owner_hierarchy='explicit fixture',task_ready='host boundary')
    return state,observation


def differential(program,engine,**parameters):
    _,expected = produce_and_admit(program,None,**parameters)
    _,observed = produce_and_admit(program,engine,**parameters)
    assert observed == expected,(parameters,observed,expected)
    observed['engines'] = ['bounded_interpreter','independent_qemu']
    return observed


def release_once(program,engine,fixture,fill,input_kind,copies):
    state,admission = produce_and_admit(program,engine,fill=fill,input_kind=input_kind,copies=copies)
    node = admission['node'];payload = node+16
    video = state.read(0x10006770,4)
    state.put(video,bytes(256))
    state.write(video+252,4,0x80000000)
    state.write(video+160,4,node)
    state.segments += fixture.segments
    runner = start(engine,state,fixture,fixture.symbols['retire'],())
    engine.set_reg(11,video)
    while engine.reg(0) != 0x1001455a:
        runner.step()
    runner.synchronize(False)
    assert not runner.services
    excluded = []
    for pc in (0x1001455a,0x10014560,0x100144d9,0x10014126,0x10014910,0x10015648):
        engine.set_reg(0,pc)
        before_steps = runner.steps
        try:
            runner.step()
        except ValueError as error:
            assert str(error) == f'native tasks left selected code: {pc:#x}'
        else:
            raise AssertionError(f'excluded hardware path executed: {pc:#x}')
        assert runner.steps == before_steps and engine.reg(0) == pc
        excluded.append(hex(pc))
    assert state.read(payload+78,2) == copies-1
    assert state.read(payload+84,4) == (state.buffer if input_kind == 1 else 0)
    assert state.read(video+160,4) == 0
    assert state.read(state.read(0x100062dc,4)+8,4) == 8
    before = state.bytes_at(state.buffer,4816)
    result = invoke(state,0x1000f0a8,[WORK+80,0],engine)
    assert result == int(copies == 1)
    live = [b for b in state.blocks() if b[2]&0x80000000]
    assert len(live) == (2 if copies > 1 else 0 if input_kind == 1 else 1)
    assert state.read(WORK+80,4) == (node if copies > 1 else 0)
    assert state.bytes_at(state.buffer,4816) == before == PREFIX+BAND
    return dict(status='pass',fill=fill,input_kind=input_kind,initial_references=copies,
        remaining_references=copies-1,remaining_allocations=len(live),cleanup_result=result,
        supplied_image_prefix_bytes=16,raw_refresh_stop='0x1001455a',
        allocator_executed=True,queue_executed=True,completed_lifecycles=0,
        rejected_before_execution=excluded,
        scope='One supplied raw completion after serialized producer/admission; no second submission or hardware prefix.')


def main():
    prefix = os.environ.get('XTENSA_PREFIX','/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf')
    program = Program(ROOT/'analysis/sihp1020.elf',prefix)
    assert sha(program.path.read_bytes()) == '2111560068db47ceca21fa550db4c7c34f5595b5a5d137ae4a19631e40e3601d'
    audited = []
    memory = Machine(program)
    for begin,end in PRODUCER+ADMISSION:
        block,offset = memory.span(begin,end-begin,execute=True)
        raw = bytes(block[offset:offset+end-begin])
        pcs = [pc for pc in program.instructions if begin <= pc < end]
        instruction_bytes = sum(len(program.instructions[pc][2]) for pc in pcs)
        # The original memset has three alignment bytes between annotated
        # instruction regions. Program's instruction gate excludes those PCs.
        assert end-begin-instruction_bytes == (3 if begin == 0x1001b4c8 else 0)
        audited.append(dict(begin=hex(begin),end=hex(end),bytes=raw.hex(),sha256=sha(raw),
                            instruction_bytes=instruction_bytes,excluded_padding_bytes=end-begin-instruction_bytes))
    with tempfile.TemporaryDirectory(prefix='hp1020-raw-producer-') as directory:
        folder = Path(directory)
        (folder/'retire.S').write_text(WRAPPER)
        subprocess.run([prefix+'-as','--text-section-literals',str(folder/'retire.S'),'-o',str(folder/'retire.o')],check=True)
        subprocess.run([prefix+'-ld','-Ttext=0x20000000','-e','retire',str(folder/'retire.o'),'-o',str(folder/'retire.elf')],check=True)
        fixture = Program(folder/'retire.elf',prefix)
        fixture_bytes = fixture.path.read_bytes()
        with QemuRAM() as engine:
            builders = [differential(program,engine,fill=fill,input_kind=kind,selector=selector,
                                     terminal=selector%2)
                        for fill in (0,204) for kind in (0,1,2,0xffffffff) for selector in range(4)]
            print(f'raw producer: {len(builders)} original producer/queue/admission cases passed',flush=True)
            reference_inputs = [(0,0,0,0),(3,0,0,0),(3,1,0,0),(3,1,1,0),
                                (3,1,0,1),(0,1,0,1),(32768,1,0,0),(65535,1,0,0)]
            references = [differential(program,engine,fill=fill,copies=copies,duplex=duplex,
                                       source=source,active=active)
                          for fill in (0,204) for copies,duplex,source,active in reference_inputs]
            flags = [differential(program,engine,fill=fill,skip_bih=0,raw_flag=raw_flag)
                     for fill in (0,204) for raw_flag in (0,1)]
            releases = [release_once(program,engine,fixture,fill,kind,copies)
                        for fill in (0,204) for kind in (1,2) for copies in (1,2)]
            version = engine.version
    sources = {Path(__file__)}
    # Include every loaded repository module used by this experiment.
    import sys
    for module in list(sys.modules.values()):
        path = getattr(module,'__file__',None)
        if path:
            path = Path(path).resolve()
            if path.is_relative_to(ROOT/'scripts') and path.is_file(): sources.add(path)
    findings = [
        'The full original helper allocates its 120-byte node through the stock pool, initializes its embedded payload and sends message 9 through the original queue. The queue is then consumed by original JobMgr admission. The caller, owner hierarchy and ordinary ready state are explicit fixtures.',
        'Descriptor selector 0 maps to message selector 3 and appends the node. Descriptor selectors 1/2/3 map to 0/1/2; JobMgr still assigns references but does not append them to the tested raw list. No physical color or channel interpretation is assigned.',
        'The producer leaves the reference field outside its 70-byte reset. Original JobMgr overwrites it from the work copy count, normalizes zero copies to one, conditionally doubles it and overrides it to one for active work. This resolves reference initialization for the supplied admission path.',
        'Doubling is stored in 16 bits: explicit unsupported large-copy fixtures 32768 and 65535 yield zero and 65534 references. These are arithmetic boundary observations, not observed printer faults or supported copy counts.',
        'Raw IRQ mode is unchanged by this producer/admission sequence. When the supplied work allows BIH copying, admission copies the selected BIH fields; source kind 1/2 alone does not supply appropriate raw work metadata.',
        'With an explicitly allocated 16-byte input prefix and one reference, one supplied raw completion followed by original cleanup frees the kind-1 input allocation and node. Kind 2 frees only the node; the separately allocated unused input remains owned by the fixture.',
        'With two references, one supplied completion retains both allocations and the node, but changes a nonzero image pointer to the input allocation base. The next submission/cursor restoration is not established. The actual producer root and input-prefix origin remain unproven.'
    ]
    limits = ('Serialized RAM execution with explicit caller, owner hierarchy, copy/mode metadata and a 16-byte input prefix. '
              'Task readiness is supplied; the real queue and allocator execute without waiters. Raw completion enters after '
              'the omitted peripheral prefix and stops before refresh. No complete page lifecycle, second-copy submission, '
              'boot, MMIO, custom instruction, USB contact, physical packing or printing is claimed.')
    report = dict(status='pass',producer_admission_cases=builders,reference_cases=references,
        metadata_controls=flags,release_cases=releases,completed_lifecycles=0,
        source_sha256={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sorted(sources)},
        stock_elf_sha256=sha(program.path.read_bytes()),qemu_version=version,
        fixture_source=WRAPPER,fixture_source_sha256=sha(WRAPPER.encode()),
        fixture_elf_sha256=sha(fixture_bytes),fixture_elf_bytes=fixture_bytes.hex(),
        input_band_sha256=sha(BAND),audited_stock_ranges=audited,findings=findings,limits=limits)
    OUT.with_suffix('.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    OUT.with_suffix('.md').write_text('# Original raw producer and admission\n\n'
        +f'{len(builders)} producer/queue/admission, {len(references)} reference and {len(flags)} metadata cases agree between the bounded interpreter and independent QEMU. '
        +f'{len(releases)} further QEMU cases execute one supplied completion and actual allocator cleanup. Zero complete page lifecycles.\n\n'
        +'\n'.join('- '+finding for finding in findings)+'\n\n'+limits+'\n')
    print(f'raw producer: {len(builders)+len(references)+len(flags)} differential cases, {len(releases)} conditional release cases; no page lifecycles')


if __name__ == '__main__':
    main()
