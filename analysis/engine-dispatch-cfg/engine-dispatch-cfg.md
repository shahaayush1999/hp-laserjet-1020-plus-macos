# HP 1020 Engine Dispatch CFG

This report records Ghidra's raw instruction and basic-block view for the engine dispatcher.
It is meant to check whether decompilation lost a branch such as engine message `0x17`.

- Function: `10016164` `hp1020_engine_message_dispatch_candidate`
- Body addresses: `332`

## Basic Blocks

| Block | Range | Destinations |
|---:|---|---|
| `0` | `10016164..10016170` | `10016174` CONDITIONAL_JUMP<br>`10016171` FALL_THROUGH |
| `1` | `10016171..10016173` | `100162aa` UNCONDITIONAL_JUMP |
| `2` | `10016174..1001617c` | `1001617d` FALL_THROUGH |
| `3` | `1001617d..1001617f` | `10016244` COMPUTED_JUMP<br>`100162aa` COMPUTED_JUMP<br>`100161a7` COMPUTED_JUMP<br>`10016180` COMPUTED_JUMP<br>`100161ba` COMPUTED_JUMP<br>`1001622f` COMPUTED_JUMP<br>`10016218` COMPUTED_JUMP<br>`10016207` COMPUTED_JUMP<br>`10016238` COMPUTED_JUMP |
| `4` | `10016180..100161a6` | `10013658` UNCONDITIONAL_CALL<br>`10016098` UNCONDITIONAL_CALL<br>`100162aa` UNCONDITIONAL_JUMP |
| `5` | `100161a7..100161b9` | `10013658` UNCONDITIONAL_CALL<br>`100162aa` UNCONDITIONAL_JUMP |
| `6` | `100161ba..100161cb` | `10015df8` UNCONDITIONAL_CALL<br>`100162aa` CONDITIONAL_JUMP<br>`100161cc` FALL_THROUGH |
| `7` | `100161cc..100161d3` | `100161ea` CONDITIONAL_JUMP<br>`100161d4` FALL_THROUGH |
| `8` | `100161d4..100161e9` | `100180dc` UNCONDITIONAL_CALL<br>`100161ea` FALL_THROUGH |
| `9` | `100161ea..100161ef` | `100162aa` CONDITIONAL_JUMP<br>`100161f0` FALL_THROUGH |
| `10` | `100161f0..10016206` | `10013620` UNCONDITIONAL_CALL<br>`100162aa` UNCONDITIONAL_JUMP |
| `11` | `10016207..10016217` | `10015dd0` UNCONDITIONAL_CALL<br>`100160a8` UNCONDITIONAL_CALL<br>`10015df8` UNCONDITIONAL_CALL<br>`100162aa` UNCONDITIONAL_JUMP |
| `12` | `10016218..1001622e` | `10013658` UNCONDITIONAL_CALL<br>`100162aa` UNCONDITIONAL_JUMP |
| `13` | `1001622f..10016237` | `10015df8` UNCONDITIONAL_CALL<br>`100162aa` UNCONDITIONAL_JUMP |
| `14` | `10016238..10016243` | `10016244` FALL_THROUGH |
| `15` | `10016244..10016256` | `10015df8` UNCONDITIONAL_CALL<br>`10016264` CONDITIONAL_JUMP<br>`10016257` FALL_THROUGH |
| `16` | `10016257..1001625b` | `1001626a` CONDITIONAL_JUMP<br>`1001625c` FALL_THROUGH |
| `17` | `1001625c..10016263` | `100162aa` UNCONDITIONAL_JUMP |
| `18` | `10016264..10016269` | `1001626a` FALL_THROUGH |
| `19` | `1001626a..10016286` | `100162b0` UNCONDITIONAL_CALL<br>`10015d14` UNCONDITIONAL_CALL<br>`1001628c` CONDITIONAL_JUMP<br>`10016287` FALL_THROUGH |
| `20` | `10016287..1001628b` | `1001628c` FALL_THROUGH |
| `21` | `1001628c..1001628f` | `100162a4` CONDITIONAL_JUMP<br>`10016290` FALL_THROUGH |
| `22` | `10016290..1001629d` | `10015c68` UNCONDITIONAL_CALL<br>`100162aa` CONDITIONAL_JUMP<br>`1001629e` FALL_THROUGH |
| `23` | `1001629e..100162a3` |  |
| `24` | `100162a4..100162a9` | `10015c68` UNCONDITIONAL_CALL<br>`100162aa` FALL_THROUGH |
| `25` | `100162aa..100162af` |  |

