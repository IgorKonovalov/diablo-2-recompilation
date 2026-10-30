---
from: reverser
to: archivist
date: 2026-10-30
status: done
context:
  - ../../findings/ai/0004-pool-c.md
  - ../../tables/MonStats.md
  - ../../tables/MonStats2.md
resolution: "Linked in [MonStats § AI columns](../../tables/MonStats.md) (pool-C readers entry) and [MonStats2 MeleeRng](../../tables/MonStats2.md); row 36 slot disagreement routed to the reverser."
---

From [ai/0004](../../findings/ai/0004-pool-c.md) (plan 0052 P1.2 batch 3), readers to link in the table docs: MonStats2 MeleeRng (+0x0E) read by sub_005F5D50_AiCorruptLancer as the path stop distance and the RunToUnitStop distance of its charge (§ 2.3); MonStats Velocity (+0x32) and Run (+0x34) read by sub_005F6E60_AiZakarumZealot (the same Run*100/Velocity - 100, clamped 0..120, override parameter as the vampire, § 2.10); MonStats Skill4/Sk4mode (+0x176/+0x183) by sub_005F72D0_AiZakarumPriest (MonBlizzard, § 2.11); MonStats aip1..aip8 per row as § 2 of the finding gives them (rows 35 and 36 read aip6/aip7 only behind their Skill2/Skill3 tests, which explains the per-record slot disagreement of MonStats § AI columns for those two rows, § 1). All [I] readings. Not blocking.
