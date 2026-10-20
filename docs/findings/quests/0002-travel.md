# 0002 — Travel: waypoints, act changes, town portals, warps and where a player is placed

> **Subsystem:** quests/travel
> **Question:** how does a player activate and use a waypoint, change act, open and use a town portal, and where is a
> player placed on entering a level (by waypoint, NPC, portal, warp, death or joining), with which draws?
> **Date:** 2026-10-17   **Plan:** 0042 (Phase 1 and 1b, static; Phase 2 run:2026-10-17-quests, § 12; part 2 run:2026-10-18-quests2, § 13; part 3 run:2026-10-19-quests3, § 14)   **Status:**
> answered (Phase 2 part 1 reviewed 2026-10-17, accept with fixes; part 2 reviewed 2026-10-19, accept with fixes; part 3 reviewed 2026-10-20, accept with fixes; plan 0042 closed 2026-10-20)

Static reading of the pinned `Game.exe` (Ghidra on the lane's copy, objdump for the instruction-level reads); no game
run. Names are ours. "Record" and "word *q*, bit *s*" are as in [save/0002](../save/0002-quest-words.md): bit `16q + s`
of the player's quest record for the game's difficulty. "Waypoint record" is player data `+0x1C + 4·difficulty`
(`fn:sub_00547F50_PlayerWaypointRecord@0x00547F50`). "Level seed" is the level's `+0x1C4` seed
([drlg/0005 § 9](../drlg/0005-collision.md#9-nearwarptestgame-room-x-y-and-the-warp-points)). Packet numbers are the
client-to-server opcodes of `data:g_SrvPacketTable@0x006E0D18` (8-byte entries `{handler, flag}`). Quest-state readers
and writers of the act changes are also listed per quest in [quests/0001](0001-progression.md).

## Answer (summary)

- [I] **Every placement goes through one routine.** A player who changes level by waypoint, NPC, portal, death or
  joining is put at `ActLevelSpot(act, level, pointType, size)` (`0x0061B060`): `LevelPointFind(pointType)` gives a
  tile, it becomes the subtile `(5·tx + 3, 5·ty + 3)`, and `COLL_FindFreeNear(room, pos, size, mask 0x1C09, radius 50,
  step 1)` moves it to the nearest free cell. On a level with `Levels.Position` set (the 18 towns and boss levels)
  `LevelPointFind` **steps the level seed once** (`LevelPointPick`) for every point type but 13; on other levels it
  takes the waypoint room, an entry-warp room, the middle room or, last, a room drawn on the level seed. The free-cell
  search itself draws nothing. (0x0061B060, fn:sub_0066B2B0_LevelPointFind@0x0066B2B0,
  fn:sub_0066AC40_LevelPointPick@0x0066AC40, fn:COLL_FindFreeNear@0x0064DEA0, tbl:Levels.txt:Position)
- [I] **A waypoint is activated by operating it, nothing else.** `WaypointOperate` (`OperateFn` 23) sets the bit of
  the operated object's level in the waypoint record on **every** operate; a waypoint in mode 0 goes to mode 1 and
  queues object event 1; one in mode 1 or 2 opens the menu (message `0x63` with the 16-byte record). There is no
  proximity or touch test of its own (the generic operate gates apply). In a town the waypoint's `InitFn` 17 puts it
  straight into mode 2, and an arrival by waypoint into a room whose waypoint is not yet created sets it to mode 1 when
  it is. Five waypoint rows (429, 494, 496, 511, 539) have `Sync` 0, so each of their mode changes draws their
  unit seed. (fn:sub_00584E30_WaypointOperate@0x00584E30, 0x00547210, 0x00547170, fn:UNIT_AnimInit@0x00624390,
  tbl:Objects.txt:Sync)
- [I] **Waypoint travel** is packet `0x49` (`{object id, u16 level}`): refused within **10 000 ms of real time** of the
  player's tick stamp `+0x160`, refused unless the object is a waypoint in the player's act near the player and the
  target's bit is set; then `WaypointTravel` arrives at point type 13 for a town or level 46, 74, 133–136 and type 0
  otherwise, through `PlayerChangeLevel`. No quest word is read. (0x0054C5D0, 0x00549570,
  fn:sub_00584F60_WaypointTravel@0x00584F60, fn:sub_0053AEC0_PlayerChangeLevel@0x0053AEC0)
- [I] **Act changes by NPC** are a branch of `NPC_MenuAction` for an action other than 1–3: NPC 155 needs word 6
  bit 0 and goes to level 40, NPC 210 needs word 14 bit 0 and goes to 75, NPC 367 needs an expansion game and word 26
  bit 0 and goes to 109 (all at point type 0, then `NpcActTravel` writes the travel words and the town's waypoint bit
  is set); NPCs 175, 264 and 520 go back to levels 1, 40 and 103 at point type 5 with no quest-word test (264 and 520 only for action 0; row names `warriv2`,
  `meshif2`, `cain6`, `[L]` as identities). The player is moved
  **before** the words are written. (fn:NPC_MenuAction@0x00579D60 0x0057A650–0x0057A7D6, 0x0054B830,
  fn:sub_005467E0_NpcActTravel@0x005467E0)
- [C] **Part 3** (run:2026-10-19-quests3, § 14): in the state logged (expansion, word 26 b0, after Tyrael's 0x4E20 talk)
  the stock client offers NPC 367 no travel line (that the line is never offered is `[I]`: the client's menu builder
  was not read; architect review), and the expansion Act IV → V travel is the Harrogath portal (object 566, `0x005B5880`: word 28 b0 and b13 once, `+0x4C`, then
  `NpcTravelMove(109, 5)`), not the 367 branch (which stays `[I]`, not reached by stock play); Meshif's return
  (`NpcTravelMove(40, 5)`) steps Lut Gholein's level seed once per trip (a type-5 point found). (0x005B5880, 0x0054B830)
- [I] **The Durance portal** (`OperateFn` 46) needs word 22 bit 13 or bit 0; on level 102 it writes word 23 (and 18),
  sets waypoint 103 and moves the player to level 103 at point type 0. On any other level the same handler only calls
  `0x005BCFD0`, which opens the Mephisto portal and bridge objects and moves no one; so `Siege Control` (410), which
  shares `OperateFn` 46, would move no player; no DS1 id, `objgroup` cell or creation call names 410, so it is never
  placed (quests/0001 § 10). (fn:sub_00584750_DurancePortalOperate@0x00584750,
  fn:sub_00546AC0_DuranceActTravel@0x00546AC0, 0x005BCFD0; quests/0001 § Act III)
- [I] **Town portal.** Using an item whose `pSpell` is 2 (`tsc`, `tbk`) runs `g_ItemUseFns[2].use` = `0x005BE290`:
  refused in a town and on level 136; it first **closes the player's previous portal pair** (one per player, player
  data `+0x48`), then creates a class-59 object at the nearest free cell (`mask 0x3E01`, size 3, no fallback) of the
  player's position, and a class-59 partner in the town of that act at the town's **point type 11** (the waypoint
  point), moved by a step-5 free search (`mask 0xBE11`). Draws, in order: game seed (field portal's unit seed), the
  town's level seed (`LevelPointPick`), game seed (partner): three, **not five** (corrected by Phase 2, § 12: both ends
  leave `SUnitCreate` already in mode 1 and 2, so the `SetMode` draws on their own seeds never happen; 62 opens,
  run:2026-10-17-quests); a town room updated for the first time adds its population's game-seed draws (oracle).
  (0x005BE290, fn:sub_0056D130_PortalObjectCreate@0x0056D130, 0x0056CF40, 0x00535430,
  fn:sub_00555230_SUnitCreate@0x00555230, data:g_ItemUseFns@0x00741790, tbl:Misc.txt:pSpell)
- [I] **Using a portal** (`OperateFn` 15, `0x00584870`) moves the player to the partner's position (free search, mask
  `0x1C09`) and gives state 102 for 75 frames. Someone else's class-59 portal is refused unless word
  `QuestFlag` (classic) or `QuestFlagEx` (expansion) of the **destination** level has bit 0 set in the user's record.
  When the owner goes through the town end, both ends are freed. Two gates read **real time** (`GetTickCount`): a 5000 ms
  wait after a tick stamp, and the 10 000 ms waypoint wait. (0x00584870 0x005849BB–0x00584A20, 0x00584B90–0x00584C40,
  tbl:Levels.txt:QuestFlag, tbl:Levels.txt:QuestFlagEx)
- [I] **Warps.** Clicking a warp tile (packets `0x13`/`0x16`, unit type 5, distance below 5) runs `WarpExitPos`: the
  player is put at the paired warp unit's position moved by the free search (mask `0x1C09`, fallback to the start
  cell), unless the destination is 73, 100, 118 or 128 (from 120), or 132 and a quest gate refuses (`0x00545B80`);
  then a walk command to `+ExitWalkX/Y`. No draw in the position; the walk command draws the player's unit seed only
  with state 42 (below). Death: packet `0x41` from mode 17 restores life, mana and stamina and calls
  `PlayerChangeLevel(town of the act, type 0)`. Joining: the act's level `act+0x08` at type 0. (fn:sub_005550B0_WarpExitPos@0x005550B0,
  0x00548B00, 0x00545B80, 0x0054C0E0, 0x005394A0)
