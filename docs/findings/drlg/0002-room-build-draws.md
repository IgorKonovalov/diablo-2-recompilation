# 0002 — Room-build draws: the k window and a static k model

> **Subsystem:** drlg/overview (feeds rng/seeds step 6, drlg/outdoor, drlg/preset)
> **Question:** Which code steps the DRLG room seed `+0x14` between the re-seed and the activation draw, and how many times (k), as a function of the room's data?
> **Date:** 2026-10-11   **Plan:** 0008 (Phase 1)   **Status:** open (static; Phase 2 runs the check)

The k window is the code between `sub_0066EE40_DrlgRoomReseed` (seed `+0x14 = init(+0x04)`) and the
inlined step in `DRLG_RoomActivate` (rng/0002 § Active room). This finding enumerates it with a
recorded script, places every open draw site of drlg/0001, and writes k as pseudocode.

## Answer (summary)

- [I] **Completeness.** `RngCallGraph.java` walks the direct-call graph under `0x0067D2D0`, `0x0067D710`,
  `0x006667D0`, `0x00666AC0` plus the six grid-op stubs of data:g_GridOps@0x00749BAC: 657 functions,
  **4 draw from an RNG, all on the DRLG room seed `+0x14`**, 0 unclassified. They are
  `DRLG_PickTileByRarity`, `sub_0066D9E0_Orient89Unit`, `sub_0066FF50_LvlSubApplyAll` and
  `sub_00670170_LvlSubApplyPick`. (fn:DRLG_PickTileByRarity@0x0066D820, fn:sub_0066D9E0_Orient89Unit@0x0066D9E0,
  fn:sub_0066FF50_LvlSubApplyAll@0x0066FF50, fn:sub_00670170_LvlSubApplyPick@0x00670170)
- [I] **Two kinds of draw make up k.** For type 1 (outdoor) rooms, the grid prepare `0x0067D2D0` first
  applies **`LvlSub` substitutions** with draws on the room seed (k_sub). Then both room types build tiles,
  with one rarity draw per tile pick whose candidate rarity sum is > 0, plus a rare `Range(3)` for
  two orientation-8/9 object units (k_tile). Type 2 (preset) rooms have no k_sub: their prepare
  `0x006667D0` makes no draw. (fn:sub_0067D2D0_OutRoomGridPrepare@0x0067D2D0, fn:sub_006667D0_PresetRoomGridPrepare@0x006667D0)
- [I] **`0x00667620` is outside the window.** It steps room `+0x14` (preset-unit keep/drop rolls), but
  `sub_0061B730_RoomActivateB` and `sub_0061B320_RoomPrepareFiles` call it through
  `sub_00667890_PresetRoomLoadDs1` **before** the re-seed, which discards those draws. The DS1 file index
  is already stored when that runs: **the preset file pick is not a room-seed draw in the window**, so it
  stays with Phase 3. (fn:sub_0061B730_RoomActivateB@0x0061B730, fn:sub_00667890_PresetRoomLoadDs1@0x00667890,
  fn:sub_00667620_PresetUnitDropRolls@0x00667620)
- [I] Every other open site of drlg/0001 is **inside** the window and draws only through
  `DRLG_PickTileByRarity` or `sub_0066D9E0_Orient89Unit` (table in § Draw-site placement).
  (fn:sub_0066E9B0_RoomCellBuild@0x0066E9B0, fn:sub_0066E940_Bit2CellBuild@0x0066E940)
- [I] **Server and client k can differ** because the bit-2 path (`0x0066E940`) looks for an existing tile
  at the same cell in the room's **neighbour rooms that are already built** (`+0x54 ≠ 0`). Which
  neighbours are built depends on activation order in that act copy, and the two branches make different
  numbers of picks. (fn:sub_0066E580_NeighbourTileScan@0x0066E580, fn:sub_0066E4C0_NeighbourTileFind@0x0066E4C0)
- [I] **RoomTile `T[+0x18]`/`T[+0x20]`** are the wall and floor tile **counts** at the end of the build:
  the builder copies the used counters `T[+0x08]`/`T[+0x0C]` over the capacities. So `DRLG_RoomActivate`
  draws once more iff the room got at least one wall or floor tile. (fn:sub_0067D710_OutRoomTilesBuild@0x0067D710,
  fn:sub_00666AC0_PresetRoomTilesBuild@0x00666AC0)
