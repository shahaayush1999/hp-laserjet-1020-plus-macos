#!/usr/bin/env python3
"""Focused exact-cookie retained-fault admission through the reusable adapter.

This keeps its 20 scenarios and report separate from the 132-case baseline and
from continuous-document validation. All controller events and settlement are
synthetic; no device access, firmware upload or physical printing occurs.
"""
import argparse
import json
from pathlib import Path
import runpy
import shutil
import struct
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'analysis/usb-path/tinyusb-printer'

OK, WAIT, STALE, INVALID, LIMIT, ERROR = range(6)
STOPPED = 3
FAULT = 0x80000201
DEVICE = bytes.fromhex('1201000200000040feca0040000100000001')
DEVICE_ID = b'\x01\x90' + bytes(65 + i % 26 for i in range(398))


def packet(kind, request, value=0, index=0, length=0):
    return struct.pack('<BBHHH', kind, request, value, index, length)


def packet_fault_profiles():
    names = ('current-in-data', 'current-out-status', 'pending-recovery',
             'direct-address', 'identity-and-busy', 'settled-and-reused',
             'superseded-setup', 'older-generation', 'bulk', 'transport-limit')
    return [('packet-fault/' + name, fill, 64, 3)
            for fill in (0, 204) for name in names]


def packet_fault_scenario(h, name, document, images):
    """Expected wire bytes, identities and state changes are independent inputs."""
    name = name.removeprefix('packet-fault/')
    small = document(['small'])

    def unchanged(op, a=0, b=0, c=0, d=0, result=OK):
        before = tuple(h.row[1:])
        h.step(op, a, b, c, d, result=result)
        assert tuple(h.row[1:]) == before, ('fault must have no side effects', h.row)

    def report_current(token):
        before = h.row.copy()
        h.step(19, token, FAULT)
        assert h.row[4] == before[4] + 1 and h.row[5] == before[5]
        assert h.row[7] == h.row[9] == h.row[36] == 1
        assert h.row[44:46] == [0, 0] and h.row[47] == 0
        assert h.row[13] == before[13] and h.row[14] == before[13]
        # Retained packet lengths, wire proposals and document storage cannot
        # change merely because a descriptor observation reported a fault.
        same = (17, 18, 19, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35,
                50, 52, 53, 54, 55, 60, 61, 80)
        assert all(h.row[i] == before[i] for i in same), h.row
        unchanged(19, token, FAULT)
        unchanged(19, token, FAULT + 1)  # Same packet, second observed reason.
        unchanged(1)
        h.step(6, result=WAIT)
        h.step(7, result=STOPPED)
        assert h.row[34] == before[34] and h.row[50] == before[50]

    def fresh_document():
        h.recover()
        h.send(small, min(64, h.capacity))
        h.close_finish(1, 1)
        h.expected_pixels += images['small'][1]

    def continue_document(token):
        h.complete(token, 31)
        h.step(7)
        h.send(small[31:], min(64, h.capacity))
        h.close_finish(1, 1)
        h.expected_pixels += images['small'][1]

    if name == 'pending-recovery':
        h.step(5)
        h.service()
        h.setup(packet(0, 9, 1))
        token = h.row[28]
        assert token == 1 and h.row[29] == 0 and h.row[17] == 1
        assert h.row[80] == 0 and h.row[42:46] == [1, 1, 1, 0]
        h.wire(b'', 'initial-configuration-status-remains-owned')
        h.step(10, 0)
        for part in (1, 2, 4):
            if part == 4:
                h.step(15)
            h.step(11, 0, part)
        assert h.row[45] == 7
        report_current(token)
        h.step(11, 0, 1, result=STALE)
        h.step(12, 0, result=STALE)
        assert h.row[32] == 1 and h.row[80] == 0 and h.row[17] == 1
        h.step(4, token)  # Supplied settled cancellation, distinct from request.
        h.service()
        assert not h.row[28] and h.row[17] == 1 and h.row[80] == 0
        h.begin_reset(slot=1)
        assert h.row[42] == 2 and h.row[80] == 1
        for part in (1, 2, 4):
            if part == 4:
                h.step(15)
            h.step(11, 1, part)
        assert h.row[45] == 7
        unchanged(19, token, FAULT, result=STALE)
        assert h.row[42:46] == [2, 1, 1, 7]
        h.step(12, 1, expect={32: 2, 7: 0, 9: 0, 36: 0})
        assert h.row[17] == 2 and h.row[80] == 1
        h.control_status('only-real-reset-submits-recovery-status')
        h.send(small, 64)
        h.close_finish(1, 1)
        h.expected_pixels += images['small'][1]
        return

    if name == 'direct-address':
        h.step(5)
        h.service()
        h.setup(packet(0, 5, value=37))
        token = h.row[28]
        assert token == 1 and h.row[29] == 0 and h.row[17] == 1
        assert h.row[64] == 0 and h.row[65] == 37
        h.wire(b'', 'faulted-address-status')
        report_current(token)
        h.complete(token, 0)  # Real late SUCCESS still must not commit address.
        assert h.row[64] == 0 and h.row[17] == 1 and not h.row[28]
        unchanged(19, token, FAULT, result=STALE)
        h.request(packet(0x80, 6, value=0x100, length=18), DEVICE)
        assert h.row[64] == 0 and h.row[80] == 0
        return

    if name == 'older-generation':
        h.step(5)
        h.service()
        h.setup(packet(0, 9, 1))
        old = h.row[28]
        assert old == 1 and h.row[88] == 1
        h.wire(b'', 'old-generation-configuration-status')
        h.step(10, 0)
        for part in (1, 2, 4):
            if part == 4:
                h.step(15)
            h.step(11, 0, part)
        h.step(12, 0, expect={32: 2, 7: 0, 9: 0, 36: 0})
        assert h.row[28] == old and h.row[17] == 1 and h.row[80] == 0
        out = h.arm_write(small[:31])
        unchanged(19, old, FAULT, result=STALE)
        assert not h.row[7] and not h.row[9] and not h.row[14]
        h.step(4, old)  # Retire only old EP0; no inferred new-generation fault.
        h.service()
        assert h.row[30] == out and not h.row[7] and not h.row[36]
        assert h.row[32] == 2 and not h.row[14]
        h.request(packet(0x80, 6, value=0x100, length=18), DEVICE)
        continue_document(out)
        return

    h.configure()

    if name in ('current-in-data', 'current-out-status'):
        h.transfer(small[:11])  # READY but unconsumed input must stop immediately.
        out = h.arm_write(small[11:31])
        if name == 'current-in-data':
            h.setup(packet(0xa1, 0, index=h.interface << 8, length=400))
            token, count = h.row[28], 64
            h.wire(DEVICE_ID[:64], 'faulted-first-device-ID-packet')
        else:
            h.setup(packet(0xa1, 1, index=h.interface, length=1))
            h.wire(b'\x18', 'successful-port-status-data')
            h.complete(h.row[28], 1)
            token, count = h.row[26], 0
        assert token and h.row[46] == h.row[77] == 1
        report_current(token)
        submitted, wire_bytes = h.row[17], h.row[24]
        h.step(4, out)
        h.service()
        # This is actual explicit settlement, not a synthesized fault event.
        h.complete(token, count)
        assert h.row[17] == submitted and h.row[24] == wire_bytes
        assert not h.row[26] and not h.row[28] and not h.row[30]
        assert h.row[46] == h.row[77] == 0 and h.row[34] == h.row[50] == 0
        unchanged(19, token, FAULT, result=STALE)
        h.request(packet(0x80, 6, value=0x100, length=18), DEVICE)
        fresh_document()
        return

    if name == 'identity-and-busy':
        out = h.arm_write(small[:31])
        h.setup(packet(0xa1, 1, index=h.interface, length=1))
        token = h.row[28]
        h.wire(b'\x18', 'identity-check-held-status')
        unchanged(19, 0, FAULT, result=STALE)
        # Independently perturb every cookie field; endpoint aliases are exact,
        # never normalized to the same owner. The saved original remains intact.
        for field, xor in ((1, 1), (1, token), (2, 1), (3, 1), (4, 1),
                           (5, 0x80), (5, 0x10), (5, 1)):
            unchanged(19, token, FAULT, field, xor, result=STALE)
        unchanged(19, token, 0)  # Zero reason does not latch a hidden fault.
        unchanged(20, 1, token, FAULT, result=WAIT)
        assert not h.row[7] and not h.row[14] and h.row[30] == out
        report_current(token)  # Also detects a hidden latch from a forged call.
        fault_epoch, submitted = h.row[4], h.row[17]
        h.complete(token, 0, usb_result=1)  # Genuine failed settlement, not a new fault.
        assert h.row[4] == fault_epoch and h.row[17] == submitted
        h.step(4, out)
        h.service()
        fresh_document()
        return

    if name == 'settled-and-reused':
        h.setup(packet(0x80, 6, value=0x100, length=18))
        old = h.row[28]
        h.wire(DEVICE, 'descriptor-before-pending-state-check')
        h.complete(old, 18, service=False)
        unchanged(19, old, FAULT, result=STALE)  # Settled/PENDING, not DCD-owned.
        h.service()
        status = h.row[26]
        assert status and not h.row[28]
        unchanged(19, old, FAULT, result=STALE)
        h.complete(status, 0)
        unchanged(19, status, FAULT, result=STALE)
        h.setup(packet(0x80, 6, value=0x100, length=18))
        assert h.row[28] != old
        unchanged(19, old, FAULT, result=STALE)  # Same endpoint/address reused.
        h.control_in(DEVICE, 'new-descriptor-after-old-fault')
        assert not h.row[7] and not h.row[9] and not h.row[36]
        return

    if name == 'superseded-setup':
        out = h.arm_write(small[:31])
        h.setup(packet(0xa1, 0, index=h.interface << 8, length=400))
        old = h.row[28]
        h.wire(DEVICE_ID[:64], 'superseded-retained-device-ID')
        h.setup(packet(0x80, 6, value=0x100, length=18), service_result=WAIT)
        assert h.row[14] == 2 and not h.row[7] and h.row[30] == out
        unchanged(19, old, FAULT, result=STALE)  # Exact owner, superseded epoch.
        h.step(4, old)
        h.service()
        assert h.row[28] != old and h.row[30] == out and not h.row[7]
        unchanged(19, old, FAULT, result=STALE)
        h.control_in(DEVICE, 'new-request-survives-old-fault')
        continue_document(out)
        return

    if name == 'bulk':
        token = h.arm_write(small[:31])
        report_current(token)
        h.complete(token, 31)  # Clear core BUSY without consuming faulted data.
        assert not h.row[30] and not h.row[81] and not h.row[34] and not h.row[50]
        unchanged(19, token, FAULT, result=STALE)
        fresh_document()
        return

    if name == 'transport-limit':
        h.setup(packet(0xa1, 1, index=h.interface, length=1))
        token = h.row[28]
        h.wire(b'\x18', 'retained-status-at-fence-identity-limit')
        h.step(20, 0, 0xffffffff)  # Test-only counter seed, never a repair API.
        submitted, generation = h.row[17], h.row[32]
        h.step(19, token, FAULT, result=LIMIT)
        assert h.row[4] == 0xffffffff and h.row[86] == 1
        assert h.row[7] == h.row[9] == h.row[36] == 1
        assert h.row[28] == token and h.row[14] == 2 and h.row[17] == submitted
        unchanged(19, token, FAULT, result=LIMIT)
        h.step(4, token)
        h.service(result=LIMIT)
        assert not h.row[28] and not h.row[46] and not h.row[77]
        assert h.row[17] == submitted and h.row[32] == generation
        unchanged(19, token, FAULT, result=STALE)
        h.step(6, result=LIMIT)
        return

    raise AssertionError('unknown packet-fault scenario: ' + name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', action='store_true')
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT / 'scripts'))
    base = runpy.run_path(str(ROOT / 'scripts/validate-hp1020-tinyusb-printer.py'))
    Host, core, stats_count = base['Host'], base['core'], base['STATS']
    assert stats_count == 96
    OUT.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix='hp1020-tinyusb-packet-fault-', dir='/tmp'))
    print('Retained packet fault captures: ' + str(temp), flush=True)

    # Freeze all implementation/harness/oracle sources before compiling or
    # executing anything. The existing helper also preserves pinned originals.
    tested = base['sources'](temp)
    this_script = Path(__file__).resolve()
    script_name = str(this_script.relative_to(ROOT))
    raw_script = this_script.read_bytes()
    tested[script_name] = core.sha(raw_script)
    script_copy = temp / 'source' / script_name
    script_copy.parent.mkdir(parents=True, exist_ok=True)
    script_copy.write_bytes(raw_script)
    (temp / 'source-sha256.json').write_text(json.dumps(tested, indent=2) + '\n')

    # The shared image_documents helper consumes these exact six inputs. Capture
    # their bytes and hashes BEFORE its reference decoder runs, never only after.
    # Assert its returned path set so a future base-helper change fails closed.
    pages_out = base['pages'].OUT
    named_images = (
        ('small', pages_out / 'fixtures/32x8-stripe4-black.jbg'),
        ('medium', pages_out / 'fixtures/9600x132-stripe128-edges.jbg'),
        ('wide', pages_out / 'fixtures/16384x4-stripe128-edges.jbg'),
        ('partial', pages_out / 'output-fixtures/1024x260-stripe128-repeat.jbg'),
        ('slim', pages_out / 'output-fixtures/64x12-stripe4-edges.jbg'),
    )
    input_paths = [path for _, path in named_images] + [
        ROOT / 'analysis/samples/generated/matrix-a4_default.zjs']
    fixture_bytes, fixture_hashes = {}, {}
    for path in input_paths:
        name = str(path.relative_to(ROOT))
        raw = path.read_bytes()
        fixture_bytes[name] = raw
        fixture_hashes[name] = core.sha(raw)
        captured = temp / 'fixtures' / name
        captured.parent.mkdir(parents=True, exist_ok=True)
        captured.write_bytes(raw)
    (temp / 'fixture-sha256.json').write_text(json.dumps(fixture_hashes, indent=2) + '\n')

    def unchanged_inputs():
        assert all(core.sha((ROOT / n).read_bytes()) == digest
                   for n, digest in tested.items()), 'source changed during execution'
        assert all(core.sha((ROOT / n).read_bytes()) == digest
                   for n, digest in fixture_hashes.items()), 'fixture changed during execution'

    unchanged_inputs()
    effective = runpy.run_path(str(ROOT / 'scripts/prepare-hp1020-tinyusb.py'))['prepare'](
        temp / 'effective-source', True)
    base['compile_host'](temp, temp / 'effective-source')
    unchanged_inputs()
    document, images, fixtures = base['image_documents'](temp)
    assert {p.resolve() for p in fixtures} == {p.resolve() for p in input_paths}
    for image_name, path in named_images:
        assert images[image_name][0] == fixture_bytes[str(path.relative_to(ROOT))]
    unchanged_inputs()

    profiles = packet_fault_profiles()
    assert len(profiles) == 20
    cases, replay = [], []
    for index, (name, fill, capacity, interface) in enumerate(profiles):
        directory = temp / f'case-{index:03}'
        directory.mkdir()
        title = f'{name}/fill={fill}/capacity={capacity}/interface={interface}'
        (directory / 'case-name').write_text(title + '\n')
        h = Host(temp / 'host', directory, fill, capacity, interface)
        try:
            packet_fault_scenario(h, name, document, images)
            captures = h.finish()
        finally:
            h.abort()
        cases.append(dict(case=title, scenario=name, fill=fill, capacity=capacity,
            interface=interface, status='pass', initial=h.initial, steps=h.rows,
            events=h.events, packet_oracles=h.packets,
            measured_host_state_and_memory_bytes=h.row[59],
            expected_pixels_sha256=core.sha(h.expected_pixels),
            pixels_bytes=len(h.expected_pixels),
            capture_sha256={n: core.sha(data) for n, data in captures.items()}))
        replay.append((h, captures, directory))
        print(f'Retained packet fault: {len(cases)}/{len(profiles)} host cases passed', flush=True)
    unchanged_inputs()

    target = None
    if args.target:
        core.command(['bash', ROOT / 'scripts/build-hp1020-tinyusb-printer-target.sh'])
        built = OUT / 'target'
        assert json.loads((built / 'effective-source.json').read_text()) == effective
        # Execute the captured ELF, not a potentially overwritten shared build
        # path. Preserve the exact map/symbol/stack-usage artifacts beside it.
        saved_target = temp / 'target'
        saved_target.mkdir()
        for path in sorted(built.iterdir()):
            if path.is_file() and path.name != 'annotated-disassembly.txt':
                shutil.copyfile(path, saved_target / path.name)
        elf = saved_target / 'target-check.elf'
        target_hashes = {p.name: core.sha(p.read_bytes()) for p in saved_target.iterdir()
                         if p.is_file()}
        unchanged_inputs()
        program, audit = core.audit_target(elf)
        assert all(core.sha((saved_target / n).read_bytes()) == digest
                   for n, digest in target_hashes.items()), 'audit changed a build artifact'
        # The audit creates its own path-specific listing; snapshot that derived
        # artifact now, while preserving the earlier hashes of all build inputs.
        target_hashes['annotated-disassembly.txt'] = core.sha(
            (saved_target / 'annotated-disassembly.txt').read_bytes())
        (temp / 'target-sha256.json').write_text(json.dumps(target_hashes, indent=2)+'\n')
        from hp1020_qemu_ram import QemuRAM
        native = []
        with QemuRAM() as q:
            version = q.version
            for case, (h, captures, directory) in zip(cases, replay):
                q.load(elf)
                assert q.call0(program.symbols['hp1020_bulk_fixture_reset'],
                    [case['fill'], case['capacity'], case['interface'], 0xffffffff]) == 0
                initial = list(struct.unpack(f'>{stats_count}I',
                    q.read(program.symbols['hp1020_bulk_fixture_stats'], stats_count * 4)))
                # Only sizeof-based statistic59 may vary between host and target.
                assert initial[:59] + initial[60:] == h.initial[:59] + h.initial[60:]
                for index, (event, host_row) in enumerate(zip(h.events, h.rows)):
                    data = bytes.fromhex(event['data_hex'])
                    if data:
                        q.put(program.symbols['hp1020_bulk_fixture_input'], data)
                    result = q.call0(program.symbols['hp1020_bulk_fixture_step'], event['words'])
                    row = list(struct.unpack(f'>{stats_count}I',
                        q.read(program.symbols['hp1020_bulk_fixture_stats'], stats_count * 4)))
                    with (directory / 'target-steps.jsonl').open('a') as saved:
                        saved.write(json.dumps(row) + '\n')
                    assert result == row[0] == event['result'] and row[15:17] == [0, 1]
                    assert row[:59] + row[60:] == host_row[:59] + host_row[60:], (
                        case['case'], index, row, host_row)
                observed = {}
                for name, symbol in (('pixels', 'hp1020_bulk_fixture_pixels'),
                                     ('wire', 'hp1020_bulk_fixture_wire')):
                    observed[name] = q.read(program.symbols[symbol], len(captures[name]))
                for name, function in (('receive', 'hp1020_bulk_fixture_receive_storage'),
                                       ('output', 'hp1020_bulk_fixture_output_storage')):
                    address = q.call0(program.symbols[function], [])
                    observed[name] = q.read(address, len(captures[name]))
                for name, data in observed.items():
                    (directory / ('target-' + name)).write_bytes(data)
                    assert data == captures[name], (case['case'], name)
                native.append(dict(case=case['case'], status='pass', all_steps_equal=True,
                    all_pixels_wire_and_storage_equal=True,
                    measured_target_state_and_memory_bytes=row[59],
                    capture_sha256={n: core.sha(data) for n, data in observed.items()}))
                print(f'Retained packet fault: {len(native)}/{len(cases)} target cases passed', flush=True)
        assert all(core.sha((saved_target / n).read_bytes()) == digest
                   for n, digest in target_hashes.items()), 'captured target changed during replay'
        target = dict(status='pass', cases=native, qemu_version=version,
            elf_sha256=core.sha(elf.read_bytes()), audit=audit,
            captured_artifact_sha256=target_hashes)
    unchanged_inputs()
    report = dict(status='pass', source_sha256=tested, fixture_sha256=fixture_hashes,
        effective_source=effective, captures=str(temp), cases=cases, target=target,
        completed_native_page_lifecycles=0, usb_transfers=0,
        scope='Exact-cookie retained packet faults through the reusable adapter and patched pinned TinyUSB, with independent wire/pixel oracles and supplied ownership settlement.',
        limits='No controller/MMIO/IRQ/cache/DMA implementation, USB traffic, firmware upload or physical printing. These 20 focused profiles are separate from the ordinary 132-case adapter baseline and continuous-document validation. Recovery documents here use the existing explicit stream-close path. Faults never establish settlement or class reset promises.')
    report_name = 'packet-fault-validation' if args.target else 'packet-fault-host-validation'
    raw_report = json.dumps(report, separators=(',', ':'), sort_keys=True) + '\n'
    (temp / (report_name + '.json')).write_text(raw_report)
    (OUT / (report_name + '.json')).write_text(raw_report)
    (OUT / (report_name + '.md')).write_text('# Exact-cookie retained packet fault validation\n\n' +
        report['scope'] + '\n\n' +
        f'{len(cases)} host cases; {len(target["cases"]) if target else 0} QEMU cases. '
        'Every replay compares all96 statistics except the measured sizeof statistic59, '
        'and exact wire/pixels/receive/output storage.\n\n' + report['limits'] + '\n')


if __name__ == '__main__':
    main()
