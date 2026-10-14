# QualityItems (`data/global/excel/qualityitems.txt` → `qualityitems.bin`)

> **Source archive:** d2exp (`.txt` and `.bin`)   **Rows:** 8 (no `Expansion` marker)   **Record:** 112 B (`0x70`)
> **sha256:** `.txt` `3d62dde3248648d1de89a994241ab7b85f3de412ddde2076b553fac693699df4`, `.bin` `cf7d88e236c86c27840dc5b484f9fc0ab43c0e75b85d3d3f65e9cdd9f82d7292`
> **Doc status:** layout complete; semantics `[I]` for the columns the superior builder reads
> ([items/0005 § 8](../findings/items/0005-affixes.md#8-superior-low-quality-normal)), the property columns `[L]`
> (`items/properties`)

## Purpose

One row per superior ("hiquality") mod set: the one or two properties a superior item gets (`mod1*`, `mod2*`), the
item kinds the row may go on (ten type flags), and two display strings. The superior builder draws one row per item
and applies its properties. Reader: `items/affixes`, the superior builder
([items/0005 § 8](../findings/items/0005-affixes.md#8-superior-low-quality-normal), plan 0021). The property values are
`items/properties`. Leads: no lead; derived from data and items/0005.

## Row identity

- `[C]` The `.bin` is a u32 record count (8) and 8 records of 112 bytes, one per `.txt` row in order
  ([excel-bin.md](../formats/excel-bin.md)). The loader allocates 112-byte records
  ([data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables), `0x00636A83`).
- `[I]` The row index is the record the superior builder picks and the value it stores as the item's file index
  (`ITEMS_SetFileIndex`). `QUALITYITEMS_GetRecord(row)` returns record `row` of `g_QualityItemsInfo`
  (`{count, records}`). (fn:ITEMS_BuildSuperiorPick@0x005C2970, fn:QUALITYITEMS_GetRecord@0x00636B20,
  fn:ITEMS_SetFileIndex@0x00629DF0, data:g_QualityItemsInfo@0x0096CC50)
- `[C]` The table has no key column; rows are addressed by index only.

## Columns

`[C]` layout: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel qualityitems`: 8 records × 21 mapped
fields = 168 cells, **0 mismatches**; `excel_bin.py unknown … qualityitems` lists `+0x00B` and `+0x06C..+0x06F`, 0 in
every record. Observed values are from `.txt` cells (8 rows).

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `nummods` | int {1, 2}, 0 blank | `+0x00A` u8 | number of mod slots in use `[L]` | — | [C] |
| `mod1code` | str {`ac%`, `att`, `dmg%`, `dur%`}, 0 blank | `+0x00C` s32 row index | first property `[L]` (`items/properties`) | [Properties](Properties.md) `code` | [C] |
| `mod1param` | int {0}, 0 blank | `+0x010` s32 | property parameter `[L]` | — | [C] value; slot by stride `[L]` |
| `mod1min` | int {1, 5, 10}, 0 blank | `+0x014` s32 | property minimum `[L]` | — | [C] |
| `mod1max` | int {3, 15}, 0 blank | `+0x018` s32 | property maximum `[L]` | — | [C] |
| `mod2code` | str {`dmg%`, `dur%`}, 4 blank | `+0x01C` s32 row index, blank −1 | second property `[L]` | [Properties](Properties.md) `code` | [C] |
| `mod2param` | int {0}, 1 blank | `+0x020` s32 | property parameter `[L]` | — | [C] value; slot by stride `[L]` |
| `mod2min` | int {5, 10}, 4 blank | `+0x024` s32 | property minimum `[L]` | — | [C] |
| `mod2max` | int {15}, 4 blank | `+0x028` s32 | property maximum `[L]` | — | [C] |
| `ToHitMin`, `ToHitMax`, `Dam%Min`, `Dam%Max`, `AC%Min`, `AC%Max`, `Dur%Min`, `Dur%Max` | int, {0} or the row's mod range | — (not compiled) | editor copies of the mod ranges | — | [C] (no offset under any encoding) |
| `effect1` | str {`improved armor class`, `improved damage`, `improved durability`, `improved to hit`}, 0 blank | `+0x02C` char[32] | description of mod 1 `[L]` | — | [C] |
| `effect2` | str {`improved damage`, `improved durability`}, 4 blank | `+0x04C` char[32] | description of mod 2 `[L]` | — | [C] |
| `armor` | int {0, 1} | `+0x000` u8 | `[I]` row allowed on an `armo` item that is not a shield, boots, gloves or belt | — | [C] family, see flags |
| `weapon` | int {0, 1} | `+0x001` u8 | `[I]` row allowed on a `weap` item that is not a scepter, wand, staff, bow or crossbow | — | [C] family |
| `shield` | int {0, 1} | `+0x002` u8 | `[I]` base type 2 (`shie`) | — | [C] family |
| `thrown` | int {0, 1}, equal to `weapon` in every row | — (not compiled) | no byte; see flags | — | [I] |
| `scepter` | int {0, 1} | `+0x003` u8 | `[I]` base type 24 (`scep`) | — | [C] family |
| `wand` | int {0, 1} | `+0x004` u8 | `[I]` base type 25 (`wand`) | — | [C] family |
| `staff` | int {0, 1} | `+0x005` u8 | `[I]` base type 26 (`staf`) | — | [C] family |
| `bow` | int {0, 1} | `+0x006` u8 | `[I]` base type 27 (`bow`) or 35 (`xbow`) | — | [C] family |
| `boots` | int {0, 1} | `+0x007` u8 | `[I]` base type 15 (`boot`) | — | [C] family |
| `gloves` | int {0, 1} | `+0x008` u8 | `[I]` base type 16 (`glov`) | — | [C] family |
| `belt` | int {0, 1} | `+0x009` u8 | `[I]` base type 19 (`belt`) | — | [C] family |
| `level` | int {1, 3} | — (not compiled) | — | — | [C] (no offset) |
| `multiply`, `add` | int {2, 3, 5}; {100, 200, 250, 350} | — (not compiled) | price columns `[L]` | — | [C] (no offset) |

### The ten flag bytes

- `[C]` By data, bytes `+0x000..+0x009` are ten u8 flags, and the eleven flag columns fall into two families whose
  members are equal in every row: the weapon family (`weapon`, `thrown`, `scepter`, `wand`, `staff`, `bow`) fits bytes
  1, 3, 4, 5, 6, and the armour family (`armor`, `shield`, `boots`, `gloves`, `belt`) fits bytes 0, 2, 7, 8, 9. So one
  weapon-family column has no byte, and `excel_bin.py probe` cannot say which column feeds which byte inside a family.
- `[I]` The layout follows the `.txt` order without `thrown`, which is the order the type test reads the bytes in:
  `sub_0065E7D0_QualityItemTypeOk` tests byte 1 for a type-45 (`weap`) item whose base type is none of
  24/25/26/27/35, byte 0 for a type-50 (`armo`) item whose base type is none of 2/15/16/19, and otherwise the byte for
  the exact base type (2 → 2, 24 → 3, 25 → 4, 26 → 5, 27/35 → 6, 15 → 7, 16 → 8, 19 → 9). No byte serves throwing
  weapons, so `thrown` is the column that is not compiled. (fn:sub_0065E7D0_QualityItemTypeOk@0x0065E7D0,
  [items/0005 § 8](../findings/items/0005-affixes.md#8-superior-low-quality-normal))

## Interpretation notes

- `[I]` **The superior pick.** n = the row count (8), or 4 when the base is throwable or `nodurability`; one LCG step
  per draw, `row = low & (n − 1)` for a power of two else `low % n`; a row already tried is redrawn; the first row
  that passes the type test is taken, its properties applied, then the staff mods. All n rows failing → the builder
  fails (normal fallback). (fn:ITEMS_BuildSuperiorPick@0x005C2970,
  [items/0005 § 8](../findings/items/0005-affixes.md#8-superior-low-quality-normal))
- `[C]` By data, rows 0–3 hold no `dur%` (`att`, `dmg%`, `ac%`, `att`+`dmg%`) and rows 4–7 each hold `dur%`, so the
  "first 4 rows" restriction of throwable and `nodurability` bases keeps exactly the rows without durability.
- `[I]` The pick's `tried` buffer is 10 bytes, so a table of more than 10 rows would overflow it; stock has 8
  ([items/0005 § 8](../findings/items/0005-affixes.md#8-superior-low-quality-normal)).
- `[C]` By data, `mod1code`/`mod2code` resolve against [Properties](Properties.md) `code`; a blank `mod2code` stores −1.

## Open questions

- `[L]` Whether `nummods` is read at all, and what `+0x06C` (0 in every record) holds at run time.
- `[L]` The property roll of the chosen row (`sub_0065FEC0_ItemApplyProps`), `items/properties`.
