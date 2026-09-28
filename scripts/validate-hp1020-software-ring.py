#!/usr/bin/env python3
"""Decoded pixels enter actual stock ring storage through bounded RAM stages.

The host bridges decoder output into chunk-12 input and explicitly supplies
fill completion, output acceptance and consumption. Peripheral prefixes/tails
never execute. These are buffer transfers, not native page lifecycles.
"""
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'analysis/hardware-boundary/software-ring'


def module(name,filename):
    spec = importlib.util.spec_from_file_location(name,ROOT/'scripts'/filename)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


raw = module('raw_parser_delivery','validate-hp1020-raw-parser.py')
core = module('image_checks_delivery','validate-hp1020-image-core.py')
from hp1020_stock_notifications import invoke
from hp1020_qemu_ram import QemuRAM
from hp1020_xtensa_call0 import Program,Machine
from hp1020_raw_handoff import bounded,reject_excluded

CODE = [(0x10014244,0x10014290),
        (0x100143b8,0x100143bb),(0x1001445d,0x1001446b),
        (0x10013f34,0x10013f37),(0x10013f57,0x10013ff9),
        (0x10013ffc,0x10014014),(0x100140c9,0x100140e5),
        (0x100144d0,0x100144d3),(0x1001451c,0x10014524),
        (0x10014560,0x10014576)]
EXCLUDED = (0x10014290,0x10014293,0x10014298,0x100143bb,
            0x1001446b,0x10013f4c,0x10013ff9,0x10014014,
            0x100140c7,0x100140e5,0x10014524,0x10014576,0x10015648)


