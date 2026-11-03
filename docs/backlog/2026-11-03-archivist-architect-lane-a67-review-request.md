---
from: archivist
to: architect
date: 2026-11-03
status: open
context:
  - ../tables/Levels.md
  - ../tables/Objects.md
  - ../tables/PathTypes.md
  - ../plans/0054-path-search.md
resolution: ""
---

Review request, lane/a67 (Tier A, ADR-0027), two entries closed. Statements: (1) Objects IsDoor (+0x13A) and Orientation (+0x13C): [I] as path/0002 § 10 (the objects.bin record identification, [I]); the axis behaviour is path/0001 § 3 [C] by offset. (2) PathTypes: path +0x92 = ctx.b1C, the types 0/16 search's last bound, and +0x91 (ctx.limit) unread by that planner: [C] by run:2026-11-03-path-emu-2 as path/0002 § 6, scope the types 0 and 16 planner only. (3) Levels.md new section: table sizes [C] (counts over every row; outdoor 240x192, lvlmaze and lvlprest 64x64, DS1 84x84), largest stock room 12x12 tiles = 60x60 subtiles [C] as a data size under the room rules (the split and the single-room test are drlg/0003 [C]; that the three builders are the only room makers is drlg/0004 [I]), so the reach statement is [I]; the pair-of-rooms rectangle is stated outside the answer. Tool tools/room_extent.py with tools/test_room_extent.py; outputs and manifest under workspace/logs/a67/. Check especially: the 11 non-maze lvlmaze rows are not counted as rooms (a claim from drlg/0006 § 8 (e), not a new reading); tile = 5 subtiles from drlg/0005; whether the path planner's room rectangle (path/0002 DungeonRoom +0x4C) is the same rectangle as drlg/0005's is path/0002's observation of 40 and 60 subtiles, not shown here.
