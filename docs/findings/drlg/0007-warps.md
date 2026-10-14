# 0007 — Level links, warp slots and the warp points

> **Subsystem:** drlg/warps
> **Question:** How does every level get its links to other levels: what the act link builder draws and writes, how `Vis` and `Warp` slots pair, which room of a level holds the warp to which neighbour, and which points end up in `level+0x1E0`?
> **Date:** 2026-10-14   **Plan:** 0022 (Phase 1, 1b)   **Status:** open (static reading)

Static reading (decompile plus disassembly for the register arguments) of the act link builder `0x006772C0` and its
callbacks, of the per-level link override list at act `+0x90`, of the warp-slot plumbing between preset DS1 cells,
room flags and destination levels, and of the two post-build passes of `LevelInit`. Maze-specific placement is in
[drlg/0006](0006-maze.md). Nothing here was run in this phase: every claim is `[I]` unless it cites a run.

## Answer (summary)

- [I] **A warp's neighbour is chosen by slot, and the slot comes from the DS1.** A DS1 cell of orientation 10 or 11
  carries a slot `m` = bits 20–25. When `DRLG_PresetMapScan` scans an instance (`Scan` set), a slot `m < 8` sets room
  flag `0x10 << m` on the 8×8 room that holds the cell. A waypoint object (Objects `SubClass` bit 6) sets `0x30000`.
  Slots 30–33 become level points: 30 and 31 a typed point, 32 type 10 and 33 type 11, the waypoint point.
  `LevelWarpId(L, m)` is `Warp[m]` and the destination level is `Vis[m]`, both from the act's override list (act
  `+0x90`) or else the `Levels` row. So `Warp`*k* pairs with `Vis`*k* by index. The code makes no draw here.
  (fn:DRLG_PresetMapScan@0x00667970, fn:sub_0066AF30_LevelWarpId@0x0066AF30, fn:sub_0066C040_LevelVisIds@0x0066C040,
  fn:sub_0066AEC0_LevelWarpIds@0x0066AEC0)
- [I] **In a maze level the warp room is the special that the finisher places.** Prev, Next, Down, the dock and so on
  are the records whose DS1 holds the warp cells. Which slot each record's cells name is DS1 data, not code. So "the
  Next stairs lead to `Vis[1]`" is a property of the stock DS1s, for the archivist to survey (backlog).
  (fn:sub_006724E0_MazeSpecialPlace@0x006724E0, fn:DRLG_PresetMapScan@0x00667970)
- [I] **A repeated `Vis` destination is paired by rank, not by a draw.** When a room with warp slot `m` activates,
  `sub_0066C220_WarpPairLink` ensures and builds the destination `Vis[m]`. It counts how many earlier slots of the source
  name the same destination (`k`), then finds the `k`-th slot of the destination that names the source back. The room
  with that slot's flag becomes the paired warp room. So a wilderness level with the same cave in four slots gets four
  distinct caves' stairs, matched in slot order. (fn:sub_0066C220_WarpPairLink@0x0066C220,
  fn:sub_0066BE80_WarpPairRoomFind@0x0066BE80, fn:sub_0066C370_RoomNeighboursEnsure@0x0066C370)
- [I] **`Vis` with `Warp` −1 is a walkable seam, not a warp.** Outdoor levels turn each such slot into a level-adjacency
  node (`sub_00677680_LevelBorderAdj`), and the outdoor generators read those for their borders. The act link builder
  forces `Warp` −1 between each entry and its anchor (Acts I–IV). It also adds seams between levels whose rectangles touch
  (Act III 75–83, Act V 109–112). Two of the four data pairs without `Warp` are maze levels joined to a neighbour by the
  maze code itself: 27↔28 (`MazeBarracksPlace`) and 107↔108 (`MazeRiverOfFlame`). (fn:sub_00677680_LevelBorderAdj@0x00677680,
  fn:sub_006772C0_LevelLinkBuild@0x006772C0, fn:sub_006775C0_LevelSeamsByTouch@0x006775C0,
  fn:sub_00673120_MazeBarracksPlace@0x00673120, fn:sub_00673320_MazeRiverOfFlame@0x00673320)
