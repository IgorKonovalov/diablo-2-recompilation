# 0002 — The in-chain oracles retired, and the composition checked with them modelled

> **Subsystem:** chain (seed to world, plan 0048)
> **Question:** can each oracle the Phase 0 review assigned (chain/0001 § 4: 2, 14, 16, 17, 22, 19, 21, 20, 7, 6, 13) be replaced by a model from code the specs already cite, and does `tools/chain.py check` pass on the kept logs with those callees predicted?
> **Date:** 2026-10-20   **Plan:** 0048 (Phase 1)   **Status:** open (Phase 1 reviewed 2026-10-20: accepted with fixes; Phase 2 next)

Phase 1 runs no harness session. Each model is checked on kept logs of earlier runs (re-analysis); the logs are named
per oracle with their manifests. `tools/chain.py` is the composition: `gen` builds what the game seed alone fixes,
`check` replays a log through the reviewed checkers with every retired oracle switched to its model and counts the
oracles still taken from the log.

## Answer (summary)

- [C] **Oracle 2 (`ITEMS_RollStaffMods`) is retired**: the staff-mods model is the default of `tools/affixes.py`,
  `tools/items_chain.py` and `tools/chain.py`; 3 991 + 3 170 creations of the 133 kept item logs reproduce with no
  staff-mods seed from a log, 99 exit seeds and 64 skill entries predicted (§ 2). (fn:ITEMS_RollStaffMods@0x005C1260,
  run:2026-10-14-affixes, run:2026-10-15-items-chain)
- [C] **Oracle 14 (the unit seed after `SUnitCreate`) is retired in part**, where the region entry is known:
  `tools/monspawn.py` predicts the unit seed at `MU` from the game-seed step, `MonRegionFindAdd` on a tracked region and
  `MonStatsInit`'s draws; at the step of § 3, 7 953 of 8 075 creations of the 62 kept world logs, 0 mismatches; with
  every Phase 1 model in (§ 13), **8 519 of 8 553**. The remainder, 34 creations, takes its unit seed from the log: a
  class appended to the region by a creation outside the model (an InitFn or operate spawn), whose variant sets the
  region snapshot does not log (§ 3, § 4). (fn:sub_00555230_SUnitCreate@0x00555230,
  fn:sub_00547BC0_MonRegionFindAdd@0x00547BC0, fn:sub_00573CB0_MonStatsInit@0x00573CB0, run:2026-10-15-mon-stats,
  run:2026-10-15-objects)
- [C] **Oracle 16 (the preset monsters of the presets window) is retired**: at the step of § 4, 299 class-case
  presets (66 MonPlace fixed-row placements among them), 35 presets that place nothing, 11 superunique and MonPlace
  2/3 windows and 29 tile units are predicted from `OPU0` to `OPUX` on the 62 world logs, 0 mismatches; with the 12
  catapult windows of § 6 in (§ 13), **311 class-case presets**. Class 434's mode (3 requests) is a quest-state input,
  taken from the request (§ 4, § 6). (fn:sub_0054E600_PresetMonSpawn@0x0054E600,
  fn:sub_0054E490_PresetClassSpawn@0x0054E490, fn:sub_0063EC70_LevelClassVariant@0x0063EC70, run:2026-10-15-objects)
- [C] **Oracle 17 (InitFn 46) is retired**: `tools/objects.py` models `OBJINIT_CityDamnedSpawns` (16 calls, every
  object-region draw) and `tools/monspawn.py` its 21 `MonSpawnTry` requests; InitFns 54 and 62 (11 calls, reached
  although chain/0001 row 17 said not) stay seed oracles; 1 245 of 1 265 objects windows carry no oracle at that step
  (§ 5), 1 253 at the end of Phase 1 (§ 13) and 1 250 after the merge of `main` (§ 14).
  (fn:OBJINIT_CityDamnedSpawns@0x005506D0, run:2026-10-15-objects)
- [C] **Oracle 22 (the `Orient89Unit` creations) is retired**: the units its rows name come as preset units of the
  presets window (`[I]` that `Orient89Unit` itself creates none at activation), so their creations are oracle 16's
  windows, and the last 12 (the objects 571 and 572 under catapults 432 and 433) are now modelled too; 1 255 of 1 265 objects windows carry no oracle (§ 6).
  (fn:sub_0066D9E0_Orient89Unit@0x0066D9E0, fn:sub_0054E490_PresetClassSpawn@0x0054E490, run:2026-10-15-objects)
