# Sets (`data/global/excel/sets.txt` → `sets.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 32 (33 data rows − 1 `Expansion` marker)   **Record:** 296 B (`0x128`)
> **sha256:** `.txt` `e6694bc603f1f29efdfa981c3f747708e11bb0410786fa8bf5ab634f60f6b822`, `.bin` `abec75e33edd8ffaf1e28c04a4e79adc8e47198f5bf9a552fa057ba4cb220aa4`
> **Doc status:** identity and generation columns; `.bin` layout complete (the bonus blocks `+0x010..+0x10F` mapped by plan 0041 Phase 0, § Bonus blocks); semantics of `version` and the load-time slots from [items/0004](../findings/items/0004-uniques-sets.md) (plan 0019 Phase 1), `[L]` elsewhere

## Purpose

One row per item set: its name, its game version, its level, and the partial and full set bonuses.
The set items themselves are rows of [SetItems](SetItems.md), which name their set through `set`.
This doc covers the identity and generation columns (plan 0019 Phase 0, research-map row
`items/uniques-sets`) and the bonus columns (`PCode2a..PMax5b`, `FCode1..FMax8`), mapped for the set-bonus
code of plan 0041 (§ Bonus blocks). Leads: no lead; derived from data.

## Row identity

- `[C]` The record index is the data row index once the `Expansion` marker is dropped (0..31): rows
  0..15 come before the marker, rows 16..31 after it. `python3 -I tools/excel_bin.py diff … sets`
  matches record *i* to data row *i* in every mapped column.
- `[C]` `index` is the row's key, unique in all 32 rows, and is stored as the row's own index (u16 at
  `+0x000`, 0..31). `name` equals `index` as text in all 32 rows and is stored as a string-table key.
- `[C]` `SetItems.set` names a row here by `index`: all 127 resolve, every one of the 32 sets is named,
  and `setitems.bin` stores the row index of this table ([SetItems](SetItems.md) layout, `+0x02C`).
  Members per set: 1 set with 2 items, 9 with 3, 14 with 4, 6 with 5, 2 with 6 (`127` in all).
- `[I]` The game loads `sets.bin` with a 296-byte record ([data/0001 §4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables)).

## Columns

