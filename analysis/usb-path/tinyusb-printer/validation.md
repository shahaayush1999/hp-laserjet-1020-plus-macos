# Reusable USB printer execution

Patched pinned TinyUSB, reusable class/receive adapter and bounded document/JBIG/output composition under synthetic DCD events, with independent USB packet and decoded pixel oracles.

132 host cases; 132 target cases. Exact decoded pixels, retained buffers and packet proposals checked.

No controller/MMIO/boot/cache implementation, physical status, USB traffic or printing. New configuration recovery requires three supplied promises without a fabricated class request. Legacy explicit reset and close paths remain covered. Cancellation, transfer settlement and output progress are synthetic; copies remain metadata. The separate continuous-printer experiment checks ordinary document boundaries without input closure.
