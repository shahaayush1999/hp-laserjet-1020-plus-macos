#!/usr/bin/env python3
"""Three separate original USB IRQ decision cuts in guarded RAM.

This is not an uninterrupted IRQ, USB lifecycle, physical event ordering test,
or controller model. Only the sampling prefix runs the original ENTRY. Later
cuts receive explicit registers/stack, and every original helper/call remains
excluded. Redirected status stores are plain RAM writes, never W1C emulation.
"""
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
from types import SimpleNamespace

DEFAULT_ROOT = Path(__file__).resolve().parents[1] if Path(__file__).parent.name == 'scripts' else Path.cwd()
ROOT = Path(os.environ.get('HP1020_ROOT', str(DEFAULT_ROOT))).resolve()
OUT = ROOT / 'analysis/usb-path/irq-capture'
sys.path.insert(0, str(ROOT / 'scripts'))
from hp1020_xtensa_call0 import Program, Machine, STOP
from hp1020_xtensa_properties import properties, section_bytes
from hp1020_stock_stop import StopRAM
from hp1020_qemu_multitask import NativeTasks
from hp1020_qemu_stock_parser import guard_memory
from hp1020_qemu_ram import QemuRAM, STACK_TOP

MASK = 0xffffffff
STOCK_SHA = '2111560068db47ceca21fa550db4c7c34f5595b5a5d137ae4a19631e40e3601d'
LINUX_COMMIT = 'adc218676eef25575469234709c2d87185ca223a'
REF = ROOT / 'analysis/usb-path/controller-reference/linux-v6.12'
REFERENCE_SHA = {
    'amd5536udc.h': '8dbf2ebffe7de042bdfea1c5e4e0d7e7ca334cb821fbfaa1cf9ccfeeae302648',
    'snps_udc_core.c': 'c1b09e8f69d3340f2afd3a033d77a42775b52716d45b1aceb211dcaab89127bf',
    'provenance.json': '023d10e246e4852c1b9415cdc3d591006edcedeba467a56b95b22b994d4a08e4',
}
PHASES = {
    'samples': dict(entry=0x10008208, code=[(0x10008208, 0x10008240)],
                    stops=(0x1000833c, 0x10008240), original_entry=True),
    'lanes': dict(entry=0x1000837e,
        code=[(0x1000837e, 0x100083cf), (0x100083e0, 0x1000841a),
              (0x10008439, 0x1000845c), (0x100084a9, 0x100084b4),
              (0x100084b7, 0x100084c5), (0x100086c3, 0x100086ed)],
        stops=(0x100084b4, 0x100084c5, 0x100086ed), original_entry=False),
    'out0_common_wake': dict(entry=0x100084c8,
        code=[(0x100084c8, 0x100084ce), (0x100086b0, 0x100086c0)],
        stops=(0x100086c0,), original_entry=False),
}
ALL_CODE = sorted({bounds for phase in PHASES.values() for bounds in phase['code']})
ARENA, ARENA_SIZE = 0x22b00000, 0x2000
DEVINT, EPINT, WRAPPER, EPMASK = [ARENA + x for x in (0x100, 0x120, 0x140, 0x160)]
IN_STATUS, OUT_STATUS = ARENA + 0x400, ARENA + 0x800
SETUP, BULK = ARENA + 0xd00, ARENA + 0xe00
SETUP_GLOBAL, BULK_GLOBAL, TRANSFER_CELL = 0x1001bbc0, 0x1001bc48, 0x100212d4
EVENT_OBJECT = 0x10021318
INITIAL_SP = STACK_TOP - 0x100
DEFAULT_EPMASK = 0xfffcfffe  # Supplied: IN0, OUT0, OUT1 enabled.
EMPTY_FIXTURE = SimpleNamespace(path=None, execute_ranges=[])
REDIRECTS = {
    0x10005de4: (0xb300040c, DEVINT, 'samples'),
    0x10005de8: (0xb3000414, EPINT, 'both'),
    0x10005dec: (0xb3010004, WRAPPER, 'samples'),
    0x10005e00: (0xb3000418, EPMASK, 'lanes'),
    0x10005e04: (0xb3000004, IN_STATUS, 'lanes'),
    0x10005e08: (0xb3000204, OUT_STATUS, 'lanes'),
}
LITERALS = {**{at: value[0] for at, value in REDIRECTS.items()},
            0x10005e18: EVENT_OBJECT, 0x10005e1c: TRANSFER_CELL}
