# Plan 0066 inventory: drlg/lifecycle

- **Spec:** [drlg/lifecycle](../../specs/drlg/lifecycle.md), read at `main` `b5999f5e`.
- **Front matter `I`:** 78; the *Count* column sums to 78.
- Classes, batches and conventions as in [the inventory README](README.md#conventions).

| # | Line | Section | Claim (excerpt) | Anchor | Class | Route or reason | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | 47 | Entry points | Every game frame | `fn:sub_0052D870_GameTick@0x0052D870` | a-logs | frame-window logs (run:2026-11-04-frame2, -frame3): RU0, TM and RR lines inside each FT0..FT1, one GameTick per frame | S7b | 1 |
| 2 | 50 | Entry points | A room is needed at once (warp, waypoint, level … | `fn:sub_0061B730_RoomActivateB@0x0061B730` | c | r2 `axt` on `RoomActivateB`: warp, waypoint, level point and preset-build callers only | S7a | 1 |
| 3 | 103 | Constants | wanderer gate — the mask's width (§ I) | `0x0054F089` | c-emu | the wanderer gate emulated with low words whose bit 15 is set (`0x7FFF` against `0xFFFF`) | S7e | 1 |
| 4 | 104 | Constants | wanderer roll — for the draw and the mod 100 ≥ 3 … | `fn:sub_0054EFF0_WandererRoll@0x0054EFF0` | a-run | the wanderer logger of run:2026-10-21-sweep-monsters-a in more sessions, to a roll below 3 and its region test | H7d | 1 |
| 5 | 113 | A. The frame | NewRoomsUpdate (rank 3, § D), the unit events, where players move (ranks 4 to 13), … | – | a-logs | frame-window logs (run:2026-11-04-frame2, -frame3): RU0 at rank 3, TM D12 at rank 18, U11 at 19, the sweep at 20, in B1's order | S7b | 1 |
| 6 | 116 | A. The frame | The remainders are signed % on the incremented frame. A room activated in frame N … | – | a-logs | frame-window logs (run:2026-11-04-frame2, -frame3): an RC at rank 14 of frame N and that room's first RU0 at frame N + 1 | S7b | 1 |
| 7 | 122 | A. The frame | Three other callers populate a room at once through RoomUpdateOne (the same body for one … | – | c | r2 `axt` on `RoomUpdateOne`: the three callers at 0x0055379D, 0x0056CF7D, 0x0059E018 | S7a | 1 |
| 8 | 125 | A. The frame | The expiry sweep of item records runs every 1 500 frames. GameTick calls on every … | `0x0052D310` | a-logs | frame-window logs (run:2026-11-04-frame2, -frame3): TM S1500 lines exactly at frame mod 1500 = 0 | S7b | 1 |
| 9 | 137 | A. The frame | first one reached; the emulation stops at UnitGetRoom, so the code after it stays | – | c-emu | `ActExpiredItemsFree` emulated past `UnitGetRoom` with it as a declared boundary (extends run:2026-11-04-ground-emu) | S7e | 1 |
| 10 | 139 | A. The frame | After that boundary the unit is unlinked, sent to every player and freed. | – | b | as sim/frame row 76: a new frame.gdb line at `ActExpiredItemsFree`'s free, a window where a drop expires | H7b | 1 |
| 11 | 145 | A. The frame | Past that, a monster's or chest's drop has + 0 until its room has deactivated. … | – | c | a writer scan with a second tool of item data `+0x24` including block copies and `ItemCreate`'s deeper chains | S7a | 1 |
| 12 | 156 | A. The frame | Its callers beyond CursorDrop are a reading: an overflow, DropGoldAmount, NPC menus, the cube's. | `fn:sub_0055A090_DropGoldAmount@0x0055A090` | c | r2 `axt` on the drop functions beyond `CursorDrop` | S7a | 1 |
| 13 | 242 | B. Activation: reference counts per near-list distance | A reference counts paths, not rooms: a room reached through several near lists at the … | – | a-logs | rooms.gdb logs (run:2026-10-17-lifecycle, -h7a-lifecycle): reference counts per path at each enter call, a new check against `DrlgRefAddNear`'s rule | S7d | 1 |
| 14 | 245 | B. Activation: reference counts per near-list distance | On the server a client therefore activates every room of its room's near list (which … | – | a-logs | rooms.gdb logs (run:2026-10-17-lifecycle, -h7a-lifecycle): every room of the client room's near list active (the several-client union is d-2c) | S7d | 1 |
| 15 | 249 | B. Activation: reference counts per near-list distance | RoomActivateA adds to the build of DRLG_RoomActivate (room-tiles) only the neighbour step | – | a-logs | frame-window logs (run:2026-11-04-frame2, -frame3): RC lines' flags `f` and the act list's order (prepend); rooms.gdb logs (run:2026-10-17-lifecycle, -h7a-lifecycle) for the act counters | S7b | 1 |
| 16 | 254 | B. Activation: reference counts per near-list distance | RoomActivateB is the on-demand variant (warp destination, waypoint room, level point, preset level build): it | – | a-logs | rooms.gdb logs (run:2026-10-17-lifecycle, -h7a-lifecycle): rooms activated by waypoint or warp (`RoomActivateB`) get no reference and stay status 4 | S7d | 1 |
| 17 | 262 | B. Activation: reference counts per near-list distance | Client copy. The client act runs the same reference code from its own loop (/, … | `0x0045CB0C` | b | new client-side rooms.gdb lines at `ClientBackgroundBuild` and the client unload tick | H7d | 1 |
| 18 | 281 | C. The client lists (+) | In general + is the number of clients whose current room's near list holds the … | – | d-2c | a count of clients and a sorted client list need two clients | – | 1 |
| 19 | 284 | C. The client lists (+) | A room just activated by a client already has + ≥ 1 at its first … | – | a-logs | rooms.gdb logs (run:2026-10-17-lifecycle, -h7a-lifecycle): `+0x78` at a client-activated room's first walk | S7d | 1 |
| 20 | 308 | D. The new-rooms walk: populate once, restore once per activ | No code clears bit 1 (every caller of RoomRestoredSet passes 1), and it lives in … | – | c | r2 `axt` on `RoomRestoredSet` with the pushed argument at each site | S7a | 1 |
| 21 | 311 | D. The new-rooms walk: populate once, restore once per activ | On a first activation the restore finds no record and draws nothing (objects § B … | – | a-logs | rooms.gdb logs (run:2026-10-17-lifecycle, -h7a-lifecycle): first activations' restores find no record and leave the seeds unchanged | S7d | 1 |
| 22 | 352 | E. Release | never taken, 0 on the server at every pass | `0x0061A3F0` | d-none | a fatal guard stock play never meets | – | 1 |
| 23 | 355 | E. Release | if R's act is a client act: fatal error ; | `0x0061BA30` | d-none | a fatal guard stock play never meets | – | 1 |
| 24 | 358 | E. Release | for level 120, not reached | `0x0061BA30` | a-run | rooms.gdb sessions in level 120 (the Arreat Summit) | H7d | 1 |
| 25 | 361 | E. Release | E3. ActiveRoomFree(act, room): | `fn:sub_0061A910_ActiveRoomFree@0x0061A910` | a-logs | frame-window logs (run:2026-11-04-frame2, -frame3) RR lines and rooms.gdb logs (run:2026-10-17-lifecycle, -h7a-lifecycle) releases against E3 | S7d | 1 |
| 26 | 384 | E. Release | Pins. RoomPinSet(room, 0) sets and RoomPinSet(room, 1) clears it (RoomPinSet passes the | – | a-run | rooms.gdb sessions that free a pinned object or close a portal (the clear sites) | H7d | 1 |
| 27 | 389 | E. Release | The 31 pin sites. RoomPinSet has 31 direct call sites in 24 functions: 18 set … | – | c | r2 `axt` on `RoomPinSet` with the pushed argument at each of the 31 sites | S7a | 1 |
| 28 | 406 | E. Release | Level unload. Every 11 frames on the server (every 13 ticks on the client) the … | – | c-emu | as sim/frame row 75: `ActLevelsUnloadTick` emulated, the countdown and re-arm | S7e | 1 |
| 29 | 419 | E. Release | No reader of was found: the only + access with that immediate is the write … | `0x0066F232` | c | exhaustive second-tool scan for readers of `0x200000` in DRLG room `+0x28` | S7a | 1 |
| 30 | 461 | F. The save rule | type 0 (player): state 7 (playerbody) → save, kept; else nothing ; | `0x005433F0` | b | a pilot step where the character dies and leaves its body behind, then the room is released (rooms.gdb) | H7d | 1 |
| 31 | 463 | F. The save rule | if kept: (if save: record) and unlink u from the room without freeing it ; | `0x005433F0` | b | as row 30: the kept body unlinked without being freed | H7d | 1 |
| 32 | 467 | F. The save rule | F2. InactiveMonsterSaveTest(game, u) → (save, kept), in this order: | `fn:sub_005431F0_InactiveMonsterSaveTest@0x005431F0` | a-logs | rooms.gdb logs (run:2026-10-17-lifecycle, -h7a-lifecycle): `rooms.py check` over the save tests' order, the tests reached | S7d | 1 |
| 33 | 469 | F. The save rule | when both are clear, never met | `0x005431F9` | a-run | rooms.gdb in a level whose `SaveMonsters` is 0, found by a full-table check of Levels | H7d | 1 |
| 34 | 494 | F. The save rule | Tests 3, 4, 6 and 7 and restore 0 were not reached (no pet or … | – | a-run | rooms.gdb with a Necromancer's summons and a mercenary left in a released room | H7d | 1 |
| 35 | 503 | F. The save rule | Not met for objects: the sparkle bit (never set on a tested object) and a … | – | a-run | rooms.gdb with a town portal's room released (classes 59, 60 kept) | H7d | 1 |
| 36 | 509 | F. The save rule | So a dead champion is not saved on stock data: every server write of the … | – | c | exhaustive second-tool scan of writes of the champion bit `0x04` and clears of `0x08` | S7a | 1 |
| 37 | 519 | F. The save rule | A player's own room is always in its near set, so a released room holds … | – | a-logs | rooms.gdb logs (run:2026-10-17-lifecycle, -h7a-lifecycle): no released room holds the player | S7d | 1 |
| 38 | 529 | G. The records | room record — x, + y (the key); + item list; + … | `fn:sub_00541D20_InactiveRoomRecordFind@0x00541D20` | c | writer/reader pair: `InactiveRoomRecordFind` against the saves' writes, second tool | S7f | 1 |
| 39 | 531 | G. The records | item record — next; + expiry; + (item); + n; + the … | `fn:sub_00541B10_InactiveItemSave@0x00541B10` | c | writer/reader pair: `InactiveItemSave` against `InactiveItemRestoreOne`'s reads | S7f | 1 |
| 40 | 568 | G. The records |  — for , , , , //, , ; for | `fn:sub_005421A0_InactiveMonsterSave@0x005421A0` | c | writer/reader pair for flag `0x40`: `InactiveMonsterSave` against the restore | S7f | 1 |
| 41 | 569 | G. The records |  — group leader id (AI control + when the AI … | `fn:sub_005421A0_InactiveMonsterSave@0x005421A0` | c | writer/reader pair: `InactiveMonsterSave`'s `+0x1C` against the restore's read | S7f | 1 |
| 42 | 570 | G. The records | +, +, + — AI control +; the preset path moved out of … | `fn:sub_00541FE0_InactiveMonAiSave@0x00541FE0` | c | writer/reader pair: `InactiveMonAiSave` against the AI restore | S7f | 1 |
| 43 | 571 | G. The records |  — monster data + | `fn:sub_005421A0_InactiveMonsterSave@0x005421A0` | c | writer/reader pair, as row 41, `+0x2C` | S7f | 1 |
| 44 | 572 | G. The records | +, +, + — for the mods , for the others | `fn:sub_005421A0_InactiveMonsterSave@0x005421A0` | c | writer/reader pair, as row 41: name seed and superunique id | S7f | 1 |
| 45 | 574 | G. The records | +, + — AI parameters (InactiveMonAiSave) | `fn:sub_00541FE0_InactiveMonAiSave@0x00541FE0` | c | writer/reader pair, as row 42 | S7f | 1 |
| 46 | 576 | G. The records |  — next record of the room's monster list | `fn:sub_005421A0_InactiveMonsterSave@0x005421A0` | c | writer/reader pair, as row 41: the list link | S7f | 1 |
| 47 | 585 | G. The records | Before writing it, the save removes the states of the list at DataTables + and … | – | c-emu | `InactiveMonsterSave` emulated with states and type-2 timers on the unit (declared read set) | S7e | 1 |
| 48 | 594 | G. The records | The only immediate store of bit into unit + is in | `0x0064C040` | c | exhaustive second-tool scan for immediate stores of `0x2000` to unit `+0xC4` | S7a | 1 |
| 49 | 599 | G. The records | What a monster loses: its states and timers, any mode but "dying or dead" (alive … | – | a-logs | rooms.gdb logs (run:2026-10-17-lifecycle, -h7a-lifecycle): restored monsters' mode, states and timers against the save | S7d | 1 |
| 50 | 619 | G. The records | Stat 14 is compared signed. | `fn:sub_00558A10_ItemGroundExpiry@0x00558A10` | c-emu | `ItemGroundExpiry` emulated with stat 14 negative (extends run:2026-11-04-ground-emu) | S7e | 1 |
| 51 | 647 | H. The restore | kept: portals, a player corpse, mode 17 else fatal | `0x00542B40` | a-run | as row 35: a kept portal relocated at the restore | H7d | 1 |
| 52 | 652 | H. The restore | H2. InactiveMonstersRestore(game, room), per monster record, oldest first: | `fn:sub_005424F0_InactiveMonstersRestore@0x005424F0` | a-logs | rooms.gdb logs (run:2026-10-17-lifecycle, -h7a-lifecycle): restores in record order, oldest first | S7d | 1 |
| 53 | 655 | H. The restore | … and rec.flags & ( / ): drop ; alignment 1 or 2; for 2 , | `0x00542609` | a-run | rooms.gdb with an alignment-1 unit left in a released room | H7d | 1 |
| 54 | 672 | H. The restore | if none: a SpawnPosPick position, then SpawnWithId there ; | `0x005424F0` | b | a staged return where the saved position is occupied, rooms.gdb | H7d | 1 |
| 55 | 673 | H. The restore | if none: COLL_FindFreeSpiral ; | `0x005424F0` | b | as row 54 | H7d | 1 |
| 56 | 675 | H. The restore | H2b. SpecialMonRestore(rec): | `fn:sub_005A4440_SpecialMonRestore@0x005A4440` | a-logs | rooms.gdb logs (run:2026-10-17-lifecycle, -h7a-lifecycle): restored champions and uniques against H2b | S7d | 1 |
| 57 | 679 | H. The restore | the pushed 0 is the minions argument | `0x005A454E` | c | the argument's use at 0x005A2123 read with a second tool | S7f | 1 |
| 58 | 682 | H. The restore | H2c. MinionRestore(rec): | `fn:sub_005A46E0_MinionRestore@0x005A46E0` | a-logs | rooms.gdb logs (run:2026-10-17-lifecycle, -h7a-lifecycle): restored minions against H2c | S7d | 1 |
| 59 | 688 | H. The restore | H3. on a created unit u, in this order: | `0x005427FB` | a-logs | rooms.gdb logs (run:2026-10-17-lifecycle, -h7a-lifecycle): the order of the writes on a restored unit | S7d | 1 |
| 60 | 711 | H. The restore | The path is picked by flag before flag 1, so a record with both goes … | – | c-emu | `InactiveMonstersRestore`'s dispatch emulated with flags 0x20 and 1 both set, the restores as boundaries | S7e | 1 |
| 61 | 736 | H. The restore | flag-0 reading of H2c stays | run:2026-10-17-lifecycle | c | as row 63 | S7f | 1 |
| 62 | 745 | H. The restore | The 0 that SpecialMonRestore pushes is the minions argument of SpecialModsApply (pushed at , | `0x005A454E` | c | as row 57 | S7f | 1 |
| 63 | 749 | H. The restore | MinionRestore calls the handlers itself with flag 0 (mods 1–4 at , its nine saved … | `0x005A4811` | c | `MinionRestore`'s handler calls read with a second tool: flag 0 pushed | S7f | 1 |
| 64 | 760 | H. The restore | The + bit is set only when the record's saved + (record +) has it, … | – | c | writer/reader pair of `+0xC8` bit 0x200 through record `+0x14` | S7f | 1 |
| 65 | 764 | H. The restore | A dead special saved without or would come back alive: SpecialMonRestore places the unit | – | d-none | a record stock play never makes (row 36) | – | 1 |
| 66 | 767 | H. The restore | A record with alignment 0 (the only one the drop lets through) reaches the fatal … | – | d-none | a fatal path no stock record reaches | – | 1 |
| 67 | 776 | H. The restore | H4. InactiveItemsRestore(game, room, recs), oldest first: except the lines tagged | `fn:sub_00541AC0_InactiveItemsRestore@0x00541AC0` | d-none | a pointer to the tagged lines below, no claim of its own | – | 1 |
| 68 | 783 | H. The restore | socketed children re-created with it ; | `0x00541990` | b | a new rooms.gdb line for socketed children at the restore, a socketed item left on the ground | H7d | 1 |
| 69 | 784 | H. The restore | it.expiry ← 0 if rec.expiry = 0 ; | `0x00541990` | a-run | rooms.gdb with a monster's drop left in a room that is released | H7d | 1 |
| 70 | 845 | H5. The grid marks of a re-created monster | The call path, read in the pinned image: a room whose driver flag bit 0 … | – | c | the driver's bit-0 test read with a second tool | S7f | 1 |
| 71 | 875 | I. The wanderer tick | I1. RoomWandererTick(game, room): for the first draw, the roll's draw and its ≥ 3 return, | `fn:sub_0054F060_RoomWandererTick@0x0054F060` | a-run | as row 4 | H7d | 1 |
| 72 | 877 | I. The wanderer tick | if room.seed.low & ≠ 0: return ; ; the mask's width | run:2026-10-17-lifecycle | c-emu | as row 3 | S7e | 1 |
| 73 | 878 | I. The wanderer tick | if room[+] ≠ 0 or Levels[level].MonWndr = 0: return ; | `0x0054F096` | c-emu | `RoomWandererTick` emulated with `+0x78` and `MonWndr` as inputs, the spawn as a boundary | S7e | 1 |
| 74 | 882 | I. The wanderer tick | if region[+] ≥ 3: return ; | `0x0054F041` | c-emu | as row 73: region `+0x2C4` at 2 and 3 | S7e | 1 |
| 75 | 900 | I. The wanderer tick | That one pass does not separate the rest: the mask's width (its low word had … | – | c-emu | as row 3 | S7e | 1 |
| 76 | 906 | I. The wanderer tick | Because of +, wanderers can appear only in active rooms that no client is near: … | – | c-emu | as row 73 | S7e | 1 |
| 77 | 915 | J. The preset path and the preset list | The release moves the path into the monster record | `0x00542098` | c | writer/reader pair at 0x00542098 and the restore's write back | S7f | 1 |
| 78 | 918 | J. The preset path and the preset list | A re-activated room never re-dispatches its preset list: RoomPresetUnits runs only while flags bit 0 … | – | a-logs | rooms.gdb logs (run:2026-10-17-lifecycle, -h7a-lifecycle): `RoomPresetUnits` only at a room's first activation | S7d | 1 |

**Totals by class:** a-logs 19, a-run 10, b 7, c 25, c-emu 11, d-2c 1, d-none 5 (sum 78).
