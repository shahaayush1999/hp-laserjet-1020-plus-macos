"""Serialized original raw-page handoff, stopping before peripheral access.

Parser ownership is retained. Original queues, pool, PrintMgr/media selection,
engine message-13 acknowledgement and VideoThread preparation execute in RAM.
The original constructor prefix creates the output buffers and idle video state.
Task starts/resumes, ready/media values and pool capacity remain explicit fixtures.
Neither RTOS scheduling nor a complete prepare/render call is claimed.
"""
import hashlib
from types import SimpleNamespace

from hp1020_xtensa_call0 import STOP
from hp1020_stock_notifications import invoke
from hp1020_stock_printmgr_harness import CODE as PRINT_CODE
from hp1020_stock_queue import BUFFER
from hp1020_qemu_pipeline import start
from hp1020_qemu_ram import RETURN
import hp1020_video_buffers as video_buffers

READY = 0x1001214c
PREPARE_END = 0x10014baf
DIVIDE_CALL = 0x10014a51
EXTRA_CODE = PRINT_CODE+[
    (0x1000f84c,0x1000fcb0),(0x1000fea4,0x100100a8),
    (0x100100fc,0x10010158),(0x10010298,0x10010306),
    (0x10016164,0x100162b0),(0x10013c18,0x10013c1b),
    (0x10013c48,0x10013cc7),(0x10014910,PREPARE_END),
    (0x10011178,0x100111b4),(0x100171b0,0x100171d7),
    (0x1001b668,0x1001b6b0)]
EXCLUDED = (0x10013c33,PREPARE_END,0x10014bb8,0x10014bc3,
            0x1001451c,0x10015438,0x10015648,*video_buffers.EXCLUDED)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def state_class(parser_class,pool_size=131072):
    class Handoff(parser_class):
        def __init__(self,*args):
            super().__init__(*args,pool_size=pool_size)
            self.handoff_active = False
            self.handoff_stop = None
            self.handoff_cut = None
            self.handoff_writes = []
            self.handoff_watch = {}
            self.handoff_phase = ''
            self.intenable = 0

        def extension(self,op,args,nxt):
            if self.handoff_active and op == 'call8' and args == (READY,):
                self.registers[10] = 0
                self.branch_taken = True
                return nxt
            if op == 'rsr.intenable':
                self.registers[args[0]] = self.intenable
                return nxt
            if op == 'wsr.intenable':
                self.intenable = self.registers[args[0]]
                return nxt
            return super().extension(op,args,nxt)

        def observe_store(self,pc,reg):
            op,args,_ = self.program.instruction(pc)
            sizes = {'s8i':1,'s16i':2,'s32i':4,'s32i.n':4,'s32e':4}
            if op not in sizes:
                return
            size = sizes[op]
            address = (reg(args[1])+args[2])&0xffffffff
            for name,(begin,length) in self.handoff_watch.items():
                if address < begin+length and begin < address+size:
                    self.handoff_writes.append(dict(phase=self.handoff_phase,pc=hex(pc),
                        field=name,address=address,size=size,
                        value=reg(args[0])&((1<<(size*8))-1)))

        def after_instruction(self,pc,nxt):
            nxt = super().after_instruction(pc,nxt)
            if not self.handoff_active:
                return nxt
            self.observe_store(pc,lambda i:self.registers[i])
            if self.handoff_cut and pc == self.handoff_cut[0]:
                _,nxt,registers = self.handoff_cut
                for i,value in registers.items():
                    self.registers[i] = value
            if self.handoff_stop and self.handoff_stop(nxt,self.read,lambda i:self.registers[i]):
                self.handoff_stopped_at = nxt
                return STOP
            return nxt
    return Handoff


def bounded(state,engine,entry,phase,stop,cut=None):
    state.handoff_phase = phase
    state.handoff_stop = stop if engine is None else None
    state.handoff_cut = cut if engine is None else None
    state.visited.clear()
    if engine is None:
        invoke(state,entry)
        stopped = state.handoff_stopped_at
        visited = state.visited.copy()
    else:
        runner = start(engine,state,SimpleNamespace(path=None,execute_ranges=[]),entry,{READY})
        def reg(i):
            return engine.reg(((engine.reg(38)*4+i)%32)+1)
        def read(address,size):
            return int.from_bytes(engine.read(address,size),'big')
        cut_pending = cut is not None
        while True:
            pc = engine.reg(0)
            if cut_pending and pc == cut[0]+3:
                assert cut[0] in runner.visited
                for i,value in cut[2].items():
                    engine.set_reg(((engine.reg(38)*4+i)%32)+1,value)
                engine.set_reg(0,cut[1])
                pc = cut[1]
                cut_pending = False
            if stop(pc,read,reg):
                break
            if pc != RETURN-3 and pc not in runner.host:
                state.observe_store(pc,reg)
            runner.step()
        runner.synchronize(False)
        stopped,visited = engine.reg(0),runner.visited.copy()
    state.handoff_stop = state.handoff_cut = None
    return stopped,visited


