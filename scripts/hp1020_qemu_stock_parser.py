"""Original parser executed by QEMU, with the existing explicit host services.

QEMU independently executes every selected stock instruction, including the
original window overflow/underflow vectors. Allocation/input/queues deliberately
share the prior host boundary fixture; this cross-check challenges CPU semantics,
not the truth of those environment assumptions. Single stepping rejects PCs
outside selected parser/libc/vector code before they execute.
"""
from hp1020_qemu_ram import RETURN, STACK_TOP
from hp1020_stock_parser_harness import ParserHarness, BOUNDARIES, CONTEXT

VECTORS = [(0x10000000,0x1000000f),(0x10000040,0x1000004f),
           (0x10000080,0x1000009e),(0x100000c0,0x100000de),
           (0x10000100,0x1000012a),(0x10000140,0x1000016a)]


def guard_memory(state,qemu,op,args):
    """Bound effective RAM addresses before QEMU steps standard load/store ops.

This is an access gate, not a CPU implementation: QEMU still decodes/executes
bytes and determines values, flags, loops and control flow independently.
"""
    base = op.removesuffix('.n')
    sizes = {'l8ui':1,'l16ui':2,'l16si':2,'l32i':4,'l32e':4,
             's8i':1,'s16i':2,'s32i':4,'s32e':4}
    if base == 'l32r':
        address,size = args[1],4
    elif base in sizes:
        wb = qemu.reg(38)
        value = qemu.reg(((wb*4+args[1])%32)+1)
        address,size = (value+args[2])&0xffffffff,sizes[base]
    else:
        return
    state.span(address,size)
    if size in (2,4) and address%size:
        raise ValueError(f'unaligned QEMU access {address:#x}/{size}')
    if base.startswith('s') and not any(a<=address and address+size<=b for a,b in state.write_ranges):
        raise ValueError(f'QEMU write outside mutable RAM {address:#x}')


class QemuParser(ParserHarness):
    def __init__(self,program,data,qemu,fill=0xcc,read_limit=None):
        self.qemu = None
        super().__init__(program,data,fill,read_limit)
        qemu.load(program.path)
        for begin,end in self.write_ranges:
            qemu.put(begin,self.bytes_at(begin,end-begin))
        self.qemu = qemu
        qemu.set_reg(111,0x10000000)  # VECBASE: original stock window handlers.
        qemu.put(RETURN-3,bytes.fromhex('0b8000'))
        qemu.reset_cpu(RETURN-3)
        self.stack_top = STACK_TOP-0x100
        qemu.set_reg(2,self.stack_top)
        # An outer synthetic caller provides the ABI save area for the wrapper.
        # This remains within the fixture stack; original spill code uses it.
        qemu.put(self.stack_top-12,(self.stack_top+64).to_bytes(4,'big'))
        qemu.set_reg(42,0x40000)
        qemu.set_reg(9,0x10009d34)
        qemu.set_reg(11,CONTEXT)
        self.vector_entries = {hex(a):0 for a,_ in VECTORS}

    def read(self,address,size):
        if self.qemu is None:
            return super().read(address,size)
        self.span(address,size)
        if size in (2,4) and address%size:
            raise ValueError('unaligned fixture read')
        return int.from_bytes(self.qemu.read(address,size),'big')

    def put(self,address,data):
        super().put(address,data)
        if self.qemu is not None:
            self.qemu.put(address,data)

    def write(self,address,size,value):
        super().write(address,size,value)
        if self.qemu is not None:
            self.qemu.put(address,(value & ((1<<(size*8))-1)).to_bytes(size,'big'))

    def bytes_at(self,address,size):
        if self.qemu is None:
            return super().bytes_at(address,size)
        self.span(address,size)
        return self.qemu.read(address,size)

    def run(self,args=(),budget=100000):
        if args and list(args)!=[CONTEXT]:
            raise ValueError('QEMU parser context is fixed')
        q = self.qemu
        while (pc := q.reg(0)) != RETURN:
            if self.steps >= budget:
                raise ValueError('QEMU parser instruction budget exhausted')
            if pc in BOUNDARIES:
                wb = q.reg(38)
                physical = lambda n: ((wb*4+n)%32)+1
                self.registers = [q.reg(physical(n)) for n in range(16)]
                ret = (self.registers[8]&0x3fffffff)|(pc&0xc0000000)
                self.pc = ret-3
                op,operands,_ = self.program.instruction(self.pc)
                assert op in ('call8','callx8')
                if op=='call8':assert operands[0]==pc
                # CALL8 already ran; no ENTRY has rotated the callee window yet.
                ParserHarness.extension(self,'call8',(pc,),ret)
                result = self.registers[10]
                if BOUNDARIES[pc]=='allocate':
                    q.put(result,bytes([self.fill])*self.allocations[result]['size'])
                q.set_reg(physical(10),result)
                q.set_reg(0,ret)
                continue
            allowed = self.code_ranges+VECTORS+[(RETURN-3,RETURN)]
            if not any(a<=pc<b for a,b in allowed):
                raise ValueError(f'QEMU parser left selected code: {pc:#x}')
            if pc != RETURN-3:
                op,operands,_ = self.program.instruction(pc)  # Exact annotated stock instruction start.
                self.pc = pc
                guard_memory(self,q,op,operands)
            if hex(pc) in self.vector_entries:
                self.vector_entries[hex(pc)] += 1
            self.visited.add(pc);self.steps += 1
            reply = q.command('s')
            if not reply.startswith('T05'):
                raise ValueError(f'QEMU single-step failed: {reply}')
        if q.reg(38)!=0 or q.reg(39)!=1:
            raise ValueError('QEMU parser did not restore caller window')
        self.pc = RETURN
        return q.reg(11)
