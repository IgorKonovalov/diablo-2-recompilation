# ArmType (`data/global/excel/ArmType.txt` → `armtype.bin`)

> **Source archive:** d2exp (`.txt` and `.bin`)   **Rows:** 3   **Record:** 52 B
> **sha256:** `.txt` `288a8c7964e5d4dc0dc3e2a05f6793e9b3946a46b50e1604c86c172e91d291a1`, `.bin` `3b66289f8e5628698b572f58ad62d4f57f7f6aec4adb35074f0f9e05b1f69761`
> **Doc status:** complete for layout; art and identity columns only; semantics `[I]` ([items/0003](../findings/items/0003-item-graphics.md))

## Purpose

The three armour weights of worn character art: `Lite`/`lit`, `Medium`/`med`, `Heavy`/`hvy`. **This doc
covers art and identity only** (plan 0009 Phase 2): the token is a DCC component code. Body armour rows
of [Armor](Armor.md) (`rArm`, `lArm`, `Torso`, `Legs`, `rSPad`, `lSPad`, values 0..2) name a row by
index. Read by the item art index ([README § Item art index](README.md#item-art-index)). Leads: no lead;
derived from data, then code ([items/0003](../findings/items/0003-item-graphics.md)).

## Row identity

- `[C]` Rows are addressed by index 0..2; `Name` and `Token` are unique.
- `[I]` The game loads `armtype.bin` with a 52-byte record (call site `0x0065B3AE`,
  [data/0001 §4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables)).

## Columns

`[C]` `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel armtype`: 3 records × 2 mapped
fields, 0 mismatches; each offset is the only one `probe` finds. With three rows this rests on little
data; `composit.bin` (also 52 B) has the same shape (name at `+0x000`, space-padded token at `+0x020`,
zeros after), seen in a hex dump of its records.

| Column | Observed type / range | `.bin` field | Meaning | References | Layout tag |
|---|---|---|---|---|---|
| `Name` | str, 3 distinct, len ≤ 6 | `+0x000` char[32] | display name `[L]` | — | [C] |
| `Token` | str, 3 distinct, len 3 | `+0x020` char[4] code (space padded) | DCC component code of a worn body part `[I]` (§ Interpretation notes) | `chars/<cls>/<layer>/<cls><layer><token>…dcc` | [C] |

## Record layout

`+0x000` `Name` char[32] · `+0x020` `Token` char[4] · `+0x024..+0x033` 16 bytes, 0 in all three records
(not a column). `[C]`

## Interpretation notes

- `[I]` A torso item (body location 3) fills six worn layers from its six Armor body-part bytes
  (`+0x116..+0x11B`), each an armtype row whose `Token` (`+0x020`) is that layer's component code:
  `Torso`→`TR`, `Legs`→`LG`, `rArm`→`RA`, `lArm`→`LA`, `rSPad`→`S1`, `lSPad`→`S2`. The token is stored
  as an index into the composite token table, which starts `lit`, `med`, `hvy`. ([items/0003](../findings/items/0003-item-graphics.md)
  § 5, fn:sub_0063D690_ArmorPartsRead@0x0063D690, fn:sub_0064F500_ArmorPartForLayer@0x0064F500,
  fn:sub_0065B620_ArmTypeRecord@0x0065B620, fn:sub_0063D710_CompTokenTableBuild@0x0063D710,
  tbl:armtype.txt:Token, tbl:Armor.txt:Torso)
- `[C]` Data check of that reading: every body-armour row of Armor finds at least one player DCC per
  part in `merged/` (`tools/item_art.py index`). It corroborates the file naming, not the code path.

## Open questions

- None of this doc's. Whether another code path reads `Token` is not traced: items/0003 names only the
  composite readers.
