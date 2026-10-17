# Books (`data/global/excel/books.txt` → `books.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 3 (no `Expansion` marker)   **Record:** 32 B (`0x20`)
> **sha256:** `.txt` `60e2527c2b30487ff68fcaaad163831abc6f6ef5e4ec6d42478ff5f30c2eeec5`, `.bin` `1f50356b5340ecfd894a10b5a17ece4551a48dc5b67edc4076cc8e6f998eb83b`
> **Doc status:** layout complete (plan 0043 Phase 0); no reader named, every meaning `[L]`

## Purpose

One row per tome: the scroll and book item codes of Town Portal and Identify, the skills they cast, and two price
columns, `BaseCost` and `CostPerCharge`. The column names say the price of a tome is a base plus a price per scroll
held. Reader expected: the price function of `items/economy` (plan 0043 Phase 1). Leads: `src:d2dfg-blizzard`
(§ Books.txt), not fetched; nothing here comes from it.

## Row identity

- `[C]` The `.bin` is a u32 record count (3) and 3 records of 32 bytes, one per `.txt` row in order
  ([excel-bin.md](../formats/excel-bin.md)). The loader allocates 32-byte records
  ([data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables), `0x00637475`).
- `[C]` Rows: 0 `of Town Portal` (`tsc`/`tbk`), 1 `of Identify` (`isc`/`ibk`), 2 `of Ressurect` (no codes, no skills).
  The `Name` cell is `unused` in all three; the rows are told apart by position and by their codes.

## Columns

`[C]` layout: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel books`: 3 records × 9 mapped
fields = 27 cells, **0 mismatches**; `+0x003` is the only byte with no column (0 in every record). With three rows,
`excel_bin.py probe` pins each offset, but not each width: the four-byte slots fit any integer width from the offset,
so the widths are the slot sizes (`[I]`, by stride). `python3 -I tools/economy_survey.py books …` prints the rows.

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `Name` | str, always `unused` | `+0x000` u16 string index (5385) | editor name `[L]` | string tables | [C] |
| `Namco` | str, 3 distinct (`of Town Portal`, `of Identify`, `of Ressurect`) | — (not compiled; none of the three is a string-table key) | display suffix `[L]` | — | [C] (no field) |
| `Completed` | int {1, 1, 0} | — (not compiled: no byte or bit follows it) | editor flag `[L]` | — | [C] (no field) |
| `ScrollSpellCode` | str {`tsc`, `isc`}, 1 blank | `+0x018` char[4] code | the scroll's item code `[L]` | [Misc](Misc.md) `code` | [C] |
| `BookSpellCode` | str {`tbk`, `ibk`}, 1 blank | `+0x01C` char[4] code | the tome's item code `[L]` | [Misc](Misc.md) `code` | [C] |
| `pSpell` | int {2, 1, 0} | `+0x004` u32 | the `pSpell` of the misc rows (`tsc`/`tbk` 2, `isc`/`ibk` 1) `[L]` | [Misc](Misc.md) `pSpell` | [C] offset |
| `SpellIcon` | int {−1, 0, −1} | `+0x002` s8 | icon index `[L]` | — | [C] offset |
| `ScrollSkill` | str {`Scroll of Townportal`, `Scroll of Identify`}, 1 blank | `+0x008` s32 Skills row (219, 217; blank −1) | the skill a scroll casts `[L]` | [Skills](Skills.md) `skill` | [C] offset |
| `BookSkill` | str {`Book of Townportal`, `Book of Identify`}, 1 blank | `+0x00C` s32 Skills row (220, 218; blank −1) | the skill a tome casts `[L]` | [Skills](Skills.md) `skill` | [C] offset |
| `BaseCost` | int {250, 200, 500} | `+0x010` u32 | price base of the tome `[L]` | — | [C] offset |
| `CostPerCharge` | int {50, 40, 100} | `+0x014` u32 | price per scroll held `[L]` | — | [C] offset |

## Interpretation notes

- `[C]` **`BaseCost` equals the tome's Misc `cost`**: `tbk` 250, `ibk` 200 (Misc `+0x0E0`). The scrolls cost
  `tsc` 100 and `isc` 80 in Misc, so `CostPerCharge` (50, 40) is not the scroll's own `cost`; it is a fifth of
  `BaseCost` in all three rows (`books_cost_per_charge_is_fifth` 3). Data only: which of `BaseCost` or the Misc `cost`
  the price reads, and how the charges (the tome's quantity, Misc `maxstack` 20) enter, is for Phase 1 `[L]`.
- `[C]` The third row (`of Ressurect`) has no codes and no skills; no item can name it by code.

## Open questions

- `[L]` Whether the game reads this table at all outside the loader, and what for (the tome price, the scroll →
  tome code link, the skills). No function that reads `+0x010` or `+0x014` is named. Plan 0043 Phase 1.
- `[L]` The widths of `pSpell`, `BaseCost` and `CostPerCharge` (any integer width at their offsets fits three rows).
