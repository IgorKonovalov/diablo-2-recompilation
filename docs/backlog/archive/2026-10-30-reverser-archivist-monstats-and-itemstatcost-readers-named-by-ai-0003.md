---
from: reverser
to: archivist
date: 2026-10-30
status: done
context:
  - ../../findings/ai/0003-pool-b.md
  - ../../tables/MonStats.md
resolution: "Linked in MonStats (§ AI columns, pool-B readers), ItemStatCost (rows 74 and 80) and States (row 22) [MonStats](../../tables/MonStats.md#ai-columns-plan-0052-phase-0)"
---

From [ai/0003](../../findings/ai/0003-pool-b.md) (plan 0052 P1.2 batch 2), readers to link in the table docs: MonStats lUndead (+0x0D bit 3) read by sub_005F2A00_AiGreaterMummyCb (row 22's corpse and wounded search, unless the searcher is Radament); MonStats Velocity (+0x32) and Run (+0x34) read by sub_005F4A70_AiVampire (the flee override parameter, Run*100/Velocity - 100 clamped to 0..120, only when Velocity > 0); MonStats Skill4/Sk4mode (+0x176/+0x183) by the vampire's Fireball/Missile pair; aip1..aip6 per row as § 2 of the finding gives them (the vampire's aip5 is a bit set: bit 0 the pair, bit 1 Skill2, bit 2 Skill3). ItemStatCost rows 74 (hpregen, row 29's perch bonus) and 80 (item_magicbonus, row 25's dance grant); States row 22 (spiderlay, row 26's lay test). All [I] readings.
