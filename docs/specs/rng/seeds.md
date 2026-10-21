---
spec: rng/seeds
status: reviewed
target: Diablo II LoD 1.14d, Game.exe sha256 631066c1649c4ea9…
depends_on: [rng]
consumed_by: [drlg/overview, drlg/room-tiles, drlg/*, monsters/spawn, objects, items/*]
tags: {C: 80, I: 13, L: 4}
updated: 2026-10-21
---

# Seed tree: game → act → level → room → unit

## Purpose

Defines where each seed object is created and what its initial value is, from the game root down
to the units of a game. With a fixed map seed, this chain fixes every act's and level's starting
seed, and therefore the inputs of the DRLG generators. Two roots exist: the **map seed** feeds
acts, levels and rooms, and the **game seed** feeds server units. What happens *inside* item
creation, monster spawning and the DRLG room-type code is left to those specs. Primitives (`Step`,
`Range`, `Init`, `InitOne`) are defined in [README.md](README.md).

## Entry points

| When | Function | Tag |
|---|---|---|
| Game created | fn:GAME_InitSeeds@0x0052C280 | [C] |
| `-seed N` on the command line, or `D2.ini` | fn:sub_0044D860_ApplySeedOption@0x0044D860 → fn:GAME_SetSeedOverride@0x0052C320 | [C] |
| Act created, server copy | fn:sub_0053AC70_ActCreate@0x0053AC70 → fn:DUNGEON_ActCreate@0x006194A0 → fn:DRLG_ActCreate@0x00642DA0 | [C] |
| Act created, client copy | client message handler 3 fn:sub_0045C8E0_PktLoadAct@0x0045C8E0 → fn:sub_0044E100_ClientActLoad@0x0044E100 → fn:DUNGEON_ActCreate@0x006194A0 | [C] |
| Level created | fn:DRLG_LevelCreate@0x00642AE0, from `DRLG_ActCreate` or one of six get-or-create callers | [C] |
| DRLG room created | fn:DRLG_RoomCreate@0x0066B3E0 | [C] |
| Room activated | fn:sub_0061B190_RoomActivateA@0x0061B190 or fn:sub_0061B730_RoomActivateB@0x0061B730 → fn:sub_0066EE40_DrlgRoomReseed@0x0066EE40 → fn:DRLG_RoomActivate@0x006422A0 → fn:DUNGEON_RoomCreate@0x00619890 | [C] |
| Server unit created (every type but players) | fn:sub_00555230_SUnitCreate@0x00555230 → fn:sub_00552DF0_UnitSeedInit@0x00552DF0 | [C] |
| Client unit created | fn:sub_00465FD0_UnitInit@0x00465FD0, fn:sub_00466200_UnitInitB@0x00466200 | [C] |

## Inputs

### Tables

| Anchor | Used for |
|---|---|
| tbl:Levels.txt:Id | level IDs 66–72 are the seven Act II Tal Rasha tombs, the range of the Act II draw (step 3c) |
| tbl:Levels.txt:DrlgType | generator dispatch after the level seed is set (step 4) |

### Runtime state

Owner names are ours, taken from the source path each allocation passes to the allocator
(`Drlg.cpp`, `Dungeon.cpp`, `DrlgRoom.cpp`, `SUnit.cpp`, `CUnit.cpp`). Offsets are byte offsets into
the owner. No struct in `re/types/` exists yet.

| Seed / value | Type | Owner offset | Source |
|---|---|---|---|
| game seed | `Seed` | game `+0xD0` | step 1 |
| map seed | `u32` | game `+0x7C` | step 1 |
| override flag | `u32` | game `+0x84` | step 1 |
| seed option | `i32`, 4-byte slot | config `+0x21A` | step 2 |
| seed override | `u32`, `0xFFFFFFFF` = none | data:g_SeedOverride@0x00731004 | step 2 |
| act seed | `Seed` | DRLG act `+0x000` | step 3 |
| act map seed copy | `u32` | DRLG act `+0x458` | step 3 |
| level seed base | `u32` | DRLG act `+0x470` | step 3 |
| act index | `u8`, 0-based | DRLG act `+0x480` | step 3 |
| level seed | `Seed` | level `+0x1C4` | step 4 |
| DRLG room seed | `Seed` | DRLG room `+0x14` | steps 5, 6 |
| DRLG room first draw | `u32` | DRLG room `+0x04` | step 5 |
| DRLG room type | `u32` | DRLG room `+0x48` | step 6 |
| `RoomTile` record | pointer | DRLG room `+0x54` | step 6 |
| active room seed | `Seed` | active room `+0x6C` | step 6 |
| active room flags | `u32` | active room `+0x34` | step 6 |
| unit seed | `Seed` | unit `+0x20` | step 7 |
| unit initial seed value | `u32` | unit `+0x28` | step 7 |

### Constants

| Name | Value | Anchor | Tag |
|---|---|---|---|
| no-override sentinel | `0xFFFFFFFF` (`−1`), the initial value of `g_SeedOverride` | data:g_SeedOverride@0x00731004; `.data` bytes and the compare at 0x0052C28B, one write (0x0052C326), [rng/0002 § Plan 0038 batch S1b](../../findings/rng/0002-seed-tree.md#plan-0038-batch-s1b-2026-10-16) | [C] |
| entropy LCG multiplier | `0x19660D` | fn:RNG_EntropySeed@0x00650DE0 | [C] |
| entropy LCG increment | `0x3C6EF35F` | fn:RNG_EntropySeed@0x00650DE0 | [C] |
| first tomb level ID | `66` | fn:DRLG_ActCreate@0x00642DA0, tbl:Levels.txt:Id | [C] |

## Algorithm

```mermaid
flowchart TD
    game["game.mapSeed (step 1)<br/>entropy, or -seed N"]
    gseed["game.seed (step 1)"]
    sact["server act (step 3)<br/>act.seed = Init(mapSeed)"]
    cact["client act (step 3)<br/>same mapSeed, sent by message 3"]
    lvl["level.seed = Init(levelSeedBase + levelId)<br/>sum, no draw (step 4)"]
    room["DRLG room.seed (step 5)<br/>one level draw"]
    reseed["room.seed = Init(room+0x04)<br/>then k room-type draws (step 6)"]
    aroom["active room.seed (step 6)<br/>one DRLG-room draw, if RoomTile test passes"]
    sunit["server unit.seed (step 7a)<br/>one game-seed draw"]
    cunit["client unit.seed (step 7b)<br/>one active-room draw, if (x, y) ≠ (0, 0)"]
    game --> sact
    game --> cact
    sact --> lvl
    cact --> lvl
    lvl -->|"Step(level.seed)"| room
    room --> reseed
    reseed -->|"Step(room.seed)"| aroom
    aroom -->|"client rooms only"| cunit
    gseed -->|"draw 1"| mreg["monster regions<br/>MonRegionsInit (step note 7a)"]
    gseed -->|"draws 2, 3, 4"| gc["object regions, store seed,<br/>quest seed (step note 7a)"]
    gseed -->|"Step(game.seed)"| sunit
```

```mermaid
---
title: Steps 1–2, the two roots
---
flowchart TD
  opt["config +0x21A, from -seed or D2.ini"] --> nz{"v ≠ 0?"}
  nz -->|yes| ov["g_SeedOverride = v as u32"]
  nz -->|no| keepov["g_SeedOverride unchanged"]
  ov & keepov --> t{"g_SeedOverride = 0xFFFFFFFF?"}
  t -->|"yes: clock path"| e1["overrideFlag = 0<br/>Init(game.seed, EntropySeed(QPC low))"]
  e1 --> e2["Step(game.seed), game draw 1"]
  e2 --> e3["mapSeed = EntropySeed(game.seed.low)"]
  t -->|"no: override"| o1["overrideFlag = 1<br/>mapSeed = override"]
  o1 --> o2["Init(game.seed, override)<br/>no draw"]
```

```mermaid
---
title: Step 3, act seed draws
---
flowchart TD
  a["Init(act.seed, mapSeed)"] --> b["Step, levelSeedBase = act.seed.low"]
  b --> idx{"actIndex"}
  idx -->|"1, Act II"| p["two Steps, a = low mod 7, b = low mod 7"]
  p --> eq{"a = b?"}
  eq -->|yes| p
  eq -->|no| tomb["act +0x094 = a + 66<br/>act +0x484 = b + 66"]
  idx -->|"2, Act III"| a3["Step, act +0x474 = low and 1"]
  idx -->|other| d3
  tomb & a3 --> d3["3d: data-dependent link draws<br/>after levelSeedBase is taken"]
```

```mermaid
---
title: Steps 4–6, level to active room
---
sequenceDiagram
  participant LC as DRLG_LevelCreate
  participant LS as level.seed
  participant RC as DRLG_RoomCreate
  participant RS as DRLG room.seed
  participant RA as room activation
  participant AS as active room.seed
  LC->>LS: Init(levelSeedBase + levelId), a u32 sum, no draw
  loop each DRLG room, in creation order
    RC->>LS: Step, one level draw
    RC->>RS: Init(level.seed.low), Step, store low at +0x04
  end
  RA->>RS: 6a Init(+0x04), earlier draws discarded
  RA->>RS: 6b room-type code, Step k times
  alt RoomTile has a wall or floor tile
    RA->>RS: 6c Step, one DRLG-room draw
    RA->>AS: Init(room.seed.low)
  else no tiles
    Note over RA: no draw, no active room
  end
```

```mermaid
---
title: Step 6, DRLG room bit 0x100000
---
stateDiagram-v2
  direction LR
  bitClear: bit 0x100000 clear
  bitSet: bit 0x100000 set
  [*] --> bitClear
  bitClear --> bitSet: 6b room-type code
  bitSet --> bitSet: RoomActivateB skips 6a to 6c
```

```mermaid
---
title: Step 7, unit seeds
---
flowchart TD
  su["server unit, SUnitCreate"] --> ty{"type = 0, player?"}
  ty -->|yes| skip["no call here"]
  ty -->|no| g1["Step(game.seed)<br/>unit.seed = Init(game.seed.low)"]
  g1 --> it{"type = 4, item?"}
  it -->|yes| g2["one more Step(game.seed)"]
  cu["client unit, UnitInit"] --> xy{"x ≠ 0 or y ≠ 0,<br/>and a client room at x, y?"}
  xy -->|yes| r1["Step(active room.seed)<br/>unit.seed = Init(room.seed.low)"]
  xy -->|no| r0["unit.seed stays InitOne: 1, 666"]
```

```
1. CreateGameSeeds(game):                                         [C] (fn:GAME_InitSeeds@0x0052C280, run:2026-10-11-seed-tree, run:2026-10-11-seed-tree-p1)
     if g_SeedOverride = 0xFFFFFFFF:
       game.overrideFlag ← 0
       InitOne(game.seed)
       Init(game.seed, EntropySeed(salt: QPC low dword))
       Step(game.seed)                                            ; game draw#1
       game.mapSeed ← EntropySeed(salt: game.seed.low)
     else:
       game.overrideFlag ← 1
       game.mapSeed ← g_SeedOverride
       InitOne(game.seed)
       Init(game.seed, g_SeedOverride)                            ; no draw

   EntropySeed(salt: u32) → u32:                                  [C] (fn:RNG_EntropySeed@0x00650DE0, 0x00650DF6–0x00650E1C, run:2026-10-11-seed-tree-p1)
     x: u32 ← GetTickCount() + _time32(NULL) + salt               ; every operation wraps mod 2^32
     repeat 3 times: x ← x × 0x19660D + 0x3C6EF35F
     return x & 0x7FFFFFFF                                        ; 31-bit result

2. ApplySeedOption(config):                                       [C] (fn:sub_0044D860_ApplySeedOption@0x0044D860, fn:GAME_SetSeedOverride@0x0052C320, run:2026-10-11-seed-tree-p1)
     v: i32 ← config[+0x21A]                                      ; option {DEBUG, SEED, seed}, type 1 (integer)
                                                                  ; filled by atol(text) from -seed, the text
                                                                  ; cut at the next '-' (step note 2), or
                                                                  ; GetPrivateProfileIntA from D2.ini
     if v ≠ 0: g_SeedOverride ← (u32) v                           ; 0 is never applied

3. CreateAct(actIndex: u8, mapSeed: u32) → act:                   [C] (fn:DRLG_ActCreate@0x00642DA0, run:2026-10-11-seed-tree)
   3a. Init(act.seed, mapSeed);  act.mapSeedCopy ← mapSeed
   3b. Step(act.seed)                                             ; act draw#1
       act.levelSeedBase ← act.seed.low                           ; +0x470
   3c. if actIndex = 1:                                           ; Act II (index is 0-based)
         repeat:
           Step(act.seed);  a: u32 ← act.seed.low mod 7          ; act draw#2k,   unguarded
           Step(act.seed);  b: u32 ← act.seed.low mod 7          ; act draw#2k+1, unguarded
         until a ≠ b
         act[+0x094] ← a + 66;  act[+0x484] ← b + 66
       else if actIndex = 2:                                      ; Act III
         Step(act.seed)                                           ; act draw#2
         act[+0x474] ← act.seed.low & 1
   3d. further act-seed draws inside DRLG_ActCreate,             [C] (fn:sub_00678AD0_ActLinkInit@0x00678AD0, fn:sub_006772C0_LevelLinkBuild@0x006772C0, run:2026-10-16-sweep-roomk)
       data-dependent; see step note 3
   The mapSeed argument is game.mapSeed for every act, and every [C] (fn:sub_0053AC70_ActCreate@0x0053AC70, fn:sub_0044E100_ClientActLoad@0x0044E100, run:2026-10-11-seed-tree-p1)
   act is created twice with it: a server copy and a client copy.

4. CreateLevel(act, levelId: u32) → level:                        [C] (fn:DRLG_LevelCreate@0x00642AE0, 0x00642B50, run:2026-10-11-seed-tree)
     Init(level.seed, (u32) (act.levelSeedBase + levelId))        ; a u32 sum that wraps, NOT a draw
     dispatch on Levels[levelId].DrlgType:                        [C] (fn:DRLG_LevelCreate@0x00642AE0, tbl:Levels.txt:DrlgType, run:2026-10-12-drlg-gen)
       1 → 0x00673B10 (maze), 2 → 0x00667430 (preset), 3 → 0x00675320 (outdoors)
     rooms come later, after LevelInit re-seeds the level with the same value:
     see drlg/overview (../drlg/README.md) steps 1–2

5. CreateDrlgRoom(level, type: u32) → room:                      [C] (fn:DRLG_RoomCreate@0x0066B3E0, run:2026-10-11-seed-tree)
     Step(level.seed)                                             ; one level draw
     Init(room.seed, level.seed.low)
     Step(room.seed)                                              ; room draw#1
     room[+0x04] ← room.seed.low
     dispatch on type: 1 → 0x0067D6D0, 2 → 0x00666630, else none [C] (fn:sub_0067D6D0_OutRoomAlloc@0x0067D6D0, fn:sub_00666630_PresetRoomAlloc@0x00666630, 0x0066B479–0x0066B4A8, run:2026-10-11-seed-tree)
                                                                  ; allocation only, no draw: an objdump closure
                                                                  ; with no drawing function, 876 type-1 and
                                                                  ; 3552 type-2 rooms (rng/0002 § Plan 0038 batch S1b);
                                                                  ; its 532 indirect calls: 359 import table, 115
                                                                  ; register from it, 58 under 0x0040B430 (step 5 note)

6. ActivateRoom(act, R: DRLG room) → activeRoom or none:          [C] (fn:sub_0061B190_RoomActivateA@0x0061B190, fn:sub_0061B730_RoomActivateB@0x0061B730, run:2026-10-11-seed-tree-p1)
   6a. Init(R.seed, R[+0x04])                                     [C] (fn:sub_0066EE40_DrlgRoomReseed@0x0066EE40, run:2026-10-11-seed-tree-p1)
                                                                  ; re-seed: earlier room-seed draws are discarded
   6b. room-type code for R[+0x48] (1 → 0x0067D2D0, 0x0067D710;  [C] (fn:sub_0066EE40_DrlgRoomReseed@0x0066EE40, fn:sub_0066EE70_DrlgRoomTypeInit@0x0066EE70, run:2026-10-11-seed-tree-p1)
       2 → 0x006667D0, 0x00666AC0); sets R[+0x28] |= 0x100000
       Step(R.seed) k times                                       ; k: drlg/room-tiles § k (../drlg/room-tiles.md#k)
   6c. DRLG_RoomActivate(act, R):                                 [C] (fn:DRLG_RoomActivate@0x006422A0, fn:DUNGEON_RoomCreate@0x00619890, run:2026-10-11-seed-tree-p1)
         T ← R[+0x54]                                             ; RoomTile record
         if T[+0x18] = 0 and T[+0x20] = 0:
           return none                                            ; no draw, no active room
         flags: u32 ← 4 if R[+0x28] & 0x40000                     [C] (fn:DRLG_RoomActivate@0x006422A0, run:2026-10-16-sweep-roomk)
                      else 1 if R[+0x60] & 1
                      else 0
         Step(R.seed)                                             ; one DRLG-room draw (inlined)
         Init(activeRoom.seed, R.seed.low)                        ; +0x6C
         activeRoom[+0x34] ← flags

7a. ServerUnitSeed(game, unit, type: u32):                       [C] (fn:sub_00555230_SUnitCreate@0x00555230, fn:sub_00552DF0_UnitSeedInit@0x00552DF0, 0x00555306, run:2026-10-11-seed-tree-p1)
     if type = 0: return                                          ; players: see step note 7a
     InitOne(unit.seed)
     Step(game.seed)                                              ; one game-seed draw
     unit[+0x28] ← game.seed.low
     Init(unit.seed, game.seed.low)
     if type = 4:                                                 ; items
       Step(game.seed)                                            ; one more game-seed draw [C] (fn:sub_00552E90_ItemSeedInit@0x00552E90, run:2026-10-11-seed-tree-p1)
                                                                  ; its low word is the item's start seed,
                                                                  ; item.seed = {low, 666} (items/uniques-sets A2)

7b. ClientUnitSeed(unit, x: i32, y: i32):                        [C] (fn:sub_00465FD0_UnitInit@0x00465FD0, fn:sub_00466200_UnitInitB@0x00466200, run:2026-10-11-seed-tree-p1)
     room ← none
     if x ≠ 0 or y ≠ 0:                                           ; literal predicate: the two position
       room ← the client act's active room at (x, y)              ; arguments are not both zero
                                                                  [C] (0x00466027, fn:sub_00465420_ClientRoomAt@0x00465420, run:2026-10-16-sweep-roomk)
     InitOne(unit.seed)
     if room ≠ none:
       Step(room.seed)                                            ; one active-room draw
       unit[+0x28] ← room.seed.low
       Init(unit.seed, room.seed.low)
```

Step notes:

1. Without an override, both the game seed and the map seed depend on the tick count, the clock
   and the performance counter, so they can't be reproduced. A reimplementation that wants
   determinism takes the override branch. [C] (fn:RNG_EntropySeed@0x00650DE0, run:2026-10-11-seed-tree-p1)
2. `config+0x21A` is a 4-byte signed integer slot: the next option's slot starts at `+0x21E`, and
   the reader loads it as one dword. A `-seed` value wider than 16 bits arrives intact (`34844169` →
   `+0x7C = 0x0213AE09`). [C] (fn:sub_004058A0_ConfigParseCmdLine@0x004058A0,
   fn:sub_00405450_ConfigLoadIni@0x00405450, run:2026-10-11-seed-tree) On the command line, a
   negative value never arrives: the parser copies a switch's text only up to the next `-`
   (`0x00405784`), so `-seed -2147483648` (and `-seed -1`) leaves the text empty, `atol` gives 0,
   step 2 applies nothing, and the game takes the clock path. A value of 2³¹ or more saturates at
   `0x7FFFFFFF`. So the seeds reproducible from the command line are `1`…`0x7FFFFFFF`, and no seed of
   `0x80000000` or above reaches step 1 that way. [C] (fn:sub_004058A0_ConfigParseCmdLine@0x004058A0,
   0x00405710, fn:GAME_InitSeeds@0x0052C280, run:2026-10-16-sweep-roomk, sessions s9 and s10;
   [rng/0002 § Plan 0038 batch H5c](../../findings/rng/0002-seed-tree.md#plan-0038-batch-h5c-run2026-10-16-sweep-roomk)) This corrects the earlier reading that a seed ≥ 2³¹ could be given as its negative
   decimal, which the run contradicted. What the `D2.ini` route stores for such values is open (*Open
   questions*).
3. All acts of one game get the same map seed, so all acts share the same `levelSeedBase`.
   Act-specific draws (3c, 3d) come after `levelSeedBase` is taken and don't change it. [C]
   (fn:DRLG_ActCreate@0x00642DA0, run:2026-10-11-seed-tree) The Act II loop draws two distinct tomb
   level IDs in 66–72. Which of the two fields is the real tomb is open. [C] (tbl:Levels.txt:Id,
   run:2026-10-11-seed-tree) Step 3d: the level-link setup copies the act seed into a local
   link-builder struct, and the link callbacks step **the copy**, which is then discarded. The act
   seed itself is stepped only by the level-link builder when its loop reaches level 6 with link
   value 1 or 3, and by the Act III link code. [C] (fn:sub_006772C0_LevelLinkBuild@0x006772C0,
   0x00677493–0x006774F9, run:2026-10-16-sweep-roomk: the act model equals the logged act seed on all 42
   act creations, Acts I–V, and no other code stepped an act seed; [rng/0002 § Plan 0038 batch H5c](../../findings/rng/0002-seed-tree.md#plan-0038-batch-h5c-run2026-10-16-sweep-roomk)) Observed act-seed steps after 3c: Act I 0 (seed 12345) and 1 (seed 777),
   Act III 119 (seed 12345), Acts II, IV and V 0. [C] (run:2026-10-11-seed-tree) These draws matter
   only to later consumers of the act seed, never to level seeds.
   Server copy: `sub_0053AC70_ActCreate` passes `game+0x7C`. Client copy: `sub_0044E100_ClientActLoad`
   gets the map seed from the 12-byte message 3 (act `u8 +1`, map seed `u32 +2`) and stores the act
   in `0x007A0634`. On game entry both are created, server first, with seed N. [C]
   (fn:sub_0045C8E0_PktLoadAct@0x0045C8E0, data:g_ClientPktHandlers@0x007114D0, run:2026-10-11-seed-tree-p1)
   The two copies have identical DRLG seed trees up to room activation (step 6). [C] (run:2026-10-11-seed-tree,
   run:2026-10-11-seed-tree-p1)
4. A level's seed depends only on the map seed and the level ID, never on the order in which levels
   are built or on which caller builds them. Besides `DRLG_ActCreate`, six functions get a level by
   ID and create it only if it is absent from the act's list. [C] for the sum
   (run:2026-10-11-seed-tree, 197 level creations). [C] for three of the six callers, logged by return
   address with no level id created twice in one act: `LevelEnsure` 346, `LevelUnloadCheck` 29,
   `LevelAddRef` 5 (fn:sub_00642BB0_LevelEnsure@0x00642BB0, fn:sub_00643060_LevelUnloadCheck@0x00643060,
   fn:sub_00642F70_LevelAddRef@0x00642F70, run:2026-10-16-sweep-roomk, [rng/0002 § Plan 0038 batch H5c](../../findings/rng/0002-seed-tree.md#plan-0038-batch-h5c-run2026-10-16-sweep-roomk)). [I] for the
   other three, which no run reached (fn:sub_00642BE0_LevelRoomCount@0x00642BE0,
   fn:sub_00642C30_RoomFromCoords@0x00642C30, fn:sub_00642D10_LevelSetPosition@0x00642D10)
5. Each DRLG room takes exactly one draw from its level's seed, so the order in which a level's
   rooms are created matters. [C] (fn:DRLG_RoomCreate@0x0066B3E0, run:2026-10-11-seed-tree, 3102 room creations)
   The type dispatch after the room draw draws nothing: the objdump closure under the two allocators (422 functions)
   holds no drawing function. Its 532 indirect calls split as 359 through the import table, 115 through a register
   whose nearest earlier write is a load from the import table, and 58 left, all under the pool allocator
   0x0040B430 (file and line arguments, fatal on failure), which is passed no seed pointer; 0 are unresolved. That
   residue is the closure's stated limit. [C] (fn:sub_0067D6D0_OutRoomAlloc@0x0067D6D0,
   fn:sub_00666630_PresetRoomAlloc@0x00666630, run:2026-10-11-seed-tree, [rng/0002 § Plan 0038 batch S1b](../../findings/rng/0002-seed-tree.md#plan-0038-batch-s1b-2026-10-16))
   `tools/sweep_s1b.py seeds` counts the logged activation re-seeds whose seed is the room's creation seed: 132 of 132
   type-2 re-seeds and 0 of 25 type-1. [I] (fn:sub_0066EE40_DrlgRoomReseed@0x0066EE40,
   [rng/0002 § Plan 0038 batch S1b](../../findings/rng/0002-seed-tree.md#plan-0038-batch-s1b-2026-10-16), tool addendum)
6. The active-room seed is `Init(Step^(k+1)(Init(R[+0x04])).low)`. It doesn't depend on any draw
   made on the room seed between creation and activation, because 6a restarts it from `+0x04`, but
   it does depend on k. Observed in that run: k = 50–376 over 157 activations. [C]
   (run:2026-10-11-seed-tree-p1) k is the number of room-seed draws of the `LvlSub` substitutions (type 1
   only) and of the tile picks whose candidates have a positive rarity sum, plus rare oracle draws; it
   is defined in [drlg/room-tiles § k](../drlg/room-tiles.md#k), which predicts it for all 520
   activations of its run (k = 0–388). [C] (fn:sub_0066EE70_DrlgRoomTypeInit@0x0066EE70,
   run:2026-10-11-drlg-roomk) `T[+0x18]`/`T[+0x20]` are the room's wall and floor tile counts after the
   build: 2066 activations equal the model's counts, and 5 exceed it by animation frames. [C]
   (fn:DRLG_RoomActivate@0x006422A0, run:2026-10-16-sweep-roomk, [rng/0002 § Plan 0038 batch H5c](../../findings/rng/0002-seed-tree.md#plan-0038-batch-h5c-run2026-10-16-sweep-roomk)) So 6c draws iff the
   room got at least one wall or floor tile; a room with neither did not occur in any run, so that
   return is not observed. [I] (fn:DRLG_RoomActivate@0x006422A0, [drlg/room-tiles](../drlg/room-tiles.md)
   step note 12)
   `sub_0061B730_RoomActivateB` runs 6a–6c only while `R[+0x28]` bit `0x100000` is clear, the bit 6b
   sets. [C] (fn:sub_0061B730_RoomActivateB@0x0061B730, run:2026-10-11-seed-tree-p1) `flags` bit 0
   marks the active room as already populated: the population pass runs only for rooms whose bit 0
   is clear. [C] (fn:sub_0052D160_NewRoomsUpdate@0x0052D160, 0x0052D1C9, run:2026-10-16-sweep-roomk:
   2072 room-driver tests with bit 0 set, none followed by a pass; each of the 558 passes followed a test
   with bit 0 clear; [rng/0002 § Plan 0038 batch H5c](../../findings/rng/0002-seed-tree.md#plan-0038-batch-h5c-run2026-10-16-sweep-roomk)) In the earlier runs every
   server-act room got `flags` 0 and every client-act room got 4. [C] (run:2026-10-11-seed-tree-p1)
   **`R[+0x28]` bit `0x40000` marks a room of the client act copy.** Its only writer is `DRLG_RoomCreate`, when the
   level's `+0x04` has bit `0x10`; `DRLG_LevelCreate` sets that bit when the act's `+0x8C` bit 0 is set, and
   `DUNGEON_ActCreate` passes 1 there for the client copy and 0 for the server copy. Second source: the flags rule held
   on all 2071 activations of run:2026-10-16-sweep-roomk (1332 with flags 4). [C] (0x0066B47C, 0x00642B3D, 0x006194F5,
   fn:DRLG_RoomCreate@0x0066B3E0, fn:DRLG_LevelCreate@0x00642AE0, fn:DUNGEON_ActCreate@0x006194A0,
   run:2026-10-16-sweep-roomk, [rng/0002 § Plan 0039 batch P1a](../../findings/rng/0002-seed-tree.md#plan-0039-batch-p1a-2026-10-16))
   **`R[+0x60]` bit 0 is the "already populated" bit kept across a release.** It is 0 at creation;
   `RoomReleaseWrap` stores the released active room's `flags` bit 0 there, and `LevelRoomStateRestore` ORs it back
   from the array `LevelUnload` saved. So a room populated, released (or unloaded) and activated again comes back with
   `flags` 1 and is not populated a second time. Second source: run:2026-10-16-sweep-roomk (1516 releases all through
   the wrapper with `+0x60` = the active room's bit 0; 25 restores setting the bit on 90 rooms). [C] (0x0066B419,
   0x0066B4D7, 0x006423C0, fn:sub_0066B4C0_RoomReleaseWrap@0x0066B4C0, fn:sub_00642390_LevelRoomStateRestore@0x00642390,
   run:2026-10-16-sweep-roomk, [rng/0002 § Plan 0039 batch P1a](../../findings/rng/0002-seed-tree.md#plan-0039-batch-p1a-2026-10-16))
   **The server and client copies of one DRLG room can get different active-room seeds**, because
   their k can differ: of the 9 rooms activated in both copies, 6 (seed 12345) and 8 (seed 777) got
   different seeds. Gameplay uses the server copy. [C] (run:2026-10-11-seed-tree-p1) The cause is the
   bit-2 tile path, which reads the neighbours already built in that act copy, so k depends on the
   activation order. [C] (fn:sub_0066E580_NeighbourTileScan@0x0066E580, run:2026-10-11-drlg-roomk)
   On the server, every room of a new-rooms walk gets one wanderer-tick draw on its active-room seed, and
   on its first activation the DS1 presets, the object population and then the population pass follow.
   The pass draws its class picks, type roll and every position from the active-room seed, and its density
   rolls, the `sparsePopulate` roll and one step per creation from the game seed
   ([monsters/spawn](../monsters/spawn.md)). [C] (fn:sub_0054EC90_RoomPopulate@0x0054EC90,
   fn:sub_0054F060_RoomWandererTick@0x0054F060, run:2026-10-13-mon-spawn) The `0x005BDFF0` room-seed step it
   contains is on the type-1 branch, which never runs: the pass maps type 1 to 2. [C]
   (fn:sub_005BDFF0_ARoomSeedStep@0x005BDFF0, 0x0054EE0B, run:2026-10-13-mon-spawn)
7a. **Server units, monsters included, seed from the game seed `+0xD0`, not from a room.** [C]
   (run:2026-10-11-seed-tree-p1: 114 server unit seeds, parent always `game+0xD0`, type 1 units among them)
   `SUnitCreate` skips the call for type 0. `UnitSeedInit` has five other callers (player creation
   and re-seeding paths), each passing its own pointer plus `0xD0`, and the type-0 (player) server units
   of the runs got their seed from `game+0xD0` through them. [C] (0x0053254E, 0x005338D8, 0x00569F53,
   0x0056A95E, 0x0057F7E5; objdump pins and a raw caller scan, run:2026-10-11-seed-tree-p1, [rng/0002 § Plan 0038 batch S1b](../../findings/rng/0002-seed-tree.md#plan-0038-batch-s1b-2026-10-16))
   Which of the five ran, and that the pointer each of the other four adds `0xD0` to is the game, are
   not established. [I] (fn:sub_00552DF0_UnitSeedInit@0x00552DF0) At runtime the player's seed is the 5th game-seed draw from `Init(N)`, and the starting
   items follow at draws 6, 8, 10…, two draws each. [C] (run:2026-10-11-seed-tree-p1) Other consumers
   of the game seed draw in between, so a unit's seed depends on the full call order of every
   game-seed consumer. Draw 1 from `Init(N)` is the monster-region build: `sub_00547D20_MonRegionsInit`
   steps the game seed once, keeps the low word at `game+0xEC` and builds every level's pool from a
   local seed `Init(low)` (see [monsters/pool](../monsters/pool.md)). [C]
   (fn:sub_00547D20_MonRegionsInit@0x00547D20, fn:sub_00530BF0_GameCreate@0x00530BF0, run:2026-10-12-mon-pool)
   The game-creation calls after it, in `sub_00530BF0_GameCreate`'s call order, take one game-seed draw each,
   so draws 2–4 are fixed. [C] (fn:sub_00530BF0_GameCreate@0x00530BF0, run:2026-10-15-objects,
   run:2026-10-15-vendors, run:2026-10-16-quest-drops, [rng/0002 § Other seed sites](../../findings/rng/0002-seed-tree.md#other-seed-sites-seen-not-yet-followed))
   The object region takes exactly draw 2: `OBJRGN_Create` steps the game seed once and seeds the game-wide
   object-region seed with `Init(low)` ([objects § A](../objects/README.md#a-the-object-region-seed-and-level-records-game-creation)). [C]
   (fn:OBJRGN_Create@0x00546C60, run:2026-10-15-objects)
   **Stored item seeds.** `ItemCreate` replaces the unit seed and the item-data seed with `Init(rec+0x48)` and
   `Init(rec+0x4C)` only when its third argument or `rec+0x2C` is non-zero. Of its 20 call sites, 19 (drops, gold, the
   store, the cube output, the imbue, objects, traps, the missile drop) pass 0 on a zeroed record, so their seeds come
   from the game seed as above. The one that sets `+0x2C` is `ItemCreateFromOldRec`, reached only from the version-`0x47`
   item-list reader of the save readers; a current save restores its items through `ItemCreateFromSave`, which does not
   call `ItemCreate`. So only an item read from an old (version-`0x47`) item list keeps stored seeds this way. [I]
   (0x00558E47–0x00558E79, fn:sub_00558D90_ItemCreate@0x00558D90, fn:sub_00530F40_ItemCreateFromOldRec@0x00530F40,
   fn:sub_005337F0_ItemListReadByVersion@0x005337F0, fn:sub_00558CB0_ItemCreateFromSave@0x00558CB0,
   [rng/0002 § Plan 0039 batch P1a](../../findings/rng/0002-seed-tree.md#which-item-creations-pass-seeds-0x480x4c))
   Draw 3 is `NPCSTORE_CtlCreate`: it seeds the store seed, which is also the hirelings' NPC seed, with `Init(low)`
   ([items/vendors](../items/vendors.md) A1). [C] (fn:NPCSTORE_CtlCreate@0x00536070, run:2026-10-15-vendors,
   run:2026-10-16-hirelings)
   Draw 4 is `QUESTS_InitGame`: it seeds the quest seed `QuestControl+0x18` with `Init(low)`
   ([items/quest-drops](../items/quest-drops.md) A1); in all 53 games of its run the game seed at its entry was three
   steps past `Init(N)`. [C] (fn:QUESTS_InitGame@0x00545D80, run:2026-10-16-quest-drops)
   The rest of the order belongs to the item, monster and object specs. A monster created by the
   population pass carries a unit seed 2 steps past `Init(game.seed.low)` by the time the pass draws on it
   (914 of 916 logged creations; 6 and 15 on the other two); the steps happen inside `SUnitCreate`, and
   [monsters/spawn § J](../monsters/spawn.md#j-creation-and-the-unit-seed) takes that seed as an input from
   `monsters/stats`. [C] (fn:sub_00555230_SUnitCreate@0x00555230, run:2026-10-13-mon-spawn) With a null parent
   pointer, `UnitSeedInit` uses `RNG_EntropySeed(2 × counter)` instead, a non-reproducible path no
   run hit. [I] (fn:sub_00552DF0_UnitSeedInit@0x00552DF0, data:g_UnitSeedSaltCounter@0x008846E8)
7b. **These are the client constructors** (`CUnit.cpp`). They store the client act at `unit+0x1C`,
   and every logged client unit drew from a room of the client act (739 seeds). They don't decide
   drops or spawns. [C] (fn:sub_00465FD0_UnitInit@0x00465FD0, run:2026-10-11-seed-tree-p1) The two
   arguments tested are (x, y). A client unit created at (0, 0) makes no room lookup, gets no room
   draw and keeps `{1, 666}`: 252 such units, against 24 565 that looked their room up. [C]
   (fn:sub_00465FD0_UnitInit@0x00465FD0, run:2026-10-16-sweep-roomk, [rng/0002 § Plan 0038 batch H5c](../../findings/rng/0002-seed-tree.md#plan-0038-batch-h5c-run2026-10-16-sweep-roomk)) The room lookup
   `0x00465420` takes them as a position, returns no room for (0, 0), and its error message names them
   `nX`, `nY`; the caller never asks it for (0, 0), so that return is not observed. [I]
   (fn:sub_00465420_ClientRoomAt@0x00465420) Type 4 does nothing that draws before the room draw: the
   objdump closure under `ItemDataAlloc` and `ItemDataSeedInitOne` holds no drawing function, only the
   one initialiser. [C] (fn:sub_00627C90_ItemDataAlloc@0x00627C90,
   fn:sub_00627DC0_ItemDataSeedInitOne@0x00627DC0, [rng/0002 § Plan 0038 batch S1b](../../findings/rng/0002-seed-tree.md#plan-0038-batch-s1b-2026-10-16)) It is
   the closure of step 5's allocators, with the same split of its indirect calls (step 5 note). Type 1 (monsters) never goes through
   `0x00465FD0` from the client creator `0x00466730`, which sends type 1 to `ClientMonCreate` and every
   other type to `UnitInit`; the 739 logged `UnitInit` hits are all type 2. [C] (0x0046675C, 0x00466796,
   0x004667D6, fn:sub_00466360_ClientMonCreate@0x00466360, run:2026-10-11-seed-tree-p1, [rng/0002 § Plan 0038 batch S1b](../../findings/rng/0002-seed-tree.md#plan-0038-batch-s1b-2026-10-16))
   `UnitInit`'s two other callers (0x004661F0, 0x00466332) pass their own caller's type, not traced,
   so the claim for them rests on the case at `0x004660A4` reaching the error path. [I] (0x004660A4)

## Outputs

A seed object, initialised as above, in each act (server and client copy), level, DRLG room,
active room, server unit and client unit. The parent seed advances by exactly the draws listed,
except that step 6a overwrites the DRLG room seed. [C] (run:2026-10-11-seed-tree, run:2026-10-11-seed-tree-p1)

## Worked example

**Observed.** Every value below was logged by the runtime harness with `-seed 12345` (map seed
`0x3039`) and is reproduced by `tools/rng.py seedtree` from N alone (run:2026-10-11-seed-tree,
run:2026-10-11-seed-tree-p1). The last block uses `-seed 34844169`. Seeds are `low:high`, hex unless noted.

| Step | Operation | Value |
|---|---|---|
| 1 | game: override flag, map seed, game seed | `1`, `00003039`, `00003039:0000029A` |
| 3a | `Init(act.seed, 12345)` | `00003039:0000029A` |
| 3b | `Step`, `levelSeedBase ←` low | `015B2E77` (act seed `015B2E77:0000141D`) |
| 3c | Act II pair 1: `low mod 7` twice | `3, 3` → equal, retry |
| 3c | Act II pair 2 | `6, 5` → `act[+0x094] = 72`, `act[+0x484] = 71` (dec); act seed `B7A5C418:63A93A78` |
| 4 | level 1 seed | `015B2E78:0000029A` |
| 5 | level 1, rooms 1–3: level seed after each draw | `F61E44F2`, `F3CFFCC1`, `6B277FA8` |
| 5 | room 3: `Init(6B277FA8)`, step, `+0x04` | room seed `F923BEE2:2CB17800`, `+0x04 = F923BEE2` |
| 6a | room 3 activated on the server: re-seed | `F923BEE2:0000029A` |
| 6b | k = 64 room-type draws | `2CE81EC1:55A43D6F` |
| 6c | activation draw, active-room seed | DRLG room `28D677F4:12BAF1A9`, active `28D677F4:0000029A`, flags 0 |
| 7a | player (type 0), seeded by a player-creation caller of `UnitSeedInit` (step note 7a), not by 7a's pseudocode: game-seed draw#5 | unit seed `B7A5C418:0000029A`, `+0x28 = B7A5C418` |
| 7a | first starting item (type 4): draw#6, then draw#7 | unit seed `8F16A0F0:0000029A`; game seed then `FD29EDF2:3BAE5B0E` |
| 3b, 4 | `-seed 34844169`: `levelSeedBase`, level 134 seed | `FFFFFF87`, `0000000D:0000029A` (u32 wrap) |

Under an override, the game seed and the act seed start from the same `Init(N)`, so their sequences
coincide (the player's draw#5 equals the Act II act seed after its five draws). They remain two
separate objects.

## Reimplementation notes

- **Two different roots.** Maps derive from the **map seed** `game+0x7C`. The game seed `+0xD0` is a
  separate object that doesn't feed the act → level chain, but does feed every server unit. [C]
  (fn:GAME_InitSeeds@0x0052C280, run:2026-10-11-seed-tree-p1)
- **`-seed 0` is impossible.** The option is applied only when non-zero, so `0` takes the clock
  path. [C] (fn:sub_0044D860_ApplySeedOption@0x0044D860, run:2026-10-11-seed-tree-p1)
- **The level seed is a sum, and it wraps.** Don't implement it as a draw from the act seed, and add
  in `u32`. [C] (fn:DRLG_LevelCreate@0x00642AE0, run:2026-10-11-seed-tree)
- **The Act II tomb draws use an unguarded `mod 7`**, not `Range`. The loop count is unbounded in
  principle, and every rejected pair consumes two act draws. [C] (fn:DRLG_ActCreate@0x00642DA0,
  run:2026-10-11-seed-tree)
- **Activation re-seeds the DRLG room.** Carrying the room seed over from level generation gives
  wrong active-room seeds. Restart it from `+0x04`. [C] (fn:sub_0066EE40_DrlgRoomReseed@0x0066EE40,
  run:2026-10-11-seed-tree-p1)
- **No `RoomTile` data, no draw.** A DRLG room failing the `T[+0x18]`/`T[+0x20]` test is not activated
  and consumes no activation draw. [C] (fn:DRLG_RoomActivate@0x006422A0, run:2026-10-11-seed-tree-p1)
- **Server units don't use the room.** The room-seed rule of step 7b is the client's. A server-side
  reimplementation seeds monsters, objects, NPCs and items from the game seed. [C]
  (fn:sub_00555230_SUnitCreate@0x00555230, run:2026-10-11-seed-tree-p1)
- **`InitOne` before `Init` is dead.** It is overwritten immediately, and neither initialiser draws,
  so it has no observable effect. [I] (fn:GAME_InitSeeds@0x0052C280, fn:sub_00552DF0_UnitSeedInit@0x00552DF0)
- **Seeds that are not gameplay seeds.** All 103 initialiser call sites (76 functions) are classified by call shape.
  Besides the tree above, they are: the client automap's global seed `init(0)` (`AutomapTxtLoad`, drawn only by the
  automap cell pick); two title-screen globals from `RNG_EntropySeed`; and local stack seeds in client/server pairs
  (constant `0x53454953`, a unit base stat, or other values). None of these feeds the act, level, room, unit or item
  seeds. The sites that re-seed a unit's `+0x20` or another object's seed lie in the skill and missile code
  (*Skill and missile re-seeds* below). [I] (fn:RNG_SeedInitOne@0x00650E30, fn:RNG_SeedInit@0x00650E40,
  fn:sub_0061FCF0_AutomapTxtLoad@0x0061FCF0, [rng/0002 § Plan 0039 batch P1a](../../findings/rng/0002-seed-tree.md#the-other-initialiser-sites))
- **The missile pierce count's seed is local.** `sub_0059F940_MissilePierceCount`, the server half of the base-stat pair,
  initialises a stack seed with `Init(baseStat(owner, 328))` (for a player, stat 328 is raised by 1 on each of its skill requests) and steps
  it at most four times for the missile's pierce count; it reads and writes no game, unit or missile seed. So it is a
  classified initialiser site, not a re-seed. [I] (fn:sub_0059F940_MissilePierceCount@0x0059F940, fn:RNG_SeedInit@0x00650E40,
  [skills/0002 § 3](../../findings/skills/0002-missiles.md#3-the-damage-the-missile-carries),
  [rng/0002 § Plan 0039 batch P1a](../../findings/rng/0002-seed-tree.md#the-other-initialiser-sites) for the client/server pair)

- **Skill and missile re-seeds.** The server sites of the skill and missile code re-seed a **missile's** seed or a
  local stack seed, with one exception among the reached sites, Armageddon:

  | Site | Re-seeds | From |
  |---|---|---|
  | missile-creation callbacks `0x005D40F0`, `0x005D4680` (the rings of progressive entries 37 and 143) | the new missile's `+0x20` | the creator's local seed's low word |
  | callbacks `0x005C9290` (Firestorm and others), `0x005CD110`, `0x005AC040` | the new missile's `+0x20` | the path position `+0x10`, plus an index for the first two |
  | missile do 28 and 35 | the missile's `+0x20` | the low word kept in `MissileData+0x28`, stored back after the draws |
  | hit 58, do 34 | the missile's `+0x20` | its position (hit 58 its `SubX`, do 34 its path X) |
  | `0x005A9820` (missile do 8, 10, 17, 25) | the parent missile's `+0x20` | its `SubX + elapsed` |
  | Armageddon's periodic function (`srvactivefunc` 146) | the **caster's** `+0x20` | the skill entry's `+0x18` (at the first period, the cast's draw under the conditions of *Armageddon's cast draw* below), then a fresh `RNG_Range(1 000 000)` is stored back there |
  | `0x00645390` | a unit's `+0x20` | a skill entry's `+0x18`/`+0x1C`; no reference in the image |

  So a missile's draws after such a re-seed are a function of the creator's value, not of the game seed, and an
  Armageddon period sets the caster's seed from a stored word: a reimplementation keeps that word per skill entry,
  written at the cast as *Armageddon's cast draw* below states.
  The one other server site of rng/0002's register-seed list, `0x005C276A` in the version-0 set builder, re-seeds an **item's** seed from
  its own saved low word, restoring it on failure.
  [I] (fn:sub_005C2740_ItemBuildSetV0@0x005C2740, 0x005C276A, fn:sub_005D40F0_MissCbReseedFromArg@0x005D40F0, fn:sub_005D4680_MissCbReseedZigzag@0x005D4680,
  fn:sub_005C9290_MissCbReseedPathXPlusArg@0x005C9290, fn:sub_005CD110_MissCbReseedRoll@0x005CD110,
  fn:sub_005AC040_MissCbReseedPathX@0x005AC040, fn:sub_005C8520_SkillDo146Armageddon@0x005C8520, 0x005C8688–0x005C8694,
  [skills/0003 § 9](../../findings/skills/0003-handlers.md#9-re-seed-sites-rng0002--the-other-initialiser-sites))

- **Armageddon's cast draw.** Skill do function 124 (`srvdofunc` 124: 249 Armageddon, 250 Hurricane, 349 Diablogeddon),
  after its record test, its `aurastate` range test and its used-skill tests, makes one `r = RNG_Range(caster+0x20,
  0x10000)` on the **caster's** seed and keeps `r` in its frame, before its `STATLIST_Alloc` or `StatListSetEnd`. In
  the run's cases it makes no other draw on the caster's seed before that call; the `auralencalc` it evaluates between
  the draw and that call ran on constant programs only, so a calc function's own draws are not covered. [C]
  (ADR-0021, up to `STATLIST_Alloc` @0x005C8295 or `StatListSetEnd` @0x005C82E1;
  fn:sub_005C8190_SkillDo124PeriodicState@0x005C8190, 0x005C8228, run:2026-10-21-cat-emu-dru,
  [skills/0013 § 4](../../findings/skills/0013-druid.md#4-the-shape-and-timed-state-functions-do-116-120-124))

  After that call, from the reading: a `STATLIST_Alloc` giving 0 makes do 124 return 0 with nothing queued or stored;
  otherwise it cancels the caster's unit events 5 for the skill id, queues unit event 5 at `frame + Param4` with
  `(id, lvl)`, and stores `r` with `UnitSkillSet18(used node, r)`. For Armageddon and Diablogeddon (state 145,
  `srvactivefunc` 146) that event runs the periodic function above, which reads the `+0x18` of
  `SKILLS_GetUnitSkill(caster, id)`'s node and seeds the caster with `Init` of it. So the first period re-seeds the
  caster from the cast's `r` when that node is the used node **and** no other writer of its `+0x18` runs between the
  cast and that period; the setter `sub_00644560_UnitSkillSet18` has 85 call sites, which were not followed, and no
  run has logged a first period. Hurricane (state 144, `srvactivefunc` 145) is stored the same `r`, and its periodic
  function does not re-seed. [I] (0x005C8299, 0x005C8354–0x005C835C, fn:sub_00644560_UnitSkillSet18@0x00644560,
  fn:sub_005C8520_SkillDo146Armageddon@0x005C8520, 0x005C8647–0x005C8779,
  [skills/0013 § 5](../../findings/skills/0013-druid.md#5-the-periodic-states-do-table-entries-145-and-146),
  [skills/0003 § 9](../../findings/skills/0003-handlers.md#9-re-seed-sites-rng0002--the-other-initialiser-sites) dated note)

## Evidence

- [findings/rng/0002-seed-tree.md](../../findings/rng/0002-seed-tree.md): the seed tree, [§ Active room](../../findings/rng/0002-seed-tree.md#active-room), [§ Units](../../findings/rng/0002-seed-tree.md#units).
  [§ Other seed sites](../../findings/rng/0002-seed-tree.md#other-seed-sites-seen-not-yet-followed): game creation's
  draws 1–5, with [items/0009 § 1](../../findings/items/0009-vendors.md#1-store-records-and-the-store-seed-game-creation)
  (draw 3) and [items/0010 § 1](../../findings/items/0010-quest-drops.md#1-quest-objects-events-and-the-quest-seed) (draw 4).
- [findings/skills/0002-missiles.md § 3](../../findings/skills/0002-missiles.md#3-the-damage-the-missile-carries): the pierce count's local seed (plan 0045 P1.2).
- [findings/skills/0003-handlers.md § 9](../../findings/skills/0003-handlers.md#9-re-seed-sites-rng0002--the-other-initialiser-sites): the skill and missile re-seed sites (plan 0045 P1.3, and its review).
- [findings/skills/0013-druid.md §§ 4, 5](../../findings/skills/0013-druid.md#4-the-shape-and-timed-state-functions-do-116-120-124) and
  [skills/experiments § run:2026-10-21-cat-emu-dru](../../findings/skills/experiments.md#run2026-10-21-cat-emu-dru):
  Armageddon's cast draw (plan 0046 batch `dru`, and the `lane/p46m10` review).
- [findings/rng/0001-rng-core.md](../../findings/rng/0001-rng-core.md): the "draw" definition, `0x005BDFF0`.
- [findings/monsters/0001-level-pool.md § 1](../../findings/monsters/0001-level-pool.md#1-where-and-when-game-creation): game-seed draw 1 and the game-creation call order (step note 7a).
- [findings/rng/experiments.md § run:2026-10-11-seed-tree](../../findings/rng/experiments.md#run2026-10-11-seed-tree):
  8 runs, 3353/3353 game, act, level and DRLG-room values predicted.
- [findings/rng/experiments.md § run:2026-10-11-seed-tree-p1](../../findings/rng/experiments.md#run2026-10-11-seed-tree-p1):
  active rooms, server and client units, act copies, clock path; 5954/5954 values predicted over all logs.
- Plan 0038 re-tag: [rng/0002 § Plan 0038 batch S1b](../../findings/rng/0002-seed-tree.md#plan-0038-batch-s1b-2026-10-16)
  (static second sources: the `g_SeedOverride` bytes, the room-type dispatch, the `UnitSeedInit` callers, the client
  creator) and [§ Plan 0038 batch H5c](../../findings/rng/0002-seed-tree.md#plan-0038-batch-h5c-run2026-10-16-sweep-roomk)
  ([drlg/experiments.md § run:2026-10-16-sweep-roomk](../../findings/drlg/experiments.md#run2026-10-16-sweep-roomk):
  act-seed steps, activation flags, the `LevelCreate` callers, `T[+0x18]`/`T[+0x20]`, flags bit 0, client units at
  (0, 0), and the step note 2 correction).
- Plan 0039: [rng/0002 § Plan 0039 batch P1a](../../findings/rng/0002-seed-tree.md#plan-0039-batch-p1a-2026-10-16)
  (room `+0x28` bit `0x40000` and `+0x60` bit 0, the stored item seeds, the initialiser survey).
- [findings/data/0001-excel-loader.md](../../findings/data/0001-excel-loader.md): level definition `+0x30` = `Levels.txt:DrlgType`.
- [README.md](README.md): primitives (`[C]`; fn:RNG_Step@0x0045C370, fn:RNG_SeedInit@0x00650E40, run:2026-10-11-rng-emu).
- [drlg/room-tiles](../drlg/room-tiles.md) and [findings/drlg/0002-room-build-draws.md](../../findings/drlg/0002-room-build-draws.md):
  k (step 6b), from run:2026-10-11-drlg-roomk; [drlg/overview](../drlg/README.md): the dispatch of step 4 and the room-creation order.

## Open questions

- ~~The k room-type draws of step 6b~~: defined in [drlg/room-tiles § k](../drlg/room-tiles.md#k)
  (plan 0008). Its own open questions (the `Orient89Unit` draw, the merge orientation tables, the
  `Trees.ds1` overread) carry over there.
- ~~What DRLG room `+0x60` bit 0 (→ flags 1) means, and where `+0x28` bit `0x40000` (→ flags 4) is set.~~ Answered
  in step note 6, both confirmed ([rng/0002 § Plan 0039 batch P1a](../../findings/rng/0002-seed-tree.md#plan-0039-batch-p1a-2026-10-16)).
- [L] Meaning of act `+0x094` vs `+0x484` (which tomb is the real one), the Act III bit `+0x474`, what
  the Act III act-seed consumers under `0x006789B0` decide, and the level-27 bit set at level 6. They are
  placed as entry points in [drlg/overview](../drlg/README.md#act-seed-consumers). Owner:
  `drlg/warps` and the quest work; the quest side is [quests/progression § Creation-path readers](../quests/progression.md#creation-path-readers).
- [L] **The order of game-seed consumers**, narrowed again: game creation's draws 1–5 are fixed (step note 7a:
  monster regions, object region, store seed, quest seed, the player). Still open: the gaps between later units.
  The population pass's own game-seed draws are in [monsters/spawn](../monsters/spawn.md), and those of the restore of a
  released room (one per monster, two per item, the objects') in [drlg/lifecycle](../drlg/lifecycle.md#draw-order-across-the-seeds). Owners: items
  (plan 0004), monster and object plans.
- ~~The server population pass `sub_0054EC90_RoomPopulate`~~: answered in step note 6 and in
  [monsters/spawn](../monsters/spawn.md) (plan 0014, run:2026-10-13-mon-spawn).
- ~~The item seeds: which creation paths pass non-zero creation-parameter seeds `+0x48`/`+0x4C` at `0x00558D90`.~~
  Answered in step note 7a (*Stored item seeds*: only the version-`0x47` item-list reader).
- [L] **The `D2.ini` route of step 2.** Run:2026-10-16-sweep-roomk contradicted the earlier reading of step note 2
  for the command line only. Whether `GetPrivateProfileIntA` stores a negative or ≥ 2³¹ `seed` value as its
  two's-complement `u32` (so that seeds `0x80000000`…`0xFFFFFFFE` are reachable, and `0xFFFFFFFF` means "no
  override"), was not run ([rng/0002 § Plan 0038 batch H5c](../../findings/rng/0002-seed-tree.md#plan-0038-batch-h5c-run2026-10-16-sweep-roomk)).
  Owner: reverser, a `D2.ini` session.
- ~~**Skill and missile re-seeds**: the server sites in the skill and missile code that re-seed a unit's `+0x20` or
  another object's seed, and from what.~~ Read from the code (*Reimplementation notes*, *Skill and missile re-seeds*;
  plan 0045 P1.3): missiles and local seeds, and the caster at Armageddon's periods.
- [L] **Armageddon's first period**, narrowed: the cast's `RNG_Range(caster+0x20, 0x10000)` and its store at the
  used node's `+0x18` are in *Reimplementation notes* (*Armageddon's cast draw*: the draw confirmed, the store read from the code). Still
  open: whether `SKILLS_GetUnitSkill(caster, id)` and do 124's used node are one node at the first period, and whether
  another writer of that node's `+0x18` (the setter `0x00644560` has 85 call sites, not followed) runs between the
  cast and that period, so whether the first period's caster seed is `Init(r)`. Owner: a run that logs a first
  period (plan 0045 Phase 2, logged whenever it fires, or plan 0046)
  ([skills/0013 § 5](../../findings/skills/0013-druid.md#5-the-periodic-states-do-table-entries-145-and-146)).
