# Ghidra HP 1020 Firmware Summary

Program: sihp1020.elf
Language: Xtensa:BE:32:default
Compiler spec: default
Image base: 10000000
Entry points:
- 100167a8

Memory blocks:
- .WindowVectors.text start=10000000 size=0x180 r=true w=false x=true
- .KernelExceptionVector.literal start=10000180 size=0x4 r=true w=false x=true
- .KernelExceptionVector.text start=10000200 size=0x1c r=true w=false x=true
- .UserExceptionVector.literal start=1000021c size=0x4 r=true w=false x=true
- .UserExceptionVector.text start=10000220 size=0x1c r=true w=false x=true
- .DoubleExceptionVector.text start=10000270 size=0xe0 r=true w=false x=true
- .sys_interface_table start=10000370 size=0x12c r=true w=true x=false
- .rodata start=10003000 size=0x2c80 r=true w=false x=false
- .text start=10005c80 size=0x15f0f r=true w=false x=true
- .data start=1001bb90 size=0x1ab0 r=true w=true x=false
- .bss start=1001d640 size=0x17ba0 r=true w=true x=false
- .ResetVector.text start=10100020 size=0x2e0 r=true w=false x=true
- .DebugExceptionVector.literal start=10100300 size=0x4 r=true w=false x=true
- .DebugExceptionVector.text start=10100320 size=0xc r=true w=false x=true
- .comment start=.comment::00000000 size=0x2df5 r=false w=false x=false
- .shstrtab start=.shstrtab::00000000 size=0x309 r=false w=false x=false
- .xt.insn start=.xt.insn::00000000 size=0xd98 r=false w=false x=false
- .xt.lit start=.xt.lit::00000000 size=0x230 r=false w=false x=false
- _elfHeader start=_elfHeader::00000000 size=0x34 r=false w=false x=false
- _elfProgramHeaders start=_elfProgramHeaders::00000000 size=0x160 r=false w=false x=false
- _elfSectionHeaders start=_elfSectionHeaders::00000000 size=0x618 r=false w=false x=false
- unallocated_0 start=unallocated_0::00000000 size=0x4 r=false w=false x=false

Function count: 326
First functions:
- 10006cd0 FUN_10006cd0
- 10006e64 FUN_10006e64
- 10006f00 FUN_10006f00
- 10007038 FUN_10007038
- 10007054 FUN_10007054
- 10007070 FUN_10007070
- 100070a8 FUN_100070a8
- 100070e0 FUN_100070e0
- 10007130 FUN_10007130
- 10007180 FUN_10007180
- 10007218 FUN_10007218
- 100072b0 FUN_100072b0
- 10007334 FUN_10007334
- 100073b8 FUN_100073b8
- 10007430 FUN_10007430
- 10007468 FUN_10007468
- 10007c00 FUN_10007c00
- 10007c5c FUN_10007c5c
- 10007c70 FUN_10007c70
- 10007cd0 FUN_10007cd0
- 10008034 FUN_10008034
- 100086f4 FUN_100086f4
- 1000899c FUN_1000899c
- 10008b78 FUN_10008b78
- 10008c24 FUN_10008c24
- 10008fb0 FUN_10008fb0
- 10009a10 FUN_10009a10
- 10009ac4 FUN_10009ac4
- 10009b4c FUN_10009b4c
- 1000a280 FUN_1000a280
- 1000a2a4 FUN_1000a2a4
- 1000ae3c FUN_1000ae3c
- 1000ae94 FUN_1000ae94
- 1000aec0 FUN_1000aec0
- 1000af88 FUN_1000af88
- 1000af98 FUN_1000af98
- 1000afd8 FUN_1000afd8
- 1000afe0 FUN_1000afe0
- 1000afec FUN_1000afec
- 1000b128 FUN_1000b128

Interesting strings and references:
- 100034f0 USB2IdleThread
  ref 10005f14
- 1000351c usbIoFlags
  ref 10005fb8
- 10003530 USB2Thread
  ref 10005fc4
- 10003748 agiACLDownload
  ref 10006054
- 10003758 TIME=Wed Mar 09 12:27:39 2005 BOI049 PROD=MANGUSTA CFG=GCC_RELEASE
  ref 10006070
- 10003f94 FUSER
- 10003fa8 PAPERLESS
- 10003fb4 SETERROR
- 10003fd8 TONEREXP
- 1000403c JAMRECOVERY
- 10004138 PARSEERROR
  ref 1000b4a8
  ref 10006118
- 10004288 	INTRAY2 PAPERTRAY
  ref 1000bda3
  ref 100061b4
- 1000429c 	INTRAY3 PAPERTRAY
  ref 1000bdc0
  ref 100061b8
- 100042b0 PAPERS [17 ENUMERATED]
  ref 1000bde0
  ref 100061bc
- 10004728 @PJL ECHO 
  ref 1000ce60
  ref 1000ce74
  ref 1000ce7c
  ref 10004668
- 10004cd3 \nxxMFG:%s;MDL:%s;CMD:%s;CLS:%s;DES:%s;FWVER:%s;
- 10004e98  no threads exist at this time\n
  ref 1000659c
- 10004ec0 Name: %s  TX_THREAD ptr: 0x%08x\n  Priority: %u  Run Count: %u\n  Stack ptr: 0x%08x  Remaining: %u\n  State: %s  SuspLoc: 0x%08x\n
  ref 100065a4
- 10004f40 ERROR corrputed event flag id\n
  ref 100065ac
- 10004ff4 ERROR corrupted semaphore id\n
  ref 100065c0
- 10005078         %u threads are currently waiting\n
  ref 100065cc
- 100050a4 ERROR corrupted mutex id\n
  ref 100065d4
- 10005120        and is currently owned by thread 0x%08x\n
  ref 100065e0
- 10005184 ERROR corrupted queue id\n
  ref 100065ec
- 1000521c Name: %s  TX_THREAD ptr: 0x%08x\n
  ref 10006600
- 100052a4        %u threads are currently waiting\n
  ref 10006610
- 100052d0 Run count unreliable for thread 0x%08x\n
  ref 1000661c
- 100052f8 Thread 0x%08x run count delta = %u\n
  ref 10006620
- 10005c6c System Timer Thread
  ref 10006aec
- 1001d570 Copyright (c) 1996-2001 Express Logic Inc. * ThreadX ARM9/ARM Version G4.0.4.0 *
