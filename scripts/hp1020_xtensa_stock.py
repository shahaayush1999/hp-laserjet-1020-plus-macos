"""Isolated stock routine execution with an abstract windowed calling convention.

This supplies unlimited logical register windows, not hardware window spills,
interrupts, peripheral behavior or a boot environment. No function is stubbed.
Only explicitly selected code ranges and synthetic input/output RAM are usable.
"""
from hp1020_xtensa_call0 import Machine, MASK, STOP, signed


class StockMachine(Machine):
    def __init__(self, program, entry, code_ranges, ram_regions=()):
        super().__init__(program)
        self.pc=entry
        self.code_ranges=code_ranges
        self.frames=[]
        self.loop=None
        for start,size in ram_regions:
            if any(start<a+len(b) and start+size>a for a,b,_ in self.segments):
                raise ValueError('synthetic RAM overlaps original ELF')
            self.segments.append((start,bytearray(size),6))
            self.write_ranges.append((start,start+size))

    def span(self,address,size,execute=False):
        if execute and not any(a<=address and address+size<=b for a,b in self.code_ranges):
            raise ValueError(f'execution outside selected stock routines: {address:#x}')
        return super().span(address,size,execute)

    def extension(self,op,a,nxt):
        r=self.registers
        if op=='entry':
            if a[0]!=1 or r[1]%16:raise ValueError('unsupported ENTRY stack convention')
            r[1]=(r[1]-a[1])&MASK
        elif op in ('call4','call8','call12','callx4','callx8','callx12'):
            count=int(op.removeprefix('callx').removeprefix('call'))
            target=r[a[0]] if op.startswith('callx') else a[0]
            caller=r.copy()
            # Abstract physical register rotation; ENTRY uses the caller's SP.
            r[:]=caller[count:]+[0]*count
            r[0]=(count//4<<30)|(nxt&0x3fffffff)
            r[1]=caller[1]
            self.frames.append((caller,count,nxt))
            nxt=target
            self.branch_taken=True
        elif op in ('retw','retw.n'):
            self.branch_taken=True
            if not self.frames:
                if r[0]!=STOP:raise ValueError('unexpected top-level return address')
                nxt=STOP
            else:
                caller,count,expected=self.frames.pop()
                target=(self.pc&0xc0000000)|(r[0]&0x3fffffff)
                if target!=expected or r[0]>>30!=count//4:
                    raise ValueError('window return address changed')
                caller[count:]=r[:16-count]
                r[:]=caller
                nxt=target
            self.branch_taken=True
        elif op in ('loop','loopnez','loopgtz'):
            n=r[a[0]]
            if op=='loopnez' and n==0 or op=='loopgtz' and signed(n)<=0:
                self.loop=None;nxt=a[1]
            else:self.loop=(nxt,a[1],(n-1)&MASK)
        else:return super().extension(op,a,nxt)
        return nxt

    def after_instruction(self,pc,nxt):
        if self.loop and nxt==self.loop[1] and not self.branch_taken:
            begin,end,remaining=self.loop
            if remaining:
                self.loop=(begin,end,remaining-1)
                return begin
            self.loop=None
        return nxt
