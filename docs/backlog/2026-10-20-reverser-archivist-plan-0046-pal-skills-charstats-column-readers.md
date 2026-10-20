---
from: reverser
to: archivist
date: 2026-10-20
status: open
context:
  - ../findings/skills/0011-paladin.md
  - ../tables/Skills.md
  - ../tables/CharStats.md
  - ../tables/MonStats.md
resolution: ""
---

Not blocking. Plan 0046 batch `pal` ([skills/0011](../findings/skills/0011-paladin.md)) settles code readers for
these columns; please link them from the table docs.

- [Skills](../tables/Skills.md) `mana`, `lvlmana`, `manashift`: `0x00644B10(id, lvl)` = `((lvl − 1) · lvlmana + mana)
  << (manashift byte & 31)`, 32-bit, `movsx` terms, no floor at level 1 (§ 3, `[C]` as a map); the aura functions
  compare it with stat 8 (`[C]` as the gate's map; that it is the mana cost in 1/256 is the column's `[I]`).
- [Skills](../tables/Skills.md) `perdelay`: `SKILLS_NextPeriodicFrame`'s `p`, raised to 5 when it gives 5 or less
  (§ 3, `[C]` as a map); the table doc's "5 when less than 6" agrees.
- [Skills](../tables/Skills.md) `aurastate`, `auratargetstate`, `aurastat1..6`, `aurastatcalc1..6`, `passivestate`,
  `passivestat1..5`, `passivecalc1..5` for do 65, 66, 81, 82: the words of the 0x50-byte block passed to
  `AURA_ApplyToTarget` (§ 3, `[C]` as block words; what the callee does with them `[I]`): do 65 needs `aurastate`
  above 0 (0 skipped) and `auratargetstate` 0 or more; do 66, 81, 82 need `aurastate` in `[0, States count)`.
- [Skills](../tables/Skills.md) `Param1` (`+0x148`) for start 31: `0x004C9460` adds it to `max(stat 67, 50)` in the
  charge speed `MulDiv(base, …, 100)` (§ 5, `[C]` as a map).
- [CharStats](../tables/CharStats.md) `RunVelocity` (`+0x041`): start 31 reads the byte `<< 8` as its base speed (§ 5,
  `[C]` as a map; the column name is the table doc's).
- [MonStats](../tables/MonStats.md) `Run` (`+0x034`): start 31 reads it `movsx` `<< 8` for a monster (§ 5, `[C]` as a
  map; the table doc lays it out as u16, the code reads it signed).
