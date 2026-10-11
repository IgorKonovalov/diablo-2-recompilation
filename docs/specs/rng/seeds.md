---
spec: rng/seeds
status: draft
target: Diablo II LoD 1.14d, Game.exe sha256 631066c1649c4ea9…
depends_on: [rng]
consumed_by: [drlg/overview, drlg/*, monsters/spawn, objects, items/*]
tags: {C: 0, I: 30, L: 8}
updated: 2026-10-11
---

# Seed tree: game → act → level → room → unit

## Purpose

Defines where each seed object is created and what its initial value is, from the game root down
to units placed in a room. With a fixed map seed, this chain fixes every act's and level's starting
seed, and therefore the inputs of the DRLG generators. This is a **first pass**: every statement
is `[I]` (code read, no runtime corroboration yet), and the item, monster-region and object-region
branches are not specced here. Primitives (`Step`, `Range`, `Init`, `InitOne`) are defined in
[README.md](README.md).

## Entry points

| When | Function | Tag |
|---|---|---|
| Game created | fn:GAME_InitSeeds@0x0052C280 | [I] |
| `-seed N` on the command line | fn:sub_0044D860_ApplySeedOption@0x0044D860 → fn:GAME_SetSeedOverride@0x0052C320 | [I] |
| Act created | fn:sub_0053AC70_ActCreate@0x0053AC70 → fn:DUNGEON_ActCreate@0x006194A0 → fn:DRLG_ActCreate@0x00642DA0 | [I] |
| Level created | fn:DRLG_LevelCreate@0x00642AE0 | [I] |
| DRLG room created | fn:DRLG_RoomCreate@0x0066B3E0 | [I] |
| Room activated | fn:DRLG_RoomActivate@0x006422A0 → fn:DUNGEON_RoomCreate@0x00619890 | [I] |
| Unit created in a room | fn:sub_00465FD0_UnitInit@0x00465FD0, fn:sub_00466200_UnitInitB@0x00466200 | [I] |

## Inputs

### Tables

| Anchor | Used for |
|---|---|
| tbl:Levels.txt:Id | level IDs 66–72 are the seven Act II Tal Rasha tombs, the range of the Act II draw (step 3c) |

### Runtime state

Owner names are ours, taken from the source path each allocation passes to the allocator. Offsets
are byte offsets into the owner. No struct in `re/types/` exists yet.

| Seed / value | Type | Owner offset | Source |
|---|---|---|---|
| game seed | `Seed` | game `+0xD0` | step 1 |
| map seed | `u32` | game `+0x7C` | step 1 |
| override flag | `u32` | game `+0x84` | step 1 |
| seed override | `i32`, `−1` = none | data:g_SeedOverride@0x00731004 | step 2 |
| act seed | `Seed` | DRLG act `+0x000` | step 3 |
| act map seed copy | `u32` | DRLG act `+0x458` | step 3 |
| level seed base | `u32` | DRLG act `+0x470` | step 3 |
| level seed | `Seed` | level `+0x1C4` | step 4 |
| DRLG room seed | `Seed` | DRLG room `+0x14` | step 5 |
| DRLG room first draw | `u32` | DRLG room `+0x04` | step 5 |
| active room seed | `Seed` | active room `+0x6C` | step 6 |
| unit seed | `Seed` | unit `+0x20` | step 7 |
| unit initial seed value | `u32` | unit `+0x28` | step 7 |

### Constants

| Name | Value | Anchor | Tag |
|---|---|---|---|
| no-override sentinel | `0xFFFFFFFF` (`−1`) | data:g_SeedOverride@0x00731004 | [I] |
| first tomb level ID | `66` | fn:DRLG_ActCreate@0x00642DA0, tbl:Levels.txt:Id | [I] |

## Algorithm

```
1. CreateGameSeeds(game):                                         [I] (fn:GAME_InitSeeds@0x0052C280)
     if g_SeedOverride = −1:
       game.overrideFlag ← 0
       InitOne(game.seed)
       Init(game.seed, EntropySeed(salt: QPC low dword))
       Step(game.seed)                                            ; game draw#1
       game.mapSeed ← EntropySeed(salt: game.seed.low)
     else:
       game.overrideFlag ← 1
       game.mapSeed ← (u32) g_SeedOverride
       InitOne(game.seed)
       Init(game.seed, (u32) g_SeedOverride)                      ; no draw

   EntropySeed(salt) → u32:                                       [I] (fn:RNG_EntropySeed@0x00650DE0)
     x ← GetTickCount() + time(NULL) + salt
     repeat 3 times: x ← x × 0x19660D + 0x3C6EF35F
     return x & 0x7FFFFFFF

2. ApplySeedOption(config):                                       [I] (fn:sub_0044D860_ApplySeedOption@0x0044D860, fn:GAME_SetSeedOverride@0x0052C320)
     v ← config[+0x21A]                                           ; option {key SEED, switch seed} (0x00705F17)
     if v ≠ 0: g_SeedOverride ← v                                 ; 0 is never applied

3. CreateAct(actIndex: u8, mapSeed: u32) → act:                   [I] (fn:DRLG_ActCreate@0x00642DA0)
   3a. Init(act.seed, mapSeed);  act.mapSeedCopy ← mapSeed
   3b. Step(act.seed)                                             ; act draw#1
       act.levelSeedBase ← act.seed.low
   3c. if actIndex = 1:                                           ; Act II
         repeat:
           Step(act.seed);  a: u32 ← act.seed.low mod 7          ; act draw#2k,   unguarded
           Step(act.seed);  b: u32 ← act.seed.low mod 7          ; act draw#2k+1, unguarded
         until a ≠ b
         act[+0x094] ← a + 66;  act[+0x484] ← b + 66
       else if actIndex = 2:                                      ; Act III
         Step(act.seed)                                           ; act draw#2
         act[+0x474] ← act.seed.low & 1
   The mapSeed argument is game.mapSeed for every act.            [I] (fn:sub_0053AC70_ActCreate@0x0053AC70)

4. CreateLevel(act, levelId: u32) → level:                        [I] (fn:DRLG_LevelCreate@0x00642AE0)
     Init(level.seed, act.levelSeedBase + levelId)                ; a sum, NOT a draw
     dispatch on levelDef[+0x30]: 1 → 0x00673B10, 2 → 0x00667430, 3 → 0x00675320

5. CreateDrlgRoom(level) → room:                                  [I] (fn:DRLG_RoomCreate@0x0066B3E0)
     Step(level.seed)                                             ; one level draw
     Init(room.seed, level.seed.low)
     Step(room.seed)                                              ; room draw#1
     room[+0x04] ← room.seed.low

6. ActivateRoom(drlgRoom) → activeRoom:                           [I] (fn:DRLG_RoomActivate@0x006422A0, fn:DUNGEON_RoomCreate@0x00619890)
     Step(drlgRoom.seed)                                          ; one DRLG-room draw
     Init(activeRoom.seed, drlgRoom.seed.low)

7. InitUnitSeed(unit, room?):                                     [I] (fn:sub_00465FD0_UnitInit@0x00465FD0, fn:sub_00466200_UnitInitB@0x00466200)
     InitOne(unit.seed)
     if room present:
       Step(room.seed)                                            ; one active-room draw
       unit.initialSeed ← room.seed.low
       Init(unit.seed, room.seed.low)
```

Step notes:

1. Without `-seed`, both the game seed and the map seed depend on the wall clock and the
   performance counter, so they can't be reproduced. A reimplementation that wants determinism
   takes the override branch. [I] (fn:RNG_EntropySeed@0x00650DE0)
3. All acts of one game get the same map seed, so all acts share the same `levelSeedBase`.
   Act-specific draws come after `levelSeedBase` is taken and don't change it. [I]
   (fn:DRLG_ActCreate@0x00642DA0, fn:sub_0053AC70_ActCreate@0x0053AC70). The Act II loop draws two
   distinct tomb level IDs in 66–72. Which of the two fields is the real tomb is open. [I]
   (fn:DRLG_ActCreate@0x00642DA0, tbl:Levels.txt:Id)
4. A level's seed depends only on the map seed and the level ID, never on the order in which
   levels are built. [I] (fn:DRLG_LevelCreate@0x00642AE0)
5. Each child creation consumes exactly one draw from its parent's seed, so the order in which
   rooms are created (and units placed) does matter below the level. [I]
   (fn:DRLG_RoomCreate@0x0066B3E0, fn:DRLG_RoomActivate@0x006422A0, fn:sub_00465FD0_UnitInit@0x00465FD0)
7. The parent of a unit seed is the *active* room's seed `+0x6C`, not the game seed. [I]
   (fn:sub_00465FD0_UnitInit@0x00465FD0)

## Outputs

A seed object, initialised as above, in each act, level, DRLG room, active room and room-placed
unit. The parent seed advances by exactly the draws listed. [I]

## Worked example

**Derived, not observed.** Computed with `tools/rng.py` (whose primitives are `[C]`) by applying the
`[I]` rules above. It checks a reimplementation against *this spec*, not against the game, until a
`-seed` run is recorded. Map seed = `12345` (override). Hex unless noted.

| Step | Operation | Value |
|---|---|---|
| 3a | `Init(act.seed, 12345)` | `{00003039, 0000029A}` |
| 3b | `Step`, `levelSeedBase ←` low | `015B2E77` |
| 3c | Act II pair 1: `low mod 7` twice | `3, 3` → equal, retry |
| 3c | Act II pair 2 | `6, 5` → `act[+0x094] = 72`, `act[+0x484] = 71` (dec) |
| 4 | level 1 seed | `Init(015B2E78)` |
| 4 | level 2 seed | `Init(015B2E79)` |
| 5 | first room of level 1, if no other level-1 draw came first: room seed | `Init(F61E44F2)` |
| 5 | that room's `+0x04` | `F33F30D4` |

## Reimplementation notes

- **Two different roots.** Maps derive from the **map seed** `game+0x7C`. The game seed `+0xD0`
  is a separate object that doesn't feed the act → level chain. [I] (fn:GAME_InitSeeds@0x0052C280)
- **`-seed 0` is impossible.** The option is applied only when non-zero, so `0` behaves like no
  option at all. [I] (fn:sub_0044D860_ApplySeedOption@0x0044D860)
- **The level seed is a sum.** Don't implement it as a draw from the act seed. [I]
  (fn:DRLG_LevelCreate@0x00642AE0)
- **The Act II tomb draws use an unguarded `mod 7`**, not `Range`. The loop count is unbounded in
  principle, and every rejected pair consumes two act draws. [I] (fn:DRLG_ActCreate@0x00642DA0)
- **`InitOne` before `Init` is dead.** It is overwritten immediately, and neither initialiser
  draws, so it has no observable effect. [I] (fn:GAME_InitSeeds@0x0052C280, fn:sub_00465FD0_UnitInit@0x00465FD0)

## Evidence

- [findings/rng/0002-seed-tree.md](../../findings/rng/0002-seed-tree.md): first pass, status open.
- [README.md](README.md): primitives (`[C]`).

## Open questions

- [L] **Runtime confirmation of the whole chain.** Run twice under wine with `-seed N` and compare
  layouts, or break on `DRLG_LevelCreate` and log `act[+0x470]` and the level seeds. This would
  promote steps 1–4 to `[C]`. ([0002](../../findings/rng/0002-seed-tree.md#open-questions))
- [L] Integer widths not recorded in the finding: whether `levelSeedBase + levelId` and the
  `EntropySeed` LCG wrap at 32 bits (expected for x86 register arithmetic, not stated), and the
  width of `config[+0x21A]`.
- [L] Which table column holds the level-definition generator type `+0x30`, and which generator each
  of `0x00673B10`, `0x00667430`, `0x00675320` is. Community docs say 1 = maze, 2 = preset, 3 = outdoor.
- [L] Meaning of act `+0x094` vs `+0x484` (which tomb is the real one) and of the Act III bit `+0x474`.
  Needs their readers.
- [L] Whether the act index in step 3 is 0-based (so 1 = Act II), as the tomb range suggests.
- [L] The second caller of `DUNGEON_ActCreate` (`0x0044E100`) and the seed it passes; possibly client-side.
- [L] Seeds of object regions, unit proxies and monster regions (draw from the seed at `ECX+0xD0`,
  maybe the game seed), items (seed set from a creation parameter, `0x00558D90`), and the
  `LvlTbls.cpp`/`QUESTS.CPP` inits. 61 of 76 initialiser-calling functions are unfollowed.
- [L] The monster-spawn seed: drawn from the active room like other units?
