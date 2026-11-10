# Plan 0066 inventory: items/inventory

- **Spec:** [items/inventory](../../specs/items/inventory.md), read at `main` `b5999f5e`.
- **Front matter `I`:** 104; the *Count* column sums to 104.
- Classes, batches and conventions as in [the inventory README](README.md#conventions).

| # | Line | Section | Claim (excerpt) | Anchor | Class | Route or reason | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | 41 | Entry points | Client packets , : interact with a unit, an … — → | `fn:sub_0054AAD0_Pkt16UnitAction@0x0054AAD0` | ? | ? | ? | 1 |
| 2 | 42 | Entry points | Client packets .., .., : the moves (§ D) | `data:g_SrvPacketTable@0x006E0D18` | ? | ? | ? | 1 |
| 3 | 43 | Entry points | A monster or chest drops — (items/tc § H) | `fn:sub_0055A550_DropCreateItem@0x0055A550` | ? | ? | ? | 1 |
| 4 | 44 | Entry points | Other callers of the ground drop (§ J4) | `fn:sub_00555DA0_GroundDropCell@0x00555DA0` | ? | ? | ? | 1 |
| 5 | 75 | Constants | body page — index 0, 13 × 1, in the image | `data:0x0074479C` | ? | ? | ? | 1 |
| 6 | 76 | Constants | belt page — index 1, 16 × 1, in the image | `data:0x0074479C` | ? | ? | ? | 1 |
| 7 | 77 | Constants | page bytes — 0 inventory, 1 and 2 trade, 3 cube, 4 … | `0x00628280` | ? | ? | ? | 1 |
| 8 | 78 | Constants | item modes — 0 on a page, 1 on the body, 2 … | `fn:sub_00549150_PktInvItemBad@0x00549150` | ? | ? | ? | 1 |
| 9 | 82 | Constants | pickup reach — d < 5; nothing at d ≥ 51 | `0x00548C60` | ? | ? | ? | 1 |
| 10 | 83 | Constants | pickup line mask | `0x00548C7E` | ? | ? | ? | 1 |
| 11 | 85 | Constants | The cell mask's constant is J1's note: its value is | `0x00555DE4` | ? | ? | ? | 1 |
| 12 | 92 | How to read the tags | … a named callee's entry; the callee and all code after it are not covered, "after, | – | ? | ? | ? | 1 |
| 13 | 97 | How to read the tags | . Two outcomes in § E and § F rest on a packet field written … | run:2026-11-04-inventory | ? | ? | ? | 2 |
| 14 | 98 | How to read the tags | : a code reading no case reaches, with the addresses read. | `fn:sub_00563560_PickupToInv@0x00563560` | ? | ? | ? | 1 |
| 15 | 130 | A. Pages and rows | A4. InvPageGet(inv, page, row): | `fn:sub_0063ADD0_InvPageGet@0x0063ADD0` | ? | ? | ? | 1 |
| 16 | 136 | A. Pages and rows | Each server caller of the page's row that was read passes game+ as expansion where … | `0x00560297` | ? | ? | ? | 1 |
| 17 | 137 | A. Pages and rows | Rows 13 and 29 (Hireling) are never returned. Types , are object classes, and no … | `0x00483705` | ? | ? | ? | 1 |
| 18 | 139 | A. Pages and rows | The second sets are the client's. All 10 calls of the inventory reader at xxxx … | `fn:sub_0065C1F0_InvRecordGrid@0x0065C1F0` | ? | ? | ? | 1 |
| 19 | 140 | A. Pages and rows | In a save moved between game types this would be the stash's refusal; no run … | `0x0063AE5A` | ? | ? | ? | 1 |
| 20 | 188 | B. The placement search | After: | `0x0063B1BF` | ? | ? | ? | 1 |
| 21 | 206 | B. The placement search | The branches for h = 3 and w ≤ 2, for 2 × 2 and … | `0x0063B790` | ? | ? | ? | 1 |
| 22 | 208 | B. The placement search | A player's search fails only where no spot fits: a best of 0 needs a … | `fn:sub_0063B490_InvSpotFindRow@0x0063B490` | ? | ? | ? | 1 |
| 23 | 209 | B. The placement search | InvGridFree tests no bound itself; InvPlaceItem's direct branch clamps a negative x, y to 0 … | `0x005602BE` | ? | ? | ? | 1 |
| 24 | 210 | B. The placement search | … InvGridPut, 500 cases with 275 distinct outcomes: the search as the caller uses it. After, | `0x0063B950` | ? | ? | ? | 1 |
| 25 | 215 | C. Placing on a page | C1. InvPlaceItem(…, x, y, 0, 1, 0): | `fn:sub_00560200_InvPlaceItem@0x00560200` | ? | ? | ? | 1 |
| 26 | 220 | C. Placing on a page | C2. ItemSkillQtyAdjust(add) : | `fn:sub_0055C110_ItemSkillQtyAdjust@0x0055C110` | ? | ? | ? | 1 |
| 27 | 227 | C. Placing on a page | So a scroll or tome placed in the stash adds nothing to the skill. holds … | `0x0055C110` | ? | ? | ? | 1 |
| 28 | 235 | D. The requests | , — UnitInteract(type ≤ 5, guid, action); 's action is 0 … | `fn:sub_00548B00_UnitInteract@0x00548B00` | ? | ? | ? | 1 |
| 29 | 236 | D. The requests |  — a cursor item; InteractIsPlayer(0) non-zero returns 3; CursorDrop | `fn:sub_00563C00_CursorDrop@0x00563C00` | ? | ? | ? | 1 |
| 30 | 237 | D. The requests |  — § E; ItemSetPage(item, page), then InvPlaceItem(…, x, y, 0, … | `fn:sub_00560200_InvPlaceItem@0x00560200` | ? | ? | ? | 1 |
| 31 | 238 | D. The requests |  — an owned item, empty cursor, not page 1; trade … | `fn:sub_00560420_InvItemToCursor@0x00560420` | ? | ? | ? | 1 |
| 32 | 239 | D. The requests | .. — equip and swap with a body location ('s slot … | `fn:sub_005606B0_ItemEquip@0x005606B0` | ? | ? | ? | 1 |
| 33 | 240 | D. The requests |  — the cursor against a page item, not an item … | `fn:sub_00561B00_PageSwapCursor@0x00561B00` | ? | ? | ? | 1 |
| 34 | 241 | D. The requests |  — two owned items, unequal guids; StackRequest (§ G) | `fn:sub_0055E7C0_StackRequest@0x0055E7C0` | ? | ? | ? | 1 |
| 35 | 242 | D. The requests |  — an owned item; the stub (§ G) | `0x0055E9A0` | ? | ? | ? | 1 |
| 36 | 243 | D. The requests |  — a cursor item; ItemToBelt(guid, box, 0) | `fn:sub_0055E9B0_ItemToBelt@0x0055E9B0` | ? | ? | ? | 1 |
| 37 | 244 | D. The requests |  — a belt item, trade test, empty cursor; BeltToCursor | `fn:sub_00562250_BeltToCursor@0x00562250` | ? | ? | ? | 1 |
| 38 | 245 | D. The requests |  — a cursor item and a belt item; BeltSwapCursor | `fn:sub_0055EB30_BeltSwapCursor@0x0055EB30` | ? | ? | ? | 1 |
| 39 | 246 | D. The requests |  — an inventory-page beltable item, empty cursor: BeltFreeSlot, then to … | `fn:sub_0054D520_SrvPacket63Handler@0x0054D520` | ? | ? | ? | 1 |
| 40 | 248 | D. The requests | Lengths, tested first by each handler: 5 bytes , , , , ; 9 bytes … | `0x0054AB43` | ? | ? | ? | 1 |
| 41 | 253 | E. Pages and the stash: , | E1. Packet for a player, in order: | `0x0054ABE5` | ? | ? | ? | 1 |
| 42 | 264 | E. Pages and the stash: , | E2. Packet : InvItemToCursor(…, 1, 0, 0, 0): | `fn:sub_00560420_InvItemToCursor@0x00560420` | ? | ? | ? | 1 |
| 43 | 271 | E. Pages and the stash: , | A placed item needs no open stash, on this reading. The packet's item is on … | `fn:sub_00535060_PlayerIsBusy@0x00535060` | ? | ? | ? | 1 |
| 44 | 272 | E. Pages and the stash: , | Forced, one case: to page 4 with no stash open, in town (level 103), was … | run:2026-11-04-inventory | ? | ? | ? | 2 |
| 45 | 273 | E. Pages and the stash: , | A refused item keeps the new page byte on the cursor, since the page is … | `0x0054AC68` | ? | ? | ? | 1 |
| 46 | 274 | E. Pages and the stash: , | Taking an item off a non-zero page, with an empty cursor, does need an interaction. | `fn:sub_00560420_InvItemToCursor@0x00560420` | ? | ? | ? | 1 |
| 47 | 304 | F. Belts | F3. ItemAutoBeltTest(item) → 1: | `0x00628BFD` | ? | ? | ? | 1 |
| 48 | 306 | F. Belts | F4. ItemToBelt(guid, box, 0) (packet ): | `0x0063C4C0` | ? | ? | ? | 1 |
| 49 | 309 | F. Belts | F5. Packet : BeltToCursor; the box's column shifts down (BeltColumnShift) | `fn:sub_00562250_BeltToCursor@0x00562250` | ? | ? | ? | 1 |
| 50 | 310 | F. Belts | Packet : BeltSwapCursor, in place, no shift | `fn:sub_0055EB30_BeltSwapCursor@0x0055EB30` | ? | ? | ? | 1 |
| 51 | 311 | F. Belts | Packet : page 0 and an empty cursor; returns 0 with no room | `fn:sub_0054D520_SrvPacket63Handler@0x0054D520` | ? | ? | ? | 1 |
| 52 | 312 | F. Belts | F6. BeltOverflow(new belt or null): | `fn:sub_005608C0_BeltOverflow@0x005608C0` | ? | ? | ? | 1 |
| 53 | 320 | F. Belts | At a corpse's making: PLAYER_CorpseCreate's loop over the slots | `0x0057F90E` | ? | ? | ? | 1 |
| 54 | 322 | F. Belts | A row with autobelt 0 (stock isc, tsc, yps, vps, wms among them) is in … | `0x0063C731` | ? | ? | ? | 1 |
| 55 | 323 | F. Belts | So the pickup's belt branch always calls BeltPlace, and the column search in it decides. | `0x00563716` | ? | ? | ? | 1 |
| 56 | 324 | F. Belts | Forced, one case: with box 12 on a 12-box belt (a Heavy Belt) stays in … | run:2026-11-04-inventory | ? | ? | ? | 2 |
| 57 | 347 | G. Stacks | After the first set: | `0x0055E623` | ? | ? | ? | 1 |
| 58 | 352 | G. Stacks | G4. StackRequest (packet ): | `fn:sub_0055E7C0_StackRequest@0x0055E7C0` | ? | ? | ? | 1 |
| 59 | 359 | G. Stacks | A negative source, target or maximum ends at the fatal path. The sum is i32: … | `0x0055E5C2` | ? | ? | ? | 1 |
| 60 | 360 | G. Stacks | There is no split on the server. Packet reaches UnstackStub, xor eax, eax; ret 8, … | `0x0054B380` | ? | ? | ? | 1 |
| 61 | 365 | H. The cursor to the ground | H1. CursorDrop(user): | `fn:sub_00563C00_CursorDrop@0x00563C00` | ? | ? | ? | 1 |
| 62 | 372 | H. The cursor to the ground | H2. CubeDropEmptied(item): | `fn:sub_00563840_CubeDropEmptied@0x00563840` | ? | ? | ? | 1 |
| 63 | 377 | H. The cursor to the ground | With fallback 1 a full surround does not give null: the item lands on the … | `fn:sub_00563C00_CursorDrop@0x00563C00` | ? | ? | ? | 1 |
| 64 | 399 | I. Pickup | I1. UnitInteract, the item case: | `fn:sub_00548B00_UnitInteract@0x00548B00` | ? | ? | ? | 1 |
| 65 | 422 | I. Pickup | (all of I4; , , , , ) | `fn:sub_00563560_PickupToInv@0x00563560` | ? | ? | ? | 1 |
| 66 | 436 | I. Pickup | I5. PickupAutoStack: | `fn:sub_00560020_PickupAutoStack@0x00560020` | ? | ? | ? | 1 |
| 67 | 447 | I. Pickup | I6. ItemAutoEquipSlot(user, item, &loc, skipReq): | `fn:sub_0055D710_ItemAutoEquipSlot@0x0055D710` | ? | ? | ? | 1 |
| 68 | 461 | I. Pickup | I7. PickupToCursor: | `fn:sub_0055CF50_PickupToCursor@0x0055CF50` | ? | ? | ? | 1 |
| 69 | 481 | I. Pickup | , not this run's. Pickup's mask does not overlap an item's ; a player's mask … | `fn:sub_00622B50_UnitsLineBlocked@0x00622B50` | ? | ? | ? | 1 |
| 70 | 482 | I. Pickup | The one item request that leaves the drain: d ≥ 5, or d < 5 … | `fn:sub_00548A50_InteractWalkTo@0x00548A50` | ? | ? | ? | 1 |
| 71 | 483 | I. Pickup | Ownership (who dropped it) is not among any test read in the two pickups, and … | `fn:sub_00563560_PickupToInv@0x00563560` | ? | ? | ? | 1 |
| 72 | 484 | I. Pickup | Gold and the party share are items/economy G. | `fn:sub_0055C850_GoldPickup@0x0055C850` | ? | ? | ? | 1 |
| 73 | 485 | I. Pickup | A pickup-merge's remainder stays the same item, its quantity reduced, and goes on down I4 … | `fn:sub_0055D0D0_PickupStackMerge@0x0055D0D0` | ? | ? | ? | 1 |
| 74 | 561 | J. The ground drop's cell | The cell mask's bits and are not decided. Removing either fails 0, since the cell … | `0x00555DE4` | ? | ? | ? | 1 |
| 75 | 563 | J. The ground drop's cell | The bits' names are drlg/collision's: has bits 0, 9, 10, 11, 12, 13; bits 0 … | `0x00555DE4` | ? | ? | ? | 1 |
| 76 | 567 | J. The ground drop's cell | The search makes no draw: it is given no seed, and the 567 functions of … | `fn:sub_00555DA0_GroundDropCell@0x00555DA0` | ? | ? | ? | 1 |
| 77 | 568 | J. The ground drop's cell | A refused allocation is the fatal line , and gives no output. | `0x0064DEF4` | ? | ? | ? | 1 |
| 78 | 570 | J. The ground drop's cell | The 128 is declared to the run; by the reading the loader stores half the … | `0x0066A344` | ? | ? | ? | 1 |
| 79 | 576 | J4. Who drops, and with what | Direct calls: 20 of the search, all with size 1 and fallback 1. Its callers: … | `fn:sub_0055A550_DropCreateItem@0x0055A550` | ? | ? | ? | 1 |
| 80 | 577 | J4. Who drops, and with what | Of the pair form's 7 direct calls: the search; four item-drop bodies that inline the … | `0x0055923B` | ? | ? | ? | 1 |
| 81 | 578 | J4. Who drops, and with what | A null room from the search: CursorDrop and DropCreateItem test it and do nothing (the … | `0x0057A19A` | ? | ? | ? | 1 |
| 82 | 579 | J4. Who drops, and with what | Draws beside the search. MissDo18ChestSpawner draws twice on its unit's seed for an offset (RNG_RangeB(2n … | `fn:sub_005AF300_MissDo18ChestSpawner@0x005AF300` | ? | ? | ? | 1 |
| 83 | 584 | J5. Seeds around a cursor drop | A monster's drop inside a death: a seed trace through the drain was not built. … | `fn:sub_0055A550_DropCreateItem@0x0055A550` | ? | ? | ? | 1 |
| 84 | 606 | K. A ground item's life | if flag ≠ 0: QUESTS_RaiseItemDropped, last | `0x00558B1C` | ? | ? | ? | 1 |
| 85 | 620 | K. A ground item's life | After: | `0x00558B90` | ? | ? | ? | 1 |
| 86 | 624 | K. A ground item's life | holds for each row until its own note lifts part of it. | `fn:sub_00558D90_ItemCreate@0x00558D90` | ? | ? | ? | 1 |
| 87 | 637 | K. A ground item's life | Quality 9 is in the code's 5..9; no stock path makes one (the cube's tempered … | `fn:sub_00558A10_ItemGroundExpiry@0x00558A10` | ? | ? | ? | 1 |
| 88 | 640 | K. A ground item's life | So 15 000 frames is 10 minutes at 25 a second, and the free falls … | `fn:sub_00558B90_ActExpiredItemsFree@0x00558B90` | ? | ? | ? | 1 |
| 89 | 642 | K. A ground item's life | "Never swept" stays the reading: a longer life than that session, DropGoldPile, and any writer … | `fn:sub_00558D90_ItemCreate@0x00558D90` | ? | ? | ? | 1 |
| 90 | 643 | K. A ground item's life | … and the expiry's write, K1. Its callers, beyond CursorDrop, are a reading: 12 direct calls. | `fn:sub_00558AA0_ItemPlaceOnGround@0x00558AA0` | ? | ? | ? | 1 |
| 91 | 645 | K. A ground item's life | Not observed: a saved word of 0 ("0 stays 0") and saved equal to the … | `0x005419FC` | ? | ? | ? | 1 |
| 92 | 648 | K. A ground item's life | for that run, which did not log its inputs; logged them. | run:2026-11-04-inventory-2 | ? | ? | ? | 1 |
| 93 | 655 | L. Draws per seed | Closures under , : 560 and 632 functions, 0 … — 0 in direct calls | `0x0063C600` | ? | ? | ? | 1 |
| 94 | 656 | L. Draws per seed | GroundDropCell, FieldWalkBlocked, ItemGroundExpiry, the distance — no seed is given; closures of 567, 551, 556, … | `fn:sub_00555DA0_GroundDropCell@0x00555DA0` | ? | ? | ? | 1 |
| 95 | 657 | L. Draws per seed | ItemPlaceOnGround: closure 711 functions, 1 with a step: RNG_RangeB … — 0 for an item | `0x00624563` | ? | ? | ? | 1 |
| 96 | 659 | L. Draws per seed | The moves , , , , , , , … — not bounded | `0x00563560` | ? | ? | ? | 1 |
| 97 | 661 | L. Draws per seed | No move's own body holds a draw; a whole move's bound past the two logged … | `0x00563560` | ? | ? | ? | 1 |
| 98 | 680 | Worked example | … the sequences are not logged in a game, items/0013 § 10 cases 1 and 2). | `fn:sub_0063B850_InvSpotFindBySize@0x0063B850` | ? | ? | ? | 1 |
| 99 | 691 | Reimplementation notes | sets the page before the placement: a refused item carries the new page byte. | `0x0054AC68` | ? | ? | ? | 1 |
| 100 | 692 | Reimplementation notes | DropGoldAmount passes fallback 0; every other direct drop passes 1. | `0x0055A15C` | ? | ? | ? | 1 |
| 101 | 694 | Reimplementation notes | … is not specified here. Pages 1 and 2 and the trade test are named only. | `0x00535610` | ? | ? | ? | 1 |
