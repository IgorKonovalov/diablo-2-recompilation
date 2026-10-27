# Books (`data/global/excel/books.txt` → `books.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 3 (no `Expansion` marker)   **Record:** 32 B (`0x20`)
> **sha256:** `.txt` `60e2527c2b30487ff68fcaaad163831abc6f6ef5e4ec6d42478ff5f30c2eeec5`, `.bin` `1f50356b5340ecfd894a10b5a17ece4551a48dc5b67edc4076cc8e6f998eb83b`
> **Doc status:** layout complete (plan 0043 Phase 0); readers and widths from [items/0011](../findings/items/0011-economy.md) (plan 0043 Phase 1): `CostPerCharge` prices a tome, `BaseCost` has no reader; the other meanings `[L]`

## Purpose

One row per tome: the scroll and book item codes of Town Portal and Identify, the skills they cast, and two price
columns, `BaseCost` and `CostPerCharge`. The column names say the price of a tome is a base plus a price per scroll
held. Reader: the price function of `items/economy` (plan 0043 Phase 1, § Interpretation notes). Leads: `src:d2dfg-blizzard`
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
| `ScrollSpellCode` | str {`tsc`, `isc`}, 1 blank | `+0x018` char[4] code | the scroll's item code `[L]`; `[I]` matched by the code match at 0x005C2540 through the table pointer ([items/0011 § Phase 0 surprises](../findings/items/0011-economy.md#phase-0-surprises-and-the-reviews-inputs-answered)) | [Misc](Misc.md) `code` | [C] |
| `BookSpellCode` | str {`tbk`, `ibk`}, 1 blank | `+0x01C` char[4] code | the tome's item code `[L]`; `[I]` matched as `ScrollSpellCode` | [Misc](Misc.md) `code` | [C] |
| `pSpell` | int {2, 1, 0} | `+0x004` s32 | the `pSpell` of the misc rows (`tsc`/`tbk` 2, `isc`/`ibk` 1) `[L]`; `[I]` read 32-bit signed (`jg`, 0x005BF2AF, [items/0011 § Phase 0 surprises](../findings/items/0011-economy.md#phase-0-surprises-and-the-reviews-inputs-answered)) | [Misc](Misc.md) `pSpell` | [C] offset; width [I] |
| `SpellIcon` | int {−1, 0, −1} | `+0x002` s8 | icon index `[L]`; `[I]` read as a byte (0x0062BBBB, [items/0011 § Phase 0 surprises](../findings/items/0011-economy.md#phase-0-surprises-and-the-reviews-inputs-answered)) | — | [C] offset; width [I] |
| `ScrollSkill` | str {`Scroll of Townportal`, `Scroll of Identify`}, 1 blank | `+0x008` s32 Skills row (219, 217; blank −1) | the skill a scroll casts `[L]`; *plan 0046 readers:* `[C]` skill do 113 takes an item of type 22 (`scro`) whose suffix's Books row has `ScrollSkill` equal to the skill, with no quantity test (ADR-0021, up to the use call) ([skills/0015 § 4](../findings/skills/0015-item.md#4-do-113-and-do-151); fn:sub_005BF3D0_SkillDo113UseBookScroll@0x005BF3D0) | [Skills](Skills.md) `skill` | [C] offset |
| `BookSkill` | str {`Book of Townportal`, `Book of Identify`}, 1 blank | `+0x00C` s32 Skills row (220, 218; blank −1) | the skill a tome casts `[L]`; *plan 0046 readers:* `[C]` skill do 113 takes an item of type 18 (`book`) whose suffix's Books row has `BookSkill` equal to the skill and whose stat 70 is above 0 (ADR-0021) ([skills/0015 § 4](../findings/skills/0015-item.md#4-do-113-and-do-151)) | [Skills](Skills.md) `skill` | [C] offset |
| `BaseCost` | int {250, 200, 500} | `+0x010` u32 | `[I]` no reader: none of the 10 call sites of `BOOKS_GetRecord` and 6 table references reads `+0x010` ([items/0011 § Phase 0 surprises](../findings/items/0011-economy.md#phase-0-surprises-and-the-reviews-inputs-answered)); the tome's base is its Misc `cost` | — | [C] offset |
| `CostPerCharge` | int {50, 40, 100} | `+0x014` u32 | `[I]` price per scroll held: a tome's base price is `CostPerCharge × q + Misc cost`, read 32-bit (`imul`) ([items/0011 § 1](../findings/items/0011-economy.md#1-the-price-core-inputs-and-the-base)) | — | [C] offset; width [I] (32-bit) |

## Interpretation notes

- `[C]` **`BaseCost` equals the tome's Misc `cost`**: `tbk` 250, `ibk` 200 (Misc `+0x0E0`). The scrolls cost
  `tsc` 100 and `isc` 80 in Misc, so `CostPerCharge` (50, 40) is not the scroll's own `cost`; it is a fifth of
  `BaseCost` in all three rows (`books_cost_per_charge_is_fifth` 3).
- `[I]` **The tome price reads `CostPerCharge` and the Misc `cost`, not `BaseCost`.** For an item of type 18 (book),
  `ITEMS_TradePriceCore` starts the buy and sell values at `Books[suffix0].CostPerCharge × q + base.cost`, with `q` =
  max(1, stat 70 quantity), the scrolls the tome holds; a missing Books row is fatal; the repair value starts at 0.
  The Npc, quest and quantity steps follow as for any item. So `tbk` with 20 scrolls is 50 × 20 + 250 before the Npc
  multiplier. ([items/0011 § 1](../findings/items/0011-economy.md#1-the-price-core-inputs-and-the-base), fn:ITEMS_TradePriceCore@0x0062EFB0 0x0062F2A2, fn:BOOKS_GetRecord@0x006374B0,
  tbl:Books.txt:CostPerCharge)
- `[C]` The third row (`of Ressurect`) has no codes and no skills; no item can name it by code.

## Open questions

- ~~Whether the game reads this table outside the loader~~: the price reads `+0x014`, the item code match reads
  the codes, `+0x02` and `+0x04` are read; `+0x010` has no reader at the 10 call sites and 6 table references `[I]`
  ([items/0011 § Phase 0 surprises](../findings/items/0011-economy.md#phase-0-surprises-and-the-reviews-inputs-answered)). `[L]` What the code match at 0x005C2540, the `SpellIcon` byte and the skills do beyond the price.
- `[L]` The sign of `CostPerCharge` and `BaseCost` (32-bit; any integer width fits three rows).
