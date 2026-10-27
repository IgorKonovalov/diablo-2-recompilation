---
from: reverser
to: architect
date: 2026-10-27
status: done
context:
  - ../../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews
  - ../../findings/drlg/experiments.md#run2026-10-27-sweep-collision
  - ../../findings/drlg/0005-collision.md#plan-0038-batch-h5d-run2026-10-27-sweep-collision
  - ../../findings/monsters/0002-room-population.md#plan-0038-batch-h5d-run2026-10-27-sweep-collision
resolution: "Reviewed (architect, 2026-10-27): accept with fixes. Six fixes (collision 21's npc half [I]; drlg/0005 § 5 rewritten to the corrected rule; spawn 41 raised in part; 318 -> 360 pattern-5 creations; the rogue mismatch's description; collision 5's 260/263 and the RectClearWH row). Rulings in the plan 0038 log: 334 d-none, no Act III session owed; spawn 42 raised in part (H4b); collision 46 in part; rows 5 and 8 a-logs; the rogue objects.py mismatch to its own reverser entry. Ledger raised 10, in part 4, shortfall 2, d-none 1; totals static 567, harness 525, blocked 415 (d-none 289), deferred 2, raised 17: 1 526. Spec-writer entry released; H4b follow-ups closed."
---

Review plan 0038 batch H5d (`collision`; drlg/collision rows 1, 5, 8–9, 11, 19, 21, 24, 30, 36, 45–46 and monsters/spawn
41; `lane/h5d`), run:2026-10-27-sweep-collision. Nine kept sessions on slot 1 (expansion Normal, `UniqNova`), one
development launch in `dev/`; no log has `internal-error:`. Manifests `workspace/logs/h5d/h5d-manifest.sha256` (logs,
pilot outputs, `check/`) and `h5d-manifest-dev.sha256`, both `sha256sum -c` from `workspace/logs/h5d`. Checks produced by
`check/run-checks.sh` under `MemoryMax=4G`, plus `sweep_h5d.py static` (`check/sweep-static.txt`, needs r2).

Ledger of the 17 statements: **raised 11, raised in part 3, shortfall 2, proposed d-none 1** (inventory § 2.6 H5d block).

Points for the ruling:
- (a) **A correction of a `[C]`:** drlg/0005 § 5's *Pattern from size* (and the spec's F2 step note) said the NPC upgrade
  is MonStats `npc` and not `interact`. `MonIsNpc` (0x0063E860) also takes `inTown` (`+0x0D` bit 2), else the unit's
  `+0xC4` bit 31; `check/patterns.txt` scores 38 338 creation marks on 1 339 logs: 0 mismatches with `npc` or `inTown`, 254
  with `npc` alone (`cow`, `act3hire`, `act5barb1`, `injuredbarb1`–`3`, all `inTown` only). Carried into drlg/0005's
  summary, § 5, § 6 and monsters/0002 § H5d; the spec is the spec-writer entry's. Row 21 is filed in part for the `+0xC4`
  branch.
- (b) **Row 5 rests on kept logs** (a-logs in effect): the `MK0` masks of 1 330 earlier logs already held both cases;
  the sessions add the 43 mask-0 barricade tests. Refinement: only 153 and 258–263 take the ring with `0x01C0`; the frog
  demons go to `SpawnPosOnTile`.
- (c) **Row 8 rests on kept logs** too (Harrogath in `h4a … foothills` and `h5b … harro`), with a new `collision.py`
  counter of the cells only the `0x04` OR explains (1 044).
- (d) **The 334 d-none proposal** rests on a table check and a classification of 81 immediates (drlg/0005 § H5d lists
  every site). spawn 42 (H4b-counted) has the same remainder; whether it is raised whole with 334 d-none is the review's
  call.
- (e) **Row 46 in part:** every lookup met had one match, so the operand (`n`) is not separated; a level where a type
  has two or more matching points is not known.
- (f) **Rows 9 and 11 shortfall:** all 37 `TileCollisionUpdate` calls (all from 0x0066E91B in `Bit2TileMerge`) had the
  tile in no room reachable from the hint.
- (g) **Check mismatches not on these rows:** `monspawn` 3 in `collision-check.txt`: two "log ends" (the last request of
  tomb-r2 and jail, cut by `slots.py stop`) and one `objects.py` operate model mismatch on rogue (the town waypoint, class
  119, clicked a second time by `wpchain` while in mode 2; model mode 1, game 2). Whether the last needs an entry of its
  own is the review's call.
- (h) **Tools:** `collision.py`, `monspawn.py` (counters only; `collision.py check` on `collision-s1-2026-normal` is
  unchanged), `sweep_h5d.py` (new), `h5d_sessions.py` (the first tomb session ran with the `16defea` revision, named in
  the record). **Symbols** I → C (rule 14): `SpawnClassCellTest`, `CollisionTest`, `PATH_PatternFromSize`,
  `COLL_PatternMark`, `COLL_PatternUnmark`, `COLL_RectOrWH`, `LevelPointPick`; `MonIsNpc` stays I (its return is not
  logged). **Totals** against `main` `0e3f501` after merging it: static 567, harness 525, blocked 415 (d-none 289),
  deferred 2, raised 17: 1 526 (the one proposed move).

The H4b follow-ups entry (2026-10-16) is annotated with the H5d piece; it closes with this review. Spec-writer entry
filed: `2026-10-27-reverser-spec-writer-h5d-collision-raises-and-the-monisnpc-correction.md` (to be released with the
review). Not blocking.
