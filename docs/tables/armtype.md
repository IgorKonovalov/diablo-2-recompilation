# ArmType (`data/global/excel/ArmType.txt` → `armtype.bin`)

> **Source archive:** d2exp (`.txt` and `.bin`)   **Rows:** 3   **Record:** 52 B
> **sha256:** `.txt` `288a8c7964e5d4dc0dc3e2a05f6793e9b3946a46b50e1604c86c172e91d291a1`, `.bin` `3b66289f8e5628698b572f58ad62d4f57f7f6aec4adb35074f0f9e05b1f69761`
> **Doc status:** complete for layout; art and identity columns only; semantics `[L]`

## Purpose

The three armour weights of worn character art: `Lite`/`lit`, `Medium`/`med`, `Heavy`/`hvy`. **This doc
covers art and identity only** (plan 0009 Phase 2): the token is a DCC component code. Body armour rows
of [Armor](Armor.md) (`rArm`, `lArm`, `Torso`, `Legs`, `rSPad`, `lSPad`, values 0..2) name a row by
index. Read by the item art index ([README § Item art index](README.md#item-art-index)). Leads: no lead;
derived from data.

## Row identity

- `[C]` Rows are addressed by index 0..2; `Name` and `Token` are unique.
- `[I]` The game loads `armtype.bin` with a 52-byte record (call site `0x0065B3AE`,
  [data/0001 §4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables)).

## Columns

`[C]` `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel armtype`: 3 records × 2 mapped
fields, 0 mismatches; each offset is the only one `probe` finds. With three rows this rests on little
data; `composit.bin` (also 52 B) has the same shape (name at `+0x000`, space-padded token at `+0x020`,
zeros after), seen in a hex dump of its records.

| Column | Observed type / range | `.bin` field | Meaning (`[L]`) | References | Layout tag |
|---|---|---|---|---|---|
| `Name` | str, 3 distinct, len ≤ 6 | `+0x000` char[32] | display name | — | [C] |
| `Token` | str, 3 distinct, len 3 | `+0x020` char[4] code (space padded) | DCC component code of a worn body part | `chars/<cls>/<layer>/<cls><layer><token>…dcc` | [C] |

## Record layout

`+0x000` `Name` char[32] · `+0x020` `Token` char[4] · `+0x024..+0x033` 16 bytes, 0 in all three records
(not a column). `[C]`

## Interpretation notes

- `[L]` An Armor body-part column (0..2) selects an armtype row, and the token is the component code of
  that part's DCC on the matching composit layer (`rArm`→`RA`, `lArm`→`LA`, `Torso`→`TR`, `Legs`→`LG`,
  `rSPad`→`S1`, `lSPad`→`S2`). Data check only: with this reading every body-armour row of Armor finds
  at least one player DCC per part in `merged/` (`tools/item_art.py index`). No code anchor.

## Open questions

- `[L]` The part → layer pairing above, and whether the token is used anywhere else. Owner: reverser
  ([backlog](../backlog.md), plan 0009 Phase 2 entry).
