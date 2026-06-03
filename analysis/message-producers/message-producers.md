# HP 1020 Message Producer Trace

This report extracts switch cases, message-ID assignments, and queue-send call sites from the decompiled print/job/status/video/engine neighborhood.

## Functions With Message Activity

- `10008c24` `FUN_10008c24`: cases `0`, interesting assignments `1`, send/receive sites `0`
- `1000aec0` `FUN_1000aec0`: cases `0`, interesting assignments `2`, send/receive sites `0`
- `1000b870` `FUN_1000b870`: cases `12`, interesting assignments `0`, send/receive sites `0`
- `1000c89c` `FUN_1000c89c`: cases `0`, interesting assignments `1`, send/receive sites `0`
- `1000c8fc` `FUN_1000c8fc`: cases `20`, interesting assignments `4`, send/receive sites `0`
- `1000e414` `hp1020_job_mgr_thread_candidate`: cases `15`, interesting assignments `3`, send/receive sites `8`
- `1000ed4c` `FUN_1000ed4c`: cases `0`, interesting assignments `0`, send/receive sites `1`
- `1000ed90` `FUN_1000ed90`: cases `0`, interesting assignments `2`, send/receive sites `2`
- `1000eeb8` `FUN_1000eeb8`: cases `0`, interesting assignments `0`, send/receive sites `1`
- `1000f164` `FUN_1000f164`: cases `0`, interesting assignments `0`, send/receive sites `1`
- `1000f324` `hp1020_print_mgr_thread_candidate`: cases `0`, interesting assignments `1`, send/receive sites `2`
- `1000f574` `FUN_1000f574`: cases `4`, interesting assignments `1`, send/receive sites `0`
- `1000f814` `FUN_1000f814`: cases `0`, interesting assignments `0`, send/receive sites `1`
- `1000fcb0` `FUN_1000fcb0`: cases `0`, interesting assignments `2`, send/receive sites `0`
- `10010170` `FUN_10010170`: cases `0`, interesting assignments `0`, send/receive sites `1`
- `10010218` `FUN_10010218`: cases `0`, interesting assignments `0`, send/receive sites `1`
- `10010338` `FUN_10010338`: cases `0`, interesting assignments `0`, send/receive sites `1`
- `10010398` `FUN_10010398`: cases `0`, interesting assignments `0`, send/receive sites `2`
- `100103f8` `FUN_100103f8`: cases `0`, interesting assignments `0`, send/receive sites `1`
- `1001040c` `FUN_1001040c`: cases `0`, interesting assignments `0`, send/receive sites `1`
- `10010590` `hp1020_status_mgr_thread_candidate`: cases `8`, interesting assignments `0`, send/receive sites `2`
- `10010838` `FUN_10010838`: cases `0`, interesting assignments `3`, send/receive sites `1`
- `10010c98` `FUN_10010c98`: cases `0`, interesting assignments `0`, send/receive sites `1`
- `10010cf0` `FUN_10010cf0`: cases `0`, interesting assignments `0`, send/receive sites `1`
- `10010f54` `FUN_10010f54`: cases `5`, interesting assignments `0`, send/receive sites `0`
- `10010fd0` `FUN_10010fd0`: cases `10`, interesting assignments `0`, send/receive sites `0`
- `10011258` `hp1020_register_event_handler_candidate`: cases `0`, interesting assignments `0`, send/receive sites `1`
- `10013140` `FUN_10013140`: cases `0`, interesting assignments `0`, send/receive sites `1`
- `10013620` `hp1020_send_or_raise_engine_msg_candidate`: cases `0`, interesting assignments `0`, send/receive sites `2`
- `10013658` `hp1020_queue_send_candidate`: cases `0`, interesting assignments `0`, send/receive sites `2`
- `10013668` `FUN_10013668`: cases `0`, interesting assignments `0`, send/receive sites `1`
- `10013c18` `hp1020_video_thread_candidate`: cases `0`, interesting assignments `1`, send/receive sites `2`
- `10013d4c` `hp1020_video_reset_dispatch_candidate`: cases `8`, interesting assignments `4`, send/receive sites `3`
- `10014910` `hp1020_video_prepare_page_candidate`: cases `0`, interesting assignments `1`, send/receive sites `0`
- `10015c68` `hp1020_engine_read_or_write_status_candidate`: cases `0`, interesting assignments `1`, send/receive sites `1`
- `10015df8` `hp1020_engine_status_poll_candidate`: cases `3`, interesting assignments `2`, send/receive sites `2`
- `100160a8` `hp1020_engine_preflight_candidate`: cases `0`, interesting assignments `2`, send/receive sites `2`
- `10016164` `hp1020_engine_message_dispatch_candidate`: cases `8`, interesting assignments `5`, send/receive sites `4`
- `10016318` `FUN_10016318`: cases `5`, interesting assignments `1`, send/receive sites `0`
- `1001635c` `hp1020_engine_delay_thread_candidate`: cases `0`, interesting assignments `0`, send/receive sites `2`
- `100163b0` `hp1020_engine_thread_candidate`: cases `0`, interesting assignments `1`, send/receive sites `8`
- `100165a4` `hp1020_engine_register_handlers_candidate`: cases `0`, interesting assignments `4`, send/receive sites `0`
- `10016b50` `FUN_10016b50`: cases `0`, interesting assignments `1`, send/receive sites `0`
- `100176c8` `FUN_100176c8`: cases `0`, interesting assignments `4`, send/receive sites `0`
- `1001809c` `threadx_queue_receive_wait_candidate`: cases `0`, interesting assignments `0`, send/receive sites `1`
- `1001a130` `FUN_1001a130`: cases `0`, interesting assignments `1`, send/receive sites `0`
- `1001a478` `FUN_1001a478`: cases `0`, interesting assignments `1`, send/receive sites `0`

## Switch Cases

### `1000b870` `FUN_1000b870`

- cases: `0`, `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`, `10`, `0xb`

### `1000c8fc` `FUN_1000c8fc`

