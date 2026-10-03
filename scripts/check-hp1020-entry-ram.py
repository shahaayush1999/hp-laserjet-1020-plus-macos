#!/usr/bin/env python3
"""Independent capture-only entry checker; stdlib, never target/producer imports.

Literal expectations were frozen before candidate execution. This checks saved
evidence, not physical boot or a second CPU implementation. See README.md for
the deliberately bounded ISA trace decoding and provenance limitations.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import posixpath
import re
import struct

MAIN = 0x10003000
ENTRY = 0x100167a8
STATE = (0x1000e000, 13496)
MEMORY = (0x10016800, 114704)
MAILBOX = (0x10014040, 1024)
STACK = (0x10012000, 8192)
DATA = (0x1000d020, 256)
ZERO = (STATE, MEMORY, MAILBOX)
MUTABLE = ZERO + (STACK,)
REGIONS = ((MAIN, 0x321e0), (0x10000000, 0x184), (0x10000200, 0x3c),
           (0x10000270, 0xe0), (0x10000370, 0x12c),
           (0x10100020, 0x2e4), (0x10100320, 0xc))
PHASES = ('initial', 'after-normalization', 'pre-c', 'pre-finish', 'park')
QPHASES = PHASES + ('park-step-1', 'park-step-2')
CP_SYMBOLS = ('hp1020_entry_after_normalization', 'hp1020_entry_before_c',
              'hp1020_usb_document_finish', 'hp1020_entry_park')
CPU = (
    dict(name='ordinary-privilege', ps=0, intenable=0, windowbase=0,
         windowstart=1, sar=0, lbeg=0, lend=0, lcount=0),
    dict(name='dirty-window3', ps=0x70302, intenable=1, windowbase=3,
         windowstart=0x89, sar=37, lbeg=0x10003000, lend=0x10003020, lcount=17),
    dict(name='dirty-window7-excm', ps=0x50711, intenable=2, windowbase=7,
         windowstart=0xc1, sar=63, lbeg=0x10003040, lend=0x10003060, lcount=65535))
PAINTS = ((0xa5, 0x5a), (0xcc, 0x96))
GDB = dict(pc=0, lbeg=33, lend=34, lcount=35, sar=36,
           windowbase=38, windowstart=39, ps=42, intenable=110)
SENTINEL = bytes.fromhex('31527394b5d6f718395a7b9cbddeff20') * 16
BIE = bytes.fromhex('000001000000002000000008000000041000035cfd98ff02ff02')
PIXELS = b'\xff' * 32
BACKEND_HASH = '8fe170ab6161d47d17ef93eb6c25622878e00dc2d4747cfd70073a0fd777b5e2'
ORACLE_HASH = 'a5046eb1a84b67ef7f4461e9169cbd14c88024161d786fd1b7438677233718ee'
LAYOUT_HASH = 'c37ba6986d6ed7cb2dceb647902873e04302e7eb55256eb73ebdf26ea1df6f35'
SAMPLE_HASH = '8c6aa75a8c967897e72673e585c8ae862004e6e1c2b22118943ead4070e96206'
PRIMARY = {
    'provenance.json': 'a207e83239270e8cd09763a9b96e80e733745e2e74d70cd44337ee27dc88f100',
    'target/xtensa/gdbstub.c': '132bb55cd6203ec5ac22f4ce2611447f225306abd6c8c4b06367b08a65ac42c1',
    'target/xtensa/core-test_kc705_be/gdb-config.c.inc': '3bca88cfe97be52026d9e9762328f293a7892407014a775a221d2262abb0e70c',
    'target/xtensa/core-test_kc705_be/core-isa.h': '449fcb676f9c05ae143749e619c4edcac3e07f590f086a58e1de0cd844f1d2cb',
    'target/xtensa/core-test_kc705_be.c': '9113b65e67095cd0697788530c3c1ed9d64628645828b6ec06e575f43be07a97'}
LAYOUT_RECORDS = (
    (1, 68, 4), (1, 72, 4), (1, 76, 4), (1, 80, 4), (1, 88, 1), (1, 89, 1),
    (1, 13492, 1), (1, 4720, 4), (1, 13248, 4), (1, 13452, 4), (1, 13456, 4),
    (1, 13493, 1), (1, 13488, 4), (1, 13484, 4), (1, 84, 4), (1, 13469, 1),
    (1, 13464, 4), (2, 0, 4096), (2, 81936, 32768), (2, 4096, 77840))
LAYOUT_WORDS = (1, 65, 20, 13496, 114704) + tuple(v for r in LAYOUT_RECORDS for v in r)
FIXED = {
    '.WindowVectors.text': (0x10000000, 0x180, 1, 6),
    '.KernelExceptionVector.literal': (0x10000180, 4, 1, 2),
    '.KernelExceptionVector.text': (0x10000200, 0x1c, 1, 6),
    '.UserExceptionVector.literal': (0x1000021c, 4, 1, 2),
    '.UserExceptionVector.text': (0x10000220, 0x1c, 1, 6),
    '.DoubleExceptionVector.text': (0x10000270, 0xe0, 1, 6),
    '.sys_interface_table': (0x10000370, 0x12c, 1, 2),
    '.entry_data': (*DATA, 1, 3), '.entry_state': (*STATE, 8, 3),
    '.entry_stack': (*STACK, 8, 3), '.entry_mailbox': (*MAILBOX, 8, 3),
    '.entry_island': (0x10016780, 0x60, 1, 6), '.entry_memory': (*MEMORY, 8, 3),
    '.ResetVector.text': (0x10100020, 0x2e0, 1, 6),
    '.DebugExceptionVector.literal': (0x10100300, 4, 1, 2),
    '.DebugExceptionVector.text': (0x10100320, 0xc, 1, 6)}


def need(ok, text):
    if not ok:
        raise ValueError(text)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def path(root, name):
    need(isinstance(name, str) and name and not Path(name).is_absolute(), 'relative capture path')
    p = (root / name).resolve()
    need(p.is_relative_to(root.resolve()), 'capture path escaped root')
    return p


def raw(root, name, limit=256 * 1024 * 1024):
    p = path(root, name)
    need(p.is_file() and p.stat().st_size <= limit, 'bounded captured file: ' + name)
    return p.read_bytes()


def js(root, name):
    return json.loads(raw(root, name, 32 * 1024 * 1024))


def digest_shape(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


def seal_tree(root, directory, expected):
    need(isinstance(expected, dict) and expected, 'nonempty ' + directory + ' seal')
    actual = {str(p.relative_to(root / directory)) for p in (root / directory).rglob('*') if p.is_file()}
    need(actual == set(expected), 'exact ' + directory + ' file set')
    for name, digest in expected.items():
        need(digest_shape(digest) and sha(raw(root, directory + '/' + name)) == digest,
             directory + ' bytes differ: ' + name)


def inside(address, size, spans):
    return type(address) is int and type(size) is int and 0 < size <= 0x100000000 - address and any(
        a <= address and address + size <= a + n for a, n in spans)


def part(images, address, size):
    for a, data in images.items():
        if a <= address and address + size <= a + len(data):
            return bytes(data[address - a:address - a + size])
    raise ValueError('capture slice outside seven regions')


def put(images, address, value):
    for a, data in images.items():
        if a <= address and address + len(value) <= a + len(data):
            data[address - a:address - a + len(value)] = value
            return
    raise ValueError('replayed write outside seven regions')


def fnv(data):
    n = 0x811c9dc5
    for b in data:
        n = ((n ^ b) * 0x01000193) & 0xffffffff
    return n


def input_literal():
    def item(k, v):
        return struct.pack('>IHBBI', 12, k, 1, 0, v)
    def chunk(k, data=b'', count=0, reserved=0):
        return struct.pack('>IIIHH', len(data) + 16, k, count, reserved, 0x5a5a) + data
    doc = b''.join(item(k, v) for k, v in ((1, 0), (2, 1), (0, 0)))
    page = b''.join(item(k, v) for k, v in ((23, 0), (17, 16), (18, 8), (16, 2),
        (12, 32), (13, 8), (7, 1), (8, 600), (9, 600), (5, 7), (4, 1), (3, 9), (6, 1)))
    return (b'JZJZ' + chunk(0, doc, 3, 36) + chunk(2, page, 13, 156) +
            chunk(4, BIE[:20]) + chunk(5, BIE[20:] + bytes(18)) +
            chunk(6) + chunk(3) + chunk(1))


def receive_literal(source):
    memory = bytearray(4096)
    pos = 0
    for i, n in enumerate((64, 64, 64, 64, 64, 32)):
        memory[(i % 4) * 1024:(i % 4) * 1024 + n] = source[pos:pos + n]
        pos += n
    need(pos == len(source) == 352, 'literal input schedule')
    return bytes(memory)


def park_words(source):
    return [0x48503130, 1, 2, 0, 5, 0, 0, 0, 0, 0, 0, 0, 129224, 256,
            352, fnv(source), 352, 6, 6, 6, 6, 1, 1, 6, 6, 0, 1, 0, 1, 1, 1, 1,
            32, fnv(PIXELS), 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 8, 8, 8, 0, 1, 6,
            32, 1, 8, 4, 0, 0, 0, fnv(receive_literal(source)),
            fnv(PIXELS + bytes(32736)), 13496, 114704, 0, 0, 0]


class Elf:
    """Read linked bytes and layout independently; no objdump or producer API."""
    def __init__(self, data):
        self.data = data
        need(data[:7] == b'\x7fELF\x01\x02\x01' and len(data) >= 52, 'ELF32 BE header')
        h = struct.unpack_from('>HHIIIIIHHHHHH', data, 16)
        typ, machine, version, entry, po, so, flags, hs, ps, pn, ss, sn, si = h
        need((typ, machine, version, entry, hs, ps, ss) == (2, 94, 1, ENTRY, 52, 32, 40), 'linked ELF identity')
        need(0 < sn <= 1024 and si < sn and so + sn * 40 <= len(data) and po + pn * 32 <= len(data), 'ELF table bounds')
        headers = [struct.unpack_from('>10I', data, so + 40 * i) for i in range(sn)]
        st = headers[si]
        names = data[st[4]:st[4] + st[5]]
        self.sections = {}
        for s in headers:
            need(s[0] < len(names) and (s[1] == 8 or s[4] + s[5] <= len(data)), 'ELF section bounds')
            name = names[s[0]:].split(b'\0', 1)[0].decode('ascii')
            need(name not in self.sections, 'unique ELF section name')
            self.sections[name] = s
        self.alloc = {k: s for k, s in self.sections.items() if s[2] & 2 and s[5]}
        need(set(self.alloc) == set(FIXED) | {'.text', '.rodata'}, 'exact allocated object set')
        for name, wanted in FIXED.items():
            s = self.alloc[name]
            need((s[3], s[5], s[1], s[2]) == wanted, 'fixed ELF object ' + name)
        t, r = self.alloc['.text'], self.alloc['.rodata']
        need(t[1] == r[1] == 1 and t[2] == 6 and r[2] == 2 and t[3] == 0x10007000 and
             t[5] > 0 and r[5] > 0 and t[3] + t[5] <= r[3] and r[3] % 4 == 0 and
             r[3] + r[5] <= 0x1000d000, 'read-only code budget')
        spans = sorted((s[3], s[3] + s[5]) for s in self.alloc.values())
        need(all(a[1] <= b[0] for a, b in zip(spans, spans[1:])), 'allocated overlap')
        self.loads = []
        for i in range(pn):
            k, off, va, pa, fs, ms, pf, al = struct.unpack_from('>8I', data, po + 32 * i)
            if k != 1:
                continue
            need(pa == va and 0 <= fs <= ms and inside(va, ms, REGIONS) and off + fs <= len(data), 'load extent')
            self.loads.append(dict(address=va, physical=pa, offset=off, filesz=fs, memsz=ms, flags=pf, align=al))
        need(len(self.loads) == 13, 'exact thirteen load segments')
        loads = sorted((x['address'], x['address'] + x['memsz']) for x in self.loads)
        need(all(a[1] <= b[0] for a, b in zip(loads, loads[1:])), 'load overlap')
        for s in self.alloc.values():
            owners = [x for x in self.loads if x['address'] <= s[3] and s[3] + s[5] <= x['address'] + x['memsz']]
            need(len(owners) == 1, 'allocated load owner')
            p = owners[0]
            need(p['flags'] == (4 | (2 if s[2] & 1 else 0) | (1 if s[2] & 4 else 0)) or
                 s[2] == 2 and p['flags'] == 5, 'load permission shape')
            if s[1] != 8:
                need(s[3] + s[5] <= p['address'] + p['filesz'] and s[4] == p['offset'] + s[3] - p['address'], 'section file mapping')
            else:
                need(p['filesz'] == 0 and p['address'] == s[3] and p['memsz'] == s[5], 'no broad NOBITS zero-load')
        syms = [s for s in headers if s[1] == 2]
        need(len(syms) == 1 and syms[0][9] == 16 and syms[0][5] % 16 == 0, 'static symbol table')
        st = syms[0]; strings = headers[st[6]]
        names = data[strings[4]:strings[4] + strings[5]]
        self.symbols = {}
        for off in range(st[4], st[4] + st[5], 16):
            ni, value, size, info, other, index = struct.unpack_from('>IIIBBH', data, off)
            if not ni:
                continue
            name = names[ni:].split(b'\0', 1)[0].decode('ascii')
            self.symbols.setdefault(name, []).append((value, size, info, index))
        self.read_spans = [(s[3], s[5]) for s in self.alloc.values()]
        need(self.file(*DATA) == SENTINEL, 'file-backed sentinel')
        self.instructions = {}
        prop = self.sections['.xt.prop']
        need(prop[1] == 1 and prop[2] == 0 and prop[5] % 12 == 0 and prop[5], 'Xtensa property metadata')
        properties = list(struct.iter_unpack('>III', data[prop[4]:prop[4] + prop[5]]))
        occupied = []
        for a, n, f in properties:
            need(f & ~0x3ffff == 0 and not f & 0x20000, 'ordinary PC-relative instruction properties')
            if not n:
                continue
            need(inside(a, n, self.read_spans), 'property allocation')
            occupied.append((a, a + n))
            kind = f & 7
            if kind == 6:
                # Pinned GAS get_frag_property_flags sets DATA for the initially
                # empty no-transform fragment, then INSN for its actual code.
                # Admit only the independently decoded CALL0 + terminal J pair;
                # no arbitrary mixed property becomes executable by this rule.
                need(f == 0x2906 and a == self.symbol('hp1020_entry_before_c') and
                     n == 6 and self.symbol('hp1020_entry_park') == a + 3,
                     'one exact no-transform CALL0/park property')
                call = int.from_bytes(self.file(a, 3), 'big')
                need(call & 0xfc0000 == 0x500000 and
                     ((a & ~3) + 4 + signed18(call & 0x3ffff) * 4) & 0xffffffff ==
                     self.symbol('hp1020_entry_c') and
                     jump_target(a + 3, self.file(a + 3, 3)) == a + 3,
                     'actual mixed property contains only linked CALL0/self-J')
            elif kind != 2:
                continue
            need(inside(a, n, [(s[3], s[5]) for s in self.alloc.values() if s[2] & 4]), 'code property permission')
            pc = a
            while pc < a + n:
                nibble = self.file(pc, 1)[0] >> 4
                width = 3 if nibble < 8 else 2 if nibble < 14 else 0
                need(width and pc + width <= a + n and pc not in self.instructions, 'bounded independent instruction width')
                self.instructions[pc] = self.file(pc, width)
                pc += width
        occupied.sort()
        need(all(a[1] <= b[0] for a, b in zip(occupied, occupied[1:])), 'overlapping properties')

    def symbol(self, name, width=None):
        items = self.symbols.get(name, [])
        need(items and len({x[0] for x in items}) == 1, 'unambiguous symbol ' + name)
        if width is not None:
            need(all(x[1] == width for x in items), 'symbol extent ' + name)
        return items[0][0]

    def file(self, address, count):
        owners = [s for s in self.alloc.values() if s[1] != 8 and s[3] <= address and address + count <= s[3] + s[5]]
        need(len(owners) == 1, 'unique file-backed bytes')
        s = owners[0]; off = s[4] + address - s[3]
        return self.data[off:off + count]


def signed18(n):
    return n - 0x40000 if n & 0x20000 else n


def jump_target(pc, code):
    n = int.from_bytes(code, 'big')
    need(len(code) == 3 and n & 0xfc0000 == 0x600000, 'actual direct J encoding')
    return (pc + 4 + signed18(n & 0x3ffff)) & 0xffffffff


def make_initial(elf, fills):
    memory = {a: bytearray((i * 29 + (a >> 4) + 0x67) & 255 for i in range(n)) for a, n in REGIONS}
    for p in elf.loads:
        if p['filesz']:
            put(memory, p['address'], elf.data[p['offset']:p['offset'] + p['filesz']])
    for a, n in ZERO:
        put(memory, a, bytes([fills[0]]) * n)
    put(memory, STACK[0], bytes([fills[1]]) * STACK[1])
    return {a: bytes(b) for a, b in memory.items()}


def cpu_initial(profile):
    result = {k: v for k, v in CPU[profile].items() if k != 'name'}
    result.update(pc=ENTRY, physical_ar=[0x8a000001 + profile * 0x100000 + i * 0x10101 for i in range(32)])
    return result


def registers(value, qemu=False):
    alias = 'logical_a' if qemu else 'logical_ar'
    need(set(value) == set(GDB) | {'physical_ar', alias}, 'exact register capture fields')
    out = dict(value); out['logical_ar'] = out.pop(alias)
    need(all(type(out[n]) is int and 0 <= out[n] <= 0xffffffff for n in GDB), 'u32 register observations')
    need(len(out['physical_ar']) == 32 and len(out['logical_ar']) == 16 and out['windowbase'] < 8, 'complete window observation')
    need(all(type(v) is int and 0 <= v <= 0xffffffff for v in out['physical_ar']), 'u32 physical ARs')
    need(out['logical_ar'] == [out['physical_ar'][(4 * out['windowbase'] + i) % 32] for i in range(16)], 'physical/logical register aliases')
    return out


def snapshots(folder, rows, labels, qemu=False):
    need([r['name'] for r in rows] == list(labels), 'exact ordered snapshot matrix')
    images = {}
    for item in rows:
        label = item['name']
        need(item == js(folder, label + '/snapshot.json') and item['status'] == 'complete', 'actual snapshot metadata')
        need(item['registers'] == js(folder, label + '/registers.json'), 'register-file seal')
        registers(item['registers'], qemu)
        need([(r['start'], r['bytes']) for r in item['regions']] == list(REGIONS), 'full ordered region set')
        images[label] = {}
        for row, (a, n) in zip(item['regions'], REGIONS):
            expected = f'{label}/region-{a:08x}-{n:08x}.bin'
            need(row['path'] == expected and row['captured_bytes'] == n, 'canonical full region identity')
            data = raw(folder, expected)
            need(len(data) == n and sha(data) == row['sha256'], 'raw region byte seal')
            images[label][a] = data
    return images


def protected(initial, actual, writable):
    for a, old in initial.items():
        now = actual[a]
        need(len(now) == len(old), 'protected region size')
        for i, (x, y) in enumerate(zip(old, now)):
            need(x == y or inside(a + i, 1, writable), f'protected byte changed at{a + i:#x}')


def semantic_snapshots(rows, images, initial, supplied, checkpoints, source, qemu=False):
    for item in rows:
        label = item['name']; regs = registers(item['registers'], qemu)
        actual = images[label]
        if label == 'initial':
            need({k: v for k, v in regs.items() if k != 'logical_ar'} == supplied and actual == initial, 'exact supplied initial state')
            continue
        cp = checkpoints['park' if label.startswith('park-step') else label]
        need(regs['pc'] == cp, 'actual checkpoint PC')
        allowed = () if label == 'after-normalization' else ZERO if label == 'pre-c' else MUTABLE
        protected(initial, actual, allowed)
        need(part(actual, *DATA) == SENTINEL, 'initialized data preserved')
        for n, v in dict(ps=15, intenable=0, windowbase=0, windowstart=1, lbeg=0, lend=0, lcount=0).items():
            need(regs[n] == v, 'normalized actual CPU ' + n)
        if label in ('after-normalization', 'pre-c') or label.startswith('park'):
            need(regs['physical_ar'][1] == STACK[0] + STACK[1], 'own stack top at checkpoint')
        if label in ('after-normalization', 'pre-c'):
            need(regs['sar'] == 0, 'startup SAR')
        if label == 'pre-c':
            need(all(part(actual, a, n) == bytes(n) for a, n in ZERO), 'all three BSS objects zero before C')
        if label in ('pre-finish', 'park', 'park-step-1', 'park-step-2'):
            values = [int.from_bytes(part(actual, STATE[0] + off, width), 'big') for base, off, width in LAYOUT_RECORDS[:17]]
            stopped = int(label != 'pre-finish')
            need(values == [1, 6, 6, 0, stopped, 0, stopped, 1, 1, 1, 1, 0, 0, 1, 0, stopped, 0], 'actual production boundary fields')
            mb = part(actual, *MAILBOX); words = list(struct.unpack('>64I', mb[:256]))
            need(mb[256:288] == PIXELS and mb[288:] == bytes(736), 'literal pixels and untouched mailbox tail')
            need(part(actual, MEMORY[0], 4096) == receive_literal(source), 'exact receive bytes/reused short suffix')
            need(part(actual, MEMORY[0] + 81936, 32768) == PIXELS + bytes(32736), 'exact output slots/tail')
            if label == 'pre-finish':
                need(words[16:21] == [352, 6, 6, 6, 6] and words[21] == 1, 'six fragments before explicit finish call')
                need(words[29:34] == [1, 1, 1, 32, fnv(PIXELS)] and words[34:40] == [1, 1, 1, 0, 1, 0], 'completed output and original event before finish')
            else:
                need(words == park_words(source), 'independent complete64-word mailbox')


def gunzip(root, name, limit):
    # CRC validation is supplied by gzip; the evidence seal is over raw records.
    with gzip.open(path(root, name), 'rb') as f:
        data = f.read(limit + 1)
    need(len(data) <= limit, 'bounded decompressed trace')
    return data


def memory_instruction(code):
    nibble = code[0] >> 4
    if nibble in (8, 9):
        return (1 if nibble == 8 else 2, 4)
    if nibble == 1:
        return (1, 4)
    if nibble == 2:
        return {0: (1, 1), 1: (1, 2), 2: (1, 4), 9: (1, 2),
                4: (2, 1), 5: (2, 2), 6: (2, 4)}.get(code[1] & 15)
    return None


def model_trace(folder, model, images, elf, cps):
    steps = gunzip(folder, 'traces/steps.bin.gz', 40_000_000)
    accesses = gunzip(folder, 'traces/accesses.bin.gz', 200_000_000)
    need(len(steps) % 4 == 0 and len(accesses) % 20 == 0 and steps, 'complete bounded trace records')
    need(sha(steps) == model['step_sha256'] and sha(accesses) == model['access_sha256'], 'raw uncompressed trace seals')
    pcs = [p[0] for p in struct.iter_unpack('>I', steps)]
    need(len(pcs) == model['instructions'] <= 10_000_000 and len(set(pcs)) == model['visited_instructions'], 'instruction trace counters')
    need(pcs[0] == ENTRY and pcs.count(ENTRY) == 1 and pcs[-2:] == [cps['park']] * 2 and
         all(pcs.count(at) == (2 if name == 'park' else 1) for name, at in cps.items()),
         'one entry, four unique checkpoints and two actual park iterations')
    need(jump_target(ENTRY, elf.instructions[ENTRY]) == pcs[1] == elf.symbol('hp1020_entry_normalize'), 'actual initial jump target')
    need(jump_target(cps['park'], elf.instructions[cps['park']]) == cps['park'], 'literal self-J target')
    ram = {a: bytearray(b) for a, b in images['initial'].items()}
    cursor = 0; counts = Counter(); widths = Counter(); seen = []; minimum = None
    pre_c_index = pcs.index(cps['pre-c'])
    call_index = 0; call_stack = []
    for i, pc in enumerate(pcs):
        need(pc in elf.instructions, 'executed PC is an annotated actual instruction boundary')
        code = elf.instructions[pc]
        need(code not in (b'\0\0\0', bytes.fromhex('d60f')), 'excluded illegal instruction executed')
        for label, at in cps.items():
            if pc == at and label not in seen:
                need(label == tuple(cps)[len(seen)], 'trace checkpoint order')
                need({a: bytes(b) for a, b in ram.items()} == images[label], 'replayed bytes at ' + label)
                seen.append(label)
        kind = memory_instruction(code)
        if kind:
            need(cursor + 20 <= len(accesses), 'missing memory access for actual memory instruction')
            chunk = accesses[cursor:cursor + 20]
            need(chunk[1:4] == bytes(3), 'access-record zero padding')
            k, at, address, size, value = struct.unpack('>B3xIIII', chunk)
            need(at == pc and (k, size) == kind and address % size == 0, 'access matches actual memory instruction')
            need(inside(address, size, elf.read_spans), 'no read/write in guard/gap/external/MMIO range')
            started = 'pre-c' in seen and i > pre_c_index
            if inside(address, size, (STACK,)):
                need(started, 'no inherited stack access')
                minimum = address if minimum is None else min(minimum, address)
            if k == 1:
                need(int.from_bytes(part(ram, address, size), 'big') == value, 'read record differs from actual preceding RAM')
                if code[0] >> 4 == 1:
                    immediate = int.from_bytes(code[1:], 'big') - 0x10000
                    target = (((pc + 3) & ~3) + immediate * 4) & 0xffffffff
                    need(address == target, 'actual L32R pointer')
            else:
                allowed = MUTABLE if started else ZERO if 'after-normalization' in seen else ()
                need(inside(address, size, allowed), 'phase write permission before effect')
                put(ram, address, (value & ((1 << (8 * size)) - 1)).to_bytes(size, 'big'))
            counts['read' if k == 1 else 'write'] += 1
            widths[('read' if k == 1 else 'write') + '/' + str(size)] += 1
            cursor += 20
        word = int.from_bytes(code, 'big')
        if len(code) == 3 and word & 0xfc0000 == 0x600000:
            need(jump_target(pc, code) == (pcs[i + 1] if i + 1 < len(pcs) else cps['park']),
                 'actual direct J target in step trace')
        direct_call = len(code) == 3 and word & 0xfc0000 == 0x500000
        indirect_call = len(code) == 3 and word & 0xff0fff == 0x030000
        is_return = code in (bytes.fromhex('020000'), bytes.fromhex('d00f'))
        if direct_call or indirect_call or is_return:
            need(i + 1 < len(pcs) and call_index < len(model['calls']), 'actual call/return evidence')
            event = model['calls'][call_index]; call_index += 1
            need(event['pc'] == pc and event['target'] == pcs[i + 1] and STACK[0] <= event['sp'] <= STACK[0] + STACK[1] and event['sp'] % 16 == 0, 'actual call location/target and owned aligned stack')
            if is_return:
                need(call_stack and event['kind'] == 'return' and event['depth'] == len(call_stack), 'real return has caller')
                previous = call_stack.pop()
                need(event['target'] == previous['return_pc'] and event['sp'] == previous['sp'], 'original call return/stack')
            else:
                need('pre-c' in seen and event['kind'] == 'call' and event['return_pc'] == pc + len(code) and event['depth'] == len(call_stack) + 1, 'real own call record')
                if call_index == 1:
                    need(pc == cps['pre-c'] and event['target'] == elf.symbol('hp1020_entry_c'), 'first and only entry-to-C call')
                if direct_call:
                    target = ((pc & ~3) + 4 + signed18(word & 0x3ffff) * 4) & 0xffffffff
                    need(event['target'] == target, 'literal CALL0 target')
                call_stack.append(event)
    need(cursor == len(accesses) and call_index == len(model['calls']) and not call_stack, 'complete memory/call traces')
    need(seen == list(PHASES[1:]) == model['checkpoints'], 'all four actual trace checkpoints')
    need({a: bytes(b) for a, b in ram.items()} == images['park'], 'all replayed final bytes equal capture')
    need(dict(counts) == model['access_count'] and dict(widths) == model['access_widths'], 'actual access counters')
    need(minimum == model['minimum_stack_access'] and minimum is not None, 'independent lowest stack access')
    need(STACK[0] <= model['minimum_sp'] <= minimum and model['owned_stack_bytes'] == 8192, 'bounded SP witness')
    need(model['terminal_self_branch_executions'] == 2 and model['terminal_self_branch_statically_checked'] is True,
         'terminal evidence matches actual trace/bytes')
    need(model['no_external_stack'] is True and model['host_runtime_mutations'] == 0, 'model declared scope')
    special = [('intenable', 0xe4, 0), ('lcount', 2, 0), ('lbeg', 0, 0),
               ('lend', 1, 0), ('ps', 0xe6, 15), ('windowbase', 0x48, 0), ('windowstart', 0x49, 1)]
    need(len(model['special_writes']) == len(special), 'seven explicit startup SR writes')
    for event, (name, number, value) in zip(model['special_writes'], special):
        at = event['pc']
        need(event == dict(pc=at, name=name, value=value) and
             elf.instructions.get(at) == bytes((2, number, 0x31)) and pcs.count(at) == 1 and
             elf.symbol('hp1020_entry_normalize') <= at < cps['after-normalization'],
             'actual one-shot admitted WSR prefix')


class Ledger:
    """Independent exact successful-command transcript, not the adapter guard."""
    def __init__(self, folder, report):
        seal = report['host_intervention_ledger']
        need(seal['path'] == 'host-interventions.jsonl', 'canonical host ledger')
        data = raw(folder, seal['path'], 16 * 1024 * 1024)
        need(sha(data) == seal['sha256'] and len(data) == seal['bytes'] and data.endswith(b'\n'), 'ledger raw seal')
        self.rows = [json.loads(line) for line in data.splitlines()]
        need(len(self.rows) == seal['lines'] and all(r['ledger_index'] == i for i, r in enumerate(self.rows)), 'complete indexed ledger')
        self.index = 0; self.commands = 0

    def take(self, kind):
        need(self.index < len(self.rows), 'missing ledger event ' + kind)
        row = self.rows[self.index]; self.index += 1
        need(row['kind'] == kind, 'unexpected ledger kind before ' + kind)
        return row

    def command(self, cmd, phase, action, expected=None):
        request = self.take('gdb-request')
        need(request['command'] == cmd and request['command_index'] == self.commands and
             request['phase'] == phase and request['action'] == action, 'exact permitted debugger command envelope')
        reply = self.take('gdb-reply')
        need(reply['command_index'] == self.commands and isinstance(reply['reply'], str), 'complete command/reply pairing')
        self.commands += 1
        value = reply['reply']
        if expected is not None:
            need(value == expected, 'actual debugger reply mismatch')
        return value

    def read(self, address, count, expected):
        value = self.command(f'm{address:x},{count:x}', 'observe', 'read-memory')
        need(len(value) == count * 2 and bytes.fromhex(value) == expected, 'debugger memory reply vs saved raw bytes')

    def reg(self, number, expected):
        value = self.command(f'p{number:x}', 'observe', 'read-register')
        need(len(value) == 8 and int(value, 16) == expected, 'debugger register reply vs saved register')

    def snapshot(self, item, images):
        label = item['name']; start = self.take('snapshot-start')
        need(start['name'] == label, 'snapshot marker order')
        regs = item['registers']
        for name, number in GDB.items():
            self.reg(number, regs[name])
        for i, v in enumerate(regs['physical_ar'], 1):
            self.reg(i, v)
        for i, v in enumerate(regs['logical_a'], 124):
            self.reg(i, v)
        for a, n in REGIONS:
            for off in range(0, n, 4096):
                count = min(4096, n - off)
                self.read(a + off, count, images[label][a][off:off + count])
        end = self.take('snapshot-end')
        need(end['name'] == label and end['status'] == 'complete', 'completed snapshot marker')


def qemu_ledger(folder, q, images, supplied, checkpoints, source_map):
    need(q['status'] == 'pass' and q == js(folder, 'result.json'), 'actual QEMU result')
    need(q['checkpoints'] == [[n, a] for n, a in checkpoints.items()], 'QEMU actual checkpoint identities')
    need(q['source_sha256'] == js(folder, 'source/sha256.json'), 'QEMU source manifest')
    for name, digest in q['source_sha256'].items():
        need(digest_shape(digest) and sha(raw(folder, 'source/' + name)) == digest, 'actual QEMU captured source bytes')
    expected_sources = {'hp1020_entry_qemu.py': source_map['scripts/hp1020_entry_qemu.py'],
                        'hp1020_qemu_ram.py': BACKEND_HASH,
                        **{'qemu-primary/' + k: v for k, v in PRIMARY.items()}}
    need(q['source_sha256'] == expected_sources, 'independent QEMU source closure')
    actual_sources = {str(p.relative_to(folder / 'source')) for p in (folder / 'source').rglob('*') if p.is_file()}
    need(actual_sources == set(expected_sources) | {'sha256.json'}, 'exact QEMU saved source files')
    identity = q['qemu']
    need(identity['version'] == 'QEMU emulator version 11.1.1' and identity['core'] == 'test_kc705_be' and identity['machine'] == 'sim' and digest_shape(identity['binary_sha256']), 'actual selected emulator identity')
    args = identity['args']
    need(len(args) == 19 and args[1:-1] == ['-M', 'sim', '-cpu', 'test_kc705_be', '-m', '1G',
         '-nodefaults', '-display', 'none', '-serial', 'none', '-monitor', 'none', '-nic', 'none', '-S', '-gdb'] and
         args[-1].startswith('unix:/tmp/hp1020-qemu-') and args[-1].endswith('/gdb.sock,server=on,wait=off'), 'isolated stopped sim launch')
    need(js(folder, 'input/registers.json') == supplied and js(folder, 'input/checkpoints.json') == q['checkpoints'], 'QEMU exact supplied inputs')
    need(len(q['initial_regions']) == 7, 'QEMU initial region records')
    for row, (a, n) in zip(q['initial_regions'], REGIONS):
        need(row['start'] == a and row['bytes'] == n and row['path'] == f'input/region-{a:08x}-{n:08x}.bin', 'QEMU original region identity')
        value = raw(folder, row['path'])
        need(value == images['initial'][a] and sha(value) == row['sha256'], 'actual QEMU initial supplied bytes')
    ledger = Ledger(folder, q)
    admit = ledger.take('admitted-input')
    need(admit['registers'] == supplied and admit['checkpoints'] == q['checkpoints'] and admit['region_sha256'] == q['initial_regions'], 'actual admitted input ledger')
    ledger.command('qSupported', 'constructor', 'bootstrap')
    for cmd in ('Hg0', 'Z0,23000000,1', 'z0,23000000,1'):
        ledger.command(cmd, 'constructor', 'bootstrap', 'OK')
    seed_count = 0
    for a, n in REGIONS:
        data = images['initial'][a]
        for off in range(0, n, 4096):
            chunk = data[off:off + 4096]
            ledger.command(f'M{a + off:x},{len(chunk):x}:' + chunk.hex(), 'seed', 'initial-seed', 'OK')
            seed_count += 1
    for name in ('windowbase', 'windowstart', 'ps', 'intenable', 'lbeg', 'lend', 'lcount', 'sar'):
        ledger.command(f'P{GDB[name]:x}={supplied[name]:08x}', 'seed', 'initial-seed', 'OK'); seed_count += 1
    for i, v in enumerate(supplied['physical_ar'], 1):
        ledger.command(f'P{i:x}={v:08x}', 'seed', 'initial-seed', 'OK'); seed_count += 1
    ledger.command(f'P0={ENTRY:08x}', 'seed', 'initial-seed', 'OK'); seed_count += 1
    locked = ledger.take('initial-state-locked')
    need(locked['seed_commands'] == seed_count == q['initial_seed_commands'] and locked['gdb_commands'] == ledger.commands, 'one complete seed before lock')
    ledger.snapshot(q['snapshots'][0], images)
    for item, (label, address) in zip(q['snapshots'][1:5], checkpoints.items()):
        code = part(images['initial'], address, 3)
        ledger.command(f'Z0,{address:x},1', 'observe', 'add-breakpoint', 'OK')
        ledger.read(address, 3, code)
        reply = ledger.command('c', 'observe', 'continue-current-pc')
        need(reply.startswith('T05'), 'actual continue stop')
        ledger.reg(0, address)
        ledger.snapshot(item, images)
        ledger.command(f'z0,{address:x},1', 'observe', 'remove-breakpoint', 'OK')
        ledger.read(address, 3, code)
    park = checkpoints['park']; code = part(images['initial'], park, 3)
    ledger.read(park, 3, code)
    need(q['park_instruction_hex'] == code.hex() and jump_target(park, code) == park, 'real terminal self-J bytes')
    for item in q['snapshots'][5:]:
        need(ledger.command('s', 'observe', 'single-step-park').startswith('T05'), 'actual park step stop')
        ledger.snapshot(item, images)
    cleanup = ledger.take('process-cleanup')
    need({k: v for k, v in cleanup.items() if k not in ('kind', 'ledger_index')} == q['cleanup'], 'actual cleanup ledger')
    need(not q['cleanup']['errors'] and q['cleanup']['still_running'] is False and q['cleanup']['returncode'] is not None, 'child stopped and reaped')
    end = ledger.take('adapter-finished')
    need(end['status'] == 'pass' and end.get('error') is None and ledger.index == len(ledger.rows) and ledger.commands == q['gdb_commands'] <= 4096, 'complete ledger without hidden traffic')
    need(q['reset_calls'] == q['call_helpers'] == q['memory_or_register_writes_after_lock'] == 0 and q['resume_attempted'] is True and q['checkpoint_stop_observed'] is True, 'declared counters agree with independently reconstructed ledger')


def check_capture(capture_root, source_root=None):
    """Return (bool, detail); read-only even when checking deliberately bad copies."""
    try:
        root = Path(capture_root).resolve()
        report = js(root, 'validation.json')
        need(report['status'] == 'pass' and report['candidate_execution'] is True and
             'error' not in report and 'source_seal_error' not in report,
             'completed candidate execution required')
        sources = js(root, 'source-sha256.json')
        need(sources == report['source_sha256'], 'source closure report')
        seal_tree(root, 'source', sources)
        seal_tree(root, 'target', report['target_sha256'])
        required_sources = ('scripts/check-hp1020-entry-ram.py', 'scripts/validate-hp1020-entry-ram.py',
            'scripts/hp1020_entry_machine.py', 'scripts/hp1020_entry_qemu.py', 'scripts/hp1020_entry_audit.py',
            'scripts/build-hp1020-entry-ram-target.sh', 'open-firmware/entry-ram-test/startup.S',
            'open-firmware/entry-ram-test/entry.ld', 'open-firmware/entry-ram-test/hp1020_entry_workload.c',
            'open-firmware/entry-ram-test/hp1020_entry_layout.c',
            'open-firmware/usb-receive-core/hp1020_usb_receive.c',
            'open-firmware/usb-receive-core/hp1020_usb_document.c',
            'open-firmware/image-core/hp1020_image.c', 'open-firmware/image-core/hp1020_image_page.c',
            'open-firmware/image-core/hp1020_image_stream.c', 'open-firmware/image-core/hp1020_image_ring.c',
            'open-firmware/image-core/hp1020_image_output.c', 'open-firmware/image-core/target-memory.c',
            'open-firmware/semantic-core/hp1020_semantic.c', 'open-firmware/semantic-core/hp1020_page_plan.c',
            'open-firmware/semantic-core/freestanding/memory.c', 'vendor/jbigkit-2.1/libjbig/jbig85.c',
            'vendor/jbigkit-2.1/libjbig/jbig_ar.c')
        need(set(required_sources) <= set(sources), 'required complete built-source members')
        for name, digest in {'scripts/hp1020_qemu_ram.py': BACKEND_HASH,
             'open-firmware/entry-ram-test/literal-oracle.py': ORACLE_HASH,
             'open-firmware/entry-ram-test/expected-target32.json': LAYOUT_HASH}.items():
            need(sources.get(name) == digest, 'frozen independent/reference source: ' + name)
        for name, digest in PRIMARY.items():
            need(sources.get('open-firmware/entry-ram-test/references/qemu-primary/' + name) == digest, 'pinned primary byte seal')
        if source_root is not None:
            live = Path(source_root).resolve()
            for name, digest in sources.items():
                need(sha(raw(live, name)) == digest, 'current source differs from exact tested capture: ' + name)
        source = input_literal()
        need(len(source) == 352 and raw(root, 'input/small-black.zjs') == source and raw(root, 'input/small-black.jbg') == BIE, 'independent exact input bytes')
        need(sha(raw(root, 'input/matrix-a4_default.zjs')) == SAMPLE_HASH, 'original host fixture bytes')
        provenance = js(root, 'input/provenance.json')
        need(provenance == report['input'] and provenance['input_sha256'] == sha(source) and provenance['source_sha256'] == SAMPLE_HASH and provenance['small_jbig_sha256'] == sha(BIE) and provenance['bytes'] == 352 and provenance['independent_literal_match'] is True, 'input provenance')
        elf_data = raw(root, 'target/entry-ram.elf'); elf = Elf(elf_data)
        need(js(root, 'elf-loads.json') == elf.loads, 'actual ELF load metadata')
        need(elf.file(elf.symbol('hp1020_entry_input', 352), 352) == source, 'actual linked const input')
        for name, wanted in (('state', STATE), ('memory', MEMORY), ('mailbox', MAILBOX), ('data', DATA)):
            need(elf.symbol('hp1020_entry_' + name, wanted[1]) == wanted[0], 'actual object symbol extent')
        address = elf.symbol('hp1020_entry_layout', 260)
        words = struct.unpack('>65I', elf.file(address, 260))
        need(words == LAYOUT_WORDS and inside(address, 260, [(elf.alloc['.rodata'][3], elf.alloc['.rodata'][5])]), 'independent literal target32 layout')
        witness = js(root, 'layout-witness.json')
        need(witness == dict(status='pass', address=address, words=list(words), sha256=sha(elf.file(address, 260)), expected_sha256=LAYOUT_HASH), 'actual layout witness metadata')
        cps = dict(zip(PHASES[1:], (elf.symbol(n) for n in CP_SYMBOLS)))
        need(len(set(cps.values())) == 4 and js(root, 'checkpoints.json') == [[n, a] for n, a in cps.items()], 'actual linked checkpoints')
        need(all(a in elf.instructions for a in cps.values()), 'annotated checkpoint boundaries')
        audit = js(root, 'linked-audit.json')
        need(audit == report['linked_audit'] and audit['target_sha256'] == sha(elf_data) and audit['target_bytes'] == len(elf_data) and audit['entry'] == ENTRY, 'sealed linked audit identity')
        need(audit['audit_source_sha256'] == sources['scripts/hp1020_entry_audit.py'], 'actual audit source identity')
        need(sha(raw(root, 'annotated-disassembly.txt')) == audit['disassembly_sha256'],
             'actual annotated disassembly byte seal')
        tools = js(root, 'tool-closure.json'); need(tools == report['tool_closure'], 'tool closure metadata')
        for name in ('compiler', 'assembler', 'linker', 'objdump', 'nm', 'readelf', 'libgcc', 'gcc-selected-cc1', 'gcc-selected-as', 'gcc-selected-ld', 'gcc-selected-collect2'):
            need(digest_shape(tools[name]['sha256']) and isinstance(tools[name]['path'], str), 'recorded actual tool identity')
        for name in ('configuration', 'specs', 'search-directories'):
            need(sha(raw(root, 'compiler-' + name + '.txt')) == tools['compiler-' + name], 'compiler configuration bytes')
        need(tools['compiler_headers'], 'preserved compiler header closure')
        for data in tools['compiler_headers'].values():
            need(sha(raw(root, data['snapshot'])) == data['sha256'], 'actual compiler-header bytes')
        dep_files = [name for name in report['target_sha256'] if name.endswith('.d')]
        need(len(dep_files) == 15, 'fifteen compiled C dependency captures')
        for name in dep_files:
            dependency_text = raw(root, 'target/' + name).decode().replace('\\\n', ' ')
            need(':' in dependency_text, 'dependency rule')
            for dependency in dependency_text.split(':', 1)[1].split():
                dependency = posixpath.normpath(dependency)
                source_matches = [p for p in sources if dependency.endswith('/' + p)]
                target_matches = [p for p in report['target_sha256'] if dependency.endswith('/analysis/boot-handoff/entry-ram/target/' + p)]
                # macOS captures resolve /tmp and /var through /private. Keep
                # this lexical so a saved archive needs no surviving toolchain.
                aliases = {dependency}
                if dependency.startswith(('/tmp/', '/var/')):
                    aliases.add('/private' + dependency)
                need(len(source_matches) == 1 or len(target_matches) == 1 or aliases & set(tools['compiler_headers']),
                     'every actual compiler dependency has captured bytes: ' + dependency)
        need(len(report['cases']) == 6, 'exact six paired CPU/paint profiles')
        expected_dirs = set()
        total_steps = 0
        for index, case in enumerate(report['cases']):
            pi = index // 2; fills = PAINTS[index % 2]
            name = f'{index:02d}-{CPU[pi]["name"]}-{fills[0]:02x}'; expected_dirs.add(name)
            folder = root / 'cases' / name
            need(case == js(folder, 'case.json') and case['case'] == name and case['status'] == 'pass' and case['cpu_profile'] == CPU[pi] and case['paints'] == list(fills) and case['paired_checkpoints'] == 5, 'literal case matrix/profile identity')
            supplied = cpu_initial(pi); need(js(folder, 'initial-registers.json') == supplied, 'literal32 physical ARs')
            initial = make_initial(elf, fills)
            model = case['model']; q = case['qemu']
            need(model == js(folder / 'model', 'result.json') and model['status'] == 'pass' and model['snapshots'] == js(folder / 'model', 'snapshots.json'), 'model metadata seals')
            mi = snapshots(folder / 'model', model['snapshots'], PHASES)
            qi = snapshots(folder / 'qemu', q['snapshots'], QPHASES, True)
            semantic_snapshots(model['snapshots'], mi, initial, supplied, cps, source)
            semantic_snapshots(q['snapshots'], qi, initial, supplied, cps, source, True)
            for m, qq in zip(model['snapshots'], q['snapshots'][:5]):
                need(registers(m['registers']) == registers(qq['registers'], True) and mi[m['name']] == qi[qq['name']], 'paired complete registers/regions')
            for s in q['snapshots'][5:]:
                need(s['registers'] == q['snapshots'][4]['registers'] and qi[s['name']] == qi['park'], 'two unchanged actual park steps')
            painted = part(mi['park'], *STACK)
            changed = [i for i, b in enumerate(painted) if b != fills[1]]
            expected_paint = dict(initial_byte=fills[1], changed_bytes=len(changed), lowest_changed_address=STACK[0] + min(changed) if changed else None)
            need({k: case['stack_paint'][k] for k in expected_paint} == expected_paint and changed and
                 isinstance(case['stack_paint'].get('limitation'), str), 'independent full stack-paint witness')
            model_trace(folder / 'model', model, mi, elf, cps)
            qemu_ledger(folder / 'qemu', q, qi, supplied, cps, sources)
            total_steps += model['instructions']
        need({p.name for p in (root / 'cases').iterdir() if p.is_dir()} == expected_dirs, 'no extra/missing case directories')
        return True, dict(cases=6, paired_checkpoints=30, qemu_park_steps=12,
                          model_instructions=total_steps, target_sha256=sha(elf_data),
                          scope='Independent saved bytes, literal results, access replay and debugger transcript; no physical boot/printing claim.')
    except Exception as error:
        return False, dict(error=type(error).__name__ + ': ' + str(error))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture_root'); parser.add_argument('--source-root')
    args = parser.parse_args()
    ok, detail = check_capture(args.capture_root, args.source_root)
    print(json.dumps(dict(ok=ok, detail=detail), sort_keys=True, indent=2))
    raise SystemExit(0 if ok else 1)


if __name__ == '__main__':
    main()
