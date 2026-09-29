#!/usr/bin/env python3
"""Printer-class control requests composed with real software page decoding.

All setup, completion, status and quiescence observations are synthetic. No USB
controller, endpoint traffic, MMIO or printer operation is implemented or tested.
"""
import argparse
import importlib.util
import itertools
import json
from pathlib import Path
import shutil
import struct
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('printer_pages', ROOT/'scripts/validate-hp1020-image-pages.py')
pages = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = pages
spec.loader.exec_module(pages)
core, IMG, SEM = pages.core, pages.SRC, pages.SEM
SRC = ROOT/'open-firmware/usb-printer-class'
RX = ROOT/'open-firmware/usb-receive-core'
OUT = ROOT/'analysis/usb-path/printer-class'
OK, WAIT, STALE, INVALID, LIMIT, DOCUMENT_ERROR = range(6)
RX_STOPPED = 3
DONE = 0x88000000
DEVICE_ID = b'\x01\x90' + bytes(65 + i % 26 for i in range(398))


def event(op, a=0, b=0, c=0, d=0, data=b'', result=OK, expect=None, **extra):
    return dict(words=[op, a, b, c, d], data=data, result=result, expect=expect or {}, **extra)


def setup(kind, request, value=0, index=0, length=0, status=0, known=0, result=OK, expect=None):
    return event(0, 8, known, status, data=struct.pack('<BBHHH', kind, request, value, index, length),
                 result=result, expect=expect)


def take(data=b'', kind=1, fallback=0, slot=0, request=None):
    return event(1, slot, reply=data, kind=kind, fallback=fallback, request=request)


def reset(kind=0x21, interface=0):
    return setup(kind, 2, index=interface, expect={5: 1, 6: 0, 20: 1})


def reset_steps(ticket=0, order=(1, 2, 4), generation=1):
    steps = [event(2, ticket), event(4, ticket, result=WAIT), event(1, result=WAIT)]
    mask = 0
    for part in order:
        mask |= part
        steps += [event(3, ticket, part, expect={6: mask}),
                  event(3, ticket, part, expect={6: mask})]
        if mask != 7:
            steps += [event(4, ticket, result=WAIT, expect={16: generation, 20: 1}),
                      event(1, result=WAIT)]
    steps.append(event(4, ticket, expect={5: 0, 6: 0, 16: generation + 1, 20: 0, 21: 0, 22: 0}))
    return steps


def transfers(data, packet=512):
    result = []
    for offset in range(0, len(data), packet):
        part = data[offset:offset + packet]
        result += [event(7, 1024, len(part), 0, data=part),
                   event(8, 0, DONE | len(part)), event(9)]
    return result


