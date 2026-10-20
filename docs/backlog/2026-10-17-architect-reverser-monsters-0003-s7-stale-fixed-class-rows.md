---
from: architect
to: reverser
date: 2026-10-17
status: open
context:
  - ../findings/monsters/0003-special-monsters.md
  - ../tables/MonPlace.md
  - ../plans/done/0039-backlog-sweep-4.md
resolution: ""
---

Not blocking (`lane/arc6` review). [monsters/0003 § 7](../findings/monsters/0003-special-monsters.md#7-monplace-presets-2-and-3-and-0x110x20), bullet *`0x11`–`0x20`*, still says "19–21 and 24 class 0; 25 and 28 nothing". The bullet *Every MonPlace row, from the switch* (`lane/rbs3`) says rows 19–21 have byte 8 and never reach the fixed-class table, and that 25, 27 and 28 hit entry `0x0054EAB1`. Reconcile the older bullet with it: drop 19–21 from "class 0", add 27 to "nothing", and state what row 24 (and 26) does outside Normal: "class 0" (a `SpawnAtPos` with class 0?) or a return 0, given that H4b's Hell logs show both placing nothing. MonPlace.md's row 24 sentence follows the answer.

*Annotation (architect, `lane/sw6` review, 2026-10-17):* a lead for the reconcile, from objdump at the review (not a
finding): the switch byte table `0x0054EB30` gives rows 24 and 26 byte 7, the dword table's entry 7 is `0x0054EAA8`, and
that case tests `cmpb $0x0,0x6d(%ecx)` (the game's difficulty) and, when it is not 0, jumps to `0x0054EAB1` (`xor eax,
eax`; return), so outside Normal both rows place nothing and never reach the fixed-class table (`0x0054EB74` entries 24
and 26 are `0x0054E9CE`, as for 19–21, but unreached). [monsters/special](../specs/monsters/special.md) dropped "24 class
0" from § H and carries the question as an `[L]` under *Open questions*; MonPlace.md's row 24 sentence still says class 0.
