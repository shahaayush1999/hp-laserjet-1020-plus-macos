#!/usr/bin/env python3
"""Unexecuted independent literals for the one-entry RAM experiment.

Written before candidate assembly/linker/workload/runner review. No producer
imports, no source-derived expected reports and no execution facility. A runner
may call these pure helpers after independently recording real observations.
Debugger register numbers, target struct offsets and private decoder bytes are
intentionally outside this oracle.
"""

import struct

MAIN_START, MAIN_END = 0x10003000, 0x100351E0
ENTRY = 0x100167A8
STATE, STATE_BYTES = 0x1000E000, 13496
MEMORY, MEMORY_BYTES = 0x10016800, 114704
MAILBOX, MAILBOX_BYTES = 0x10014040, 1024
STACK_BOTTOM, STACK_TOP = 0x10012000, 0x10014000
DATA, DATA_BYTES = 0x1000D020, 256
OUTPUT, OUTPUT_BYTES = 0x1002A810, 32768
ZERO_RANGES = ((STATE, STATE_BYTES), (MEMORY, MEMORY_BYTES),
               (MAILBOX, MAILBOX_BYTES))
MUTABLE_RANGES = ZERO_RANGES + ((STACK_BOTTOM, STACK_TOP - STACK_BOTTOM),)
ISLANDS = ((0x10000000, 0x10000184), (0x10000200, 0x1000023C),
           (0x10000270, 0x10000350), (0x10000370, 0x1000049C),
           (0x10100020, 0x10100304), (0x10100320, 0x1010032C))
SENTINEL = bytes.fromhex("31527394b5d6f718395a7b9cbddeff20") * 16
BIE = bytes.fromhex("000001000000002000000008000000041000035cfd98ff02ff02")
PIXELS = b"\xff" * 32
FRAGMENTS = (64, 64, 64, 64, 64, 32)
DOCUMENT = (1, 1, 0, 1)
PAINTS = ((0xA5, 0x5A), (0xCC, 0x96))
CPU_PROFILES = (
    dict(name="ordinary-privilege", ps=0, intenable=0, windowbase=0,
         windowstart=1, sar=0, lbeg=0, lend=0, lcount=0),
    dict(name="dirty-window3", ps=0x70302, intenable=1, windowbase=3,
         windowstart=0x89, sar=37, lbeg=0x10003000, lend=0x10003020, lcount=17),
    dict(name="dirty-window7-excm", ps=0x50711, intenable=2, windowbase=7,
         windowstart=0xC1, sar=63, lbeg=0x10003040, lend=0x10003060, lcount=65535),
)


def need(condition, message):
    if not condition:
        raise ValueError(message)


def physical_ars(profile_index):
    need(profile_index in (0, 1, 2), "CPU profile index")
    return [0x8A000001 + profile_index * 0x00100000 + i * 0x00010101
            for i in range(32)]


def fnv32(data):
    value = 0x811C9DC5
    for byte in data:
        value = ((value ^ byte) * 0x01000193) & 0xFFFFFFFF
    return value


def small_input():
    """Known ZjStream framing, not a candidate parser/decoder oracle."""
    def chunk(kind, payload=b"", count=0, reserved=0):
        return struct.pack(">IIIHH", 16 + len(payload), kind, count,
                           reserved, 0x5A5A) + payload

    def item(number, value):
        return struct.pack(">IHBBI", 12, number, 1, 0, value)

    start = b"".join(item(n, v) for n, v in ((1, 0), (2, 1), (0, 0)))
    page = b"".join(item(n, v) for n, v in (
        (23, 0), (17, 16), (18, 8), (16, 2), (12, 32), (13, 8),
        (7, 1), (8, 600), (9, 600), (5, 7), (4, 1), (3, 9), (6, 1)))
    coded = BIE[20:] + bytes(16 + ((-len(BIE[20:])) & 3))
    result = (b"JZJZ" + chunk(0, start, 3, 36) + chunk(2, page, 13, 156)
              + chunk(4, BIE[:20]) + chunk(5, coded)
              + chunk(6) + chunk(3) + chunk(1))
    need(len(result) == 352, "independent input length")
    return result


def receive_bytes():
    memory = bytearray(4096)
    source = small_input()
    position = 0
    for index, length in enumerate(FRAGMENTS):
        offset = (index % 4) * 1024
        memory[offset:offset + length] = source[position:position + length]
        position += length
    need(position == len(source), "six supplied fragments cover input")
    return bytes(memory)


def output_bytes():
    return PIXELS + bytes(OUTPUT_BYTES - len(PIXELS))


def slice_main(image, address, length):
    need(len(image) == MAIN_END - MAIN_START, "full main capture length")
    need(MAIN_START <= address <= MAIN_END and 0 <= length <= MAIN_END - address,
         "main slice outside independently admitted envelope")
    return image[address - MAIN_START:address - MAIN_START + length]


def unchanged_outside(before, after, writable):
    need(len(before) == len(after) == MAIN_END - MAIN_START, "main pair size")
    for index, (old, new) in enumerate(zip(before, after)):
        address = MAIN_START + index
        if old != new and not any(a <= address < a + n for a, n in writable):
            raise ValueError(f"protected byte changed at0x{address:08x}")


