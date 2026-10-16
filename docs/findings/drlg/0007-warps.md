# 0007 — Level links, warp slots and the warp points

> **Subsystem:** drlg/warps
> **Question:** How does every level get its links to other levels: what the act link builder draws and writes, how `Vis` and `Warp` slots pair, which room of a level holds the warp to which neighbour, and which points end up in `level+0x1E0`?
> **Date:** 2026-10-14 (Phase 2: 2026-10-15)   **Plan:** 0022 (Phase 1, 1b, 2)   **Status:** reproduced (run:2026-10-15-drlg-maze; § 5)

Static reading (decompile plus disassembly for the register arguments) of the act link builder `0x006772C0` and its
callbacks, of the per-level link override list at act `+0x90`, of the warp-slot plumbing between preset DS1 cells,
room flags and destination levels, and of the two post-build passes of `LevelInit`. Maze-specific placement is in
[drlg/0006](0006-maze.md). Phase 1 ran nothing. Phase 2 (§ 5) reproduced the link builder of Acts I, II, IV and V, the room
flags, the warp points and the warp pairing in run:2026-10-15-drlg-maze with 0 mismatches. The claims it covers are `[C]`;
the others keep `[I]`.

## Answer (summary)

- [C] **A warp's neighbour is chosen by slot, and the slot comes from the DS1.** A DS1 cell of orientation 10 or 11
  carries a slot `m` = bits 20–25. When `DRLG_PresetMapScan` scans an instance (`Scan` set), a slot `m < 8` sets room
  flag `0x10 << m` on the 8×8 room that holds the cell. A waypoint object (Objects `SubClass` bit 6) sets `0x30000`.
  Slots 30–33 become level points: 30 and 31 a typed point, 32 type 10 and 33 type 11, the waypoint point.
  `LevelWarpId(L, m)` is `Warp[m]` and the destination level is `Vis[m]`, both from the act's override list (act
  `+0x90`) or else the `Levels` row. So `Warp`*k* pairs with `Vis`*k* by index. The code makes no draw here.
  Before the scan, every room of the instance gets the `PresetRoomsCreate` flags and `0x10 << k` for every `Vis` slot `k`
  whose `Warp` is −1 (§ 5). (fn:DRLG_PresetMapScan@0x00667970, fn:sub_0066AF30_LevelWarpId@0x0066AF30,
  fn:sub_0066C040_LevelVisIds@0x0066C040, fn:sub_0066AEC0_LevelWarpIds@0x0066AEC0, run:2026-10-15-drlg-maze)
- [C] **In a maze level the warp room is the special that the finisher places.** Prev, Next, Down, the dock and so on
  are the records whose DS1 holds the warp cells. Which slot each record's cells name is DS1 data, not code. So "the
  Next stairs lead to `Vis[1]`" is a property of the stock DS1s, for the archivist to survey (backlog).
  (fn:sub_006724E0_MazeSpecialPlace@0x006724E0, fn:DRLG_PresetMapScan@0x00667970, run:2026-10-15-drlg-maze)
- [C] **A repeated `Vis` destination is paired by rank, not by a draw**, with a fallback (correction, § 5). When a room with warp slot `m` activates,
  `sub_0066C220_WarpPairLink` ensures and builds the destination `Vis[m]`. It counts how many earlier slots of the source
  name the same destination (`k`), then finds the `k`-th slot of the destination that names the source back. The room
  with that slot's flag becomes the paired warp room. So a wilderness level with the same cave in four slots gets four
  distinct caves' stairs, matched in slot order. When the destination has no room with the rank slot's bit, the first
  slot of the destination naming the source whose room exists is taken (the Durance levels, whose stairs face one side).
  (fn:sub_0066C220_WarpPairLink@0x0066C220, fn:sub_0066BE80_WarpPairRoomFind@0x0066BE80,
  fn:sub_0066C370_RoomNeighboursEnsure@0x0066C370, run:2026-10-15-drlg-maze)
- [C] **`Vis` with `Warp` −1 is a walkable seam, not a warp** (the override lists of Acts I, II, IV and V reproduced;
  `LevelBorderAdj` is checked by drlg/0008's outdoor replay, not here). Outdoor levels turn each such slot into a level-adjacency
  node (`sub_00677680_LevelBorderAdj`), and the outdoor generators read those for their borders. The act link builder
  forces `Warp` −1 between each entry and its anchor (Acts I–IV). It also adds seams between levels whose rectangles touch
  (Act III 75–83, Act V 109–112). Two of the four data pairs without `Warp` are maze levels joined to a neighbour by the
  maze code itself: 27↔28 (`MazeBarracksPlace`) and 107↔108 (`MazeRiverOfFlame`). (fn:sub_00677680_LevelBorderAdj@0x00677680,
  fn:sub_006772C0_LevelLinkBuild@0x006772C0, fn:sub_006775C0_LevelSeamsByTouch@0x006775C0,
  fn:sub_00673120_MazeBarracksPlace@0x00673120, fn:sub_00673320_MazeRiverOfFlame@0x00673320)
- [C] **The act `+0x90` list** holds 0x48-byte `LevelLinks` nodes `{levelId, vis[8], warp[8], next}`. A node is created on
  first write as a copy of the level's `Levels` `Vis0..7`/`Warp0..7` (`sub_00642860_ActLevelLinksCopy`). It is written only by
  `sub_00642920_LevelLinkSet`: if the destination is already in a slot, it overwrites that slot's warp; otherwise it fills
  the first slot with `vis == 0 && warp == −1`. Its writers are the act link builder and `LevelSeamsByTouch`. Its readers are
  `LevelWarpIds` (`+0x24`) and `LevelVisIds` (`+0x04`). (fn:sub_00642860_ActLevelLinksCopy@0x00642860,
  fn:sub_00642920_LevelLinkSet@0x00642920, run:2026-10-15-drlg-maze)
- [C] **The act link builder** lays out each act's outdoor chain on a **copy** of the act seed. Per table entry
  `{pick, levelId, anchor}`, the pick callback places `rect[i]` against `rect[anchor]`. The rect size comes from `Levels`
  `SizeX/SizeY[difficulty]`, and the first call draws a direction. A validator then rejects overlaps; a rejected pick
  tries the next direction, and an exhausted pick backtracks one entry. The builder then writes each level's rectangle,
  the town file index of levels 1 and 40, and level 27's index from **one draw on the act seed itself** while handling
  level 6: `2 − (lo & 1)` when Black Marsh's side is 1, `(~lo) & 1` when it is 3. (fn:sub_006772C0_LevelLinkBuild@0x006772C0,
  fn:sub_00678AD0_ActLinkInit@0x00678AD0, run:2026-10-15-drlg-maze; Act III's layout is drlg/0008's)