- [I] **Maze rooms' `+0x50` mask** is the `LvlPrest` `Dt1Mask` of the room's preset, like other preset rooms.
  The maze code `0x00673A60` turns its rooms into DRLG rooms through `sub_00667ED0_PresetRoomsCreate`,
  which writes `+0x50` (drlg/0001 § Third pass). (fn:sub_00673A60_MazeLevelRooms@0x00673A60,
  fn:sub_00667ED0_PresetRoomsCreate@0x00667ED0)

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
| `0x00666710` | `sub_00666710_PresetUnitsToRoom` | move the preset's units inside the room to the room (no draw) | I |
| `0x006667D0` | `sub_006667D0_PresetRoomGridPrepare` | type 2 prepare: grids from DS1 layers (no draw) | I |
| `0x00667620` | `sub_00667620_PresetUnitDropRolls` | pre-window keep/drop rolls on room `+0x14` for some preset units | I |
| `0x00673A60` | `sub_00673A60_MazeLevelRooms` | maze code that calls `sub_00667ED0_PresetRoomsCreate` | I |
| `0x0067D2D0` | `sub_0067D2D0_OutRoomGridPrepare` | type 1 prepare: grids, three `LvlSub` passes, theme fill | I |

| Address | Global | Role | Tag |
|---|---|---|---|
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
- [I] `sub_00667890_PresetRoomLoadDs1` opens `LvlPrest + 0x44 + i·0x3C` with `i` read from the preset
  record (`piVar[1]`); it draws nothing to choose `i`. `0x00667620` walks the DS1's preset units:
  monsters with ids `0xCC`, `0xCD`, `0x173`, `0x174` are kept on `step % 3 == 0`, some
  SuperUnique/object ids on a parity or `& 3` test. That belongs to `drlg/preset`.
  (fn:sub_00667620_PresetUnitDropRolls@0x00667620)

### Type 1 prepare: the `LvlSub` passes (k_sub)

```c
// fn:sub_0067D2D0_OutRoomGridPrepare@0x0067D2D0 (trimmed). OR = the 0x70-byte OutRoom (R[+0x20]), D = leveldefs record
grids_init(); 8×8 grid op set(0x40002); if (act(level) == 0) 0x00680C80();   // no draws
RoomTileAlloc(R);
p = {room: R, outroom: OR, ..., type, theme, mask};
if (m = (R[+0x28] >> 16) & 3) LvlSubApply(p{type: D.SubWaypoint /*+0x40*/, theme: 0, mask: m});
if (m = (R[+0x28] >> 12) & 0xF) LvlSubApply(p{type: D.SubShrine /*+0x44*/, theme: 0, mask: m});
LvlSubApply(p{type: OR[+0x64], theme: OR[+0x68], mask: OR[+0x6C]});
theme-fill cells whose bits 0x3F0FF80 are clear, by level type (no draw)

// fn:sub_006707A0_LvlSubApply@0x006707A0
if (p.type == -1) return;
rec = LVLSUB_GetRecordByType(p.type);                   // 0x15C-byte records
for (m = p.mask; m; m >>= 1, rec++)                     // bit i = i-th record of that Type
  if (m & 1) { LvlSubLoadDs1(rec); rec.CheckAll ? LvlSubApplyAll(p, rec) : LvlSubApplyPick(p, rec); }
```

- [I] Draws, with `Range(n)` = `RNG_Range` semantics inlined (n < 1 → 0 with no draw; power of two →
  mask; else `low % n`), all on room `+0x14` (fn:sub_0066FF50_LvlSubApplyAll@0x0066FF50,
  fn:sub_00670170_LvlSubApplyPick@0x00670170):

