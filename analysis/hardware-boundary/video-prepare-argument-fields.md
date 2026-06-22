# HP 1020 Video Prepare Argument Fields

This generated report is offline only. It does not contact the printer.

## Result

- status: `pass`
- prepare argument identity: `0x94-byte video/page work object`
- sourced/default/unsourced counts: `{'sourced': 4, 'computed_default': 1, 'default_or_unsourced': 1, 'unsourced_active_work': 3, 'default_zero_for_current_path': 2}`

## Field Sources

| Field | Prepare use | Source status | Source |
|---|---|---|---|
| `+0x14` | timing/resolution branch input | `sourced` | copied by 0x100104c8 from page-param +0x1a |
| `+0x16` | timing/resolution branch input | `sourced` | copied by 0x100104c8 from page-param +0x1e |
| `+0x18` | computed/adjusted vertical timing value | `computed_default` | cleared by common init, then written inside prepare |
| `+0x22` | mode/setup branch selector | `sourced` | copied by 0x100104c8 from page-param +0x12 |
| `+0x24` | offset/centering input | `default_or_unsourced` | cleared by common init; no visible work-object writer in current static corpus |
| `+0x26` | remaining-unit seed copied to video state +0xd0/+0xd4 | `unsourced_active_work` | page-param +0x26 is built upstream, but not copied into active 0x94 work object by visible code |
| `+0x30` | copied to video state +0xe8 | `unsourced_active_work` | page-param +0x30 is built upstream, but not copied into active 0x94 work object by visible code |
| `+0x32` | copied to video state +0xec | `unsourced_active_work` | page-param +0x32 is built upstream, but not copied into active 0x94 work object by visible code |
| `+0x36` | normal setup branch gate | `default_zero_for_current_path` | cleared by common init for active work; page-param +0x36 case exists but is not visibly copied |
| `+0x74` | descriptor-queue versus raw-linked-list mode flag | `default_zero_for_current_path` | set to zero by work create for descriptor-queue path |
| `+0x84/+0x88/+0x8c/+0x90` | host raster geometry and render descriptor controls | `sourced` | filled by JobMgr from runtime BIH block before engine/video handoff |

## Current Conclusion

- Video prepare reads a mix of sourced fields, default/computed fields, and currently unsourced active-work sideband fields.
- The critical sourced render geometry is still strong: JobMgr fills +0x84/+0x88/+0x8c/+0x90 from the BIH/runtime block.
- The weak fields are active work +0x26/+0x30/+0x32: page-param values exist upstream, but current visible code does not copy them into the work object passed to prepare.

## Checks

| Check | Status | Detail |
|---|---|---|
| `prepare_argument_is_work_object` | `present` | queue payload chain identifies the prepare argument as the active 0x94 work object |
| `all_field_evidence_present` | `present` | all modeled prepare-argument fields have current source/use evidence |
| `unsourced_sideband_fields_preserved` | `present` | active work +0x26/+0x30/+0x32 remain unsourced in current visible code |
| `jobmgr_geometry_fields_sourced` | `present` | JobMgr-sourced geometry fields are separated from low sideband defaults |
