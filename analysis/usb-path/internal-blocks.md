# HP 1020 USB2Thread Internal Blocks

These are jump-table target blocks inside `USB2Thread`, not standalone functions.

## Target `10009476`

Containing function: `none` `none`

### Depth 0 Block `10009476` - `10009483`

Outgoing block destinations:
- `10009492` via `CONDITIONAL_JUMP`
- `10009484` via `FALL_THROUGH`

Instructions:
- `10009476` `l32r a8,0x10005e68` refs=`10005e68`/READ
- `10009479` `memw`
- `1000947c` `l32i.n a9,a8,0x0` refs=`b3000408`/READ
- `1000947e` `l32r a8,0x10005ea4` refs=`10005ea4`/READ
- `10009481` `bany 0x10009492,a9,a8,` refs=`10009492`/CONDITIONAL_JUMP

### Depth 1 Block `10009492` - `100094a9`

Outgoing block destinations:
- `100094b9` via `CONDITIONAL_JUMP`
- `100094aa` via `FALL_THROUGH`

Instructions:
- `10009492` `l32r a8,0x10005f28` refs=`10005f28`/READ
- `10009495` `s32i a8,a5,0x40` refs=`10021314`/WRITE
- `10009498` `l8ui a8,a4,0x6` refs=`9002134e`/READ
- `1000949b` `movi a6,0x12`
- `1000949e` `l8ui a9,a4,0x7` refs=`9002134f`/READ
- `100094a1` `slli a8,a8,0x8`
- `100094a4` `or a9,a9,a8`
- `100094a7` `bltu a6,a9,0x100094b9` refs=`100094b9`/CONDITIONAL_JUMP

### Depth 1 Block `10009484` - `10009491`

Outgoing block destinations:
- `1000950c` via `CONDITIONAL_JUMP`
- `10009492` via `FALL_THROUGH`

Instructions:
- `10009484` `l32r a8,0x10005df4` refs=`10005df4`/READ
- `10009487` `memw`
- `1000948a` `l32i.n a8,a8,0x0` refs=`b3000400`/READ
- `1000948c` `extui a8,a8,0x0,0x2`
- `1000948f` `beqz a8,0x1000950c` refs=`1000950c`/CONDITIONAL_JUMP

### Depth 2 Block `100094b9` - `100094bb`

Outgoing block destinations:
- `100094bc` via `FALL_THROUGH`

Instructions:
- `100094b9` `movi a10,0x12`

### Depth 2 Block `100094aa` - `100094b8`

Outgoing block destinations:
- `100094bc` via `UNCONDITIONAL_JUMP`

Instructions:
- `100094aa` `l8ui a8,a4,0x6` refs=`9002134e`/READ
- `100094ad` `l8ui a9,a4,0x7` refs=`9002134f`/READ
- `100094b0` `slli a8,a8,0x8`
- `100094b3` `or a10,a9,a8`
- `100094b6` `j 0x100094bc` refs=`100094bc`/UNCONDITIONAL_JUMP

### Depth 2 Block `1000950c` - `10009522`

Outgoing block destinations:
- `10009532` via `CONDITIONAL_JUMP`
- `10009523` via `FALL_THROUGH`

Instructions:
- `1000950c` `l32r a8,0x10005f38` refs=`10005f38`/READ
- `1000950f` `s32i a8,a5,0x40` refs=`10021314`/WRITE
- `10009512` `l8ui a8,a4,0x6` refs=`9002134e`/READ
- `10009515` `movi.n a6,0x12`
- `10009517` `l8ui a9,a4,0x7` refs=`9002134f`/READ
- `1000951a` `slli a8,a8,0x8`
- `1000951d` `or a9,a9,a8`
- `10009520` `bltu a6,a9,0x10009532` refs=`10009532`/CONDITIONAL_JUMP

### Depth 3 Block `100094bc` - `1000950b`

Outgoing block destinations:
- `10009594` via `UNCONDITIONAL_JUMP`