- [C] **Warp points.** `sub_006423D0_LevelWarpPointsBuild` walks the rooms in list order and appends one point per room:
  the room centre `(x + w/2, y + h/2)`, signed halves, converted to subtiles. A room qualifies if its flags have `0x30000`
  (a waypoint room), or one of the bits `0x10..0x800` whose slot has `LevelWarpId ≠ −1`. **Correction to drlg/0005 § 9:**
  the `0x30000` state does not carry to the next room. It is set and consumed in the same iteration. The count `+0x228`
  is not bounded by the 9-entry arrays. `LevelUnload` clears `+0x1E0..+0x22B` (x[9], y[9] and the count), so each build
  starts empty. (fn:sub_006423D0_LevelWarpPointsBuild@0x006423D0, fn:sub_00642010_LevelUnload@0x00642010,
  run:2026-10-15-drlg-maze; the unbounded count is `[I]`: no build had more than 9 points)
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
| `0x00678AD0` | `sub_00678AD0_ActLinkInit` | `DL` act index → one of the five act functions | C |
| `0x00677750` | `sub_00677750_ActLinkAct1` | tables `0x006F0750` (check `0x00676DD0`), `0x006F0840` (check `0x00676EB0`), both with `LinkOutdoorFlags`; `LevelBorderAdj(1..17)` | C |
| `0x00677790` | `sub_00677790_ActLinkAct2` | tables `0x006F0930`, `0x006F0A20`; `LevelBorderAdj(40..46)` | C |
| `0x006789B0` | `sub_006789B0_ActLinkAct3` | level 75 at its `Levels` offset; `0x00677880`/`0x00678910` (jungle layout, not read); `LevelSeamsByTouch(75, 83)`; `LevelBorderAdj(75..83)` | I |
| `0x00678A20` | `sub_00678A20_ActLinkAct4` | tables `0x006F0C00`, `0x006F0CF0`; level 104's outdoor flags; `LevelBorderAdj(103..106)` | C |
| `0x00678A70` | `sub_00678A70_ActLinkAct5` | tables `0x006F0DE0`, `0x006F0ED0`; seams 111–112, 110–111, 109–110; `LevelBorderAdj(111..112)`; table `0x006F0B10` | C |
| `0x006772C0` | `sub_006772C0_LevelLinkBuild` | the builder: picks, checks, backtracking; level rects; town/level-27 indices; seams | C |
| `0x006760F0` | `sub_006760F0_LinkAnchor` | anchor entry: position = `Levels` `OffsetX/OffsetY`, no draw | C |
| `0x00676150` | `sub_00676150_LinkPick` | 4 sides, `lo & 3`, 16-tile stagger | C |
| `0x00676280` | `sub_00676280_LinkPick` | 8 placements, `lo & 7` (4 sides × 2 half-offsets) | C |
| `0x00676450` | `sub_00676450_LinkPick` | 4 sides × 2 alignments, `lo & 3` then `lo & 1` | C |
| `0x00676650` | `sub_00676650_LinkPick` | as `0x00676450`, and sets the size 56×96 or 96×56 by side parity (Blood Moor) | C |
| `0x006768C0` | `sub_006768C0_LinkPickFixed` | fixed side 0 (below), no draw (Tamoe Highland) | C |
| `0x006769A0` | `sub_006769A0_LinkPick` | side 1 or 2, `(lo & 1) + 1` (Rocky Waste) | C |
| `0x00676AE0` | `sub_00676AE0_LinkPick` | 4 sides, `lo & 7` paired (Valley of Snakes) | C |
| `0x00676C00` | `sub_00676C00_LinkPick` | side 3, `lo & 1` picks the vertical offset and the outdoor flag `0x800000`/`0x400000` (Outer Steppes) | C |
| `0x0067D830` | `sub_0067D830_LinkPick` | `lo & 1`: size 64×160 or 160×64, fixed side (Rigid Highlands) | C |
| `0x0067D980` | `sub_0067D980_LinkPick` | `lo & 1`, toggles on retry; size by choice; offset table `0x006F1F7C` (Arreat Plateau) | C |
| `0x0067D8E0` | `sub_0067D8E0_LinkPick` | `lo & 1`: width 64 or 160; x from `Levels` `OffsetX` (Tundra Wastelands) | C |
| `0x00676DD0` | `sub_00676DD0_LinkCheckAct1A` | no overlap with earlier entries but the anchor; Rogue Encampment's side pair from table `0x006F1158`; Burial Grounds' side unique among its anchor's children | C |
| `0x00676EB0` | `sub_00676EB0_LinkCheckAct1B` | no overlap, plus a test of the rect widened 200 tiles west | C |
| `0x00676F50`, `0x00676FC0`, `0x006770A0`, `0x00677110`, `0x00677030` | `LinkCheckAct2A/2B/4A/4B/5C` | no overlap with earlier entries but the anchor | C |
| `0x00677180` | `sub_00677180_LinkOutdoorFlags` | Act I: ORs outdoor-data flags from table `0x006F1258` by the entry's and next entry's sides (drlg/outdoor input) | I |
| `0x006775C0` | `sub_006775C0_LevelSeamsByTouch` | every pair in a level range whose rects touch gets a `Warp` −1 slot | C |
| `0x0066B880` | `sub_0066B880_RectTouch` | two rects share an edge segment (`t` −1), or touch/overlap (`t` 0); § 3 | C |
| `0x00677680` | `sub_00677680_LevelBorderAdj` | outdoor levels: a level-adjacency node per `Vis` slot with `Warp` −1 | I |
| `0x0066B790` | `sub_0066B790_LevelAdjAdd` | sorted level-adjacency node `{level, dir, isPreset, 0, &rect}` | I |
| `0x00642860` | `sub_00642860_ActLevelLinksCopy` | get or create a level's `LevelLinks` node in act `+0x90` | C |
| `0x00642920` | `sub_00642920_LevelLinkSet` | set a destination's warp, or add it in the first free slot | C |
| `0x0066C040` | `sub_0066C040_LevelVisIds` | a level's `vis[8]`: override node `+0x04`, else leveldefs `+0x48` | C |
| `0x0066AEC0` | `sub_0066AEC0_LevelWarpIds` | a level's `warp[8]`: override node `+0x24`, else leveldefs `+0x68` | C |
| `0x0066C220` | `sub_0066C220_WarpPairLink` | slot `m` of a room → destination level built, paired room found by rank | C |
| `0x0066BE80` | `sub_0066BE80_WarpPairRoomFind` | the destination room with the paired slot's flag | C |
| `0x0066BE10` | `sub_0066BE10_RoomWarpNodeAdd` | room `+0x4C` warp node with the `'b'` LvlWarp record | C |
| `0x0066AB00` | `sub_0066AB00_WarpDestRoom` | the paired room of a warp class, activated if needed | I |
| `0x0066AF80` | `sub_0066AF80_RoomWarpRecOfUnit` | the LvlWarp record of a warp unit in a room | I |
| `0x00619620` | `sub_00619620_UnitWarpRec` | unit → its room → `RoomWarpRecOfUnit` | I |
| `0x006195A0` | `sub_006195A0_UnitWarpDestRoom` | unit → `WarpDestRoom` | I |
| `0x005550B0` | `sub_005550B0_WarpExitPos` | server: exit position = paired warp + `ExitWalkX/Y` | I |
| `0x0045B1E0` | `sub_0045B1E0_WarpSelectBoxDraw` | client: draws the `Select*` box | I |
| `0x00673FF0` | `sub_00673FF0_VisWarpFlag` | the flag `0x10 << k` of the slot of level A that names level B | I |
| `0x006423D0` | `sub_006423D0_LevelWarpPointsBuild` | the warp point list (above) | C |
| `0x00642D10` | `sub_00642D10_LevelSetPosition` | level rect: sizes of the difficulty at the offsets, plus the `Depend` level's position | C |
| `0x0066AF30` | `sub_0066AF30_LevelWarpId` | `LevelWarpIds(L)[m]` | C |
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

