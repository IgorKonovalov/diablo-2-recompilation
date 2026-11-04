# 0014 — Item use and inventory: the ground drop's cell search, ground-item lifetime, the requests' order in a drain

> **Subsystem:** items/use
> **Question:** which cell does an item dropped on the ground take, in which order is it searched and with how many draws; how long does a ground item live in a room that stays active; in which order do the item requests run inside one drain?
> **Date:** 2026-11-04   **Plan:** 0060 (Phase 1.3)   **Status:** for review (`lane/r60c`)

Static reading of the pinned `Game.exe` (objdump, the lane's Ghidra copy `ghidra-r60c`), then emulation under ADR-0015 and ADR-0021 with `re/ghidra_scripts/EmuBoundary.java` (unchanged), `tools/item_emu3.py` against `tools/item_inventory.py` (run:2026-11-04-ground-emu: **8 728 cases, 8 families, 0 mismatches, 0 stops, 0 unaccounted accesses**, each at the boundary its family states below).

**Tag convention.** **[C] (ADR-0015)** rests on families that run the named function to its return with all callees emulated over declared scratch memory: `drop`, `line`, `expiry`, `ground`, `dist`. **[C] (ADR-0021)** rests on families that end at a named call: `sweep` at `UnitGetRoom` (`0x00620BB0`), `los` at `COLL_LineTest` (`0x0064E260`) or `UNIT_CollUnmark` (`0x00649560`), `dispatch` at the handler's pointer test (`0x0054D7DC`). For these **the callee and all code after it are not covered** (written "after, `[I]`"), so "0 mismatches" holds up to that boundary. The image is scratch, not the game's structures, so each `[C]` is the code's map from the bytes it reads, and no symbol row is raised (review-fixes 14). A plain `[I]` is a code reading the emulator does not reach. Nothing here ran on a live game: Phase 2 does.

**One declared departure in `drop`.** The search allocates 8 bytes from the shared pool. The pool's page is declared as data, and the two lock imports' table slots (`0x006CC214`, `0x006CC218`) hold `0x0066A250`, a `ret 4` of the image, so no instruction is patched and the allocator's own code runs on the declared page; what the locks do is not evidenced (ADR-0015 condition 5). The block only holds the origin's two words, and the run reads them back from it.

## Answer (summary)

- [C] (ADR-0015) **The ground drop's search is a function of the position and the grid.** `GroundDropCell(room, pos, out, size, fallback)` starts at `(x + 2, y + 3)` when `room` or its near list holds that cell, else at `pos`, and calls `COLL_FindFreeNear` with masks `0x3E01` on the cell and `0x801` on the walk back to `pos`. (fn:sub_00555DA0_GroundDropCell@0x00555DA0, fn:COLL_FindFreeNear@0x0064DEA0, run:2026-11-04-ground-emu)
- [I] **It makes no draw:** it is given no seed, and the 567 functions of its closure hold no step, 54 indirect calls unfollowed (§ 7). (`rcg-summary.txt`, fn:sub_00555DA0_GroundDropCell@0x00555DA0)
- [C] (ADR-0015) **Rings around the start.** The start cell itself first, then ring `r = 1..49`: for each row `y - r..y + r` the columns `x - r`, `x + r`, then for each column `x - r + 1..x + r - 1` the rows `y - r`, `y + r`. The first ring holding a free cell ends the search and gives its lowest `|dx| + |dy|`, the earliest of equals. Ring 50 is never looked at. (fn:COLL_FindFreeNear@0x0064DEA0, run:2026-11-04-ground-emu)
- [C] (ADR-0015) **A free cell** has a room, `cell & 0x3E01 == 0`, and a clear walk: from the cell to `pos` along `expfield.d2`'s directions, each cell but `pos` itself with `& 0x801 == 0`. A cell or walk step with no room, no map or no cells counts as blocked (`0x27`). So a cell holding another ground item (bit `0x200`, in the cell mask, not the walk mask) is refused and does not stop a walk over it. (fn:sub_0066A670_FieldWalkBlocked@0x0066A670, fn:sub_0066A5D0_FieldStep@0x0066A5D0, fn:COLL_CellTestAt@0x0064CB30, run:2026-11-04-ground-emu)
- [C] (ADR-0015) **The base room moves.** The lookup that finds a candidate's room starts from the last non-null room a lookup returned, not from `room`, and the first lookup's result is kept even when null. A cell is reachable only through that room's near list, and the walk is tested from the candidate's room. The result's lookup uses the moved base too, so with no free cell and `fallback` 1 the return can be null though the start cell lies in the first room (control `fixedbase` fails 95 of 4 000). (fn:COLL_FindFreeNear@0x0064DEA0 0x0064E043, 0x0064E13C, 0x0064E21F, 0x0064E23F, run:2026-11-04-ground-emu)
- [C] (ADR-0015) **No free cell, `fallback` 1:** the item takes the start cell, blocked or not, in the room that last lookup gives. `fallback` 0 returns null and `out` keeps the start. (fn:COLL_FindFreeNear@0x0064DEA0, run:2026-11-04-ground-emu)
- [I] Every direct caller of the search passes `size` 1 and `fallback` 1. `DropGoldAmount` does the same work itself with `fallback` 0, so its pile with no free cell is not dropped. (`static.txt`, 0x0055A15C, fn:sub_0055A090_DropGoldAmount@0x0055A090)
- [C] (ADR-0015) **A placed item's expiry.** `ItemPlaceOnGround` writes item data `+0x24 = ItemGroundExpiry`: 0 for a quest base; else the frame + 30000 for quality 4, + 45000 for qualities 5..9, for base type 4 + 45000 above 10000 gold else + 15000, + 30000 for a socket filler, + 15000 otherwise. It sets mode 3, page `0xFF`, flags `0x1002` and `0x2000000`, and marks the cell `0x200`. (fn:sub_00558AA0_ItemPlaceOnGround@0x00558AA0, fn:sub_00558A10_ItemGroundExpiry@0x00558A10, run:2026-11-04-ground-emu)
- [I] **A monster's or chest's drop gets no expiry.** `ItemCreate` goes through `SUnitCreate` (item data zeroed), neither calls `ItemGroundExpiry`, and the sweep skips 0. So in a room that stays active such an item lasts until its room deactivates; the record then carries an expiry, and once restored it is `max(saved, frame + 15000)` and the sweep can free it with the room active. Scope below (§ 3); Phase 2 reads the field. (fn:sub_00558D90_ItemCreate@0x00558D90, fn:sub_00555230_SUnitCreate@0x00555230, fn:sub_00627C90_ItemDataAlloc@0x00627C90, fn:sub_00541990_InactiveItemRestoreOne@0x00541990)
- [C] (ADR-0021) **The sweep's test:** a type-4 unit with `+0x24 ≠ 0` and `+0x24 ≤ frame` (signed) is reached, in room order and each room's list order, up to the first one reached. After, `[I]`: unlink, sent to every player, freed; every 1 500 frames (frame/0003). (fn:sub_00558B90_ActExpiredItemsFree@0x00558B90, run:2026-11-04-ground-emu)
- [I] **The drain's order for item requests is arrival order, one at a time, to completion.** Queue 1 is FIFO for all clients and games; each packet's handler runs at once under the game's lock; no item request is reordered, batched or rate-limited in `SrvProcessClientMessage` or `SrvPacketDispatch`, and the next packet sees the state the last one left. Their return values are discarded. (0x0053F459, 0x0053F45E, fn:sub_0053F3D0_SrvProcessClientMessage@0x0053F3D0, fn:sub_0054D750_SrvPacketDispatch@0x0054D750, fn:sub_006BEAD0_NetQueuePop@0x006BEAD0)
- [C] (ADR-0021) **The gate before each handler:** opcode 0 or above `0x66`, or an empty table row, returns 3; `0x14`, `0x15`, `0x3C`, `0x43`, `0x66` pass; `0x41` passes only in mode `0x11`; any other passes unless the player has state 54 or is in mode 0 or `0x11`, which returns 0. After the pointer test, `[I]`. (fn:sub_0054D750_SrvPacketDispatch@0x0054D750, fn:sub_0057EEC0_PlayerModeAllowed@0x0057EEC0, data:g_SrvPacketTable@0x006E0D18, run:2026-11-04-ground-emu)
- [I] **The one item request that leaves the drain** is a pickup out of reach: it starts a walk, and the pickup runs in a later frame's mode pass at `PlrModeMoveFrame`. (fn:sub_00548A50_InteractWalkTo@0x00548A50, 0x00580E73, fn:sub_00548B00_UnitInteract@0x00548B00)
- [C] (ADR-0015) **Pickup's distance** is `UnitInteractDistance` with the table at `0x006EB180`; player to item, `d < 5` reaches 22 of the 64 `|dx|, |dy|` pairs under 8, among them `(4, 2)` and not `(3, 4)` or `(5, 0)`. (fn:sub_00641530_UnitInteractDistance@0x00641530, data:0x006EB180, run:2026-11-04-ground-emu)
- [C] (ADR-0021) **Pickup's line test** returns 0 for touching units (`|dx| + |dy| < min(sa, 2) + min(sb, 2)`), else calls `COLL_LineTest(room, a', b', mask)` with each end moved toward the other by its unit's clamped size. After, `[I]`. (fn:sub_00622B50_UnitsLineBlocked@0x00622B50, fn:sub_00622920_LineTestShortened@0x00622920, run:2026-11-04-ground-emu)
- [I] **A pickup-merge's remainder** stays the same item, its quantity reduced, and goes on down the pickup's order (equip, belt, inventory); with no room it stays on the ground reduced, and the merges made stand. (fn:sub_0055D0D0_PickupStackMerge@0x0055D0D0, fn:sub_00563560_PickupToInv@0x00563560)
- [I] **`0x0055C110` is not a stash-open test.** It keeps a scroll's or tome's skill quantity with the item's count and returns 0 for every other item; `InvPlaceItem` skips it on page 4, so a scroll or tome placed in the stash adds nothing to the skill. (fn:sub_0055C110_ItemSkillQtyAdjust@0x0055C110, fn:sub_0055BFF0_ItemBookSkill@0x0055BFF0, 0x00560327)
- [I] **`ItemAutoEquipSlot`'s tail:** ammunition needs a matching weapon in a hand; one body location takes the item if empty; two (hands, rings) take the first empty one if the other is empty or the pair is compatible. (fn:sub_0055D710_ItemAutoEquipSlot@0x0055D710, fn:sub_0055D670_EquipPairCompatible@0x0055D670)

## Leads used

No community source was compared; every claim is from the code.

## Functions

33 new rows at `I` in `re/symbols.csv`, evidence here; the maps of `drop`, `line`, `expiry`, `ground`, `dist` and of `sweep`, `los`, `dispatch` up to their boundary are `[C]` under the convention above. (fn:sub_00555DA0_GroundDropCell@0x00555DA0, run:2026-11-04-ground-emu)

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x00555DA0` | `sub_00555DA0_GroundDropCell` | the offset start, then the pair search | I (map C) |
| `0x00558AA0` | `sub_00558AA0_ItemPlaceOnGround` | position, mark, room, mode 3, expiry | I (map C, room flag 4) |
| `0x00558B40` | `sub_00558B40_ItemTakeFromGround` | the sweep's removal as a function; no `call` or `jmp` to it in the objdump listing | I |
| `0x0066A2B0`, `0x0066A420` | `sub_0066A2B0_FieldLoad`, `sub_0066A420_FieldFree` | `expfield.d2` to `0x0096D654`, sizes to `0x0096D658`..`0x0096D668`; freed | I |
| `0x0066A4B0`, `0x0066A500`, `0x0066A540` | `sub_0066A4B0_FieldStateAlloc`, `sub_0066A500_FieldStateFree`, `sub_0066A540_FieldStateOrigin` | the 8-byte origin | I (map C through `drop`) |
| `0x0066A5D0`, `0x0066A670` | `sub_0066A5D0_FieldStep`, `sub_0066A670_FieldWalkBlocked` | one step, the walk's test | I (map C) |
| `0x00641530` | `sub_00641530_UnitInteractDistance` | the distance of `UnitInteract` | I (map C) |
| `0x00622B50`, `0x00622920` | `sub_00622B50_UnitsLineBlocked`, `sub_00622920_LineTestShortened` | pickup's line test | I (map C to the boundary) |
| `0x00620AE0`, `0x0064C350` | `sub_00620AE0_UnitSetStaticPos`, `sub_0064C350_RoomUnitAddMarked` | the static path's cell; `RoomUnitAdd(unit, room, 1)` | I (map C through `ground`) |
| `0x00563840` | `sub_00563840_CubeDropEmptied` | a dropped `box `: page-3 items to page 0, else to the ground | I |
| `0x005594C0`, `0x0055A200`, `0x00582AC0`, `0x00585A80`, `0x005A30E0`, `0x0056DAB0` | `sub_005594C0_DropRolledAtPos`, `sub_0055A200_DropEar`, `sub_00582AC0_ObjDropCreate`, `sub_00585A80_ObjDropCreate2`, `sub_005A30E0_MonDropCreated`, `sub_0056DAB0_NpcDropCreate` | other callers of the search, each only as far as that call | I |
| `0x0055BFF0`, `0x0055C110`, `0x0055C270` | `sub_0055BFF0_ItemBookSkill`, `sub_0055C110_ItemSkillQtyAdjust`, `sub_0055C270_ItemSkillQtyAdd` | a scroll's or tome's skill quantity | I |
| `0x0055C9A0` | `sub_0055C9A0_PickupRefused` | the refusal: back to mode 3, event | I |
| `0x0055D560`, `0x0055D670` | `sub_0055D560_EquipPairFlags`, `sub_0055D670_EquipPairCompatible` | the two-location test | I |
| `0x0062FDF0`, `0x00628480`, `0x0062E6F0`, `0x0062EA80`, `0x0063DE60` | `sub_0062FDF0_ItemTypeBodyByte`, `sub_00628480_ItemTypeQuiver`, `sub_0062E6F0_ItemTypeShoots`, `sub_0062EA80_ItemBodyLocs`, `sub_0063DE60_BodyLocTest` | ItemTypes readers and the body's test | I |

## 1. The search

`[C]` (ADR-0015), family `drop`, to the return (fn:sub_00555DA0_GroundDropCell@0x00555DA0, fn:COLL_FindFreeNear@0x0064DEA0, run:2026-11-04-ground-emu):

```
GroundDropCell(room, pos, out, size = 1, fallback):
    start = (pos.x + 2, pos.y + 3)  if room_at(room, that) else pos
    out = start
    return FreeNear(room, out, origin = pos, 0x3E01, 0x801, fallback)

room_at(base, x, y):       null base: null; base holds it: base; else the first of base's near list, in list order, that holds it; else null
cell(base, x, y, mask):    r = room_at(base, x, y); no r, no map or no cells: 0x27; else r's cell & mask

FreeNear(base, out, origin, A, B, fallback):
    r = room_at(base, out); base = r                       -- kept even when null
    if r and cell(r, out, A) == 0 and walk(r, out, origin, B) == 0: return r
    for ring = 1..49:
        best = none
        for y = sy - ring .. sy + ring:  try (sx - ring, y), (sx + ring, y)
        for x = sx - ring + 1 .. sx + ring - 1:  try (x, sy - ring), (x, sy + ring)
        if best: out = best's cell; return room_at(base, out)
    return fallback ? room_at(base, out) : null

try(x, y): r = room_at(base, x, y); no r: skip
           base = r                                         -- moved before the tests
           if cell(r, x, y, A) != 0 or walk(r, (x, y), origin, B) != 0: skip
           d = |x - sx| + |y - sy|; if no best or d < best.d: best = (x, y), d
walk(r, (x, y), origin, B):
    loop: if cell(r, x, y, B) != 0: return 1
          step by the field byte; if the new cell's byte is 8: return 0
```

- [C] (ADR-0015) The field: row `128 + y - oy`, column `128 + x - ox` of the 256 × 256 bytes after the file's 10-byte header; byte `d` steps `dx[d]`, `dy[d]` from `0x00749780`, `0x007497A4`; 8 is the centre. So the origin cell is tested only when the walk starts on it. File `expfield.d2`. (fn:sub_0066A5D0_FieldStep@0x0066A5D0, data:0x00749780, data:0x007497A4, run:2026-11-04-ground-emu)
- [C] Full-file check: every one of the 65 536 cells walks to the one byte 8 at `(128, 128)`, the longest in 128 steps, none leaving the table, and each walk's length is the Chebyshev distance, so a walk never detours. (`static.txt`, fn:sub_0066A5D0_FieldStep@0x0066A5D0, run:2026-11-04-ground-emu)
- [I] The candidates stay within 52 of the origin, inside the ±127 the table covers, so no drop reads past it. (fn:sub_00555DA0_GroundDropCell@0x00555DA0, 0x0066A61C)
- [I] The masks' bits by drlg/collision: `0x3E01` has bits 0, 9, 10, 11, 12, 13; `0x801` bits 0 and 11. Which of them a stock cell holds is drlg/collision's. (0x00555DE4, 0x00555DDF)

**What the run separates** (`check.txt`; each control is a wrong reading, and fails that many of `drop`'s 4 000 cases):

| Control | Wrong reading | Fails |
|---|---|---|
| `noline` | no walk test | 567 |
| `nooffset` | the search starts at the position | 2474 |
| `offset32` | the offset is (+3, +2) | 2232 |
| `first` | a ring's first free cell wins, not its lowest distance | 717 |
| `leq` | a later cell of equal distance wins | 559 |
| `capsfirst` | the end rows before the side columns | 476 |
| `noitembit` | the cell mask lacks the item bit 0x200 | 647 |
| `linecellmask` | the walk uses the cell mask | 1041 |
| `r48` | the last ring is 48 | 6 |
| `r50` | the last ring is 50 | 6 |
| `alwaysfallback` | fallback 0 acts as 1 | 47 |
| `linediag` | the walk is diagonal then straight, not the file's | 220 |
| `lineorigin` | the walk tests the origin too | 296 |
| `lineroom0` | the walk is tested from the first room, not the candidate's | 43 |
| `fixedbase` | every lookup starts from the first room | 95 |

**Distinct outcomes** (`check.txt`, `outcome drop`), 55 labels; collapsed:

| Outcome | Cases |
|---|---|
| start accepted at (+2, +3) | 1286 |
| start accepted at the position | 617 |
| fallback on the blocked start at (+2, +3) | 95 |
| fallback on the blocked start at the position | 24 |
| ring 1: side / end row | 764 / 217 |
| rings 2..5: side / end row | 213 / 163 |
| rings 6..20: side / end row | 31 / 27 |
| rings 21..46: end row | 1 |
| rings 47..49: side / end row | 7 / 11 |
| no room, fallback 0 | 170 |
| no room, fallback 1 (a moved or null base) | 374 |

## 2. Who drops, and with what

- [I] Direct calls: 20 of the search, all with `size` 1 and `fallback` 1; 12 of `ItemPlaceOnGround`; 7 of the pair form: the search; four item-drop bodies that inline the same start and masks with `size` 1 and `fallback` 1 (`0x0055923B`, `DropGoldPile`'s `0x005593F7`, `0x00559770`, `0x00559969`); `DropGoldAmount`'s `0x0055A15C` with `fallback` 0; and `PortalObjectCreate`'s `0x0056D213` with `size` 3, masks `0x3E01`, `0xC01`, `fallback` 0. `static.txt` lists each with its pushes. The search's callers: monster and chest drops through `DropCreateItem` and `DropItemAtUnit`, `CursorDrop`, the belt overflow, the cube's contents, the corpse overflow, NPC menus, shrines. (`static.txt`, 0x0055923B, 0x005593F7, 0x0055A15C, 0x0056D213, fn:sub_0055A550_DropCreateItem@0x0055A550, fn:sub_00559A30_DropItemAtUnit@0x00559A30, fn:sub_00563C00_CursorDrop@0x00563C00, fn:sub_005608C0_BeltOverflow@0x005608C0, fn:sub_0057F540_CorpseOverflowDrop@0x0057F540)
- [I] **Draws beside the search.** `MissDo18ChestSpawner` draws twice on its unit's seed for an offset (`RNG_RangeB(2n + 1) - n`, x then y) and then calls the search from there. The search itself and every other caller read so far add no draw of their own around the call: their rolls belong to the item they create. (fn:sub_005AF300_MissDo18ChestSpawner@0x005AF300, fn:sub_00555DA0_GroundDropCell@0x00555DA0)
- [I] A null room from the search: `CursorDrop` and `DropCreateItem` test it and do nothing (the item stays on the cursor; no item). `NPC_MenuAction` (0x0057A19A) and `CorpseOverflowDrop` pass it to `ItemPlaceOnGround`, whose null-room branch returns having done nothing (family `ground`). (fn:sub_00563C00_CursorDrop@0x00563C00, fn:sub_0055A550_DropCreateItem@0x0055A550, 0x0057A19A, 0x0057F61B, fn:sub_00558AA0_ItemPlaceOnGround@0x00558AA0)
- [I] `sub_00563840_CubeDropEmptied`: `CursorDrop` calls it with the dropped item; for code `box ` each item on page 3 moves to the cursor word, to page 0 and into the search; if none fits, it takes the cell search and `ItemPlaceOnGround`. (fn:sub_00563840_CubeDropEmptied@0x00563840, 0x00563BAF, 0x00563BC7)
- [C] (ADR-0015) `ItemPlaceOnGround(game, flag, item, room, x, y)`, family `ground` to the return with the room's flag 4 declared (so `UnitMarkUpdated` does not enter its list): the path's room and cell, cell `| 0x200`, unit `+0xC4 | 0x2001002`, mode 3 from mode 3 or 4, item data `+0x24`. A null room writes nothing. (fn:sub_00558AA0_ItemPlaceOnGround@0x00558AA0, fn:UNIT_CollMarkRect@0x00620A70, run:2026-11-04-ground-emu)
- [I] `flag` non-zero calls `QUESTS_RaiseItemDropped` last. (0x00558B1C, 0x00558B26, fn:QUESTS_RaiseItemDropped@0x00543DB0)

## 3. Lifetime in an active room

- [C] (ADR-0015) The expiry's branches, family `expiry`, to the return: 0, + 15000, + 30000, + 45000, each with the boundary values named in the summary (10000 and 10001 gold, control `goldgeq` fails 6; quality 4 against 5, `q4eq45` 50; the filler, `fillerplain` 67). The add wraps as `i32`: for + 45000, frame 2 147 438 647 still fits (`2³¹ − 1 − 45000`) and 2 147 438 648 wraps negative, and a negative expiry is `≤ frame` at the next sweep, so the item goes at once. That frame is about 2.7 years of play at 25 frames a second, so no game reaches it; the `expiry` family has frames in that range. (fn:sub_00558A10_ItemGroundExpiry@0x00558A10, 0x00558A3F, run:2026-11-04-ground-emu)
- [I] **Writers of item data `+0x24`.** A kept scan (`static.txt`) lists 14 accesses of `[r + 0x24]` within 14 instructions of `mov r, [s + 0x14]`, 10 writes. For an item: `0x00554C04` (`UnitRelocate`, mode 3), `0x00558B19` (`ItemPlaceOnGround`), `0x005419FC` and `0x00541A04` (`InactiveItemRestoreOne`). The others read as other unit kinds: `0x0064A7D5` tests type 3; `0x00553627`, `0x00553688`, `0x005536F8` copy another unit's position (callers not followed); `0x00541883` is a setter with 0 direct calls; `0x006B01D2` is not a unit. The scan does not see a copy of the whole item data, and `ItemCopy`'s bytes were not read for this field. (`static.txt`, 0x00554C04, 0x00558B19, 0x005419FC, 0x00541A04, 0x0064A7BF, 0x00553627, 0x005536F8, 0x00541883)
- [I] **Three lives.**

| How it got to the ground | Item data `+0x24` | In a room that stays active |
|---|---|---|
| `ItemCreate`: a monster's or chest's drop, `DropGoldPile` | 0 (zeroed, no writer on the path) | never swept |
| `ItemPlaceOnGround`: a player's drop, an overflow, `DropGoldAmount`, NPC menus, the cube's | `ItemGroundExpiry` | freed at the first multiple of 1 500 at or past it |
| Restored from a record (drlg/lifecycle) | `max(saved, frame + 15000)`, 0 stays 0 | as above |

(fn:sub_00558D90_ItemCreate@0x00558D90, fn:sub_00558AA0_ItemPlaceOnGround@0x00558AA0, fn:sub_00541990_InactiveItemRestoreOne@0x00541990, fn:sub_00558B90_ActExpiredItemsFree@0x00558B90)

- [I] So 15000 frames is 10 minutes at 25 a second, and the free falls up to 1 499 frames later. A held item keeps its old `+0x24`, unread: only a room's list is swept, and a new drop overwrites it. (fn:sub_00558B90_ActExpiredItemsFree@0x00558B90, 0x00558B19)
- [C] (ADR-0021) The sweep, family `sweep`: `ltframe` (`<`) fails 92, `zerofrees` (0 expires) fails 69, of 600; earlier `run:2026-10-30-frame-emu-3` holds its period and order. After the first unit, `[I]`. (fn:sub_00558B90_ActExpiredItemsFree@0x00558B90, run:2026-11-04-ground-emu)
- [I] `sub_00558B40_ItemTakeFromGround` holds the sweep's removal body. A grep of the objdump listing for its address finds no operand; table pointers to it were not scanned. (0x00558B40)

## 4. One drain

- [I] The pieces, from frame/0001 § 5 and read again here: `NetQueuePop` is FIFO; the drain pops queue 1 to empty; `SrvProcessClientMessage` locks the client's game and calls `SrvPacketDispatch`; the return is dropped: `0x0053F459` is followed by `mov ecx, esi; call 0x0052DA90`, with no test of `eax`. So a "refusal" return (2, 3) has no effect beyond the handler's own. (0x0053F459, 0x0053F45E, fn:sub_006BEAD0_NetQueuePop@0x006BEAD0)
- [I] So two item requests in one drain run in arrival order and see each other's results: `0x17` then `0x16` on the same item finds it on the ground already; a second `0x19` finds a full cursor. Across clients it is arrival too. No rate limit or per-frame cap appears in the two functions. Scope: those two bodies and `PlayerModeAllowed`, not each handler's whole closure. (fn:sub_0054D750_SrvPacketDispatch@0x0054D750, fn:sub_0053F3D0_SrvProcessClientMessage@0x0053F3D0)
- [C] (ADR-0021) The gate, family `dispatch` (428 cases over each opcode 0..`0x68`, `0x80`, `0xFF` × mode 1, 0, `0x11` and state 54 at mode 6): `nogate` fails 258, `noexempt` 15. It ends at the `IsBadCodePtr` call, which is an import; the handler's call is after it, `[I]`. `PlayerModeAllowed(1, 0, 0)` returns before its RNG line because its second argument is 0 (`0x0057EEFB`), so the gate draws nothing on this path. (fn:sub_0054D750_SrvPacketDispatch@0x0054D750, fn:sub_0057EEC0_PlayerModeAllowed@0x0057EEC0, 0x0054D7DC, run:2026-11-04-ground-emu)
- [I] **What leaves the drain.** `UnitInteract`'s item case with `d ≥ 5`, or `d < 5` and a blocked line, and `d ≤ 50`, starts `PLAYER_ModeCmdUnit(0, 3, …)`, and the stored interaction runs at the walk's end from `PlrModeMoveFrame`, in a frame pass. A later request in the same drain sees the item still on the ground. The reach and line tests run again there. The other item handlers of items/0012 § 1 and items/0013 § 1, as read, do their moves in the handler; their callees' queued events and marks (`UnitSetEvent`, `UnitMarkUpdated`) reach clients later, and those were not followed. (fn:sub_00548B00_UnitInteract@0x00548B00, fn:sub_00548A50_InteractWalkTo@0x00548A50, 0x00580E73, fn:PLAYER_ModeCmdUnit@0x00580A70, 0x00553380)
- [I] The frame an expiry is computed in: a drop handled while `Game+0xA8 = N` uses `N`; the sweep tests at the frame's own `N`. (0x00558A38, 0x00558BA8)

## 5. What P1.2 left

- [C] (ADR-0015) **The distance** (family `dist`, to the return): for `|dx| < 8`, `|dy| < 8` and both sizes below 4, `v = table[|dx| + 8|dy|]`; `v < 0` returns 0; a size of 3 takes 1 off, floored at 0; if either size is below 2, `v + 1`, else `v`. Otherwise each axis less `(sb >> 1) + (sa >> 1)`, floored at 0, and `2 × larger + smaller`. `plainmanh` fails 1419, `sizeless` 682 of 1 500. Sizes: `UNIT_GetSizeX` is 2 for a player, 1 for an item, the record's `+0xD0` for an object; a monster and a missile were not run. (fn:sub_00641530_UnitInteractDistance@0x00641530, fn:UNIT_GetSizeX@0x00620510, run:2026-11-04-ground-emu)
- [I] Pickup: `d ≥ 51` does nothing; `d < 5` and a clear line picks up; else the walk. The pairs with `d < 5`, player to item, are in `static.txt`. (0x00548C60..0x00548CC5, `static.txt`)
- [C] (ADR-0021) **The line test** (family `los`): both units' masks are tested against `mask`; a unit overlapping it goes to `UNIT_CollUnmark` (boundary; after, `[I]`: it is marked again after the test). Otherwise, per `line_ends`, the call's room is the first unit's and its arguments the shortened ends; `swapsizes` fails 129, `noshorten` 262 of 600. `COLL_LineTest`'s own result is drlg/collision's `[I]`, not this run's. Pickup's mask `0x804` does not overlap an item's `0x200`; a player's mask at `path+0x4C` was declared, not read from a game. (fn:sub_00622B50_UnitsLineBlocked@0x00622B50, fn:sub_00622920_LineTestShortened@0x00622920, fn:UNIT_GetCollMask@0x006209D0, 0x00548C7E, run:2026-11-04-ground-emu)
- [I] **The remainder.** `PickupStackMerge` loops while the source's stat 70 is above 0: the next stack with room (`InvStackWithRoom`, after the last target; for a quiver type the body first). Above the maximum: the target takes the maximum, the source the rest, a tome's skill adjusts, and it loops. At or below: the source is unlinked, freed and the function returns 1. No further stack with room: return 0, so `PickupAutoStack` returns 0, and `PickupToInv` goes on to auto-equip, belt and inventory with the reduced item. With no room there, `0x0055C9A0(0x17)` puts it back in mode 3 on the ground with its reduced count, and the merged stacks keep what they took. The fatal line after the loop (`0x606`) needs a source reaching 0 outside the return, which no branch read does. (fn:sub_0055D0D0_PickupStackMerge@0x0055D0D0, fn:sub_00560020_PickupAutoStack@0x00560020, fn:sub_0063C200_InvStackWithRoom@0x0063C200, fn:sub_0055C9A0_PickupRefused@0x0055C9A0, fn:sub_00563560_PickupToInv@0x00563560)
- [I] **`0x0055C110(add)`:** `ItemBookSkill` is `Books`' `+8` for type 22 (scroll) or `+0xC` for type 18 (tome), else −1, which returns 0. `add` non-zero: quantity = the skill's + `max(stat 70, 1 for a non-tome)`, granting the skill if missing; `add` 0: less, floored at 0, and an empty left or right skill choice is reset. It sends the quantity to the client. There is no test of a page or a stash. `0x18` to page 4 therefore has no such test on the paths read; Phase 2 case 7 stays. This closes items/0013's open reading. (fn:sub_0055C110_ItemSkillQtyAdjust@0x0055C110, fn:sub_0055BFF0_ItemBookSkill@0x0055BFF0, fn:sub_0055C270_ItemSkillQtyAdd@0x0055C270, 0x00560327)
- [I] **`ItemAutoEquipSlot(user, item, &loc, skipReq)`** after the first half: `Quiver` of the item's type set (`+0xE`): a hand (locations 4, 5) must hold a weapon whose `Shoots` (`+0xC`) the item is, else 0. `BodyLoc1`, `BodyLoc2` (`+0xA`, `+0xB`) equal: that location if empty. Unequal: both empty gives `BodyLoc1`; one empty gives it when `EquipPairCompatible(item, the other)`; else 0. The pair is compatible for bow and bow quiver, crossbow and crossbow quiver (types 27, 5 and 35, 6), a one-handed weapon and a shield (45 without the two-handed test, 51), two one-handed weapons when both have flag 7 (a class-4 user, or class 6 and type 67), and two of type 10. `PickupToInv` then needs `BodyLocTest(user, loc, item, 0) == 1`. Types are `tbl:ItemTypes.txt` rows. (fn:sub_0055D710_ItemAutoEquipSlot@0x0055D710, fn:sub_0055D560_EquipPairFlags@0x0055D560, fn:sub_0055D670_EquipPairCompatible@0x0055D670, fn:sub_0062EA80_ItemBodyLocs@0x0062EA80, fn:sub_0063DE60_BodyLocTest@0x0063DE60, fn:sub_00563560_PickupToInv@0x00563560, tbl:ItemTypes.txt:Shoots, tbl:ItemTypes.txt:Quiver, tbl:ItemTypes.txt:BodyLoc1, tbl:ItemTypes.txt:BodyLoc2, tbl:ItemTypes.txt:Body)

## 6. Corrections to earlier readings

- [C] (ADR-0015) **quests/0002 § the free-cell search and specs/quests/travel B1** write `other` as a "second footprint" and `room` as a fixed input. `other` is a walk's origin along `expfield.d2` (§ 1), and the lookup's base moves. Of the travel callers only `PortalObjectCreate` (`0x0056D213`, mask `0xC01`) passes an `other`, and its walk is this walk; the moving base applies to all of them. Entry filed for the spec-writer. (fn:COLL_FindFreeNear@0x0064DEA0, fn:sub_0066A670_FieldWalkBlocked@0x0066A670, run:2026-11-04-ground-emu)
- [I] items/0013 § 8's "No cell, nothing moves" for `CursorDrop` holds only where the search returns null: with `fallback` 1 that is a moved base that cannot see the start, or a null first room. An ordinary full surround drops on the blocked start cell. (fn:sub_00563C00_CursorDrop@0x00563C00, 0x00563C87, run:2026-11-04-ground-emu)

## 7. Draws per seed

| Path | Draws | Tag |
|---|---|---|
| The search, `FieldWalkBlocked`, `ItemGroundExpiry`, the distance, each to its return | no seed is given to them: the arguments are a room, cells and masks, or (the distance) two units; the families' outputs are fixed by the declared bytes, and the closures below hold no step | [C] (ADR-0015) for the map, [I] for 0 draws (fn:sub_00555DA0_GroundDropCell@0x00555DA0, run:2026-11-04-ground-emu, `rcg-summary.txt`) |
| Closures under `0x00555DA0`, `0x0066A670`, `0x00558A10`, `0x00641530`, `0x00622B50`, `0x0055D710`: 567, 551, 556, 551, 585, 599 functions, 0 with a step, 54 indirect calls each unfollowed | 0 in direct calls | [I] (`rcg-summary.txt`, 0x00555DA0) |
| Closure under `0x00558AA0`: 711 functions, 1 with a step, 58 indirect. The step is `RNG_RangeB` at `0x00624563` on `unit+0x20`, in `UNIT_AnimInit`'s type-2 branch; family `ground` reads that function's table only at type 4 (`0x0062468C`) and takes the item branch `0x0062459D` | 0 for an item | [I] (`rcg-summary.txt`, 0x00624563, 0x0062459D) |
| Closure under `0x0054D750`, its handlers not followed (table pointers): 576 functions, 1 with a step, at `0x0057EF75`, after `PlayerModeAllowed`'s test of its second argument (`0x0057EEFB`), which the gate passes as 0 | 0 at the gate | [I] (`rcg-summary.txt`, 0x0057EEFB, 0x0057EF75) |
| `0x00558B90`, `0x00563C00`, `0x00563840`, `0x0055D0D0`, `0x0055C110`: 2 096..2 101 functions, 118 with a step, 112 indirect | not bounded: the closures run through the same unit paths as items/0012 § 8 and the unit free; a whole move's bound is Phase 2's seed comparison | [I] (`rcg-summary.txt`, 0x00558B90) |
| `MissDo18ChestSpawner`'s offset | 2 on its unit's seed before the search | [I] (fn:sub_005AF300_MissDo18ChestSpawner@0x005AF300) |

## 8. Harness cases for Phase 2

Predicted by `tools/item_inventory.py`; logged: the item's cell, room, mode and item data `+0x24`, game frame, seed before and after, the collision cells around the drop.

1. Drop from the cursor on open ground: the cell is `(x + 2, y + 3)`.
2. Drop repeatedly in place with no movement: rings by `ground_drop_cell`; the order `(x + 1, y + 2)`… by the lowest distance, each ring's ties.
3. Drop beside a wall so a free cell's walk is blocked (the ring skips it): predicted from a logged collision snapshot, control `noline`.
4. Drop at a room's edge where `(x + 2, y + 3)` is in a neighbour, and where it is in no room: the start.
5. A monster's death with several drops: each cell in turn; each takes the search.
6. A full surround on a small enclosed floor, if a stock place gives one: the fallback's blocked start. If none does, this stays `[C]` under ADR-0015 alone.
7. Read `+0x24` after a monster's drop (expected 0), a player's drop (frame + 15000 or the row's), gold above and at 10000, a magic, a rare, a socket filler, a quest item.
8. Leave a player's drop past its expiry beside the player in an active room: gone at the first multiple of 1 500 at or past it; a removal message; no draw. The control is a monster's drop lying beside it for the same window: still there.
9. Leave a monster's drop, deactivate its room, return: `+0x24` is `max(saved, frame + 15000)`, then swept with the room active.
10. Pick up, drop again: `+0x24` rewritten.
11. Two item requests in one drain (crafted: `0x17` then `0x16`, then a `0x19`): the second sees the first's result, by the handlers' logged order and `Game+0xA8`.
12. Item requests from a dead player (mode 0, `0x11`) and with state 54: no handler entered. `0x14`-class ones enter.
13. Pickup at each `|dx|, |dy|` around `d = 5`, 50, 51: picked up, walk, nothing. The walk's pickup in a later frame.
14. Pickup behind a wall at `d < 5`: the walk.
15. Pickup with arrows into two partial stacks, a remainder, then a full inventory: the reduced item on the ground. Case 20 of items/0013.
16. Pickup of a scroll to a full tome and to the inventory; placing it on page 4: skill quantity unchanged (`0x0055C110`). Taking it off: see items/0013 § 5.
17. Auto-equip: an arrow with a bow, with no bow; a ring on each of two empty fingers, one taken; a shield beside a one-handed weapon; a second weapon as a Barbarian and as a Sorceress.
18. Drop the cube with items inside: to page 0; a full inventory: on the ground by the search.
19. `MissDo18ChestSpawner`'s two draws where a chest spawner runs: logged seed steps.
20. The seed compared over each drop above.

## Data touched

tbl:ItemTypes.txt:Body, tbl:ItemTypes.txt:BodyLoc1, tbl:ItemTypes.txt:BodyLoc2, tbl:ItemTypes.txt:Shoots, tbl:ItemTypes.txt:Quiver, tbl:Books.txt:pSpell, tbl:ItemStatCost.txt:Stat. File `expfield.d2`: a u16 of 266 by this copy, a u32 row count, a u32 column count, then the bytes; entry filed for the archivist. Game data is not copied here.

## Dead ends

- `0x00555DA0` read as a fixed-room search from the decompile: its hidden `ECX` hides `[ebp+8]` being rewritten at `0x0064E043` and `0x0064E13C`. Two of `dev-3`'s 136 cases showed it (`dev-1`..`dev-4` kept).
- A monster's drop's expiry looked for in `ItemCreate`: none is there; the three `ItemGroundExpiry` callers are the record save, `UnitRelocate` and `ItemPlaceOnGround`.

## Open questions

- `[L]` Whether a monster's drop's `+0x24` is 0 in a game, by a writer the scan's form misses (`ItemCopy`, a block copy): Phase 2 case 7.
- `[L]` A player's stock mask at `path+0x4C` against `0x804`, and so whether pickup's line test ever takes the unmark branch: Phase 2 case 14.
- `[L]` `0x18` to page 4 with no stash open: no test on the paths read; Phase 2's crafted request (items/0013 case 7).
- `[L]` A full surround's blocked start in a stock game, and a moved base's null return: emulated only.