Instructions:
- `100094bc` `l32r a9,0x10005ec0` refs=`10005ec0`/READ
- `100094bf` `l32r a8,0x10005f2c` refs=`10005f2c`/READ
- `100094c2` `s32i.n a10,a5,0x3c` refs=`10021310`/WRITE
- `100094c4` `l32r a11,0x10005ec8` refs=`10005ec8`/READ
- `100094c7` `l32r a10,0x10005ed0` refs=`10005ed0`/READ
- `100094ca` `memw`
- `100094cd` `s32i.n a8,a9,0x0` refs=`b3000508`/WRITE
- `100094cf` `l32r a9,0x10005f30` refs=`10005f30`/READ
- `100094d2` `l32r a8,0x10005f34` refs=`10005f34`/READ
- `100094d5` `memw`
- `100094d8` `s32i.n a9,a11,0x0` refs=`b3000510`/WRITE
- `100094da` `memw`
- `100094dd` `s32i.n a8,a10,0x0` refs=`b300050c`/WRITE
- `100094df` `l32r a8,0x10005e50` refs=`10005e50`/READ
- `100094e2` `l32r a9,0x10005f08` refs=`10005f08`/READ
- `100094e5` `movi.n a6,0x40`
- `100094e7` `s32i.n a6,a8,0x0` refs=`10021590`/WRITE
- `100094e9` `memw`
- `100094ec` `s32i.n a6,a9,0x0` refs=`b300022c`/WRITE
- `100094ee` `l32r a8,0x10005ee4` refs=`10005ee4`/READ
- `100094f1` `l32r a9,0x10005e9c` refs=`10005e9c`/READ
- `100094f4` `memw`
- `100094f7` `s32i.n a6,a8,0x0` refs=`b300020c`/WRITE
- `100094f9` `memw`
- `100094fc` `s32i.n a6,a9,0x0` refs=`b300000c`/WRITE
- `100094fe` `l32r a8,0x10005ee0` refs=`10005ee0`/READ
- `10009501` `l32r a9,0x10005edc` refs=`10005edc`/READ
- `10009504` `memw`
- `10009507` `s32i.n a6,a8,0x0` refs=`b300002c`/WRITE
- `10009509` `j 0x10009594` refs=`10009594`/UNCONDITIONAL_JUMP

### Depth 3 Block `10009532` - `10009533`

Outgoing block destinations:
- `10009534` via `FALL_THROUGH`

Instructions:
- `10009532` `movi.n a9,0x12`

### Depth 3 Block `10009523` - `10009531`

Outgoing block destinations:
- `10009534` via `UNCONDITIONAL_JUMP`

Instructions:
- `10009523` `l8ui a8,a4,0x6` refs=`9002134e`/READ
- `10009526` `l8ui a9,a4,0x7` refs=`9002134f`/READ
- `10009529` `slli a8,a8,0x8`
- `1000952c` `or a9,a9,a8`
- `1000952f` `j 0x10009534` refs=`10009534`/UNCONDITIONAL_JUMP

### Depth 4 Block `10009594` - `100095b2`

Outgoing block destinations:
- `10008c24` via `UNCONDITIONAL_CALL`
- `10007c70` via `UNCONDITIONAL_CALL`
- `10008fb0` via `UNCONDITIONAL_CALL`
- `1000985c` via `UNCONDITIONAL_JUMP`

Instructions:
- `10009594` `memw`
- `10009597` `s32i.n a6,a9,0x0` refs=`b3000028`/WRITE
- `10009599` `l32r a8,0x10005e50` refs=`10005e50`/READ
- `1000959c` `l32i.n a8,a8,0x0` refs=`10021590`/READ
- `1000959e` `s32i a8,a5,0x68` refs=`1002133c`/WRITE
- `100095a1` `call8 0x10008c24` refs=`10008c24`/UNCONDITIONAL_CALL, `b300050c`/PARAM, `b3000510`/PARAM, `90021340`/PARAM
- `100095a4` `l32i a10,a5,0x0` refs=`100212d4`/READ
- `100095a7` `mov a1,a1`
- `100095aa` `call8 0x10007c70` refs=`10007c70`/UNCONDITIONAL_CALL
- `100095ad` `call8 0x10008fb0` refs=`10008fb0`/UNCONDITIONAL_CALL
- `100095b0` `j 0x1000985c` refs=`1000985c`/UNCONDITIONAL_JUMP

### Depth 4 Block `10009534` - `10009593`

Outgoing block destinations:
- `10009594` via `FALL_THROUGH`

