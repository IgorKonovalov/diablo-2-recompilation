# UniqueAppellation (`data/global/excel/uniqueappellation.txt` → `uniqueappellation.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 25 (no `Expansion` marker)   **Record:** 2 B
> **sha256:** `.txt` `fbb5661f61f578219cd6b72b6709a319c0ee906fb9b1fb44f018ab17c3aa4c1a`, `.bin` `d5743375bf5d5539799663080716e36ee18ec74ff89b890ac61831d370d0decc`
> **Doc status:** complete for layout; semantics `[L]`

## Purpose

One row per word that can close a random unique monster's name ("the Hammer", "the Axe", … "the Cold"). The
`.txt` holds the string-table **key** of the word; the record holds the string index of that key. Together with
[UniqueSuffix](UniqueSuffix.md) and [UniquePrefix](UniquePrefix.md) it is the name source for random uniques
(ADR-0002 names the three as the name roll's tables; [tbl.md § Unique monster name tables](../formats/tbl.md#unique-monster-name-tables)).
The roll itself is `monsters/special` (plan 0018). Leads: no lead; derived from data.

## Row identity

- `[C]` The `.bin` is a u32 record count (25) and 25 records of one u16 each, one per `.txt` row in order
  ([excel-bin.md](../formats/excel-bin.md)). The loader reads it with record size 2
  ([data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables)).
- `[L]` Rows have no key column in the record; a reader can only address them by row index.

## Columns

`[C]` layout: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel uniqueappellation`: 25 records × 1 field
= 25 cells, **0 mismatches**.

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `Name` | str, 25 distinct, 0 blank | `+0x000` u16 string index of the key, 2825..2849 | the word's string key | string tables (`string.tbl`) | layout [C]; meaning [L] |

## Interpretation notes

- `[C]` The stored indices are 2825..2849, one per row, consecutive and in row order (first `the Hammer` → 2825, last
  `the Cold` → 2849). The keys are the English text itself (`the Hammer` → "the Hammer"); no key ends in `UM` and none
  repeats. The key lookup gives the stored index for every row, in every language with a `string.tbl`
  (`python3 -I tools/tbl.py survey workspace/merged`, [tbl.md § Unique monster name tables](../formats/tbl.md#unique-monster-name-tables)).
- `[C]` The three name tables are adjacent in `string.tbl`: prefixes 2702–2754, suffixes 2755–2824 (less 2790),
  appellations 2825–2849.

## Open questions

- `[L]` Which rows a unique monster's name draws from, with which seed and in which order, and how the parts are joined
  into the displayed name: plan 0018 Phase 1 (reverser), `monsters/special`.
