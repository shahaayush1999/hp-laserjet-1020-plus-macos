#!/usr/bin/env python3
"""Audit the stock ELF's compiler annotations and unsupported instruction sites."""
import collections
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
from hp1020_xtensa_call0 import Program
from hp1020_xtensa_properties import properties, section_bytes

ROOT = Path(__file__).resolve().parents[1]
ELF = ROOT / 'analysis/sihp1020.elf'
OUT = ROOT / 'analysis/hardware-boundary/instruction-properties'


def main():
    data = ELF.read_bytes()
    sections, tables = properties(data)
    prefix = os.environ.get('XTENSA_PREFIX', '/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf')
    program = Program(ELF, prefix)
    rows = program.instructions
    direct = []
    literals = []
    unannotated_literals = []
    unknown = []
    user = []
    for pc, (op, args, raw) in sorted(rows.items()):
        if (op.startswith(('b', 'call', 'loop')) or op == 'j') and not op.startswith(('break', 'callx')):
            target = args[-1]
            assert target in rows, (hex(pc), op, hex(target))
            direct.append((pc, target))
        if op == 'l32r':
            section_bytes(data, sections, args[1], 4)
            assert not any(a <= args[1] < a+n for a,n in tables['.xt.insn'])
            if not any(a <= args[1] and args[1] + 4 <= a + n for a, n in tables['.xt.lit']):
                unannotated_literals.append(dict(instruction=f'0x{pc:08x}', literal=f'0x{args[1]:08x}'))
            literals.append((pc,args[1]))
        if op == 'excw':
            record = dict(address=f'0x{pc:08x}', bytes=raw.hex())
            if raw[0] >> 4 == 0 and raw[2] == 0x3f:
                record.update(user_register=raw[1], source_register=raw[0] & 15)
                user.append(record)
            else:
                record['encoding_group'] = f'0x{raw[2]:02x}'
                unknown.append(record)
    assert all(0x10015518 <= int(x['address'],16) < 0x10015bc5 for x in unknown+user)
    linear = dict(Program.parse(subprocess.check_output([prefix+'-objdump','-d',str(ELF)],text=True)))
    missing = sorted(set(rows) - set(linear))
    different = [p for p in rows.keys() & linear.keys() if rows[p] != linear[p]]
    # The newly noticed routine has no direct call/branch or literal pointer in
    # any file-backed allocated section. Computed/runtime references remain open.
    extra_start, extra_end = 0x10015518, 0x10015645
    refs = []
    needle = struct.pack('>I', extra_start)
    for name,s in sections.items():
        if s['flags'] & 2 and s['type'] != 8:
            blob = data[s['offset']:s['offset'] + s['size']]
            pos = blob.find(needle)
            while pos >= 0:
                refs.append(dict(section=name,address=f"0x{s['address']+pos:08x}"))
                pos = blob.find(needle,pos+1)
    extra_direct = [(a,b) for a,b in direct if extra_start <= b < extra_end and not extra_start <= a < extra_end]
    assert not refs and not extra_direct
    # Corrupt the actual annotation table, not a second copy of parsing logic.
    rejected = []
    table = sections['.xt.insn']['offset']
    lit = 0x10006904  # A literal inside executable .text, exercising cross-table overlap.
    for name,address,size in [('zero_length',0x10006bb0,0),('outside_code',0xb0000000,3),
                              ('overlap',tables['.xt.insn'][0][0],tables['.xt.insn'][0][1]),
                              ('literal_as_code',lit,4),('wrapping',0xfffffffe,8)]:
        changed = bytearray(data)
        struct.pack_into('>II',changed,table,address,size)
        try: properties(changed)
        except ValueError: rejected.append(name)
        else: raise AssertionError(name)
    for name,pc in [('instruction_interior',extra_start+1),('literal',0x10006904),('padding',0x1001550d)]:
        try: program.instruction(pc)
        except ValueError: rejected.append(name)
        else: raise AssertionError(name)
    report = dict(status='pass', stock_sha256=hashlib.sha256(data).hexdigest(),
        scope='Static stock-byte/annotation agreement; not proof of runtime reachability or hardware ISA semantics.',
        format_evidence='Pinned binutils bfd/elf32-xtensa.c: xtensa_read_table_entries and xtensa_get_property_predef_flags; old tables use address,size pairs with implicit flags.',
        code_regions=[dict(address=f'0x{a:08x}',size=n,sha256=hashlib.sha256(section_bytes(data,sections,a,n)).hexdigest()) for a,n in tables['.xt.insn']],
        literal_regions=[dict(address=f'0x{a:08x}',size=n) for a,n in tables['.xt.lit']],
        instruction_count=len(rows),code_bytes=sum(n for _,n in tables['.xt.insn']),
        direct_control_transfers_checked=len(direct),literal_loads_checked=len(literals), unannotated_literal_loads=unannotated_literals,
        missing_from_linear_decode=[f'0x{x:08x}' for x in missing], different_from_linear_decode=[f'0x{x:08x}' for x in different],
        decoder_unrecognized=unknown,user_register_writes=user,
        unrecognized_groups=dict(collections.Counter(x['encoding_group'] for x in unknown)),
        additional_routine=dict(start=f'0x{extra_start:08x}',end=f'0x{extra_end:08x}',
            allocated_pointer_references=refs,external_direct_references=extra_direct,
            caveat='No static direct/pointer reference found; computed references and device reachability are not disproven.'),
        rejected_mutations=rejected,
        limitations=['Annotations exclude padding/data; they are not a function map or a reachability proof.',
                     'Generic binutils names do not establish exact core support or side effects. Unrecognized encodings remain forbidden in execution.',
                     'Code outside annotations is not proven impossible to execute; the stock host interpreter conservatively refuses it.',
                     'The additional routine contains groups 0x68/0x66/0x65/0x64 absent from the three selected callbacks; their semantics remain unknown.'])
    OUT.with_suffix('.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    OUT.with_suffix('.md').write_text('\n'.join([
        '# Stock instruction annotations','',report['scope'],'',
        f"The ELF has {len(tables['.xt.insn'])} nonoverlapping instruction regions ({report['code_bytes']} bytes) and {len(tables['.xt.lit'])} literal regions. Each region decodes contiguously and matches the original bytes.",
        f"All {len(direct)} decoded direct control transfers land on annotated instruction starts. All {len(literals)} literal loads resolve to file-backed data outside instruction regions; {len(unannotated_literals)} loads use literal pools omitted from .xt.lit (startup/scheduler code). The literal table is therefore incomplete.",'',
        f"Decoding each region recovers {len(rows)} instructions, including {len(missing)} starts missed by whole-section linear decoding ({len(different)} differing decodes at shared starts). Stock execution now requires these boundaries and refuses literal, padding and instruction-interior PCs.",'',
        f"The generic decoder cannot name {len(unknown)} encodings beyond {len(user)} identifiable user-register writes. Every such site lies in 0x10015518..0x10015bc5; this is a static census, not proof they all execute. Groups: {report['unrecognized_groups']}.",'',
        'The previously unaudited routine at 0x10015518 has four additional groups (68/66/65/64), writes user registers, and transforms row words. A scan of all annotated direct targets and every byte offset in allocated file-backed sections finds no reference to its entry. Do not add it to the active printing path without evidence; computed references remain possible. The three selected callbacks retain their existing report.','',
        f"Malformed annotation and forbidden-PC checks reject {len(rejected)} mutations.",'',
        'Format provenance: '+report['format_evidence'],'','## Limits','',
        *['- '+x for x in report['limitations']],''
    ]))
    print(f'instruction properties: {len(rows)} instructions, {len(direct)} direct targets, {len(unknown)} unresolved encodings, {len(rejected)} negative checks')

if __name__ == '__main__':
    main()
