#!/usr/bin/env python3
"""Original RAM-only raw dispatch and conditional retirement/cleanup fragments.

Every prepare, render/refill peripheral path and custom callback remains excluded.
These fragments are not a scheduled page, boot, DMA or physical completion.
"""
import importlib.util
import json
import os
from pathlib import Path
import struct
import sys
import tempfile

from hp1020_xtensa_call0 import Program, Machine
from hp1020_stock_stop import StopRAM
from hp1020_stock_notifications import invoke
from hp1020_qemu_pipeline import start
from hp1020_qemu_ram import QemuRAM
from hp1020_qemu_stock_parser import VECTORS
from hp1020_qemu_scheduler import RANGES
from hp1020_qemu_scheduled_status import READY_CODE

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'analysis/hardware-boundary/raw-buffer-contract'
WORK, NODE, PAYLOAD, BUFFER = 0x22700000, 0x22700200, 0x22700210, 0x22704000
DISPATCH = [(0x10013c7d, 0x10013c97), (0x10013ca6, 0x10013cad)]
FLAG = [(0x10014b92, 0x10014baf)]
ALTERNATE = [(0x10015438, 0x10015450)]
SELECT = [(0x10014138, 0x10014153)]
BUILD_KIND = [(0x10010448, 0x10010460)]
RETIRE = [(0x1001451c, 0x1001455a)]
CLEANUP = [(0x1000f0a8, 0x1000f128), (0x10013050, 0x1001307c), (0x1001b770, 0x1001b788)]
FREE = 0x10013408
HASHES = {
    (0x10010448, 0x10010460): '87d91c7d2515a0dc6df2d5fc8418d13879f843bc1fa6ff98079cf4e2961f20f6',
    (0x10013c7d, 0x10013cc4): 'b545933c73cc711d6fdea6e8c8d20c1401680e0caafd9a40cf12084b8042845d',
    (0x10015438, 0x10015458): '16bf6cec843b78f2b0eb2e241ac3b5b3f73e62af4a903b28eba3fef82edd53d8',
    (0x100140f8, 0x10014244): '3bf597a8e0e58bc27c4e257053235ddb6aa56e6471e7ca79b4f7add578b1d1f8',
    (0x10014b92, 0x10014baf): 'ddd48969e3737ca5453451a05d6b548e8413da48bf701afa08acd6003188f275',
    (0x1001451c, 0x10014560): '43834761c2a95a8c473019f8703e590de66ae159b5e72cc1a5e24aa7070693c8',
    (0x1000f0a8, 0x1000f128): '881829830bef323a5256f7fce7ed05f2417c40efc93cb3a6b869ab237ec43ce8',
    (0x10013050, 0x1001307c): '9a5d67fd2e6cc975117843a2aef72fba3682a56d47fa0a077bc291d4e93d647b',
    (0x1001b770, 0x1001b788): '7e1b037e7f2f8df113f21e45bf5d8db4c4ae3b161afe4bd338896c9e1a5cd518',
}
WRAPPER = '''
.text
.align 4
.global builder
builder:
 entry a1,48
 mov a7,a2
 mov a3,a3
 movi a5,0
 movi a8,0x10010448
 jx a8
.align 4
.global dispatch
dispatch:
 entry a1,48
 mov a6,a2
 movi a5,0
 movi a8,0x10013c7d
 jx a8
.align 4
.global flag
flag:
 entry a1,48
 mov a4,a2
 mov a5,a3
 movi a8,0x10014b92
 jx a8
.align 4
.global select_pointer
select_pointer:
 entry a1,48
 mov a4,a2
 movi a8,0x10014138
 jx a8
.align 4
.global retire
retire:
 entry a1,48
 mov a10,a2
 movi a8,0x1001451c
 jx a8
'''


class RawRAM(StopRAM):
    def extension(self, op, args, nxt):
        if op == 'call8' and args == (FREE,):
            self.free_requests.append(self.registers[10])
            self.registers[10] = 0
            self.branch_taken = True
            return nxt  # Observe a request only; no allocator or reclamation proof.
        return super().extension(op, args, nxt)


