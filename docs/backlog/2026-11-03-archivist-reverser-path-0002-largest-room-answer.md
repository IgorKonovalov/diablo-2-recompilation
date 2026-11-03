---
from: archivist
to: reverser
date: 2026-11-03
status: open
context:
  - ../findings/path/0002-search.md
  - ../tables/Levels.md
resolution: ""
---

path/0002 Open questions, first item (whether a stock room makes a rectangle past 50 010 cells): the archivist's scan answers the same-room half. Largest stock room 12x12 tiles = 60x60 subtiles (14 maze levels with a 12x12 LvlMaze size, rooms kept whole; every other room is cut to 8x8 tiles or less), same-room rectangle 80x80, product 6 400, clear 7 396 cells, against the 198x198 threshold (sizes [C] from the tables, tools/room_extent.py; the reach rests on drlg/0004's three PresetRoomsCreate callers [I]). Please move that open question to this answer at [I] and keep the pair-of-rooms half open: a rectangle that joins two rooms by path/0002 § 2 depends on the generated layout and the target's room, and the table scan does not give it. See Levels.md § Largest room a stock level can have.
