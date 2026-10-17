# Armor (`data/global/excel/armor.txt`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 202 (203 data rows − 1 `Expansion` marker)   **Record:** 424 B
> **sha256:** `.txt` `d8a4827d52807652f8de33d1b9b335ab8bdd40d1b60b5cbabce24ff9987b30fa`, `.bin` `25dd0a0080b8bf7c44a22f8b5265ff9a0e580fd34eb5718bbfbae0cd1533e7cb`
> **Doc status:** columns listed, `.bin` layout complete (shared item record), semantics pending except [§ Fields the base-stat roll reads](#fields-the-base-stat-roll-reads-plan-0024-phase-1) (`[I]`, plan 0024 Phase 1); vendor columns in [§ Vendor columns](#vendor-columns-plan-0031-phase-0) (plan 0031 Phase 0; `[I]` meanings from items/0009)

## Purpose

One row per armor base item (helms, body armor, shields, gloves, boots, belts, class items). Second
part of the item list (`items/tc`, `items/quality`). The record layout is shared with
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

`[C]` layout tags are by data behaviour: `python3 -I tools/excel_bin.py diff <excel-dir> armor` decodes every record and compares it with every mapped cell (blank cells and encoding rules as in [excel-bin.md](../formats/excel-bin.md#cell-encoding-rules)). A field is tagged `[C]` when the column's values pin its offset (a probe over every record finds no other offset that fits), `[I]` when the column is constant or identical to a sibling column, so its position comes from the neighbouring fields or the stride of its group. Widths are `[C]` with the same proviso; signedness is `[I]` (`s` where the column holds negative values). **Meaning:** no column semantics are claimed here; they come from reverser findings. For the item tables the probe runs over the 659 records of all three files, which share the layout, so a column that is constant in this file can still be `[C]`. `excel_bin.py diff` also checks the 39 layout fields that `armor.txt`
has no column for (7 878 cells, all at the missing-column default).

| Column | Observed type / range | `.bin` field | References | Layout tag |
|---|---|---|---|---|
| `name` | str, 201 distinct, len ≤ 18 | — (editor name; the record holds the namestr string index instead) | — | — |
| `version` | int 0..100 (2 distinct) | `+0x0F6` u16 | — | [C] |
| `compactsave` | int, always 0 | `+0x143` u8 | — | [C] |
| `rarity` | int 1..4 (4 distinct) | `+0x0FC` u8 | — | [C] |
| `spawnable` | int, always 1 | `+0x133` u8 | — | [C] |
| `minac` | int 2..487 (116 distinct) | `+0x0CC` u32 | — | [C] |
| `maxac` | int 2..600 (125 distinct) | `+0x0D0` u32 | — | [C] |
| `absorbs` | int 0..5 (4 distinct) | `+0x10E` u8 | — | [C] |
| `speed` | int 0..10 (3 distinct) | `+0x0D8` s32 | — | [C] |
| `reqstr` | int 0..232 (91 distinct) | `+0x10A` u16 | — | [C] |
| `block` | int 0..30 (18 distinct) | `+0x111` u8 | — | [C] |
| `durability` | int 12..100 (36 distinct) | `+0x112` u8 | — | [C] |
| `nodurability` | int, always 0 | `+0x113` u8 | — | [C] |
| `level` | int 1..85 (71 distinct) | `+0x0FD` u8 | — | [C] |
| `levelreq` | int 0..67 (47 distinct) | `+0x13F` u8 | — | [C] |
| `cost` | int 64..373558 (200 distinct) | `+0x0E0` u32 | — | [C] |
| `gamble cost` | int 3016..4872212 (179 distinct) | `+0x0D4` u32 | — | [C] |
| `code` | str, 202 distinct, len ≤ 3 | `+0x080` char[4] code | — | [C] |
| `namestr` | str, 202 distinct, len ≤ 3 | `+0x0F4` u16 string index | string tables | [C] |
| `magic lvl` | int 3..18 (4 distinct), 198 blank | `+0x140` u8 | — | [C] |
| `auto prefix` | int 304..305 (2 distinct), 172 blank | `+0x0F8` u16 | — | [C] |
| `alternategfx` | str, 54 distinct, len ≤ 3 | `+0x090` char[4] code | — | [C] |
| `OpenBetaGfx` | str, 45 distinct, len ≤ 3 | — (obsolete art code; no field matches) | — | — |
| `normcode` | str, 68 distinct, len ≤ 3 | `+0x084` char[4] code | — | [C] |
| `ubercode` | str, 67 distinct, len ≤ 3 | `+0x088` char[4] code | — | [C] |
| `ultracode` | str, 67 distinct, len ≤ 3 | `+0x08C` char[4] code | — | [C] |
| `spelloffset` | int, always 0 | — (armor: 0 in every row; not located) | — | — |
| `component` | int 0..16 (5 distinct) | `+0x115` u8 | — | [C] |
| `invwidth` | int, always 2 | `+0x10F` u8 | — | [C] |
| `invheight` | int 1..4 (4 distinct) | `+0x110` u8 | — | [C] |
| `hasinv` | int 0..1 (2 distinct) | `+0x137` u8 | — | [C] |
| `gemsockets` | int 0..4 (5 distinct) | `+0x138` u8 | — | [C] |
| `gemapplytype` | int 0..2 (3 distinct) | `+0x13E` u8 | — | [C] |
| `flippyfile` | str, 61 distinct, len ≤ 6 | `+0x000` char[32] | — | [C] |
| `invfile` | str, 70 distinct, len ≤ 6 | `+0x020` char[32] | — | [C] |
| `uniqueinvfile` | str, 22 distinct, len ≤ 7, 161 blank | `+0x040` char[32] | — | [C] |
| `setinvfile` | str, 25 distinct, len ≤ 7, 159 blank | `+0x060` char[32] | — | [C] |
| `rArm` | int 0..2 (3 distinct), 157 blank | `+0x116` u8 | — | [C] |
| `lArm` | int 0..2 (3 distinct), 157 blank | `+0x117` u8 | — | [C] |
| `Torso` | int 0..2 (3 distinct), 157 blank | `+0x118` u8 | — | [C] |
| `Legs` | int 0..2 (3 distinct), 157 blank | `+0x119` u8 | — | [C] |
| `rSPad` | int 1..2 (2 distinct), 157 blank | `+0x11A` u8 | — | [C] |
| `lSPad` | int 0..2 (3 distinct), 157 blank | `+0x11B` u8 | — | [C] |
| `useable` | int, always 0 | `+0x11D` u8 | — | [C] |
| `throwable` | int, always 0 | — (0 in every armor/misc row; not located (weapons.txt has no such column)) | — | — |
| `stackable` | int, always 0 | `+0x132` u8 | — | [C] |
| `minstack` | int, always 0 | `+0x0E4` u32 | — | [C] |
| `maxstack` | int, always 0 | `+0x0E8` u32 | — | [C] |
| `type` | str, 11 distinct, len ≤ 4 | `+0x11E` u16 index | `itemtypes:Code` | [C] |
| `type2` | always blank | `+0x120` u16 index | `itemtypes:Code` | [C] |
| `dropsound` | str, 15 distinct, len ≤ 16 | `+0x124` u16 index | `sounds:Sound` | [C] |
| `dropsfxframe` | int, always 12 | `+0x128` u8 | — | [C] |
| `usesound` | str, 15 distinct, len ≤ 16 | `+0x126` u16 index | `sounds:Sound` | [C] |
| `unique` | int, always 0 | `+0x129` u8 | — | [C] |
| `transparent` | int, always 0 | `+0x12C` u8 | — | [C] |
| `transtbl` | int, always 5 | `+0x12D` u8 | — | [C] |
| `quivered` | int, always 0 | — (weapons: 1 on 42 bows/crossbows, but no byte or bit in the record follows it; not compiled) | — | — |
| `lightradius` | int 0..5 (6 distinct) | `+0x12F` u8 | — | [C] |
| `belt` | int 0..6 (6 distinct) | `+0x130` u8 | — | [C] |
| `quest` | int, always 0 | `+0x12A` u8 | — | [C] |
| `missiletype` | int, always 0 | `+0x0FA` u16 | — | [C] |
| `durwarning` | int 1..6 (6 distinct) | `+0x135` u8 | — | [C] |
| `qntwarning` | int, always 0 | `+0x136` u8 | — | [C] |
| `mindam` | int 0..83 (32 distinct) | `+0x0FE` u8 | — | [C] |
| `maxdam` | int 0..149 (37 distinct) | `+0x0FF` u8 | — | [C] |
| `StrBonus` | int 100..120 (2 distinct), 148 blank | `+0x106` s16 | — | [C] |
| `DexBonus` | always blank | `+0x108` s16 | — | [C] |
| `gemoffset` | int, always 0 | `+0x0F0` s32 (compiled; overwritten at load, see Open questions) | — | [I] |
| `bitfield1` | int 1..3 (2 distinct) | `+0x0DC` u32 | — | [C] |
| `CharsiMin` | int, always 1, 191 blank | `+0x148` u8 | — | [C] |
| `CharsiMax` | int, always 1, 183 blank | `+0x159` u8 | — | [C] |
| `CharsiMagicMin` | int, always 1, 191 blank | `+0x16A` u8 | — | [C] |
| `CharsiMagicMax` | int, always 1, 186 blank | `+0x17B` u8 | — | [C] |
| `CharsiMagicLvl` | int 1..255 (7 distinct) | `+0x18C` u8 | — | [C] |
| `GheedMin` | int, always 1, 199 blank | `+0x147` u8 | — | [C] |
| `GheedMax` | int, always 1, 186 blank | `+0x158` u8 | — | [C] |
| `GheedMagicMin` | always blank | `+0x169` u8 | — | [C] |
| `GheedMagicMax` | int, always 1, 186 blank | `+0x17A` u8 | — | [C] |
| `GheedMagicLvl` | int 1..255 (2 distinct) | `+0x18B` u8 | — | [C] |
| `AkaraMin` | always blank | `+0x146` u8 | — | [C] |
| `AkaraMax` | always blank | `+0x157` u8 | — | [C] |
| `AkaraMagicMin` | always blank | `+0x168` u8 | — | [C] |
| `AkaraMagicMax` | always blank | `+0x179` u8 | — | [C] |
| `AkaraMagicLvl` | int, always 255 | `+0x18A` u8 | — | [C] |
| `FaraMin` | int, always 1, 192 blank | `+0x149` u8 | — | [C] |
| `FaraMax` | int 1..2 (2 distinct), 183 blank | `+0x15A` u8 | — | [C] |
| `FaraMagicMin` | int, always 1, 197 blank | `+0x16B` u8 | — | [C] |
| `FaraMagicMax` | int, always 1, 185 blank | `+0x17C` u8 | — | [C] |
| `FaraMagicLvl` | int 1..255 (2 distinct) | `+0x18D` u8 | — | [C] |
| `LysanderMin` | always blank | `+0x14A` u8 | — | [C] |
| `LysanderMax` | always blank | `+0x15B` u8 | — | [C] |
| `LysanderMagicMin` | always blank | `+0x16C` u8 | — | [C] |
| `LysanderMagicMax` | always blank | `+0x17D` u8 | — | [C] |
| `LysanderMagicLvl` | int, always 255 | `+0x18E` u8 | — | [I] |
| `DrognanMin` | int, always 1, 199 blank | `+0x14B` u8 | — | [C] |
| `DrognanMax` | int, always 2, 199 blank | `+0x15C` u8 | — | [C] |
| `DrognanMagicMin` | int, always 1, 199 blank | `+0x16D` u8 | — | [C] |
| `DrognanMagicMax` | int, always 3, 199 blank | `+0x17E` u8 | — | [C] |
| `DrognanMagicLvl` | int 20..255 (2 distinct) | `+0x18F` u8 | — | [C] |
| `HraltiMin` | int 1..2 (2 distinct), 195 blank | `+0x14C` u8 | — | [C] |
| `HraltiMax` | int 1..2 (2 distinct), 192 blank | `+0x15D` u8 | — | [C] |
| `HraltiMagicMin` | int, always 1, 198 blank | `+0x16E` u8 | — | [C] |
| `HraltiMagicMax` | int, always 1, 194 blank | `+0x17F` u8 | — | [C] |
| `HratliMagicLvl` | int 1..255 (2 distinct) | — (misspelled header in weapons/armor: the field HraltiMagicLvl +0x190 stays 0 (column not found)) | — | — |
| `AlkorMin` | always blank | `+0x14D` u8 | — | [C] |
| `AlkorMax` | always blank | `+0x15E` u8 | — | [C] |
| `AlkorMagicMin` | always blank | `+0x16F` u8 | — | [I] |
| `AlkorMagicMax` | always blank | `+0x180` u8 | — | [I] |
| `AlkorMagicLvl` | int, always 255 | `+0x191` u8 | — | [I] |
| `OrmusMin` | always blank | `+0x14E` u8 | — | [C] |
| `OrmusMax` | int, always 1, 201 blank | `+0x15F` u8 | — | [C] |
| `OrmusMagicMin` | always blank | `+0x170` u8 | — | [C] |
| `OrmusMagicMax` | int, always 1, 198 blank | `+0x181` u8 | — | [C] |
| `OrmusMagicLvl` | int 1..255 (2 distinct) | `+0x192` u8 | — | [C] |
| `ElzixMin` | int, always 1, 189 blank | `+0x14F` u8 | — | [C] |
| `ElzixMax` | int 1..2 (2 distinct), 188 blank | `+0x160` u8 | — | [C] |
| `ElzixMagicMin` | int, always 1, 194 blank | `+0x171` u8 | — | [C] |
| `ElzixMagicMax` | int, always 1, 188 blank | `+0x182` u8 | — | [C] |
| `ElzixMagicLvl` | int 1..255 (2 distinct) | `+0x193` u8 | — | [C] |
| `AshearaMin` | int, always 1, 186 blank | `+0x150` u8 | — | [C] |
| `AshearaMax` | int 1..2 (2 distinct), 186 blank | `+0x161` u8 | — | [C] |
| `AshearaMagicMin` | int, always 1, 195 blank | `+0x172` u8 | — | [C] |
| `AshearaMagicMax` | int, always 1, 183 blank | `+0x183` u8 | — | [C] |
| `AshearaMagicLvl` | int 1..255 (2 distinct) | `+0x194` u8 | — | [C] |
| `CainMin` | int, always 1, 186 blank | `+0x151` u8 | — | [C] |
| `CainMax` | int 1..2 (2 distinct), 186 blank | `+0x162` u8 | — | [C] |
| `CainMagicMin` | int, always 1, 195 blank | `+0x173` u8 | — | [C] |
| `CainMagicMax` | int, always 1, 183 blank | `+0x184` u8 | — | [C] |
| `CainMagicLvl` | int 1..255 (2 distinct) | `+0x195` u8 | — | [C] |
| `HalbuMin` | int, always 1, 193 blank | `+0x152` u8 | — | [C] |
| `HalbuMax` | int, always 1, 193 blank | `+0x163` u8 | — | [C] |
| `HalbuMagicMin` | int, always 1, 187 blank | `+0x174` u8 | — | [C] |
| `HalbuMagicMax` | int, always 1, 186 blank | `+0x185` u8 | — | [C] |
| `HalbuMagicLvl` | int 20..255 (2 distinct) | `+0x196` u8 | — | [C] |
| `JamellaMin` | int, always 1, 190 blank | `+0x153` u8 | — | [C] |
| `JamellaMax` | int, always 1, 189 blank | `+0x164` u8 | — | [C] |
| `JamellaMagicMin` | int, always 1, 200 blank | `+0x175` u8 | — | [C] |
| `JamellaMagicMax` | int, always 1, 192 blank | `+0x186` u8 | — | [C] |
| `JamellaMagicLvl` | int 1..255 (2 distinct) | `+0x197` u8 | — | [C] |
| `LarzukMin` | int, always 1, 195 blank | `+0x155` u8 | — | [C] |
| `LarzukMax` | int, always 1, 193 blank | `+0x166` u8 | — | [C] |
| `LarzukMagicMin` | int, always 1, 186 blank | `+0x177` u8 | — | [C] |
| `LarzukMagicMax` | int 1..2 (2 distinct), 186 blank | `+0x188` u8 | — | [C] |
| `LarzukMagicLvl` | int 20..255 (2 distinct) | `+0x199` u8 | — | [C] |
| `MalahMin` | always blank | `+0x154` u8 | — | [C] |
| `MalahMax` | always blank | `+0x165` u8 | — | [C] |
| `MalahMagicMin` | always blank | `+0x176` u8 | — | [C] |
| `MalahMagicMax` | always blank | `+0x187` u8 | — | [C] |
| `MalahMagicLvl` | int 20..255 (2 distinct) | `+0x198` u8 | — | [C] |
| `DrehyaMin` | int, always 1, 196 blank | `+0x156` u8 | — | [C] |
| `DrehyaMax` | int, always 1, 191 blank | `+0x167` u8 | — | [C] |
| `DrehyaMagicMin` | int, always 1, 197 blank | `+0x178` u8 | — | [C] |
| `DrehyaMagicMax` | int 1..2 (2 distinct), 194 blank | `+0x189` u8 | — | [C] |
| `DrehyaMagicLvl` | int 1..255 (3 distinct) | `+0x19A` u8 | — | [C] |
| `Source Art` | always blank | — (editor note; blank) | — | — |
| `Game Art` | always blank | — (editor note; blank or a single space) | — | — |
| `Transform` | int 0..8 (6 distinct) | `+0x141` u8 | — | [C] |
| `InvTrans` | int 0..8 (4 distinct) | `+0x142` u8 | — | [C] |
| `SkipName` | int, always 0 | `+0x144` u8 | — | [C] |
| `NightmareUpgrade` | str, 35 distinct, len ≤ 3 | `+0x19C` char[4] code | — | [C] |
| `HellUpgrade` | str, 21 distinct, len ≤ 3 | `+0x1A0` char[4] code | — | [C] |
| `mindam#2` | int, always 0 | — (armor.txt repeats the header mindam; the first occurrence feeds +0x0FE, this one is 0 in every row) | — | — |
| `maxdam#2` | int, always 0 | — (armor.txt repeats the header maxdam; the first occurrence feeds +0x0FF, this one is 0 in every row) | — | — |
| `nameable` | int, always 1 | `+0x145` u8 | — | [C] |

- `[C]` `armor.txt` repeats `mindam` and `maxdam` near the end of the header (shown as `mindam#2`,
  `maxdam#2`, 0 in every row). The first occurrence is the one compiled (`+0x0FE`/`+0x0FF`).

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

## Fields the quality roll reads (plan 0010 Phase 0)

The item-record offsets that [items/0002 §1](../findings/items/0002-quality-roll.md#1-arguments-and-early-returns-0x005586400x005586ce) and [§2](../findings/items/0002-quality-roll.md#2-row-selection--itemratio_select-0x00637910)
read, with the `.txt` column behind each; the shared table and its notes are in
[Weapons § Fields the quality roll reads](Weapons.md#fields-the-quality-roll-reads-plan-0010-phase-0).
Counts are computed over `armor.txt`; layout tags are by `excel_bin.py diff` (0 mismatches).

| Offset (items/0002) | `.txt` column | Data in armor | Layout tag |
|---|---|---|---|
| `+0x129` | `unique` | 0 in every row | [C] |
| `quest` (`+0x12A`) | `quest` | 0 in every row | [C] |
| `level` (`+0x0FD`), the qlvl | `level` | 1..85 | [C] |
| `type` (`+0x11E`) | `type` | 11 types, every one with itemtypes `Rare` = 1, none with `Magic` or `Normal` | [C] |
| uber / exceptional flag | **no column** | `code` = `normcode` on 68 items, = `ubercode` on 67, = `ultracode` on 67 | — |
| class-specific flag | **no column** in this table | 60 armors have a `type` whose itemtypes `Class` is set | — |

## Art columns (items/0003)

Column meanings from [items/0003](../findings/items/0003-item-graphics.md) (static, `[I]`); the item art index (`tools/item_art.py`,
[README § Item art index](README.md#item-art-index)) follows them. The cel and shift columns sit in the
record shared with Weapons and Misc.

- `[I]` `component` (`+0x115`) is the worn layer of a non-torso equipped item: a `composit.txt` row (HD 0,
  TR 1, LG 2, RA 3, LA 4, RH 5, LH 6, SH 7, S1 8, S2 9 …); a value above 15 means no layer (stock: 16).
  An item in inventory slot 5 or 6 is drawn on RH (5) or LH (6) whatever its `component`.
  (fn:ITEMS_GetComponent@0x00628660, fn:sub_0063DA70_CompositeItemLayer@0x0063DA70, tbl:Armor.txt:component)
- `[I]` A torso item (body location 3) does not use `component`: it fills six layers from `rArm`, `lArm`,
  `Torso`, `Legs`, `rSPad`, `lSPad` (`+0x116..+0x11B`), each an [armtype](armtype.md) row: `Torso`→TR,
  `Legs`→LG, `rArm`→RA, `lArm`→LA, `rSPad`→S1, `lSPad`→S2. (fn:sub_0063E510_CompositeFromEquip@0x0063E510,
  fn:sub_0064F500_ArmorPartForLayer@0x0064F500, tbl:Armor.txt:Torso)
- `[I]` Inventory cel, first non-empty wins: an identified set item's SetItems `invfile`, then
  `setinvfile` (`+0x060`); an identified unique's UniqueItems `invfile` (row > 0), then `uniqueinvfile`
  (`+0x040`); then, if the item type has `VarInvGfx` > 0, the type's `InvGfx`; then `invfile` (`+0x020`).
  Ground cel: the unique/set row's own `flippyfile`, else `flippyfile` (`+0x000`). (fn:ITEMGFX_SelectCelName@0x004DABC0,
  tbl:Armor.txt:setinvfile, tbl:Armor.txt:uniqueinvfile)
- `[I]` `InvTrans` (`+0x142`) is the shift file type of the inventory icon and `Transform` (`+0x141`) that
  of the ground and worn views ([item-palette.md](../formats/item-palette.md)).
  (fn:ITEMGFX_GetItemShift@0x0062C100, tbl:Armor.txt:Transform, tbl:Armor.txt:InvTrans)

## Fields the base-stat roll reads (plan 0024 Phase 1)

From [items/0006 § 1](../findings/items/0006-properties.md#1-base-stats-sub_00557ab0_iteminitstats-0x00557ab0),
[§ 4](../findings/items/0006-properties.md#4-the-handlers-per-func) and
[§ 6](../findings/items/0006-properties.md#6-ethereal-and-sockets-after-the-switch-0x005579430x005579a3) (static
reading); the data counts are computed over `armor.txt`. The base-stat draws are on the item unit's own seed, before
the quality builder runs; armour draws durability, then defense.

- `[I]` **`durability`.** `cur = ⌊d/2⌋ + RangeB(⌊d/2⌋)` (no draw when `d < 2`; every armour row has `d` ≥ 12), so
  `cur` lies in `[⌊d/2⌋, 2⌊d/2⌋ − 1]`; max durability = `d`. `nodurability` is not tested.
  (fn:sub_00557AB0_ItemInitStats@0x00557AB0, tbl:Armor.txt:durability)
- `[I]` **`minac`, `maxac`.** Defense = `RangeOffset(minac, maxac − minac + 1)`, so `[minac, maxac]` inclusive. No
  row has `maxac` < `minac`; the 4 rows with `minac` = `maxac` still make one draw (width 1).
  (fn:sub_00556360_ItemRollDefense@0x00556360, tbl:Armor.txt:minac, tbl:Armor.txt:maxac)
- `[I]` **`maxac` and `ac%`.** A func-2 property (`ac%`, stat 16) on an armour with `maxac` ≠ 0 resets the base
  defense to `max(defense + 1, maxac + 1)` each time it runs, so a superior, magic or unique armour with `ac%` has
  base defense `maxac + 1` (`maxac + 2` after a second `ac%` block); an ethereal roll then multiplies that by 3/2.
  (fn:sub_0065CCC0_PropBaseReset@0x0065CCC0, fn:sub_00556CA0_ItemRollEthereal@0x00556CA0)
- `[I]` **`hasinv`, `gemsockets` (sockets).** As for weapons ([Weapons](Weapons.md#fields-the-base-stat-roll-reads-plan-0024-phase-1)),
  with one exception: body armour (type `tors`) in a classic game (item version < 100) makes no socket draw.
  157 armour rows have `hasinv` 1 and `gemsockets` > 0. (fn:sub_00556B60_ItemRollSockets@0x00556B60,
  tbl:Armor.txt:gemsockets)

## Vendor columns (plan 0031 Phase 0)

The vendor fields, their offsets, the group order and the survey command are in
[Weapons § Vendor columns](Weapons.md#vendor-columns-plan-0031-phase-0), with their code meanings from
[items/0009](../findings/items/0009-vendors.md). Armor counts
(`[C]`, `python3 -I tools/vendor_survey.py summary` and `bases`):

| Group | bases | magic | magic only | `MagicLvl` on those bases |
|---|---:|---:|---:|---|
| Akara, Lysander, Alkor, Malah | 0 | 0 | 0 | — |
| Gheed | 16 | 16 | 0 | 1 |
| Charsi | 19 | 16 | 0 | 1 (6), 3 (2), 5 (4), 10 (4), 15 (1), 20 (1), 255 (1) |
| Fara | 19 | 17 | 0 | 1 |
| Drognan | 3 | 3 | 0 | 20 |
| Hralti | 10 | 8 | 0 | **0** (dead `HratliMagicLvl` header, [Interpretation notes](#interpretation-notes)) |
| Ormus | 4 | 4 | 3 | 1 |
| Elzix | 14 | 14 | 0 | 1 |
| Asheara | 19 | 19 | 3 | 1 |
| Cain | 19 | 19 | 3 | 1 |
| Halbu | 16 | 16 | 7 | 20 (14), 255 (2) |
| Jamella | 16 | 10 | 3 | 1 (8), 255 (8) |
| Larzuk | 16 | 16 | 7 | 20 |
| Drehya | 12 | 8 | 1 | 20 (5), 1 (3), 255 (4) |

- `[C]` 46 armors have a non-zero vendor byte, all of item `version` 0 (no expansion armor is stocked by these
  columns).
- `[C]` Charsi is the only group with graded `MagicLvl` values on armor (3, 5, 10, 15, 20 besides 1).
- `[C]` 34 armors have a `NightmareUpgrade` and 26 a `HellUpgrade` naming an item; every target is a normal-tier
  base, of the same item type except one nightmare target. `PermStoreItem` and `multibuy` are 0 on every armor.
- `[I]` Every armor has `bitfield1` bit 0 (values 1 and 3), `Nameable` 1 and `compactsave` 0, so every armor passes
  the record tests of Charsi's imbue and Anya's personalization; the item tests are in
  [Weapons § Fields the quest services read](Weapons.md#fields-the-quest-services-read-plan-0032).
  ([items/0010 § 6](../findings/items/0010-quest-drops.md#6-npc-rewards), fn:sub_0062C590_ItemCanImbue@0x0062C590,
  fn:sub_0062C6A0_ItemCanPersonalize@0x0062C6A0, tbl:Armor.txt:bitfield1, tbl:Armor.txt:nameable)

## Combat columns (plan 0037 Phase 0)

The columns the defender's block and the kick and shield damage are expected to read. Offsets are § [Columns](#columns)
(`[C]`, `excel_bin.py diff`); the counts are `python3 -I tools/combat_survey.py items workspace/merged/data/global/excel`
(gate survey `combat`) over the 202 records, `[C]` as data. Meanings `[L]` unless tagged.

| Column | `.bin` field | Non-zero | Values | Tag |
|---|---|---:|---|---|
| `minac`, `maxac` | `+0x0CC`, `+0x0D0` u32 | 202, 202 | 2..487, 2..600 | [C] |
| `block` | `+0x111` u8 | 53 | 0..30 | [C] |
| `absorbs` | `+0x10E` u8 | 18 | 0..5 | [C] |
| `speed` | `+0x0D8` s32 | 36 | 0..10 | [C] |
| `mindam`, `maxdam` | `+0x0FE`, `+0x0FF` u8 | 54, 54 | 0..83, 0..149 | [C] |
| `StrBonus` | `+0x106` s16 | 54 | 100..120 | [C] |
| `DexBonus` | `+0x108` s16 | 0 | always blank | [C] |
| `reqstr` | `+0x10A` u16 | 192 | 0..232 | [C] |

- `[C]` `block` is non-zero on 53 rows: shields `shie` 23, paladin shields `ashd` 15 and necromancer heads `head` 15
  (`ne1`..`nef`). (tbl:Armor.txt:block)
- `[C]` `mindam`/`maxdam` are non-zero on 54 rows, the same 54 that have `StrBonus`: shields `shie` 24, `ashd` 15 and
  boots `boot` 15. (tbl:Armor.txt:mindam, tbl:Armor.txt:StrBonus)
- `[L]` By the names, `block` is the shield's block chance, the shield damage feeds a shield attack (Smite) and the
  boot damage the kick; `absorbs` has no known reader. Plan 0037 Phase 1.

## Economy (plan 0043 Phase 0)

The fields, their offsets, the readers named so far and the survey command are in
[Weapons § Economy](Weapons.md#economy-plan-0043-phase-0); every price, repair and wear meaning is `[L]`. Armor rows
(`[C]`, `python3 -I tools/economy_survey.py items` and `types`, gate survey `economy`):

- `[C]` `cost` 64..373 558 (200 distinct) and `gamble cost` 3 016..4 872 212 (179 distinct) are set on all 202 rows.
  **`cost` is above `gamble cost` on 5 rows**, the elite class shields and heads `pac`, `pad`, `pae`, `paf` (85 659..139 860
  against 82 066..82 069) and `nef` (86 238 against 82 073); none of the five is on the gamble list.
- `[C]` `durability` 12..100 on every row, `nodurability` 0 on every row; `durwarning` takes six values (1 ×39,
  2 ×45, 3 ×73, 4 ×15, 5 ×15, 6 ×15). No stack, `qntwarning`, `multibuy` or `quest` cell is set.
- `[C]` Every armor's own `type` has `Repair` 1 (202 of 202), and none is `Throwable`.
- `[C]` `CostFormula` 1 is set on seven armor types and no other: `shie`, `tors`, `boot`, `glov`, `belt`, `helm`,
  `circ` (the one 2 is on `body`, the misc body parts;
  [ItemTypes § Repair and throwing columns](ItemTypes.md#repair-and-throwing-columns-plan-0043-phase-0)).

## Open questions

- Answered `[I]` by [data/0004](../findings/data/0004-cell-converters.md) (field descriptors and fillers): the four bytes no shipped column fills,
  0 in every record of all three files, are `+0x0F0` = **`gemoffset`** (s32; every cell `0`; `GEMS_Load`
  overwrites it at load: records 0 … nGems−1 get −1, then each gem's item gets its `gems` row),
  `+0x114` = **`missile`** and `+0x122` = **`subtype`** (u8 each, descriptor entries whose columns no
  shipped `.txt` has, so they hold the missing-column default 0), and `+0x123`, `+0x12E` padding (no
  descriptor entry, no reader or writer found). `excel_bin.py diff` now checks `gemoffset`, `missile`
  and `subtype` (0 mismatches). ([data/0004 §3](../findings/data/0004-cell-converters.md#3-runtime-fillers-of-no-column-fields), fn:GEMS_Load@0x00636B70, tbl:Weapons.txt:gemoffset)
- Answered: columns compiled nowhere (`quivered`, `special`, `throwable`, `OpenBetaGfx`…)
  are not read in a stock run, because the game loads only the `.bin` `[C]`
  ([data/0001](../findings/data/0001-excel-loader.md#answer-summary)).
- Answered `[I]`: item index order (weapons, armor, misc) and the code→index function
  (`ITEMS_GetByCode` `0x00633640`), see Row identity.