def ar(q, index):
    return q.reg(((q.reg(38)*4+index) % 32)+1)


def stop(runner, boundaries):
    while runner.q.reg(0) not in boundaries:
        runner.step()
    runner.synchronize(False)
    return runner.q.reg(0)


def excluded(runner, pc):
    runner.q.set_reg(0, pc)
    before = runner.steps
    try:
        runner.step()
    except ValueError as error:
        assert str(error) == f'native tasks left selected code: {pc:#x}'
    else:
        raise AssertionError(f'excluded instruction executed: {pc:#x}')
    assert runner.steps == before and runner.q.reg(0) == pc
    return hex(pc)


def memory(program, ranges, fill, band, pointer):
    state = RawRAM(program, ranges[0][0], ranges+VECTORS, [(WORK, 0x10000)])
    state.put(WORK, bytes([fill])*0x10000)
    state.video = state.read(0x10006770, 4)
    state.put(state.video, bytes([fill])*256)
    state.write(WORK+80, 4, NODE)
    state.write(WORK+84, 4, NODE)
    state.write(NODE, 4, 0)
    state.write(NODE+12, 4, PAYLOAD)
    state.write(PAYLOAD+84, 4, pointer)
    if pointer: state.put(pointer, band)
    return state


def routing(q, program, fixture, band, kind, raw_flag, fill, work_type=6):
    state = memory(program, DISPATCH, fill, band, BUFFER+16)
    state.write(WORK, 4, work_type)
    if work_type == 7: state.write(WORK+80, 4, 0)  # This branch must skip list dereferences.
    state.write(WORK+116, 1, raw_flag)
    state.write(PAYLOAD+80, 4, kind)
    state.write(state.video+96, 4, WORK)
    latch = state.read(0x10006774, 4)
    state.write(latch, 4, 0x12345678)
    state.segments += fixture.segments
    before = state.bytes_at(WORK, 0x10000)
    runner = start(q, state, fixture, fixture.symbols['dispatch'], ())
    q.set_reg(11, state.video)
    at = stop(runner, {0x10013c97, 0x10013cad, 0x10013cb5})
    expected = 0x10013cb5 if work_type == 7 or kind not in (0, 1, 2) else 0x10013c97 if kind == 0 else 0x10013cad
    assert at == expected
    assert state.read(latch, 4) == (0x12345678 if work_type == 7 else 0)
    if at != 0x10013cb5: assert ar(q, 10) == WORK
    route_steps = runner.steps
    controls = [excluded(runner, pc) for pc in (0x10013c97, 0x10013cad, 0x10013cb5, 0x10014910, 0x10015214, 0x10015648)]
    state.code_ranges = FLAG+VECTORS
    previous = state.read(state.video+252, 4)
    runner = start(q, state, fixture, fixture.symbols['flag'], ())
    q.set_reg(11, WORK)
    q.set_reg(12, state.video)
    stop(runner, {0x10014baf})
    expected_flags = previous | 0x80000000 if raw_flag else previous & 0x7fffffff
    assert state.read(state.video+252, 4) == expected_flags
    flag_steps = runner.steps
    controls.append(excluded(runner, 0x10014baf))
    alternate = None
    if kind in (1, 2) and work_type != 7:
        state.code_ranges = ALTERNATE+VECTORS
        runner = start(q, state, fixture, 0x10015438, ())
        q.set_reg(11, WORK)
        stop(runner, {0x10015450})
        assert state.read(state.video+156, 4) == state.read(state.video+160, 4) == NODE
        assert not runner.services
        alternate = dict(steps=runner.steps, queued_pointer=hex(NODE), stop=hex(0x10015450))
        controls += [excluded(runner, pc) for pc in (0x10015450, 0x10014126)]
    assert state.bytes_at(WORK, 0x10000) == before
    return dict(status='pass', source_kind=kind, work_raw_flag=raw_flag, work_type=work_type, fill=fill,
                route='notification_boundary' if at == 0x10013cb5 else 'compressed_prepare_boundary' if kind == 0 else 'alternate_prepare_boundary',
                dispatch_steps=route_steps, stop=hex(at), flag_steps=flag_steps,
                resulting_irq_flags=expected_flags, alternate=alternate,
                payload_and_decoded_band_unchanged=True, rejected_before_execution=controls)