- [I] **Draws by event kind** (§ 10): waypoint operate: none, or the waypoint's unit seed (five `Sync` 0 rows); waypoint
  travel, NPC act change, death, join, the lair, Arcane and Durance portals: the destination's level seed when it has
  `Position` (plus a full level or room build when the level or room does not exist yet, DRLG oracles); town portal
  creation: three (above; corrected from five by Phase 2, § 12; a town room updated for the first time adds its
  population's game-seed draws, an oracle); portal use: none of its own (a room activation is an oracle); warp: none.
  (fn:sub_0054C5D0_Pkt49WaypointTravel@0x0054C5D0, fn:sub_005467E0_NpcActTravel@0x005467E0,
  fn:sub_0066AC40_LevelPointPick@0x0066AC40, fn:sub_0056D130_PortalObjectCreate@0x0056D130, 0x00584870)

## Leads used

Blind first: every claim above was written from the code before any community text was read; the pages below were
fetched and compared afterwards.

### Phase 1b verdicts

- [L] src:arreat-summit-basics-travel: a waypoint is activated by clicking it. **held**
  Detail: the operate sets the record bit on every click (§ 2); there is no walk-by activation.
- [L] src:arreat-summit-basics-travel: a player can travel to any activated waypoint from any other, using act tabs.
  **held with refinement**
  Detail: the server tests only the target's bit and a 10 000 ms real-time wait (§ 3); the act tabs are the client's
  gate (save/0002).
- [L] src:arreat-summit-basics-travel: party members do not share waypoints, and a town portal takes a player to a
  waypoint he has not found. **held**
  Detail: the portal operate reads no waypoint bit (§ 6).
- [L] src:arreat-summit-basics-travel: a scroll opens a portal near the character to the nearest town. **held with
  refinement**
  Detail: the field end is the nearest free cell (mask `0x3E01`) to the player; the town end is the act's town at its
  type-11 point, moved by a step-5 search; refused in a town and on level 136 (§ 6).
- [L] src:arreat-summit-basics-travel: a new portal closes the caster's previous one. **held**
  Detail: `PlayerPortalClose` at the start of `ITEMUSE_TownPortal` (§ 6).
- [L] src:arreat-summit-basics-travel: the portal stays open until the caster re-enters it from town. **held**
  Detail: the owner's use of the town end frees both ends (§ 6).
- [L] src:arreat-summit-basics-travel: only party members may use a player's portal. **held with refinement**
  Detail: the owner and the operator must have the same party id; the owner is exempt from this party test (§ 6).
  Refinement (2026-10-20, `lane/mp26`): an operator in no party is refused before the ids are compared, so two
  players both in no party do not pass (multiplayer/0001 § 6, MP26; § 6 here).
- [L] src:arreat-summit-basics-travel: going hostile closes the player's portal. **held with refinement**
  Detail: `0x005A5E50` closes it and sets the declarer's tick; it reads as the hostility toggle (town only, level 9
  or more on both players, relation bit 8, a 60 s stamp per pair: [multiplayer/0001 § 4](../multiplayer/0001-cases.md#4-the-hostility-declaration-and-the-two-travel-gates),
  plan 0044 Phase 1, folded at its review 2026-10-17). (0x005A5E5F–0x005A5E9D, 0x005A5F41–0x005A5F65)
- [L] src:arreat-summit-basics-travel: a hostile player cannot use other players' portals. **held** (was "not
  covered"; plan 0044 Phase 1 review)
  Detail: `OBJOP_Portal`'s first test refuses when `0x00535B10(game, operator)` is non-zero (the operator holds
  relation bit 8 toward some player of the game) and the portal's owner is not the operator. (0x0058488F–0x005848B1,
  0x00535B10–0x00535B44, 0x00535AF0–0x00535B0D)
- [L] src:arreat-summit-basics-travel: a 10-second delay separates a hostility declaration from leaving town by
  waypoint or portal. **held** for waypoints (10 000 ms, § 3), **contradicted** for portals: the portal gate waits
  5000 ms (`0x00584870`). Both gates read the operator's own player data `+0x160` (`PlayerTickGet` with EDX = 0 at
  0x0054C5F5 and 0x005848BA), set to `GetTickCount()` by `0x0055B720`, whose one caller is the declaration
  `0x005A5E50`; no portal is exempt, the operator's own included (plan 0044 Phase 1 review). Multiplayer only, not
  reachable with one client; plan 0044 MP24 stages it.
