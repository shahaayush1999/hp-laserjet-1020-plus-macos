# Portable semantic core validation

Status: pass; 512 cases; 11 generated streams; AddressSanitizer and UndefinedBehaviorSanitizer enabled.

The C implementation incrementally constructs page metadata and raster records in a caller-supplied bounded RAM arena. Generated sample geometry and raster byte hashes agree with the existing Python print-path model at five fragment sizes. Exact-capacity, short-capacity, malformed item/header, ordering, every short-stream truncation, object limit, multi-page, multi-BID and seeded binary-payload cases are checked.

The retained compressed bytes are opaque: no JBIG decompression or printing occurs. Active-work VIDEO_Y/RET/ECONOMODE sources match the ELF-verified direct START_PAGE builder. This code is native-host tested, is not linked into a probe, and contains no USB, hardware address, or output callback.
