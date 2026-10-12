# MonLvl (`data/global/excel/MonLvl.txt`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 111 (levels 0..110; no `Expansion` marker)   **Record:** 120 B
> **sha256:** `.txt` `bda243efe1d1e9591f75b8cf97ac73f78ff691362381f35cc000233eb46c092a`, `.bin` `7dc108d66df6bad7032bd6678d23f9864b398f2b71ee24c3ac88528dc7832499`
> **Doc status:** columns listed, `.bin` layout complete, semantics pending

## Purpose

One row per monster level 0..110, with five per-level base values (`AC`, `TH`, `HP`, `DM`, `XP`), each
in six columns: three for the classic game (normal, nightmare, hell) and three prefixed `L-` (by
the name, the expansion game). By the names they are the monster armour class, to-hit, hit points,
damage and experience a monster of that level gets, which `MonStats` columns scale `[L]`. Read by
`monsters/stats`. Plan 0012 lists it to settle whether the *monster level* rule (`monsters/pool`) reads it
at all; the plan expects it to be stats only.

## Row identity

- `[C]` `Level` equals the row index (0..110) in every row and is **not compiled**: no field of
  `monlvl.bin` holds it, so a record is addressed by its position. (tbl:MonLvl.txt:Level)
- `[C]` The loader reads `monlvl.bin` with 120-byte records
  ([data/0001 §4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables), call site
  `0x00659956`). The `.bin` record count (111) equals the `.txt` data rows.

## Columns

`[C]` layout tags are by data behaviour: `python3 -I tools/excel_bin.py diff <excel-dir> monlvl`
decodes every record and compares it with every mapped cell (111 records × 30 fields = 3 330 cells,
0 mismatches). A field is tagged `[C]` when the column's values pin its offset (a probe over every
record finds no other offset that fits), `[I]` when the column is identical to a sibling column, so its
position comes from the stride of its group. Widths: every field is u32 by the stride (`XP` needs 32
bits, the 30 fields fill the 120 bytes exactly); signedness is `[I]` (every value is ≥ 1).
**Meaning:** no column semantics are claimed here; the readings of the names are `[L]`.

| Column | Observed type / range | `.bin` field | Equal to | Layout tag |
|---|---|---|---|---|
| `Level` | int 0..110, = row index | — (not compiled) | — | — |
| `AC` | int 1..2100 (111 distinct) | `+0x000` u32 | `L-AC` | [I] |
| `AC(N)` | int 1..2100 (111 distinct) | `+0x004` u32 | — | [C] |
| `AC(H)` | int 1..2100 (111 distinct) | `+0x008` u32 | — | [C] |
| `L-AC` | int 1..2100 (111 distinct) | `+0x00C` u32 | `AC` | [I] |
| `L-AC(N)` | int 1..2100 (111 distinct) | `+0x010` u32 | — | [C] |
| `L-AC(H)` | int 1..2100 (111 distinct) | `+0x014` u32 | — | [C] |
| `TH` | int 1..6532 (111 distinct) | `+0x018` u32 | `L-TH` | [I] |
| `TH(N)` | int 1..6532 (111 distinct) | `+0x01C` u32 | `L-TH(N)` | [I] |
| `TH(H)` | int 1..6532 (111 distinct) | `+0x020` u32 | `L-TH(H)` | [I] |
| `L-TH` | int 1..6532 (111 distinct) | `+0x024` u32 | `TH` | [I] |
| `L-TH(N)` | int 1..6532 (111 distinct) | `+0x028` u32 | `TH(N)` | [I] |
| `L-TH(H)` | int 1..6532 (111 distinct) | `+0x02C` u32 | `TH(H)` | [I] |
| `HP` | int 1..10000 (111 distinct) | `+0x030` u32 | `L-HP` | [I] |
| `HP(N)` | int 1..10000 (111 distinct) | `+0x034` u32 | `L-HP(N)` | [I] |
| `HP(H)` | int 1..10000 (111 distinct) | `+0x038` u32 | — | [C] |
| `L-HP` | int 1..10000 (111 distinct) | `+0x03C` u32 | `HP` | [I] |
| `L-HP(N)` | int 1..10000 (111 distinct) | `+0x040` u32 | `HP(N)` | [I] |
| `L-HP(H)` | int 1..10000 (111 distinct) | `+0x044` u32 | — | [C] |
| `DM` | int 1..130 (68 distinct) | `+0x048` u32 | `L-DM` | [I] |
| `DM(N)` | int 1..130 (68 distinct) | `+0x04C` u32 | `L-DM(N)` | [I] |
| `DM(H)` | int 1..130 (68 distinct) | `+0x050` u32 | `L-DM(H)` | [I] |
| `L-DM` | int 1..130 (68 distinct) | `+0x054` u32 | `DM` | [I] |
| `L-DM(N)` | int 1..130 (68 distinct) | `+0x058` u32 | `DM(N)` | [I] |
| `L-DM(H)` | int 1..130 (68 distinct) | `+0x05C` u32 | `DM(H)` | [I] |
| `XP` | int 1..160000 (111 distinct) | `+0x060` u32 | `L-XP` | [I] |
| `XP(N)` | int 1..160000 (111 distinct) | `+0x064` u32 | `L-XP(N)` | [I] |
| `XP(H)` | int 1..160000 (111 distinct) | `+0x068` u32 | `L-XP(H)` | [I] |
| `L-XP` | int 1..160000 (111 distinct) | `+0x06C` u32 | `XP` | [I] |
| `L-XP(N)` | int 1..160000 (111 distinct) | `+0x070` u32 | `XP(N)` | [I] |
| `L-XP(H)` | int 1..160000 (111 distinct) | `+0x074` u32 | `XP(H)` | [I] |

