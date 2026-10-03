# Recorded bulk-OUT publication execution

Synchronous full-speed OUT1 arm and publication through recording cache/register hooks, actual TinyUSB callbacks and the existing adapter/descriptor/document path. Independent literal traces, pre-reservation refusals, retained original failure identity, explicit cleanup, exact pixels and END_DOC are compared in synthetic RAM.

40 host; 40 QEMU cases. Every explicit read, attempted register command and ordering hook, original cleanup/grant identity, packet, pixel, document event and guarded allocation is compared.

No physical register/cache backend, DMA/IRQ acquisition, boot, USB traffic or printing. Mode, stopped receive DMA, global SETUP/OUT readiness, stable register/RDE writers, CNAK window, exact CPU/DMA mappings and safe cache-line envelopes remain supplied. Completion and physical cleanup are external facts. Recorded writes never generate read observations or imply USB acceptance. Tests add zero native or physical page lifecycles; first profile is full-speed64, configuration0/1, interface0/alt0.
