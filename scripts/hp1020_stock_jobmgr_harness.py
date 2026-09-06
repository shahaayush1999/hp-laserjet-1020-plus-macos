"""Replay parser messages through original JobMgr/list/BIH-copy instructions.

This is a serialized RAM fixture. Task startup, document publication, RTOS
critical sections and queue deliveries are explicit host boundaries. No
PrintMgr/VideoThread consumer, interrupt controller or hardware is executed.
"""
from hp1020_stock_parser_harness import ParserHarness, CONTEXT
from hp1020_xtensa_call0 import STOP, STACK, STACK_SIZE

JOB_CODE = [(0x1000e414,0x1000ee6c),(0x1000eeb8,0x1000efd8),(0x1000f280,0x1000f29c),
            (0x10011178,0x100111b4),(0x10013000,0x10013050),
            (0x1001b34d,0x1001b485)]
JOB_BOUNDARIES = {0x1001214c:'task_ready',0x1001809c:'queue_receive',
                  0x1000f164:'document_publish',0x1001b770:'critical_section'}


class JobMgrHarness(ParserHarness):
    def __init__(self,program,data,fill=0xcc,duplex=0,credits=20):
        super().__init__(program,data,fill)
        self.job_mode=False
        self.duplex=duplex;self.credits=credits
        self.job_events=[];self.delivered=0;self.snapshots=[];self.scheduled=[]

    def parse_input(self):
        self.run([CONTEXT])

    def replay(self):
        self.parse_input()
        self.parser_steps=self.steps
        self.pending=[m['words'] for m in self.messages]
        self.initialize_job()
        self.run()
        return self

    def initialize_job(self):
        self.job_mode=True
        self.code_ranges=self.code_ranges+JOB_CODE
        self.registers=[0]*16;self.registers[0]=STOP;self.registers[1]=STACK+STACK_SIZE-16
        self.pc=0x1000e414;self.frames=[];self.loop=None;self.sar=0
        # Fixture state: empty document list, normal input acceptance, no cancel,
        # fixed scheduling credits and configurable duplex datastore byte.
        for cell,size in [(0x100062e4,8),(0x100062fc,1),(0x10006308,4)]:
            self.put(self.read(cell,4),bytes(size))
        self.write(self.read(0x100062e8,4),2,self.credits)
        table=self.read(0x1000647c,4)
        self.write(table+36*24+4,4,CONTEXT+0x100)
        self.write(table+36*24+8,4,0)
        self.write(CONTEXT+0x100,1,self.duplex)

    def snapshot(self):
        if not self.delivered:return
        words=self.pending[self.delivered-1]
        doc_list=self.read(0x100062e4,4)
        doc_node=self.read(doc_list+4,4)
        work=0
        if doc_node:
            doc=self.read(doc_node+12,4)
            child_node=self.read(doc+0x74,4)
            if child_node:work=self.read(self.read(child_node+12,4)+0x48,4)
        self.snapshots.append(dict(message=words.copy(),work=work,
            work_bytes=self.bytes_at(work,0x94).hex() if work else None))

    def extension(self,op,a,nxt):
        if not self.job_mode or op not in ('call8','callx8'):
            return super().extension(op,a,nxt)
        target=self.registers[a[0]] if op=='callx8' else a[0]
        if target==0x10013658:
            queue,ptr=self.registers[10:12]
            words=[self.read(ptr+i*4,4) for i in range(4)]
            if queue!=1 or words[0]!=11:raise ValueError('unexpected downstream queue message')
            self.scheduled.append(words[3])
            self.registers[10]=0;self.branch_taken=True
            return nxt
        if target not in JOB_BOUNDARIES:
            return super().extension(op,a,nxt)
        args=self.registers[10:14];name=JOB_BOUNDARIES[target]
        event=dict(name=name,callsite=f'0x{self.pc:08x}',args=args.copy())
        result=0
        if name=='queue_receive':
            if args[0]!=self.read(0x100062d0,4) or args[2]!=2:
                raise ValueError('unexpected JobMgr queue receive contract')
            self.snapshot()
            if self.delivered==len(self.pending):
                self.job_events.append(event)
                self.branch_taken=True
                return STOP
            for i,v in enumerate(self.pending[self.delivered]):self.write(args[1]+i*4,4,v)
            self.delivered+=1
        elif name=='document_publish':
            # The omitted function updates datastore records 27/28, queues a
            # publication to queue 10, then writes this local bookkeeping flag.
            # This is an explicit substitute, not instruction-derived execution.
            self.write(args[0]+0x6b,1,1)
        elif name=='critical_section':
            # Serialized execution has no interrupts. Return previous mask zero.
            result=0
        self.job_events.append(event)
        self.registers[10]=result;self.branch_taken=True
        return nxt
