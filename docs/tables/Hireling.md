# Hireling (`data/global/excel/hireling.txt` → `hireling.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 120 (no `Expansion` marker)   **Record:** 280 B (`0x118`)
> **sha256:** `.txt` `c743a6489456bd2c29143ae55312fda8fb6acb226d55a637c2c8f54a555afa78`, `.bin` `540ec2865297d57a4faa0793476858cb7226aa27a457b3ac2d9845151b9d95f7`
> **Doc status:** layout complete (plan 0033 Phase 0); semantics `[L]` except the save fields save/0001 reads

## Purpose

One row per (hireling kind, game version, level bracket): the mercenaries a town offers, with their monster class,
act, difficulty, price, experience factor, base stats and per-level growth, skills, and name range. Readers:
`hirelings` (plan 0033: the hire list, the hire, the mercenary from a save) and `monsters/pool` (the hireling classes
`sub_0063EE90_HirelingType` recognises). Leads: none registered; nothing here comes from one.

## Row identity

- `[C]` The `.bin` is a u32 record count (120) and 120 records of 280 bytes, one per `.txt` row in order
  ([excel-bin.md](../formats/excel-bin.md)). The loader allocates 280-byte records
  ([data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables), `0x0065616B`).
- `[C]` `Id` (0..29) is **not unique**. Rows group by (`Version`, `Id`): 60 groups of 1 to 3 rows, each group in
  ascending `Level` order, and every one of `Class`, `Act`, `Difficulty`, `Seller`, `Gold`, `Exp/Lvl`, `HireDesc`,
  `NameFirst`, `NameLast`, `DefaultChance`, `Skill1..3` is constant within a group (`hireling_survey.py summary`:
  `group_field_varies=0`, `group_level_not_ascending=0`).
- `[C]` The rows 0–59 are `Version` 0 and the rows 60–119 `Version` 100, the same 30 Ids in the same order. Between
  the two versions of an Id only the level-dependent columns differ: `Level` (the brackets), `HP`, `Defense`, `Str`,
  `Dex`, `AR`, `Dmg-Min`/`Dmg-Max`, `Resist`, the three `/Lvl` columns `HP/Lvl`, `Def/Lvl`, `AR/Lvl`, and some skill
  levels and chances.
- `[I]` The save stores the hireling `Id` (`merc_type`, header `0x0B9`), and the reader finds the record by that id
  ([save/0001](../findings/save/0001-d2s-io.md), `0x006562F0`). Which of the group's rows (version, level bracket)
  it takes is for the reverser.

## Columns

