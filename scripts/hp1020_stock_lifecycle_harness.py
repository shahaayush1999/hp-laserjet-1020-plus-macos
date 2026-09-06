"""Serialized stock job lifecycle with explicitly injected completion events.

Hardware does not run. The fixture retires compressed nodes through the pure
RAM block inside the stock channel-A handler, then injects JobMgr message 17.
That assumes successful ordered consumption; it cannot establish IRQ timing,
DMA correctness, printing or recovery. Original scheduling, release, datastore
bookkeeping and document-finalization instructions execute against host RAM.
"""
from hp1020_stock_jobmgr_harness import JobMgrHarness
from hp1020_stock_parser_harness import ParserHarness, CONTEXT
from hp1020_xtensa_stock import StockMachine
from hp1020_xtensa_call0 import STOP, STACK, STACK_SIZE

LIFECYCLE_CODE=[(0x1000f0a8,0x1000f1c4),(0x10010f54,0x10011178),
                (0x10013050,0x1001307c),(0x1001262c,0x10012642),(0x100126b0,0x100126c4)]

class RetireBlock(StockMachine):
    def __init__(self,owner,nodes,band_done=1):
        super().__init__(owner.program,0x10014319,[(0x10014319,0x10014342)])
        self.segments=owner.segments;self.write_ranges=owner.write_ranges
        self.events=[]
        video=self.read(0x10006770,4)
        self.write(video+0xf8,4,band_done)
        for i in range(5):self.write(video+0xa4+i*4,4,nodes[i] if i<len(nodes) else 0)
        self.registers[3]=video;self.registers[5]=0;self.registers[6]=0;self.registers[7]=video+0xa4
    def extension(self,op,args,nxt):
        if op=='call8' and args[0]==0x10017dac:
            values=self.registers[10:13]
            if values!=[self.read(0x100062dc,4),8,0]:raise ValueError('unexpected retirement event')
            self.events.append(values.copy());self.registers[10]=0;self.branch_taken=True;return nxt
        return super().extension(op,args,nxt)
    def after_instruction(self,pc,nxt):
        return STOP if nxt==0x10014342 else super().after_instruction(pc,nxt)


class LifecycleHarness(JobMgrHarness):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.code_ranges=self.code_ranges+LIFECYCLE_CODE
        self.completed=[];self.notifications=[];self.retirement_steps=0;self.retirement_visited=set()
        self.fixture_events=[];self.critical_depth=0
        # No subscribers in the fixture. Original datastore copies/updates run;
        # callback dispatch into another task remains outside this experiment.
        subscribers=self.read(0x10006490,4)
        for key in (5,6,27,28):self.write(subscribers+key*4,4,0)
        table=self.read(0x1000647c,4)
        for key in (5,6):
            record=table+key*24
            self.write(record+4,4,CONTEXT+0x200+key*4)
            self.write(record+8,4,2)
            self.write(record+20,4,0)
            self.write(CONTEXT+0x200+key*4,4,0)

    def parse_input(self):
        while True:
            self.run([CONTEXT])
            if not self.input[self.input_pos:].startswith(b'JZJZ'):break
            self.registers=[0]*16;self.registers[0]=STOP;self.registers[1]=STACK+STACK_SIZE-16
            self.pc=0x10009d34;self.frames=[];self.loop=None;self.sar=0

    def retire(self,work):
        nodes=[];at=self.read(work+0x50,4)
        while at:
            if at in nodes or len(nodes)>=128:raise ValueError('invalid raster list')
            nodes.append(at);at=self.read(at,4)
        for offset in range(0,len(nodes),5):
            block=RetireBlock(self,nodes[offset:offset+5]);block.run()
            self.retirement_steps+=block.steps;self.retirement_visited.update(block.visited)
            self.fixture_events.append(dict(name='injected_ordered_consumption',nodes=nodes[offset:offset+5],events=len(block.events)))

    def extension(self,op,args,nxt):
        if not self.job_mode and op=='call8' and args[0] in (0x1001262c,0x100126b0):
            return StockMachine.extension(self,op,args,nxt) # Original parser lock/unlock wrappers.
        # These three exact instructions are a serialized critical-section
        # substitute. No general PS/interrupt-controller implementation is added.
        if self.job_mode and self.pc==0x1000f0dc and op=='rsil':
            assert args==(7,1) and self.critical_depth==0
            self.critical_depth=1;self.registers[7]=0;return nxt
        if self.job_mode and self.pc==0x1000f0e7 and op=='wsr.ps':
            assert args==(7,) and self.critical_depth==1 and self.registers[7]==0
            self.critical_depth=0;return nxt
        if self.job_mode and self.pc==0x1000f0ea and op=='rsync':return nxt
        if not self.job_mode or op not in ('call8','callx8'):return super().extension(op,args,nxt)
        target=self.registers[args[0]] if op=='callx8' else args[0]
        if target==0x1001809c and self.delivered==len(self.pending) and len(self.completed)<len(self.scheduled):
            work=self.scheduled[len(self.completed)]
            self.retire(work)
            self.pending.append([17,0,0,work]);self.completed.append(work)
        if target==0x1000f164:
            return StockMachine.extension(self,op,args,nxt) # Execute publication, formerly substituted.
        if target==0x100131b8:
            return ParserHarness.extension(self,'call8',(0x10013140,),nxt) # Same bounded host allocator.
        if target in (0x10017e64,0x10017ed8,0x10017dac):
            self.fixture_events.append(dict(name={0x10017e64:'semaphore_get',0x10017ed8:'semaphore_put',0x10017dac:'event_set'}[target],args=self.registers[10:13].copy()))
            self.registers[10]=0;self.branch_taken=True;return nxt
        if target==0x10013658 and self.registers[10]==10:
            ptr=self.registers[11];words=[self.read(ptr+i*4,4) for i in range(4)]
            event=dict(words=words)
            if words[0]==47:
                event['payload']=self.bytes_at(words[3],16).hex()
            self.notifications.append(event);self.registers[10]=0;self.branch_taken=True;return nxt
        return super().extension(op,args,nxt)


