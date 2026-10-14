# LvlPrest (`data/global/excel/lvlprest.txt` → `lvlprest.bin`)

> **Source archive:** patch_d2 (`lvlprest.txt`, `lvlprest.bin`)   **Rows:** 1091 (1092 data rows − 1 `Expansion` marker at data row 863)
> **Record:** `lvlprest.bin` 432 B
> **sha256:** `.txt` `c2f6a891f07145fcffd8755b6fd163f86b6c3363fc45e9c6fe133436f7ae3f9e`, `.bin` `bdb6b98a648de5fde9cf1e587a28140786960d7fceba4b8064ef5584ec199c30`
> **Doc status:** columns listed, `.bin` layout complete, every compiled column has a code reader (drlg/0002, drlg/0003, drlg/0004); per-generator survey (plan 0016 P0)

## Purpose

One record per preset definition: the level it belongs to, the DS1 files it may use, its size and
a set of behaviour flags. Read by `drlg/overview`, `drlg/preset`, `drlg/maze`, `drlg/outdoor` and
`drlg/collision` ([research map](../specs/README.md)). The DS1 files themselves are in
[ds1.md](../formats/ds1.md). Written for plan 0005 Phase 1. The column semantics belong to the
drlg plans.

## Row identity

- `[C]` `Def` equals the data row index once the `Expansion` marker row is dropped (0..1090) in every
  row, and is compiled as `+0x000`. `Name` is not compiled.
- `[C]` `LevelId` is 0 in 1056 rows. The other 35 rows each name a distinct `Levels.txt` `Id`, and
  all of them resolve.

## Columns

