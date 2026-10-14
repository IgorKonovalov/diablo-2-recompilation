# UniqueTitle (`data/global/excel/uniquetitle.txt` → `uniquetitle.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 16 (no `Expansion` marker)   **Record:** 2 B
> **sha256:** `.txt` `3ecf4e1b3fdbd905e3057407fac1b82ff6faf30425cfc2ed64e0cd79a6acde8e`, `.bin` `f17a320cb61c25c374ccd1a1e718c9054855f070f90f330900954d955bcab275`
> **Doc status:** complete for layout; semantics `[L]`

## Purpose

Sixteen titles ("Judge", "Magistrate", "Count", … "Lady") in a `Namco` column, with `Name` = `unused` on every row.
Only `Name` is compiled, so the `.bin` holds sixteen copies of the string index of `unused`. The archive spells the files
`UniqueTitle.txt`/`UniqueTitle.bin` (the merged tree lowercases them). The game loads the table
([data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables), `0x0065A44D`);
whether anything reads it is open. ADR-0002 and [tbl.md](../formats/tbl.md) name only the other three tables as the
name source. Leads: no lead; derived from data.

## Row identity

- `[C]` The `.bin` is a u32 record count (16) and 16 records of one u16 each, one per `.txt` row in order
  ([excel-bin.md](../formats/excel-bin.md)). The loader reads it with record size 2
  ([data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables)).
- `[L]` Rows have no key column in the record; a reader can only address them by row index.

## Columns

`[C]` layout: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel uniquetitle`: 16 records × 1 field
= 16 cells, **0 mismatches**.

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `Name` | str, 1 distinct (`unused`), 0 blank | `+0x000` u16 string index of the key, 5385 in every record | string key | string tables (`string.tbl`) | layout [C]; meaning [L] |
| `Namco` | str, 16 distinct (Judge, Magistrate, Count, Earl, Baron, Duke, Lord, Overlord, Warlord, Chief, Prince, King, Mistress, Countess, Duchess, Lady) | — (not compiled) | title text | — | [C] (no field) |

## Interpretation notes

- `[C]` Every record is 5385, the `string.tbl` index of the key `unused`, whose English value is "an evil force". The
  `Namco` titles are not string keys: `tools/tbl.py lookup … Judge` finds no entry (5382, the not-found index).
- `[L]` With every record equal, a name drawn from this table could only ever read "an evil force"; the table looks
  unused by its own `Name` cells. Whether a reader exists is plan 0018 Phase 1.

## Open questions

- `[L]` Which rows a unique monster's name draws from, with which seed and in which order, and how the parts are joined
  into the displayed name: plan 0018 Phase 1 (reverser), `monsters/special`. For this table: whether any code reads it.
