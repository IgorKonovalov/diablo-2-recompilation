# DifficultyLevels (`data/global/excel/difficultylevels.txt` → `difficultylevels.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 3 (no `Expansion` marker)   **Record:** 88 B (`0x58`)
> **sha256:** `.txt` `6929153657001e19f2ea0e04d839a5f2534d00b91460d76006d9c51784d76fa3`, `.bin` `d7842533610b2511558b95152c0e2bedbf462482007dab2ea12c8dd939dc89f5`
> **Doc status:** columns listed, `.bin` layout complete (the three equal groups fixed by the loader descriptor, plan 0025 Phase 1); semantics `[I]` for the monster-creation readers ([monsters/0004](../findings/monsters/0004-stats.md)), pending elsewhere

## Purpose

One row per game difficulty (`Normal`, `Nightmare`, `Hell`), holding per-difficulty constants. By the column
names `[L]` they are: the player resistance penalty, the experience lost on death, the odds of exceptional
(`Uber`) and elite (`Ultra`) item codes, a monster skill-level bonus, divisors for freeze, cold and curse
durations and for life and mana steal, the damage bonus of uniques and champions, damage percentages for
hireable bosses and "CE" monster damage, a Static Field floor, and the gamble odds. Plan 0025 lists it for
`monsters/stats` (`MonsterSkillBonus`, the damage bonuses and percents); the item columns concern `items/*` and
the gamble columns vendors. Readers named so far: § Code semantics.

## Row identity

- `[C]` `Name` is **not compiled**: no field of `difficultylevels.bin` holds it (`excel_bin.py diff`: `Name` is a
  `.txt`-only column), so a record is addressed by its position. The three rows are `Normal`, `Nightmare`,
  `Hell` in that order. (tbl:DifficultyLevels.txt:Name)
- `[I]` Record index = difficulty (0 normal, 1 nightmare, 2 hell), the index the MonStats `(N)`/`(H)` columns
  use: every reader goes through `sub_00611D30_DifficultyRec(game+0x6D)`, which returns record `clamp(d, 0, n − 1)`
  ([monsters/0004 § 1](../findings/monsters/0004-stats.md#1-the-two-loader-descriptors),
  fn:sub_00611D30_DifficultyRec@0x00611D30, data:g_pDifficultyLevels@0x0096C8AC).
- `[C]` The loader reads `difficultylevels.bin` with 88-byte records
  ([data/0001 §4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables), call site
  `0x006180B9`); the record count (3) equals the `.txt` data rows.

## Columns

`[C]` layout tags are by data behaviour: `python3 -I tools/excel_bin.py diff <excel-dir> difficultylevels`
decodes every record and compares it with every mapped cell (3 records × 22 fields = 66 cells, 0 mismatches).
A field is tagged `[C]` when the column's values pin its offset (a probe over every record finds no other
offset that fits), `[I]` when the column equals a sibling in every row, so probe places only the group and
the slot inside it is fixed by the loader descriptor (below). Width: 22 fields × 4 bytes fill the 88-byte record exactly, with no
gap, so every field is a dword `[C]`; signedness is `[I]` (`ResistPenalty` is negative, and all are read as
s32). Observed ranges are over the 3 rows. **Meaning:** no column semantics are claimed here.

