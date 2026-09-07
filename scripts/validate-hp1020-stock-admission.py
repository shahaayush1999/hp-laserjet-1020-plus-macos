#!/usr/bin/env python3
"""Check original document admission through buffered reads and job completion."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from hp1020_xtensa_call0 import Program
from hp1020_stock_admission_harness import AdmissionLifecycle, CooperativeAdmission, ADMISSION_CODE

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'analysis/open-firmware-model/stock-execution'
spec = importlib.util.spec_from_file_location('admission_inputs', ROOT / 'scripts/validate-hp1020-stock-execution.py')
inputs = importlib.util.module_from_spec(spec); spec.loader.exec_module(inputs)


def main():
    program = Program(ROOT / 'analysis/sihp1020.elf', os.environ.get('XTENSA_PREFIX','/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf'))
    raw = (ROOT / 'analysis/samples/generated/matrix-a4_default.zjs').read_bytes()
    parts = inputs.chunks(raw)[0]
    page = inputs.stream(parts)
    empty = inputs.stream(parts[:1]+parts[-1:])
    cases = []; counterexamples = []; visited = set(); steps = 0

    def account(machine):
        nonlocal steps
        steps += machine.steps + machine.retirement_steps
        visited.update(machine.visited | machine.retirement_visited)

    def check(name, data, documents, impressions, fragment=1024, batch=None, policy='eager'):
        cls = AdmissionLifecycle if batch is None else CooperativeAdmission
        kw = {} if batch is None else dict(batch=batch,completion_policy=policy)
        m = cls(program,data,probe_fragment=fragment,credits=2,**kw).replay()
        assert m.input_pos == len(data) and len(m.parser_entries) == documents, (name,m.parser_entries)
        assert len(m.scheduled) == len(m.completed) == impressions
        assert m.scheduled == m.completed
        assert len([x for x in m.messages if x['words'][0] == 1]) == documents
        assert len([x for x in m.messages if x['words'][0] == 2]) == documents
        notices = [x for x in m.notifications if x['words'][0] == 47]
        assert len(notices) == documents
        doc_list = m.read(0x100062e4,4)
        assert m.read(doc_list,4) == m.read(doc_list+4,4) == 0
        assert m.read(m.read(0x100062e8,4),2) == 2
        # Persistent transport owns its input buffer; notification receiver owns
        # 16 bytes per document. No other parser/job allocation survives.
        live = {p for p,a in m.allocations.items() if not a['freed']}
        expected = {m.read(m.transport+28,4)} | {x['words'][3] for x in notices}
        assert live == expected, (name,live,expected)
        assert m.read(m.transport+36,4) == 0
        assert all(x['callsite']=='0x10007ed5' and x['context']==hex(m.transport) for x in m.parser_entries)
        assert 0x10012644 not in m.visited  # separate draining wrapper never entered
        account(m)
        cases.append(dict(name=name,status='pass',documents=documents,impressions=impressions,
                          probe_fragment=fragment,schedule='serialized' if batch is None else policy,batch=batch,
                          parser_entries=m.parser_entries,instructions=m.steps,
                          input_sha256=hashlib.sha256(data).hexdigest()))

    for fragment in (1,2,3,4,7,31,1023,1024):
        for prefix in (b'',b'noise JZJX junk\x00',b'\x1b%-12345X@PJL ENTER LANGUAGE=ZJS\n'):
            # ZjStream is the only registered language in this fixture; prefixes
            # exercise recognizer scanning, not the separate PJL parser.
            check(f'scan/fragment={fragment}/prefix={len(prefix)}',prefix+page,1,1,fragment)
        check(f'two-documents/fragment={fragment}',page+b'noise\x00'+page,2,2,fragment)
        check(f'empty-pair/fragment={fragment}',empty+empty,2,0,fragment)
    for batch in (1,2,7,32):
        for policy in ('eager','after_document','after_parser'):
            for fragment in (1,7,1024):
                check(f'cooperative/batch={batch}/{policy}/fragment={fragment}',page+page,2,2,fragment,batch,policy)
    for fragment in (1,7,1024):
        check(f'empty-after-page/eager/{fragment}',page+empty,2,1,fragment,1,'eager')
    # The recognizer, dispatch callback, buffering and parser lock wrapper now
    # execute without substituting manual parser reinvocation between documents.
    for fragment in (1,3,7,1024):
        for cls,extra in ((AdmissionLifecycle,{}),(CooperativeAdmission,dict(batch=1,completion_policy='after_parser'))):
            m = cls(program,page+empty,probe_fragment=fragment,credits=1,**extra)
            try:
                m.replay()
            except ValueError as error:
                assert m.pc == 0x1000e7dd and str(error) == 'unmapped RAM 0x4c+4', (hex(m.pc),str(error))
                docs = [x['words'][3] for x in m.messages if x['words'][0] == 1]
                assert len(m.parser_entries) == len(docs) == 2
                assert m.allocations[docs[0]]['freed'] and not m.allocations[docs[1]]['freed']
                assert m.input_pos == len(m.input)
                account(m)
                counterexamples.append(dict(schedule='cooperative_after_parser' if extra else 'serialized',
                    probe_fragment=fragment,parser_entries=m.parser_entries,pc=hex(m.pc),error=str(error),
                    input_sha256=hashlib.sha256(m.input).hexdigest()))
            else:
                raise AssertionError('expected conditional lifecycle failure did not reproduce')
    report = dict(status='pass',cases=cases,counterexamples=counterexamples,total_cases=len(cases),
        reproduced_counterexamples=len(counterexamples),executed_instructions=steps,distinct_instructions=len(visited),
        new_code_ranges=[[hex(a),hex(b)] for a,b in ADMISSION_CODE],
        finding='The original single-language stream recognizer admits consecutive ZjStream documents without waiting for JobMgr list drain. Non-head empty-document cleanup still frees the unfinished head under serialized and delayed-completion cooperative host schedules. Eager completion avoids the fault.',
        scope='Original ZjStream registration, language matching, parser dispatch, input-buffer construction, pushback, buffered read, parser mutex wrappers, parser, JobMgr and completion bookkeeping execute unchanged in host RAM.',
        assumptions=['One transport and one registered language (ZjStream); other language handlers are not modeled.',
                     'Host readiness bit and low-level read callback deliver the supplied bytes. Nonblocking probe reads are fragmented; timed reads supply requested available bytes. No elapsed-time, timeout, disconnect or USB controller simulation.',
                     'RTOS setup, allocation, locks and queues retain prior host substitutes. Successful FIFO raster consumption and completion ordering are injected.',
                     'This reduces the unresolved software admission question. Actual host USB delivery, RTOS/IRQ scheduling, engine backpressure and physical occurrence remain unverified. It is not a demonstrated printer bug.'],
        stock_elf_sha256=hashlib.sha256((ROOT/'analysis/sihp1020.elf').read_bytes()).hexdigest(),
        source_sha256={name:hashlib.sha256((ROOT/'scripts'/name).read_bytes()).hexdigest() for name in (
            'hp1020_stock_admission_harness.py','validate-hp1020-stock-admission.py','hp1020_stock_lifecycle_harness.py',
            'hp1020_stock_jobmgr_harness.py','hp1020_stock_parser_harness.py','hp1020_xtensa_stock.py','hp1020_xtensa_call0.py')})
    (OUT/'admission.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    (OUT/'admission.md').write_text('# Original stream admission execution\n\n'
        +f"Status: pass. {len(cases)} normal cases and {len(counterexamples)} reproduced conditional counterexamples.\n\n"
        +report['finding']+'\n\n'+report['scope']+'\n\n## Explicit limits\n\n'
        +'\n'.join('- '+x for x in report['assumptions'])+'\n')
    print(f'stock admission: {len(cases)} cases, {len(counterexamples)} conditional counterexamples, {steps} original instructions')


if __name__ == '__main__':
    main()