- cases: `0`, `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`, `10`, `0xb`, `0xc`, `0xd`, `0xe`, `0xf`, `0x10`, `0x11`, `0x12`, `0x13`

### `1000e414` `hp1020_job_mgr_thread_candidate`

- cases: `1`, `2`, `3`, `5`, `6`, `8`, `0x2b`, `9`, `0xf`, `0x11`, `0x21`, `0x25`, `0x29`, `0x2a`, `0x33`

### `1000f574` `FUN_1000f574`

- cases: `0`, `2`, `4`, `7`

### `10010590` `hp1020_status_mgr_thread_candidate`

- cases: `0xf`, `0x2c`, `0x2e`, `0x2f`, `0x30`, `0x31`, `0x32`, `0x43`

### `10010f54` `FUN_10010f54`

- cases: `0`, `1`, `2`, `3`, `4`

### `10010fd0` `FUN_10010fd0`

- cases: `0`, `1`, `2`, `3`, `4`, `0`, `1`, `2`, `3`, `4`

### `10013d4c` `hp1020_video_reset_dispatch_candidate`

- cases: `0`, `1`, `2`, `7`, `3`, `4`, `5`, `6`

### `10015df8` `hp1020_engine_status_poll_candidate`

- cases: `0x10`, `0x14`, `0x18`

### `10016164` `hp1020_engine_message_dispatch_candidate`

- cases: `0xd`, `0xf`, `0x11`, `0x18`, `0x19`, `0x1a`, `0x40`, `0xb`

### `10016318` `FUN_10016318`

- cases: `1`, `2`, `3`, `4`, `5`

## Interesting Message Assignments

### `10008c24` `FUN_10008c24`

- line `88`: `iVar8 = 0x10` from `iVar8 = 0x10;`

### `1000aec0` `FUN_1000aec0`

- line `12`: `local_50 = 0xf` from `local_50 = 0xf;`
- line `17`: `local_50 = 0xd` from `local_50 = 0xd;`

### `1000c89c` `FUN_1000c89c`

- line `25`: `local_40 = 0xf` from `local_40 = 0xf;`

### `1000c8fc` `FUN_1000c8fc`

- line `96` case `3`: `local_b0 = 0x25` from `local_b0 = 0x25;`
- line `122` case `5`: `local_b0 = 0xd` from `local_b0 = 0xd;`
- line `147` case `0xb`: `local_b0 = 0x10` from `local_b0 = 0x10;`
- line `150` case `0xb`: `local_b0 = 0x11` from `local_b0 = 0x11;`

### `1000e414` `hp1020_job_mgr_thread_candidate`

- line `225` case `0xf`: `uStack_90 = 0xf` from `uStack_90 = 0xf;`
- line `249` case `0xf`: `uStack_80 = 0x25` from `uStack_80 = 0x25;`
- line `348` case `0x21`: `uStack_90 = 0xb` from `uStack_90 = 0xb;`

### `1000ed90` `FUN_1000ed90`

- line `38`: `local_30[0] = 0xb` from `local_30[0] = 0xb;`
- line `56`: `local_30[0] = 0xb` from `local_30[0] = 0xb;`

### `1000f324` `hp1020_print_mgr_thread_candidate`

- line `11`: `aiStack_50[0] = 0x18` from `aiStack_50[0] = 0x18;`

### `1000f574` `FUN_1000f574`

- line `158` case `7`: `uVar13 = 0xd` from `uVar13 = 0xd;`

### `1000fcb0` `FUN_1000fcb0`

- line `68`: `uVar7 = 0x1a` from `uVar7 = 0x1a;`
- line `75`: `uVar7 = 0xf` from `uVar7 = 0xf;`

### `10010838` `FUN_10010838`

- line `106`: `local_50 = 0x18` from `local_50 = 0x18;`
- line `119`: `uStack_40 = 0xf` from `uStack_40 = 0xf;`
- line `133`: `local_50 = 0x19` from `local_50 = 0x19;`

### `10013c18` `hp1020_video_thread_candidate`

- line `67`: `aiStack_30[0] = 0x10` from `aiStack_30[0] = 0x10;`

### `10013d4c` `hp1020_video_reset_dispatch_candidate`

- line `83` case `0`: `local_30 = 0x11` from `local_30 = 0x11;`
- line `90` case `0`: `local_30 = 0xb` from `local_30 = 0xb;`
- line `96` case `1`: `local_30 = 0x25` from `local_30 = 0x25;`
- line `119` case `6`: `local_30 = 0x17` from `local_30 = 0x17;`

### `10014910` `hp1020_video_prepare_page_candidate`

- line `520`: `uVar19 = 0x10` from `uVar19 = 0x10;`

### `10015c68` `hp1020_engine_read_or_write_status_candidate`

- line `52`: `uStack_30 = 0x17` from `uStack_30 = 0x17;`

### `10015df8` `hp1020_engine_status_poll_candidate`

- line `97` case `0x18`: `local_40 = 0x17` from `local_40 = 0x17;`
- line `112` case `0x18`: `local_40 = 0x17` from `local_40 = 0x17;`

### `100160a8` `hp1020_engine_preflight_candidate`

- line `20`: `local_40 = 0x17` from `local_40 = 0x17;`
- line `53`: `uStack_30 = 0x17` from `uStack_30 = 0x17;`

### `10016164` `hp1020_engine_message_dispatch_candidate`

- line `18` case `0xd`: `param_1 = 0xe` from `*param_1 = 0xe;`
- line `22` case `0xf`: `local_40 = 0x25` from `local_40 = 0x25;`
- line `36` case `0x11`: `local_40 = 0x11` from `local_40 = 0x11;`
- line `42` case `0x11`: `local_40 = 0xb` from `local_40 = 0xb;`
- line `53` case `0x19`: `uStack_30 = 0x16` from `uStack_30 = 0x16;`

### `10016318` `FUN_10016318`

- line `13` case `2`: `uVar1 = 0x10` from `uVar1 = 0x10;`

### `100163b0` `hp1020_engine_thread_candidate`

- line `32`: `uStack_30 = 0x16` from `uStack_30 = 0x16;`

