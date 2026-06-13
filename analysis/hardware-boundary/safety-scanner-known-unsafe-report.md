# HP 1020 Custom Firmware Safety Scan

- fail hits: `4`
- watch hits: `0`

| Severity | Kind | File:line | Description | Text |
|---|---|---|---|---|
| `fail` | `unsafe_func_video_render` | `analysis/dispatch-mmio/decompiled/10015214_hp1020_video_render_or_dma_candidate.c:1` | video render/DMA path | `/* Function: 10015214 hp1020_video_render_or_dma_candidate */` |
| `fail` | `unsafe_func_video_render` | `analysis/dispatch-mmio/decompiled/10015214_hp1020_video_render_or_dma_candidate.c:6` | video render/DMA path | `undefined4 hp1020_video_render_or_dma_candidate(int param_1)` |
| `fail` | `unsafe_func_engine_io` | `analysis/dispatch-mmio/decompiled/10015c68_hp1020_engine_status_io_candidate.c:1` | engine command/status path | `/* Function: 10015c68 hp1020_engine_status_io_candidate */` |
| `fail` | `unsafe_func_engine_io` | `analysis/dispatch-mmio/decompiled/10015c68_hp1020_engine_status_io_candidate.c:6` | engine command/status path | `uint hp1020_engine_status_io_candidate(undefined2 param_1)` |
