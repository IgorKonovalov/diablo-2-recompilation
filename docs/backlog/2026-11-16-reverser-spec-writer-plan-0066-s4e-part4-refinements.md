---
from: reverser
to: spec-writer
date: 2026-11-16
status: open
context: ["../plans/0066-simulation-inferred-claims-sweep.md", "../findings/items/0013-grids-belts-stacks.md"]
resolution: ""
---

Plan 0066 batch S4e part 4 (`lane/n66z`, run:2026-11-16-sweep2-s4e-emu part 4) ran the other item request handlers,
`InvItemToCursor`, `InvPlaceItem` as `0x18` calls it, `InvPageGet` and `InvRowForUnit` under emulation. Claims in
[items/0013 § 13](../findings/items/0013-grids-belts-stacks.md#13-plan-0066-batch-s4e-part-4-the-other-request-handlers-invitemtocursor-invplaceitems-refusals-invpageget-invrowforunit-run2026-11-16-sweep2-s4e-emu);
rows in the 0066 inventory (items/inventory 15, 17, 23, 32–34, 36–40, 42, 45, 46, 99). For Phase 3, not blocking.
Refinements to carry into items/inventory (no contradiction):

1. **§ D, lengths.** `0x1C` has length 3 (a `u16` slot at `+1`, no guid); add it to the list. Every handler returns
   3 on a wrong length.
2. **§ D, `0x1A`..`0x1E`.** Each takes the slot with `s − 1 ≤ 9` unsigned, else 2 (not only `0x1B`). `0x1C`, `0x1D`,
   `0x1E` call `InvMoveInteractTest` (0 returns 0). `0x1D` and `0x1E` need an item at the slot, else 1. `0x1D` at slot 8
   first needs `TradeBeltLock` (0 returns 0: interacting with a player while an item of the list has location byte 2).
   `0x1E` takes slots 4 and 5 only, else 3. `0x1A` passes the slot as a dword whose bits 8..31 are the frame's old
   bytes (a reimplementation takes the byte).
3. **§ D, `0x1F`.** `PktIsCursorItem` on `+1`, `PktInvItemBad` on `+5` (mode 0, owned), page 1 or 2 → 3, then
   `InvMoveInteractTest`, then `PageSwapCursor(+1, +5, x +9, y +0xD)`.
4. **§ D, `0x24`.** The trade test is `InvMoveInteractTest` with an item of 0, before the cursor test; a full cursor
   returns 2.
5. **§ D, `0x63`.** The item passes `PktInvItemBad` (mode 0, owned); a full cursor calls `NoManaMsg` and returns 2;
   "beltable" is ItemTypes `+0x19` (else 2); a page byte ≠ 0 returns 3; then `BeltFreeSlot(inventory, item, &slot)`.
6. **§ E2.** `InvItemToCursor`'s `+0x1C` argument lets a non-empty cursor pass; a missing item, a refused page and a
   mode ≠ 0 set the out flag to 1, a full cursor leaves it 0; "busy" is `PlayerIsBusy` (an interaction, or PlayerData
   `+0x4C` ≠ 0, the cursor being empty there) and only a type-0 user is tested; the item's `+0xC4` bit 1 is cleared
   before the remove.
7. **§ E1 / Reimplementation notes.** `InvPlaceItem`'s refusals before `InvItemRemove` leave the page byte: the claim
   holds for every refusal of this route (an item missing or not in mode 4, no ItemData, the row's size, the bounds,
   a cell). A refusal after `InvItemRemove` (`InvPlaceSocketed` returning 0) is not run.
8. **§ A4.** `InvPageGet`'s page index is compared signed and shifted by 4 with wrap (`0x80000000` names page 0); with
   no row it returns a made page or 0; an index at or above the count with a row reaches the reallocation
   `0x0040B4B0`, a page not made the allocator `0x0040B430`.
9. **§ B5.** `InvGridPut` refuses an item with no ItemData before its size test (0x0063B003).
