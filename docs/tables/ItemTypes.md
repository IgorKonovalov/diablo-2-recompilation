# ItemTypes (`data/global/excel/itemtypes.txt`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 103 (104 data rows − 1 `Expansion` marker at row 58)   **Record:** 228 B
> **sha256:** `.txt` `d399dc5d0f3a3e1a4f1eb611dabef8311b7025392c416f58dc26baff93af3550`, `.bin` `233068c5ff96101cd9c460ddf6b7274286e4bd7967dc8168ddda80c3908826b3`
> **Doc status:** columns listed, `.bin` layout complete, semantics pending except [§ Fields the base-stat roll reads](#fields-the-base-stat-roll-reads-plan-0024-phase-1) (`[I]`, plan 0024 Phase 1)

## Purpose

The item-type hierarchy: each row is a type code (`axe`, `weap`, `armo`…) with up to two parent
types (`Equiv1/2`), body locations, socket limits, the flag that makes it a TC-generating type, and
inventory graphics. Item rows (`weapons`/`armor`/`misc` `type`, `type2`) and affix rows (`itype*`,
`etype*`) point here. Read by `items/tc`, `items/quality`, `items/affixes`.

## Row identity

- `[C]` Key column `Code`, a 4-character code. Five rows have an **empty** code: rows 0 and 1
  (`None`) and rows 14, 17, 23 (`Not Used`). The other 98 codes are distinct.
- `[C]` References store the **record index** of the first row with that code (u16 in item, affix and
  rare-affix records; u16 for `Equiv1/2`, `Shoots`, `Quiver` here). A blank reference cell is looked
  up like any key and finds row 0 (`None`), so it stores **0**; a column missing from a `.txt` stores
  `0xFFFF`. Codes are cut to 4 characters before the lookup (`staff` → `staf`).
- `[C]` The `Expansion` marker after data row 57 takes no record: types after it are one lower.

## Columns

`[C]` layout tags are by data behaviour: `python3 -I tools/excel_bin.py diff <excel-dir> itemtypes` decodes every record and compares it with every mapped cell (blank cells and encoding rules as in [excel-bin.md](../formats/excel-bin.md#cell-encoding-rules)). A field is tagged `[C]` when the column's values pin its offset (a probe over every record finds no other offset that fits), `[I]` when the column is constant or identical to a sibling column, so its position comes from the neighbouring fields or the stride of its group. Widths are `[C]` with the same proviso; signedness is `[I]` (`s` where the column holds negative values). **Meaning:** no column semantics are claimed here; they come from reverser findings.

| Column | Observed type / range | `.bin` field | References | Layout tag |
|---|---|---|---|---|
| `ItemType` | str, 100 distinct, len ≤ 16 | — (display name for editors; not in the record (rows are addressed by Code / index)) | — | — |
| `Code` | str, 98 distinct, len ≤ 4, 5 blank | `+0x000` char[4] code | — | [C] |
| `Equiv1` | str, 25 distinct, len ≤ 4, 11 blank | `+0x004` u16 index | `itemtypes:Code` | [C] |
| `Equiv2` | str, 13 distinct, len ≤ 4, 87 blank | `+0x006` u16 index | `itemtypes:Code` | [C] |
| `Repair` | int 0..1 (2 distinct) | `+0x008` u8 | — | [C] |
| `Body` | int 0..1 (2 distinct) | `+0x009` u8 | — | [C] |
| `BodyLoc1` | str, 8 distinct, len ≤ 4, 62 blank | `+0x00A` u8 index | `bodylocs:Code` | [C] |
| `BodyLoc2` | str, 8 distinct, len ≤ 4, 62 blank | `+0x00B` u8 index | `bodylocs:Code` | [C] |
| `Shoots` | str, 2 distinct, len ≤ 4, 100 blank | `+0x00C` u16 index | `itemtypes:Code` | [C] |
| `Quiver` | str, 2 distinct, len ≤ 4, 99 blank | `+0x00E` u16 index | `itemtypes:Code` | [C] |
| `Throwable` | int 0..1 (2 distinct) | `+0x010` u8 | — | [C] |
| `Reload` | int 0..1 (2 distinct) | `+0x011` u8 | — | [C] |
| `ReEquip` | int 0..1 (2 distinct) | `+0x012` u8 | — | [C] |
| `AutoStack` | int 0..1 (2 distinct) | `+0x013` u8 | — | [C] |
| `Magic` | int, always 1, 94 blank | `+0x014` u8 | — | [C] |
| `Rare` | int, always 1, 45 blank | `+0x015` u8 | — | [C] |
| `Normal` | int 0..1 (2 distinct) | `+0x016` u8 | — | [C] |
| `Charm` | int 0..1 (2 distinct) | `+0x017` u8 | — | [C] |
| `Gem` | int 0..1 (2 distinct) | `+0x018` u8 | — | [C] |
| `Beltable` | int 0..1 (2 distinct) | `+0x019` u8 | — | [C] |
| `MaxSock1` | int 0..5 (6 distinct) | `+0x01A` u8 | — | [C] |
| `MaxSock25` | int 0..6 (6 distinct) | `+0x01B` u8 | — | [C] |
| `MaxSock40` | int 0..6 (6 distinct) | `+0x01C` u8 | — | [C] |
| `TreasureClass` | int 0..1 (2 distinct) | `+0x01D` u8 | — | [C] |
| `Rarity` | int 1..3 (3 distinct) | `+0x01E` u8 | — | [C] |
| `StaffMods` | str, 6 distinct, len ≤ 3, 94 blank | `+0x01F` u8 index | `playerclass:Code` | [C] |
| `CostFormula` | int 0..2 (3 distinct) | `+0x020` u8 | — | [C] |
| `Class` | str, 7 distinct, len ≤ 3, 85 blank | `+0x021` u8 index | `playerclass:Code` | [C] |
| `VarInvGfx` | int 0..6 (4 distinct) | `+0x023` u8 | — | [C] |
| `InvGfx1` | str, 6 distinct, len ≤ 7, 96 blank | `+0x024` char[32] | — | [C] |
| `InvGfx2` | str, 6 distinct, len ≤ 7, 96 blank | `+0x044` char[32] | — | [C] |
| `InvGfx3` | str, 6 distinct, len ≤ 7, 96 blank | `+0x064` char[32] | — | [C] |
| `InvGfx4` | str, 2 distinct, len ≤ 7, 101 blank | `+0x084` char[32] | — | [C] |
| `InvGfx5` | str, 2 distinct, len ≤ 7, 101 blank | `+0x0A4` char[32] | — | [C] |
| `InvGfx6` | str, always 'invjw6', 102 blank | `+0x0C4` char[32] | — | [C] |
| `StorePage` | str, 3 distinct, len ≤ 4, 28 blank | `+0x022` u8 index | `storepage:Code` | [C] |
| `*eol` | int, always 0 | — (comment / end-of-line column; not compiled) | — | — |

## Record layout (228 bytes)

`+0x00` `Code` · `+0x04` `Equiv1` · `+0x06` `Equiv2` · `+0x08`..`+0x09` `Repair`, `Body` ·
`+0x0A`/`+0x0B` `BodyLoc1/2` (u8 index into `bodylocs`) · `+0x0C` `Shoots` · `+0x0E` `Quiver` ·
`+0x10`..`+0x1E` one byte each, `Throwable` … `Rarity` · `+0x1F` `StaffMods`, `+0x21` `Class`
(u8 index into `playerclass`, blank → `0xFF`) · `+0x20` `CostFormula` · `+0x22` `StorePage`
(u8 index into `storepage`) · `+0x23` `VarInvGfx` · `+0x24 + 32·i` `InvGfx(i+1)` `char[32]`. No unknown bytes.

## Fields the quality roll reads (plan 0010 Phase 0)

The itemtypes offsets that [items/0002 §1](../findings/items/0002-quality-roll.md#1-arguments-and-early-returns-0x005586400x005586ce) and [§2](../findings/items/0002-quality-roll.md#2-row-selection--itemratio_select-0x00637910) read in `ITEMS_DropRollQuality`
(quality codes in [§ Answer](../findings/items/0002-quality-roll.md#answer-summary)), with the `.txt` column behind each. Layout tags are by
`excel_bin.py diff` (0 mismatches over the 103 records). "Items" counts the 659 records of
weapons, armor and misc whose own `type` (or `type2`) has the flag; following `Equiv1/2` changes only the
`Rare` count. The role column repeats what [items/0002](../findings/items/0002-quality-roll.md) reads in the
code (all `[I]` there); the finding owns it.

| Offset (items/0002) | `.txt` column | Data | Role in the drop roll (items/0002, `[I]`) | Layout tag |
|---|---|---|---|---|
| `+0x14` | `Magic` | 1 on 9 types: `ring`, `amul`, `char`, `jewl`, `scha`, `mcha`, `lcha`, `mboq`, `mxbq`; 7 items (`amu`, `vip`, `rin`, `cm1`..`cm3`, `jew`) | with the item's `quest`: no-draw return 7; otherwise the roll returns 4 (magic) when it reaches the magic test, so the item is magic at worst | [C] |
| `+0x15` | `Rare` | 1 on 58 types; 506 items directly (300 weapons, 202 armor, 4 misc), 632 when `Equiv` parents count (the misc root `misc` has `Rare` = 1) | the rare test runs only when it is set (no draw otherwise) | [C] |
| `+0x16` | `Normal` | 1 on 31 types (gold, potions, gems, runes, scrolls, books, keys, quivers, body parts…); 121 items (6 weapons: the throwing potions; 115 misc) | no-draw return 2 (normal), the first early return | [C] |
| `+0x21` (§2) | `Class` | 7 classes on 18 types; 111 items (51 weapons, 60 armor), the same with `Equiv` parents | `Class` < 7 on the item's own `type` makes the item class-specific for `ITEMRATIO_Select` (`ITEMS_IsClassSpecific` `0x00629F70`); blank is stored `0xFF` | [C] |

- `[C]` No type has both `Normal` and `Magic`, and no type has both `Normal` and `Rare`. `Magic` and
  `Rare` are both 1 on `ring`, `amul`, `jewl`, `mboq` and `mxbq`. (tbl:ItemTypes.txt:Magic, tbl:ItemTypes.txt:Normal)
- `[I]` The roll tests the item's own `type` only: not `type2`, not the `Equiv1/2` chain (for `Rare` the walk
  would have added 126 items). `StaffMods` is not read by the row selection.
  (fn:ITEMS_DropRollQuality@0x00558640, fn:ITEMS_IsClassSpecific@0x00629F70, tbl:ItemTypes.txt:Rare)

## Fields the TC resolver reads (items/0001)

- `[I]` `Throwable` (`+0x10`): in a classic game an item picked by a TC whose own `type` has
  `Throwable` set is re-picked; the first 10 throwables in one resolver call refund their pick, later
  ones become a Long Sword. Only the item's own `type` is tested
  (fn:ITEMTYPES_IsThrowable@0x00628860, tbl:ItemTypes.txt:Throwable;
  [items/0001 §8](../findings/items/0001-tc-resolution.md#8-item-pick-and-hand-off-0x0055ac5f0x0055af59)).
- `[I]` `Rarity` (`+0x1E`): the entry weight of an item in the auto item-type TCs (`weapN`, `armoN`, …)
  is `max(1, Rarity)` of the item's own `type` record. The 1..3 range of the data means the `max` never
  changes a stock weight (fn:TC_BuildAutoTCs@0x006541C0, tbl:ItemTypes.txt:Rarity;
  [items/0001 §9](../findings/items/0001-tc-resolution.md#9-auto-item-type-tcs-weapn-armon-bown-melen-abown)).

## Fields the base-stat roll reads (plan 0024 Phase 1)

From [items/0006 § 1, § 6](../findings/items/0006-properties.md#1-base-stats-sub_00557ab0_iteminitstats-0x00557ab0)
(static reading); the data counts are computed over `itemtypes.txt`.

- `[I]` **`Quiver`** (`+0x0E`): an item whose own type has a `Quiver` link takes the quiver branch of the base-stat
  roll (quantity from `minstack`/`maxstack`, no `spawnstack`, no durability). Four types have it: `bowq` and `mboq`
  (→ `bow`), `xboq` and `mxbq` (→ `xbow`). (fn:sub_0062E740_ItemTypeQuiver@0x0062E740, tbl:ItemTypes.txt:Quiver)
- `[I]` **`VarInvGfx`** (`+0x23`): when ≠ 0, the last base-stat draw is the picture variant
  `RangeOffset(unit seed, 0, VarInvGfx)`, so `[0, VarInvGfx − 1]`. Seven types have it: `ring` 5, `amul` 3, `char`,
  `scha`, `mcha`, `lcha` 3, `jewl` 6. (fn:sub_00628420_ItemSetInvGfxVariant@0x00628420, tbl:ItemTypes.txt:VarInvGfx)
- `[I]` **`MaxSock1`, `MaxSock25`, `MaxSock40`** (`+0x1A..+0x1C`): `ItemMaxSockets = min(gemsockets, MaxSock1 |
  MaxSock25 | MaxSock40)`, chosen by ilvl ≤ 25, ≤ 40, else. The socket roll (quality 2 or 3) caps it again at 3 / 4 / 6
  by difficulty and sockets the item with count `startSeed % cap + 1`; func 14 (`sock`) caps by
  `min(6, invwidth × invheight, ItemMaxSockets)` with no difficulty cap. (fn:sub_0062BC20_ItemMaxSockets@0x0062BC20,
  fn:ITEMS_SetSockets@0x0062BCB0, fn:PROP_Func14_Sockets@0x0065F590, tbl:ItemTypes.txt:MaxSock1)

## Repair and throwing columns (plan 0043 Phase 0)

The per-type columns the repair, price and wear code is expected to read. Offsets are [§ Columns](#columns) (`[C]`,
`excel_bin.py diff`); the rows come from `python3 -I tools/economy_survey.py types workspace/merged/data/global/excel`
(gate survey `economy`), `[C]` as data. The repair and price readers are read by plan 0043 Phase 1
([items/0011](../findings/items/0011-economy.md)); the meanings are `[L]` except where tagged. Item-side columns (`cost`, `durability`, stacks) are in [Weapons § Economy](Weapons.md#economy-plan-0043-phase-0).

| Column | Field | Rows with it | Meaning |
|---|---|---|---|
| `Repair` | `+0x008` u8 | 32: `shie`, `tors`, `boot`, `glov`, `belt`, `helm`, `circ`, `phlm`, `pelt`, `head`, `ashd`, `cloa`, `scep`, `wand`, `staf`, `orb`, `axe`, `club`, `swor`, `hamm`, `knif`, `spea`, `pole`, `mace`, `xbow`, `h2h`, `h2h2`, `aspe`, `tkni`, `taxe`, `jave`, `ajav` | `[I]` the repair test `ItemCanRepair` reads it on the item's **own** type, no `Equiv` walk ([items/0011 § 5](../findings/items/0011-economy.md#5-callers-buy-sell-repair-the-client-copy)) |
| `Throwable` | `+0x010` u8 | 7: `tpot`, `tkni`, `taxe`, `jave`, `ajav`, `thro`, `comb` | `[I]` the classic-game re-pick in the TC resolver ([items/0001](../findings/items/0001-tc-resolution.md), 0x0055AE6E) and the affix-count rule ([items/0005](../findings/items/0005-affixes.md), fn:sub_0062BA80_ItemTypeThrowable@0x0062BA80); quantity loss on a throw `[L]` |
| `Reload` | `+0x011` u8 | 9: `bowq`, `xboq`, `mboq`, `mxbq`, `tpot`, `tkni`, `taxe`, `jave`, `ajav` | a spent stack is refilled from the inventory `[L]` |
| `ReEquip` | `+0x012` u8 | 5: `tpot`, `tkni`, `taxe`, `jave`, `ajav` | a spent stack is replaced by a like item `[L]` |
| `AutoStack` | `+0x013` u8 | 8: `bowq`, `xboq`, `tpot`, `key`, `tkni`, `taxe`, `jave`, `ajav` | a picked-up item joins a stack `[L]` |
| `Shoots` | `+0x00C` u16 type row | 3: `bow` → `bowq`, `abow` → `bowq`, `xbow` → `xboq` | the ammunition a launcher uses (quantity loss per shot) `[L]` |
| `Quiver` | `+0x00E` u16 type row | 4: `bowq`, `mboq` → `bow`; `xboq`, `mxbq` → `xbow` | `[I]` the quiver branch of the base-stat roll (above); the launcher a quiver feeds `[L]` |
| `CostFormula` | `+0x020` u8 | 1 on 7: `shie`, `tors`, `boot`, `glov`, `belt`, `helm`, `circ`; 2 on `body` (body parts) | price formula selector `[L]` |

- `[C]` `Throwable` and `ReEquip` go together: every `ReEquip` type is `Throwable`; `thro` and `comb` are `Throwable`
  but not `ReEquip`, and they are the parent types (no item has them as its own `type`). Four `Throwable` types
  also have `Repair` (`tkni`, `taxe`, `jave`, `ajav`); `tpot` has neither `Repair` nor durability.
- `[C]` `Reload` without `AutoStack`: `mboq` and `mxbq` (the magic quivers); every other `Reload` type also has
  `AutoStack`, and `key` is the one `AutoStack` type without `Reload`.
- `[C]` `CostFormula` 1 is on armour types only, every one of them a `Repair` type. The one 2 is on `body` (*Body
  Part*, `Equiv1` `misc`, no `Repair`): the 12 misc body parts (`hrt`, `brz`, `jaw`, `eyz`, `hrn`, `tal`, `flg`, `fng`,
  `qll`, `sol`, `scz`, `spe`, `cost` 32..100). No weapon type has a `CostFormula`.
- `[C]` **The item's own `type` against these flags** (the `Equiv` tree not walked): 270 of 306 weapons and all 202
  armors have a `Repair` type; the 36 weapons without one are `bow`, `abow` and `tpot` items, all `nodurability` 1;
  36 weapons have a `Throwable` type (the 30 throwing weapons and the 6 throwing potions, exactly the `stackable`
  weapons). `[I]` The repair test reads the item's own type ([items/0011 § 5](../findings/items/0011-economy.md#5-callers-buy-sell-repair-the-client-copy), 0x0062E6B2–0x0062E6C2); on stock
  data the closure would change no count: walking `Equiv1`/`Equiv2` to the root gives the same 270, 202 and 0 (misc), no item
  differing (survey keys `w_closure_repair` = 270, `a_closure_repair` = 202, `m_closure_repair` = 0 and
  `*_closure_repair_differs` = 0, `economy_survey.py types`).
- `[I]` **`ItemCanRepair`** (fn:sub_0062E660_ItemCanRepair@0x0062E660): an identified, non-ethereal item with missing
  charges can be repaired; otherwise its own type must have `Repair`, and then a repairable stack (throwable,
  stackable, not ethereal) or an item with durability can. So the 13 `nodurability` crossbows of a `Repair` type,
  bows and `tpot` are refused unless they have charges ([items/0011 § 5](../findings/items/0011-economy.md#5-callers-buy-sell-repair-the-client-copy)).
- `[I]` **`StaffMods`** (`+0x01F`) gates the price's staff-mod term: the term runs for every `item_singleskill`
  (stat 107) entry unless the type's byte is 7, which no stock type has (the bytes are 1..6 or 255)
  ([items/0011 § 3](../findings/items/0011-economy.md#3-the-value-terms), fn:sub_0062EDD0_PriceStaffModTerm@0x0062EDD0, tbl:ItemTypes.txt:StaffMods).
- `[I]` **`Class`** (`+0x021`) < 7 (a class-only type) quarters the sell value `S` (after the ethereal quartering,
  which stacks with it); the buy and repair values are untouched ([items/0011 § 3](../findings/items/0011-economy.md#3-the-value-terms) step 8, tbl:ItemTypes.txt:Class).

## Open questions

- `[L]` How `Equiv1/2` chains are walked (depth, cycles) (backlog → reverser).
- Answered `[I]`: each type with `TreasureClass` ≠ 0 (5 types: `bow`, `weap`, `mele`, `armo`, `abow`)
  gets 32 auto TCs named code + level (3, 6, …, 96), which fill TC indices 1–160
  ([data/0001 §7](../findings/data/0001-excel-loader.md#7-treasure-classes-at-load-time)). Item filters and naming details are with the
  reverser (plan 0004).
