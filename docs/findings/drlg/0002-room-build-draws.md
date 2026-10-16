# 0002 — Room-build draws: the k window and a static k model

> **Subsystem:** drlg/overview (feeds rng/seeds step 6, drlg/outdoor, drlg/preset)
> **Question:** Which code steps the DRLG room seed `+0x14` between the re-seed and the activation draw, and how many times (k), as a function of the room's data?
> **Date:** 2026-10-11 (§ Entry flags: 2026-10-15)   **Plan:** 0008 (Phases 1–2), 0027 Phase 2   **Status:** open (k `[C]` by run:2026-10-11-drlg-roomk; P2 accepted with fixes F1–F3, plan 0008 log 2026-10-12; F1 and F2 done 2026-10-12, same run, checker addendum; 2026-10-12 backlog answers: merge tables re-read, Bit2TileMerge tags split, release/re-activation)

The k window is the code between `sub_0066EE40_DrlgRoomReseed` (seed `+0x14 = init(+0x04)`) and the
inlined step in `DRLG_RoomActivate` (rng/0002 § Active room). This finding enumerates it with a
recorded script, places every open draw site of drlg/0001, and writes k as pseudocode.

## Answer (summary)

- [C] **Plan 0027 Phase 2 (2026-10-15).** The entry flag word is now stated and reproduced in full, per entry kind
  (§ Entry flags in full): every wall, floor and shadow entry of every logged activation dump in the 40 logs that carry
  `CB` lines matches the model, including the cell bits 28, 17 and 16 that the collision stamp reads. The bit-2 path
  needs real entry chains: a visible warp wall or a hidden-warp floor is re-linked into its warp node's list, which
  cuts older entries off the node's chain. And `tools/drlg.py gen` now runs the roomk passes on the type-1 grids it
  predicts (drlg/0008 § 16.4), not the logged ones (§ Entry flags, the 2026-10-15 addenda).
  (fn:sub_0066DB20_RoomTileSetFlags@0x0066DB20, fn:sub_0066E260_WarpTileAdd@0x0066E260, run:2026-10-14-collision, run:2026-10-15-objects)

- [C] **k is predicted bit-exact.** `tools/drlg.py roomk` implements § k as pseudocode (with the Phase 2
  corrections below) and predicts the room seed at every LvlSub pass, at the type init, at the activation
  draw (RACT) and the active-room seed (AROOM) for **all 520 activations** of
  [run:2026-10-11-drlg-roomk](experiments.md#run2026-10-11-drlg-roomk): seeds 12345 and 777, the Act I town
  and the Blood Moor (type 1 and type 2 rooms), the Act II town (`-act 2`, preset rooms) and the maze levels
  Den of Evil, Catacombs Levels 2–4 (reached by waypoint), server and client copies, k = 0..388, with
  0 mismatches over 8776 checks. Every p1 room repeats its logged k (45/45 for 12345, 40/40 for 777). The
  only boundary oracle is `sub_0066D9E0_Orient89Unit` (526 calls). (fn:sub_0066EE40_DrlgRoomReseed@0x0066EE40,
  fn:DRLG_RoomActivate@0x006422A0, fn:sub_0066D9E0_Orient89Unit@0x0066D9E0)
- [C] **Correction: the bit-2 merge re-pick draws on the neighbour's seed.** At `0x0066E8F7`
  `sub_0066E740_Bit2TileMerge` calls `DRLG_PickTileByRarity` with ECX = the **neighbour** room (`arg_ch`), so
  that pick steps the neighbour's `+0x14` (after the neighbour's own activation) and reads the neighbour's
  DT1 list. It is **not** part of this room's k. The other merge pick (`0x0066E87C`, a new orientation-3
  wall and its orientation-4 partner) is on this room; that branch is `[I]` (never reached in the run, see
  § Bit2TileMerge, 2026-10-12). 354 neighbour re-picks in the run, each checked
  through the neighbour's seed at the next TINIT. (fn:sub_0066E740_Bit2TileMerge@0x0066E740)
- [C] **Correction: hidden-warp floor picks use orientation 0.** `sub_0066E360_HiddenWarpTilesAdd` picks
  with EDX = 0 and cell `((s << 12) | i | 4) << 8`, i.e. key (0, s, 4+i), i = 0..3, s = bits 8–15 of the
  warp cell. (fn:sub_0066E360_HiddenWarpTilesAdd@0x0066E360)
- [C] **Every room border carries bit 2, so the bit-2 path is the common case.** Type 1: after the LvlSub
  passes and the theme fill, `sub_0067C600_GridBorderOp` ORs `0x4` into the border cells of the wall and
  floor grids (`0x0067D4E8`, `0x0067D4F9`); the modelled grids equal the logged TINIT grids in every type-1
  room. Bit 7 of a cell becomes entry flag `0x1`, which makes a later merge with that entry draw nothing
  (exercised through the logged type-2 grids). (fn:sub_0067C600_GridBorderOp@0x0067C600,
  fn:sub_0067D2D0_OutRoomGridPrepare@0x0067D2D0, fn:sub_0066E740_Bit2TileMerge@0x0066E740)
- [C] **Type 2: the grids are views of the room's DS1, with `0x84` on the borders.** The prepare
  makes each grid a view into a layer of the cached DS1 at the room's offset in the preset, OR-s `0x84`
  (bits 2 and 7) into the border cells of wall layer 0, of every floor layer and of the shadow layer
  (`0x0066688D`, `0x00666952`, `0x0066696E`), and `i << 18` into every cell of wall and floor layer i ≥ 1
  (§ Type 2 prepare). `tools/drlg.py roomk` rebuilds the grids of **all 464 type-2 rooms** of
  run:2026-10-11-drlg-roomk from the DS1 files and equals the logged TINIT grids, server and client,
  town, Act II town and maze levels (checker addendum of 2026-10-12). Dropping any one of the writes
  gives 380 to 464 grid mismatches. (fn:sub_006667D0_PresetRoomGridPrepare@0x006667D0,
  fn:sub_0067CCC0_GridView@0x0067CCC0, fn:sub_0067C600_GridBorderOp@0x0067C600, fn:sub_0067C590_GridOpAll@0x0067C590)
- [I] **The write persists in a cache that every copy shares, and no grid can show it.**
  `DS1_LoadCached` keeps one parsed DS1 per path in a process-wide list (data:g_Ds1Cache@0x0096D60C,
  under a critical section), so every preset instance that uses the file, in both act copies, gets the same
  buffer, and the prepare writes into it, because the grids are views and not copies. All the writes are OR-s
  that each room repeats on its own view, so a later room can see an earlier room's bits only in a cell that
  is a border of the earlier view and interior to its own. In the run, a model with a persistent buffer
  and a model with a fresh buffer per room give identical grids for every type-2 room `[C]`. So a
  reimplementation may apply the prepare to a private copy. (fn:DS1_LoadCached@0x00665F40)
- [I] **Completeness.** `RngCallGraph.java` walks the direct-call graph under `0x0067D2D0`, `0x0067D710`,
  `0x006667D0`, `0x00666AC0` plus the six grid-op stubs of data:g_GridOps@0x00749BAC: 657 functions
  (558 code functions and 99 import externals; tail calls are followed through Ghidra's `CALL_TERMINATOR`
  flow type), **4 draw from an RNG, all on the DRLG room seed `+0x14`**, 0 unclassified. They are
  `DRLG_PickTileByRarity`, `sub_0066D9E0_Orient89Unit`, `sub_0066FF50_LvlSubApplyAll` and
  `sub_00670170_LvlSubApplyPick`. (fn:DRLG_PickTileByRarity@0x0066D820, fn:sub_0066D9E0_Orient89Unit@0x0066D9E0,
  fn:sub_0066FF50_LvlSubApplyAll@0x0066FF50, fn:sub_00670170_LvlSubApplyPick@0x00670170)
- [C] **Two kinds of draw make up k.** For type 1 (outdoor) rooms, the grid prepare `0x0067D2D0` first
  applies **`LvlSub` substitutions** with draws on the room seed (k_sub). Then both room types build tiles,
  with one rarity draw per tile pick whose candidate rarity sum is > 0, plus a rare `Range(3)` for
  two orientation-8/9 object units (k_tile). Type 2 (preset) rooms have no k_sub: their prepare
  `0x006667D0` makes no draw. (fn:sub_0067D2D0_OutRoomGridPrepare@0x0067D2D0, fn:sub_006667D0_PresetRoomGridPrepare@0x006667D0)
- [I] **`0x00667620` is outside the window.** It steps room `+0x14` (preset-unit keep/drop rolls), but
  `sub_0061B730_RoomActivateB` and `sub_0061B320_RoomPrepareFiles` call it through
  `DRLG_PresetRoomLoadDs1` **before** the re-seed, which discards those draws. The DS1 file index
  is already stored when that runs: **the preset file pick is not a room-seed draw in the window**, so it
  stays with Phase 3. `0x00667620` has two more callers outside activation (§ Activation order); its own
  semantics go to Phase 3 / `drlg/preset`. (fn:sub_0061B730_RoomActivateB@0x0061B730, fn:DRLG_PresetRoomLoadDs1@0x00667890,
  fn:DRLG_PresetUnitDropRolls@0x00667620, fn:DRLG_PresetMapScan@0x00667970)
- [I] Every other open site of drlg/0001 is **inside** the window and draws only through
  `DRLG_PickTileByRarity` or `sub_0066D9E0_Orient89Unit` (table in § Draw-site placement).
  (fn:sub_0066E9B0_RoomCellBuild@0x0066E9B0, fn:sub_0066E940_Bit2CellBuild@0x0066E940)
- [C] **Server and client k can differ** because the bit-2 path (`0x0066E940`) looks for an existing tile
  at the same cell in the room's **neighbour rooms that are already built** (`+0x54 ≠ 0`). Which
  neighbours are built depends on activation order in that act copy, and the two branches make different
  numbers of picks. Both copies are predicted by the same model; no client-only branch inside the window
  was needed (run:2026-10-11-drlg-roomk: 0 mismatches in both copies, 179 server activations among them).
  (fn:sub_0066E580_NeighbourTileScan@0x0066E580, fn:sub_0066E4C0_NeighbourTileFind@0x0066E4C0)
- [I] **RoomTile `T[+0x18]`/`T[+0x20]`** are the wall and floor tile **counts** at the end of the build:
  the builder copies the used counters `T[+0x08]`/`T[+0x0C]` over the capacities. So `DRLG_RoomActivate`
  draws once more iff the room got at least one wall or floor tile. (fn:sub_0067D710_OutRoomTilesBuild@0x0067D710,
  fn:sub_00666AC0_PresetRoomTilesBuild@0x00666AC0)
- [C] **Maze rooms are type-2 rooms.** Every Catacombs room of the run had `+0x48 = 2` and a
  `LvlPrest` record, and the type-2 model predicts them. (fn:sub_00667ED0_PresetRoomsCreate@0x00667ED0)
