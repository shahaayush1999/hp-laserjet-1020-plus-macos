# HP 1020 Engine Event To PJL CODE Correlation

This is an offline correlation model. It does not contact the printer.

## Key Result

- Engine queue `0x17` event words are not automatically final PJL `CODE=` values.
- The truncated decompilation omitted the ordinary numeric lookup in `0x1000a2a4`. Original bytes and interpreter/QEMU execution now recover it; `status-code-execution.json` contains the current evidence.
- The separate `410xx` path depends on datastore `0x1f`'s media key and word at+8: a nonzero word adds `(word+1)*100` with native32-bit arithmetic.
- The ordinary scan executes222 four-byte rows, continuing past111 code pairs into the media table and following strings/data. The media scan similarly executes40 rows although the next object follows20 pairs. Tested adjacent-data aliases are original behavior, not replacement requirements.
- The values below are direct converter results. StatusMgr priority/source filtering, subscription and physical calibration still determine whether/why a notification is emitted. Names such as `PAPERLESS` and `FUSER` remain configuration-table names, not evidence of a raw event's meaning.

## Converter Paths

- default code path: `10001`
- mapped paper/media code base: `41000`

| Direct converter classification | Count |
|---|---:|
| ordinary code table | `16` |
| zero result | `5` |

## Engine Event Words

| Event Word | Low16 | Source | Condition | Direct CODE | Path |
|---:|---:|---|---|---:|---|
| `0xfe001401` | `0x1401` | `hp1020_engine_status_io_candidate` | status command timeout/failure | `50021` | ordinary code table |
| `0xfe001401` | `0x1401` | `hp1020_engine_preflight_candidate` | preflight wait timeout/failure | `50021` | ordinary code table |
| `0xe6101100` | `0x1100` | `hp1020_engine_preflight_candidate` | preflight start/status transition | `10003` | ordinary code table |
| `0xe6100a01` | `0x0a01` | `hp1020_engine_status_poll_candidate` | ready/ok-looking status transition | `0` | zero result |
| `0xf6000300` | `0x0300` | `hp1020_engine_status_poll_candidate` | status register 0x20 path, bitmask branch | `0` | zero result |
| `0xf6000400` | `0x0400` | `hp1020_engine_status_poll_candidate` | status register 0x20 path, bit 0x400 branch | `0` | zero result |
| `0xe6100800` | `0x0800` | `hp1020_engine_status_poll_candidate` | engine status register 2 mask branch | `40021` | ordinary code table |
| `0x20001607` | `0x1607` | `hp1020_engine_status_poll_candidate` | engine status register 2 bits 0x424 branch | `10031` | ordinary code table |
| `0xe6101100` | `0x1100` | `hp1020_engine_status_poll_candidate` | engine status register 2 DAT_1000605c branch | `10003` | ordinary code table |
| `0xe6100e00` | `0x0e00` | `hp1020_engine_status_poll_candidate` | engine status register 2 DAT_10005dc8 branch | `40600` | ordinary code table |
| `0x80000000` | `0x0000` | `hp1020_engine_status_poll_candidate` | status fallback under uVar4/uVar5 condition | `0` | zero result |
| `0xe6000d03` | `0x0d03` | `hp1020_engine_status_poll_candidate` | engine substatus 0x16 bit 0x10 branch | `30201` | ordinary code table |
| `0xe6000d06` | `0x0d06` | `hp1020_engine_status_poll_candidate` | engine substatus 0x16 bit 0x08 branch | `0` | zero result |
| `0xe6000d04` | `0x0d04` | `hp1020_engine_status_poll_candidate` | engine substatus 0x16 bit 0x04 branch | `30096` | ordinary code table |
| `0xe6100b0a` | `0x0b0a` | `hp1020_engine_status_poll_candidate` | engine register 0x13 default subcase | `42000` | ordinary code table |
| `0xe6100b0b` | `0x0b0b` | `hp1020_engine_status_poll_candidate` | engine register 0x13 cases 0x10/0x14/0x18 | `42001` | ordinary code table |
| `0xe6e01201` | `0x1201` | `hp1020_video_reset_dispatch_candidate` | video reset case 3 | `30017` | ordinary code table |
| `0xe6e01202` | `0x1202` | `hp1020_video_reset_dispatch_candidate` | video reset case 4 | `30017` | ordinary code table |
| `0xeee01b02` | `0x1b02` | `hp1020_video_reset_dispatch_candidate` | video reset case 5 | `30022` | ordinary code table |
| `0xeee01b04` | `0x1b04` | `hp1020_video_reset_dispatch_candidate` | video reset case 6 | `30021` | ordinary code table |
| `0xeee01b01` | `0x1b01` | `hp1020_video_reset_dispatch_candidate` | video reset cases 2 and 7 | `30020` | ordinary code table |

## 410xx Table

This table is still useful, but it is selected through the converter's data-store lookup path, not by directly treating every engine event word as a table key.

| Input/status index | Offset | PJL CODE |
|---:|---:|---:|
| `0x0` | `0x0` | `41000` |
| `0x1` | `0x2` | `41002` |
| `0x5` | `0x3` | `41003` |
| `0x9` | `0x4` | `41004` |
| `0x7` | `0x5` | `41005` |
| `0x14` | `0x8` | `41008` |
| `0x25` | `0x9` | `41009` |
| `0x1c` | `0xa` | `41010` |
| `0x1b` | `0xb` | `41011` |
| `0xc` | `0xc` | `41012` |
| `0x103` | `0x1f` | `41031` |
| `0x22` | `0xe` | `41014` |
| `0xd` | `0xd` | `41013` |
| `0x104` | `0x10` | `41016` |
| `0x105` | `0x11` | `41017` |
| `0xb` | `0x12` | `41018` |
| `0x101` | `0x20` | `41032` |
| `0x102` | `0x21` | `41033` |
| `0x106` | `0x22` | `41034` |
| `0x100` | `0xf` | `41015` |

## Practical Meaning

Use the recovered ordinary mappings when connecting known engine observations to compatible status replies. Do not copy the adjacent-data aliases, turn a supplied numeric fixture into a sensed condition, or manufacture ready/job completion from input decoding. The current open command path provides ECHO only.

