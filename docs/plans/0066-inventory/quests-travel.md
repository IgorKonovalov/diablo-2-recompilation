# Plan 0066 inventory: quests/travel

- **Spec:** [quests/travel](../../specs/quests/travel.md), read at `main` `b5999f5e`.
- **Front matter `I`:** 86; the *Count* column sums to 86.
- Classes, batches and conventions as in [the inventory README](README.md#conventions).

| # | Line | Section | Claim (excerpt) | Anchor | Class | Route or reason | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | 28 | Entry points | click on a waypoint, a portal or another object … — sub_00548B00_UnitInteract case 2 → OBJ_OperateDispatch → g_ObjOperateFns[OperateFn] | `fn:sub_00548B00_UnitInteract@0x00548B00` | c | r2 `axt` chain: `sub_00548B00_UnitInteract` case 2 to `OBJ_OperateDispatch` to the OperateFn table | S3c | 1 |
| 2 | 29 | Entry points | the client picks a waypoint row (packet , {u32 … — sub_0054C5D0_Pkt49WaypointTravel → sub_00584F60_WaypointTravel | `fn:sub_0054C5D0_Pkt49WaypointTravel@0x0054C5D0` | a-logs | the p49 and wptr brackets of the plan 0042 logs (61 each): one wptr inside each p49 | S3a | 1 |
| 3 | 30 | Entry points | an NPC menu action other than 1–3 (13-byte packet) — NPC_MenuAction → sub_0054B830_NpcTravelMove | `fn:NPC_MenuAction@0x00579D60` | a-logs | the npcmove brackets (22) of the plan 0042 logs, each after a menu click | S3a | 1 |
| 4 | 31 | Entry points | the player uses an item whose Misc.pSpell is 2 … — g_ItemUseFns[2].use = ITEMUSE_TownPortal, by the dispatch of items/use § … | `fn:ITEMUSE_TownPortal@0x005BE290` | a-logs | the tp brackets (62) and the town refusals of the plan 0042 logs | S3a | 1 |
| 5 | 32 | Entry points | click on a warp tile (unit type 5, distance … — sub_00548B00_UnitInteract case 5 → sub_005550B0_WarpExitPos | `fn:sub_00548B00_UnitInteract@0x00548B00` | a-logs | the warp brackets (106) of run:2026-10-18-quests2 and run 1 | S3a | 1 |
| 6 | 33 | Entry points | the dead player presses "resurrect" (packet , mode 17 … — sub_0054C0E0_Pkt41Resurrect | `fn:sub_0054C0E0_Pkt41Resurrect@0x0054C0E0` | a-logs | the p41 brackets of h-death3 (run:2026-10-19-quests3) | S3a | 1 |
| 7 | 34 | Entry points | a player joins the game — sub_005394A0_PlayerPlaceInAct (callers , , ) | `fn:sub_005394A0_PlayerPlaceInAct@0x005394A0` | a-logs | the join and place lines of the plan 0042 logs (11 joins and the part 2 and 3 joins) | S3a | 1 |
| 8 | 35 | Entry points | the client reports its act loaded (packet ) — sub_0054C590_Pkt48ActChangeClear | `fn:sub_0054C590_Pkt48ActChangeClear@0x0054C590` | a-logs | the p48 brackets of x-meshif, x-meshifw, x-tyrael3 | S3a | 1 |
| 9 | 73 | Constants | placement mask, radius, step — 50, 1 | `fn:sub_0061B060_ActLevelSpot@0x0061B060` | a-logs | the FF0/FFX lines of the placement searches (mask, radius, step) in the plan 0042 logs | S3a | 1 |
| 10 | 74 | Constants | act-change second search — mask , radius 50, step 5 | `fn:sub_0053ACC0_PlayerChangeAct@0x0053ACC0` | a-logs | the chact free searches (32) of the plan 0042 logs: mask and step | S3a | 1 |
| 11 | 75 | Constants | portal field end search — size 3, masks /, no fallback | `fn:sub_0056D130_PortalObjectCreate@0x0056D130` | a-logs | the pocreate free searches (62) of the portal opens: size, masks, no fallback | S3a | 1 |
| 12 | 76 | Constants | portal town end search — mask , radius 50, step 5 | `fn:sub_0056CF40_PortalPartnerCreate@0x0056CF40` | a-logs | the partner free searches of the portal opens | S3a | 1 |
| 13 | 77 | Constants | portal-use state — state 102 for 75 frames | `fn:OBJOP_Portal@0x00584870` | b | a unit-state line (state 102 on and off, with frames) at portal use under quest-state.gdb | H3e | 1 |
| 14 | 84 | Inputs and oracles | the click, the packet, the NPC menu action — which travel the player asked for | `fn:sub_00548B00_UnitInteract@0x00548B00` | d-none | an inputs-table row: the travel asked for, no behavioural claim | – | 1 |
| 15 | 87 | Inputs and oracles | a level or act built on first arrival, a … — its draws are drlg's and drlg/collision § I's | `fn:sub_0053AC70_ActCreate@0x0053AC70` | d-none | a DRLG oracle declaration; its draws are drlg's | – | 1 |
| 16 | 89 | Inputs and oracles | party membership, hostility, a second player's portal — for hostility and for the no-party refusal ; for … | `fn:OBJOP_Portal@0x00584870` | d-2c | the different-ids compare and the quest-word test need a second player | – | 1 |
| 17 | 135 | A. Placement | A2. LevelPointFind(act, level, type) → (room, tx, ty): | `fn:sub_0066B2B0_LevelPointFind@0x0066B2B0` | a-logs | the LPL lines (2 356 lookups) of the plan 0042 logs: the level point pick per type | S3a | 1 |
| 18 | 177 | A. Placement | The last fallback, RangeB(level seed, level+), never ran in either run. | `0x0066AE70` | d-none | the last fallback ran in none of the 45 logs; no stock level is known to reach it | – | 1 |
| 19 | 191 | A. Placement | The act-change search uses step 5, so the player can land up to several cells … | – | a-logs | the chact placements (32) of the plan 0042 logs: the landing cell against the found point | S3a | 1 |
| 20 | 197 | B. The free-cell search | B1. COLL_FindFreeNear(room, pos, other, size, maskA, maskB, fallback, radius: i32, step: i32) → room: | `fn:COLL_FindFreeNear@0x0064DEA0` | a-logs | the free search checks (545) of the plan 0042 logs; an extended model for the partner footprints (62) | S3a | 1 |
| 21 | 264 | B. The free-cell search | The centre's row and column 128 are declared to that run; by the reading the … | – | c | a second reader of the collision map's dimensions (the loader at 0x0066A3E0 against its users) | S3c | 1 |
| 22 | 266 | B. The free-cell search | Sizes other than 1 and steps other than 1 are the reading: neither end of … | – | a-logs | the 62 portal searches with a partner footprint (not modelled): an extended free-cell model over them | S3a | 1 |
| 23 | 287 | C. Waypoint activation | C1. WaypointOperate(game, object, player) (OperateFn 23): for modes 1 and 2 ; | `fn:sub_00584E30_WaypointOperate@0x00584E30` | a-run | more mode-0 activations by the x-wpact5c route (the Frigid Highlands on foot, plan 0047) | H3e | 1 |
| 24 | 296 | C. Waypoint activation | C2. OBJINIT_Waypoint (InitFn 17): | `fn:OBJINIT_Waypoint@0x00547210` | b | a creation-mode line at `OBJINIT_Waypoint` (InitFn 17) under quest-state.gdb | H3e | 1 |
| 25 | 309 | C. Waypoint activation | For a waypoint in mode 0 the first operate both sets the bit and starts … | – | a-run | as row 23 | H3e | 1 |
| 26 | 312 | C. Waypoint activation | … attempts, from the Rogue Encampment and the Kurast Docks, reached no mode-0 waypoint). This stays | – | a-run | as row 23 | H3e | 1 |
| 27 | 315 | C. Waypoint activation | Plan 0047's runs operated seven waypoints from mode 0 on the Act V routes from … | – | a-run | as row 23 | H3e | 1 |
| 28 | 320 | C. Waypoint activation |  | `fn:sub_00584E30_WaypointOperate@0x00584E30` | a-run | as row 23 | H3e | 1 |
| 29 | 323 | C. Waypoint activation | Over the 45 logs of the three runs, a field waypoint first seen after a … | – | b | as row 24 | H3e | 1 |
| 30 | 327 | C. Waypoint activation | There is no proximity or touch test of the waypoint's own: activation is the operate, … | – | c | r2 scan: no waypoint-specific test before the operate; `Levels.Waypoint` over every row against `WAYPOINT_IndexFromLevel` | S3c | 1 |
| 31 | 330 | C. Waypoint activation | The arrival list is pushed only by WaypointTravel (§ D) and emptied by the first … | – | c | r2 scan of the writers of the arrival list's head (`WaypointArrivalAdd` and the init) | S3c | 1 |
| 32 | 332 | C. Waypoint activation | The draw. SetMode → UNIT_AnimInit draws RangeB(object seed, FrameDelta[mode] >> 3) when the row's | – | c | `Objects.txt` Sync and FrameDelta over every waypoint row (rule 2), with the seven logged mode-0 draws | S3c | 1 |
| 33 | 337 | C. Waypoint activation | Other writers of the waypoint record: NPC_MenuAction after an NPC act change (levels 40, 75, … | – | c | r2 scan of every writer of the waypoint record | S3c | 1 |
| 34 | 350 | D. Waypoint travel | D2. WaypointTravelCheck(objectId, level) → code: | `fn:sub_00549570_WaypointTravelCheck@0x00549570` | a-logs | the p49 gate and wptr lines of the plan 0042 logs: the return codes met | S3a | 1 |
| 35 | 373 | D. Waypoint travel | … 13, with no draw, for the towns and levels 46 and 74 the runs reached; | – | a-logs | the type-0 field arrivals of the kept waypoint chains (level seed type 0 checks); 133-136 have no waypoint | S3a | 1 |
| 36 | 375 | D. Waypoint travel | The act tabs of the waypoint menu are a client gate: the server tests only … | – | c | `WaypointTravelCheck` read with a second tool: no act test, only the target's bit | S3c | 1 |
| 37 | 397 | E. Act change through an NPC | E1. NPC_MenuAction(action, npc, arg), action ∉ {1, 2, 3}, by NPC class: | `fn:NPC_MenuAction@0x00579D60` | a-logs | the npcmove and npcact brackets of x-act, x-meshif, x-meshifw, x-tyrael3 by NPC class | S3a | 1 |
| 38 | 406 | E. Act change through an NPC | E2. NpcTravelMove(level, type): | `fn:sub_0054B830_NpcTravelMove@0x0054B830` | a-logs | the npcmove brackets (22) and their level seeds | S3a | 1 |
| 39 | 411 | E. Act change through an NPC | E3. NpcActTravel(npc): for word 7's branch ; | `fn:sub_005467E0_NpcActTravel@0x005467E0` | a-run | the refusing side of NPCs 155 and 210 on saves with words 6 and 14 b0 clear (x-act recipe) | H3e | 1 |
| 40 | 418 | E. Act change through an NPC | for returns 3 and 2 | `fn:sub_0054C590_Pkt48ActChangeClear@0x0054C590` | d-none | returns 3 and 2 need a 0x48 the stock client does not send | – | 1 |
| 41 | 433 | E. Act change through an NPC | The client's menus, as screenshotted in the run's development logs, explain it: NPC 367's has … | – | d-none | a client menu reading; the 367 branch is not reachable by stock play | – | 1 |
| 42 | 436 | E. Act change through an NPC | travel line and that the 367 branch is unreachable by stock play are | `fn:NPC_MenuAction@0x00579D60` | d-none | as row 41 | – | 1 |
| 43 | 438 | E. Act change through an NPC | The quest-word tests of NPCs 155, 210 and 367 were not run on their refusing … | – | a-run | as row 39 | H3e | 1 |
| 44 | 445 | E. Act change through an NPC | Word 28's branch (, reached only through NPC 367's menu branch) and E1's word 26 … | `0x0054684A` | d-none | word 28's branch is reached only through NPC 367's menu branch, which no stock state offers | – | 1 |
| 45 | 447 | E. Act change through an NPC | While + = 1, OBJ_OperateDispatch and PlayerIsBusy refuse, so the player can operate nothing and … | – | b | operate and waypoint attempts during an act change (`+0x4C` = 1), a new pilot step | H3e | 1 |
| 46 | 454 | E. Act change through an NPC | The returns 3 (a2 ≠ 1) and 2 (+ already 0) were not reached. What … | – | d-none | as row 40 | – | 1 |
| 47 | 459 | E. Act change through an NPC | NPC 520's return uses type 5 too, with A3's draw rule (a draw only when … | – | b | NPC 520's return travel (a new d2pilot menu row) under quest-state.gdb | H3e | 1 |
| 48 | 461 | E. Act change through an NPC | TownLevelLeave(old, new) marks the old town's store stale (items/vendors) and, on | – | a-logs | the vendors.py store lines around the town leaves in the plan 0042 logs | S3a | 1 |
| 49 | 470 | F. The Durance portal and the other travel objects | F1. DurancePortalOperate (OperateFn 46): | `fn:sub_00584750_DurancePortalOperate@0x00584750` | a-run | the Durance portal (342) operated on a save after Mephisto, under the `durance` bracket | H3e | 1 |
| 50 | 473 | F. The Durance portal and the other travel objects | F2. DuranceActTravel(level): | `fn:sub_00546AC0_DuranceActTravel@0x00546AC0` | a-run | as row 49 | H3e | 1 |
| 51 | 481 | F. The Durance portal and the other travel objects | Duriel's lair portal 100 (43) — class 100 → level 73; class 377 → its … | `fn:OBJOP_LevelPortal@0x00584D00` | a-run | Duriel's lair portal (100) under the `lvlportal` bracket (the run:2026-10-16 orifice route) | H3e | 1 |
| 52 | 482 | F. The Durance portal and the other travel objects | Arcane portal 298 (34) — 74 → 54 at type 0; 54 → 74 … | `fn:OBJOP_ArcanePortal@0x005846B0` | a-run | the Arcane portal (298) both ways under the `arcane` bracket (waypoint to 74) | H3e | 1 |
| 53 | 483 | F. The Durance portal and the other travel objects | Durance portal 342 (46) — word 22 bit 13 or 0 | `fn:sub_00584750_DurancePortalOperate@0x00584750` | a-run | as row 49 | H3e | 1 |
| 54 | 485 | F. The Durance portal and the other travel objects | Baal's portals 563/569 (70) — quest 36's private flag | `fn:sub_0058E6A0_A5Q6_BaalPortalOperate@0x0058E6A0` | b | Baal's portals after a Baal kill under quest-state.gdb | H3b | 1 |
| 55 | 486 | F. The Durance portal and the other travel objects | the last portal 565 (72) — word 40 bit 13 | `fn:sub_0058E740_A5Q6_LastPortalOperate@0x0058E740` | b | the last portal after a Baal kill | H3b | 1 |
| 56 | 488 | F. The Durance portal and the other travel objects | Object 410 Siege Control shares OperateFn 46, but no DS1 id, objgroup cell or creation … | – | c | the DS1, objgroup and creation-call scan for object 410, repeated with a second parser | S3c | 1 |
| 57 | 490 | F. The Durance portal and the other travel objects | Each of these objects in mode 0 goes to mode 1 and queues object event … | – | a-run | as rows 49 and 52: the mode change and event 1 at each operate | H3e | 1 |
| 58 | 516 | Opening | G1. ITEMUSE_TownPortal(player, item): | `fn:ITEMUSE_TownPortal@0x005BE290` | a-logs | the tp brackets of the plan 0042 logs | S3a | 1 |
| 59 | 533 | Opening | G2a. PortalPartnerCreate(field, dest, src): for the draws and their order ; | `fn:sub_0056CF40_PortalPartnerCreate@0x0056CF40` | a-run | a town portal in Duriel's lair at each quest-13 private state | H3e | 1 |
| 60 | 557 | Opening | The field end's search tests a walk back to the point (x, y) with mask … | – | a-logs | the field-end searches of the 62 portal opens (mask 0xC01 walk back) | S3a | 1 |
| 61 | 563 | Opening | The refusal on level 136 was not reached. | `fn:ITEMUSE_TownPortal@0x005BE290` | d-none | level 136 is not reachable in this Game.exe (its portals do not open) | – | 1 |
| 62 | 564 | Opening | A portal from Duriel's lair (73) puts its town end at level 40's point type … | – | a-run | as row 59 | H3e | 1 |
| 63 | 571 | Using a portal | G3. OBJOP_Portal(game, object, operator) (OperateFn 15): | `fn:OBJOP_Portal@0x00584870` | a-logs | the portal brackets (122) of the plan 0042 logs | S3a | 1 |
| 64 | 619 | Using a portal | The compare of two different party ids needs a third player, since two players hold … | – | d-2c | a third player | – | 1 |
| 65 | 623 | Using a portal | When the free-spot search at the destination finds no room, the use returns 0 with … | – | d-none | a destination with no free room is a guard stock levels never fail | – | 1 |
| 66 | 625 | Using a portal | The quest-word test needs a second player (plan 0044, MP27). | – | d-2c | a second player (plan 0044 MP27) | – | 1 |
| 67 | 632 | Closing and permanent portals | A player's class-59 pair is freed when (a) the owner goes through the town end; … | – | a-logs | the portal cycles of x-lut and c-tp: the old pair freed at each new open and at the town end; cases (a) and (b) only, (c) and (d) stay `[I]` unless another log holds them (Phase 0 review) | S3a | 1 |
| 68 | 640 | Closing and permanent portals | Permanent portals (class 60). OBJINIT_Portal (InitFn 12) sets the destination from the level the | – | a-logs | x-tyrael3's object 566 and x-anya's portal lines: the class-60 destinations | S3a | 1 |
| 69 | 649 | H. Warps | H1. UnitInteract case 5: a warp unit within distance 5 → WarpExitPos(player, warp) | `fn:sub_00548B00_UnitInteract@0x00548B00` | a-logs | the warp brackets with the player's distance to the warp unit | S3a | 1 |
| 70 | 650 | H. Warps | H2. WarpExitPos(player, warp): for the placement with no draw ; | `fn:sub_005550B0_WarpExitPos@0x005550B0` | a-logs | the warp gate checks of the plan 0042 logs (the 100 gate, the summit) | S3a | 1 |
| 71 | 656 | H. Warps | H3. QUESTS_WarpGate(src, dest) → refuse: | `fn:QUESTS_WarpGate@0x00545B80` | a-logs | as row 70 | S3a | 1 |
| 72 | 662 | H. Warps | H4. The walk command PlayerModeCmd(0, 2, x, y, 0) first calls PlayerModeAllowed: | `fn:sub_005809D0_PlayerModeCmd@0x005809D0` | b | a walk in state 42 with that skill's flag (a new state line) | H3e | 1 |
| 73 | 673 | H. Warps | The gates are quest code (quests/progression § Warp and portal gates). | – | a-run | warp 64 into 100 with the orb whole (x-orbno recipe) and the 120 warp tiles 82 and 83 | H3e | 1 |
| 74 | 680 | H. Warps | The state-42 draw was not met in either run. | `fn:sub_0057EEC0_PlayerModeAllowed@0x0057EEC0` | b | as row 72 | H3e | 1 |
| 75 | 685 | I. Death, resurrection and joining | I1. Pkt41Resurrect(player), player in mode 17: for the move and the draw ; | `fn:sub_0054C0E0_Pkt41Resurrect@0x0054C0E0` | b | h-death3's recipe with a line of the life, mana, stamina and state-54 writes at resurrect | H3e | 1 |
| 76 | 700 | I. Death, resurrection and joining | The life, mana, stamina and state-54 writes were not logged. The point type comes from … | – | b | as row 75 | H3e | 1 |
| 77 | 707 | J. Operate gates and real-time gates | OBJ_OperateDispatch refuses when the player is interacting with an NPC, has + set, or holds … | – | b | operates with a cursor item held and while in an NPC talk (new pilot steps) | H3e | 1 |
| 78 | 714 | J. Operate gates and real-time gates | The stamp is written only by PlayerTickSet, whose one caller is the hostility declaration | `0x005A5E50` | c | r2 `axt` on `PlayerTickSet`: one caller | S3c | 1 |
| 79 | 723 | J. Operate gates and real-time gates | Its other conditions and effects are read from the code: the declarer must stand in … | – | d-2c | the hostility declaration needs two players | – | 1 |
| 80 | 729 | J. Operate gates and real-time gates | The withdrawal (hostile = 0, ) left the declarer's + unchanged in the one case … | `0x005A5FA4` | d-2c | as row 79 | – | 1 |
| 81 | 738 | Draws by event kind | waypoint operate, mode 0 — the object's own seed | `fn:UNIT_AnimInit@0x00624390` | a-run | as row 23 | H3e | 1 |
| 82 | 742 | Draws by event kind | Durance, lair, Arcane portals — per level seed | `fn:sub_00546AC0_DuranceActTravel@0x00546AC0` | a-run | as rows 49-52: the level seed at arrival | H3e | 1 |
| 83 | 752 | Outputs | arrival, a portal use or a warp. | `fn:sub_0053AEC0_PlayerChangeLevel@0x0053AEC0` | a-logs | the chlevel brackets (81) of the plan 0042 logs | S3a | 1 |
| 84 | 754 | Outputs | 23 and 28 with word 10's first-crossing bits. | `fn:WAYPOINT_Set@0x00660EC0` | a-logs | the act travel word checks and the waypoint record bit checks of the plan 0042 logs | S3a | 1 |
| 85 | 755 | Outputs | Objects: the portal pair, player data + and +, state 102 on a portal user. | `fn:ITEMUSE_TownPortal@0x005BE290` | a-logs | the tp and portal brackets (+0x48, +0x4C); state 102 rides row 13 | S3a | 1 |
| 86 | 758 | Outputs |  | `fn:QUESTS_DispatchEvent@0x005438E0` | a-logs | the de lines of the travel events in the plan 0042 logs | S3a | 1 |

**Totals by class:** a-logs 32, a-run 18, b 12, c 9, d-2c 5, d-none 10 (sum 86).
