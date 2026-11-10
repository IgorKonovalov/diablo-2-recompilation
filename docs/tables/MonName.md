# MonName (`data/global/excel/MonName.txt`)

> **Source archive:** `.txt` d2exp
> **sha256:** `.txt` `1fe9c6856136b81e1d1534bd713d397d4c11342633eab69e625a8ca29aa27475`
> **Doc status:** shape complete (plan 0068 Phase 1); not loaded

## Purpose

A one-column list of 43 monster names: a header `MonName`, then `NULL` and 42 two- or three-word names (`Bone Stealer`, `Gray Death`, `Limb Ripper`, ...). It is shipped as `.txt` only and has no loader. The name pools the game does use for unique monsters are [UniquePrefix](UniquePrefix.md), [UniqueSuffix](UniqueSuffix.md) and [UniqueAppellation](UniqueAppellation.md) ([monsters/0003](../findings/monsters/0003-special-monsters.md)). Leads: none.

## Row identity

- `[C]` One column, 43 data rows, all distinct; rows have no key and nothing stores an index into them.
- `[I]` Not loaded: [data/0001 § 3](../findings/data/0001-excel-loader.md#3-what-is-registered-datatbls_loadall-0x00619300) lists it among the `.txt`-only tables with no loader. No `.bin` exists.

## Columns

| Column | Observed type / range | Meaning | Tag |
|---|---|---|---|
| `MonName` | str, 43 distinct, len <= 17 | a monster name; the first value is `NULL` | [C] shape, [L] meaning |

## Interpretation notes

- The record count is checked by the full-tier `excel` survey (`python3 -I tools/gate.py --full`): 43 `.txt` data rows.

## Open questions

- `[L]` What the list was for: the names look like an older pool of unique-monster names. Nothing in the data or in a finding settles it.