### `100165a4` `hp1020_engine_register_handlers_candidate`

- line `81`: `puVar7 = 0xb` from `*puVar7 = 0xb;`
- line `82`: `puVar5 = 0xd` from `*puVar5 = 0xd;`
- line `86`: `puVar1 = 0x25` from `*puVar1 = 0x25;`
- line `109`: `uStack_c4 = 0xe` from `uStack_c4 = 0xe;`

### `10016b50` `FUN_10016b50`

- line `38`: `param_4 = 0x10` from `param_4 = 0x10;`

### `100176c8` `FUN_100176c8`

- line `48`: `iVar8 = 0x18` from `iVar8 = 0x18;`
- line `52`: `iVar8 = 0x10` from `iVar8 = 0x10;`
- line `82`: `iVar8 = 0x18` from `iVar8 = 0x18;`
- line `86`: `iVar8 = 0x10` from `iVar8 = 0x10;`

### `1001a130` `FUN_1001a130`

- line `47`: `uVar2 = 0xb` from `uVar2 = 0xb;`

### `1001a478` `FUN_1001a478`

- line `44`: `uVar2 = 0xd` from `uVar2 = 0xd;`

## Queue Send/Receive Sites

### `1000e414` `hp1020_job_mgr_thread_candidate`

#### line `42` `threadx_queue_receive_wait_candidate`

Nearby decompiler context:

```c
int *piStack_4c;
int iStack_40;
undefined4 uStack_3c;
int iStack_38;
char cStack_21;
uVar16 = 0;
FUN_1001214c();
switchD_1000e461_caseD_4:
while( true ) {
uVar16 = uVar16 & 0xffffcfff;
iVar8 = threadx_queue_receive_wait_candidate(PTR_DAT_100062d0,&uStack_90,2);
```

#### line `227` `hp1020_queue_send_candidate` case `0xf`

Nearby decompiler context:

```c
iVar9 = *(int *)(iVar15 + 0x4c);
if (*(int *)(iVar15 + 0x48) != 0) {
iVar9 = *(int *)(iVar15 + 0x48);
}
if (iVar9 != 0) {
*puVar4 = *(undefined1 *)(iVar9 + 0x75);
}
if (((iVar15 != 0) && (iVar9 != 0)) && (*(short *)(iVar9 + 0x48) != 0)) {
uStack_90 = 0xf;
uVar16 = uVar16 & 0xffffcfff;
hp1020_queue_send_candidate(1,&uStack_90);
```

#### line `243` `hp1020_queue_send_candidate` case `0xf`

Nearby decompiler context:

```c
if (iVar15 == 1) {
uStack_88 = (uint)(byte)*PTR_DAT_10006314;
if ((iVar9 != 0) && (*(short *)(iVar9 + 0x4a) == 0)) {
uStack_88 = 1;
}
if ((*(int *)PTR_DAT_10006308 == 2) || (*(int *)PTR_DAT_10006308 == 4)) {
uStack_88 = 0;
}
*PTR_DAT_10006318 = (undefined1)uStack_88;
uVar16 = uVar16 & 0xffffcfff;
hp1020_queue_send_candidate(*(undefined4 *)(iVar8 + 100),&uStack_90);
```

#### line `251` `hp1020_queue_send_candidate` case `0xf`

Nearby decompiler context:

```c
*PTR_DAT_10006318 = (undefined1)uStack_88;
uVar16 = uVar16 & 0xffffcfff;
hp1020_queue_send_candidate(*(undefined4 *)(iVar8 + 100),&uStack_90);
*PTR_DAT_1000630c = *PTR_DAT_1000630c + '\x01';
}
cVar11 = *PTR_DAT_1000630c;
*PTR_DAT_1000631c = 0;
if (cVar11 == '\0') {
uStack_80 = 0x25;
uVar16 = uVar16 & 0xffffcfff;
hp1020_queue_send_candidate(3,&uStack_80);
```

#### line `262` `hp1020_queue_send_candidate` case `0x11`

Nearby decompiler context:

```c
}
}
}
goto switchD_1000e461_caseD_4;
case 0x11:
iVar9 = *(int *)(*(int *)PTR_DAT_100062e4 + 0xc);
*(short *)(iVar9 + 0x6c) = *(short *)(iVar9 + 0x6c) + 1;
piVar12 = *(int **)(*(int *)(*(int *)puVar4 + 0xc) + 0x70);
if (*(int *)(iVar9 + 0x60) == 1) {
uVar16 = uVar16 & 0xffffcfff;
hp1020_queue_send_candidate(*(undefined4 *)(iVar9 + 100),&uStack_90);
```

#### line `270` `hp1020_queue_send_candidate` case `0x11`

Nearby decompiler context:

```c
if (*(int *)(iVar9 + 0x60) == 1) {
uVar16 = uVar16 & 0xffffcfff;
hp1020_queue_send_candidate(*(undefined4 *)(iVar9 + 100),&uStack_90);
}
if (*(int *)(iVar9 + 0x5c) == 1) {
uStack_80 = 0x31;
uStack_7c = (uint)*(ushort *)(iVar9 + 0x6c);
uStack_78 = *(undefined4 *)(iVar9 + 0x58);
uStack_74 = *(undefined4 *)(iVar9 + 0x48);
uVar16 = uVar16 & 0xffffcfff;
hp1020_queue_send_candidate(10,&uStack_80);
```

#### line `354` `hp1020_queue_send_candidate` case `0x21`

Nearby decompiler context:

```c
*(short *)(iVar9 + 0x48) == 0)))) {
uVar16 = uVar16 & 0xffffcfff;
FUN_1000f0a8(iVar9 + 0x50,3);
if (*(int *)PTR_DAT_10006308 == 0) {
uStack_90 = 0xb;
*(undefined2 *)(iVar9 + 0x48) = 1;
*(undefined2 *)(iVar9 + 0xc) = 1;
*(undefined2 *)(iVar9 + 0x72) = 1;
uVar16 = uVar16 & 0xffffcfff;
iStack_84 = iVar9;
hp1020_queue_send_candidate(1,&uStack_90);
```