Instructions:
- `10009534` `s32i.n a9,a5,0x3c` refs=`10021310`/WRITE
- `10009536` `l32r a11,0x10005ebc` refs=`10005ebc`/READ
- `10009539` `l32r a9,0x10005c84` refs=`10005c84`/READ
- `1000953c` `l32r a10,0x10005ec0` refs=`10005ec0`/READ
- `1000953f` `l32r a8,0x10005ec4` refs=`10005ec4`/READ
- `10009542` `movi a6,0x200`
- `10009545` `memw`
- `10009548` `s32i.n a9,a11,0x0` refs=`b3000504`/WRITE
- `1000954a` `memw`
- `1000954d` `s32i.n a8,a10,0x0` refs=`b3000508`/WRITE, `100000c1`/DATA
- `1000954f` `l32r a11,0x10005ec8` refs=`10005ec8`/READ
- `10009552` `l32r a9,0x10005ecc` refs=`10005ecc`/READ
- `10009555` `l32r a10,0x10005ed0` refs=`10005ed0`/READ
- `10009558` `l32r a8,0x10005ed4` refs=`10005ed4`/READ
- `1000955b` `memw`
- `1000955e` `s32i.n a9,a11,0x0` refs=`b3000510`/WRITE, `100080c1`/DATA
- `10009560` `memw`
- `10009563` `s32i.n a8,a10,0x0` refs=`b300050c`/WRITE, `100000d1`/DATA
- `10009565` `l32r a8,0x10005e50` refs=`10005e50`/READ
- `10009568` `l32r a9,0x10005f08` refs=`10005f08`/READ
- `1000956b` `s32i.n a6,a8,0x0` refs=`10021590`/WRITE
- `1000956d` `memw`
- `10009570` `s32i.n a6,a9,0x0` refs=`b300022c`/WRITE
- `10009572` `l32r a8,0x10005ee4` refs=`10005ee4`/READ
- `10009575` `l32r a9,0x10005e9c` refs=`10005e9c`/READ
- `10009578` `movi.n a6,0x40`
- `1000957a` `memw`
- `1000957d` `s32i.n a6,a8,0x0` refs=`b300020c`/WRITE
- `1000957f` `memw`
- `10009582` `s32i.n a6,a9,0x0` refs=`b300000c`/WRITE
- `10009584` `l32r a8,0x10005ee0` refs=`10005ee0`/READ
- `10009587` `l32r a9,0x10005edc` refs=`10005edc`/READ
- `1000958a` `movi a6,0x200`
- `1000958d` `memw`
- `10009590` `s32i.n a6,a8,0x0` refs=`b300002c`/WRITE
- `10009592` `movi.n a6,0x40`

## Target `100095b3`

Containing function: `none` `none`

### Depth 0 Block `100095b3` - `100095c1`

Outgoing block destinations:
- `100095d0` via `CONDITIONAL_JUMP`
- `100095c2` via `FALL_THROUGH`

Instructions:
- `100095b3` `l32r a8,0x10005e68` refs=`10005e68`/READ
- `100095b6` `memw`
- `100095b9` `l32i a9,a8,0x0` refs=`b3000408`/READ
- `100095bc` `l32r a8,0x10005ea4` refs=`10005ea4`/READ
- `100095bf` `bany 0x100095d0,a9,a8,` refs=`100095d0`/CONDITIONAL_JUMP

### Depth 1 Block `100095d0` - `100095d5`

Outgoing block destinations:
- `100095d9` via `UNCONDITIONAL_JUMP`

Instructions:
- `100095d0` `l32r a8,0x10005f3c` refs=`10005f3c`/READ
- `100095d3` `j 0x100095d9` refs=`100095d9`/UNCONDITIONAL_JUMP

### Depth 1 Block `100095c2` - `100095cf`

Outgoing block destinations:
- `100095d6` via `CONDITIONAL_JUMP`
- `100095d0` via `FALL_THROUGH`

Instructions:
- `100095c2` `l32r a8,0x10005df4` refs=`10005df4`/READ
- `100095c5` `memw`
- `100095c8` `l32i a8,a8,0x0` refs=`b3000400`/READ
- `100095cb` `extui a8,a8,0x0,0x2`
- `100095ce` `beqz.n a8,0x100095d6` refs=`100095d6`/CONDITIONAL_JUMP

### Depth 2 Block `100095d9` - `100095ed`

Outgoing block destinations:
- `100095f1` via `CONDITIONAL_JUMP`
- `100095ee` via `FALL_THROUGH`

Instructions:
- `100095d9` `s32i a8,a5,0x40` refs=`10021314`/WRITE
- `100095dc` `l8ui a8,a4,0x6` refs=`9002134e`/READ
- `100095df` `movi a6,0x20`
- `100095e2` `l8ui a9,a4,0x7` refs=`9002134f`/READ
- `100095e5` `slli a8,a8,0x8`
- `100095e8` `or a9,a9,a8`
- `100095eb` `bltu a6,a9,0x100095f1` refs=`100095f1`/CONDITIONAL_JUMP

### Depth 2 Block `100095d6` - `100095d8`

Outgoing block destinations:
- `100095d9` via `FALL_THROUGH`

Instructions:
- `100095d6` `l32i a8,a5,0x64` refs=`10021338`/READ

### Depth 3 Block `100095f1` - `100095f5`

Outgoing block destinations:
- `100096a6` via `UNCONDITIONAL_JUMP`

Instructions:
- `100095f1` `movi.n a9,0x20`
- `100095f3` `j 0x100096a6` refs=`100096a6`/UNCONDITIONAL_JUMP

### Depth 3 Block `100095ee` - `100095f0`

Outgoing block destinations:
- `1000969a` via `UNCONDITIONAL_JUMP`

Instructions:
- `100095ee` `j 0x1000969a` refs=`1000969a`/UNCONDITIONAL_JUMP

### Depth 4 Block `100096a6` - `100096a8`

Outgoing block destinations:
- `100096a9` via `FALL_THROUGH`

