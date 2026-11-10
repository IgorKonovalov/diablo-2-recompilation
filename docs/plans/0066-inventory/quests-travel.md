# Plan 0066 inventory: quests/travel

- **Spec:** [quests/travel](../../specs/quests/travel.md), read at `main` `b5999f5e`.
- **Front matter `I`:** 86; the *Count* column sums to 86.
- Classes, batches and conventions as in [the inventory README](README.md#conventions).

| # | Line | Section | Claim (excerpt) | Anchor | Class | Route or reason | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | 28 | Entry points | click on a waypoint, a portal or another object … — sub_00548B00_UnitInteract case 2 → OBJ_OperateDispatch → g_ObjOperateFns[OperateFn] | `fn:sub_00548B00_UnitInteract@0x00548B00` | ? | ? | ? | 1 |
| 2 | 29 | Entry points | the client picks a waypoint row (packet , {u32 … — sub_0054C5D0_Pkt49WaypointTravel → sub_00584F60_WaypointTravel | `fn:sub_0054C5D0_Pkt49WaypointTravel@0x0054C5D0` | ? | ? | ? | 1 |
| 3 | 30 | Entry points | an NPC menu action other than 1–3 (13-byte packet) — NPC_MenuAction → sub_0054B830_NpcTravelMove | `fn:NPC_MenuAction@0x00579D60` | ? | ? | ? | 1 |
| 4 | 31 | Entry points | the player uses an item whose Misc.pSpell is 2 … — g_ItemUseFns[2].use = ITEMUSE_TownPortal, by the dispatch of items/use § … | `fn:ITEMUSE_TownPortal@0x005BE290` | ? | ? | ? | 1 |
| 5 | 32 | Entry points | click on a warp tile (unit type 5, distance … — sub_00548B00_UnitInteract case 5 → sub_005550B0_WarpExitPos | `fn:sub_00548B00_UnitInteract@0x00548B00` | ? | ? | ? | 1 |
| 6 | 33 | Entry points | the dead player presses "resurrect" (packet , mode 17 … — sub_0054C0E0_Pkt41Resurrect | `fn:sub_0054C0E0_Pkt41Resurrect@0x0054C0E0` | ? | ? | ? | 1 |
| 7 | 34 | Entry points | a player joins the game — sub_005394A0_PlayerPlaceInAct (callers , , ) | `fn:sub_005394A0_PlayerPlaceInAct@0x005394A0` | ? | ? | ? | 1 |
| 8 | 35 | Entry points | the client reports its act loaded (packet ) — sub_0054C590_Pkt48ActChangeClear | `fn:sub_0054C590_Pkt48ActChangeClear@0x0054C590` | ? | ? | ? | 1 |
| 9 | 73 | Constants | placement mask, radius, step — 50, 1 | `fn:sub_0061B060_ActLevelSpot@0x0061B060` | ? | ? | ? | 1 |
| 10 | 74 | Constants | act-change second search — mask , radius 50, step 5 | `fn:sub_0053ACC0_PlayerChangeAct@0x0053ACC0` | ? | ? | ? | 1 |
| 11 | 75 | Constants | portal field end search — size 3, masks /, no fallback | `fn:sub_0056D130_PortalObjectCreate@0x0056D130` | ? | ? | ? | 1 |
| 12 | 76 | Constants | portal town end search — mask , radius 50, step 5 | `fn:sub_0056CF40_PortalPartnerCreate@0x0056CF40` | ? | ? | ? | 1 |
| 13 | 77 | Constants | portal-use state — state 102 for 75 frames | `fn:OBJOP_Portal@0x00584870` | ? | ? | ? | 1 |
| 14 | 84 | Inputs and oracles | the click, the packet, the NPC menu action — which travel the player asked for | `fn:sub_00548B00_UnitInteract@0x00548B00` | ? | ? | ? | 1 |
| 15 | 87 | Inputs and oracles | a level or act built on first arrival, a … — its draws are drlg's and drlg/collision § I's | `fn:sub_0053AC70_ActCreate@0x0053AC70` | ? | ? | ? | 1 |
| 16 | 89 | Inputs and oracles | party membership, hostility, a second player's portal — for hostility and for the no-party refusal ; for … | `fn:OBJOP_Portal@0x00584870` | ? | ? | ? | 1 |
| 17 | 135 | A. Placement | A2. LevelPointFind(act, level, type) → (room, tx, ty): | `fn:sub_0066B2B0_LevelPointFind@0x0066B2B0` | ? | ? | ? | 1 |
| 18 | 177 | A. Placement | The last fallback, RangeB(level seed, level+), never ran in either run. | `0x0066AE70` | ? | ? | ? | 1 |
| 19 | 191 | A. Placement | The act-change search uses step 5, so the player can land up to several cells … | – | ? | ? | ? | 1 |
| 20 | 197 | B. The free-cell search | B1. COLL_FindFreeNear(room, pos, other, size, maskA, maskB, fallback, radius: i32, step: i32) → room: | `fn:COLL_FindFreeNear@0x0064DEA0` | ? | ? | ? | 1 |
| 21 | 264 | B. The free-cell search | The centre's row and column 128 are declared to that run; by the reading the … | – | ? | ? | ? | 1 |
| 22 | 266 | B. The free-cell search | Sizes other than 1 and steps other than 1 are the reading: neither end of … | – | ? | ? | ? | 1 |
| 23 | 287 | C. Waypoint activation | C1. WaypointOperate(game, object, player) (OperateFn 23): for modes 1 and 2 ; | `fn:sub_00584E30_WaypointOperate@0x00584E30` | ? | ? | ? | 1 |
| 24 | 296 | C. Waypoint activation | C2. OBJINIT_Waypoint (InitFn 17): | `fn:OBJINIT_Waypoint@0x00547210` | ? | ? | ? | 1 |
| 25 | 309 | C. Waypoint activation | For a waypoint in mode 0 the first operate both sets the bit and starts … | – | ? | ? | ? | 1 |
| 26 | 312 | C. Waypoint activation | … attempts, from the Rogue Encampment and the Kurast Docks, reached no mode-0 waypoint). This stays | – | ? | ? | ? | 1 |
| 27 | 315 | C. Waypoint activation | Plan 0047's runs operated seven waypoints from mode 0 on the Act V routes from … | – | ? | ? | ? | 1 |
| 28 | 320 | C. Waypoint activation |  | `fn:sub_00584E30_WaypointOperate@0x00584E30` | ? | ? | ? | 1 |
| 29 | 323 | C. Waypoint activation | Over the 45 logs of the three runs, a field waypoint first seen after a … | – | ? | ? | ? | 1 |
| 30 | 327 | C. Waypoint activation | There is no proximity or touch test of the waypoint's own: activation is the operate, … | – | ? | ? | ? | 1 |
| 31 | 330 | C. Waypoint activation | The arrival list is pushed only by WaypointTravel (§ D) and emptied by the first … | – | ? | ? | ? | 1 |
| 32 | 332 | C. Waypoint activation | The draw. SetMode → UNIT_AnimInit draws RangeB(object seed, FrameDelta[mode] >> 3) when the row's | – | ? | ? | ? | 1 |
| 33 | 337 | C. Waypoint activation | Other writers of the waypoint record: NPC_MenuAction after an NPC act change (levels 40, 75, … | – | ? | ? | ? | 1 |
| 34 | 350 | D. Waypoint travel | D2. WaypointTravelCheck(objectId, level) → code: | `fn:sub_00549570_WaypointTravelCheck@0x00549570` | ? | ? | ? | 1 |
| 35 | 373 | D. Waypoint travel | … 13, with no draw, for the towns and levels 46 and 74 the runs reached; | – | ? | ? | ? | 1 |
| 36 | 375 | D. Waypoint travel | The act tabs of the waypoint menu are a client gate: the server tests only … | – | ? | ? | ? | 1 |
| 37 | 397 | E. Act change through an NPC | E1. NPC_MenuAction(action, npc, arg), action ∉ {1, 2, 3}, by NPC class: | `fn:NPC_MenuAction@0x00579D60` | ? | ? | ? | 1 |
| 38 | 406 | E. Act change through an NPC | E2. NpcTravelMove(level, type): | `fn:sub_0054B830_NpcTravelMove@0x0054B830` | ? | ? | ? | 1 |
| 39 | 411 | E. Act change through an NPC | E3. NpcActTravel(npc): for word 7's branch ; | `fn:sub_005467E0_NpcActTravel@0x005467E0` | ? | ? | ? | 1 |
| 40 | 418 | E. Act change through an NPC | for returns 3 and 2 | `fn:sub_0054C590_Pkt48ActChangeClear@0x0054C590` | ? | ? | ? | 1 |
| 41 | 433 | E. Act change through an NPC | The client's menus, as screenshotted in the run's development logs, explain it: NPC 367's has … | – | ? | ? | ? | 1 |
| 42 | 436 | E. Act change through an NPC | travel line and that the 367 branch is unreachable by stock play are | `fn:NPC_MenuAction@0x00579D60` | ? | ? | ? | 1 |
| 43 | 438 | E. Act change through an NPC | The quest-word tests of NPCs 155, 210 and 367 were not run on their refusing … | – | ? | ? | ? | 1 |
| 44 | 445 | E. Act change through an NPC | Word 28's branch (, reached only through NPC 367's menu branch) and E1's word 26 … | `0x0054684A` | ? | ? | ? | 1 |
| 45 | 447 | E. Act change through an NPC | While + = 1, OBJ_OperateDispatch and PlayerIsBusy refuse, so the player can operate nothing and … | – | ? | ? | ? | 1 |
| 46 | 454 | E. Act change through an NPC | The returns 3 (a2 ≠ 1) and 2 (+ already 0) were not reached. What … | – | ? | ? | ? | 1 |
| 47 | 459 | E. Act change through an NPC | NPC 520's return uses type 5 too, with A3's draw rule (a draw only when … | – | ? | ? | ? | 1 |
| 48 | 461 | E. Act change through an NPC | TownLevelLeave(old, new) marks the old town's store stale (items/vendors) and, on | – | ? | ? | ? | 1 |
| 49 | 470 | F. The Durance portal and the other travel objects | F1. DurancePortalOperate (OperateFn 46): | `fn:sub_00584750_DurancePortalOperate@0x00584750` | ? | ? | ? | 1 |
| 50 | 473 | F. The Durance portal and the other travel objects | F2. DuranceActTravel(level): | `fn:sub_00546AC0_DuranceActTravel@0x00546AC0` | ? | ? | ? | 1 |
| 51 | 481 | F. The Durance portal and the other travel objects | Duriel's lair portal 100 (43) — class 100 → level 73; class 377 → its … | `fn:OBJOP_LevelPortal@0x00584D00` | ? | ? | ? | 1 |
| 52 | 482 | F. The Durance portal and the other travel objects | Arcane portal 298 (34) — 74 → 54 at type 0; 54 → 74 … | `fn:OBJOP_ArcanePortal@0x005846B0` | ? | ? | ? | 1 |
| 53 | 483 | F. The Durance portal and the other travel objects | Durance portal 342 (46) — word 22 bit 13 or 0 | `fn:sub_00584750_DurancePortalOperate@0x00584750` | ? | ? | ? | 1 |
| 54 | 485 | F. The Durance portal and the other travel objects | Baal's portals 563/569 (70) — quest 36's private flag | `fn:sub_0058E6A0_A5Q6_BaalPortalOperate@0x0058E6A0` | ? | ? | ? | 1 |
| 55 | 486 | F. The Durance portal and the other travel objects | the last portal 565 (72) — word 40 bit 13 | `fn:sub_0058E740_A5Q6_LastPortalOperate@0x0058E740` | ? | ? | ? | 1 |
| 56 | 488 | F. The Durance portal and the other travel objects | Object 410 Siege Control shares OperateFn 46, but no DS1 id, objgroup cell or creation … | – | ? | ? | ? | 1 |
| 57 | 490 | F. The Durance portal and the other travel objects | Each of these objects in mode 0 goes to mode 1 and queues object event … | – | ? | ? | ? | 1 |
| 58 | 516 | Opening | G1. ITEMUSE_TownPortal(player, item): | `fn:ITEMUSE_TownPortal@0x005BE290` | ? | ? | ? | 1 |
| 59 | 533 | Opening | G2a. PortalPartnerCreate(field, dest, src): for the draws and their order ; | `fn:sub_0056CF40_PortalPartnerCreate@0x0056CF40` | ? | ? | ? | 1 |
| 60 | 557 | Opening | The field end's search tests a walk back to the point (x, y) with mask … | – | ? | ? | ? | 1 |
| 61 | 563 | Opening | The refusal on level 136 was not reached. | `fn:ITEMUSE_TownPortal@0x005BE290` | ? | ? | ? | 1 |
| 62 | 564 | Opening | A portal from Duriel's lair (73) puts its town end at level 40's point type … | – | ? | ? | ? | 1 |
| 63 | 571 | Using a portal | G3. OBJOP_Portal(game, object, operator) (OperateFn 15): | `fn:OBJOP_Portal@0x00584870` | ? | ? | ? | 1 |
| 64 | 619 | Using a portal | The compare of two different party ids needs a third player, since two players hold … | – | ? | ? | ? | 1 |
| 65 | 623 | Using a portal | When the free-spot search at the destination finds no room, the use returns 0 with … | – | ? | ? | ? | 1 |
| 66 | 625 | Using a portal | The quest-word test needs a second player (plan 0044, MP27). | – | ? | ? | ? | 1 |
| 67 | 632 | Closing and permanent portals | A player's class-59 pair is freed when (a) the owner goes through the town end; … | – | ? | ? | ? | 1 |
| 68 | 640 | Closing and permanent portals | Permanent portals (class 60). OBJINIT_Portal (InitFn 12) sets the destination from the level the | – | ? | ? | ? | 1 |
| 69 | 649 | H. Warps | H1. UnitInteract case 5: a warp unit within distance 5 → WarpExitPos(player, warp) | `fn:sub_00548B00_UnitInteract@0x00548B00` | ? | ? | ? | 1 |
| 70 | 650 | H. Warps | H2. WarpExitPos(player, warp): for the placement with no draw ; | `fn:sub_005550B0_WarpExitPos@0x005550B0` | ? | ? | ? | 1 |
| 71 | 656 | H. Warps | H3. QUESTS_WarpGate(src, dest) → refuse: | `fn:QUESTS_WarpGate@0x00545B80` | ? | ? | ? | 1 |
| 72 | 662 | H. Warps | H4. The walk command PlayerModeCmd(0, 2, x, y, 0) first calls PlayerModeAllowed: | `fn:sub_005809D0_PlayerModeCmd@0x005809D0` | ? | ? | ? | 1 |
| 73 | 673 | H. Warps | The gates are quest code (quests/progression § Warp and portal gates). | – | ? | ? | ? | 1 |
| 74 | 680 | H. Warps | The state-42 draw was not met in either run. | `fn:sub_0057EEC0_PlayerModeAllowed@0x0057EEC0` | ? | ? | ? | 1 |
| 75 | 685 | I. Death, resurrection and joining | I1. Pkt41Resurrect(player), player in mode 17: for the move and the draw ; | `fn:sub_0054C0E0_Pkt41Resurrect@0x0054C0E0` | ? | ? | ? | 1 |
| 76 | 700 | I. Death, resurrection and joining | The life, mana, stamina and state-54 writes were not logged. The point type comes from … | – | ? | ? | ? | 1 |
| 77 | 707 | J. Operate gates and real-time gates | OBJ_OperateDispatch refuses when the player is interacting with an NPC, has + set, or holds … | – | ? | ? | ? | 1 |
| 78 | 714 | J. Operate gates and real-time gates | The stamp is written only by PlayerTickSet, whose one caller is the hostility declaration | `0x005A5E50` | ? | ? | ? | 1 |
| 79 | 723 | J. Operate gates and real-time gates | Its other conditions and effects are read from the code: the declarer must stand in … | – | ? | ? | ? | 1 |
| 80 | 729 | J. Operate gates and real-time gates | The withdrawal (hostile = 0, ) left the declarer's + unchanged in the one case … | `0x005A5FA4` | ? | ? | ? | 1 |
| 81 | 738 | Draws by event kind | waypoint operate, mode 0 — the object's own seed | `fn:UNIT_AnimInit@0x00624390` | ? | ? | ? | 1 |
| 82 | 742 | Draws by event kind | Durance, lair, Arcane portals — per level seed | `fn:sub_00546AC0_DuranceActTravel@0x00546AC0` | ? | ? | ? | 1 |
| 83 | 752 | Outputs | arrival, a portal use or a warp. | `fn:sub_0053AEC0_PlayerChangeLevel@0x0053AEC0` | ? | ? | ? | 1 |
| 84 | 754 | Outputs | 23 and 28 with word 10's first-crossing bits. | `fn:WAYPOINT_Set@0x00660EC0` | ? | ? | ? | 1 |
| 85 | 755 | Outputs | Objects: the portal pair, player data + and +, state 102 on a portal user. | `fn:ITEMUSE_TownPortal@0x005BE290` | ? | ? | ? | 1 |
| 86 | 758 | Outputs |  | `fn:QUESTS_DispatchEvent@0x005438E0` | ? | ? | ? | 1 |
