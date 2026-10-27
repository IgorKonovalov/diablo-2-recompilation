---
from: reverser
to: spec-writer
date: 2026-10-27
status: open
context:
  - ../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews
  - ../findings/drlg/0005-collision.md#plan-0038-batch-h5d-run2026-10-27-sweep-collision
  - ../findings/monsters/0002-room-population.md#plan-0038-batch-h5d-run2026-10-27-sweep-collision
resolution: ""
---

For the Phase 3 re-tag of drlg/collision and monsters/spawn, once the H5d review has accepted (released by it): apply
the H5d ledger (inventory § 2.6 H5d block, the "Plan 0038 batch H5d" sections). In particular (a) **a correction** in
drlg/collision § F (F2's step note *Pattern from size*, the bit table's row 13, the Inputs row of `npc`/`interact`): the
upgrade to patterns 3 and 4 is for MonStats `npc` **or** `inTown` with `interact` clear (else the unit's `+0xC4` bit 31,
`[I]`), and monsters/spawn's in-pass mark if it repeats the rule; (b) the Constants row of the `spawnCol` 1 and 3 masks,
with the refinement that only 153 and 258–263 reach the ring (the frog demons take `SpawnPosOnTile`); (c) § A's entry flag
`0x80` line, § D rows 9 and 13, § E's sizes 0 and 1, F1/F2's patterns 3 and 4, the item row of the footprints table, § H's
228, 298 (flag 0) and 528 rows, § I's `Position` levels (one step per lookup; the operand stays `[I]`); (d) B1 and the
plain AND-NOT stay `[I]` (shortfall), the 334 row stays `[I]` with its d-none note if the review accepts it; (e) the
*Open questions* lines that H5d answers. Not blocking.
