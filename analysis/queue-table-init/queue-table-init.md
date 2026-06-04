# HP 1020 Queue Table Initializer Search

- queue table base: `0x1002c918`
- scanned table window: `0x1002c918` through `0x1002ca40`

## Hits

| Function | Calls | Table references |
|---:|---|---|
| `0x10013620` `FUN_10013620` | `1001362b` calls `0x10013668` `hp1020_queue_send_indexed_candidate` |  |
| `0x10013658` `hp1020_queue_send_candidate` | `10013661` calls `0x10013668` `hp1020_queue_send_indexed_candidate` |  |
| `0x10013668` `hp1020_queue_send_indexed_candidate` |  | `1001366b` `l32r` `l32r a8,0x100066f0` -> ref `0x100066f0`<br>`10013673` `l32i.n` `l32i.n a10,a2,0x0` -> ref `0x1002c918` |
| `0x10017f18` `threadx_queue_create_candidate` | `10017f89` calls `0x100199a4` `threadx_queue_create_core_candidate` |  |

## Interpretation

- A direct constant reference to `0x1002c918` is expected in `hp1020_queue_send_indexed_candidate` because that function indexes the queue table for sends.
- If no other direct hit appears, the table is likely populated through a pointer copied from descriptor data or through a boot/runtime descriptor loop that does not embed `0x1002c918` as an immediate in each write.
- The next fallback is to map descriptor initialization routines that call `threadx_queue_create_candidate` and then assign queue objects into the table indirectly.
