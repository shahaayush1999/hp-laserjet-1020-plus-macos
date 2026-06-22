# HP 1020 Video Sideband Write Census

This generated report is offline only. It does not contact the printer.

## Result

- status: `pass`
- decompiled files scanned for raw sideband-looking hits: `632`
- raw corpus hits: `112`

## Conclusion

- The obvious page-param writes for +0x26/+0x30/+0x32 are upstream page-parameter fields, not active work-object writes.
- The child-page `puVar1[0x13] = 0` false lead is byte +0x4c because the pointer is `undefined4 *`.
- The JobMgr `puVar[0x13]` hits feed work +0x90 from runtime byte +0x13, not work +0x26.
- A headless Ghidra instruction probe confirms 0x100104c8 has no stores to active work +0x26/+0x30/+0x32.
- A whole-program Ghidra instruction scan finds `s16i` stores to offsets 0x26/0x30/0x32 only in the page-parameter builder.
- A broader overlapping-store scan is noisy by design, but its selected direct-path hits do not identify an active-work sideband writer.
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

## Ghidra Work-Populate Probe

- path: `analysis/ghidra-probes/work-populate-instruction-probe.md`
- language: `Xtensa:BE:32:default`
- halfword destination offsets: `0xc, 0xa, 0x10, 0x22, 0x1e, 0x14, 0x16, 0xe`
- word destination offsets: `0x0`

## Ghidra Whole-Program Sideband Store Scan

- path: `analysis/ghidra-probes/sideband-store-scan.md`
- language: `Xtensa:BE:32:default`

| Address | Function | Offset | Instruction |
|---|---|---|---|
| `10009c35` | `10009b4c FUN_10009b4c` | `0x26` | `s16i a8,a2,0x26` |
| `10009c86` | `10009b4c FUN_10009b4c` | `0x30` | `s16i a8,a2,0x30` |
| `10009c8f` | `10009b4c FUN_10009b4c` | `0x32` | `s16i a8,a2,0x32` |

## Ghidra Whole-Program Overlap Store Scan

- path: `analysis/ghidra-probes/sideband-overlap-store-scan.md`
- language: `Xtensa:BE:32:default`
- overlapping stores found: `103`
- selected direct-path overlap hits: `4`

| Address | Function | Mnemonic | Offset | Width | Overlaps | Role | Meaning |
|---|---|---|---:|---:|---|---|---|
| `10009c35` | `10009b4c FUN_10009b4c` | `s16i` | `0x26` | `2` | `+0x26` | `upstream_page_param_exact_store` | real page-param sideband store; it is upstream of the active work object |
| `10009c86` | `10009b4c FUN_10009b4c` | `s16i` | `0x30` | `2` | `+0x30` | `upstream_page_param_exact_store` | real page-param sideband store; it is upstream of the active work object |
| `10009c8f` | `10009b4c FUN_10009b4c` | `s16i` | `0x32` | `2` | `+0x32` | `upstream_page_param_exact_store` | real page-param sideband store; it is upstream of the active work object |
| `10014a2a` | `10014910 FUN_10014910` | `s32i` | `0x24` | `4` | `+0x26` | `video_state_ring_clear` | 32-bit clear at video state ring entry +0x24; overlaps +0x26 as bytes, but not an active-work field write |

## Checks

| Check | Status | Detail |
|---|---|---|
| `selected_sideband_hits_classified` | `present` | selected sideband-looking hits are classified as upstream writers, consumers, or false leads |
| `child_record_0x13_is_not_work_0x26` | `present` | 0x10010398 puVar1[0x13] is a 32-bit child/page record slot at byte +0x4c |
| `runtime_byte_0x13_feeds_work_0x90_not_sideband` | `present` | JobMgr puVar[0x13] references are BIH/runtime byte +0x13 copied to work +0x90 |
| `work_populate_still_lacks_sideband_copy` | `present` | simple page-param to work-object copier has no visible +0x26/+0x30/+0x32 copy |
| `ghidra_instruction_probe_excludes_sideband_stores` | `present` | headless Ghidra instruction probe for 0x100104c8 has no stores to +0x26/+0x30/+0x32 |
| `ghidra_whole_program_sideband_stores_are_page_param_only` | `present` | whole-program Ghidra scan finds target-offset halfword stores only in the page-parameter builder |
| `ghidra_overlap_scan_is_broad_not_exact_sideband_proof` | `present` | whole-program overlap scan is intentionally broader than exact target stores and catches noisy wider stores |
| `ghidra_overlap_scan_finds_no_work_populate_or_jobmgr_sideband_writer` | `present` | no overlapping store hit appears in the selected active-work create/populate/JobMgr functions |
| `ghidra_direct_path_overlap_hits_are_classified` | `present` | direct-path overlap hits are page-param exact stores or a video-state ring clear, not active work writers |
| `no_selected_active_work_writer_found` | `present` | the selected print-path corpus still has no direct active work sideband writer |
| `prepare_field_model_keeps_sidebands_unsourced` | `present` | prepare field model still marks +0x26/+0x30/+0x32 as unsourced on active work |
| `queue_chain_keeps_prepare_argument_as_work_object` | `present` | queue chain still identifies the active prepare argument as the 0x94 work object |