- [C] **Maze rooms' `+0x50` mask** is the `LvlPrest` `Dt1Mask` of the room's preset, like other preset rooms.
  The maze code `0x00673A60` turns its rooms into DRLG rooms through `sub_00667ED0_PresetRoomsCreate`,
  which writes `+0x50` (drlg/0001 § Third pass). Checked for all 464 type-2 rooms of the run, 92 of them on
  `DrlgType` 1 levels (Catacombs Levels 2 and 3), 349 on `DrlgType` 2 and 23 on `DrlgType` 3 levels.
  (fn:sub_00673A60_MazeLevelRooms@0x00673A60, fn:sub_00667ED0_PresetRoomsCreate@0x00667ED0, tbl:LvlPrest.txt:Dt1Mask)
- [C] **The room's DT1 list** (`+0x68`) is `LvlTypes` `File i+1` for each set bit i of `+0x50`, in bit order,
  prefixed `DATA\GLOBAL\TILES\`, followed by `Act1\Outdoors\Blank.dt1`, `Act1\Barracks\InvisWal.dt1` and
  `Act1\Barracks\Warp.dt1` (prefix `DATA\GLOBAL\Tiles\`). This equals the logged list in all 520 rooms of the
  run (56 type 1, 464 type 2). No mask bit in the run selected a `"0"` cell. (fn:DRLG_LevelDt1ListBuild@0x0066F240,
  tbl:LvlTypes.txt:File 1)
- [C] **Correction to drlg/0001: an outdoor room's `+0x50` is not only the level-type value.**
  `sub_0067D540_OutRoomCreate` stores the value of `sub_006750F0_OutdoorRoomsCreate` (level type 2 →
  `0x44103`, …). Then `sub_006706A0_LvlSubRoll` takes the level's `SubType`/`SubTheme` (leveldefs `+0x38`/`+0x3C`)
  and, for each `LvlSub` record of that `Type` in order, draws `step(room +0x14).lo % 100`. If the result is
  below `Prob[theme]` (`+0x11C`, signed `jge` skip), it sets the record's bit in the returned mask (stored
  as OutRoom `+0x6C`, the SubType pass mask) and ORs the record's `Dt1Mask` (`+0x48`) into `+0x50`. The model
  (level-type value | the `Dt1Mask` of every bit of the logged SubType pass) equals the logged `+0x50` in all 56
  type-1 rooms. All of them are Blood Moor rooms (level type 2): 28 with `0x44103` and 28 with `0x444103`, which
  is a pick of record 13 or 14 (`Dt1Mask` `0x400001`). The values for the other level types are not exercised and
  stay `[I]` (drlg/0001). These draws step the
  room seed at room creation, **before** the re-seed, so they are not in k. They are a room-creation draw for
  Phase 3. (fn:sub_0067D540_OutRoomCreate@0x0067D540, fn:sub_006706A0_LvlSubRoll@0x006706A0,
  tbl:LvlSub.txt:Prob0, tbl:Levels.txt:SubType)

## Leads used

None. No community source describes these functions; names are ours (no lead). `LvlSub` column names come
from the header row of the shipped `LvlSub.txt`, and their offsets were checked against `lvlsub.bin` (§ Data touched).

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x0061B320` | `sub_0061B320_RoomPrepareFiles` | DT1 list and, for type 2, the DS1 load, outside activation | I |
| `0x0061FA90` | `LVLSUB_GetRecordByType` | first `LvlSub` record (0x15C bytes) of a `Type`, through an index table | I |
| `0x0066B980` | `sub_0066B980_RectContains` | `x0 ≤ x < x0+w && y0 ≤ y < y0+h` on a rect `{x0,y0,w,h}` (ECX) | I |
| `0x0066C370` | `sub_0066C370_RoomNeighboursEnsure` | pre-window: ensures neighbour rooms/levels exist (reaches level creation) | I |
| `0x0066D9E0` | `sub_0066D9E0_Orient89Unit` | orientation 8/9 tile → preset unit; `Range(3)` for object ids 91–92 | I |
| `0x0066E060` | `sub_0066E060_ShadowTileAdd` | pick (orientation 13) and add one shadow tile | I |
| `0x0066E1C0` | `sub_0066E1C0_WarpUnitAdd` | warp tile → preset unit type 5 (no draw) | I |
| `0x0066E260` | `sub_0066E260_WarpTileAdd` | visible orientation 10/11: one extra pick from the room's warp record | I |
| `0x0066E360` | `sub_0066E360_HiddenWarpTilesAdd` | hidden orientation 10/11: four floor picks | I |
| `0x0066E4C0` | `sub_0066E4C0_NeighbourTileFind` | a built neighbour's tile at this cell, matching kind and bits 18–19 | I |
| `0x0066E580` | `sub_0066E580_NeighbourTileScan` | `0x0066E4C0` over the room's neighbour list (`+0x08`, count `+0x2C`) | I |
| `0x0066E620` | `sub_0066E620_Bit2TileNew` | bit-2 cell, no neighbour tile: one pick, add | I |
| `0x0066E740` | `sub_0066E740_Bit2TileMerge` | bit-2 cell over a neighbour's tile: re-pick on orientation change | I |
| `0x0066E940` | `sub_0066E940_Bit2CellBuild` | bit-2 dispatcher: merge or new | I |
| `0x0066ECE0` | `sub_0066ECE0_RoomTileCountCells` | capacity count: walls, floors (incl. filler), shadows | I |
| `0x0066EDB0` | `sub_0066EDB0_RoomTileCountOrient` | capacity count from orientations 3 and 10/11 | I |
| `0x0066EEE0` | `sub_0066EEE0_RoomTileArraysAlloc` | allocate the three 0x30-byte entry arrays | I |
| `0x0066FAD0` | `sub_0066FAD0_LvlSubStamp` | write one substitution group into the room grids; shadow picks | I |
| `0x0066FCF0` | `sub_0066FCF0_LvlSubFits` | placement test for `LvlSub` (CheckAll = 0, and tag 1) | I |
| `0x0066FE00` | `sub_0066FE00_LvlSubMatches` | match test for `LvlSub` tag-2 groups | I |
| `0x0066FF50` | `sub_0066FF50_LvlSubApplyAll` | `CheckAll ≠ 0`: try every position | I |
| `0x00670170` | `sub_00670170_LvlSubApplyPick` | `CheckAll = 0`: random group and position, `Max` times | I |
| `0x006704E0` | `sub_006704E0_LvlSubLoadDs1` | load the record's DS1 on first use (`+0x50`) | I |
| `0x006707A0` | `sub_006707A0_LvlSubApply` | one `LvlSub` pass: one record per mask bit | I |
| `0x00666710` | `DRLG_PresetUnitsToRoom` | move the preset's units inside the room to the room (no draw) | I |
| `0x006667D0` | `sub_006667D0_PresetRoomGridPrepare` | type 2 prepare: grids as views of the DS1 layers, `0x84` borders, `i << 18` layer bits (no draw) | C |
| `0x006661A0` | `DRLG_PresetClientUnitsA` | client-only: adds object preset units (id `0x41`) to the preset (no grid write) | I |
| `0x00666220` | `DRLG_PresetClientUnitsB` | client-only: adds object preset units (ids `0x28`–`0x2A`) by floor-cell test (no grid write) | I |
| `0x006663C0` | `DRLG_PresetClientObjects` | client-only, pre-window: scans DS1 floor layer 0 (read only) and adds object preset units | I |
| `0x006706A0` | `sub_006706A0_LvlSubRoll` | outdoor room creation: one `% 100` draw on room `+0x14` per SubType record, picks → SubType pass mask, ORs `Dt1Mask` into `+0x50` | C |
| `0x0067C590` | `sub_0067C590_GridOpAll` | one grid op (data:g_GridOps@0x00749BAC) on every cell | I |
| `0x0067CD30` | `sub_0067CD30_GridViewLocal` | grid view with caller-supplied row-offset buffer | I |
| `0x00667620` | `DRLG_PresetUnitDropRolls` | pre-window keep/drop rolls on room `+0x14` for some preset units | I |
| `0x00673A60` | `sub_00673A60_MazeLevelRooms` | maze code that calls `sub_00667ED0_PresetRoomsCreate` | I |
| `0x0061F310` | `LVLWARP_FindByIdDir` | first LvlWarp row (0x30 bytes) with an Id and a fitting `Direction` (`'b'` fits all); fatal if none | I |
| `0x0066AEC0` | `sub_0066AEC0_LevelWarpIds` | a level's 8 warp ids: act `+0x90` override list, else leveldefs `+0x68` | I |
| `0x0066AF30` | `sub_0066AF30_LevelWarpId` | `ids[DL]` of `0x0066AEC0` | I |
| `0x0066AF50` | `sub_0066AF50_LevelWarpRec` | `LVLWARP_FindByIdDir(ids[DL], arg)` | I |
| `0x0066B9D0` | `sub_0066B9D0_RectContainsIncl` | `x0 ≤ x ≤ x0+w && y0 ≤ y ≤ y0+h` | I |
| `0x0066DDE0` | `sub_0066DDE0_TileEntryInit` | fill a floor entry: position, tile, flags from the cell | I |
| `0x0066DEF0` | `sub_0066DEF0_RoomFloorAdd` | append a floor entry (optionally to a node list) | I |
| `0x0066DF40` | `sub_0066DF40_RoomShadowAdd` | append a shadow entry (orientation 13) | I |
| `0x0066E160` | `sub_0066E160_WarpRecFitDir` | re-look a warp node's LvlWarp row up for direction `'l'`/`'r'` | I |
| `0x0066F0B0` | `sub_0066F0B0_RoomTileFree` | free a room's RoomTile, `+0x54 = 0` | I |
| `0x0066F1A0` | `sub_0066F1A0_RoomTilesRelease` | release a built room: clear `0x100000`, free RoomTile and grids, reset warp nodes | I |
| `0x0067D680` | `sub_0067D680_OutRoomGridsFree` | type 1: free the OutRoom grids | I |
| `0x00666610` | `sub_00666610_PresetRoomGridsFree` | type 2: free the preset room's grid data (`0x00666520`) | I |
| `0x0067C600` | `sub_0067C600_GridBorderOp` | one grid op on rows 0 and h, columns 0 and w | I |
| `0x0067CB80` | `sub_0067CB80_GridAlloc` | allocate a zeroed grid {cells, row offsets, w, h, owned} | I |
| `0x0067CCC0` | `sub_0067CCC0_GridView` | grid view into a DS1 layer at an origin, with its stride | I |
| `0x0067D2D0` | `sub_0067D2D0_OutRoomGridPrepare` | type 1 prepare: grids, three `LvlSub` passes, theme fill | I |

