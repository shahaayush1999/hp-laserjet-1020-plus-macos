"""Original notification producers/consumers, with explicit task boundaries.

ONLINE notification tests execute the original registered-subscriber writer and
relay its packet to a separately initialized PrintMgr sharing the committed
ONLINE value. This is compositional execution, not an RTOS schedule simulation.
Status receiver tests consume original JobMgr-produced notices, while treating
status publication as an observed host boundary; no physical output runs.
"""
from hp1020_stock_printmgr_harness import PrintMgrHarness, HOST as PRINT_HOST
from hp1020_stock_lifecycle_harness import LifecycleHarness
from hp1020_xtensa_call0 import STOP, STACK, STACK_SIZE
from hp1020_qemu_task import run_task

PRODUCER_HOST = PRINT_HOST | {0x10017e64,0x10017ed8}
RECEIVER_HOST = {0x1001214c,0x1001809c,0x10010838,0x10013408,
                 0x100181a4,0x10018214}


def invoke(state, entry, args=(), qemu=None, host=()):
    """Begin a fresh synthetic CALL8, preserving existing RAM and ownership."""
    state.pc = entry
    state.registers = [0]*16
    state.registers[0] = STOP
    state.registers[1] = STACK+STACK_SIZE-16
    state.frames = []
    state.loop = None
    state.sar = 0
    if qemu is None:
        return state.run(args)
    return run_task(state,qemu,host,args=args)


class NotificationProducer(PrintMgrHarness):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.code_ranges += [(0x10010f54,0x100111b4)]

    def extension(self,op,args,nxt):
        if op == 'call8' and args[0] in (0x10017e64,0x10017ed8):
            self.registers[10] = 0
            self.branch_taken = True
            return nxt
        return super().extension(op,args,nxt)


class StatusReceiver(LifecycleHarness):
    def initialize_receiver(self):
        self.receiver_mode = True
        self.job_mode = False
        self.code_ranges += [(0x10010590,0x100106ab)]
        self.receive_index = 0
        self.status_updates = []
        # Explicit startup state: no active documents or observed counters.
        for cell,size in [(0x100063d8,28),(0x100063e0,4),(0x10006408,4)]:
            self.put(self.read(cell,4),bytes(size))

    def extension(self,op,args,nxt):
        if not getattr(self,'receiver_mode',False) or op != 'call8':
            return super().extension(op,args,nxt)
        target = args[0]
        a = self.registers[10:14]
        if target == 0x10010838:
            self.status_updates.append(a[:2])
        elif target == 0x1001214c:
            pass
        elif target == 0x1001809c:
            assert a[0] == self.read(0x100063b4,4) and a[2] == 0xffffffff
            if self.receive_index == len(self.notifications):
                return STOP
            for i,value in enumerate(self.notifications[self.receive_index]['words']):
                self.write(a[1]+i*4,4,value)
            self.receive_index += 1
        else:
            return super().extension(op,args,nxt)
        self.registers[10] = 0
        self.branch_taken = True
        return nxt
