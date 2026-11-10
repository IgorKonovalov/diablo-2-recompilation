# MonItemPercent (`data/global/excel/MonItemPercent.txt` → `monitempercent.bin`)

> **Source archive:** `.txt` d2exp, `.bin` d2exp   **Rows:** 2 `.bin` records (= `.txt` data rows)   **Record:** 4 B
> **sha256:** `.txt` `a49d6d55bff6d557509e7f24231c62dfc6303e9345d89f0950bb1012625f36f7`, `.bin` `01bfe3f20f5167a762a30da619be5d47e59e2909245ed02669f582cd82b4b008`
> **Doc status:** columns and `.bin` layout complete (plan 0068 Phase 1); what the four percentages do is the reverser's (Phase 2)

## Purpose

Two rows, `Composited` and `NonComposited`, each with four percentages named for drops: `HeartPercent`, `BodyPartPercent`, `TreasureClassPercent`, `ComponentPercent`. No spec mentions the table. Which code reads it, what picks a row and what the percentages select are not known from data (plan 0068 Phase 2, item 1). The loader call site is `0x00654FA8`, record size 4, not marked `-txt`-only in [data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables), so `[I]` a stock run loads it ([data/0001 § 3](../findings/data/0001-excel-loader.md#3-what-is-registered-datatbls_loadall-0x00619300)). Leads: none.

## Row identity

- `[C]` Key column `Name`: 2 distinct values, none blank. The `.bin` holds no name: the row index is the only identity (`NonComposited` = 1). Which of the two rows a monster uses is not in the data `[L]`.
- `[C]` No `Expansion` row; 2 `.txt` rows, 2 `.bin` records, 4 bytes each.

## Columns

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `Name` | str, 2 distinct, len <= 13, 0 blank (`Composited`, `NonComposited`) | not compiled | row name; editor text, not in the record | — | [C] shape |
| `HeartPercent` | int, 0..0, 1 distinct, 0 blank | +0x000 u8 | by name a chance (percent) of a heart drop `[L]`; 0 in both rows | — | [I] layout, [L] meaning |
| `BodyPartPercent` | int, 0..0, 1 distinct, 0 blank | +0x001 u8 | by name a chance of a body-part drop `[L]`; 0 in both rows | — | [I] layout, [L] meaning |
| `TreasureClassPercent` | int, 20..20, 1 distinct, 0 blank | +0x002 u8 | by name a chance of a treasure-class drop `[L]`; 20 in both rows | — | [I] layout, [L] meaning |
| `ComponentPercent` | int, 0..0, 1 distinct, 0 blank | +0x003 u8 | by name a chance of a component drop `[L]`; 0 in both rows | — | [I] layout, [L] meaning |

## Interpretation notes

- `[C]` Data: in both records byte +0x2 is 20 and the other three bytes are 0; the four-`u8` layout matches 8 of 8 cells (`python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel monitempercent`).
- `[I]` Layout: four `u8` in column order, +0x0..+0x3. Only `TreasureClassPercent` is non-zero, so only its start (+0x2) is tied to the data; its width and the offsets and widths of the three zero columns are the first fit of `excel_bin.py probe` (a `u16` at +0x0, or at +0x2, fits as well). Column order is assumed because the other tables' records mostly follow their `.txt` order. The reader settles it (plan 0068 Phase 2 item 1).
- Both rows are identical except for the name, so a reader that picks a row cannot be told from the data alone.
- The record count is checked by the full-tier surveys: `excel` (`.bin` count against `.txt` data rows) and `excel_layout` (every `.bin` cell against its `.txt` cell, layout in `tools/excel_layouts.py`) (`python3 -I tools/gate.py --full`).

## Open questions

- `[L]` Every reader, the row choice, and the order of any draw against `TC_ResolveDrops`: plan 0068 Phase 2 item 1. Until then no spec carries this table.

