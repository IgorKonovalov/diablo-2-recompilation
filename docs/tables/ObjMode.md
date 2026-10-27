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

## Timing (plan 0050 Phase 0)

The table has no timing column. An object's frames per mode are in [Objects](Objects.md#timing-plan-0050-phase-0)
(`FrameCnt<k>`, `FrameDelta<k>`) and in `animdata.d2` ([animdata](../formats/animdata.md)), whose record names are
`<Objects Token><this table's Token>HTH`. `[C]` The join (`python3 -I tools/anim_survey.py objects workspace/merged`;
survey keys `obj_*`), per row of this table: Objects rows whose `Mode<k>` is 1, and how many of them have a record.

| Row | `Token` | Objects rows with `Mode<k>` | With a record | `FrameCnt<k>` = record `frames` | `FrameDelta<k>` = record `speed` |
|---:|---|---:|---:|---:|---:|
| 0 | NU | 562 | 561 | 473 | 157 |
| 1 | OP | 422 | 391 | 262 | 234 |
| 2 | ON | 441 | 410 | 350 | 127 |
| 3 | S1 | 97 | 41 | 22 | 26 |
| 4 | S2 | 33 | 33 | 32 | 24 |
| 5 | S3 | 27 | 27 | 26 | 23 |
| 6 | S4 | 20 | 19 | 7 | 18 |
| 7 | S5 | 1 | 1 | 1 | 0 |

1 603 flagged modes, 1 483 with a record, 120 without (`S1` 56, `OP` 31, `ON` 31, `NU` 1, `S4` 1). The Objects columns
and the comparison are in [Objects § Timing](Objects.md#timing-plan-0050-phase-0).

## Open questions

- `[L]` Whether the 16 zero bytes at `+0x024` are filled at load (e.g. a string-table index or a pointer). Reverser,
  the loader at `0x0065B22E`.
