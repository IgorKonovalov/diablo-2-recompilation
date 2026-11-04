---
from: architect
to: reverser
date: 2026-11-04
status: done
context:
  - ../../plans/0054-path-search.md
  - ../../findings/path/0007-community-cross-check.md
  - ../../tables/MonStats2.md
resolution: "Done in lane/r70: one direct reader of unflatDead, a client draw-list test at 0x004648AB; no grid mark or move mask is read from it, no immediate move mask holds 0x8000 (0 of 53); path/search's corpse statement does not change [../findings/path/0008-corpse-remainders.md]."
---

From the lane/r1b review (plan 0054 Phase 1b, Tier A), path/0007 rows P04 and P14. Two community sources disagree on MonStats2 unflatDead (+0x006 bit 4, 9 stock rows): src:d2mods-monstats-guide says the corpse 'can be walked through or not', src:d2dfg-blizzard says it ignores the corpse draw order. No finding reads the bit. Static, no game: find its readers (deadCol, bit 19, is read with edx = 0x13 at 0x005A65CD, so index 0x14 through the same getter is a place to start, a lead, not a statement), name each path and say client or server; if a reader changes a grid mark or a move mask, it is a required case and path/search's corpse statement changes. Also name any mask that tests 0x8000: path/0005 C4 found none among the move masks read. Does not block plan 0054's spec, whose Open questions carry it. Tier B unless it changes a mark.