def builder(q, program, fixture, band, input_kind, fill):
    state = memory(program, BUILD_KIND, fill, band, BUFFER+16)
    descriptor = WORK+0x700
    state.write(descriptor, 4, BUFFER+16)
    state.write(descriptor+4, 4, input_kind)
    before = state.bytes_at(WORK, 0x10000)
    state.segments += fixture.segments
    runner = start(q, state, fixture, fixture.symbols['builder'], ())
    q.set_reg(11, PAYLOAD)
    q.set_reg(12, descriptor)
    stop(runner, {0x10010460})
    kind, pointer = (1, BUFFER+16) if input_kind == 1 else (2, 0)
    expected = bytearray(before)
    expected[PAYLOAD+80-WORK:PAYLOAD+84-WORK] = kind.to_bytes(4, 'big')
    expected[PAYLOAD+84-WORK:PAYLOAD+88-WORK] = pointer.to_bytes(4, 'big')
    assert state.bytes_at(WORK, 0x10000) == expected
    assert not runner.services
    return dict(status='pass', input_kind=input_kind, supplied_pointer=hex(BUFFER+16),
                source_kind=kind, result_pointer=hex(pointer), fill=fill, steps=runner.steps,
                stop=excluded(runner, 0x10010460),
                scope='Producer selection after omitted allocation/reset, before metadata, message construction and queue send.')


def select_pointer(q, program, fixture, band, kind, selector, fill, empty=False):
    pointer = BUFFER+16 if kind == 1 else 0
    state = memory(program, SELECT, fill, band, pointer)
    state.write(state.video+156, 4, 0 if empty else NODE)
    state.write(PAYLOAD+80, 4, kind)
    selector_cell = state.read(0x100067c8, 4)
    assert state.read(selector_cell, 4) == 2
    if selector is not None: state.write(selector_cell, 4, selector)
    effective_selector = 2 if selector is None else selector
    before = state.bytes_at(WORK, 0x10000)
    before_video = state.bytes_at(state.video, 256)
    state.segments += fixture.segments
    runner = start(q, state, fixture, fixture.symbols['select_pointer'], ())
    q.set_reg(11, state.video)
    at = stop(runner, {0x10014153, 0x100141ec, 0x10014241})
    assert at == (0x10014241 if empty else 0x10014153 if effective_selector == 1 else 0x100141ec)
    if not empty:
        assert [ar(q, i) for i in (5, 6, 7, 12)] == [kind, effective_selector, PAYLOAD, pointer]
    assert state.bytes_at(WORK, 0x10000) == before
    assert state.bytes_at(state.video, 256) == before_video
    assert not runner.services
    return dict(status='pass', source_kind=kind, selector=effective_selector,
                selector_source='stock_file' if selector is None else 'explicit_mutation',
                fill=fill, empty_head=empty, selected_pointer=None if empty else hex(pointer),
                steps=runner.steps, stop=hex(at), decoded_band_unchanged=True,
                rejected_before_execution=[excluded(runner, pc) for pc in
                    (0x10014153, 0x100141ec, 0x10014241, 0x10014126, 0x1001415f, 0x100141f8)],
                scope='Entered after omitted readiness/MMIO prefix; stops before either peripheral-output branch.')


