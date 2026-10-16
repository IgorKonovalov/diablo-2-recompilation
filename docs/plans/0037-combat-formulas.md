# 0037 — Combat formulas: to-hit, damage, resistances, defences and on-hit effects

> **Status:** in-progress (P0 accepted 2026-10-16)
> **Created:** 2026-10-16
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0007-fetched-leads-only, 0011-harness-slots, 0013-forced-path-runs-cell-level, 0014-scope-game-simulation

## TL;DR

**Question:** when one unit attacks another, how does the game decide whether the attack hits, how much damage of
each type it does, how the defender's resistances, block, avoidance, damage reduction and absorb change that, and what
the on-hit effects do (crushing blow, deadly strike, open wounds, life and mana leech, cold and freeze, poison)? This
covers player against monster and monster against player, in every difficulty and in classic and expansion games.
It is the first simulation plan under [ADR-0014](../adrs/0014-scope-game-simulation.md), phase (1).

When it is done:
- the combat columns of the tables are documented, and the element and mode code lists have table docs;
- `docs/findings/combat/0001-formulas.md` states each formula, its draws and seeds, its inputs and its outputs;
- `tools/combat.py` reproduces logged attack events bit for bit under ADR-0014's per-event rule, with stat values as
  value oracles and a skill's damage packet as an input;
