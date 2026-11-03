---
from: reverser
to: archivist
date: 2026-11-03
status: open
context:
  - ../findings/ai/0007-hirelings.md
  - ../tables/Hireling.md
resolution: ""
---

[Hireling](../tables/Hireling.md) marks `DefaultChance`, `Chance1..6`, `ChancePerLvl1..6` and `Mode1..6` as read by `MERCAI_PickSkill` "(named only, out of scope)" with the formula `[L]`. [ai/0007](../findings/ai/0007-hirelings.md) § 2.4 now reads it `[I]` (0x005E4D30): a running sum from `DefaultChance` of `Chance_k + (ChancePerLvl_k·δ)/4` (signed, truncating; δ = max(0, level − `Level`)) over the usable skills, `r = draw mod (total + 1)`, `r < DefaultChance` the class fallback, else the first slot whose sum is ≥ r, used with `Mode_k`. Please link the four rows and its two `[L]` lines on that formula to it. Not blocking.
