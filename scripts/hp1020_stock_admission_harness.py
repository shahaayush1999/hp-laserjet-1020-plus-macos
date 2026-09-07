"""Original stream recognizer, buffering and parser admission in host RAM.

A single registered transport supplies bytes at an explicit low-level callback.
Original registration, magic matching, pushback, buffered reads and ZjStream
parser run. Event readiness, task setup and arrival timing are host inputs;
USB/RTOS/hardware do not execute. JobMgr can subsequently replay the messages.
"""
from hp1020_stock_lifecycle_harness import LifecycleHarness, CooperativeLifecycle
from hp1020_xtensa_call0 import STOP, STACK, STACK_SIZE

LOW_READ = 0x30000008
ADMISSION_CODE = [(0x10007c98,0x10007cd0),(0x10007d1c,0x100081f4),
                  (0x10009b20,0x10009b4c),(0x10011178,0x100111b4),
                  (0x1001b34d,0x1001b4c8),(0x1001b6b0,0x1001b6ec)]


class AdmissionMixin:
    def __init__(self, *args, probe_fragment=1024, **kwargs):
        super().__init__(*args, **kwargs)
        if not 1 <= probe_fragment <= 1024:
            raise ValueError('invalid admission probe fragment')
        self.probe_fragment = probe_fragment
        self.code_ranges = self.code_ranges + ADMISSION_CODE
        self.admission_events = []
        self.parser_entries = []
        self.ready_events = 0
        self.transport = self.read(0x10005da0,4)
        self.registry = self.read(0x10005dac,4)
        self.prepared = False

    def reset_cpu(self, entry):
        self.registers = [0] * 16
        self.registers[0] = STOP
        self.registers[1] = STACK + STACK_SIZE - 16
        self.pc = entry
        self.frames = []; self.loop = None; self.sar = 0

    def prepare_admission(self):
        if self.prepared:
            raise ValueError('admission already initialized')
        self.write(self.read(0x10005db0,4),4,0)
        self.reset_cpu(0x10009b20)
        self.run()  # Original ZjStream registration constructor.
        assert self.read(self.read(0x10005db0,4),4) == 1
        assert [self.read(self.registry+i*4,4) for i in range(6)] == [
            0x10009d34,0x1001bc80,0x1001bc78,4,0,0]
        self.write(self.read(0x10005d9c,4),4,1)
        self.put(self.transport,bytes(0x58))
        self.write(self.transport,4,1)  # sole transport readiness bit
        self.write(self.transport+4,4,LOW_READ)
        self.reset_cpu(0x10008034)
        self.run([self.transport,0x22000000,0])  # Original input-buffer constructor.
        table = self.read(0x1000647c,4)
        self.write(table+9*24+4,4,0x22000300)
        self.write(table+9*24+8,4,0)
        self.write(0x22000300,1,5)  # read timeout policy; no elapsed-time simulation
        self.reset_cpu(0x10007d1c)
        self.prepared = True

    def parse_input(self):
        self.prepare_admission()
        self.run()

    def extension(self, op, args, nxt):
        if self.job_mode or op not in ('call8','callx8'):
            return super().extension(op,args,nxt)
        target = self.registers[args[0]] if op == 'callx8' else args[0]
        values = self.registers[10:14]
        if target == 0x10009d34:
            self.parser_entries.append(dict(callsite=hex(self.pc),received=self.input_pos,
                buffered=self.read(self.transport+36,4),context=hex(values[0])))
        if target not in (0x10012048,0x10012184,0x1001214c,0x10017d28,LOW_READ):
            return super().extension(op,args,nxt)
        result = 0
        if target == 0x10017d28:
            assert values[:3] == [self.read(0x10005da4,4),0xffffffff,1]
            if self.ready_events:
                assert self.input_pos == len(self.input) and self.read(self.transport+36,4) == 0
                self.branch_taken = True
                return STOP  # Fixture stops when dispatcher returns to idle wait.
            self.write(values[3],4,1)
            self.ready_events += 1
        elif target == LOW_READ:
            dst,size,timeout = values[:3]
            assert 0 <= size <= 0x100000 and timeout in (0,50,200,500)
            result = min(size,len(self.input)-self.input_pos)
            if timeout == 0:
                result = min(result,self.probe_fragment)
            if result:
                self.put(dst,self.input[self.input_pos:self.input_pos+result])
            self.input_pos += result
        self.admission_events.append(dict(target=hex(target),args=values.copy(),result=result))
        self.registers[10] = result; self.branch_taken = True
        return nxt


class AdmissionLifecycle(AdmissionMixin, LifecycleHarness):
    pass


class CooperativeAdmission(AdmissionMixin, CooperativeLifecycle):
    def initialize_parser(self):
        self.prepare_admission()

    def parser_returned(self):
        # Original dispatcher itself recognized every subsequent document.
        assert self.input_pos == len(self.input) and self.read(self.transport+36,4) == 0
        self.parser_done = True