| Address | Global | Role | Tag |
|---|---|---|---|
| `0x006EF574` | data:g_Bit2OrientMerge@0x006EF574 | s32[row·7 + old orientation], 43 cells (rows 0–5, old o 0–7, rows overlap by one): merged orientation | I |
| `0x006EF620` | data:g_Bit2OrientRow@0x006EF620 | s32[20] per new orientation 0–19: row 0–5 of the table above, −1 keep, −2 no merge | I |
| `0x0096CA00` | data:g_pLvlWarp@0x0096CA00 | LvlWarp records (count at `0x0096CA04`) | I |
| `0x0096CA10` | data:g_pLvlSub@0x0096CA10 | LvlSub records | I |
| `0x0096CA18` | data:g_LvlSubTypeIndex@0x0096CA18 | first LvlSub record index per `Type` | I |
| `0x00749BAC` | data:g_GridOps@0x00749BAC | 6 grid-cell ops: `or`, `and`, `xor`, `set`, `0x0067C460`, `and not` | I |

## Walkthrough

### The recorded enumeration

```bash
tools/ghidra.sh rngcallgraph re/rngclass/drlg-room-build.txt \
    0x0067D2D0 0x0067D710 0x006667D0 0x00666AC0 table@0x00749BAC:6
# → summary: functions=657 rng=4 unclassified=0 indirect=64
```

- [I] The script (`re/ghidra_scripts/RngCallGraph.java`) does a breadth-first walk of direct calls. It marks
  a function when it holds the immediate `0x6AC690C5` (any inlined step) or calls `RNG_Step`, `RNG_Range`,
  `RNG_RangeB`, `RNG_RangePow2`, `RNG_RangePow2Plus`, `RNG_SeedInitOne` or `RNG_SeedInit`. Each marked
  function must have a row in `re/rngclass/drlg-room-build.txt`. The file gives the seed it steps, read
  from the code. (fn:RNG_Step@0x0045C370, fn:RNG_Range@0x0045C390)
- [I] Indirect calls are not followed, so each one was checked. The grid helpers
  (`0x0067C4F0`, `0x0067C590`, `0x0067C600`, `0x0067C8E0`) call through data:g_GridOps@0x00749BAC. Its six
  targets are scanned as stubs: 2–5 instructions, no call, no multiplier. The other 60 are inside
  allocator, file, string-format and fatal-error library code (`0x00401CB0`–`0x0042B170`,
  `0x00681A57`–`0x0069A295`, `0x006B01B0`–`0x006B0660`, depth ≥ 4). No game RNG is reached through them.
- [I] Classification: all four are room `+0x14`. `DRLG_PickTileByRarity` copies ECX (the DRLG room) to ESI
  and steps `[ESI+0x14]` (`0x0066D831`). `sub_0066D9E0_Orient89Unit` calls `RNG_Range(ESI+0x14, 3)`
  (`0x0066DABB`) with ESI = the room (it reads `+0x58`, `+0x34..+0x40`). The two `LvlSub` functions step
  `*(param_1)+0x14`, and `0x0067D2D0` stores the room (ESI) at `[ebp-0x68]`, the head of the struct it
  passes (`0x0067D3D7`).

### Activation order (where the window is)

```c
// fn:sub_0061B730_RoomActivateB@0x0061B730 (trimmed). RoomActivateA runs only the last block.
if (!(R[+0x28] & 0x1000000)) DRLG_LevelDt1ListBuild(R);               // DT1 list
if (!(R[+0x28] & 0x2000000) && R[+0x48] == 2) PresetRoomLoadDs1(R);   // → 0x00667620 (draws, discarded)
if (!(R[+0x28] & 0x100000)) {
  if (R[+0x2C] == 0) RoomNeighboursEnsure(R);                         // 0x0066C370, pre-window
  DrlgRoomReseed(R);      // seed = init(R[+0x04]); type 1 → 0x0067D2D0, type 2 → 0x006667D0   ┐ window
  DrlgRoomTypeInit(R);    // type 1 → 0x0067D710, type 2 → 0x00666AC0                          ┘
  DRLG_RoomActivate(act, R);                                           // +1 draw iff T[+0x18] || T[+0x20]
}
```

- [I] So the window is exactly the four roots and their callees. `0x0066F240`, `0x00667890` (with
  `0x00667620`) and `0x0066C370` run **before** the re-seed. They set the window's inputs (DT1 list,
  DS1 grids, neighbour rooms) but their own draws on `+0x14` don't count.
  (fn:sub_0061B730_RoomActivateB@0x0061B730, fn:sub_0061B190_RoomActivateA@0x0061B190,
  fn:sub_0066EE40_DrlgRoomReseed@0x0066EE40, fn:sub_0066EE70_DrlgRoomTypeInit@0x0066EE70)
- [I] `DRLG_PresetRoomLoadDs1` opens `LvlPrest + 0x44 + i·0x3C` with `i` read from the preset
  record (`piVar[1]`); it draws nothing to choose `i`. `0x00667620` walks the DS1's preset units:
  monsters with ids `0xCC`, `0xCD`, `0x173`, `0x174` are kept on `step % 3 == 0`, some
  SuperUnique/object ids on a parity or `& 3` test. That belongs to `drlg/preset`.
  (fn:DRLG_PresetUnitDropRolls@0x00667620)
- [I] `0x00667620` has three callers in all (architect review, r2): `DRLG_PresetRoomLoadDs1`
  (from `RoomActivateB`, `sub_0061B320_RoomPrepareFiles`, and `0x0061B210+0x133`), and
  `DRLG_PresetMapScan`, which `sub_00667ED0_PresetRoomsCreate` calls at `0x00667F3F` during room
  creation. `0x00667890` runs it only on the **first** DS1 load per preset instance (`preset[+0xC] == 0`),
  and it steps the seed of whichever room triggers that load. None of these is in the k window.
  (fn:DRLG_PresetRoomLoadDs1@0x00667890, fn:DRLG_PresetMapScan@0x00667970,
  fn:sub_00667ED0_PresetRoomsCreate@0x00667ED0)

### Type 1 prepare: the `LvlSub` passes (k_sub)

```c
// fn:sub_0067D2D0_OutRoomGridPrepare@0x0067D2D0 (trimmed). OR = the 0x70-byte OutRoom (R[+0x20]), D = leveldefs record
grids_init(); 8×8 grid op set(0x40002); if (act(level) == 0) 0x00680C80();   // no draws
RoomTileAlloc(R);
p = {room: R, outroom: OR, ..., type, theme, mask};
if (m = (R[+0x28] >> 16) & 3) LvlSubApply(p{type: D.SubWaypoint /*+0x40*/, theme: 0, mask: m});
if (m = (R[+0x28] >> 12) & 0xF) LvlSubApply(p{type: D.SubShrine /*+0x44*/, theme: 0, mask: m});
LvlSubApply(p{type: OR[+0x64], theme: OR[+0x68], mask: OR[+0x6C]});
theme-fill: floor-grid cells whose bits 0x3F0FF80 are clear |= v(level type)   (no draw)
GridBorderOp(wall grid, or 0x4); GridBorderOp(floor grid, or 0x4)                 (no draw)

// fn:sub_006707A0_LvlSubApply@0x006707A0
if (p.type == -1) return;
rec = LVLSUB_GetRecordByType(p.type);                   // 0x15C-byte records
for (m = p.mask; m; m >>= 1, rec++)                     // bit i = i-th record of that Type
  if (m & 1) { LvlSubLoadDs1(rec); rec.CheckAll ? LvlSubApplyAll(p, rec) : LvlSubApplyPick(p, rec); }
```

- [C] Draws, all on room `+0x14`, all values int32, `theme` = `p[+0x34]`. `Range(n)` is the inlined
  `RNG_Range`: signed `n ≤ 0` → 0 with **no** step; n a power of two → step, `lo' & (n−1)` (so n = 1 still
  steps); else step, unsigned `lo' % n`. (fn:sub_0066FF50_LvlSubApplyAll@0x0066FF50,
  fn:sub_00670170_LvlSubApplyPick@0x00670170, fn:RNG_Range@0x0045C390)

```c
// ApplyAll, CheckAll != 0. G = the record's DS1 groups: count ds1[+0x4C], array ds1[+0x50], stride 0x18
for g in G:                                         // in DS1 order
  W = R[+0x3C] - g[+0x08] + 1;  H = R[+0x40] - g[+0x0C] + 1
  if (W <= 0 || H <= 0) continue                    // signed
  if (ds1.tag_type == 1)
    for y in 1..H-1: for x in 1..W-1:               // x inner
      if Fits(x,y): Stamp(x,y,0)                    // no draws
  else if (ds1.tag_type == 2)
    for y in 0..H-1: for x in 0..W-1:               // x inner
      if Matches(x,y):
        r = step(seed).lo % 100                     // always one step; unsigned %
        if (Prob[theme] < r):                       // signed (cmp Prob,r; jge skip)
          v = Range(g[+0x14])
          Stamp(x,y,(g[+0x08]+1)*(v+1))
  // other tag_type values: nothing

// ApplyPick, CheckAll == 0
if (G.count == 0 || Max[theme] <= 0) return         // signed
repeat Max[theme] times:
  g = G[Range(G.count)]                             // drawn even if the size test below fails
  dx = R.w - g.w;  dy = R.h - g.h
  if (dx < 1 || dy < 1) continue
  if (Trials[theme] == -1):
    n = dx*dy;  list[i] = (i % dx, i / dx) for i < n          // signed idiv
    repeat n times: a = Range(n); b = Range(n); swap(list[a], list[b])   // exactly 2n draws
    first i with Fits(list[i].x+1, list[i].y+1) → Stamp(…,0)
  else:
    repeat Trials[theme] times (none if signed <= 0):
      x = Range(dx)+1; y = Range(dy)+1              // x drawn before y
      if Fits(x,y): Stamp(x,y,0); break
```

- [I] **Shipped data:** all 34 stock `LvlSub` records have `CheckAll = 0`, so ApplyAll and `Prob` are never
  reached with shipped data (the ApplyAll lines stay `[I]`; `tools/drlg.py` refuses such a record).
  11 records have `Trials0 = −1`. (fn:sub_00670170_LvlSubApplyPick@0x00670170)
- [C] ApplyPick as written above, including the `Trials = −1` shuffle (records 6 and 9 in the run, 5 passes)
  and the group draw made before the size test (run:2026-10-11-drlg-roomk; every LSUBX seed predicted).
  (fn:sub_00670170_LvlSubApplyPick@0x00670170)
- [C] The grids (`p[1]`, `p[5]`, `p[9]` = OutRoom `+0x00` orientation, `+0x14` wall, `+0x28` floor, each
  (w+1)×(h+1)) and the record's DS1 grids (`sub_006704E0_LvlSubLoadDs1`: orientation layer i at rec
  `+0x54+0x14·i`, wall layer i at `+0xA4+0x14·i` with `i << 18` OR-ed in for i ≥ 1, floor 0 at `+0xF4`,
  shadow at `+0x108`; views of the DS1 cells, stride `size_x+1`). With `sx, sy` the group cell and
  `rx, ry` the room cell: (fn:sub_0066FCF0_LvlSubFits@0x0066FCF0, fn:sub_0066FAD0_LvlSubStamp@0x0066FAD0,
  fn:sub_006704E0_LvlSubLoadDs1@0x006704E0)

