---
from: reverser
to: archivist
date: 2026-10-21
status: done
context:
  - ../../findings/skills/0014-assassin.md
  - ../../tables/Skills.md
  - ../../tables/Levels.md
resolution: "Folded 2026-10-27 (plan 0051 P0b, lane/p51b): Levels Teleport, Skills startmana, prgcalc1..3, Param4, passivestat1/passivecalc1, pettype, summode, ItemEffect 36 and Missiles Vel/VelLev link skills/0014; 0 forbids / 2 restricts and stat 8 as mana in 256ths stay [I], as the review asked ([Levels](../../tables/Levels.md), [Skills](../../tables/Skills.md), [Missiles](../../tables/Missiles.md), [log](../../plans/done/0051-backlog-sweep-6.md#implementation-log))."
---

Not blocking. Plan 0046 batch `ass` ([skills/0014](../../findings/skills/0014-assassin.md)) settles code readers for these
columns; please link them from the table docs.

- [Levels](../../tables/Levels.md) `Teleport` (`levels` `+0x004` u8, now "none named", `[L]`): do 52 (Dragon Flight) reads
  it through `LEVELS_GetRecord(RoomGetLevelId(the caster's room))` on its teleport branch: 0 → the function returns 0
  (no teleport), 2 → `0x006229F0(caster, x, y, 0x804)` decides, any other value → `UnitTeleport(game, caster; 0, x, y,
  0, 0)` (§ 4, `[C]` as the test and the calls up to the boundary; that 0 forbids and 2 restricts a teleport `[I]`).
- [Skills](../../tables/Skills.md) `startmana` (`+0x184`, read `cmp word; jle` then `movsx; shl 8`) for start 26: a
  positive value refuses the cast (0) when `STATS_GetUnitStat(caster, 8, 0)` is below `startmana << 8` (§ 3, `[C]` as
  the test; stat 8 being mana in 256ths `[I]`).
- [Skills](../../tables/Skills.md) `prgcalc1..3` (`+0x038`–`+0x040`) through `sub_005D3DA0_SkillPrgCalcByCharge`: the calc
  at `+0x34 + 4 · clamp(charges, 1, 3)` on the progressive path (`progressive`, `aurastate` and `aurastat1` in range, a
  list of the state on the caster, the charges its `aurastat1` base stat), else `prgcalc1`; read by entries 37, 38, 39,
  41, 143 and do 43, 48, 51, 54 (§§ 5, 6, `[C]` as the map; 38, 39, 51 and 54 fall back to `aurarangecalc` when it is
  0, 37 and 143 too).
- [Skills](../../tables/Skills.md) `Param4` (`+0x154`) for start 27: `0x0056E520`'s `EDX` (§ 3, `[C]` as the value).
  `passivestat1` (`+0x098`, `movsx`) and `passivecalc1` (`+0x0A4`) for do 47: the timed block's `+0x14` and `+0x18`
  (§ 6, `[C]` as the values). `pettype` (`+0x0BE`) for do 44 and 45: `movsx`, a negative value or one at or past the
  PetType count becomes **0** (no refusal), for do 49 `movzx` with the same rule; `summode` (`+0x0BF`) for do 49 at the
  block's `+0x10` and `+0x24` (§ 6, `[C]` as the maps).
- [Missiles](../../tables/Missiles.md) `Vel` and `VelLev` (`+0x09A`, `+0x09B`) for entry 36: the nova's velocity
  `(VelLev · lvl) / 8 + Vel + calc1` at the block's `+0x28`, flag 4 when non-zero (§ 5, `[C]` as the map; the table
  already cites skills/0003 § 1 for it).
- [Skills](../../tables/Skills.md) `ItemEffect` 36 (rows 44, 48): the do-table entry 36 is `0x005D4DB0`, a nova of the
  row's `srvmissilea` centred on the cast's target unit (§ 1, `[I]`).

**Released (architect, 2026-10-21, `lane/p46m11` review: accept with fixes).** Every item as written; the review
re-read do 52's `Teleport` branch (`0x005D78F4`–`0x005D792D`: 0 → 0, 2 → the test, whose non-zero gives 0 and zero
falls through to the teleport) and `PrgCalcByCharge`'s clamp (`0x005D3E38`–`0x005D3E4A`, signed `jle 1`, `jl 3`; the
`progressive` mask byte is `g_BitMask32[2]`, `0x006CE270` = 4). Keep "0 forbids, 2 restricts" and stat 8 as mana in
256ths `[I]` in the table docs.
