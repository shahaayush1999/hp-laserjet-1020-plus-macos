# Stock raster callback bypass

- The stock ELF stores u32 1 at the backing pointer for datastore entry 32 (type 2). The original getter reads it directly; no fixture overrides that getter.
- With that file-backed value, the original prepare prefix sets video +0xc0=0 and +0xf4=0. The separately entered original band gate chooses its raw slot pointer despite a deliberately stale custom callback pointer.
- Two constructor-fragment cases execute the dynamic-backing relocation loops. They change entries 0 through 22 only, preserving entry 32 and its value 1. The rest of initialization is excluded; this is not proof of the live boot value.
- 42 prepare/band cases include 34 raw-buffer selections and eight stops before the custom call. Mutating entry 32 to zero enables callbacks only when work +0x36 is also zero; BPP1/300 clears the pointer, and a separately cleared pointer also suppresses the call.
- Unsupported BPP4/600 with both gates enabled retains the stale callback. This is a conditional finding, not support for that format. Stock configuration and nonzero work +0x36 suppress it in the tested fragments.
- A separate read-only byte audit distinguishes the raster payload pointer sent to channel A from the video slot pointer sent to channel B. The bypass-selected slot pointer is then written toward the video block in either lane branch. Skipping the custom callback does not provide or prove the hardware transformation between those buffers.
- No custom instruction, callback invocation, peripheral access, DMA or physical image processing executes. These fragment results are not completed page lifecycles or evidence of printable output.

## Limits and next evidence

- Prepare enters with an explicitly idle video context and supplied successful mutex acquisition, then stops before hardware/buffer setup.
- The band fragment is entered after the omitted peripheral-read prefix. Ring indices, descriptor units, non-final flag and both buffer addresses are synthetic; no producer filled the raw buffer.
- Constructor allocation returns synthetic RAM. Earlier RTOS setup, later default/persistence helpers and all remaining boot activity are excluded.
- The generic datastore writer can update type-2 backing; file value 1 is not a guarantee that every runtime path preserves it. A complete boot/writer audit or targeted stock observation remains needed.
- Work +0x36 also participates in JobMgr BIH-field handling. Changing a host bitmap item is not established as a callback-only switch.
- Usable image format, raw buffer production, output quality, engine timing, physical printing and recovery remain unproven.