def candidates(doc, body, images, base):
    cases = []

    def add(name, events, pixels=b'', fill=204, config=0, invalid=0, prefix=None):
        cases.append(dict(name=name, events=events, pixels=pixels, fill=fill,
                          config=config, invalid=invalid, prefix=prefix))

    for config in (0, 0x010302):
        ci, interface, alternate = config & 255, (config >> 8) & 255, (config >> 16) & 255
        for fill in (0, 204):
            events = []
            for length in (0, 1, 2, 255, 256, 399, 400, 401, 65535):
                events += [setup(0xa1, 0, ci, (interface << 8) | alternate, length),
                           take(DEVICE_ID[:length]), event(1, result=WAIT), event(5),
                           event(5, result=STALE)]
            add(f'id/config={config}/fill={fill}', events, fill=fill, config=config)
            events = []
            for status in range(0, 0x40, 8):
                events += [setup(0xa1, 1, index=interface, length=1, known=2, status=status),
                           take(bytes([status])), event(5)]
            for mode in (0, 1):
                events += [setup(0xa1, 1, index=interface, length=1, known=mode, status=255),
                           take(b'\x18', fallback=1), event(5)]
            for mode, value in ((2, 1), (2, 0x80), (2, 0xff), (3, 0x18)):
                events += [setup(0xa1, 1, index=interface, length=1, known=mode, status=value,
                                 result=INVALID), take(kind=3), event(5)]
            add(f'status/config={config}/fill={fill}', events, fill=fill, config=config)

        valid_id = [0xa1, 0, ci, (interface << 8) | alternate, 400]
        valid_status = [0xa1, 1, 0, interface, 1]
        valid_reset = [0x21, 2, 0, interface, 0]
        events = []
        mutations = [(valid_id, 0, 0x21), (valid_id, 1, 3), (valid_id, 2, ci + 1),
                     (valid_id, 3, ((interface + 1) << 8) | alternate),
                     (valid_id, 3, (interface << 8) | (alternate + 1)),
                     (valid_status, 0, 0x81), (valid_status, 1, 3), (valid_status, 2, 1),
                     (valid_status, 3, interface + 1), (valid_status, 4, 0),
                     (valid_status, 4, 2), (valid_reset, 0, 0xa1), (valid_reset, 0, 0x20),
                     (valid_reset, 1, 3), (valid_reset, 2, 1), (valid_reset, 3, interface + 1),
                     (valid_reset, 4, 1)]
        for values, field, value in mutations:
            changed = values.copy()
            changed[field] = value
            events += [setup(*changed, result=INVALID, expect={20: 0, 5: 0}),
                       take(kind=3), event(5)]
        for length in (0, 7, 9):
            events += [event(0, length, data=bytes(9), result=INVALID, expect={20: 0}),
                       take(kind=3), event(5)]
        add(f'invalid-wire-fields/config={config}', events, config=config)

    for fill, kind, order in itertools.product((0, 204), (0x21, 0x23), itertools.permutations((1, 2, 4))):
        events = [event(2, result=WAIT), event(3, result=STALE), reset(kind)]
        events += reset_steps(order=order)
        events += [take(kind=2), event(4, result=STALE), event(5),
                   event(6, 1, 0x200, result=STALE, expect={16: 2, 20: 0})]
        add(f'reset/type={kind}/order={order}/fill={fill}', events, fill=fill)

    for order in itertools.permutations((1, 2, 4)):
        events = [reset(), event(2), event(3, 0, 1), event(3, 0, 2), event(3, 0, 4),
                  reset(), event(2, 1), event(3, 0, 1, result=STALE), event(4, result=STALE),
                  event(4, 1, result=WAIT)]
        events += reset_steps(1, order)
        events += [take(kind=2, request=2), event(5)]
        add(f'repeated-reset/order={order}', events)

    for kind in (0x21, 0x23):
        add(f'reset/nonzero-interface/type={kind}', [reset(kind, 3)] + reset_steps() +
            [take(kind=2), event(5)], config=0x010302)

    events = [reset(), event(2)]
    for part in (0, 3, 7, 8, 0xffffffff):
        events.append(event(3, 0, part, result=INVALID, expect={6: 0, 20: 1}))
    for req, gen in ((0, 1), (1, 0), (2, 1), (1, 2), (0xffffffff, 0xffffffff)):
        events += [event(12, 1, req, gen), event(3, 1, 1, result=STALE),
                   event(4, 1, result=STALE)]
    events += reset_steps() + [take(kind=2), event(5)]
    add('invalid-reset-parts-and-tickets', events)

    for supersede in ('id', 'status', 'malformed'):
        for early_reply in (False, True):
            new_setup = (setup(0xa1, 0, length=12) if supersede == 'id' else
                         setup(0xa1, 1, length=1, known=2, status=0x30) if supersede == 'status' else
                         setup(0xa1, 3, result=INVALID))
            response = (take(DEVICE_ID[:12], request=2) if supersede == 'id' else
                        take(b'\x30', request=2) if supersede == 'status' else take(kind=3, request=2))
            events = [reset(), event(2), event(3, 0, 1), new_setup]
            if early_reply:
                events.append(response)
            events += [event(3, 0, 2), event(4, result=WAIT), event(3, 0, 4),
                       event(4, expect={16: 2, 20: 0})]
            if not early_reply:
                events.append(response)
            events += [event(5), event(1, result=WAIT), event(4, result=STALE)]
            add(f'superseded-reset/{supersede}/early={early_reply}', events)

    events = [setup(0xa1, 1, length=1, known=2, status=8), take(b'\x08'),
              setup(0xa1, 1, length=1, known=2, status=0x30), event(14, 2, result=STALE),
              event(1, result=WAIT, expect={15: 8, 8: 1, 9: 1}), reset(), event(2),
              event(6, 1, 0x200, expect={5: 0, 20: 1, 15: 8}), event(4, result=STALE),
              setup(0xa1, 1, length=1, known=2, status=0x30), event(1, result=WAIT, expect={15: 8}),
              event(14, 4, result=STALE), event(5), take(b'\x30', slot=1, request=4),
              event(5, result=STALE), event(5, 1), reset()]
    events += reset_steps() + [take(kind=2, request=5), event(5)]
    add('ep0-old-status-retained-through-supersession-reset-fault', events)
    for kind in (0x21, 0x23):
        events = [reset(kind), event(2), event(3, 0, 1), event(3, 0, 2), event(3, 0, 4),
                  event(6, 1, 0, expect={5: 1, 6: 7}), event(6, 1, 0x80, expect={5: 0, 6: 0}),
                  event(3, 0, 4, result=STALE), event(4, result=STALE), take(kind=3), event(5), reset(kind)]
        events += reset_steps() + [take(kind=2), event(5), event(6, 1, 0x200, result=STALE),
                                  event(6, 2, 0, expect={20: 0})]
        add(f'fault-invalidates-reset/type={kind}', events)

    add('request-identity-exhaustion-retains-ep0', [event(11, 0xfffffffe, 1),
        setup(0xa1, 1, length=1, known=2, status=0x28), take(b'\x28', request=0xffffffff),
        setup(0xa1, 0, length=10, result=LIMIT, expect={1: 0, 2: 0, 7: 1, 20: 1, 15: 0x28}),
        event(1, result=LIMIT), event(2, result=LIMIT), event(3, 0, 1, result=LIMIT),
        event(4, result=LIMIT), event(14, 1, result=STALE), event(5), event(5, result=STALE),
        setup(0x21, 2, result=LIMIT), event(7, 1024, 0, result=RX_STOPPED)])
    add('receive-generation-exhaustion', [event(11, 0, 0xffffffff), reset(), event(2),
        event(3, 0, 4), event(3, 0, 2), event(3, 0, 1),
        event(4, result=LIMIT, expect={7: 1, 16: 0xffffffff, 20: 1}),
        event(1, result=LIMIT), event(2, result=LIMIT), setup(0x21, 2, result=LIMIT)])
    for invalid in (1, 2, 3, 4):
        add(f'invalid-initialization/{invalid}', [setup(0xa1, 0, length=20, result=INVALID,
            expect={46: 0, 49: INVALID}), event(1, result=INVALID), event(2, result=INVALID),
            event(3, 0, 1, result=INVALID), event(4, result=INVALID), event(5, result=INVALID),
            event(6, 1, 0x80, result=INVALID)], invalid=invalid)

    # Stop after BID, before END_JBIG/END_PAGE/END_DOC. Accepted output remains
    # in flight. The independent decoder supplies source pixels for both jobs.
    partial = b'JZJZ' + pages.pack([base[0]] + body('medium')[:3])
    events = [event(11, 0, 0xffffffff)] + transfers(partial)
    marker = len(events) - 1
    events += [reset(), event(2), event(3, 0, 1), event(3, 0, 2), event(3, 0, 4),
               event(4, result=LIMIT, expect={7: 1, 16: 0xffffffff, 20: 1}),
               event(1, result=LIMIT), event(9, result=RX_STOPPED)]
    add('generation-exhaustion-retains-accepted-output', events,
        prefix=dict(marker=marker, source=images['medium'][1]))
    for fill, order in itertools.product((0, 204), itertools.permutations((1, 2, 4))):
        events = transfers(partial, 512)
        events[0]['words'][3] = 5
        events[1]['words'][1] = 5
        marker = len(events) - 1
        events += [event(7, 1024, 3, 7, data=b'old'), reset(), event(2),
                   event(9, result=RX_STOPPED), event(10, result=RX_STOPPED)]
        events += reset_steps(order=order)
        events += [take(kind=2), event(5), event(8, 7, DONE | 3, result=STALE),
                   event(6, 1, 0x200, result=STALE)]
        fresh = transfers(doc(['small']), 31)
        # Slot zero has been reused by the new generation before this old
        # slot-zero completion arrives. It must not complete the new bytes.
        fresh.insert(1, event(8, 5, DONE | min(512, len(partial)), result=STALE))
        events += fresh + [event(10, expect={16: 2, 25: 1, 36: 1, 37: 1, 38: 1})]
        add(f'accepted-output-reset-fresh-document/order={order}/fill={fill}', events,
            pixels=images['small'][1], fill=fill, prefix=dict(marker=marker, source=images['medium'][1]))
    for fill in (0, 204):
        events = transfers(doc(['medium', 'small']), 1024) + [event(10, expect={25: 1, 36: 1, 37: 2, 38: 2}),
                  setup(0xa1, 1, length=1), take(b'\x18', fallback=1), event(5), reset()]
        events += reset_steps() + [take(kind=2), event(5)]
        events += transfers(doc(['small']), 17) + [event(10, expect={16: 2, 25: 1, 37: 1, 38: 1})]
        add(f'completed-document-class-reset/fill={fill}', events,
            pixels=images['medium'][1] + images['small'][1] * 2, fill=fill)
    return cases


