"""Bounded stop acknowledgement code; hardware stopping is never executed.

EngineStop executes the original dispatcher until its call into hardware stop.
VideoStopTail begins after the omitted hardware reset/wait prefix, with explicit
video-owned raster lists. Its result is conditional on reaching that RAM tail.
"""
from hp1020_xtensa_stock import StockMachine
from hp1020_xtensa_call0 import STOP

MESSAGE = 0x22000000
ENGINE_HOST = {0x10013658,0x10016098}
VIDEO_HOST = {0x10013620,0x10017dac}


class StopRAM(StockMachine):
    def bytes_at(self,address,size):
        data,offset = self.span(address,size)
        return bytes(data[offset:offset+size])


class EngineStop(StopRAM):
    def __init__(self,program,reason=2,fill=0x5a,active=0,deferred=0):
        super().__init__(program,0x10016164,[(0x10016164,0x100162b0)],[(MESSAGE,16)])
        self.sent = []
        self.stop_before_hardware = False
        self.state = self.read(0x10006920,4)
        self.put(self.state,bytes([fill])*112)
        self.write(self.state+104,4,active)
        self.write(self.state+108,4,deferred)
        for i,value in enumerate((15,reason,0,0)):
            self.write(MESSAGE+i*4,4,value)

    def extension(self,op,args,nxt):
        if op == 'call8' and args[0] == 0x10016098:
            self.stop_before_hardware = True
            return STOP
        if op == 'call8' and args[0] == 0x10013658:
            r = self.registers
            self.sent.append(dict(queue=r[10],words=[self.read(r[11]+i*4,4) for i in range(4)]))
            r[10] = 0
            self.branch_taken = True
            return nxt
        return super().extension(op,args,nxt)


class VideoStopTail(StopRAM):
    def __init__(self,program,sign,refs,cursor,chains=(3,)):
        super().__init__(program,0x10013e00,[(0x10013e00,0x10013f34)],[(MESSAGE,4096)])
        if len(chains)>5 or sign and len(chains)>1 or sum(chains)>24:
            raise ValueError('invalid bounded video-list fixture')
        self.sent = []
        self.events = []
        self.nodes = []
        self.video = self.read(0x10006770,4)
        self.put(self.video,bytes(256))
        self.write(self.video+0xfc,4,sign<<31)
        for offset,value in ((0x60,0xdead1000),(0x64,0xdead2000),(0x68,0xdead3000),(0x6c,2)):
            self.write(self.video+offset,4,value)
        for slot,length in enumerate(chains):
            first = MESSAGE+len(self.nodes)*128
            for i in range(length):
                node = MESSAGE+len(self.nodes)*128
                payload = node+16
                self.nodes.append((node,payload))
                self.write(node,4,node+128 if i+1<length else 0)
                self.write(node+12,4,payload)
                self.write(payload+78,2,refs)
                self.write(payload+84,4,cursor)
            if length:
                self.write(self.video+(0xa0 if sign else 0xa4+slot*4),4,first)
        # The omitted prefix clears these two message words before the RAM tail.
        self.write(self.registers[1]+8,4,0)
        self.write(self.registers[1]+12,4,0)

    def extension(self,op,args,nxt):
        if op == 'call8' and args[0] in VIDEO_HOST:
            r = self.registers
            if args[0] == 0x10013620:
                self.sent.append(dict(queue=r[10],words=[self.read(r[11]+i*4,4) for i in range(4)]))
            else:
                self.events.append(r[10:13].copy())
            r[10] = 0
            self.branch_taken = True
            return nxt
        return super().extension(op,args,nxt)
