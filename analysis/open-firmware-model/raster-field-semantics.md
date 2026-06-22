# HP 1020 Raster Field Semantics

This is a generated offline model. It does not contact the printer.

## Result

- status: `pass`
- scope: host ZjStream/JBIG fields through firmware raster objects and into the video hardware boundary

## Simple Readout

The host-side print file already contains the page geometry and compressed raster bytes. The stock firmware mostly packages those values into work-object and raster-node fields, then the video path consumes those fields at the hardware boundary.

For a narrow open replacement, these are the fields that matter before the dangerous engine/video timing work starts.

## Source Reports

- `analysis/open-firmware-model/print-path-model.json`
- `analysis/open-firmware-model/variants/*/print-path-model.json`
- `analysis/video-raster-consumer-report.md`
- `analysis/hardware-boundary/video-register-projection.json`
- `analysis/hardware-boundary/video-transfer-ring.json`
- `analysis/hardware-boundary/video-refill-topology.json`

## Field Semantics

| Firmware field | Host source | Stock consumer | Replacement meaning | Confidence |
|---|---|---|---|---|
| `work +0x84` | JBIG BIH XD via runtime block 0x10023e28 +0x04 | 0x10015214 video render writes 0xb2000008 and contributes to stride/window setup | horizontal raster/transfer geometry; must match host-generated compressed stream | `high` |
| `work +0x88` | JBIG BIH YD via runtime block 0x10023e28 +0x08 | 0x10015214 video render writes 0xb200000c | vertical raster/page geometry | `high` |
| `work +0x8c` | JBIG BIH L0 via runtime block 0x10023e28 +0x0c | 0x10015214 video render writes 0xb2000024 and seeds band-height logic | JBIG stripe/band unit height used by the video transfer path | `high` |
| `work +0x90` | JBIG BIH options byte via runtime block 0x10023e28 +0x13 | 0x10015214 video render derives 0xb2000000 control bits from it | mode/options bits for compressed raster transfer | `medium-high` |
| `work +0x50` | JobMgr list of ZJT_JBIG_BID raster nodes | video render stores it at video state +0x9c; refill paths walk or derive from this raster stream | ordered compressed raster-band list for the page | `high` |
| `payload +0x48` | ZJT_JBIG_BID compressed payload byte count | video render/refill uses it as transfer-length evidence | compressed-band byte length; bounds DMA/raw-band transfer | `high` |
| `payload +0x4c` | copied marker/ref flag candidate from parser payload +0x2c | raw-band path turns nonzero into a hardware flag bit | per-band flag; exact semantics still need targeted evidence | `medium` |
| `payload +0x4e` | initialized from active work +0x0c | cleanup/lifetime path decrements or forces this retain counter | raster node lifetime/reference count | `medium-high` |
| `payload +0x50` | initialized to zero for parser-owned BID data | cleanup frees payload +0x54 unless this equals 2 | source/ownership mode, not a print geometry field | `medium-high` |
| `payload +0x54` | pointer to ZJT_JBIG_BID compressed payload bytes | video render/raw-band path writes or passes this pointer toward hardware transfer | compressed raster buffer pointer | `high` |

## Variant Matrix

| Case | Paper | Res | Video X/Y | Raster X/Y | BIH XD/YD/L0/options | Work +0x84/+0x88/+0x8c/+0x90 | Payload +0x48 | Payload +0x4e | Payload +0x50 | BID bytes |
|---|---:|---|---|---|---|---|---:|---:|---:|---:|
| `base` | `9` | `600x600` | `4768/6824` | `9536/6824` | `9600/6824/128/0x5c` | `9600/6824/128/0x5c` | `6364` | `1` | `0` | `6364` |
| `a4_2400x600` | `9` | `600x600` | `4768/6824` | `19072/6824` | `19072/6824/128/0x5c` | `19072/6824/128/0x5c` | `9080` | `1` | `0` | `9080` |
| `a4_600x600` | `9` | `600x600` | `4768/6824` | `4768/6824` | `4864/6824/128/0x5c` | `4864/6824/128/0x5c` | `4448` | `1` | `0` | `4448` |
| `a4_cardstock_media` | `9` | `600x600` | `4768/6824` | `9536/6824` | `9600/6824/128/0x5c` | `9600/6824/128/0x5c` | `6364` | `1` | `0` | `6364` |
| `a4_default` | `9` | `600x600` | `4768/6824` | `9536/6824` | `9600/6824/128/0x5c` | `9600/6824/128/0x5c` | `6364` | `1` | `0` | `6364` |
| `a4_draft` | `9` | `600x600` | `4768/6824` | `9536/6824` | `9600/6824/128/0x5c` | `9600/6824/128/0x5c` | `6364` | `1` | `0` | `6364` |
| `a4_logical_clip` | `9` | `600x600` | `4768/6824` | `9536/6824` | `9600/6824/128/0x5c` | `9600/6824/128/0x5c` | `6364` | `1` | `0` | `6364` |
| `a4_manual_feed` | `9` | `600x600` | `4768/6824` | `9536/6824` | `9600/6824/128/0x5c` | `9600/6824/128/0x5c` | `6364` | `1` | `0` | `6364` |
| `a4_two_copies` | `9` | `600x600` | `4768/6824` | `9536/6824` | `9600/6824/128/0x5c` | `9600/6824/128/0x5c` | `6364` | `2` | `0` | `6364` |
| `legal_default` | `5` | `600x600` | `4908/8208` | `9816/8208` | `9856/8208/128/0x5c` | `9856/8208/128/0x5c` | `6388` | `1` | `0` | `6388` |
| `letter_default` | `1` | `600x600` | `4908/6408` | `9816/6408` | `9856/6408/128/0x5c` | `9856/6408/128/0x5c` | `6376` | `1` | `0` | `6376` |

## Checks

| Check | Status | Detail |
|---|---|---|
| `variant_models_present` | `present` | 11 print-path model(s) loaded |
| `bih_runtime_to_work_fields` | `present` | BIH runtime block +0x04/+0x08/+0x0c/+0x13 still maps to work +0x84/+0x88/+0x8c/+0x90 |
| `bih_decoded_to_runtime_fields` | `present` | decoded JBIG BIH XD/YD/L0/options still matches the runtime block fields |
| `bid_payload_size_to_raster_fields` | `present` | BID compressed byte count is present both at payload +0x48 and payload +0x54 byte_count |
| `host_variants_move_geometry` | `present` | paper/resolution variants move the BIH-derived hardware geometry fields |
| `compressed_bytes_vary_by_host_case` | `present` | BID compressed payload size varies across generated host cases |