`[C]` layout tags are by data behaviour: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel sets`
decodes all 32 records and matches every mapped cell (32 × 67 = 2 144 cells, 0 mismatches; gate survey
`excel_layout`, `sets_cells`), and `excel_bin.py probe` finds `version` at `+0x004` only. Until plan 0041 Phase 0
the layout was partial (3 columns, 96 cells); it now maps the 64 bonus columns too.
`[L]` The integer type the game reads inside a slot is not pinned (no code anchor).
**Meaning:** `[L]` unless tagged in the cell; `version` and `level` are `[I]` from
[items/0004 § 7](../findings/items/0004-uniques-sets.md#7-load-time-slots-in-uniqueitems-setitems-and-sets-the-backlog-questions).

| Column | Observed type / range | `.bin` field | Meaning (`[L]`) | References | Layout tag |
|---|---|---|---|---|---|
| `index` | str, 32 distinct, len ≤ 22 | `+0x000` u16, the row's own index | set key | `setitems` `set` (all 127 resolve) | [C] |
| `name` | str, equal to `index` in all 32 rows | `+0x002` u16 string-table key | display name | `.tbl` key ([tbl.md](../formats/tbl.md)) | [C] |
| `version` | int {0: 16, 100: 16}, 0 blank | `+0x004` 4-byte slot (u32 decode) | 0 classic, 100 expansion; `[I]` copied at load into each member's `setitems` `+0x022`, where the set builder tests it (≥ 100 only in an expansion game) | `setitems` `+0x022` | [C] |
| `level` | int 3..55 (29 distinct), 0 blank | — **no field**: `probe` finds it at no offset under any encoding | `[I]` not compiled and not read: the loader has no `level` descriptor, and the only set level test reads `SetItems.lvl` | equals the `lvl` of every member in `setitems` (127 of 127) | [C] (absence) |
| `PCode2a..PMax5b` | 8 quads (code, param, min, max); 67 codes set | `+0x010 + 16j`, *j* = 0..7: code s32 (blank −1), param, min, max s32 | partial-set bonuses (§ Bonus blocks) | `properties` `code`; a param names a `skills` or `states` row | [C] |
| `FCode1..FMax8` | 8 quads; 153 codes set | `+0x090 + 16(k−1)`, *k* = 1..8: as above | full-set bonuses (§ Bonus blocks) | as above | [C] |
| `*eol` | end-of-line marker column | — (not compiled) | — | — | — |

`[C]` `version` follows the marker: 0 in rows 0..15 and 100 in rows 16..31.

## Record layout

`+0x000` `index` (u16 row index) · `+0x002` `name` (u16 string key) · `+0x004` `version` (u32) ·
`+0x008` u32, 0 in every record (`unk_008`; no `.txt` column) · `+0x00C` u32, 0 in every record
(`nMembers`, filled at load) · `+0x010..+0x10F` sixteen 16-byte bonus quads in `.txt` order (`PCode2a`
at `+0x010`, `FCode1` at `+0x090`; § Bonus blocks) · `+0x110..+0x127` six u32, 0 in
every record (`member0..member5`, filled at load). `python3 -I tools/excel_bin.py unknown … sets` lists
only these load-time slots, each 0 in all 32 records. `[C]` for the offsets of the mapped fields and for the zero ranges.

- `[C]` `+0x00C` is the member count and `+0x110..+0x127` six pointers to the member `setitems` records,
  both filled by the loader once `setitems` is loaded: for each `setitems` row in order whose `set` is
  valid and whose set has fewer than 6 members, the row's pointer goes to `members[nMembers]` and the
  count goes up by one. Corroborated by a second code path: the writer agrees with two readers,
  `sub_005C2740_ItemBuildSetV0` (walks `members[0 .. nMembers−1]`) and `sub_00660120_SetBonusApply`
  (reads `+0x0C` to choose partial or full bonuses). ([items/0004 § 7](../findings/items/0004-uniques-sets.md#7-load-time-slots-in-uniqueitems-setitems-and-sets-the-backlog-questions),
  fn:sub_00634DC0_LoadSetTables@0x00634DC0, fn:sub_005C2740_ItemBuildSetV0@0x005C2740,
  fn:sub_00660120_SetBonusApply@0x00660120, struct:SetsRec+0x0C)
- `[I]` `+0x008` is written neither by the column descriptors nor by the post-load loop, and no reader
  was found in the code read for items/0004 (not a full search). ([items/0004 § 7](../findings/items/0004-uniques-sets.md#7-load-time-slots-in-uniqueitems-setitems-and-sets-the-backlog-questions), 0x00634DC0)

## Bonus blocks (plan 0041 Phase 0)

The set bonuses a worn set adds, for the set-bonus code plan 0041 Phase 1 reads
(`sub_00660120_SetBonusApply`). Layout `[C]` by `excel_bin.py diff` (§ Columns, 2 144 cells, 0 mismatches); the
counts are `python3 -I tools/stats_survey.py sets workspace/merged/data/global/excel` (gate survey `stats`), `[C]` as
data. **Meanings `[L]`** (the column names), except the member count of § Record layout.
(fn:sub_00660120_SetBonusApply@0x00660120, tbl:Sets.txt:PCode2a)

**Layout.** Sixteen 16-byte blocks `(code s32, param s32, min s32, max s32)`, the [SetItems](SetItems.md#property-block-plan-0024-phase-1)
property-block shape: block *j* at `+0x010 + 16j`, the eight partial blocks first in `.txt` order (`PCode2a`, `PCode2b`,
`PCode3a`, …, `PCode5b`, *j* = 0..7, `+0x010..+0x08F`), then `FCode1..8` (*j* = 8..15, `+0x090..+0x10F`). A blank
code stores −1; a code is the [Properties](Properties.md) row index, matched case-insensitively.

| Columns | Cells set (of 256) | Values | Survey key |
|---|---:|---|---|
| `PCode2a..5b` | 67 | 24 distinct property rows | `sets_partial_blocks` |
| `PParam2a..5b` | 5 | the 3 `oskill` skill names below, and 2 numbers | — |
| `PMin2a..5b`, `PMax2a..5b` | 67, 67 | 5..200 (19 distinct) | — |
| `FCode1..8` | 153 | 71 distinct property rows | `sets_full_blocks` |
| `FParam1..8` | 67 | 0..176 (6 distinct), names included | — |
| `FMin1..8`, `FMax1..8` | 153, 153 | 1..350 (29 distinct) | — |

- `[C]` **A param cell may hold a name.** Ten of them: the `oskill` blocks of Trang-Oul's Avatar (`PParam2b` `Fire
  Ball` → 47, `PParam3b` `Fire Wall` → 51, `PParam4b` `Meteor` → 56, `FParam7` `Fire Mastery` → 61) store the
  [Skills](Skills.md) row, and the six `state` blocks (`FParam5` of Immortal King, Griswold's Legacy and Trang-Oul's
  Avatar, `FParam6` of Tal Rasha's Wrappings and M'avina's Battle Hymn, `FParam7` of Aldur's Watchtower) store the
  [States](States.md) row: 175 `fullsetgeneric`, 176 `monsterset` (Trang-Oul's). `excel_bin.py` resolves such a cell in
  Skills, then in States (field option `names="skills:skill|states:state"`). None of the ten names stored here is
  both a skill and a state, so the data does not show how the compiler picks the table. The two name spaces do
  overlap elsewhere: 44 names are both a Skills `skill` and a States `state`, case-insensitively (`might`,
  `fanaticism`, `thorns`, `fade`…), so a `state` block naming one of them would decode as the skill row under
  this tool order. (`sets_params_named` = 10, tbl:Sets.txt:FParam5)
- **Known limit of `excel_bin.py`** (not a claim about the game): the skills-then-states order is a tool
  convention that is right for stock data only. The tool does not look at the block's property, so on edited data
  a `state` block naming one of the 44 shared names would be compared against the Skills row, and an `oskill` block
  naming a name that is only a state against the States row. The tool keeps the order until plan 0041 Phase 1
  item (e) reads how the compiler resolves a param name; it then follows that rule rather than a guessed one.
- `[C]` No block has a param, min or max without its code. Within each run (the `a` blocks, the `b` blocks, the full
  blocks) no used block follows a blank one (`sets_block_gaps` = 0).
- `[C]` No set has a partial block `k` (`PCode<k>a/b`) above its member count (`sets_partial_beyond_members` = 0);
  `[L]` by the name, block `k` belongs to *k* worn members. Used: `2a` 31, `3a` 23, `4a` 8, `5a` 2, and only
  Trang-Oul's Avatar uses `b` blocks (`2b`, `3b`, `4b`). Bul-Kathos' Children (2 members) has no partial block.
- `[C]` 74 distinct property codes over the 220 blocks (`sets_codes_distinct`); the most used are `ac` and
  `res-all` (19 each), `att` 12, `lifesteal` and `mana` 11, `str` 10, `dex` 9, `hp` 8.

| Set | `index` | Members | Partial blocks used | Full blocks used |
|---:|---|---:|---|---|
| 0 | Civerb's Vestments | 3 | 2a | 1, 2, 3 |
| 1 | Hsarus' Defense | 3 | 2a | 1, 2, 3 |
| 2 | Cleglaw's Brace | 3 | 2a | 1, 2, 3, 4 |
| 3 | Iratha's Finery | 4 | 2a, 3a | 1, 2, 3, 4, 5, 6 |
| 4 | Isenhart's Armory | 4 | 2a, 3a | 1, 2, 3, 4, 5 |
| 5 | Vidala's Rig | 4 | 2a, 3a | 1, 2, 3, 4 |
| 6 | Milabrega's Regalia | 4 | 2a, 3a | 1, 2, 3, 4 |
| 7 | Cathan's Traps | 5 | 2a, 3a | 1, 2, 3, 4, 5 |
| 8 | Tancred's Battlegear | 5 | 2a, 3a | 1, 2, 3, 4 |
| 9 | Sigon's Complete Steel | 6 | 2a, 3a | 1, 2, 3, 4, 5 |
| 10 | Infernal Tools | 3 | 2a, 3a | 1, 2, 3, 4 |
| 11 | Berserker's Garb | 3 | 2a | 1, 2, 3, 4, 5 |
| 12 | Death's Disguise | 3 | 2a | 1, 2, 3 |
| 13 | Angelical Raiment | 4 | 2a, 3a | 1, 2, 3, 4 |
| 14 | Arctic Gear | 4 | 2a, 3a | 1, 2, 3, 4 |
| 15 | Arcanna's Tricks | 4 | 2a, 3a | 1, 2, 3 |
| 16 | Natalya's Odium | 4 | 2a, 3a, 4a | 1, 2, 3, 4, 5, 6, 7 |
| 17 | Aldur's Watchtower | 4 | 2a, 3a, 4a | 1, 2, 3, 4, 5, 6, 7 |
| 18 | Immortal King | 6 | 2a, 3a, 4a, 5a | 1, 2, 3, 4, 5 |
| 19 | Tal Rasha's Wrappings | 5 | 2a, 3a, 4a | 1, 2, 3, 4, 5, 6 |
| 20 | Griswold's Legacy | 4 | 2a, 3a | 1, 2, 3, 4, 5, 6 |
| 21 | Trang-Oul's Avatar | 5 | 2a, 2b, 3a, 3b, 4a, 4b | 1, 2, 3, 4, 5, 6, 7, 8 |
| 22 | M'avina's Battle Hymn | 5 | 2a, 3a | 1, 2, 3, 4, 5, 6 |
| 23 | The Disciple | 5 | 2a, 3a, 4a, 5a | 1, 2, 3 |
| 24 | Heaven's Brethren | 4 | 2a, 3a, 4a | 1, 2, 3, 4 |
| 25 | Orphan's Call | 4 | 2a, 3a, 4a | 1, 2, 3, 4, 5, 6 |
| 26 | Hwanin's Majesty | 4 | 2a, 3a | 1, 2, 3, 4 |
| 27 | Sazabi's Grand Tribute | 3 | 2a | 1, 2, 3 |
| 28 | Bul-Kathos' Children | 2 | - | 1, 2, 3, 4, 5, 6 |
| 29 | Cow King's Leathers | 3 | 2a | 1, 2, 3, 4, 5, 6 |
| 30 | Naj's Ancient Set | 3 | 2a | 1, 2, 3, 4, 5, 6 |
| 31 | McAuley's Folly | 4 | 2a, 3a | 1, 2, 3, 4 |

- `[I]` Which block is active is the equip-time code's: `sub_00660120_SetBonusApply` reads the set's member count
  (`+0x00C`) to choose between partial and full bonuses (§ Record layout, items/0004 § 7). How it counts worn members
  and applies the blocks is plan 0041 Phase 1. (fn:sub_00660120_SetBonusApply@0x00660120, struct:SetsRec+0x0C)
- The set items' own partial bonuses are the `aprop` pairs and `add func` of [SetItems § Bonus blocks](SetItems.md#bonus-blocks-plan-0041-phase-0).

## Interpretation notes

- `[C]` `level` is not compiled, but every set item carries the same value in its own `lvl`
  (`python3 -I tools/unique_survey.py … ` prints `SetItems lvl against its Sets level: 0 below, 127
  equal, 0 above`). A reader of the `.bin` that needs a set's level gets it from a member row.
- `[C]` The set items of the 16 classic sets are `setitems` rows 0..61 and those of the 16 expansion
  sets rows 62..126; the version changes once along `setitems` record order. `setitems.txt` has no
  `version` column, so the set's `version` is the only version a set item has in the data. `[I]` The
  loader copies it into each member row (`setitems` `+0x022`) and the set builder tests that copy: a
  member of a set with `version` ≥ 100 is a candidate only in an expansion game.
  ([items/0004 § 4](../findings/items/0004-uniques-sets.md#4-the-set-builder-items_buildsetitem-rec-0x005c2940), 0x005C2630, tbl:Sets.txt:version)
- `[I]` Set 29 (`Cow King's Leathers` in stock data) is the one set the builder treats apart: its members
  are candidates only when the drop's source is a `hellbovine`. ([items/0004 § 4](../findings/items/0004-uniques-sets.md#4-the-set-builder-items_buildsetitem-rec-0x005c2940), 0x005C264E–0x005C265F)
- The bonus columns are § Bonus blocks. Plan 0019 left them unmapped because several param cells hold names; the
  names resolve to a Skills or a States row (§ Bonus blocks), which the layout now follows.

## Open questions

- Answered by [items/0004 § 7](../findings/items/0004-uniques-sets.md#7-load-time-slots-in-uniqueitems-setitems-and-sets-the-backlog-questions): `+0x00C` and `+0x110..+0x127` (`[C]`, § Record
  layout); whether `version` and `SetItems.lvl` gate the set builder (both do, `[I]`, Interpretation notes
  and [SetItems](SetItems.md)).
- `[L]` What `+0x008` is: no writer and no reader found; a full search of the `sets` readers would settle it.