Instructions:
- `100096a6` `s32i a9,a5,0x3c` refs=`10021310`/WRITE

### Depth 4 Block `1000969a` - `100096a5`

Outgoing block destinations:
- `100096a6` via `FALL_THROUGH`

Instructions:
- `1000969a` `l8ui a8,a4,0x6` refs=`9002134e`/READ
- `1000969d` `l8ui a9,a4,0x7` refs=`9002134f`/READ
- `100096a0` `slli a8,a8,0x8`
- `100096a3` `or a9,a9,a8`

## Target `100095f6`

Containing function: `none` `none`

### Depth 0 Block `100095f6` - `100095fd`

Outgoing block destinations:
- `1000961c` via `CONDITIONAL_JUMP`
- `100095fe` via `FALL_THROUGH`

Instructions:
- `100095f6` `memw`
- `100095f9` `l8ui a8,a4,0x2` refs=`9002134a`/READ
- `100095fc` `bnez.n a8,0x1000961c` refs=`1000961c`/CONDITIONAL_JUMP

### Depth 1 Block `1000961c` - `1000963c`

Outgoing block destinations:
- `10009640` via `CONDITIONAL_JUMP`
- `1000963d` via `FALL_THROUGH`

Instructions:
- `1000961c` `l32r a8,0x10005f40` refs=`10005f40`/READ
- `1000961f` `l8ui a9,a4,0x4` refs=`9002134c`/READ
- `10009622` `l16ui a8,a8,0x2` refs=`10021382`/READ
- `10009625` `slli a9,a9,0x8`
- `10009628` `srli a10,a8,0x8`
- `1000962b` `slli a8,a8,0x8`
- `1000962e` `or a10,a10,a8`
- `10009631` `l8ui a8,a4,0x5` refs=`9002134d`/READ
- `10009634` `extui a10,a10,0x0,0x10`
- `10009637` `or a8,a8,a9`
- `1000963a` `beq a10,a8,0x10009640` refs=`10009640`/CONDITIONAL_JUMP

### Depth 1 Block `100095fe` - `10009612`

Outgoing block destinations:
- `10009616` via `CONDITIONAL_JUMP`
- `10009613` via `FALL_THROUGH`

Instructions:
- `100095fe` `l32r a8,0x10005f40` refs=`10005f40`/READ
- `10009601` `s32i a8,a5,0x40` refs=`10021380`/DATA, `10021314`/WRITE
- `10009604` `l8ui a8,a4,0x6` refs=`9002134e`/READ
- `10009607` `l8ui a9,a4,0x7` refs=`9002134f`/READ
- `1000960a` `slli a8,a8,0x8`
- `1000960d` `or a9,a9,a8`
- `10009610` `bgeui a9,0x5,0x10009616` refs=`10009616`/CONDITIONAL_JUMP

### Depth 2 Block `10009640` - `1000964b`

Outgoing block destinations:
- `1000964f` via `CONDITIONAL_JUMP`
- `1000964c` via `FALL_THROUGH`

Instructions:
- `10009640` `memw`
- `10009643` `l8ui a8,a4,0x2` refs=`9002134a`/READ
- `10009646` `extui a8,a8,0x0,0x8`
- `10009649` `bltui a8,0x4,0x1000964f` refs=`1000964f`/CONDITIONAL_JUMP

### Depth 2 Block `1000963d` - `1000963f`

Outgoing block destinations:
- `10009859` via `UNCONDITIONAL_JUMP`

Instructions:
- `1000963d` `j 0x10009859` refs=`10009859`/UNCONDITIONAL_JUMP

### Depth 2 Block `10009616` - `1000961b`

Outgoing block destinations:
- `100096a6` via `UNCONDITIONAL_JUMP`

Instructions:
- `10009616` `movi a9,0x4`
- `10009619` `j 0x100096a6` refs=`100096a6`/UNCONDITIONAL_JUMP

### Depth 2 Block `10009613` - `10009615`

Outgoing block destinations:
- `1000969a` via `UNCONDITIONAL_JUMP`

Instructions:
- `10009613` `j 0x1000969a` refs=`1000969a`/UNCONDITIONAL_JUMP

### Depth 3 Block `1000964f` - `10009693`

Outgoing block destinations:
- `100169d4` via `UNCONDITIONAL_CALL`
- `10009ac4` via `COMPUTED_CALL`
- `1000969a` via `CONDITIONAL_JUMP`
- `10009694` via `FALL_THROUGH`