ANCHORS = {
    0x10008208: ('entry', (1, 48), '6c1006'),
    0x10008214: ('l32i.n', (5, 10, 0), '85a0'),
    0x10008219: ('l32i.n', (8, 8, 0), '8880'),
    0x1000821d: ('s32i.n', (8, 1, 0), '9810'),
    0x1000822b: ('s32i.n', (9, 10, 0), '99a0'),
    0x10008230: ('l32i.n', (9, 8, 0), '8980'),
    0x10008240: ('call8', (0x10011178,), '5823cd'),
    0x1000838d: ('l32i.n', (10, 8, 0), '8a80'),
    0x1000839b: ('s32i.n', (14, 9, 0), '9e90'),
    0x100083bb: ('beqz', (14, 0x100086db), '64e31c'),
    0x100083c1: ('bbsi', (14, 31, 0x100083c7), '7fef02'),
    0x100083eb: ('l32i.n', (6, 7, 0), '8670'),
    0x100083f6: ('s32i.n', (8, 7, 0), '9870'),
    0x10008401: ('s32i', (8, 7, 0), '287600'),
    0x1000840c: ('s32i.n', (8, 7, 0), '9870'),
    0x10008443: ('s32i', (8, 7, 0), '287600'),
    0x1000844f: ('s32i.n', (8, 7, 0), '9870'),
    0x100084b4: ('call8', (0x10017dac,), '583e3d'),
    0x100084c5: ('call8', (0x10007c5c,), '5bfde5'),
    0x100084c8: ('beqi', (5, 1, 0x100084ce), '685102'),
    0x100084cb: ('j', (0x100086b0,), '6001e1'),
    0x100086b0: ('l32r', (10, 0x10005e18), '1af5da'),
    0x100086c0: ('call8', (0x10017dac,), '583dba'),
    0x100086db: ('addi', (4, 4, 16), '244c10'),
    0x100086de: ('addi', (3, 3, 1), '233c01'),
    0x100086ed: ('call8', (0x100171e0,), '583abc'),
    # Static-only helper anchor; no helper instruction executes in any phase.
    0x10007c69: ('call8', (0x10017dac,), '584050'),
}
# Every actual peripheral load/store instruction in the selected phase ranges.
# A separate standalone control injects a real peripheral address at each site.
ACCESS_SITES = (
    ('samples', 'devint-read', 0x10008214, 10, 0xb300040c),
    ('samples', 'epint-read', 0x10008219, 8, 0xb3000414),
    ('samples', 'reset-ack-write', 0x1000822b, 10, 0xb300040c),
    ('samples', 'wrapper-read', 0x10008230, 8, 0xb3010004),
    ('lanes', 'endpoint-mask-read', 0x1000838d, 8, 0xb3000418),
    ('lanes', 'saved-epint-ack-write', 0x1000839b, 9, 0xb3000414),
    ('lanes', 'lane-status-read', 0x100083eb, 7, 0xb3000204),
    ('lanes', 'he-ack-write', 0x100083f6, 7, 0xb3000204),
    ('lanes', 'bna-ack-write', 0x10008401, 7, 0xb3000204),
    ('lanes', 'in-ack-write', 0x1000840c, 7, 0xb3000204),
    ('lanes', 'out-type-ack-write', 0x10008443, 7, 0xb3000204),
    ('lanes', 'tdc-ack-write', 0x1000844f, 7, 0xb3000204),
)
REMOVED_REDIRECTS = (
    ('samples', 0x10005de4, 0x10008214, 0x30001),
    ('samples', 0x10005de8, 0x10008219, 0x30001),
    ('samples', 0x10005dec, 0x10008230, 0x30001),
    ('lanes', 0x10005e00, 0x1000838d, 1),
    ('lanes', 0x10005de8, 0x1000839b, 1),
    ('lanes', 0x10005e04, 0x100083eb, 1),
    ('lanes', 0x10005e08, 0x100083eb, 0x10000),
)
EXCLUDED_COMMON = (0x10008240, 0x10008264, 0x1000829f, 0x100082c6,
    0x100082f0, 0x100083d4, 0x1000841a, 0x10008428, 0x10008470, 0x100084b4,
    0x100084c5, 0x100084ce, 0x100086ad, 0x100086c0, 0x100086ed,
    0x10007c5c, 0x10017dac, 0x10011178, 0x1001bb5c, 0x100171e0,
    0x100086f4, 0x1000935b, 0x10009884)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def patterned(seed, address, size):
    return bytes((seed + (address >> 8) + i * 17 + (i >> 4) * 3) & 255 for i in range(size))


def access(pc, kind, address, size, value):
    return dict(pc=hex(pc), kind=kind, address=hex(address), size=size, value=hex(value))


def base_case(phase, name, fill):
    return dict(phase=phase, name=name, kind='conditional_phase', fill=fill,
        devint=8, epint=0x30001, live_epint=0xa5c31234 ^ (fill * 0x01010101),
        wrapper=0x96a50020, endpoint_mask=DEFAULT_EPMASK,
        in0_status=0x400, out0_status=0x20, out1_status=0x10,
        transfer_handle=0x5a000008 ^ (fill << 16))


