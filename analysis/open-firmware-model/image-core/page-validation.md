# Open complete-file image path

Status: pass. Complete ZjStream files pass through the open semantic parser, narrow page planner and open streaming decoder into packed image bands. Host output matches every byte from the original full JBIG decoder.

57 host cases; 35 target cases. Complete-file fragmentation, 6/13/64 BID splits, differing images across pages/documents, exact retained BIHs, paused output and strict default padding are checked.

Software pages only, separate from original native lifecycles. Compressed input remains in the caller arena. One decode per page, with copy count retained as metadata. No stock raw queue, DMA, physical format proof, engine, USB, boot or printing.