- `docs/specs/combat/` is drafted and reviewed; [monsters/stats § H](../specs/monsters/stats.md#h-to-hit-and-damage-at-attack-time-reference-only)
  moves from reference to `[C]` where the run reaches it, and the `ToHitFactor` contradiction is settled.

The boundary: a unit's **final stats** are inputs here (phase (2), stats and states, models how they add up), and a
**skill's damage packet** is an input (phase (3), skills and missiles, models how a skill builds it). This plan
covers a normal attack's own damage build, the to-hit roll, everything the defender applies, and the on-hit effects.

## Context

- Research map: new band **Simulation (ADR-0014)**, row `combat/formulas`, `not started`. Dependencies, all
  `reviewed`: [monsters/stats](../specs/monsters/stats.md) (C 99; creation stats, the attack-time § H as reference
  `[I]`), [player/creation](../specs/player/creation.md) (base stats, the attack rating term), [items/properties](../specs/items/properties.md)
  (base damage, defence, the property writers), [data/calc](../specs/data/calc.md) (the evaluator for `ToHitCalc` and
  the skill damage formulas), `rng` and `rng/seeds` (the unit seed).
- **Code already named** (grep `re/symbols.csv`):
  - `sub_005A4F50_MonAttackStats` (I) and `sub_005A4F20_PlayerDmgBonus` (I), `data:g_PlayerDmgBonus`: a monster's to-hit,
    damage and elemental damage at attack time, with `El<e>` draws on the **attacker's unit seed**
    ([monsters/0004 § 9](../findings/monsters/0004-stats.md#9-to-hit-and-damage-at-attack-time-sub_005a4f50_monattackstats));
  - `sub_006538A0_MonLvlStats` (C), `sub_00611D30_DifficultyRec` (I), `g_pDifficultyLevels` (C);
  - `sub_00622560_PlayerBaseToHit` (I): `(dex − 7) × 5 + stat 19 + ToHitFactor`; `0x00583740` (unnamed) adds
    `ToHitFactor` once more to a computed rating ([player/0001 § 9–10](../findings/player/0001-creation.md#9-other-charstats-readers-for-the-archivists-table-doc));
  - `sub_00622720_UnitBlockChance` (I): `toblock + BlockFactor`, the dexterity form, capped at 75;
  - `SKILLS_GetToHit` (I, data/calc), `sub_00625500_UnitGetStat` (I), the stat-list functions (`STATLIST_*`,
    `sub_00624F60_StatListGetValue`), `UNIT_SetMode` (C), `sub_005A7C20_MonSetMode` (I: the death set-mode where the
    drop runs, items/0010);
  - the mod handlers that change combat stats at creation: `sub_005A1370_UModResist` (C), `sub_005A1F90_UModManaHit`
    (C), `sub_005A1E00_UModPoisonHit` (I), `sub_005A21D0_UModElemDamage` (I), `sub_005A0D20_MonHpAddPct` (C).
- **Contradiction waiting for this plan**: backlog 2026-10-15 "ToHitFactor": src:arreat-summit-character-basics calls
  the class constants (20/15/5/−10/−15) a bonus to the attacker's level in the chance-to-hit formula; 1.14d adds
  `ToHitFactor` to the attack rating ([player/0001 § 10](../findings/player/0001-creation.md#10-community-cross-check-phase-1b)).
  The block formula's 25 % cap while running is `not covered` there too.
- Open notes from earlier plans: monsters/stats *Open questions* (the noRatio elemental damage written to
  `+0x24`/`+0x28` and read at `+0x2C`/`+0x30` by the attack code, "for a later `monsters/combat` row"); the DifficultyLevels
  columns with no reader yet (`ResistPenalty`, the freeze, cold and curse divisors, `LifeStealDivisor`,
  `ManaStealDivisor`, [DifficultyLevels § Open questions](../tables/DifficultyLevels.md#open-questions)).
- **Data already documented** (no Phase 0 work unless named below): [CharStats](../tables/CharStats.md) (`ToHitFactor`,
  `BlockFactor` with readers), [MonLvl](../tables/MonLvl.md) (TH, DM, AC per level), [MonProp](../tables/MonProp.md),
  [MonUMod](../tables/MonUMod.md), [Skills](../tables/Skills.md) (layout `[C]`, including `ToHit`, `LevToHit`,
  `ToHitCalc`, `SrcDam`, `HitShift`, `MinDam`, `EType`, `EMin`), [SkillCalc](../tables/SkillCalc.md),
  [MissCalc](../tables/MissCalc.md), [Hireling](../tables/Hireling.md) (`AR`).
- Leads already registered: `src:arreat-summit-character-basics`, `src:arreat-summit-bonuses`,
  `src:arreat-summit-monster-pages`, `src:d2dfg-blizzard`, `src:pk-monstats-guide`, `src:pk-monumod-guide`,
  `src:fandom-d2-elite-monsters`. Combat is heavily documented, so Phase 1b searches for and registers more
  (ADR-0014 § Sources).
- Harness: the Nova sorceress build of [harness-play](../../.claude/skills/reverser/references/harness-play.md) kills
  through all three difficulties; melee "with a low-level character fails in Nightmare and Hell", so the melee and
  defence characters are tool-built at a high level with stock items (ADR-0013 § Neutral: tool-built saves on stock
  tables are not forced-path runs).

## Phases

### Phase 0 — Combat columns and code lists
- **Owner skill:** archivist
- **What:** document the table columns the combat code is expected to read, where the existing docs stop short, and
  add the code-list tables combat indexes.
- **Outputs:**
  - new table docs `docs/tables/ElemTypes.md` (`elemtypes.txt`/`.bin`: the element codes that Skills `EType` and
    the monster `El` groups name), `MonMode.md` and `PlrMode.md` (the mode codes that select a monster's `A1`/`A2`/`S1`
    damage columns and the attack modes); `HitClass` waits for the animation phase (ADR-0014 phase 5);
  - [MonStats](../tables/MonStats.md) § Combat columns: the per-mode damage and to-hit columns, the three `El`
    groups (mode, type, percent, min, max, duration), `Drain`, `coldeffect`, `DamageRegen`, `ToBlock`, `NoRatio` and any
    other column the survey ties to an attack, per difficulty, with blank patterns; extend § Stat columns rather than
    duplicate it;
  - [MonStats2](../tables/MonStats2.md) § Combat columns: the per-mode availability flags and any melee-range or
    hit-class column;
  - [DifficultyLevels](../tables/DifficultyLevels.md) § Combat columns: `ResistPenalty`, `MonsterFreezeDivisor`,
    `MonsterColdDivisor`, `AiCurseDivisor`, `LifeStealDivisor`, `ManaStealDivisor`, the damage-percent columns and
    `StaticFieldMin`, with their values per row;
  - [ItemStatCost](../tables/ItemStatCost.md) § Combat stats: a table of the stat ids a combat formula is expected to
    read (attack rating and its percent, defence, the damage group and enhanced damage, each element's min, max and
    length, each resistance and its maximum, damage reduction and magic damage reduction flat and percent, absorb,
    block, crushing blow, deadly strike, open wounds, life and mana leech, pierce and the enemy-resistance stats), each
    with `ValShift`, `Save Bits`, signedness and the `.bin` offsets, from data only;
  - [Weapons](../tables/Weapons.md) and [Armor](../tables/Armor.md) § Combat columns: the one-hand, two-hand and
    missile damage columns, `StrBonus`, `DexBonus`, `speed`, the range column; `block` and the shield and boot damage
    columns;
  - [States](../tables/States.md): the rows the on-hit effects are expected to set (cold, freeze, poison, open wounds),
    by row id; [Skills](../tables/Skills.md): a survey of which rows carry each damage-feeding column, and the row of
    the normal attack;
  - `tools/combat_survey.py` (gate survey `combat`), printing the counts the docs state; the `excel_layout` baseline
    regenerated if a new table is parsed.
- **Done when:** each new table doc has its layout `[C]` by `excel_bin.py diff` against the `.txt` and its row count
  equal to the `.txt` data rows; each named section lists every column it claims with offset, width and value range;
  `python3 -I tools/combat_survey.py` runs and its `SURVEY` line matches the docs; meanings stay `[L]` unless an
  earlier finding already anchors them; the gate is green.

### Phase 1 — Read the combat code
- **Owner skill:** reverser
- **What:** find and read the server's attack resolution from the attack event to the defender's life change, and
  every formula on that path.
- **Entry points to find and name** (subsystem `combat/formulas`):
  - the **attack event**: where the server resolves one attack (a normal attack and a skill hit) against one target,
    and the **damage packet** it carries (recover its struct into `re/types/combat.h`); the caller of
    `sub_005A4F50_MonAttackStats` gives the monster side;
  - the **to-hit roll**: the chance-to-hit formula (attacker rating, defender defence, the levels, the clamp), its
    draw and seed; where `ToHitFactor` enters (`sub_00622560_PlayerBaseToHit`, `0x00583740`), and which caller uses
    each; the skill bonus through `SKILLS_GetToHit`;
  - the **attacker's damage build** for a normal attack: weapon damage, enhanced damage, the `StrBonus`/`DexBonus`
    share, two-handed and thrown cases, `SrcDam` and `HitShift` as a skill applies them to weapon damage; the
    monster's from `MonAttackStats` and the noRatio placement;
  - the **defender's side**, in its exact order: block (`sub_00622720_UnitBlockChance`, the running case, the
    caller's flag), avoidance, evade and dodge as they appear at the hit (their chances are inputs), resistances with
    `ResistPenalty` and the maximum-resistance cap, immunity and pierce, absorb, damage reduction and magic damage
    reduction, each flat and percent, and the minimum damage floor if any;
  - the **on-hit effects**: crushing blow (player and monster targets, bosses, the difficulty and classic branches),
    deadly strike, open wounds (the state and its per-frame bleed), life and mana leech with the difficulty divisors and
    monster `Drain`, cold and freeze durations with `MonsterColdDivisor`, `MonsterFreezeDivisor` and `coldeffect`,
    poison length and per-frame damage, monster `DamageRegen`;
  - the **life change**: the write to stat 6 (×256), and the hand-off to the death path (`sub_005A7C20_MonSetMode`) and
    to hit recovery (named only; animation timing is phase (5));
  - **difficulty and game-type branches**: classic against expansion, `/players` scaling, the hireling and
    hireable-boss damage percents, player against player (named only, ADR-0014 § Multiplayer).
- **Outputs:** `docs/findings/combat/0001-formulas.md`; `docs/findings/combat/experiments.md` (empty heading for
  Phase 2); `re/symbols.csv` rows (subsystem `combat/formulas`); `re/types/combat.h`; the noRatio and DifficultyLevels
  questions answered in their table docs' backlog entries to the archivist.
- **Done when:** the finding states, each with addresses and `[I]` or better:
  - every entry point above named in `re/symbols.csv`, or recorded as not present in 1.14d with the evidence;
  - each formula with its integer widths, signedness, rounding, clamps and order of application;
  - for each event kind: the **draws** in order with their ranges and the **seed** each draws on (attacker's unit seed,
    defender's unit seed, or the game seed), the **inputs** (each stat id the formula reads, by accessor, for
    ADR-0014's value oracles), and the **outputs**;
  - which events can follow each other on one seed with no out-of-scope draw between (so Phase 2 can chain them), and
    which must be resynchronised;
  - the server path told apart from any client-side copy (ADR-0014 § Time);
  - the ToHitFactor question settled statically, or made a named Phase 2 case;
  - **the boundary recommendation** for Phase 2: the event entry points, the value oracles, the skill damage packets
    taken as inputs, and the breakpoint sites with the per-event read list. The architect rules at the review.

### Phase 1b — Community cross-check
- **Owner skill:** reverser
- **What:** fetch the registered leads and search for and register combat documentation (chance to hit, block, the
  resistance caps and penalties, crushing blow, deadly strike, open wounds, leech, damage reduction order, the classic
  and player-count branches); compare blind, after Phase 1's claims are written.
- **Outputs:** `docs/sources.md` entries, each with the game version it describes; verdicts in the finding's *Leads
  used*.
- **Done when:** each compared claim carries one verdict; the ToHitFactor backlog entry carries the Phase 1 reading;
  every `contradicted` claim reachable on stock data is a required case of Phase 2, and each other one has a backlog
  entry. A calculator is used only through its prose (ADR-0014 § Sources).

### Phase 2 — Per-event reproduction
- **Owner skill:** reverser (agent-driven per [harness-play](../../.claude/skills/reverser/references/harness-play.md);
  at most two slots, given in the prompt; owner play is the fallback for a fight scripted play can't win)
- **What:** write `tools/combat.py` (model and `check`), `tools/gdb/combat.gdb` and its Python handler, the recipes
  for the test characters, and log a run.
- **Characters** (tool-built from recipes with stock items, ADR-0013 § Neutral; no table is edited, so no forced-path
  run is planned; if Phase 1 finds a branch that only an edited table reaches, it is ruled cell by cell under ADR-0013
  at the Phase 1 review):
  - a **melee** character at a level that hits in Hell, with stock items that carry crushing blow, deadly strike, open
    wounds, life and mana leech, enhanced damage and attack rating;
  - the **Nova** sorceress, for skill damage packets (inputs) through the defender's resistances, immunities included;
  - a **defender**: a shield, resistances below, at and above the cap (with maximum-resistance items), damage
    reduction, magic damage reduction and absorb, standing in monster packs with elemental attacks, champions and
    uniques;
  - a **classic** character for the classic branches; `/players 8` sessions for the player-count bonus.
- **Logging** (ADR-0014 § Log volume): one line set per event at the Phase 1 entry points, filtered to events involving
  the logged character or its target; each event's inputs from the Phase 1 read list, the seeds on entry and on exit,
  the outputs, and the frame number for timed effects; per-kind caps stated in the record; no breakpoint on a per-frame
  path outside a stated window; a manifest with the logs' hashes.
- **Done when:** `run:YYYY-MM-DD-combat` reproduces with **0 mismatches** under `python3 -I tools/combat.py check`, which
  asserts every exit seed and every output and reports chained and resynchronised events per kind, over at least:
  - **chaining (ADR-0014):** for every event kind, at least 20 chained pairs (consecutive events of that kind on one
    seed, the second's entry seed asserted against the first's predicted exit), reported per kind by the checker; a
    kind with no chained pair keeps its draw-order claims at `[I]`;
  - 2 000 player-against-monster attack events, at least 300 in each difficulty, with at least 300 hits and 300
    misses;
  - 1 000 monster-against-player attack events, at least 200 in each difficulty, with at least 100 blocks and, if
    Phase 1 places them in the event, 30 avoid, evade or dodge outcomes;
  - per element (fire, cold, lightning, poison, magic): 200 resistance applications, with at least 30 at or above the
    defender's cap and 30 against an immune monster;
  - 30 crushing blows, 30 deadly strikes, 30 open-wound applications with their bleed ticks and duration checked in
    frames, 200 leech events in each difficulty, 100 events with damage reduction, magic damage reduction or absorb
    non-zero;
  - 100 monster `El` attacks and 100 champion or unique attacks, reproducing `sub_005A4F50_MonAttackStats` (monsters/stats
    § H moves to `[C]`);
  - 200 events in a classic Nightmare or Hell game, and the player-count bonus in sessions with at least 2 and 8 players;
  - the ToHitFactor case and every Phase 1b contradiction reachable on stock data.

  The rare-branch minimums (avoid and evade, at cap and immune per element, crushing blow, deadly strike, open wounds,
  and any similar rare case Phase 1 names, about 30 each) may fall short: the run record then names each shortfall with
  its count, it does not block the phase, and the claims of that branch stay `[I]`. The main counts and the
  per-difficulty splits are required.

  In-scope claims go to `[C]`, citing the run; each `[C]` names its value oracles and input packets (ADR-0014).

### Phase 3 — Spec: combat/formulas
- **Owner skill:** spec-writer
- **What:** write `docs/specs/combat/README.md` (overview, the event entry points, the data flow, the ADR-0014
  boundary) and one or more algorithm files (for example to-hit, damage, defences, on-hit effects); update
  [monsters/stats § H](../specs/monsters/stats.md#h-to-hit-and-damage-at-attack-time-reference-only) and its
  *Open questions*, [player/creation](../specs/player/creation.md) (the attack rating term), and the
  [data/calc](../specs/data/calc.md) open question on what `ToHitCalc` feeds.
- **Done when:** the spec follows the template and every statement is tagged; it gives each event's draw order on its
  seed as a Mermaid sequence with the same facts tagged in the text; it states the order of the defender's reductions,
  every clamp and cap, and the classic and difficulty branches; it has worked examples from the run (a melee hit with
  crushing blow and leech, a monster hit blocked and one resisted in each difficulty); its *Open questions* list the
  inputs owed to phases (2) and (3); the architect's review passes.

## Open questions

- Stat aggregation (how items, skills, auras and states add up to the values this plan takes as inputs) is phase (2)
  of ADR-0014. The input identities stay `[I]` until that plan consumes them.
- A skill's own damage packet (Nova's lightning, a synergy) is phase (3); here it is an input.
- Hit recovery, knockback and stun lengths are animation timing (phase (5)); this plan names the hand-off only.
- Player against player and hostile auras need two clients; they stay `[I]` while ADR-0008 is proposed.
- Mercenary and minion attacks probably share the monster path; Phase 1 says whether, and a mercenary case is added to
  Phase 2 only if they differ.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-16 — Drafted and approved (architect).** Written with ADR-0014 in the architect worktree `lane/p37`. The
  owner set the order: plan 0032 (Phase 2 running) and its spec, then plan 0036, then this plan.
- **2026-10-16 — Owner decisions (architect).** Chaining is required for every event kind (ADR-0014 Decision); Phase 2
  asks for at least 20 chained pairs per kind. The rare-branch minimums are lowered to about 30, and a shortfall is
  named instead of blocking, with that branch's claims kept at `[I]`. MonMode and PlrMode stay in Phase 0; `HitClass`
  moves to the animation phase. ADR-0008 stays open.
- **2026-10-16 — Phase 0 landed (archivist, `lane/a37p0`).** New table docs [ElemTypes](../tables/ElemTypes.md),
  [MonMode](../tables/MonMode.md) and [PlrMode](../tables/PlrMode.md): layouts `[C]` by `excel_bin.py diff` (13, 32, 40
  cells, 0 mismatches; 13, 16, 20 records = the `.txt` data rows; every byte placed). Combat sections in MonStats,
  MonStats2, DifficultyLevels, ItemStatCost (104 stats by name), Weapons, Armor, States (11 rows by name) and Skills,
  each column with offset, width and range. `tools/combat_survey.py` (gate survey `combat`); the `excel_layout`
  baseline regenerated (66 tables). Surprises: the MonMode and PlrMode records hold the animation **token**, not the
  `Code` other tables resolve by (`knockback`, `Sequence`, `Knock back` store `GH`); the PlrMode mixed-archive pair
  agrees (the patch `.txt` only adds `Code`); **no MonStats record with `S1` damage has the `S1` mode** (all 29 are
  `seq_*` sequence monsters), and 27 `El1` groups name a mode their MonStats2 row lacks. Meanings stay `[L]`; questions
  for Phase 1 in the [backlog](../backlog.md).
- **2026-10-16 — Phase 0 review (architect): accept with fixes.** Re-ran `excel_bin.py diff` for `elemtypes`,
  `monmode`, `plrmode` (13, 32, 40 cells, 0 mismatches; 13, 16, 20 records = the `.txt` data rows) and
  `combat_survey.py summary` (equal to the new baseline); `gate.py` fast tier and `--full combat,excel_layout` green;
  `test_d2s` (43) and `test_gate` (22) pass; the table-doc sha256 values match the files. Every `[I]` cites a finding
  that says it (monsters/0004 § 4 and § 9, monsters/0003 for `MonModeAllowed`, data/0001 § 3–4, items/0006, save/0001);
  every `fn:` anchor resolves in `re/symbols.csv`; meanings stay `[L]`; no provenance. The ItemStatCost § Combat stats
  table (104 of 359 rows, 7 storage columns) is the plan's own requested index, not a dump: kept, and Phase 1 should
  trim it to the stats the code reads rather than grow it. The backlog questions to the reverser are well formed
  (each names records, columns and the function to read). Fixes applied: the `damagerelated` sentence in ItemStatCost
  named whole groups that hold `damagerelated` 0 stats (`item_kickdamage`, `firelength`, `burningmin`, `burningmax`);
  plan status, plans index and research-map note updated. Merge: only `docs/backlog.md` conflicts with `main` (both
  sides append at the end); keep both sides.
