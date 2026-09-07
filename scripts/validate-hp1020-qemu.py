#!/usr/bin/env python3
"""Cross-check the synthetic C target with independently implemented QEMU ISA."""
import hashlib
import importlib.util
import json
import os
import random
from pathlib import Path
import struct
from hp1020_qemu_ram import QemuRAM
from hp1020_xtensa_call0 import Program, signed
from hp1020_xtensa_stock import StockMachine

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'analysis/open-firmware-model/semantic-target'


def main():
    spec = importlib.util.spec_from_file_location('qemu_target_cases', ROOT / 'scripts/validate-hp1020-semantic-target.py')
    target = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(target)
    cases = []
    with QemuRAM() as qemu:
        def observe(name, data, fragment, program, expected, returned):
            entry = qemu.load(program.path)
            qemu.put(program.symbols['hp1020_test_input'], data)
            result = qemu.call0(entry, [len(data), fragment])
            actual = list(struct.unpack('>32I', qemu.read(program.symbols['hp1020_test_output'], 128)))
            assert result == returned and actual == expected, (name, fragment, result, actual, expected)
            cases.append(dict(case=name, fragment=fragment, status='pass'))
        target.main(observer=observe)
        spec = importlib.util.spec_from_file_location('qemu_stock_cases', ROOT / 'scripts/validate-hp1020-stock-execution.py')
        stock = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(stock)
        libc_counts = {}
        qemu.load(ROOT / 'analysis/sihp1020.elf')
        def libc(name, entry, args, initial, expected, returned):
            qemu.put(stock.RAM, initial)
            actual = qemu.call8(entry, args)
            assert actual == returned and qemu.read(stock.RAM, len(expected)) == expected, (name, args, actual, returned)
            libc_counts[name] = libc_counts.get(name, 0) + 1
        stock.main(libc_observer=libc)
        program = Program(ROOT / 'analysis/sihp1020.elf', os.environ.get('XTENSA_PREFIX','/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf'))
        edge = (0,1,2,3,4,7,31,32,255,256,65535,65536,0x7fffffff,0x80000000,0x80000001,0xffffffff)
        pairs = [(x,y) for x in edge for y in edge]
        rng = random.Random(102006)
        pairs += [(rng.getrandbits(32),rng.getrandbits(32)) for _ in range(512)]
        arithmetic = {}
        arithmetic_visited = set()
        for name,entry,end in (('signed_divide',0x1001b5b8,0x1001b618),('signed_remainder',0x1001b618,0x1001b668),
                               ('unsigned_divide',0x1001b668,0x1001b6b0),('unsigned_remainder',0x1001b6b0,0x1001b6ec)):
            for x,y in pairs:
                a,b = (signed(x),signed(y)) if name.startswith('signed') else (x,y)
                # Stock software helpers explicitly return zero for divisor zero.
                # Signed quotient truncates toward zero, including wrapped INT_MIN/-1.
                if not b:
                    expected = 0
                else:
                    quotient = abs(a)//abs(b) * (-1 if (a<0)!=(b<0) else 1)
                    expected = (a-quotient*b if name.endswith('remainder') else quotient) & 0xffffffff
                model = StockMachine(program,entry,[(entry,end)])
                assert model.run([x,y]) == expected, (name,x,y,expected)
                assert qemu.call8(entry,[x,y]) == expected, (name,x,y,expected)
                arithmetic_visited.update(model.visited)
            arithmetic[name] = len(pairs)
        report = dict(arithmetic_cases=arithmetic,arithmetic_distinct_instructions=len(arithmetic_visited),libc_cases=libc_counts, stock_elf_sha256=hashlib.sha256((ROOT / 'analysis/sihp1020.elf').read_bytes()).hexdigest(), status='pass', engine=qemu.version, cpu='test_kc705_be', machine='sim, 1 GiB RAM',
                      total_cases=len(cases)+sum(libc_counts.values())+sum(arithmetic.values()), target_cases=len(cases), cases=cases,
                      comparison='Compiled C target results agree across QEMU, our instruction interpreter, ASan/UBSan native C and fixture expectations. Stock libc agrees with complete bytearray oracles; four stock division/remainder helpers agree with independent Python arithmetic, including zero-divisor return-zero and signed-overflow wrapping.',
                      scope='Original compiled BE/call0 target ELF bytes loaded through a private Unix GDB socket. Original stock memset/memcpy/memmove/strlen also run through actual windowed CALL8/ENTRY/RETW and hardware loops, matching complete 1024-byte RAM oracles. No QEMU instruction decoding is delegated to our interpreter. No printer or host USB backend exists.',
                      limits='The QEMU CPU is not the printer CPU configuration. This does not test firmware boot, register-window spills, custom raster instructions, caches, interrupts, transport or physical printing.',
                      elf_sha256=hashlib.sha256((OUT / 'target-check.elf').read_bytes()).hexdigest(),
                      source_sha256={name:hashlib.sha256((ROOT / 'scripts' / name).read_bytes()).hexdigest() for name in ('hp1020_qemu_ram.py', 'validate-hp1020-qemu.py', 'validate-hp1020-semantic-target.py', 'validate-hp1020-stock-execution.py')},
                      register_map_source='https://github.com/qemu/qemu/blob/v11.1.1/target/xtensa/core-test_kc705_be/gdb-config.c.inc')
    (OUT / 'qemu.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    (OUT / 'qemu.md').write_text('# Independent QEMU cross-check\n\n'
        + f"Status: pass. {report['total_cases']} cases using {report['engine']}.\n\n"
        + report['comparison'] + '\n\n' + report['scope'] + '\n\n' + report['limits'] + '\n')
    print(f'QEMU: {report["total_cases"]} cases agree with interpreter and independent oracles')


if __name__ == '__main__':
    main()
