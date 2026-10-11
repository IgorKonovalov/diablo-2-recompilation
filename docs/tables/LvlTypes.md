# LvlTypes (`data/global/excel/LvlTypes.txt` → `lvltypes.bin`)

> **Source archive:** patch_d2 (`LvlTypes.txt`, `lvltypes.bin`)   **Rows:** 36 (37 data rows − 1 `Expansion` marker at data row 30)
> **Record:** `lvltypes.bin` 1928 B (0x788)
> **sha256:** `.txt` `4d8a6cc08afd6c66a493b677b1601182695a437dcc0ab5fedecc379537e5c84c`, `.bin` `9399f78364f96ef4bbd3971f808ada15af810dde65c76e9b9132128c8e2c3ece`
> **Doc status:** columns listed, `.bin` layout complete, semantics partial (DT1 list anchored by drlg/0001)

## Purpose

One record per level type: the up-to-32 DT1 tile files a level of that type can draw its tiles
from, plus an act number and an expansion flag. Read by `drlg/overview` (a room's DT1 list) and
`drlg/collision` ([research map](../specs/README.md)). The DT1 files are in
[dt1.md](../formats/dt1.md). Written for plan 0008 Phase 0. Leads: no lead; derived from data and
from the code anchors of [drlg/0001](../findings/drlg/0001-ds1-dt1-readers.md).

## Row identity

- `[C]` `Id` equals the data row index once the `Expansion` marker row is dropped (0..35) in every
  row. Neither `Id` nor `Name` is compiled: `lvltypes.bin` holds no field that matches either, so a
  record is addressed by its index. `Name` is unique in all 36 rows.
- `[I]` The game addresses a record as `g_pLvlTypes + i·0x788`.
  (fn:LVLTYPES_GetRecord@0x0061EAA0, data:g_pLvlTypes@0x0096C9F0, data:g_nLvlTypes@0x0096C9FC)
- `[C]` `Levels.txt` `LevelType` (`leveldefs +0x34`, [Levels](Levels.md#leveldefs-0x30--0x34)) takes
  every value 0..35, so every row is used by at least one level. That `LevelType` is the index
  `LVLTYPES_GetRecord` receives is `[L]`: drlg/0001 reads the type from level `+0x1C0` and does not
  trace where that field is filled. Owner: `drlg/overview`.

## Columns

`[C]` layout tags are by data behaviour: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel lvltypes`
decodes all 36 records and matches every mapped cell (36 × 34 = 1224 cells, 0 mismatches), and
`excel_bin.py unknown … lvltypes` finds no byte of the 0x788-byte record outside a mapped field.
Each column's offset is the only one `excel_bin.py probe` finds. The slot widths are `[C]` because
the fields tile the record with no gap. `[L]` The integer type the game reads inside a slot (narrower
read, signedness) is not pinned: no code anchor reads `Act` or `Expansion`, and the data is
non-negative and fits a byte in every case. The `u32` in the `.bin field` column and in § Record
layout is the slot decode `excel_bin.py` uses, not a claim about that type.
The record size is also the stride the loader passes (`lvltypes` 1928 at `0x0061EA29`,
[data/0001](../findings/data/0001-excel-loader.md)).
**Meaning:** `[L]` unless the line cites an anchor; see *Interpretation notes*.

| Column | Observed type / range | `.bin` field | References | Layout tag |
|---|---|---|---|---|
| `Name` | str, 36 distinct, len ≤ 18 | — (editor name; not in the record) | — | — |
| `Id` | int 0..35 (36 distinct) = row index | — (not in the record) | `Levels.txt` `LevelType` | — |
| `File 1` | str, 35 named (`0` in 1), len ≤ 33 | `+0x000` char[60] | DT1 path under `data/global/tiles/` | [C] |
| `File 2` | str, 29 named (`0` in 7), len ≤ 28 | `+0x03C` char[60] | DT1 path under `data/global/tiles/` | [C] |
| `File 3` | str, 27 named (`0` in 9), len ≤ 32 | `+0x078` char[60] | DT1 path under `data/global/tiles/` | [C] |
| `File 4` | str, 25 named (`0` in 11), len ≤ 31 | `+0x0B4` char[60] | DT1 path under `data/global/tiles/` | [C] |
| `File 5` | str, 23 named (`0` in 13), len ≤ 33 | `+0x0F0` char[60] | DT1 path under `data/global/tiles/` | [C] |
| `File 6` | str, 24 named (`0` in 12), len ≤ 34 | `+0x12C` char[60] | DT1 path under `data/global/tiles/` | [C] |
| `File 7` | str, 21 named (`0` in 15), len ≤ 27 | `+0x168` char[60] | DT1 path under `data/global/tiles/` | [C] |
| `File 8` | str, 18 named (`0` in 18), len ≤ 28 | `+0x1A4` char[60] | DT1 path under `data/global/tiles/` | [C] |
| `File 9` | str, 19 named (`0` in 17), len ≤ 28 | `+0x1E0` char[60] | DT1 path under `data/global/tiles/` | [C] |
| `File 10` | str, 14 named (`0` in 22), len ≤ 26 | `+0x21C` char[60] | DT1 path under `data/global/tiles/` | [C] |
| `File 11` | str, 11 named (`0` in 25), len ≤ 28 | `+0x258` char[60] | DT1 path under `data/global/tiles/` | [C] |
| `File 12` | str, 8 named (`0` in 28), len ≤ 27 | `+0x294` char[60] | DT1 path under `data/global/tiles/` | [C] |
| `File 13` | str, 7 named (`0` in 29), len ≤ 30 | `+0x2D0` char[60] | DT1 path under `data/global/tiles/` | [C] |
| `File 14` | str, 6 named (`0` in 30), len ≤ 34 | `+0x30C` char[60] | DT1 path under `data/global/tiles/` | [C] |
| `File 15` | str, 5 named (`0` in 31), len ≤ 27 | `+0x348` char[60] | DT1 path under `data/global/tiles/` | [C] |
| `File 16` | str, 5 named (`0` in 31), len ≤ 29 | `+0x384` char[60] | DT1 path under `data/global/tiles/` | [C] |
| `File 17` | str, 4 named (`0` in 32), len ≤ 29 | `+0x3C0` char[60] | DT1 path under `data/global/tiles/` | [C] |
| `File 18` | str, 4 named (`0` in 32), len ≤ 25 | `+0x3FC` char[60] | DT1 path under `data/global/tiles/` | [C] |
| `File 19` | str, 4 named (`0` in 32), len ≤ 29 | `+0x438` char[60] | DT1 path under `data/global/tiles/` | [C] |
| `File 20` | str, 4 named (`0` in 32), len ≤ 34 | `+0x474` char[60] | DT1 path under `data/global/tiles/` | [C] |
| `File 21` | str, 3 named (`0` in 33), len ≤ 25 | `+0x4B0` char[60] | DT1 path under `data/global/tiles/` | [C] |
| `File 22` | str, 3 named (`0` in 33), len ≤ 33 | `+0x4EC` char[60] | DT1 path under `data/global/tiles/` | [C] |
| `File 23` | str, 3 named (`0` in 33), len ≤ 31 | `+0x528` char[60] | DT1 path under `data/global/tiles/` | [C] |
| `File 24` | str, 3 named (`0` in 33), len ≤ 34 | `+0x564` char[60] | DT1 path under `data/global/tiles/` | [C] |
| `File 25` | str, 3 named (`0` in 33), len ≤ 33 | `+0x5A0` char[60] | DT1 path under `data/global/tiles/` | [C] |
| `File 26` | str, 3 named (`0` in 33), len ≤ 30 | `+0x5DC` char[60] | DT1 path under `data/global/tiles/` | [C] |
| `File 27` | str, 2 named (`0` in 34), len ≤ 27 | `+0x618` char[60] | DT1 path under `data/global/tiles/` | [C] |
| `File 28` | str, 2 named (`0` in 34), len ≤ 25 | `+0x654` char[60] | DT1 path under `data/global/tiles/` | [C] |
| `File 29` | str, 2 named (`0` in 34), len ≤ 27 | `+0x690` char[60] | DT1 path under `data/global/tiles/` | [C] |
| `File 30` | str, 1 named (`0` in 35), len ≤ 24 | `+0x6CC` char[60] | DT1 path under `data/global/tiles/` | [C] |
| `File 31` | str, 1 named (`0` in 35), len ≤ 28 | `+0x708` char[60] | DT1 path under `data/global/tiles/` | [C] |
| `File 32` | `0` in all 36 | `+0x744` char[60] | DT1 path under `data/global/tiles/` | [C] |
| `Beta` | int 0..1 (1 in 4 rows) | — (no field in `lvltypes.bin` matches it) | — | — |
| `Act` | int 0..5 (0 only in row 0 `None`) | `+0x780` u32 | — | [C] |
| `Expansion` | int 0..1 (1 in rows 29..35) | `+0x784` u32 | — | [C] |

## Record layout

`+0x000` `File 1..32` (`char[60]` each, 0x3C apart, ending at `+0x780`) · `+0x780` `Act` (4-byte slot, u32 decode) ·
`+0x784` `Expansion` (4-byte slot, u32 decode). Every byte is covered. `[C]`

- `[C]` **The `File 1..32` stride agrees with the code.** drlg/0001 reads `DRLG_LoadLvlTypes` as
  loading 0x788-byte records with `File 1..32` at a 0x3C stride from `+0x00`, and
  `DRLG_LevelDt1ListBuild` steps `file += 0x3C` from the record base for bits 0..31 of the room mask.
  The data puts `File 1` at `+0x000` and `File k` at `+0x3C·(k−1)` in all 36 records: code anchor plus
  data behaviour. (fn:DRLG_LoadLvlTypes@0x0061E520, fn:DRLG_LevelDt1ListBuild@0x0066F240)
- `[C]` Each `char[60]` is NUL-terminated and zero-filled after the NUL in all 1152 slots. The
  longest cell is 34 characters.

## Interpretation notes

- `[C]` `File 1..32` hold DT1 paths relative to `data/global/tiles/` (e.g. `Act1/Town/Floor.dt1`),
  in mixed case, with `/` separators. The literal `0` means none and is stored as the string `"0"`.
  All 319 named cells (230 distinct paths) resolve case-insensitively to a shipped `.dt1`
  ([dt1.md](../formats/dt1.md)). `File 32` is `0` in every row; type 31 (`Act 5 - Barricade`) names 31.
- `[C]` Named cells are not always contiguous: types 1 (`Act 1 - Town`), 8 (`Act 1 - Jail`) and 15
  (`Act 2 - Basement`) have a `0` before a later named file. A slot index is therefore not a
  "count of files".
- `[I]` **Bit *i* of a DRLG room's DT1 mask (room `+0x50`) selects `File i+1`** of the level type at
  level `+0x1C0`; the selected files go into the room's 32-slot DT1 list, followed by three fixed files
  (`Act1\Outdoors\Blank.dt1`, `Act1\Barracks\InvisWal.dt1`, `Act1\Barracks\Warp.dt1`). So the slot
  index, gaps included, is the mask bit number. (fn:DRLG_LevelDt1ListBuild@0x0066F240,
  fn:DT1_ListAdd@0x00604A40)
- `[I]` At load each path is rewritten in place: `/` becomes `\` and the cell gets a `"%s\%s"`
  prefix. (fn:DRLG_LoadLvlTypes@0x0061E520, fn:sub_0061E4A0_TilePathPrefix@0x0061E4A0)
  `python3 -I tools/dt1.py lvltypes workspace/merged <Id>` prints one type's 32 slots with their mask
  bit, record offset and prefixed path, and exits non-zero if a named file is missing. The base string
  the prefix inserts is not anchored for this table: the tool defaults to `DATA\GLOBAL\Tiles`, the
  prefix of the three fixed files above (`--base` overrides). `[L]`
- `[C]` `Act` is 1..5 on every row but row 0 (`None`, `Act` 0), and `Expansion` is 1 exactly on the
  rows after the `Expansion` marker (29..35, `Act` 5).
- `[C]` For 133 of the 136 levels with a non-zero `LevelType`, the type's `Act` equals `Levels.Act + 1`.
  The three exceptions are Act 5 levels 133, 134 and 136 (`Pandemonium 1`, `2`, `Finale`), which use
  types 4, 16 and 11 (`Act` 1, 2, 1).

## Open questions

- `[L]` What `Act` and `Expansion` are used for (an expansion gate on loading, as `DRLG_LoadLvlPrest`
  does for LvlPrest?), and what happens when a mask bit selects a `"0"` slot. Owner: `drlg/overview`.
- `[L]` The base string of the `"%s\%s"` prefix, and whether `"0"` cells are prefixed too. Owner:
  `drlg/overview` (backlog → reverser).
- `[L]` Where level `+0x1C0` comes from (`Levels.txt` `LevelType` is the obvious candidate). Owner:
  `drlg/overview`.
