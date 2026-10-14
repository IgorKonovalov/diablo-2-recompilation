# Properties (`data/global/excel/properties.txt` → `properties.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 268 (269 data rows − 1 `Expansion` marker)   **Record:** 46 B (`0x2E`)
> **sha256:** `.txt` `1cea2a360d804559528e7cfdb4dc30f7e33950d074846ef66e49fbc142bacd18`, `.bin` `5dc97008fb367ff1f4301d784835a93e9e4e0379cd42b1faf013a1f7582dcc3f`
> **Doc status:** every column located; `.bin` layout complete; semantics `[L]`; survey of the codes the item tables
> use (plan 0024 Phase 0)

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
**Meaning:** `[L]`, from the column name and the comment columns.

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
  `[L]` func 3 reuses the value func 1 rolled for the first slot (the `*notes` say so; one roll for all four resists).
- **Funcs with no stat.** `[C]` Five codes have a `func1` and a blank `stat1`: `dmg-min` (5), `dmg-max` (6),
  `dmg%` (7), `indestruct` (20) and `ethereal` (23). `[L]` These funcs pick their stats themselves (the weapon
  damage stats by the base's damage columns, the durability and ethereal flags).
- **No func.** `[C]` 25 rows have no `func1` (and `*done` blank): `gembonus`, `regen-dur`, `fire-fx`, `ltng-fx`,
  `gems%/lvl`, `item%`, the 12 `dmg/abs-slash/crush/thrust` codes, `gems%/time` and the 8 `…-mon` codes. No source
  table names any of them.
- **The `Expansion` marker** separates records 0..120 from 121..267 and takes no index. `[L]` The later rows are the
  expansion's additions (`dru`, `ass`, the `/lvl` and `/time` families).

## Survey: the codes the item tables use

`python3 -I tools/prop_survey.py codes|funcs|stats|summary workspace/merged/data/global/excel`. The `properties` and
`itemstatcost` records are decoded from the `.bin`; the source tables' blocks are read from their `.txt` (their `.bin`
blocks are unmapped or have no layout). A block is used when its code cell is not blank and names a row (exactly,
else case-insensitively); the 13 commented-out unique codes are skipped as the compiler stores `-1` for them.

The **drop path** is this survey's reading of the plan's scope, not a claim about the code: `uniqueitems` `prop1..12`,
`setitems` `prop1..9`, `magicprefix`/`magicsuffix`/`automagic` `mod1..3`, and `qualityitems` `mod1..2` (that the
superior builder reads `qualityitems` is a lead). Off the drop path: `setitems` `aprop1a..5b` (partial-set bonuses),
`sets` (set bonuses, applied when worn), `gems` (socketed) and `runes` (runewords). `rareprefix`/`raresuffix` carry no
property columns. A **live** row passes its table's own filter: `uniqueitems` `enabled` = 1
([items/uniques-sets](../specs/items/uniques-sets.md)), the affix tables `spawnable` = 1; other sources count every row.

- `[C]` 183 codes are used by some source (180 on the drop path), 85 rows by none. 155 stats are written (152 on the
  drop path). Rows with at least one used block: uniqueitems 387, setitems 127 (`aprop` 84), magicprefix 637,
  magicsuffix 725, automagic 36, qualityitems 8, sets 32, gems 68, runes 80.
- `[C]` **23 distinct `func` values** occur (1, 2, 3, 5, 6, 7, 8, 10..24, 36; 4, 9 and 25..35 never), and **every one
  is reached on the drop path** by at least one row. A row counts once under each func its codes use (so a row with
  `dmg-cold` counts under 15, 16 and 17):

