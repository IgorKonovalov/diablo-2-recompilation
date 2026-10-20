---
from: reverser
to: reverser
date: 2026-10-17
status: moved
context:
  - ../../findings/items/0009-vendors.md#plan-0039-batch-p1b-2026-10-17
resolution: "moved to plan 0043 Phase 2 question 9 (read watchpoint on a store record +0x24..+0x26 during store, sell, repair, gamble and hire); static scan of the 10 economy functions negative (items/0011, economy-scan STOREREC 0 hits); ruled at the plan 0043 P1 review 2026-10-17"
---

[2026-10-17] from reverser → reverser (plan 0043 Phase 1): moved from plan 0039 Q23. Find the readers of `NpcStoreRec` `+0x24`, `+0x25` (1 for `gheed`, `charsi`, `fara`, `asheara`, `hratli`, `halbu`, `jamella`, `larzuk`, `drehya`) and `+0x26` (the store table's byte 6); none is read by the 27 functions that look a record up or walk the store control, so search the trade, repair and price paths ([items/0009 § Plan 0039 batch P1b](../../findings/items/0009-vendors.md#plan-0039-batch-p1b-2026-10-17)).
