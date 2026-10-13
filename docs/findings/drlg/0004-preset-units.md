# 0004 — Preset units: the DS1 unit list, the keep/drop rolls and the LvlPrest columns

> **Subsystem:** drlg/preset
> **Question:** Which preset units does a DS1 put into a room (after the act rewrites and the keep/drop rolls), and what does each `LvlPrest` column still `[L]` do?
> **Date:** 2026-10-13   **Plan:** 0016   **Status:** answered (Phase 1); corroborated (Phase 2, run:2026-10-13-drlg-preset)

## Answer (summary)

Phase 2 reproduced the whole pipeline bit-exactly with no boundary oracle: 2210 preset room unit lists over all five
acts and towns, Normal, Nightmare and Hell, 123 606 checks, 0 mismatches (run:2026-10-13-drlg-preset). Branches the
run did not reach stay `[I]` and are named in each bullet.

- [C] **Keep/drop rolls.** `sub_00667620_PresetUnitDropRolls` copies the DS1's unit list into the preset instance
  (`+0x38`). It walks the list from its head, which is reverse file order. Ten ids draw once each, on the seed its
  caller passes; `r` is the low dword after one `RNG_Next` step. The run saw both outcomes for MonStats 204/205, MonPlace
  34 and object 581, and the kept outcome for MonPlace 35: 44 drawing calls among 962 checked calls
  (fn:sub_00667620_PresetUnitDropRolls@0x00667620, run:2026-10-13-drlg-preset):
  - MonStats 204/205 (`act2vendor1/2`) and 371/372 (`lightningspire`, `firetower`): kept when `r % 3 == 0` (unsigned).
  - MonPlace 33 (`place_group25`): kept when `r & 3 ≠ 0`.
  - MonPlace 34 (`place_group50`): kept when `r & 1 ≠ 0`.
  - MonPlace 35 (`place_group75`): kept when `r & 3 == 0`.
  - Objects 196 and 261 (floor traps): kept when `r & 1 == 0`.
  - Object 581 (above the objects table): kept when `r & 3 ≠ 0`.

  Every other unit is kept with no draw. A kept unit is a copy whose `x`/`y` and path points are offset by the
  instance origin ×5, prepended, so the kept list is back in file order. (fn:sub_00667510_PresetUnitCopy@0x00667510,
  run:2026-10-13-drlg-preset)
- [I] Four tests were not reached in the run and rest on the disassembly, one address per branch:
  - MonStats 371/372 (`mod 3 = 0`): `0x00667721`, the switch at `0x0066771A` through the byte table `0x006677DC`,
    whose index 0 is taken only by ids 204, 205, 371 and 372 (204/205 reached, 371/372 not);
  - MonPlace 33 (`& 3 ≠ 0`): `0x00667687`, the test it shares with object 581 (581 reached);
  - the dropped outcome of MonPlace 35 (`& 3 = 0`): `0x00667794` (only the kept outcome reached);
  - objects 196/261 (`& 1 = 0`): `0x006676D0`.

  MonPlace 34's test (`& 1 ≠ 0`, `0x006677B8`, `jmp 0x0066769B`) was reached with both outcomes.
  (fn:sub_00667620_PresetUnitDropRolls@0x00667620)
- [C] **Two callers, one roll per instance.** `sub_00667970_PresetMapScan` rolls on the **level seed** (`level
  +0x1C4`) at room creation, for records with `Scan` or `Pops` non-zero (391 calls). Otherwise
  `sub_00667890_PresetRoomLoadDs1` rolls on the **room seed** (`room +0x14`) of the first room of the instance that
  loads its DS1 (571 calls). That seed is still the one `DRLG_RoomCreate` set, `step(Init(level lo))`
  (`0x0066B44A`–`0x0066B477`), because the roll comes before the room's re-seed. Both load the DS1 into instance
  `+0x0C`, and `PresetRoomLoadDs1` rolls only while that slot is empty. (fn:sub_00667970_PresetMapScan@0x00667970,
  fn:sub_00667890_PresetRoomLoadDs1@0x00667890, fn:DRLG_RoomCreate@0x0066B3E0, run:2026-10-13-drlg-preset)
- [C] **Act rewrites in `DS1_Parse`.** These apply after the MonPreset mapping and turn the unit into an object
  (type 2, mode 0). The run reproduced lists containing act index 2's MonStats 297 (`natalya`) → object 382 and act
  index 4's 514 (`nihlathak`) → object 461. (fn:DS1_Parse@0x00665950, 0x00665CB2, run:2026-10-13-drlg-preset)
- [I] The other rewrites (act index 2: 366 `compellingorb` → object 404; act index 4: 537..539 `ancientstatue1..3` →
  `1013 − id`) were not in a rolled DS1 of the run. `0x004E6C50` is only a MonStats range check (`id` if
  `0 ≤ id < nMonStats`, else −1). (fn:DS1_Parse@0x00665950, fn:MONSTATS_ValidId@0x004E6C50)
- [C] **Into the room.** `sub_00666710_PresetUnitsToRoom` moves each instance unit whose subtile position lies in the
  room's rectangle ×5 (half-open) to the room list (`room +0x5C`), prepended and re-expressed relative to the room
  origin. Path points keep their instance coordinates. (fn:sub_00666710_PresetUnitsToRoom@0x00666710,
  run:2026-10-13-drlg-preset)
- [C] `PresetRoomLoadDs1` adds the client-only river objects 40/41/42/65 once per instance (`Def` 1, 26, 27 seen, on
  rooms with flag `0x40000`), every one with `flags` bit 0. (fn:sub_006663C0_PresetClientObjects@0x006663C0,
  run:2026-10-13-drlg-preset)
- [I] It also adds the Blood Moor centre monster: MonStats 266 `navi` at the instance centre, for `Def` 4–7 in level 2
  with file index 3. Not reached in the run. (fn:sub_006664A0_PresetCentreMonster@0x006664A0)
- [C] **Server handover.** `sub_005559A0_RoomPresetUnits` walks the room list twice: first every unit that is not a monster, then the monsters (373 of 373 walks with spawns). In 689
  walks the modelled room list was the tail of the walked list. At the head were units that other code prepends
  after `PresetUnitsToRoom`: objects 14–16, 23–25, 27, 64, 449 and type-5 units, one of them from
  `sub_0066D9E0_Orient89Unit` (caller `0x0066DAEE`). Those are inputs here (owners `objects`, `drlg/warps`).
  (fn:sub_005559A0_RoomPresetUnits@0x005559A0, fn:sub_0066BF30_PresetUnitCreate@0x0066BF30,
  run:2026-10-13-drlg-preset)
