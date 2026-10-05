"""UNEXECUTED draft: audit the bounded new entry-to-C RAM ELF, never a .dl.

The only external command is the caller-selected corrected Xtensa objdump.
Nothing in this module loads QEMU, executes target code, contacts a device, or
modifies an artifact. The caller must preserve the ELF, build inputs, .su files,
returned audit and program.entry_audit_disassembly before any target execution.
Static ISA admission does not establish dynamic memory/control destinations;
the entry runner must enforce the returned exact permissions on every access.
"""
from __future__ import annotations

from collections import Counter
import hashlib
from pathlib import Path
import struct
import subprocess


STOCK_SHA256 = '2111560068db47ceca21fa550db4c7c34f5595b5a5d137ae4a19631e40e3601d'
ENTRY = 0x100167a8
MAIN = (0x10003000, 0x100351e0)
WRITE_RANGES = ((0x1000e000, 0x100114c8), (0x10012000, 0x10014000),
                (0x10014040, 0x10014440), (0x10016800, 0x10032810))
DATA_PATTERN = bytes.fromhex('31527394b5d6f718395a7b9cbddeff20') * 16
STACK_USAGE_NAMES = {
    'hp1020_entry_workload', 'hp1020_entry_layout', 'hp1020_usb_receive', 'hp1020_usb_document',
    'hp1020_image', 'hp1020_image_page', 'hp1020_image_stream',
    'hp1020_image_ring', 'hp1020_image_output', 'hp1020_image_pump', 'hp1020_semantic',
    'hp1020_page_plan', 'target-memory', 'memory', 'jbig85', 'jbig_ar',
}
ORDINARY = set('''add add.n addi addi.n addmi addx2 addx4 addx8 and
bbci bbsi beq beqi beqz beqz.n bge bgei bgeu bgeui bgez blt blti bltu bltui
bltz bne bnei bnez bnez.n bnone bany ball bnall call0 callx0 extui j jx
l16si l16ui l32i l32i.n l32r l8ui mov.n moveqz movgez movi movi.n movltz
movnez mull neg nsau nop nop.n or ret ret.n s16i s32i s32i.n s8i sll slli
sra srai srl srli ssl ssr sub subx2 subx4 subx8 xor src memw'''.split())
DIRECT_BRANCHES = set('''bbci bbsi beq beqi beqz beqz.n bge bgei bgeu bgeui
bgez blt blti bltu bltui bltz bne bnei bnez bnez.n bnone bany ball bnall'''.split())
# Exact proposed a2 encodings. Their standard opcode/register fields are
# independently anchored below to original annotated bytes, not to a target run.
PREFIX_RAW = {
    'rsil': '02f600', 'wsr.intenable': '02e431', 'wsr.lcount': '020231',
    'wsr.lbeg': '020031', 'wsr.lend': '020131', 'isync': '000200',
    'wsr.ps': '02e631', 'rsync': '010200', 'wsr.windowbase': '024831',
    'wsr.windowstart': '024931', 'ssai': '000404',
}
# name: (address, size, section type, exact SHF flags)
FIXED_SECTIONS = {
    '.WindowVectors.text': (0x10000000, 0x180, 1, 6),
    '.KernelExceptionVector.literal': (0x10000180, 4, 1, 2),
    '.KernelExceptionVector.text': (0x10000200, 0x1c, 1, 6),
    '.UserExceptionVector.literal': (0x1000021c, 4, 1, 2),
    '.UserExceptionVector.text': (0x10000220, 0x1c, 1, 6),
    '.DoubleExceptionVector.text': (0x10000270, 0xe0, 1, 6),
    '.sys_interface_table': (0x10000370, 0x12c, 1, 2),
    '.entry_data': (0x1000d020, 0x100, 1, 3),
    '.entry_state': (0x1000e000, 0x34c8, 8, 3),
    '.entry_stack': (0x10012000, 0x2000, 8, 3),
    '.entry_mailbox': (0x10014040, 0x400, 8, 3),
    '.entry_island': (0x10016780, 0x60, 1, 6),
    '.entry_memory': (0x10016800, 0x1c010, 8, 3),
    '.ResetVector.text': (0x10100020, 0x2e0, 1, 6),
    '.DebugExceptionVector.literal': (0x10100300, 4, 1, 2),
    '.DebugExceptionVector.text': (0x10100320, 0xc, 1, 6),
}
GUARDS = {
    'data_guard_lo': (0x1000d000, 0x1000d020),
    'data_guard_hi': (0x1000d120, 0x1000d140),
    'state_guard_lo': (0x1000dfe0, 0x1000e000),
    'state_guard_hi': (0x100114c8, 0x100114f0),
    'stack_guard_lo': (0x10011fe0, 0x10012000),
    'stack_guard_hi': (0x10014000, 0x10014020),
    'mailbox_guard_lo': (0x10014020, 0x10014040),
    'mailbox_guard_hi': (0x10014440, 0x10014460),
    'memory_guard_lo': (0x100167e0, 0x10016800),
    'memory_guard_hi': (0x10032810, 0x10032830),
}


def require(condition, *detail):
    if not condition:
        raise ValueError(('entry ELF audit',) + detail)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def inside(a, n, start, end):
    return n > 0 and start <= a < a + n <= end


