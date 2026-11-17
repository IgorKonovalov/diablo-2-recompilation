---
from: reverser
to: spec-writer
date: 2026-11-16
status: done
context:
  - ../../plans/done/0066-simulation-inferred-claims-sweep.md
  - ../../findings/items/0013-grids-belts-stacks.md
  - ../../findings/stats/0001-aggregate.md
  - ../../findings/stats/0002-states.md
resolution: "Applied in plan 0066 Phase 3, the stats/items cluster (lane/n66si): items 1–2 in items/inventory, item 3 in items/economy (D2S_WriteCorpses' arguments [C]), items 4–5 in stats/aggregate (H4, A/B links, the refresh's reach) [log](../../plans/done/0066-simulation-inferred-claims-sweep.md)"
---

Plan 0066 batch S4e part 5f (`lane/n66z`), the closing part, raised or refined these spec statements. Not blocking.
Re-tag when the inventory rows are accepted at the batch's Tier B review; the evidence is in the findings named
(objdump readings beside the specs' Ghidra readings, `workspace/logs/n66z/s4e/run10/`).

1. **items/inventory A2, A3** (the server reads `gridX`, `gridY`, `numboxes`, no rectangle): `[C]` (static) per
   [items/0013 § 19](../../findings/items/0013-grids-belts-stacks.md#19-plan-0066-batch-s4e-part-5f-the-servers-record-reads-and-the-quality-9-writers-run2026-11-16-sweep2-s4e-emu-static).
   Refinements: `numboxes` (u32 `+0x004`) is read as its low byte by both server callers (0x00560963, 0x0063C6F5);
   `gridX`/`gridY` are read directly by `InvGridPut` and through `sub_0063ADD0_InvPageGet` by the other nine calls,
   so "by direct calls" should read "by the calls and `InvPageGet`".
2. **items/inventory K2** (quality 9): stays `[I]`, but its parenthesis can name the code path: `RecipeOutputCreate`
   sets quality 9 when the recipe output's byte `+0x06` is 9 (0x00565EB6..0x00565EE8, `[C]` static). Whether a stock
   CubeMain row has it is the archivist's check (backlog `2026-11-16-reverser-archivist-plan-0066-s4e-part5f-table-checks`).
3. **items/economy F** (`D2S_WriteCorpses`, line 551): the call's arguments are `[C]` (static): difficulty 3,
   class 513, mode 0 at 0x005698B4, the return added to `EBX` (0x005698B9); "to choose the most valuable corpse"
   stays `[I]`.
4. **stats/aggregate** per [stats/0001 § 14](../../findings/stats/0001-aggregate.md#14-plan-0066-batch-s4e-part-5f-the-static-remainders-run2026-11-16-sweep2-s4e-emu-static):
   - *Entry points*, "An item is equipped or unequipped": the other paths' direct callers are `[C]` (static):
     `StatListLinkOwner` 44 rel32 sites in 14 functions, `KeyConsume` 2 (`OBJOP_Chest`, `ObjEvent7Thunk`).
   - A2: the `+0x38` reader is `[C]` (static): `STATLIST_Unlink` calls it (0x00626BE7) with `EDX` the state and the
     list pushed. The rest of A2's remainder stays `[I]`.
   - H4: "What queues it was not read" can now say: `ActsClockPass` refreshes every client's player of an act whose
     `ActClockTick` returns non-zero (`[C]` static, 0x0052D822 → 0x0055FDE8). The 136 as act index 3's bucket period
     is `[I]` (all 28 kept logs start in level 103).
   - H6: `ITEMS_MakeEthereal` writes only its argument (`[C]` static); "only" across the flag's other users stays `[I]`.
   - J2: "`add func` 0 puts the aprop in the main list at creation" is `[C]` (static): state 0 and flags 0x40, as a
     `prop` block (0x0065FFE3..0x00660034).
   - *Draw order* bullet 2: `EquipReqRefresh` calls `PlayerSkillReselect` on every run past its three early returns
     (`[C]` static, 0x0055DEA0), and the reselect's gates are `[C]` (static); whether a stock refresh reaches the
     draw stays `[I]` (routed to H4e).
5. **stats/states H** (row 46): no spec change; moved to b (H4e). The release chain `PetLimit` → `PetRemove` →
   `PetUnitRelease` → `UnitKilled` is `[C]` (static) per
   [stats/0002 § 13](../../findings/stats/0002-states.md#13-plan-0066-batch-s4e-part-5f-the-pet-release-routed-run2026-11-16-sweep2-s4e-emu-static).
