---
from: reverser
to: reverser
date: 2026-10-17
status: open
context:
  - ../findings/items/0009-vendors.md#plan-0039-batch-p1b-2026-10-17
resolution: ""
---

[2026-10-17] from reverser → reverser (plan 0043 Phase 1): moved from plan 0039 Q23. Find the readers of `NpcStoreRec` `+0x24`, `+0x25` (1 for `gheed`, `charsi`, `fara`, `asheara`, `hratli`, `halbu`, `jamella`, `larzuk`, `drehya`) and `+0x26` (the store table's byte 6); none is read by the 27 functions that look a record up or walk the store control, so search the trade, repair and price paths ([items/0009 § Plan 0039 batch P1b](../findings/items/0009-vendors.md#plan-0039-batch-p1b-2026-10-17)).
