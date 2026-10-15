---
spec: objects
status: draft
target: Diablo II LoD 1.14d, Game.exe sha256 631066c1649c4ea9…
depends_on: [rng, rng/seeds, data/excel, drlg/preset, drlg/collision]
consumed_by: [monsters/spawn, drlg/collision, items/tc, items/quality]
tags: {C: 120, I: 32, L: 7}
updated: 2026-10-15
---

# Objects: room object population, placement, preset objects, creation rolls and the chest drop

## Purpose

When the server activates a room for the first time it creates the room's objects in three steps: the DS1 preset
objects, the inactive-unit restore (which does nothing on a first activation) and the random object population,
which walks the eight object-group slots of the room's level, picks a group member, and places it with a handler
chosen by the member's `PopulateFn`. Every object created then runs its creation rolls (unit seed, `InitFn`,
`PreOperate`). This spec gives that whole window with its exact draw order on its four seeds: the **room seed**,
the game-wide **object-region seed**, the **game seed** and each object's **unit seed**. It also gives the operate
path of chests and containers up to the call into item creation; the treasure class chosen there and everything after
it belong to [items/tc](../items/tc.md). What a shrine, a well, a trap or any other object *does* is game simulation
(ADR-0002) and is only named. Primitives (`Step`, `Range`, `Init`) are those of [rng](../rng/README.md).

## Entry points

| When | Function | Tag |
|---|---|---|
| Game creation: the object region and its seed (right after the monster regions) | fn:OBJRGN_Create@0x00546C60, called from fn:sub_00530BF0_GameCreate@0x00530BF0 | [C] |
| First activation of a room, in the room driver: presets, restore, objects, then the monster pass | fn:sub_0052D160_NewRoomsUpdate@0x0052D160 | [C] |
| DS1 preset units of the room (objects first, then monsters) | fn:sub_005559A0_RoomPresetUnits@0x005559A0 → fn:sub_005557D0_PresetUnitDispatch@0x005557D0 | [C] |
| DS1 pseudo-objects 574..582 | fn:OBJ_PresetPseudoDispatch@0x0054F490 | [C] |
| Inactive-unit restore (nothing on a first activation; a full re-creation on a revisit) | fn:sub_00542B40_RoomInactiveUnitsRestore@0x00542B40 | [C] |
| Random object population of the room | fn:sub_00552610_RoomObjectsPopulate@0x00552610 | [C] |
| Every object creation | fn:sub_00555230_SUnitCreate@0x00555230 → fn:OBJ_ServerInit@0x0054F5D0 | [C] |
| A player operates an object | fn:OBJ_OperateDispatch@0x00584420 | [C] |
| A chest or container drops (into items/tc) | fn:sub_00585B90_ObjectChestDrop@0x00585B90 → fn:TC_ResolveDrops@0x0055A6D0 | [C] |
| An object timer event runs from the game's event queue | data:g_ObjEventFns@0x006E19B0 | [C] |

