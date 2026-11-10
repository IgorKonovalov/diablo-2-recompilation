---
from: architect
to: reverser
date: 2026-11-04
status: dropped
context:
  - ../../plans/done/0054-path-search.md
  - ../../findings/path/0006-holdout.md
resolution: "Owner decision 2026-11-04: the grid-tie hold-out is dropped; the spec keeps its counted oracle and the shortfalls named in [path/0006](../../findings/path/0006-holdout.md); triage 2026-11-10."
---

Not blocking; from the lane/p54c review (plan 0054). The 11 wrong plans of path/0006 have candidate causes, [I], chosen after the result: 8 by drlg/collision § F1 (no bit is reference-counted, so the union of the present holders is not the grid) and 3 by 0x005CAF8E (class 194 in mode 14, outside corpse_mark's mode test). A rule for either needs a new revision of tools/path.py, frozen first, and a new kept run as its hold-out; the logger would need a line per ordinary mark and unmark to replay the order. The same run may take what is short: W1 (7 of 16 act changes, 3 of 9 in-act arrivals, floors 10; the hop stages need the waypoint's position, wpchain's fallback lay off the window in the River), PATH_CHAIN on classes 225 and 195 (22 and 3 of 50), server deadCol 1 for class 273, a break at the client's tests 0x004B05DB and 0x004B09FB, type 1's unstaged sites (state 13 with plan 0052's next batch, SkillDo103DiabRun, SwarmMove, a hireling left far behind), and town-follow. When it lands, the spec's counted oracle shrinks or goes; until then the spec states it.