## Switch Table

The dispatcher subtracts `0x0b` from message word 0, accepts indexes `0..0x35`,
and jumps through the table at `0x10005a10`.

| Message | Target | Working meaning |
|---:|---:|---|
| `0x0b` | `10016244` | page/engine work |
| `0x0c` | `100162aa` | default return/no-op |
| `0x0d` | `100161a7` | rewrite to `0x0e` and resend queue `1` |
| `0x0e` | `100162aa` | default return/no-op |
| `0x0f` | `10016180` | engine reset/clear; sends `0x25` |
| `0x10` | `100162aa` | default return/no-op |
| `0x11` | `100161ba` | drain deferred engine/page work |
| `0x12` | `100162aa` | default return/no-op |
| `0x13` | `100162aa` | default return/no-op |
| `0x14` | `100162aa` | default return/no-op |
| `0x15` | `100162aa` | default return/no-op |
| `0x16` | `100162aa` | default return/no-op |
| `0x17` | `100162aa` | default return/no-op |
| `0x18` | `1001622f` | status poll |
| `0x19` | `10016218` | send startup/ready message `0x16` |
| `0x1a` | `10016207` | preflight/status refresh |
| `0x1b` | `100162aa` | default return/no-op |
| `0x1c` | `100162aa` | default return/no-op |
| `0x1d` | `100162aa` | default return/no-op |
| `0x1e` | `100162aa` | default return/no-op |
| `0x1f` | `100162aa` | default return/no-op |
| `0x20` | `100162aa` | default return/no-op |
| `0x21` | `100162aa` | default return/no-op |
| `0x22` | `100162aa` | default return/no-op |
| `0x23` | `100162aa` | default return/no-op |
| `0x24` | `100162aa` | default return/no-op |
| `0x25` | `100162aa` | default return/no-op |
| `0x26` | `100162aa` | default return/no-op |
| `0x27` | `100162aa` | default return/no-op |
| `0x28` | `100162aa` | default return/no-op |
| `0x29` | `100162aa` | default return/no-op |
| `0x2a` | `100162aa` | default return/no-op |
| `0x2b` | `100162aa` | default return/no-op |
| `0x2c` | `100162aa` | default return/no-op |
| `0x2d` | `100162aa` | default return/no-op |
| `0x2e` | `100162aa` | default return/no-op |
| `0x2f` | `100162aa` | default return/no-op |
| `0x30` | `100162aa` | default return/no-op |
| `0x31` | `100162aa` | default return/no-op |
| `0x32` | `100162aa` | default return/no-op |
| `0x33` | `100162aa` | default return/no-op |
| `0x34` | `100162aa` | default return/no-op |
| `0x35` | `100162aa` | default return/no-op |
| `0x36` | `100162aa` | default return/no-op |
| `0x37` | `100162aa` | default return/no-op |
| `0x38` | `100162aa` | default return/no-op |
| `0x39` | `100162aa` | default return/no-op |
| `0x3a` | `100162aa` | default return/no-op |
| `0x3b` | `100162aa` | default return/no-op |
| `0x3c` | `100162aa` | default return/no-op |
| `0x3d` | `100162aa` | default return/no-op |
| `0x3e` | `100162aa` | default return/no-op |
| `0x3f` | `100162aa` | default return/no-op |
| `0x40` | `10016238` | force/start page path; falls through to `0x0b` |

Message `0x17` maps to `0x100162aa`, the default return block. That means the
engine thread receives `0x17` messages, but this recovered dispatcher does not consume
their payload directly.

## Instructions

