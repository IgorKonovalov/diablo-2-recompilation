# 0041 — Stats and states: how a unit's final stats add up, and how timed states live and die (ADR-0014 phase 2)

> **Status:** done (approved 2026-10-16, closed 2026-10-17; P0, P1/1b, P2 and P3 accepted with fixes)
> **Created:** 2026-10-16
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0007-fetched-leads-only, 0011-harness-slots, 0013-forced-path-runs-cell-level, 0014-scope-game-simulation, 0015-emulated-reproduction, 0016-pipelined-simulation-phases

## TL;DR

**Question:** given a unit's base stats, its equipped items, its active set bonuses, its passive skills, the auras
around it and the states on it, what value does the server read for each stat; and when a state is put on a unit (a
curse, an aura, cold, poison, a potion, a shrine), how long does it last in frames, what stat list does it carry, how
does it refresh, expire and tick? This is phase (2) of [ADR-0014](../../adrs/0014-scope-game-simulation.md). When it is
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
[data/calc](../../specs/data/calc.md) evaluates), is in this plan; so is a curse's state once applied. Which skill is
cast, and when, is an input.

## Context

- Research map: new row(s) `stats/aggregate` and `stats/states` in the **Simulation** band, added when this plan
  starts. Dependencies: [combat/formulas](0037-combat-formulas.md) (P2 accepted 2026-10-16; its spec is P3), and
  reviewed [items/properties](../../specs/items/properties.md) (the property writers and stat storage),
  [player/creation](../../specs/player/creation.md) (base stats; the refill maxima as named value inputs, open question
  4), [data/calc](../../specs/data/calc.md) (the aura and passive calcs), [monsters/stats](../../specs/monsters/stats.md)
  (the monster's creation stats and mods), [items/uniques-sets](../../specs/items/uniques-sets.md) (set membership).
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
  like) and a well's refill are state and stat sources; their operate is named in [objects](../../specs/objects/README.md)
  as simulation. They are in this plan as state sources; shrines that create missiles or monsters are not (phase 3,
  and monsters/special).
- Leads: `src:arreat-summit-bonuses` and the registered ItemStatCost guides; Phase 1b searches for set-bonus,
  life-per-vitality, aura stacking and state duration documentation.

## Phases

