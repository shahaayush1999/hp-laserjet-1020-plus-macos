# HP 1020 Video Prepare Argument Fields

This generated report is offline only. It does not contact the printer.

## Result

- status: `pass`
- prepare argument identity: `0x94-byte video/page work object`
- field status counts: `{'sourced': 8, 'computed_default': 1, 'default_zero_for_current_path': 2}`

## Field Sources

| Field | Prepare use | Source status | Source |
|---|---|---|---|
| `+0x14` | timing/resolution branch input | `sourced` | Direct START_PAGE item builder 0x10009b4c writes ZJI_RESOLUTION_X to active work +0x14 |
| `+0x16` | timing/resolution branch input | `sourced` | Direct START_PAGE item builder 0x10009b4c writes ZJI_RESOLUTION_Y to active work +0x16 |
| `+0x18` | computed/adjusted vertical timing value | `computed_default` | Direct item OFFSET_X/default zero, then overwritten inside prepare |
| `+0x22` | mode/setup branch selector | `sourced` | Direct START_PAGE item builder 0x10009b4c writes ZJI_VIDEO_BPP to active work +0x22 |
| `+0x24` | offset/centering input | `sourced` | Direct START_PAGE item builder 0x10009b4c writes ZJI_VIDEO_X to active work +0x24 |
| `+0x26` | remaining-unit seed copied to video state +0xd0/+0xd4 | `sourced` | Direct START_PAGE item builder 0x10009b4c writes ZJI_VIDEO_Y to active work +0x26 |
| `+0x30` | copied to video state +0xe8 | `sourced` | Direct START_PAGE item builder 0x10009b4c writes ZJI_RET (absent => zero) to active work +0x30 |
| `+0x32` | copied to video state +0xec | `sourced` | Direct START_PAGE item builder 0x10009b4c writes ZJI_ECONOMODE to active work +0x32 |
| `+0x36` | normal setup branch gate | `default_zero_for_current_path` | Common init zero; special item 0x65 can set one, but is absent from current host fixtures |
| `+0x74` | descriptor-queue versus raw-linked-list mode flag | `default_zero_for_current_path` | set to zero by work create for descriptor-queue path |
| `+0x84/+0x88/+0x8c/+0x90` | host raster geometry and render descriptor controls | `sourced` | filled by JobMgr from runtime BIH block before engine/video handoff |

## Current Conclusion

- Video prepare reads direct START_PAGE item fields, default/computed fields, and JobMgr-filled raster geometry.
- The critical sourced render geometry is still strong: JobMgr fills +0x84/+0x88/+0x8c/+0x90 from the BIH/runtime block.
- The former sideband gap is resolved: the item builder operates directly on active work; no intermediate copy is needed.

## Checks

| Check | Status | Detail |
|---|---|---|
| `direct_builder_elf_verified` | `present` | direct allocation, call and item stores match stock ELF |
| `prepare_argument_is_work_object` | `present` | queue payload chain identifies the prepare argument as the active 0x94 work object |
| `all_field_evidence_present` | `present` | all modeled prepare-argument fields have current source/use evidence |
| `direct_sideband_fields_sourced` | `present` | active work +0x26/+0x30/+0x32 are written by the direct START_PAGE builder |
| `jobmgr_geometry_fields_sourced` | `present` | JobMgr-sourced geometry fields are separated from low sideband defaults |
