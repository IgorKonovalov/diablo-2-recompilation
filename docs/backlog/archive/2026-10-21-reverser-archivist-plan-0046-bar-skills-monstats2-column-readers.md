---
from: reverser
to: archivist
date: 2026-10-21
status: done
context:
  - ../../findings/skills/0012-barbarian.md
  - ../../tables/Skills.md
  - ../../tables/MonStats2.md
resolution: "Folded 2026-10-27 (plan 0051 P0b, lane/p51b): Skills srvoverlay, aurastate, auratargetstate, auralencalc, calc3, aurarangecalc, Param1..4, InTown (the +0x005 bit 0, by the layout) and MonStats2 corpseSel, soft, large, small, SizeX link skills/0012, values and tests [C], meanings [I] ([Skills](../../tables/Skills.md), [MonStats2](../../tables/MonStats2.md), [log](../../plans/done/0051-backlog-sweep-6.md#implementation-log))."
---

Not blocking. Plan 0046 batch `bar` ([skills/0012](../../findings/skills/0012-barbarian.md)) settles code readers for
these columns; please link them from the table docs.

- [Skills](../../tables/Skills.md) `srvoverlay` (`+0x04E`) for do 2: `movzx; test ax, ax; jle`, then `movsx` against
  `DataTables+0xBC0` with `jg`: the block runs for `0 < value ≤ that count` (§ 3, `[C]` as a map; that the count is the
  Overlay table's row count is `[I]`).
- [Skills](../../tables/Skills.md) `auratargetstate` (`+0x082`) and `aurastate` (`+0x080`) for do 2: the first admitted
  in `[0, States count)`, the second in `(0, States count)` (§ 3, `[C]` as the tests); `auralencalc` (`+0x060`): its
  value raised to 1, added to the game frame, the third argument of `STATLIST_Alloc` and the second of
  `UnitQueueEvent` (§ 3, `[C]` as a map; that it is a length in frames `[I]`).
- [Skills](../../tables/Skills.md) `calc3` (`+0x140`) for start 32: the `EDX` argument of `0x0056E520` (§ 3, `[C]` as the
  value; that it becomes stat 68 `[I]`, after the boundary).
- [Skills](../../tables/Skills.md) `aurarangecalc` (`+0x064`) for start 40: the `range` of `0x005D9A10`'s pull
  `(x − ux) · range / d + ux` (§ 6, `[C]` as a map; that it is the leap's range is `[I]`).
- [Skills](../../tables/Skills.md) `Param1..4` (`+0x148..+0x154`) for do 72 and `Param3`/`Param4` (`+0x150`/`+0x154`)
  for do 69: read after the boundaries, as the bands of the second roll and of the inline step (§ 4, `[I]`).
- [Skills](../../tables/Skills.md) `+0x005` bit 0 (`g_BitMask32[0]`) for start 40: when set, a town room does not refuse
  the target point (§ 6, `[C]` as the test; which column sets the bit is for the table doc).
- [MonStats2](../../tables/MonStats2.md) `+0x004` bit 7 (`corpseSel`) and `+0x005` bit 4 (`soft`): the flag-7 and
  flag-12 tests of `0x006455E0` and `0x00645590` (§ 4, `[C]` as the bit tests; the column names `[I]`, the table doc's
  layout); `+0x005` bits 3 and 2 (`large`, `small`): do 75's missile pick after its boundary (§ 4, `[I]`); `+0x008`
  (`SizeX`, read `movsx`): `UNIT_GetSizeX` of a type-1 unit, the third argument of start 40's `FreeNearFallback` (§ 6,
  `[C]` as the value).

**2026-10-27 (archivist, `lane/p51b`, plan 0051 Phase 0b).** Folded. The data question: Skills `+0x005` bit 0 is the
`InTown` column by the Skills layout (`excel_bin.py diff`, `[C]`), as the `dru` entry names it; start 40's reader is on
the `InTown` row of [Skills § Start checks](../../tables/Skills.md#start-checks-town-item-types-hands). No Phase 1b item.