#### line `372` `hp1020_queue_send_candidate` case `0x25`

Nearby decompiler context:

```c
(cVar11 = *PTR_DAT_1000631c, *PTR_DAT_1000631c = cVar11 + 1U,
(byte)*puVar7 <= (byte)(cVar11 + 1U))))) {
iVar9 = *(int *)PTR_DAT_10006308;
*PTR_DAT_1000630c = 0;
if (iVar9 == 2) {
uStack_80 = 0x30;
uStack_7c = 0;
uStack_78 = *(undefined4 *)(*(int *)(*(int *)PTR_DAT_100062e4 + 0xc) + 0x58);
uStack_74 = *(undefined4 *)(*(int *)(*(int *)PTR_DAT_100062e4 + 0xc) + 0x48);
uVar16 = uVar16 & 0xffffcfff;
hp1020_queue_send_candidate(10,&uStack_80);
```

### `1000ed4c` `FUN_1000ed4c`

#### line `21` `hp1020_queue_send_candidate`

Nearby decompiler context:

```c
*(undefined2 *)(piStack_24 + 3) = *(undefined2 *)(*(int *)(param_1 + 0xc) + 0x6c);
iVar1 = *(int *)(*(int *)(param_1 + 0xc) + 0x48);
*piStack_24 = iVar1;
piStack_24[2] = (uint)*(byte *)(*(int *)(param_1 + 0xc) + 0x6a);
if (iVar1 == 0) {
piStack_24[1] = 0;
}
else {
piStack_24[1] = *(int *)(*(int *)(param_1 + 0xc) + 0x58);
}
hp1020_queue_send_candidate(10,local_30);
```

### `1000ed90` `FUN_1000ed90`

#### line `40` `hp1020_queue_send_candidate`

Nearby decompiler context:

```c
if (uVar4 < uVar1) {
uVar4 = uVar1;
}
if (*(ushort *)(iVar7 + 0x48) != uVar1) {
do {
if (*(short *)puVar2 == 0) break;
*(short *)puVar2 = *(short *)puVar2 + -1;
*(short *)(iVar7 + 0x48) = *(short *)(iVar7 + 0x48) + 1;
local_30[0] = 0xb;
uStack_24 = *(undefined4 *)(iVar6 + 0x48);
hp1020_queue_send_candidate(1,local_30);
```

#### line `58` `hp1020_queue_send_candidate`

Nearby decompiler context:

```c
if (uVar4 < uVar1) {
uVar4 = uVar1;
}
if (*(ushort *)(iVar7 + 0x48) != uVar1) {
do {
if (*(short *)puVar2 == 0) break;
*(short *)puVar2 = *(short *)puVar2 + -1;
*(short *)(iVar7 + 0x48) = *(short *)(iVar7 + 0x48) + 1;
local_30[0] = 0xb;
uStack_24 = *(undefined4 *)(iVar6 + 0x4c);
hp1020_queue_send_candidate(1,local_30);
```

### `1000eeb8` `FUN_1000eeb8`

#### line `30` `hp1020_queue_send_candidate`

Nearby decompiler context:

```c
*(undefined2 *)(piStack_34 + 3) = *(undefined2 *)(param_1 + 0x6c);
iVar2 = *(int *)(param_1 + 0x48);
*piStack_34 = iVar2;
piStack_34[2] = (uint)*(byte *)(param_1 + 0x6a);
if (iVar2 == 0) {
piStack_34[1] = 0;
}
else {
piStack_34[1] = aiStack_30[0];
}
hp1020_queue_send_candidate(10,auStack_40);
```

### `1000f164` `FUN_1000f164`

#### line `25` `hp1020_queue_send_candidate`

Nearby decompiler context:

```c
auStack_30[0] = *(undefined4 *)(param_1 + 0x5c);
FUN_10010fd0(&uStack_40);
uStack_40 = 0x1c;
puStack_3c = auStack_30;
FUN_10010f54(&uStack_40);
auStack_30[0] = *(undefined4 *)(param_1 + 0x58);
FUN_10010fd0(&uStack_40);
local_50[0] = 0x2e;
uStack_48 = *(undefined4 *)(param_1 + 0x58);
uStack_44 = *(undefined4 *)(param_1 + 0x48);
hp1020_queue_send_candidate(10,local_50);
```

### `1000f324` `hp1020_print_mgr_thread_candidate`

#### line `12` `hp1020_queue_send_candidate`

Nearby decompiler context:

```c
void hp1020_print_mgr_thread_candidate(undefined4 param_1,undefined4 param_2)
{
undefined *puVar1;
int aiStack_50 [20];
FUN_1001214c();
FUN_1001135c(0x18,1);
FUN_1001135c(1,1);
aiStack_50[0] = 0x18;
hp1020_queue_send_candidate(0,aiStack_50);
```

#### line `15` `threadx_queue_receive_wait_candidate`

Nearby decompiler context:

```c
{
undefined *puVar1;
int aiStack_50 [20];
FUN_1001214c();
FUN_1001135c(0x18,1);
FUN_1001135c(1,1);
aiStack_50[0] = 0x18;
hp1020_queue_send_candidate(0,aiStack_50);
puVar1 = PTR_DAT_10006338;
do {
threadx_queue_receive_wait_candidate(PTR_DAT_1000632c,aiStack_50,0xffffffff);
```

### `1000f814` `FUN_1000f814`

#### line `14` `hp1020_queue_send_candidate`

Nearby decompiler context:

```c
void FUN_1000f814(undefined4 param_1)
{
undefined4 *puVar1;
if (*(int *)(PTR_DAT_10006338 + 4) == 0) {
PTR_DAT_10006338[2] = PTR_DAT_10006338[2] + '\x01';
}
puVar1 = (undefined4 *)FUN_10013050(PTR_DAT_10006328);
puVar1[3] = 0;
*puVar1 = 0;
FUN_10013408();
hp1020_queue_send_candidate(3,param_1);
```

### `10010170` `FUN_10010170`

#### line `31` `hp1020_queue_send_candidate`

Nearby decompiler context:

