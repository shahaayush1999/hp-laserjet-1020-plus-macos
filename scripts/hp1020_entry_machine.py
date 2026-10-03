"""UNEXECUTED bounded concrete entry-to-C interpreter extension.

No shared interpreter change, peripheral, cache/TLB, arbitrary special register,
windowed call, inherited stack, host callback or runtime CPU reset is admitted.
Only the reviewed startup prefix may normalize CPU state. QEMU is separate.
"""
from pathlib import Path
import gzip
import hashlib
import struct
from hp1020_xtensa_call0 import Machine, STOP, MASK

MAIN_START, MAIN_END = 0x10003000, 0x100351e0
ENTRY = 0x100167a8
STATE, MEMORY, MAILBOX = (0x1000e000,13496), (0x10016800,114704), (0x10014040,1024)
ZERO_SPANS = (STATE,MEMORY,MAILBOX)
STACK = (0x10012000,8192)
WRITABLE = ZERO_SPANS+(STACK,)
SPECIAL = {'lbeg':0,'lend':1,'lcount':2,'windowbase':72,'windowstart':73,
           'intenable':228,'ps':230}
NORMALIZED = {'lbeg':0,'lend':0,'lcount':0,'windowbase':0,'windowstart':1,
              'intenable':0,'ps':15}


def require(value, message):
    if not value:raise ValueError(message)


def contains(spans,address,size):
    return 0<=address<=MASK and 0<size<=0x100000000-address and any(
        a<=address and address+size<=a+n for a,n in spans)


