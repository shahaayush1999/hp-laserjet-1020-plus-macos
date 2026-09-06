"""Bounded concrete Xtensa call0 interpreter for synthetic RAM-only C tests.

No peripherals, register windows, interrupts, caches, custom instructions,
floating point or hardware division are emulated. Unknown operations fail.
"""
from pathlib import Path
import re
import struct
import subprocess

MASK=0xffffffff
STOP=0xfffffffc
STACK=0x21000000
STACK_SIZE=0x20000

def signed(x):return x if x<0x80000000 else x-0x100000000

class Program:
    def __init__(self,path,prefix):
        self.path=Path(path);self.prefix=prefix;data=self.path.read_bytes()
        if data[:6]!=b'\x7fELF\x01\x02':raise ValueError('expected ELF32 big-endian')
        self.entry,phoff,shoff=struct.unpack_from('>III',data,24)
        phsize,phnum,shsize,shnum=struct.unpack_from('>HHHH',data,42)
        self.segments=[];self.write_ranges=[];self.execute_ranges=[]
        for i in range(phnum):
            typ,off,va,_,filesz,memsz,flags,_=struct.unpack_from('>8I',data,phoff+i*phsize)
            if typ!=1:continue
            if memsz>0x200000:raise ValueError('excessive synthetic ELF RAM')
            self.segments.append((va,bytearray(data[off:off+filesz])+bytearray(memsz-filesz),flags))
        for i in range(shnum):
            _,_,flags,addr,_,size,_,_,_,_=struct.unpack_from('>10I',data,shoff+i*shsize)
            if flags&3==3 and size:self.write_ranges.append((addr,addr+size))
            if flags&4 and size:self.execute_ranges.append((addr,addr+size))
        text=subprocess.check_output([prefix+'-objdump','-d',str(path)],text=True)
        nm=subprocess.check_output([prefix+'-nm','-n',str(path)],text=True,stderr=subprocess.DEVNULL)
        self.symbols={name:int(addr,16) for addr,name in re.findall(r'^([0-9a-f]+) \w (\S+)$',nm,re.M)}
        self.instructions=dict(self.parse(text))
    @staticmethod
    def parse(text):
        for line in text.splitlines():
            m=re.match(r'\s*([0-9a-f]{8}):\s+([0-9a-f]{4,6})\s+(\S+)\s*(.*)',line)
            if not m:continue
            pc=int(m[1],16);op=m[3];body=m[4].split('<')[0].strip()
            args=[]
            for s in body.split(',') if body else []:
                s=s.strip()
                if re.fullmatch(r'a\d+',s):args.append(int(s[1:]))
                elif re.fullmatch(r'[0-9a-f]{8}',s):args.append(int(s,16))
                else:
                    try:args.append(int(s,0))
                    except ValueError:args.append(s)
            yield pc,(op,tuple(args),bytes.fromhex(m[2]))
    def instruction(self,pc):
        if pc not in self.instructions:
            text=subprocess.check_output([self.prefix+'-objdump','-d',f'--start-address={pc}',f'--stop-address={pc+3}',str(self.path)],text=True)
            self.instructions.update(self.parse(text))
        if pc not in self.instructions:raise ValueError(f'cannot decode reached PC {pc:#x}')
        return self.instructions[pc]