Instructions:
- `1000964f` `l8ui a8,a4,0x2` refs=`9002134a`/READ
- `10009652` `l32r a9,0x10005f44` refs=`10005f44`/READ
- `10009655` `addi.n a8,a8,-0x1`
- `10009657` `addx4 a8,a8,a9`
- `1000965a` `l32i.n a6,a8,0x0` refs=`100034a4`/DATA
- `1000965c` `l32r a7,0x10005f48` refs=`10005f48`/READ
- `1000965f` `mov.n a10,a6`
- `10009661` `mov a1,a1`
- `10009664` `call8 0x100169d4` refs=`100169d4`/UNCONDITIONAL_CALL
- `10009667` `slli a10,a10,0x1`
- `1000966a` `addi.n a10,a10,0x2`
- `1000966c` `s8i a10,a7,0x0` refs=`10022b70`/WRITE
- `1000966f` `movi.n a8,0x3`
- `10009671` `s8i a8,a7,0x1` refs=`10022b71`/WRITE
- `10009674` `l32r a10,0x10005f4c` refs=`10005f4c`/READ
- `10009677` `mov.n a11,a6`
- `10009679` `l32r a8,0x10005f98` refs=`10005f98`/READ
- `1000967c` `callx8 a8` refs=`10009ac4`/COMPUTED_CALL
- `1000967f` `s32i a7,a5,0x40` refs=`10022b70`/DATA, `10021314`/WRITE
- `10009682` `l8ui a9,a4,0x6` refs=`9002134e`/READ
- `10009685` `l8ui a10,a7,0x0` refs=`10022b70`/READ
- `10009688` `l8ui a8,a4,0x7` refs=`9002134f`/READ
- `1000968b` `slli a9,a9,0x8`
- `1000968e` `or a8,a8,a9`
- `10009691` `bgeu a10,a8,0x1000969a` refs=`1000969a`/CONDITIONAL_JUMP

### Depth 3 Block `1000964c` - `1000964e`

Outgoing block destinations:
- `10009859` via `UNCONDITIONAL_JUMP`

Instructions:
- `1000964c` `j 0x10009859` refs=`10009859`/UNCONDITIONAL_JUMP

### Depth 3 Block `10009859` - `1000985b`

Outgoing block destinations:
- `1000985c` via `FALL_THROUGH`

Instructions:
- `10009859` `movi a2,0x1`

### Depth 3 Block `100096a6` - `100096a8`

Outgoing block destinations:
- `100096a9` via `FALL_THROUGH`

Instructions:
- `100096a6` `s32i a9,a5,0x3c` refs=`10021310`/WRITE

### Depth 3 Block `1000969a` - `100096a5`

Outgoing block destinations:
- `100096a6` via `FALL_THROUGH`

Instructions:
- `1000969a` `l8ui a8,a4,0x6` refs=`9002134e`/READ
- `1000969d` `l8ui a9,a4,0x7` refs=`9002134f`/READ
- `100096a0` `slli a8,a8,0x8`
- `100096a3` `or a9,a9,a8`

### Depth 4 Block `100169d4` - `100169e8`

Outgoing block destinations:
- `10016a1c` via `CONDITIONAL_JUMP`
- `100169e9` via `FALL_THROUGH`

Instructions:
- `100169d4` `entry a1,0x10`
- `100169d7` `addi a3,a2,-0x4`
- `100169da` `l32r a4,0x100066b8` refs=`100066b8`/READ
- `100169dd` `l32r a5,0x10006a20` refs=`10006a20`/READ
- `100169e0` `l32r a6,0x10005f74` refs=`10005f74`/READ
- `100169e3` `l32r a7,0x10006a24` refs=`10006a24`/READ
- `100169e6` `bbsi a2,0x1f,0x10016a1c` refs=`10016a1c`/CONDITIONAL_JUMP

### Depth 4 Block `10009ac4` - `10009ac8`

Outgoing block destinations:
- `10009ac9` via `FALL_THROUGH`

Instructions:
- `10009ac4` `entry a1,0x20`
- `10009ac7` `mov.n a5,a2`

### Depth 4 Block `10009694` - `10009699`

Outgoing block destinations:
- `100096a6` via `UNCONDITIONAL_JUMP`

Instructions:
- `10009694` `mov a9,a10`
- `10009697` `j 0x100096a6` refs=`100096a6`/UNCONDITIONAL_JUMP

### Depth 4 Block `1000985c` - `1000985e`

Outgoing block destinations:
- `10009884` via `CONDITIONAL_JUMP`
- `1000985f` via `FALL_THROUGH`

Instructions:
- `1000985c` `bnei a2,0x1,0x10009884` refs=`10009884`/CONDITIONAL_JUMP

## Target `10009859`

Containing function: `none` `none`

### Depth 0 Block `10009859` - `1000985b`

Outgoing block destinations:
- `1000985c` via `FALL_THROUGH`

Instructions:
- `10009859` `movi a2,0x1`

### Depth 1 Block `1000985c` - `1000985e`

Outgoing block destinations:
- `10009884` via `CONDITIONAL_JUMP`
- `1000985f` via `FALL_THROUGH`

Instructions:
- `1000985c` `bnei a2,0x1,0x10009884` refs=`10009884`/CONDITIONAL_JUMP