def case_specs():
    for fill in (0, 204):
        for reset in (0, 8):
            for pending in (0, 0x30001):
                case = base_case('samples', f'samples-f{fill}-reset{reset}-ep{pending:x}', fill)
                case.update(devint=reset, epint=pending)
                yield case
        lane_profiles = (
            ('no-pending', dict(epint=0)),
            ('in0-tdc', dict(epint=1)),
            ('in0-no-tdc', dict(epint=1, in0_status=0)),
            ('out0-setup', dict(epint=0x10000)),
            ('out0-data', dict(epint=0x10000, out0_status=0x10)),
            ('out0-setup-tdc', dict(epint=0x10000, out0_status=0x420)),
            ('out1-data', dict(epint=0x20000)),
            ('in0-out0-co-pending', dict(epint=0x10001)),
            ('in0-no-tdc-then-out0', dict(epint=0x10001, in0_status=0x40)),
            ('out0-out1-co-pending', dict(epint=0x30000)),
            ('out0-all-flags', dict(epint=0x10000, out0_status=0x6f0)),
            ('out0-errors-without-tdc', dict(epint=0x10000, out0_status=0x2f0)),
            ('out0-zero-status', dict(epint=0x10000, out0_status=0)),
            ('conditional-out0-masked-out1-enabled', dict(epint=0x10000, endpoint_mask=0xfffdffff)),
            ('conditional-out0-masked-with-tdc', dict(epint=0x10000, endpoint_mask=0xfffdffff, out0_status=0x420)),
            ('conditional-out1-above-last-enabled', dict(epint=0x20000, endpoint_mask=0xfffeffff)),
            ('conditional-all-out-masked', dict(epint=0x10000, endpoint_mask=0xfffffffe)),
        )
        for label, fields in lane_profiles:
            case = base_case('lanes', f'lanes-f{fill}-{label}', fill)
            case.update(fields, profile=label)
            yield case
        yield base_case('out0_common_wake', f'out0-common-wake-f{fill}', fill)
        for phase, literal, pc, pending in REMOVED_REDIRECTS:
            case = base_case(phase, f'unredirected-{literal:x}-{phase}-f{fill}', fill)
            case.update(kind='removed_literal_redirect', skip_literal=literal, reject_pc=pc, epint=pending)
            yield case
        for phase, label, pc, register, address in ACCESS_SITES:
            case = base_case(phase, f'guard-{label}-f{fill}', fill)
            case.update(kind='standalone_peripheral_instruction', entry=pc,
                        reject_pc=pc, registers={register: address})
            yield case


def selected_redirects(case):
    if case['kind'] == 'standalone_peripheral_instruction':
        return {}
    return {at: (original, image) for at, (original, image, phase) in REDIRECTS.items()
            if phase == case['phase'] or phase == 'both' and case['phase'] in ('samples', 'lanes')}


def seeded_registers(case):
    r = [(0x13579bdf + i * 0x10203 + case['fill'] * 0x01010101) & MASK for i in range(16)]
    r[0], r[1] = STOP, INITIAL_SP
    if case['phase'] == 'out0_common_wake':
        r[2], r[3], r[4], r[5] = 1, 1, 16, 0
    for index, value in case.get('registers', {}).items():
        r[index] = value
    return r


# These literal selections are deliberately separate from the scan oracle.
# They are not derived from status/mask calculations or from either engine.
# Values: stop PC, ordered endpoint-status read addresses, proposed a11 if an
# event call is selected (None for the OUT helper or terminal IRQ-clear call).
LANE_SELECTIONS = {
    'no-pending': (0x100086ed, [], None),
    'in0-tdc': (0x100084b4, [IN_STATUS], 1),
    'in0-no-tdc': (0x100086ed, [IN_STATUS], None),
    'out0-setup': (0x100084c5, [OUT_STATUS], None),
    'out0-data': (0x100084c5, [OUT_STATUS], None),
    'out0-setup-tdc': (0x100084b4, [OUT_STATUS], 0x10000),
    'out1-data': (0x100084c5, [OUT_STATUS + 32], None),
    'in0-out0-co-pending': (0x100084b4, [IN_STATUS], 1),
    'in0-no-tdc-then-out0': (0x100084c5, [IN_STATUS, OUT_STATUS], None),
    'out0-out1-co-pending': (0x100084c5, [OUT_STATUS], None),
    'out0-all-flags': (0x100084b4, [OUT_STATUS], 0x10000),
    'out0-errors-without-tdc': (0x100084c5, [OUT_STATUS], None),
    'out0-zero-status': (0x100084c5, [OUT_STATUS], None),
    'conditional-out0-masked-out1-enabled': (0x100084c5, [OUT_STATUS], None),
    'conditional-out0-masked-with-tdc': (0x100084b4, [OUT_STATUS], 0x10000),
    'conditional-out1-above-last-enabled': (0x100086ed, [], None),
    'conditional-all-out-masked': (0x100086ed, [], None),
}


class IRQRAM(StopRAM):
    def __init__(self, program, case):
        self.recording, self.events = False, []
        definition = PHASES[case['phase']]
        super().__init__(program, case.get('entry', definition['entry']),
                         definition['code'].copy(), [(ARENA, ARENA_SIZE)])
        self.case = case
        for begin, end in self.write_ranges:
            self.put(begin, patterned(case['fill'], begin, end - begin))
        self.redirects = selected_redirects(case)
        for literal, (original, image) in self.redirects.items():
            assert self.read(literal, 4) == original
            if literal != case.get('skip_literal'):
                self.write_ranges.append((literal, literal + 4))
                self.write(literal, 4, image)
        for address, value in (
            (DEVINT, case['devint']),
            (EPINT, case['epint'] if case['phase'] == 'samples' else case['live_epint']),
            (WRAPPER, case['wrapper']), (EPMASK, case['endpoint_mask']),
            (IN_STATUS, case['in0_status']), (OUT_STATUS, case['out0_status']),
            (OUT_STATUS + 32, case['out1_status']),
            (TRANSFER_CELL, case['transfer_handle']), (SETUP_GLOBAL, SETUP), (BULK_GLOBAL, BULK)):
            self.write(address, 4, value)
        # Neither this raw SETUP record nor either record-pointer global is an
        # execution input to any selected cut. They are acquisition canaries.
        self.put(SETUP, bytes.fromhex('8e123456d3c2b1a0a100341256789abc'))
        self.put(BULK, bytes.fromhex('800000400123456789abcdef76543210'))
        if case['phase'] == 'lanes':
            self.write(INITIAL_SP, 4, case['epint'])
        self.registers = seeded_registers(case)
        self.supplied_registers = self.registers.copy()

    def read(self, address, size):
        value = super().read(address, size)
        if self.recording:
            self.events.append(access(self.pc, 'read', address, size, value))
        return value

    def write(self, address, size, value):
        self.span(address, size)  # Reject peripherals before mutable-range checks.
        super().write(address, size, value)
        if self.recording:
            self.events.append(access(self.pc, 'write', address, size, value & ((1 << (8 * size)) - 1)))