- [I] **The act `+0x90` list** holds 0x48-byte `LevelLinks` nodes `{levelId, vis[8], warp[8], next}`. A node is created on
  first write as a copy of the level's `Levels` `Vis0..7`/`Warp0..7` (`sub_00642860_ActLevelLinksCopy`). It is written only by
  `sub_00642920_LevelLinkSet`: if the destination is already in a slot, it overwrites that slot's warp; otherwise it fills
  the first slot with `vis == 0 && warp == −1`. Its writers are the act link builder and `LevelSeamsByTouch`. Its readers are
  `LevelWarpIds` (`+0x24`) and `LevelVisIds` (`+0x04`). (fn:sub_00642860_ActLevelLinksCopy@0x00642860,
  fn:sub_00642920_LevelLinkSet@0x00642920)
- [I] **The act link builder** lays out each act's outdoor chain on a **copy** of the act seed. Per table entry
  `{pick, levelId, anchor}`, the pick callback places `rect[i]` against `rect[anchor]`. The rect size comes from `Levels`
  `SizeX/SizeY[difficulty]`, and the first call draws a direction. A validator then rejects overlaps; a rejected pick
  tries the next direction, and an exhausted pick backtracks one entry. The builder then writes each level's rectangle,
  the town file index of levels 1 and 40, and level 27's index from **one draw on the act seed itself** while handling
  level 6. (fn:sub_006772C0_LevelLinkBuild@0x006772C0, fn:sub_00678AD0_ActLinkInit@0x00678AD0)
- [I] **Warp points.** `sub_006423D0_LevelWarpPointsBuild` walks the rooms in list order and appends one point per room:
  the room centre `(x + w/2, y + h/2)`, signed halves, converted to subtiles. A room qualifies if its flags have `0x30000`
  (a waypoint room), or one of the bits `0x10..0x800` whose slot has `LevelWarpId ≠ −1`. **Correction to drlg/0005 § 9:**
  the `0x30000` state does not carry to the next room. It is set and consumed in the same iteration. The count `+0x228`
  is not bounded by the 9-entry arrays. `LevelUnload` clears `+0x1E0..+0x22B` (x[9], y[9] and the count), so each build
  starts empty. (fn:sub_006423D0_LevelWarpPointsBuild@0x006423D0, fn:sub_00642010_LevelUnload@0x00642010)
- [I] **`0x00642390` is not a warp pass.** It restores room `+0x60` bit 0 on a rebuild from the per-room array at level
  `+0x22C`, which `LevelUnload` (keep mode) saves. It makes no draw. (fn:sub_00642390_LevelRoomStateRestore@0x00642390,
  fn:sub_00642010_LevelUnload@0x00642010)
- [I] **LvlWarp columns.** `OffsetX/OffsetY` (`+0x1C`/`+0x20`) offset the warp unit from its cell. The warp unit is a
  preset unit of type 5 whose class is `Id` (`WarpUnitAdd`). `ExitWalkX/ExitWalkY` (`+0x14`/`+0x18`) offset where the
  server puts a unit that comes out of the paired warp (`0x005550B0`). `SelectX/Y/DX/DY` (`+0x04`..`+0x10`) are read only
  by the client, which draws the warp's selection box (`0x0045B1E0`). (fn:sub_0066E1C0_WarpUnitAdd@0x0066E1C0,
  fn:sub_005550B0_WarpExitPos@0x005550B0, fn:sub_0045B1E0_WarpSelectBoxDraw@0x0045B1E0)

## Leads used

Blind first: every claim above was written from the code before any community text was read.

