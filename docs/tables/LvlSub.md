# LvlSub (`data/global/excel/LvlSub.txt` → `lvlsub.bin`)

> **Source archive:** patch_d2 (`LvlSub.txt`, `lvlsub.bin`)   **Rows:** 34 (35 data rows − 1 `Expansion` marker at data row 29)
> **Record:** `lvlsub.bin` 348 B (0x15C)
> **sha256:** `.txt` `d3dc9dc70066f819ff9e0c1b433b327952789ed7ad3e5eadccf7160280ddc64f`, `.bin` `de461fd72b8b72ecce452587e408d9aef84eb679c53f2c78a398cb55b17a0247`
> **Doc status:** columns listed, `.bin` layout complete, semantics partial (from drlg/0002, under review)

## Purpose

One record per substitution: a DS1 file of tile groups that the outdoor generator stamps into a room's
grids (waypoints, shrines, and per-act decoration such as stones, trees, puddles, dunes, palms). Read by
the type 1 (outdoor) room grid prepare, `drlg/outdoor` ([research map](../specs/README.md)), which owns
every column's meaning. Written for plan 0008 Phase 2, from the reverser's backlog request. Leads: no
lead; derived from data. Column names are the `.txt` header row.

## Row identity

- `[C]` `Type` runs 0..12 and the rows are sorted by it: every `Type` is one contiguous block (block
  sizes 1, 1, 1, 1, 2, 4, 6, 1, 4, 7, 3, 2, 1 for `Type` 0..12). `Name` is not unique (`Healing Well`
  names a `Type` 5 and a `Type` 8 row). `File` is unique, and every path resolves to a DS1 under
  `data/global/tiles/` in `workspace/merged/`.
- `[C]` The `Levels.txt` columns `SubType`, `SubWaypoint` and `SubShrine` ([Levels](Levels.md)) hold
  −1 or a `Type` value: `SubType` ∈ {0, 6, 9, 10, 11}, `SubWaypoint` ∈ {0, 4, 7}, `SubShrine` ∈
  {0, 5, 8}. The value 0 occurs only in the `Null` level row (all three columns). `Type` 1, 2, 3 and 12
  are named by no `Levels.txt` row. `SubTheme` is −1..4, the same range as the theme suffix of
  `Prob0..4`/`Trials0..4`/`Max0..4`.
- `[I]` Code addresses a record by `Type` and position, not by row index: `0x0061FA90` returns the first
  record of a `Type` through an index table, and the apply loop at `0x006707A0` takes the *i*-th record
  of that `Type` for mask bit *i* (drlg/0002 (under review), § Type 1 prepare). The contiguous blocks
  above are what that lookup needs. (0x0061FA90, 0x006707A0)
- `[C]` The block sizes fit the masks drlg/0002 reads: `SubWaypoint` passes a 2-bit mask (room `+0x28`
  bits 16–17) and its `Type`s 4 and 7 have 2 and 1 records; `SubShrine` passes a 4-bit mask (bits
  12–15) and its `Type`s 5 and 8 have 4 records each. That the mask comes from those room bits is `[I]`
  in drlg/0002 (0x0067D2D0), not a data fact.

## Columns

