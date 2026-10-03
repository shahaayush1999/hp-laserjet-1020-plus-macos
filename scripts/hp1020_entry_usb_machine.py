"""Draft owned entry/USB-lifetime interpreter policy; RAM only, unexecuted.

The accepted entry model and standard ISA engine stay unchanged. Reuse only
CPU normalization, snapshot and trace lifetime helpers; split RAM permissions
and six phase-dependent function-entry stops are local to this profile.
"""
from pathlib import Path
import gzip
import hashlib
import struct
from hp1020_xtensa_call0 import Machine, STOP, MASK
from hp1020_entry_machine import EntryMachine, require, contains, SPECIAL, NORMALIZED

ENTRY=0x100167a8

class EntryUSBMachine(EntryMachine):
    def __init__(self,program,regions,initial,checkpoints,trace_dir,observe):
        Machine.__init__(self,program)
        # Replace, rather than supplement, the shared per-call synthetic stack.
        self.segments=[(a,bytearray(raw),7) for a,raw in regions]
        require(len({a for a,_,_ in self.segments})==len(self.segments),'unique initial regions')
        ordered=sorted((a,a+len(raw)) for a,raw,_ in self.segments)
        require(all(a[1]<=b[0] for a,b in zip(ordered,ordered[1:])),'initial regions overlap')
        self.initial_regions=[(a,bytes(raw)) for a,raw in regions]
        self.zero_spans=tuple(program.entry_zero_spans)
        self.stack=tuple(program.entry_stack)
        self.data_span=tuple(program.entry_data_span)
        require(len(self.zero_spans)==4 and self.stack==(0x10014020,8192),
                'exact split four-span zero layout and owned stack')
        require(all(n>0 and not(a&3) and not(n&3) for a,n in self.zero_spans),
                'nonempty word-aligned actual zero spans')
        self.writable=self.zero_spans+(self.stack,self.data_span)
        self.write_ranges=[(a,a+n) for a,n in self.writable]
        require(self.write_ranges==list(program.write_ranges),'audit/machine exact write policy')
        # Program supplied by the complete linked audit exposes only admitted
        # actual allocated read objects; entire main-envelope gaps stay absent.
        self.read_spans=list(program.entry_read_spans)
        require(len(initial['physical_ar'])==32 and len(set(initial['physical_ar']))==32,
                'all32 distinct initial physical ARs')
        require(initial['pc']==ENTRY==program.entry,'one original-address entry')
        require(not(initial['ps']&0xe0),'privileged initial PS with UM/RING clear')
        require(0<=initial['windowbase']<8 and initial['windowstart']&(1<<initial['windowbase']),
                'admissible selected initial window')
        self.physical=list(initial['physical_ar'])
        self.special={n:initial[n] for n in SPECIAL}
        self.windowbase=initial['windowbase'];self.pending_windowbase=None
        self.registers[:]=[self.physical[(self.windowbase*4+i)%32] for i in range(16)]
        self.sar=initial['sar'];self.pc=ENTRY
        self.checkpoints=dict(checkpoints);self.checkpoint_order=[n for n,_ in checkpoints]
        require(self.checkpoint_order==['after-normalization','pre-c','pre-close','pre-final-service','pre-finish','park'],
                'exact ordered checkpoints')
        require(len(set(self.checkpoints.values()))==6,'distinct checkpoint addresses')
        require(self.checkpoints['after-normalization']==program.symbols['hp1020_entry_after_normalization'] and
                self.checkpoints['pre-c']==program.symbols['hp1020_entry_before_c'] and
                self.checkpoints['pre-close']==program.symbols['hp1020_tusb_adapter_close_input'] and
                self.checkpoints['pre-final-service']==program.symbols['hp1020_udc_publish_service'] and
                self.checkpoints['pre-finish']==program.symbols['hp1020_tusb_adapter_finish'] and
                self.checkpoints['park']==program.symbols['hp1020_entry_park'],'linked checkpoint binding')
        require(not(initial['lcount'] and any(a<=initial['lend']<=b for a,b in (
            (program.symbols['hp1020_entry_normalize'],self.checkpoints['after-normalization']),
            (ENTRY,ENTRY+3)))),'incoming loop cannot intercept initial normalization')
        self.observe=observe;self.seen=[];self.normalized=False;self.c_started=False
        self.minimum_sp=self.stack[0]+self.stack[1];self.minimum_stack_access=None
        self.entry_events=[]
        self.close_entries=0;self.finish_entries=0
        self.entry_names={program.symbols[n]:n for n in (
            'hp1020_usb_runtime_c','hp1020_usb_document_init','hp1020_usb_document_init_documents',
            'hp1020_tusb_adapter_init','hp1020_udc_setup_bus_reset','hp1020_udc_setup_offer',
            'hp1020_udc_setup_dispatch','hp1020_udc_ep0_take_submission','hp1020_udc_ep0_observe',
            'hp1020_tusb_adapter_pending_reset','hp1020_tusb_adapter_ack_reset',
            'hp1020_tusb_adapter_finish_reset','hp1020_tusb_adapter_pump',
            'hp1020_usb_document_restart','tusb_rhport_init','hp1020_udc_publish_arm_out',
            'hp1020_udc_acquire_packet','hp1020_udc_publish_service',
            'hp1020_tusb_adapter_close_input','hp1020_tusb_adapter_finish')}
        self.calls=[];self.call_stack=[];self.special_writes=[]
        self.park_steps=0;self.park_registers=None;self.park_effect_counts=None
        self.access_count={'read':0,'write':0};self.access_widths={}
        self.access_digest=hashlib.sha256();self.step_digest=hashlib.sha256()
        self.allowed_write_spans=()
        self.trace_dir=Path(trace_dir);self.trace_dir.mkdir(parents=True,exist_ok=False)
        self.access_file=(self.trace_dir/'accesses.bin.gz').open('wb')
        self.step_file=(self.trace_dir/'steps.bin.gz').open('wb')
        self.access_trace=gzip.GzipFile(fileobj=self.access_file,mode='wb',mtime=0)
        self.step_trace=gzip.GzipFile(fileobj=self.step_file,mode='wb',mtime=0)
        self.closed=False

    def record_access(self,kind,address,size,value):
        raw=struct.pack('>B3xIIII',1 if kind=='read' else 2,self.pc,address,size,value&MASK)
        self.access_trace.write(raw);self.access_digest.update(raw)
        self.access_count[kind]+=1
        key=f'{kind}/{size}';self.access_widths[key]=self.access_widths.get(key,0)+1
        if self.stack[0]<=address<self.stack[0]+self.stack[1]:
            require(self.c_started,'stack access before C CALL0')
            self.minimum_stack_access=address if self.minimum_stack_access is None else min(self.minimum_stack_access,address)

    def read(self,address,size):
        require(contains(self.read_spans,address,size),f'forbidden data read {address:#x}+{size} at{self.pc:#x}')
        require(not(self.stack[0]<=address<self.stack[0]+self.stack[1]) or self.c_started,
                'stack read before C CALL0')
        # Both alignment and complete backing-span checks precede the read.
        result=Machine.read(self,address,size)
        self.record_access('read',address,size,result)
        return result

    def write(self,address,size,value):
        require(contains(self.allowed_write_spans,address,size),
                f'forbidden phase store {address:#x}+{size} at{self.pc:#x}')
        require(not(self.stack[0]<=address<self.stack[0]+self.stack[1]) or self.c_started,'stack store before C CALL0')
        # Base implementation checks full width/alignment before changing RAM.
        Machine.write(self,address,size,value)
        self.record_access('write',address,size,value)

    def after_instruction(self,pc,next_pc):
        raw=struct.pack('>I',pc);self.step_trace.write(raw);self.step_digest.update(raw)
        op,args,encoded=self.program.instructions[pc]
        base=op.removesuffix('.n')
        if self.special['lcount'] and next_pc==self.special['lend']:
            raise ValueError('inadmissible incoming active loop intercepted normalization')
        if base in ('call0','callx0'):
            require(self.normalized,'call before own CPU/stack initialization')
            sp=self.registers[1]
            require(self.stack[0]<=sp<=self.stack[0]+self.stack[1] and not(sp&15),'call SP outside owned aligned stack')
            require(next_pc in self.program.entry_function_starts,
                    'call target outside audited original function entries')
            if not self.c_started:
                require(pc==self.checkpoints['pre-c'] and next_pc==self.program.symbols['hp1020_usb_runtime_c'],
                        'first C call is exact workload entry')
                require(self.seen==['after-normalization','pre-c'],'first call follows complete BSS witness')
                self.c_started=True;self.allowed_write_spans=self.writable
            event=dict(kind='call',pc=pc,target=next_pc,sp=sp,return_pc=pc+len(encoded),depth=len(self.call_stack)+1)
            self.calls.append(event);self.call_stack.append(event)
        elif base=='ret':
            require(self.call_stack,'return without a recorded own call')
            caller=self.call_stack[-1]
            require(next_pc==caller['return_pc'] and self.registers[1]==caller['sp'],
                    'return target/stack differs from own recorded caller')
            self.calls.append(dict(kind='return',pc=pc,target=next_pc,sp=self.registers[1],depth=len(self.call_stack)))
            self.call_stack.pop()
        if self.normalized:
            sp=self.registers[1]
            require(self.stack[0]<=sp<=self.stack[0]+self.stack[1],'SP escaped owned stack')
            self.minimum_sp=min(self.minimum_sp,sp)
        if pc==self.checkpoints['park']:
            require(self.seen==self.checkpoint_order and base=='j' and args==(pc,) and next_pc==pc,
                    'only terminal self-branch may execute after park')
            require(self.registers_at(pc)==self.park_registers and
                    (self.access_count,len(self.calls))==self.park_effect_counts,
                    'terminal park changed registers or performed an access/call')
            self.park_steps+=1
            return STOP if self.park_steps==2 else next_pc
        # Record genuine entry transitions, including compiler tail branches.
        # Ordinary service calls before close are legitimate; the next-service
        # checkpoint becomes active only after the first actual close entry.
        if next_pc in self.entry_names:
            name=self.entry_names[next_pc]
            self.entry_events.append(dict(name=name,pc=pc,target=next_pc,
                instruction=self.steps,sp=self.registers[1],arguments=self.registers[2:8].copy()))
            if name=='hp1020_tusb_adapter_close_input':
                self.close_entries+=1
                require(self.close_entries==1 and self.finish_entries==0,
                        'one actual close entry before one finish')
            if name=='hp1020_tusb_adapter_finish':
                self.finish_entries+=1
                require(self.finish_entries==1 and self.close_entries==1,
                        'one actual finish entry after close')
        for label,address in self.checkpoints.items():
            if label=='pre-final-service' and not self.close_entries:continue
            if next_pc!=address:continue
            require(label not in self.seen,'repeated checkpoint')
            require(self.checkpoint_order[len(self.seen)]==label,'checkpoint order changed')
            if label=='after-normalization':
                require(self.pending_windowbase is None and self.special==NORMALIZED and self.sar==0,
                        'normalization state incomplete')
                require(set(s['name'] for s in self.special_writes)==set(SPECIAL),'missing CPU normalization write')
                require(self.registers[1]==self.stack[0]+self.stack[1],'startup did not establish owned SP')
                self.normalized=True;self.allowed_write_spans=self.zero_spans
            self.seen.append(label)
            self.observe(label,self.registers_at(address),self.regions_at())
            if label=='park':
                require(self.c_started and not self.call_stack,'C did not return to own terminal park')
                require(self.program.instructions[address][0]=='j' and self.program.instructions[address][1]==(address,),
                        'terminal instruction is not a local self-jump')
                self.park_registers=self.registers_at(address)
                self.park_effect_counts=(self.access_count.copy(),len(self.calls))
        return next_pc

    def evidence(self):
        result=super().evidence()
        require(self.close_entries==1 and self.finish_entries==1,
                'exactly one original close and finish entry')
        result.update(actual_entry_events=self.entry_events,
            actual_close_entries=self.close_entries,actual_finish_entries=self.finish_entries,
            zero_spans=[list(x) for x in self.zero_spans],
            initialized_data_span=list(self.data_span),owned_stack=list(self.stack))
        return result
