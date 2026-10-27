# MonEquip (`data/global/excel/monequip.txt` → `monequip.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 45 (44 data rows and the `*end*` row; no `Expansion` marker)   **Record:** 28 B (`0x1C`)
> **sha256:** `.txt` `0254d070195e61ada97cec052ae14aaf10597bb1c5fc4da7eddde5cd05a7e17f`, `.bin` `d99930fa66da9b03e60305266d6d0d3d7e24e3aac5e742e1ae9967a2107dc8ad`
> **Doc status:** layout complete (plan 0051 Phase 0); readers of `monster`, `level`, `oninit` and the locations from
> [monsters/0004 § 6](../findings/monsters/0004-stats.md#6-appearance-and-monequip-draws) and
> [chain/0002 § 11](../findings/chain/0002-retirements.md#11-oracle-13-monequips-items); `mod1..3` `[L]`

## Purpose

One row per piece of equipment a monster class may wear: the class, the lowest monster level the row applies to,
up to three item codes with a body location and a mod each, and an `oninit` flag. Reader: `MonEquipInit` (`0x005D6B60`)
at monster creation and from the summon code (§ Interpretation notes). The question it answers for plan 0048
(oracle 13): whether stock data reaches `MonEquipInit`'s item creation, and for which classes. Requested by the
[MonEquip entry](../backlog/archive/2026-10-20-architect-archivist-monequip-table-doc-for-plan-0048.md).

## Row identity

- `[C]` The `.bin` is a u32 record count (45) and 45 records of 28 bytes, one per `.txt` row in order, the `*end*  do
  not remove` row included ([excel-bin.md](../formats/excel-bin.md)); the loader's record size is 28
  ([data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables), `0x0065A03B`).
- `[C]` Rows are grouped by class, five classes in this order: `bloodraven` (record 267, 1 row), `flyingscimitar`
  (234, 1 row), `valkyrie` (357, 19 rows), `shadowwarrior` (417, 4 rows), `shadowmaster` (418, 19 rows); then the
  `*end*` row, whose class does not resolve and is stored as −1. The class numbers are MonStats record indices (the
  distinct-`Id` ordinal, [MonStats § Row identity](MonStats.md#row-identity); the `.txt` row numbers of the last two are 418
  and 419, after the duplicate `cr_lancer8`). Within a class the rows run from the highest `level` down.
- `[I]` A class's first row is found at load, not stored here: `MONEQUIP_Load` sets every MonStats `+0x02A` to −1, then,
  for each row whose `monster` is a valid record and whose class still has −1, to that row's index; the field is 0 in
  `monstats.bin` ([data/0004 § 3](../findings/data/0004-cell-converters.md#3-runtime-fillers-of-no-column-fields),
  fn:MONEQUIP_Load@0x00659E60; [MonStats § Fields with no `.txt` column](MonStats.md#fields-with-no-txt-column)).

## Columns

`[C]` layout: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel monequip`: 45 records × 12 mapped
fields = 540 cells, **0 mismatches** (the `*end*` class is the one non-blank reference that matches no row, stored −1).
`excel_bin.py unknown` shows `+0x005..+0x007` and `+0x01A..+0x01B` 0 in every record, with no column. `probe` pins the
offsets of `monster` (with the distinct-ordinal lookup), `level`, `oninit`, `item1..3`, `loc1` and `mod1`. It cannot
separate `loc2` from `loc3` (`+0x015`/`+0x016`) or `mod2` from `mod3` (`+0x018`/`+0x019`): the 9 rows that set the
second slot also set the third with the same location and mod. So those four are placed by the group's order, `[I]`.
Values over the 44 data rows (the `*end*` row left out), by script over the `.txt`.

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `monster` | str, 5 distinct: `bloodraven` 1, `flyingscimitar` 1, `valkyrie` 19, `shadowwarrior` 4, `shadowmaster` 19 rows | `+0x000` s16 MonStats record (−1 for `*end*`) | the class the row equips; `[I]` `MONEQUIP_Load` keys the class's first row on it (§ Row identity) and `MonEquipInit` walks the rows of the unit's class from there ([monsters/0004 § 6](../findings/monsters/0004-stats.md#6-appearance-and-monequip-draws); fn:sub_005D30A0_MonEquipFirstRow@0x005D30A0) | `monstats:Id` (distinct ordinal) | [C] offset; width [I] (s16, the reverser's note in the entry) |
| `oninit` | int {1} on 2 rows (`bloodraven`, `flyingscimitar`), 42 blank | `+0x004` u8 | `[C]` `MonEquipInit` tests the byte `(char) row[+4]` of the class's first row; `[I]` at creation the walk runs only when it is set and the unit has an inventory ([chain/0002 § 11](../findings/chain/0002-retirements.md#11-oracle-13-monequips-items), [monsters/0004 § 6](../findings/monsters/0004-stats.md#6-appearance-and-monequip-draws); fn:sub_005D6B60_MonEquipInit@0x005D6B60, 0x005D6BA5) | — | [C] offset; width [I] (`+0x005..+0x007` are 0, so u8 to u32 all fit; the code reads a byte) |
| `level` | int 0..27 (20 distinct) | `+0x002` s16 | `[C]` the s16 `MonEquipInit` compares with the monster level ([chain/0002 § 11](../findings/chain/0002-retirements.md#11-oracle-13-monequips-items); fn:sub_005D6B60_MonEquipInit@0x005D6B60); `[I]` the walk starts at the first row of the class whose `level` is at most the monster level and takes every following row of the class ([monsters/0004 § 6](../findings/monsters/0004-stats.md#6-appearance-and-monequip-draws)) | — | [C] offset; width [I] (s16, as read) |
| `item1` | str, 26 distinct, 8 blank | `+0x008` char[4] code | the item code of slot 1; `[I]` created by `sub_00573B20_MonEquipItemCreate` and equipped on the monster, with item flag `0x1000` ([items/0010](../findings/items/0010-quest-drops.md), fn:sub_00573B20_MonEquipItemCreate@0x00573B20) | [Weapons](Weapons.md) / [Armor](Armor.md) / [Misc](Misc.md) `code` | [C] |
| `loc1` | str, 10 distinct (`head`, `neck`, `tors`, `rarm`, `larm`, `rrin`, `lrin`, `belt`, `feet`, `glov`), 0 blank | `+0x014` u8 BodyLocs row (1..10; blank 0) | body location of slot 1; `[I]` the walk counts a row's leading slots with a location in 1..10 (at most 3) and, when there is one or more, draws one on the unit seed; the item is made only when that location is free ([monsters/0004 § 6](../findings/monsters/0004-stats.md#6-appearance-and-monequip-draws)) | `bodylocs:Code` | [C] |
| `mod1` | int {3, 4, 6}: 3 ×5, 4 ×18, 6 ×21 | `+0x017` u8 | mod of slot 1 (the name's reading; the item quality numbers would read 3 superior, 4 magic, 6 rare) `[L]` | — | [C] offset |
| `item2` | str {`7xf` 3, `7tw` 3, `umg` 3}, 35 blank | `+0x00C` char[4] code | item code of slot 2 (as `item1`) | as `item1` | [C] |
| `loc2` | str {`rarm`, `larm`, `glov`}, 3 each, 35 blank | `+0x015` u8 BodyLocs row | body location of slot 2 (as `loc1`) | `bodylocs:Code` | [C] value; slot by order [I] |
| `mod2` | int {3, 4, 6}, 3 each, 35 blank | `+0x018` u8 | mod of slot 2 `[L]` | — | [C] value; slot by order [I] |
| `item3` | str {`7qr` 6, `uhg` 3}, 35 blank | `+0x010` char[4] code | item code of slot 3 (as `item1`) | as `item1` | [C] |
| `loc3` | str {`rarm`, `larm`, `glov`}, 3 each, 35 blank | `+0x016` u8 BodyLocs row | body location of slot 3 (as `loc1`) | `bodylocs:Code` | [C] value; slot by order [I] |
| `mod3` | int {3, 4, 6}, 3 each, 35 blank | `+0x019` u8 | mod of slot 3 `[L]` | — | [C] value; slot by order [I] |
| `eol` | int {0} | — (not compiled) | end-of-line marker | — | [C] (no field) |

## Interpretation notes

- `[C]` **The two `oninit` classes.** Only the first rows of `bloodraven` (267) and `flyingscimitar` (234) set
  `oninit`; each class has that one row, of `level` 0, with one location (`rarm`, BodyLocs 4) and one item (`sbw` and
  `scm`, mod 6). The `[C]` of oracle 13 covers that path in four logged creations, Blood Raven three times (Nightmare)
  and a flying scimitar once: one row, one location, the masked unit-seed step, one item at a free location
  ([chain/0002 § 11](../findings/chain/0002-retirements.md#11-oracle-13-monequips-items),
  [chain/0003](../findings/chain/0003-end-to-end-run.md); fn:sub_005D6B60_MonEquipInit@0x005D6B60, run:2026-10-21-chain2).
  With the stock table, a creation never meets the level skip, a second row, two or three locations or an occupied
  location: those branches stay `[I]` (chain/0002 § 11).
- **Where the two classes are met.** `[C]` No `Levels` cell, no `SuperUniques` `Class` and no `MonPreset` row names
  `flyingscimitar` or `bloodraven` by class (by script over the `.txt` files); the Act 1 MonPreset row names the MonPlace
  entry `place_bloodraven` ([MonPreset](MonPreset.md)). `[I]` The preset code places MonPlace row 5 `place_bloodraven`
  as class 267 ([MonPlace § Interpretation notes](MonPlace.md#interpretation-notes),
  [monsters/0003 § 7](../findings/monsters/0003-special-monsters.md#7-monplace-presets-2-and-3-and-0x110x20)). `[I]` Class 234 is the default
  class (`0xEA`) of the object-region class pick (`sub_005474C0_RegionActClass`), used when no pool entry falls in its
  class ranges: the trap, casket and barrel spawns ([monsters/0001](../findings/monsters/0001-level-pool.md),
  fn:sub_005474C0_RegionActClass@0x005474C0). Which level the logged flying scimitar was on is the run's
  ([chain/0003](../findings/chain/0003-end-to-end-run.md)), not this table's.
- `[I]` **The other three classes** are player summons (`valkyrie`, the assassin's `shadowwarrior` and `shadowmaster`),
  42 rows with no `oninit`, keyed by `level` from 27 down to 0. The summon code calls `MonEquipInit` for them; whether
  the walk then runs is open (§ Open questions), since none of the 42 has `oninit`: `sub_005C4470_SummonInitStats` ends with it
  ([skills/0003 § 7](../findings/skills/0003-handlers.md#7-summons); fn:sub_005C4470_SummonInitStats@0x005C4470), and
  do 49 (Shadow Warrior, Shadow Master) calls `MonEquipInit(m, id, lvl, level, 0)` after its boundary with a level from
  `SkillParam5ByLevel` capped by `ExpMaxLevel`
  ([skills/0014 § 6](../findings/skills/0014-assassin.md#6-traps-states-and-areas-do-43-44-45-47-48-49-51-54);
  fn:sub_005D6E70_SkillDo49Shadow@0x005D6E70). Do 49's last argument is 0, the creation's 1 (`SummonInitStats`' arguments are not
  recorded in skills/0003); whether that argument skips the `oninit` test is not read (§ Open questions).
- `[C]` Eight rows (two `shadowwarrior`, six `shadowmaster`) have a `loc1` (`tors` or `head`) and no `item1`; 9 rows
  (all `shadowmaster`) fill all three slots, with one location and one mod for the three.

## Open questions

- `[L]` What `mod1..3` select (an item quality is the name's reading): `sub_00573B20_MonEquipItemCreate`'s use of
  them is not read.
- `[L]` Whether `MonEquipInit`'s last argument (1 at creation, 0 in do 49) skips the `oninit` test, so that the summons'
  rows are walked; and what a row with a location and a blank item code makes. A reverser question for the summon
  findings, not needed by oracle 13 (the stock creations it covers are the two `oninit` classes).
