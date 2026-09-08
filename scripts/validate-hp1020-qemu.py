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
from hp1020_qemu_stock_parser import QemuParser
from hp1020_qemu_windows import validate_windows
from hp1020_qemu_lifecycle import QemuLifecycle
from hp1020_stock_lifecycle_harness import LifecycleHarness

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
        parser_cases = []
        parser_vectors = {}
        def parser(name, data, fill, expected):
            actual = QemuParser(expected.program,data,qemu,fill=fill)
            assert actual.run() == 0
            assert actual.messages == expected.messages, (name,'QEMU parser messages differ')
            assert actual.input_pos == expected.input_pos, (name,'QEMU input consumption differs')
            assert actual.allocations == expected.allocations, (name,'QEMU allocation ownership differs')
            for address,count in actual.vector_entries.items():
                parser_vectors[address] = parser_vectors.get(address,0)+count
            parser_cases.append(dict(name=name,fill=fill,instructions=actual.steps,status='pass'))
        stock.main(libc_observer=libc,parser_observer=parser)
        program = Program(ROOT / 'analysis/sihp1020.elf', os.environ.get('XTENSA_PREFIX','/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf'))
        windows = validate_windows(qemu,program,program.prefix)
        base = stock.chunks((ROOT/'analysis/samples/generated/matrix-a4_default.zjs').read_bytes())[0]
        empty = stock.stream(base[:1]+base[-1:])
        copies = list(base)
        k,p,n,r = copies[1]
        p = b''.join(p[i:i+8]+(3).to_bytes(4,'big') if p[i+4:i+6]==b'\0\4' else p[i:i+12] for i in range(0,len(p),12))
        copies[1] = (k,p,n,r)
        k,p,_,_ = base[3]
        bids = [(k,p[len(p)*i//7:len(p)*(i+1)//7],0,0) for i in range(7)]
        streams = {'single':stock.stream(base),'three_pages':stock.stream(base[:1]+base[1:6]*3+base[-1:]),
                   'two_documents':stock.stream(base)*2,'three_copies':stock.stream(copies),
                   'seven_rasters':stock.stream(base[:3]+bids+base[4:]),'empty':empty}
        receiver_words = {}
        for kind,begin,end in ((46,0x100105de,0x10010657),(47,0x10010657,0x100106ab)):
            offsets = {args[2] for pc,(op,args,_) in program.instructions.items()
                       if begin<=pc<end and op in ('l32i','l32i.n') and args[1]==1}
            assert offsets == ({8,12} if kind==46 else {12}), (kind,offsets)
            receiver_words[str(kind)] = sorted(offset//4 for offset in offsets)
        lifecycle_cases = []
        def notices(items):
            # Stock receiver uses words 0/2/3 for message 46, and 0/3 plus
            # pointed payload for 47. Other queue words retain stack bytes.
            return [(x['words'][0],x['words'][2] if x['words'][0]==46 else None,
                     x['words'][3],x.get('payload')) for x in items]
        for name,data in streams.items():
            for fill in (0,0xcc):
                expected = LifecycleHarness(program,data,fill=fill,credits=2).replay()
                actual = QemuLifecycle(program,data,fill=fill,credits=2).replay_qemu(qemu)
                assert actual.allocations == expected.allocations, (name,'lifecycle allocation mismatch')
                assert actual.scheduled == expected.scheduled and actual.completed == expected.completed
                assert notices(actual.notifications) == notices(expected.notifications), (name,'lifecycle notices mismatch')
                for begin,end in program.write_ranges:
                    assert actual.bytes_at(begin,end-begin) == expected.bytes_at(begin,end-begin), (name,'stock global RAM mismatch',hex(begin))
                lifecycle_cases.append(dict(name=name,fill=fill,instructions=actual.qemu_steps,
                                            vector_entries=actual.vector_entries,status='pass'))
        witness = QemuLifecycle(program,stock.stream(base)+empty,credits=1)
        try:
            witness.replay_qemu(qemu)
        except ValueError as error:
            assert witness.pc == 0x1000e7dd and str(error) == 'unmapped RAM 0x4c+4',(hex(witness.pc),str(error))
            lifecycle_witness = dict(status='reproduced',pc=hex(witness.pc),error=str(error))
        else:
            raise AssertionError('independent engine did not reproduce delayed-empty-document finding')
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
        report = dict(notification_receiver_word_indices=receiver_words,windows=windows,lifecycle_cases=lifecycle_cases,lifecycle_counterexample=lifecycle_witness,parser_cases=parser_cases,parser_vector_entries=parser_vectors,arithmetic_cases=arithmetic,arithmetic_distinct_instructions=len(arithmetic_visited),libc_cases=libc_counts, stock_elf_sha256=hashlib.sha256((ROOT / 'analysis/sihp1020.elf').read_bytes()).hexdigest(), status='pass', engine=qemu.version, cpu='test_kc705_be', machine='sim, 1 GiB RAM',
                      total_cases=len(cases)+sum(libc_counts.values())+sum(arithmetic.values())+len(parser_cases)+windows["total_cases"]+len(lifecycle_cases), target_cases=len(cases), cases=cases,
                      comparison='Compiled C target results agree across QEMU, our instruction interpreter, ASan/UBSan native C and fixture expectations. Original parser messages, input consumption and allocation ownership also match, using actual stock window spill/fill handlers under QEMU. JobMgr completion and cleanup also match allocation ownership, scheduled work, defined notification fields and all stock writable global RAM. QEMU independently reproduces the delayed-empty-document failure. Host services intentionally share the existing boundary fixture. Stock libc agrees with complete bytearray oracles; four stock division/remainder helpers agree with independent Python arithmetic, including zero-divisor return-zero and signed-overflow wrapping.',
                      scope='Original compiled BE/call0 target ELF bytes loaded through a private Unix GDB socket. Original stock memset/memcpy/memmove/strlen also run through actual windowed CALL8/ENTRY/RETW and hardware loops, matching complete 1024-byte RAM oracles. No QEMU instruction decoding is delegated to our interpreter. No printer or host USB backend exists.',
                      limits='The QEMU CPU is not the printer CPU configuration. This does not test firmware boot, arbitrary window/interrupt state, custom raster instructions, caches, interrupts, transport or physical printing.',
                      elf_sha256=hashlib.sha256((OUT / 'target-check.elf').read_bytes()).hexdigest(),
                      source_sha256={name:hashlib.sha256((ROOT / 'scripts' / name).read_bytes()).hexdigest() for name in ('hp1020_qemu_ram.py', 'hp1020_qemu_stock_parser.py', 'hp1020_qemu_windows.py', 'hp1020_qemu_lifecycle.py', 'hp1020_stock_lifecycle_harness.py', 'hp1020_stock_jobmgr_harness.py', 'hp1020_stock_parser_harness.py', 'validate-hp1020-qemu.py', 'validate-hp1020-semantic-target.py', 'validate-hp1020-stock-execution.py')},
                      register_map_source='https://github.com/qemu/qemu/blob/v11.1.1/target/xtensa/core-test_kc705_be/gdb-config.c.inc')
    (OUT / 'qemu.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    (OUT / 'qemu.md').write_text('# Independent QEMU cross-check\n\n'
        + f"Status: pass. {report['total_cases']} cases using {report['engine']}.\n\n"
        + report['comparison'] + '\n\n' + windows['scope'] + '\n\n' + windows['limits'] + '\n\n' + report['scope'] + '\n\n' + report['limits'] + '\n')
    print(f'QEMU: {report["total_cases"]} cases agree with interpreter and independent oracles')


if __name__ == '__main__':
    main()
