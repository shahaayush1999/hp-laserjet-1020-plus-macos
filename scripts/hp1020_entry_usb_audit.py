"""UNEXECUTED draft: strict ELF audit for the new entry-owned RAM USB runtime.

No target execution or device operations. Only corrected objdump is invoked.
This profile reuses unchanged neutral ELF/byte helpers from the accepted entry
experiment, never its old layout, permissions, startup checks or mutable globals.
The caller must preserve all returned evidence, objects, dependencies and actual
source bytes before running any target. No physical loader/RAM/cache claim.
"""
from __future__ import annotations

from collections import Counter
import csv
import io
import json
import re
from pathlib import Path
import shlex
import struct

import hp1020_entry_audit as neutral

require = neutral.require
digest = neutral.digest
inside = neutral.inside
merge = neutral.merge
file_bytes = neutral.file_bytes

ENTRY = 0x100167a8
MAIN = (0x10003000, 0x100351e0)
STACK = (0x10014020, 8192)
PIN = 'dae3f9a366bfcddbf9dcf1b48d7500286a849539'
PRIVATE_PROOF_SHA256 = 'a304d09a141b9b5671dabeeb65ccd1de42393ed88ef2a747564b64bc6500b273'
INPUT_SHA256 = 'ad339333c0d37ee41da13849184caebec4b55d8f913eb30f9565e30cd33a062d'
DATA_PATTERN = bytes.fromhex('31527394b5d6f718395a7b9cbddeff20') * 16
SCRIPT_PINS = {
    'hp1020_entry_audit.py': '2f990f9f57731c49d8931138d32ce100fecd1d2fed722354f6c01117e52042eb',
    'hp1020_xtensa_call0.py': 'ed2924d8e46c0e553fe079a5ecdfff77dc40f1aa228588d9a86c39ce98769480',
    'hp1020_xtensa_properties.py': '8a98e5ba3ead469cd431a06260e78c836993348d878ae96595d0b622538d0280',
}
CONTRACT_PINS = {
    'hp1020_usb_runtime_contract.h': '25f5e76cff3633d6e3ab85f4e9adfc2e94edcc02e2cfe0b7d7d2bafea2e82995',
    'layout-objects.tsv': '9eb91e5bc6565773758f9fad22498e639b64289a1a9060adb0a2456637dee012',
    'layout-fields.tsv': '0a810d9c44f99f8507d2338e9a1fa0e0f307606361ee03f536ca0935fd4d2008',
    'startup.S': 'c8271bbea0fdc7ed4ffb4c18469a15d91170d26c948d41e3706e8ed95922bad6',
    'runtime.ld': '235934f043f7b18741a1db960fd8a129d64e5075dad55b8aca87c2988348d74d',
}
REPO_PINS = {
    'vendor/tinyusb-0.21.0/PROVENANCE.json': '31ee172160e0c9e51cec7fa0e3e9348e4b20b92493743849fcba649542eae2e0',
    'open-firmware/tinyusb-device/tusb_config.h': '895c6599700b09f84be46ce74ac75f3974ce3b277d98f233134a54aea637616a',
    'open-firmware/tinyusb-device/patches/protocol-compatibility.patch': '9f334e5cff0086e4d87de7cc9393cf2e204ae601112efefa9a6fd3c96293919d',
    'open-firmware/tinyusb-device/patches/manifest.json': 'f9b14a4e4cf1313e43cad973ad7cb4e331ecd94398ecdca7a3a7a5fbba9cc94c',
}
C_UNITS = {
    'hp1020_usb_runtime', 'hp1020_usb_runtime_ram', 'hp1020_usb_runtime_layout',
    'hp1020_udc_publish', 'hp1020_udc_program', 'hp1020_udc_ep0', 'hp1020_udc_out',
    'hp1020_udc_setup', 'hp1020_tusb_adapter', 'hp1020_usb_printer',
    'hp1020_usb_receive', 'hp1020_usb_document', 'hp1020_image', 'hp1020_image_page',
    'hp1020_image_stream', 'hp1020_image_ring', 'hp1020_image_output',
    'hp1020_semantic', 'hp1020_page_plan', 'target-memory', 'memory',
    'jbig85', 'jbig_ar', 'tusb', 'usbd', 'tusb_fifo',
}
SOURCE_UNITS = {
    'hp1020_udc_publish': 'open-firmware/udc-publish/hp1020_udc_publish.c',
    'hp1020_udc_program': 'open-firmware/udc-program/hp1020_udc_program.c',
    'hp1020_udc_ep0': 'open-firmware/udc-ep0/hp1020_udc_ep0.c',
    'hp1020_udc_out': 'open-firmware/udc-out/hp1020_udc_out.c',
    'hp1020_udc_setup': 'open-firmware/udc-setup/hp1020_udc_setup.c',
    'hp1020_tusb_adapter': 'open-firmware/tinyusb-printer-adapter/hp1020_tusb_adapter.c',
    'hp1020_usb_printer': 'open-firmware/usb-printer-class/hp1020_usb_printer.c',
    'hp1020_usb_receive': 'open-firmware/usb-receive-core/hp1020_usb_receive.c',
    'hp1020_usb_document': 'open-firmware/usb-receive-core/hp1020_usb_document.c',
    'hp1020_image': 'open-firmware/image-core/hp1020_image.c',
    'hp1020_image_page': 'open-firmware/image-core/hp1020_image_page.c',
    'hp1020_image_stream': 'open-firmware/image-core/hp1020_image_stream.c',
    'hp1020_image_ring': 'open-firmware/image-core/hp1020_image_ring.c',
    'hp1020_image_output': 'open-firmware/image-core/hp1020_image_output.c',
    'hp1020_semantic': 'open-firmware/semantic-core/hp1020_semantic.c',
    'hp1020_page_plan': 'open-firmware/semantic-core/hp1020_page_plan.c',
    'target-memory': 'open-firmware/image-core/target-memory.c',
    'memory': 'open-firmware/semantic-core/freestanding/memory.c',
    'jbig85': 'vendor/jbigkit-2.1/libjbig/jbig85.c',
    'jbig_ar': 'vendor/jbigkit-2.1/libjbig/jbig_ar.c',
}
# Whole target32 mutable globals outside the approved sixteen public objects.
# Values are (size, defining input unit, linked output section).
PRIVATE_MUTABLE = {
    'bound': (4, 'hp1020_tusb_adapter', '.bss'),
    '_tusb_rhport_role': (8, 'tusb', '.bss'),
    '_usbd_q': (4, 'usbd', '.bss'),
    '_usbd_qdef_buf': (192, 'usbd', '.bss'),
    '_app_driver_count': (1, 'usbd', '.bss'),
    '_app_driver': (4, 'usbd', '.bss'),
    '_ctrl_epbuf': (64, 'usbd', '.bss'),
    '_usbd_queued_setup': (1, 'usbd', '.bss'),
    '_usbd_dev': (68, 'usbd', '.bss'),
    '_usbd_qdef': (20, 'usbd', '.data'),
    '_usbd_spin': (8, 'usbd', '.data'),
    '_usbd_rhport': (1, 'usbd', '.data'),
}
PUBLIC_CUSTOM = {
    'hp1020_usb_runtime_document': ('.runtime_document', '.bss'),
    'hp1020_usb_runtime_memory': ('.runtime_memory', '.runtime_memory'),
    'hp1020_usb_runtime_mailbox': ('.runtime_mailbox', '.runtime_mailbox'),
    'hp1020_usb_runtime_witness': ('.runtime_witness', '.runtime_witness'),
    'hp1020_usb_runtime_sentinel': ('.runtime_sentinel', '.runtime_sentinel'),
}
FIXED = {
    '.WindowVectors.text': (0x10000000, 0x180, 1, 6),
    '.KernelExceptionVector.literal': (0x10000180, 4, 1, 2),
    '.KernelExceptionVector.text': (0x10000200, 0x1c, 1, 6),
    '.UserExceptionVector.literal': (0x1000021c, 4, 1, 2),
    '.UserExceptionVector.text': (0x10000220, 0x1c, 1, 6),
    '.DoubleExceptionVector.text': (0x10000270, 0xe0, 1, 6),
    '.sys_interface_table': (0x10000370, 0x12c, 1, 2),
    '.runtime_stack': (0x10014020, 8192, 8, 3),
    '.runtime_mailbox': (0x10016060, 1024, 8, 3),
    '.runtime_sentinel': (0x10016500, 256, 1, 3),
    '.entry_island': (0x10016780, 0x60, 1, 6),
    '.runtime_memory': (0x10016800, 114704, 8, 3),
    '.runtime_witness': (0x10032830, 9216, 8, 3),
    '.ResetVector.text': (0x10100020, 0x2e0, 1, 6),
    '.DebugExceptionVector.literal': (0x10100300, 4, 1, 2),
    '.DebugExceptionVector.text': (0x10100320, 0xc, 1, 6),
}
GUARDS = {
    'code_guard_hi': (0x1000ffe0, 0x10010000),
    'state_guard_lo': (0x1000ffe0, 0x10010000),
    'state_guard_hi': (0x10013fe0, 0x10014000),
    'stack_guard_lo': (0x10014000, 0x10014020),
    'stack_guard_hi': (0x10016020, 0x10016040),
    'mailbox_guard_lo': (0x10016040, 0x10016060),
    'mailbox_guard_hi': (0x10016460, 0x10016480),
    'data_guard_lo': (0x10016480, 0x100164a0),
    'data_guard_hi': (0x10016600, 0x10016620),
    'pre_island_gap': (0x10016620, 0x10016780),
    'memory_guard_lo': (0x100167e0, 0x10016800),
    'memory_guard_hi': (0x10032810, 0x10032830),
    'witness_guard_lo': (0x10032810, 0x10032830),
    'witness_guard_hi': (0x10034ff0, 0x10035010),
    'tail_gap': (0x10035010, 0x100351e0),
}


