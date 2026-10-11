# 0002 — Seed tree: where seeds come from and how children derive from parents

> **Subsystem:** rng/seeds (research map, ADR-0002); Plan 0001 phase 5 asks for the first pass
> **Question:** Where is each seed initialised (game, act, level, room, unit, item), and how is a child seed derived from its parent?
> **Date:** 2026-10-11   **Plan:** 0001, 0003   **Status:** answered for plan 0003 (game → act → level → DRLG room `[C]` by run:2026-10-11-seed-tree; active room, server and client unit seeds `[C]` by run:2026-10-11-seed-tree-p1; what happens *inside* items, monster spawning and the room-type code goes to their own findings)

Struct names here are ours, from the source paths each allocation passes to the allocator
(`.\DRLG\Drlg.cpp`, `.\DUNGEON\Dungeon.cpp`, `.\DRLG\DrlgRoom.cpp`, `.\UNIT\CUnit.cpp`). Offsets are byte offsets.
No struct in `re/types/` exists yet.

## Answer (summary)

- [C] **One derivation rule:** to make a child seed, the parent's seed is stepped once, and the new
  `low` becomes the child's initial value: `RNG_SeedInit(child, step(parent).low)`, so `child.high = 666`. Each
  child creation consumes exactly one draw from its parent. It holds at runtime for the DRLG room, the active room,
  server units and client units. There are two exceptions. The level adds instead of drawing (below). The active
  room's parent (the DRLG room seed) is **re-initialised** just before the draw ([Active room](#active-room)).
  (fn:DRLG_RoomCreate@0x0066B3E0, fn:DRLG_RoomActivate@0x006422A0, fn:sub_00552DF0_UnitSeedInit@0x00552DF0,
  fn:sub_00465FD0_UnitInit@0x00465FD0, run:2026-10-11-seed-tree, run:2026-10-11-seed-tree-p1)
- [C] **Game root**, `GAME_InitSeeds` (game object in EDI). With no override (`g_SeedOverride == −1`, its initial
  value): game seed `+0xD0` = `init(RNG_EntropySeed(salt = QueryPerformanceCounter low dword))`, then one step. Then
  **map seed** `+0x7C` = `RNG_EntropySeed(salt = game seed low after that step)`, and flag `+0x84 = 0`. With an
  override: `+0x7C` = override, game seed = `init(override)` with no extra step, and `+0x84 = 1`. The override path
  is observed in every run: `-seed N` gives `+0x84 = 1`, `+0x7C = N`, `+0xD0 = {N, 666}`. The clock path is observed
  in a `-seed 0` run: both `RNG_EntropySeed` calls, the second one's salt (= game seed low after the step), the map seed
  and `+0x84 = 0` all match the model. (fn:GAME_InitSeeds@0x0052C280, data:g_SeedOverride@0x00731004,
  run:2026-10-11-seed-tree, run:2026-10-11-seed-tree-p1)
- [C] **`-seed` option, and its width.** The option table `g_CmdLineOptions` (`0x00705040`, 58 entries of 0x5C bytes:
  section `char[27]`, key `char[27]`, switch `char[27]`, type u8 at `+0x51`, config offset u32 at `+0x54`, default u32
  at `+0x58`) has the entry {`DEBUG`, `SEED`, `seed`, type 1, offset `0x21A`, default 0} at `0x00705EFC`. Type 1 is an
  integer: the command-line parser stores `atol(text)` (a signed 32-bit `long`) at `config+offset`, and the
  `D2.ini` reader stores `GetPrivateProfileIntA(section, key, default)` there. The next entry's field starts at `0x21E`, so
  the slot is 4 bytes, and `sub_0044D860_ApplySeedOption` reads it as one dword (`mov eax, [ecx+0x21A]`). It passes the
  value to `GAME_SetSeedOverride` **only if it is non-zero**, so seed 0 cannot be forced: a `-seed 0` run takes the
  clock path. Corroboration: writer and reader agree on 32 bits, `-seed 34844169` (more than 16 bits) arrives intact as
  `+0x7C = 0x0213AE09`, and `-seed 0` gives `+0x84 = 0`. (fn:sub_004058A0_ConfigParseCmdLine@0x004058A0,
  fn:sub_00405450_ConfigLoadIni@0x00405450, fn:sub_0044D860_ApplySeedOption@0x0044D860, 0x0044D860,
  fn:GAME_SetSeedOverride@0x0052C320, run:2026-10-11-seed-tree, run:2026-10-11-seed-tree-p1)
- [I] Since `GAME_InitSeeds` tests `g_SeedOverride == −1`, a seed whose 32-bit value is `0xFFFFFFFF` (`-seed -1`) also
  means "no override". `atol` overflow behaviour (text above 2³¹−1) depends on the CRT and was not checked. Valid,
  reproducible seeds are 1…2³¹−1, plus negative values, which are stored as their two's-complement u32.
  (fn:GAME_InitSeeds@0x0052C280)
