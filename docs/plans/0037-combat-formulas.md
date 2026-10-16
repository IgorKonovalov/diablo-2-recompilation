# 0037 — Combat formulas: to-hit, damage, resistances, defences and on-hit effects

> **Status:** in-progress (P0 accepted 2026-10-16; P1/1b accepted with fixes 2026-10-16; P2 accepted with fixes 2026-10-16; P3 accepted with fixes 2026-10-16; P2 shortfall resume and the spec re-tag next)
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

### Phase 4 — Wiki page: combat (added 2026-10-16, plan 0038 Phase 3 wiki review)
- **Owner skill:** spec-writer
- **What:** write `docs/wiki/combat.md` under ADR-0012 from the reviewed combat spec as it stands after the re-tag
  that follows the resume lane: one attack end to end (to-hit, damage, the defender's reductions in order, the on-hit
  effects and leech), player against monster and monster against player, the difficulty and classic branches, with
  the spec's worked examples; a *What is not known yet* section that keeps every `[I]` and open question of the
  combat spec in words (the under-floor branches, the value-oracle compositions, the ADR-0014 hand-offs). Add it to
  the wiki index's reading order and replace the index's "no page yet" paragraph.
- **Done when:** the page's `based_on:` lists the combat spec files at their `updated:` dates; every section links the
  spec section it explains; the gate is green with no W4 on it; the architect's review passes. Plan 0041's P3 then
  keeps the page in step (ADR-0012), since it changes the combat spec's input list.

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
- **2026-10-16 — Phases 1 and 1b landed (reverser, `lane/r37p1`).** [combat/0001](../findings/combat/0001-formulas.md): the server path is `.\UNIT\SUnitDmg.cpp` (`0x0057A830`–`0x0057EFFF`) plus the stat-event handlers; attack events, to-hit (`ToHitFactor` an AR term, settled statically), block/evade/dodge/avoid on the defender's seed, the builder (including an unconditional `RangeB(seed, 1)` and the player builder running on a miss), the 12-row reduction table, delivery, leech, cold/freeze/poison/stun, crushing blow, open wounds, draws per event and the chaining plan; all `[I]` (no emulation, no run). 77 symbols, `re/types/combat.h`. 1b: 7 sources, 30 verdicts, 5 contradicted (four behaviours, all Phase 2 required cases). Surprises: `HireableBossDamagePercent` has a reader; absorb heals from both % and flat absorb; a mercenary case is needed (its branches differ). Archivist questions (a)–(e) answered in § 12b.
- **2026-10-16 — Phases 1 and 1b review (architect): accept with fixes.** Every Done-when item is met: the entry points
  are named (77 rows, no duplicate address or name), each formula has widths, signs, rounding and order, § 11 gives
  draws and seeds per event kind with the chaining reading, the client AR copy is told apart, the `ToHitFactor` backlog
  entry carries the Phase 1 reading, 30 claims carry one verdict each and the five `contradicted` (four behaviours) are
  required cases below. The seven new sources are prose pages, registered with the version they describe; nothing reads
  as transliterated code (names are ours or from the binary's own `SUnitDmg.cpp` path). All tags `[I]`, honestly.
  Gate fast tier green. **Spot checks** (objdump/r2 on the pinned image, sha256 matches the inventory): the to-hit
  percent, the level factor and the 5..95 clamp at `0x0057DB01`–`0x0057DB30` and the negative AR/DEF swap above them;
  `edi` = `c` at `0x0057DB35` and `esi` = `r` at `0x0057DB61`; `call RNG_RangeB` with `EDX` = 1 on attacker `+0x20`
  at `0x0057BC47`, outside any branch, and the burn `max(0, ·)/128`; `0x0057C0FE` reading `+0x38` of the context's
  `+0x04`, which `0x0057C1F9` fills with `DifficultyRec`'s result; `g_DamageResistTable` (12 × 11 dwords, every stat,
  slot and flag as tabled); crushing blow 10 (player, hireling) / 4 / 8 (boss flag or type `0x02`), `MulDiv` by
  `PlayerHpPct(max(stat 100, 1))` for non-hirelings, `×2` on event 6, physical resist capped 100 and only when > 0;
  `SKILL_AttackDo` calling `COMBAT_BuildDamage` after the hit test whatever its result. All seven hold.
  **Fixes applied:** the `HireableBossDamagePercent` correction note in [monsters/0004](../findings/monsters/0004-stats.md#1-the-two-loader-descriptors)
  § 1 and its *Open questions* (the earlier full xref named `0x0057C060` as not reading the member; it does); backlog
  entries to the spec-writer (monsters/stats G7) and to the reverser (the leftovers in ruling 3); the archivist's
  DifficultyLevels change is already filed ("combat table readers" (a)). **Rulings.** (1) Accept; the finding stays
  `open` until Phase 2. (2) `HireableBossDamagePercent` is a Phase 2 required case: a mercenary hitting an act boss in
  each difficulty (50/35/25, which Hell tells from `MonsterCEDamagePercent` 20). (3) Gaps to close statically before
  the logs (backlog, reverser): `0x005D3AC0`/`0x005D3BA0` around the builder and `0x005D5220` before delivery (state
  hooks over states with stat 350), the state-38 branch to `0x0056C2D0`, the state-expiry path and the stat-74 tick.
  Until (3) is read, the checker drops events where either unit has a state carrying stat 350 or state 38, and names
  the count. (4) The mercenary case is added (its branches differ, § 2): 100 mercenary attack events, 30 against act
  bosses. (5) **Chaining.** Chains are counted per seed role. The player's seed: any two consecutive in-scope events on
  it (player attack, monster attack's defence part, missile defence, cold shatter on the player) chain, mixed kinds
  included, and each kind needs 20 pairs where it is the first and 20 where it is the second. The monster's seed is
  drawn by its AI between attacks, so the monster attack's own draws chain only from `MonAttackStats` at the mode change
  to `MON_MeleeHit` at the hit frame of the same attack; if that link reaches fewer than 20 pairs, the shortfall is
  named, the monster-seed draw-order claims stay `[I]` (ADR-0014) and the phase is not blocked. This is a plan-level
  reading of ADR-0014's "consecutive events of that kind" (both ends of each kind are checked); the owner may veto it.
  (6) **Log caps per session** (ADR-0014 § Log volume): player attack 800, monster attack 500, `MonAttackStats` 300,
  missile defence 300; the effects inside a logged attack are not capped; the only windowed breakpoint is the stat-74
  tick, ≤ 250 frames after an open-wounds or poison application, at most 30 windows per session; stats are read only
  from the per-kind lists of the brief.
  **Phase 2 brief.** *Events and logger points:* player attack = `SKILL_AttackDo` entry/return; monster attack =
  `MON_MeleeHit` entry to `COMBAT_DeliverQueued` return, with `MonAttackStats` at the mode change as its own boundary;
  missile hit = `MISSILE_ApplyDamage` entry/return (packet as input); inside: `COMBAT_ToHitRoll` (`c`, `r`; or the stub
  call at `0x0057DB72`), `COMBAT_DefenceRoll` and `COMBAT_AvoidRoll` returns, `COMBAT_BuildDamage` and
  `COMBAT_ApplyReductions` entry/return (packet), `COMBAT_ApplyDamage` entry/return, the handlers `0x005BFFC0`,
  `0x005BFE60`, `0x005BFC60`, `COMBAT_Leech`, `COMBAT_ApplyCold`/`Freeze`/`Poison`/`Stun`, `STATE_ApplyTimed`; seeds of
  both units at every entry and exit; `Game+0xA8` at the timed effects; the unit's state list at event entry.
  *Read lists:* to-hit 0, 2, 12, 16, 19, 31–33, 115, 116, 119, 123, 124, 171, 179, 182, 325 and `ToHitFactor`; defence
  2, 12, 20, 338–340, 348, modes and `BlockFactor`; build 0, 17, 18, 21–25, 48–66, 101, 103, 104, 106, 111, 120–122,
  141, 180, 315, 326, 329–332, 337, 357 and the weapon's bonus columns; reductions 34–46, 110, 118, 142–149, 153, 327,
  333–336 and the DifficultyLevels row; apply and effects 6, 7, 8–11 (life, mana, stamina), 12, 36, 74, 100, 134–136.
  *Characters (tool-built, stock items):* a melee Barbarian (high level, crushing blow, deadly strike, open wounds, leech,
  enhanced damage, AR) with a mercenary; the Nova sorceress (skill packets, immunes; her normal attacks give the
  `ToHitFactor` contrast with the Barbarian); a shield defender with resistances below, at and above the cap, a
  percent-absorb item, DR and MDR; a classic character. *Sessions:* melee Normal, Nightmare, Hell (champions, uniques,
  superuniques, an act boss each for crushing blow and open wounds, the mercenary against the act boss); defender
  Normal, Nightmare, Hell in elemental packs; Nova Hell against immunes; classic Nightmare and Hell; `/players 2` and
  `/players 8` with the melee character. *Required cases beyond the counts:* `ToHitFactor`; percent absorb heal; crushing
  blow on champion, unique, superunique, act boss and in `/players 8`; the hireling boss percent; open wounds on an act
  boss; the unconditional `RangeB(1)` and the build on a miss (both checked by the exit seed). *Slots:* one slot
  serially covers it; a second slot only for the classic and `/players` sessions in parallel (plan 0038 · P2 yields).
- **2026-10-16 — Phase 2 landed (reverser, `lane/h37p2`, slot 3; review pending).** run:2026-10-16-combat
  ([experiments](../findings/combat/experiments.md#run2026-10-16-combat)): 19 sessions, 15 358 events, **0 mismatches**
  under `tools/combat.py check`; player attacks 2 030 (485 / 787 / 758 by difficulty, 1 644 hits, 386 misses), monster
  attacks 4 533 (608 / 1 446 / 2 479, 697 hits, 2 243 blocks overall), missile defence 1 957, Nova 519, mercenary
  1 259, `MonAttackStats` 5 060; chained pairs on the player's seed `pa` 1 796, `ma` 4 235, `md` 1 505, `pm` 519, on
  a monster's seed 2 795 (`MonAttackStats` → attack). Static leftovers of ruling 3 closed in [combat/0001 § 14](../findings/combat/0001-formulas.md#14-phase-2-static-leftovers-phase-1-review-ruling-3)
  (no `PRG` event occurred; "state 38" is the `meleeonly` flag; the monster tick is `0x005A6920`). § 15 raises the
  reproduced claims to `[C]`. **Shortfalls:** the hireling boss percent in Hell (Andariel not reached; 50 and 35 done),
  open wounds on an act boss, crushing blow on an act boss (1) and a superunique (5) below 30, champions 0, evade /
  weapon block / dodge / avoid 0, magic at the cap and immune 0, conversion, freeze, pierce, flat absorb, the player's
  tick. Tooling: `tools/gdb/combat.{gdb,py}` (r1–r9), `tools/combat.py`, `tools/combat_sessions.py`, `d2pilot.py
  --melee-button`, recipes `combatsor`, `combatsolo`, `combatbar`, `combatclassic`.
- **2026-10-16 — Phase 2 review (architect): accept with fixes.** Fresh review in the lane worktree after merging
  `main` (one conflict, `docs/backlog.md`, both sides kept). **Re-run:** the 19 logs match the manifest (sha256 and
  size); `combat.py check` over the run list under `MemoryMax=4G` gives `SUMMARY mismatches=0 events=15358`, and its
  text and JSON outputs are byte-identical to the recorded `c37p2-check.txt`/`.json`; the checker and the logger hash
  as recorded. **Done when, item by item:** chaining per seed role ≥ 20 on both ends for every kind (player seed `pa`
  1 796/1 808, `ma` 4 235/4 226, `md` 1 505/1 503, `pm` 519/518; monster seed `MonAttackStats` → `ma` 2 237, → `ha`
  558; the mercenary is a monster unit, so `ha` chains the ruling-5 way); player attacks 2 030 (485/787/758; 1 644
  hits, 386 misses); monster attacks 4 533 (608/1 446/2 479; 2 243 blocks); per element ≥ 200 applications (fire
  2 803, cold 1 386, lightning 930, poison 1 374, magic 1 340); crushing blow 316, deadly strike 250, open wounds 246
  with 11 duration windows; leech 364/681/455; DR/MDR/absorb 1 747; champion or unique attacks 906; classic 616 + 669;
  /players 2, 3 and 8; `ToHitFactor` both signs; mercenary 1 259 attacks, 80 against act bosses. All main counts and
  splits are met. Short of the rare-branch floor (named, not blocking): at-cap cold 15, lightning 17, poison 2, magic
  0; magic immune 0; avoid/evade/dodge/weapon block 0; crushing blow on an act boss 1, superunique 5, champion 0;
  open wounds on an act boss 0; Hell's hireling boss percent 0; `MonAttackStats` outputs not modelled (monsters/stats
  § H stays `[I]` for its stats; its draws are `[C]`). **Spot checks** (objdump, pinned image): `RNG_Step` on the
  attacker at `0x005D537B` in the finisher; `push 0x26` → `UNIT_HasStateFlag` at `0x0056F19A`; event 3 requeued at
  `frame + 1` at `0x0057C92F`; the 256 floor at `0x00580663`; the to-hit stub call at `0x0057DB72`; the two hooks
  around `COMBAT_BuildDamage` at `0x0056F163`/`0x0056F182`. All hold. **Fixes applied:** (1) § 15 raised six branches
  that reproduced with fewer than the floor's ~30 events (crushing blow `k` = 8 on act boss 1 / superunique 5, the
  prime-evil 200 once, the negative absorbed amount 4, the monster drain 7, the stun draw 17); they move to a new
  `[I]` bullet "below the floor", with the cold/lightning/poison at-cap counts (the cap formula stays `[C]`: one path
  over the table rows, fire 381 at the cap). (2) "8 000+ melee events" → 7 669 rolls in 7 822 events; `ha` checked 994
  (record said 993). (3) The record names the pre-r6 crossing of the monster on-hit skill (attacker seed taken at
  `AD1`, 630 events). (4) The stat-74 open question narrowed to the player's tick. (5) `re/symbols.csv`: 21 rows whose
  claims § 15 holds at `[C]` raised I → C (the to-hit, defence, build, reduction, delivery, crushing blow and open
  wounds functions, the monster tick, `MonAttackStats`, the two debug stubs, `g_DamageResistTable`). (6) The Phase 1
  leftovers backlog entry struck (answered by § 14). Review addendum under the [run record](../findings/combat/experiments.md#architect-review-2026-10-16).
  **Rulings.** (a) A reproduced branch under the floor stays `[I]` with its count, whatever the code shape; the cap
  formula is the exception because the same instructions run for every element row and fire covers it. (b) The
  finding stays `open` until the resume lane. (c) **Resume lane** (reverser, 1 slot, short): run
  `sor-h-andariel-nova2`/`-nova3` from `tools/combat_sessions.py` for Hell's hireling boss percent 25 (≥ 30 mercenary
  hits on Andariel, with `MonsterCEDamagePercent` 20 told apart), and an act-boss session with open wounds on the boss
  (≥ 30 applications); crushing blow on act bosses and superuniques at the same time if the kills give them; append to
  run:2026-10-16-combat as a dated addendum (or a new run id), re-check the whole run list, and move the matching
  lines of the last § 15 bullet to `[C]`. (d) Phase 3 (spec-writer) may start now on what is `[C]`/`[I]`; it lists the
  shortfalls under *Open questions* and re-tags after (c) lands.
- **2026-10-16 — Phase 3 drafted (spec-writer, `lane/p37s`; review pending).** [combat](../specs/combat/README.md)
  in five files: README (events, the packet, the ADR-0014 boundary, the draw order of a player attack, a monster
  attack and a missile on the player as sequence diagrams, chaining per seed role, the branch table, Example 1),
  [to-hit](../specs/combat/to-hit.md), [damage](../specs/combat/damage.md), [reductions](../specs/combat/reductions.md),
  [delivery](../specs/combat/delivery.md); tags C 175 / I 138 / L 23, all `draft`. Worked examples recomputed from the
  run's logs with every seed re-derived: a Hell melee hit with crushing blow and leech (`solo-h3` 357), monster hits
  blocked and resisted in Normal, Nightmare, Hell and classic Hell, crushing blow at `/players 8`, open wounds at level
  85. Every shortfall of § 15's last bullet is under *Open questions* with its count (23 `[L]`); re-tag after the
  resume lane. Also updated: monsters/stats § H (draws `[C]`, stats `[I]`, the `noRatio` open question answered `[I]`,
  the hireling-boss paragraph `[C]` for 50 and 35), player/creation (`ToHitFactor` an AR term `[C]`), data/calc (what
  `ToHitCalc` feeds `[I]`), glossary, the research-map row (`draft`). One gap found while writing: the run's model
  leaves life unchanged for a negative total (25 events), which § 8 does not state (backlog to the reverser). Status
  change for the map: `combat/formulas` not started → draft. Wiki untouched (not asked by the plan).
- **2026-10-16 — Phase 3 review (architect): accept with fixes.** Fresh review in the lane worktree after merging
  `main` (one conflict, `docs/backlog.md`, both sides kept). Gate fast tier green (E9 parses all five specs' Mermaid,
  the `packet-beta` included). **Re-derived:** Example 1 (`solo-h3` 357) draw by draw with an independent LCG script
  (to-hit 3, block 30, physical 50826, deadly strike 83, fire 120, cold 6608, magic 9220, `RangeB(1)` 0, open wounds 44,
  crushing blow 13, leech `Range(2)` 0, cold 79; every intermediate seed equal to the table and to the log), its
  arithmetic (AR 2300 → `c` 77, `lo`/`hi` 41369/112473, `MulDiv` truncating, crushing blow 15890, leech 731, kill
  pre-test 106752 > 74752); the to-hit example's four columns (seeds, `c`, block chances 136/124/126 → 75, 53); the
  reductions example's four columns; crushing blow at `/players 8` (`solo-nm-p8` 426: `r` 19 < 20, 138409 → 130720,
  from the `EVH`/`EVR` lines). `tools/combat.py check` on `solo-h3`, `bar-n-plains`, `solo-nm-p8` and `sor-n-plains`
  (under `MemoryMax=4G`): 763, 593, 1 127 and 587 events, 0 mismatches each. **Spot checks** (objdump, pinned image):
  the 5..95 clamp at `0x0057DB22`; the `÷ 3` (`0x55555556` multiply) at `0x0057E011` after the mode-2 test at
  `0x0057E00B`; the running test `cmp [edi+0x10], 3` at `0x0057EC71`; the burn `+ 0x13C` and `RangeB(1)` at
  `0x0057BC41`/`0x0057BC47`, with `srcdam` read as a byte; leech `Range(2)` at `0x0057C560`–`0x0057C568`; absorb cap
  `0x28` at `0x0057BF2A` and the `−1` row skip at `0x0057BF17`; the life change. One anchor was wrong: **the cold draw
  is at `0x0057B0FA`–`0x0057B124`**, not `0x0057B00D` (that is the `DifficultyRec` call for `MonsterColdDivisor`).
  **Fixes applied:** (1) the cold-draw anchor in combat/README, delivery (constants, D2, notes) and combat/0001 § 9;
  (2) delivery B4: the test is named, `test edi, edi` / `jle` at `0x0057C855`–`0x0057C857` (skips the subtraction when
  `total ≤ 0`), added to combat/0001 § 8 step 4; the claim stays `[I]` (25 events, under the floor), the separate
  `[L]` folded into the under-floor bullet; (3) to-hit: the moving player's `÷ 3` and its "after the cap" note `[C]` →
  `[I]`, and combat/0001 § 15 moves it to the under-floor bullet (ruling 2); (4) damage step 7: `burn = 2` raised to
  `[C]` for a build entering with `burn = 0` and `srcdam` 128 (the checker compares the whole packet at `BD1`), the
  general formula, the constant 316 and the byte read of `srcdam` `[I]`; (5) reductions B3: the `absorbPctStat < 0`
  row skip; (6) README: the packet text names `+0x64` (the `packet-beta` showed it alone) and the unnamed `+0x50`/
  `+0x58`/`+0x5C`; ADR-0008 is accepted, not proposed; the shortfall list gains the `÷ 3` and the total ≤ 0; (7)
  to-hit: `MulDiv` is the overflow-guarded multiply-divide (it truncates), not a rounding helper; (8) delivery: the
  flat-absorb half of the absorb note tagged `[I]`. Tags now C 173 / I 142 / L 22 (README 36/20/5, to-hit 26/30/4,
  damage 34/27/4, reductions 35/24/5, delivery 42/41/4); status `reviewed`. Research map: combat row reviewed, and the
  rows the follow-ons changed (monsters/stats 102/58/5, player/creation 81/39/5, data/calc 77/66/3). **Rulings.**
  (1) *Where `[C]` stops*: accepted as drawn. A value oracle's composition (the player's percent, step 1's `edPct`, the
  shield test, `MonAttackStats`' output stats) stays `[I]`; what the checker compares (every packet field at `BD1`,
  `RD1`, `AD0`, `AD1`) is `[C]` within the inputs the run met, hence (4). (2) *Running auto-hit against moving `÷ 3`*:
  both rest on the same 26 events, under the Phase 2 floor, so both are `[I]` (ruling (a) of the Phase 2 review applies
  whatever the code shape; the Phase 2 review missed the `÷ 3`). (3) *Delivery B4*: named at this review; `[I]` until
  30 events; the spec-writer → reverser entry is answered and struck. (4) The 2026-10-15 "ToHitFactor" entry and the
  2026-10-16 "combat contradictions" entry close: `ToHitFactor` is an AR term `[C]` (1 889 + 85 attacks); the percent
  absorb heals `[C]` (32); crushing blow is 1/4 on uniques `[C]` (63) and scales with the player count `[C]` (5/40/124).
  The champion half of contradiction (3) had 0 events: the code has no champion branch (`k` = 8 only for MonStats `boss`
  or type flag `0x02`), so it stays `[I]` under combat/delivery *Open questions* and with the resume lane, not with this
  entry. (5) The `packet-beta` diagram is accepted: it parses, it adds no fact once the text names `+0x64`, and the
  bit ranges match `re/types/combat.h`. **Not closed:** the plan stays `in-progress` until the resume lane
  (`lane/h37r`) lands, its review, and the spec re-tag (backlog). Wiki: not part of this plan.
- **2026-10-16 — Phase 4 page written ahead of the re-tag (spec-writer, `lane/wiki2`; review pending).** At the
  owner's request the [combat wiki page](../wiki/combat.md) is written now, on the reviewed spec's current tags
  (`based_on:` the five combat files at 2026-10-16), and linked from the wiki index's reading order; the index's
  "no page yet" paragraph is replaced. Confirmed and read-from-the-code statements follow the current `[C]`/`[I]`
  split, and the under-floor branches and the ADR-0014 hand-offs are in its *What is not known yet*. **Phase 4 now
  only refreshes that page** after the resume lane's re-tag: restate every claim the re-tag raises or changes, bump the
  `based_on:` dates, and keep the gate's W4 silent. The same pass restated monsters, game-data and characters to the
  Phase 3 follow-ons (`MonAttackStats` draws, `ToHitCalc`, `ToHitFactor`).
