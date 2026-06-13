# HP 1020 Video Register Projection

This report projects the offline print-path model onto the first unsafe video register writes.

It does not contact the printer. It answers: if the original firmware continued past our safe stop, which host-controlled values would reach video registers?

## Projection Table

| Case | Paper | Copies | Resolution | Raster X/Y | `0xb2000008` | `0xb200000c` | `0xb2000024` | `0xb2000000` control source |
|---|---:|---:|---|---|---:|---:|---:|---|
| `a4_2400x600` | `9` | `1` | `600x600` | `19072`/`6824` | `19072` | `6824` | `128` | `control derived from work +0x90=0x5c, then OR 0x400` |
| `a4_600x600` | `9` | `1` | `600x600` | `4768`/`6824` | `4864` | `6824` | `128` | `control derived from work +0x90=0x5c, then OR 0x400` |
| `a4_default` | `9` | `1` | `600x600` | `9536`/`6824` | `9600` | `6824` | `128` | `control derived from work +0x90=0x5c, then OR 0x400` |
| `a4_two_copies` | `9` | `2` | `600x600` | `9536`/`6824` | `9600` | `6824` | `128` | `control derived from work +0x90=0x5c, then OR 0x400` |
| `legal_default` | `5` | `1` | `600x600` | `9816`/`8208` | `9856` | `8208` | `128` | `control derived from work +0x90=0x5c, then OR 0x400` |
| `letter_default` | `1` | `1` | `600x600` | `9816`/`6408` | `9856` | `6408` | `128` | `control derived from work +0x90=0x5c, then OR 0x400` |

## Register Mapping

| Register | Source in modeled object | Firmware consumer | Meaning |
|---:|---|---:|---|
| `0xb2000008` | `work +0x84` | `0x10015214` | BIH-derived horizontal/video descriptor field |
| `0xb200000c` | `work +0x88` | `0x10015214` | BIH-derived vertical/video descriptor field |
| `0xb2000024` | `work +0x8c` | `0x10015214` | BIH `L0`/band-height-like field |
| `0xb2000000` | `work +0x90` | `0x10015214` | control word bits; firmware ORs `0x400` before writing |
| `0xb1000008` / `0xb1000108` | raster payload `+0x54` | `0x100140f8` | raw-band buffer pointer/window writes |
| `0xb100000c` / `0xb100010c` | raster payload `+0x20/+0x4c/+0x50` | `0x100140f8` | raw-band count and flag writes |

## Safety Meaning

The host print stream already controls values that flow directly into video transfer descriptors. That is fine inside HP's firmware because the surrounding state machines gate timing and hardware state. It is not safe to reproduce blindly in custom firmware.

For a first custom firmware experiment, the rule remains: do not reach these projected writes. Stay on boot/USB identity only.

