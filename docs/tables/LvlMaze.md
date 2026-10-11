# LvlMaze (`data/global/excel/lvlmaze.txt` → `lvlmaze.bin`)

> **Source archive:** patch_d2 (`lvlmaze.txt`, `lvlmaze.bin`)   **Rows:** 81 (82 data rows − 1 `Expansion` marker at data row 65)
> **Record:** `lvlmaze.bin` 28 B (0x1C)
> **sha256:** `.txt` `b9e04882f357b20ecfc0f166d7699c93119d1aed545503f2f85866c0a89b4dc3`, `.bin` `4da089a98d38235ab2b66bcfffde11f1a7e179c84f796e36a7f37db0b29fc80a`
> **Doc status:** columns listed, `.bin` layout complete, semantics pending (`drlg/maze`)

## Purpose

One record per maze level: the level it applies to, a room count per difficulty, a size pair and a
`Merge` value. Read by the maze generator, `drlg/maze` ([research map](../specs/README.md)), which
owns every column's meaning. Written for plan 0008 Phase 0. Leads: no lead; derived from data.

## Row identity

- `[C]` `Level` is unique in all 81 rows and every value resolves to a `Levels.txt` `Id`
  ([Levels](Levels.md)). It is compiled at `+0x000`; `Name` is not compiled.
- `[C]` The rows are not sorted by `Level` (the Act 5 block runs 107, 113, 115, 118, 114, …). `Name`
  is not unique: `Act 5 - Baal 1` names four rows (levels 128, 129, 130, 132).
- `[I]` The maze generator entry (`0x00673B10`, reached from `DRLG_LevelCreate` for `DrlgType` 1) looks
  the level up in `lvlmaze`, the 28-byte table at `0x0096CA08`
  ([rng/0002](../findings/rng/0002-seed-tree.md)). (fn:DRLG_LevelCreate@0x00642AE0)
  That the lookup matches on `Level` (and not on the row index) is `[L]`. Owner: `drlg/maze`.
- `[C]` Each of the 70 `Levels.txt` rows with `DrlgType` 1 has exactly one `lvlmaze` row. The other 11
  rows name levels with `DrlgType` 2 (levels 13–16, 25, 37, 90, 91, 93, 132) or level 0 (`Null`,
  `DrlgType` 0; the row is named `Act 1 - Cave 1 Treasure`).

## Columns

`[C]` layout tags are by data behaviour: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel lvlmaze`
decodes all 81 records and matches every mapped cell (81 × 7 = 567 cells, 0 mismatches), and
`excel_bin.py unknown … lvlmaze` finds no byte of the 0x1C-byte record outside a mapped field.
Each column's offset is the only one `excel_bin.py probe` finds. The slot widths are `[C]` because
the seven 4-byte fields tile the record. `[L]` The integer type the game reads inside a slot is not
pinned: no code anchor reads a column, and all values are non-negative (`Merge` needs at least 16
bits). The `u32` in the `.bin field` column and in § Record layout is the slot decode `excel_bin.py`
uses, not a claim about that type. The record size is also
the stride the loader passes (`lvlmaze` 28 at `0x0061F46C`, [data/0001](../findings/data/0001-excel-loader.md)).
**Meaning:** no column semantics are claimed here; all are `[L]`, owner `drlg/maze`.

| Column | Observed type / range | `.bin` field | References | Layout tag |
|---|---|---|---|---|
| `Name` | str, 78 distinct, len ≤ 26 | — (editor name; not in the record) | — | — |
| `Level` | int 0..135 (81 distinct) | `+0x000` u32 | `Levels.txt` `Id` | [C] |
| `Rooms` | int 1..61 (13 distinct) | `+0x004` u32 | — | [C] |
| `Rooms(N)` | int 1..61 (15 distinct) | `+0x008` u32 | — | [C] |
| `Rooms(H)` | int 1..61 (17 distinct) | `+0x00C` u32 | — | [C] |
| `SizeX` | int 8..64 (9 distinct) | `+0x010` u32 | — | [C] |
| `SizeY` | int 8..64 (9 distinct) | `+0x014` u32 | — | [C] |
| `Merge` | int 0, 500, 800, 1000 (5 / 69 / 2 / 5 rows) | `+0x018` u32 | — | [C] |
| `Beta` | int 0..1 (1 in 25 rows) | — (no field in `lvlmaze.bin` matches it) | — | — |

## Record layout

`+0x000` `Level` · `+0x004` `Rooms`, `Rooms(N)`, `Rooms(H)` · `+0x010` `SizeX`, `SizeY` · `+0x018`
`Merge`, all 4-byte slots (u32 decode), in `.txt` column order. Every byte is covered. `[C]`

## Interpretation notes

- `[C]` `Rooms ≤ Rooms(N) ≤ Rooms(H)` in every row; 72 of the 81 rows have the same value in all three.
- `[C]` `SizeX = SizeY` in every row but `Act 1 - Barracks` (level 28: 10 × 14).
- `[C]` `Merge` is 0 in exactly the five `Act 1 - Cave N Treasure` rows (all with `Rooms` 1).
- `[L]` Reading the names: `Rooms*` is the number of rooms the maze builds on normal, nightmare and
  hell, `SizeX`/`SizeY` the size of one maze room (in tiles), and `Merge` a chance (per mille?) of
  merging adjacent rooms. None of this is anchored. Owner: `drlg/maze`.

## Open questions

- `[L]` Meaning of every column, and whether the generator matches `Level` or indexes by row. What
  the 11 rows for non-maze levels (and the `Level` 0 row) are used for, if anything. Owner: `drlg/maze`.
