# Plan 0066 inventory: sim/frame

- **Spec:** [sim/frame](../../specs/sim/frame.md), read at `main` `b5999f5e`.
- **Front matter `I`:** 127; the *Count* column sums to 127.
- Classes, batches and conventions as in [the inventory README](README.md#conventions).

| # | Line | Section | Claim (excerpt) | Anchor | Class | Route or reason | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | 37 | Entry points | Each pass of the client's main frame in game … | `fn:sub_0044EFA0_ClientMainFrame@0x0044EFA0` | ? | ? | ? | 1 |
| 2 | 38 | Entry points | Before any frame of that pass | `fn:sub_0052CFE0_SrvDrainMessages@0x0052CFE0` | ? | ? | ? | 1 |
| 3 | 39 | Entry points | One interval has passed | `fn:sub_0052FC20_ServerGamesFrame@0x0052FC20` | ? | ? | ? | 1 |
| 4 | 40 | Entry points | Per live game, per frame | `fn:sub_0052D870_GameTick@0x0052D870` | ? | ? | ? | 1 |
| 5 | 41 | Entry points | Pass 4 of the tick — its code's map (§ D) | `fn:sub_005414D0_GameRunUnitEvents@0x005414D0` | ? | ? | ? | 1 |
| 6 | 45 | Entry points | reaches, so in this build every frame is run by ServerGamesFrame. | `fn:sub_005645E0_GameTickAlt@0x005645E0` | ? | ? | ? | 1 |
| 7 | 56 | Tables |  | `fn:sub_0052D870_GameTick@0x0052D870` | ? | ? | ? | 1 |
| 8 | 80 | Constants | frames per second — 25 in the image; the setter SetServerFps has no … | `data:g_ServerFps@0x00731014` | ? | ? | ? | 1 |
| 9 | 81 | Constants | frame interval — 1000 ÷ 25 = 40 ms, computed by a … | `0x006CAF10` | ? | ? | ? | 1 |
| 10 | 82 | Constants | game slots — 1 024 dwords | `data:g_GameSlots@0x00882D38` | ? | ? | ? | 1 |
| 11 | 86 | Constants | unit type → list — the five lists' use code's map | run:2026-10-30-frame-emu-2 | ? | ? | ? | 1 |
| 12 | 87 | Constants | record block — 600 records of bytes, bytes in all | `fn:sub_00540BB0_EventBlockNew@0x00540BB0` | ? | ? | ? | 1 |
| 13 | 93 | Constants | empty game close — 300 000 ms, or 1500 < frame < 7500 | `0x0052FD90` | ? | ? | ? | 1 |
| 14 | 94 | Constants | player kind 11 — first at placement + 250, then every 30 frames | `0x00534B1D` | ? | ? | ? | 1 |
| 15 | 95 | Constants | chat record life — 8·n + 125 frames, n ≤ 254 characters | `fn:sub_00661110_ChatRecordNew@0x00661110` | ? | ? | ? | 1 |
| 16 | 104 | A. The host loop and the frame clock | A1. HostLoopPass: | `0x0044F136` | ? | ? | ? | 1 |
| 17 | 111 | A. The host loop and the frame clock | A2. ServerGamesFrame(cap: u32) → u32: | `0x0052FC38` | ? | ? | ? | 1 |
| 18 | 126 | A. The host loop and the frame clock | Every caller passes cap = 1, so one call runs at most one frame per … | – | ? | ? | ? | 1 |
| 19 | 129 | A. The host loop and the frame clock | The flush returns at once when both arguments are 0 and under 40 ms (GetTickCount) … | – | ? | ? | ? | 1 |
| 20 | 134 | A. The host loop and the frame clock | The lag scale Game+ always stores (g_ServerLagFixed holds 1 and nothing writes it), and its … | – | ? | ? | ? | 1 |
| 21 | 148 | B. GameTick | B1. GameTick(game): | `0x0052D87B` | ? | ? | ? | 1 |
| 22 | 165 | B. GameTick | … reads the stamp N after tick N's passes is at rank 21 of stamp N. | – | ? | ? | ? | 1 |
| 23 | 169 | B. GameTick | The seven calls from 1 to 16 have no branch between them. | `fn:sub_0052D870_GameTick@0x0052D870` | ? | ? | ? | 1 |
| 24 | 170 | B. GameTick | The debug switch's one identified writer has no reference of any kind, so the switch … | – | ? | ? | ? | 1 |
| 25 | 189 | C. The message drain | C1. SrvDrainMessages: | `0x0052CFFF` | ? | ? | ? | 1 |
| 26 | 194 | C. The message drain | C2. SrvProcessClientMessage(m): | `0x0053F3D0` | ? | ? | ? | 1 |
| 27 | 202 | C. The message drain | Each queue is FIFO: the pop takes the head under the context's lock and returns … | – | ? | ? | ? | 1 |
| 28 | 206 | C. The message drain | Messages are applied between frames, never inside GameTick. SrvPacketDispatch has one call site, in | – | ? | ? | ? | 1 |
| 29 | 211 | C. The message drain | The packets of all clients and all games share queue 1, so their order is … | – | ? | ? | ? | 1 |
| 30 | 226 | D. The unit events: the control, the pass, the runners | Created zeroed with its first block at game create, freed with every block at game … | – | ? | ? | ? | 1 |
| 31 | 238 | D. The unit events: the control, the pass, the runners | D1. GameRunUnitEvents(game): | `0x005414EC` | ? | ? | ? | 1 |
| 32 | 266 | D. The unit events: the control, the pass, the runners | A walk reads its list's head when it starts (each head is loaded right before … | `0x005414EE` | ? | ? | ? | 1 |
| 33 | 281 | D. The unit events: the control, the pass, the runners | Ranks 5, 6 and 10 to 13 hold no event in any counted window, so … | – | ? | ? | ? | 1 |
| 34 | 290 | D. The unit events: the control, the pass, the runners | For a reimplementer: a unit's events in one frame run in the order (its type's … | – | ? | ? | ? | 1 |
| 35 | 294 | D. The unit events: the control, the pass, the runners | The frame counter holds for 2 147 483 647 frames (994.2 days at 25 per … | – | ? | ? | ? | 1 |
| 36 | 321 | E. The queue | UninterruptibleEnd(unit, 0) ; | `0x00541701` | ? | ? | ? | 1 |
| 37 | 350 | E. The queue | A frame-−1 request through UnitQueueEventCb would lose its callback; its one caller (UnitTeleport, | – | ? | ? | ? | 1 |
| 38 | 354 | E. The queue | Who queues every frame: UnitQueueEveryFrame has 3 sites, SUNIT_ModeEveryFrame (kind 0), MissileUnitInit | – | ? | ? | ? | 1 |
| 39 | 360 | E. The queue | Allocation. EventRecordTake walks the blocks from + to the first with a free record, pops … | – | ? | ? | ? | 1 |
| 40 | 371 | E. The queue | The state-54 branch: UninterruptibleEnd(unit, 0) clears state 54 and, if the unit has a game, … | – | ? | ? | ? | 1 |
| 41 | 376 | E. The queue | Queued during a pass. A timed record never runs in the frame it is queued … | – | ? | ? | ? | 1 |
| 42 | 381 | E. The queue | : that log has no start of theirs, and the windows' QF lines for missiles … | – | ? | ? | ? | 1 |
| 43 | 387 | E. The queue | Freed during a walk. A record freed is never run after it: the free moves … | – | ? | ? | ? | 1 |
| 44 | 419 | F. Dispatch: the event tables, the freeze drop, kinds 6 and  | The dispatches. Players and monsters test kind < 15 unsigned, so a negative kind that … | – | ? | ? | ? | 1 |
| 45 | 427 | F. Dispatch: the event tables, the freeze drop, kinds 6 and  | The queue sites by kind: all 269 push a constant kind: 265 UnitQueueEvent sites (kind … | – | ? | ? | ? | 1 |
| 46 | 433 | F. Dispatch: the event tables, the freeze drop, kinds 6 and  | F3. MonEventDispatch(game, unit, kind, a, b): | `fn:sub_005A7F80_MonEventDispatch@0x005A7F80` | ? | ? | ? | 1 |
| 47 | 439 | F. Dispatch: the event tables, the freeze drop, kinds 6 and  | The drop is in the dispatch, after the runner set the running flag, so a … | – | ? | ? | ? | 1 |
| 48 | 444 | F. Dispatch: the event tables, the freeze drop, kinds 6 and  | F4. PlrEvent11Every30(game, player): | `fn:sub_00580BE0_PlrEvent11Every30@0x00580BE0` | ? | ? | ? | 1 |
| 49 | 452 | F. Dispatch: the event tables, the freeze drop, kinds 6 and  | ChatRecordFree(pool, record) ; the boundary; the writes below are | `0x00580B70` | ? | ? | ? | 1 |
| 50 | 460 | F. Dispatch: the event tables, the freeze drop, kinds 6 and  | By its graph kind 11 reaches no RNG function (601 functions) with PetUnitRelease and UninterruptibleEnd … | – | ? | ? | ? | 1 |
| 51 | 464 | F. Dispatch: the event tables, the freeze drop, kinds 6 and  | Kind 6 is untested in the game: 0 events in every window. Its draw-free reading … | – | ? | ? | ? | 1 |
| 52 | 473 | G. The other per-frame passes | G1. ActsClockPass(game): | `0x0052D7C6` | ? | ? | ? | 1 |
| 53 | 502 | G. The other per-frame passes | T0, T1, T2 are six rows of three dwords (start, type, a colour word), read … | – | ? | ? | ? | 1 |
| 54 | 507 | G. The other per-frame passes | GameFpsStats: on 1 000 ms or more since Game+, it stores frames × 1000 ÷ … | – | ? | ? | ? | 1 |
| 55 | 516 | G. The other per-frame passes | ActUnitsFrameReset(game): | `0x0053B02C` | ? | ? | ? | 1 |
| 56 | 525 | G. The other per-frame passes | Within a room the reset visits units in the reverse of the order they were … | – | ? | ? | ? | 1 |
| 57 | 530 | G. The other per-frame passes | UnitFrameReset is the per-frame flag clear: bits of + and + for every unit | `0x0055325A` | ? | ? | ? | 1 |
| 58 | 533 | G. The other per-frame passes | Removal notes. RoomUnitOp pushes a 12-byte note {type, guid, next} on room+ and sets the … | – | ? | ? | ? | 1 |
| 59 | 558 | H. Rooms: list order, the new-room walk, the room sync, the  | An act's room list is newest first. DUNGEON_RoomCreate, called only by DRLG_RoomActivate | `0x00642369` | ? | ? | ? | 1 |
| 60 | 564 | H. Rooms: list order, the new-room walk, the room sync, the  | H2. NewRoomsUpdate(game): | `0x0052D1A9` | ? | ? | ? | 1 |
| 61 | 579 | H. Rooms: list order, the new-room walk, the room sync, the  | So in one frame's walk, an act's rooms created since its last walk come first, … | – | ? | ? | ? | 1 |
| 62 | 583 | H. Rooms: list order, the new-room walk, the room sync, the  | A room created during the walk (NearWarpTest's level-point lookup can activate one) is linked before … | – | ? | ? | ? | 1 |
| 63 | 590 | H. Rooms: list order, the new-room walk, the room sync, the  | DUNGEON_RoomCreate calls the act's + with the new room when it is non-zero, before its … | – | ? | ? | ? | 1 |
| 64 | 594 | H. Rooms: list order, the new-room walk, the room sync, the  | H3. ClientsRoomSync(game): | `0x0052D453` | ? | ? | ? | 1 |
| 65 | 604 | H. Rooms: list order, the new-room walk, the room sync, the  | ClientRoomSync(game, client), with a player: | `fn:sub_005380D0_ClientRoomSync@0x005380D0` | ? | ? | ? | 1 |
| 66 | 618 | H. Rooms: list order, the new-room walk, the room sync, the  | The client order is ClientCreate's front push; one client in single player. AutosaveTick does not … | – | ? | ? | ? | 1 |
| 67 | 625 | H. Rooms: list order, the new-room walk, the room sync, the  | Within one room change rooms are created in the reference walk's order: DrlgRefAdd(new, 0) walks … | – | ? | ? | ? | 1 |
| 68 | 631 | H. Rooms: list order, the new-room walk, the room sync, the  | What a log-free build takes as input, per frame: (a) for each client whose player's … | – | ? | ? | ? | 1 |
| 69 | 636 | H. Rooms: list order, the new-room walk, the room sync, the  | The limit. The record is not derivable from client messages alone: the room a player … | – | ? | ? | ? | 1 |
| 70 | 646 | I. The periodic calls | if game+ = 0: return ; | `0x00543E17` | ? | ? | ? | 1 |
| 71 | 654 | I. The periodic calls | if IsBadCodePtr(t.fn): fatal ; | `0x00543E79` | ? | ? | ? | 1 |
| 72 | 657 | I. The periodic calls | t ← next; continue ; | `0x00543E10` | ? | ? | ? | 1 |
| 73 | 665 | I. The periodic calls | the non-zero branch is a fatal line. | `0x00543E73` | ? | ? | ? | 1 |
| 74 | 666 | I. The periodic calls | QUESTS_TimerAdd pushes on the front, so within a pass timers run newest registered first (read, … | – | ? | ? | ? | 1 |
| 75 | 676 | I. The periodic calls | Level-unload tick. Each level of the act's list with no reference and built rooms counts … | – | ? | ? | ? | 1 |
| 76 | 687 | I. The periodic calls | Beyond its position, that the sweep unlinks, sends and frees in a game is a … | – | ? | ? | ? | 1 |
| 77 | 694 | I. The periodic calls | Within a frame the four calls run in the order of B1, read from the … | `0x0052D912` | ? | ? | ? | 1 |
| 78 | 700 | J. Draws per pass and the shared seeds | 21, before the tick — as each spec names | `data:g_SrvPacketTable@0x006E0D18` | ? | ? | ? | 1 |
| 79 | 701 | J. Draws per pass and the shared seeds | 1 — EquipReqRefresh per client's player on a clock change, through … | `0x0055FDE8` | ? | ? | ? | 1 |
| 80 | 702 | J. Draws per pass and the shared seeds | 2 — none (5 functions) | `fn:sub_0052D720_GameFpsStats@0x0052D720` | ? | ? | ? | 1 |
| 81 | 703 | J. Draws per pass and the shared seeds | 3 — room's own; a neighbour's room seed; game; level; object … | `fn:sub_0052D160_NewRoomsUpdate@0x0052D160` | ? | ? | ? | 1 |
| 82 | 704 | J. Draws per pass and the shared seeds | 4 to 13 — the unit's; another unit's (J2 kind 5); game; local | `fn:sub_005414D0_GameRunUnitEvents@0x005414D0` | ? | ? | ? | 1 |
| 83 | 705 | J. Draws per pass and the shared seeds | any — the kill's or hit's | `0x00541701` | ? | ? | ? | 1 |
| 84 | 706 | J. Draws per pass and the shared seeds | 14 — room's own, level's; never the game seed by direct … | `data:g_DrlgRefEnterFns@0x00744384` | ? | ? | ? | 1 |
| 85 | 707 | J. Draws per pass and the shared seeds | 15 — UnitFree for an inventory item with item flag 1 | `0x00557FE7` | ? | ? | ? | 1 |
| 86 | 708 | J. Draws per pass and the shared seeds | 16 — none (549 functions) | `fn:sub_0053A820_ActsRoomRemovalsClear@0x0053A820` | ? | ? | ? | 1 |
| 87 | 709 | J. Draws per pass and the shared seeds | 17 — game, quest, level | `fn:QUESTS_TimersRun@0x00543E10` | ? | ? | ? | 1 |
| 88 | 710 | J. Draws per pass and the shared seeds | 18 — lifecycle § F | `fn:sub_0052D240_RoomsDeactivate@0x0052D240` | ? | ? | ? | 1 |
| 89 | 711 | J. Draws per pass and the shared seeds | 19 — none (572 functions) | `0x006430E9` | ? | ? | ? | 1 |
| 90 | 712 | J. Draws per pass and the shared seeds | 20 — UnitFree of an expired item | `fn:sub_0052D310_ExpirySweepTick@0x0052D310` | ? | ? | ? | 1 |
| 91 | 714 | J. Draws per pass and the shared seeds | Function counts are RNG call graphs with the later passes and specified entries as stops; … | – | ? | ? | ? | 1 |
| 92 | 721 | J. Draws per pass and the shared seeds | Five kinds. (1) The game seed: every unit creation (SUnitCreate), in population and the inactive … | – | ? | ? | ? | 1 |
| 93 | 730 | J. Draws per pass and the shared seeds | g_HitClassCounter is process state. It is a byte, 0 at load, whose one store is … | – | ? | ? | ? | 1 |
| 94 | 780 | K2. What the reader asserts | K2. For each window, reader rev 2 (tools/frame_xs.py) keeps each chained seed's value: | run:2026-11-04-frame2 | ? | ? | ? | 1 |
| 95 | 803 | K3. A large zero can test little | Most events move nothing. Of the 37 977 UE0, 37 489 (98.7%) moved neither the … | – | ? | ? | ? | 1 |
| 96 | 807 | K3. A large zero can test little | A step on no chained seed is not tested at all: 157 769 of the … | – | ? | ? | ? | 1 |
| 97 | 810 | K3. A large zero can test little | 225 readings accepted any of several values. While a fresh seed shares a low word … | – | ? | ? | ? | 1 |
| 98 | 815 | K3. A large zero can test little | Oracles, not predictions: a unit's own draws (AI, skill do, missile own), the number of … | – | ? | ? | ? | 1 |
| 99 | 819 | K3. A large zero can test little | The per-KD rule tests almost nothing. Over 54 KD events the item constructor's steps and … | – | ? | ? | ? | 1 |
| 100 | 824 | K3. A large zero can test little | What the controls separate. The reader has 26 window-selftest controls, and reversing each of its … | – | ? | ? | ? | 1 |
| 101 | 832 | K4. Touches: another unit's event or a room's walk drawing o | kill — items/tc § D, items/quality | `fn:TC_ResolveDrops@0x0055A6D0` | ? | ? | ? | 1 |
| 102 | 833 | K4. Touches: another unit's event or a room's walk drawing o | room — lifecycle § I, monsters/spawn § H, objects § E, … | `fn:sub_0054F060_RoomWandererTick@0x0054F060` | ? | ? | ? | 1 |
| 103 | 834 | K4. Touches: another unit's event or a room's walk drawing o | owner — sub_005A5560_MonCritDouble at with a missile event open, 4 hits, … | `fn:COMBAT_ToHitRoll@0x0057D9B0` | ? | ? | ? | 1 |
| 104 | 835 | K4. Touches: another unit's event or a room's walk drawing o | defender — combat/to-hit § C, items/economy § H | `fn:COMBAT_DefenceRoll@0x0057DFB0` | ? | ? | ? | 1 |
| 105 | 836 | K4. Touches: another unit's event or a room's walk drawing o | killev — UModPartyDeadDeath sites: none hit | `fn:sub_005A2D10_UModPartyDeadDeath@0x005A2D10` | ? | ? | ? | 1 |
| 106 | 838 | K4. Touches: another unit's event or a room's walk drawing o | A trigger matches event type and site, not the target, for owner and defender: the … | – | ? | ? | ? | 1 |
| 107 | 840 | K4. Touches: another unit's event or a room's walk drawing o | … an open RU0, not the neighbour relation, which the specs state for MonSpawnTry and at | – | ? | ? | ? | 1 |
| 108 | 843 | K4. Touches: another unit's event or a room's walk drawing o | Two hits on one unit is the whole of that. That the seed is the … | run:2026-11-04-frame3 | ? | ? | ? | 1 |
| 109 | 846 | K4. Touches: another unit's event or a room's walk drawing o | Step classes in the counted windows: own 1 808, game 8 768, pass 27, touch … | – | ? | ? | ? | 1 |
| 110 | 852 | K5. Shared-seed pairs | 2 pairs in the counted windows, both handed and in pass order, 0 reversed: frame … | – | ? | ? | ? | 1 |
| 111 | 861 | K6. The hooks: where a function ran | Placements say where a hook ran, not where it can. Of the 65 functions the … | – | ? | ? | ? | 1 |
| 112 | 867 | K6. The hooks: where a function ran | ), UNIT_AnimAdvance 568, RunStaminaDrain 90. (, | run:2026-11-03-frame-order-2 | ? | ? | ? | 1 |
| 113 | 872 | K7. Client steps are not evidence | Between the ticks the main loop runs client code on client copies of the seeds, … | – | ? | ? | ? | 1 |
| 114 | 881 | L. Inactive units and the room unlink | A unit made inactive (released room, InactiveUnitSaveTest → UnitFree) loses its records with the unit. … | – | ? | ? | ? | 1 |
| 115 | 887 | L. Inactive units and the room unlink | UnitRoomUnlink takes a unit out of its room's unit list, lowers the room's player count … | – | ? | ? | ? | 1 |
| 116 | 895 | Outputs | … of a game's frame: the rank of each event and the order inside each list. | `fn:sub_0052D870_GameTick@0x0052D870` | ? | ? | ? | 1 |
| 117 | 896 | Outputs | … state after the frame; nothing else leaves the frame but queued packets, flushed after it. | `fn:sub_0052FD90_ServerGamesFlush@0x0052FD90` | ? | ? | ? | 1 |
| 118 | 897 | Outputs | For the chain: the activation-order record, § H5, as an input. | `fn:sub_0061B730_RoomActivateB@0x0061B730` | ? | ? | ? | 1 |
| 119 | 928 | Worked example | The pair is one instance of the rules of § E7 and § K2a, named … | run:2026-11-04-frame2 | ? | ? | ? | 1 |
| 120 | 932 | Reimplementation notes | The stamp a packet reads is the frame before the one it acts in. Handlers … | `0x0052D87B` | ? | ? | ? | 1 |
| 121 | 936 | Reimplementation notes | So a record due at F, queued in frame q, is passed over (F − … | `fn:sub_005416B0_EventQueueAt@0x005416B0` | ? | ? | ? | 1 |
| 122 | 937 | Reimplementation notes | The new-rooms flag is cleared after the walk, so a room created during its own … | `0x0052D21D` | ? | ? | ? | 1 |
| 123 | 938 | Reimplementation notes | The wanderer tick runs on every room of a walked act, not only on new … | `0x0052D1C4` | ? | ? | ? | 1 |
| 124 | 939 | Reimplementation notes | The AI has two entries: at a mode end it runs inside that mode-end event, … | `fn:sub_005B1740_MonAiEvent@0x005B1740` | ? | ? | ? | 1 |
| 125 | 940 | Reimplementation notes | Do not reset g_HitClassCounter per game. | `0x0057CE4F` | ? | ? | ? | 1 |
| 126 | 941 | Reimplementation notes | ActsClockPass refreshes every client's player on any act's clock change, not only that act's clients; … | `0x0052D7C6` | ? | ? | ? | 1 |
| 127 | 952 | Open questions | The 20-pair floor is decided, and no longer open. The owner ruled on 2026-11-04, option … | run:2026-11-04-frame2 | ? | ? | ? | 1 |
