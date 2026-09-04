#!/usr/bin/env python3
"""Audit and execute the complete stock unsigned divide/remainder helpers.

The saved mnemonic decode is regenerated with recover-hp1020-division-decode.py.
Every saved instruction is checked against the ELF. Loop execution below is
explicit: it deliberately does not use Ghidra's defective loop p-code wrapper.
"""
from __future__ import annotations
import hashlib
import json
import random
from pathlib import Path
import importlib.util

ROOT_DIR = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('division_decode', ROOT_DIR/'scripts/recover-hp1020-division-decode.py')
decoder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(decoder)
elf_range = decoder.elf_range
OUT = ROOT_DIR/'analysis/hardware-boundary'
MASK = 0xffffffff


def unsigned_divide(numerator: int, denominator: int) -> int:
    if not 0 <= numerator <= MASK or not 0 <= denominator <= MASK:
        raise ValueError('requires unsigned 32-bit operands')
    return numerator // denominator if denominator else 0


def compile_program(function):
    cursor = function['start']
    program = {}
    for row in function['instructions']:
        raw = bytes.fromhex(row['bytes'])
        if row['address'] != cursor or elf_range(cursor,len(raw)) != raw:
            raise ValueError('saved instruction bytes do not match contiguous ELF range')
        args = tuple(int(x.strip()[1:]) if x.strip().startswith('a') else int(x.strip(),0)
                     for x in row['operands'].split(',') if x.strip())
        program[cursor] = (row['mnemonic'], args, len(raw))
        cursor += len(raw)
    if cursor != function['end']:
        raise ValueError('incomplete function')
    if hashlib.sha256(elf_range(function['start'],cursor-function['start'])).hexdigest() != function['sha256']:
        raise ValueError('function hash differs')
    return program


def execute(program, entry, numerator, denominator, visited=None):
    r = [0]*16
    r[2],r[3] = numerator,denominator
    pc,shift = entry,0
    loop_begin,loop_end,loop_remaining = 0,0,0
    for step in range(300):
        if visited is not None: visited.add(pc)
        op,a,size = program[pc]
        nxt = pc+size
        if op == 'entry': pass  # local register-window view; no memory in body
        elif op.startswith('retw'): return r[2]
        elif op in ('movi','movi.n'): r[a[0]]=a[1]
        elif op == 'mov.n': r[a[0]]=r[a[1]]
        elif op == 'nsau': r[a[0]]=32-r[a[1]].bit_length()
        elif op == 'sub': r[a[0]]=(r[a[1]]-r[a[2]])&MASK
        elif op in ('addi','addi.n'): r[a[0]]=(r[a[1]]+a[2])&MASK
        elif op == 'ssl': shift=r[a[0]]&31
        elif op == 'sll': r[a[0]]=(r[a[1]]<<shift)&MASK
        elif op == 'slli': r[a[0]]=(r[a[1]]<<a[2])&MASK
        elif op == 'srli': r[a[0]]=r[a[1]]>>a[2]
        elif op == 'nop.n': pass
        elif op == 'bltui':
            if r[a[0]]<a[1]: nxt=a[2]
        elif op == 'bltu':
            if r[a[0]]<r[a[1]]: nxt=a[2]
        elif op == 'bgeu':
            if r[a[0]]>=r[a[1]]: nxt=a[2]
        elif op == 'beqz.n':
            if r[a[0]]==0: nxt=a[1]
        elif op == 'loopnez':
            loop_begin,loop_end,loop_remaining = nxt,a[1],r[a[0]]
            if not loop_remaining: nxt=loop_end
        else: raise ValueError(f'unsupported instruction {op}')
        if nxt == loop_end and loop_remaining:
            loop_remaining-=1
            if loop_remaining: nxt=loop_begin
        pc=nxt
    raise ValueError('nonterminating helper')


