"""Native completion fixture entering only the original no-next-DMA RAM tail.

The fixture explicitly supplies successful consumption and clears the pending
DMA cursor. It does not execute the IRQ prefix, next-transfer path or peripherals.
The original tail decrements references, sets the JobMgr event, clears its CPU
interrupt bit and returns through the fixture's valid register-window frame.


UNEXECUTED DRAFT: this assembly composition has not been run or validated.
See analysis/open-firmware-model/next-evidence.md for its required oracles and gate test.
"""

RETIRE_CODE = [(0x10014319,0x1001434b),(0x100143a5,0x100143b8),
               (0x100171e0,0x100171f0)]


def retirement_source(video):
    return f'''
.align 4
retire_work:
 entry a1,64
 l32i a4,a2,80
retire_next:
 beqz a4,retire_done
 l32i a5,a4,0
 mov a10,a4
 call8 retire_one
 mov a4,a5
 j retire_next
retire_done:
 movi a2,0
 retw
.align 4
retire_one:
 entry a1,48
 movi a3,{video:#x}
 mov a4,a1
 movi a5,0
 s32i a5,a3,156
 s32i a2,a3,164
 s32i a5,a3,168
 s32i a5,a3,172
 s32i a5,a3,176
 s32i a5,a3,180
 movi a8,1
 s32i a8,a3,248
 movi a6,0
 movi a8,164
 add a7,a3,a8
 movi a8,0x10014319
 jx a8
'''
