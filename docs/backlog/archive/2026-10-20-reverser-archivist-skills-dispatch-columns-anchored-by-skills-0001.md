---
from: reverser
to: archivist
date: 2026-10-20
status: done
context:
  - ../../findings/skills/0001-dispatch.md
  - ../../tables/Skills.md
resolution: "Done 2026-10-20 (archivist, lane/p46a, plan 0046 P0): the Skills dispatch and Columns meanings cite skills/0001's sections as [I] (start/do tables and bounds, costs, delay, start checks, item-cast columns, hit columns and calc1..4, SrcDam, Kick, anim 18), InGame's slot raised to [I]; MonStats SkillDamage from § 13 [../tables/Skills.md#dispatch-plan-0045-phase-0]"
---

Plan 0045 P1.1 anchored the meaning of several [Skills](../../tables/Skills.md) columns in code; Phase 0's § Dispatch can
link them as `[I]` instead of `[L]` (not blocking; Phase 0 is still to run):

- `srvstfunc` → `g_SkillStartFuncs` `0x00732140` (bound 0x5B), `srvdofunc`, `srvprgfunc1..3` and `ItemEffect` (> 1)
  → `g_SkillDoFuncs` `0x007322B0` (bound 0xBF); every stock value hits a non-null entry (skills/0001 Answer, `[C]`).
- `mana`, `lvlmana`, `manashift`, `minmana` (the cost formula and the payment-only floor), `startmana` (refused below it
  except in state 12), `delay` (state 121), `perdelay` (event 8 grid), `InTown`, `InGame`, `LineOfSight` (1..5 → five
  collision masks), `range` (`both` resolved by the weapon), `restrict` with `State1..3`, `usemanaondo`, `decquant`,
  `scroll`, `AttackNoMana` (falls back to Attack), `TargetableOnly`, `TargetCorpse`, `TargetAlly`, `TargetItem`,
  `ItemEffect`, `ItemTarget` (1..4), `ItemCheckStart`, `immediate`, `periodic`, `prgstack`, `lob`, `srvmissile`,
  `ResultFlags`, `HitFlags`, `HitClass`, `calc1..calc4` in the skill hit (`edPct`, flat damage, attack rate,
  conversion percent), `EType` (the conversion type), `SrcDam` (0 read as 128 by most builders), `Kick` (the
  `(str + dex − 20) / 4` physical), `anim`/`monanim` (the entry's mode), MonStats `SkillDamage`.
- The `.bin` byte `+0x188` is read as a byte (`manashift & 31`); `+0x18A`/`+0x18C` as s16.
Sections are named in each line's finding paragraph; the `PetType` and `Missiles` documents are untouched by P1.1.
