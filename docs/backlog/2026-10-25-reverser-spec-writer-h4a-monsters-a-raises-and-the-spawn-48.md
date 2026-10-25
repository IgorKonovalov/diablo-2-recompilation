---
from: reverser
to: spec-writer
date: 2026-10-25
status: open
context:
  - ../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews
  - ../findings/monsters/0002-room-population.md#plan-0038-batch-h4a-run2026-10-21-sweep-monsters-a
  - ../findings/monsters/0003-special-monsters.md#plan-0038-batch-h4a-run2026-10-21-sweep-monsters-a
resolution: ""
---

For the Phase 3 re-tag of monsters/pool, spawn, special, stats and items/quest-drops, once the H4a review has
accepted (released by it): apply the H4a ledger (inventory § 2.6 H4a block, the "Plan 0038 batch H4a" sections).
In particular (a) monsters/spawn K1 and its note (spawn 47, 48): the wanderer roll fired once; the note's "never
fired" is corrected, the gate, the roll's step and the no-spawn branch are `[C]`, the mask's width, room `+0x78` and
the spawn branch stay `[I]`; (b) monsters/special § G: the tails table rows for 10, 26, 27, 29, 36, 38, 42 and 60
`[C]`, the rest `[I]`; the aura-twice line with its extra-pick control; the Lord De Seis lines stay `[I]` (shortfall);
(c) `EscortSpawn` is now `C` in `re/symbols.csv`. Not blocking.
