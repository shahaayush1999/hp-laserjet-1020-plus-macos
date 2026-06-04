# HP 1020 ZjStream Parser Boundary

This pass maps the parser-side boundary between USB receive and the JobMgr/page/video objects already identified.

## Proven Anchors

- USB2Thread descriptor `0x10005fc4` points at task body `0x10008ff0`, parser entry `0x10009d34`, `JZJZ` magic `0x1001bc78`, and parser/table data near `0x1001bc80`.
- `0x10009d34` reads `strlen("JZJZ")`, reads exactly that magic from the stream, compares it, then enters a 16-byte ZjStream chunk-header loop.
- The chunk loop checks the header signature word at offset `+0x0e` against the constant pointed to by `0x10006000`, which matches ZjStream's `ZZ` signature.
- For each chunk, it reads `size`, `type`, and `items` fields from the 16-byte header buffer at `0x10022ce0` via pointer word `0x10005ffc`.
- If `type < 0x0d`, it dispatches through the switch table at `0x100036f0`.

## ZjStream Type Switch Table

| Type | ZjStream name | Target | Containing function |
|---:|---|---:|---|
| `0x00` | `ZJT_START_DOC` | `0x10009efe` | `hp1020_zjs_parser_entry_candidate` |
| `0x01` | `ZJT_END_DOC` | `0x1000a1b3` | `hp1020_zjs_parser_entry_candidate` |
| `0x02` | `ZJT_START_PAGE` | `0x10009f86` | `hp1020_zjs_parser_entry_candidate` |
| `0x03` | `ZJT_END_PAGE` | `0x1000a19e` | `hp1020_zjs_parser_entry_candidate` |
| `0x04` | `ZJT_JBIG_BIH` | `0x1000a006` | `hp1020_zjs_parser_entry_candidate` |
| `0x05` | `ZJT_JBIG_BID` | `0x1000a014` | `hp1020_zjs_parser_entry_candidate` |
| `0x06` | `ZJT_END_JBIG` | `0x1000a053` | `hp1020_zjs_parser_entry_candidate` |
| `0x07` | `ZJT_SIGNATURE` | `0x1000a1ef` | `hp1020_zjs_parser_entry_candidate` |
| `0x08` | `ZJT_RAW_IMAGE` | `0x1000a1ef` | `hp1020_zjs_parser_entry_candidate` |
| `0x09` | `ZJT_START_PLANE` | `0x1000a1ef` | `hp1020_zjs_parser_entry_candidate` |
| `0x0a` | `ZJT_END_PLANE` | `0x1000a173` | `hp1020_zjs_parser_entry_candidate` |
| `0x0b` | `ZJT_2600N_PAUSE` | `0x1000a1d6` | `hp1020_zjs_parser_entry_candidate` |
| `0x0c` | `ZJT_2600N` | `0x1000a05d` | `hp1020_zjs_parser_entry_candidate` |

## Important Reference Hits