- [C] **A re-prepared room keeps its list.** When `PresetUnitsToRoom` runs again for a room (108 rooms, both copies),
  the room list already holds that room's previous list. In 34 of them other code had prepended 1 or 3 units in
  between, as at the server walk. `PresetUnitsToRoom` prepends the newly moved units (none, since the instance list
  lost them on the first pass). In 19 units, all monsters, the path pointer had become null in between. The checker
  asserts the previous modelled list as the tail. (fn:sub_00666710_PresetUnitsToRoom@0x00666710,
  run:2026-10-13-drlg-preset)
- [I] The walk skips every unit with `flags` (`+0x1C`) bit 0, so the client river objects and DS1 `flags = 1`
  (`worldstoneeffect`) never spawn on the server. No flagged unit reached a server walk in the run: the river objects
  exist only on the client copy. (fn:sub_005559A0_RoomPresetUnits@0x005559A0)
- [I] `sub_005557D0_PresetUnitDispatch` routes by type and id: type 1 to `sub_0054E600_PresetMonSpawn`, type 2 with
  id > 573 to `0x0054F490`, type 2 with id 573 to nothing, every other unit to `sub_00555230_SUnitCreate`. In levels
  133–136 the walk has extra filters (not reached): level 136 makes only the first pass, so no preset monster spawns,
  and skips objects 26, 268 and 269; levels 133 and 135 skip object 397; level 134 skips object 402 and the one object
  at which a per-game counter (`game +0x1DE4`) reaches `game +0x7C % 3 + 3`. (fn:sub_005557D0_PresetUnitDispatch@0x005557D0, fn:sub_005559A0_RoomPresetUnits@0x005559A0)
- **LvlPrest columns** (§ LvlPrest columns):
  - [C] `Populate` 0 sets room flag `0x800000`, for which `sub_0061A1F0_RoomPopLevelId` returns 0: no random population
    (241 calls on `Populate` 0 rooms, all 0). Preset units still spawn: 48 preset monsters created in `Populate` 0
    rooms (Harrogath, the Pandemonium Fortress). (fn:sub_0061A1F0_RoomPopLevelId@0x0061A1F0,
    run:2026-10-13-drlg-preset)
  - [C] `sub_0066BD50_RoomNoPopNearTown` also sets `0x800000` on `Populate` 1 rooms: a room outside a town whose
    neighbour room is in a town level (`sub_006426A0_LevelIsTown`: levels 1, 40, 75, 103, 109). Two counts in the
    run, both from the two logs with `FLG` lines (`preset-play-act4`, `preset-play-act5`):
    - **22 flag sets** at `0x0066BD92`, on 22 distinct preset rooms (10 + 12);
    - **16 `RoomPopLevelId` returns of 0** on those rooms: 8 of the 22 were populated, with two calls each, all 0.
      The other 14 had no `RoomPopLevelId` call in the logs.

    (fn:sub_0066BD50_RoomNoPopNearTown@0x0066BD50, fn:sub_006426A0_LevelIsTown@0x006426A0, run:2026-10-13-drlg-preset)
  - [I] `sub_0066E360_HiddenWarpTilesAdd` sets `0x800000` at `0x0066E37E` on a room with hidden warp tiles. The run
    logged no flag set there, so this rests on the disassembly. (fn:sub_0066E360_HiddenWarpTilesAdd@0x0066E360)
  - [C] `Logicals` selects the room's logic-region builder: 0 calls `sub_0066CCB0_SpawnBoxesSingle` (logic flags bit
    0), 1 calls `sub_0066D110_LogicRegionsFromDs1` (flags bit 1). Both copies build them (the flag bit checked on 1540
    preset rooms). The client reads a wall entry's box pointer (`+0x10`) and that box's region id every frame in
    `sub_004DD060_WallCutawayTest` (`0x004DD075`, `0x004DD085`, watch reads). The run checks only the builder
    selection and these reads. (fn:sub_00666AC0_PresetRoomTilesBuild@0x00666AC0, fn:sub_004DD060_WallCutawayTest@0x004DD060,
    run:2026-10-13-drlg-preset)
  - [I] What the builders produce: 0 gives one region covering the room, 1 floods the DS1 cells into regions (ids from
    level counter `+0x1DC`, merged across neighbour rooms of one level), one box per run of equal cells, and each
    wall tile entry's `+0x10` pointing to its region box. No region, box or wall pointer was reproduced. Owner:
    `drlg/collision` (research map, 2026-10-13). (fn:sub_0066D110_LogicRegionsFromDs1@0x0066D110,
    fn:sub_0066CCB0_SpawnBoxesSingle@0x0066CCB0, fn:sub_0066CA50_LogicBoxesFromGrid@0x0066CA50,
    fn:sub_0066C9C0_LogicWallBoxes@0x0066C9C0)
  - [I] `sub_004DD060_WallCutawayTest` returns true for a wall whose region id differs from the global
    `0x007C8A0C` and whose box starts past `0x007C8A08`/`0x007C8A10`. Without logic regions it falls back to a test on
    the wall's orientation near that point. Read as the player's region and tile, this is the wall cut-away the
    sources call wall transparency. The three globals are not traced. (fn:sub_004DD060_WallCutawayTest@0x004DD060)
  - [I] The same boxes are the server's spawn areas (monsters/0002 § 5: `sub_0054EC90_RoomPopulate` reads box `+0x10`,
    `+0x20`, `+0x28`). The run did not catch that read (Open questions). (fn:sub_0054EC90_RoomPopulate@0x0054EC90)
  - [I] `Outdoors` ORs `0x80000` into the room flags. `Animate` adds animated-tile frame lists, and `+0x024` is their
    period (0 means 80). `KillEdge` and `FillBlanks` are as in drlg/0002. `AutoMap` gates the act callbacks, which are
    null on the server and drive the automap on the client. `Scan` and `Pops` gate the map scan.
    (fn:sub_00666AC0_PresetRoomTilesBuild@0x00666AC0, fn:sub_00667970_PresetMapScan@0x00667970)
  - [C] `Pops` is the capacity of the roof-pop tables. **`PopPad` is read** by the client's
    `sub_006671E0_PresetPopsUpdate` (`0x00667255`, `0x00667261`, the only reader the watchpoint saw): the trigger
    rectangle of pop *k* is `(x·5, y·5, w·5 + PopPad, h·5 + PopPad)` in subtiles, half-open, so a negative `PopPad`
    pulls in the far x and y edges. The model of that test reproduces 6443 logged player positions, 70 of them
    decided by `PopPad`. (fn:sub_006671E0_PresetPopsUpdate@0x006671E0, fn:sub_0066B980_RectContains@0x0066B980,
    run:2026-10-13-drlg-preset)

  None of these columns draws. (§ LvlPrest columns)
