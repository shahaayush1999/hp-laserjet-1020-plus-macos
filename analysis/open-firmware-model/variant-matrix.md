# HP 1020 ZjStream Model Variant Matrix

This matrix generates several host-side ZjStream files, runs the offline print-path model on each one, and compares the fields that move.

No printer is contacted. The `.zjs` files are generated locally from `analysis/samples/minimal-page.ps` through `foo2zjs-wrapper`.

## Cases

| Case | Wrapper args | File bytes | Paper | Copies | Res | Video X/Y | Raster X/Y | BIH/work +0x84/+0x88/+0x8c/+0x90 | BID bytes |
|---|---|---:|---:|---:|---|---|---|---|---:|
| `a4_default` | `-p9` | `6987` | `9` | `1` | `600x600` | `4768`/`6824` | `9536`/`6824` | `9600`/`6824`/`128`/`0x5c` | `6364` |
| `letter_default` | `-p1` | `6999` | `1` | `1` | `600x600` | `4908`/`6408` | `9816`/`6408` | `9856`/`6408`/`128`/`0x5c` | `6376` |
| `legal_default` | `-p5` | `7011` | `5` | `1` | `600x600` | `4908`/`8208` | `9816`/`8208` | `9856`/`8208`/`128`/`0x5c` | `6388` |
| `a4_600x600` | `-p9 -r600x600` | `5071` | `9` | `1` | `600x600` | `4768`/`6824` | `4768`/`6824` | `4864`/`6824`/`128`/`0x5c` | `4448` |
| `a4_2400x600` | `-p9 -r2400x600` | `9703` | `9` | `1` | `600x600` | `4768`/`6824` | `19072`/`6824` | `19072`/`6824`/`128`/`0x5c` | `9080` |
| `a4_two_copies` | `-p9 -n2` | `6987` | `9` | `2` | `600x600` | `4768`/`6824` | `9536`/`6824` | `9600`/`6824`/`128`/`0x5c` | `6364` |
| `a4_draft` | `-p9 -t` | `6986` | `9` | `1` | `600x600` | `4768`/`6824` | `9536`/`6824` | `9600`/`6824`/`128`/`0x5c` | `6364` |
| `a4_manual_feed` | `-p9 -s4` | `6987` | `9` | `1` | `600x600` | `4768`/`6824` | `9536`/`6824` | `9600`/`6824`/`128`/`0x5c` | `6364` |
| `a4_cardstock_media` | `-p9 -m261` | `6987` | `9` | `1` | `600x600` | `4768`/`6824` | `9536`/`6824` | `9600`/`6824`/`128`/`0x5c` | `6364` |
| `a4_logical_clip` | `-p9 -L3` | `7011` | `9` | `1` | `600x600` | `4768`/`6824` | `9536`/`6824` | `9600`/`6824`/`128`/`0x5c` | `6364` |

## Non-Geometry Fields

| Case | Source | Media | Econo | Duplex | Offset X/Y |
|---|---:|---:|---:|---:|---|
| `a4_default` | `7` | `1` | `0` | `1` | ``/`` |
| `letter_default` | `7` | `1` | `0` | `1` | ``/`` |
| `legal_default` | `7` | `1` | `0` | `1` | ``/`` |
| `a4_600x600` | `7` | `1` | `0` | `1` | ``/`` |
| `a4_2400x600` | `7` | `1` | `0` | `1` | ``/`` |
| `a4_two_copies` | `7` | `1` | `0` | `1` | ``/`` |
| `a4_draft` | `7` | `1` | `1` | `1` | ``/`` |
| `a4_manual_feed` | `4` | `1` | `0` | `1` | ``/`` |
| `a4_cardstock_media` | `7` | `261` | `0` | `1` | ``/`` |
| `a4_logical_clip` | `7` | `1` | `0` | `1` | `192`/`96` |

## Readout

- Paper-size changes move the page item dimensions and the BIH-derived work fields.
- Resolution changes mostly move horizontal raster/video fields; vertical fields stay tied to paper height for this sample.
- Copy-count changes move `ZJI_DMCOPIES` and the modeled work `+0x0c` reference/count candidate without changing the BIH geometry.
- Source, media, draft/economode, and logical clip options change host-visible page items without moving the modeled video work geometry for this one-page sample.
- Every case still follows the same firmware message skeleton: `1`, `3`, `5`, `0x29`, `0x2a`, `0x2b`, `6`, `2` on JobMgr queue `3`.

## Generated Model Directories

- `a4_default`: `analysis/open-firmware-model/variants/a4_default`
- `letter_default`: `analysis/open-firmware-model/variants/letter_default`
- `legal_default`: `analysis/open-firmware-model/variants/legal_default`
- `a4_600x600`: `analysis/open-firmware-model/variants/a4_600x600`
- `a4_2400x600`: `analysis/open-firmware-model/variants/a4_2400x600`
- `a4_two_copies`: `analysis/open-firmware-model/variants/a4_two_copies`
- `a4_draft`: `analysis/open-firmware-model/variants/a4_draft`
- `a4_manual_feed`: `analysis/open-firmware-model/variants/a4_manual_feed`
- `a4_cardstock_media`: `analysis/open-firmware-model/variants/a4_cardstock_media`
- `a4_logical_clip`: `analysis/open-firmware-model/variants/a4_logical_clip`

## Practical Meaning

The offline model is not just hard-coded to one lucky A4 sample. It survives the basic wrapper variations we care about and shows which fields are host-controlled before the hardware boundary.

