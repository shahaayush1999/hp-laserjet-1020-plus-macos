# Original native retirement tail

28 standalone QEMU cases pass, including two excluded-path mutations.

- The native wrapper enters the original RAM retirement tail once per linked node, supplies completion flag 1 and a zero pending cursor, and executes original reference decrement, slot clearing, event-set and standard CPU INTCLEAR code before returning through a valid register window.
- Empty, one-, five-, six- and thirteen-node fixtures preserve every unrelated work/node byte. References 1, 2 and 65535 each decrease by one; event bit 8 is set through the original primitive. Each completed entry writes bit 20 to INTCLEAR. No runtime host service is used.
- Both RAM fills and both nonzero-pending-cursor mutations are checked. A mutated cursor stops at the excluded instruction 0x1001434b before it executes, with no next-transfer or MMIO instruction visited.

Node consumption, no pending DMA and successful band completion are explicit fixture inputs. Original event creation rejects the initial null-caller/ordinary-system fixture with result 19; a separate nonwaiting constructor caller is then supplied. The hardware IRQ prefix, raster instructions, DMA, engine/PrintMgr tasks, automatic interrupt delivery and physical printing do not execute. The standalone event has no waiter; scheduled integration remains a separate check. INTCLEAR execution verifies its value and return, not a physical interrupt or its origin.
