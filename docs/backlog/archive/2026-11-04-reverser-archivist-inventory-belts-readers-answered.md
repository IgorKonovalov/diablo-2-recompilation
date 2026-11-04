---
from: reverser
to: archivist
date: 2026-11-04
status: done
context:
  - ../../findings/items/0013-grids-belts-stacks.md
resolution: "Belts and Inventory take items/0013 § 4 at its tags: the row function as a table, the stash sizes, gridX/gridY bytes, the worn belt's row, the second sets and the rectangle readers (direct calls, [I]), hireling rows 13 and 29; Misc autobelt [Inventory](../../tables/Inventory.md), [Belts](../../tables/Belts.md), [Misc](../../tables/Misc.md)"
---

Plan 0060 P1.2 answers the Open questions of docs/tables/Belts.md and docs/tables/Inventory.md, for the archivist to link (items/0013 § 4, run:2026-11-04-inventory-emu). Row for a unit and page: sub_00621050_InvRowForUnit (player page 1 -> 6, 2 -> 7, 3 -> 9, 4 -> 12 in an expansion game else 8, otherwise the class row; monster 5; object classes 0x152, 0x153 -> 10, 11; else -1). Second sets: server calls pass a literal set of 0; only 0x4xxxxx callers vary it. gridX, gridY: read as bytes. Hireling rows 13, 29 are not returned by the row function. Belts row: the worn item's Items +0x130, or 2 with no belt (0x0063C6A3, 0x0056091B); numboxes +0x004. Rectangles: 0x0065C180, 0x0065C270, 0x00660D10 have client callers only by direct call. Misc: autobelt gates only the belt search's second pass (0x0063C731).

Tags and scope (check fix): the row function, the second-set literal-0 calls and the byte reads of `gridX`/`gridY` are `[C]` as maps of the code (ADR-0015, items/0013 § 4) except the survey of callers, which is `[I]` over direct calls. The rectangle readers' "client callers only" is by direct call; table pointers to `0x0065C140` and `0x00660C70` (0 direct calls) are unfollowed. The hireling rows 13 and 29 not being returned is `[I]`. Cell-level table statements will be reviewed Tier A (ADR-0027).
