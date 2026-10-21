---
from: reverser
to: archivist
date: 2026-10-20
status: open
context:
  - ../findings/skills/0008-sorceress.md
  - ../tables/Skills.md
  - ../tables/Missiles.md
resolution: ""
---

Not blocking. Plan 0046 batch `sor` ([skills/0008](../findings/skills/0008-sorceress.md)) settles code readers for
these columns; please link them from the table docs.

- [Skills](../tables/Skills.md) `startmana`: the row says a **player** is refused below `startmana · 256` unless in
  state 12 (`SKILLS_CanUse`); start 11 makes the same test for any caster type (§ 3, `[C]`).
- [Skills](../tables/Skills.md) `progressive` (`+0x04` bit 2): `sub_005D3CF0_SkillSrvMissileByCharge` picks
  `srvmissileb` for a charge of 2 and `srvmissilec` for 3 or more (the base `aurastat1` of the caster's `aurastate`
  list), else `srvmissilea` (§ 7, `[C]`, emulated in do 17 and 22).
- [Skills](../tables/Skills.md) `Param2`: do 21's stun chance out of 100 (Telekinesis 35; § 4, `[C]` up to the draw's
  flag); `Param7`: do 29's search radius (Thunder Storm 17; § 5, `[C]` as an argument); `Param1`/`Param2`: do 144's
  summon life `Param1 + (lvl − 1)·Param2` frames (§ 6, `[C]` as the block word).
- [Skills](../tables/Skills.md) `aurarangecalc`: start 12's range (`dx² + dy² ≤ r²`) and do 20's radius;
  `auralencalc`: the length passed to `STATE_ApplyTimed` by do 23, 25, 29; `aurastat1`: do 23/25 accept −1 (blank)
  to below the ItemStatCost count; `calc1`: do 17's bolt count, do 22's velocity term, do 26's count word, Inferno's
  `+0x4C`; `calc2`: a monster's Inferno length (§§ 3–8).
- [Skills](../tables/Skills.md) `summon`, `summode` (0..15, else 1), `pettype`, `petmax`: do 144's spawn block (§ 6);
  the three Hydra spawns are classes `summon`, `summon + 1`, `summon + 2` (`[I]` past the first).
- [Missiles](../tables/Missiles.md) `Vel`, `VelLev`: also read through the table at `0x0096C794` by `0x00663270` (do
  22's nova velocity, `VelLev · lvl / 8 + Vel`, § 7); `Size`: `COLL_WHTest`'s width and height in do 24 and 28.
