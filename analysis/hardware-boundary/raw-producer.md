# Original raw producer and admission

32 producer/queue/admission, 16 reference and 4 metadata cases agree between the bounded interpreter and independent QEMU. 8 further QEMU cases execute one supplied completion and actual allocator cleanup. Zero complete page lifecycles.

- The full original helper allocates its 120-byte node through the stock pool, initializes its embedded payload and sends message 9 through the original queue. The queue is then consumed by original JobMgr admission. The caller, owner hierarchy and ordinary ready state are explicit fixtures.
- Descriptor selector 0 maps to message selector 3 and appends the node. Descriptor selectors 1/2/3 map to 0/1/2; JobMgr still assigns references but does not append them to the tested raw list. No physical color or channel interpretation is assigned.
- The producer leaves the reference field outside its 70-byte reset. Original JobMgr overwrites it from the work copy count, normalizes zero copies to one, conditionally doubles it and overrides it to one for active work. This resolves reference initialization for the supplied admission path.
- Doubling is stored in 16 bits: explicit unsupported large-copy fixtures 32768 and 65535 yield zero and 65534 references. These are arithmetic boundary observations, not observed printer faults or supported copy counts.
- Raw IRQ mode is unchanged by this producer/admission sequence. When the supplied work allows BIH copying, admission copies the selected BIH fields; source kind 1/2 alone does not supply appropriate raw work metadata.
- With an explicitly allocated 16-byte input prefix and one reference, one supplied raw completion followed by original cleanup frees the kind-1 input allocation and node. Kind 2 frees only the node; the separately allocated unused input remains owned by the fixture.
- With two references, one supplied completion retains both allocations and the node, but changes a nonzero image pointer to the input allocation base. The next submission/cursor restoration is not established. The actual producer root and input-prefix origin remain unproven.

Serialized RAM execution with explicit caller, owner hierarchy, copy/mode metadata and a 16-byte input prefix. Task readiness is supplied; the real queue and allocator execute without waiters. Raw completion enters after the omitted peripheral prefix and stops before refresh. No complete page lifecycle, second-copy submission, boot, MMIO, custom instruction, USB contact, physical packing or printing is claimed.
