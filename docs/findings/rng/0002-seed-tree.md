# 0002 — Seed tree: where seeds come from and how children derive from parents

> **Subsystem:** rng/seeds (research map, ADR-0002); Plan 0001 phase 5 asks for the first pass
> **Question:** Where is each seed initialised (game, act, level, room, unit, item), and how is a child seed derived from its parent?
> **Date:** 2026-10-11   **Plan:** 0001, 0003   **Status:** open (game → act → level → DRLG room `[C]` by run:2026-10-11-seed-tree; active room and units `[I]`; the item and monster branches go to their own findings)

Struct names here are ours, from the source paths each allocation passes to the allocator
(`.\DRLG\Drlg.cpp`, `.\DUNGEON\Dungeon.cpp`, `.\DRLG\DrlgRoom.cpp`, `.\UNIT\CUnit.cpp`). Offsets are byte offsets.
No struct in `re/types/` exists yet.

## Answer (summary)

- [I] **One derivation rule everywhere:** to make a child seed, the parent's seed is stepped once, and the new
  `low` becomes the child's initial value: `RNG_SeedInit(child, step(parent).low)`, so `child.high = 666`. Each
  child creation consumes exactly one draw from its parent. The only exception is the level, which adds instead
  of drawing (below). (fn:DRLG_RoomCreate@0x0066B3E0, fn:DRLG_RoomActivate@0x006422A0, fn:sub_00465FD0_UnitInit@0x00465FD0)
- [C] for the override path, [I] for the clock path: **Game root**, `GAME_InitSeeds` (game object in EDI). With no override (`g_SeedOverride == −1`, its initial
  value): game seed `+0xD0` = `init(RNG_EntropySeed(salt = QueryPerformanceCounter low dword))`, then one step. Then
  **map seed** `+0x7C` = `RNG_EntropySeed(salt = game seed low after that step)`, and flag `+0x84 = 0`. With an
  override: `+0x7C` = override, game seed = `init(override)` with no extra step, and `+0x84 = 1`. The override path
  is observed in every run: `-seed N` gives `+0x84 = 1`, `+0x7C = N`, `+0xD0 = {N, 666}`.
  (fn:GAME_InitSeeds@0x0052C280, data:g_SeedOverride@0x00731004, run:2026-10-11-seed-tree)
- [I] **`-seed` command-line option:** the option table has an entry {key `SEED`, switch `seed`, config offset
  `0x21A`} at `0x00705F17`. `sub_0044D860_ApplySeedOption` passes `config+0x21A` to `GAME_SetSeedOverride` **only if
  it is non-zero**, so seed 0 cannot be forced. (0x00705F50, fn:sub_0044D860_ApplySeedOption@0x0044D860, fn:GAME_SetSeedOverride@0x0052C320)
- [I] `RNG_EntropySeed(salt)` = `((GetTickCount() + time(NULL) + salt)` put through `x*0x19660D + 0x3C6EF35F` three
  times`) & 0x7FFFFFFF`. Without `-seed`, the seeds are clock-dependent and cannot be reproduced. (fn:RNG_EntropySeed@0x00650DE0)
- [C] **Act:** `DRLG_ActCreate` gets the **map seed** for every act (`sub_0053AC70_ActCreate` → `DUNGEON_ActCreate`
  → `DRLG_ActCreate`, seed argument = `ESI+0x7C`; that `ESI` is the game object is inferred from the shared
  `+0x7C` offset). It sets act seed `+0x000` = `init(mapSeed)`, keeps `mapSeed` at
  `+0x458`, steps once, and stores that new `low` at `+0x470`. So all acts of a game share the same `+0x470` value.
  The act index (`DL`, stored at `+0x480`) is **0-based**: Act I = 0 … Act V = 4. Observed for all five acts, each
  act created twice per game entry with identical values (the two `DUNGEON_ActCreate` callers, see Open questions).
  (fn:DRLG_ActCreate@0x00642DA0, fn:DUNGEON_ActCreate@0x006194A0, fn:sub_0053AC70_ActCreate@0x0053AC70, run:2026-10-11-seed-tree)
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
  Then it dispatches on a type read from the level's definition record (`+0x30`):
  1 → `0x00673B10`, 2 → `0x00667430`, 3 → `0x00675320`. (fn:DRLG_LevelCreate@0x00642AE0, run:2026-10-11-seed-tree)
- [C] **DRLG room:** `DRLG_RoomCreate(level /*ECX*/, type /*EDX*/)` steps the level seed, sets room seed `+0x14` =
  `init(low)`, then **steps the room seed once more** and stores that `low` at `+0x04`. 3102 room creations over 8
  runs match. The type dispatch that follows (1 → `0x0067D6D0`, 2 → `0x00666630`) only allocates and zeroes the
  type's record (`.\DRLG\OutRoom.cpp` 0x70 bytes, `.\DRLG\Preset.cpp` 0xF8 bytes) and stores it at room `+0x20`.
  Neither draws `[I]`. (fn:DRLG_RoomCreate@0x0066B3E0, fn:sub_0067D6D0_OutRoomAlloc@0x0067D6D0,
  fn:sub_00666630_PresetRoomAlloc@0x00666630, run:2026-10-11-seed-tree)
- [I] **Active room:** `DRLG_RoomActivate`
  steps the DRLG room's seed and creates a `Dungeon.cpp` room (`DUNGEON_RoomCreate`) whose seed `+0x6C` = `init(low)`.
