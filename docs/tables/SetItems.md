# SetItems (`data/global/excel/setitems.txt` → `setitems.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 127 (128 data rows − 1 `Expansion` marker)   **Record:** 440 B
> **sha256:** `.txt` `5696730cf84564f1cb815fb362fba13f23e22f5176e854730733519048f711be`, `.bin` `b793de221bf5ebe94e4f8fdbab6b0c4a6ce0f5b1ba8f4ff78f12dc3d851272ce`
> **Doc status:** art, identity and generation columns (generation survey: plan 0019 Phase 0); `.bin` layout of the record head (`+0x000..+0x087`) mapped, the property block not mapped; semantics `[I]` for the art columns ([items/0003](../findings/items/0003-item-graphics.md)) and the generation columns ([items/0004](../findings/items/0004-uniques-sets.md), plan 0019 Phase 1), `[L]` elsewhere

## Purpose

One row per set item: its name, the set it belongs to, the base item it is made from, and how it
looks. **This doc covers the art and identity columns** (plan 0009 Phase 2, the item art index)
**and the observed values of the generation columns** (plan 0019 Phase 0, § Generation columns). The
stat columns (`prop1..9`, `aprop1a..5b` and their parameters) belong to `items/properties`, and what
the code does with the generation columns to `items/uniques-sets`; this doc only links the meanings
that [items/0004](../findings/items/0004-uniques-sets.md) gives (§ Semantics from the set builder). Read by the item art index ([README § Item art index](README.md#item-art-index)).
Leads: no lead; derived from data.

## Row identity

- `[C]` The record index is the data row index once the `Expansion` marker is dropped (0..126); the
  diff below matches record *i* to data row *i* in every mapped column.
- `[C]` `index` is the row's name, unique in all 127 rows. `[I]` The loader adds it to the `setitems` name
  tree in row order, so a TC cell naming it resolves to that row (a hit ≥ 0, so row 0 can be named,
  unlike in `uniqueitems`). ([items/0004 § 6](../findings/items/0004-uniques-sets.md#6-a-tc-cell-that-names-a-unique-or-a-set-item),
  fn:TC_ParseItemCell@0x00654440)
- `[I]` A treasure-class cell can name a set item by `index`: `TC_ParseItemCell` falls back to the
  `setitems` name link (`0x0096C844`) after the unique one
  ([data/0001 §7](../findings/data/0001-excel-loader.md#7-treasure-classes-at-load-time)).
- `[C]` `set` names a row of `sets.txt` by its `index` (all 127 resolve, 32 distinct sets) and is stored
  as that row's index (a u16; the loader reads it as `int16_t`, [items/0004 § 7](../findings/items/0004-uniques-sets.md#7-load-time-slots-in-uniqueitems-setitems-and-sets-the-backlog-questions), `[I]`). `item` is the base item code (all 127 resolve to a `weapons`/`armor`/`misc`
  code). `*item` is a comment column (the base item's name) and is not compiled.
- `[I]` The game loads `setitems.bin` with a 440-byte record (call site `0x00636651`,
  [data/0001 §4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables)).

## Columns

`[C]` layout tags are by data behaviour: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel setitems`
decodes all 127 records and matches every mapped cell (127 × 16 = 2 032 cells, 0 mismatches), and each
`[C]` offset is the only one `excel_bin.py probe` finds. The layout is **partial** on purpose: the 76
property columns are reported by `diff` as outside the layout and are not checked. A column that is
blank in every row, or equal to a sibling in every row, cannot be placed by the data; its position
follows the `uniqueitems` head and the `.txt` order and is `[L]`. `[I]` The set builder reads `lvl` as an
s16 at `+0x030` (`movsx`) and `item` at `+0x028`; the loader reads `set` as a u16 at `+0x02C`
([items/0004 §§ 4, 7](../findings/items/0004-uniques-sets.md#4-the-set-builder-items_buildsetitem-rec-0x005c2940), fn:ITEMS_BuildSetPick@0x005C25C0, fn:sub_00634DC0_LoadSetTables@0x00634DC0).
`[L]` The integer type of the other slots is not pinned (the data is non-negative).
**Meaning:** `[L]` unless tagged in the cell. The art ones are `[I]` from [items/0003](../findings/items/0003-item-graphics.md),
the generation ones `[I]` from [items/0004](../findings/items/0004-uniques-sets.md) (§ Semantics from the set builder).
"Not read by the builders" means the set builder does not test the column; no other reader was looked for.

| Column | Observed type / range | `.bin` field | Meaning (`[L]`) | References | Layout tag |
|---|---|---|---|---|---|
| `index` | str, 127 distinct, len ≤ 29 | `+0x002` char[32] | set item name (identity); `[I]` name-tree key | TC cells | [C] |
| `set` | str, 32 distinct, len ≤ 22 | `+0x02C` u16, row index | owning set; `[I]` set 29 rows are candidates only for a `hellbovine` source; the set's `version` is copied into the row at load | `sets` `index` (all resolve) | [C] |
| `item` | str, 112 distinct, len ≤ 3 | `+0x028` char[4] code | base item; `[I]` a row is a candidate only for an item of this base code | `weapons`/`armor`/`misc` `code` (all resolve) | [C] |
| `*item` | comment column | — (not compiled) | — | — | — |
| `lvl` | int 3..55 (29 distinct) | `+0x030` s16 | `[I]` a row is a candidate only when `lvl` ≤ the item's ilvl (signed compare) | — | [C] |
| `lvl req` | int 2..81 (48 distinct) | `+0x032` u16 | not read by the builders | — | [C] |
| `rarity` | int 1..7 (3 distinct) | `+0x034` 4-byte slot (u32 decode) | `[I]` pick weight, 0 raised to 1 | — | [C] |
| `cost mult` | int, always 5 | `+0x038` 4-byte slot (u32 decode) | — | — | [C] |
| `cost add` | int 2500..5000 (2 distinct) | `+0x03C` 4-byte slot (u32 decode) | — | — | [C] |
| `chrtransform` | str, 16 distinct, len ≤ 4, 14 blank | `+0x040` u8 index, blank = `0xFF` | `[I]` colour of the ground and worn views (with the base `Transform`); blank = no shift | [colors](colors.md) `Code` (all resolve) | [L] |
| `invtransform` | str, 16 distinct, len ≤ 4, 14 blank | `+0x041` u8 index, blank = `0xFF` | `[I]` colour of the inventory icon (with the base `InvTrans`); blank = no shift | [colors](colors.md) `Code` (all resolve) | [L] |
| `flippyfile` | always blank | `+0x042` char[32] (0 in every record) | `[I]` own ground-drop DC6, else the base `flippyfile` | — | [L] |
| `invfile` | always blank | `+0x062` char[32] (0 in every record) | `[I]` own inventory DC6 of an identified item (see notes) | — | [L] |
| `dropsound` | always blank | `+0x082` u16 (0 in every record) | — | `sounds` `Sound` | [L] |
| `usesound` | always blank | `+0x084` u16 (0 in every record) | — | `sounds` `Sound` | [L] |
| `dropsfxframe` | always blank | `+0x086` u8 (0 in every record) | — | — | [L] |
| `add func` | int 1..2 (2 distinct), 44 blank | `+0x087` u8 | — | — | [C] |
| `prop1..9`, `aprop1a..5b` and parameters | (out of scope) | `+0x088..+0x1B7` (not mapped) | — | — | — |

## Record layout

`+0x000` u16, 0 in every record (`rowIndex`) · `+0x002` `index` char[32] · `+0x022` u16, 0 in every
record (`setVersion`) · `+0x024` u16, 0 in every record (`nameKey`) · `+0x026` u16, 0 in every record
(`unk_026`) · `+0x028` `item` · `+0x02C` `set` (u16) · `+0x02E` u16, 0 in every record (`memberSlot`) ·
`+0x030` `lvl` · `+0x032` `lvl req` · `+0x034` `rarity` · `+0x038`
`cost mult` · `+0x03C` `cost add` · `+0x040`/`+0x041` transforms · `+0x042..+0x081` 64 bytes, 0 in every
record (`flippyfile`, `invfile`) · `+0x082..+0x086` sounds and frame, 0 in every record · `+0x087`
`add func` · `+0x088..+0x1B7` property block (not mapped). The `[C]` offsets are pinned by the data;
`+0x040..+0x086` is placed by analogy and is `[L]`, as the table says. `[I]` The game reads `+0x040`,
`+0x041` (colour bytes, `movsx`), `+0x042` and `+0x062` (strings) at those offsets, so the four fields
exist where the table places them; which of each equal pair the compiler fills from which `.txt`
column stays `[L]`. (fn:ITEMGFX_GetItemShift@0x0062C100, fn:ITEMGFX_SelectCelName@0x004DABC0)

- `[I]` `+0x000`, `+0x022`, `+0x024` and `+0x02E` are written at load, so they are 0 in the file. After
  loading `setitems`, `sub_00634DC0_LoadSetTables` stores in each row its own index (`+0x000`), the
  string-table key of `index` (`+0x024`, `0x1507` when missing) and, when `set` is a valid row whose
  member count is below 6, that set's `version` (`+0x022`) and the row's member slot in the set
  (`+0x02E`, the count before linking). The `index` descriptor is 32 bytes long (length `0x1F` at
  `+0x002`), so `index` is char[32] (`+0x002..+0x021`), not char[34]. No stock set has more than 6
  members, so every row gets its version. ([items/0004 § 7](../findings/items/0004-uniques-sets.md#7-load-time-slots-in-uniqueitems-setitems-and-sets-the-backlog-questions),
  fn:sub_00634DC0_LoadSetTables@0x00634DC0, struct:SetItemsRec+0x22, tbl:SetItems.txt:index)
- `[L]` What `+0x026` (u16, 0 in every record) is: items/0004 does not name it.

## Generation columns

Plan 0019 Phase 0. Every count in this section is `[C]` by script:
`python3 -I tools/unique_survey.py workspace/merged/data/global/excel`. What the set builder does with
these columns is § Semantics from the set builder ([items/0004](../findings/items/0004-uniques-sets.md), plan 0019 Phase 1).

- `[C]` `setitems.txt` has **no** `version`, `enabled`, `ladder`, `carry1` or `nolimit` column, and
  `+0x024` (where `uniqueitems` holds `version`) is 0 in every record. The only version a set item has
  in the data is the `version` of its [Sets](Sets.md) row, which the loader copies to `+0x022` (`[I]`,
  § Record layout). No row is blank in `index`, `set`, `item`,
  `lvl`, `lvl req` or `rarity`: there are no label rows to skip.
- `[C]` By the version of their set:

  | Class (set version) | Records | Sets | `lvl` | `lvl req` | `rarity` |
  |---|---|---:|---|---|---|
  | classic (0) | 0..61 (62 rows) | 16 | 3..27 (16 distinct) | 2..20 (13 distinct) | 1..7 (3 distinct) |
  | expansion (100) | 62..126 (65 rows) | 16 | 20..55 (15 distinct) | 13..81 (36 distinct) | 1..7 (3 distinct) |

  The set version changes once along the record order, at the `Expansion` marker.
- `[C]` `lvl` equals the `level` of the row's set in all 127 rows (`sets.bin` has no field for `level`,
  [Sets](Sets.md)).
- `[C]` `rarity` is 7 in 122 rows. The others: 1 in `Arcanna's Sign` (58, `amu`), `Tal Rasha's
  Adjudication` (77, `amu`), `Telling of Beads` (95, `amu`); 3 in `Angelic Halo` (52, `rin`) and
  `McAuley's Paragon` (123, `cap`).

### Candidates per base

The survey prints every base with its unique and set rows (see [UniqueItems § Candidates per
base](UniqueItems.md#candidates-per-base)). For set rows:

- `[C]` The 127 rows name 112 base codes; 14 of them have no unique row, 98 also have an enabled unique.
- `[C]` 8 bases have more than one set row: `amu` 9 (records 1, 9, 20, 28, 33, 53, 58 classic; 77, 95
  expansion), `rin` 2 (29, 52), and `cap` (41, 123), `crn` (11, 23), `mbl` (5, 110), `tbl` (12, 43),
  `tgl` (10, 57), `vbt` (119, 124) with 2 each. `cap` and `mbl` mix a classic and an expansion set.
- `[C]` `index` is unique over the 127 rows: no duplicated name.

## Semantics from the set builder (plan 0019 Phase 1)

All from [items/0004](../findings/items/0004-uniques-sets.md) §§ 4, 6, 7. The builder for a drop is
`ITEMS_BuildSetPick` (fn:ITEMS_BuildSetPick@0x005C25C0); this doc names only what it does with each
column. The full pick belongs to the `items/uniques-sets` spec.

- `[I]` **Candidate filter, in this order**: the set's `version` as copied into the row at load (`+0x022`)
  < 100 or item version ≥ 100; `lvl` ≤ the item's ilvl, compared as signed 16-bit; `item` = the base's
  code; and a row of set 29 only when the creation record's flag bit 0 is set, which the drop code sets
  when the source is monster class 391 (`hellbovine`). Rows are visited in table order. So a classic
  game gets only the members of the 16 classic sets. ([items/0004 § 4](../findings/items/0004-uniques-sets.md#4-the-set-builder-items_buildsetitem-rec-0x005c2940),
  0x005C2630–0x005C26A2, tbl:SetItems.txt:lvl, tbl:SetItems.txt:item, tbl:Sets.txt:version)
- `[I]` **Weight**: `rarity`, 0 raised to 1 (a negative value would be kept). Stock values are 1, 3 and 7.
  ([items/0004 § 4](../findings/items/0004-uniques-sets.md#4-the-set-builder-items_buildsetitem-rec-0x005c2940), tbl:SetItems.txt:rarity)
- `[I]` **Not read by the builders**: `lvl req`. There is no `enabled`, ladder or once-per-game test for
  set items (the table has no such column). ([items/0004 § 4](../findings/items/0004-uniques-sets.md#4-the-set-builder-items_buildsetitem-rec-0x005c2940), 0x005C2630–0x005C26A2)
- `[I]` **TC-named row**: taken with no draw when it passes the filter for this item, else the ordinary
  weighted pick runs. ([items/0004 § 6](../findings/items/0004-uniques-sets.md#6-a-tc-cell-that-names-a-unique-or-a-set-item), 0x005C2661–0x005C2672)

## Interpretation notes

- `[C]` `chrtransform` equals `invtransform` in every one of the 127 rows (14 rows blank in both). The
  two bytes `+0x040`/`+0x041` are equal in every record too, so the data can't say which column is
  which.
- `[C]` **No set item names its own `invfile` or `flippyfile`** in 1.14d: both columns are blank in all
  127 rows. Any per-set-item icon must come from the base item.
- `[I]` Inventory cel of an **identified** set item, first non-empty wins: the row's `invfile`, the base's
  `setinvfile`, the base item type's `InvGfx[min(g, VarInvGfx − 1)]` when `VarInvGfx` > 0 (`g` a per-item
  picture index), the base's `invfile`. An unidentified set item skips the first two. Ground cel: the
  row's `flippyfile`, else the base's (no identification test). ([items/0003](../findings/items/0003-item-graphics.md) § 2,
  fn:ITEMGFX_SelectCelName@0x004DABC0, tbl:SetItems.txt:invfile, tbl:ItemTypes.txt:VarInvGfx)
- `[I]` Shift: inventory `InvTrans` × `invtransform`, ground and worn `Transform` × `chrtransform`; a blank
  colour gives no shift, with no fallback to an affix colour. ([items/0003](../findings/items/0003-item-graphics.md) § 3, fn:ITEMGFX_GetItemShift@0x0062C100,
  tbl:SetItems.txt:invtransform)
- `[C]` In stock data: 35 of 127 rows find a base `setinvfile`, 11 (bases `rin`, `amu`) reach the
  `VarInvGfx` step, 81 the base `invfile` (`tools/item_art.py index`, `inv_src`).

## Open questions

- Answered `[I]` by [items/0003](../findings/items/0003-item-graphics.md): which inventory file a set item shows and how its colours combine
  with the base `Transform`/`InvTrans` (Interpretation notes).
- `[L]` The order of the pairs the data can't separate (`chrtransform`/`invtransform`,
  `flippyfile`/`invfile`, `dropsound`/`usesound`).
- Answered `[I]` by [items/0004](../findings/items/0004-uniques-sets.md): which of `lvl`, `lvl req`,
  `rarity` and the set's `version` the set builder tests, and in what order (§ Semantics from the set
  builder).
- `[L]` Whether any code outside the set builder reads `lvl req`.
