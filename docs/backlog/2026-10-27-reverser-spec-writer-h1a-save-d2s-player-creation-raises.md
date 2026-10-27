---
from: reverser
to: spec-writer
date: 2026-10-27
status: open
context:
  - ../findings/save/0001-d2s-io.md#plan-0038-batch-h1a-run2026-10-27-sweep-d2s-load
  - ../findings/player/0001-creation.md#plan-0038-batch-h1a-run2026-10-27-sweep-d2s-load
resolution: ""
---

Held until the lane/h1a review accepts plan 0038 batch H1a. Then: re-tag the save/d2s, hirelings and player/creation statements the batch raised (the ledger in inventory § 2.6, H1a block), and carry the new readings into the spec: (a) D2S_ReadSave's own 9 (fewer than 8 bytes, bad magic) is returned unmapped, not through the failure exit; (b) PLRSAVE_ReadFile reads at most 0x2000 bytes, so a longer file is read truncated (a valid 8 192-byte prefix loads); (c) a waypoint record with marker 0 or 0x0101 is zeroed including the marker, and WAYPOINT_Save stores 0x0102 back before copying; the marker test of the section reader (16) comes before WAYPOINT_Load's own fatal test; (d) a set id with no SetItems record drops that item (the unit is freed) and the load goes on; (e) a unique id at or above the count is read as -1 and written as 0xFFF; (f) for a version <= 95, ITEMS_ReadFull reads stat 72 (current durability) in 8 bits; (g) the stat-slot count 0x29 bounds the old stat form (a count of 12 leaves stat 12 unset, header level 0 written); (h) a class-7 character never loads: a class-7 full save and a class-7 stub pass the header and halt at sub_00553180's null-unit test (line 1210); player-creation 20 and 34 are proposed d-none; (i) the character screen lists only files that pass 0x0043C8A0's tests, so codes 9 and 7 (version) are not reachable from the screen without a file changed after the list was read.