`[C]` layout tags are by data behaviour: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel lvlsub`
decodes all 34 records and matches every mapped cell (34 × 22 = 748 cells, 0 mismatches). `excel_bin.py
unknown … lvlsub` finds two ranges outside a mapped column, both zero in all 34 records: `+0x050`
(4 B, `unk_050`) and `+0x054..+0x11B` (200 B). Every offset but `CheckAll`'s is the only one
`excel_bin.py probe` finds. `CheckAll` is 0 in every row, so probe matches it at thousands of zero
bytes; its `+0x040` comes from the code (drlg/0002) and from being the only 4-byte slot left between
`File` and `BordType`. The record size is the stride the loader passes (`lvlsub` 348 at `0x0061F842`,
[data/0001](../findings/data/0001-excel-loader.md)). `[L]` The integer type the game reads inside a slot
is not pinned by the data: the `u32`/`s32` in the `.bin field` column is the decode `excel_bin.py` uses
(`s32` where a cell is −1), not a claim about that type.

**Meaning tags** are `[I]` only where drlg/0002 (under review) reads the column in code
(`0x006707A0`, `0x0066FF50`, `0x00670170`, `0x006704E0`); every other meaning is `[L]`, owner
`drlg/outdoor`.

| Column | Observed type / range | `.bin` field | Meaning | References | Layout tag | Meaning tag |
|---|---|---|---|---|---|---|
| `Name` | str, 33 distinct, len ≤ 16 | — (editor name; not in the record) | — | — | — | — |
| `Type` | int 0..12 (13 distinct) | `+0x000` u32 | substitution group; records of one `Type` are selected by mask bit | `Levels.txt` `SubType`/`SubWaypoint`/`SubShrine` | [C] | [I] |
| `File` | str, 34 distinct, len ≤ 38 | `+0x004` char[60] | DS1 loaded on first use; its groups are the stamp candidates | DS1 under `data/global/tiles/` | [C] | [I] |
| `Expansion` | int 0..1 (1 in the 6 rows after the marker) | `+0x158` u32 | — | — | [C] | [L] |
| `CheckAll` | int 0 (all rows) | `+0x040` u32 (code offset, see above) | ≠ 0: try every position (`0x0066FF50`); 0: random group and position (`0x00670170`) | — | [C] | [I] |
| `BordType` | int −1..2 (−1 in 29 rows) | `+0x044` s32 | — | — | [C] | [L] |
| `GridSize` | int 1..2 (2 in 1 row, `Barricade`) | `+0x04C` u32 | — | — | [C] | [L] |
| `Dt1Mask` | int 0..0x400001 (16 distinct) | `+0x048` u32 | — | `LvlTypes` `File N` (bit *i* → `File i+1`?) | [C] | [L] |
| `Prob0..4` | int 0..100 | `+0x11C` + 4·t u32 | per theme t: percent threshold for a tag-2 group match (`CheckAll` ≠ 0) | `Levels.txt` `SubTheme` | [C] | [I] |
| `Trials0..4` | int −1..20 | `+0x130` + 4·t s32 | per theme t: placement attempts per group; −1 = shuffle all positions (`CheckAll` = 0) | `Levels.txt` `SubTheme` | [C] | [I] |
| `Max0..4` | int 0..12 | `+0x144` + 4·t u32 | per theme t: groups to place (`CheckAll` = 0) | `Levels.txt` `SubTheme` | [C] | [I] |
| `Beta` | int 0..1 (1 in the 16 Act 1 rows) | — (no field in `lvlsub.bin` matches it) | — | — | — | — |

## Record layout

`+0x000` `Type` · `+0x004` `File` (60-byte NUL-terminated) · `+0x040` `CheckAll` · `+0x044` `BordType` ·
`+0x048` `Dt1Mask` · `+0x04C` `GridSize` · `+0x050` `unk_050` (4 B, 0 in the file) · `+0x054..+0x11B`
200 B, 0 in the file · `+0x11C` `Prob0..4` · `+0x130` `Trials0..4` · `+0x144` `Max0..4` · `+0x158`
`Expansion`. Every byte is covered. `[C]`

- `[C]` The record does **not** follow `.txt` column order. `Dt1Mask` (`.txt` column 8) sits before
  `GridSize` (column 7), and the `.txt`'s per-theme triples `Prob t, Trials t, Max t` are stored as three
  arrays of five. `Expansion` (`.txt` column 4) is last. Probe pins each of these offsets uniquely
  (`Dt1Mask` takes 16 distinct values, `GridSize` 2, so the swap cannot be a coincidence of equal
  values). This confirms the reverser's offsets in drlg/0002 § Data touched, including the
  `Dt1Mask`/`GridSize` swap.
- `[I]` `+0x050` holds the record's loaded DS1 pointer at run time (drlg/0002, `0x006704E0` loads on
  first use). What `+0x054..+0x11B` holds at run time is `[L]`.

## Interpretation notes

- `[I]` One `LvlSub` pass is (type, theme, mask): for each set mask bit *i*, record *i* of `Type` is
  loaded and applied, with `CheckAll` choosing between the exhaustive (`0x0066FF50`) and the random
  (`0x00670170`) apply. The type 1 prepare `0x0067D2D0` runs three passes in order: `SubWaypoint`
  (theme 0), `SubShrine` (theme 0), then `SubType` with the room's theme and mask. The draws each pass
  makes on the room seed are written out in drlg/0002 (under review) § Type 1 prepare. (0x0067D2D0, 0x006707A0)
- `[I]` Only `Type`, `File`, `CheckAll`, `Prob`, `Trials` and `Max` are read on those paths
  (drlg/0002 § Data touched). `BordType`, `Dt1Mask`, `GridSize` and `Expansion` have no code anchor.
- `[C]` The waypoint and shrine rows (`Type` 4, 5, 7, 8) all have `Prob` 100, `Trials` −1, `Max` 1 in
  every theme and `Dt1Mask` 1. The four `Border - *` rows and `Barricade` have all-zero
  `Prob`/`Trials`/`Max` and `Dt1Mask` 0; they are the only rows with `BordType` ≠ −1.
- `[L]` Reading the names: `Dt1Mask` selects the `LvlTypes` DT1 files the substitution's tiles come
  from (bit *i* → `File i+1`, as for `LvlPrest.Dt1Mask`), `BordType` and `GridSize` describe border
  pieces and the grid unit. None of this is anchored. Owner: `drlg/outdoor`.

## Open questions

- `[L]` What `BordType`, `GridSize` and `Dt1Mask` do, and which code reads them (none of the drlg/0002
  paths does). Whether `Type` 0..3 (borders) and 12 (`Barricade`) are used outside `Levels.txt`'s three
  `Sub*` columns. Owner: `drlg/outdoor`.
- `[L]` Whether `+0x054..+0x11B` is used at run time. Owner: `drlg/outdoor`.
