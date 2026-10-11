# ItemRatio (`data/global/excel/itemratio.txt`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 6   **Record:** 68 B
> **sha256:** `.txt` `f8ebb2128c09311d2f17f9f3ea9e1933441f3322ab2c4c203eb9858a00af90ff`, `.bin` `9285afeda0b7de64ba57ee755b869932cb57f8c245e1a37ee56debf37088b0b1`
> **Doc status:** columns listed, `.bin` layout complete, semantics pending

## Purpose

Six rows of quality-roll ratios (unique, rare, set, magic, high quality, normal, each with a divisor
and most with a minimum), selected by the `Version`, `Uber` and `Class Specific` flags. Read by item
quality rolls (`items/quality`).

## Row identity

- `[C]` No key column is compiled: `Function` is a description and is not in the record. Rows are
  distinguished only by (`Version`, `Uber`, `Class Specific`): (0,0,0), (0,1,0), (1,0,0), (1,1,0),
  (1,0,1), (1,1,1) in file order. How the game picks a row is a code question.

## Columns

`[C]` layout tags are by data behaviour: `python3 -I tools/excel_bin.py diff <excel-dir> itemratio` decodes every record and compares it with every mapped cell (blank cells and encoding rules as in [excel-bin.md](../formats/excel-bin.md#cell-encoding-rules)). A field is tagged `[C]` when the column's values pin its offset (a probe over every record finds no other offset that fits), `[I]` when the column is constant or identical to a sibling column, so its position comes from the neighbouring fields or the stride of its group. Widths are `[C]` with the same proviso; signedness is `[I]` (`s` where the column holds negative values). **Meaning:** no column semantics are claimed here; they come from reverser findings.

| Column | Observed type / range | `.bin` field | References | Layout tag |
|---|---|---|---|---|
| `Function` | str, 4 distinct, len ≤ 39 | — (comment column (row description); no bytes in the record) | — | — |
| `Version` | int 0..1 (2 distinct) | `+0x040` u16 | — | [C] |
| `Uber` | int 0..1 (2 distinct) | `+0x042` u8 | — | [C] |
| `Class Specific` | int 0..1 (2 distinct) | `+0x043` u8 | — | [C] |
| `Unique` | int 240..400 (2 distinct) | `+0x000` u32 | — | [C] |
| `UniqueDivisor` | int 1..3 (3 distinct) | `+0x004` u32 | — | [C] |
| `UniqueMin` | int, always 6400 | `+0x008` u32 | — | [I] |
| `Rare` | int 80..160 (4 distinct) | `+0x00C` u32 | — | [C] |
| `RareDivisor` | int 2..3 (2 distinct) | `+0x010` u32 | — | [C] |
| `RareMin` | int, always 3200 | `+0x014` u32 | — | [I] |
| `Set` | int 96..160 (4 distinct) | `+0x018` u32 | — | [C] |
| `SetDivisor` | int 2..6 (3 distinct) | `+0x01C` u32 | — | [C] |
| `SetMin` | int, always 5600 | `+0x020` u32 | — | [I] |
| `Magic` | int 3..34 (4 distinct) | `+0x024` u32 | — | [C] |
| `MagicDivisor` | int 3..100 (4 distinct) | `+0x028` u32 | — | [C] |
| `MagicMin` | int, always 192 | `+0x02C` u32 | — | [I] |
| `HiQuality` | int 4..12 (3 distinct) | `+0x030` u32 | — | [C] |
| `HiQualityDivisor` | int 8..16 (2 distinct) | `+0x034` u32 | — | [C] |
| `Normal` | int 1..4 (3 distinct) | `+0x038` u32 | — | [C] |
| `NormalDivisor` | int 1..8 (3 distinct) | `+0x03C` u32 | — | [C] |

`UniqueMin`, `RareMin`, `SetMin`, `MagicMin` are constant (6400, 3200, 5600, 192), so their offsets
are `[I]`: they sit in the only free u32 slot of each ratio/divisor/min triple.

## Record layout (68 bytes)

Sixteen u32 in column order from `+0x00` (`Unique`, `UniqueDivisor`, `UniqueMin`, … `Normal`,
`NormalDivisor`), then `Version` u16 at `+0x40`, `Uber` u8 at `+0x42`, `Class Specific` u8 at `+0x43`.
No unknown bytes.

## Open questions

- `[L]` Row selection by version / uber / class-specific, and the integer arithmetic of the ratio
  (plan 0004 / `items/quality`).