def retirement(q, program, fixture, band, kind, refs, layout, fill):
    pointer = 0 if layout == 'null' else BUFFER+16 if layout == 'prefix16' else BUFFER
    state = memory(program, RETIRE+RANGES+READY_CODE, fill, band, pointer)
    event = state.read(0x100062dc, 4)
    for cell in (0x10006a9c, 0x10005d80, 0x10006ac0): state.write(state.read(cell, 4), 4, 0)
    invoke(state, 0x10017554, qemu=q)
    state.put(WORK+0xf00, bytes(256))
    state.write(state.read(0x10006a9c, 4), 4, WORK+0xf00)
    assert invoke(state, 0x10017ca0, [event, 0], qemu=q) == 0
    state.write(state.video+252, 4, 0x80001234)
    state.write(state.video+160, 4, NODE)
    state.write(PAYLOAD+78, 2, refs)
    state.write(PAYLOAD+80, 4, kind)
    before = state.bytes_at(WORK, 0x10000)
    state.segments += fixture.segments
    runner = start(q, state, fixture, fixture.symbols['retire'], ())
    q.set_reg(11, state.video)
    event_calls = []
    while q.reg(0) != 0x1001455a:
        if q.reg(0) == 0x10017dac: event_calls.append([ar(q, i) for i in (10, 11, 12)])
        runner.step()
    runner.synchronize(False)
    result_pointer = pointer-16 if refs and pointer else pointer
    result_refs = max(0, refs-1)
    assert state.read(PAYLOAD+84, 4) == result_pointer
    assert state.read(PAYLOAD+78, 2) == result_refs
    assert state.read(state.video+160, 4) == 0
    assert event_calls == ([[event, 8, 0]] if refs else [])
    assert state.read(event+8, 4) == (8 if refs else 0)
    assert runner.services == []
    expected = bytearray(before)
    expected[PAYLOAD+84-WORK:PAYLOAD+88-WORK] = result_pointer.to_bytes(4, 'big')
    expected[PAYLOAD+78-WORK:PAYLOAD+80-WORK] = result_refs.to_bytes(2, 'big')
    assert state.bytes_at(WORK, 0x10000) == expected
    controls = [excluded(runner, pc) for pc in (0x1001455a, 0x10014560, 0x100144d9, 0x10014126)]
    # The generic list cleanup executes separately after the excluded refresh.
    # Free calls are observed host boundaries, not successful heap reclamation.
    state.code_ranges = CLEANUP+VECTORS
    state.free_requests = []
    returned = invoke(state, 0x1000f0a8, [WORK+80, 0], qemu=q, host={FREE})
    expected_frees = [] if result_refs else ([result_pointer] if kind != 2 else [])+[NODE]
    assert state.free_requests == expected_frees
    assert returned == int(not result_refs)
    assert state.read(WORK+80, 4) == (NODE if result_refs else 0)
    if pointer: assert state.bytes_at(pointer, len(band)) == band
    return dict(status='pass', source_kind=kind, initial_refs=refs, layout=layout, fill=fill,
                initial_pointer=hex(pointer), result_pointer=hex(result_pointer), result_refs=result_refs,
                retirement_steps=runner.steps, event_calls=event_calls, next_raw_head=0,
                free_requests=[hex(x) for x in state.free_requests], allocator_executed=False,
                decoded_band_unchanged=True, rejected_before_execution=controls,
                outcome='conditional_unprefixed_release_address' if kind == 1 and refs == 1 and layout == 'base' else 'bounded_contract_observation')


def raw_mode_control(q, program, fixture, band, fill):
    state = memory(program, RETIRE, fill, band, BUFFER+16)
    state.write(state.video+252, 4, 0x1234)
    state.write(state.video+160, 4, NODE)
    before = state.bytes_at(WORK, 0x10000)
    before_video = state.bytes_at(state.video, 256)
    state.segments += fixture.segments
    runner = start(q, state, fixture, fixture.symbols['retire'], ())
    q.set_reg(11, state.video)
    stop(runner, {0x10014560})
    assert state.bytes_at(WORK, 0x10000) == before
    assert state.bytes_at(state.video, 256) == before_video
    assert not runner.services
    return dict(status='expected boundary', fill=fill, stop=excluded(runner, 0x10014560),
                steps=runner.steps, mutation='raw IRQ flag clear; raw retirement must not execute')


