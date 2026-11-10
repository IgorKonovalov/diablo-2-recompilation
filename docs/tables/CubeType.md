# CubeType (`data/global/excel/cubetype.txt` → `cubetype.bin`)

> **Source archive:** `.txt` d2exp, `.bin` d2exp   **Rows:** 15 `.bin` records (= `.txt` data rows)   **Record:** 4 B
> **sha256:** `.txt` `09d9edc27d168ddcd769916664df834338f8309ab496dd639f19d2961728f20b`, `.bin` `44bbcf3339272291a0490eb3cef4abd9749cba7dae19eae2990f99ec7c700ad6`
> **Doc status:** columns and `.bin` layout complete (plan 0068 Phase 1); not loaded

## Purpose

A list of 15 cube item classes (`None`, `hpt`, `mpt`, `gem`, `arm`, `wep`, ...) with a 4-character code. Shipped with a `.bin` that no code loads. No table column holds only these codes. Leads: none.

## Row identity

- `[C]` 15 `.txt` rows (14 non-blank codes), 15 `.bin` records of 4 bytes; rows by position only.
- `[I]` Not loaded: the name `cubetype` does not occur in `Game.exe` ([data/0001](../findings/data/0001-excel-loader.md#answer-summary), [data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables)).

## Columns

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `cube item class` | str, 15 distinct, len <= 13, 0 blank | not compiled | editor name; not in the record | — | [C] shape |
| `Code` | str, 14 distinct, len <= 3, 1 blank | +0x000 4-char code | 4-character code (space padded) | — | [C] layout |

## Interpretation notes

- `[C]` Layout: the 4-character code (`python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel cubetype`, 15 of 15 cells).
- The record count is checked by the full-tier surveys: `excel` (`.bin` count against `.txt` data rows) and `excel_layout` (every `.bin` cell against its `.txt` cell, layout in `tools/excel_layouts.py`) (`python3 -I tools/gate.py --full`).

## Open questions

- None.

