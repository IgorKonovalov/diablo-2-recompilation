# UniqueItems (`data/global/excel/UniqueItems.txt` → `uniqueitems.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 402 (403 data rows − 1 `Expansion` marker)   **Record:** 332 B
> **sha256:** `.txt` `161a5ac42bbcc281e29647822c5a119ac593cef3d631b2ef693b4e5075eab46c`, `.bin` `29328c76a0881f57a268ceba1eefeb6728720881085593faea47e3d7aa708769`
> **Doc status:** art and identity columns only; `.bin` layout of the record head (`+0x000..+0x08B`) complete, the property block not mapped; semantics `[L]` except the art columns (`[I]`, [items/0003](../findings/items/0003-item-graphics.md))

## Purpose

One row per unique item: its name, the base item it is made from, and how it looks. **This doc covers
the art and identity columns only** (plan 0009 Phase 2, the item art index). The stat columns
(`prop1..12`, `par`, `min`, `max`) and the generation columns' semantics belong to the items/uniques
work and are not described here. Read by the item art index ([README § Item art index](README.md#item-art-index)).
Leads: no lead; derived from data.

## Row identity

- `[C]` The record index is the data row index once the `Expansion` marker is dropped (0..401):
  `uniqueitems.bin` holds 402 records and the diff below matches record *i* to data row *i* in every
  mapped column.
- `[C]` `index` is the row's name. It is **not unique**: 393 distinct values over 401 named rows
  (`Rainbow Facet` ×8, `Azurewrath` ×2; one of the two `Azurewrath` rows has `enabled` 0), and the last
  row (401) is blank in every column. A consumer that keys on `index` must also carry the row number.
- `[I]` A treasure-class cell can name a unique by `index`: `TC_ParseItemCell` falls back to the
  `uniqueitems` name link (`0x0096C850`) when the cell is neither an item code nor a TC name
  ([data/0001 §7](../findings/data/0001-excel-loader.md#7-treasure-classes-at-load-time)). Which of two
  equal names wins is not anchored `[L]`.
- `[C]` 14 rows have a blank `code`. Five are label rows whose `index` reads as a heading (`Armor`,
  `Elite Uniques`, `Rings`, `Class Specific`, and the blank row 401); the others (`Gore Ripper`,
  `Zakarum's Salvation`, `Odium`, `Larzuk's Champion`, `Giantmaimer`, `Nethercrow`, `Warriv's Warder`,
  `Merman's Speed`, `Sigurd's Staunch`) are named rows with no base item. All 388 non-blank `code` cells
  resolve to a `weapons`/`armor`/`misc` code.
- `[I]` The game loads `uniqueitems.bin` with a 332-byte record (call site `0x00634CEA`,
  [data/0001 §4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables)).

## Columns

`[C]` layout tags are by data behaviour: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel uniqueitems`
decodes all 402 records and matches every mapped cell (402 × 18 = 7 236 cells, 0 mismatches), and each
`[C]` offset is the only one `excel_bin.py probe` finds for that column. The layout is **partial** on
purpose: the 48 property columns are reported by `diff` as outside the layout and are not checked.
`[L]` The integer type the game reads inside a slot (narrower read, signedness) is not pinned: the
data is non-negative and no code anchor reads these fields. The `.bin field` type is the slot decode
`excel_bin.py` uses, not a claim about that type.
**Meaning:** `[L]` unless tagged in the cell; only the art and identity columns get a meaning, and the
art ones are `[I]` from [items/0003](../findings/items/0003-item-graphics.md).

| Column | Observed type / range | `.bin` field | Meaning (`[L]`) | References | Layout tag |
|---|---|---|---|---|---|
| `index` | str, 393 distinct, len ≤ 25, 1 blank | `+0x002` char[34] | unique name (identity, see above) | TC cells | [C] |
| `version` | int 0..100 (2 distinct), 5 blank | `+0x024` 4-byte slot (u32 decode) | 0 classic, 100 expansion | — | [C] |
| `enabled` | int 0..1, 15 blank | `+0x02C` bit 0 | row is live | — | [C] |
| `ladder` | int 1, 373 blank | `+0x02C` bit 3 | — | — | [C] |
| `carry1` | int 1, 399 blank | `+0x02C` bit 2 | — | — | [C] |
| `nolimit` | always blank | — (not placed: matches any always-zero byte or bit) | — | — | — |
| `rarity` | int 1..20 (9 distinct), 6 blank | `+0x030` 4-byte slot (u32 decode) | — | — | [C] |
| `lvl` | int 0..110 (76 distinct), 15 blank | `+0x034` u16 | — | — | [C] |
| `lvl req` | int 0..95 (81 distinct), 15 blank | `+0x036` u16 | — | — | [C] |
| `code` | str, 353 distinct, len ≤ 3, 14 blank | `+0x028` char[4] code | base item | `weapons`/`armor`/`misc` `code` (all resolve) | [C] |
| `*type`, `*uber` | comment columns | — (`*` columns are not compiled) | — | — | — |
| `chrtransform` | str, 21 distinct, len ≤ 4, 101 blank | `+0x038` u8 index, blank = `0xFF` | `[I]` colour of the ground and worn views (with the base `Transform`); blank = no shift | [colors](colors.md) `Code` (all resolve) | [C] |
| `invtransform` | str, 21 distinct, len ≤ 4, 192 blank | `+0x039` u8 index, blank = `0xFF` | `[I]` colour of the inventory icon (with the base `InvTrans`); blank = no shift | [colors](colors.md) `Code` (all resolve) | [C] |
| `flippyfile` | str, 3 distinct, len ≤ 7, 399 blank | `+0x03A` char[32] | `[I]` own ground-drop DC6 (`flphmr`, `flpmss`, `flptrch`), else the base `flippyfile` | `data/global/items/<file>.dc6` (all resolve) | [C] |
| `invfile` | str, 81 distinct, len ≤ 7, 262 blank | `+0x05A` char[32] | `[I]` own inventory DC6 of an identified item, row > 0 (see notes) | `data/global/items/<file>.dc6` (all resolve) | [C] |
| `cost mult` | int 3..5 (2 distinct), 6 blank | `+0x07C` 4-byte slot (u32 decode) | — | — | [C] |
| `cost add` | int 5000, 6 blank | `+0x080` 4-byte slot (u32 decode) | — | — | [C] |
| `dropsound` | str `item_gem` in 2 rows, 400 blank | `+0x084` u16 index, blank = 0 | — | `sounds` `Sound` | [L] |
| `usesound` | str `item_gem` in 2 rows, 400 blank | `+0x086` u16 index, blank = 0 | — | `sounds` `Sound` | [L] |
| `dropsfxframe` | int 12 in 2 rows, 400 blank | `+0x088` 4-byte slot (u32 decode) | — | — | [C] |
| `prop1..12`, `par`, `min`, `max` | (out of scope) | `+0x08C..+0x14B`, 12 × 16 B (not mapped) | — | — | — |

`dropsound` and `usesound` are equal in both rows that fill them, so the data fits either at
`+0x084` or `+0x086`; the order shown follows the `.txt` column order and is `[L]`.

## Record layout

`+0x000` u16, 0 in every record (`unk_000`; not a column) · `+0x002` `index` char[34] ·
`+0x024` `version` · `+0x028` `code` · `+0x02C` flag byte (bits 0, 2, 3; bits 1 and 4..7 are 0 in every
record), `+0x02D..+0x02F` 0 in every record · `+0x030` `rarity` · `+0x034` `lvl` · `+0x036` `lvl req` ·
`+0x038` `chrtransform` · `+0x039` `invtransform` · `+0x03A` `flippyfile` char[32] · `+0x05A` `invfile`
char[32] · `+0x07A` u16, 0 in every record (`unk_07A`) · `+0x07C` `cost mult` · `+0x080` `cost add` ·
`+0x084`/`+0x086` sounds · `+0x088` `dropsfxframe` · `+0x08C..+0x14B` property block (not mapped).
`[C]` for every offset tagged `[C]` above; the char-array widths are `[C]` because the next field
starts where they end. `python3 -I tools/excel_bin.py unknown … uniqueitems` lists only `+0x02D..+0x02F`
(zero) and the property block as uncovered.

## Interpretation notes

- `[C]` `chrtransform` and `invtransform` are stored as the row index of the code in `colors.txt`
  (0..20), `0xFF` when blank. They differ in 91 rows, so the two columns are independently placed.
- `[C]` Only 140 rows name an own `invfile` and 3 an own `flippyfile`; every named file exists in
  `data/global/items/`.
- `[I]` Inventory cel of an **identified** unique, first non-empty wins: the row's `invfile` (only for
  row > 0: the test is `file index > 0`), the base's `uniqueinvfile`, the base item type's
  `InvGfx[min(g, VarInvGfx − 1)]` when `VarInvGfx` > 0 (`g` a per-item picture index), the base's
  `invfile`. An unidentified unique skips the first two. Ground cel: the row's `flippyfile` (row 0
  allowed), else the base's, with no identification test. ([items/0003](../findings/items/0003-item-graphics.md) § 2,
  fn:ITEMGFX_SelectCelName@0x004DABC0, tbl:UniqueItems.txt:invfile, tbl:ItemTypes.txt:VarInvGfx)
- `[C]` In stock data row 0 (`The Gnasher`, base `hax`) names `invhaxu`, which is also `hax`'s
  `uniqueinvfile`, so the row-0 rule changes nothing visible. 30 rows (bases `amu`, `rin`, `jew`, `cm3`)
  reach the `VarInvGfx` step (`tools/item_art.py index`, `inv_src`).
- `[I]` Shift: inventory `InvTrans` × `invtransform`, ground and worn `Transform` × `chrtransform`; a blank
  colour gives no shift, with no fallback to an affix colour. ([items/0003](../findings/items/0003-item-graphics.md) § 3, fn:ITEMGFX_GetItemShift@0x0062C100,
  tbl:UniqueItems.txt:chrtransform)

## Open questions

- Answered `[I]` by [items/0003](../findings/items/0003-item-graphics.md): which inventory and ground file a unique shows and how its colours
  combine with the base `Transform`/`InvTrans` (Interpretation notes).
- `[L]` What `+0x000` (u16, always 0) is: a slot filled at load (a string index for `index`?) or
  padding.
- `[L]` Which row a TC cell naming a duplicated `index` resolves to.
