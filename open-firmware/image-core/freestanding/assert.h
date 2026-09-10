/* The target uses the library's release mode; host sanitizer tests retain
 * the arithmetic coder's normal assertions. No host assert runtime is linked. */
#ifndef NDEBUG
#error The synthetic target must explicitly select NDEBUG
#endif
#define assert(expression) ((void)0)
