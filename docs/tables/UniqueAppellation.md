# UniqueAppellation (`data/global/excel/uniqueappellation.txt` → `uniqueappellation.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 25 (no `Expansion` marker)   **Record:** 2 B
> **sha256:** `.txt` `fbb5661f61f578219cd6b72b6709a319c0ee906fb9b1fb44f018ab17c3aa4c1a`, `.bin` `d5743375bf5d5539799663080716e36ee18ec74ff89b890ac61831d370d0decc`
> **Doc status:** complete for layout; semantics `[I]` by the client name roll ([monsters/0003 § 8](../findings/monsters/0003-special-monsters.md#8-names-server-seed-client-roll))

## Purpose

One row per word that can close a random unique monster's name ("the Hammer", "the Axe", … "the Cold"). The
`.txt` holds the string-table **key** of the word; the record holds the string index of that key. Together with
[UniqueSuffix](UniqueSuffix.md) and [UniquePrefix](UniquePrefix.md) it is the name source for random uniques
(ADR-0002 names the three as the name roll's tables; [tbl.md § Unique monster name tables](../formats/tbl.md#unique-monster-name-tables)).
The roll is on the client ([monsters/0003 § 8](../findings/monsters/0003-special-monsters.md#8-names-server-seed-client-roll)). Leads: no lead; derived from data.

## Row identity

- `[C]` The `.bin` is a u32 record count (25) and 25 records of one u16 each, one per `.txt` row in order
  ([excel-bin.md](../formats/excel-bin.md)). The loader reads it with record size 2
  ([data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables)).
- `[C]` Rows have no key column in the record. `[I]` The roll addresses them by row index, `RangeB(seed, rows)`
  (fn:sub_00653F50_UniqueAppellationRoll@0x00653F50, [monsters/0003 § 8](../findings/monsters/0003-special-monsters.md#8-names-server-seed-client-roll)).

## Columns

`[C]` layout: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel uniqueappellation`: 25 records × 1 field
= 25 cells, **0 mismatches**.

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `Name` | str, 25 distinct, 0 blank | `+0x000` u16 string index of the key, 2825..2849 | the word's string key; the word drawn for the name | string tables (`string.tbl`) | layout [C]; meaning [I] |

## Interpretation notes

- `[C]` The stored indices are 2825..2849, one per row, consecutive and in row order (first `the Hammer` → 2825, last
  `the Cold` → 2849). The keys are the English text itself (`the Hammer` → "the Hammer"); no key ends in `UM` and none
  repeats. The key lookup gives the stored index for every row, in every language with a `string.tbl`
  (`python3 -I tools/tbl.py survey workspace/merged`, [tbl.md § Unique monster name tables](../formats/tbl.md#unique-monster-name-tables)).
- `[C]` The three name tables are adjacent in `string.tbl`: prefixes 2702–2754, suffixes 2755–2824 (less 2790),
  appellations 2825–2849.
- `[C]` **The roll.** Names are rolled on the client by `sub_004AC870_ClientMonNameBuild` for a random unique (not a
  superunique, champion, Blood Raven or the fixed-name bosses). The server sends a 16-bit name seed, but the client's reader
  `sub_0045F190_ClientMonAssign` keeps only its low byte (`0x0045F387`), so the roll runs on `Init(nameSeed & 0xFF)` and
  only 256 random-unique names exist. The draws are:
  suffix, then prefix, joined by `string.tbl` 1721 `"%0 %1"` (prefix first); then `Range(seed, 100) < 50` → appellation,
  suffix, prefix again, joined by 1722 `"%0 %1 %2"` (prefix, suffix, appellation), the first pair discarded. Each word from
  this table is `RangeB(seed, rows)` over its rows, through `sub_00653F50_UniqueAppellationRoll`; an entry with string index 0 or unresolved gives an empty
  string. (fn:sub_004AC870_ClientMonNameBuild@0x004AC870, fn:sub_00653F50_UniqueAppellationRoll@0x00653F50,
  fn:sub_0045F190_ClientMonAssign@0x0045F190, 0x0045F387, run:2026-10-14-mon-special: 94 client rolls reproduced,
  [monsters/0003 § 8](../findings/monsters/0003-special-monsters.md#8-names-server-seed-client-roll)). The roll is
  reimplemented in `tools/monspecial.py` (`name_roll`, `client_name_seed`) and specified in
  [specs/monsters/special § I](../specs/monsters/special.md#i-names).

## Open questions

- None for this table.
