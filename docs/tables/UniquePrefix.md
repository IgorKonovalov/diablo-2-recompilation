# UniquePrefix (`data/global/excel/uniqueprefix.txt` → `uniqueprefix.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 53 (no `Expansion` marker)   **Record:** 2 B
> **sha256:** `.txt` `564ce70637b464c3cfe735c898310208b062751f80c5952afb78bbfb48f45369`, `.bin` `feef153fe5292ad607cba993dc223d0f82a6e4b0f7591a11f98141e4f70d15a3`
> **Doc status:** complete for layout; semantics `[I]` by the client name roll ([monsters/0003 § 8](../findings/monsters/0003-special-monsters.md#8-names-server-seed-client-roll))

## Purpose

One row per word that can start a random unique monster's name ("Gloom", "Gray", "Dire", … "Devil"). The
`.txt` holds the string-table **key** of the word; the record holds the string index of that key. Together with
[UniqueSuffix](UniqueSuffix.md) and [UniqueAppellation](UniqueAppellation.md) it is the name source for random uniques
(ADR-0002 names the three as the name roll's tables; [tbl.md § Unique monster name tables](../formats/tbl.md#unique-monster-name-tables)).
The roll is on the client ([monsters/0003 § 8](../findings/monsters/0003-special-monsters.md#8-names-server-seed-client-roll)). Leads: no lead; derived from data.

## Row identity

- `[C]` The `.bin` is a u32 record count (53) and 53 records of one u16 each, one per `.txt` row in order
  ([excel-bin.md](../formats/excel-bin.md)). The loader reads it with record size 2
  ([data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables)).
- `[C]` Rows have no key column in the record. `[I]` The roll addresses them by row index, `RangeB(seed, rows)`
  (fn:sub_00653ED0_UniquePrefixRoll@0x00653ED0, [monsters/0003 § 8](../findings/monsters/0003-special-monsters.md#8-names-server-seed-client-roll)).

## Columns

`[C]` layout: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel uniqueprefix`: 53 records × 1 field
= 53 cells, **0 mismatches**.

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `Name` | str, 53 distinct, 0 blank, 21 end in `UM` | `+0x000` u16 string index of the key, 2702..2754 | the word's string key; the word drawn for the name | string tables (`string.tbl`) | layout [C]; meaning [I] |

## Interpretation notes

- `[C]` The stored indices are 2702..2754, one per row, consecutive and in row order: the keys are the 53 consecutive
  `string.tbl` entries 2702–2754 (first `GloomUM` → 2702 "Gloom", then `Gray` → 2703 "Gray", last `Devil` → 2754
  "Devil"). For every row the English key lookup gives the stored index and the source text's value, and the keys
  resolve in every language that ships a `string.tbl` (`[C]`, `python3 -I tools/tbl.py survey workspace/merged`, [tbl.md § Unique monster name
  tables](../formats/tbl.md#unique-monster-name-tables)).
- `[C]` 21 of the 53 keys end in `UM` (`GloomUM`, `DireUM`, `ViperUM`, …); the value drops the suffix (`GloomUM` →
  "Gloom"). No key repeats.
- `[I]` The value is a stored index, so it is read against the language's `string.tbl` at run time; for the
  5322-entry `deu`/`fra` tables the stored index names other strings ([tbl.md](../formats/tbl.md#unique-monster-name-tables)).
- `[I]` **The roll.** Names are rolled on the client by `sub_004AC870_ClientMonNameBuild` for a random unique (not a
  superunique, champion, Blood Raven or the fixed-name bosses), on a seed set from the 16-bit name seed the server sends:
  suffix, then prefix, joined by `string.tbl` 1721 `"%0 %1"` (prefix first); then `Range(seed, 100) < 50` → appellation,
  suffix, prefix again, joined by 1722 `"%0 %1 %2"` (prefix, suffix, appellation), the first pair discarded. Each word from
  this table is `RangeB(seed, rows)` over its rows, through `sub_00653ED0_UniquePrefixRoll`; an entry with string index 0 or unresolved gives an empty
  string. (fn:sub_004AC870_ClientMonNameBuild@0x004AC870, fn:sub_00653ED0_UniquePrefixRoll@0x00653ED0,
  [monsters/0003 § 8](../findings/monsters/0003-special-monsters.md#8-names-server-seed-client-roll))

## Open questions

- None for this table; the reimplementation of the roll is plan 0018 Phase 2.
