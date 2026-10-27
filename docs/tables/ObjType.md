# ObjType (`data/global/excel/ObjType.txt` → `objtype.bin`)

> **Source archive:** d2exp (`.txt` and `.bin`)   **Rows:** 573 (one `Expansion` marker row, no record)   **Record:** 52 B (`0x34`)
> **sha256:** `.txt` `bb036f337fb0feceec4b5b65d2a318c02d675a6f0577e017b2949f0ba02aba46`, `.bin` `299482ce1ae88e53db7ea6f9df805145b6b85c56237b73a37ba8be3c17a3064f`
> **Doc status:** complete for layout (every byte placed); the token's use `[I]`, the rest `[L]`

## Purpose

One row per object class: an editor name and the object's animation token. `[I]` The token is the first part of an
object's animation name: `COMPOSIT_BuildCofName` builds an object's `animdata.d2` record name from the object token
(`0x0065B570(class, 0)`), the [ObjMode](ObjMode.md) `Token` of the mode and `hth`
([anim/0001 § 2](../findings/anim/0001-modes-frames.md#2-records-the-token-the-lookup-and-the-fallback),
fn:COMPOSIT_BuildCofName@0x0064F5B0). Reader: `anim/timing` (plan 0050). Same 52-byte shape as [ObjMode](ObjMode.md)
and [PlrType](PlrType.md).

## Row identity

- `[C]` The `.bin` is a u32 record count (573) and 573 records of 52 bytes, one per `.txt` data row in order once the
  `Expansion` marker row (between records 409 `fortress brazier #2` and 410 `Siege Control`) is dropped. The loader
  passes record size 52 (`0x0065B216`, [data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables)).
- `[C]` **Record *k* pairs with [Objects](Objects.md) record *k*.** Both tables have 573 records and their `Expansion`
  marker at the same `.txt` line, and the `Token`s agree on 557 of the 573 records (below). `[I]` The record is looked
  up by object class (`0x0065B570(class, 0)`, anim/0001 § 2); `[L]` that the class passed is the Objects record index.
- `[C]` Neither column is unique: `Name` has 527 distinct values; `Token` 532 once trailing spaces are dropped (528
  ignoring case), `ss` 27 times, `xk` 6, `pp` 4.

## Columns

`[C]` layout: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel objtype`: 573 records × 2 mapped
fields = **1 146 cells, 0 mismatches**; `excel_bin.py unknown … objtype` lists only `+0x024` (16 B, zero in every
record). `probe` finds no field for `Beta`. Gate survey `excel_layout` (`objtype_cells=1146`).

| Column | Observed type / range | `.bin` field | Meaning | References | Layout tag |
|---|---|---|---|---|---|
| `Name` | str ≤ 23 chars, 527 distinct | `+0x000` `char[32]` | editor name of the object `[L]` (differs from the Objects `Name` in 496 rows: `Casket #5` / `Casket`) | — | [C] |
| `Token` | str 2 chars, 3 in 10 rows (`NU0` row 0, `ss ` with a trailing space in 9) | `+0x020` 4-byte code, space padded (`C5  `; `ss ` stores `ss  `, `NU0` stores `NU0 `) | `[I]` the object's animation token, the first part of the record name (anim/0001 § 2) | — | [C] |
| `Beta` | int 0/1 (0: 419, 1: 154) | none | not compiled `[C]`; meaning `[L]` | — | — |
| — | — | `+0x024` 16 B | zero in every record | — | [C] value |

| Record | `Name` | `Token` | `Beta` | Objects `Token` |
|---:|---|---|---:|---|
| 1 | Casket #5 | C5 | 1 | C5 |
| 45 | Town 1 Ambient | SS | 1 | S1 |
| 410 | Siege Control | zq | 0 | zq |

## Timing (plan 0050)

The table has no timing column. [Objects § Timing](Objects.md#timing-plan-0050-phase-0) and
[ObjMode § Timing](ObjMode.md#timing-plan-0050-phase-0) join the **Objects** `Token` with `animdata.d2`; anim/0001 § 2
names this table's token for the record name. Where an entry and its finding differ the finding wins, so the
token-by-token comparison (`python3 -I tools/anim_survey.py objects workspace/merged`, `OBJTYPE` lines; survey keys
`obj_objtype_*`):

- `[C]` The two tokens differ in **16** records (`obj_objtype_token_ne`), compared ignoring case and trailing spaces:
  record 0 (`NU0` in both `.txt` files, but Objects stores it cut to `NU` and this table as `NU0 `; the row has no
  flagged mode) and 15 with another token
  (45 `SS`/`S1`, 78 `SS`/`TA`, 133 `az`/`xx`, 194 `9c`/`sl`, 277, 361, 363, 419, 425, 473, 504, 505, 509, 510, 511).
- `[C]` Of the 1 603 flagged (row, mode) pairs, **1 491** have a record under this table's token
  (`obj_objtype_hit`), against 1 483 under the Objects `Token`. Example: record 194 (`stair`, modes 0–2) has `9CNUHTH`,
  `9CONHTH` and `9COPHTH` but only `SLNUHTH` under its Objects token `sl`.
- `[I]` The server's own object frame fields do not come from the record: `UNIT_AnimInit` sets an object's length,
  start frame and rate from Objects `FrameCnt`, `Start` and `FrameDelta` (anim/0001 § 3,
  fn:UNIT_AnimInit@0x00624390). So the token affects which `animdata.d2` record an object gets, not its server frame
  count.

## Open questions

- `[L]` Whether `0x0065B570`'s class is the Objects record index (the pairing above is by data), and whether the
  object record name keeps `NU0`'s third character (record 0, the `Dummy` row, has no flagged mode, so the data does
  not need it).
- `[L]` Who else reads the table (anim/0001 reads only the record name); what `Beta` meant to the editor.
- `[L]` Whether the 16 zero bytes at `+0x024` are filled at load, as for [ObjMode](ObjMode.md#open-questions).