- [C] `RNG_EntropySeed(salt)` = `lcg(lcg(lcg(GetTickCount() + time(NULL) + salt))) & 0x7FFFFFFF` with
  `lcg(x) = x * 0x19660D + 0x3C6EF35F`. **Every operation is 32-bit and wraps mod 2³²** (`add eax`, `imul eax, eax,
  imm`, `add eax, imm`; `time` is the 32-bit `_time32`). The result has 31 bits. Without `-seed`, the seeds are
  clock-dependent and cannot be reproduced. Bit-exact against both calls in the `-seed 0` run (logged tick, time, salt
  → result). (0x00650DF6–0x00650E1C, fn:RNG_EntropySeed@0x00650DE0, run:2026-10-11-seed-tree-p1)
- [C] **Act:** `DRLG_ActCreate` gets the **map seed** for every act (`sub_0053AC70_ActCreate` → `DUNGEON_ActCreate`
  → `DRLG_ActCreate`, seed argument = `ESI+0x7C`; that `ESI` is the game object is inferred from the shared
  `+0x7C` offset). It sets act seed `+0x000` = `init(mapSeed)`, keeps `mapSeed` at
  `+0x458`, steps once, and stores that new `low` at `+0x470`. So all acts of a game share the same `+0x470` value.
  The act index (`DL`, stored at `+0x480`) is **0-based**: Act I = 0 … Act V = 4. Observed for all five acts.
  The `Dungeon.cpp` act is stored in the DRLG act at `+0x46C` (`0x00642DFC`); the active rooms hang off it.
  (fn:DRLG_ActCreate@0x00642DA0, fn:DUNGEON_ActCreate@0x006194A0, fn:sub_0053AC70_ActCreate@0x0053AC70, run:2026-10-11-seed-tree)
- [C] **Each act exists twice, a server copy and a client copy, with the same seed.** `DUNGEON_ActCreate` has two
  callers. `sub_0053AC70_ActCreate` (server) passes `game+0x7C` and stack arg 3 = 0. `sub_0044E100_ClientActLoad`
  passes arg 3 = 1 and stores the result in the client's current-act global `0x007A0634`. Its seed is the `EDX` of
  its caller `0x0045C8E0`, which takes it from a 12-byte message: act `u8 +1`, **map seed `u32 +2`**, `u16 +6` (also
  passed on), `u32 +8`. `0x0045C8E0` is entry 3 of the client message-handler table at `0x007114D0` ({handler, size,
  0} records, entry 3 has size 12). So the client builds its act from the map seed the server sends. A
  `DUNGEON_ActCreate` breakpoint logs both calls on game entry: return address `0x0053ACA5` with arg 3 = 0, then
  `0x0044E142` with arg 3 = 1, both with seed N. That is why every act appeared twice in run:2026-10-11-seed-tree.
  The DRLG seed tree of the two copies is identical up to room activation. Gameplay (drops, spawns) is decided on
  the server copy. (fn:sub_0044E100_ClientActLoad@0x0044E100, fn:sub_0045C8E0_PktLoadAct@0x0045C8E0,
  data:g_ClientPktHandlers@0x007114D0, run:2026-10-11-seed-tree-p1)
- [C] **Act-specific draws right after that step**, from the act seed. If the act byte (`DL`, stored at `+0x480`) is 1:
  loop { `a = range7`; `b = range7` } until `a ≠ b`, then `+0x094 = a + 66`, `+0x484 = b + 66`. Each `range7` is a step
  plus an unguarded `low % 7`. Levels 66–72 are exactly `Act 2 - Tomb Tal 1..7` in `levels.txt`, so this picks two
  different Tal Rasha tombs. If the byte is 2: one step, then `+0x474 = low & 1`. Seed 12345 gives tombs 72/71
  and `+0x474 = 0`, as predicted. (fn:DRLG_ActCreate@0x00642DA0, tbl:Levels.txt:Id, run:2026-10-11-seed-tree)
- [I] **Later consumers of the act seed, inside `DRLG_ActCreate`** (after the act-specific draws, through
  `sub_00678AD0_ActLinkInit` → per-act code → `sub_006772C0_LevelLinkBuild`). `0x006772C0` copies the act seed
  into a local link-builder struct and its link callbacks (`sub_…_LinkPick`, 9 functions) step **that copy**.
  The copy is discarded, so these draws don't advance the act seed. Two places do step the act seed itself:
  (a) in `0x006772C0`, when the link loop reaches level 6 and its link value is 1 or 3, one step sets a bit in
  level 27's data (`2 − (low & 1)` for 1, `~low & 1` for 3; `0x00677493`–`0x006774F9`); (b) the Act III code
  (`0x006789B0` → `0x00677880` / `0x00678910` / `0x006775C0`, not read yet). Observed counts of act-seed steps between
  `0x00642F1A` and the function exit: Act I seed 12345 → 0, seed 777 → 1; Act III seed 12345 → 119; Acts II, IV
  and V → 0 `[C]` for those seeds (run:2026-10-11-seed-tree). This matters only to later consumers of the act seed,
  not to level seeds, which come from `+0x470`. (fn:sub_006772C0_LevelLinkBuild@0x006772C0, fn:sub_00678AD0_ActLinkInit@0x00678AD0)