```c
// CheckAll != 0. G = the record's DS1 groups (DS1 [19] count, [20] 0x18-byte {x,y,w,h,_,unk})
for g in G:                                    // in DS1 order
  W = R.w(+0x3C) - g.w + 1;  H = R.h(+0x40) - g.h + 1;  if (W <= 0 || H <= 0) continue;
  if (ds1.tag_type == 1)
    for y in 1..H-1: for x in 1..W-1: if Fits(x,y) Stamp(x,y,0)          // no draw
  else if (ds1.tag_type == 2)
    for y in 0..H-1: for x in 0..W-1:
      if Matches(x,y):
        r = step(seed).low % 100;                                       // draw (always one step)
        if (rec.Prob[theme] < r) { v = Range(g.unk); Stamp(x,y,(g.w+1)*(v+1)); }

// CheckAll == 0
if (G.count == 0 || rec.Max[theme] < 1) return;
repeat rec.Max[theme] times:
  g = G[Range(G.count)];
  dx = R.w - g.w;  dy = R.h - g.h;
  if (dx + 1 > 1 && dy + 1 > 1)
    if (rec.Trials[theme] == -1) {
      n = dx*dy;  list = [(i % dx, i / dx) for i < n];
      repeat n times: a = Range(n); b = Range(n); swap(list[a], list[b]);   // 2n draws
      first (x,y) in list with Fits(x+1, y+1) → Stamp
    } else
      repeat rec.Trials[theme] times: x = Range(dx)+1; y = Range(dy)+1; if Fits(x,y) { Stamp; break; }
```

- [I] k_sub depends on the grid contents through `Fits`/`Matches`, which read the room's grids as the
  earlier passes left them. `Stamp` (`0x0066FAD0`) also picks a tile for every stamped shadow cell
  (bit 27) at `0x0066E073` (`sub_0066E060_ShadowTileAdd`, orientation 13), **inside** the prepare.
  (fn:sub_0066FAD0_LvlSubStamp@0x0066FAD0, fn:sub_0066E060_ShadowTileAdd@0x0066E060)

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
  and **pick** = one `DRLG_PickTileByRarity`, which draws iff the summed rarity of its candidates is > 0
  (drlg/0001). Write `Σ(o,m,s)` for that sum over the room's DT1 list (falling back to key (10,0,0) when
  the key has no tile). (fn:sub_0066E9B0_RoomCellBuild@0x0066E9B0, fn:sub_0066DC50_RoomTileAdd@0x0066DC50,
  fn:sub_0066DB20_RoomTileSetFlags@0x0066DB20)

```text
if o ∈ {10,11} and m ≥ 8: nothing
if o == 0 and m == 30 and s ∈ {0,1}: cell |= 0x80000000
if cell bit 31:
  o ∈ {8,9}, level ∉ {111,112,117}: Orient89Unit(cell)                   → 0 or 1 Range(3); stop
  o ∈ {10,11}:  WarpUnitAdd; HiddenWarpTilesAdd: if the room's warp record (R[+0x4C] list) has +0x24 ≠ 0:
                4 picks, keys (o, s, 4..7)                                 ; stop
if cell bit 2:
  kind = bit 1 → floor (o 0) | bit 0 → wall (o) | bit 27 and not bit 31 → shadow (o 13) | else fall through
  Bit2CellBuild: neighbour tile found (built neighbours only) → Bit2TileMerge, else Bit2TileNew; stop
floor:  bit 1 → pick(0, cell)
        else if filler and RectContains(R.rect, x, y) → pick(0, 0x1E00000 | (level 74 ? 0x100 : 0))
wall:   bit 0 → pick(o, cell); AddWall: o == 3 → pick(4, cell) [0x0066DD02];
                o ∈ {8,9} → Orient89Unit(tile);  o ∈ {10,11}, level ≠ 133 → WarpTileAdd
shadow: bit 27 → pick(13, cell)
```

- [I] `WarpTileAdd` (`0x0066E260`): finds the room's warp record for this level (fatal if none). If
  `s ∉ {0,4}`, or `WarpUnitAdd` succeeds, and the record's `+0x24 ≠ 0`: **one pick** (`0x0066E31B`) of
  `cell | rec[+0x28] << 8`. (fn:sub_0066E260_WarpTileAdd@0x0066E260)
- [I] `Bit2TileNew` (`0x0066E620`): for o 10/11 it needs `RectContains` first, else nothing. Then
  **one pick** (`0x0066E6B2`); a wall of o 3 adds the o-4 pick, o 8/9 calls `Orient89Unit`, o 10/11 calls
  `WarpTileAdd`. (fn:sub_0066E620_Bit2TileNew@0x0066E620)
- [I] `Bit2TileMerge` (`0x0066E740`) works on the **neighbour's** tile. If that tile's flag bit 0 is set:
  no pick. Otherwise the new orientation may be remapped through the tables at `0x006EF620`/`0x006EF574`
  (an unmapped pair returns with no pick). If the new o is 3 and the old is not, **one pick**
  (`0x0066E87C`) plus the o-4 pick. If o changed, or the old tile is the blank floor (0,30,0),
  **one pick** (`0x0066E8F7`). (fn:sub_0066E740_Bit2TileMerge@0x0066E740)