Provenance follow-up of 2026-10-15 (backlog spec-writer → reverser): every pick, validator and pass below was read from
the code and the data. The Phase 2 model agrees with the code everywhere except the Act1B widening, which it had on the
wrong axis (see that item; model fixed, still 0 mismatches). The reached choices and the reject counts below are counted
on the builds that run:2026-10-15-drlg-maze checks line by line (`LNK1`): 159 checks of 73 builds, all from map seed 2027.
Every entry ended on the same choice in all of them. The older logs (map seeds 1, 12345, 777) have no `LNK` lines; there
the builder is only an input to the preset and maze checks, so it adds no reached choice here.

**The builder state `B`** (a 500-byte stack block at `0x006772C0`, `ECX` of every pick and check):
`+0x000` seed copy (8 bytes) · `+0x008` `rect[15]` `{x, y, w, h}` (16 bytes each) · `+0x0F8` table pointer ·
`+0x0FC` `dir[15]` · `+0x138` `dir0[15]` · `+0x174` `flip[15]` · `+0x1B0` `flip0[15]` · `+0x1EC` current index `i` ·
`+0x1F0` current entry's level id. A table entry is 16 bytes: `{+0 pick, +4 level, +8 anchor, +0xC anchor2}`. The
tables are 0xF0 bytes apart (15 entries), and level 0 ends one.

```c
// fn:sub_006772C0_LevelLinkBuild@0x006772C0 (trimmed). ESI = act, args table, check, after
memset(&B, 0, 500); B.seed = act.seed (copy); dir, dir0, flip, flip0 = -1 for all 15
for i while table[i].level: B.rect[i].w, h = leveldefs[level].SizeX/SizeY[act+0x450 diff]   // +0x0C / +0x18
i = 0
while (table[i].level):                                // backtracking
  B.i = i; B.level = table[i].level
  if (!table[i].pick(&B)) { dir, dir0, flip, flip0 [i] = -1; i--; continue }   // exhausted: back up one entry
  if (!check || check(&B, i)) i++                      // else: same i, the pick tries its next choice
for i:
  a1 = table[i].anchor  != -1 ? table[a1].level : 0;  a2 = table[i].anchor2 != -1 ? table[a2].level : 0
  L = LevelEnsure(act, table[i].level); L.rect (+0x1C..+0x28) = B.rect[i]
  if (L.drlg == 2): if (L.id == 1) L.data.idx = B.dir[i]; if (L.id == 40) L.data.idx = B.dir[i + 1]
  if (L.id == 6):                                      // level 27's preset index, on the act seed itself
    D = LevelEnsure(act, 27).data
    if (B.dir[i] == 1) D.idx = 2 - (step(act.seed) & 1); else if (B.dir[i] == 3) D.idx = ~step(act.seed) & 1
  if (after) after(..., B.dir)                         // Act I: LinkOutdoorFlags
  if (act.index /*+0x480*/ != 4):
    if (a1) { LevelLinkSet(L, a1, warp -1); LevelLinkSet(a1, L, warp -1) }      // a walkable seam both ways
    if (a2) { same with a2 }
```

