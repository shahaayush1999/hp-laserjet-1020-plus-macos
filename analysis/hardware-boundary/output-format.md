# Original output-format arithmetic

12 original-byte cases agree between the bounded interpreter and independent QEMU. Zero completed page lifecycles.

Original 600 dpi BPP1/2 bypass table selection, BPP control-field mask and stride-field mask. File-backed selector 2 is primary; 0/1 are explicit conditional RAM overrides. All destination addresses and values are observed before excluded video stores.

Fresh ENTRY and explicit register/PC cuts omit the prepare prefix, every video access and every readiness path. Old control/stride values, bypass geometry, output BPP and secondary=0 are supplied. The stride cut also supplies its destination/video registers, anchored to the original omitted L32R instructions. The BPP2 scratch counter alone changes in nonstack RAM; omitted video stores have no sink. BPP1 captures two pending words and does not execute the earlier table-zeroing loop. No complete hardware configuration, live engine selector, pixel polarity/bit order/lane order, decoded-DMA byte layout, padding interpretation, cache visibility, submission or printing is proven. These numeric tables must not be assigned physical sample meanings without independent hardware evidence.
