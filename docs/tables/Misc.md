# Misc (`data/global/excel/misc.txt`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 151 (152 data rows − 1 `Expansion` marker)   **Record:** 424 B
> **sha256:** `.txt` `f7fa37ae4f7cdb3f5337a28a55b3876fc27aef066822b3268933e56b636b50f0`, `.bin` `4c0b0e6c2f888847b7a71225d15caf8708c1dd33a9cc8420b6cbbf594963bc1b`
> **Doc status:** columns listed, `.bin` layout complete (shared item record), semantics pending

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

`[C]` layout tags are by data behaviour: `python3 -I tools/excel_bin.py diff <excel-dir> misc` decodes every record and compares it with every mapped cell (blank cells and encoding rules as in [excel-bin.md](../formats/excel-bin.md#cell-encoding-rules)). A field is tagged `[C]` when the column's values pin its offset (a probe over every record finds no other offset that fits), `[I]` when the column is constant or identical to a sibling column, so its position comes from the neighbouring fields or the stride of its group. Widths are `[C]` with the same proviso; signedness is `[I]` (`s` where the column holds negative values). **Meaning:** no column semantics are claimed here; they come from reverser findings. For the item tables the probe runs over the 659 records of all three files, which share the layout, so a column that is constant in this file can still be `[C]`. `excel_bin.py diff` also checks the 31 layout fields that `misc.txt`
has no column for (4 681 cells, all at the missing-column default).

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
| `gemoffset` | int, always 0 | — (0 in every row; not located) | — | — |
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

## Fields the quality roll reads (plan 0010 Phase 0)

The item-record offsets that [items/0001 §10](../findings/items/0001-tc-resolution.md#10-the-quality-roll-as-seen-from-the-resolver-sub_00558640_droprollquality)
quotes, with the `.txt` column behind each; the shared table and its notes are in
[Weapons § Fields the quality roll reads](Weapons.md#fields-the-quality-roll-reads-plan-0010-phase-0).
Counts are computed over `misc.txt`; layout tags are by `excel_bin.py diff` (0 mismatches).

| Offset (§10) | `.txt` column | Data in misc | Layout tag |
|---|---|---|---|
| `+0x129` | `unique` | 1 on 10 items, all of type `ques`: `bks`, `bkd`, `j34`, `g34`, `bbb`, `tr1`, `mss`, `ass`, `tr2`, `std` | [C] |
| `quest` (`+0x12A`) | `quest` | 5..32 on 17 items: 9 of the 10 above (not `std`, Standard of Heroes) plus `vip`, `luv`, `xyz`, `box`, `qey`, `qhr`, `qbr`, `ice` | [C] |
| `level` (`+0x0FD`), the qlvl | `level` | 0..90 | [C] |
| `type` (`+0x11E`) | `type` | 32 types. 115 items have a `type` with itemtypes `Normal` = 1; 7 (`amu`, `vip`, `rin`, `cm1`..`cm3`, `jew`) one with `Magic` = 1; 4 of those 7 (`amu`, `vip`, `rin`, `jew`) one with `Rare` = 1 | [C] |
| uber / exceptional flag | **no column** | `misc.txt` has no `normcode`/`ubercode`/`ultracode`; the three fields are 4 spaces (blank) in every record | — |
| class-specific flag | **no column** in this table | no misc `type` has itemtypes `Class` set | — |

- `[C]` `vip` (Amulet of the Viper) is the only item in the three files with `quest` > 0 whose `type`
  has itemtypes `Magic` = 1, the combination §10 reads as an early return to quality 7. No item with
  `unique` = 1 has a `type` with itemtypes `Normal` = 1. (tbl:Misc.txt:quest, tbl:ItemTypes.txt:Magic)

## Open questions

- `[L]` Unknown fields `+0x0F0` (u32), `+0x114`, `+0x122` (u16), `+0x12E`: 0 in every record of all
  three files. Runtime-filled? (backlog → reverser.)
- Answered: columns compiled nowhere (`quivered`, `special`, `gemoffset`, `throwable`, `OpenBetaGfx`…)
  are not read in a stock run, because the game loads only the `.bin` `[C]`
  ([data/0001](../findings/data/0001-excel-loader.md#answer-summary)).
- Answered `[I]`: item index order (weapons, armor, misc) and the code→index function
  (`ITEMS_GetByCode` `0x00633640`), see Row identity.
