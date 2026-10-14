# Properties (`data/global/excel/properties.txt` → `properties.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 268 (269 data rows − 1 `Expansion` marker)   **Record:** 46 B (`0x2E`)
> **sha256:** `.txt` `1cea2a360d804559528e7cfdb4dc30f7e33950d074846ef66e49fbc142bacd18`, `.bin` `5dc97008fb367ff1f4301d784835a93e9e4e0379cd42b1faf013a1f7582dcc3f`
> **Doc status:** every column located; `.bin` layout complete; `set`, `val`, `func` and `stat` read by the code at
> creation `[I]` ([§ Code semantics](#code-semantics-plan-0024-phase-1)); survey of the codes the item tables use
> (plan 0024 Phase 0, drop-path split corrected by Phase 1)

## Purpose

One row per **property code** (`str`, `res-fire`, `dmg-cold`, `skill`…): the name an item table gives a property in
its `(code, param, min, max)` blocks. The row expands the code into up to seven `(set, val, func, stat)` slots:
`func` says how the block's `param`/`min`/`max` become stat values, and `stat` names the [ItemStatCost](ItemStatCost.md)
row written. The tables that name codes are [UniqueItems](UniqueItems.md) (`prop1..12`), [SetItems](SetItems.md)
(`prop1..9`, `aprop1a..5b`), [Sets](Sets.md) (`PCode2a..5b`, `FCode1..8`), [MagicPrefix and MagicSuffix](MagicPrefix.md)
(`mod1..3code`), [AutoMagic](AutoMagic.md) (`mod1..3code`), `qualityitems` (`mod1..2code`), `gems` (`weapon/helm/shieldMod1..3Code`)
and `runes` (`T1Code1..7`). Research-map row `items/properties` (plan 0024). Leads: no lead; derived from data.

## Row identity

- `[C]` The record index is the data row index once the `Expansion` marker is dropped (0..267): records 0..120 come
  before the marker, 121..267 after it (`dru` is record 121). `python3 -I tools/excel_bin.py diff … properties`
  matches record *i* to data row *i* in every column.
- `[C]` `code` is the key, unique in all 268 rows, and is stored as the row's own index (u16 at `+0x000`). Every
  table that names a code stores this row index: `magicprefix`/`magicsuffix`/`automagic` `mod1..3code` (u32,
  [MagicPrefix § layout](MagicPrefix.md)), and, unmapped but found by `probe`, the `prop` blocks of `uniqueitems`
  (`prop1` at `+0x08C`) and `setitems` (`prop1` at `+0x088`).
- `[C]` A code cell that names no row compiles to `-1`. The uniques table has 13 commented-out codes (`*enr` ×4,
  `*mana` ×3, `*hp` ×2, `*vit`, `*charged`, `*hit-skill`, `*gethit-skill`), and each such block holds code `-1`
  in `uniqueitems.bin` (checked for rows 22, 36, 186, 214, 264; the param, min and max are still compiled).
- `[C]` **The code lookup ignores case**: `setitems` row 122 (`Naj's Circlet`) `prop3` is `Light`, and
  `setitems.bin` holds 73 there, the row of `light`. It is the only cell in the source tables that differs from its
  row's `code` by case alone. (`prop_survey.py codes` prints it; `struct.unpack` of `setitems.bin` record 122 `+0x0A8`.)

## Columns

`[C]` layout tags are by data behaviour: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel properties`
decodes all 268 records and matches every mapped cell (268 × 29 = 7 772 cells, 0 mismatches). Observed values from
`python3 -I tools/prop_survey.py columns … properties` (decoded `.bin`; *blank* counts the `.txt` cells).
**Meaning:** `[L]` in this table, from the column name and the comment columns; the code readings that replace
them are in [§ Code semantics](#code-semantics-plan-0024-phase-1).

| Column | Observed (blank / values) | `.bin` field | Meaning (`[L]`) | References | Layout tag |
|---|---|---|---|---|---|
| `code` | str, 268 distinct, 0 blank | `+0x000` u16, the row's own index | property code | named by the source tables above | [C] |
| `*done` | 1 in 243 rows, blank in 25 | — (not compiled) | editor progress mark; blank exactly on the 25 rows with no `func1` | — | [C] (absence) |
| `set1` | 1 in one row (`color`), 267 blank | `+0x002` u8 | flag for the slot's stat write (set rather than add?) | — | [C] |
| `set2..set7` | blank in every row | `+0x003..+0x008` u8 | as `set1` | — | [C] (slots by stride) |
| `val1` | {0 ×260, 1 ×2, 2, 3 ×2, 4, 5, 6}; 259 blank | `+0x00A` 2-byte slot (s16 decode) | fixed value the func uses instead of the block's param: the class number of `ama`(0)…`ass`(6) and `randclassskill`, the element of `fireskill` | — | [C] |
| `val2..val7` | blank in every row | `+0x00C..+0x016`, 2 B each | as `val1` | — | [C] (slots by stride) |
| `func1` | 0..36, 22 distinct; 25 blank | `+0x018` u8 | how the block becomes stat values | — | [C] |
| `func2` | {3 ×5, 16 ×8}; 255 blank | `+0x019` u8 | as `func1`, second slot | — | [C] |
| `func3` | {3 ×5, 15, 17 ×2}; 260 blank | `+0x01A` u8 | third slot | — | [C] |
| `func4` | {3 ×3, 16, 17}; 263 blank | `+0x01B` u8 | fourth slot | — | [C] |
| `func5`, `func6`, `func7` | 15, 16, 17 in one row each (`dmg-elem`) | `+0x01C`, `+0x01D`, `+0x01E` u8 | fifth to seventh slot | — | [C] |
| `stat1` | 210 distinct stats; 30 blank | `+0x020` u16 stat index, blank `0xFFFF` | stat the slot writes | `itemstatcost` `Stat` | [C] |
| `stat2` | 11 distinct; 255 blank | `+0x022` u16 stat index | second slot | `itemstatcost` `Stat` | [C] |
| `stat3` | 8 distinct; 260 blank | `+0x024` u16 stat index | third | `itemstatcost` `Stat` | [C] |
| `stat4` | 5 distinct; 263 blank | `+0x026` u16 stat index | fourth | `itemstatcost` `Stat` | [C] |
| `stat5`, `stat6`, `stat7` | one row each (`dmg-elem`: `coldmindam`, `coldmaxdam`, `coldlength`) | `+0x028`, `+0x02A`, `+0x02C` u16 stat index | fifth to seventh | `itemstatcost` `Stat` | [C] |
| `*desc`, `*param`, `*min`, `*max`, `*notes` | comment text | — (not compiled) | what the block's columns mean for this code | — | [C] (absence) |
| `*eol` | end-of-line marker column | — | — | — | — |

- `[C]` Every `stat1..7` cell resolves to an `itemstatcost` row (`diff` 0 mismatches; a name that resolved nowhere
  would store `0xFFFF` against a non-blank cell).
- `[C]` Slots: `set2..7` and `val2..7` are blank in every row, so `probe` places them only as "any zero byte"; their
  slots follow the strides of `set1` (1 B) and `val1` (2 B) and end where the next array starts. The width of `val1`
  is 2 bytes (the stride), but no cell is negative, so the sign is not fixed by the data.

## Record layout

`+0x000` `code` u16 (own row index) · `+0x002..+0x008` `set1..7` u8 · `+0x009` u8, 0 in every record ·
`+0x00A..+0x017` `val1..7`, 2 B each · `+0x018..+0x01E` `func1..7` u8 · `+0x01F` u8, 0 in every record ·
`+0x020..+0x02D` `stat1..7` u16 stat index (blank `0xFFFF`). `[C]` (`diff`; `excel_bin.py unknown … properties`
lists only `+0x009` and `+0x01F`, both 0 in all 268 records.)

## Interpretation notes

- **Slots.** `[C]` A code fills its slots from slot 1 without gaps: 243 rows have `func1`, 13 also use slot 2, 8 slot 3,
  5 slot 4, one (`dmg-elem`) slots 5..7. The multi-slot codes are `res-all`, `res-all-max`, `all-stats`,
  `dmg-elem-min` (func 1 then func 3 for the other stats), `dmg-elem-max` (the same, then func 17 `coldlength`) and the damage pairs `dmg-fire`, `dmg-ltng`, `dmg-mag`,
  `dmg-cold`, `dmg-pois`, `dmg-throw`, `dmg-norm`, `dmg-elem` (func 15 = min stat, 16 = max stat, 17 = length).
  `[I]` func 3 reuses the value func 1 rolled for the first slot, unless slot 1 wrote nothing (rolled 0), in which
  case each func-3 slot rolls its own ([items/0006 § 4](../findings/items/0006-properties.md#4-the-handlers-per-func),
  fn:PROP_Func03_Reuse@0x0065EC10).
- **Funcs with no stat.** `[C]` Five codes have a `func1` and a blank `stat1`: `dmg-min` (5), `dmg-max` (6),
  `dmg%` (7), `indestruct` (20) and `ethereal` (23). `[I]` These funcs pick their stats themselves:
  funcs 5 and 6 write 21/23/159 and 22/24/160 by the base's damage columns, func 7 stats 18 and 17 (or +1 max damage
  through func 6), func 20 stat 152, func 23 the ethereal flag (items/0006 § 4, fn:PROP_Func05_DmgMin@0x0065ECF0,
  fn:PROP_Func07_DmgPercent@0x0065F010, fn:PROP_Func23_Ethereal@0x0065FD20).
- **No func.** `[C]` 25 rows have no `func1` (and `*done` blank): `gembonus`, `regen-dur`, `fire-fx`, `ltng-fx`,
  `gems%/lvl`, `item%`, the 12 `dmg/abs-slash/crush/thrust` codes, `gems%/time` and the 8 `…-mon` codes. No source
  table names any of them.
- **The `Expansion` marker** separates records 0..120 from 121..267 and takes no index. `[L]` The later rows are the
  expansion's additions (`dru`, `ass`, the `/lvl` and `/time` families).

## Code semantics (plan 0024 Phase 1)

From [items/0006](../findings/items/0006-properties.md) (static reading of `Game.exe`). Tags are the finding's.

- `[I]` **Walk.** A block expands its row's slots 1..7 in order and stops at the first `func` 0 (or ≥ 37). Slot *k*
  calls `g_PropFuncTable[func]` with the slot's `set`, `stat` and `val` and the whole `(code, par, min, max)` block;
  slot 1's return value is handed to slots 2..7 as *prev* (items/0006 § 3, fn:PROP_ApplyBlock@0x0065FD70,
  data:g_PropFuncTable@0x007462F8). `[C]` The table pointer and count are `DataTables+0xA4`/`+0xAC`, where the loader
  stores them (data:g_pProperties@0x0096BCD4, data:g_nProperties@0x0096BCDC).
- `[I]` **`set`.** 0 adds the value to the existing (stat, param) entry, non-zero replaces it; `color` is the only
  row with `set1` 1 (items/0006 § 7, fn:PROP_WriteStat@0x0065EA50, tbl:Properties.txt:set1).
- `[I]` **`val`.** Read by two funcs only: func 21 uses it as the stat param (the class of `ama`..`ass`, the element
  of `fireskill`), func 36 as the stat value with the rolled class as param (`randclassskill`) (items/0006 § 4,
  fn:PROP_Func21_ValParam@0x0065FB50, fn:PROP_Func36_RandClassSkill@0x0065FBA0, tbl:Properties.txt:val1).
- `[I]` **`func`: what each draws and writes** is the table in
  [items/0006 § 4](../findings/items/0006-properties.md#4-the-handlers-per-func). In short: one value roll
  `PROP_RollValue(min, max)` (no draw when `min = max`, else one `RNG_RangeB(item seed, |max − min| + 1)`); funcs 11,
  15, 16, 18, 20 and 23 never draw; funcs 3, 5–8, 10 and 24 draw only when *prev* is 0; func 17 draws only when `par`
  is 0; func 19 makes one charge draw of its own (fn:PROP_RollValue@0x0065E9E0, fn:PROP_Func19_Charged@0x0065F6A0).
- `[I]` **`stat`.** The written value is `value << ValShift`, and a value of 0 writes nothing; `op` and its columns
  are not read at creation (fn:PROP_WriteStat@0x0065EA50, tbl:ItemStatCost.txt:ValShift).
- `[I]` **The superior builder reads `qualityitems` `mod1..2`** (mode 1, 2 blocks), so func 13 `dur%` is on the drop
  path (items/0006 § 2, fn:sub_0065FEC0_ItemApplyProps@0x0065FEC0).
- `[C]` **The code lookup ignores case** (§ Row identity): the loader and every `prop`/`mod` cell lower-case through
  `STR_ToLowerN` (items/0006 § 8, fn:EXCEL_FindName@0x006BD3C0).

## Survey: the codes the item tables use

`python3 -I tools/prop_survey.py codes|funcs|stats|summary workspace/merged/data/global/excel`. The `properties` and
`itemstatcost` records are decoded from the `.bin`; the source tables' blocks are read from their `.txt` (their `.bin`
blocks are unmapped or have no layout). A block is used when its code cell is not blank and names a row (exactly,
else case-insensitively); the 13 commented-out unique codes are skipped as the compiler stores `-1` for them.

The **drop path** is the set of blocks rolled when the item is created. `[I]` It is `uniqueitems` `prop1..12`,
`setitems` `prop1..9` and `aprop1a..5b`, `magicprefix`/`magicsuffix`/`automagic` `mod1..3`, and `qualityitems`
`mod1..2` (the superior builder, mode 1), per [items/0006 § 2](../findings/items/0006-properties.md#2-sub_0065fec0_itemapplypropsmode-a2-item-row-a5-a6-0x0065fec0)
(fn:sub_0065FEC0_ItemApplyProps@0x0065FEC0). `[C]` The `aprop` blocks are on it: set mode applies them right after
`prop1..9` with the same item-seed draws, and the save writer's set lists are the second code path (items/0006 § 2,
data:g_SetAPropStates@0x006EDB40). Off the drop path, `[I]` not reached from `ItemCreate`: `sets` (set bonuses,
applied when worn, fn:sub_00660120_SetBonusApply@0x00660120), `gems` (socketed) and `runes` (runewords). Until
plan 0024 Phase 1 the survey counted `aprop` off the drop path (the Phase 0 working scope); the counts below are
the corrected split. `rareprefix`/`raresuffix` carry no
property columns. A **live** row passes its table's own filter: `uniqueitems` `enabled` = 1
([items/uniques-sets](../specs/items/uniques-sets.md)), the affix tables `spawnable` = 1; other sources count every row.

- `[C]` 183 codes are used by some source (180 on the drop path), 85 rows by none. 155 stats are written (152 on the
  drop path). Rows with at least one used block: uniqueitems 387, setitems 127 (`aprop` 84), magicprefix 637,
  magicsuffix 725, automagic 36, qualityitems 8, sets 32, gems 68, runes 80.
- `[C]` **23 distinct `func` values** occur (1, 2, 3, 5, 6, 7, 8, 10..24, 36; 4, 9 and 25..35 never), and **every one
  is reached on the drop path** by at least one row. A row counts once under each func its codes use (so a row with
  `dmg-cold` counts under 15, 16 and 17), and once per source, so a set item with the func in a `prop` and in an
  `aprop` counts under `set` and under `aprop`:

| func | codes with it | drop rows | live | blocks | min = max | non-numeric par | other rows | drop rows by source | codes used on the drop path |
|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| 1 | 111 | 1336 | 1301 | 2771 | 1710 | 0 | 175 | uniq 385, set 124, aprop 51, mpre 380, msuf 366, auto 27, qual 3 | `str`, `ac`, `res-fire`, … (99) |
| 2 | 1 | 156 | 156 | 156 | 29 | 0 | 15 | uniq 124, set 11, aprop 4, mpre 15, qual 2 | `ac%` |
| 3 | 5 | 105 | 104 | 109 | 57 | 0 | 45 | uniq 57, set 10, aprop 10, mpre 23, auto 5 | `all-stats`, `res-all`, `res-all-max` |
| 5 | 1 | 49 | 38 | 49 | 30 | 0 | 3 | uniq 11, set 3, mpre 19, msuf 16 | `dmg-min` |
| 6 | 1 | 85 | 62 | 85 | 33 | 0 | 4 | uniq 12, set 1, mpre 30, msuf 42 | `dmg-max` |
| 7 | 1 | 249 | 248 | 249 | 47 | 0 | 41 | uniq 187, set 15, aprop 2, mpre 37, auto 5, qual 3 | `dmg%` |
| 8 | 15 | 267 | 267 | 282 | 282 | 0 | 52 | uniq 177, set 40, aprop 13, msuf 37 | `swing1..3`, `cast1..3`, `move1..3`, `balance1..3`, `block2`, `block3` |
| 10 | 1 | 142 | 142 | 150 | 131 | 0 | 3 | uniq 35, set 9, aprop 5, mpre 84, auto 9 | `skilltab` |
| 11 | 6 | 110 | 107 | 125 | 7 | 33 | 37 | uniq 76, set 11, aprop 1, msuf 22 | `att-skill`, `hit-skill`, `gethit-skill`, `kill-skill`, `death-skill`, `levelup-skill` |
| 12 | 1 | 1 | 1 | 1 | 0 | 0 | 0 | uniq 1 | `skill-rand` |
| 13 | 1 | 4 | 4 | 4 | 0 | 0 | 0 | qual 4 | `dur%` |
| 14 | 1 | 28 | 28 | 28 | 17 | 0 | 0 | uniq 16, set 9, mpre 3 | `sock` |
| 15 | 8 | 184 | 183 | 209 | 63 | 0 | 25 | uniq 124, set 15, aprop 6, mpre 17, msuf 22 | `dmg-norm`, `dmg-fire`, `dmg-ltng`, `dmg-mag`, `dmg-cold`, `dmg-pois`, `dmg-elem` |
| 16 | 8 | 184 | 183 | 209 | 63 | 0 | 25 | as func 15 | as func 15 |
| 17 | 44 | 213 | 184 | 246 | 215 | 0 | 26 | uniq 94, set 14, aprop 26, mpre 44, msuf 35 | 27 `…/lvl` codes, `dmg-cold`, `dmg-pois`, `dmg-elem`, `rep-dur`, `rep-quant` |
| 18 | 36 | 2 | **0** | 2 | 0 | 0 | 0 | msuf 2 | `ac/time` |
| 19 | 1 | 236 | 135 | 244 | 0 | 21 | 20 | uniq 30, set 1, msuf 205 | `charged` |
| 20 | 1 | 22 | 22 | 22 | 22 | 0 | 4 | uniq 16, set 5, msuf 1 | `indestruct` |
| 21 | 8 | 111 | 111 | 111 | 104 | 0 | 18 | uniq 57, set 6, aprop 1, mpre 47 | `ama`, `pal`, `nec`, `sor`, `bar`, `dru`, `ass`, `fireskill` |
| 22 | 3 | 46 | 46 | 90 | 58 | 26 | 32 | uniq 45, set 1 | `skill`, `oskill`, `aura` |
| 23 | 1 | 4 | 4 | 4 | 4 | 0 | 1 | uniq 4 | `ethereal` |
| 24 | 4 | 1 | 1 | 1 | 1 | 0 | 7 | uniq 1 | `reanimate` |
| 36 | 1 | 1 | 1 | 1 | 0 | 0 | 0 | uniq 1 | `randclassskill` |

  (uniq = uniqueitems, set = setitems `prop`, aprop = setitems `aprop`, mpre/msuf = magicprefix/magicsuffix, auto = automagic, qual = qualityitems.
  *min = max* counts the blocks whose `min` and `max` cells are equal; *non-numeric par* the blocks whose `par` is a
  name, such as a skill.)
- `[C]` Rare paths on the drop path: func 18 (`ac/time`) is named only by two `magicsuffix` rows with `spawnable` 0,
  so no live drop-path row uses it; funcs 12, 24 and 36 have one row each, all uniques; func 13 (`dur%`) comes only
  from `qualityitems`, and func 23 (`ethereal`) only from four uniques.
- `[C]` `prop_survey.py stats` lists, per stat a used code writes, its `Save Bits`, `Save Param Bits`, `Encode` and
  `op`. On the drop path all 152 stats have `Save Bits` > 0, 14 have `Save Param Bits` > 0 (the skill stats), 10 have
  `Encode` > 0 and 34 have an `op` (the `/lvl` stats with `op base` `level`, and the stats with derived targets such as
  `energy` → `maxmana`). Details in [ItemStatCost](ItemStatCost.md#interpretation-notes).

## Open questions

- ~~What each `func` draws and writes, how `set` and `val` are used, and whether func 3 reuses the slot-1 value~~
  answered in [§ Code semantics](#code-semantics-plan-0024-phase-1) (items/0006 § 4).
- ~~Whether the superior builder reads `qualityitems`, and whether `setitems` `aprop` lists are rolled at creation~~
  answered: both yes (items/0006 § 2); the survey's split is corrected.
- `[L]` What `add func` 1 and 2 change for the `aprop` lists is equip-time code (`sub_00660120_SetBonusApply`), not
  read by plan 0024 Phase 1.