```c
/* WARNING: Could not recover jumptable at 0x100101a9. Too many branches */
/* WARNING: Treating indirect jump as call */
(**(code **)(PTR_switchdataD_10004a00_100063a4 + (*(int *)(PTR_DAT_10006344 + 0xc) - 1U) * 4))()
;
return;
}
uStack_34 = 0;
FUN_10010fd0(&uStack_30);
local_50[0] = 0x2c;
uStack_48 = 1;
hp1020_queue_send_candidate(10,local_50);
```

### `10010218` `FUN_10010218`

#### line `15` `hp1020_queue_send_candidate`

Nearby decompiler context:

```c
undefined4 param_5)
{
undefined4 local_30;
undefined4 uStack_2c;
undefined4 uStack_28;
undefined4 uStack_24;
local_30 = param_2;
uStack_2c = param_3;
uStack_28 = param_4;
uStack_24 = param_5;
hp1020_queue_send_candidate(param_1,&local_30);
```

### `10010338` `FUN_10010338`

#### line `26` `hp1020_queue_send_candidate`

Nearby decompiler context:

```c
*(undefined4 *)(iVar1 + 0x5c) = param_1[1];
*(undefined4 *)(iVar1 + 0x58) = *param_1;
*(undefined4 *)(iVar1 + 0x60) = param_1[3];
*(undefined4 *)(iVar1 + 100) = param_1[4];
*(undefined4 *)(iVar1 + 0x48) = param_1[2];
if (param_2 != 0) {
FUN_100104c8(iVar1,param_2);
}
local_30[0] = 1;
iStack_24 = iVar1;
hp1020_queue_send_candidate(3,local_30);
```

### `10010398` `FUN_10010398`

#### line `17` `hp1020_queue_send_candidate`

Nearby decompiler context:

```c
int iVar2;
undefined4 local_30 [3];
undefined4 *puStack_24;
puVar1 = (undefined4 *)FUN_10013140(0x50,1);
FUN_1000f204();
puVar1[0x13] = 0;
puVar1[0x12] = 0;
*puVar1 = *param_1;
local_30[0] = 3;
puStack_24 = puVar1;
hp1020_queue_send_candidate(3,local_30);
```

#### line `25` `hp1020_queue_send_candidate`

Nearby decompiler context:

```c
local_30[0] = 3;
puStack_24 = puVar1;
hp1020_queue_send_candidate(3,local_30);
iVar2 = FUN_1000f228();
FUN_100104c8(iVar2,param_1);
*(undefined2 *)(iVar2 + 0x48) = 1;
*(undefined2 *)(iVar2 + 0x4a) = 1;
*(undefined1 *)(iVar2 + 0x76) = 0;
local_30[0] = 5;
puStack_24 = (undefined4 *)iVar2;
hp1020_queue_send_candidate(3,local_30);
```

### `100103f8` `FUN_100103f8`

#### line `8` `hp1020_queue_send_candidate`

Nearby decompiler context:

```c
void FUN_100103f8(void)
{
undefined4 local_30 [12];
local_30[0] = 6;
hp1020_queue_send_candidate(3,local_30);
```

### `1001040c` `FUN_1001040c`

#### line `8` `hp1020_queue_send_candidate`

Nearby decompiler context:

```c
void FUN_1001040c(void)
{
undefined4 local_30 [12];
local_30[0] = 2;
hp1020_queue_send_candidate(3,local_30);
```

### `10010590` `hp1020_status_mgr_thread_candidate`

#### line `24` `threadx_queue_receive_wait_candidate`

Nearby decompiler context:

```c
undefined4 uStack_30;
int iStack_2c;
undefined4 uStack_28;
int *piStack_24;
FUN_1001214c();
FUN_10010838(DAT_100063dc,1);
puVar4 = PTR_DAT_10006408;
puVar2 = PTR_DAT_100063d8;
puVar1 = PTR_DAT_100063b0;
switchD_100105cd_caseD_10:
threadx_queue_receive_wait_candidate(PTR_DAT_100063b4,&uStack_30,0xffffffff);
```

#### line `102` `hp1020_queue_send_candidate` case `0x43`

Nearby decompiler context:

```c
goto switchD_100105cd_caseD_10;
case 0x32:
if ((((*(uint *)(puVar2 + 8) & DAT_10005c88) == 0) &&
(uVar6 = *(uint *)(puVar2 + 8) & DAT_10006358, uVar6 != DAT_10006358)) &&
(uVar6 != DAT_1000635c)) goto switchD_100105cd_caseD_10;
uVar5 = *(undefined4 *)(puVar2 + 0x14);
break;
case 0x43:
goto switchD_100105cd_caseD_43;
}
hp1020_queue_send_candidate(uVar5,&uStack_30);
```

### `10010838` `FUN_10010838`

#### line `130` `hp1020_queue_send_candidate`

Nearby decompiler context:

```c
if (((auStack_30[0] & DAT_10005f74) == DAT_10005f78) ||
((auStack_30[0] & 0xffff) == DAT_10006424)) {
uStack_3c = 3;
}
else if ((auStack_30[0] & DAT_10006380) == 0) {
uStack_3c = 4;
}
else {
uStack_3c = 1;
}
hp1020_queue_send_candidate(3,&uStack_40);
```

### `10010c98` `FUN_10010c98`

#### line `22` `hp1020_queue_send_candidate`

Nearby decompiler context:

```c
if (uVar2 < 10) {
*(uint *)PTR_DAT_10006454 = uVar2 + 1;
puVar1 = (undefined4 *)(PTR_DAT_1000645c + uVar2 * 0x14);
*puVar1 = param_1;
puVar1[1] = param_2;
puVar1[2] = param_3;
puVar1[3] = param_4;
puVar1[4] = param_2;
local_30 = 0x44;
uStack_2c = 0;
hp1020_queue_send_candidate(0xf,&local_30);
```

### `10010cf0` `FUN_10010cf0`

#### line `32` `hp1020_queue_send_candidate`

Nearby decompiler context:

