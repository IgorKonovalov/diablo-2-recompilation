# UniqueSuffix (`data/global/excel/uniquesuffix.txt` → `uniquesuffix.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 69 (no `Expansion` marker)   **Record:** 2 B
> **sha256:** `.txt` `5c9597373fd8c3621c94afc95aa80487c59c81349c663635a2cae2f156e862f7`, `.bin` `79f3983a50b9efbbb14ccce270ae7f2eb5f280ffcd1665e984bb607f5a4f9d9b`
> **Doc status:** complete for layout; semantics `[L]`

## Purpose

One row per word that can follow the prefix in a random unique monster's name ("Touch", "Spell", "Feast", … "Lust"). The
`.txt` holds the string-table **key** of the word; the record holds the string index of that key. Together with
[UniquePrefix](UniquePrefix.md) and [UniqueAppellation](UniqueAppellation.md) it is the name source for random uniques
(ADR-0002 names the three as the name roll's tables; [tbl.md § Unique monster name tables](../formats/tbl.md#unique-monster-name-tables)).
The roll itself is `monsters/special` (plan 0018). Leads: no lead; derived from data.

## Row identity

- `[C]` The `.bin` is a u32 record count (69) and 69 records of one u16 each, one per `.txt` row in order
  ([excel-bin.md](../formats/excel-bin.md)). The loader reads it with record size 2
  ([data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables)).
- `[L]` Rows have no key column in the record; a reader can only address them by row index.

## Columns

`[C]` layout: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel uniquesuffix`: 69 records × 1 field
= 69 cells, **0 mismatches**.

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `Name` | str, 69 distinct, 0 blank, 26 end in `UM` | `+0x000` u16 string index of the key, 2755..2824 (2790 skipped) | the word's string key | string tables (`string.tbl`) | layout [C]; meaning [L] |

## Interpretation notes

- `[C]` The stored indices are 2755..2824 in row order with **one gap**: rows 0–34 hold 2755–2789 and rows 35–68 hold
  2791–2824. The skipped `string.tbl` entry 2790 is the key `raven` ("Raven"), which sits between `crow` (row 34, 2789) and
  `hawk` (row 35, 2791) in the string table but has no row here. (`excel_bin.py dump`, `tools/tbl.py lookup … raven`)
- `[C]` First `touchUM` → 2755 "Touch", last `lust` → 2824 "Lust". 26 of the 69 keys end in `UM`; no key repeats. The
  key lookup gives the stored index for every row, in every language with a `string.tbl` (`python3 -I tools/tbl.py survey workspace/merged`,
  [tbl.md § Unique monster name tables](../formats/tbl.md#unique-monster-name-tables)).
- `[L]` The values are capitalised words ("Touch", "Spell"); how the game joins prefix and suffix (a space, case) is
  code, not data.

## Open questions

- `[L]` Which rows a unique monster's name draws from, with which seed and in which order, and how the parts are joined
  into the displayed name: plan 0018 Phase 1 (reverser), `monsters/special`.