- [C] Everything here runs on the server; the room driver calls the window only while the room's flags bit 0 is clear,
  and the monster population pass ([monsters/spawn](../monsters/spawn.md)) follows it.
  (fn:sub_0052D160_NewRoomsUpdate@0x0052D160, run:2026-10-15-objects,
  [objects/0001 § 1](../../findings/objects/0001-object-population.md#1-the-window-and-the-three-seeds))

## Inputs

### Tables

All tables are the compiled `.bin` records, indexed by record position ([data/excel](../data/excel.md)).

| Anchor | Used for |
|---|---|
| tbl:Levels.txt:ObjGrp0, tbl:Levels.txt:ObjPrb0 | u8 × 8 at `+0x0E5` and `+0x0ED` (`..7`): the eight slots, group index and chance (§ D) |
| tbl:Levels.txt:Themes | `+0x210`: the theme roll in the gate (§ C) |
| tbl:Levels.txt:MonLvl1 | u8 `+0x010`, the normal-difficulty column in **every** difficulty: trap and lock chances (§ H) |
| tbl:Levels.txt:Act | `+0x003`: the act of each object-region level record (§ A) |
| tbl:ObjGroup.txt:ID0 | u32 × 8 at `+0x00`: member classes (Objects record indices); the walk stops at the first 0 (§ D) |
| tbl:ObjGroup.txt:PROB0 | u8 × 8 at `+0x28`: cumulative percentages against one draw (§ D) |
| tbl:ObjGroup.txt:DENSITY0 | u8 × 8 at `+0x20`: the count factor passed to the handler; ≥ 128 is fatal (§ D, § E) |
| tbl:Objects.txt:PopulateFn, tbl:Objects.txt:InitFn, tbl:Objects.txt:OperateFn | u8 `+0x1B2`, `+0x1B1`, `+0x1B3`: handler indices (§ E, § H, § J) |
| tbl:Objects.txt:SizeX, tbl:Objects.txt:SizeY | `+0xD0`, `+0xD4`: placement sizes and the mark (§ F, § G) |
| tbl:Objects.txt:SubClass | `+0x167`: read by the forced-slot rule **at the group index** (§ D) |
| tbl:Objects.txt:Gore | `+0x172`: member skip against the gore limit (§ D) |
| tbl:Objects.txt:Orientation | `+0x13C`: the shrine placer (§ F) |
| tbl:Objects.txt:Xspace, tbl:Objects.txt:Yspace | `+0x162`, `+0x163`, read as **u8**: barrel and crate cluster steps (§ E) |
| tbl:Objects.txt:Lockable | `+0x171`: the lock roll of `InitFn` 3 (§ H) |
| tbl:Objects.txt:PreOperate | `+0x13D`: the 1/14 opened roll (§ G) |
| tbl:Objects.txt:Sync, tbl:Objects.txt:FrameDelta0 | `+0x175`, `+0xF8 + mode`: the animation-start draw on the unit seed (§ G) |
| tbl:Objects.txt:Selectable0 | `+0xC4 + mode`: the selectable flag (§ G) |
| tbl:Objects.txt:Parm0, tbl:Objects.txt:Parm1 | s32 `+0x178`, `+0x17C`: shrine class and forced-shrine class (§ E, § H) |
| tbl:Objects.txt:Mode1 | `+0x140`: a chest's mode after operating (§ J) |
| tbl:Shrines.txt:effectclass | u8 `+0xB2`: which pick list a code is in (§ A, § H) |
| tbl:Shrines.txt:LevelMin | u32 `+0xB4`, compared with the Levels **Id** (§ H) |

Not read by any code of this spec: ObjGroup `SHRINES` and `WELLS`, Shrines `rarity`, Objects `SpawnMax`, `TrapProb`,
`Act`. [I] ([objects/0001 § Data touched](../../findings/objects/0001-object-population.md#data-touched),
tbl:ObjGroup.txt:SHRINES, tbl:Shrines.txt:rarity, tbl:Objects.txt:TrapProb)

### Runtime state

| State | Type | Source |
|---|---|---|
| room seed `S` | `Seed` at active room `+0x6C` | [rng/seeds](../rng/seeds.md) step 6c, then the wanderer tick ([monsters/spawn § K](../monsters/spawn.md#k-wanderers-the-tick)) |
| object-region seed `O` | `Seed` at `*(game+0x10F0)` (struct:ObjRgn+0x0) | § A; one stream for the whole game |
| game seed `G` | `Seed` at game `+0xD0` | [rng/seeds](../rng/seeds.md) |
| unit seed | `Seed` at unit `+0x20` | § G |
| level record `L` | `ObjRgnLevel` (0x90 B) per level id, `objrgn+0x48 + 4·id` | § A: `roomsVisited` `+0x04`, `roomCount` `+0x08`, `+0x0C`, `healthShrines` `+0x10`, `nShrinePos` `+0x14`, `nWellPos` `+0x18`, shrine and well positions |
| shrine lists | per `effectclass` 0..7: the Shrines codes in record order (struct:ObjRgn+0x8) | § A |
| room rectangle | `rect = {x, y, w, h}` in subtiles | DRLG |
| object data | `interact` u8 at ObjectData `+0x04` (struct:ObjectData+0x4): shrine code, or trap type (bits 0–6) and locked (bit 7); sparkle flag at unit `+0x78` | § G, § H |
| difficulty, expansion | game | game creation |

### Constants

| Name | Value | Anchor | Tag |
|---|---|---|---|
| slot count | 8 | fn:sub_00552610_RoomObjectsPopulate@0x00552610 | [C] |
| forced-slot threshold | `roomsVisited·128 ÷ roomCount > 96` (signed) | 0x005526CC | [C] |
| gore limit | byte 2, no writer | data:g_ObjGoreLimit@0x00731BBC | [I] |
| placement attempts per placer call | 5 | fn:OBJ_PlaceRandom@0x00550380 | [C] |
| position-test masks | `0x3F11` (box test), `0xC01` (padded box) | fn:OBJ_PosTestPadded@0x00550220 | [C] |
| shrine spacing, well spacing | 50, 100 subtiles on **each** axis | fn:OBJRGN_ShrineDistOk@0x00547430, fn:OBJRGN_WellDistOk@0x005473A0 | [C] |
| shrine cap, well cap per level | 10 (or `> roomCount ÷ 8`), 4 (or `> roomCount ÷ 8`) | fn:OBJRGN_ShrineCapReached@0x00547360, fn:OBJRGN_WellCapReached@0x00547300 | [I] |
| `PreOperate` chance | `Range(O, 14) = 0` | fn:OBJ_ServerInit@0x0054F5D0 | [C] |
| handler tables | `g_ObjInitFns` 80, `g_ObjPopulateFns` 10, `g_ObjOperateFns` 101, `g_ObjTrapFns` 10, `g_ObjPseudoFns` 9 entries | data:g_ObjInitFns@0x00731BC0, data:g_ObjPopulateFns@0x00731D00, data:g_ObjOperateFns@0x00732D18, data:g_ObjTrapFns@0x00732CEC, data:g_ObjPseudoFns@0x00731D28 | [C] |
| eight directions | `dx = −1, 0, 1, −1, 1, −1, 0, 1`, `dy = −1, −1, −1, 0, 0, 1, 1, 1` | data:g_ObjDir8X@0x00731B7C, data:g_ObjDir8Y@0x00731B9C | [C] |

### Inputs and oracles

The reproduction of run:2026-10-15-objects models this whole spec on the four seeds, with the object-region seed
predicted from game creation and carried across every room, operate and timer event; the window RW1 → RW4 of each room
is predicted from its entry, 1265 windows with 0 mismatches in 142 540 checks. The rows below are what it took from the
log ([ADR-0004](../../adrs/0004-boundary-oracles-in-reproduction.md)); a reimplementation supplies them from their
owners. Every `[C]` of this spec holds under these inputs. [C] (run:2026-10-15-objects,
[objects/0001 § 12](../../findings/objects/0001-object-population.md#12-phase-2-the-bit-exact-run))

| Input | Kind | What it holds | Owner | Tag |
|---|---|---|---|---|
| the gate's DRLG parts | value oracle | room flags `0x30000`, `RoomPopLevelId`, the preset test, the town test, `LevelRoomCount` on first read | `drlg/preset`, `drlg/overview` | [C] (fn:OBJ_PopulateGate@0x00552560, run:2026-10-15-objects) |
| `COLL_WHTest` results at the seven object call sites | value oracle | 0 = free; the arguments (room, point, box, mask) are predicted and compared, the result is taken (5767 calls) | [drlg/collision](../drlg/collision.md#inputs-and-oracles) | [C] (fn:COLL_WHTest@0x0064D800, run:2026-10-15-objects) |
| object marks in the collision grid | logged | the marks each created object makes (§ G step 5) are the logged CM lines; they are **not** fed from this model to the collision model yet (architect ruling, plan 0023 Phase 2) | `drlg/collision` | [C] (fn:UNIT_CollMarkRect@0x00620A70, run:2026-10-15-objects) |
| preset monsters of the presets window | seed oracle | `PresetUnitDispatch` of type 1, and the superunique and MonPlace spawns | [monsters/spawn](../monsters/spawn.md), [monsters/special](../monsters/special.md) | [C] (fn:sub_0054E600_PresetMonSpawn@0x0054E600, run:2026-10-15-objects) |
| monster and quest `InitFn`s | seed oracle | `InitFn` 46 (it draws the room, game and object-region seeds inside its monster spawns: 584 object-region draws in 16 calls), 47, 54, 55, 62, 66, 68, 69, Zoo 79, pseudo-object 582 | monsters, quests | [C] (fn:OBJINIT_CityDamnedSpawns@0x005506D0, run:2026-10-15-objects) |
| state `InitFn`s | value oracle | the mode or `interact` value that `InitFn`s without draws set from game state (4, 6, 8, 9, 12, 14, 16, 17, 22, 26 in the run); the unit-seed draw of the mode change is predicted | game state | [C] (data:g_ObjInitFns@0x00731BC0, run:2026-10-15-objects) |
| `TC_ResolveDrops` | seed oracle in the run; modelled by [items/tc](../items/tc.md) | draws the dropping object's **unit seed**; it left the object-region seed alone in all 59 calls | `items/tc` | [C] (fn:TC_ResolveDrops@0x0055A6D0, run:2026-10-15-objects) |
| gold drop of `InitFn` 28, operate monster spawn `0x00582280` | seed oracle | item creation; the spawn draws no object-region draw (2 spawns) | items, monsters | [C] (fn:OBJINIT_GoldPiles@0x0054F8C0, fn:OBJOP_Barrel@0x005868A0, run:2026-10-15-objects) |
| when a player operates which object | input | simulation | game | [C] (fn:OBJ_OperateDispatch@0x00584420, run:2026-10-15-objects) |
| when an object timer event runs | input | simulation (ADR-0002); its draws are modelled (§ K) | game | [C] (data:g_ObjEventFns@0x006E19B0, run:2026-10-15-objects) |
| trap effects | named only | `g_ObjTrapFns[t]` | game simulation | [I] (fn:OBJ_TrapFire@0x00582510) |

## Algorithm

```mermaid
flowchart TD
    gc["GameCreate: MonRegionsInit, game draw 1"] --> rgn["A. OBJRGN_Create, game draw 2<br/>O = Init(low)"]
    win["B. room driver, flags bit 0 clear"] --> pre["RoomPresetUnits: objects, then monsters"]
    pre --> rst["RoomInactiveUnitsRestore: nothing on a first activation"]
    rst --> gate["C. gate and theme roll"]
    gate -->|"open"| slot["D. 8 slots: room draw each,<br/>member pick on a pass"]
    slot --> h["E. PopulateFn handler"]
    h --> pl["F. placement, 5 attempts per call"]
    pl --> cr["G. SUnitCreate: game draw, InitFn (H), PreOperate"]
    pre --> cr
    pre --> ps["I. pseudo-objects 574..582"]
    ps --> cr
    op["J. operate"] --> drop["ObjectChestDrop: items/tc"]
    ev["K. object timer events"] --> rgn
```

```mermaid
---
title: Which seed each decision draws
---
flowchart LR
    S["room seed S"] --- s1["slot draws, member picks"]
    S --- s2["shrine, well and trap handlers (2, 8, 9)"]
    O["object-region seed O"] --- o1["handlers 1, 3 to 7, theme roll"]
    O --- o2["every InitFn, PreOperate"]
    O --- o3["operate handlers, timer events"]
    G["game seed G"] --- g1["one step per object created"]
    U["unit seed"] --- u1["animation start, TC resolution"]
```

- [C] The window draws four seeds. The **room seed** gives the slot draws, the member picks and every draw of the
  shrine (2), well (8) and trap (9) handlers' room part. The **object-region seed** gives the other handlers, the theme
  roll, every `InitFn`, the `PreOperate` roll, the operate handlers and the timer events. The **game seed** steps once
  per object created. The **unit seed** gives the animation-start draw and, through `TC_ResolveDrops`, the drop.
  (fn:sub_00552610_RoomObjectsPopulate@0x00552610, fn:OBJRGN_GetSeed@0x00546FA0, run:2026-10-14-objects-window,
  run:2026-10-15-objects)

### A. The object-region seed and level records (game creation)

```
A1. OBJRGN_Create(game):                                          [C] (fn:OBJRGN_Create@0x00546C60, run:2026-10-15-objects)
      Step(G); v: u32 ← G.low                                      ; game-seed draw 2 after Init(N)
      Init(objrgn.seed, v)                                         ; O = {v, 666}
      for id in 1 ..< nLevels:
        L[id] ← { act ← Levels[id].Act, roomCount ← 0x7FFFFFFF, +0x1C ← −1, all else 0 }
      for c in 0 ..< 8:
        shrines[c] ← the Shrines codes whose effectclass = c, in record order
```

- A1. [C] `GameCreate` calls `OBJRGN_Create` at `0x00530DD1`, right after `MonRegionsInit` (`0x00530DCA`, game-seed draw
  1, [rng/seeds](../rng/seeds.md) step note 7a); no call sits between the two, so the object region takes game-seed draw
  2. (fn:sub_00530BF0_GameCreate@0x00530BF0, fn:sub_00547D20_MonRegionsInit@0x00547D20, run:2026-10-15-objects)
- A2. [C] `OBJRGN_GetSeed(game, room)` returns the region's seed and ignores the room: there is **one object-region
  stream per game**, advanced by every room's objects in activation order, every operate and every timer event.
  (fn:OBJRGN_GetSeed@0x00546FA0, struct:ObjCtx+0xC, run:2026-10-15-objects)

### B. The window in the room driver, and the revisit

```
B1. per room of the act's new-rooms walk, after the wanderer tick, if room.flags & 1 = 0:   [C] (fn:sub_0052D160_NewRoomsUpdate@0x0052D160, run:2026-10-15-objects)
      RoomPresetUnits(game, room)          ; RW1 → RW2: non-monsters first (objects: § G, § I), then monsters (oracle)
      RoomInactiveUnitsRestore(game, room) ; RW2 → RW3: no record on a first activation, no draw
      RoomObjectsPopulate(game, room)      ; RW3 → RW4: §§ C–F
      ... monster population pass (monsters/spawn), then flags |= 1
```

- B1. [C] A preset object goes `PresetUnitDispatch` → `SUnitCreate(x, y, game, room, flags 1, mode = DS1 mode)` and
  makes the creation draws of § G and **no room-seed draw**, unless its `InitFn` spawns monsters. The walk order (all
  non-monsters, then all monsters) and the per-level walk filters are [drlg/preset § 6](../drlg/preset.md#6-handover-to-the-server-spawners-boundary).
  (fn:sub_005557D0_PresetUnitDispatch@0x005557D0, fn:sub_005559A0_RoomPresetUnits@0x005559A0, run:2026-10-15-objects)
- B2. [C] On a first activation the inactive-unit restore leaves the room, game and object-region seeds unchanged (2090
  first activations of the three earlier runs, and every window of run:2026-10-15-objects).
  (fn:sub_00542B40_RoomInactiveUnitsRestore@0x00542B40, run:2026-10-14-objects-window, run:2026-10-15-objects)
- B3. [C] **Revisit.** When a room that went inactive is activated again (flags bit 0 already set, so outside the
  window above), the restore re-creates each saved object through `PresetUnitDispatch` with **every creation draw**
  of § G (one game-seed step, its `InitFn` on the object-region seed, the `PreOperate` roll), then restores the saved
  `interact` byte, mode and sparkle flag. A chest locked at its first creation stays locked even when its new `InitFn`
  3 roll did not lock it. 548 re-creations reproduced. (fn:sub_00542B40_RoomInactiveUnitsRestore@0x00542B40,
  fn:sub_005557D0_PresetUnitDispatch@0x005557D0, run:2026-10-15-objects)

### C. The gate and the theme roll

```
C1. Gate(game, room, lvlRec) → bool:                              [I] (fn:OBJ_PopulateGate@0x00552560)
      if DrlgRoom(room).flags & 0x30000: return false              ; input: a waypoint sets it on its room
      pop ← RoomPopLevelId(room)                                   ; input: 0 for Populate 0 or the near-town rule
      if pop = 0 or PresetPopTest(room) or pop ≥ nLevels or LevelIsTown(room): return false   ; inputs
      L ← objrgn.level[pop]
      if L.roomCount = 0x7FFFFFFF: L.roomCount ← LevelRoomCount(act of L, pop)               ; input, once
      L.roomsVisited ← L.roomsVisited + 1                          ; [C] counts gated rooms, not populated ones (run:2026-10-15-objects)
      if lvlRec.Themes ≠ 0 and ThemeRoll(game, room, L, lvlRec.Themes) = 1: return false
      return true

C2. ThemeRoll(game, room, L, themes) → i32:                       [C] (fn:OBJ_RoomThemeRoll@0x00552400, run:2026-10-15-objects)
      if L.roomCount < 10 × L[+0x0C]: return 0                     ; +0x0C has no writer: never taken
      r ← Range(O, 100)                                            ; draw
      thr: i32 ← 12
      if L.roomsVisited > L.roomCount ÷ 2: thr ← thr + 5
      if L.roomsVisited > L.roomCount − L.roomCount ÷ 4: thr ← thr + 5
      if r ≥ thr: return 0
      list ← the theme numbers t in 1 ... 7 with themes & (1 << (t − 1)) ≠ 0;  n ← |list|
      i ← Range(O, n)                                              ; draw
      t ← list[i]
      if t < n and g_ObjThemeFns[t] is enabled: return ThemeFn[t](…)   ; never on stock data
      return 0
```

- C1. [C] The gate's DRLG inputs are taken from the log (*Inputs and oracles*). Town windows drew nothing in all 222
  logged town activations. `lvlRec` is the room's **own** level record (`RoomGetLevelId`), while the counters belong
  to the **population** level `pop`. (fn:sub_0061A1F0_RoomPopLevelId@0x0061A1F0, fn:sub_006426A0_LevelIsTown@0x006426A0,
  struct:ObjRgnLevel+0x4, run:2026-10-14-objects-window, run:2026-10-15-objects)
- C2. [C] The stock `Themes` values are 8, 48 and 60; each lists only theme numbers ≥ `n` except 60, whose theme 3 has
  no handler, so **no theme ever runs on stock data** and the roll costs 1 or 2 object-region draws per gated room of
  the 39 levels with `Themes` set (20 rolls in the run, 2 of them drew an index). The theme handlers are named only:
  1 an empty room, 2 a barrel grid, 4 an item grid, 5 and 6 bookshelf or weapon-rack rows. (tbl:Levels.txt:Themes,
  data:g_ObjThemeFns@0x00731E68, run:2026-10-15-objects)

### D. The slot loop and the member pick

```mermaid
flowchart TD
    k["slot k = 0..7"] --> r["r = Range(S, 100), always"]
    r --> f{"level past 96/128 of its rooms,<br/>no code-2 shrine, Objects[g].SubClass != 0?"}
    f -->|"yes"| r100["r = 100"]
    f -->|"no"| t{"g != 0 and r <= ObjPrb[k]?"}
    r100 --> t
    t -->|"no"| k
    t -->|"yes"| r2["r2 = Range(S, 100)"]
    r2 --> w["walk ID0..7 to the first 0, sum PROB:<br/>first member with r2 < sum and Gore ok"]
    w -->|"found"| h["PopulateFn handler(DENSITY, class, 100)"]
    w -->|"sum <= r2"| k
    h --> k
```

```
D1. RoomObjectsPopulate(game, room):                              [C] (fn:sub_00552610_RoomObjectsPopulate@0x00552610, run:2026-10-14-objects-window, run:2026-10-15-objects)
      lvl ← Levels[RoomGetLevelId(room)]
      if not Gate(game, room, lvl): return
      for k in 0 ..< 8:
        g: u8 ← lvl.ObjGrp[k]
        r: u32 ← Range(S, 100)                                     ; draw, every slot, group 0 included
        L ← objrgn.level[RoomPopLevelId(room)]
        if L.roomCount > 0 and (L.roomsVisited << 7) ÷ L.roomCount > 96
           and L.healthShrines = 0 and Objects[g].SubClass ≠ 0:    ; record index g = the GROUP number (sic)
          r ← 100                                                  ; fails every slot (largest ObjPrb is 90)
        if g = 0 or r > lvl.ObjPrb[k]: continue
        G ← ObjGroup[g]; if G = none: return                       ; [I] only past the 133 records (fn:OBJGROUP_GetRecord@0x006412F0)
        r2: u32 ← Range(S, 100)                                    ; draw
        sum: i32 ← 0
        for i in 0 ..< 8 while G.ID[i] ≠ 0:
          sum ← sum + G.PROB[i]
          if r2 < sum and Objects[G.ID[i]].Gore ≤ goreLimit:
            fn ← g_ObjPopulateFns[Objects[G.ID[i]].PopulateFn]    ; PopulateFn ≥ 10 or DENSITY ≥ 0x80: fatal error
            if fn ≠ none: fn(game, room, G.DENSITY[i], G.ID[i], 100)
            break
```

- D1. [C] This order accounts for every room-seed draw of the 1405 drawing windows of the three earlier runs and of
  every window of run:2026-10-15-objects: one draw per slot whether or not the group is 0, `r ≤ ObjPrb` passes (so the
  chance is `(ObjPrb + 1)/100`), one pick draw per passing slot, and nothing placed when the `PROB` sum is at most
  `r2` (259 of 2307 passing slots). `PROB` is a percentage against 100, not a weight over the members' sum.
  (tbl:ObjGroup.txt:PROB0, tbl:Levels.txt:ObjPrb0, run:2026-10-14-objects-window)
- D2. [C] **The forced-slot rule is a game bug the spec keeps.** It tests `Objects[g].SubClass`, the Objects record
  whose index is the group number, so the slots it suppresses are those whose group index is 1–6, 50–53, 59, 60, 77,
  109, 116, 119, 120, 123, 124 or 129. Phase 2 tracked the counters at every slot and they matched; one slot was forced
  directly (Sewers level 2, slot 2, group 5). (0x005526CC, fn:OBJRGN_GetLevel@0x00546F90, tbl:Objects.txt:SubClass,
  run:2026-10-15-objects)
- D3. [I] Group 0 and the memberless groups 30 and 72 cost their draws and place nothing; a `PROB` 0 member is never
  picked; group 69 starts with an empty member slot and never places. The `Gore` test never excludes on stock data
  (`Gore` is 0 or 1, the limit 2). (tbl:Objects.txt:Gore, data:g_ObjGoreLimit@0x00731BBC)
- D4. [C] Every handler receives the member's `DENSITY`, its class (the Objects **record index**) and the
  probability 100. The handlers draw their own probability against 100: that draw always passes, but it is made.
  (data:g_ObjPopulateFns@0x00731D00, run:2026-10-15-objects)

### E. The `PopulateFn` handlers

Notation: `R(s, n)` is `Range(s, n)`: 0 with **no draw** when `n < 1`, else one draw and `low mod n`
([rng](../rng/README.md) step 2). `P100(s)` is `Range(s, 100)`. `RandLoHi(s, lo, hi)` is `lo + Range(s, hi − lo)`, `lo`
without a draw when `hi ≤ lo`. `cnt: i32 ← ((w·h >> 7) · DENSITY) >> 8` with signed shifts. `sx`, `sy` are the class's
`SizeX`, `SizeY` unless noted. Every creation is `SUnitCreate(2, class, x, y, game, room, flags 1, mode 0)` (§ G).
[C] (fn:RNG_RandLoHi@0x004BC500, fn:OBJPOP_Scatter@0x00551470, run:2026-10-15-objects)

| Fn | Handler | Seed | Draw sequence | Tag |
|---|---|---|---|---|
| 1 | `OBJPOP_Clusters` | O | `P100`; the class picks a list; clusters while `cnt > 0` and tries remain (E1) | [C] (fn:OBJPOP_Clusters@0x00550C20, run:2026-10-15-objects) |
| 2 | `OBJPOP_Shrine` | S | `P100`; cap; up to 3 (forced: 30) `OBJ_PlaceByOrientation` calls (E2) | [C] (fn:OBJPOP_Shrine@0x00552B50, run:2026-10-15-objects) |
| 3 | `OBJPOP_Scatter` | O | `P100`; `cnt` × `OBJ_PlaceRandom` | [C] (fn:OBJPOP_Scatter@0x00551470, run:2026-10-15-objects) |
| 4 | `OBJPOP_Barrels` | O | `P100`; `cnt` clusters, `2·cnt` tries, at most 8 objects (E3) | [C] (fn:OBJPOP_Barrels@0x00551850, run:2026-10-15-objects) |
| 5 | `OBJPOP_Crates` | O | `P100`; like 4, a class list of five, at most 8 followers (E4) | [I] (fn:OBJPOP_Crates@0x00551C00) |
| 6 | `OBJPOP_Corpse` | O | handler 3, then `OBJ_FliesAdd` on its last placement | [C] (fn:OBJPOP_Corpse@0x00551690, run:2026-10-15-objects) |
| 7 | `OBJPOP_StickCorpses` | O | `P100`; pattern `R(4)`; ≤ 8 anchor tries; one class draw per placed cell (E5) | [C] (fn:OBJPOP_StickCorpses@0x00551200, run:2026-10-15-objects) |
| 8 | `OBJPOP_Well` | S | cap; `P100`; one `OBJ_PlaceRandomRoomSeed` (E6) | [C] (fn:OBJPOP_Well@0x005516C0, run:2026-10-15-objects) |
| 9 | `OBJPOP_Trap` | S, then O | `P100` on S; `cnt` × `OBJ_PlaceRandom` on O, stopping at the first trap placed | [C] (fn:OBJPOP_Trap@0x00551580, run:2026-10-15-objects) |

- [C] On the room seed, handler 9 draws exactly once, handler 2 draws `1 + 2a` (`a` = placement attempts made), and
  handler 8 draws 0 (cap reached) or `1 + 2a`. Handlers 1 and 3–7 never draw the room seed.
  (run:2026-10-14-objects-window, run:2026-10-15-objects)

**E1. Handler 1 (urns, caskets, baskets, sarcophagi).** [C] (fn:OBJPOP_Clusters@0x00550C20,
data:g_ObjClusterLists@0x00731D50, run:2026-10-15-objects) The class chooses a list, the number of tries, and the ring
step and base used to walk away from the first object; the first object of every cluster uses the padded test.

| Class | List | Tries | Step / base | Follower test |
|---|---|---|---|---|
| 3 | 3, 28 | 18 | 5 / 5 | padded |
| 1, 79 | 79, 53, 1 | 12 | 5 / 5 | padded |
| 4 | 4, 9, 52, 94, 95 | 12 | 0 / 1 | tight |
| 89 | 89, 284 | 12 | 5 / 5 | padded |
| 208, 209 | 208, 209 | 12 | 0 / 1 | tight |
| any other | — | — | — | returns after the `P100` |

```
E1. Clusters(class, DENSITY):                                     [C] (fn:OBJPOP_Clusters@0x00550C20, run:2026-10-15-objects)
      if P100(O) > 100: return                                     ; draw; never taken
      if cnt ≤ 0: return
      while tries > 0:
        cls ← list[R(O, n)]                                        ; n = list length
        x ← rect.x + R(O, w − sx − 1);  y ← rect.y + R(O, h − sy − 1)   ; sx, sy of the member class
        if not PosTestPadded(x, y): tries ← tries − 1; continue
        create(cls, x, y);  k ← 1;  ok ← true
        loop:
          m ← k >> 1
          if m > 0 and R(O, m) ≠ 0: break                          ; the cluster ends with chance 1 − 1/m
          if not ok: break
          ok ← false;  i ← 0;  lim ← 3 × max(cnt, 4)
          while not ok and i < lim:
            Step(O); d ← O.low & 7                                 ; draw
            x ← x + (R(O, step) + base) × dx[d] × 2                 ; R(O, 0) makes no draw
            y ← y + (R(O, step) + base) × dy[d] × 2
            ok ← followerTest(x, y);  i ← i + 1                     ; a rejected step still moves the point
          if ok: create(list[R(O, n)], x, y); k ← k + 1
        cnt ← cnt − 1;  tries ← tries − 1
        if cnt ≤ 0: return
```

**E2. Handler 2 (shrines).** [C] (fn:OBJPOP_Shrine@0x00552B50, fn:OBJRGN_HealthShrineDue@0x00547330,
fn:OBJRGN_ShrineCapReached@0x00547360, struct:ObjRgnLevel+0x10, run:2026-10-15-objects)

```
E2. Shrine(class, prob = 100):
      r ← P100(S)                                                  ; draw
      forced ← HealthShrineDue(L)                                  ; [I] the due rule (fn:OBJRGN_HealthShrineDue@0x00547330)
      if forced: tries ← 30
      else: if r > prob: return;  tries ← 3                        ; never returns
      if ShrineCapReached(L): return                               ; [I] nShrinePos = 10 or > roomCount ÷ 8; not reached (fn:OBJRGN_ShrineCapReached@0x00547360)
      repeat tries times until placed:
        PlaceByOrientation(class, Orientation, popLvl, ShrineDistOk)   ; on S, § F
      on a placement:
        if forced and code ≠ 2:                                    ; [I] not reached (fn:OBJ_ShrineClassSubst@0x00552AC0)
          class ← Parm1 if 1 ≤ Parm1 ≤ 572 else 84
          ShrinePick(class 2, level 1)                             ; its draws are made, the result discarded
          code ← 2
        if code = 2 or forced: L.healthShrines ← L.healthShrines + 1
        record the position in the level's shrine list (nShrinePos + 1)
```

- E2. [I] `HealthShrineDue` holds once more than 75 % of the level's rooms have been gated and no code-2 shrine
  stands. Its 30 tries were needed by 2 windows of the older runs; a forced conversion of a placed shrine was never
  reached. (fn:OBJRGN_HealthShrineDue@0x00547330, run:2026-10-15-objects)

**E3. Handler 4 (barrels).** [C] (fn:OBJPOP_Barrels@0x00551850, tbl:Objects.txt:Xspace, run:2026-10-15-objects) It
ignores the member class and uses the size and `Xspace`/`Yspace` of record 7 (`Barrel`).
- Each try draws, in order: the class (`low mod 3 = 0` → 11 `BarrelExploding`, else 7), `x = rect.x + R(O, w)`,
  `y = rect.y + R(O, h)`; the tight test decides, and a failure only spends a try (`2·cnt` in all).
- On a success it creates the object and walks a cluster as in E1, each step one draw `d = low & 7`, then
  `x += Xspace·dx[d]`, `y += Yspace·dy[d]` (u8 values), up to 15 steps per follower; each follower draws its class,
  `low & 3 = 0` → 11, else 7.
- The handler returns after 8 objects in all. So the first barrel of a cluster explodes with chance 1/3, each follower
  with 1/4.

**E4. Handler 5 (crates).** [I] (fn:OBJPOP_Crates@0x00551C00) For a class other than 46, each try draws
`cls = list[R(O, 5)]` from (4, 9, 52, 94, 95), then `x`, `y` as in E3; on a success it draws the class **again** and
creates that one; followers take the same class with up to `max(4, ringLim)` steps of the member class's
`Xspace`/`Yspace`, `ringLim` starting at `4·cnt` and dropping by 4 per cluster; the handler stops after 8 followers.
Class 46 (`Crate`) skips both class draws. No stock level reaches it (*Open questions*).

**E5. Handler 7 (rogue on a stick), and flies.** [C] (fn:OBJPOP_StickCorpses@0x00551200, fn:OBJ_FliesAdd@0x00551150,
data:g_ObjStickPatterns@0x00731EB4, run:2026-10-15-objects)
1. `P100(O)` (passes), then the pattern `p = R(O, 4)`.
2. Up to 8 anchor tries: `x = rect.x + R(O, w − sx − 1)`, `y = rect.y + R(O, h − sy − 1)`, padded test with size 5 × 5.
3. For each offset of pattern `p`: the padded test at `anchor + offset` with the class size; on a pass, one draw for
   the class `57 + (low & 1)`, the creation, and `OBJ_FliesAdd`.

`OBJ_FliesAdd` (also handler 6, on the last placement of its handler-3 run) draws `P100(O)` and creates object 103
(`flies`) at the corpse's position when the value is above 70 (chance 29/100). The patterns are written at start-up by
the initialiser `0x006CAF30` (the file image holds zero counts):

| p | Offsets (dx, dy) |
|---|---|
| 0 | (−4,0) (0,0) (4,0) (8,0) (0,4) (0,−4) |
| 1 | (−8,0) (−4,0) (0,0) (4,0) (8,0) |
| 2 | (0,−8) (0,−4) (0,0) (0,4) (0,8) |
| 3 | (−7,−5) (−5,−3) (−3,−1) (0,0) (3,−1) (5,−3) (7,−5) |

**E6. Handler 8 (wells).** [C] (fn:OBJPOP_Well@0x005516C0, fn:OBJRGN_WellCapReached@0x00547300, run:2026-10-15-objects)
It returns at once when `WellCapReached` (`nWellPos = 4` or `> roomCount ÷ 8`; the cap itself is `[I]`, not reached).
Otherwise one room draw against `prob`, then one `OBJ_PlaceRandomRoomSeed` with size `(2·sx + 1) × (2·sy + 1)` and
`WellDistOk`; a placed well's position is recorded.

### F. Placement and the position tests

```
F1. PlaceRandom(class, sx, sy, room) → unit | none:               [C] (fn:OBJ_PlaceRandom@0x00550380, run:2026-10-15-objects)
      if w < 2 or h < 2: return none
      repeat 5 times:
        x ← rect.x + R(O, w − sx − 1);  y ← rect.y + R(O, h − sy − 1)     ; 2 draws per attempt
        if x ≠ 0 and y ≠ 0
           and rect.x + 1 ≤ x < rect.x + w − 1 and rect.y + 1 ≤ y < rect.y + h − 1     ; compared as u16
           and COLL_WHTest(room, x, y, sx + 6, sy + 6, 0x3F11) = 0:
          return create(class, x, y)
      return none                                                  ; no fallback

F2. PlaceRandomRoomSeed: as F1 on S, plus the handler's extra test (WellDistOk)     [C] (fn:OBJ_PlaceRandomRoomSeed@0x00550540, run:2026-10-15-objects)

F3. PlaceByOrientation(class, orientation, …), on S:              [C] (fn:OBJ_PlaceByOrientation@0x00550A30, tbl:Objects.txt:Orientation, run:2026-10-15-objects)
      orientation 1: x ← rect.x + w ÷ 4 + R(S, w ÷ 2);  y ← rect.y + RandLoHi(S, 1, 2)   ; always 1, but one draw
      orientation 2: the same with the axes swapped
      otherwise:     as F1's point, on S

F4. PosTestPadded(x, y, sx, sy):                                  [C] (fn:OBJ_PosTestPadded@0x00550220, run:2026-10-15-objects)
      sx + 2 ≤ w, sy + 2 ≤ h, rect.x + 1 < x < rect.x + w − sx − 2, rect.y + 1 < y < rect.y + h − sy − 2,
      COLL_WHTest(room, x, y, sx + 7, sy + 7, 0xC01) = 0 and COLL_WHTest(room, x, y, sx, sy, 0x3F11) = 0

F5. PosTestTight(x, y, sx, sy):                                   [C] (fn:OBJ_PosTestTight@0x005502F0, run:2026-10-15-objects)
      w > 1, h > 1, rect.x + 2 < x < rect.x + w − sx, rect.y + 2 < y < rect.y + h − sy,
      COLL_WHTest(room, x, y, sx + 2, sy + 2, 0x3F11) = 0
```

- F1. [C] Accepted attempts in run:2026-10-15-objects fell at attempts 1 to 5 (153, 87, 67, 51, 29), and 911 placer
  calls found no spot. When no spot is found the object is not created. (fn:OBJ_PlaceRandom@0x00550380,
  run:2026-10-15-objects)
- F6. [I] `COLL_WHTest(room, x, y, w, h, mask)` tests one cell (`COLL_CellTestNb`) when `w ≤ 1` and `h ≤ 1`, otherwise
  the inclusive rectangle `{x − w/2, y − h/2, x − w/2 + w − 1, y − h/2 + h − 1}` (unsigned halving) with `COLL_RectTest`,
  whose semantics are [drlg/collision § E](../drlg/collision.md#e-collisiontest-by-size). Mask `0x3F11` contains the
  object bit `0x400`, so an earlier object's mark rejects the spot. Its result is a logged value in the run
  (*Inputs and oracles*). (fn:COLL_WHTest@0x0064D800, fn:COLL_RectTest@0x0064CEB0, fn:COLL_CellTestNb@0x0064CA50)
- F7. [C] `ShrineDistOk` rejects a point when, for some recorded shrine of the level, `|dx| < 50` **or** `|dy| < 50`:
  a second shrine needs both axes 50 subtiles away from every earlier one. `WellDistOk` does the same with 100.
  (fn:OBJRGN_ShrineDistOk@0x00547430, fn:OBJRGN_WellDistOk@0x005473A0, run:2026-10-15-objects)

### G. Creation: `SUnitCreate` for an object

```
G1. SUnitCreate(type 2, class, x, y, game, room, flags, mode):    [C] (fn:sub_00555230_SUnitCreate@0x00555230, run:2026-10-15-objects)
      Step(G); Init(unit.seed, G.low)                              ; one game-seed draw (UnitSeedInit)
      unit.data ← new ObjectData (0x38 B); objRec ← Objects[class] ; class = record index
      SetMode(unit, mode)                                          ; G2
      ServerInit(unit)                                             ; G3
      path; if objRec.HasCollision[mode]: mark SizeX × SizeY       ; drlg/collision § F; no draw

G2. SetMode(unit, mode) → UNIT_AnimInit:                          [C] (fn:UNIT_SetMode@0x00624690, fn:UNIT_AnimInit@0x00624390, run:2026-10-15-objects)
      if objRec.Sync = 0: Range(unit.seed, objRec.FrameDelta[mode] >> 3)     ; unit-seed draw (none when the value is < 1)

G3. ServerInit(unit):                                             [C] (fn:OBJ_ServerInit@0x0054F5D0, run:2026-10-15-objects)
      sparkle ← 0; interact ← 0
      if objRec.InitFn < 80: g_ObjInitFns[InitFn]({game, unit, room, &O, objRec, x, y})   ; § H
      selectable ← objRec.Selectable[mode]
      if objRec.PreOperate and not (unit.flags & 0x80):
        if Range(O, 14) = 0: SetMode(unit, 2)                      ; draw; opened, chance 1/14
```

- G1. [C] `UnitSeedInit` steps the game seed for every non-player unit, objects included; the path step makes no draw
  for an object. The class is the Objects **record index**: `Id` is never read, so records 410–412 are classes
  410–412 ([I] for the lookup itself). (fn:sub_00552DF0_UnitSeedInit@0x00552DF0, fn:sub_00554850_SUnitPathCreate@0x00554850,
  fn:OBJECTS_GetRecord@0x00640E90, run:2026-10-15-objects)
- G2. [C] The animation draw touches only the object's own unit seed. Any later mode change (a state `InitFn`, the
  `PreOperate` roll, the operate) makes it again. (fn:UNIT_AnimInit@0x00624390, tbl:Objects.txt:Sync,
  tbl:Objects.txt:FrameDelta0, run:2026-10-15-objects)
- G3. [C] 510 `PreOperate` rolls reproduced; unit flag `0x80` (set by the super-chest pseudo-object, § I) skips the
  roll. (tbl:Objects.txt:PreOperate, fn:OBJ_PresetSuperChest@0x0054F370, run:2026-10-15-objects)

### H. Draws at creation, per `InitFn`

A callee scan of all 76 distinct `InitFn` handlers to depth 3 found draws only in the rows below; every draw is on
the object-region seed `O` unless the row says otherwise. [I] (data:g_ObjInitFns@0x00731BC0,
[objects/0001 § 7](../../findings/objects/0001-object-population.md#7-the-initfn-draws))

| InitFn | Objects | Draws, in order | Tag |
|---|---|---|---|
| 1 | 92 shrine rows | H1 | [C] (fn:OBJINIT_Shrine@0x0054F9D0, fn:OBJ_ShrinePick@0x0054F770, run:2026-10-15-objects: 65 shrines) |
| 2 | 37 urns, jars, baskets | `P100(O) < MonLvl1 ÷ 8 + 5` → trap type `RandLoHi(O, 1, 9)` (1..8), else none | [C] (fn:OBJINIT_TrapByte@0x0054FBB0, tbl:Levels.txt:MonLvl1, run:2026-10-15-objects: 397 runs) |
| 3 | 71 chests | `InitFn` 2; then, for a `Lockable` row, `P100(O) < MonLvl1 ÷ 2 + 8` → locked (`interact` bit 7); then one draw `v = low mod 0xFFFE + 1` and `Init(unit.seed, v)` | [C] (fn:OBJINIT_Chest@0x0054FCB0, tbl:Objects.txt:Lockable, run:2026-10-15-objects: 212 runs) |
| 27 | goo pile | one draw: `low mod 1000 > 332` → `interact` 0, else 3 (chance 333/1000) | [C] (data:g_ObjInitFns@0x00731BC0, run:2026-10-15-objects: 2 runs) |
| 28 | gold-pile dummy (269) | `n = 1 + low mod 9` piles (1..9); per pile two draws, offsets `(low & 3, low & 3)`, a 1×1 test at the object's cell plus the offset, a gold drop (seed oracle) | [C] (fn:OBJINIT_GoldPiles@0x0054F8C0, run:2026-10-15-objects: 14 objects, counts 2–9, 71 drops) |
| 34 | 358, 359 `fire` | one draw, odd → mode 1 | [C] (data:g_ObjInitFns@0x00731BC0, run:2026-10-15-objects: 20 runs) |
| 57 | 397 `sparklychest`, 455 `specialchest` | `InitFn` 3, then the sparkle flag | [I] (fn:OBJINIT_SparklyChest@0x0054FD90) |
| 58 | fissure | one draw for a timer | [I] (data:g_ObjInitFns@0x00731BC0) |
| 79 | Zoo | `RandLoHi` on a quest-held seed, not `O` | [I] (data:g_ObjInitFns@0x00731BC0) |
| 46 | 369 (City of the Damned) | random points and monster spawns 403/404: room, game and `O` draws; seed oracle | [C] (fn:OBJINIT_CityDamnedSpawns@0x005506D0, run:2026-10-15-objects: 16 calls) |
| 47, 54, 55, 62, 66, 68, 69 | quest objects | monster spawns through `SpawnAtPos` or `PresetMonSpawn`; seed oracles | [I] (data:g_ObjInitFns@0x00731BC0) |
| every other | — | no draw; some (4, 6, 8, 9, 12, 14, 16, 17, 22, 26 in the run) set mode or `interact` from game state, whose mode change draws the unit seed (G2) | [I] no draw (data:g_ObjInitFns@0x00731BC0); [C] the state values as inputs (run:2026-10-15-objects) |

Together with § G, one object's creation draws, in order: one game-seed step; G2's unit-seed draw for mode 0 (when
`Sync` is 0); the `InitFn` row above; for a `PreOperate` row the 1/14 roll on `O`, and its mode change's unit-seed draw.
[C] (fn:sub_00555230_SUnitCreate@0x00555230, fn:OBJ_ServerInit@0x0054F5D0, run:2026-10-15-objects)

```
H1. InitFn 1, shrines (object, room):                              [C] (fn:OBJINIT_Shrine@0x0054F9D0, fn:OBJ_ShrinePick@0x0054F770, tbl:Objects.txt:Parm0, run:2026-10-15-objects)
      lid ← RoomGetLevelId(room)                                   ; the Levels Id, not a monster level
      if Parm0 = 0:                                                ; [I] no stock row, unreachable (0x0054F9F5)
        up to 8 tries: code ← 1 + R(O, N − 1) until Shrines[code].LevelMin ≤ lid
      else:
        c ← 2 if Parm0 = 1; 3 if Parm0 = 2; else (R(O, 10) = 0 ? 1 : 4)     ; one draw only in the last case
        code ← ShrinePick(c, lid):  up to 8 tries: shrines[c][R(O, n_c)] until LevelMin ≤ lid
      if code = 4: code ← 2;  if code = 5: code ← 3;  if code = 16: code ← 18
      interact ← code
```

- H1. [C] `rarity` is not read: the pick is uniform in the class list. Class 0 (holding row 0, `None`) is never asked
  for. So Health Exchange (4), Mana Exchange (5) and Shrine of Enirhs (16) are never placed by a populate pass, and
  Resist Cold (26), Lightning (32) and Poison (21) only in levels whose id reaches those values. The run's 65 shrines
  took codes 1, 2, 3, 6, 7, 8, 10, 11, 12, 13, 14, 15, 18 and 20. (tbl:Shrines.txt:LevelMin, tbl:Shrines.txt:effectclass,
  run:2026-10-15-objects)
- H2. [C] The trap and lock chances read `MonLvl1` in Nightmare and Hell too: every lock and trap roll of the 212
  chests and 397 containers reproduced on the normal-difficulty column. In Lower Kurast (`MonLvl1` 22) a chest locks
  with chance 19 %. (tbl:Levels.txt:MonLvl1, fn:OBJINIT_Chest@0x0054FCB0, run:2026-10-15-objects)
- H3. [C] `InitFn` 3's re-seed replaces the chest's unit seed, so its drops (§ J) draw from `{v, 666}`, not from the
  game-seed-derived seed of G1. (fn:OBJINIT_Chest@0x0054FCB0, run:2026-10-15-objects)

### I. DS1 preset objects and the pseudo-objects

- [C] `PresetUnitDispatch` sends a type-2 id below 573 to `SUnitCreate` (§ G), does nothing for 573, and sends 574..582
  to `OBJ_PresetPseudoDispatch` (`g_ObjPseudoFns`). (fn:sub_005557D0_PresetUnitDispatch@0x005557D0,
  fn:OBJ_PresetPseudoDispatch@0x0054F490, data:g_ObjPseudoFns@0x00731D28, run:2026-10-15-objects)

| Id | Handler | What it creates | Tag |
|---|---|---|---|
| 574..579 | `OBJ_PresetFixedShrine` | class 136 in the DS1 mode (its `InitFn` 1 draws first), then `code = lo + R(unit.seed, hi − lo)` with (lo, hi) = (2,6), (7,7), (8,11), (12,12), (1,5), (14,14); 4 and 5 → 2. No stock DS1 places them | [I] (fn:OBJ_PresetFixedShrine@0x0054F0D0, data:g_PresetShrineRanges@0x006E1080) |
| 580 | `OBJ_PresetSuperChest` | a random chest as 581 (level 25: class 371), the sparkle flag except in Maggot Lair 62–64, where `P100(O) > 50` skips it; level 25 sets trap type 3; unit flag `0x80`; mode 0 | [C] (fn:OBJ_PresetSuperChest@0x0054F370, run:2026-10-15-objects: 4 super chests) |
| 581 | `OBJ_PresetRandomChest` | one draw on `O`: Act II level 74 `{387, 389, 390, 391}[low & 3]`, other Act II `{87, 88}[low & 1]`; Act III level 83 `{329..332}[low & 3]`, other Act III `{181, 183}[low & 1]`; other acts `{5, 6, 139, 140, 141, 144, 176, 177, 198, 240, 241, 242, 243}[low mod 13]`; mode 0 | [C] (fn:OBJ_PresetRandomChest@0x0054F180, run:2026-10-15-objects) |
| 582 | `OBJ_PresetQuestObject` | the class from quest 13's state, else 307; seed oracle | [I] (fn:OBJ_PresetQuestObject@0x0054F430) |

### J. Operate: chests and containers up to the drop

```mermaid
flowchart TD
    op["OBJ_OperateDispatch: OperateFn"] --> c4{"OperateFn"}
    c4 -->|"4 chest"| lk{"locked?"}
    lk -->|"no key, not class 6"| stop["return"]
    lk -->|"ok"| sp{"sparkle?"}
    sp -->|"yes"| q["r0 = P100(O): q = 6 if r0 < 5 else 4"]
    sp -->|"no"| r["r = P100(O)"]
    q --> r
    r --> e{"r <= 24, not locked, not sparkle?"}
    e -->|"yes"| none["empty"]
    e -->|"no"| d["1 + locked drops: ObjectChestDrop(q)"]
    c4 -->|"3 urn"| u["P100(O) < 21: one drop"]
    c4 -->|"5 barrel"| b["spawn test, then P100(O) < 21: one drop"]
    d --> tc["items/tc: TC_GetChestTC, TC_ResolveDrops"]
    u --> tc
    b --> tc
```

```
J1. OperateDispatch(object, player):                               [C] (fn:OBJ_OperateDispatch@0x00584420, run:2026-10-15-objects)
      if class ∈ {121, 122, 22}: excluded
      g_ObjOperateFns[OperateFn]({game, object, player, &O, class})

J2. Chest, OperateFn 4:                                           [C] except class 397 (fn:OBJOP_Chest@0x00585F60, run:2026-10-15-objects)
      if mode ≠ 0: return
      locked ← interact & 0x80
      if locked: needs a key (consumed) or player class 6, else return;  drops ← 2
      else: drops ← 1
      if sparkle: r0 ← P100(O); q ← (r0 < 5) ? 6 : 4               ; draw; forced quality rare or magic
      else: q ← 0
      if class ≠ 397:
        r ← P100(O)                                                ; draw
        if r > 24 or sparkle or locked:
          repeat drops times: ObjectChestDrop(q)
          if sparkle and no item made so far is magic or better:
            up to 10 more ObjectChestDrop(q), until one is
        ; else nothing: 25 % of plain chests are empty
      else:                                                        ; [I] class 397, not operated in the run (fn:OBJOP_Chest@0x00585F60)
        q ← 0; sparkle ← 0; r ← Range(O, 10000)
        < 200: ObjectChestDrop(7), once more if not magic+, then F if still not
        < 600: the same with 5;   < 1200: the same with 6
        < 3200: up to 10 drops (4) until 3 are magic+; no item at all → F
        < 6200: up to 10 drops (4) until 2 are magic+; n ← the non-magic items; if n = 0: one drop (0), n ← 1 if it made an item; then 7 − n gold
        else: F
        F: up to 10 drops (4) until one is magic+, then 4 − n drops (0), then 5 'gld ', 2 'hp3 ', 2 'mp3 ' (0x00585970)
      SetMode(1 if objRec.Mode1 ≠ 0 else 2)                        ; G2's unit-seed draw; mode 1 queues the next event
      OBJ_TrapFire(interact & 0x7F)                                ; [I] last, as a timed event; effect named only (fn:OBJ_TrapFire@0x00582510)

J3. ObjectChestDrop(object, player, q):                           [C] (fn:sub_00585B90_ObjectChestDrop@0x00585B90, fn:TC_GetChestTC@0x00654E80, run:2026-10-15-objects)
      tier ← the level's monster level against the act's two reference levels
      tc ← TC_GetChestTC(difficulty, act, tier)                    ; no draw
      return TC_ResolveDrops(game, src: object, killer: player, tc, forcedQ: q, …)   ; draws the object's unit seed
```

- J2. [C] The run operated 40 chests: 11 empty (`r ≤ 24`), 6 locked ones opened with two drops each, and 3 sparkle
  chests (DS1 580), all with forced quality 4, which repeated the drop until one item was magic or better (4, 4 and 6
  drops). (fn:OBJOP_Chest@0x00585F60, fn:sub_0062A0F0_ItemQualityMagicPlus@0x0062A0F0, fn:UNIT_GetSparkle@0x005540D0,
  run:2026-10-15-objects)
- J3. [C] **The chest drop is the item-creation entry.** `ObjectChestDrop` makes no draw of its own, picks
  `Act N Chest A/B/C` with `TC_GetChestTC` and calls `TC_ResolveDrops` once; the choice of the TC and the resolution
  are [items/tc § J](../items/tc.md#j-object-drops-named-only). Its `EDX` argument is passed on as the resolver's forced
  quality: 0 from the casket, urn and barrel handlers, `q` from the chest; the resolver applies a non-zero forced
  quality in place of the quality roll of [items/quality](../items/quality.md) for every entry that is not a unique or
  set entry ([items/tc § H](../items/tc.md#h-item-pick-and-hand-off), H4). A sparkle chest uses the usual act chest TC
  (`Act 3 Chest B` twice, `Act 1 Chest A` in the run): only its quality is forced. (0x00585CC5,
  fn:TC_ResolveDrops@0x0055A6D0, data:g_ChestTCs@0x0096C5F4, run:2026-10-15-objects)
- J4. [C] The other containers draw on `O` as follows (37 urns, jars and baskets, 11 barrels, 1 casket in the run;
  run:2026-10-15-objects):

| OperateFn | Objects | Sequence | Tag |
|---|---|---|---|
| 3 | urns, jars, baskets | `P100(O) < 21` → one `ObjectChestDrop(0)` (chance 21/100: an urn at `r = 20` dropped), then the trap | [C] (fn:OBJOP_Urn@0x005866C0, run:2026-10-15-objects) |
| 5 | barrels | an effect on the operating player (`0x00580A70`, not read), then `Range(O, 10000) ≥ 8192` → a monster spawn (`0x00582280`, no `O` draw), then `P100(O) < 21` → one drop | [C] (fn:OBJOP_Barrel@0x005868A0, run:2026-10-15-objects) |
| 1 | caskets, sarcophagi | one `ObjectChestDrop(0)`; only if it made an item, `Range(O, 10000) ≥ 8192` (18.08 %) → a monster spawn; then the trap | [C] for the no-item path, [I] after an item (fn:OBJOP_Casket@0x00586410, run:2026-10-15-objects) |

- J5. [I] Armor stands (`OperateFn` 19) and weapon racks (20) call other item creators (`0x005594C0`, `0x00559630`), not
  the chest TC. `OBJ_TrapFire(t)` calls `g_ObjTrapFns[t]` (0 = none); types 8 and 9 spawn monsters after a
  region-class test. (fn:OBJ_TrapFire@0x00582510, data:g_ObjTrapFns@0x00732CEC)

### K. Object timer events

- [C] The twelve object event callbacks of `g_ObjEventFns` run from the game's event queue, outside every populate or
  operate scope, and some draw the object-region seed: `0x00581700` draws `Range(O, 35)` for its next event time at
  every call (3042 draws in the run, all at `0x0058176F`). **When** an event runs is game simulation (ADR-0002) and an
  input; its draws are modelled and were compared one by one. A reimplementation that advances `O` only through §§ C–J
  drifts as soon as such an object (a periodic effect, e.g. the act-town fires) has run. What the callbacks do is
  named only (`[I]`). (data:g_ObjEventFns@0x006E19B0, run:2026-10-15-objects)

```mermaid
sequenceDiagram
    participant GC as GameCreate
    participant W as room windows
    participant P as operate
    participant E as timer events
    participant O as object-region seed
    GC->>O: Init(low of game draw 2)
    W->>O: theme rolls, handlers 1 and 3 to 7, InitFns, PreOperate
    P->>O: operate draws up to each ObjectChestDrop
    E->>O: next-event draws, when the event runs
```

## Outputs

- The room's objects, each with its class, position, mode, `interact` byte (shrine code, or trap type and lock bit),
  sparkle flag and unit seed, and its collision mark when `HasCollision[mode]` is set
  ([drlg/collision § F](../drlg/collision.md#f-unit-marks)). [C] (fn:sub_00555230_SUnitCreate@0x00555230,
  run:2026-10-15-objects)
- The room seed at the monster pass entry (`RW4`), which [monsters/spawn § A](../monsters/spawn.md#a-when-the-pass-runs-and-the-room-seed-before-it)
  consumes, and the advanced object-region and game seeds. [C] (run:2026-10-15-objects)
- The level records' counters (rooms visited, health shrines, shrine and well positions). [C] (struct:ObjRgnLevel+0x4,
  run:2026-10-15-objects)
- On operate: the forced quality and the number of `ObjectChestDrop` calls handed to [items/tc](../items/tc.md). [C]
  (fn:sub_00585B90_ObjectChestDrop@0x00585B90, run:2026-10-15-objects)

## Worked example

Source: run:2026-10-15-objects, checked by `python3 -I tools/objects.py check -v <log>` (0 mismatches). Seeds are
`low:high`, hex; draw values are recomputed with the [rng](../rng/README.md) step from the logged seeds. Positions are
in subtiles; `COLL_WHTest` results are the logged values.

### 1. One room's object population (Cold Plains)

Log `objects-s2-2302-normal.log` (seed 2302, Normal, expansion). Level 3 (Cold Plains), room rectangle
(5080, 5600, 40, 40). At `RW3`: `S = F203F612:445A3ECF`, `O = E5E436E7:37A0A321`, `G = C8BE2664:542FC4C8`. The gate is
open (no flag, population level 3, no preset test, not a town; `Themes` 0, so no theme roll); `roomsVisited` 9 after
the increment, `roomCount` 71, so the forced rule does not apply (`9·128 ÷ 71 = 16`). Slots: 0 group 4 `ObjPrb` 3,
1 group 38 `ObjPrb` 22, 2 group 33 `ObjPrb` 22, 3 group 34 `ObjPrb` 22, 4–7 group 0.

| # | Seed | After | Value | Meaning |
|---|---|---|---|---|
| S1 | S | `81BCBAA9` | 17 | slot 0: 17 > 3, fails |
| S2 | S | `BCE20FDD` | 5 | slot 1: 5 ≤ 22, passes |
| S3 | S | `7FED4BB1` | 41 | pick in group 38: `PROB` sums 34, 67 → member 1, class 174 (`loose rock`, `PopulateFn` 3, `DENSITY` 30) |
| — | — | — | — | handler 3: `cnt = ((40·40 >> 7)·30) >> 8 = (12·30) >> 8 = 1` |
| O1 | O | `9BCAD2E4` | 40 | `P100` against 100: passes |
| O2 | O | `DDEF58B3` | 27 | attempt 1: `x = 5080 + R(38) = 5107` |
| O3 | O | `6480C40A` | 36 | `y = 5600 + R(38) = 5636`; inside the margin; `COLL_WHTest(…, 7, 7, 0x3F11)` = 1 (logged): rejected |
| O4 | O | `E5A9BB0C` | 20 | attempt 2: `x = 5100` |
| O5 | O | `0206F5D5` | 11 | `y = 5611`; test = 0: accepted |
| G1 | G | `DD738FBC` | — | `SUnitCreate`: unit seed `DD738FBC:0000029A`; `InitFn` 0, `PreOperate` 0, `Sync` 1: no other draw. The 1×1 mark `0x400` at (5100, 5611) is a logged CM line |
| S4 | S | `0FDCEB6F` | 31 | slot 2: fails |
| S5 | S | `BCA517A3` | 99 | slot 3: fails |
| S6–S9 | S | `D506A7C1`, `A47055AC`, `8E84AA6F`, `5865A6C4` | 69, 88, 55, 36 | slots 4–7, group 0: drawn, nothing placed |

At `RW4`: `S = 5865A6C4:3B7179C6` (9 room draws), `O = 0206F5D5:5FCA6A9A` (5 draws), `G = DD738FBC:53BA707C` (1 step),
as logged. [C] (fn:sub_00552610_RoomObjectsPopulate@0x00552610, fn:OBJ_PlaceRandom@0x00550380, run:2026-10-15-objects)

### 2. A shrine creation (Jail Level 1)

Log `objects-s24-2324-normal.log` (seed 2324, Normal, expansion). Level 29 (Jail Level 1, `Themes` 8, `MonLvl1` 10),
room rectangle (17500, 5060, 60, 60). At `RW3` (after the presets window): `S = 3E9F9A6B:140070BB`,
`O = 0163CA78:0EEC6069`, `G = 44AAD1B0:109C952C`.

| # | Seed | After | Value | Meaning |
|---|---|---|---|---|
| O1 | O | `8B6AAEC1` | 77 | theme roll in the gate (`roomCount` 13, `roomsVisited` 2): 77 ≥ 12, no theme |
| S1 | S | `C8707512` | 2 | slot 0, group 51 (`act1 jail shrines`), `ObjPrb` 11: passes |
| S2 | S | `9A6EDFA5` | 77 | pick: `PROB` 12 per member, sums 12, 24, … 84 → member 6, class 77 (`Shrine`, `PopulateFn` 2, `Orientation` 1, size 3 × 3, `Parm0` 1) |
| S3 | S | `D456F2C6` | 38 | handler 2: `P100` against 100; not due (`2·128 ÷ 13 = 19`), so 3 tries; cap not reached |
| S4 | S | `5105E40E` | 28 | orientation 1: `x = 17500 + 60 ÷ 4 + R(30) = 17543` |
| S5 | S | `313512A0` | 0 | `y = 5060 + RandLoHi(1, 2) = 5061`; `COLL_WHTest(…, 9, 9, 0x3F11)` = 0 (logged), no earlier shrine: placed |
| G1 | G | `0C22F19C` | — | unit seed `0C22F19C:0000029A` |
| O2 | O | `5F3F7052` | 0 | `InitFn` 1: `Parm0` 1 → class 2 (no draw); `ShrinePick`: list `{2, 4}`, `R(2) = 0` → code 2 (Health Boost), `LevelMin` 1 ≤ 29; no rewrite |

The shrine stores `interact` 2; `PreOperate` 0 and `Sync` 1 add no draw; its 3 × 3 mark is a logged CM line. Code 2,
so `healthShrines` becomes 1 and the position enters the shrine list (`nShrinePos` 1), as the next slot's logged counters
show. Slot 1 (group 15, barrels) follows from `S = 313512A0:21CB48CE`, `O = 5F3F7052:3A264FB6`. [C]
(fn:OBJPOP_Shrine@0x00552B50, fn:OBJ_PlaceByOrientation@0x00550A30, fn:OBJINIT_Shrine@0x0054F9D0, run:2026-10-15-objects)

### 3. A chest creation and its operate (Jail Level 1)

Same log. A DS1 preset chest, class 241 (`InitFn` 3, `Lockable` 1, `OperateFn` 4, `Mode1` 1), at (17580, 5073) in level
29, created in a presets window with `O = B894D7A0:5DCD3C69` and `G = 93DC1A62:2A937708`. With `MonLvl1` 10, the trap
chance is `10 ÷ 8 + 5 = 6` and the lock chance `10 ÷ 2 + 8 = 13`.

| # | Seed | After | Value | Meaning |
|---|---|---|---|---|
| G1 | G | `BD96E472` | — | unit seed `BD96E472:0000029A` |
| O1 | O | `27612A89` | 5 | trap roll: 5 < 6, trapped |
| O2 | O | `E2A59836` | 6 | trap type `RandLoHi(1, 9) = 1 + 6 = 7` |
| O3 | O | `B53D4896` | 74 | lock roll: 74 ≥ 13, not locked |
| O4 | O | `8F8998B3` | 47047 | re-seed: `v = 47047 + 1 = 0xB7C8`, unit seed `0000B7C8:0000029A` |

The chest holds `interact` 7. Later in the same game the player operates it, with `O = 01E3F721:3AAA3C21` at entry (the
stream has moved through other rooms, operates and timer events since):

| # | Seed | After | Value | Meaning |
|---|---|---|---|---|
| O5 | O | `B79FF886` | 74 | mode 0, not locked, no sparkle (`q = 0`): `r = 74 > 24` → one drop |
| — | unit | — | — | `ObjectChestDrop(0)`: tier 2, TC 387 `Act 1 Chest C`; `TC_ResolveDrops` draws the unit seed from `0000B7C8:0000029A` and makes no item (exit `9BFABC9C:61AE08E7`, logged; items/tc) |

The resolver leaves `O` at `B79FF886:00C9DBB6`; the chest goes to mode 1 (`Mode1` set) and trap type 7 fires (named
only). [C] (fn:OBJINIT_Chest@0x0054FCB0, fn:OBJINIT_TrapByte@0x0054FBB0, fn:OBJOP_Chest@0x00585F60,
fn:sub_00585B90_ObjectChestDrop@0x00585B90, run:2026-10-15-objects)

## Reimplementation notes

- **One object-region stream per game.** Do not seed it per room or per level. It starts at game-seed draw 2 and
  every theme roll, handler, `InitFn`, `PreOperate`, operate and timer event of the whole game advances it, so the
  order in which rooms activate and objects are operated changes every later object. [C] (fn:OBJRGN_GetSeed@0x00546FA0,
  run:2026-10-15-objects)
- **Draw every slot.** A group-0 slot and a failing slot each cost one room draw; a passing slot costs two even when
  the `PROB` sum leaves nothing. [C] (fn:sub_00552610_RoomObjectsPopulate@0x00552610, run:2026-10-14-objects-window)
- **Keep the forced-slot bug.** The rule reads `Objects[groupIndex].SubClass`, not a member's; testing the member (or
  the group's `SHRINES` flag) changes which slots are suppressed. [C] (0x005526CC, run:2026-10-15-objects)
- **`r ≤ ObjPrb`, `r2 < sum`, `P100 < 21`, `r ≤ 24`.** The comparisons differ by one between the slot test (`≤`), the
  member walk (`<`), the urn drop (`< 21`, so 21 %) and the empty chest (`≤ 24`, so 25 %). [C]
  (fn:sub_00552610_RoomObjectsPopulate@0x00552610, fn:OBJOP_Urn@0x005866C0, fn:OBJOP_Chest@0x00585F60, run:2026-10-15-objects)
- **Draws whose result is not used.** Each handler's `P100` against 100, `RandLoHi(S, 1, 2)` in the shrine placer
  (always 1), and the discarded `ShrinePick` of a forced conversion are all made. [C] for the first two
  (fn:OBJ_PlaceByOrientation@0x00550A30, run:2026-10-15-objects); [I] for the third (fn:OBJ_ShrineClassSubst@0x00552AC0)
- **`R(O, 0)` makes no draw.** The cluster ring steps with `step` 0 (urns, classes 208/209) draw only the direction.
  [C] (fn:RNG_RangeB@0x0045C3E0, fn:OBJPOP_Clusters@0x00550C20, run:2026-10-15-objects)
- **`Xspace`/`Yspace` are unsigned.** A negative `.txt` value is a step of 249..255 subtiles. [C]
  (tbl:Objects.txt:Xspace, fn:OBJPOP_Barrels@0x00551850, run:2026-10-15-objects)
- **`MonLvl1` in every difficulty, `LevelMin` against the level Id.** Neither is the difficulty's monster level. [C]
  (tbl:Levels.txt:MonLvl1, tbl:Shrines.txt:LevelMin, run:2026-10-15-objects)
- **A chest drops from its re-seeded unit seed, not from `O`.** The resolver never touches the object-region seed. [C]
  (fn:OBJINIT_Chest@0x0054FCB0, fn:TC_ResolveDrops@0x0055A6D0, run:2026-10-15-objects)
- **A revisit re-rolls and then overwrites.** The re-created object makes all its creation draws, but its saved
  `interact`, mode and sparkle win. [C] (fn:sub_00542B40_RoomInactiveUnitsRestore@0x00542B40, run:2026-10-15-objects)
- **The guide's numbers that 1.14d does not follow** (cross-check of objects/0001 § Leads used): urns drop at 21 %,
  not 20 %; gold piles are 1–9, not 1–10; a sparkle chest uses the act chest TC. [C] (run:2026-10-15-objects)

## Evidence

- [findings/objects/0001-object-population.md](../../findings/objects/0001-object-population.md): §§ 1–10 (the window,
  gate, slot loop, handlers, placement, creation, `InitFn`s, presets, operate, restore), § 11 (the boundary), § 12
  (Phase 2 results) and the cross-check in *Leads used*.
- [findings/objects/experiments.md § run:2026-10-15-objects](../../findings/objects/experiments.md#run2026-10-15-objects):
  29 logs, 142 540 checks, 0 mismatches; 1265 windows predicted, 316 populated rooms, 65 shrines, 609 containers,
  89 operated containers; the boundaries and the unreached cases.
- [findings/objects/experiments.md § run:2026-10-14-objects-window](../../findings/objects/experiments.md#run2026-10-14-objects-window):
  the room-seed replay of 22 older logs (2090 first activations, 1405 drawing windows).
- [findings/monsters/0002 § 9](../../findings/monsters/0002-room-population.md#9-boundary-decision-and-the-phase-2-logging-plan)
  and [findings/drlg/0005](../../findings/drlg/0005-collision.md): which oracles the run replaced and which stay.
- Tables: [Objects](../../tables/Objects.md), [ObjGroup](../../tables/ObjGroup.md), [Shrines](../../tables/Shrines.md),
  [ObjMode](../../tables/ObjMode.md), [Levels § Object population columns](../../tables/Levels.md#object-population-columns-plan-0023-phase-1).
- Types: `re/types/objects.h` (`ObjRgn`, `ObjRgnLevel`, `ObjectData`, `ObjCtx`, `ObjOpCtx`, `ObjGroupRec`).
- Upstream: [rng](../rng/README.md), [rng/seeds](../rng/seeds.md), [drlg/preset](../drlg/preset.md),
  [drlg/collision](../drlg/collision.md). Downstream: [monsters/spawn](../monsters/spawn.md) (the room seed at pass
  entry), [items/tc](../items/tc.md) and [items/quality](../items/quality.md) (the chest drop and its forced quality).

## Open questions

- [I] **Not reached by any run, so as read** (architect ruling (3), plan 0023 Phase 2): `PopulateFn` 5 (no stock level
  names a group with a crate member); `InitFn` 57 and 58 and the class-397 operate table; the casket after it made an
  item; the shrine and well caps; the forced conversion of a placed shrine; the fixed-shrine pseudo-objects 574–579
  (no stock DS1 places them); the theme handlers. (fn:OBJPOP_Crates@0x00551C00, fn:OBJINIT_SparklyChest@0x0054FD90,
  fn:OBJOP_Casket@0x00586410, fn:OBJRGN_ShrineCapReached@0x00547360, fn:OBJ_PresetFixedShrine@0x0054F0D0)
- [L] **Object marks are not fed to the collision model.** The marks of the objects this spec creates, and the
  `COLL_WHTest` results at the seven object call sites, are logged values in run:2026-10-15-objects; a run that feeds
  the predicted marks into [drlg/collision](../drlg/collision.md) and predicts the test results is still to do
  (reverser, [backlog](../../backlog.md)).
- [L] **Unread operate handlers.** The run saw other `OperateFn`s (doors, waypoints and the like) taken as oracles; the
  finding names only 1, 3, 4, 5, 19 and 20. Whether any other operate handler draws the object-region seed is not
  stated ([backlog](../../backlog.md), reverser).
- [L] **Details the finding does not spell out:** which size the follower test of handler 1 uses; the margin test of
  `OBJ_PlaceByOrientation` for orientations 1 and 2 (the run's calls at its call site used a box `SizeX + 6` and mask
  `0x3F11`); the `(0 → 1)` mapping noted for `ShrinePick` and the outcome when its 8 tries all fail `LevelMin`; the
  order of the 580 handler's sparkle draw relative to the chest's creation draws; the order in which a revisit
  re-creates saved objects ([backlog](../../backlog.md), reverser).
- [L] Which code, if any, reads Objects `TrapProb`, `SpawnMax`, `Act` and the zero byte ranges; the `InitFn` callee
  scan stopped at depth 3 ([objects/0001 § Open questions](../../findings/objects/0001-object-population.md#open-questions)).
- [L] How the resolver applies a forced quality to a TC entry that is gold or a potion (a sparkle chest passes one on
  every drop); owner [items/tc](../items/tc.md).
- [L] **Unreachable contradictions of the cross-check** (precedent: `sparsePopulate`, plan 0014): `DENSITY` 128 is
  fatal (`cmp bl, 0x80; jae` at `0x005527CE`) where src:d2dfg-blizzard allows it; a shrine row with `Parm0` 0 makes a
  uniform pick over all codes where the guide says health shrine. Only modified data reaches either.
- [L] Multiplayer games were not logged; quest-state objects (582, Zoo, the quest `InitFn`s) stay inputs.