- [I] **Type-2 rooms never read DS1 substitution data.** No code reads a preset instance's DS1 substitution layer or
  groups (`+0x48`/`+0x4C`/`+0x50`). The only group reader, `sub_006704E0_LvlSubLoadDs1`, reads the DS1 a `LvlSub`
  record names. The 429 groups in `LvlPrest` DS1s are dead data. (fn:sub_006704E0_LvlSubLoadDs1@0x006704E0)
- [C] **Level 27's preset index** is written while `sub_006772C0_LevelLinkBuild` handles level 6, from level 6's link
  value `v` and one draw `r` on the act seed: `v = 3` gives index `(~r) & 1` (6 draws, and level 27 was built with that
  index twice). The run confirms the formula and the single step on the act seed as logged just before the draw.
  (0x006774F9, fn:sub_006772C0_LevelLinkBuild@0x006772C0, run:2026-10-13-drlg-preset)
- [I] Where this draw falls in the act seed's sequence: the act seed before it was taken from the log, not
  predicted. The earlier draws are `LevelLinkBuild`'s (`drlg/warps`), so its position is that row's to establish.
  (fn:sub_006772C0_LevelLinkBuild@0x006772C0)
- [I] `v = 1` gives `2 − (r & 1)`; any other `v` draws nothing and writes nothing. The `v = 1` branch was not reached.
  (0x006774F9)

## Leads used

Blind first: every claim above was written from the code in Phase 1, before any community source was fetched. The
sources below were fetched and read on 2026-10-13 (plan 0016 Phase 1b) and are registered in
[sources.md](../../sources.md). Agreement promotes nothing. Two pages found in the search were registered
`rejected` and not used (`src:pk-maze-ds1-mechanisms`, `src:nefarius-metalstorm-log`). The three `contradicted`
verdicts were required Phase 2 cases. run:2026-10-13-drlg-preset settled them: `Populate` stays contradicted (the
sources are wrong for 1.14d), and `Logicals` and `PopPad` become `held with refinement` (the finding was wrong).

**Keep/drop rolls and act rewrites**

- [L] src:siramy-ds1-any-units, src:siramy-ds1edit, src:pk-hardcoded-ds1: no statement that any preset unit appears
  only by chance; `place_group25/50/75`, `act2vendor1/2`, `lightningspire`/`firetower` and the floor traps are not
  named. **not covered**
  Detail: the ten drawing ids and their keep probabilities (3/4, 1/2, 1/4 for `place_group25/50/75`, the inverse
  of the names) rest on the code alone (`0x0066777D` → `0x00667687`). No source to contradict them was found.
  `src:pk-hardcoded-ds1` reports clearings that "sometimes … will not appear", but those are `File` variants of
  outdoor presets, not units.
