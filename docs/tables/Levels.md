# Levels (`data/global/excel/levels.txt` → `levels.bin` + `leveldefs.bin`)

> **Source archive:** patch_d2 (`levels.txt`, `levels.bin`, `leveldefs.bin`)   **Rows:** 137 (138 data rows − 1 `Expansion` marker at row 109)
> **Record:** `levels.bin` 544 B, `leveldefs.bin` 156 B
> **sha256:** `.txt` `34add892965a7b38f08c7346ffe7a41ede6668b9d5b28277493ddf157e55da0b`, `levels.bin` `4af188176b8830afa78ee5f31558e6fd3b6c4a6c77fd9b4016490611a18e0cba`, `leveldefs.bin` `eeb6a9a485cdb217007c3aee1c20a7974466f2966f5b2a6ff210e5555e18e77c`
> **Doc status:** columns listed, both `.bin` layouts complete, semantics pending

## Purpose

One row per level (area): act, size per difficulty, DRLG generator type and level type, visibility
and warp links, monster levels and densities, the monster pools (`mon*`, `nmon*`, `umon*`, critters),
object groups, names and the entry file. Read by `drlg/*`, `monsters/*` and seeding
(`rng` finding 0002 cites `leveldefs +0x30`/`+0x34`).

## Row identity

- `[C]` `Id` equals the data row index after dropping the marker (0..136) in every row, and is
  compiled into `levels.bin +0x000`. `Name` is not compiled.
- `[I]` **(corrected)** `Id` is compiled as a **u8** (descriptor type 4); `+0x001` is never written (0 in
  every record), so a reader of `+0x000` as a u16 sees the same values in stock data. ([data/0004](../findings/data/0004-cell-converters.md),
  tbl:Levels.txt:Id)
- `[C]` `levels.bin` and `leveldefs.bin` both have one record per row in the same order. Each
  `Levels.txt` column is in exactly one of them (`excel_bin.py diff` refuses a column mapped in both).

## leveldefs `+0x30` / `+0x34`

