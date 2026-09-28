"""Original video initialization prefix and buffer ownership in offline RAM.

The enclosing constructor stops before its first peripheral setup instruction.
Only an explicitly seeded pool and synthetic task/CPU context are supplied.
Allocation retry sleeps, waiters, scheduling and every hardware tail are excluded.
"""
import hashlib

from hp1020_stock_notifications import invoke

INITIALIZED = 0x100147e3
RETRY_STOPS = (0x1001486c,0x100148ad)
CELLS = (0x10006830,0x10006838)
SIZES = (0x9900,0x10000)
# Exclude the retry CALLs themselves, not just their scheduler callee.
CODE = [(0x10014738,INITIALIZED),(0x10014838,0x1001486c),
        (0x1001486f,0x100148ad),(0x100148b0,0x100148da),
        (0x100148dc,0x100148fa),(0x1001816c,0x100181a1),
        (0x1001716c,0x10017184),(0x100171b0,0x100171d7)]
EXCLUDED = (INITIALIZED,0x100147ee,0x100147f8,*RETRY_STOPS,0x1001766c)
AUDIT = [(0x10014738,INITIALIZED),(0x10014838,0x1001488c),
         (0x1001488c,0x100148bc),(0x100148bc,0x100148da),
         (0x100148dc,0x100148fa),(0x1001816c,0x100181a1),
         (0x1001716c,0x10017184)]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pointers(state):
    return [state.read(state.read(cell,4),4) for cell in CELLS]


def live(blocks):
    return [b for b in blocks if b[2]&0x80000000]


def owned(state,pointer,size):
    assert pointer%16 == 0
    matches = [b for b in live(state.blocks())
               if b[0]+12 <= pointer and pointer+size <= b[0]+12+b[1]]
    assert len(matches) == 1,(pointer,size,matches)
    return matches[0]


def initialize(state,engine,fill,bounded):
    state.code_ranges += CODE
    state.handoff_active = True
    video = state.read(0x10006770,4)
    semaphore = state.read(0x10006810,4)
    assert semaphore == video+116 and state.read(semaphore,4) == 0
    assert pointers(state) == [0,0]
    assert [state.read(c,4) for c in (0x10006834,0x10005e6c,0x10005f20)] == [0x1900,0x8000,0x10000]
    # Dirty the video state, preserving the original uncreated semaphore. The
    # original constructor, not host writes, must create the ready idle state.
    state.put(video,bytes([fill])*260)
    state.put(semaphore,bytes(28))
    stop,visited = bounded(state,engine,0x10014738,'video_initialize',
        lambda pc,read,reg:pc in (INITIALIZED,*RETRY_STOPS))
    ptrs = pointers(state)
    records = [dict(pointer=p,size=n,block=owned(state,p,n),sha256=sha(state.bytes_at(p,n)))
               for p,n in zip(ptrs,SIZES) if p]
    if ptrs[0]:
        assert state.bytes_at(ptrs[0],SIZES[0]) == bytes([255])*SIZES[0]
    if ptrs[1]:
        assert state.bytes_at(ptrs[1],SIZES[1]) == bytes([fill])*SIZES[1]
    if stop == INITIALIZED:
        assert len(records) == 2
        assert {0x10014838,0x1001488c,0x100131b8,0x1001b4c8,0x1001811c,0x1001716c}.issubset(visited)
        # The original initializer clears 260 bytes then sets its two sentinels
        # and its embedded original semaphore. All other state remains zero.
        expected = bytearray(260)
        for offset in (92,256):
            expected[offset:offset+4] = bytes.fromhex('bed4dad1')
        expected[116:144] = state.bytes_at(semaphore,28)
        assert state.bytes_at(video,260) == expected
        assert state.read(semaphore,4) == state.read(0x100065bc,4)
        assert state.read(semaphore+8,4) == 1
        assert state.read(semaphore+12,4) == state.read(semaphore+16,4) == 0
        table = state.read(0x10006a60,4)
        handlers = {str(number):state.read(table+number*4,4)
                    for number in (10,11,19,21,20)}
        assert list(handlers.values()) == [state.read(c,4) for c in
            (0x1000681c,0x10006820,0x10006824,0x10006828,0x1000682c)]
    else:
        assert stop == RETRY_STOPS[len(records)]
        assert 0x1001766c not in visited and 0x1001478e not in visited
        handlers = {}
    return dict(stop=hex(stop),outcome='initialized_before_peripherals' if stop == INITIALIZED else 'allocation_failed_before_retry',
        allocations=records,pool_size=state.pool_size,pool_blocks=state.blocks(),
        video_sha256=sha(state.bytes_at(video,260)),registered_handlers=handlers,
        hardware_tail_executed=False,retry_executed=False)