### Depth 2 Block `10009884` - `1000988f`

Outgoing block destinations:
- `10009890` via `FALL_THROUGH`

Instructions:
- `10009884` `l32r a8,0x10005ee8` refs=`10005ee8`/READ
- `10009887` `l32i a8,a8,0x0` refs=`1001bbc0`/READ
- `1000988a` `memw`
- `1000988d` `s32i a3,a8,0x0` refs=`90021340`/WRITE

### Depth 2 Block `1000985f` - `10009883`

Outgoing block destinations:
- `10009884` via `FALL_THROUGH`

Instructions:
- `1000985f` `l32r a6,0x10005e24` refs=`10005e24`/READ
- `10009862` `memw`
- `10009865` `l32i.n a8,a6,0x0` refs=`b3000200`/READ
- `10009867` `l32r a9,0x10005e90` refs=`10005e90`/READ
- `1000986a` `or a8,a8,a2`
- `1000986d` `memw`
- `10009870` `s32i.n a8,a6,0x0` refs=`b3000200`/WRITE
- `10009872` `mov.n a9,a9`
- `10009874` `memw`
- `10009877` `l32i.n a8,a9,0x0` refs=`b3000000`/READ
- `10009879` `or a8,a8,a2`
- `1000987c` `memw`
- `1000987f` `s32i.n a8,a9,0x0` refs=`b3000000`/WRITE
- `10009881` `movi a2,0x0`

### Depth 3 Block `10009890` - `100098c1`

Outgoing block destinations:
- `100098f9` via `CONDITIONAL_JUMP`
- `100098c2` via `FALL_THROUGH`

Instructions:
- `10009890` `l32r a8,0x10005ef8` refs=`10005ef8`/READ
- `10009893` `memw`
- `10009896` `l32i.n a11,a8,0x0` refs=`b3000214`/READ
- `10009898` `l8ui a10,a11,0x0` refs=`90022bc0`/READ
- `1000989b` `l8ui a9,a11,0x1` refs=`90022bc1`/READ
- `1000989e` `slli a10,a10,0x18`
- `100098a1` `slli a9,a9,0x10`
- `100098a4` `l8ui a8,a11,0x2` refs=`90022bc2`/READ
- `100098a7` `or a9,a9,a10`
- `100098aa` `slli a8,a8,0x8`
- `100098ad` `l8ui a10,a11,0x3` refs=`90022bc3`/READ
- `100098b0` `or a8,a8,a9`
- `100098b3` `or a10,a10,a8`
- `100098b6` `l32r a8,0x10005e30` refs=`10005e30`/READ
- `100098b9` `l32r a9,0x10005e34` refs=`10005e34`/READ
- `100098bc` `and a8,a10,a8`
- `100098bf` `bne a8,a9,0x100098f9` refs=`100098f9`/CONDITIONAL_JUMP

### Depth 4 Block `100098f9` - `10009916`

Outgoing block destinations:
- `10009928` via `CONDITIONAL_JUMP`
- `10009917` via `FALL_THROUGH`

Instructions:
- `100098f9` `l32r a6,0x10005e24` refs=`10005e24`/READ
- `100098fc` `movi a10,0x100`
- `100098ff` `l32r a9,0x10005e38` refs=`10005e38`/READ
- `10009902` `memw`
- `10009905` `l32i.n a8,a6,0x0` refs=`b3000200`/READ
- `10009907` `l32i.n a9,a9,0x0` refs=`1001bc50`/READ
- `10009909` `or a8,a8,a10`
- `1000990c` `memw`
- `1000990f` `s32i.n a8,a6,0x0` refs=`b3000200`/WRITE
- `10009911` `movi a6,0x200`
- `10009914` `bltu a6,a9,0x10009928` refs=`10009928`/CONDITIONAL_JUMP

### Depth 4 Block `100098c2` - `100098f8`

Outgoing block destinations:
- `100098f9` via `FALL_THROUGH`

Instructions:
- `100098c2` `l32r a8,0x10005eec` refs=`10005eec`/READ
- `100098c5` `l32i.n a8,a8,0x0` refs=`1001bc60`/READ
- `100098c7` `memw`
- `100098ca` `l8ui a9,a8,0x0` refs=`90022bc0`/READ
- `100098cd` `movi.n a9,0x8`
- `100098cf` `memw`
- `100098d2` `s8i a9,a8,0x0` refs=`90022bc0`/WRITE
- `100098d5` `memw`
- `100098d8` `l8ui a9,a8,0x1` refs=`90022bc1`/READ
- `100098db` `memw`
- `100098de` `s8i a3,a8,0x1` refs=`90022bc1`/WRITE
- `100098e1` `memw`
- `100098e4` `l8ui a9,a8,0x2` refs=`90022bc2`/READ
- `100098e7` `memw`
- `100098ea` `s8i a3,a8,0x2` refs=`90022bc2`/WRITE
- `100098ed` `memw`
- `100098f0` `l8ui a9,a8,0x3` refs=`90022bc3`/READ
- `100098f3` `memw`
- `100098f6` `s8i a3,a8,0x3` refs=`90022bc3`/WRITE