def transfer(program,engine,pixels,fill,index):
    rows = len(pixels)//1200
    assert rows in (1,4) and len(pixels) == rows*1200
    state,admission = raw.execute(program,engine,fill=fill,bitmap=0,page_bitmap=1,
        bih_chunk=True,width=9600,rows=rows,image=pixels,
        state_class=raw.handoff.state_class(raw.Parser),return_state=True)
    preparation = raw.handoff.run(state,engine,admission)
    assert preparation['prepare_stride'] == 1200
    assert preparation['output_layout']['first_slot_bytes'] == 4800
    state.code_ranges += CODE
    video = state.read(0x10006770,4)
    descriptor_base = state.read(0x100067bc,4)
    assert descriptor_base == video+32
    assert state.read(video+192,4) == state.read(video+244,4) == 0
    assert state.read(video+252,4)&0x80000000 == 0
    work,payload = admission['owner_hierarchy']['work'],admission['payload']
    source = admission['input_pointer']
    input_owner = state.bytes_at(work,148),state.bytes_at(payload,104)
    pool_before = state.blocks()
    first,second = [v['pointer'] for v in preparation['video_initialization']['allocations']]
    first_before,second_before = state.bytes_at(first,39168),state.bytes_at(second,65536)
    # Index 3 is an explicit wrap fixture, not three inferred earlier transfers.
    for offset in (216,220,224):
        assert state.read(video+offset,4) == 0
        state.write(video+offset,4,index)
    desc = descriptor_base+index*12
    target = state.read(video+index*4,4)
    assert target == first+index*4800
    assert state.read(video+204,4) == 4
    assert state.read(video+208,4) == state.read(video+212,4) == rows
    stages = []
    def snapshot(phase):
        stages.append(dict(phase=phase,
            descriptor=[state.read(desc+i*4,4) for i in range(3)],
            indices=[state.read(video+i,4) for i in (224,220,216)],
            remaining=[state.read(video+i,4) for i in (208,212)],
            target_sha256=core.sha(state.bytes_at(target,len(pixels)))))
    snapshot('prepared')
    stop,visited = bounded(state,engine,0x10014244,'descriptor_claim',
        lambda pc,read,reg:pc in (0x10014290,0x1001429a))
    assert stop == 0x10014290 and 0x10014283 in visited
    assert [state.read(desc+i*4,4) for i in range(3)] == [1,1,rows]
    assert state.read(video+208,4) == 0
    assert state.bytes_at(target,len(pixels)) == bytes([255])*len(pixels)
    snapshot('claimed_before_pixels')
    # The original occupied-descriptor guard returns without overwriting it.
    before = state.bytes_at(video,260)
    stop,visited = bounded(state,engine,0x10014244,'occupied_control',
        lambda pc,read,reg:pc in (0x10014290,0x1001429a))
    assert stop == 0x1001429a and state.bytes_at(video,260) == before
    assert 0x1001426e not in visited
    # An explicit software adapter uses original memcpy; this copy is not a
    # recovered stock caller and does not simulate compressed-image DMA.
    state.visited.clear()
    invoke(state,0x1001b38c,[target,source,len(pixels)],engine)
    assert 0x1001b38c in state.visited
    assert state.bytes_at(target,len(pixels)) == pixels
    expected = bytearray(first_before)
    expected[target-first:target-first+len(pixels)] = pixels
    assert state.bytes_at(first,39168) == expected
    assert state.bytes_at(second,65536) == second_before
    snapshot('software_pixels_copied')
    stop,visited = bounded(state,engine,0x100143b8,'supplied_fill_completion',
        lambda pc,read,reg:pc == 0x1001446b,
        cut=(0x100143b8,0x1001445d,{}))
    next_index = (index+1)&3
    assert 0x10014468 in visited and state.read(video+224,4) == next_index
    snapshot('fill_published')
    # A separately supplied nonfinal flag must retain the original one-slot
    # withholding condition. Restore the actual final flag before selection.
    state.write(desc+4,4,0)
    stop,visited = bounded(state,engine,0x10013f34,'nonfinal_collision_control',
        lambda pc,read,reg:pc in (0x10014014,0x100140f6,0x10013ff9),
        cut=(0x10013f34,0x10013f57,{11:video,5:desc,9:256}))
    assert stop == 0x100140f6 and 0x10014012 not in visited
    state.write(desc+4,4,1)
    stop,visited = bounded(state,engine,0x10013f34,'final_buffer_selection',
        lambda pc,read,reg:pc in (0x10014014,0x100140f6,0x10013ff9),
        cut=(0x10013f34,0x10013f57,{11:video,5:desc,9:256}))
    assert stop == 0x10014014 and 0x10014012 in visited
    selected = state.registers[12] if engine is None else engine.reg(((engine.reg(38)*4+12)%32)+1)
    assert selected == target and state.bytes_at(selected,len(pixels)) == pixels
    snapshot('final_buffer_selected')
    stop,visited = bounded(state,engine,0x10013f34,'supplied_output_acceptance',
        lambda pc,read,reg:pc == 0x100140e5,
        cut=(0x10013f34,0x100140c9,{7:video,5:desc}))
    assert 0x100140e2 in visited
    assert state.read(video+220,4) == next_index and state.read(video+212,4) == 0
    snapshot('output_accounted')
    stop,visited = bounded(state,engine,0x100144d0,'supplied_output_completion',
        lambda pc,read,reg:pc in (0x10014524,0x10014576),
        cut=(0x100144d0,0x1001451c,{10:video}))
    assert stop == 0x10014576 and {0x10014569,0x10014573}.issubset(visited)
    assert state.read(desc,4) == 0 and state.read(video+216,4) == next_index
    snapshot('descriptor_released')
    before = state.bytes_at(video,260)
    stop,visited = bounded(state,engine,0x10014244,'no_remaining_data_control',
        lambda pc,read,reg:pc in (0x10014290,0x1001429a))
    assert stop == 0x1001429a and state.bytes_at(video,260) == before
    assert 0x1001426e not in visited
    assert state.bytes_at(first,39168) == expected
    assert state.bytes_at(second,65536) == second_before
    assert state.bytes_at(source,len(pixels)) == pixels
    assert input_owner == (state.bytes_at(work,148),state.bytes_at(payload,104))
    assert state.blocks() == pool_before
    controls = reject_excluded(state,engine,EXCLUDED)
    return dict(status='pass',fill=fill,initial_index=index,final_index=next_index,
        index_origin='constructor zero' if index == 0 else 'explicit wrap fixture',
        preparation=preparation,stages=stages,selected_pointer=selected,
        image_rows=rows,image_bytes=len(pixels),image_sha256=core.sha(pixels),all_image_bytes_equal=True,
        only_selected_slot_changed=True,source_owners_and_pool_unchanged=True,
        occupied_guard_stop='0x1001429a',no_remaining_guard_stop='0x1001429a',
        nonfinal_collision_stop='0x100140f6',rejected_before_execution=controls,
        completed_page_lifecycles=0,hardware_transfers=0,
        supplied_boundaries=['decoder capture to raw input','software memcpy adapter',
            'fill completion','output acceptance','output completion'])


