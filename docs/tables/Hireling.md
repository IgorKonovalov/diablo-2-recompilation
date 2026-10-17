# Hireling (`data/global/excel/hireling.txt` → `hireling.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 120 (no `Expansion` marker)   **Record:** 280 B (`0x118`)
> **sha256:** `.txt` `c743a6489456bd2c29143ae55312fda8fb6acb226d55a637c2c8f54a555afa78`, `.bin` `540ec2865297d57a4faa0793476858cb7226aa27a457b3ac2d9845151b9d95f7`
> **Doc status:** layout complete (plan 0033 Phase 0); semantics from [hirelings/0001](../findings/hirelings/0001-hirelings.md)
> (plan 0033 Phase 1); `Share` and the equipment columns have no reader in 1.14d (plan 0039 P1c); the combat-skill columns' meaning remains `[L]`

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
- `[C]` The rows interleave by act: rows 0–11 are `Version` 0 of Act I and rows 12–23 `Version` 100 of Act I, then
  18 + 18 rows for Act II (24–41, 42–59), 18 + 18 for Act III (60–77, 78–95) and 12 + 12 for Act V (96–107,
  108–119). Each version holds 60 rows and the same 30 Ids in the same order (`.txt` read by script). Between
  the two versions of an Id only the level-dependent columns differ: `Level` (the brackets), `HP`, `Defense`, `Str`,
  `Dex`, `AR`, `Dmg-Min`/`Dmg-Max`, `Resist`, the three `/Lvl` columns `HP/Lvl`, `Def/Lvl`, `AR/Lvl`, and some skill
  levels and chances.