The ranges are over all 111 rows; row 0 is 1 in every column and row 110 holds the maxima
(`AC` 2100, `TH` 6532, `HP` 10000, `DM` 130, `XP` 160000) in all six columns of each group.

## Record layout (120 bytes)

Thirty u32 in `.txt` column order, `Level` left out: for each group g = `AC`, `TH`, `HP`, `DM`, `XP`
(`+0x18·g`), the classic triple `X`, `X(N)`, `X(H)` at `+0x00/+0x04/+0x08`, then `L-X`, `L-X(N)`,
`L-X(H)` at `+0x0C/+0x10/+0x14`. No unknown bytes.

- `[C]` The order is pinned by the six columns of the three pairs whose classic and `L-` values differ:
  `AC(N)`, `AC(H)` (`+0x004`, `+0x008`), `L-AC(N)`, `L-AC(H)` (`+0x010`, `+0x014`), `HP(H)` (`+0x038`) and
  `L-HP(H)` (`+0x044`); probe finds one offset for each. Every other
  column equals its classic or `L-` twin in every row, so probe accepts both slots of the pair and the
  slot comes from that order `[I]`. A reader of the record cannot tell which twin it reads, and with
  stock data it does not matter.

## Interpretation notes

- `[C]` **The classic and expansion columns differ in three pairs only.** `AC(N)`, `AC(H)` and `HP(H)`
  differ from their `L-` columns; `AC`, every `TH`, `HP`, `HP(N)`, every `DM` and every `XP` column are equal
  to their `L-` twin in all 111 rows. So with stock data, a classic/expansion switch on this table
  only changes nightmare and hell armour class and hell hit points. (tbl:MonLvl.txt:AC(N), tbl:MonLvl.txt:HP(H))
- `[I]` The reader is `sub_006538A0_MonLvlStats`, called by the monster init after the monster level is set. It
  reads row `min(level, 110)` (the row count − 1) and picks the column as `+0x18·g + 0xC·Lflag + 4·d` (for `HP`:
  `0x30 + 0xC·Lflag + 4·d`), which is this doc's layout. `Lflag` = 1, the `L-` columns, when game `+0x6A` ≠ 0 **or**
  game `+0x74` ≠ 0; it is **not** the expansion flag (`+0x70`) that `sub_0061DCA0_LevelMonLvl` uses for
  `Levels.MonLvl*Ex`. `game+0x6A` was 3 in every logged single-player game, classic ones included, so single
  player reads the `L-` columns. ([monsters/0001](../findings/monsters/0001-level-pool.md) § 5, fn:sub_006538A0_MonLvlStats@0x006538A0, fn:sub_00573CB0_MonStatsInit@0x00573CB0, tbl:MonLvl.txt:HP)
- `[I]` The level pool and the monster-level rule do not read this table; it only feeds stats. ([monsters/0001](../findings/monsters/0001-level-pool.md) § 5)
- `[L]` Read by the names, a monster's base AC/TH/HP/DM/XP are this table's row at the monster's
  level, scaled by the percentages in `MonStats` (`AC`, `A1TH`, `minHP`…). How the stats use the values is owned
  by `monsters/stats`.

## Open questions

- `[L]` How each value is scaled into the monster's stats (`monsters/stats`), and what `game+0x6A` and `+0x74`
  mean beyond "non-zero in single player" (backlog → reverser if a spec needs it).