def sequence(program,engine,pixels,fill):
    """Five fills traverse a real four-slot ring under explicit backpressure.

    All indices start at the original constructor's zero and advance only in
    original instructions. The host supplies copies/completions and their order.
    """
    assert len(pixels) == 17*1200
    state,admission = raw.execute(program,engine,fill=fill,bitmap=0,page_bitmap=1,
        bih_chunk=True,width=9600,rows=17,image=pixels,
        state_class=raw.handoff.state_class(raw.Parser),return_state=True)
    preparation = raw.handoff.run(state,engine,admission)
    assert preparation['prepare_stride'] == 1200
    assert preparation['output_layout']['first_slot_bytes'] == 4800
    state.code_ranges += CODE
    video = state.read(0x10006770,4)
    descriptor_base = state.read(0x100067bc,4)
    assert descriptor_base == video+32
    assert [state.read(video+i,4) for i in (224,220,216)] == [0,0,0]
    assert state.read(video+192,4) == state.read(video+244,4) == 0
    assert state.read(video+252,4)&0x80000000 == 0
    assert state.read(video+204,4) == 4
    assert state.read(video+208,4) == state.read(video+212,4) == 17
    work,payload = admission['owner_hierarchy']['work'],admission['payload']
    source = admission['input_pointer']
    input_owner = state.bytes_at(work,148),state.bytes_at(payload,104)
    pool_before = state.blocks()
    first,second = [v['pointer'] for v in preparation['video_initialization']['allocations']]
    expected = bytearray(state.bytes_at(first,39168))
    second_before = state.bytes_at(second,65536)
    events,produced,selected,retired = [],[],[],[]
    copied = accepted = 0
    output = bytearray()

    def snapshot(phase,index=None,rows=None):
        events.append(dict(phase=phase,index=index,rows=rows,
            descriptors=[[state.read(descriptor_base+i*12+j*4,4) for j in range(3)] for i in range(4)],
            indices=[state.read(video+i,4) for i in (224,220,216)],
            remaining=[state.read(video+i,4) for i in (208,212)],
            first_buffer_sha256=core.sha(state.bytes_at(first,39168))))

    def unchanged_claim(phase):
        before = state.bytes_at(video,260)
        stop,visited = bounded(state,engine,0x10014244,phase,
            lambda pc,read,reg:pc in (0x10014290,0x1001429a))
        assert stop == 0x1001429a and 0x1001426e not in visited
        assert state.bytes_at(video,260) == before
        assert state.bytes_at(first,39168) == expected
        snapshot(phase)

    def produce():
        nonlocal copied
        index = state.read(video+224,4)
        desc = descriptor_base+index*12
        assert state.read(desc,4) == 0 and copied < len(pixels)
        stop,visited = bounded(state,engine,0x10014244,'sequence_claim',
            lambda pc,read,reg:pc in (0x10014290,0x1001429a))
        assert stop == 0x10014290 and 0x10014283 in visited
        rows = min(4,(len(pixels)-copied)//1200)
        final = int(copied+rows*1200 == len(pixels))
        assert [state.read(desc+i*4,4) for i in range(3)] == [1,final,rows]
        assert state.bytes_at(first,39168) == expected
        snapshot('claimed_before_pixels',index,rows)
        target = state.read(video+index*4,4)
        assert target == first+index*4800
        invoke(state,0x1001b38c,[target,source+copied,rows*1200],engine)
        expected[target-first:target-first+rows*1200] = pixels[copied:copied+rows*1200]
        assert state.bytes_at(first,39168) == expected
        assert state.bytes_at(second,65536) == second_before
        produced.append(dict(index=index,rows=rows,source_offset=copied,
            target=target,sha256=core.sha(state.bytes_at(target,rows*1200))))
        copied += rows*1200
        assert state.read(video+208,4) == (len(pixels)-copied)//1200
        stop,visited = bounded(state,engine,0x100143b8,'sequence_supplied_fill_completion',
            lambda pc,read,reg:pc == 0x1001446b,
            cut=(0x100143b8,0x1001445d,{}))
        assert 0x10014468 in visited and state.read(video+224,4) == (index+1)&3
        snapshot('fill_published',index,rows)

    def select(withheld=False):
        nonlocal accepted
        index = state.read(video+220,4)
        desc = descriptor_base+index*12
        assert state.read(desc,4) == 1
        before = state.bytes_at(video,260)
        stop,visited = bounded(state,engine,0x10013f34,'sequence_supplied_output_ready',
            lambda pc,read,reg:pc in (0x10014014,0x100140f6,0x10013ff9),
            cut=(0x10013f34,0x10013f57,{11:video,5:desc,9:256}))
        assert state.bytes_at(video,260) == before
        assert state.bytes_at(first,39168) == expected
        if withheld:
            assert stop == 0x100140f6 and 0x10014012 not in visited
            snapshot('nonfinal_withheld',index)
            return
        assert stop == 0x10014014 and 0x10014012 in visited
        pointer = state.registers[12] if engine is None else engine.reg(((engine.reg(38)*4+12)%32)+1)
        rows = state.read(desc+8,4)
        assert pointer == state.read(video+index*4,4) == first+index*4800
        band = state.bytes_at(pointer,rows*1200)
        assert band == pixels[accepted:accepted+len(band)]
        selected.append(dict(index=index,rows=rows,source_offset=accepted,
            pointer=pointer,sha256=core.sha(band)))
        output.extend(band)
        accepted += len(band)
        stop,visited = bounded(state,engine,0x10013f34,'sequence_supplied_output_acceptance',
            lambda pc,read,reg:pc == 0x100140e5,
            cut=(0x10013f34,0x100140c9,{7:video,5:desc}))
        assert 0x100140e2 in visited and state.read(video+220,4) == (index+1)&3
        assert state.read(video+212,4) == (len(pixels)-accepted)//1200
        assert state.read(desc,4) == 1  # Acceptance does not release ownership.
        snapshot('output_accounted_still_owned',index,rows)

    def retire():
        index = state.read(video+216,4)
        desc = descriptor_base+index*12
        assert state.read(desc,4) == 1
        assert len(retired) < len(selected) and selected[len(retired)]['index'] == index
        stop,visited = bounded(state,engine,0x100144d0,'sequence_supplied_output_completion',
            lambda pc,read,reg:pc in (0x10014524,0x10014576),
            cut=(0x100144d0,0x1001451c,{10:video}))
        assert stop == 0x10014576 and {0x10014569,0x10014573}.issubset(visited)
        assert state.read(desc,4) == 0 and state.read(video+216,4) == (index+1)&3
        retired.append(index)
        snapshot('descriptor_released',index)

    snapshot('prepared')
    produce()
    select(withheld=True)  # The actual first nonfinal band, not a changed flag.
    for _ in range(3):
        produce()
    assert [state.read(descriptor_base+i*12,4) for i in range(4)] == [1]*4
    unchanged_claim('full_ring_producer_blocked')
    select()
    unchanged_claim('accepted_without_completion_still_blocked')
    retire()
    produce()  # Real index wrap and reuse after the observed release.
    for _ in range(4):
        select()
        retire()
    unchanged_claim('no_remaining_data')
    assert [p['index'] for p in produced] == [p['index'] for p in selected] == retired == [0,1,2,3,0]
    assert [p['rows'] for p in produced] == [p['rows'] for p in selected] == [4,4,4,4,1]
    assert copied == accepted == len(pixels) and output == pixels
    assert [state.read(video+i,4) for i in (224,220,216)] == [1,1,1]
    assert [state.read(descriptor_base+i*12,4) for i in range(4)] == [0]*4
    assert state.read(video+208,4) == state.read(video+212,4) == 0
    assert state.bytes_at(first,39168) == expected
    assert state.bytes_at(second,65536) == second_before
    assert state.bytes_at(source,len(pixels)) == pixels
    assert input_owner == (state.bytes_at(work,148),state.bytes_at(payload,104))
    assert state.blocks() == pool_before
    controls = reject_excluded(state,engine,EXCLUDED)
    return dict(status='pass',fill=fill,preparation=preparation,events=events,
        produced=produced,selected=selected,retired=retired,
        image_rows=17,image_bytes=len(pixels),image_sha256=core.sha(pixels),
        output_sha256=core.sha(output),all_image_bytes_equal=True,
        whole_buffer_guards_equal=True,source_owners_and_pool_unchanged=True,
        final_indices=[1,1,1],final_remaining=[0,0],completed_page_lifecycles=0,
        buffer_transfers=5,hardware_transfers=0,rejected_before_execution=controls,
        index_origin='original constructor zero; only original code advances indices',
        supplied_boundaries=['decoder capture to raw input','software memcpy adapter with explicit source offsets',
            'fill completion','output ready and acceptance','output completion','host-selected interleaving'])


def main():
    tested_sources = raw.raw.source_hashes()
    baseline = json.loads((ROOT/'analysis/hardware-boundary/raw-parser.json').read_text())
    for name,digest in baseline['source_sha256'].items():
        assert core.sha((ROOT/name).read_bytes()) == digest,name
    image_report = json.loads((core.OUT/'validation.json').read_text())
    for name,digest in {**image_report['source_sha256'],**image_report['fixture_sha256']}.items():
        assert core.sha((ROOT/name).read_bytes()) == digest,name
    image_elf = core.OUT/'target/target-check.elf'
    assert core.sha(image_elf.read_bytes()) == image_report['target']['elf_sha256']
    image_program,_ = core.audit_target(image_elf)
    prefix = os.environ.get('XTENSA_PREFIX','/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf')
    program = Program(ROOT/'analysis/sihp1020.elf',prefix)
    assert core.sha(program.path.read_bytes()) == raw.STOCK_SHA
    memory,audited = Machine(program),[]
    for begin,end in CODE:
        pc,decoded = begin,bytearray()
        while pc < end:
            encoded = program.instruction(pc)[2]
            decoded.extend(encoded);pc += len(encoded)
        block,offset = memory.span(begin,end-begin,execute=True)
        assert pc == end and decoded == block[offset:offset+end-begin]
        audited.append(dict(begin=hex(begin),end=hex(end),bytes=decoded.hex(),sha256=core.sha(decoded)))
    bie_path = core.OUT/'fixtures/9600x132-stripe128-edges.jbg'
    bie = bie_path.read_bytes()
    with tempfile.TemporaryDirectory(prefix='hp1020-software-ring-',dir='/tmp') as directory:
        folder = Path(directory)
        full = ROOT/'vendor/foo2zjs-source'
        reference = folder/'reference'
        core.command(['clang','-std=c11','-O1','-fsanitize=address,undefined','-I'+str(full),
                      core.SRC/'reference.c',full/'jbig.c',full/'jbig_ar.c','-o',reference])
        core.command([reference,'decode',bie_path,folder/'pixels'])
        expected = (folder/'pixels').read_bytes()[:20400]
        assert expected == core.pattern(9600,132,'edges')[:20400]
        with QemuRAM() as engine:
            engine.load(image_elf)
            engine.put(image_program.symbols['hp1020_image_input'],bie)
            assert engine.call0(image_program.symbols['hp1020_image_run'],[len(bie),7,4,204]) == 2
            decoded = engine.read(image_program.symbols['hp1020_image_capture'],20400)
            assert decoded == expected and len(set(decoded)) > 1
            pixels = decoded[:4800]
            cases = []
            for fill in (0,204):
                for index in (0,3):
                    for rows in (1,4):
                        band = pixels[:rows*1200]
                        a = transfer(program,None,band,fill,index)
                        b = transfer(program,engine,band,fill,index)
                        assert a == b,(fill,index,rows,a,b)
                        b['engines'] = ['bounded_interpreter','independent_qemu']
                        cases.append(b)
                        print(f'decoded software ring fill={fill} index={index} rows={rows}: exact pixels, descriptor released',flush=True)
            sequences = []
            for fill in (0,204):
                a = sequence(program,None,decoded,fill)
                b = sequence(program,engine,decoded,fill)
                assert a == b,(fill,a,b)
                b['engines'] = ['bounded_interpreter','independent_qemu']
                sequences.append(b)
                print(f'decoded software ring sequence fill={fill}: five exact bands, stall, wrap and reuse',flush=True)
            version = engine.version
    assert raw.raw.source_hashes() == tested_sources,'research sources changed during execution'
    sources = {**tested_sources,**image_report['source_sha256']}
    findings = [
        'Eight bounded buffer-transfer cases use the current open decoder target output, compare every pixel with sanitized original full decoding, pass its first one or four 9600-bit rows through actual chunk-12 parser ownership and original video allocation/preparation, then copy to the real first-ring storage with original memcpy. The host bridge and software-copy caller are explicit, not a recovered original pipeline.',
        'The original descriptor prefix claims one or four rows while its slot still contains initialization bytes. The one-row final band leaves the rest of its four-row slot unchanged. Original occupied and zero-remaining controls skip all descriptor writes. An explicit copied-data completion enters the original RAM publication tail; the original callback-disabled band gate then selects the exact populated slot.',
        'Clearing the final flag as a separate control reaches the original one-slot withholding boundary; restoring the actual final flag permits selection. Original post-output RAM accounting and normal-mode retirement release that descriptor after explicitly supplied acceptance/completion. No raw source-pointer subtraction or reference decrement occurs.',
        'Both fills and initial indices zero/three agree in the interpreter and independent QEMU, including every pixel, pool partition, owners, output guards and final indices one/zero. Index three is supplied to exercise wrap arithmetic, not evidence of three preceding transfers. Only the selected first-ring slot changes; the second buffer and source allocation remain unchanged.',
        'Two additional 17-row sequences begin at constructor-zero indices and publish four actual nonfinal bands, fill all four slots, and stop the producer on a still-owned slot. Output acceptance alone does not free it. After explicitly supplied completion, original retirement releases it and original indices wrap for a one-row final band. Every selected byte concatenates to the original 17 rows. No ring index or final flag is patched in these sequences.',
        'The actual first nonfinal band is withheld before the second publication. Each continuous sequence delivers row counts 4,4,4,4,1 in slots 0,1,2,3,0. Unwritten bytes in the reused final slot retain the earlier band exactly; the whole first-buffer guard, second buffer, source ownership and pool remain unchanged apart from the intended copies. Readiness, source offsets, completion and scheduling order remain explicit host inputs.',
        'Thirteen excluded-code controls per case reject before execution. Compressed-image DMA, actual output writes, readiness/status reads, custom callbacks and automatic completion never run. Eight isolated transfers plus two five-transfer sequences are zero completed native page lifecycles and no physical output proof.'
    ]
    report = dict(status='pass',cases=cases,buffer_transfer_cases=8,completed_page_lifecycles=0,
        image=dict(bytes=4800,rows=4,stride=1200,sha256=core.sha(pixels),bie_sha256=core.sha(bie),
                   target_elf_sha256=core.sha(image_elf.read_bytes()),
                   scope='First one or four rows cropped from the existing 9600x132 fixture and declared as a short raw input'),
        bands={str(rows):dict(rows=rows,bytes=rows*1200,sha256=core.sha(pixels[:rows*1200])) for rows in (1,4)},
        sequences=sequences,sequence_cases=2,sequence_buffer_transfers=10,
        sequence_image=dict(rows=17,bytes=len(decoded),sha256=core.sha(decoded),
            scope='First 17 rows cropped from the existing 9600x132 fixture and declared as one raw input'),
        source_sha256=sources,stock_elf_sha256=raw.STOCK_SHA,qemu_version=version,
        raw_parser_report_sha256=core.sha((ROOT/'analysis/hardware-boundary/raw-parser.json').read_bytes()),
        audited_stock_ranges=audited,findings=findings)
    OUT.with_suffix('.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    OUT.with_suffix('.md').write_text('# Software-decoded pixels in original ring storage\n\n'
        +'8 isolated buffer transfers and 2 continuous five-transfer sequences agree between both engines. Zero completed page lifecycles.\n\n'
        +'\n'.join('- '+v for v in findings)+'\n')
    print('software ring: 8 isolated transfers and 2 five-transfer sequences, explicit completion boundaries; zero page lifecycles')


if __name__ == '__main__':
    main()
