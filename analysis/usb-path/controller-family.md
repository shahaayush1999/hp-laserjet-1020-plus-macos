# USB controller-family comparison

Strong register/descriptor-family match to the classic Synopsys device-only UDC used by the Linux snps_udc driver; not the DWC2 high-speed OTG register layout. This does not identify an AMD chip or prove a compatible silicon revision.

Pinned Linux v6.12 [register definitions](https://github.com/torvalds/linux/blob/adc218676eef25575469234709c2d87185ca223a/drivers/usb/gadget/udc/amd5536udc.h), [driver](https://github.com/torvalds/linux/blob/adc218676eef25575469234709c2d87185ca223a/drivers/usb/gadget/udc/snps_udc_core.c) and [platform glue](https://github.com/torvalds/linux/blob/adc218676eef25575469234709c2d87185ca223a/drivers/usb/gadget/udc/snps_udc_plat.c) are preserved with provenance and GPL license under `controller-reference/linux-v6.12/`.

24 stock literal/layout matches and 18 byte-checked instruction anchors. Twelve re-arm cases agree between original instruction interpretation, independent QEMU and an independently constructed byte oracle. Both unredirected-store controls reject before MMIO.

| Item | Stock literal | Value |
|---|---|---|
| devcfg | `0x10005df4` | `0xb3000400` |
| devctl | `0x10005ea8` | `0xb3000404` |
| devsts | `0x10005e68` | `0xb3000408` |
| devint | `0x10005de4` | `0xb300040c` |
| devint_msk | `0x10005eb8` | `0xb3000410` |
| epint | `0x10005de8` | `0xb3000414` |
| epint_msk | `0x10005e00` | `0xb3000418` |
| in0_status | `0x10005e04` | `0xb3000004` |
| out0_status | `0x10005e08` | `0xb3000204` |
| out0_control | `0x10005e24` | `0xb3000200` |
| out1_control | `0x10005e70` | `0xb3000220` |
| out1_max_packet | `0x10005f08` | `0xb300022c` |
| out1_descriptor | `0x10005e60` | `0xb3000234` |
| in1_descriptor | `0x10005e84` | `0xb3000034` |
| in0_max_packet | `0x10005e9c` | `0xb300000c` |
| in0_descriptor | `0x10005ea0` | `0xb3000014` |
| out0_setup | `0x10005ef4` | `0xb3000210` |
| out0_descriptor | `0x10005ef8` | `0xb3000214` |
| out0_max_packet | `0x10005ee4` | `0xb300020c` |
| descriptor_owner_mask | `0x10005e30` | `0xc0000000` |
| descriptor_dma_done | `0x10005e34` | `0x80000000` |
| descriptor_last | `0x10005e80` | `0x8000000` |
| enumerated_speed_mask | `0x10005ea4` | `0x6000` |
| control_pair_and_out1_unmasked | `0x10005f04` | `0xfffcfffe` |

The old re-arm note called the leading byte an opcode/value 8. The full status word is `0x08000000`: the reference identifies bit 27 as the last-descriptor flag, with ownership bits 31:30 zero (host ready). Stock completion separately requires ownership 2 and reads the low 16-bit count. These labels are a cross-source interpretation supported by exact original bytes, not live controller observation.

Re-arm preserves descriptor bytes 4..7, selects an aligned nonzero next pointer or base plus offset, writes the target at +8, and clears +12. Submission precedes the status-byte stores in the original instruction order; this RAM experiment does not validate the bus ordering. Entire guard regions and completion flags are compared under two initial fills.

51 separate original RAM-fragment cases cross all four ownership states, both last-flag values and counts 0/1/64/512/1024/65535. Both engines admit only owner state 2 and reconstruct the low 16-bit count. Three additional receive-status controls show that this fragment does not reject bits 29:28: they must not be promoted to valid-transfer evidence. Zero is only the decoded field value here, not proof of how a real zero-length or 65536-byte transfer is represented. The IRQ/NAK prefix and downstream update/re-arm paths remain excluded.

6 original software-list drains (0/1/4 nodes, two fills) execute in both engines, with explicit host substitutes for free and outer mask calls. Original list peek/pop code runs; QEMU also executes its original short critical helper while the interpreter abstracts PS save/restore. The expected buffer/node free calls occur and the list becomes empty. A supplied busy descriptor and the entire guarded arena remain unchanged. This is software ownership bookkeeping, not DMA cancellation or proof that the substituted frees are safe on a device.

Eleven additional instruction anchors retain that drain call sequence and the original IRQ mask-8 test. The corresponding upstream UR bit is 3, but HP also consults wrapper status 0xb3010004 bit 4 in this branch. Neither that observation nor the Linux reset routine supplies an HP quiescence condition.

The pinned upstream OUT ISR checks endpoint BNA/HE before descriptor completion (snps_udc_core.c:2071-2092). It never interprets the declared RX status field. Thus the new software adapter treats nonzero RX as unsupported and reports endpoint-wide faults independently; RX zero is a conservative policy, not documented HP success. Upstream dequeue temporarily clears global RDE and gives back a request without an explicit quiescence poll (1250-1300). Its dummy-descriptor comments say HOST_BUSY while the code writes DMA_DONE (606-618). These are reasons to keep explicit external quiescence gates instead of copying this platform-specific cancellation path.

A separately byte-checked startup branch ORs `0x320` into device control, matching the reference BE/burst/mode bit positions. The branch and its peripheral stores are inspected only. This supports investigating the controller byte-order setting; it does not prove live configuration or portable DMA/cache behavior.

Use the existing Linux controller code to guide a small freestanding adapter, then assess a generic USB/printer class layer. Retain HP-specific startup, byte order, cache/alias and reset/abort questions. Do not add peripheral writes to the current software image pipeline or bypass the existing inert hardware-test ladder.

Original re-arm construction executes with supplied globals and the submission literal redirected to RAM. Status decoding starts after the omitted IRQ/NAK prefix, with a supplied descriptor, and stops before either next path. No USB controller behavior, real DMA/interrupts/cache, setup/reset/cancel correctness, live traffic, boot or printing is established. HP-specific wrapper registers at 0xb3010000/4 remain outside this match. The Linux driver is a reference, not a linked runtime or usable HP port.
