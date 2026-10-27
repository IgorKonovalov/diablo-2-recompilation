# Weapons (`data/global/excel/weapons.txt`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 306 (307 data rows − 1 `Expansion` marker)   **Record:** 424 B
> **sha256:** `.txt` `05a938e3fc0b8974bc722bfa8974f44e45e99d19c6877613ff731104b12b3536`, `.bin` `70f6677a8b2c019795d172dd9c90deea4663249504b85c65121da9c917e00983`
> **Doc status:** columns listed, `.bin` layout complete (shared item record), semantics pending except [§ Fields the base-stat roll reads](#fields-the-base-stat-roll-reads-plan-0024-phase-1) (`[I]`, plan 0024 Phase 1); vendor columns in [§ Vendor columns](#vendor-columns-plan-0031-phase-0) (plan 0031 Phase 0; `[I]` meanings from items/0009)

## Purpose

One row per weapon base item: graphics, codes, damage, requirements, prices, vendor stock and the
item type it belongs to. With [Armor](Armor.md) and [Misc](Misc.md) it forms the item list that
treasure classes draw from (`items/tc`, `items/quality`).

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

`[C]` layout tags are by data behaviour: `python3 -I tools/excel_bin.py diff <excel-dir> weapons` decodes every record and compares it with every mapped cell (blank cells and encoding rules as in [excel-bin.md](../formats/excel-bin.md#cell-encoding-rules)). A field is tagged `[C]` when the column's values pin its offset (a probe over every record finds no other offset that fits), `[I]` when the column is constant or identical to a sibling column, so its position comes from the neighbouring fields or the stride of its group. Widths are `[C]` with the same proviso; signedness is `[I]` (`s` where the column holds negative values). **Meaning:** no column semantics are claimed here; they come from reverser findings. For the item tables the probe runs over the 659 records of all three files, which share the layout, so a column that is constant in this file can still be `[C]`. `excel_bin.py diff` also checks the 35 layout fields that
`weapons.txt` has no column for (10 710 cells, all at the missing-column default).

| Column | Observed type / range | `.bin` field | References | Layout tag |
|---|---|---|---|---|
| `name` | str, 306 distinct, len ≤ 21 | — (editor name; the record holds the namestr string index instead) | — | — |
| `type` | str, 23 distinct, len ≤ 4 | `+0x11E` u16 index | `itemtypes:Code` | [C] |
| `type2` | always blank | `+0x120` u16 index | `itemtypes:Code` | [C] |
| `code` | str, 306 distinct, len ≤ 3 | `+0x080` char[4] code | — | [C] |
| `alternateGfx` | str, 57 distinct, len ≤ 3 | `+0x090` char[4] code | — | [C] |
| `namestr` | str, 306 distinct, len ≤ 3 | `+0x0F4` u16 string index | string tables | [C] |
| `version` | int 0..100 (2 distinct) | `+0x0F6` u16 | — | [C] |
| `compactsave` | always blank | `+0x143` u8 | — | [C] |
| `rarity` | int 1..5 (5 distinct), 15 blank | `+0x0FC` u8 | — | [C] |
| `spawnable` | int, always 1, 9 blank | `+0x133` u8 | — | [C] |
| `mindam` | int 0..50 (45 distinct), 119 blank | `+0x0FE` u8 | — | [C] |
| `maxdam` | int 1..80 (70 distinct), 119 blank | `+0x0FF` u8 | — | [C] |
| `1or2handed` | int, always 1, 288 blank | `+0x13D` u8 | — | [C] |
| `2handed` | int, always 1, 169 blank | `+0x11C` u8 | — | [C] |
| `2handmindam` | int 1..83 (59 distinct), 169 blank | `+0x102` u8 | — | [C] |
| `2handmaxdam` | int 4..180 (90 distinct), 169 blank | `+0x103` u8 | — | [C] |
| `minmisdam` | int 4..40 (20 distinct), 276 blank | `+0x100` u8 | — | [C] |
| `maxmisdam` | int 9..85 (24 distinct), 276 blank | `+0x101` u8 | — | [C] |
| `#col18` | int 13..19 (5 distinct), 140 blank | — (unnamed weapons.txt column 18 (values 13..19); not compiled) | — | — |
| `rangeadder` | int 1..4 (4 distinct), 135 blank | `+0x104` s16 | — | [C] |
| `speed` | int -60..20 (10 distinct), 105 blank | `+0x0D8` s32 | — | [C] |
| `StrBonus` | int 75..110 (4 distinct), 48 blank | `+0x106` s16 | — | [C] |
| `DexBonus` | int 50..100 (3 distinct), 195 blank | `+0x108` s16 | — | [C] |
| `reqstr` | int 15..253 (118 distinct), 51 blank | `+0x10A` u16 | — | [C] |
| `reqdex` | int 15..188 (93 distinct), 106 blank | `+0x10C` u16 | — | [C] |
| `durability` | int 0..72 (41 distinct) | `+0x112` u8 | — | [C] |
| `nodurability` | int, always 1, 257 blank | `+0x113` u8 | — | [C] |
| `level` | int 0..86 (85 distinct) | `+0x0FD` u8 | — | [C] |
| `levelreq` | int 0..66 (54 distinct) | `+0x13F` u8 | — | [C] |
| `cost` | int 5..33375 (260 distinct) | `+0x0E0` u32 | — | [C] |
| `gamble cost` | int 0..2644750 (282 distinct) | `+0x0D4` u32 | — | [C] |
| `magic lvl` | int, always 1, 268 blank | `+0x140` u8 | — | [C] |
| `auto prefix` | int 300..303 (3 distinct), 276 blank | `+0x0F8` u16 | — | [C] |
| `OpenBetaGfx` | str, 51 distinct, len ≤ 3 | — (obsolete art code; no field matches) | — | — |
| `normcode` | str, 110 distinct, len ≤ 3 | `+0x084` char[4] code | — | [C] |
| `ubercode` | str, 97 distinct, len ≤ 3, 15 blank | `+0x088` char[4] code | — | [C] |
| `ultracode` | str, 97 distinct, len ≤ 3, 15 blank | `+0x08C` char[4] code | — | [C] |
| `wclass` | str, 7 distinct, len ≤ 3 | `+0x0C0` char[4] code | — | [C] |
| `2handedwclass` | str, 8 distinct, len ≤ 3 | `+0x0C4` char[4] code | — | [C] |
| `component` | int 5..6 (2 distinct) | `+0x115` u8 | — | [C] |
| `hit class` | str, 11 distinct, len ≤ 4 | `+0x13C` u8 index | `hitclass:Code` | [C] |
| `invwidth` | int 1..2 (2 distinct) | `+0x10F` u8 | — | [C] |
| `invheight` | int 1..4 (4 distinct) | `+0x110` u8 | — | [C] |
| `stackable` | int, always 1, 270 blank | `+0x132` u8 | — | [C] |
| `minstack` | int 3..40 (9 distinct), 270 blank | `+0x0E4` u32 | — | [C] |
| `maxstack` | int 20..200 (13 distinct), 270 blank | `+0x0E8` u32 | — | [C] |
| `spawnstack` | int 6..80 (9 distinct), 270 blank | `+0x0EC` u32 | — | [C] |
| `flippyfile` | str, 102 distinct, len ≤ 6 | `+0x000` char[32] | — | [C] |
| `invfile` | str, 109 distinct, len ≤ 6 | `+0x020` char[32] | — | [C] |
| `uniqueinvfile` | str, 52 distinct, len ≤ 7, 196 blank | `+0x040` char[32] | — | [C] |
| `setinvfile` | str, 52 distinct, len ≤ 7, 196 blank | `+0x060` char[32] | — | [C] |
| `hasinv` | int, always 1, 41 blank | `+0x137` u8 | — | [C] |
| `gemsockets` | int 1..6 (6 distinct), 41 blank | `+0x138` u8 | — | [C] |
| `gemapplytype` | int, always 0 | `+0x13E` u8 | — | [C] |
| `special` | str, 6 distinct, len ≤ 27, 187 blank | — (free-text note ("primarily thrown", ...); not compiled) | — | — |
| `useable` | int, always 0 | `+0x11D` u8 | — | [C] |
| `dropsound` | str, 11 distinct, len ≤ 21 | `+0x124` u16 index | `sounds:Sound` | [C] |
| `dropsfxframe` | int 12..14 (2 distinct) | `+0x128` u8 | — | [C] |
| `usesound` | str, 11 distinct, len ≤ 21 | `+0x126` u16 index | `sounds:Sound` | [C] |
| `unique` | int 0..1 (2 distinct) | `+0x129` u8 | — | [C] |
| `transparent` | int, always 0 | `+0x12C` u8 | — | [C] |
| `transtbl` | int, always 5 | `+0x12D` u8 | — | [C] |
| `quivered` | int 0..1 (2 distinct) | — (weapons: 1 on 42 bows/crossbows, but no byte or bit in the record follows it; not compiled) | — | — |
| `lightradius` | int 0..5 (3 distinct) | `+0x12F` u8 | — | [C] |
| `belt` | int, always 0 | `+0x130` u8 | — | [C] |
| `quest` | int 1..25 (6 distinct), 297 blank | `+0x12A` u8 | — | [C] |
| `questdiffcheck` | int, always 1, 297 blank | `+0x12B` u8 | — | [C] |
| `missiletype` | int 0..371 (13 distinct) | `+0x0FA` u16 | — | [C] |
| `durwarning` | int, always 7 | `+0x135` u8 | — | [C] |
| `qntwarning` | int 0..5 (5 distinct) | `+0x136` u8 | — | [C] |
| `gemoffset` | int, always 0 | `+0x0F0` s32 (compiled; overwritten at load, see Open questions) | — | [I] |
| `bitfield1` | int 0..5 (4 distinct) | `+0x0DC` u32 | — | [C] |
| `CharsiMin` | int 1..2 (2 distinct), 290 blank | `+0x148` u8 | — | [C] |
| `CharsiMax` | int 1..3 (3 distinct), 285 blank | `+0x159` u8 | — | [C] |
| `CharsiMagicMin` | int, always 1, 296 blank | `+0x16A` u8 | — | [C] |
| `CharsiMagicMax` | int, always 1, 288 blank | `+0x17B` u8 | — | [C] |
| `CharsiMagicLvl` | int 1..255 (2 distinct) | `+0x18C` u8 | — | [C] |
| `GheedMin` | int, always 1, 287 blank | `+0x147` u8 | — | [C] |
| `GheedMax` | int 1..2 (2 distinct), 286 blank | `+0x158` u8 | — | [C] |
| `GheedMagicMin` | int, always 1, 289 blank | `+0x169` u8 | — | [C] |
| `GheedMagicMax` | int 1..2 (2 distinct), 289 blank | `+0x17A` u8 | — | [C] |
| `GheedMagicLvl` | int 1..255 (4 distinct) | `+0x18B` u8 | — | [C] |
| `AkaraMin` | int 1..5 (4 distinct), 301 blank | `+0x146` u8 | — | [C] |
| `AkaraMax` | int 2..9 (5 distinct), 301 blank | `+0x157` u8 | — | [C] |
| `AkaraMagicMin` | int 1..7 (4 distinct), 301 blank | `+0x168` u8 | — | [C] |
| `AkaraMagicMax` | int 1..9 (4 distinct), 301 blank | `+0x179` u8 | — | [C] |
| `AkaraMagicLvl` | int 1..255 (2 distinct) | `+0x18A` u8 | — | [C] |
| `FaraMin` | int, always 1, 283 blank | `+0x149` u8 | — | [C] |
| `FaraMax` | int, always 1, 276 blank | `+0x15A` u8 | — | [C] |
| `FaraMagicMin` | int 1..2 (2 distinct), 283 blank | `+0x16B` u8 | — | [C] |
| `FaraMagicMax` | int 1..2 (2 distinct), 275 blank | `+0x17C` u8 | — | [C] |
| `FaraMagicLvl` | int 20..255 (3 distinct) | `+0x18D` u8 | — | [C] |
| `LysanderMin` | always blank | `+0x14A` u8 | — | [C] |
| `LysanderMax` | always blank | `+0x15B` u8 | — | [C] |
| `LysanderMagicMin` | always blank | `+0x16C` u8 | — | [C] |
| `LysanderMagicMax` | always blank | `+0x17D` u8 | — | [C] |
| `LysanderMagicLvl` | int, always 255 | `+0x18E` u8 | — | [I] |
| `DrognanMin` | int 1..3 (3 distinct), 299 blank | `+0x14B` u8 | — | [C] |
| `DrognanMax` | int 2..5 (3 distinct), 299 blank | `+0x15C` u8 | — | [C] |
| `DrognanMagicMin` | int 1..5 (3 distinct), 299 blank | `+0x16D` u8 | — | [C] |
| `DrognanMagicMax` | int 1..9 (5 distinct), 296 blank | `+0x17E` u8 | — | [C] |
| `DrognanMagicLvl` | int 1..255 (2 distinct), 1 blank | `+0x18F` u8 | — | [C] |
| `HraltiMin` | int, always 1, 289 blank | `+0x14C` u8 | — | [C] |
| `HraltiMax` | int, always 1, 286 blank | `+0x15D` u8 | — | [C] |
| `HraltiMagicMin` | int, always 1, 290 blank | `+0x16E` u8 | — | [C] |
| `HraltiMagicMax` | int 1..2 (2 distinct), 286 blank | `+0x17F` u8 | — | [C] |
| `HratliMagicLvl` | int 20..255 (2 distinct) | — (misspelled header in weapons/armor: the field HraltiMagicLvl +0x190 stays 0 (column not found)) | — | — |
| `AlkorMin` | always blank | `+0x14D` u8 | — | [C] |
| `AlkorMax` | always blank | `+0x15E` u8 | — | [C] |
| `AlkorMagicMin` | always blank | `+0x16F` u8 | — | [I] |
| `AlkorMagicMax` | always blank | `+0x180` u8 | — | [I] |
| `AlkorMagicLvl` | int, always 255 | `+0x191` u8 | — | [I] |
| `OrmusMin` | int 1..3 (3 distinct), 297 blank | `+0x14E` u8 | — | [C] |
| `OrmusMax` | int 1..5 (4 distinct), 296 blank | `+0x15F` u8 | — | [C] |
| `OrmusMagicMin` | int 1..5 (4 distinct), 300 blank | `+0x170` u8 | — | [C] |
| `OrmusMagicMax` | int 1..7 (4 distinct), 293 blank | `+0x181` u8 | — | [C] |
| `OrmusMagicLvl` | int 1..255 (2 distinct) | `+0x192` u8 | — | [C] |
| `ElzixMin` | int 1..2 (2 distinct), 281 blank | `+0x14F` u8 | — | [C] |
| `ElzixMax` | int 1..2 (2 distinct), 280 blank | `+0x160` u8 | — | [C] |
| `ElzixMagicMin` | int, always 1, 299 blank | `+0x171` u8 | — | [C] |
| `ElzixMagicMax` | int, always 1, 286 blank | `+0x182` u8 | — | [C] |
| `ElzixMagicLvl` | int 1..255 (3 distinct) | `+0x193` u8 | — | [C] |
| `AshearaMin` | int, always 1, 290 blank | `+0x150` u8 | — | [C] |
| `AshearaMax` | int 1..2 (2 distinct), 285 blank | `+0x161` u8 | — | [C] |
| `AshearaMagicMin` | int, always 1, 300 blank | `+0x172` u8 | — | [C] |
| `AshearaMagicMax` | int, always 1, 293 blank | `+0x183` u8 | — | [C] |
| `AshearaMagicLvl` | int 1..255 (3 distinct) | `+0x194` u8 | — | [C] |
| `CainMin` | int 1..2 (2 distinct), 292 blank | `+0x151` u8 | — | [C] |
| `CainMax` | int 1..3 (3 distinct), 288 blank | `+0x162` u8 | — | [C] |
| `CainMagicMin` | int, always 1, 301 blank | `+0x173` u8 | — | [C] |
| `CainMagicMax` | int, always 1, 295 blank | `+0x184` u8 | — | [C] |
| `CainMagicLvl` | int 1..255 (2 distinct) | `+0x195` u8 | — | [C] |
| `HalbuMin` | int, always 1, 290 blank | `+0x152` u8 | — | [C] |
| `HalbuMax` | int 1..2 (2 distinct), 287 blank | `+0x163` u8 | — | [C] |
| `HalbuMagicMin` | int 1..2 (2 distinct), 283 blank | `+0x174` u8 | — | [C] |
| `HalbuMagicMax` | int 1..3 (3 distinct), 282 blank | `+0x185` u8 | — | [C] |
| `HalbuMagicLvl` | int 20..255 (2 distinct) | `+0x196` u8 | — | [C] |
| `JamellaMin` | int 1..3 (3 distinct), 290 blank | `+0x153` u8 | — | [C] |
| `JamellaMax` | int 1..4 (4 distinct), 289 blank | `+0x164` u8 | — | [C] |
| `JamellaMagicMin` | int 1..2 (2 distinct), 292 blank | `+0x175` u8 | — | [C] |
| `JamellaMagicMax` | int 1..3 (3 distinct), 291 blank | `+0x186` u8 | — | [C] |
| `JamellaMagicLvl` | int 20..255 (2 distinct) | `+0x197` u8 | — | [C] |
| `LarzukMin` | int, always 1, 298 blank | `+0x155` u8 | — | [C] |
| `LarzukMax` | int, always 1, 293 blank | `+0x166` u8 | — | [C] |
| `LarzukMagicMin` | int, always 1, 290 blank | `+0x177` u8 | — | [C] |
| `LarzukMagicMax` | int 1..3 (3 distinct), 290 blank | `+0x188` u8 | — | [C] |
| `LarzukMagicLvl` | int 20..255 (2 distinct) | `+0x199` u8 | — | [C] |
| `DrehyaMin` | int, always 1, 305 blank | `+0x156` u8 | — | [C] |
| `DrehyaMax` | int, always 1, 305 blank | `+0x167` u8 | — | [C] |
| `DrehyaMagicMin` | int, always 1, 299 blank | `+0x178` u8 | — | [C] |
| `DrehyaMagicMax` | int, always 1, 299 blank | `+0x189` u8 | — | [C] |
| `DrehyaMagicLvl` | int 20..255 (2 distinct) | `+0x19A` u8 | — | [C] |
| `MalahMin` | int 1..3 (3 distinct), 293 blank | `+0x154` u8 | — | [C] |
| `MalahMax` | int 1..4 (4 distinct), 293 blank | `+0x165` u8 | — | [C] |
| `MalahMagicMin` | int 1..2 (2 distinct), 288 blank | `+0x176` u8 | — | [C] |
| `MalahMagicMax` | int 1..4 (4 distinct), 288 blank | `+0x187` u8 | — | [C] |
| `MalahMagicLvl` | int 20..255 (2 distinct) | `+0x198` u8 | — | [C] |
| `Source Art` | always blank | — (editor note; blank) | — | — |
| `Game Art` | always blank | — (editor note; blank or a single space) | — | — |
| `Transform` | int 0..5 (4 distinct) | `+0x141` u8 | — | [C] |
| `InvTrans` | int 0..8 (3 distinct) | `+0x142` u8 | — | [C] |
| `SkipName` | int 0..1 (2 distinct) | `+0x144` u8 | — | [C] |
| `NightmareUpgrade` | str, 45 distinct, len ≤ 3 | `+0x19C` char[4] code | — | [C] |
| `HellUpgrade` | str, 38 distinct, len ≤ 3 | `+0x1A0` char[4] code | — | [C] |
| `Nameable` | int 0..1 (2 distinct) | `+0x145` u8 | — | [C] |
| `PermStoreItem` | int 0..1 (2 distinct) | `+0x1A4` u8 | — | [C] |

`#col18` is the unnamed column between `maxmisdam` and `rangeadder` (values 13..19 or blank).

## Record layout (424 bytes, shared by weapons, armor and misc)

`[C]` All three item tables compile to the **same 424-byte record**. Each `.txt` has only part of the
columns; the rest of the record holds the [missing-column default](../formats/excel-bin.md#columns-are-found-by-name)
(0, or −1 for index and calc fields), checked over every record. The full field list, with every
offset, is the union of the Columns tables in [Weapons.md](Weapons.md), [Armor.md](Armor.md) and
[Misc.md](Misc.md); the layout is `ITEM_FIELDS` in `tools/excel_layouts.py`.

| range | content |
|---|---|
| `+0x000`..`+0x07F` | `flippyfile`, `invfile`, `uniqueinvfile`, `setinvfile` (`char[32]` each) |
| `+0x080`..`+0x093` | codes: `code`, `normcode`, `ubercode`, `ultracode`, `alternategfx` |
| `+0x094`..`+0x0BB` | misc use effects: `pSpell` u32, `state`/`cstate1`/`cstate2` (u16 → states), `stat1..3` (u16 → itemstatcost), `calc1..3`, `len` (s32 → `itemscode.bin`), `spelldesc` u16, `spelldescstr` (string index), `spelldesccalc` |
| `+0x0BC`..`+0x0CB` | codes: `BetterGem`, `wclass`, `2handedwclass`, `TMogType` |
| `+0x0CC`..`+0x0EF` | u32: `minac`, `maxac`, `gamble cost`, `speed`, `bitfield1`, `cost`, `minstack`, `maxstack`, `spawnstack` |
| `+0x0F0` | `gemoffset` s32, 0 in every record (overwritten at load) |
| `+0x0F4` | `namestr` string index (u16) |
| `+0x0F6`..`+0x10D` | `version`, `auto prefix`, `missiletype` (u16), `rarity`, `level`, damage bytes, `rangeadder`, `StrBonus`, `DexBonus`, `reqstr`, `reqdex` (u16) |
| `+0x10E`..`+0x145` | one byte each: `absorbs` … `Nameable`, with `type`/`type2` (u16 → itemtypes) at `+0x11E`/`+0x120`, `dropsound`/`usesound` (u16 → sounds) at `+0x124`/`+0x126`, `hit class` (u8 → hitclass) at `+0x13C`; `missile` u8 at `+0x114` and `subtype` u8 at `+0x122` (columns no shipped `.txt` has), padding `+0x123`, `+0x12E`; all four 0 in every record |
| `+0x146`..`+0x19A` | vendor bytes: `<Vendor>Min` at `+0x146 + v`, `Max` `+0x157 + v`, `MagicMin` `+0x168 + v`, `MagicMax` `+0x179 + v`, `MagicLvl` `+0x18A + v`, with v = 0..16 in the order Akara, Gheed, Charsi, Fara, Lysander, Drognan, Hralti, Alkor, Ormus, Elzix, Asheara, Cain, Halbu, Jamella, Malah, Larzuk, Drehya |
| `+0x19B` | 0 in every record |
| `+0x19C`..`+0x1A5` | `NightmareUpgrade`, `HellUpgrade` (codes), `PermStoreItem`, `multibuy` (u8) |
| `+0x1A6`..`+0x1A7` | 0 in every record |

- `[C]` Vendor order is the stride above (17 vendors × 5 columns), pinned by the vendors whose columns
  vary; the columns that are constant in every file (`LysanderMagicLvl`, `AlkorMagicMin`, `AlkorMagicMax`,
  `AlkorMagicLvl`) are placed by the stride `[I]`.

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

- `[C]` `quivered` is 1 on 42 bows and crossbows, but no byte or bit of the record follows it: it is
  not compiled.

## Fields the quality roll reads (plan 0010 Phase 0)

The item-record offsets that [items/0002 §1](../findings/items/0002-quality-roll.md#1-arguments-and-early-returns-0x005586400x005586ce) and [§2](../findings/items/0002-quality-roll.md#2-row-selection--itemratio_select-0x00637910)
read in `ITEMS_DropRollQuality`, with the `.txt` column behind each. Layout tags are by
`excel_bin.py diff` (0 mismatches over the 306 records, and over the 659 records of the three item
files); the counts are computed over `weapons.txt`. What the roll does with each field is the reverser's
([items/0002](../findings/items/0002-quality-roll.md), plan 0010 Phase 1).

| Offset (items/0002) | `.txt` column | Data in weapons | Layout tag |
|---|---|---|---|
| `+0x129` (forces unique on a drop, items/0002 `[I]`) | `unique` | 1 on 8 items: `d33`, `g33` (Gidbinn), `hdm`, `hfh` (Horadric Malus, Hellforge Hammer), `hst`, `msf` (Horadric Staff, Staff of Kings), `qf1`, `qf2` (Khalim's Flail, Will) | [C] |
| `quest` (`+0x12A`) | `quest` | 1..25 on 9 items: the 8 above plus `leg` (Wirt's Leg, `unique` 0) | [C] |
| `level` (`+0x0FD`), the qlvl | `level` | 0..86 | [C] |
| `type` (`+0x11E`), whose itemtypes `+0x14`/`+0x15`/`+0x16` the roll tests | `type` | 23 types; see [ItemTypes § Fields the quality roll reads](ItemTypes.md#fields-the-quality-roll-reads-plan-0010-phase-0) | [C] |
| uber / exceptional flag | **no column** | no byte of the record holds a tier flag: the bytes no shipped column fills (`+0x0F0` `gemoffset`, `+0x114` `missile`, `+0x122` `subtype`, padding `+0x123`/`+0x12E`) are 0 in every record. The tier shows only in the codes: `code` = `normcode` on 110 items, = `ubercode` on 97, = `ultracode` on 97, none of them on 2 (`qf1`, `qf2`, whose `normcode` is `fla`) | — |
| class-specific flag | **no column** in this table | 51 weapons have a `type` whose itemtypes `Class` (`+0x21`) is set (ItemTypes) | — |

- `[C]` Every `unique` = 1 weapon also has `quest` > 0 and `questdiffcheck` 1. (tbl:Weapons.txt:unique, tbl:Weapons.txt:quest)
- `[I]` The keys are computed, not stored: an item is uber when it is a `weap`/`armo` whose `ubercode` or
  `ultracode` equals its own `code`, its type is not `tpot` and its `quest` is 0 (194 weapons and 134 armors by
  the data); it is class-specific when its own `type` has itemtypes `Class` < 7. (fn:sub_0062B4D0_ItemRatioUber@0x0062B4D0,
  fn:ITEMS_IsClassSpecific@0x00629F70, [items/0002 §2](../findings/items/0002-quality-roll.md#2-row-selection--itemratio_select-0x00637910))

## Fields the base-stat roll reads (plan 0024 Phase 1)

From [items/0006 § 1](../findings/items/0006-properties.md#1-base-stats-sub_00557ab0_iteminitstats-0x00557ab0) and
[§ 6](../findings/items/0006-properties.md#6-ethereal-and-sockets-after-the-switch-0x005579430x005579a3) (static
reading); the data counts are computed over `weapons.txt`. Every draw below is on the item unit's own seed, in the
order of the bullets, before the quality builder runs.

- `[I]` **`stackable`, `minstack`, `maxstack`.** A `stackable` weapon (36 rows, the throwing weapons and potions)
  draws its quantity first: `minstack + RangeB(top − minstack)` with `top = maxstack + stat 254` (capped at 511), so
  `top` itself is never drawn; a result of 0 becomes 1. `spawnstack` is **not** read for weapons (it is a misc
  reading). (fn:sub_00557AB0_ItemInitStats@0x00557AB0, fn:ITEMS_GetMinStack@0x006296F0,
  fn:ITEMS_GetMaxStack@0x006295B0, tbl:Weapons.txt:minstack)
- `[I]` **`durability`.** Then `cur = ⌊d/2⌋ + RangeB(⌊d/2⌋)` (no draw when `d < 2`), so `cur` lies in
  `[⌊d/2⌋, 2⌊d/2⌋ − 1]`; max durability = `d`. (items/0006 § 1, tbl:Weapons.txt:durability)
- `[I]` **`nodurability` is not tested by that draw**: the 48 rows with `nodurability` 1 and `durability` > 1
  still draw (49 rows have `nodurability` 1, one of them with `durability` < 2). (tbl:Weapons.txt:nodurability)
- `[I]` **Damage columns.** `mindam`/`maxdam`, `2handmindam`/`2handmaxdam` and `minmisdam`/`maxmisdam` are written
  as base stats 21–24 and 159/160 (no draw); funcs 5–7 of [Properties](Properties.md#code-semantics-plan-0024-phase-1)
  pick which of them a damage property touches. (fn:PROP_Func05_DmgMin@0x0065ECF0, tbl:Weapons.txt:mindam)
- `[I]` **`hasinv`, `gemsockets` (sockets).** A quality 2 or 3 weapon is a socket candidate when `hasinv` is set, it is
  not `stackable`, and `ItemMaxSockets = min(gemsockets, MaxSock1|25|40 of its type)` > 0 ([ItemTypes](ItemTypes.md#fields-the-base-stat-roll-reads-plan-0024-phase-1)).
  One `RNG_Range(item seed, 100)` < 33 sockets it; the count is not drawn: `startSeed % cap + 1`, `cap` also capped
  at 3 / 4 / 6 by difficulty. 265 weapons have `hasinv` 1 and `gemsockets` > 0. (fn:sub_00556B60_ItemRollSockets@0x00556B60,
  fn:ITEMS_SetSockets@0x0062BCB0, tbl:Weapons.txt:gemsockets)

## Vendor columns (plan 0031 Phase 0)

The columns a vendor's stock reads. They are the same 424-byte record fields in all three item tables
([Record layout](#record-layout-424-bytes-shared-by-weapons-armor-and-misc)); the counts for armor and misc are in
[Armor § Vendor columns](Armor.md#vendor-columns-plan-0031-phase-0) and
[Misc § Vendor columns](Misc.md#vendor-columns-plan-0031-phase-0). The layout is `[C]` (as above). The meanings come
from the stock builder in [items/0009 § 2](../findings/items/0009-vendors.md#2-the-candidate-lists-vendor_buildlist-0x00536d50),
[§ 4](../findings/items/0009-vendors.md#4-the-stock-build-vendor_buildstock-0x00576980) and
[§ 5](../findings/items/0009-vendors.md#5-one-stock-item-vendor_createstockitem-0x00576330); "stock level" is the
`ilvl` of a build, `min(clvl + 5, cap[act])` in Normal (caps 12, 20, 28, 36, 45) and `clvl + 5` in Nightmare and Hell,
up to 104 (items/0009 § 4).

**Survey command.** `python3 -I tools/vendor_survey.py bases workspace/merged/data/global/excel <vendor> [normal|nightmare|hell]`
prints, for one vendor column group (or an [Npc](Npc.md) name) and one difficulty, every item record whose `Min`,
`Max`, `MagicMin` or `MagicMax` byte is non-zero, with its five vendor bytes, `PermStoreItem`, `multibuy` and the
difficulty's upgrade cell. `summary` gives the counts (gate survey `vendors`). The bytes are read from the `.bin`,
which is what the game loads.

| Column group | Field | Observed (all three tables) | Meaning (items/0009) |
|---|---|---|---|
| `<Vendor>Min`, `<Vendor>Max` | `+0x146 + v`, `+0x157 + v` u8 | 0..17; `Min` ≤ `Max` on every record | `[I]` normal copies per build: `RandLoHi(S, Min, Max + 1)`, so `Min..Max`, drawn only while the stock level is below 25 (0 copies from 25 on). `Max` (or `MagicMax`) ≠ 0 lists the base; `Min` plays no part in the listing |
| `<Vendor>MagicMin`, `<Vendor>MagicMax` | `+0x168 + v`, `+0x179 + v` u8 | 0..17; `MagicMin` ≤ `MagicMax` on every record | `[I]` magic (quality 4) copies: `RandLoHi(S, MagicMin, MagicMax + x)` with `x` = 1 below stock level 25, else `RandLoHi(S, 1, 3) + 1` (2 or 3, one draw) |
| `<Vendor>MagicLvl` | `+0x18A + v` u8 | {0, 1, 3, 5, 10, 15, 20, 30, 255} | `[I]` the **minimum stock level** for magic copies: they are made only when `MagicLvl` ≤ the stock level and the base's `bitfield1` bit 0 is set. Not an affix level: the affix level is the ordinary alvl rule ([items/0005](../findings/items/0005-affixes.md)). `[C]` read as an **unsigned** byte (`movzx`, 0x00576AE3): 255 never passes (the stock level is at most 104), 0 is no gate ([items/0009 § 4](../findings/items/0009-vendors.md#4-the-stock-build-vendor_buildstock-0x00576980), run:2026-10-15-vendors) |
| `NightmareUpgrade`, `HellUpgrade` | `+0x19C`, `+0x1A0` char[4] code | an item code, or `xxx` | `[I]` the base a stock item is made from instead, in Nightmare / Hell when the opener's level is ≥ 26; `xxx` = none (order below) |
| `PermStoreItem` | `+0x1A4` u8 | 0 or 1 | `[I]` the base goes to the vendor's permanent list instead of the counted list: one quality-2 (normal) copy per build, whatever the counts; `aqv`/`cqv` get a full stack |
| `multibuy` | `+0x1A5` u8 | 0 or 1, set only where `PermStoreItem` is | `[L]` the player can buy several at once (shift-click) |
| `bitfield1` bit 0 | `+0x0DC` u32 | see [Columns](#columns) | `[I]` allows magic copies in stock (with `MagicLvl`) and is required by Charsi's imbue (below) |

`v` is the vendor's position in the column-group order: 0 Akara, 1 Gheed, 2 Charsi, 3 Fara, 4 Lysander, 5 Drognan,
6 Hralti, 7 Alkor, 8 Ormus, 9 Elzix, 10 Asheara, 11 Cain, 12 Halbu, 13 Jamella, 14 Malah, 15 Larzuk, 16 Drehya `[C]`.
This order is not the [Npc](Npc.md) row order (`gheed`, `charsi`, `akara`, …), and the two sets differ: Npc has
`nihlathak` and no `cain`.

- `[C]` **NPC class → group** comes from two switches in the code (the store-record filler and the list builder), which
  agree: 148 Akara 0, 147 Gheed 1, 154 Charsi 2, 178 Fara 3, 202 Lysander 4, 177 Drognan 5, 253 Hralti 6, 254 Alkor 7,
  255 Ormus 8, 199 Elzix 9, 252 Asheara 10, 257 Halbu 12, 405 Jamella 13, 513 Malah 14, 511 Larzuk 15, 512 Drehya 16.
  Group 11 (Cain) is never used. The class ids are MonStats rows; the Npc table's `npc` column is not read for this map.
  ([items/0009 § Answer](../findings/items/0009-vendors.md#answer-summary), 0x00536271–0x005363EE, 0x00536FC0–0x00537046)
- `[I]` Nihlathak (514) has no group of his own: his store record takes Larzuk's list (15), and he is not in the trade
  menu's class list, so he only gambles. (items/0009 § Answer, fn:NPC_MenuAction@0x00579D60)
- `[I]` **Listing rule.** Once per process, `VENDOR_BuildList(v)` walks weapons, armor, misc in index order and keeps a
  base when `spawnable` ≠ 0 and (`<V>Max` ≠ 0 or `<V>MagicMax` ≠ 0). A base with `PermStoreItem` ≠ 0 goes to the
  permanent list; every other one becomes an entry `{Min, Max, MagicMin, MagicMax, code, MagicLvl}`.
  ([items/0009 § 2](../findings/items/0009-vendors.md#2-the-candidate-lists-vendor_buildlist-0x00536d50),
  fn:VENDOR_BuildList@0x00536D50, tbl:Weapons.txt:spawnable, tbl:Weapons.txt:PermStoreItem)
- `[I]` **Per entry, in list order**: skip when the base `level` > the stock level; draw the normal count (below 25);
  in a classic game skip an expansion base (`version` ≥ 100) after that draw; then the magic copies as in the table.
  ([items/0009 § 4](../findings/items/0009-vendors.md#4-the-stock-build-vendor_buildstock-0x00576980),
  fn:VENDOR_BuildStock@0x00576980, tbl:Weapons.txt:CharsiMagicLvl, tbl:Weapons.txt:level)

**Weapons, per vendor group** (`[C]`, `vendor_survey.py summary` and `bases`): bases = records with a non-zero
`Min`/`Max`/`MagicMin`/`MagicMax`; magic = with a non-zero `MagicMin`/`MagicMax`; magic only = magic with `Min` = `Max` = 0.

| Group | bases | magic | magic only | `MagicLvl` on those bases |
|---|---:|---:|---:|---|
| Akara | 5 | 5 | 0 | 1 |
| Gheed | 23 | 17 | 3 | 20 (18), 30 (2), 1 (1), 255 (2) |
| Charsi | 21 | 18 | 0 | 1 (18), 255 (3) |
| Fara | 34 | 31 | 4 | 20 (32), 30 (2) |
| Lysander, Alkor | 0 | 0 | 0 | — |
| Drognan | 10 | 10 | 3 | 1 (9), 255 (1) |
| Hralti | 22 | 20 | 2 | **0** (22): the dead `HratliMagicLvl` header |
| Ormus | 13 | 13 | 3 | 1 |
| Elzix | 26 | 20 | 0 | 1 (22), 20 (1), 255 (3) |
| Asheara | 21 | 13 | 0 | 1 (13), 20 (2), 255 (6) |
| Cain | 18 | 11 | 0 | 1 (13), 255 (5) |
| Halbu | 24 | 24 | 5 | 20 |
| Jamella | 21 | 15 | 4 | 20 (15), 255 (6) |
| Malah | 18 | 18 | 5 | 20 |
| Larzuk | 16 | 16 | 3 | 20 |
| Drehya | 7 | 7 | 6 | 20 |

- `[C]` 87 weapons have a non-zero byte for some vendor: 80 of item `version` 0, 7 of `version` 100.
- `[C]` **`MagicLvl` where the vendor stocks nothing** (a record and group with all four count bytes 0): 255 on
  10 120 pairs, 20 on 40, 1 on 10, 0 on 1 (a blank Drognan cell), besides Hralti's dead zeros (476 weapon and armor
  records). **255 also sits on 41 stocked weapon and armor pairs** (26 weapons), 8 of them with a non-zero
  `MagicMin`/`MagicMax` (Elzix `lxb`, Drognan `scy`, Charsi `rng`, Halbu `tgl`/`hgl`, Jamella `tgl`/`tbt`/`tbl`).
  `[C]` 255 blocks magic copies: the gate reads `MagicLvl` unsigned and passes at `MagicLvl` ≤ stock level, and the
  stock level never exceeds 104 ([items/0009 § 4](../findings/items/0009-vendors.md#4-the-stock-build-vendor_buildstock-0x00576980), 0x00576AE3–0x00576AE8, run:2026-10-15-vendors). These 8 pairs
  get normal copies only.
- `[C]` **Hralti's `MagicLvl` is 0 on every weapon and armor record**: the header is spelled `HratliMagicLvl` there
  (see [Interpretation notes](#interpretation-notes)), so the game sees 0 for all 32 Hralti weapon and armor bases,
  whatever the `.txt` says (20 or 255 on the weapons, 1 on the armors). `[C]` A 0 passes the gate at every stock level,
  so Hratli stocks magic copies of every listed base whose `bitfield1` bit 0 is set, from his first build
  ([items/0009 § 4](../findings/items/0009-vendors.md#4-the-stock-build-vendor_buildstock-0x00576980), run:2026-10-15-vendors).
- `[C]` **Upgrades.** 51 weapons have a `NightmareUpgrade` and 53 a `HellUpgrade` that name an item; the rest hold
  `xxx`, which names none. Every row with an upgrade is stocked by some vendor. Every target is a **normal-tier** base
  (its `code` equals its own `normcode`), never the row's own `ubercode`/`ultracode`: a step up the normal bases of
  the same type (`wnd` → `ywn` → `bwn`), not the exceptional/elite tier. 4 hell and 2 nightmare targets have another
  item type. One `HellUpgrade` names its own row (`mau`, Maul).
- `[I]` **Upgrade order** (`VENDOR_CreateStockItem`), only in Nightmare or Hell when the opener's level is ≥ 26, with
  one draw `u = RNG_RangeB(S, 100000)` per item. Nightmare: `u < ilvl·64 + 4000` and a valid `ubercode` → the
  ubercode, else `NightmareUpgrade` if not `xxx`. Hell: in an expansion game `u < ilvl·16 + 1000` and a valid
  `ultracode` → the ultracode; else `u < ilvl·128 + 5000` and a valid `ubercode` → the ubercode; then `HellUpgrade`,
  when not `xxx`, replaces the result in every case. An item whose code differs from the chosen code is destroyed and
  made once more with quality 2. ([items/0009 § 5](../findings/items/0009-vendors.md#5-one-stock-item-vendor_createstockitem-0x00576330),
  fn:VENDOR_CreateStockItem@0x00576330, tbl:Weapons.txt:NightmareUpgrade, tbl:Weapons.txt:HellUpgrade)
- `[C]` `PermStoreItem` is 1 on six weapons, the throwing potions (`gps`, `ops`, `gpm`, `opm`, `gpl`, `opl`), and no
  vendor byte is set on them. `multibuy` is 0 on every weapon.

## Fields the quest services read (plan 0032)

From [items/0010 § 5](../findings/items/0010-quest-drops.md#5-quest-items) and
[§ 6](../findings/items/0010-quest-drops.md#6-npc-rewards). The same record fields in all three item tables.

- `[I]` **`questdiffcheck`** (`+0x12B`). Every created item with `quest` ≠ 0 and `questdiffcheck` ≠ 0 gets stat 356
  (`questitemdifficulty`) = the game difficulty, and when a quest script asks whether the player already holds such an
  item, it counts only when its stat 356 is ≥ the game's difficulty. So a Normal Horadric Staff does not stop a
  Nightmare chest from making a new one; the cube (`box`, `questdiffcheck` blank) does.
  (fn:sub_00557AB0_ItemInitStats@0x00557AB0, fn:sub_00558110_PlayerFindItemByCode@0x00558110,
  tbl:Weapons.txt:questdiffcheck)
- `[I]` **`bitfield1` bit 0** is required by Charsi's imbue (`sub_0062C590_ItemCanImbue`), besides the item tests of
  items/0010 § 6; the same bit allows magic copies in stock ([Vendor columns](#vendor-columns-plan-0031-phase-0)).
  On the data: every weapon but the six throwing potions and `hdm` has it. (fn:sub_0062C590_ItemCanImbue@0x0062C590,
  tbl:Weapons.txt:bitfield1)
- `[I]` **`compactsave`** (`+0x143`) 0 and **`Nameable`** (`+0x145`) ≠ 0 are required by Anya's personalization
  (`sub_0062C6A0_ItemCanPersonalize`), with the item tests of items/0010 § 6. On the data: 292 weapons have `Nameable`
  1, 14 have 0; `compactsave` is blank on every weapon. (fn:sub_0062C6A0_ItemCanPersonalize@0x0062C6A0,
  tbl:Weapons.txt:Nameable, tbl:Weapons.txt:compactsave)
- `[C]` The `quest` column's value minus 1 is a **quest object id** (`g_QuestDescs` `+0x10`), not a quest word + 1:
  the item event and hook look the object up by `quest − 1`, and the gate's own `{word, quest}` pairs agree. `[I]`
  Through `g_QuestDescs`, `hdm` 4 → object 3 (word 3), `hst`/`msf` 10 → object 9 (word 10), `hfh` 25 → object 24
  (word 27). ([items/0010 § 5](../findings/items/0010-quest-drops.md#5-quest-items), fn:QUESTS_FindById@0x00543640, data:g_QuestDescs@0x00731510, data:g_QuestItemWordGate@0x00731FEC, tbl:Weapons.txt:quest)

## Combat columns (plan 0037 Phase 0)

The columns a normal attack's damage build and to-hit are expected to read. Offsets are § [Columns](#columns)
(`[C]`, `excel_bin.py diff`); the counts are `python3 -I tools/combat_survey.py items workspace/merged/data/global/excel`
(gate survey `combat`) over the 306 records, `[C]` as data. "Set" is a non-blank `.txt` cell. Meanings `[L]` unless
tagged.

| Column | `.bin` field | Set | Non-zero | Values | Tag |
|---|---|---:|---:|---|---|
| `mindam` | `+0x0FE` u8 | 187 | 181 | 0..50 | [C] |
| `maxdam` | `+0x0FF` u8 | 187 | 187 | 1..80 | [C] |
| `1or2handed` | `+0x13D` u8 | 18 | 18 | 1 | [C] |
| `2handed` | `+0x11C` u8 | 137 | 137 | 1 | [C] |
| `2handmindam` | `+0x102` u8 | 137 | 137 | 1..83 | [C] |
| `2handmaxdam` | `+0x103` u8 | 137 | 137 | 4..180 | [C] |
| `minmisdam` | `+0x100` u8 | 30 | 30 | 4..40 | [C] |
| `maxmisdam` | `+0x101` u8 | 30 | 30 | 9..85 | [C] |
| `rangeadder` | `+0x104` s16 | 171 | 171 | 1..4 | [C] |
| `speed` | `+0x0D8` s32 | 201 | 201 | −60..20 | [C] |
| `StrBonus` | `+0x106` s16 | 258 | 258 | 75..110 | [C] |
| `DexBonus` | `+0x108` s16 | 111 | 111 | 50..100 | [C] |
| `reqstr`, `reqdex` | `+0x10A`, `+0x10C` u16 | 255, 200 | 255, 200 | 15..253, 15..188 | [C] |
| `hit class` | `+0x13C` u8 `hitclass` row | 306 | 306 | 11 classes: `1hsl` 86, `2hsl` 39, `1ht` 38, `bow` 30, `1hss` 27, `2ht` 21, `2hss` 18, `club` 15, `staf` 14, `xbow` 12, `hth` 6 | [C] |
| `missiletype` | `+0x0FA` u16 | 306 | 42 | 0..371 | [C] |

- `[C]` Every weapon has one-hand damage (`mindam`/`maxdam`, 187 rows) or two-hand damage (`2handmindam`/`2handmaxdam`,
  137 rows); the 18 rows with both are exactly the `1or2handed` rows (swords such as `2hs`, `clm`, `gis`, `bsw`, `flb`).
  The 137 `2handed` rows are bows 24, swords 18, polearms 18, staves 17, axes 15, spears 15, crossbows 12, hammers 6,
  Amazon bows 6 and Amazon spears 6. (tbl:Weapons.txt:2handed, tbl:Weapons.txt:1or2handed)
- `[C]` Missile damage (`minmisdam`/`maxmisdam`) is set on the 30 throwing weapons only: javelins 15, throwing knives
  6, throwing axes 6, Amazon javelins 3. (tbl:Weapons.txt:minmisdam)
- `[I]` At item creation the damage columns become base stats 21–24 and 159/160 with no draw
  ([§ Fields the base-stat roll reads](#fields-the-base-stat-roll-reads-plan-0024-phase-1),
  fn:PROP_Func05_DmgMin@0x0065ECF0); which of them an attack reads, and what `StrBonus`, `DexBonus`, `speed` and
  `rangeadder` do, is plan 0037 Phase 1. `hit class` is [HitClass](HitClass.md) and plan 0050's ([§ Timing](#timing-plan-0050-phase-0)).

## Economy (plan 0043 Phase 0)

The columns the price, repair and wear code is expected to read. They are fields of the shared 424-byte record
([Record layout](#record-layout-424-bytes-shared-by-weapons-armor-and-misc)), so the table below covers
[Armor § Economy](Armor.md#economy-plan-0043-phase-0) and [Misc § Economy](Misc.md#economy-plan-0043-phase-0) too;
each of those lists its own rows. The layout is `[C]` (`excel_bin.py diff`, 0 mismatches in all three files). The
counts come from `python3 -I tools/economy_survey.py items workspace/merged/data/global/excel` (gate survey
`economy`: each count below is a key of its `SURVEY` line), `[C]` as data. Readers named so far are on the item
creation side only (the quantity and durability draws, `[I]`,
[§ Fields the base-stat roll reads](#fields-the-base-stat-roll-reads-plan-0024-phase-1)); the price function
(`sub_0062FDC0_ItemTradePrice`), the repair cost (`sub_0062FE60_RepairCost`) and the wear code are read by plan 0043
Phase 1 ([items/0011](../findings/items/0011-economy.md)); the meanings that cite it are `[I]`, the others `[L]`.

| Column | Field | Weapons | Armor | Misc | Meaning |
|---|---|---|---|---|---|
| `cost` | `+0x0E0` u32 | 5..33 375, never 0 | 64..373 558, never 0 | 0..134 540; 0 on 7 | `[I]` the base of the buy, sell and repair values (`P = S = R = cost`; a tome, a quiver, a body part and an ear have their own base), scaled for armour by `armorclass / maxac` ([items/0011 § 1](../findings/items/0011-economy.md#1-the-price-core-inputs-and-the-base)); a `cost` 0 prices at 0 and returns the floor 1 |
| `gamble cost` | `+0x0D4` u32 | 0..2 644 750; 0 on 15 | 3 016..4 872 212, never 0 | 32 000..63 000 on 5; 146 blank | `[I]` the gamble price only of `rin`, `amu` and version-0 items; every other gamble price is computed from the character level and the base's `cost`, `level`, stack and `ubercode`/`ultracode` bases ([items/0011 § 2](../findings/items/0011-economy.md#2-the-gamble-price-mode-2)) |
| `durability` | `+0x112` u8 | 0..72; 0 on 1 (`7cr`) | 12..100, never 0 | blank in every row | max durability; `[I]` the creation draw puts the current value in `[⌊d/2⌋, 2⌊d/2⌋ − 1]` |
| `nodurability` | `+0x113` u8 | 1 on 49 (257 blank) | 0 in every row | 1 in every row | `[C]` `ItemHasDurability` fails when it is set ([items/0004](../findings/items/0004-uniques-sets.md), fn:sub_00629930_ItemHasDurability@0x00629930); what else reads it `[L]` |
| `durwarning` | `+0x135` u8 | 7 in every row | 1..6 (6 values) | 0 in every row | low-durability warning threshold `[L]` |
| `qntwarning` | `+0x136` u8 | 2..5, on the 36 `stackable` rows exactly | 0 in every row | 1 on 2 (`aqv`, `cqv`) | low-quantity warning threshold `[L]` |
| `stackable` | `+0x132` u8 | 1 on 36 | 0 in every row | 1 on 10 | `[I]` the creation quantity draw runs ([items/0006 § 1](../findings/items/0006-properties.md#1-base-stats-sub_00557ab0_iteminitstats-0x00557ab0)) |
| `minstack`, `maxstack`, `spawnstack` | `+0x0E4`, `+0x0E8`, `+0x0EC` u32 | 3..40, 20..200, 6..80 on the 36 | 0 in every row | see Misc | `[I]` the creation quantity bounds (`maxstack` + stat 254, cap 511; `spawnstack` for misc only); `[I]` in the price: the gamble price averages `(minstack + maxstack)/2`, a stackable base with `MaxStack` ≥ 2 divides the stat terms by it, and the sell value of a repairable stack is `M·S − (M − q)·R` ([items/0011 § 1](../findings/items/0011-economy.md#1-the-price-core-inputs-and-the-base), [items/0011 § 4](../findings/items/0011-economy.md#4-mode-steps-the-npc-row-quantity-and-the-result)) |
| `multibuy` | `+0x1A5` u8 | 0 in every row | 0 in every row | 1 on 20, all `PermStoreItem` | bought several at once `[L]` ([§ Vendor columns](#vendor-columns-plan-0031-phase-0)) |
| `quest` | `+0x12A` u8 | 1..25 on 9 | 0 in every row | 1..32 on 17 | quest item; whether it sells, and for what `[L]` |

The repair flag is not an item column: it is the item type's `Repair` (ItemTypes `+0x008`,
[ItemTypes § Repair and throwing columns](ItemTypes.md#repair-and-throwing-columns-plan-0043-phase-0)), and
`CostFormula` (ItemTypes `+0x020`) is the other per-type price column. The per-stat price terms are in
[ItemStatCost § Price](ItemStatCost.md#price-plan-0043-phase-0), the affix and unique/set terms in
[MagicPrefix § Price](MagicPrefix.md#price-plan-0043-phase-0), [UniqueItems § Price](UniqueItems.md#price-plan-0043-phase-0)
and [SetItems § Price](SetItems.md#price-plan-0043-phase-0), the NPC multipliers in
[Npc § Multipliers](Npc.md#multipliers-plan-0043-phase-0), the charges in
[Skills § Charge cost columns](Skills.md#charge-cost-columns-plan-0043-phase-0), the tomes in [Books](Books.md) and
the hire price in [Hireling § Costs](Hireling.md#costs-plan-0043-phase-0).

**Weapons** (`[C]`, data):

- `[C]` `cost` is set on every row (260 distinct values) and `gamble cost` on 291. **`gamble cost` is 0 on 15 rows**:
  the six throwing potions (`gps`, `ops`, `gpm`, `opm`, `gpl`, `opl`) and the nine quest weapons (`d33`, `g33`, `leg`,
  `hdm`, `hfh`, `hst`, `msf`, `qf1`, `qf2`). No weapon has a `cost` above a set `gamble cost`.
- `[C]` **The quest weapons' `cost`**: `leg` 20, `hdm`/`hfh` 600, `d33`/`g33` 666, `hst`/`msf` 1 223, `qf1`/`qf2`
  1 412; none is 0.
- `[C]` **`nodurability` 1 on 49 rows**, 48 of them with a `durability` (bows 20..55, crossbows 30..50, Amazon bows
  48/55, throwing potions 2) and one without: `7cr` (Phase Blade, `durability` 0). No weapon has both `nodurability`
  0 and `durability` 0. `[I]` The creation draw does not test `nodurability`, so the 48 still get a durability
  ([§ Fields the base-stat roll reads](#fields-the-base-stat-roll-reads-plan-0024-phase-1)).
- `[C]` **Stacks.** The 36 `stackable` rows are the 30 throwing weapons (javelins, throwing knives and axes, Amazon
  javelins) and the six throwing potions; every row with a `maxstack` is `stackable`, and `qntwarning` is set on these
  rows and no other (2 javelins and spears, 3 potions, 4 knives, 5 axes). Elite tiers have the larger `maxstack`
  (`tkf` 40/160/75, `7tk` 40/200/75 as `minstack`/`maxstack`/`spawnstack`); the potions 3/25/6.
- `[C]` **Repair type against `nodurability`** (`economy_survey.py types`; the item's own `type` row only, the
  `Equiv` tree not walked): 270 of 306 weapons have a type with `Repair` 1; the other 36 are the bows (`bow`, `abow`)
  and the throwing potions (`tpot`), all `nodurability` 1. Every weapon with `nodurability` 0 has a `Repair` type. The
  13 `nodurability` rows whose type has `Repair` are the 12 crossbows (`xbow`) and `7cr` (`swor`).
- `[C]` **The gamble list** ([Gamble](Gamble.md)): 125 bases, 75 weapons, 48 armors and `amu`, `rin`; every one has a
  `gamble cost` > 0 and none a `cost` above it. `[I]` Of these cells only `amu`'s and `rin`'s are read on a current
  item ([items/0011 § 2](../findings/items/0011-economy.md#2-the-gamble-price-mode-2)).
- `[I]` **The price base and the armour scaling** ([items/0011 § 1](../findings/items/0011-economy.md#1-the-price-core-inputs-and-the-base), fn:ITEMS_TradePriceCore@0x0062EFB0): `P = S = R = cost`;
  for an armour item (type 50 `armo`) with `maxac − minac ≠ −1` and `maxac ≠ 0`, all three become
  `cost × armorclass / maxac` (the item's base defence, signed truncation). So `minac`/`maxac`
  ([Armor](Armor.md)) scale the armour price.

## Timing (plan 0050 Phase 0)

The columns a player's attack timing can read (values from the `.bin` over the 306 records):

| Column | `.bin` field | Observed | Meaning | Tag |
|---|---|---|---|---|
| `speed` | `+0x0D8` s32 | −60..20 (11 values: 0 ×105 set, −10 ×79, 10 ×67, −20 ×22, 20 ×19, …); 105 blank store 0 | the weapon's speed modifier (name) | [C] layout; `[L]` |
| `wclass` | `+0x0C0` 4-byte code | `1hs` 122, `stf` 56, `1ht` 44, `bow` 30, `2ht` 21, `ht1` 21, `xbw` 12 | weapon class held one-handed: the third part of the player's `animdata.d2` record name | [C] layout; `[L]` |
| `2handedwclass` | `+0x0C4` 4-byte code | as `wclass` except 18 rows with `2hs` (their `wclass` is `1hs`) | weapon class held two-handed | [C] layout; `[L]` |
| `hit class` | `+0x13C` u8, [HitClass](HitClass.md) row | 1..11 in all 306 | the hit class | [C] layout ([HitClass](HitClass.md)); `[L]` |

- `[C]` The 18 rows whose two classes differ are the 18 with both `2handed` (`+0x11C`) and `1or2handed` (`+0x13D`)
  set. Every `wclass`/`2handedwclass` code is a `weaponclass.txt` code, and each names an `NU` record for every class
  except `ht1` (the Assassin's only); which modes have a record per weapon class is in
  [PlrMode § Timing](PlrMode.md#timing-plan-0050-phase-0) and the tool's `players` output.
- `[L]` How `speed` enters the attack rate with IAS (`item_fasterattackrate`) and the skill rate terms, and which
  weapon class a dual wield or a two-handed grip names, are plan 0050 Phase 1.2.

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
