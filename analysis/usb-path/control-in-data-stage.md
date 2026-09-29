# HP 1020 Control-IN Data Stage Model

This is an offline model of the stock USB endpoint-0 data sender. It does not contact the printer.

## Key Result

- This static model covers descriptor construction and submission intent, not controller acceptance or successful transfers.
- The stock path uses a staging buffer, a 0x10-byte descriptor ring, a per-descriptor `0x08000000` flag, `0xb3000014` descriptor submission, and `0xb3000000 |= 0x108` transfer kick.
- Active submissions preserve the supplied descriptor pointer. Separate initialization adds `0x80000000` modulo 32 bits; the former pointer-OR model was incorrect.
- Cache/DMA behavior, real completion and settlement remain unproved.

## Resolved Constants

| Name | Value |
|---|---:|
| `transfer_state_base` | `0x100212d4` |
| `completion_event_flags` | `0x10021318` |
| `descriptor_flag` | `0x08000000` |
| `descriptor_base_ptr_cell` | `0x1001bc58` |
| `staging_buffer_ptr_cell` | `0x1001bc64` |
| `descriptor_base` | `0x900226f0` |
| `staging_buffer` | `0x90022bd0` |
| `usb_main_control` | `0xb3000000` |
| `chunk_size_register` | `0xb300000c` |
| `descriptor_submit_register` | `0xb3000014` |
| `initial_descriptor_pointer_addend` | `0x80000000` |
| `descriptor_submit_value` | `0x900226f0` |
| `initial_descriptor_submit_value` | `0x100226f0` |

## Pointer dataflow correction

Each contiguous byte slice is checked against the stock ELF. This is static evidence, not new stock execution.

- `0x10008d02` (`88c019f467dcf00c02009890`): active zero-length pointer unchanged.
- `0x10008f11` (`19f3e38870c7ef0c02009890`): active nonzero pointer unchanged.
- `0x100092aa` (`88b019f2e21bf2fca98819f2fe0c020098b0`): initial pointer plus literal modulo 2^32.

The initialized descriptor has HOST_BUSY status `0xc0000000`. With the file-backed pointer, initialization wraps `0x900226f0` to `0x100226f0`; active submission stays `0x900226f0`. Neither operation establishes a physical alias or address translation rule.

| Supplied pointer | Active submission | Initialization ADD |
|---|---|---|
| `0x100226f0` | `0x100226f0` | `0x900226f0` |
| `0x900226f0` | `0x900226f0` | `0x100226f0` |

## Algorithm

- set 0xb3000000 bit 0x2 before staging the control-IN response
- copy response bytes into the staging buffer at 0x90022bd0; cache visibility is not established here
- build one to five 0x10-byte transfer descriptors at 0x900226f0
- descriptor word +0x00 is byte_count OR 0x08000000 on the final descriptor of each hardware kick
- descriptor word +0x08 is the source pointer into the staging buffer
- descriptor word +0x0c is the next descriptor pointer or zero
- write the unchanged active descriptor base through 0xb3000014, then OR 0xb3000000 with 0x108
- wait on the USB completion event flag and repeat if bytes remain

## Scenario Matrix

Scenarios assume the normal 64-byte endpoint chunk value, matching the descriptor path's `0x40` setup writes.

| Response bytes | Batches | Descriptor counts | Flagged descriptor words |
|---:|---:|---|---|
| `0` | `1` | `1` | batch 0 desc 0 `0x08000000` |
| `1` | `1` | `1` | batch 0 desc 0 `0x08000001` |
| `18` | `1` | `1` | batch 0 desc 0 `0x08000012` |
| `32` | `1` | `1` | batch 0 desc 0 `0x08000020` |
| `34` | `1` | `1` | batch 0 desc 0 `0x08000022` |
| `38` | `1` | `1` | batch 0 desc 0 `0x08000026` |
| `64` | `1` | `1` | batch 0 desc 0 `0x08000040` |
| `65` | `1` | `2` | batch 0 desc 1 `0x08000001` |
| `255` | `1` | `4` | batch 0 desc 3 `0x0800003f` |
| `320` | `1` | `5` | batch 0 desc 4 `0x08000040` |
| `321` | `2` | `5, 1` | batch 0 desc 4 `0x08000040`, batch 1 desc 0 `0x08000001` |

## Descriptor Details

### Response `18` bytes

- batch `0`, remaining after batch `0`:
  - `0` len `18` word `0x08000012` src `0x90022bd0` next `0`

### Response `38` bytes

- batch `0`, remaining after batch `0`:
  - `0` len `38` word `0x08000026` src `0x90022bd0` next `0`

### Response `65` bytes

- batch `0`, remaining after batch `0`:
  - `0` len `64` word `0x00000040` src `0x90022bd0` next `0x90022700`
  - `1` len `1` word `0x08000001` src `0x90022c10` next `0`

### Response `321` bytes

- batch `0`, remaining after batch `1`:
  - `0` len `64` word `0x00000040` src `0x90022bd0` next `0x90022700`
  - `1` len `64` word `0x00000040` src `0x90022c10` next `0x90022710`
  - `2` len `64` word `0x00000040` src `0x90022c50` next `0x90022720`
  - `3` len `64` word `0x00000040` src `0x90022c90` next `0x90022730`
  - `4` len `64` word `0x08000040` src `0x90022cd0` next `0x90022740`
- batch `1`, remaining after batch `0`:
  - `0` len `1` word `0x08000001` src `0x90022bd0` next `0`

## Remaining Live Unknowns

- whether the open payload inherits initialized USB transfer-state RAM after ACL upload
- whether the control-IN completion event flag can be replaced with a safe polling loop
- which live register transition confirms the 0x108 kick completed without ThreadX

