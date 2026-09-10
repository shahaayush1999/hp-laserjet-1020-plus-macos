# JBIG-KIT streaming subset

Retrieved 2026-09-10 from Markus Kuhn's original
[JBIG-KIT 2.1 release](https://www.cl.cam.ac.uk/~mgk25/jbigkit/).
`provenance.json` records the original archive URL, observed SHA-256 and each
retained upstream/local file hash. These are content pins recorded at retrieval,
not an independently authenticated release signature. `COPYING` and the source
notices retain the GPL version 2 or later terms.

Only the streaming implementation, arithmetic coder, headers, usage text and
license are included. The existing `vendor/foo2zjs-source/jbig.c` full decoder
remains the independent host oracle; it is not part of the target component.

`LOCAL-CHANGES.patch` records the complete change from upstream `jbig85.c`:

- An absent previous row has index -1. Upstream formed a pointer before the
  caller's buffer even though its later reads were conditional. Host UBSan
  reproduced unsigned pointer overflow at both assignments. Use row zero as
  the unused pointer instead; retain the original validity conditions.
- Assemble header/marker byte fields with `unsigned long` casts. This avoids
  signed left-shift overflow on 32-bit targets when the top byte is large,
  including malformed marker fields. It preserves the intended unsigned value.

No compression decisions, arithmetic probabilities, context layout, marker
semantics or normalization were changed. The HP1020 wrapper normalizes a private
BIH copy only after rejecting everything outside its explicit narrow profile.
The validator checks local hashes and reverses the patch to verify the upstream
hash. The original failing host capture and harness snapshot are retained in
`analysis/open-firmware-model/image-core/`; they are not a passing target test.
