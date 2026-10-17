# DifficultyLevels (`data/global/excel/difficultylevels.txt` → `difficultylevels.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 3 (no `Expansion` marker)   **Record:** 88 B (`0x58`)
> **sha256:** `.txt` `6929153657001e19f2ea0e04d839a5f2534d00b91460d76006d9c51784d76fa3`, `.bin` `d7842533610b2511558b95152c0e2bedbf462482007dab2ea12c8dd939dc89f5`
> **Doc status:** columns listed, `.bin` layout complete (the three equal groups fixed by the loader descriptor, plan 0025 Phase 1); semantics `[I]` for the monster-creation readers ([monsters/0004](../findings/monsters/0004-stats.md)) and the combat readers ([combat/0001](../findings/combat/0001-formulas.md), plan 0039 A1); every column but the `Uber`/`Ultra` code odds and `UniqueDamageBonus` has a named reader

## Purpose

One row per game difficulty (`Normal`, `Nightmare`, `Hell`), holding per-difficulty constants. By the column
names `[L]` they are: the player resistance penalty, the experience lost on death, the odds of exceptional
(`Uber`) and elite (`Ultra`) item codes, a monster skill-level bonus, divisors for freeze, cold and curse
durations and for life and mana steal, the damage bonus of uniques and champions, damage percentages for
hireable bosses and "CE" monster damage, a Static Field floor, and the gamble odds. Plan 0025 lists it for
`monsters/stats` (`MonsterSkillBonus`, the damage bonuses and percents); the item columns concern `items/*` and
the gamble columns vendors. Readers named so far: § Code semantics and § Gamble columns.

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
  this column (`UniqueDamageBonus` has no reader, below).
- `[I]` Every reader goes through `DifficultyRec(game+0x6D)`, so the record is the game's difficulty
  (fn:sub_00611D30_DifficultyRec@0x00611D30).
