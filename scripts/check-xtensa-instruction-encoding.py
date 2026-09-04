#!/usr/bin/env python3
"""Reject LE or incompatible ISA modules even if their ELF headers say BE."""
import argparse
import os
import json
import re
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
# Values independently decoded from stock BE instructions. Explicit .n forms
# and disabled transformations prevent assembler relaxation hiding mismatches.
CASES = [
    ('entry a1, 16', '6c1002'), ('movi.n a2, 0', 'c020'),
    ('retw.n', 'd10f'), ('nsau a5, a6', '056f04'),
    ('s16i a4, a2, 0x26', '242513'), ('l16ui a4, a3, 0x22', '243111'),
    ('memw', '0c0200'), ('j .', '63fffc'),
]


def validate(prefix):
    with tempfile.TemporaryDirectory(prefix='hp1020-isa-check-') as tmp:
        d=Path(tmp)
        for i,(asm,expected) in enumerate(CASES):
            src,obj,raw=(d/f'check.{ext}' for ext in ('S','o','bin'))
            src.write_text('.text\n.begin no-transform\n'+asm+'\n.end no-transform\n')
            subprocess.run([prefix+'-as','-o',str(obj),str(src)],check=True,capture_output=True)
            header=obj.read_bytes()
            if header[:6]!=b'\x7fELF\x01\x02': raise ValueError('not ELF32 BE')
            subprocess.run([prefix+'-objcopy','-O','binary','--only-section=.text',str(obj),str(raw)],check=True,capture_output=True)
            actual=raw.read_bytes().hex()
            # .text may receive tail alignment, never ignore a wrong instruction.
            if not actual.startswith(expected):
                raise ValueError(f'{asm}: expected stock BE {expected}, got {actual}. Rebuild the matching BE ISA overlay.')
        # Reassemble both complete stock arithmetic helpers, including branches
        # and LOOPNEZ. This independently cross-checks the repaired SLEIGH decode.
        functions = json.loads((ROOT/'analysis/hardware-boundary/division-instructions.json').read_text())['functions']
        for function in functions:
            lines=['.text', '.begin no-transform']
            for row in function['instructions']:
                operands=re.sub(r'0x1001b[0-9a-f]+', lambda m: '.L'+m[0][2:], row['operands'])
                lines += [f".L{row['address']:08x}:", row['mnemonic']+' '+operands]
            lines += ['.end no-transform']
            src.write_text('\n'.join(lines)+'\n')
            subprocess.run([prefix+'-as','-o',str(obj),str(src)],check=True,capture_output=True)
            subprocess.run([prefix+'-objcopy','-O','binary','--only-section=.text',str(obj),str(raw)],check=True,capture_output=True)
            expected=bytes.fromhex(''.join(row['bytes'] for row in function['instructions']))
            if raw.read_bytes()!=expected:
                raise ValueError(function['name']+': full helper reassembly differs from stock ELF')
    print(f'BE instruction encoding: {len(CASES)} instruction fixtures and 2 complete stock helpers passed')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prefix',default=os.environ.get('XTENSA_PREFIX','/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf'))
    args=parser.parse_args()
    validate(args.prefix)

if __name__=='__main__': main()
