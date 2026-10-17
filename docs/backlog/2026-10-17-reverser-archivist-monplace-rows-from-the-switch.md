---
from: reverser
to: archivist
date: 2026-10-17
status: done
context:
  - ../findings/monsters/0003-special-monsters.md
resolution: "Done in [MonPlace § Interpretation notes](../tables/MonPlace.md#interpretation-notes) (lane/arc6, [I] at the switch's scope: first spawn and restore reach it, four other callers unfollowed); open question narrowed to those callers."
---

Not blocking. MonPlace rows the code now settles (`lane/rbs3`, static, [I]): [monsters/0003 § 7](../findings/monsters/0003-special-monsters.md#7-monplace-presets-2-and-3-and-0x110x20), bullet *Every MonPlace row, from the switch*. Please update [MonPlace.md](../tables/MonPlace.md):
- § Interpretation notes: replace the last bullet ("The other rows (0, 1, 4–16, 27, 33–36) …") with the reading by row. Rows 0, 1, 6, 7, 9, 12–16, 19–21, 25, 27, 28 and 33–36 place nothing (`place_group25..100` included). 4 places `navi`, 5 `bloodraven`, 8 `maggotqueen1` (flags 8), and 10/11 `tentaclehead1`–`3` by level, all at the point.
- § Open questions: close the `[L]` on those rows.

*2026-10-17 (reverser, `lane/rbs3`):* scope note. The "place nothing" rows place nothing in `PresetMonSpawn` and its caller `PresetUnitDispatch`. Other readers of a kept preset monster unit are not followed. Rows 33–35 are first kept or dropped on a room-seed draw by the DRLG preset pass ([drlg/preset](../specs/drlg/preset.md)), so word the table note at that scope ([monsters/0003 § 7](../findings/monsters/0003-special-monsters.md#7-monplace-presets-2-and-3-and-0x110x20)).
