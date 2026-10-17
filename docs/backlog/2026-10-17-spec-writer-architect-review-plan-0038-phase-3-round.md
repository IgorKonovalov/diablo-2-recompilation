---
from: spec-writer
to: architect
date: 2026-10-17
status: open
context:
  - ../plans/0038-inferred-claims-sweep.md#implementation-log
resolution: ""
---

[2026-10-17] from spec-writer → architect: review plan 0038 Phase 3 round 4 on `lane/p38s4` (from `main` `2783aee`; commits `4dc605a` data/calc, `f8b9c76` rng/README, then the backlog and plan log). Old → new: [data/calc](../specs/data/calc.md) {C 77, I 66, L 3} → **{C 129, I 17, L 3}**; [rng/README](../specs/rng/README.md) {C 22, I 8, L 1} → **{C 28, I 4, L 1}**. Research-map rows for both rewritten; wiki [game-data](../wiki/game-data.md) restated for calc (`based_on` 2026-10-17, W4 0) and [randomness](../wiki/randomness.md) restated (same date, no W4). Points for the review: (1) data/calc's new § G1 `[C]` bullet on `MISS_GetElemMin`/`Max` (S1f review (f)) and the split `m2eo m2ey me3o me3y` table row `[C]`, taken out of the deferred row 32's `[I]` row; (2) the NULL-callback skip (S1f (g)) and the `MulDiv` negative-`c` rule (S1f (b)) are not written into data/calc: they belong to data/excel J3 and monsters/stats A1; (3) rng's 9 unreferenced bodies folded into step note 4's `[I]` (weaker tag, as `RangePow2Plus`'s own d-none); (4) drlg/preset L154 (S1f) is not done here, since `lane/p39s2` edits that spec. Context: [plan 0038 log](../plans/0038-inferred-claims-sweep.md#implementation-log)
