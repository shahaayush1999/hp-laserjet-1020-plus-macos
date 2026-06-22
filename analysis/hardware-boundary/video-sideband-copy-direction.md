# HP 1020 Video Sideband Copy Direction

This generated report is offline only. It does not contact the printer.

## Result

- status: `pass`
- helper: `0x1001b38c` `memcpy_candidate`
- argument order: `destination, source, length`
- limitation: decompiler still truncates later optimized copy loop on old Xtensa instructions, but the byte prologue and callers are enough to pin argument direction

## Sideband Copy Call

- call: `FUN_1001b38c(PTR_DAT_10006304,iStack_84,0x14)`
- interpreted as: `memcpy(dst=PTR_DAT_10006304 runtime block, src=iStack_84 active work, len=0x14)`
- effect: copies early work fields out to the runtime block; does not fill active work +0x26/+0x30/+0x32

## Direction Evidence

| Snippet | Present | Meaning |
|---|---|---|
| `uVar1 = *param_2;` | `True` | read one byte from second argument |
| `*param_1 = uVar1;` | `True` | write one byte to first argument |
| `param_2 = param_2 + 1;` | `True` | advance source pointer |
| `param_1 = param_1 + 1;` | `True` | advance destination pointer |

## Comparator Calls

| Function | Present | Interpretation |
|---|---|---|
| `0x10010fd0 datastore write` | `True` | copy caller data into datastore slot |
| `0x10010f54 datastore read` | `True` | copy datastore slot into caller buffer |

## Effect On Prepare Fields

- ruled out hidden source: 0x1000e414 case 0x29 memcpy does not copy PTR_DAT_10006304 into the active work object
- still unsourced: `+0x26, +0x30, +0x32`

## Checks

| Check | Status | Detail |
|---|---|---|
| `memcpy_helper_direction_is_dest_src_len` | `present` | 0x1001b38c decompile shows reads from param_2 and writes to param_1 before the bad-instruction tail |
| `jobmgr_sideband_copy_is_work_to_runtime_block` | `present` | JobMgr case 0x29 call copies iStack_84 active work into PTR_DAT_10006304 when interpreted with dest,src,len order |
| `datastore_comparators_match_direction` | `present` | datastore read/write callers agree with dest,src,len direction |
| `unsourced_fields_remain_after_copy_direction` | `present` | prepare field model still marks +0x26/+0x30/+0x32 unsourced after ruling out this copy path |
