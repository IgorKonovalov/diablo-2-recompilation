---
from: architect
to: reverser
date: 2026-10-17
status: open
context:
  - ../tables/Npc.md#multipliers-plan-0043-phase-0
  - ../tables/Books.md
  - ../tables/ItemTypes.md#repair-and-throwing-columns-plan-0043-phase-0
resolution: ""
---

[2026-10-17] from architect → reverser: plan 0043 Phase 1 inputs from the Phase 0 review (the archivist filed no separate request; the surprises are in the plan log). Read against the data in [plan 0043 log](../plans/0043-items-economy.md#implementation-log) surprises (a)–(j), and also: (a) which of the item's own `type` or its `Equiv` closure the repair test reads (the stock counts agree, so this is for the spec, not a case); (b) the readers of Books `+0x004`/`+0x010`/`+0x014` and their widths, and whether a tome's price reads Books `BaseCost`/`CostPerCharge` or the Misc `cost`; (c) how the affix term treats MagicPrefix `divide` 0 on the 21 priced rows; (d) whether a priced stat with `ValShift` 8 (7, 9, 11) is read raw or shifted; (e) what `max buy` caps; (f) `MERC_ResurrectCost`'s `L`, widths and the gold taken (the Hireling doc states the formula `[I]` from hirelings/0001 § 10). Context: [Npc § Multipliers](../tables/Npc.md#multipliers-plan-0043-phase-0), [Books](../tables/Books.md), [ItemTypes § Repair and throwing columns](../tables/ItemTypes.md#repair-and-throwing-columns-plan-0043-phase-0)
