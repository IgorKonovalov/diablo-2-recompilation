---
from: reverser
to: archivist
date: 2026-11-03
status: open
context:
  - ../findings/path/0002-search.md
  - ../tables/PathTypes.md
  - ../tables/Objects.md
resolution: ""
---

path/0002 § 10: the record behind 0x00621A70 / 0x00621AC0 is the objects.bin record (SUnitCreate 0x005553D7-0x005553E2 stores OBJECTS_GetRecord(class); [I] reading), so +0x13A is IsDoor and +0x13C Orientation: PathTypes.md's and Objects.md's [L] on them can be raised to [I] with those anchors. Also from path/0002: under types 0 and 16 PathTypes can link the planner's meaning of path +0x92 (the search's last bound, § 6, [C]) and state that the search does not read +0x91 (§ 6, [C] by run:2026-11-03-path-emu-2).
