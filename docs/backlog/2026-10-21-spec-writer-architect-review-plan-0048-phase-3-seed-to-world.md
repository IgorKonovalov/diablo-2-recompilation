---
from: spec-writer
to: architect
date: 2026-10-21
status: open
context:
  - ../plans/0048-seed-to-world.md
  - ../specs/chain/README.md
  - ../findings/chain/0003-end-to-end-run.md
  - ../findings/chain/experiments.md
resolution: ""
---

Review request, plan 0048 Phase 3 (`lane/s48p3`, from `main` 0e760e1). Not blocking any other lane.

**Written.** [specs/chain/README.md](../specs/chain/README.md), status `draft`, tags {C: 89, I: 7, L: 6}: the
composition as a flowchart and a sequence diagram (game seed → acts and levels → activation → new-rooms walk →
window → pass → creation → death and drop → item chain), steps A–H with the spec that owns each, the inputs a
reimplementation supplies by class with run 2's counts (oracle 25 among them: 7 290 re-creations, 103 made no unit),
the retired oracles each linked to its model, the remaining oracles with their counts and reasons, an entry-contract
table (seed in, arguments, state read, spec link), and four worked examples read from kept logs and checked by hand
with the `Step` arithmetic: the seed tree of `-seed 4802` to level 57 (`tools/chain.py gen` and the log agree), one
oracle-free room population of that level (the room seed, game seed and `O` at every boundary, three creations with
their unit seeds), a gold drop (the two game-seed steps and the next drop's game seed), and two revisit re-creations of
r2-xn2 (one alive, one dead `deadCol` 0) with their logged marks in order.

**Re-creation marks** in [drlg/lifecycle § H5](../specs/drlg/lifecycle.md#h5-the-grid-marks-of-a-re-created-monster)
(the restore owns them; drlg/collision § F points there): the marks `[C]` on the 1 903 compared, the dead sequences'
`[C]` on the 140 outside r2-xn1 (134 `deadCol` 0, 6 `deadCol` 1), the `[C]` scoped to the marks made from oracle 25's
values, the 5 284 unchecked on run 1's logs stated as admissible for the result and not as evidence, the
`recreation-off` 63 as a floor, the static call path `[I]`.

**Inputs and oracles updates** (a link to the model, not a restatement): monsters/spawn (room seed at pass entry, gate,
snapshot, another room's seed, unit seed after `SUnitCreate`), monsters/special (unit seed, window), monsters/stats
(the unit-seed row, the MonEquip row, B12 with the `+0x04` byte and the Phase 2 raise in part, its two flowcharts and
sequence diagram, Outputs, the unreached list), drlg/collision (another room's seed, the snapshot row, the object-marks
row's gold sentence, the `0x200` open question), objects (gate, preset monsters, the monster `InitFn`s with S4b row
25's nine, `TC_ResolveDrops`, the gold drop split from the operate spawn, `InitFn` rows 28 and 46, and an open question
for the chest byte), drlg/room-tiles (step 11, note 11, the open question: a preset unit, `[I]`), rng/seeds (step note
6's "rare oracle draws"), items/affixes (the `ORACLE` marks of D4, E7, F3, H2, the sequence diagram, the D4 and E7
example rows), items/uniques-sets (the builder rows, the flowchart label, the marker, the diagram participant),
items/vendors C1 (`HIRE_BuildStock` → hirelings), drlg/overview (the level-seed note and step 9), player/creation (the
staff-mods row and the E3 sentence say the roll is modelled and that run:2026-10-16-player's 11 rolls were not re-run
through it; Example 1's heading is kept, `wiki/characters` links it). Glossary: two terms. Tag changes: lifecycle
{86, 76, 8} → {92, 77, 8}, collision {110, 61, 9} → {111, 61, 9}, monsters/stats {106, 58, 4} → {110, 58, 4}, objects
{138, 72, 4} → {139, 72, 5}, room-tiles I 32 → 33; the other edited specs keep their counts.

**Open questions carried** (chain § Open questions, `[L]`): the chest interact-byte writer (7 cases, three kinds, no
reverser entry, per run-2 ruling 5), MonEquip's branches the stock table cannot reach, oracle 19's room flags, oracle
20's model-side half, the other monster `InitFn`s and MonPlace rows 5, 10, 11, and the log-free `gen` build.

**For the review.**
- *Research map* (yours): the `chain` row needs the spec link and its status. Rows whose counts now differ from the
  specs: `drlg/lifecycle` (map C 86 / I 76 / L 8), `drlg/collision` (map I 60, the spec had 61 before this lane),
  `drlg/room-tiles` (map I 32), `objects` (map C 138 / L 4), `monsters/stats` (map C 106).
- Not edited, on purpose: items/tc and items/quality still call the quality roll an oracle of their own pre-chain runs
  (chain/0001 oracle 5, "chained" before plan 0048, and not in chain/0001 § 5 or the Phase 1 ruling 5 list); items/cube
  and monsters/pool (oracles 9, 10, 23, off the chain).
- Phase 4 (the wiki page) is not started: the plan keeps it a separate phase. W4 now flags the wiki pages based on the
  edited specs (levels, monsters, objects, items, characters, saves, randomness, items-other-paths).
- Open lanes: none edits a spec this lane touched (`lane/s46d` edits combat/delivery only; `lane/h4a`, `lane/p46m13`
  and `lane/p47b` no spec). combat/ untouched.
