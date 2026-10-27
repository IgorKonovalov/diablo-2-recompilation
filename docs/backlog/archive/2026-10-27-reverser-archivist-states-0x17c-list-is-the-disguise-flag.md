---
from: reverser
to: archivist
date: 2026-10-27
status: done
context:
  - ../../findings/skills/0013-druid.md#6-the-melee-functions-start-56-57-58-do-121-122
resolution: "Folded on lane/a51f: [States § Flag bits](../../tables/States.md#flag-bits-0x010-40-bits-bit-i--byte-0x010--i8-bit-i-mod-8) links skills/0013 § 6 for the disguise list (+0x17C/+0x180, [I]) and the other STATES_Load lists; the § Open questions candidates bullet struck as answered, the other-writer question kept [L]; [plan 0051 log](../../plans/done/0051-backlog-sweep-6.md#implementation-log)"
---

Plan 0051 Phase 1b item 3a (`lane/p51s`, 2026-10-27): the States § Open questions bullet *The shape-shift state list* can be answered. [I] `STATES_Load` (0x00618100) fills `DataTables+0x17C` (`u16` ids) / `+0x180` (`s16` count) through `sub_00611DC0_StatesListByFlag` with `k = 16`: the rows with flag bit 16, **`disguise`** (byte `+0x12` bit 0), in id order. On stock data that is 63, 93, 119, 139, 140, 176, 177 (bit 16 of § Flag bits by row). It is not `restrict`, `group` 3 or `transform`. The same pass builds `+0x16C` (`pgsv`), `+0x174` (`curse`), `+0x184` (`active`) and `+0x18C` (rows with `itemtype` `+0x2A` > 0). Reading: [skills/0013 § 6](../../findings/skills/0013-druid.md#6-the-melee-functions-start-56-57-58-do-121-122). Asked: link it from the bullet (and the `disguise` row's Meaning cell if you see fit), keeping the finding's `[I]`. Context: [plan 0051 log](../../plans/done/0051-backlog-sweep-6.md#implementation-log)
