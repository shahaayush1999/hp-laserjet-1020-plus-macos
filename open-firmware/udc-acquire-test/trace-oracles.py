"""UNEXECUTED independent acquisition expectations; no production imports.

Derived from the pre-implementation boundary review, existing OUT/adapter
contracts, fixed fixture allocations and the public acquisition header only.
The new acquisition C implementation has not been read. Opcode allocation and
appended diagnostic positions remain a lead-owned fixture integration decision.
"""

OK, WAIT, STALE, INVALID, FAULT, ADAPTER_ERROR = range(6)
DESCRIPTOR_CPU, PAYLOAD_CPU, ACQUIRE_ORDER = 6, 7, 8
IO_OK, NOT_PERFORMED, UNKNOWN = 0, 1, 2
DESCRIPTOR_DMA = 0x579bdf10
RECEIVE_DMAS = (0x24681340, 0x24682340, 0x24683340, 0x24684340)
REASON_IO = 0x80000103
DEFAULT_FACTS = bytes((1, 1, 1))
GET_CONFIGURATION = bytes.fromhex('8008000000000100')
EXPECTED_BLACK_PIXELS = bytes.fromhex('ff' * 32)
SMALL_BIE = bytes.fromhex('000001000000002000000008000000041000035cfd98ff02ff02')
SMALL_BIE_SHA256 = '78744d4c1f1f3ac06000192663330834b02b277df26f790aaa340ac322e9cf99'


def be32(value):
    assert type(value) is int and 0 <= value <= 0xffffffff
    return value.to_bytes(4, 'big')


def words(values):
    return b''.join(be32(value) for value in values)


def slot_dma(slot):
    assert type(slot) is int and 0 <= slot < 4
    return RECEIVE_DMAS[slot]


def literal_descriptor(slot, count, *, done=True):
    """Only DONE and explicit not-DONE controls; not a descriptor decoder."""
    assert type(count) is int and 0 <= count <= 64
    status = (0x88000000 if done else 0x48000000) | count
    return words((status, 0, slot_dma(slot), 0))


def cpu_poison(slot, *, false_done=False):
    """Synthetic fixture writes to descriptor16 and this prefix64 ONLY."""
    dma = slot_dma(slot)
    descriptor = (words((0x88000040, 0, dma, 0)) if false_done else
        words((0xc35a0000 | slot, 0x13579bdf, 0xfedcba90, 0x2468ace0)))
    payload = bytes((0xd3 ^ (slot * 0x29) ^ (i * 0x17)) & 255 for i in range(64))
    return descriptor, payload


def device_images(slot, payload, *, done=True):
    """Input bytes are authoritative, never reconstructed from acquired RAM.

    Every unused byte in the owned64-byte prefix is deliberately nonzero and
    independent of fill. It is acquired but must not be passed to the parser.
    """
    assert isinstance(payload, bytes) and len(payload) <= 64
    tail = bytes((0x69 ^ (slot * 0x1d) ^ (i * 7)) & 255
                 for i in range(len(payload), 64))
    return literal_descriptor(slot, len(payload), done=done), payload + tail


def acquire_trace(slot, *, fail_kind=None, outcome=NOT_PERFORMED):
    """Literal (kind,DMA,length,result) prefix, before event/ordinal tagging."""
    full = ((DESCRIPTOR_CPU, DESCRIPTOR_DMA, 16, IO_OK),
            (PAYLOAD_CPU, slot_dma(slot), 64, IO_OK),
            (ACQUIRE_ORDER, 0, 0, IO_OK))
    if fail_kind is None:
        return full
    assert fail_kind in (DESCRIPTOR_CPU, PAYLOAD_CPU, ACQUIRE_ORDER)
    assert type(outcome) is int and 0 < outcome <= 0xffffffff
    result = []
    for kind, dma, length, _ in full:
        result.append((kind, dma, length, outcome if kind == fail_kind else IO_OK))
        if kind == fail_kind:
            break
    return tuple(result)


def event_trace(event, prior_ordinal, trace):
    assert event > 0 and prior_ordinal >= 0
    return tuple((event, prior_ordinal+i+1, *row) for i, row in enumerate(trace))


