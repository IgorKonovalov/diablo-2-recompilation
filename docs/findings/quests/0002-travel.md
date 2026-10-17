# 0002 — Travel: waypoints, act changes, town portals, warps and where a player is placed

> **Subsystem:** quests/travel
> **Question:** how does a player activate and use a waypoint, change act, open and use a town portal, and where is a
> player placed on entering a level (by waypoint, NPC, portal, warp, death or joining), with which draws?
> **Date:** 2026-10-17   **Plan:** 0042 (Phase 1 and 1b, static)   **Status:** open (Phase 2 runs the reproduction)

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
  is set); NPCs 175, 264 and 520 go back to levels 1, 40 and 103 at point type 5 with no test (row names `warriv2`,
  `meshif2`, `cain6`, `[L]` as identities). The player is moved
  **before** the words are written. (fn:NPC_MenuAction@0x00579D60 0x0057A650–0x0057A7D6, 0x0054B830,
  fn:sub_005467E0_NpcActTravel@0x005467E0)
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
  point), moved by a step-5 free search (`mask 0xBE11`). Draws, in order: game seed (field portal's unit seed), field
  portal's unit seed (`Sync` 0, mode 1), the town's level seed (`LevelPointPick`), game seed (partner), partner's unit
  seed (mode 2). (0x005BE290, fn:sub_0056D130_PortalObjectCreate@0x0056D130, 0x0056CF40, 0x00535430,
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
  creation: five (above); portal use: none of its own (a room activation is an oracle); warp: none.

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
  Detail: the owner and the operator must have the same party id; the owner's own portal is exempt (§ 6).
- [L] src:arreat-summit-basics-travel: going hostile closes the player's portal. **held with refinement**
  Detail: `0x005A5E50` closes it and writes the tick stamp; that it is the hostility declaration is a lead (open
  question).
- [L] src:arreat-summit-basics-travel: a hostile player cannot use other players' portals. **not covered**
  Detail: no hostility test was found in `OBJOP_Portal`; the party test may be what enforces it.
- [L] src:arreat-summit-basics-travel: a 10-second delay separates a hostility declaration from leaving town by
  waypoint or portal. **held** for waypoints (10 000 ms, § 3), **contradicted** for portals: the portal gate waits
  5000 ms (`0x00584870`). Multiplayer only, not reachable with one client; backlog entry 2026-10-17 (plan 0044).
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
  new act (`0x00544FA0`), and sets player data `+0x4C` = 1, which blocks operates and waypoint menus until cleared (the
  clearing is not read). For NPC 155 it also runs quest 6's event-3 callback when word 6 bits 13 and 0 are set, and
  `0x00597310` (the Act I "Cain not rescued" mark, quests/0001). It does **not** move the player: the move has already
  happened in `NpcTravelMove`. (fn:sub_005467E0_NpcActTravel@0x005467E0)
- [I] The NPC classes are `monstats` rows; their names (Warriv, Meshif, Tyrael, …) are `[L]`.
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
  if 0x00535B10(operator) ≠ 0 and the owner (0x00552B10) is not the operator: refuse
  if GetTickCount() < PlayerTickGet(…) + 5000: refuse        ; 0x0055B6C0, arguments not traced
  if an owner exists and is not the operator: refuse unless both have the same party id (0x00554630)
  partner = PortalPartnerGet(object) (objects only)
  dest = object data +4; def = LevelDefs[dest]
  if class 59 and object ≠ own portal and a partner exists and partner ≠ own portal:
      q = def.QuestFlagEx if expansion else def.QuestFlag
      if q > 0 and word q bit 0 clear: refuse
  target = partner's position and room, or (no partner) ActLevelSpot(act(dest), dest, 0, &x, &y, 3)
  object flags |= 5
  if RoomIsTown(the operator's room): raise quest event 3 (new level, operator)
  room = COLL_FindFreeNear(target room, target, size, 0x1C09, 0); UnitTeleport(room, x, y, 0, 0)
  walk command to (x + 5, y + 5)
  if no partner or class 60: (mode 1) queue object event 1
  elif PlayerPortalGet(operator) == partner id:            ; the owner, through the town end
      free the object and the partner, unpin their rooms (RoomPinSet(room, 1)), summit hook 0x0058CF50
  timed state 102 on the operator for 75 frames (event 12 at frame + 75)
```

- [I] The quest gate reads leveldefs `+0x00` (`QuestFlag`) or `+0x04` (`QuestFlagEx`) of the portal's destination
  (0x005849BB–0x005849C5, 0x00584A03–0x00584A19). The stock values: 39 (cow level) 26 / 40; 46, 66–73 13; 50–54, 74
  11; 100–102 21; 128–132 39. So another player's portal to the Durance needs word 21 bit 0, to the Arcane or the
  palace word 11, and so on. The owner and anyone using the owner's own end are not tested. (tbl:Levels.txt:QuestFlag,
  tbl:Levels.txt:QuestFlagEx)
- [I] **Closing.** The pair is freed when (a) the owner goes through the town end; (b) the owner opens a new portal
  (`PlayerPortalClose` at the start of `ITEMUSE_TownPortal`); (c) the owner unit is freed (`sub_00555600_UnitFree`
  calls `PlayerPortalClose`); (d) `0x005A5E50` runs (it also writes the 10 000 / 5000 ms tick stamp). Class 60
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

- [I] Packet `0x41` with the player in mode 17: life, mana, stamina to their maxima, unit `+0xC4 |= 2`, state 54 set
  and cleared, `PlayerChangeLevel(ActTownLevel(act of the player's level), type 0)`, a mode command, the skills
  re-selected. Type 0 in a town (all `Position` levels) draws the town's level seed. (0x0054C0E0)
- [I] Joining (`0x005394A0`, second argument 0): level `act+0x08` of the player's act (`0x0061AE80`), type 0,
  `ActLevelSpot`; a hireling of the player is created there (`MERC_Create`) or, if it exists, moved to the town's type-0
  spot. With a given position (second argument ≠ 0) the player is put there. (0x005394A0 0x005394E2–0x00539530,
  0x00539653–0x005396A0)

### 9. Act-change state and real-time gates

- [I] Player data `+0x4C` = 1 is set by `NpcActTravel`, `DuranceActTravel` and the Act IV/V quest code that calls
  `0x0053D940` (`0x005B5880`, `0x0058E740`). While it is set, `OBJ_OperateDispatch` and `PlayerIsBusy` refuse. Its clear
  was not found in the code read (open question).
- [I] Two gates use `GetTickCount` (wall-clock milliseconds), not the game frame: waypoint travel (10 000) and portal
  use between players (5000, per-owner entry of player data list `+0x38`). With one player the portal gate compares
  against the entry for that owner only when owner ≠ operator; an own portal is never delayed. (0x0055B6C0)

### 10. Event kinds: inputs, outputs, draws and chaining

| Event | Inputs (log) | Outputs | Draws, in order | Chaining |
|---|---|---|---|---|
| waypoint operate | player, object, mode, level | record bit; mode 0→1 + event 1, or menu | rows 429, 494, 496, 511, 539 only: `RangeB(object seed, FrameDelta[mode] >> 3)` per mode change | the object's own seed: chained across its mode changes |
| waypoint travel | packet, tick stamp, record | new level, position | target level seed (1 step) if `Position` and type ≠ 13; level/room build if absent (oracle) | per level seed, with every other user of it (drlg/0005) |
| NPC act change | NPC class, action, words 6/14/26, expansion | position, words, waypoint bit, `+0x4C` | destination town's level seed (1 step, type 0 or 5); act creation if absent (oracle) | per level seed |
| Durance portal | words 22, 23, 18, level | words, waypoint 103, position | 103's level seed (1 step) | per level seed |
| town portal open | player position, act | two objects, `+0x48` | game seed, field seed (25), town level seed (type 11), game seed, partner seed (25) | game seed: with every unit creation; level seed: per town |
| portal use | owner, tick, partner, words | position, state 102, maybe frees the pair | none of its own; room activation (oracle) | — |
| warp | warp unit, paired warp, quest gates | position, walk | none (state-42 case aside) | — |
| death, join | act | position | town level seed (1 step) | per level seed |

- [I] **ADR-0014 chaining.** The draws that chain are the destination level seed (one step per placement on a
  `Position` level, shared with the waypoint lookups of the population pass) and the game seed (portal creation, shared
  with every server unit). A reimplementation that models travel must assert both on entry, as drlg/0005's R1 did for
  the level seed.

### 11. Boundary recommendation for Phase 2 (travel)

- Event entry points: `WaypointOperate`, `Pkt49WaypointTravel`, `NPC_MenuAction`'s travel branch, `ITEMUSE_TownPortal`,
  `OBJOP_Portal`, `WarpExitPos`, `Pkt41Resurrect`, `PlayerPlaceInAct`, `DurancePortalOperate`, the other portal
  operates.
- Inputs: the clicks and packets, `GetTickCount` at the two gates, the quest words read, the act and level creation
  (DRLG oracle), room activation and population (lifecycle oracle).
- Model: `ActLevelSpot` and `COLL_FindFreeNear` from a logged collision snapshot (drlg/collision boundary B), the
  point-type rules, the level-seed step, the portal pair's draws, the closing rules.
- Oracles: the collision grid at the search (logged), `UNIT_AnimInit`'s `FrameDelta` (data).

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

- [L] Where player data `+0x4C` is cleared after an act change (likely on the client's "act loaded" message); Phase 2
  can log its writes.
- [L] What `0x005A5E50` is (an entry of the table at `0x006E2228`; it writes the tick stamp and closes the portal); the
  hostility declaration is a guess. Multiplayer, plan 0044.
- [L] The exact distance metrics of the operate (`0x00641530` < 51, `0x00623660`) and the warp click (< 5) were not
  read; Phase 2 logs the distances.
- [L] The `Levels.Portal` and `Levels.Teleport` columns: no server reader found for `Portal`; `Teleport` is the skill's.
- [L] `UNIT_AnimInit`'s draw for the portal pair (class 59, `Sync` 0) at `SUnitCreate` time, before the explicit
  `SetMode`: whether object creation itself sets a mode that draws is not read here; Phase 2 asserts the object seeds.