def automatic_recovery_candidates():
    cases = []

    def add(name, events, fill=204):
        cases.append(dict(name='automatic/' + name, events=events, pixels=b'',
                          fill=fill, config=0, invalid=0, prefix=None))

    def begin(slot, recovery, generation, request_count, **extra):
        expected = {2: 0, 3: recovery, 4: generation, 5: 1, 6: 0,
                    16: generation, 20: 1, 55: recovery, 56: 0,
                    57: request_count}
        expected.update(extra)
        return event(13, slot, expect=expected)

    # Existing wire-reset cases already exercise all six acknowledgement orders.
    # Here each individual external promise must independently remain necessary,
    # even when no input/output/EP0 owner exists in this first-use document.
    for omitted in (1, 2, 4):
        events = [begin(0, 1, 1, 0), event(1, result=WAIT),
                  event(4, 0, result=WAIT)]
        parts = 0
        for part in (1, 2, 4):
            if part == omitted:
                continue
            parts |= part
            events += [event(3, 0, part, expect={6: parts}),
                       event(3, 0, part, expect={6: parts}),
                       event(4, 0, result=WAIT, expect={16: 1, 20: 1})]
        events += [event(1, result=WAIT, expect={42: 0}),
                   event(3, 0, omitted, expect={6: 7}),
                   event(4, 0, expect={2: 0, 5: 0, 6: 0, 16: 2, 20: 0,
                                       55: 1, 56: 0, 57: 0}),
                   event(1, result=WAIT, expect={8: 0, 42: 0}),
                   # A real request still gets request ID 1 after recovery ID 1.
                   setup(0xa1, 1, length=1, expect={1: 1, 2: 1, 55: 1, 57: 1}),
                   take(b'\x18', fallback=1, request=1), event(5)]
        add(f'missing-promise-{omitted}', events, fill=0 if omitted == 1 else 204)

    # Two real requests precede recovery 1; the next wire reset must ACK request
    # 3, not recovery 2. Keep response storage borrowed through automatic restart.
    events = [setup(0xa1, 1, length=1), take(b'\x18', fallback=1, request=1), event(5),
              setup(0xa1, 0, length=2), take(DEVICE_ID[:2], slot=1, request=2),
              begin(0, 1, 1, 2), event(1, result=WAIT, expect={8: 1, 9: 2})]
    events += reset_steps(0, generation=1)
    events += [event(1, result=WAIT, expect={8: 1, 9: 2, 55: 1, 56: 0, 57: 2}),
               event(5, 1), event(1, result=WAIT),
               setup(0x21, 2, expect={1: 3, 2: 3, 3: 2, 55: 2, 56: 3, 57: 3})]
    events += reset_steps(1, generation=2)
    events += [take(kind=2, slot=2, request=3), event(5, 2),
               begin(2, 3, 3, 3),
               setup(0x21, 2, expect={1: 4, 2: 4, 3: 4, 55: 4, 56: 4, 57: 4}),
               event(3, 2, 1, result=STALE), event(4, 2, result=STALE)]
    events += reset_steps(3, generation=3)
    events += [take(kind=2, slot=3, request=4), event(5, 3)]
    add('separate-identities-and-retained-ep0', events)

    # The next transport boundary replaces a real reset even though generation
    # is unchanged. Later recovery cannot create that superseded wire ACK.
    events = [reset(), event(2, 0), event(3, 0, 1), event(3, 0, 2),
              begin(1, 2, 1, 1), event(3, 0, 4, result=STALE),
              event(4, 0, result=STALE), event(1, result=WAIT)]
    events += reset_steps(1, generation=1)
    events += [event(1, result=WAIT, expect={8: 0, 42: 0, 55: 2, 56: 0, 57: 1}),
               setup(0x23, 2, expect={1: 2, 3: 3, 55: 3, 56: 2, 57: 2})]
    events += reset_steps(2, generation=2)
    events += [take(kind=2, request=2), event(5)]
    add('transport-supersedes-real-reset', events)

    # Collect all three promises, then invalidate them before restart. The old
    # quiescence booleans cannot stand in for fresh promises on recovery 2.
    events = [begin(0, 1, 1, 0), event(3, 0, 1), event(3, 0, 2),
              event(3, 0, 4, expect={6: 7}), event(6, 1, 0x200, expect={5: 0, 6: 0}),
              event(2, 1, result=WAIT), event(4, 0, result=STALE),
              event(3, 0, 1, result=STALE), event(1, result=WAIT),
              begin(1, 2, 1, 0), event(4, 1, result=WAIT),
              event(3, 0, 4, result=STALE)]
    events += reset_steps(1, generation=1)
    events += [event(1, result=WAIT, expect={8: 0, 42: 0, 55: 2, 57: 0})]
    add('fault-invalidates-all-promises', events)

    # Seeding is a fixture-only first-use operation. No production initializer
    # or recovery API can rewind either counter. MAX is usable once; wrap is not.
    events = [event(15, 0xfffffffe, expect={55: 0xfffffffe, 57: 0}),
              setup(0xa1, 1, length=1, known=2, status=0x28),
              take(b'\x28', request=1), begin(0, 0xffffffff, 1, 1),
              event(13, 1, result=LIMIT,
                    expect={2: 0, 5: 0, 7: 1, 8: 1, 9: 1, 15: 0x28,
                            20: 1, 55: 0xffffffff, 56: 0, 57: 1}),
              event(3, 0, 1, result=LIMIT), event(4, 0, result=LIMIT),
              event(1, result=LIMIT), event(2, 2, result=LIMIT), event(5),
              event(13, 2, result=LIMIT), setup(0x21, 2, result=LIMIT)]
    add('recovery-exhaustion-retains-ep0', events)

    # Existing request-exhaustion tests cover the original APIs; this addition
    # specifically prevents the new internal API from escaping terminal state.
    events = [event(11, 0xfffffffe, 1),
              setup(0xa1, 1, length=1, known=2, status=0x28),
              take(b'\x28', request=0xffffffff),
              setup(0xa1, 0, length=2, result=LIMIT),
              event(13, 0, result=LIMIT,
                    expect={2: 0, 7: 1, 8: 1, 9: 0xffffffff,
                            55: 0, 56: 0, 57: 0xffffffff}),
              event(5), event(13, 1, result=LIMIT), event(1, result=LIMIT)]
    add('request-exhaustion-cannot-recover-internally', events)

    # A real request still cannot allocate a wrapped recovery identity.
    events = [event(15, 0xffffffff),
              setup(0x21, 2, result=LIMIT,
                    expect={1: 1, 2: 0, 5: 0, 7: 1, 20: 1,
                            55: 0xffffffff, 56: 0, 57: 1}),
              event(1, result=LIMIT), event(13, 0, result=LIMIT)]
    add('real-reset-cannot-wrap-recovery-counter', events)
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', action='store_true')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix='hp1020-usb-printer-', dir='/tmp'))
    print('Printer-class validation captures: ' + str(temp), flush=True)
    sources = set(SRC.glob('*.[ch]')) | set(SRC.glob('*.ld'))
    sources.update(RX/name for name in ('hp1020_usb_receive.c', 'hp1020_usb_receive.h',
                                       'hp1020_usb_document.c', 'hp1020_usb_document.h'))
    for name in ('hp1020_image', 'hp1020_image_page', 'hp1020_image_stream', 'hp1020_image_ring', 'hp1020_image_output'):
        sources.update(IMG/(name + suffix) for suffix in ('.c', '.h'))
    sources.update((IMG/'target-memory.c', IMG/'reference.c'))
    sources.update((IMG/'freestanding').glob('*.h'))
    sources.update(SEM.rglob('*.c'))
    sources.update(SEM.rglob('*.h'))
    sources.update((core.VENDOR/'libjbig').glob('*.h'))
    sources.update(core.VENDOR/'libjbig'/n for n in ('jbig85.c', 'jbig_ar.c'))
    sources.update(ROOT/'vendor/foo2zjs-source'/n for n in ('jbig.c', 'jbig_ar.c', 'jbig.h', 'jbig_ar.h'))
    sources.update(ROOT/'scripts'/n for n in ('validate-hp1020-usb-printer.py', 'build-hp1020-usb-printer-target.sh',
        'validate-hp1020-image-pages.py', 'validate-hp1020-image-core.py', 'check-hp1020-c-compiler-profile.py',
        'hp1020_qemu_ram.py', 'hp1020_xtensa_call0.py', 'hp1020_xtensa_properties.py'))
    tested = {str(p.relative_to(ROOT)): core.sha(p.read_bytes()) for p in sorted(sources)}
    for name in tested:
        saved = temp/'source'/name
        saved.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT/name, saved)
    (temp/'source-sha256.json').write_text(json.dumps(tested, indent=2) + '\n')
    flags = ['clang', '-std=c11', '-O1', '-g', '-fno-common', '-Wall', '-Wextra', '-Werror',
             '-fsanitize=address,undefined']
    implementation = [SRC/n for n in ('hp1020_usb_printer.c', 'fixture.c', 'host-check.c')]
    implementation += [RX/'hp1020_usb_receive.c', RX/'hp1020_usb_document.c']
    implementation += [IMG/n for n in ('hp1020_image.c', 'hp1020_image_page.c', 'hp1020_image_stream.c',
                                      'hp1020_image_ring.c', 'hp1020_image_output.c')]
    implementation += [SEM/'hp1020_semantic.c', SEM/'hp1020_page_plan.c',
                       core.VENDOR/'libjbig/jbig85.c', core.VENDOR/'libjbig/jbig_ar.c']
    core.command(flags + ['-I' + str(p) for p in (SRC, RX, IMG, SEM, core.VENDOR/'libjbig')]
                 + implementation + ['-o', temp/'host'])
    full = ROOT/'vendor/foo2zjs-source'
    core.command(flags + ['-I' + str(full), IMG/'reference.c', full/'jbig.c', full/'jbig_ar.c', '-o', temp/'reference'])
    images, fixtures = {}, []
    for name, w, h, pattern, filename in (('small', 32, 8, 'black', '32x8-stripe4-black.jbg'),
                                          ('medium', 9600, 132, 'edges', '9600x132-stripe128-edges.jbg')):
        path = pages.OUT/'fixtures'/filename
        raw = core.pattern(w, h, pattern)
        info = json.loads(core.command([temp/'reference', 'decode', path, temp/'oracle']))
        assert (temp/'oracle').read_bytes() == raw and info['consumed'] == path.stat().st_size
        images[name] = (path.read_bytes(), raw)
        fixtures.append(path)
    base_path = ROOT/'analysis/samples/generated/matrix-a4_default.zjs'
    base = pages.chunks(base_path.read_bytes())

    def body(name):
        bie = images[name][0]
        width, height = struct.unpack_from('>II', bie, 4)
        items = bytearray(base[1][1])
        for offset in range(0, len(items), 12):
            ident = struct.unpack_from('>H', items, offset + 4)[0]
            value = {4: 1, 12: width, 13: height, 17: width // 2, 18: height}.get(ident)
            if value is not None:
                struct.pack_into('>I', items, offset + 8, value)
        payload = bie[20:] + bytes(16 + ((-len(bie[20:])) & 3))
        return [(2, bytes(items), base[1][2], base[1][3]), (4, bie[:20], 0, 0),
                (5, payload, 0, 0), (6, b'', 0, 0), (3, b'', 0, 0)]

    def doc(names):
        return b'JZJZ' + pages.pack([base[0]] + sum((body(n) for n in names), []) + [base[-1]])

    records, target_inputs = [], []
    for index, candidate in enumerate(candidates(doc, body, images, base) + automatic_recovery_candidates()):
        events = candidate['events']
        directory = temp/f'case-{index:03}'
        directory.mkdir()
        wire = b''.join(struct.pack('>6I', *e['words'], len(e['data'])) + e['data'] for e in events)
        (directory/'events').write_bytes(wire)
        (directory/'case-name').write_text(candidate['name'] + '\n')
        output = core.command([temp/'host', directory/'events', candidate['fill'], candidate['config'],
            candidate['invalid'], directory/'capture', directory/'receive', directory/'output', directory/'replies'])
        (directory/'host-steps.json').write_text(output)
        observed = json.loads(output)
        assert len(observed) == len(events)
        expected_replies = bytearray()
        for step, (e, row) in enumerate(zip(events, observed)):
            assert row[0] == e['result'], (candidate['name'], step, e, row)
            assert row[34:36] == [0, 1], (candidate['name'], step, 'guard or ownership failure', row)
            assert all(row[int(at)] == value for at, value in e['expect'].items()), (candidate['name'], step, e, row)
            if e['words'][0] == 1 and e['result'] == OK:
                expected_replies.extend(e['reply'])
                expected_request = e['request'] if e['request'] is not None else row[2]
                assert row[10:15] == [e['kind'], len(e['reply']), expected_request, e['fallback'],
                                      core.fnv(e['reply'])], (candidate['name'], step, 'reply', row)
                assert row[8:10] == [1, expected_request]
        captures = [(directory/n).read_bytes() for n in ('capture', 'receive', 'output', 'replies')]
        capture, receive, image_output, replies = captures
        expected = candidate['pixels']
        prefix_bytes = 0
        if candidate['prefix']:
            marker = observed[candidate['prefix']['marker']]
            prefix_bytes = marker[26]
            assert marker[28] > marker[29] and marker[30] > 0 and prefix_bytes > 0, (candidate['name'], 'no output in flight')
            assert prefix_bytes <= len(candidate['prefix']['source'])
            expected = candidate['prefix']['source'][:prefix_bytes] + expected
        assert capture == expected, (candidate['name'], 'independent pixels', len(capture), len(expected))
        assert replies == expected_replies, (candidate['name'], 'wire reply bytes')
        final = observed[-1]
        assert final[26:28] == [len(capture), core.fnv(capture)]
        assert final[32:34] == [core.fnv(receive), core.fnv(image_output)]
        assert final[42:44] == [len(replies), core.fnv(replies)]
        records.append(dict(case=candidate['name'], status='pass', event_count=len(events), steps=observed,
            events_sha256=core.sha(wire), output_bytes=len(capture), output_sha256=core.sha(capture),
            control_reply_bytes=len(replies), control_reply_sha256=core.sha(replies),
            receive_storage_sha256=core.sha(receive), output_storage_sha256=core.sha(image_output),
            interrupted_source_prefix_bytes=prefix_bytes, fill=candidate['fill'], config_fields=candidate['config'],
            invalid_initialization=candidate['invalid']))
        target_inputs.append((candidate, events, observed, captures, directory))
    print(f'Printer class: {len(records)} sanitized host cases passed', flush=True)
    target = None
    if args.target:
        core.command(['bash', ROOT/'scripts/build-hp1020-usb-printer-target.sh'])
        elf = OUT/'target/target-check.elf'
        program, audit = core.audit_target(elf)
        shutil.copyfile(elf, temp/'target-check.elf')
        from hp1020_qemu_ram import QemuRAM
        native = []
        with QemuRAM() as q:
            q.load(elf)
            version = q.version
            for candidate, events, observed, captures, directory in target_inputs:
                r = q.call0(program.symbols['hp1020_pc_fixture_reset'],
                            [candidate['fill'], candidate['config'], candidate['invalid']])
                assert r == (INVALID if candidate['invalid'] else OK)
                target_steps = []
                for step, (e, host_row) in enumerate(zip(events, observed)):
                    if e['data']:
                        q.put(program.symbols['hp1020_pc_fixture_input'], e['data'])
                    r = q.call0(program.symbols['hp1020_pc_fixture_step'], e['words'])
                    row = list(struct.unpack('>64I', q.read(program.symbols['hp1020_pc_fixture_stats'], 256)))
                    assert r == row[0] and row[:40] + row[42:] == host_row[:40] + host_row[42:], (candidate['name'], step, row, host_row)
                    target_steps.append(row)
                (directory/'qemu-steps.json').write_text(json.dumps(target_steps) + '\n')
                for symbol, capture in (('hp1020_pc_fixture_capture', captures[0]), ('hp1020_pc_fixture_replies', captures[3])):
                    assert q.read(program.symbols[symbol], len(capture)) == capture, candidate['name']
                for function, capture in (('hp1020_pc_fixture_storage', captures[1]), ('hp1020_pc_fixture_output', captures[2])):
                    address = q.call0(program.symbols[function], [])
                    assert q.read(address, len(capture)) == capture, candidate['name']
                native.append(dict(case=candidate['name'], status='pass', all_steps_equal=True,
                    all_pixels_storage_and_control_replies_equal=True, state_and_memory_bytes=sum(target_steps[-1][40:42])))
                if len(native) % 10 == 0:
                    print(f'Printer class: {len(native)}/{len(records)} QEMU cases passed', flush=True)
        sizes = {c['state_and_memory_bytes'] for c in native}
        assert len(sizes) == 1
        target = dict(status='pass', cases=native, qemu_version=version, elf_sha256=core.sha(elf.read_bytes()),
                      state_and_memory_bytes=sizes.pop(), audit=audit)
    assert all(core.sha((ROOT/n).read_bytes()) == digest for n, digest in tested.items()), 'source changed during execution'
    report = dict(status='pass', cases=records, target=target, source_sha256=tested,
        fixture_sha256={str(p.relative_to(ROOT)): core.sha(p.read_bytes()) for p in fixtures},
        sample_sha256={str(base_path.relative_to(ROOT)): core.sha(base_path.read_bytes())},
        completed_native_page_lifecycles=0, usb_transfers=0, completed_usb_control_transfers=0,
        scope='Compiled printer-class request/ownership layer composed with the bounded receive, ZjStream, JBIG and output pipeline. Synthetic wire bytes, old-event identities and explicit quiescence promises; exact independently decoded pixels and control reply bytes.',
        limits='No USB controller, enumeration, EP0 framing, endpoint submission, DMA/cache, physical reset/abort, boot or printing is implemented or proven. Status is supplied or explicitly unknown fallback, never a measured printer state. Three reset acknowledgements and EP0 quiescence are external promises. The adapter must serialize events, preserve original identities, honor response lifetime, and establish actual quiescence. Copies remain metadata.')
    name = 'validation' if args.target else 'host-validation'
    text = json.dumps(report, indent=2, sort_keys=True) + '\n'
    (temp/(name + '.json')).write_text(text)
    (OUT/(name + '.json')).write_text(text)
    (OUT/(name + '.md')).write_text('# Bounded USB printer-class/document software\n\n' + report['scope'] + '\n\n'
        + f'{len(records)} sanitized host cases; {len(target["cases"]) if target else 0} independent QEMU cases.\n\n'
        + (f'Target state and fixed memory: {target["state_and_memory_bytes"]} bytes, excluding code, stack and fixture captures.\n\n' if target else '')
        + report['limits'] + '\n')
    print(f'Printer class: {len(records)} host cases; target={len(target["cases"]) if target else "not run"}', flush=True)


if __name__ == '__main__':
    main()
