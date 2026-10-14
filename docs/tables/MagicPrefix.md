# MagicPrefix and MagicSuffix (`data/global/excel/MagicPrefix.txt`, `MagicSuffix.txt` → `magicprefix.bin`, `magicsuffix.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`, both tables)   **Rows:** `magicprefix` 669 (670 data rows − 1 `Expansion` marker), `magicsuffix` 747 (748 − 1)   **Record:** 144 B (both)
> **sha256:** `magicprefix.txt` `f58b05c7b5db4464cbce1087b73a6f99592be56ea955fe60dd901fcddb56c561`, `magicprefix.bin` `cdcbf46c2e32c39006b224d2590041a076d45bc768fd68d09706607a1493f20b`; `magicsuffix.txt` `47d4399809c3f123f338deebb139139b0f775f47c435e286954457b0cd47de21`, `magicsuffix.bin` `ec44c7bcff0323661170832452a9996759acc7673f15b6dc7fe07998a9f36206`
> **Doc status:** columns listed, `.bin` layout complete, generation columns surveyed (plan 0021 Phase 0); the pick's use of every generation column `[I]` from
> [items/0005](../findings/items/0005-affixes.md) (plan 0021 Phase 1, § Code semantics below); property columns `[L]`

One shared doc: the two tables have the same columns (`MagicSuffix.txt` lacks `etype4` and `etype5`) and the
same 144-byte record. [MagicSuffix.md](MagicSuffix.md) only points here. [AutoMagic](AutoMagic.md) uses the
same record too.

## Purpose

One row per magic affix: the prefix (`MagicPrefix`) or suffix (`MagicSuffix`) a magic item can carry, and
that a rare item draws its affixes from. A row names up to three properties (`mod1code`..`mod3code` with
param, min, max), the item types it may and may not appear on (`itype1..7`, `etype1..5`), the level
window and the pick weight. Read by `items/affixes` (which rows an item gets: plan 0021) and
`items/properties` (the property values, out of scope here). Leads: no lead; derived from data.

## Row identity

- `[C]` The record index is the data row index once the `Expansion` marker is dropped: `excel_bin.py diff`
  matches record *i* to data row *i* in every mapped column of both tables (counts below).
  (tbl:MagicPrefix.txt:Name, tbl:MagicSuffix.txt:Name)
- `[C]` **Blank rows.** 32 `magicprefix` records have a blank `Name` (0, 9, 10, 11, 20, 21, 22, 23, 30, 43..47,
  50, 51, 53, 61, 62, 70, 72, 73, 79, 81, 82, 88, 90, 91, 97, 99, 115, 116) and every field of each is 0
  (`classspecific`/`class`/`transformcolor` hold their blank code, `0xFF`). **Record 0 of `magicprefix` is one
  of them.** 6 `magicsuffix` records are blank (4, 9, 62, 69, 100, 103), all 0 except record 4, whose
  `spawnable` cell is `1`. **Record 0 of `magicsuffix` is a real row** (`of Health`). (tbl:MagicPrefix.txt:Name,
  tbl:MagicSuffix.txt:spawnable)
- `[C]` `Name` is not unique: 252 distinct names over the 637 named prefix rows (`Rugged` ×12, `Jagged` ×11,
  `Lizard's` ×11) and 288 over the 741 named suffix rows (`of Dexterity` ×13, `of Strength` ×12). A consumer
  keys on the record index. (tbl:MagicPrefix.txt:Name, tbl:MagicSuffix.txt:Name)
- `[I]` A saved magic item stores its prefix as `id − firstPrefix` of the merged affix array
  (`g_MagicAffixInfo`) and its suffix unchanged, with 0 = none ([d2s format](../formats/d2s.md),
  data:g_MagicAffixInfo@0x0096CA7C).
