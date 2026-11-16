---
from: reverser
to: spec-writer
date: 2026-11-15
status: open
context:
  - ../plans/0066-simulation-inferred-claims-sweep.md
  - ../findings/anim/experiments.md
resolution: ""
---

Plan 0066 batch S6c (`lane/n66l`, 2026-11-15) corrections for Phase 3 in specs/anim (lines at `b5999f5e`, match by
text). Record: findings/anim/experiments.md, the "plan 0066 batch S6c" static addendum; `workspace/logs/n66l/s6c/check.txt`.
Not blocking.

1. **Contradicted in part**, timing § I2's table, row "3, 6 — GH, BL" (line 532): the *Frame function* cell says "—",
   but both records' frame slot is 0x005A6DE0 (`sub_005A6DE0_MonFrameCancelEvents`, `UNIT_CancelEvents(0, 0)`), the
   same function as NU's (r2 = raw bytes = the kept `MMODE` lines, `mon-mode-records`). Both modes are scheduled
   (`schedule` 1), so the slot runs at a frame event of their record. findings/anim/0001's own table already shows it.
2. **Refinement**, the same table: S4's (row 11) and DD's (row 12) frame slot is also 0x005A6DE0 (never queued:
   `schedule` 0), and S3's end slot is 0x005A74D0, a bare `ret`, where the table prints "—" (lines 534, 535).
3. **Refinement**, timing § I2 `MonSetMode` sentence (line 541): between `SUNIT_AnimInit` and the cancels the code also
   calls `MonModeVelocity` (0x005A7DBF; movement A3 names it) and `UNIT_SetUsedSkill(unit, 0)` again (0x005A7DDE).
4. **Refinement**, timing § I2 *Class overrides* (line 546): the switch's ten classes all set `SplGetModeChart`, and ten
   more stock rows set it with no case (404, 546–550, 559, 571–573), so "all ten classes" reads as "the ten the switch
   names"; the switch runs only when MonStats `+0x1A5` is non-zero (0x005A78EF).
5. **Refinement**, movement § A4 (line 131): `MonStatsSpeeds`' out-of-range `BaseId` case also writes `i` back into the
   row's `BaseId` (0x00650F37); no stock row reaches it (734 rows).
6. **Refinement**, README § A, mode end (line 90): `PlayerModeEnd`'s draws lie below `PlayerModeAllowed`,
   `PlrModeStartNeutral`, `PlayerDeathModeEnd` and `sub_00580310_HandsRefresh`; "the next start's, PlayerModeAllowed's,
   the AI's" does not name the hands refresh's (118 draw functions below it under the modes scan's stops).
