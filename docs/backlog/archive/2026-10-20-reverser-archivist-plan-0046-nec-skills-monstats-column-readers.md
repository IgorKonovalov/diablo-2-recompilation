---
from: reverser
to: archivist
date: 2026-10-20
status: done
context:
  - ../../findings/skills/0010-necromancer.md
  - ../../tables/Skills.md
  - ../../tables/MonStats2.md
  - ../../tables/DifficultyLevels.md
  - ../../tables/MonStats.md
  - ../../tables/States.md
resolution: "Folded 2026-10-25 (plan 0051 P0a, lane/p51a): Skills aura and summon words, srvmissilea; MonStats2 corpseSel, revive; MonStats Velocity; DifficultyLevels AiCurseDivisor (DiffDivide, the other three readers still unread); States udead link skills/0010 ([Skills](../../tables/Skills.md), [MonStats2](../../tables/MonStats2.md), [MonStats](../../tables/MonStats.md), [DifficultyLevels](../../tables/DifficultyLevels.md), [States](../../tables/States.md), [log](../../plans/0051-backlog-sweep-6.md#implementation-log))."
---

Not blocking. Plan 0046 batch `nec` ([skills/0010](../../findings/skills/0010-necromancer.md)) settles code readers for
these columns; please link them from the table docs.

- [Skills](../../tables/Skills.md) `aurastat1..6`, `aurastatcalc1..6`, `auratargetstate`, `auraevent1..3`,
  `auraeventfunc1..3`, `auralencalc`, `aurarangecalc`, `aurafilter` for do 30 and do 61: the 0x68-byte block passed to
  `sub_0056E780_SkillForUnitsNearTarget` (§ 4, `[C]` as block words; their use by the per-unit callback `[I]`); a
  blank `aurastat1` (−1) passes do 30's and do 61's range test; do 61 leaves `aurastat1` out of its block.
- [Skills](../../tables/Skills.md) `pettype`: read signed by do 31 (refused below 0 or at or past the PetType count),
  unsigned by do 56, 57, 58, 60, 62 (0 at or past the count) (§§ 5, 6, `[C]`); `summon`, `summode`, `petmax` as the
  spawn block's words (§ 6, `[C]` as values).
- [Skills](../../tables/Skills.md) `srvmissilea` for do 63: out of `[0, Missiles count)` the function returns 1 (§ 5,
  `[C]`).
- [MonStats2](../../tables/MonStats2.md) `corpseSel` (`+0x004` bit 7) and `revive` (`+0x005` bit 0): read by the corpse
  tests `0x00645510`/`0x00645680` and by `0x005C3300` (§ 3, `[C]` as a map; the column names are the table doc's).
- [MonStats](../../tables/MonStats.md) `Velocity` (`+0x032`): `0x00645510` refuses a monster whose word is 0 (§ 3,
  `[C]` as a map; why it is read there is an open question).
- [DifficultyLevels](../../tables/DifficultyLevels.md) `AiCurseDivisor` (`+0x01C`): `0x005C37A0` divides do 30's
  length by it for `auratargetstate` 23 and 56 and do 61's always, when it is non-zero (§ 4, `[C]`); the table doc's
  `[I]` "use not read" can name these readers.
- [States](../../tables/States.md) `udead` (the bit-set at `DataTables+0x150`): read by `0x0063A770` in the corpse
  tests (§ 3, `[C]` as a map of the bit-set; the column name is the table doc's `[I]`).
