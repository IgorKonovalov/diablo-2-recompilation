# 0041 — Stats and states: how a unit's final stats add up, and how timed states live and die (ADR-0014 phase 2)

> **Status:** approved (owner, 2026-10-16; unattended). [ADR-0016](../adrs/0016-pipelined-simulation-phases.md) accepted: P0 and P1/1b may start now; P2 waits for 0037·P3's review
> **Created:** 2026-10-16
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0007-fetched-leads-only, 0011-harness-slots, 0013-forced-path-runs-cell-level, 0014-scope-game-simulation, 0015-emulated-reproduction, 0016-pipelined-simulation-phases

## TL;DR

**Question:** given a unit's base stats, its equipped items, its active set bonuses, its passive skills, the auras
around it and the states on it, what value does the server read for each stat; and when a state is put on a unit (a
curse, an aura, cold, poison, a potion, a shrine), how long does it last in frames, what stat list does it carry, how
does it refresh, expire and tick? This is phase (2) of [ADR-0014](../adrs/0014-scope-game-simulation.md). When it is
done:
- ItemStatCost's aggregation columns, the States table and the passive and aura columns of Skills are documented to
  the depth this code reads them;
- `docs/findings/stats/0001-aggregate.md` and `docs/findings/stats/0002-states.md` name the stat-list structure, the
  aggregation, the `op` derivations, the set-bonus activation, `UnitGetMaxHp/Mana/Stamina`, the state lifecycle and the
  regeneration ticks;
- `tools/stats.py` predicts a unit's stats from its lists, and reproduces the state events of a run per event;
- `docs/specs/stats/` is drafted and reviewed; the value oracles of plans 0034 and 0037 are replaced where the kept
  logs hold what the model needs.

The boundary: **what a skill does when used** (its dispatch, missiles, its damage packet) is phase (3). A passive
skill's or an aura's **stat list**, as the Skills table defines it (`passivestat*`, `aurastat*` with their calcs, which
[data/calc](../specs/data/calc.md) evaluates), is in this plan; so is a curse's state once applied. Which skill is
cast, and when, is an input.

## Context

- Research map: new row(s) `stats/aggregate` and `stats/states` in the **Simulation** band, added when this plan
  starts. Dependencies: [combat/formulas](0037-combat-formulas.md) (P2 accepted 2026-10-16; its spec is P3), and
  reviewed [items/properties](../specs/items/properties.md) (the property writers and stat storage),
  [player/creation](../specs/player/creation.md) (base stats; the refill maxima as named value inputs, open question
  4), [data/calc](../specs/data/calc.md) (the aura and passive calcs), [monsters/stats](../specs/monsters/stats.md)
  (the monster's creation stats and mods), [items/uniques-sets](../specs/items/uniques-sets.md) (set membership).
- **The gate.** ADR-0014 says a later phase's plan is written only once the earlier phase's spec is reviewed.
  ADR-0016 (accepted 2026-10-16) lets P0 and P1/1b start once the previous phase's P2 is accepted, which 0037's was
  on 2026-10-16, and keeps this plan's P2 behind 0037·P3's review.
- **The input list is set.** combat/0001's *Boundary recommendation* lists every stat a combat event reads, as value
  oracles (stats 0, 2, 12, 16–25, 31–46, 48–66, 74, 100–106, 110–111, 115–124, 134–136, 141–149, 153, 171, 179–182,
  315, 325–327, 329–340, 348, 357). Those identities stay `[I]` until this plan consumes them (ADR-0014 § Negative,
  "Value oracles hide input errors").
- **Code already named** (grep `re/symbols.csv`): `sub_00625500_UnitGetStat` (I), `sub_00624F60_StatListGetValue`
  (I), `STATLIST_AddStat`, `STATLIST_SetStat` (I), `sub_00626D40_UnitStatListCreate` (I),
  `sub_00627910_StatListLinkOwner` (I), `sub_00625790_UnitFindStatList`, `sub_00625650_StatListFindByState`,
  `sub_006256E0_StatListFindByFlags` (I), `sub_00626200_StatEvaluate` (C), `sub_00625D10_UnitGetMaxHp` (C),
  `STATE_ApplyTimed`, `sub_0056E740_AddStatEvent` (I), `data:g_StatEventFuncs` (I), `UNIT_HasState` (I),
  `sub_00611D60_StatesMaskBuild` (I), `sub_00580610_LifeRegenTick` (I), `data:g_SetAPropStates` (C),
  `sub_005BEDA0_ItemUseTimedState` (C); the combat stat-event handlers (`STATEVENT_*`).
- **Open edges this plan closes:** player/creation open question 4 (`UnitGetMaxHp/Mana/Stamina` with item bonuses);
  items/properties open question 3 (`add func` 1/2 when worn and the Sets bonus blocks); combat/0001's open question on
  the player's stat-74 tick under poison or open wounds; the data/calc unit-state inputs (`stat()`, the unit-reading
  codes) that plan 0038 parks as d-sim; the States layout gaps (backlog 2026-10-15, plan 0039 B7 (c)).
