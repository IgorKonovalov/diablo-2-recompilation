# UniqueTitle (`data/global/excel/uniquetitle.txt` → `uniquetitle.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 16 (no `Expansion` marker)   **Record:** 2 B
> **sha256:** `.txt` `3ecf4e1b3fdbd905e3057407fac1b82ff6faf30425cfc2ed64e0cd79a6acde8e`, `.bin` `f17a320cb61c25c374ccd1a1e718c9054855f070f90f330900954d955bcab275`
> **Doc status:** complete for layout; never read by the game `[I]` ([monsters/0003 § 8](../findings/monsters/0003-special-monsters.md#8-names-server-seed-client-roll))

## Purpose

Sixteen titles ("Judge", "Magistrate", "Count", … "Lady") in a `Namco` column, with `Name` = `unused` on every row.
Only `Name` is compiled, so the `.bin` holds sixteen copies of the string index of `unused`. The archive spells the files
`UniqueTitle.txt`/`UniqueTitle.bin` (the merged tree lowercases them). The game loads the table
([data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables), `0x0065A44D`)
and frees it, and nothing reads it `[I]` ([monsters/0003 § 8](../findings/monsters/0003-special-monsters.md#8-names-server-seed-client-roll)). ADR-0002 and [tbl.md](../formats/tbl.md) name only the other three tables as the
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
| `Name` | str, 1 distinct (`unused`), 0 blank | `+0x000` u16 string index of the key, 5385 in every record | string key; `[I]` never read | string tables (`string.tbl`) | layout [C]; meaning [L] |
| `Namco` | str, 16 distinct (Judge, Magistrate, Count, Earl, Baron, Duke, Lord, Overlord, Warlord, Chief, Prince, King, Mistress, Countess, Duchess, Lady) | — (not compiled) | title text | — | [C] (no field) |

## Interpretation notes

- `[C]` Every record is 5385, the `string.tbl` index of the key `unused`, whose English value is "an evil force". The
  `Namco` titles are not string keys: `tools/tbl.py lookup … Judge` finds no entry (5382, the not-found index).
- `[I]` **No reader.** The table pointer (`0x0096D488`) is written by the loader `0x0065A463` and by
  `sub_00653DB0_UNameTableLoad`, and cleared by `sub_00653E20_UNameTablesFree`; nothing else references it or its count
  `0x0096D498`, and the three name-roll functions read only the prefix, suffix and appellation tables
  (data:g_pUniqueNameTables@0x0096D488, fn:sub_0065A400_MonsterTablesLoad@0x0065A400, [monsters/0003 § 8](../findings/monsters/0003-special-monsters.md#8-names-server-seed-client-roll)). The
  sixteen `unused` records never reach a name.

## Open questions

- None: the table is loaded and freed, never read.
