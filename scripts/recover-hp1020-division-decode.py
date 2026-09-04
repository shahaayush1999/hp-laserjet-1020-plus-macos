#!/usr/bin/env python3
"""Reproduce the isolated Ghidra BE loop decoder repair (requires pypcode 4).

Never changes the installed Ghidra, firmware ELF, or printer. This is a
mnemonic decoder audit, not an endorsement of Ghidra's loop p-code semantics.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def elf_range(address, size):
    data = (ROOT / 'analysis/sihp1020.elf').read_bytes()
    phoff = struct.unpack_from('>I', data, 28)[0]
    entsize, count = struct.unpack_from('>HH', data, 42)
    for i in range(count):
        typ, off, va, _, length, _, _, _ = struct.unpack_from('>8I', data, phoff+i*entsize)
        if typ == 1 and va <= address and address+size <= va+length:
            return data[off+address-va:off+address-va+size]
    raise ValueError('range not file backed')


def main():
    import pypcode
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ghidra-home', type=Path, default=Path('/opt/homebrew/Cellar/ghidra/12.1.1/libexec'))
    args = parser.parse_args()
    original = args.ghidra_home / 'Ghidra/Processors/Xtensa/data/languages'
    with tempfile.TemporaryDirectory(prefix='hp1020-division-sleigh-') as tmp:
        langdir = Path(tmp)/'languages'
        shutil.copytree(original, langdir)
        source = langdir/'xtensaInstructions.sinc'
        before = source.read_text()
        old = 'at = 0b0111 & op0 ='
        new = 'bri8_m = 0b01 & bri8_n = 0b11 & op0 ='
        loop_lines = [line for line in before.splitlines() if line.startswith(':loop')]
        if len(loop_lines) != 3 or not all(old in line for line in loop_lines):
            raise ValueError('expected three loop constructors; inspect this Ghidra version')
        after = before
        for line in loop_lines:
            after = after.replace(line, line.replace(old,new))
        source.write_text(after)
        compiler = Path(pypcode.__file__).parent/'bin/sleigh'
        subprocess.run([str(compiler), str(langdir/'xtensa_be.slaspec')], check=True)
        element = next(x for x in ET.parse(langdir/'xtensa.ldefs').getroot() if x.get('id')=='Xtensa:BE:32:default')
        context = pypcode.Context(pypcode.ArchLanguage(str(langdir), element))
        functions = []
        for name, start, end in [('unsigned_divide',0x1001b668,0x1001b6b0), ('unsigned_remainder',0x1001b6b0,0x1001b6ec)]:
            raw = elf_range(start,end-start)
            rows=[]
            for ins in context.disassemble(raw, base_address=start).instructions:
                addr=ins.addr.offset
                rows.append({'address':addr,'bytes':raw[addr-start:addr-start+ins.length].hex(), 'mnemonic':ins.mnem, 'operands':ins.body})
            if sum(len(bytes.fromhex(row['bytes'])) for row in rows) != len(raw):
                raise ValueError('incomplete decode')
            functions.append({'name':name,'start':start,'end':end,'sha256':hashlib.sha256(raw).hexdigest(),'instructions':rows})
        report={'scope':'offline mnemonic decode only; p-code loops not used', 'language':element.get('id'),
                'pypcode_version':pypcode.__version__, 'ghidra_version':'12.1.1',
                'instruction_source_sha256':hashlib.sha256(before.encode()).hexdigest(),
                'repair':{'old':old,'new':new,'constructors_changed':3,
                          'reason':'BRI8 m/n field groups swap position in BE; literal at=7 encodes LE field order. BE at must be 13.'},
                'functions':functions}
        out=ROOT/'analysis/hardware-boundary/division-instructions.json'
        out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
        print(out)

if __name__=='__main__': main()
