"""Original RTOS queue RAM operations, with explicit single-thread preconditions.

No queue operation is a host service. The interpreter abstracts interrupt masking;
QEMU executes the original RSIL/WSR.PS/RSYNC instructions. Scheduling is absent
from the nonblocking slice and remains an explicit boundary for blocked waiters.
"""
from hp1020_stock_stop import StopRAM

QUEUE = 0x22000000
BUFFER = 0x22001000
SOURCE = 0x22002000
DEST = 0x22002100
THREAD = 0x22003000
CODE = [(0x10017f18,0x10017f90),(0x1001809c,0x1001811c),
        (0x100199a4,0x10019a30),(0x10019eb4,0x1001a380),
        (0x100135e0,0x10013600),(0x10013658,0x10013688)]


class QueueRAM(StopRAM):
    def __init__(self,program,fill=0):
        super().__init__(program,0x10017f18,CODE.copy(),[(QUEUE,0x4000)])
        self.put(QUEUE,bytes([fill])*0x4000)
        self.ps = 0x40000
        # A synthetic ordinary thread is current; interrupt/system state is zero.
        self.write(self.read(0x10006a9c,4),4,THREAD)
        self.write(self.read(0x10005d80,4),4,0)
        self.write(self.read(0x10006b70,4),4,0)
        self.write(self.read(0x10006b74,4),4,0)

    def extension(self,op,args,nxt):
        if op == 'rsil':
            self.registers[args[0]] = self.ps
            self.ps = (self.ps&~15)|args[1]
        elif op == 'wsr.ps':
            self.ps = self.registers[args[0]]
        elif op == 'rsync':
            pass
        else:
            return super().extension(op,args,nxt)
        return nxt


class QueueWaitRace(QueueRAM):
    """A queued wait is satisfied before its suspend helper runs.

    This is an explicit instruction-boundary interleaving. It checks the original
    pending-suspension cancellation logic, not actual interrupt reachability.
    """
    def __init__(self,program,fill=0):
        super().__init__(program,fill)
        self.code_ranges += [(0x100176c8,0x1001788a),(0x1001aac0,0x1001ab79)]
        self.put(THREAD,bytes(256))
        self.write(self.read(0x10006aa0,4),4,THREAD)
        self.write(self.read(0x10006ac0,4),4,0)
        self.cut_suspend = True
        self.suspensions = []

    def extension(self,op,args,nxt):
        if self.cut_suspend and op=='call8' and args[0]==0x100176c8:
            from hp1020_xtensa_call0 import STOP
            self.suspensions.append(self.registers[10])
            return STOP
        return super().extension(op,args,nxt)