def merge(ranges):
    """Merge adjacent half-open ranges, rejecting overlaps."""
    out = []
    for a, b in sorted(ranges):
        require(0 <= a < b <= 0x100000000, 'bad range', a, b)
        require(not out or out[-1][1] <= a, 'overlapping ranges', a, b)
        if out and out[-1][1] == a:
            out[-1] = (out[-1][0], b)
        else:
            out.append((a, b))
    return out


def cstring(raw, offset):
    require(0 <= offset < len(raw), 'string offset', offset)
    end = raw.find(b'\0', offset)
    require(end >= 0, 'unterminated ELF string', offset)
    return raw[offset:end].decode('ascii')


def read_elf(data):
    require(len(data) >= 52 and data[:7] == b'\x7fELF\x01\x02\x01',
            'expected ELF32 big-endian version 1')
    h = struct.unpack_from('>HHIIIIIHHHHHH', data, 16)
    typ, machine, version, entry, phoff, shoff, flags, ehsize, phsize, phnum, shsize, shnum, shstr = h
    require(typ == 2 and machine == 94 and version == 1, 'ELF target/type', h[:3])
    require(flags & ~0x300 == 0, 'unrecognized Xtensa ELF flags', flags)
    require(ehsize == 52 and phsize == 32 and shsize == 40, 'ELF header sizes')
    require(0 < phnum < 128 and 0 < shnum < 512 and shstr < shnum, 'ELF table counts')
    require(phoff >= 52 and phoff + phsize * phnum <= len(data), 'program table bounds')
    require(shoff >= 52 and shoff + shsize * shnum <= len(data), 'section table bounds')
    headers = [struct.unpack_from('>10I', data, shoff + i * shsize) for i in range(shnum)]
    ns = headers[shstr]
    require(ns[1] == 3 and ns[4] + ns[5] <= len(data), 'section-name table')
    strings = data[ns[4]:ns[4] + ns[5]]
    sections = {}
    by_index = []
    for i, s in enumerate(headers):
        name = cstring(strings, s[0])
        require(name not in sections, 'duplicate section name', name)
        sec = dict(index=i, name=name, type=s[1], flags=s[2], address=s[3],
                   offset=s[4], size=s[5], link=s[6], info=s[7], align=s[8], entsize=s[9])
        require(s[3] + s[5] <= 0x100000000, 'section wraps', name)
        require(s[8] == 0 or s[8] & (s[8] - 1) == 0, 'section alignment', name)
        require(s[1] == 8 or s[4] + s[5] <= len(data), 'section file bounds', name)
        require(not s[2] & 0x400, 'TLS is outside profile', name)
        require(s[1] not in (4, 6, 9, 11) or s[5] == 0,
                'relocation/dynamic section is outside linked closure', name)
        sections[name] = sec
        by_index.append(sec)
    require(headers[0] == (0,) * 10, 'non-null section zero')
    loads = []
    for i in range(phnum):
        p = struct.unpack_from('>8I', data, phoff + i * phsize)
        typ, off, va, pa, filesz, memsz, pflags, align = p
        require(typ == 1, 'unexpected program header', i, typ)
        require(va == pa and 0 < memsz <= 0x40000 and filesz <= memsz,
                'load extent/address', i, p)
        require(off + filesz <= len(data) and va + memsz <= 0x100000000,
                'load wraps/outside file', i)
        require(align in (0, 1) or (align & (align - 1) == 0 and va % align == off % align),
                'load alignment', i, align)
        loads.append(dict(address=va, physical=pa, offset=off, filesz=filesz,
                          memsz=memsz, flags=pflags, align=align))
    loads.sort(key=lambda p: p['address'])
    merge([(p['address'], p['address'] + p['memsz']) for p in loads])
    tables = [s for s in by_index if s['type'] == 2 and s['size']]
    require(len(tables) == 1, 'one full static symbol table required')
    tab = tables[0]
    require(tab['entsize'] == 16 and tab['size'] % 16 == 0 and tab['link'] < shnum,
            'symbol-table shape')
    st = by_index[tab['link']]
    require(st['type'] == 3, 'symbol string table')
    names = data[st['offset']:st['offset'] + st['size']]
    symbols, records = {}, []
    for off in range(tab['offset'], tab['offset'] + tab['size'], 16):
        name, value, size, info, other, index = struct.unpack_from('>IIIBBH', data, off)
        name = cstring(names, name)
        if not name:
            continue
        require(index not in (0, 0xfff2), 'undefined/common symbol', name)
        require(index < shnum or index == 0xfff1, 'unsupported symbol section', name, index)
        record = dict(name=name, address=value, size=size, type=info & 15,
                      binding=info >> 4, visibility=other, section=index)
        records.append(record)
        # Local names may repeat (e.g. file-scope helpers from different C
        # units); only unambiguous names become Program lookup symbols.
        if name not in symbols:
            symbols[name] = value
        elif symbols[name] != value:
            require(info >> 4 == 0, 'conflicting global symbol', name)
            symbols[name] = None
    symbols = {k: v for k, v in symbols.items() if v is not None}
    return dict(entry=entry, flags=flags, sections=sections, indexed=by_index,
                loads=loads, symbols=symbols, symbol_records=records)


def file_bytes(data, sections, address, size):
    matches = [s for s in sections.values() if s['flags'] & 2 and s['type'] != 8
               and inside(address, size, s['address'], s['address'] + s['size'])]
    require(len(matches) == 1, 'no unique file-backed allocation', address, size)
    s = matches[0]
    off = s['offset'] + address - s['address']
    return data[off:off + size]