```text
Fits(x, y):  for each group cell (row-major):
               if sub.floor & 2, or (sub has wall layer 0 and sub.wall0 & 1):
                 room.floor[rx,ry] & 0x3F0FF00 → false;  !(room.floor & 2) → false;  room.wall & 1 → false
             true
Stamp(x, y): for each group cell (row-major):
               f = sub.floor (0 if the DS1 has no floor layer);  f & 2 → room.floor = f | 0x80
               w = sub.wall0;  w & 1 → room.wall = w;   o = sub.orient0;  o ≠ 0 → room.orient = o
               sh = sub.shadow;  sh & 0x8000000 → pick(13, sh), shadow entry   [0x0066E073]
             then the record's preset units (no draw)
```

- [C] So k_sub depends on the grid contents through `Fits`, which reads the room's grids as the earlier
  passes and stamps left them, and `Stamp` picks a tile for every stamped shadow cell at `0x0066E073`
  (`sub_0066E060_ShadowTileAdd`, orientation 13), **inside** the prepare. The modelled grids equal the
  next LSUB grids and, after the theme fill and border bits, the TINIT grids in every room of the run.
  (fn:sub_0066E060_ShadowTileAdd@0x0066E060)
- [C] Theme value by level type (`0x0067D446`): 16 → `0x100`, 21 → `0x120000`, 22 → `0x100000`,
  27 → `0xA00000`, 28 → `0x1600000`, 31 → `0x600000` for level 117 else 0, other → 0; OR-ed into
  floor-grid cells with no bit of `0x3F0FF80`, over the whole (w+1)×(h+1) grid. `sub_0067C600_GridBorderOp`
  applies one grid op to row 0, row h, then column 0 and column w of rows 1..h−1.
  (fn:sub_0067C600_GridBorderOp@0x0067C600)
- [I] `Act1/Outdoors/Trees.ds1` (LvlSub record 11, `Type` 6) is 12 bytes short: `DS1_Parse` reads the last
  group's y, w and h past the end of the file buffer (`FILE_LoadWhole` allocates the exact size, no
  padding seen). The run logged the group list from memory 27 times: `(0,0,0,0)` 26 times and once
  `(0,229120,245560,1)`. The model takes the logged values; the group was drawn 4 times, always with w = h = 0
  (Fits holds trivially, Stamp writes nothing, so the pass consumes its group draw plus one x and one y
  draw). With heap garbage, `dx < 1` and only the group draw is made. See Open questions.
  (fn:DS1_Parse@0x00665950, fn:FILE_LoadWhole@0x00517079)

### Type 2 prepare: the grids from the DS1

```c
// fn:sub_006667D0_PresetRoomGridPrepare@0x006667D0 (from the disassembly, renamed). ECX = room R.
PR = R[+0x20]; ps = PR[+0x08] /*preset instance*/; ds1 = ps[+0x0C] /*DS1_LoadCached record*/
rect = {R.x - ps.x, R.y - ps.y, R.w + 1, R.h + 1};  stride = ps.w /*+0x18*/ + 1
for i in 0 .. ds1.nwall-1:  GridView(&PR.wall[i] /*+0x10+0x14i*/,   ds1.wall[i] /*[11+i]*/,   rect, stride)
                            GridView(&PR.orient[i] /*+0x60+0x14i*/, ds1.orient[i] /*[7+i]*/,  rect, stride)
if (ds1.nwall) GridBorderOp(&PR.wall[0], 0x84, or)                         // 0x0066688D
for i in 1 .. ds1.nwall-1: GridOpAll(&PR.wall[i], i << 18, or)
for i in 0 .. ds1.nfloor-1: GridView(&PR.floor[i] /*+0xB0+0x14i*/, ds1.floor[i] /*[15+i]*/, rect, stride)
                            GridOpAll(&PR.floor[i], i << 18, or)
GridView(&PR.shadow /*+0xD8*/, ds1.shadow /*[17]*/, rect, stride)
for i in 0 .. ds1.nfloor-1: GridBorderOp(&PR.floor[i], 0x84, or)           // 0x00666952
GridBorderOp(&PR.shadow, 0x84, or)                                         // 0x0066696E
PresetUnitsToRoom(R)                                                       // 0x00666710, no draw
```

- [C] `sub_0067CCC0_GridView` makes a grid `{cells = layer + 4·(rect.y·stride + rect.x), row i at i·stride,
  w = rect.w, h = rect.h}`, so the grid is a window on the DS1 cells, not a copy, and every op above
  writes the cached DS1. The model `preset_prepare` in `tools/drlg.py` does exactly the lines above, and its
  views equal the logged TINIT grids of all 464 type-2 rooms (run:2026-10-11-drlg-roomk, checker addendum
  2026-10-12). The orientation layers get no write. Wall layers i ≥ 1 get no border bits.
  (fn:sub_0067CCC0_GridView@0x0067CCC0, fn:sub_0067C590_GridOpAll@0x0067C590, fn:sub_0067C600_GridBorderOp@0x0067C600)
- [I] `ps.w` (`+0x18`) is the preset's width, equal to the DS1's `size_x` in every room of the run, so the
  view's stride is the DS1 row length. The DS1 a room views is `LvlPrest` `File(ps[+0x04]+1)` of its record
  `ps[+0x08]` (`DRLG_PresetRoomLoadDs1`). The logger does not record `ps[+0x04]`, so the checker finds the
  file whose views reproduce the grids: 457 rooms have exactly one such file, 7 have 2 or 3 identical
  candidates, and the files found for the rooms of one preset instance always agree. Logging the index
  belongs to Phase 3. (fn:DRLG_PresetRoomLoadDs1@0x00667890)

### Tile build (k_tile)

```c
// type 1: fn:sub_0067D710_OutRoomTilesBuild@0x0067D710
RoomTileAlloc; CountOrient(OR); CountCells ×2; ArraysAlloc;
RoomCellsBuild(OR, filler=0, kx=0, ky=0);  RoomCellsBuild(0, 0, 0, 0);      // two passes
T[+0x18]=T[+0x08]; T[+0x20]=T[+0x0C]; T[+0x28]=T[+0x10];  0x0066CCB0;      // no draw after

// type 2: fn:sub_00666AC0_PresetRoomTilesBuild@0x00666AC0; P = LvlPrest record
kx, ky = P.KillEdge(+0x18) ? (room right/bottom edge == preset right/bottom edge) : false
for f in floor layers (DS1 [6]):  RoomCellsBuild(floor f, filler = (f == 0 && P.FillBlanks(+0x1C)), kx, ky)
for w in wall layers (DS1 [5]):   RoomCellsBuild(wall w + orient w, 0, kx, ky)
RoomCellsBuild(shadow, 0, kx, ky)
if (P.Def == 1 || P.Def == 108) RoomCellsBuild(extra grid, 0, kx, ky)
copy counts as type 1                                                       // anim passes: no draw

// fn:sub_0066EC10_RoomCellsBuild@0x0066EC10
for y in 0 .. R.h - 1 + (ky ? 0 : 1):           // rows outer
  for x in 0 .. R.w - 1 + (kx ? 0 : 1):         // columns inner
    RoomCellBuild(cell, orient, R.x + x, R.y + y, filler)
```

- [I] Per cell (`sub_0066E9B0_RoomCellBuild`), with `o` the orientation, `m` = bits 20–25, `s` = bits 8–15,
  and **pick** = one `DRLG_PickTileByRarity`. It gathers at most 40 candidates (`push 0x28`) for the
  **primary** key `(o,m,s)` over the room's DT1 list, and draws iff that gathers ≥ 1 candidate **and** their
  signed rarity sum is > 0. When the primary key finds nothing, the `(10,0,0)` fallback returns `buf[0]`
  with **no draw** (`0x0066D868`–`0x0066D8A3`, architect review). Write `Σ(o,m,s)` for the sum over the
  primary candidates. (fn:sub_0066E9B0_RoomCellBuild@0x0066E9B0, fn:sub_0066DC50_RoomTileAdd@0x0066DC50,
  fn:sub_0066DB20_RoomTileSetFlags@0x0066DB20)

```text
if o ∈ {10,11} and m ≥ 8: nothing
if o == 0 and m == 30 and s ∈ {0,1}: cell |= 0x80000000
if cell bit 31:
  o ∈ {8,9}, level ∉ {111,112,117}: Orient89Unit(cell)                   → 0 or 1 Range(3); stop
  o ∈ {10,11}:  WarpUnitAdd; HiddenWarpTilesAdd: warp node of this cell (below) or return; fit its LvlWarp
                row to o; if LitVersion (+0x24) ≠ 0: 4 picks, keys (0, s, 4..7) ; stop
if cell bit 2:
  kind = bit 1 → floor (o 0) | bit 0 → wall (o) | bit 27 and not bit 31 → shadow (o 13) | else fall through
  Bit2CellBuild: neighbour tile found (built neighbours only) → Bit2TileMerge, else Bit2TileNew; stop
floor:  bit 1 → pick(0, cell)
        else if filler and RectContains(R.rect, x, y) → pick(0, 0x1E00000 | (level 74 ? 0x100 : 0))
wall:   bit 0 → pick(o, cell); AddWall: o == 3 → pick(4, cell) [0x0066DD02];
                o ∈ {8,9} → Orient89Unit(tile);  o ∈ {10,11}, level ≠ 133 → WarpTileAdd
shadow: bit 27 → pick(13, cell)
```

- [C] **Warp node of a cell.** `sub_0066AF30_LevelWarpId` returns `ids[m]`, m = bits 20–25 of the cell,
  from the level's warp-id array (`sub_0066AEC0_LevelWarpIds`: the act's per-level override list at act
  `+0x90`, else leveldefs `+0x68`). The node is the first of the room's list `R[+0x4C]` (next `+0x04`) whose
  LvlWarp row (`+0x10`) has that `Id`. `sub_0066E160_WarpRecFitDir` then replaces the node's row by
  `LVLWARP_FindByIdDir(Id, d)` (first row with that Id whose `Direction` is `'b'` or d) when its own
  `Direction` is neither `'b'` nor d, with d = `'r'` for o 11 and `'l'` for o 10. `sub_0066E1C0_WarpUnitAdd`
  (no draw) needs `LVLWARP_FindByIdDir(ids[m], d)` (fatal if none) and makes a unit unless the cell is on the
  room's right column (`x − R.x = w`) or bottom row. (fn:sub_0066AF30_LevelWarpId@0x0066AF30,
  fn:sub_0066AEC0_LevelWarpIds@0x0066AEC0, fn:sub_0066E160_WarpRecFitDir@0x0066E160,
  fn:LVLWARP_FindByIdDir@0x0061F310, fn:sub_0066E1C0_WarpUnitAdd@0x0066E1C0, data:g_pLvlWarp@0x0096CA00)
- [C] `WarpTileAdd` (`0x0066E260`): the warp node of the cell (fatal if none). If `s ∉ {0,4}`, or
  `WarpUnitAdd` succeeds: fit the row to o, and if its `LitVersion` (`+0x24`) ≠ 0, **one pick**
  (`0x0066E31B`, orientation o) of `cell | Tiles(+0x28) << 8`. 24 visible and 15 hidden warp cells in the run.
  (fn:sub_0066E260_WarpTileAdd@0x0066E260)
