/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef HP1020_DCACHE_H
#define HP1020_DCACHE_H
#include <stdint.h>

/* Privileged BE/call0 target routines, not host functions or boot code.
 * Return1 after the requested CPU operations,0 before any operation on invalid
 * input. Empty ranges succeed without a barrier. Nonempty ranges must be
 * 16-byte aligned/sized, nonwrapping and inside [0x10000000,0x40000000).
 * That numeric window is a restriction, NOT evidence that memory exists there.
 *
 * The caller must own a valid stationary cached CPU RAM span including every
 * ACTUAL cache line touched, exclude all CPU/IRQ/DMA alias accesses, and supply
 * a compatible cache/privilege profile. The16-byte step comes from original
 * firmware; it alone does not prove the physical cache-line size. Never round
 * an arbitrary USB buffer into someone else's line or pass an uncached/DMA
 * label. No DMA address conversion, cache setup, exception recovery, hardware
 * completion or physical visibility guarantee is supplied by these routines.
 *
 * clean is for CPU-produced data before device reads. clean_invalidate is for
 * exclusively owned storage BEFORE permitting device writes. It is NOT an
 * acquire-after-DMA primitive: writing back stale dirty data then could destroy
 * device output. Existing controller/ownership/settlement gates still apply.
 * A target exception is not converted into a successful/clean result.
 */
uint32_t hp1020_dcache_clean_owned(void *cpu_base,uint32_t bytes);
uint32_t hp1020_dcache_clean_invalidate_owned(void *cpu_base,uint32_t bytes);
#endif