def check_layout(elf, data):
    sections, symbols = elf['sections'], elf['symbols']
    allocated = {n: s for n, s in sections.items() if s['flags'] & 2 and s['size']}
    require(set(allocated) == set(FIXED_SECTIONS) | {'.text', '.rodata'},
            'unexpected allocated sections', sorted(allocated))
    for name, expected in FIXED_SECTIONS.items():
        s = allocated[name]
        require(tuple(s[k] for k in ('address', 'size', 'type', 'flags')) == expected,
                'fixed allocation differs', name, s, expected)
    text, rodata = allocated['.text'], allocated['.rodata']
    require((text['address'], text['type'], text['flags']) == (0x10007000, 1, 6), 'text profile')
    require(text['size'] > 28 and (rodata['type'], rodata['flags']) == (1, 2), 'code/data shape')
    require(rodata['address'] == ((text['address'] + text['size'] + 3) & ~3),
            'unexpected text/rodata gap')
    end = rodata['address'] + rodata['size']
    require(end <= 0x1000d000, 'code/input spills into data guard', end)
    merge([(s['address'], s['address'] + s['size']) for s in allocated.values()])
    expected_loads = [
        (0x10000000, 0x184, 0x184, 5), (0x10000200, 0x3c, 0x3c, 5),
        (0x10000270, 0xe0, 0xe0, 5), (0x10000370, 0x12c, 0x12c, 4),
        (0x10007000, end - 0x10007000, end - 0x10007000, 5),
        (0x1000d020, 0x100, 0x100, 6), (0x1000e000, 0, 0x34c8, 6),
        (0x10012000, 0, 0x2000, 6), (0x10014040, 0, 0x400, 6),
        (0x10016780, 0x60, 0x60, 5), (0x10016800, 0, 0x1c010, 6),
        (0x10100020, 0x2e4, 0x2e4, 5), (0x10100320, 0xc, 0xc, 5),
    ]
    actual = [tuple(p[k] for k in ('address', 'filesz', 'memsz', 'flags')) for p in elf['loads']]
    require(actual == expected_loads, 'PT_LOAD footprint/tails differ', actual)
    for s in allocated.values():
        owners = [p for p in elf['loads'] if inside(s['address'], s['size'], p['address'], p['address'] + p['memsz'])]
        require(len(owners) == 1, 'section load owner', s['name'])
        p = owners[0]
        if s['type'] != 8:
            require(s['offset'] == p['offset'] + s['address'] - p['address'] and
                    s['address'] + s['size'] <= p['address'] + p['filesz'],
                    'section/load file mapping', s['name'])
        else:
            require(p['filesz'] == 0, 'BSS must have no file-backed tail', s['name'])
    allowed_metadata = {'', '.xt.prop', '.xt.lit', '.xt.insn', '.xtensa.info',
                        '.symtab', '.strtab', '.shstrtab', '.debug_line',
                        '.debug_info', '.debug_abbrev', '.debug_aranges', '.debug_str'}
    for n, s in sections.items():
        if not s['size']:
            continue
        require(n in allocated or (n in allowed_metadata and not s['flags'] & 7),
                'unexpected nonload section', n)
    pairs = {
        'main': MAIN, 'low_reserved': (0x10003000, 0x10007000),
        'code': (0x10007000, end), 'rodata': (rodata['address'], end),
    }
    names = {
        'window': '.WindowVectors.text', 'kernel_literal': '.KernelExceptionVector.literal',
        'kernel': '.KernelExceptionVector.text', 'user_literal': '.UserExceptionVector.literal',
        'user': '.UserExceptionVector.text', 'double': '.DoubleExceptionVector.text',
        'interface': '.sys_interface_table', 'data': '.entry_data', 'state': '.entry_state',
        'stack': '.entry_stack', 'mailbox': '.entry_mailbox', 'island': '.entry_island',
        'memory': '.entry_memory', 'reset': '.ResetVector.text',
        'debug_literal': '.DebugExceptionVector.literal', 'debug': '.DebugExceptionVector.text',
    }
    for n, section in names.items():
        s = allocated[section]
        pairs[n] = (s['address'], s['address'] + s['size'])
    pairs.update(GUARDS)
    for name, (a, b) in pairs.items():
        require(symbols.get('__hp1020_entry_' + name + '_start') == a and
                symbols.get('__hp1020_entry_' + name + '_end') == b, 'span symbols', name)
    require(symbols.get('__hp1020_entry_text_end') == text['address'] + text['size'], 'text-end symbol')
    require(elf['entry'] == ENTRY == symbols.get('hp1020_entry_start') == symbols.get('_start'), 'entry')
    objects = {name: (allocated['.entry_' + name]['address'], allocated['.entry_' + name]['size'])
               for name in ('data', 'state', 'mailbox', 'memory')}
    actual_objects = {}
    for r in elf['symbol_records']:
        if r['section'] < len(elf['indexed']):
            s = elf['indexed'][r['section']]
            if r['size'] and r['type'] in (1, 2):
                require(inside(r['address'], r['size'], s['address'], s['address'] + s['size']),
                        'object/function outside defining section', r)
            if s['flags'] & 3 == 3 and r['type'] == 1:
                actual_objects[r['name']] = (r['address'], r['size'])
    require(actual_objects == {'hp1020_entry_' + n: span for n, span in objects.items()},
            'unexpected mutable objects', actual_objects)
    for name, (a, _) in objects.items():
        require(symbols.get('hp1020_entry_' + name) == a, 'object displaced', name)
    require(file_bytes(data, sections, 0x1000d020, 256) == DATA_PATTERN, 'initialized sentinel bytes')
    for name in ('.KernelExceptionVector.literal', '.UserExceptionVector.literal', '.DebugExceptionVector.literal'):
        s = allocated[name]
        require(file_bytes(data, sections, s['address'], 4) == bytes(4), 'inert vector literal', name)
    for p in elf['loads']:
        require(not any(p['address'] < b and a < p['address'] + p['memsz'] for a, b in GUARDS.values()),
                'load overlaps guard', p)
    return allocated


