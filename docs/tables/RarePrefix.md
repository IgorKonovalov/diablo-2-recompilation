# RarePrefix and RareSuffix (`data/global/excel/RarePrefix.txt`, `RareSuffix.txt` → `rareprefix.bin`, `raresuffix.bin`)

> **Source archive:** mixed: the `.txt` of both tables is the d2exp copy and the `.bin` the patch_d2 one (see § The two forms)   **Rows:** `RarePrefix` 46, `RareSuffix` 155 (no `Expansion` marker)   **Record:** 72 B (both)
> **sha256:** `rareprefix.txt` `529caeee9493a331bd693b8de4e5eaecac271b93f25117ae28da222fc787b5f4`, `rareprefix.bin` `3138a4e84b612611cfe6d929e5de8e800e417c3f26ee9e98ee203f4d41d49617`; `raresuffix.txt` `4652d644dff63c5f7086e747911d86a21175f4dcd4718813ac2607fcf6da5ffe`, `raresuffix.bin` `00f0a4867541e5ce458ad2f7eb829a1a5fef7809b8348230657da5e632dc7185`
> **Doc status:** columns listed, `.bin` layout complete except 16 zero bytes, values surveyed (plan 0021 Phase 0); semantics `[L]`

One shared doc: the two tables have the same columns and record. [RareSuffix.md](RareSuffix.md) only points here.

## Purpose