```c
if (uVar4 < *(int *)PTR_DAT_10006454 - 1U) {
do {
iVar1 = uVar4 * 0x14;
uVar4 = uVar4 + 1;
FUN_1001b38c(puVar3 + iVar1,puVar3 + uVar4 * 0x14,0x14);
} while (uVar4 < *(int *)puVar2 - 1U);
}
local_40 = 0x44;
uStack_3c = 1;
*(int *)puVar2 = *(int *)puVar2 + -1;
hp1020_queue_send_candidate(0xf,&local_40);
```

### `10011258` `hp1020_register_event_handler_candidate`

#### line `2` `hp1020_register_event_handler_candidate`

Nearby decompiler context:

```c
void hp1020_register_event_handler_candidate(int param_1,undefined4 param_2)
```

### `10013140` `FUN_10013140`

#### line `38` `hp1020_queue_send_candidate`

Nearby decompiler context:

```c
uVar4 = piVar5[2] & DAT_100066b8;
piVar5[2] = uVar4;
memw();
piVar5[2] = uVar4 | *(uint *)puVar2 & uVar1;
return;
}
threadx_sleep_candidate(10);
uVar4 = uVar4 + 1;
} while (uVar4 < 10);
local_30[0] = 0x21;
hp1020_queue_send_candidate(3,local_30);
```

### `10013620` `hp1020_send_or_raise_engine_msg_candidate`

#### line `2` `hp1020_send_or_raise_engine_msg_candidate`

Nearby decompiler context:

```c
void hp1020_send_or_raise_engine_msg_candidate(undefined4 param_1,undefined4 param_2)
```

#### line `7` `FUN_10013668`

Nearby decompiler context:

```c
void hp1020_send_or_raise_engine_msg_candidate(undefined4 param_1,undefined4 param_2)
{
int iVar1;
iVar1 = FUN_10013668(param_1,param_2,0);
```

### `10013658` `hp1020_queue_send_candidate`

#### line `2` `hp1020_queue_send_candidate`

Nearby decompiler context:

```c
undefined4 hp1020_queue_send_candidate(undefined4 param_1,undefined4 param_2)
```

#### line `7` `FUN_10013668`

Nearby decompiler context:

```c
undefined4 hp1020_queue_send_candidate(undefined4 param_1,undefined4 param_2)
{
undefined4 uVar1;
uVar1 = FUN_10013668(param_1,param_2,0xffffffff);
```

### `10013668` `FUN_10013668`

#### line `2` `FUN_10013668`

Nearby decompiler context:

```c
undefined4 FUN_10013668(int param_1,undefined4 param_2,undefined4 param_3)
```

### `10013c18` `hp1020_video_thread_candidate`

#### line `29` `threadx_queue_receive_wait_candidate`

Nearby decompiler context:

```c
memw();
memw();
*puVar2 = *puVar2 | 8;
uVar6 = 0;
FUN_1001214c();
puVar1 = PTR_DAT_10006770;
do {
while( true ) {
while( true ) {
uVar6 = uVar6 & 0xffffcfff;
threadx_queue_receive_wait_candidate(PTR_DAT_1000676c,aiStack_30,0xffffffff);
```

#### line `69` `hp1020_queue_send_candidate`

Nearby decompiler context:

```c
}
else if (iVar5 - 1U < 2) {
uVar6 = uVar6 & 0xffffcfff;
hp1020_video_prepare_page_candidate(piVar3);
uVar6 = uVar6 & 0xffffcfff;
hp1020_video_alt_render_candidate(piVar3);
}
}
aiStack_30[0] = 0x10;
uVar6 = uVar6 & 0xffffcfff;
hp1020_queue_send_candidate(1,aiStack_30);
```

### `10013d4c` `hp1020_video_reset_dispatch_candidate`

#### line `85` `hp1020_send_or_raise_engine_msg_candidate` case `0`

Nearby decompiler context:

```c
uVar7 = FUN_10017dac(puVar1,8,0);
}
iVar6 = **(int **)(puVar2 + 0xa0);
*(int *)(puVar2 + 0xa0) = iVar6;
puVar1 = PTR_DAT_10006770;
}
switch(param_1) {
case 0:
local_30 = 0x11;
iStack_24 = FUN_1001608c((int)uVar7,(int)((ulonglong)uVar7 >> 0x20));
hp1020_send_or_raise_engine_msg_candidate(0,&local_30);
```

#### line `91` `hp1020_send_or_raise_engine_msg_candidate` case `0`

Nearby decompiler context:

```c
switch(param_1) {
case 0:
local_30 = 0x11;
iStack_24 = FUN_1001608c((int)uVar7,(int)((ulonglong)uVar7 >> 0x20));
hp1020_send_or_raise_engine_msg_candidate(0,&local_30);
puVar2 = PTR_DAT_10006770;
iStack_24 = *(int *)(PTR_DAT_10006770 + 100);
*(undefined4 *)(PTR_DAT_10006770 + 0x60) = 0;
if (iStack_24 != 0) {
local_30 = 0xb;
hp1020_send_or_raise_engine_msg_candidate(8,&local_30);
```

#### line `121` `hp1020_send_or_raise_engine_msg_candidate` case `6`

Nearby decompiler context:

```c
uStack_2c = DAT_100067ac;
break;
case 6:
uStack_2c = DAT_100067b0;
break;
default:
goto switchD_10013e8d_default;
}
local_30 = 0x17;
LAB_10013f21:
hp1020_send_or_raise_engine_msg_candidate(1,&local_30);
```

### `10015c68` `hp1020_engine_read_or_write_status_candidate`

#### line `56` `hp1020_queue_send_candidate`

Nearby decompiler context:

```c
break;
}
}
iVar8 = iVar8 + -1;
} while (iVar8 != 0);
if (iVar8 == 0) {
uStack_30 = 0x17;
uStack_2c = DAT_1000692c;
iStack_28 = iVar8;
iStack_24 = iVar8;
hp1020_queue_send_candidate(1,&uStack_30);
```

### `10015df8` `hp1020_engine_status_poll_candidate`

#### line `101` `hp1020_queue_send_candidate` case `0x18`

