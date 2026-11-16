---
from: reverser
to: spec-writer
date: 2026-11-16
status: open
context: [../plans/0066-simulation-inferred-claims-sweep.md, ../plans/0066-inventory/skills-missiles.md, ../findings/skills/0002-missiles.md]
resolution: ""
---

Plan 0066 batch S2c (`lane/n66q`, part 1) found one correction and some refinements in the skills specs. They are for
Phase 3, when the specs are re-tagged. None of them blocks the re-tag of the raised rows. The anchors and counts are in
[skills/0002 § 15](../findings/skills/0002-missiles.md#15-plan-0066-batch-s2c-part-1-second-tool-table-call-and-data-scans-2026-11-16-lanen66q)
and `workspace/logs/n66q/s2c/check-s2c-p1.txt`.

- **Correction, skills/missiles entry-points table (inventory row 2):** "A missile is created at a point (quests,
  shrines, missiles, some skills)". `sub_0056EDE0_MissileCreateAt` has 17 callers: 3 quest functions, 7 missile
  functions, 5 skill functions and 2 monster AI functions (`AiUseSkillNearSelf`, `AiBladeCreeper`). No shrine function
  calls it; the shrines create through the other creators (missiles B5). Reword the list as quests, missiles, some
  skills and two monster AIs.
- skills/catalogue C0 (row 10): besides mdo 20, 30, 32 and 34, the 9b entries 19, 21–29, 31, 33, 35 and 36 also end in
  mdo 1. Do-table entry 37 (`0x005B0AA0`, inside the BaalFx function's range) is non-null, and no Missiles row names it.
- skills/catalogue `g_Circle64X/Y` (row 3): the points are trunc(30·cos, 30·sin) of i/64 turns, so their radius runs
  from 28.84 to 30.
- skills/catalogue O8 (row 87): sandmaggot6 and sandmaggot7 also spawn (`maggotegg6`, S1).
- skills/dispatch constants (row 22): `sub_005D2B20_StateDo147Attached` also looks up state 114's stat list.
- skills/dispatch I4 (row 98): `SKILLS_GetMasteryBonus` is also called by `COMBAT_RollPhysical`, `MissileCritRoll`,
  `AttackRatingCalc` (0x00583740) and `AiBladeCreeper`.
- skills/dispatch C (row 42): the raise is scoped to the direct callers. A direct-call closure from the monster mode
  functions reaches `SKILLS_CanUse` through the defender's durability path (MonAttackFrame → DeliverQueued → durability
  loss → HandsRefresh → PlrModeStartSkillUnit). The spec should say so, or scope the line to the attacker.
- skills/dispatch E1 (rows 56–57, part 2 of S2c will settle them): `sub_005A77C0_MonModeStartKnockback` clears bit 6,
  and 44 of the 124 set sites and 7 of the 17 clear sites are in client-range functions.
