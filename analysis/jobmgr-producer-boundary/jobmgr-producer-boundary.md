# HP 1020 JobMgr Producer Boundary

This pass scans decompiled firmware for JobMgr queue producers, direct queue-object sends, and the currently unresolved JobMgr messages `9` and `0x29`.

## Counts

- queue-id `3` wrapper sends: `8`
- direct JobMgr scalar sends: `2`
- possible message `9` constants: `13`
- possible message `0x29` constants: `0`
- video hardware runtime block refs: `0`

## Notable Hits

| Function | Line | Kind | Code |
|---:|---:|---|---|
| `1000f814` `hp1020_print_mgr_return_work_to_jobmgr_candidate` | `14` | `queue_id_3_send` | `hp1020_queue_send_candidate(3,param_1);` |
| `10010338` `hp1020_job_record_create_and_enqueue_candidate` | `26` | `queue_id_3_send` | `hp1020_queue_send_candidate(3,local_30);` |
| `10010398` `hp1020_child_page_record_create_candidate` | `17` | `queue_id_3_send` | `hp1020_queue_send_candidate(3,local_30);` |
| `10010398` `hp1020_child_page_record_create_candidate` | `25` | `queue_id_3_send` | `hp1020_queue_send_candidate(3,local_30);` |
| `100103f8` `hp1020_jobmgr_send_case_6_candidate` | `8` | `queue_id_3_send` | `hp1020_queue_send_candidate(3,local_30);` |
| `1001040c` `hp1020_jobmgr_send_case_2_candidate` | `8` | `queue_id_3_send` | `hp1020_queue_send_candidate(3,local_30);` |
| `10010838` `hp1020_status_state_update_candidate` | `130` | `queue_id_3_send` | `hp1020_queue_send_candidate(3,&amp;uStack_40);` |
| `10013140` `FUN_10013140` | `38` | `queue_id_3_send` | `hp1020_queue_send_candidate(3,local_30);` |
| `10013d4c` `hp1020_video_reset_dispatch_candidate` | `0` | `direct_jobmgr_scalar_send_function` | `function references JobMgr queue object and scalar queue-send helper` |
| `100144d0` `hp1020_video_irq_or_band_done_candidate` | `0` | `direct_jobmgr_scalar_send_function` | `function references JobMgr queue object and scalar queue-send helper` |

## Interpretation

- The normal queue-id wrapper proves JobMgr messages `1`, `2`, `3`, `5`, `6`, `0x0f`, `0x21`, and `0x25` in earlier queue-send reports.
- Direct queue-object sends to JobMgr are real: video reset/interrupt paths call the scalar ThreadX send helper with message `8`.
- This scan still does not prove a normal static producer for JobMgr message `0x29`.
- Message `9` constants mostly occur in PJL/data-store parsing contexts and should not be blindly treated as JobMgr message `9` without queue evidence.
- The next target is broader parser-side tracing: find where the payload copied into JobMgr `0x29` is built, likely before it reaches a wrapper our current queue census recognizes.