- [C] **Bit-2 lookup** (`sub_0066E580_NeighbourTileScan`): neighbours in `R[+0x08]` order, skipping R; a
  neighbour counts if it has a RoomTile (`+0x54 ≠ 0`) and `x0 ≤ x ≤ x0+w`, `y0 ≤ y ≤ y0+h`
  (`sub_0066B9D0_RectContainsIncl`, inclusive). In its node list (head first; kind 1 = floor, kind 0 =
  walls and shadows; the lookup wants kind 1 iff o = 0), entries head first (prepended): the first entry at
  (x, y) with o ≠ 4, (o = 13 or cell bit 27 clear), and (flags & `0x1C000` = 0 or
  ((flags >> 14) & 7) − 1 = (cell >> 18) & 3). Only entries added by the bit-2 path are in node lists.
  Entry flags: floors and walls get `((cell >> 18) & 3) + 1) << 14` OR-ed in at every SetFlags, shadows
  never; bit 7 of the cell gives `0x1`. (fn:sub_0066E580_NeighbourTileScan@0x0066E580,
  fn:sub_0066E4C0_NeighbourTileFind@0x0066E4C0, fn:sub_0066B9D0_RectContainsIncl@0x0066B9D0,
  fn:sub_0066DDE0_TileEntryInit@0x0066DDE0, fn:sub_0066DEF0_RoomFloorAdd@0x0066DEF0,
  fn:sub_0066DF40_RoomShadowAdd@0x0066DF40)
- [C] `Bit2TileNew` (`0x0066E620`): for o 10/11 it needs `RectContains` (exclusive) first, else nothing.
  The room's node of the kind is found or created, then **one pick** (`0x0066E6B2`, this room); a wall of
  o 3 adds the o-4 pick, o 8/9 calls `Orient89Unit`, o 10/11 calls `WarpTileAdd`. (fn:sub_0066E620_Bit2TileNew@0x0066E620)
- `Bit2TileMerge` (`0x0066E740`, E = the neighbour N's entry, T = data:g_Bit2OrientRow@0x006EF620`[o]`). Tags
  per branch (revised 2026-10-12, backlog spec-writer → reverser (a)): `[C]` for the flag-`0x1` return, the
  cell-bit-7 path, the `T = −1` keep and the neighbour re-pick, the only branches run:2026-10-11-drlg-roomk
  reaches (6835 merges in `tools/drlg.py roomk` coverage: flag `0x1` 6481, `T = −1` with o 0 kept 310, cell bit 7
  44; 354 neighbour re-picks); `[I]` from the code for the remap through `g_Bit2OrientMerge`, the `T = −2`
  return, the o 8/9 edge tests and the orientation-3 branch (`0x0066E87C` and the partner flag), none reached
  in the run. A reimplementation of the unreached branches rests on the reading below
  (0x0066E781–0x0066E8B9). The earlier `[C]` on the whole block overstated the run.

```text
if E.flags & 1:  (E.o ∈ {8,9} → SetFlags → Orient89Unit(E));  return
if !(cell & 0x80):
  if o ∈ {8,9}:  if x = R.x or y = R.y → keep o, goto M
  elif E.o ∈ {8,9}:  if x = N.x or y = N.y → return
  if T ≥ 0 and E.o ≤ 7: o = g_Bit2OrientMerge[T·7 + E.o]
  elif T ≠ −1: return                                   ; T = −1 keeps o
M: if E.o ≠ 3 and o = 3: E.flags |= 0xC008; this room's kind-0 node; pick(R, 3) [0x0066E87C] + o-4 pick (R)
if o ≠ E.o or E is the blank floor (o 0, main 30, sub 0):
  pick(N, o, cell) [0x0066E8F7]  — ECX = N: the NEIGHBOUR's seed and DT1 list;  E.o = o, E.tile = it
SetFlags(E, cell) → E.o ∈ {8,9}: Orient89Unit(E) on this room
```

  (data:g_Bit2OrientMerge@0x006EF574; `python3 -I tools/drlg.py tables` prints both tables.)

- [I] **Merge table layout** (re-read 2026-10-12, 0x0066E747, 0x0066E7BC–0x0066E7D3). `T = [o·4 + 0x006EF620]`
  (s32, signed test `jl`); if `T ≥ 0` and `E.o ≤ 7` (signed `jg 7`), the new o is `[(T·7 + E.o)·4 + 0x006EF574]`
  (`lea [ecx·8]; sub ecx` = ×7). The row table holds, for o 0–19: `−1, 0, 1, 2, −1, 3, 4, 5, −2, −2, −1, −1,
  −1, −2, −1, −1, −1, −1, −1, −1` (it ends where the string `"%s\Tiles\Act1\…"` begins at 0x006EF670, so 20
  entries); so walls of o 1, 2, 3, 5, 6, 7 remap through rows 0–5, floors (o 0) and o 4, 10–12, 14–19 keep o,
  and o 8, 9 and 13 (shadows) never merge. The merge table, read with stride 7 and old o 0–7 (43 cells, the
  last column of a row is the first of the next): row 0 `0 1 3 3 4 1 3 1`, row 1 `1 1 2 3 4 3 2 2`, row 2
  `2 3 3 3 4 3 3 3`, row 3 `3 1 3 3 4 5 6 1`, row 4 `1 3 2 3 4 3 6 2`, row 5 `2 1 2 3 4 1 2 7`. Read from the
  file with r2 (`pxw` at both addresses).
- **Tool correction (2026-10-12).** `tools/drlg.py` read both tables (and `g_Ds1OldOrientMap`) at wrong file
  offsets: its PE section walk took `VirtualSize, VirtualAddress, SizeOfRawData, PointerToRawData` in the wrong
  order, so `tables` printed bytes of `.rdata` 0x39000 + (0x2EF620 − 0x38A10) away (the 206–255 values the
  spec-writer saw). Fixed, and the row table is now read as 20 entries. Before and after the fix:
  `roomk` 520 activations, 11208 checks, **0 mismatches**; `gen` 21153 checks, **0 mismatches** (all seven
  gen logs); every coverage line identical except the new per-branch merge counters. The wrong tables changed
  no result because no logged merge reached a table lookup (the counts above). The only `v < 7` DS1 among the
  stock files (`act1/court/court1b.ds1`, v 3) is not loaded in the runs, so the old-orientation remap was not
  exercised either.
- [I] `Orient89Unit`: looks up (level id, m, s, o == 9) in a table at `0x006EEFD0`/`0x006EF18C`. If the unit lands inside
  the room's sub-tile area and is an object (type 2) with id 91 or 92, **one `Range(3)`**: result 0
  means no unit. With a tile argument, a tile already marked `0x20` is skipped. The mark is set only when
  the table lookup hits **and** the unit lands in bounds: a miss (`0x0066DA27`) or out of bounds
  (`0x0066DA72`–`0x0066DA8E`) returns without marking. On the bit-31 orientation 8/9 path the tile
  argument is 0: no skip, no mark.
  (fn:sub_0066D9E0_Orient89Unit@0x0066D9E0)

### k as pseudocode

```text
k(R) = k_sub(R) + k_tile(R)                                     ; type 2: k_sub = 0
inputs: R.type, R.rect (+0x34..+0x40), R[+0x28] bits 12–17, level id, level type, the room's
        DT1 list (+0x68: LvlTypes File i+1 for mask bit i, then Blank/InvisWal/Warp), the grids at
        the re-seed (type 1: OutRoom grids; type 2: DS1 layers through the preset origin),
        LvlSub records and their DS1 groups, the warp record list R[+0x4C], and which neighbours
        (R[+0x08][0..R[+0x2C]-1]) have a RoomTile (+0x54 ≠ 0)

draw(o, cell) = 1 if n ≥ 1 and Σ > 0 else 0, where n, Σ = count (≤ 40) and signed rarity (+0x20) sum
                of the candidates of the primary key (o, (cell>>20)&0x3F, (cell>>8)&0xFF)
                ; (10,0,0) fallback: no draw
k_tile = Σ over RoomCellsBuild passes (builder order), rows then columns,
         Σ over the cell's picks in the order above of draw(o, cell), counting only picks on R
         (not the merge re-pick 0x0066E8F7, which draws on the neighbour)
         + 1 per Orient89Unit that reaches Range(3)
k_sub  includes the shadow picks made by LvlSub Stamp                ; type 1, at prepare time
state  carried between rooms of one act copy, in activation order: each built room's bit-2 entries
       (orientation, position, flags, tile key) and its seed, which merges change
k_sub  = the LvlSub draws above, in pass order (SubWaypoint, SubShrine, SubType), records in mask-bit order
```

- [C] The model of this section, as `tools/drlg.py roomk`, predicts every activation of
  run:2026-10-11-drlg-roomk. Inputs it takes from the log because they are run-time state: the grids at
  the first LvlSub pass (type 1, made by `drlg/outdoor`), the neighbour list and their built state, the warp
  nodes and the level's warp ids, the LvlSub groups as held in memory. The type-2 grids and the DT1 list are
  inputs too, but the checker now rebuilds both from data and requires equality (§ Type 2 prepare, the DT1
  list rule above). For type 2 the only run-time input left is the preset's file index (Phase 3).
  (fn:sub_0066EE70_DrlgRoomTypeInit@0x0066EE70)
- [I] The order matters only for the bit-2 path and LvlSub, because only they read state that earlier
  draws change: the room's own grids, and tiles already added. Every other `draw()` is a pure function of
  the cell and the DT1 list, so for the remaining cells k is a count. (fn:sub_0066FCF0_LvlSubFits@0x0066FCF0,
  fn:sub_0066FE00_LvlSubMatches@0x0066FE00, fn:sub_0066E4C0_NeighbourTileFind@0x0066E4C0)
- [C] **What Phase 2 models and what it logs (architect review).** `sub_006707A0_LvlSubApply` and
  `sub_0066E940_Bit2CellBuild` are in this row's scope, so the Phase 2 model replays them; neither is an
  oracle. The only **boundary oracle (ADR-0004)** is `sub_0066D9E0_Orient89Unit` (row `objects`, 0 or 1 draw
  per call): log the room seed in and out. (fn:sub_006707A0_LvlSubApply@0x006707A0,
  fn:sub_0066E940_Bit2CellBuild@0x0066E940, fn:sub_0066D9E0_Orient89Unit@0x0066D9E0)
  - Grids: type-1 grids do not exist yet at the re-seed. Dump them at each `0x006707A0` entry (model input)
    and at `0x0066EE70` entry (as a check).
  - Bit-2 path: no per-call breakpoint (ADR-0003 hot path). Log per activation which neighbours have
    `+0x54 ≠ 0`, and log deactivations; the model replays the builds in activation order per act copy.
  - Throughput: about 8–10 stops per room per copy, so the town, Blood Moor and maze cases go in separate
    game entries.

### Server and client

- [C] Both copies run the same window code (`RoomActivateA` and `RoomActivateB` both call reseed → type
  init → activate). The paths diverge on state, not on a client test (fn:sub_0061B190_RoomActivateA@0x0061B190,
  fn:sub_0061B730_RoomActivateB@0x0061B730):
  - the bit-2 path depends on which neighbours are already built in that act copy (`0x0066E580` scans
    `R[+0x08]`, count `R[+0x2C]`, and `0x0066E4C0` requires the neighbour's `+0x54 ≠ 0`);
  - `Orient89Unit` marks a tile `0x20` and then skips it. When the tile is a neighbour's (merge path),
    whether it has already been seen depends on order too.
  (fn:sub_0066E580_NeighbourTileScan@0x0066E580, fn:sub_0066D9E0_Orient89Unit@0x0066D9E0)
- [I] One client-only branch sits before the window: `DRLG_PresetRoomLoadDs1` calls
  `DRLG_PresetClientObjects` once per preset instance (`ps[+0x3C] == 1`, then cleared), when
  `R[+0x28] & 0x40000` (the client-act flag, rng/0002), for preset defs 1, 3, 26, 27, 28 and 300 (def 27,
  `0x1B`, takes a branch that adds units once for the whole preset). The same function, for defs 4–7 on level 2
  with file index 3 and in both copies, calls `sub_006664A0_PresetCentreMonster` instead, which adds one monster preset unit at the
  preset centre and writes no grid either (fn:sub_006664A0_PresetCentreMonster@0x006664A0). It builds a temporary view of DS1 floor layer 0
  (`sub_0067CD30_GridViewLocal`), reads cells with `sub_0067C570_GridCellGet` only, and for each cell with main
  index 2 and sub index `0x18` adds object preset units to the preset's list `ps[+0x38]` through
  `DRLG_PresetClientUnitsA`/`DRLG_PresetClientUnitsB` (`sub_0066BF30_PresetUnitCreate`, type 2).
  It writes no grid cell and draws nothing. (fn:DRLG_PresetClientObjects@0x006663C0,
  fn:DRLG_PresetClientUnitsA@0x006661A0, fn:DRLG_PresetClientUnitsB@0x00666220)
- [C] So the client copy of a preset room has the same grids as the server copy: the prepare model has no
  client branch and reproduces the logged grids of the client rooms too (Act I town rooms are def 1, where
  this branch runs). (fn:sub_006667D0_PresetRoomGridPrepare@0x006667D0)
- [I] A RoomTile is freed by `sub_0066F0B0_RoomTileFree` (`+0x54 = 0`); no free was logged in the run, so
  every built room kept its entries for its neighbours. (fn:sub_0066F0B0_RoomTileFree@0x0066F0B0)
- [I] **Release and re-activation** (static, 2026-10-12, backlog spec-writer → reverser (d)). The only callers
  of `RoomTileFree` are `sub_0066C100_RoomFree` (the level unload, drlg/0003) and
  `sub_0066F1A0_RoomTilesRelease` (0x0066F1F4), which `0x0066B4C0` calls (from `0x0061A910`) when a built room
  (`R[+0x28] & 0x100000`) is released. `RoomTilesRelease`: frees the active-room object at `R[+0x30]` unless its
  `EDX` argument is set, zeroes `R[+0x30]`, calls `0x0066C6E0`, and if bit `0x100000` is set: **clears it**,
  adds 1 to a counter at `[act+0x1B4]+0x468`, calls `RoomTileFree` (`0x0066F050` frees the three entry arrays
  `+0x14/+0x1C/+0x24`; then the node list `+0x00` and the list at `+0x04` are freed and `+0x54 = 0`), frees the
  type's grids (type 1 `sub_0067D680_OutRoomGridsFree`: the four grids of the OutRoom data and `+0x50`; type 2
  `sub_00666610_PresetRoomGridsFree` → `0x00666520`), zeroes `+0x0C` and `+0x14` of every warp node of
  `R[+0x4C]`, and ORs `0x200000` into `R[+0x28]` when its `EDX` argument is non-zero
  (0x0066F1A0–0x0066F23F). It does **not** clear `0x1000000` (DT1 list) or `0x2000000` (DS1 loaded), nor
  `R[+0x2C]` or the seed base `R[+0x04]`. So a later activation runs the whole `0x100000` block again
  (§ Activation order): the neighbour step is skipped, the room is re-seeded from the same `+0x04`, the grids
  are prepared again and the tiles rebuilt, and the activation draw follows. The room's own draws restart from
  the same seed, but k can differ from the first build, because the bit-2 lookups see whichever neighbours
  are built at that moment, and the merges the first build made into neighbours' entries (their orientation,
  tile and seed steps) are not undone; the freed room's own entries are gone from its neighbours' scans
  (`+0x54 = 0`). Not observed: no release was logged (run:2026-10-11-drlg-roomk); a run that leaves a room's
  range and returns without changing level is the test. (fn:sub_0066F1A0_RoomTilesRelease@0x0066F1A0,
  fn:sub_0067D680_OutRoomGridsFree@0x0067D680, fn:sub_00666610_PresetRoomGridsFree@0x00666610)

