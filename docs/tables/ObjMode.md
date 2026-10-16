# ObjMode (`data/global/excel/ObjMode.txt` → `ObjMode.bin`)

> **Source archive:** d2exp (`.txt` and `.bin`)   **Rows:** 8 (no `Expansion` marker)   **Record:** 52 B (`0x34`)
> **sha256:** `.txt` `23fd7ab06a6942239c75ddd97540d89b16fcd88f51a956e61794700353babec3`, `.bin` `25484b14e1f84f4cf53bd575c0aaebac7bab75bff35972237b3c394a0c4b7300`
> **Doc status:** complete for layout (every byte placed); semantics `[L]`

## Purpose

The eight object modes, by name and two-letter token: `Neutral` `NU`, `Operating` `OP`, `Opened` `ON`, `Special1`..`Special5`
`S1`..`S5`. `[L]` The row index is the mode number that indexes the eight-column runs of [Objects](Objects.md)
(`Mode0..7`, `HasCollision0..7`, `FrameCnt0..7`, …), and the token names the mode's animation files. `[I]` For
`HasCollision` the code reads Objects `+0x120 + mode` ([drlg/0005 § 5](../findings/drlg/0005-collision.md#5-unit-marks),
fn:UNIT_CollMarkRect@0x00620A70); that the mode numbers are this table's rows is the column naming. [MonMode](MonMode.md) and
[PlrMode](PlrMode.md) have the same 52-byte shape.

## Row identity

- `[C]` The `.bin` is a u32 record count (8) and 8 records of 52 bytes, one per `.txt` row in order. The loader passes
  record size 52 (0x0065B22E, [data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables)).
- `[C]` Both columns are unique. `[L]` Rows are addressed by index (the mode number).

## Columns

`[C]` layout: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel objmode`: 8 records × 2 mapped fields
= 16 cells, **0 mismatches**; `excel_bin.py unknown … objmode` lists only `+0x024` (16 B, zero in every record).

| Column | Observed type / range | `.bin` field | Meaning (`[L]` unless stated) | References | Layout tag |
|---|---|---|---|---|---|
| `Name` | str ≤ 9 chars, 8 distinct | `+0x000` `char[32]` | mode name | — | [C] |
| `Token` | str 2 chars, 8 distinct | `+0x020` 4-byte code, space padded (`NU  `) | mode token | — | [C] |
| — | — | `+0x024` 16 B | zero in every record | — | [C] value |

| Row | `Name` | `Token` |
|---|---|---|
| 0 | Neutral | NU |
| 1 | Operating | OP |
| 2 | Opened | ON |
| 3..7 | Special1..Special5 | S1..S5 |

## Open questions

- `[L]` Whether the 16 zero bytes at `+0x024` are filled at load (e.g. a string-table index or a pointer). Reverser,
  the loader at `0x0065B22E`.
