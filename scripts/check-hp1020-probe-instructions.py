#!/usr/bin/env python3
"""Fail closed on reachable unknown/custom instructions in inert probe ELFs.

This audits CPU control flow, not USB behavior or MMIO authorization. Embedded
literal pools are not disassembled as executable code. Only the current
constant l32r/jx vector trampolines are accepted as indirect transfers.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import tempfile

STRAIGHT={'movi','mov','addi','add','sub','and','or','xor','slli','srli','srai',
          'extui','l32r','l32i','l16ui','l8ui','s32i','s16i','s8i','nop','memw','rsil'}
BRANCH={'beq','bne','bltu','bgeu','beqz','bnez','beqi','bnei','bltui','bgeui',
        'blti','bgei','blt','bge','bgez','bltz','bany','bnone','ball','bnall','bbci','bbsi'}


def audit(path,prefix):
    data=path.read_bytes()
    if data[:6]!=b'\x7fELF\x01\x02':raise ValueError('requires BE ELF32')
    entry,phoff=struct.unpack_from('>II',data,24)
    entsize,count=struct.unpack_from('>HH',data,42)
    segments=[]
    for i in range(count):
        typ,off,va,_,size,_,flags,_=struct.unpack_from('>8I',data,phoff+i*entsize)
        if typ==1:segments.append((va,va+size,off,flags))
    def read(address,size,execute=False):
        for begin,end,off,flags in segments:
            if begin<=address and address+size<=end and (not execute or flags&1):return data[off+address-begin:off+address-begin+size]
        raise ValueError(f'unmapped {"instruction" if execute else "literal"} {address:#x}')
    def rows(text):
        for line in text.splitlines():
            m=re.match(r'\s*([0-9a-f]{8}):\s+([0-9a-f]{4,6})\s+(\S+)\s*(.*)',line)
            if m:yield int(m[1],16),(bytes.fromhex(m[2]),m[3],m[4].split('<')[0].strip())
    initial=subprocess.check_output([prefix+'-objdump','-d',str(path)],text=True)
    decoded=dict(rows(initial))
    def decode(pc):
        if pc not in decoded:
            txt=subprocess.check_output([prefix+'-objdump','-d',f'--start-address={pc}',f'--stop-address={pc+3}',str(path)],text=True)
            decoded.update(rows(txt))
        if pc not in decoded:raise ValueError(f'cannot decode {pc:#x}')
        raw,op,body=decoded[pc]
        if read(pc,len(raw),True)!=raw:raise ValueError('instruction bytes mismatch')
        return raw,op,body
    nm=subprocess.check_output([prefix+'-nm','-n',str(path)],text=True)
    seeds={entry}
    for addr,name in re.findall(r'^([0-9a-f]+) [Tt] (\S+)$',nm,re.M):
        if name=='hp1020_window_vectors' or name.endswith('_vector'):seeds.add(int(addr,16))
    if len(seeds)!=7:raise ValueError(f'expected entry plus six vector roots: {seeds}')
    pending=list(seeds);visited={};owners={};parents={};indirect={}
    while pending:
        pc=pending.pop()
        if pc in visited:continue
        raw,op,body=decode(pc);base=op.removesuffix('.n');args=[a.strip() for a in body.split(',')]
        for address in range(pc,pc+len(raw)):
            if address in owners and owners[address]!=pc:raise ValueError('branch enters middle of an instruction')
            owners[address]=pc
        visited[pc]=dict(address=f'0x{pc:08x}',bytes=raw.hex(),mnemonic=op,operands=body)
        if base in STRAIGHT:
            if base=='rsil' and args[-1] not in ('15','0xf'):raise ValueError('unexpected interrupt-level change')
            edges=[pc+len(raw)]
        elif base=='j':edges=[int(args[-1],16)]
        elif base in BRANCH:edges=[pc+len(raw),int(args[-1],16)]
        elif base=='jx':
            prior=pc-3;pr,po,pb=decode(prior);pa=[a.strip() for a in pb.split(',')]
            if po!='l32r' or pa[0]!=args[0]:raise ValueError('indirect jump lacks constant trampoline load')
            target=int.from_bytes(read(int(pa[1],16),4),'big')
            indirect[pc]=prior;edges=[target]
        else:raise ValueError(f'forbidden or unknown reachable instruction {pc:#x}: {op} {body}')
        for target in edges:
            parents.setdefault(target,set()).add(pc);pending.append(target)
    for pc,prior in indirect.items():
        if parents.get(pc)!= {prior} or pc in seeds:raise ValueError('indirect target not proven on every incoming path')
    return dict(status='pass',elf_sha256=hashlib.sha256(data).hexdigest(),roots=[f'0x{x:08x}' for x in sorted(seeds)],
                reachable_instructions=len(visited),constant_indirect_jumps=len(indirect),unknown_instructions=0,
                instructions=[visited[x] for x in sorted(visited)],
                scope='CPU instruction/control-flow gate only; existing memory and MMIO audits remain mandatory')


def self_test(path,prefix):
    data=bytearray(path.read_bytes());entry,phoff=struct.unpack_from('>II',data,24);size,count=struct.unpack_from('>HH',data,42)
    for i in range(count):
        typ,off,va,_,n,_,_,_=struct.unpack_from('>8I',data,phoff+i*size)
        if typ==1 and va<=entry<va+n:entryoff=off+entry-va;break
    else:raise ValueError('entry not file backed')
    mutations={'custom_bpp2':bytes.fromhex('068869'),'custom_memory':bytes.fromhex('05808e'),
               'user_register':bytes.fromhex('08003f'),'indirect_unproven':bytes.fromhex('0a3000'),
               'illegal':bytes.fromhex('000000')}
    with tempfile.TemporaryDirectory(prefix='hp1020-instruction-gate-') as tmp:
        p=Path(tmp)/'mutant.elf'
        for name,raw in mutations.items():
            mutant=data.copy();mutant[entryoff:entryoff+3]=raw;p.write_bytes(mutant)
            try:audit(p,prefix)
            except ValueError:continue
            raise AssertionError(f'mutation {name} escaped instruction gate')
    return list(mutations)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('elf',type=Path)
    ap.add_argument('--prefix',default=os.environ.get('XTENSA_PREFIX','/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf'))
    ap.add_argument('--self-test',action='store_true');a=ap.parse_args()
    report=audit(a.elf,a.prefix)
    if a.self_test:report['rejected_mutations']=self_test(a.elf,a.prefix)
    out=a.elf.parent/'instruction-gate'
    out.with_suffix('.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    out.with_suffix('.md').write_text(f"# Reachable instruction gate\n\nStatus: pass. {report['reachable_instructions']} instructions from entry and six vector roots; "
        f"{report['constant_indirect_jumps']} proven constant trampolines; zero unknown/custom instructions.\n\n"
        'Literal pools are skipped by control-flow traversal. Indirect targets require the same constant load on every incoming path. '
        'Unknown instructions, user-register access and unproven indirect transfers fail closed.\n\n'+report['scope']+'\n')
    print(f"instruction gate: {report['reachable_instructions']} reachable, zero unknown; {len(report.get('rejected_mutations',[]))} rejected mutants")

if __name__=='__main__':main()