def read_properties(elf, data):
    sections = elf['sections']
    require('.xt.prop' in sections, 'modern instruction properties required')
    s = sections['.xt.prop']
    require(s['type'] == 1 and s['flags'] == 0 and s['size'] > 0 and s['size'] % 12 == 0,
            'modern property table shape')
    rows = []
    for a, n, flags in struct.iter_unpack('>III', data[s['offset']:s['offset'] + s['size']]):
        require(flags & ~0x3ffff == 0 and not flags & 0x20000,
                'unknown property or absolute-literal mode', a, n, flags)
        kind = flags & 7
        require(kind in (0, 1, 2, 4, 5, 6), 'property kind', a, n, flags)
        if kind == 6:
            # Pinned GAS marks this no-transform fragment DATA before adding
            # INSN. Admit only the reviewed direct CALL0 and adjacent park;
            # keep its original mixed kind/flags in the evidence.
            require((a, n, flags) ==
                    (elf['symbols'].get('hp1020_entry_before_c'), 6, 0x2906) and
                    elf['symbols'].get('hp1020_entry_park') == a + 3 and
                    file_bytes(data, sections, a, n) == bytes.fromhex('5000d563fffc'),
                    'mixed DATA/INSN outside exact no-transform call/park', a, n, flags)
        if n:
            owners = [q for q in sections.values() if q['flags'] & 2 and q['type'] != 8
                      and inside(a, n, q['address'], q['address'] + q['size'])]
            require(len(owners) == 1, 'property allocation', a, n)
            require(kind not in (2, 6) or owners[0]['flags'] & 4, 'instruction property outside executable allocation', a)
            require(not flags & 0x10, 'hardware-loop target outside profile', a)
            if kind == 0:
                # RELAX_UNREACHABLE padding has no DATA/INSN kind in this
                # assembler. It is verified zero padding, never decoded.
                require(flags == 8 and 1 <= n <= 3 and owners[0]['name'] == '.text' and
                        file_bytes(data, sections, a, n) == bytes(n),
                        'unreachable padding outside reviewed form', a, n, flags)
            if kind & 1:
                require(a % 4 == 0 and n % 4 == 0, 'unaligned literal property', a, n)
            owner = owners[0]['name']
        else:
            owner = None
        rows.append(dict(address=a, bytes=n, flags=flags, kind=kind, section=owner))
    rows.sort(key=lambda r: (r['address'], r['bytes'], r['flags']))
    merge([(r['address'], r['address'] + r['bytes']) for r in rows if r['bytes']])
    require(sum(r['kind'] == 6 for r in rows) == 1, 'one exact no-transform call/park property required')
    ranges = merge([(r['address'], r['address'] + r['bytes']) for r in rows if r['bytes'] and r['kind'] in (2, 6)])
    require(ranges, 'empty instruction annotations')
    literals = [(r['address'], r['address'] + r['bytes']) for r in rows if r['bytes'] and r['kind'] & 1]
    # Legacy tables, if emitted beside .xt.prop, must agree byte-for-byte with
    # the modern classification. They do not authorize a second code closure.
    for name, modern in (('.xt.insn', ranges), ('.xt.lit', merge(literals))):
        if name not in sections or not sections[name]['size']:
            continue
        t = sections[name]
        require(t['type'] == 1 and t['flags'] == 0 and t['size'] % 8 == 0, 'legacy table shape', name)
        entries = list(struct.iter_unpack('>II', data[t['offset']:t['offset'] + t['size']]))
        require(merge([(a, a + n) for a, n in entries]) == modern, 'legacy/modern disagreement', name)
    return rows, ranges, literals


def disassemble(path, prefix, a, b, parser):
    result = subprocess.run([str(prefix) + '-objdump', '-d', f'--start-address={a}',
                             f'--stop-address={b}', str(path)],
                            capture_output=True, text=True, timeout=60, check=False)
    require(result.returncode == 0 and not result.stderr, 'objdump failed', result.returncode, result.stderr)
    return list(parser(result.stdout)), result.stdout


