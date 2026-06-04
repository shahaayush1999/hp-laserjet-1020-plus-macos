# HP 1020 Status Mask And Constant Map

This report lists the literal-pool data words and scalar constants used by the
status manager, status-state updater, and engine status poller.

## Target Functions

- `1000a280` `hp1020_status_code_offset_lookup_candidate`
- `1000a2a4` `hp1020_status_word_to_pjl_code_candidate`
- `10010590` `hp1020_status_mgr_thread_candidate`
- `10010838` `hp1020_status_state_update_candidate`
- `10010a3c` `hp1020_status_notify_pending_candidate`
- `10010a8c` `hp1020_status_event_store_candidate`
- `10015c68` `hp1020_engine_status_io_candidate`
- `10015df8` `hp1020_engine_status_poll_candidate`
- `100160a8` `hp1020_engine_preflight_candidate`

## Data References

| Function | Instruction | Data Ref | Symbol | Value | Classification |
|---|---:|---:|---|---:|---|
| `hp1020_status_code_offset_lookup_candidate` | `1000a283` `l32r a3,0x10006014` | `10006014` | `hp1020_status_code_offset_table_ptr` | `0x1001be40` | status mask/constant |
| `hp1020_status_word_to_pjl_code_candidate` | `1000a2b6` `l32r a8,0x10005f74` | `10005f74` | `DAT_10005f74` | `0xff00` |  |
| `hp1020_status_word_to_pjl_code_candidate` | `1000a2c2` `l32r a8,0x10005e74` | `10005e74` | `DAT_10005e74` | `0x20000` | single-bit mask |
| `hp1020_status_word_to_pjl_code_candidate` | `1000a2c8` `l32r a8,0x10005e34` | `10005e34` | `DAT_10005e34` | `0x80000000` | engine/status event word |
| `hp1020_status_word_to_pjl_code_candidate` | `1000a2ce` `l32r a2,0x10006018` | `10006018` | `DAT_10006018` | `0x2711` |  |
| `hp1020_status_word_to_pjl_code_candidate` | `1000a2d4` `l32r a8,0x10005f70` | `10005f70` | `DAT_10005f70` | `0x1001` |  |
| `hp1020_status_word_to_pjl_code_candidate` | `1000a2e0` `l32r a8,0x1000601c` | `1000601c` | `DAT_1000601c` | `0xa028` |  |
| `hp1020_status_word_to_pjl_code_candidate` | `1000a301` `l32r a12,0x10006020` | `10006020` | `PTR_DAT_10006020` | `0x1001bc84` | status mask/constant |
| `hp1020_status_mgr_thread_candidate` | `10010599` `l32r a10,0x100063dc` | `100063dc` | `DAT_100063dc` | `0xe6101100` | engine/status event word |
| `hp1020_status_mgr_thread_candidate` | `100105a4` `l32r a5,0x100063d8` | `100063d8` | `PTR_DAT_100063d8` | `0x1002adb4` | status mask/constant |
| `hp1020_status_mgr_thread_candidate` | `100105a7` `l32r a3,0x100063b0` | `100063b0` | `PTR_DAT_100063b0` | `0x1002aca4` | status mask/constant |
| `hp1020_status_mgr_thread_candidate` | `100105aa` `l32r a4,0x10006408` | `10006408` | `PTR_DAT_10006408` | `0x1001bf3c` | status mask/constant |
| `hp1020_status_mgr_thread_candidate` | `100105ad` `l32r a10,0x100063b4` | `100063b4` | `PTR_hp1020_status_mgr_queue_object_candidate_100063b4` | `0x10028adc` | status mask/constant |
| `hp1020_status_mgr_thread_candidate` | `100105c5` `l32r a8,0x10006414` | `10006414` | `PTR_switchdataD_10004a50_10006414` | `0x10004a50` | status mask/constant |
| `hp1020_status_mgr_thread_candidate` | `100105cb` `l32i.n a8,a8,0x0` | `10004a50` | `switchdataD_10004a50` | `0x100106fe` | status mask/constant |
| `hp1020_status_mgr_thread_candidate` | `100105e0` `l32r a11,0x100063e0` | `100063e0` | `PTR_DAT_100063e0` | `0x1001bf38` | status mask/constant |
| `hp1020_status_mgr_thread_candidate` | `100105e6` `l32i.n a9,a11,0x0` | `1001bf38` | `DAT_1001bf38` | `0x0` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `100105ef` `s32i.n a9,a11,0x0` | `1001bf38` | `DAT_1001bf38` | `0x0` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `100105fc` `l32r a8,0x10006404` | `10006404` | `PTR_switchdataD_10004b30_10006404` | `0x10004b30` | status mask/constant |
| `hp1020_status_mgr_thread_candidate` | `10010602` `l32i a8,a8,0x0` | `10004b30` | `switchdataD_10004b30` | `0x10010608` | status mask/constant |
| `hp1020_status_mgr_thread_candidate` | `10010608` `l32r a10,0x100063e4` | `100063e4` | `DAT_100063e4` | `0x20001601` | engine/status event word |
| `hp1020_status_mgr_thread_candidate` | `1001060e` `l32r a10,0x100063e8` | `100063e8` | `DAT_100063e8` | `0x20001608` | engine/status event word |
| `hp1020_status_mgr_thread_candidate` | `10010614` `l32r a10,0x100063ec` | `100063ec` | `DAT_100063ec` | `0x20001607` | engine/status event word |
| `hp1020_status_mgr_thread_candidate` | `1001061a` `l32r a10,0x100063f0` | `100063f0` | `DAT_100063f0` | `0x20001603` | engine/status event word |
| `hp1020_status_mgr_thread_candidate` | `10010620` `l32r a10,0x100063f4` | `100063f4` | `DAT_100063f4` | `0x20001604` | engine/status event word |
| `hp1020_status_mgr_thread_candidate` | `10010626` `l32r a10,0x100063f8` | `100063f8` | `DAT_100063f8` | `0x20001605` | engine/status event word |
| `hp1020_status_mgr_thread_candidate` | `1001062c` `l32r a10,0x100063fc` | `100063fc` | `DAT_100063fc` | `0x20001606` | engine/status event word |
| `hp1020_status_mgr_thread_candidate` | `10010632` `l32r a10,0x10006400` | `10006400` | `DAT_10006400` | `0x20001602` | engine/status event word |
| `hp1020_status_mgr_thread_candidate` | `1001065c` `l32i.n a9,a4,0x0` | `1001bf3c` | `DAT_1001bf3c` | `0x0` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `10010665` `s32i a9,a4,0x0` | `1001bf3c` | `DAT_1001bf3c` | `0x0` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `1001069d` `l32r a10,0x1000604c` | `1000604c` | `DAT_1000604c` | `0x4800100` | status mask/constant |
| `hp1020_status_mgr_thread_candidate` | `100106b0` `l32i.n a8,a4,0x0` | `1001bf3c` | `DAT_1001bf3c` | `0x0` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `100106b9` `s32i a8,a4,0x0` | `1001bf3c` | `DAT_1001bf3c` | `0x0` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `100106bc` `l32r a10,0x1000604c` | `1000604c` | `DAT_1000604c` | `0x4800100` | status mask/constant |
| `hp1020_status_mgr_thread_candidate` | `1001070f` `l32r a10,0x1000640c` | `1000640c` | `DAT_1000640c` | `0x20001611` | engine/status event word |
| `hp1020_status_mgr_thread_candidate` | `10010715` `l32r a10,0x10006410` | `10006410` | `DAT_10006410` | `0x20001612` | engine/status event word |
| `hp1020_status_mgr_thread_candidate` | `10010727` `l32r a8,0x10005c88` | `10005c88` | `DAT_10005c88` | `0x1000000` | single-bit mask |
| `hp1020_status_mgr_thread_candidate` | `1001072d` `l32r a8,0x10006358` | `10006358` | `DAT_10006358` | `0x70000000` | status mask/constant |
| `hp1020_status_mgr_thread_candidate` | `10010736` `l32r a8,0x1000635c` | `1000635c` | `DAT_1000635c` | `0x60000000` | status mask/constant |
| `hp1020_status_mgr_thread_candidate` | `1001074e` `l32r a10,0x100063d0` | `100063d0` | `PTR_DAT_100063d0` | `0x1002acf4` | status mask/constant |
| `hp1020_status_mgr_thread_candidate` | `10010790` `l32r a10,0x100063d0` | `100063d0` | `PTR_DAT_100063d0` | `0x1002acf4` | status mask/constant |
| `hp1020_status_state_update_candidate` | `1001083f` `l32r a12,0x100063d8` | `100063d8` | `PTR_DAT_100063d8` | `0x1002adb4` | status mask/constant |
| `hp1020_status_state_update_candidate` | `1001085f` `l32r a11,0x10005f74` | `10005f74` | `DAT_10005f74` | `0xff00` |  |
| `hp1020_status_state_update_candidate` | `10010877` `l32r a8,0x10006048` | `10006048` | `DAT_10006048` | `0x2000160a` | engine/status event word |
| `hp1020_status_state_update_candidate` | `1001087d` `l32r a8,0x10006418` | `10006418` | `DAT_10006418` | `0x1600` |  |
| `hp1020_status_state_update_candidate` | `10010890` `l32r a8,0x10005e34` | `10005e34` | `DAT_10005e34` | `0x80000000` | engine/status event word |
| `hp1020_status_state_update_candidate` | `100108a1` `l32r a8,0x10006378` | `10006378` | `DAT_10006378` | `0x7c000000` | status mask/constant |
| `hp1020_status_state_update_candidate` | `100108b5` `l32r a8,0x10005f74` | `10005f74` | `DAT_10005f74` | `0xff00` |  |
| `hp1020_status_state_update_candidate` | `100108cc` `l32r a9,0x1000641c` | `1000641c` | `DAT_1000641c` | `0x160a` |  |
| `hp1020_status_state_update_candidate` | `100108d5` `l32r a8,0x10005e34` | `10005e34` | `DAT_10005e34` | `0x80000000` | engine/status event word |
| `hp1020_status_state_update_candidate` | `100108e9` `l32r a8,0x10006418` | `10006418` | `DAT_10006418` | `0x1600` |  |
| `hp1020_status_state_update_candidate` | `100108f8` `l32r a8,0x10006378` | `10006378` | `DAT_10006378` | `0x7c000000` | status mask/constant |
| `hp1020_status_state_update_candidate` | `10010910` `l32r a11,0x10005f74` | `10005f74` | `DAT_10005f74` | `0xff00` |  |
| `hp1020_status_state_update_candidate` | `1001091b` `l32r a8,0x10005e34` | `10005e34` | `DAT_10005e34` | `0x80000000` | engine/status event word |
| `hp1020_status_state_update_candidate` | `10010948` `l32r a8,0x10006418` | `10006418` | `DAT_10006418` | `0x1600` |  |
| `hp1020_status_state_update_candidate` | `10010968` `l32r a8,0x10006420` | `10006420` | `DAT_10006420` | `0x1100` |  |
| `hp1020_status_state_update_candidate` | `10010971` `l32r a8,0x10006378` | `10006378` | `DAT_10006378` | `0x7c000000` | status mask/constant |
| `hp1020_status_state_update_candidate` | `100109a1` `l32r a8,0x100063d8` | `100063d8` | `PTR_DAT_100063d8` | `0x1002adb4` | status mask/constant |
| `hp1020_status_state_update_candidate` | `100109b1` `l32r a9,0x100063d8` | `100063d8` | `PTR_DAT_100063d8` | `0x1002adb4` | status mask/constant |
| `hp1020_status_state_update_candidate` | `100109bf` `l32r a8,0x10005c84` | `10005c84` | `DAT_10005c84` | `0x2000000` | single-bit mask |
| `hp1020_status_state_update_candidate` | `100109cd` `l32r a8,0x10005f74` | `10005f74` | `DAT_10005f74` | `0xff00` |  |
| `hp1020_status_state_update_candidate` | `100109d0` `l32r a9,0x10005f78` | `10005f78` | `DAT_10005f78` | `0xa00` |  |
| `hp1020_status_state_update_candidate` | `100109d9` `l32r a9,0x10006424` | `10006424` | `DAT_10006424` | `0x1c01` |  |
| `hp1020_status_state_update_candidate` | `100109e8` `l32r a8,0x10006380` | `10006380` | `DAT_10006380` | `0x100000` | single-bit mask |
| `hp1020_status_state_update_candidate` | `10010a27` `l32r a8,0x10005e74` | `10005e74` | `DAT_10005e74` | `0x20000` | single-bit mask |
| `hp1020_status_notify_pending_candidate` | `10010a43` `l32r a10,0x100063d0` | `100063d0` | `PTR_DAT_100063d0` | `0x1002acf4` | status mask/constant |
| `hp1020_status_notify_pending_candidate` | `10010a52` `l32r a5,0x100063b0` | `100063b0` | `PTR_DAT_100063b0` | `0x1002aca4` | status mask/constant |
| `hp1020_status_notify_pending_candidate` | `10010a80` `l32r a10,0x100063d0` | `100063d0` | `PTR_DAT_100063d0` | `0x1002acf4` | status mask/constant |
| `hp1020_status_event_store_candidate` | `10010a8f` `l32r a5,0x1000642c` | `1000642c` | `PTR_DAT_1000642c` | `0x1001bf40` | status mask/constant |
| `hp1020_status_event_store_candidate` | `10010a92` `l32r a3,0x10006428` | `10006428` | `PTR_DAT_10006428` | `0x1002add0` | status mask/constant |
| `hp1020_status_event_store_candidate` | `10010a95` `l32i.n a4,a5,0x0` | `1001bf40` | `DAT_1001bf40` | `0x0` | small message/config/status id |
| `hp1020_status_event_store_candidate` | `10010a9e` `s32i.n a4,a5,0x0` | `1001bf40` | `DAT_1001bf40` | `0x0` | small message/config/status id |
| `hp1020_status_event_store_candidate` | `10010aa8` `s32i.n a3,a5,0x0` | `1001bf40` | `DAT_1001bf40` | `0x0` | small message/config/status id |
| `hp1020_engine_status_io_candidate` | `10015c6d` `l32r a5,0x10005f20` | `10005f20` | `DAT_10005f20` | `0x10000` | single-bit mask |
| `hp1020_engine_status_io_candidate` | `10015c70` `l32r a6,0x10006928` | `10006928` | `hp1020_engine_command_reg_table_word` | `0xb0500004` | status mask/constant |
| `hp1020_engine_status_io_candidate` | `10015c73` `l32r a4,0x10005d04` | `10005d04` | `DAT_10005d04` | `0xffff0000` | status mask/constant |
| `hp1020_engine_status_io_candidate` | `10015c76` `l32r a10,0x10006920` | `10006920` | `PTR_DAT_10006920` | `0x1002f0c4` | status mask/constant |
| `hp1020_engine_status_io_candidate` | `10015c79` `l32r a11,0x1000691c` | `1000691c` | `hp1020_engine_status_reg_table_word` | `0xb050000c` | status mask/constant |
| `hp1020_engine_status_io_candidate` | `10015c7c` `l32r a9,0x10006924` | `10006924` | `DAT_10006924` | `0xfeffffff` | engine/status event word |
| `hp1020_engine_status_io_candidate` | `10015c91` `l32r a8,0x1000691c` | `1000691c` | `hp1020_engine_status_reg_table_word` | `0xb050000c` | status mask/constant |
| `hp1020_engine_status_io_candidate` | `10015cf9` `l32r a8,0x1000692c` | `1000692c` | `DAT_1000692c` | `0xfe001401` | engine/status event word |
| `hp1020_engine_status_io_candidate` | `10015d07` `l32r a2,0x100068e4` | `100068e4` | `DAT_100068e4` | `0xffff` |  |
| `hp1020_engine_status_io_candidate` | `10015d0c` `l32r a8,0x10006920` | `10006920` | `PTR_DAT_10006920` | `0x1002f0c4` | status mask/constant |
| `hp1020_engine_status_poll_candidate` | `10015dfd` `l32r a2,0x10005e34` | `10005e34` | `DAT_10005e34` | `0x80000000` | engine/status event word |
| `hp1020_engine_status_poll_candidate` | `10015e0c` `l32r a9,0x100068e4` | `100068e4` | `DAT_100068e4` | `0xffff` |  |
| `hp1020_engine_status_poll_candidate` | `10015e19` `l32r a8,0x10006940` | `10006940` | `DAT_10006940` | `0x4040` |  |
| `hp1020_engine_status_poll_candidate` | `10015e2c` `l32r a8,0x10005ddc` | `10005ddc` | `DAT_10005ddc` | `0x800` | single-bit mask |
| `hp1020_engine_status_poll_candidate` | `10015e32` `l32r a2,0x10006944` | `10006944` | `DAT_10006944` | `0xf6000300` | engine/status event word |
| `hp1020_engine_status_poll_candidate` | `10015e3b` `l32r a2,0x10006948` | `10006948` | `DAT_10006948` | `0xf6000400` | engine/status event word |
| `hp1020_engine_status_poll_candidate` | `10015e5c` `l32r a8,0x10006954` | `10006954` | `PTR_switchdataD_100059c0_10006954` | `0x100059c0` | status mask/constant |
| `hp1020_engine_status_poll_candidate` | `10015e62` `l32i a8,a8,0x0` | `100059c0` | `switchdataD_100059c0` | `0x10015e6e` | status mask/constant |
| `hp1020_engine_status_poll_candidate` | `10015e68` `l32r a2,0x10006950` | `10006950` | `DAT_10006950` | `0xe6100b0b` | engine/status event word |
| `hp1020_engine_status_poll_candidate` | `10015e6e` `l32r a2,0x1000694c` | `1000694c` | `DAT_1000694c` | `0xe6100b0a` | engine/status event word |
| `hp1020_engine_status_poll_candidate` | `10015e8b` `l32r a2,0x10006958` | `10006958` | `DAT_10006958` | `0xe6100a01` | engine/status event word |
| `hp1020_engine_status_poll_candidate` | `10015e97` `l32r a2,0x1000695c` | `1000695c` | `DAT_1000695c` | `0xe6000d03` | engine/status event word |
| `hp1020_engine_status_poll_candidate` | `10015ea0` `l32r a2,0x10006960` | `10006960` | `DAT_10006960` | `0xe6000d06` | engine/status event word |
| `hp1020_engine_status_poll_candidate` | `10015ea9` `l32r a2,0x10006964` | `10006964` | `DAT_10006964` | `0xe6000d04` | engine/status event word |
| `hp1020_engine_status_poll_candidate` | `10015eb2` `l32r a10,0x10006968` | `10006968` | `DAT_10006968` | `0x501a` |  |
| `hp1020_engine_status_poll_candidate` | `10015ebe` `l32r a8,0x10005f5c` | `10005f5c` | `DAT_10005f5c` | `0x4000` | single-bit mask |
| `hp1020_engine_status_poll_candidate` | `10015ec4` `l32r a10,0x10006968` | `10006968` | `DAT_10006968` | `0x501a` |  |
| `hp1020_engine_status_poll_candidate` | `10015ec7` `l32r a2,0x1000696c` | `1000696c` | `DAT_1000696c` | `0xe6100800` | engine/status event word |
| `hp1020_engine_status_poll_candidate` | `10015ed0` `l32r a8,0x10005f5c` | `10005f5c` | `DAT_10005f5c` | `0x4000` | single-bit mask |
| `hp1020_engine_status_poll_candidate` | `10015ed6` `l32r a2,0x1000696c` | `1000696c` | `DAT_1000696c` | `0xe6100800` | engine/status event word |
| `hp1020_engine_status_poll_candidate` | `10015ee2` `l32r a2,0x100063ec` | `100063ec` | `DAT_100063ec` | `0x20001607` | engine/status event word |
| `hp1020_engine_status_poll_candidate` | `10015ee8` `l32r a8,0x1000605c` | `1000605c` | `DAT_1000605c` | `0x1000` | single-bit mask |
| `hp1020_engine_status_poll_candidate` | `10015eee` `l32r a2,0x100063dc` | `100063dc` | `DAT_100063dc` | `0xe6101100` | engine/status event word |
| `hp1020_engine_status_poll_candidate` | `10015ef4` `l32r a8,0x10005dc8` | `10005dc8` | `DAT_10005dc8` | `0x2000` | single-bit mask |
| `hp1020_engine_status_poll_candidate` | `10015efa` `l32r a2,0x10006970` | `10006970` | `DAT_10006970` | `0xe6100e00` | engine/status event word |
| `hp1020_engine_status_poll_candidate` | `10015f06` `l32r a2,0x10006958` | `10006958` | `DAT_10006958` | `0xe6100a01` | engine/status event word |
| `hp1020_engine_status_poll_candidate` | `10015f0e` `l32r a2,0x1000604c` | `1000604c` | `DAT_1000604c` | `0x4800100` | status mask/constant |
| `hp1020_engine_status_poll_candidate` | `10015f14` `l32r a10,0x10006974` | `10006974` | `DAT_10006974` | `0xa01` |  |
| `hp1020_engine_status_poll_candidate` | `10015f17` `l32r a11,0x10006978` | `10006978` | `DAT_10006978` | `0x14000a04` | status mask/constant |
| `hp1020_engine_status_poll_candidate` | `10015f1a` `l32r a9,0x10006920` | `10006920` | `PTR_DAT_10006920` | `0x1002f0c4` | status mask/constant |
| `hp1020_engine_status_poll_candidate` | `10015f2f` `l32r a9,0x10006364` | `10006364` | `DAT_10006364` | `0xa04` |  |
| `hp1020_engine_status_poll_candidate` | `10015f4a` `l32r a8,0x10006958` | `10006958` | `DAT_10006958` | `0xe6100a01` | engine/status event word |
| `hp1020_engine_status_poll_candidate` | `10015f58` `l32r a8,0x10006920` | `10006920` | `PTR_DAT_10006920` | `0x1002f0c4` | status mask/constant |
| `hp1020_engine_status_poll_candidate` | `10015f5e` `l32r a8,0x1000696c` | `1000696c` | `DAT_1000696c` | `0xe6100800` | engine/status event word |
| `hp1020_engine_status_poll_candidate` | `10015f6d` `l32r a10,0x1000697c` | `1000697c` | `DAT_1000697c` | `0x5043` |  |
| `hp1020_engine_status_poll_candidate` | `10015f78` `l32r a8,0x10006920` | `10006920` | `PTR_DAT_10006920` | `0x1002f0c4` | status mask/constant |
| `hp1020_engine_status_poll_candidate` | `10015fa7` `l32r a11,0x10006920` | `10006920` | `PTR_DAT_10006920` | `0x1002f0c4` | status mask/constant |
| `hp1020_engine_status_poll_candidate` | `10015fae` `l32r a8,0x10006980` | `10006980` | `DAT_10006980` | `0x2e00` |  |
| `hp1020_engine_status_poll_candidate` | `10015fcb` `l32r a9,0x10006920` | `10006920` | `PTR_DAT_10006920` | `0x1002f0c4` | status mask/constant |
| `hp1020_engine_status_poll_candidate` | `10015fd9` `l32r a9,0x10006920` | `10006920` | `PTR_DAT_10006920` | `0x1002f0c4` | status mask/constant |
| `hp1020_engine_status_poll_candidate` | `10015fe0` `l32r a8,0x10005dc8` | `10005dc8` | `DAT_10005dc8` | `0x2000` | single-bit mask |
| `hp1020_engine_status_poll_candidate` | `10015ff8` `l32r a8,0x10006980` | `10006980` | `DAT_10006980` | `0x2e00` |  |
| `hp1020_engine_status_poll_candidate` | `10016000` `l32r a10,0x10006920` | `10006920` | `PTR_DAT_10006920` | `0x1002f0c4` | status mask/constant |
| `hp1020_engine_status_poll_candidate` | `10016009` `l32r a10,0x10006920` | `10006920` | `PTR_DAT_10006920` | `0x1002f0c4` | status mask/constant |
| `hp1020_engine_status_poll_candidate` | `1001600c` `l32r a9,0x10006980` | `10006980` | `DAT_10006980` | `0x2e00` |  |
| `hp1020_engine_preflight_candidate` | `100160b7` `l32r a8,0x100063dc` | `100063dc` | `DAT_100063dc` | `0xe6101100` | engine/status event word |
| `hp1020_engine_preflight_candidate` | `100160c4` `l32r a9,0x10006928` | `10006928` | `hp1020_engine_command_reg_table_word` | `0xb0500004` | status mask/constant |
| `hp1020_engine_preflight_candidate` | `100160c7` `l32r a10,0x10005e74` | `10005e74` | `DAT_10005e74` | `0x20000` | single-bit mask |
| `hp1020_engine_preflight_candidate` | `100160eb` `l32r a8,0x10006920` | `10006920` | `PTR_DAT_10006920` | `0x1002f0c4` | status mask/constant |
| `hp1020_engine_preflight_candidate` | `10016103` `l32r a8,0x1000692c` | `1000692c` | `DAT_1000692c` | `0xfe001401` | engine/status event word |
| `hp1020_engine_preflight_candidate` | `10016114` `l32r a8,0x10006928` | `10006928` | `hp1020_engine_command_reg_table_word` | `0xb0500004` | status mask/constant |
| `hp1020_engine_preflight_candidate` | `1001611c` `l32r a8,0x10005e74` | `10005e74` | `DAT_10005e74` | `0x20000` | single-bit mask |
| `hp1020_engine_preflight_candidate` | `1001612f` `l32r a9,0x10006920` | `10006920` | `PTR_DAT_10006920` | `0x1002f0c4` | status mask/constant |
| `hp1020_engine_preflight_candidate` | `10016132` `l32r a8,0x10006994` | `10006994` | `PTR_DAT_10006994` | `0x1001cd34` | status mask/constant |
| `hp1020_engine_preflight_candidate` | `10016135` `l32r a11,0x10006998` | `10006998` | `PTR_DAT_10006998` | `0x1001cd3c` | status mask/constant |
| `hp1020_engine_preflight_candidate` | `10016138` `s32i a8,a9,0x48` | `1001cd34` | `DAT_1001cd34` | `0x1` | single-bit mask |
| `hp1020_engine_preflight_candidate` | `1001613b` `s32i a11,a9,0x4c` | `1001cd3c` | `DAT_1001cd3c` | `0x2` | single-bit mask |
| `hp1020_engine_preflight_candidate` | `1001614c` `call8 0x10011178` | `1001cd3c` | `DAT_1001cd3c` | `0x2` | single-bit mask |

