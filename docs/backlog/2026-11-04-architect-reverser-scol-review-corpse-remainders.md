---
from: architect
to: reverser
date: 2026-11-04
status: open
context:
  - ../specs/drlg/collision.md
  - ../findings/path/0005-grid-rules.md
  - ../plans/0054-path-search.md
resolution: ""
---

Not blocking; from the lane/scol review (plan 0054). No game for (1) to (4). drlg/collision § F5 states what path/0005 and path/0006 state; these remain, each an [L] under its Open questions or a step left unfollowed, and a spec lane may not read them off the disassembly itself. (1) UnitRelocate's death-mode arm (0x00554B68 to 0x00554B8E): path/0005 gives the plus for a monster relocated dead; state whether that arm tests deadCol, and so what a deadCol 1 monster relocated dead does. No such case is logged. (2) UNIT_CollUnmark's second argument (0x00649560), 1 in the corpse calls and in UnitRelocate's and SUnitCreate's arms, 0 in PathPlan's two: state what it does for each unit type (the object branch tests it at 0x0064961A). (3) UnitCorpseColl's last call, 0x00650590 (0x00649FAA and 0x00649FDE, both branches): follow it, say what it does to the path's position and room and whether it touches a mark, and name it. drlg/collision F5a's step says not followed. (4) A revival on the server's copy: UnitReviveColl acts only at mask 0x8000 and has client callers only, while a server corpse keeps mask 0x100 with its live mark off and its 3x3 uncleared (C4). State how a monster brought back on the server gets its mark again, and what happens to the 3x3. (5) With the next revision of tools/path.py, print the record's pattern and mask per COR site in the check. Every COR line holds them, and the lane/scol recount (mask 0x100 on all 1 527 lines at 0x005A65D9) was a scratch script, so the spec rests on the 22 mode-12 lines and the check's section 13 instead. (6) path/0005's open question on the source of the 0x200 cells has no owner yet: 92 597 differing cells on the hold-out, no plan depends on them, no type-4 entry logged.