| Function | Line | Kind | Code |
|---:|---:|---|---|
| `10009d34` `hp1020_zjs_parser_entry_candidate` | `22` | `zjs_magic_ref` | `puVar3 = PTR_hp1020_zjs_magic_jzjz_10005fe0;` |
| `10009d34` `hp1020_zjs_parser_entry_candidate` | `28` | `zjs_magic_ref` | `uStack_70 = hp1020_strlen_like(PTR_hp1020_zjs_magic_jzjz_10005fe0);` |
| `10009d34` `hp1020_zjs_parser_entry_candidate` | `29` | `zjs_header_buffer_ref` | `puVar8 = hp1020_zjs_header_buffer_ptr_word;` |
| `10009d34` `hp1020_zjs_parser_entry_candidate` | `30` | `zjs_header_buffer_ref` | `iVar1 = (**(code **)(param_1 + 0xc))(param_1,hp1020_zjs_header_buffer_ptr_word,uStack_70,0);` |
| `10009d34` `hp1020_zjs_parser_entry_candidate` | `54` | `zjs_header_buffer_ref` | `uStack_34 = (uint)*(ushort *)(hp1020_zjs_header_buffer_ptr_word + 0xc);` |
| `10009d34` `hp1020_zjs_parser_entry_candidate` | `55` | `zjs_header_buffer_ref` | `uVar6 = (*(int *)hp1020_zjs_header_buffer_ptr_word + -0x10) - uStack_34;` |
| `10009d34` `hp1020_zjs_parser_entry_candidate` | `64` | `zjs_item_or_reserved_size_read` | `(uVar2 = (**(code **)(param_1 + 0xc))(param_1,puStack_3c,uStack_34,0), uVar2 != uStack_34` |
| `10009d34` `hp1020_zjs_parser_entry_candidate` | `79` | `zjs_header_buffer_ref` | `uVar2 = *(uint *)(hp1020_zjs_header_buffer_ptr_word + 4);` |
| `10009d34` `hp1020_zjs_parser_entry_candidate` | `80` | `zjs_header_buffer_ref` | `uVar5 = *(undefined4 *)(hp1020_zjs_header_buffer_ptr_word + 8);` |
| `10009d34` `hp1020_zjs_parser_entry_candidate` | `83` | `zjs_header_buffer_ref` | `(param_1,hp1020_zjs_header_buffer_ptr_word,uStack_70,0);` |
| `10009d34` `hp1020_zjs_parser_entry_candidate` | `88` | `zjs_header_buffer_ref` | `(*pcVar7)(param_1,hp1020_zjs_header_buffer_ptr_word,uVar4);` |
| `10009d34` `hp1020_zjs_parser_entry_candidate` | `96` | `zjs_header_buffer_ref` | `if (*(ushort *)(hp1020_zjs_header_buffer_ptr_word + 0xe) !=` |
| `10009d34` `hp1020_zjs_parser_entry_candidate` | `103` | `zjs_type_bounds_check` | `if (uVar2 &lt; 0xd) {` |
| `10009d34` `hp1020_zjs_parser_entry_candidate` | `132` | `jobmgr_queue_send` | `hp1020_queue_send_candidate(3,auStack_1d0);` |
| `1000e414` `hp1020_job_mgr_thread_candidate` | `45` | `jobmgr_video_runtime_block` | `puVar6 = PTR_DAT_10006304;` |
| `1000e414` `hp1020_job_mgr_thread_candidate` | `181` | `jobmgr_video_runtime_block` | `puVar4 = PTR_DAT_10006304;` |
| `1000e414` `hp1020_job_mgr_thread_candidate` | `183` | `jobmgr_video_runtime_block` | `*(undefined4 *)(iVar9 + 0x84) = *(undefined4 *)(PTR_DAT_10006304 + 4);` |
| `1000e414` `hp1020_job_mgr_thread_candidate` | `251` | `jobmgr_queue_send` | `hp1020_queue_send_candidate(3,&amp;uStack_80);` |
| `1000e414` `hp1020_job_mgr_thread_candidate` | `501` | `jobmgr_video_runtime_block` | `hp1020_memcpy_candidate(PTR_DAT_10006304,iStack_84,0x14);` |
| `1000e414` `hp1020_job_mgr_thread_candidate` | `508` | `jobmgr_video_runtime_block` | `*(undefined4 *)(iVar9 + 0x84) = *(undefined4 *)(PTR_DAT_10006304 + 4);` |
| `1000ed90` `FUN_1000ed90` | `27` | `zjs_item_or_reserved_size_read` | `((*(ushort *)(iVar7 + 0x48) != *(ushort *)(iVar7 + 0xc) &amp;&amp;` |
| `1000ed90` `FUN_1000ed90` | `29` | `zjs_item_or_reserved_size_read` | `uVar1 = *(ushort *)(iVar7 + 0xc);` |
| `1000ed90` `FUN_1000ed90` | `45` | `zjs_item_or_reserved_size_read` | `if (((iVar7 != 0) &amp;&amp; (*(ushort *)(iVar7 + 0x48) != *(ushort *)(iVar7 + 0xc))) &amp;&amp;` |
| `1000ed90` `FUN_1000ed90` | `47` | `zjs_item_or_reserved_size_read` | `uVar1 = *(ushort *)(iVar7 + 0xc);` |
| `1000f814` `FUN_1000f814` | `14` | `jobmgr_queue_send` | `hp1020_queue_send_candidate(3,param_1);` |
| `1000f84c` `FUN_1000f84c` | `157` | `zjs_item_or_reserved_size_read` | `*(uint *)(puVar3 + 0xc) = (uint)*(ushort *)(param_1 + 0xe);` |
| `10010338` `FUN_10010338` | `26` | `jobmgr_queue_send` | `hp1020_queue_send_candidate(3,local_30);` |
| `10010398` `FUN_10010398` | `17` | `jobmgr_queue_send` | `hp1020_queue_send_candidate(3,local_30);` |
| `10010398` `FUN_10010398` | `25` | `jobmgr_queue_send` | `hp1020_queue_send_candidate(3,local_30);` |
| `100103f8` `FUN_100103f8` | `8` | `jobmgr_queue_send` | `hp1020_queue_send_candidate(3,local_30);` |
| `1001040c` `FUN_1001040c` | `8` | `jobmgr_queue_send` | `hp1020_queue_send_candidate(3,local_30);` |
| `10010838` `FUN_10010838` | `130` | `jobmgr_queue_send` | `hp1020_queue_send_candidate(3,&amp;uStack_40);` |
| `10013140` `hp1020_alloc_with_retry_candidate` | `38` | `jobmgr_queue_send` | `hp1020_queue_send_candidate(3,local_30);` |
| `100140f8` `hp1020_video_refresh_raw_bands_candidate` | `22` | `raw_band_video_consumer` | `FUN_10006f00(DAT_10005e74,PTR_s_refreshRawBands__ic_pBidBlock_0x_100067e0,` |
| `10016d23` `FUN_10016d23` | `105` | `zjs_type_bounds_check` | `if (uVar2 &lt; 0xd) {` |