- [C] **Level:** `DRLG_LevelCreate(act /*ECX*/, levelId /*EDX*/)` sets level seed `+0x1C4` = `init(act[+0x470] + levelId)`.
  This is **not a draw**. It is a sum, so a level's seed depends only on the map seed and the level ID, not on
  creation order. The sum is a 32-bit `add` (`0x00642B50`–`0x00642B56`) and **wraps mod 2³²**: with `+0x470 =
  0xFFFFFF87` (seed 34844169), level 134 gets `0x0000000D`. 197 level creations over 8 runs match.
  Then it dispatches on a type read from the level's definition record (`+0x30` = `Levels.txt:DrlgType`):
  1 → `0x00673B10` (maze: looks the level up in `lvlmaze`, the 28-byte table at `0x0096CA08`), 2 → `0x00667430`
  (`.\DRLG\Preset.cpp`), 3 → `0x00675320` (`.\DRLG\Outdoors.cpp`); the generator names are `[I]` from those
  anchors. (fn:DRLG_LevelCreate@0x00642AE0, 0x00673B19, run:2026-10-11-seed-tree)
- [I] **On-demand level creation.** Besides `DRLG_ActCreate`, six functions create levels. Each one first walks the
  act's level list (head `act+0x47C`, next `level+0x1AC`, id `level+0x1D0`) and calls `DRLG_LevelCreate` only if the id
  is absent ("get or create"). Because the level seed is a sum, it doesn't depend on which caller runs first:
  | Caller | Role |
  |---|---|
  | `0x00642BB0` `sub_00642BB0_LevelEnsure` | `(act, levelId)`: get or create, nothing else |
  | `0x00642BE0` `sub_00642BE0_LevelRoomCount` | get or create, return the number of its DRLG rooms (list `+0x10`, next `+0x24`) without flag `0x800000` in `+0x28` |
  | `0x00642C30` `sub_00642C30_RoomFromCoords` | find the DRLG room containing a position: the given room or its neighbours (array `+0x08`, count `+0x2C`), else the level at that position (`0x006427A0`), get or create it, build its rooms if it has none (`0x006424A0`), then search them (`0x00642630`) |
  | `0x00642D10` `sub_00642D10_LevelSetPosition` | set a level's size `+0x24/+0x28` from its definition (indexed by act `+0x450`), and its origin `+0x1C/+0x20` = definition offset + origin of the level it is placed relative to (definition `+0x2C`), which is got or created |
  | `0x00642F70` `sub_00642F70_LevelAddRef` | add `EDX` to a level's `+0x0C` counter (clamped at 0 from below), set `+0x1D4 = 10`, and do the same for up to 8 linked levels (`0x0066C040`), getting or creating each |
  | `0x00643060` `sub_00643060_LevelUnloadCheck` | for the 8 linked levels (got or created), check the rooms on the shared border and free their `+0x08` data; returns 0 if any is still in use |
  (fn:sub_00642BB0_LevelEnsure@0x00642BB0, fn:sub_00642BE0_LevelRoomCount@0x00642BE0,
  fn:sub_00642C30_RoomFromCoords@0x00642C30, fn:sub_00642D10_LevelSetPosition@0x00642D10,
  fn:sub_00642F70_LevelAddRef@0x00642F70, fn:sub_00643060_LevelUnloadCheck@0x00643060)
- [C] **DRLG room:** `DRLG_RoomCreate(level /*ECX*/, type /*EDX*/)` steps the level seed, sets room seed `+0x14` =
  `init(low)`, then **steps the room seed once more** and stores that `low` at `+0x04`. 3102 room creations over 8
  runs match. The type dispatch that follows (1 → `0x0067D6D0`, 2 → `0x00666630`) only allocates and zeroes the
  type's record (`.\DRLG\OutRoom.cpp` 0x70 bytes, `.\DRLG\Preset.cpp` 0xF8 bytes) and stores it at room `+0x20`.
  Neither draws `[I]`. (fn:DRLG_RoomCreate@0x0066B3E0, fn:sub_0067D6D0_OutRoomAlloc@0x0067D6D0,
  fn:sub_00666630_PresetRoomAlloc@0x00666630, run:2026-10-11-seed-tree)
### Active room

