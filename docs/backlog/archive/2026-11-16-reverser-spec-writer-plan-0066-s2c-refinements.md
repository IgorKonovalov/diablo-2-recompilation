---
from: reverser
to: spec-writer
date: 2026-11-16
status: done
context:
  - ../../plans/0066-simulation-inferred-claims-sweep.md
  - ../../plans/0066-inventory/skills-missiles.md
  - ../../findings/skills/0002-missiles.md
resolution: "Plan 0066 Phase 3, skills cluster (lane/n66sk): part 1 applied the missiles, catalogue and README items; part 2 the dispatch items: constants 22 (StateDo147Attached's state-114 lookup), C's durability path (the defender's, [I]), I4's 13 mastery callers, E1–E2's bit-6 writers and readers with the client-range counts, mode 14's start MonModeStartSeq clearing bit 6 (entry table, A2, E2, M1, note 6), I1's 0x005D8B10 in SkillDo75GrimWard's range, in [skills/dispatch](../../specs/skills/dispatch.md)."
---

Plan 0066 batch S2c (`lane/n66q`, part 1) found one correction and some refinements in the skills specs. They are for
Phase 3, when the specs are re-tagged. None of them blocks the re-tag of the raised rows. The anchors and counts are in
[skills/0002 § 15](../../findings/skills/0002-missiles.md#15-plan-0066-batch-s2c-part-1-second-tool-table-call-and-data-scans-2026-11-16-lanen66q)
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
- skills/dispatch E1 (rows 56–57; part 2 below corrects the owner of the clear: it is `sub_005A7870_MonModeStartSeq`, 0x005A7884, not `MonModeStartKnockback`): the bit-6 clear,
  and 44 of the 124 set sites and 7 of the 17 clear sites are in client-range functions.

**2026-11-16, S2c part 2 (`lane/n66q`).** More rewordings for Phase 3. The evidence is [skills/0002 § 16](../../findings/skills/0002-missiles.md#16-plan-0066-batch-s2c-part-2-bit-6-the-flag-bits-packets-and-the-creators-2026-11-16-lanen66q) and `check-s2c-p2.txt`.
- skills/dispatch E2, its reimplementation note and the entry table (rows 57 and 193, **contradicted in part**): the
  "AI sets bit 6, its mode start does not clear it, so the do runs only through the attack-frame handler and the
  `+0x4E` = 4 case" holds for modes 4, 5, 7, 8, 9 and 16–20 (`MonModeStartSkill`, frame `MonAttackFrame`). Mode 14's
  start `sub_005A7870_MonModeStartSeq` clears bit 6 (0x005A7884). Its frame `MonSeqFrame` then runs the do on a code 1
  or 2 with the bit clear, as the player frame does, and on `+0x4E` = 4 untested. skills/README § C and dispatch § M1
  need the same scope (S2a's backlog list).
- skills/missiles B2 (row 23, **contradicted in part**): "five monster functions (six sites)" should read six functions.
  The sites lie in six recursive-descent bodies: 0x005A2620, 0x005A2840, 0x005A2C20, 0x005A3F30, 0x005A6D50 and
  0x005A6FF0.
- skills/missiles D7 (row 48): mdo 31 (0x005B0325) also unmarks `0x40` (`COLL_SizeUnmark`). The writer of a `Collision`
  row's mark is `MissileCreate` setting the path's mark mask (0x0059FD54–0x0059FD64).
- skills/missiles reimplementation note "the weapon terms are frozen at creation" (row 94): `MISSILE_BuildDamage` reads
  only the missile, but two damage-table functions read the owner at the hit: mdmg 13 reads the owner's stat 25, and
  mdmg 11 reads the owner's elemental length (catalogue D8, D10). Scope the note to `BuildDamage`, or name both.
- skills/catalogue C3 (row 14): 93 calls of `MISSDATA_SetSeedLow` write `MissileData+0x28`, so do 10 is one writer of
  bit 0, not the only one.
- skills/catalogue J2 (row 58): Smite's closure reaches `SKILLS_SrvDo`'s set site through the durability path, the same
  path as dispatch row 42's.
- skills/dispatch I1 (row 88): 0x005D8B10 lies after `SkillDo75GrimWard`'s `ret`, inside that symbol's range.
