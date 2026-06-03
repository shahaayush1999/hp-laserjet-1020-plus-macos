# HP 1020 Firmware Upload Wrapper

This maps the difference between the raw firmware image and the `.dl` file sent to the printer.

## Files

- Raw date-prefixed image: `assets/firmware-source/sihp1020.img`
- Upload file: `assets/runtime/sihp1020.dl`
- Extracted ELF payload: `analysis/sihp1020.elf`

Sizes:

- `sihp1020.dl`: `128431` bytes
- `sihp1020.img`: `128380` bytes
- `sihp1020.elf`: `128372` bytes

## Structure

`sihp1020.dl` is:

```text
PJL UEL + @PJL ENTER LANGUAGE=ACL
ACL binary header
date-prefixed firmware image
PJL UEL trailer
```

Exact layout:

| Offset | Size | Meaning |
|---:|---:|---|
| `0x00000000` | `34` | `ESC %-12345X@PJL ENTER LANGUAGE=ACL\r\n` |
| `0x00000022` | `8` | ACL binary header: `00 ac c0 de 00 01 f5 74` |
| `0x0000002a` | `128380` | `sihp1020.img` |
| EOF - `9` | `9` | trailing `ESC %-12345X` |

The raw `sihp1020.img` is embedded byte-for-byte at offset `42` / `0x2a` inside `sihp1020.dl`.

## ACL Header

The 8-byte ACL header is:

```text
00 ac c0 de 00 01 f5 74
```

Interpretation:

- `00 ac c0 de`: ACL magic/header marker
- `00 01 f5 74`: big-endian length `128372`

`128372` equals the ELF payload size after skipping the 8-byte date prefix in `sihp1020.img`.

So the upload wrapper length field appears to describe the ELF payload length, while the transmitted image includes the 8-byte ASCII date prefix:

```text
20050309 + ELF
```

## First Bytes

`sihp1020.dl` begins:

```text
1b 25 2d 31 32 33 34 35 58 40 50 4a 4c 20 45 4e
54 45 52 20 4c 41 4e 47 55 41 47 45 3d 41 43 4c
0d 0a 00 ac c0 de 00 01 f5 74 32 30 30 35 30 33
30 39 7f 45 4c 46
```

That decodes as:

```text
ESC %-12345X@PJL ENTER LANGUAGE=ACL\r\n
00 ac c0 de
00 01 f5 74
20050309
0x7f ELF
```

## Prototype Packaging Implication

For a minimal replacement firmware upload file, the packaging shape is likely:

```text
ESC %-12345X@PJL ENTER LANGUAGE=ACL\r\n
00 ac c0 de
uint32_be(length_of_elf_payload)
8-byte ASCII build/date prefix
ELF payload
ESC %-12345X
```

Open questions before trying a prototype upload:

- whether the date prefix can be arbitrary ASCII
- whether the printer validates only the ELF length or also the full image length
- whether the ELF entry/load addresses must match the HP firmware exactly
- whether the boot ROM accepts any valid Xtensa ELF or expects HP-specific sections/interface tables

This is enough to build a packaging tool later without rediscovering the wrapper format.
