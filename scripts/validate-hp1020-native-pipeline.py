#!/usr/bin/env python3
"""Original native lifecycle oracles and narrowly verified conditional null reads.

A reproduced guarded stop is reported separately from a completed lifecycle.
Unexpected stops and unexpectedly successful counterexamples fail this validator.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from hp1020_xtensa_call0 import Program,Machine
from hp1020_qemu_ram import QemuRAM
from hp1020_qemu_pipeline import run_pipeline,PipelineFault,P,J,S

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'analysis/open-firmware-model/stock-execution'
spec = importlib.util.spec_from_file_location('stock_helper',ROOT/'scripts/validate-hp1020-stock-execution.py')
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


def instruction_audit(program):
    expected = {
        0x1000e3db:('movi.n',(8,15),'c08f'),
        0x1000e3e1:('movi.n',(8,10),'c08a'),
        0x10010543:('movi.n',(8,15),'c08f'),
        0x10010549:('s32i.n',(6,1,8),'9612'),
        0x10010599:('l32r',(10,0x100063dc),'1ad790'),
        0x100105a1:('call8',(0x10010838,),'5800a5'),
        0x1000e44f:('l32i.n',(8,1,0),'8810'),
        0x1000e975:('l32i.n',(8,1,4),'8811'),
        0x1000e97d:('s32i.n',(8,2,0),'9820'),
        0x1000e9d2:('bnez',(9,0x1000e41d),'659a47'),
        0x1000e9d5:('movi.n',(8,37),'c285'),
        0x1000e9e1:('call8',(0x10013658,),'58131d'),
        0x1000e9e7:('l32r',(15,0x10006308),'1fde48'),
        0x1000e9ec:('beqz',(8,0x1000e41d),'648a2d'),
        0x1000e9ef:('l32r',(2,0x100062e4),'12de3d'),
        0x1000e9f2:('l32i.n',(8,2,0),'8820'),
        0x1000e9f4:('l32i',(8,8,12),'288203'),
        0x1001306b:('s32i.n',(8,2,0),'9820'),
    }
    memory = Machine(program)
    for pc,(op,args,raw) in expected.items():
        assert program.instruction(pc)==(op,args,bytes.fromhex(raw))
        span,offset = memory.span(pc,len(bytes.fromhex(raw)),execute=True)
        assert span[offset:offset+len(bytes.fromhex(raw))]==bytes.fromhex(raw)
    assert memory.read(0x100063dc,4)==0xe6101100
    # Both constructors pass priority/threshold 15 and time slice 10. StatusMgr
    # keeps 10 in a6; the wrapper forwards these stack arguments unchanged.
    assert program.instruction(0x10010537)[:2]==('movi.n',(6,10))
    for pc,op,args in ((0x1000e3dd,'s32i.n',(8,1,0)),
                       (0x1000e3df,'s32i.n',(8,1,4)),
                       (0x1000e3e3,'s32i.n',(8,1,8)),
                       (0x10010545,'s32i.n',(8,1,0)),
                       (0x10010547,'s32i.n',(8,1,4)),
                       (0x100182e8,'l32i.n',(8,1,56)),
                       (0x100182f8,'s32i.n',(8,1,8))):
        assert program.instruction(pc)[:2]==(op,args)
    return dict(instructions={hex(pc):dict(op=op,args=args,bytes=raw)
                for pc,(op,args,raw) in expected.items()},
                original_preflight_event='0xe6101100',job_status_priority=15,
                job_status_time_slice=10)


def verify_conditional_stop(detail,documents):
    assert detail['pc']=='0x1000e9f4' and detail['thread']==hex(J)
    assert detail['error']=='unmapped RAM 0xc+4'
    assert detail['head']=='0x0' and detail['cancel']==1
    assert detail['counters']==[11,10] and detail['queued_job_types']==[]
    assert detail['input_bytes_consumed']==documents*72
    assert detail['host_services']==['0x30000000']
    trace = detail['trace']
    sends = [r for r in trace if r['kind']=='send' and r['queue']==3]
    cancel, = [r for r in sends if r['raw_words'][:2]==[15,1]]
    ack, = [r for r in sends if r['raw_words'][0]==37]
    assert cancel['thread']==hex(S) and cancel['caller']=='0x10010a00'
    assert ack['thread']==hex(J) and ack['caller']=='0x1000e9e1'
    assert cancel['step']<ack['step'] and cancel['head']!='0x0'
    receives = [r for r in trace if r['kind']=='job_receive']
    index = next(i for i,r in enumerate(receives) if r['raw_words'][0]==15)
    tail = receives[index:]
    expected = [15,2]+[1,2]*(documents-11)+[37]
    assert [r['raw_words'][0] for r in tail]==expected
    assert tail[0]['queued_job_types']==expected[1:-1]
    assert ack['queued_job_types']==expected[1:-1]
    assert tail[-2]['queued_job_types']==[37] and tail[-2]['head']!='0x0'
    assert tail[-1]['head']=='0x0' and tail[-1]['cancel']==1
    pops = [r for r in trace if r['kind']=='list_pop' and r['cancel']==1]
    assert len(pops)==documents-10
    assert pops[-1]['next_head']=='0x0' and pops[-1]['queued_job_types']==[37]
    assert tail[-2]['step']<pops[-1]['step']<tail[-1]['step']
    preflight, = [r for r in trace if r['kind']=='status_publish' and r['args']==[0xe6101100,1]]
    assert preflight['step']<cancel['step']
    assert trace[-1]['kind']=='null_read' and trace[-1]['raw_words'][0]==37
    detail['status'] = 'reproduced_conditional_null_read'
    detail['job_receive_tail'] = expected
    detail['lifecycle_completed'] = False
    return detail


def main():
    program = Program(ROOT/'analysis/sihp1020.elf',os.environ.get('XTENSA_PREFIX','/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf'))
    audit = instruction_audit(program)
    base = helper.chunks((ROOT/'analysis/samples/generated/matrix-a4_default.zjs').read_bytes())[0]
    empty = helper.stream(base[:1]+base[-1:])
    assert len(empty)==72
    configurations = [(n,p,0) for n in (1,3,13)
                      for p in ((5,2,15),(2,5,15),(5,5,5),(5,2,1))]
    configurations += [(n,(5,5,5),0) for n in (10,11)]
    configurations += [(n,(15,15,15),10) for n in (10,11)]
    cases = []
    with QemuRAM() as q:
        for documents,priorities,time_slice in configurations:
            expected_stop = documents>=11 and len(set(priorities))==1
            for fill in (0,0xcc):
                try:
                    case = run_pipeline(q,program,empty*documents,documents,fill,priorities,time_slice)
                except PipelineFault as error:
                    if not expected_stop:
                        raise
                    case = verify_conditional_stop(error.detail,documents)
                else:
                    assert not expected_stop,'conditional null read unexpectedly disappeared'
                    if documents==13 and priorities==(2,5,15):
                        assert case['job_queue_full_waits']>0
                    if documents==13 and priorities[2]==15:
                        assert case['status_queue_full_waits']>0
                    trace = case.pop('trace')
                    case['trace_sha256'] = hashlib.sha256(json.dumps(trace,sort_keys=True).encode()).hexdigest()
                    case['job_receive_types'] = [r['raw_words'][0] for r in trace if r['kind']=='job_receive']
                    if documents==10 and len(set(priorities))==1:
                        cancel, = [r for r in trace if r['kind']=='job_receive' and r['raw_words'][0]==15]
                        assert cancel['head']=='0x0' and cancel['cancel']==0
                        assert not any(r['kind']=='self_ack' for r in trace)
                        case['cancellation_after_empty_list'] = True
                cases.append(case)
                print(f'pipeline {documents} documents, {priorities}, slice {time_slice}, fill {fill}: {case["status"]}',flush=True)
    completed = sum(c['status']=='pass' for c in cases)
    reproduced = sum(c['status']=='reproduced_conditional_null_read' for c in cases)
    assert (completed,reproduced)==(26,6)
    sources = ('validate-hp1020-native-pipeline.py','hp1020_qemu_pipeline.py','hp1020_qemu_multitask.py',
               'hp1020_qemu_scheduled_status.py','hp1020_qemu_timers.py','hp1020_stock_pool.py',
               'hp1020_stock_parser_harness.py','hp1020_stock_jobmgr_harness.py','hp1020_stock_lifecycle_harness.py',
               'hp1020_qemu_stock_parser.py','hp1020_qemu_ram.py')
    report = dict(status='pass',total_cases=len(cases),completed_lifecycles=completed,
        reproduced_conditional_stops=reproduced,cases=cases,instruction_audit=audit,
        elf_sha256=hashlib.sha256(program.path.read_bytes()).hexdigest(),
        source_sha256={name:hashlib.sha256((ROOT/'scripts'/name).read_bytes()).hexdigest() for name in sources},
        findings=[
            'Original parser, JobMgr and StatusMgr run concurrently with original allocation, queues, locks and scheduling. The host supplies input bytes only during execution; no replay, queue injection or heap migration is used.',
            'Twenty-six completed empty-document cases pass the unchanged document, pool partition, original free, lock, counter and queue-wait oracles. Only the persistent 20-byte ONLINE subscriber remains live. JobMgr has an original two-tick receive timeout armed; no ticks were delivered.',
            'Six conditional stops reproduce the original read through null at 0x1000e9f4. They are separate outcomes, not completed lifecycles. Original StatusMgr sends cancellation [15,1]; JobMgr receives it while END_DOC is queued, sends its own message 37 behind the queued input, removes the last document through the original list-pop store, then processes 37 with cancellation state 1 and head zero.',
            'Ten equal-priority documents finish before cancellation is consumed, so JobMgr sees an empty list and never arms cancellation or enqueues 37. Eleven and thirteen reach the guarded null read under the fixed wrapper/schedule; eleven is a local boundary, not a globally minimal reproducer.',
            'Both RAM fills agree despite different undefined packet suffixes. JobMgr/StatusMgr constructors specify priority 15 and time slice 10; using those values for all three fixture tasks preserves the ten/eleven boundary. With zero delivered ticks this checks a parameter omission, not physical time slicing.',
            'The original StatusMgr startup loads numeric event 0xe6101100 directly from stock literal 0x100063dc and publishes it before receiving notices. The cancellation producer and self-ack are original instructions. The observed ordering is therefore a conditional original-software hazard exposed by the fixture, not a host-injected cancellation or an observed device fault.'
        ],
        limits='Empty documents only. Parser context, datastore descriptors, repeated direct parser invocation, priorities, stacks and startup readiness are explicit fixtures. JobMgr/StatusMgr constructor thread creation is hosted before native task creation. The datastore constructor still stops before event-group/backing-value initialization. PrintMgr is absent and its ONLINE packet remains queued; no downstream cancellation request is sent in these empty-document traces. CPU interrupts and automatic time are disabled. Hardware reachability, actual boot, DMA, raster custom instructions, engine stopping, physical printing and recovery remain unproven. Raw trace words are observations; uninitialized suffixes of cancellation, acknowledgement and notice packets are not semantic arguments.')
    (OUT/'pipeline.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    (OUT/'pipeline.md').write_text('# Original parser, job and status task pipeline\n\n'
        +f'{completed} completed lifecycles and {reproduced} separately verified conditional null reads across {len(cases)} QEMU cases.\n\n'
        +'\n'.join('- '+x for x in report['findings'])+'\n\n'+report['limits']+'\n')
    print(f'Original native pipeline: {completed} lifecycles; {reproduced} conditional stops')


if __name__=='__main__':
    main()