- `[I]` **Merged ids.** The loader appends `magicsuffix`, `magicprefix` and `automagic`, in that order, into one array
  of 144-byte records, and an affix id is the **merged index + 1**: suffix record r is id r + 1, prefix record r is id
  `nSuffix + r + 1` (748 + r with stock data), automagic record r is id 1417 + r. Id 0 means "none", so `magicsuffix`
  record 0 (`of Health`) is a real affix with id 1. Item data holds these ids (prefixes `+0x38`, suffixes `+0x3E`),
  so a save stores prefix record r as r + 1 (`id − firstPrefix`) and suffix record r as r + 1 (the id), 0 = none.
  (fn:sub_00633730_LoadMagicAffixes@0x00633730, fn:MAGICAFFIX_GetRecord@0x00633EE0,
  [items/0005 § 1](../findings/items/0005-affixes.md#1-the-merged-affix-arrays-and-the-ids-0x00633730-0x00633f40))
- `[I]` The game loads both with a 144-byte record (call sites `0x00633D7D` prefix, `0x00633D60` suffix,
  [data/0001 §4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables)).

## Columns

`[C]` layout tags are by data behaviour: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel magicprefix`
decodes 669 records × 40 mapped fields = 26 760 cells, 0 mismatches; `magicsuffix` 747 × 38 = 29 880 cells,
0 mismatches, plus 1 494 cells of the two columns its `.txt` lacks (`etype4`, `etype5`), which hold the
missing-column default `0xFFFF` in every record ([data/0004](../findings/data/0004-cell-converters.md)).
Each offset is the one `excel_bin.py probe` finds. Observed values are from
`python3 -I tools/affix_survey.py columns workspace/merged/data/global/excel <table>` (decoded from the `.bin`;
"blank" counts empty `.txt` cells, which compile to 0, or `0xFF`/`0xFFFF`/−1 for the reference columns).
**Meaning** is the column name's plain reading, `[L]`; what the affix pick does with each generation column is `[I]`
in [§ Code semantics](#code-semantics-items0005) below.

| Column | Prefix: observed | Suffix: observed | `.bin` field | Meaning (`[L]`) | References | Tag |
|---|---|---|---|---|---|---|
| `Name` | str, 252 distinct, len ≤ 14, 32 blank | str, 288 distinct, len ≤ 24, 6 blank | `+0x000` char[34] (see notes) | affix name, a string-table key | string table | [C] |
| `version` | 0 ×118 (32 blank), 1 ×102, 100 ×449 | 0 ×114 (6 blank), 1 ×148, 100 ×485 | `+0x022` u16 | game version the row belongs to | — | [C] |
| `spawnable` | 0..1; 1 ×587, 52 blank | 0..1; 1 ×576, 163 blank | `+0x054` u16 | row may be rolled | — | [C] |
| `rare` | 0..1; 1 ×524, 145 blank | 0..1; 1 ×550, 197 blank | `+0x064` u8 | row may be rolled on a rare item | — | [C] |
| `level` | 0..91 (named rows 1..91) | 0..110 | `+0x058` u32 | lowest affix level | — | [C] |
| `maxlevel` | 0..34, set on 9 rows | 0..44, set on 18 rows | `+0x060` u32 | highest affix level, 0 = none | — | [C] |
| `levelreq` | 0..83 | 0..97 | `+0x065` u8 | character level the affix requires | — | [C] |
| `classspecific` | 7 classes on 116 rows, 553 blank | blank in every row | `+0x066` u8 index, blank `0xFF` | row only for this class's items | `playerclass` `Code` | [C] |
| `class` | blank in every row | 6 classes on 205 rows, 542 blank | `+0x067` u8 index, blank `0xFF` | class for `classlevelreq` | `playerclass` `Code` | [C] |
| `classlevelreq` | blank in every row | 0..33 (20 distinct) | `+0x068` u16 | level requirement for `class` | — | [C] |
| `frequency` | 0..9, 32 blank | 0..10, 130 blank | `+0x082` u16 | pick weight | — | [C] |
| `group` | 101..142 (36 distinct), 32 blank | 1..45 (41 distinct), 6 blank | `+0x05C` u32 | exclusion group | — | [C] |
| `mod1code`..`mod3code` | (`items/properties`) | | `+0x024`, `+0x034`, `+0x044` u32 index, blank −1 | property (out of scope: `items/properties`) | `properties` `code` | [C] |
| `mod1param`..`mod3param` | | | `+0x028`, `+0x038`, `+0x048` s32 | property parameter (`items/properties`) | — | [C] |
| `mod1min`..`mod3min` | | | `+0x02C`, `+0x03C`, `+0x04C` s32 | property minimum (`items/properties`) | — | [C] |
| `mod1max`..`mod3max` | | | `+0x030`, `+0x040`, `+0x050` s32 | property maximum (`items/properties`) | — | [C] |
| `transform` | 1 on 313 rows | 1 on 147 rows | — (not compiled; see notes) | — | — | [C] |
| `transformcolor` | 15 colours on 317 rows | 12 colours on 147 rows | `+0x056` u8 index, blank `0xFF` | item colour shift | [colors](colors.md) `Code` | [C] |
| `itype1`..`itype7` | 26 / 22 / 15 / 15 / 9 / 7 / 3 distinct types | 33 / 27 / 16 / 13 / 6 / 3 / 2 | `+0x06A` + 2·(n−1), u16 index, blank 0 | item types the row is allowed on | [ItemTypes](ItemTypes.md) `Code` | [C] |
| `etype1`..`etype5` | 13 / 7 / 2 / 1 / 1 distinct types | 10 / 6 / 1; `etype4/5` absent | `+0x078` + 2·(n−1), u16 index, blank 0, absent `0xFFFF` | item types the row is excluded from | [ItemTypes](ItemTypes.md) `Code` | [C] |
| `divide`, `multiply`, `add` | `multiply` 1280 ×21, `add` 0..32000; `divide` 0 | 0 in every row | `+0x084`, `+0x088`, `+0x08C` u32 | price adjustment (vendors) | — | [C] |

- `[C]` Every non-blank `itype*`/`etype*` cell resolves to an `itemtypes` code once cut to 4 characters
  (`staff` → `staf`, [data/0004](../findings/data/0004-cell-converters.md)); the `.bin` stores the row index of
  that code. `excel_bin.py diff` checks every one. (tbl:MagicPrefix.txt:itype1, tbl:ItemTypes.txt:Code)
- `[C]` `classspecific` is filled only in `MagicPrefix` and `class`/`classlevelreq` only in `MagicSuffix`.
  (tbl:MagicPrefix.txt:classspecific, tbl:MagicSuffix.txt:class)

## Record layout

`+0x000` `Name` char[34] · `+0x022` `version` · `+0x024..+0x053` three property slots of 16 B (`code` u32,
`param`, `min`, `max` s32) · `+0x054` `spawnable` u16 · `+0x056` `transformcolor` u8 · `+0x057` u8, 0 in every
record · `+0x058` `level` · `+0x05C` `group` · `+0x060` `maxlevel` · `+0x064` `rare` u8 · `+0x065` `levelreq` u8 ·
`+0x066` `classspecific` u8 · `+0x067` `class` u8 · `+0x068` `classlevelreq` u16 · `+0x06A..+0x077` `itype1..7`
u16 · `+0x078..+0x081` `etype1..5` u16 · `+0x082` `frequency` u16 · `+0x084` `divide` · `+0x088` `multiply` ·
`+0x08C` `add` (u32 each). `[C]` (`excel_bin.py diff`, tbl:MagicPrefix.txt:frequency).
`python3 -I tools/excel_bin.py unknown workspace/merged/data/global/excel magicprefix` lists `+0x057` as the
only byte no column covers (0 in every record of both tables).

- `[C]` `transform` is a `.txt` column with no field: it is `1` on 313 prefix and 147 suffix rows, but no byte
  or bit follows it (`+0x057` is 0 throughout). (tbl:MagicPrefix.txt:transform)
- `[I]` `Name` is decoded as char[34] because the next field starts at `+0x022` and the longest name is 24
  characters, but `+0x020..+0x021` is a load-time u16: the loader writes the string key of `Name` there for every
  record, as in `UniqueItems` ([UniqueItems § Record layout](UniqueItems.md#record-layout)). In the file the two bytes
  are 0, which is why the char[34] decode diffs clean. (fn:sub_00633730_LoadMagicAffixes@0x00633730,
  [items/0005 § 1](../findings/items/0005-affixes.md#1-the-merged-affix-arrays-and-the-ids-0x00633730-0x00633f40))
- `[I]` `+0x057` (0 in every record) is read by no pick ([items/0005 § Answers](../findings/items/0005-affixes.md#answers-to-the-phase-0-questions)). The integer widths are the slot decodes `excel_bin.py` uses; signedness of the
  non-negative slots is not pinned by data.

## Generation columns (plan 0021 Phase 0)

Every count here is `[C]` by script, `python3 -I tools/affix_survey.py summary workspace/merged/data/global/excel`
plus the `columns` command above, over named rows (blank rows left out) unless stated.
What the code does with each column is plan 0021 Phase 1.

### Version, frequency, spawnable, rare

| Table | `version` | Rows | `frequency` > 0 | `spawnable` 1 | `rare` 1 |
|---|---:|---:|---:|---:|---:|
| `magicprefix` | 0 | 86 | 0 | 86 | 86 |
| | 1 | 102 | 102 | 100 | 101 |
| | 100 | 449 | 449 | 401 | 337 |
| `magicsuffix` | 0 | 108 | 0 | 108 | 108 |
| | 1 | 148 | 148 | 148 | 147 |
| | 100 | 485 | 467 | 319 | 295 |

- `[C]` **Every `version` 0 row has `frequency` 0** in both tables, and every `version` 1 row has
  `frequency` > 0. In `magicsuffix` 18 `version` 100 rows also have `frequency` 0 (17 of them with
  `spawnable` 0). (tbl:MagicPrefix.txt:version, tbl:MagicPrefix.txt:frequency)
- `[C]` The `version` 0 rows are a block: `magicprefix` records 1..117 and `magicsuffix` records 0..113, all
  before the `Expansion` marker. After it, `version` 1 and 100 rows alternate in runs. 16 of the 36 prefix
  groups and 29 of the 41 suffix groups hold both `version` 0 and later rows: the classic block repeats names
  that come back after the marker with a weight (`Jagged` record 12, `frequency` 0, `version` 0; record 185,
  `frequency` 9, `version` 1). (tbl:MagicPrefix.txt:version)
- `[C]` `spawnable` × `rare` × (`frequency` > 0), named rows:

  | Table | 1·1·>0 | 1·1·0 | 1·0·>0 | 0·1·>0 | 0·0·>0 | 0·0·0 |
  |---|---:|---:|---:|---:|---:|---:|
  | `magicprefix` | 403 | 86 | 98 | 35 | 15 | 0 |
  | `magicsuffix` | 412 | 109 | 54 | 29 | 120 | 17 |

  So 501 prefix and 466 suffix rows are `spawnable` with a non-zero weight.
- `[C]` `frequency`: prefix 0 ×86, 1 ×182, 2 ×98, 3 ×28, 4 ×199, 5 ×13, 6 ×7, 7 ×10, 8 ×8, 9 ×6; suffix 0 ×126,
  1 ×303, 2 ×44, 3 ×77, 4 ×158, 5 ×10, 6 ×9, 7 ×10, 8 ×3, 10 ×1. (tbl:MagicSuffix.txt:frequency)

### Levels

- `[C]` `level`: prefix 1..91 on every named row; suffix 0..110, with `level` 0 on 16 rows (all `version` 100,
  `frequency` 0, group 44, no `itype`; 15 of them `spawnable` 0). (tbl:MagicSuffix.txt:level)
- `[C]` `maxlevel` is set on 9 prefix rows (316, 317, 319 `Shimmering`, 661..666 `Tireless`, `Lizard's`,
  `Azure`, `Crimson`, `Tangerine`, `Beryl`) and 18 suffix rows (204, 205, 207, 209, 211, 213, 729..740);
  in each `maxlevel` ≥ `level`. (tbl:MagicPrefix.txt:maxlevel)
- `[C]` `levelreq` ≤ `level` on every prefix row; 9 suffix rows have `levelreq` > `level` (281 and 283
  `of Greed`, 340 and 346 `of Life`, 437, 465, 467, 469, 471). (tbl:MagicSuffix.txt:levelreq)

### Groups and class rows

- `[C]` `group`: prefix groups 101..142 (36 distinct), largest 125 (119 rows); suffix groups 1..45 (41
  distinct), largest 44 (243 rows). (tbl:MagicPrefix.txt:group)
- `[C]` The 116 `classspecific` prefix rows are all in group 125 (with 3 more rows), `version` 1 ×22 and
  100 ×94, all `spawnable`. The 205 `class` suffix rows are all in group 44 with the same first property
  (`charged`), all `version` 100, 104 `spawnable`. (tbl:MagicPrefix.txt:classspecific, tbl:MagicSuffix.txt:class)

### Item types

- `[C]` Every named prefix row names at least one `itype`. 27 named suffix rows name none (records 424..456
  and 620..642, skill-named rows such as `of Frozen Armor`, `of Battle Orders`, `of Item Finding`), all `version` 100, group 44 or 45, 26 of them
  `spawnable` 0; whatever the type test is, such a row can only match through some other path. 109 prefix and
  100 suffix records name at least one `etype`. (tbl:MagicSuffix.txt:itype1)
- `[C]` `magicsuffix.bin` holds `0xFFFF` in `etype4` and `etype5` of every record (the columns are absent from
  its `.txt`), while a blank cell elsewhere holds 0. A reader that treats any non-zero type index as a real
  type would see `0xFFFF` here. (tbl:MagicSuffix.txt:etype3, [data/0004](../findings/data/0004-cell-converters.md))

### Candidates per item type

`python3 -I tools/affix_survey.py candidates workspace/merged/data/global/excel <type-or-base> <level>` prints,
for each of the five affix tables, the rows that name the item type: the type is expanded through the
[ItemTypes](ItemTypes.md) `Equiv1`/`Equiv2` chains (a base code contributes its `type` and `type2`), a row is
kept when an `itype` is in that set and no `etype` is, and for the three tables with a level column, when
`level` ≤ the given level ≤ `maxlevel` (or `maxlevel` 0). These two rules are the survey's reading of the
column names (`[L]`); `spawnable`, `rare`, `version` and the class columns are printed, not filtered.
Examples (`[C]` counts of the survey, not of the game):

| Query | Type set | Prefix | Suffix | RarePrefix | RareSuffix | AutoMagic |
|---|---|---:|---:|---:|---:|---:|
| `hax 20` (Hand Axe) | `axe mele weap` | 54 | 68 | 37 | 18 | 13 |
| `am1 40` (Stag Bow) | `abow amaz bow clas miss weap` | 104 | 81 | 36 | 14 | 24 |
| `ring 30` | `misc ring` | 64 | 79 | 24 | 16 | 0 |

`[C]` `AutoMagic` rows all name `armo` and `weap`, so for any weapon or armor the type rule keeps every
`AutoMagic` row within the level window; the survey prints the base's `auto prefix` and how many of the rows
carry that group ([AutoMagic](AutoMagic.md)).

## Code semantics (items/0005)

The Phase 0 questions of this doc are answered in
[items/0005 § Answers to the Phase 0 questions](../findings/items/0005-affixes.md#answers-to-the-phase-0-questions). Every statement here is `[I]`: read from the
code, not yet reproduced (plan 0021 Phase 2 logs the picks).

- `[I]` **One pick** (`ITEMS_PickMagicAffix`) walks one block of the merged array (suffixes, prefixes or automagic) in
  record order and keeps a row only if, in this order: `spawnable` ≠ 0 (when the caller asks), `version` < 100 or
  the item is an expansion item, `level` ≤ alvl and (`maxlevel` = 0 or `maxlevel` ≥ alvl), `rare` ≠ 0 on a rare
  (quality 6, 8, 9) item, the type test passes, `group` = the automagic group (automagic picks only), `frequency` ≠ 0,
  `classspecific` is blank or matches the item type's `Class` (or that `Class` is 7, none), and no affix already on the
  item has the same `group`. `spawnable`, `rare`, `frequency`, `classspecific` are read as bytes, `version` as u16,
  `level`, `maxlevel`, `group` as s32. (fn:ITEMS_PickMagicAffix@0x005C1560, fn:sub_005C1500_AffixGroupTaken@0x005C1500,
  [items/0005 § 3](../findings/items/0005-affixes.md#3-items_pickmagicaffixitem-needspawnable-mustroll-applyprops-isprefix-forcedid-autogroup-0x005c1560))
- `[I]` **alvl**, the value `level`/`maxlevel` are compared with: `i = max(ilvl, qlvl)`; with the base's `magic lvl`
  m ≠ 0, `alvl = i + m`; else with `h = qlvl / 2`, `alvl = i − h` when `i < 99 − h`, else `2·i − 99`; clamped to 1..99.
  ([items/0005 § 2](../findings/items/0005-affixes.md#2-alvl-0x005c16340x005c16c2))
- `[I]` **The type test**: any `etype1..5` the item is (through the `Equiv` chains) refuses, and one `itype1..7` must
  match; each list ends at its first value < 1, so the `0xFFFF` absent `etype4/5` of `magicsuffix` (−1 as s16) ends
  the list, and a row with no `itype` (the 27 suffix rows above) is never picked. Before that, a classic item whose
  base is stackable or throwable is refused, and a `sock` row needs a socketable base.
  (fn:ITEMS_MagicAffixTypeOk@0x0065E620, [items/0005 § 3](../findings/items/0005-affixes.md#3-items_pickmagicaffixitem-needspawnable-mustroll-applyprops-isprefix-forcedid-autogroup-0x005c1560))
- `[I]` **The weight** is `frequency`, or `frequency × level` when the base has `magic lvl`; one draw
  `low % (W + 1)` picks by running sum, and a draw of exactly W takes the last candidate.
  ([items/0005 § 4](../findings/items/0005-affixes.md#4-the-weighted-draw-0x005c18210x005c189e))
- `[I]` **`version` 0 rows** (all `frequency` 0) are never picked on the drop path: the `frequency` test drops them, and
  created items never take the classic (version 0) pick body. ([items/0005 § 10](../findings/items/0005-affixes.md#10-classic-items-version--100))
- `[I]` **Not read by any pick**: `levelreq`, `class`, `classlevelreq`, `transformcolor`, the price columns, `+0x057`.
  ([items/0005 § Answers](../findings/items/0005-affixes.md#answers-to-the-phase-0-questions))

## Open questions

- `[L]` Every `[I]` above until plan 0021 Phase 2 reproduces the picks; the Phase 1b cross-check in items/0005 lists
  the points where community documentation disagrees, for Phase 2 to settle.
- `[L]` The meaning of the property columns (`items/properties`).
