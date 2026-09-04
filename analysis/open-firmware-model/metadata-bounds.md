# Stock metadata allocation bounds

offline analysis; no fixture was sent and no installed runtime was changed

The logical-clip fixture requests 15 items but supplies only 13 in the declared metadata buffer. Paper and media items lie outside that initialized allocation.

The portable core safely parses all 180 payload bytes. That model result is not proof of equivalent stock behavior for this fixture.

10 fixtures fit the declared metadata allocation; 1 does not.

| Fixture | Status |
|---|---|
| matrix-a4_2400x600 | bounded |
| matrix-a4_600x600 | bounded |
| matrix-a4_cardstock_media | bounded |
| matrix-a4_default | bounded |
| matrix-a4_draft | bounded |
| matrix-a4_logical_clip | invalid |
| matrix-a4_manual_feed | bounded |
| matrix-a4_two_copies | bounded |
| matrix-legal_default | bounded |
| matrix-letter_default | bounded |
| minimal-page-a4 | bounded |

## Instruction evidence

| Address | Bytes | Meaning |
|---|---|---|
| 0x10009e19 | 288106 | l16ui a8,a8,12: header reserved bytes |
| 0x10009e1f | 28166708550c | save reserved; remaining payload subtracts it |
| 0x10009e27 | 088a022b0a02 | allocation argument is reserved, flags=2 |
| 0x10009e30 | 5824c3 | call8 allocator 0x10013140 |
| 0x10009e4c | 2b1265dce0 | read callback destination is reserved buffer; count is reserved |
| 0x10009e74 | da20db40dc50 | remaining payload read goes to separate buffer |
| 0x10009fe5 | 2b12652c1267dd305bfed7 | START_PAGE builder receives reserved buffer plus original item count |
| 0x10009d24 | 8830b144a833754b0263fe44 | builder advances by item size and stops by item count, with no remaining-byte bound |

Allocator rounding does not establish initialization or contiguity of separately allocated data. Actual erroneous stock output is not predicted or tested.
