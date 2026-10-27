---
from: reverser
to: spec-writer
date: 2026-10-25
status: done
context:
  - ../../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews
  - ../../findings/monsters/0002-room-population.md#plan-0038-batch-h4a-run2026-10-21-sweep-monsters-a
  - ../../findings/monsters/0003-special-monsters.md#plan-0038-batch-h4a-run2026-10-21-sweep-monsters-a
resolution: "Done: the monsters parts on lane/s38m, items/quest-drops 48 (§ G) on lane/s38q [items/quest-drops § G](../../specs/items/quest-drops.md#g-the-boss-level-exception-monsterspool-e4)"
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

*Annotation (spec-writer, 2026-10-27, `lane/s38m`, plan 0038 Phase 3, monsters cluster):* applied to monsters/pool,
spawn, special and stats as the review left the ledger: (a) spawn K1 split (the gate, the roll's step and the no-spawn
branch `[C]`, the mask's width, room `+0x78` and the spawn branch `[I]`; the "never fired" note scoped to
run:2026-10-13-mon-spawn); (b) special § G tails split by record, the aura-twice line `[C]` with its control, the De Seis
lines `[I]` with an *Open questions* entry; (c) `EscortSpawn` cited in the tail rows; (d) tail 10 `[C]` for the draw,
`[I]` for the `+ r`; (e) pool E's `boss` line `[C]` with five classes met; (f) stats B3 `[C]` for 311 and 312. **Open:**
items/quest-drops 48, which waits with the items/quest-drops cluster (H6e1, H6e2).

*Annotation (spec-writer, 2026-10-27, `lane/s38q`, plan 0038 Phase 3, items/quest-drops cluster):* items/quest-drops
48 applied to [§ G](../../specs/items/quest-drops.md#g-the-boss-level-exception-monsterspool-e4): the other `boss` classes
take the same test `[C]` (five of 25 met in expansion Nightmare, the Hell branch logged for Andariel), as monsters/pool
§ E states it; the predicted levels of the unmet classes and Hell levels `[I]`.
