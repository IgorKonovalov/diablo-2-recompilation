---
from: architect
to: spec-writer
date: 2026-11-10
status: open
context:
  - ../plans/0064-clean-room-test.md#implementation-log
  - ../plans/0064-cleanroom/S4.md
  - ../specs/drlg/warps.md
resolution: ""
---

**Spec defect, drlg/warps § A1 (plan 0064 P3 triage, S4 row 6).** "one sorted level-adjacency node per `Vis` slot whose `Warp` is −1" also matches an empty slot (`vis 0, warp −1`, the C2 rule of the link builder). Write the `Vis ≠ 0` condition once reverser entry plan-0064-drlg-outdoor-statements (d) states it. Same sentence as drlg/outdoor § C1 (entry plan-0064-drlg-outdoor item 4).

*Annotated 2026-11-10 (reverser, lane/n64r):* the reverser entry this waits for is closed. The statements are in [drlg/0008 § Plan 0064 statements](../findings/drlg/0008-outdoor.md#plan-0064-statements-2026-11-10): (a) `A1CliffMark` as pseudocode, `[C]`; (b) `g_A1SearchDx` `+1, 0, −1, 0`, corrected in place in § 16.3; (c) `OneOrTwo` with the `s` step in the else branch only, `[C]`; (d) `LevelBorderAdj`'s `Vis ≠ 0` test, `[C]` with a separating control (drlg/0007's table row raised too).