- **Shrines and wells.** A shrine that puts a state on the player (armour, combat, resist, skill, experience and the
  like) and a well's refill are state and stat sources; their operate is named in [objects](../specs/objects/README.md)
  as simulation. They are in this plan as state sources; shrines that create missiles or monsters are not (phase 3,
  and monsters/special).
- Leads: `src:arreat-summit-bonuses` and the registered ItemStatCost guides; Phase 1b searches for set-bonus,
  life-per-vitality, aura stacking and state duration documentation.

## Phases

### Phase 0 — Aggregation columns and the States table
- **Owner skill:** archivist
- **What:** document the columns this code is expected to read, where the existing docs stop.
- **Outputs:**
  - [ItemStatCost](../tables/ItemStatCost.md) § Aggregation: `op`, `op param`, `op base`, `op stat1..3`, `direct`,
    `maxstat`, `itemspecific`, `damagerelated`, `keepzero`, the callback and minimum columns, with each
    stat that uses an `op` listed with its targets, per row;
  - [States](../tables/States.md): the full layout (the gaps of plan 0039 B7 (c) closed if that batch has landed,
    otherwise listed), every column the `.txt` header names with its flag bit or field, per row; which rows a skill,
    an item, a monster mod or a shrine names;
  - [Skills](../tables/Skills.md) § Passive and aura columns: `passivestate`, `passiveitype`, `passivestat1..5`,
    `passivecalc1..5`, `aurastate`, `auratargetstate`, `aurastat1..6` with calcs, `auralencalc`, `aurarangecalc`,
    `aurafilter`, which rows are passives and which auras;
  - [Sets](../tables/Sets.md) and [SetItems](../tables/SetItems.md) § Bonus blocks (partial and full set columns, `add
    func`);
  - [Shrines](../tables/Shrines.md) § Effects: the columns an operate is expected to read (the code, the two
    arguments, the duration, `effectclass`, as the `.txt` header names them);
  - `tools/stats_survey.py` (gate survey `stats`), printing the counts the docs state.
- **Done when:** each named section lists every column it claims with offset, width and value range; the survey's
  `SURVEY` line matches the docs; meanings stay `[L]` unless a finding anchors them; the gate is green.

### Phase 1 — Read aggregation and the state lifecycle
- **Owner skill:** reverser
- **What:** read the stat-list code from a unit's lists to `UnitGetStat`'s result, and the state code from apply to
  expiry.
- **Outputs:** `docs/findings/stats/0001-aggregate.md`, `docs/findings/stats/0002-states.md`,
  `docs/findings/stats/experiments.md` (empty heading); `re/symbols.csv` rows (subsystems `stats/aggregate`,
  `stats/states`); `re/types/stats.h`.
