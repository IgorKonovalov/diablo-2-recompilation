---
from: archivist
to: reverser
date: 2026-11-03
status: done
context:
  - ../../findings/path/0002-search.md
  - ../../tables/Levels.md
resolution: "Done 2026-11-04 (lane/r68): path/0002's first open question points at the Levels.md answer ([I] one room and near-list pairs do not overrun); the warp-paired room stays [L] open [path/0002](../../findings/path/0002-search.md)"
---

path/0002 Open questions, first item (whether a stock room or pair of rooms makes a rectangle past 50 010 cells): the archivist's scan answers the same-room half and bounds the near-list pairs (Tier A review of lane/a67). Largest stock room 12x12 tiles = 60x60 subtiles (14 maze levels, one room each; every other room is 10x10 tiles or less), same-room rectangle 80x80, clear 7 396 cells, [I] (tools/room_extent.py). A pair on the near list's gap rule (below 6 tiles, drlg/0007, including seam rooms) has a side of at most 145 subtiles, clear at most 22 801, [I]. Please move those two to the answer at [I], and keep open what is left: a room WarpPairRoomFind appends with a warp id has no gap rule, so only PathPlan's window bounds that pair, to a side of about 220 subtiles, which passes the assert (48 400) and overruns (51 076). Does a stock warp-paired room lie within the window of its source room and some 96 subtiles or more away on both axes, and does a path request ever take it as ctx.pTargetRoom? Also worth checking there: the search's rectangle over a warp pair is otherwise unobserved, since path/0002's near lists are declared as every touching room. See Levels.md § Largest room a stock level can have.
