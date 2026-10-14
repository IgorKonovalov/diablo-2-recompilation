# Shrines (`data/global/excel/shrines.txt` → `shrines.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 23 (no `Expansion` marker)   **Record:** 184 B (`0xB8`)
> **sha256:** `.txt` `1dae6107c983c5e03079ac6916cf77a3d828df4b2a0517818504dcf20a68fb6d`, `.bin` `2a7e6f8f0cc8c8743f4d7971c31b80c3083cef846ff8100598944c71b0ab0678`
> **Doc status:** complete for layout (every byte placed); semantics `[L]` (plan 0023 Phase 1 reads the shrine pick)

## Purpose

One row per shrine effect: `Refill`, `Health Boost`, `Armor Boost`, `Experience Boost`, `Gem Upgrade`, `Exploding
Shrine`, … (row 0 is `None`). A row gives the effect's two arguments, its duration, the time before the shrine can be
used again, a `rarity` and a minimum level. The shrine objects (Objects `SubClass` bit 0, [Objects](Objects.md)) are
created with one of these effects. How the effect is picked (`rarity`, `LevelMin`, difficulty) is plan
[0023](../plans/0023-objects.md) Phase 1; what the effect does is game simulation (ADR-0002) and is only named. Leads:
no lead read (`src:d2dfg-blizzard` § Shrines is for Phase 1b).

## Row identity

- `[C]` The `.bin` is a u32 record count (23) and 23 records of 184 bytes, one per `.txt` row in order. The loader passes
  record size 184 (0x00641493, [data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables)).
- `[C]` `Code` equals the row index in all 23 rows (`SURVEY obj_shrines … code_is_index=23`). `[L]` it is the effect
  number the shrine object stores.

## Columns

`[C]` layout: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel shrines`: 23 records × 10 mapped
fields = 230 cells, **0 mismatches**; `excel_bin.py unknown … shrines` lists only `+0x0B3` (1 B, zero in every record).
Values from `python3 -I tools/obj_survey.py shrines workspace/merged/data/global/excel`. No blank cell.

| Column | Observed type / range | `.bin` field | Meaning (`[L]` unless stated) | References | Layout tag |
|---|---|---|---|---|---|
| `Shrine Type` | str {Booster 10, Magic 7, Recharge 5, None 1} | — | editor grouping | — | [C] |
| `Shrine name` | str, 23 distinct | — | editor name | — | [C] |
| `Effect` | str, 23 distinct | — | editor description | — | [C] |
| `Code` | int 0..22 = row index | `+0x000` u32 | effect number | — | [C] |
| `Arg0` | int 0..400 (8 distinct) | `+0x004` s32 | first effect argument | — | [C] |
| `Arg1` | int 0..2000 (9 distinct) | `+0x008` s32 | second effect argument | — | [C] |
| `Duration in frames` | int {0: 13, 3600: 5, 2400: 4, 4800: 1} | `+0x00C` u32 | effect duration (25 frames per second: 2400 = 96 s) | — | [C] |
| `reset time in minutes` | int {5: 11, 0: 10, 2: 2} | `+0x010` u8 | time before the shrine can be used again (0 = once) | — | [C] |
| `rarity` | int {2: 12, 3: 9, 1: 2} | `+0x011` u8 | weight or class of the effect in the shrine pick | — | [C] |
| `view name` | str `blah` in every row | `+0x012` `char[32]` | unused text | — | [C] (width by next field) |
| `niftyphrase` | str `blah` in every row | `+0x032` `char[128]` | unused text | — | [C] (width by next field) |
| `effectclass` | int {4: 11, 1: 7, 2: 2, 3: 2, 0: 1} | `+0x0B2` u8 | effect class; `[C]` by data it follows `Shrine Type`: Booster → 4, Magic → 1, None → 0, Recharge → 2 (Health Boost, Health Exchange), 3 (Mana Boost, Mana Exchange) or 4 (Refill) | — | [C] |
| — | — | `+0x0B3` u8 | zero in every record | — | [C] value |
| `LevelMin` | int 0..32 (1: 11) | `+0x0B4` u32 | lowest level (area level or character level, unknown) at which the effect can appear | — | [C] |

`[C]` `view name` and `niftyphrase` hold the same value in every row, so `probe` places them only as a pair at
`+0x012`/`+0x032`; the order follows the `.txt`, and the widths follow from the next field. `effectclass` is placed as a
u8; a u16 at `+0x0B2` would decode the same values (`+0x0B3` is 0 everywhere).

## The 23 effects

Short form of the survey (`tools/obj_survey.py shrines`), for orientation; effect names are the `.txt` editor names.

| `Code` | Name | `Arg0` | `Arg1` | Duration | reset | `rarity` | `effectclass` | `LevelMin` |
|---|---|---|---|---|---|---|---|---|
| 0 | None | 100 | 100 | 0 | 2 | 1 | 0 | 0 |
| 1 | Refill | 100 | 100 | 0 | 2 | 1 | 4 | 1 |
| 2 | Health Boost | 200 | 400 | 0 | 5 | 2 | 2 | 1 |
| 6 | Armor Boost | 100 | 1 | 2400 | 5 | 2 | 4 | 5 |
| 9 | Resist Cold Boost | 75 | 0 | 3600 | 5 | 2 | 4 | 26 |
| 15 | Experience Boost | 50 | 50 | 3600 | 0 | 3 | 4 | 1 |
| 18 | Gem Upgrade | 0 | 0 | 0 | 0 | 3 | 1 | 4 |

- `[C]` `rarity` sums to 53 over the 23 rows (1 on rows 0 and 1, 3 on rows 4, 5, 14–16, 18, 20–22, else 2).
- `[C]` `LevelMin` is above 8 only for the three resist boosts other than fire: cold 26, poison 21, lightning 32.

## Interpretation notes

- `[L]` A shrine object's effect is likely picked when the object is created, weighted by `rarity` and filtered by
  `LevelMin`; the Objects shrine rows (`PopulateFn` 2, `InitFn` 1) and their `Parm0` ∈ {1, 2, 3} may restrict the
  candidates (e.g. by `effectclass`). Phase 1 reads the init handler and states the draw.

## Open questions

- `[L]` Which level `LevelMin` compares against, how `rarity` enters the pick, and whether row 0 (`None`) can be picked.
  Reverser, plan 0023 Phase 1.
- `[L]` Whether `effectclass` or Objects `Parm0` restricts the pick per shrine object.