- [C] **Activation sequence.** Both activation paths (`sub_0061B190_RoomActivateA`, `sub_0061B730_RoomActivateB`;
  the second does the following only while room `+0x28` bit `0x100000` is clear) run, for DRLG room `R` with
  act `A = R[+0x58][+0x1B4]` (room → level → act):
  1. `sub_0066EE40_DrlgRoomReseed`: **`R.seed (+0x14) = init(R[+0x04])`**. The seed restarts from the value its
     first draw stored at creation, so draws made on the room seed during level generation don't carry over. Then
     the room-type code runs: type `R[+0x48]` 1 → `0x0067D2D0`, 2 → `0x006667D0`.
  2. `sub_0066EE70_DrlgRoomTypeInit`: 1 → `0x0067D710`, 2 → `0x00666AC0`; sets `R[+0x28] |= 0x100000`.
  3. `DRLG_RoomActivate(A /*ECX*/, R /*EDX*/)`.

  The room-type code in steps 1–2 **steps `R.seed` k times**, and k is data-dependent: 50 to 376 in the runs, with
  no k = 0 among 157 activations. Those draws belong to the DRLG room-content work and are not decoded here.
  (fn:sub_0066EE40_DrlgRoomReseed@0x0066EE40, fn:sub_0066EE70_DrlgRoomTypeInit@0x0066EE70,
  fn:sub_0061B190_RoomActivateA@0x0061B190, fn:sub_0061B730_RoomActivateB@0x0061B730, run:2026-10-11-seed-tree-p1)
- [C] **`DRLG_RoomActivate`** (review fix 2). It first converts the room's two corner points `+0x34..+0x40` with
  `0x00643560` into a local rectangle. Then, **only if** `T = R[+0x54]` has `T[+0x18] ≠ 0 || T[+0x20] ≠ 0`, it:
  - computes `flags` = 4 if `R[+0x28] & 0x40000`, else 1 if `R[+0x60] & 1`, else 0;
  - steps `R.seed` once (inlined, `0x0064233A`–`0x0064235A`);
  - calls `DUNGEON_RoomCreate(A[+0x46C] /*ECX: Dungeon act*/, R /*EDX*/, &rect, T + 0x14, R.seed.low, flags)`
    and stores the result at `R[+0x30]`.

  Otherwise it returns with **no draw and no active room**. `DUNGEON_RoomCreate` allocates the 0x80-byte active room,
  sets **its seed `+0x6C` = `init(low)`**, stores `flags` at `+0x34`, `T + 0x14` at `+0x08` and `R` at `+0x10`, links
  it at the head of the Dungeon act's list (`act+0x10`, next `+0x7C`) and sets the act's "new rooms" flag `+0x54 = 1`.
  So: `active.seed = init(step^(k+1)(init(R[+0x04])).low)`. All 157 activations in three runs match, with k
  counted per room by the checker. (fn:DRLG_RoomActivate@0x006422A0, fn:DUNGEON_RoomCreate@0x00619890,
  run:2026-10-11-seed-tree-p1)
- [I] **What `R[+0x54]` is:** a 0x2C-byte `.\DRLG\RoomTile.cpp` record, allocated and zeroed on first use by
  `0x0066EEA0`, which the room-type code calls during steps 1–2 (`0x0067D2D0`, `0x0067D710`, `0x00666AC0`). The two
  dwords tested are `+0x04` and `+0x0C` of its sub-structure at `+0x14`, which becomes the active room's `+0x08`. What they
  count is not read. (fn:sub_0066EEA0_RoomTileAlloc@0x0066EEA0)
- [I] **The `flags` value** is the active room's `+0x34`. Bit 0 is the "already populated" bit:
  `sub_0052D160_NewRoomsUpdate` runs the population pass (`sub_0054EC90_RoomPopulate` and three others) only for rooms
  whose bit 0 is clear, then sets it. So a DRLG room with `+0x60` bit 0 set is created as if already populated.
  In the runs, every room of the server act got `flags` 0 and every room of the client act got `flags` 4 (`R[+0x28]` bit
  `0x40000`) `[C]` (run:2026-10-11-seed-tree-p1). (0x0052D1C9, fn:sub_0052D160_NewRoomsUpdate@0x0052D160)
- [C] **Server and client copies can get different active-room seeds.** Activating the same DRLG room (same `+0x04`)
  in the server act and the client act gives the same k for some rooms and a different k for others. Of the 9
  rooms activated in both acts, seed 12345 gives 6 different seeds and seed 777 gives 8. Only the server copy matters for gameplay. (run:2026-10-11-seed-tree-p1)
- [I] **Consumers of the active-room seed:** server side, `sub_0054EC90_RoomPopulate` steps it once through
  `sub_005BDFF0_ARoomSeedStep` on one branch of its per-tile spawn loop (the loop's other rolls draw from the game
  seed `+0xD0`). Client side, the client unit constructors draw from it (below). The run entered only the Act I town, where
  `0x005BDFF0` never fired. (0x0054EEE6, fn:sub_005BDFF0_ARoomSeedStep@0x005BDFF0)

