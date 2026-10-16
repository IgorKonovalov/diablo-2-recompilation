# Npc (`data/global/excel/npc.txt` → `npc.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 17 (17 `.txt` data rows, no `Expansion` marker)   **Record:** 76 B (`0x4C`)
> **sha256:** `.txt` `912becf632e93306b00e2d1feaa879be8611b4cc6cec8fdad91594482e7e0afd`, `.bin` `b4af470431925d2d5090489f600cf023b3737abdb93a3850c711535f397d9314`
> **Doc status:** layout complete (plan 0031 Phase 0), every slot named by the loader's descriptor; row lookup and quest overrides `[I]` from [items/0009 § 9](../findings/items/0009-vendors.md#9-named-only-prices-and-repair); the price formula and `max buy` named only

## Purpose

One row per trading NPC: the monster class it belongs to, three price multipliers (buy, sell, repair), up to three
quest-gated overrides of those multipliers, and a "max buy" amount per difficulty. The column names say these are
the economy side of a vendor: what the NPC charges and what it pays, not what it stocks. Stock comes from the
vendor columns of the item tables ([Weapons § Vendor columns](Weapons.md#vendor-columns-plan-0031-phase-0)), and
gambling from [Gamble](Gamble.md). Reader: `items/vendors` (plan 0031); prices are named only under ADR-0002.
Leads: `src:d2dfg-blizzard` (§ Npc.txt), not yet fetched; nothing here comes from it.

- `[I]` **Not read on the item-creation path.** Stock building, the stock upgrade and gambling read none of this
  table: the NPC → vendor group map is two switches on the MonStats class, not the `npc` column, and the multiplier,
  quest and `max buy` columns are inputs of the price function (`sub_0062FDC0_ItemTradePrice`), which is named only.
  ([items/0009 § Answer](../findings/items/0009-vendors.md#answer-summary),
  [§ 9](../findings/items/0009-vendors.md#9-named-only-prices-and-repair), fn:sub_0062FDC0_ItemTradePrice@0x0062FDC0,
  tbl:Npc.txt:npc)

## Row identity

- `[C]` The `.bin` is a u32 record count (17) and 17 records of 76 bytes, one per `.txt` row in order
  ([excel-bin.md](../formats/excel-bin.md)). The loader allocates 76-byte records
  ([data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables), `0x006568DC`).
- `[C]` The key `npc` is a [MonStats](MonStats.md) `Id`, stored as that monstats row index (u32). All 17 resolve, and
  each names the monstats row of the same name: `gheed` 147, `charsi` 154, `akara` 148, `lysander` 202, `drognan`
  177, `elzix` 199, `fara` 178, `hratli` 253, `alkor` 254, `ormus` 255, `asheara` 252, `jamella` 405, `halbu` 257,
  `malah` 513, `drehya` 512, `larzuk` 511, `nihlathak` 514 (`python3 -I tools/vendor_survey.py npc …`).
- `[I]` The game finds a row by scanning the records for `+0x00` = the NPC's MonStats class, first match, NULL when
  none: a class with no row gets no multiplier (`sub_00656900_NpcGetByClass`, called from the price function at
  `0x0062FA94`). ([items/0009 § 9](../findings/items/0009-vendors.md#9-named-only-prices-and-repair), fn:sub_00656900_NpcGetByClass@0x00656900)
- `[C]` The rows do not match the 17 vendor column groups of the item tables one to one. 16 rows map to a group by
  name (`hratli` to the `Hralti` group, the item tables' spelling). `nihlathak` has no group, and the `Cain` group has
  no row here.
- `[I]` In the code, Nihlathak (514) has no column group: his store record takes Larzuk's list, and he is not in the
  trade menu's class list, so he only gambles. The `Cain` group (11) is used by no NPC class.
  ([items/0009 § Answer](../findings/items/0009-vendors.md#answer-summary), fn:NPC_MenuAction@0x00579D60)

## Columns

`[C]` layout: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel npc`: 17 records × 19 mapped
fields = 323 cells, **0 mismatches**; every byte of the 76 is a mapped field. Every field is a u32; a blank cell stores
0. The column order in the record differs from the `.txt` order (sell before buy). `[C]` Every slot, including the
ones the data cannot pin (the `questbuymult`/`questrepmult` triplets, group C), is named by the loader's descriptor
(`sub_00656620_NpcLoadTable`, `0x006567B0`–`0x00656866`) and corroborated by the price code, which applies
`+0x28 + 4k` to the value `buy mult` scales and `+0x34 + 4k` to the one `rep mult` scales ([items/0009 § 9](../findings/items/0009-vendors.md#9-named-only-prices-and-repair),
fn:sub_00656620_NpcLoadTable@0x00656620).

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `npc` | str, 17 distinct, 0 blank | `+0x00` u32 row index | the NPC's monster class: the key `NpcGetByClass` scans for `[I]` | [MonStats](MonStats.md) `Id` | [C] |
| `sell mult` | int 960..2048 (4 distinct: 960 `charsi`, 1088 `gheed`, 2048 the four Act V rows, 1024 the rest) | `+0x04` u32 | first of the three running values the price function scales (`v · m / 1024`) `[I]`; that it is the NPC-sells price `[L]` | — | [C] |
| `buy mult` | int, always 512 | `+0x08` u32 | second running value's multiplier `[I]`; the NPC-buys price `[L]` | — | [C] |
| `rep mult` | int, always 128 | `+0x0C` u32 | third running value's multiplier `[I]`; the repair cost `[L]` | — | [C] |
| `questflag A` | int {4, 9, 17, 41}: 4 on the three Act I rows, 9 on Act II, 17 on Act III, 41 on Acts IV–V | `+0x10` u32 | a quest record **word** (save/0002 numbering): with bit 0 (done) or bit 1 (reward pending) of it set, the A multipliers apply `[I]` | [save/0002](../findings/save/0002-quest-words.md) words | [C] |
| `questflag B` | int 35 on 4 rows (`malah`, `drehya`, `larzuk`, `nihlathak`), 13 blank | `+0x14` u32 | the same for the B multipliers (word 35) `[I]` | — | [C] |
| `questflag C` | always blank | `+0x18` u32 | the same for C; 0 = no override `[I]` | — | [C] |
| `questsellmult A` | int, always 922 | `+0x1C` u32 | scales the first value again when quest A's test holds `[I]` | — | [C] |
| `questsellmult B` | int 512 on the 4 rows with `questflag B`, 13 blank | `+0x20` u32 | the same for quest B `[I]` | — | [C] |
| `questsellmult C` | always blank | `+0x24` u32 | the same for C `[I]` | — | [C] |
| `questbuymult A`, `questrepmult A` | int, always 1024 (both) | `questbuymult` `+0x28`, `questrepmult` `+0x34` u32 | scale the second and third values when quest A's test holds `[I]` | — | [C] (descriptor, see notes) |
| `questbuymult B`, `questrepmult B` | int 1024 on the 4 rows with `questflag B`, 13 blank (both) | `+0x2C`, `+0x38` u32 | the same for quest B `[I]` | — | [C] |
| `questbuymult C`, `questrepmult C` | always blank (both) | `+0x30`, `+0x3C` u32 | the same for C `[I]` | — | [C] |
| `max buy` | int 5000..25000: 5000 on Act I rows, 10000 Act II, 15000 Act III, 20000 Act IV (`jamella`, `halbu`), 25000 Act V | `+0x40` u32 | most gold the NPC pays for one item in normal `[L]` | — | [C] |
| `max buy (N)` | int, always 30000 | `+0x44` u32 | the same in nightmare `[L]` | — | [C] |
| `max buy (H)` | int, always 35000 | `+0x48` u32 | the same in hell `[L]` | — | [C] |

The act grouping in the ranges above is by the NPC's town (`[L]`, from the names); it is exact in the data: every
row of one `questflag A` value has the same `max buy`, except `jamella` and `halbu` (`questflag A` 41, `max buy`
20000) against the Act V rows (41, 25000).

## Interpretation notes

- **Record order.** The record keeps each kind of column together: the three base multipliers (sell, buy, rep),
  then `questflag A..C`, `questsellmult A..C`, two more triplets, and `max buy` for the three difficulties.
  `[C]` for every slot whose column has a value that pins it.
- `[C]` **`questbuymult` against `questrepmult`.** Both columns hold the same cells, so the data alone cannot place
  them; the loader's descriptor does: `questbuymult A..C` at `+0x28/+0x2C/+0x30`, `questrepmult A..C` at
  `+0x34/+0x38/+0x3C`, and the price code applies the first triplet with `buy mult` and the second with `rep mult`
  ([items/0009 § 9](../findings/items/0009-vendors.md#9-named-only-prices-and-repair), fn:sub_00656620_NpcLoadTable@0x00656620).
- `[C]` **Group C** is blank in every row; the descriptor places its slots at `+0x18`, `+0x24`, `+0x30` and `+0x3C`
  (same anchor). A `questflag` of 0 skips the group `[I]`.
- `[I]` **The multipliers are fixed point over 1024.** Each scaling is `v · m / 1024` truncated toward zero, or
  `(v / 1024) · m` when `v ≥ 0x10000` and `m ≠ 0`; the base multipliers apply first, then groups A, B, C in order.
  ([items/0009 § 9](../findings/items/0009-vendors.md#9-named-only-prices-and-repair), fn:sub_0062FDC0_ItemTradePrice@0x0062FDC0)
- `[I]` **`questflag` is a quest record word** in the save's numbering ([save/0002](../findings/save/0002-quest-words.md)):
  4, 9, 17, 35, 41. The group applies when `QUESTRECORD_GetState(rec, questflag, 0)` or `(…, 1)` is 1, i.e. the quest
  is done or done with the reward pending. ([items/0009 § 9](../findings/items/0009-vendors.md#9-named-only-prices-and-repair), fn:QUESTRECORD_GetState@0x0065C310)

## Open questions

- Answered by [items/0009 § 9](../findings/items/0009-vendors.md#9-named-only-prices-and-repair): the row lookup (by MonStats class), the `questflag` test (quest record word, bit 0 or 1),
  the order and arithmetic of the scalings, and which triplet is `questbuymult` (above).
- `[L]` What the three running values are before the scaling (the item's base price), which one is the sell, buy or
  repair price in the trade screens, and what `max buy` does: the price function is named only (ADR-0002).
- Answered `[I]`: `nihlathak` has a row but no column group because he only gambles (his record borrows Larzuk's
  list, never shown); the `Cain` group is unused by any class (Row identity). Why the data keeps either is not a code
  question.