No lead was used to locate code. The Phase 1b cross-check is in § Phase 1b verdicts.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x00678AD0` | `sub_00678AD0_ActLinkInit` | `DL` act index → one of the five act functions | I |
| `0x00677750` | `sub_00677750_ActLinkAct1` | tables `0x006F0750` (check `0x00676DD0`), `0x006F0840` (check `0x00676EB0`), both with `LinkOutdoorFlags`; `LevelBorderAdj(1..17)` | I |
| `0x00677790` | `sub_00677790_ActLinkAct2` | tables `0x006F0930`, `0x006F0A20`; `LevelBorderAdj(40..46)` | I |
| `0x006789B0` | `sub_006789B0_ActLinkAct3` | level 75 at its `Levels` offset; `0x00677880`/`0x00678910` (jungle layout, not read); `LevelSeamsByTouch(75, 83)`; `LevelBorderAdj(75..83)` | I |
| `0x00678A20` | `sub_00678A20_ActLinkAct4` | tables `0x006F0C00`, `0x006F0CF0`; level 104's outdoor flags; `LevelBorderAdj(103..106)` | I |
| `0x00678A70` | `sub_00678A70_ActLinkAct5` | tables `0x006F0DE0`, `0x006F0ED0`; seams 111–112, 110–111, 109–110; `LevelBorderAdj(111..112)`; table `0x006F0B10` | I |
| `0x006772C0` | `sub_006772C0_LevelLinkBuild` | the builder: picks, checks, backtracking; level rects; town/level-27 indices; seams | I |
| `0x006760F0` | `sub_006760F0_LinkAnchor` | anchor entry: position = `Levels` `OffsetX/OffsetY`, no draw | I |
| `0x00676150` | `sub_00676150_LinkPick` | 4 sides, `lo & 3`, 16-tile stagger | I |
| `0x00676280` | `sub_00676280_LinkPick` | 8 placements, `lo & 7` (4 sides × 2 half-offsets) | I |
| `0x00676450` | `sub_00676450_LinkPick` | 4 sides × 2 alignments, `lo & 3` then `lo & 1` | I |
| `0x00676650` | `sub_00676650_LinkPick` | as `0x00676450`, and sets the size 56×96 or 96×56 by side parity (Blood Moor) | I |
| `0x006768C0` | `sub_006768C0_LinkPickFixed` | fixed side 0 (below), no draw (Tamoe Highland) | I |
| `0x006769A0` | `sub_006769A0_LinkPick` | side 1 or 2, `(lo & 1) + 1` (Rocky Waste) | I |
| `0x00676AE0` | `sub_00676AE0_LinkPick` | 4 sides, `lo & 7` paired (Valley of Snakes) | I |
| `0x00676C00` | `sub_00676C00_LinkPick` | side 3, `lo & 1` picks the vertical offset and the outdoor flag `0x800000`/`0x400000` (Outer Steppes) | I |
| `0x0067D830` | `sub_0067D830_LinkPick` | `lo & 1`: size 64×160 or 160×64, fixed side (Rigid Highlands) | I |
| `0x0067D980` | `sub_0067D980_LinkPick` | `lo & 1`, toggles on retry; size by choice; offset table `0x006F1F7C` (Arreat Plateau) | I |
| `0x0067D8E0` | `sub_0067D8E0_LinkPick` | `lo & 1`: width 64 or 160; x from `Levels` `OffsetX` (Tundra Wastelands) | I |
| `0x00676DD0` | `sub_00676DD0_LinkCheckAct1A` | no overlap with earlier entries but the anchor; Rogue Encampment's side pair from table `0x006F1158`; Burial Grounds' side unique among its anchor's children | I |
| `0x00676EB0` | `sub_00676EB0_LinkCheckAct1B` | no overlap, plus a test of the rect widened 200 tiles west | I |
| `0x00676F50`, `0x00676FC0`, `0x006770A0`, `0x00677110`, `0x00677030` | `LinkCheckAct2A/2B/4A/4B/5C` | no overlap with earlier entries but the anchor | I |
| `0x00677180` | `sub_00677180_LinkOutdoorFlags` | Act I: ORs outdoor-data flags from table `0x006F1258` by the entry's and next entry's sides (drlg/outdoor input) | I |
| `0x006775C0` | `sub_006775C0_LevelSeamsByTouch` | every pair in a level range whose rects touch gets a `Warp` −1 slot | I |
| `0x00677680` | `sub_00677680_LevelBorderAdj` | outdoor levels: a level-adjacency node per `Vis` slot with `Warp` −1 | I |
| `0x0066B790` | `sub_0066B790_LevelAdjAdd` | sorted level-adjacency node `{level, dir, isPreset, 0, &rect}` | I |
| `0x00642860` | `sub_00642860_ActLevelLinksCopy` | get or create a level's `LevelLinks` node in act `+0x90` | I |
| `0x00642920` | `sub_00642920_LevelLinkSet` | set a destination's warp, or add it in the first free slot | I |
| `0x0066C040` | `sub_0066C040_LevelVisIds` | a level's `vis[8]`: override node `+0x04`, else leveldefs `+0x48` | I |
| `0x0066AEC0` | `sub_0066AEC0_LevelWarpIds` | a level's `warp[8]`: override node `+0x24`, else leveldefs `+0x68` | I |
| `0x0066C220` | `sub_0066C220_WarpPairLink` | slot `m` of a room → destination level built, paired room found by rank | I |
| `0x0066BE80` | `sub_0066BE80_WarpPairRoomFind` | the destination room with the paired slot's flag | I |
| `0x0066BE10` | `sub_0066BE10_RoomWarpNodeAdd` | room `+0x4C` warp node with the `'b'` LvlWarp record | I |
| `0x0066AB00` | `sub_0066AB00_WarpDestRoom` | the paired room of a warp class, activated if needed | I |
| `0x0066AF80` | `sub_0066AF80_RoomWarpRecOfUnit` | the LvlWarp record of a warp unit in a room | I |
| `0x00619620` | `sub_00619620_UnitWarpRec` | unit → its room → `RoomWarpRecOfUnit` | I |
| `0x006195A0` | `sub_006195A0_UnitWarpDestRoom` | unit → `WarpDestRoom` | I |
| `0x005550B0` | `sub_005550B0_WarpExitPos` | server: exit position = paired warp + `ExitWalkX/Y` | I |
| `0x0045B1E0` | `sub_0045B1E0_WarpSelectBoxDraw` | client: draws the `Select*` box | I |
| `0x00673FF0` | `sub_00673FF0_VisWarpFlag` | the flag `0x10 << k` of the slot of level A that names level B | I |
| `0x006423D0` | `sub_006423D0_LevelWarpPointsBuild` | the warp point list (above) | I |
| `0x00642390` | `sub_00642390_LevelRoomStateRestore` | room `+0x60` bit 0 from level `+0x22C` | I |

## Walkthrough

### 1. Slots, flags and points from a preset DS1

```c
// fn:DRLG_PresetMapScan@0x00667970 (trimmed): per DS1 cell of the instance, when Scan (+0x34) is set
o = orientation; m = (cell >> 20) & 0x3F; sub = (cell >> 8) & 0xFF
if (o == 10 || o == 11):
  if (m < 8 && (sub == 0 || sub == 4 || cell & 0x80000000))
    roomFlagGrid[x/8, y/8] |= 0x10 << m                // (0, 0) when the instance is a single room
  if (8 <= m < 30) ... pops (drlg/0004)
  if (30 <= m < 34): L.points[L.nPoints++] = { inst.x + x, inst.y + y,
                       type = {30: sub, 31: sub + 5, 32: 10, 33: 11}[m] }   // level +0x2C, 12-byte entries