- [C] The builder and its per-entry writes are as above. The `anchor2` field is −1 in all nine stock tables, so the second
  seam pair never fires. (fn:sub_006772C0_LevelLinkBuild@0x006772C0, data 0x006F0750–0x006F0FBF, run:2026-10-15-drlg-maze)
- [C] **Pick protocol.** The cycling picks test `dir0[i] = −1`. If it is −1, they draw on `B.seed`, store the choice in
  `dir0` and `dir` (and `flip0`/`flip`), and place. Otherwise they compute the next choice, return 0 if it equals the first
  one (leaving `dir` as it was), else store it and place. So an entry draws again only after a backtrack has reset it.
  Every `mod` is the signed `% n` of the compiler (`& 0x80000003` with a sign fix). (fn:sub_00676150_LinkPick@0x00676150,
  run:2026-10-15-drlg-maze)
- [I] Five picks never return 0: `LinkAnchor`, `LinkPickFixed`, `0x00676C00`, `0x0067D830` and `0x0067D8E0`. A check that
  rejected an anchor or the fixed pick would retry the same rect forever. The other three redraw on every call. No stock
  case was seen to reject them. (fn:sub_006760F0_LinkAnchor@0x006760F0, fn:sub_006768C0_LinkPickFixed@0x006768C0)
- [C] **No backtrack happened in the run.** Every reject (51 in the checked builds) was followed by the same entry's next choice, which a later
  check accepted. (run:2026-10-15-drlg-maze)

**The picks.** `P` = `rect[table[i].anchor]`, `w`/`h` = the entry's own size, `÷` a signed division by 2 (`(int)w / 2`).
"Reached" means some build ended on that choice, so its rect was checked (`LNKL`, `LNK1`). A choice tried and rejected is
checked only through the accept/reject sequence and stays inferred.

| Pick | Choice (draws on `B.seed`) | Position by choice | Reached | Tag |
|---|---|---|---|---|
| `0x006760F0` `LinkAnchor` | none; `dir` stays −1 | `(leveldefs OffsetX, OffsetY)` (`+0x24`, `+0x28` of `B.level`) | all anchors | C |
| `0x00676150` | first `d = lo & 3`; next `(d + 1) % 4` | 0 `(P.x − 16, P.y + P.h)`; 1 `(P.x − w, P.y − 16)`; 2 `(P.x + P.w − w + 16, P.y − h)`; 3 `(P.x + P.w, P.y + P.h − h + 16)` | 0 (105, 5), 2 (17, 3), 3 (106, 6); 2 also tried by 106 and 6, rejected | C 0, 2, 3 / I 1 |
| `0x00676280` | first `d = lo & 7`; next `(d + 1) % 8` | 0 `(P.x − 8 − w÷2, P.y + P.h)`; 1 `(P.x + w÷2 + 8, P.y + P.h)`; 2 `(P.x − w, P.y − h÷2 − 8)`; 3 `(P.x − w, P.y + h÷2 + 8)`; 4 `(P.x − 8 − w÷2, P.y − h)`; 5 `(P.x + w÷2 + 8, P.y − h)`; 6 `(P.x + P.w, P.y − h÷2 − 8)`; 7 `(P.x + P.w, P.y + h÷2 + 8)` | 2 (43, 44), 5 (42); 0 and 1 tried by 43, rejected | C 2, 5 / I others |
| `0x00676450` | first `d = lo & 3`, then `f = lo & 1` (two draws); next `d ← (d + f) % 4`, `f ← (f + 1) % 2`, exhausted when both equal `dir0`, `flip0` | `f` 1: 0 `(P.x, P.y + P.h)`; 1 `(P.x − w, P.y + 8)`; 2 `(P.x + P.w − w, P.y − h)`; 3 `(P.x + P.w, P.y + P.h − h − 8)`. `f` ≠ 1: 0 `(P.x + P.w − w, P.y + P.h)`; 1 `(P.x − w, P.y + P.h − h − 8)`; 2 `(P.x, P.y − h)`; 3 `(P.x + P.w, P.y + 8)` | `(d, f)` = (1, 0) | C (1, 0) / I others |
| `0x00676650` (Blood Moor) | as `0x00676450`; then, before the position, `w, h = 96, 56` for odd `d`, `56, 96` for even `d` | `f` 1: 0 `(P.x − 16, P.y + P.h)`; 1 `(P.x − w, P.y − 16)`; 2 `(P.x + P.w − w + 16, P.y − h)`; 3 `(P.x + P.w, P.y + P.h − h + 16)`. `f` ≠ 1: 0 `(P.x + P.w − w + 16, P.y + P.h)`; 1 `(P.x − w, P.y + P.h − h + 16)`; 2 `(P.x − 16, P.y − h)`; 3 `(P.x + P.w, P.y − 16)` | (1, 1); (0, 0), (0, 1), (1, 0) tried, rejected | C (1, 1) / I others |
| `0x006768C0` `LinkPickFixed` (Tamoe Highland) | `dir0 = dir = 0` on every call, no draw | `(P.x, P.y + P.h)` (cases 1–3 exist, unreachable) | 0 | C |
| `0x006769A0` (Rocky Waste) | first `d = (lo & 1) + 1`; next `d = (d == 1) ? 2 : 1` | 1 `(P.x − w, P.y)`; 2 `(P.x, P.y − h)` (cases 0, 3 unreachable) | 1 | C 1 / I 2 |
| `0x00676AE0` (Valley of Snakes) | first `d = lo & 7`; next `(d + 1) % 8` | 0, 1 `(P.x, P.y + P.h)`; 2, 3 `(P.x − w, P.y)`; 4, 5 `(P.x, P.y − h)`; 6, 7 `(P.x + P.w, P.y)` (paired case labels) | 3 | C 2, 3 (one case label) / I others |
| `0x00676C00` (Outer Steppes) | `dir0 = dir = 3`; a draw on every call | `lo & 1`: `(P.x + P.w, P.y + P.h − h + 8)` and `g_LinkPickOutdoorFlag = 0x800000`; else `(P.x + P.w, P.y − 8)` and `0x400000` | `lo & 1` = 0 (9 builds) | C even / I odd |
| `0x0067D830` (Rigid Highlands) | `b = lo & 1` on every call, `dir = dir0 = b` | `w, h = 64, 160` (`b` 0) or `160, 64`; `(P.x − w, P.y + P.h − h − 16)` | `b` 0 | C 0 / I 1 |
| `0x0067D980` (Arreat Plateau) | first `b = lo & 1`; next `b = (b == 0)` | size as above; `(P.x + T[k].x, P.y + T[k].y)`, `k = b + 2·dir[anchor]`, `T` = `g_LinkArreatOffsets` | `b` 0 with `dir[anchor]` 0 (`k` 0) | C `k` 0 / I others |
| `0x0067D8E0` (Tundra Wastelands) | `b = lo & 1` on every call, `dir = dir0 = b` | size as above; `(leveldefs OffsetX, OffsetY)` of `B.level` | `b` 0 (9 builds) | C 0 / I 1 |