def sealed(path, expected=None):
    path = Path(path)
    raw = path.read_bytes()
    actual = digest(raw)
    require(expected is None or actual == expected, 'source pin differs', str(path), actual, expected)
    return raw, dict(file=str(path), bytes=len(raw), sha256=actual)


def contract_inputs(root):
    source = root / 'open-firmware/entry-usb-test'
    evidence = []
    for name, expected in SCRIPT_PINS.items():
        _, row = sealed(Path(neutral.__file__).parent / name, expected)
        evidence.append(row)
    for name, expected in REPO_PINS.items():
        _, row = sealed(root / name, expected)
        evidence.append(row)
    raw_tables = {}
    for name, expected in CONTRACT_PINS.items():
        raw, row = sealed(source / name, expected)
        evidence.append(row)
        raw_tables[name] = raw
    objects = list(csv.DictReader(io.StringIO(raw_tables['layout-objects.tsv'].decode('ascii')), delimiter='\t'))
    fields = list(csv.DictReader(io.StringIO(raw_tables['layout-fields.tsv'].decode('ascii')), delimiter='\t'))
    require(len(objects) == 16 and len(fields) == 101, 'frozen manual table counts')
    object_rows = [dict(id=int(r['id']), name=r['symbol'], size=int(r['target32_size']),
                        alignment=int(r['type_alignment']), type=r['type_or_array']) for r in objects]
    field_rows = [dict(id=int(r['id']), object_id=int(r['object_id']), member=r['member'],
                       offset=int(r['target32_offset']), width=int(r['width'])) for r in fields]
    require([r['id'] for r in object_rows] == list(range(1, 17)) and
            [r['id'] for r in field_rows] == list(range(1, 102)), 'manual table IDs')
    return source, object_rows, field_rows, evidence


def mutable_expectations(objects):
    expected = {r['name']: dict(size=r['size'], alignment=r['alignment'],
                units={'hp1020_usb_runtime', 'hp1020_usb_runtime_ram'},
                section=PUBLIC_CUSTOM.get(r['name'], ('', '.bss'))[1]) for r in objects}
    expected['hp1020_usb_runtime_sentinel'] = dict(size=256, alignment=1,
        units={'hp1020_usb_runtime', 'hp1020_usb_runtime_ram'}, section='.runtime_sentinel')
    for name, (size, unit, section) in PRIVATE_MUTABLE.items():
        alignment = 1 if name in ('_usbd_qdef_buf', '_app_driver_count', '_usbd_queued_setup', '_usbd_rhport') else 4
        expected[name] = dict(size=size, alignment=alignment,
                             units={unit}, section=section)
    return expected


def check_layout(elf, data, objects):
    sections, symbols = elf['sections'], elf['symbols']
    allocated = {n: s for n, s in sections.items() if s['flags'] & 2 and s['size']}
    require(len(allocated) == 20 and set(allocated) == set(FIXED) | {'.text', '.rodata', '.bss', '.data'},
            'exact twenty allocated sections', sorted(allocated))
    for name, expected in FIXED.items():
        require(tuple(allocated[name][k] for k in ('address', 'size', 'type', 'flags')) == expected,
                'fixed allocation differs', name, allocated[name], expected)
    text, rodata, bss, data_sec = [allocated[n] for n in ('.text', '.rodata', '.bss', '.data')]
    require((text['address'], text['type'], text['flags']) == (0x10003000, 1, 6) and text['size'] > 36,
            'text profile')
    require((rodata['type'], rodata['flags']) == (1, 2) and
            rodata['address'] == ((text['address'] + text['size'] + 3) & ~3), 'rodata profile/gap')
    code_end = rodata['address'] + rodata['size']
    require(code_end <= 0x1000ffe0, 'code budget overflow', code_end)
    require((bss['address'], bss['type'], bss['flags']) == (0x10010000, 8, 3) and
            13496 < bss['size'] <= 0x3fe0 and bss['size'] % 4 == 0, 'actual generic BSS profile', bss)
    require((data_sec['address'], data_sec['type'], data_sec['flags']) == (0x100164a0, 1, 3) and
            0 < data_sec['size'] <= 96, 'actual initialized data profile', data_sec)
    merge([(s['address'], s['address'] + s['size']) for s in allocated.values()])
    expected_loads = [
        (0x10000000, 0x184, 0x184, 5), (0x10000200, 0x3c, 0x3c, 5),
        (0x10000270, 0xe0, 0xe0, 5), (0x10000370, 0x12c, 0x12c, 4),
        (0x10003000, code_end - 0x10003000, code_end - 0x10003000, 5),
        (0x10010000, 0, bss['size'], 6), (0x10014020, 0, 8192, 6),
        (0x10016060, 0, 1024, 6), (0x100164a0, data_sec['size'], data_sec['size'], 6),
        (0x10016500, 256, 256, 6), (0x10016780, 0x60, 0x60, 5),
        (0x10016800, 0, 114704, 6), (0x10032830, 0, 9216, 6),
        (0x10100020, 0x2e4, 0x2e4, 5), (0x10100320, 0xc, 0xc, 5),
    ]
    actual = [tuple(p[k] for k in ('address', 'filesz', 'memsz', 'flags')) for p in elf['loads']]
    require(actual == expected_loads, 'exact fifteen PT_LOAD footprints/tails', actual)
    for s in allocated.values():
        owners = [p for p in elf['loads'] if inside(s['address'], s['size'], p['address'], p['address'] + p['memsz'])]
        require(len(owners) == 1, 'section load owner', s['name'])
        p = owners[0]
        if s['type'] == 8:
            require(p['filesz'] == 0, 'NOLOAD must have no file tail', s['name'])
        else:
            require(s['offset'] == p['offset'] + s['address'] - p['address'] and
                    s['address'] + s['size'] <= p['address'] + p['filesz'], 'section file mapping', s['name'])
    metadata = {'', '.xt.prop', '.xt.lit', '.xt.insn', '.xtensa.info', '.symtab', '.strtab',
                '.shstrtab', '.debug_line', '.debug_info', '.debug_abbrev', '.debug_aranges', '.debug_str'}
    for name, s in sections.items():
        require(not s['size'] or name in allocated or (name in metadata and not s['flags'] & 7),
                'unexpected nonload section', name)
    pairs = dict(GUARDS, main=MAIN, code=(text['address'], code_end),
                 rodata=(rodata['address'], code_end))
    names = {'window': '.WindowVectors.text', 'kernel_literal': '.KernelExceptionVector.literal',
        'kernel': '.KernelExceptionVector.text', 'user_literal': '.UserExceptionVector.literal',
        'user': '.UserExceptionVector.text', 'double': '.DoubleExceptionVector.text',
        'interface': '.sys_interface_table', 'state': '.bss', 'stack': '.runtime_stack',
        'mailbox': '.runtime_mailbox', 'data': '.data', 'sentinel': '.runtime_sentinel',
        'island': '.entry_island', 'memory': '.runtime_memory', 'witness': '.runtime_witness',
        'reset': '.ResetVector.text', 'debug_literal': '.DebugExceptionVector.literal', 'debug': '.DebugExceptionVector.text'}
    for name, section in names.items():
        s = allocated[section]
        pairs[name] = (s['address'], s['address'] + s['size'])
    caps = {'code': 0x1000ffe0, 'state': 0x10013fe0, 'data': 0x10016500, 'witness': 0x10034ff0}
    for name, cap in caps.items():
        require(symbols.get('__hp1020_entry_' + name + '_cap') == cap, 'budget cap symbol', name)
        pairs[name + '_unused'] = (pairs[name][1], cap)
    for name, (a, b) in pairs.items():
        require(symbols.get('__hp1020_entry_' + name + '_start') == a and
                symbols.get('__hp1020_entry_' + name + '_end') == b, 'exact span symbols', name)
    require(symbols.get('__hp1020_entry_text_end') == text['address'] + text['size'], 'text end')
    require(symbols.get('__hp1020_runtime_document_start') == 0x10010000 and
            symbols.get('__hp1020_runtime_document_end') == 0x10010000 + 13496 and
            symbols.get('__hp1020_runtime_other_bss_start') == 0x10010000 + 13496, 'document first in BSS')
    bss_raw_end = symbols.get('__hp1020_runtime_bss_unaligned_end', -1)
    require(0 <= pairs['state'][1] - bss_raw_end < 4 and bss_raw_end >= 0x10010000 + 13496,
            'generic BSS trailing alignment only')
    require(symbols.get('__hp1020_runtime_witness_unaligned_end') == 0x10032830 + 9216,
            'witness used end')
    require(elf['entry'] == ENTRY == symbols.get('hp1020_entry_start') == symbols.get('_start'), 'entry')
    expected = mutable_expectations(objects)
    observed = {}
    for r in elf['symbol_records']:
        if r['section'] >= len(elf['indexed']):
            continue
        s = elf['indexed'][r['section']]
        if r['size'] and r['type'] in (1, 2):
            require(inside(r['address'], r['size'], s['address'], s['address'] + s['size']),
                    'object/function outside defining section', r)
        if r['type'] == 1 and s['flags'] & 3 == 3:
            require(r['name'] in expected and r['name'] not in observed, 'unexpected/duplicate mutable object', r)
            want = expected[r['name']]
            require(r['size'] == want['size'] and s['name'] == want['section'] and
                    r['address'] % want['alignment'] == 0, 'mutable object shape', r, want)
            observed[r['name']] = dict(r, output_section=s['name'])
    require(set(observed) == set(expected), 'incomplete mutable symbol closure', sorted(set(expected) - set(observed)))
    merge([(r['address'], r['address'] + r['size']) for r in observed.values()])
    for name, section in PUBLIC_CUSTOM.items():
        require(observed[name]['address'] == allocated[section[1]]['address'], 'custom object start', name)
    require(bss_raw_end == max(r['address'] + r['size'] for r in observed.values() if r['output_section'] == '.bss'),
            'anonymous trailing BSS allocation')
    require(file_bytes(data, sections, 0x10016500, 256) == DATA_PATTERN, 'immutable sentinel bytes')
    for name in ('.KernelExceptionVector.literal', '.UserExceptionVector.literal', '.DebugExceptionVector.literal'):
        require(file_bytes(data, sections, allocated[name]['address'], 4) == bytes(4), 'inert vector literal', name)
    protected = [*GUARDS.values(), *(pairs[n + '_unused'] for n in caps)]
    for p in elf['loads']:
        require(not any(a < b and p['address'] < b and a < p['address'] + p['memsz'] for a, b in protected),
                'load tail overlaps preserved guard/unused capacity', p)
    zero_spans = [(allocated[n]['address'], allocated[n]['size'])
                  for n in ('.bss', '.runtime_mailbox', '.runtime_memory', '.runtime_witness')]
    return allocated, observed, zero_spans, pairs