Nearby decompiler context:

```c
}
}
else {
if (((*(uint *)(PTR_DAT_10006920 + 0x60) & 0xffff) == 0x100) &&
((uVar6 & 0xffff) == DAT_10006364)) {
FUN_10015dd0(0);
local_40 = 0x17;
uStack_38 = 0;
uStack_34 = 0;
uStack_3c = DAT_10006958;
hp1020_queue_send_candidate(1,&local_40);
```

#### line `116` `hp1020_queue_send_candidate` case `0x18`

Nearby decompiler context:

```c
FUN_10015dd0(1);
}
bVar8 = true;
*(uint *)(PTR_DAT_10006920 + 0x60) = uVar6;
}
if (bVar8) {
local_40 = 0x17;
uStack_38 = 0;
uStack_34 = 0;
uStack_3c = uVar6;
hp1020_queue_send_candidate(1,&local_40);
```

### `100160a8` `hp1020_engine_preflight_candidate`

#### line `24` `hp1020_queue_send_candidate`

Nearby decompiler context:

```c
undefined4 uStack_38;
undefined4 uStack_34;
undefined4 uStack_30;
undefined4 uStack_2c;
undefined4 uStack_28;
undefined4 uStack_24;
local_40 = 0x17;
uStack_38 = 0;
uStack_34 = 0;
uStack_3c = DAT_100063dc;
hp1020_queue_send_candidate(1,&local_40);
```

#### line `57` `hp1020_queue_send_candidate`

Nearby decompiler context:

```c
threadx_sleep_candidate(0x14);
iVar6 = iVar6 + 1;
if ((*(int *)(PTR_DAT_10006920 + 0x24) != 0) || (iVar6 == 0x1e)) break;
memw();
uVar1 = *DAT_10006928 & DAT_10005e74;
}
uStack_30 = 0x17;
uStack_28 = 0;
uStack_24 = 0;
uStack_2c = DAT_1000692c;
hp1020_queue_send_candidate(1,&uStack_30);
```

### `10016164` `hp1020_engine_message_dispatch_candidate`

#### line `19` `hp1020_queue_send_candidate` case `0xd`

Nearby decompiler context:

```c
uint uVar4;
undefined4 local_40;
undefined4 uStack_3c;
int iStack_34;
undefined4 uStack_30;
undefined4 uStack_2c;
puVar2 = PTR_DAT_10006920;
switch(*param_1) {
case 0xd:
*param_1 = 0xe;
hp1020_queue_send_candidate(1,param_1);
```

#### line `27` `hp1020_queue_send_candidate` case `0xf`

Nearby decompiler context:

```c
case 0xd:
*param_1 = 0xe;
hp1020_queue_send_candidate(1,param_1);
break;
case 0xf:
local_40 = 0x25;
uStack_3c = 0;
PTR_DAT_10006920[0x28] = 1;
*(undefined4 *)(puVar2 + 0x68) = 0;
*(undefined4 *)(puVar2 + 0x6c) = 0;
hp1020_queue_send_candidate(1,&local_40);
```

#### line `43` `hp1020_send_or_raise_engine_msg_candidate` case `0x11`

Nearby decompiler context:

```c
if ((uVar4 & 0xffff & DAT_10005e34) == 0) {
iStack_34 = *(int *)(PTR_DAT_10006920 + 0x68);
if (iStack_34 != 0) {
local_40 = 0x11;
FUN_100180dc(PTR_DAT_1000699c,&local_40,0xffffffff);
*(undefined4 *)(puVar2 + 0x68) = 0;
}
iStack_34 = *(int *)(puVar2 + 0x6c);
if (iStack_34 != 0) {
local_40 = 0xb;
hp1020_send_or_raise_engine_msg_candidate(0,&local_40);
```

#### line `54` `hp1020_queue_send_candidate` case `0x19`

Nearby decompiler context:

```c
*(undefined4 *)(puVar2 + 0x6c) = 0;
}
}
break;
case 0x18:
hp1020_engine_status_poll_candidate(1);
break;
case 0x19:
uStack_2c = 2;
uStack_30 = 0x16;
hp1020_queue_send_candidate(1,&uStack_30);
```

### `1001635c` `hp1020_engine_delay_thread_candidate`

#### line `13` `threadx_queue_receive_wait_candidate`

Nearby decompiler context:

```c
void hp1020_engine_delay_thread_candidate(void)
{
undefined *puVar1;
int iVar2;
int aiStack_30 [12];
FUN_1001214c();
puVar1 = PTR_DAT_10006920;
iVar2 = *(int *)(PTR_DAT_10006920 + 0x24);
while (iVar2 == 0) {
iVar2 = threadx_queue_receive_wait_candidate(PTR_DAT_1000699c,aiStack_30,0xffffffff);
```

#### line `16` `hp1020_send_or_raise_engine_msg_candidate`

Nearby decompiler context:

```c
undefined *puVar1;
int iVar2;
int aiStack_30 [12];
FUN_1001214c();
puVar1 = PTR_DAT_10006920;
iVar2 = *(int *)(PTR_DAT_10006920 + 0x24);
while (iVar2 == 0) {
iVar2 = threadx_queue_receive_wait_candidate(PTR_DAT_1000699c,aiStack_30,0xffffffff);
if ((((iVar2 == 0) && (aiStack_30[0] == 0x11)) && (puVar1[0x28] != '\x01')) &&
(threadx_sleep_candidate(0x9b), puVar1[0x28] != '\x01')) {
hp1020_send_or_raise_engine_msg_candidate(1,aiStack_30);
```

### `100163b0` `hp1020_engine_thread_candidate`

#### line `23` `hp1020_register_event_handler_candidate`

Nearby decompiler context:

```c
*(undefined4 *)(PTR_DAT_10006920 + 0x68) = 0;
FUN_1001215c(2);
hp1020_engine_preflight_candidate();
uVar1 = DAT_10006420;
*(undefined4 *)(puVar2 + 0x44) = DAT_10005e34;
while (uVar3 = hp1020_engine_status_poll_candidate(0), (uVar3 & uVar1) == uVar1) {
threadx_sleep_candidate(1);
}
hp1020_engine_init_step_candidate();
hp1020_engine_register_handlers_candidate();
hp1020_register_event_handler_candidate(0xf,PTR_FUN_100069b4);
```