def snapshot(state,admission,phase):
    work,payload = admission['owner_hierarchy']['work'],admission['payload']
    return dict(phase=phase,work_sha256=sha(state.bytes_at(work,148)),
        payload_sha256=sha(state.bytes_at(payload,104)),
        input_pointer=state.read(payload+84,4),raw_irq_flag=state.read(work+116,1),
        source_kind=state.read(payload+80,4),references=state.read(payload+78,2),
        scheduled_copies=state.read(work+72,2),
        work_bih_fields=[state.read(work+i,4) for i in (132,136,140)])


def run(state,engine,admission):
    """Continue an actual admitted parser allocation; never manufacture a work."""
    state.handoff_active = True
    state.code_ranges = [r for r in state.code_ranges if r != (0x1001451c,0x1001455a)]
    state.code_ranges += EXTRA_CODE
    work,payload = admission['owner_hierarchy']['work'],admission['payload']
    state.handoff_watch = dict(image_cursor=(payload+84,4),work_raw_mode=(work+116,1))
    stages = [snapshot(state,admission,'admission')]
    queues = {}
    # Separate original queue objects, all with private bounded storage.
    for number,cell,buf in ((0,0x1000699c,BUFFER+0x200),
                            (1,0x1000632c,BUFFER+0x400),
                            (8,0x1000676c,BUFFER+0x600)):
        queue = state.read(cell,4)
        assert invoke(state,0x10017f18,[queue,0,4,buf,256],engine) == 0
        assert invoke(state,0x100135e0,[number,queue],engine) == 0
        queues[number] = queue
    job_queue = state.read(0x100062d0,4)
    stop,visited = bounded(state,engine,0x1000e414,'job_endings',
        lambda pc,read,reg:pc == 0x1000e41d and read(job_queue+16,4) == 0)
    assert stop == 0x1000e41d and {0x1000e6b0,0x1000e70d,0x1000ed90}.issubset(visited)
    assert state.read(queues[1]+16,4) == admission['copies']
    assert state.read(work+72,2) == admission['copies']
    stages.append(snapshot(state,admission,'job_endings'))

    # Explicit idle/ready and matching one-tray media fixture. These are RAM
    # inputs, not engine observations, boot defaults or a media sensor model.
    for cell,size in ((0x10006338,20),(0x10006340,40),(0x10006344,20),
                      (0x10006324,8),(0x10006328,8)):
        state.put(state.read(cell,4),bytes(size))
    for key in (1,24):
        state.write(state.read(0x10006490,4)+key*4,4,0)
    for key in (1,24,29):
        assert invoke(state,0x1001811c,[state.read(0x10006464,4)+key*28,0,1],engine) == 0
    table = state.read(0x1000647c,4)
    rec = table+24
    assert state.read(rec+4,4) == 0 and state.read(rec+16,2) == 16
    media_options = invoke(state,0x100131b8,[16,1],engine)
    state.put(media_options,bytes(16))
    state.write(rec+4,4,media_options)
    media = state.read(table+29*24+4,4)
    assert state.read(table+29*24+16,2) == 168
    state.put(media,bytes(168))
    for offset in (0x34,0x38,0x3c,0x40):
        state.write(media+offset,4,1)
    pm = state.read(0x10006338,4)
    for offset in (0,1,2):
        state.write(pm+offset,1,1)
    stop,visited = bounded(state,engine,0x1000f324,'printmgr_request',
        lambda pc,read,reg:pc == 0x1000f358 and read(queues[1]+16,4) == 0)
    assert {0x1001135c,0x10010298,0x1000f84c,0x100100fc,0x10010128}.issubset(visited)
    stages.append(snapshot(state,admission,'printmgr_request'))
    packets = []
    while state.read(queues[0]+16,4):
        pointer = BUFFER+0x100
        assert invoke(state,0x1001809c,[queues[0],pointer,0],engine) == 0
        words = [state.read(pointer+i*4,4) for i in range(4)]
        # Startup message 24 is observed only; its hardware handler is excluded.
        if words[0] == 24:
            packets.append(dict(queue=0,type=24))
            continue
        assert words == [13,0,0,work]
        packets.append(dict(queue=0,words=words))
        state.visited.clear()
        invoke(state,0x10016164,[pointer],engine)
        assert [state.read(pointer+i*4,4) for i in range(4)] == [14,0,0,work]
    assert [p.get('type',p.get('words',[None])[0]) for p in packets] == [24,13]
    assert state.read(queues[1]+16,4) == 1
    # A fresh synthetic task context enters the original receive-loop prefix;
    # subscription/startup code has already executed. This is not an RTOS resume.
    stop,visited = bounded(state,engine,0x1000f324,'printmgr_acknowledgement',
        lambda pc,read,reg:pc == 0x1000f358 and read(queues[1]+16,4) == 0,
        cut=(0x1000f324,0x1000f353,{7:0}))
    assert 0x1000f44c in visited and state.read(queues[8]+16,4) == 1
    at = state.read(queues[8]+32,4)
    assert [state.read(at+i*4,4) for i in range(4)] == [11,0,0,work]
    stages.append(snapshot(state,admission,'video_queued'))

    # The complete original constructor prefix owns output-buffer allocation,
    # clearing idle state, semaphore creation and IRQ-table RAM registration.
    # Its peripheral tail remains excluded; no registered handler is executed.
    initialization = video_buffers.initialize(state,engine,admission['fill'],bounded)
    assert initialization['outcome'] == 'initialized_before_peripherals'
    video = state.read(0x10006770,4)
    state.handoff_watch['video_irq_mode'] = (video+252,4)
    stop,visited = bounded(state,engine,0x10013c18,'video_prepare',
        lambda pc,read,reg:pc == PREPARE_END or pc == DIVIDE_CALL and reg(11) == 0,
        cut=(0x10013c18,0x10013c48,{4:11,5:0}))
    branch = 0x10013cad if admission['source_kind'] == 1 else 0x10013c97
    assert {branch,0x10014910,0x10014a3b}.issubset(visited)
    assert state.read(video+96,4) == work
    assert state.read(queues[8]+16,4) == 0
    dimensions_present = admission['work_bih_fields'] == [32,4,4]
    assert (stop == PREPARE_END) == dimensions_present
    assert state.read(video+184,4) == (4 if dimensions_present else 0)
    if dimensions_present:
        assert 0x10014bac in visited and state.read(video+252,4)&0x80000000 == 0
        layout = video_buffers.prepared_layout(state,initialization)
    else:
        assert 0x1001b668 not in visited
        layout = None
    stages.append(snapshot(state,admission,'prepare_boundary'))
    assert all(s['input_pointer'] == admission['input_pointer'] and s['raw_irq_flag'] == 0
               and s['source_kind'] == admission['source_kind']
               and s['references'] == admission['copies'] for s in stages)
    assert not any(w['field'] in ('image_cursor','work_raw_mode') for w in state.handoff_writes)
    assert state.bytes_at(admission['input_pointer'],16) == bytes(range(16))
    rejected = reject_excluded(state,engine,EXCLUDED)
    return dict(status='pass',bitmap=admission['bitmap'],page_bitmap=admission['page_bitmap'],
        copies=admission['copies'],fill=admission['fill'],
        separate_bih_chunk=admission['separate_bih_chunk'],stages=stages,
        outcome='pre_peripheral_prepare' if dimensions_present else 'zero_stride_predivision_stop',
        prepare_stop=hex(stop),prepare_stride=state.read(video+184,4),
        video_mode_word=state.read(video+252,4),tracked_stores=state.handoff_writes,
        engine_packets=packets,pool_blocks=state.blocks(),image_unchanged=True,
        video_initialization=initialization,output_layout=layout,
        rejected_before_execution=rejected,completed_lifecycles=0,
        task_context='serialized entry and explicit receive-loop cuts; no native scheduler',
        supplied_state='ready/online/media RAM and 128-KiB pool; original video initialization prefix; no device feedback')


def reject_excluded(state,engine,pcs):
    rejected = []
    for pc in pcs:
        op,args,encoded = state.program.instruction(pc)
        try:
            state.span(pc,len(encoded),execute=True)
        except ValueError as error:
            assert 'execution outside selected stock routines' in str(error)
        else:
            raise AssertionError(f'excluded code remains executable: {pc:#x}')
        if engine is not None:
            engine.set_reg(0,pc)
            runner = start_exclusion_runner(engine,state)
            try:
                runner.step()
            except ValueError as error:
                assert str(error) == f'native tasks left selected code: {pc:#x}'
            else:
                raise AssertionError('QEMU executed an excluded boundary')
            assert runner.steps == 0 and engine.reg(0) == pc
        rejected.append(hex(pc))
    return rejected


def start_exclusion_runner(engine,state):
    from hp1020_qemu_multitask import NativeTasks
    return NativeTasks(engine,state,SimpleNamespace(execute_ranges=[]),state.code_ranges)
