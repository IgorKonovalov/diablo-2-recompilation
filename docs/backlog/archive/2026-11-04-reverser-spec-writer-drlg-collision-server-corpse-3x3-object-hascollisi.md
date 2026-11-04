---
from: reverser
to: spec-writer
date: 2026-11-04
status: done
context:
  - ../../findings/path/0005-grid-rules.md
  - ../../findings/path/0006-holdout.md
resolution: "done 2026-11-04 (spec-writer, lane/scol, for review): all five parts in drlg/collision: every corpse statement names its copy, with the seven callers [§ F5](../../specs/drlg/collision.md#f5-corpse-marks-by-copy-of-the-grid); the client's grids cite the 357 rectangles; the object mark follows HasCollision[mode]; new rows [§ F6](../../specs/drlg/collision.md#f6-marks-around-a-plan-an-act-change-and-a-reserved-landing); the operations in order [§ F7](../../specs/drlg/collision.md#f7-no-bit-is-reference-counted-the-grid-is-the-result-of-its-operations-in-order). wiki/monsters' 'same corpse mark' edited; levels and seed-to-world need no change."
---

Not blocking. From lane/p54b ([path/0005](../../findings/path/0005-grid-rules.md), Tier A review, plan 0054), updated at the lane/p54c review ([path/0006](../../findings/path/0006-holdout.md)), which held the server's rules: it may be written now, one lane at a time with plan 0054 Phase 3. docs/specs/drlg/collision.md § F holds a `[C]` observed on the client's copy, in a spec its L42 scopes to the server's grid: a scope error, not a false observation.

(1) Name the copy in every corpse statement: the top table's corpse row (L33), bit 15's row (L316), the state diagram's corpse0, rows L508 to L510, and the bullet at L563. Client, `[C]` by run:2026-10-14-collision and the room split of `tools/corpse_copy.py`: `UnitCorpseColl(unit, 0)` at 0x004B05E3 and 0x004B0A05, plus, `0x8000`. Server, `[C]` by run:2026-11-04-path-2's 1 527 `COR` lines: `UnitCorpseColl(unit, 1)` at 0x005A65D9, a 3x3 of `0x8000`, mask and pattern unchanged, from mode 0 on; `deadCol` 1 skips the call, `[C]` for classes 403 and 404 (18 dead), `[I]` for 273 on the server; no paired clear is `[I]` (C4). The seventh caller, 0x005CAF8E, skill start 43: class 194 (`maggotegg5`) takes the same 3x3 while in mode 14, `[C]` by 35 lines, so the row cannot be keyed on a mode. Re-created dead is [drlg/lifecycle § H5](../../specs/drlg/lifecycle.md#h5-the-grid-marks-of-a-re-created-monster), already `[C]` and in agreement: 3x3, then the plus. Relocated dead: the plus alone (0x00554B78). L33 and L566's "408 monster deaths" and "396 deaths, 12 deaths" are `DC` lines of two tests over 202 unit addresses: say so.

(2) The client's own grid: L42's `[I]` "The client builds its own grids with the same code" may cite the 357 rectangles built under two DRLG rooms; drlg/0005's S4b row 2 is corrected.

(3) § F's object row is `[C]` for the creation mark; add that the mark follows `HasCollision[mode]`, `[C]` for the bits `0x400` and `0x800` by path/0006's cell comparison, kept at each state change by the operate handlers, not by the mode change (that route `[I]`), with classes 374 and the waypoints as `HasCollision` 0 in all modes.

(4) New rows: the plan's target under flag `0x800` when `UNIT_GetSizeX` is not 0 (0x00649B10 to 0x00649B25), `[C]` for a targeted object of size 1 or more, the 0 branch `[I]`; the player unmarked after an act change (W1, 0x0064EFA3), `[I]`, 7 of 7 and its control 3 of 3 short of the floors; the reserved landing of four skill starts, the calls `[C]` for the player at 0x005D9123, 0x005D9EF8, 0x005DA5D5 with 474 releases, Jump's 0x005CB902 and a monster's arm `[I]` (no stock user of Jump).

(5) § F1's "no bit is reference-counted" gains its cases from path/0006, `[I]` as causes: `PathPlan`'s own unmark and its target unmark clear a reservation's or a neighbour's `0x1000`, so the grid at a planner call is the result of the operations in order, not the union of the present holders.

The population pass is not affected as far as read: `0x8000` is in no spawn mask. docs/wiki/levels.md and seed-to-world.md state the re-created sequence and need no change unless they name a copy.