## Target `100096af`

Containing function: `none` `none`

### Depth 0 Block `100096af` - `100096c5`

Outgoing block destinations:
- `100096d5` via `CONDITIONAL_JUMP`
- `100096c6` via `FALL_THROUGH`

Instructions:
- `100096af` `l32r a8,0x10005f50` refs=`10005f50`/READ
- `100096b2` `s32i a8,a5,0x40` refs=`1001bbd0`/DATA, `10021314`/WRITE
- `100096b5` `l8ui a8,a4,0x6` refs=`9002134e`/READ
- `100096b8` `l8ui a9,a4,0x7` refs=`9002134f`/READ
- `100096bb` `slli a8,a8,0x8`
- `100096be` `or a9,a9,a8`
- `100096c1` `movi.n a8,0xa`
- `100096c3` `bltu a8,a9,0x100096d5` refs=`100096d5`/CONDITIONAL_JUMP

### Depth 1 Block `100096d5` - `100096d7`

Outgoing block destinations:
- `100096d8` via `FALL_THROUGH`

Instructions:
- `100096d5` `mov a10,a8`

### Depth 1 Block `100096c6` - `100096d4`

Outgoing block destinations:
- `100096d8` via `UNCONDITIONAL_JUMP`

Instructions:
- `100096c6` `l8ui a8,a4,0x6` refs=`9002134e`/READ
- `100096c9` `l8ui a9,a4,0x7` refs=`9002134f`/READ
- `100096cc` `slli a8,a8,0x8`
- `100096cf` `or a10,a9,a8`
- `100096d2` `j 0x100096d8` refs=`100096d8`/UNCONDITIONAL_JUMP

### Depth 2 Block `100096d8` - `100096e4`

Outgoing block destinations:
- `100096a9` via `UNCONDITIONAL_JUMP`

Instructions:
- `100096d8` `s32i.n a10,a5,0x3c` refs=`10021310`/WRITE
- `100096da` `l32r a8,0x10005f50` refs=`10005f50`/READ
- `100096dd` `movi.n a6,0x40`
- `100096df` `s8i a6,a8,0x7` refs=`1001bbd7`/WRITE
- `100096e2` `j 0x100096a9` refs=`100096a9`/UNCONDITIONAL_JUMP

### Depth 3 Block `100096a9` - `100096ae`

Outgoing block destinations:
- `10008c24` via `UNCONDITIONAL_CALL`
- `1000985c` via `UNCONDITIONAL_JUMP`

Instructions:
- `100096a9` `call8 0x10008c24` refs=`10008c24`/UNCONDITIONAL_CALL, `90021340`/PARAM
- `100096ac` `j 0x1000985c` refs=`1000985c`/UNCONDITIONAL_JUMP

### Depth 4 Block `10008c24` - `10008c4e`

Outgoing block destinations:
- `100173c8` via `UNCONDITIONAL_CALL`
- `10008c59` via `CONDITIONAL_JUMP`
- `10008c4f` via `FALL_THROUGH`

Instructions:
- `10008c24` `entry a1,0x30`
- `10008c27` `l32r a8,0x10005e1c` refs=`10005e1c`/READ
- `10008c2a` `l32r a4,0x10005e90` refs=`10005e90`/READ
- `10008c2d` `l32i a10,a8,0x40` refs=`10021314`/READ
- `10008c30` `l32i.n a11,a8,0x3c` refs=`10021310`/READ
- `10008c32` `memw`
- `10008c35` `l32i.n a8,a4,0x0` refs=`b3000000`/READ
- `10008c37` `movi.n a2,0x2`
- `10008c39` `or a8,a8,a2`
- `10008c3c` `memw`
- `10008c3f` `s32i.n a8,a4,0x0` refs=`b3000000`/WRITE
- `10008c41` `mov a1,a1`
- `10008c44` `call8 0x100173c8` refs=`100173c8`/UNCONDITIONAL_CALL
- `10008c47` `memw`
- `10008c4a` `l32i.n a8,a4,0x0` refs=`b3000000`/READ
- `10008c4c` `bnone 0x10008c59,a8,a2,` refs=`10008c59`/CONDITIONAL_JUMP

### Depth 4 Block `1000985c` - `1000985e`

Outgoing block destinations:
- `10009884` via `CONDITIONAL_JUMP`
- `1000985f` via `FALL_THROUGH`

Instructions:
- `1000985c` `bnei a2,0x1,0x10009884` refs=`10009884`/CONDITIONAL_JUMP

