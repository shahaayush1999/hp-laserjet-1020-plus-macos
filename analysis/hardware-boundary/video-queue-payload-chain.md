# HP 1020 Video Queue Payload Chain

This generated report is offline only. It does not contact the printer.

## Result

- status: `pass`
- prepare argument identity: `0x94-byte video/page work object`
- remaining-unit impact: current static evidence weakens the earlier page-param +0x26 -> work +0x26 alias theory; the active work +0x26 source remains unresolved

## Plain-English Meaning

The video code is almost certainly receiving the work object whose geometry is filled by JobMgr. The page-height value is proven in the earlier page-param block, but this chain does not show it being copied into the work object field that prepare reads.

## Pointer Chain

| Stage | Function | Object | Confidence | Evidence |
|---|---|---|---|---|
| `page_parameter_block` | `0x10009b4c` | page parameter block | `high for page-param object only` | builder writes ZJI item 0x12 into page-param +0x26 |
| `work_object_creation` | `0x10010398 -> 0x1000f228 -> 0x100104c8` | 0x94-byte video/page work object | `high` | child-page creator allocates work, copies selected fields, then sends JobMgr message 5 with the work pointer |
| `raster_geometry_fill` | `0x1000e414` | same work object | `high` | JobMgr writes BIH/runtime block values into work +0x84/+0x88/+0x8c/+0x90 |
| `engine_queue_handoff` | `0x1000e414 -> queue 1 message 0x0b` | work pointer in message word 4 | `medium-high` | JobMgr stores iVar9 in iStack_84 and sends engine queue message 0x0b |
| `engine_active_work` | `0x10016164` | engine state +0x68 active work pointer | `high` | engine dispatch stores param_1[3] into engine state +0x68 for message 0x0b/0x40 |
| `print_mgr_video_send` | `0x1000f574 -> 0x10010218` | work pointer in message word 4 | `medium-high` | PrintMgr sends queue 8 message 0x0b with uVar10, and wrapper places param_5 into uStack_24 |
| `video_thread_prepare` | `0x10013c18 -> 0x10014910` | VideoThread active work pointer | `high` | VideoThread receives message 0x0b, stores uStack_24 at video state +0x60, and calls prepare(piVar3) |

## `+0x26` Write Hits

| Source | Line | Text |
|---|---:|---|
| `prepare` | `196` | `*(uint *)(puVar15 + 0xd0) = (uint)*(ushort *)(param_1 + 0x26);` |
| `prepare` | `197` | `*(uint *)(puVar15 + 0xd4) = (uint)*(ushort *)(param_1 + 0x26);` |
| `page_param_builder` | `102` | `*(undefined2 *)(param_1 + 0x26) = *(undefined2 *)((int)param_2 + 10);` |

## Work Geometry Writes

| Source | Line | Text |
|---|---:|---|
| `job_mgr` | `185` | `*(undefined4 *)(iVar9 + 0x84) = *(undefined4 *)(PTR_DAT_10006304 + 4);` |
| `job_mgr` | `510` | `*(undefined4 *)(iVar9 + 0x84) = *(undefined4 *)(PTR_DAT_10006304 + 4);` |
| `work_create` | `15` | `*(undefined4 *)(iVar1 + 0x84) = 0;` |
| `job_mgr` | `186` | `*(undefined4 *)(iVar9 + 0x88) = *(undefined4 *)(puVar4 + 8);` |
| `job_mgr` | `511` | `*(undefined4 *)(iVar9 + 0x88) = *(undefined4 *)(puVar6 + 8);` |
| `work_create` | `16` | `*(undefined4 *)(iVar1 + 0x88) = 0;` |
| `job_mgr` | `187` | `*(undefined4 *)(iVar9 + 0x8c) = *(undefined4 *)(puVar4 + 0xc);` |
| `job_mgr` | `512` | `*(undefined4 *)(iVar9 + 0x8c) = *(undefined4 *)(puVar6 + 0xc);` |
| `work_create` | `17` | `*(undefined4 *)(iVar1 + 0x8c) = 0;` |
| `job_mgr` | `188` | `*(undefined *)(iVar9 + 0x90) = puVar4[0x13];` |
| `job_mgr` | `513` | `*(undefined *)(iVar9 + 0x90) = puVar6[0x13];` |
| `work_create` | `18` | `*(undefined1 *)(iVar1 + 0x90) = 0;` |

## Checks

| Check | Status | Detail |
|---|---|---|
| `work_object_is_allocated_before_jobmgr_message_5` | `present` | child-page create path creates a 0x94 work object and sends it to JobMgr as message 5 |
| `work_create_allocates_0x94_and_clears_video_fields` | `present` | work creator allocates the object that later gets video geometry fields |
| `work_populate_does_not_copy_page_param_0x26` | `present` | selected page-param copier still does not copy +0x26 into the work object |
| `jobmgr_fills_work_video_geometry` | `present` | JobMgr fills the same work object fields consumed by video prepare/render |
| `jobmgr_sends_engine_0x0b_with_work_pointer` | `present` | JobMgr sends engine queue 0x0b with the candidate work pointer in the fourth message word |
| `engine_dispatch_stores_active_work_pointer` | `present` | engine dispatch stores queue message word 4 as active work pointer |
| `printmgr_sends_video_queue_payload_word` | `present` | PrintMgr sends Video Queue 0x0b with the same payload slot shape |
| `video_thread_uses_payload_as_prepare_argument` | `present` | VideoThread stores message word 4 as active work and passes it to prepare |
| `prepare_reads_both_geometry_and_0x26_from_same_argument` | `present` | prepare reads +0x84 geometry and +0x26 remaining-units field from the same argument |
