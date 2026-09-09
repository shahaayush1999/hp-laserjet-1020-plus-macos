"""Selected original PrintMgr execution in RAM, with explicit host queue input.

Executes dispatch, stop sequencing, list removal, media notification state and
small queue wrappers. Original datastore subscription registration also runs. RTOS startup/delivery, allocator and serialized
critical sections remain host services. No engine or VideoThread MMIO runs here.
"""
from hp1020_stock_parser_harness import ParserHarness
from hp1020_xtensa_call0 import STOP

HOST = {0x1001214c, 0x10013658, 0x1001809c,
        0x100131b8, 0x100181a4, 0x10018214,
        0x10013140, 0x10013408, 0x1001b770}
CODE = [(0x1000f324,0x1000f84c), (0x1000fcb0,0x1000fea4),
        (0x10010158,0x10010170), (0x10010218,0x10010298),
        (0x10013000,0x100130d4), (0x100111b4,0x100111ec),
        (0x1001135c,0x100113e4), (0x1001b290,0x1001b2f0)]


class PrintMgrHarness(ParserHarness):
    def __init__(self, program, messages, fill=0xcc, media=0, pending=0, active=0):
        super().__init__(program, b'', fill)
        self.pc = 0x1000f324
        self.code_ranges = CODE
        self.pending = messages
        self.delivered = 0
        self.sent = []
        self.snapshots = []
        for key in (1,24):
            self.write(self.read(0x10006490,4)+key*4,4,0)
        self.nodes = []
        self.works = []
        for cell, size in [(0x10006338,20), (0x10006340,40), (0x10006344,16),
                           (0x10006324,8), (0x10006328,8)]:
            self.put(self.read(cell,4), bytes(size))
        self.write(self.read(0x10006340,4), 4, media)
        for cell, count in [(0x10006324,pending), (0x10006328,active)]:
            nodes = []
            for _ in range(count):
                work = self.allocate(0x94)
                node = self.allocate(16)
                self.works.append(work)
                nodes.append(node)
            for i, node in enumerate(nodes):
                for offset, value in [(0,nodes[i+1] if i+1<count else 0),
                                      (4,5), (8,1), (12,self.works[-count+i])]:
                    self.write(node+offset,4,value)
            if nodes:
                self.write(self.read(cell,4),4,nodes[0])
                self.write(self.read(cell,4)+4,4,nodes[-1])
            self.nodes.extend(nodes)
        self.registers[8:] = [0]*8

    def allocate(self, size):
        self.registers[10:12] = [size,0]
        ParserHarness.extension(self,'call8',(0x10013140,),self.pc)
        return self.registers[10]

    def snapshot(self):
        self.snapshots.append(dict(delivered=self.delivered,
                                   state=self.read(self.read(0x10006338,4)+4,4),
                                   nodes_freed=sum(self.allocations[n]['freed'] for n in self.nodes),
                                   sent=len(self.sent)))

    def extension(self, op, args, nxt):
        if op == 'wsr.ps':
            assert self.registers[args[0]] == 0
            return nxt  # Explicit serialized critical-section fixture.
        if op == 'rsync':
            return nxt
        if op != 'call8' or args[0] not in HOST:
            return super().extension(op,args,nxt)
        target = args[0]
        a = self.registers[10:15]
        if target in (0x1001214c,0x1001b770):
            pass
        elif target == 0x100131b8:
            return ParserHarness.extension(self,'call8',(0x10013140,),nxt)
        elif target in (0x100181a4,0x10018214):
            return ParserHarness.extension(self,op,args,nxt)
        elif target == 0x10013658:
            self.sent.append(dict(queue=a[0], words=[self.read(a[1]+i*4,4) for i in range(4)]))
        elif target == 0x1001809c:
            assert a[0] == self.read(0x1000632c,4) and a[2] == 0xffffffff
            self.snapshot()
            if self.delivered == len(self.pending):
                return STOP
            for i,value in enumerate(self.pending[self.delivered]):
                self.write(a[1]+i*4,4,value)
            self.delivered += 1
        else:
            return super().extension(op,args,nxt)
        self.registers[10] = 0
        self.branch_taken = True
        return nxt
