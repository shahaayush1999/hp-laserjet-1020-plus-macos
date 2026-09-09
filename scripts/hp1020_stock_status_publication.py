"""Original StatusMgr construction, publication, history and notice consumption.

The prior whole-publication substitute is removed. RTOS creation, scheduling,
locks and queues remain host services. The constructor leaves the language
context table empty, so optional outward language callbacks do not run. A real
ONLINE queue subscription may be added through original registration code.
"""
from hp1020_stock_notifications import StatusReceiver
from hp1020_stock_parser_harness import ParserHarness
from hp1020_xtensa_stock import StockMachine

HOST = {0x1001214c,0x1001809c,0x10013658,0x10013408,0x100131b8,
        0x100181a4,0x10018214,0x10017e64,0x10017ed8,
        0x10017f18,0x10018274,0x10017dd8}


class FullStatusReceiver(StatusReceiver):
    def initialize_receiver(self):
        self.receiver_mode = True
        self.job_mode = False
        self.receive_index = 0
        self.status_updates = []
        self.sent = []
        self.creates = []
        self.code_ranges += [(0x10010504,0x10010aac),(0x100135e0,0x10013600),
                             (0x1001135c,0x100113e4),(0x1001b290,0x1001b2f0)]

    def extension(self,op,args,nxt):
        if not getattr(self,'receiver_mode',False) or op != 'call8':
            return super().extension(op,args,nxt)
        target = args[0]
        a = self.registers[10:16]
        if target == 0x10010838:
            return StockMachine.extension(self,op,args,nxt)
        if target == 0x10013658:
            self.sent.append(dict(queue=a[0],words=[self.read(a[1]+i*4,4) for i in range(4)]))
        elif target in (0x10017e64,0x10017ed8):
            pass
        elif target in (0x10017f18,0x10018274,0x10017dd8):
            self.creates.append(dict(function=hex(target),args=a.copy()))
        elif target == 0x100131b8:
            return ParserHarness.extension(self,'call8',(0x10013140,),nxt)
        else:
            return super().extension(op,args,nxt)
        self.registers[10] = 0
        self.branch_taken = True
        return nxt