def read_relocatable(data):
    """Inspect retained input objects; do not link or execute them."""
    require(len(data) >= 52 and data[:7] == b'\x7fELF\x01\x02\x01', 'input ELF32BE header')
    h = struct.unpack_from('>HHIIIIIHHHHHH', data, 16)
    typ, machine, version, entry, phoff, shoff, flags, ehsize, phsize, phnum, shsize, shnum, shstr = h
    require((typ, machine, version, entry, phoff, phnum, ehsize, shsize) == (1, 94, 1, 0, 0, 0, 52, 40),
            'input relocatable target/header', h)
    require(phsize in (0, 32) and flags & ~0x300 == 0 and
            0 < shnum < 4096 and shstr < shnum and shoff >= 52 and shoff + 40 * shnum <= len(data),
            'input table bounds/flags')
    headers = [struct.unpack_from('>10I', data, shoff + 40 * i) for i in range(shnum)]
    require(headers[0] == (0,) * 10, 'input section zero')
    ns = headers[shstr]
    require(ns[1] == 3 and ns[4] + ns[5] <= len(data), 'input section strings')
    names = data[ns[4]:ns[4] + ns[5]]
    sections = []
    for i, s in enumerate(headers):
        name = neutral.cstring(names, s[0])
        require(s[1] == 8 or s[4] + s[5] <= len(data), 'input section file bounds', name)
        require(not s[2] & 0x400 and (s[8] == 0 or s[8] & (s[8] - 1) == 0), 'input TLS/alignment', name)
        require(s[3] == 0, 'relocatable section with fixed virtual address', name, s[3])
        sections.append(dict(index=i, name=name, type=s[1], flags=s[2], address=s[3],
            offset=s[4], size=s[5], link=s[6], info=s[7], align=s[8], entsize=s[9]))
    tables = [s for s in sections if s['type'] == 2 and s['size']]
    require(len(tables) == 1, 'input single symbol table')
    table = tables[0]
    require(table['entsize'] == 16 and table['size'] % 16 == 0 and table['link'] < shnum,
            'input symbol table shape')
    st = sections[table['link']]
    require(st['type'] == 3, 'input symbol strings')
    strings = data[st['offset']:st['offset'] + st['size']]
    records = []
    for off in range(table['offset'], table['offset'] + table['size'], 16):
        ni, value, size, info, other, index = struct.unpack_from('>IIIBBH', data, off)
        name = neutral.cstring(strings, ni)
        require(index < shnum or index == 0xfff1, 'input common/unsupported symbol section', name, index)
        records.append(dict(name=name, address=value, size=size, type=info & 15,
                            binding=info >> 4, visibility=other, section=index))
    relocations = []
    for s in sections:
        if s['type'] not in (4, 9) or not s['size']:
            continue
        entsize = 12 if s['type'] == 4 else 8
        require(s['entsize'] == entsize and s['size'] % entsize == 0 and
                0 < s['info'] < shnum and s['link'] == table['index'], 'input relocation shape', s)
        target = sections[s['info']]
        for off in range(s['offset'], s['offset'] + s['size'], entsize):
            at, info = struct.unpack_from('>II', data, off)
            require(at < target['size'] and info >> 8 < len(records), 'input relocation bounds', s['name'], at, info)
            relocations.append(dict(section=s['info'], offset=at, type=info & 255,
                                    symbol=records[info >> 8]['name']))
    return sections, records, relocations


# Unexecuted integration fragment for hp1020_entry_usb_audit.py.
# Reuses its require, digest, sealed, read_relocatable, Path, json and C_UNITS.
# Add `import re` beside existing standard-library imports. No CLI or build.

LIBGCC_ARCHIVE_SHA256 = 'e57e97f0f5679a83f5a394d94fe024973f05d32be292293b247e647e567c4e32'
LIBGCC_ARCHIVE_BYTES = 878846
LIBGCC_MEMBERS = {
    '_udivsi3.o': (2612, '6e2ed6774b25c833f8071872d6f7b699838e22f625bdb215cd21eea34a96814a'),
    '_umodsi3.o': (2368, 'f7cb9b22bf91ae5b5f40f06a9c2ad1d4e16ea5a7e7be8631e7f2595d89c3e5ee'),
}
RAW_STARTUP_SECTIONS = {
    '.entry.normalizer': 6, '.entry.island': 6, '.WindowVectors.text': 6,
    '.KernelExceptionVector.literal': 2, '.KernelExceptionVector.text': 6,
    '.UserExceptionVector.literal': 2, '.UserExceptionVector.text': 6,
    '.DoubleExceptionVector.text': 6, '.sys_interface_table': 2,
    '.ResetVector.text': 6, '.DebugExceptionVector.literal': 2,
    '.DebugExceptionVector.text': 6,
}
RAW_CUSTOM_SECTIONS = {
    '.runtime_document', '.runtime_memory', '.runtime_mailbox',
    '.runtime_witness', '.runtime_sentinel',
}


