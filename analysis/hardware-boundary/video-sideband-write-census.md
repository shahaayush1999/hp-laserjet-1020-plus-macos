# HP 1020 Video Sideband Write Census

This generated report is offline only. It does not contact the printer.

## Result

- status: `pass`
- decompiled files scanned for raw sideband-looking hits: `627`
- raw corpus hits: `112`

## Conclusion

- The obvious page-param writes for +0x26/+0x30/+0x32 are upstream page-parameter fields, not active work-object writes.
- The child-page `puVar1[0x13] = 0` false lead is byte +0x4c because the pointer is `undefined4 *`.
- The JobMgr `puVar[0x13]` hits feed work +0x90 from runtime byte +0x13, not work +0x26.
- Within the selected print-path corpus, active work +0x26/+0x30/+0x32 remain unsourced.

## Selected Hit Classification

| Source | Line | Role | Byte offset | Text | Meaning |
|---|---:|---|---|---|---|
| `page_param_builder` | `102` | `upstream_page_param_writer` | `+0x26` | `*(undefined2 *)(param_1 + 0x26) = *(undefined2 *)((int)param_2 + 10);` | real page-param +0x26 writer, not active work |
| `page_param_builder` | `119` | `upstream_page_param_writer` | `+0x30` | `*(undefined2 *)(param_1 + 0x30) = *(undefined2 *)((int)param_2 + 10);` | real page-param +0x30 writer, not active work |
| `page_param_builder` | `122` | `upstream_page_param_writer` | `+0x32` | `*(undefined2 *)(param_1 + 0x32) = *(undefined2 *)((int)param_2 + 10);` | real page-param +0x32 writer, not active work |
| `child_page_create` | `14` | `scaled_index_false_lead` | `+0x4c` | `puVar1[0x13] = 0;` | undefined4* index 0x13 means child/page record byte offset +0x4c |
| `job_mgr` | `188` | `runtime_byte_to_work_0x90` | `source +0x13, destination +0x90` | `*(undefined *)(iVar9 + 0x90) = puVar4[0x13];` | undefined* index 0x13 is runtime block byte +0x13 copied into work +0x90 |
| `job_mgr` | `513` | `runtime_byte_to_work_0x90` | `source +0x13, destination +0x90` | `*(undefined *)(iVar9 + 0x90) = puVar6[0x13];` | undefined* index 0x13 is runtime block byte +0x13 copied into work +0x90 |
| `prepare` | `196` | `active_work_consumer` | `+0x26` | `*(uint *)(puVar15 + 0xd0) = (uint)*(ushort *)(param_1 + 0x26);` | consumer: prepare reads active argument +0x26 into video state counters |
| `prepare` | `197` | `active_work_consumer` | `+0x26` | `*(uint *)(puVar15 + 0xd4) = (uint)*(ushort *)(param_1 + 0x26);` | consumer: prepare reads active argument +0x26 into video state counters |
| `prepare` | `198` | `active_work_consumer` | `+0x32` | `*(uint *)(puVar15 + 0xec) = (uint)*(ushort *)(param_1 + 0x32);` | consumer: prepare reads active argument +0x32 into video state +0xec |
| `prepare` | `199` | `active_work_consumer` | `+0x30` | `*(uint *)(puVar15 + 0xe8) = (uint)*(ushort *)(param_1 + 0x30);` | consumer: prepare reads active argument +0x30 into video state +0xe8 |

## Raw Unique Corpus Texts

- `*(uint *)(puVar15 + 0xd0) = (uint)*(ushort *)(param_1 + 0x26);`
- `*(uint *)(puVar15 + 0xd4) = (uint)*(ushort *)(param_1 + 0x26);`
- `*(uint *)(puVar15 + 0xe8) = (uint)*(ushort *)(param_1 + 0x30);`
- `*(uint *)(puVar15 + 0xec) = (uint)*(ushort *)(param_1 + 0x32);`
- `*(undefined *)(iVar9 + 0x90) = puVar4[0x13];`
- `*(undefined *)(iVar9 + 0x90) = puVar6[0x13];`
- `*(undefined2 *)(param_1 + 0x26) = *(undefined2 *)((int)param_2 + 10);`
- `*(undefined2 *)(param_1 + 0x30) = *(undefined2 *)((int)param_2 + 10);`
- `*(undefined2 *)(param_1 + 0x32) = *(undefined2 *)((int)param_2 + 10);`
- `*(undefined4 *)(PTR_DAT_10006920 + 0x30) = 1;`
- `*(undefined4 *)(iVar10 + 0x30) = 5;`
- `*(undefined4 *)(iVar2 + 0x30) = 5;`
- `*(undefined4 *)(iVar2 + 0x30) = 7;`
- `*(undefined4 *)(iVar3 + 0x30) = 6;`
- `*(undefined4 *)(iVar4 + 0x30) = 4;`
- `*(undefined4 *)(iVar5 + 0x30) = 0xd;`
- `*(undefined4 *)(iVar5 + 0x30) = 5;`
- `*(undefined4 *)(iVar5 + 0x30) = 9;`
- `*(undefined4 *)(iVar8 + 0x30) = 3;`
- `*(undefined4 *)(param_1 + 0x30) = 0;`
- `*(undefined4 *)(param_1 + 0x30) = 3;`
- `*(undefined4 *)(param_1[0xd] + 0x30) = param_1[0xc];`
- `*(undefined4 *)(puVar2 + 0x30) = 1;`
- `*(undefined4 **)(iVar3 + 0x30) = param_1;`
- `*param_7 = *(undefined4 *)(param_1 + 0x30);`
- `else if (1 < *(int *)(param_1 + 0x30) - 1U) {`
- `if ((*(uint *)(iVar3 + 0x30) & 1) != 0) {`
- `if ((*(uint *)(iVar3 + 0x30) & 2) != 0) {`
- `if ((*(uint *)(iVar5 + 0x30) & 2) != 0) {`
- `if (*(int *)(iVar4 + 0x30) == 0) {`
- `if (*(int *)(param_1 + 0x30) != 0) {`
- `if (*(int *)(param_1 + 0x30) == 0) {`
- `if (*(int *)(param_1 + 0x30) == 8) {`
- `if (*(int *)(param_1 + 0x30) == 9) {`
- `puVar1[0x13] = 0;`

## Checks

| Check | Status | Detail |
|---|---|---|
| `selected_sideband_hits_classified` | `present` | selected sideband-looking hits are classified as upstream writers, consumers, or false leads |
| `child_record_0x13_is_not_work_0x26` | `present` | 0x10010398 puVar1[0x13] is a 32-bit child/page record slot at byte +0x4c |
| `runtime_byte_0x13_feeds_work_0x90_not_sideband` | `present` | JobMgr puVar[0x13] references are BIH/runtime byte +0x13 copied to work +0x90 |
| `work_populate_still_lacks_sideband_copy` | `present` | simple page-param to work-object copier has no visible +0x26/+0x30/+0x32 copy |
| `no_selected_active_work_writer_found` | `present` | the selected print-path corpus still has no direct active work sideband writer |
| `prepare_field_model_keeps_sidebands_unsourced` | `present` | prepare field model still marks +0x26/+0x30/+0x32 as unsourced on active work |
| `queue_chain_keeps_prepare_argument_as_work_object` | `present` | queue chain still identifies the active prepare argument as the 0x94 work object |