#### line `25` `hp1020_register_event_handler_candidate`

Nearby decompiler context:

```c
hp1020_engine_preflight_candidate();
uVar1 = DAT_10006420;
*(undefined4 *)(puVar2 + 0x44) = DAT_10005e34;
while (uVar3 = hp1020_engine_status_poll_candidate(0), (uVar3 & uVar1) == uVar1) {
threadx_sleep_candidate(1);
}
hp1020_engine_init_step_candidate();
hp1020_engine_register_handlers_candidate();
hp1020_register_event_handler_candidate(0xf,PTR_FUN_100069b4);
puVar2 = PTR_LAB_100069b8;
hp1020_register_event_handler_candidate(0x10,PTR_LAB_100069b8);
```

#### line `26` `hp1020_register_event_handler_candidate`

Nearby decompiler context:

```c
uVar1 = DAT_10006420;
*(undefined4 *)(puVar2 + 0x44) = DAT_10005e34;
while (uVar3 = hp1020_engine_status_poll_candidate(0), (uVar3 & uVar1) == uVar1) {
threadx_sleep_candidate(1);
}
hp1020_engine_init_step_candidate();
hp1020_engine_register_handlers_candidate();
hp1020_register_event_handler_candidate(0xf,PTR_FUN_100069b4);
puVar2 = PTR_LAB_100069b8;
hp1020_register_event_handler_candidate(0x10,PTR_LAB_100069b8);
hp1020_register_event_handler_candidate(0x11,puVar2);
```

#### line `27` `hp1020_register_event_handler_candidate`

Nearby decompiler context:

```c
*(undefined4 *)(puVar2 + 0x44) = DAT_10005e34;
while (uVar3 = hp1020_engine_status_poll_candidate(0), (uVar3 & uVar1) == uVar1) {
threadx_sleep_candidate(1);
}
hp1020_engine_init_step_candidate();
hp1020_engine_register_handlers_candidate();
hp1020_register_event_handler_candidate(0xf,PTR_FUN_100069b4);
puVar2 = PTR_LAB_100069b8;
hp1020_register_event_handler_candidate(0x10,PTR_LAB_100069b8);
hp1020_register_event_handler_candidate(0x11,puVar2);
hp1020_register_event_handler_candidate(0x12,puVar2);
```

#### line `28` `hp1020_register_event_handler_candidate`

Nearby decompiler context:

```c
while (uVar3 = hp1020_engine_status_poll_candidate(0), (uVar3 & uVar1) == uVar1) {
threadx_sleep_candidate(1);
}
hp1020_engine_init_step_candidate();
hp1020_engine_register_handlers_candidate();
hp1020_register_event_handler_candidate(0xf,PTR_FUN_100069b4);
puVar2 = PTR_LAB_100069b8;
hp1020_register_event_handler_candidate(0x10,PTR_LAB_100069b8);
hp1020_register_event_handler_candidate(0x11,puVar2);
hp1020_register_event_handler_candidate(0x12,puVar2);
hp1020_register_event_handler_candidate(0x13,puVar2);
```

#### line `29` `hp1020_register_event_handler_candidate`

Nearby decompiler context:

```c
threadx_sleep_candidate(1);
}
hp1020_engine_init_step_candidate();
hp1020_engine_register_handlers_candidate();
hp1020_register_event_handler_candidate(0xf,PTR_FUN_100069b4);
puVar2 = PTR_LAB_100069b8;
hp1020_register_event_handler_candidate(0x10,PTR_LAB_100069b8);
hp1020_register_event_handler_candidate(0x11,puVar2);
hp1020_register_event_handler_candidate(0x12,puVar2);
hp1020_register_event_handler_candidate(0x13,puVar2);
hp1020_register_event_handler_candidate(0x14,puVar2);
```

#### line `33` `hp1020_queue_send_candidate`

Nearby decompiler context:

```c
hp1020_register_event_handler_candidate(0xf,PTR_FUN_100069b4);
puVar2 = PTR_LAB_100069b8;
hp1020_register_event_handler_candidate(0x10,PTR_LAB_100069b8);
hp1020_register_event_handler_candidate(0x11,puVar2);
hp1020_register_event_handler_candidate(0x12,puVar2);
hp1020_register_event_handler_candidate(0x13,puVar2);
hp1020_register_event_handler_candidate(0x14,puVar2);
hp1020_engine_init_step_candidate();
uStack_2c = 2;
uStack_30 = 0x16;
hp1020_queue_send_candidate(1,&uStack_30);
```

#### line `38` `threadx_queue_receive_wait_candidate`

Nearby decompiler context:

```c
hp1020_register_event_handler_candidate(0x13,puVar2);
hp1020_register_event_handler_candidate(0x14,puVar2);
hp1020_engine_init_step_candidate();
uStack_2c = 2;
uStack_30 = 0x16;
hp1020_queue_send_candidate(1,&uStack_30);
FUN_10012184(2);
puVar2 = PTR_DAT_10006920;
iVar4 = *(int *)(PTR_DAT_10006920 + 0x24);
while (iVar4 == 0) {
iVar4 = threadx_queue_receive_wait_candidate(PTR_DAT_100069bc,&uStack_30,0x32);
```

### `1001809c` `threadx_queue_receive_wait_candidate`

#### line `2` `threadx_queue_receive_wait_candidate`

Nearby decompiler context:

```c
undefined4 threadx_queue_receive_wait_candidate(int *param_1,int param_2,int param_3)
```

## Interpretation

- Treat these as candidate producers, not final names. Decompiler variable names are temporary.
- The strongest evidence is a constant assignment immediately before `hp1020_queue_send_candidate` or `hp1020_send_or_raise_engine_msg_candidate`.
- Message IDs must be interpreted per queue. `0x0b` in `PrintMgrQueue`, video queue, and engine queue may not mean the exact same operation.
