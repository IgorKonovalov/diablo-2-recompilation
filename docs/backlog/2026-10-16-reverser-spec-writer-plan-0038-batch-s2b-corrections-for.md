---
from: reverser
to: spec-writer
date: 2026-10-16
status: open
context:
  - ../findings/items/0005-affixes.md#plan-0038-batch-s2b-2026-10-16
resolution: ""
---

[2026-10-16] from reverser → spec-writer: plan 0038 batch S2b corrections for the Phase 3 re-tag (after the S2b review). (a) [items/properties § Entry points](../specs/items/properties.md#entry-points) L53: mode 6 is `RUNEWORD_Apply` (0x006600A0), not the set bonuses; `sub_00660120_SetBonusApply` uses `PROP_ApplyBlockByVersion` in modes 4 and 7 ([items/0006](../findings/items/0006-properties.md#plan-0038-batch-s2b-2026-10-16), prop 1). (b) L88: the `op` columns are read by the stat evaluation (func 13, the ethereal step); "not read" holds for the handlers, the writer and the stored lists (prop 2). (c) [items/affixes](../specs/items/affixes.md) L338: the bound is 188 type-eligible rows in one block (135 with `spawnable` and frequency ≠ 0), not 165 (affixes 15). (d) items/properties L454: the `+1` dmg% fallback is now reached 7 times (IR, prop 18). (e) L137: `ITEMS_RollStaffMods` is modelled, no longer an oracle (prop 4). (f) *Added at the S2b review:* aff 28 (G2 L544 and the L816 bullet) is raised in part: "not on the item seed" `[C]`, the `RangeB` draw on the unit seed `[I]`; aff 30 (I2–I6) keeps `[I]` on each threshold's strictness at its boundary (except the classic tier stop); (d) says the fallback is reached in the forced runs, with no frequency. Context: [items/0005](../findings/items/0005-affixes.md#plan-0038-batch-s2b-2026-10-16)

*Annotation (spec-writer, 2026-10-20, `lane/s38h2b`, plan 0038 Phase 3, items/affixes cluster):* **done in part.** (c) applied (C4 cap note: 188 type-eligible rows, 135 with `spawnable` and frequency ≠ 0) and the affixes half of (f): aff 28 split in G1, G2 and the reimplementation note ("not on the item seed" `[C]`, the `RangeB` unit-seed draw `[I]`), aff 30 I2–I6 with the threshold-strictness remainder; with them every S2b affixes row of [items/0005 § S2b](../findings/items/0005-affixes.md#plan-0038-batch-s2b-2026-10-16). **Open:** (a), (b), (d), (e) and (f)'s (d) clause, for items/properties (waits for H2c).
