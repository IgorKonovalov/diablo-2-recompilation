# LvlPrest (`data/global/excel/lvlprest.txt` → `lvlprest.bin`)

> **Source archive:** patch_d2 (`lvlprest.txt`, `lvlprest.bin`)   **Rows:** 1091 (1092 data rows − 1 `Expansion` marker at data row 863)
> **Record:** `lvlprest.bin` 432 B
> **sha256:** `.txt` `c2f6a891f07145fcffd8755b6fd163f86b6c3363fc45e9c6fe133436f7ae3f9e`, `.bin` `bdb6b98a648de5fde9cf1e587a28140786960d7fceba4b8064ef5584ec199c30`
> **Doc status:** columns listed, `.bin` layout complete, semantics pending

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
column's offset is the only one a probe finds. Widths are `[C]`; signedness is `[I]` (`s` where the
column holds negative values). The `File1..6` arrays are 60 bytes apart, and no cell is longer than
40 characters. **Meaning:** no column semantics are claimed here.

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
| `SizeX` | int 0..64 (12 distinct) | `+0x028` s32 | — | [C] |
| `SizeY` | int 0..64 (12 distinct) | `+0x02C` s32 | — | [C] |
| `AutoMap` | int 0..1 (2 distinct) | `+0x030` u32 | — | [C] |
| `Scan` | int 0..1 (2 distinct) | `+0x034` u32 | — | [C] |
| `Pops` | int 0..4 (5 distinct) | `+0x038` u32 | — | [C] |
| `PopPad` | int -5..0 (3 distinct) | `+0x03C` s32 | — | [C] |
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
`Expansion` (u32) · `+0x024` unknown u32 · `+0x028` `SizeX`, `SizeY` (s32), `AutoMap`, `Scan`, `Pops`
(u32), `PopPad` (s32), `Files` (u32) · `+0x044` `File1..6` (`char[60]` each) · `+0x1AC` `Dt1Mask`
(u32). `Expansion`, the last `.txt` column, is compiled at `+0x020`, out of header order.

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

## Open questions

- `[L]` Meaning of `Populate`, `Logicals`, `Outdoors`, `Animate`, `KillEdge`, `FillBlanks`, `AutoMap`,
  `Scan`, `Pops`, `PopPad`, `Files` and `Dt1Mask` (a bitmask of `LvlTypes` files?), and how the game
  picks one of `File1..6`. Owned by the drlg plans (backlog).
- `[L]` `+0x024`: padding or runtime-filled (backlog → reverser, with the other unknown fields).
