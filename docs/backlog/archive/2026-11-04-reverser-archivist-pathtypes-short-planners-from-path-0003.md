---
from: reverser
to: archivist
date: 2026-11-04
status: done
context:
  - ../../findings/path/0003-short-planners.md
  - ../../tables/PathTypes.md
resolution: "PathTypes names slots 3, 11, 12 and takes path/0003 at its tags (0x100 and 0x200 scoped to its planners, +0x98 read by greedy and rewritten by type 12; 0x400 and 0x20000 stay [L], the finding does not name them); Missiles Range and row 195 noted [PathTypes](../../tables/PathTypes.md), [Missiles](../../tables/Missiles.md)"
---

[PathTypes](../../tables/PathTypes.md) can name the last planners and take the planners' uses from [path/0003](../../findings/path/0003-short-planners.md), after this batch's review: `sub_00679E50_PathPlanType3`, `sub_00679FD0_PathPlanType11` and `sub_00679E60_PathPlanType12` for slots 3, 11 and 12; `g_PathTypeParam98` read only by greedy's `+0x98` walk and rewritten by type 12; the flags `0x100`, `0x400`, `0x20000` read by no planner (only `0x200`, through `PathAimNextPoint`); [Missiles](../../tables/Missiles.md): `Range` sets the type-10 walk's draws for the callback rows, and row 195's `[L]` line can note class 195's 176 logged creations (who creates it stays unread). Not blocking.
