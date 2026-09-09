"""JobMgr cancellation under an explicit single-work stopping fixture.

Original admission/parser/JobMgr work is retained. At the stop boundary the
fixture assumes one scheduled work owns the video raster chain and that reset
reaches its RAM tail. The original tail executes on a separate stack. Its
acknowledgement is relayed to JobMgr through the separately tested PrintMgr
handshake contract. Engine stopping and RTOS timing are not modeled.
"""
from hp1020_stock_lifecycle_harness import LifecycleHarness
from hp1020_stock_jobmgr_harness import JobMgrHarness
from hp1020_stock_stop import VideoStopTail, StopRAM, MESSAGE
from hp1020_xtensa_call0 import STOP, STACK


class Cancellation(LifecycleHarness):
    def __init__(self,*args,reason=2,timing='after_document',flags=None,**kwargs):
        super().__init__(*args,**kwargs)
        assert reason in (2,4) and timing in ('before_document_end','after_document')
        self.code_ranges += [(0x1000ee6c,0x1000eeb8),(0x1000efd8,0x1000f068)]
        self.reason = reason
        self.timing = timing
        self.flags = flags
        self.cancelled = False
        self.stop_trace = []

    def extension(self,op,args,nxt):
        if self.job_mode and op == 'call8':
            target = args[0]
            if target == 0x1001809c:
                inject_at = len(self.pending)-(self.timing=='before_document_end')
                if self.delivered == inject_at and not self.cancelled:
                    if self.timing == 'before_document_end':
                        assert self.pending[-1][0] == 2
                    self.cancelled = True
                    self.pending.insert(self.delivered,[15,self.reason,0,0])
                # No successful-page completion is injected during cancellation.
                return JobMgrHarness.extension(self,op,args,nxt)
            if target == 0x10013658:
                queue,ptr = self.registers[10:12]
                words = [self.read(ptr+i*4,4) for i in range(4)]
                if queue == 1 and words[0] == 15:
                    assert len(self.scheduled) == 1
                    work = self.scheduled[0]
                    self.original_flags = [self.read(work+0x4a,1),self.read(work+0x72,1)]
                    if self.flags is not None:
                        self.write(work+0x4a,1,self.flags[0])
                        self.write(work+0x72,1,self.flags[1])
                    tail = VideoStopTail(self.program,0,0,0,())
                    tail.segments = self.segments
                    tail.write_ranges = self.write_ranges
                    tail.registers[1] = STACK+0x4000-16
                    tail.put(tail.video,bytes(256))
                    tail.write(tail.video+0x60,4,work)
                    tail.write(tail.video+0xa4,4,self.read(work+0x50,4))
                    tail.run([1])
                    self.stop_trace = tail.sent
                    assert len(tail.sent)==1 and tail.sent[0]['queue']==1 and tail.sent[0]['words'][0]==37
                    self.pending.insert(self.delivered,tail.sent[0]['words'])
                    self.registers[10] = 0
                    self.branch_taken = True
                    return nxt
        return super().extension(op,args,nxt)


RELAY_HOST = {0x1001214c,0x10010838,0x1001809c,0x10013658,0x100181a4,0x10018214}
REQUEST_HOST = {0x10013658,0x10010a8c,0x10010f54,0x10010fd0,0x10010a3c}


class StatusCancelRelay(StopRAM):
    def __init__(self,program,packet):
        super().__init__(program,0x10010590,[(0x10010590,0x1001074e),(0x10011178,0x100111ec)],[(MESSAGE,512)])
        self.packet = packet
        self.delivered = False
        self.sent = []
        self.effects = []
        self.write(self.read(0x100063d8,4)+24,1,1)
        table = self.read(0x1000647c,4)
        self.write(table+27*24+4,4,MESSAGE+64)
        self.write(table+27*24+8,4,2)
        self.write(MESSAGE+64,4,1)

    def extension(self,op,args,nxt):
        if op != 'call8' or args[0] not in RELAY_HOST:
            return super().extension(op,args,nxt)
        target = args[0]
        a = self.registers[10:14]
        if target == 0x1001809c:
            assert a[0] == self.read(0x100063b4,4) and a[2] == 0xffffffff
            if self.delivered:
                return STOP
            for i,value in enumerate(self.packet):
                self.write(a[1]+i*4,4,value)
            self.delivered = True
        elif target == 0x10013658:
            self.sent.append(dict(queue=a[0],words=[self.read(a[1]+i*4,4) for i in range(4)]))
        elif target == 0x10010838:
            self.effects.append(a[:2])
        self.registers[10] = 0
        self.branch_taken = True
        return nxt


class StatusCancelRequest(StopRAM):
    def __init__(self,program):
        super().__init__(program,0x10010838,[(0x10010838,0x10010a3c)])
        self.sent = []
        self.effects = []
        state = self.read(0x100063d8,4)
        self.write(state+4,4,2)
        self.write(state+8,4,0x100)
        self.write(state+24,1,1)

    def extension(self,op,args,nxt):
        if op != 'call8' or args[0] not in REQUEST_HOST:
            return super().extension(op,args,nxt)
        a = self.registers[10:14]
        if args[0] == 0x10013658:
            self.sent.append(dict(queue=a[0],words=[self.read(a[1]+i*4,4) for i in range(4)]))
        else:
            self.effects.append(dict(function=hex(args[0]),args=a.copy()))
        self.registers[10] = 0
        self.branch_taken = True
        return nxt
