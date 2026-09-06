"""Read old Xtensa ELF instruction/literal annotations without guessing code.

The binutils elf32-xtensa.c xtensa_read_table_entries implementation reads
legacy .xt.insn/.xt.lit records as two target-endian words: address and size.
Unlike newer .xt.prop records, these have implicit flags and no third word.
Annotations describe regions, not function boundaries or execution reachability.
"""
import struct


def properties(data):
    if data[:6] != b'\x7fELF\x01\x02':
        raise ValueError('expected ELF32 big-endian')
    shoff = struct.unpack_from('>I', data, 32)[0]
    shsize, shnum, shstr = struct.unpack_from('>HHH', data, 46)
    if shsize != 40 or shstr >= shnum or shoff + shsize * shnum > len(data):
        raise ValueError('invalid section table')
    headers = [struct.unpack_from('>10I', data, shoff + i * shsize) for i in range(shnum)]
    strings = headers[shstr]
    names = data[strings[4]:strings[4] + strings[5]]
    sections = {}
    for h in headers:
        name = names[h[0]:].split(b'\0')[0].decode('ascii')
        if h[1] != 8 and h[4] + h[5] > len(data):
            raise ValueError('section outside ELF')
        sections[name] = dict(flags=h[2], address=h[3], offset=h[4], size=h[5], type=h[1])
    tables = {}
    for name in ('.xt.insn', '.xt.lit'):
        if name not in sections:
            continue
        sec = sections[name]
        if sec['size'] % 8:
            raise ValueError('partial Xtensa property record')
        ranges = sorted(struct.iter_unpack('>II', data[sec['offset']:sec['offset'] + sec['size']]))
        end = 0
        for address, size in ranges:
            if not size or address < end or address + size > 0x100000000:
                raise ValueError('invalid or overlapping Xtensa properties')
            owners = [s for s in sections.values() if s['flags'] & 2 and s['type'] != 8
                      and s['address'] <= address < address + size <= s['address'] + s['size']]
            if len(owners) != 1 or (name == '.xt.insn' and not owners[0]['flags'] & 4):
                raise ValueError('property outside matching allocated section')
            end = address + size
        tables[name] = ranges
    for a, size in tables.get('.xt.insn', []):
        if any(a < b + count and b < a + size for b, count in tables.get('.xt.lit', [])):
            raise ValueError('instruction and literal properties overlap')
    return sections, tables


def section_bytes(data, sections, address, size):
    for s in sections.values():
        if s['flags'] & 2 and s['type'] != 8 and s['address'] <= address < address + size <= s['address'] + s['size']:
            off = s['offset'] + address - s['address']
            return data[off:off + size]
    raise ValueError('address has no file-backed section')
