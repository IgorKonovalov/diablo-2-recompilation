# LvlPrest (`data/global/excel/lvlprest.txt` → `lvlprest.bin`)

> **Source archive:** patch_d2 (`lvlprest.txt`, `lvlprest.bin`)   **Rows:** 1091 (1092 data rows − 1 `Expansion` marker at data row 863)
> **Record:** `lvlprest.bin` 432 B
> **sha256:** `.txt` `c2f6a891f07145fcffd8755b6fd163f86b6c3363fc45e9c6fe133436f7ae3f9e`, `.bin` `bdb6b98a648de5fde9cf1e587a28140786960d7fceba4b8064ef5584ec199c30`
> **Doc status:** columns listed, `.bin` layout complete, semantics partial (drlg/0002, drlg/0003); per-generator survey (plan 0016 P0)

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
40 characters. **Meaning:** see [Semantics from the drlg findings](#semantics-from-the-drlg-findings-plan-0008).

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
| lvlprest | `+0x024` | u32 | 0 in every record | unknown |

## Record layout

`+0x000` `Def`, `LevelId`, `Populate`, `Logicals`, `Outdoors`, `Animate`, `KillEdge`, `FillBlanks`,
`Expansion` (u32) · `+0x024` unknown u32 · `+0x028` `SizeX`, `SizeY` (s32 decode), `AutoMap`, `Scan`, `Pops`
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
| `Scan`, `Pops` (`+0x34`/`+0x38`) | when both are 0 the build skips the map scan (`sub_00667970_PresetMapScan`) and its unit rolls on the level seed | [I] | fn:sub_00667970_PresetMapScan@0x00667970 |
| `Expansion` (`+0x20`) | not tested by the record pick (`LvlPrestByLevel`, `LvlPrestByDef`); it gates only the start-up DS1 preload (drlg/0001) | [I] | fn:sub_0061F0E0_LvlPrestByLevel@0x0061F0E0 |
| `Dt1Mask` (`+0x1AC`) | the DT1 mask (room `+0x50`) of every preset and maze room built from the record: bit *i* selects `LvlTypes` `File i+1` ([LvlTypes](LvlTypes.md#interpretation-notes)); checked over all 464 type-2 rooms of the run | [C] | fn:sub_00667ED0_PresetRoomsCreate@0x00667ED0, run:2026-10-11-drlg-roomk, tbl:LvlPrest.txt:Dt1Mask |

- `[C]` Data side of the `Files` reading: `Files` ranges 0..6 and 81 records disagree with the number of
  named `File1..6` cells (see *Interpretation notes*); the draw takes `Files` as it is, so for those records
  the named files beyond `Files` are reachable only through an override. (tbl:LvlPrest.txt:Files)
- `[L]` drlg/0003's walkthrough of `sub_00668100_PresetLevelBuild` also reads `AutoMap` (`+0x30`) as part of
  the gate for building the linked levels; the finding does not tag that line. Owner: `drlg/preset`.

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
  - `[C]` For those two types a record inside a maze rotation range (`base < Def < base + 16`, drlg/0003) is taken
    as maze. The other 93 stay "maze or outdoor".
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
| `SizeY` | 0 ×35 | as `SizeX` but 10 ×28, 14 ×77 | 8 ×123, 16 ×130, 32 ×83, 48 ×15, 24, 40, 56 | 8, 12, 16, 24, 32 | 0, 16 ×2 |
| `AutoMap` = 1 | 5 | 0 | 0 | 0 | 0 |
| `Scan` = 1 | 34 | 175 | 61 | 22 | 0 |
| `Pops` | 0 ×30, 1 ×3, 2, 3 | 0 ×602, 1 ×1 | 0 ×352, 1 ×2, 2 ×3 | 0 ×69, 1, 2 ×4, 3 ×6, 4 ×13 | 0 |
| `PopPad` | 0 ×32, −4 ×2, −5 ×1 | 0 ×582, −4 ×21 | 0 ×315, −4 ×42 | 0 ×28, −4 ×65 | 0 |
| `Files` | 0..6 (1 ×22) | 0..6 (1 ×313, 2 ×142) | 0..6 (1 ×234) | 0..5 (1 ×58) | 0 |
| `Files` ≠ named count | 2 | 17 | 57 | 5 | 0 |
| `Dt1Mask` distinct | 22 | 22 | 72 | 8 | 2 |

What the data alone shows (`[C]` as data; the meanings stay `[L]`):
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

### Shared files

Files named by more than one record (the `0x84` candidates from drlg/0002) are listed in
[ds1.md § Files shared between records](../formats/ds1.md#files-shared-between-records-the-0x84-candidates).
`[C]` There are six such files, and **none is named by records of different `SizeX`/`SizeY`**.

## Open questions

- `[L]` Meaning of `Populate`, `Logicals`, `Outdoors`, `Animate`, `KillEdge`, `FillBlanks`, `AutoMap`
  and `PopPad`, and of `Scan`/`Pops` beyond the map-scan gate. Owner: `drlg/preset` (plan 0016 Phase 1; the
  per-kind distributions are in [§ Survey by generator kind](#survey-by-generator-kind-plan-0016-phase-0)). Answered: `Files`,
  the `File1..6` pick, `LevelId`, `SizeX`/`SizeY`, `Expansion` and `Dt1Mask` (see
  [Semantics from the drlg findings](#semantics-from-the-drlg-findings-plan-0008)).
- `[L]` `+0x024`: padding or runtime-filled (backlog → reverser, with the other unknown fields).