def check_stock(stock_path, prefix, parser):
    from hp1020_xtensa_properties import properties, section_bytes
    stock = Path(stock_path).read_bytes()
    require(digest(stock) == STOCK_SHA256, 'stock source hash')
    sections, tables = properties(stock)
    anchors = (
        (0x100167ab, '021600', 'rsil', (2, 1)),
        (0x100167b0, '02e431', 'wsr.intenable', (2,)),
        (0x100167b5, '02e631', 'wsr.ps', (2,)),
        (0x100167b8, '010200', 'rsync', ()),
        (0x10006cd8, '004831', 'wsr.windowbase', (0,)),
        (0x10006cfa, '014931', 'wsr.windowstart', (1,)),
        (0x10006d00, '000231', 'wsr.lcount', (0,)),
        (0x10006d03, '000031', 'wsr.lbeg', (0,)),
        (0x10006d06, '000131', 'wsr.lend', (0,)),
        (0x10006d0c, '000200', 'isync', ()),
        (0x10006d29, '000404', 'ssai', (0,)),
        (0x10016f2b, '054418', 'src', (4, 4, 5)),
        (0x10008211, '0c0200', 'memw', ()),
    )
    result = []
    for address, raw, op, args in anchors:
        expected = bytes.fromhex(raw)
        require(any(a <= address and address + 3 <= a + n for a, n in tables['.xt.insn']), 'unannotated stock anchor', op)
        require(section_bytes(stock, sections, address, 3) == expected, 'stock instruction bytes', op)
        decoded, _ = disassemble(stock_path, prefix, address, address + 3, parser)
        require(decoded == [(address, (op, args, expected))], 'corrected decoder anchor', op, decoded)
        result.append(dict(address=address, hex=raw, opcode=op, operands=list(args)))
    # Verify the candidate envelope remains inside the original PT_LOAD memory
    # declarations, without assuming the gaps or identifying physical RAM.
    phoff = struct.unpack_from('>I', stock, 28)[0]
    phsize, phnum = struct.unpack_from('>HH', stock, 42)
    loads = [struct.unpack_from('>8I', stock, phoff + i * phsize) for i in range(phnum)]
    spans = merge([(p[2], p[2] + p[5]) for p in loads if p[0] == 1])
    require(MAIN in spans, 'stock main envelope changed')
    return result, spans


def check_startup(elf, data, instructions):
    symbols, sections = elf['symbols'], elf['sections']
    required = ('hp1020_entry_normalize', 'hp1020_entry_after_normalization',
                'hp1020_entry_before_c', 'hp1020_entry_park',
                'hp1020_entry_unexpected_park', 'hp1020_entry_c')
    require(all(n in symbols for n in required), 'missing startup checkpoints')
    normal, after, before, park, unexpected, c_entry = [symbols[n] for n in required]
    require(normal == 0x1000701c and normal < after < before < park < unexpected < c_entry,
            'startup checkpoint ordering', [hex(symbols[n]) for n in required])
    pool_values = (0x10014000, 0x1000e000, 0x100114c8, 0x10014040,
                   0x10014440, 0x10016800, 0x10032810)
    require(file_bytes(data, sections, 0x10007000, 28) == struct.pack('>7I', *pool_values),
            'fixed startup literal pool')
    expected = [
        ('rsil', (2, 15)), ('movi', (2, 0)), ('wsr.intenable', (2,)),
        ('wsr.lcount', (2,)), ('wsr.lbeg', (2,)), ('wsr.lend', (2,)),
        ('isync', ()), ('movi', (2, 15)), ('wsr.ps', (2,)), ('rsync', ()),
        ('movi', (2, 0)), ('wsr.windowbase', (2,)), ('rsync', ()),
        ('movi', (2, 1)), ('wsr.windowstart', (2,)), ('rsync', ()),
        ('ssai', (0,)), ('l32r', (1, 0x10007000)), ('movi', (4, 0)),
    ]
    pc, normalized = normal, []
    for op, args in expected:
        require(pc in instructions, 'prefix missing instruction', pc)
        actual, operands, raw = instructions[pc]
        require(actual.removesuffix('.n') == op and operands == args, 'prefix instruction', pc, actual, operands, op, args)
        if op in PREFIX_RAW:
            require(raw.hex() == PREFIX_RAW[op], 'privileged opcode raw bytes', pc, op, raw.hex())
        normalized.append(dict(address=pc, opcode=actual, operands=list(operands), hex=raw.hex()))
        pc += len(raw)
    require(pc == after, 'normalization checkpoint moved', pc, after)
    # The three clears are checked independently from their linker symbols.
    # Only ordinary stores/branches may connect normalization to the one CALL0.
    for literal in (0x10007004, 0x1000700c, 0x10007014):
        for dst, word in ((2, literal), (3, literal + 4)):
            op, args, raw = instructions.get(pc, ('', (), b''))
            require(op == 'l32r' and args == (dst, word), 'BSS literal load', pc, op, args)
            pc += len(raw)
        loop = pc
        for want, operands in (('s32i', (4, 2, 0)), ('addi', (2, 2, 4)), ('bltu', (2, 3, loop))):
            op, args, raw = instructions.get(pc, ('', (), b''))
            require(op.removesuffix('.n') == want and args == operands, 'ordinary clear loop', pc, op, args)
            pc += len(raw)
    require(pc == before, 'pre-C checkpoint moved')
    op, args, raw = instructions.get(before, ('', (), b''))
    require(op == 'call0' and args == (c_entry,) and before + len(raw) == park, 'own C call/return')
    parks = [park, unexpected, *range(0x10000000, 0x10000180, 0x40),
             0x10000200, 0x10000220, 0x10000270, 0x10100020, 0x10100320]
    for a in parks:
        op, args, raw = instructions.get(a, ('', (), b''))
        require(op == 'j' and args == (a,) and len(raw) == 3, 'inert self-park', a, op, args)
    op, args, raw = instructions.get(ENTRY, ('', (), b''))
    require(op == 'j' and args == (normal,) and len(raw) == 3, 'stack-free entry jump')
    require(file_bytes(data, sections, 0x10000370, 0x12c) == struct.pack('>75I', *([unexpected] * 75)),
            'inert interface table')
    zero_padding = [(0x10016780, ENTRY), (ENTRY + 3, 0x100167e0)]
    zero_padding += [(a + 3, a + 0x40) for a in range(0x10000000, 0x10000180, 0x40)]
    zero_padding += [(a + 3, a + n) for a, n in
                     ((0x10000200, 0x1c), (0x10000220, 0x1c), (0x10000270, 0xe0),
                      (0x10100020, 0x2e0), (0x10100320, 0xc))]
    for a, b in zero_padding:
        require(file_bytes(data, sections, a, b - a) == bytes(b - a), 'fixed inert padding', a, b)
    return normalized, zero_padding, (0x10007000, normal), parks


