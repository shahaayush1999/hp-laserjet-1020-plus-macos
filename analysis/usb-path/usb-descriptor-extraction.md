# HP 1020 USB Descriptor Extraction

This report is generated from the firmware ELF bytes. It does not contact the printer.

## Device Descriptors

| VAddr | Product | USB | EP0 | Manufacturer | Product String | Serial | Configs | Raw |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `0x1001bbe0` | `0x2b17` | `0x0200` | `64` | `1` | `2` | `3` | `1` | `12 01 00 02 00 00 00 40 f0 03 17 2b 00 01 01 02 03 01` |
| `0x1001bc00` | `0x2b17` | `0x0200` | `64` | `1` | `2` | `3` | `1` | `12 01 00 02 00 00 00 40 f0 03 17 2b 00 01 01 02 03 01` |

## Configuration Descriptors

| VAddr | Total Length | Interfaces | Endpoints | Raw Prefix |
| ---: | ---: | ---: | ---: | --- |
| `0x100034b0` | `32` | `1` | `2` | `09 02 20 00 01 01 00 c0 31 09 04 00 00 02 07 01 02 00 07 05 01 02 00 02 00 07 05 81 02 00 02 00` |
  - interface `0` class `0x07` subclass `0x01` protocol `0x02`
  - endpoint `0x01` attr `0x02` max packet `512` interval `0`
  - endpoint `0x81` attr `0x02` max packet `512` interval `0`
| `0x100034d0` | `32` | `1` | `2` | `09 02 20 00 01 01 00 c0 31 09 04 00 00 02 07 01 02 00 07 05 01 02 40 00 00 07 05 81 02 40 00 00` |
  - interface `0` class `0x07` subclass `0x01` protocol `0x02`
  - endpoint `0x01` attr `0x02` max packet `64` interval `0`
  - endpoint `0x81` attr `0x02` max packet `64` interval `0`

## Known Strings

| VAddr | Text |
| ---: | --- |
| `0x10003490` | `$$DEVICE_ID_STRING$$` |
| `0x1001bf70` | `Hewlett-Packard` |
| `0x1001bf8c` | `HP LaserJet 1020` |
| `0x1001bfb0` | `HP LaserJet 1020` |
| `0x10003b18` | `HPBOISEID` |
| `0x10004728` | `@PJL ECHO ` |
| `0x10004cd6` | `MFG:%s;MDL:%s;CMD:%s;CLS:%s;DES:%s;FWVER:%s;` |
| `0x10004cdd` | `MDL:%s;CMD:%s;CLS:%s;DES:%s;FWVER:%s;` |
| `0x10004cf9` | `FWVER:%s;` |

## Pointer Runs To Known Strings

| VAddr | Words | Values |
| ---: | ---: | --- |
| `0x100064e0` | `2` | `0x1001bf70, 0x1001bf8c` |
| `0x100034a4` | `2` | `0x1001bf70, 0x1001bf8c` |
| `0x1001d0e8` | `1` | `0x1001bfb0` |
| `0x100064f0` | `1` | `0x1001bfb0` |
| `0x10004c84` | `1` | `0x1001bfb0` |
| `0x10004c7c` | `1` | `0x1001bf8c` |
| `0x10004c74` | `1` | `0x1001bf70` |
| `0x10004668` | `1` | `0x10004728` |
| `0x10003b10` | `1` | `0x10003b18` |

## Interpretation

- Two HP device descriptor candidates are present in `.data`, both with vendor ID `0x03f0`.
- The descriptor product ID bytes match the host-observed `0x2b17` identity.
- A full USB printer-style configuration descriptor is present with interface class `0x07`.
- Static string evidence confirms the stock firmware has manufacturer/product strings and an IEEE-1284 template.
- This strengthens the future USB-marker target, but it does not remove the need to implement/control endpoint-0 behavior in open firmware.

