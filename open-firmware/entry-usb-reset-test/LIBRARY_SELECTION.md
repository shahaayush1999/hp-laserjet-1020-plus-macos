# Reset-profile GCC runtime selection

Frozen2026-10-03 before the first reset-profile build, linked audit or execution.
This is a precise admission expectation, not a claim about an emitted reset ELF.

The accepted healthy map selected `_umodsi3.o` for the original top-level
`hp1020_usb_runtime.o` loop's variable `%6u`, and `_udivsi3.o` for the RAM
provider. The new reset orchestration replaces that modulo loop with separate
bounded old/fresh loops. Its provider retains the division. Production C,
TinyUSB sources/configuration, compiler flags and pinned compiler remain the
same. The reset profile therefore expects exactly `_udivsi3.o` to be selected
from the original GCC archive, and exactly `__udivsi3` linked. An unexpected
selection is a new admission stop requiring original-source/byte investigation.

The complete original archive remains byte-pinned and captured:
878846 bytes, SHA256
`e57e97f0f5679a83f5a394d94fe024973f05d32be292293b247e647e567c4e32`.
Both known extracted original members remain captured, byte-checked against
that archive and independently section-classified, including discarded and
nonallocated sections. The existing extraction-manifest schema remains an
inventory of these captured members; it does not claim both were linked.

| Captured member | Bytes | SHA256 | Required map selection |
|---|---:|---|---|
|`_udivsi3.o`|2612|`6e2ed6774b25c833f8071872d6f7b699838e22f625bdb215cd21eea34a96814a`|yes|
|`_umodsi3.o`|2368|`f7cb9b22bf91ae5b5f40f06a9c2ad1d4e16ea5a7e7be8631e7f2595d89c3e5ee`|no|

The map must contain precisely the one original archive/member selection and
the unchanged28 unique LOAD inputs:26 C objects, startup and that archive.
The final ELF must have one76-byte `__udivsi3` function, whole SHA256
`97c0f245a842a23b8ca0ad47d15b781a0dc0537c7aa2dc7251efa494e734e3f9`,
with its original three-byte ILL at offset65 and following four-byte DIV0 data.
That one trap remains excluded from execution. No `__umodsi3` symbol, arbitrary
helper subset, new archive, changed helper bytes or admitted exception path is
allowed. Original raw archive/member notices and provenance remain preserved.

This sibling profile owns its selection check. The accepted healthy audit and
independent gate, including their exact-two-helper rule, stay byte-identical.
No target behavior, semantic checkpoint or hardware claim follows from this
source-level selection expectation.
