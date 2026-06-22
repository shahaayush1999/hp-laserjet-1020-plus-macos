# HP 1020 Print Model Invariant Check

- cases checked: `11`
- checks: `209`
- fail hits: `0`

## Case Summary

| Case | Checks | Failures |
|---|---:|---:|
| `a4_2400x600` | `19` | `0` |
| `a4_600x600` | `19` | `0` |
| `a4_cardstock_media` | `19` | `0` |
| `a4_default` | `19` | `0` |
| `a4_draft` | `19` | `0` |
| `a4_logical_clip` | `19` | `0` |
| `a4_manual_feed` | `19` | `0` |
| `a4_two_copies` | `19` | `0` |
| `base` | `19` | `0` |
| `legal_default` | `19` | `0` |
| `letter_default` | `19` | `0` |

## Checks

| Severity | Case | Check | Detail |
|---|---|---|---|
| `watch` | `base` | `chunk_sequence` | parser must follow the daily print-path skeleton |
| `watch` | `base` | `jobmgr_message_sequence` | parser-to-JobMgr messages must preserve the modeled order |
| `watch` | `base` | `document_count` | single-page fixture should create one document |
| `watch` | `base` | `page_count` | single-page fixture should create one page |
| `watch` | `base` | `work_count` | single-page fixture should create one video work object |
| `watch` | `base` | `raster_count` | single-page fixture should create one raster node |
| `watch` | `base` | `work_copy_count` | work +0x0c tracks page copy count |
| `watch` | `base` | `work_plane_count` | work +0x22 tracks page NBIE/plane count |
| `watch` | `base` | `page_work_link` | page object points at the modeled work object |
| `watch` | `base` | `runtime_+0x04_to_work_+0x84` | BIH runtime +0x04 must seed work +0x84 |
| `watch` | `base` | `runtime_+0x08_to_work_+0x88` | BIH runtime +0x08 must seed work +0x88 |
| `watch` | `base` | `runtime_+0x0c_to_work_+0x8c` | BIH runtime +0x0c must seed work +0x8c |
| `watch` | `base` | `runtime_+0x13_to_work_+0x90` | BIH runtime +0x13 must seed work +0x90 |
| `watch` | `base` | `raster_owner` | raster node owner matches active work |
| `watch` | `base` | `raster_list_link` | work +0x50 contains the raster list node |
| `watch` | `base` | `raster_payload_size` | payload +0x48 matches compressed BID byte count |
| `watch` | `base` | `raster_retain_count` | raster payload +0x4e tracks work copy/reference count |
| `watch` | `base` | `hardware_boundary_functions` | safe-stop boundary must name the known unsafe video/engine consumers |
| `watch` | `base` | `hardware_boundary_rasters` | hardware boundary raster list matches work +0x50 |
| `watch` | `a4_2400x600` | `chunk_sequence` | parser must follow the daily print-path skeleton |
| `watch` | `a4_2400x600` | `jobmgr_message_sequence` | parser-to-JobMgr messages must preserve the modeled order |
| `watch` | `a4_2400x600` | `document_count` | single-page fixture should create one document |
| `watch` | `a4_2400x600` | `page_count` | single-page fixture should create one page |
| `watch` | `a4_2400x600` | `work_count` | single-page fixture should create one video work object |
| `watch` | `a4_2400x600` | `raster_count` | single-page fixture should create one raster node |
| `watch` | `a4_2400x600` | `work_copy_count` | work +0x0c tracks page copy count |
| `watch` | `a4_2400x600` | `work_plane_count` | work +0x22 tracks page NBIE/plane count |
| `watch` | `a4_2400x600` | `page_work_link` | page object points at the modeled work object |
| `watch` | `a4_2400x600` | `runtime_+0x04_to_work_+0x84` | BIH runtime +0x04 must seed work +0x84 |
| `watch` | `a4_2400x600` | `runtime_+0x08_to_work_+0x88` | BIH runtime +0x08 must seed work +0x88 |
| `watch` | `a4_2400x600` | `runtime_+0x0c_to_work_+0x8c` | BIH runtime +0x0c must seed work +0x8c |
| `watch` | `a4_2400x600` | `runtime_+0x13_to_work_+0x90` | BIH runtime +0x13 must seed work +0x90 |
| `watch` | `a4_2400x600` | `raster_owner` | raster node owner matches active work |
| `watch` | `a4_2400x600` | `raster_list_link` | work +0x50 contains the raster list node |
| `watch` | `a4_2400x600` | `raster_payload_size` | payload +0x48 matches compressed BID byte count |
| `watch` | `a4_2400x600` | `raster_retain_count` | raster payload +0x4e tracks work copy/reference count |
| `watch` | `a4_2400x600` | `hardware_boundary_functions` | safe-stop boundary must name the known unsafe video/engine consumers |
| `watch` | `a4_2400x600` | `hardware_boundary_rasters` | hardware boundary raster list matches work +0x50 |
| `watch` | `a4_600x600` | `chunk_sequence` | parser must follow the daily print-path skeleton |
| `watch` | `a4_600x600` | `jobmgr_message_sequence` | parser-to-JobMgr messages must preserve the modeled order |
| `watch` | `a4_600x600` | `document_count` | single-page fixture should create one document |
| `watch` | `a4_600x600` | `page_count` | single-page fixture should create one page |
| `watch` | `a4_600x600` | `work_count` | single-page fixture should create one video work object |
| `watch` | `a4_600x600` | `raster_count` | single-page fixture should create one raster node |
| `watch` | `a4_600x600` | `work_copy_count` | work +0x0c tracks page copy count |
| `watch` | `a4_600x600` | `work_plane_count` | work +0x22 tracks page NBIE/plane count |
| `watch` | `a4_600x600` | `page_work_link` | page object points at the modeled work object |
| `watch` | `a4_600x600` | `runtime_+0x04_to_work_+0x84` | BIH runtime +0x04 must seed work +0x84 |
| `watch` | `a4_600x600` | `runtime_+0x08_to_work_+0x88` | BIH runtime +0x08 must seed work +0x88 |
| `watch` | `a4_600x600` | `runtime_+0x0c_to_work_+0x8c` | BIH runtime +0x0c must seed work +0x8c |
| `watch` | `a4_600x600` | `runtime_+0x13_to_work_+0x90` | BIH runtime +0x13 must seed work +0x90 |
| `watch` | `a4_600x600` | `raster_owner` | raster node owner matches active work |
| `watch` | `a4_600x600` | `raster_list_link` | work +0x50 contains the raster list node |
| `watch` | `a4_600x600` | `raster_payload_size` | payload +0x48 matches compressed BID byte count |
| `watch` | `a4_600x600` | `raster_retain_count` | raster payload +0x4e tracks work copy/reference count |
| `watch` | `a4_600x600` | `hardware_boundary_functions` | safe-stop boundary must name the known unsafe video/engine consumers |
| `watch` | `a4_600x600` | `hardware_boundary_rasters` | hardware boundary raster list matches work +0x50 |
| `watch` | `a4_cardstock_media` | `chunk_sequence` | parser must follow the daily print-path skeleton |
| `watch` | `a4_cardstock_media` | `jobmgr_message_sequence` | parser-to-JobMgr messages must preserve the modeled order |
| `watch` | `a4_cardstock_media` | `document_count` | single-page fixture should create one document |
| `watch` | `a4_cardstock_media` | `page_count` | single-page fixture should create one page |
| `watch` | `a4_cardstock_media` | `work_count` | single-page fixture should create one video work object |
| `watch` | `a4_cardstock_media` | `raster_count` | single-page fixture should create one raster node |
| `watch` | `a4_cardstock_media` | `work_copy_count` | work +0x0c tracks page copy count |
| `watch` | `a4_cardstock_media` | `work_plane_count` | work +0x22 tracks page NBIE/plane count |
| `watch` | `a4_cardstock_media` | `page_work_link` | page object points at the modeled work object |
| `watch` | `a4_cardstock_media` | `runtime_+0x04_to_work_+0x84` | BIH runtime +0x04 must seed work +0x84 |
| `watch` | `a4_cardstock_media` | `runtime_+0x08_to_work_+0x88` | BIH runtime +0x08 must seed work +0x88 |
| `watch` | `a4_cardstock_media` | `runtime_+0x0c_to_work_+0x8c` | BIH runtime +0x0c must seed work +0x8c |
| `watch` | `a4_cardstock_media` | `runtime_+0x13_to_work_+0x90` | BIH runtime +0x13 must seed work +0x90 |
| `watch` | `a4_cardstock_media` | `raster_owner` | raster node owner matches active work |
| `watch` | `a4_cardstock_media` | `raster_list_link` | work +0x50 contains the raster list node |
| `watch` | `a4_cardstock_media` | `raster_payload_size` | payload +0x48 matches compressed BID byte count |
| `watch` | `a4_cardstock_media` | `raster_retain_count` | raster payload +0x4e tracks work copy/reference count |
| `watch` | `a4_cardstock_media` | `hardware_boundary_functions` | safe-stop boundary must name the known unsafe video/engine consumers |
| `watch` | `a4_cardstock_media` | `hardware_boundary_rasters` | hardware boundary raster list matches work +0x50 |
| `watch` | `a4_default` | `chunk_sequence` | parser must follow the daily print-path skeleton |
| `watch` | `a4_default` | `jobmgr_message_sequence` | parser-to-JobMgr messages must preserve the modeled order |
| `watch` | `a4_default` | `document_count` | single-page fixture should create one document |
| `watch` | `a4_default` | `page_count` | single-page fixture should create one page |
| `watch` | `a4_default` | `work_count` | single-page fixture should create one video work object |
| `watch` | `a4_default` | `raster_count` | single-page fixture should create one raster node |
| `watch` | `a4_default` | `work_copy_count` | work +0x0c tracks page copy count |
| `watch` | `a4_default` | `work_plane_count` | work +0x22 tracks page NBIE/plane count |
| `watch` | `a4_default` | `page_work_link` | page object points at the modeled work object |
| `watch` | `a4_default` | `runtime_+0x04_to_work_+0x84` | BIH runtime +0x04 must seed work +0x84 |
| `watch` | `a4_default` | `runtime_+0x08_to_work_+0x88` | BIH runtime +0x08 must seed work +0x88 |
| `watch` | `a4_default` | `runtime_+0x0c_to_work_+0x8c` | BIH runtime +0x0c must seed work +0x8c |
| `watch` | `a4_default` | `runtime_+0x13_to_work_+0x90` | BIH runtime +0x13 must seed work +0x90 |
| `watch` | `a4_default` | `raster_owner` | raster node owner matches active work |
| `watch` | `a4_default` | `raster_list_link` | work +0x50 contains the raster list node |
| `watch` | `a4_default` | `raster_payload_size` | payload +0x48 matches compressed BID byte count |
| `watch` | `a4_default` | `raster_retain_count` | raster payload +0x4e tracks work copy/reference count |
| `watch` | `a4_default` | `hardware_boundary_functions` | safe-stop boundary must name the known unsafe video/engine consumers |
| `watch` | `a4_default` | `hardware_boundary_rasters` | hardware boundary raster list matches work +0x50 |
| `watch` | `a4_draft` | `chunk_sequence` | parser must follow the daily print-path skeleton |
| `watch` | `a4_draft` | `jobmgr_message_sequence` | parser-to-JobMgr messages must preserve the modeled order |
| `watch` | `a4_draft` | `document_count` | single-page fixture should create one document |
| `watch` | `a4_draft` | `page_count` | single-page fixture should create one page |
| `watch` | `a4_draft` | `work_count` | single-page fixture should create one video work object |
| `watch` | `a4_draft` | `raster_count` | single-page fixture should create one raster node |
| `watch` | `a4_draft` | `work_copy_count` | work +0x0c tracks page copy count |
| `watch` | `a4_draft` | `work_plane_count` | work +0x22 tracks page NBIE/plane count |
| `watch` | `a4_draft` | `page_work_link` | page object points at the modeled work object |
| `watch` | `a4_draft` | `runtime_+0x04_to_work_+0x84` | BIH runtime +0x04 must seed work +0x84 |
| `watch` | `a4_draft` | `runtime_+0x08_to_work_+0x88` | BIH runtime +0x08 must seed work +0x88 |
| `watch` | `a4_draft` | `runtime_+0x0c_to_work_+0x8c` | BIH runtime +0x0c must seed work +0x8c |
| `watch` | `a4_draft` | `runtime_+0x13_to_work_+0x90` | BIH runtime +0x13 must seed work +0x90 |
| `watch` | `a4_draft` | `raster_owner` | raster node owner matches active work |
| `watch` | `a4_draft` | `raster_list_link` | work +0x50 contains the raster list node |
| `watch` | `a4_draft` | `raster_payload_size` | payload +0x48 matches compressed BID byte count |
| `watch` | `a4_draft` | `raster_retain_count` | raster payload +0x4e tracks work copy/reference count |
| `watch` | `a4_draft` | `hardware_boundary_functions` | safe-stop boundary must name the known unsafe video/engine consumers |
| `watch` | `a4_draft` | `hardware_boundary_rasters` | hardware boundary raster list matches work +0x50 |
| `watch` | `a4_logical_clip` | `chunk_sequence` | parser must follow the daily print-path skeleton |
| `watch` | `a4_logical_clip` | `jobmgr_message_sequence` | parser-to-JobMgr messages must preserve the modeled order |
| `watch` | `a4_logical_clip` | `document_count` | single-page fixture should create one document |
| `watch` | `a4_logical_clip` | `page_count` | single-page fixture should create one page |
| `watch` | `a4_logical_clip` | `work_count` | single-page fixture should create one video work object |
| `watch` | `a4_logical_clip` | `raster_count` | single-page fixture should create one raster node |
| `watch` | `a4_logical_clip` | `work_copy_count` | work +0x0c tracks page copy count |
| `watch` | `a4_logical_clip` | `work_plane_count` | work +0x22 tracks page NBIE/plane count |
| `watch` | `a4_logical_clip` | `page_work_link` | page object points at the modeled work object |
| `watch` | `a4_logical_clip` | `runtime_+0x04_to_work_+0x84` | BIH runtime +0x04 must seed work +0x84 |
| `watch` | `a4_logical_clip` | `runtime_+0x08_to_work_+0x88` | BIH runtime +0x08 must seed work +0x88 |
| `watch` | `a4_logical_clip` | `runtime_+0x0c_to_work_+0x8c` | BIH runtime +0x0c must seed work +0x8c |
| `watch` | `a4_logical_clip` | `runtime_+0x13_to_work_+0x90` | BIH runtime +0x13 must seed work +0x90 |
| `watch` | `a4_logical_clip` | `raster_owner` | raster node owner matches active work |
| `watch` | `a4_logical_clip` | `raster_list_link` | work +0x50 contains the raster list node |
| `watch` | `a4_logical_clip` | `raster_payload_size` | payload +0x48 matches compressed BID byte count |
| `watch` | `a4_logical_clip` | `raster_retain_count` | raster payload +0x4e tracks work copy/reference count |
| `watch` | `a4_logical_clip` | `hardware_boundary_functions` | safe-stop boundary must name the known unsafe video/engine consumers |
| `watch` | `a4_logical_clip` | `hardware_boundary_rasters` | hardware boundary raster list matches work +0x50 |
| `watch` | `a4_manual_feed` | `chunk_sequence` | parser must follow the daily print-path skeleton |
| `watch` | `a4_manual_feed` | `jobmgr_message_sequence` | parser-to-JobMgr messages must preserve the modeled order |
| `watch` | `a4_manual_feed` | `document_count` | single-page fixture should create one document |
| `watch` | `a4_manual_feed` | `page_count` | single-page fixture should create one page |
| `watch` | `a4_manual_feed` | `work_count` | single-page fixture should create one video work object |
| `watch` | `a4_manual_feed` | `raster_count` | single-page fixture should create one raster node |
| `watch` | `a4_manual_feed` | `work_copy_count` | work +0x0c tracks page copy count |
| `watch` | `a4_manual_feed` | `work_plane_count` | work +0x22 tracks page NBIE/plane count |
| `watch` | `a4_manual_feed` | `page_work_link` | page object points at the modeled work object |
| `watch` | `a4_manual_feed` | `runtime_+0x04_to_work_+0x84` | BIH runtime +0x04 must seed work +0x84 |
| `watch` | `a4_manual_feed` | `runtime_+0x08_to_work_+0x88` | BIH runtime +0x08 must seed work +0x88 |
| `watch` | `a4_manual_feed` | `runtime_+0x0c_to_work_+0x8c` | BIH runtime +0x0c must seed work +0x8c |
| `watch` | `a4_manual_feed` | `runtime_+0x13_to_work_+0x90` | BIH runtime +0x13 must seed work +0x90 |
| `watch` | `a4_manual_feed` | `raster_owner` | raster node owner matches active work |
| `watch` | `a4_manual_feed` | `raster_list_link` | work +0x50 contains the raster list node |
| `watch` | `a4_manual_feed` | `raster_payload_size` | payload +0x48 matches compressed BID byte count |
| `watch` | `a4_manual_feed` | `raster_retain_count` | raster payload +0x4e tracks work copy/reference count |
| `watch` | `a4_manual_feed` | `hardware_boundary_functions` | safe-stop boundary must name the known unsafe video/engine consumers |
| `watch` | `a4_manual_feed` | `hardware_boundary_rasters` | hardware boundary raster list matches work +0x50 |
| `watch` | `a4_two_copies` | `chunk_sequence` | parser must follow the daily print-path skeleton |
| `watch` | `a4_two_copies` | `jobmgr_message_sequence` | parser-to-JobMgr messages must preserve the modeled order |
| `watch` | `a4_two_copies` | `document_count` | single-page fixture should create one document |
| `watch` | `a4_two_copies` | `page_count` | single-page fixture should create one page |
| `watch` | `a4_two_copies` | `work_count` | single-page fixture should create one video work object |
| `watch` | `a4_two_copies` | `raster_count` | single-page fixture should create one raster node |
| `watch` | `a4_two_copies` | `work_copy_count` | work +0x0c tracks page copy count |
| `watch` | `a4_two_copies` | `work_plane_count` | work +0x22 tracks page NBIE/plane count |
| `watch` | `a4_two_copies` | `page_work_link` | page object points at the modeled work object |
| `watch` | `a4_two_copies` | `runtime_+0x04_to_work_+0x84` | BIH runtime +0x04 must seed work +0x84 |
| `watch` | `a4_two_copies` | `runtime_+0x08_to_work_+0x88` | BIH runtime +0x08 must seed work +0x88 |
| `watch` | `a4_two_copies` | `runtime_+0x0c_to_work_+0x8c` | BIH runtime +0x0c must seed work +0x8c |
| `watch` | `a4_two_copies` | `runtime_+0x13_to_work_+0x90` | BIH runtime +0x13 must seed work +0x90 |
| `watch` | `a4_two_copies` | `raster_owner` | raster node owner matches active work |
| `watch` | `a4_two_copies` | `raster_list_link` | work +0x50 contains the raster list node |
| `watch` | `a4_two_copies` | `raster_payload_size` | payload +0x48 matches compressed BID byte count |
| `watch` | `a4_two_copies` | `raster_retain_count` | raster payload +0x4e tracks work copy/reference count |
| `watch` | `a4_two_copies` | `hardware_boundary_functions` | safe-stop boundary must name the known unsafe video/engine consumers |
| `watch` | `a4_two_copies` | `hardware_boundary_rasters` | hardware boundary raster list matches work +0x50 |
| `watch` | `legal_default` | `chunk_sequence` | parser must follow the daily print-path skeleton |
| `watch` | `legal_default` | `jobmgr_message_sequence` | parser-to-JobMgr messages must preserve the modeled order |
| `watch` | `legal_default` | `document_count` | single-page fixture should create one document |
| `watch` | `legal_default` | `page_count` | single-page fixture should create one page |
| `watch` | `legal_default` | `work_count` | single-page fixture should create one video work object |
| `watch` | `legal_default` | `raster_count` | single-page fixture should create one raster node |
| `watch` | `legal_default` | `work_copy_count` | work +0x0c tracks page copy count |
| `watch` | `legal_default` | `work_plane_count` | work +0x22 tracks page NBIE/plane count |
| `watch` | `legal_default` | `page_work_link` | page object points at the modeled work object |
| `watch` | `legal_default` | `runtime_+0x04_to_work_+0x84` | BIH runtime +0x04 must seed work +0x84 |
| `watch` | `legal_default` | `runtime_+0x08_to_work_+0x88` | BIH runtime +0x08 must seed work +0x88 |
| `watch` | `legal_default` | `runtime_+0x0c_to_work_+0x8c` | BIH runtime +0x0c must seed work +0x8c |
| `watch` | `legal_default` | `runtime_+0x13_to_work_+0x90` | BIH runtime +0x13 must seed work +0x90 |
| `watch` | `legal_default` | `raster_owner` | raster node owner matches active work |
| `watch` | `legal_default` | `raster_list_link` | work +0x50 contains the raster list node |
| `watch` | `legal_default` | `raster_payload_size` | payload +0x48 matches compressed BID byte count |
| `watch` | `legal_default` | `raster_retain_count` | raster payload +0x4e tracks work copy/reference count |
| `watch` | `legal_default` | `hardware_boundary_functions` | safe-stop boundary must name the known unsafe video/engine consumers |
| `watch` | `legal_default` | `hardware_boundary_rasters` | hardware boundary raster list matches work +0x50 |
| `watch` | `letter_default` | `chunk_sequence` | parser must follow the daily print-path skeleton |
| `watch` | `letter_default` | `jobmgr_message_sequence` | parser-to-JobMgr messages must preserve the modeled order |
| `watch` | `letter_default` | `document_count` | single-page fixture should create one document |
| `watch` | `letter_default` | `page_count` | single-page fixture should create one page |
| `watch` | `letter_default` | `work_count` | single-page fixture should create one video work object |
| `watch` | `letter_default` | `raster_count` | single-page fixture should create one raster node |
| `watch` | `letter_default` | `work_copy_count` | work +0x0c tracks page copy count |
| `watch` | `letter_default` | `work_plane_count` | work +0x22 tracks page NBIE/plane count |
| `watch` | `letter_default` | `page_work_link` | page object points at the modeled work object |
| `watch` | `letter_default` | `runtime_+0x04_to_work_+0x84` | BIH runtime +0x04 must seed work +0x84 |
| `watch` | `letter_default` | `runtime_+0x08_to_work_+0x88` | BIH runtime +0x08 must seed work +0x88 |
| `watch` | `letter_default` | `runtime_+0x0c_to_work_+0x8c` | BIH runtime +0x0c must seed work +0x8c |
| `watch` | `letter_default` | `runtime_+0x13_to_work_+0x90` | BIH runtime +0x13 must seed work +0x90 |
| `watch` | `letter_default` | `raster_owner` | raster node owner matches active work |
| `watch` | `letter_default` | `raster_list_link` | work +0x50 contains the raster list node |
| `watch` | `letter_default` | `raster_payload_size` | payload +0x48 matches compressed BID byte count |
| `watch` | `letter_default` | `raster_retain_count` | raster payload +0x4e tracks work copy/reference count |
| `watch` | `letter_default` | `hardware_boundary_functions` | safe-stop boundary must name the known unsafe video/engine consumers |
| `watch` | `letter_default` | `hardware_boundary_rasters` | hardware boundary raster list matches work +0x50 |
