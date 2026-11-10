# Composit (`data/global/excel/Composit.txt` → `composit.bin`)

> **Source archive:** `.txt` d2exp, `.bin` d2exp   **Rows:** 16 `.bin` records (= `.txt` data rows)   **Record:** 52 B
> **sha256:** `.txt` `f59507ae8d7d4fa6a919f502ea957b47369ac4077ae21e2fa28de360a515c604`, `.bin` `4fbabef748a3bc7db0dae25577ef56ae7003a6730efece2ce185b394d1c85c1e`
> **Doc status:** columns and layout complete (plan 0068 Phase 1); one reader named in [items/0003](../findings/items/0003-item-graphics.md)

## Purpose

The 16 composite layers of a character or monster that is drawn from separate parts, each with a two-letter animation token: `Head` `HD`, `Torso` `TR`, `Legs` `LG`, `RightArm` `RA`, `LeftArm` `LA`, `RightHand` `RH`, `LeftHand` `LH`, `Shield` `SH`, `Special1..8` `S1..S8`. The `component` column of [Weapons](Weapons.md), [Armor](Armor.md) and [Misc](Misc.md) is a row index into this table ([items/0003](../findings/items/0003-item-graphics.md) names the worn-layer path `[I]`, and `sub_0065B5E0_CompositRecord` as the 0x34-byte record reader `[I]`); Loader call site `0x0065B33E`, record 52. Leads: none.

## Row identity

- `[C]` Rows are addressed by **row index** 0..15 in file order (16 layers); `Name` and `Token` are each unique. No `Expansion` row.

## Columns

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `Name` | str, 16 distinct, len <= 9, 0 blank | +0x000 char[32] | layer name | — | [C] |
| `Token` | str, 16 distinct, len <= 2, 0 blank | +0x020 4-char code | two-letter animation token of the layer | — | [C] layout, [I] the client's layer token ([items/0003](../findings/items/0003-item-graphics.md): `sub_0065B5E0_CompositRecord` reads the rows into the 16 layer tokens) |

## Interpretation notes

- `[C]` Layout: the ObjMode/MonMode shape: `Name` as a 32-byte string, `Token` as a 4-character code at +0x20, then 16 bytes that are 0 in every record (`unk_024`) (`python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel composit`, 32 of 32 cells; `excel_bin.py unknown` lists only `unk_024`).
- Readers and what the unit-side animation takes from the table: plan 0068 Phase 2 item 3. `COMPOSIT_BuildCofName` (`0x0064F5B0`, [anim/0001 § 2](../findings/anim/0001-modes-frames.md#2-records-the-token-the-lookup-and-the-fallback)) builds a record name from the unit's type token, its mode token and the weapon class; that finding names no read of a composit row.
- `[I]` Readers (plan 0068 Phase 2, [data/0006 § 3](../findings/data/0006-loaded-tables-and-bundles.md#3-composit-overlay-skilldesc-arena-plan-item-3-with-monsounds-and-automap)): `g_pComposit` (`0x0096D4EC`) is reached only through `sub_0065B5E0_CompositRecord`, whose one caller is the client at `0x004DA7A5`. The server reads no composit row: presentation.
- The record count is checked by the full-tier surveys: `excel` (`.bin` count against `.txt` data rows) and `excel_layout` (every `.bin` cell against its `.txt` cell, layout in `tools/excel_layouts.py`) (`python3 -I tools/gate.py --full`).

## Open questions

- None for the rules (client only).