### RoomTile record (`R[+0x54]`, 0x2C bytes)

| offset | meaning | tag |
|---|---|---|
| `+0x00` | head of a list of 0xC-byte nodes `{kind, first, next}` added by the bit-2 path | I |
| `+0x08`, `+0x0C`, `+0x10` | wall, floor, shadow entries used | I |
| `+0x14`, `+0x1C`, `+0x24` | wall, floor, shadow entry arrays (0x30 bytes per entry) | I |
| `+0x18`, `+0x20`, `+0x28` | capacity from the count passes; **after the build, the used counts** | I |

- [I] Capacities: `CountCells` adds 1 wall per bit-0 cell, 1 floor per bit-1 or filler cell, 1 shadow per
  bit-27 cell. `CountOrient` adds 1 wall per o-3 cell, and per o-10/11 cell 1 wall (cell ≥ 0) or 6
  floors (hidden). Floor entries are added in the floor branch, by `HiddenWarpTilesAdd` and by `Bit2TileNew` (o 0).
  (fn:sub_0066ECE0_RoomTileCountCells@0x0066ECE0, fn:sub_0066EDB0_RoomTileCountOrient@0x0066EDB0,
  fn:sub_0066EEE0_RoomTileArraysAlloc@0x0066EEE0)
- [I] So `T[+0x18] = 0 && T[+0x20] = 0` (no active room, no activation draw) means that no wall and no
  floor tile was added. A room with only shadows or nothing gets none. (fn:DRLG_RoomActivate@0x006422A0)

### Entry flags in full, and the entry chains (plan 0027 Phase 2, 2026-10-15)

The backlog asked (2026-10-14, spec-writer → reverser) for the whole flag word of every tile entry, not only the bits the
k model reads: step 9d of [drlg/room-tiles](../../specs/drlg/room-tiles.md) left out the bits from cell bits 28, 17 and
16 that the collision stamp reads. The formula below is read from the four writers. `tools/drlg.py` now builds every
entry with it and compares the entry arrays of every activation dump (the `CB` lines of `tools/gdb/collision.py`).

```text
cellbits(f, cell):                                  shared tail of RoomTileSetFlags, TileEntryInit and RoomShadowAdd
  if cell & 0x80:        f |= 0x001                 ; bit 7
  if cell & 0x10000000:  f |= 0x102                 ; bit 28 (the collision stamp reads 0x002 → grid 0x10)
  if cell & 0x20000:     f |= 0x040                 ; bit 17 (→ grid 0x01)
  if cell & 0x10000:     f |= 0x080                 ; bit 16 (→ grid 0x04)
  if cell & 0x8:         f |= 0x004                 ; bit 3
  if cell & 0x80000000:  f |= 0x008  else f &= ~0x008   ; bit 31
  if cell & 0x4000000:   f |= 0x20C                 ; bit 26
  if cell & 0x20000000:  f |= 0x800                 ; bit 29
  if cell & 0x4:         f |= 0x2000                ; bit 2
  t = TILE_GetFlags16(entry tile) (tile +0x06): if t & 1: f |= 0x004;  if t & 4: f |= 0x800
layer(cell) = (((cell >> 18) & 3) + 1) << 14         ; 0x4000, 0x8000, 0xC000 or 0x10000
wall    (RoomTileAdd → RoomTileSetFlags, 0x0066DB20; o = the entry's orientation):
  if o ∈ {8, 9}: Orient89Unit(entry, x, y, cell) first (below)
  f |= (o ≠ 13 ? layer(cell) : 0); f |= (o = 14 ? 0x4 : o ∈ 8..11 ? 0x2 : 0); f = cellbits(f, cell)
  o = 3: the o-4 partner gets the same, then the caller ORs layer and cellbits again (no change)
floor   (TileEntryInit 0x0066DDE0: the floor branch, RoomFloorAdd, the hidden-warp floors): f = cellbits(layer(cell), cell)
shadow  (RoomShadowAdd 0x0066DF40): f = cellbits(0, cell)
bit-2 merge into E (Bit2TileMerge 0x0066E740, after the remap, the o-3 branch and the re-pick):
  E.flags = RoomTileSetFlags(E.flags, cell, E.o)     ; OR onto the old word; bit 3 follows cell bit 31 again
  E.flags & 1 return: only E.o ∈ {8, 9} runs RoomTileSetFlags (Orient89Unit first)
  E.o = 3 and the new o ≠ 3: (E +0x20).flags |= 0x8 (0x0066E8A7), the next entry of E's chain
  E.o ≠ 3 and o = 3: E.flags |= 0xC008 before the final RoomTileSetFlags
then
  Orient89Unit (0x0066D9E0) with an entry: skipped if the entry has 0x20; row = Orient89RowFind(level, cell main, cell sub,
    o = 9) in g_Orient89Levels / g_Orient89Rows (0x006EEFC8, 0x006EF188; −1 → nothing); the unit's subtile
    ((x − R.x)·5 + dx, (y − R.y)·5 + dy) inside R's w·5 × h·5, else nothing; then the unit (or, unit type 2 with id 91 or 92,
    the RNG_Range(R +0x14, 3) = 0 skip) and entry.flags |= 0x20
  WarpTileAdd (0x0066E260), the lit version's wall: | 0x8 (0x0066E345)
  HiddenWarpTilesAdd (0x0066E360), the four floors at (x − 1, y − 1) + g_HiddenWarpOfs[i] = (0,0) (1,0) (0,1) (1,1): | 0x8 (0x0066E45F)
  AnimTilesBuild (0x0066D440, Animate presets): the original keeps its flags and takes the rarity-0 frame's tile; each
    frame k ≥ 1 is a new entry of the same kind on the cell of the original's layer grid ((flags >> 14) & 7) − 1, | 0x8 (0x0066D6B0)
```

