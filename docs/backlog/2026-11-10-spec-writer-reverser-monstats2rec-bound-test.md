---
from: spec-writer
to: reverser
date: 2026-11-10
status: open
context:
  - ../specs/monsters/pool.md
  - ../findings/monsters/0001-level-pool.md
resolution: ""
---

**`sub_00451FE0_MonStats2Rec` (0x00451FE0): its own range test (plan 0064 Phase 4, S3 row 4; low priority).** monsters/pool D1 returns when the class's `monstats2` record is none. [monsters/0001 § 4](../findings/monsters/0001-level-pool.md) says only "if none, it stops"; the spec now states the none case `[I]` from the same lookup inlined in `MonSpawnTry` ([monsters/0002 § 6](../findings/monsters/0002-room-population.md#6-placement-monspawntry): `i2 < 0 or i2 ≥ nMonStats2`, then a null record, 0x005B2A66–0x005B2A8B). State the getter's own test (signed or unsigned compare, the count it reads, a null-record check) so D1 can cite it. No stock class reaches it (`MonStatsEx` 0..603 in all 734 records, `monstats2` 609 records), so nothing in the golden set depends on it.

*Architect note (`lane/n64x` review, 2026-11-10), a lead for the reader, not a statement:* r2 on the pinned image shows
0x00451FE0 testing the class first (`ecx < 0` or `≥ [tables+0xA80]` → 0, 0x00451FE2/0x00451FF0), then the `movsx` of
record `+0x18` (`< 0` or `≥ [tables+0xA98]` → 0, 0x00452005/0x0045200D), and returning `index·0x134 + [tables+0xA90]`
with no null test after the add. State it from the decompile.