- `[I]` The game reads only the rows of its own version: `Version` 100 in an expansion game, `Version` 0 otherwise.
  `HIRELING_GetRecord(version, Id, L)` returns the matching row with the greatest `Level` ≤ L (the first row of the
  Id when L is below every band), so a group's rows must stay in `Level` order; the loader indexes the first row of
  each (version, Id) in `g_HirelingFirstById[(Version > 99)·256 + Id]` ([hirelings/0001 § 1](../findings/hirelings/0001-hirelings.md#1-the-table-and-its-lookups),
  fn:HIRELING_GetRecord@0x006562F0, fn:HIRELING_LoadTable@0x00655720). The scan works with the interleaved order above.
- `[I]` The loader and `GetRecord` test `Version` differently: the loader indexes the first row by `Version > 99`
  (`cmp word [rec], 0x64; sbb …`, 0x0065623E), while `GetRecord` matches a row's `Version` against exactly 100
  (expansion) or 0. `[C]` by data, stock `Version` takes only 0 (60 rows) and 100 (60 rows), so the two agree on
  every stock row; a `Version` other than 0 or 100 would be indexed but never returned
  ([hirelings/0001 § S3b](../findings/hirelings/0001-hirelings.md#plan-0038-batch-s3b-2026-10-16),
  fn:HIRELING_LoadTable@0x00655720, fn:HIRELING_GetRecord@0x006562F0, tbl:Hireling.txt:Version).
- `[I]` The save stores the hireling `Id` (`merc_type`, header `0x0B9`); the reader takes `GetRecord(version, Id, 1)`
  for the class and name range, then the row of each level band as it walks the experience up
  ([save/0001](../findings/save/0001-d2s-io.md), [hirelings/0001 § 7](../findings/hirelings/0001-hirelings.md#7-the-mercenary-from-a-save),
  fn:D2S_ReadMercHeader@0x0056AA50).
- `[I]` In an expansion install the loader stops with a fatal error when a row's `NameFirst` string index is 0
  (`0x816`), when `NameLast` ≤ `NameFirst` (`0x817`) or when `Id` > 255 (`0x818`) ([hirelings/0001 § 1](../findings/hirelings/0001-hirelings.md#1-the-table-and-its-lookups),
  fn:HIRELING_LoadTable@0x00655720).

## Columns

`[C]` layout: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel hireling`: 120 records × 69 mapped
fields = 8 280 cells, **0 mismatches**; `excel_bin.py unknown … hireling` lists `+0x002`, `+0x113` (padding) and `+0x114`,
`+0x116` (no column), 0 in every record. The fields up to `+0x077` are s32 in `.txt` order except `Version` (u16)
and `Seller`/`Gold` before `Level`; then the six skill slots as six parallel arrays. `[C]` The column → offset map is
the loader's own field descriptor, which agrees with every offset below ([hirelings/0001 § 1](../findings/hirelings/0001-hirelings.md#1-the-table-and-its-lookups),
`struct:HirelingRec+0x000`, fn:HIRELING_LoadTable@0x00655720). Observed values are computed over the 120 `.txt`
rows. In the meanings, `d = L − Level` for a mercenary of level L and its band's row, `÷8` and `÷4` are signed
divisions truncating toward zero, and "`[C]` for `d ≥ 0`" means two code paths agree on that arithmetic for a
non-negative product, which every stock row gives (every per-level column is ≥ 0); the choice of the band row stays
`[I]` ([§ 6](../findings/hirelings/0001-hirelings.md#6-the-stats-per-level-merc_setlevel), fn:MERC_SetLevel@0x00572840, fn:HIRELING_RollEntry@0x006637F0).

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `Hireling` | str, 4 distinct: `Rogue Scout` 24, `Desert Mercenary` 36, `Eastern Sorceror` 36, `Barbarian` 24 | — (not loaded) | editor name of the kind; the descriptor has no field for it ([hirelings/0001 § 1](../findings/hirelings/0001-hirelings.md#1-the-table-and-its-lookups)) | — | [C] |
| `SubType` | str, 27 distinct (`Fire - Normal`, `Comb-Nightmare`, `1hs-Hell`, …) | — (not loaded) | editor label of the variant; not in the descriptor ([hirelings/0001 § 1](../findings/hirelings/0001-hirelings.md#1-the-table-and-its-lookups)) | — | [C] |
| `Version` | int {0: 60, 100: 60} | `+0x000` u16 (`+0x002` no field, 0) | 100 rows are used in an expansion game, 0 rows otherwise `[I]` ([hirelings/0001 § 1](../findings/hirelings/0001-hirelings.md#1-the-table-and-its-lookups)) | — | [C] |
| `Id` | int 0..29 | `+0x004` s32 | the hireling id: drawn by the hire (the type of the entry), stored in the save, looked up with the version and level `[I]` ([hirelings/0001 § 1](../findings/hirelings/0001-hirelings.md#1-the-table-and-its-lookups), [§ 4](../findings/hirelings/0001-hirelings.md#4-an-entry-type-level-price-and-the-displayed-stats)) | — | [C]; use `[I]` |
| `Class` | int {271, 338, 359, 561} | `+0x008` s32 | monster class: `roguehire`, `act2hire`, `act3hire`, `act5hire2` | [MonStats](MonStats.md) row index | [C] |
| `Act` | int {1, 2, 3, 5} (24/36/36/24 rows), 1-based | `+0x00C` s32 | the town act: an entry's type is drawn from the rows with `Act` = the act of the list's name range + 1 `[I]` ([hirelings/0001 § 1](../findings/hirelings/0001-hirelings.md#1-the-table-and-its-lookups), [§ 4](../findings/hirelings/0001-hirelings.md#4-an-entry-type-level-price-and-the-displayed-stats)) | — | [C] |
| `Difficulty` | int 1..3 (60/40/20 rows), 1-based | `+0x010` s32 | the type draw takes the rows with `Difficulty` = game difficulty + 1 `[I]` ([§ 4](../findings/hirelings/0001-hirelings.md#4-an-entry-type-level-price-and-the-displayed-stats)) | — | [C] |
| `Seller` | int {150, 198, 252, 515}, one per act | `+0x014` s32 | the NPC who hires out: monstats `kashya`, `greiz`, `asheara`, `qual-kehk`; its first `Difficulty` 1 row gives the name range and the spawned class in every difficulty `[I]` ([§ 3](../findings/hirelings/0001-hirelings.md#3-the-stock-build)) | [MonStats](MonStats.md) row index | [C] |
| `Gold` | int 100..32000 (19 distinct) | `+0x018` s32 | price base: `max(Gold, ((15·d + 100)·Gold) / 100)` with the first band's row, signed truncating `[I]` ([§ 4](../findings/hirelings/0001-hirelings.md#4-an-entry-type-level-price-and-the-displayed-stats)) | — | [C] |
| `Level` | int 3..80 (18 distinct) | `+0x01C` s32 | start of the row's level band: the world stats use the row with the greatest `Level` ≤ the mercenary's level; the hire list's type draw and displayed stats use the first band's row `[I]` ([hirelings/0001 § 1](../findings/hirelings/0001-hirelings.md#1-the-table-and-its-lookups), [§ 4](../findings/hirelings/0001-hirelings.md#4-an-entry-type-level-price-and-the-displayed-stats)) | — | [C] |
| `Exp/Lvl` | int 100..140 (8 distinct) | `+0x020` s32 | experience factor: `ExpForLevel(L) = (L+1)·L²·Exp/Lvl` (i32) `[C]` (two code paths and a save run, [§ 6](../findings/hirelings/0001-hirelings.md#6-the-stats-per-level-merc_setlevel), fn:HIRELING_ExpForLevel@0x00663790) | — | [C] |
| `HP`, `HP/Lvl` | int 45..1430; 8..45 | `+0x024`, `+0x028` s32 | life `max(40, HP + HP/Lvl·d)` (stored in 1/256) `[C]` for `d ≥ 0` ([§ 6](../findings/hirelings/0001-hirelings.md#6-the-stats-per-level-merc_setlevel)) | — | [C] |
| `Defense`, `Def/Lvl` | int 15..1250; 4..50 | `+0x02C`, `+0x030` s32 | defense `max(0, Defense + Def/Lvl·d)` `[C]` for `d ≥ 0` ([§ 6](../findings/hirelings/0001-hirelings.md#6-the-stats-per-level-merc_setlevel)) | — | [C] |
| `Str`, `Str/Lvl` | int 35..200; {10, 14, 15} | `+0x034`, `+0x038` s32 | strength `max(10, Str + Str/Lvl·d ÷8)`: the per-level column is in eighths `[C]` for `d ≥ 0` ([§ 6](../findings/hirelings/0001-hirelings.md#6-the-stats-per-level-merc_setlevel)) | — | [C] |
| `Dex`, `Dex/Lvl` | int 40..173; {8, 10, 12, 16} | `+0x03C`, `+0x040` s32 | dexterity `max(10, Dex + Dex/Lvl·d ÷8)`, eighths `[C]` for `d ≥ 0` ([§ 6](../findings/hirelings/0001-hirelings.md#6-the-stats-per-level-merc_setlevel)) | — | [C] |
| `AR`, `AR/Lvl` | int 10..1520; 10..45 | `+0x044`, `+0x048` s32 | attack rating `max(0, AR + AR/Lvl·d)` `[I]` (one code path, [§ 6](../findings/hirelings/0001-hirelings.md#6-the-stats-per-level-merc_setlevel)) | — | [C] |
| `Share` | int 1..6, 10 blank | `+0x04C` s32 | copied, clamped at 0, into the hire entry (`+0x28`) by `HIRELING_RollEntry` `[I]` ([§ 4](../findings/hirelings/0001-hirelings.md#4-an-entry-type-level-price-and-the-displayed-stats)); `[I]` none of the entry's four readers reads `+0x28`, so it has no effect in 1.14d ([hirelings/0001 § Plan 0039 batch P1c](../findings/hirelings/0001-hirelings.md#plan-0039-batch-p1c-2026-10-17)) | — | [C] |
| `Dmg-Min`, `Dmg-Max`, `Dmg/Lvl` | int 1..61; 3..65; {2, 4, 6, 8} | `+0x050`, `+0x054`, `+0x058` s32 | damage `max(0, Dmg-Min + Dmg/Lvl·d ÷8)` and `max(1, Dmg-Max + Dmg/Lvl·d ÷8)`, eighths `[C]` for `d ≥ 0` ([§ 6](../findings/hirelings/0001-hirelings.md#6-the-stats-per-level-merc_setlevel)) | — | [C] |
| `Resist`, `Resist/Lvl` | int 0..148; 4..8 | `+0x05C`, `+0x060` s32 | one pair for all four resistances (fire, lightning, cold, poison): `max(0, Resist + Resist/Lvl·d ÷4)`, quarters `[I]` (one code path, [§ 6](../findings/hirelings/0001-hirelings.md#6-the-stats-per-level-merc_setlevel)) | — | [C] |
| `DefaultChance` | int {10, 30, 50, 75}, one per kind | `+0x064` s32 | read by the combat skill choice `MERCAI_PickSkill` (named only, out of scope) `[I]` ([§ 10](../findings/hirelings/0001-hirelings.md#10-named-only)); its formula `[L]` | — | [C] |
| `Head`, `Weapon` | int {0, 2} (both: 0 on the 24 Barbarian rows, 2 elsewhere) | `+0x068` `Head`, `+0x070` `Weapon` s32 | `[I]` no reader in 1.14d ([hirelings/0001 § Plan 0039 batch P1c](../findings/hirelings/0001-hirelings.md#plan-0039-batch-p1c-2026-10-17)); equipment-related by name `[L]` | — | [C] (the descriptor names the offsets, [hirelings/0001 § 1](../findings/hirelings/0001-hirelings.md#1-the-table-and-its-lookups)) |
| `Torso` | int {0, 1, 2}: 1 on the Rogues, 2 on Acts II–III, 0 on Barbarians | `+0x06C` s32 | `[I]` no reader in 1.14d ([hirelings/0001 § Plan 0039 batch P1c](../findings/hirelings/0001-hirelings.md#plan-0039-batch-p1c-2026-10-17)) | — | [C] |
| `Shield` | int {0, 1}: 1 on the 36 Eastern Sorceror rows | `+0x074` s32 | `[I]` no reader in 1.14d ([hirelings/0001 § Plan 0039 batch P1c](../findings/hirelings/0001-hirelings.md#plan-0039-batch-p1c-2026-10-17)) | — | [C] |
| `Skill1` … `Skill3` | str: `Skill1` 6 distinct, `Skill2` 12, `Skill3` only `Ice Blast` (12 rows, 108 blank) | `+0x078 + 4(k−1)` s32 row index, blank −1 | the hireling's skills, added in slot order; the loop stops at the first `Skill_k` < 1 or ≥ the skill count; a skill is added only when its `reqlevel` ≤ the mercenary's level `[I]` ([§ 6](../findings/hirelings/0001-hirelings.md#6-the-stats-per-level-merc_setlevel)) | [Skills](Skills.md) `skill` | [C] |
| `Skill4` … `Skill6` | always blank | `+0x084`, `+0x088`, `+0x08C` | as `Skill1..3`; blank ends the loop | — | [C] value −1; slots in the descriptor ([hirelings/0001 § 1](../findings/hirelings/0001-hirelings.md#1-the-table-and-its-lookups)) [C] |
| `Chance1..6` | int 10..152; 10..1000; 240; slots 4–6 blank | `+0x090 + 4(k−1)` s32 | read by `MERCAI_PickSkill` (out of scope) `[I]` ([§ 10](../findings/hirelings/0001-hirelings.md#10-named-only)); its use `[L]` | — | [C] (6 × s32 in the descriptor) |
| `ChancePerLvl1..6` | int {0, 4}; {0, 2, 5, 8}; 0 | `+0x0A8 + 4(k−1)` s32 | read by `MERCAI_PickSkill` `[I]` ([§ 10](../findings/hirelings/0001-hirelings.md#10-named-only)); its use `[L]` | — | [C] (6 × s32 in the descriptor) |
| `Mode1..6` | int {4, 5, 7, 14}; {1, 4, 5, 7}; 7 | `+0x0C0 + (k−1)` s8 | read by `MERCAI_PickSkill` `[I]`; `MERC_SetLevel`'s skill loop also stops at `Mode_k` > 15 (signed) `[I]` ([§ 6](../findings/hirelings/0001-hirelings.md#6-the-stats-per-level-merc_setlevel), [§ 10](../findings/hirelings/0001-hirelings.md#10-named-only)) | — | [C] (6 × s8 in the descriptor) |
| `Level1..6` | int 1..27; 1..25; 6..27 | `+0x0C6 + (k−1)` s8 | skill level at the band start: `slvl = min(32, Level_k + (LvlPerLvl_k·d >> 5))`, added when ≥ 1 `[C]` for `d ≥ 0` ([§ 6](../findings/hirelings/0001-hirelings.md#6-the-stats-per-level-merc_setlevel)) | — | [C] (6 × s8 in the descriptor) |
| `LvlPerLvl1..6` | int {0, 5, 10}; {0, 7, 8, 10}; 10 | `+0x0CC + (k−1)` s8 | skill level growth in 1/32 per level (the `>> 5` above, a floor) `[C]` for `d ≥ 0` ([§ 6](../findings/hirelings/0001-hirelings.md#6-the-stats-per-level-merc_setlevel)) | — | [C] (6 × s8 in the descriptor) |
| `HireDesc` | str, 8 codes, 24 blank (the Barbarians) | `+0x0D2` u8 row index, blank → 0 | the description of the hire list entry; `HIRELING_RollEntry` copies the byte into the entry, the text is not read `[I]` ([§ 4](../findings/hirelings/0001-hirelings.md#4-an-entry-type-level-price-and-the-displayed-stats)) | [HireDesc](HireDesc.md) `Code` | [C] |
| `NameFirst`, `NameLast` | str, 4 pairs: `merc01`/`merc41`, `merca201`/`merca221`, `merca222`/`merca241`, `MercX101`/`MercX167` | `+0x0D3`, `+0x0F3` char[32] | first and last string-table key of the kind's names; the loader resolves them into `+0x114`/`+0x116` `[C]` ([hirelings/0001 § 1](../findings/hirelings/0001-hirelings.md#1-the-table-and-its-lookups)) | string tables ([tbl.md](../formats/tbl.md)) | [C] |
| `WType1`, `WType2` | str {`bow`, `pole`, `swor`}; {`spea`, `shie`}, 48 blank | — (not loaded: not in the descriptor, and every byte of the record is another field) | weapon item types by name `[L]`; the game does not read them from this table | [ItemTypes](ItemTypes.md) `Code` | [C] |
| — | — | `+0x113` u8 | padding, 0 | — | [C] value |
| — | — | `+0x114`, `+0x116` u16 | string indices of `NameFirst` and `NameLast`, 0 in the file and filled at load by `STRTABLE_GetByKey` `[C]` ([hirelings/0001 § 1](../findings/hirelings/0001-hirelings.md#1-the-table-and-its-lookups), fn:STRTABLE_GetByKey@0x00524D30) | — | [C] value 0 in the file |

## Interpretation notes

- **Who is offered where** (`python3 -I tools/hireling_survey.py summary …`, `[C]` for the counts): per version the
  same shape. Act I: Ids 0–1 in normal (3 rows each), 2–3 in nightmare (2 each), 4–5 in hell (1 each); Act II: 6–8,
  9–11, 12–14; Act III: 15–17, 18–20, 21–23; Act IV: none; Act V: 24–25, 26–27, 28–29. A group has one row per
  level band that its difficulty reaches: the `Version` 0 bands start at 3/25/49 (Act I), 9/31/55, 15/37/61, 28/42/75;
  the `Version` 100 bands at 3/36/67, 9/43/75, 15/49/79, 28/58/80. Nightmare groups start at the second band,
  hell groups at the third.
- **Bands are picked, not interpolated.** In the world every stat comes from the one row whose band holds the
  mercenary's level, extrapolated linearly by `d` `[I]`. The hire list instead rolls the type over the first band's
  rows of (version, act, difficulty), one row per type, and shows the price and stats extrapolated from that row with
  floor division, so the list and the world agree only inside the first band `[I]` ([§ 4](../findings/hirelings/0001-hirelings.md#4-an-entry-type-level-price-and-the-displayed-stats), [§ 6](../findings/hirelings/0001-hirelings.md#6-the-stats-per-level-merc_setlevel)).
- **The entry level** is `max(2, playerLevel − 5 + (low mod 5))` from the entry's seed and the player's current level
  `[I]` ([§ 4](../findings/hirelings/0001-hirelings.md#4-an-entry-type-level-price-and-the-displayed-stats)).
- **Two classes are absent.** Act V has only class 561 (`act5hire2`); class 560 (`act5hire1`), which
  `sub_0063EE90_HirelingType` also recognises ([monsters/pool](../specs/monsters/pool.md)), has no row, so no hire or
  save path creates it `[I]` ([§ 8](../findings/hirelings/0001-hirelings.md#8-monstats-class-and-the-e2-level-path)). Ids 24/25, 26/27 and 28/29 are identical except for `Id` (every other cell
  equal). `[C]`
- **`Version` 0 rows for Act V** exist (Ids 24–29) although a classic game has no Act V. `[C]` for the data; no
  classic act reaches them `[I]` ([§ 8](../findings/hirelings/0001-hirelings.md#8-monstats-class-and-the-e2-level-path)).
- **Name range.** `NameFirst` and `NameLast` are string keys; their string-table indices are 3411..3451 (41 names,
  Rogues), 1019..1039 (21, Act II), 1040..1059 (20, Act III), 10835..10901 (67, Barbarians) (`tools/tbl.py`; `[C]`
  that the keys resolve). The loader stores them at `+0x114`/`+0x116` `[C]` ([hirelings/0001 § 1](../findings/hirelings/0001-hirelings.md#1-the-table-and-its-lookups)). A seller's stock uses the
  range of its first `Difficulty` 1 row in every difficulty, one name per index, ten listed `[I]` ([§ 3](../findings/hirelings/0001-hirelings.md#3-the-stock-build)); the
  save stores the name as an offset from `+0x114` `[I]` ([save/0001](../findings/save/0001-d2s-io.md), [§ 7](../findings/hirelings/0001-hirelings.md#7-the-mercenary-from-a-save)).
- **`Exp/Lvl`.** `ExpForLevel(L) = (L+1)·L²·Exp/Lvl`; a loaded mercenary's level is the greatest L ≤ 99 with
  `ExpForLevel(L)` (using the row of band L − 1) ≤ its experience `[C]` (two code paths and run:2026-10-12-mon-pool-p2:
  Id 4, `Exp/Lvl` 120, experience 500 000 gives 15, [§ 6](../findings/hirelings/0001-hirelings.md#6-the-stats-per-level-merc_setlevel), [§ 7](../findings/hirelings/0001-hirelings.md#7-the-mercenary-from-a-save)).
- **`Head` against `Weapon`.** The two columns hold the same cells in every row; the loader's descriptor puts `Head`
  at `+0x068` and `Weapon` at `+0x070` `[C]` ([hirelings/0001 § 1](../findings/hirelings/0001-hirelings.md#1-the-table-and-its-lookups)). `[I]` None of the four equipment columns has a reader: the record array is read only by the loader, the free and the five getters, whose 19 callers never read `+0x068`…`+0x074` nor pass a record on ([hirelings/0001 § Plan 0039 batch P1c](../findings/hirelings/0001-hirelings.md#plan-0039-batch-p1c-2026-10-17), data:g_pHirelingTxt@0x0096BDD0).
- **Skill slots 4–6** are blank in every row, and slot 3 is used only by the Cold Eastern Sorcerors (`Ice Blast`).
  The descriptor declares six slots per array at the strides above `[C]`; their bytes are −1 (skill) and 0 `[C]`.
- **`WType1`/`WType2` are not loaded.** All 280 bytes are accounted for by other fields and the descriptor names
  neither column `[C]` ([hirelings/0001 § 1](../findings/hirelings/0001-hirelings.md#1-the-table-and-its-lookups)).

## Costs (plan 0043 Phase 0)

The gold columns of a hire. `Gold` (`+0x018` s32) is the only price column in the 1.14d header; there is no
resurrection column. Rows from `python3 -I tools/economy_survey.py hireling workspace/merged/data/global/excel` (gate
survey `economy`), `[C]` as data.

| Act | Normal (Ids: `Gold`) | Nightmare | Hell |
|---|---|---|---|
| I | 0: 100, 1: 150 | 2: 6000, 3: 7500 | 4: 12500, 5: 14000 |
| II | 6–8: 350 | 9–11: 7900 | 12–14: 15000 |
| III | 15, 17: 1000; 16: 1500 | 18: 9500, 19: 12000, 20: 10000 | 21, 23: 21000; 22: 27000 |
| V | 24–25: 9000 | 26–27: 18000 | 28–29: 32000 |

- `[C]` `Gold` is constant within each (`Version`, `Id`) group across its level bands (60 of 60 groups), and the
  `Version` 100 group of an Id has the classic group's `Gold` (30 of 30). Within each act and version, every
  Nightmare `Gold` is above every Normal one and every Hell `Gold` above every Nightmare one. 19 distinct values,
  100..32 000.
- `[C]` `Exp/Lvl` is constant within each group too (100..140); inside an act it never falls as `Gold` rises (Act III: 110 for
  1000, 120 for 1500 and 9500/10000, 130 for 12000/21000, 140 for 27000).
- `[C]` **The hire price** is `max(Gold, ((15·d + 100)·Gold) / 100)` with `d` = the entry level − the first band's
  `Level`, signed and truncating, computed when the entry is rolled ([hirelings/0001 § 4](../findings/hirelings/0001-hirelings.md#4-an-entry-type-level-price-and-the-displayed-stats),
  run:2026-10-16-hirelings, tbl:Hireling.txt:Gold). Whether the gold taken at the hire (`sub_00576D90_PayGold`) is this
  value or is scaled again is plan 0043 Phase 1 `[L]`.
- `[C]` **Resurrection** has no column: the 1.14d header lacks the later builds' `resurrectcost*` columns (the
  header and the 280-byte layout above). `[I]` The price is code: `MERC_ResurrectCost = min(50000, (L²/2)·15)`
  (unsigned compare), with the divisor, multiplier and cap as constants
  ([hirelings/0001 § 10](../findings/hirelings/0001-hirelings.md#10-named-only), fn:MERC_ResurrectCost@0x006637B0,
  fn:MERC_Resurrect@0x00579C00). Its widths, `L` (the mercenary's level) and the gold taken are plan 0043 Phase 1.

## Open questions

- ~~What `Share`, the equipment columns (`Head`, `Torso`, `Weapon`, `Shield`) do~~: no reader in 1.14d `[I]`
  ([hirelings/0001 § Plan 0039 batch P1c](../findings/hirelings/0001-hirelings.md#plan-0039-batch-p1c-2026-10-17)).
- `[L]` How `MERCAI_PickSkill` uses `DefaultChance`, `Chance_k`, `ChancePerLvl_k` and `Mode_k` (combat AI, out of
  scope under ADR-0002; [hirelings/0001 § 10](../findings/hirelings/0001-hirelings.md#10-named-only)).