One row per rare-item name part: a rare item's name is a `RarePrefix` word and a `RareSuffix` word
(`Beast` + `bite`). A row only names the item types the word is allowed on (`itype1..7`, `etype1..4`). It
carries no property and no level. Read by `items/affixes` (the rare builder's two name rolls, plan 0021).
Leads: no lead; derived from data.

## Row identity

- `[C]` The record index is the data row index (neither `.txt` has an `Expansion` marker): `excel_bin.py diff`
  matches record *i* to data row *i* in every mapped column. (tbl:RarePrefix.txt:name, tbl:RareSuffix.txt:name)
- `[C]` `name` is lower-case in `RareSuffix` (155 distinct, len ≤ 8) and capitalised in `RarePrefix` (45
  distinct over 46 rows, len ≤ 10: `Storm` is both record 13, types `armo weap misc`, and record 19, types
  `armo weap`). No row is blank. (tbl:RarePrefix.txt:name)
- `[L]` Some prefix names read as string-table keys rather than display text (`GhoulRI`, `PlagueRI`,
  `Wraithra`, `Fiendra`).
- `[I]` A saved rare item stores two 8-bit name ids, `name1` and `name2` ([d2s format](../formats/d2s.md)). A
  stored rare ring has names (160, 121): `RareSuffix` record 121 is `circle`, but 160 is past the end of both
  tables (46 and 155 records). `[L]` How the two ids map to records (one merged list, suffixes first, would fit)
  is for the reverser (backlog).
- `[I]` The game loads both with a 72-byte record (call sites `0x0063414C` prefix, `0x00634132` suffix,
  [data/0001 §4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables)).

## Columns

`[C]` layout tags are by data behaviour: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel rareprefix`
decodes 46 records × 12 mapped fields = 552 cells, `raresuffix` 155 × 12 = 1 860 cells, 0 mismatches in both.
Observed values from `python3 -I tools/affix_survey.py columns workspace/merged/data/global/excel <table>`.
**Meaning** is `[L]` throughout (plan 0021 Phase 1 reads the code).

| Column | Prefix: observed | Suffix: observed | `.bin` field | Meaning (`[L]`) | References | Tag |
|---|---|---|---|---|---|---|
| `name` | str, 45 distinct, len ≤ 10 | str, 155 distinct, len ≤ 8 | `+0x026` char[34] | name word, a string-table key | string table | [C] |
| `version` | 0 in every row | 0 in every row | — (not located) | — | — | [C] |
| `itype1` | `armo` ×37, `ring` ×4, `rod` ×2, `tors` ×1; 2 blank | 22 distinct types, 0 blank | `+0x010` u16 index, blank 0 | item types the word is allowed on | [ItemTypes](ItemTypes.md) `Code` | [C] |
| `itype2`..`itype7` | 4 / 3 / 1 / 1 / 0 / 0 distinct types | 18 / 13 / 9 / 5 / 2 / 0 | `+0x012` + 2·(n−2), u16 index, blank 0 | as `itype1` | [ItemTypes](ItemTypes.md) `Code` | [C] |
| `etype1`..`etype4` | blank in every row | blank in every row | `+0x01E` + 2·(n−1), u16 index, blank 0 | item types the word is excluded from | [ItemTypes](ItemTypes.md) `Code` | [C] |
| `add`, `multiply`, `divide` | 0 in every row | 1 on 10 rows (110..119), else 0 | — (not located) | — | — | [C] |

- `[C]` Every non-blank type cell resolves to an `itemtypes` code; no row of either table names an `etype`.
  (tbl:RareSuffix.txt:itype1, tbl:ItemTypes.txt:Code)
- `[C]` `RarePrefix` rows name broad types (`armo`, `weap`, `misc`; 20 rows add `misc`), except record 36
  `Holocaust` (`tors helm shld swor axe`) and a few on `ring`, `amul`, `rod`, `scep`, `helm`. `RareSuffix` rows
  name narrow types (`swor knif spea pole axe h2h` for `bite`); records 110..119 (`clasp` .. `cord`) are the
  `belt` words. (tbl:RarePrefix.txt:itype1)
- `[C]` `RarePrefix` records 43 `Warp` and 44 `Rift` name no type at all. Whatever the type test is, they
  can only be reached by some other path. (tbl:RarePrefix.txt:itype1)

## Record layout

`+0x000..+0x00F` 16 bytes, 0 in every record of both tables · `+0x010..+0x01D` `itype1..7` u16 ·
`+0x01E..+0x025` `etype1..4` u16 · `+0x026..+0x047` `name` char[34]. `[C]` (`excel_bin.py diff`,
tbl:RarePrefix.txt:itype1). `python3 -I tools/excel_bin.py unknown workspace/merged/data/global/excel rareprefix`
lists only `+0x000..+0x00F` (zero) as uncovered.

- `[C]` `version`, `add`, `multiply` and `divide` have no field: the only uncovered bytes are 0 in every record,
  while `RareSuffix` has `add` = `multiply` = `divide` = 1 on its 10 belt rows. `version` is 0 in every row, so
  it could sit in the zero bytes; the data cannot tell. (tbl:RareSuffix.txt:add, tbl:RareSuffix.txt:version)
- `[L]` The 16 zero bytes may be slots the loader fills (as `UniqueItems` gets its row index and string key at
  load, [UniqueItems § Record layout](UniqueItems.md#record-layout)); `name` may likewise be char[32] plus a
  2-byte slot. For the reverser (backlog).

## The two forms (mixed-archive table)

The `.txt` of both tables is the expansion archive's (d2exp) and was not re-shipped; the patch (patch_d2) ships
only a re-compiled `.bin`. The game reads the `.bin` ([README § Source and shape](README.md#source-and-shape),
[excel-bin § Mixed-archive tables](../formats/excel-bin.md#mixed-archive-tables-automagic-rareprefix-raresuffix)).

- `[C]` **No compiled cell differs.** Decoded with the 72-byte layout, the `.bin` equals the `.txt` in every
  mapped column (552 + 1 860 cells, 0 mismatches, re-run for this doc). (tbl:RarePrefix.txt:name)
- `[C]` **What differs is the record format and the uncompiled columns.** The patch `.bin` has a 72-byte record
  with u16 type indices; the d2exp `.bin` of the same tables (not loaded in a stock run) has a 60-byte record
  with u8 type indices ([excel-bin § Mixed-archive tables](../formats/excel-bin.md#mixed-archive-tables-automagic-rareprefix-raresuffix)).
  The `.txt` columns `version`, `add`, `multiply`, `divide` have no field in either form.
- So for these two tables the `.txt` may be cited for content; a reader of the `.bin` uses the layout above.

## Open questions

- `[L]` How the saved `name1`/`name2` ids map to records of the two tables (the stored 160 exceeds both)
  (backlog → reverser).
- `[L]` What the 16 zero bytes at `+0x000` hold at run time, and whether `version` is read at all (backlog → reverser).
- `[L]` Every meaning above, including how `itype` is tested (through the `Equiv` chains or not) and whether the
  name rolls are weighted (no weight column exists) (plan 0021 Phase 1).