def check_raw_input_sections(unit, sections):
    """Gate all raw headers, including zero-size/nonalloc/discarded sections.

    `unit` is a C_UNITS stem, startup, or libgcc/<member filename>. Existing
    ET_REL parsing/bounds and writable-object/initializer checks stay mandatory.
    This is a closed compiler profile, not a general ELF section admission API.
    """
    libgcc = unit in {'libgcc/' + n for n in LIBGCC_MEMBERS}
    require(unit in C_UNITS or unit == 'startup' or libgcc, 'raw input unit', unit)
    by_name = {s['name']: s for s in sections}
    require(len(by_name) == len(sections), 'duplicate raw input section names', unit)
    require(set(('.text', '.data', '.bss', '.symtab', '.strtab', '.shstrtab',
                 '.xtensa.info')).issubset(by_name), 'raw input base section closure', unit)
    symtab = by_name['.symtab']
    require(symtab['link'] == by_name['.strtab']['index'] and
            0 < symtab['info'] <= symtab['size'] // 16,
            'raw symbol table string/local boundary', unit)
    rows = []
    for index, s in enumerate(sections):
        name, typ, flags = s['name'], s['type'], s['flags']
        require(s['index'] == index and s['address'] == 0, 'raw section index/address', unit, s)
        if index == 0:
            require(name == '' and all(s[k] == 0 for k in (
                'type', 'flags', 'address', 'offset', 'size', 'link', 'info', 'align', 'entsize')),
                'raw null section', unit, s)
            rows.append(dict(s, family='null'))
            continue
        require(bool(name), 'unnamed raw input section', unit, s)
        shape = None
        family = None
        if name.startswith('.rela'):
            require(typ == 4 and flags == 0x40 and s['align'] == 4 and
                    s['entsize'] == 12 and s['size'] % 12 == 0 and
                    s['link'] == symtab['index'] and 0 < s['info'] < len(sections),
                    'raw RELA shape/link', unit, s)
            target = sections[s['info']]
            require(name == '.rela' + target['name'] and target['type'] == 1,
                    'raw RELA target/name', unit, s, target)
            # The target is independently classified in this same full loop.
            family = 'rela'
        elif name in RAW_STARTUP_SECTIONS:
            require(unit == 'startup', 'startup section in another unit', unit, name)
            shape, family = (1, RAW_STARTUP_SECTIONS[name], (4,), 0), 'startup'
        elif name in RAW_CUSTOM_SECTIONS:
            require(unit == 'hp1020_usb_runtime_ram', 'custom section in another unit', unit, name)
            shape, family = (1, 3, (16,), 0), 'custom-mutable'
        elif name == '.text' or name.startswith('.text.'):
            shape, family = (1, 6, (1, 4), 0), 'text'
            require(not s['size'] or s['align'] == 4, 'raw nonempty text alignment', unit, s)
        elif name == '.literal' or name.startswith('.literal.'):
            shape, family = (1, 6, (4,), 0), 'literal'
            require(s['size'] % 4 == 0, 'raw literal word extent', unit, s)
        elif name in ('.rodata.str1.1', '.rodata.jbg85_strerror.str1.1'):
            shape, family = (1, 0x32, (1,), 1), 'rodata-strings'
        elif name == '.rodata' or name.startswith('.rodata.'):
            shape, family = (1, 2, (1, 2, 4), 0), 'rodata'
        elif name == '.data' or name.startswith('.data.'):
            shape, family = (1, 3, (1, 4), 0), 'data'
        elif name == '.bss' or name.startswith('.bss.'):
            shape, family = (8, 3, (1, 4, 16), 0), 'bss'
        elif name == '.comment':
            require(unit in C_UNITS, 'comment outside C compiler units', unit)
            shape, family = (1, 0x30, (1,), 1), 'comment'
        elif name == '.xtensa.info':
            shape, family = (7, 0, (1,), 0), 'xtensa-info'
            require(s['size'] == 56, 'raw Xtensa note extent', unit, s)
        elif name in ('.xt.prop', '.xt.lit'):
            shape, family = (1, 0, (1,), 0), 'xtensa-property'
            require(s['size'] % (12 if name == '.xt.prop' else 8) == 0,
                    'raw property record extent', unit, s)
        elif name in ('.debug_line', '.debug_info', '.debug_abbrev', '.debug_aranges'):
            require(libgcc, 'debug section outside selected libgcc', unit, name)
            shape, family = (1, 0, (8,) if name == '.debug_aranges' else (1,), 0), 'libgcc-debug'
        elif name == '.debug_str':
            require(libgcc, 'debug strings outside selected libgcc', unit)
            shape, family = (1, 0x30, (1,), 1), 'libgcc-debug-strings'
        elif name == '.symtab':
            shape, family = (2, 0, (4,), 16), 'symtab'
            require(s['size'] > 0 and s['size'] % 16 == 0, 'raw symtab extent', unit, s)
        elif name in ('.strtab', '.shstrtab'):
            shape, family = (3, 0, (1,), 0), 'strtab'
            require(s['size'] > 0, 'raw string table extent', unit, s)
        require(family is not None, 'unknown raw input section family', unit, s)
        if shape is not None:
            t, f, alignments, entry_bytes = shape
            require((typ, flags, s['entsize']) == (t, f, entry_bytes) and
                    s['align'] in alignments, 'raw input section type/flags/shape', unit, s, shape)
            if name != '.symtab':
                require(s['link'] == 0 and s['info'] == 0, 'raw section auxiliary fields', unit, s)
        if libgcc and flags & 3 == 3:
            require(s['size'] == 0, 'selected libgcc has writable allocation', unit, s)
        rows.append(dict(s, family=family))
    return rows


def selected_archive_members(raw):
    """Read exact ordinary GNU ar bytes; never invoke tools or extract paths."""
    require(len(raw) == LIBGCC_ARCHIVE_BYTES and digest(raw) == LIBGCC_ARCHIVE_SHA256,
            'pinned captured libgcc archive bytes')
    require(raw[:8] == b'!<arch>\n', 'captured libgcc GNU archive header')
    pos, long_names, members = 8, None, {}
    while pos < len(raw):
        head = raw[pos:pos + 60]
        require(len(head) == 60 and head[58:] == b'`\n', 'libgcc archive member header', pos)
        encoded_size = head[48:58].decode('ascii').strip()
        require(encoded_size.isdigit(), 'libgcc archive member size', pos)
        size = int(encoded_size)
        start, end = pos + 60, pos + 60 + size
        require(end <= len(raw), 'libgcc archive member bounds', pos, size)
        body = raw[start:end]
        name = head[:16].decode('ascii').strip()
        if name == '//':
            require(long_names is None, 'duplicate libgcc long-name table')
            long_names = body
        elif name not in ('/', '/SYM64/'):
            if name.startswith('/'):
                require(name[1:].isdigit() and long_names is not None,
                        'libgcc archive long-name reference', name)
                offset = int(name[1:])
                require(offset < len(long_names) and (offset == 0 or long_names[offset - 1] == 10),
                        'libgcc archive long-name boundary', offset)
                finish = long_names.find(b'/\n', offset)
                require(finish >= offset, 'libgcc archive long-name terminator', offset)
                name = long_names[offset:finish].decode('ascii')
            else:
                require(name.endswith('/'), 'unsupported libgcc archive name encoding', name)
                name = name[:-1]
            require(name and '/' not in name and name not in ('.', '..') and name not in members,
                    'libgcc archive member name/uniqueness', name)
            members[name] = body
        if size & 1:
            require(raw[end:end + 1] == b'\n', 'libgcc archive member padding', pos)
        pos = end + (size & 1)
    require(pos == len(raw) and set(LIBGCC_MEMBERS).issubset(members), 'libgcc archive closure')
    return {name: members[name] for name in LIBGCC_MEMBERS}


def check_selected_libgcc(directory, map_path):
    """Validate captured archive, exact copied selected members and map binding.

    `directory` is target/libgcc; no toolchain or original-path read is needed.
    The enclosing runner also binds archive provenance to tool_closure.libgcc.
    """
    directory = Path(directory)
    require({p.name for p in directory.iterdir()} == {'libgcc.a', 'manifest.json', *LIBGCC_MEMBERS} and
            all(p.is_file() and not p.is_symlink() for p in directory.iterdir()),
            'exact captured libgcc file closure')
    manifest_raw, manifest_file = sealed(directory / 'manifest.json')
    manifest = json.loads(manifest_raw)
    require(set(manifest) == {'schema', 'archive', 'members'} and
            manifest['schema'] == 'hp1020-entry-usb-libgcc-v1', 'libgcc manifest schema')
    ar = manifest['archive']
    require(set(ar) == {'file', 'original_path', 'sha256', 'bytes'} and
            ar['file'] == 'libgcc.a' and ar['sha256'] == LIBGCC_ARCHIVE_SHA256 and
            ar['bytes'] == LIBGCC_ARCHIVE_BYTES and Path(ar['original_path']).is_absolute(),
            'libgcc manifest archive')
    original = Path(ar['original_path'])
    require(str(original) == str(original.resolve()), 'libgcc canonical original path')
    expected_members = {name: dict(file=name, bytes=n, sha256=h)
                        for name, (n, h) in LIBGCC_MEMBERS.items()}
    require(manifest['members'] == expected_members, 'libgcc manifest selected members')
    archive_raw, archive_file = sealed(directory / 'libgcc.a')
    extracted = selected_archive_members(archive_raw)
    files = []
    for name, (n, h) in sorted(LIBGCC_MEMBERS.items()):
        raw, row = sealed(directory / name)
        sections, records, relocations = read_relocatable(raw)
        row['sections'] = check_raw_input_sections('libgcc/' + name, sections)
        require(len(raw) == n and digest(raw) == h and raw == extracted[name],
                'captured selected libgcc member bytes', name)
        row['archive_member'] = name
        files.append(row)
    map_raw, map_file = sealed(Path(map_path))
    text = map_raw.decode('utf-8')
    selections = {(str(Path(a).resolve()), n)
                  for a, n in re.findall(r'(\S+\.a)\(([^()\s]+)\)', text)}
    require(selections == {(str(original), n) for n in LIBGCC_MEMBERS},
            'exact link-map selected archive members', sorted(selections))
    loads = [line[5:].strip() for line in text.splitlines() if line.startswith('LOAD ')]
    require(len(loads) == len(C_UNITS) + 2 and len(loads) == len(set(loads)),
            'exact link-map LOAD count', loads)
    archives = [p for p in loads if p.endswith('.a')]
    objects = [Path(p) for p in loads if p.endswith('.o')]
    require(len(archives) == 1 and Path(archives[0]).resolve() == original and
            len(objects) == len(C_UNITS) + 1 and
            {p.name for p in objects} == {n + '.o' for n in C_UNITS | {'startup'}} and
            len({p.parent.resolve() for p in objects}) == 1,
            'exact link-map ordinary/archive input closure', loads)
    return dict(manifest=manifest_file, archive=archive_file, original_path=str(original),
                members=files, link_map=map_file, selected_members=sorted(LIBGCC_MEMBERS),
                selected_archive_sha256=LIBGCC_ARCHIVE_SHA256,
                scope='All raw selected sections classified before execution, including discarded, zero-size and nonalloc inputs.')