| Column | Observed type / range | `.bin` field | Equal to | Layout tag |
|---|---|---|---|---|
| `Name` | str, 3 distinct (`Normal`, `Nightmare`, `Hell`) | — (not compiled) | — | — |
| `ResistPenalty` | int −100..0 (3 distinct) | `+0x000` s32 | — | [C] |
| `DeathExpPenalty` | int 0..10 (3 distinct) | `+0x004` s32 | — | [C] |
| `UberCodeOddsNormal` | int 0..20 (3 distinct) | `+0x008` s32 | — | [C] |
| `UberCodeOddsGood` | int 0..40 (3 distinct) | `+0x00C` s32 | — | [C] |
| `UltraCodeOddsNormal` | int 0..30 (2 distinct) | `+0x020` s32 | — | [C] |
| `UltraCodeOddsGood` | int 0..40 (2 distinct) | `+0x024` s32 | — | [C] |
| `MonsterSkillBonus` | int 0..7 (3 distinct) | `+0x010` s32 | — | [C] |
| `MonsterFreezeDivisor` | int 1..4 (3 distinct) | `+0x014` s32 | `MonsterColdDivisor`, `AiCurseDivisor` | [C] (descriptor) |
| `MonsterColdDivisor` | int 1..4 (3 distinct) | `+0x018` s32 | `MonsterFreezeDivisor`, `AiCurseDivisor` | [C] (descriptor) |
| `AiCurseDivisor` | int 1..4 (3 distinct) | `+0x01C` s32 | `MonsterFreezeDivisor`, `MonsterColdDivisor` | [C] (descriptor) |
| `LifeStealDivisor` | int 1..3 (3 distinct) | `+0x028` s32 | `ManaStealDivisor` | [C] (descriptor) |
| `ManaStealDivisor` | int 1..3 (3 distinct) | `+0x02C` s32 | `LifeStealDivisor` | [C] (descriptor) |
| `UniqueDamageBonus` | int 66..90 (3 distinct) | `+0x030` s32 | `ChampionDamageBonus` | [C] (descriptor) |
| `ChampionDamageBonus` | int 66..90 (3 distinct) | `+0x034` s32 | `UniqueDamageBonus` | [C] (descriptor) |
| `HireableBossDamagePercent` | int 25..50 (3 distinct) | `+0x038` s32 | — | [C] |
| `MonsterCEDamagePercent` | int 20..50 (3 distinct) | `+0x03C` s32 | — | [C] |
| `StaticFieldMin` | int 0..50 (3 distinct) | `+0x040` s32 | — | [C] |
| `GambleRare` | int, always 10000 | `+0x044` s32 | — | [C] |
| `GambleSet` | int, always 100 | `+0x048` s32 | — | [C] |
| `GambleUnique` | int, always 50 | `+0x04C` s32 | — | [C] |
| `GambleUber` | int, always 90 | `+0x050` s32 | — | [C] |
| `GambleUltra` | int, always 33 | `+0x054` s32 | — | [C] |

The five `Gamble*` columns are constant, but each value occurs at one offset only in all three records, so probe
pins them. Every value rises or stays equal from `Normal` to `Hell` except `ResistPenalty` (0, −40, −100) and the
two damage bonuses and two damage percents, which fall.

## Record layout (88 bytes)

Twenty-two s32, `Name` left out, **not in `.txt` column order**:

```
+0x000 ResistPenalty         +0x02C ManaStealDivisor
+0x004 DeathExpPenalty       +0x030 UniqueDamageBonus
+0x008 UberCodeOddsNormal    +0x034 ChampionDamageBonus
+0x00C UberCodeOddsGood      +0x038 HireableBossDamagePercent
+0x010 MonsterSkillBonus     +0x03C MonsterCEDamagePercent
+0x014 MonsterFreezeDivisor  +0x040 StaticFieldMin
+0x018 MonsterColdDivisor    +0x044 GambleRare
+0x01C AiCurseDivisor        +0x048 GambleSet
+0x020 UltraCodeOddsNormal   +0x04C GambleUnique
+0x024 UltraCodeOddsGood     +0x050 GambleUber
+0x028 LifeStealDivisor      +0x054 GambleUltra
```

No unknown bytes.

- `[C]` `UltraCodeOddsNormal` and `UltraCodeOddsGood` sit at `+0x020`/`+0x024`, **after** the three divisors,
  though the `.txt` lists them right after the `UberCodeOdds` pair: probe finds no other offset where their values
  (0, 0, 30 and 0, 0, 40) fit all three records. (tbl:DifficultyLevels.txt:UltraCodeOddsNormal)
