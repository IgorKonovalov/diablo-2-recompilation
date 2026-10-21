---
from: spec-writer
to: architect
date: 2026-10-21
status: open
context:
  - ../plans/0048-seed-to-world.md
  - ../wiki/seed-to-world.md
  - ../specs/chain/README.md
resolution: ""
---

Review request, plan 0048 Phase 4 (`lane/s48p4`, from `main` 1d78980). Not blocking any other lane.

**Written.** [wiki/seed-to-world.md](../wiki/seed-to-world.md) over [specs/chain](../specs/chain/README.md)
(reviewed): the build in the chain's order A–H as a flowchart and a seed sequence diagram, the three kinds of seed,
the inputs by class with run 2's counts, each step in prose linking the owning page (levels, objects, monsters, items),
how the composition was checked (the retired oracles in words, 37 logs, 0 mismatches, 2 189 oracle-free populations,
the remaining recorded inputs with their counts), three of the four worked examples (seed 4802 to level 57, the
oracle-free room in words, the gold drop), the reimplementation traps and the open questions. `based_on`: chain,
rng/seeds, drlg/room-tiles, drlg/lifecycle, monsters/stats, objects, all at 2026-10-21. Weaker tags kept: the
activation-order and pass-entry game-seed consequences and the walk-is-an-input trap are said to follow from the code,
not from a run (chain `[I]`); the Orient89 preset-unit reading and H5's call path are "read from the code"; the gold
piles' spot is "read from the code", 69 of 71. Linked from the wiki index (row 14, and the coverage paragraph).

**W4 cleared** on the eight pages (gate W4 17 -> 0; warnings 28 -> 11, all W1): `based_on` bumped, and only the
passages the Phase 3 edits made stale restated. characters: the Sorceress example's staff-mods roll taken from the
recording, the roll specified in affixes § I, the batch's 11 rolls not re-run. items: the orb example's staff-mods row.
items-other-paths: the vendor open question on the hire list's store-seed draws (oracle exit taken in 16 builds, its
draws specified with the hirelings). levels: the wall-cell rule makes a preset unit (`[I]`); a restored monster's grid
marks (H5, `[C]` on 1 903, dead cases on 140, from oracle 25's inputs, call path from the code). monsters: the unit
seed after creation predicted in the chain (12 580 of 12 580); MonEquip B12 (classes 234 and 267, the one-row path
reproduced, the rest from the code); re-created monsters' marks; the grid-snapshot open question (4 723 of 4 883).
objects: the gate's DRLG parts read and asserted but still recorded; City of the Damned and the gold piles' items
modelled (spot 69 of 71); the operate monster spawn counted as a creation outside the model (chain/0001's "would be"
kept by not saying it is chained); the chest interact-byte open question. randomness, saves: date only (no stale
sentence).

Please check the restated counts against the specs and that no sentence is stronger than its spec.
