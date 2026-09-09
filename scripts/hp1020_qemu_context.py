"""Original window flush and voluntary context save/restore on synthetic RAM.

This uses QEMU's physical register windows, PS and RFE, not an abstract context
model. It deliberately schedules the same synthetic thread; a successful round
trip does not prove cross-thread scheduling, interrupt delivery or stock boot.
"""
import hashlib
from pathlib import Path
import subprocess
import tempfile

from hp1020_qemu_ram import RETURN, STACK_TOP
from hp1020_qemu_stock_parser import VECTORS, guard_memory
from hp1020_stock_stop import StopRAM
from hp1020_xtensa_call0 import Program

THREAD = 0x22000000
FLUSH = [(0x1001b128,0x1001b239),(0x1001b23c,0x1001b25f)]
CONTEXT = [(0x10018750,0x100187df),(0x100188f3,0x1001896a)]


def validate_context(q,stock,prefix):
    with tempfile.TemporaryDirectory(prefix='hp1020-context-') as temp:
        root = Path(temp)
        source = '.text\n'+''.join(f'''
.align 4
.global recurse{mode}{width}
recurse{mode}{width}:
 entry a1,64
 beqz a2,done{mode}{width}
 addi a{width+2},a2,-1
 mov a{width+3},a3
 call{width} recurse{mode}{width}
 mull a2,a2,a3
 add a2,a{width+2},a2
 retw
 done{mode}{width}:
 movi a8,{target:#x}
 callx8 a8
 movi a2,0
 retw
''' for mode,target in [('flush',0x1001b23c),('context',0x10018750)] for width in (4,8,12))
        (root/'context.S').write_text(source)
        # Relative input names keep ELF file symbols independent of /tmp paths.
        subprocess.run([prefix+'-as','--text-section-literals','context.S','-o','context.o'],cwd=root,check=True)
        subprocess.run([prefix+'-ld','-Ttext=0x20000000','-e','recursecontext8','context.o','-o','context.elf'],cwd=root,check=True)
        elf = root/'context.elf'
        fixture = Program(elf,prefix)
        state = StopRAM(stock,0,[],[(THREAD,256)])
        state.segments += fixture.segments
        current = state.read(0x10006a9c,4)
        selected = state.read(0x10006aa0,4)
        timeslice = state.read(0x10006ac8,4)
        cases = []
        mutation_applied = False

        def word(address):
            return int.from_bytes(q.read(address,4),'big')

        def run(mode,width,depth,salt,mutate=False):
            nonlocal mutation_applied
            q.load(stock.path)
            q.load(elf)
            q.put(THREAD,bytes(256))
            q.put(current,THREAD.to_bytes(4,'big'))
            q.put(selected,THREAD.to_bytes(4,'big'))
            q.put(timeslice,(7).to_bytes(4,'big'))
            q.put(THREAD+28,(23).to_bytes(4,'big'))
            q.put(RETURN-3,bytes.fromhex('0b8000'))
            q.reset_cpu(RETURN-3)
            top = STACK_TOP-0x100
            q.put(top-0x6000,bytes([0xcc])*0x6100)
            q.put(top-12,(top+64).to_bytes(4,'big'))
            q.set_reg(2,top)
            q.set_reg(42,0x40000)
            q.set_reg(111,0x10000000)
            q.set_reg(9,fixture.symbols[f'recurse{mode}{width}'])
            q.set_reg(11,depth)
            q.set_reg(12,salt)
            # Nonzero architectural loop/SAR values must survive the context
            # save. Inert loop addresses avoid triggering a hardware loop.
            q.set_reg(33,0x20010000)
            q.set_reg(34,0x20010004)
            q.set_reg(35,17)
            q.set_reg(36,11)
            saved = None
            frame_checked = False
            mutated = False
            seen = set()
            steps = 0
            while (pc := q.reg(0)) != RETURN:
                if steps>=20000:
                    raise ValueError('context instruction budget exhausted')
                if pc == 0x10018753:
                    wb = q.reg(38)
                    regs = [q.reg(((wb*4+i)%32)+1) for i in range(16)]
                    frame = regs[1]-128
                    ps = q.reg(42)
                    saved = (frame,[regs[0],regs[1],ps,frame]+regs[4:16]+
                             [q.reg(33),q.reg(34),q.reg(35),q.reg(36),ps|16,0x100187dd])
                if pc == 0x1001879f:
                    frame,expected = saved
                    # Untouched a4..a15 have no defined incoming values here. Reading their
                    # raw physical slots before access-triggered window spills
                    # may see an older live window, not a defined callee value.
                    defined = list(range(4))+list(range(16,22))
                    assert all(word(frame+i*4)==expected[i] for i in defined),(
                        mode,width,depth,[(i,hex(expected[i]),hex(word(frame+i*4)))
                                         for i in defined if expected[i]!=word(frame+i*4)])
                    frame_checked = True
                if pc == 0x100187d7:
                    frame,_ = saved
                    assert word(THREAD+8)==frame and word(current)==0
                    assert word(THREAD+24)==23 and word(timeslice)==0
                    if mutate:
                        q.put(frame+84,(0xdeadbeef).to_bytes(4,'big'))
                        mutated = True
                        mutation_applied = True
                if pc != RETURN-3:
                    if any(a<=pc<b for a,b in fixture.execute_ranges):
                        program,ranges = fixture,fixture.execute_ranges
                    else:
                        program,ranges = stock,VECTORS+FLUSH+CONTEXT
                    op,args,raw = program.instruction(pc)
                    if not any(a<=pc and pc+len(raw)<=b for a,b in ranges):
                        raise ValueError(f'context left selected code: {pc:#x}')
                    state.pc = pc
                    guard_memory(state,q,op,args)
                seen.add(pc)
                steps += 1
                reply = q.command('s')
                if not reply.startswith('T05'):
                    raise ValueError(f'context step failed: {reply}')
            expected = depth*(depth+1)//2*salt&0xffffffff
            assert q.reg(11)==expected
            assert q.reg(38)==0 and q.reg(39)==1
            # CALLINC and OWB record intervening window calls/exceptions; RETW
            # does not restore them to the synthetic startup value.
            assert q.reg(42)&~0x30f00==0x40000,(mode,width,depth,hex(q.reg(42)))
            if mode=='context':
                assert frame_checked and word(current)==THREAD
                assert word(THREAD+4)==1 and word(timeslice)==23
                # The return chain may change SAR while restoring windows;
                # the saved context itself is checked before restoring it.
            assert not mutated,'mutated continuation unexpectedly returned normally'
            return dict(mode=mode,call_window=width,depth=depth,salt=salt,
                        result=expected,instructions=steps,frame_checked=frame_checked,status='pass')

        for mode in ('flush','context'):
            for width in (4,8,12):
                for depth in (0,1,2,3,7,16,32):
                    for salt in (1,0x1234567,0xffffffff):
                        cases.append(run(mode,width,depth,salt))
        try:
            run('context',8,7,1,mutate=True)
        except ValueError as error:
            assert mutation_applied and 'PC is not an annotated instruction boundary' in str(error)
            mutation = dict(status='detected',error=str(error))
        else:
            raise AssertionError('corrupt context continuation was not detected')
        return dict(status='pass',total_cases=len(cases),cases=cases,mutation=mutation,
            elf_sha256=hashlib.sha256(stock.path.read_bytes()).hexdigest(),
            fixture_elf_sha256=hashlib.sha256(elf.read_bytes()).hexdigest(),
            fixture_source_sha256=hashlib.sha256(source.encode()).hexdigest(),
            findings=[
                'Original explicit window flush preserves the nested return chain for CALL4/8/12 through depth 32, matching a triangular-number arithmetic oracle.',
                'Original voluntary context save, window flush, scheduler selection and RFE restoration execute on QEMU. Before explicit window flushing, saved return/stack and loop/SAR/PS/continuation fields match an independently captured CPU-register oracle; untouched data registers can alias older live windows before access-triggered spilling and are not treated as preserved input; flushing may reuse ABI spill slots, and the restored caller arithmetic also agrees; current-thread pointer, run count and time-slice bookkeeping agree.',
                'Corrupting the saved continuation in synthetic RAM is detected before execution can leave the permitted code ranges.'
            ],
            limits='Only the same synthetic thread is selected after each voluntary save. A different QEMU core, synthetic stacks and an explicitly seeded ordinary-thread/time-slice environment are used. No cross-thread switch, actual interrupt, timer delivery, boot, custom raster opcode, MMIO or printer execution is established.')
