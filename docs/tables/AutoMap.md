# AutoMap (`data/global/excel/AutoMap.txt` → `automap.bin`)

> **Source archive:** `.txt` d2exp, `.bin` d2exp   **Rows:** 3286 `.bin` records (= `.txt` data rows)   **Record:** 44 B
> **sha256:** `.txt` `dfc3b99857c85fe60a11185b4522c7f60b46564afd383ddfac944f69ccedbed3`, `.bin` `1f39ba673bf40a58921e68f579591de54f8789a520379fe4873341848c362a80`
> **Doc status:** columns and `.bin` layout complete (plan 0068 Phase 1); client automap, out of scope (ADR-0014)

## Purpose

3 286 rows that map a level and a tile name (`TileName`, a two-letter tile family such as `fl`) with a style and a sequence range to four automap cel numbers, for the client's automap drawing. No other table references it. Client presentation: out of scope under [ADR-0014](../adrs/0014-scope-game-simulation.md); it is documented so that the table directory is complete. Loader call site `0x0061FE62`, record 44, not `-txt`-only ([data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables)). Leads: none.

## Row identity

- `[C]` No key: 3 286 rows, `LevelName` repeats (34 distinct names, e.g. `1 Town`); a row is a (level, tile family, style, sequence range) record addressed by position.
- `[C]` One `Expansion` marker row: 3 287 `.txt` rows, 3 286 `.bin` records.

## Columns

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `LevelName` | str, 34 distinct, len <= 12, 0 blank | +0x000 char[16] | level group name, 16-byte char array | — | [C] layout, [L] meaning |
| `TileName` | str, 14 distinct, len <= 4, 0 blank | +0x010 char[8] | tile family code, 8-byte char array | — | [C] layout, [L] meaning |
| `Style` | int, 0..49, 47 distinct, 0 blank | +0x018 u8 | tile style number `[L]` | — | [C] layout, [L] meaning |
| `StartSequence`, `EndSequence` | int, -1..63, 65 distinct, 0 blank | +0x019, +0x01A (u8) | first and last tile sequence of the row `[L]` | — | [C] layout, [L] meaning |
| cel types | str, 1230 distinct, len <= 27, 9243 blank | not compiled | cel type names (the `.txt` header repeats `Type2` for the third pair; the doc keys it `Type2#2`); not compiled | — | [C] shape |
| cel numbers | int, -1..1498, 1246 distinct, 0 blank | +0x01C, +0x020, +0x024, +0x028 (u32) | automap cel numbers `[L]`; blank is stored as −1 | — | [C] layout, [L] meaning |

## Interpretation notes

- `[C]` Layout: 16-byte level name, 8-byte tile name, three `u8`, one pad byte (0), four `u32` cel numbers (`python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel automap`, 29 574 of 29 574 cells). The four type columns are text only.
- The record count is checked by the full-tier surveys: `excel` (`.bin` count against `.txt` data rows) and `excel_layout` (every `.bin` cell against its `.txt` cell, layout in `tools/excel_layouts.py`) (`python3 -I tools/gate.py --full`).

## Open questions

- None for the data; out of scope.

