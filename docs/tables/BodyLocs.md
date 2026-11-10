# BodyLocs (`data/global/excel/BodyLocs.txt` → `bodylocs.bin`)

> **Source archive:** `.txt` d2exp, `.bin` d2exp   **Rows:** 11 `.bin` records (= `.txt` data rows)   **Record:** 4 B
> **sha256:** `.txt` `6b3a6ac0bb1cef5e7f216f083ef85082acedf22c4bbfacf5b254fb36ecd8bbd5`, `.bin` `0ab153d73217c1f56846f143487bed1d6498a45de8a83af6014c8250137687c6`
> **Doc status:** complete for columns and layout (plan 0068 Phase 1); readers of the row index are in the item and creation specs

## Purpose

The 11 equipment locations: `None`, `Head`, `Neck`, `Torso`, `Right Arm`, `Left Arm`, `Right Ring`, `Left Ring`, `Belt`, `Feet`, `Gloves`, each with a 4-character code. Other tables name a location by that code and the `.bin` of those tables stores the BodyLocs row index: [ItemTypes](ItemTypes.md) `BodyLoc1`/`BodyLoc2` and [MonEquip](MonEquip.md) `loc1..loc3`. [player/creation](../specs/player/creation.md) E6 and [items/inventory](../specs/items/inventory.md) I6 use the row index (4 `rarm`, 5 `larm`). Leads: none.

## Row identity

- `[C]` Rows are addressed by **row index**: `None` is row 0 and has a blank code (stored as four spaces), the other ten rows are 1..10 in file order. MonEquip `loc1` stores that index (`python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel monequip`).
- `[C]` No `Expansion` row; 11 `.txt` rows, 11 `.bin` records.
- `[I]` The `.bin` is read only under `-txt`: its call site `0x006128AC` is in `DATATBLS_LoadCodeLists` ([data/0001 § 3](../findings/data/0001-excel-loader.md#3-what-is-registered-datatbls_loadall-0x00619300), [data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables)), which fills code links while compiling other `.txt`. A stock run does not load it, so the shipped `.bin` is not the source of the row order at run time `[I]`; the order the compiled tables store is the shipped one `[C]` (MonEquip and ItemTypes diffs, 0 mismatches).

## Columns

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `Body Location` | str, 11 distinct, len <= 10, 0 blank | not compiled | editor name of the slot; not in the record | — | [C] shape |
| `Code` | str, 10 distinct, len <= 4, 1 blank | +0x000 4-char code | 4-character code; the key other tables use | read by [ItemTypes](ItemTypes.md) `BodyLoc1`, `BodyLoc2`, [MonEquip](MonEquip.md) `loc1..loc3` | [C] |

## Interpretation notes

- `[C]` Layout: the record is the 4-character code, space padded ([excel-bin.md](../formats/excel-bin.md#cell-encoding-rules)); `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel bodylocs` matches 11 of 11 cells.
- `[C]` Foreign keys, checked by set inclusion over every row (this phase): `itemtypes:BodyLoc1` (8 distinct codes), `BodyLoc2` (8) and `monequip:loc1` (10), `loc2` (3), `loc3` (3) are all subsets of the 10 non-blank codes.
- The record count is checked by the full-tier surveys: `excel` (`.bin` count against `.txt` data rows) and `excel_layout` (every `.bin` cell against its `.txt` cell, layout in `tools/excel_layouts.py`) (`python3 -I tools/gate.py --full`).

## Open questions

- None for the data. What the equip code does with a location number is in [items/0014](../findings/items/0014-ground-items.md) and the inventory spec.

