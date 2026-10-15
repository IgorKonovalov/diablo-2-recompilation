# Weapons (`data/global/excel/weapons.txt`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 306 (307 data rows − 1 `Expansion` marker)   **Record:** 424 B
> **sha256:** `.txt` `05a938e3fc0b8974bc722bfa8974f44e45e99d19c6877613ff731104b12b3536`, `.bin` `70f6677a8b2c019795d172dd9c90deea4663249504b85c65121da9c917e00983`
> **Doc status:** columns listed, `.bin` layout complete (shared item record), semantics pending except [§ Fields the base-stat roll reads](#fields-the-base-stat-roll-reads-plan-0024-phase-1) (`[I]`, plan 0024 Phase 1); vendor columns surveyed in [§ Vendor columns](#vendor-columns-plan-0031-phase-0) (`[L]` meanings, plan 0031 Phase 0)

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

The columns a vendor's stock reads, as far as the data shows. They are the same 424-byte record fields in all three
item tables ([Record layout](#record-layout-424-bytes-shared-by-weapons-armor-and-misc)); the counts for armor and misc
are in [Armor § Vendor columns](Armor.md#vendor-columns-plan-0031-phase-0) and
[Misc § Vendor columns](Misc.md#vendor-columns-plan-0031-phase-0). The layout is `[C]` (as above); every meaning is
`[L]` until plan 0031 Phase 1 reads the stock builder.

**Survey command.** `python3 -I tools/vendor_survey.py bases workspace/merged/data/global/excel <vendor> [normal|nightmare|hell]`
prints, for one vendor column group (or an [Npc](Npc.md) name) and one difficulty, every item record whose `Min`,
`Max`, `MagicMin` or `MagicMax` byte is non-zero, with its five vendor bytes, `PermStoreItem`, `multibuy` and the
difficulty's upgrade cell. `summary` gives the counts (gate survey `vendors`). The bytes are read from the `.bin`,
which is what the game loads.

| Column group | Field | Observed (all three tables) | Meaning `[L]` |
|---|---|---|---|
| `<Vendor>Min`, `<Vendor>Max` | `+0x146 + v`, `+0x157 + v` u8 | 0..17; `Min` ≤ `Max` on every record | how many copies of the base the vendor stocks as a normal item, a range |
| `<Vendor>MagicMin`, `<Vendor>MagicMax` | `+0x168 + v`, `+0x179 + v` u8 | 0..17; `MagicMin` ≤ `MagicMax` on every record | the same for magic copies |
| `<Vendor>MagicLvl` | `+0x18A + v` u8 | {0, 1, 3, 5, 10, 15, 20, 30, 255} | an item level, or a level cap, for the magic copies' affixes |
| `NightmareUpgrade`, `HellUpgrade` | `+0x19C`, `+0x1A0` char[4] code | an item code, or `xxx` | the base the vendor stocks in place of this one in nightmare / hell |
| `PermStoreItem` | `+0x1A4` u8 | 0 or 1 | the base is always in stock (potions, scrolls, keys, ammunition, tomes) |
| `multibuy` | `+0x1A5` u8 | 0 or 1, set only where `PermStoreItem` is | the player can buy several at once (shift-click) |

`v` is the vendor's position in the column-group order: 0 Akara, 1 Gheed, 2 Charsi, 3 Fara, 4 Lysander, 5 Drognan,
6 Hralti, 7 Alkor, 8 Ormus, 9 Elzix, 10 Asheara, 11 Cain, 12 Halbu, 13 Jamella, 14 Malah, 15 Larzuk, 16 Drehya `[C]`.
This order is not the [Npc](Npc.md) row order (`gheed`, `charsi`, `akara`, …), and the two sets differ: Npc has
`nihlathak` and no `cain`. Which code maps an NPC to its group is a Phase 1 question `[L]`.

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
  Whether 255 means "no cap" or blocks magic copies is `[L]`.
- `[C]` **Hralti's `MagicLvl` is 0 on every weapon and armor record**: the header is spelled `HratliMagicLvl` there
  (see [Interpretation notes](#interpretation-notes)), so the game sees 0 for all 32 Hralti weapon and armor bases,
  whatever the `.txt` says (20 or 255 on the weapons, 1 on the armors). What a 0 does in the stock roll is `[L]` (Phase 1).
- `[C]` **Upgrades.** 51 weapons have a `NightmareUpgrade` and 53 a `HellUpgrade` that name an item; the rest hold
  `xxx`, which names none. Every row with an upgrade is stocked by some vendor. Every target is a **normal-tier** base
  (its `code` equals its own `normcode`), never the row's own `ubercode`/`ultracode`: a step up the normal bases of
  the same type (`wnd` → `ywn` → `bwn`), not the exceptional/elite tier. 4 hell and 2 nightmare targets have another
  item type. One `HellUpgrade` names its own row (`mau`, Maul). `[L]` that the vendor swaps the base at that
  difficulty.
- `[C]` `PermStoreItem` is 1 on six weapons, the throwing potions (`gps`, `ops`, `gpm`, `opm`, `gpl`, `opl`), and no
  vendor byte is set on them. `multibuy` is 0 on every weapon.

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