(the pick functions; data 0x006F1F7C; run:2026-10-15-drlg-maze)

- [C] `g_LinkArreatOffsets` (`0x006F1F7C`, four `{dx, dy}` s32 pairs): `k` 0 `(0, −160)`, 1 `(−96, −64)`, 2 `(−64, −96)`,
  3 `(−160, 0)`. Arreat's anchor is Rigid Highlands, so `dir[anchor]` is Rigid's `b`. (data 0x006F1F7C,
  fn:sub_0067D980_LinkPick@0x0067D980)
- [C] **Act IV flag.** `ActLinkAct4` ORs `g_LinkPickOutdoorFlag` (`0x0096D66C`) into level 104's outdoor data (`+0x14`,
  dword 0) after its two builds (`0x00678A50`). Writer and reader agree. (fn:sub_00678A20_ActLinkAct4@0x00678A20,
  fn:sub_00676C00_LinkPick@0x00676C00)

**The validators.** `overlap(A, B)` is `RectGapTest(A, B, 0) == 0`: both per-axis gaps negative, as in drlg/0006 § 2.
`ECX` = `&rect[i]`, `EDX` = `&rect[j]` at every call.

```c
// plain (Act2A 0x00676F50, Act2B 0x00676FC0, Act4A 0x006770A0, Act4B 0x00677110, Act5C 0x00677030; first part of Act1A/1B)
a = table[i].anchor
for j in 0 ..< i: if (j != a && overlap(rect[i], rect[j])) return 0
// fn:sub_00676DD0_LinkCheckAct1A@0x00676DD0, table 0x006F0750
if (table[i].level == 1)  return g_LinkRogueSideOk[dir[i] + 4·flip[i] + 8·dir[a] + 32·flip[a]]   // current flip, not flip0
if (table[i].level == 17) for j in 0 ..< 15: if (j != i && table[j].anchor == a && dir[i] == dir[j]) return 0
return 1
// fn:sub_00676EB0_LinkCheckAct1B@0x00676EB0, table 0x006F0840
if (i != 0): rect[0].h += 200; rect[0].y -= 200; r = !overlap(rect[0], rect[i]); restore; return r
return 1
```

- [C] The plain test, for the rejects the checked builds made: 51, every one by overlap (Blood Moor 21, Far Oasis 14,
  City of the Damned 9, Black Marsh 7). (the five checks, run:2026-10-15-drlg-maze)
- [C] **Rogue Encampment** reads `g_LinkRogueSideOk` (`0x006F1158`, 64 s32, 0 or 1) at index
  `dir[i] + 4·flip[i] + 8·dir[a] + 32·flip[a]`, `a` = Blood Moor. The nonzero indices are 0, 1, 9, 19, 21, 24, 30, 31, 33,
  39, 41, 53, 54, 56, 62, 63. The 7 lookups in the checked builds were accepts at index 41 (Rogue Encampment (1, 0), Blood Moor (1, 1)),
  `0x00676E7B`–`0x00676EA1` (run:2026-10-15-drlg-maze). A 0 entry was never read, so a reject by the table is inferred
  only.
- [I] **Burial Grounds** rejects a side already taken by another child of its anchor. The walk runs `j` over all 15 slots
  (`cmp eax, 0x006F0848` at `0x00676E5F`), past the terminator. Slot 5 has anchor −1, slots 6–14 are zero (anchor 0 =
  Stony Field), and their `dir` is −1 after the reset, so the extra slots never match. Burial Grounds was never rejected in
  the checked builds. (fn:sub_00676DD0_LinkCheckAct1A@0x00676DD0, data 0x006F0750)
- [I] **Act1B widens rect[0] 200 tiles toward −y** (`add [esi+0x14], 200; add [esi+0xC], −200`, `0x00676F10`–`0x00676F1F`):
  `y` and `h` of rect[0], with rect[0] at `B+8`, so `+0xC` = `y` and `+0x14` = `h`. Rect[0] of `0x006F0840` is Moo Moo Farm
  (39). The model had widened `x`/`w` (west). It is now fixed to `y`/`h`, and the run still gives 0 mismatches, because the
  widening never decided a check (all 7 Act1B rejects were plain overlaps). (fn:sub_00676EB0_LinkCheckAct1B@0x00676EB0)

**The act functions** (disassembly of the pushes; `LevelBorderAdj` takes `EAX` = first level, args act and last level):

