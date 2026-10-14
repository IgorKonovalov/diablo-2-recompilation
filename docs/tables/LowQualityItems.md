# LowQualityItems (`data/global/excel/lowqualityitems.txt` → `lowqualityitems.bin`)

> **Source archive:** d2exp (`.txt` and `.bin`)   **Rows:** 4 (no `Expansion` marker)   **Record:** 34 B (`0x22`)
> **sha256:** `.txt` `66a8a59dd88e0bed8130a08d803a057f9331f575a7c9a28f0aa622b34f098108`, `.bin` `aaeb6f0eab7d768ac48ecf2fcca82fced595b0529467c2e6cbdd9d38aa3821e3`
> **Doc status:** complete (one column); the row pick `[I]` ([items/0005 § 8](../findings/items/0005-affixes.md#8-superior-low-quality-normal))

## Purpose

One row per low-quality name: `Crude`, `Cracked`, `Damaged`, `Low Quality`. The low-quality builder draws one row per
item and stores it as the item's file index. Reader: `items/affixes`
([items/0005 § 8](../findings/items/0005-affixes.md#8-superior-low-quality-normal), plan 0021). Leads: no lead.

## Row identity

- `[C]` The `.bin` is a u32 record count (4) and 4 records of 34 bytes, one per `.txt` row in order
  ([excel-bin.md](../formats/excel-bin.md)); the loader allocates 34-byte records
  ([data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables), `0x00637549`).
- `[I]` The row index is the drawn value: `row = RNG_Range(item seed, nLow)` (one step), with nLow the count at
  `g_LowQualityItemsInfo` (4), stored as the file index. (fn:ITEMS_BuildLowPick@0x005C2D40,
  fn:sub_006375B0_GetLowQualityInfo@0x006375B0, data:g_LowQualityItemsInfo@0x0096CC58)

## Columns

`[C]` layout: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel lowqualityitems`: 4 records × 1 field
= 4 cells, **0 mismatches**; no uncovered byte.

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `Name` | str {`Cracked`, `Crude`, `Damaged`, `Low Quality`}, 4 distinct, len ≤ 11, 0 blank | `+0x000` char[34] | the name prefix shown on the item `[L]` | — | [C] |

## Interpretation notes

- `[I]` After the row draw, an item with durability gets maximum durability `durability·33/100` (at least 1) and a
  current durability drawn on the **unit** seed; weapons get damage ×75/100 and armour defense ×75/100; then the staff
  mods. None of this reads this table. (fn:ITEMS_BuildLowPick@0x005C2D40,
  [items/0005 § 8](../findings/items/0005-affixes.md#8-superior-low-quality-normal))
- `[L]` Whether `Name` is a string-table key (the strings `Crude`, `Cracked`, `Damaged`, `Low Quality`) or displayed
  as is.

## Open questions

- `[L]` How the client turns the stored row into the displayed name.
