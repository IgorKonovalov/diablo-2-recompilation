---
from: reverser
to: spec-writer
date: 2026-11-16
status: done
context:
  - ../../plans/0066-simulation-inferred-claims-sweep.md
  - ../../findings/skills/0002-missiles.md
resolution: "Plan 0066 Phase 3, skills cluster (lane/n66sk): items 1 and 2 in [skills/dispatch](../../specs/skills/dispatch.md) L2 (pseudocode and both bullets [C]) and item 3 as K4 (Cyclone Armor, [C] to UnitMarkUpdated and STATE_Set, the stat-84 write and off branch [I])."
---

Plan 0066 batch S2ae part 9 (`lane/n66sa`, run:2026-11-16-sweep2-s2ae9), the batch's closing part, ran
`sub_005C49E0_SummonSetLevel` whole and handler 25 to its boundaries, both with the stat setter whole, and settled
skills/dispatch rows 142, 143 (L2) and 129 (K 25) in part. For Phase 3 to carry when the skills cluster is re-tagged
(claims and anchors in
[skills/0002 § 25](../../findings/skills/0002-missiles.md#25-plan-0066-batch-s2ae-part-9-summonsetlevel-and-handler-25-emulated-with-the-setter-whole-the-batch-closed-2026-11-16-lanen66sa);
lines of `docs/specs/skills/dispatch.md` at `b5999f5e`, match by text). Not blocking.

1. **L2, the summon level, refinement.** The `L · 3/4` is `trunc(s32(3L) / 4)` (32-bit product,
   truncating division: `cdq`/`and 3`/`sar 2`), so a negative `L` rounds toward 0; `3L` wraps past
   ±715 827 882 (`wrap.txt`). The skill-level term is the function's third argument (`bonus`), also added in 32 bits.
   The level is `min(max(n, 1), L)` exactly as written (both clamps bind in the run); a resulting level of 0 is not
   written (no `UnitSetStat`); a positive level argument is written as given. The MonLvl row is then indexed by the
   level clamped to `count − 1`, and an index outside `[0, count)` returns 0 before the stats. The "[I] the clamps
   … are the reading" sentence can be re-tagged `[C]` (run:2026-11-16-sweep2-s2ae9).
2. **L2, no `noRatio` test, re-tag and detail.** `[C]`: `UnitAddStat(summon, 31, row[d + 3x], 0)` then
   `UnitAddStat(summon, 19, row[d + 3(x + 2)], 0)`, `d` = the game's `+0x6D` mapped 0 → 0, 1 → 1, ≥ 2 → 2, `x` = 1 when
   the game's byte `+0x6A` or dword `+0x74` is non-zero; the summon's class and MonStats are not read.
   `UnitAddStat` adds nothing for a value of 0 and does not test the unit.
3. **K 25, Cyclone Armor (the § K table's row 25), refinement.** The handler's list is the `aurastate`
   list (`UNIT_FindStatListByState`: the `+0x3C` chain, then `+0x40`), the pool its base `aurastat1` and the maximum
   its base `aurastat2` (base array, not the cache; a maximum ≤ 0 returns 0). A positive pool is spent on the
   packet's fire (`+0x10`), cold (`+0x24`) and lightning (`+0x1C`) in that order, each only when positive: a field
   smaller than the pool is zeroed and the pool reduced, else the field loses the whole pool. The pool is written
   back by `STATLIST_SetStat` (no unit mark). A pool left `≤ 0` (or 0 on entry) calls `STATE_Set(unit, aurastate,
   0)` and the list is unlinked and, when plain, freed (past the run). Otherwise `pct = MulDiv(pool, 100, max)`,
   and when `pct` exceeds the list's base stat 84 by 5 or more the state's bit is set in the unit's second state
   bit set, the unit marked updated, and stat 84 set to `pct` (the last write past the observed call, `[I]`); a
   smaller change returns 1 with stat 84 unchanged. `[C]` to `UnitMarkUpdated` and `STATE_Set`
   (run:2026-11-16-sweep2-s2ae9); the stat-84 write and the off branch past `STATE_Set` stay `[I]`.