def snapshot(state):
    return {(a, b): state.bytes_at(a, b - a) for a, b in state.write_ranges}


def manifest(memory):
    return [dict(begin=hex(a), end=hex(b), bytes=len(data), sha256=sha(data))
            for (a, b), data in sorted(memory.items())]


def oracle(before, case):
    """Independent supplied-state contract, never decoded from executed opcodes.

    Literal status writes and the lane scan are specified explicitly. Reads are
    ordered (including literals/stack); every register and mutable byte is
    checked. This predicts software effects on RAM, not W1C/DMA/IRQ semantics.
    """
    memory = {bounds: bytearray(data) for bounds, data in before.items()}
    events, r, sar = [], seeded_registers(case), 0
    stop, call_intent = None, None

    class PeripheralBoundary(Exception):
        def __init__(self, pc):
            self.pc = pc

    def locate(address, size):
        matches = [(a, b) for a, b in memory if a <= address and address + size <= b]
        assert len(matches) == 1, (hex(address), size)
        return matches[0]

    def rd(pc, address, size=4):
        if 0xb0000000 <= address < 0xc0000000:
            raise PeripheralBoundary(pc)
        matches = [(a, b) for a, b in memory if a <= address and address + size <= b]
        if not matches and address in LITERALS and size == 4:
            value = LITERALS[address]
        else:
            a, b = locate(address, size)
            value = int.from_bytes(memory[(a, b)][address - a:address - a + size], 'big')
        events.append(access(pc, 'read', address, size, value))
        return value

    def wr(pc, address, value, size=4):
        if 0xb0000000 <= address < 0xc0000000:
            raise PeripheralBoundary(pc)
        a, b = locate(address, size)
        value &= (1 << (size * 8)) - 1
        memory[(a, b)][address - a:address - a + size] = value.to_bytes(size, 'big')
        events.append(access(pc, 'write', address, size, value))

    try:
        if case['kind'] == 'standalone_peripheral_instruction':
            raise PeripheralBoundary(case['reject_pc'])
        if case['phase'] == 'samples':
            r[1] -= 48  # Original ENTRY, with a fresh supplied CPU window.
            r[10] = rd(0x1000820b, 0x10005de4)
            r[8] = rd(0x1000820e, 0x10005de8)
            r[5] = rd(0x10008214, r[10])
            r[8] = rd(0x10008219, r[8])
            r[9] = 8
            wr(0x1000821d, r[1], r[8])
            stop = 0x1000833c
            if r[5] & 8:
                r[8] = rd(0x10008225, 0x10005dec)
                wr(0x1000822b, r[10], 8)
                r[9] = rd(0x10008230, r[8])
                r[8] = 16
                r[7] = r[9] & 16
                assert r[7] == 0, 'wrapper/timer branch deliberately outside this experiment'
                r[10] = 21
                stop, call_intent = 0x10008240, dict(target=hex(0x10011178), a10=21)
        elif case['phase'] == 'out0_common_wake':
            assert r[2:6] == [1, 1, 16, 0]
            r[10] = rd(0x100086b0, 0x10005e18)
            r[11] = r[4] + r[5]
            sar = 32 - (r[11] & 31)
            r[11] = (r[2] << (32 - sar)) & MASK
            r[12] = 0
            stop = 0x100086c0
            call_intent = dict(target=hex(0x10017dac), a10=EVENT_OBJECT, a11=0x10000, a12=0)
        else:
            assert case['phase'] == 'lanes'
            r[3], r[2], r[4] = 0, 1, 0
            r[8] = rd(0x10008384, 0x10005e00)
            r[9] = rd(0x10008387, 0x10005de8)
            r[10] = rd(0x1000838d, r[8])
            r[14] = rd(0x1000838f, r[1])
            r[8], r[10] = MASK, r[10] ^ MASK
            wr(0x10008396, r[1] + 4, r[10])
            wr(0x1000839b, r[9], r[14])
            while stop is None:
                r[14] = rd(0x1000839d, r[1] + 4)
                r[5], sar = 0, r[4] & 31
                r[8] = (r[14] >> sar) & 0xffff
                r[14] = rd(0x100083aa, r[1])
                wr(0x100083ac, r[1] + 8, r[8])
                sar = r[4] & 31
                r[8] = (r[14] >> sar) & 0xffff
                wr(0x100083b7, r[1] + 12, r[8])
                while stop is None:
                    r[14] = rd(0x100083b9, r[1] + 8)
                    if r[14] == 0:
                        break
                    r[14] = rd(0x100083be, r[1] + 12)
                    if r[14] & 1:
                        assert (r[3], r[5]) in ((0, 0), (1, 0), (1, 1))
                        r[9] = rd(0x100083c9 if r[3] == 0 else 0x100083e0,
                                  0x10005e04 if r[3] == 0 else 0x10005e08)
                        r[8] = r[5] * 32
                        r[7] = (r[9] + r[8]) & MASK
                        r[6] = rd(0x100083eb, r[7])
                        for bit, pc in ((0x200, 0x100083f6), (0x80, 0x10008401)):
                            r[8] = bit
                            if r[6] & bit:
                                wr(pc, r[7], bit)
                        r[8] = 0x40
                        if r[6] & 0x40:
                            wr(0x1000840c, r[7], 0x40)
                            r[8] = r[4] + r[5]
                            sar = 32 - (r[8] & 31)
                            r[8] = (r[2] << (32 - sar)) & MASK
                            assert r[8] != 2  # IN1 list path is excluded.
                        r[8] = r[6] & 0x30
                        if r[8]:
                            wr(0x10008443, r[7], r[8])
                        r[8] = 0x400
                        if r[6] & 0x400:
                            wr(0x1000844f, r[7], 0x400)
                            r[8] = r[4] + r[5]
                            sar = 32 - (r[8] & 31)
                            r[7] = (r[2] << (32 - sar)) & MASK
                            assert r[7] != 2
                            r[10] = rd(0x100084a9, 0x10005e18)
                            r[11], r[12] = r[7], 0
                            stop = 0x100084b4
                            call_intent = dict(target=hex(0x10017dac), a10=EVENT_OBJECT, a11=r[7], a12=0)
                            break
                        if r[3] == 1:
                            r[8] = rd(0x100084bd, 0x10005e1c)
                            r[10] = rd(0x100084c0, r[8])
                            stop, call_intent = 0x100084c5, dict(target=hex(0x10007c5c), a10=case['transfer_handle'])
                            break
                    r[14] = rd(0x100086c3, r[1] + 8)
                    r[5] += 1
                    r[14] >>= 1
                    wr(0x100086ca, r[1] + 8, r[14])
                    r[14] = rd(0x100086cc, r[1] + 12)
                    r[8], r[14] = 15, r[14] >> 1
                    wr(0x100086d3, r[1] + 12, r[14])
                    if r[5] > 15:
                        break
                if stop is not None:
                    break
                r[4] += 16
                r[3] += 1
                if r[3] >= 2:
                    r[10] = 4
                    stop, call_intent = 0x100086ed, dict(target=hex(0x100171e0), a10=4)
    except PeripheralBoundary as error:
        assert error.pc == case.get('reject_pc'), (case, error.pc)
        stop = error.pc
    else:
        assert 'reject_pc' not in case, ('unreached peripheral rejection', case)
    return dict(memory={bounds: bytes(data) for bounds, data in memory.items()},
                accesses=events, registers=r, sar=sar, stop=stop, proposed_call=call_intent)


