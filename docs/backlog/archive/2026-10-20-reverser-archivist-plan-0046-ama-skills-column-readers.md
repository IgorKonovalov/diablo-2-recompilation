---
from: reverser
to: archivist
date: 2026-10-20
status: done
context:
  - ../../findings/skills/0009-amazon.md
  - ../../tables/Skills.md
  - ../../tables/MonStats2.md
resolution: "Folded 2026-10-25 (plan 0051 P0a, lane/p51a): Skills ToHit map, calc1..3, the aura block, srvmissileb (word 0 only), the summon words; MonStats2 MeleeRng link skills/0009, value [C] and meaning [I] as the ama review left them ([Skills](../../tables/Skills.md), [MonStats2](../../tables/MonStats2.md), [log](../../plans/0051-backlog-sweep-6.md#implementation-log))."
---

Not blocking. Plan 0046 batch `ama` ([skills/0009](../../findings/skills/0009-amazon.md)) settles code readers for
these columns; please link them from the table docs.

- [Skills](../../tables/Skills.md) `ToHit`, `LevToHit`, `ToHitCalc`: `SKILLS_GetToHit` gives 0 for `lvl ≤ 0`,
  `(lvl − 1)·LevToHit + ToHit` (32-bit) when `ToHitCalc` is blank, else the calc (§ 4, `[C]`, emulated in start 7 and
  do 7); start 6 and start 10 do not pass it to the hit test (§ 4).
- [Skills](../../tables/Skills.md) `calc1`, `calc2`, `calc3` for do 8: `calc1` the fan size `n` (the start point and
  the first group's flags `[C]`; that `n` missiles are created in all is `[I]`, past the first creation), `calc3` the
  centre group (`n` when 0), `calc2` the creation block's `+0x44` (§ 6, `[C]` for the first creation; its meaning to
  the missile `[I]`); do 10: `calc1` the creation callback's value, added to the missile's stat 25 (`[I]` past the
  call).
- [Skills](../../tables/Skills.md) `auratargetstate`, `aurastat1`, `aurastatcalc1`, `auralencalc`, `aurarangecalc`,
  `aurafilter` for do 6: the block `{id, lvl, auralencalc, auratargetstate, aurastat1, aurastatcalc1}` and the
  search radius and filter; a blank `aurastat1` (−1) refuses (§ 5, `[C]`).
- [Skills](../../tables/Skills.md) `aurarangecalc`: start 8's and do 12's search radius (§§ 3, 7, `[C]` as the value
  passed; its use as a radius is the callee's, `[I]`).
- [Skills](../../tables/Skills.md) `srvmissileb`: do 8 and 10 take it (when ≥ 0) when the caster's weapon word is not 1,
  which a caster with no inventory gives (§ 6; `[C]` for that case only).
- [Skills](../../tables/Skills.md) `summon`, `pettype` (0 when at or past the PetType count), `summode`, `petmax` for do
  15 and 16 (§ 8, `[C]` as block words); do 16 refuses a caster that is not a player.
- [MonStats2](../../tables/MonStats2.md) `MeleeRng` (`+0x00E`, the byte `0x00622870` reads through MonStats `MonStatsEx`): a monster's melee
  reach, plus 4 the search radius of start 9 and do 13; `0xFF` sends it to `0x0064F380` (§ 3, `[C]` as a map; the
  column's name is the table doc's).