- [I] **Units:** `sub_00465FD0_UnitInit` sets the unit seed `+0x20` = `init_one()`. If a parent room is found, it steps the
  room's seed `+0x6C` and sets the unit seed to `init(low)`, keeping that initial value at `+0x28`. `sub_00466200_UnitInitB`
  does the same. That the parent is the `Dungeon.cpp` active room is inferred from the shared `+0x6C` seed offset and
  the room → level → act lookups the code performs on it (`FUN_0061A1B0`, `DRLG_ActFromLevelId`).

## Leads used

- [L] d2-landmarks: "seeds per game, unit, item, room/DRLG; level seed derived from the game seed, so the same game
  seed gives the same maps". **Held, with a refinement:** the maps derive from the separate *map seed* (`game+0x7C`),
  not from the game seed at `+0xD0`, and level seeds are sums rather than draws.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x0052C280` | `GAME_InitSeeds` | game seed `+0xD0`, map seed `+0x7C`, override flag `+0x84` | C |
| `0x0052C320` | `GAME_SetSeedOverride` | `g_SeedOverride = arg` (stack arg) | I |
| `0x00731004` | `g_SeedOverride` | initial value `0xFFFFFFFF` = no override | I |
| `0x0044D860` | `sub_0044D860_ApplySeedOption` | `if (cfg+0x21A) GAME_SetSeedOverride(cfg+0x21A)` | I |
| `0x00650DE0` | `RNG_EntropySeed` | clock + salt, put through an LCG three times, 31-bit result | I |
| `0x0053AC70` | `sub_0053AC70_ActCreate` | creates act `EBX` with seed `game+0x7C`, stores it at `game+0xBC+4*act` | I |
| `0x006194A0` | `DUNGEON_ActCreate` | 0x60-byte act object, calls `DRLG_ActCreate` | I |
| `0x00642DA0` | `DRLG_ActCreate` | 0x48C-byte DRLG act, act seed and act-specific draws | C |
| `0x00642AE0` | `DRLG_LevelCreate` | 0x230-byte level, seed `+0x1C4`, generator dispatch | C |
| `0x0066B3E0` | `DRLG_RoomCreate` | 0xEC-byte DRLG room, seed `+0x14` | C |
| `0x006422A0` | `DRLG_RoomActivate` | derives an active room from a DRLG room | I |
| `0x00619890` | `DUNGEON_RoomCreate` | 0x80-byte active room, seed `+0x6C` | I |
| `0x006427F0` | `DRLG_ActFromLevelId` | act index from level ID (threshold table at `0x006EB2F0`) | I |
| `0x00465FD0` | `sub_00465FD0_UnitInit` | unit seed `+0x20` from room seed, initial value `+0x28` | I |
| `0x00466200` | `sub_00466200_UnitInitB` | same derivation, second constructor | I |
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

// fn:DRLG_RoomActivate@0x006422A0 → DUNGEON_RoomCreate@0x00619890
RNG_Step(&drlgRoom->seed);  RNG_SeedInit(&activeRoom->seed /*+0x6C*/, drlgRoom->seed.low);

// fn:sub_00465FD0_UnitInit@0x00465FD0
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
  and `0x005479C0` (`.\MONSTER\MonsterRegion.cpp`) seed a new object from one draw of the seed at `ECX+0xD0`. That this
  `ECX` is the game object is only suggested by the shared `+0xD0` offset `[L]`.
- [I] Items (`.\ITEMS\Items.cpp`, `0x00558D90`): the item unit seed `+0x20` is set from a creation parameter (`+0x48`)
  rather than drawn, and a second item-side seed is set from `+0x4C`. This is the item spec's starting point.
- [I] `.\DATATBLS\LvlTbls.cpp` (`0x0061FCF0`) initialises a global seed (via `PTR_DAT_00744504`) to `init(0)`.
  `.\QUESTS\QUESTS.CPP` (`0x00545D80`) has seed inits too. Neither is followed yet.
- In total, 103 calls to the two initialisers sit in 76 functions. This finding covers the 15 above.

## Dead ends

- Assumed at first that units draw from the game seed. They draw from their active room's seed.

## Open questions

- Who calls `DUNGEON_ActCreate` from `0x0044E100` (the second caller), and with which seed? It may be the client side.
- Meaning of act `+0x094`/`+0x484` (which tomb is the real one) and `+0x474` (Act III bit). These need their readers.
- (Column answered: `+0x30` = `Levels.txt:DrlgType`, see [data/0001](../data/0001-excel-loader.md).) Which generator each of `0x00673B10`, `0x00667430`
  and `0x00675320` is. Community docs say 1 = maze, 2 = preset, 3 = outdoor `[L]`.
- The `ECX` object of the `+0xD0` sites (game?), and the monster spawn path's seed (spawn draws from the active room?).
- Runtime check: done, see run:2026-10-11-seed-tree. Not reached by the run: active-room seeds (`DUNGEON_RoomCreate`)
  and unit seeds. They need breakpoints at `0x006422A0`/`0x00619890` and `0x00465FD0`, and the unit-constructor
  predicate from plan 0003 Phase 1 first.
- The Act III act-seed consumers under `0x006789B0` (119 steps for seed 12345) and the level-6 branch's meaning
  (which level-27 field the bit sets). Both belong with `drlg/overview`.
- Each act is created twice per game entry with identical values. That fits a server and a client copy (second
  `DUNGEON_ActCreate` caller `0x0044E100`), but the run didn't log which caller each hit came from.