for each object unit of the DS1 with id < 0x23D and Objects SubClass bit 6:   // the waypoint
  roomFlagGrid[(unit.x / 5) / 8, ...] |= 0x30000
```

- [I] `PresetRoomsCreate` passes the grid cell as the new room's flags (`sub_00666680_PresetRoomCreate` ORs them into
  room `+0x28`). A room's warp bits name the slots of the warp cells it contains. This holds for presets placed by any
  generator: preset levels, maze rooms and outdoor embedded presets. The outdoor generator also writes the same bits
  (`0x800`, `0x20000`) into its own cells, at `0x00674B70` for level 3 (the cave mouth, plan 0026).
  (fn:DRLG_PresetMapScan@0x00667970, fn:sub_00666680_PresetRoomCreate@0x00666680)
- [I] The type-11 point that `LevelPointFind` uses (drlg/0005 § 9, including its one level-seed draw) is a slot-33 cell
  of a preset. That draw belongs to `LevelPointFind`, which runs during population, not to the build. The same point
  list serves `Levels` `Position`. (fn:DRLG_PresetMapScan@0x00667970, fn:sub_0066B2B0_LevelPointFind@0x0066B2B0)

### 2. Slot → destination, and the pairing

```c
// fn:sub_0066C220_WarpPairLink@0x0066C220. args: ?, srcRoom, m (fatal if m > 7)
S = srcRoom.level; vis = LevelVisIds(act, S.id); dest = vis[m]
D = LevelEnsure(act, dest); wid = LevelWarpId(S, m); if (!D.rooms) LevelInit(D)   // lazy build of the neighbour
if (wid != -1):
  k = count of j < m with vis[j] == dest
  walk D's vis slots j = 0..7 naming S.id; at the k-th: if (WarpPairRoomFind(D.rooms, j, ...)) return
