#!/usr/bin/env python3
"""Execute the compiled inert parser on host RAM only; reject every MMIO access.

This is a bounded Xtensa instruction interpreter for the parser slice, not a
USB, boot-ROM, cache, exception, or peripheral emulator. It executes the newly
assembled ELF, independently of the Python parser's implementation.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'analysis/open-firmware-probes/usb-bulk-parser-draft'
ELF = OUT/'hp1020-usb-bulk-parser-draft.elf'
MASK=0xffffffff


def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module
    spec.loader.exec_module(module)
    return module


def load_elf():
    data=ELF.read_bytes()
    if data[:6]!=b'\x7fELF\x01\x02': raise ValueError('requires BE ELF32')
    phoff=struct.unpack_from('>I',data,28)[0]
    entsize,count=struct.unpack_from('>HH',data,42)
    memory={}
    for i in range(count):
        typ,off,va,_,filesz,memsz,_,_=struct.unpack_from('>8I',data,phoff+i*entsize)
        if typ!=1: continue
        if memsz>0x100000: raise ValueError('unexpected ELF segment size')
        memory.update((va+j,b) for j,b in enumerate(data[off:off+filesz]+bytes(memsz-filesz)))
    return memory


def decode(prefix):
    text=subprocess.check_output([prefix+'-objdump','-d',str(ELF)],text=True)
    nm=subprocess.check_output([prefix+'-nm','-n',str(ELF)],text=True)
    symbols={name:int(addr,16) for addr,name in re.findall(r'^([0-9a-f]+) \w (\S+)$',nm,re.M)}
    start=symbols['hp1020_zjs_parse_transfer_loop']
    end=symbols['hp1020_usb_marker_no_match']
    memory=load_elf()
    instructions={}
    for line in text.splitlines():
        match=re.match(r'\s*([0-9a-f]{8}):\s+([0-9a-f]+)\s+(\S+)\s*(.*)',line)
        if not match: continue
        address=int(match[1],16)
        if not start<=address<end: continue
        raw=bytes.fromhex(match[2]); op=match[3]
        if raw!=bytes(memory[address+i] for i in range(len(raw))): raise ValueError('disassembly bytes differ')
        body=match[4].split('<')[0].strip()
        operands=body.split(',') if body else []
        args=[]
        for x in operands:
            x=x.strip()
            if x.startswith('a'): args.append(int(x[1:]))
            elif re.fullmatch(r'[0-9a-f]{8}',x): args.append(int(x,16))
            else: args.append(int(x,0))
        instructions[address]=(op,tuple(args),len(raw))
    ptr=symbols['hp1020_usb_marker_state_ptr']
    state=int.from_bytes(bytes(memory[ptr+i] for i in range(4)),'big')
    return memory,instructions,symbols,state


class Machine:
    def __init__(self,memory,instructions,symbols,state):
        self.memory=memory.copy()
        self.instructions=instructions
        self.symbols=symbols
        self.state=state
        self.visited=set()
        self.steps=0
        self.writes=set()

    @staticmethod
    def physical(address):
        if 0xb0000000<=address<=0xbfffffff: raise ValueError('MMIO access prohibited')
        return address&0x7fffffff

    def read(self,address,size):
        address=self.physical(address)
        try: return int.from_bytes(bytes(self.memory[address+i] for i in range(size)),'big')
        except KeyError: raise ValueError(f'unmapped read {address:#x}') from None

    def write(self,address,size,value):
        address=self.physical(address)
        if not (self.state<=address and address+size<=self.state+0x100):
            raise ValueError(f'parser write outside state {address:#x}')
        for i,b in enumerate((value&((1<<(8*size))-1)).to_bytes(size,'big')):
            self.memory[address+i]=b; self.writes.add(address+i)

    def transfer(self,payload):
        if len(payload)>1024: raise ValueError('oversized synthetic transfer')
        for i,b in enumerate(payload): self.memory[0x100216f0+i]=b
        r=[0]*16
        r[6],r[12],r[13]=len(payload),0x900216f0,0
        pc=self.symbols['hp1020_zjs_parse_transfer_loop']
        stop=self.symbols['hp1020_usb_bulk_rearm']
        for _ in range(100000):
            if pc==stop: return
            self.visited.add(pc); self.steps+=1
            if pc not in self.instructions: raise ValueError(f'PC outside parser {pc:#x}')
            op,a,size=self.instructions[pc]; nxt=pc+size
            base=op.removesuffix('.n')
            if base=='movi': r[a[0]]=a[1]&MASK
            elif base=='mov': r[a[0]]=r[a[1]]
            elif base=='addi': r[a[0]]=(r[a[1]]+a[2])&MASK
            elif base=='add': r[a[0]]=(r[a[1]]+r[a[2]])&MASK
            elif base=='or': r[a[0]]=r[a[1]]|r[a[2]]
            elif base=='and': r[a[0]]=r[a[1]]&r[a[2]]
            elif base=='slli': r[a[0]]=(r[a[1]]<<a[2])&MASK
            elif base=='srli': r[a[0]]=r[a[1]]>>a[2]
            elif base=='extui': r[a[0]]=(r[a[1]]>>a[2])&((1<<a[3])-1)
            elif base=='l32r': r[a[0]]=self.read(a[1],4)
            elif base in ('l8ui','l16ui','l32i'): r[a[0]]=self.read((r[a[1]]+a[2])&MASK,{'l8ui':1,'l16ui':2,'l32i':4}[base])
            elif base in ('s8i','s16i','s32i'): self.write((r[a[1]]+a[2])&MASK,{'s8i':1,'s16i':2,'s32i':4}[base],r[a[0]])
            elif base=='j': nxt=a[0]
            elif base in ('beq','bne','bltu','bgeu'):
                taken={'beq':r[a[0]]==r[a[1]],'bne':r[a[0]]!=r[a[1]],'bltu':r[a[0]]<r[a[1]],'bgeu':r[a[0]]>=r[a[1]]}[base]
                if taken: nxt=a[2]
            elif base in ('beqz','bnez'):
                if (r[a[0]]==0)==(base=='beqz'): nxt=a[1]
            elif base=='nop': pass
            else: raise ValueError(f'unsupported instruction {op}')
            pc=nxt
        raise ValueError('parser instruction budget exceeded')

    def snapshot(self):
        return {name:self.read(self.state+off,4) for name,off in
                [('recognized_chunks',0x68),('parser_errors',0x6c),('unknown_chunks',0x70),
                 ('state',0x74),('header_bytes',0x7c),('remaining_payload',0x80)]}


def main():
    prefix=os.environ.get('XTENSA_PREFIX','/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf')
    model=load_module('hp1020_parser_reference',ROOT/'scripts/model-hp1020-usb-bulk-parser-draft.py')
    known=model.probe_known_types(model.EXPECTED_STOCK_TYPES)
    template=decode(prefix)
    cases=model.sample_cases(known)+model.synthetic_cases()
    rows=[]; all_visited=set(); total_steps=0
    for case in cases:
        machine=Machine(*template)
        oracle=model.InertZjStreamParser(known)
        comparisons=0
        for part in case.transfers:
            machine.transfer(part); oracle.feed_descriptor(part)
            actual=machine.snapshot()
            expected={name:getattr(oracle.counters,name)&MASK for name in ('recognized_chunks','parser_errors','unknown_chunks')}
            expected.update(state={oracle.SEEK_MAGIC:0,oracle.READ_HEADER:1,oracle.SKIP_PAYLOAD:2}[oracle.state],
                            header_bytes=len(oracle._header),remaining_payload=oracle._payload_remaining)
            # Payload remainder is ignored by both parsers outside payload mode;
            # firmware may retain its previous value during partial headers.
            if actual['state']!=2: expected.pop('remaining_payload'); actual.pop('remaining_payload')
            if actual!=expected: raise AssertionError((case.name,comparisons,actual,expected))
            comparisons+=1
        rows.append({'name':case.name,'transfers_compared':comparisons,'instructions_executed':machine.steps,'status':'pass'})
        all_visited|=machine.visited; total_steps+=machine.steps
    report={'status':'pass','scope':'assembled parser slice only; no descriptor/MMIO/boot emulation',
            'elf_sha256':hashlib.sha256(ELF.read_bytes()).hexdigest(),'cases':rows,
            'total_cases':len(rows),'instructions_executed':total_steps,'unique_instructions_executed':len(all_visited),
            'decoded_parser_instructions':len(template[1]),'mmio_accesses':0,
            'comparison':'After each transfer, before host-only finalize; compare counters, parser state, partial header and active payload remainder.'}
    (OUT/'assembled-parser-check.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    lines=['# Assembled parser execution check','',f"Status: pass; {len(rows)} cases; {total_steps} instructions executed; zero MMIO accesses.",'',
           'The actual BE ELF parser instructions run in a bounded host RAM interpreter. '
           'After every transfer their counters and partial parser state are compared with the independent Python model. '
           'Unknown instructions, unmapped reads, MMIO, writes outside parser state, and runaway execution fail closed.','',
           'This starts at the parser loop with a synthetic buffer and length, and stops before USB re-arm. '
           'It does not validate the descriptor length contract, USB initialization, cache aliases, boot acceptance, '
           'or physical I/O. Host-only end-of-input finalization is deliberately excluded because a live stream has no such signal.','',
           '| Case | Transfers compared | Instructions |','|---|---:|---:|']
    lines += [f"| {x['name']} | {x['transfers_compared']} | {x['instructions_executed']} |" for x in rows]
    (OUT/'assembled-parser-check.md').write_text('\n'.join(lines)+'\n')
    print(f"assembled parser: {len(rows)} cases, {total_steps} instructions, zero MMIO")

if __name__=='__main__': main()
