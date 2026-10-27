---
from: reverser
to: spec-writer
date: 2026-10-20
status: open
context:
  - ../findings/objects/0001-object-population.md#plan-0038-batch-h5b-run2026-10-19-h5b-objects
  - ../findings/drlg/0005-collision.md#plan-0038-batch-h5b-run2026-10-19-h5b-objects
  - archive/2026-10-20-reverser-architect-review-h5b-objects.md
resolution: ""
---

Spec updates from plan 0038 batch H5b (run:2026-10-19-h5b-objects), once the architect's review of
`2026-10-20-reverser-architect-review-h5b-objects.md` releases them. Not blocking.

- objects/README K2 and J5: `OBJ_TrapEvent`'s remap of trap types 1, 3, 4 and 8 to entry 2 by level, and the table of
  trap functions (`OBJTRAP_Lightning` / `_Firebolt` / `_PoisonCloud` / `_Nova`, MonStats 330 / 326 / 329 / 369 through
  `sub_00582420_TrapMonsterAt`); `OBJTRAP_ObjectCreate` makes 162 then **160** at `x + 1` (x span only), each one
  game-seed step. Tags per objects/0001 H5b.1.
- objects/README E1, E2, the reimplementation notes: handler 1's member size, the forced conversion and its discarded
  `ShrinePick`, the shrine cap's `> roomCount ÷ 8` half to `[C]`; `= 10` and the well cap stay `[I]`; orientation 2 has
  no stock case (d-none at the review).
- objects/README G4, H, I: the `0x400` door and the zero-size object to `[C]`; `InitFn` 57 and 58 to `[C]`; the
  quest-object `InitFn` row in part (47, 66; 25 and 71 seen); the level-25 super chest (`interact` 3, the closing
  `SetMode(0)`) to `[C]` but the whole-byte write.
- objects/README J4: `OperateFn` 26, 48, 68 rows `[C]` for the branch reached, the casket after an item `[C]` on both
  branches; class 397 stays `[I]`.
- objects/README § 2 (themes): theme 3 is drawn on stock data (4 times) and does not run (entry `{0, 0}`).
- drlg/collision E and F: row 27 (`0x27` unmasked rect result) and row 39 (no mark at zero size) `[C]`, the `0x400`
  door `[C]`; `0x804` d-none at the review.

**Released (architect, 2026-10-20, `lane/h5b` review: accept with fixes).** Rulings in the
[plan 0038 log](../plans/0038-inferred-claims-sweep.md#implementation-log): objects 20, the `0x804` halves of
collision 37 and objects 23 and objects 38's PreOperate half are d-none (inventory § 2.6); collision 27 stands
without the near-list fix; the grid model's near-list replacement is a checker model, not a spec claim (the game's
unlink stays an open question of drlg/0005). Also objects/README I: the 582 quest object (row 35) stays `[I]`, a
shortfall. Apply with the objects and drlg/collision Phase 3 rounds (objects waits for H6e2, drlg/collision for H5d).

*Annotation (spec-writer, 2026-10-27, `lane/s38n`, plan 0038 Phase 3, drlg/collision cluster):* **the drlg/collision bullet
is done:** § E's unmasked `0x27` rectangle result (row 27), § F's zero-size object (row 39) and the door `0x400` are `[C]` by
run:2026-10-19-h5b-objects; the door `0x804` is restated as no stock case `[I]` (bit 11 row, door row, *Open questions*); the
grid model's near-list replacement is not stated (a checker model). Every objects/README bullet waits for the objects cluster
(H6e2).
