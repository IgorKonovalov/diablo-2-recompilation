# RarePrefix and RareSuffix (`data/global/excel/RarePrefix.txt`, `RareSuffix.txt` → `rareprefix.bin`, `raresuffix.bin`)

> **Source archive:** mixed: the `.txt` of both tables is the d2exp copy and the `.bin` the patch_d2 one (see § The two forms)   **Rows:** `RarePrefix` 46, `RareSuffix` 155 (no `Expansion` marker)   **Record:** 72 B (both)
> **sha256:** `rareprefix.txt` `529caeee9493a331bd693b8de4e5eaecac271b93f25117ae28da222fc787b5f4`, `rareprefix.bin` `3138a4e84b612611cfe6d929e5de8e800e417c3f26ee9e98ee203f4d41d49617`; `raresuffix.txt` `4652d644dff63c5f7086e747911d86a21175f4dcd4718813ac2607fcf6da5ffe`, `raresuffix.bin` `00f0a4867541e5ce458ad2f7eb829a1a5fef7809b8348230657da5e632dc7185`
> **Doc status:** columns listed, `.bin` layout complete except 16 zero bytes, values surveyed (plan 0021 Phase 0); the name pick's use of the columns `[I]` from
> [items/0005](../findings/items/0005-affixes.md) (plan 0021 Phase 1, § Code semantics below)

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
  tables (46 and 155 records).
