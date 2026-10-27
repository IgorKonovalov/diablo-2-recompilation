---
from: reverser
to: archivist
date: 2026-10-21
status: done
context:
  - ../../findings/skills/0013-druid.md
  - ../../tables/Skills.md
  - ../../tables/Missiles.md
  - ../../tables/States.md
resolution: "Folded 2026-10-27 (plan 0051 P0b, lane/p51b): Skills pettype, petmax, summode, aurastate, auralencalc, aurarangecalc, Param4, ResultFlags/HitFlags/HitClass, SrcDam, calc1, InTown, Missiles Size and States srvactivefunc link skills/0013, with the lane/p46m10 review's narrowed wording; the DataTables +0x17C/+0x180 list goes to plan 0051 Phase 1b (dated note; data candidates in States § Open questions) ([Skills](../../tables/Skills.md), [Missiles](../../tables/Missiles.md), [States](../../tables/States.md), [log](../../plans/done/0051-backlog-sweep-6.md#implementation-log))."
---

Not blocking. Plan 0046 batch `dru` ([skills/0013](../../findings/skills/0013-druid.md)) settles code readers for these
columns; please link them from the table docs.

- [Skills](../../tables/Skills.md) `pettype` (`+0x0BE`) for do 114, 115 and 119: read `movsx`, refused (the function
  returns 0, bit 6 not set) when negative or at or past `DataTables+0xBF0`, else the block's `+0x1C` (§ 3, `[C]` as the
  test and the value; that the count is PetType's row count `[I]`). `petmax` (`+0x0C0`): the block's `+0x20` (§ 3,
  `[C]` as the value). `summode` (`+0x0BF`): the block's `+0x10` for do 114 and 119 and `+0x24` for do 114 and 115,
  `movsx`, kept in `[0, 16)` else 1 (§ 3, `[C]` as the map).
- [Skills](../../tables/Skills.md) `aurastate` (`+0x080`) for do 116, 120, 124, start 57 and do-table entries 145, 146:
  admitted in `[0, States count)` (`test ax, ax; jl`, so 0 is admitted) (§§ 4–6, `[C]` as the test). `auralencalc`
  (`+0x060`): added to the game frame as `STATLIST_Alloc`'s third argument, raised to 1 by do 124 and not by do 120
  (§ 4, `[C]` as the map; that it is a length in frames `[I]`). `aurarangecalc` (`+0x064`): entries 145 and 146 take
  the shared exit at `UNIT_CancelEvents(game, caster; 5, id)` when it is ≤ 0 (§ 5, `[C]` as the test; that the period
  then ends, and its use as the area radius and the point range after the
  boundary `[I]`). `Param4` (`+0x154`): entry 145's first argument slot holds `frame + Param4` before its re-arm call
  (§ 5, `[C]` as the value; that it is the period `[I]`).
- [Skills](../../tables/Skills.md) `ResultFlags` (`+0x12E`), `HitFlags` (`+0x130`), `HitClass` (`+0x134`), `SrcDam`
  (`+0x1A5`) for start 58 and do 122 through `0x0056E680`: with `ResultFlags` bit 0 set no hit test is made and the
  packet gets `+0x04 = ResultFlags`, `+0x00 = 2 | HitFlags`, `+0x60 = HitClass` when non-zero, and `SrcDam` is
  `COMBAT_BuildDamage`'s fourth argument (§ 6, `[C]` as the map). `calc1` (`+0x138`) for start 58: the packet's `+0x0C`
  (§ 6, `[C]` as the value).
- [Skills](../../tables/Skills.md) `InTown` (`+0x005` bit 0, `g_BitMask32[0]`) for entries 145 and 146: when clear, a
  caster whose room is a town room (`RoomIsTown`) takes the branch that ends at `UNIT_UnlinkStatList(caster, list)`
  or `STATE_Set(caster, aurastate, 0)` (§ 5, `[C]` as the test and the calls up to the boundary; that the state is
  removed and no further period is queued `[I]`, after the boundary; wording narrowed at the `lane/p46m10` review).
- [Missiles](../../tables/Missiles.md) `Size` (`+0x18A`, `movzx`) for do 123 through `COLL_WHTest`: 0 or 1 tests one cell
  (`COLL_CellTestNb`, mask 5), 2 or more a rectangle `{x − Size/2, y − Size/2, …}` (`shr`) (§ 7, `[C]` as the map).
- [States](../../tables/States.md) `srvactivefunc` (`+0x036`): `sub_0056D790_StateDoFunc` (unit event 5,
  `g_PlayerEventFuncs[5]` and `g_MonEventFuncs[5]`, read from the image) calls `g_SkillDoFuncs[value]` with the
  event's skill id and level (§ 1, `[I]` from the reading; the event-table words `[C]` as data).
- DataTables `+0x17C`/`+0x180` (a `u16` state list and its `s16` count) for do 121's `0x005C8980`: which loader
  fills it, and from which States column (§ 6 Open question; `[I]` that it holds the shape-shift states).

**2026-10-27 (archivist, `lane/p51b`, plan 0051 Phase 0b).** Folded. The data question (DataTables `+0x17C`/`+0x180`):
the layouts cannot answer it (`states.bin` has no list field, and `DataTables` is no table record), so it goes to
**plan 0051 Phase 1b** as an item (§ Phase 1b item 3: which loader fills the list, from which States column). The data
candidates are in [States § Open questions](../../tables/States.md#open-questions): `restrict` (exactly 139, 140, 177),
`group` 3 and `transform`.