| Address | Instruction | References |
|---:|---|---|
| `10016164` | `entry a1,0x40` |  |
| `10016167` | `l32i.n a8,a2,0x0` |  |
| `10016169` | `addi a9,a8,-0xb` |  |
| `1001616c` | `movi.n a8,0x35` |  |
| `1001616e` | `bgeu a8,a9,0x10016174` | `10016174` CONDITIONAL_JUMP |
| `10016171` | `j 0x100162aa` | `100162aa` UNCONDITIONAL_JUMP |
| `10016174` | `l32r a8,0x100069a8` | `100069a8` READ |
| `10016177` | `addx4 a8,a9,a8` |  |
| `1001617a` | `l32i a8,a8,0x0` | `10005a10` DATA |
| `1001617d` | `jx a8` | `10016244` COMPUTED_JUMP<br>`100162aa` COMPUTED_JUMP<br>`100161a7` COMPUTED_JUMP<br>`10016180` COMPUTED_JUMP<br>`100161ba` COMPUTED_JUMP<br>`1001622f` COMPUTED_JUMP<br>`10016218` COMPUTED_JUMP<br>`10016207` COMPUTED_JUMP<br>`10016238` COMPUTED_JUMP |
| `10016180` | `movi.n a8,0x25` |  |
| `10016182` | `s32i.n a8,a1,0x0` | `Stack[-0x40]` DATA |
| `10016184` | `movi.n a12,0x0` |  |
| `10016186` | `s32i.n a12,a1,0x4` |  |
| `10016188` | `movi.n a10,0x1` |  |
| `1001618a` | `mov.n a11,a1` |  |
| `1001618c` | `l32r a8,0x10006920` | `10006920` READ |
| `1001618f` | `mov a9,a10` |  |
| `10016192` | `s8i a9,a8,0x28` | `1002f0ec` WRITE |
| `10016195` | `s32i a12,a8,0x68` | `1002f12c` WRITE |
| `10016198` | `s32i a12,a8,0x6c` | `1002f130` WRITE |
| `1001619b` | `mov a1,a1` |  |
| `1001619e` | `call8 0x10013658` | `10013658` UNCONDITIONAL_CALL |
| `100161a1` | `call8 0x10016098` | `10016098` UNCONDITIONAL_CALL |
| `100161a4` | `j 0x100162aa` | `100162aa` UNCONDITIONAL_JUMP |
| `100161a7` | `movi.n a8,0xe` |  |
| `100161a9` | `s32i.n a8,a2,0x0` |  |
| `100161ab` | `movi a10,0x1` |  |
| `100161ae` | `mov a11,a2` |  |
| `100161b1` | `mov a1,a1` |  |
| `100161b4` | `call8 0x10013658` | `10013658` UNCONDITIONAL_CALL |
| `100161b7` | `j 0x100162aa` | `100162aa` UNCONDITIONAL_JUMP |
| `100161ba` | `movi a10,0x0` |  |
| `100161bd` | `call8 0x10015df8` | `10015df8` UNCONDITIONAL_CALL |
| `100161c0` | `l32r a8,0x10005e34` | `10005e34` READ |
| `100161c3` | `extui a10,a10,0x0,0x10` |  |
| `100161c6` | `and a7,a10,a8` |  |
| `100161c9` | `bnez a7,0x100162aa` | `100162aa` CONDITIONAL_JUMP |
| `100161cc` | `l32r a2,0x10006920` | `10006920` READ |
| `100161cf` | `l32i a9,a2,0x68` | `1002f12c` READ |
| `100161d2` | `beqz.n a9,0x100161ea` | `100161ea` CONDITIONAL_JUMP |
| `100161d4` | `movi.n a8,0x11` |  |
| `100161d6` | `s32i.n a8,a1,0x0` | `Stack[-0x40]` DATA |
| `100161d8` | `s32i.n a9,a1,0xc` |  |
| `100161da` | `l32r a10,0x1000699c` | `1000699c` READ |
| `100161dd` | `mov.n a11,a1` |  |
| `100161df` | `movi.n a12,0xff` |  |
| `100161e1` | `mov a1,a1` |  |
| `100161e4` | `call8 0x100180dc` | `100180dc` UNCONDITIONAL_CALL |
| `100161e7` | `s32i a7,a2,0x68` | `1002f12c` WRITE |
| `100161ea` | `l32i a9,a2,0x6c` | `1002f130` READ |
| `100161ed` | `beqz a9,0x100162aa` | `100162aa` CONDITIONAL_JUMP |
| `100161f0` | `movi.n a8,0xb` |  |
| `100161f2` | `s32i.n a8,a1,0x0` | `Stack[-0x40]` DATA |
| `100161f4` | `s32i.n a9,a1,0xc` |  |
| `100161f6` | `mov.n a10,a7` |  |
| `100161f8` | `mov a11,a1` |  |
| `100161fb` | `mov a1,a1` |  |
| `100161fe` | `call8 0x10013620` | `10013620` UNCONDITIONAL_CALL |
| `10016201` | `s32i a7,a2,0x6c` | `1002f130` WRITE |
| `10016204` | `j 0x100162aa` | `100162aa` UNCONDITIONAL_JUMP |
| `10016207` | `movi a10,0x1` |  |
| `1001620a` | `call8 0x10015dd0` | `10015dd0` UNCONDITIONAL_CALL |
| `1001620d` | `call8 0x100160a8` | `100160a8` UNCONDITIONAL_CALL |
| `10016210` | `movi.n a10,0x0` |  |
| `10016212` | `call8 0x10015df8` | `10015df8` UNCONDITIONAL_CALL |
| `10016215` | `j 0x100162aa` | `100162aa` UNCONDITIONAL_JUMP |
| `10016218` | `movi.n a8,0x2` |  |
| `1001621a` | `s32i.n a8,a1,0x14` |  |
| `1001621c` | `movi.n a8,0x16` |  |
| `1001621e` | `s32i.n a8,a1,0x10` |  |
| `10016220` | `movi a10,0x1` |  |
| `10016223` | `addi a11,a1,0x10` |  |
| `10016226` | `mov a1,a1` |  |
| `10016229` | `call8 0x10013658` | `10013658` UNCONDITIONAL_CALL |
| `1001622c` | `j 0x100162aa` | `100162aa` UNCONDITIONAL_JUMP |
| `1001622f` | `movi a10,0x1` |  |
| `10016232` | `call8 0x10015df8` | `10015df8` UNCONDITIONAL_CALL |
| `10016235` | `j 0x100162aa` | `100162aa` UNCONDITIONAL_JUMP |
| `10016238` | `l32r a8,0x10006920` | `10006920` READ |
| `1001623b` | `movi.n a9,0x0` |  |
| `1001623d` | `s8i a9,a8,0x28` | `1002f0ec` WRITE |
| `10016240` | `movi.n a9,0x1` |  |
| `10016242` | `s32i.n a9,a8,0x38` | `1002f0fc` WRITE |
| `10016244` | `movi.n a7,0x0` |  |
| `10016246` | `mov a10,a7` |  |
| `10016249` | `call8 0x10015df8` | `10015df8` UNCONDITIONAL_CALL |
| `1001624c` | `l32r a9,0x10006920` | `10006920` READ |
| `1001624f` | `l32i a8,a9,0x68` | `1002f12c` READ |
| `10016252` | `s8i a7,a9,0x28` | `1002f0ec` WRITE |
| `10016255` | `beqz.n a8,0x10016264` | `10016264` CONDITIONAL_JUMP |
| `10016257` | `l32i a8,a9,0x6c` | `1002f130` READ |
| `1001625a` | `bnez.n a8,0x1001626a` | `1001626a` CONDITIONAL_JUMP |
| `1001625c` | `l32i.n a8,a2,0xc` |  |
| `1001625e` | `s32i a8,a9,0x6c` | `1002f130` WRITE |
| `10016261` | `j 0x100162aa` | `100162aa` UNCONDITIONAL_JUMP |
| `10016264` | `l32i a8,a2,0xc` |  |
| `10016267` | `s32i a8,a9,0x68` | `1002f12c` WRITE |
| `1001626a` | `l32r a7,0x10006920` | `10006920` READ |
| `1001626d` | `l32i a8,a7,0x68` | `1002f12c` READ |
| `10016270` | `l16ui a10,a8,0x80` |  |
| `10016273` | `mov a1,a1` |  |
| `10016276` | `call8 0x100162b0` | `100162b0` UNCONDITIONAL_CALL |
| `10016279` | `s32i a10,a7,0x48` | `1002f10c` WRITE |
| `1001627c` | `call8 0x10015d14` | `10015d14` UNCONDITIONAL_CALL |
| `1001627f` | `l32i a8,a7,0x68` | `1002f12c` READ |
| `10016282` | `l32i.n a8,a8,0x0` |  |
| `10016284` | `bnei a8,0x7,0x1001628c` | `1001628c` CONDITIONAL_JUMP |
| `10016287` | `movi.n a8,0x1` |  |
| `10016289` | `s32i a8,a7,0x38` | `1002f0fc` WRITE |
| `1001628c` | `l32i.n a8,a7,0x38` | `1002f0fc` READ |
| `1001628e` | `beqz.n a8,0x100162a4` | `100162a4` CONDITIONAL_JUMP |
| `10016290` | `l32r a10,0x100069a0` | `100069a0` READ |
| `10016293` | `call8 0x10015c68` | `10015c68` UNCONDITIONAL_CALL |
| `10016296` | `l32r a8,0x10005e6c` | `10005e6c` READ |
| `10016299` | `and a2,a10,a8` |  |
| `1001629c` | `bnez.n a2,0x100162aa` | `100162aa` CONDITIONAL_JUMP |
| `1001629e` | `movi.n a8,0x1` |  |
| `100162a0` | `s32i.n a8,a7,0x38` | `1002f0fc` WRITE |
| `100162a2` | `retw.n` |  |
| `100162a4` | `l32r a10,0x100069a4` | `100069a4` READ |
| `100162a7` | `call8 0x10015c68` | `10015c68` UNCONDITIONAL_CALL |
| `100162aa` | `movi a2,0x0` |  |
| `100162ad` | `retw` |  |