- `[I]` **Merged ids.** The loader appends `raresuffix` then `rareprefix` into one array of 72-byte records, and a name
  id is the **merged index + 1**: suffix record r is id r + 1, prefix record r is id 156 + r. So the stored 160 is
  `RarePrefix` record 4, and `name1` comes from `RarePrefix`, `name2` from `RareSuffix`. Item data holds the ids at
  `+0x32`/`+0x34`. (fn:sub_00633F40_LoadRareAffixes@0x00633F40, fn:RAREAFFIX_GetRecord@0x00634260,
  [items/0005 § 1](../findings/items/0005-affixes.md#1-the-merged-affix-arrays-and-the-ids-0x00633730-0x00633f40))
- `[I]` The game loads both with a 72-byte record (call sites `0x0063414C` prefix, `0x00634132` suffix,
  [data/0001 §4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables)).

## Columns

`[C]` layout tags are by data behaviour: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel rareprefix`
decodes 46 records × 13 mapped fields = 598 cells, `raresuffix` 155 × 13 = 2 015 cells, 0 mismatches in both.
Observed values from `python3 -I tools/affix_survey.py columns workspace/merged/data/global/excel <table>`.
**Meaning** is the column name's plain reading, `[L]`; the name pick's use of the columns is `[I]` in
[§ Code semantics](#code-semantics-items0005) below.

| Column | Prefix: observed | Suffix: observed | `.bin` field | Meaning (`[L]`) | References | Tag |
|---|---|---|---|---|---|---|
| `name` | str, 45 distinct, len ≤ 10 | str, 155 distinct, len ≤ 8 | `+0x026` char[34] | name word, a string-table key | string table | [C] |
| `version` | 0 in every row | 0 in every row | `+0x00E` u16 (0 everywhere) | `[I]` ≥ 100 needs an expansion item | — | [C] value; slot `[I]` by the reader (below) |
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

`+0x000..+0x00F` 16 bytes, 0 in every record of both tables (`+0x00C` the load-time string key, `+0x00E`
`version`, see below) · `+0x010..+0x01D` `itype1..7` u16 · `+0x01E..+0x025` `etype1..4` u16 · `+0x026..+0x047`
`name` char[34]. `[C]` (`excel_bin.py diff`, tbl:RarePrefix.txt:itype1).
`python3 -I tools/excel_bin.py unknown workspace/merged/data/global/excel rareprefix` lists only `+0x000..+0x00D`
(zero) as uncovered.

- `[C]` `add`, `multiply` and `divide` have no field: the only uncovered bytes are 0 in every record, while
  `RareSuffix` has `add` = `multiply` = `divide` = 1 on its 10 belt rows. (tbl:RareSuffix.txt:add)
- `[I]` **The first 16 bytes**: `+0x00E` u16 is tested as `version` by the name pick's type test, so the layout puts
  `version` there (0 in every row, so the data alone cannot place it); `+0x00C` u16 is the string key of `name`,
  written by the loader (0 in the file); `+0x000..+0x00B` are read by no pick.
  (fn:ITEMS_RareNameTypeOk@0x0065E710, fn:sub_00633F40_LoadRareAffixes@0x00633F40,
  [items/0005 § Answers](../findings/items/0005-affixes.md#answers-to-the-phase-0-questions))

## The two forms (mixed-archive table)

The `.txt` of both tables is the expansion archive's (d2exp) and was not re-shipped; the patch (patch_d2) ships
only a re-compiled `.bin`. The game reads the `.bin` ([README § Source and shape](README.md#source-and-shape),
[excel-bin § Mixed-archive tables](../formats/excel-bin.md#mixed-archive-tables-automagic-rareprefix-raresuffix)).

- `[C]` **No compiled cell differs.** Decoded with the 72-byte layout, the `.bin` equals the `.txt` in every
  mapped column (598 + 2 015 cells, 0 mismatches, re-run for this doc). (tbl:RarePrefix.txt:name)
- `[C]` **What differs is the record format and the uncompiled columns.** The patch `.bin` has a 72-byte record
  with u16 type indices; the d2exp `.bin` of the same tables (not loaded in a stock run) has a 60-byte record
  with u8 type indices ([excel-bin § Mixed-archive tables](../formats/excel-bin.md#mixed-archive-tables-automagic-rareprefix-raresuffix)).
  The `.txt` columns `add`, `multiply`, `divide` have no field in either form.
- So for these two tables the `.txt` may be cited for content; a reader of the `.bin` uses the layout above.

## Code semantics (items/0005)

The Phase 0 questions of this doc are answered in
[items/0005 § Answers to the Phase 0 questions](../findings/items/0005-affixes.md#answers-to-the-phase-0-questions). Every statement here is `[I]`: read from the
code, not yet reproduced (plan 0021 Phase 2).

- `[I]` **The name pick is unweighted and has no level.** `ITEMS_PickRareName` collects every row of the block
  (`RarePrefix` for `name1`, then `RareSuffix` for `name2`) that passes the type test, then draws one
  `RNG_RangeOffset(seed, 0, n)`, uniform over them; no candidate → 0, no draw, and the rare builder fails.
  (fn:ITEMS_PickRareName@0x005C1AB0, [items/0005 § 6](../findings/items/0005-affixes.md#6-rare-items_buildrare-0x005c21a0--items_buildrareaffixesrec-0x005c1bf0-item-in-esi))
- `[I]` **The type test** (`ITEMS_RareNameTypeOk`): a classic item whose base is stackable or throwable is refused;
  `version` ≥ 100 needs an expansion item; any `etype1..4` the item is refuses; one of `itype1..7` must match. Each list
  ends at its first value < 1, and an empty `itype` list refuses, so `Warp` and `Rift` are never picked.
  (fn:ITEMS_RareNameTypeOk@0x0065E710, [items/0005 § 6](../findings/items/0005-affixes.md#6-rare-items_buildrare-0x005c21a0--items_buildrareaffixesrec-0x005c1bf0-item-in-esi))
- `[I]` The two names are drawn before the affix count and the affix picks. ([items/0005 § 6](../findings/items/0005-affixes.md#6-rare-items_buildrare-0x005c21a0--items_buildrareaffixesrec-0x005c1bf0-item-in-esi))

## Open questions

- `[L]` Every `[I]` above until plan 0021 Phase 2 reproduces the rare builder.
- `[L]` Whether the type test walks the `Equiv` chains as the magic one does (items/0005 § 6 does not say).