`[C]` layout tags are by data behaviour: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel lvlprest`
decodes all 1091 records and matches every mapped cell (25 093 cells, 0 mismatches). Each varying
column's offset is the only one a probe finds. Widths are `[C]`: every integer column is a 4-byte
slot. The `u32`/`s32` in the `.bin field` column is the decode `excel_bin.py` uses for the slot, not a
claim about the type the game reads. `[L]` Signedness is not pinned by any code anchor: `PopPad`'s
negative values pin only the stored bits (two's complement), and `SizeX`/`SizeY` hold 0..64, so the
data does not show them signed either. The `File1..6` arrays are 60 bytes apart, and no cell is longer than
40 characters. **Meaning:** see [Semantics from the drlg findings](#semantics-from-the-drlg-findings-plan-0008) and
[Semantics from the preset findings](#semantics-from-the-preset-findings-plan-0016).

| Column | Observed type / range | `.bin` field | References | Layout tag |
|---|---|---|---|---|
| `Name` | str, 1089 distinct, len ≤ 44 | — (editor name; not in the record (rows are addressed by Def / row index)) | — | — |
| `Def` | int 0..1090 (1091 distinct) | `+0x000` u32 | — | [C] |
| `LevelId` | int 0..136 (36 distinct) | `+0x004` u32 | Levels `Id` | [C] |
| `Populate` | int 0..1 (2 distinct) | `+0x008` u32 | — | [C] |
| `Logicals` | int 0..1 (2 distinct) | `+0x00C` u32 | — | [C] |
| `Outdoors` | int 0..1 (2 distinct) | `+0x010` u32 | — | [C] |
| `Animate` | int 0..1 (2 distinct) | `+0x014` u32 | — | [C] |
| `KillEdge` | int 0..1 (2 distinct) | `+0x018` u32 | — | [C] |
| `FillBlanks` | int 0..1 (2 distinct) | `+0x01C` u32 | — | [C] |
| `SizeX` | int 0..64 (12 distinct) | `+0x028` 4-byte slot (s32 decode) | — | [C] |
| `SizeY` | int 0..64 (12 distinct) | `+0x02C` 4-byte slot (s32 decode) | — | [C] |
| `AutoMap` | int 0..1 (2 distinct) | `+0x030` u32 | — | [C] |
| `Scan` | int 0..1 (2 distinct) | `+0x034` u32 | — | [C] |
| `Pops` | int 0..4 (5 distinct) | `+0x038` u32 | — | [C] |
| `PopPad` | int -5..0 (3 distinct) | `+0x03C` 4-byte slot (s32 decode) | — | [C] |
| `Files` | int 0..6 (7 distinct) | `+0x040` u32 | — | [C] |
| `File1` | str, 1082 non-blank (`0` = none in 9), len ≤ 40 | `+0x044` char[60] | DS1 path under `data/global/tiles/` ([ds1.md](../formats/ds1.md#lvlprest-references)) | [C] |
| `File2` | str, 491 non-blank (`0` = none in 600), len ≤ 34 | `+0x080` char[60] | DS1 path under `data/global/tiles/` ([ds1.md](../formats/ds1.md#lvlprest-references)) | [C] |
| `File3` | str, 296 non-blank (`0` = none in 795), len ≤ 33 | `+0x0BC` char[60] | DS1 path under `data/global/tiles/` ([ds1.md](../formats/ds1.md#lvlprest-references)) | [C] |
| `File4` | str, 138 non-blank (`0` = none in 953), len ≤ 33 | `+0x0F8` char[60] | DS1 path under `data/global/tiles/` ([ds1.md](../formats/ds1.md#lvlprest-references)) | [C] |
| `File5` | str, 38 non-blank (`0` = none in 1053), len ≤ 33 | `+0x134` char[60] | DS1 path under `data/global/tiles/` ([ds1.md](../formats/ds1.md#lvlprest-references)) | [C] |
| `File6` | str, 13 non-blank (`0` = none in 1078), len ≤ 33 | `+0x170` char[60] | DS1 path under `data/global/tiles/` ([ds1.md](../formats/ds1.md#lvlprest-references)) | [C] |
| `Dt1Mask` | int 0..1074003987 (111 distinct) | `+0x1AC` u32 | — | [C] |
| `Beta` | int 0..1 (2 distinct) | — (no field in lvlprest.bin matches it) | — | — |
| `Expansion` | int 0..1 (2 distinct) | `+0x020` u32 | — | [C] |

## Fields with no `.txt` column

| record | offset | type | observed | tag |
|---|---|---|---|---|
| lvlprest | `+0x024` | u32 | 0 in every record | `[I]` the animated-tile frame period (0 means 80), read only with `Animate` ([§ Semantics](#semantics-from-the-preset-findings-plan-0016)) |

## Record layout

`+0x000` `Def`, `LevelId`, `Populate`, `Logicals`, `Outdoors`, `Animate`, `KillEdge`, `FillBlanks`,
`Expansion` (u32) · `+0x024` animation period u32 (no column) · `+0x028` `SizeX`, `SizeY` (s32 decode), `AutoMap`, `Scan`, `Pops`
(u32), `PopPad` (s32 decode), `Files` (u32) · `+0x044` `File1..6` (`char[60]` each) · `+0x1AC` `Dt1Mask`
(u32). `Expansion`, the last `.txt` column, is compiled at `+0x020`, out of header order. The
integer types are the slot decode only; signedness is `[L]` (see § Columns).

## Interpretation notes

- `[C]` `File1..6` hold DS1 paths relative to `data/global/tiles/` (e.g. `Act1/Town/TownN1.ds1`),
  in mixed case. The literal `0` means none, and is stored as the string `"0"`. All 2058 non-`0`
  cells resolve case-insensitively to a shipped `.ds1`
  ([ds1.md § LvlPrest references](../formats/ds1.md#lvlprest-references)).
- `[C]` `SizeX`/`SizeY` equal the `size_x`/`size_y` header fields of every DS1 the record names,
  whenever they are non-zero (1995 references). 63 references come from records with size 0. Both
  count tiles. The DS1 cell grid is one larger in each direction, which the DS1 byte accounting shows
  ([ds1.md § Header](../formats/ds1.md#header)).
- `[C]` `Files` is not the count of non-`0` `File1..6` cells: 81 records disagree (e.g. `Files = 0`
  with 4 files named).

## Semantics from the drlg findings (plan 0008)

Column meanings that [drlg/0002](../findings/drlg/0002-room-build-draws.md) and
[drlg/0003](../findings/drlg/0003-generator-dispatch.md) settle in code (backlog reverser → archivist,
2026-10-12). The tags are the findings'; the anchors are theirs.

| Column | Meaning | Tag | Anchor |
|---|---|---|---|
| `Files` (`+0x40`) | operand of the file-index draw `idx = Range(level seed, Files)` in `sub_00666ED0_PresetInstanceCreate`; `Files` ≤ 0 → index 0, no draw. It is **not** the count of named files: the 81 disagreeing records get their index from an override (town link value, outdoor cell bits 16–19, maze cell) — seen for 9 records in the run, `[I]` for the other 72 | [C] | fn:sub_00666ED0_PresetInstanceCreate@0x00666ED0, run:2026-10-12-drlg-gen, tbl:LvlPrest.txt:Files |
| `File1..6` (`+0x44 + 0x3C·idx`) | the instance's DS1 is `File(idx+1)`; all 960 preset instances of the run load the predicted file | [C] | fn:sub_00666ED0_PresetInstanceCreate@0x00666ED0, run:2026-10-12-drlg-gen, tbl:LvlPrest.txt:File1 |
| `LevelId` (`+0x04`) | a preset level (`DrlgType` 2) takes the first record whose `LevelId` is its id; none is fatal | [I] | fn:sub_0061F0E0_LvlPrestByLevel@0x0061F0E0 |
| `Def` (`+0x00`) | the key `sub_0061F0B0_LvlPrestByDef` indexes by | [I] | fn:sub_0061F0B0_LvlPrestByDef@0x0061F0B0 |
| `SizeX`, `SizeY` (`+0x28`/`+0x2C`) | the instance size when both are non-zero, else the rect the caller gives | [I] | fn:sub_00666ED0_PresetInstanceCreate@0x00666ED0 |
| `Scan`, `Pops` (`+0x34`/`+0x38`) | when both are 0 the build skips the map scan (`DRLG_PresetMapScan`) and its unit rolls on the level seed | [I] | fn:DRLG_PresetMapScan@0x00667970 |
| `Expansion` (`+0x20`) | not tested by the record pick (`LvlPrestByLevel`, `LvlPrestByDef`); it gates only the start-up DS1 preload (drlg/0001) | [I] | fn:sub_0061F0E0_LvlPrestByLevel@0x0061F0E0 |
| `Dt1Mask` (`+0x1AC`) | the DT1 mask (room `+0x50`) of every preset and maze room built from the record: bit *i* selects `LvlTypes` `File i+1` ([LvlTypes](LvlTypes.md#interpretation-notes)); checked over all 464 type-2 rooms of the run | [C] | fn:sub_00667ED0_PresetRoomsCreate@0x00667ED0, run:2026-10-11-drlg-roomk, tbl:LvlPrest.txt:Dt1Mask |

- `[C]` Data side of the `Files` reading: `Files` ranges 0..6 and 81 records disagree with the number of
  named `File1..6` cells (see *Interpretation notes*); the draw takes `Files` as it is, so for those records
  the named files beyond `Files` are reachable only through an override. (tbl:LvlPrest.txt:Files)
- `AutoMap` (`+0x30`), which drlg/0003's walkthrough of `sub_00668100_PresetLevelBuild` reads untagged, is
  settled by drlg/0004 ([below](#semantics-from-the-preset-findings-plan-0016)).

## Semantics from the preset findings (plan 0016)

The remaining columns, from [drlg/0004](../findings/drlg/0004-preset-units.md) (plan 0016 Phase 1, static) and its Phase 2 run
(run:2026-10-13-drlg-preset); backlog reverser → archivist, 2026-10-13. The tags and anchors are the finding's
([drlg/0004 § LvlPrest columns](../findings/drlg/0004-preset-units.md#lvlprest-columns)). `[I]` None of these readers draws on any seed (no LCG constant in them; drlg/0003's level-seed check covers
the build).

| Column | Meaning | Tag | Anchor |
|---|---|---|---|
| `Populate` (`+0x08`) | 0 sets room `+0x28` bit `0x800000`, for which `RoomPopLevelId` returns 0: **no random population**. Preset units still spawn (48 preset monsters in `Populate` 0 rooms of Harrogath and the Pandemonium Fortress). The column is not the only switch: `DRLG_RoomNoPopNearTown` sets the same bit on a room next to a town level, and `sub_0066E360_HiddenWarpTilesAdd` on a room with hidden warp tiles (`[I]`) | [C] | fn:sub_00666680_PresetRoomCreate@0x00666680, fn:sub_0061A1F0_RoomPopLevelId@0x0061A1F0, fn:DRLG_RoomNoPopNearTown@0x0066BD50, run:2026-10-13-drlg-preset, tbl:LvlPrest.txt:Populate |
| `Logicals` (`+0x0C`) | selects the room's logic-region builder: 0 one region covering the room (`LogicBoxSingle`), 1 regions flooded from the DS1 cells (`LogicRegionsFromDs1`). The client's wall cut-away reads them every frame; the server's population uses the same boxes as spawn areas (`[I]`). The builders' output is `[I]` and belongs to `drlg/collision` | [C] selection; [I] output | fn:sub_00666AC0_PresetRoomTilesBuild@0x00666AC0, fn:sub_0066CCB0_LogicBoxSingle@0x0066CCB0, fn:sub_0066D110_LogicRegionsFromDs1@0x0066D110, fn:sub_004DD060_WallCutawayTest@0x004DD060, run:2026-10-13-drlg-preset |
| `Outdoors` (`+0x10`) | ORs `0x80000` into the room flags the scan grid writes; no reader of that room bit found | [I] | fn:sub_00667ED0_PresetRoomsCreate@0x00667ED0 |
| `Animate` (`+0x14`) | counts animated tiles (DT1 flag `0x100`), sets room bit `0x8000000` and builds the frame lists | [I] | fn:sub_00666AC0_PresetRoomTilesBuild@0x00666AC0, fn:sub_0066D700_AnimTilesBuildAll@0x0066D700 |
| `+0x024` (no column) | the frame period of those lists; 0 means 80. Read only with `Animate` (at `0x00666D80`); 0 in every record | [I] | fn:sub_00666AC0_PresetRoomTilesBuild@0x00666AC0 |
| `KillEdge` (`+0x18`), `FillBlanks` (`+0x1C`) | as in [drlg/0002](../findings/drlg/0002-room-build-draws.md) § Room tile build | [I] | fn:sub_00666AC0_PresetRoomTilesBuild@0x00666AC0 |
| `AutoMap` (`+0x30`) | gates the act callbacks of `PresetLevelBuild`, which are null on the server and fill the automap on the client: no server effect | [I] | fn:sub_00668100_PresetLevelBuild@0x00668100 |
| `Scan` (`+0x34`) | with `Pops`, gates the map scan; the scan marks wall cells of orientation 10/11 in the level grid, collects style 30–33 cells as warp markers (level `+0x2C`) and marks the cells of some objects | [I] | fn:DRLG_PresetMapScan@0x00667970 |
| `Pops` (`+0x38`) | the capacity of the roof-pop tables (one entry per distinct style 8–29 of orientation 10/11), from which the client hides roofs | [C] | fn:DRLG_PresetMapScan@0x00667970, fn:DRLG_PresetPopsUpdate@0x006671E0, run:2026-10-13-drlg-preset |
| `PopPad` (`+0x3C`) | added to a pop trigger rectangle's width and height in subtiles, `(x·5, y·5, w·5 + PopPad, h·5 + PopPad)`, half-open, by the client's per-frame pop update; a negative value pulls in the far x and y edges. The model reproduces 6443 logged player positions, 70 of them decided by `PopPad`. The value is used as signed, so the `[L]` on signedness in [§ Columns](#columns) is answered for this column | [C] | fn:DRLG_PresetPopsUpdate@0x006671E0, fn:sub_0066B980_RectContains@0x0066B980, run:2026-10-13-drlg-preset, tbl:LvlPrest.txt:PopPad |

- `[C]` Data side of `Populate`: the shipped data carries preset monsters under `Populate` 0 (`townWest.ds1`,
  `Def` 863, Harrogath; the act-3 treasure rooms `Def` 703/704), so a reimplementation must not drop preset units
  there. ([drlg/0004](../findings/drlg/0004-preset-units.md) § Leads used, tbl:LvlPrest.txt:Populate)

## Survey by generator kind (plan 0016 Phase 0)

`python3 -I tools/ds1.py units workspace/merged` puts each record into one generator kind. This is the kind of
generator that builds a preset instance from the record. The values of `Levels.DrlgType` are 1 maze, 2 preset,
3 outdoor (drlg/0003).

- **preset level** (35): records with a `LevelId`. `[I]` A preset level takes the first record with its id
  (fn:sub_0061F0E0_LvlPrestByLevel@0x0061F0E0). `[C]` All 35 are the first, and only, record of their level, and
  all 35 levels have `DrlgType` 2.
- **maze room** (603), **outdoor cell** (357), **maze or outdoor** (93): records without a `LevelId`.
  - `[L]` The kind is a data-only match. Take the record's `Dt1Mask` and look at each `LvlTypes` row. The mask's
    set bits must name non-`0` files in that row. Among those rows, pick the one whose selected files hold the
    most of the DT1s listed in the record's DS1s. The kind is then the `DrlgType` of that row's non-preset levels.
  - `[C]` Two level types are used by both maze and outdoor levels: 22 (Act 3 Kurast: outdoor 79–83, maze
    100–101) and 28 (Act 4 Lava: maze 107, outdoor 108).
  - `[L]` For those two types the survey takes a record inside a maze rotation range (`base < Def < base + 16`,
    drlg/0003) as maze. This is the survey's sorting rule, not an observation. The other 93 stay "maze or outdoor".
  - `[C]` All 216 records in a rotation range come out as maze.
- **no file** (3): `Def` 0 (`None`, all zeros) and `Def` 2/3 (`Act 1 - Town 1 Transition E/S`, sizes 8×40 and
  56×8, `Files` 0, nothing named).

`[C]` Distribution per kind, as records with the value. The counts are exact. The grouping is `[L]` except for the
preset-level column and the rotation ranges.

| Column | preset level (35) | maze room (603) | outdoor cell (357) | maze or outdoor (93) | no file (3) |
|---|---|---|---|---|---|
| `Populate` = 1 | 30 | 595 | 309 | 93 | 2 |
| `Logicals` = 1 | 16 | 333 | 42 | 55 | 0 |
| `Outdoors` = 1 | 11 | 21 | 357 | 66 | 2 |
| `Animate` = 1 | 0 | 21 | 0 | 12 | 0 |
| `KillEdge` = 1 | 11 | 226 | 357 | 48 | 2 |
| `FillBlanks` = 1 | 35 | 582 | 357 | 81 | 2 |
| `Expansion` = 1 | 6 | 83 | 136 | 0 | 2 |
| `+0x024` | 0 | 0 | 0 | 0 | 0 |
| `SizeX` | 0 ×35 | 8, 10, 12 (×218), 14, 16, 24, 32, 40, 64; 0 ×1 | 8 ×125, 16 ×145, 32 ×79, 24, 56, 64 | 8, 12, 16, 24, 32, 48 | 0, 16 ×2 |
| `SizeY` | 0 ×35 | 8 ×50, 10 ×28, 12 ×218, 14 ×77, 16 ×143, 24 ×71, 32 ×2, 40 ×11, 64 ×2; 0 ×1 | 8 ×123, 16 ×130, 32 ×83, 48 ×15, 24, 40, 56 | 8, 12, 16, 24, 32 | 0, 16 ×2 |
| `AutoMap` = 1 | 5 | 0 | 0 | 0 | 0 |
| `Scan` = 1 | 34 | 175 | 61 | 22 | 0 |
| `Pops` | 0 ×30, 1 ×3, 2, 3 | 0 ×602, 1 ×1 | 0 ×352, 1 ×2, 2 ×3 | 0 ×69, 1, 2 ×4, 3 ×6, 4 ×13 | 0 |
| `PopPad` | 0 ×32, −4 ×2, −5 ×1 | 0 ×582, −4 ×21 | 0 ×315, −4 ×42 | 0 ×28, −4 ×65 | 0 |
| `Files` | 0..6 (1 ×22) | 0..6 (1 ×313, 2 ×142) | 0..6 (1 ×234) | 0..5 (1 ×58) | 0 |
| `Files` ≠ named count | 2 | 17 | 57 | 5 | 0 |
| `Dt1Mask` distinct | 22 | 22 | 72 | 8 | 2 |

What the data alone shows (`[C]` as data; the meanings are in [§ Semantics from the preset findings](#semantics-from-the-preset-findings-plan-0016)):
- `AutoMap` is 1 on exactly five records: the five towns (`Def` 1, 301, 529, 797, 863 for levels 1, 40, 75, 103,
  109).
- `Animate` is 1 on 33 records. They are `Def` 836–862 (`Act 4 - Lava …`) and 1053–1058 (`Act 5 - Lava …`), all
  with `Outdoors` 1. `Animate` = 1 goes with `FillBlanks` = 0 in all 33. The only other record with `FillBlanks`
  0 is `Def` 0.
- `Outdoors` is 1 on every outdoor-cell record and on 21 maze-room records. Those 21 are the lava rooms in the maze rotation ranges of acts 4 and 5
  (`Def` 837–851 and 1053–1058), the same 21 that have `Animate` 1.
  `KillEdge` is 1 on every outdoor-cell record.
- `Pops` > 0 occurs on 35 records, and on 30 of them `PopPad` is −4 or −5. `PopPad` −4 also occurs on 101 records
  with `Pops` 0. `Scan` and `Pops` are independent: 22 records have `Pops` > 0 with `Scan` 0.
- `+0x024` is 0 in every record of every kind.
- `Beta` is not in the table: it has no field in `lvlprest.bin` ([§ Columns](#columns)), so the game cannot read
  it and the survey does not count it.

### Shared files

Files named by more than one record (the `0x84` candidates from drlg/0002) are listed in
[ds1.md § Files shared between records](../formats/ds1.md#files-shared-between-records-the-0x84-candidates).
`[C]` There are six such files, and **none is named by records of different `SizeX`/`SizeY`**.

## Maze presets (plan 0022 Phase 0)

`python3 -I tools/maze_survey.py workspace/merged/data/global/excel` § 2 (gate survey `maze`) lists, per level
type used by a maze level (`Levels.DrlgType` 1, 20 types), the records the maze rotation reads and the records
that fit the type. Every count is `[C]` by that command. Meanings stay `[L]`, owner `drlg/maze`.

- **Rotation range.** `sub_006738C0_MazePresetFile` rotates the file index of a maze room whose `Def` lies
  strictly between a per-type base and base + 16, so in `base+1..base+15` ([drlg/0003](../findings/drlg/0003-generator-dispatch.md),
  `MAZE_DEF_BASE` in `tools/drlg.py`, fn:sub_006738C0_MazePresetFile@0x006738C0). 15 of the 20 maze types have a
  base. The survey checks each range against the exit mask *m* = `Def` − base, written with N = 8, S = 4, E = 2,
  W = 1. The letters are in N S E W order, so *m* = 1..15 reads W, E, EW, S, SW, SE, SEW, N, NW, NE, NEW, NS, NSW,
  NSE, NSEW.
- **Block** (a sorting rule of the survey, not a claim about the generator): the records with `LevelId` 0 whose
  `Dt1Mask` is non-zero and selects only non-`0` files of the type's [LvlTypes](LvlTypes.md) row, and whose
  `File1` lies in the directory of one of those files. Types that share DT1s share block records: 7 + 8
  (Def 168–255), 14 + 15 (358–361), 22 + 24 (665–702) and 28 + 35 (798–862).

`[C]` Per maze type with a base (rows = 15 per range; "Files" = the `Files` sum over the range / the named
`File1..6` cells):

| Type | Name | Base (record at base) | Range | Files | Size | DS1 pattern (`{m}` = exit letters) | Block |
|---|---|---|---|---|---|---|---|
| 3 | Act 1 - Cave | 52 (`DOE Entrance`) | 53–67 | 30 / 30 | 24×24 | `Act1/Caves/Cave{m}.ds1`, `…{m}2` | 53–103 |
| 4 | Act 1 - Crypt | 108 (`Graveyard`) | 109–123 | 30 / 30 | 8×8 | `Act1/Crypt/Crypt{m}.ds1`, `…{m}2` | 109–158 |
| 7 | Act 1 - Barracks | 167 (`Barracks Court Connect`) | 168–182 | 60 / 60 | 10×14 | `Act1/Barracks/Bar{m}.ds1`, `…{m}2..4` | 167–255 |
| 8 | Act 1 - Jail | 205 (`Barracks Forge N`) | 206–220 | 61 / 61 | 12×12 | `Act1/Barracks/Jail{m}.ds1`, `…{m}2..4`; one `File5` `Jail{m}Secret` | 168–255 |
| 10 | Act 1 - Catacombs | 257 (`Cathedral`) | 258–272 | 60 / 60 | 12×12 | `Act1/Catacomb/Cat{m}.ds1`, `…{m}2..4` | 258–298 |
| 13 | Act 2 - Sewer | 301 (`Town `) | 302–316 | 30 / 30 | 12×12 | `Act2/Sewer/Sew{m}.ds1`, `…{m}2` | 302–352 |
| 17 | Act 2 - Tomb | 413 (`Desert Ruins Elder`) | 414–428 | 48 / 48 | 16×16 | `Act2/Tomb/Tomb{m}.ds1`, `…{m}2..3`; `File4` in 3 | 414–480 |
| 18 | Act 2 - Lair | 481 (`Duriel's Lair`) | 482–496 | 56 / 57 | 10×10 | `Act2/Maggot/Mag{m}.ds1`, `…{m}2..6`, unevenly | 482–509 |
| 22 | Act 3 - Kurast | 753 (`Temple 6`) | 754–768 | 30 / 30 | 12×12 | `Act3/Travincal/Meph{m}.ds1`, `…{m}2` | 754–795 (run) |
| 24 | Act 3 - Dungeon | 664 (`Spider Chest NE`) | 665–679 | 45 / 45 | 14×14 | `Act3/Jungle/Dung{m}.ds1`, `…{m}2..3` | 665–702 |
| 25 | Act 3 - Sewer | 704 (`Dungeon Treasure 2`) | 705–719 | 30 / 30 | 12×12 | `Act3/Sewer/Sewer{m}.ds1`, `…{m}2` | 705–746 |
| 28 | Act 4 - Lava | 836 (`Lava X`) | 837–851 | 30 / 30 | 24×24 | `Act4/Lava/Lava{m}.ds1`, `…{m}2` | 837–862 (run) |
| 33 | Act 5 - Ice Caves | 1002 (`Barricade 16 Snow`) | 1003–1017 | 45 / 45 | 16×16 | `Expansion/icecave/Ice{m}01.ds1`, `…02`, `…03` | 1003–1041 |
| 34 | Act 5 - Baal | 1058 (`Lava NS`) | 1059–1073 | 45 / 45 | 16×16 | `Expansion/BaalLair/baal{m}01.ds1`, `…02`, `…03` | 1059–1085 |
| 35 | Act 5 - Lava | 1052 (`Temple SW Waypoint`) | 1053–1067 | 39 / 39 | 24×24 (6), 16×16 (9) | none (below) | 1053–1058 (and 798–862) |

