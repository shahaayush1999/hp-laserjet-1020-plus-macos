/* SPDX-License-Identifier: GPL-2.0-or-later */
#include <stddef.h>
int memcmp(const void *a,const void *b,size_t size) {
    const unsigned char *p=a,*q=b;
    while (size--) { if (*p!=*q) return (int)*p-(int)*q; p++; q++; }
    return 0;
}