| Act | Calls, in order | Tag |
|---|---|---|
| I `0x00677750` | `Build(0x006F0750, Act1A, LinkOutdoorFlags)`; `Build(0x006F0840, Act1B, LinkOutdoorFlags)`; `LevelBorderAdj(1 … 17)` | C |
| II `0x00677790` | `Build(0x006F0930, Act2A, —)`; `Build(0x006F0A20, Act2B, —)`; `LevelBorderAdj(40 … 46)` | C |
| IV `0x00678A20` | `Build(0x006F0C00, Act4A, —)`; `Build(0x006F0CF0, Act4B, —)`; level 104 data `|= g_LinkPickOutdoorFlag`; `LevelBorderAdj(103 … 106)` | C |
| V `0x00678A70` | `Build(0x006F0DE0, —, —)`; `Build(0x006F0ED0, —, —)`; `LevelSeamsByTouch(111, 112)`; `LevelBorderAdj(111 … 112)`; `LevelSeamsByTouch(110, 111)`; `LevelSeamsByTouch(109, 110)`; `Build(0x006F0B10, Act5C, —)` | C |

(fn:sub_00677750_ActLinkAct1@0x00677750, fn:sub_00677790_ActLinkAct2@0x00677790, fn:sub_00678A20_ActLinkAct4@0x00678A20,
fn:sub_00678A70_ActLinkAct5@0x00678A70, run:2026-10-15-drlg-maze: the act seed at every build, the 69 link lists)

**Seams by touch.**

```c
// fn:sub_006775C0_LevelSeamsByTouch@0x006775C0. EBX = act, args lo, hi
for a in lo..hi: A = LevelEnsure(act, a); N = ActLevelLinksCopy(act, a)
  for b in lo..hi, b != a: Bv = LevelEnsure(act, b)
    if (RectTouch(&A.rect, &Bv.rect, -1)) LevelLinkSet(N, b, warp -1, slot -1)
// fn:sub_0066B880_RectTouch@0x0066B880. ECX = A, EDX = B, arg t
gx = (B.x < A.x) ? A.x - B.w - B.x : B.x - A.w - A.x;  gy likewise
t == 0:  return gx <= 0 && gy <= 0                  // touch or overlap
t != 0:  if (gx == 0 && gy <= t) return 1;  if (gy != 0) return 0;  return gx <= t
```

- [C] With `t` = −1 (its only use here) `RectTouch` is true when the rects share an edge segment: one gap 0 and the other
  negative. Touching corners (both gaps 0) and separated rects fail. Every pair test of the run was true (54: 36 with
  `gx = 0`, 18 with `gy = 0`), and the checked Act V link lists follow from them. (fn:sub_0066B880_RectTouch@0x0066B880, run:2026-10-15-drlg-maze)
- [I] The false branches of `RectTouch` and its `t = 0` mode were not exercised. (fn:sub_0066B880_RectTouch@0x0066B880)

**The link list.**

```c
// fn:sub_00642860_ActLevelLinksCopy@0x00642860. ECX = act, EDX = level id
for (N = act[+0x90]; N; N = N.next /*+0x44*/) if (N.level == id) return N
N = alloc; N.level = id; N.vis[0..7] = leveldefs[id] +0x48..+0x64; N.warp[0..7] = +0x68..+0x84
N.next = act[+0x90]; act[+0x90] = N                          // prepended
// fn:sub_00642920_LevelLinkSet@0x00642920. ECX = node, EDX = dest, args warp, slot
for k in 0..7: if (N.vis[k] == dest) { N.warp[k] = warp; return }    // the first match
if (slot == -1): slot = first k with N.vis[k] == 0 && N.warp[k] == -1
N.vis[slot] = dest; N.warp[slot] = warp
```

- [C] The node copy, the first-match update and the first-free-slot add are what the 69 link lists show.
  (fn:sub_00642860_ActLevelLinksCopy@0x00642860, fn:sub_00642920_LevelLinkSet@0x00642920, run:2026-10-15-drlg-maze)
- [I] With no free slot, `slot` stays −1 and the write lands on `N.level` and `N.vis[7]` (`in_ECX[slot + 1]`,
  `in_ECX[slot + 9]`). No stock level fills all 8 slots in the run. (fn:sub_00642920_LevelLinkSet@0x00642920)

**The tables** (entry: level ← anchor index, pick; `anchor2` −1 everywhere; data:g_ActLinkTables@0x006F0750, nine tables to 0x006F0FBF):

- [C] `0x006F0750`: Stony Field 4 (anchor), Cold Plains 3 ← 0 (`0x00676150`), Blood Moor 2 ← 1 (`0x00676650`), Rogue
  Encampment 1 ← 2 (`0x00676450`), Burial Grounds 17 ← 1 (`0x00676150`).
- [C] `0x006F0840`: Moo Moo Farm 39 (anchor), Monastery Gate 26 (anchor), Tamoe Highland 7 ← 1 (`0x006768C0`), Black Marsh
  6 ← 2, Dark Wood 5 ← 3 (`0x00676150`).
- [C] `0x006F0930`: Lut Gholein 40 (anchor), Rocky Waste 41 ← 0 (`0x006769A0`), Dry Hills 42, Far Oasis 43 and Lost City 44,
  each anchored on the previous entry (`0x00676280`), Valley of Snakes 45 ← 4 (`0x00676AE0`).
- [C] `0x006F0A20`: Canyon of the Magi 46 (anchor). `0x006F0CF0`: Chaos Sanctum 108 (anchor). `0x006F0B10`: Pandemonium
  Run 2 134, Tristram 136 (anchors).
- [C] `0x006F0C00`: Pandemonium Fortress 103 (anchor), Outer Steppes 104 ← 0 (`0x00676C00`), Plains of Despair 105 ← 1,
  City of the Damned 106 ← 2 (`0x00676150`).
- [C] `0x006F0DE0`: Harrogath 109 (anchor), Bloody Foothills 110 ← 0 (`LinkAnchor`: its `Levels` offsets), Rigid
  Highlands 111 ← 1 (`0x0067D830`), Arreat Plateau 112 ← 2 (`0x0067D980`). `0x006F0ED0`: Tundra Wastelands 117 (`0x0067D8E0`, no anchor).
