# 0025 — Monsters: stats per level, difficulty and player count

> **Status:** in-progress (approved 2026-10-14)
> **Created:** 2026-10-14
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0007-fetched-leads-only

## TL;DR

**Question:** once a monster is placed with its level ([pool.md § E](../specs/monsters/pool.md#e-the-monster-level-sub_00573cb0_monstatsinit))
and its special mods ([monsters/special](../specs/monsters/special.md)), what hit points, defence, to-hit, damage,
resistances and experience does it get? Which draws on the monster's unit seed set them, and how do difficulty, the
player count and the mods change them?

When it is done:
- `docs/findings/monsters/0004-stats.md` has the realisation at `[C]`;
- `tools/monstats.py` predicts a monster's stats from its class, level, difficulty, player count and mods;
- `docs/specs/monsters/stats.md` is drafted.

It also settles the open question on the level the `aura` handler reads in a classic game.

## Context

- Research-map row `monsters/stats`: `not started`. Its dependencies:
  - `monsters/pool` reviewed (C 75 / I 31 / L 5);
  - `monsters/special` reviewed (C 102 / I 85 / L 7).
- Downstream, waiting on this row: `hirelings`, and the TC player-count model, which already uses the player count
  but not its effect on life.
- Code already named:
  - `sub_00574250_MonsterInit` → `sub_00573CB0_MonStatsInit` (level, `[C]`);
  - `sub_006538A0_MonLvlStats` (`[I]`, a reader only);
  - the 40-odd MonUMod handlers of [monsters/0003](../findings/monsters/0003-special-monsters.md) § 5 (`hpmultiply`,
    `leveladd`, `champion`, `fanatic`, `berserk`, ...), whose effects special.md names but does not specify.
- Open items this plan absorbs:
  - [special.md *Open questions*](../specs/monsters/special.md): the classic `aura` level;
  - the backlog entry on `sub_005A1650_UModAura`'s guards (spec-writer → reverser, 2026-10-14).
- Data:
  - [MonStats](../tables/MonStats.md) gives `minHP`/`maxHP`, `AC`, `Exp`, the damage, to-hit and resistance columns
    per difficulty;
  - [MonLvl](../tables/MonLvl.md) gives the per-level base values, classic and `L-` expansion;
  - [MonUMod](../tables/MonUMod.md) gives the mod parameters;
  - `DifficultyLevels` (3 rows) and `MonProp` (13 rows) have no table doc.
- Harness: monster logging exists (`tools/gdb/mon-special.gdb`, the MON lines of `tools/d2pilot.py`). Stats are
  readable from the unit's stat list, so one session yields hundreds of samples without killing anything.
- Leads: `src:d2dfg-blizzard` (§ MonStats.txt, § MonLvl.txt, § MonProp.txt, § DifficultyLevels.txt). Monster HP and
  player-count scaling are widely documented, so Phase 1b is required.

## Phases

### Phase 0 — MonProp and DifficultyLevels
- **Owner skill:** archivist
- **What:** document `MonProp` and `DifficultyLevels` with their `.bin` layouts, and complete the stat-column
  semantics in MonStats and MonLvl as far as the data shows them.
- **Outputs:**
  - `docs/tables/MonProp.md` and `docs/tables/DifficultyLevels.md`;
  - updates to MonStats.md and MonLvl.md: per-difficulty column groups, blank patterns, and which classes are
    `[I]` boss/npc rows;
  - `tools/excel_layouts.py` entries and a regenerated `excel_layout` baseline;
  - a survey command (`tools/mon_survey.py stats <class> <difficulty>`) that prints every stat-relevant cell of a
    class for one difficulty, beside the MonLvl row for its level.
- **Done when:** `excel_bin.py diff` passes on both new tables, and the survey runs for every MonStats row. Meanings
  stay `[L]`.

### Phase 1 — Read the stat realisation
- **Owner skill:** reverser
- **What:** read how `MonsterInit` (after `MonStatsInit`) fills the monster's stat list, how difficulty, the player
  count and `MonProp` change it, and what each MonUMod handler does to the stats.
- **Outputs:**
  - `docs/findings/monsters/0004-stats.md`;
  - `re/symbols.csv` rows (subsystem `monsters/stats`, naming the readers it settles);
  - `re/types/` additions.
- **Done when:** the finding states, with addresses and `[I]` or better:
  - **hit points:** the `minHP`..`maxHP` draw (seed, range) and the scaling by the MonLvl `HP` value, with the exact
    integer arithmetic and rounding. The player-count factor, and when it is applied (at spawn, or on a later
    player-count change).
  - **defence, to-hit, damage and experience:** the same for each (draws, if any; MonLvl scaling; the difficulty
    tables).
  - **resistances and immunities:** the per-difficulty columns and the hell adjustments, if any.
  - **MonProp:** when a row applies (by class and difficulty), its chance draws, and the properties it adds.
  - **mods:** per MonUMod handler, the stat it changes and the arithmetic (`hpmultiply`, `champion`, `leveladd`,
    `extra strong`, the enchantments' resistance and damage additions), and the `aura` handler's level in classic
    and expansion.
  - **order:** the draws on the unit seed, relative to the special-mod draws of monsters/special.
  - **the boundary decision** for Phase 2: skills, AI and aura stat effects are oracles or out of scope. Recommend
    one; the architect rules at the review.

### Phase 1b — Community cross-check
- **Owner skill:** reverser
- **What:** fetch `src:d2dfg-blizzard` (§ MonStats.txt, § MonLvl.txt, § MonProp.txt, § DifficultyLevels.txt).
  Search for and register community documents on monster HP, player-count scaling and champion/unique stat
  bonuses. Compare blind. Downloads go to the scratchpad only.
- **Outputs:** `docs/sources.md` entries or a "none found" note; verdicts in the finding's *Leads used*.
- **Done when:** every claim about the HP draw, the scalings, the player count, MonProp and the mod effects carries a
  verdict. Every `contradicted` claim is a required case of Phase 2.

### Phase 2 — Bit-exact reproduction
- **Owner skill:** reverser (agent-driven per [harness-play](../../.claude/skills/reverser/references/harness-play.md))
- **What:** write `tools/monstats.py`, chained after `tools/monspawn.py` and `tools/monspecial.py`. Log a new run and
  rerun the plan 0018 logs if they hold the stat lists.
- **Logging:** at the end of monster init, each monster's class, level, difficulty, player count, mods, the stat
  list (HP, max HP, AC, to-hit, damage, resistances, experience) and the unit seed before and after.
- **Done when:** a run `run:YYYY-MM-DD-mon-stats` shows, with 0 mismatches against the model:
  - at least 500 monsters over the three difficulties, classic and expansion, and at least three player counts
    (1, 3 and 8), including at least one count change during a session if the code rescales live monsters;
  - champions, uniques and superuniques with every stat-changing mod the run meets (each mod not met is named);
  - at least one MonProp row applied in each difficulty where one exists;
  - a classic `aura` unique, which settles the level question;
  - the Phase 1b cases.

  In-scope claims go to `[C]`.

### Phase 3 — Spec: monsters/stats
- **Owner skill:** spec-writer
- **What:**
  - write `docs/specs/monsters/stats.md` and link it from the monsters README;
  - replace the "effect: see monsters/stats" notes and the aura-level open question in special.md with links.
- **Done when:**
  - the spec follows the template, and every statement is tagged;
  - it gives each stat's arithmetic as an ordered computation, the player-count rule and the per-mod effects table;
  - it has worked examples from the run (a normal monster, a champion and a unique, in hell at `/players 8`);
  - the architect's review passes.

## Open questions

- What auras and skills do in combat is out of scope. Only the stats a monster is created with, and any rescale on a
  player-count change, are in scope.
- Hireling stats reuse MonStats rows through Hireling.txt (`hirelings`, later).

## Implementation log

- 2026-10-14 (architect): drafted and approved on the owner's request. Phase 0 (archivist) may start.
- 2026-10-14 (archivist): Phase 0 done on `lane/a0025p0`.
  - New table docs [MonProp](../tables/MonProp.md) and [DifficultyLevels](../tables/DifficultyLevels.md); layouts `monprop`
    (312 B) and `difficultylevels` (88 B) in `tools/excel_layouts.py`. `excel_bin.py diff`: monprop 13 × 91 = 1 183 cells,
    difficultylevels 3 × 22 = 66 cells, 0 mismatches each. `excel_layout` baseline regenerated (43 tables, 654 404 cells,
    0 unexplained).
  - [MonStats § Stat columns](../tables/MonStats.md#stat-columns-plan-0025-phase-0): per-difficulty groups (`base + w·d`),
    blank patterns per group and difficulty, the 114 records with no core stats and the 91 with some, the
    boss/primeevil/npc rows, value checks. [MonLvl § Stat survey](../tables/MonLvl.md#stat-survey-plan-0025-phase-0): no
    blanks, monotonic columns, levels reached.
  - `tools/mon_survey.py stats <excel-dir> <class|record|all> <difficulty|all> [--print]`; `all all` formats all 734
    records × 3 difficulties (2 202 blocks, no error). Registered as gate survey `mon_stats` with a baseline; the
    `mon_collision` output is unchanged.
  - Surprises: (1) MonProp `par` and `chance` are blank in every row, so their slots are a choice (`[L]`), and if
    `chance` were a plain percentage no MonProp slot would ever apply. (2) The `irongolem` MonProp row is named by no
    MonStats record. (3) DifficultyLevels is not in `.txt` order (`UltraCodeOdds*` after the divisors) and has three
    groups of equal columns. (4) Data oddities: `minionspawner1` `minHP` > `maxHP`, `andariel`'s `El1MinD(N)` >
    `El1MaxD(N)`, `wakeofdestruction` `El1` values with no type. Questions in the backlog (archivist → reverser).
    Meanings stay `[L]`.
- 2026-10-14 (architect): Phase 0 accepted. Rulings: (1) the MonProp `{prop, par, min, max}` + tail `chance` layout stays `[L]` until Phase 1 reads the loader descriptor (call site `0x006594B3`); (2) the all-blank `chance` cells are a required Phase 1 item: how a MonProp slot is applied with `chance` 0; (3) the order inside DifficultyLevels' equal-value groups stays `[I]`, settled by its readers in Phase 1; (4) the `mon_stats` gate survey is kept, since it guards the counts the table docs quote; (5) the reversed or blank MonStats ranges (`minionspawner1`, `mephistospirit`, `andariel`, `wakeofdestruction`) are required Phase 2 cases if a run meets those classes.
- 2026-10-14 (reverser): Phase 1 and 1b done on `lane/r0025p1`, static only:
  [monsters/0004](../findings/monsters/0004-stats.md), `re/types/monstats.h`, 27 `re/symbols.csv` rows (`monsters/stats`).
  - Rulings answered: the MonProp descriptor (call `0x006594B3`) gives layout (a) `[C]`; a `chance` 0 slot applies with no draw,
    `chance` > 0 makes one unit-seed step (`low % 100 < chance`); the DifficultyLevels descriptor gives the `.txt` order in the
    three equal groups `[C]`, record index = difficulty.
  - HP: `lo + RangeB(hi − lo + 1)` over MonLvl × MonStats / 100 (raw for `noRatio`), then `+ (n − 1)·50 %` for the player count,
    once at creation (no rescale); AC and XP likewise (XP with the same player %); to-hit and damage are attack-time. Classic
    nightmare/hell: HP × 1/2, AC × 10/12, XP × 10/17 or 10/26, level stat = `Level` + 25·d, which answers the classic aura level
    (`Level + 25·d + 3`). Per-handler stat effects with their `constants` rows.
  - Phase 1b: `src:d2dfg-blizzard`, `src:arreat-summit-bonuses`, `src:arreat-summit-monster-pages` re-read, `src:maxroll-player-settings`
    new. Four `contradicted`: `L-` MonLvl columns in single player, Spectral Hit + 20 (not + 40), a berserker's level + 3,
    `UniqueDamageBonus` unread. Phase 2 boundary recommended in § 10. Review requested (backlog reverser → architect).