- [C] **Every entry of every logged dump matches.** `tools/drlg.py gen` on the 40 logs with `OD0` and `LSUB` lines
  (which also carry `TL` and `CB`) builds every room's entries and compares, at each activation dump, the wall, floor
  and shadow arrays of every near room index by index: position, orientation and flags. 12 974 activations, 44 291 room dumps (10 909 of the activating room, 33 382 of its neighbours), 3 684 791 entries (floors 2 875 733, shadows 183 136, walls of orientations 1–19), 0 mismatches. Bits from the cells: `0x2` on 490 979 entries, `0x40` on 258 219, `0x80` on 1164. 293 entries were rewritten by the bit-2 merge (the `E.flags & 1` and re-pick paths). `tools/drlg.py roomk` on the 29 logs of run:2026-10-15-objects alone: 3995 activations, 1 786 086 entries, 0 mismatches.
  (fn:sub_0066DB20_RoomTileSetFlags@0x0066DB20, fn:sub_0066DDE0_TileEntryInit@0x0066DDE0, fn:sub_0066DF40_RoomShadowAdd@0x0066DF40,
  fn:sub_0066DC50_RoomTileAdd@0x0066DC50, run:2026-10-14-collision, run:2026-10-13-mon-spawn, run:2026-10-14-mon-special,
  run:2026-10-15-mon-stats, run:2026-10-15-objects)
- [C] **Orient89Unit's `0x20`.** 912 entries got `0x20` (unit type 1: the catapults 432–435 and 524–525; type 2: objects 13–16, 60, 91, 92 and 230). In 855 calls no row was found, in 41 the unit fell outside the room (no `0x20` in either case), and 14 entries already had it. Whether the one draw (`O89D`) happens is now predicted too: 3 draws. The row table is data read from `Game.exe`. (fn:sub_0066D9E0_Orient89Unit@0x0066D9E0,
  fn:sub_0066D960_Orient89RowFind@0x0066D960, data:g_Orient89Rows@0x006EF188)
- [C] **The two tables** (backlog 2026-10-15, static dump; both in `.rdata`, data a reimplementation copies from
  `Game.exe`). `g_Orient89Levels` is 37 records of 12 bytes, `{s32 levelId, s32 firstRow, s32 lastRow}` (inclusive),
  from `0x006EEFC8`; `Orient89RowFind` stops once a record's `lastRow` field would lie past `0x006EF18B`, so the
  4-byte word at `0x006EF184` (a 38th `levelId` 0) is never a record. `g_Orient89Rows` is 34 used records of 0x1C bytes
  from `0x006EF188`, seven s32 `{main, sub, is9, unitId, unitType, dx, dy}`; the bytes after row 33 are a string and no
  range reaches them. `Orient89RowFind(levelId, cell, is9)` walks the level records in order and, for a record with
  that `levelId`, scans `firstRow..lastRow` for the first row with `main = (cell >> 20) & 0x3F`, `sub = (cell >> 8) &
  0xFF` and `is9` equal; −1 when none. `Orient89Unit` takes the level id from `R+0x58 → +0x1D0`, `is9` = (orientation
  = 9), and `dx`, `dy` in subtiles. Unit type 1 is a monster (`MONSTATS_ValidId(unitId)`, created with flag 1), type
  2 an object. Corroboration: run:2026-10-15-objects, where `tools/drlg.py` reads these exact bytes and predicts
  every `0x20` mark, every no-row call and the 3 draws. The marks it checked come from rows 0–3 (or 10, for object
  16), 19, 20, 22 and 24–33 (the unit ids in the bullet above); rows 4–9, 11–18, 21 and 23 were not reached and rest on
  the same layout and the bytes. (fn:sub_0066D960_Orient89RowFind@0x0066D960,
  fn:sub_0066D9E0_Orient89Unit@0x0066D9E0 0x0066D9E0–0x0066DAFE, data:g_Orient89Levels@0x006EEFC8,
  data:g_Orient89Rows@0x006EF188, run:2026-10-15-objects)

  | levels (id) | rows |
  |---|---|
  | 28, 29, 30, 31 | 0–3 |
  | 26, 27 | 4–6 |
  | 32, 33 | 5–9 |
  | 34, 35, 36 | 10–11 |
  | 37 | 10–12 |
  | 51 | 13–14 |
  | 52, 53, 54 | 15–18 |
  | 55, 56, 57, 58, 59, 60, 61, 66, 67, 68, 69, 70, 71, 72 | 19–20 |
  | 62, 63, 64 | 21–22 |
  | 109 | 23–24 |
  | 111, 112, 117 | 24–33 |

  | row | main | sub | is9 | unit id | type | dx | dy | | row | main | sub | is9 | unit id | type | dx | dy |
  |---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
  | 0 | 7 | 0 | 1 | 14 | 2 | 5 | 0 | | 17 | 0 | 0 | 1 | 295 | 2 | 2 | 0 |
  | 1 | 7 | 0 | 0 | 13 | 2 | 0 | 5 | | 18 | 0 | 0 | 0 | 294 | 2 | 0 | 2 |
  | 2 | 5 | 0 | 1 | 16 | 2 | 0 | 0 | | 19 | 2 | 4 | 1 | 92 | 2 | 1 | 0 |
  | 3 | 5 | 0 | 0 | 15 | 2 | 0 | 0 | | 20 | 2 | 1 | 0 | 91 | 2 | 0 | 2 |
  | 4 | 6 | 0 | 1 | 27 | 2 | 5 | −2 | | 21 | 0 | 1 | 1 | 229 | 2 | 0 | 0 |
  | 5 | 4 | 0 | 1 | 24 | 2 | 1 | 2 | | 22 | 0 | 1 | 0 | 230 | 2 | 0 | 0 |
  | 6 | 4 | 0 | 0 | 23 | 2 | 0 | 0 | | 23 | 3 | 3 | 0 | 449 | 2 | −2 | 4 |
  | 7 | 4 | 3 | 1 | 25 | 2 | 1 | 0 | | 24 | 2 | 1 | 0 | 435 | 1 | 1 | 2 |
  | 8 | 1 | 2 | 0 | 62 | 2 | 0 | 3 | | 25 | 2 | 1 | 1 | 435 | 1 | 2 | 1 |
  | 9 | 1 | 2 | 1 | 63 | 2 | 3 | 0 | | 26 | 2 | 6 | 0 | 435 | 1 | 1 | 1 |
  | 10 | 0 | 0 | 1 | 16 | 2 | 0 | 0 | | 27 | 2 | 2 | 0 | 433 | 1 | 0 | 1 |
  | 11 | 0 | 0 | 0 | 64 | 2 | 0 | 0 | | 28 | 2 | 3 | 1 | 432 | 1 | 1 | 0 |
  | 12 | 2 | 0 | 1 | 47 | 2 | 5 | 0 | | 29 | 26 | 0 | 0 | 434 | 1 | 0 | 1 |
  | 13 | 0 | 1 | 1 | 291 | 2 | 2 | 0 | | 30 | 2 | 4 | 1 | 524 | 1 | 0 | 0 |
  | 14 | 0 | 1 | 0 | 290 | 2 | 0 | 2 | | 31 | 2 | 4 | 0 | 525 | 1 | 0 | 0 |
  | 15 | 5 | 0 | 1 | 293 | 2 | 2 | 0 | | 32 | 29 | 0 | 1 | 60 | 2 | 2 | 0 |
  | 16 | 4 | 0 | 0 | 292 | 2 | 0 | 2 | | 33 | 29 | 0 | 0 | 60 | 2 | 0 | 2 |

  The ranges overlap (rows 5–6, 10–11 and 24 are reached from two level groups), and level 109's range ends on row 24,
  a type-1 row of the 111/112/117 group; the code takes them as they are.
- [C] **Animated tiles.** The frames of the Animate presets of levels 107 and 125: 383 742 frame entries in the objects logs and 3258 in the 40. Each matched the formula of its kind on its layer cell `| 0x8`, with 0 mismatches. (fn:sub_0066D440_AnimTilesBuild@0x0066D440)
- [C] **The chains.** An entry sits in one list at a time through its `+0x20` link. `WarpTileAdd` re-links a visible
  warp wall into its warp node's list (`+0x20 = node +0x0C`, `0x0066E2F2`), and `HiddenWarpTilesAdd` re-links every
  floor of the room whose tile is (main s, sub < 4) the same way (`0x0066E4A2`). The entries that followed in the
  RoomTile node's chain are then out of reach of `NeighbourTileFind`, so a later neighbour builds a new entry instead
  of merging. Seen in `monstats-s5` (level 53, a Palace Cellar 3 preset room): a level-53 warp wall (o 11) cut five
  older walls off its node, and the left neighbour then made its own wall at (8, 0) (`0x0066E620`). The model keeps
  real chains since. 28 such cuts in the logs (23 in the 40, 5 in the objects logs). (fn:sub_0066E260_WarpTileAdd@0x0066E260, fn:sub_0066E4C0_NeighbourTileFind@0x0066E4C0)
- [I] Bits that are not the build's and are not compared: `0x20000` and `0x40000`, which neighbours' entries carry at a
  later room's dump but never at their own room's (159 694 entries in the 40 logs; the writer is not in the build code),
  and the `0x8` of an animated tile, which the animation toggles to show one frame (19 632 entries in the objects logs).
  (fn:sub_0066D440_AnimTilesBuild@0x0066D440, run:2026-10-14-collision, run:2026-10-15-objects)
- [I] Not reached: a merge into orientation 3 or from orientation 3 (the `0xC008` and the next-entry `0x8`), an
  animated wall or shadow (the shadow frame reads floor layer 1, index −1 below the shadow grid), and `Orient89Unit`'s
  draw skip (unit type 2, ids 91/92) with result 0. The hidden-warp floors were reached (524 entries, compared, `[C]`).
  (fn:sub_0066E740_Bit2TileMerge@0x0066E740, fn:sub_0066E360_HiddenWarpTilesAdd@0x0066E360, fn:sub_0066D9E0_Orient89Unit@0x0066D9E0)

## Draw-site placement

| Site (drlg/0001) | Where it runs | Window | Seed | Draws | Tag |
|---|---|---|---|---|---|
| `0x0066E940` bit-2 path | tile build | in | room `+0x14` | new: 1 (+1 o 3, +1 warp); merge: 0, or 2 (o → 3) on R | C |
| `0x0066D9E0` orientation 8/9 | tile build, hidden, wall and merge paths | in | room `+0x14` | 0–1 `Range(3)` (call `0x0066DAC1`); oracle | C entry seed (526 calls); I the draw (never reached) |
| `0x0066E1C0` | 10/11 paths | in | — | no draw (unit only) | C |
| `0x0066E360` hidden 10/11 | tile build | in | room `+0x14` | 0 or 4 picks, orientation 0 | C |
| `0x0066E260` visible 10/11 | tile build | in | room `+0x14` | 0–1 pick | C |
| `0x0066E073` | LvlSub `Stamp`, type 1 prepare | in | room `+0x14` | 1 pick per stamped shadow cell | C |
| `0x0066E31B` | in `0x0066E260` | in | room `+0x14` | 0–1 pick | C |
| `0x0066E3FB` | in `0x0066E360` | in | room `+0x14` | 4 picks | C |
| `0x0066E6B2` | in `0x0066E620` | in | room `+0x14` | 1 pick | C |
| `0x0066E87C` | in `0x0066E740` | in | room `+0x14` | 0–1 pick (+ the o-4 partner pick); never reached in the run | I |
| `0x0066E8F7` | in `0x0066E740` | in (time) | **the neighbour's** `+0x14` | 0–1 pick, not in this room's k | C |
| `0x0066B980` filler test | tile build | in | — | no draw (rect test) | C |
| `0x0066FF50` / `0x00670170` | type 1 prepare via `0x006707A0` | in | room `+0x14` | k_sub (`0x0066FF50` never reached with stock data) | C / I |
| `0x00667620` | `PresetRoomLoadDs1` before the re-seed; `PresetMapScan` at room creation | **out** | room `+0x14` (discarded) | keep/drop rolls | I |
| `0x006706A0` | `sub_0067D540_OutRoomCreate`, room creation | **out** | room `+0x14` (before the re-seed) | one `% 100` per SubType record | C (mask), I (draw) |

