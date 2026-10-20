---
from: reverser
to: architect
date: 2026-10-20
status: open
context:
  - ../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../findings/objects/0001-object-population.md#plan-0038-batch-h5b-run2026-10-19-h5b-objects
  - ../findings/drlg/0005-collision.md#plan-0038-batch-h5b-run2026-10-19-h5b-objects
  - ../findings/objects/experiments.md#run2026-10-19-h5b-objects
resolution: ""
---

Review plan 0038 batch H5b (`objects`, `lane/h5b`, `main` not merged into the lane: the lane may not merge), run:2026-10-19-h5b-objects. 22 scripted sessions on slot 1 (2 on 2026-10-19, 20 on 2026-10-20), `tools/objects.py check`: **234 315 checks, 1 failure**, a logger error (the cave log's `LOGERR collision MemoryError`, no model mismatch); the 29 logs of run:2026-10-15-objects re-checked: 150 314 checks, 0 mismatches (150 338 before the nine monster-creating `InitFn`s of S4b row 25 became seed oracles). Manifest `workspace/logs/h5b-manifest.sha256` (85 lines, `sha256sum -c` from `workspace/logs/`).

Ledger of the 28 rows (33 statements): **raised 10** (collision 27, 39; objects 13, 16, 17, 40, 45, 50, 51, 52); **raised in part 11** (collision 37: `0x400` raised, `0x804` no stock door; objects 3 and 15: the `> roomCount ÷ 8` shrine cap, not `= 10` nor the well cap; 4: `OBJTRAP_ObjectCreate` modelled and reached, types 8/9 not; 23: `0x400` and the zero size raised, `0x804` no stock door; 26: `InitFn` 57 and 58 raised, 79 not; 27: 47 and 66 (and 25, 71 of S4b's list) reached, 54/55/62/68/69 not; 36: `interact` 3 seen, whole byte vs OR not separable; 38: the level-25 `SetMode(0)` reached, the "after a PreOperate" half has no stock class; 41 and 42: 26, 48 and 68 operated on one branch each, the casket after an item on both); **shortfall 7** (objects 6, 19, 20, 35, 39, 46, 49).

Points for the ruling:
- (a) **Proposed d-none**: objects 20 (no PopulateFn-2 member has `Orientation` 2; `OBJ_PlaceByOrientation`'s only call passes the member's), the `0x804` halves of collision 37 and objects 23 (the 7 `IsDoor` records without `BlocksVis` all have `BlockMissile` 0), row 38's PreOperate half (neither 371 nor any 581 class has `PreOperate`). All from `sweep_h5b.py static`; § 2.6 not edited.
- (b) **A grid-model fix inside the run**: `tools/collision.py` now puts a re-activated DRLG room's new active room in its old one's place in near lists (same level, DRLG room and rect, pointer not reused). It turned flayer3's one failure (game `0x0001`, model `0x27`) into a match, keeps the 29 older logs and run:2026-10-14-collision's 7 logs at 0 mismatches; two simpler fixes failed and were dropped (record). The game's unlink of a freed room was not read: drlg/0005 open question. Whether collision 27's raise may stand on 514 + 734 predicted cases with this fix in the model.
- (c) **Corrections**: objects/0001 § 13.6 said `OBJTRAP_ObjectCreate` makes 162 twice; the second is 160 (4 events, `[C]`). New reading: `OBJ_TrapEvent` remaps types 1, 3, 4 (below level 40; 3 not in level 25) and 8 (from level 75) to entry 2, `[I]` with the type-4 case `[C]`. The checker's theme rule now reads `g_ObjThemeFns`' enabled flag (theme 3 drawn 4 times, nothing ran).
- (d) Row 39's shortfall is the pilot's (the chest was created three times, never reached); row 6's is the arcane pads' (no room activated inside an operate).

Not blocking. Spec-writer entry filed: `2026-10-20-reverser-spec-writer-h5b-objects-spec-updates.md` (to be released with the review).
