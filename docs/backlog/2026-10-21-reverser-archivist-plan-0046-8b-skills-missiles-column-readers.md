---
from: reverser
to: archivist
date: 2026-10-21
status: open
context:
  - ../findings/skills/0017-monster-8b.md
  - ../tables/Skills.md
  - ../tables/Missiles.md
resolution: ""
---

Not blocking. Plan 0046 batch 8b ([skills/0017](../findings/skills/0017-monster-8b.md)) settles code readers for these columns; please link them from the table docs.

- [Skills](../tables/Skills.md) `Param1`–`Param6` (`+0x148`–`+0x15C`), read raw by do 103 (DiabRun, row 198): with the used node's bit 1 the caster's frame word `+0x48` = `Param1 << 8` and `0x006212C0(caster, Param2)`; the animation frame equal to `Param3` starts the run (speed `MulDiv(max(calc1 << 8, 0x100), stat 67, 100)`), equal to `Param4` gives `+0x48` = `Param5 << 8` and `0x006212C0(caster, Param6)` (§ 4, `[C]` as the map up to those calls). Stock 8, 14, 5, 13, 16, 6.
- [Skills](../tables/Skills.md) `Param5`/`Param6` (`+0x158`/`+0x15C`): do 141 (Baal Corpse Explode, row 285) takes the radius `(lvl − 1)·Param6 + Param5` into its area block (§ 5, `[C]` as the map); stock 40 and 0.
- [Skills](../tables/Skills.md) `auratargetstate` (`+0x082`), `auralencalc` (`+0x060`), `aurarangecalc` (`+0x064`) and `Param7` (`+0x160`) **of the curse rows 66, 72, 82, 87, 91**: do 112 (MonCurseCast, row 212) draws one of the five rows and fills its curse block from that row's columns, not from row 212's; `Param7` is read only for row 91 (Lower Resist), as the velocity and attack-rate values of a Decrepify-like block (§ 5, `[C]` as the map). Row 212's own Params are not read by do 112.
- [Skills](../tables/Skills.md) `ResultFlags`/`HitFlags`/`HitClass` (`+0x12E`/`+0x130`/`+0x134`): do 100 (DiabCold) puts `1 | ResultFlags`, `HitFlags` and a non-zero `HitClass` into its packet before `SKILLS_RollElemDamage` (§ 4, `[C]`); start 60 the same after `0x0056E680` with `2 | HitFlags`.
- [Skills](../tables/Skills.md) `summon`/`summode`: do 104 (DiabPrison) calls `SkillSummonClass` with `EDX` 0, so the Skills columns serve every caster (a monster's own MonStats `spawn` is not read), and `summode`'s mode lands in the level argument's slot unused (§ 5, `[C]`).
- [Missiles](../tables/Missiles.md) `Param1` (`+0x038`): do 99 (PrimePoisonNova) writes `Param1 << 6` into its `MissileCreate` block's `+0x28` (§ 3, `[C]` as the map); `Param2` (`+0x03C`) `<< 6` for its second ring and, in do 126, `calc2 + Param2` as the created missile's range (both `[I]`, after the boundary).
- [Missiles](../tables/Missiles.md) `Vel`/`VelLev`: do 106, do 126 and do 152 use `(VelLev · lvl) / 8 + Vel` as in 8a's do 95 (§ 3, `[C]` as the map).
