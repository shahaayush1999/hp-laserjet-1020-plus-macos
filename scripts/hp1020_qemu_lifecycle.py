"""Independent QEMU execution of original JobMgr completion/cleanup paths.

Parser-produced RAM and the existing bounded host service fixture are inputs.
QEMU executes JobMgr, libc, datastore, critical-section and actual window-vector
instructions. Successful FIFO raster consumption remains an injected event;
its RAM retirement helper retains the earlier interpreter implementation.
"""
from hp1020_stock_lifecycle_harness import LifecycleHarness
from hp1020_stock_parser_harness import BOUNDARIES
from hp1020_stock_jobmgr_harness import JOB_BOUNDARIES
from hp1020_qemu_stock_parser import VECTORS, guard_memory
from hp1020_qemu_ram import RETURN, STACK_TOP
from hp1020_xtensa_call0 import STOP

HOST = (set(BOUNDARIES)|set(JOB_BOUNDARIES)|{0x100131b8,0x10017e64,0x10017ed8,0x10017dac})-{0x1000f164,0x1001b770}


class QemuLifecycle(LifecycleHarness):
    def replay_qemu(self,qemu,budget=200000):
        self.parse_input()
        self.parser_steps = self.steps
        self.pending = [m['words'] for m in self.messages]
        self.initialize_job()
        self.code_ranges = self.code_ranges+VECTORS+[(0x1001b770,0x1001b788)]
        q = qemu
        q.load(self.program.path)
        self.to_qemu(q)
        q.put(RETURN-3,bytes.fromhex('0b8000'))
        q.reset_cpu(RETURN-3)
        top = STACK_TOP-0x100
        q.set_reg(2,top);q.put(top-12,(top+64).to_bytes(4,'big'))
        q.set_reg(111,0x10000000);q.set_reg(42,0x40000)
        q.set_reg(9,0x1000e414)
        self.qemu_steps = 0
        self.vector_entries = {hex(a):0 for a,_ in VECTORS}
        while True:
            pc = q.reg(0)
            if self.qemu_steps>=budget:
                raise ValueError('QEMU lifecycle instruction budget exhausted')
            if pc in HOST:
                wb = q.reg(38)
                physical = lambda n: ((wb*4+n)%32)+1
                self.registers = [q.reg(physical(n)) for n in range(16)]
                ret = (self.registers[8]&0x3fffffff)|(pc&0xc0000000)
                self.pc = ret-3
                op,operands,_ = self.program.instruction(self.pc)
                assert op in ('call8','callx8')
                if op=='call8':assert operands[0]==pc
                self.from_qemu(q)
                result = self.extension('call8',(pc,),ret)
                self.to_qemu(q)
                if result == STOP:
                    self.pc = STOP
                    return self  # Original infinite task is stopped at empty queue.
                assert result == ret
                q.set_reg(physical(10),self.registers[10]);q.set_reg(0,ret)
                continue
            self.pc = pc
            if pc != RETURN-3:
                if not any(a<=pc<b for a,b in self.code_ranges):
                    raise ValueError(f'QEMU lifecycle left selected code: {pc:#x}')
                op,args,_ = self.program.instruction(pc)
                guard_memory(self,q,op,args)
            if hex(pc) in self.vector_entries:self.vector_entries[hex(pc)] += 1
            self.visited.add(pc);self.steps += 1;self.qemu_steps += 1
            reply = q.command('s')
            if not reply.startswith('T05'):
                raise ValueError(f'QEMU single-step failed: {reply}')

    def to_qemu(self,qemu):
        for begin,end in self.write_ranges:
            qemu.put(begin,self.bytes_at(begin,end-begin))

    def from_qemu(self,qemu):
        for begin,end in self.write_ranges:
            self.put(begin,qemu.read(begin,end-begin))
