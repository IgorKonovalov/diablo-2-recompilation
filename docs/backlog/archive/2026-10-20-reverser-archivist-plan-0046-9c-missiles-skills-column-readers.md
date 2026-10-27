---
from: reverser
to: archivist
date: 2026-10-20
status: done
context:
  - ../../findings/skills/0006-missile-hit-1-29.md
  - ../../tables/Missiles.md
  - ../../tables/Skills.md
resolution: "Folded 2026-10-25 (plan 0051 P0a, lane/p51a): Missiles HitSubMissile2..4 (the stride [L] replaced by hit 4's reader), sHitPar1/2, HitFlags/ResultFlags, SHitCalc1, EType; Skills TargetPet, auratargetstate, aurastate, aurafilter, Param1..6 link skills/0006; the radii of hits 14, 22, 24, 44 [I] (9c ruling 1) ([Missiles](../../tables/Missiles.md), [Skills](../../tables/Skills.md), [log](../../plans/0051-backlog-sweep-6.md#implementation-log))."
---

The request: what is needed, from whom, and why. Not blocking / blocking <what>.
Plan 0046 batch 9c ([skills/0006](../../findings/skills/0006-missile-hit-1-29.md)) settles code readers for hit-function columns; please link them in the table docs (tags are the finding's: `[C]` on returning cases, `[C]` (ADR-0021) up to the named boundary, `[I]` readings otherwise).

- **Missiles `HitSubMissile2..4`** (`+0x026`, `+0x028`, `+0x02A`): hit 4 reads all four words at stride 2 from `+0x024` and creates each that is > 0 (§ 7; the cases reach the creation at each slot, `[C]` (ADR-0021)). This is the code reader the "slot by stride `[L]`" note lacks; all four are blank in stock rows.
- **Missiles `sHitPar1`/`sHitPar2`** per hit function (§§ 3–15): the area radius (1, 9's disc, 13, 14, 20, 22, 24; hit 44 any non-zero value, negative included), hit 4's "hit the unit at once" switch, hit 7's heal switch (1) and target class (2: 0 any, 2 demons, else undead), hit 8's none, hit 12's search radius, hit 25's and 29's direction step, hit 26's range, hit 9's and 13's second value (radius, length), hit 20's and 22's bolt count. `[C]` up to the boundaries.
- **Missiles `HitFlags`/`ResultFlags`**: OR'ed into the area packet's `+0x00` (u32) and `+0x04` (u16) by hits 1, 9, 13 (`[C]` (ADR-0021), compared in the packet `AreaHitAt` receives) and 14, 24, 44 (`[I]`, after `BuildDamage`).
- **Missiles `SHitCalc1`**: hit 9's fire value for the disc of `HitSubMissile1` (§ 5, `[I]`).
- **Missiles `EType`**: also selects the length field hit 13 writes (`0x005A8F20`: 4 → `+0x30`, 5 → `+0x2C`, 9 → `+0x44`, 11 → `+0x18`, 12 → `+0x34`), `[C]` (ADR-0021).
- **Skills `TargetPet`** (`+0x007` bit 1): read by `sub_005542C0_SkillPetTest` for hit 7's heal (§ 6, `[C]`); today "behaviour flag (name reading)".
- **Skills `auratargetstate`** (`+0x082`): the state hits 16, 17, 19, 21 put or test (§§ 10–12); `aurastate` (`+0x080`) hit 18's (`[I]`); **`aurafilter`** (`+0x050`): hit 20's and 22's unit flags (0 → `0xA783` / `0xA683`), hit 21 only as set / not set (§§ 12–14).
- **Skills `Param1`..`Param6`**: hit 17's flee values `Param3 + (lvl−1)·Param4`, `Param5 + (lvl−1)·Param6` and its level margin `Param2`; hit 28's radius `Param1 + (lvl−1)·Param2` and flat `Param5`, `Param6` (§ 11, `[C]` (ADR-0021)).
