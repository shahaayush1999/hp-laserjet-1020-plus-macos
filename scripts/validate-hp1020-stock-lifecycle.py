#!/usr/bin/env python3
"""Check original lifecycle against input counts, ownership and credit invariants."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import struct
from hp1020_xtensa_call0 import Program
from hp1020_stock_lifecycle_harness import LifecycleHarness, CooperativeLifecycle, RetireBlock, LIFECYCLE_CODE

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'analysis/open-firmware-model/stock-execution/lifecycle'
spec=importlib.util.spec_from_file_location('job_check',ROOT/'scripts/validate-hp1020-stock-jobmgr.py')
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)


def main():
    program=Program(ROOT/'analysis/sihp1020.elf',os.environ.get('XTENSA_PREFIX','/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf'))
    base=helper.chunks((ROOT/'analysis/samples/generated/matrix-a4_default.zjs').read_bytes())[0]
    cases=[];steps=0;visited=set();retirement_steps=0
    def check(name,documents,credits=20,duplex=0,fill=0xcc,batch=None,completion_policy='eager'):
        nonlocal steps,retirement_steps
        factory=LifecycleHarness if batch is None else CooperativeLifecycle
        scheduling={} if batch is None else dict(batch=batch,completion_policy=completion_policy)
        m=factory(program,b''.join(documents),credits=credits,duplex=duplex,fill=fill,**scheduling).replay()
        assert m.input_pos==len(m.input) and m.delivered==len(m.pending)
        pages=[msg['words'][3] for msg in m.messages if msg['words'][0]==5]
        copies=[struct.unpack_from('>H',bytes.fromhex(msg['payload']),12)[0] for msg in m.messages if msg['words'][0]==5]
        expected=[work for work,count in zip(pages,copies) for _ in range(count)]
        assert m.scheduled==m.completed==expected,(name,'completion order')
        doc_list=m.read(0x100062e4,4)
        assert m.read(doc_list,4)==m.read(doc_list+4,4)==0,(name,'document list not empty')
        assert m.read(m.read(0x100062e8,4),2)==credits,(name,'credits not restored')
        assert m.critical_depth==0
        freed=next(p for p,a in m.allocations.items() if a['freed'])
        try:m.read(freed,4)
        except ValueError as error:assert 'unmapped RAM' in str(error)
        else:raise AssertionError('freed allocation remains readable')
        notices=[x for x in m.notifications if x['words'][0]==47]
        assert len(notices)==len(documents)
        doc_copies=[]
        for data in documents:
            total=0
            for kind,payload,_,_ in helper.chunks(data)[0]:
                if kind==2:
                    items=[payload[i:i+12] for i in range(0,len(payload),12)]
                    total+=next((int.from_bytes(x[8:12],'big')&65535 for x in items if x[4:6]==b'\0\4'),1)
            doc_copies.append(total)
        assert [int.from_bytes(bytes.fromhex(x['payload'])[12:14],'big') for x in notices]==doc_copies
        # Queue 10 has not consumed these notification payloads. They are the
        # only live allocations; every original page/document/raster is released.
        owned={n['words'][3] for n in notices}
        live={p for p,a in m.allocations.items() if not a['freed']}
        assert live==owned and all(m.allocations[p]['size']==16 for p in owned),(name,'unexpected surviving allocation')
        for msg in m.messages:
            if msg['words'][0] in (1,3,5,41,42):assert m.allocations[msg['words'][3]]['freed']
        # Original datastore code counts completed impressions in record 6.
        table=m.read(0x1000647c,4)
        count=m.read(m.read(table+6*24+4,4),4)
        assert count==sum(copies),(name,'datastore completion count',count,sum(copies))
        steps+=m.steps;retirement_steps+=m.retirement_steps
        visited.update(m.visited|m.retirement_visited)
        cases.append(dict(name=name,status='pass',documents=len(documents),pages=len(pages),completed=sum(copies),
                          initial_and_final_credits=credits,duplex_fixture=duplex,fill=fill,
                          notification_owned_bytes=len(owned)*16,stock_instructions=m.steps,
                          schedule='serialized' if batch is None else completion_policy,batch=batch,context_switches=getattr(m,'switches',0),
                          retirement_instructions=m.retirement_steps,input_sha256=hashlib.sha256(m.input).hexdigest()))
    def document(pages,copies,pieces):
        parts=helper.edit_items(base,{4:copies})
        kind,payload,_,_=parts[3];cuts=[len(payload)*i//pieces for i in range(pieces+1)]
        page=parts[1:3]+[(kind,payload[cuts[i]:cuts[i+1]],0,0) for i in range(pieces)]+parts[4:6]
        return helper.stream(parts[:1]+page*pages+parts[6:])
    for pages in (1,2,8,16):
        for copies in (1,3,21):
            for credits in (1,2,5,20):
                check(f'pages={pages}/copies={copies}/credits={credits}',[document(pages,copies,1)],credits)
    for pieces in (2,5,6,11,64):
        for duplex in (0,1):
            for fill in (0,0xcc):check(f'chunks={pieces}/duplex={duplex}/fill={fill}',[document(2,3,pieces)],credits=2,duplex=duplex,fill=fill)
    for count in (2,3,8):
        for credits in (1,5,20):
            docs=[document(1+i%3,1+i%4,1+i%7) for i in range(count)]
            check(f'documents={count}/credits={credits}',docs,credits)
    empty=helper.stream(base[:1]+base[6:])
    for docs in ([empty],[empty,empty]):
        check(f'empty-and-mixed/{len(docs)}',docs,credits=1)
    for batch in (1,2,7,32,128):
        for policy in ('eager','after_document','after_parser'):
            for duplex in (0,1):
                docs=[document(2,3,6),document(3,2,11)]
                check(f'cooperative/batch={batch}/{policy}/duplex={duplex}',docs,credits=2,duplex=duplex,batch=batch,completion_policy=policy)
    # Conditional stock counterexample: empty non-head document finalization
    # frees the global head, leaving its later page-completion message unmatched.
    witness=[document(1,1,1),empty]
    check('empty-after-page/eager',witness,credits=1,batch=1)
    counterexamples=[]
    for factory,extra in [(LifecycleHarness,{}),(CooperativeLifecycle,dict(batch=1,completion_policy='after_parser'))]:
        m=factory(program,b''.join(witness),credits=1,**extra)
        try:m.replay()
        except ValueError as error:
            assert m.pc==0x1000e7dd and str(error)=='unmapped RAM 0x4c+4',(hex(m.pc),str(error))
            docs=[x['words'][3] for x in m.messages if x['words'][0]==1]
            assert len(docs)==2 and m.allocations[docs[0]]['freed'] and not m.allocations[docs[1]]['freed']
            counterexamples.append(dict(schedule='serialized' if not extra else 'cooperative_after_parser',
                pc=hex(m.pc),error=str(error),first_document_freed=True,empty_document_still_allocated=True,
                input_sha256=hashlib.sha256(m.input).hexdigest(),
                explanation='Empty-document finalizer receives the tail document but frees the global head. A later FIFO page completion cannot find its child in the remaining head.'))
        else:raise AssertionError('empty queued behind unfinished page no longer reproduces; investigate changed semantics')
        steps+=m.steps;retirement_steps+=m.retirement_steps;visited.update(m.visited|m.retirement_visited)
    # Both contexts share heap/data but must never access the other's stack.
    stack_check=CooperativeLifecycle(program,empty)
    try:stack_check.read(0x21000000,4)
    except ValueError as error:assert str(error)=='cross-thread stack access'
    else:raise AssertionError('parser could read JobMgr stack')
    # Entire selected RAM block, including the progress gate, slot clearing and
    # exact decrement semantics. These inputs are deliberately synthetic.
    fragment_checks=[]
    owner=LifecycleHarness(program,document(1,1,1))
    nodes=[0x22000400+i*0x80 for i in range(5)]
    for node in nodes:owner.write(node+12,4,node+16)
    video=owner.read(0x10006770,4)
    for slots in range(6):
        for progress in (0,1,0xffffffff):
            for refs in (0,1,2,65535):
                for node in nodes:owner.write(node+16+0x4e,2,refs)
                block=RetireBlock(owner,nodes[:slots],progress);block.run()
                expected=(refs-1)&65535 if progress else refs
                assert [owner.read(n+16+0x4e,2) for n in nodes[:slots]]==[expected]*slots
                assert [owner.read(video+0xa4+i*4,4) for i in range(5)]==([0]*5 if progress else nodes[:slots]+[0]*(5-slots))
                assert len(block.events)==(slots if progress else 0)
                fragment_checks.append(dict(slots=slots,progress=progress,initial_refs=refs,final_refs=expected,status='pass'))
                retirement_steps+=block.steps;visited.update(block.visited)
    report=dict(status='pass',scope='Original software lifecycle in serialized/cooperative schedules under injected ordered successful completion; no device or printing evidence.',
        stock_sha256=hashlib.sha256((ROOT/'analysis/sihp1020.elf').read_bytes()).hexdigest(),
        implementation_sha256={p:hashlib.sha256((ROOT/'scripts'/p).read_bytes()).hexdigest() for p in ('hp1020_xtensa_call0.py','hp1020_xtensa_stock.py','hp1020_stock_parser_harness.py','hp1020_stock_jobmgr_harness.py','hp1020_stock_lifecycle_harness.py')},
        cases=cases,case_count=len(cases),counterexamples=counterexamples,fragment_checks=fragment_checks,fragment_case_count=len(fragment_checks),
        stock_instructions=steps,retirement_instructions=retirement_steps,distinct_instructions=len(visited),
        additional_code_ranges=[[hex(a),hex(b)] for a,b in LIFECYCLE_CODE],
        retirement_block=['0x10014319','0x10014342'],
        findings=['Original completion handling restores scheduling credits and drains jobs larger than the initial queue capacity.',
                  'Cooperative queue-boundary schedules interleave parser and JobMgr contexts with eager, end-document and end-parser FIFO completions. Nonempty documents preserve final ownership/counts; standalone empty documents finalize. A delayed mixed empty/nonempty sequence is recorded separately as a counterexample.',
                  'Multiple documents, copies and split rasters finish in FIFO order, leaving only queue-10-owned completion notices allocated.',
                  'Original publication/finalization, parser lock/unlock wrappers and datastore counter instructions now run; these were previously host substitutes or untested.',
                  'The parser lock wrapper only acquires its producer mutex; it does not wait for the JobMgr document list to drain. The separate 0x10012644 helper contains that drain wait and is not the parser call target.',
                  'The channel-A RAM block retires five saved pointers only when video +0xf8 is nonzero, clearing each pointer and decrementing payload +0x4e.',
                  'The retirement decrement has no zero guard: synthetic zero references wrap to 65535. Valid pipeline cases never require that state.',
                  'An empty document queued behind an unfinished nonempty document triggers incorrect head-document release in two schedules, followed by a missing-child access at 0x1000e7dd. Eager completion of the earlier page avoids it; physical reachability is unproven.'],
        boundaries=['The host injects one successful JobMgr message 17 for each queued work request, in FIFO order, after simulated consumption of its rasters.',
                    'The host batches consumed nodes into five saved-pointer slots and sets the progress flag, then executes only the original RAM retirement block. Its preceding/following MMIO is never executed.',
                    'Allocation/free, task-ready, mutex/semaphore/event operations and queue delivery remain host services; queue 10 notices are captured but not consumed.',
                    'Datastore records 5/6 have explicit zeroed word storage, and subscriber lists for 5/6/27/28 are empty. All selected datastore read/write logic executes.',
                    'Three exact critical-section instructions in the release loop use a serialized fixture substitute; no general interrupt model is claimed.'],
        limitations=['This harness manually re-invokes the parser between documents. Separate admission.json now reproduces the counterexample through original single-language recognition/buffering/dispatch; actual USB delivery and external completion timing remain unverified.',
                     'Only queue-boundary cooperative interleavings are exercised; instruction-level preemption, allocation failure, cancellation, out-of-order completions, reset/power cycle and physical consumption remain unverified.',
                     'Duplex cases exercise stock bookkeeping only; the replacement remains narrow simplex.',
                     'Completion injection is an assumption to verify software lifetime, not a claim that the open replacement can produce that event.'])
    OUT.with_suffix('.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    OUT.with_suffix('.md').write_text('\n'.join(['# Original software lifecycle','',report['scope'],'',
        f'{len(cases)} passing lifecycle cases, {len(counterexamples)} reproduced conditional counterexamples and {len(fragment_checks)} retirement-block cases; {steps+retirement_steps} original instructions, {len(visited)} distinct addresses.','',
        *['- '+x for x in report['findings']],'','## Explicit environment','',*['- '+x for x in report['boundaries']],'','## Limits','',*['- '+x for x in report['limitations']],'']))
    print(f'stock lifecycle: {len(cases)} cases, {len(fragment_checks)} retirement cases, {steps+retirement_steps} instructions')

if __name__=='__main__':main()