def build_report():
    decoded=json.loads((OUT/'division-instructions.json').read_text())
    funcs=decoded['functions']
    programs=[compile_program(f) for f in funcs]
    edge={0,1,2,3,MASK,MASK-1,8192,1200,608}
    for b in range(32):
        edge.update(x for x in ((1<<b)-1,1<<b,(1<<b)+1) if x<=MASK)
    pairs=[(n,d) for n in range(256) for d in range(256)]
    pairs.extend((n,d) for n in sorted(edge) for d in sorted(edge))
    rng=random.Random(1020)
    pairs.extend((rng.getrandbits(32),rng.getrandbits(32)) for _ in range(10000))
    coverage=[set(),set()]
    for n,d in pairs:
        expected=(unsigned_divide(n,d),n%d if d else 0)
        for i in range(2):
            actual=execute(programs[i],funcs[i]['start'],n,d,coverage[i])
            if actual!=expected[i]: raise AssertionError((funcs[i]['name'],n,d,actual,expected[i]))
    examples=[]
    for n,d in [(1,2),(7,2),(8192,1200),(8192,608),(8192,1100),(MASK,2),(MASK,MASK),(123,0)]:
        examples.append({'numerator':n,'denominator':d,'stock_quotient':execute(programs[0],funcs[0]['start'],n,d),
                         'old_ceiling_hypothesis':(n+d-1)//d if d else 0})
    checks=[{'name':'complete_ELF_matched_decode','status':'present'},
            {'name':'quotient_and_remainder_differential_cases','status':'present'},
            {'name':'all_instructions_exercised','status':'present' if all(len(c)==len(p) for c,p in zip(coverage,programs)) else 'missing'},
            {'name':'ceiling_hypothesis_refuted','status':'present' if examples[0]['stock_quotient']==0 else 'missing'}]
    return {'status':'pass' if all(x['status']=='present' for x in checks) else 'fail',
            'helper':{'address':'0x1001b668','working_name':'unsigned_divide',
                      'confirmed_behavior':{'denominator_0':'returns 0','denominator_1':'returns numerator',
                                            'denominator_ge_2':'returns floor(numerator / denominator)'}},
            'neighbor':{'address':'0x1001b6b0','working_name':'unsigned_remainder','zero_divisor_result':0},
            'conclusion':{'status':'instruction_verified','plain_english':'The previous ceiling-division hypothesis was wrong. The complete stock helper computes unsigned floor division; its neighbor computes remainder.'},
            'validation':{'input_pairs':len(pairs),'executions':2*len(pairs),'instruction_coverage':[len(c) for c in coverage],
                          'method':'ELF-matched saved mnemonic decode, independent explicit instruction interpreter, Python // and % oracle',
                          'limit':'Not exhaustive over all 2^64 inputs; no hardware execution, timing, ABI, or Ghidra loop p-code claim.'},
            'examples':examples,'checks':checks,'decoder_repair':decoded['repair']}


def main():
    report=build_report()
    (OUT/'video-helper-disassembly.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    lines=['# HP 1020 Unsigned Division and Remainder Audit','',report['conclusion']['plain_english'],'',
           'The missing instruction `6d 49 0d` at `0x1001b685` is `loopnez a4,0x1001b696`. '
           'Ghidra 12.1.1 uses the LE `at=7` field layout for its loop constructors; BE needs `at=13`. '
           'The isolated repair uses the existing endian-aware `bri8_m/bri8_n` fields. It changes no installed tool or ELF.', '',
           'The branch/shift/subtract sequence matches the unsigned division and remainder algorithms in '
           '[GCC 3.4.6](https://github.com/gcc-mirror/gcc/blob/releases/gcc-3.4.6/gcc/config/xtensa/lib1funcs.asm). '
           'This is supporting source correlation, not proof of the exact compiler version.', '',
           '## Verification','',f"- Status: `{report['status']}`",
           f"- {report['validation']['executions']} differential executions; all {sum(report['validation']['instruction_coverage'])} decoded instructions exercised.",
           '- Inputs: exhaustive 8-bit pairs, 32-bit power boundaries, seeded 32-bit random pairs, and video sizes.',
           '- Loop count and control flow are executed explicitly, independently of Ghidra loop p-code.',
           '- All decoded bytes and function hashes must match the stock ELF on every validation run.',
           '- '+report['validation']['limit'],'',
           '## Consequences','',
           '`+0xcc = floor(8192 / stride) & ~3`. A4 stride 1200 still gives four units, but the intermediate quotient is six, not seven. '
           'At stride 1100 the old rule permits eight units (8800 bytes) against an 8192-byte budget; the stock rule permits four. '
           'Raw-band unit encodings must also use floor division. This arithmetic correction does not validate hardware timing.','',
           '| Numerator | Divisor | Stock quotient | Old ceiling hypothesis |','|---:|---:|---:|---:|']
    for x in report['examples']: lines.append('| {numerator} | {denominator} | {stock_quotient} | {old_ceiling_hypothesis} |'.format(**x))
    lines+=['','## Complete decoded bodies','']
    for f in json.loads((OUT/'division-instructions.json').read_text())['functions']:
        lines+=['### '+f['name'],'','```text']
        lines += [f"{i['address']:08x}  {i['bytes']:6s}  {i['mnemonic']} {i['operands']}".rstrip() for i in f['instructions']]
        lines+=['```','']
    lines+=['## Reproduce','',
            'Regular validation requires only Python 3. To regenerate the independent mnemonic decode, install `pypcode==4.0.0` in a temporary virtual environment and run `scripts/recover-hp1020-division-decode.py` with Ghidra 12.1.1 available. Then run `scripts/model-hp1020-video-helper-disassembly.py`.','']
    (OUT/'video-helper-disassembly.md').write_text('\n'.join(lines))
    print(f"status={report['status']} executions={report['validation']['executions']}")
    return report['status']!='pass'

if __name__=='__main__': raise SystemExit(main())