def release_and_reuse(state,engine,initial,initial_blocks):
    """An isolated idle ownership experiment, never release active page buffers."""
    video = state.read(0x10006770,4)
    assert all(state.read(video+offset,4) == 0 for offset in (96,100,108))
    allocated = state.blocks()
    ptrs = pointers(state)
    for entry in (0x10014838,0x1001488c):
        state.visited.clear()
        assert invoke(state,entry,qemu=engine) == 0
        assert 0x100131b8 not in state.visited
    assert state.blocks() == allocated and pointers(state) == ptrs
    for entry in (0x100148bc,0x100148dc):
        state.visited.clear()
        assert invoke(state,entry,qemu=engine) == 1
        assert 0x10013408 in state.visited
    freed = state.blocks()
    assert pointers(state) == [0,0]
    assert live(freed) == live(initial_blocks)
    for pointer,size in zip(ptrs,SIZES):
        assert any(not flags&0x80000000 and base+12 <= pointer
                   and pointer+size <= base+12+n for base,n,flags in freed)
    # Free marks the split blocks reusable; it does not eagerly coalesce them.
    assert len(freed) == len(initial_blocks)+2
    for entry in (0x100148bc,0x100148dc):
        state.visited.clear()
        assert invoke(state,entry,qemu=engine) == 0
        assert 0x10013408 not in state.visited
    assert state.blocks() == freed
    for entry in (0x10014838,0x1001488c):
        assert invoke(state,entry,qemu=engine) == 1
    assert pointers(state) == ptrs and state.blocks() == allocated
    assert state.bytes_at(ptrs[0],SIZES[0]) == bytes([255])*SIZES[0]
    assert sha(state.bytes_at(ptrs[1],SIZES[1])) == initial['allocations'][1]['sha256']
    # Leave the isolated experiment with no video allocations held.
    for entry in (0x100148bc,0x100148dc):
        assert invoke(state,entry,qemu=engine) == 1
    assert state.blocks() == freed
    return dict(already_initialized_returns=[0,0],release_returns=[1,1],empty_release_returns=[0,0],
                reallocation_returns=[1,1],same_addresses_reused=True,
                original_live_allocations_unchanged=True,freed_pool_blocks=freed,
                final_video_pointers=pointers(state),completed_page_lifecycles=0)


def prepared_layout(state,initial):
    video = state.read(0x10006770,4)
    first,second = [r['pointer'] for r in initial['allocations']]
    stride,padding = state.read(video+184,4),state.read(video+244,4)
    scale = 2048//stride
    first_size,second_size = scale*4*stride,scale*8*stride
    first_slots = [state.read(video+i*4,4) for i in range(4)]
    second_slots = [state.read(video+16+i*4,4) for i in range(4)]
    assert first_slots == [first+padding*stride+i*first_size for i in range(4)]
    assert second_slots == [second+i*second_size for i in range(4)]
    assert state.read(video+80,4) == first
    assert state.read(video+84,4) == first+padding*stride+first_size*4
    assert first_slots[-1]+first_size <= first+SIZES[0]
    assert second_slots[-1]+second_size <= second+SIZES[1]
    assert padding == 0
    assert state.bytes_at(first,SIZES[0]) == bytes([255])*SIZES[0]
    assert sha(state.bytes_at(second,SIZES[1])) == initial['allocations'][1]['sha256']
    return dict(stride=stride,first_slot_bytes=first_size,second_slot_bytes=second_size,
                first_slots=first_slots,second_slots=second_slots,
                first_unused_tail=SIZES[0]-first_size*4,
                all_spans_inside_original_allocations=True,buffers_unchanged=True)
