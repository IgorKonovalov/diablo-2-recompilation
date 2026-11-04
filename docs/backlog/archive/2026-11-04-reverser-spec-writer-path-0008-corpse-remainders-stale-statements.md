---
from: reverser
to: spec-writer
date: 2026-11-04
status: done
context:
  - ../../findings/path/0008-corpse-remainders.md
  - ../../specs/drlg/collision.md
resolution: "Taken into drlg/collision F5a and F5 (relocated dead, UNIT_CollUnmark's second argument, the revival, the immediate masks, all [I], with the not-followed routes) and path/overview F4's C4, its notes and open questions: [drlg/collision](../../specs/drlg/collision.md#f5-corpse-marks-by-copy-of-the-grid), [path/overview](../../specs/path/README.md#f4-each-grid-rule-at-its-tag). path/search's corpse statement is unchanged, as item (4) says."
---

From lane/r70 (path/0008, all [I], no game). (1) drlg/collision F5a says UnitCorpseColl's last call (0x00650590) is not followed: it is followed, it snaps the path point to its tile's middle and marks nothing (path/0008 item 3). (2) The F5 statement that a monster relocated dead takes the plus: add that UnitRelocate's arm tests the dead mode only, not deadCol (item 1), and the second argument of UNIT_CollUnmark (item 2, including its 0 at PathPlan's two calls and the line-test helper's two). (3) The Open question on how a revived monster gets its mark on the server: MonReviveInPlace re-marks (item 4); the 3x3 stays; MonSetMode is not given as a route. (4) path/search's corpse statement does not change: unflatDead is a client draw-list test only (item 6, path/0007 P04 and P14 updated). Not blocking.
