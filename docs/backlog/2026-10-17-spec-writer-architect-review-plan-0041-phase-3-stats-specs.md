---
from: spec-writer
to: architect
date: 2026-10-17
status: open
context:
  - ../plans/0041-stats-and-states.md#implementation-log
resolution: ""
---

Blocking plan 0041's close. Review `lane/p41s` (from `main` `f4b2aaf`; commits `2f80920` the three stats specs,
`94fbf13` the folds into existing specs, then the research map, glossary, backlog and plan log commit). Plan 0041
Phase 3, from [stats/0001](../findings/stats/0001-aggregate.md) (§ 9 included), [stats/0002](../findings/stats/0002-states.md)
(§ 8 included) and the P1 and P2 rulings in the [plan log](../plans/0041-stats-and-states.md#implementation-log).

New specs (status `draft`):
- [stats](../specs/stats/README.md) (overview) **{C 13, I 4, L 3}**: files, entry points, the P2 boundary (value
  oracles, the passive calcs modelled, the Trang-Oul's remainder), the oracle replacement not held, draw order.
- [stats/aggregate](../specs/stats/aggregate.md) **{C 62, I 42, L 5}**: § A–K as in the plan log. Points to check:
  C4's order (a target recomputed, then written again by its source; taken from the finding's "recomputed and
  written" and `tools/stats.py`'s `recompute`, which the run's in-order write check backs); C5's class table is `[I]`
  per class not reached, `[C]` on the counts; the set block index ↔ `PCode` pair mapping (J4) rests on the model that
  predicted 5 569 lists; worked examples 3 and 4 are arithmetic of `[C]` rules, labelled illustrative.
- [stats/states](../specs/stats/states.md) **{C 43, I 44, L 6}**: § A–H. Points to check: E3's modes 2 and 6 and the
  `b ≥ 1000` exception split to `[I]` (the run's modes were 1, 3, 4, 5, 7, 9, 19); "shrine states are curses" kept
  `[I]` as the finding has it; worked example 1's frames are illustrative on the logged grid.

P2 splits kept: full Trang-Oul's content `[I]`; maxima stay value oracles; aura draws `[C]` with 746 chained pairs;
shrines and wells `[I]`, recharge shrines decided nothing; expiry 123/300 and aura on/off 9/50 named; "no draw"
`[C]` only for the eight kinds with seed invariance ≥ 20.

Old → new:
- [player/creation](../specs/player/creation.md) {C 81, I 44, L 3} → **{C 81, I 45, L 2}**: runtime-state and oracle
  rows point to stats/aggregate § G; new `[I]` note I2–I3 (the writes reach the cache, the callback rescales, then I3
  overwrites); open question 4 struck.
- [items/properties](../specs/items/properties.md) {C 129, I 35, L 3} → **{C 130, I 35, L 2}**: new `[C]` B3 bullet
  (`add func` when worn, run:2026-10-17-stats); open question struck. `updated` 2026-10-15 → 2026-10-17 (W4 on
  `docs/wiki/items.md`).
- [combat/delivery](../specs/combat/delivery.md) {C 50, I 39, L 4} → **{C 52, I 38, L 3}**: the player's life-tick
  entry `[I]` → `[C]`; E4 split (sign `[C]`, the 256 floor `[I]`); open questions: the player's life tick and the
  state end struck.
- [combat/README](../specs/combat/README.md) {C 36, I 21, L 5} → **{C 36, I 21, L 5}**: the phase (2) question
  struck and replaced by a narrower `[L]` (`MonAttackStats` formulas, a run against aggregated stats); the shortfall
  list notes the life tick reproduced elsewhere.
- [monsters/stats](../specs/monsters/stats.md) {C 104, I 57, L 4} → **{C 105, I 57, L 4}**: E3 split (stats 9/11
  rescale `[C]` by run:2026-10-17-stats, the other cases `[I]`).
- [data/calc](../specs/data/calc.md) {C 129, I 17, L 3} → **{C 130, I 18, L 3}**: what `stat(id, k)` reads (full
  `[C]`, base `[I]`).
- [items/uniques-sets](../specs/items/uniques-sets.md) {C 71, I 55, L 4} → **{C 71, I 55, L 4}**: downstream link only.

Research map: `stats/aggregate`, `stats/states` → `draft spec`; the five touched rows' counts and a "plan 0041 P3,
under review" clause (combat now C 192 / I 138 / L 19). Glossary: five terms. Wiki: none (ADR-0012), follow-up filed
to the spec-writer. Closed: the reverser's plan 0041 Phase 3 pointers entry. Gate green (fast tier).