- `[C]` **`leveldefs +0x30` is `DrlgType`** (u32; values 0..3 on 1/70/35/31 rows) and
  **`+0x34` is `LevelType`** (u32, 0..35). Both match all 137 records; no other offset fits either column.
  The meaning of the `DrlgType` values (generator 1/2/3) is the reverser's (finding `rng/0002`).
  `[C]` The game's own `leveldefs` field descriptor maps the same two columns; its full column→offset
  list is in [data/0001 § Data touched](../findings/data/0001-excel-loader.md#data-touched).

## leveldefs `+0x68`: the warp ids

- `[C]` **`leveldefs +0x068..+0x087` is `Warp0..Warp7`**, 8 × s32 in column order (`+0x068 + 4·k` =
  `Warp`*k*). `excel_bin.py diff … leveldefs` matches all 137 × 8 cells, and a scan of every s32 offset of
  the 156-byte record finds exactly one that fits each column (`Warp0` takes 31 distinct values). This is the array drlg/0002 reads as "8 × s32 warp ids at
  leveldefs `+0x68`" (`sub_0066AEC0_LevelWarpIds`, `0x0066AEC0`), so its column names are confirmed.
- `[C]` Each cell is −1 (none, 860 cells) or a [LvlWarp](LvlWarp.md) `Id` (236 cells). All 236 resolve,
  and every one of the 83 LvlWarp `Id`s is named by at least one cell. 20 cells name an `Id` that has an
  `'l'` and an `'r'` row (the Act 5 pairs); the other 216 name an `Id` with one `'b'` row. 8 of the 236 are
  level 0 (`Null`), whose `Warp0..7` cells are all an explicit `0` in the `.txt` (and `Vis0..7` too), so
  228 cells on levels 1..136 name a warp ([§ Links survey](#links-survey-plan-0022-phase-0)).
- `[C]` A warp cell's bits 20–25 index this array, and the id found is looked up in LvlWarp by `Id` and
  `Direction`; the act's per-level override list (act `+0x90`) takes precedence when present
  ([drlg/0002 § Warp node of a cell](../findings/drlg/0002-room-build-draws.md), 0x0066AF30, 0x0061F310).

## Links survey (plan 0022 Phase 0)

`python3 -I tools/maze_survey.py workspace/merged/data/global/excel` §§ 3–4 (gate survey `maze`) prints the
`Vis0..7` resolution, the symmetry check with its exceptions, the per-slot `Vis`/`Warp` pairing and the full
pairing table (A, slot, B, `Warp`, the LvlWarp `Direction`s of that `Id`, B's slot back to A, B's `Warp`).
Every count is `[C]` by that command. The code meaning (`Warp`*k* pairs with `Vis`*k*) is in
[§ Code semantics of the links](#code-semantics-of-the-links-plan-0022-phase-1).

- `[C]` **Resolution.** A `Vis` cell is 0 or a `Levels` `Id`. 236 cells are non-zero on 116 levels, and all of
  them resolve (1..132). None is negative, and none names its own level. Per slot: `Vis0` 91, `Vis1` 67,
  `Vis2` 24, `Vis3` 21, `Vis4` 18, `Vis5` 7, `Vis6` 7, `Vis7` 1.
- `[C]` Slots are not filled from 0 up: 36 levels have a 0 slot before a set one (11 of them maze levels). The
  Act I wilderness levels 2–7, for example, leave `Vis0..2` at 0 and name their cave in `Vis3..6`.
- `[C]` 27 levels name a level in more than one slot:
  - wilderness 2–7 name their cave four times (`Warp` 0, 1, 2, 3), and Desert 1/2 name their tomb four times
    (33–36);
  - the Act II town (40 → 47), Sewer 1 A (47 → 40), Harem (50), Corrupt Harem (51), Basements 1–3 (52–54),
    Kurast 2/3 (80, 81 → 92), the Act III sewer (92 → 80 and 81), the six Act III temples (94–99) and Mephisto
    1–3 (100–102) name a level twice. Kurast 2 and 3 name level 92 with `Warp` 57 in both slots, and Basement
    1/2 name the next basement with `Warp` 32 in both.
- `[C]` **Cross-act.** One link only: level 133 (`Act 5 - Pandemonium 1`, Act V) `Vis0` → level 17
  (`Act 1 - Graveyard`, Act I), with `Warp0` 8 (`Act 1 Crypt Up`).
- `[C]` **Symmetry.** Of the 236 links (A names B), 235 have a link back (B names A). The one exception is that
  same 133 → 17: level 17 names only 18 and 19. Over the 235, the slot index is the same both ways in 12 links.
- `[C]` **`Vis`/`Warp` per slot**, over the 1088 slots of levels 1..136:

  | `Vis` | `Warp` | Slots |
  |---|---|---|
  | set | set | 228 |
  | set | −1 | 8 |
  | 0 | set | 0 |
  | 0 | −1 | 852 |

  The 8 `Vis`-without-`Warp` slots are four symmetric pairs: 26 ↔ 27 (Monastery, Courtyard 1), 27 ↔ 28
  (Courtyard 1, Barracks), 32 ↔ 33 (Courtyard 2, Cathedral) and 107 ↔ 108 (Lava 1, Diablo 1). Each pair has
  `Warp` −1 on both sides. Every other link has a `Warp` on both sides, and in all 227 such links the two
  `Warp` ids differ (e.g. Cave 1 → Wilderness 1 is `Warp` 4 `Act 1 Cave Up`, and Wilderness 1 → Cave 1 is 0–3).
- `[C]` **Maze levels:** 126 `Vis` links. Two have `Warp` −1: 28 → 27 (Barracks → Courtyard 1) and 107 → 108
  (Lava 1 → Diablo 1).
- `[C]` **LvlWarp `Direction` per `Id`.** Of the 83 `Id`s, 78 have one `'b'` record and 5 (71, 73, 74, 81, 82) have
  an `'l'` and an `'r'` record. The five are named by 20 cells, all on Act V levels (112–132: the Barricade, Ice
  Caves and Baal Temple stairs). The other 216 non-−1 cells name a `'b'` `Id` (8 of them are level 0's zeros). See also
  [LvlWarp § Row identity](LvlWarp.md#row-identity).

## Code semantics of the links (plan 0022 Phase 1)

From [drlg/0007](../findings/drlg/0007-warps.md) (static reading; nothing run in that phase).

- `[I]` **`Vis`*k* and `Warp`*k* pair by slot index.** A preset DS1 warp cell carries a slot *m* (bits 20–25,
  orientation 10/11). The room holding it gets flag `0x10 << m`, its destination is `Vis`*m* and its LvlWarp `Id` is
  `Warp`*m*, both read from the act's per-level override list (act `+0x90`) when the level has a node there, else from
  this row. (fn:sub_0066AF30_LevelWarpId@0x0066AF30, fn:sub_0066C040_LevelVisIds@0x0066C040,
  fn:sub_0066AEC0_LevelWarpIds@0x0066AEC0, fn:DRLG_PresetMapScan@0x00667970)
- `[I]` **`Warp` −1 with a `Vis` is a walkable seam, not a warp.** Outdoor levels turn each such slot into a
  level-adjacency node for their borders. The act link builder also writes −1 between each entry and its anchor
  (Acts I–IV) and between levels whose rectangles touch (Act III 75–83, Act V 109–112). Of the four data pairs without
  `Warp` (§ Links survey), 27↔28 and 107↔108 are joined by the maze code itself.
  (fn:sub_00677680_LevelBorderAdj@0x00677680, fn:sub_006772C0_LevelLinkBuild@0x006772C0,
  fn:sub_006775C0_LevelSeamsByTouch@0x006775C0)
- `[I]` **A repeated destination pairs by rank, without a draw.** When a room with slot *m* activates, the pairing
  counts the earlier slots of the source naming the same destination (*k*) and takes the *k*-th slot of the
  destination that names the source back. So a wilderness level naming its cave in four slots gets four distinct
  cave stairs, matched in slot order. (fn:sub_0066C220_WarpPairLink@0x0066C220,
  fn:sub_0066BE80_WarpPairRoomFind@0x0066BE80)
- `[I]` **The one asymmetric link, 133 → 17**, finds no back-link in the rank search or the fallback walk. What the
  game does when that warp is used is open (drlg/0007 § Open questions). (fn:sub_0066C220_WarpPairLink@0x0066C220)
- `[I]` `SizeX`/`SizeY` per difficulty size each level's rectangle in the act link builder, and anchor entries take
  `OffsetX`/`OffsetY` (drlg/0007 § 3). (fn:sub_006772C0_LevelLinkBuild@0x006772C0)
- `[C]` **`Depend` offsets a level by its `Depend` level's position** (plan 0022 Phase 2). A level the link builder
  does not place takes `sub_00642D10_LevelSetPosition`'s rect: `SizeX/SizeY` of the difficulty at `OffsetX/OffsetY`,
  plus the position of the `Depend` level, which is created first if needed. Two rows use it: 27 Courtyard 1
  (`Depend` 26, offset 0,−40) and 33 Cathedral (`Depend` 32, offset −4,−34). Level 27's rect at 26's builder position
  + (0, −40) is reproduced in run:2026-10-15-drlg-maze; level 33 was not logged and is `[I]` by the same reader.
  (fn:sub_00642D10_LevelSetPosition@0x00642D10, tbl:Levels.txt:Depend, run:2026-10-15-drlg-maze,
  [drlg/0007 § 5](../findings/drlg/0007-warps.md#5-phase-2-reproduction-run2026-10-15-drlg-maze))
- `[C]` Which slot each stock preset DS1 carries (Prev, Next, Down, …) is data:
  [LvlPrest § Warp slots](LvlPrest.md#warp-slots-plan-0022-phase-2).

## Outdoor survey (plan 0026 Phase 0)

`python3 -I tools/outdoor_survey.py workspace/merged [--act N]` § 1 (gate survey `outdoor`) lists the outdoor levels
(`DrlgType` 3) per **generator act**: the act whose `OutdoorAct*` function `sub_00675360_OutdoorLevelBuild` calls.
That act is the level's `Act`, except for level 134, which goes to the Act II generator
([drlg/0003](../findings/drlg/0003-generator-dispatch.md), `[I]`, fn:sub_00675360_OutdoorLevelBuild@0x00675360).
The survey's companion sections are [LvlPrest § Outdoor presets](LvlPrest.md#outdoor-presets-plan-0026-phase-0)
and [LvlSub § Outdoor survey](LvlSub.md#outdoor-survey-plan-0026-phase-0). Every count is `[C]` by that command.
The survey claims no column meaning; where `SizeX/Y` is overwritten by the link builder is in
[§ Outdoor sizes from the link picks](#outdoor-sizes-from-the-link-picks-plan-0026-phase-1) (drlg/0008).

`[C]` 31 outdoor levels use 8 level types. The cell grid is `SizeX / 8` × `SizeY / 8`, the division that
`OutdoorLevelBuild` makes (drlg/0003, `[I]`).

| Gen. act | Level | Name | `LevelType` | `SizeX`×`SizeY` | Cells | `OffsetX`,`OffsetY` | `SubType`/`SubTheme`/`SubWaypoint`/`SubShrine` |
|---|---|---|---|---|---|---|---|
| I | 2–7 | Wilderness 1–6 | 2 Act 1 - Wilderness | 80×80 | 10×10 | −1 (3, 4: 1000,1000) | 6 / 0,1,2,3,4,2 / 4 / 5 |
| I | 17 | Graveyard | 2 | 40×48 | 5×6 | −1 | −1 |
| I | 39 | Moo Moo Farm | 2 | 80×80 | 10×10 | 5000,1148 | −1 |
| II | 41–44 | Desert 1–4 | 16 Act 2 - Desert | 80×80 | 10×10 | −1 | 9 / 0..3 / 7 / 8 |
| II | 45 | Desert 5 | 16 | 32×32 | 4×4 | −1 | −1 / −1 / −1 / 8 |
| II | 46 | Valley of the Kings | 16 | 80×80 | 10×10 | 2500,1000 | 9 / 4 / 7 / 8 |
| II | 134 | Pandemonium 2 (Act V) | 16 | 80×80 | 10×10 | 4000,1700 | 9 / 4 / 7 / 8 |
| III | 76–78 | Jungle 1–3 | 21 Act 3 - Jungle | 64×192 | 8×24 | −1 | −1 |
| III | 79–81 | Kurast 1–3 | 22 Act 3 - Kurast | 80×64 | 10×8 | −1 | −1 |
| III | 82 | Kurast 4 | 22 | 48×16 | 6×2 | −1 | −1 |
| III | 83 | Travincal | 22 | 64×64 | 8×8 | −1 | −1 |
| IV | 104, 106 | Mesa 1, 3 | 27 Act 4 - Mesa | 80×64 | 10×8 | −1 | −1 |
| IV | 105 | Mesa 2 | 27 | 64×80 | 8×10 | −1 | −1 |
| IV | 108 | Diablo 1 | 28 Act 4 - Lava | 120×120 | 15×15 | 1500,1000 | −1 |
| V | 110 | Siege 1 | 30 Act 5 - Siege | 240×48 | 30×6 | 760,1000 | −1 |
| V | 111, 112 | Barricade 1, 2 | 31 Act 5 - Barricade | −1×−1 | — | −1 | 10 / 1 / −1 / −1 |
| V | 117 | Barricade Snow | 31 | 128×80 | 16×10 | 2000,1896 | 11 / 1 / −1 / −1 |

- `[C]` Per generator act: I 8 levels, II 7 (six Act II levels and level 134), III 8, IV 4, V 4.
- `[C]` `SizeX`, `SizeY` are the same in all three difficulties for all 31 levels. Every non-negative size is a
  multiple of 8.
- `[C]` **Barricade 1 and 2 (111, 112) have −1 in all six size cells and in `OffsetX/Y`.** Their size comes from
  the Act V link pick (§ Outdoor sizes from the link picks below).
- `[C]` `OffsetX/Y` is set on 8 of the 31 levels (3, 4, 39, 46, 108, 110, 117, 134). The others have −1, −1.
- `[C]` Four outdoor level types are also used by levels of another `DrlgType`: type 2 by the preset level 20
  (Tower 2), type 22 by the preset levels 94–99 and 102 and the maze levels 100–101, type 28 by the maze level 107
  (Lava 1), and type 31 by the preset levels 120–121.
- `[C]` Only Acts I, II and V carry `Sub*` values. Every Act III and Act IV level, Siege 1, the Graveyard and
  the Moo Moo Farm have −1 in all four columns, so `sub_006706A0_LvlSubRoll` returns without a draw for their out
  rooms ([drlg/0003](../findings/drlg/0003-generator-dispatch.md), `[I]`). Desert 5 has only `SubShrine`.
  Barricade 1, 2 and Barricade Snow have `SubType` and `SubTheme` but no `SubWaypoint` or `SubShrine`.

### Outdoor sizes from the link picks (plan 0026 Phase 1)

From [drlg/0008 § 8 and § 12 (a)](../findings/drlg/0008-outdoor.md#12-act-v-levels-110112-117-and-the-phase-0-answers):
`sub_006772C0_LevelLinkBuild` first gives each level its `SizeX/Y[difficulty]`, then a level's pick callback may
overwrite the size, and the builder writes the rect into the level. For four outdoor levels the size in this table is
therefore **not** the size generated:

| Level | `SizeX`×`SizeY` here | Generated size | Picked by | Tag |
|---|---|---|---|---|
| 2 Blood Moor | 80×80 | 56×96 or 96×56 (7×12 or 12×7 cells), by side parity | `sub_00676650_LinkPick` | C |
| 111 Barricade 1 | −1×−1 | 64×160 (bit 0) or 160×64 (bit 1), one act-seed-copy step, `b = lo & 1` | `sub_0067D830_LinkPick` | C |
| 112 Barricade 2 | −1×−1 | the same sizes, `b` drawn on the first call and flipped on a retry | `sub_0067D980_LinkPick` | C |
| 117 Barricade Snow | 128×80 | the same sizes, one draw; its `OffsetX/Y` still place it | `sub_0067D8E0_LinkPick` | C |

- `[C]` So every Barricade-type outdoor level is 8×20 or 20×8 cells; the replay derives every logged 111 and 112 rect
  from the link model (fn:sub_0067D830_LinkPick@0x0067D830, fn:sub_0067D980_LinkPick@0x0067D980, run:2026-10-12-drlg-gen).
  Level 117 is `[C]` since plan 0026 Phase 2: its 128×80 is overwritten by its link pick in the logged windows of
  run:2026-10-15-drlg-outdoor (fn:sub_0067D8E0_LinkPick@0x0067D8E0, run:2026-10-15-drlg-outdoor,
  [drlg/0008 § 12](../findings/drlg/0008-outdoor.md#12-act-v-levels-110112-117-and-the-phase-0-answers)).
- `[C]` Blood Moor's pick sets 56×96 or 96×56, not the row's 80×80 (fn:sub_00676650_LinkPick@0x00676650,
  run:2026-10-12-drlg-gen).
- `[I]` The dispatch then sets the grid to `w / 8` × `h / 8` cells of the generated size; no outdoor generator branches on
  difficulty, so the equal per-difficulty sizes of the § Outdoor survey table are not a lost distinction
  (fn:sub_00675360_OutdoorLevelBuild@0x00675360).

## Object population columns (plan 0023 Phase 1)

From [objects/0001 §§ 2–3, 7](../findings/objects/0001-object-population.md#2-the-gate). The slot loop is `[C]` by the
replay of run:2026-10-14-objects-window (architect ruling (1), plan 0023 log); the rest is `[I]`.

- `[C]` **`ObjGrp0..7`, `ObjPrb0..7`**: one room-seed draw per slot (always eight once the gate is open), the slot passing
  when `ObjGrp ≠ 0` and `r ≤ ObjPrb`; the group's member pick is in [ObjGroup § Code semantics](ObjGroup.md#code-semantics-plan-0023-phase-1).
  The level read is the room's own level id, while the gate and the counters use the population level.
  (fn:sub_00552610_RoomObjectsPopulate@0x00552610, tbl:Levels.txt:ObjPrb0, run:2026-10-14-objects-window)
- `[I]` **`Themes`** is a bit set: bit `t − 1` stands for theme number `t` = 1..7. When `Themes` ≠ 0 the gate draws
  `r = low mod 100` on the object-region seed against a threshold of 12 (+ 5 past half the level's rooms, + 5 more past
  three quarters); below it, it lists the set theme numbers, draws `i = RangeB(n)` and runs theme `list[i]` **only if
  that number is below `n`** (the count of set bits) and has a handler. (fn:OBJ_RoomThemeRoll@0x00552400,
  data:g_ObjThemeFns@0x00731E68, tbl:Levels.txt:Themes)
- `[I]` **Why stock values never fire.** The stock values are 8 (24 levels: themes {4}, n = 1), 48 (level 26: themes
  {5, 6}, n = 2) and 60 (14 levels: themes {3, 4, 5, 6}, n = 4). Only theme 3 of value 60 is below its `n`, and theme 3
  has no handler. So no theme runs on stock data; the roll still costs 1 or 2 object-region draws per gated room of
  those 39 levels. (Level counts from `levels.txt` `Themes`; tbl:Levels.txt:Themes)
- `[C]` **`MonLvl1` is read in every difficulty** (reproduced in Normal, Nightmare and Hell by run:2026-10-15-objects,
  [objects/0001 § 12](../findings/objects/0001-object-population.md#12-phase-2-the-bit-exact-run)) by the container rolls: `InitFn` 2 (urns, jars, baskets, and chests
  through `InitFn` 3) traps with chance `(MonLvl1/8 + 5)` %, and `InitFn` 3 locks a `Lockable` chest with chance
  `(MonLvl1/2 + 8)` %. It is the fixed column at `+0x010`, not the difficulty's `MonLvl2/3` or the `Ex` set, so
  nightmare and hell chests trap and lock at the normal-difficulty rates (Lower Kurast, `MonLvl1` 22: lock 19 %).
  (fn:OBJINIT_TrapByte@0x0054FBB0, fn:OBJINIT_Chest@0x0054FCB0, tbl:Levels.txt:MonLvl1, run:2026-10-15-objects)

## Travel (plan 0042 Phase 0)

The columns the waypoint, town-portal, act-travel and level-entry code is expected to read. Counts are
`python3 -I tools/travel_survey.py levels <excel-dir>` (the `SURVEY travel` line is a gate baseline); the meaning of a
column is `[I]` only where a finding names its reader, and Phase 1 of plan 0042 reads the rest.

| Column | Field | Range on stock data | Known reader | Tag (meaning) |
|---|---|---|---|---|
| `Act` | `levels` `+0x003` u8 | 0..4 | the act ranges of the waypoint menu tabs (table `0x007224AC`, per act) and the act change of `sub_0053AEC0_PlayerChangeLevel` compare acts; that they read this byte is not shown | `[L]` |
| `Waypoint` | `levels` `+0x0E4` u8 | 0..38 on 39 levels, 255 (none) on 98 | `WAYPOINT_IndexFromLevel` returns it, 255 = none; `WAYPOINT_LevelFromIndex` is its inverse | `[I]` (fn:WAYPOINT_IndexFromLevel@0x00660E00, fn:WAYPOINT_LevelFromIndex@0x00660D90) |
| `QuestFlag` | `leveldefs` `+0x000` u32 | 0; 11, 13, 21, 26, 39 on 24 levels | `OBJOP_Portal` (OperateFn 15): another player's town portal (class 59) to this level is refused unless the operator's quest word `QuestFlag` has bit 0 set (classic game), [quests/0002 § 6](../findings/quests/0002-travel.md#6-town-portals) | `[I]` (fn:OBJOP_Portal@0x00584870, 0x005849BB–0x00584A19) |
| `QuestFlagEx` | `leveldefs` `+0x004` u32 | equal to `QuestFlag` on every level but 39 (26 / 40) | the same test in an expansion game | `[I]` (fn:OBJOP_Portal@0x00584870) |
| `Portal` | `leveldefs` `+0x08C` u32 | 1 on 16 levels | none found: no read of `+0x8C` at the 28 `sub_0061E470_LevelDefGet` call sites ([quests/0002 § Dead ends](../findings/quests/0002-travel.md#dead-ends)) | `[I]` (no reader at those sites) |
| `Position` | `leveldefs` `+0x090` u32 | 1 on 18 levels | `LevelPointFind` takes the level point list when it is set, else the waypoint room's object (drlg/0005 § 9, drlg/0007); so it decides whether a placement steps the level seed (one draw on a `Position` level when a point of the type exists, none for type 13), for every placement through `ActLevelSpot` ([quests/0002 § 4](../findings/quests/0002-travel.md#4-placement-playerchangelevel-playerchangeact-actlevelspot)) | `[C]` (fn:sub_0066B2B0_LevelPointFind@0x0066B2B0, run:2026-10-14-collision); the seed step on every placement `[I]` |
| `SubWaypoint` | `leveldefs` `+0x040` s32 | 4 on levels 2–7, 7 on 41–44, 46, 134, −1 elsewhere (0 on level 0) | the `LvlSub` record of the cell `OutWaypointPlace` marks (drlg/0008 § 6) | `[I]` (fn:sub_00674B70_OutWaypointPlace@0x00674B70) |
| `Teleport` | `levels` `+0x004` u8 | 1 everywhere but level 0 (0) and Duriel's Lair 73 (2) | *plan 0046 readers:* skill do 52 (Dragon Flight), on its teleport branch, reads the byte through `LEVELS_GetRecord(RoomGetLevelId(the caster's room))`: 0 → the function returns 0 (no teleport); 2 → `0x006229F0(caster, x, y, 0x804)` decides (non-zero → 0, zero → the teleport); any other value → `UnitTeleport(game, caster; 0, x, y, 0, 0)` ([skills/0014 § 4](../findings/skills/0014-assassin.md#4-the-hits-and-the-finishing-moves-do-33-34-35-42-46-50-52); fn:sub_005D7850_SkillDo52DragonFlight@0x005D7850); that 0 forbids and 2 restricts a teleport is the reading | `[C]` the test and the calls (ADR-0021); `[I]` forbid / restrict |
| `IsInside`, `Quest` | `levels` `+0x008`, `+0x030` u8 | `Quest` 1 on level 8, 11 on level 74, 0 elsewhere | `Quest` is copied by the pool loader (monsters/pool) | `[L]` |

- `[C]` **Waypoint indices.** The 39 non-255 `Waypoint` cells are 0..38, each once, and run in act order: Act I
  0–8, Act II 9–17, Act III 18–26, Act IV 27–29, Act V 30–38, every index of an act below every index of the next.
  The town holds the first index of its act (0, 9, 18, 27, 30). Index *n* is bit *n* of a difficulty's waypoint field
  ([d2s.md § Waypoints](../formats/d2s.md#waypoints-ws); `[C]` for bits 2, 6, 8 and 16 by runs). Data:
  `wp_contiguous=1 wp_act_ordered=1 wp_town_first=1`. (tbl:Levels.txt:Waypoint)

  | Act | Indices | Levels in index order |
  |---|---|---|
  | I | 0–8 | 1 Rogue Encampment, 3, 4, 5, 6, 27, 29, 32, 35 |
  | II | 9–17 | 40 town, 48, 42, 57, 43, 44, 52, 74, 46 |
  | III | 18–26 | 75 town, 76, 77, 78, 79, 80, 81, 83, 101 |
  | IV | 27–29 | 103 town, 106, 107 |
  | V | 30–38 | 109 town, 111, 112, 113, 115, 123, 117, 118, 129 |

  The index order is not the level id order in Acts II and V (index 10 is Sewer 1 B, 48; index 35 is Temple 2, 123).
  By generator: 19 waypoint levels are outdoor (`DrlgType` 3), 13 maze (1), 7 preset (2).
- `[I]` **Towns are not a column.** The town test is a byte table in code over ids 1, 40, 75, 103, 109
  (fn:sub_006426A0_LevelIsTown@0x006426A0, drlg/0004); the act-entry hooks of `sub_0053AEC0_PlayerChangeLevel` name
  the same five ids ([save/0002 § 4](../findings/save/0002-quest-words.md)). All five have `Position` 1; `Portal` is 1 on
  the Act I and Act II towns only.
- `[C]` **`QuestFlag` / `QuestFlagEx` by data.** Non-zero on 24 levels: 11 on 50–54 and 74 (the Act II Harem,
  Palace cellars, Arcane Sanctuary), 13 on 46 and 66–73 (Canyon of the Magi, Tal Rasha's tombs, Duriel's Lair), 21 on
  100–102 (the Durance of Hate), 39 on 128–132 (the Worldstone Keep and Throne), and on level 39 (the cow level) 26 in
  `QuestFlag` and 40 in `QuestFlagEx`, the only row where the two differ. `[L]` 11, 13, 21 and 39 are quest-record
  words of the level's own act in `g_QuestDescs` (Act II words 8–14, Act III 16–22, Act V 35–40; save/0002), and the
  cow level's 26 / 40 (Acts IV and V) are the classic / expansion words the cow portal tests (items/0008 § 5.1, fn:CUBE_CowPortalOpen@0x00594140), so the
  pair reads as "the quest word that gates entry, classic / expansion". `[I]` The reader is the town-portal operate:
  for someone else's portal (class 59) the destination level's word (`QuestFlagEx` in an expansion game, else
  `QuestFlag`) must have bit 0 set, so another player's portal to the Durance needs word 21 bit 0, to the Arcane
  Sanctuary or the palace word 11; the portal's owner and anyone using the owner's own end are not tested
  ([quests/0002 § 6](../findings/quests/0002-travel.md#6-town-portals), fn:OBJOP_Portal@0x00584870). (tbl:Levels.txt:QuestFlag, tbl:Levels.txt:QuestFlagEx)
- `[C]` **`Portal` by data** is 1 on levels 1, 3, 5, 7, 27, 29, 33, 36, 40, 43, 45, 46, 53, 54, 74, 134: Acts I and
  II and Pandemonium 2, none in Acts III–V otherwise. `[I]` None of the 28 `LevelDefGet` call sites reads `+0x8C`, and no
  reader through `g_pLevelDefs` directly was found ([quests/0002 § Dead ends](../findings/quests/0002-travel.md#dead-ends)); a town portal opens in Act III–V field levels, so it is not a "portal allowed" switch.
  (tbl:Levels.txt:Portal)
- `[C]` **`Position`** is 1 on levels 1, 38, 40, 46, 54, 73, 74, 75, 102, 103, 109, 121, 125, 126, 127, 132, 134, 135.
  The waypoint-travel arrival (point type 13 on 46, 74, 133–136, else 0, `sub_00584F60_WaypointTravel`) goes through
  `LevelPointFind`, which reads it (drlg/0005 § 9). (tbl:Levels.txt:Position)
- `[C]` **`SubWaypoint`** is set on 12 outdoor levels; four of them have no `Waypoint` index (2 Blood Moor, 7 Tamoe
  Highland, 41 Rocky Waste, 134 Pandemonium 2). On those four the column is never applied: the `SubWaypoint` pass
  runs only on a room whose flag bits 16–17 `OutWaypointPlace` set, and the outdoor generators call
  `OutWaypointPlace` only on levels 3–6 and 42–44 (`[C]`, [drlg/outdoor](../specs/drlg/outdoor.md) Act I dispatch
  and I1, run:2026-10-15-drlg-outdoor; level 134's branch is `[I]`, never reached). Level 46 is the fifth level with
  the column set and no call; its waypoint (index 17) does not come from this pass. (tbl:Levels.txt:SubWaypoint,
  fn:sub_00674B70_OutWaypointPlace@0x00674B70, fn:sub_0067F980_OutdoorAct2@0x0067F980)

## Columns

`[C]` layout tags are by data behaviour: `python3 -I tools/excel_bin.py diff <excel-dir> levels` and `leveldefs` decodes every record and compares it with every mapped cell (blank cells and encoding rules as in [excel-bin.md](../formats/excel-bin.md#cell-encoding-rules)). A field is tagged `[C]` when the column's values pin its offset (a probe over every record finds no other offset that fits), `[I]` when the column is constant or identical to a sibling column, so its position comes from the neighbouring fields or the stride of its group. Widths are `[C]` with the same proviso; signedness is `[I]` (`s` where the column holds negative values). **Meaning:** no column semantics are claimed here; they come from reverser findings. The `.bin field` cell names the file.

| Column | Observed type / range | `.bin` field | References | Layout tag |
|---|---|---|---|---|
| `Name` | str, 137 distinct, len ≤ 27 | — (editor name; not in the record (rows are addressed by Id / row index)) | — | — |
| `Id` | int 0..136 (137 distinct) | `levels` `+0x000` u8 (`+0x001` never written) | — | [C] |
| `Pal` | int 0..4 (5 distinct) | `levels` `+0x002` u8 | — | [C] |
| `Act` | int 0..4 (5 distinct) | `levels` `+0x003` u8 | — | [C] |
| `QuestFlag` | int 11..39 (5 distinct), 113 blank | `leveldefs` `+0x000` u32 | — | [C] |
| `QuestFlagEx` | int 11..40 (5 distinct), 113 blank | `leveldefs` `+0x004` u32 | — | [C] |
| `Layer` | int 0..99 (100 distinct) | `leveldefs` `+0x008` u32 | — | [C] |
| `SizeX` | int -1..240 (25 distinct) | `leveldefs` `+0x00C` s32 | — | [I] |
| `SizeY` | int -1..200 (29 distinct) | `leveldefs` `+0x018` s32 | — | [I] |
| `SizeX(N)` | int -1..240 (25 distinct) | `leveldefs` `+0x010` s32 | — | [I] |
| `SizeY(N)` | int -1..200 (29 distinct) | `leveldefs` `+0x01C` s32 | — | [I] |
| `SizeX(H)` | int -1..240 (25 distinct) | `leveldefs` `+0x014` s32 | — | [I] |
| `SizeY(H)` | int -1..200 (29 distinct) | `leveldefs` `+0x020` s32 | — | [I] |
| `OffsetX` | int -4..5000 (13 distinct) | `leveldefs` `+0x024` s32 | — | [C] |
| `OffsetY` | int -40..3100 (45 distinct) | `leveldefs` `+0x028` s32 | — | [C] |
| `Depend` | int 0..32 (3 distinct) | `leveldefs` `+0x02C` u32 | `Levels` `Id`; the rect is offset by that level's position ([§ Code semantics of the links](#code-semantics-of-the-links-plan-0022-phase-1)) | [C] |
| `Teleport` | int 0..2 (3 distinct) | `levels` `+0x004` u8 | — | [C] |
| `Rain` | int 0..1 (2 distinct) | `levels` `+0x005` u8 | — | [C] |
| `Mud` | int 0..1 (2 distinct) | `levels` `+0x006` u8 | — | [C] |
| `NoPer` | int 0..1 (2 distinct) | `levels` `+0x007` u8 | — | [C] |
| `LOSDraw` | int 0..1 (2 distinct) | `leveldefs` `+0x098` u32 | — | [C] |
| `FloorFilter` | int 0..1 (2 distinct) | `levels` `+0x214` u32 | — | [C] |
| `BlankScreen` | int, always 1 | `levels` `+0x218` u32 | — | [I] |
| `DrawEdges` | int 0..1 (2 distinct) | `levels` `+0x009` u8 | — | [C] |
| `IsInside` | int 0..1 (2 distinct) | `levels` `+0x008` u8 | — | [C] |
| `DrlgType` | int 0..3 (4 distinct) | `leveldefs` `+0x030` u32 | — | [C] |
| `LevelType` | int 0..35 (36 distinct) | `leveldefs` `+0x034` u32 | — | [C] |
| `SubType` | int -1..11 (6 distinct) | `leveldefs` `+0x038` s32 | — | [C] |
| `SubTheme` | int -1..4 (6 distinct) | `leveldefs` `+0x03C` s32 | — | [C] |
| `SubWaypoint` | int -1..7 (4 distinct) | `leveldefs` `+0x040` s32 | — | [C] |
| `SubShrine` | int -1..8 (4 distinct) | `leveldefs` `+0x044` s32 | — | [C] |
| `Vis0` | int 0..131 (71 distinct) | `leveldefs` `+0x048` s32 | `Levels` `Id` (0 = none); slot 0's destination ([§ Code semantics of the links](#code-semantics-of-the-links-plan-0022-phase-1)) | [C] |
| `Vis1` | int 0..132 (60 distinct) | `leveldefs` `+0x04C` s32 | `Levels` `Id` (0 = none); slot 1's destination ([§ Code semantics of the links](#code-semantics-of-the-links-plan-0022-phase-1)) | [C] |
| `Vis2` | int 0..119 (25 distinct) | `leveldefs` `+0x050` s32 | `Levels` `Id` (0 = none); slot 2's destination ([§ Code semantics of the links](#code-semantics-of-the-links-plan-0022-phase-1)) | [C] |
| `Vis3` | int 0..101 (21 distinct) | `leveldefs` `+0x054` s32 | `Levels` `Id` (0 = none); slot 3's destination ([§ Code semantics of the links](#code-semantics-of-the-links-plan-0022-phase-1)) | [C] |
| `Vis4` | int 0..93 (18 distinct) | `leveldefs` `+0x058` s32 | `Levels` `Id` (0 = none); slot 4's destination ([§ Code semantics of the links](#code-semantics-of-the-links-plan-0022-phase-1)) | [C] |
| `Vis5` | int 0..70 (7 distinct) | `leveldefs` `+0x05C` s32 | `Levels` `Id` (0 = none); slot 5's destination ([§ Code semantics of the links](#code-semantics-of-the-links-plan-0022-phase-1)) | [C] |
| `Vis6` | int 0..71 (7 distinct) | `leveldefs` `+0x060` s32 | `Levels` `Id` (0 = none); slot 6's destination ([§ Code semantics of the links](#code-semantics-of-the-links-plan-0022-phase-1)) | [C] |
| `Vis7` | int 0..72 (2 distinct) | `leveldefs` `+0x064` s32 | `Levels` `Id` (0 = none); slot 7's destination ([§ Code semantics of the links](#code-semantics-of-the-links-plan-0022-phase-1)) | [C] |
| `Warp0` | int -1..81 (31 distinct) | `leveldefs` `+0x068` s32 | [LvlWarp](LvlWarp.md) `Id` (−1 = none) | [C] |
| `Warp1` | int -1..82 (31 distinct) | `leveldefs` `+0x06C` s32 | [LvlWarp](LvlWarp.md) `Id` (−1 = none) | [C] |
| `Warp2` | int -1..75 (15 distinct) | `leveldefs` `+0x070` s32 | [LvlWarp](LvlWarp.md) `Id` (−1 = none) | [C] |
| `Warp3` | int -1..66 (10 distinct) | `leveldefs` `+0x074` s32 | [LvlWarp](LvlWarp.md) `Id` (−1 = none) | [C] |
| `Warp4` | int -1..60 (9 distinct) | `leveldefs` `+0x078` s32 | [LvlWarp](LvlWarp.md) `Id` (−1 = none) | [C] |
| `Warp5` | int -1..42 (4 distinct) | `leveldefs` `+0x07C` s32 | [LvlWarp](LvlWarp.md) `Id` (−1 = none) | [C] |
| `Warp6` | int -1..43 (4 distinct) | `leveldefs` `+0x080` s32 | [LvlWarp](LvlWarp.md) `Id` (−1 = none) | [C] |
| `Warp7` | int -1..44 (3 distinct) | `leveldefs` `+0x084` s32 | [LvlWarp](LvlWarp.md) `Id` (−1 = none) | [C] |
| `Intensity` | int 0..140 (8 distinct) | `leveldefs` `+0x088` u8 | — | [C] |
| `Red` | int 0..255 (2 distinct) | `leveldefs` `+0x089` u8 | — | [I] |
| `Green` | int 0..255 (2 distinct) | `leveldefs` `+0x08A` u8 | — | [I] |
| `Blue` | int 0..255 (2 distinct) | `leveldefs` `+0x08B` u8 | — | [I] |
| `Portal` | int 0..1 (2 distinct) | `leveldefs` `+0x08C` u32 | — | [C] |
| `Position` | int 0..1 (2 distinct) | `leveldefs` `+0x090` u32 | — | [C] |
| `SaveMonsters` | int 0..1 (2 distinct) | `leveldefs` `+0x094` u32 | [§ Inactive-room save](#inactive-room-save-plan-0040-phase-1) | [C] |
| `Quest` | int 0..11 (3 distinct) | `levels` `+0x030` u8 | — | [C] |
| `WarpDist` | int 0..3900 (8 distinct) | `levels` `+0x00C` u32 | — | [C] |
| `MonLvl1` | int 0..50 (37 distinct) | `levels` `+0x010` u16 | [§ Object population columns](#object-population-columns-plan-0023-phase-1) (trap and lock chances) | [C] |
| `MonLvl2` | int 0..75 (38 distinct) | `levels` `+0x012` u16 | — | [C] |
| `MonLvl3` | int 0..93 (37 distinct) | `levels` `+0x014` u16 | — | [C] |
| `MonLvl1Ex` | int 1..50 (37 distinct), 8 blank | `levels` `+0x016` u16 | — | [C] |
| `MonLvl2Ex` | int 36..75 (33 distinct), 8 blank | `levels` `+0x018` u16 | — | [C] |
| `MonLvl3Ex` | int 67..87 (20 distinct), 8 blank | `levels` `+0x01A` u16 | — | [C] |
| `MonDen` | int 0..2200 (17 distinct) | `levels` `+0x01C` u32 | — | [C] |
| `MonDen(N)` | int 0..2200 (17 distinct) | `levels` `+0x020` u32 | — | [I] |
| `MonDen(H)` | int 0..2200 (17 distinct) | `levels` `+0x024` u32 | — | [I] |
| `MonUMin` | int 0..3 (4 distinct), 18 blank | `levels` `+0x028` u8 | — | [C] |
| `MonUMax` | int 0..3 (4 distinct), 18 blank | `levels` `+0x02B` u8 | — | [C] |
| `MonUMin(N)` | int 0..6 (7 distinct), 15 blank | `levels` `+0x029` u8 | — | [C] |
| `MonUMax(N)` | int 1..7 (7 distinct), 15 blank | `levels` `+0x02C` u8 | — | [C] |
| `MonUMin(H)` | int 0..10 (11 distinct), 15 blank | `levels` `+0x02A` u8 | — | [C] |
| `MonUMax(H)` | int 2..15 (11 distinct), 15 blank | `levels` `+0x02D` u8 | — | [C] |
| `MonWndr` | int 0..1 (2 distinct) | `levels` `+0x02E` u8 | — | [C] |
| `MonSpcWalk` | int 0..5 (3 distinct) | `levels` `+0x02F` u8 | — | [C] |
| `NumMon` | int 0..3 (3 distinct), 10 blank | `levels` `+0x032` u8 | — | [C] |
| `mon1` | str, 73 distinct, len ≤ 16, 11 blank | `levels` `+0x036` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `mon2` | str, 78 distinct, len ≤ 16, 11 blank | `levels` `+0x038` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `mon3` | str, 66 distinct, len ≤ 16, 26 blank | `levels` `+0x03A` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `mon4` | str, 42 distinct, len ≤ 13, 52 blank | `levels` `+0x03C` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `mon5` | str, 30 distinct, len ≤ 13, 86 blank | `levels` `+0x03E` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `mon6` | str, 10 distinct, len ≤ 11, 114 blank | `levels` `+0x040` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `mon7` | str, 4 distinct, len ≤ 12, 122 blank | `levels` `+0x042` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `mon8` | str, always 'bonefetish3', 134 blank | `levels` `+0x044` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `mon9` | always blank | `levels` `+0x046` u16 index (distinct-key ordinal) | `monstats:Id` | [I] |
| `mon10` | always blank | `levels` `+0x048` u16 index (distinct-key ordinal) | `monstats:Id` | [I] |
| `rangedspawn` | int, always 1, 117 blank | `levels` `+0x031` u8 | — | [C] |
| `nmon1` | str, 69 distinct, len ≤ 16, 11 blank | `levels` `+0x068` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `nmon2` | str, 75 distinct, len ≤ 14, 11 blank | `levels` `+0x06A` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `nmon3` | str, 74 distinct, len ≤ 16, 16 blank | `levels` `+0x06C` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `nmon4` | str, 60 distinct, len ≤ 16, 33 blank | `levels` `+0x06E` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `nmon5` | str, 48 distinct, len ≤ 14, 67 blank | `levels` `+0x070` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `nmon6` | str, 29 distinct, len ≤ 14, 95 blank | `levels` `+0x072` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `nmon7` | str, 19 distinct, len ≤ 12, 103 blank | `levels` `+0x074` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `nmon8` | str, 20 distinct, len ≤ 13, 114 blank | `levels` `+0x076` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `nmon9` | str, 18 distinct, len ≤ 16, 117 blank | `levels` `+0x078` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `nmon10` | str, 19 distinct, len ≤ 14, 117 blank | `levels` `+0x07A` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `umon1` | str, 71 distinct, len ≤ 16, 12 blank | `levels` `+0x09A` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `umon2` | str, 71 distinct, len ≤ 14, 15 blank | `levels` `+0x09C` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `umon3` | str, 63 distinct, len ≤ 14, 30 blank | `levels` `+0x09E` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `umon4` | str, 41 distinct, len ≤ 13, 53 blank | `levels` `+0x0A0` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `umon5` | str, 29 distinct, len ≤ 13, 87 blank | `levels` `+0x0A2` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `umon6` | str, 10 distinct, len ≤ 11, 115 blank | `levels` `+0x0A4` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `umon7` | str, 4 distinct, len ≤ 12, 123 blank | `levels` `+0x0A6` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `umon8` | str, always 'bonefetish3', 134 blank | `levels` `+0x0A8` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `umon9` | always blank | `levels` `+0x0AA` u16 index (distinct-key ordinal) | `monstats:Id` | [I] |
| `umon10` | always blank | `levels` `+0x0AC` u16 index (distinct-key ordinal) | `monstats:Id` | [I] |
| `cmon1` | str, 8 distinct, len ≤ 10, 43 blank | `levels` `+0x0CC` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `cmon2` | str, 3 distinct, len ≤ 6, 73 blank | `levels` `+0x0CE` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `cmon3` | str, always 'scorpion', 110 blank | `levels` `+0x0D0` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `cmon4` | str, always 'larva', 136 blank | `levels` `+0x0D2` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `cpct1` | int 2..100 (5 distinct), 43 blank | `levels` `+0x0D4` u16 | — | [C] |
| `cpct2` | int 30..100 (2 distinct), 73 blank | `levels` `+0x0D6` u16 | — | [C] |
| `cpct3` | int, always 20, 110 blank | `levels` `+0x0D8` u16 | — | [C] |
| `cpct4` | int, always 100, 136 blank | `levels` `+0x0DA` u16 | — | [C] |
| `camt1` | always blank | `levels` `+0x0DC` s16 (see below) | — | [I] |
| `camt2` | always blank | `levels` `+0x0DC` s16 (see below) | — | [I] |
| `camt3` | always blank | `levels` `+0x0DC` s16 (see below) | — | [I] |
| `camt4` | always blank | `levels` `+0x0DC` s16 (see below) | — | [I] |
| `Themes` | int 0..60 (4 distinct) | `levels` `+0x210` u32 | [§ Object population columns](#object-population-columns-plan-0023-phase-1) | [C] |
| `SoundEnv` | int 0..49 (48 distinct) | `levels` `+0x21C` u32 | — | [C] |
| `Waypoint` | int 0..255 (40 distinct) | `levels` `+0x0E4` u8 | — | [C] |
| `LevelName` | str, 127 distinct, len ≤ 27, 1 blank | `levels` `+0x0F5` char[40] | — | [C] |
| `LevelWarp` | str, 127 distinct, len ≤ 33, 1 blank | `levels` `+0x11D` char[40] | — | [C] |
| `EntryFile` | str, 129 distinct, len ≤ 5, 1 blank | `levels` `+0x145` char[40] | — | [C] |
| `ObjGrp0` | int 0..126 (30 distinct) | `levels` `+0x0E5` u8 | — | [C] |
| `ObjGrp1` | int 0..127 (27 distinct) | `levels` `+0x0E6` u8 | — | [C] |
| `ObjGrp2` | int 0..121 (20 distinct) | `levels` `+0x0E7` u8 | — | [C] |
| `ObjGrp3` | int 0..124 (18 distinct) | `levels` `+0x0E8` u8 | — | [C] |
| `ObjGrp4` | int 0..129 (10 distinct) | `levels` `+0x0E9` u8 | — | [C] |
| `ObjGrp5` | int 0..129 (7 distinct) | `levels` `+0x0EA` u8 | — | [C] |
| `ObjGrp6` | int 0..128 (3 distinct) | `levels` `+0x0EB` u8 | — | [C] |
| `ObjGrp7` | int 0..106 (2 distinct) | `levels` `+0x0EC` u8 | — | [C] |
| `ObjPrb0` | int 0..90 (24 distinct) | `levels` `+0x0ED` u8 | — | [C] |
| `ObjPrb1` | int 0..80 (23 distinct) | `levels` `+0x0EE` u8 | — | [C] |
| `ObjPrb2` | int 0..70 (22 distinct) | `levels` `+0x0EF` u8 | — | [C] |
| `ObjPrb3` | int 0..75 (17 distinct) | `levels` `+0x0F0` u8 | — | [C] |
| `ObjPrb4` | int 0..50 (9 distinct) | `levels` `+0x0F1` u8 | — | [C] |
| `ObjPrb5` | int 0..35 (4 distinct) | `levels` `+0x0F2` u8 | — | [C] |
| `ObjPrb6` | int 0..30 (3 distinct) | `levels` `+0x0F3` u8 | — | [C] |
| `ObjPrb7` | int 0..25 (2 distinct) | `levels` `+0x0F4` u8 | — | [C] |
| `Beta` | int 0..1 (2 distinct) | — (no field in levels.bin or leveldefs.bin matches it) | — | — |

Columns that equal their sibling in every row are ordered by header order `[I]`: `SizeX`/`SizeY` (all
three difficulties equal), `MonDen(N)`/`MonDen(H)`, and `Red`/`Green`/`Blue` (each row has all three 0
or all 255).
`mon9/10`, `umon9/10` are blank everywhere and placed by stride `[I]`.

- `[I]` **(corrected) `camt1..4` all write `+0x0DC`.** The level descriptor has four `camt` entries with the
  same offset (s16), so the compiler stores the **last `camt` column present** in `+0x0DC` and never writes
  `+0x0DE..+0x0E3`, while the critter code reads `camt` *k* at `+0x0DC + 2k` (`0x0046C524`). This doc placed
  `camt2..4` at `+0x0DE..+0x0E2` by stride before; the code contradicts that. Every stock cell is blank, so
  the six bytes are 0 and nothing differs in a stock run; a mod that fills `camt1..3` would see them
  lost (only `camt4` lands, in slot 0). ([data/0004](../findings/data/0004-cell-converters.md), 0x0046C524, tbl:Levels.txt:camt1)

### Fields with no `.txt` column

| file | offset | type | observed | tag |
|---|---|---|---|---|
| levels | `+0x001` | u8 | 0 in every record | `[I]` never written: `Id` is compiled as a u8 ([data/0004](../findings/data/0004-cell-converters.md)) |
| levels | `+0x00A` | u16 | 0 in every record | `[I]` padding: no descriptor entry, no writer found ([data/0004](../findings/data/0004-cell-converters.md)) |
| levels | `+0x033`, `+0x034`, `+0x035` | u8 × 3 | 0 in the file | `[C]` run-time counts written by `DRLG_LoadLevels`: the leading non-negative slots of `mon`, `nmon`, `umon` (25 each); the pool's candidate counts ([monsters/0001](../findings/monsters/0001-level-pool.md) § 3, fn:DRLG_LoadLevels@0x0061C540). The `umon` count `+0x035` is the `n` of the normal-difficulty special pick `L.umon[RangeB(room seed, n)]`; the 9 such picks of run:2026-10-13-mon-spawn reproduce only with it filled at load ([monsters/0002](../findings/monsters/0002-room-population.md) § 4, fn:sub_005BDE80_MonRegionPickClass@0x005BDE80) |
| levels | `+0x04A`..`+0x067`, `+0x07C`..`+0x099`, `+0x0AE`..`+0x0CB` | u16 × 15 each | `0xFFFF` in every record | `[I]` slots 11..25 of the `mon`, `nmon`, `umon` arrays (25 × u16 each; only 10 have columns) |
| levels | `+0x0DE`..`+0x0E3` | s16 × 3 | 0 | `[I]` never compiled (`camt` slots 1..3 as the critter code reads them, see above) |
| levels | `+0x16D`, `+0x20E`..`+0x20F` | 1 B, 2 B | 0 | `[I]` alignment ([data/0004](../findings/data/0004-cell-converters.md)) |
| levels | `+0x16E`, `+0x1BE` | `wchar[40]` each | 0 | `[I]` the localised `LevelName` and `LevelWarp` text, written by `DRLG_LoadLevels` after the load (the `+0x0F5`/`+0x11D` keys looked up in the string tables; 40 characters, last forced 0) ([data/0004](../findings/data/0004-cell-converters.md) § 3, fn:DRLG_LoadLevels@0x0061C540) |

## Monster pool columns (plan 0012 Phase 0)

What the data alone says about the columns the level's monster pool may read. Counts are by
`python3 -I tools/mon_survey.py levels <excel-dir>` over the 137 decoded `levels.bin` records; a
pool entry is looked up in `monstats.bin` as a record position (the stored distinct-`Id` ordinal,
[data/0001 §8](../findings/data/0001-excel-loader.md#8-answers-to-the-archivists-phase-1-questions)). Which
column set a difficulty or game type reads, and what each set feeds, is settled by
[monsters/0001](../findings/monsters/0001-level-pool.md) (plan 0012 Phase 1), cited per bullet below. Class columns are in [MonStats § Pool and level columns](MonStats.md#pool-and-level-columns-plan-0012-phase-0).

### The three pools and the slot arrays

- `[C]` `mon*`, `nmon*` and `umon*` are each a 25-slot u16 array (`+0x036`, `+0x068`, `+0x09A`); only
  slots 1..10 have `.txt` columns, and slots 11..25 hold `0xFFFF` in every record. A blank cell is `0xFFFF`
  too. (tbl:Levels.txt:mon1)
- `[C]` **`mon9`, `mon10`, `umon9` and `umon10` are blank in every row**, and `mon8`/`umon8` are set only
  in the three `Act 3 - Dungeon 2` levels (`bonefetish3`). `nmon9`/`nmon10` are used: 20 levels have ten
  `nmon` entries. Pool sizes (non-blank slots of 1..10): `mon` 0 ×11, 2 ×15, 3 ×26, 4 ×34, 5 ×28, 6 ×8,
  7 ×12, 8 ×3; `nmon` 0 ×11, 2 ×5, 3 ×17, 4 ×34, 5 ×28, 6 ×8, 7 ×11, 8 ×3, 10 ×20. (tbl:Levels.txt:mon9, tbl:Levels.txt:nmon10)
- `[C]` **`nmon` equals `mon` slot for slot in 117 levels.** The 20 that differ are all Act 5 levels
  (`Act` 4): `Siege 1`, the three Barricades, the six Ice Caves, `Temple 1`, `Temple 2`, `Temple Boss`,
  `Hell 1..3`, `Baal Temple 1..3` and `Throne Room`. `umon` equals `mon` in 110 levels; the 27 that
  differ include Acts 1–4 levels (`Wilderness 3`, `Desert 3`, `Mesa 1`, …). (tbl:Levels.txt:nmon1, tbl:Levels.txt:umon1)
- `[C]` A pool may repeat a class: 19 levels in `mon`, 21 in `nmon`, 18 in `umon`.
- `[C]` `rangedspawn` is 1 on 20 levels, all in Act 5 (the 20 whose `nmon` differs, less `Temple 1`, plus
  `Pandemonium 3`). (tbl:Levels.txt:rangedspawn)
- `[C]` Settled by [monsters/0001](../findings/monsters/0001-level-pool.md) (the pool is built once per game, at creation, for every level):
  `mon*` is read in normal, `nmon*` in nightmare and hell; the selector is `difficulty != 0` alone, so classic and
  expansion games read the same set. The candidates are the slots up to the first blank (the count at `+0x033` /
  `+0x034`). (fn:sub_005475E0_MonRegionPool@0x005475E0, tbl:Levels.txt:mon1, tbl:Levels.txt:nmon1, run:2026-10-12-mon-pool, run:2026-10-12-mon-pool-p2)
- `[C]` `NumMon` bounds the picks: `picks = min(NumMon, 13, candidates)`, each a uniform draw over the remaining
  slots, removed after the draw; a picked class is kept only if its MonStats `isSpawn` is set, and a dropped pick
  still counts. `rangedspawn` redraws the **first** pick up to 20 times until the class has MonStats `rangedtype`.
  ([monsters/0001](../findings/monsters/0001-level-pool.md) § 3, tbl:Levels.txt:NumMon, tbl:Levels.txt:rangedspawn, run:2026-10-12-mon-pool)
- `[C]` `umon*` gives the class of every random champion and unique **in normal difficulty only**: a uniform pick
  `umon[RangeB(room seed, n)]` over the `+0x035` count *n*, with no `spawn` substitution. In nightmare and hell the
  special's class is a second pool pick with substitution threshold 0. ([monsters/0001](../findings/monsters/0001-level-pool.md) § Answer,
  [monsters/0002](../findings/monsters/0002-room-population.md) § 4–§ 5, fn:sub_005BDE80_MonRegionPickClass@0x005BDE80, tbl:Levels.txt:umon1, run:2026-10-13-mon-spawn)

### Survey per difficulty

The per-difficulty table uses normal → `mon`, nightmare and hell → `nmon` (`[C]` above). "Over `NumMon`" counts pools with more
entries than `NumMon`; "disabled" counts pools naming a class whose `monstats` `enabled` bit is 0.

| Difficulty (pool) | `MonDen` = 0 | Empty pool | Empty pool with `MonDen` ≠ 0 | Pool over `NumMon` | Pool naming a disabled class |
|---|---:|---:|---:|---:|---:|
| normal (`mon`, `MonDen`) | 13 | 11 | 0 | 85 | 0 |
| nightmare (`nmon`, `MonDen(N)`) | 12 | 11 | 0 | 104 | 0 |
| hell (`nmon`, `MonDen(H)`) | 12 | 11 | 0 | 104 | 0 |

| Pool set | Empty | Over `NumMon` | Repeats a class | Naming a disabled class | Entries | Entries with `Rarity` 0 | Entries with `isSpawn` 0 |
|---|---:|---:|---:|---:|---:|---:|---:|
| `mon` | 11 | 85 | 19 | 0 | 540 | 3 | 3 |
| `nmon` | 11 | 104 | 21 | 0 | 686 | 3 | 3 |
| `umon` | 12 | 84 | 18 | 0 | 527 | 4 | 3 |

- `[C]` The 11 empty pools (`mon` and `nmon` alike) are *Null*, the five towns, `Act 1 - Tower 2`,
  `Act 2 - Harem`, `Act 5 - Temple Entrance`, `Act 5 - World Stone` and `Act 5 - Pandemonium Finale`, and they
  are exactly the 11 levels with `NumMon` 0 (10 blank, `Pandemonium Finale` an explicit 0). `umon` is also
  empty in `Act 5 - Siege 1`. (tbl:Levels.txt:NumMon)
- `[C]` `NumMon` is 3 on 125 levels and 2 on one (`Act 5 - Siege 1`). 85 of the 126 non-empty `mon`
  pools and 104 of the 126 non-empty `nmon` pools hold more classes than `NumMon`, so (since `NumMon` bounds the
  picks, above) a pick among the candidates happens in most levels.
- `[C]` `MonDen` = 0 with a non-empty pool: `Act 5 - Siege 1` (normal only) and `Act 5 - Mountain Top`
  (all three). *Mountain Top*'s pool is the three `ancientbarb*` classes, the only pool entries with
  `Rarity` 0 and `isSpawn` 0 (the fourth `Rarity` 0 `umon` entry is `baaltaunt` in `Act 5 - Temple 2`).
- `[C]` No pool, critter, minion or `spawn` cell names a class with `enabled` 0 (the 31 disabled
  `monstats` records are listed in MonStats). The 723 entry of `Pandemonium 3` (`mon1`, `nmon1`, `umon1`) is
  the one entry whose record position (second `cr_lancer8`) and distinct `Id` (`overseer6`) differ.

### Per-difficulty columns and their blanks

- `[C]` `MonDen`, `MonDen(N)`, `MonDen(H)` are never blank. `MonUMin`/`MonUMax` are blank in 18 rows,
  their `(N)`/`(H)` columns in 15; three rows set `(N)`/`(H)` with a blank normal pair: `Act 1 - Wilderness 1`,
  `Act 2 - Valley of the Kings` and `Act 5 - Pandemonium 2`. A blank stores 0. (tbl:Levels.txt:MonUMin)
- `[C]` `MonLvl1..3` are never blank; `MonLvl1Ex..3Ex` are blank (stored 0) in the same 8 rows: *Null*,
  the five towns, `Act 1 - Tower 2` and `Act 2 - Harem`. (tbl:Levels.txt:MonLvl1Ex)
- `[I]` `MonLvl1..3` / `MonLvl1Ex..3Ex` are indexed by difficulty, and the `Ex` set is used when game
  `+0x70` (expansion) is non-zero (fn:sub_0061DCA0_LevelMonLvl@0x0061DCA0, [items/0001](../findings/items/0001-tc-resolution.md)).
- A spawned monster's level: in an **expansion** game in nightmare or hell, `MonLvl2Ex`/`MonLvl3Ex` of the
  monster's level, unless the class has MonStats `noRatio` or `boss` or is a hireling; otherwise (normal
  difficulty, any classic game) the class's MonStats `Level`/`Level(N)`/`Level(H)`. `MonLvl1..3` (classic) are
  not read for a monster level. ([monsters/0001](../findings/monsters/0001-level-pool.md) § 5, fn:sub_00573CB0_MonStatsInit@0x00573CB0, tbl:Levels.txt:MonLvl1Ex, run:2026-10-12-mon-pool-p2)
  - `[C]` for the logged cases: expansion nightmare/hell (`MonLvlEx`), classic nightmare/hell (MonStats, so
    `MonLvl2/3` not read there), expansion normal (MonStats), a `noRatio` class (MonStats) and hireling 271
    (`d` = 0).
  - `[I]` for the cases no run logged: the other hirelings (338, 359, 560, 561), classic normal (and so `MonLvl1`
    not being read), the `boss` arm and the no-level-record fallback (level 1).
- `[I]` The monster region copies `MonLvl*`/`MonLvl*Ex` (by game type) but never reads it back. ([monsters/0001](../findings/monsters/0001-level-pool.md) § 2)
- `[C]` `MonDen`/`MonDen(N)`/`MonDen(H)` is copied into the level's region by difficulty, and `MonUMin`/`MonUMax`
  likewise ([monsters/0001](../findings/monsters/0001-level-pool.md) § 2, run:2026-10-12-mon-pool). `[I]` A room is populated only when that `MonDen` is non-zero, so
  *Mountain Top* and *Siege 1* in normal get no random population whatever their pool. ([monsters/0001](../findings/monsters/0001-level-pool.md) § 6, fn:sub_0054EBC0_RoomPopulateGate@0x0054EBC0, tbl:Levels.txt:MonDen)
- `[C]` The density: each spawn-box attempt of the population pass goes on when a game-seed roll gives
  `low mod 100000 ≤ min(MonDen, 10000)`. ([monsters/0002](../findings/monsters/0002-room-population.md) § 3, fn:sub_0054EC90_RoomPopulate@0x0054EC90, run:2026-10-13-mon-spawn)

### Critters (`cmon1..4`, `cpct1..4`, `camt1..4`)

- `[C]` 94 levels name at least one critter. Every named `cmon` slot has a non-zero `cpct`, and no `cpct`
  is set without its `cmon`. `camt1..4` are blank (0) in every row. Values of `cpct` on named slots: 30 ×139,
  20 ×34, 100 ×9, 2 ×3, 3 ×1. Classes by slot: `cmon1` `rat` 68, `snake` 8, `scorpion` 7, `bunny` 4, `bat` 3,
  `minispider` 2, `chicken` 1, `bug` 1; `cmon2` `bat` 54, `parrot` 8, `rat` 2; `cmon3` `scorpion` 27;
  `cmon4` `larva` 1. (tbl:Levels.txt:cmon1, tbl:Levels.txt:cpct1)
- `[C]` Four levels have critters and an empty pool: `Act 1 - Town`, `Act 1 - Tower 2`, `Act 2 - Town`,
  `Act 2 - Harem`.
- `[C]` Critters are a separate, client-side draw per client room from the room seed, not from the pool. For each
  `cmon` slot until a negative one: a percent roll against `cpct` (one per slot per room), then a count
  `RangeB(MaxGrp − MinGrp) + MinGrp` from the class's MonStats record (so `MaxGrp` is never reached when they
  differ), multiplied by `camt` when non-zero (`camt` *k* read at `+0x0DC + 2k`, of which only slot 0 is
  ever compiled, see [Columns](#columns)). The `cmon` value is a MonStats record position; no critter flag is
  tested. ([monsters/0001](../findings/monsters/0001-level-pool.md) § 7, fn:sub_0046C460_ClientCritters@0x0046C460, tbl:Levels.txt:cmon1, tbl:Levels.txt:cpct1, tbl:Levels.txt:camt1, run:2026-10-12-mon-pool)

### Spawn survey per difficulty (plan 0014 Phase 0)

The inputs of the room population pass (`monsters/spawn`), by `python3 -I tools/mon_survey.py spawn <excel-dir>`
over the decoded `levels.bin` and `monstats.bin`. Same pool mapping as above (normal → `mon`, nightmare and
hell → `nmon`). "Pool classes" are the distinct classes named by the difficulty's pool of a level whose `MonDen`
for that difficulty is non-zero. Meanings of the MonStats columns are in
[MonStats § Spawn columns](MonStats.md#spawn-columns-plan-0014-phase-0); what the pass does with them is
[monsters/0002](../findings/monsters/0002-room-population.md) (plan 0014), linked below and there.

| | normal | nightmare | hell |
|---|---:|---:|---:|
| levels with `MonDen` 0 | 13 | 12 | 12 |
| levels with `MonDen` ≠ 0 | 124 | 125 | 125 |
| `MonDen` values (non-zero) | 325..2200 | 325..2200 | 325..2200 |
| pool classes | 240 | 342 | 342 |
| `MinGrp` range / `MaxGrp` range | 1..7 / 1..10 | 1..7 / 1..10 | 1..7 / 1..10 |
| `PartyMin` range / `PartyMax` range | 0..4 / 0..8 | 0..4 / 0..8 | 0..4 / 0..8 |
| classes with `PartyMax` > 0 / `minion1` / `minion2` | 36 / 36 / 3 | 55 / 55 / 5 | 55 / 55 / 5 |
| classes with `spawn` / `placespawn` / both | 12 / 3 / 3 | 15 / 3 / 3 | 15 / 3 / 3 |
| classes with `SetBoss` / `BossXfer` | 27 / 19 | 42 / 28 | 42 / 28 |
| distinct (`MonUMin`, `MonUMax`) pairs | 6 | 11 | 18 |
| levels with `MonUMin` > `MonUMax` | 0 | 0 | 0 |

- `[C]` `MonDen` 0: the 12 levels *Null*, the five towns, `Act 1 - Tower 2`, `Act 2 - Harem`, `Act 5 - Mountain Top`,
  `Act 5 - Temple Entrance`, `Act 5 - World Stone`, `Act 5 - Pandemonium Finale` in every difficulty, plus
  `Act 5 - Siege 1` in normal only (its `MonDen(N)`/`MonDen(H)` are 650). On every other level the three
  `MonDen` columns are equal: 136 of 137 levels have one value for all difficulties. (tbl:Levels.txt:MonDen)
- `[C]` `MonDen` values on the populated levels (normal): 2200 ×19 (the act 2 tombs, cellars and *Duriel's Lair*,
  plus `Act 2 - Corrupt Harem 1`), then 700 ×18, 680 ×13, 800 ×13, 600 ×12, 990 ×10, 520 ×8, 650 ×7, 880 ×7,
  325 ×5, 1024 ×5, 1056 ×3, and 350, 450, 550, 720 once each.
- `[C]` `MonUMin`/`MonUMax` pairs on the populated levels, as (min, max) ×levels:
  - normal: (0,0) ×13, (0,1) ×42, (0,2) ×12, (1,1) ×9, (1,2) ×47, (2,3) ×1;
  - nightmare: (0,0) ×4, (0,1) ×4, (0,2) ×1, (1,2) ×15, (2,3) ×16, (3,4) ×34, (3,5) ×2, (4,5) ×16, (4,6) ×28,
    (5,6) ×3, (6,7) ×2;
  - hell: (0,0) ×4, (0,2) ×1, (1,2) ×4, (2,2) ×7, (2,3) ×7, (3,3) ×1, (3,4) ×9, (4,5) ×7, (4,6) ×1, (5,5) ×2,
    (5,6) ×5, (5,7) ×6, (6,7) ×6, (6,8) ×28, (7,9) ×28, (8,10) ×3, (9,11) ×3, (10,15) ×3.
  The populated levels with (0,0) in nightmare and hell are `Act 1 - Cave 1`, `Act 1 - Graveyard`,
  `Act 2 - Corrupt Harem 1` and `Act 5 - Temple Boss`; normal adds the three blank normal pairs (`Wilderness 1`,
  `Valley of the Kings`, `Pandemonium 2`) and six Act 5 temple and throne levels. (tbl:Levels.txt:MonUMin, tbl:Levels.txt:MonUMax)
- `[C]` What the pair does (`SpawnTypeRoll`, per successful attempt, compared with the level's live special count
  `+0x2C8`): below `MonUMin`, an attempt is special with probability `⌊100·visited/rooms⌋/100`; below `MonUMax`, with a
  flat 6 %. With (0,0) both tests are skipped, so such a level gets **no random champions or uniques**; preset and
  superunique placements are separate. ([monsters/0002](../findings/monsters/0002-room-population.md) § 4, fn:sub_005BE020_SpawnTypeRoll@0x005BE020, run:2026-10-13-mon-spawn)
- `[C]` `umon` (normal champions and uniques, [monsters/0001](../findings/monsters/0001-level-pool.md) § 6):
  234 distinct classes on the populated levels, with the same `MinGrp`/`MaxGrp` and `PartyMin`/`PartyMax` ranges
  as `mon`; 35 have `minion1`, 9 `spawn`, none `placespawn`.
- `[C]` `MonWndr` and `MonSpcWalk` have one column for all difficulties and are never blank. `MonWndr` is 1 on
  113 levels and 0 on 24. The levels with `MonWndr` 0 and a non-zero normal `MonDen` are `Act 1 - Cave 1`, `Act 1 - Tristram`, the three
  Act 5 barricades and the seven Act 5 temple and throne levels; `Act 1 - Tower 2` has `MonWndr` 1 with `MonDen` 0.
  (tbl:Levels.txt:MonWndr)
- `[C]` `MonSpcWalk` is non-zero on 10 levels, all populated: 1 on `Act 1 - Jail 1..3` and `Act 2 - Basement 1..3`,
  5 on `Act 3 - Jungle 1..3` and `Act 4 - Lava 1`. (tbl:Levels.txt:MonSpcWalk)
- `[I]` `MonWndr` (`levels.bin` `+0x2E`) is copied into the level's monster region at game creation
  ([monsters/0001](../findings/monsters/0001-level-pool.md) § 2), and that copy (`+0x2BE`) is never read. The only
  other reader is the wanderer tick, which reads the Levels record: on `low & 0x7FFF = 0` with `MonWndr` ≠ 0 it may
  spawn one wanderer, and only Act I has a wanderer class (`rogue2`). `[C]` At run time, over three games, the only
  access to the byte was the region-build read. ([monsters/0002](../findings/monsters/0002-room-population.md) § 7, fn:sub_0054F060_RoomWandererTick@0x0054F060, run:2026-10-13-mon-spawn)
- `[I]` `MonSpcWalk` (`+0x2F`) is read only by a pathing helper that re-targets a monster when the value is non-zero
  and below a path distance; it plays no part in spawning. ([monsters/0002](../findings/monsters/0002-room-population.md) § 7, fn:sub_005B13E0_MonSpcWalkCheck@0x005B13E0)
- `[C]` `WarpDist` (`+0x00C`) keeps random groups away from warps: the spawn-point pick, with `avoidWarp` (every
  random group and special), rejects a point whose squared distance in subtiles to a room warp point, or to the
  level's type-11 point, is below `WarpDist`. ([monsters/0002](../findings/monsters/0002-room-population.md) § 6, fn:sub_0054DC40_SpawnPosPick@0x0054DC40, run:2026-10-13-mon-spawn)

## Inactive-room save (plan 0040 Phase 1)

- `[I]` `SaveMonsters` (leveldefs `+0x94`) is read by `sub_00642820_LevelSaveMonsters`, the starting value of the save
  test for a monster and for an object of a room being released: a monster's `save` starts as `SaveMonsters` of its
  level (or unit `+0xC4` bit `0x2000000`), an object's as `SaveMonsters` or its preset flag; later tests can still veto
  it ([MonStats2 § Inactive-room save](MonStats2.md#inactive-room-save-plan-0040-phase-1),
  [States § Interpretation notes](States.md#interpretation-notes)). (fn:sub_00642820_LevelSaveMonsters@0x00642820,
  fn:sub_005431F0_InactiveMonsterSaveTest@0x005431F0, fn:sub_005433F0_InactiveUnitSaveTest@0x005433F0,
  tbl:Levels.txt:SaveMonsters; [drlg/0009 § 5](../findings/drlg/0009-room-lifecycle.md#5-the-inactive-records))
- `[C]` By data, `SaveMonsters` is 0 only for levels 0 (the null level), 1, 40, 75, 103 and 109 (the five towns) and 50 (the Harem) and 1 for
  every other level (`levels.txt` read by script, tbl:Levels.txt:SaveMonsters).

## Record layouts

`levels.bin` (544 B): `+0x000` `Id` u8, `Pal`, `Act`, `Teleport`, `Rain`, `Mud`, `NoPer`, `IsInside`,
`DrawEdges` (u8) · `+0x00C` `WarpDist` u32 · `+0x010` `MonLvl1..3`, `MonLvl1Ex..3Ex` u16 · `+0x01C`
`MonDen` ×3 u32 · `+0x028` `MonUMin` ×3, `MonUMax` ×3, `MonWndr`, `MonSpcWalk`, `Quest`,
`rangedspawn`, `NumMon` (u8) · `+0x036` `mon[25]`, `+0x068` `nmon[25]`, `+0x09A` `umon[25]` (u16
monster ordinals) · `+0x0CC` `cmon1..4`, `cpct1..4` (u16), `+0x0DC` `camt` (s16, all four columns),
`+0x0DE..+0x0E3` never compiled · `+0x0E4` `Waypoint`,
`ObjGrp0..7`, `ObjPrb0..7` (u8) · `+0x0F5` `LevelName`, `+0x11D` `LevelWarp`, `+0x145` `EntryFile`
(`char[40]`) · `+0x16E`, `+0x1BE` localised text (`wchar[40]`, filled at load) · `+0x210` `Themes`,
`FloorFilter`, `BlankScreen`, `SoundEnv` (u32).

### leveldefs.bin (156 B)

`+0x000` `QuestFlag`, `QuestFlagEx`, `Layer` · `+0x00C` `SizeX`, `SizeX(N)`, `SizeX(H)`, `SizeY` ×3 ·
`+0x024` `OffsetX`, `OffsetY`, `Depend` · `+0x030` `DrlgType` · `+0x034` `LevelType` · `+0x038`
`SubType`, `SubTheme`, `SubWaypoint`, `SubShrine` · `+0x048` `Vis0..7` · `+0x068` `Warp0..7` (all u32 /
s32) · `+0x088` `Intensity`, `Red`, `Green`, `Blue` (u8) · `+0x08C` `Portal`, `Position`,
`SaveMonsters`, `LOSDraw` (u32). No unknown bytes.

## Open questions

- Answered `[I]`: monster references (`mon*`/`nmon*`/`umon*`) are used as record positions, so after
  the duplicate `cr_lancer8` they point one record early
  ([data/0001 §8](../findings/data/0001-excel-loader.md#8-answers-to-the-archivists-phase-1-questions), [MonStats.md](MonStats.md#open-questions)).
- Answered `[I]` by [data/0004](../findings/data/0004-cell-converters.md): `levels.bin +0x16D..+0x20F` is
  alignment plus the two localised-name buffers filled at load (§ Fields with no `.txt` column).
- `[L]` `BlankScreen` is 1 in every row; `+0x218` is placed by elimination `[I]`.
- ~~Where the size of Barricade 1 and 2 (levels 111, 112) comes from~~ answered by drlg/0008: the Act V link pick
  ([§ Outdoor sizes from the link picks](#outdoor-sizes-from-the-link-picks-plan-0026-phase-1)).