def check_input_objects(directory, objects, linked_mutable):
    paths = sorted(directory.glob('*.o'))
    require({p.stem for p in paths} == C_UNITS | {'startup'}, 'exact retained object closure', [p.name for p in paths])
    expected = mutable_expectations(objects)
    files, retained, input_functions = [], {}, []
    for path in paths:
        raw, file_row = sealed(path)
        sections, records, relocations = read_relocatable(raw)
        file_row['raw_sections'] = check_raw_input_sections(path.stem, sections)
        file_row['allocated_writable_sections'] = []
        for s in sections:
            if not s['size'] or s['flags'] & 3 != 3:
                continue
            require(path.stem not in ('startup', 'hp1020_usb_runtime_layout'),
                    'startup/layout unit has writable storage', path.name, s['name'])
            require(s['flags'] == 3 and s['type'] in (1, 8), 'input mutable allocation flags/type', path.name, s)
            members = [r for r in records if r['section'] == s['index'] and r['type'] == 1]
            require(len(members) == 1, 'mutable input section must contain one closed object', path.name, s, members)
            r = members[0]
            name = r['name']
            require(name in expected and name not in retained and path.stem in expected[name]['units'],
                    'input mutable object source/uniqueness', path.name, r)
            require(r['address'] == 0 and r['size'] == s['size'] == expected[name]['size'],
                    'anonymous input allocation or object size differs', path.name, s, r)
            custom = PUBLIC_CUSTOM.get(name)
            if custom:
                require(s['name'] == custom[0], 'custom object input section differs', name, s['name'])
            else:
                prefix = '.data' if expected[name]['section'] == '.data' else '.bss'
                short = '.sdata' if prefix == '.data' else '.sbss'
                require(s['name'] in (prefix, short, prefix + '.' + name, short + '.' + name),
                        'ordinary object input section differs', name, s['name'])
            is_zero = expected[name]['section'] not in ('.data', '.runtime_sentinel')
            contents = bytes(s['size']) if s['type'] == 8 else raw[s['offset']:s['offset'] + s['size']]
            targeted = [r for r in relocations if r['section'] == s['index']]
            if is_zero:
                require(contents == bytes(s['size']) and not targeted,
                        'NOLOAD would discard initializer/relocation', path.name, name, targeted)
            else:
                require(s['type'] == 1, 'initialized input must be file backed', name)
            if name == 'hp1020_usb_runtime_sentinel':
                require(contents == DATA_PATTERN and not targeted, 'sentinel input differs')
            retained[name] = dict(file=path.name, section=s['name'], bytes=s['size'],
                file_backed=s['type'] != 8, initializer_sha256=digest(contents),
                zero_before_link=is_zero, relocations=targeted,
                linked_address=linked_mutable[name]['address'])
            file_row['allocated_writable_sections'].append(s['name'])
        functions = [r for r in records if r['type'] == 2 and r['size'] and 0 < r['section'] < len(sections)]
        if path.stem == 'hp1020_usb_runtime_layout':
            require(not functions, 'layout witness unit must have no executable functions')
        input_functions.extend(dict(file=path.name, **r) for r in functions)
        files.append(file_row)
    require(set(retained) == set(expected), 'input mutable closure missing', sorted(set(expected) - set(retained)))
    return dict(files=files, mutable_objects=[retained[n] | {'name': n} for n in sorted(retained)],
                function_symbols=input_functions,
                scope='Actual ET_REL zero bytes plus absence of relocations establish NOLOAD-input safety; ELF output BSS alone cannot.')


def check_dependencies(directory, root, source):
    """Bind the compiler's complete -MD input lists, including system headers."""
    paths = sorted(directory.glob('*.d'))
    require({p.stem for p in paths} == C_UNITS, 'exact dependency closure', [p.name for p in paths])
    files, sources, dependencies = [], {}, {}
    for path in paths:
        raw, row = sealed(path)
        target, sep, body = raw.decode('utf-8').replace('\\\n', '').partition(':')
        require(sep == ':', 'dependency rule missing target', path.name)
        targets = shlex.split(target)
        allowed_targets = {(directory / (path.stem + '.o')).resolve(),
                           (root / 'analysis/boot-handoff/entry-usb/target' / (path.stem + '.o')).resolve()}
        require(len(targets) == 1 and Path(targets[0]).resolve() in allowed_targets,
                'dependency target does not match retained object', path.name, target)
        row['declared_output'] = str(Path(targets[0]).resolve())
        row['retained_object'] = str((directory / (path.stem + '.o')).resolve())
        names = shlex.split(body)
        require(names, 'empty dependency rule', path.name)
        resolved = [Path(n).resolve() for n in names]
        # Preserve GCC's actual occurrences: its -MD output can list the same
        # header twice. Repetition neither creates a new input nor permits an
        # unsealed one; each distinct resolved file is still checked below.
        row['declared_dependencies'] = names
        row['repeated_dependencies'] = {str(p): n for p, n in Counter(resolved).items() if n > 1}
        c = [p for p in resolved if p.suffix == '.c']
        require(len(c) == 1 and c[0].stem == path.stem, 'dependency source unit mismatch', path.name, c)
        sources[path.stem] = c[0]
        row['dependencies'] = [str(p) for p in resolved]
        files.append(row)
        for p in resolved:
            if str(p) not in dependencies:
                _, dependencies[str(p)] = sealed(p)
    for unit in ('hp1020_usb_runtime', 'hp1020_usb_runtime_ram', 'hp1020_usb_runtime_layout'):
        require(sources[unit] == (source / (unit + '.c')).resolve(), 'runtime source location', unit)
    for unit, relative in SOURCE_UNITS.items():
        require(sources[unit] == (root / relative).resolve(), 'production source location', unit)
    effective_root = sources['usbd'].parent.parent.parent
    require(sources['usbd'] == effective_root / 'src/device/usbd.c' and
            sources['tusb'] == effective_root / 'src/tusb.c' and
            sources['tusb_fifo'] == effective_root / 'src/common/tusb_fifo.c', 'one pinned effective source tree')
    provenance = json.loads((root / 'vendor/tinyusb-0.21.0/PROVENANCE.json').read_text())
    patch = json.loads((root / 'open-firmware/tinyusb-device/patches/manifest.json').read_text())
    require(provenance['commit'] == PIN and not provenance['local_changes'] and
            patch['upstream_commit'] == PIN, 'upstream/effective provenance')
    expected = {name: r['sha256'] for name, r in provenance['upstream_files'].items()}
    require(len(expected) == 19, 'pinned upstream source count')
    for name, r in patch['files'].items():
        require(expected[name] == r['original_sha256'], 'patch base differs', name)
        expected[name] = r['result_sha256']
    manifest_raw, manifest_record = sealed(directory / 'effective-source.json')
    manifest = json.loads(manifest_raw)
    require(manifest == dict(upstream_commit=PIN, patched=True, effective_sha256=expected, patch_manifest=patch),
            'effective source report differs from pinned patch closure')
    effective = []
    for name, value in sorted(expected.items()):
        require(not Path(name).is_absolute() and '..' not in Path(name).parts, 'effective source path')
        _, record = sealed(effective_root / name, value)
        effective.append(record)
    # Prevent an alternate config or patched/private header from silently being
    # selected while merely preserving an unrelated correct manifest.
    for unit in ('usbd', 'tusb', 'tusb_fifo', 'hp1020_tusb_adapter', 'hp1020_usb_runtime_ram'):
        selected = next(r['dependencies'] for r in files if Path(r['file']).stem == unit)
        configs = [Path(n) for n in selected if Path(n).name == 'tusb_config.h']
        require(configs == [(root / 'open-firmware/tinyusb-device/tusb_config.h').resolve()],
                'actual selected USB configuration differs', unit, configs)
        for n in selected:
            p = Path(n)
            if p.name in ('usbd_pvt.h', 'usbd.h', 'tusb.h', 'tusb_option.h', 'osal_none.h', 'tusb_fifo.h'):
                require(p.is_relative_to(effective_root), 'USB header outside effective source', unit, n)
    return dict(files=files, inputs=[dependencies[n] for n in sorted(dependencies)],
                effective_manifest=manifest_record, effective_sources=effective,
                limitation='Compiler dependency and exact input object closure; caller still preserves tool binaries, profile result, all source snapshots and libgcc provenance.')


