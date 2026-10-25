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

**Released** by the `lane/h4a` review (architect, 2026-10-25: accept with fixes). Apply the ledger as the review left
it (inventory § 2.6, the H4a block and its review paragraph): raised 15, raised in part 9, shortfall 8. Changes from the
filed ledger: (d) special 54 (special § G, tail 10) is **raised in part**: the draw and its place are `[C]`, the `+ r` of
the `skeleton5` count stays `[I]` (only r = 0 met); (e) pool 12 and quest-drops 48: the `(H)` half rests on the branch
and Andariel's hell creation, five classes met (not six); (f) stats 14 and 13 (monsters/stats § B, still counted as
H4b) are raised whole: class 312's one `Range(4)` stored at `+0x0E` and `+0x0F` (monsters/0004 § H4a). The Lord De Seis
rows and spawn 11 stay `[I]`; their open question names the owner-play route.