### Units

- [C] **Server units draw from the game seed `+0xD0`, not from a room.** The server unit constructor
  `sub_00555230_SUnitCreate` (`.\UNIT\SUnit.cpp` module; `ECX` = unit type, `EDX` = class id, stack arg 3 = game) calls
  `sub_00552DF0_UnitSeedInit(unit, &game->seed /*+0xD0*/)` **for every type except 0 (players)**:
  `unit.seed (+0x20) = init_one()`, then `step(parent)`, `unit[+0x28] = low`, `unit.seed = init(low)`. With a null
  parent it uses `RNG_EntropySeed(2 × counter)` with the counter at `0x008846E8` instead, a non-reproducible path that no run hit.
  Items (type 4) then call `0x00627C90` (allocate the 0x74-byte item data at `unit+0x14`, no draw) and
  `sub_00552E90_ItemSeedInit`, which draws **once more** from the game seed and seeds the item data from it (the
  item's own story is plan 0004's). The other five callers of `0x00552DF0` (`0x0053254E`, `0x005338D8`,
  `0x00569F53`, `0x0056A95E`, `0x0057F7E5`, player creation and re-seeding paths) also pass `game+0xD0`.
  Runtime: 114 server unit seeds over three runs. The parent pointer is always `game+0xD0` (the game pointer comes from
  `GAME_InitSeeds`), and `unit.seed = init(step(parent).low)` and `+0x28` match. The parent's position in the game
  seed's sequence from `init(N)` is 5 for the player, then 6, 8, 10… for the starting items (two draws each), then
  NPCs and objects. (fn:sub_00555230_SUnitCreate@0x00555230, fn:sub_00552DF0_UnitSeedInit@0x00552DF0,
  0x00555306, fn:sub_00552E90_ItemSeedInit@0x00552E90, run:2026-10-11-seed-tree-p1)
- [C] **Client units draw from the client active room.** `sub_00465FD0_UnitInit` and `sub_00466200_UnitInitB` are the
  **client** constructors (`.\UNIT\CUnit.cpp`; they store the client act `0x007A0634` at `unit+0x1C`). They set
  `unit.seed (+0x20) = init_one()`. If a room was found, they step the room's seed `+0x6C`, set `unit[+0x28] = low` and
  `unit.seed = init(low)`. 739 client unit seeds over three runs match, all drawn from rooms of the client act.
  (fn:sub_00465FD0_UnitInit@0x00465FD0, fn:sub_00466200_UnitInitB@0x00466200, run:2026-10-11-seed-tree-p1)
- [I] **The predicate is a position test.** The room lookup runs only when the two integer arguments are not both
  zero (`0x00465FD0`: `EBX` and stack arg 3; `0x00466200`: stack args 1 and 2). They are **(x, y)**:
  `0x00465420` takes them as `(ECX, EDX)`, returns no room for (0, 0) itself, looks the room up by
  coordinates in the client act (`0x00619DA0(0x007A0634, x, y)`), and on failure formats "Unable to find room for
  unit... nX:%d nY:%d". The same pair goes to the position setter `0x00460BF0`. So a client unit created at (0, 0)
  gets **no room draw** and keeps `{1, 666}`. (0x00466027, fn:sub_00465420_ClientRoomAt@0x00465420)
- [I] **Type 4 in the client constructor doesn't draw before the room draw:** `0x00627C90` allocates and zeroes the
  0x74-byte item data (`.\ITEMS\Items.cpp`), and `0x00627DC0` sets its seed at `+0x04` to `init_one()`. Neither steps
  anything. (fn:sub_00627C90_ItemDataAlloc@0x00627C90, fn:sub_00627DC0_ItemDataSeedInitOne@0x00627DC0)
- [I] **Type 1 (monsters) is not built through `0x00465FD0`:** its `case 1` reaches the non-returning error path
  (`0x00408090(0x202)` → `0x00681E09`). Client monsters go through `0x00466360` (`0x00466730` sends type 1 there).
  Server monsters use `sub_00555230_SUnitCreate`, so **their seed is a game-seed draw**, not a room draw: type 1 units
  appear among the logged server seeds `[C]` (run:2026-10-11-seed-tree-p1). (0x004660A4)

## Leads used