- [C] The town index of level 1 is Rogue Encampment's `dir` (0–3). Lut Gholein's (40) is Rocky Waste's `dir`
  (`B.dir[i + 1]`, 1 or 2). Level 27's index is drawn on the act seed only when Black Marsh's `dir` is 1 or 3: Black Marsh
  ended on 3 in every checked build. Side 1 was never reached, so its formula is inferred only (`0x006774F9`). (fn:sub_006772C0_LevelLinkBuild@0x006772C0,
  run:2026-10-15-drlg-maze)

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

### 5. Phase 2 reproduction (run:2026-10-15-drlg-maze)

`tools/drlg.py` holds the one implementation of the act link builder (`Act`, `link_build`, `act_links`; Act I's outdoor
flags and the border lists included), which `tools/outdoor_replay.py` now imports (148 outdoor windows, 0 mismatches).
`drlg.py gen` checks it against the `LNK0`/`LNKL`/`LK27`/`LNK1`/`LNKS` lines and the warp side against `LWP` and `WPR`.

- [C] **Link builder.** 196 `LevelLinkBuild` calls (Acts I, II, IV, V; the three difficulties): the act seed at entry,
  the seed copy at exit, the 15 rects and the `dir`/`dir0`/second-axis/`flip0` arrays, the per-level rect writes, the town
  indices of levels 1 and 40, and the level-27 draw on the act seed (16 draws). The act's `LevelLinks` list after
  `ActLinkInit` matches the model in Acts I, II, IV and V (69 lists). (fn:sub_006772C0_LevelLinkBuild@0x006772C0,
  fn:sub_00678AD0_ActLinkInit@0x00678AD0, run:2026-10-15-drlg-maze)
- [C] **Level rects.** A level the builder does not place takes `sub_00642D10_LevelSetPosition`'s rect: `SizeX/SizeY` of the
  difficulty at `OffsetX/OffsetY`, plus the position of its `Depend` level (created first if needed). Level 27 sits at
  level 26's builder position + (0, −40). 218 maze levels' rects and the level 27 / 108 rects the maze reads match.
  (fn:sub_00642D10_LevelSetPosition@0x00642D10, tbl:Levels.txt:Depend, run:2026-10-15-drlg-maze)
- [C] **Room flags.** `DRLG_PresetMapScan` first fills the instance's room-flag grid with its `flags` argument (the
  `PresetRoomsCreate` flags) OR `0x10 << k` for each `Vis` slot `k` with `LevelWarpId` −1 (a walkable seam; this runs even
  when `Scan` and `Pops` are 0). Then, when `Scan` is set, the slot and waypoint bits of § 1 are added per 8×8 cell. 21728
  preset rooms' warp/waypoint bits (`0x30FF0`) match, 770 of them with DS1 slot or waypoint bits.
  (fn:DRLG_PresetMapScan@0x00667970, run:2026-10-15-drlg-maze)
- [C] **Warp points.** 389 builds: the level's room list is the `LevelRoomLink` order reversed, and the point list
  follows from the flags and the warp ids. The warp-slot bits of outdoor rooms (`DrlgType` 3, written by the outdoor
  generators) are taken from the log: 38 lists. In the run:2026-10-14-collision logs the predicted list replaces the logged
  one at 1392 `NearWarpTest` calls; at the 254 calls in levels 4 and 44 the outdoor-room point stays logged and the
  preset-room points are predicted in order. (fn:sub_006423D0_LevelWarpPointsBuild@0x006423D0, run:2026-10-15-drlg-maze)
- [C] **Pairing, corrected.** In `WarpPairLink`, the `k`-th slot of the destination that names the source back (`k` =
  earlier source slots naming the same destination) is tried first. If `WarpPairRoomFind` finds no room with that slot's
  bit, a second walk takes the first slot of the destination naming the source whose room exists. The paired room is the
  first room in the destination's list with the bit. 172 pairings: 162 by rank (32 at rank 1), 10 by the fallback
  (Durance 101 ↔ 100 and 101 ↔ 102, Ice caves). The Durance stairs records carry slot 2/3 or 0/1 by the side the
  finisher's rotation draw faced, so the slot a level ends up with depends on that draw. In seed 2027, 100's Prev took
  slot 2, and Travincal pairs with it by rank (83 slot 0 ↔ 100 slot 2). (fn:sub_0066C220_WarpPairLink@0x0066C220,
  fn:sub_0066BE80_WarpPairRoomFind@0x0066BE80, run:2026-10-15-drlg-maze)
- [C] **Basement 3 (54)** has no slot-2/3 bit: its NW and SE corner rooms take `File4` (drlg/0006 § 10), whose DS1s have no
  warp-slot cell, so its `Vis2`/`Vis3` = 0 never meets a room. (run:2026-10-15-drlg-maze)
- Boundaries (named in the record): Act III's rects and `LevelLinks` list (the jungle layout, drlg/0008), and the outdoor
  rooms' warp-slot bits. Both are modelled since plan 0026 Phase 2 ([drlg/0008 § 15](0008-outdoor.md#15-phase-2-reproduction-run2026-10-15-drlg-outdoor)):
  `drlg.py gen` predicts Act III's list and every out room's `+0x28` (grid0 `| 0x80000`), so the warp points of levels with
  out rooms are predicted too. (run:2026-10-15-drlg-outdoor)

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

## Plan 0038 batch S4a (2026-10-16)

