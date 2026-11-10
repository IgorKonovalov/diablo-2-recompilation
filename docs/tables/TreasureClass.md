# TreasureClass (`data/global/excel/TreasureClass.txt`)

> **Source archive:** `.txt` d2exp   **Rows:** 707 `.txt` data rows
> **sha256:** `.txt` `99935e641c5d7e3e8f62181873f66b87506a14e113d885388eb2c931010101d0`
> **Doc status:** columns complete (plan 0068 Phase 1); not loaded; the live table is [TreasureClassEx](TreasureClassEx.md)

## Purpose

The classic-era treasure-class table: 707 rows with `Treasure Class`, `Picks`, `Unique`, `Set`, `Rare`, `Magic`, `NoDrop`, ten `Item`/`Prob` pairs and `Term`. It has no `group` or `level` column and fewer rows than [TreasureClassEx](TreasureClassEx.md) (853 records), which is the table the game loads. Leads: none.

## Row identity

- `[C]` Key column `Treasure Class`; 707 data rows (the last is `Smith (H)`). The `.bin` of this table does not exist.
- `[I]` Not loaded by the game: [data/0001 § 3](../findings/data/0001-excel-loader.md#3-what-is-registered-datatbls_loadall-0x00619300) lists it among the `.txt`-only tables with no loader (data/excel B1), and the table is shipped anyway. The absence of a loader is a statement about `Game.exe`, so a stock run reads nothing from this file. The string `treasureclass` in `Game.exe` is an `itemtypes` column name (data/0001 summary).

## Columns

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `Treasure Class` | str, 707 distinct, len <= 19, 0 blank | none (no `.bin`) | name of the class | — | [C] shape |
| `Picks` | int, -3..7, 6 distinct, 0 blank | none (no `.bin`) | picks, as in TreasureClassEx `Picks` `[L]` here | — | [C] shape, [L] meaning |
| quality chances | int, 0..1024, 10 distinct, 2576 blank | none (no `.bin`) | quality and no-drop columns, as in TreasureClassEx `[L]` here | — | [C] shape, [L] meaning |
| items | str, 534 distinct, len <= 17, 3935 blank | none (no `.bin`) | item or class names of the pool | — | [C] shape |
| probabilities | int, 1..81880, 80 distinct, 3908 blank | none (no `.bin`) | weights of the pool items | — | [C] shape |
| `Term` | int, 0..0, 1 distinct, 20 blank | none (no `.bin`) | end-of-line marker column | — | [C] shape |

## Interpretation notes

- The game reads [TreasureClassEx](TreasureClassEx.md); nothing in this table feeds a rule. The meaning of the columns is stated in that doc and the item specs, not re-derived here.
- The record count is checked by the full-tier surveys: the `excel` survey (the `.txt` data row count; there is no `.bin`)`excel_layout` (every `.bin` cell against its `.txt` cell, layout in `tools/excel_layouts.py`) (`python3 -I tools/gate.py --full`).

## Open questions

- None.

