"""Exercise unmodified stock window vectors with synthetic nested CALL4/8/12.

The recursive fixture has no firmware entry point or peripherals. QEMU models
physical registers and window exceptions; our abstract-window interpreter is
only an additional arithmetic comparison, never the mechanism handling a spill.
"""
import hashlib
from pathlib import Path
import subprocess
import tempfile
from hp1020_qemu_ram import RETURN, STACK_TOP
from hp1020_qemu_stock_parser import VECTORS
from hp1020_xtensa_call0 import Program
from hp1020_xtensa_stock import StockMachine


def validate_windows(qemu,stock,prefix):
    cases = [];vectors = {hex(a):0 for a,_ in VECTORS}
    with tempfile.TemporaryDirectory(prefix='hp1020-windows-') as temp:
        root = Path(temp)
        source = root/'windows.S';obj = root/'windows.o';elf = root/'windows.elf'
        source.write_text('.text\n'+''.join(f'''
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
 movi a2,0
 retw
''' for width in (4,8,12)))
        subprocess.run([prefix+'-as',source.name,'-o',obj.name],cwd=root,check=True)
        subprocess.run([prefix+'-ld','-Ttext=0x20000000','-e','recurse8',obj.name,'-o',elf.name],cwd=root,check=True)
        fixture = Program(elf,prefix)
        qemu.load(stock.path);qemu.load(elf)
        qemu.set_reg(111,0x10000000)
        def run(width,depth,salt):
            entry = fixture.symbols[f'recurse{width}']
            qemu.put(RETURN-3,bytes.fromhex('0b8000'))
            qemu.reset_cpu(RETURN-3)
            top = STACK_TOP-0x100
            qemu.put(top-0x6000,bytes([0xcc])*0x6100)
            qemu.put(top-12,(top+64).to_bytes(4,'big'))
            qemu.set_reg(2,top);qemu.set_reg(42,0x40000)
            qemu.set_reg(9,entry);qemu.set_reg(11,depth);qemu.set_reg(12,salt)
            steps = 0;counts = {hex(a):0 for a,_ in VECTORS}
            while (pc := qemu.reg(0)) != RETURN:
                if steps>=20000:
                    raise ValueError('window test instruction budget exhausted')
                if any(a<=pc<b for a,b in VECTORS):
                    stock.instruction(pc)
                elif any(a<=pc<b for a,b in fixture.execute_ranges):
                    fixture.instruction(pc)
                elif pc != RETURN-3:
                    raise ValueError(f'window test left selected code: {pc:#x}')
                if hex(pc) in counts:counts[hex(pc)] += 1
                reply = qemu.command('s')
                assert reply.startswith('T05'),reply
                steps += 1
            assert qemu.reg(38)==0 and qemu.reg(39)==1
            return qemu.reg(11),steps,counts
        for width in (4,8,12):
            for depth in (0,1,2,3,4,7,8,16,32,64):
                for salt in (1,0x1234567,0xffffffff):
                    actual,steps,counts = run(width,depth,salt)
                    expected = depth*(depth+1)//2*salt & 0xffffffff
                    assert actual == expected, (width,depth,salt,actual,expected)
                    model = StockMachine(fixture,fixture.symbols[f'recurse{width}'],fixture.execute_ranges)
                    assert model.run([depth,salt]) == expected
                    for address,count in counts.items():vectors[address] += count
                    cases.append(dict(call_window=width,depth=depth,salt=salt,result=actual,
                                      instructions=steps,vector_entries=counts,status='pass'))
        assert all(count>0 for count in vectors.values()),vectors
        # Deliberately lose the saved return address in the QEMU RAM copy only.
        # Unmodified original bytes are reloaded afterward; the stock ELF is never edited.
        qemu.put(0x10000080,bytes.fromhex('029c94'))  # S32E a2,a9,-16 replaces S32E a0,a9,-16.
        try:
            value,_,_ = run(8,16,1)
        except (ValueError,AssertionError) as error:
            mutation = dict(status='detected',error=str(error))
        else:
            assert value != 136,'corrupt stock spill unexpectedly retained the return chain'
            mutation = dict(status='detected',wrong_result=value)
        qemu.load(stock.path)
        return dict(status='pass',cases=cases,total_cases=len(cases),vector_entries=vectors,
                    mutation=mutation,fixture_elf_sha256=hashlib.sha256(elf.read_bytes()).hexdigest(),
                    fixture_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                    scope='Original six window spill/fill handlers execute under independent QEMU exceptions for CALL4/8/12 recursion through depth 64. Results match a triangular-number arithmetic oracle and the abstract interpreter. Corrupting one saved-return store in the QEMU RAM copy is detected.',
                    limits='Synthetic, aligned ABI stacks and QEMU test_kc705_be with 32 physical ARs; not stock boot state, real core register count, interrupts, cache or malformed-stack recovery.')
