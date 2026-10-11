# SetItems (`data/global/excel/setitems.txt` → `setitems.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 127 (128 data rows − 1 `Expansion` marker)   **Record:** 440 B
> **sha256:** `.txt` `5696730cf84564f1cb815fb362fba13f23e22f5176e854730733519048f711be`, `.bin` `b793de221bf5ebe94e4f8fdbab6b0c4a6ce0f5b1ba8f4ff78f12dc3d851272ce`
> **Doc status:** art and identity columns only; `.bin` layout of the record head (`+0x000..+0x087`) mapped, the property block not mapped; semantics `[L]`

## Purpose

One row per set item: its name, the set it belongs to, the base item it is made from, and how it
looks. **This doc covers the art and identity columns only** (plan 0009 Phase 2, the item art index).
The stat columns (`prop1..9`, `aprop1a..5b` and their parameters) belong to the items/sets work and
are not described here. Read by the item art index ([README § Item art index](README.md#item-art-index)).
Leads: no lead; derived from data.

## Row identity

- `[C]` The record index is the data row index once the `Expansion` marker is dropped (0..126); the
  diff below matches record *i* to data row *i* in every mapped column.
- `[C]` `index` is the row's name, unique in all 127 rows.
- `[I]` A treasure-class cell can name a set item by `index`: `TC_ParseItemCell` falls back to the
  `setitems` name link (`0x0096C844`) after the unique one
  ([data/0001 §7](../findings/data/0001-excel-loader.md#7-treasure-classes-at-load-time)).
- `[C]` `set` names a row of `sets.txt` by its `index` (all 127 resolve, 32 distinct sets) and is stored
  as that row's index. `item` is the base item code (all 127 resolve to a `weapons`/`armor`/`misc`
  code). `*item` is a comment column (the base item's name) and is not compiled.
- `[I]` The game loads `setitems.bin` with a 440-byte record (call site `0x00636651`,
  [data/0001 §4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables)).

## Columns

`[C]` layout tags are by data behaviour: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel setitems`
decodes all 127 records and matches every mapped cell (127 × 16 = 2 032 cells, 0 mismatches), and each
`[C]` offset is the only one `excel_bin.py probe` finds. The layout is **partial** on purpose: the 76
property columns are reported by `diff` as outside the layout and are not checked. A column that is
blank in every row, or equal to a sibling in every row, cannot be placed by the data; its position
follows the `uniqueitems` head and the `.txt` order and is `[L]`. `[L]` The integer type the game reads
inside a slot is not pinned (no code anchor; the data is non-negative).
**Meaning:** `[L]` throughout; only the art and identity columns get a meaning.

| Column | Observed type / range | `.bin` field | Meaning (`[L]`) | References | Layout tag |
|---|---|---|---|---|---|
| `index` | str, 127 distinct, len ≤ 29 | `+0x002` char[34] | set item name (identity) | TC cells | [C] |
| `set` | str, 32 distinct, len ≤ 22 | `+0x02C` 4-byte slot, row index (u32 decode) | owning set | `sets` `index` (all resolve) | [C] |
| `item` | str, 112 distinct, len ≤ 3 | `+0x028` char[4] code | base item | `weapons`/`armor`/`misc` `code` (all resolve) | [C] |
| `*item` | comment column | — (not compiled) | — | — | — |
| `lvl` | int 3..55 (29 distinct) | `+0x030` u16 | — | — | [C] |
| `lvl req` | int 2..81 (48 distinct) | `+0x032` u16 | — | — | [C] |
| `rarity` | int 1..7 (3 distinct) | `+0x034` 4-byte slot (u32 decode) | — | — | [C] |
| `cost mult` | int, always 5 | `+0x038` 4-byte slot (u32 decode) | — | — | [C] |
| `cost add` | int 2500..5000 (2 distinct) | `+0x03C` 4-byte slot (u32 decode) | — | — | [C] |
| `chrtransform` | str, 16 distinct, len ≤ 4, 14 blank | `+0x040` u8 index, blank = `0xFF` | colour shift on the character / ground | [colors](colors.md) `Code` (all resolve) | [L] |
| `invtransform` | str, 16 distinct, len ≤ 4, 14 blank | `+0x041` u8 index, blank = `0xFF` | colour shift on the inventory icon | [colors](colors.md) `Code` (all resolve) | [L] |
| `flippyfile` | always blank | `+0x042` char[32] (0 in every record) | own ground-drop DC6 | — | [L] |
| `invfile` | always blank | `+0x062` char[32] (0 in every record) | own inventory DC6 | — | [L] |
| `dropsound` | always blank | `+0x082` u16 (0 in every record) | — | `sounds` `Sound` | [L] |
| `usesound` | always blank | `+0x084` u16 (0 in every record) | — | `sounds` `Sound` | [L] |
| `dropsfxframe` | always blank | `+0x086` u8 (0 in every record) | — | — | [L] |
| `add func` | int 1..2 (2 distinct), 44 blank | `+0x087` u8 | — | — | [C] |
| `prop1..9`, `aprop1a..5b` and parameters | (out of scope) | `+0x088..+0x1B7` (not mapped) | — | — | — |

## Record layout

`+0x000` u16, 0 in every record (`unk_000`) · `+0x002` `index` char[34] · `+0x024` 4 bytes, 0 in every
record (`unk_024`; `setitems.txt` has no `version` column; `uniqueitems` holds `version` here) ·
`+0x028` `item` · `+0x02C` `set` · `+0x030` `lvl` · `+0x032` `lvl req` · `+0x034` `rarity` · `+0x038`
`cost mult` · `+0x03C` `cost add` · `+0x040`/`+0x041` transforms · `+0x042..+0x081` 64 bytes, 0 in every
record (`flippyfile`, `invfile`) · `+0x082..+0x086` sounds and frame, 0 in every record · `+0x087`
`add func` · `+0x088..+0x1B7` property block (not mapped). The `[C]` offsets are pinned by the data;
`+0x040..+0x086` is placed by analogy and is `[L]`, as the table says.

## Interpretation notes

- `[C]` `chrtransform` equals `invtransform` in every one of the 127 rows (14 rows blank in both). The
  two bytes `+0x040`/`+0x041` are equal in every record too, so the data can't say which column is
  which.
- `[C]` **No set item names its own `invfile` or `flippyfile`** in 1.14d: both columns are blank in all
  127 rows. Any per-set-item icon must come from the base item. The item art index uses the base's
  `setinvfile`, else its `invfile`, as a heuristic `[L]`; 35 of 127 rows find a base `setinvfile`, the other 92 fall back to the base `invfile`.

## Open questions

- `[L]` Which inventory file the game shows for a set item (base `setinvfile`, then `invfile`?), and
  how `chrtransform`/`invtransform` combine with the base item's `Transform`/`InvTrans`. Owner: reverser
  ([backlog](../backlog.md), plan 0009 Phase 2 entry).
- `[L]` The order of the pairs the data can't separate (`chrtransform`/`invtransform`,
  `flippyfile`/`invfile`, `dropsound`/`usesound`).