## Target `100096e5`

Containing function: `none` `none`

### Depth 0 Block `100096e5` - `100096fc`

Outgoing block destinations:
- `1000970c` via `CONDITIONAL_JUMP`
- `100096fd` via `FALL_THROUGH`

Instructions:
- `100096e5` `l32r a6,0x10005f54` refs=`10005f54`/READ
- `100096e8` `s32i a6,a5,0x40` refs=`1001bc20`/DATA, `10021314`/WRITE
- `100096eb` `l8ui a8,a4,0x6` refs=`9002134e`/READ
- `100096ee` `movi a6,0x20`
- `100096f1` `l8ui a9,a4,0x7` refs=`9002134f`/READ
- `100096f4` `slli a8,a8,0x8`
- `100096f7` `or a9,a9,a8`
- `100096fa` `bltu a6,a9,0x1000970c` refs=`1000970c`/CONDITIONAL_JUMP

### Depth 1 Block `1000970c` - `1000970d`

Outgoing block destinations:
- `1000970e` via `FALL_THROUGH`

Instructions:
- `1000970c` `movi.n a10,0x20`

### Depth 1 Block `100096fd` - `1000970b`

Outgoing block destinations:
- `1000970e` via `UNCONDITIONAL_JUMP`

Instructions:
- `100096fd` `l8ui a8,a4,0x6` refs=`9002134e`/READ
- `10009700` `l8ui a9,a4,0x7` refs=`9002134f`/READ
- `10009703` `slli a8,a8,0x8`
- `10009706` `or a10,a9,a8`
- `10009709` `j 0x1000970e` refs=`1000970e`/UNCONDITIONAL_JUMP

### Depth 2 Block `1000970e` - `1000971d`

Outgoing block destinations:
- `1000973c` via `CONDITIONAL_JUMP`
- `1000971e` via `FALL_THROUGH`

Instructions:
- `1000970e` `l32r a8,0x10005e68` refs=`10005e68`/READ
- `10009711` `memw`
- `10009714` `l32i.n a9,a8,0x0` refs=`b3000408`/READ
- `10009716` `l32r a8,0x10005ea4` refs=`10005ea4`/READ
- `10009719` `s32i.n a10,a5,0x3c` refs=`10021310`/WRITE
- `1000971b` `bnone 0x1000973c,a9,a8,` refs=`1000973c`/CONDITIONAL_JUMP

### Depth 3 Block `1000973c` - `10009757`

Outgoing block destinations:
- `100096a9` via `UNCONDITIONAL_JUMP`

Instructions:
- `1000973c` `l32r a8,0x10005f5c` refs=`10005f5c`/READ
- `1000973f` `l32r a6,0x10005f54` refs=`10005f54`/READ
- `10009742` `l32r a9,0x10005f58` refs=`10005f58`/READ
- `10009745` `s16i a8,a6,0x16` refs=`1001bc36`/WRITE
- `10009748` `l32i.n a8,a6,0x1c` refs=`1001bc3c`/READ
- `1000974a` `l32r a10,0x10005f60` refs=`10005f60`/READ
- `1000974d` `and a8,a8,a9`
- `10009750` `or a8,a8,a10`
- `10009753` `s32i.n a8,a6,0x1c` refs=`1001bc3c`/WRITE
- `10009755` `j 0x100096a9` refs=`100096a9`/UNCONDITIONAL_JUMP

### Depth 3 Block `1000971e` - `1000973b`

Outgoing block destinations:
- `100096a9` via `UNCONDITIONAL_JUMP`

Instructions:
- `1000971e` `movi.n a8,0x2`
- `10009720` `l32r a6,0x10005f54` refs=`10005f54`/READ
- `10009723` `l32r a10,0x10005f58` refs=`10005f58`/READ
- `10009726` `l32i.n a9,a6,0x1c` refs=`1001bc3c`/READ
- `10009728` `s16i a8,a6,0x16` refs=`1001bc36`/WRITE
- `1000972b` `and a9,a9,a10`
- `1000972e` `movi a6,0x200`
- `10009731` `or a9,a9,a6`
- `10009734` `l32r a6,0x10005f54` refs=`10005f54`/READ
- `10009737` `s32i.n a9,a6,0x1c` refs=`1001bc3c`/WRITE
- `10009739` `j 0x100096a9` refs=`100096a9`/UNCONDITIONAL_JUMP

### Depth 4 Block `100096a9` - `100096ae`

Outgoing block destinations:
- `10008c24` via `UNCONDITIONAL_CALL`
- `1000985c` via `UNCONDITIONAL_JUMP`

Instructions:
- `100096a9` `call8 0x10008c24` refs=`10008c24`/UNCONDITIONAL_CALL, `90021340`/PARAM
- `100096ac` `j 0x1000985c` refs=`1000985c`/UNCONDITIONAL_JUMP