- [L] src:siramy-ds1-any-units: DS1 type-1 ids map through per-act MonPreset ranges ("Act 1 = entries 0 to 59 …
  Act 5 = entries 240 to 299"). It says nothing of a unit turned into an object in act index 2 or 4. **not covered**
  Detail: the rewrites (297 → 382, 366 → 404; 514 → 461, 537..539 → `1013 − id`) rest on the code alone
  (0x00665CB2).

**LvlPrest columns** (`src:pk-lvlprest-guide` describes 1.10–1.14; `src:d2dfg-blizzard` states no version)

- [L] src:pk-lvlprest-guide: `Populate` "If set to 0 monsters will not be able to spawn on the map. NOTE: Causes
  Unhandled Exception if you add other monster objects when column is set to 0." src:d2dfg-blizzard: "If equals 0,
  then units will never spawn in the Level Preset." **contradicted**
  Detail: the finding has `Populate` 0 suppressing only random population (room bit `0x800000` →
  `RoomPopLevelId` 0). Preset units go to `RoomPresetUnits`, which skips only `flags` bit 0. The shipped data
  carries preset monsters under `Populate` 0: `townWest.ds1` (`Def` 863, Harrogath) has type-1 units, as do the
  act-3 treasure rooms (`Def` 703/704, e.g. `DungRm1A.ds1`). **Settled** by run:2026-10-13-drlg-preset: in Harrogath
  and the Pandemonium Fortress (`Populate` 0) `RoomPopLevelId` is 0 on all 241 calls, and 48 preset monsters are
  created. A reimplementation must not drop preset units under `Populate` 0. The run also shows the column is not
  the only switch: rooms next to a town lose population too (Answer).
- [L] src:pk-lvlprest-guide: `Logicals` "Set it to 1 to allow wall transparency." src:d2dfg-blizzard: "If equals 0,
  then walls will always appear solid." **held with refinement** (was `contradicted` in Phase 1b)
  Detail: run:2026-10-13-drlg-preset watched the boxes. With `Logicals` 1 every wall tile entry points to its region
  box, and the client reads both every frame in `sub_004DD060_WallCutawayTest`, which cuts away walls of another
  region. With `Logicals` 0 there is one region and no per-wall box, so the client falls back to a geometric test.
  The same boxes are also the server's spawn areas (monsters/0002). The function is renamed
  `sub_0066D110_LogicRegionsFromDs1` (was `…SpawnBoxesFromDs1`).
- [L] src:pk-lvlprest-guide: `Outdoors` "Set to 1 for outdoor maps and 0 for indoors." src:d2dfg-blizzard: "…
  classified as an outdoor area, which can mean that lighting will function differently." **held with refinement**
  Detail: 1.14d ORs `0x80000` into the room flags (`sub_00667ED0_PresetRoomsCreate`), and no reader of that bit
  was found. The lighting effect is a lead only (Open questions).
- [L] src:pk-lvlprest-guide: `Animate` "1 makes the animated tile to play their animation. 0 disables animations.
  NOTE: Animated tiles, in levels with Animate = 0, will display a random yet static frame." src:d2dfg-blizzard:
  same, without the note. **held with refinement**
  Detail: 1 builds the frame lists (`sub_0066D700_AnimTilesBuildAll`) and sets room bit `0x8000000`. The "random
  static frame" under 0 is not in the finding. If it draws, the draw is on the client tile path, which is not read.
  The shipped data has `Animate` 1 only on the 33 lava records.
- [L] src:pk-lvlprest-guide, src:d2dfg-blizzard: no column at `+0x024`. **not covered**
  Detail: the animation period (0 means 80) at `0x00666D80` rests on the code alone. The value is 0 in every
  record.
- [L] src:pk-lvlprest-guide: `KillEdge` "Removes the tiles bordering the east and south edge of the ds1 in game."
  src:d2dfg-blizzard: "remove tiles that border the size of the Level Preset". **held**
  Detail: drlg/0002 § Room tile build applies it only where the room's right/bottom edge is the preset's
  right/bottom edge. That matches "east and south" in Phrozen Keep's wording. The Blizzard guide's wording does
  not name the sides.
- [L] src:pk-lvlprest-guide: `FillBlanks` "Setting to 1 makes all empty spaces unwalkable." src:d2dfg-blizzard:
  "all blank tiles … filled with unwalkable tiles". **held with refinement**
  Detail: drlg/0002 uses it as the filler flag for floor layer 0 only.
- [L] src:pk-lvlprest-guide: `AutoMap` "setting it to 1 will reveal the full automap. NOTE: Only works for preset
  maps". src:d2dfg-blizzard: "automatically completely revealed on the Automap". **held with refinement**
  Detail: it gates the act callbacks `+0x454`/`+0x488`, which are null on the server and drive the client
  automap. The data has it on the five towns only.
- [L] src:pk-lvlprest-guide: `Scan` "Setting it to 1 allows warps to be selected." src:d2dfg-blizzard: "allow the
  usage of warping with waypoints (This requires that the Level Preset has a waypoint object)". **held with
  refinement**
  Detail: `Scan` (or `Pops`) gates `PresetMapScan`. The scan collects style 30–33 cells (warp markers) into level
  `+0x2C`, marks the cells of objects with record `+0x167` bit `0x40`, and moves the keep/drop rolls onto the
  level seed. The rolls are not in either source. The waypoint reading is plausible only through the object
  bit, which is not read (`objects` row).
- [L] src:pk-lvlprest-guide: `Pops` "the special tiles with the Style (main-index) of 8 - 29. … You can only have
  one set of each style of pop." src:d2dfg-blizzard: "how many Pop tiles are defined in the Level Preset file".
  **held with refinement**
  Detail: 1.14d uses `Pops` as the capacity of the pop tables, one entry per distinct style 8–29 of orientation
  10/11. "One set per style" matches the one-entry-per-style table. The roof hiding is client-only
  (`sub_006671E0_PresetPopsUpdate`).
- [L] src:pk-lvlprest-guide: `PopPad` "determines the line of the 'trigger pad'. It determines the number of
  sub-tile units south & west the trigger line is offset." src:d2dfg-blizzard: "the size of the Pop tile area, by
  using an offset value". **held with refinement** (was `contradicted` in Phase 1b)
  Detail: Phase 1 missed the reader. `sub_006671E0_PresetPopsUpdate` adds `PopPad` to the trigger rectangle's width
  and height in subtiles (`0x00667255`, `0x00667261`). A watchpoint on Harrogath's `+0x3C` saw only that reader, and
  the model reproduces every logged player position (run:2026-10-13-drlg-preset). In the sources' terms the
  "trigger line" is the rectangle's far x and y edges, moved by `PopPad` subtiles; only those two edges move.

**Path `action`**

- [L] src:siramy-ds1edit § Path Editing: "the (hardcoded) 'Action' (animation and / or sound) that the NPC will do
  at a particular place". It also says "only Type 1 (Monster / NPC) objects can use paths in the game", and
  (§ F10) the NPC "will only use the points … (and randomly), and they'll never go back to their original
  starting position". **not covered**
  Detail: the finding reads no consumer of the path points (monster AI, ADR-0002), so it has no claim to compare.
  The lead goes under Open questions. The type-1 statement is a gap: two shipped paths have object owners, one of
  them `nihlathak` after the act-index-4 rewrite.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x00667620` | `sub_00667620_PresetUnitDropRolls` | copy the DS1 units into the instance list with the keep/drop draws | C |
| `0x00667510` | `sub_00667510_PresetUnitCopy` | allocate a unit copy offset by the instance origin (path copied too) | C |
| `0x006660B0` | `sub_006660B0_PresetPathCopy` | copy a path (count, 12-byte points) | I |
| `0x00643560` | `sub_00643560_TileToSubtile` | `x *= 5; y *= 5` | I |
| `0x00667890` | `sub_00667890_PresetRoomLoadDs1` | load the DS1 and roll on the room seed (once per instance), centre monster, client objects | C |
| `0x00667970` | `sub_00667970_PresetMapScan` | `Scan`/`Pops` gate; load the DS1 and roll on the level seed; scan the wall cells | C |
| `0x00666E00` | `sub_00666E00_PresetPopsFinish` | pop rectangles to absolute tiles, pop index `style/4 − 1` | I |
| `0x00666710` | `sub_00666710_PresetUnitsToRoom` | move the units in the room rectangle to `room +0x5C` | C |
| `0x006664A0` | `sub_006664A0_PresetCentreMonster` | add MonStats 266 at the instance centre | I |
| `0x006663C0` | `sub_006663C0_PresetClientObjects` | client river objects (flag bit 0) | C |
| `0x006661A0`, `0x00666220` | `sub_006661A0_PresetClientUnitsA`, `sub_00666220_PresetClientUnitsB` | object 65 every 8 tiles down a column / objects 40, 41, 41, 41, 42 in a row, per DS1 row | C |
| `0x0066BF30` | `sub_0066BF30_PresetUnitCreate` | allocate one unit, prepend to `ECX+0x5C` when `ECX` is set | I |
| `0x004E6C50` | `MONSTATS_ValidId` | `id` if `0 ≤ id < nMonStats`, else −1 | I |
| `0x005557D0` | `sub_005557D0_PresetUnitDispatch` | server: route one preset unit by type and id | I |
| `0x0066D110` | `sub_0066D110_LogicRegionsFromDs1` | logic regions from the DS1 layers (`Logicals` = 1); was `sub_0066D110_SpawnBoxesFromDs1`. Selection and flag bit `[C]`; its regions were not reproduced | I |
| `0x0066CA50` | `sub_0066CA50_LogicBoxesFromGrid` | one box per run of equal region cells, prepended to the logic record `+0x30` | I |
| `0x0066C9C0` | `sub_0066C9C0_LogicWallBoxes` | each wall entry `+0x10` = its region box (0 with one region) | I |
| `0x004DD060` | `sub_004DD060_WallCutawayTest` | client, per wall: region id against the player's (`0x007C8A0C`); else an orientation test | I |
| `0x0066BD50` | `sub_0066BD50_RoomNoPopNearTown` | room outside a town with a neighbour room in a town: `+0x28 \|= 0x800000` | C |
| `0x006426A0` | `sub_006426A0_LevelIsTown` | level id 1, 40, 75, 103 or 109 | I |
| `0x0066D290` | `sub_0066D290_AnimTilesCount` | count the animated-tile entries of a grid (`Animate`) | I |
| `0x0066D700` | `sub_0066D700_AnimTilesBuildAll` | `AnimTilesBuild` for floors, walls and roofs with the `+0x024` period | I |
| `0x006671E0` | `sub_006671E0_PresetPopsUpdate` | client roof pops: trigger rectangles with `PopPad`, tick-count timers | C |
| `0x00667060` | `sub_00667060_PresetPopSet` | client: show or hide one pop's tiles (`ECX` pop rectangle, main index, flag) | I |
| `0x00459150`, `0x004591A0` | `sub_00459150_ClientActRoomCb`, `sub_004591A0_ClientTownCb` | client act callbacks `+0x454` / `+0x488` | I |

## Walkthrough

### Where the unit list comes from

`DS1_Parse` builds the DS1's unit list (drlg/0001 § Object entries), prepending each unit, so the head is the last
entry in the file. The act rewrites sit between the MonPreset mapping and `PresetUnitCreate`:

```c
// fn:DS1_Parse@0x00665950, 0x00665CB2 (disassembly, renamed); act = header act clamped to ≤ 4; id after MonPreset
if (act == 2 && id < nMonStats) {
  if      (id == MONSTATS_ValidId(297)) { id = 382; type = 2; mode = 0; }   // natalya       -> object 382
  else if (id == MONSTATS_ValidId(366)) { id = 404; type = 2; mode = 0; }   // compellingorb -> object 404
} else if (act == 4 && 0 <= id && id < nMonStats) {
  if      (id == 514)              { id = 461;        type = 2; mode = 0; } // nihlathak
  else if (536 < id && id <= 539)  { id = 1013 - id;  type = 2; mode = 0; } // ancientstatue1..3 -> 476..474
}
```

- [I] The comparison uses the id **after** the MonPreset mapping, and only MonStats-range ids can match.
  (0x00665CB2–0x00665D3E, fn:MONSTATS_ValidId@0x004E6C50)

### The keep/drop rolls

```c
// fn:sub_00667620_PresetUnitDropRolls@0x00667620 (disassembly-checked; stack arg = seed, EDX = instance)
ox = inst.x * 5;  oy = inst.y * 5;                       // +0x10, +0x14 (tiles) -> subtiles
for (u = inst.ds1.units; u; u = u.next) {                // +0x0C -> +0x54; reverse file order
  if (u.type == 1) {
    if (u.id < nMonStats) {
      if (u.id in {204, 205, 371, 372}) { r = RNG_Next(seed); if (r % 3 != 0) continue; }
    } else if (u.id - nMonStats >= nSuperUniques) {      // MonPlace range
      p = u.id - nMonStats - nSuperUniques;
      if (p == 33) { r = RNG_Next(seed); if ((r & 3) == 0) continue; }
      if (p == 34) { r = RNG_Next(seed); if ((r & 1) == 0) continue; }
      if (p == 35) { r = RNG_Next(seed); if ((r & 3) != 0) continue; }
    }                                                    // SuperUniques: no draw
  } else if (u.type == 2) {
    if (u.id == 196 || u.id == 261) { r = RNG_Next(seed); if ((r & 1) != 0) continue; }
    if (u.id == 581)                { r = RNG_Next(seed); if ((r & 3) == 0) continue; }
  }
  c = PresetUnitCopy(u, ox, oy);  c.next = inst.units;  inst.units = c;   // +0x38, prepend
}
```

- [C] `RNG_Next` here is the inlined step `seed = lo·0x6AC690C5 + hi` (64-bit), and `r` is the new low dword. `% 3` is
  unsigned (`mul 0xAAAAAAAB`, `shr 1`). (0x00667721–0x00667748, run:2026-10-13-drlg-preset)
- [C] The copy keeps `mode`, `id`, `type`, `flags` and the path, adding `ox`/`oy` to `x`/`y` and to every path point.
  Since it prepends, the instance list is back in file order for kept units. (fn:sub_00667510_PresetUnitCopy@0x00667510,
  fn:sub_006660B0_PresetPathCopy@0x006660B0, run:2026-10-13-drlg-preset)
- [I] The names come from the tables: MonStats `hcIdx` 204/205 `act2vendor1/2`, 371 `lightningspire`, 372 `firetower`;
  MonPlace rows 33–35 `place_group25/50/75`; Objects `Id` 196/261 "floortrap". `objects.txt` has no row 581 (rows
  0..572), so object 581 is one of the ids above 573 that the server routes to `0x0054F490`.
  (tbl:MonStats.txt:hcIdx, tbl:MonPlace.txt:code; `objects.txt` `Id`, which has no table doc yet)
- [I] The `place_group*` thresholds run against what the names suggest: `place_group25` is kept with probability
  3/4 and `place_group75` with 1/4. This is the code, not a misreading: `0x0066777D` `sub ecx,0x21` →
  `0x00667687` (`test al,3` / `je` drop). The run saw `place_group50` (MonPlace 34) kept 6 and dropped 4 times and
  `place_group75` kept twice, each matching its test; `place_group25` was not reached. (run:2026-10-13-drlg-preset)

```mermaid
flowchart TD
  U[unit u of the DS1 list] --> T{type}
  T -->|1, id < nMonStats| M{id in 204,205,371,372}
  M -->|yes| D3[draw r; keep iff r mod 3 = 0]
  M -->|no| K[keep, no draw]
  T -->|1, SuperUnique| K
  T -->|1, MonPlace p| P{p}
  P -->|33| D4a[draw; keep iff r and 3 != 0]
  P -->|34| D2a[draw; keep iff r and 1 != 0]
  P -->|35| D4b[draw; keep iff r and 3 = 0]
  P -->|other| K
  T -->|2| O{id}
  O -->|196, 261| D2b[draw; keep iff r and 1 = 0]
  O -->|581| D4c[draw; keep iff r and 3 != 0]
  O -->|other| K
  T -->|other| K
```

### Which seed, and when

```c
// fn:sub_00667ED0_PresetRoomsCreate@0x00667ED0 -> fn:sub_00667970_PresetMapScan@0x00667970 (at room creation)
if (rec.Scan == 0 && rec.Pops == 0) return;                       // +0x34, +0x38
DS1_LoadCached(rec.File[inst.idx], &inst.ds1);                     // ECX = inst + 0x0C (0x00667A1C)
PresetUnitDropRolls(&level.seed /* +0x1C4 */, inst);              // 0x00667A35

// fn:sub_00667890_PresetRoomLoadDs1@0x00667890 (room activation, before the room re-seed; drlg/0002)
if (inst.ds1 == 0) { DS1_LoadCached(rec.File[inst.idx], &inst.ds1); PresetUnitDropRolls(&room.seed /* +0x14 */, inst); }
if (inst.pending /* +0x3C */ == 1) {
  inst.pending = 0;
  if (Def in 4..7) { if (level.id == 2 && inst.idx == 3) PresetCentreMonster(inst); }
  else if ((Def in {1, 3, 26, 27, 28, 300}) && (room.flags & 0x40000)) PresetClientObjects(inst);
}
room.flags |= 0x2000000;
```

- [C] So, per instance, the rolls run exactly once (0x006678E2, 0x00667A35, run:2026-10-13-drlg-preset):
  - on the level seed while the rooms are created, when `Scan || Pops`;
  - otherwise on the room seed of whichever room of the instance loads first. That draw happens before the room's
    re-seed, so it changes nothing in that room's later draws, but its outcome fixes the unit list of **every** room
    of the instance. The room seed it draws on is `step(Init(level lo))` from `DRLG_RoomCreate`.
  (0x006678D2, 0x006678E2, 0x00667A1F, 0x00667A35, 0x0066B44A)
- [I] `PresetRoomLoadDs1` is called from `sub_0061B730_RoomActivateB` (`0x0061B752`) and `sub_0061B320_RoomPrepareFiles`
  (`0x0061B343`). `PresetUnitDropRolls` has exactly two call sites, `0x006678E2` and `0x00667A35` (xrefs).
- [I] Centre monster: `x = (inst.x + inst.w / 2)·5`, `y = (inst.y + inst.h / 2)·5` (signed `/ 2`; sizes are
  positive), id 266 when `nMonStats > 266`, else −1. It goes to the instance list after the rolls, with no draw.
  (fn:sub_006664A0_PresetCentreMonster@0x006664A0)
- [C] Client objects: the room flag `0x40000` gates them. Each placement adds object 65 every 8 tiles (40 subtiles)
  down a column, and objects 40, 41, 41, 41, 42 one tile apart in a row for each DS1 row. `Def` 27 makes one
  placement at the instance edge. The other `Def`s make one at every floor-layer-0 cell of style 2, main index 24.
  Every one of these units gets `flags |= 1`. No draw. They are client presentation (ambient river objects), and
  the server skips them. The rows step one DS1 row at a time, three more after a style-4 floor cell of main index 0,
  4, 8, 16, 29 or 39 (switch table `0x0066638C`).
  (fn:sub_006663C0_PresetClientObjects@0x006663C0, fn:sub_006661A0_PresetClientUnitsA@0x006661A0,
  fn:sub_00666220_PresetClientUnitsB@0x00666220, run:2026-10-13-drlg-preset)

### From the instance to the room, and on to the spawners

- [C] The rectangle test is half-open (`sub_0066B980_RectContains`), and path points are not moved to room
  coordinates. (fn:sub_0066B980_RectContains@0x0066B980, run:2026-10-13-drlg-preset)

```c
// fn:sub_00666710_PresetUnitsToRoom@0x00666710 (called from the type-2 grid prepare, 0x0066697D)
for (u in inst.units) if (RectContains(room.rect × 5, u.x, u.y)) {
  u.x -= room.x * 5;  u.y -= room.y * 5;
  unlink u from inst.units;  u.next = room.units;  room.units = u;      // room +0x5C
}
```

- [I] The room-level record a spawner receives is the 0x20-byte preset unit (`re/types/preset.h`): type, id, mode,
  `x`/`y` in subtiles relative to the room, `flags`, and the path. For monsters the id carries the MonPreset range
  (drlg/0001; struct:PresetUnit+0x04):
  - MonStats: the class;
  - SuperUniques: `nMonStats + row`;
  - MonPlace: `nMonStats + nSuperUniques + row`. (struct:PresetUnit+0x04)
- [I] Server boundary: `sub_005559A0_RoomPresetUnits` (monsters/0002 § 7) walks `room +0x5C` in two passes,
  non-monsters then monsters (the second pass is skipped in level 136). It skips a unit with
  `+0x1C` bit 0 and spawns each other unit through `sub_00555910_PresetUnitSpawn` → `sub_005557D0_PresetUnitDispatch` (fn:sub_005557D0_PresetUnitDispatch@0x005557D0):
  ```c
  if (type == 1)       PresetMonSpawn(id, …);           // monsters/spawn, monsters/special
  else if (type == 2 && id > 573)  sub_0054F490(id, …); // objects row
  else if (type == 2 && id == 573) ;                    // nothing
  else                 SUnitCreate(…);                  // objects row (type 4 too)
  ```
  (fn:sub_005557D0_PresetUnitDispatch@0x005557D0, fn:sub_005559A0_RoomPresetUnits@0x005559A0)
- [I] `flags` bit 0 therefore means "the server does not spawn this unit". The DS1 sets it on one referenced unit
  (`wstone01.ds1` `worldstoneeffect`), and `PresetClientObjects` sets it on every unit it adds.
  (struct:PresetUnit+0x1C)

### LvlPrest columns

| Column | Reader | Effect | Tag |
|---|---|---|---|
| `Populate` (`+0x08`) | `sub_00666680_PresetRoomCreate`, `sub_00667ED0_PresetRoomsCreate` (single-room branch) | 0 sets room `+0x28` bit `0x800000` (`0x006666EC`, `0x00667FC7`), for which `sub_0061A1F0_RoomPopLevelId` returns 0: no random population (monsters/0002). Preset units still spawn. Two other writers set the bit (Answer) | C |
| `Logicals` (`+0x0C`) | `sub_00666AC0_PresetRoomTilesBuild` | selects the builder: 0 `sub_0066CCB0_SpawnBoxesSingle` (flags bit 0), 1 `sub_0066D110_LogicRegionsFromDs1` (flags bit 1); client wall cut-away reads seen in the run. The builders' output (tag I) is: 0 one region = the room; 1 regions flooded from the DS1 cells, ids from level counter `+0x1DC`, merged across neighbour rooms of one level, wall entries `+0x10` → box (not reproduced; `drlg/collision`). The server population read is monsters/0002's, inferred | C (selection), I (output) |
| `Outdoors` (`+0x10`) | `sub_00667ED0_PresetRoomsCreate` | ORs `0x80000` into the flags the scan grid writes into each room's `+0x28`. No reader of that room bit found | I |
| `Animate` (`+0x14`) | `sub_00666AC0_PresetRoomTilesBuild` | counts animated tiles (DT1 flag `0x100`) per grid, sets room bit `0x8000000`, builds frame lists (`sub_0066D700_AnimTilesBuildAll`) | I |
| `+0x024` | `0x00666D80` | the frame period passed to `AnimTilesBuild`; 0 means 80. Only with `Animate`. No `.txt` column; 0 in every record | I |
| `KillEdge` (`+0x18`), `FillBlanks` (`+0x1C`) | `sub_00666AC0_PresetRoomTilesBuild` | as drlg/0002 § Room tile build | I |
| `AutoMap` (`+0x30`) | `sub_00668100_PresetLevelBuild` | gates the act callbacks (below). No server effect | I |
| `Scan` (`+0x34`) | `sub_00667970_PresetMapScan` | with `Pops`, gates the scan and the level-seed rolls; marks wall cells of orientation 10/11 (style < 8, main 0 or 4 or bit 31) in the level grid, collects style 30–33 cells into level `+0x2C` (warp markers; drlg/warps), marks cells of objects with record `+0x167` bit `0x40` | I |
| `Pops` (`+0x38`) | `sub_00667970_PresetMapScan` | capacity of the pop tables (`+0x44/+0x48/+0x4C/+0x50`, one entry per distinct style 8–29 of orientation 10/11); the client hides roofs from them (`sub_006671E0_PresetPopsUpdate`) | C |
| `PopPad` (`+0x3C`) | `sub_006671E0_PresetPopsUpdate` (`0x00667255`, `0x00667261`), client | added to the trigger rectangle's width and height in subtiles: `(x·5, y·5, w·5 + PopPad, h·5 + PopPad)`, half-open | C |

```c
// fn:sub_00668100_PresetLevelBuild@0x00668100, after PresetRoomsCreate
if (level.id in {40, 103, 109}) { if (act[+0x488] && rec.AutoMap) act[+0x488](level.id, inst.idx, cx, cy); }
else if (act[+0x454] && rec.AutoMap) { LevelEnsure+LevelInit each linked level; for each room: RoomActivateB, act[+0x454](room) }
```

- [I] On the server both callbacks are null. `DUNGEON_ActCreate` is called from `0x0053ACA0` with 0 in both callback
  arguments (`0x00619505`–`0x00619524` → `DRLG_ActCreate` `0x00642E45`/`0x00642E59`). The other writer of a
  `+0x488` (`0x00538783`) is reached from `D2S_ReadHeader` on a different struct. So `AutoMap` has no server
  effect, and its linked-level `LevelInit`s run only in the client's own act. (fn:DRLG_ActCreate@0x00642DA0,
  fn:D2S_ReadHeader@0x0056A090)
- [I] On the client (`0x0044E13D`), `+0x454` is `0x00459150` (per room, into the current automap layer
  `0x007A5164`) and `+0x488` is `0x004591A0`. The latter writes a fixed grid of entries for levels 40/103/109
  (5×4, 2×2, 3×2), with level 40 indexed by the file index. Both draw nothing. The automap meaning is `[I]` from
  the column name and the layer global, not read further (presentation, ADR-0002).
```c
// fn:sub_006671E0_PresetPopsUpdate@0x006671E0 (client, per frame; ESI = the player's room, EDI/arg = player x/y subtiles)
found = 0;
if (room.type == 2) for (k = 0; k < inst.nPops; k++) {                 // inst = room +0x20 -> +8
  r = inst.popRect[k];  pad = inst.pRecord.PopPad;                      // +0x50 (tiles), record +0x3C
  if (RectContains({r.x*5, r.y*5, r.w*5 + pad, r.h*5 + pad}, x, y)) { found = inst.popIndex[k]; break; }
}
// then every pop of the neighbour preset rooms: hidden when its (instance, index) is not found, shown when it is
```

- [C] The trigger test above reproduces the pop index at all 6443 logged player positions; at 70 of them a `PopPad`
  of 0 would give another index. (0x00667224–0x00667292, run:2026-10-13-drlg-preset)
- [I] None of these readers draws: `0x0066CCB0`, `0x0066D110`, `0x0066D290`, `0x0066D700`, `AnimTilesBuild` and
  `0x006671E0` have no LCG constant (findscalar `0x6AC690C5`), and drlg/0003's level-seed check covers the build.

### Shared DS1 buffers (`0x84`)

- [I] `PresetRoomsCreate(flags, single)` has three callers (fn:sub_00667ED0_PresetRoomsCreate@0x00667ED0):
  - `PresetLevelBuild` (`0x0066814D`): `(0, 0)`, split into 8×8 rooms;
  - the maze builder (`0x00673AAF`): `single = (w ≤ 12 && h ≤ 12)` on the maze room's size;
  - the outdoor builder (`0x006751EB`): `(flags, 0)`, split.

  Every file named by two records is used by records of the same kind and size (archivist survey: `tri_town4`
  preset/preset 43×48, `mag*` maze 10×10 single, `lake1` outdoor 8×8). So no shipped DS1 is cut two ways, and each
  cell's `0x84` border state is the same in every view. (0x0066814D, 0x00673AAF, 0x006751EB)

### Level 27's index

```c
// fn:sub_006772C0_LevelLinkBuild@0x006772C0, per linked level L (act seed copy in ESI)
if (L.id == 6) {
  ps27 = LevelEnsure(act, 27)->presetData;                // +0x14
  if      (link[k] == 1) { r = RNG_Next(actSeed); ps27.idx = 2 - (r & 1); }
  else if (link[k] == 3) { r = RNG_Next(actSeed); ps27.idx = (~r) & 1; }
}                                                          // write at 0x006774F9
```

- [I] Level 6 is Act 1 Wilderness 5 and level 27 is Courtyard 1 (tbl:Levels.txt:Name). `link[k]` is the link value the
  `LinkPick` callbacks chose for level 6. (fn:sub_006772C0_LevelLinkBuild@0x006772C0, 0x006774F9)

## Data touched

- tbl:LvlPrest.txt:Populate (`+0x08`), tbl:LvlPrest.txt:Logicals (`+0x0C`), tbl:LvlPrest.txt:Outdoors (`+0x10`),
  tbl:LvlPrest.txt:Animate (`+0x14`), tbl:LvlPrest.txt:KillEdge (`+0x18`), tbl:LvlPrest.txt:FillBlanks (`+0x1C`),
  tbl:LvlPrest.txt:AutoMap (`+0x30`), tbl:LvlPrest.txt:Scan (`+0x34`), tbl:LvlPrest.txt:Pops (`+0x38`),
  tbl:LvlPrest.txt:Files (`+0x40`), tbl:LvlPrest.txt:SizeX (`+0x28`); the unnamed `+0x024`.
- tbl:MonStats.txt:hcIdx, tbl:MonPlace.txt:code, `objects.txt` `Id` (names only; no table doc yet).
- struct:PresetInstance+0x0C, struct:PresetInstance+0x38, struct:PresetInstance+0x3C, struct:PresetUnit+0x04,
  struct:PresetUnit+0x1C, struct:PresetUnit+0x10.

## Dead ends

- `0x004E6C50` was listed as "the act-3 rewrite ids". It is the MonStats range check. The ids are immediates at
  `0x00665CC8`/`0x00665CDD`.
- The "third caller" `0x0061B210+0x133` is `0x0061B343`, inside `sub_0061B320_RoomPrepareFiles`.
- `PopPad`: no reader found by any of these four searches:
  - the decompiles of all twelve callers of `sub_0061F0B0_LvlPrestByDef`/`sub_0061F0E0_LvlPrestByLevel`;
  - every `[x+8] → [y+8] → [+0x24|+0x38|+0x3C]` load chain in the disassembly (one hit, `0x00666D80`, `+0x24`);
  - every `room+0x20 → +8 → +8 → field` chain;
  - every use of `g_pLvlPrest` (the loader and the two lookups only).

  The reader exists (`sub_006671E0_PresetPopsUpdate`, Phase 2). Its chain starts from the instance kept in a local
  (`[ebp-8]`, then `ESI` → `+8` record → `+0x3C`), a shape none of the four searches covered.
- `+0x488` written at `0x00538783` looked like the server's town callback. That is a setter called from `D2S_ReadHeader`
  (`0x0056A1CF`) on another struct.

## Open questions

- Path `action` values: the path is copied with the unit and handed to the spawners, but no reader of the points was
  read. Monster AI is out of scope (ADR-0002). An object-owned path (`nihlathak` as object 461) goes to
  `SUnitCreate`, whose use of it is not read. Owner `monsters/spawn`/`objects`.
- Who reads room flag `0x80000` (`Outdoors`)? A search for `test [reg+0x28], 0x80000` found nothing. A getter may
  hide it.
- [L] Path `action` is a hardcoded animation and/or sound played at the point, and an NPC walks the points in random
  order without returning to its start (src:siramy-ds1edit § Path Editing, § F10). Not read. Owner
  `monsters/spawn`/`objects`.
- [L] `Outdoors` changes lighting (src:d2dfg-blizzard), and `Animate` 0 shows a random static frame
  (src:pk-lvlprest-guide). Both are client-side and not read.
- Does the server's population read the logic boxes as monsters/0002 says? The run placed its box watches when the
  player entered a box, after the room had been populated, so the read at `0x0054ED03` was never in a watch window.
  A watch placed at `LGB` time on a populated `Logicals` 1 room would show it.
- `sub_004DD060_WallCutawayTest`'s globals `0x007C8A08`/`0x007C8A0C`/`0x007C8A10`: who writes them? `0x0066CEA4`
  (`sub_0066CE30_SpawnBoxIdAtTile`) runs on the client about every frame (10 530 reads), a likely source of the
  player's region id. Presentation (ADR-0002), owner of a future client spec.
- `0x0066E37E` (`sub_0066E360_HiddenWarpTilesAdd`) sets `0x800000` on a room with hidden warp tiles. Not attributed
  in the run; 29 `Populate` 1 rooms with pop level 0 come from logs without the FLG tag. Owner `drlg/warps`.
- Who detaches a preset monster's path between two prepares of a room (19 units, client and server copies)? Not
  attributed. Owner `monsters/spawn`.
- Units other code prepends to a room list after `PresetUnitsToRoom` (objects 14–16, 23–25, 27, 64, 449, type-5
  units): only `sub_0066D9E0_Orient89Unit` (`0x0066DAEE`) was attributed. A re-activated room gets such a unit again,
  so the server list can hold duplicates. Owners `objects`, `drlg/warps`.
- `0x0054F490` (objects above 573, including 581) and the objects record `+0x167` bit `0x40` that the scan marks
  (`FUN_0066AD80` uses the same test to find a room position) belong to the `objects` row.
- `Def` 108 / level 17: `0x00666990` records up to six orientation-10, main 23–27 cells (+2 subtiles) in the preset room
  data `+0xF0`. Its consumer is not read.
- Not reached in run:2026-10-13-drlg-preset (they stay `[I]`): the draws of MonStats 371/372, MonPlace 33 and
  objects 196/261, the dropped outcome of MonPlace 35, the act rewrites 366 and 537..539, the Blood Moor centre
  monster, the `v = 1` level-27 branch, the walk filters of levels 133–136, and a maze preset room in Acts III and V.

## Phase 2 logging points

Done (run:2026-10-13-drlg-preset): tags PSL, PRR/PRRX, PLD/PLDX, PTR0/PTR1, RPU, PSP, RPL, L27/L27X, LIP, FLG, PUC in
`tools/gdb/drlg-preset.py`, and the watch and pop tags in `tools/gdb/drlg-preset-wp.py`. The checker is
`python3 -I tools/drlg.py gen` (`--preset-oracle` restores the plan 0008 oracle).
