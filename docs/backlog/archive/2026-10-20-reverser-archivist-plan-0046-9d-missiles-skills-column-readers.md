---
from: reverser
to: archivist
date: 2026-10-20
status: done
context:
  - ../../findings/skills/0007-missile-hit-31-59.md
  - ../../tables/Skills.md
  - ../../tables/Missiles.md
resolution: "Folded 2026-10-25 (plan 0051 P0a, lane/p51a): Skills Kick (max divides by 3), the physical and elemental length maps; Missiles sHitPar1..3, Param4, CollideKill, pSrvHitFunc; MonStats2 large link skills/0007 (ring steps of hits 52/59 and the CollideKill returns [I], as the finding) ([Missiles](../../tables/Missiles.md), [Skills](../../tables/Skills.md), [MonStats2](../../tables/MonStats2.md), [log](../../plans/0051-backlog-sweep-6.md#implementation-log))."
---

Not blocking. Plan 0046 batch 9d ([skills/0007](../../findings/skills/0007-missile-hit-31-59.md)) settles code readers
for these columns; please link them from the table docs.

- [Skills](../../tables/Skills.md) `Kick`: the row says `/ 4 << 8` for minimum and maximum; `SKILLS_GetPhysMin` divides
  by 4, `SKILLS_GetPhysMax` calls `sub_00644C20_SkillKickDamage` with flag 0, which divides by 3 (skills/0007 § 3,
  `[I]`; the minimum `[C]`).
- [Skills](../../tables/Skills.md) `MinDam`/`MaxDam`, `MinLevDam1..5`/`MaxLevDam1..5`, `DmgSymPerCalc`, `HitShift`,
  `SrcDam`: the physical damage map of `SKILLS_GetPhysMin/Max` (§ 3, `[C]`, emulated inside hit 43).
- [Skills](../../tables/Skills.md) `ELen`, `ELevLen1..3`, `ELenSymPerCalc`: `SKILLS_GetElemLen`'s map (§ 8, `[C]`,
  emulated inside hit 53).
- [Missiles](../../tables/Missiles.md) `sHitPar1`: hit 38/40 `(lvl−1)·sHitPar2 + sHitPar1` creations (n ≥ 41 asserts),
  hit 45 the count, hit 50 frames before the range end, hit 52 and 25 the direction step, hit 55 the mana percent
  (clamped 1..100), hit 58 the scatter radius, hit 59 the ring step; `sHitPar2` hit 38/40 the per-level count, hit 45
  the callback switch; `sHitPar3` hit 2's ring loops; `Param4` hit 32's portal argument (cairnstones 38); `CollideKill`
  hits 31 and 43's return value (§§ 3–9).
- [Missiles](../../tables/Missiles.md) `pSrvHitFunc`: values above 0x7FFF read as negative and skip the hit function
  (row 568's 64 948, § 10, `[I]`).
- [MonStats2](../../tables/MonStats2.md) `large`: read by hit 47 (molten boulder explodes only on `large` monsters, § 8,
  `[C]`).