### Phase 0 — Aggregation columns and the States table
- **Owner skill:** archivist
- **What:** document the columns this code is expected to read, where the existing docs stop.
- **Outputs:**
  - [ItemStatCost](../../tables/ItemStatCost.md) § Aggregation: `op`, `op param`, `op base`, `op stat1..3`, `direct`,
    `maxstat`, `itemspecific`, `damagerelated`, `keepzero`, the callback and minimum columns, with each
    stat that uses an `op` listed with its targets, per row;
  - [States](../../tables/States.md): the full layout (the gaps of plan 0039 B7 (c) closed if that batch has landed,
    otherwise listed), every column the `.txt` header names with its flag bit or field, per row; which rows a skill,
    an item, a monster mod or a shrine names;
  - [Skills](../../tables/Skills.md) § Passive and aura columns: `passivestate`, `passiveitype`, `passivestat1..5`,
    `passivecalc1..5`, `aurastate`, `auratargetstate`, `aurastat1..6` with calcs, `auralencalc`, `aurarangecalc`,
    `aurafilter`, which rows are passives and which auras;
  - [Sets](../../tables/Sets.md) and [SetItems](../../tables/SetItems.md) § Bonus blocks (partial and full set columns, `add
    func`);
  - [Shrines](../../tables/Shrines.md) § Effects: the columns an operate is expected to read (the code, the two
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
    [Sets § Bonus blocks](../../tables/Sets.md#bonus-blocks-plan-0041-phase-0), arc4 review 2026-10-17*); (f) which code sets the 56 States rows no data column names, the monster-mod states among them;
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
    ([rng/seeds](../../specs/rng/seeds.md)) on entry and exit of every logged event; each kind (apply, expire, tick,
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
  - [ItemStatCost § Aggregation](../../tables/ItemStatCost.md#aggregation-plan-0041-phase-0): `op`, `op param`, `op base`,
    `op stat1..3`, `direct`, `maxstat`, `itemspecific`, `damagerelated`, `keepzero`, `fCallback`, `fMin`/`MinAccr`,
    `UpdateAnimRate` with offset, width and rows; all 84 `op` rows with their targets. 42 targets, at most 5 sources on
    one (the `+0x0DE` table holds 16); `energy` and `vitality` are both targets and sources, so a derivation chains.
  - [States § States by row](../../tables/States.md#states-by-row-plan-0041-phase-0): the rows of each flag bit, the value
    columns and `stat` by row, and which data names each row: 129 of 185 (Skills 119, Misc 9, Sets 2); 56 by none.
    No monster-mod column names a state. The B7 (c) layout gaps (`immed`, `attred`, bit 10, bits 26–28) are **still
    open**: plan 0039 Phase 1b has not landed, so they stay listed.
  - [Skills § Passive and aura columns](../../tables/Skills.md#passive-and-aura-columns-plan-0041-phase-0): the 26
    `passive` rows and 26 `aura` rows with their states, stats and calcs, and the 123 other rows that carry these
    columns (timed states, curses, summon stat lists, radii).
  - [Sets § Bonus blocks](../../tables/Sets.md#bonus-blocks-plan-0041-phase-0): the sixteen bonus quads are now in the
    `sets` layout (no longer partial; `excel_layout` baseline `sets_cells` 96 → 2 144, 0 mismatches); a param naming a
    state (property `state`: 175 `fullsetgeneric`, 176 `monsterset`) stores the States row, so `excel_bin.py`'s
    `names=` option takes alternatives. [SetItems § Bonus blocks](../../tables/SetItems.md#bonus-blocks-plan-0041-phase-0):
    `add func` against the `aprop` pairs (only `a` blocks used; pair *k* only on sets of more than *k* members).
  - [Shrines § Effects](../../tables/Shrines.md#effects-plan-0041-phase-0): all 23 rows; the ten timed codes 6–15 pair by
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
  [stats/0001](../../findings/stats/0001-aggregate.md) (41 `[I]`, 14 `[L]`) and [stats/0002](../../findings/stats/0002-states.md)
  (39 `[I]`, 9 `[L]`); [stats/experiments](../../findings/stats/experiments.md) (empty heading). 101 symbols added (95
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
- **2026-10-17 — Phase 2 checkpoint (reverser, `lane/p41h`, slots 2 and 1): resume note.** Stopped at a clean break
  on the orchestrator's rotation; both slots stopped and empty, no background loop left. Run id `run:2026-10-17-stats`
  ([record](../../findings/stats/experiments.md#run2026-10-17-stats), marked in progress). 13 sessions logged and checked:
  **0 mismatches** (`tools/stats.py check`, 17 703 links/unlinks, 156 683 CacheAdd/CacheWrite predicted in order,
  648 599 reads of 118 stat ids, 3 907 set lists, 12 895 aprop toggles, 14 240 requirement checks, 6 200 passive
  lists, 3 226 rescales, 2 941 applies, 2 208 expiry runs (80 lists freed, lateness 0), 42 794 ticks, 4 810 aura
  durations (= `perdelay` + 1), 3 timed shrines, 714 refresh step-4 checks, 7 level changes; the ISC run-time graph
  equals the loader's rules on all 359 rows). Ops reached in predicted writes: 1 288, 2 1 484, 4 1 932, 5 26,
  8 531, 9 2 572, 11 92, 13 124. Seed invariance (entry = exit, game and acting unit): link 8 856, unlink 8 841, own
  write 67 592, toggle 12 895, apply 4 835, expire 2 208, tick 42 794, shrine 4, well 3, aura 2 064 — every kind ≥ 20
  except shrine and well; the aura kind draws when Sanctuary hits (865 runs chained: one `RNG_RangeB` per hit from
  `SKILLS_RollElemDamage` 0x0056E0C0, called by `sub_005CF3A0_AuraHitDo`; a kill inside a run also moves the game
  seed through the drop).
  **Questions:** 1 (snapshots), 2 (reads), 3 (cache writes, take test, level-up, stale source), 4 (rescale), 6 (sets:
  masks, add func 0/1/2, partial and full, duplicate member, failing member), 7 (dual wield, switch: callers
  0x005616A0 / 0x0054CE70), 8 (apply: refresh, lower refused, higher replaces, new; shrine states are curses), 9
  (expiry: one event per request), 11 (stamina and mana ticks by mode, state 85, life capped; stat 74 positive only),
  12 (aura grid ≡ 1 mod 50, durations, merc through the monster table), 14 (passives), 15 (itemspecific 72/73 reach the
  wearer's cache) are covered. **Left:** Q5 decisive cases (`req_decisive_ethereal` and `_req_percent` are 0: run
  `bard-town1`, StatsBarD strength 85, built); Q10 effective group clear (run `nec-town1`, StatsNec full Trang-Oul's,
  built; the first attempt failed because `inv:open` took the dark Act IV town for an open panel, fixed in
  `d2pilot.py` `inv_grid_open`, failed log kept as `s1017-nec-town1.log.failed-dark-town`); Q11 poison and the
  stat-74 tick at 256 (run `palc-spider`, `palc-oasis`, StatsPalC low defence, built; no Paladin was poisoned so far);
  Q13 shrines (3) and wells (3) are far below 50 (shortfall likely; `objop --walk` finds few); op 5 at 26 and op 11 at
  92 (op 3, 6, 7, 10, 12 unreachable). Not done at all: the findings' § 9 (0001) and § 8 (0002) sections — drafts with
  `{PLACEHOLDERS}` and the helpers (`fill.py` fills them from the check JSON, `table.py` the session table, `acts.py`
  lists the clicks' effects) are in `workspace/logs/stats/p41h-drafts/`; the summary bullets of both findings are
  already split and raised against this run; the oracle replacement (`tools/stats.py oracle-player`: 13 of 20
  level-up maxima of run:2026-10-16-player equal the own entries, 7 need item lists the logs lack; the combat logs
  hold values, not lists: not replaceable); the review request.
  **Built saves:** `workspace/logs/stats/p41h-saves/*.d2s` (Stats, StatsB/C/D, StatsNec, StatsPal/B/C; rebuild
  with `d2s.py build` on `workspace/samples/d2s/smp{bar,pal,nec}.d2s`, hashes in `test_d2s.py`). **Resume:**
  `python3 -I tools/stats_sessions.py run --slot 2 --tag s41 --saves workspace/logs/stats/p41h-saves --run s1017
  bard-town1 nec-town1` and `… --slot 1 --tag s41p … palc-spider palc-oasis`, then append the logs to
  `s1017-run.lst`, re-run the check and the manifest, fill the sections, finish the record and file the review.
  **Gotchas:** every click that changes lists must be `clickv`; a requirement-failing item cannot be re-equipped by
  the UI (never toggle it); start the next session only after the previous one's `restore` (two launches at once
  missed the menu); the game's `EquipReqRefresh` runs on a 136-frame period by itself; the logger slows the game to
  about a frame per click in town (settle handles it).
- **2026-10-17 — Phase 2 landed (reverser, `lane/p41h`, slots 2 and 1): resumed from the checkpoint above.** Main
  merged twice (`78b96a9`, then `7e15a1b` before the request). Five sessions added (`bard-town1`, `bard-town2`,
  `nec-town1` on slot 2; `palc-spider`, `palc-oasis` on slot 1): `run:2026-10-17-stats`
  ([record](../../findings/stats/experiments.md#run2026-10-17-stats)) is **18 sessions, 0 mismatches** (`tools/stats.py
  check` at `27f49ad`, report `s1017-check.json` `677e12a6…`, run list `a42758f3…`, manifest `7fd7a93a…`): 26 087
  links/unlinks, 232 042 CacheAdd/CacheWrite in order, 891 844 reads of 120 stat ids, 17 634 requirement checks,
  5 749 set lists, 19 525 aprop toggles, 8 832 passive lists, 5 752 rescales, 3 643 applies, 2 749 expiry runs (123
  lists freed, lateness 0), 54 719 ticks, 6 207 aura durations, 450 group clears, 7 shrines, 5 wells. Ops in
  predicted writes 1 348, 2 1 490, 4 2 568, 5 26, 8 919, 9 3 784, 11 92, 13 136. Seed invariance: link 12 868,
  unlink 12 853, own write 101 995, toggle 19 525, apply 6 232, expire 2 749, tick 54 719, aura 2 763 unchanged;
  aura 865 runs chained (Sanctuary's `RNG_RangeB`); shrine 7 and well 5 below 20.
  **Raised:** the ethereal −10 decides 30 requirement checks (`StatsBarD`; a second session, `bard-town2`, was added
  for the count) → `[C]`; the stat-74 tick under poison (1 082 ticks, `StatsPalC`) → `[C]`; the `monsterset` group
  clear with the self argument (180 effective clears, `StatsNec`) → `[C]`. **Kept `[I]`, named:** the
  `item_req_percent` term (814 checks, none decisive); the life floor at 256 and open wounds (not reached); a clear
  of a *different* state of one group (no group-3 pair on one unit); shrines and wells, **12 operates against 50**
  (every one predicted: 3 timed shrines, 4 recharge shrines on a full player, 5 wells), their "no draw" too; the
  summary shrine bullet of stats/0002 was lowered from `[C]` to `[I]` for that count. The 180 full Trang-Oul's set
  lists (`state` and `oskill` blocks) are taken as logged: a tool limit, named in the record.
  **Tool changes** (`27f49ad`): `tools/stats.py` predicts wells (`Parm1 · max >> 8`, capped, the return) and the
  recharge shrines 1–3, splits the life tick by the sign of stat 74 and the requirement cases by dexterity, and resets
  events left open at a log's end (a killed session's open aura run was carried into the next log when the logs were
  checked in another order); `tools/stats_sessions.py` gains `bard-town2`.
  **Oracle replacement:** run:2026-10-16-player's level-up maxima: 13 of 20 equal the own entries (replaceable), 7
  need item lists the logs lack; run:2026-10-16-combat logs values only: not replaceable.
  **Findings:** stats/0001 § 9 and stats/0002 § 8 written; summaries split (stats/0001 {C 8, I 40, L 13} →
  {C 22, I 44, L 11}; stats/0002 {C 7, I 41, L 9} → {C 14, I 49, L 8}); answered open questions struck (itemspecific,
  weapon switch, one event 12 per request). Both slots stopped and empty; no background loop left.
  **Review request** filed to the architect (backlog).
- **2026-10-17 — Phase 2 reviewed (architect, `lane/p41h`, `main` `af90ea8` merged in): accept with fixes; P3
  opens.** Merge clean (no `docs/backlog.md` or `re/symbols.csv` conflict; `backlog.py migrate` moved nothing).
  **Re-runs.** Manifest: the 18 logs re-hashed (sha256, size, line count) and the run list, manifest and report hash
  to the record's `a42758f3…`, `7fd7a93a…`, `677e12a6…`. `tools/stats.py check` under `systemd-run --user --scope -p
  MemoryMax=4G python3 -I` over the 18 logs: in the run's order the report is byte-identical to `s1017-check.json`
  (0 mismatches); reversed and shuffled (`random.Random(41)`): 0 mismatches, identical counts and seed tallies (only
  the aura grid's cross-log gaps and the report's first 20 wells differ). The pre-fix checker (`27f49ad^`, scratch
  copy) on the shuffled order fails once (`aura_rng` at `s1017-pal-tundra.log:613`: `palc-oasis` ends inside an
  aura run), so the per-log reset is the fix and is sound. `test_stats.py` (6) and `test_d2s.py` (45) pass. Gate
  green before and after.
  **Anchors** (objdump on the pinned `game.exe`, `631066c1…`): the well entry 0x00585720 (`push ebp`) and its only
  return 0x0058589B (`ret 8`); `OBJOP_Shrine`'s two returns 0x00583CA4 and 0x00583E65 are its only `ret`s;
  `STATE_GroupClear`'s returns 0x0056C82F and 0x0056C83A; the seven aura-tick returns the logger stops at are the
  seven `ret 8` of 0x0056FCB0–0x0056FEFF; `EVENT_TimedListExpire` returns at 0x0058080D and the tick at 0x00580855;
  0x005CF5D5 calls `SKILLS_RollElemDamage` (return 0x005CF5DA, the logger's `ra2`), which calls `RNG_RangeB` at
  0x0056E132.
  **Rulings.**
  1. *Shrines and wells:* a **named shortfall**, no addendum required for P3. Their claims are a table read and two
     short handlers, already `[I]` with code anchors, and the spec can state them so; 12 operates (7 shrines, 5
     wells) are below the 50 and the draw-freedom floor (7, 5 against 20). The 4 recharge shrines were all on a full
     player, so none decided: the summary now says so. An optional addendum (a shrine-and-well hunt with lowered
     vitals, an aura state's end, a different-state group clear) is filed for an idle slot.
  2. *Trang-Oul's lists:* acceptable, but **not as an ADR-0004 oracle**: the set list is in-scope code, which
     ADR-0004 never oracles. The 180 lists are an unchecked remainder taken as the input of the predicted events
     after them (as an ADR-0014 value oracle is), excluded from the Sets count (5 569 of 5 749), seeds checked around
     them; the content of a full block with a `state` or `oskill` property stays `[I]` (stats/0001 summary now says
     so). The record names it. Predicting the other blocks of those lists is a tool follow-up.
  3. *Checker fix:* sound (re-runs above).
  4. *Oracle replacement:* **does not hold**. `oracle-player` compares the logged maxima with the own entries and
     calls the 13 equal ones replaceable; but the 14 level-ups of built characters carry 9 or 10 items and the new characters
     their starting items, the logs hold no child list, and "no linked child adds to 7, 9 or 11" is concluded from the
     equality itself. A consistency check, not a prediction: **none of the 20 is replaced**, the maxima stay value
     oracles of run:2026-10-16-player, the combat logs are not replaceable either. The done-when asks the record to
     name what could and could not be replaced, which it now does.
  5. *Done-when:* **met**, with named shortfalls. Seed invariance ≥ 20 for link, unlink, own write, toggle, apply,
     expire, tick and aura; shrine 7 and well 5 named. The aura kind moves the caster's seed (one `RNG_RangeB` per
     Sanctuary hit), so it takes the chaining minimum: the checker asserts each of the 865 drawing runs' exits against
     the logged draws, and the review counted **746 chained pairs** (the next run of the same caster entering on that
     exit; the record had called the 865 "chained"). Counted shortfalls the record had not named: expiries as freed
     lists 123 against 300 (the 2 749 event-12 runs check the free set), aura on/off events 9 against 50 (Prayer's
     and Sanctuary's states never ended), both under rules that are `[C]` on these counts.
  6. *Raises:* Q5 ethereal −10 (30 decisive checks, a reading without it fails each), Q11 poison tick (1 082, `hp +
     stat 74` with a negative 74; a reading that ignores negatives fails each) and Q10 `monsterset` self-clear (180;
     the "other states only" reading keeps the bit) stand at `[C]`; each split has its remainder at `[I]` (stat 91,
     level, class, broken; the 256 floor, open wounds; a different state of the group). Counts recomputed after the
     merge: stats/0001 {C 22, I 44, L 11}, stats/0002 {C 15, I 49, L 8} (one `[C]` bullet added to § 7 below).
  7. *Symbols:* 29 rows raised `I` → `C`, each a logged breakpoint or a function whose writes the run predicted, with
     the code reading as the other source: `STATLIST_LinkToUnit`, `STATLIST_Unlink`, `STATLIST_Propagate`,
     `sub_006266C0_StatRecompute`, `STATLIST_CacheAdd`, `STATLIST_CacheWrite`, `sub_00624F60_StatListGetValue`,
     `ITEMSTATCOST_Load`, `UNIT_ToggleStatListByState`, `sub_0055DBC0_EquipReqRefresh`, `sub_0062EAF0_ItemReqCheck`,
     `SETS_UpdateOnEquip`, `SETS_ToggleItemAProps`, `SETS_UpdateOwnerBonusList`, `sub_00660120_SetBonusApply`,
     `SETS_WornMemberMask`, `STATE_ApplyTimed`, `STATE_GroupClear`, `EVENT_TimedListExpire`, `UNIT_ExpireTimedLists`,
     `sub_00580810_RegenEvent`, `sub_00580610_LifeRegenTick`, `PLAYER_StaminaRegenTick`, `PLAYER_ManaRegenTick`,
     `EVENT_SelectedAuraTick`, `EVENT_ItemAuraTick`, `SKILLS_NextPeriodicFrame`, `AURA_ApplyToTarget`,
     `SKILLS_RefreshPassive`; the findings' *Functions* tags follow. Left at `I`: the shrine and well code
     (shortfall), `STATE_Set` and the bit helpers, the readers' base-value half, the damage-stat toggles, the maxima
     getters, `sub_005CF3A0_AuraHitDo` and `SKILLS_RollElemDamage` (located by return chains, their own work phase 3's).
  **Fixes applied on the lane** (9): overclaim 1 (the oracle replacement); misread 2 (the 865 exit-asserted runs
  called chained pairs; "the game seed never moved" in the aura bullet, against the checker's one kill-drop run);
  stale cross-reference 1 (stats/0002 § 7's aura row and "no event kind draws", corrected with an anchored `[C]`
  bullet; the summary's aura bullet gains the draw); omission 3 (the expiry and aura on/off counts; the Trang-Oul's
  remainder in stats/0001's summary); under-claim 1 (29 symbol confidences and the *Functions* tags); other 1 (the
  recharge shrines' non-decisive match). The record gains the review's re-check and the "not an oracle" note.
  **Follow-ups filed** (backlog): reverser, tools (the chained-pair count, the per-log aura grid, tests for the
  well, refill, negative tick and reset, the full Trang-Oul's stat blocks, `oracle-player`'s wording or its
  precondition); reverser, optional harness addendum (shrines and wells, an aura state's end, a different-state group
  clear). **P3 opens** (spec-writer queue order) with these rulings: the shrine, well, `item_req_percent`, 256-floor
  and different-state group claims are `[I]`, and the stats oracles of plans 0034 and 0037 stay oracles.
- **2026-10-17 — Phase 3 drafted (spec-writer, `lane/p41s`, from `main` `f4b2aaf`).** Three new specs, status `draft`:
  [stats](../../specs/stats/README.md) (overview: files, entry points, the P2 boundary, draw order; {C 13, I 4, L 3}),
  [stats/aggregate](../../specs/stats/aggregate.md) ({C 62, I 42, L 5}; § A tree, § B link/unlink/toggle, § C propagation
  and `StatRecompute` with the take-test quirk and the zero-source early write, § D op 1–13, § E the loader's op graph,
  § F reads, § G maxima, rescale and callback, § H items, requirements with the ethereal −10, the refresh and its
  136-frame period, per-level item values not refreshed on level-up, § I dual wield, § J set bonuses, § K passives,
  draw order; four worked examples) and [stats/states](../../specs/stats/states.md) ({C 43, I 44, L 6}; § A bit and list,
  § B the timed apply as a decision diagram, § C expiry (one event per request) and removal with the lifecycle state
  diagram, § D the group clear with the self argument, § E the tick (order diagram, stat-74 sign, 256 floor `[I]`),
  § F auras (grid, `perdelay + 1`, stacking, the shortfall), § G shrines and wells all `[I]`, § H draws per kind; four
  worked examples). The P2 splits are kept: the full Trang-Oul's block content `[I]` (an unchecked remainder, not an
  oracle); the oracle maxima of plans 0034/0037 stay value oracles; aura draws `[C]` with the 746 chained pairs;
  shrines and wells `[I]`, the recharge shrines deciding nothing; the expiry (123 of 300) and aura on/off (9 of 50)
  shortfalls named; "no draw" `[C]` for link, unlink, own write, toggle, apply, expire, tick and aura, `[I]` for the
  group clear, removal, shrines and wells. The op 6/7 contradicted lead is stated as 1.14d behaviour under *Open
  questions*. Folded (one reverser entry closed): player/creation {C 81, I 44, L 3} → {C 81, I 45, L 2} (open
  question 4 struck, I2–I3 note), items/properties {C 129, I 35, L 3} → {C 130, I 35, L 2} (B3 when worn; open
  question struck), combat/delivery {C 50, I 39, L 4} → {C 52, I 38, L 3} (the player's life tick `[C]` under
  poison, the floor `[I]`; the state end struck), combat/README {C 36, I 21, L 5} unchanged (the phase (2) question
  pointed to stats, a narrower `[L]` kept), monsters/stats {C 104, I 57, L 4} → {C 105, I 57, L 4} (E3, the callback's
  stats 9 and 11), data/calc {C 129, I 17, L 3} → {C 130, I 18, L 3} (what `stat(id, k)` reads), items/uniques-sets
  {C 71, I 55, L 4} unchanged (downstream link). Research-map rows `stats/aggregate` and `stats/states` set to
  `draft spec`, the touched rows' counts updated; five glossary terms. No wiki page (ADR-0012: the specs are not
  reviewed); follow-up filed to the spec-writer, and `docs/wiki/items.md` keeps a W4 staleness warning until then.
  Open questions: 14 `[L]` over the three specs. Gate green. Review request filed (backlog).
- **2026-10-17 — Phase 3 reviewed (architect, `lane/p41s`, `main` `407758a` merged in as `bc5d7f5`): accept with
  fixes; plan closed.** Merge clean (no `docs/backlog.md` conflict). Gate green before and after.
  **Anchors** (objdump on the pinned `game.exe`, `631066c1…`): the starts of 28 functions the specs cite (the link,
  unlink, toggle, add, set, propagate, cache, recompute, set, apply, expiry, group, tick, aura, grid, shrine, well,
  callback, requirement and passive entries) are function prologues; the stat-98 branch 0x0055BD8F–0x0055BDC4, the 256
  floor 0x0058065B–0x0058066E, the grid 0x0056CD50 (`p ≤ 5 → 5`, signed `idiv`), the requirement check (stat 91 at
  `+0x10A`/`+0x10C`, `MulDiv`, `0x400000`, two `sub 0xA`), the curse rules (stat 109, `cmp 0x64`, `MulDiv`, state 57),
  the stamina jump table 0x005805B8 (modes 1–6 → 8, 9-if-≥256, b-test, b-test, 8, 9) all match.
  **Rulings on the lane's points.**
  1. *`StatRecompute`'s order (C4):* the finding's wording and the checker's model were not enough alone, but the
     instructions settle it, read at the review: evaluate (0x006266D0); no `+0x51`: write and return; `v = 0` written
     at once (0x00626708); per target the target's own `StatRecompute` (0x00626775) then its `CacheWrite`
     (0x00626786), the take test only for a non-zero result by the **source** row's op byte through the class bytes
     0x0062690C (`00 05 01 01 02 02 03 03 00 00 00 00 05 04`) and the jump table 0x006268F4; then, no target taken and
     `v ≠ 0`, the source's write (0x00626868) and the `+0x5E` dependents (≤ 64). That is the order C4 states; with the
     run's in-order writes it stands at `[C]`. Written into stats/0001 § 3 as an `[I]` instruction line and into C4 as
     an anchored step note. The take tests read the list's `+0x08` (owner type), not its unit: C5 and D1 say so now.
  2. *Set block mapping (J4):* not resting on the model alone. `SetBonusApply` walks `b < 2·min(n, members − 1) − 2`
     over 16-byte quads from record `+0x010` (0x006601A8–0x006601F1) and the full quads from `+0x090`; the compiled
     record holds the partial quads in `.txt` order (Sets § Bonus blocks, `[C]` by the layout diff). Three legs: J4
     gains the anchored step note.
  3. *Worked examples:* arithmetic re-done. Aggregate 1 (115..124 against 125 − 10), 2 (Civerb's `m = 2` → 0..1;
     Immortal King 3 worn → 0..3, 1 worn → none), 3 (`16 × 10 × 64` = 10 240 = 40 life), 4 (30 720 ÷ 25 600 × 12 800 =
     15 360 in float32 and in x87 precision); states 1 (5 001 → 5 051, duration 51, end 5 052, refresh to 5 102),
     3 (230 400 ÷ 3 000 = 76, `MulDiv(76, 358, 100)` = 272), 2 and 4 restate the run's counts. None claims a new rule.
     States 1 and 3 were not labelled illustrative as the request said: labelled now.
  **Against the findings and the P1/P2 rulings:** the Trang-Oul's full blocks `[I]` (an unchecked remainder, not an
  oracle), the maxima of plans 0034/0037 value oracles (none replaced), the aura draw `[C]` with 746 chained pairs,
  shrines and wells `[I]` with the recharge shrines deciding nothing, the expiry 123/300 and aura on/off 9/50
  shortfalls named, ops 3, 6, 7, 10, 12 `[I]`, op 6/7's contradicted lead under *Open questions*, "no draw" `[C]` for
  the eight kinds at ≥ 20: all at the findings' strength. Touched specs: each changed statement matches stats/0001,
  stats/0002 or the run record. No `[L]` above *Open questions* in the ten specs; every front matter recounted by script
  and by the gate (E6). Diagrams: two carried more or less than the text (below), fixed.
  **Fixes applied on the lane** (9): omission 4 (C4's instruction anchors; J4's layout and loop anchors; D2's
  has-state condition on both branches and the `off` on the zero branch, 0x0055BD94–0x0055BDBF; the lifecycle
  diagram's stay-on-death case); misread 3 (C5 and D1 "the list's unit" for the owner type `+0x08`; the
  reimplementation note that the second write "matters for the callback count": it changes nothing unless the target
  is a taking source, none in stock data; the overview diagram's dependent walk missing `v = 0`); overclaim 2 (E3's
  pseudocode `[C]` over the unreached modes 2/6 and `b ≥ 1000`, now a line marked `[I]`; states examples 1 and 3
  unlabelled). Counts: stats/aggregate {C 62, I 42, L 5} → {C 64, I 42, L 5}; stats/states {C 43, I 44, L 6} →
  {C 43, I 46, L 6}; stats/0001 {C 22, I 44, L 11} → {C 22, I 45, L 11}.
  **Status:** stats, stats/aggregate and stats/states set to `reviewed`; "(plan 0041, draft)" in the six touched
  specs made "(plan 0041)"; the research-map rows rewritten whole. Wiki W4: `docs/wiki/items.md` claims nothing about
  `add func` when worn, so its `based_on` date for items/properties was moved to 2026-10-17 at the review (no text
  change); the stats page and the combat refresh stay with the spec-writer (backlog entry, unblocked now).
  **Done when:** template followed; every statement tagged; the list kinds and summing order as diagrams (§ A, the
  overview); each `op` as pseudocode (D1); the maxima (G); the set activation (J); the lifecycle as a state diagram
  with durations in frames (states, § C1, example 1); worked examples from the run. Met. **Close:** the *Open
  questions* entry on plan 0038's d-sim rows: data/calc's `stat()` read is now `[C]` (what it returns), its
  unit-reading codes stay value inputs; the monsters/stats rows wait for a logged damaged monster, which this run (the
  player's tree only) did not reach. Plan moved to `done/`, links rewritten, index and research map updated, the
  review request closed. Follow-ups open: spec-writer (wiki page and refresh), reverser (shrine-and-well addendum;
  checker chaining count and tests; op 6/7 emulation, optional).
- **2026-10-17 — Wiki page written (spec-writer, `lane/wiki7`, from `main` `a3a5abe`).** The backlog entry
  [plan-0041-wiki-after-review](../../backlog/2026-10-17-spec-writer-spec-writer-plan-0041-wiki-after-review.md) is
  closed: [wiki/stats-and-states](../../wiki/stats-and-states.md) (new, `based_on` the three stats specs at
  2026-10-17, 16 sections, four diagrams, six worked examples from the specs), indexed in the
  [wiki README](../../wiki/README.md) (stats and states now covered, the second simulation row), and linked from
  [wiki/combat](../../wiki/combat.md) (inputs, the player's life tick, *not known*) and
  [wiki/characters](../../wiki/characters.md) (the level-up maxima). Review requested:
  [wiki7 review](../../backlog/2026-10-17-spec-writer-architect-wiki7-stats-and-states-review.md).
  - **Next:** architect review of `lane/wiki7`.
