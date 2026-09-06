"""Execute the stock parser with explicit host RAM / RTOS boundary substitutes.

Original parser, item builder, work constructor, list initializer and libc bytes
execute unchanged. Only allocation/free, input/pushback, message delivery,
datastore locks and document notifications are intercepted. No queue consumer,
USB controller, scheduler or peripheral is modeled. Results are conditional on
these boundary assumptions, not a claim to run all firmware.
"""
from hp1020_xtensa_stock import StockMachine

INPUT_CALLBACK=0x30000000
PUSHBACK_CALLBACK=0x30000004
CONTEXT=0x22000000
TRAY=0x22001000
HEAP=0x22100000
CODE=[(0x10009b4c,0x1000a264),(0x1000f1c4,0x1000f280),
      (0x100111b4,0x100111ec),(0x100130c4,0x100130d4),
      (0x100169d4,0x10016a38),(0x1001b4c8,0x1001b542),
      (0x1001b56c,0x1001b59c)]
BOUNDARIES={0x10013140:'allocate',0x10013408:'free',0x10013658:'queue_send',
            0x100181a4:'datastore_lock',0x10018214:'datastore_unlock',
            0x1001262c:'document_begin',0x100126b0:'document_end',
            INPUT_CALLBACK:'read',PUSHBACK_CALLBACK:'pushback'}

class ParserHarness(StockMachine):
    def __init__(self,program,data,fill=0xcc,read_limit=None):
        super().__init__(program,0x10009d34,CODE,[(CONTEXT,0x2000)])
        self.input=data;self.input_pos=0;self.heap_cursor=HEAP
        self.allocations={};self.messages=[];self.boundary_calls=[]
        self.fill=fill;self.read_limit=read_limit
        self.write(CONTEXT+12,4,INPUT_CALLBACK)
        self.write(CONTEXT+20,4,PUSHBACK_CALLBACK)
        # Explicit fixture: a single empty tray record; no live tray mapping claim.
        table=self.read(0x1000647c,4)
        self.write(table+29*24+4,4,TRAY)

    def bytes_at(self,address,size):
        data,off=self.span(address,size)
        return bytes(data[off:off+size])

    def extension(self,op,a,nxt):
        if op not in ('call8','callx8'):
            return super().extension(op,a,nxt)
        target=self.registers[a[0]] if op=='callx8' else a[0]
        if target not in BOUNDARIES:
            return super().extension(op,a,nxt)
        args=self.registers[10:14]
        name=BOUNDARIES[target]
        event=dict(name=name,callsite=f'0x{self.pc:08x}',args=args.copy())
        result=0
        if name=='allocate':
            size,kind=args[:2]
            if not 0<size<=0x100000 or self.heap_cursor+size>HEAP+0x400000:
                raise ValueError('bounded fixture allocator rejected request')
            result=self.heap_cursor;self.heap_cursor+=(size+15)&~15
            self.segments.append((result,bytearray([self.fill])*size,6))
            self.write_ranges.append((result,result+size))
            self.allocations[result]=dict(size=size,kind=kind,freed=False)
        elif name=='free':
            ptr=args[0]
            if ptr not in self.allocations or self.allocations[ptr]['freed']:
                raise ValueError('unknown/double free')
            self.allocations[ptr]['freed']=True
            self.write_ranges=[(x,y) for x,y in self.write_ranges if x!=ptr]
            self.segments=[s for s in self.segments if s[0]!=ptr]
        elif name=='read':
            ctx,dst,size,mode=args
            if ctx!=CONTEXT or mode!=0:raise ValueError('unexpected input callback contract')
            result=min(size,len(self.input)-self.input_pos)
            if self.read_limit is not None:result=min(result,self.read_limit)
            if result:self.put(dst,self.input[self.input_pos:self.input_pos+result])
            self.input_pos+=result
        elif name=='pushback':
            ctx,src,size=args[:3]
            if ctx!=CONTEXT or size>self.input_pos:raise ValueError('bad pushback')
            if self.bytes_at(src,size)!=self.input[self.input_pos-size:self.input_pos]:
                raise ValueError('pushback not equal to previous input')
            self.input_pos-=size
        elif name=='queue_send':
            queue,ptr=args[:2]
            if queue!=3:raise ValueError('unexpected destination queue')
            words=[self.read(ptr+i*4,4) for i in range(4)]
            message=dict(words=words)
            payload=words[3]
            if payload in self.allocations and not self.allocations[payload]['freed']:
                message['payload']=self.bytes_at(payload,self.allocations[payload]['size']).hex()
            self.messages.append(message)
        elif name in ('document_begin','document_end'):
            if args[0]!=0:raise ValueError('unexpected document notification')
        elif name=='datastore_lock':
            if args[1]!=0xffffffff:raise ValueError('unexpected lock timeout')
        event['result']=result;self.boundary_calls.append(event)
        self.registers[10]=result
        self.branch_taken=True
        return nxt
