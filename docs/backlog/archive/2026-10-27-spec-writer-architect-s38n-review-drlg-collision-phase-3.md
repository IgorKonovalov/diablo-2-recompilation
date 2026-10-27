---
from: spec-writer
to: architect
date: 2026-10-27
status: done
context:
  - ../../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../../specs/drlg/collision.md
resolution: "Reviewed 2026-10-27 (architect): accept with fixes (3: omission, overclaim, misread); readiness confirmed (no collision row in H6e2); rulings in the plan 0038 log."
---

Review request, plan 0038 Phase 3, the **drlg/collision** cluster (`lane/s38n`, from `main` `0848879`, `main` `4fe6362`
merged after the spec commit). Its batches are S4a, S4b, H5b and H5d (inventory drlg-collision and § 5; none is in H6e2),
all accepted; H5d's review (2026-10-27) named this round as next. Every raise was checked against the "Plan 0038 batch S4a,
S4b, H5b, H5d" sections of [drlg/0005](../../findings/drlg/0005-collision.md) and the inventory § 2.6 blocks.

- **Counts** (script over the body, the gate's rule): {C 111, I 61, L 9} → **{C 157, I 35, L 7}**; `updated:` 2026-10-27.
- **S4a raised `[C]`** (inventory rows): 6 (`g_LogicFloodDirs`), 42 (ROW/RULES, the G3 note: the unexercised entries
  (3, −1), (4, −1) and the rows of orientations 4, 13, 15 split off `[I]`; the Constants row split the same way), 7 (A2's OR
  path), 12, 13 (writers), 15, 16, 17, 18 (bit rows), 20 (bit 11: `BlocksVis` `[C]`, `BlockMissile` alone `[I]` no stock door),
  29 (F1: missiles `[C]`, types 4 and 5 `[I]`), 31 (F3: sizes 1 and 2 `[C]`, others `[I]`), 32 (sizes by type, the player's size
  2 `[I]`), 33 (player row; the move mask named only), 38 (type 5 row), 41 (G1), 42's G1 note, 43 (G2 barriers), 44 (G2 merge
  and its edge points), 47 (J flags16), 49 (the reimplementation note).
- **S4b:** 10 split (one caller, three sites `[C]`; what each does and the active-neighbour condition `[I]`); 26 restated as
  240 / 124 / `baaltaunt` over the 365 classes `[C]` (correction (d)), "marks nothing" `[I]`; 4 restated as no stock input;
  2 kept `[I]`.
- **H5b:** 27 (§ E: the unmasked `0x27` rectangle result, 514 + 734), 37 (door `0x400` `[C]`, `0x804` no stock door `[I]`), 39
  (the zero-size object, § F).
- **H5d:** 5 (Constants, with the 153 / 258–263 refinement; 260 and 263 `[I]`), 8 (A3), 19 and 36 (bit 9, the item row, a new
  F1 note on the `UNIT_CollMarkRect` path, which also settles the S4a corrections entry's (b)), 24 (E1, a new § E bullet), 30
  ×2 (F2 lines 3 and 4), 45 (228, 298 flag 0, 528 `[C]`; 334 `[I]` with a no-stock-source bullet); in part 1 (Entry points
  row and § B's call bullet `[C]`, the write `[I]`), 21 (bit 13 and F2's note rewritten: `npc` or `inTown` with `interact`
  clear; `inTown` half `[C]`, `npc` half and `+0xC4` `[I]`), 46 (I2: one step per lookup in 46, 74, 125 `[C]`; the operand
  `[I]`); 9 and 11 kept `[I]`.
- **Open questions:** struck sizes 0/1, `SpawnClassCellTest` 228/334/528 and NPC patterns; the `Position` levels narrowed to
  the operand with n ≥ 2; C2's reader and `TileCollisionUpdate` narrowed; one new `[L]` for `MonIsNpc`'s `npc` half and the
  `+0xC4` branch; the door-mask clause of the object-masks entry rewritten.
- **Points to check:** (1) the readiness ruling: the orchestrator's prompt said drlg/collision waited on H6e2, and `lane/s38m`'s
  annotation said so too, but no collision row is in H6e2 (inventory, § 5, the plan log's waiting lists); I ran it. (2) The
  B-section call bullet names 0x0066E91B as the re-pick site (`call` at 0x0066E916 + 5). (3) Bits 1 and 2: only the writers
  are tagged `[C]`; the readers stay named.
- **Backlog:** closed the S4a corrections entry ((b)) and the H5d entry (monsters parts on `lane/s38m`, collision parts here);
  annotated the S4b corrections entry ((d) done, (a) waits for objects) and the H5b entry (collision bullet done, objects
  waits for H6e2). Counts entry
  [2026-10-27-spec-writer-architect-s38n-drlg-collision-counts-for-the-research-map](2026-10-27-spec-writer-architect-s38n-drlg-collision-counts-for-the-research-map.md),
  with the wiki W4 note (levels, monsters; not done here).

Not blocking.