def check_registers(registers, phase):
    need(phase in ("pre-c", "park"), "register phase")
    expected = dict(ps=15, intenable=0, windowbase=0, windowstart=1,
                    lbeg=0, lend=0, lcount=0)
    if phase == "pre-c":
        expected["sar"] = 0
    for name, wanted in expected.items():
        need(registers.get(name) == wanted, f"{phase}: {name} must be{wanted:#x}")
    ars = registers.get("physical_ar")
    need(isinstance(ars, (list, tuple)) and len(ars) == 32,
         f"{phase}: all32 physical ARs are required")
    need(ars[1] == STACK_TOP and not (ars[1] & 15), f"{phase}: owned SP")
    # Arbitrary call0 GPRs and final C-owned SAR are deliberately unconstrained.


def check_pre_c(before, observed, registers):
    check_registers(registers, "pre-c")
    unchanged_outside(before, observed, ZERO_RANGES)
    for address, count in ZERO_RANGES:
        actual = slice_main(observed, address, count)
        if any(actual):
            bad = next(i for i, byte in enumerate(actual) if byte)
            raise ValueError(f"pre-C owned byte not zero at0x{address + bad:08x}")
    need(slice_main(observed, DATA, DATA_BYTES) == SENTINEL,
         "pre-C initialized sentinel")


def check_islands(initial, observed):
    """Mappings use integer interval-start keys, values exact interval bytes."""
    need(set(initial) == set(observed) == {a for a, _ in ISLANDS}, "island set")
    for start, end in ISLANDS:
        need(len(initial[start]) == end - start, f"island length{start:#x}")
        need(initial[start] == observed[start], f"immutable island{start:#x}")


def mailbox_words(raw):
    need(len(raw) == MAILBOX_BYTES, "full1024-byte mailbox")
    return list(struct.unpack(">64I", raw[:256]))


def check_pre_finish(raw_mailbox, state):
    """First actual finish-entry observation, before its first instruction.

    State is independently read production fields, not inferred from mailbox
    final-snapshot words, which the workload may not have filled yet.
    """
    words = mailbox_words(raw_mailbox)
    need(raw_mailbox[256:288] == PIXELS, "pixels exist before finish")
    need(words[29:33] == [1, 1, 1, 32], "one software output before finish")
    need(words[33] == fnv32(PIXELS), "actual pixel FNV before finish")
    need(words[34:39] == [1, *DOCUMENT], "original END_DOC before finish")
    need(words[16:21] == [352, 6, 6, 6, 6], "six fragments before finish")
    wanted = dict(generation=1, issued=6, consumed=6, count=0, stopped=0,
                  finished=0, quiescent=0, parser_documents=1, stream_pages=1,
                  pages_drained=1, documents_completed=1)
    for name, value in wanted.items():
        need(state.get(name) == value, f"before finish: {name} must be{value}")


def expected_park_words():
    # Order is the public64-word ABI; private implementation is not imported.
    result = [0] * 64
    expected = {
        0: 0x48503130, 1: 1, 2: 2, 3: 0, 4: 5, 5: 0, 6: 0, 7: 0,
        8: 0, 9: 0, 10: 0, 11: 0, 12: 129224, 13: 256,
        14: 352, 15: fnv32(small_input()), 16: 352, 17: 6,
        18: 6, 19: 6, 20: 6, 21: 1, 22: 1, 23: 6, 24: 6,
        25: 0, 26: 1, 27: 0, 28: 1, 29: 1, 30: 1, 31: 1,
        32: 32, 33: fnv32(PIXELS), 34: 1, 35: 1, 36: 1,
        37: 0, 38: 1, 39: 0, 40: 1, 41: 1, 42: 1, 43: 1,
        44: 8, 45: 8, 46: 8, 47: 0, 48: 1, 49: 6, 50: 32,
        51: 1, 52: 8, 53: 4, 54: 0, 55: 0, 56: 0,
        57: fnv32(receive_bytes()), 58: fnv32(output_bytes()),
        59: STATE_BYTES, 60: MEMORY_BYTES, 61: 0, 62: 0, 63: 0,
    }
    need(set(expected) == set(range(64)), "complete independent mailbox ABI")
    for index, value in expected.items():
        result[index] = value
    return result


def check_park(before, observed, registers):
    check_registers(registers, "park")
    unchanged_outside(before, observed, MUTABLE_RANGES)
    need(slice_main(observed, DATA, DATA_BYTES) == SENTINEL,
         "park initialized sentinel")
    need(slice_main(observed, MEMORY, 4096) == receive_bytes(),
         "exact receive storage including reused slot tail")
    need(slice_main(observed, OUTPUT, OUTPUT_BYTES) == output_bytes(),
         "exact software output storage including untouched tail")
    raw = slice_main(observed, MAILBOX, MAILBOX_BYTES)
    actual, expected = mailbox_words(raw), expected_park_words()
    for index, (value, wanted) in enumerate(zip(actual, expected)):
        need(value == wanted, f"mailbox[{index}]={value:#x}, expected{wanted:#x}")
    need(raw[256:288] == PIXELS, "literal32-byte completed pixel witness")
    need(raw[288:] == bytes(736), "mailbox reserved zero tail")


# No __main__, runtime import, file write, emulator or source-execution path.
# The caller must separately prove initial-load seals, forbidden-access/call
# audit, uninterrupted execution, actual park PC, initial physical-register
# read-back, target member offsets, stack evidence and paired full captures.