## Working Interpretation

- This identifies the main host print-stream parser. It is not scanner code, and it is not a generic macOS driver path; it is embedded firmware parsing ZjStream chunks.
- The firmware supports at least ZjStream chunk types `0..12`, matching the `foo2zjs` constants from `vendor/foo2zjs-source/zjs.h`.
- The parser cases are branch targets inside or adjacent to `0x10009d34`, not clean named C functions. That is why earlier function-level call clustering did not expose them cleanly.
- `ZJT_JBIG_BIH` at `0x1000a006` is the previously unresolved producer for JobMgr message `0x29`: it stores message id `0x29`, stores the chunk payload pointer in payload word 3, and sends queue id `3`.
- `ZJT_JBIG_BID` at `0x1000a014` builds a `0x78`-byte raster/list node, stores the chunk payload pointer at node payload `+0x54`, stores chunk length at `+0x48`, and sends JobMgr message `0x2a`.
- `ZJT_2600N` at `0x1000a05d` has a compatibility-looking path that can also send JobMgr message `9`; for HP 1020 daily printing the direct JBIG_BID `0x2a` path is the cleaner raster-data producer to follow first.
- The earlier JobMgr message `9` question was probably too narrow. The parser proves that raster-list traffic can arrive as `0x2a` as well, so the next JobMgr pass should include cases `9`, `0x29`, `0x2a`, and `0x2b` together.
- `0x100140f8` remains a later video/raw-band consumer. It is useful for output-side validation, but it is downstream of the parser.

## Case Body Summary

| ZjStream case | Parser target | Proven action | JobMgr message |
|---|---:|---|---:|
| `ZJT_START_DOC` | `0x10009efe` | allocates/parses a document object and sends it to JobMgr | `1` |
| `ZJT_END_DOC` | `0x1000a1b3` | sends document-end and closes parser state | `2` |
| `ZJT_START_PAGE` | `0x10009f86` | allocates `0x50` child/page object, creates `0x94` video work object, parses page items | `3`, then `5` |
| `ZJT_END_PAGE` | `0x1000a19e` | sends page-end | `6` |
| `ZJT_JBIG_BIH` | `0x1000a006` | sends first 20-byte JBIG BIH payload pointer | `0x29` |
| `ZJT_JBIG_BID` | `0x1000a014` | wraps compressed raster payload in a list node | `0x2a` |
| `ZJT_END_JBIG` | `0x1000a053` | sends end-of-JBIG marker | `0x2b` |
| `ZJT_END_PLANE` | `0x1000a173` | parses plane-end fields and sends plane/event message | `8` |

## Next Reverse-Engineering Step

Run a focused JobMgr pass for messages `0x29`, `0x2a`, and `0x2b`, then connect `0x2a`'s list-node shape to the `0x94` video work object's raster list at `+0x50`.