| func | codes with it | drop rows | live | blocks | min = max | non-numeric par | other rows | drop rows by source | codes used on the drop path |
|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| 1 | 111 | 1285 | 1250 | 2683 | 1624 | 0 | 226 | uniq 385, set 124, mpre 380, msuf 366, auto 27, qual 3 | `str`, `ac`, `res-fire`, … (99) |
| 2 | 1 | 152 | 152 | 152 | 25 | 0 | 19 | uniq 124, set 11, mpre 15, qual 2 | `ac%` |
| 3 | 5 | 95 | 94 | 99 | 47 | 0 | 55 | uniq 57, set 10, mpre 23, auto 5 | `all-stats`, `res-all`, `res-all-max` |
| 5 | 1 | 49 | 38 | 49 | 30 | 0 | 3 | uniq 11, set 3, mpre 19, msuf 16 | `dmg-min` |
| 6 | 1 | 85 | 62 | 85 | 33 | 0 | 4 | uniq 12, set 1, mpre 30, msuf 42 | `dmg-max` |
| 7 | 1 | 247 | 246 | 247 | 45 | 0 | 43 | uniq 187, set 15, mpre 37, auto 5, qual 3 | `dmg%` |
| 8 | 15 | 254 | 254 | 269 | 269 | 0 | 65 | uniq 177, set 40, msuf 37 | `swing1..3`, `cast1..3`, `move1..3`, `balance1..3`, `block2`, `block3` |
| 10 | 1 | 137 | 137 | 145 | 126 | 0 | 8 | uniq 35, set 9, mpre 84, auto 9 | `skilltab` |
| 11 | 6 | 109 | 106 | 124 | 7 | 32 | 38 | uniq 76, set 11, msuf 22 | `att-skill`, `hit-skill`, `gethit-skill`, `kill-skill`, `death-skill`, `levelup-skill` |
| 12 | 1 | 1 | 1 | 1 | 0 | 0 | 0 | uniq 1 | `skill-rand` |
| 13 | 1 | 4 | 4 | 4 | 0 | 0 | 0 | qual 4 | `dur%` |
| 14 | 1 | 28 | 28 | 28 | 17 | 0 | 0 | uniq 16, set 9, mpre 3 | `sock` |
| 15 | 8 | 178 | 177 | 198 | 62 | 0 | 31 | uniq 124, set 15, mpre 17, msuf 22 | `dmg-norm`, `dmg-fire`, `dmg-ltng`, `dmg-mag`, `dmg-cold`, `dmg-pois`, `dmg-elem` |
| 16 | 8 | 178 | 177 | 198 | 62 | 0 | 31 | as func 15 | as func 15 |
| 17 | 44 | 187 | 158 | 218 | 191 | 0 | 52 | uniq 94, set 14, mpre 44, msuf 35 | 27 `…/lvl` codes, `dmg-cold`, `dmg-pois`, `dmg-elem`, `rep-dur`, `rep-quant` |
| 18 | 36 | 2 | **0** | 2 | 0 | 0 | 0 | msuf 2 | `ac/time` |
| 19 | 1 | 236 | 135 | 244 | 0 | 21 | 20 | uniq 30, set 1, msuf 205 | `charged` |
| 20 | 1 | 22 | 22 | 22 | 22 | 0 | 4 | uniq 16, set 5, msuf 1 | `indestruct` |
| 21 | 8 | 110 | 110 | 110 | 103 | 0 | 19 | uniq 57, set 6, mpre 47 | `ama`, `pal`, `nec`, `sor`, `bar`, `dru`, `ass`, `fireskill` |
| 22 | 3 | 46 | 46 | 90 | 58 | 26 | 32 | uniq 45, set 1 | `skill`, `oskill`, `aura` |
| 23 | 1 | 4 | 4 | 4 | 4 | 0 | 1 | uniq 4 | `ethereal` |
| 24 | 4 | 1 | 1 | 1 | 1 | 0 | 7 | uniq 1 | `reanimate` |
| 36 | 1 | 1 | 1 | 1 | 0 | 0 | 0 | uniq 1 | `randclassskill` |

  (uniq = uniqueitems, set = setitems `prop`, mpre/msuf = magicprefix/magicsuffix, auto = automagic, qual = qualityitems.
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

- `[L]` What each `func` draws and writes, how `set` and `val` are used, and whether func 3 reuses the slot-1 value:
  plan 0024 Phase 1 (reverser).
- `[L]` Whether the superior builder reads `qualityitems` (which would put func 13 `dur%` on the drop path), and
  whether `setitems` `aprop` lists are rolled at creation: plan 0024 Phase 1.