def linker_fill_evidence(path, elf):
    """Read the preserved link map; its labels alone never authorize bytes."""
    map_path = path.with_suffix('.map')
    raw = map_path.read_bytes()
    text = elf['sections']['.text']
    fills = []
    for line in raw.decode('utf-8').splitlines():
        columns = line.split()
        if not columns or columns[0] != '*fill*':
            continue
        require(len(columns) >= 3 and columns[1].startswith('0x') and
                columns[2].startswith('0x'), 'unrecognized map fill', line)
        a, n = int(columns[1], 16), int(columns[2], 16)
        if not n or not inside(a, n, text['address'], text['address'] + text['size']):
            continue
        require(1 <= n <= 3, 'unexpected text linker fill extent', a, n)
        fills.append((a, a + n))
    require(len(fills) == len(set(fills)), 'duplicate nonempty text linker fill')
    merge(fills)
    return sorted(fills), dict(file=map_path.name, bytes=len(raw), sha256=digest(raw))


def classify_code(elf, data, rows, instructions, zero_padding, pool, linker_fills):
    """Every executable-section byte has an explicit non-overclaiming label."""
    labels = {}
    for s in elf['sections'].values():
        if s['size'] and s['flags'] & 4:
            labels[s['name']] = bytearray(s['size'])
    def paint(a, b, label, compatible=()):
        matches = [s for s in elf['sections'].values() if s['name'] in labels and
                   inside(a, b - a, s['address'], s['address'] + s['size'])]
        if not matches:
            return
        require(len(matches) == 1, 'classification allocation', a, b)
        s = matches[0]
        area = labels[s['name']]
        for i in range(a - s['address'], b - s['address']):
            require(area[i] in (0, label, *compatible), 'code/data classification overlap', a, b, label, area[i])
            area[i] = label
    # 1=instructions, 2=literals, 3=explicit DATA, 4=fixed zero padding,
    # 5=the fixed seven-word pool, 6=property-authorized alignment padding,
    # 7=nonempty UNREACHABLE zero padding, 8=map/property-backed linker fill,
    # 9=the excluded libgcc divide-trap's four-byte diagnostic marker.
    for r in rows:
        if r['bytes']:
            label = 1 if r['kind'] in (2, 6) else 2 if r['kind'] & 1 else 7 if r['kind'] == 0 else 3
            paint(r['address'], r['address'] + r['bytes'], label)
    paint(*pool, 5, compatible=(2, 3))
    for a, b in zero_padding:
        paint(a, b, 4, compatible=(3,))
    alignment = []
    for r in rows:
        if not r['flags'] & 0x800:
            continue
        power = (r['flags'] >> 12) & 31
        require(power <= 4, 'unexpected code alignment requirement', r)
        a = r['address'] + r['bytes']
        b = (a + (1 << power) - 1) & -(1 << power)
        if a == b:
            continue
        owner = [s for s in elf['sections'].values() if s['name'] in labels and inside(a, b - a, s['address'], s['address'] + s['size'])]
        if not owner:
            continue
        # Only the exact next-block alignment, never a guessed gap extending
        # to another instruction. Its bytes remain non-executable regardless
        # of whether the assembler used zeros or NOP encodings.
        paint(a, b, 6, compatible=(3, 4, 7))
        alignment.append(dict(address=a, bytes=b - a, hex=file_bytes(data, elf['sections'], a, b - a).hex()))
    linker_padding = []
    for a, b in linker_fills:
        # Input-section end markers do not transfer their next-section
        # alignment into a nonempty property. Require both actual markers,
        # the exact map fill, zero bytes and the minimal next-4-byte extent.
        require(b == ((a + 3) & ~3) and
                any(r['address'] == a and r['bytes'] == 0 and r['flags'] == 8 for r in rows) and
                any(r['bytes'] and r['kind'] in (2, 6) and r['address'] + r['bytes'] == a for r in rows) and
                any(r['address'] == b and r['bytes'] == 0 and r['flags'] == 0x2804 for r in rows) and
                file_bytes(data, elf['sections'], a, b - a) == bytes(b - a),
                'unproved text linker alignment fill', a, b)
        paint(a, b, 8)
        linker_padding.append(dict(address=a, bytes=b - a, hex='00' * (b - a)))
    divide_markers = []
    if '__udivsi3' in elf['symbols']:
        trap = elf['symbols']['__udivsi3'] + 0x41
        a, b = trap + 3, trap + 7
        require(instructions.get(trap) == ('ill', (), bytes(3)) and
                file_bytes(data, elf['sections'], a, 4) == b'DIV0',
                'libgcc divide trap/diagnostic marker differs', trap)
        paint(a, b, 9)
        divide_markers.append(dict(address=a, bytes=4, hex='44495630',
                                   kind='libgcc source diagnostic after excluded ILL; never executable'))
    for name, area in labels.items():
        missing = area.find(b'\0')
        require(missing < 0, 'unclassified executable-section byte', name,
                elf['sections'][name]['address'] + missing)
    # Fixed padding and fixed literal words must never have become INSN.
    for at, (_, _, raw) in instructions.items():
        require(not any(at < b and a < at + len(raw) for a, b in [pool, *zero_padding]),
                'instruction in fixed literal/padding', at)
    return [dict(section=name, classification_bytes=dict(sorted(Counter(area).items())))
            for name, area in sorted(labels.items())], alignment, linker_padding, divide_markers


