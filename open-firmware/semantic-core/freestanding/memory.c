#include <stddef.h>
void *memset(void *out, int value, size_t count) {
    unsigned char *p=out;
    while (count--) *p++=(unsigned char)value;
    return out;
}
void *memcpy(void *out, const void *in, size_t count) {
    unsigned char *p=out;const unsigned char *q=in;
    while (count--) *p++=*q++;
    return out;
}