- [I] `Orient89Unit`: looks up (level id, m, s, o == 9) in a table at `0x006EEFD0`/`0x006EF18C`. If the unit lands inside
  the room's sub-tile area and is an object (type 2) with id 91 or 92, **one `Range(3)`**: result 0
  means no unit. A tile already marked `0x20` is skipped, and it is marked after.
  (fn:sub_0066D9E0_Orient89Unit@0x0066D9E0)

### k as pseudocode

```text
k(R) = k_sub(R) + k_tile(R)                                     ; type 2: k_sub = 0
inputs: R.type, R.rect (+0x34..+0x40), R[+0x28] bits 12–17, level id, level type, the room's
        DT1 list (+0x68: LvlTypes File i+1 for mask bit i, then Blank/InvisWal/Warp), the grids at
        the re-seed (type 1: OutRoom grids; type 2: DS1 layers through the preset origin),
        LvlSub records and their DS1 groups, the warp record list R[+0x4C], and which neighbours
        (R[+0x08][0..R[+0x2C]-1]) have a RoomTile (+0x54 ≠ 0)

draw(o, cell) = 1 if Σ(o, (cell>>20)&0x3F, (cell>>8)&0xFF) > 0 else 0    ; signed sum of tile +0x20
k_tile = Σ over RoomCellsBuild passes (builder order), rows then columns,
         Σ over the cell's picks in the order above of draw(o, cell)
         + 1 per Orient89Unit that reaches Range(3)
         + the shadow picks made by LvlSub Stamp            ; type 1, counted at prepare time
k_sub  = the LvlSub draws above, in pass order (SubWaypoint, SubShrine, SubType), records in mask-bit order
```

- [I] The order matters only for the bit-2 path and LvlSub, because only they read state that earlier
  draws change: the room's own grids, and tiles already added. Every other `draw()` is a pure function of
  the cell and the DT1 list, so for the remaining cells k is a count. (fn:sub_0066FCF0_LvlSubFits@0x0066FCF0,
  fn:sub_0066FE00_LvlSubMatches@0x0066FE00, fn:sub_0066E4C0_NeighbourTileFind@0x0066E4C0)
- [I] **Boundary oracles for Phase 2 (ADR-0004).** These callees draw on `+0x14` inside the window but belong
  to other rows. Log the room seed at entry and exit of each (fn:sub_006707A0_LvlSubApply@0x006707A0,
  fn:sub_0066D9E0_Orient89Unit@0x0066D9E0, fn:sub_0066E940_Bit2CellBuild@0x0066E940):
  1. `sub_006707A0_LvlSubApply` (row `drlg/outdoor` / `drlg/preset`: substitutions), once per pass. Its
     exit seed minus its entry seed is k_sub for that pass, including `Stamp`'s shadow picks.
  2. `sub_0066D9E0_Orient89Unit` (row `objects`): 0 or 1 draw per call.
  3. `sub_0066E940_Bit2CellBuild` (neighbour-dependent): log per call the return of `0x0066E580`
     (neighbour hit or not) as well as entry/exit seed. The architect may judge it too frequent under the
     ADR-0003 throughput limit. If so, log per activation which neighbours have `+0x54 ≠ 0` instead.

### Server and client

