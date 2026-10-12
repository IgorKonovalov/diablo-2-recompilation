# TreasureClassEx (`data/global/excel/treasureclassex.txt`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 853 (no `Expansion` marker)   **Record:** 736 B
> **sha256:** `.txt` `214c3b83e1f45f44380598b2157de0689bd6ad0318edae4af4cc8d2ee5c2b525`, `.bin` `d6d1b457247a613fe67a28fec52d9406b9256c01264a78446dfb9d8178c710b5`
> **Doc status:** columns listed, `.bin` layout complete, semantics pending

## Purpose

One row is one treasure class: a name, a pick count, quality ratios and up to ten weighted entries.
Read by item drops ([research map](../specs/README.md) `items/tc`). `[C]` This is the live TC table;
`TreasureClass.txt` (707 rows, `.txt` only) is never loaded ([data/0001](../findings/data/0001-excel-loader.md#answer-summary)). Its
rows are appended after 161 load-time TCs (see Row identity).

## Row identity

- `[C]` Key column `Treasure Class`; 852 non-empty names, all distinct. Record 852, the last, has an
  empty name: its `.txt` row holds only `Term = 0`.
- `[C]` No `Expansion` marker, so record *n* is data row *n*.
- `[C]` Other tables reference a TC **by name in the `.txt`**. In `monstats.bin` the TC columns store
  **row + 161** (u16); see [MonStats.md](MonStats.md). `[C]` The 161 indices below are TC 0 (empty
  name) and TCs 1–160, the auto-built item-type TCs; TCEx rows follow in file order
  ([data/0001 §7–8](../findings/data/0001-excel-loader.md#7-treasure-classes-at-load-time)). Inside this table, `Item1..10` keep the name
  as text (below).

## Columns

`[C]` layout tags are by data behaviour: `python3 -I tools/excel_bin.py diff <excel-dir> treasureclassex` decodes every record and compares it with every mapped cell (blank cells and encoding rules as in [excel-bin.md](../formats/excel-bin.md#cell-encoding-rules)). A field is tagged `[C]` when the column's values pin its offset (a probe over every record finds no other offset that fits), `[I]` when the column is constant or identical to a sibling column, so its position comes from the neighbouring fields or the stride of its group. Widths are `[C]` with the same proviso; signedness is `[I]` (`s` where the column holds negative values). **Meaning:** no column semantics are claimed here; they come from reverser findings.

| Column | Observed type / range | `.bin` field | References | Layout tag |
|---|---|---|---|---|
| `Treasure Class` | str, 852 distinct, len ≤ 19, 1 blank | `+0x000` char[32] | — | [C] |
| `group` | int 1..18 (18 distinct), 151 blank | `+0x024` u16 | — | [C] |
| `level` | int 0..96 (63 distinct), 151 blank | `+0x026` u16 | — | [C] |
| `Picks` | int -4..7 (9 distinct), 1 blank | `+0x020` s32 | — | [C] |
| `Unique` | int 512..1024 (10 distinct), 613 blank | `+0x02E` u16 | — | [C] |
| `Set` | int 654..995 (7 distinct), 622 blank | `+0x02C` u16 | — | [C] |
| `Rare` | int 800..1024 (6 distinct), 622 blank | `+0x02A` u16 | — | [C] |
| `Magic` | int, always 1024, 622 blank | `+0x028` u16 | — | [C] |
| `NoDrop` | int 0..125 (7 distinct), 225 blank | `+0x034` u32 | — | [C] |
| `Item1` | str, 264 distinct, len ≤ 17, 1 blank | `+0x038` char[64] | — | [C] |
| `Prob1` | int 1..60 (23 distinct), 1 blank | `+0x2B8` u32 | — | [C] |
| `Item2` | str, 256 distinct, len ≤ 18, 23 blank | `+0x078` char[64] | — | [C] |
| `Prob2` | int 1..5170 (19 distinct), 23 blank | `+0x2BC` u32 | — | [C] |
| `Item3` | str, 165 distinct, len ≤ 17, 328 blank | `+0x0B8` char[64] | — | [C] |
| `Prob3` | int 1..3957 (30 distinct), 328 blank | `+0x2C0` u32 | — | [C] |
| `Item4` | str, 94 distinct, len ≤ 17, 414 blank | `+0x0F8` char[64] | — | [C] |
| `Prob4` | int 2..42 (14 distinct), 414 blank | `+0x2C4` u32 | — | [C] |
| `Item5` | str, 154 distinct, len ≤ 17, 604 blank | `+0x138` char[64] | — | [C] |
| `Prob5` | int 1..28 (10 distinct), 604 blank | `+0x2C8` u32 | — | [C] |
| `Item6` | str, 73 distinct, len ≤ 8, 674 blank | `+0x178` char[64] | — | [C] |
| `Prob6` | int 1..14 (8 distinct), 647 blank | `+0x2CC` u32 | — | [C] |
| `Item7` | str, 66 distinct, len ≤ 6, 737 blank | `+0x1B8` char[64] | — | [C] |
| `Prob7` | int 1..7 (6 distinct), 737 blank | `+0x2D0` u32 | — | [C] |
| `Item8` | str, 50 distinct, len ≤ 6, 743 blank | `+0x1F8` char[64] | — | [C] |
| `Prob8` | int 1..5 (4 distinct), 743 blank | `+0x2D4` u32 | — | [C] |
| `Item9` | str, 94 distinct, len ≤ 17, 749 blank | `+0x238` char[64] | — | [C] |
| `Prob9` | int 1..2270 (55 distinct), 749 blank | `+0x2D8` u32 | — | [C] |
| `Item10` | always blank | `+0x278` char[64] | — | [I] |
| `Prob10` | always blank | `+0x2DC` u32 | — | [I] |
| `SumItems` | int 26..42 (7 distinct), 752 blank | — (editor helper (count of ItemN); not in the record) | — | — |
| `TotalProb` | int 66..2306 (60 distinct), 752 blank | — (editor helper (sum of ProbN); not in the record) | — | — |
| `DropChance` | str, 56 distinct, len ≤ 6, 752 blank | — (editor helper (computed percentage); not in the record) | — | — |
| `Term` | int, always 0, 2 blank | — (terminator column, 0 or blank in every row; no field found (+0x30 is 0 in every record)) | — | — |

### Fields with no `.txt` column

| offset | type | observed | tag |
|---|---|---|---|
| `+0x030` | u16 × 2 | 0 in every record | two ratio words copied into the runtime TC as words 5–6 (`+0x1A + 2·4`, `+0x1A + 2·5`) `[C]`; upgrade chances, each tested as `(rand & 0x3FF) < w` and setting upgrade flag `0x04` or `0x10` on the picked item `[I]`; never non-zero in stock data ([items/0001 §1](../findings/items/0001-tc-resolution.md#1-runtime-tc-layout-built-at-load-read-by-the-resolver), [§8](../findings/items/0001-tc-resolution.md#8-item-pick-and-hand-off-0x0055ac5f0x0055af59)) |

## Record layout (736 bytes)

`+0x000` name `char[32]` · `+0x020` `Picks` s32 · `+0x024` `group` u16 · `+0x026` `level` u16 ·
`+0x028` `Magic` · `+0x02A` `Rare` · `+0x02C` `Set` · `+0x02E` `Unique` (u16 each) · `+0x030`, `+0x032` upgrade-ratio words (u16 each) ·
`+0x034` `NoDrop` u32 · `+0x038 + 64·i` `Item(i+1)` `char[64]`, i = 0..9 · `+0x2B8 + 4·i` `Prob(i+1)` u32.

## Interpretation notes

- `[C]` **`ItemN` is stored as text, not as an index.** Each entry is the cell copied into a
  `char[64]` (max cell length 18). An entry may be an item code (`gld`, `rin`), an item-type-and-level
  name, or another TC; the `.bin` does not say which. `[C]` It is resolved at load time by
  `TC_ParseItemCell` `0x00654440`; resolution order in
  [data/0001 §7](../findings/data/0001-excel-loader.md#7-treasure-classes-at-load-time).
- `[C]` `Picks` has negative values (−4..7) and is 4 bytes wide; `group`/`level` and the four quality
  ratios are 2 bytes; `NoDrop` and `ProbN` are 4 bytes.
- `[C]` In 27 rows `Prob6` is set while `Item6` is blank (674 blank items vs 647 blank probs); both are
  compiled as written.
- `[C]` `SumItems`, `TotalProb`, `DropChance` are spreadsheet helpers and not in the record; `Term` is not
  located (0 or blank everywhere).

## Open questions

- Answered in [data/0001 §7–8](../findings/data/0001-excel-loader.md#7-treasure-classes-at-load-time): this table feeds drops, `ItemN`
  is resolved by `TC_ParseItemCell`, and the 161 lower indices are the empty TC plus 160 auto
  item-type TCs (all `[C]`).
- Answered in [items/0001 §1](../findings/items/0001-tc-resolution.md#1-runtime-tc-layout-built-at-load-read-by-the-resolver): `+0x030` is two
  u16 ratio words that the loader copies into the runtime TC (`[C]`, writer and reader agree); the
  resolver uses them as upgrade chances (`[I]`, §8). Both are 0 in every stock record, so that path
  never runs with stock data.
