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
- [C] (ADR-0015) **`gridX` and `gridY` are read as bytes.** With `+0x12`, `+0x13` declared `0x7F`, a wider reading fails 2 465 of 4 000 search cases, and the bound test too (`put`). (fn:sub_0063ADD0_InvPageGet@0x0063ADD0, fn:sub_0063AFD0_InvGridPut@0x0063AFD0, run:2026-11-04-inventory-emu)
- [C] (ADR-0015) **The belt search.** Only a beltable 1 × 1 item. For each bottom box 0..3 that holds an item of the same class or the same list (`hp1..5`, `mp1..5`, `rvl`/`rvs`), the first free box up that column (`box, box + 4, …` below `numboxes`). Then, with `autobelt`, the first free box of 0..3. Else it returns 0. (fn:sub_0063C600_BeltFreeSlot@0x0063C600, fn:sub_00628A40_PotionSameGroup@0x00628A40, run:2026-11-04-inventory-emu)
- [C] (ADR-0015) **Stacks.** Two items can stack when class, quality and file index are equal, the row is stackable (`+0x132`), ethereal status is equal, quality is not 0 and not 4..9, stats 21, 22, 23, 24, 159, 160 are equal, and the low byte of stat 194 is 0 on both. (fn:sub_0062C850_ItemsCanStack@0x0062C850, run:2026-11-04-inventory-emu)
- [C] (ADR-0021) **A merge** with `source + target` above the maximum sets the target to the maximum; else a durable source below the target's stat 72 first lowers the target's stat 72; else the target takes the sum. The maximum is Items `+0xE8` + stat 254, and 511 when that exceeds 510. After the first `UnitSetStat`, `[I]`. (fn:sub_0055E590_StackMerge@0x0055E590, fn:ITEMS_GetMaxStack@0x006295B0, run:2026-11-04-inventory-emu)
- [I] **There is no split on the server.** Packet `0x22` reaches `sub_0055E9A0_UnstackStub`, `xor eax, eax; ret 8`, and the handler returns 0. Scope: the handler `0x0054B380` (table entry `0x22`, read from `g_SrvPacketTable`) and the 12 request rows of § 1 only; the rest of the packet table was not read for a request that divides a stack (gold's withdraw and drop, for one, are other requests), and the stub is a reading of 8 bytes, not a run. (0x0054B380, 0x0055E9A0, `static.txt`)
- [I] **A placed item needs no open stash, on this reading.** The packet's item is on the cursor, so `PlayerIsBusy` is 1 and the "page ≠ 0 needs busy" test always passes. Page 4 needs a town room, page 2 an interaction with a player, page 3 nothing. Taking an item off a non-zero page, with an empty cursor, does need an interaction (§ 5). `0x0055C110`, which `InvPlaceItem` skips on page 4 (§ 5), holds no such test: items/0014 § 5. (fn:sub_0055C110_ItemSkillQtyAdjust@0x0055C110, 0x0054ABFC, 0x00535099, 0x0054AC1D, 0x0054AC4E, fn:sub_00560420_InvItemToCursor@0x00560420)
- [I] **The pickup's order**, to the inventory: refuse by the cursor or busy; not on the ground sets the refuse flag; quest gate; gold; a scroll into a tome, a tome into a tome, an auto-stack; auto-equip; the belt; the inventory; the refusal `0x0055C9A0(0x17)`. To the cursor: the same tests, gold, then the cursor. (fn:sub_00563560_PickupToInv@0x00563560, fn:sub_0055CF50_PickupToCursor@0x0055CF50)

## Leads used

No community source was compared; every claim is from the code.

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
| `0x0055EB30`, `0x00562250`, `0x005608C0` | `sub_0055EB30_BeltSwapCursor`, `sub_00562250_BeltToCursor`, `sub_005608C0_BeltOverflow` | the belt's moves | I |
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
| `0x13`, `0x16` | `0x0054AA90`, `0x0054AAD0` | `UnitInteract(type ≤ 5, guid, action)`; `0x13`'s action is 0 | [I] (fn:sub_00548B00_UnitInteract@0x00548B00) |
| `0x17` | `0x0054AB40` | a cursor item; `InteractIsPlayer(0)` non-zero returns 3; `CursorDrop` | [I] (fn:sub_00563C00_CursorDrop@0x00563C00) |
| `0x18` | `0x0054ABB0` | § 5; `ItemSetPage(item, page)`, then `InvPlaceItem(…, x, y, 0, 1, 0)` | [I] (fn:sub_00560200_InvPlaceItem@0x00560200) |
| `0x19` | `0x0054ACD0` | an owned item, empty cursor, not page 1; trade test `0x00535610`; `InvItemToCursor` | [I] (fn:sub_00560420_InvItemToCursor@0x00560420) |
| `0x1A`..`0x1E` | | equip and swap with a body location (`0x1B`'s slot 1..10) | [I] (fn:sub_005606B0_ItemEquip@0x005606B0, fn:sub_00563D20_EquipCursorAtSlot@0x00563D20, fn:sub_00560CD0_BodyToCursor@0x00560CD0, fn:sub_00560F00_BodySwapCursor@0x00560F00, fn:sub_00561220_BodySwapCursor2@0x00561220) |
| `0x1F` | `0x0054B0F0` | the cursor against a page item, not an item on page 1 or 2 | [I] (fn:sub_00561B00_PageSwapCursor@0x00561B00) |
| `0x21` | `0x0054B300` | two owned items, unequal guids; `StackRequest` | [I] (fn:sub_0055E7C0_StackRequest@0x0055E7C0) |
| `0x22` | `0x0054B380` | an owned item; the stub | [I] (0x0055E9A0) |
| `0x23` | `0x0054B3E0` | a cursor item; `ItemToBelt(guid, box, 0)` | [I] (fn:sub_0055E9B0_ItemToBelt@0x0055E9B0) |
| `0x24` | `0x0054B450` | a belt item, trade test, empty cursor; `BeltToCursor` | [I] (fn:sub_00562250_BeltToCursor@0x00562250) |
| `0x25` | `0x0054B4E0` | a cursor item and a belt item; `BeltSwapCursor` | [I] (fn:sub_0055EB30_BeltSwapCursor@0x0055EB30) |
| `0x63` | `0x0054D520` | an inventory-page beltable item, empty cursor: `BeltFreeSlot`, then to that box | [I] (fn:sub_0054D520_SrvPacket63Handler@0x0054D520) |

## 2. Grids and pages

- [I] An inventory is `0x40` bytes (magic `0x01020304`); `+0x08` owner, `+0x0C`/`+0x10` the item list, `+0x14` the pages, `+0x18` their count, `+0x20` the cursor item, `+0x28` the item count. (fn:INV_Create@0x0063ABD0, fn:sub_0063AAF0_InvItemRemove@0x0063AAF0)
- [I] The page table's index is `page + 2`; index 0 is the body (13 × 1), index 1 the belt (16 × 1), both sizes in the image, not the tables. Each entry is 16 bytes: `+8` width, `+9` height, `+0xC` the cells (u32 unit pointers, `row × width + col`). (data:0x0074479C, data:0x007447B4, fn:sub_0063ADD0_InvPageGet@0x0063ADD0)
- [I] A page is made on first use from the row given then. A later request with another size returns 0, so nothing is placed. In a save moved between game types this would be the refusal; no run reaches it. (0x0063AE53, 0x0063AE5A, fn:sub_0063ADD0_InvPageGet@0x0063ADD0)
- [C] (ADR-0021) `InvGridPut(col, row, index, invrow)` refuses a zero size. Indices 0 and 1 force the size to 1 × 1 and have **no** bound test; index 2 and above refuse `col < 0`, `col + w > gridX`, `row < 0`, `row + h > gridY`, then an occupied cell. The rest ends at `InvItemRemove`, after, `[I]`: the page fill, the page byte, the location byte. (fn:sub_0063AFD0_InvGridPut@0x0063AFD0, run:2026-11-04-inventory-emu)
- [I] Note `InvGridFree` tests no bound itself; `InvPlaceItem`'s direct branch clamps a negative `x`, `y` to 0 and relies on `InvGridPut`. (0x005602BE, fn:sub_00560200_InvPlaceItem@0x00560200)
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
- [I] A best of 0 fails only when no spot scores above 0, which needs a free rectangle touching nothing and no slide to one that touches. Sliding a free rectangle toward any occupied cell or edge finds a higher score, so a player's search fails only where no spot fits. The `search` family holds no counter-case, and this is a reading of the loop. (fn:sub_0063B490_InvSpotFindRow@0x0063B490, fn:sub_0063B620_InvSpotFind@0x0063B620, run:2026-11-04-inventory-emu)

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
- [I] So by direct calls the server reads `gridX`, `gridY` of `inventory` and `numboxes` of `belts`, and no rectangle. Rows 13 and 29 (Hireling) are never returned by `InvRowForUnit`: a hireling is type 1, row 5. The literal `0x0D` at `0x00483705` is client code. (0x00483705, fn:sub_00621050_InvRowForUnit@0x00621050)
- [I] **`Armor.belt` as the row is now a reader:** `0x0063C6A3` (the belt search) and `0x0056091B` (the belt overflow) both pass the worn item's Items `+0x130` to `BeltsRecord` with set 0. No worn belt gives row 2, at `0x0063C69B` and `0x0056093B`. (0x0063C6A3, 0x0056091B, 0x0056093D)
- [I] Of P1.1's unclassified readers, `0x0063C8B1` is `sub_0063C830_BeltBoxQuery`'s: `useable` and `belt` both exactly 1 on a 1 × 1 beltable item, else 0; callers unfollowed. (fn:sub_0063C830_BeltBoxQuery@0x0063C830)
- [I] Types `0x152`, `0x153` for rows 10 and 11 (Guild Vault, Trophy Case) are object classes; no path reaching them was read, and `inventory`'s page names are the only reason to give them those names. (0x00621050)

## 5. The stash and pages: `0x18`, `0x19`

- [I] `0x18` for a player, in order: the cursor test; a page ≥ 5 returns 2 (the `PlayerIsBusy` branch never returns there, § Answer); page 4: a room in town, else 3; page 2: `InteractIsPlayer(1)`, else 3; page 3, 0: nothing further. Then `ItemSetPage(item, page)` **before** the placement, so a refused item keeps the new page byte on the cursor. A non-player user has only the page ≥ 5 test. (0x0054ABE5..0x0054AC7E, 0x0054AC68)
- [I] `InvPlaceItem`: page 4 alone skips `0x0055C270` (for a player, `0x0055C110(1)`, a scroll's or tome's skill quantity, no page test; read at items/0014 § 5, fn:sub_0055C110_ItemSkillQtyAdjust@0x0055C110). An active charm then attaches. A failed put returns 0, the handler 3. (0x00560327, 0x0056032F, fn:ITEMS_IsActiveCharm@0x0062FF70, fn:sub_00560200_InvPlaceItem@0x00560200)
- [I] `0x19` → `InvItemToCursor(…, 1, 0, 0, 0)`: the cursor empty; a player not busy (no interaction, empty cursor, PlayerData `+0x4C` 0) refuses any page but 0; the item in mode 0; then remove, page byte saved, page `0xFF`, cursor word, mode 4, event flag 4. (fn:sub_00560420_InvItemToCursor@0x00560420, 0x005604D2, 0x005604DC)
- [I] Page bytes in the code: 0 inventory, 1 and 2 trade, 3 cube, 4 stash; `0xFF` while on the cursor or the belt. (0x00628280, 0x0054AC7E, fn:sub_00621050_InvRowForUnit@0x00621050)

## 6. Belts

- [C] (ADR-0015) `BeltFreeSlot`, each case to its return, boxes reached 0..12 and 15 (`check.txt` outcomes 15, `belt`). The `walk1` control (column walk by 1) fails 192, `nogroup` 126, `noauto` 337, `defaultbelt` 160, `secondset` 237 of 2 000. (fn:sub_0063C600_BeltFreeSlot@0x0063C600, run:2026-11-04-inventory-emu)
- [C] (ADR-0021) `BeltPlace` ends at `InvGridPut(box, 0, 1, 0)`, or returns 0 where the search does. After, `[I]`. (fn:sub_0063C790_BeltPlace@0x0063C790, run:2026-11-04-inventory-emu)
- [I] A row with `autobelt` 0 (stock `isc`, `tsc`, `yps`, `vps`, `wms` among them) is in no list, so it joins only a column whose bottom box holds its own class. (0x0063C731, tbl:Misc.txt:autobelt, fn:sub_00628A40_PotionSameGroup@0x00628A40)
- [I] **`ItemAutoBeltTest` is always 1** on an item: an `autobelt` row returns 1, any other compares `BeltHoldsSameGroup` (0 or 1) with −1. So the pickup's belt branch always calls `BeltPlace`, and the column search in it decides. (0x00628BFD, 0x00563716, `static.txt`)
- [I] **`0x23` does not test `numboxes`:** `ItemToBelt(guid, box, 0)` → `BeltPutItem` needs 1 × 1, beltable, `box < 16`; `InvGridPut` refuses an occupied box. Whether a box past the belt's count stays is Phase 2's. (0x0063C4C0, fn:sub_0063C4F0_BeltPutItem@0x0063C4F0, fn:sub_0055E9B0_ItemToBelt@0x0055E9B0)
- [I] `0x24` → the box's column shifts down (`BeltColumnShift`, items/0012 § 3 at `0x0055EDC0`). `0x25` swaps in place with no shift. `0x63` needs page 0 and an empty cursor, and returns 0 with no room. (fn:sub_00562250_BeltToCursor@0x00562250, fn:sub_0055EDC0_BeltColumnShift@0x0055EDC0, fn:sub_0055EB30_BeltSwapCursor@0x0055EB30, fn:sub_0054D520_SrvPacket63Handler@0x0054D520)
- [I] **A smaller belt:** `BeltOverflow(new belt or null)` walks boxes 0..15; each item at or above the new `numboxes` is removed, set to page 0 and placed by the search, and if that fails dropped by the cell search (`0x00555DA0`, P1.3). Its callers are the body moves' belt-type branches. (fn:sub_005608C0_BeltOverflow@0x005608C0, 0x00560C45, 0x00563D20)

## 7. Stacks

- [C] (ADR-0015) `ItemsCanStack`: `stackok`'s 660 cases hold each test broken alone, with both returns met. Quality 3 and 10 stack, 0, 4 and 9 do not; stat 194 of `0x100` on both passes (the low byte). (fn:sub_0062C850_ItemsCanStack@0x0062C850, 0x0062A2F0, run:2026-11-04-inventory-emu)
- [C] (ADR-0021) `StackMerge`, 500 cases to the first `UnitSetStat(target, stat, value, 0)`: 246 above the maximum, 87 exactly at it (the sum, not the over-branch), 167 below; 40 cases lower stat 72. After, `[I]`. (fn:sub_0055E590_StackMerge@0x0055E590, run:2026-11-04-inventory-emu)
- [I] **After the first set:** above the maximum the source keeps `source + target − maximum` and stays on the cursor, the target gets flag 8, and a tome adds `maximum − target` to the skill's quantity (`0x0055C070`). Otherwise stat 70 is the sum, a tome adds the source's quantity, the cursor is cleared and the source freed. (0x0055E623, 0x0055E66A, 0x0055C070)
- [I] **Bound.** A negative source, target or maximum ends at the fatal path. The sum is `int32`: two stacks at the 511 ceiling give 1 022, which fits, and `2³¹ − 1` is the largest sum that does. Past it the add wraps negative, the `jle` at `0x0055E617` takes the not-above branch, and its `≥ 0` test ends at the fatal path too, so no wrapped value is stored. (0x0055E5C2, 0x0055E5F2, 0x0055E606, 0x0055E617, fn:sub_0055E590_StackMerge@0x0055E590)
- [I] `StackRequest`: a missing unit or a target on page 2 sets the refuse flag, and the handler returns 3, as it does for equal guids. An unstackable pair returns 0 with the flag clear, so the handler returns 0 with nothing done. (fn:sub_0055E7C0_StackRequest@0x0055E7C0, 0x0054B33E, 0x0054B356)

## 8. Pickup

- [I] `UnitInteract`'s item case: the unit's mode 3; distance (`0x00641530`) above 50 does nothing; below 5 and `0x00622B50(…, 0x804)` 0 picks up: action 0 to the inventory, else to the cursor; else it walks there. (0x00548C60..0x00548CC5, fn:sub_00548B00_UnitInteract@0x00548B00)
- [I] **To the inventory** (`0x00563560`), in order: cursor empty and not busy, else return 0; the unit's mode 3, else the refuse flag; `ItemQuestGate`, a refusal calls `0x0055C9A0(0x13)`; `UnitSetEvent`; gold → `GoldPickup`; `PickupAutoStack`; `ItemAutoEquipSlot` with `0x0063DE60 == 1` → the body; beltable and `BeltPlace`; `InvAutoPlace` on page 0; else `0x0055C9A0(0x17)`, nothing moved. (fn:sub_00563560_PickupToInv@0x00563560, fn:sub_0055CC90_ItemQuestGate@0x0055CC90, fn:sub_0055C850_GoldPickup@0x0055C850)
- [I] `PickupAutoStack`: type 22 → the first tome of its kind with room (`0x0063C3B0`: type 18, the same `ITEMS_GetSuffix`, quantity below the maximum); type 18 → the same finder and a merge; a stackable row whose item type's byte `+0x13` is set → `PickupStackMerge`, repeating on each stack with room, a quiver type looking at the body first. Otherwise 0, and the order goes on. A remainder stays the same item, reduced, and goes on down the order (items/0014 § 5). (fn:sub_00560020_PickupAutoStack@0x00560020, fn:sub_0055FFA0_PickupScrollToTome@0x0055FFA0, fn:sub_0055D370_PickupTomeMerge@0x0055D370, fn:sub_0055D0D0_PickupStackMerge@0x0055D0D0)
- [I] `ItemAutoEquipSlot` needs `ItemReqCheck`, flag `0x10`, not disabled, not type 38; the rest of its body names the location (items/0014 § 5). (fn:sub_0055D710_ItemAutoEquipSlot@0x0055D710)
- [I] **To the cursor** (`0x0055CF50`): the same refusals and the gate; gold; else remove from the room, cursor word, mode 4, page `0xFF`, event flag `0x40`, clears flag bit 25, `QUESTS_RaiseItemPlaced`; `UnitSetEvent` last. (fn:sub_0055CF50_PickupToCursor@0x0055CF50)
- [I] Ownership (who dropped it) is not among any test read in the two pickups; `nopickup` was not found read there. Scope: these two functions and their direct callees' first level, not the gate's whole body, which items/0010 holds. (fn:sub_00563560_PickupToInv@0x00563560, fn:sub_0055CF50_PickupToCursor@0x0055CF50)
- [I] **The cursor to the ground:** mode 4; cell search `0x00555DA0(…, 1, 1)` from the user's position; `0x00558AA0` places; cursor cleared; flag 1 for an item holding items; `0x4000` cleared; `0x00563840`, which empties a dropped cube (items/0014 § 2). A null room from the search moves nothing; with `fallback` 1 a full surround does not give null, it drops on the blocked start (items/0014 § 1, § 6). (fn:sub_00563C00_CursorDrop@0x00563C00, fn:sub_00555DA0_GroundDropCell@0x00555DA0)

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