- [I] Both copies run the same window code (`RoomActivateA` and `RoomActivateB` both call reseed → type
  init → activate). The paths diverge on state, not on a client test (fn:sub_0061B190_RoomActivateA@0x0061B190,
  fn:sub_0061B730_RoomActivateB@0x0061B730):
  - the bit-2 path depends on which neighbours are already built in that act copy (`0x0066E580` scans
    `R[+0x08]`, count `R[+0x2C]`, and `0x0066E4C0` requires the neighbour's `+0x54 ≠ 0`);
  - `Orient89Unit` marks a tile `0x20` and then skips it. When the tile is a neighbour's (merge path),
    whether it has already been seen depends on order too.
  (fn:sub_0066E580_NeighbourTileScan@0x0066E580, fn:sub_0066D9E0_Orient89Unit@0x0066D9E0)
- [I] One client-only branch sits before the window: `sub_00667890_PresetRoomLoadDs1` calls `0x006663C0`
  only when `R[+0x28] & 0x40000` (the client-act flag, rng/0002), for some preset defs. Whether it
  changes the grids that k reads is not read (Open questions). (fn:sub_00667890_PresetRoomLoadDs1@0x00667890)

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

## Draw-site placement

| Site (drlg/0001) | Where it runs | Window | Seed | Draws | Tag |
|---|---|---|---|---|---|
| `0x0066E940` bit-2 path | tile build | in | room `+0x14` | 0–3 picks (new: 1 (+1 o 3, +1 warp); merge: 0–3) | I |
| `0x0066D9E0` orientation 8/9 | tile build, both hidden and wall paths | in | room `+0x14` | 0–1 `Range(3)` | I |
| `0x0066E1C0` | 10/11 paths | in | — | no draw (unit only) | I |
| `0x0066E360` hidden 10/11 | tile build | in | room `+0x14` | 0 or 4 picks | I |
| `0x0066E260` visible 10/11 | tile build | in | room `+0x14` | 0–1 pick | I |
| `0x0066E073` | LvlSub `Stamp`, type 1 prepare | in | room `+0x14` | 1 pick per stamped shadow cell | I |
| `0x0066E31B` | in `0x0066E260` | in | room `+0x14` | 0–1 pick | I |
| `0x0066E3FB` | in `0x0066E360` | in | room `+0x14` | 4 picks | I |
| `0x0066E6B2` | in `0x0066E620` | in | room `+0x14` | 1 pick | I |
| `0x0066E8F7` (and `0x0066E87C`) | in `0x0066E740` | in | room `+0x14` | 0–1 pick each | I |
| `0x0066B980` filler test | tile build | in | — | no draw (rect test) | I |
| `0x0066FF50` / `0x00670170` | type 1 prepare via `0x006707A0` | in | room `+0x14` | k_sub | I |
| `0x00667620` | `PresetRoomLoadDs1`, before the re-seed | **out** | room `+0x14` (discarded) | keep/drop rolls | I |

## Data touched

- tbl:LvlPrest.txt:KillEdge (`+0x18`), tbl:LvlPrest.txt:FillBlanks (`+0x1C`), tbl:LvlPrest.txt:Animate
  (`+0x14`), tbl:LvlPrest.txt:Def (`+0x00`), tbl:LvlPrest.txt:Dt1Mask (`+0x1AC`).
- tbl:Levels.txt:SubWaypoint (leveldefs `+0x40`), tbl:Levels.txt:SubShrine (leveldefs `+0x44`).
- `LvlSub` (no table doc): record 0x15C, offsets checked against `lvlsub.bin` (34 records, all match):
  `+0x00` Type, `+0x04` File char[60], `+0x40` CheckAll, `+0x44` BordType, `+0x48` Dt1Mask,
  `+0x4C` GridSize, `+0x11C` Prob0..4, `+0x130` Trials0..4, `+0x144` Max0..4, `+0x158` Expansion; `+0x50`
  is the DS1 record pointer at run time. The code uses `Type`, `File`, `CheckAll`, `Prob`, `Trials`, `Max`.
- DS1 record `[0]` tag_type, `[19]` group count, `[20]` groups (drlg/0001 § `DS1_Parse`).
- OutRoom `+0x64`, `+0x68`, `+0x6C` (SubType record, theme, mask); room `+0x28` bits 12–17; level type `+0x1C0`.

## Dead ends

- `0x00667620` looked like the preset file pick (drlg/0001); it is the per-unit keep/drop roll and runs before
  the re-seed.
- The first call-graph run reported 4 RNG functions with 64 unresolved indirect calls. The grid-op table
  had to be added as a root (`table@0x00749BAC:6`) before the result could count as complete.

## Open questions

- k is static (tagged I). Phase 2 checks it against logged activations with the three oracles above.
- `0x006663C0` (client-only, pre-window) and `0x0066C370` (pre-window neighbour creation): do they change
  the grids or the neighbour state that k reads? Resolve with the Phase 2 run (server vs client k per room).
- What `0x0067C460` (grid op 4) does; it is not used on the paths read here.
- The orientation-8/9 unit table (`0x006EEFD0`) and the merge tables (`0x006EF620`, `0x006EF574`) are not
  dumped. A model has to read them from `Game.exe` (a Phase 2 tool task).
- Objects 91 and 92 in `Orient89Unit`: which objects these are (row `objects`).
- `LvlSub` has no table doc; backlog to the archivist.