def main():
    spec = importlib.util.spec_from_file_location('image_checks', ROOT/'scripts/validate-hp1020-image-core.py')
    core = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = core
    spec.loader.exec_module(core)
    prefix = os.environ.get('XTENSA_PREFIX', '/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf')
    program = Program(ROOT/'analysis/sihp1020.elf', prefix)
    original = Machine(program)
    audited = []
    for (begin, end), digest in HASHES.items():
        data, offset = original.span(begin, end-begin, execute=True)
        raw = bytes(data[offset:offset+end-begin])
        assert core.sha(raw) == digest
        audited.append(dict(begin=hex(begin), end=hex(end), sha256=digest, bytes=raw.hex()))
    image_report = json.loads((core.OUT/'validation.json').read_text())
    for name, digest in {**image_report['source_sha256'], **image_report['fixture_sha256']}.items():
        assert core.sha((ROOT/name).read_bytes()) == digest, name
    image_elf = core.OUT/'target/target-check.elf'
    assert core.sha(image_elf.read_bytes()) == image_report['target']['elf_sha256']
    image_program, _ = core.audit_target(image_elf)
    bie_path = core.OUT/'fixtures/9600x132-stripe128-edges.jbg'
    bie = bie_path.read_bytes()
    with tempfile.TemporaryDirectory(prefix='hp1020-raw-contract-', dir='/tmp') as directory:
        folder = Path(directory)
        (folder/'wrapper.S').write_text(WRAPPER)
        core.command([prefix+'-as', '--text-section-literals', folder/'wrapper.S', '-o', folder/'wrapper.o'])
        core.command([prefix+'-ld', '-Ttext=0x20000000', '-e', 'dispatch', folder/'wrapper.o', '-o', folder/'wrapper.elf'])
        fixture = Program(folder/'wrapper.elf', prefix)
        fixture_bytes = fixture.path.read_bytes()
        full = ROOT/'vendor/foo2zjs-source'
        reference = folder/'reference'
        core.command(['clang', '-std=c11', '-O1', '-fsanitize=address,undefined', '-I'+str(full),
                      core.SRC/'reference.c', full/'jbig.c', full/'jbig_ar.c', '-o', reference])
        core.command([reference, 'decode', bie_path, folder/'pixels'])
        with QemuRAM() as q:
            q.load(image_elf)
            q.put(image_program.symbols['hp1020_image_input'], bie)
            assert q.call0(image_program.symbols['hp1020_image_run'], [len(bie), 7, 4, 204]) == 2
            band = q.read(image_program.symbols['hp1020_image_capture'], 4800)
            assert band == (folder/'pixels').read_bytes()[:4800]
            builders = [builder(q, program, fixture, band, kind, fill)
                        for kind in (0, 1, 2, 0xffffffff) for fill in (0, 204)]
            routes = [routing(q, program, fixture, band, kind, flag, fill)
                      for kind in (0, 1, 2, 3, 0xffffffff) for flag in (0, 1) for fill in (0, 204)]
            routes += [routing(q, program, fixture, band, 1, 1, fill, 7) for fill in (0, 204)]
            print(f'raw contract: {len(routes)} dispatch/flag fragments passed', flush=True)
            selections = [select_pointer(q, program, fixture, band, kind, selector, fill)
                          for kind in (1, 2) for selector in (None, 0, 1) for fill in (0, 204)]
            selections += [select_pointer(q, program, fixture, band, 1, None, fill, True) for fill in (0, 204)]
            retirements = [retirement(q, program, fixture, band, kind, refs, layout, fill)
                           for kind in (1, 2) for refs, layout in ((0, 'null'), (0, 'base'),
                           (1, 'prefix16'), (1, 'base'), (2, 'prefix16'), (2, 'base')) for fill in (0, 204)]
            mode_controls = [raw_mode_control(q, program, fixture, band, fill) for fill in (0, 204)]
            qemu_version = q.version
    sources = {ROOT/'scripts'/name for name in ('hp1020_xtensa_call0.py', 'hp1020_xtensa_stock.py',
        'hp1020_stock_stop.py', 'hp1020_stock_notifications.py', 'hp1020_qemu_ram.py', 'hp1020_qemu_pipeline.py',
        'hp1020_qemu_multitask.py', 'hp1020_qemu_stock_parser.py', 'hp1020_qemu_scheduler.py',
        'hp1020_qemu_scheduled_status.py', 'hp1020_qemu_task.py', 'hp1020_xtensa_properties.py')}
    sources.add(Path(__file__))
    sources.update(ROOT/name for name in image_report['source_sha256'])
    findings = [
        'The bounded original producer selection preserves the supplied pointer only when its input descriptor kind equals 1, setting payload source kind 1. Other tested input kinds set source kind 2 and pointer zero, even with a supplied nonzero pointer. This does not establish a generic borrowed-buffer input mode.',
        'Source kind 0 reaches compressed prepare; 1/2 reach alternate prepare; other kinds or work type 7 reach notification without rendering. The independent work raw flag changes the IRQ-family bit but does not change that dispatch.',
        'Separately entered alternate render stores the supplied node at both raw-list heads, then stops before raw refresh. Decoded image bytes and payload remain unchanged; physical image format is not established.',
        'After an omitted readiness/MMIO prefix, the original raw-list pointer fragment loads the decoded-band pointer for source kind 1 and the supplied null pointer for kind 2. The file-backed output selector is 2; mutation to 1 selects the other excluded output branch. Empty heads reach the return boundary. No pointer or count is written to a peripheral.',
        'After a skipped peripheral IRQ prefix, the original raw completion tail subtracts 16 from a nonzero payload pointer whenever its reference count is nonzero, decrements that count, sets the original JobMgr event and advances the raw head. This occurs for both source kinds 1 and 2.',
        'Separate generic cleanup observes buffer and node free requests for kind 1 once references reach zero, and only node free requests for kind 2. The allocator is supplied; actual freeing, pool ownership and concurrent reuse are not proven.',
        'An intentionally unprefixed kind-1 pointer with one reference yields a free request 16 bytes before its supplied buffer. This is a conditional fixture finding, not a stock fault: a reusable decoder-band pointer cannot be substituted without proving the prefix/ownership contract.',
        'Source kind 2 also controls a hardware flag in the separately audited raw-refresh bytes. Avoiding its buffer-free request is not evidence that it is a suitable physical format or mode.'
    ]
    limits = 'Separate fragments with supplied RAM, work metadata and completion entry. Remaining prepare/render/refill paths, the peripheral IRQ prefix, engine operations, custom callbacks and all USB operations are excluded. Event creation/set executes original RTOS code with no waiters. No boot, complete page lifecycle, DMA, physical output or automatic asynchronous consumer is claimed.'
    report = dict(status='pass', builder_cases=builders, dispatch_cases=routes, selection_cases=selections,
                  retirement_cases=retirements, raw_mode_controls=mode_controls,
                  completed_lifecycles=0, custom_callbacks_executed=0, allocator_executed=False,
                  image_band=dict(bytes=len(band), sha256=core.sha(band), bie_sha256=core.sha(bie),
                                  image_elf_sha256=core.sha(image_elf.read_bytes()),
                                  scope='First four decoded rows from current open target execution, compared with original full host decoding, then copied as a separate stock RAM fixture.'),
                  source_sha256={str(p.relative_to(ROOT)):core.sha(p.read_bytes()) for p in sorted(sources)},
                  fixture_source=WRAPPER, fixture_source_sha256=core.sha(WRAPPER.encode()),
                  fixture_elf_sha256=core.sha(fixture_bytes), fixture_elf_bytes=fixture_bytes.hex(),
                  audited_stock_ranges=audited, stock_elf_sha256=core.sha(program.path.read_bytes()),
                  qemu_version=qemu_version, findings=findings, limits=limits)
    OUT.with_suffix('.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    OUT.with_suffix('.md').write_text('# Original raw buffer contract fragments\n\n'
        +f'{len(builders)} producer-selection, {len(routes)} dispatch/flag, {len(selections)} raw-pointer selection and {len(retirements)} conditional retirement/cleanup cases pass, plus two raw-mode boundary controls. No completed lifecycles.\n\n'
        +'\n'.join('- '+s for s in findings)+'\n\n'+limits+'\n')
    print(f'raw contract: {len(builders)} producer, {len(routes)} dispatch/flag, {len(selections)} pointer and {len(retirements)} retirement/cleanup observations; no lifecycles')


if __name__ == '__main__':
    main()
