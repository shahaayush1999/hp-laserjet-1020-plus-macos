#!/usr/bin/env python3
"""Challenge buffered debugger framing with split/coalesced/corrupt responses."""
from hp1020_qemu_ram import QemuRAM


class FragmentedSocket:
    def __init__(self, data, size):
        self.data = data
        self.size = size
        self.sent = []
    def recv(self, count):
        n = min(count,self.size,len(self.data))
        result,self.data = self.data[:n],self.data[n:]
        return result
    def sendall(self, data):
        self.sent.append(data)


def fixture(data, size):
    q = QemuRAM.__new__(QemuRAM)
    q.socket = FragmentedSocket(data,size)
    q.receive_buffer = bytearray()
    return q


def main():
    cases = 0
    for size in (1,2,3,7,65536):
        q = fixture(b'+$OK#9a+$0000000a#b1',size)
        assert q.command('one') == 'OK'
        assert q.command('two') == '0000000a'
        assert q.socket.sent == [b'$one#42',b'+',b'$two#5a',b'+']
        cases += 1
    for data,expected in [(b'-$OK#9a','not acknowledged'),
                          (b'+!OK#9a','missing QEMU packet marker'),
                          (b'+$OK#00','checksum mismatch'),
                          (b'+$OK','disconnected'),
                          (b'+$*#2a','unexpected encoded'),
                          (b'+$'+b'a'*0x40001+b'#00','excessive QEMU packet')]:
        for size in (3,65536):
            q = fixture(data,size)
            try:
                q.command('one')
            except RuntimeError as error:
                assert expected in str(error), (expected,str(error))
            else:
                raise AssertionError('corrupt debugger response accepted')
            cases += 1
    print(f'QEMU debugger protocol: {cases} fragmentation/corruption cases')


if __name__ == '__main__':
    main()