- [I] **Oracle 19 (the gate's DRLG parts) is read but not retired**: `OBJ_PopulateGate`'s four DRLG tests are now
  read to the room fields they test (flags `0x30000`, flag `0x800000`, the out room's `0x80`, the level id), and the
  logged values agree with the reading on every gate of the 62 world logs; which rooms carry those flags, and
  `LevelRoomCount`, are DRLG state that `tools/drlg.py` does not yet hand to the chain, so they stay logged (§ 7).
  (fn:OBJ_PopulateGate@0x00552560, fn:sub_0066BB20_DrlgRoomPopLevelId@0x0066BB20, run:2026-10-15-objects)
- [C] **Oracle 21 (another room's seed in a pass) is retired**: the seed is the chain's state for that room (its
  predicted activation seed, or its seed after its last pass); both calls of the world logs predicted (§ 8).
  (fn:sub_005B2A00_MonSpawnTry@0x005B2A00, run:2026-10-14-collision)
- [C] **Oracle 7 (the gold piles' items) is retired in part**, in its seeds and marks: each of the 71 gold drops of `InitFn` 28
  is now created by the model (two game-seed steps, the item's unit seed, its `0x200` mark, no object-region draw);
  the drop spot is predicted for 69 of 71 and taken from the log for 2, where the model disagrees (§ 9).
  (fn:sub_00559300_DropGoldPile@0x00559300, fn:OBJINIT_GoldPiles@0x0054F8C0, run:2026-10-15-objects)
- [C] **Oracle 6 (an object's drop) is retired**: `tools/chain.py check` replays every `TC_ResolveDrops` call of the
  world logs through `tools/tc.py` with the quality roll modelled, and `tools/objects.py` no longer takes the drop's
  seeds: the object's unit seed after the drop equals the resolver's predicted exit seed, and the game seed after it is
  predicted from the items the drop creates; 59 object drops, 0 mismatches (§ 10). (fn:TC_ResolveDrops@0x0055A6D0,
  run:2026-10-15-objects)
- [C] **Oracle 13 (MonEquip's items) is modelled; reached in Phase 2, raised in part** (2026-10-21): its draws on the
  unit seed and the two game-seed steps per item are in the chain; the two stock classes with an `oninit` row (234 and
  267, Blood Raven) were not created on the Phase 1 logs, and Phase 2 created one of each, both reproduced, with `--cf
  monequip-off` failing both (chain/0003). The level skip, a second row, n of 2 or 3 and an occupied location are
  unreachable with the stock table and stay `[I]` (§ 11). A reading error of `tools/monstats.py` (the `oninit` byte) is corrected on
  the way (§ 11). (fn:sub_005D6B60_MonEquipInit@0x005D6B60, run:2026-10-20-chain)
- [I] **Oracle 20 (the pass-entry grid snapshot) is not retired**: the composed grid (activation stamp plus the
  logged window marks) already equals the snapshot in 3 871 of 3 998 pass rooms; the predicates still read the
  snapshot, the barrier grid of the flood stays an input (its builder is read, not modelled) and so does the type-11
  point (§ 12). (fn:sub_0054EC90_RoomPopulate@0x0054EC90, fn:LOGIC_BarrierGridBuild@0x0066C870)
- [C] **`tools/chain.py gen`** reproduces the seed tree the rng/seeds worked example logged from `-seed N` alone (game
  seed, the four game-creation draws, act bases, Act II tombs, level seeds) (§ 1). (fn:GAME_InitSeeds@0x0052C280,
  fn:DRLG_ActCreate@0x00642DA0, fn:DRLG_LevelCreate@0x00642AE0, run:2026-10-11-seed-tree)

## 1. `tools/chain.py`

- [C] `gen --seed N` gives, under the override branch of rng/seeds step 1: the game seed `Init(N)` and map seed `N`; the
  four game-creation draws in order, each seeding its object with `Init(low)`: monster regions (draw 1, then
  `tools/monpool.py build_all` for the difficulty and game type), the object-region seed (draw 2), the store seed
  (draw 3), the quest seed (draw 4); each act's `levelSeedBase` and its act-specific draws (`tools/rng.py act_seeds`);
  each level's create seed `Init(levelSeedBase + id)`. On `-seed 12345` it prints the worked example of
  [rng/seeds](../../specs/rng/seeds.md#worked-example): level 1 `015B2E78:0000029A`, Act II tombs 72 and 71, act seed
  `B7A5C418:63A93A78`; on `-seed 34844169`, level 134 `0000000D:0000029A`. `tools/test_chain.py` holds these cases.
  (fn:GAME_InitSeeds@0x0052C280, fn:sub_00547D20_MonRegionsInit@0x00547D20, fn:OBJRGN_Create@0x00546C60,
  fn:NPCSTORE_CtlCreate@0x00536070, fn:QUESTS_InitGame@0x00545D80, fn:DRLG_ActCreate@0x00642DA0,
  run:2026-10-11-seed-tree, run:2026-10-15-objects, run:2026-10-16-quest-drops)
- [I] What `gen` stops at is what needs an input of chain/0001 § 3.3: the level layouts are built when a level is
  first needed and the rooms activate in the player's order (§ 3.2 there), so `check` replays them on logs that carry
  that order. (fn:DRLG_LevelCreate@0x00642AE0, fn:DRLG_RoomActivate@0x006422A0)
- `check <log>...` runs, per log, the line sets it carries: item lines through `tools/items_chain.py` (affixes, props
  or both, split as in the items experiments record of 2026-10-15), and the summary counts every oracle still taken.

## 2. Oracle 2: the staff mods

- [C] With `--staff model` the default, `tools/chain.py check` over the 133 kept item logs (51 of
  run:2026-10-14-affixes, 50 of run:2026-10-14-props and -props-forced, 32 of run:2026-10-15-items-chain; each manifest
  `sha256sum -c` clean) reproduces 3 991 creations from the affix lines (the property roll and the staff mods
  modelled) and 3 170 from the property lines (the builders and the staff mods modelled), 0 failed; it predicts 99
  `STF1` exit seeds and the 64 `item_singleskill` entries of the final lists, and takes no staff-mods seed from a log
  (the former "exit not checkable" count of the props pass is 0). 14 logs carry no creation (sessions that never
  dropped an item). (fn:ITEMS_RollStaffMods@0x005C1260, fn:sub_005C0F90_StaffModsRoll@0x005C0F90,
  run:2026-10-14-affixes, run:2026-10-14-props-forced, run:2026-10-15-items-chain)
- [I] The classic body `sub_005C0D70_StaffModsRollV0` is not modelled; it runs only for an item of version 0, which no
  created item has (items/0005 § 10). (fn:sub_005C0D70_StaffModsRollV0@0x005C0D70)

## 3. Oracle 14: the unit seed after `SUnitCreate`

The world logs: the 62 kept logs of run:2026-10-13-mon-spawn (3), run:2026-10-14-mon-special (12),
run:2026-10-15-mon-stats (11), run:2026-10-14-collision (sessions 1–7) and run:2026-10-15-objects (sessions 2–30),
listed with their sha256 in `workspace/logs/chain-p1/inputs-world.sha256` (the first three checked against their
records by `tools/mon_sweep.py`'s run table).

- [C] `tools/monspawn.py` no longer takes the new monster's unit seed from `MU`. It computes `Init(low)` of the
  game-seed step, runs `sub_00547BC0_MonRegionFindAdd` on the unit seed against a region it tracks per game (the
  `tools/monpool.py` regions of `-seed N` and the difficulty, plus every append; an append rolls `MonVariantRoll(unit
  seed, entry, 3)`, `tools/mon_sweep.py findadd`), then the draws of `sub_00573CB0_MonStatsInit`
  (`tools/monstats.py Model.init_seed`: the appearance pick, the doomknight `Range(4)`, the HP draw, MonProp), and
  compares the result with `MU`. `tools/chain.py check` over the 62 logs: 8 075 creations, **7 953 unit seeds
  predicted**, 0 mismatches in 1 169 391 monspawn checks and 62 991 monstats checks; FindAdd found 7 251, appended 32,
  stale 792. The baseline step counts (7 852 of 2 steps, 193 of 3, 30 of 5 to 17) are all among the predicted ones but
  the 122 below. (fn:sub_00555230_SUnitCreate@0x00555230, fn:sub_00547BC0_MonRegionFindAdd@0x00547BC0,
  fn:sub_005BDB20_MonVariantRoll@0x005BDB20, fn:sub_00573CB0_MonStatsInit@0x00573CB0, run:2026-10-13-mon-spawn,
  run:2026-10-14-mon-special, run:2026-10-15-mon-stats, run:2026-10-14-collision, run:2026-10-15-objects)
- [C] The tracked region equals all 4 555 logged region snapshots (`P0`, `SU0`, `PM0`) once 117 appends made by
  creations the checker does not run are taken from the snapshot (class only: the region snapshot logs no sets). Those
  creations are the preset monsters of the presets window (oracle 16); a later creation of such a class takes its unit
  seed from the log (122, counted `ORACLE (world): unit seed after SUnitCreate (region entry appended outside the
  model: sets unknown)`). (fn:sub_00547BC0_MonRegionFindAdd@0x00547BC0, run:2026-10-15-objects)
- [C] Negative controls, `tools/chain.py check --cf` on the 11 mon-stats logs and objects sessions 3 and 5:
  `findadd-none` fails (416 monspawn mismatches, 663 unit seeds still equal) and `monprop-off` fails (26 monspawn
  mismatches; the SI checks of `tools/monstats.py`, which share the MonProp model, fail too); `L0` passes, as it should: `L` selects the MonLvl column of the HP range,
  and the HP draw is one step whatever the range when the range holds at least one value.
  (fn:sub_006538A0_MonLvlStats@0x006538A0, run:2026-10-15-mon-stats)
- [I] `MonEquipInit` (oracle 13) is still not modelled: a class with an `oninit` MonEquip row keeps its unit seed from
  the log (0 such creations on these logs). (fn:sub_005D6B60_MonEquipInit@0x005D6B60)

## 4. Oracle 16: the preset monsters of the presets window

`tools/objects.py` takes the room, object-region and game seeds at the `OPUX` of every preset unit that is not an
object. `tools/monspawn.py` now models each of those windows from the seeds at its `OPU0` (which `tools/objects.py`
predicts and asserts) to its `OPUX` (which it asserts), so the objects window holds no oracle where both checks pass.
`tools/objects.py` records, per window, the `OPUX` lines it took; `tools/monspawn.py` counts a window as having no
oracle left when it predicted every one of them.

- [C] **The class case**, `sub_0054E490_PresetClassSpawn` (called by `sub_0054E600_PresetMonSpawn` for an id below
  `nMonStats`), read in the disassembly (0x0054E490–0x0054E5EF): class 434 starts one cell to the left and, when
  `QUESTS_IsActive(game, 0x20)` is 0, takes mode 12; a class with MonStats2 flag 13 (`sub_004638A0_MonStats2FlagTest`,
  byte `+0x05` bit 5) places nothing; the request flags are 8 when MonStats `+0x0E` & 4 (neverCount), else 0;
  `SpawnAtPos(x, y, class, mode, −1, flags)`, and when it places nothing and `sub_0054E3A0_PresetRetryAllowed(class)`
  is 1, the same with radius 4; after a placement, MonStats2 flag 18 with class 432 (object class 571 under it) or 433
  creates an object. Predicted on the 62 world logs: 217 placed, 16 nothing placed, 16 refused by flag 13, 3 retries
  with radius 4; each creation's unit seed and every draw of `MonSpawnTry` predicted (§ 3's model).
  (fn:sub_0054E490_PresetClassSpawn@0x0054E490, fn:sub_004638A0_MonStats2FlagTest@0x004638A0,
  fn:sub_005B2F20_SpawnAtPos@0x005B2F20, fn:QUESTS_IsActive@0x005444B0, run:2026-10-15-objects)
- [I] `sub_0054E3A0_PresetRetryAllowed(class)` returns 0 for classes 229, 284–288, 392 and 393 (the byte table
  `0x0054E3E0` over classes 229–393, two jump targets at `0x0054E3D8`) and 1 for every other class, out-of-range ids
  included (the unsigned bound jumps to `mov eax, 1`). The 3 retries are of classes outside that list.
  (fn:sub_0054E3A0_PresetRetryAllowed@0x0054E3A0)
- [C] **The MonPlace fixed rows 17–32** (0x0054E973–0x0054EAA5): the class from the jump table `0x0054EB74` (17
  class 19, 18 class 58, 22 class 141, 23 class 278, 29 class 453, 30 class 492, or 529 in level 110, 31 class 522,
  32 class 438; rows 29–32 take mode 12), then `sub_0063EC70_LevelClassVariant` and `sub_0054E2A0_PresetFallenVariant`,
  flags 8 when neverCount, `SpawnAtPos` with radius −1 then 4 (no retry test on this path), and class 438 draws
  `Range(unit seed, 50)` after the creation. LevelClassVariant, read in the decompile: with no `mon` entries the class
  is kept; else the level's `mon` entry whose BaseId equals the class's BaseId; else from the BaseId record's
  NextInClass, up to the chain length (MonStats `+0x4A`, written at load by `sub_00651040_MonClassChain`) steps, each
  accepted while its Level (`+0xAA`) is at most Levels `MonLvlEx` (`+0x16`) + 1. Predicted: 66 placements (rows 17,
  18, 23, 29, 30, 31), the fallen and shaman variants of levels 5 and 76 among them. (fn:sub_0054E600_PresetMonSpawn@0x0054E600,
  fn:sub_0063EC70_LevelClassVariant@0x0063EC70, fn:sub_00651040_MonClassChain@0x00651040,
  fn:sub_0054E2A0_PresetFallenVariant@0x0054E2A0, run:2026-10-15-objects)
- [C] A preset whose MonPlace row or superunique places nothing (no request in the window) leaves the room and game
  seeds unchanged (35); a superunique or MonPlace 2/3 window (`SU0`/`PM0`, the plan 0018 model) has the `OPU0` seeds
  at its entry and the `OPUX` seeds at its exit (11). A tile unit (preset type 5, 29) steps the game seed once and
  gets `Init(low)` as its unit seed, with no other draw (rng/seeds 7a). (fn:sub_005557D0_PresetUnitDispatch@0x005557D0,
  fn:sub_00555230_SUnitCreate@0x00555230, run:2026-10-15-objects)
- [C] The window's position predicates (737 `CollisionTest`, 737 `SpawnClassCellTest`) are predicted on the
  activation model with the window's marks so far (the earlier presets' and objects' `CM` lines) on a copy of the
  cells; 15 whose cell lies in an activated room with no cells in the model are taken from the log and counted.
  Controls (`--cf`, objects sessions 2, 4 and 7): `lcv-off` (no LevelClassVariant or PresetFallenVariant) 25
  mismatches, `overlay-off` (no window marks) 19. (fn:sub_0064D9B0_CollisionTest@0x0064D9B0, run:2026-10-15-objects)
- [I] **Left as oracles**: the 12 placements of classes 432 and 433, whose object (class 571 under 432) is created
  inside the monster's window and belongs to `tools/objects.py`; the 3 `mode` values of class 434, taken from the
  request because `QUESTS_IsActive(game, 0x20)` is quest state (an input). Correction to chain/0001 § 2 row 17:
  InitFns 54 (7 calls) and 62 (4 calls) were reached on run:2026-10-15-objects; with InitFn 46 (16 calls) they are
  the oracles left in 19 windows. (fn:OBJINIT_CityDamnedSpawns@0x005506D0, run:2026-10-15-objects)
- [C] Creations the checker does not run (an `MU` line outside a modelled window: the InitFn spawns, the operate
  spawns, the 12 catapult windows) now update the tracked region (90 appends, sets unknown), so the unit seeds of
  later creations of those classes are not mispredicted; 34 such creations still take their unit seed from the log
  (§ 3 had 122). (fn:sub_00547BC0_MonRegionFindAdd@0x00547BC0, run:2026-10-15-objects)

## 5. Oracle 17: InitFn 46, City of the Damned

- [C] `tools/objects.py init_46` models `OBJINIT_CityDamnedSpawns` as read in the disassembly (the walk and its
  draws are in [objects/0001 § Plan 0048 Phase 1](../objects/0001-object-population.md#plan-0048-phase-1-initfn-46-modelled-2026-10-20)):
  all 16 calls of run:2026-10-15-objects (session 25, level 106) reproduce on the object-region seed, with each
  `OBJ_PosTestPadded` call's two position tests predicted on the grid model and each request (`MT0`: room, class,
  position, mode 1, radius −1, flags 0, entry room and game seeds) compared. (fn:OBJINIT_CityDamnedSpawns@0x005506D0,
  fn:OBJ_PosTestPadded@0x00550220, run:2026-10-15-objects)
- [C] `tools/monspawn.py` predicts the 21 requests from `MT0` to `MTX` (`RequestPass`: every `MonSpawnTry` draw on
  the room seed, the creation's game-seed step and unit seed), so the window's seeds after each request are
  predicted, not taken. (fn:sub_005B2A00_MonSpawnTry@0x005B2A00, fn:sub_00555230_SUnitCreate@0x00555230,
  run:2026-10-15-objects)
- [C] Over the 62 world logs, 1 245 of 1 265 objects windows now have no oracle left inside; the 20 others hold
  InitFn 54 (7 windows), InitFn 62 (3) or a catapult preset (12 `OPUX`, in 12 windows). Control: `--cf i46-stored`
  fails (10 mismatches). (fn:OBJINIT_CityDamnedSpawns@0x005506D0, run:2026-10-15-objects)
- [I] InitFns 54 and 62 (7 and 4 calls on run:2026-10-15-objects; chain/0001 § 2 row 17 says 47–69 were not reached,
  which is wrong for these two) and 47, 55, 66, 68, 69 (not reached) stay seed oracles: the assignment named InitFn 46
  only. (data:g_ObjInitFns@0x00731BC0, run:2026-10-15-objects)

## 6. Oracle 22: the `Orient89Unit` creations

- [I] What `sub_0066D9E0_Orient89Unit` makes at activation is a **preset unit** of the room, not a unit (the code
  that adds it is not read here; the logs show the flagged classes created later, as below): the units
  its rows name (`tools/drlg.py roomk` on objects sessions 5, 25 and 28: entry flag `0x20` set for classes 432 ×25,
  433 ×14, 434 ×8, 435 ×43, 524 ×14 and object 60 ×2) are created later in the presets window, through
  `PresetUnitDispatch`, as `OPU0` windows of type 1 (or 2 for the object: session 5, line 21663, an `OPU0` of id 60
  in level 111). The other `SUnitCreate` lines outside every window and pass of the 29 objects logs are 5 (objects
  60, 160 and 162; one is a portal, class 60 in mode 2, created after a pass ended); their origin is not followed. Its own draw, the `Range(3)` and the `0x20` flag were
  already modelled (plan 0027 Phase 2). (fn:sub_0066D9E0_Orient89Unit@0x0066D9E0,
  fn:sub_005557D0_PresetUnitDispatch@0x005557D0, run:2026-10-15-objects)
- [C] So their creations are the preset monster windows of § 4, whose class case now also creates the object under a
  catapult (0x0054E558–0x0054E5EF): after a placement of a class with MonStats2 flag 18, class 432 creates object 571 and
  class 433 object 572 with `SUnitCreate(2, class, UnitGetSubX(unit), UnitGetSubY(unit), game, room, 1, 0, 0)`.
  `tools/monspawn.py` checks the object's `OU0` (type, class, the monster's cell and room, the game seed) and steps
  the game seed; `tools/objects.py` models the creation itself inside the window (its unit seed, InitFn, PreOperate and
  mark, and the object-region seed, now asserted at `OPUX` instead of taken). 12 creations (8 under 432, 4 under 433)
  predicted on the 62 world logs, 0 mismatches. (fn:sub_0054E490_PresetClassSpawn@0x0054E490,
  fn:sub_0045ADF0_UnitGetSubX@0x0045ADF0, fn:sub_0045AE20_UnitGetSubY@0x0045AE20, fn:sub_00555230_SUnitCreate@0x00555230,
  run:2026-10-15-objects)
- [C] After this step 1 255 of 1 265 objects windows have no oracle left inside; the other 10 hold InitFn 54 (7) or
  InitFn 62 (3). (run:2026-10-15-objects)
- [I] Class 434's mode (`QUESTS_IsActive(game, 0x20)`) stays a quest-state input, taken from the request (3).
  (fn:QUESTS_IsActive@0x005444B0)

## 7. Oracle 19: the gate's DRLG parts (read; inputs kept)

- [I] `OBJ_PopulateGate` (0x00552560) tests, in order: `sub_0061A210_RoomWarpFlagsTest` → `sub_0066BB60_DrlgRoomWarpFlags`
  (the DRLG room's `+0x28 & 0x30000` not 0 closes the gate); `pop = sub_0061A1F0_RoomPopLevelId(room)` →
  `sub_0066BB20_DrlgRoomPopLevelId`, which is 0 when `+0x28 & 0x800000`, else the level id `[+0x58] → +0x1D0` (the field
  `sub_0066BAB0_RoomLevelId` reads); pop = 0 closes it; `sub_0061ABB0_RoomPresetPopTest` → `sub_0066BA90_DrlgRoomPresetPopTest`,
  0 unless the room's type `+0x48` is 1, then `sub_0067D7A0_OutRoomFlag80` (`[+0x20] → +0x54 & 0x80`); pop ≥ nLevels;
  `sub_0061AB00_RoomIsTown` → `sub_006426A0_LevelIsTown` on the level id (1, 40, 75, 103, 109). Then the level counters
  and `LevelRoomCount`, which counts the level's DRLG rooms without `0x800000` (and builds the level first when it is
  not built). (fn:OBJ_PopulateGate@0x00552560, fn:sub_0066BB60_DrlgRoomWarpFlags@0x0066BB60,
  fn:sub_0066BB20_DrlgRoomPopLevelId@0x0066BB20, fn:sub_0066BA90_DrlgRoomPresetPopTest@0x0066BA90,
  fn:sub_0067D7A0_OutRoomFlag80@0x0067D7A0, fn:sub_006426A0_LevelIsTown@0x006426A0, fn:sub_00642BE0_LevelRoomCount@0x00642BE0)
- [C] The logged gate inputs agree with that reading on all 1 265 `OG` lines of the 62 world logs (`tools/chain.py
  gate_inputs`): the 46 gates closed by `0x30000` read nothing further; `pop` is 0 or the room's level id in all
  1 219 others; the 869 town tests equal `LevelIsTown(level id)`; the 904 preset tests are 0 or `0x80`.
  (fn:OBJ_PopulateGate@0x00552560, run:2026-10-15-objects; output `o19-world-check.txt`)
- [I] **Not modelled, with the reason**: which DRLG rooms carry `0x30000` (a waypoint's room: `tools/drlg.py
  room_flags` predicts it for preset rooms from the DS1 scan, and for out rooms from the outdoor model's grid0),
  `0x800000` (the hidden-warp rooms of `HiddenWarpTilesAdd` and, on the logs, many rooms of levels 3, 42–44 and 103,
  whose setter is not read here) and the out room's `0x80`, and `LevelRoomCount`, are DRLG room state; the chain would
  need `tools/drlg.py`'s per-room predictions mapped to the active rooms through the `AROOM` lines. Until then they
  stay values taken from the `OG` line (1 265 gates, 26 `LevelRoomCount` reads), now checked against the reading.
  (fn:sub_0066BB20_DrlgRoomPopLevelId@0x0066BB20, fn:sub_00642BE0_LevelRoomCount@0x00642BE0)

## 8. Oracle 21: another room's seed in a pass

- [C] A request on a room other than the pass room (a frog demon placed on a neighbour's tile) took that room's seed
  from its first `MT0`. `tools/monspawn.py` now carries every room's seed as chain state: the roomk model's predicted
  activation seed at its `AROOM` line, then the pass model's seed at the end of each pass (`PX`), for the pass room and
  for every other room it drew on. Both such requests of the world logs (collision sessions 2 and 3, level 77) take
  the state's seed, which `MT0` then confirms, 0 mismatches. (fn:sub_005B2A00_MonSpawnTry@0x005B2A00,
  fn:sub_005B2700_SpawnPosOnTile@0x005B2700, fn:DRLG_RoomActivate@0x006422A0, run:2026-10-14-collision)
- [C] Control: `--cf state-stale` (a room keeps its first seed, its passes ignored) fails both (`MT0 rs` mismatches),
  so the requests read a seed the earlier pass of that room had moved. (run:2026-10-14-collision; output
  `o21-cf-state-stale.txt`)

## 9. Oracle 7: the gold piles' items

- [I] `sub_00559300_DropGoldPile`, read in the decompile: the item level is `LevelMonLvl(level, difficulty,
  expansion)` − 1 when above 1; the start cell is `(px + 2, py + 3)` when `RoomAtSubtile` finds a room there, else
  `(px, py)`; `sub_0064E810_FreeNearPair(room, start, size 1, masks 0x3E01 and 0x801)` gives the spot; then
  `ItemCreate` of `gld` in mode 3 at the spot, and the item flag `0x2000`. (fn:sub_00559300_DropGoldPile@0x00559300,
  fn:sub_0061DCA0_LevelMonLvl@0x0061DCA0, fn:sub_00463740_RoomAtSubtile@0x00463740, fn:sub_0064E810_FreeNearPair@0x0064E810,
  fn:sub_00558D90_ItemCreate@0x00558D90)
- [C] `tools/objects.py gold_drop` replaces the plan 0023 seed oracle (`OGP0` → `OGPX`): for all 71 drops of the 29
  objects logs the item's `SUnitCreate` (type 4, class 523, flags 1, mode 3) steps the game seed twice and gets the unit
  seed `Init(low)` of the first step (rng/seeds 7a), its mark is `RO 1 × 1` mask `0x200` at the spot, and the
  object-region seed does not move; all compared, 0 mismatches. (fn:sub_00559300_DropGoldPile@0x00559300,
  fn:sub_00555230_SUnitCreate@0x00555230, fn:UNIT_CollMarkRect@0x00620A70, run:2026-10-15-objects)
- [I] The spot: 49 drops land on a start cell the grid model finds free; 20 on the cell `COLL_FindFreeNear`'s ring
  (`tools/quests.py free_near`, quests/0002 § 4) gives on the grid model, a cell counted blocked when `COLL_WHTest`
  1 × 1 with either mask is not 0. Two disagree (objects session 29 line 19985: the model finds the start cell free and
  the game moved the pile one cell; one ring answer elsewhere); the second mask's exact role and `FreeNearPair`'s
  other argument are not read. There the spot is taken from the log and counted, and its window now counts as holding an oracle: 1 253 of
  1 265 windows have none left (§ 6 had 1 255 before the gold drops were followed into). (fn:COLL_FindFreeNear@0x0064DEA0,
  run:2026-10-15-objects)
- [I] The gold amount draws on the item's own seed, which these logs do not log; it is items/economy's.
  (fn:sub_00559300_DropGoldPile@0x00559300)

## 10. Oracle 6: an object's drop

- [C] All 510 `TC_ResolveDrops` calls of the 62 world logs (59 with an object source; the objects logs load
  `tools/gdb/tc-drops.gdb`) reproduce under `tools/tc.py replay --quality model`, each to its `TCEND` seed, with no
  quality oracle (`tools/chain.py check` runs it per log and fails on any failed call). (fn:TC_ResolveDrops@0x0055A6D0,
  fn:ITEMS_DropRollQuality@0x00558640, run:2026-10-15-objects; output `o6-world-check.txt`)
- [C] In `tools/objects.py` the chest drop (`OCT` → `OCX`) is no longer a seed oracle: the object's unit seed at `OCX`
  must equal the resolver's `TCEND` seed (59 of 59), so it is the tc model's; each item the resolver creates is
  `SUnitCreate`'s two game-seed steps with the unit seed `Init(low)` of the first (rng/seeds 7a), and the game seed at
  `OCX` is predicted (15 drops with no item, 29 with one, 14 with two, 1 with three); the object-region seed does not
  move. (fn:TC_ResolveDrops@0x0055A6D0, fn:sub_00555230_SUnitCreate@0x00555230, run:2026-10-15-objects)
- [C] A casket or barrel that spawns a monster before its drop (the operate monster spawn, oracle 8, a player-action
  input) now hands its exit game seed (its last `MTX`) to the drop that follows; before, that game seed was taken at
  `OCX` with the drop's. (0x00582280, run:2026-10-15-objects)
- [I] Still logged inside the drop: the dropped items' cells and marks (their drop-spot search is not modelled; their
  `CM` lines are applied from the log), and the item builds' own draws, which are the item chain's and need the item
  lines this logger does not write. (fn:sub_00558D90_ItemCreate@0x00558D90)

## 11. Oracle 13: MonEquip's items

- [C] The `monequip` record's `oninit` byte is at `+0x04` (`MonEquipInit` tests `(char) row[+4]`; the s16 at `+0x02` is
  the level it compares with the monster level), and a class's first row is the first record whose `monster` is the
  class (`MonStats +0x2A` is written at load, 0 in the `.bin`). `tools/monstats.py` read `+0x02` of row `+0x2A`, so its
  `MonEquipOracle` never fired; with the correction the stock table has two `oninit` classes, 234 and 267.
  Second source (added at the review): a full-table check of `monequip.bin` against `monequip.txt` (45 rows of 28 bytes
  after the u32 count): the byte at `+0x04` equals the `oninit` column and the s16 at `+0x02` the `level` column in all
  45, 0 mismatches; the two `oninit` rows are `bloodraven` (267) and `flyingscimitar` (234), each its class's first
  row. (fn:sub_005D6B60_MonEquipInit@0x005D6B60, fn:sub_005D30A0_MonEquipFirstRow@0x005D30A0, 0x005D6BA5) The table has no doc yet: the archivist's
  [MonEquip entry](../../backlog/archive/2026-10-20-architect-archivist-monequip-table-doc-for-plan-0048.md) holds it.
- [I] The model (`tools/monstats.py Model.monequip`, from monsters/0004 § 6): rows of the class from the first whose
  level is at most the monster level; per row, n = the leading locations in 1..10 (at most 3); if n > 0 one unit-seed
  step picks one (masked for a power of two, a step all the same), and a free location gets its item. In
  `tools/monspawn.py` each item adds two game-seed steps inside the creation. `tools/test_chain.py` checks the walk
  on stub rows. No creation of class 234 or 267 is in the 62 world logs (`grep` of their `MU` lines finds none), so
  the model is unreached here and stays `[I]` on these logs; the item builds themselves are the item chain's.
  (fn:sub_005D6B60_MonEquipInit@0x005D6B60, fn:sub_00573B20_MonEquipItemCreate@0x00573B20,
  fn:sub_00555230_SUnitCreate@0x00555230)
- [C] **Raised in part at Phase 2** (2026-10-21; scoped at the Phase 2 run 1 review): run:2026-10-20-chain creates
  class 267 (raven-xn2) and class 234 (cn2), each with its `oninit` row, the unit seed after `MonEquipInit` predicted
  and its one item reproduced by the item chain; `--cf monequip-off` (no location draw) fails both. The `[C]` covers
  the path the two stock rows take: one row of level 0, one location (`4`), so n = 1, the masked step, one item at a
  free location. (fn:sub_005D6B60_MonEquipInit@0x005D6B60, fn:sub_00573B20_MonEquipItemCreate@0x00573B20,
  run:2026-10-20-chain)
- [I] **The remainder, unreachable with the stock table**: the level skip (a first row whose level is above the
  monster level), a second row, n = 2 or 3 (n = 3 is the `RangeB` branch), and an occupied location skipped. Each of
  the two `oninit` classes has one row (`monequip.bin` rows 0 and 1, level 0, locations `4, 0, 0`), so no stock game
  reaches them. (fn:sub_005D6B60_MonEquipInit@0x005D6B60)
- The archivist's MonEquip table doc ([backlog entry](../../backlog/archive/2026-10-20-architect-archivist-monequip-table-doc-for-plan-0048.md))
  should record the `+0x04` `oninit` byte and the load-time `MonStats +0x2A`; a note is added to that entry.

## 12. Oracle 20: the grid snapshot, the barrier grid, the type-11 point (named, not modelled)

- [C] How far the composition already reaches: `tools/monspawn.py`'s R3 comparison over the 62 world logs
  (`o20-monspawn-r3.txt`) puts the activation model (every active room's stamp from its tile entries) beside the
  pass-entry snapshot in 3 998 pass rooms: 21 205 cells differ before the window's marks, 447 after them (20 758
  explained by the logged preset and object marks); 3 871 rooms are exact and 127 keep a residue of unit bits
  (`0x80` 260 cells, `0x100` 92, `0x1080` 65, `0x1100` 16, `0x404` 9, `0x400` 5): the players, monsters that walked in,
  items and corpses the assignment keeps as logged inputs. (fn:sub_0054EC90_RoomPopulate@0x0054EC90,
  fn:COLL_StampTileList@0x0064C790, run:2026-10-14-collision, run:2026-10-15-objects)
- [I] **Not modelled, with the reason.** The pass's predicates still read the logged snapshot (`SN`): replacing it with
  the composed grid needs the residue's cells as an explicit input list per pass room (a new input record), and the
  window's monster marks applied from the model rather than from the `CM` lines; neither is in the checkers yet. The
  residue also holds 14 cells of object bits (`0x400`, `0x404`) that no window mark explains, whose source is not
  followed. (fn:sub_0054EC90_RoomPopulate@0x0054EC90)
- [I] **The barrier grid** of the logic flood, `LOGIC_BarrierGridBuild` (read in the decompile): for each tile entry
  of the room (`RoomTile +0x14`, 0x30-byte records, count `+0x18`) whose flags `+0x14` have `& 0x1C000 = 0x4000`,
  whose orientation `+0x1C` is not 15 and whose bit 11 is clear, `sub_0067C4F0_GridCellOp(grid, position, 1, op 0)`;
  then the same test on the tile lists of the near rooms, at the position relative to the room when
  `sub_0066B9D0_RectContainsIncl` holds. It is a function of the tile entries `tools/drlg.py` builds, so it is
  modellable (or emulable under ADR-0015 with the entries as the declared read set). A probe, `tools/chain.py barrier`
  (`o20-barrier.txt`), builds it from the wall entries of the room's last activation dump: of the 307 `LG0` grids
  whose room has a dump in the 62 world logs, 258 equal the probe, 17 differ on the grid's edge only and 32 inside
  (1 814 `LG0` lines are of rooms with no dump: the flood runs for rooms never activated). The near rooms' lists the
  code walks (`[+0x54]` → groups of type 0 → tiles linked at `+0x20`) are not the activation dump's lists, which
  likely explains the rest; not followed. It stays a logged input of the flood (`LG0`). (fn:LOGIC_BarrierGridBuild@0x0066C870, fn:sub_0067C4F0_GridCellOp@0x0067C4F0,
  fn:sub_0066B9D0_RectContainsIncl@0x0066B9D0)
- [I] **The type-11 point** (`NWW`) stays logged: drlg/warps § D1 gives its rule (the waypoint object's tile for a
  `Position`-0 level, a level-seed draw among the level's slot-33 points otherwise), but the chain does not yet carry
  the level's preset unit lists to the walk that needs them. (fn:sub_0066B2B0_LevelPointFind@0x0066B2B0,
  fn:sub_0054DB50_NearWarpTest@0x0054DB50)

## 13. The composition over every kept log

- [C] `tools/chain.py check` over the 195 kept logs of § 2 and § 3 (133 item logs, 62 world logs; the input lists
  with their sha256 are `inputs-items.sha256` and `inputs-world.sha256`), with the final tool revisions
  (`tools-final.sha256`), passes: 0 sub-checks failed. Items: 3 991 creations from the affix lines and 3 170 from the
  property lines, 0 failed, 99 staff-mods exit seeds and 64 skill entries predicted. Tc: 510 `TC_ResolveDrops` calls
  reproduced with the quality roll modelled, 59 with an object source. World: 1 187 297 monspawn checks and 62 991
  monstats checks, 0 mismatches; 8 553 creations, **8 519 unit seeds predicted** (34 still taken: classes appended by
  creations outside the model); 311 class-case presets predicted (229 placed, the 12 catapult windows of § 6 now
  among them, so the counts of § 4 and § 3 grow by those), 35 that place nothing, 11 specials, 29 tile units; 21
  InitFn 46 requests; 2 other-room seeds from the chain state; 71 gold drops and 59 object drops with their seeds
  predicted; **1 253 of 1 265 objects windows with no oracle left inside**. The summary lists every oracle still
  taken from a log, by name and count; besides the ones named below, they are the plan's inputs (player actions,
  quest state, simulation: the state InitFns, the timer draws, the operate spawns) and, on the logs without a pass
  snapshot (plan 0014's), the position predicates and the whole window (oracle 15's older logs). (run:2026-10-14-affixes, run:2026-10-15-items-chain, run:2026-10-15-mon-stats,
  run:2026-10-14-collision, run:2026-10-15-objects)
- What remains of the assignment, with the reason: oracle 19's DRLG room flags and `LevelRoomCount` (§ 7: not handed
  from `tools/drlg.py` to the chain), oracle 20 (§ 12: the predicates still read the snapshot; the barrier grid and the
  type-11 point stay inputs), InitFns 54 and 62 (§ 5: outside the assignment), the 2 gold spots (§ 9), the class-434
  mode (quest state, § 6) and oracle 13's reach (§ 11: no logged creation).

## 14. Review re-run after the merge of `main` (architect, 2026-10-20)

- [C] `tools/chain.py check` over the same 195 logs with `main` merged (`main`'s plan 0038 batches H5b and H2a changed
  `tools/objects.py`, `tools/collision.py`, `tools/tc.py` and `tools/quality.py`; tool revisions in
  `tools-review.sha256`): 0 sub-checks failed (`review-merged-check.txt`). One count moves: **1 250** of 1 265 objects
  windows carry no oracle (was 1 253), because `main` made the nine `InitFn`s that create monsters seed oracles (objects/0001
  § S4b row 25); `InitFn` 18 holds 3 windows of these logs. Every other line of the summary equals `final-check.txt`.
  (fn:OBJ_PopulateGate@0x00552560, run:2026-10-15-objects)
- [C] The controls re-run on the merged tree fail as recorded: `--cf i46-stored` 10 mismatches, `state-stale` 2,
  `lcv-off` 25, `overlay-off` 19 (`review-cf-*.txt`). (fn:OBJINIT_CityDamnedSpawns@0x005506D0,
  fn:sub_005B2A00_MonSpawnTry@0x005B2A00, fn:sub_0063EC70_LevelClassVariant@0x0063EC70, run:2026-10-15-objects,
  run:2026-10-14-collision)
- [C] The `oninit` correction (§ 11) changes no earlier result: `tools/monstats.py check` on the 9 H4b logs (35 461
  checks) and the 6 forced-berserk logs (30 863) gives 0 monstats mismatches, with no MonEquip oracle hit; the H4b
  session 5b's DRLG mismatches are the second-game ones recorded at H4b, reproduced unchanged with `main`'s tools.
  (fn:sub_005D6B60_MonEquipInit@0x005D6B60, run:2026-10-15-berserk-forced)

## Kept outputs

`workspace/logs/chain-p1/`, one path base, `manifest.txt` (`sha256sum -c manifest.txt` from that directory):
`o2-items-check.txt` (`tools/chain.py check` over the 133 item logs), `o14-world-check.txt` (over the 62 world
logs), `o14-cf-{findadd-none,monprop-off,L0}.txt` (the controls), `o16-world-check.txt` and
`o16-cf-{lcv-off,overlay-off}.txt` (oracle 16), `o17-world-check.txt` and `o17-cf-i46-stored.txt` (oracle 17), `o22-world-check.txt` (oracle 22), `o19-world-check.txt` (oracle 19), `o21-world-check.txt` and
`o21-cf-state-stale.txt` (oracle 21), `o7-world-check.txt` (oracle 7), `o6-world-check.txt` (oracle 6), `o13-world-check.txt` (oracle 13), `o20-monspawn-r3.txt` (`tools/monspawn.py check` over the 62 world
logs, for the R3 counts of oracle 20, same tools as `tools-o13.sha256`), `o20-barrier.txt` (`tools/chain.py barrier`,
tools in `tools-o20.sha256`), `final-check.txt` (§ 13, tools in `tools-final.sha256`), and the input lists `inputs-world.sha256` and
`inputs-items.sha256` (paths relative to `chain-p1/`, so `sha256sum -c` runs from there too). The review's re-runs (§ 14) are
`review-*.txt` with `tools-review.sha256`, hashed in `review-manifest.txt` (`f0dd87f8…`) in the same directory. The tool revisions
behind these outputs are recorded in `tools-o14.sha256`, `tools-o16.sha256`, `tools-o17.sha256`, `tools-o22.sha256`, `tools-o19.sha256`, `tools-o21.sha256`, `tools-o7.sha256`, `tools-o6.sha256` and `tools-o13.sha256` (paths relative to the repository
root).

## Open questions

- None yet for the retired oracles; the remaining assignment is in the plan 0048 log.
