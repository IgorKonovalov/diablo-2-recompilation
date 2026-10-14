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
  (1,0,1), (1,1,1) in file order. How the game picks a row: see *Row selection* below.

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

## Fields the quality roll reads (plan 0010 Phase 0)

Every column of the record is laid out (`excel_bin.py diff`: 6 records × 19 fields = 114 cells,
0 mismatches). The operands of the quality roll ([items/0002](../findings/items/0002-quality-roll.md) §2–§6; the quality codes in
[§ Answer](../findings/items/0002-quality-roll.md#answer-summary))
map to columns as follows; the arithmetic and the row choice are the finding's (`[I]` there,
plan 0010 Phase 1), not claims of this doc.

| Roll operand | Columns (offset) |
|---|---|
| row key of `ITEMRATIO_Select`: version, uber, class-specific | `Version` (`+0x40`), `Uber` (`+0x42`), `Class Specific` (`+0x43`) |
| unique test: base, divisor, minimum | `Unique` (`+0x00`), `UniqueDivisor` (`+0x04`), `UniqueMin` (`+0x08`) |
| set test | `Set` (`+0x18`), `SetDivisor` (`+0x1C`), `SetMin` (`+0x20`) |
| rare test | `Rare` (`+0x0C`), `RareDivisor` (`+0x10`), `RareMin` (`+0x14`) |
| magic test | `Magic` (`+0x24`), `MagicDivisor` (`+0x28`), `MagicMin` (`+0x2C`) |
| superior test | `HiQuality` (`+0x30`), `HiQualityDivisor` (`+0x34`); **no column** for a minimum |
| normal/low test | `Normal` (`+0x38`), `NormalDivisor` (`+0x3C`); **no column** for a minimum |
| the frame's ratio words (`chance × ratio / 1024`) | **no column** here: `TreasureClassEx` `Unique`/`Set`/`Rare`/`Magic` ([TreasureClassEx](TreasureClassEx.md)) |
| `ilvl`, `qlvl` | **no column** here: the source's level and the item's `level` ([Weapons](Weapons.md#fields-the-quality-roll-reads-plan-0010-phase-0)) |

- `[C]` In the `Version` 1 rows the `Uber` flag changes nothing: rows (1,0,0) and (1,1,0) hold the same
  16 values, and so do (1,0,1) and (1,1,1). Only the two `Version` 0 rows differ by `Uber` (`Unique` 400 vs
  240, `Rare` 160 vs 96, `Set` 125 vs 96, …). (tbl:ItemRatio.txt:Uber)

### Row selection (from items/0002)

- `[I]` `ITEMRATIO_Select(item, diff, version)` keeps the rows whose `Class Specific` equals "the item's own
  `type` has itemtypes `Class` < 7" and whose `Uber` equals "the item is a `weap`/`armo` whose `ubercode` or
  `ultracode` is its own `code`, not `tpot`, not a quest item", with `Version` ≤ the argument; the highest
  `Version` wins, the later row on a tie; no match is fatal. The `diff` argument is not read.
  (fn:ITEMRATIO_Select@0x00637910, fn:ITEMS_IsClassSpecific@0x00629F70, fn:sub_0062B4D0_ItemRatioUber@0x0062B4D0, [items/0002 §2](../findings/items/0002-quality-roll.md#2-row-selection--itemratio_select-0x00637910))
- `[I]` **The drop roll always passes 100**, in classic games too, so a drop uses records 2–5 (the
  `Version` 1 rows) only. Combined with the identical pairs above: with stock data **a drop's row depends
  on the class-specific key only**, and the `Uber` key changes no drop. The `Version` 0 rows are reachable only
  with the argument 0, which only the creation-side roll passes. (fn:ITEMS_DropRollQuality@0x00558640, [items/0002 §2](../findings/items/0002-quality-roll.md#2-row-selection--itemratio_select-0x00637910))
- `[C]` Data side of those keys: by that rule 328 bases are uber (194 weapons, 134 armor, no misc) and 111
  are class-specific (51 weapons, 60 armor). (tbl:Weapons.txt:ubercode, tbl:ItemTypes.txt:Class)
- `[I]` Arithmetic (items/0002 §3–6): each `X`/`XDivisor` pair gives `(X − (ilvl − qlvl) / XDivisor) × 128`;
  `UniqueMin`, `SetMin`, `RareMin`, `MagicMin` are lower bounds applied after magic find; `HiQuality` and `Normal`
  have no minimum, magic find or ratio. ([items/0002](../findings/items/0002-quality-roll.md#answer-summary))
- `[C]` The older copy in the `d2exp` archive has 52-byte records and no `*Min` columns (12 u32, then
  `Version` u16 and the two key bytes); its ratios differ (`Unique` 1000, `UniqueDivisor` 6 in the first row). The game
  loads the `patch_d2` copy ([data/0002](../findings/data/0002-mpq-precedence.md)). (tbl:ItemRatio.txt:UniqueMin)

## Open questions

- Answered `[I]`: row selection and the arithmetic, see *Row selection* ([items/0002](../findings/items/0002-quality-roll.md)).
  Still open: classic and creation-side use of the `Version` 0 rows is not observed (no classic run; plan 0010 Phase 2).