- [L] src:arreat-summit-quest-acts: another player's portal into an area behind a "blocking quest" (cow level: Terror's
  End or Eve of Destruction; Durance: The Blackened Temple) cannot be entered without that quest. **held**
  Detail: `QuestFlag` 26 / `QuestFlagEx` 40 on level 39 and 21 on 100–102, bit 0 of that word (§ 6).

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x0061B060` | `sub_0061B060_ActLevelSpot` | `(act, level, type, &x, &y, size)`: level point → subtile + 3 → free cell (mask 0x1C09, radius 50, step 1) → room | I |
| `0x0064E7B0` | `sub_0064E7B0_FreeNearFallback` | `COLL_FindFreeNear(room, pos, 0, size, mask, mask, fallback, 50, 1)` | I |
| `0x0064E7E0` | `sub_0064E7E0_FreeNearStep` | `COLL_FindFreeNear(room, pos, 0, size, mask, mask, 0, 50, step)` | I |
| `0x0064E810` | `sub_0064E810_FreeNearPair` | `COLL_FindFreeNear(room, pos, other, size, mask, mask2, fallback, 50, 1)` | I |
| `0x00554EA0` | `sub_00554EA0_UnitTeleport` | `(room, x, y, noSearch, flag)`: free search unless `noSearch`, move, path flags; player: history and tick | I |
| `0x0054C5D0` | `sub_0054C5D0_Pkt49WaypointTravel` | packet 0x49: 10 000 ms gate, check, `WaypointTravel` | I |
| `0x00549570` | `sub_00549570_WaypointTravelCheck` | object exists, same act, near, target bit set → 0 | I |
| `0x00547210` | `OBJINIT_Waypoint` | `InitFn` 17: arrival list → mode 1, town → mode 2 | I |
| `0x00547170` | `sub_00547170_WaypointArrivalAdd` | pushes `{room, x, y}` on objrgn `+0x1110` | I |
| `0x00550140` | `OBJINIT_TownPortal` | `InitFn` 11: destination = town of the act | I |
| `0x00584870` | `OBJOP_Portal` | `OperateFn` 15: portal use | I |
| `0x00584D00` | `OBJOP_LevelPortal` | `OperateFn` 43: class 100 → 73, class 377 → its object byte, type 0 | I |
| `0x005846B0` | `OBJOP_ArcanePortal` | `OperateFn` 34: 74 ↔ 54 (type 0 into 54, type 11 into 74) | I |
| `0x005BE290` | `ITEMUSE_TownPortal` | `g_ItemUseFns[2].use`: the town portal of a scroll or book | I |
| `0x0056CF40` | `sub_0056CF40_PortalPartnerCreate` | town end at point 11, free search step 5, links the pair | I |
| `0x00535430` | `sub_00535430_PlayerPortalClose` | frees the player's pair (class 59 only), unpins their rooms | I |
| `0x005353B0` | `sub_005353B0_PlayerPortalSet` | player data `+0x48` = portal id | I |
| `0x005353F0` | `sub_005353F0_PlayerPortalGet` | player data `+0x48` | I |
| `0x00553720` | `sub_00553720_PortalPartnerGet` | partner by object data `+0x98` | I |
| `0x00535060` | `sub_00535060_PlayerIsBusy` | interacting, cursor item, or player data `+0x4C` | I |
| `0x0055B6C0` | `sub_0055B6C0_PlayerTickGet` | player data `+0x160`, or the per-player entry of list `+0x38` | I |
| `0x0055B720` | `sub_0055B720_PlayerTickSet` | writes both (only caller `0x005A5E50`) | I |
| `0x0054B830` | `sub_0054B830_NpcTravelMove` | level 0 → act town; same act → class-59 portal; else `PlayerChangeLevel` | I |
| `0x00548B00` | `sub_00548B00_UnitInteract` | packets 0x13/0x16: player, NPC, object (distance < 51), item, warp (distance < 5) | I |
| `0x0054C0E0` | `sub_0054C0E0_Pkt41Resurrect` | packet 0x41: dead player back to the act's town | I |
| `0x005394A0` | `sub_005394A0_PlayerPlaceInAct` | join: act level `+0x08`, type 0; hirelings to the town point | I |
| `0x00545B80` | `QUESTS_WarpGate` | warp destination 73, 100, 118/128 from 120, 132 → quest gate function | I |
| `0x00545830` | `QUESTS_PortalTownSpot` | partner spot override for a portal from level 73 (`0x0059DFD0`: level 40, type 12) | I |
| `0x005809D0` | `sub_005809D0_PlayerModeCmd` | player command (walk to x, y after a move) | I |
| `0x0057EEC0` | `sub_0057EEC0_PlayerModeAllowed` | mode-change gate; `Range(unit seed, 100)` under state 42 | I |
| `0x00582A30` | `sub_00582A30_PortalToTownAtUnit` | class-59 portal to the act's town at a unit's free cell | I |
| `0x005A9930` | `sub_005A9930_PermPortalAtUnit` | class-60 portal at a unit's path position, no free search; then `RoomPinSet(room, 1)` on the unit's room | I |
| `0x0061AB00` | `sub_0061AB00_RoomIsTown` | `LevelIsTown(room level)` | I |
| `0x0061AAF0` | `sub_0061AAF0_LevelIsTown` | thunk to `sub_006426A0_LevelIsTown` | I |
| `0x0061AB70` | `sub_0061AB70_ActTownLevel` | act → town level, table `0x006E7D1C` | I |
| `0x0061AE80` | `sub_0061AE80_ActStartLevel` | act `+0x08` | I |

Already named and read here: `sub_00584E30_WaypointOperate`, `sub_00584F60_WaypointTravel`, `sub_0053AEC0_PlayerChangeLevel`,
`sub_0053ACC0_PlayerChangeAct`, `sub_00537340_TownLevelLeave`, `sub_005467E0_NpcActTravel`, `sub_00546AC0_DuranceActTravel`,
`sub_00584750_DurancePortalOperate`, `sub_0056D130_PortalObjectCreate`, `OBJINIT_Portal`, `sub_005550B0_WarpExitPos`,
`COLL_FindFreeNear`, `sub_0066B2B0_LevelPointFind`, `sub_0066AC40_LevelPointPick`, `OBJ_OperateDispatch`, `UNIT_SetMode`,
`UNIT_AnimInit`.

## Walkthrough

### 1. Entry points

| Trigger | Server entry | Notes |
|---|---|---|
| click on a waypoint, portal, other object | packet `0x13`/`0x16` → `0x00548B00` case 2 → `0x00584540` → `OBJ_OperateDispatch` → `g_ObjOperateFns[OperateFn]` | object distance < `0x33`, line test |
| choose a waypoint row | packet `0x49` → `0x0054C5D0` → `WaypointTravel` | 9 bytes: object id, level |
| NPC "travel" menu | `NPC_MenuAction` (action ∉ {1, 2, 3}) → `0x0054B830` | § 5 |
| use a scroll or book | item use, `pSpell` 2 → `0x005BE290` | § 6 |
| click a warp tile | packet `0x13`/`0x16` → `0x00548B00` case 5 → `WarpExitPos` | distance < 5 |
| press "resurrect" | packet `0x41` → `0x0054C0E0` | mode 17 only |
| join | `0x005394A0` (callers `0x00530237`, `0x0053A3EB`, `0x0053A4E6`) | § 8 |

- [I] `OBJ_OperateDispatch` refuses when the player is interacting with an NPC, has player data `+0x4C` set (the act
  change in progress, § 5), or holds a cursor item (except class 267), and never operates classes 121, 122, 22. It
  fetches the object region seed (`OBJRGN_GetSeed`) before calling the handler. (fn:OBJ_OperateDispatch@0x00584420)
- [I] A changed level is reported to the quests as event 3 by the room sync (`sub_005380D0_ClientRoomSync`, old level
  in the event's `+0x14`, new one in `+0x18`), whatever moved the player; a portal use from a town also raises it
  itself (`0x00584AF6`). See [quests/0001 § 2](0001-progression.md#2-events).

### 2. Waypoint activation

```text
WaypointOperate (OperateFn 23; ctx: [0] game, [1] object, [2] player, [4] class)            [I] (fn:sub_00584E30_WaypointOperate@0x00584E30)
  n = WAYPOINT_IndexFromLevel(level of the object's room); if n valid: WAYPOINT_Set(waypoint record, n)
  if object.mode == 0: SetMode(object, 1); queue object event 1 at frame + (Objects+0xDC >> 8) + 1
  elif object.mode in (1, 2) and not PlayerIsBusy(player):
      send 0x63 {object id, 16-byte record}; set the player's interaction (type 2, object id)
OBJINIT_Waypoint (InitFn 17)                                                                [I] (0x00547210)
  for each entry {room, x, y} of objrgn+0x1110:                    ; pushed by WaypointTravel (0x00547170)
      if entry.room == object's room or (x, y) inside it:
          if object.mode == 0: SetMode(object, 1); queue event 1 at frame + (Objects+0xDC >> 8)
          free the entry, objrgn+0x1110 = 0; return
  if RoomIsTown(object's room): SetMode(object, 2)
```

- [I] The record bit is set on every operate, before the mode test, so the first click both marks the waypoint and
  starts the animation; the menu opens from the next click (mode 1 or 2). (0x00584E78–0x00584E81)
- [I] The arrival list is pushed only by `WaypointTravel` and freed by the first waypoint init that matches; the head is
  zeroed after freeing one node (any older nodes are dropped). (0x00547170, 0x00547290)
- [I] **Draw.** `UNIT_SetMode` → `UNIT_AnimInit` draws `RangeB(object seed, FrameDelta[mode] >> 3)` when the row's
  `Sync` is 0 ([objects/0001](../objects/0001-object-population.md)). Waypoint rows with `Sync` 0 are 429, 494, 496,
  511, 539 (`FrameDelta` 200 for mode 1, 100 for mode 2); the other eleven have `Sync` 1.
  (fn:UNIT_SetMode@0x00624690, fn:UNIT_AnimInit@0x00624390, tbl:Objects.txt:Sync, tbl:Objects.txt:FrameDelta)
- [I] Other writers of the waypoint record: `NPC_MenuAction` after an NPC act change (40, 75, 109; § 5),
  `DurancePortalOperate` (103), and quest code `0x005B4FF0` (quests/0001 § Act IV). (fn:WAYPOINT_Set@0x00660EC0 callers)
- [I] *2026-10-20 (plan 0047 Phase 1, static, r2/objdump):* **a field waypoint is created in mode 0 unless the player
  arrived in its room by waypoint.** A waypoint is a DS1 preset object. `sub_00555910_PresetUnitSpawn` passes the
  preset unit's `+0x00` (its mode: 0 for every type-2 preset unit, [drlg/0004](../drlg/0004-preset-units.md) row 7)
  as the fifth argument of `sub_005557D0_PresetUnitDispatch` (push at 0x0055593A), which passes it on as the mode
  argument of `sub_00555230_SUnitCreate` (push at 0x00555837). For an object, `SUnitCreate` stores it at unit `+0x10`
  (0x005553DF–0x005553E5) before `OBJ_ServerInit` (0x005553FE) runs the `InitFn`. `g_ObjInitFns[17]` is
  `OBJINIT_Waypoint` (`0x00731C04` holds `0x00547210`). Reading `OBJINIT_Waypoint` again: it walks the arrival list
  at `objrgn+0x1110` and matches an entry by room pointer (0x00547231) or by the entry's point inside the room's
  rectangle (`+0x4C`/`+0x54` in x, `+0x50`/`+0x58` in y, 0x0054723C–0x0054725D); on a match it sets mode 1 only if the
  mode is 0 (0x0054728C), queues object event 1 at frame + (Objects `+0xDC` >> 8) (0x005472AF–0x005472CA), frees the
  entry and zeroes the list head (0x005472EC). With no match it sets mode 2 when `sub_0061AB00_RoomIsTown` holds
  (0x0054726A–0x00547279), and otherwise leaves the mode alone. The function never reads the waypoint record, so a
  waypoint the player already holds is also created in mode 0 when its room is built on foot or through a warp.
  (fn:sub_00555910_PresetUnitSpawn@0x00555910, fn:sub_005557D0_PresetUnitDispatch@0x005557D0,
  fn:sub_00555230_SUnitCreate@0x00555230, fn:OBJ_ServerInit@0x0054F5D0, data:g_ObjInitFns@0x00731BC0,
  fn:OBJINIT_Waypoint@0x00547210, fn:sub_0061AB00_RoomIsTown@0x0061AB00)
- [I] *2026-10-20 (plan 0047 Phase 1):* **a route a fresh character can walk**, for the plan's 20 activations with
  the `Sync` 0 draw. The five waypoint rows with `Sync` 0 (429, 494, 496, 511, 539) are the expansion ones by their
  descriptions (`expansion no snow`, `baals_waypoint`, `wilderness_waypoint`, `icecave`, `temple`), and four Act V
  field waypoints lie one warp apart below the Arreat Plateau: LvlWarp 71 from the Plateau (112) to the Crystalline Passage (113),
  74 to the Glacial Trail (115), 74 to the Frozen Tundra (117), 71 to the Ancients' Way (118) (Levels `Vis`/`Warp`
  columns). A save holding only the towns and the Plateau (`TravelWpArreat`,
  `tools/d2s_recipes/quest-p47wp.json`) arrives at the Plateau by waypoint (its own waypoint takes the arrival
  node, the room the arrival names), then takes the warps: no arrival node names the four rooms, so each waypoint is
  created in mode 0, and operating it is an activation (§ 2 above). The ice caves' waypoint rooms are LvlPrest Def
  1034–1037, the tundra's 953 or 954. Sessions `x-wpact5r-0` … `-5` in `tools/quest_sessions.py` (six map seeds,
  four activations each); not run. (tbl:Levels.txt:Warp0, tbl:Objects.txt:Sync, tbl:LvlPrest.txt:Def,
  fn:OBJINIT_Waypoint@0x00547210)

### 3. Waypoint travel

```text
Pkt49 (0x0054C5D0) {u32 objectId, u16 level}                                                 [I]
  if GetTickCount() < PlayerTickGet(player, 0) + 10000: cancel; return
  r = WaypointTravelCheck(objectId, level)          ; 0x00549570
      ; object missing → 1; object in another act → 2; player not near (0x00548EF0) → that code;
      ; level 0 → 0 (no travel); level ≥ levels count or bit clear → 2 / 3
  if r != 0: return r
  WaypointTravel(objectId, level)
WaypointTravel (0x00584F60)                                                                  [I]
  object's OperateFn slot must be WaypointOperate; target ≠ current level and ≠ 0; bit of target set
  type = 13 if LevelIsTown(target) or target in {46, 74, 133, 134, 135, 136} else 0
  PlayerChangeLevel(target, type)
  if the player's new room is the room of the target's type point: walk command, message 0x1072 (presentation)
  WaypointArrivalAdd(player's room)                  ; § 2
```

- [I] The 10 000 ms gate reads `GetTickCount`, real time, against player data `+0x160`, written only by
  `0x0055B720` (called from `0x005A5E50`, which also closes the player's portal). It is not in game frames, so Phase 2
  logs it as an input. (0x0054C5DE–0x0054C5F0, 0x0055B76B)

### 4. Placement: `PlayerChangeLevel`, `PlayerChangeAct`, `ActLevelSpot`

```text
PlayerChangeLevel(level, type) (0x0053AEC0)                                                  [I]
  if act(level) != player's act: TownLevelLeave(old, level); PlayerChangeAct(level, type); return
  room = ActLevelSpot(act, level, type, &x, &y, UnitSizeX(player))
  if room: UnitTeleport(room, x, y, noSearch 0, 0)     ; a second free search from (x, y): returns at once
PlayerChangeAct(level, type) (0x0053ACC0)                                                    [I]
  create the act if absent (sub_0053AC70_ActCreate)
  room = ActLevelSpot(act, level, type, &x, &y, size)
  room = COLL_FindFreeNear(room, (x, y), size, mask 0x1C89, radius 50, step 5)   ; 0x0064E7E0
  move the unit between acts, CLIENT_SetAct, unit act byte, path flags 0x10000
ActLevelSpot(act, level, type, &x, &y, size) (0x0061B060)                                    [I]
  room = LevelPointFind(level, type, &tx, &ty)       ; drlg/0005 § 9: Position ≠ 0 → LevelPointPick (one level-seed
                                                     ;   step when a point matches) unless type 13; else waypoint room,
                                                     ;   entry-warp room (0x0066B1F0), middle room, room by RangeB(level seed)
  (x, y) = TileToSubtile(tx, ty) + 3
  room = COLL_FindFreeNear(room, (x, y), 0, size, 0x1C09, 0x1C09, fallback 0, 50, 1); fatal if none
```

- [C] (from drlg/0005, run:2026-10-14-collision) `LevelPointFind` ensures and inits the level, picks a point and
  activates the point's room (`RoomActivateB`); on a `Position` level the type-11 lookup steps the level seed once.
  Here it is also reached with types 0, 5 and 13; type 13 on a `Position` level goes to `LevelWaypointRoom` (no
  draw), every other type to `LevelPointPick` (one draw when at least one point of that type or group exists). This
  extension is `[I]`. (fn:sub_0066B2B0_LevelPointFind@0x0066B2B0, fn:sub_0066AC40_LevelPointPick@0x0066AC40)
- [I] `Position` levels (data): 1, 38, 40, 46, 54, 73, 74, 75, 102, 103, 109, 121, 125, 126, 127, 132, 134, 135.
  (tbl:Levels.txt:Position)
- [I] On a level without `Position`, `LevelPointFind` ignores the type: the waypoint room, else the first DRLG room
  with a warp flag whose warp id is set (`0x0066B1F0`), else the room holding the level's middle column, else
  `0x0066AE70` (`RangeB(level seed, level+0x08)`); the point is the room's centre when none was given.
  (fn:sub_0066B2B0_LevelPointFind@0x0066B2B0 0x0066B2FB–0x0066B370, 0x0066AE70)

**The free-cell search.** `COLL_FindFreeNear(room, pos, other, size, maskA, maskB, fallback, radius, step)` (no draw):

```text
if CollisionTest(room at pos, pos, size, maskA) == 0 (and the second footprint test passes): return that room
best = −1
x0, y0 = pos; xl = xh = x0; yl = y0 − 1; yh = y0 + 1; w = 2
while (xh − x0 + 1) < radius:
    for y = yl to yh by step:                 ; the two side columns, left then right
        for x = xl − 1 to xh + 1 by w:
            if free(x, y) and (|x − x0| + |y − y0| < best or best = −1): pos = (x, y); best = that
    for x = xl to xh by step:                 ; the two end rows, top then bottom
        for y = yl to yh by w:
            if free(x, y) and (… < best …): pos = (x, y); best = …
    if best ≠ −1: break
    xl −= step; xh += step; yl −= step; yh += step; w += 2·step
if best = −1 and fallback = 0: return 0   ; else the room at pos (pos unchanged when nothing was found)
```

- [I] Read from the decompile of `0x0064DEA0`; the loop bounds and the strict `<` (the first cell found wins a tie)
  are as written, the Manhattan distance is `|dx| + |dy|`. (fn:COLL_FindFreeNear@0x0064DEA0 0x0064DF6B–0x0064E1F7)
- [I] Masks and steps used by travel: player placement `0x1C09` step 1; act change a second search `0x1C89` step 5;
  portal field end `0x3E01`/`0xC01` with the partner footprint, size 3, no fallback; portal town end `0xBE11` step 5.
  (fn:sub_0061B060_ActLevelSpot@0x0061B060, fn:COLL_FindFreeNear@0x0064DEA0, 0x005BE290)

### 5. Act change through an NPC

```text
NPC_MenuAction(action, npcId, arg), action ∉ {1, 2, 3}, by NPC class:             [I] (0x0057A650–0x0057A7D6)
  155: if word 6 bit 0: NpcTravelMove(40, 0); NpcActTravel(npc); WAYPOINT_Set(index of 40)
  175: NpcTravelMove(1, 5)
  210: if action == 0 and word 14 bit 0: NpcTravelMove(75, 0); NpcActTravel(npc); WAYPOINT_Set(index of 75)
  264: if action == 0: NpcTravelMove(40, 5)
  367: if action == 0 and expansion and word 26 bit 0: NpcTravelMove(109, 0); NpcActTravel(npc); WAYPOINT_Set(index of 109)
  520: if action == 0: NpcTravelMove(103, 5)
NpcTravelMove(level, type) (0x0054B830)
  level == 0 → PlayerChangeLevel(ActTownLevel(player's act), type)
  same act → PortalObjectCreate(class 59, player x − 5, y, level)
  else → PlayerChangeLevel(level, type)
```

- [I] `NpcActTravel` (read in [save/0002 § 2](../save/0002-quest-words.md#2-who-writes-the-act-travel-words)) sets the
  travel word (7, 15 with 10, 28) with bits 0 and 13 only if bit 0 was clear, sends the record and the NPC flags of the
  new act (`0x00544FA0`), and, on that branch only (each branch tests bit 0 first and exits when it is set: word 7
  `0x00546991`, the branch Phase 2 ran, § 12; word 15 `0x005468E4` and word 28 `0x0054684A` read, not run), sets
  player data `+0x4C` = 1, which blocks operates and waypoint menus until the client's
  packet 0x48 clears it (§ 9). For NPC 155 it also runs quest 6's event-3 callback when word 6 bits 13 and 0 are set, and
  `0x00597310` (the Act I "Cain not rescued" mark, quests/0001). It does **not** move the player: the move has already
  happened in `NpcTravelMove`. (fn:sub_005467E0_NpcActTravel@0x005467E0)
- [C] **Tyrael's travel is the red portal, not the menu** (part 3 correction, run:2026-10-19-quests3, § 14): the stock
  client's menu for NPC 367 in an expansion game after Diablo (word 26 b0) has only *talk* and *cancel* (screenshot
  `workspace/logs/quests/dev-p42r-tyrael-menu.png`), so the 367 branch above is not reached by stock play in that state (like packet 0x58 on word 33; that no stock state
  offers the line is `[I]`, the client's menu builder not read: architect review). The Act
  IV → V travel is the operate of the Harrogath portal (object 566, `0x005B5880`, made by Tyrael's 0x4E20 talk, quests/0001
  § 10): expansion only (`game +0x70`), word 26 b0 or b13 (else message 0x13 to the player), the player in Act IV; with
  word 28 b0 clear it sets word 28 b0 then b13 (0x005B590F, 0x005B5919), sends the record and sets player data `+0x4C`
  = 1 (0x005B5960, `0x0053D940`), and in every case `NpcTravelMove(109, 5)` (0x005B598F) and `0x005B4FF0` (the
  waypoint record). The run: x-tyrael3, five trips (§ 14). (0x005B5880–0x005B59A5)
- [I] **Meshif's Act III menu** (part 3, run:2026-10-19-quests3): *talk*, *sail west*, *cancel* (no trade line; part 2's
  driver clicked *cancel*). A screenshot of the client, whose menu builder was not read, so `[I]` (Phase 3 review); the
  *sail west* line's server side is § 14's `[C]`. (fn:NPC_MenuAction@0x00579D60, screenshot
  `workspace/logs/quests/dev-p42r-meshif-menu.png`)
- [I] The NPC classes are `monstats` rows; their names (Warriv, Meshif, Tyrael, …) are `[L]`.
  (fn:sub_005467E0_NpcActTravel@0x005467E0)
- [I] `TownLevelLeave(old, new)` marks the old town's store stale (vendors) and, on arrival in town 1, 40, 75 or 109,
  sends that act's NPC quest flags (`0x00545100`, lists at `0x007318B0`…); arrival in 40 also runs `0x00597310`.
  (fn:sub_00537340_TownLevelLeave@0x00537340)

### 6. Town portals

```text
ITEMUSE_TownPortal (g_ItemUseFns[2].use, 0x005BE290)                                         [I]
  player only; unit +0xC4 |= 0x40
  town = ActTownLevel(act of the player's level)
  if RoomIsTown(room) or level == 136: refuse
  PlayerPortalClose(player)                                ; the previous pair, if class 59
  ok = PortalObjectCreate(room, x, y, town, &field, class 59, noSearch 0)
  if ok: PlayerPortalSet(field); summit hooks 0x0058CF00 for both ends (level 120 only)
PortalObjectCreate(room, x, y, dest, &out, class, noSearch) (0x0056D130)                    [I]
  if player given and RoomIsTown(room) and not (class 60 and dest in {39, 133..136}): refuse
  act(dest) must equal act(room level), else fatal
  unless noSearch: COLL_FindFreeNear(room, (x, y), (x, y), 3, 0x3E01, 0xC01, 0) else (x, y) as given
  field = SUnitCreate(object, class, x, y)                 ; game-seed draw
  SetMode(field, 1)                                        ; class 59: Sync 0 → RangeB(field seed, 25)
  partner = PortalPartnerCreate(field, dest, room level)
  flags |= 3; pin the rooms of both ends (RoomPinSet(room, 0))
PortalPartnerCreate(field, dest, src) (0x0056CF40)
  room = ActLevelSpot(act(dest), dest, type 11, &x, &y, 3)  ; LevelPointPick: dest's level seed when Position
  RoomUpdateOne(room)
  if src == 73 and QUESTS_PortalTownSpot(...):        ; 0x0059DFD0: an Act II quest's private +0x3C = 1 →
      room, (x, y) = ActLevelSpot(Act II, 40, type 12, size 3), then a step-7 search, mask 0xBE11
  room = COLL_FindFreeNear(room, (x, y), 3, 0xBE11, 50, step 5); else ActLevelSpot again
  partner = SUnitCreate(object, class of field, x, y)      ; game-seed draw
  partner data +4 = src; flags |= 3; SetMode(partner, 2)   ; class 59: RangeB(partner seed, 25)
  link field ↔ partner
```

```text
OBJOP_Portal (OperateFn 15, 0x00584870)                                                      [I]
  refuse if PlayerIsBusy
  if 0x00535B10(operator) ≠ 0 and the owner (0x00552B10) is not the operator: refuse   ; operator hostile to anyone
  if GetTickCount() < PlayerTickGet(operator, 0) + 5000: refuse   ; EDX = 0 at 0x005848BA: the operator's own +0x160
  if an owner exists (0x00552B10 ≠ −1) and is not the operator:     ; 0x005848EB–0x00584908
      if PartyId(operator) = 0xFFFF: refuse                            ; 0x00554630, 16-bit, 0x00584911
      owner = GameFindUnit(game, owner id, player) (0x00552F60)
      if owner found and PartyId(owner) ≠ PartyId(operator): refuse   ; 0x0058493A; no owner unit: no test
  partner = PortalPartnerGet(object) (objects only)
  dest = object data +4; def = LevelDefs[dest]
  if class 59 and object ≠ own portal and a partner exists and partner ≠ own portal:
      q = def.QuestFlagEx if expansion else def.QuestFlag
      if q > 0 and word q bit 0 clear: refuse
  target = partner's position and room, or (no partner) ActLevelSpot(act(dest), dest, 0, &x, &y, 3)
  object flags |= 5
  if RoomIsTown(the operator's room): raise quest event 3 (new level, operator)
  room = COLL_FindFreeNear(target room, target, size, 0x1C09, 0)   ; 0x0064E7B0
  if room is null: return 0                                       ; 0x00584B18, no refusal call (0x00553380)
  UnitTeleport(room, x, y, 0, 0)
  walk command to (x + 5, y + 5)
  if no partner or class 60: (mode 1) queue object event 1
  elif PlayerPortalGet(operator) == partner id:            ; the owner, through the town end
      free the object and the partner, unpin their rooms (RoomPinSet(room, 1)), summit hook 0x0058CF50
  timed state 102 on the operator for 75 frames (event 12 at frame + 75)
```

- [C] **The party test, raised in part** (MP26, two clients): on the host's town portal, the joiner in no party was
  refused after passing the 5 s gate, with the host also in no party (equal ids, so the `0xFFFF` test refused), and in
  the host's party it passed and arrived in level 3; one click each, outcome only, the test itself unlogged. The
  different-ids compare and the no-owner-unit pass stay `[I]`. (fn:OBJOP_Portal@0x00584870 0x00584911 0x0058493A,
  run:2026-10-20-two-clients)
- [I] The quest gate reads leveldefs `+0x00` (`QuestFlag`) or `+0x04` (`QuestFlagEx`) of the portal's destination
  (0x005849BB–0x005849C5, 0x00584A03–0x00584A19). The stock values: 39 (cow level) 26 / 40; 46, 66–73 13; 50–54, 74
  11; 100–102 21; 128–132 39. So another player's portal to the Durance needs word 21 bit 0, to the Arcane or the
  palace word 11, and so on. The owner and anyone using the owner's own end are not tested. (tbl:Levels.txt:QuestFlag,
  tbl:Levels.txt:QuestFlagEx)
- [I] **Closing.** The pair is freed when (a) the owner goes through the town end; (b) the owner opens a new portal
  (`PlayerPortalClose` at the start of `ITEMUSE_TownPortal`); (c) the owner unit is freed (`sub_00555600_UnitFree`
  calls `PlayerPortalClose`); (d) `0x005A5E50` runs (it also sets the declarer's `+0x160`, which both real-time gates read). Class 60
  portals are never closed by these paths. (0x00535430 callers: 0x005BE2FD, 0x00555674, 0x005A5F65, 0x0058D2F3)
- [I] A portal from Duriel's lair (73) puts its town end at level 40's point type 12 (step-7 free search, mask `0xBE11`)
  when an Act II quest object's private byte `+0x3C` is 1 (`0x0059DFD0`, through `QUESTS_PortalTownSpot`); quests/0001
  § 8. (0x00545830, 0x0059DFD0)
- [I] **Permanent portals (class 60).** `OBJINIT_Portal` (`InitFn` 12) sets the destination byte from the level it
  stands on: 1 ↔ 39, 4 ↔ 38, 46 ↔ 74, 109 ↔ 121, 111 ↔ 125, 112 ↔ 126, 117 ↔ 127, the true tomb (`act+0x094`, via
  `0x0061AEB0`) → 73 and 73 → the true tomb; for 111, 112, 117 a changed byte queues object event 11. They are created
  by `CUBE_CowPortalOpen`, the quest scripts (quests/0001) and `0x005A9930`. (fn:OBJINIT_Portal@0x0054FE70)
- [I] Other travel objects: `OperateFn` 43 (`0x00584D00`): class 100 → level 73, class 377 → its object byte, type 0,
  no quest test; `OperateFn` 34 (`0x005846B0`): from 74 to 54 at type 0, from 54 to 74 at type 11, then `0x0059BAF0`
  (Act II quest code). Both set mode 1 and queue event 1 when the object is in mode 0. (0x00584D00, 0x005846B0)

- [C] **The town refusal** (part 3, run:2026-10-19-quests3, § 14): a tome used in the Rogue Encampment or Harrogath
  returns at the town test (0x005BE2E2 → 0x005BE3CE) with no portal and no draw. The level-136 refusal stays `[I]`.
  (0x005BE2DB–0x005BE2E2)

### 7. Warps

```text
UnitInteract case 5 (0x00548B00): warp unit within distance 5 → WarpExitPos(warp)           [I]
WarpExitPos(warp) (0x005550B0)
  dest = UnitWarpDestRoom(room, warp class) → the paired warp unit
  (x, y) = its subtile position; room = COLL_FindFreeNear(dest room, (x, y), size, 0x1C09, fallback 1)
  if dest level in {73, 100, 118, 128, 132} and QUESTS_WarpGate(src level, dest level) ≠ 0: refuse
  UnitTeleport(room, x, y, 0, 0); walk command to (x + ExitWalkX, y + ExitWalkY)
QUESTS_WarpGate(src, dest) (0x00545B80)
  73 → 0x0059DB20; 100 → 0x005BBFA0; 118 or 128 with src 120 → 0x0058D090(dest); 132 → 0x0058E640; else 0
```

- [I] The paired warp, `ExitWalkX/Y` and the room are [drlg/0007](../drlg/0007-warps.md)'s; the gates are read in
  quests/0001 (Acts II, III, V). (fn:sub_005550B0_WarpExitPos@0x005550B0, tbl:LvlWarp.txt:ExitWalkX, tbl:LvlWarp.txt:ExitWalkY)
- [I] **The walk command.** `sub_005809D0_PlayerModeCmd(0, 2, x, y, 0)` (after a warp, a waypoint arrival, a portal
  use) first calls `0x0057EEC0`, which, for a player in state 42 whose current skill has Skills flag byte `+7` bit 7,
  draws `Range(player seed, 100)` against stat 164 of that state's list. Otherwise no draw. (0x0057EF6D–0x0057EF7C)

### 8. Death, resurrection and joining

- [C] **Raised in part** (part 3, run:2026-10-19-quests3, § 14): three resurrections (h-death3, Hell) each moved the
  player to level 1 by `PlayerChangeLevel(1, type 0)` with one step of the town's level seed, chained from one death to
  the next, and no game, quest or player seed draw across the handler; the life, mana and state writes were not logged
  and stay `[I]`. (0x0054C0E0)
- [I] Packet `0x41` with the player in mode 17: life, mana, stamina to their maxima, unit `+0xC4 |= 2`, state 54 set
  and cleared, `PlayerChangeLevel(ActTownLevel(act of the player's level), type 0)`, a mode command, the skills
  re-selected. Type 0 in a town (all `Position` levels) draws the town's level seed. (0x0054C0E0)
- [I] Joining (`0x005394A0`, second argument 0): level `act+0x08` of the player's act (`0x0061AE80`), type 0,
  `ActLevelSpot`; a hireling of the player is created there (`MERC_Create`) or, if it exists, moved to the town's type-0
  spot. With a given position (second argument ≠ 0) the player is put there. (0x005394A0 0x005394E2–0x00539530,
  0x00539653–0x005396A0)

### 9. Act-change state and real-time gates

- [I] Player data `+0x4C` = 1 is set by `NpcActTravel`, `DuranceActTravel` and the Act IV/V quest code that calls
  `0x0053D940` (`0x005B5880`, `0x0058E740`). While it is set, `OBJ_OperateDispatch` and `PlayerIsBusy` refuse.
- [I] **The clear** (plan 0042 P1 review follow-up (c), `lane/rbs2`) is the client's packet **0x48**. Its
  `g_SrvPacketTable` entry (0x006E0D18 + 8·0x48 = 0x006E0F58) is `0x0054C590`, next to packet 0x49's `0x0054C5D0`.
  The handler returns 3 unless its second argument is 1, and returns 2 when player data `+0x4C` is already 0.
  Otherwise it calls `0x005350B0` and returns 0. `0x005350B0` fetches the player data (`0x006221A0`), stops the game
  with error 0x1C7 if `+0x4C` is 0, and writes `+0x4C` = 0 (`movl $0x0,0x4c(%eax)` at 0x005350DB). `0x005350B0` has
  one direct caller (`grep -cE '(call|jmp) +0x5350b0$'`: 1, at 0x0054C5BE). Other writers of `+0x4C` were not
  listed (the offset is common: `grep -cE 'mov[lb]? +\$0x[01],0x4c\(%e[a-z]{2}\)$'` finds 26 immediate 0/1 stores to some
  `0x4c(%reg)` in `.text`). What the client sends
  0x48 after is not read here; the act-loaded reading of the old open question stays a lead.
  (fn:sub_0054C590_Pkt48ActChangeClear@0x0054C590, fn:sub_005350B0_PlayerActChangeClear@0x005350B0,
  data:g_SrvPacketTable@0x006E0D18)
- [I] Two gates use `GetTickCount` (wall-clock milliseconds), not the game frame: waypoint travel (10 000) and portal
  use (5000). Both read the operator's own player data `+0x160` (`PlayerTickGet(player, 0)`: EDX = 0 at 0x0054C5F5
  and 0x005848BA); the per-player entries of list `+0x38` hold the 60 s hostility stamp of each pair, which only
  the declaration reads. No portal is exempt, the operator's own included. (Corrected at the plan 0044 Phase 1
  review, 2026-10-17: this section read a per-owner entry and an exempt own portal.) (0x0055B6C0–0x0055B715,
  0x0054C5F5–0x0054C612, 0x005848BA–0x005848CF)

### 10. Event kinds: inputs, outputs, draws and chaining

| Event | Inputs (log) | Outputs | Draws, in order | Chaining |
|---|---|---|---|---|
| waypoint operate | player, object, mode, level | record bit; mode 0→1 + event 1, or menu | rows 429, 494, 496, 511, 539 only: `RangeB(object seed, FrameDelta[mode] >> 3)` per mode change | the object's own seed: chained across its mode changes |
| waypoint travel | packet, tick stamp, record | new level, position | target level seed (1 step) if `Position` and type ≠ 13; level/room build if absent (oracle) | per level seed, with every other user of it (drlg/0005) |
| NPC act change | NPC class, action, words 6/14/26, expansion | position, words, waypoint bit, `+0x4C` | destination town's level seed (1 step, type 0 or 5); act creation if absent (oracle) | per level seed |
| Durance portal | words 22, 23, 18, level | words, waypoint 103, position | 103's level seed (1 step) | per level seed |
| town portal open | player position, act | two objects, `+0x48` | game seed, town level seed (type 11), game seed (Phase 2: no object-seed draw, § 12) | game seed: with every unit creation; level seed: per town |
| portal use | owner, tick, partner, words | position, state 102, maybe frees the pair | none of its own; room activation (oracle) | — |
| warp | warp unit, paired warp, quest gates | position, walk | none (state-42 case aside) | — |
| death, join | act | position | town level seed (1 step) | per level seed |

- [I] **ADR-0014 chaining.** The draws that chain are the destination level seed (one step per placement on a
  `Position` level, shared with the waypoint lookups of the population pass) and the game seed (portal creation, shared
  with every server unit). A reimplementation that models travel must assert both on entry, as drlg/0005's R1 did for
  the level seed. (fn:sub_0066AC40_LevelPointPick@0x0066AC40, fn:sub_0056D130_PortalObjectCreate@0x0056D130,
  fn:sub_00555230_SUnitCreate@0x00555230)

### 11. Boundary recommendation for Phase 2 (travel)

- Event entry points: `WaypointOperate`, `Pkt49WaypointTravel`, `NPC_MenuAction`'s travel branch, `ITEMUSE_TownPortal`,
  `OBJOP_Portal`, `WarpExitPos`, `Pkt41Resurrect`, `PlayerPlaceInAct`, `DurancePortalOperate`, the other portal
  operates.
- Inputs: the clicks and packets, `GetTickCount` at the two gates, the quest words read, the act and level creation
  (DRLG oracle), room activation and population (lifecycle oracle).
- Model: `ActLevelSpot` and `COLL_FindFreeNear` from a logged collision snapshot (drlg/collision boundary B), the
  point-type rules, the level-seed step, the portal pair's draws, the closing rules.
- Oracles: the collision grid at the search (logged), `UNIT_AnimInit`'s `FrameDelta` (data).

### 12. Phase 2 (run:2026-10-17-quests)

The run ([experiments](experiments.md#run2026-10-17-quests)) logged every travel event at its entry and exit with
the game seed, the quest seed and the player's unit seed, the level-point lookups with the level's seed and points,
the free-cell searches with the collision cells around them, the portal pair's seeds and both real-time gates, and
checked them with `tools/quests.py check`: **0 mismatches over 16 199 checks** in 11 sessions (expansion
Normal and Nightmare, classic Normal and Nightmare, on slots 1 and 2; no Hell session; one client).

| Claim (section) | Run | Result |
|---|---|---|
| `LevelPointPick` steps the level seed once when a point of the type or its group exists, on a `Position` level (§ 4) | type 0: 22 lookups, type 11: 334; 343 chained pairs of one level's seed | **raised** `[C]`: each one step, the point the `k`-th match (`r mod n` or `r & (n − 1)`, then the `k`-th of the matching points); the group table `0x006EED88` (`{has, group}`: type 0 group 0, types 5–9 group 1, type 11 none) (run:2026-10-17-quests) |
| type 13 on a `Position` level draws nothing (§ 3, § 4) | 28 waypoint arrivals in towns and on 46, 74 | **raised** `[C]` (run:2026-10-17-quests) |
| type 5 (NPC 175's return to level 1) | 11 lookups on level 1 | **raised** `[C]` as a no-draw case: level 1 holds no point of group 1, so `LevelPointPick` takes point 0 with no draw (0x0066AC90 `je` to the `n = 0` branch). A type-5 lookup that finds a point (one step) was not reached (Meshif's return to 40 is the planned case; § 12 shortfalls) (run:2026-10-17-quests) |
| a non-`Position` level draws nothing in `LevelPointFind` (§ 4) | 1958 lookups (waypoint arrivals, `NearWarpTest`'s type-11 lookups through `0x00619E50`) | **raised** `[C]` for the waypoint-room, warp-room and middle-room branches the run reached; the `RangeB` fallback (`0x0066AE70`) never ran (run:2026-10-17-quests) |
| **the town portal draws five times** (§ 6, § 10) | 62 portals opened | **corrected**: three draws. Game seed (the field end's `SUnitCreate`), the town's level seed (`LevelPointPick` type 11), game seed (the partner's `SUnitCreate`). Both ends come out of `SUnitCreate` already in their mode (field 1, partner 2: PU `omode`), with unit seed exactly `Init(game seed low)`, so neither the creation nor the following `SetMode` draws on the object's seed. `UNIT_SetMode` changes nothing and draws nothing when the mode is unchanged (`0x006246A9` `je 0x006246D4`). When the town end's room is first updated (`RoomUpdateOne`, 0x0056CF7D, after the type-11 `ActLevelSpot` at 0x0056CF6E), its population draws on the game seed between the two creations (41 draws in 9 of the opens): a boundary oracle (plan 0040's population) whose entry is the asserted field-end state and whose exit is logged at 0x0056CF82 by logger revisions B and C (4 opens). In the 5 opens with population draws in the revision-A logs (x-lut 3, c-tp 2) that exit was not logged and the checker derives it from the partner's seed, so those 5 do not test the partner's draw; the three-draw `[C]` rests on the other 57 opens (53 with no population draw, 4 with the oracle exit logged). The open is a one-shot function (ADR-0017): its entry seed is the input and every draw is asserted to its exit, so ADR-0014's chaining floor does not apply to it (architect review, plan 0042 P2 part 1). `[C]` (run:2026-10-17-quests) |
| refusal in a town and on 136 (§ 6) | none in the recorded sessions | not reached (the town uses ran in development logs only); stays `[I]` (run:2026-10-17-quests) |
| portal use: no draw of its own; owner through the town end frees both (§ 6) | 122 uses, 122 gate reads | **raised** `[C]` for "no draw": gs, qs, ps unchanged across every use; the pair freed at the owner's town-end use is seen as the next open creating a new pair; the field end of a still-open pair is not re-checked (not modelled) (run:2026-10-17-quests) |
| both real-time gates read `GetTickCount` against the operator's own stamp (§ 3, § 9) | 61 packet-0x49 gates, 122 portal gates | **raised** `[C]` for one client: the stamp is 0 in every read (no declaration ran), the gate passes, and `pass = (stamp + 10000 or 5000) <= tick` (unsigned) on every line. A non-zero stamp is plan 0044's (run:2026-10-17-quests) |
| waypoint operate: the record bit set on every operate (§ 2) | 61 operates | **raised** `[C]` for operates of waypoints already in mode 2 (all 61: the saves hold their waypoints, so every logged waypoint was created in mode 2); no draw on gs, qs, ps or the object's seed. The mode-0 activation (mode 0 → 1, event 1, the `Sync` 0 draw) was not reached: every waypoint met was already in mode 2, and the walk of session x-wpnew to the Spider Forest waypoint did not get there (run:2026-10-17-quests) |
| waypoint travel: no quest test, no draw but the destination's level seed (§ 3) | 61 travels | **raised** `[C]`: gs, qs, ps unchanged; the destination lookups as in the rows above (run:2026-10-17-quests) |
| NPC act change: moved before the words; word 7 bits 0 and 13 only when bit 0 was clear; `+0x4C` = 1 (§ 5) | 22 Warriv trips (11 east, 11 west) | **raised** `[C]` for the move-then-write order and the word; **narrowed**: `+0x4C` is set only on the branch that writes the word (word 7: `0x00546991` exits to the word-6 test at `0x005469E4` when bit 0 is set, before the `+0x4C` write at `0x005469CD`), so 10 of the 11 eastward trips left it 0 and sent no packet 0x48 (run:2026-10-17-quests) |
| packet 0x48 clears `+0x4C` (§ 9) | 1 | **not raised**: the one logged clear (1 → 0, return 0) holds; one case, kept `[I]` (run:2026-10-17-quests) |
| placement: `ActLevelSpot`'s search, `PlayerChangeAct`'s second search, `UnitTeleport`'s own search returns at once (§ 4) | 124 placements (81 `PlayerChangeLevel`, 32 `PlayerChangeAct`, 11 joins) | **raised** `[C]`: the player ends on the last search's cell every time (run:2026-10-17-quests) |
| `COLL_FindFreeNear`'s ring search (§ 4) | 545 searches inside travel events, 4 of which moved the cell | raised in part `[C]`: the first-cell test and the moved cases agree; the ring order beyond the first ring and the partner-footprint search (the portal's field end, 62) were not separated by the run (no logged search needed a far ring) and stay `[I]` (run:2026-10-17-quests) |
| the summit door on 120 (quests/0001 § 10, `OperateFn` 71, object 564, at the arrival point from 118) | 73 operates: 37 by a creator without word 39 bit 0 (`QuestSummit`), 36 with every quest done (`TravelWpFive`) | **raised** `[C]` as refused: its private "done" byte 0, mode 1 or 2 → message 0x13, the player stays on 120, for both creators (quest 35 active in the first, switched off in the second): the door does not test `+0x09` (0x0058D6A0–0x0058D711). Whether the door or level 120's own warp tiles (WRP rows 82 and 83, logged, never taken) is the way back to 118 is not separated; `QUESTS_WarpGate`'s 118/128 branch never ran and stays `[I]` (run:2026-10-17-quests) |
| warps: no draw (§ 7) | 2 warps | **not raised**: gs, qs, ps unchanged on the 2 warps taken, under the 20-event floor, so "no draw" stays `[I]`; the 150 level entries the plan asks for were not reached (run:2026-10-17-quests) |

**Shortfalls (named).** Waypoint activation from mode 0; 150 waypoint travels (61 reached); 150 warp
entries (2); a type-5 lookup that steps (no group-1 point on the towns the run reached); the walk command's
state-42 draw; death and resurrection (packet 0x41: no death in the run); the portal `QuestFlag` gate, the party gate
and a non-zero stamp (two clients: plan 0044, out of scope here); the Arcane and lair portals, the Durance portal.

### 13. Phase 2 part 2 (run:2026-10-18-quests2)

The completion pass ([experiments](experiments.md#run2026-10-18-quests2); quest half
[quests/0001 § 16](0001-progression.md#16-phase-2-part-2-run2026-10-18-quests2)) logged the travel events as part 1
did (same logger, revision D), on slot 2, one client. `tools/quests.py check` predicts them with the part 1 rules.

| Claim (section) | Run | Result |
|---|---|---|
| warps: no draw (§ 7) | 104 warps (x-warps 100: LvlWarp rows 20 and 21 alternately; x-orb 2; x-summit2 and x-summit3 1 each), 106 with part 1's | **raised** `[C]` for the warps reached: gs, qs and ps unchanged across every `WarpExitPos` call (the sewer-dock pair, LvlWarp rows 20 and 21, 100 times; row 64 into 100; row 76 into 120); the free-cell search after each is predicted as in § 12 (run:2026-10-18-quests2, fn:sub_005550B0_WarpExitPos@0x005550B0) |
| level 120's warp tiles and `QUESTS_WarpGate(120, 118/128)` (§ 7) | x-summit2 (`QuestSummit`) and x-summit3 (`TravelWpFive`): clicks at row 82's place (to 118) and row 83's (to 128) | **not reached**: no click took either tile (no `WarpExitPos` call); the clicks at row 82's place operated the summit door instead (9 and 6 operates, each refused as quests/0001 § 15 has it). The 118/128 branch stays `[I]` for both creators (run:2026-10-18-quests2) |
| the gate into 100 (§ 7) | x-orb: 83 → 100 after the orb broke | held in one case, `[I]` (run:2026-10-18-quests2, fn:sub_005BBFA0_A3Q5_DuranceWarpGate@0x005BBFA0) |
| NPC act change: the travel word set once, `+0x4C` = 1 and packet 0x48 (§ 5, § 9) | x-meshif: Meshif east from `ActThreeMeshif` (word 15 bit 0 clear) | **raised in part** `[C]` for word 15's branch (`0x005468E4`, read in Phase 1, not run before): word 15 set, `+0x4C` = 1, then packet 0x48 clears it (1 → 0, return 0); one case per travel word now for words 7 (part 1) and 15; word 28 (Tyrael) not reached (the scripted Tyrael menu did not travel). Packet 0x48 stays `[I]` (two cases) (run:2026-10-18-quests2, fn:sub_005467E0_NpcActTravel@0x005467E0, fn:sub_0054C590_Pkt48ActChangeClear@0x0054C590) |
| waypoint travel: no quest test, no draw but the destination's level seed (§ 3) | 47 travels (packet 0x49 and `WaypointTravel`), 108 with part 1's 61; 47 operates of waypoints in mode 2 | holds as raised in part 1: gs, qs, ps unchanged, gates passed with stamp 0, the record bit set on every operate, the mode kept; 150 travels not reached (run:2026-10-18-quests2) |
| waypoint activation from mode 0 (§ 2) | x-wpact3 (`TravelWpOne`, no Act III field waypoint): 14 minutes of exploration from the Kurast Docks; the Spider Forest (76) and Great Marsh (77) waypoints were logged in mode 0 (`OBJP`) | **not reached**: the driver crossed from 76 into 77 inside one exploration chunk and could not get next to the Great Marsh waypoint (straight Teleport hops over the marsh), so no operate of a mode-0 waypoint was logged; the activation, event 1 and the `Sync` 0 draw (checked by `ev_wpop` when logged) stay `[I]`; the mode 1 → 2 draw that would make a chained pair is not logged by any revision (run:2026-10-18-quests2, fn:sub_00584E30_WaypointOperate@0x00584E30) |
| death and resurrection (packet 0x41, § 8) | `dev-p42q-x-death-a` only: the 24-life save in the Cold Plains was not killed (the driver read a low life orb as death and pressed Escape) | **not reached**; stays `[I]` (fn:sub_0054C0E0_Pkt41Resurrect@0x0054C0E0) |
| type-5 placement that steps (Meshif's return to 40, § 4) | x-meshif: the westward Meshif menu was not taken by the driver | **not reached**; stays `[I]` (run:2026-10-18-quests2, fn:sub_0061B060_ActLevelSpot@0x0061B060) |

**Shortfalls (named).** 150 waypoint travels (108); 60 activations from mode 0 (none); 150 warp entries (106);
level 120's warp tiles from either creator (the door answers the clicks) and the gates into 73 and 132 (not attempted);
the refusal into 100 (the client offered no warp); `NpcActTravel` 20 events (1 in part 2: Meshif east; Meshif west,
Tyrael's Act IV → V travel and more Warriv trips were not taken by the driver), packet 0x48 on word 28, a type-5 lookup
that steps; death and resurrection; a portal refused in a town and the Durance, Arcane and lair portals (not
attempted); the free-cell search's far rings (named at part 1). Two-client cases stay plan 0044's.

### 14. Phase 2 part 3 (run:2026-10-19-quests3)

The last pass ([experiments](experiments.md#run2026-10-19-quests3); quest half
[quests/0001 § 17](0001-progression.md#17-phase-2-part-3-run2026-10-19-quests3)) logged the travel events with the
part 2 lines (logger revision E adds only quest lines) on slot 2, one client; `tools/quests.py check` predicts them with
the part 1 and 2 rules plus the town-portal refusal in a town.

| Claim (section) | Run | Result |
|---|---|---|
| a town portal refused in a town (§ 6) | the tome used in the Rogue Encampment (x-entry, x-entry2, h-entry) and in Harrogath (x-anya, h-anya, nm-anya): 6 uses | **raised** `[C]`: `ITEMUSE_TownPortal` returns at the town test (0x005BE2E2 → 0x005BE3CE) with no portal created (no `PU` line), the player's portal unchanged and no draw on the game, quest or player seed (run:2026-10-19-quests3, 0x005BE2DB–0x005BE2E2) |
| the type-5 lookup that steps: Meshif's return to 40 (§ 4, § 5) | x-meshifw: six westward trips (NPC 264, `NpcTravelMove(40, 5)`) and six back east (word 15 already set) | **raised** `[C]`: each westward trip's `LevelPointFind(40, type 5)` found a point and stepped Lut Gholein's level seed once, the point picked as `LevelPointPick` predicts, the level seed chained from one trip to the next; no other seed moved; the eastward trips wrote nothing (word 15 already set, `+0x4C` 0) (run:2026-10-19-quests3, fn:sub_0054B830_NpcTravelMove@0x0054B830, 0x0066B2B0) |
| Tyrael's Act IV → V travel, word 28, packet 0x48 (§ 5, § 9) | x-tyrael3 (`ActFiveTyrael`: word 26 b0, word 28 clear): Tyrael talked to (his 0x4E20 makes the portal), then five trips through the red portal (object 566) and back by waypoint | **corrected and raised** `[C]`: the travel is object 566's operate, not the NPC menu (above, § 5); the first trip set word 28 b0 then b13 (0x005B590F, 0x005B5919), `+0x4C` = 1, and the client's packet 0x48 cleared it (1 → 0, return 0); the four later trips wrote nothing and sent no 0x48; every trip's `NpcTravelMove(109, 5)` found no point matching type 5 among Harrogath's points (one, of type 0) and took the first point without a draw (`LevelPointPick`'s n = 0 exit, 0x0066AC90), the level seed unchanged, as part 1's rule predicts. Packet 0x48's clear now has one case per travel word (7 in part 1, 15 in part 2, 28 here): **raised in part** `[C]` for the clear branch; the 20-event floor stays out of this plan (run:2026-10-19-quests3, 0x005B5880–0x005B59A5, fn:sub_0054C590_Pkt48ActChangeClear@0x0054C590) |
| death and resurrection (packet 0x41, § 8) | h-death3: the 24-life save (`QuestDeath`) killed three times in Hell's Cold Plains, Escape each time (x-death3 in Normal: the monsters seldom hit the character, two development logs) | **raised** `[C]` for the branch reached: packet 0x41 with the player dead moves him to the town by `PlayerChangeLevel(1, type 0)`: one step of the town's level seed (type 0, a `Position` level), the free search predicted, the game, quest and player seeds unchanged across the handler, three of three; the life, mana and state-54 writes were not logged (`[I]`) (run:2026-10-19-quests3, fn:sub_0054C0E0_Pkt41Resurrect@0x0054C0E0) |
| waypoint activation from mode 0 (§ 2) | three sessions with a save lacking the act's field waypoints: x-wpact1-0 (`QuestWpAct`, map seed 4322: exploration from the Rogue Encampment, 4 min, the Cold Plains never reached), x-wpactr-0 (the same seed, straight Teleport hops towards the Cold Plains waypoint's place known from an older log of that seed: stopped at a river in the Blood Moor, stopped by hand), x-wpact3r-0 (`TravelWpOne`, map seed 4361: from the Kurast Docks towards the Spider Forest waypoint, Def 581 at (5099, 4769), logged in mode 0 at 110 sub-tiles; the driver ended in a pocket of the jungle with no walking or 8-sub-tile jump path over the logged cells, and walking clicks did not move the player) | **not reached**: no operate of a mode-0 waypoint, so event 1 and the `Sync` 0 draw stay `[I]`. What the logs show about `InitFn` 17's creation mode, without a raise: over the 45 part 1–3 logs, a field waypoint first seen after a waypoint arrival in its level was in mode 1 (87) or already 2 (8, seen after its event 1), and one first seen with no arrival was in mode 0 (4) (`tools/quests.py wpmodes`, output `workspace/logs/quests/2026-10-19-quests3-wpmodes.txt`; the `OBJP` lines are periodic, so first seen is not the creation, and the reading stays `[I]`; run:2026-10-19-quests3, fn:OBJINIT_Waypoint@0x00547210) |

**Shortfalls (named, final for this plan).** No further pass is planned; these stay `[I]` in this plan. Waypoint
activation from mode 0, its event 1 and the `Sync` 0 object-seed draw (above: the driver reaches no mode-0 waypoint by
a hop or a short walk; the mode 1 → 2 draw is logged by no revision); NPC 367's menu travel branch (the stock client
offers no line); the 150-travel, 150-warp, 60-activation and 20-`NpcActTravel` floors; level 120's warp tiles and the
118/128 branch, the gates into 73, 100 and 132; the Durance, Arcane and lair portals; the level-136 portal refusal; the
resurrection's life, mana and state writes (not logged); the free-cell search's far rings. Two-client cases stay plan
0044's. (run:2026-10-19-quests3)

## Data touched

- `tbl:Levels.txt:Position`, `tbl:Levels.txt:QuestFlag`, `tbl:Levels.txt:QuestFlagEx`, `tbl:Levels.txt:Waypoint`
  (through `WAYPOINT_IndexFromLevel`)
- `tbl:Objects.txt:Sync`, `tbl:Objects.txt:FrameDelta`, `tbl:Objects.txt:OperateFn`, `tbl:Objects.txt:InitFn`
- `tbl:Misc.txt:pSpell` (2 = `tsc`, `tbk`)
- `tbl:LvlWarp.txt:ExitWalkX`, `tbl:LvlWarp.txt:ExitWalkY`
- `struct:PlayerData+0x1C` (waypoint records), `struct:PlayerTravel+0x48` (own portal id), `struct:PlayerTravel+0x4C`
  (act change in progress), `struct:PlayerTravel+0x160` (tick stamp); see `re/types/quests.h`

## Dead ends

- `Levels.Portal` (leveldefs `+0x8C`): none of the 28 `sub_0061E470_LevelDefGet` call sites reads `+0x8C` (the one hit,
  `0x00642B3D`, is the act's `+0x8C`). Its reader, if any, goes through `g_pLevelDefs` directly; not found.
- `FUN_0053FDF0` (the point type of the resurrection) returns 0 unconditionally.

## Open questions

- ~~Where player data `+0x4C` is cleared~~: packet 0x48's handler, § 9 (`lane/rbs2`). [L] What the client
  sends 0x48 after is still a lead ("act loaded"); Phase 2 can log the packet.
- [L] The un-declare path of `0x005A5E50` (hostile = 0, 0x005A5FA4) and what the table at `0x006E2228` dispatches;
  the declaring path is read in multiplayer/0001 § 4. Multiplayer, plan 0044 MP24.
- [L] The exact distance metrics of the operate (`0x00641530` < 51, `0x00623660`) and the warp click (< 5) were not
  read; Phase 2 logs the distances.
- [L] The `Levels.Portal` and `Levels.Teleport` columns: no server reader found for `Portal`; `Teleport` is the skill's.
- ~~`UNIT_AnimInit`'s draw for the portal pair at `SUnitCreate` time~~: answered by the run (§ 12): no draw at
  creation, the ends created in their modes, no draw at the `SetMode` either.