- Hypothesis from our own lead notes (`.claude/skills/reverser/references/d2-landmarks.md`, no external source,
  nothing to register): "seeds per game, unit, item, room/DRLG; level seed derived from the game seed, so the same
  game seed gives the same maps". **Held, with a refinement:** the maps derive from the separate *map seed*
  (`game+0x7C`), not from the game seed at `+0xD0`, and level seeds are sums rather than draws.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x0052C280` | `GAME_InitSeeds` | game seed `+0xD0`, map seed `+0x7C`, override flag `+0x84` | C |
| `0x0052C320` | `GAME_SetSeedOverride` | `g_SeedOverride = arg` (stack arg) | I |
| `0x00731004` | `g_SeedOverride` | initial value `0xFFFFFFFF` = no override | I |
| `0x0044D860` | `sub_0044D860_ApplySeedOption` | `if (cfg+0x21A) GAME_SetSeedOverride(cfg+0x21A)`, 32-bit read | C |
| `0x00405450` | `sub_00405450_ConfigLoadIni` | fills the config from `D2.ini` per `g_CmdLineOptions` entry (type 0 bool, 1 int, 2 string) | I |
| `0x004058A0` | `sub_004058A0_ConfigParseCmdLine` | fills the config from `-switch value` pairs (type 1 → `atol`) | I |
| `0x00650DE0` | `RNG_EntropySeed` | clock + salt, put through an LCG three times (32-bit wrap), 31-bit result | C |
| `0x0053AC70` | `sub_0053AC70_ActCreate` | creates act `EBX` with seed `game+0x7C`, stores it at `game+0xBC+4*act` | I |
| `0x006194A0` | `DUNGEON_ActCreate` | 0x60-byte act object, calls `DRLG_ActCreate`; seed at `+0x0C`, arg 3 at `+0x50`; room list `+0x10`, new-rooms flag `+0x54` | I |
| `0x0044E100` | `sub_0044E100_ClientActLoad` | client side: creates the client act from the server's map seed, stores it in `0x007A0634` | C |
| `0x0045C8E0` | `sub_0045C8E0_PktLoadAct` | handler 3 of the client message table: `(act u8 +1, seed u32 +2, u16 +6, u32 +8)` → `0x0044E100` | I |
| `0x007114D0` | `g_ClientPktHandlers` | client message-handler table, `{handler, size, 0}` 12-byte records | I |
| `0x00642DA0` | `DRLG_ActCreate` | 0x48C-byte DRLG act, act seed and act-specific draws | C |
| `0x00642AE0` | `DRLG_LevelCreate` | 0x230-byte level, seed `+0x1C4`, generator dispatch | C |
| `0x0066B3E0` | `DRLG_RoomCreate` | 0xEC-byte DRLG room, seed `+0x14` | C |
| `0x00642BB0`, `0x00642BE0`, `0x00642C30`, `0x00642D10`, `0x00642F70`, `0x00643060` | `sub_<addr>_Level…`, `…_RoomFromCoords` | get-or-create level callers (table in the summary) | I |
| `0x006422A0` | `DRLG_RoomActivate` | conditional: steps the DRLG room seed and creates the active room | C |
| `0x00619890` | `DUNGEON_RoomCreate` | 0x80-byte active room, seed `+0x6C`, flags `+0x34` | C |
| `0x0066EE40` | `sub_0066EE40_DrlgRoomReseed` | room seed `+0x14 = init(+0x04)`, then the type-1/2 room code | C |
| `0x0066EE70` | `sub_0066EE70_DrlgRoomTypeInit` | type-1/2 room code, then sets `+0x28` bit `0x100000` | I |
| `0x0066EEA0` | `sub_0066EEA0_RoomTileAlloc` | allocates the 0x2C-byte `RoomTile.cpp` record at room `+0x54` | I |
| `0x0061B190`, `0x0061B730` | `sub_0061B190_RoomActivateA`, `sub_0061B730_RoomActivateB` | reseed → type init → `DRLG_RoomActivate` | I |
| `0x0052D160` | `sub_0052D160_NewRoomsUpdate` | per act: for each active room with `+0x34` bit 0 clear, run the population pass and set the bit | I |
| `0x0054EC90` | `sub_0054EC90_RoomPopulate` | per-room spawn pass (game seed `+0xD0` rolls; one branch steps the room seed) | I |
| `0x005BDFF0` | `sub_005BDFF0_ARoomSeedStep` | steps active room `+0x6C`, returns the global at `0x007415F0` | I |
| `0x006427F0` | `DRLG_ActFromLevelId` | act index from level ID (threshold table at `0x006EB2F0`) | I |
| `0x00555230` | `sub_00555230_SUnitCreate` | server unit constructor; seeds every non-player unit from game `+0xD0` | C |
| `0x00552DF0` | `sub_00552DF0_UnitSeedInit` | `unit+0x20 = init(step(parent).low)`, `+0x28 = low`; null parent → entropy | C |
| `0x00552E90` | `sub_00552E90_ItemSeedInit` | items: one more game-seed draw seeds the item data | I |
| `0x008846E8` | `g_UnitSeedSaltCounter` | salt counter for the null-parent path (`2 × counter`) | I |
| `0x00465FD0` | `sub_00465FD0_UnitInit` | **client** unit constructor: seed `+0x20` from client room `+0x6C` if (x, y) ≠ (0, 0) | C |
| `0x00466200` | `sub_00466200_UnitInitB` | same derivation, second client constructor | C |
| `0x00465420` | `sub_00465420_ClientRoomAt` | client room at (x, y); none for (0, 0) | I |
| `0x00627C90` | `sub_00627C90_ItemDataAlloc` | 0x74-byte item data at `unit+0x14`, no draw | I |
| `0x00627DC0` | `sub_00627DC0_ItemDataSeedInitOne` | item data seed `+0x04 = init_one()`, no draw | I |
| `0x00678AD0` | `sub_00678AD0_ActLinkInit` | per-act switch on `DL` (0–4) into the level-link setup | I |
| `0x006772C0` | `sub_006772C0_LevelLinkBuild` | builds level links from a callback table; draws from a **copy** of the act seed, and from the act seed itself at level 6 | I |
| `0x00676150`, `0x00676280`, `0x00676450`, `0x00676650`, `0x006769A0`, `0x00676AE0`, `0x00676C00`, `0x0067D830`, `0x0067D980` | `sub_<addr>_LinkPick` | link callbacks (only referenced from tables at `0x006F07xx`–`0x006F0Exx`), each steps the link-builder copy `ECX+0x000` and uses `low & 1` | I |
| `0x0067D6D0` | `sub_0067D6D0_OutRoomAlloc` | DRLG room type 1: 0x70-byte `OutRoom.cpp` record at room `+0x20`, no draw | I |
| `0x00666630` | `sub_00666630_PresetRoomAlloc` | DRLG room type 2: 0xF8-byte `Preset.cpp` record at room `+0x20`, no draw | I |

## Walkthrough

```c
// fn:GAME_InitSeeds@0x0052C280 (game in EDI; trimmed, renamed)
if (g_SeedOverride == -1) {
    game->overrideUsed = 0;                                  // +0x84
    QueryPerformanceCounter(&qpc);
    RNG_SeedInitOne(&game->seed);                            // +0xD0
    RNG_SeedInit(&game->seed, RNG_EntropySeed(/*salt*/ qpc.LowPart));
    RNG_Step(&game->seed);                                   // inlined
    game->mapSeed = RNG_EntropySeed(/*salt*/ game->seed.low); // +0x7C
} else {
    game->overrideUsed = 1;
    game->mapSeed = g_SeedOverride;
    RNG_SeedInitOne(&game->seed);
    RNG_SeedInit(&game->seed, g_SeedOverride);
}
```

```c
// fn:DRLG_ActCreate@0x00642DA0 (trimmed; act index in DL, seed arg = map seed)
act = alloc(0x48C, ".\\DRLG\\Drlg.cpp", 0x3A); memset(act, 0, 0x48C);
RNG_SeedInit(&act->seed, mapSeed);            // +0x000
act->mapSeed = mapSeed;                        // +0x458
RNG_Step(&act->seed);  act->levelSeedBase = act->seed.low;   // +0x470
if (actIndex == 1) {                           // Act II
    do { a = step_then_mod(&act->seed, 7); b = step_then_mod(&act->seed, 7); } while (a == b);
    act->taltomb_a = a + 66;  act->taltomb_b = b + 66;       // +0x094, +0x484 (meaning TBD)
} else if (actIndex == 2) {                    // Act III
    RNG_Step(&act->seed);  act->bit474 = act->seed.low & 1;   // +0x474 (meaning TBD)
}
```

```c
// fn:DRLG_LevelCreate@0x00642AE0 (act in ECX, level id in EDX)
lvl = alloc(0x230, ".\\DRLG\\Drlg.cpp", 0x1A8);
lvl->act = act; lvl->id = levelId;                            // +0x1B4, +0x1D0
lvl->drlgType = levelDef(...)->+0x30;                         // +0x000
RNG_SeedInit(&lvl->seed, act->levelSeedBase + levelId);      // +0x1C4  (sum, no draw)
switch (lvl->drlgType) { case 1: 0x00673B10(); case 2: 0x00667430(); case 3: 0x00675320(); }

