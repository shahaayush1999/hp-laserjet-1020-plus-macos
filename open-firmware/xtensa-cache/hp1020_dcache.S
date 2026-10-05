/* SPDX-License-Identifier: GPL-2.0-or-later */
/* No MMIO, mapping changes, calls, stack accesses or implicit range rounding.
 * Keep each operation on a2 for the independent stock-encoding comparison. */
    .text
    .begin no-transform
    .macro cache_range name, operation
    .balign 4
    .global \name
    .type \name, @function
\name:
    beqz a3, .Lok\@
    or a4, a2, a3
    extui a4, a4, 0, 4
    bnez a4, .Lbad\@
    movi a5, 1
    slli a5, a5, 28
    bltu a2, a5, .Lbad\@
    add a4, a2, a3
    bltu a4, a2, .Lbad\@
    movi a5, 1
    slli a5, a5, 30
    bltu a5, a4, .Lbad\@
    memw
.Lnext\@:
    \operation a2, 0
    addi a2, a2, 16
    bne a2, a4, .Lnext\@
    dsync
.Lok\@:
    movi a2, 1
    ret.n
.Lbad\@:
    movi a2, 0
    ret.n
    .size \name, . - \name
    .endm

    cache_range hp1020_dcache_clean_owned, dhwb
    cache_range hp1020_dcache_clean_invalidate_owned, dhwbi
    cache_range hp1020_dcache_invalidate_owned, dhi
    .end no-transform
