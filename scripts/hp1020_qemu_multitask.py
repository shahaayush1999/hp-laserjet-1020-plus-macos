"""Bounded persistent QEMU stepping across native tasks and explicit host services."""
from hp1020_xtensa_call0 import STOP
from hp1020_qemu_ram import RETURN
from hp1020_qemu_stock_parser import guard_memory


class NativeTasks:
    def __init__(self,q,state,fixture,ranges,host=()):
        self.q,self.state,self.fixture,self.ranges = q,state,fixture,ranges
        self.host = set(host)
        self.steps = 0
        self.visited = set()
        self.services = []

    def synchronize(self,to_qemu):
        for start,end in self.state.write_ranges:
            if to_qemu:
                self.q.put(start,self.state.bytes_at(start,end-start))
            else:
                self.state.put(start,self.q.read(start,end-start))

    def step(self):
        q,state = self.q,self.state
        pc = q.reg(0)
        if self.steps>=200000:
            raise ValueError('native multitask budget exhausted')
        if pc in self.host:
            wb = q.reg(38)
            physical = lambda n:((wb*4+n)%32)+1
            state.registers = [q.reg(physical(n)) for n in range(16)]
            ret = (state.registers[8]&0x3fffffff)|(pc&0xc0000000)
            state.pc = ret-3
            op,args,_ = state.program.instruction(state.pc)
            assert op in ('call8','callx8')
            if op=='call8':
                assert args[0]==pc
            self.synchronize(False)
            result = state.extension('call8',(pc,),ret)
            assert result==ret and result!=STOP
            self.synchronize(True)
            q.set_reg(physical(10),state.registers[10])
            q.set_reg(0,ret)
            self.services.append(pc)
        else:
            if pc!=RETURN-3:
                if any(a<=pc<b for a,b in self.fixture.execute_ranges):
                    program,ranges = self.fixture,self.fixture.execute_ranges
                else:
                    program,ranges = state.program,self.ranges
                op,args,raw = program.instruction(pc)
                if not any(a<=pc and pc+len(raw)<=b for a,b in ranges):
                    raise ValueError(f'native tasks left selected code: {pc:#x}')
                if op in ('excw','ill','break'):
                    raise ValueError(f'unsupported native task instruction: {pc:#x} {op}')
                state.pc = pc
                guard_memory(state,q,op,args)
            reply = q.command('s')
            if not reply.startswith('T05'):
                raise ValueError(f'native task step failed: {reply}')
        self.visited.add(pc)
        self.steps += 1