walk again: the first slot j of D naming S whose WarpPairRoomFind succeeds
```

- [I] The caller is `RoomNeighboursEnsure`, run when a room activates, once per warp bit. So entering a room with
  stairs builds the next level. This is the "linked levels" lazy build of drlg/0003. `WarpPairRoomFind` marks the
  destination room (`0x0066BDA0`) and gives it a warp node (`RoomWarpNodeAdd`, record `'b'`). With `wid == −1` it only
  marks the rooms within 6 tiles. (fn:sub_0066C370_RoomNeighboursEnsure@0x0066C370, fn:sub_0066BE80_WarpPairRoomFind@0x0066BE80)
- [I] **The one asymmetric link, 133 → 17**, is read. Matron's Den (133) is a type-4 crypt maze whose finisher places the
  Crypt Prev stairs (§ 6 of drlg/0006). If their DS1 warp cell is slot 0, `Warp0` = 8 (`Act 1 Crypt Up`) and
  `Vis0` = 17. The warp tile pick is skipped on level 133 (drlg/0002, `WarpTileAdd` not called there), but the slot bit,
  the warp unit and the pairing code do not test the level. The back-link from 17 does not exist, so the
  pairing's rank search finds no slot and the second walk fails too. What the game then does on use is not read
  (Open questions). (fn:sub_0066C220_WarpPairLink@0x0066C220)

### 3. The act link builder

```c
// fn:sub_006772C0_LevelLinkBuild@0x006772C0 (trimmed). ESI = act, args table, check, after
B = {0}; B.seed = act.seed (copy); every dir/dir0/step/flip0 = -1
for i: B.rect[i].w, h = Levels[table[i].level].SizeX/SizeY[act.diff]
i = 0
while (table[i].level):                                // backtracking
  if (!table[i].pick(&B)) { reset entry i; i--; continue }      // exhausted: back up one entry
  if (!check || check(&B, i)) i++                        // else: same i, the pick tries its next choice
for i:
  L = LevelEnsure(act, table[i].level); L.rect = B.rect[i]
  if (L.drlg == 2): if (L.id == 1) L.data.idx = B.dir[i]; if (L.id == 40) L.data.idx = B.dir[i + 1]
  if (L.id == 6):                                        // level 27's preset index, on the act seed itself
    if (B.dir[i] == 1) idx27 = 2 - (step(act.seed) & 1); else if (B.dir[i] == 3) idx27 = ~step(act.seed) & 1
  if (after) after(...)                                  // Act I: LinkOutdoorFlags
  if (act.index != 4 && table[i].anchor != -1): LevelLinkSet both ways with warp -1   // a walkable seam
