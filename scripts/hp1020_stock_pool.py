"""Original allocator/free in a bounded, explicitly seeded single RAM pool.

The original semaphore primitives run normally. Boot pool discovery, timed waits
and the public allocator's retry policy remain outside this single-thread slice.
"""
from hp1020_stock_queue import QueueRAM

POOL = 0x22400000
POOL_CODE = [(0x10013140,0x10013478),(0x1001811c,0x1001816c),
             (0x100181a4,0x100181dc),(0x10018214,0x10018234),
             (0x1001a380,0x1001a3c4),(0x1001a478,0x1001a590)]


def seed_pool(state,address,size,fill):
    if address%4 or size<64 or size%4:
        raise ValueError('pool fixture must be word aligned and at least 64 bytes')
    if any(a<address+size and address<a+len(data) for a,data,_ in state.segments):
        raise ValueError('pool fixture overlaps existing RAM')
    state.segments.append((address,bytearray([fill])*size,6))
    state.write_ranges.append((address,address+size))
    state.write(address,4,state.read(0x100066a4,4))
    state.write(address+4,4,size-12)
    state.write(address+8,4,0x40000000)
    for cell in (0x10006698,0x1000669c):
        state.write(state.read(cell,4),4,address)
    state.write(state.read(0x100066a8,4),4,size-12)


class PoolRAM(QueueRAM):
    def __init__(self,program,size=8192,fill=0xcc,offset=0):
        super().__init__(program,fill)
        self.code_ranges += POOL_CODE
        self.pool,self.pool_size = POOL+offset,size
        seed_pool(self,self.pool,size,fill)

    def blocks(self):
        """Observe a partition; do not calculate allocation decisions for firmware."""
        at,end = self.pool,self.pool+self.pool_size
        result = []
        while at<end:
            assert self.read(at,4)==self.read(0x100066a4,4),'invalid pool block magic'
            size,flags = self.read(at+4,4),self.read(at+8,4)
            assert size%4==0 and at+12+size<=end,'invalid block extent'
            result.append((at,size,flags&0xe0000000))
            at += 12+size
            assert bool(flags&0x40000000)==(at==end),'wrong terminal block flag'
        assert at==end and result
        assert self.read(self.read(0x100066a8,4),4)==sum(n for _,n,f in result if not f&0x80000000)
        assert self.read(self.read(0x1000669c,4),4) in [a for a,_,_ in result]
        sem = self.read(0x100066ac,4)
        assert self.read(sem+8,4)==1 and self.read(sem+12,4)==0 and self.read(sem+16,4)==0
        return result
