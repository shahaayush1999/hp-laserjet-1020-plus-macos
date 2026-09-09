"""Two synthetic tasks use original stack construction and voluntary switching.

Task selection is written by the synthetic tasks themselves. Original firmware
saves, flushes, selects and restores the CPU contexts; there is no host context
substitution. Scheduling policy and interrupt delivery are outside this fixture.
"""
import hashlib
from pathlib import Path
import subprocess
import tempfile
from hp1020_qemu_context import FLUSH, CONTEXT
from hp1020_qemu_ram import RETURN, STACK_TOP
from hp1020_qemu_stock_parser import VECTORS, guard_memory
from hp1020_stock_stop import StopRAM
from hp1020_stock_notifications import invoke
from hp1020_xtensa_call0 import Program

A = 0x22000000
B = A+256
DATA = A+512
BSTACK = 0x22010000


def validate_switch(q,stock,prefix):
    with tempfile.TemporaryDirectory(prefix='hp1020-switch-') as temp:
        root = Path(temp)
        probe = StopRAM(stock,0,[])
        selected = probe.read(0x10006aa0,4)
        current = probe.read(0x10006a9c,4)
        source = '.text\n'+''.join(f'''
.align 4
.global recurse{width}
recurse{width}:
 entry a1,64
 beqz a2,done{width}
 addi a{width+2},a2,-1
 mov a{width+3},a3
 call{width} recurse{width}
 mull a2,a2,a3
 add a2,a{width+2},a2
 retw
 done{width}:
 movi a4,{DATA:#x}
 l32i a4,a4,0
 movi a5,0
again{width}:
 add a5,a5,a3
 movi a8,{selected:#x}
 movi a9,{B:#x}
 s32i a9,a8,0
 movi a8,0x10018750
 callx8 a8
 addi a4,a4,-1
 bnez a4,again{width}
 mov a2,a5
 retw
''' for width in (4,8,12))+f'''
.align 4
.global task_b
task_b:
 entry a1,64
 movi a2,0
 movi a3,0
 movi a4,{DATA:#x}
 l32i a4,a4,4
loop_b:
 addi a2,a2,1
 add a3,a3,a4
 movi a8,{DATA:#x}
 s32i a2,a8,8
 s32i a3,a8,12
 movi a8,{selected:#x}
 movi a9,{A:#x}
 s32i a9,a8,0
 movi a8,0x10018750
 callx8 a8
 j loop_b
'''
        (root/'switch.S').write_text(source)
        subprocess.run([prefix+'-as','--text-section-literals','switch.S','-o','switch.o'],cwd=root,check=True)
        subprocess.run([prefix+'-ld','-Ttext=0x20000000','-e','recurse8','switch.o','-o','switch.elf'],cwd=root,check=True)
        elf = root/'switch.elf'
        fixture = Program(elf,prefix)
        cases = []
        for width in (4,8,12):
            for depth in (0,3,16):
                for rounds in (1,2,7):
                    for fill in (0,0xcc):
                        # Independently run the original stack-frame builder in
                        # both engines before using that actual frame for task B.
                        built = []
                        for engine in (None,q):
                            state = StopRAM(stock,0x1001ae2c,[(0x1001ae2c,0x1001ae79)],
                                            [(A,1024),(BSTACK,0x10000)])
                            state.segments += fixture.segments
                            state.put(A,bytes(1024))
                            state.put(BSTACK,bytes([fill])*0x10000)
                            end = BSTACK+0xffef
                            state.write(B+16,4,end)
                            invoke(state,0x1001ae2c,[B,fixture.symbols['task_b']],engine)
                            frame = (end&~15)-128
                            expected = [0,end&~15]+[0]*18+[state.read(0x10006b98,4),fixture.symbols['task_b']]
                            assert state.read(B+8,4)==frame
                            assert [state.read(frame+i*4,4) for i in range(22)]==expected
                            assert state.bytes_at(frame+88,40)==bytes([fill])*40
                            built.append((state.bytes_at(A,1024),state.bytes_at(BSTACK,0x10000)))
                        assert built[0]==built[1]
                        # The second builder ran in QEMU, leaving its exact
                        # frame in RAM. Only stock globals/fixture code are loaded.
                        q.load(stock.path)
                        q.load(elf)
                        q.put(current,A.to_bytes(4,'big'))
                        q.put(selected,A.to_bytes(4,'big'))
                        q.put(DATA,rounds.to_bytes(4,'big')+(0x12345).to_bytes(4,'big')+bytes(8))
                        q.put(RETURN-3,bytes.fromhex('0b8000'))
                        q.reset_cpu(RETURN-3)
                        top = STACK_TOP-0x100
                        q.put(top-0x6000,bytes([fill])*0x6100)
                        q.put(top-12,(top+64).to_bytes(4,'big'))
                        q.set_reg(2,top)
                        q.set_reg(42,0x40000)
                        q.set_reg(111,0x10000000)
                        q.set_reg(9,fixture.symbols[f'recurse{width}'])
                        q.set_reg(11,depth)
                        q.set_reg(12,0x1234567)
                        steps = 0
                        selections = []
                        while (pc := q.reg(0)) != RETURN:
                            if steps>=20000:
                                raise ValueError('two-task instruction budget exhausted')
                            if pc == 0x10018904:
                                selections.append(int.from_bytes(q.read(selected,4),'big'))
                            if pc != RETURN-3:
                                if any(a<=pc<b for a,b in fixture.execute_ranges):
                                    program,ranges = fixture,fixture.execute_ranges
                                else:
                                    program,ranges = stock,VECTORS+FLUSH+CONTEXT
                                op,args,raw = program.instruction(pc)
                                if not any(a<=pc and pc+len(raw)<=b for a,b in ranges):
                                    raise ValueError(f'two-task left selected code: {pc:#x}')
                                state.pc = pc
                                guard_memory(state,q,op,args)
                            steps += 1
                            reply = q.command('s')
                            assert reply.startswith('T05'),reply
                        word = lambda a:int.from_bytes(q.read(a,4),'big')
                        wb = q.reg(38)
                        # Physical windows can shift across task switches. Read
                        # logical caller a10 using WINDOWBASE, not fixed AR10.
                        actual = q.reg(((wb*4+10)%32)+1)
                        expected = ((depth*(depth+1)//2+rounds)*0x1234567)&0xffffffff
                        assert actual==expected
                        assert word(DATA+8)==rounds and word(DATA+12)==rounds*0x12345
                        assert selections==[B,A]*rounds
                        assert word(A+4)==rounds and word(B+4)==rounds
                        assert word(current)==A and q.reg(39)==1<<wb
                        assert q.reg(42)&~0x30f00==0x40000
                        assert 0x21000000<=word(A+8)<0x21020000
                        assert BSTACK<=word(B+8)<BSTACK+0x10000
                        cases.append(dict(call_window=width,depth=depth,rounds=rounds,fill=fill,
                            task_a_result=actual,task_b_result=word(DATA+12),switches=len(selections),
                            final_windowbase=wb,instructions=steps,status='pass'))
        return dict(status='pass',total_cases=len(cases),cases=cases,
            fixture_elf_sha256=hashlib.sha256(elf.read_bytes()).hexdigest(),
            fixture_source_sha256=hashlib.sha256(source.encode()).hexdigest(),
            findings=[
                'Original initial-stack builder agrees between the interpreter, QEMU and a complete defined-frame oracle, including alignment and untouched padding.',
                'Two synthetic tasks alternate on separate stacks using original voluntary save, window flush, scheduler selection and RFE restoration. Both independent arithmetic accumulators and every selection/run count agree across nested CALL4/8/12 and repeated switches.',
                'After a cross-thread switch WINDOWBASE can differ from startup: results must be read through the current logical register mapping. The remaining live window matches that current base.'
            ],
            limits='The fixture tasks explicitly choose each other by writing the selected-thread pointer. This verifies context switching, not RTOS priority policy, interrupts, timer expiry, blocking task integration, boot, custom instructions, hardware or physical printing. Task B remains suspended after task A completes.')