def qemu_memory_event(state, q):
    pc = q.reg(0)
    if not any(a <= pc < b for a, b in state.code_ranges):
        return None
    op, args, raw = state.program.instruction(pc)
    guard_memory(state, q, op, args)
    base = op.removesuffix('.n')
    ar = lambda n: q.reg(((q.reg(38) * 4 + n) % 32) + 1)
    if base == 'l32r':
        address, size, kind = args[1], 4, 'read'
    elif base in ('l32i', 's32i'):
        address, size = (ar(args[1]) + args[2]) & MASK, 4
        kind = 'read' if base == 'l32i' else 'write'
    else:
        return None
    value = int.from_bytes(q.read(address, size), 'big') if kind == 'read' else ar(args[0])
    return access(pc, kind, address, size, value)


def execute(program, case, q, capture, code_audit):
    state = IRQRAM(program, case)
    engine = 'interpreter' if q is None else 'qemu'
    directory = capture / case['name']
    directory.mkdir(exist_ok=True)
    stem = directory / engine
    before = snapshot(state)
    expected = oracle(before, case)
    original_entry = case['phase'] == 'samples' and case['kind'] != 'standalone_peripheral_instruction'
    initial_ps = 0x40000 if original_entry else 0  # PS.WOE for ENTRY; CALLINC stays zero.
    supplied = dict(case=case, entry=hex(state.pc), stop_before=hex(expected['stop']),
        original_entry_executed=original_entry,
        phases_connected=False, omitted_helpers_executed=False,
        logical_registers={f'a{i}': hex(v) for i, v in enumerate(state.supplied_registers)},
        initial_sar=0, windowbase=0, windowstart=1, processor_status=initial_ps,
        private_literal_redirects={hex(at): dict(original=hex(old), ram=hex(image))
            for at, (old, image) in state.redirects.items() if at != case.get('skip_literal')})
    stem.with_suffix('.input.json').write_text(json.dumps(supplied, indent=2, sort_keys=True) + '\n')
    for suffix, memory in (('before', before), ('expected', expected['memory'])):
        stem.with_suffix('.' + suffix + '.bin').write_bytes(b''.join(data for _, data in sorted(memory.items())))
    runner, failure = None, None
    try:
        if q is None:
            state.recording = True
            state.run(budget=512)
        else:
            q.load(program.path)
            runner = NativeTasks(q, state, EMPTY_FIXTURE, state.code_ranges, (), instruction_budget=512)
            runner.synchronize(True)
            q.reset_cpu(state.pc)
            q.set_reg(42, initial_ps)
            for index, value in enumerate(state.supplied_registers, 1):
                q.set_reg(index, value)
            while True:
                state.pc = q.reg(0)
                event = qemu_memory_event(state, q)
                runner.step()
                if event is not None:
                    state.events.append(event)
    except Exception as error:
        failure = dict(type=type(error).__name__, reason=str(error), pc=hex(state.pc))
    finally:
        state.recording = False
        if runner is not None:
            runner.synchronize(False)
            state.registers = [q.reg(((q.reg(38) * 4 + i) % 32) + 1) for i in range(16)]
            state.sar = q.reg(36)
    actual = snapshot(state)
    visited = state.visited if runner is None else runner.visited
    retired = visited - {case.get('reject_pc')}
    expected_cpu = dict(processor_status=initial_ps, windowbase=0, windowstart=1,
                        sar=expected['sar'], lbeg=0, lend=0, lcount=0)
    native_cpu = None if q is None else dict(processor_status=q.reg(42),
        windowbase=q.reg(38), windowstart=q.reg(39), sar=q.reg(36),
        lbeg=q.reg(33), lend=q.reg(34), lcount=q.reg(35))
    result = dict(status='captured_unchecked', engine=engine, phase=case['phase'],
        entry=hex(case.get('entry', PHASES[case['phase']]['entry'])), stop_before=hex(expected['stop']),
        original_entry_executed=supplied['original_entry_executed'], failure=failure,
        registers=[hex(v) for v in state.registers], expected_registers=[hex(v) for v in expected['registers']],
        sar=state.sar, expected_sar=expected['sar'], proposed_call=expected['proposed_call'],
        expected_native_cpu_state=expected_cpu, native_cpu_state=native_cpu,
        interpreter_models_physical_window_registers=False,
        before_memory=manifest(before), expected_memory=manifest(expected['memory']), actual_memory=manifest(actual),
        accesses=state.events, expected_accesses=expected['accesses'],
        setup_record_hex=state.bytes_at(SETUP, 16).hex(), bulk_record_hex=state.bytes_at(BULK, 16).hex(),
        original_instructions_retired=[hex(pc) for pc in sorted(retired)],
        engine_steps=state.steps if runner is None else runner.steps)
    stem.with_suffix('.after.bin').write_bytes(b''.join(data for _, data in sorted(actual.items())))
    stem.with_suffix('.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    reason = 'MMIO forbidden' if 'reject_pc' in case else (
        'execution outside selected stock routines: ' if q is None else 'native tasks left selected code: ') + hex(expected['stop'])
    assert failure == dict(type='ValueError', reason=reason, pc=hex(expected['stop'])), (case, engine, failure)
    if runner is not None:
        assert q.reg(0) == expected['stop'] and expected['stop'] not in runner.visited
        assert q.reg(38) == 0 and q.reg(39) == 1 and not runner.services
        assert native_cpu == expected_cpu, (case, 'PS/WB/WS/SAR/loop state')
    assert actual == expected['memory'], (case['name'], engine, 'all mutable RAM including stack and guards')
    assert state.events == expected['accesses'], (case['name'], engine, 'ordered read/write oracle')
    assert state.registers == expected['registers'] and state.sar == expected['sar'], (case, engine, 'full register oracle')
    if case['phase'] == 'lanes' and case['kind'] == 'conditional_phase':
        stop, reads, proposed_bit = LANE_SELECTIONS[case['profile']]
        assert expected['stop'] == stop
        assert [int(event['address'], 16) for event in state.events if event['pc'] == hex(0x100083eb)] == reads
        if proposed_bit is not None:
            assert state.registers[10:13] == [EVENT_OBJECT, proposed_bit, 0]
        if case['profile'] == 'out0-all-flags':
            assert [int(event['value'], 16) for event in state.events
                    if event['kind'] == 'write' and event['address'] == hex(OUT_STATUS)] == [0x200, 0x80, 0x40, 0x30, 0x400]
            assert state.bytes_at(OUT_STATUS, 4) == bytes.fromhex('00000400')
    assert not set(EXCLUDED_COMMON) & retired
    assert (0x10008208 in retired) == supplied['original_entry_executed']
    for event in state.events:
        address, size = int(event['address'], 16), event['size']
        for lo, hi in ((SETUP, SETUP + 16), (BULK, BULK + 16),
                       (SETUP_GLOBAL, SETUP_GLOBAL + 4), (BULK_GLOBAL, BULK_GLOBAL + 4),
                       (0x90021340, 0x90021350)):
            assert address + size <= lo or address >= hi, ('unexpected record acquisition/return', event)
    for item in code_audit:
        start, end = int(item['begin'], 16), int(item['end'], 16)
        raw = state.bytes_at(start, end - start)
        assert sha(raw) == item['sha256']
        if q is not None:
            assert q.read(start, end - start) == raw
    result.update(status='pass', independent_full_registers_equal=True,
        native_cpu_state_checked=q is not None,
        independent_ordered_accesses_equal=True, all_mutable_ram_equal=True,
        no_setup_record_or_pointer_access=True, no_record_ownership_return=True,
        original_code_unchanged=True, actual_peripheral_accesses=0,
        omitted_helpers_executed=False, completed_usb_transfers=0)
    stem.with_suffix('.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    return result


def source_paths():
    pending, found = [Path(__file__).resolve()], set()
    while pending:
        path = pending.pop()
        if path in found:
            continue
        found.add(path)
        for node in ast.walk(ast.parse(path.read_text())):
            names = [item.name for item in node.names] if isinstance(node, ast.Import) else (
                [node.module] if isinstance(node, ast.ImportFrom) and node.module else [])
            for name in names:
                candidate = ROOT / 'scripts' / (name.split('.')[0] + '.py')
                if candidate.is_file() and candidate not in found:
                    pending.append(candidate)
    return sorted(found | {ROOT / 'analysis/sihp1020.elf', *(REF / name for name in REFERENCE_SHA)})


def audit(program, blob):
    assert sha(blob) == STOCK_SHA
    sections, _ = properties(blob)
    allowed = {'entry', 'l32r', 'l32i', 's32i', 'movi', 'mov', 'or', 'and', 'xor',
               'add', 'addi', 'slli', 'srli', 'ssr', 'ssl', 'srl', 'sll', 'extui',
               'memw', 'j', 'bany', 'bnone', 'beqz', 'bnez', 'beqi', 'bnei',
               'bbsi', 'bltu', 'bgeui'}
    chunks = []
    for begin, end in ALL_CODE:
        raw = section_bytes(blob, sections, begin, end - begin)
        pc, instructions = begin, {}
        while pc < end:
            op, args, encoded = program.instruction(pc)
            assert op.removesuffix('.n') in allowed and pc + len(encoded) <= end, (hex(pc), op)
            assert encoded == section_bytes(blob, sections, pc, len(encoded))
            instructions[hex(pc)] = dict(op=op, args=args, bytes=encoded.hex())
            pc += len(encoded)
        assert pc == end
        chunks.append(dict(begin=hex(begin), end=hex(end), bytes=raw.hex(), sha256=sha(raw), instructions=instructions))
    for pc, (op, args, raw) in ANCHORS.items():
        assert program.instruction(pc) == (op, args, bytes.fromhex(raw)), hex(pc)
        assert section_bytes(blob, sections, pc, len(bytes.fromhex(raw))).hex() == raw
    original = Machine(program)
    for address, value in LITERALS.items():
        assert original.read(address, 4) == value
    for name, digest in REFERENCE_SHA.items():
        assert sha((REF / name).read_bytes()) == digest
    assert json.loads((REF / 'provenance.json').read_bytes())['commit'] == LINUX_COMMIT
    header = (REF / 'amd5536udc.h').read_text()
    for name, value in (('UDC_DEVINT_UR', '3'), ('UDC_DEVINT_ADDR', '0x40c'),
                        ('UDC_EPINT_ADDR', '0x414'), ('UDC_EPINT_MSK_ADDR', '0x418'),
                        ('UDC_EPSTS_TDC', '10'), ('UDC_EPSTS_OUT_SETUP_CLEAR', '0x20')):
        assert re.search(r'^#define\s+' + name + r'\s+' + value + r'\s*$', header, re.M)
    return dict(chunks=chunks, anchors={hex(k): v for k, v in ANCHORS.items()},
        literal_originals={hex(k): hex(v) for k, v in LITERALS.items()},
        linux_commit=LINUX_COMMIT, linux_source_sha256=REFERENCE_SHA)


def reject_excluded(program, q, capture):
    rows = []
    for phase, definition in PHASES.items():
        state = IRQRAM(program, base_case(phase, 'excluded-' + phase, 204))
        before = snapshot(state)
        q.load(program.path)
        runner = NativeTasks(q, state, EMPTY_FIXTURE, state.code_ranges, (), instruction_budget=1)
        runner.synchronize(True)
        q.reset_cpu(state.pc)
        excluded = set(EXCLUDED_COMMON) | {other['entry'] for name, other in PHASES.items() if name != phase}
        for pc in sorted(excluded):
            assert not any(a <= pc < b for a, b in state.code_ranges)
            state.pc, state.steps, state.visited = pc, 0, set()
            try:
                state.run(budget=1)
            except ValueError as error:
                assert str(error) == f'execution outside selected stock routines: {pc:#x}'
            else:
                raise AssertionError(f'excluded interpreter instruction executed: {pc:#x}')
            assert state.steps == 0 and not state.visited
            q.set_reg(0, pc)
            try:
                runner.step()
            except ValueError as error:
                assert str(error) == f'native tasks left selected code: {pc:#x}'
            else:
                raise AssertionError(f'excluded QEMU instruction executed: {pc:#x}')
            assert runner.steps == 0 and not runner.visited and q.reg(0) == pc
            rows.append(dict(phase=phase, pc=hex(pc), status='rejected before instruction execution in both engines'))
        runner.synchronize(False)
        assert snapshot(state) == before
    (capture / 'excluded-code.json').write_text(json.dumps(rows, indent=2) + '\n')
    return rows


def main():
    stock = ROOT / 'analysis/sihp1020.elf'
    assert stock.is_file(), 'Run from repository root or set HP1020_ROOT.'
    capture = Path(tempfile.mkdtemp(prefix='hp1020-usb-irq-capture-', dir='/tmp'))
    print('Independent USB IRQ cut captures: ' + str(capture), flush=True)
    sources, origins = {}, {}
    for path in source_paths():
        name = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else 'draft/' + path.name
        assert name not in sources
        sources[name], origins[name] = sha(path.read_bytes()), str(path)
        target = capture / 'source' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        assert sha(target.read_bytes()) == sources[name]
    (capture / 'source-sha256.json').write_text(json.dumps(sources, indent=2, sort_keys=True) + '\n')
    (capture / 'source-origins.json').write_text(json.dumps(origins, indent=2, sort_keys=True) + '\n')
    program = Program(stock, os.environ.get('XTENSA_PREFIX', '/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf'))
    evidence = audit(program, stock.read_bytes())
    (capture / 'original-byte-audit.json').write_text(json.dumps(evidence, indent=2, sort_keys=True) + '\n')
    specs = list(case_specs())
    assert len(specs) == 82 and len({case['name'] for case in specs}) == 82
    results = []
    with QemuRAM() as q:
        version = q.version
        for case in specs:
            a = execute(program, case, None, capture, evidence['chunks'])
            b = execute(program, case, q, capture, evidence['chunks'])
            for key in ('phase', 'entry', 'stop_before', 'registers', 'expected_registers', 'sar', 'expected_sar',
                        'original_entry_executed', 'proposed_call', 'expected_native_cpu_state',
                        'before_memory', 'expected_memory', 'actual_memory',
                        'accesses', 'expected_accesses', 'setup_record_hex', 'bulk_record_hex', 'original_instructions_retired'):
                assert a[key] == b[key], (case['name'], key)
            results.append(dict(input=case, interpreter=a, qemu=b, status='pass'))
            print(f'Independent IRQ cuts: {len(results)} conditional/control cases passed', flush=True)
        excluded = reject_excluded(program, q, capture)
    assert all(sha(Path(origins[name]).read_bytes()) == digest for name, digest in sources.items()), 'source changed during execution'
    counts = dict(samples=8, lanes=34, out0_common_wake=2, removed_redirect=14, standalone_mmio=24)
    actual_counts = {phase: sum(row['input']['phase'] == phase and row['input']['kind'] == 'conditional_phase'
                                for row in results) for phase in PHASES}
    actual_counts.update(removed_redirect=sum(row['input']['kind'] == 'removed_literal_redirect' for row in results),
                         standalone_mmio=sum(row['input']['kind'] == 'standalone_peripheral_instruction' for row in results))
    assert actual_counts == counts
    report = dict(status='pass', cases=results, counts=counts, phase_definitions=PHASES,
        excluded_code_controls=excluded, source_sha256=sources, source_origins=origins,
        original_byte_audit=evidence, stock_elf_sha256=STOCK_SHA, qemu_version=version,
        original_entry_executed_only_in_samples=True, independent_phases=True,
        original_entry_supplied_cpu=dict(ps_woe=1, ps_callinc=0, windowbase=0,
            windowstart=1, initial_sar=0, stack_adjustment=48,
            synthetic_caller_executed=False, actual_interrupt_entry_established=False),
        omitted_helpers_executed=False, supplied_services=[], actual_peripheral_accesses=0,
        completed_usb_control_transfers=0, completed_native_page_lifecycles=0,
        physical_event_order_established=False, coherent_setup_capture_established=False,
        overwrite_prevention_established=False, controller_settlement_established=False,
        scope='Three independent original-instruction RAM cuts: ordered DEVINT/EPINT sampling and reset-ack intent; literal endpoint acknowledgements and pre-call lane selection; a separately seeded OUT0 common-wake proposal. Complete RAM, ordered accesses and all logical registers/SAR are checked against supplied-state oracles.',
        limits='No uninterrupted IRQ lifecycle is executed. Only the prefix runs original ENTRY, from supplied WOE1/CALLINC0/WB0/WS1 with no artificial caller; this is not actual interrupt entry. Later phases begin with explicit registers/stack and no ENTRY. No configuration, timer, kernel, wakeup, bulk service/rearm, request dispatch or descriptor return helper executes. Peripheral literals point to private RAM; stores do not model W1C, timing, DMA, masks, cache visibility or physical interrupts. A mask/pending mismatch is a conditional software predicate, not a demonstrated reachable hardware bug or lost event. Co-pending bits and scan order provide no chronology or reset generation for SETUP. No selected cut acquires/copies/returns the SETUP record; the future ingress barrier still needs stable CPU-visible ownership plus a justified relation to reset. No real USB completion, physical cancellation, hardware stall clearing, boot or printing is established.')
    text = json.dumps(report, separators=(',', ':'), sort_keys=True) + '\n'
    markdown = '# Original USB IRQ sampling and capture boundary\n\n' + report['scope'] + '\n\n' + (
        '44 conditional cut profiles and38 pre-peripheral guard profiles per engine. '
        'These are separate supplied-state cuts, with zero completed physical transfers.\n\n') + report['limits'] + '\n'
    (capture / 'report.json').write_text(text)
    (capture / 'report.md').write_text(markdown)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.with_suffix('.json').write_text(text)
    OUT.with_suffix('.md').write_text(markdown)
    print('Independent USB IRQ cut capture complete: ' + str(capture), flush=True)


if __name__ == '__main__':
    main()
