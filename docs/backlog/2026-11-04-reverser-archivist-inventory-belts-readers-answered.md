---
from: reverser
to: archivist
date: 2026-11-04
status: open
context:
  - ../findings/items/0013-grids-belts-stacks.md
resolution: ""
---

Plan 0060 P1.2 answers the Open questions of docs/tables/Belts.md and docs/tables/Inventory.md, for the archivist to link (items/0013 § 4, run:2026-11-04-inventory-emu). Row for a unit and page: sub_00621050_InvRowForUnit (player page 1 -> 6, 2 -> 7, 3 -> 9, 4 -> 12 in an expansion game else 8, otherwise the class row; monster 5; object classes 0x152, 0x153 -> 10, 11; else -1). Second sets: server calls pass a literal set of 0; only 0x4xxxxx callers vary it. gridX, gridY: read as bytes. Hireling rows 13, 29 are not returned by the row function. Belts row: the worn item's Items +0x130, or 2 with no belt (0x0063C6A3, 0x0056091B); numboxes +0x004. Rectangles: 0x0065C180, 0x0065C270, 0x00660D10 have client callers only by direct call. Misc: autobelt gates only the belt search's second pass (0x0063C731).