class CooperativePause(Exception):
    """Host scheduling boundary; not a firmware exception."""


class CooperativeLifecycle(LifecycleHarness):
    """Two saved CPU contexts sharing heap, with yields at queue boundaries.

The input parser and JobMgr have disjoint stack halves. A bounded host schedule
chooses message batches and successful FIFO completions; no wall-clock/RTOS
accuracy or hardware completion mechanism is claimed.
"""
    def __init__(self,*args,batch=1,completion_policy='eager',**kwargs):
        super().__init__(*args,**kwargs)
        if not 1<=batch<=128 or completion_policy not in ('eager','after_document','after_parser'):
            raise ValueError('invalid cooperative schedule')
        self.batch=batch;self.completion_policy=completion_policy
        self.pending=[];self.parser_done=False;self.switches=0;self.parser_steps=0
        self.thread='parser';self.retirement_eligible=False

    def capture_cpu(self):
        return dict(registers=self.registers.copy(),pc=self.pc,sar=self.sar,
                    frames=[(r.copy(),n,pc) for r,n,pc in self.frames],loop=self.loop)

    def restore_cpu(self,cpu,thread):
        self.registers=cpu['registers'];self.pc=cpu['pc'];self.sar=cpu['sar']
        self.frames=cpu['frames'];self.loop=cpu['loop'];self.thread=thread;self.job_mode=thread=='job'
        self.switches+=1
        if self.switches>200000:raise ValueError('cooperative schedule budget exhausted')

    def span(self,address,size,execute=False):
        if not execute and STACK<=address<STACK+STACK_SIZE:
            middle=STACK+STACK_SIZE//2
            low,high=(middle,STACK+STACK_SIZE) if self.thread=='parser' else (STACK,middle)
            if address<low or address+size>high:raise ValueError('cross-thread stack access')
        return super().span(address,size,execute)

    def snapshot(self):
        if len(self.snapshots)<self.delivered:super().snapshot()

    def extension(self,op,args,nxt):
        target=(self.registers[args[0]] if op=='callx8' else args[0]) if op in ('call8','callx8') else None
        if self.thread=='parser' and target==0x10013658:
            result=super().extension(op,args,nxt)
            self.pending.append(self.messages[-1]['words'].copy())
            self.pc=self.after_instruction(self.pc,result)
            raise CooperativePause('parser queued message')
        if self.thread=='job' and target==0x1001809c:
            if self.delivered==len(self.pending):
                self.snapshot()
                outstanding=len(self.completed)<len(self.scheduled)
                allowed=self.parser_done or self.completion_policy=='eager'
                if self.completion_policy=='after_document':
                    allowed=allowed or self.retirement_eligible
                if not outstanding or not allowed:
                    raise CooperativePause('job queue waits')
            if self.delivered<len(self.pending):
                if self.pending[self.delivered][0]==1:self.retirement_eligible=False
                if self.pending[self.delivered][0]==2:self.retirement_eligible=True
        return super().extension(op,args,nxt)

    def replay(self):
        self.initialize_job()
        self.registers[1]=STACK+STACK_SIZE//2-16
        job=self.capture_cpu()
        self.registers=[0]*16;self.registers[0]=STOP;self.registers[1]=STACK+STACK_SIZE-16
        self.pc=0x10009d34;self.frames=[];self.loop=None;self.sar=0
        parser=self.capture_cpu()
        while True:
            if not self.parser_done:
                self.restore_cpu(parser,'parser')
                before=self.steps
                for _ in range(self.batch):
                    try:self.run([CONTEXT] if self.pc==0x10009d34 else [])
                    except CooperativePause:continue
                    if self.pc!=STOP:raise ValueError('unexpected parser suspension')
                    if self.input[self.input_pos:].startswith(b'JZJZ'):
                        self.registers=[0]*16;self.registers[0]=STOP;self.registers[1]=STACK+STACK_SIZE-16
                        self.pc=0x10009d34;self.frames=[];self.loop=None;self.sar=0
                    else:
                        self.parser_done=True;break
                self.parser_steps+=self.steps-before;parser=self.capture_cpu()
            self.restore_cpu(job,'job')
            try:self.run()
            except CooperativePause:pass
            else:raise ValueError('JobMgr unexpectedly returned')
            job=self.capture_cpu()
            if self.parser_done and self.delivered==len(self.pending) and len(self.completed)==len(self.scheduled):break
        self.pc=STOP
        return self