// fn:DRLG_RoomCreate@0x0066B3E0 (level in ECX)
RNG_Step(&lvl->seed);  RNG_SeedInit(&room->seed, lvl->seed.low);   // room +0x14: 1 draw from level
RNG_Step(&room->seed); room->+0x04 = room->seed.low;               // first draw of the new room

// activation: fn:sub_0061B190_RoomActivateA@0x0061B190 (room in ESI)
RNG_SeedInit(&room->seed, room->firstDraw /*+0x04*/);        // fn:sub_0066EE40_DrlgRoomReseed
roomTypeCode(room);                                           // steps room->seed k times (k data-dependent)
// fn:DRLG_RoomActivate@0x006422A0 (act in ECX, room in EDX)
tiles = room->tiles;                                          // +0x54, RoomTile.cpp record
if (tiles->sub.a /*+0x18*/ || tiles->sub.b /*+0x20*/) {
    flags = (room->flags28 & 0x40000) ? 4 : (room->flags60 & 1) ? 1 : 0;
    RNG_Step(&room->seed);                                    // inlined
    room->active /*+0x30*/ = DUNGEON_RoomCreate(act->dungeonAct /*+0x46C*/, room, &rect,
                                                &tiles->sub /*+0x14*/, room->seed.low, flags);
}                                     // DUNGEON_RoomCreate: RNG_SeedInit(&active->seed /*+0x6C*/, low)