def check_public_layout(elf, data, objects, fields):
    names = elf['symbols']
    records = [r for r in elf['symbol_records'] if r['name'] == 'hp1020_usb_runtime_layout']
    require(len(records) == 1 and records[0]['type'] == 1 and records[0]['size'] == 1828 and
            elf['indexed'][records[0]['section']]['name'] == '.rodata', 'const compiler layout witness shape')
    words = [0x4850554c, 1, 457, 16, 101]
    for r in objects:
        words.extend((r['id'], r['size'], r['alignment']))
    for r in fields:
        words.extend((r['id'], r['object_id'], r['offset'], r['width']))
    expected = struct.pack('>457I', *words)
    actual = file_bytes(data, elf['sections'], records[0]['address'], 1828)
    require(actual == expected, 'compiler sizes/offsets differ from independently frozen manual table')
    raw_objects = []
    for r in objects:
        rows = [q for q in elf['symbol_records'] if q['name'] == r['name']]
        require(len(rows) == 1 and rows[0]['type'] == 1 and rows[0]['size'] == r['size'], 'public actual symbol', r)
        raw_objects.append(dict(r, address=names[r['name']]))
    for name, size, expected_sha in (
            ('hp1020_usb_runtime_input', 352, INPUT_SHA256),
            ('hp1020_usb_runtime_setup_record', 16, digest(bytes.fromhex('80000000000000000009010000000000')))):
        rows = [r for r in elf['symbol_records'] if r['name'] == name]
        require(len(rows) == 1 and rows[0]['type'] == 1 and rows[0]['size'] == size and
                elf['indexed'][rows[0]['section']]['name'] == '.rodata', 'immutable source object shape', name)
        require(digest(file_bytes(data, elf['sections'], rows[0]['address'], size)) == expected_sha,
                'immutable source bytes differ', name)
    return dict(symbol=records[0], sha256=digest(actual), words=words,
                objects=raw_objects, fields=fields, manual_table_source_hashes={
                    n: CONTRACT_PINS[n] for n in ('layout-objects.tsv', 'layout-fields.tsv')})


def check_initialized_data(elf, data, mutable, instructions):
    """Check source-derived queue/spin/rhport pointer bytes against actual symbols."""
    symbols, sections = elf['symbols'], elf['sections']
    interrupt = symbols.get('usbd_int_set')
    require(interrupt in instructions and any(r['type'] == 2 and r['size'] and r['address'] == interrupt
                                             for r in elf['symbol_records']), 'initialized callback pointer not an actual function')
    qdef = bytearray(20)
    struct.pack_into('>I', qdef, 0, interrupt)
    struct.pack_into('>H', qdef, 4, 12)
    struct.pack_into('>I', qdef, 8, symbols['_usbd_qdef_buf'])
    struct.pack_into('>H', qdef, 12, 192)
    expected = {'_usbd_qdef': bytes(qdef), '_usbd_spin': struct.pack('>II', interrupt, 0), '_usbd_rhport': b'\xff'}
    s = sections['.data']
    actual = file_bytes(data, sections, s['address'], s['size'])
    coverage = bytearray(s['size'])
    result = []
    for name, want in expected.items():
        r = mutable[name]
        got = file_bytes(data, sections, r['address'], r['size'])
        require(got == want, 'source-derived initialized bytes differ', name, got.hex(), want.hex())
        off = r['address'] - s['address']
        require(not any(coverage[off:off + len(want)]), 'data object overlap')
        coverage[off:off + len(want)] = b'\x01' * len(want)
        result.append(dict(name=name, address=r['address'], bytes=len(want), hex=want.hex()))
    require(max(mutable[n]['address'] + mutable[n]['size'] for n in expected) == s['address'] + s['size'] and
            min(mutable[n]['address'] for n in expected) == s['address'], 'unowned data tail/start')
    require(all(b == 0 for b, used in zip(actual, coverage) if not used), 'nonzero anonymous initialized data padding')
    return dict(address=s['address'], bytes=s['size'], hex=actual.hex(), sha256=digest(actual), objects=result,
                basis='Pinned OS_NONE queue20, spin8, rhport1; original static pointers relocate to actual usbd_int_set and queue192. Generic .data is preserved at startup and writable only during C.')


def read_properties(elf, data):
    """Local modern-property admission: no broad DATA decode or old CALL0 pin."""
    sections = elf['sections']
    require('.xt.prop' in sections, 'modern instruction properties required')
    s = sections['.xt.prop']
    require(s['type'] == 1 and s['flags'] == 0 and s['size'] > 0 and s['size'] % 12 == 0,
            'modern property table shape')
    rows = []
    for a, n, flags in struct.iter_unpack('>III', data[s['offset']:s['offset'] + s['size']]):
        require(flags & ~0x3ffff == 0 and not flags & 0x20000,
                'unknown property/absolute literal mode', a, n, flags)
        kind = flags & 7
        require(kind in (0, 1, 2, 4, 5, 6), 'property kind', a, n, flags)
        if kind == 6:
            require((a, n, flags) == (elf['symbols'].get('hp1020_entry_before_c'), 6, 0x2906) and
                    elf['symbols'].get('hp1020_entry_park') == a + 3 and
                    file_bytes(data, sections, a + 3, 3) == bytes.fromhex('63fffc'),
                    'mixed DATA/INSN outside no-transform CALL0/park', a, n, flags)
            # The newly relocated first three bytes are decoded and checked
            # against the new C symbol below; old experiment bytes are not reused.
        if n:
            owners = [q for q in sections.values() if q['flags'] & 2 and q['type'] != 8 and
                      inside(a, n, q['address'], q['address'] + q['size'])]
            require(len(owners) == 1, 'property allocation', a, n)
            require(kind not in (2, 6) or owners[0]['flags'] & 4, 'instruction outside executable allocation', a)
            require(not flags & 0x10, 'hardware loop target outside profile', a)
            if kind == 0:
                require(flags == 8 and 1 <= n <= 3 and owners[0]['name'] == '.text' and
                        file_bytes(data, sections, a, n) == bytes(n), 'unreachable padding form', a, n, flags)
            if kind & 1:
                require(a % 4 == 0 and n % 4 == 0, 'literal property alignment', a, n)
            owner = owners[0]['name']
        else:
            owner = None
        rows.append(dict(address=a, bytes=n, flags=flags, kind=kind, section=owner))
    rows.sort(key=lambda r: (r['address'], r['bytes'], r['flags']))
    merge([(r['address'], r['address'] + r['bytes']) for r in rows if r['bytes']])
    require(sum(r['kind'] == 6 for r in rows) == 1, 'one exact no-transform property')
    code = merge([(r['address'], r['address'] + r['bytes']) for r in rows if r['bytes'] and r['kind'] in (2, 6)])
    literals = [(r['address'], r['address'] + r['bytes']) for r in rows if r['bytes'] and r['kind'] & 1]
    require(code, 'empty annotated closure')
    for name, modern in (('.xt.insn', code), ('.xt.lit', merge(literals))):
        if name not in sections or not sections[name]['size']:
            continue
        t = sections[name]
        require(t['type'] == 1 and t['flags'] == 0 and t['size'] % 8 == 0, 'legacy property table shape', name)
        entries = list(struct.iter_unpack('>II', data[t['offset']:t['offset'] + t['size']]))
        require(merge([(a, a + n) for a, n in entries]) == modern, 'legacy/modern disagreement', name)
    return rows, code, literals