`[C]` layout: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel hireling`: 120 records × 69 mapped
fields = 8 280 cells, **0 mismatches**; `excel_bin.py unknown … hireling` lists `+0x113` (padding) and `+0x114`,
`+0x116` (no column), 0 in every record. The fields up to `+0x077` are s32 in `.txt` order except `Seller`/`Gold`
before `Level`; then the six skill slots as six parallel arrays. Observed values are computed over the 120 `.txt`
rows.

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `Hireling` | str, 4 distinct: `Rogue Scout` 24, `Desert Mercenary` 36, `Eastern Sorceror` 36, `Barbarian` 24 | — (not compiled) | editor name of the kind | — | [C] |
| `SubType` | str, 27 distinct (`Fire - Normal`, `Comb-Nightmare`, `1hs-Hell`, …) | — (not compiled) | editor label of the variant | — | [C] |
| `Version` | int {0: 60, 100: 60} | `+0x000` s32 | classic (0) or expansion (100) row `[L]` | — | [C] |
| `Id` | int 0..29 | `+0x004` s32 | the hireling id a save stores | — | [C]; save use `[I]` |
| `Class` | int {271, 338, 359, 561} | `+0x008` s32 | monster class: `roguehire`, `act2hire`, `act3hire`, `act5hire2` | [MonStats](MonStats.md) row index | [C] |
| `Act` | int {1, 2, 3, 5} (24/36/36/24 rows), 1-based | `+0x00C` s32 | the town that offers it `[L]` | — | [C] |
| `Difficulty` | int 1..3 (60/40/20 rows), 1-based | `+0x010` s32 | the difficulty that offers it `[L]` | — | [C] |
| `Seller` | int {150, 198, 252, 515}, one per act | `+0x014` s32 | the NPC who hires out: monstats `kashya`, `greiz`, `asheara`, `qual-kehk` | [MonStats](MonStats.md) row index | [C] |
| `Gold` | int 100..32000 (19 distinct) | `+0x018` s32 | hiring price base `[L]` | — | [C] |
| `Level` | int 3..80 (18 distinct) | `+0x01C` s32 | the level bracket the row's stats are given for `[L]` | — | [C] |
| `Exp/Lvl` | int 100..140 (8 distinct) | `+0x020` s32 | experience factor (see notes) `[L]` | — | [C] |
| `HP`, `HP/Lvl` | int 45..1430; 8..45 | `+0x024`, `+0x028` s32 | life at `Level` and per level `[L]` | — | [C] |
| `Defense`, `Def/Lvl` | int 15..1250; 4..50 | `+0x02C`, `+0x030` s32 | defense and per level `[L]` | — | [C] |
| `Str`, `Str/Lvl` | int 35..200; {10, 14, 15} | `+0x034`, `+0x038` s32 | strength and per level `[L]` | — | [C] |
| `Dex`, `Dex/Lvl` | int 40..173; {8, 10, 12, 16} | `+0x03C`, `+0x040` s32 | dexterity and per level `[L]` | — | [C] |
| `AR`, `AR/Lvl` | int 10..1520; 10..45 | `+0x044`, `+0x048` s32 | attack rating and per level `[L]` | — | [C] |
| `Share` | int 1..6, 10 blank | `+0x04C` s32 | `[L]` | — | [C] |
| `Dmg-Min`, `Dmg-Max`, `Dmg/Lvl` | int 1..61; 3..65; {2, 4, 6, 8} | `+0x050`, `+0x054`, `+0x058` s32 | damage at `Level` and per level `[L]` | — | [C] |
| `Resist`, `Resist/Lvl` | int 0..148; 4..8 | `+0x05C`, `+0x060` s32 | resistances and per level `[L]` | — | [C] |
| `DefaultChance` | int {10, 30, 50, 75}, one per kind | `+0x064` s32 | chance of the default (no-skill) attack `[L]` | — | [C] |
| `Head`, `Weapon` | int {0, 2} (both: 0 on the 24 Barbarian rows, 2 elsewhere) | `+0x068`, `+0x070` s32 | `[L]` (equipment-related by name) | — | [C] bytes; which column is which `[L]` (notes) |
| `Torso` | int {0, 1, 2}: 1 on the Rogues, 2 on Acts II–III, 0 on Barbarians | `+0x06C` s32 | `[L]` | — | [C] |
| `Shield` | int {0, 1}: 1 on the 36 Eastern Sorceror rows | `+0x074` s32 | `[L]` | — | [C] |
| `Skill1` … `Skill3` | str: `Skill1` 6 distinct, `Skill2` 12, `Skill3` only `Ice Blast` (12 rows, 108 blank) | `+0x078 + 4(k−1)` s32 row index, blank −1 | the hireling's skills | [Skills](Skills.md) `skill` | [C] |
| `Skill4` … `Skill6` | always blank | `+0x084`, `+0x088`, `+0x08C` | — | — | [C] value −1; slots by the stride `[L]` |
| `Chance1..6` | int 10..152; 10..1000; 240; slots 4–6 blank | `+0x090 + 4(k−1)` s32 | use chance of skill k `[L]` | — | [C] for 1–3; 4–6 by the stride `[L]` |
| `ChancePerLvl1..6` | int {0, 4}; {0, 2, 5, 8}; 0 | `+0x0A8 + 4(k−1)` s32 | per level `[L]` | — | [C] for 1–2; 3–6 by the stride `[L]` (column 3 is 0 or blank) |
| `Mode1..6` | int {4, 5, 7, 14}; {1, 4, 5, 7}; 7 | `+0x0C0 + (k−1)` u8 | a monster mode for the skill `[L]` | — | [C] for 1–3; 4–6 by the stride `[L]` |
| `Level1..6` | int 1..27; 1..25; 6..27 | `+0x0C6 + (k−1)` u8 | skill level at `Level` `[L]` | — | [C] for 1–3; 4–6 by the stride `[L]` |
| `LvlPerLvl1..6` | int {0, 5, 10}; {0, 7, 8, 10}; 10 | `+0x0CC + (k−1)` u8 | skill level growth `[L]` | — | [C] for 1–3; 4–6 by the stride `[L]` |
| `HireDesc` | str, 8 codes, 24 blank (the Barbarians) | `+0x0D2` u8 row index, blank → 0 | the description line of the hire list | [HireDesc](HireDesc.md) `Code` | [C] |
| `NameFirst`, `NameLast` | str, 4 pairs: `merc01`/`merc41`, `merca201`/`merca221`, `merca222`/`merca241`, `MercX101`/`MercX167` | `+0x0D3`, `+0x0F3` char[32] | first and last string-table key of the kind's names | string tables ([tbl.md](../formats/tbl.md)) | [C] |
| `WType1`, `WType2` | str {`bow`, `pole`, `swor`}; {`spea`, `shie`}, 48 blank | — (not compiled: every byte of the record is another field) | weapon item types the kind may use `[L]` | [ItemTypes](ItemTypes.md) `Code` | [C] |
| — | — | `+0x113` u8 | padding, 0 | — | [C] value |
| — | — | `+0x114`, `+0x116` u16 | no column, 0 in the file; see notes | — | [C] value 0 |

## Interpretation notes

- **Who is offered where** (`python3 -I tools/hireling_survey.py summary …`, `[C]` for the counts): per version the
  same shape. Act I: Ids 0–1 in normal (3 rows each), 2–3 in nightmare (2 each), 4–5 in hell (1 each); Act II: 6–8,
  9–11, 12–14; Act III: 15–17, 18–20, 21–23; Act IV: none; Act V: 24–25, 26–27, 28–29. A group has one row per
  level bracket that its difficulty reaches: the `Version` 0 brackets are 3/25/49 (Act I), 9/31/55, 15/37/61, 28/42/75;
  the `Version` 100 brackets are 3/36/67, 9/43/75, 15/49/79, 28/58/80. Nightmare groups start at the second bracket,
  hell groups at the third. Whether the game interpolates between the rows or picks one is `[L]` (plan 0033 Phase 1).
- **Two classes are absent.** Act V has only class 561 (`act5hire2`); class 560 (`act5hire1`), which
  `sub_0063EE90_HirelingType` also recognises ([monsters/pool](../specs/monsters/pool.md)), has no row. Ids 24/25,
  26/27 and 28/29 are identical except for `Id` (every other cell equal). `[C]`
- **`Version` 0 rows for Act V** exist (Ids 24–29) although a classic game has no Act V. `[C]` for the data; whether
  a classic game reads them is `[L]`.
- **Name range.** `NameFirst` and `NameLast` are string keys; their string-table indices are 3411..3451 (41 names,
  Rogues), 1019..1039 (21, Act II), 1040..1059 (20, Act III), 10835..10901 (67, Barbarians) (`tools/tbl.py`; `[C]`
  that the keys resolve). save/0001 reads the record's `+0x114` and `+0x116` as the first and last name id and stores
  the name as an offset from `+0x114` (`[I]`, [save/0001](../findings/save/0001-d2s-io.md)); in the file both are 0,
  so they are filled at load, presumably with these two indices `[L]`.
- **`Exp/Lvl`.** One run fits *experience threshold of level L = `Exp/Lvl` × L² × (L + 1)*: the `exphellmerc` mercenary
  (Id 4, `Exp/Lvl` 120, experience 500 000) showed level 15 (432 000 ≤ 500 000 < 522 240), [monsters/experiments](../findings/monsters/experiments.md).
  One point is not a rule: `[L]`.
- **`Head` against `Weapon`.** The two columns hold the same cells in every row, so the data cannot say which of
  `+0x068`/`+0x070` is which; the layout follows the `.txt` order (`Head`, `Torso`, `Weapon`, `Shield`). `[L]`
- **Skill slots 4–6** are blank in every row, and slot 3 is used only by the Cold Eastern Sorcerors (`Ice Blast`).
  The slots follow the stride of slots 1–3 `[L]`; their bytes are −1 (skill) and 0 `[C]`.
- **`WType1`/`WType2` are not compiled.** All 280 bytes are accounted for by other fields, so the game cannot read
  these columns from the `.bin`. `[C]`

## Open questions

- `[L]` How the hire list is built (count, row pick by level, name roll), what `Level`, the stat columns, `Share`,
  `DefaultChance`, `Head`/`Torso`/`Weapon`/`Shield` and the skill `Mode`/`Chance`/`Level` columns do, and how the
  game fills `+0x114`/`+0x116`. Reverser, plan 0033 Phase 1 ([backlog](../backlog.md)).
- `[L]` Which of `+0x068`/`+0x070` is `Head` and which `Weapon`; the skill slots 4–6 (a `-txt` compile probe would
  settle both).
