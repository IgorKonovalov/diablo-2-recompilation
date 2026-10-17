---
from: reverser
to: spec-writer
date: 2026-10-16
status: open
context:
  - ../specs/objects/README.md#h-draws-at-creation-per-initfn
  - ../findings/objects/0001-object-population.md#plan-0038-batch-s4b-2026-10-16
  - ../specs/drlg/preset.md#lvlprest-columns
  - ../specs/drlg/collision.md#e-collisiontest-by-size
  - ../specs/items/tc.md#j-object-drops-named-only
resolution: ""
---

[2026-10-16] from reverser → spec-writer: plan 0038 S4b corrections for Phase 3 (after the S4b review). (a) [objects § H](../specs/objects/README.md#h-draws-at-creation-per-initfn): the InitFn table misses the monster spawns of InitFn 18, 19, 25, 43, 49, 50, 52, 60 and 71 ([objects/0001 § Plan 0038 batch S4b](../findings/objects/0001-object-population.md#plan-0038-batch-s4b-2026-10-16)). (b) [drlg/preset LvlPrest columns](../specs/drlg/preset.md#lvlprest-columns): `Outdoors`' bit is read by `sub_0066BA70_RoomIsOutdoors`. (c) preset L439, L509 and L526: the bit-0x40 object marks are the waypoint bits of drlg/warps. (d) [drlg/collision § E](../specs/drlg/collision.md#e-collisiontest-by-size): the pool counts are 240 and 124 over the Levels `mon`/`nmon`/`umon` classes. (e) Restate the d-none parts named in the ledgers (the 40 cap, the LvlMaze fatal, DS1 path action below version 15). (f) [items/tc § J](../specs/items/tc.md#j-object-drops-named-only): the tier arithmetic and the `ilvl` hand-off are now `[C]` in items/0001 § 2 (entry (b) of the tc 64 item). **(e), room-tiles and drlg/README parts done 2026-10-16** (spec-writer, `lane/p38s`): the 40 cap (Constants, Reimplementation notes), the `Expansion` lookup and the `LvlSubRoll` halves restated as no-stock-case `[I]`. (a)–(d), (f) and the LvlMaze and DS1-action parts of (e) wait for their clusters. **(b), (c) and the LvlMaze and DS1-action parts of (e) done 2026-10-17** (spec-writer, `lane/p38s3`, plan 0038 Phase 3 round 3): preset § LvlPrest columns names `RoomIsOutdoors` as the `0x80000` reader (note 8); step 6 note 3, column note 5 and the Boundaries rows give the bit-0x40 marks to drlg/warps as waypoint bits; maze *Entry points* and preset step 1 note 5 state the LvlMaze fatal and `action` below version 15 as no-stock-case `[I]`. (a), (d) and (f) wait for their clusters.
