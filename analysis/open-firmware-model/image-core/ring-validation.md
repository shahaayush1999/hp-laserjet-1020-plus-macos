# Compiled software decoder and output ring

Status: pass. One compiled C call decodes original JBIG into its own four-slot software output ring. Every output and storage byte is checked; acceptance and completion are separate explicit consumer actions.

36 sanitized host cases, 36 target cases, 11 host API rejection controls and 11 target API controls. Six 17-row host cases match the original bounded ownership trace exactly.

Serialized RAM experiment, with an explicit simulated consumer. No original owner/allocator integration, native scheduling, interrupts, hardware writes, physical pixel-format proof, page cleanup or printing. Odd-row images remain outside the stricter ZjStream page planner; this does not broaden that grammar.
