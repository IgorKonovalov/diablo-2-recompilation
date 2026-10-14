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

## Survey (plan 0022 Phase 0)

`python3 -I tools/maze_survey.py workspace/merged/data/global/excel` § 1 prints every row with its level's
`Act`, `DrlgType` and `LevelType`, then the maze levels with their values. Gate survey `maze`
(`tools/gate/baselines/maze.txt`). A maze level is a `Levels.txt` row with `DrlgType` 1. Every count below is
`[C]` by that command. No column meaning is claimed.

- `[C]` **Reconciliation.** 70 levels have `DrlgType` 1 (Act I 18, Act II 26, Act III 9, Act IV 1, Act V 16)
  across 20 level types, and each has exactly one LvlMaze row. LvlMaze has 81 rows: 70 maze rows and 11 others.
  No `Level` repeats, all 81 resolve, and no maze level lacks a row.
- `[C]` The 11 rows whose level is not a maze level:

  | Row | Level | Level name | `DrlgType` | `LevelType` |
  |---|---|---|---|---|
  | 5 | 0 | `Null` (the row is named `Act 1 - Cave 1 Treasure`) | 0 | 0 |
  | 6–9 | 13–16 | `Act 1 - Cave 2..5 Treasure` | 2 | 3 |
  | 16 | 25 | `Act 1 - Crypt 3 E` | 2 | 4 |
  | 24 | 37 | `Act 1 - Catacombs 4` | 2 | 10 |
  | 57, 58 | 90, 91 | `Act 3 - Dungeon 1/2 Treasure` | 2 | 24 |
  | 60 | 93 | `Act 3 - Sewer 2` | 2 | 25 |
  | 78 | 132 | `Act 5 - World Stone` | 2 | 34 |

  The 10 non-`Null` levels are preset levels (`DrlgType` 2). Each names one level in `Vis`: a maze level for
  nine of them, and level 131 (`Act 5 - Throne Room`, preset) for level 132
  ([Levels § Links survey](Levels.md#links-survey-plan-0022-phase-0)). Each has a level type that maze levels
  also use (3, 4, 10, 24, 25, 34). Five of these rows (`Null` and the four cave treasures) are the five rows with
  `Merge` 0. Level 93 is one of the two `Merge` 800 rows; the other is maze level 92.
- `[C]` Per maze level type (levels as `Levels` `Id`; `Rooms` as normal/N/H, or one number when the three are
  equal; size as `SizeX`×`SizeY`):

  | Type | `LvlTypes` name | Maze levels | `Rooms` | Size | `Merge` |
  |---|---|---|---|---|---|
  | 3 | Act 1 - Cave | 8–12 | 1, 4, 6 | 24×24 | 500 |
  | 4 | Act 1 - Crypt | 18, 19, 21–24, 133 | 12/24/36 (18, 19, 133); 6/12/24, 6/12/20, 6/12/16, 6/12/12 (21–24) | 8×8 | 500 |
  | 7 | Act 1 - Barracks | 28 | 10 | 10×14 | 500 |
  | 8 | Act 1 - Jail | 29–31 | 12, 14, 16 | 12×12 | 500 |
  | 10 | Act 1 - Catacombs | 34–36 | 12, 14, 16 | 12×12 | 500 |
  | 13 | Act 2 - Sewer | 47–49, 65 | 6, 12, 14, 10 | 12×12 | 500 |
  | 14 | Act 2 - Harem | 51 | 4 | 16×16 | 1000 |
  | 15 | Act 2 - Basement | 52–54 | 4 | 16×16 | 1000 |
  | 17 | Act 2 - Tomb | 55–61, 66–72 | 4, 6, 12 | 16×16 | 500 |
  | 18 | Act 2 - Lair | 62–64 | 18, 14, 10 | 10×10 | 500 |
  | 19 | Act 2 - Arcane | 74 | 61 | 12×12 | 1000 |
  | 22 | Act 3 - Kurast | 100, 101 | 10/16/16; 12/48/48 | 12×12 | 500 |
  | 23 | Act 3 - Spider | 84, 85 | 4 | 16×16 | 500 |
  | 24 | Act 3 - Dungeon | 86–89 | 4 | 14×14 | 500 |
  | 25 | Act 3 - Sewer | 92 | 32 | 12×12 | 800 |
  | 28 | Act 4 - Lava | 107 | 6 | 24×24 | 500 |
  | 32 | Act 5 - Temple | 122, 123 | 4 | 40×40 | 500 |
  | 33 | Act 5 - Ice Caves | 113–116, 118, 119 | 10, 10, 15 (113, 115, 118); 1 (114, 116, 119) | 16×16; 64×64 (114); 32×32 (116, 119) | 500 |
  | 34 | Act 5 - Baal | 128–130 | 9 | 16×16 | 500 |
  | 35 | Act 5 - Lava | 125–127, 135 | 3 | 24×24 | 500 |

  Level 133 (`Act 5 - Pandemonium 1`) is an Act V level of the Act I `Crypt` type. `Merge` 1000 occurs on
  exactly the levels of three types: Harem, Basement and Arcane.
- `[C]` 15 maze types have a rotation range ([LvlPrest § Maze presets](LvlPrest.md#maze-presets-plan-0022-phase-0)).
  For 13 of them, the LvlMaze size of the type's levels equals `SizeX`×`SizeY` of all 15 range records. The two
  exceptions are type 33, whose one-room levels 114/116/119 are 64×64/32×32, and type 35, whose range holds nine
  16×16 Baal records. `[L]` That `SizeX`/`SizeY` is the size of one maze room fits this agreement, but no code
  anchor backs it yet. Owner: `drlg/maze`.

## Open questions

- `[L]` Meaning of every column, and whether the generator matches `Level` or indexes by row. What
  the 11 rows for non-maze levels (and the `Level` 0 row) are used for, if anything. Owner: `drlg/maze`.