Static batch S4a of [plan 0038](../../plans/0038-inferred-claims-sweep.md) (Phase 1), rows of
[inventory drlg-warps](../../plans/0038-inventory/drlg-warps.md). No new session. Checks: `python3 -I
tools/sweep_s4a.py <check>` over the kept logs. The addendum is the 2026-10-16 entry under run:2026-10-15-drlg-maze in
[experiments](experiments.md#run2026-10-15-drlg-maze).

Where a statement above is tagged inferred and this section raises it, the tag and the second source given here
are the current ones; the wording above is unchanged.

- [C] **Row 13 (§ 1: a preset room's warp-slot and waypoint bits come from `DRLG_PresetMapScan` whatever generator
  placed the preset).** The room flags that `tools/drlg.py gen` predicts from the DS1 scan are compared with the logged
  flags at every warp-point build (LWP). The logs are run:2026-10-12-drlg-gen, run:2026-10-15-drlg-maze,
  run:2026-10-15-drlg-outdoor and run:2026-10-15-acts-3-5, with 0 mismatches. Split by generator:
  - preset levels: 6120 rooms, 100 with a warp-slot bit and 184 with the waypoint bits;
  - maze rooms: 19 389 rooms, 805 and 163;
  - outdoor embedded presets: 65 052 rooms, 882 and 240.

  `sweep_s4a.py wgen`. (fn:DRLG_PresetMapScan@0x00667970, fn:sub_00666680_PresetRoomCreate@0x00666680,
  run:2026-10-15-drlg-maze, run:2026-10-15-drlg-outdoor)
- [C] **Row 18 (the warp unit).** `sub_0066E1C0_WarpUnitAdd` (decompiled again) makes `PresetUnitCreate(5, LvlWarp Id,
  mode 0, x, y)`. Here (x, y) is the cell's room-relative tile, ×5 (`TileToSubtile`), plus `OffsetX`/`OffsetY`
  (`+0x1C`/`+0x20`) of the LvlWarp row fitted to the cell's direction, unless the cell is on the room's last column or
  row. All 21 type-5 units of the server walks (RPU) were checked, in run:2026-10-13-drlg-preset and
  run:2026-10-15-acts-3-5. Each sits at a warp cell (orientation 10/11, main index below 8) of its room's preset
  instance, ×5 plus the offsets of a LvlWarp row whose Id is the unit's class and whose `Direction` fits the cell.
  `sweep_s4a.py warpunit`. (fn:sub_0066E1C0_WarpUnitAdd@0x0066E1C0, fn:sub_0066BF30_PresetUnitCreate@0x0066BF30,
  tbl:LvlWarp.txt:OffsetX, run:2026-10-13-drlg-preset)
- [C] **New reading for row 14, the Position-0 path.** `LevelPointFind` (`0x0066B2B0`) takes the point list
  (`LevelPointPick`, the slot-30–33 cells of § 1) only when the level's `Position` (leveldefs `+0x90`) is set. With
  `Position` 0 it calls `LevelWaypointRoom` (`0x0066AD80`). That function takes the first room of the level's list that
  passes the waypoint test, activates it, and scans its preset unit list (`+0x5C`) for the first type-2 object with
  id < `0x23D` and Objects `SubClass` bit `0x40`. The point is that unit's tile: `x / 5 +` the room's tile x, and the same
  for y. Without such a room it falls back to other room searches and the room centre. NearWarpTest's type-11 point
  (NWW) was compared in run:2026-10-14-collision and run:2026-10-15-objects:
  - all 26 distinct points of `Position`-0 levels whose waypoint object is logged (PRC DS1s, OPU0) are that object's
    tile;
  - the one `Position`-set point with a logged source (level 125) is a slot-33 cell.

  `sweep_s4a.py nww`. (fn:sub_0066B2B0_LevelPointFind@0x0066B2B0, fn:sub_0066AD80_LevelWaypointRoom@0x0066AD80,
  fn:sub_0066AC40_LevelPointPick@0x0066AC40, tbl:Levels.txt:Position, run:2026-10-14-collision, run:2026-10-15-objects)

Not raised:
- **Row 14 (§ 1: "the type-11 point that `LevelPointFind` uses is a slot-33 cell of a preset"): shortfall, and the claim
  is narrower than written.** It holds for levels with `Position` set: one case, and Tristram's point (5034, 1016) has
  no logged source. For `Position` 0 levels the point is the waypoint object's tile (above). So § 1's statement needs the
  `Position` split, and the spec statement (warps D1 L374) with it (backlog to the spec-writer). It stays inferred for
  `Position` levels. Also unexplained: 3 `Position`-0 points (levels 4, 44, 110) whose waypoint source is not in the
  log.
- **Row 16 (the caller is `RoomNeighboursEnsure`, once per warp bit, at activation; Warp −1 only marks): reclassified to
  (b), H5c.** The WPR logger sits inside `WarpPairRoomFind`, just before `RoomWarpNodeAdd`. So it logs successful pairings
  only. It records neither the caller nor the activation, nor the calls that end in the mark-only path. A first try at
  matching each source room's WPR slots with its warp bits as logged at the warp-point build (LWP) did not match
  one-to-one, and the kept lines cannot say why. Settling it needs a line at `RoomNeighboursEnsure` (`0x0066C370`): its
  room, its bits, each `WarpPairLink` call and its outcome. That is H5c's logger work.

## Plan 0038 batch H5c (run:2026-10-16-sweep-roomk, in progress)

Sessions 1–5 of [experiments.md § run:2026-10-16-sweep-roomk](experiments.md#run2026-10-16-sweep-roomk); `tools/drlg.py roomk`, 0 mismatches.

- [C] **`LevelRoomStateRestore`** ORs bit 0 into room `+0x60` from the array `LevelUnload` saved (keep mode), room by
  room in list order: 24 rebuilds with a saved array, 90 rooms whose bit it set; it changes nothing on a first build
  (107). (fn:sub_00642390_LevelRoomStateRestore@0x00642390, fn:sub_00642010_LevelUnload@0x00642010, run:2026-10-16-sweep-roomk)
- The warp exit (`0x005550B0`, WXP lines) is not reached yet: no session took a warp.

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
- What happens when a warp with no back-link (133 → 17) is used. This needs a harness run (not done in Phase 2: level
  133 is an uber level).
- ~~Act III's layout functions `0x00677880` and `0x00678910` (owner `drlg/outdoor`).~~ Read 2026-10-14 in
  [drlg/0008 § 10](0008-outdoor.md#10-act-iii-levels-7683-and-the-jungle-layout).
- The second argument of `WarpPairLink` and the marking function `0x0066BDA0` were not read in full.
