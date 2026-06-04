# PJL Status Code Reference Notes

This note links the firmware's generated PJL `CODE=` values to HP's PJL status-code vocabulary.

Sources checked:

- HP Support product manual listing for LaserJet 1012, which lists `HP PCL/PJL reference - Printer Job Language Technical Reference Manual`:
  `https://support.hp.com/us-en/product/hp-laserjet-1012-printer/377934/manuals`
- Text-accessible copy of HP's `Printer Job Language Technical Reference Manual`, Appendix D:
  `https://pic.hallikainen.org/techref/language/pcl/JTECHREF.PDF`

## Relevant HP PJL Rules

HP's PJL reference describes status readback responses as carrying numeric `CODE=` values and
localized `DISPLAY=` strings. The numeric code is the stable field to use for applications.

The same reference groups status codes by their first digits:

| Code group | Meaning |
|---:|---|
| `10xxx` | informational messages |
| `30xxx` | auto-continuable conditions |
| `35xxx` | possible operator intervention |
| `40xxx` | operator intervention required |
| `41xyy` | foreground paper loading |
| `50xxx` | hardware errors |

For `41xyy`, HP documents:

- `x` as a tray/source code
- `yy` as a media-size code

Examples from the reference include `41002` as foreground loading for tray/source `0` with media
code `02` (`Letter`) and `41303` as tray/source `3` with media code `03` (`Legal`).

## Firmware Link

The firmware's `0x1000a2a4` `hp1020_status_word_to_pjl_code_candidate` has two code paths:

| Path | Code base/value | Current meaning |
|---|---:|---|
| default | `0x2711` / `10001` | HP PJL informational ready/online code |
| mapped fault/status | `0xa028` / `41000` plus offset table | HP PJL foreground paper-loading code family |

The firmware offset table at `0x1001be40` produces:

| Input/status index | Offset | PJL code |
|---:|---:|---:|
| `0x0000` | `0x00` | `41000` |
| `0x0001` | `0x02` | `41002` |
| `0x0005` | `0x03` | `41003` |
| `0x0009` | `0x04` | `41004` |
| `0x0007` | `0x05` | `41005` |
| `0x0014` | `0x08` | `41008` |
| `0x0025` | `0x09` | `41009` |
| `0x001c` | `0x0a` | `41010` |
| `0x001b` | `0x0b` | `41011` |
| `0x000c` | `0x0c` | `41012` |
| `0x000d` | `0x0d` | `41013` |
| `0x0022` | `0x0e` | `41014` |
| `0x0100` | `0x0f` | `41015` |
| `0x0104` | `0x10` | `41016` |
| `0x0105` | `0x11` | `41017` |
| `0x000b` | `0x12` | `41018` |
| `0x0103` | `0x1f` | `41031` |
| `0x0101` | `0x20` | `41032` |
| `0x0102` | `0x21` | `41033` |
| `0x0106` | `0x22` | `41034` |

## Interpretation

This strongly suggests the mapped PJL `CODE=` path is primarily paper/media loading state.
It does not by itself identify fuser, toner, or jam hardware sensors.

The status command-table strings `PAPERLESS`, `FUSER`, `TONEREXP`, and `JAMRECOVERY` remain
PJL-visible variable names. The generated `410xx` output codes are a separate PJL status-code path,
with `410xx` anchored by HP's reference as foreground paper loading.
