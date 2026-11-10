# CubeMod (`data/global/excel/cubemod.txt` → `cubemod.bin`)

> **Source archive:** `.txt` d2exp, `.bin` d2exp   **Rows:** 12 `.bin` records (= `.txt` data rows)   **Record:** 4 B
> **sha256:** `.txt` `58c50ced7a4d922b5af42bf5738ff63d4e1306435beab1d994ce0b1214d4b138`, `.bin` `46162fde6e8b0910562fcf1c962ada2256621c4b5e651ecf7c707dabbd3021e6`
> **Doc status:** columns and `.bin` layout complete (plan 0068 Phase 1); not loaded

## Purpose

A list of 12 cube modifier types (`None`, then gem and quality words such as `ame`, `rub`, `crf`, `rar`, `unq`) with a 4-character code. Shipped with a `.bin` that no code loads. No table column holds only these codes. Leads: none.

## Row identity

- `[C]` 12 `.txt` rows (11 non-blank codes), 12 `.bin` records of 4 bytes; rows by position only.
- `[I]` Not loaded: the name `cubemod` does not occur in `Game.exe` ([data/0001](../findings/data/0001-excel-loader.md#answer-summary), [data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables)).

## Columns

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `cube modifier type` | str, 12 distinct, len <= 8, 0 blank | not compiled | editor name; not in the record | — | [C] shape |
| `Code` | str, 11 distinct, len <= 3, 1 blank | +0x000 4-char code | 4-character code (space padded) | — | [C] layout |

## Interpretation notes

- `[C]` Layout: the 4-character code (`python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel cubemod`, 12 of 12 cells). Layout added in plan 0068 so the survey keeps the shipped `.bin` honest.
- The record count is checked by the full-tier surveys: `excel` (`.bin` count against `.txt` data rows) and `excel_layout` (every `.bin` cell against its `.txt` cell, layout in `tools/excel_layouts.py`) (`python3 -I tools/gate.py --full`).

## Open questions

- None.