// server: fn:sub_00555230_SUnitCreate@0x00555230 → fn:sub_00552DF0_UnitSeedInit@0x00552DF0
if (type != 0) {
    RNG_SeedInitOne(&unit->seed);                             // +0x20
    RNG_Step(&game->seed /*+0xD0*/); unit->initSeed /*+0x28*/ = game->seed.low;
    RNG_SeedInit(&unit->seed, game->seed.low);
    if (type == 4) { ItemDataAlloc(unit); ItemSeedInit(unit, &game->seed); }   // one more draw
}

// client: fn:sub_00465FD0_UnitInit@0x00465FD0 (x in EBX, y = stack arg 3)
room = (x || y) ? ClientRoomAt(x, y) : NULL;
RNG_SeedInitOne(&unit->seed);                                 // +0x20
if (room) { RNG_Step(&room->seed /*+0x6C*/); unit->initSeed /*+0x28*/ = room->seed.low;
            RNG_SeedInit(&unit->seed, room->seed.low); }
```

## Data touched

- tbl:Levels.txt:Id (levels 66–72 = Tal Rasha tombs, matching the Act II draw `+66`, range 7).
- The level definition record's `+0x30` (generator type) and `+0x34` (copied to level `+0x1C0`). Answered in
  [data/0001](../data/0001-excel-loader.md): the record is `leveldefs.bin` (`g_pLevelDefs`), `+0x30` =
  `tbl:Levels.txt:DrlgType`, `+0x34` = `tbl:Levels.txt:LevelType` `[C]` (descriptor at `0x0061DE00` + all 137 rows).

## Other seed sites seen, not yet followed

- [I] Object regions (`.\OBJECTS\objrgn.cpp`, `0x00546C60`), unit proxies (`.\UNIT\sunitproxy.cpp`, `0x00536070`)
  and `0x005479C0` (`.\MONSTER\MonsterRegion.cpp`) seed a new object from one draw of the seed at `ECX+0xD0`. The
  `+0xD0` seed is the game seed, by `sub_00555230_SUnitCreate`, which passes `game+0xD0`, and by the run, where
  that pointer is `GAME_InitSeeds`' `EDI + 0xD0`. That these three callers' `ECX` is the game object is inferred
  from the offset.
- [I] Items (`.\ITEMS\Items.cpp`, `0x00558D90`): the item unit seed `+0x20` is set from a creation parameter (`+0x48`)
  rather than drawn, and a second item-side seed is set from `+0x4C`. This is the item spec's starting point.
- [I] `.\DATATBLS\LvlTbls.cpp` (`0x0061FCF0`) initialises a global seed (via `PTR_DAT_00744504`) to `init(0)`.
  `.\QUESTS\QUESTS.CPP` (`0x00545D80`) has seed inits too. Neither is followed yet.
- In total, 103 calls to the two initialisers sit in 76 functions. This finding covers about 20 of them.

## Dead ends

- Assumed at first that units draw from the game seed, then (plan 0001) that they draw from their active room's
  seed. Both were half right: the room-seed constructors are the **client** ones (`CUnit.cpp`). The server
  constructor draws from the game seed.

## Open questions

- Meaning of act `+0x094`/`+0x484` (which tomb is the real one) and `+0x474` (Act III bit). These need their readers.
- The Act III act-seed consumers under `0x006789B0` (119 steps for seed 12345) and the level-6 branch's meaning
  (which level-27 field the bit sets). Both belong with `drlg/overview`.
- **The k room-seed draws of the room-type code** (`0x0067D2D0`/`0x006667D0`, `0x0067D710`/`0x00666AC0` and callees)
  between the re-seed and the activation step, and why server and client copies sometimes differ. They decide every
  active-room seed, so `drlg/overview` (room content) has to decode them. Until then the active-room seed is
  reproducible only by running that code.
- What the two `RoomTile.cpp` fields tested by `DRLG_RoomActivate` (`T[+0x18]`, `T[+0x20]`) count, and what DRLG room
  `+0x60` bit 0 (→ flags 1, "populated") and `+0x28` bit `0x40000` (→ flags 4, seen only on client rooms) mean.
- The full population pass `sub_0054EC90_RoomPopulate` (and the other three callees of `0x0052D160`): the monster
  spawn plan's starting point. Its game-seed rolls and its active-room-seed step were read only far enough to name
  the owner of `+0x6C`, and no run has reached it yet (the harness only entered the Act I town).