## Scalar Literals

| Function | Instruction | Value | Classification |
|---|---:|---:|---|
| `hp1020_status_code_offset_lookup_candidate` | `1000a280` `entry a1,0x20` | `0x20` | single-bit mask |
| `hp1020_status_code_offset_lookup_candidate` | `1000a286` `addi.n a5,a3,0x2` | `0x2` | single-bit mask |
| `hp1020_status_code_offset_lookup_candidate` | `1000a28a` `movi a3,0x28` | `0x28` | small message/config/status id |
| `hp1020_status_word_to_pjl_code_candidate` | `1000a2a4` `entry a1,0x20` | `0x20` | single-bit mask |
| `hp1020_status_word_to_pjl_code_candidate` | `1000a2a9` `movi.n a2,0x0` | `0x0` | small message/config/status id |
| `hp1020_status_word_to_pjl_code_candidate` | `1000a2ab` `movi a10,0x1f` | `0x1f` | small message/config/status id |
| `hp1020_status_word_to_pjl_code_candidate` | `1000a2b9` `extui a11,a7,0x0,0x10` | `0x0` | small message/config/status id |
| `hp1020_status_word_to_pjl_code_candidate` | `1000a2b9` `extui a11,a7,0x0,0x10` | `0x10` | single-bit mask |
| `hp1020_status_word_to_pjl_code_candidate` | `1000a2bf` `beqi a8,0x100,0x1000a2ce` | `0x100` | single-bit mask |
| `hp1020_status_word_to_pjl_code_candidate` | `1000a2da` `l32i a10,a6,0x0` | `0x0` | small message/config/status id |
| `hp1020_status_word_to_pjl_code_candidate` | `1000a2e3` `l32i.n a9,a6,0x8` | `0x8` | single-bit mask |
| `hp1020_status_word_to_pjl_code_candidate` | `1000a2e9` `addi a8,a9,0x1` | `0x1` | single-bit mask |
| `hp1020_status_word_to_pjl_code_candidate` | `1000a304` `movi a10,0x0` | `0x0` | small message/config/status id |
| `hp1020_status_word_to_pjl_code_candidate` | `1000a328` `movi.n a10,0x1f` | `0x1f` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `10010590` `entry a1,0x30` | `0x30` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `1001059c` `movi.n a11,0x1` | `0x1` | single-bit mask |
| `hp1020_status_mgr_thread_candidate` | `100105bb` `l32i.n a8,a1,0x0` | `0x0` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `100105bd` `addi a9,a8,-0xf` | `0xfffff1` | status mask/constant |
| `hp1020_status_mgr_thread_candidate` | `100105c0` `movi.n a8,0x34` | `0x34` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `100105cb` `l32i.n a8,a8,0x0` | `0x0` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `100105d0` `l32i.n a10,a1,0x4` | `0x4` | single-bit mask |
| `hp1020_status_mgr_thread_candidate` | `100105d2` `l32i a11,a1,0x8` | `0x8` | single-bit mask |
| `hp1020_status_mgr_thread_candidate` | `100105de` `movi.n a10,0x1b` | `0x1b` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `100105e3` `l8ui a8,a5,0x18` | `0x18` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `100105e6` `l32i.n a9,a11,0x0` | `0x0` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `100105e8` `addi.n a8,a8,0x1` | `0x1` | single-bit mask |
| `hp1020_status_mgr_thread_candidate` | `100105ea` `s8i a8,a5,0x18` | `0x18` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `100105ed` `addi.n a9,a9,0x1` | `0x1` | single-bit mask |
| `hp1020_status_mgr_thread_candidate` | `100105ef` `s32i.n a9,a11,0x0` | `0x0` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `100105f7` `addi.n a10,a10,-0x1` | `0xffffffff` | wait forever / all bits |
| `hp1020_status_mgr_thread_candidate` | `100105f9` `bgeui a10,0x7,0x10010632` | `0x7` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `10010602` `l32i a8,a8,0x0` | `0x0` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `10010635` `movi.n a11,0xa` | `0xa` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `1001063d` `l32i.n a10,a1,0xc` | `0xc` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `10010642` `l32i a8,a10,0x40` | `0x40` | single-bit mask |
| `hp1020_status_mgr_thread_candidate` | `10010645` `bbsi a8,0x2,0x1001064b` | `0x2` | single-bit mask |
| `hp1020_status_mgr_thread_candidate` | `1001064b` `l32i a11,a1,0x8` | `0x8` | single-bit mask |
| `hp1020_status_mgr_thread_candidate` | `10010657` `l8ui a8,a5,0x18` | `0x18` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `1001065c` `l32i.n a9,a4,0x0` | `0x0` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `1001065e` `addi.n a8,a8,-0x1` | `0xffffffff` | wait forever / all bits |
| `hp1020_status_mgr_thread_candidate` | `10010660` `s8i a8,a5,0x18` | `0x18` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `10010663` `addi.n a9,a9,0x1` | `0x1` | single-bit mask |
| `hp1020_status_mgr_thread_candidate` | `10010665` `s32i a9,a4,0x0` | `0x0` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `10010668` `l32i.n a9,a1,0xc` | `0xc` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `1001066a` `l32i.n a10,a9,0x0` | `0x0` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `1001066e` `l32i a8,a10,0x40` | `0x40` | single-bit mask |
| `hp1020_status_mgr_thread_candidate` | `10010671` `bbci a8,0x2,0x10010683` | `0x2` | single-bit mask |
| `hp1020_status_mgr_thread_candidate` | `10010674` `l32i a11,a9,0x4` | `0x4` | single-bit mask |
| `hp1020_status_mgr_thread_candidate` | `10010677` `l16ui a12,a9,0xc` | `0xc` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `1001067a` `l8ui a13,a9,0xb` | `0xb` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `10010683` `l32i.n a8,a1,0xc` | `0xc` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `10010685` `l32i.n a10,a8,0x4` | `0x4` | single-bit mask |
| `hp1020_status_mgr_thread_candidate` | `1001068f` `l32i.n a10,a1,0xc` | `0xc` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `10010697` `l8ui a8,a5,0x18` | `0x18` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `100106a0` `movi.n a11,0xa` | `0xa` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `100106ab` `l8ui a9,a5,0x18` | `0x18` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `100106b0` `l32i.n a8,a4,0x0` | `0x0` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `100106b2` `addi.n a9,a9,-0x1` | `0xffffffff` | wait forever / all bits |
| `hp1020_status_mgr_thread_candidate` | `100106b4` `s8i a9,a5,0x18` | `0x18` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `100106b7` `addi.n a8,a8,0x1` | `0x1` | single-bit mask |
| `hp1020_status_mgr_thread_candidate` | `100106b9` `s32i a8,a4,0x0` | `0x0` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `100106bf` `movi.n a11,0xa` | `0xa` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `100106c7` `l32i.n a10,a1,0xc` | `0xc` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `100106cc` `l32i a8,a10,0x40` | `0x40` | single-bit mask |
| `hp1020_status_mgr_thread_candidate` | `100106cf` `bbsi a8,0x2,0x100106d5` | `0x2` | single-bit mask |
| `hp1020_status_mgr_thread_candidate` | `100106d5` `l32i.n a11,a1,0x8` | `0x8` | single-bit mask |
| `hp1020_status_mgr_thread_candidate` | `100106d7` `l32i a12,a1,0x4` | `0x4` | single-bit mask |
| `hp1020_status_mgr_thread_candidate` | `100106e3` `l32i a10,a1,0xc` | `0xc` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `100106e9` `l32i a8,a10,0x40` | `0x40` | single-bit mask |
| `hp1020_status_mgr_thread_candidate` | `100106ec` `bbsi a8,0x3,0x100106f2` | `0x3` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `100106f2` `l32i a11,a1,0x4` | `0x4` | single-bit mask |
| `hp1020_status_mgr_thread_candidate` | `100106fe` `l8ui a8,a5,0x18` | `0x18` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `10010704` `movi.n a10,0x1b` | `0x1b` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `1001070c` `bnei a10,0x1,0x10010715` | `0x1` | single-bit mask |
| `hp1020_status_mgr_thread_candidate` | `10010718` `movi.n a11,0xa` | `0xa` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `10010720` `movi.n a10,0x3` | `0x3` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `10010725` `l32i.n a9,a5,0x8` | `0x8` | single-bit mask |
| `hp1020_status_mgr_thread_candidate` | `1001073f` `l32i a10,a5,0x14` | `0x14` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `10010751` `movi.n a11,0xff` | `0xff` |  |
| `hp1020_status_mgr_thread_candidate` | `10010753` `movi a6,0x0` | `0x0` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `1001075c` `extui a10,a6,0x0,0x8` | `0x0` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `1001075c` `extui a10,a6,0x0,0x8` | `0x8` | single-bit mask |
| `hp1020_status_mgr_thread_candidate` | `10010762` `l32i.n a9,a7,0x0` | `0x0` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `10010766` `l32i a8,a9,0x40` | `0x40` | single-bit mask |
| `hp1020_status_mgr_thread_candidate` | `10010769` `extui a8,a8,0x13,0x9` | `0x9` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `10010769` `extui a8,a8,0x13,0x9` | `0x13` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `1001076e` `l32i.n a8,a1,0x4` | `0x4` | single-bit mask |
| `hp1020_status_mgr_thread_candidate` | `10010773` `movi.n a10,0x19` | `0x19` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `1001077d` `l32i.n a10,a7,0x0` | `0x0` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `10010785` `addi.n a6,a6,0x1` | `0x1` | single-bit mask |
| `hp1020_status_mgr_thread_candidate` | `10010787` `extui a10,a6,0x0,0x8` | `0x0` | small message/config/status id |
| `hp1020_status_mgr_thread_candidate` | `10010787` `extui a10,a6,0x0,0x8` | `0x8` | single-bit mask |
| `hp1020_status_mgr_thread_candidate` | `1001078a` `movi a8,0x13` | `0x13` | small message/config/status id |
| `hp1020_status_state_update_candidate` | `1001083b` `s32i.n a2,a1,0x20` | `0x20` | single-bit mask |
| `hp1020_status_state_update_candidate` | `1001083d` `movi.n a7,0x0` | `0x0` | small message/config/status id |
| `hp1020_status_state_update_candidate` | `10010844` `l32i a8,a12,0x4` | `0x4` | single-bit mask |
| `hp1020_status_state_update_candidate` | `1001084a` `beqi a8,0x3,0x100108b5` | `0x3` | small message/config/status id |
| `hp1020_status_state_update_candidate` | `1001084d` `bgeui a8,0x4,0x10010856` | `0x4` | single-bit mask |
| `hp1020_status_state_update_candidate` | `10010850` `beqi a8,0x2,0x1001085f` | `0x2` | single-bit mask |
| `hp1020_status_state_update_candidate` | `10010856` `bnei a8,0x4,0x1001085c` | `0x4` | single-bit mask |
| `hp1020_status_state_update_candidate` | `10010862` `l32i a9,a1,0x20` | `0x20` | single-bit mask |
| `hp1020_status_state_update_candidate` | `10010868` `bnei a10,0x100,0x10010877` | `0x100` | single-bit mask |
| `hp1020_status_state_update_candidate` | `1001086b` `l32i a8,a12,0x8` | `0x8` | single-bit mask |
| `hp1020_status_state_update_candidate` | `10010871` `bnei a8,0x100,0x10010877` | `0x100` | single-bit mask |
| `hp1020_status_state_update_candidate` | `10010883` `movi.n a2,0x1` | `0x1` | single-bit mask |
| `hp1020_status_state_update_candidate` | `10010885` `movi.n a8,0x3` | `0x3` | small message/config/status id |
| `hp1020_status_state_update_candidate` | `10010887` `s32i.n a8,a12,0x4` | `0x4` | single-bit mask |
| `hp1020_status_state_update_candidate` | `10010889` `s32i.n a7,a12,0xc` | `0xc` | small message/config/status id |
| `hp1020_status_state_update_candidate` | `1001088b` `s32i.n a9,a12,0x10` | `0x10` | single-bit mask |
| `hp1020_status_state_update_candidate` | `10010896` `l32i.n a11,a12,0x8` | `0x8` | single-bit mask |
| `hp1020_status_state_update_candidate` | `1001089e` `beqi a10,0x100,0x100108b0` | `0x100` | single-bit mask |
| `hp1020_status_state_update_candidate` | `100108b0` `movi.n a2,0x1` | `0x1` | single-bit mask |
| `hp1020_status_state_update_candidate` | `100108b8` `l32i.n a11,a1,0x20` | `0x20` | single-bit mask |
| `hp1020_status_state_update_candidate` | `100108bd` `bnei a10,0x100,0x100108cc` | `0x100` | single-bit mask |
| `hp1020_status_state_update_candidate` | `100108c0` `beqi a3,0xa,0x100108c6` | `0xa` | small message/config/status id |
| `hp1020_status_state_update_candidate` | `100108c6` `movi a2,0x1` | `0x1` | single-bit mask |
| `hp1020_status_state_update_candidate` | `100108cf` `extui a8,a11,0x0,0x10` | `0x0` | small message/config/status id |
| `hp1020_status_state_update_candidate` | `100108cf` `extui a8,a11,0x0,0x10` | `0x10` | single-bit mask |
| `hp1020_status_state_update_candidate` | `100108db` `s8i a7,a12,0x0` | `0x0` | small message/config/status id |
| `hp1020_status_state_update_candidate` | `100108de` `movi.n a2,0x1` | `0x1` | single-bit mask |
| `hp1020_status_state_update_candidate` | `100108e2` `movi.n a8,0x4` | `0x4` | single-bit mask |
| `hp1020_status_state_update_candidate` | `100108e4` `s32i.n a8,a12,0x4` | `0x4` | single-bit mask |
| `hp1020_status_state_update_candidate` | `100108ef` `movi a2,0x1` | `0x1` | single-bit mask |
| `hp1020_status_state_update_candidate` | `100108f2` `s32i a11,a12,0x10` | `0x10` | single-bit mask |
| `hp1020_status_state_update_candidate` | `100108fb` `l32i.n a9,a12,0xc` | `0xc` | small message/config/status id |
| `hp1020_status_state_update_candidate` | `10010909` `s32i.n a11,a12,0xc` | `0xc` | small message/config/status id |
| `hp1020_status_state_update_candidate` | `1001090b` `movi.n a7,0x1` | `0x1` | single-bit mask |
| `hp1020_status_state_update_candidate` | `10010913` `l32i.n a10,a1,0x20` | `0x20` | single-bit mask |
| `hp1020_status_state_update_candidate` | `10010918` `beqi a9,0x100,0x10010921` | `0x100` | single-bit mask |
| `hp1020_status_state_update_candidate` | `10010921` `l32i.n a8,a12,0x14` | `0x14` | small message/config/status id |
| `hp1020_status_state_update_candidate` | `10010926` `movi.n a8,0x1` | `0x1` | single-bit mask |
| `hp1020_status_state_update_candidate` | `10010928` `s8i a8,a12,0x0` | `0x0` | small message/config/status id |
| `hp1020_status_state_update_candidate` | `1001092b` `movi.n a2,0x1` | `0x1` | single-bit mask |
| `hp1020_status_state_update_candidate` | `1001092d` `l8ui a8,a12,0x18` | `0x18` | small message/config/status id |
| `hp1020_status_state_update_candidate` | `10010934` `movi.n a8,0x3` | `0x3` | small message/config/status id |
| `hp1020_status_state_update_candidate` | `10010936` `s32i.n a8,a12,0x4` | `0x4` | single-bit mask |
| `hp1020_status_state_update_candidate` | `10010938` `l32i.n a8,a12,0x10` | `0x10` | single-bit mask |
| `hp1020_status_state_update_candidate` | `1001093a` `s32i.n a7,a12,0xc` | `0xc` | small message/config/status id |
| `hp1020_status_state_update_candidate` | `1001093c` `s32i.n a8,a1,0x20` | `0x20` | single-bit mask |
| `hp1020_status_state_update_candidate` | `10010941` `movi.n a8,0x2` | `0x2` | single-bit mask |
| `hp1020_status_state_update_candidate` | `10010943` `s32i.n a8,a12,0x4` | `0x4` | single-bit mask |
| `hp1020_status_state_update_candidate` | `1001094e` `bbci a10,0x1b,0x10010962` | `0x1b` | small message/config/status id |
| `hp1020_status_state_update_candidate` | `10010951` `l32i.n a8,a12,0x8` | `0x8` | single-bit mask |
| `hp1020_status_state_update_candidate` | `10010953` `movi a2,0x1` | `0x1` | single-bit mask |
| `hp1020_status_state_update_candidate` | `10010959` `addmi a8,a8,-0x1000` | `0xfffff000` | status mask/constant |
| `hp1020_status_state_update_candidate` | `10010962` `s32i a10,a12,0x10` | `0x10` | single-bit mask |
| `hp1020_status_state_update_candidate` | `10010974` `l32i.n a11,a12,0x8` | `0x8` | single-bit mask |
| `hp1020_status_state_update_candidate` | `1001097f` `movi.n a2,0x1` | `0x1` | single-bit mask |
| `hp1020_status_state_update_candidate` | `10010981` `extui a8,a10,0x0,0x10` | `0x0` | small message/config/status id |
| `hp1020_status_state_update_candidate` | `10010981` `extui a8,a10,0x0,0x10` | `0x10` | single-bit mask |
| `hp1020_status_state_update_candidate` | `10010984` `extui a9,a11,0x0,0x10` | `0x0` | small message/config/status id |
| `hp1020_status_state_update_candidate` | `10010984` `extui a9,a11,0x0,0x10` | `0x10` | single-bit mask |
| `hp1020_status_state_update_candidate` | `1001098f` `movi.n a7,0x1` | `0x1` | single-bit mask |
| `hp1020_status_state_update_candidate` | `10010991` `movi.n a8,0x18` | `0x18` | small message/config/status id |
| `hp1020_status_state_update_candidate` | `10010993` `s32i.n a8,a1,0x0` | `0x0` | small message/config/status id |
| `hp1020_status_state_update_candidate` | `10010995` `movi.n a8,0x0` | `0x0` | small message/config/status id |
| `hp1020_status_state_update_candidate` | `10010997` `s32i.n a8,a1,0x4` | `0x4` | single-bit mask |
| `hp1020_status_state_update_candidate` | `100109a6` `s32i.n a8,a1,0x4` | `0x4` | single-bit mask |
| `hp1020_status_state_update_candidate` | `100109b4` `l32i.n a10,a1,0x20` | `0x20` | single-bit mask |
| `hp1020_status_state_update_candidate` | `100109b6` `l32i.n a8,a9,0x8` | `0x8` | single-bit mask |
| `hp1020_status_state_update_candidate` | `100109bb` `movi.n a7,0x1` | `0x1` | single-bit mask |
| `hp1020_status_state_update_candidate` | `100109bd` `s32i.n a10,a9,0x8` | `0x8` | single-bit mask |
| `hp1020_status_state_update_candidate` | `100109c2` `s32i a3,a9,0x14` | `0x14` | small message/config/status id |
| `hp1020_status_state_update_candidate` | `100109c8` `movi.n a8,0xf` | `0xf` | small message/config/status id |
| `hp1020_status_state_update_candidate` | `100109ca` `s32i a8,a1,0x10` | `0x10` | single-bit mask |
| `hp1020_status_state_update_candidate` | `100109dc` `extui a8,a10,0x0,0x10` | `0x0` | small message/config/status id |
| `hp1020_status_state_update_candidate` | `100109dc` `extui a8,a10,0x0,0x10` | `0x10` | single-bit mask |
| `hp1020_status_state_update_candidate` | `100109e2` `movi a8,0x3` | `0x3` | small message/config/status id |
| `hp1020_status_state_update_candidate` | `100109ee` `s32i a7,a1,0x14` | `0x14` | small message/config/status id |
| `hp1020_status_state_update_candidate` | `100109f4` `movi.n a8,0x4` | `0x4` | single-bit mask |
| `hp1020_status_state_update_candidate` | `100109f6` `s32i.n a8,a1,0x14` | `0x14` | small message/config/status id |
| `hp1020_status_state_update_candidate` | `100109f8` `movi.n a10,0x3` | `0x3` | small message/config/status id |
| `hp1020_status_state_update_candidate` | `100109fa` `addi a11,a1,0x10` | `0x10` | single-bit mask |
| `hp1020_status_state_update_candidate` | `10010a03` `l32i.n a10,a1,0x20` | `0x20` | single-bit mask |
| `hp1020_status_state_update_candidate` | `10010a08` `movi.n a8,0x19` | `0x19` | small message/config/status id |
| `hp1020_status_state_update_candidate` | `10010a0a` `s32i.n a8,a1,0x0` | `0x0` | small message/config/status id |
| `hp1020_status_state_update_candidate` | `10010a0c` `movi.n a8,0x0` | `0x0` | small message/config/status id |
| `hp1020_status_state_update_candidate` | `10010a0e` `s32i.n a8,a1,0x4` | `0x4` | single-bit mask |
| `hp1020_status_state_update_candidate` | `10010a18` `addi a8,a1,0x20` | `0x20` | single-bit mask |
| `hp1020_status_state_update_candidate` | `10010a1b` `s32i.n a8,a1,0x4` | `0x4` | single-bit mask |
| `hp1020_status_state_update_candidate` | `10010a25` `l32i.n a10,a1,0x20` | `0x20` | single-bit mask |
| `hp1020_status_state_update_candidate` | `10010a2a` `movi.n a9,0x0` | `0x0` | small message/config/status id |
| `hp1020_status_notify_pending_candidate` | `10010a3c` `entry a1,0x20` | `0x20` | single-bit mask |
| `hp1020_status_notify_pending_candidate` | `10010a3f` `movi.n a11,0xff` | `0xff` |  |
| `hp1020_status_notify_pending_candidate` | `10010a41` `movi.n a6,0x0` | `0x0` | small message/config/status id |
| `hp1020_status_notify_pending_candidate` | `10010a46` `movi a4,0x13` | `0x13` | small message/config/status id |
| `hp1020_status_notify_pending_candidate` | `10010a4f` `extui a10,a6,0x0,0x8` | `0x0` | small message/config/status id |
| `hp1020_status_notify_pending_candidate` | `10010a4f` `extui a10,a6,0x0,0x8` | `0x8` | single-bit mask |
| `hp1020_status_notify_pending_candidate` | `10010a58` `l32i.n a8,a7,0x0` | `0x0` | small message/config/status id |
| `hp1020_status_notify_pending_candidate` | `10010a5c` `l32i a8,a8,0x40` | `0x40` | single-bit mask |
| `hp1020_status_notify_pending_candidate` | `10010a5f` `extui a8,a8,0x1e,0x2` | `0x2` | single-bit mask |
| `hp1020_status_notify_pending_candidate` | `10010a5f` `extui a8,a8,0x1e,0x2` | `0x1e` | small message/config/status id |
| `hp1020_status_notify_pending_candidate` | `10010a64` `movi.n a10,0x3` | `0x3` | small message/config/status id |
| `hp1020_status_notify_pending_candidate` | `10010a6c` `l32i.n a10,a7,0x0` | `0x0` | small message/config/status id |
| `hp1020_status_notify_pending_candidate` | `10010a77` `addi a6,a6,0x1` | `0x1` | single-bit mask |
| `hp1020_status_notify_pending_candidate` | `10010a7a` `extui a10,a6,0x0,0x8` | `0x0` | small message/config/status id |
| `hp1020_status_notify_pending_candidate` | `10010a7a` `extui a10,a6,0x0,0x8` | `0x8` | single-bit mask |
| `hp1020_status_event_store_candidate` | `10010a8c` `entry a1,0x20` | `0x20` | single-bit mask |
| `hp1020_status_event_store_candidate` | `10010a95` `l32i.n a4,a5,0x0` | `0x0` | small message/config/status id |
| `hp1020_status_event_store_candidate` | `10010a9a` `s32i.n a2,a3,0x0` | `0x0` | small message/config/status id |
| `hp1020_status_event_store_candidate` | `10010a9c` `addi.n a4,a4,0x1` | `0x1` | single-bit mask |
| `hp1020_status_event_store_candidate` | `10010a9e` `s32i.n a4,a5,0x0` | `0x0` | small message/config/status id |
| `hp1020_status_event_store_candidate` | `10010aa6` `movi.n a3,0x0` | `0x0` | small message/config/status id |
| `hp1020_status_event_store_candidate` | `10010aa8` `s32i.n a3,a5,0x0` | `0x0` | small message/config/status id |
| `hp1020_engine_status_io_candidate` | `10015c68` `entry a1,0x40` | `0x40` | single-bit mask |
| `hp1020_engine_status_io_candidate` | `10015c6b` `movi.n a7,0x4` | `0x4` | single-bit mask |
| `hp1020_engine_status_io_candidate` | `10015c85` `l32i.n a8,a11,0x0` | `0x0` | small message/config/status id |
| `hp1020_engine_status_io_candidate` | `10015c8f` `s32i.n a8,a11,0x0` | `0x0` | small message/config/status id |
| `hp1020_engine_status_io_candidate` | `10015c97` `l32i.n a8,a8,0x0` | `0x0` | small message/config/status id |
| `hp1020_engine_status_io_candidate` | `10015c9f` `l32i.n a8,a6,0x0` | `0x0` | small message/config/status id |
| `hp1020_engine_status_io_candidate` | `10015cad` `s32i a8,a6,0x0` | `0x0` | small message/config/status id |
| `hp1020_engine_status_io_candidate` | `10015cb3` `l32i.n a8,a6,0x0` | `0x0` | small message/config/status id |
| `hp1020_engine_status_io_candidate` | `10015cb5` `movi.n a10,0x6` | `0x6` | small message/config/status id |
| `hp1020_engine_status_io_candidate` | `10015cbd` `s32i.n a8,a6,0x0` | `0x0` | small message/config/status id |
| `hp1020_engine_status_io_candidate` | `10015cc7` `movi.n a11,0x1` | `0x1` | single-bit mask |
| `hp1020_engine_status_io_candidate` | `10015cc9` `movi.n a12,0x3` | `0x3` | small message/config/status id |
| `hp1020_engine_status_io_candidate` | `10015cdf` `movi.n a10,0x1` | `0x1` | single-bit mask |
| `hp1020_engine_status_io_candidate` | `10015ce7` `addi a7,a7,-0x1` | `0xffffff` | status mask/constant |
| `hp1020_engine_status_io_candidate` | `10015cef` `movi.n a8,0x17` | `0x17` | small message/config/status id |
| `hp1020_engine_status_io_candidate` | `10015cf1` `s32i.n a8,a1,0x10` | `0x10` | single-bit mask |
| `hp1020_engine_status_io_candidate` | `10015cf3` `s32i.n a7,a1,0x18` | `0x18` | small message/config/status id |
| `hp1020_engine_status_io_candidate` | `10015cf5` `s32i.n a7,a1,0x1c` | `0x1c` | small message/config/status id |
| `hp1020_engine_status_io_candidate` | `10015cf7` `movi.n a10,0x1` | `0x1` | single-bit mask |
| `hp1020_engine_status_io_candidate` | `10015cfc` `addi a11,a1,0x10` | `0x10` | single-bit mask |
| `hp1020_engine_status_io_candidate` | `10015cff` `s32i.n a8,a1,0x14` | `0x14` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `10015df8` `entry a1,0x40` | `0x40` | single-bit mask |
| `hp1020_engine_status_poll_candidate` | `10015dfb` `s32i.n a2,a1,0x10` | `0x10` | single-bit mask |
| `hp1020_engine_status_poll_candidate` | `10015e00` `movi.n a4,0x0` | `0x0` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `10015e04` `movi.n a3,0x1` | `0x1` | single-bit mask |
| `hp1020_engine_status_poll_candidate` | `10015e11` `extui a8,a6,0x0,0x10` | `0x0` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `10015e11` `extui a8,a6,0x0,0x10` | `0x10` | single-bit mask |
| `hp1020_engine_status_poll_candidate` | `10015e27` `movi.n a10,0x20` | `0x20` | single-bit mask |
| `hp1020_engine_status_poll_candidate` | `10015e38` `bbci a10,0x15,0x10015e41` | `0x15` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `10015e41` `movi.n a10,0x2` | `0x2` | single-bit mask |
| `hp1020_engine_status_poll_candidate` | `10015e49` `bbci a7,0x17,0x10015e79` | `0x17` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `10015e4c` `movi.n a10,0x13` | `0x13` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `10015e51` `extui a10,a10,0x1,0x6` | `0x1` | single-bit mask |
| `hp1020_engine_status_poll_candidate` | `10015e51` `extui a10,a10,0x1,0x6` | `0x6` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `10015e54` `addi a10,a10,-0x8` | `0xfffff8` | status mask/constant |
| `hp1020_engine_status_poll_candidate` | `10015e57` `movi.n a8,0x10` | `0x10` | single-bit mask |
| `hp1020_engine_status_poll_candidate` | `10015e62` `l32i a8,a8,0x0` | `0x0` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `10015e71` `movi.n a10,0x16` | `0x16` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `10015e7f` `movi a10,0x16` | `0x16` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `10015e85` `extui a8,a10,0x0,0x10` | `0x0` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `10015e85` `extui a8,a10,0x0,0x10` | `0x10` | single-bit mask |
| `hp1020_engine_status_poll_candidate` | `10015e88` `bnei a8,0x40,0x10015e94` | `0x40` | single-bit mask |
| `hp1020_engine_status_poll_candidate` | `10015e94` `bbci a10,0x1b,0x10015e9d` | `0x1b` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `10015e9d` `bbci a10,0x1c,0x10015ea6` | `0x1c` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `10015ea6` `bbci a10,0x1d,0x10015eac` | `0x1d` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `10015ebb` `bbci a10,0x19,0x10015f11` | `0x19` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `10015f00` `bbci a6,0x19,0x10015f06` | `0x19` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `10015f03` `bbci a7,0x16,0x10015f11` | `0x16` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `10015f09` `movi.n a4,0x1` | `0x1` | single-bit mask |
| `hp1020_engine_status_poll_candidate` | `10015f11` `extui a8,a2,0x0,0x10` | `0x0` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `10015f11` `extui a8,a2,0x0,0x10` | `0x10` | single-bit mask |
| `hp1020_engine_status_poll_candidate` | `10015f29` `extui a8,a9,0x0,0x10` | `0x0` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `10015f29` `extui a8,a9,0x0,0x10` | `0x10` | single-bit mask |
| `hp1020_engine_status_poll_candidate` | `10015f2c` `bnei a8,0x100,0x10015f58` | `0x100` | single-bit mask |
| `hp1020_engine_status_poll_candidate` | `10015f32` `extui a8,a2,0x0,0x10` | `0x0` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `10015f32` `extui a8,a2,0x0,0x10` | `0x10` | single-bit mask |
| `hp1020_engine_status_poll_candidate` | `10015f38` `movi.n a7,0x0` | `0x0` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `10015f40` `movi.n a8,0x17` | `0x17` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `10015f42` `s32i.n a8,a1,0x0` | `0x0` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `10015f44` `s32i.n a7,a1,0x8` | `0x8` | single-bit mask |
| `hp1020_engine_status_poll_candidate` | `10015f46` `s32i.n a7,a1,0xc` | `0xc` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `10015f48` `movi.n a10,0x1` | `0x1` | single-bit mask |
| `hp1020_engine_status_poll_candidate` | `10015f4f` `s32i a8,a1,0x4` | `0x4` | single-bit mask |
| `hp1020_engine_status_poll_candidate` | `10015f73` `movi.n a10,0x1` | `0x1` | single-bit mask |
| `hp1020_engine_status_poll_candidate` | `10015f7b` `movi a5,0x1` | `0x1` | single-bit mask |
| `hp1020_engine_status_poll_candidate` | `10015f84` `l32i.n a12,a1,0x10` | `0x10` | single-bit mask |
| `hp1020_engine_status_poll_candidate` | `10015f86` `movi.n a9,0x1` | `0x1` | single-bit mask |
| `hp1020_engine_status_poll_candidate` | `10015f88` `addi.n a8,a12,-0x1` | `0xffffffff` | wait forever / all bits |
| `hp1020_engine_status_poll_candidate` | `10015f8d` `bnei a5,0x1,0x10015fa7` | `0x1` | single-bit mask |
| `hp1020_engine_status_poll_candidate` | `10015f90` `movi.n a8,0x17` | `0x17` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `10015f92` `s32i.n a8,a1,0x0` | `0x0` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `10015f94` `s32i.n a2,a1,0x4` | `0x4` | single-bit mask |
| `hp1020_engine_status_poll_candidate` | `10015f96` `movi.n a8,0x0` | `0x0` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `10015f98` `s32i.n a8,a1,0x8` | `0x8` | single-bit mask |
| `hp1020_engine_status_poll_candidate` | `10015f9a` `s32i.n a8,a1,0xc` | `0xc` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `10015faa` `l32i.n a8,a11,0x38` | `0x38` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `10015fb8` `l16ui a8,a11,0x64` | `0x64` |  |
| `hp1020_engine_status_poll_candidate` | `10015fbe` `s32i.n a10,a11,0x38` | `0x38` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `10015fc0` `movi.n a8,0x1` | `0x1` | single-bit mask |
| `hp1020_engine_status_poll_candidate` | `10015fc2` `s32i a8,a11,0x30` | `0x30` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `10015fd0` `l32i.n a8,a9,0x30` | `0x30` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `10015fd5` `movi.n a8,0x1` | `0x1` | single-bit mask |
| `hp1020_engine_status_poll_candidate` | `10015fd7` `s32i.n a8,a9,0x30` | `0x30` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `10015fdc` `l32i.n a8,a9,0x2c` | `0x2c` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `10015fe8` `bbci a6,0x18,0x10015ff0` | `0x18` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `10015feb` `movi.n a8,0x1` | `0x1` | single-bit mask |
| `hp1020_engine_status_poll_candidate` | `10015fed` `s32i a8,a9,0x3c` | `0x3c` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `10015ff0` `movi.n a8,0x1` | `0x1` | single-bit mask |
| `hp1020_engine_status_poll_candidate` | `10015ff2` `s32i a8,a9,0x30` | `0x30` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `10015ff5` `s32i a10,a9,0x2c` | `0x2c` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `10016003` `l32i.n a8,a10,0x3c` | `0x3c` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `10016007` `s32i.n a9,a10,0x3c` | `0x3c` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `1001600f` `l16ui a8,a10,0x64` | `0x64` |  |
| `hp1020_engine_status_poll_candidate` | `10016012` `movi.n a11,0x0` | `0x0` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `10016017` `movi.n a9,0x1` | `0x1` | single-bit mask |
| `hp1020_engine_status_poll_candidate` | `1001601c` `s32i.n a11,a10,0x34` | `0x34` | small message/config/status id |
| `hp1020_engine_status_poll_candidate` | `1001601e` `s16i a6,a10,0x64` | `0x64` |  |
| `hp1020_engine_preflight_candidate` | `100160a8` `entry a1,0x40` | `0x40` | single-bit mask |
| `hp1020_engine_preflight_candidate` | `100160ab` `movi.n a7,0x0` | `0x0` | small message/config/status id |
| `hp1020_engine_preflight_candidate` | `100160ad` `movi.n a8,0x17` | `0x17` | small message/config/status id |
| `hp1020_engine_preflight_candidate` | `100160af` `s32i.n a8,a1,0x0` | `0x0` | small message/config/status id |
| `hp1020_engine_preflight_candidate` | `100160b1` `s32i.n a7,a1,0x8` | `0x8` | single-bit mask |
| `hp1020_engine_preflight_candidate` | `100160b3` `s32i.n a7,a1,0xc` | `0xc` | small message/config/status id |
| `hp1020_engine_preflight_candidate` | `100160b5` `movi.n a10,0x1` | `0x1` | single-bit mask |
| `hp1020_engine_preflight_candidate` | `100160bc` `s32i.n a8,a1,0x4` | `0x4` | single-bit mask |
| `hp1020_engine_preflight_candidate` | `100160cd` `l32i.n a8,a9,0x0` | `0x0` | small message/config/status id |
| `hp1020_engine_preflight_candidate` | `100160d5` `s32i.n a8,a9,0x0` | `0x0` | small message/config/status id |
| `hp1020_engine_preflight_candidate` | `100160da` `l32i.n a8,a9,0x0` | `0x0` | small message/config/status id |
| `hp1020_engine_preflight_candidate` | `100160e2` `movi a10,0x14` | `0x14` | small message/config/status id |
| `hp1020_engine_preflight_candidate` | `100160ee` `l32i.n a8,a8,0x24` | `0x24` | small message/config/status id |
| `hp1020_engine_preflight_candidate` | `100160f0` `addi.n a7,a7,0x1` | `0x1` | single-bit mask |
| `hp1020_engine_preflight_candidate` | `100160f4` `movi.n a8,0x1e` | `0x1e` | small message/config/status id |
| `hp1020_engine_preflight_candidate` | `100160f9` `movi.n a8,0x17` | `0x17` | small message/config/status id |
| `hp1020_engine_preflight_candidate` | `100160fb` `s32i.n a8,a1,0x10` | `0x10` | single-bit mask |
| `hp1020_engine_preflight_candidate` | `100160fd` `s32i.n a6,a1,0x18` | `0x18` | small message/config/status id |
| `hp1020_engine_preflight_candidate` | `100160ff` `s32i.n a6,a1,0x1c` | `0x1c` | small message/config/status id |
| `hp1020_engine_preflight_candidate` | `10016101` `movi.n a10,0x1` | `0x1` | single-bit mask |
| `hp1020_engine_preflight_candidate` | `10016106` `addi a11,a1,0x10` | `0x10` | single-bit mask |
| `hp1020_engine_preflight_candidate` | `10016109` `s32i.n a8,a1,0x14` | `0x14` | small message/config/status id |
| `hp1020_engine_preflight_candidate` | `1001611a` `l32i.n a9,a8,0x0` | `0x0` | small message/config/status id |
| `hp1020_engine_preflight_candidate` | `10016122` `movi a10,0x3c` | `0x3c` | small message/config/status id |
| `hp1020_engine_preflight_candidate` | `1001612b` `movi.n a7,0xf` | `0xf` | small message/config/status id |
| `hp1020_engine_preflight_candidate` | `1001613e` `movi.n a8,0x0` | `0x0` | small message/config/status id |
| `hp1020_engine_preflight_candidate` | `10016154` `extui a11,a11,0x0,0x8` | `0x0` | small message/config/status id |
| `hp1020_engine_preflight_candidate` | `10016154` `extui a11,a11,0x0,0x8` | `0x8` | single-bit mask |

## Current Interpretation

- The engine poller emits many full-width event words, while the status-state updater mostly compares masks and stores a normalized status word.
- `hp1020_status_word_to_pjl_code_candidate` is where stored status words become user-visible PJL `CODE=` numbers.
- Constants in this report are not fully named yet; this file narrows the next manual pass to a few literal-pool words rather than the whole firmware.
