# Continuous full real-host two-page RAM contract

Drafted 2026-10-05 before target build or execution. This is a separate offline
profile; no upload, physical controller/cache/engine behavior or printing is
implemented or established. It keeps every production C source, full buffer,
startup, linker, RAM/code cap and stack unchanged from the healthy entry profile.

The retained first host job is967 bytes, SHA256
`8ccf8bc1391e9025e3bd0a196dd155a04b967271bbb2a896bfd185453c0ed669`.
Unchanged vendored foo2zjs encodes literal128x4 and256x4 pages in one invocation.
All268 prefix and27 suffix PJL bytes, including the actual timestamp, are retained.
The full original JBIG decoder independently recovered exact64+128 source pixels.
Framing consumption does not implement responses to the included PJL commands.
No geometry/header rewrite, input truncation or timestamp normalization is allowed.

One entry owns initialization/CPU/stack/BSS. Initial reset/configuration, original
EP0 status completion and three separately supplied recovery promises establish
G2. The967 bytes enter in16 consecutive real receive packets (fifteen64, then7),
without a close, reset or special boundary between pages. At their actual output
callback entries require the independent first/second page plan, ring contents,
full original state and accepted/completed history. One END_DOC event is(2,1,0,2),
then the remaining raw suffix is consumed. At the sole close a seventeenth eager
OUT is still owned. An explicit supplied SUCCESS ZLP settles that owner, then
next service, empty pump, sole finish and own park. No host calls/reset/repair.

Two ordinary CPU paint cases. Natural stops: after-normalization, pre-c,
pre-first-output, pre-first-complete, pre-second-output, pre-document-event,
pre-close, pre-final-service, pre-finish, park. The first completion stop is the
actual ring-complete entry after acceptance. It separates two occurrences of the
same output function without a hidden skip or debugger single-step.

The target32 public table is manually derived before build:16 objects101 fields,
layout header(0x4850554c,3,457,16,101). Provider204 bytes remains unchanged.
Evidence stays9216 bytes/cap10176:308 four-word I/O rows,85 original nine-word
range rows,18 original nine-word binds,144 device bytes,192 exact pixels and one
20-byte event. Every I/O ordinal is its array index+1 and scope follows the full
independently reconstructed schedule; no event is discarded or hashed away.
Final308 I/O=19 initial+17*17,85 ranges=17*5,18 binds=1 status+17 bulk;
before-close305 I/O and82 ranges leave the final acquisition pending.
Header/table comments state the exact offsets and guards; unused bytes stayzero.

A new whole-linked audit, independent callback/stack review and exact ELF pin
must precede either CPU engine. Old stack bounds do not transfer automatically.
Admission requires full paired RAM/CPU snapshots, raw PC/access replay, original
function transitions, descriptor/payload poison and range checks, all exact
pixels and final storage; producer counters/hashes alone cannot accept a run.
No result exists until a fresh run passes its separate independent capture gate.