def expected_visibility(slot, device_descriptor, device_payload, *,
                        false_done=False, fail_kind=None, outcome=NOT_PERFORMED):
    """Fixture hook effect oracle, not a physical cache implementation.

    OK copies exactly one owned range. NOT_PERFORMED copies none. UNKNOWN
    copies exactly its first half, chosen explicitly by this test. Order has
    no byte effect. Invalid raw outcomes have no byte effect in this fixture.
    """
    assert len(device_descriptor) == 16 and len(device_payload) == 64
    descriptor, payload = cpu_poison(slot, false_done=false_done)
    for kind, _, _, result in acquire_trace(slot, fail_kind=fail_kind, outcome=outcome):
        if kind == DESCRIPTOR_CPU:
            if result == IO_OK:
                descriptor = device_descriptor
            elif result == UNKNOWN:
                descriptor = device_descriptor[:8] + descriptor[8:]
        elif kind == PAYLOAD_CPU:
            if result == IO_OK:
                payload = device_payload
            elif result == UNKNOWN:
                payload = device_payload[:32] + payload[32:]
    return descriptor, payload


def failure_fields(cookie, slot, kind, outcome):
    """Fields independent of implementation output; cookie from DCD history."""
    assert len(cookie) == 5 and cookie[0] and cookie[4] == 1
    assert kind in (DESCRIPTOR_CPU, PAYLOAD_CPU, ACQUIRE_ORDER)
    assert outcome != IO_OK
    prefix, dma, length, operation = {
        DESCRIPTOR_CPU: (0, DESCRIPTOR_DMA, 16, 1),
        PAYLOAD_CPU: (1, slot_dma(slot), 64, 2),
        ACQUIRE_ORDER: (3, 0, 0, 3),
    }[kind]
    return dict(cookie=list(cookie), prefix=prefix, dma=dma, bytes=length,
                io_result=outcome, reason=REASON_IO, operation=operation,
                snapshot_valid=0)


def captured_fields(cookie, descriptor, result):
    assert len(cookie) == 5 and cookie[0] and cookie[4] == 1
    assert len(descriptor) == 16 and result in (OK, WAIT, FAULT, ADAPTER_ERROR)
    return dict(cookie=list(cookie), prefix=15, dma=0, bytes=0, io_result=0,
                operation=3, snapshot_valid=1, snapshot_hex=descriptor.hex(),
                result=result)


def document_event(generation):
    """One successfully notified document with one page; explicit BE words."""
    assert generation >= 2
    return words((generation, 1, 0, 1, 0))


def fact_probes():
    result = []
    for index, name in enumerate(('transfer-settled', 'mapping-lease', 'cache-range-safe')):
        for value, expected in ((0, WAIT), (2, INVALID), (255, INVALID)):
            facts = bytearray(DEFAULT_FACTS)
            facts[index] = value
            result.append((name+'/'+str(value), bytes(facts), expected))
    return tuple(result)


def mutated_cookie(cookie, mutation):
    assert len(cookie) == 5 and 1 <= mutation <= 5
    result = list(cookie)
    result[mutation-1] ^= 0x80 if mutation == 5 else 0x80000000
    return tuple(result)


# Named semantic profiles, not another cross-product descriptor-policy matrix.
# Entries contain expected generation of the sole completed small document.
POSITIVE_AND_GUARD_PROFILES = (
    ('visibility-packets', 2),
    ('facts-and-identities', 2),
    ('callback-authority', 2),
    ('held-setup-settlement', 2),
    ('admitted-reset-settlement', 3),
    ('same-address-reuse', 3),
    ('prepared-publication-failure', 3),
    ('exposed-publication-failure', 3),
    ('endpoint-fault-only', 3),
    ('not-done-fresh-retry', 2),
)
HOOK_FAILURE_PROFILES = (
    ('descriptor-not-performed', DESCRIPTOR_CPU, NOT_PERFORMED),
    ('descriptor-unknown', DESCRIPTOR_CPU, UNKNOWN),
    ('payload-not-performed', PAYLOAD_CPU, NOT_PERFORMED),
    ('payload-unknown', PAYLOAD_CPU, UNKNOWN),
    ('order-not-performed', ACQUIRE_ORDER, NOT_PERFORMED),
    ('order-unknown', ACQUIRE_ORDER, UNKNOWN),
)


def profiles():
    names = [name for name, _ in POSITIVE_AND_GUARD_PROFILES]
    names += [name for name, _, _ in HOOK_FAILURE_PROFILES]
    return [('acquire/'+name, fill, 64, 0) for name in names for fill in (0, 204)]


def expected_generation(name):
    short = name.removeprefix('acquire/')
    for title, generation in POSITIVE_AND_GUARD_PROFILES:
        if title == short:
            return generation
    assert short in [title for title, _, _ in HOOK_FAILURE_PROFILES]
    return 3
