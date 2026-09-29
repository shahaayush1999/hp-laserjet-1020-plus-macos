# Original USB pause/restore intent

46 conditional RAM cases agree in both engines; 6 unredirected-register cases reject before peripheral access.

Original pause clears DEVCTL bit 3, saves OUT1/OUT0 NAK bit 6, issues SNAK bit 7, and requests a supplied delay. Original restore sets bit 3 and issues CNAK bit 8 only for a zero saved word. RDE bit 2 is preserved by both. Exact ordered RAM accesses and every nonstack mutable byte match separate oracles.

One annotated direct pause call is present at 0x100121f3 in 0x100121e4; its enclosing interrupt service, 0x1001658c and indirect callback are not executed. No annotated direct call or aligned file-backed pointer to restore was found. Calling restore and supplying later control images are experiment preconditions, not a recovered reset lifecycle.

Repeated pause replaces the saved NAK state; it is not a nesting counter. Restore enables TDE even when it was disabled before pause. Noncanonical saved nonzero values also suppress CNAK. None of these observations is an abort acknowledgement.

Three address literals are redirected to ordinary RAM; command bits do not self-clear and hardware readback is not emulated. Register images between calls are supplied, including the second pause NAK bits. The delay body/time and all caller context are excluded. No RDE disable, descriptor retirement, owner transition, FIFO flush, DMA reset, pending-IRQ drain or quiescence is established. Family bit names are reference-supported inferences, not HP silicon documentation or permission to issue these writes. Descriptor/payload preservation proves only the selected routines did not touch these supplied bytes. Zero physical USB transfers or printing.
