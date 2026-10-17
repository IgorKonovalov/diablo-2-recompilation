---
from: reverser
to: spec-writer
date: 2026-10-17
status: open
context:
  - ../findings/drlg/0009-room-lifecycle.md
resolution: ""
---

Not blocking; after the architect's review of `lane/rbs3`. New static readings ([I]) the specs may take:
- [drlg/0009 § 6 and § 11.1](../findings/drlg/0009-room-lifecycle.md#111-static-follow-ups-of-the-phase-2-review-lanerbs3). `SpecialMonRestore`'s `SpecialModsApply` pushes 0 for `minions`; the handlers run with flag 1 (0x005A214D, 0x005A21A6). § 6 used to read that 0 as the handler flag. `MinionRestore` passes flag 0 itself, so `rndname` takes no unit-seed step there. Every server write of the champion bit follows `MonMarkSpecial`. The path planner refuses a town target for a hostile monster (0x006483A0), with three routes left open.
- [monsters/0003 § 7](../findings/monsters/0003-special-monsters.md#7-monplace-presets-2-and-3-and-0x110x20), bullet *Every MonPlace row, from the switch*: the full `PresetMonSpawn` row table. `place_group25..100` place nothing in `PresetMonSpawn` even when the DRLG preset pass keeps them. Rows 4 (`navi`), 5 (`bloodraven`), 8 (`maggotqueen1`) and 10/11 (`tentaclehead1`–`3` by level) are placed at the point. [drlg/preset](../specs/drlg/preset.md)'s `place_group` rows may want a pointer.
- [monsters/0003 § S3b, special 43](../findings/monsters/0003-special-monsters.md#plan-0038-batch-s3b-2026-10-16): the save, the restore and the three-slot packet use of the mod list.