def stack_usage(directory):
    paths = sorted(directory.glob('*.su'))
    require({p.stem for p in paths} == STACK_USAGE_NAMES, 'exact C stack-usage closure', [p.name for p in paths])
    files, records = [], []
    for path in paths:
        raw = path.read_bytes()
        files.append(dict(file=path.name, bytes=len(raw), sha256=digest(raw)))
        for line in raw.decode('utf-8').splitlines():
            columns = line.rsplit('\t', 2)
            require(len(columns) == 3 and columns[1].isdigit() and columns[2] == 'static',
                    'nonstatic/unrecognized stack-use row', path.name, line)
            frame = int(columns[1])
            require(frame <= 0x2000 and frame % 16 == 0, 'single frame exceeds/violates owned stack', path.name, line)
            records.append(dict(file=path.name, function=columns[0], bytes=frame, qualifier=columns[2]))
    require(records, 'no stack-use records')
    return dict(files=files, functions=records, largest_individual_frame=max(r['bytes'] for r in records),
                owned_stack_bytes=0x2000,
                limitation='Individual compiler frames only; libgcc/assembly and nested/callback depth still require actual runtime stack bounds.')


def audit_target(path, prefix, stock_path):
    """Return a strict Program plus JSON-safe evidence; do not execute it.

    entry_read_spans is (start, BYTE_COUNT), unlike write_ranges and
    execute_ranges, which are (start, END). .entry_data is readable and
    file-backed SHF_WRITE, but deliberately excluded from runtime writes.
    """
    from hp1020_xtensa_call0 import Program
    path = Path(path)
    data = path.read_bytes()
    elf = read_elf(data)
    allocated = check_layout(elf, data)
    rows, code_ranges, literal_ranges = read_properties(elf, data)
    anchors, stock_spans = check_stock(stock_path, prefix, Program.parse)
    for p in elf['loads']:
        require(any(inside(p['address'], p['memsz'], a, b) for a, b in stock_spans),
                'load outside original-declared envelope', p)
    instructions, listings = {}, []
    for a, b in code_ranges:
        decoded, listing = disassemble(path, prefix, a, b, Program.parse)
        listings.append(listing)
        pc = a
        for at, (op, args, raw) in decoded:
            require(at == pc and len(raw) in (2, 3) and at not in instructions,
                    'noncontiguous/duplicate decoded instruction', at, pc)
            require(at + len(raw) <= b and raw == file_bytes(data, elf['sections'], at, len(raw)),
                    'decoded instruction differs from original ELF bytes', at)
            instructions[at] = (op, args, raw)
            pc += len(raw)
        require(pc == b, 'incomplete annotated decode', a, b, pc)
    prefix_rows, padding, pool, parks = check_startup(elf, data, instructions)
    linker_fills, link_map = linker_fill_evidence(path, elf)
    labels, alignment, linker_padding, divide_markers = classify_code(
        elf, data, rows, instructions, padding, pool, linker_fills)
    normal = elf['symbols']['hp1020_entry_normalize']
    after = elf['symbols']['hp1020_entry_after_normalization']
    traps, direct, literal_uses, dynamic = [], [], [], []
    literal_permissions = [pool, *literal_ranges]
    for pc, (op, args, raw) in sorted(instructions.items()):
        if op == 'ill':
            require(pc == elf['symbols'].get('__udivsi3', -1000) + 0x41 and raw == bytes(3),
                    'unrecognized trap', pc, raw.hex())
            traps.append(dict(address=pc, hex=raw.hex(), kind='libgcc unsigned division by zero; excluded from execution'))
        elif op in PREFIX_RAW:
            require(normal <= pc < after and raw.hex() == PREFIX_RAW[op], 'special operation outside exact prefix', pc, op)
        else:
            require(op in ORDINARY, 'opcode outside conservative call0 profile', pc, op)
        if op in DIRECT_BRANCHES or op in ('call0', 'j'):
            require(args and isinstance(args[-1], int) and args[-1] in instructions,
                    'static target not an annotated boundary', pc, op, args)
            direct.append(dict(address=pc, opcode=op, target=args[-1]))
        elif op in ('callx0', 'jx', 'ret', 'ret.n'):
            dynamic.append(dict(address=pc, opcode=op, operands=list(args)))
        if op == 'l32r':
            require(len(args) == 2 and isinstance(args[1], int) and args[1] % 4 == 0 and
                    any(inside(args[1], 4, a, b) for a, b in literal_permissions),
                    'L32R outside annotated/fixed readable literal', pc, args)
            # PC-relative mode is a supplied entry condition. Recompute the
            # sign-extended negative word displacement from the actual BE
            # instruction, independently of objdump's printed target.
            require(len(raw) == 3 and raw[0] >> 4 == 1 and args[0] == (raw[0] & 15),
                    'L32R encoding/register', pc, args, raw.hex())
            encoded_target = (((pc + 3) & ~3) +
                              (int.from_bytes(raw[1:], 'big') - 0x10000) * 4) & 0xffffffff
            require(args[1] == encoded_target, 'L32R decoded displacement', pc, args, encoded_target)
            literal_uses.append(dict(address=pc, target=args[1],
                                     word=int.from_bytes(file_bytes(data, elf['sections'], args[1], 4), 'big')))
    require(len(traps) <= 1, 'multiple divide traps')
    for r in elf['symbol_records']:
        if r['type'] == 2 and r['size']:
            require(r['address'] in instructions, 'function symbol starts outside annotation', r)
    trap_pcs = {r['address'] for r in traps}
    admitted = {pc: row for pc, row in instructions.items() if pc not in trap_pcs}
    execute_ranges = merge([(pc, pc + len(row[2])) for pc, row in admitted.items()])
    # Avoid Program.__init__: it would decode all sections if old .xt.insn is
    # absent. Program.parse is shared, but only the validated modern closure
    # enters this object. Non-None annotated_code also disables lazy decoding.
    program = Program.__new__(Program)
    program.path, program.prefix, program.entry = path, str(prefix), elf['entry']
    program.symbols = elf['symbols']
    program.segments = [(p['address'], bytearray(data[p['offset']:p['offset'] + p['filesz']]) +
                         bytearray(p['memsz'] - p['filesz']), p['flags']) for p in elf['loads']]
    program.instructions = admitted
    program.annotated_code = [(a, b - a) for a, b in execute_ranges]
    program.execute_ranges = execute_ranges
    program.write_ranges = list(WRITE_RANGES)
    program.entry_read_spans = [(s['address'], s['size']) for s in sorted(allocated.values(), key=lambda s: s['address'])]
    program.entry_audit_disassembly = ''.join(listings)
    program.entry_excluded_traps = sorted(trap_pcs)
    su = stack_usage(path.parent)
    objdump = Path(str(prefix) + '-objdump')
    audit = dict(
        schema='hp1020-entry-ram-audit-v1', target_sha256=digest(data), target_bytes=len(data),
        stock_sha256=STOCK_SHA256, entry=elf['entry'], elf_flags=elf['flags'],
        objdump_sha256=digest(objdump.read_bytes()), audit_source_sha256=digest(Path(__file__).read_bytes()),
        allocated_sections=[dict(s) for s in sorted(allocated.values(), key=lambda s: s['address'])],
        load_segments=elf['loads'], source_anchor_checks=anchors,
        symbols=dict(sorted(elf['symbols'].items())),
        properties=rows, annotated_instructions=len(instructions), admitted_instructions=len(admitted),
        annotated_instruction_bytes=sum(len(row[2]) for row in instructions.values()),
        execution_ranges=[[a, b] for a, b in execute_ranges],
        read_spans=[[a, n] for a, n in program.entry_read_spans],
        write_ranges=[[a, b] for a, b in program.write_ranges],
        immutable_initialized_data=[0x1000d020, 0x1000d120],
        footprint=dict(text_bytes=allocated['.text']['size'], rodata_bytes=allocated['.rodata']['size'],
                       initialized_data_bytes=256, state_bytes=13512, memory_bytes=114704,
                       mailbox_bytes=1024, owned_stack_bytes=8192,
                       file_backed_load_bytes=sum(p['filesz'] for p in elf['loads']),
                       load_memory_bytes=sum(p['memsz'] for p in elf['loads'])),
        prefix=prefix_rows, inert_park_addresses=parks, byte_classification=labels,
        alignment_padding=alignment, excluded_division_traps=traps,
        linker_alignment_padding=linker_padding, link_map=link_map,
        excluded_division_markers=divide_markers,
        direct_targets=direct, dynamic_control_sites=dynamic, literal_loads=literal_uses,
        opcode_counts=dict(sorted(Counter(row[0] for row in admitted.values()).items())),
        stack_usage=su, disassembly_sha256=digest(program.entry_audit_disassembly.encode()),
        scope='Whole linked annotated call0 closure and exact new offline layout; no target instructions executed by this audit.',
        limitations=[
            'No hardware loader, RAM size/attributes, cache, privilege, USB or printing compatibility claim.',
            'Privileged usable mapped RAM, PC-relative L32R, no asynchronous/debug exception and nonintersecting incoming loop endpoint are supplied.',
            'Runtime must enforce actual instruction boundaries, phase-specific writes, read spans, dynamic targets and owned stack; no historical external stack.',
            'Data sentinel is ELF-writable for object placement but is immutable during this experiment.',
            'Excluded divide-by-zero ILL is byte-verified but not admitted for execution.',
        ])
    return program, audit