- `[I]` **`UniqueDamageBonus` (`+0x30`) has no reader** (plan 0025 Phase 2). `g_pDifficultyLevels` is referenced only
  by the loader, the unload and `DifficultyRec`; each of the 23 call sites of `DifficultyRec` was followed to every use
  of the returned pointer, and none reads `+0x30` (the `+0x30` read at `0x00547AA3` is a Levels record). So a unique's
  damage bonus comes from `ChampionDamageBonus` through the `strong` handler (above). This is the
  [monsters/0004 § 1](../findings/monsters/0004-stats.md#1-the-two-loader-descriptors) xref, which combat/0001 § 12b
  (c) leaves standing; it stays `[I]` because the two columns are equal in stock data and play cannot tell them
  apart. (fn:sub_00611D30_DifficultyRec@0x00611D30, data:g_pDifficultyLevels@0x0096C8AC, 0x00547AA3)
- **(corrected, plan 0039 A1)** This bullet said `HireableBossDamagePercent` (`+0x38`) has no reader too. It has one:
  `COMBAT_DamagePercent` reads it at `0x0057C0FE` through the record pointer kept in the reduction context
  (`ReduceCtx+0x04`), a use the `DifficultyRec` call-site walk missed ([monsters/0004 § 1](../findings/monsters/0004-stats.md#1-the-two-loader-descriptors)
  carries the same correction); the `+0x38` reads near `0x0057C3C2`/`0x0057C4B8`
  are still a damage block. See [§ Combat readers](#combat-readers-plan-0037-phase-1-plan-0039-a1).
  (fn:COMBAT_DamagePercent@0x0057C060, struct:ReduceCtx+0x04)

## Gamble columns (plan 0031)

From [items/0009 § 7](../findings/items/0009-vendors.md#7-gambling-gamble_buildinv-0x00578790) (static reading).
`GAMBLE_BuildInv` is the only reader found of the five columns (its `DifficultyRec` call at `0x005787B7`).

- `[I]` **`GambleRare`, `GambleSet`, `GambleUnique`** (`+0x44`, `+0x48`, `+0x4C`) are shares out of 100 000, taken
  cumulatively in the order unique, set, rare. When their sum is > 0, one store-seed step gives `r = low % 100000`
  (unsigned): `r < GambleUnique` → quality 7, `< GambleUnique + GambleSet` → 5, `< GambleUnique + GambleSet +
  GambleRare` → 6, else 4 (magic). Stock values give unique 0.05 %, set 0.1 %, rare 10 %, magic 89.85 %, in every
  difficulty. (fn:GAMBLE_BuildInv@0x00578790, tbl:DifficultyLevels.txt:GambleUnique, tbl:DifficultyLevels.txt:GambleSet,
  tbl:DifficultyLevels.txt:GambleRare)
- `[I]` **`GambleUber`, `GambleUltra`** (`+0x50`, `+0x54`), expansion games only (`GAMBLE_Upgrade`): with the base's
  `ubercode` valid, `c = (lvl − level(ubercode))·GambleUber + 1`; `c ≤ 0` keeps the base with no draw; else
  `R(S, 10000) < c` gives the uber base. After a failed uber draw the same test with `ultracode`, its level and
  `GambleUltra` gives the ultra base. `lvl` is the slot's gamble level. (fn:GAMBLE_Upgrade@0x005786A0,
  tbl:DifficultyLevels.txt:GambleUber, tbl:DifficultyLevels.txt:GambleUltra)

## Combat columns (plan 0037 Phase 0)

The columns that by their names are combat-time constants, with their values per row. Offsets and widths are
§ [Record layout](#record-layout-88-bytes) (`[C]`, `excel_bin.py diff`, 66 cells, 0 mismatches); the values are
`python3 -I tools/combat_survey.py difficulty workspace/merged/data/global/excel` (gate survey `combat`), `[C]` as data.

| Column | `.bin` field | Normal | Nightmare | Hell | Reader so far |
|---|---|---:|---:|---:|---|
| `ResistPenalty` | `+0x000` s32 | 0 | −40 | −100 | `[C]` `COMBAT_ResistFor`, player and hireling defenders, expansion only |
| `MonsterFreezeDivisor` | `+0x014` s32 | 1 | 2 | 4 | `[I]` `COMBAT_ApplyFreeze`, monster defenders |
| `MonsterColdDivisor` | `+0x018` s32 | 1 | 2 | 4 | `[I]` `COMBAT_ApplyCold`, monster defenders with `coldeffect` < 0 |
| `AiCurseDivisor` | `+0x01C` s32 | 1 | 2 | 4 | `[I]` four curse functions, use not read |
| `LifeStealDivisor` | `+0x028` s32 | 1 | 2 | 3 | `[C]` `COMBAT_Leech`, player attackers |
| `ManaStealDivisor` | `+0x02C` s32 | 1 | 2 | 3 | `[C]` `COMBAT_Leech`, player attackers |
| `UniqueDamageBonus` | `+0x030` s32 | 90 | 75 | 66 | `[I]` none in the whole binary (§ Code semantics) |
| `ChampionDamageBonus` | `+0x034` s32 | 90 | 75 | 66 | `[I]` the `champion`, `berserk`, `strong` mod handlers (§ Code semantics) |
| `HireableBossDamagePercent` | `+0x038` s32 | 50 | 35 | 25 | `[C]` `COMBAT_DamagePercent`, hireling against boss (all three difficulties) |
| `MonsterCEDamagePercent` | `+0x03C` s32 | 50 | 35 | 20 | `[I]` `sub_005A2620_MonDeathDamage` |
| `StaticFieldMin` | `+0x040` s32 | 0 | 33 | 50 | `[I]` `sub_005C9800_SorSkillStaticMin`, expansion only |

- `[C]` `HireableBossDamagePercent` and `MonsterCEDamagePercent` are equal in Normal and Nightmare and differ only in
  Hell (25 against 20), so a run in Hell tells the two apart; the three divisors are equal in every row, and so are the
  two steal divisors (§ Record layout). (tbl:DifficultyLevels.txt:MonsterCEDamagePercent,
  tbl:DifficultyLevels.txt:HireableBossDamagePercent)
- The "Reader" column is the summary of [§ Combat readers](#combat-readers-plan-0037-phase-1-plan-0039-a1), which
  carries the anchors. It replaced the plan 0037 Phase 0 `[L]` readings by name ("none" in every row then); two of
  them were wrong in detail: the steal divisors apply to **player** attackers whatever the defender, and
  `MonsterCEDamagePercent` scales a monster's own death damage (a death explosion from its MonLvl life), which is not
  read as a corpse explosion.

## Combat readers (plan 0037 Phase 1, plan 0039 A1)

From [combat/0001](../findings/combat/0001-formulas.md) §§ 7, 9, 12 and 12b (c) (static reading), and § 15 for the
cases run:2026-10-16-combat reproduced. Every reader goes through `DifficultyRec(game+0x6D)` or the record pointer
the reduction context keeps (`ReduceCtx+0x04`).

- `[C]` **`ResistPenalty`** (`+0x00`): `COMBAT_ResistFor` adds it to the resistance of a defender that is not a
  monster (a **player or a hireling**) for every row but physical and magic, in an **expansion** game only; a classic
  game uses the constants −20 (Nightmare) and −50 (Hell) instead. The result is then floored at −100 and capped at
  `min(75 + max, 95)`. Monster defenders are neither penalised nor capped. Reproduced on the player: the classic
  constants in 138 (Nightmare) and 208 (Hell) events, the expansion `ResistPenalty` throughout (combat/0001 § 15,
  [combat/reductions](../specs/combat/reductions.md) B2).
  ([combat/0001 § 7](../findings/combat/0001-formulas.md#7-reductions-combat_applyreductions),
  fn:COMBAT_ResistFor@0x0057BE00, struct:ReduceCtx+0x04, run:2026-10-16-combat, tbl:DifficultyLevels.txt:ResistPenalty)
- `[C]` **`HireableBossDamagePercent`** (`+0x38`): the percent `P` of `COMBAT_DamagePercent` when the attacker is a
  hireling and the defender a boss; `P` scales every scaled field of the packet (`MulDiv(field, P, 100)`) before the
  resistances. Reproduced for the mercenary hitting Andariel with 50 (Normal, 2 events), 35 (Nightmare, 78) and 25
  (Hell, 33), one read indexed by the difficulty; all 33 Hell events logged `P` = 25, which tells this column from
  `MonsterCEDamagePercent` (20 in Hell) ([combat/reductions § A2](../specs/combat/reductions.md#a-combat_applyreductions)).
  (fn:COMBAT_DamagePercent@0x0057C060, 0x0057C0FE, run:2026-10-16-combat,
  tbl:DifficultyLevels.txt:HireableBossDamagePercent)
- `[C]` **`LifeStealDivisor`, `ManaStealDivisor`** (`+0x28`, `+0x2C`): in `COMBAT_Leech`, for a **player** attacker,
  the life and mana steal fields (already `<< 6`) are divided by them (signed, when ≠ 0) before the gains are
  computed; the defender's mana loss reads the same divided field. Reproduced with the leech of players and the
  mercenary (combat/0001 § 15). That monster and hireling attackers are not divided is `[I]` (the monster branch and
  the hireling path were not asserted apart, [combat/delivery](../specs/combat/delivery.md) C1).
  ([combat/0001 § 9](../findings/combat/0001-formulas.md#9-leech-stun-cold-freeze-poison-burn), fn:COMBAT_Leech@0x0057C420,
  0x0057C47D–0x0057C4CE, run:2026-10-16-combat, tbl:DifficultyLevels.txt:LifeStealDivisor)
- `[I]` **`MonsterColdDivisor`** (`+0x18`): `COMBAT_ApplyCold` divides the cold length by it for a **monster** defender
  whose MonStats `coldeffect` is < 0; the length is then at least 1. (fn:COMBAT_ApplyCold@0x0057AF80, 0x0057B00D,
  tbl:DifficultyLevels.txt:MonsterColdDivisor)
- `[I]` **`MonsterFreezeDivisor`** (`+0x14`): `COMBAT_ApplyFreeze` divides the freeze length by it for a monster that
  can be frozen (not a boss, unique or hireling, `coldeffect` < 0, not under state 54); players, bosses, uniques and
  hirelings get cold instead. No freeze was reproduced. (fn:COMBAT_ApplyFreeze@0x0057B230, 0x0057B2F1,
  tbl:DifficultyLevels.txt:MonsterFreezeDivisor)
- `[I]` **`AiCurseDivisor`** (`+0x1C`) is read in four curse functions, `0x004E6E30`, `0x004EDEA0`, `0x005C37A0` and
  `0x005C39C0`; what they do with it is not read (§ Open questions). Not a combat-formula input.
  ([combat/0001 § 12](../findings/combat/0001-formulas.md#12-branches-difficulty-game-type-players-hirelings-player-against-player))
- `[I]` **`MonsterCEDamagePercent`** (`+0x3C`) is read by `sub_005A2620_MonDeathDamage`, a monster's death explosion
  computed from its MonLvl life (0x005A2709). Not a combat-formula input. (fn:sub_005A2620_MonDeathDamage@0x005A2620,
  tbl:DifficultyLevels.txt:MonsterCEDamagePercent)
- `[I]` **`StaticFieldMin`** (`+0x40`) is read by `sub_005C9800_SorSkillStaticMin`, in an expansion game only.
  (fn:sub_005C9800_SorSkillStaticMin@0x005C9800, tbl:DifficultyLevels.txt:StaticFieldMin)
- `[C]` `HireableBossDamagePercent` and `MonsterCEDamagePercent` are equal in Normal and Nightmare, but
  `COMBAT_DamagePercent` reads the first: the Hell mercenary hitting a boss shows its 25 in all 33 events, not
  `MonsterCEDamagePercent`'s 20. (fn:COMBAT_DamagePercent@0x0057C060, 0x0057C0FE, run:2026-10-16-combat) `[I]` The
  other column feeds `MonDeathDamage` only (above). (fn:sub_005A2620_MonDeathDamage@0x005A2620)
- `[I]` Outside combat, **`DeathExpPenalty`** (`+0x04`) is read by `PLAYER_DeathExpLoss`: a player above level 1 loses
  `DeathExpPenalty × (Exp[lvl] − Exp[lvl − 1]) / 100` experience on death, never below the level's start
  ([player/0001](../findings/player/0001-creation.md), fn:PLAYER_DeathExpLoss@0x005359F0,
  tbl:DifficultyLevels.txt:DeathExpPenalty).

## Interpretation notes

- `[I]` None of the combat columns is a monster-creation input: their readers are the combat and skill functions of
  [§ Combat readers](#combat-readers-plan-0037-phase-1-plan-0039-a1) (§ Code semantics lists the creation readers).
- `[L]` `tools/mon_survey.py stats <excel-dir> <class> <difficulty>` prints the row of the difficulty asked beside
  the class's MonStats and MonLvl cells.

## Open questions

- ~~Whether the record index is the game's difficulty, and the member order inside the three equal groups~~
  answered by [monsters/0004 § 1](../findings/monsters/0004-stats.md#1-the-two-loader-descriptors) (Row identity,
  Record layout).
- ~~Whether anything reads `UniqueDamageBonus` (`+0x30`) or `HireableBossDamagePercent` (`+0x38`)~~ answered `[I]`
  by the plan 0025 Phase 2 full xref: no reader ([§ Code semantics](#code-semantics-plan-0025-phase-1)). Absence cannot
  be reproduced on stock data, where the two bonus columns are equal. **Corrected (plan 0039 A1):** that holds for
  `UniqueDamageBonus` only; `HireableBossDamagePercent` is read by `COMBAT_DamagePercent`
  ([§ Combat readers](#combat-readers-plan-0037-phase-1-plan-0039-a1)).
- ~~The other readers: the scan saw displacements `+0x14`, `+0x18`, `+0x1C`, `+0x28`/`+0x2C`, `+0x3C` and `+0x40`
  near call sites, none read as code~~ answered by combat/0001 ([§ Combat readers](#combat-readers-plan-0037-phase-1-plan-0039-a1));
  `+0x44..+0x54` are read by gambling ([§ Gamble columns](#gamble-columns-plan-0031)). The `HireableBossDamagePercent`
  "no reader" above is corrected there.
- `[L]` What the four curse functions do with `AiCurseDivisor` (by the name, a curse duration divisor), and how
  `StaticFieldMin` bounds Static Field (by the name, a floor in percent of life). Owner of a future skills finding.
- The `UberCodeOdds*`/`UltraCodeOdds*` columns have no reader in a finding yet.
