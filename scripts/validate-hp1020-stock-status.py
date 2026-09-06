#!/usr/bin/env python3
"""Compare original engine decision instructions with the independent branch model.

Only the decision routine executes. Status-I/O, queue delivery, datastore mode
publication and video reset are intercepted at function boundaries. They never
execute, and every MMIO address remains forbidden in the underlying interpreter.
"""
import hashlib
import importlib.util
import itertools
import json
import os
from pathlib import Path
import random
import sys
from hp1020_xtensa_call0 import Program
from hp1020_xtensa_stock import StockMachine

ROOT=Path(__file__).resolve().parents[1]

def load_model():
    spec=importlib.util.spec_from_file_location('stock_status_reference',ROOT/'scripts/model-hp1020-engine-status-decisions.py')
    model=importlib.util.module_from_spec(spec);sys.modules[spec.name]=model;spec.loader.exec_module(model)
    return model

class StatusHarness(StockMachine):
    def __init__(self,program,inputs,flags=None):
        super().__init__(program,0x10015df8,[(0x10015df8,0x10016024)])
        self.inputs=inputs;self.commands=[];self.events=[];self.mode_updates=[];self.resets=[];self.branch_outcomes=set()
        self.state=self.read(0x10006920,4)
        self.write(self.state+0x60,4,inputs.previous_event)
        for offset,value in (flags or {}).items():self.write(self.state+offset,2 if offset==0x64 else 4,value)
    def extension(self,op,a,nxt):
        if op!='call8':return super().extension(op,a,nxt)
        target=a[0];args=self.registers[10:14];result=0
        if target==0x10015c68:
            command=args[0];self.commands.append(command)
            values={1:self.inputs.primary,0x20:self.inputs.status_20,2:self.inputs.status_2,
                    0x16:self.inputs.substatus_16,0x13:self.inputs.substatus_13,0x501a:0,0x5043:0}
            if command not in values:raise ValueError('unmodeled status I/O command')
            result=values[command]
        elif target==0x10013658:
            assert args[0]==1
            words=[self.read(args[1]+i*4,4) for i in range(4)]
            assert words[0]==0x17 and words[2:]==[0,0],words
            self.events.append(words[1])
        elif target==0x10015dd0:self.mode_updates.append(args[0])
        elif target==0x10013d4c:self.resets.append(args[0])
        else:raise ValueError(f'unmodeled status helper {target:#x}')
        self.registers[10]=result;self.branch_taken=True
        return nxt
    def after_instruction(self,pc,nxt):
        if self.program.instructions[pc][0].startswith('b'):
            self.branch_outcomes.add((pc,self.branch_taken))
        return super().after_instruction(pc,nxt)

