# 0013 — Item use and inventory: grids, the placement search, belts, stacks, the cursor, pickup, the stash

> **Subsystem:** items/use
> **Question:** which grid does an item go to, in which order is it searched, which row of `inventory` and `belts` applies, how do
> stacks merge and split, what refuses a pickup, and what does the stash add?
> **Date:** 2026-11-04   **Plan:** 0060 (Phase 1.2)   **Status:** for review (`lane/r60b`)

Static reading of the pinned `Game.exe` (objdump, the lane's Ghidra copy `ghidra-r60b`), then emulation under ADR-0015 and ADR-0021
with `re/ghidra_scripts/EmuBoundary.java` (unchanged), `tools/item_emu2.py` against `tools/item_inventory.py`
(run:2026-11-04-inventory-emu: **9 560 cases, 10 families, 0 mismatches, 0 stops, 0 unaccounted accesses**).

**Tag convention.** **[C] (ADR-0015)** rests on families that run the named function to its return with all callees emulated over declared (run:2026-11-04-inventory-emu, fn:sub_0063B850_InvSpotFindBySize@0x0063B850)
scratch memory: `search`, `belt`, `rowfor`, `invrec`, `beltrec`, `stackok`. **[C] (ADR-0021)** rests on families that end at a named callee:
`place` and `beltplace` at `InvGridPut`, `put` at `InvItemRemove`, `merge` at `UnitSetStat`. For these **the callee and all code after it are not covered**
(written "after, `[I]`"), so "0 mismatches" holds up to that boundary. The image is scratch, not the game's structures, so each `[C]` is the code's map from the
bytes it reads, and no symbol row is raised (review-fixes 14). A plain `[I]` is a code reading the emulator does not reach. Nothing here ran on a live game: Phase 2 does.

## Answer (summary)

- [C] (ADR-0015) **The placement search has two orders by owner and two by height.** The item's size is Items `+0x10F`, `+0x110`. A player's page takes the best score: one cell high, columns from the right and in each rows from the bottom; any other height, rows from the top and in each columns from the left. A strictly higher score replaces the spot, so a tie keeps the earlier one. Any other owner, a null owner included, takes the first fit: one cell high, columns from the right, rows from the top; any other height, columns from the left, rows from the top. (fn:sub_0063B850_InvSpotFindBySize@0x0063B850, fn:sub_0063B490_InvSpotFindRow@0x0063B490, fn:sub_0063B620_InvSpotFind@0x0063B620, fn:sub_0063B540_InvSpotFirstRow@0x0063B540, fn:sub_0063B6E0_InvSpotFirst@0x0063B6E0, run:2026-11-04-inventory-emu)
- [C] (ADR-0015) **The score** counts occupied cells along the four sides, an outside side counting its whole length, and is 255 when the count reaches `2 × (w + h)`. A spot needs a free anchor cell, the rectangle inside the grid, and the rectangle free. (fn:sub_0063B340_InvSpotScore@0x0063B340, fn:sub_0063A8A0_InvGridFree@0x0063A8A0, run:2026-11-04-inventory-emu)
- [C] (ADR-0015) **`inventory`'s row** is `sub_00621050_InvRowForUnit(unit, page, expansion)`. Player: page 1 → 6, 2 → 7, 3 → 9, 4 → 12 when `expansion` is non-zero else 8, any other page → class row (0..4, 14, 15). Type 1 (a monster, so a hireling too) → 5. Type 2 class `0x152` → 10, `0x153` → 11. Otherwise −1. (fn:sub_00621050_InvRowForUnit@0x00621050, data:0x00744544, run:2026-11-04-inventory-emu)
- [C] (ADR-0015) **The stash is 6 × 8 in an expansion game and 6 × 4 in a classic one**, by that row (`rowfor`'s `expansion` argument; control `stashsmall` fails 20 of 400). (fn:sub_00621050_InvRowForUnit@0x00621050, run:2026-11-04-inventory-emu)
- [I] Each server caller of the page's row that was read passes `game+0x70` as `expansion` where the page can be 4; callers not listed here were not followed. (0x00560297, 0x00560598, 0x0054D658)
- [C] (ADR-0015) **`belts`' row is the worn belt's Items `+0x130`, or 2 with no belt worn, in the first set**; the count is the record's `+0x004`. With the second set's counts declared unlike the first's, the second-set control fails 237 of 2 000 cases. (fn:sub_0063C600_BeltFreeSlot@0x0063C600, fn:sub_00660CB0_BeltsRecord@0x00660CB0, fn:sub_00621ED0_ItemBeltByte@0x00621ED0, run:2026-11-04-inventory-emu)
- [I] **The second sets are the client's.** The record readers index `set × 16 + row` and `set × 7 + row`. All 10 calls of the inventory reader at `0x0063xxxx` and the 3 belts calls outside `0x4xxxxx` pass a literal set of 0; the other 11 and 4 calls, all in `0x4xxxxx`, take it from a register or a global (`0x007A5218` at `0x00483610`), writers unfollowed. (fn:sub_0065C1F0_InvRecordGrid@0x0065C1F0, fn:sub_00660CB0_BeltsRecord@0x00660CB0, 0x0063C6B3, 0x00560939, 0x00560918, `static.txt`)
- [C] (ADR-0015) **`gridX` and `gridY` are read as bytes** by the search. With `+0x12`, `+0x13` declared `0x7F`, a wider reading fails 2 465 of 4 000 search cases. [C] (ADR-0021) The same for the bound test of the put family (`put`, which ends at `InvItemRemove`: the callee and what follows are `[I]`). (fn:sub_0063ADD0_InvPageGet@0x0063ADD0, fn:sub_0063AFD0_InvGridPut@0x0063AFD0, run:2026-11-04-inventory-emu)
  *Corrected 2026-11-04 (`lane/r70`, from the `lane/a69` review): the bullet carried one tag (ADR-0015) for both; the put family's half rests on ADR-0021, as this finding's tag convention lists it. Two tags now.*
- [C] (ADR-0015) **The belt search.** Only a beltable 1 × 1 item. For each bottom box 0..3 that holds an item of the same class or the same list (`hp1..5`, `mp1..5`, `rvl`/`rvs`), the first free box up that column (`box, box + 4, …` below `numboxes`). Then, with `autobelt`, the first free box of 0..3. Else it returns 0. (fn:sub_0063C600_BeltFreeSlot@0x0063C600, fn:sub_00628A40_PotionSameGroup@0x00628A40, run:2026-11-04-inventory-emu)
- [C] (ADR-0015) **Stacks.** Two items can stack when class, quality and file index are equal, the row is stackable (`+0x132`), ethereal status is equal, quality is not 0 and not 4..9, stats 21, 22, 23, 24, 159, 160 are equal, and the low byte of stat 194 is 0 on both. (fn:sub_0062C850_ItemsCanStack@0x0062C850, run:2026-11-04-inventory-emu)
- [C] (ADR-0021) **A merge** with `source + target` above the maximum sets the target to the maximum; else a durable source below the target's stat 72 first lowers the target's stat 72; else the target takes the sum. The maximum is Items `+0xE8` + stat 254, and 511 when that exceeds 510. After the first `UnitSetStat`, `[I]`. (fn:sub_0055E590_StackMerge@0x0055E590, fn:ITEMS_GetMaxStack@0x006295B0, run:2026-11-04-inventory-emu)
- [I] **There is no split on the server.** Packet `0x22` reaches `sub_0055E9A0_UnstackStub`, `xor eax, eax; ret 8`, and the handler returns 0. Scope: the handler `0x0054B380` (table entry `0x22`, read from `g_SrvPacketTable`) and the 12 request rows of § 1 only; the rest of the packet table was not read for a request that divides a stack (gold's withdraw and drop, for one, are other requests), and the stub is a reading of 8 bytes, not a run. (0x0054B380, 0x0055E9A0, `static.txt`)
  *2026-11-15 (plan 0066 S4c, `lane/n66i`), correction:* the handler does not return 0. It passes `&len` as the stub's
  out word, the stub leaves it at 5, so the test at 0x0054B3BD fails and the handler returns 3 (0x0054B3C4); a not-owned
  item returns `PktOwnedItemBad`'s non-zero (0x0054B3A9). Read by r2 and objdump; the drain discards the return, so no
  outcome changes. Contradicted in part: [items/experiments § Addendum 2026-11-15 (S4c)](experiments.md#addendum-2026-11-15-plan-0066-batch-s4c-new-checks-over-the-kept-inventory-logs-and-static-second-sources-lanen66i). (0x0054B3BD, 0x0054B3C4, fn:sub_0055E9A0_UnstackStub@0x0055E9A0)
- [I] **A placed item needs no open stash, on this reading.** The packet's item is on the cursor, so `PlayerIsBusy` is 1 and the "page ≠ 0 needs busy" test always passes. Page 4 needs a town room, page 2 an interaction with a player, page 3 nothing. Taking an item off a non-zero page, with an empty cursor, does need an interaction (§ 5). `0x0055C110`, which `InvPlaceItem` skips on page 4 (§ 5), holds no such test: items/0014 § 5. (fn:sub_0055C110_ItemSkillQtyAdjust@0x0055C110, 0x0054ABFC, 0x00535099, 0x0054AC1D, 0x0054AC4E, fn:sub_00560420_InvItemToCursor@0x00560420)
- [I] **The pickup's order**, to the inventory: refuse by the cursor or busy; not on the ground sets the refuse flag; quest gate; gold; a scroll into a tome, a tome into a tome, an auto-stack; auto-equip; the belt; the inventory; the refusal `0x0055C9A0(0x17)`. To the cursor: the same tests, gold, then the cursor. (fn:sub_00563560_PickupToInv@0x00563560, fn:sub_0055CF50_PickupToCursor@0x0055CF50)

## Leads used

No community source was compared; every claim is from the code. **2026-11-04 (`lane/r60d`):** the comparison was made afterwards, with these statements as they stood; every verdict is in [items/0017](0017-community-cross-check.md), and no tag moved.

## Functions

70 rows at `I` in `re/symbols.csv`, evidence here; the map of the `search`, `belt`, `rowfor`, `invrec`, `beltrec` and `stackok` functions and of `place`, `put`, `beltplace`, `merge` up to their boundary is `[C]` under the convention above. (fn:sub_0063B850_InvSpotFindBySize@0x0063B850, run:2026-11-04-inventory-emu)

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x0054AAD0`, `0x0054AB40`, `0x0054ABB0`, `0x0054ACD0` | `sub_0054AAD0_Pkt16UnitAction`, `sub_0054AB40_Pkt17CursorDrop`, `sub_0054ABB0_Pkt18CursorToPage`, `sub_0054ACD0_Pkt19PageToCursor` | packets `0x16`..`0x19` | I |
| `0x0054AD90`..`0x0054B0F0` | `sub_0054AD90_Pkt1AEquip`, `sub_0054AE30_Pkt1BEquipSlotCursor`, `sub_0054AEC0_Pkt1CBodyToCursor`, `sub_0054AF50_Pkt1DBodySwap`, `sub_0054B030_Pkt1EBodySwap2`, `sub_0054B0F0_Pkt1FPageSwap` | packets `0x1A`..`0x1F` | I |
| `0x0054B300`..`0x0054B4E0` | `sub_0054B300_Pkt21Stack`, `sub_0054B380_Pkt22Unstack`, `sub_0054B3E0_Pkt23CursorToBelt`, `sub_0054B450_Pkt24BeltToCursor`, `sub_0054B4E0_Pkt25BeltSwap` | packets `0x21`..`0x25` | I |
| `0x0055CF50`, `0x00563560` | `sub_0055CF50_PickupToCursor`, `sub_00563560_PickupToInv` | the two pickups | I |
| `0x00560020`, `0x0055FFA0`, `0x0055D370`, `0x0055D0D0` | `sub_00560020_PickupAutoStack`, `sub_0055FFA0_PickupScrollToTome`, `sub_0055D370_PickupTomeMerge`, `sub_0055D0D0_PickupStackMerge` | the pickup's merges | I |
| `0x0055EF20` | `sub_0055EF20_ScrollIntoTome` | a scroll into a tome | I |
| `0x0055D710`, `0x005600A0` | `sub_0055D710_ItemAutoEquipSlot`, `sub_005600A0_InvAutoPlace` | auto-equip, the search on page 0 | I |
| `0x00560420`, `0x00560CD0`, `0x00560F00`, `0x00561220`, `0x00561B00`, `0x00563D20` | `sub_00560420_InvItemToCursor`, `sub_00560CD0_BodyToCursor`, `sub_00560F00_BodySwapCursor`, `sub_00561220_BodySwapCursor2`, `sub_00561B00_PageSwapCursor`, `sub_00563D20_EquipCursorAtSlot` | the cursor's moves | I |
| `0x00563C00` | `sub_00563C00_CursorDrop` | the cursor to the ground | I |
| `0x0055E7C0`, `0x0055E590` | `sub_0055E7C0_StackRequest`, `sub_0055E590_StackMerge` | packet `0x21`'s body, the merge | I (map C to the first set) |
| `0x0055E9A0` | `sub_0055E9A0_UnstackStub` | returns 0 | I |
| `0x0055EB30`, `0x00562250` | `sub_0055EB30_BeltSwapCursor`, `sub_00562250_BeltToCursor` | the belt's moves | I |
| `0x005608C0` | `sub_005608C0_BeltOverflow` | the belt's overflow: the corpse call logged at entry and return, 24 of 24 moves as predicted (§ 11) | C (raised 2026-11-15 at the `lane/n65h` review; the body moves' calls unobserved) |
| `0x00621050` | `sub_00621050_InvRowForUnit` | row for a unit and page | I (map C) |
| `0x0065C1F0`, `0x00660CB0` | `sub_0065C1F0_InvRecordGrid`, `sub_00660CB0_BeltsRecord` | the table readers | I (map C) |
| `0x0065C180`, `0x0065C270`, `0x00660D10` | `sub_0065C180_InvRecordRect`, `sub_0065C270_InvRecordSlotRect`, `sub_00660D10_BeltsBoxRect` | the rectangle readers, client callers | I |
| `0x00628A40`, `0x00628BA0`, `0x0062BAD0`, `0x0062E790` | `sub_00628A40_PotionSameGroup`, `sub_00628BA0_ItemAutoBeltTest`, `sub_0062BAD0_ItemTypeBeltable`, `sub_0062E790_ItemTypeAutoStack` | the belt and auto-stack tests | I (`0x00628A40` map C) |
| `0x0062C850`, `0x00629570` | `sub_0062C850_ItemsCanStack`, `sub_00629570_ItemRecMaxStack` | the stack test, Items `+0xE8` | I (map C) |
| `0x0063ADD0`, `0x0063A910`, `0x0063A970`, `0x0063AAF0`, `0x0063AD90`, `0x0063AF70`, `0x0063BCC0` | `sub_0063ADD0_InvPageGet`, `sub_0063A910_InvGridFill`, `sub_0063A970_InvPageUnlink`, `sub_0063AAF0_InvItemRemove`, `sub_0063AD90_InvTakeItem`, `sub_0063AF70_InvPageAppend`, `sub_0063BCC0_InvPutAt` | the page's upkeep | I |
| `0x0063B540`, `0x0063B6E0`, `0x0063B5E0`, `0x0063B790`, `0x0063B7D0`, `0x0063B810` | `sub_0063B540_InvSpotFirstRow`, `sub_0063B6E0_InvSpotFirst`, `sub_0063B5E0_InvSpotOneHigh`, `sub_0063B790_InvSpotTall`, `sub_0063B7D0_InvSpot2x2`, `sub_0063B810_InvSpotOther` | the search's branches | I (map C) |
| `0x0063C180`, `0x0063C200`, `0x0063C2F0`, `0x0063C3B0` | `sub_0063C180_InvSetCursor`, `sub_0063C200_InvStackWithRoom`, `sub_0063C2F0_BodyStackWithRoom`, `sub_0063C3B0_InvTomeWithRoom` | the cursor word, stack finders | I |
| `0x0063C4C0`, `0x0063C4F0`, `0x0063C560`, `0x0063C7F0` | `sub_0063C4C0_BeltPut`, `sub_0063C4F0_BeltPutItem`, `sub_0063C560_BeltHoldsSameGroup`, `sub_0063C7F0_BeltBoxItem` | the belt's pages | I |

## 1. The requests

`[I]` Read from `g_SrvPacketTable` at `0x006E0D18`, 8-byte entries, and each handler's body (data:g_SrvPacketTable@0x006E0D18). "Refuse" is a handler return of 3 or 2.

| Packet | Handler | Body | Tag and anchor |
|---|---|---|---|
| `0x13`, `0x16` | `0x0054AA90`, `0x0054AAD0` | `UnitInteract(type ≤ 5, guid, action)`; `0x13`'s action is 0. *2026-11-16, § 12: `[C]` to the call; a type of 6 up returns 2, and `0x16` with type 0 and the player's own guid returns 3* | [I] (fn:sub_00548B00_UnitInteract@0x00548B00) |
| `0x17` | `0x0054AB40` | a cursor item; `InteractIsPlayer(0)` non-zero returns 3; `CursorDrop`. *2026-11-16, § 12: `[C]` to the call; the interaction test runs only when `PlayerIsBusy` is non-zero, and `InteractIsPlayer` does not read its argument* | [I] (fn:sub_00563C00_CursorDrop@0x00563C00) |
| `0x18` | `0x0054ABB0` | § 5; `ItemSetPage(item, page)`, then `InvPlaceItem(…, x, y, 0, 1, 0)`. *2026-11-16, § 12: `[C]` to the call* | [I] (fn:sub_00560200_InvPlaceItem@0x00560200) |
| `0x19` | `0x0054ACD0` | an owned item, empty cursor, not page 1; trade test `0x00535610`; `InvItemToCursor`. *2026-11-16, § 12: `[C]` to the call; a full cursor ends at `NoManaMsg`, and a 0 from the trade test returns 0 with nothing moved* | [I] (fn:sub_00560420_InvItemToCursor@0x00560420) |
| `0x1A`..`0x1E` | | equip and swap with a body location (`0x1B`'s slot 1..10) *2026-11-16, § 13: `[C]` to each call; `0x1C` has length 3 and a `u16` slot, `0x1D`/`0x1E` need an item at the slot, `0x1E` takes slots 4 and 5 only* | [I] (fn:sub_005606B0_ItemEquip@0x005606B0, fn:sub_00563D20_EquipCursorAtSlot@0x00563D20, fn:sub_00560CD0_BodyToCursor@0x00560CD0, fn:sub_00560F00_BodySwapCursor@0x00560F00, fn:sub_00561220_BodySwapCursor2@0x00561220) |
| `0x1F` | `0x0054B0F0` | the cursor against a page item, not an item on page 1 or 2 *2026-11-16, § 13: `[C]` to the call, `InvMoveInteractTest` before it* | [I] (fn:sub_00561B00_PageSwapCursor@0x00561B00) |
| `0x21` | `0x0054B300` | two owned items, unequal guids; `StackRequest` *2026-11-16, § 13: `[C]` to the call* | [I] (fn:sub_0055E7C0_StackRequest@0x0055E7C0) |
| `0x22` | `0x0054B380` | an owned item; the stub *2026-11-16, § 13: `[C]` to the call, length 5* | [I] (0x0055E9A0) |
| `0x23` | `0x0054B3E0` | a cursor item; `ItemToBelt(guid, box, 0)` *2026-11-16, § 13: `[C]` to the call* | [I] (fn:sub_0055E9B0_ItemToBelt@0x0055E9B0) |
| `0x24` | `0x0054B450` | a belt item, trade test, empty cursor; `BeltToCursor` *2026-11-16, § 13: `[C]` to the call; the trade test gets an item of 0 and a full cursor returns 2* | [I] (fn:sub_00562250_BeltToCursor@0x00562250) |
| `0x25` | `0x0054B4E0` | a cursor item and a belt item; `BeltSwapCursor` *2026-11-16, § 13: `[C]` to the call* | [I] (fn:sub_0055EB30_BeltSwapCursor@0x0055EB30) |
| `0x63` | `0x0054D520` | an inventory-page beltable item, empty cursor: `BeltFreeSlot`, then to that box *2026-11-16, § 13: `[C]` to `BeltFreeSlot`; a full cursor ends at `NoManaMsg`; after it `[I]`* | [I] (fn:sub_0054D520_SrvPacket63Handler@0x0054D520) |

## 2. Grids and pages

- [I] An inventory is `0x40` bytes (magic `0x01020304`); `+0x08` owner, `+0x0C`/`+0x10` the item list, `+0x14` the pages, `+0x18` their count, `+0x20` the cursor item, `+0x28` the item count. (fn:INV_Create@0x0063ABD0, fn:sub_0063AAF0_InvItemRemove@0x0063AAF0)
- [I] The page table's index is `page + 2`; index 0 is the body (13 × 1), index 1 the belt (16 × 1), both sizes in the image, not the tables. Each entry is 16 bytes: `+8` width, `+9` height, `+0xC` the cells (u32 unit pointers, `row × width + col`). (data:0x0074479C, data:0x007447B4, fn:sub_0063ADD0_InvPageGet@0x0063ADD0)
- [I] A page is made on first use from the row given then. A later request with another size returns 0, so nothing is placed. *2026-11-16, § 13: the size refusal `[C]` (ADR-0015, `pageget`); the first use reaches the allocator `0x0040B430` (b, H4d); the index is signed and wraps when shifted by 4.* In a save moved between game types this would be the refusal; no run reaches it. (0x0063AE53, 0x0063AE5A, fn:sub_0063ADD0_InvPageGet@0x0063ADD0)
- [C] (ADR-0021) `InvGridPut(col, row, index, invrow)` refuses a zero size. Indices 0 and 1 force the size to 1 × 1 and have **no** bound test; index 2 and above refuse `col < 0`, `col + w > gridX`, `row < 0`, `row + h > gridY`, then an occupied cell. The rest ends at `InvItemRemove`, after, `[I]`: the page fill, the page byte, the location byte. (fn:sub_0063AFD0_InvGridPut@0x0063AFD0, run:2026-11-04-inventory-emu)
- [I] Note `InvGridFree` tests no bound itself; `InvPlaceItem`'s direct branch clamps a negative `x`, `y` to 0 and relies on `InvGridPut`. *2026-11-16, § 13: the clamp and `InvGridPut`'s refusals `[C]` (ADR-0021, `place`); `InvGridFree` not run.* (0x005602BE, fn:sub_00560200_InvPlaceItem@0x00560200) *Update 2026-11-16 (plan 0066 S4e part 5a): `InvGridFree`'s lack of a bound test `[C]` (ADR-0015), family `gridfree`, [§ 14](#14-plan-0066-batch-s4e-part-5a-the-search-on-full-pages-and-in-sequence-invgridfree-the-belt-tests-beltputitem-the-ground-expirys-quality-9-and-the-quest-call-run2026-11-16-sweep2-s4e-emu); the clamp was § 13's.*
- [I] `InvGridPut`'s location byte (`+0x69`): body `(col > 10) + 3`, belt 2, a page 1. (0x0063B1BF, 0x0063B1D2, 0x0063B1E9, fn:sub_0063AFD0_InvGridPut@0x0063AFD0)

## 3. The placement search

`[C]` (ADR-0015) Entry `InvSpotFindBySize(inv, item, row, &col, &row, page)` (fn:sub_0063B850_InvSpotFindBySize@0x0063B850, run:2026-11-04-inventory-emu):

```
(w, h) = Items[+0x10F], Items[+0x110]; a zero refuses
grid   = page(page + 2) with gridX, gridY of row            -- bytes
player = inv.owner != null and inv.owner.type == 0
if h == 1:  player ? BEST(cols W-1..0, rows H-1..0) : FIRST(cols W-1..0, rows 0..H-1)
else:       player ? BEST(rows 0..H-1, cols 0..W-1) : FIRST(cols 0..W-1, rows 0..H-1)

BEST:  best = 0; for each spot in order that fits: s = score(spot); if s > best: keep it, best = s; if s == 255: return
       return best != 0
FIRST: return the first spot that fits
fits:  cell(col, row) == 0 and col + w <= W and row + h <= H and every cell of the rectangle is 0
score: n = 0
       left:   col < 1       ? n += h : n += occupied cells in column col - 1
       right:  col + w >= W  ? n += h : n += occupied cells in column col + w
       top:    row < 1       ? n += w : n += occupied cells in row row - 1
       bottom: row + h >= H  ? n += w : n += occupied cells in row row + h
       n >= 2 * (w + h) ? 255 : n
```

- [C] (ADR-0015) On an empty page, one cell high for a player lands at `(W − 1, H − 1)`, taller at `(0, 0)`; for any other owner one cell high lands at `(W − 1, 0)`, taller at `(0, 0)`. (fn:sub_0063B5E0_InvSpotOneHigh@0x0063B5E0, fn:sub_0063B810_InvSpotOther@0x0063B810, run:2026-11-04-inventory-emu)
- [I] The branches for `h == 3` and `w ≤ 2`, for 2 × 2 and for the rest call three bodies equal byte for byte with their call displacements masked (`static.txt`), so the size only tells the height-1 case from the others. The separation of the branches is not a behaviour. (0x0063B790, 0x0063B7D0, 0x0063B810, `static.txt`)
- [C] (ADR-0015) The early stop at 255 is not separable from no stop: 255 is the highest score and only a strictly higher one replaces, control `no255` fails 0 of 4 000, and a reimplementation may leave it out. (fn:sub_0063B620_InvSpotFind@0x0063B620, run:2026-11-04-inventory-emu)
- [I] A best of 0 fails only when no spot scores above 0, which needs a free rectangle touching nothing and no slide to one that touches. Sliding a free rectangle toward any occupied cell or edge finds a higher score, so a player's search fails only where no spot fits. The `search` family holds no counter-case, and this is a reading of the loop. (fn:sub_0063B490_InvSpotFindRow@0x0063B490, fn:sub_0063B620_InvSpotFind@0x0063B620, run:2026-11-04-inventory-emu) *Update 2026-11-16 (plan 0066 S4e part 5a): `[C]` (ADR-0015) on full, near-full and one-hole pages, family `search`, [§ 14](#14-plan-0066-batch-s4e-part-5a-the-search-on-full-pages-and-in-sequence-invgridfree-the-belt-tests-beltputitem-the-ground-expirys-quality-9-and-the-quest-call-run2026-11-16-sweep2-s4e-emu).*

**What the run separates** (`check.txt`; each control fails that many of `search`'s 4 000 cases, of `place`'s 500 where named):

| Control | Wrong reading | Fails |
|---|---|---|
| `geq` | a later spot wins a tie | 707 (`place` 113) |
| `noedge` | outside sides do not count | 898 |
| `h1general` | one cell high takes the general order | 723 |
| `colright` | the general order, columns from the right | 362 |
| `rowfirst` | one cell high, rows as the outer loop | 74 |
| `firstall` | a player gets the first fit | 543 (`place` 76) |
| `bestall` | every owner gets the score | 575 (`place` 47) |
| `no255` | no early stop | 0: not separable, above |

## 4. The rows, the tables' open questions

- [C] (ADR-0015) `InvRecordGrid(row, set, out)` copies 24 bytes from `base + (16·set + row) × 0xF0 + 0x10`: `gridX` to `gridBoxHeight`; a rectangle is not copied. An index above the count (`0x0096D4F0`) reaches `0x00408090`; the count itself (32) is accepted and past the table. (fn:sub_0065C1F0_InvRecordGrid@0x0065C1F0, run:2026-11-04-inventory-emu)
- [C] (ADR-0015) `BeltsRecord(row, set, out)` copies the 264-byte record from `base + (7·set + row) × 0x108`, with no upper bound on the row. (fn:sub_00660CB0_BeltsRecord@0x00660CB0, run:2026-11-04-inventory-emu)
- [I] **Reader survey of the bases:** the operand references to `0x0096D4F4` and `0x0096D4F8` sit in the loaders, the frees, `InvRecordGrid`, `BeltsRecord` and four more readers. `0x0065C270` (a body slot's rectangle, 20 direct calls), `0x0065C180` (the page and grid rectangles, 10) and `0x00660D10` (a box's rectangle, 6) are called only from `0x4xxxxx`, client code by the project's convention; `0x0065C140` and `0x00660C70` have 0 direct calls, table pointers to them unfollowed. (`static.txt`, 0x0065C270, 0x0065C180, 0x00660D10, 0x0065C140, 0x00660C70)
- [I] So by direct calls the server reads `gridX`, `gridY` of `inventory` and `numboxes` of `belts`, and no rectangle. Rows 13 and 29 (Hireling) are never returned by `InvRowForUnit`: a hireling is type 1, row 5. *2026-11-16, § 13: `[C]` (ADR-0015, `rowfor`, every page byte).* The literal `0x0D` at `0x00483705` is client code. (0x00483705, fn:sub_00621050_InvRowForUnit@0x00621050)
- [I] **`Armor.belt` as the row is now a reader:** `0x0063C6A3` (the belt search) and `0x0056091B` (the belt overflow) both pass the worn item's Items `+0x130` to `BeltsRecord` with set 0. No worn belt gives row 2, at `0x0063C69B` and `0x0056093B`. (0x0063C6A3, 0x0056091B, 0x0056093D)
- [I] Of P1.1's unclassified readers, `0x0063C8B1` is `sub_0063C830_BeltBoxQuery`'s: `useable` and `belt` both exactly 1 on a 1 × 1 beltable item, else 0; callers unfollowed. (fn:sub_0063C830_BeltBoxQuery@0x0063C830)
- [I] Types `0x152`, `0x153` for rows 10 and 11 (Guild Vault, Trophy Case) are object classes; no path reaching them was read, and `inventory`'s page names are the only reason to give them those names. (0x00621050)

## 5. The stash and pages: `0x18`, `0x19`

- [I] `0x18` for a player, in order: the cursor test; a page ≥ 5 returns 2 (the `PlayerIsBusy` branch never returns there, § Answer); page 4: a room in town, else 3; page 2: `InteractIsPlayer(1)`, else 3; page 3, 0: nothing further. Then `ItemSetPage(item, page)` **before** the placement, so a refused item keeps the new page byte on the cursor. *2026-11-16, § 13: `InvPlaceItem`'s refusals before `InvItemRemove` leave the byte, `[C]` (ADR-0021, `place`); one after it not run.* A non-player user has only the page ≥ 5 test. *Corrected 2026-11-04 (`lane/s60` review): for a player the code passes only pages 0, 2, 3 and 4 and returns 2 for any other, page 1 and negatives included (`0x0054AC3E`, `0x0054AC40`).* *2026-11-16 (S4e part 3, § 12): `[C]` (ADR-0021) up to `InvPlaceItem`'s call, the page byte written before it; whether a refused placement keeps it is `InvPlaceItem`'s code, still `[I]`.* (0x0054ABE5..0x0054AC7E, 0x0054AC68)
- [I] `InvPlaceItem`: page 4 alone skips `0x0055C270` (for a player, `0x0055C110(1)`, a scroll's or tome's skill quantity, no page test; read at items/0014 § 5, fn:sub_0055C110_ItemSkillQtyAdjust@0x0055C110). An active charm then attaches. A failed put returns 0, the handler 3. (0x00560327, 0x0056032F, fn:ITEMS_IsActiveCharm@0x0062FF70, fn:sub_00560200_InvPlaceItem@0x00560200)
- [I] `0x19` → `InvItemToCursor(…, 1, 0, 0, 0)`: the cursor empty; a player not busy (no interaction, empty cursor, PlayerData `+0x4C` 0) refuses any page but 0; the item in mode 0; then remove, page byte saved, page `0xFF`, cursor word, mode 4, event flag 4. *2026-11-16, § 13: `[C]` (ADR-0021, `tocur`) to `InvTakeItem` ("remove"), with the force argument `+0x1C` and the `+0xC4` bit 1 clear before it; what follows not run.* (fn:sub_00560420_InvItemToCursor@0x00560420, 0x005604D2, 0x005604DC)
- [I] Page bytes in the code: 0 inventory, 1 and 2 trade, 3 cube, 4 stash; `0xFF` while on the cursor or the belt. (0x00628280, 0x0054AC7E, fn:sub_00621050_InvRowForUnit@0x00621050)

## 6. Belts

- [C] (ADR-0015) `BeltFreeSlot`, each case to its return, boxes reached 0..12 and 15 (`check.txt` outcomes 15, `belt`). The `walk1` control (column walk by 1) fails 192, `nogroup` 126, `noauto` 337, `defaultbelt` 160, `secondset` 237 of 2 000. (fn:sub_0063C600_BeltFreeSlot@0x0063C600, run:2026-11-04-inventory-emu)
- [C] (ADR-0021) `BeltPlace` ends at `InvGridPut(box, 0, 1, 0)`, or returns 0 where the search does. After, `[I]`. (fn:sub_0063C790_BeltPlace@0x0063C790, run:2026-11-04-inventory-emu)
- [I] A row with `autobelt` 0 (stock `isc`, `tsc`, `yps`, `vps`, `wms` among them) is in no list, so it joins only a column whose bottom box holds its own class. (0x0063C731, tbl:Misc.txt:autobelt, fn:sub_00628A40_PotionSameGroup@0x00628A40)
- [I] **`ItemAutoBeltTest` is always 1** on an item: an `autobelt` row returns 1, any other compares `BeltHoldsSameGroup` (0 or 1) with −1. So the pickup's belt branch always calls `BeltPlace`, and the column search in it decides. (0x00628BFD, 0x00563716, `static.txt`) *Update 2026-11-16 (plan 0066 S4e part 5a): `[C]` (ADR-0015) for every item the test accepts, families `autobelt` and `holds`; a null item, a non-item or a row past the table ends at the error routine 0x00408090, [§ 14](#14-plan-0066-batch-s4e-part-5a-the-search-on-full-pages-and-in-sequence-invgridfree-the-belt-tests-beltputitem-the-ground-expirys-quality-9-and-the-quest-call-run2026-11-16-sweep2-s4e-emu).*
- [I] **`0x23` does not test `numboxes`:** `ItemToBelt(guid, box, 0)` → `BeltPutItem` needs 1 × 1, beltable, `box < 16`; `InvGridPut` refuses an occupied box. Whether a box past the belt's count stays is Phase 2's. (0x0063C4C0, fn:sub_0063C4F0_BeltPutItem@0x0063C4F0, fn:sub_0055E9B0_ItemToBelt@0x0055E9B0)
- [I] `0x24` → the box's column shifts down (`BeltColumnShift`, items/0012 § 3 at `0x0055EDC0`). `0x25` swaps in place with no shift. `0x63` needs page 0 and an empty cursor, and returns 0 with no room. (fn:sub_00562250_BeltToCursor@0x00562250, fn:sub_0055EDC0_BeltColumnShift@0x0055EDC0, fn:sub_0055EB30_BeltSwapCursor@0x0055EB30, fn:sub_0054D520_SrvPacket63Handler@0x0054D520)
- [I] **A smaller belt:** `BeltOverflow(new belt or null)` walks boxes 0..15; each item at or above the new `numboxes` is removed, set to page 0 and placed by the search, and if that fails dropped by the cell search (`0x00555DA0`, P1.3). Its callers are the body moves' belt-type branches. *Corrected 2026-11-04 (`lane/r60d` review): 4 direct calls: 0x00560E18, 0x00561058, 0x00563EE4, and 0x0057F47A on a corpse's making, with a null belt; 0x00560C45 is its own call of the ground search (`tools/call_arg_sites.py`, items/0017 B8).* *2026-11-15: the corpse call observed, § 11.* (fn:sub_005608C0_BeltOverflow@0x005608C0, 0x00560C45, 0x00563D20, 0x0057F47A)

## 7. Stacks

- [C] (ADR-0015) `ItemsCanStack`: `stackok`'s 660 cases hold each test broken alone, with both returns met. Quality 3 and 10 stack, 0, 4 and 9 do not; stat 194 of `0x100` on both passes (the low byte). (fn:sub_0062C850_ItemsCanStack@0x0062C850, 0x0062A2F0, run:2026-11-04-inventory-emu)
- [C] (ADR-0021) `StackMerge`, 500 cases to the first `UnitSetStat(target, stat, value, 0)`: 246 above the maximum, 87 exactly at it (the sum, not the over-branch), 167 below; 40 cases lower stat 72. After, `[I]`. (fn:sub_0055E590_StackMerge@0x0055E590, run:2026-11-04-inventory-emu)
- [I] **After the first set:** above the maximum the source keeps `source + target − maximum` and stays on the cursor, the target gets flag 8, and a tome adds `maximum − target` to the skill's quantity (`0x0055C070`). Otherwise stat 70 is the sum, a tome adds the source's quantity, the cursor is cleared and the source freed. (0x0055E623, 0x0055E66A, 0x0055C070) *2026-11-16, § 15: moved to the harness (H4d): every branch's stat message can allocate (0x0053B2DD).*
- [I] **Bound.** A negative source, target or maximum ends at the fatal path. The sum is `int32`: two stacks at the 511 ceiling give 1 022, which fits, and `2³¹ − 1` is the largest sum that does. Past it the add wraps negative, the `jle` at `0x0055E617` takes the not-above branch, and its `≥ 0` test ends at the fatal path too, so no wrapped value is stored. (0x0055E5C2, 0x0055E5F2, 0x0055E606, 0x0055E617, fn:sub_0055E590_StackMerge@0x0055E590)
- [I] `StackRequest`: a missing unit or a target on page 2 sets the refuse flag, and the handler returns 3, as it does for equal guids. An unstackable pair returns 0 with the flag clear, so the handler returns 0 with nothing done. (fn:sub_0055E7C0_StackRequest@0x0055E7C0, 0x0054B33E, 0x0054B356) *2026-11-16, § 15: `[C]` to `StackMerge`; a found unit not of type 4 also returns 0 with the flag clear (refinement); the class compare at 0x0055E8A3 is unreachable unequal.*

## 8. Pickup

- [I] `UnitInteract`'s item case: the unit's mode 3; distance (`0x00641530`) above 50 does nothing; below 5 and `0x00622B50(…, 0x804)` 0 picks up: action 0 to the inventory, else to the cursor; else it walks there. *2026-11-16 (S4e part 3, § 12): `[C]` (ADR-0021) up to the pickups, `InteractWalkTo` (0x00548A50, not `PLAYER_ModeCmdUnit` directly) and the line test; a missing item, a mode other than 3 and `d > 50` return 1.* (0x00548C60..0x00548CC5, fn:sub_00548B00_UnitInteract@0x00548B00)
- [I] **To the inventory** (`0x00563560`), in order: cursor empty and not busy, else return 0; the unit's mode 3, else the refuse flag; `ItemQuestGate`, a refusal calls `0x0055C9A0(0x13)`; `UnitSetEvent`; gold → `GoldPickup`; `PickupAutoStack`; `ItemAutoEquipSlot` with `0x0063DE60 == 1` → the body; beltable and `BeltPlace`; `InvAutoPlace` on page 0; else `0x0055C9A0(0x17)`, nothing moved. *Corrected 2026-11-04 (`lane/s60` review): a named location with `0x0063DE60 != 1` does not go on to the belt: it sets the refuse flag and returns 0 (`0x005636AE`, `0x00563607`). `InvClearUseMarks` runs before the gate (`0x00563627`), and first in `CursorDrop` (`0x00563C47`).* (fn:sub_00563560_PickupToInv@0x00563560, fn:sub_0055CC90_ItemQuestGate@0x0055CC90, fn:sub_0055C850_GoldPickup@0x0055C850)
- [I] `PickupAutoStack`: type 22 → the first tome of its kind with room (`0x0063C3B0`: type 18, the same `ITEMS_GetSuffix`, quantity below the maximum); type 18 → the same finder and a merge; a stackable row whose item type's byte `+0x13` is set → `PickupStackMerge`, repeating on each stack with room, a quiver type looking at the body first. Otherwise 0, and the order goes on. A remainder stays the same item, reduced, and goes on down the order (items/0014 § 5). (fn:sub_00560020_PickupAutoStack@0x00560020, fn:sub_0055FFA0_PickupScrollToTome@0x0055FFA0, fn:sub_0055D370_PickupTomeMerge@0x0055D370, fn:sub_0055D0D0_PickupStackMerge@0x0055D0D0)
- [I] `ItemAutoEquipSlot` needs `ItemReqCheck`, flag `0x10`, not disabled, not type 38; the rest of its body names the location (items/0014 § 5). (fn:sub_0055D710_ItemAutoEquipSlot@0x0055D710)
- [I] **To the cursor** (`0x0055CF50`): the same refusals and the gate; gold; else remove from the room, cursor word, mode 4, page `0xFF`, event flag `0x40`, clears flag bit 25, `QUESTS_RaiseItemPlaced`; `UnitSetEvent` last. (fn:sub_0055CF50_PickupToCursor@0x0055CF50)
- [I] Ownership (who dropped it) is not among any test read in the two pickups; `nopickup` was not found read there. Scope: these two functions and their direct callees' first level, not the gate's whole body, which items/0010 holds. (fn:sub_00563560_PickupToInv@0x00563560, fn:sub_0055CF50_PickupToCursor@0x0055CF50)
- [I] **The cursor to the ground:** mode 4; cell search `0x00555DA0(…, 1, 1)` from the user's position; `0x00558AA0` places; cursor cleared; flag 1 for an item holding items; `0x4000` cleared; `0x00563840`, which empties a dropped cube (items/0014 § 2). A null room from the search moves nothing; with `fallback` 1 a full surround does not give null, it drops on the blocked start (corrected 2026-11-04: items/0014 § 1, § 6). (fn:sub_00563C00_CursorDrop@0x00563C00, fn:sub_00555DA0_GroundDropCell@0x00555DA0)

## 9. Draws per seed

| Path | Draws | Tag |
|---|---|---|
| The search, `InvGridFree`, the score, `InvRowForUnit`, the table readers, `BeltFreeSlot`, `ItemsCanStack`, each to its return | 0: no traced access to a unit's seed (`unit+0x20`) | [C] (ADR-0015) (fn:sub_0063B850_InvSpotFindBySize@0x0063B850, fn:sub_0063C600_BeltFreeSlot@0x0063C600, run:2026-11-04-inventory-emu) |
| Closure under `0x0063C600` and `0x0063B950`: 560 and 632 functions, 0 with a step, 54 and 57 indirect calls unfollowed | 0 in direct calls | [I] (`rcg-summary.txt`, 0x0063C600, 0x0063B950) |
| The moves `0x0055CF50`, `0x00563560`, `0x0055E7C0`, `0x00563C00`, `0x00560420`, `0x00560200`, `0x0055E9B0`, `0x00562250`, `0x0055EB30`, `0x00561B00`, `0x005608C0`: 2 096..2 122 functions, 118 with a step, 112 indirect | not bounded: the closures run through the same unit paths as items/0012 § 8 | [I] (`rcg-summary.txt`, 0x00563560) |

[I] No move's own body holds a draw; a whole move's bound is Phase 2's seed comparison. (0x00563560, `rcg-summary.txt`)

## 10. Harness cases for Phase 2

Predicted by `tools/item_inventory.py`; logged: the item's page, cell and mode after each request, seed before and after.

1. Sequential 1 × 1 pickups to a player's empty inventory: `(9, 3), (9, 2), (9, 1), (9, 0), (8, 3)`.
2. 2 × 3, 1 × 4, 2 × 2 pickups on an empty inventory: `(0, 0)`, then the score's choice; the tie to the earlier spot.
3. A crowded inventory where score and first fit differ: `spot_find` for both, the player's expected.
4. A full inventory: message `0x17`, nothing moved, item on the ground.
5. The cube: outputs by the existing cube run; 3 × 4 as row 9.
6. Stash, expansion: a 2 × 4 item placed at cell y = 4 (inside 6 × 8, outside 6 × 4); the same request from a classic-game character: refused.
7. `0x18` to page 4 with no stash open, in town (a crafted request): accepted per § 5. Out of town: 3.
8. `0x19` from page 4 with no stash open: refused.
9. `0x18` with a page of 5: 2. Page 2 with no player interaction: 3.
10. A refused `0x18` (occupied cell): the item stays on the cursor, page byte as sent.
11. Worn belts: `hp1` pickups on no belt, `lbl`, `mbl`, `hbl` and an elite belt: boxes in order; 4, 8, 12, 16 stop.
12. `hp2` beside `hp1` in a column, `mp1` beside it (a new column), `rvs` beside `rvl`.
13. `tsc`, `isc`, `yps` pickups with an empty belt (all `autobelt` 0): not belted; each beside a box of its own class: belted.
14. `0x23` to a box past `numboxes` (crafted): § 6's open case.
15. Taking off a 16-box belt with items in the top rows: order 0..15; to the inventory; a full inventory drops them.
16. `0x24` from the bottom box of a 3-high column: the shift; `0x25`: no shift.
17. `0x63` shift-move: an inventory `hp1`, a non-beltable item, with a cursor item.
18. `0x21`: two quivers whose sum is above the maximum: target at maximum, source on cursor, flag 8. Equal sum: the source freed. Unequal ethereal: refused.
19. `0x21` tome and tome, stat 70 and the skill's quantity; `0x22`: nothing changes.
20. Pickup: an `isc` to an `ibk` with room, at the maximum (goes on to the belt or inventory); arrows to two partial stacks; a remainder's fate (§ 8).
21. Pickup at distance 4 and 5, 50 and 51; a line-blocked one.
22. Pickup with a cursor item, and busy: refused, no message.
23. Auto-equip: an empty ring slot; a weapon with a requirement unmet.
24. Two throwing stacks with durability: the merge's stat 72 rule.
25. The seed compared over each move above.

## 11. Plan 0065 Phase 1: B8, the belt on a death (run:2026-11-15-sweep8-single, `lane/n65h`)

Two sessions (seed 3, Normal, a character at life 5 of 60 with a `hbl` belt and 16 boxes filled, walked out of town
without a potion until the first hit killed it): `b8room` with page 0 empty, `b8full` with page 0 full (40 `isc`).
`sweep8_check.py b8` on each kept log: 12 boxes moved, 0 mismatches.

- [C] The corpse's `BeltOverflow` call (one per session, the corpse path's slot loop) leaves boxes 0..3 in the belt
  (their 4 items in each session) and moves boxes 4..15 out in box order: with room, to page 0 (12 of 12, as predicted, from (9,3) upward);
  with no room, to the ground (12 of 12). The statement `BeltOverflow` empties the upper rows into the inventory or
  onto the ground (`src:maxroll-death`, D2R) is held for 1.14d on this path. (fn:sub_005608C0_BeltOverflow@0x005608C0,
  fn:PLAYER_CorpseCreate@0x0057F700, run:2026-11-15-sweep8-single)

## 12. Plan 0066 batch S4e part 3: the request handlers and the pickup under emulation (run:2026-11-16-sweep2-s4e-emu)

Five families, 12 700 cases, 0 mismatches, 0 stops, 0 undeclared reads, no traced write; 16 controls, each separating,
`passed` 0 (`tools/items_s4e3_emu.py`, `workspace/logs/n66z/s4e/run3/check.txt`; record in
[experiments](experiments.md#part-3-the-item-request-handlers-and-unitinteracts-item-case-2026-11-16)). Every case runs
the handler from its entry over a declared world (the game's unit hash heads, the player, its data, path and
inventory, items, interaction partners, a room chain) to its return or to a declared callee's entry (ADR-0021: the
callee and everything after it are not covered, nor the meaning of each offset; `lane/n66z`). Each confirmed claim below holds for the
code as that map; the callees named as run are run, not observed. No import, no allocator is reached.

- [C] (ADR-0015) **`PktPosFar` (0x00548EF0)**, family `pos` (1 500, all unit types 0..7): the unit's position is the
  static path's dwords `+0x0C`, `+0x10` for types 2, 4, 5, else `PathGetX`/`PathGetY`'s `u16` at `+2`, `+6` of the
  dynamic path, 0 with no path (70); per axis `d = pos − u16(packet value)` as `i32`, negated when negative (32-bit
  `neg`, so −2³¹ stays −2³¹ and passes: 12 cases), `d > bound` signed (EBX) returns 1; both within, 0 (322 / 1 178).
  Controls `pos_unsigned` 148, `pos_ge` 145, `pos_full` (the packet dword unmasked) 72. (0x00548F4D–0x00548F6B,
  run:2026-11-16-sweep2-s4e-emu)
- [C] (ADR-0021) **The use requests to their use functions**, family `use` (3 000). `0x20` (0x0054B1E0): length 13,
  else 3 (94); `PktInvItemBad` (the guid found among type-4 units, mode 0, its ItemData `+0x5C` the player's
  inventory, else 1); `PktPosFar` with EBX 50 (`lea ebx, [eax + 0x32]`, `eax` 0) on the packet's `+5`, `+9`, else 1
  (refused 556); then `PlayerUseInvItem(guid, x, y, &flag)` (ECX game, EDX player; 354, site 0x0054B24C). `0x26`
  (0x0054B560): length 13 (87); `PktBeltItemBad` (found, mode 2, owned, else 1); `PktPosFar(50)` on the unit's own
  position read by the same rule, so it passes for every dynamic-path unit (the player): `u16(pos) = pos`; for a
  static-path unit with a coordinate above `0xFFFF` it can return 1 (control `spec_anypos`, "holds with any input",
  separates 127, none with a player); then `PlayerUseBeltItem(guid, x, y, &flag, +5)` (493, site 0x0054B62F). `0x27`
  (0x0054B280): length 9 (105); `PktOwnedItemBad` on `+1`, then on `+5` (EDI the player): not found 1; owned 0;
  else 1 unless it is the player's cursor item (control `owned_only` 26); then `PlayerUseItemOnItem(+1, +5, &flag)`
  (577, site 0x0054B2D4). Control `inv_nomode` (no mode test) 64. (fn:sub_0054B1E0_Pkt20UseInvItem@0x0054B1E0,
  fn:sub_0054B560_Pkt26UseBeltItem@0x0054B560, fn:sub_0054B280_Pkt27ItemOnItem@0x0054B280, 0x0054B222, 0x0054B602,
  run:2026-11-16-sweep2-s4e-emu)
- [I] After each use function: a return of 0 with the flag set returns 3 (0x0054B250, 0x0054B633, 0x0054B2D8). Not
  covered: the use functions' closures reach `ItemUse` and the use entries (H4c).
- [C] (ADR-0021) **`0x13` and `0x16` to `UnitInteract`**, family `act` (1 200). `0x13` (0x0054AA90): length 9, else 3;
  type `+1` as `u32` below 6, else 2; `UnitInteract(guid +5, 0, game)` with ECX the player, EDX the type (400, site
  0x0054AAC9). `0x16` (0x0054AAD0): length 13; type below 6, else 2; **type 0 with the player's own guid returns 3**
  (`noself` 48); else `UnitInteract(guid +5, action +9, game)` (340, site 0x0054AB2C); a null player compares as −1.
  Control `type_le6` 113. (0x0054AAAC, 0x0054AB10, 0x0054AB15, run:2026-11-16-sweep2-s4e-emu)
- [C] (ADR-0021) **`UnitInteract`'s item case** (EDX 4), family `pick` (2 500): the guid not found among type-4 units,
  or a mode other than 3, returns 1; `d = UnitInteractDistance(player, item)` (run, items/inventory § I2) above 50
  returns 1 (1 217 returns of 1 in all); `d` from 5 to 50 ends at `InteractWalkTo` (0x00548A50) with ECX the game,
  EDI 4 and the pushed word −2 for a non-zero action, −1 for action 0 (490, site 0x00548CDD); `d ≤ 4` enters
  `UnitsLineBlocked(player, item, 0x804)`, where the player's path mask `+0x4C` overlapping `0x804` ends at
  `UNIT_CollUnmark` (294) and a non-touching pair at `COLL_LineTest` with mask `0x804` and the shortened ends (294); a
  touching pair returns 0 and the case ends at `PickupToCursor(guid, &flag)` for a non-zero action (135, site
  0x00548CA2) or `PickupToInv` for action 0 (70, site 0x00548CB1). Controls `reach50` (`d ≥ 50` refused) 43, `reach6`
  (`d ≤ 5` to the line) 53, `mask801` 196, `actswap` 205. (0x00548C60, 0x00548C70, 0x00548C79, 0x00548C7E, 0x00548C8E,
  run:2026-11-16-sweep2-s4e-emu)
- [I] After `COLL_LineTest`: a blocked line walks (0x00548C8C → 0x00548CC5); after each pickup, the flag → 3. H4c.
- [C] (ADR-0021) **`0x17` to `CursorDrop`**, family `mv` (4 500 over three handlers; 0x17 911): length 5, else 3;
  `PktIsCursorItem` (found, mode 4, the player's cursor item, else 1; 317 returns of 1); then, **only when
  `PlayerIsBusy` is non-zero**, `InteractIsPlayer` non-zero returns 3 (121 returns of 3, the length refusals among
  them); then `CursorDrop(guid)` (473, site 0x0054AB9C). `PlayerIsBusy` is 1 for a player whenever the cursor test
  passed (it has a cursor item) and 0 for any other unit type, so a non-player's drop skips the interaction test
  (control `iip_always` 12). `InteractIsPlayer` (0x005678A0) does not read its stack argument (`static.txt`: no
  `[ebp+0x8]` in its body), so the `0` and `1` the handlers push select nothing. (0x0054AB7D, 0x0054AC4A,
  run:2026-11-16-sweep2-s4e-emu)
- [C] (ADR-0021) **`0x18` to `InvPlaceItem`** (1 776 cases): length 17, else 3; the cursor test, else 1; for a
  player, `PlayerIsBusy` is 1 in every case that passed the cursor test, so "not busy and page ≠ 0" never refuses;
  page 4 needs a room (path `+0x1C`) whose level (`+0x10` → `+0x58` → `+0x1D0`) `LevelIsTown` accepts (levels 1, 40,
  75, 103, 109 in the image's table, `static.txt`), else 3; page 2 needs `InteractIsPlayer`, else 3; pages 0 and 3
  nothing; every other page (1 and 5 up) returns 2. A non-player has only `page ≥ 5` unsigned → 2, so page 1 passes
  (16). Then the low byte of the page dword is written to ItemData `+0x45` (`ItemSetPage`) **before** the call, and the
  case ends at `InvPlaceItem(game, player, guid, x, y, 0, 1, 0)` with ECX 0x006E1050 and EDX 0xBF6 (410: pages 0 136,
  2 44, 3 118, 4 96; refused 3 on page 2 81 and on page 4 108). Controls `page_after` 331, `page1_ok` 126.
  (0x0054AC0D–0x0054AC68, 0x0054AC7E, 0x0054ACA1, run:2026-11-16-sweep2-s4e-emu)
- [I] After `InvPlaceItem`: whether a refused placement keeps that byte is its own code (part 4, `place`). *2026-11-16, § 13: refusals before `InvItemRemove` keep it, `[C]`.*
  (fn:sub_00560200_InvPlaceItem@0x00560200)
- [C] (ADR-0021) **`0x19` to `InvItemToCursor`** (1 813 cases): length 5, else 3; `PktInvItemBad`, else 1; **a
  non-empty cursor ends at `NoManaMsg` (0x00549A60)** with ECX the player (405), the return of 2 after it not covered;
  an item whose page byte is 1 returns 3; then `InvMoveInteractTest` (0x00535610), run: with the interaction flag
  (`+0x6C`) set, the partner (type `+0x68`, id `+0x64`) not found ends at `PlayerClearInteract` (139), an NPC (type 1)
  at 0x00573140 (19), a player at `TradeItemTest`, which returns 0 when the partner's PlayerData `+0x5C` is 0 and else
  ends at 0x005B5810 (18), and any other type passes; with no interaction, PlayerData `+0x4C` non-zero returns 0, else
  `TradeItemTest` passes when PlayerData `+0x50 ≤ 4` (signed). **A 0 from the test returns 0 with nothing moved** (181
  returns of 0); else `InvItemToCursor(guid, &flag, 1, 0, 0, 0)` (219, site 0x0054AD6C). Control `trade_ignored` 357.
  (0x0054AD3A, 0x0054AD4D, 0x0053568D, 0x00567834, run:2026-11-16-sweep2-s4e-emu)
- [C] (ADR-0015) `GameFindUnit` (run in every family): types 0..4 walk the chain `+0xE4` from the head at game +
  `0x006E10E0[type]` + 4 × (guid & 0x7F); **type 5 walks one list from game + `0x1B20`**, with no bucket.
  (fn:sub_00552F60_GameFindUnit@0x00552F60)
- Not covered here (S4e part 4 and on): the handlers `0x1A`..`0x1E`, `0x1F`, `0x21`, `0x23`..`0x25`, `0x63`;
  `InvItemToCursor`'s body (rows 42, 46); the use rows 21, 22, 34, 38, 52, 54. *2026-11-16: the handlers and `InvItemToCursor` to its remove are § 13.*

## 13. Plan 0066 batch S4e part 4: the other request handlers, `InvItemToCursor`, `InvPlaceItem`'s refusals, `InvPageGet`, `InvRowForUnit` (run:2026-11-16-sweep2-s4e-emu)

Six families, 17 952 cases, 0 mismatches, 0 undeclared reads, no traced write; 375 `pageget` cases stop at an
allocator guard, each where the model expects it; 19 controls, each separating, `passed` 0 (`tools/items_s4e4_emu.py`,
`workspace/logs/n66z/s4e/run4/check.txt`; record in
[experiments](experiments.md#part-4-the-other-request-handlers-invitemtocursor-invplaceitems-refusals-2026-11-16)).
Part 3's world (§ 12) plus the inventory's page array (`+0x14`, count `+0x18`), the body page's cells, the item list
(`+0x0C`; each ItemData `+0x64` the next, `+0x69` the location byte) and Items/ItemTypes/inventory rows declared as
`tools/item_emu2.py` declares them. Every case runs from the function's entry to its return or a declared callee's
entry (ADR-0021: the callee and what follows are not covered; `lane/n66z`). The callees named as run are run, not
observed. No import is reached; the only allocators reached are `InvPageGet`'s, as guards.

- [C] (ADR-0021) **`0x1A`..`0x1E` to their functions**, family `body` (3 000). `0x1A` (0x0054AD90), `0x1B`
  (0x0054AE30), `0x1D` (0x0054AF50), `0x1E` (0x0054B030): length 9, else 3; `PktIsCursorItem` on `+1`, else 1; the
  slot is the byte at `+5`, and `s − 1 > 9` unsigned returns 2 (control `slot_signed` 95). `0x1C` (0x0054AEC0): length 3,
  the slot the `u16` at `+1`, no guid. Then: `0x1A` → `ItemEquip(guid, slot, 0, &out)` (167, site 0x0054ADFC); `0x1B` →
  `EquipCursorAtSlot(guid, slot, 0, &out)` (137, site 0x0054AE95); `0x1C` → `InvMoveInteractTest` (0 returns 0; its
  boundaries as § 12's `0x19`), then `BodyToCursor(slot, 0, &out)` (151, site 0x0054AF30); `0x1D` → the slot's item by
  `InvGetBodyLocItem` (page 0 by `InvPageGet` with the image's 13 × 1 row at `0x0074479C`), none returns 1 (control
  `nobody_ok` 171), slot 8 then `TradeBeltLock` (0 returns 0; control `no_lock` 5), `InvMoveInteractTest`, then
  `BodySwapCursor(guid, slot, 0, &out)` (49, site 0x0054B00B); `0x1E` → a slot other than 4 or 5 returns 3 (control
  `swap2_any` 238), no item at it returns 1, `InvMoveInteractTest`, then `BodySwapCursor2(guid, slot, &out)` (17, site
  0x0054B0CE). ECX the game, EDX the player at each. (0x0054ADCE, 0x0054AED7, 0x0054AF07, 0x0054AFC2, 0x0054B084,
  0x0054B089, run:2026-11-16-sweep2-s4e-emu)
- [C] (ADR-0021) **`0x1A`'s slot argument is a dword whose bits 8..31 are the frame's old bytes**: the handler stores
  the byte at `[ebp−4]` and pushes the dword; 68 of the 167 calls had non-zero high bits. `0x1B`, `0x1D`, `0x1E` reuse
  the length's dword (9), so their high bits are 0. What `ItemEquip` reads of it is after the boundary, `[I]`.
  (0x0054ADBB, 0x0054ADE1, run:2026-11-16-sweep2-s4e-emu)
- [I] `TradeBeltLock` (0x00567840) as run: with the interaction flag set and type 0, a listed item whose location byte
  is 2 returns 0, else 1. `0x1C`'s slot-8 test comes after `InvMoveInteractTest`, which with an interaction of type 0
  returns 0 or ends at `TradeItemTest`'s boundary 0x005B5810, so no case reaches it; it stays a reading. (0x0054AF07,
  0x00567876, 0x0063E043)
- [C] (ADR-0021) **`0x1F`, `0x21`..`0x25`, `0x63` to their functions**, family `req` (4 000). `0x1F` (0x0054B0F0):
  length 17; `PktIsCursorItem` on `+1`, `PktInvItemBad` on `+5`; that item's page 1 or 2 returns 3 (control
  `page12_ok` 29); `InvMoveInteractTest`; `PageSwapCursor(+1, +5, +9, +0xD, &out)` (44, site 0x0054B1AC). `0x21`
  (0x0054B300): length 9; `PktOwnedItemBad` on `+1`, then `+5`; equal guids return 3 (control `same_ok` 335);
  `StackRequest(+1, +5, &out)` (112, site 0x0054B352). `0x22` (0x0054B380): length 5; `PktOwnedItemBad`; the stub
  0x0055E9A0 (255). `0x23` (0x0054B3E0): length 9; `PktIsCursorItem`; `ItemToBelt(+1, +5, 0, &out)` (231, site
  0x0054B428). `0x24` (0x0054B450): length 5; `PktBeltItemBad`; `InvMoveInteractTest` with an item of 0; then a
  non-empty cursor returns 2 (control `cursor_first` 140); `BeltToCursor(+1, &out)` (80, site 0x0054B4B8). `0x25`
  (0x0054B4E0): length 9; `PktIsCursorItem` on `+1`, `PktBeltItemBad` on `+5`; `BeltSwapCursor(+1, +5, &out)` (48, site
  0x0054B536). `0x63` (0x0054D520): length 5; `PktInvItemBad`; a non-empty cursor ends at `NoManaMsg` (226; the 2 after
  it not covered); the item's ItemTypes `+0x19` 0 returns 2 (control `beltable_ignored` 73); a page byte ≠ 0 returns 3
  (control `page_any` 100); `BeltFreeSlot(inventory, item, &slot)` (63, site 0x0054D5C4). Each wrong length returns 3.
  (0x0054B0F9, 0x0054B16B, 0x0054B33E, 0x0054B383, 0x0054B3E3, 0x0054B47C, 0x0054B48E, 0x0054B4E3, 0x0054D526,
  0x0054D58E, 0x0054D598, run:2026-11-16-sweep2-s4e-emu)
- [I] After each function: a return of 0 with `out` set returns 3, else 0 (each handler's tail); `0x63` after
  `BeltFreeSlot`: a slot below 0 returns 0, then `InvMoveInteractTest`, `InvTakeItem` and `BeltPutItem` (0x0054D5C6,
  0x0054D628, 0x0054D6E3). Not covered.
- [C] (ADR-0021) **`InvItemToCursor` (0x00560420) to `InvTakeItem`**, family `tocur` (1 500; ECX game, EDX player,
  `guid, &out, a3, a4, inventory, force`): `out ← 0`; the inventory is the argument or else the player's; a non-empty
  cursor returns 0 unless `force` (`+0x1C`) is non-zero (control `force_ignored` 639); a guid not found sets `out` to 1
  and returns 0; for a type-0 user, `PlayerIsBusy` 0 with a page byte ≠ 0 sets 1 (control `busy_ignored` 69); a mode
  ≠ 0 sets 1 (control `mode_any` 125); then `InvClearUseMarks` (run, no flagged item), the item's `+0xC4` bit 1
  cleared (dumped) and `InvTakeItem(inventory, item)` (575, site 0x00560535). A type-1 user skips the busy test.
  (0x00560465, 0x0056048D, 0x005604CB, 0x005604DC, 0x005604F9, 0x00560527, run:2026-11-16-sweep2-s4e-emu)
- [C] (ADR-0021) **`InvPlaceItem` (0x00560200) as `0x18` calls it**, family `place` (2 500; `x, y, 0, f20, 0`, the item
  on the cursor in mode 4 with the page byte written): `InvClearUseMarks` (run); a guid not found or a mode ≠ 4 returns
  0; `InvRowForUnit(player, page, game+0x70)`; the direct branch clamps a negative `x`, `y` (signed) to 0 (control
  `noclamp` 522); `0x0063BCC0` → `InvGridPut(x, y, page + 2, row)`: an item with no ItemData returns 0 first, then
  `InvRecordGrid`'s row, `InvPageGet`'s size refusal, the bound and cell tests (§ 2); a fit ends at `InvItemRemove` (544,
  site 0x0063B138). **No refusal before `InvItemRemove` writes the page byte** (1 956 refusals, the byte dumped after
  each; control `page_reset` 2 290). (0x00560259, 0x005602E5, 0x005602EE, 0x0063B003, run:2026-11-16-sweep2-s4e-emu)
- [C] (ADR-0015) **`InvPageGet` (0x0063ADD0)**, family `pageget` (1 000; EAX the page, EDI the inventory, the row
  pointer on the stack): `page < count` is signed and the entry is `pages + (page << 4)` wrapping, so `0x80000000` names
  page 0 (control `unsigned_idx` 138); with no row, the entry if its cells exist, else 0; with a row, a made page of
  another size returns 0 (control `size_ignored` 93), a page not made reaches the allocator `0x0040B430` (68 guard
  stops) and a page at or above the count the reallocation `0x0040B4B0` (307). (0x0063ADDA, 0x0063AE53, 0x0063AE5A,
  run:2026-11-16-sweep2-s4e-emu)
- [C] (ADR-0015) **`InvRowForUnit` (0x00621050)**, family `rowfor` (5 952): every page byte (as a byte: control
  `page_dword` 28) for player classes 0..7 and two others with both expansion words, and types 1..6 and two others over
  13 classes. Returns: −1, 0..4, 14, 15 (the class table `0x00744544`, 7 entries, .data, named by three loads and no
  store in `.text`, `static.txt`), 5 (type 1), 6, 7, 9, 8 or 12 (page 4: control `stashsmall` 10), 10, 11 (type 2,
  class `0x152`, `0x153`). **13 and 29 are never returned.** (fn:sub_00621050_InvRowForUnit@0x00621050,
  run:2026-11-16-sweep2-s4e-emu)
- Not covered here (S4e part 5): the use rows 21, 22, 34, 38, 52, 54; the `put`, `search`, `merge`, `drop`, `ground`,
  `expiry` and belt families (inventory 20, 22, 25–27, 47, 48, 55, 57, 58, 63, 67, 81, 84, 87, 98); what follows
  `InvTakeItem`, `BeltFreeSlot` and `InvItemRemove`; `InvGridFree`.

## 14. Plan 0066 batch S4e part 5a: the search on full pages and in sequence, `InvGridFree`, the belt tests, `BeltPutItem`, the ground expiry's quality 9 and the quest call (run:2026-11-16-sweep2-s4e-emu)

Eight families, 10 633 cases, 0 mismatches, 0 stops, 0 undeclared reads, no traced write; 22 controls, each
separating, `passed` 0 (`tools/items_s4e5_emu.py`, `workspace/logs/n66z/s4e/run5/check.txt`; record in
[experiments](experiments.md#part-5a-the-search-on-full-pages-and-in-sequence-invgridfree-the-belt-tests-beltputitem-the-ground-expiry-and-the-quest-call-2026-11-16)).
The cases are built on `tools/item_emu2.py`'s world (search, seq, gridfree, holds, autobelt, beltput; its regions
zero-filled before every case) and `tools/item_emu3.py`'s (expiry, ground), unchanged. Every case runs from the
function's entry to its return or a declared callee's entry (ADR-0021; `lane/n66z`). No import and no allocator is
reached (the allocator entries are guards; none is hit).

- [C] (ADR-0015) **A player's search fails only where no spot fits**, family `search` (3 000 on full, near-full and
  one-hole pages, every owner kind). Of the 1 747 player cases, the 779 with a free rectangle of the item's size inside
  the page (an enumeration that does not use the search's orders) all return 1, 191 of them at a spot scoring below
  255; the 968 without one all return 0; no other. The control `noedge` (the page's edges uncounted, under which a
  free spot can score 0 and a best of 0 refuses) separates 91, `firstall` 96. (fn:sub_0063B490_InvSpotFindRow@0x0063B490,
  fn:sub_0063B850_InvSpotFindBySize@0x0063B850, run:2026-11-16-sweep2-s4e-emu)
- [C] (ADR-0015) **The search in sequence**, family `seq` (733 cases in 62 sequences; each case's page is the earlier
  placements, each item its own cell pointer; 60 sequences end at a refusal). The worked example's two sequences on an
  empty 10 × 4 player page emulate as `(9, 3)`, `(9, 2)`, `(9, 1)`, `(9, 0)`, `(8, 3)` for five 1 × 1 items and `(0, 0)`,
  `(9, 0)`, `(2, 0)`, `(0, 3)` for 2 × 3, 1 × 4, 2 × 2, 1 × 1. Controls `firstall` 277, `geq` 301, `h1general` 205.
  (fn:sub_0063B850_InvSpotFindBySize@0x0063B850, run:2026-11-16-sweep2-s4e-emu)
- [C] (ADR-0015) **`InvGridFree` (0x0063A8A0) tests no bound**, family `gridfree` (1 500; EAX the page, ECX the row,
  DL the width, then the column and the height on the stack, `ret 8`). It tests cell `row × gridX + column` (the
  page's byte `+8`, cells at `+0xC`) for every cell of the rectangle, rows and columns compared signed, and returns 0 at
  the first occupied one, else 1; a zero width or height returns 1. Of the 879 rectangles reaching outside the page,
  288 return 1. Controls `bounded` 578, `clip` (outside cells free) 435, `colwrap` 183. (0x0063A8AC, 0x0063A8D6,
  run:2026-11-16-sweep2-s4e-emu)
- [C] (ADR-0015) **`BeltHoldsSameGroup` (0x0063C560) returns 0 or 1**, family `holds` (1 500; inventory, item): 0 for a
  bad signature, a non-item, `isc` or `tsc` (the codes `0x20637369`, `0x20637374`), or a belt page made at another size
  than the image's 16 × 1 row `0x007447B4`; else 1 when one of boxes 0..3 holds an item of the same class or the same
  potion list (`PotionSameGroup` 0x00628A40), else 0: 351 and 1 149. Controls `allboxes` 192, `nogroup` 262, `tsc_ok` 13.
  (0x0063C59C, 0x0063C5A3, 0x0063C5DA, run:2026-11-16-sweep2-s4e-emu)
- [C] (ADR-0015) **`ItemAutoBeltTest` (0x00628BA0) returns 1 for every item it accepts**, family `autobelt` (1 200;
  inventory, item): a row with `autobelt` (Items `+0x131`) returns 1; any other compares `BeltHoldsSameGroup`'s 0 or 1
  with −1 and returns 1 (1 173 in all). A null item, a non-item or a row past the table's count ends at the error
  routine 0x00408090 (27; lines 0x9A6, 0x9A7, 0x9A9). Controls `holds_ret` 315, `auto_only` 359. With the pickup's
  branch read by objdump (0x00563716 the call, 0x0056371B `test eax, eax`, 0x0056371D `je`, 0x00563728 `BeltPlace`),
  the branch past a beltable test always calls `BeltPlace`. (0x00628BEA, 0x00628BFD, 0x00628C09, 0x00563716,
  run:2026-11-16-sweep2-s4e-emu)
- [C] (ADR-0021) **`BeltPutItem` (0x0063C4F0) to `InvItemRemove`**, family `beltput` (1 500; inventory, item, box).
  It refuses a non-item, a type whose ItemTypes `+0x19` is 0, a size other than 1 × 1, a box above 15 as unsigned
  (−1 and `0x80000000` among them; 0x0063C4D0 `cmp ecx, 0xf; ja`), and through `InvGridPut(box, 0, 1, 0)` a bad
  signature, a belt page made at another size than 16 × 1, or an occupied box; otherwise it reaches `InvItemRemove`
  0x0063AAF0 with ECX the item (351, return 0x0063B138). The worn belt's `numboxes` is not tested (control `numboxes`
  183); `signed_box` 254, `size_any` 17. `ItemToBelt`'s own steps before it are not on this route.
  (fn:sub_0063C4F0_BeltPutItem@0x0063C4F0, 0x0063C4C0, run:2026-11-16-sweep2-s4e-emu)
- [C] (ADR-0015) **Quality 9 adds 45 000**, family `expiry` (800, quality 9 weighted): 190 of 190 non-quest quality-9
  cases; a quest base gives 0 first (26). Controls `q9plain` 166, `q9as4` 190. That no stock path makes a quality-9
  item stays `[I]` (a reading of the item creation's quality writers, not run). (fn:sub_00558A10_ItemGroundExpiry@0x00558A10,
  run:2026-11-16-sweep2-s4e-emu)
- [C] (ADR-0021) **`ItemPlaceOnGround`'s quest call is last**, family `ground` (400; ECX the game, EDX the flag; item,
  room, x, y). With a room and a flag of 1, `0x100` or `0xFFFFFFFF`, it reaches `QUESTS_RaiseItemDropped` 0x00543DB0
  (ECX the game, the item pushed, return 0x00558B2B; 310) with the cell's `0x200`, the path's room and cell, mode 3,
  `+0xC4` and the expiry already written (controls `raise_first`, `flag_ignored` 310 each); a flag of 0 returns with the
  same writes (60). After the call only `pop esi`, `pop ebx`, `pop edi` and `ret 0x10` (0x00558B2B..0x00558B31, objdump).
  A null room returns with nothing written and no call, the flag set or not (35; `null_raises` 30).
  **Refinement:** `+0xC4` ends `| 0x2001003`: bit 0 is set by `UNIT_SetMode` (0x006246B3, 0x006246E3), called with mode 3
  at 0x00558AEC, beside the function's own `0x1002` and `0x2000000` (control `nomodebit` 365).
  (fn:sub_00558AA0_ItemPlaceOnGround@0x00558AA0, 0x00558B1F, 0x00558B26, run:2026-11-16-sweep2-s4e-emu)
- **Moved, not run:** `CursorDrop` with a full surround and its null-room test (inventory rows 63, 81's remainder)
  lie after `GroundDropCell`'s field-state allocation from the shared pool (0x00555DEA → 0x0064DEE8), so ruling R2
  sends them to the harness (H4d). `[I]` here. (0x00563C96, 0x00563C9B)

## 15. Plan 0066 batch S4e part 5b: the Blood Golem's heal, the doubling draw, kind 3's return and `StackRequest` (run:2026-11-16-sweep2-s4e-emu)

Four families, 8 600 cases, 0 mismatches, 0 stops, 0 undeclared reads, no traced write; 16 controls, each separating,
`passed` 0 (`tools/items_s4e6_emu.py`, `workspace/logs/n66z/s4e/run6/check.txt`; record in
[experiments](experiments.md#part-5b-the-blood-golems-heal-the-doubling-draw-kind-3s-return-and-stackrequest-2026-11-16)).
`golem`, `double` and `potret` are built on `tools/use_emu.py`'s world (its regions zero-filled before every case),
`stackreq` on `tools/items_s4e3_emu.py`'s units with `tools/item_emu2.py`'s tables, all unchanged. Every case runs from
the function's entry to its return or a declared callee's entry (ADR-0021; `lane/n66z`). No import and no allocator is
reached (the allocator entries are guards; none is hit). These are items/use rows (§§ F, H of
[items/use](../../specs/items/use.md)) beside the inventory row 58; items/0012 §§ 5, 6 carry dated notes.

- [C] (ADR-0021) **`v = 0` sets the golem to full in `GolemHealShare`, not in `GolemHeal`**, family `golem` (1 200).
  `GolemHealShare` (0x005C6870; ECX the game, EDX the user, `v` on the stack) with a user, a pet of type 3 whose unit is
  of type 1 and class `0x122`, and `v = 0` calls `UnitSetStat(golem, 6, UnitGetMaxHp(golem), 0)` from its own branch
  (0x005C68AC → 0x005C68F0, return 0x005C6901; 190 of 190; control `v0_as_heal`, `v = 0` passed to `GolemHeal`,
  separates 190). For `v ≠ 0` the share `trunc(i32(p · v) / 100)` goes to `GolemHeal` (EAX the share, EBX the golem),
  which returns 0 with no call for a share ≤ 0 (`GolemHealShare` then returns `v`; 158 positive and 53 negative `v`
  return `v`, these counts holding also the cases with a null user or a MonStats row of −1, and 8 with `v = 0` and a null user), else
  calls `UnitSetStat(golem, 6, e, 0)` (return 0x005C5F47) with `e = i32(life + share)` lowered to the maximum when
  `e > max` as signed (193 positive `v`; with a negative percent a negative `v` heals too, 6). `GolemHeal` called
  directly: 92 with `v = 0` and 137 with `v < 0` return 0, 137 with `v > 0` reach the set (control `heal0_full` 156).
  No pet, a pet of another class or a pet unit not of type 1 return `v` (86, 71, 69). Controls `nocap` 142,
  `cap_unsigned` 147: the compare is signed, so a sum that wraps past `2³¹ − 1` is stored as the negative value, not
  capped. After the set, `[I]`: `GolemHealShare` returns `esi` (0 on the `v = 0` branch, 0x005C6901) or `v` less the
  heal's return (0x005C68E6), and `GolemHeal` returns the share it applied (0x005C5F48). **Refinement** of items/use H5
  (the anchor: the `v = 0` rule is 0x005C68AC's branch; `GolemHeal`'s own `v ≤ 0` returns 0, 0x005C5F13).
  (fn:sub_005C6870_GolemHealShare@0x005C6870, fn:sub_005C5F10_GolemHeal@0x005C5F10, 0x005C5F30, run:2026-11-16-sweep2-s4e-emu)
- [C] (ADR-0021) **The doubling draw's rule at each `(r1, r2)`**, family `double` (3 000; kind 3, one slot of stat 6 or
  8, `len` 0, the seed built so the two draws give a chosen `r1 < n` and `r2 < 100`, at and around `r2 = r1 >> 1`; 146
  distinct `n`): the amount at `UnitAddStat` is doubled exactly when `r2 < r1 >> 1` — players 852 doubled at `r2 < r1 >> 1`,
  780 not at `r2 = r1 >> 1`, 563 not above; non-players (type 1) 170, 139, 106. 379 cases have `r1 >> 1 ≥ 100`, where
  every `r2` doubles, which is the formula's `min(100, r >> 1)`. Controls `le` 919, `half` (`r2 < r1`) 777, `swap` (the
  100-draw first) 975, `nodraw_nonplayer` 170. A user whose stat (vitality for life, energy for mana) is 0 or negative
  makes no draw and keeps its seed: 293 non-players at 0, 97 cases at −1 or −100 (players and non-players). So the
  chance for `n ≥ 1` is the share of `(r1, r2)` pairs with `r2 < r1 >> 1`, `Σ min(100, r >> 1) ÷ (100 n)` over `r < n`
  (2.00 % at 10, 5.76 % at 25, 12.00 % at 50, 24.50 % at 100, 37.00 % at 150, 40.75 % at 165, 49.50 % at 200, 79.80 % at
  500; `check.txt`). **Refinement:** each pair is as likely as `low mod n` and `low mod 100` of the generator make it,
  so the formula is the uniform-pair count, not a property of the LCG run here. (fn:sub_005BE3F0_ItemUsePotion@0x005BE3F0,
  0x005BE514–0x005BE53B, run:2026-11-16-sweep2-s4e-emu)
- [C] (ADR-0021) **Kind 3 returns 0 for every amount at or below 0**, family `potret` (2 400; zero and negative calcs,
  and positive ones the class scale, the doubling or the shift takes to ≤ 0 as `i32`). 1 200 cases outside a bad state
  or a missing record reach the return with 0: 972 where every calc is ≤ 0 and 228 where a positive calc became ≤ 0.
  274 return 1 with no callee reached: a refill whose slot 0 is ≤ 0 and whose later slot is positive with `len + rem ≤ 0`
  (control `applied_only`, such a slot not counting, separates 274). A bad state returns 0 (199), a missing record 0
  (204). The rest end at the first callee as `use_emu`'s families did (`UnitAddStat` 209, `STATLIST_Alloc` 48,
  `UnitQueueEvent` 39, `STATLIST_SetStat` 214, `GolemHeal` 13). Control `unsigned_amount` (a negative amount taken as
  positive) 1 021. Stays `[I]`: the 1 after a slot reached `UnitAddStat` or `STATLIST_SetStat` (0x005BE6D4 writes it
  after the call returns; the callees' closures were not run). (0x005BE6D4, 0x005BE73D, fn:sub_005BE3F0_ItemUsePotion@0x005BE3F0,
  run:2026-11-16-sweep2-s4e-emu)
- [C] (ADR-0021) **`StackRequest` (0x0055E7C0) to `StackMerge`**, family `stackreq` (2 000; ECX the game, EDX the player;
  guid 1, guid 2, `&out`). `out ← 0`, `InvClearUseMarks(player)`; equal guids set `out` to 1 and return 0 (110); a
  guid with no unit sets 1 and returns 0 (91 the first, 91 the second); **a unit found that is not of type 4 returns 0
  with `out` clear** (205, `nonitem_flag` separates 205); the second item on page 2 sets 1 and returns 0 (212); the first
  item's page is not tested (`page_first` 320) and other pages of the second pass (`page_any` 806); `ItemsCanStack`
  false returns 0 with `out` clear (875; `nostack_flag` 875); else `StackMerge(game, first)` with ESI the second, EBX the
  player (416, return 0x0055E8B1). `same_ok` 110, `miss_noflag` 182. After, `[I]`: flag `0x100` on the second, its
  update queued, the player marked, return 1 (0x0055E8B1..0x0055E8D2). The class compare at 0x0055E8A3, which returns 1
  with nothing merged, follows `ItemsCanStack`'s own compare of the same two `+4` words (0x0062C873, `je` 0x0062C875), so
  no case reaches its unequal branch: `[I]`, a reading. **Refinement** of items/inventory G4 (the non-item). 
  (fn:sub_0055E7C0_StackRequest@0x0055E7C0, 0x0055E819, 0x0055E88E, run:2026-11-16-sweep2-s4e-emu)
- **Moved, not run:** `StackMerge` after its first `UnitSetStat` (inventory row 57). Every branch sends a stat message
  before its later writes: `PlayerGetClient` (0x0055E63E) and 0x0053D130 (0x0055E647; also 0x0055E68E, 0x0055E71E,
  0x0055E75B), which queues the packet through `ClientQueuePacket` 0x0053B280 (0x0053D200); with no room in the client's
  current buffer (`+ len > 0x200`, 0x0053B2A4) and none on its free list (`+0x1C0`), that allocates (0x0040B430 at
  0x0053B2DD). Ruling R2 sends the claim to the harness (H4d). `[I]` here. (0x0055E647, 0x0053B2DD)

## 16. Plan 0066 batch S4e part 5c: the mercenary button, `ItemUse` after its entries, `ItemSkillQtyAdjust`, and the routes past `InvItemRemove` (run:2026-11-16-sweep2-s4e-emu)

Three families, 8 000 cases, 0 mismatches, 0 stops, 0 undeclared reads, no traced write; 18 controls, each separating,
`passed` 0 (`tools/items_s4e7_emu.py`, `workspace/logs/n66z/s4e/run7/check.txt`; record in
[experiments](experiments.md#part-5c-the-mercenary-button-itemuse-after-its-entries-itemskillqtyadjust-and-the-routes-2026-11-16)).
`merc` is built on `tools/items_s4e3_emu.py`'s world, `c2` on `tools/use_emu.py`'s world with
`tools/items_s4e6_emu.py`'s `potret` cases, `qty` on `tools/use_emu.py`'s world, all unchanged. Every case runs from the
function's entry to its return or a declared callee's entry (ADR-0021; `lane/n66z`). No import and no allocator is
reached (the allocator entries are guards; none is hit). The rows are items/use 21, 22 (items/0012 §§ 1, 2 carry dated
notes) and items/inventory 25–27.

- [C] (ADR-0021) **The mercenary button's request**, family `merc` (3 000). `Pkt61MercItem` (0x0054D430; ECX the game,
  EDX the player, packet, length) returns 3 for a length ≠ 3 (control `len_ignored` separates 153) and for
  `game+0x70` = 0 (`exp_ignored` 431); returns 3 when `PlayerIsBusy` and `InteractIsPlayer` are both non-zero
  (`iip_ignored` 140); returns 0 for a used skill, the skill block at `player+0xA8` with a non-zero `+0x10`
  (`UNIT_GetUsedSkill`; a block whose `+0x10` is 0 passes, `skill_any` 88), and for a dead player (`UnitIsDead`:
  `+0xC6` bit 0, or a player in mode 0 or 17; `pdead_ignored` 74); asks `PETS_GetUnitOfType(game, player, 7, 0)`, which
  takes type 7's list only when the pet-type count (data tables `+0xBF0`) is above 7 and returns the unit of the first
  node whose bit 0 is clear (`pet_first` 40), and returns 0 with none or with a dead pet (a monster in mode 0 or 12, or
  bit 0 of `+0xC6`; `petdead_ignored` 64); returns 0 unless `0x0065A590(pet, player)` finds the pet's room in the
  player's room's near list (`[room]` the array, `[room+0x24]` the signed count; a null room fails; `spec_noroom` 107);
  returns 3 with no inventory (`player+0x60` = 0); with no cursor item, a non-zero `u16` at `+1` calls
  `0x0054D130(player, u16)` (EBX the game; 30) and 0 returns 0; a cursor item whose Items row has the quest byte
  (`+0x12A`) returns 0 (`quest_ignored` 52); else `MercGiveCursorItem` (0x0054D230; EAX the item, ECX the pet, the game
  and the player on the stack; 122). Outcomes: 813 returns of 3, 2 035 of 0, 30 and 122 at the two callees.
  **Refinements** of items/use B (`0x61`): the busy-and-player test, the pet's room near the player's, the inventory
  test, the no-cursor branch to `0x0054D130`, the first-free-node rule; "used skill" is the block's `+0x10`. After the
  two callees, `[I]`. (fn:sub_0054D430_Pkt61MercItem@0x0054D430, 0x0054D4B8, 0x0054D4E9, fn:PETS_GetUnitOfType@0x00574EC0,
  0x00574F05, 0x0065A5F5, 0x00628D19, run:2026-11-16-sweep2-s4e-emu)
- [C] (ADR-0021) **`ItemUse` after its entries**, family `c2` (2 500), the entries run, not declared (ruling R2).
  Kind 1's test (0x005BE130) on a book or scroll with flag 4 clear and no Books row for its suffix returns 1 without a
  message, and `ItemUse` returns 0 with no call of `InvClearUseMark` (349; control `clear_on_test` separates 349); with a
  Books row the test sends its message (0x0053D220, 223) and with flag 4 set kind 1's use is called (182). Kind 3's use
  (0x005BE3F0) on `items_s4e6_emu.py`'s `potret` worlds: a use returning 0 calls `InvClearUseMark` (0x005BE1C0, return
  0x005BF395; 1 123; `no_clear` 1 123), a use returning 1 makes `ItemUse` return 1 (192; `use_ret0` 192), and the rest
  end at kind 3's callees as in § 15 (431). Flag 4 is set before the use or the test in all 2 095 cases that reach one
  (dumped). **Not met:** a test returning 0 (kind 1's test returns 1 on both its paths, 0x005BE16F, and no other kind has
  a test) and a use return other than 0 or 1. After `InvClearUseMark`, `[I]`: message `0x7C` goes through
  `SendUnitPacket6` (0x005BF345, 0x005BF3B1) → `ClientQueuePacket` (0x0053B3EE), which can allocate (0x0040B430 at
  0x0053B2DD; ruling R2 → H4c). (fn:sub_005BF240_ItemUse@0x005BF240, fn:sub_005BE130_ItemUseIdentifyTest@0x005BE130,
  0x005BF320, 0x005BF38C, 0x005BF3B6, run:2026-11-16-sweep2-s4e-emu)
- [C] (ADR-0021) **`ItemSkillQtyAdjust`**, family `qty` (2 500: 2 004 direct calls with EAX the item, EDI the unit,
  `add` on the stack; 496 through `ItemSkillQtyAdd`). The skill is Books `+8` for an item of type 22 (also when it is of
  type 18 too), Books `+0xC` for type 18, else −1, and −1 (or no Books row) returns 0 (`swap_books` 790). `q` is stat 70
  of the item when non-zero, as it is (a negative stat 70 is used negative; `spec_max` 127); stat 70 = 0 returns 0 for a
  tome (`tome0_adds0` 164) and gives 1 for any other item (`nontome0_zero` 113). The unit's skill is found by id with
  owner word `+0x34` = −1. `add ≠ 0`: a missing skill calls `UnitAddStat(unit, 5, q, 0)` (return 0x0055C17B; 837 with
  `0x00570080` after it unrun), else the quantity becomes `i32(qty + q)`; `add = 0`: a missing skill reaches the error
  routine with line `0x230` (184), else `i32(qty − q)` floored at 0 (`noclamp` 25). The quantity is written to the
  skill's `+0x30` (`0x00645120`) and the message builder `PlayerGetClient` is reached with `0x234`, the unit's id, the
  skill and the quantity (309). The item's page byte is not consulted: page 4 gives the same outcomes (`page4_nothing`
  341). `ItemSkillQtyAdd` (0x0055C270) calls it with `add = 1` for a player only; another unit type returns at once (154).
  **Refinements** of items/inventory C2: a tome with stat 70 = 0 returns 0 before the skill is looked up (0x0055C13E);
  `q` is stat 70 itself, not `max(stat 70, 1)`; a scroll that is also a tome uses `+8`. After the message builder,
  `[I]`: the send (`0x0053C520` → `ClientQueuePacket`), the left and right skill resets, the grant at `0x00570080`, and
  the return of 1 (0x0055C24E). (fn:sub_0055C110_ItemSkillQtyAdjust@0x0055C110, fn:sub_0055C270_ItemSkillQtyAdd@0x0055C270,
  fn:sub_0055BFF0_ItemBookSkill@0x0055BFF0, 0x0055C14E, 0x0055C1D7, 0x0055C20C, run:2026-11-16-sweep2-s4e-emu)
- [C] (static, `sites.txt`, objdump direct-call closures) **The routes that cross an allocator**, read by the tool's
  `sites` command (19 roots, 102 calls whose closure reaches an allocator entry or an import; the error routine's
  branches and the stack-cookie report 0x006889D6 not followed): (1) `InvItemRemove` 0x0063AAF0 calls `0x006277F0` at
  0x0063ABA4 whenever the inventory has an owner, which unlinks the item's stat list (`STATLIST_Unlink` 0x006269F0) and
  recomputes the owner's (`StatRecompute` 0x006266C0 at 0x00626B24 → `STATLIST_CacheWrite` 0x00625150 →
  `STATLIST_InsertEntry` 0x00624C80 → 0x0040B4B0), with an indirect callback at 0x00626BE7; `InvGridPut` reaches it at
  0x0063B133, `InvPlaceSocketed` at 0x0063B26E, `InvTakeItem` through it, the `0x63` handler at 0x0054D628; (2)
  `PlayerUseInvItem` and `PlayerUseBeltItem` call `InvClearUseMarks` 0x0055BF50 at their entry (0x0055E1C1, 0x005623E1),
  before the `useable` gate, and it reaches `ClientQueuePacket` → 0x0040B430; (3) `UnitAddStat` (0x006272CA → 0x00627030)
  and `STATLIST_SetStat` (0x00627167 → 0x006270B0) reach `STATLIST_InsertEntry` → 0x0040B4B0. Ruling R2 sends what
  lies past them to the harness: items/inventory 20, the remainders of 25, 26, 27, 39, 42 and 45/99 (H4d), items/use 54
  and the remainders of 22 and 34 (H4c). (0x0063ABA4, 0x00626B24, 0x00626BE7, 0x0063B133, 0x0055E1C1, 0x005623E1,
  run:2026-11-16-sweep2-s4e-emu)

## Data touched

tbl:Inventory.txt:gridX, tbl:Inventory.txt:gridY, tbl:Belts.txt:numboxes, tbl:Armor.txt:belt, tbl:Misc.txt:autobelt, tbl:Misc.txt:stackable, tbl:Misc.txt:invwidth, tbl:Misc.txt:invheight, tbl:ItemStatCost.txt:Stat, tbl:ItemTypes.txt:Beltable, tbl:ItemTypes.txt:AutoStack.

## Dead ends

- `0x0063B790`, `0x0063B7D0`, `0x0063B810` read as size-specific searches: they are one body three times.
- An emulated image keeps writes between cases: a null owner must be written, or an earlier case's owner is read (`dev-2`'s `search` family: 105 mismatches when rechecked with the final checker, all owner null; the 523 of experiments.md was the whole development checker's count before its other two faults were fixed, and no check output of it was kept).

## Open questions

- `[L]` A box past `numboxes` by `0x23`: does it stay, and does a smaller belt's overflow take it? Phase 2 case 14.
- `[L]` Whether `0x18` to page 4 has any "stash open" test: none in the handler, `InvPlaceItem` or `0x0055C110` as read (items/0014 § 5); Phase 2 case 7 is a crafted request.
- `[L]` Who writes `0x007A5218`, the client's set: UI, out of scope (ADR-0025).
- Closed by items/0014 § 5: `0x00622B50`'s test and `0x00641530`'s distance in pickup, `ItemAutoEquipSlot`'s tail, the fate of a pickup-merge remainder.
