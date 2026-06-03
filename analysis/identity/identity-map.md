# HP 1020 Identity Data Map

This maps product/manufacturer/PJL identity strings and pointer tables around them.

## Strings

### `10003734` `20050309`

Direct code/data references:
- `10006038`

Pointer-table references:
- `10006038`

### `10003b18` `HPBOISEID`

Direct code/data references:
- none found

Pointer-table references:
- `10003b10`

### `10004728` `@PJL ECHO `

Direct code/data references:
- `1000ce60`
- `1000ce74`
- `1000ce7c`
- `10004668`

Pointer-table references:
- `10004668`

### `10004cd3` `\nxxMFG:%s;MDL:%s;CMD:%s;CLS:%s;DES:%s;FWVER:%s;`

Direct code/data references:
- none found

Pointer-table references:
- none found

### `10004d04` `20050309`

Direct code/data references:
- `100064f8`

Pointer-table references:
- `100064f8`

### `10004d28` `20050309`

Direct code/data references:
- `10006548`

Pointer-table references:
- `10006548`

### `1001bf70` `Hewlett-Packard`

Direct code/data references:
- `100034a4`
- `100064e0`

Pointer-table references:
- `100034a4`
- `10004c74`
- `100064e0`

### `1001bf8c` `HP LaserJet 1020`

Direct code/data references:
- `100034a8`
- `100064e4`

Pointer-table references:
- `100034a8`
- `10004c7c`
- `100064e4`

### `1001bfb0` `HP LaserJet 1020`

Direct code/data references:
- `100064f0`

Pointer-table references:
- `10004c84`
- `100064f0`
- `1001d0e8`

## Related Functions

- `1000b3f8` `hp1020_pjl_ustatus_result_builder`
- `1000bd04` `hp1020_pjl_info_capabilities_builder`
- `1000cdb0` `hp1020_pjl_echo_matcher`

## Interpretation

- ASCII identity strings live in `.data`, not USB UTF-16 descriptor form.
- Static USB descriptors separately contain string indexes; the actual string response path likely builds runtime strings from these ASCII values or related buffers.
- PJL/IEEE1284 identity construction is centered around the `xxMFG:%s;MDL:%s;CMD:%s;CLS:%s;DES:%s;FWVER:%s;` format string and the status/capability builder functions.
