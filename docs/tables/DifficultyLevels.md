# DifficultyLevels (`data/global/excel/difficultylevels.txt` → `difficultylevels.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 3 (no `Expansion` marker)   **Record:** 88 B (`0x58`)
> **sha256:** `.txt` `6929153657001e19f2ea0e04d839a5f2534d00b91460d76006d9c51784d76fa3`, `.bin` `d7842533610b2511558b95152c0e2bedbf462482007dab2ea12c8dd939dc89f5`
> **Doc status:** columns listed, `.bin` layout complete (three groups placed by order, below), semantics pending

## Purpose

One row per game difficulty (`Normal`, `Nightmare`, `Hell`), holding per-difficulty constants. By the column
names `[L]` they are: the player resistance penalty, the experience lost on death, the odds of exceptional
(`Uber`) and elite (`Ultra`) item codes, a monster skill-level bonus, divisors for freeze, cold and curse
durations and for life and mana steal, the damage bonus of uniques and champions, damage percentages for
hireable bosses and "CE" monster damage, a Static Field floor, and the gamble odds. Plan 0025 lists it for
`monsters/stats` (`MonsterSkillBonus`, the damage bonuses and percents); the item columns concern `items/*` and
the gamble columns vendors. No reader of any column is named yet.

## Row identity

- `[C]` `Name` is **not compiled**: no field of `difficultylevels.bin` holds it (`excel_bin.py diff`: `Name` is a
  `.txt`-only column), so a record is addressed by its position. The three rows are `Normal`, `Nightmare`,
  `Hell` in that order. (tbl:DifficultyLevels.txt:Name)
- `[L]` Record index = difficulty (0 normal, 1 nightmare, 2 hell), the index the MonStats `(N)`/`(H)` columns
  use. Nothing in our code reading anchors it yet.
- `[C]` The loader reads `difficultylevels.bin` with 88-byte records
  ([data/0001 §4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables), call site
  `0x006180B9`); the record count (3) equals the `.txt` data rows.

## Columns

`[C]` layout tags are by data behaviour: `python3 -I tools/excel_bin.py diff <excel-dir> difficultylevels`
decodes every record and compares it with every mapped cell (3 records × 22 fields = 66 cells, 0 mismatches).
A field is tagged `[C]` when the column's values pin its offset (a probe over every record finds no other
offset that fits), `[I]` when the column equals a sibling in every row, so probe places only the group and
the slot inside it is a choice (below). Width: 22 fields × 4 bytes fill the 88-byte record exactly, with no
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
| `MonsterFreezeDivisor` | int 1..4 (3 distinct) | `+0x014` s32 | `MonsterColdDivisor`, `AiCurseDivisor` | [I] |
| `MonsterColdDivisor` | int 1..4 (3 distinct) | `+0x018` s32 | `MonsterFreezeDivisor`, `AiCurseDivisor` | [I] |
| `AiCurseDivisor` | int 1..4 (3 distinct) | `+0x01C` s32 | `MonsterFreezeDivisor`, `MonsterColdDivisor` | [I] |
| `LifeStealDivisor` | int 1..3 (3 distinct) | `+0x028` s32 | `ManaStealDivisor` | [I] |
| `ManaStealDivisor` | int 1..3 (3 distinct) | `+0x02C` s32 | `LifeStealDivisor` | [I] |
| `UniqueDamageBonus` | int 66..90 (3 distinct) | `+0x030` s32 | `ChampionDamageBonus` | [I] |
| `ChampionDamageBonus` | int 66..90 (3 distinct) | `+0x034` s32 | `UniqueDamageBonus` | [I] |
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
- `[I]` Three groups are equal column for column in every row, so the data places only the group: the divisors
  `MonsterFreezeDivisor`/`MonsterColdDivisor`/`AiCurseDivisor` (`+0x014..+0x01C`), `LifeStealDivisor`/
  `ManaStealDivisor` (`+0x028`/`+0x02C`) and `UniqueDamageBonus`/`ChampionDamageBonus` (`+0x030`/`+0x034`).
  Inside each group the layout follows the `.txt` order. With stock data a reader cannot tell which member it
  reads; a modded table could. Which column the code reads at which offset is a reverser question (backlog).

## Interpretation notes

- `[L]` The column names suggest that only `MonsterSkillBonus`, `UniqueDamageBonus`, `ChampionDamageBonus`,
  `HireableBossDamagePercent` and `MonsterCEDamagePercent` touch monster stats at creation; `ResistPenalty` is by
  its name a player penalty, `MonsterFreezeDivisor`/`MonsterColdDivisor`/`AiCurseDivisor` combat-time durations.
  `monsters/stats` (plan 0025 Phase 1) reads which of them the monster init uses.
- `[L]` `tools/mon_survey.py stats <excel-dir> <class> <difficulty>` prints the row of the difficulty asked beside
  the class's MonStats and MonLvl cells.

## Open questions

- `[L]` Which code reads each column, and whether the record index is the game's difficulty
  ([backlog](../backlog.md), archivist → reverser, plan 0025 Phase 1).
- `[L]` The member order inside the three equal groups (above).