def main():
    model=load_model();constants=model.load_literals(model.ENGINE_MODEL_JSON)
    program=Program(ROOT/'analysis/sihp1020.elf',os.environ.get('XTENSA_PREFIX','/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf'))
    count=0;steps=0;visited=set();branches=set();signatures=set();counterexamples=[]
    def check(inputs,flags=None):
        nonlocal count,steps
        m=StatusHarness(program,inputs,flags);m.run([int(inputs.force_emit)])
        expected=model.select_engine_event(inputs,constants)
        stored=inputs.previous_event if expected['stored_event'] is None else int(expected['stored_event'],16)
        events=[int(x,16) for x in expected['extra_emitted_events']]
        if expected['emits_queue_0x17']:events.append(stored)
        reads=[int(x,16) for x in expected['reads']]
        side=[int(x,16) for x in expected['side_effect_commands']]
        actual=(m.read(m.state+0x60,4),m.events,[x for x in m.commands if x<0x100],[x for x in m.commands if x>=0x100])
        wanted=(stored,events,reads,side)
        if actual!=wanted:
            counterexamples.append(dict(inputs=vars(inputs),actual=actual,expected=wanted))
            if len(counterexamples)>=10:raise AssertionError(counterexamples)
        if flags is not None:
            # Directly expressed state-transition contract, distinct from instruction execution.
            f={x:flags.get(x,0) for x in (0x2c,0x30,0x34,0x38,0x3c,0x64)};resets=[]
            mask=m.read(0x10006980,4)
            primary=inputs.primary
            if primary!=65535:
                if f[0x38] and not primary&mask and f[0x64]&mask:
                    f[0x38]=0;f[0x30]=1;resets=[0]
                if expected['ready_branch']:f[0x30]=1
                if f[0x2c] and not primary&0x2000:
                    if primary&0x80:f[0x3c]=1
                    f[0x30]=1;f[0x2c]=0
                if not primary&mask and f[0x3c]:f[0x3c]=0
                f[0x34]=int(bool(f[0x64]&mask));f[0x64]=primary
            actual_flags={offset:m.read(m.state+offset,2 if offset==0x64 else 4) for offset in f}
            assert actual_flags==f and m.resets==resets,(vars(inputs),flags,actual_flags,f,m.resets,resets)
        count+=1;steps+=m.steps;visited.update(m.visited)
        branches.update(m.branch_outcomes)
        signatures.add((stored,tuple(m.events),tuple(m.commands),tuple(m.mode_updates),tuple(m.resets)))
    scenarios=json.loads((ROOT/'analysis/hardware-boundary/engine-status-decisions.json').read_text())['scenarios']
    for scenario in scenarios:
        inp={k:int(v,16) if isinstance(v,str) else v for k,v in scenario['inputs'].items()}
        check(model.Inputs(**inp))
    for value in range(65536):
        check(model.Inputs(primary=0,status_2=value,substatus_16=0x40))
    for value in range(65536):
        check(model.Inputs(primary=0,status_2=0x40,substatus_16=value))
    for value in range(128):check(model.Inputs(primary=0,status_2=0x100,substatus_13=value))
    rng=random.Random(10200906)
    for _ in range(2048):
        check(model.Inputs(*(rng.randrange(65536) for _ in range(5)),previous_event=rng.choice((0,0x100,0xe6100800,0x14000a04,0xffffffff)),force_emit=bool(rng.getrandbits(1))))
    for primary in (0,0x40,0x80,0x2000,0x2080,0x4040,0xffff):
        for values in itertools.product((0,1),repeat=5):
            flags=dict(zip((0x2c,0x30,0x34,0x38,0x3c),values))
            for old_primary in (0,0x80,0xffff):
                check(model.Inputs(primary=primary),flags|{0x64:old_primary})
    assert not counterexamples,counterexamples
    instructions={pc:row for pc,row in program.instructions.items() if 0x10015df8<=pc<0x10016024}
    missing_instructions=set(instructions)-visited
    missing_branches={(pc,taken) for pc,row in instructions.items() if row[0].startswith('b') for taken in (False,True)}-branches
    assert not missing_instructions,sorted(missing_instructions)
    assert not missing_branches,sorted(missing_branches)
    report=dict(status='pass',cases=count,executed_instructions=steps,distinct_instructions=len(visited),
                distinct_observed_outcomes=len(signatures),counterexamples=counterexamples,
                all_instructions_covered=True,conditional_branch_outcomes=len(branches),all_branch_outcomes_covered=True,
                source_elf_sha256=hashlib.sha256((ROOT/'analysis/sihp1020.elf').read_bytes()).hexdigest(),
                executed_range=['0x10015df8','0x10016024'],
                boundaries={'0x10015c68':'supplied status values / captured command intents',
                            '0x10013658':'captured queue 0x17 event words',
                            '0x10015dd0':'captured datastore mode updates','0x10013d4c':'captured reset intent'},
                scope='Original decision code only; all MMIO forbidden. Exhaustive status_2 and substatus_16 axes are not exhaustive joint inputs or physical calibration.')
    out=ROOT/'analysis/hardware-boundary/stock-status-execution'
    out.with_suffix('.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    out.with_suffix('.md').write_text('# Original engine decision execution\n\nStatus: pass. '+f'{count:,} cases, {steps:,} instructions, {len(visited)} distinct instructions.\n\n'+report['scope']+'\n\n'
        'Compares stored event, event emissions, status-read order, command intents and state latches. Every instruction and both outcomes of every conditional branch are reached. Each 16-bit status_2 value and each 16-bit substatus_16 value is exercised in a fixed qualifying context; substatus_13, mixed random inputs, prior events and latch transitions add branch coverage.\n\n'
        'The original status-I/O, queue, datastore and reset helpers are intercepted, never executed. No engine/video/MMIO implementation is added to open firmware. Physical meanings and timing remain unknown.\n')
    print('stock status:',count,'cases',steps,'instructions',len(visited),'distinct')

if __name__=='__main__':main()
