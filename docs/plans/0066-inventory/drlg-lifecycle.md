# Plan 0066 inventory: drlg/lifecycle

- **Spec:** [drlg/lifecycle](../../specs/drlg/lifecycle.md), read at `main` `b5999f5e`.
- **Front matter `I`:** 78; the *Count* column sums to 78.
- Classes, batches and conventions as in [the inventory README](README.md#conventions).

| # | Line | Section | Claim (excerpt) | Anchor | Class | Route or reason | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | 47 | Entry points | Every game frame | `fn:sub_0052D870_GameTick@0x0052D870` | ? | ? | ? | 1 |
| 2 | 50 | Entry points | A room is needed at once (warp, waypoint, level … | `fn:sub_0061B730_RoomActivateB@0x0061B730` | ? | ? | ? | 1 |
| 3 | 103 | Constants | wanderer gate — the mask's width (§ I) | `0x0054F089` | ? | ? | ? | 1 |
| 4 | 104 | Constants | wanderer roll — for the draw and the mod 100 ≥ 3 … | `fn:sub_0054EFF0_WandererRoll@0x0054EFF0` | ? | ? | ? | 1 |
| 5 | 113 | A. The frame | NewRoomsUpdate (rank 3, § D), the unit events, where players move (ranks 4 to 13), … | – | ? | ? | ? | 1 |
| 6 | 116 | A. The frame | The remainders are signed % on the incremented frame. A room activated in frame N … | – | ? | ? | ? | 1 |
| 7 | 122 | A. The frame | Three other callers populate a room at once through RoomUpdateOne (the same body for one … | – | ? | ? | ? | 1 |
| 8 | 125 | A. The frame | The expiry sweep of item records runs every 1 500 frames. GameTick calls on every … | `0x0052D310` | ? | ? | ? | 1 |
| 9 | 137 | A. The frame | first one reached; the emulation stops at UnitGetRoom, so the code after it stays | – | ? | ? | ? | 1 |
| 10 | 139 | A. The frame | After that boundary the unit is unlinked, sent to every player and freed. | – | ? | ? | ? | 1 |
| 11 | 145 | A. The frame | Past that, a monster's or chest's drop has + 0 until its room has deactivated. … | – | ? | ? | ? | 1 |
| 12 | 156 | A. The frame | Its callers beyond CursorDrop are a reading: an overflow, DropGoldAmount, NPC menus, the cube's. | `fn:sub_0055A090_DropGoldAmount@0x0055A090` | ? | ? | ? | 1 |
| 13 | 242 | B. Activation: reference counts per near-list distance | A reference counts paths, not rooms: a room reached through several near lists at the … | – | ? | ? | ? | 1 |
| 14 | 245 | B. Activation: reference counts per near-list distance | On the server a client therefore activates every room of its room's near list (which … | – | ? | ? | ? | 1 |
| 15 | 249 | B. Activation: reference counts per near-list distance | RoomActivateA adds to the build of DRLG_RoomActivate (room-tiles) only the neighbour step | – | ? | ? | ? | 1 |
| 16 | 254 | B. Activation: reference counts per near-list distance | RoomActivateB is the on-demand variant (warp destination, waypoint room, level point, preset level build): it | – | ? | ? | ? | 1 |
| 17 | 262 | B. Activation: reference counts per near-list distance | Client copy. The client act runs the same reference code from its own loop (/, … | `0x0045CB0C` | ? | ? | ? | 1 |
| 18 | 281 | C. The client lists (+) | In general + is the number of clients whose current room's near list holds the … | – | ? | ? | ? | 1 |
| 19 | 284 | C. The client lists (+) | A room just activated by a client already has + ≥ 1 at its first … | – | ? | ? | ? | 1 |
| 20 | 308 | D. The new-rooms walk: populate once, restore once per activ | No code clears bit 1 (every caller of RoomRestoredSet passes 1), and it lives in … | – | ? | ? | ? | 1 |
| 21 | 311 | D. The new-rooms walk: populate once, restore once per activ | On a first activation the restore finds no record and draws nothing (objects § B … | – | ? | ? | ? | 1 |
| 22 | 352 | E. Release | never taken, 0 on the server at every pass | `0x0061A3F0` | ? | ? | ? | 1 |
| 23 | 355 | E. Release | if R's act is a client act: fatal error ; | `0x0061BA30` | ? | ? | ? | 1 |
| 24 | 358 | E. Release | for level 120, not reached | `0x0061BA30` | ? | ? | ? | 1 |
| 25 | 361 | E. Release | E3. ActiveRoomFree(act, room): | `fn:sub_0061A910_ActiveRoomFree@0x0061A910` | ? | ? | ? | 1 |
| 26 | 384 | E. Release | Pins. RoomPinSet(room, 0) sets and RoomPinSet(room, 1) clears it (RoomPinSet passes the | – | ? | ? | ? | 1 |
| 27 | 389 | E. Release | The 31 pin sites. RoomPinSet has 31 direct call sites in 24 functions: 18 set … | – | ? | ? | ? | 1 |
| 28 | 406 | E. Release | Level unload. Every 11 frames on the server (every 13 ticks on the client) the … | – | ? | ? | ? | 1 |
| 29 | 419 | E. Release | No reader of was found: the only + access with that immediate is the write … | `0x0066F232` | ? | ? | ? | 1 |
| 30 | 461 | F. The save rule | type 0 (player): state 7 (playerbody) → save, kept; else nothing ; | `0x005433F0` | ? | ? | ? | 1 |
| 31 | 463 | F. The save rule | if kept: (if save: record) and unlink u from the room without freeing it ; | `0x005433F0` | ? | ? | ? | 1 |
| 32 | 467 | F. The save rule | F2. InactiveMonsterSaveTest(game, u) → (save, kept), in this order: | `fn:sub_005431F0_InactiveMonsterSaveTest@0x005431F0` | ? | ? | ? | 1 |
| 33 | 469 | F. The save rule | when both are clear, never met | `0x005431F9` | ? | ? | ? | 1 |
| 34 | 494 | F. The save rule | Tests 3, 4, 6 and 7 and restore 0 were not reached (no pet or … | – | ? | ? | ? | 1 |
| 35 | 503 | F. The save rule | Not met for objects: the sparkle bit (never set on a tested object) and a … | – | ? | ? | ? | 1 |
| 36 | 509 | F. The save rule | So a dead champion is not saved on stock data: every server write of the … | – | ? | ? | ? | 1 |
| 37 | 519 | F. The save rule | A player's own room is always in its near set, so a released room holds … | – | ? | ? | ? | 1 |
| 38 | 529 | G. The records | room record — x, + y (the key); + item list; + … | `fn:sub_00541D20_InactiveRoomRecordFind@0x00541D20` | ? | ? | ? | 1 |
| 39 | 531 | G. The records | item record — next; + expiry; + (item); + n; + the … | `fn:sub_00541B10_InactiveItemSave@0x00541B10` | ? | ? | ? | 1 |
| 40 | 568 | G. The records |  — for , , , , //, , ; for | `fn:sub_005421A0_InactiveMonsterSave@0x005421A0` | ? | ? | ? | 1 |
| 41 | 569 | G. The records |  — group leader id (AI control + when the AI … | `fn:sub_005421A0_InactiveMonsterSave@0x005421A0` | ? | ? | ? | 1 |
| 42 | 570 | G. The records | +, +, + — AI control +; the preset path moved out of … | `fn:sub_00541FE0_InactiveMonAiSave@0x00541FE0` | ? | ? | ? | 1 |
| 43 | 571 | G. The records |  — monster data + | `fn:sub_005421A0_InactiveMonsterSave@0x005421A0` | ? | ? | ? | 1 |
| 44 | 572 | G. The records | +, +, + — for the mods , for the others | `fn:sub_005421A0_InactiveMonsterSave@0x005421A0` | ? | ? | ? | 1 |
| 45 | 574 | G. The records | +, + — AI parameters (InactiveMonAiSave) | `fn:sub_00541FE0_InactiveMonAiSave@0x00541FE0` | ? | ? | ? | 1 |
| 46 | 576 | G. The records |  — next record of the room's monster list | `fn:sub_005421A0_InactiveMonsterSave@0x005421A0` | ? | ? | ? | 1 |
| 47 | 585 | G. The records | Before writing it, the save removes the states of the list at DataTables + and … | – | ? | ? | ? | 1 |
| 48 | 594 | G. The records | The only immediate store of bit into unit + is in | `0x0064C040` | ? | ? | ? | 1 |
| 49 | 599 | G. The records | What a monster loses: its states and timers, any mode but "dying or dead" (alive … | – | ? | ? | ? | 1 |
| 50 | 619 | G. The records | Stat 14 is compared signed. | `fn:sub_00558A10_ItemGroundExpiry@0x00558A10` | ? | ? | ? | 1 |
| 51 | 647 | H. The restore | kept: portals, a player corpse, mode 17 else fatal | `0x00542B40` | ? | ? | ? | 1 |
| 52 | 652 | H. The restore | H2. InactiveMonstersRestore(game, room), per monster record, oldest first: | `fn:sub_005424F0_InactiveMonstersRestore@0x005424F0` | ? | ? | ? | 1 |
| 53 | 655 | H. The restore | … and rec.flags & ( / ): drop ; alignment 1 or 2; for 2 , | `0x00542609` | ? | ? | ? | 1 |
| 54 | 672 | H. The restore | if none: a SpawnPosPick position, then SpawnWithId there ; | `0x005424F0` | ? | ? | ? | 1 |
| 55 | 673 | H. The restore | if none: COLL_FindFreeSpiral ; | `0x005424F0` | ? | ? | ? | 1 |
| 56 | 675 | H. The restore | H2b. SpecialMonRestore(rec): | `fn:sub_005A4440_SpecialMonRestore@0x005A4440` | ? | ? | ? | 1 |
| 57 | 679 | H. The restore | the pushed 0 is the minions argument | `0x005A454E` | ? | ? | ? | 1 |
| 58 | 682 | H. The restore | H2c. MinionRestore(rec): | `fn:sub_005A46E0_MinionRestore@0x005A46E0` | ? | ? | ? | 1 |
| 59 | 688 | H. The restore | H3. on a created unit u, in this order: | `0x005427FB` | ? | ? | ? | 1 |
| 60 | 711 | H. The restore | The path is picked by flag before flag 1, so a record with both goes … | – | ? | ? | ? | 1 |
| 61 | 736 | H. The restore | flag-0 reading of H2c stays | run:2026-10-17-lifecycle | ? | ? | ? | 1 |
| 62 | 745 | H. The restore | The 0 that SpecialMonRestore pushes is the minions argument of SpecialModsApply (pushed at , | `0x005A454E` | ? | ? | ? | 1 |
| 63 | 749 | H. The restore | MinionRestore calls the handlers itself with flag 0 (mods 1–4 at , its nine saved … | `0x005A4811` | ? | ? | ? | 1 |
| 64 | 760 | H. The restore | The + bit is set only when the record's saved + (record +) has it, … | – | ? | ? | ? | 1 |
| 65 | 764 | H. The restore | A dead special saved without or would come back alive: SpecialMonRestore places the unit | – | ? | ? | ? | 1 |
| 66 | 767 | H. The restore | A record with alignment 0 (the only one the drop lets through) reaches the fatal … | – | ? | ? | ? | 1 |
| 67 | 776 | H. The restore | H4. InactiveItemsRestore(game, room, recs), oldest first: except the lines tagged | `fn:sub_00541AC0_InactiveItemsRestore@0x00541AC0` | ? | ? | ? | 1 |
| 68 | 783 | H. The restore | socketed children re-created with it ; | `0x00541990` | ? | ? | ? | 1 |
| 69 | 784 | H. The restore | it.expiry ← 0 if rec.expiry = 0 ; | `0x00541990` | ? | ? | ? | 1 |
| 70 | 845 | H5. The grid marks of a re-created monster | The call path, read in the pinned image: a room whose driver flag bit 0 … | – | ? | ? | ? | 1 |
| 71 | 875 | I. The wanderer tick | I1. RoomWandererTick(game, room): for the first draw, the roll's draw and its ≥ 3 return, | `fn:sub_0054F060_RoomWandererTick@0x0054F060` | ? | ? | ? | 1 |
| 72 | 877 | I. The wanderer tick | if room.seed.low & ≠ 0: return ; ; the mask's width | run:2026-10-17-lifecycle | ? | ? | ? | 1 |
| 73 | 878 | I. The wanderer tick | if room[+] ≠ 0 or Levels[level].MonWndr = 0: return ; | `0x0054F096` | ? | ? | ? | 1 |
| 74 | 882 | I. The wanderer tick | if region[+] ≥ 3: return ; | `0x0054F041` | ? | ? | ? | 1 |
| 75 | 900 | I. The wanderer tick | That one pass does not separate the rest: the mask's width (its low word had … | – | ? | ? | ? | 1 |
| 76 | 906 | I. The wanderer tick | Because of +, wanderers can appear only in active rooms that no client is near: … | – | ? | ? | ? | 1 |
| 77 | 915 | J. The preset path and the preset list | The release moves the path into the monster record | `0x00542098` | ? | ? | ? | 1 |
| 78 | 918 | J. The preset path and the preset list | A re-activated room never re-dispatches its preset list: RoomPresetUnits runs only while flags bit 0 … | – | ? | ? | ? | 1 |
