#!/usr/bin/env python3
"""Execute original allocation/free against partition, ownership and byte oracles."""
import hashlib
import json
import os
from pathlib import Path
import random
from hp1020_stock_pool import PoolRAM
from hp1020_stock_notifications import invoke
from hp1020_xtensa_call0 import Program
from hp1020_qemu_ram import QemuRAM

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'analysis/open-firmware-model/stock-execution'


def setup(program,engine,**kw):
    s = PoolRAM(program,**kw)
    assert invoke(s,0x1001811c,[s.read(0x100066ac,4),0,1],engine)==0
    s.blocks()
    return s


def allocate(s,engine,size,kind=1,public=False):
    return invoke(s,0x10013140 if public else 0x100131b8,[size,kind],engine)


def free(s,engine,pointer):
    invoke(s,0x10013408,[pointer],engine)


def basic(program,engine,fill,offset,size,kind):
    s = setup(program,engine,fill=fill,offset=offset)
    rounded = (size+3)&~3
    required = (rounded//16)*16+28 if kind in (0,2) else rounded
    pointer = allocate(s,engine,size,kind,public=True)
    expected = (s.pool+27)&~15 if kind in (0,2) else s.pool+12
    assert pointer==expected
    assert s.blocks()==[(s.pool,required,0x80000000|(0x20000000 if kind==0 else 0)),
                        (s.pool+12+required,8192-required-24,0x40000000)]
    assert s.bytes_at(pointer,size)==bytes([fill])*size
    assert s.bytes_at(s.pool+12,pointer-s.pool-12)==bytes(pointer-s.pool-12)
    s.put(pointer,bytes([0x5a])*size)
    before = s.bytes_at(s.pool,8192)
    free(s,engine,pointer)
    after = bytearray(before)
    after[8] &= 0x7f
    assert s.bytes_at(s.pool,8192)==after,'free changed bytes beyond allocated flag'
    assert s.bytes_at(pointer,size)==bytes([0x5a])*size
    blocks = s.blocks()
    free(s,engine,0)
    assert s.blocks()==blocks and s.bytes_at(s.pool,8192)==after
    return blocks


def split_threshold(program,engine,fill,remainder):
    s = setup(program,engine,size=12+64+remainder,fill=fill)
    assert allocate(s,engine,64)==s.pool+12
    expected = [(s.pool,64+remainder,0xc0000000)] if remainder<=48 else [
        (s.pool,64,0x80000000),(s.pool+76,remainder-12,0x40000000)]
    assert s.blocks()==expected
    free(s,engine,s.pool+12)
    return s.blocks()


def fragmentation(program,engine,fill):
    s = setup(program,engine,fill=fill)
    pointers = [allocate(s,engine,64) for _ in range(4)]
    assert pointers==[s.pool+12+i*76 for i in range(4)]
    for i,pointer in enumerate(pointers):
        s.put(pointer,bytes([0x30+i])*64)
    for pointer in pointers[:3]:
        free(s,engine,pointer)
        s.blocks()
    assert len(s.blocks())==5,'free should defer coalescing'
    pointer = allocate(s,engine,160)
    assert pointer==pointers[0]
    assert s.blocks()[:3]==[(s.pool,160,0x80000000),(s.pool+172,44,0x20000000),(s.pool+228,64,0x80000000)]
    assert s.bytes_at(pointers[3],64)==bytes([0x33])*64
    free(s,engine,pointer)
    free(s,engine,pointers[3])
    # A large type-2 request bypasses the reserve check and forces all adjacent
    # free blocks to coalesce. Alignment slack is included in the request size.
    pointer = allocate(s,engine,8128,2)
    assert pointer==(s.pool+27)&~15
    assert s.blocks()==[(s.pool,8180,0xc0000000)]
    free(s,engine,pointer)
    assert s.blocks()==[(s.pool,8180,0x40000000)]
    return s.blocks()


def random_trace(program,engine,fill,seed):
    s = setup(program,engine,size=4096,fill=fill)
    rng = random.Random(seed)
    live = {}
    trace = []
    for step in range(72):
        if live and rng.randrange(3)==0:
            pointer = rng.choice(sorted(live))
            free(s,engine,pointer)
            del live[pointer]
            trace.append(('free',pointer))
        else:
            size,kind = rng.choice((1,4,13,64,120,148,512,1024)),rng.choice((1,2))
            pointer = allocate(s,engine,size,kind)
            trace.append(('allocate',size,kind,pointer))
            if pointer:
                assert pointer%(16 if kind==2 else 4)==0
                assert all(pointer+size<=p or p+len(data)<=pointer for p,data in live.items())
                payload = bytes([step+1])*size
                s.put(pointer,payload)
                live[pointer] = payload
        blocks = s.blocks()
        assert len([1 for _,_,flags in blocks if flags&0x80000000])==len(live)
        for pointer,payload in live.items():
            assert s.bytes_at(pointer,len(payload))==payload,'live allocation overwritten'
            assert len([1 for a,n,f in blocks if f&0x80000000 and a+12<=pointer and pointer+len(payload)<=a+12+n])==1
    for pointer in live:
        free(s,engine,pointer)
    assert not any(flags&0x80000000 for _,_,flags in s.blocks())
    return trace,s.blocks()


def repeated_free_gate(program,engine,fill):
    s = setup(program,engine,fill=fill)
    pointer = allocate(s,engine,64)
    free(s,engine,pointer)
    before = s.bytes_at(s.pool,s.pool_size)
    try:
        free(s,engine,pointer)
    except ValueError as error:
        assert s.pc==0x10013429 and f'{s.pool-4:#x}' in str(error),str(error)
        assert s.bytes_at(s.pool,s.pool_size)==before
        return 'read_before_arena_detected'
    raise AssertionError('repeated free unexpectedly accepted by strict RAM gate')


def main():
    p = Program(ROOT/'analysis/sihp1020.elf',os.environ.get('XTENSA_PREFIX','/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf'))
    cases = []
    with QemuRAM() as q:
        for fill in (0,0xcc):
            for offset in (0,4):
                for size in (1,4,13,16,33,120):
                    for kind in (0,1,2):
                        args = (fill,offset,size,kind)
                        assert basic(p,None,*args)==basic(p,q,*args)
                        cases.append(dict(test='allocation_free',fill=fill,offset=offset,size=size,kind=kind,status='pass'))
            for remainder in (48,52):
                assert split_threshold(p,None,fill,remainder)==split_threshold(p,q,fill,remainder)
                cases.append(dict(test='split_threshold',fill=fill,remainder=remainder,status='pass'))
            assert fragmentation(p,None,fill)==fragmentation(p,q,fill)
            cases.append(dict(test='deferred_coalescing',fill=fill,status='pass'))
            for seed in (1020,2026):
                assert random_trace(p,None,fill,seed)==random_trace(p,q,fill,seed)
                cases.append(dict(test='ownership_trace',fill=fill,seed=seed,operations=72,status='pass'))
        for fill in (0,0xcc):
            assert repeated_free_gate(p,None,fill)==repeated_free_gate(p,q,fill)
            cases.append(dict(test='repeated_free_gate',fill=fill,status='pass'))
        admission = [(4096,64,0,False),(4096,64,1,True),(4096,64,2,True),
                     (4096,2048,1,True),(4096,2052,1,False),(4096,2052,2,True),
                     (8192,4096,1,False),(8216,4096,1,True),(8192,8192,2,False)]
        for arena,size,kind,success in admission:
            outcomes = []
            for engine in (None,q):
                s = setup(p,engine,size=arena)
                pointer = allocate(s,engine,size,kind)
                assert bool(pointer)==success,(arena,size,kind,pointer)
                blocks = s.blocks()
                if not success:
                    assert blocks==[(s.pool,arena-12,0x40000000)]
                outcomes.append((pointer,blocks))
            assert outcomes[0]==outcomes[1]
            cases.append(dict(test='admission',arena=arena,size=size,kind=kind,success=success,status='pass'))
    report = dict(status='pass',total_cases=len(cases),cases=cases,
        elf_sha256=hashlib.sha256(p.path.read_bytes()).hexdigest(),
        source_sha256={name:hashlib.sha256((ROOT/'scripts'/name).read_bytes()).hexdigest() for name in
            ('validate-hp1020-stock-pool.py','hp1020_stock_pool.py','hp1020_stock_queue.py','hp1020_stock_notifications.py','hp1020_qemu_task.py')},
        findings=[
            'Original public allocation on successful requests, allocation core, free and semaphore create/get/put execute in both engines without whole-function replacements.',
            'The pool is a partition of 12-byte headers and payloads. Header magic is 0x2e3d4c5a; size is at +4; flags at +8 include allocated bit 31, terminal bit 30 and type-0 marker bit 29 on allocated blocks (free blocks can retain stale bit 29). Lower 24 bits record a caller address and intentionally differ between synthetic caller environments.',
            'Type 1 rounds to four bytes. Types 0 and 2 reserve (rounded_size // 16) * 16 + 28 bytes and return a 16-byte-aligned pointer; only leading alignment padding is zeroed. Requested payload bytes retain prior contents.',
            'A remainder of 48 bytes is absorbed; 52 bytes produces a new 12-byte header and 40-byte free payload. Free clears the allocated flag and restores the block payload size to the counter, without clearing payload or immediately coalescing. A later scan merges adjacent free blocks, returning each removed header to free-byte accounting.',
            'The core can reject a request despite enough contiguous space: type 0 preserves a reserve; type 1 permits requests through 2048 bytes despite the reserve but rejects the tested larger request below it; type 2 bypasses that reserve check. Core failure returns zero.',
            'Repeatedly freeing the first type-1 block reaches a backward header search before the bounded arena. Both engines are stopped by the strict RAM gate at that read; there is no general double-free safety guarantee or claim that this occurs on the device.',
            'Seeded allocation/release traces verify exact arena partition and free-byte accounting after every operation, no overlapping live allocations, preserved live contents, semaphore balance, and matching independent-engine outcomes.'
        ],
        limits='One explicitly seeded, word-aligned RAM arena and one ordinary current thread. No boot pool discovery, concurrent allocation, semaphore contention, allocator retry/sleep/low-memory notification path, IRQs, timers or hardware. Null free is tested; invalid and repeated frees have no safety guarantee. Differential comparison excludes caller-address provenance bits, but validates block structure and independently written live payloads. Type-0 wraparound policy is not covered by the initial-allocation cases.')
    (OUT/'pool.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    (OUT/'pool.md').write_text('# Original memory allocation and release\n\n'+f'{len(cases)} cases pass in the interpreter and independent QEMU.\n\n'+'\n'.join('- '+x for x in report['findings'])+'\n\n'+report['limits']+'\n')
    print(f'Original memory pool: {len(cases)} independent cases')


if __name__=='__main__':
    main()
