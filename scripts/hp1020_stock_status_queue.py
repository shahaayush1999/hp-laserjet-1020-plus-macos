"""Original status task backed by original RAM queues, stopping at task suspension.

Completed JobMgr notices are pre-enqueued, not injected by the receive service.
The status constructor creates its own queue. Empty receive executes original
wait-list insertion and stops before the scheduler; no context switch is faked.
"""
from hp1020_stock_status_publication import FullStatusReceiver, HOST as STATUS_HOST
from hp1020_stock_queue import QueueRAM, CODE
from hp1020_xtensa_stock import StockMachine
from hp1020_xtensa_call0 import STOP

RAM = 0x22600000
THREAD = RAM+0x3000
HOST = (STATUS_HOST-{0x10017f18,0x10013658,0x1001809c})|{0x100176c8}


class QueuedStatusReceiver(FullStatusReceiver):
    def initialize_receiver(self):
        super().initialize_receiver()
        self.code_ranges += CODE
        self.segments.append((RAM,bytearray(0x4000),6))
        self.write_ranges.append((RAM,RAM+0x4000))
        self.ps = 0x40000
        self.suspended = []
        self.write(self.read(0x10006a9c,4),4,THREAD)
        self.write(self.read(0x10005d80,4),4,0)
        self.write(self.read(0x10006b70,4),4,0)
        self.write(self.read(0x10006b74,4),4,0)
        self.write(self.read(0x10006ac0,4),4,0)

    def extension(self,op,args,nxt):
        if not getattr(self,'receiver_mode',False):
            return super().extension(op,args,nxt)
        if op in ('rsil','wsr.ps','rsync'):
            return QueueRAM.extension(self,op,args,nxt)
        if op == 'call8':
            if args[0] in (0x10017f18,0x10013658,0x1001809c):
                return StockMachine.extension(self,op,args,nxt)
            if args[0] == 0x100176c8:
                self.suspended.append(self.registers[10])
                return STOP
        return super().extension(op,args,nxt)