```

- [I] Pick protocol: the first call for an entry draws its choice(s) on `B.seed` and stores them in `dir0`/`flip0`.
  Each later call steps to the next choice and returns 0 once it is back at the first. So an entry draws only on its
  first try after each backtrack reset. The positions are fixed formulas of the anchor rect and the entry's size.
  `0x00676150`, for example:
  - side 0: `(P.x − 16, P.y + P.h)`;
  - side 1: `(P.x − w, P.y − 16)`;
  - side 2: `(P.x + P.w − w + 16, P.y − h)`;
  - side 3: `(P.x + P.w, P.y + P.h − h + 16)`.

  (fn:sub_00676150_LinkPick@0x00676150, fn:sub_006772C0_LevelLinkBuild@0x006772C0)
- [I] Tables (entry: pick, level, anchor index) (fn:sub_006772C0_LevelLinkBuild@0x006772C0):
  - `0x006F0750`: Stony Field 4 (anchor), Cold Plains 3 ← 0 (`0x00676150`), Blood Moor 2 ← 1 (`0x00676650`),
    Rogue Encampment 1 ← 2 (`0x00676450`), Burial Grounds 17 ← 1 (`0x00676150`);
  - `0x006F0840`: Moo Moo Farm 39 (anchor), Monastery Gate 26 (anchor), Tamoe Highland 7 ← 1 (fixed), Black Marsh
    6 ← 2, Dark Wood 5 ← 3 (`0x00676150`);
  - `0x006F0930`: Lut Gholein 40 (anchor), Rocky Waste 41 ← 0 (`0x006769A0`), Dry Hills 42, Far Oasis 43 and Lost City 44,
    each anchored on the previous entry (`0x00676280`), Valley of Snakes 45 ← 4 (`0x00676AE0`);
  - `0x006F0A20`: Canyon of the Magi 46 (anchor);
  - `0x006F0C00`: Pandemonium Fortress 103 (anchor), Outer Steppes 104 ← 0 (`0x00676C00`), Plains of Despair 105 ← 1,
    City of the Damned 106 ← 2 (`0x00676150`);
  - `0x006F0CF0`: Chaos Sanctum 108 (anchor);
  - `0x006F0DE0`: Harrogath 109 (anchor), Bloody Foothills 110 ← 0 (anchor pick, `Levels` offsets),
    Rigid Highlands 111 ← 1 (`0x0067D830`), Arreat Plateau 112 ← 2 (`0x0067D980`);
  - `0x006F0ED0`: Tundra Wastelands 117 (`0x0067D8E0`);
  - `0x006F0B10`: Pandemonium Run 2 134, Tristram 136 (anchors).

  (data 0x006F0750–0x006F0ED0)
- [I] The Act I town index is the Rogue Encampment entry's side (`0x00676450`, 0–3). Lut Gholein's index is Rocky Waste's
  side (1 or 2). Level 27's index is drawn on the act seed only when Black Marsh's side is 1 or 3. This matches the
  link-value writes [drlg/0003](0003-generator-dispatch.md) logged for levels 1 and 40. (fn:sub_006772C0_LevelLinkBuild@0x006772C0)

### 4. Warp points

```c
// fn:sub_006423D0_LevelWarpPointsBuild@0x006423D0. EDI = L; called once at the end of every LevelInit
for R in L.rooms (newest first):
  if (R.flags & 0x30000) || any m in 0..7 with (R.flags & (0x10 << m)) && LevelWarpId(L, m) != -1:
    n = L[+0x228]++                                      // no bound check against the 9 slots
    L.x[n] /*+0x1E0*/ = R.x + R.w / 2;  L.y[n] /*+0x204*/ = R.y + R.h / 2   // signed halves
    TileToSubtile(&L.x[n], &L.y[n])                      // ×5
