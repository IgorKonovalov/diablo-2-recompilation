# PlrType (`data/global/excel/PlrType.txt` → `plrtype.bin`)

> **Source archive:** d2exp (`.txt` and `.bin`)   **Rows:** 7 (one `Expansion` marker row, no record)   **Record:** 52 B (`0x34`)
> **sha256:** `.txt` `a78710289e5ca6381ecaffbba164549483b2958e0cece5d89b4081123afa4907`, `.bin` `e79def3dccbc8885be5438dec686d9635f8f102a726ef00aa9e3d3eb2fb20f9b`
> **Doc status:** complete for layout (every byte placed); the token's use `[I]`, the rest `[L]`

## Purpose

The seven player classes, by name and two-letter animation token: `Amazon` `AM`, `Sorceress` `SO`, `Necromancer` `NE`,
`Paladin` `PA`, `Barbarian` `BA`, `Druid` `DZ`, `Assassin` `AI`. `[I]` The token is the first part of a player's
animation name: `COMPOSIT_BuildCofName` builds a player's `animdata.d2` record name from the PlrType token of the class
(`0x0065B480(class, 0)`, 0x34-byte records, token at `+0x20`), the [PlrMode](PlrMode.md) `Token` of the mode and the
weapon class ([anim/0001 § 2](../findings/anim/0001-modes-frames.md#2-records-the-token-the-lookup-and-the-fallback),
fn:COMPOSIT_BuildCofName@0x0064F5B0). Reader: `anim/timing` (plan 0050). Same 52-byte shape as [ObjMode](ObjMode.md),
[PlrMode](PlrMode.md), [MonMode](MonMode.md) and [ObjType](ObjType.md).

## Row identity

- `[C]` The `.bin` is a u32 record count (7) and 7 records of 52 bytes, one per `.txt` data row in order once the
  `Expansion` marker row (between `Barbarian` and `Druid`) is dropped. The loader passes record size 52 (`0x0065AE26`,
  [data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables)).
- `[C]` Both columns are unique. The record order is the class order of [CharStats](CharStats.md) (`Amazon` …
  `Assassin`, records 0..6). `[I]` The record is looked up by class number (`0x0065B480(class, 0)`, anim/0001 § 2).

## Columns

`[C]` layout: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel plrtype`: 7 records × 2 mapped
fields = **14 cells, 0 mismatches**; `excel_bin.py unknown … plrtype` lists only `+0x024` (16 B, zero in every
record). Gate survey `excel_layout` (`plrtype_cells=14`).

| Column | Observed type / range | `.bin` field | Meaning | References | Layout tag |
|---|---|---|---|---|---|
| `Name` | str ≤ 11 chars, 7 distinct | `+0x000` `char[32]` | class name `[L]` | — | [C] |
| `Token` | str 2 chars, 7 distinct | `+0x020` 4-byte code, space padded (`AM  `) | `[I]` the class's animation token, the first part of the record name (anim/0001 § 2) | — | [C] |
| — | — | `+0x024` 16 B | zero in every record | — | [C] value |

| Record | `Name` | `Token` |
|---:|---|---|
| 0 | Amazon | AM |
| 4 | Barbarian | BA |
| 6 | Assassin | AI |

## Timing (plan 0050)

The table has no timing column. `[C]` Joined with `animdata.d2`, the 7 tokens × the PlrMode tokens × the 14
`weaponclass.txt` codes name 755 of the 756 records that start with a class token
([PlrMode § Timing](PlrMode.md#timing-plan-0050-phase-0); `python3 -I tools/anim_survey.py players workspace/merged`,
survey keys `plr_*`). `[I]` Under a shape-shift state with `gfxtype` 1 a player is drawn as a monster class instead
(display type 1, the MonStats `Code`), so its record name does not start with a PlrType token (anim/0001 § 2,
fn:UNIT_AnimTransform@0x00645270).

## Open questions

- `[L]` Whether the 16 zero bytes at `+0x024` are filled at load, as for [ObjMode](ObjMode.md#open-questions).
- `[L]` Other readers of the table than the record name (none is read; anim/0001 reads only `0x0065B480`'s use there).
