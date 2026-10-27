---
from: reverser
to: archivist
date: 2026-10-20
status: done
context:
  - ../../findings/skills/0005-missile-do-19-36-damage.md
  - ../../tables/Missiles.md
  - ../../tables/Skills.md
  - ../../tables/MonStats2.md
resolution: "Folded 2026-10-25 (plan 0051 P0a, lane/p51a): Missiles dParam1/2, EType, DmgCalc1, ProgOverlay, HitFlags/ResultFlags, Param1..5, SubMissile1..3; Skills ELen bands, Param1/2, calc4, aurarangecalc, aurafilter; MonStats2 small/large link skills/0005; do 28/34 at [C] (ADR-0021) as the 9b review raised them ([Missiles](../../tables/Missiles.md), [Skills](../../tables/Skills.md), [MonStats2](../../tables/MonStats2.md), [log](../../plans/done/0051-backlog-sweep-6.md#implementation-log))."
---

Plan 0046 batch 9b ([skills/0005](../../findings/skills/0005-missile-do-19-36-damage.md)) settles code readers for columns the table docs leave unexplained; please link them (the tags are the finding's: `[C]` for the damage functions, emulated on returning cases; `[I]` (ADR-0021) for the do functions up to their boundary; `[I]` readings otherwise).

- **Missiles `dParam1`/`dParam2`** (§§ 13–16): damage 2 freeze-length percent (`max(dParam1, 0)`); 3 the missile-pass chance out of 128; 5 the undead / demon bonus percents; 7, 9 the stun length (else a Skills value); 13 the undead percent (through 5); 14 the knockback mode (`dParam1` < 1, 1, ≥ 2 by MonStats2 `small`/`large`) and chance (`dParam2`). `[C]`.
- **Missiles `EType`** (`+0x0E4`): the element damage 1, 5, 12 and 13 roll or convert into (`sub_0064B0C0_MissileGetEType`, § 13), `[C]`; **`DmgCalc1`**: damage 1 and 12's conversion percent, capped at 100, `[C]`.
- **Missiles `ProgOverlay`**: damage 8 puts it on the hit unit (§ 14), do 29/33 on the owner after the heal (§ 11, `[I]`).
- **Missiles `HitFlags`/`ResultFlags`**: do 27 ORs them into its packet's flags and result before the area hit (§ 12, `[I]`).
- **Missiles `Param1`..`Param5`, `SubMissile2`/`3`**: do 28's window `Param3 < elapsed < Param4` and `Param5` into the creation block's `+0x24` (§ 7); do 34's sub-missile pairs `SubMissile1..3` with `Param2..4` (§ 8). `[I]` (ADR-0021).
- **Skills `ELen`, `ELevLen1..3`, `ELenCalc`** (`+0x214..+0x224`): `SKILLS_GetElemLen`'s level bands (§ 15), `[C]`; **`Param1`/`Param2`**: damage 7 `Param1 + (lvl − 1)·Param2`, damage 9 `Param2`, `[C]`; **`calc4`, `aurarangecalc`, `aurafilter`**: do 27 and do 28's period and radius (§§ 7, 12).
- **MonStats2 `small`, `large`** (`+0x005` bits 2, 3): read by damage 14 through `sub_004638A0_MonStats2FlagTest` (flags 10, 11), `[C]`.
