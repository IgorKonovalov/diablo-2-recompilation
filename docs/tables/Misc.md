# Misc (`data/global/excel/misc.txt`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 151 (152 data rows − 1 `Expansion` marker)   **Record:** 424 B
> **sha256:** `.txt` `f7fa37ae4f7cdb3f5337a28a55b3876fc27aef066822b3268933e56b636b50f0`, `.bin` `4c0b0e6c2f888847b7a71225d15caf8708c1dd33a9cc8420b6cbbf594963bc1b`
> **Doc status:** columns listed, `.bin` layout complete (shared item record), item-use columns in [§ Item-use columns](#item-use-columns-plan-0060-phase-0) (plan 0060 Phase 0; the dispatch table `[C]`, handler bodies `[I]` or `[L]`); semantics pending except [§ Fields the base-stat roll reads](#fields-the-base-stat-roll-reads-plan-0024-phase-1) (`[I]`, plan 0024 Phase 1); vendor columns in [§ Vendor columns](#vendor-columns-plan-0031-phase-0) (plan 0031 Phase 0; `[I]` meanings from items/0009)

## Purpose

One row per miscellaneous base item: potions, scrolls, gems, runes, jewels, charms, quest items, gold.
Third part of the item list (`items/tc`). The record layout is shared with
[Weapons](Weapons.md#record-layout-424-bytes-shared-by-weapons-armor-and-misc).

## Row identity

- `[C]` Key column `code` (4-character code, space-padded in the record). All 659 codes across
  weapons, armor and misc are distinct.
- `[C]` The `Expansion` marker takes no record (weapons after data row 174, armor after 91, misc after 93).
- `[I]` The game's item index is the position in one combined array: weapons, then armor, then misc,
  copied in that order at load. Codes resolve through a sorted code list (first record wins on a
  duplicate) ([data/0001 §5–6](../findings/data/0001-excel-loader.md#5-where-the-nine-phase-1-tables-land)).
- `[C]` `name` is not compiled; the record holds `namestr` as a string index
  ([tbl.md](../formats/tbl.md)).

## Columns

`[C]` layout tags are by data behaviour: `python3 -I tools/excel_bin.py diff <excel-dir> misc` decodes every record and compares it with every mapped cell (blank cells and encoding rules as in [excel-bin.md](../formats/excel-bin.md#cell-encoding-rules)). A field is tagged `[C]` when the column's values pin its offset (a probe over every record finds no other offset that fits), `[I]` when the column is constant or identical to a sibling column, so its position comes from the neighbouring fields or the stride of its group. Widths are `[C]` with the same proviso; signedness is `[I]` (`s` where the column holds negative values). **Meaning:** no column semantics are claimed here; they come from reverser findings. For the item tables the probe runs over the 659 records of all three files, which share the layout, so a column that is constant in this file can still be `[C]`. `excel_bin.py diff` also checks the 33 layout fields that `misc.txt`
has no column for (4 983 cells, all at the missing-column default).

| Column | Observed type / range | `.bin` field | References | Layout tag |
|---|---|---|---|---|
| `name` | str, 138 distinct, len ≤ 35 | — (editor name; the record holds the namestr string index instead) | — | — |
| `*name` | str, 149 distinct, len ≤ 35 | — (comment / end-of-line column; not compiled) | — | — |
| `szFlavorText` | always blank | — (blank in every misc row; no field identified) | — | — |
| `compactsave` | int 0..1 (2 distinct) | `+0x143` u8 | — | [C] |
| `version` | int 0..109 (3 distinct) | `+0x0F6` u16 | — | [C] |
| `level` | int 0..90 (36 distinct) | `+0x0FD` u8 | — | [C] |
| `levelreq` | int 0..90 (35 distinct) | `+0x13F` u8 | — | [C] |
| `rarity` | int 0..999 (32 distinct) | `+0x0FC` u8 | — | [C] |
| `spawnable` | int 0..1 (2 distinct) | `+0x133` u8 | — | [C] |
| `speed` | int, always 0 | `+0x0D8` s32 | — | [C] |
| `nodurability` | int, always 1 | `+0x113` u8 | — | [C] |
| `cost` | int 0..134540 (68 distinct) | `+0x0E0` u32 | — | [C] |
| `gamble cost` | int 32000..63000 (5 distinct), 146 blank | `+0x0D4` u32 | — | [C] |
| `code` | str, 151 distinct, len ≤ 3 | `+0x080` char[4] code | — | [C] |
| `alternategfx` | str, 124 distinct, len ≤ 3 | `+0x090` char[4] code | — | [C] |
| `namestr` | str, 151 distinct, len ≤ 3 | `+0x0F4` u16 string index | string tables | [C] |
| `component` | int 7..16 (2 distinct) | `+0x115` u8 | — | [C] |
| `invwidth` | int 1..2 (2 distinct) | `+0x10F` u8 | — | [C] |
| `invheight` | int 1..3 (3 distinct) | `+0x110` u8 | — | [C] |
| `hasinv` | int 0..1 (2 distinct) | `+0x137` u8 | — | [C] |
| `gemsockets` | int 0..1 (2 distinct) | `+0x138` u8 | — | [C] |
| `gemapplytype` | int 0..1 (2 distinct) | `+0x13E` u8 | — | [C] |
| `flippyfile` | str, 52 distinct, len ≤ 7 | `+0x000` char[32] | — | [C] |
| `invfile` | str, 131 distinct, len ≤ 8 | `+0x020` char[32] | — | [C] |
| `uniqueinvfile` | str, always 'invvip', 150 blank | `+0x040` char[32] | — | [C] |
| `special` | always blank | — (free-text note ("primarily thrown", ...); not compiled) | — | — |
| `Transmogrify` | int 0..1 (2 distinct) | `+0x139` u8 | — | [C] |
| `TMogType` | str, 10 distinct, len ≤ 3 | `+0x0C8` char[4] code | — | [C] |
| `TMogMin` | str, 4 distinct, len ≤ 2, 137 blank | `+0x13A` u8 | — | [C] |
| `TMogMax` | str, 4 distinct, len ≤ 2, 137 blank | `+0x13B` u8 | — | [C] |
| `useable` | int 0..1 (2 distinct) | `+0x11D` u8 | — | [C] |
| `throwable` | int, always 0 | — (0 in every armor/misc row; not located (weapons.txt has no such column)) | — | — |
| `type` | str, 32 distinct, len ≤ 4 | `+0x11E` u16 index | `itemtypes:Code` | [C] |
| `type2` | str, 5 distinct, len ≤ 4, 116 blank | `+0x120` u16 index | `itemtypes:Code` | [C] |
| `dropsound` | str, 18 distinct, len ≤ 16 | `+0x124` u16 index | `sounds:Sound` | [C] |
| `dropsfxframe` | int 10..14 (3 distinct) | `+0x128` u8 | — | [C] |
| `usesound` | str, 18 distinct, len ≤ 17, 4 blank | `+0x126` u16 index | `sounds:Sound` | [C] |
| `unique` | int 0..1 (2 distinct) | `+0x129` u8 | — | [C] |
| `transparent` | int 0..1 (2 distinct) | `+0x12C` u8 | — | [C] |
| `transtbl` | int 3..5 (3 distinct) | `+0x12D` u8 | — | [C] |
| `lightradius` | int 0..6 (2 distinct) | `+0x12F` u8 | — | [C] |
| `belt` | int 0..1 (2 distinct) | `+0x130` u8 | — | [C] |
| `autobelt` | int 0..1 (2 distinct) | `+0x131` u8 | — | [C] |
| `stackable` | int 0..1 (2 distinct) | `+0x132` u8 | — | [C] |
| `minstack` | int 0..100 (6 distinct) | `+0x0E4` u32 | — | [C] |
| `maxstack` | int 0..5000 (7 distinct) | `+0x0E8` u32 | — | [C] |
| `spawnstack` | int 0..200 (5 distinct) | `+0x0EC` u32 | — | [C] |
| `quest` | int 5..32 (9 distinct), 134 blank | `+0x12A` u8 | — | [C] |
| `questdiffcheck` | int, always 1, 135 blank | `+0x12B` u8 | — | [C] |
| `missiletype` | int, always 0 | `+0x0FA` u16 | — | [C] |
| `spellicon` | int, always -1 | `+0x134` s8 | — | [I] |
| `pSpell` | int 1..9 (8 distinct), 129 blank | `+0x094` u32 | — | [C] |
| `state` | str, 6 distinct, len ≤ 10, 137 blank | `+0x098` u16 index | `states:state` | [C] |
| `cstate1` | str, 2 distinct, len ≤ 6, 149 blank | `+0x09A` u16 index | `states:state` | [C] |
| `cstate2` | str, always 'cold', 150 blank | `+0x09C` u16 index | `states:state` | [C] |
| `len` | int 128..1000 (7 distinct), 137 blank | `+0x0B0` s32 offset into itemscode.bin | — | [C] |
| `stat1` | str, 8 distinct, len ≤ 20, 134 blank | `+0x09E` u16 index | `itemstatcost:Stat` | [C] |
| `calc1` | int 5..5000 (15 distinct), 134 blank | `+0x0A4` s32 offset into itemscode.bin | — | [C] |
| `stat2` | str, 3 distinct, len ≤ 15, 147 blank | `+0x0A0` u16 index | `itemstatcost:Stat` | [C] |
| `calc2` | int 10..100 (3 distinct), 147 blank | `+0x0A8` s32 offset into itemscode.bin | — | [C] |
| `stat3` | always blank | `+0x0A2` u16 index | `itemstatcost:Stat` | [I] |
| `calc3` | always blank | `+0x0AC` s32 offset into itemscode.bin | — | [I] |
| `spelldesc` | int 1..2 (2 distinct), 139 blank | `+0x0B4` u16 | — | [C] |
| `spelldescstr` | str, 3 distinct, len ≤ 15, 139 blank | `+0x0B6` u16 string index | string tables | [C] |
| `spelldesccalc` | int 20..320 (10 distinct), 141 blank | `+0x0B8` s32 offset into itemscode.bin | — | [C] |
| `durwarning` | int, always 0 | `+0x135` u8 | — | [C] |
| `qntwarning` | int 0..1 (2 distinct) | `+0x136` u8 | — | [C] |
| `gemoffset` | int, always 0 | `+0x0F0` s32 (compiled; overwritten at load, see Open questions) | — | [I] |
| `BetterGem` | str, 29 distinct, len ≤ 3 | `+0x0BC` char[4] code | — | [C] |
| `bitfield1` | int 0..1 (2 distinct) | `+0x0DC` u32 | — | [C] |
| `CharsiMin` | int 2..3 (2 distinct), 149 blank | `+0x148` u8 | — | [C] |
| `CharsiMax` | int 4..5 (2 distinct), 149 blank | `+0x159` u8 | — | [C] |
| `CharsiMagicMin` | always blank | `+0x16A` u8 | — | [C] |
| `CharsiMagicMax` | always blank | `+0x17B` u8 | — | [C] |
| `CharsiMagicLvl` | int, always 255 | `+0x18C` u8 | — | [C] |
| `GheedMin` | int 1..5 (3 distinct), 148 blank | `+0x147` u8 | — | [C] |
| `GheedMax` | int 3..9 (3 distinct), 148 blank | `+0x158` u8 | — | [C] |
| `GheedMagicMin` | int, always 5, 150 blank | `+0x169` u8 | — | [C] |
| `GheedMagicMax` | int, always 9, 150 blank | `+0x17A` u8 | — | [C] |
| `GheedMagicLvl` | int, always 255 | `+0x18B` u8 | — | [C] |
| `AkaraMin` | int 1..11 (3 distinct), 143 blank | `+0x146` u8 | — | [C] |
| `AkaraMax` | int 1..17 (4 distinct), 141 blank | `+0x157` u8 | — | [C] |
| `AkaraMagicMin` | int, always 1, 150 blank | `+0x168` u8 | — | [C] |
| `AkaraMagicMax` | int, always 2, 150 blank | `+0x179` u8 | — | [C] |
| `AkaraMagicLvl` | int, always 255 | `+0x18A` u8 | — | [C] |
| `FaraMin` | int, always 3, 149 blank | `+0x149` u8 | — | [C] |
| `FaraMax` | int, always 4, 149 blank | `+0x15A` u8 | — | [C] |
| `FaraMagicMin` | int, always 3, 149 blank | `+0x16B` u8 | — | [C] |
| `FaraMagicMax` | int, always 4, 149 blank | `+0x17C` u8 | — | [C] |
| `FaraMagicLvl` | int, always 255 | `+0x18D` u8 | — | [C] |
| `LysanderMin` | int 1..9 (4 distinct), 143 blank | `+0x14A` u8 | — | [C] |
| `LysanderMax` | int 1..15 (4 distinct), 143 blank | `+0x15B` u8 | — | [C] |
| `LysanderMagicMin` | int 3..9 (3 distinct), 147 blank | `+0x16C` u8 | — | [C] |
| `LysanderMagicMax` | int 5..15 (3 distinct), 147 blank | `+0x17D` u8 | — | [C] |
| `LysanderMagicLvl` | int, always 255 | `+0x18E` u8 | — | [I] |
| `DrognanMin` | int 1..11 (3 distinct), 143 blank | `+0x14B` u8 | — | [C] |
| `DrognanMax` | int 1..17 (3 distinct), 143 blank | `+0x15C` u8 | — | [C] |
| `DrognanMagicMin` | int 2..11 (2 distinct), 147 blank | `+0x16D` u8 | — | [C] |
| `DrognanMagicMax` | int 4..17 (2 distinct), 147 blank | `+0x17E` u8 | — | [C] |
| `DrognanMagicLvl` | int, always 255 | `+0x18F` u8 | — | [C] |
| `HraltiMin` | int 2..3 (2 distinct), 148 blank | `+0x14C` u8 | — | [C] |
| `HraltiMax` | int 3..4 (2 distinct), 148 blank | `+0x15D` u8 | — | [C] |
| `HraltiMagicMin` | int 2..3 (2 distinct), 148 blank | `+0x16E` u8 | — | [C] |
| `HraltiMagicMax` | int 3..4 (2 distinct), 148 blank | `+0x17F` u8 | — | [C] |
| `HraltiMagicLvl` | int, always 255 | `+0x190` u8 | — | [I] |
| `AlkorMin` | int 3..8 (3 distinct), 148 blank | `+0x14D` u8 | — | [C] |
| `AlkorMax` | int 5..11 (3 distinct), 148 blank | `+0x15E` u8 | — | [C] |
| `AlkorMagicMin` | always blank | `+0x16F` u8 | — | [I] |
| `AlkorMagicMax` | always blank | `+0x180` u8 | — | [I] |
| `AlkorMagicLvl` | int, always 255 | `+0x191` u8 | — | [I] |
| `OrmusMin` | int 1..11 (3 distinct), 141 blank | `+0x14E` u8 | — | [C] |
| `OrmusMax` | int 1..17 (3 distinct), 141 blank | `+0x15F` u8 | — | [C] |
| `OrmusMagicMin` | int 2..11 (2 distinct), 147 blank | `+0x170` u8 | — | [C] |
| `OrmusMagicMax` | int 4..17 (2 distinct), 147 blank | `+0x181` u8 | — | [C] |
| `OrmusMagicLvl` | int, always 255 | `+0x192` u8 | — | [C] |
| `ElzixMin` | int, always 2, 149 blank | `+0x14F` u8 | — | [C] |
| `ElzixMax` | int, always 3, 149 blank | `+0x160` u8 | — | [C] |
| `ElzixMagicMin` | always blank | `+0x171` u8 | — | [C] |
| `ElzixMagicMax` | always blank | `+0x182` u8 | — | [C] |
| `ElzixMagicLvl` | int, always 255 | `+0x193` u8 | — | [C] |
| `AshearaMin` | int, always 2, 149 blank | `+0x150` u8 | — | [C] |
| `AshearaMax` | int, always 3, 149 blank | `+0x161` u8 | — | [C] |
| `AshearaMagicMin` | always blank | `+0x172` u8 | — | [C] |
| `AshearaMagicMax` | always blank | `+0x183` u8 | — | [C] |
| `AshearaMagicLvl` | int, always 255 | `+0x194` u8 | — | [C] |
| `CainMin` | int 2..8 (3 distinct), 148 blank | `+0x151` u8 | — | [C] |
| `CainMax` | int 3..11 (3 distinct), 148 blank | `+0x162` u8 | — | [C] |
| `CainMagicMin` | always blank | `+0x173` u8 | — | [C] |
| `CainMagicMax` | always blank | `+0x184` u8 | — | [C] |
| `CainMagicLvl` | int, always 255 | `+0x195` u8 | — | [C] |
| `HalbuMin` | int, always 3, 149 blank | `+0x152` u8 | — | [C] |
| `HalbuMax` | int, always 4, 149 blank | `+0x163` u8 | — | [C] |
| `HalbuMagicMin` | always blank | `+0x174` u8 | — | [C] |
| `HalbuMagicMax` | always blank | `+0x185` u8 | — | [C] |
| `HalbuMagicLvl` | int, always 255 | `+0x196` u8 | — | [C] |
| `MalahMin` | int 1..5 (4 distinct), 135 blank | `+0x154` u8 | — | [C] |
| `MalahMax` | int 1..7 (6 distinct), 135 blank | `+0x165` u8 | — | [C] |
| `MalahMagicMin` | always blank | `+0x176` u8 | — | [C] |
| `MalahMagicMax` | always blank | `+0x187` u8 | — | [C] |
| `MalahMagicLvl` | int, always 255 | `+0x198` u8 | — | [C] |
| `LarzukMin` | int, always 3, 149 blank | `+0x155` u8 | — | [C] |
| `LarzukMax` | int, always 4, 149 blank | `+0x166` u8 | — | [C] |
| `LarzukMagicMin` | always blank | `+0x177` u8 | — | [C] |
| `LarzukMagicMax` | always blank | `+0x188` u8 | — | [C] |
| `LarzukMagicLvl` | int, always 255 | `+0x199` u8 | — | [C] |
| `DrehyaMin` | int, always 3, 149 blank | `+0x156` u8 | — | [C] |
| `DrehyaMax` | int, always 4, 149 blank | `+0x167` u8 | — | [C] |
| `DrehyaMagicMin` | always blank | `+0x178` u8 | — | [C] |
| `DrehyaMagicMax` | always blank | `+0x189` u8 | — | [C] |
| `DrehyaMagicLvl` | int, always 255 | `+0x19A` u8 | — | [C] |
| `JamellaMin` | int 1..5 (4 distinct), 135 blank | `+0x153` u8 | — | [C] |
| `JamellaMax` | int 1..7 (6 distinct), 135 blank | `+0x164` u8 | — | [C] |
| `JamellaMagicMin` | int, always 1, 150 blank | `+0x175` u8 | — | [C] |
| `JamellaMagicMax` | int, always 2, 150 blank | `+0x186` u8 | — | [C] |
| `JamellaMagicLvl` | int, always 255 | `+0x197` u8 | — | [C] |
| `Source Art` | always blank | — (editor note; blank) | — | — |
| `Game Art` | str, always ' ', 150 blank | — (editor note; blank or a single space) | — | — |
| `Transform` | int, always 0 | `+0x141` u8 | — | [C] |
| `InvTrans` | int, always 0 | `+0x142` u8 | — | [C] |
| `SkipName` | int 0..1 (2 distinct) | `+0x144` u8 | — | [C] |
| `NightmareUpgrade` | str, 3 distinct, len ≤ 3 | `+0x19C` char[4] code | — | [C] |
| `HellUpgrade` | str, 3 distinct, len ≤ 3 | `+0x1A0` char[4] code | — | [C] |
| `mindam` | always blank | `+0x0FE` u8 | — | [C] |
| `maxdam` | always blank | `+0x0FF` u8 | — | [C] |
| `PermStoreItem` | int, always 1, 127 blank | `+0x1A4` u8 | — | [C] |
| `multibuy` | int, always 1, 131 blank | `+0x1A5` u8 | — | [C] |
| `Nameable` | always blank | `+0x145` u8 | — | [C] |
| `*eol` | int, always 0 | — (comment / end-of-line column; not compiled) | — | — |

- `[C]` `TMogMin`/`TMogMax` are tagged `[C]` although the probe cannot use the three single-space cells:
  the remaining values (0, 1, 10, 40) pin the bytes, and the spaces decode as −16 (`0xF0`).
- `[I]` `spellicon` is −1 in every row; `+0x134` is the only byte that is `0xFF` in every misc record
  and 0 in every weapon and armor record (which lack the column).

## Interpretation notes

- `[C]` **`HratliMagicLvl` is a dead column** in weapons and armor: the header is misspelled, the
  compiler does not find `HraltiMagicLvl`, and `+0x190` is 0 in every weapon and armor record. In misc
  the header is spelled `HraltiMagicLvl` and the field holds its 255s.
- `[C]` Values wider than their field are truncated (misc `rarity = 999` → 231), and a single-space
  cell compiles to −16 (misc `TMogMin`/`TMogMax` of the Khalim parts → `0xF0`).
- `[C]` Calc columns are offsets into `itemscode.bin`; every non-blank misc calc cell is an integer
  constant and decodes back to its value ([excel-bin.md § calc](../formats/excel-bin.md#calc-columns-formulas)).
- `[I]` **`version` 0 places a row in the classic index map.** `ITEMS_LoadItemTables` writes, in item order, the
  combined index of every weapons, armor and misc record whose `version` (`+0x0F6`) is 0 into a u16 list
  (`g_pClassicItemIndex`); its one reader is the version-`0x47` item record reader, which names an item by its
  position among the version-0 items and maps it through the list to the current index. `[C]` (data) 361 of the 659
  item rows have `version` 0: weapons 175, armor 92, misc 94; the rest are 100 (misc one row 109).
  ([data/0001 § Plan 0039 batch P1b](../findings/data/0001-excel-loader.md#plan-0039-batch-p1b-2026-10-17) Q3,
  fn:ITEMS_LoadItemTables@0x006315D0, data:g_pClassicItemIndex@0x0096CA78, tbl:Weapons.txt:version)
- *plan 0046 readers* (`pSpell`): `[C]` the item-use table `g_ItemUseFns` holds entries 10 and 11 (data, [skills/0015 § 1](../findings/skills/0015-item.md#1-the-table-slots-the-stock-rows-and-the-callers)); `[I]` both cast skill 47 (Fire Ball) at level 1, effect 0, through `ItemCastAtUnit` or `ItemCastAtXY` (10 at the user's target unit or its path point, 11 at the stack point) (fn:sub_005BF170_ItemUseCastFireBall@0x005BF170, fn:sub_005BF1F0_ItemUseCastFireBallXY@0x005BF1F0, data:g_ItemUseFns@0x00741790); `[C]` (data) no stock row has `pSpell` 10 or 11: the values are 1, 2, 3, 5, 6, 7, 8, 9 (tbl:Misc.txt:pSpell).

## Fields the quality roll reads (plan 0010 Phase 0)

The item-record offsets that [items/0002 §1](../findings/items/0002-quality-roll.md#1-arguments-and-early-returns-0x005586400x005586ce) and [§2](../findings/items/0002-quality-roll.md#2-row-selection--itemratio_select-0x00637910)
read, with the `.txt` column behind each; the shared table and its notes are in
[Weapons § Fields the quality roll reads](Weapons.md#fields-the-quality-roll-reads-plan-0010-phase-0).
Counts are computed over `misc.txt`; layout tags are by `excel_bin.py diff` (0 mismatches).

| Offset (items/0002) | `.txt` column | Data in misc | Layout tag |
|---|---|---|---|
| `+0x129` | `unique` | 1 on 10 items, all of type `ques`: `bks`, `bkd`, `j34`, `g34`, `bbb`, `tr1`, `mss`, `ass`, `tr2`, `std` | [C] |
| `quest` (`+0x12A`) | `quest` | 5..32 on 17 items: 9 of the 10 above (not `std`, Standard of Heroes) plus `vip`, `luv`, `xyz`, `box`, `qey`, `qhr`, `qbr`, `ice` | [C] |
| `level` (`+0x0FD`), the qlvl | `level` | 0..90 | [C] |
| `type` (`+0x11E`) | `type` | 32 types. 115 items have a `type` with itemtypes `Normal` = 1; 7 (`amu`, `vip`, `rin`, `cm1`..`cm3`, `jew`) one with `Magic` = 1; 4 of those 7 (`amu`, `vip`, `rin`, `jew`) one with `Rare` = 1 | [C] |
| uber / exceptional flag | **no column** | `misc.txt` has no `normcode`/`ubercode`/`ultracode`; the three fields are 4 spaces (blank) in every record | — |
| class-specific flag | **no column** in this table | no misc `type` has itemtypes `Class` set | — |

- `[C]` `vip` (Amulet of the Viper) is the only item in the three files with `quest` > 0 whose `type`
  has itemtypes `Magic` = 1, the combination items/0002 §1 reads as an early return to quality 7. No item with
  `unique` = 1 has a `type` with itemtypes `Normal` = 1. (tbl:Misc.txt:quest, tbl:ItemTypes.txt:Magic)

## Fields the quest services read (plan 0032)

- `[I]` **`questdiffcheck`** (`+0x12B`): every created item with `quest` ≠ 0 and `questdiffcheck` ≠ 0 gets stat 356
  (`questitemdifficulty`) = the game difficulty, and counts as held by a quest script's "already has it" test only
  when its stat 356 is ≥ the game's difficulty. `box` (blank) counts in every difficulty.
  ([items/0010 § 5](../findings/items/0010-quest-drops.md#5-quest-items), fn:sub_00557AB0_ItemInitStats@0x00557AB0,
  fn:sub_00558110_PlayerFindItemByCode@0x00558110, tbl:Misc.txt:questdiffcheck)
- `[C]` **`quest` − 1 is a quest object id** (`g_QuestDescs` `+0x10`), not a quest word + 1:
  `sub_00543BD0_QuestsInvItemEvent` calls event 9 of the quest object whose id is `quest − 1`,
  `sub_00555D20_ItemQuestHook` registers the item with that object, and the gate `sub_0055CC90_ItemQuestGate` keeps its
  own `{word, quest}` pairs, each the word `g_QuestDescs` gives object `quest − 1`. `[I]` The object maps to the record
  word as id = word in Act I only, so `bks`/`bkd` 5 → word 4, `vip`/`box` 10 → word 10, `qey`… 17 → word 18,
  `mss` 23 → word 25, `ice` 32 → word 35. ([items/0010 § 5](../findings/items/0010-quest-drops.md#5-quest-items), fn:QUESTS_FindById@0x00543640, data:g_QuestDescs@0x00731510, data:g_QuestItemWordGate@0x00731FEC, tbl:Misc.txt:quest)
- The imbue and personalization tests (`bitfield1` bit 0, `compactsave`, `Nameable`) are in
  [Weapons § Fields the quest services read](Weapons.md#fields-the-quest-services-read-plan-0032).

## Fields the base-stat roll reads (plan 0024 Phase 1)

From [items/0006 § 1](../findings/items/0006-properties.md#1-base-stats-sub_00557ab0_iteminitstats-0x00557ab0)
(static reading); the data counts are computed over `misc.txt`. The draws are on the item unit's own seed.

- `[I]` **`stackable`, `minstack`, `maxstack`, `spawnstack`.** A stackable misc base draws `minstack + RangeB(top −
  minstack)`, `top` never drawn, with `top = spawnstack` when `spawnstack ≥ minstack` and ≠ 0, else
  `maxstack` (+ stat 254, capped at 511). The branch is chosen by the item's type before that:
  - gold (`gld`, type `gold`) does not use these columns: `ilvl + RNG_Range(5 × ilvl)`, at least 1;
  - the quivers (`aqv` `bowq`, `cqv` `xboq`: their type has a `Quiver` link, [ItemTypes](ItemTypes.md#fields-the-base-stat-roll-reads-plan-0024-phase-1))
    draw `minstack + RangeB(maxstack − minstack)` and **ignore `spawnstack`** (200 and 150): `aqv` 100..349,
    `cqv` 60..249;
  - the other 7 stackable rows take the misc reading: `tbk`, `ibk` (1..4) and `key` (1..5) by `spawnstack`; the
    four `rps`/`rpl`/`bps`/`bpl` rows have `spawnstack` 0, so `top = maxstack` (5..9).

  (fn:sub_00557AB0_ItemInitStats@0x00557AB0, fn:ITEMS_GetSpawnStack@0x00629660, fn:ITEMS_GetMaxStack@0x006295B0,
  tbl:Misc.txt:spawnstack)
- `[I]` **`nodurability`** is not read by the base-stat roll: misc bases draw no durability.
  (fn:sub_00557AB0_ItemInitStats@0x00557AB0)
- `[I]` **`hasinv`, `gemsockets`.** The socket roll needs quality 2 or 3, `hasinv`, not `stackable` and
  `ItemMaxSockets` > 0 (2 misc rows have `hasinv` 1 and `gemsockets` > 0). (fn:sub_00556B60_ItemRollSockets@0x00556B60,
  tbl:Misc.txt:gemsockets)

## Vendor columns (plan 0031 Phase 0)

The vendor fields, their offsets, the group order and the survey command are in
[Weapons § Vendor columns](Weapons.md#vendor-columns-plan-0031-phase-0), with their code meanings from
[items/0009](../findings/items/0009-vendors.md). Misc counts
(`[C]`, `python3 -I tools/vendor_survey.py summary` and `bases`):

| Group | bases | magic | `MagicLvl` on those bases |
|---|---:|---:|---|
| Akara | 10 | 1 | 255 |
| Gheed | 3 | 1 | 255 |
| Charsi, Elzix, Asheara, Halbu, Larzuk, Drehya | 2 | 0 | 255 |
| Fara | 2 | 2 | 255 |
| Lysander, Drognan | 8 | 4 | 255 |
| Hralti | 3 | 3 | 255 (misc spells the header `HraltiMagicLvl`, so the field is live here) |
| Alkor, Cain | 3 | 0 | 255 |
| Ormus | 10 | 4 | 255 |
| Jamella | 16 | 1 | 255 |
| Malah | 16 | 0 | 255 |

- `[C]` 18 misc records have a non-zero vendor byte (all `version` 0), and every one has `MagicLvl` 255 for every
  group. The non-zero `MagicMin`/`MagicMax` on misc are on Lysander's `vps`, `yps`, `wms`, Drognan's and Ormus's
  tomes and scrolls (`tbk`, `ibk`, `tsc`, `isc`), Fara's and Hralti's quivers (`aqv`, `cqv`), and the key (`key`:
  Akara, Gheed, Lysander, Hralti, Jamella). `[I]` No misc item is stocked magic: magic copies need `MagicLvl` ≤ the
  stock level (at most 104) and `bitfield1` bit 0, and every stocked misc record has `MagicLvl` 255 (and `bitfield1`
  0; only `amu`, `vip`, `rin`, `jew` have bit 0). ([items/0009 § 4](../findings/items/0009-vendors.md#4-the-stock-build-vendor_buildstock-0x00576980),
  fn:VENDOR_BuildStock@0x00576980, tbl:Misc.txt:bitfield1)
- `[C]` **`PermStoreItem` is 1 on 24 misc records** (potions of every kind, `tbk`, `ibk`, `aqv`, `cqv`, `tsc`, `isc`,
  `key`), and `multibuy` is 1 on 20 of them (not on the two tomes and the two quivers). Six permanent records have no
  vendor byte at all: `hpo`, `mpo`, `hpf`, `mpf`, `hp5`, `mp5`. `[I]` Those six are never listed: the list builder
  needs `<V>Max` or `<V>MagicMax` ≠ 0 before it looks at `PermStoreItem`; a listed permanent base gets one
  quality-2 copy per build, and `aqv`/`cqv` a full stack. ([items/0009 § 2](../findings/items/0009-vendors.md#2-the-candidate-lists-vendor_buildlist-0x00536d50),
  fn:VENDOR_BuildList@0x00536D50)
- `[C]` 6 misc records have a `NightmareUpgrade` and 8 a `HellUpgrade` naming an item: the healing and mana potions
  (`hp1`..`hp3` → `hp4` in nightmare and every `hp1`..`hp4` → `hp5` in hell; the same for `mp*`), each to an item of the same type.

## Economy (plan 0043 Phase 0)

The fields, their offsets, the readers named so far and the survey command are in
[Weapons § Economy](Weapons.md#economy-plan-0043-phase-0), with the readers plan 0043 Phase 1 found (`[I]`). Misc rows
(`[C]`, `python3 -I tools/economy_survey.py items`, gate survey `economy`):

- `[C]` `cost` 0..134 540 (68 distinct). **`cost` is 0 on 7 rows**: gold (`gld`), the ear (`ear`) and five quest items
  (`box`, `tr1`, `mss`, `ass`, `tr2`; editor names Horadric Cube, Scroll of Horadric Quest Info, Mephisto SoulStone,
  Book of Skill, Scroll of Malah - Boost Resistances). The other 12 quest rows have a `cost` (e.g. `luv` 99 999, `bkd` 12 000, `ice` 10 000, `xyz` 10 000, `qey` 45).
- `[C]` **`gamble cost` is set on 5 rows only**, all above `cost`: `amu` 2 400 / 63 000, `rin` 1 800 / 50 000, the charms
  `cm1` 2 000 / 45 000, `cm2` 1 000 / 38 000, `cm3` 600 / 32 000 (`cost` / `gamble cost`); the other 146 cells are
  blank. Only `amu` and `rin` are on the gamble list. `[I]` Only those two (and version-0 items) have their gamble
  price read from the column ([items/0011 § 2](../findings/items/0011-economy.md#2-the-gamble-price-mode-2)).
- `[C]` `durability` is blank and `nodurability` 1 on every row; `durwarning` 0 everywhere.
- `[C]` **Stacks.** 10 `stackable` rows: the tomes `tbk`, `ibk` (1/20/5 as `minstack`/`maxstack`/`spawnstack`), the
  quivers `aqv` (100/350/200) and `cqv` (60/250/150), `key` (1/12/6), gold `gld` (0/5000/0) and the four unused potions
  `rps`, `rpl`, `bps`, `bpl` (5/10/0). One row has a `maxstack` without `stackable`: the torch `tch` (2/10/0).
  `qntwarning` is 1 on the two quivers and 0 elsewhere.
- `[C]` **`multibuy` 1 on 20 rows**, all `PermStoreItem`: the potions (`hp1`..`hp5`, `mp1`..`mp5`, `hpo`, `mpo`, `hpf`,
  `mpf`, `vps`, `yps`, `wms`), the scrolls `tsc` (`cost` 100) and `isc` (80), and `key` (45).
- `[C]` The 12 body parts (type `body`: `hrt`, `brz`, `jaw`, `eyz`, `hrn`, `tal`, `flg`, `fng`, `qll`, `sol`, `scz`,
  `spe`, `cost` 32..100) are the only items whose type has `CostFormula` 2; no other misc type has a `CostFormula`
  ([ItemTypes § Repair and throwing columns](ItemTypes.md#repair-and-throwing-columns-plan-0043-phase-0)).
- `[C]` The tomes' `cost` equals [Books](Books.md) `BaseCost` (`tbk` 250, `ibk` 200); `CostPerCharge` (50, 40) is
  neither scroll's `cost` (`tsc` 100, `isc` 80). `[I]` A tome's base price is `CostPerCharge × q + cost` (this
  `cost`, not `BaseCost`); a quiver's is `cost × q / 1024` with the repair value `MaxStack × cost / 1024`; a body part's
  `cost + 8 × MonStats Level` of its monster for the difficulty; an ear's `earLevel × cost` ([items/0011 § 1](../findings/items/0011-economy.md#1-the-price-core-inputs-and-the-base)).

## Item-use columns (plan 0060 Phase 0)

The columns a used, stacked or belted item reads, with the readers the findings name. `python3 -I tools/excel_bin.py
diff` checks every offset below (0 mismatches over the 151 rows); the counts are over the 151 misc rows and were
computed from the `.txt`. Whatever a function does beyond what is quoted is Phase 1.1 and 1.2 of
[plan 0060](../plans/0060-item-use-inventory.md).

### The use dispatch: `pSpell` selects a `g_ItemUseFns` entry

- `[C]` (data, the pinned image) `g_ItemUseFns` (`0x00741790`, count 31 at `0x0074178C`) is an array of `{test, use}`
  address pairs, one per `pSpell`. Entries 1..11 hold a `use` address, entries 0 and 12..30 are zero, and only entry 1 has a
  `test` (`0x005BE130`); the `use` addresses are 1 `0x005BE230`, 2 `0x005BE290`, 3 `0x005BE3F0`, 4 `0x005BE7B0`,
  5 `0x005BEAC0`, 6 `0x005BEF90`, 7 `0x005BF0C0`, 8 `0x005BF060`, 9 `0x005BEDA0`, 10 `0x005BF170`, 11 `0x005BF1F0`.
  (data:g_ItemUseFns@0x00741790, tbl:Misc.txt:pSpell)
- `[I]` `sub_005BF240_ItemUse` (`.\SKILLS\SkillItem.cpp`) runs the entry of the used item's `pSpell` (`+0x094`) as
  `use(ECX game, EDX the user, stack: the item, …)`; a scroll or tome reaches it through skill do 113, whose handler
  finds the scroll or book in the inventory and calls `InvUse` (item page 1) or `BeltUse` (page 2)
  ([data/0005](../findings/data/0005-calc.md), [skills/0015 § 4](../findings/skills/0015-item.md#4-do-113-and-do-151),
  fn:sub_005BF240_ItemUse@0x005BF240, fn:sub_005BF3D0_SkillDo113UseBookScroll@0x005BF3D0).
- The stock rows per value (`[C]` data; 22 rows have a `pSpell`, 129 are blank, and all 22 have `useable` 1):

| `pSpell` | Rows | `use` (what the findings say) | Tag |
|---|---|---|---|
| 1 | `isc`, `ibk` (identify scroll, book) | `0x005BE230` with the only `test`, `0x005BE130`; body not read | address [C]; body `[L]` |
| 2 | `tsc`, `tbk` (town portal) | `ITEMUSE_TownPortal`, `0x005BE290` ([quests/0002](../findings/quests/0002-travel.md)) | [I] |
| 3 | `hp1`..`hp5`, `mp1`..`mp5` (10 healing and mana potions) | `0x005BE3F0`: `len` read at `0x005BE430`, `calc1..3` at `0x005BE4D9` | [I] |
| 4 | none | `0x005BE7B0` | address [C]; body `[L]` |
| 5 | `rvs`, `rvl` (rejuvenation) | `0x005BEAC0` | [I] |
| 6 | `yps` (antidote), `wms` (thawing) | `0x005BEF90`, which calls `0x005BEDA0` | [I] |
| 7 | `box` (Horadric Cube) | `0x005BF0C0`; body not read | address [C]; body `[L]` |
| 8 | `elx` (elixir) | `0x005BF060`; body not read | address [C]; body `[L]` |
| 9 | `vps` (stamina), `hrb` (herb) | `sub_005BEDA0_ItemUseTimedState` | [C] |
| 10, 11 | none | cast skill 47 at level 1 ([skills/0015 § 1](../findings/skills/0015-item.md#1-the-table-slots-the-stock-rows-and-the-callers)) | [I] |

- `[C]` (data) Of the 35 `useable` rows, the 13 with no `pSpell` are `hpo`, `mpo`, `hpf`, `mpf` (the full and plain
  healing and mana potions of types `hpot`/`mpot`, `belt` 1), `rps`, `rpl`, `bps`, `bpl` (the small and large red and
  blue potions, `belt` 0, stackable 5..10), `xyz`, `ass`, `tr2`, `toa` (quest items of type `ques`) and `0sc` (a scroll).
  So `useable` is not what picks a handler; the dispatch is `pSpell` alone, and what `useable` gates is read nowhere in
  the findings (`[L]`).

### Timed states: `state`, `cstate1`, `cstate2`, `len`, `stat1..3`, `calc1..3`

- `[C]` (data) 14 rows have a `state`: `healthpot` (`hp1`..`hp5`), `manapot` (`mp1`..`mp5`), `staminapot` (`vps`),
  `antidote` (`yps`, with `cstate1` `poison`), `thawing` (`wms`, with `cstate1` `freeze` and `cstate2` `cold`) and
  `innersight` (`hrb`). `len` is set on 14 rows (potions 128..256 for the 10 healing and mana potions, 750 for `vps`,
  `yps`, `wms`, 1000 for `hrb`; a bytecode offset that decodes to an integer constant). `stat1`/`calc1` is set on 17 rows
  (`stat2`/`calc2` on 4: `yps` and `wms` the max resistance, `rvs` and `rvl` mana), `stat3`/`calc3` never.
- `[I]` `sub_005BEDA0_ItemUseTimedState`: the record's `state` (`+0x098`) must be a valid state and `len` at least 1; the
  state is set, or extended, for `len` frames on a stat list of the user with a timer event 12 at its end, and each of
  `stat1..3` (`+0x09E`) gets `calc1..3` (`+0x0A4`) when non-zero (after stat 28, when stat 10 is below stat 11, stat 10
  is set to stat 11 + 256). The potions run the group clear before they apply
  ([data/0005](../findings/data/0005-calc.md), [stats/states](../specs/stats/states.md) B3, fn:sub_005BEDA0_ItemUseTimedState@0x005BEDA0).
  The healing potions' `stat1` is `hpregen` (stat 74) and the mana potions' `manarecovery` (stat 26), the amounts
  `calc1`: 30, 60, 100, 180, 320 and 20, 40, 80, 150, 250. The life tick adds stat 74 every frame whatever its sign, so
  the healing potion's `hpregen` is added to life (stat 6) at each tick while the state lasts (`[C]` the tick,
  [stats/states](../specs/stats/states.md) E2, fn:sub_00580610_LifeRegenTick@0x00580610).
- `[C]` (data) The one-shot rows have no `state` and no `len`: `rvs`/`rvl` (`pSpell` 5) carry `hitpoints` 35/100 and `mana`
  35/100 as `stat1`/`stat2`/`calc1`/`calc2`, and `elx` (`pSpell` 8) carries `experience` 5. `[L]` how `0x005BEAC0`
  and `0x005BF060` apply them (a flat value or a percentage of the maximum): the findings do not read them.

### Display columns of the same rows

`[C]` (data) `spelldesc` is 1 on `rvs`/`rvl` (string key `spelldescstr` `ItemStatsrejuv1`/`2`, no calc) and 2 on the
ten healing and mana potions (`ItemStats1q`, `spelldesccalc` = the potion's amount: 30..320, 20..250). They are
tooltip text and numbers, the client's; the code anchors in [data/0004](../findings/data/0004-cell-converters.md) are
the converters only. `durwarning` is 0 in all 151 rows and `qntwarning` is 1 on `aqv` and `cqv` (the arrows and bolts)
only; `usesound` is blank on `sol`, `j34`, `g34`, `box`. `[L]` the warning columns' readers.

### Belt and stack columns

- `belt` (`+0x130`, u8): 1 on 22 rows (`hpo`, `mpo`, `hpf`, `mpf`, `vps`, `yps`, `rvs`, `rvl`, `wms`, `tsc`, `isc`,
  `hp1`..`hp5`, `mp1`..`mp5`, `hrb`), 0 on the other 129; `autobelt` (`+0x131`, u8): 1 on 14 (`hpo`, `hpf`, `rvs`,
  `rvl`, `hp1`..`hp5`, `mp1`..`mp5`). `[C]` (data) `autobelt` is a subset of `belt`, and the eight stock rows `mpo`, `mpf`, `tsc`, `isc`, `vps`,
  `yps`, `wms`, `hrb` are beltable without it. `[C]` The start-item belt placement runs the potion column search and then boxes 0..3 "when the item record's byte
  `+0x131` is set" (`autobelt`, player/0001); the beltable test itself is
  `ItemTypes.Beltable` ([player/0001 § Placement](../findings/player/0001-creation.md),
  [ItemTypes](ItemTypes.md), fn:sub_0055E9B0_ItemToBelt@0x0055E9B0, fn:sub_0063C600_BeltFreeSlot@0x0063C600).
  `[L]` what `belt` (`+0x130`) selects, and how a belt's size (`Armor.belt`, [Belts](Belts.md)) restricts the boxes.
- `stackable`, `minstack`, `maxstack`, `spawnstack`: 10 stackable rows (`tbk`, `ibk`, `gld`, `aqv`, `cqv`, `key`, `rps`,
  `rpl`, `bps`, `bpl`) with `minstack`/`maxstack`/`spawnstack` 1/20/5, 1/20/5, 0/5000/0, 100/350/200, 60/250/150,
  1/12/6, and 5/10/0 on the four small and large potions. The creation draw is
  [§ base-stat roll](#fields-the-base-stat-roll-reads-plan-0024-phase-1) above; the merge and split rules (the
  largest stack a pickup merges into, the cap by stat 254) are Phase 1.2's `[L]`.
- `[C]` (data) `useable`, `belt`, `autobelt`, `stackable`: 35, 22, 14 and 10 rows with 1; `Books` (3 rows) is
  [Books](Books.md) (the scroll and tome codes, the skills, the tome price). `[L]` `usesound`'s consumer.

## Open questions

- Answered `[I]` by [data/0004](../findings/data/0004-cell-converters.md) (field descriptors and fillers): the four bytes no shipped column fills,
  0 in every record of all three files, are `+0x0F0` = **`gemoffset`** (s32; every cell `0`; `GEMS_Load`
  overwrites it at load: records 0 … nGems−1 get −1, then each gem's item gets its `gems` row),
  `+0x114` = **`missile`** and `+0x122` = **`subtype`** (u8 each, descriptor entries whose columns no
  shipped `.txt` has, so they hold the missing-column default 0), and `+0x123`, `+0x12E` padding (no
  descriptor entry, no reader or writer found). `excel_bin.py diff` now checks `gemoffset`, `missile`
  and `subtype` (0 mismatches). ([data/0004 §3](../findings/data/0004-cell-converters.md#3-runtime-fillers-of-no-column-fields), fn:GEMS_Load@0x00636B70, tbl:Weapons.txt:gemoffset)
- `[I]` Misc `+0x0F0` is read as a Gems row index: the item-colour code passes a socketed gem's record
  `+0x0F0` to `GEMS_GetRecord` and takes the Gems record's colour byte (`+0x2F`). Every `.bin` record holds
  0 there; `GEMS_Load` sets it at load (above). ([items/0003 § 3](../findings/items/0003-item-graphics.md#3-the-colour-decision-itemgfx_getitemshift),
  fn:ITEMGFX_GetItemShift@0x0062C100, fn:GEMS_GetRecord@0x006372C0)
- `[I]` The socket path reads `gemoffset` from the **child's** base record only (the gem or rune put in the socket),
  never from the parent's, to find its Gems row; the parent's `gemapplytype` picks the property group. So the
  community reading of `gemoffset` as "the starting index into `gems.txt`" for an item does not apply to 1.14d.
  ([items/0007 § 3](../findings/items/0007-sockets-runewords.md#3-gems-and-runes-items_attachtoowner-0x0055c2c0),
  fn:ITEMS_AttachToOwner@0x0055C2C0, tbl:Misc.txt:gemoffset)
- Answered: columns compiled nowhere (`quivered`, `special`, `throwable`, `OpenBetaGfx`…)
  are not read in a stock run, because the game loads only the `.bin` `[C]`
  ([data/0001](../findings/data/0001-excel-loader.md#answer-summary)).
- Answered `[I]`: item index order (weapons, armor, misc) and the code→index function
  (`ITEMS_GetByCode` `0x00633640`), see Row identity.
