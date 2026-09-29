/* SPDX-License-Identifier: GPL-2.0-or-later
 * The selected TinyUSB core includes inttypes.h but, with debug disabled,
 * uses none of its format macros or runtime declarations. This is a narrow
 * freestanding include shim, not an implementation of the hosted header.
 */
#ifndef HP1020_TUSB_FREESTANDING_INTTYPES_H
#define HP1020_TUSB_FREESTANDING_INTTYPES_H
#include <stdint.h>
#if CFG_TUSB_DEBUG != 0
#error "The narrow freestanding header only supports disabled TinyUSB debug"
#endif
#endif
