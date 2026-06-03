# HP 1020 Queue Routing Generated Map

This generated pass preserves queue routing evidence and decompiler output for the queue send helper and known queue consumers.

## Queue Table

- `0x10013668` indexes `DAT_100066f0` by queue number.
- word at `0x100066f0`: `0x1002c918`
- candidate runtime queue table base: `0x1002c918`

## Candidate Queue IDs

| Queue ID | Candidate owner | Consumer function | Receive/control object |
|---:|---|---|---|
| `0` | `PrintMgrQueue` | `0x1000f324` `hp1020_print_mgr_thread_candidate` | `0x10028a74` |
| `1` | `engMsgQ` | `0x100163b0` `hp1020_engine_thread_candidate` | `0x1002f134` |
| `3` | `Job Mgr Queue` | `0x1000e414` `hp1020_job_mgr_thread_candidate` | `0x1002386c` |
| `8` | `Video Queue` candidate | `0x10013c18` `hp1020_video_thread_candidate` | `0x1002ee38` |
| `10` | `StatusMgrQueue` | `0x10010590` `hp1020_status_mgr_thread_candidate` | `0x10028adc` |
| `0x0f` | `DelayMgr Msg Queue` | `0x10010b0c` `hp1020_delay_mgr_receive_thread_candidate` | `0x1001d694` candidate |

## Decompiled Evidence

### `10013668` `hp1020_queue_send_indexed_candidate`

```c
undefined4 hp1020_queue_send_indexed_candidate(int param_1,undefined4 param_2,undefined4 param_3)
iVar1 = threadx_queue_send_wait_candidate
(*(undefined4 *)(param_1 * 4 + DAT_100066f0),param_2,param_3);
```

### `100136d8` `hp1020_calibration_control_queue_worker_candidate`

```c
void hp1020_calibration_control_queue_worker_candidate(void)
threadx_queue_receive_wait_candidate(PTR_DAT_100066f8,auStack_80,0xffffffff);
```

### `1000f324` `hp1020_print_mgr_thread_candidate`

```c
hp1020_queue_send_candidate(0,aiStack_50);
threadx_queue_receive_wait_candidate(PTR_DAT_1000632c,aiStack_50,0xffffffff);
```

### `1000e414` `hp1020_job_mgr_thread_candidate`

```c
iVar8 = threadx_queue_receive_wait_candidate(PTR_DAT_100062d0,&uStack_90,2);
hp1020_queue_send_candidate(1,&uStack_90);
hp1020_queue_send_candidate(*(undefined4 *)(iVar8 + 100),&uStack_90);
hp1020_queue_send_candidate(3,&uStack_80);
hp1020_queue_send_candidate(*(undefined4 *)(iVar9 + 100),&uStack_90);
hp1020_queue_send_candidate(10,&uStack_80);
hp1020_queue_send_candidate(1,&uStack_90);
hp1020_queue_send_candidate(10,&uStack_80);
hp1020_queue_send_candidate
```

### `10010590` `hp1020_status_mgr_thread_candidate`

```c
threadx_queue_receive_wait_candidate(PTR_DAT_100063b4,&uStack_30,0xffffffff);
hp1020_queue_send_candidate(uVar5,&uStack_30);
```

### `10013c18` `hp1020_video_thread_candidate`

```c
threadx_queue_receive_wait_candidate(PTR_DAT_1000676c,aiStack_30,0xffffffff);
hp1020_queue_send_candidate(1,aiStack_30);
```

### `10013d4c` `hp1020_video_reset_dispatch_candidate`

```c
hp1020_send_or_raise_engine_msg_candidate(0,&local_30);
hp1020_send_or_raise_engine_msg_candidate(8,&local_30);
hp1020_send_or_raise_engine_msg_candidate(1,&local_30);
```

### `1001635c` `hp1020_engine_delay_thread_candidate`

```c
iVar2 = threadx_queue_receive_wait_candidate(PTR_DAT_1000699c,aiStack_30,0xffffffff);
hp1020_send_or_raise_engine_msg_candidate(1,aiStack_30);
```

### `100163b0` `hp1020_engine_thread_candidate`

```c
hp1020_queue_send_candidate(1,&uStack_30);
iVar4 = threadx_queue_receive_wait_candidate(PTR_DAT_100069bc,&uStack_30,0x32);
```

### `10010b0c` `hp1020_delay_mgr_receive_thread_candidate`

```c
iVar3 = threadx_queue_receive_wait_candidate(PTR_DAT_10006438,auStack_50,0xffffffff);
hp1020_queue_send_candidate(*puVar6,&uStack_40);
```

