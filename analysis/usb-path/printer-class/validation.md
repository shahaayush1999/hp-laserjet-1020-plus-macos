# Bounded USB printer-class/document software

Compiled printer-class request/ownership layer composed with the bounded receive, ZjStream, JBIG and output pipeline. Synthetic wire bytes, old-event identities and explicit quiescence promises; exact independently decoded pixels and control reply bytes.

82 sanitized host cases; 82 independent QEMU cases.

Target state and fixed memory: 128256 bytes, excluding code, stack and fixture captures.

No USB controller, enumeration, EP0 framing, endpoint submission, DMA/cache, physical reset/abort, boot or printing is implemented or proven. Status is supplied or explicitly unknown fallback, never a measured printer state. Three reset acknowledgements and EP0 quiescence are external promises. The adapter must serialize events, preserve original identities, honor response lifetime, and establish actual quiescence. Copies remain metadata.
