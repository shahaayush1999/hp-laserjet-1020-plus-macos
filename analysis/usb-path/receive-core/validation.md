# Bounded USB receive/document software

Compiled fixed receive queue feeding the bounded ZjStream/JBIG/output composition, with explicit synthetic transfer observations and separately supplied quiescence.

75 sanitized host cases; 75 independent QEMU cases.

Target state and fixed memory: 128168 bytes, excluding code, stack and fixture captures.

No USB controller, device descriptor scheduling, DMA/cache synchronization, endpoint configuration, physical abort/reset, boot or printing is implemented or proven. RX==0 and L==1 are a conservative single-descriptor policy, not HP success semantics. The caller must serialize events and truthfully establish receive/output quiescence; this code cannot prove it. Copies remain metadata.