def check_startup(elf, data, instructions, zero_spans):
    symbols, sections = elf['symbols'], elf['sections']
    required = ('hp1020_entry_normalize', 'hp1020_entry_after_normalization',
                'hp1020_entry_before_c', 'hp1020_entry_park', 'hp1020_entry_unexpected_park',
                'hp1020_usb_runtime_c')
    require(all(n in symbols for n in required), 'missing startup symbols')
    normal, after, before, park, unexpected, c_entry = [symbols[n] for n in required]
    require(normal == 0x10003024 and normal < after < before < park < unexpected < c_entry,
            'startup checkpoint order', [hex(symbols[n]) for n in required])
    pool_values = [STACK[0] + STACK[1]]
    for a, n in zero_spans:
        pool_values.extend((a, a + n))
    require(file_bytes(data, sections, 0x10003000, 36) == struct.pack('>9I', *pool_values),
            'exact nine-word startup pool')
    expected = [
        ('rsil', (2, 15)), ('movi', (2, 0)), ('wsr.intenable', (2,)),
        ('wsr.lcount', (2,)), ('wsr.lbeg', (2,)), ('wsr.lend', (2,)),
        ('isync', ()), ('movi', (2, 15)), ('wsr.ps', (2,)), ('rsync', ()),
        ('movi', (2, 0)), ('wsr.windowbase', (2,)), ('rsync', ()),
        ('movi', (2, 1)), ('wsr.windowstart', (2,)), ('rsync', ()),
        ('ssai', (0,)), ('l32r', (1, 0x10003000)), ('movi', (4, 0)),
    ]
    pc, normalized = normal, []
    for want, operands in expected:
        op, args, raw = instructions.get(pc, ('', (), b''))
        require(op.removesuffix('.n') == want and args == operands, 'normalizer instruction', pc, op, args, want, operands)
        if want in neutral.PREFIX_RAW:
            require(raw.hex() == neutral.PREFIX_RAW[want], 'normalizer privileged raw bytes', pc, raw.hex())
        normalized.append(dict(address=pc, opcode=op, operands=list(args), hex=raw.hex()))
        pc += len(raw)
    require(pc == after, 'after-normalization checkpoint differs')
    clears = []
    for literal, (a, n) in zip((0x10003004, 0x1000300c, 0x10003014, 0x1000301c), zero_spans):
        begin = pc
        for dst, word in ((2, literal), (3, literal + 4)):
            op, args, raw = instructions.get(pc, ('', (), b''))
            require(op == 'l32r' and args == (dst, word), 'clear literal load', pc, op, args)
            pc += len(raw)
        loop = pc
        for want, operands in (('s32i', (4, 2, 0)), ('addi', (2, 2, 4)), ('bltu', (2, 3, loop))):
            op, args, raw = instructions.get(pc, ('', (), b''))
            require(op.removesuffix('.n') == want and args == operands, 'ordinary clear loop', pc, op, args)
            pc += len(raw)
        clears.append(dict(address=begin, loop=loop, end=pc, destination=a, bytes=n, stores=n // 4))
    require(pc == before, 'pre-C checkpoint differs')
    op, args, raw = instructions.get(before, ('', (), b''))
    require(op == 'call0' and args == (c_entry,) and len(raw) == 3 and before + 3 == park,
            'new own C CALL0/immediate return park')
    parks = [park, unexpected, *range(0x10000000, 0x10000180, 0x40),
             0x10000200, 0x10000220, 0x10000270, 0x10100020, 0x10100320]
    for at in parks:
        require(instructions.get(at) == ('j', (at,), bytes.fromhex('63fffc')), 'inert self-park', at)
    op, args, raw = instructions.get(ENTRY, ('', (), b''))
    require(op == 'j' and args == (normal,) and len(raw) == 3, 'stack-free entry jump')
    require(file_bytes(data, sections, 0x10000370, 0x12c) == struct.pack('>75I', *([unexpected] * 75)),
            'inert interface table')
    padding = [(0x10016780, ENTRY), (ENTRY + 3, 0x100167e0)]
    padding += [(a + 3, a + 0x40) for a in range(0x10000000, 0x10000180, 0x40)]
    padding += [(a + 3, a + n) for a, n in
                ((0x10000200, 0x1c), (0x10000220, 0x1c), (0x10000270, 0xe0),
                 (0x10100020, 0x2e0), (0x10100320, 0xc))]
    for a, b in padding:
        require(file_bytes(data, sections, a, b - a) == bytes(b - a), 'fixed inert padding', a, b)
    return normalized, padding, (0x10003000, normal), parks, clears


def check_private_getter(elf, data, instructions):
    records = [r for r in elf['symbol_records'] if r['name'] == 'usbd_edpt_busy']
    require(len(records) == 1 and records[0]['type'] == 2 and records[0]['size'] == 25,
            'private core getter exact size/type')
    at = records[0]['address']
    first = instructions.get(at)
    require(first is not None and first[0] == 'l32r' and first[1][0] == 10 and len(first[2]) == 3,
            'getter first base load')
    base_literal = first[1][1]
    require(file_bytes(data, elf['sections'], base_literal, 4) == struct.pack('>I', elf['symbols']['_usbd_dev']),
            'getter literal not actual core object')
    suffix = bytes.fromhex('0309430a9909037340a3990c0200229034020240d00f')
    require(file_bytes(data, elf['sections'], at + 3, 22) == suffix, 'getter exact offset/index/mask bytes')
    expected = [('extui', (9, 3, 0, 4)), ('addx2', (9, 9, 10)), ('extui', (3, 3, 7, 1)),
                ('add.n', (9, 9, 3)), ('memw', ()), ('l8ui', (2, 9, 52)),
                ('extui', (2, 2, 0, 1)), ('ret.n', ())]
    pc = at + 3
    for op, args in expected:
        actual = instructions.get(pc, ('', (), b''))
        require(actual[:2] == (op, args), 'getter annotated operation', pc, actual, op, args)
        pc += len(actual[2])
    require(pc == at + 25, 'getter coverage')
    return dict(proof_sha256=PRIVATE_PROOF_SHA256, core_symbol='_usbd_dev', core_address=elf['symbols']['_usbd_dev'],
                core_bytes=68, control_bytes=24, endpoint_status_offset=52, endpoint_status_bytes=16,
                bulk_out1_offset=54, busy_mask=1, claimed_mask=4, stalled_mask=2,
                getter=records[0], literal_address=base_literal,
                getter_hex=file_bytes(data, elf['sections'], at, 25).hex(),
                scope='Source/ABI and exact getter binding only; software BUSY/CLAIMED never prove controller settlement.')


# Exact pinned GCC14.3.0 call0 leaf implementations. Both zero-divisor ILL
# paths remain excluded from execution; their following DIV0 bytes are data.
# The newly linked modulo helper is not covered by the earlier entry audit.
LIBGCC_HELPER_PROFILE = {
    '__udivsi3': (76, 65, '97c0f245a842a23b8ca0ad47d15b781a0dc0537c7aa2dc7251efa494e734e3f9'),
    '__umodsi3': (57, 46, '14ae148884c6f9f3658da10de58e1d0a6ba01a70a145260bc8899a98c586ca21'),
}


def check_libgcc_helpers(elf, data):
    result = []
    for name, (size, offset, expected) in LIBGCC_HELPER_PROFILE.items():
        rows = [r for r in elf['symbol_records'] if r['name'] == name]
        require(len(rows) == 1 and rows[0]['type'] == 2 and rows[0]['size'] == size,
                'exact selected libgcc helper symbol', name)
        r = rows[0]
        require(elf['indexed'][r['section']]['name'] == '.text', 'libgcc helper outside text', name)
        raw = file_bytes(data, elf['sections'], r['address'], size)
        require(digest(raw) == expected and raw[offset:offset + 7] == bytes(3) + b'DIV0',
                'pinned whole libgcc helper/zero-divisor bytes differ', name)
        result.append(dict(name=name, address=r['address'], bytes=size, sha256=expected,
            trap_address=r['address'] + offset, marker_address=r['address'] + offset + 3,
            basis='Pinned GCC14.3.0 lib1funcs.S conditional zero-divisor ILL plus DIV0; ordinary call0 leaves. No exception path is admitted.'))
    return result


def classify_usb_code(elf, data, rows, instructions, zero_padding, pool, linker_fills, helpers):
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
    # 5=the fixed nine-word pool, 6=property-authorized alignment padding,
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
    for helper in helpers:
        trap = helper['trap_address']
        a, b = trap + 3, trap + 7
        require(instructions.get(trap) == ('ill', (), bytes(3)) and
                file_bytes(data, elf['sections'], a, 4) == b'DIV0',
                'libgcc divide trap/diagnostic marker differs', trap)
        paint(a, b, 9)
        divide_markers.append(dict(address=a, bytes=4, hex='44495630', helper=helper['name'],
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
    require({p.stem for p in paths} == C_UNITS, 'exact compiler stack-use closure', [p.name for p in paths])
    files, records = [], []
    for path in paths:
        raw, row = sealed(path)
        files.append(row)
        for line in raw.decode('utf-8').splitlines():
            columns = line.rsplit('\t', 2)
            require(len(columns) == 3 and columns[1].isdigit() and columns[2] == 'static',
                    'nonstatic/unrecognized stack-use row', path.name, line)
            frame = int(columns[1])
            require(frame <= STACK[1] and frame % 16 == 0, 'single-frame stack limit/alignment', path.name, line)
            records.append(dict(file=path.name, function=columns[0], bytes=frame, qualifier=columns[2]))
        if path.stem == 'hp1020_usb_runtime_layout':
            require(not raw.strip(), 'const layout unit unexpectedly has stack-use records')
    require(records, 'empty whole-linked stack-use evidence')
    return dict(files=files, functions=records, largest_individual_frame=max(r['bytes'] for r in records),
                owned_stack_bytes=STACK[1],
                limitation='No inherited 784-byte bound: nested USB callbacks, compiler/libgcc and actual runtime stack depth require independent linked review and runtime limits.')


def audit_target(path, prefix, stock_path):
    """Return Program plus exact evidence, without executing a target instruction.

    entry_read_spans and entry_zero_spans use (start, BYTE_COUNT); write_ranges
    and execute_ranges use (start, END). Generic .data is preserved at startup,
    then writable during C. The distinct initialized sentinel stays immutable.
    """
    from hp1020_xtensa_call0 import Program
    path, stock_path = Path(path).resolve(), Path(stock_path).resolve()
    root = stock_path.parent.parent
    source, objects, fields, input_pins = contract_inputs(root)
    data = path.read_bytes()
    elf = neutral.read_elf(data)
    allocated, mutable, zero_spans, span_symbols = check_layout(elf, data, objects)
    inputs = check_input_objects(path.parent, objects, mutable)
    selected_libgcc = check_selected_libgcc(path.parent / 'libgcc', path.with_suffix('.map'))
    dependencies = check_dependencies(path.parent, root, source)
    public_layout = check_public_layout(elf, data, objects, fields)
    rows, code_ranges, literal_ranges = read_properties(elf, data)
    anchors, stock_spans = neutral.check_stock(stock_path, prefix, Program.parse)
    for p in elf['loads']:
        require(any(inside(p['address'], p['memsz'], a, b) for a, b in stock_spans),
                'load outside stock-declared envelope', p)
    instructions, listings = {}, []
    for a, b in code_ranges:
        decoded, listing = neutral.disassemble(path, prefix, a, b, Program.parse)
        listings.append(listing)
        pc = a
        for at, (op, args, raw) in decoded:
            require(at == pc and len(raw) in (2, 3) and at not in instructions,
                    'noncontiguous/duplicate decode', at, pc)
            require(at + len(raw) <= b and raw == file_bytes(data, elf['sections'], at, len(raw)),
                    'decoded bytes differ from ELF', at)
            instructions[at] = (op, args, raw)
            pc += len(raw)
        require(pc == b, 'incomplete annotated decode', a, b, pc)
    prefix_rows, padding, pool, parks, clears = check_startup(elf, data, instructions, zero_spans)
    linker_fills, link_map = neutral.linker_fill_evidence(path, elf)
    helper_proofs = check_libgcc_helpers(elf, data)
    trap_sites = {h['trap_address']: h for h in helper_proofs}
    labels, alignment, linker_padding, divide_markers = classify_usb_code(
        elf, data, rows, instructions, padding, pool, linker_fills, helper_proofs)
    normal, after = elf['symbols']['hp1020_entry_normalize'], elf['symbols']['hp1020_entry_after_normalization']
    functions = [dict(r) for r in elf['symbol_records'] if r['type'] == 2 and r['size']]
    starts = {r['address'] for r in functions}
    require(starts and all(at in instructions for at in starts), 'function entry outside annotated boundary')
    traps, direct, literals, dynamic = [], [], [], []
    for pc, (op, args, raw) in sorted(instructions.items()):
        if op == 'ill':
            require(pc in trap_sites and raw == bytes(3), 'unrecognized trap', pc, raw.hex())
            traps.append(dict(address=pc, hex=raw.hex(), helper=trap_sites[pc]['name'],
                kind='libgcc zero-divisor ILL; excluded from execution'))
        elif op in neutral.PREFIX_RAW:
            require(normal <= pc < after and raw.hex() == neutral.PREFIX_RAW[op],
                    'special operation outside exact prefix', pc, op)
        else:
            require(op in neutral.ORDINARY, 'opcode outside conservative call0 profile', pc, op)
        if op in neutral.DIRECT_BRANCHES or op in ('call0', 'j'):
            require(args and isinstance(args[-1], int) and args[-1] in instructions,
                    'direct target outside annotation', pc, op, args)
            if op == 'call0':
                require(args[-1] in starts, 'direct CALL0 target not an actual function entry', pc, args)
            direct.append(dict(address=pc, opcode=op, target=args[-1]))
        elif op in ('callx0', 'jx', 'ret', 'ret.n'):
            dynamic.append(dict(address=pc, opcode=op, operands=list(args)))
        if op == 'l32r':
            require(len(args) == 2 and isinstance(args[1], int) and args[1] % 4 == 0 and
                    any(inside(args[1], 4, a, b) for a, b in [pool, *literal_ranges]),
                    'L32R outside actual readable literal', pc, args)
            require(len(raw) == 3 and raw[0] >> 4 == 1 and args[0] == raw[0] & 15,
                    'L32R raw register/encoding', pc, args)
            encoded = (((pc + 3) & ~3) + (int.from_bytes(raw[1:], 'big') - 0x10000) * 4) & 0xffffffff
            require(args[1] == encoded, 'L32R decoded displacement differs', pc, args, encoded)
            literals.append(dict(address=pc, target=args[1],
                word=int.from_bytes(file_bytes(data, elf['sections'], args[1], 4), 'big')))
    require(len(traps) == len(helper_proofs) == 2, 'exact two excluded libgcc zero-divisor traps')
    private_core = check_private_getter(elf, data, instructions)
    initialized = check_initialized_data(elf, data, mutable, instructions)
    trap_pcs = {r['address'] for r in traps}
    admitted = {pc: row for pc, row in instructions.items() if pc not in trap_pcs}
    execute_ranges = merge([(pc, pc + len(row[2])) for pc, row in admitted.items()])
    program = Program.__new__(Program)
    program.path, program.prefix, program.entry = path, str(prefix), elf['entry']
    program.symbols = elf['symbols']
    program.segments = [(p['address'], bytearray(data[p['offset']:p['offset'] + p['filesz']]) +
                         bytearray(p['memsz'] - p['filesz']), p['flags']) for p in elf['loads']]
    program.instructions = admitted
    program.annotated_code = [(a, b - a) for a, b in execute_ranges]
    program.execute_ranges = execute_ranges
    program.entry_zero_spans = list(zero_spans)
    program.entry_stack = STACK
    program.entry_data_span = (allocated['.data']['address'], allocated['.data']['size'])
    program.entry_function_starts = starts
    program.entry_read_spans = [(s['address'], s['size']) for s in sorted(allocated.values(), key=lambda s: s['address'])]
    program.write_ranges = [(a, a + n) for a, n in zero_spans] + [
        (STACK[0], STACK[0] + STACK[1]),
        (program.entry_data_span[0], program.entry_data_span[0] + program.entry_data_span[1]),
    ]
    program.entry_audit_disassembly = ''.join(listings)
    program.entry_excluded_traps = sorted(trap_pcs)
    su = stack_usage(path.parent)
    audit = dict(
        schema='hp1020-entry-usb-audit-v1', target_sha256=digest(data), target_bytes=len(data),
        stock_sha256=neutral.STOCK_SHA256, entry=elf['entry'], elf_flags=elf['flags'],
        objdump_sha256=digest(Path(str(prefix) + '-objdump').read_bytes()),
        audit_source_sha256=digest(Path(__file__).read_bytes()), neutral_source_pins=SCRIPT_PINS,
        pinned_inputs=input_pins, object_inputs=inputs, compiler_dependencies=dependencies,
        selected_libgcc=selected_libgcc,
        allocated_sections=[dict(s) for s in sorted(allocated.values(), key=lambda s: s['address'])],
        load_segments=elf['loads'], source_anchor_checks=anchors,
        symbols=dict(sorted(elf['symbols'].items())), symbol_records=elf['symbol_records'],
        function_symbols=functions, function_starts=sorted(starts),
        mutable_objects=[mutable[n] for n in sorted(mutable)], public_layout=public_layout,
        private_core=private_core, initialized_data=initialized,
        zero_spans=[[a, n] for a, n in zero_spans], owned_stack=list(STACK),
        initialized_data_span=list(program.entry_data_span),
        immutable_sentinel=[0x10016500, 256], span_symbols={n: list(v) for n, v in span_symbols.items()},
        properties=rows, annotated_instructions=len(instructions), admitted_instructions=len(admitted),
        annotated_instruction_bytes=sum(len(row[2]) for row in instructions.values()),
        execution_ranges=[[a, b] for a, b in execute_ranges],
        read_spans=[[a, n] for a, n in program.entry_read_spans], write_ranges=program.write_ranges,
        footprint=dict(text_bytes=allocated['.text']['size'], rodata_bytes=allocated['.rodata']['size'],
            initialized_data_bytes=allocated['.data']['size'], sentinel_bytes=256,
            generic_bss_bytes=allocated['.bss']['size'], memory_bytes=114704, mailbox_bytes=1024,
            witness_bytes=9216, owned_stack_bytes=8192, zero_bytes=sum(n for _, n in zero_spans),
            file_backed_load_bytes=sum(p['filesz'] for p in elf['loads']),
            load_memory_bytes=sum(p['memsz'] for p in elf['loads'])),
        prefix=prefix_rows, clear_loops=clears, inert_park_addresses=parks, byte_classification=labels,
        alignment_padding=alignment, linker_alignment_padding=linker_padding, link_map=link_map,
        libgcc_helpers=helper_proofs, excluded_division_traps=traps, excluded_division_markers=divide_markers,
        direct_targets=direct, dynamic_control_sites=dynamic, literal_loads=literals,
        opcode_counts=dict(sorted(Counter(row[0] for row in admitted.values()).items())),
        stack_usage=su, disassembly_sha256=digest(program.entry_audit_disassembly.encode()),
        scope='Whole linked annotated closure, actual split-object layout and preserved initialization; no target execution by this audit.',
        limitations=[
            'New offline layout; no HP-loader compatibility, physical RAM, USB or printing proof.',
            'Privilege, usable mapped RAM, PC-relative L32R, no asynchronous/debug exception and a nonintersecting incoming loop endpoint remain supplied.',
            'Runner must enforce phase-specific read/write/fetch/stack/call targets and contextual actual-function checkpoints.',
            'Input ET_REL checks prevent hidden NOLOAD initializers; they do not prove hardware memory attributes or loader behavior.',
            'Static individual stack frames are not a complete callback/libgcc depth bound; the earlier smaller workload bound does not transfer.',
            'Generic .data may change during C; the separate initialized sentinel is immutable.',
            'DMA labels, register observations, cache visibility and physical settlement remain supplied by the separate RAM provider.',
        ])
    return program, audit