## Scalar Literals

This lists small scalar literals seen in operands. It is a quick check for visible case IDs.

| Address | Literal | Instruction |
|---:|---:|---|
| `10016164` | `0x40` | `entry a1,0x40` |
| `10016167` | `0x0` | `l32i.n a8,a2,0x0` |
| `1001616c` | `0x35` | `movi.n a8,0x35` |
| `1001617a` | `0x0` | `l32i a8,a8,0x0` |
| `10016180` | `0x25` | `movi.n a8,0x25` |
| `10016182` | `0x0` | `s32i.n a8,a1,0x0` |
| `10016184` | `0x0` | `movi.n a12,0x0` |
| `10016186` | `0x4` | `s32i.n a12,a1,0x4` |
| `10016188` | `0x1` | `movi.n a10,0x1` |
| `10016192` | `0x28` | `s8i a9,a8,0x28` |
| `100161a7` | `0xe` | `movi.n a8,0xe` |
| `100161a9` | `0x0` | `s32i.n a8,a2,0x0` |
| `100161ab` | `0x1` | `movi a10,0x1` |
| `100161ba` | `0x0` | `movi a10,0x0` |
| `100161c3` | `0x0` | `extui a10,a10,0x0,0x10` |
| `100161c3` | `0x10` | `extui a10,a10,0x0,0x10` |
| `100161d4` | `0x11` | `movi.n a8,0x11` |
| `100161d6` | `0x0` | `s32i.n a8,a1,0x0` |
| `100161d8` | `0xc` | `s32i.n a9,a1,0xc` |
| `100161f0` | `0xb` | `movi.n a8,0xb` |
| `100161f2` | `0x0` | `s32i.n a8,a1,0x0` |
| `100161f4` | `0xc` | `s32i.n a9,a1,0xc` |
| `10016207` | `0x1` | `movi a10,0x1` |
| `10016210` | `0x0` | `movi.n a10,0x0` |
| `10016218` | `0x2` | `movi.n a8,0x2` |
| `1001621a` | `0x14` | `s32i.n a8,a1,0x14` |
| `1001621c` | `0x16` | `movi.n a8,0x16` |
| `1001621e` | `0x10` | `s32i.n a8,a1,0x10` |
| `10016220` | `0x1` | `movi a10,0x1` |
| `10016223` | `0x10` | `addi a11,a1,0x10` |
| `1001622f` | `0x1` | `movi a10,0x1` |
| `1001623b` | `0x0` | `movi.n a9,0x0` |
| `1001623d` | `0x28` | `s8i a9,a8,0x28` |
| `10016240` | `0x1` | `movi.n a9,0x1` |
| `10016242` | `0x38` | `s32i.n a9,a8,0x38` |
| `10016244` | `0x0` | `movi.n a7,0x0` |
| `10016252` | `0x28` | `s8i a7,a9,0x28` |
| `1001625c` | `0xc` | `l32i.n a8,a2,0xc` |
| `10016264` | `0xc` | `l32i a8,a2,0xc` |
| `10016279` | `0x48` | `s32i a10,a7,0x48` |
| `10016282` | `0x0` | `l32i.n a8,a8,0x0` |
| `10016284` | `0x7` | `bnei a8,0x7,0x1001628c` |
| `10016287` | `0x1` | `movi.n a8,0x1` |
| `10016289` | `0x38` | `s32i a8,a7,0x38` |
| `1001628c` | `0x38` | `l32i.n a8,a7,0x38` |
| `1001629e` | `0x1` | `movi.n a8,0x1` |
| `100162a0` | `0x38` | `s32i.n a8,a7,0x38` |
| `100162aa` | `0x0` | `movi a2,0x0` |

