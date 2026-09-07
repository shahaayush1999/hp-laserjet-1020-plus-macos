"""Independent BE Xtensa execution in QEMU's RAM-only sim machine.

No firmware boot, USB devices, networking, peripheral model or upload artifact.
The test_kc705_be CPU supplies a standard ISA cross-check, not the printer's
custom processor configuration. GDB register numbers are from QEMU v11.1.1
 target/xtensa/core-test_kc705_be/gdb-config.c.inc (PC, ARs, loops, WB/WS, PS).
"""
import os
from pathlib import Path
import shutil
import socket
import struct
import subprocess
import tempfile
import time

RETURN = 0x23000000
STACK_TOP = 0x2101fff0


class QemuRAM:
    def __init__(self):
        self.binary = shutil.which(os.environ.get('HP1020_QEMU', 'qemu-system-xtensaeb'))
        if not self.binary:
            raise RuntimeError('qemu-system-xtensaeb is required; see analysis/README.md')
        self.version = subprocess.check_output([self.binary, '--version'], text=True).splitlines()[0]
        self.temp = tempfile.TemporaryDirectory(prefix='hp1020-qemu-', dir='/tmp')
        self.socket = None
        self.process = None
        try:
            path = Path(self.temp.name) / 'gdb.sock'
            self.process = subprocess.Popen([
                self.binary, '-M', 'sim', '-cpu', 'test_kc705_be', '-m', '1G',
                '-nodefaults', '-display', 'none', '-serial', 'none',
                '-monitor', 'none', '-nic', 'none', '-S',
                '-gdb', f'unix:{path},server=on,wait=off',
            ], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            deadline = time.monotonic() + 5
            while not path.exists():
                if self.process.poll() is not None or time.monotonic() > deadline:
                    raise RuntimeError('QEMU did not start its private debugger socket')
                time.sleep(.01)
            self.socket = socket.socket(socket.AF_UNIX)
            self.socket.settimeout(10)
            self.socket.connect(str(path))
            self.command('qSupported')
            self.ok('Hg0')
            self.ok(f'Z0,{RETURN:x},1')
        except BaseException:
            self.close()
            raise

    def close(self):
        if self.socket is not None:
            self.socket.close()
        if self.process is not None:
            self.process.terminate()
            try:
                self.process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.communicate()
        self.temp.cleanup()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def byte(self):
        value = self.socket.recv(1)
        if not value:
            raise RuntimeError('QEMU debugger disconnected')
        return value

    def command(self, command):
        payload = command.encode('ascii')
        self.socket.sendall(b'$' + payload + b'#' + f'{sum(payload) % 256:02x}'.encode())
        first = self.byte()
        if first != b'+':
            raise RuntimeError(f'QEMU packet not acknowledged: {first!r}')
        if self.byte() != b'$':
            raise RuntimeError('missing QEMU packet marker')
        packet = bytearray()
        while (value := self.byte()) != b'#':
            packet.extend(value)
            if len(packet) > 0x40000:
                raise RuntimeError('excessive QEMU packet')
        checksum = int(self.byte() + self.byte(), 16)
        if checksum != sum(packet) % 256:
            raise RuntimeError('QEMU packet checksum mismatch')
        self.socket.sendall(b'+')
        # Our register/memory/stop replies never require binary escaping or RLE.
        if b'}' in packet or b'*' in packet:
            raise RuntimeError('unexpected encoded QEMU reply')
        return packet.decode('ascii')

    def ok(self, command):
        reply = self.command(command)
        if reply != 'OK':
            raise RuntimeError(f'QEMU rejected {command[:50]}: {reply}')

    def set_reg(self, number, value):
        self.ok(f'P{number:x}={value & 0xffffffff:08x}')

    def reg(self, number):
        value = self.command(f'p{number:x}')
        if len(value) != 8:
            raise RuntimeError(f'invalid QEMU register {number}: {value}')
        return int(value, 16)

    @staticmethod
    def ram_range(address, size):
        if not (0 <= address <= address + size <= 0x40000000):
            raise ValueError('outside QEMU synthetic RAM')

    def put(self, address, data):
        self.ram_range(address, len(data))
        for off in range(0, len(data), 4096):
            part = data[off:off + 4096]
            self.ok(f'M{address + off:x},{len(part):x}:' + part.hex())

    def read(self, address, size):
        self.ram_range(address, size)
        result = bytearray()
        for off in range(0, size, 4096):
            count = min(size - off, 4096)
            part = bytes.fromhex(self.command(f'm{address + off:x},{count:x}'))
            if len(part) != count:
                raise RuntimeError('short QEMU memory read')
            result.extend(part)
        return bytes(result)

    def load(self, path):
        """Independent ELF PT_LOAD reader; does not use our decoder/interpreter."""
        data = Path(path).read_bytes()
        if data[:6] != b'\x7fELF\x01\x02':
            raise ValueError('expected ELF32 BE')
        entry, phoff = struct.unpack_from('>II', data, 24)
        phsize, phnum = struct.unpack_from('>HH', data, 42)
        if phsize != 32:
            raise ValueError('unexpected ELF program header size')
        for i in range(phnum):
            kind, off, va, _, filesz, memsz, _, _ = struct.unpack_from('>8I', data, phoff + i * phsize)
            if kind != 1:
                continue
            if not 0 <= filesz <= memsz <= 0x200000 or off + filesz > len(data):
                raise ValueError('invalid ELF load span')
            self.put(va, data[off:off + filesz] + bytes(memsz - filesz))
        return entry

    def reset_cpu(self, entry):
        self.set_reg(38, 0)  # WINDOWBASE
        self.set_reg(39, 1)  # WINDOWSTART
        self.set_reg(42, 0)  # PS: no interrupt or window state inherited
        for number in range(1, 37):  # all physical ARs plus loop/SAR registers
            self.set_reg(number, 0)
        self.set_reg(1, RETURN)
        self.set_reg(2, STACK_TOP)
        self.set_reg(0, entry)

    def resume(self, stop=RETURN):
        reply = self.command('c')
        pc = self.reg(0)
        if not reply.startswith('T05') or pc != stop:
            raise RuntimeError(f'QEMU stopped unexpectedly: {reply}, PC={pc:#x}')

    def call0(self, entry, args):
        self.reset_cpu(entry)
        for i, value in enumerate(args, 3):
            self.set_reg(i, value)
        self.resume()
        return self.reg(3)

    def call8(self, entry, args):
        # Pinned BE assembler: 0b8000 = CALLX8 a8. Execute a real CALL8/ENTRY/
        # RETW sequence so QEMU, not the test, rotates the physical windows.
        self.put(RETURN - 3, bytes.fromhex('0b8000'))
        self.reset_cpu(RETURN - 3)
        self.set_reg(42, 0x40000)  # PS.WOE
        self.set_reg(9, entry)  # caller a8
        for i, value in enumerate(args, 11):
            self.set_reg(i, value)  # caller a10 ...
        self.resume()
        if self.reg(38) != 0 or self.reg(39) != 1:
            raise RuntimeError('QEMU register windows did not return to caller')
        return self.reg(11)
