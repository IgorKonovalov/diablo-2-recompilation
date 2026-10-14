# MonUMod (`data/global/excel/monumod.txt` → `monumod.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 43 (no `Expansion` marker)   **Record:** 32 B (`0x20`)
> **sha256:** `.txt` `d515513e953c4db98b39f1af9cb6d58c972630a0f9a765d1381411128b9cdf0c`, `.bin` `b1d612b7b568ca818a794f988601664a6ae5d853e82686fb1c8b001b2f48cc8c`
> **Doc status:** complete for layout; semantics `[I]` for every column the special-monster code reads
> ([monsters/0003](../findings/monsters/0003-special-monsters.md)), row 0 `constants` `[C]` (monsters/0002 § 5); the other `constants` rows `[L]`

## Purpose

One row per special-monster modifier ("unique mod"): `strong`, `fast`, `curse`, `fire`, `champion`, `ghostly`, … and a
few internal ones (`rndname`, `hpmultiply`, `bloodraven`, `questcomplete`, `worms_on_death`, …). Each row carries the
weights with which a champion (`cpick`) or a unique (`upick`) draws the mod in each difficulty, whether minions inherit
it (`xfer`), and a monster type it may not go on (`exclude1`/`exclude2`). The `constants` column is a separate list of
numbers, one per row, that the code reads by row index (row 0 is the champion chance). Readers: the special branch of
the population pass ([monsters/0002 § 5](../findings/monsters/0002-room-population.md#5-the-two-group-branches)) and
the mod roll, mod handlers and minion transfer of [monsters/0003](../findings/monsters/0003-special-monsters.md) (plan 0018 Phase 1). [SuperUniques](SuperUniques.md) `Mod1`–`Mod3` hold row indices of this
table. Leads: no lead; derived from data.

## Row identity

- `[C]` The `.bin` is a u32 record count (43) and 43 records of 32 bytes, one per `.txt` row in order
  ([excel-bin.md](../formats/excel-bin.md)). The table is at `DataTables+0xC50`, record size 32 confirmed by the loader
  ([data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables), `0x00655279`).
- `[C]` `id` equals the row index in all 43 rows; the key `uniquemod` is not compiled (no bytes in the record).
- `[C]` SuperUniques `Mod1`–`Mod3` are plain integers in their `.txt` and match this table's `id` (= row index) by name
  where the survey prints them (e.g. Bishibosh `resist(8)/fire(9)`). `[I]` They are row indices of this table:
  `SuperUniqueSpawn` writes them into the mod list unchanged and dispatches them through the handler table
  (fn:sub_005A49B0_SuperUniqueSpawn@0x005A49B0, [monsters/0003 § 6](../findings/monsters/0003-special-monsters.md#6-superuniques-superuniquespawn)).
- `[I]` The row index is also the handler index: `g_UModHandlers` (`0x0073C008`) holds one code pointer per row, and the
  mod list stores row indices (data:g_UModHandlers@0x0073C008, [monsters/0003 § 4](../findings/monsters/0003-special-monsters.md#4-specialmodsapply-and-the-per-handler-draw-table)).

## Columns

`[C]` layout: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel monumod`: 43 records × 16 mapped
fields = 688 cells, **0 mismatches**; `excel_bin.py unknown … monumod` lists no uncovered byte. Value columns below are
from `python3 -I tools/mon_survey.py umod workspace/merged/data/global/excel` (decoded from the `.bin`).

| Column | Observed type / range | `.bin` field | Meaning (`[L]` unless stated) | References | Layout tag |
|---|---|---|---|---|---|
| `uniquemod` | str, 43 distinct, 0 blank | — (not compiled) | the mod's name | — | [C] |
| `id` | int 0..42 = row index | `+0x000` u32 | the mod's number; `[I]` = row = handler index in `g_UModHandlers` (`0x0073C008`), [§ 4](../findings/monsters/0003-special-monsters.md#4-specialmodsapply-and-the-per-handler-draw-table) | — | [C] value; [L] whether `+0x002` u16 (always 0) is part of it |
| `version` | int {0: 32 rows, 100: 11 rows (32–42)} | `+0x004` u16 | `[I]` ≥ 100 = refused in a classic game (`game+0x70` = 0) by `ModEligible`, [§ 3](../findings/monsters/0003-special-monsters.md#3-the-two-picks-and-modeligible) | — | [C] |
| `enabled` | int {1: 41, 0: 2 (`none` 0, `thief` 24)} | `+0x006` u8 | `[I]` 0 = never a pick candidate (`ModEligible`), [§ 3](../findings/monsters/0003-special-monsters.md#3-the-two-picks-and-modeligible) | — | [C] |
| `xfer` | int {1: 19, 0: 24} | `+0x007` u8 | `[I]` 1 = copied from the boss into each unique minion's mod list when the minion is created (`ModsXferCopy`), [§ 5](../findings/monsters/0003-special-monsters.md#5-minions-and-xfer) | — | [C] |
| `champion` | int {1: 5 (16, 36–39), 0: 38} | `+0x008` u8 | `[I]` 1 = candidate of the champion pick only, 0 = of the unique pick only, [§ 3](../findings/monsters/0003-special-monsters.md#3-the-two-picks-and-modeligible) | — | [C] (see *cpick* note) |
| `fPick` | int {0: 40, 3: `fast`, 1: `teleport`, 2: `multishot`} | `+0x009` u8 | `[I]` extra pick test: 1 = the class needs MonStats2 mode `A1`, 2 = refused to `isMelee` and `nomultishot` classes, 3 = the class needs mode `WL`; 0 = none, [§ 3](../findings/monsters/0003-special-monsters.md#3-the-two-picks-and-modeligible) | — | [C] |
| `exclude1` | str, 1 set (`lightning` → `sandleaper`), 42 blank | `+0x00A` u16 MonType row index, blank 0 | `[I]` refused when the monster's MonType is-a this type (MonType bit matrix); 0 ends the list, [§ 3](../findings/monsters/0003-special-monsters.md#3-the-two-picks-and-modeligible) | `montype:type` | [C] |
| `exclude2` | blank in all rows | `+0x00C` u16 (0 everywhere) | `[I]` second excluded type, tested like `exclude1` (read at `+0x0C`), [§ 3](../findings/monsters/0003-special-monsters.md#3-the-two-picks-and-modeligible) | `montype:type` | [C] value; slot by stride `[L]` |
| `cpick`, `cpick (N)`, `cpick (H)` | int {1: 5 rows (16, 36–39), 0: 38}, equal in all three | `+0x00E`, `+0x010`, `+0x012` u16 | `[I]` champion pick weight for Normal, Nightmare, Hell (s16 at `+0x0E + 2·d`; candidate when > 0), [§ 3](../findings/monsters/0003-special-monsters.md#3-the-two-picks-and-modeligible) | — | [C] bytes; order `[I]` by the reader (below) |
| `upick`, `upick (N)`, `upick (H)` | int {6, 0}; 12 / 13 / 13 rows non-zero | `+0x014`, `+0x016`, `+0x018` u16 | `[I]` unique pick weight for Normal, Nightmare, Hell (s16 at `+0x14 + 2·d`; candidate when > 0), [§ 3](../findings/monsters/0003-special-monsters.md#3-the-two-picks-and-modeligible) | — | [C] (`upick` placed by probe; `(N)`/`(H)` equal in every row, order by stride `[L]`) |
| `fInit` | blank in all rows | `+0x01A` u16 (0 everywhere) | `[I]` no reader: the eight functions that address the table read every other field, [Data touched](../findings/monsters/0003-special-monsters.md#data-touched) | — | [C] value; slot by stride `[L]` |
| `constants` | int, 10 distinct values (0..300) on rows 0–33, blank 34–42 | `+0x01C` u32 | a per-row constant (see below) | — | [C] |
| `*constant desc` | str, 34 set | — (comment) | names the `constants` value of the row | — | — |
| `*eol` | always 0 | — | end-of-line marker | — | — |

`[C]` `exclude1` resolves against MonType `type` with a blank cell stored as 0. MonType row 0 is itself blank, so
"blank" and "MonType row 0" are the same value; `sandleaper` is MonType row 22.

`[C]` *cpick note*: `champion` and the three `cpick` columns hold the same value in every row, so `probe` could place
them only as a group (`+0x008` u8, `+0x00E`/`+0x010`/`+0x012` u16, either way round). The layout takes `champion` as the
u8 at `+0x008` and `cpick` as the three u16, because the reader `sub_005A0500_ChampionModPick` takes the champion
weight as the u16 at `+0x0E + 2·difficulty` (`[I]`, [monsters/0002 § 8](../findings/monsters/0002-room-population.md#8-classic-expansion-and-difficulty)).

## Pick weights per difficulty

`[C]` from `python3 -I tools/mon_survey.py umod workspace/merged/data/global/excel` (last line
`SURVEY mon_umod records=43 … cpick_normal_n=5 … upick_normal_sum=72 … upick_nightmare_sum=78 … exclude_pairs=1`).
"Classic" and "expansion" below apply the survey's own filter (`enabled` = 1, and `version` = 0 for classic). `[I]` The
code's filter agrees: `enabled` ≠ 0 and, in a classic game, `version` < 100; it also tests `champion`, the `exclude`
types, `fPick` and (unique pick) the mods already present, which the survey does not
([monsters/0003 § 3](../findings/monsters/0003-special-monsters.md#3-the-two-picks-and-modeligible)).

| Difficulty | `cpick` non-zero (weight) | sum: all / classic / expansion | `upick` non-zero (weight 6 each) | sum |
|---|---|---|---|---|
| Normal | `champion` 16, `ghostly` 36, `fanatic` 37, `possessed` 38, `berserk` 39 (1 each) | 5 / 1 / 5 | `strong` 5, `fast` 6, `curse` 7, `fire` 9, `lightning` 17, `cold` 18, `manahit` 25, `teleport` 26, `spectralhit` 27, `stoneskin` 28, `multishot` 29, `aura` 30 (12) | 72 |
| Nightmare | same five | 5 / 1 / 5 | the twelve + `resist` 8 (13) | 78 |
| Hell | same five | 5 / 1 / 5 | the twelve + `resist` 8 (13) | 78 |

- `[C]` Of the champion mods only `champion` (16) has `version` 0; `ghostly`, `fanatic`, `possessed` and `berserk` are
  `version` 100. All thirteen `upick` mods are `version` 0 and `enabled` 1; all but `aura` (30) have `xfer` 1, and so do the five champion mods.
- `[C]` The only `exclude` pair in the table is `lightning` (17) `exclude1` = `sandleaper` (MonType 22). `exclude2` is
  never set.
- `[C]` `fPick` is set only on three unique mods: `fast` 3, `teleport` 1, `multishot` 2.
- `[C]` `resist` (8) is the only mod whose weight differs by difficulty (0 in Normal, 6 in Nightmare and Hell).
- `[C]` `thief` (24, `enabled` 0, no weight) is `Mod3` of the superunique Lord De Seis ([SuperUniques](SuperUniques.md)).

## Interpretation notes

- **`constants` is a list, not a property of the mod.** `[C]` by data: the `*constant desc` of a row does not describe
  that row's mod (row 1 `rndname` holds 100, "minion +hp%"; row 16 `champion` holds 0, "minion +elem min dmg%"). Rows 0–33
  carry 34 constants; 34–42 are blank (0). By description: row 0 champion chance (20); rows 1–3 minion +hp% per
  difficulty (100/75/50); 4–6 champion +hp% (200/150/100); 7–9 unique +hp% (300/200/100); 10 champion +tohit% (75);
  11 champion +dmg% (100); 12 minion +tohit% (50); 13 unique +tohit% (100); 14 minion +dmg% (strong) (75); 15 unique
  +dmg% (strong) (150); 16–21 minion elemental min/max dmg% per difficulty (0/33/33, 0/50/50); 22–27 champion elemental
  min/max (33/33/33, 50/50/50); 28–33 unique elemental min/max (66/66/66, 100/100/100). The descriptions are `[L]`.
- `[C]` **Row 0 `constants` = 20 is the champion chance**: the special branch rolls `Range(boss.seed, 100) <` the u32 at
  MonUMod record 0 `+0x1C`, confirmed by run (fn:sub_005A0760_SpecialModsRoll@0x005A0760, 0x005A0817,
  run:2026-10-13-mon-spawn; [monsters/0002 § 5](../findings/monsters/0002-room-population.md#5-the-two-group-branches)).
  The other constants have no reader read yet `[L]` (their effects belong to `monsters/stats`).
- `[I]` **The two picks.** `ChampionModPick` and `UniqueModPick` walk the 43 rows in row order; a row is a candidate when
  its weight for the difficulty is > 0, its `champion` byte matches the pick, it passes `ModEligible` (`enabled`,
  `version` against the expansion flag `game+0x70`, `exclude1`/`exclude2`, `fPick`) and, for the unique pick, it is not
  already among the monster's mods. One `Range(unit.seed, Σweights)` selects by cumulative weight; no candidate, no draw.
  (fn:sub_005A0500_ChampionModPick@0x005A0500, fn:sub_005A0600_UniqueModPick@0x005A0600, fn:sub_005A03E0_ModEligible@0x005A03E0,
  [monsters/0003 § 3](../findings/monsters/0003-special-monsters.md#3-the-two-picks-and-modeligible))
- `[I]` The `exclude` test is "the class's MonType is reachable from the excluded type" through MonType `equiv1`–`equiv3`;
  the columns and the closure are in [MonType](MonType.md#equiv-semantics) (fn:sub_00658460_MonTypeReachable@0x00658460).
- `[I]` Superunique fixed mods (`Mod1`–`Mod3`) skip `ModEligible`, so `enabled`, `fPick` and `exclude*` do not apply to
  them; `thief` (24) is dropped by a test of its own (fn:sub_005A49B0_SuperUniqueSpawn@0x005A49B0,
  [monsters/0003 § 6](../findings/monsters/0003-special-monsters.md#6-superuniques-superuniquespawn)).

## Open questions

- `[L]` Whether `+0x000` is a u32 or a u16 `id` followed by a zero u16.
- `[L]` The readers of `constants` rows 1–33 (`monsters/stats`).
