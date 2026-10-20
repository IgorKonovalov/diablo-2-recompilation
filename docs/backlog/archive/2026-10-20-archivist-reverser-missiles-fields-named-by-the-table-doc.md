---
from: archivist
to: reverser
date: 2026-10-20
status: done
context: []
resolution: "Done 2026-10-20 (lane/p45m): quests/0001's +0x96 open-question line annotated as Range (its second mention, in the final open-questions list, sits in a hunk main changed since; strike it at the merge); drlg/0005 points at Size and Collision; drlg/0008 names Param4; row 568's 64948 answered in [skills/0002 § 5](../../findings/skills/0002-missiles.md#5-the-hit)."
---

Not blocking. Plan 0045 Phase 0 documented the whole Missiles record ([Missiles](../../tables/Missiles.md), every column
placed, `excel_bin.py diff` 0 mismatches). Three findings name a Missiles field without a table doc; when the lane next
touches them (plan 0045 P1.2 or a sweep), please point them at the column:

- [quests/0001](../../findings/quests/0001-progression.md): the Horadric staff timer's `Missiles[338] +0x96` is `Range`
  (s16; row 338 `horadricstaff` holds 440); the finding's
  *Open questions* line "Missiles row 338 `+0x96` … column not identified" and the note near its line 2338 can close.
- [drlg/0005](../../findings/drlg/0005-collision.md): "Missiles (no table doc): `+0x18A` as the footprint size" is
  `Size`; `+0x184` is `Collision` (already named).
- [drlg/0008](../../findings/drlg/0008-outdoor.md) S4b row 3: Missiles `+0x44` is `Param4` (0, 38, 128 on three rows).

Also, from the same layout: row 568 `royalstrikechainlightning` stores server hit function 64 948 (`*12` in the
`.txt`); it is in plan 0045 Phase 1.2's scope, listed here only so the missiles batch sees it.