class EntryMachine(Machine):
    def __init__(self,program,regions,initial,checkpoints,trace_dir,observe):
        super().__init__(program)
        # Replace, rather than supplement, the shared per-call synthetic stack.
        self.segments=[(a,bytearray(raw),7) for a,raw in regions]
        require(len({a for a,_,_ in self.segments})==len(self.segments),'unique initial regions')
        ordered=sorted((a,a+len(raw)) for a,raw,_ in self.segments)
        require(all(a[1]<=b[0] for a,b in zip(ordered,ordered[1:])),'initial regions overlap')
        self.initial_regions=[(a,bytes(raw)) for a,raw in regions]
        self.write_ranges=[(a,a+n) for a,n in WRITABLE]
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
        require(self.checkpoint_order==['after-normalization','pre-c','pre-finish','park'],
                'exact ordered checkpoints')
        require(len(set(self.checkpoints.values()))==4,'distinct checkpoint addresses')
        require(self.checkpoints['after-normalization']==program.symbols['hp1020_entry_after_normalization'] and
                self.checkpoints['pre-c']==program.symbols['hp1020_entry_before_c'] and
                self.checkpoints['pre-finish']==program.symbols['hp1020_usb_document_finish'] and
                self.checkpoints['park']==program.symbols['hp1020_entry_park'],'linked checkpoint binding')
        require(not(initial['lcount'] and any(a<=initial['lend']<=b for a,b in (
            (program.symbols['hp1020_entry_normalize'],self.checkpoints['after-normalization']),
            (ENTRY,ENTRY+3)))),'incoming loop cannot intercept initial normalization')
        self.observe=observe;self.seen=[];self.normalized=False;self.c_started=False
        self.minimum_sp=STACK[0]+STACK[1];self.minimum_stack_access=None
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

    def close(self):
        if not self.closed:
            self.access_trace.close();self.step_trace.close()
            self.access_file.close();self.step_file.close();self.closed=True

    def physical_registers(self):
        result=self.physical.copy()
        for i,v in enumerate(self.registers):result[(self.windowbase*4+i)%32]=v&MASK
        return result

    def registers_at(self,pc):
        return {'pc':pc,**self.special,'sar':self.sar,
                'physical_ar':self.physical_registers(),'logical_ar':self.registers.copy()}

    def regions_at(self):
        return [(a,bytes(raw)) for a,raw,_ in self.segments]

    def record_access(self,kind,address,size,value):
        raw=struct.pack('>B3xIIII',1 if kind=='read' else 2,self.pc,address,size,value&MASK)
        self.access_trace.write(raw);self.access_digest.update(raw)
        self.access_count[kind]+=1
        key=f'{kind}/{size}';self.access_widths[key]=self.access_widths.get(key,0)+1
        if STACK[0]<=address<STACK[0]+STACK[1]:
            require(self.c_started,'stack access before C CALL0')
            self.minimum_stack_access=address if self.minimum_stack_access is None else min(self.minimum_stack_access,address)

    def read(self,address,size):
        require(contains(self.read_spans,address,size),f'forbidden data read {address:#x}+{size} at{self.pc:#x}')
        require(not(STACK[0]<=address<STACK[0]+STACK[1]) or self.c_started,
                'stack read before C CALL0')
        # Both alignment and complete backing-span checks precede the read.
        result=super().read(address,size)
        self.record_access('read',address,size,result)
        return result

    def write(self,address,size,value):
        require(contains(self.allowed_write_spans,address,size),
                f'forbidden phase store {address:#x}+{size} at{self.pc:#x}')
        require(not(STACK[0]<=address<STACK[0]+STACK[1]) or self.c_started,'stack store before C CALL0')
        # Base implementation checks full width/alignment before changing RAM.
        super().write(address,size,value)
        self.record_access('write',address,size,value)

    def extension(self,op,args,next_pc):
        start=self.program.symbols['hp1020_entry_normalize']
        require(start<=self.pc<self.checkpoints['after-normalization'],
                f'special operation outside normalization {op} at{self.pc:#x}')
        if op=='rsil':
            require(args==(2,15),'only reviewed RSIL a2,15')
            self.registers[2]=self.special['ps'];self.special['ps']=(self.special['ps']&~15)|15
        elif op in ('rsync','isync'):
            require(not args,'synchronization operands')
            if op=='rsync' and self.pending_windowbase is not None:
                self.physical=self.physical_registers()
                self.windowbase=self.pending_windowbase;self.pending_windowbase=None
                self.registers[:]=[self.physical[(self.windowbase*4+i)%32] for i in range(16)]
        elif op.startswith('wsr.'):
            name=op.split('.',1)[1]
            require(name in SPECIAL and len(args)==1,'only reviewed WSR')
            value=self.registers[args[0]]
            require(value==NORMALIZED[name],f'unexpected normalization {name}={value:#x}')
            require(name not in [s['name'] for s in self.special_writes],'duplicate normalization write')
            self.special[name]=value
            if name=='windowbase':self.pending_windowbase=value
            self.special_writes.append(dict(pc=self.pc,name=name,value=value))
        else:
            raise ValueError(f'unadmitted startup instruction {op} at{self.pc:#x}')
        return next_pc

    def after_instruction(self,pc,next_pc):
        raw=struct.pack('>I',pc);self.step_trace.write(raw);self.step_digest.update(raw)
        op,args,encoded=self.program.instructions[pc]
        base=op.removesuffix('.n')
        if self.special['lcount'] and next_pc==self.special['lend']:
            raise ValueError('inadmissible incoming active loop intercepted normalization')
        if base in ('call0','callx0'):
            require(self.normalized,'call before own CPU/stack initialization')
            sp=self.registers[1]
            require(STACK[0]<=sp<=STACK[0]+STACK[1] and not(sp&15),'call SP outside owned aligned stack')
            require(next_pc in self.program.instructions,'call target outside annotated admitted code')
            if not self.c_started:
                require(pc==self.checkpoints['pre-c'] and next_pc==self.program.symbols['hp1020_entry_c'],
                        'first C call is exact workload entry')
                require(self.seen==['after-normalization','pre-c'],'first call follows complete BSS witness')
                self.c_started=True;self.allowed_write_spans=WRITABLE
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
            require(STACK[0]<=sp<=STACK[0]+STACK[1],'SP escaped owned stack')
            self.minimum_sp=min(self.minimum_sp,sp)
        if pc==self.checkpoints['park']:
            require(self.seen==self.checkpoint_order and base=='j' and args==(pc,) and next_pc==pc,
                    'only terminal self-branch may execute after park')
            require(self.registers_at(pc)==self.park_registers and
                    (self.access_count,len(self.calls))==self.park_effect_counts,
                    'terminal park changed registers or performed an access/call')
            self.park_steps+=1
            return STOP if self.park_steps==2 else next_pc
        for label,address in self.checkpoints.items():
            if next_pc!=address:continue
            require(label not in self.seen,'repeated checkpoint')
            require(self.checkpoint_order[len(self.seen)]==label,'checkpoint order changed')
            if label=='after-normalization':
                require(self.pending_windowbase is None and self.special==NORMALIZED and self.sar==0,
                        'normalization state incomplete')
                require(set(s['name'] for s in self.special_writes)==set(SPECIAL),'missing CPU normalization write')
                require(self.registers[1]==STACK[0]+STACK[1],'startup did not establish owned SP')
                self.normalized=True;self.allowed_write_spans=ZERO_SPANS
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
        require(self.seen==self.checkpoint_order and self.park_steps==2,'all checkpoints and two park iterations required')
        return dict(instructions=self.steps,visited_instructions=len(self.visited),opcodes=sorted(self.opcodes),
            special_writes=self.special_writes,checkpoints=self.seen,calls=self.calls,
            access_count=self.access_count,access_widths=self.access_widths,
            access_sha256=self.access_digest.hexdigest(),step_sha256=self.step_digest.hexdigest(),
            minimum_sp=self.minimum_sp,minimum_stack_access=self.minimum_stack_access,
            owned_stack_bytes=STACK[1],no_external_stack=True,host_runtime_mutations=0,
            terminal_self_branch_statically_checked=True,terminal_self_branch_executions=self.park_steps,
            limits='Bounded concrete standard-ISA path, not HP processor, mapping, interrupts, cache, hardware or printing.')
