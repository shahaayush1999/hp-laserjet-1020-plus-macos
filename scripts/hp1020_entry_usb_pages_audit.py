"""Unexecuted separate real-page-profile linked audit; ELF/RAM evidence only.

Reuses pinned neutral raw-object/startup/ISA/library helpers without mutating
accepted modules. Local contract/layout/dependency/coordination binds only this
sibling profile. No target or device execution by the audit.
"""
from collections import Counter
import csv,io,json,re,shlex,struct
from pathlib import Path
import hp1020_entry_usb_audit as usb
from hp1020_entry_usb_audit import (
    neutral,require,digest,inside,merge,file_bytes,sealed,PIN,
    C_UNITS,SOURCE_UNITS,REPO_PINS,STACK,check_layout,check_input_objects,
    read_properties,check_startup,LIBGCC_MEMBERS,LIBGCC_ARCHIVE_SHA256,
    LIBGCC_ARCHIVE_BYTES,selected_archive_members,read_relocatable,check_raw_input_sections,
    classify_usb_code,check_private_getter,check_initialized_data,stack_usage,
)
SCRIPT_PINS = dict(usb.SCRIPT_PINS)
SCRIPT_PINS['hp1020_entry_usb_audit.py'] = 'bf3e4dbe77b7f4b9c6c8f264d31c28186b40f65621d947468080bda9c984dc9d'
INPUT_SHA256 = '8ccf8bc1391e9025e3bd0a196dd155a04b967271bbb2a896bfd185453c0ed669'
CONTRACT_PINS = {'LIBRARY_SELECTION.md': '344575b6e5123bd655d3b8e81420eaefccaf6bd54172144433ea348daf6e40db', 'hp1020_usb_runtime_contract.h': '58b0921807073bd9dd1dda5c3f7b3366fd634e2d682c4d20e97b44388c5176eb', 'layout-objects.tsv': 'c1c49c7743960ae63fd22d7cb1fdf7d4dfd04904ba2d6e8a200e3a9068b8b681', 'layout-fields.tsv': '91bb103c8ff980e53d9edffec8c4da04e24d0d32497fa805141ef6289ca25a97', 'startup.S': 'c8271bbea0fdc7ed4ffb4c18469a15d91170d26c948d41e3706e8ed95922bad6', 'runtime.ld': 'a9da60d3538fcd92fdf7d1329092df2f9208fede69778b168661a3dcfee712a7'}

# Frozen before a real-page build: the old %6 orchestration was removed, while
# provider division remains. Unexpected map selection is an admission stop.
PAGES_SELECTED_MEMBERS = {'_udivsi3.o'}
PAGES_LIBGCC_HELPERS = {
    '__udivsi3': (76, 65, '97c0f245a842a23b8ca0ad47d15b781a0dc0537c7aa2dc7251efa494e734e3f9'),
}

def check_selected_libgcc(directory, map_path):
    """Validate both original member copies and the exact real-page link selection.

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
    require(manifest['members'] == expected_members, 'libgcc manifest captured member inventory')
    archive_raw, archive_file = sealed(directory / 'libgcc.a')
    extracted = selected_archive_members(archive_raw)
    files = []
    for name, (n, h) in sorted(LIBGCC_MEMBERS.items()):
        raw, row = sealed(directory / name)
        sections, records, relocations = read_relocatable(raw)
        row['sections'] = check_raw_input_sections('libgcc/' + name, sections)
        require(len(raw) == n and digest(raw) == h and raw == extracted[name],
                'captured original libgcc member bytes', name)
        row['archive_member'] = name
        files.append(row)
    map_raw, map_file = sealed(Path(map_path))
    text = map_raw.decode('utf-8')
    selections = {(str(Path(a).resolve()), n)
                  for a, n in re.findall(r'(\S+\.a)\(([^()\s]+)\)', text)}
    require(selections == {(str(original), n) for n in PAGES_SELECTED_MEMBERS},
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
                members=files, link_map=map_file, selected_members=sorted(PAGES_SELECTED_MEMBERS),
                captured_members=sorted(LIBGCC_MEMBERS),
                selected_archive_sha256=LIBGCC_ARCHIVE_SHA256,
                scope='Both preserved original member inputs classified; exact real-page map selection is _udivsi3.o alone. Extraction is not link selection.')


def check_libgcc_helpers(elf, data):
    result = []
    require(not any(r['name'] == '__umodsi3' for r in elf['symbol_records']),
            'real-page profile must not retain the unused modulo helper')
    for name, (size, offset, expected) in PAGES_LIBGCC_HELPERS.items():
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


def contract_inputs(root):
    source = root / 'open-firmware/entry-usb-pages-test'
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
                           (root / 'analysis/boot-handoff/entry-usb-pages/target' / (path.stem + '.o')).resolve()}
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
    words = [0x4850554c, 3, 457, 16, 101]
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
            ('hp1020_usb_runtime_input', 967, INPUT_SHA256),
            ('hp1020_usb_runtime_setup_record', 16, digest(bytes.fromhex('80000000000000000009010000000000')))):
        rows = [r for r in elf['symbol_records'] if r['name'] == name]
        require(len(rows) == 1 and rows[0]['type'] == 1 and rows[0]['size'] == size and
                elf['indexed'][rows[0]['section']]['name'] == '.rodata', 'immutable source object shape', name)
        require(digest(file_bytes(data, elf['sections'], rows[0]['address'], size)) == expected_sha,
                'immutable source bytes differ', name)
    return dict(symbol=records[0], sha256=digest(actual), words=words,
                objects=raw_objects, fields=fields, manual_table_source_hashes={
                    n: CONTRACT_PINS[n] for n in ('layout-objects.tsv', 'layout-fields.tsv')})

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
    require(len(traps) == len(helper_proofs) == 1, 'exact one excluded real-page-profile libgcc zero-divisor trap')
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
    program.entry_symbol_records = [dict(r) for r in elf['symbol_records']]
    program.entry_read_spans = [(s['address'], s['size']) for s in sorted(allocated.values(), key=lambda s: s['address'])]
    program.write_ranges = [(a, a + n) for a, n in zero_spans] + [
        (STACK[0], STACK[0] + STACK[1]),
        (program.entry_data_span[0], program.entry_data_span[0] + program.entry_data_span[1]),
    ]
    program.entry_audit_disassembly = ''.join(listings)
    program.entry_excluded_traps = sorted(trap_pcs)
    su = stack_usage(path.parent)
    audit = dict(
        schema='hp1020-entry-usb-pages-audit-v1', target_sha256=digest(data), target_bytes=len(data),
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