## Plan 0038 batch H5c (run:2026-10-16-sweep-roomk, in progress)

Sessions 1–5 of [experiments.md § run:2026-10-16-sweep-roomk](experiments.md#run2026-10-16-sweep-roomk); the checks are `tools/drlg.py roomk` / `gen` (`h5c_event`, `h5c_ract`), 0 mismatches over
1456 activations. Rows of [inventory drlg-room-tiles](../../plans/0038-inventory/drlg-room-tiles.md) and drlg-README.

- [C] **RoomTileFree** runs for every built room that `RoomTilesRelease` releases (1133, RTFREE between RTR0 and RTR1)
  and for the built rooms of a level unload through `RoomFree` (48). (fn:sub_0066F0B0_RoomTileFree@0x0066F0B0, run:2026-10-16-sweep-roomk)
- [C] **Release.** On a built room `RoomTilesRelease` clears `0x100000`, adds 1 to `[act+0x468]`, leaves `+0x54 = 0`,
  zeroes `+0x0C`/`+0x14` of every warp node (22 rooms with nodes), keeps `0x1000000`, `0x2000000`, `+0x2C` and `+0x04`,
  zeroes `+0x30`, and sets `0x200000` iff `EDX` ≠ 0 (437 of 1133): 1133 releases, each compared field by field. On an
  unbuilt room it only zeroes `+0x30` (369). Every built-room release came through the wrapper `0x0066B4C0`, which first
  writes `+0x60` = the active room's flags bit 0. Correction to the static reading: the call nests. A release with
  `EDX` 0 frees the active room (`0x0061A910`), whose wrapper calls `RoomTilesRelease` again on the same room with
  `EDX` = (DUNGEON act `+0x50` = 0); the outer call then finds `0x100000` clear and changes nothing more (696 nested
  pairs). (fn:sub_0066F1A0_RoomTilesRelease@0x0066F1A0, 0x0066B4C0, 0x0061A9D7, run:2026-10-16-sweep-roomk)
- [C] **Re-activation.** 185 released rooms were activated again: same `+0x04` and level, `0x1000000`/`0x2000000`
  still set, re-seeded from `+0x04`, grids and tiles rebuilt as the k model predicts. k equalled the first build's in
  153 and differed in 32 (the bit-2 path sees other built neighbours). (fn:sub_0061B730_RoomActivateB@0x0061B730,
  fn:sub_0066E580_NeighbourTileScan@0x0066E580, run:2026-10-16-sweep-roomk)
- [C] **Neighbours keep the first build's merges.** 1887 entries of near rooms, last rewritten by a bit-2 merge of a
  room that was released afterwards, were compared at later activation dumps (position, orientation, flags): all as the
  model that never undoes a merge. (fn:sub_0066E740_Bit2TileMerge@0x0066E740, run:2026-10-16-sweep-roomk)
- [C] **Level exceptions.** A hidden orientation-8/9 cell is built as a wall (not the oracle-only return) in levels 111
  (51 cells), 112 (4) and 117 (57), and every such room matched. (fn:sub_0066E9B0_RoomCellBuild@0x0066E9B0, run:2026-10-16-sweep-roomk)
  Level 74's filler key and level 133's warps are not reached yet (133 is unreachable).
- [C] **Outdoor mask** of level type 31 (`0x11`): 145 type-1 rooms in levels 111, 112, 117, with the SubType masks
  ORed. (fn:sub_006750F0_OutdoorRoomsCreate@0x006750F0, run:2026-10-16-sweep-roomk) Types 16 and 21 are checked on run:2026-10-14-collision
  (40 and 20 rooms, same checker); 22, 27, 28 and 30 are not reached yet.
- [C] **RoomTile counts.** At every activation `T[+0x18]`/`T[+0x20]` equal the model's wall and floor entries (1453)
  or exceed them by animated-tile frames (3 rooms). (fn:DRLG_RoomActivate@0x006422A0, run:2026-10-16-sweep-roomk)
- Not reached yet in this batch: a merge into or out of orientation 3, an Orient89Unit draw (rows of unit type 2,
  ids 91/92, levels 55–61 and 66–72: the O89R/O89U lines and the `Range(3)` = 0 case wait for a tomb session).

## Data touched

- tbl:LvlPrest.txt:KillEdge (`+0x18`), tbl:LvlPrest.txt:FillBlanks (`+0x1C`), tbl:LvlPrest.txt:Animate
  (`+0x14`), tbl:LvlPrest.txt:Def (`+0x00`), tbl:LvlPrest.txt:Dt1Mask (`+0x1AC`).
- tbl:LvlTypes.txt:File 1 (`File i+1` at `+0x3C·i`, by the room mask), tbl:LvlSub.txt:Dt1Mask (`+0x48`) and
  tbl:LvlSub.txt:Prob0 (`+0x11C`) in `sub_006706A0_LvlSubRoll`, tbl:Levels.txt:SubType and tbl:Levels.txt:SubTheme
  (leveldefs `+0x38`, `+0x3C`).
- tbl:Levels.txt:SubWaypoint (leveldefs `+0x40`), tbl:Levels.txt:SubShrine (leveldefs `+0x44`), the warp
  ids at leveldefs `+0x68` (8 × s32; the column names are the archivist's to confirm).
- `LvlWarp` (`lvlwarp.bin`, 0x30-byte records, no table doc yet): `+0x00` Id, `+0x1C`/`+0x20` OffsetX/Y,
  `+0x24` LitVersion, `+0x28` Tiles, `+0x2C` Direction (char), by the code's reads and the `.txt` column
  order; backlog → archivist.
- `LvlSub` (table doc docs/tables/LvlSub.md, archivist, on another branch): record 0x15C, offsets checked against `lvlsub.bin` (34 records, all match):
  `+0x00` Type, `+0x04` File char[60], `+0x40` CheckAll, `+0x44` BordType, `+0x48` Dt1Mask,
  `+0x4C` GridSize, `+0x11C` Prob0..4, `+0x130` Trials0..4, `+0x144` Max0..4, `+0x158` Expansion; `+0x50`
  is the DS1 record pointer at run time. The code uses `Type`, `File`, `CheckAll`, `Prob`, `Trials`, `Max`.
  All 34 stock records have `CheckAll = 0`; 11 have `Trials0 = −1`.
- DS1 record `[0]` tag_type, `[19]` group count, `[20]` groups (drlg/0001 § `DS1_Parse`).
- OutRoom `+0x64`, `+0x68`, `+0x6C` (SubType record, theme, mask); room `+0x28` bits 12–17; level type `+0x1C0`.

## Dead ends

- `0x00667620` looked like the preset file pick (drlg/0001); it is the per-unit keep/drop roll and runs before
  the re-seed.
- The first call-graph run reported 4 RNG functions with 64 unresolved indirect calls. The grid-op table
  had to be added as a root (`table@0x00749BAC:6`) before the result could count as complete.

## Open questions

- **`Trees.ds1` read past its end** (LvlSub record 11, Act I outdoor levels): the last group's y, w, h are
  heap bytes. 26 of 27 loads held zeros, one held garbage. A reimplementation has to choose (zeros match
  every draw seen). Owner: `drlg/overview` spec (Phase 4) to state it; the archivist's ds1.md already lists
  the file as malformed.
- `Orient89Unit`'s `Range(3)` (objects 91/92) was never reached in the run (526 oracle calls, 0 draws), so
  its draw is `[I]` from the code; it stays an oracle (row `objects`). Update 2026-10-15 (plan 0027 Phase 2): the 40
  logs of § Entry flags reach it 3 times and the model now predicts when it happens; the unit creation stays the oracle.
- The `(10,0,0)` fallback (no draw) and the ApplyAll path (`CheckAll ≠ 0`) were not exercised; both `[I]`.
- ~~Type-2 grids are a logged input~~ Settled 2026-10-12 (fix F1): the prepare is modelled and reproduces every
  logged type-2 grid (§ Type 2 prepare). The `0x84` write lands in a DS1 buffer that all preset instances and
  both act copies share, but no grid in the run shows it. A case that could show it needs a cell that is
  a border of one view and interior to another view of the same file, which no logged preset has. Whether
  any shipped preset has one (rooms of one preset split along different lines, or one file in two LvlPrest
  records of different splits) is for `drlg/preset`, together with how a preset is split into rooms.
- `0x00667620` semantics and its callers outside activation (`0x00667970` at room creation, `0x0061B210+0x133`,
  first-load-only via `preset[+0xC]`): which room's seed it steps and what it keeps. Owner: Phase 3 / `drlg/preset`.
  **Answered** in [drlg/0004](0004-preset-units.md) (`0x0061B210+0x133` is `0x0061B343` in `RoomPrepareFiles`), along with
  the `0x84` question: no shipped DS1 is cut two ways.
- ~~`0x006663C0` (client-only, pre-window): does it change the grids k reads?~~ No (§ Server and client): it
  only adds object preset units. Which objects (ids `0x28`–`0x2A`, `0x41`) and where they go is row `objects`.
  `0x0066C370` (pre-window neighbour creation): the neighbour lists are logged inputs (generators, Phase 3).
- What `0x0067C460` (grid op 4) does; it is not used on the paths read here.
- The orientation-8/9 unit table (`0x006EEFD0`) is not dumped (the oracle stands in for it). The merge
  tables are read from `Game.exe` by `tools/drlg.py tables` (offsets fixed 2026-10-12).
- **The bit-2 remap and orientation-3 merge branches are unexercised** (2026-10-12). A run that reaches them
  needs two built rooms whose shared border cells hold walls of o 1–3 or 5–7 without bit 7 on the newer
  room's cell and without flag `0x1` on the older entry. Type-2 borders carry bit 7 (`0x84`, § Type 2 prepare),
  so preset-to-preset wall merges end at flag `0x1`; type-1 borders get bit 2 only, so wall merges between
  outdoor rooms (the 6 roomk logs have one outdoor level, the Blood Moor) are where to look. Owner: a future
  `drlg/outdoor` run.
- Objects 91 and 92 in `Orient89Unit`: which objects these are (row `objects`).
- `LvlSub` table doc: the archivist's docs/tables/LvlSub.md (on another branch: 34×22 cells, 0 mismatches,
  `Dt1Mask`/`GridSize` swap confirmed) merges with this one.
