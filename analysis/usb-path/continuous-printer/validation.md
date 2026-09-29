# Continuous printer document execution

Validated END_PAGE drains and exactly-once document observations through patched pinned TinyUSB, reusable receive and bounded JBIG/output, with independent document traces and exact pixels.

34 host cases; 34 target cases. Exact pixels, notification tuples, retained storage and packet proposals checked.

Synthetic DCD and synchronous software output only. Startup recovery supplies all three quiescence promises; no fabricated SOFT_RESET is used for configuration. Normal documents need no EOF/reset. Explicit close still detects truncation. Notification errors stop current input and preserve earlier observations. Copies remain metadata. No controller/MMIO/boot/cache, physical status, USB traffic or printing.
