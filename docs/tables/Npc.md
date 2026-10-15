# Npc (`data/global/excel/npc.txt` → `npc.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 17 (17 `.txt` data rows, no `Expansion` marker)   **Record:** 76 B (`0x4C`)
> **sha256:** `.txt` `912becf632e93306b00e2d1feaa879be8611b4cc6cec8fdad91594482e7e0afd`, `.bin` `b4af470431925d2d5090489f600cf023b3737abdb93a3850c711535f397d9314`
> **Doc status:** layout complete (plan 0031 Phase 0); semantics `[L]`

## Purpose

One row per trading NPC: the monster class it belongs to, three price multipliers (buy, sell, repair), up to three
quest-gated overrides of those multipliers, and a "max buy" amount per difficulty. The column names say these are
the economy side of a vendor: what the NPC charges and what it pays, not what it stocks. Stock comes from the
vendor columns of the item tables ([Weapons § Vendor columns](Weapons.md#vendor-columns-plan-0031-phase-0)), and
gambling from [Gamble](Gamble.md). Reader: `items/vendors` (plan 0031); prices are named only under ADR-0002.
Leads: `src:d2dfg-blizzard` (§ Npc.txt), not yet fetched; nothing here comes from it.

## Row identity

- `[C]` The `.bin` is a u32 record count (17) and 17 records of 76 bytes, one per `.txt` row in order
  ([excel-bin.md](../formats/excel-bin.md)). The loader allocates 76-byte records
  ([data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables), `0x006568DC`).
- `[C]` The key `npc` is a [MonStats](MonStats.md) `Id`, stored as that monstats row index (u32). All 17 resolve, and
  each names the monstats row of the same name: `gheed` 147, `charsi` 154, `akara` 148, `lysander` 202, `drognan`
  177, `elzix` 199, `fara` 178, `hratli` 253, `alkor` 254, `ormus` 255, `asheara` 252, `jamella` 405, `halbu` 257,
  `malah` 513, `drehya` 512, `larzuk` 511, `nihlathak` 514 (`python3 -I tools/vendor_survey.py npc …`).
- `[L]` Whether the game finds a row by scanning for the NPC's monster class (the record holds no other key) or by
  row index is for the reverser.
- `[C]` The rows do not match the 17 vendor column groups of the item tables one to one. 16 rows map to a group by
  name (`hratli` to the `Hralti` group, the item tables' spelling). `nihlathak` has no group, and the `Cain` group has
  no row here.

## Columns

`[C]` layout: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel npc`: 17 records × 19 mapped
fields = 323 cells, **0 mismatches**; every byte of the 76 is a mapped field. Every field is a u32; a blank cell stores
0. A field is `[C]` where the probe (`excel_bin.py probe … npc`) finds exactly one offset that fits its column; the
column order in the record differs from the `.txt` order (sell before buy).

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `npc` | str, 17 distinct, 0 blank | `+0x00` u32 row index | the NPC's monster class `[L]` | [MonStats](MonStats.md) `Id` | [C] |
| `sell mult` | int 960..2048 (4 distinct: 960 `charsi`, 1088 `gheed`, 2048 the four Act V rows, 1024 the rest) | `+0x04` u32 | price multiplier when the NPC sells to the player `[L]` | — | [C] |
| `buy mult` | int, always 512 | `+0x08` u32 | multiplier when the NPC buys from the player `[L]` | — | [C] |
| `rep mult` | int, always 128 | `+0x0C` u32 | repair cost multiplier `[L]` | — | [C] |
| `questflag A` | int {4, 9, 17, 41}: 4 on the three Act I rows, 9 on Act II, 17 on Act III, 41 on Acts IV–V | `+0x10` u32 | a quest whose completion switches on the A multipliers `[L]` | quest numbering not documented | [C] |
| `questflag B` | int 35 on 4 rows (`malah`, `drehya`, `larzuk`, `nihlathak`), 13 blank | `+0x14` u32 | a second quest for the B multipliers `[L]` | — | [C] |
| `questflag C` | always blank | `+0x18` u32 | a third quest `[L]` | — | [C] value 0; slot by the stride `[L]` |
| `questsellmult A` | int, always 922 | `+0x1C` u32 | sell multiplier once quest A is done `[L]` | — | [C] |
| `questsellmult B` | int 512 on the 4 rows with `questflag B`, 13 blank | `+0x20` u32 | sell multiplier once quest B is done `[L]` | — | [C] |
| `questsellmult C` | always blank | `+0x24` u32 | — | — | [C] value 0; slot by the stride `[L]` |
| `questbuymult A`, `questrepmult A` | int, always 1024 (both) | `+0x28` and `+0x34` u32 | buy and repair multipliers once quest A is done `[L]` | — | [C] bytes; which column is which `[L]` (see notes) |
| `questbuymult B`, `questrepmult B` | int 1024 on the 4 rows with `questflag B`, 13 blank (both) | `+0x2C` and `+0x38` u32 | the same for quest B `[L]` | — | [C] bytes; which column is which `[L]` |
| `questbuymult C`, `questrepmult C` | always blank (both) | `+0x30` and `+0x3C` u32 | — | — | [C] value 0; slots by the stride `[L]` |
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
- **`questbuymult` against `questrepmult`.** Both columns hold the same cells (1024 in the A triplet, 1024 or blank
  in the B triplet), so the data cannot say which of the triplets at `+0x28` and `+0x34` is which. The layout puts
  `questbuymult` first, after the order of the base multipliers (sell, buy, rep); a `-txt` compile of an edited
  `npc.txt` with distinct values would settle it (as the plan 0030 compile probe did for CubeMain). `[L]`
- **Group C** is blank in every row. Its three slots (`+0x18`, `+0x24`, `+0x30`/`+0x3C`) follow the 4-byte stride of
  each triplet `[L]`; their bytes are 0 `[C]`.
- **The multipliers look like fixed point over 1024** (1024 = ×1, 512 = ×½, 922 ≈ ×0.9, 2048 = ×2, 128 = ×⅛). `[L]`
- `questflag` values 4, 9, 17, 35 and 41 are not item or level indices; the save's quest word numbering
  ([save/0002](../findings/save/0002-quest-words.md)) is a candidate. `[L]`

## Open questions

- `[L]` How the game finds the Npc row for a vendor unit, what the multipliers and `max buy` do, and how `questflag`
  is tested (which quest numbering, which bit): reverser, plan 0031 Phase 1. Prices are named only (ADR-0002).
- `[L]` Which of `+0x28`/`+0x34` is `questbuymult` and which `questrepmult`; the group C slots. Needs a `-txt` compile
  probe (harness) or the code that reads them ([backlog](../backlog.md)).
- `[L]` Why `nihlathak` has a row but no item vendor column group, and why the `Cain` group has no Npc row.
