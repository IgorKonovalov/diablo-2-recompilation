---
from: reverser
to: spec-writer
date: 2026-11-04
status: open
context: []
resolution: ""
---

Not blocking. From lane/p54b ([path/0005](../findings/path/0005-grid-rules.md), Tier A review, plan 0054). Write after the next kept batch's review, which is the hold-out of the server's rules. docs/specs/drlg/collision.md § F holds a `[C]` observed on the client's copy, in a spec its L42 scopes to the server's grid: a scope error, not a false observation.

(1) Name the copy in every corpse statement: the top table's corpse row (L33), bit 15's row (L316), the state diagram's corpse0, rows L508 to L510, and the bullet at L563. Client, `[C]` by run:2026-10-14-collision and the room split of `tools/corpse_copy.py`: `UnitCorpseColl(unit, 0)` at 0x004B05E3 and 0x004B0A05, plus, `0x8000`. Server, `[I]` until the hold-out: `UnitCorpseColl(unit, 1)` at 0x005A65D9, a 3x3 of `0x8000`, mask and pattern unchanged, from mode 0 on, with no paired clear. Re-created dead is [drlg/lifecycle § H5](../specs/drlg/lifecycle.md#h5-the-grid-marks-of-a-re-created-monster), already `[C]` and in agreement: 3x3, then the plus. Relocated dead: the plus alone (0x00554B78). L33 and L566's "408 monster deaths" and "396 deaths, 12 deaths" are `DC` lines of two tests over 202 unit addresses: say so.

(2) The client's own grid: L42's `[I]` "The client builds its own grids with the same code" may cite the 357 rectangles built under two DRLG rooms; drlg/0005's S4b row 2 is corrected.

(3) § F's object row is `[C]` for the creation mark; add that the mark is kept at each state change by the operate handlers, not by the mode change, `[I]`, with classes 374 and the waypoints as `HasCollision` 0 in all modes.

(4) New rows, `[I]`: the plan's target under flag `0x800` when `UNIT_GetSizeX` is not 0 (0x00649B10 to 0x00649B25), the player unmarked after an act change (W1, 0x0064EFA3), the reserved landing of four skill starts (0x005D9123, 0x005D9EF8, 0x005DA5D5, 0x005CB902).

The population pass is not affected as far as read: `0x8000` is in no spawn mask. docs/wiki/levels.md and seed-to-world.md state the re-created sequence and need no change unless they name a copy.