class Machine:
    def __init__(self,program):
        self.program=program
        self.segments=[(a,b.copy(),flags) for a,b,flags in program.segments]+[(STACK,bytearray(STACK_SIZE),6)]
        self.write_ranges=program.write_ranges+[(STACK,STACK+STACK_SIZE)]
        self.registers=[0]*16;self.registers[0]=STOP;self.registers[1]=STACK+STACK_SIZE-16
        self.sar=0;self.pc=program.entry;self.steps=0;self.visited=set();self.opcodes=set()
    def span(self,address,size,execute=False):
        if not 0<=address<=MASK or address+size>0x100000000:raise ValueError('address wraps')
        if execute and not any(a<=address and address+size<=b for a,b in self.program.execute_ranges):raise ValueError('execute outside code section')
        if address<0xc0000000 and address+size>0xb0000000:raise ValueError('MMIO forbidden')
        for start,data,flags in self.segments:
            if start<=address and address+size<=start+len(data) and (not execute or flags&1):return data,address-start
        raise ValueError(f'unmapped RAM {address:#x}+{size}')
    def read(self,address,size):
        if size in (2,4) and address%size:raise ValueError(f'unaligned load {address:#x}/{size}')
        data,off=self.span(address,size);return int.from_bytes(data[off:off+size],'big')
    def write(self,address,size,value):
        if size in (2,4) and address%size:raise ValueError('unaligned store')
        if not any(a<=address and address+size<=b for a,b in self.write_ranges):raise ValueError(f'write outside mutable RAM {address:#x}')
        data,off=self.span(address,size);data[off:off+size]=(value&((1<<(size*8))-1)).to_bytes(size,'big')
    def put(self,address,value):
        if not any(a<=address and address+len(value)<=b for a,b in self.write_ranges):raise ValueError('input outside RAM')
        data,off=self.span(address,len(value));data[off:off+len(value)]=value
    def extension(self,op,args,next_pc):
        raise ValueError(f'unsupported target instruction at {self.pc:#x}: {op} {args}')
    def after_instruction(self,pc,next_pc):
        return next_pc
    def run(self,args=(),budget=10000000):
        r=self.registers
        for i,v in enumerate(args,2):r[i]=v&MASK
        while self.pc!=STOP:
            if self.steps>=budget:raise ValueError('instruction budget exhausted')
            pc=self.pc;op,a,raw=self.program.instruction(pc)
            data,off=self.span(pc,len(raw),True)
            if bytes(data[off:off+len(raw)])!=raw:raise ValueError('executed bytes differ from disassembly')
            self.steps+=1;self.visited.add(pc);self.opcodes.add(op)
            self.branch_taken=False
            nxt=pc+len(raw);base=op.removesuffix('.n')
            if base=='movi':r[a[0]]=a[1]&MASK
            elif base=='mov':r[a[0]]=r[a[1]]
            elif base in ('addi','addmi'):r[a[0]]=(r[a[1]]+a[2])&MASK
            elif base in ('add','sub','and','or','xor','mull'):
                x,y=r[a[1]],r[a[2]]
                r[a[0]]={'add':lambda:x+y,'sub':lambda:x-y,'and':lambda:x&y,'or':lambda:x|y,'xor':lambda:x^y,'mull':lambda:x*y}[base]()&MASK
            elif base in ('addx2','addx4','addx8','subx2','subx4','subx8'):
                x=r[a[1]]*int(base[-1]);y=r[a[2]];r[a[0]]=(x+y if base.startswith('add') else x-y)&MASK
            elif base in ('min','max','minu','maxu'):
                x,y=r[a[1]],r[a[2]];fx,fy=(x,y) if base.endswith('u') else (signed(x),signed(y))
                r[a[0]]=x if (fx<fy)==base.startswith('min') else y
            elif base=='neg':r[a[0]]=(-r[a[1]])&MASK
            elif base=='abs':r[a[0]]=abs(signed(r[a[1]]))&MASK
            elif base=='extui':r[a[0]]=(r[a[1]]>>a[2])&((1<<a[3])-1)
            elif base=='slli':r[a[0]]=(r[a[1]]<<a[2])&MASK
            elif base=='srli':r[a[0]]=r[a[1]]>>a[2]
            elif base=='srai':r[a[0]]=(signed(r[a[1]])>>a[2])&MASK
            elif base=='ssl':self.sar=32-(r[a[0]]&31)
            elif base=='ssr':self.sar=r[a[0]]&31
            elif base=='ssai':self.sar=a[0]
            elif base=='ssa8b':self.sar=32-((r[a[0]]&3)*8)
            elif base=='ssa8l':self.sar=(r[a[0]]&3)*8
            elif base=='sll':r[a[0]]=(r[a[1]]<<(32-self.sar))&MASK
            elif base=='srl':r[a[0]]=r[a[1]]>>self.sar
            elif base=='sra':r[a[0]]=(signed(r[a[1]])>>self.sar)&MASK
            elif base=='src':r[a[0]]=(((r[a[1]]<<32)|r[a[2]])>>self.sar)&MASK
            elif base=='nsau':r[a[0]]=32-r[a[1]].bit_length()
            elif base=='nsa':
                x=r[a[1]];r[a[0]]=31-(x if x<0x80000000 else (~x)&MASK).bit_length()
            elif base in ('moveqz','movnez','movltz','movgez'):
                x=r[a[2]];take={'moveqz':x==0,'movnez':x!=0,'movltz':signed(x)<0,'movgez':signed(x)>=0}[base]
                if take:r[a[0]]=r[a[1]]
            elif base=='l32r':r[a[0]]=self.read(a[1],4)
            elif base in ('l8ui','l16ui','l16si','l32i'):
                size={'l8ui':1,'l16ui':2,'l16si':2,'l32i':4}[base]
                value=self.read((r[a[1]]+a[2])&MASK,size)
                r[a[0]]=(value-65536 if base=='l16si' and value&32768 else value)&MASK
            elif base in ('s8i','s16i','s32i'):self.write((r[a[1]]+a[2])&MASK,{'s8i':1,'s16i':2,'s32i':4}[base],r[a[0]])
            elif base in ('call0','callx0'):
                target=a[0] if base=='call0' else r[a[0]];r[0]=nxt;nxt=target;self.branch_taken=True
            elif base=='ret':nxt=r[0];self.branch_taken=True
            elif base=='j':nxt=a[0];self.branch_taken=True
            elif base=='jx':nxt=r[a[0]];self.branch_taken=True
            elif base in ('beqz','bnez','bltz','bgez'):
                x=r[a[0]];take={'beqz':x==0,'bnez':x!=0,'bltz':signed(x)<0,'bgez':signed(x)>=0}[base]
                if take:nxt=a[-1];self.branch_taken=True
            elif base in ('beq','bne','blt','bge','bltu','bgeu','beqi','bnei','blti','bgei','bltui','bgeui'):
                x=r[a[0]];y=(a[1]&MASK) if base.endswith('i') else r[a[1]]
                kind=base.removesuffix('i')
                if kind=='beq':take=x==y
                elif kind=='bne':take=x!=y
                else:
                    sx,sy=(x,y) if kind.endswith('u') else (signed(x),signed(y))
                    take=sx<sy if kind.startswith('blt') else sx>=sy
                if take:nxt=a[-1];self.branch_taken=True
            elif base in ('bbci','bbsi','bbc','bbs'):
                bit=a[1] if base.endswith('i') else r[a[1]]&31
                # Xtensa BE bit-branch indices count from the MSB, unlike EXTUI.
                take=bool(r[a[0]]&(0x80000000>>bit))==base.startswith('bbs')
                if take:nxt=a[-1];self.branch_taken=True
            elif base in ('bany','bnone','ball','bnall'):
                x,y=r[a[0]],r[a[1]]
                take={'bany':bool(x&y),'bnone':not(x&y),'ball':x&y==y,'bnall':x&y!=y}[base]
                if take:nxt=a[-1];self.branch_taken=True
            elif base in ('nop','memw'):pass
            else:nxt=self.extension(op,a,nxt)
            self.pc=self.after_instruction(pc,nxt)
        return r[2]
