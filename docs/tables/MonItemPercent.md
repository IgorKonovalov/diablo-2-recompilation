# MonItemPercent (`data/global/excel/MonItemPercent.txt` → `monitempercent.bin`)

> **Source archive:** `.txt` d2exp, `.bin` d2exp   **Rows:** 2 `.bin` records (= `.txt` data rows)   **Record:** 4 B
> **sha256:** `.txt` `a49d6d55bff6d557509e7f24231c62dfc6303e9345d89f0950bb1012625f36f7`, `.bin` `01bfe3f20f5167a762a30da619be5d47e59e2909245ed02669f582cd82b4b008`
> **Doc status:** columns and `.bin` layout complete; loaded, read by no code (plan 0068 Phase 2, [data/0006 § 1](../findings/data/0006-loaded-tables-and-bundles.md#1-monitempercent-plan-item-1))

## Purpose

Two rows, `Composited` and `NonComposited`, each with four percentages named for drops: `HeartPercent`, `BodyPartPercent`, `TreasureClassPercent`, `ComponentPercent`. No spec mentions the table. `[C]` The table is loaded in every run that reaches the table load (loader `sub_00654F20_MonItemPctLoad`, call `0x00654FA8`, record size 4, `count` 2 in the six H3b runs that reach it) and `[I]` no code reads a percentage: the globals `g_nMonItemPercent` (`0x0096D480`) and `g_pMonItemPercent` (`0x0096D484`) have 3 absolute references each, all in the loader, the free function and two dead getters, so nothing picks a row or draws on it, and the drop chain (`TC_ResolveDrops`) has no `MonItemPercent` step ([data/0006 § 1.2-1.3](../findings/data/0006-loaded-tables-and-bundles.md#12-every-reader)). The `[I]` rests on a static scan; an `rwatch` over a session with kills would raise it (reverser backlog). Leads: none.

## Row identity

- `[C]` Key column `Name`: 2 distinct values, none blank. The `.bin` holds no name: the row index is the only identity (`NonComposited` = 1). No code picks a row (below), so the question has no answer in the game `[I]`.
- `[C]` No `Expansion` row; 2 `.txt` rows, 2 `.bin` records, 4 bytes each.

## Columns

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `Name` | str, 2 distinct, len <= 13, 0 blank (`Composited`, `NonComposited`) | not compiled | row name; editor text, not in the record | — | [C] shape |
| `HeartPercent` | int, 0..0, 1 distinct, 0 blank | +0x000 u8 | by name a heart-drop chance `[L]`; 0 in both rows; read by no code `[I]` | — | [I] layout (descriptor offset 0, type 4), [L] meaning |
| `BodyPartPercent` | int, 0..0, 1 distinct, 0 blank | +0x001 u8 | by name a body-part-drop chance `[L]`; 0 in both rows; read by no code `[I]` | — | [I] layout (descriptor offset 1, type 4), [L] meaning |
| `TreasureClassPercent` | int, 20..20, 1 distinct, 0 blank | +0x002 u8 | by name a treasure-class-drop chance `[L]`; 20 in both rows; read by no code `[I]` | — | [C] layout (descriptor offset 2 and the data's only non-zero byte), [L] meaning |
| `ComponentPercent` | int, 0..0, 1 distinct, 0 blank | +0x003 u8 | by name a component-drop chance `[L]`; 0 in both rows; read by no code `[I]` | — | [I] layout (descriptor offset 3, type 4), [L] meaning |

## Interpretation notes

- `[C]` Data: in both records byte +0x2 is 20 and the other three bytes are 0; the four-`u8` layout matches 8 of 8 cells (`python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel monitempercent`).
- `[I]` Layout: four `u8` in column order, +0x0..+0x3: the loader's descriptor gives every field as type 4 (u8) at its own byte (`0x00654F64`-`0x00654F9A`), which settles the probe's alternative fits (a `u16` at +0x0 or +0x2). `+0x2` is `[C]` (descriptor and data agree); the three zero columns cannot be tested by the data. ([data/0006 § 1.5](../findings/data/0006-loaded-tables-and-bundles.md#15-layout-for-the-table-doc))
- Both rows are identical except for the name, so a reader that picks a row cannot be told from the data alone.
- The record count is checked by the full-tier surveys: `excel` (`.bin` count against `.txt` data rows) and `excel_layout` (every `.bin` cell against its `.txt` cell, layout in `tools/excel_layouts.py`) (`python3 -I tools/gate.py --full`).

## Open questions

- `[L]` Whether any run reads a record: the static scan (3 absolute references per global, no displacement operand) leaves a run-time-built address unseen. The reverser's harness piece (`rwatch` on the 8 record bytes during kills) would settle it. Until then no spec carries this table beyond one `[I]` sentence in items/tc (Phase 4).
