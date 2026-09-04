# Direct ZjStream page work construction

Status: **pass**. Offline ELF-byte verification only.

START_PAGE calls the item builder directly on the allocated 0x94 work; no hidden copy or alias is required.

- +0x26 is VIDEO_Y; +0x30 is RET (absent => zero); +0x32 is ECONOMODE.
- +0x22 is VIDEO_BPP, while NBIE is +0x12. Default BPP=2; 600x600 variant=1; 2400x600 variant=4.
- 0x10010398 -> 0x100104c8 is a different constructor path; its missing stores do not establish missing START_PAGE fields.
- The saved 0x10009d34 decompilation stops at the indirect switch and omitted these handlers.

| Item | ID | Work offset | Target |
|---|---|---|---|
| ZJI_DMPAPER | 0x03 | +0x0a | 0x10009bae |
| ZJI_DMCOPIES | 0x04 | +0x0c | 0x10009bb7 |
| ZJI_DMMEDIATYPE | 0x06 | +0x10 | 0x10009bcf |
| ZJI_NBIE | 0x07 | +0x12 | 0x10009bd8 |
| ZJI_RESOLUTION_X | 0x08 | +0x14 | 0x10009be1 |
| ZJI_RESOLUTION_Y | 0x09 | +0x16 | 0x10009bf0 |
| ZJI_OFFSET_X | 0x0a | +0x18 | 0x10009bff |
| ZJI_OFFSET_Y | 0x0b | +0x1c | 0x10009c08 |
| ZJI_RASTER_X | 0x0c | +0x1e | 0x10009c3b |
| ZJI_RASTER_Y | 0x0d | +0x20 | 0x10009c44 |
| ZJI_VIDEO_BPP | 0x10 | +0x22 | 0x10009c20 |
| ZJI_VIDEO_X | 0x11 | +0x24 | 0x10009c29 |
| ZJI_VIDEO_Y | 0x12 | +0x26 | 0x10009c32 |
| ZJI_INTERLACE | 0x13 | +0x2a | 0x10009c4d |
| ZJI_RET | 0x16 | +0x30 | 0x10009c83 |
| ZJI_ECONOMODE | 0x17 | +0x32 | 0x10009c8c |

