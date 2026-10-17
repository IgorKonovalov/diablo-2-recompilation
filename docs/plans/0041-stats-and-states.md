# 0041 — Stats and states: how a unit's final stats add up, and how timed states live and die (ADR-0014 phase 2)

> **Status:** in progress. P0 and P1/1b reviewed (accepted with fixes, 2026-10-16 and 2026-10-17); P2 open (0037·P3 reviewed 2026-10-17, the [ADR-0016](../adrs/0016-pipelined-simulation-phases.md) gate is met)
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
  starts. Dependencies: [combat/formulas](done/0037-combat-formulas.md) (P2 accepted 2026-10-16; its spec is P3), and
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
  - *(added 2026-10-16, Phase 0 review)* the Phase 0 data surprises answered from the code, each with a verdict:
    (a) what the `aura` bit does on the masteries 127–129, which have no aura column; (b) whether the aggregation
    honours the off-name `op stat` cells of ItemStatCost 273, 237 and 291; (c) Holy Shield's `aurastatcalc2` with no
    stat and the six progressive `aurastat` cells with no calc; (d) which States row each timed shrine code applies
    (the name pairing is `[L]`; code + 122 holds for 7 of 10) and whether `Arg0`/`Arg1` become its stat value; (e)
    how the Sets compiler resolves a param name (by the property, or by a table order; 44 names are both a skill and
    a state; *the answer goes to the archivist for `excel_bin.py`'s Sets lookup, now a recorded tool limit in
    [Sets § Bonus blocks](../tables/Sets.md#bonus-blocks-plan-0041-phase-0), arc4 review 2026-10-17*); (f) which code sets the 56 States rows no data column names, the monster-mod states among them;
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
  - *(amended 2026-10-17, P1 review)* **draw-freedom:** stats/0002 § 7 finds no draw in any event kind of this plan,
    so the chaining bullet above has nothing to pair. Instead, log the game seed and the acting unit's seed
    ([rng/seeds](../specs/rng/seeds.md)) on entry and exit of every logged event; each kind (apply, expire, tick,
    aura, recompute, shrine/well) shows the seeds unchanged over at least 20 events, which raises its "no draw" to
    `[C]` (run). A kind that moves a seed is re-read and then takes the chaining minimum;
  - **the oracle replacement:** run:2026-10-16-combat and run:2026-10-16-player re-checked with the stat oracles
    replaced by `tools/stats.py` where their logs hold the lists it needs; the record names what could and could not
    be replaced;
  - the Phase 1b cases.

  Rare-branch minimums (about 30 each) may fall short, named in the record with their counts; their claims stay `[I]`.

  *(amended 2026-10-17, P1 review)* "Each `op` used by a stock row" is ops **1, 2, 4, 5, 8, 9, 11, 13**: op 1 only
  through the Barbarian's Increased Stamina (`skill_staminapercent`, `skill_passive_staminapercent`), op 5 through
  `ac%/lvl` and `dmg%/lvl` (two magic prefixes and three uniques, so a tool-built item); ops 3, 10 and 12 have no
  row, ops 6 and 7 only the unspawnable *of Dawn* and *of Sunlight*. Those five stay `[I]` from the code.

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
- **2026-10-16 — Phase 0 landed (archivist, `lane/p41a`).** Gate survey `stats` (`tools/stats_survey.py`, baseline
  `tools/gate/baselines/stats.txt`) and five table-doc sections, every count a survey key:
  - [ItemStatCost § Aggregation](../tables/ItemStatCost.md#aggregation-plan-0041-phase-0): `op`, `op param`, `op base`,
    `op stat1..3`, `direct`, `maxstat`, `itemspecific`, `damagerelated`, `keepzero`, `fCallback`, `fMin`/`MinAccr`,
    `UpdateAnimRate` with offset, width and rows; all 84 `op` rows with their targets. 42 targets, at most 5 sources on
    one (the `+0x0DE` table holds 16); `energy` and `vitality` are both targets and sources, so a derivation chains.
  - [States § States by row](../tables/States.md#states-by-row-plan-0041-phase-0): the rows of each flag bit, the value
    columns and `stat` by row, and which data names each row: 129 of 185 (Skills 119, Misc 9, Sets 2); 56 by none.
    No monster-mod column names a state. The B7 (c) layout gaps (`immed`, `attred`, bit 10, bits 26–28) are **still
    open**: plan 0039 Phase 1b has not landed, so they stay listed.
  - [Skills § Passive and aura columns](../tables/Skills.md#passive-and-aura-columns-plan-0041-phase-0): the 26
    `passive` rows and 26 `aura` rows with their states, stats and calcs, and the 123 other rows that carry these
    columns (timed states, curses, summon stat lists, radii).
  - [Sets § Bonus blocks](../tables/Sets.md#bonus-blocks-plan-0041-phase-0): the sixteen bonus quads are now in the
    `sets` layout (no longer partial; `excel_layout` baseline `sets_cells` 96 → 2 144, 0 mismatches); a param naming a
    state (property `state`: 175 `fullsetgeneric`, 176 `monsterset`) stores the States row, so `excel_bin.py`'s
    `names=` option takes alternatives. [SetItems § Bonus blocks](../tables/SetItems.md#bonus-blocks-plan-0041-phase-0):
    `add func` against the `aprop` pairs (only `a` blocks used; pair *k* only on sets of more than *k* members).
  - [Shrines § Effects](../tables/Shrines.md#effects-plan-0041-phase-0): all 23 rows; the ten timed codes 6–15 pair by
    name with States 128–137 (`[L]`: Shrines names no state).

  Confidence: layouts and counts `[C]` (diff and survey); meanings `[L]` unless an existing finding anchors them.
  Surprises, for Phase 1: (a) Sword, Axe and Mace Mastery (127–129) set both `passive` and `aura`; (b) ItemStatCost
  273 `item_maxdamage_percent_bytime` targets `secondary_mindamage` and `item_throw_mindamage`, 237 and 291
  (`item_absorb_pois_*`) target `item_absorbmagic`; (c) Holy Shield (117) has an `aurastatcalc2` with no stat, the six
  progressive skills an `aurastat` with no calc; (d) the shrine states are in a different order from the shrine codes
  for fire, cold and lightning (the code + 122 holds for 7 of 10); (e) which table the compiler resolves a set param
  name in first (no stock name is both a skill and a state; *corrected at the review: none of the ten names Sets
  stores is both, but 44 names are both a Skills `skill` and a States `state`*). Gate green (fast tier and `--full`, 29 surveys).
- **2026-10-16 — Phase 0 reviewed (architect, `lane/p41a`): accept with fixes**, applied on the lane after merging
  `main` (`b011919`). Re-runs: `gate.py --full` green (29 surveys, `stats` and `excel_layout` among them, 0 errors);
  fast tier green; `excel_bin.py diff … sets` 32 × 67 = 2 144 cells, 0 mismatches; `stats_survey.py summary` equal to
  the baseline key for key. Spot-checks against the survey: the 104 `damagerelated` and 35 `fCallback` ids, the
  `op` histogram and the 37 `op base` rows; States' 56 unnamed rows, the 65/44/28 rows per Skills column and the
  129 union (recomputed from the doc's own lists); the 26 + 26 Skills rows and the 61 + 13 + 15 + 34 = 123 other
  rows (172 in all); the 67 partial and 153 full Sets blocks from the per-set table; the shrine `Arg0`/`Arg1` counts.
  All match. Rulings on the five points:
  1. **`sets` layout, `names=` alternatives, baseline move: accepted.** The change is additive (no other layout
     uses `|`), the diff is clean and `sets_cells` 96 → 2 144 is (3 + 64) columns × 32 records. One claim was wrong: "no stock name is both a skill and a state". 44 names are both, case-insensitively
     (`might`, `fanaticism`, `thorns`, `fade`…); only the ten names Sets stores avoid it. Sets § Bonus blocks and
     surprise (e) corrected. The skills-then-states order is a tool convention that holds for stock data only;
     a property-aware lookup is filed to the archivist (backlog, not blocking).
  2. **"No monster-mod column names a state": kept `[C]` as data, with a second leg.** A name scan alone cannot see a
     column that stores a state as a number. The review added the header check (the only state columns are Misc's
     and Skills', each a States index in its layout) and the property check (the property `state` occurs only in
     the six Sets blocks). The closing sentence ("set by code") is a claim about code with no finding, so it is now
     `[L]`, for Phase 1.
  3. **Shrine-to-state pairing stays `[L]`.** Shrines has no state column, the pairing is by name and breaks the
     code + 122 pattern for fire, cold and lightning; only the shrine operate can raise it. The counts (`shrine_timed`,
     `shrine_pairs`, `shrine_pairs_code_plus_122`) stay `[C]` as data. Shrines' "96 s at 25 frames a second" removed:
     ADR-0014 states timing in frames only.
  4. **Surprises: no backlog entries.** They are questions for this plan's own Phase 1, so they go into its *Done
     when* (bullet added, items (a)–(f), with the 56 unnamed States rows as (f)). The backlog is for requests
     across plans or lanes; a duplicate there would drift.
  5. **"Per row": met, with one gap closed.** ItemStatCost lists all 84 `op` rows; States lists every flag bit and
     value column by row and the naming data per row; Shrines all 23 rows; Sets all 32 sets. The overlay, sound,
     colour and light columns of States are not listed per row, which is right: presentation is outside ADR-0014.
     The gap: the aura rows' passive columns (eight paladin auras carry a `passivestat`, four a `passivestate`) were
     counted but not shown; a per-row table was added to Skills § Passive and aura columns. The 123 "other rows" by
     id only are enough for Phase 0 (the plan asks which rows are passives and auras).
  Also: Sets' "by name block *k* belongs to *k* worn members" was under a `[C]`; split, the meaning `[L]`. Tags
  otherwise follow the evidence rules: meanings `[L]`, data counts `[C]`, the `+0x0DE` reader and the set builder's
  member count `[I]` from items/0006 and items/0004. Follow-up: archivist, property-aware param lookup (backlog).
- **2026-10-17 — Phase 1 and Phase 1b done (reverser, `lane/p41r`, static).** No game run, no slot; Ghidra on the lane's
  copy (`ghidra-p41r`), objdump for the instruction-level reads. The States layout answer of plan 0039 P1b (`attred` =
  bit 10, `immed` not compiled, `rfred`/`rcred`/`rlred` = 26/27/28; `lane/p39b`, not yet merged) was read and is not
  needed by these findings (they read bits 11, 13, 14, 16, 30, 32 through the loader's bit-sets). Findings:
  [stats/0001](../findings/stats/0001-aggregate.md) (41 `[I]`, 14 `[L]`) and [stats/0002](../findings/stats/0002-states.md)
  (39 `[I]`, 9 `[L]`); [stats/experiments](../findings/stats/experiments.md) (empty heading). 101 symbols added (95
  functions, 6 data; subsystems `stats/aggregate`, `stats/states`); types in `re/types/stats.h` (`StatList`,
  `StatEntry`, the ISC run-time tail `ItemStatCostOps`, `TimedStateReq`, `ShrineEffect`).

  | Done-when item | Answer | Anchor |
  |---|---|---|
  | structure | one extended list per unit (`0x80000000`, callback `0x0055B800` for players and monsters); every other list linked under it, counting on `+0x3C`, kept but not counting on `+0x40` (`0x2000`); flags 2 timed, 4 mode-drop, 8 aura, `0x20` curse, `0x40` item props, `0x800` exp, `0x40000000` no damage; full reads = the `+0x48` cache, base reads = `+0x24`, both with the `fMin` floor | 0001 § 1–2 `[I]` |
  | aggregation | no read-time sum: every write, link, unlink propagates up the parent chain (fast add, or a re-evaluation for op-linked stats); evaluation = own + one level of children, then the op terms in source-row order; `op` 1–13 arithmetic with widths (`MulDiv`, `imul` + `sar`, `× n × 64`); op 6/7 time value; a source of op 1–7, 12, 13 keeps its old cache while its target is non-zero; level-up re-evaluates the 37 per-level rows | 0001 § 3–4 `[I]` |
  | maxima | cached full 7/9/11 with `MinAccr` floors 1/0/0; item vitality/energy through op 9/8 (`full − own`), percent through op 11 on the flat sum; current rescaled on a maximum change (`ftol(new/max(old,256)·cur)`, ≥ 1, ≤ new); clamp on unequip | 0001 § 5 `[I]` |
  | items | linked unless broken (`0x100`) or failing requirements (`0x4000`: identified, str/dex with `item_req_percent` and ethereal −10, level, class); the refresh loops until stable; charms from inventory; a dual-wielder's other weapon linked without damage | 0001 § 6 `[I]` |
  | set bonuses | per item: `aprop` lists 165–169 toggled by `add func` (1 by member, 2 by count); per set on the wearer: one list (state 165–170, stat 71 = set id) with partial blocks `0..2·min(n, m−1)−3` and full blocks at `n ≥ m`; broken and unusable members excluded; duplicates count once | 0001 § 7 `[I]` |
  | passives and auras | passive: the `passivestate` list with `passivestat` (param `passiveitype`), 350/351, rebuilt on a level change, absent while the skill's `aurastate` is on; aura: events 8 (selected right skill) and 9 (item `item_aura`), on the `perdelay` grid (min 5), targets in `aurarangecalc` by `aurafilter`, a timed state lasting to one frame past the next run, `direct` heals capped at `maxstat`; same for hirelings (monster event table) | 0002 § 4 `[I]` |
  | states | `STATE_ApplyTimed`: curse resistance (≥ 100 immune, else duration cut), `attract` blocks curses, one curse at a time; same skill+level refresh, lower level refused, else replace; expiry by event 12 at `frame + duration`; `group` exclusion in `STATE_GroupClear` (potions, five skills, stat 98); death purge, mode drop; ticks: life (stat 74, floor 256, cap), stamina by mode, mana `max/(ManaRegen·25)` | 0002 § 2, 3, 6 `[I]` |
  | shrines, wells | table `0x006E1850` code → (stat, state): 6–15 → 128, 129, 131, 132, 130, 133, 134, 135, 136, 137, value `Arg0` (armour 171 not States' `armorclass`), combat `Arg1` damage% + to-hit, stamina 162/10/28 = 1000, skill a bare state; re-arm `reset × 1200 + 1`; recharge and exchange shrines; wells `Parm1/256` of each max, cure poison and freeze | 0002 § 5 `[I]` |
  | event kinds | table of inputs, outputs and draws; **no draw** in any function read (RNG-call and LCG scan), so no chained pairs exist for this plan's event kinds | 0002 § 7 `[I]` |
  | Phase 0 surprises | (a) no effect found for the masteries' `aura` bit; (b) off-name `op stat` cells honoured as written; (c) blank stat or zero value never written by the aura code read (Holy Shield's own function open); (d) the code + 122 pairing confirmed by the table for all ten; (e) not read (open question); (f) 22 of the 56 rows placed (shrines, set states, 85, combat's), 34 left | 0001, 0002 |

  **Surprises.** (1) The take test of `StatRecompute` for ops 2–5 reads the source row's own `opIn[0].opBase` (0 =
  `strength`), not its `op base`, so on a player a per-level stat's own cached value stays hidden. (2) The shrine of
  armour writes `skill_armor_percent` (171), not the `armorclass` its States row names. (3) The stamina shrine sets
  `staminarecoverybonus` 1000, which is exactly the threshold that lets stamina regenerate while running. (4) The set
  marker stat 71 `value` is an ordinary entry, so the wearer's full stat 71 holds the active set ids.

  **Phase 1b.** Registered `src:pk-itemstatcost-guide`; re-fetched `src:arreat-summit-character-basics`,
  `src:arreat-summit-class-pages` (Barbarian), `src:arreat-summit-item-pages` (set basics). 12 verdicts: 1 held,
  9 held with refinement, 1 not covered (weapon-switch slots), 1 **contradicted** (op 6/7 "do not work": the server
  computes them). The contradicted case is not reachable on stock data (the only `…/time` property users, *of Dawn*
  and *of Sunlight*, are not spawnable), so it is not a Phase 2 case; backlog entry filed. The Arreat Summit shrine and
  paladin pages are gone; no shrine or aura-stacking lead.

  **P2 harness questions** (what to log and what the checker predicts; every line needs the frame `game +0xA8`):
  1. *List snapshots:* at each `STATLIST_LinkToUnit` (`0x00626E10`), `STATLIST_Unlink` (`0x006269F0`) and
     `UNIT_ToggleStatListByState` (`0x006279A0`): the list's flags, state, owner type/guid, `+0x18`, its active
     entries; the model rebuilds every unit's lists from these and predicts the `+0x48` cache.
  2. *Stat reads:* at `sub_00624F60_StatListGetValue` (`0x00624F60`) on player and monster lists, a sampled window
     (one unit, all reads for N frames after each equip/unequip): key, returned value; predicted from (1) with § 4 of
     stats/0001. Covers ops 1, 2, 4, 8, 9, 11, 13 on stock items; boundary: a value at the `fMin` floor (negative
     strength from a curse), `keepzero` mana 0.
  3. *Cache writes:* `STATLIST_CacheAdd`/`STATLIST_CacheWrite` (`0x006250B0`, `0x00625150`): key, old, new; the
     checker predicts each from the propagation order (stats/0001 § 3), including the hidden per-level source (log
     the player's stat 216/224 cache with a per-level item on).
  4. *Rescale:* stat callback cases 7, 9, 11 (`0x0055B8EC` and the mana/stamina twins): old, new, current, result;
     boundary: `old ≤ 256`, a result of 0 or 1, a maximum that rises.
  5. *Requirements:* `sub_0062EAF0_ItemReqCheck` (`0x0062EAF0`) return per item and `sub_0055DBC0_EquipReqRefresh`
     (`0x0055DBC0`) marks; cases: an item whose strength comes from another item (the one-pass detach), an ethereal
     item at its −10 boundary, `item_req_percent`, an unidentified item, a broken item.
  6. *Sets:* `SETS_WornMemberMask` (`0x0062A370`) result, `SETS_ToggleItemAProps` (`0x00663A20`) per state on/off,
     `sub_00660120_SetBonusApply` block indices; predicted from Sets/SetItems; partial (2, 3 of 4+) and full; `add
     func` 1 and 2; a duplicate member; a broken member.
  7. *Dual-wield:* a Barbarian with two weapons: the other weapon's list flag `0x40000000` and its damage stats absent
     from the cache; the weapon switch (open question: which code unlinks the switch hand).
  8. *Applies:* `STATE_ApplyTimed` (`0x0056E970`) entry (the request) and exit (return, list); the model predicts
     refuse/refresh/replace/new; cases: a curse on a target with `curse_resistance`, a second curse, a higher and a
     lower aura level, two paladins of one aura, an `attract` target.
  9. *Expiry:* each `EVENT_TimedListExpire` (`0x00580800`) run and each list it frees: frame vs `+0x18` (durations
     in frames); whether one event 12 per call or per unit (open question).
  10. *Group:* `STATE_GroupClear` (`0x0056C740`): potions of one group, a `state` stat item.
  11. *Ticks:* `sub_00580610_LifeRegenTick`, `PLAYER_StaminaRegenTick`, `PLAYER_ManaRegenTick` in/out per frame for a
      window: mode, stats 6–11, 26–28, 74, states 85/100/106; boundary: life at 256 under poison, stamina at 255
      walking, a potion at the cap (`healthpot` freed), stat 74 of the player under open wounds.
  12. *Auras:* events 8 and 9 (`0x0056FCB0`, `0x0056FE40`) frames vs the `perdelay` grid, `SKILLS_ForUnitsInRange`
      targets with distances, `AURA_ApplyToTarget` stats; a mercenary's aura (monster table).
  13. *Shrines and wells:* `OBJOP_Shrine` (`0x00583C70`) code, the state/stat/value applied, `reset` re-arm frame;
      a well use (charges, healed amounts, poison and freeze freed).
  14. *Passives:* `SKILLS_RefreshPassive` (`0x00646D60`) per skill level change: stats, param `passiveitype`.
  15. *itemspecific:* the player's full 72/73 with an item on and off (open question in stats/0001).

  **Boundary recommendation.** Event entry points as in the P2 questions; value oracles: a skill's own `*calc`
  results (data/calc evaluates the stock ones, but the unit-reading variables stay oracles), the shrine to-hit and
  damage values (`SHRINE_StatValue` cases 19 and 21), monster AI and the combat events that apply states (inputs).
  The stat-read window: reads are per frame and many (combat, regeneration); log reads only in windows after a list
  change, and log every cache write, which bounds the model (ADR-0014 § Log volume).

  **Points for the review.** (a) Everything is `[I]`; no event kind of this plan draws (0002 § 7), so the chaining
  minimum has nothing to pair. (b) The `StatRecompute` take-test quirk (0x006267C0–0x006267DA) and the hidden source
  value. (c) op 11 as a percentage of the flat sum only (`[ebp-8]`). (d) The unequip of a set item frees the wearer's
  set list, which the refresh rebuilds; Phase 2 should see the rebuild. (e) Surprise (e) and 34 of the (f) rows
  left as static follow-ups. (f) The contradicted lead and its stock reachability.
- **2026-10-17 — Phase 1 and 1b reviewed (architect, `lane/p41r`, `main` `f10dca8` merged in as `270c773`): accept
  with fixes; Phase 2 opens.** Merge: six addresses were named on both sides (p39b on `main`, this lane):
  `0x0055DB00`, `0x0055DBC0`, `0x0055F850`, `0x00624ED0`, `0x00625420`, `0x0062EAF0`. `main`'s names are kept
  (`sub_0055DB00_ItemUsableBy`, `sub_0055DBC0_EquipReqRefresh`, `sub_0055F850_ItemBreak`,
  `sub_00624ED0_StatListGetBaseValue`, `sub_00625420_StatListGetStat`, `sub_0062EAF0_ItemReqCheck`) and stats/0001
  and the P2 questions above cite them; the lane's symbols are 95 after the merge (89 functions, 6 data). Gate green.
  **Anchors** (objdump on the pinned `Game.exe`): the 17 function starts of the event entry points and the set,
  aura, passive and shrine code (`STATLIST_Propagate`, `STATE_GroupClear`, `EVENT_TimedListExpire`,
  `ITEMSTATCOST_Load`, `SETS_WornMemberMask`, events 8/9, `OBJOP_Shrine`, `SKILLS_RefreshPassive`,
  `AURA_ApplyToTarget`, `UNIT_ToggleStatListByState`, `STATLIST_LinkToUnit`/`Unlink`, `SETS_ToggleItemAProps`,
  `sub_00660120_SetBonusApply`, the life tick, `SKILLS_NextPeriodicFrame`) all resolve; `StatRecompute`'s op class
  table `0x0062690C` (0→none, 1 and 12 always, 2/3, 4/5, 6/7, 13) and `StatEvaluate`'s jump table `0x00626688`
  match § 3–4; the curse rules at `0x0056EA0A–0x0056EA4A` (109 ≥ 100 refused, `MulDiv` cut, 57) match; the shrine
  table `0x006E1850` read as 24 × `{fn, stat, state}`: codes 6–15 give exactly the ten pairs of 0002 § 5, codes
  0–5 and 16–23 no state; `SHRINE_Stamina` writes 28 = 1000 (`0x00583B14`). An independent one-level scan of the 95
  functions' ranges finds RNG calls or the LCG constant only in neighbouring functions (`0x0056C8E0`, shrine codes
  18/21/22, an item-event function at `0x005BFA10`), never inside a function the findings read.
  **Tags:** no `[C]` in either finding (the "C" in stats/0001's function table is the existing symbol row for op
  13, items/0006); every behavioural claim `[I]` with a code anchor; every `[L]` is a lead verdict or under *Open
  questions*; `src:pk-itemstatcost-guide` registered with version and "no game code"; verdicts recorded blind-first.
  **Rulings:**
  - (a) **Draw-free subsystem: no ADR change.** ADR-0016 only gates phases; ADR-0014's chaining floor applies to kinds
    that draw. What the plan lacked was evidence for the absence itself: P2's done-when now asks for seed
    invariance per event kind (amendment above), which makes "no draw" `[C]` by run and sends any kind that moves
    a seed back to the chaining minimum. Everything else rises by the per-event reproduction, as for 0037.
  - (b) **The take-test quirk: confirmed.** `0x006267C0` loads `[ebp−8]` = source row `+0x0DE + 6k` (set at
    `0x0062670D`), whose word 0 is `opIn[k].opBase` (the loader writes it at `+0x0DE` from `op base`,
    `0x0063840B–0x0063841B`), not the row's `+0x56`; ops 4/5 do the same at `0x006267F7` with `STATS_GetUnitStat`
    on the linked unit. Two refinements written into 0001 § 3: the loader's `0xFFFF` fill covers `+0x5E..+0xDD`
    only, so the 0 that makes the quirk test strength is the record's initial content (P2 question 3 confirms);
    and a source evaluating to 0 writes 0 early and never walks its `+0x5E` dependents (`0x00626851`), which the
    finding had missed.
  - (c) **op 11 on the flat sum: confirmed.** Case 11 (`0x0062660B`) multiplies `[ebp−8]`, set to own + children at
    `0x0062624C` and changed only by ops 1 and 13 when the owner is an item; op 7 alone uses the running `[ebp−4]`.
  - (d) **Set unequip frees the set list: confirmed.** `SETS_UpdateOwnerBonusList` mode 1 calls
    `UNIT_UnlinkStatList` and `STATLIST_FreeIfPlain` (`0x00663C0A`, `0x00663C10`); mode 0 clears an existing list or
    allocates, links with damage and sets the state, then adds stat 71 and applies the blocks (`0x00663C8A`). The
    finding's stat-71 anchor pointed at the unlink call; corrected to `0x00663C93`, and "includes the ids" made
    "the sum of the active set ids" (two sets add).
  - (e) **Phase 0 surprises (e) and (f): not blocking.** The *Done when* asked for a verdict on each; (e) has "not
    read" and (f) 22 of 56 placed. Neither changes an aggregation or state rule the spec needs: (e) is the Sets
    compiler (the stored values are `[C]` as data), and the 34 unplaced rows are set by skill or monster code
    (phase 3 territory). Both filed to the reverser as one static follow-up; (e)'s answer then goes to the
    archivist as the arc4 review recorded.
  - (f) **Other surprises: accepted as findings.** Armour shrine → 171 and the stamina shrine's 28 = 1000 are read
    from the table and the handler (above); the skill shrine's table stat 11 is not read (the handler writes 11 = 0
    itself), added to 0002 § 5. Stat 71 in the totals: see (d).
  - **The contradicted lead (op 6/7).** Settled as "1.14d's server computes them" by the code; the evidence rules
    want a contradiction settled by a second path, run or reproduction. Data check repeated: of the 36 `…/time`
    properties only `ac/time` is used, by *of Dawn* and *of Sunlight* (`spawnable` blank, `frequency` 0), so no stock
    path reaches op 6/7 and P2 cannot see them. The claim stays `[I]`; the spec states it as a 1.14d behaviour
    differing from the guide and lists it under *Open questions*. Optional, not blocking: an ADR-0015 emulation of
    `STAT_ByTimeValue` and `StatEvaluate` cases 6/7 with a declared image (filed).
  - **P2 questions: concrete enough, with four additions.** Each names its breakpoint, its fields and its boundary
    cases, and together they cover every P2 *Done when* line. Additions: (i) the seed invariance above, at the
    breakpoints already listed; (ii) question 2's window is stated as "all reads of the logged unit for 50 frames
    after each list change", and its op list is the eight stock ops of the amendment (op 1 by the Barbarian's
    Increased Stamina, op 5 by a tool-built `ac%/lvl` item); (iii) question 3 also logs a level-up (stat 12 change:
    the 37 per-level rows re-evaluated) and a source that falls to 0 (no dependent walk); (iv) question 8's "two
    paladins of one aura" is a paladin plus an Act 2 hireling with the same aura (one client; plan 0044 keeps the
    two-player case).
  - **Boundary: accepted as recommended.** 0037·P3's review (2026-10-17) moved no input across the combat boundary,
    so ADR-0016 needs no re-ruling: a skill's own calc results with unit-reading variables, the shrine to-hit and
    damage values (`SHRINE_StatValue` 19 and 21), monster AI and the combat appliers stay value oracles; reads are
    logged in windows after list changes and every cache write is logged.
  **Fixes applied:** stats/0001 § 3 (the `v = 0` path and the `+0x0DE` initial content), § 7 (stat 71 sum, anchor);
  stats/0002 summary (curse cut by `r` = stat 109, negative lengthens) and § 5 (skill shrine's table stat); the merge
  renames; P2 *Done when* amendments (draw-freedom, the stock op list); research map rows `stats/aggregate` and
  `stats/states` added (they were due when the plan started); README row.
  **P2 readiness:** open now, **two slots** (the plan's maximum): slot A a Barbarian (dual wield, Increased Stamina,
  per-level and `ac%/lvl` items, a partial and a full set, charms, ethereal and socketed items, an item whose
  requirement fails) for questions 1–7, 14, 15; slot B a Paladin with two auras and an Act 2 hireling, standing in
  curses, cold and poison, with potions, shrines and wells, for 8–13. Lane H1 takes it after 0040·P2 per the queue;
  the second slot is lane H2's between two 0038 batches.
  **Filed:** reverser (static: Phase 0 surprise (e) and the 34 States rows of (f); optional op 6/7 emulation),
  backlog. Struck: the review request and the contradicted-lead entry (ruled here).