- `[C]` Three groups are equal column for column in every row, so the data places only the group: the divisors
  `MonsterFreezeDivisor`/`MonsterColdDivisor`/`AiCurseDivisor` (`+0x014..+0x01C`), `LifeStealDivisor`/
  `ManaStealDivisor` (`+0x028`/`+0x02C`) and `UniqueDamageBonus`/`ChampionDamageBonus` (`+0x030`/`+0x034`).
  The loader's field descriptor (`sub_00617D90_DifficultyLevelsLoad`) names every column with its offset, and the
  member order inside each group is the `.txt` order this layout uses; the diff of all 66 cells is the second path.
  ([monsters/0004 § 1](../findings/monsters/0004-stats.md#1-the-two-loader-descriptors),
  fn:sub_00617D90_DifficultyLevelsLoad@0x00617D90, struct:DifficultyLevelsRec+0x34)

## Code semantics (plan 0025 Phase 1)

From [monsters/0004](../findings/monsters/0004-stats.md) (static reading). Only the monster-creation readers were
read as code.

- `[I]` **`MonsterSkillBonus`** (`+0x10`): added to every MonStats skill level at creation, `Sk<k>lvl +
  MonsterSkillBonus` (0 / 3 / 7 by data), through `MonPlayerBonus`
  ([monsters/0004 § 2](../findings/monsters/0004-stats.md#2-monstatsinit-in-order), fn:sub_00573930_MonPlayerBonus@0x00573930,
  tbl:DifficultyLevels.txt:MonsterSkillBonus).
- `[I]` **`ChampionDamageBonus`** (`+0x34`, `CDB`; 90 / 75 / 66 by data): read by the `champion`, `berserk` and `strong`
  mod handlers, the last for uniques and minions too: damage % = `CDB · c ÷ 100` and to-hit % likewise, with `c` a
  MonUMod `constants` row or 300 for `berserk` ([monsters/0004 § 8](../findings/monsters/0004-stats.md#8-the-mod-handlers-stat-effects),
  fn:sub_005A0E80_UModChampion@0x005A0E80, fn:sub_005A17E0_UModStrong@0x005A17E0,
  tbl:DifficultyLevels.txt:ChampionDamageBonus). So the "unique" damage bonus of an Extra Strong unique comes from
  this column (see Open questions for `UniqueDamageBonus`).
- `[I]` Every reader goes through `DifficultyRec(game+0x6D)`, so the record is the game's difficulty
  (fn:sub_00611D30_DifficultyRec@0x00611D30).

## Interpretation notes

- `[L]` By their names, `ResistPenalty` is a player penalty and `MonsterFreezeDivisor`/`MonsterColdDivisor`/
  `AiCurseDivisor` combat-time durations; none of them is a monster-creation input (§ Code semantics lists the
  creation readers).
- `[L]` `tools/mon_survey.py stats <excel-dir> <class> <difficulty>` prints the row of the difficulty asked beside
  the class's MonStats and MonLvl cells.

## Open questions

- ~~Whether the record index is the game's difficulty, and the member order inside the three equal groups~~
  answered by [monsters/0004 § 1](../findings/monsters/0004-stats.md#1-the-two-loader-descriptors) (Row identity,
  Record layout).
- `[L]` **`UniqueDamageBonus` (`+0x30`) and `HireableBossDamagePercent` (`+0x38`): no reader found**, but the scan
  covered only the 40 instructions after each of the 22 `DifficultyRec` call sites, so a reader that keeps the record
  longer would be missed. The architect's ruling (plan 0025 log) makes this an open question, not a contradiction of
  `src:d2dfg-blizzard`: plan 0025 Phase 2 runs a full static xref of the `+0x30` field. The two bonus columns are
  equal in stock data, so play cannot tell them apart.
- `[L]` The other readers: the scan saw displacements `+0x14`, `+0x18`, `+0x1C`, `+0x28`/`+0x2C`, `+0x3C`, `+0x40`
  and `+0x44..+0x4C` near call sites, none read as code (monsters/0004 § 1).
