"""Independent QEMU runner for a selected stock task and bounded host services.

The task owns its RAM fixture and host boundary implementation. QEMU executes
original instruction bytes; standard memory accesses and selected PC ranges are
checked before every step. Actual stock window vectors and critical-mask helpers
execute. Host service agreement is deliberately not independent environment proof.
"""
from hp1020_qemu_stock_parser import VECTORS, guard_memory
from hp1020_qemu_ram import RETURN, STACK_TOP
from hp1020_xtensa_call0 import STOP


def run_task(state, q, host, args=(), budget=100000):
    entry = state.pc
    code = state.code_ranges + VECTORS + [(0x1001b770,0x1001b788)]
    host = set(host) - {0x1001b770}
    q.load(state.program.path)
    def to_qemu():
        for begin,end in state.write_ranges:
            q.put(begin,state.bytes_at(begin,end-begin))
    def from_qemu():
        for begin,end in state.write_ranges:
            state.put(begin,q.read(begin,end-begin))
    to_qemu()
    q.put(RETURN-3,bytes.fromhex('0b8000'))
    q.reset_cpu(RETURN-3)
    top = STACK_TOP-0x100
    q.set_reg(2,top)
    q.put(top-12,(top+64).to_bytes(4,'big'))
    q.set_reg(111,0x10000000)
    q.set_reg(42,0x40000)
    q.set_reg(9,entry)
    for i,value in enumerate(args,11):
        q.set_reg(i,value)
    state.qemu_steps = 0
    state.vector_entries = {hex(a):0 for a,_ in VECTORS}
    while True:
        pc = q.reg(0)
        if pc == RETURN:
            from_qemu()
            assert q.reg(38) == 0 and q.reg(39) == 1
            state.pc = STOP
            return q.reg(11)
        if state.qemu_steps >= budget:
            raise ValueError('QEMU task instruction budget exhausted')
        if pc in host:
            wb = q.reg(38)
            physical = lambda n: ((wb*4+n)%32)+1
            state.registers = [q.reg(physical(n)) for n in range(16)]
            ret = (state.registers[8]&0x3fffffff)|(pc&0xc0000000)
            state.pc = ret-3
            op,operands,_ = state.program.instruction(state.pc)
            assert op in ('call8','callx8')
            if op == 'call8':
                assert operands[0] == pc
            from_qemu()
            result = state.extension('call8',(pc,),ret)
            to_qemu()
            if result == STOP:
                state.pc = STOP
                return state
            assert result == ret
            q.set_reg(physical(10),state.registers[10])
            q.set_reg(0,ret)
            continue
        state.pc = pc
        if pc != RETURN-3:
            if not any(a<=pc<b for a,b in code):
                raise ValueError(f'QEMU task left selected code: {pc:#x}')
            op,operands,_ = state.program.instruction(pc)
            guard_memory(state,q,op,operands)
        if hex(pc) in state.vector_entries:
            state.vector_entries[hex(pc)] += 1
        state.visited.add(pc)
        state.qemu_steps += 1
        reply = q.command('s')
        if not reply.startswith('T05'):
            raise ValueError(f'QEMU task single-step failed: {reply}')