- **Done when:** the findings state, each with addresses and `[I]` or better:
  - **the structure:** stat lists, their kinds and flags (base, item, set, skill, state, aura, temporary), the owner
    chain and how lists are linked to a unit and unlinked; the full and the base accessors and which callers use each;
  - **aggregation:** the order in which lists are summed; `op` 1–13 with their arithmetic (widths, shifts, rounding,
    per-level and per-time terms); the `maxstat` and other clamps; item requirements and a broken or unusable item
    (whether its list counts); ethereal and socketed children; the recompute triggers (equip, unequip, level-up, state
    change) and whether a cache exists;
  - **the maxima:** `UnitGetMaxHp/Mana/Stamina` from base, the CharStats per-point factors, the item and state
    bonuses, and percent bonuses;
  - **set bonuses:** activation on equip and unequip, partial and full blocks, `add func` 1 and 2;
  - **passives and auras:** how a passive's and an aura's stat list is built (the calcs, the skill level input), the
    aura range and target filter, stacking of two auras of one kind, a mercenary's aura;
  - **states:** apply (`STATE_ApplyTimed` and the other callers), the duration in frames and where it comes from,
    refresh and stacking rules, the `group` exclusion, removal and expiry (`AddStatEvent`, the event queue), the
    per-frame ticks (life, mana and stamina regeneration, poison, the player's stat-74 tick), the shrine and well
    operates that apply a state or refill; for each, its **draws** and **seeds**, and the client copy told apart;
  - for each event kind (apply, expire, tick, recompute), the inputs, outputs and the chaining reading (ADR-0014);
  - the community cross-check (Phase 1b) done;
  - **the boundary recommendation** for Phase 2: the event entry points, which stats stay value oracles (a skill's own
    computation, AI), the stat-read window (a recompute is a per-frame path: ADR-0014 § Log volume). The architect
    rules at the review.

### Phase 1b — Community cross-check
- **Owner skill:** reverser
- **What:** search for and register stat-op, set-bonus, life-per-vitality, aura and state-duration documentation;
  compare blind.
- **Outputs:** `docs/sources.md` entries with the game version each describes; verdicts in the findings' *Leads used*.
- **Done when:** each compared claim carries one verdict; every `contradicted` claim reachable on stock data is a
  required case of Phase 2.

### Phase 2 — Per-event reproduction
- **Owner skill:** reverser (agent-driven; **at most two slots**, given in the prompt; starts only after 0037·P3 is
  reviewed (ADR-0016))
- **What:** write `tools/stats.py` (model and `check`), `tools/gdb/stats.gdb` and its handler, the character recipes,
  and log a run.
- **Characters** (tool-built with stock items, ADR-0013 § Neutral): a character with per-level stats (`op` 2 and 4), a
  partial and a full set, charms, socketed and ethereal items, an item whose requirements are not met; a Barbarian or an
  Amazon with passives; a Paladin with two auras and a mercenary with an aura; a character standing in curses and cold
  and poison attacks; potion and shrine states.
- **Done when:** `run:YYYY-MM-DD-stats` reproduces with **0 mismatches** over at least:
  - 2 000 stat reads predicted from the logged lists (at least 30 stat ids, each `op` used by a stock row at least 20
    times), with the read window stated;
  - 300 recomputes on equip or unequip, 100 set-bonus changes (partial and full), 50 aura on and off events,
    `UnitGetMaxHp/Mana/Stamina` predicted with item, set, aura and state bonuses;
  - 400 state applications and 300 expiries, durations checked in frames, at least 30 refreshes and 20 `group`
    exclusions; 200 regeneration and poison ticks, the player's stat-74 tick among them;
  - 50 shrine or well operates that apply a state or refill;
  - **chaining (ADR-0014):** for every event kind that draws, at least 20 chained pairs; a kind with none keeps its
    draw-order claims at `[I]`;
  - **the oracle replacement:** run:2026-10-16-combat and run:2026-10-16-player re-checked with the stat oracles
    replaced by `tools/stats.py` where their logs hold the lists it needs; the record names what could and could not
    be replaced;
  - the Phase 1b cases.

  Rare-branch minimums (about 30 each) may fall short, named in the record with their counts; their claims stay `[I]`.

### Phase 3 — Spec: stats
- **Owner skill:** spec-writer
- **What:** write `docs/specs/stats/README.md`, `stats/aggregate.md` and `stats/states.md`; update player/creation
  (the maxima), items/properties (the set blocks when worn), data/calc (the unit-state inputs) and the combat spec's
  input list.
- **Done when:** the spec follows the template; every statement is tagged; it has the list kinds and the summing order
  as a diagram, each `op` as pseudocode with its arithmetic, the maxima, the set activation, the state lifecycle as a
  state diagram with durations in frames, and worked examples from the run. The architect's review passes.

## Open questions

- **Two clients.** Party auras and hostile states stay `[I]` here; plan 0044 (two clients, ADR-0008
  accepted 2026-10-16) can stage them.
- **Skills.** A skill's own effect (the damage it builds, the missiles it makes) and charged and item-granted skills
  are phase 3.
- **Plan 0038's d-sim rows** that this plan reaches (data/calc unit-state codes, monsters/stats x87 rows if a damaged
  monster is logged) are re-checked at its close.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-16 — Drafted (architect, `lane/plans39`).** Status `proposed`; gated on ADR-0016 or on 0037·P3's review.
- **2026-10-16 — Approved (owner, via the main session).** Plans 0039–0044 approved to run unattended, like 0027–0038. ADR-0016 accepted the same day: P0 and P1/1b may start; P2 waits for 0037·P3's review.
