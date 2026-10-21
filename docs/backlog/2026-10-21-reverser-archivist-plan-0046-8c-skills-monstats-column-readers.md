---
from: reverser
to: archivist
date: 2026-10-21
status: open
context:
  - ../findings/skills/0018-monster-8c.md
  - ../tables/Skills.md
  - ../tables/MonStats.md
  - ../tables/States.md
resolution: ""
---

Not blocking. Plan 0046 batch 8c ([skills/0018](../findings/skills/0018-monster-8c.md)) settles code readers for these columns; please link them from the table docs. `[C]` here is the finding's ADR-0021 map up to the named boundary; what follows a boundary stays `[I]`.

- [Skills](../tables/Skills.md) `aurastate` (`+0x080`): do 129 (Imp Teleport, row 330) and do 137 (fenris rage, row 314) return 0 unless it is in `[0, States count)` (§§ 4–5, `[C]`); do 129 reads it as a gate only, its attach and detach helpers set and clear state 143 by the constant `0x8F` (`[I]`); do 137 passes it to `0x00570590` after its boundary (`[I]`).
- [Skills](../tables/Skills.md) `auratargetstate` (`+0x082`) and `auralencalc` (`+0x060`): do 131 (Overseer Whip, row 295) gates on `auratargetstate` in `[0, States count)` and puts it, with `auralencalc` evaluated as the length, into its `STATE_ApplyTimed` block (§ 4, `[C]`).
- [Skills](../tables/Skills.md) `summon`/`summode` (`+0xBC`/`+0xBF`) and `sumumod` (`+0xE4`): do 131's class change `0x005D1E10` calls `SkillSummonClass` with `EDX` 0 (the Skills columns, stock 461 and 8) and applies `sumumod` in `(0, 43)` (§ 4, `[I]`, after the boundary); start 62 (row 302) calls it with `EDX` 1, so a monster caster's MonStats `spawn` row serves (§ 5, `[C]`).
- [Skills](../tables/Skills.md) `sumoverlay` (`+0xE6`) on do 135's spawn, `srvoverlay` (`+0x04E`) on do 128's target, `aurarangecalc` (`+0x064`) as do 134's area radius: all read after their boundaries (§§ 4–5, `[I]`).
- [Skills](../tables/Skills.md) `lob` (`+0x04` bit 1, mask byte `0x006CE26C`): do 148 and 149 (rows 335, 338) call `SkillMissileCreateLob` when set, `SkillMissileCreate` otherwise (§ 3, `[C]`); no stock row of the batch sets it.
- [Skills](../tables/Skills.md) `ResultFlags`/`HitFlags`/`HitClass` (`+0x12E`/`+0x130`/`+0x134`): do 134 (Siege Beast Stomp, row 301) puts `1 | HitFlags`, `ResultFlags` and a non-zero `HitClass` into its packet before `SkillRollPhys` (§ 4, `[C]`); its `srvmissilea` is a gate only, and the stock row's −1 returns 0 before the packet (§ 1, `[I]`).
- [MonStats](../tables/MonStats.md) `BaseId` (`+0x002`): do 131 draws only for a target whose `MonClassCheck(MonBaseId)` is 453 (`minion1`); do 133 (Impregnate, row 300) refuses 546 (`putriddefiler1`) and 551 (`painworm1`) (§ 4, `[C]`); do 129's attach tests an imp (492) and a 435 or 441 target, and `0x0063EFA0` (do 140's class) switches on the caster's base (§§ 5, 7, `[I]`).
- [States](../tables/States.md) `srvactivefunc` 147 (row 143 `attached`): `sub_005D2B20_StateDo147Attached` calls `0x006505E0(unit, its owner)` when the unit has an owner, else returns 1 (§ 5, `[C]` to that call); that the callee moves the unit's path to its owner's point is a reading (`[I]`).
- For information, not a column: do 148 and 149 add the caster's monster-data byte `+0x0E` or `+0x0F` (`U+0x14`) to `srvmissilea` (§ 3, `[C]`). If a table column fills either byte, a link from that column would close the join; otherwise nothing to do.
