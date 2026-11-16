---
from: reverser
to: spec-writer
date: 2026-11-16
status: done
context:
  - ../../plans/0066-simulation-inferred-claims-sweep.md
  - ../../findings/items/0013-grids-belts-stacks.md
  - ../../findings/stats/0001-aggregate.md
resolution: "Applied in plan 0066 Phase 3, the stats/items cluster (lane/n66si): items 1–2 in items/inventory (2 as H1's [I] remainder), items 3–8 in stats/aggregate [log](../../plans/0066-simulation-inferred-claims-sweep.md)"
---

Plan 0066 batch S4e part 5d (`lane/n66z`) raised or refined these spec statements. Not blocking. Re-tag when the
inventory rows are accepted at the batch's Tier B review; the evidence is in the findings named.

1. **items/inventory I6** (`ItemAutoEquipSlot`): the body of I6 with `skipReq` non-zero is `[C]` (ADR-0015,
   ADR-0021) per [items/0013 § 17](../../findings/items/0013-grids-belts-stacks.md#17-plan-0066-batch-s4e-part-5d-itemautoequipslot-under-emulation-and-cursordrops-cursor-clear-routed-run2026-11-16-sweep2-s4e-emu);
   with `skipReq` 0 the first call is `ItemReqCheck(item, user, 0, 0, 0, 0)`, and what follows its return stays `[I]`.
   Refinements to state: a location byte above 12 reads as empty (`InvGetBodyLocItem` returns 0 above 12, 0x0063BE00)
   and is returned; in an unequal pair a location of 0 is a slot like any other; the hands are tried 4 then 5. The
   ninth flag word of `EquipPairFlags` is never read by `EquipPairCompatible` (`[I]`).
2. **items/inventory H** (`CursorDrop`): the cursor clear is `InvSetCursor(inventory, 0)` at 0x00563CB8, after the
   search and the ground placement; it stays `[I]` (routed to the harness, H4d).
3. **stats/aggregate A3**: "`AddStat` adds to an entry and removes it at 0" is `[C]` (ADR-0021) per
   [stats/0001 § 12](../../findings/stats/0001-aggregate.md#12-plan-0066-batch-s4e-part-5d-addstats-removal-under-emulation-and-the-static-remainders-run2026-11-16-sweep2-s4e-emu);
   add: the key's param is its low 16 bits; the array shrinks by 4 entries through the pool when its spare room
   exceeds 8 after a removal.
4. **stats/aggregate B1** (`StatListLinkOwner`): `[C]`, with the refinement that the damage switch is conditional
   on the list's flag `0x40000000` (enable only when set, disable only when clear; otherwise nothing).
5. **stats/aggregate D1**: the stat-point code's addition is `[C]`: energy adds `ManaPerMagic` × n << 6 to mana
   (n > 0) and max mana, then clamps mana; vitality adds `LifePerVitality` × n << 6 to max life and (n > 0) life,
   clamps, then `StaminaPerVitality` the same for stamina; n = 1 from `PLAYER_SpendStatPoint`.
6. **stats/aggregate G3**: 126 shares 127's case and 107 shares 97's (`[C]`, raw switch bytes); the registration's
   reads (`itemevent1/2`, `itemeventfunc1/2`) `[C]`. Refinements `[I]`: 107 acts only for a player whose class is
   the skill row's `+0xC`; the registration tests the callback's fourth argument (non-zero registers unless one is
   found, 0 removes), not a crossing of 0.
7. **stats/aggregate J3**: "the lookup reads stat 71 of each set list itself" is `[C]` (six `g_SetBonusStates`,
   `StatListGetBaseStat` → `StatListGetBaseValue`).
8. **stats/aggregate A2**: `+0x0C` is `STATLIST_Alloc`'s fifth argument (the set code passes the unit's guid),
   `+0x38` is written by `STATLIST_SetRemoveCallback`, an extended list is 0x64 bytes with `+0x44` the unit and
   `+0x58` one block of two bit-sets sized from DataTables `+0xC4`; the rest of A2's extended fields stays `[I]`.