| Check | Address | Bytes | Status | Meaning |
|---|---|---|---|---|
| chunk_switch_base | 0x1000600c | 100036f0 | present | chunk-type switch table |
| start_page_target | 0x100036f8 | 10009f86 | present | ZjStream type 2 selects this handler |
| work_allocate | 0x10009faf | 58149e | present | call8 0x1000f228; returns 0x94 work in a10 |
| save_work | 0x10009fb5 | d7a0 | present | mov.n a7,a10 |
| builder_destination | 0x10009fe0 | da702e7477 | present | mov.n a10,a7; only writes flag byte +0x77 |
| builder_arguments | 0x10009fe5 | 2b12652c1267dd305bfed7 | present | a11=item buffer, a12=reserved length, a13=item count; call8 0x10009b4c |
| work_queue_message | 0x10009ffd | c08598109713 | present | queue message 5, payload a7 at stack+12 |
| builder_preserves_destination | 0x10009b4f | d720 | present | mov.n a7,a2 saves incoming call8 destination |
| builder_destination_for_stores | 0x10009b67 | d270 | present | mov.n a2,a7 restores destination before item dispatch |
| default_copies | 0x10009ff3 | 287106cc83c0f12f7506 | present | zero copies become one |
| ZJI_DMPAPER_load | 0x10009bae | 283105 | present | l16ui a8,a3,10 takes low half of BE uint32 item |
| ZJI_DMPAPER_store | 0x10009bb1 | 282505 | present | s16i a8,a2,10 |
| ZJI_DMCOPIES_load | 0x10009bb7 | 283105 | present | l16ui a8,a3,10 takes low half of BE uint32 item |
| ZJI_DMCOPIES_store | 0x10009bba | 282506 | present | s16i a8,a2,12 |
| ZJI_DMMEDIATYPE_load | 0x10009bcf | 283105 | present | l16ui a8,a3,10 takes low half of BE uint32 item |
| ZJI_DMMEDIATYPE_store | 0x10009bd2 | 282508 | present | s16i a8,a2,16 |
| ZJI_NBIE_load | 0x10009bd8 | 283105 | present | l16ui a8,a3,10 takes low half of BE uint32 item |
| ZJI_NBIE_store | 0x10009bdb | 282509 | present | s16i a8,a2,18 |
| ZJI_RESOLUTION_X_load | 0x10009be1 | 283105 | present | l16ui a8,a3,10 takes low half of BE uint32 item |
| ZJI_RESOLUTION_X_store | 0x10009be7 | 28250a | present | s16i a8,a2,20 |
| ZJI_RESOLUTION_Y_load | 0x10009bf0 | 283105 | present | l16ui a8,a3,10 takes low half of BE uint32 item |
| ZJI_RESOLUTION_Y_store | 0x10009bf6 | 28250b | present | s16i a8,a2,22 |
| ZJI_OFFSET_X_load | 0x10009bff | 283105 | present | l16ui a8,a3,10 takes low half of BE uint32 item |
| ZJI_OFFSET_X_store | 0x10009c02 | 28250c | present | s16i a8,a2,24 |
| ZJI_OFFSET_Y_load | 0x10009c08 | 283105 | present | l16ui a8,a3,10 takes low half of BE uint32 item |
| ZJI_OFFSET_Y_store | 0x10009c0b | 28250e | present | s16i a8,a2,28 |
| ZJI_RASTER_X_load | 0x10009c3b | 283105 | present | l16ui a8,a3,10 takes low half of BE uint32 item |
| ZJI_RASTER_X_store | 0x10009c3e | 28250f | present | s16i a8,a2,30 |
| ZJI_RASTER_Y_load | 0x10009c44 | 283105 | present | l16ui a8,a3,10 takes low half of BE uint32 item |
| ZJI_RASTER_Y_store | 0x10009c47 | 282510 | present | s16i a8,a2,32 |
| ZJI_VIDEO_BPP_load | 0x10009c20 | 283105 | present | l16ui a8,a3,10 takes low half of BE uint32 item |
| ZJI_VIDEO_BPP_store | 0x10009c23 | 282511 | present | s16i a8,a2,34 |
| ZJI_VIDEO_X_load | 0x10009c29 | 283105 | present | l16ui a8,a3,10 takes low half of BE uint32 item |
| ZJI_VIDEO_X_store | 0x10009c2c | 282512 | present | s16i a8,a2,36 |
| ZJI_VIDEO_Y_load | 0x10009c32 | 283105 | present | l16ui a8,a3,10 takes low half of BE uint32 item |
| ZJI_VIDEO_Y_store | 0x10009c35 | 282513 | present | s16i a8,a2,38 |
| ZJI_INTERLACE_load | 0x10009c4d | 283105 | present | l16ui a8,a3,10 takes low half of BE uint32 item |
| ZJI_INTERLACE_store | 0x10009c50 | 282515 | present | s16i a8,a2,42 |
| ZJI_RET_load | 0x10009c83 | 283105 | present | l16ui a8,a3,10 takes low half of BE uint32 item |
| ZJI_RET_store | 0x10009c86 | 282518 | present | s16i a8,a2,48 |
| ZJI_ECONOMODE_load | 0x10009c8c | 283105 | present | l16ui a8,a3,10 takes low half of BE uint32 item |
| ZJI_ECONOMODE_store | 0x10009c8f | 282519 | present | s16i a8,a2,50 |
| early_fields_zero_initialized | — | — | present | common init zeros low body; missing RET defaults zero |

## Limits

- Static source/dataflow proof, not proof of a live page.
- Page items use low 16 bits. Malformed reserved lengths and physical timing still require separate analysis.
