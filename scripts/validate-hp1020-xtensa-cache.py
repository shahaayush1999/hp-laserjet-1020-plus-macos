#!/usr/bin/env python3
"""Recover stock cache operands; check bounded call0 cache routines offline.

Cache/TLB effects are NOT modeled. The interpreter records operands, QEMU
independently executes cache instructions, and neither proves physical visibility.
Original TLB writes are recorded only; this QEMU CPU has a different MMU profile.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

from hp1020_qemu_ram import QemuRAM, RETURN
from hp1020_xtensa_call0 import Program, Machine, STOP, MASK
from hp1020_xtensa_stock import StockMachine

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'open-firmware/xtensa-cache'
PREFIX = os.environ.get('XTENSA_PREFIX','/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf')
OPERATIONS = {'dhwb':(0x100173c8,0x100173e6,'hp1020_dcache_clean_owned','242700'),
              'dhwbi':(0x10017414,0x10017432,'hp1020_dcache_clean_invalidate_owned','252700')}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Trace(StockMachine):
    def __init__(self, program, entry, stop=None):
        super().__init__(program,entry,program.execute_ranges)
        self.events = []
        self.stop = stop

    def extension(self, op, args, nxt):
        if op in OPERATIONS:
            self.events.append([op,(self.registers[args[0]]+args[1])&MASK])
        elif op in ('witlb','wdtlb'):
            self.events.append([op,self.registers[args[0]],self.registers[args[1]]])
        elif op in ('dsync','isync'):
            self.events.append([op])
        else:
            return super().extension(op,args,nxt)
        return nxt

    def after_instruction(self, pc, nxt):
        if self.program.instruction(pc)[0]=='memw':
            self.events.append(['memw'])
        nxt = super().after_instruction(pc,nxt)
        return STOP if nxt==self.stop else nxt


def native(q, program, entry, args, allowed, stock=False):
    """Observe registers before actual cache instructions, reject other accesses."""
    q.load(program.path)
    if stock:
        q.put(RETURN-3,bytes.fromhex('0b8000'))
        q.reset_cpu(RETURN-3)
        q.set_reg(42,0x40000)
        q.set_reg(9,entry)
        for i,value in enumerate(args,11):
            q.set_reg(i,value)
    else:
        q.reset_cpu(entry)
        for i,value in enumerate(args,3):
            q.set_reg(i,value)
    events = []
    for _ in range(20000):
        pc = q.reg(0)
        if pc==RETURN:
            assert q.reg(38)==0 and q.reg(39)==1
            return q.reg(11 if stock else 3),events
        if stock and pc==RETURN-3:
            pass
        else:
            op,a,raw = program.instruction(pc)
            assert any(start<=pc and pc+len(raw)<=end for start,end in allowed)
            # No indirect calls, peripheral loads/stores or unexpected helpers.
            assert op in {'entry','retw.n','ret.n','retw','ret','movi','movi.n','mov.n',
                'or','extui','add.n','add','addi.n','addi','srli','slli','loopnez',
                'beqz','beqz.n','bnez','bnez.n','bne','bltu','memw','dsync',*OPERATIONS},op
            if op in OPERATIONS:
                wb = q.reg(38)
                value = q.reg(((wb*4+a[0])%32)+1)+a[1]
                # Every executed cache address stays in synthetic RAM; rejected
                # high/MMIO inputs must branch away before reaching this gate.
                assert 0x10000000<=value<0x40000000
                events.append([op,value])
            elif op in ('memw','dsync'):
                events.append([op])
        assert q.command('s').startswith('T05')
    raise ValueError('cache instruction budget exhausted')


def main():
    inputs = [Path(__file__),SOURCE/'hp1020_dcache.S',SOURCE/'hp1020_dcache.h']
    inputs += [ROOT/'scripts'/n for n in ('hp1020_xtensa_call0.py','hp1020_xtensa_stock.py',
               'hp1020_xtensa_properties.py','hp1020_qemu_ram.py')]
    identities = {str(p.relative_to(ROOT)):sha(p) for p in inputs}
    stock = Program(ROOT/'analysis/sihp1020.elf',PREFIX)
    assert sha(stock.path)=='2111560068db47ceca21fa550db4c7c34f5595b5a5d137ae4a19631e40e3601d'
    memory = Machine(stock)
    assert memory.read(0x10005cd0,4)==0x22222222
    assert memory.read(0x10005c9c,4)==0xff222244
    assert memory.read(0x10005ca0,4)==0xe0000000
    attributes = []
    for start,end,value in ((0x10006d4a,0x10006da2,2),(0x10006def,0x10006e52,None)):
        state = Trace(stock,start,end)
        state.run(budget=1000)
        for op in ('witlb','wdtlb'):
            wanted = [[op,value if value is not None else (0xff222244>>(i*4))&15,i<<29] for i in range(8)]
            assert [e for e in state.events if e[0]==op]==wanted
        attributes.append(dict(start=hex(start),stop=hex(end),
            instruction_attributes=[e[1] for e in state.events if e[0]=='witlb'],
            data_attributes=[e[1] for e in state.events if e[0]=='wdtlb'],
            regions=[e[2] for e in state.events if e[0]=='wdtlb'],
            isync_count=state.events.count(['isync']),dsync_count=state.events.count(['dsync'])))
    observations = []
    with tempfile.TemporaryDirectory(prefix='hp1020-cache-') as directory:
        temp = Path(directory)
        subprocess.run([PREFIX+'-as','--no-transform',SOURCE/'hp1020_dcache.S','-o',temp/'cache.o'],check=True)
        subprocess.run([PREFIX+'-ld','-Ttext=0x20000000','-e','hp1020_dcache_clean_owned',
                        temp/'cache.o','-o',temp/'cache.elf'],check=True)
        program = Program(temp/'cache.elf',PREFIX)
        # Hand assembly does not produce GCC's instruction-property table.
        # Bound both complete functions by their ELF symbol sizes and require
        # contiguous decoding; no alignment padding is admitted as code.
        names={item[2] for item in OPERATIONS.values()}
        listing=subprocess.check_output([PREFIX+'-nm','-n','-S',program.path],text=True)
        ranges=[]
        for line in listing.splitlines():
            fields=line.split()
            if len(fields)==4 and fields[3] in names:
                start,size=int(fields[0],16),int(fields[1],16)
                ranges.append((start,start+size))
        assert len(ranges)==2
        program.instructions={}
        for start,end in ranges:
            listing=subprocess.check_output([PREFIX+'-objdump','-d',f'--start-address={start}',
                f'--stop-address={end}',program.path],text=True)
            pc=start
            for address,instruction in Program.parse(listing):
                assert address==pc
                program.instructions[address]=instruction
                pc+=len(instruction[2])
            assert pc==end
        allowed = {'movi','movi.n','or','extui','slli','add','addi','ret.n','beqz','bnez','bltu','bne','memw','dsync',*OPERATIONS}
        for pc,(op,args,raw) in program.instructions.items():
            assert op in allowed,(hex(pc),op)
            if op in OPERATIONS:
                assert args==(2,0) and raw.hex()==OPERATIONS[op][3]
        for op,(entry,end,name,encoding) in OPERATIONS.items():
            assert stock.instruction(entry+19)==(op,(2,0),bytes.fromhex(encoding))
            for offset in (0,1,15):
                for size in (0,1,15,16,17,63,64):
                    address = 0x22000000+offset
                    state = Trace(stock,entry)
                    state.run([address,size],budget=1000)
                    count=(size+offset+15)//16
                    assert state.events==[[op,address+i*16] for i in range(count)]+[['dsync']]
                    observations.append(dict(kind='stock',operation=op,address=address,bytes=size,events=state.events))
            # Overflow is an original arithmetic finding, never executed as a
            # cache access in QEMU or accepted by the replacement API.
            state=Trace(stock,entry)
            state.run([0x2200000f,0xfffffff0],budget=1000)
            assert state.events==[['dsync']]
        cases = [(0x22000000,0),(0x90000001,0),(0x22000000,16),(0x22000010,64),
                 (0x22000000,256),(0x10000000,16),(0x3ffffff0,16),
                 (0x22000001,16),(0x22000000,1),(0x22000000,15),(0x22000000,17),
                 (0x22000000,0xfffffff0),(0x3ffffff0,32),(0x90000000,16),
                 (0xb3000000,16),(0x0ffffff0,16),(0,16),(0xfffffff0,32)]
        with QemuRAM() as q:
            for op,(entry,end,name,_) in OPERATIONS.items():
                for address,size in ((0x22000000,0),(0x22000001,0),(0x2200000f,1),
                                     (0x22000000,16),(0x22000001,64),(0x2200000f,17)):
                    state=Trace(stock,entry);state.run([address,size])
                    _,events=native(q,stock,entry,[address,size],[(entry,end)],stock=True)
                    assert events==state.events
                for address,size in cases:
                    admitted = size==0 or (address%16==0 and size%16==0 and
                        0x10000000<=address<address+size<=0x40000000)
                    wanted = ([['memw']]+[[op,a] for a in range(address,address+size,16)]+[['dsync']]
                              if admitted and size else [])
                    state=Trace(program,program.symbols[name])
                    result=state.run([address,size],budget=20000)
                    assert result==int(admitted) and state.events==wanted,(name,address,size)
                    actual,events=native(q,program,program.symbols[name],[address,size],ranges)
                    assert actual==result and events==wanted
                    observations.append(dict(kind='open',operation=op,address=address,bytes=size,
                                             result=result,events=events))
                print('Checked original operands and open '+op+' ranges',flush=True)
            version=q.version
        assert all(sha(ROOT/n)==h for n,h in identities.items())
        report=dict(status='pass',source_sha256=identities,stock_elf_sha256=sha(stock.path),
            target_elf_sha256=sha(program.path),qemu_version=version,
            startup_operand_traces=attributes,
            observations_sha256=hashlib.sha256(json.dumps(observations,sort_keys=True).encode()).hexdigest(),
            stock_unaligned_zero_bytes='A nonaligned zero-length request still issues one cache operation.',
            stock_length_overflow='Address0x2200000f,length0xfffffff0 wraps the rounded count to zero; only DSYNC runs. The open API rejects this request before any operation.',
            interpreted_stock_cases=44,native_stock_cases=12,open_cases=36,
            limits='Cache/TLB effects are not modeled. Original TLB operand computation runs only with record-only writes; QEMU uses a different processor profile. Original/open cache instructions execute in QEMU with every operand constrained to synthetic RAM. No actual dirty cache, bus alias, CPU/DMA mapping, line geometry, MMIO, USB, boot, physical visibility or printer is established. The open routines are not linked to a hardware/entry backend.')
        (ROOT/'analysis/boot-handoff/cache-contract.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')


if __name__=='__main__':
    main()