```

- [I] run:2026-10-14-collision logged this list as an input to `NearWarpTest`; it did not check the build rule. Phase 2
  predicts it from the room flags. (fn:sub_006423D0_LevelWarpPointsBuild@0x006423D0, fn:sub_0054DB50_NearWarpTest@0x0054DB50)

## Answers to the Phase 0 question (d)

- [I] **What reads `Vis0..7`:** `LevelVisIds` (`0x0066C040`), used by warp pairing (`WarpPairLink`), by the outdoor
  border pass (`LevelBorderAdj`), by preset-level builds (`PresetLevelBuild`, `PresetMapScan`), by level reference counting
  (`0x00642F70`, `0x00643060`) and by `0x00673FF0`. `Warp`*k* pairs with `Vis`*k* by index.
- [I] **Repeated levels in `Vis`** (fn:sub_0066C220_WarpPairLink@0x0066C220; wilderness → cave ×4, Kurast 2/3 → 92 twice): no slot is chosen per game, and no
  draw is involved. Each slot is its own warp, paired by rank with the destination's matching back-slot.
- [I] **133 → 17** is read, not dead data (§ 2). (fn:sub_0066C220_WarpPairLink@0x0066C220)
- The eight `Vis`-without-`Warp` slots are walkable seams (summary).

## Phase 1b verdicts

Compared after the blind reading above (2026-10-14); see `docs/sources.md` `d2dfg-blizzard` for the searches.

- [L] src:d2dfg-blizzard: `Vis0`–`Vis7` "defines the visibility of other area levels involved with this area level". **held
  with refinement**
  Detail: in 1.14d `Vis`*k* is the destination level of warp slot *k*, or a walkable seam when `Warp`*k* is −1 (§ 2,
  summary).
- [L] src:d2dfg-blizzard: `Warp0`–`Warp7` use LvlWarp `Id`, "which Level Warp to use when exiting". **held**
  Detail: `Warp`*k* is the `Id` of slot *k*, paired with `Vis`*k* by index (`LevelWarpIds`).
- [L] src:d2dfg-blizzard: Levels `SizeX & SizeY` are the tile size of the level, and `OffsetX & OffsetY` the origin
  offset. **held**
  Detail: the link builder sizes each rect from `SizeX/SizeY[difficulty]`, and anchor entries take `OffsetX/OffsetY` (§ 3).
- [L] src:d2dfg-blizzard: LvlWarp `SelectX/Y`, `SelectDX/DY` define the warp's selection area. **held with refinement**
  Detail: only the client reads them (`0x0045B1E0`, the box drawn around a warp).
- [L] src:d2dfg-blizzard: `ExitWalkX/Y` are "the destination location where the player will walk to after exiting".
  **held**
  Detail: the server's exit position is the paired warp unit's position plus `ExitWalkX/Y` (`0x005550B0`).
- [L] src:d2dfg-blizzard: `OffsetX/Y` are "the sub-tile for the Level Warp, where the player will appear when exiting".
  **held with refinement**
  Detail: they offset the warp unit from its cell (`WarpUnitAdd`). The player appears relative to that unit, plus
  `ExitWalkX/Y`.
- [L] src:d2dfg-blizzard: `LitVersion`, `Tiles` and `Direction`. **held**
  Detail: as drlg/0002 reads them (one extra lit-tile pick, the sub-index of that tile, `'b'`/`'l'`/`'r'` fitting).
- [L] src:d2dfg-blizzard: `NoInteract`, `UniqueId`. **not covered**
  Detail: these columns are absent from 1.14d `lvlwarp.bin` (a later build).
- [L] src:d2dfg-blizzard: the act link builder, rank pairing of repeated `Vis` and the warp point list. **not covered**

## Data touched

- tbl:Levels.txt:Vis0 (`+0x48 + 4k`, the slot's destination), tbl:Levels.txt:Warp0 (`+0x68 + 4k`, the LvlWarp `Id`),
  tbl:Levels.txt:SizeX (`+0x0C + 4·diff`, the link rect size), tbl:Levels.txt:SizeY (`+0x18 + 4·diff`),
  tbl:Levels.txt:OffsetX / tbl:Levels.txt:OffsetY (`+0x24`/`+0x28`, anchors' positions).
- tbl:LvlWarp.txt:Id (`+0x00`), tbl:LvlWarp.txt:SelectX..`SelectDY` (`+0x04`..`+0x10`, client), tbl:LvlWarp.txt:ExitWalkX /
  tbl:LvlWarp.txt:ExitWalkY (`+0x14`/`+0x18`, server exit), tbl:LvlWarp.txt:OffsetX / tbl:LvlWarp.txt:OffsetY
  (`+0x1C`/`+0x20`, warp unit position), tbl:LvlWarp.txt:Direction (`+0x2C`).
- struct:LevelLinks+0x04 (`vis`), struct:LevelLinks+0x24 (`warp`), struct:LinkBuild+0x0FC (`dir`, the link value),
  struct:DrlgRoomMaze+0x28 (warp slot bits and `0x30000`).
- Level `+0x1E0` x[9], `+0x204` y[9], `+0x228` count; level `+0x2C` points (12 bytes), count `+0x1D8`; level `+0x22C`
  saved room state; act `+0x90` (`LevelLinks` list), `+0x480` act index, `+0x450` difficulty.

## Boundary for Phase 2

- [I] The links are modellable end to end for Acts I, II, IV and V: tables, pick formulas, checks and backtracking, all
  on the act-seed copy. **Act III's jungle layout** (`0x00677880`/`0x00678910`, 119 act-seed steps for seed 12345 per
  rng/0002) was not read here. It is an outdoor layout, so the recommendation is to leave it to `drlg/outdoor` (plan 0026)
  and keep Act III's level rectangles as a logged input in Phase 2. The warp points need only the room list and
  flags; the flags come from the DS1 scan, which `tools/drlg.py` already models for presets.

## Dead ends

- drlg/0005 § 9 read the `0x30000` flag as carrying to the next room. The disassembly (`0x006423F0`–`0x00642487`)
  consumes it in the same iteration.
- `0x00642390` was named as a warp pass in drlg/0003. It restores a saved room bit and touches no warp data.

## Open questions

- Which slot each stock DS1's warp cells name (Prev = 0, Next = 1, …?) is DS1 data: backlog → archivist (survey).
- What happens when a warp with no back-link (133 → 17) is used. This needs a harness run.
- ~~Act III's layout functions `0x00677880` and `0x00678910` (owner `drlg/outdoor`).~~ Read 2026-10-14 in
  [drlg/0008 § 10](0008-outdoor.md#10-act-iii-levels-7683-and-the-jungle-layout).
- The second argument of `WarpPairLink` and the marking function `0x0066BDA0` were not read in full.