"(run)" is the contiguous block run that starts at base + 1; the full block of type 22 is 530–658, 665–702 and
754–795 (209 records, most of them outdoor Kurast cells), and type 28's is 798–862.

- `[C]` In 14 of the 15 ranges, the record at base + *m* has the exit letters of *m* as the last word of its
  `Name` (`Def` 303 `Act 2 - Sewer E ` has a trailing space) and in its `File1` basename. Every file slot of the
  range follows one name pattern. The record at base itself has no exit-mask name in any type. It falls in its
  own type's block only for type 7 (167, `Barracks Court Connect`). Five bases are preset-level records
  (`LevelId` ≠ 0: 257, 301, 481, 704, 753), and 301 (`Act 2 - Town `) names no file.
- `[C]` **Type 35 (Act 5 Lava, levels 125–127 and 135) does not fit.** Its range 1053–1067 holds the six
  `Act 5 - Lava` records 1053–1058 (`N`, `S`, `E`, `W`, `EW`, `NS`, in that order, so not in mask order, 24×24,
  `Act4/Expansion/Lava*.ds1`) followed by the first nine records of type 34's range (1059–1067,
  `Act 5 - Baal W` … `NW`, 16×16). The two ranges overlap on 1059–1067. These levels have `Rooms` 3 in
  [LvlMaze](LvlMaze.md#survey-plan-0022-phase-0). `[L]` Whether the Act 5 Lava maze ever asks for a mask
  other than those six, and what base 0x41C means for it, needs the generator (Phase 1).
- `[C]` In the Lair range the `File1..6` cells are filled unevenly: `Files` 1–6 per record, and four records
  name `Mag{m}3` and `Mag{m}4` twice each (488, 492, 494, 495). `Def` 493 has `Files` 5 with six named files.
  This is the one range record where `Files` and the named count differ.
- `[C]` The **five maze types without a base** and their blocks:

  | Type | Name | Maze levels | Block | Records | Files / named | Size | Names |
  |---|---|---|---|---|---|---|---|
  | 14 | Act 2 - Harem | 51 | 354–361 | 8 | 16 / 22 | 16×16 | `Corrupt Harem NE/SE/SW/NW` (`SubNE.ds1` …) + the four Basement records |
  | 15 | Act 2 - Basement | 52–54 | 358–361 | 4 | 8 / 14 | 16×16 | `Basement NE/SE/SW/NW` (`CelNE.ds1`, `CelNE2.ds1`, `CelNEWaypoint.ds1`, some `CelNE3.ds1`) |
  | 19 | Act 2 - Arcane | 74 | 510–528 | 19 | 8 / 53 | 12×12 | `Arcane W` … `NSEW` (510–524) + `Arcane Summoner W/E/S/N` (525–528) |
  | 23 | Act 3 - Spider | 84, 85 | 659–664 | 6 | 18 / 18 | 16×16 | `Spider SW/SE/NW/NE` + `Spider Chest NW/NE` (`Lair*.ds1`) |
  | 32 | Act 5 - Temple | 122, 123 | 1042–1052 | 11 | 15 / 15 | 40×40 | `Temple NE/NW/SE up/SW`, three `… Down`, four `… Waypoint` (`temp*.ds1`) |

  The Harem, Basement, Spider and Temple records are named for quadrants (NE, SE, SW, NW), not for exit masks.
  `Arcane` 510–524 is the one 15-record run in mask order outside the rotation table, as if its base were 509.
  11 of those 15 records have `Files` 0 and 4 or 5 named files (`SanctNSEW.ds1`, `SanctNSEW1..4.ds1`). By
  [§ Semantics from the drlg findings](#semantics-from-the-drlg-findings-plan-0008), `Files` 0 means no file
  draw, so `[I]` without a forced index those records always load `File1`. Basement's `Files` 2 leaves its
  `…Waypoint`/`…3` files outside the draw in the same way. (fn:sub_00666ED0_PresetInstanceCreate@0x00666ED0,
  fn:sub_006738C0_MazePresetFile@0x006738C0, tbl:LvlPrest.txt:Files)
- `[L]` How the maze generator chooses a `Def` for each room (from the exit mask, from a per-type table, or from
  the special `Prev`/`Next`/`Down`/`Theme`/`Treasure` records that follow each range in the blocks) is not in
  the data. Owner: `drlg/maze` (plan 0022 Phase 1).

## Outdoor presets (plan 0026 Phase 0)

`python3 -I tools/outdoor_survey.py workspace/merged [--act N]` § 2 (gate survey `outdoor`) lists, per generator
act ([Levels § Outdoor survey](Levels.md#outdoor-survey-plan-0026-phase-0)), the records the act's outdoor
generator can place under a data-only rule, grouped into families. Every count is `[C]` by that command. Which
records a generator actually places, and where, is `[L]`, owner `drlg/outdoor` (plan 0026 Phase 1).

- **The rule** (a sorting rule of the survey, not a claim about the generator). A record belongs to an act when
  all of the following hold:
  - it has `LevelId` 0 and at least one named file;
  - its `Def` lies outside every maze rotation range (`base < Def < base + 16`, [§ Maze presets](#maze-presets-plan-0022-phase-0));
  - its `Dt1Mask` is non-zero and selects only named files of the [LvlTypes](LvlTypes.md) row of one of the
    act's outdoor level types;
  - at least one selected DT1 is listed by one of the record's DS1s.
- **A family** is the record `Name` with its variant tokens removed: numbers (`6A` too), `N`/`S`/`E`/`W` letter sets and
  `16X16`-style sizes. So `Act 3 - Clearing Webby NW` is in `Act 3 - Clearing Webby`. It is a label, not data
  the game reads (`Name` is not compiled).

`[C]` Totals. 450 records in 126 families. No record fits two acts. Every named DS1's header size equals its
record's `SizeX`×`SizeY`, and no record of these families has size 0. In 62 records `Files` differs from the
number of named files.

| Gen. act | Level types | Records | Families |
|---|---|---|---|
| I | 2 | 56 | 27 |
| II | 16 | 52 | 27 |
| III | 21, 22 | 156 | 26 |
| IV | 27, 28 | 50 | 13 |
| V | 30, 31 | 136 | 33 |

`[C]` The families per act ("Files" is the `Files` sum / the named `File1..6` cells; sizes are `SizeX`×`SizeY`, with a
record count where there is more than one):

- **Act I** (all `Act1/Outdoors` unless stated):
  - borders and edges: `Town Transition` 2–3 (8×40, 56×8, `Act1/Town`, `Files` 0 with 1 and 2 named);
    `Wild Border` 4–15 (12 × 8×8, 20 / 28); `Wild Cliff Border` 16–23 (8 × 8×8); `Wild Cliff Cave Right/Left`
    24, 25 (8×8, `Act1/Caves`);
  - river: `River Upper` 26, `River Lower` 27 and `Bridge` 28 (8×8, `Files` 0 with 4, 4 and 3 named);
  - fills: `Stone Fill` 29–30, `Corral Fill` 31, `Fence Fill` 32–37 (8×8, 8×16 ×2, 16×8, 16×16 ×2), `Swamp Fill`
    38–39, `Tree Fill` 40 (16×16), `Ruin` 41 (16×16);
  - areas: `Fallen Camp` 42–43 (4 files each), `Fallen Camp Bishibosh` 44, `Camp` 45, `Pond` 46, `Cottages` 47–49
    (13 files), `Bivouac` 50 (16×16), `Cave Entrance` 51 and `DOE Entrance` 52 (`Act1/Caves`), `Graveyard` 108
    (24×32, `Act1/Graveyard`), `Cairn Stones` 160, `Inifus` 161, `Tower Tome` 162, `Tower` 163.
- **Act II** (`Act2/Outdoors` unless stated):
  - borders: `Desert Transition` 362–363 (8×56, 56×8, `Act2/Town`); `Desert Border` 364–375 (12 × 8×8);
  - cliffs, 376–387 (`Act2/BigCliff`, ten families of 1 record): `Desert Cliff Right/Left` `Ends`, `Wall`, `Path`
    (16×8 right, 8×16 left), `Top` (16×16), and the `King Tomb` / `King Ends` variants of each. `Files` 0 with
    2–3 named in 376, 379, 383, 385, 387;
  - areas: `Desert Tomb` 388–389, `Desert Lair` 390–391 (`Act2/Maggot`), `Desert Valley Ruin` 392–393
    (`Act2/Ruin`, 11 files), `Desert Valley Warp` 394, `Desert Oasis` 395–397;
  - fills: `Desert Fill Mesa/Head/Bone/Wagon/Berms` 398–407, `Desert Ruins` 408–411 (8×8, 8×16, 16×8, 16×16),
    `Desert Ruins Sewer` 412, `Desert Ruins Elder` 413 (16×16).
- **Act III** (`Act3/Jungle`, `Act3/Kurast`, `Act3/Travincal`):
  - jungle (32×32): `Jungle` 530–572 (43 records, 75 files), `Jungle Head` 573 and `Jungle Tail` 574 (64×32,
    `Files` 0 with 2 named), `Clearing Webby` 575–584, `Clearing Boggy` 585–594, `Clearing Pygmy` 595–604 (each
    10 records with `Files` 1 and 3 named);
  - Kurast: per district (`Slums`, `Burbs`, `Metro`), a `Border` family of 8 records (8×8, named N, S, E, W, NE,
    NW, SE, SW), a `Gate` family of 2 (N, S) and fill records of 8×8, 8×16, 16×8 and 16×16. Single records:
    `Burbs Sewer` 629, `Burbs Temple` 630, `Burbs Waypoint` 631, `Metro Sewer` 646, `MetroTemple` 647 (all `Files` 0),
    and `Bridge` 652 (48×16);
  - Travincal: `Travincal` 653–658 (`NW`, `NE`, `SW`, `SE` 16×32; `N`, `S` 32×32);
  - also fitting type 22: `Mephisto Theme` 769–783, `Mephisto Prev` 784–787, `Mephisto Next` 788–791,
    `Mephisto Waypoint` 792–795 (12×12). They follow the Act III Kurast maze range (754–768, maze levels 100–101).
- **Act IV** (`Act4/Mesa`, `Act4/Lava`, `Act4/Diab`):
  - Mesa (type 27): `Fortress Transition` 798 (8×24); `Mesa Border` 799–810 (12 × 8×8, 36 / 40);
    `Mesa Warp` 811; `Mesa` 812–821, 823–827 (three sets `Outer`/`Mid`/`Chaos`, each in 24×24, 16×16, 16×8, 8×16 and
    8×8, 4–5 files per record); `Mesa Izual` 822; `Pits` 828–835 (two sets, 16×16, 16×8, 8×16, 8×8, 3 files each);
  - Lava (type 28, 24×24): `Lava X` 836, `Lava Warp` 852, `Lava Forge` 853–854, `Bridge` 855–856, `Diablo Entry`
    857, `Diablo Arm` 858–861 (W, E, S, N), `Diablo Heart` 862.
- **Act V** (`Expansion/Siege`, `Expansion/IceCave`, `Expansion/Ruins`):
  - Siege (16×48): `Siege To Town` 865, `Siege Strip` 866–878 (13), `Siege To Barricade` 879;
  - Barricade borders (16×16): `Barricade Cliff Border`, `Barricade Ravine Border`, `Barricade Ravine-Cliff
    Border`, `Barricade Cliff Ravine Border`, 12 + 12 + 1 + 1 records (881–906). The `Snow` set 957–982 repeats
    them, but its records 967 and 979 (`… Border 11 Snow`) name no file, so the survey counts 11 + 11 + 1 + 1;
  - Barricade joins (16×32 and 32×16): `Barricade To Siege` 880, `Barricade Entrance` 907–908, `Barricade Exit`
    909–910, `Barricade From Cave` / `To Cave` 911–914 (and `Snow` 983–986);
  - Barricade fills (16×16): `Barricade` 915–930 (16 records), `Barricade Snow` 987–1002 (16), `Barricade Prison`
    931–938 (8);
  - Barricade areas (8×8 unless stated): `Barricade Building` 939, `Filler` 940, `Filler Treasure` 941, `Ruins`
    942–943, 945–946, `Ruins Treasure` 944, 947, `Snow Lake` 948–949, `Snow Other` 950, `Snow Treasure` 951,
    `Snow Unique` 952 (16×16), `Waypoint Dirt` 953, `Waypoint Snow` 954, `Hell Portal` 955–956 (16×16, `Files` 0).

What the data shows besides (`[C]` as data; the layouts they suggest are `[L]`):
- **Level sizes and record sizes.**
  - Siege 1 (240×48) is 15 widths of the 16×48 Siege records: `Siege To Town`, 13 `Siege Strip`s, `Siege To Barricade`.
  - A Jungle level (64×192) is two 32-wide columns and six 32-high rows. `Jungle Head` and `Jungle Tail` are 64×32,
    the full width.
  - Kurast 4 (48×16) has the size of the Act III `Bridge` 652.
  - Travincal (64×64) is 16 + 32 + 16 wide (the `NW`/`N`/`NE` record widths) and 32 + 32 high.
  - Diablo 1 (120×120) is 5 × 5 of the 24×24 Lava and Diablo records.
- **Border families.** Acts I, II and IV each have a 12-record border family of 8×8 (`Wild Border`, `Desert
  Border`, `Mesa Border`). Act V has 12-record `Cliff` and `Ravine` border families of 16×16. Its `Snow` copies
  have 12 records each too, but the 11th names no file.
- **Files beyond `Files`.**
  - `Wild Border 1–4` have `Files` 3 and five named files. The 4th and 5th are the `…o` and `…oe` files.
  - `Mesa Border 1–4` have `Files` 3 and a 4th `…o` file.
  - By [§ Semantics from the drlg findings](#semantics-from-the-drlg-findings-plan-0008), files past `Files`
    are reachable only through the outdoor cell's bits 16–19. In run:2026-10-12-drlg-gen, records 4–7 loaded index 3, and
    records 26–28 (`Files` 0) indices 0–3 (drlg/0003). (fn:sub_006750F0_OutdoorRoomsCreate@0x006750F0,
    tbl:LvlPrest.txt:Files)
- **Exit letters.**
  - `Act 3 - Jungle` 530–544 are named W, E, EW, S, … NSEW, the exit-mask order of the maze ranges (N 8, S 4,
    E 2, W 1). No rotation base points at them.
  - 545–572 carry two-letter-set names (`Jungle W E`, `Jungle EW S`, …). Their files are `Riv{a}o{b}.ds1`.
  - Each `Clearing` family has the 10 masks with one or two exits (W, E, EW, S, SW, SE, N, NW, NE, NS).
- **Shared level types.** Every Act III record fits type 21 and type 22, except the `Bridge`, `Travincal` and
  `Mephisto` families (22 only). 168 of the 450 records fit a level type that a maze level also uses: types 22
  and 28 ([Levels § Outdoor survey](Levels.md#outdoor-survey-plan-0026-phase-0)). The rule cannot tell an outdoor
  record from a maze record of those types outside the rotation ranges, so the `Mephisto` families (Durance-named)
  and the Act IV Lava records (836, 852–862) are listed for both.

## Open questions

- Answered: every compiled column now has a code reader, in
  [Semantics from the drlg findings](#semantics-from-the-drlg-findings-plan-0008) (`Files`, the `File1..6` pick,
  `LevelId`, `SizeX`/`SizeY`, `Expansion`, `Dt1Mask`) and
  [Semantics from the preset findings](#semantics-from-the-preset-findings-plan-0016) (`Populate`, `Logicals`,
  `Outdoors`, `Animate`, `+0x024`, `KillEdge`/`FillBlanks`, `AutoMap`, `Scan`, `Pops`, `PopPad`).
- `[L]` What the `Outdoors` room bit `0x80000` is read for: no reader found (drlg/0004). The logic-region output of `Logicals` is `drlg/collision`'s.
- `[L]` Which [§ Outdoor presets](#outdoor-presets-plan-0026-phase-0) records each act generator places, and
  whether the `Mephisto` families (769–795) and the Act IV Lava records (836, 852–862) are outdoor or maze records.
  The survey's rule lists them under both. Owner: `drlg/outdoor` (plan 0026 Phase 1).
