# 0045 — Skills and missiles, the machinery: dispatch, packets, missiles, event handlers (ADR-0014 phase 3, part 1)

> **Status:** approved 2026-10-20 (owner)
> **Created:** 2026-10-20
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0007-fetched-leads-only, 0011-harness-slots, 0013-forced-path-runs-cell-level, 0014-scope-game-simulation, 0015-emulated-reproduction, 0016-pipelined-simulation-phases, 0020-skills-phase-in-two-plans

## TL;DR

**Question:** when a unit uses a skill, what does the server do, frame by frame, until the skill's effects are
resolved: which checks let it start, which function runs on which frame, which damage packet it builds, which
missiles it creates and how they move, collide and hit, which stat-event handlers fire, which units it summons, and
which seeds it draws on? This is phase (3) of [ADR-0014](../adrs/0014-scope-game-simulation.md), part 1 under
[ADR-0020](../adrs/0020-skills-phase-in-two-plans.md). When it is done:
- the Missiles table and the dispatch columns of Skills are documented, with a survey;
- `docs/findings/skills/0001-dispatch.md` and `docs/findings/skills/0002-missiles.md` name the machinery;
- `tools/skills.py` reproduces skill-use, missile and event-handler events of a run per event;
- `docs/specs/skills/` (overview, `dispatch`, `missiles`) is reviewed, and the skill and missile oracles of
  [combat](../specs/combat/README.md), [stats/states](../specs/stats/states.md), [data/calc](../specs/data/calc.md),
  [rng/seeds](../specs/rng/seeds.md) and [items/economy](../specs/items/economy.md) are replaced where the kept logs
  hold what the model needs.

The boundary: **the machinery and a named tier A of skills** are in this plan. What each of the remaining numbered
skill and missile functions does is plan [0046](0046-skills-function-catalogue.md). Which skill a monster chooses,
and when, is phase (4) (an input here); the frame on which an animation reaches its action frame is phase (5) (a
logged input here, stated in game frames).

## Context

- **The gate is open.** Phase (2) is [plan 0041](done/0041-stats-and-states.md), closed 2026-10-17 with
  `stats/aggregate` and `stats/states` reviewed, so ADR-0014 lets this plan be written and ADR-0016 lets all its
  phases run, P2 included.
- **Research map rows** (added when the plan starts, Simulation band): `skills/dispatch` and `skills/missiles`, and a
  third row `skills/catalogue` owned by plan 0046 (ADR-0020 § Negative). The wiki owner is Phase 4 below.
- **Oracles this plan replaces** (counts are files / occurrences across specs and findings, survey of 2026-10-20):
  `MonAttackStats` outputs (7/64); the non-crushing stat-event handlers 7, 8, 11, 19 and the kill handler 9 (5/38);
  `MISS_CalcVar` 19–27, the damage getters not cased by data/calc (5/32); `SKILLS_EvalCalc` and `skill(s, v)` in
  context (10/24, 6/29); the `srvdofunc` skill packets (6/24); `PLAYER_UseAmmo` and `SkillWeaponWear` (2/20, 2/11);
  `edPct` and `SKILLS_GetToHit` (3/17, 6/16); `MISSILE_ApplyDamage` and `MISSILE_HitUnit` (4/14, 3/8); `SrcDam`
  (3/11); `SKILLS_ForUnitsInRange` (3/11); `AuraHitDo` (3/8); `MonOnHitSkill` `0x005A4390` (4/7); the conversion fields
  `+0x65`/`+0x68` (3/3); knockback `0x005D10C0` (2/2). The full combat boundary is
  [combat § Inputs](../specs/combat/README.md), its open question "Owed to phase (3)".
- **Open questions this plan answers by name:**
  - the prevent-heal state 52 (stat 117, *Fleshripper*): which call applies it between `COMBAT_ToHitRoll` and the
    defence roll ([combat/0001](../findings/combat/0001-formulas.md) *Open questions*; backlog
    `2026-10-17-reverser-reverser-a-read-which-call-applies-the.md`);
  - the event-9 (kill) handler at `0x005C01D0` that runs inside delivery before `AD1` and explains the 101 remaining
    mismatches of the set-aside *Fleshripper* session (same entry; backlog
    `2026-10-17-architect-reverser-plan-0037-resume-lane-review-follow.md` (a) for the log copy);
  - the skill and missile re-seed sites of `+0x20` (`0x005ACDF0`, `0x005C9290`, `0x005D40F0`, `0x005D5BF0`, the call
    at `0x005AC073`, the shared `0x00645390`) and the eight register-held server seeds of
    [rng/0002 § Plan 0039 batch P1a](../findings/rng/0002-seed-tree.md#plan-0039-batch-p1a-2026-10-16), routed here by
    the research map and [rng/seeds](../specs/rng/seeds.md) *Open questions*;
  - the reader of the missile `0x40` collision mark ([drlg/collision](../specs/drlg/collision.md) *Open questions*);
  - stats/states' Holy Shield, progressive charges and timed self-states, the damaging aura's hit (`AuraHitDo`,
    `SKILLS_RollElemDamage`; one `RNG_RangeB` per hit, already `[C]` on 746 chained pairs), the aura request's
    `+0x48` and `SKILLS_ForUnitsInRange`'s monster exclusion flag ([stats/states](../specs/stats/states.md)
    *Open questions*);
  - items/economy's `PLAYER_UseAmmo` gates and `SkillWeaponWear` ([items/economy](../specs/items/economy.md)
    *Open questions*);
  - data/calc's BearSmite cast and `MISS_CalcVar` 19–27 ([data/calc](../specs/data/calc.md) *Open questions*);
  - the `MonAttackStats` formulas still owed by combat (combat *Open questions*, monsters/stats § H).
- **Code already named** (grep `re/symbols.csv`, 2026-10-20: about 100 skill and missile rows): `SKILL_AttackStart`
  `0x0056CA40` and `SKILL_AttackDo` `0x0056F070` (`[C]`), `SKILLS_ForUnitsInRange` `0x0056B7E0`,
  `SKILLS_NextPeriodicFrame` `0x0056CD50`, `SKILLS_RollElemDamage` `0x0056E0C0`, `STATE_ApplyTimed` `0x0056E970`,
  `sub_005CF3A0_AuraHitDo`, `sub_005D9C80_MonSkillAttackDo`, `sub_005A4F50_MonAttackStats`,
  `sub_0059FA30_MissileCreate`, `MISSILE_BuildDamage` `0x005A89A0`, `MISSILE_ApplyDamage` `0x005AD730`,
  `MISSILE_HitUnit` `0x005ADF10`, `sub_005AEDA0_MissileSpawnOwnedMonster`, `UNIT_DispatchEvent` `0x005C0C30`,
  `g_StatEventFuncs` `0x007325B0`, the data/calc getters (`SKILLS_GetToHit`, `SKILLS_GetElemMin/Max/Len`,
  `SKILLS_CalcVar`, `SKILLS_EvalCalc`, `MISS_GetDamMin/Max`, `MISS_GetElem*`, `MISS_CalcVar`, `MISS_EvalCalc`),
  `SKILLS_GetMasteryBonus` `0x00645830`; five do-functions (Revive, BoneWall, BonePrison, Teleport, MonTeleport). The
  `srvdofunc` table at `0x007322B0` (cited by combat/0001) has no symbol row.
- **Tools to build on:** `tools/combat.py` (already loads `missiles.bin`, checks `md`/`pm` missile events),
  `tools/gdb/combat.gdb` (a capped "player missile" kind), `tools/combat_sessions.py` (Nova, Energy Shield),
  `tools/stats.py` and `tools/stats_sessions.py` (auras, `pal_field`), `tools/calc.py` and `tools/calc_funcs.py`
  (missile-context emulation), `tools/gdb/calc-<cls>-cast.steps` (cast F1–F8 per class), `tools/callee_writes.py`
  (follows switch tables: fits the do-function tables), `tools/d2pilot.py` (Teleport, Nova, `farm`). Kept logs:
  `workspace/logs/combat/` (1 957 missile-defence events, 519 player Nova missile events, all matching) and
  `workspace/logs/stats/`.
- **The harness limit.** Scripted play casts few targeted skills
  ([harness-play](../../.claude/skills/reverser/references/harness-play.md), "no targeted spells"). Tier A below is
  chosen for what the pilot can cast: self-centred, directional and melee skills, auras and summons.
- **Leads:** none registered yet for skills. Phase 1b searches (ADR-0007: fetched in session only) for skill-damage,
  synergy, missile pierce and range, and summon-limit documentation.

## Phases

### Phase 0 — Missiles and the dispatch columns
- **Owner skill:** archivist
- **What:** document the tables the machinery reads, where the existing docs stop.
- **Outputs:**
  - `docs/tables/Missiles.md` (new; 684 rows, 420-byte records): every column with offset, width and value range;
    the function-number columns (server do, hit and damage functions, client columns marked presentation), the motion
    columns (velocity, max velocity, acceleration, range and its level term, the loop and sub-loop columns), the
    collision columns (`CollideType`, `Collision`, the kill and pierce columns), the damage and elemental columns and
    their calcs, the sub-missile and explosion links (`SubMissile*`, `HitSubMissile*`, `ExplosionMissile`), the
    `Param` columns; the calc offsets already in `tools/excel_layouts.py`;
  - [Skills](../tables/Skills.md) § Dispatch: `srvstfunc`, `srvdofunc`, `srvprgfunc1..3`, `prgcalc1..3`,
    `prgdam`, `srvmissile*`, `cltmissile*` (marked presentation), `param1..8`, `anim`, `seqtrans`, `monanim`, `seqnum`,
    `delay`, `range`, the mana columns, `InTown`, `ItypeA*`/`ItypeB*`/`EtypeA*`, `weapsel`, `leftskill`, `repeat`,
    `TgtPlaceCheck`, `summon`, `pettype`, `summode`, `sumskill*`, `sumsk*calc`, `petmax`; which rows use each
    function number, printed per number; the stale line 6 ("no skills subsystem is planned") rewritten;
  - `docs/tables/PetType.md` (new): the summon-limit columns the summon code reads;
  - `tools/skills_survey.py` (gate survey `skills`): rows per `srvstfunc`, `srvdofunc`, `srvprgfunc` and missile
    function number, the family sizes Phase 1 batches by, the tier-A rows below.
- **Done when:** each named section lists every column it claims with offset, width and value range; the survey's
  `SURVEY` line matches the docs; meanings stay `[L]` unless a finding anchors them; the `excel_layout` baseline is
  regenerated if a layout changed; the gate is green.

### Phase 1 — Read the machinery
- **Owner skill:** reverser
- **What:** read the skill path from the request to the last effect, the missile life from creation to removal, and
  the stat-event handlers.
- **Outputs:** `docs/findings/skills/0001-dispatch.md`, `docs/findings/skills/0002-missiles.md`,
  `docs/findings/skills/experiments.md` (empty heading); `re/symbols.csv` rows (subsystems `skills/dispatch`,
  `skills/missiles`), the `0x007322B0` table among them; `re/types/skills.h`.
- **Done when:** the findings state, each with addresses and `[I]` or better:
  - **dispatch:** the request (left and right skill, the client packet's server handler), the start checks (mana,
    `delay` and cooldown state, `InTown`, weapon class, target place), the start function (`srvstfunc`) and the do
    function (`srvdofunc`) tables and the frame each runs on relative to the mode's action frame (the frame is a
    logged input until phase (5)), progressive charges (`srvprgfunc`, `prgcalc`), mana and life costs and their
    rounding, the `repeat` and channelled forms, charged and item-granted skills (`ctc` events, charges);
  - **the skill packet:** how a skill attack builds its damage packet from the weapon, `SrcDam`, `edPct`, the
    elemental min/max/len getters, the mastery bonus and the synergy calcs; the conversion fields `+0x65`/`+0x68`
    and their writer; the to-hit term (`SKILLS_GetToHit`), so that combat's packet oracle has a model;
  - **missiles:** creation (`MissileCreate` and its callers: skills, items, monsters, objects, shrines that create
    missiles), the missile's own seed and how it is initialised, per-frame motion (velocity, acceleration, range,
    loops), the collision test against the room grids and units (the `0x40` mark's reader), the hit
    (`MISSILE_HitUnit` → `BuildDamage` → `ApplyDamage`, the knockback roll), pierce, sub-missiles and explosions, the
    end of life; the server do, hit and damage function tables;
  - **event handlers:** `UNIT_DispatchEvent` and `g_StatEventFuncs` for every event kind other than 14–16 (skill on
    hit, knockback 7, howl 8, kill 9, 11 with energy shield and the bone and cyclone armours, slow 19 and the rest),
    `MonOnHitSkill` `0x005A4390`; the event-9 handler `0x005C01D0`; **which call applies state 52**, with its place
    in delivery;
  - **summons:** a skill that creates a monster (raise, revive, golems, valkyrie, spirits, `MissileSpawnOwnedMonster`),
    the `pettype` limit, the created unit's seed and its hand-off to [monsters/spawn](../specs/monsters/spawn.md) and
    [monsters/stats](../specs/monsters/stats.md);
  - **monster skill use:** `MonSkillAttackDo` and the `MonAttackStats` formulas (the stats it writes), with the AI's
    choice as an input;
  - **the re-seed sites** of rng/0002 Q15: which skills re-seed `+0x20` or another object's seed, from what;
  - **ammunition and wear:** `PLAYER_UseAmmo`'s gates and `SkillWeaponWear`;
  - **from Phase 0's survey** (added 2026-10-20, archivist): the 50 Skills rows that name a server missile and have no
    `srvdofunc` (6 Magic Arrow, 36 Fire Bolt, 251 Fire Trauma, …): which code creates their missile; the progressive
    rows 254 Tiger Strike and 265 Cobra Strike, with `prgdam` and no `srvprgfunc`; Missiles row 568's server hit
    function 64 948 (the `.txt` cell `*12`): bounds test, out-of-table call or unreached
    ([Skills § Dispatch](../tables/Skills.md#dispatch-plan-0045-phase-0), [Missiles](../tables/Missiles.md#encodings-particular-to-this-table));
  - **tier A**, the skills Phase 2 reproduces, fixed at this phase's review from the survey: the general rows
    (Attack, Kick, Throw, Left Hand Throw, Left Hand Swing); per class at least two skills the pilot can cast
    (self-centred, directional, melee or summon; for example Nova, Frost Nova, Static Field, Teleport, Fire Bolt;
    Bash, Howl; Jab, Multiple Shot; Raise Skeleton, Bone Armor; the Paladin's Holy Fire and Holy Shield; a Druid and
    an Assassin pair); every function family with ten or more stock rows represented once; the monster skills of the
    combat logs' attackers. **Phase 0 review ruling (2026-10-20):** the 26 candidate rows of
    [Skills § Dispatch](../tables/Skills.md#families-and-the-tier-a-candidates) are this phase's starting list: the
    Druid pair 221 Raven, 225 Firestorm and the Assassin pair 251 Fire Trauma (*Fire Blast*), 259 Fists of Fire are
    accepted; of the four family rows, 98 Might (aura) and 25 Plague Javelin (directional, like Throw) are accepted
    as castable, and 56 Meteor and 66 Amplify Damage (cast at a point or a unit) are accepted on condition that
    Phase 2 casts them with the pilot's attack click at a monster's screen position (plan 0037 Phase 2); if it
    cannot, the Phase 2 lane says so and this phase's review substitutes another row of the same `srvdofunc`
    family (28 or 30). Phase 2 equips a claw for 259 (`itypea1` `h2h`, `weapsel` 3) and javelins for 25
    (`itypea1` `jave`);
  - for each event kind (start, do, progressive, missile create, move, collide, hit, handler, summon), its inputs,
    outputs, draws, seeds and the chaining reading (ADR-0014);
  - the community cross-check (Phase 1b) done;
  - **the boundary recommendation** for Phase 2: which values stay value oracles (AI choices, the action frame, the
    catalogue functions outside tier A), the event entry points, the log windows (missile motion is a per-frame
    path: ADR-0014 § Log volume). The architect rules at the review.
- **Batches.** This phase is larger than one lane run: run it as **P1.1** (dispatch, packets, monster skill use, ammunition
  and wear), **P1.2** (missiles) and **P1.3** (handlers, summons, re-seeds, tier A and the boundary recommendation),
  each its own lane and review, in that order; lanes rotate past about 4 h (owner rule). Phase 1b may run beside any
  of them.

### Phase 1b — Community cross-check
- **Owner skill:** reverser
- **What:** search for and register skill-damage, synergy, missile and summon-limit documentation; compare blind.
- **Outputs:** `docs/sources.md` entries with the game version each describes; verdicts in the findings' *Leads used*.
- **Done when:** each compared claim carries one verdict; every `contradicted` claim reachable on stock data is a
  required case of Phase 2; agreement promotes nothing.

### Phase 2 — Per-event reproduction
- **Owner skill:** reverser (agent-driven; **at most two slots**, given in the prompt; not while plan 0044·P2 holds
  both)
- **What:** write `tools/skills.py` (model and `check`), `tools/gdb/skills.gdb` and its handler, the tier-A character
  recipes (tool-built, stock items and skill points, ADR-0013 § Neutral), and log a run.
- **Done when:** `run:YYYY-MM-DD-skills` reproduces with **0 mismatches** over at least:
  - 2 000 skill uses across every tier-A skill (at least 30 each), the start checks' refusals among them (mana,
    delay, town), with the action frame logged;
  - 1 500 missile creations, 300 missiles followed from creation to removal with their positions per logged frame in
    a stated window, 500 missile hits with the packet predicted, 100 collisions that end a missile, 50 pierces, 50
    sub-missiles or explosions;
  - 300 stat-event handler fires over at least five event kinds, event 9 among them, and the state-52 apply;
  - 100 summons with the created unit's seed and stats predicted to the monsters/stats boundary;
  - 200 monster skill uses with `MonAttackStats` predicted;
  - 50 re-seed events at the Q15 sites;
  - **chaining (ADR-0014):** for every event kind that draws, at least 20 chained pairs; a kind with none keeps its
    draw-order claims at `[I]`;
  - **the oracle replacement:** run:2026-10-16-combat (its skill and missile events), run:2026-10-17-stats (the
    aura hits) and the *Fleshripper* session (once its log is under `workspace/logs/combat/` with a manifest hash)
    re-checked with the packet, handler and missile oracles replaced by `tools/skills.py` where the logs hold what it
    needs; the record names what could and could not be replaced;
  - the Phase 1b cases.

  Rare-branch minimums (about 30 each) may fall short, named in the record with their counts; their claims stay `[I]`.

### Phase 3 — Spec: skills
- **Owner skill:** spec-writer
- **What:** write `docs/specs/skills/README.md`, `skills/dispatch.md` and `skills/missiles.md`; update combat (the
  packet, the handlers), stats/states (aura hits, the self-states of tier A), data/calc (19–27 in context), rng/seeds
  (the re-seed sites), monsters/spawn and monsters/stats (summons, `MonAttackStats`), items/economy (ammunition and
  wear), drlg/collision (the `0x40` reader).
- **Done when:** the spec follows the template; every statement is tagged; it has the skill's life as a sequence
  diagram per event kind, the start checks as a decision order, the packet as pseudocode with its integer widths, the
  missile's life as a state diagram with its per-frame motion, the handler table, and worked examples from the run; the
  architect's review passes.

### Phase 4 — Wiki page: skills
- **Owner skill:** spec-writer
- **What:** `docs/wiki/skills.md` (ADR-0012) over the reviewed skills spec, and the reading-order row in the wiki
  index; combat and stats pages cross-linked.
- **Done when:** `based_on` dates current (gate W4); no claim of its own; the architect's review passes.

## Resources and limits

- **Static:** Phase 1 holds **one** of the two static Ghidra lanes (`-Xmx3G`) for its three batches; P0 and P1b need
  no Ghidra. Emulated cases (ADR-0015) run in the same lane's Ghidra.
- **Harness:** Phase 2 takes **two slots from 1–2** (slot 0 is the owner's), at most two games at once across all
  plans; while it holds both, no plan 0038 batch or plan 0047 session runs, and it never overlaps plan 0044·P2.
- **Replays:** the oracle-replacement re-checks of the kept logs run under `MemoryMax=4G`.
- **Rotation:** lanes past about 4 h checkpoint, write a resume note and stop; a fresh lane resumes on the same branch.
- **Estimate** (an estimate, not a measured figure): P1 three lane runs; P2 two to three lane runs of 10–20 sessions.

## Open questions

- ~~**Phase order (owner).**~~ Decided 2026-10-20 (owner): **animation and frame timing is phase (4)**, before
  monster AI (phase (5)). It is small, mostly data (`animdata.d2`, MonSeq, HitClass), and feeds the action frame this
  plan takes as an input; AI is large and may need per-frame observation (ADR-0014's reserve, an injected logger).
  Recorded in [ADR-0020](../adrs/0020-skills-phase-in-two-plans.md) § Neutral.
- **Client-only skills.** Client missiles (`cltmissile*`) and the skill description tables are presentation and stay
  out.
- **Two clients.** Party auras and player-against-player skills stay `[I]` (plan 0044 if it stages them).

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-20 — Drafted (architect, `lane/plans45`).** Status `proposed`, with ADR-0020 (proposed).
- **2026-10-20 — Approved (owner, via the orchestrator).** Plans 0045–0049 and ADR-0020 approved as proposed; the run
  order of the [plans index](README.md#run-order-unattended-queue-set-2026-10-20-plans-00380049) is the current queue.
- **2026-10-20 — Phase 0 landed (archivist, `lane/p45a`).** [Missiles](../tables/Missiles.md) (new): the layout is
  complete, 146 fields over the 420-byte record, `excel_bin.py diff` 99 864 cells, 0 mismatches (the partial
  layout of plan 0035 held the seven calc fields only); every column with offset, width, observed values, grouped as
  the plan names them (function numbers, motion, collision, damage, links, params, presentation); the server function
  numbers printed per number. [PetType](../tables/PetType.md) (new): layout complete (224 B, 400 cells, 0
  mismatches), the 20 rows with the 31 Skills rows that name them. [Skills § Dispatch](../tables/Skills.md#dispatch-plan-0045-phase-0):
  the 75 named columns, the rows per `srvstfunc`/`srvdofunc`/`srvprgfunc` number, the family sizes and 26 tier-A
  candidate rows (the plan's 18 named, a Druid pair 221 Raven/225 Firestorm and an Assassin pair 251 Fire Trauma/259
  Fists of Fire proposed, four rows added for the four families of ten rows or more the named rows miss: 56 Meteor,
  66 Amplify Damage, 98 Might, 25 Plague Javelin); the stale "no skills subsystem is planned" rewritten.
  `tools/skills_survey.py` registered as gate survey `skills` (new baseline). **`excel_layout` baseline changed**
  (regenerated by rerunning `excel_bin.py survey`): `tables` 67 → 68, `records` 11 437 → 11 457, `cells` 850 613 →
  946 089, `missiles_cells` 4 788 → 99 864, new `pettype_cells=400`/`pettype_bad=0`. Meanings stay `[L]` except
  those the findings and the data/calc spec anchor. Surprises, added to Phase 1's *Done when*: 50 missile skills have
  no `srvdofunc`; two progressive rows have no `srvprgfunc`; row 568's hit function cell `*12` compiles to 64 948.
  Families of ten rows or more: eight (`srvstfunc` 4; `srvdofunc` 65, 2, 28, 18, 30; `pSrvDoFunc` 1, 3). Backlog:
  [reverser, the fields three findings left unnamed](../backlog/archive/2026-10-20-archivist-reverser-missiles-fields-named-by-the-table-doc.md);
  review request [to the architect](../backlog/archive/2026-10-20-archivist-architect-lane-p45a-review-plan-0045-phase-0.md).
- **2026-10-20 — Phase 0 reviewed (architect): accept with fixes.** `gate.py --full=excel_layout,skills` and
  `test_gate.py` rerun green after merging `main`; both baselines equal the surveys' output. Anchors spot-checked
  against `re/symbols.csv` and the findings (`MISS_CalcVar`, `MISS_GetDamMin`, `MISS_GetElemLen`, `UNIT_GetSizeX`,
  `PATH_SetMarkMask`, `PermPortalAtUnit`, `SKILLS_CalcVar` `pets`; combat/0001 for `srvstfunc` 42, `srvdofunc` 7 and
  67, `COMBAT_PrgFinisher`, the knockback roll); meanings default to `[L]`, raised only where a finding or data/calc
  anchors them. Fixes (3): the plan names 18 tier-A rows, not 17 (this log and the survey's comment); Skills §
  Families: "the first 22 rows" of the 26; PetType row 17's sentry wording. Tier A: ruling in Phase 1's tier-A
  bullet (all 26 accepted, Meteor and Amplify Damage on the attack-click condition). Notes for P1.1/P1.2:
  [backlog to the reverser](../backlog/archive/2026-10-20-architect-reverser-plan-0045-p0-review-notes-for-p1-1.md).
- **2026-10-20 — Phase 1 batch P1.1 landed for review (reverser, `lane/p45r`, static).**
  [skills/0001-dispatch](../findings/skills/0001-dispatch.md): the request (client packets 0x05–0x11, `PLRMSG_SkillAtXY`
  / `PLRMSG_SkillAtUnit`, stat 328 counted per request, the dual-wield Attack alternation, the `AttackNoMana` fallback,
  the melee-range walk), `SKILLS_CanUse` and its codes, the mode command, start and frame (players and monsters, the
  `Unit+0xC4` bit-6 "action done" flag), `SKILLS_SrvStart` and `SKILLS_SrvDo` with `g_SkillStartFuncs` `0x00732140` and
  `g_SkillDoFuncs` `0x007322B0`, the mana cost and its rounding (`minmana` floors only the payment; the payment's result is
  ignored), blood mana, the delay state 121, periodic and channelled skills, item charges, item auras and item-event casts
  (`ITEMSKILL_Cast`, the `ItemEffect` override), the skill hit packet (the writer of the conversion fields
  `+0x65`/`+0x68`; hits built at the mode start and delivered at the action frame), progressive charges, monster skill
  use and `MonAttackStats`' callers and owner skill damage, `PLAYER_UseAmmo`'s callers and Impale's weapon wear.
  All `[I]` except the two tables and the full-row check (`[C]`). **Correction** carried into combat/0001 § 14: the
  progressive finisher's `RNG_Step` is a peek (seed saved and restored), not a draw; combat/0001's open question on the
  conversion writer answered. 83 symbol rows, `re/types/skills.h`, `tools/skills_dispatch_scan.py` with kept outputs
  (`workspace/logs/skills/p45r-manifest.sha256`). Backlog: review request to the architect, the combat-spec change to the
  spec-writer, the Skills column anchors to the archivist. Open (in the finding): `repeat`'s reader, the ally test's
  inner record, `Unit+0x38`, the `srvprgfunc` entries (P1.3 / plan 0046). Phase 0 (archivist) had not run; this batch
  read the Skills layout from the existing table doc.
- **2026-10-20 — P1.1 reviewed (architect): accept with fixes.** Spot-checked on the pinned image (objdump and an
  independent PE read): the finisher's copy-out / `RNG_Step` / copy-back at `0x005D5374`/`0x005D537B`/`0x005D538C`
  (`sub_00650E70`/`sub_00650E60` move the two seed words to `[ebp−0x20]`/`[ebp−0x1C]` and back); the two tables and
  their bounds (`cmp ax,0x5B` at `0x0056F75D`, `cmp ax,0xBF` at `0x0056F911`; 64 and 152 non-null entries); the cost
  formula in `SKILLS_PayCost` (`+0x18A` mana, `+0x18C` lvlmana s16, `shl` by the `+0x188` byte, the `minmana · 256`
  floor) and the two unchecked calls at `0x0056F7AA`/`0x0056FA7A`. `tools/skills_dispatch_scan.py` rerun: output
  bit-identical to the kept `dispatch-scan.txt`; manifest `sha256sum -c` passes; no lead opened, no foreign code.
  Fixes: the `[C]` on the tables scoped to the data join (column-to-table and bounds stay `[I]` code readings); "30 null"
  reworded (id 30 is the one null start entry below 66); the plan's unread dispatch items (`TgtPlaceCheck`, `prgcalc`,
  `prgdam`, `weapsel`/`leftskill`) routed to P1.3 under the finding's open questions, `SKILLS_GetToHit` pointed at
  data/0005. Gate: the merged branch has main's 25 warnings, its W1 and W3 lists line for line equal to main's, so the
  lane adds none (its 38 were counted before the merge). Rulings: (1) the full-row check plus three independent byte reads
  suffice for `[C]` on the table contents and the stock-row coverage, not on the semantics; (2) the finisher
  correction stands at `[I]`; combat/0001 carries it and the spec-writer entry asks for delivery § A2; Phase 2 keeps
  dropping `PRG` events while the `srvprgfunc` entries are unread; (3) the ignored payment is a Phase 2 case: a
  negative-`lvlmana` row (Teleport, for example) at a level where the unfloored cost passes the checks and mana sits
  between it and `minmana · 256`; expect mana unchanged and the skill run; (4) start-then-do hits are logged as two
  events, each entry seed asserted, the gap between them being ADR-0014's chaining measurement. P1.2 (missiles) may
  start now: it needs `SkillMissileCreate`/`Lob` (`0x0056ECB0`/`0x0056EE90`), the `useAmmo` argument, `0x0064B860`
  and the `ItemEffect` aim offset of § 6, and does not need lane/p45a merged first (it reads Missiles from the binary
  and links `docs/tables/Missiles.md` once that lands). P1.3 picks up the `srvprgfunc` entries and `0x00571AA0`, the
  item-event handlers that call `ITEMSKILL_Cast` (`0x005BF170`–`0x005C0670`), `SKILLS_SrvStart`/`SKILLS_PayCost`
  callers in do functions 83, 109 and `0x005D69D0`, the twelve unmapped `EType` stores, and the routed open questions.
- **2026-10-20 — Combat spec fixes from P1.1 landed for review (spec-writer, `lane/cfix`).** The
  [reverser's entry](../backlog/archive/2026-10-20-reverser-spec-writer-combat-finisher-peek-and-conversion-writer.md)
  closed: [combat/delivery § A](../specs/combat/delivery.md#a-queue-and-delivery) A2 says the finisher peeks the
  attacker's seed (`[I]`, ruling (2)), with a reimplementation note and a new `[L]` for the `srvprgfunc` entries and
  `0x00571AA0`; [combat/damage § D](../specs/combat/damage.md#d-conversion) D1 names the skill hit builders as the
  conversion writers (`[I]`), the old `[L]` struck and a narrower one added; combat/README and
  [wiki/combat](../wiki/combat.md) follow. Tags: delivery {C: 52, I: 38, L: 3} → {C: 52, I: 39, L: 4}, damage
  {C: 34, I: 27, L: 4} → {C: 34, I: 28, L: 5}, README unchanged. Open questions: delivery 3 → 4 live, damage 4 live
  (one struck, one added). No combat or rng call-order table listed the finisher as a draw. Review:
  [request](../backlog/archive/2026-10-20-spec-writer-architect-review-lane-cfix-combat-finisher-peek-and-conversi.md).
- **2026-10-20 — `lane/cfix` reviewed (architect): accept with fixes.** Checked against combat/0001 § 14 (the dated
  correction) and skills/0001 §§ 11–12: the peek's copy-out / `RNG_Step` / copy-back addresses, the `EType`/`calc4`
  store rule of start function 32 and the 3-of-15 mapping match; `sub_00650E70_Copy64Out`, `sub_00650E60_Copy64In`,
  `sub_005D7EA0_SkillSt32Hit`, `COMBAT_PrgFinisher` and `RNG_Step` resolve in `re/symbols.csv`; no other spec or wiki
  page states the finisher as a draw. Ruling on the struck question: an answered open question stays struck as history
  (as in drlg/maze, drlg/lifecycle, objects), but without its tag, so the front matter counts live leads only; damage
  goes to {C: 34, I: 28, L: 4}. Fixes: that tag dropped; A2 states the finisher's gate (queued hit with `0x1`, target in
  melee range, level `max(stat 351, current)` > 0); combat/README A1's peek comment carries `[I]` inside the `[C]` block
  (README {C: 36, I: 22, L: 5}); "the skill hit builders" scoped to "skill hit builders" in damage D1 and README, the
  wiki to "a skill with an element type". The wiki carries no tags or anchors and says "read from the code only". The
  combat specs stay `reviewed`: the change narrows and corrects at `[I]` from reviewed findings and raises nothing.
- **2026-10-20 — Phase 1 batch P1.2 landed for review (reverser, `lane/p45m`, static).**
  [skills/0002-missiles](../findings/skills/0002-missiles.md): `MissileCreate` and its 0x5C-byte request (97 call sites
  in 82 functions: skills, shrines 19/21/22, quests, monsters, missile and skill functions; items only through
  `ITEMSKILL_Cast`), velocity, range, activate, the `0x40` mark and the collide mask at creation; the three skill
  creators and `useAmmo` per call site (1 at `SKILL_AttackDo`, Throw, Left Hand Throw and a few monster/skill
  functions, 0 at `SKILLS_SrvDo`); the `ItemEffect` aim offset (a line missile starts at the target point); the 48
  `srvmissile` rows with no `srvdofunc` (tier A 36, 251, 25) created only by `SKILLS_SrvDo`; the creation-time damage
  block (`0x0064B860`: Missiles or Skills columns, the weapon share, the mastery bonus as enhanced damage, the owner's
  1–3 critical draws, the elemental masteries for `ApplyMastery`); the pierce count from a local seed of stat 328; the
  missile frame (town tests, `g_MissileSrvDoFuncs` bound 53), do function 1 (step, range countdown, cell collision),
  the path's acceleration rule; `MISSILE_HitUnit`'s order, `justhit`, pierce, to-hit, the hit/damage tables (bounds 71
  and 31, tested signed: **row 568's 64 948 is never called**), `BuildDamage`'s draw order on the missile seed; the two
  `CallDoFunc` missile callers (hit 22: a null entry on stock data; do 14: the grim wards' skill do 30 every 6 frames).
  1 `[C]` (the data join), 39 `[I]`, 7 `[L]`. 66 symbol rows (two copied from `main`'s plan 0049 names),
  `re/types/skills.h` missile structs, `tools/skills_missiles_scan.py` with kept outputs
  (`workspace/logs/skills/p45m-manifest.sha256`). Surprises: the critical roll at creation draws on the **owner's** seed
  even with no critical stat; the `0x40` mark has no stock missile reader (`CollideType` 7 unused) and a second writer
  (do 3); `ExplosionMissile` has no server reader by the scan. Backlog: review request
  [to the architect](../backlog/archive/2026-10-20-reverser-architect-lane-p45m-review-plan-0045-p1-2-missiles.md), the Missiles
  columns [to the archivist](../backlog/2026-10-20-reverser-archivist-missiles-columns-anchored-by-skills-0002.md), the
  collision, combat and economy inputs
  [to the spec-writer](../backlog/archive/2026-10-20-reverser-spec-writer-missile-path-inputs-for-drlg-collision-combat-econ.md);
  [the archivist's fields entry](../backlog/archive/2026-10-20-archivist-reverser-missiles-fields-named-by-the-table-doc.md)
  closed. Open for P1.3: the numbered tier-A functions, the re-seed sites in the missile range, the step direction
  (`0x0064FC60`) for Phase 2's position logs.
- **2026-10-20 — `lane/p45m` reviewed (architect): accept with fixes.** Spot-checked on the pinned `Game.exe`
  (objdump): the signed `movzx; test ax,ax; jle; movsx; cmp bound` before every read of the three tables (hit
  0x005ADA0D, 0x005AE09B, 0x005AE106, 0x005B02CF; damage 0x005AE158; do 0x005ADBEE), so row 568's 64 948 (−588) is
  never called; the bounds 53/71/31 at `0x0073C71C`/`0x0073C83C`/`0x0073C95C` and the non-null counts 36/53/14 from the
  image; `sub_0064A850_MissileCritRoll`'s three inline LCG steps on `ESI`'s `+0x20`/`+0x24` (stat 337 by
  `STATS_GetUnitStat` unconditionally, 141 and the mastery critical each only when non-zero, return 1 at the first
  success); `sub_0059F940_MissilePierceCount`'s `RNG_SeedInit(STATS_GetUnitBaseStat(owner, 328))` local seed, at most
  four steps, the count written as stat 328. Ghidra's 97 call sites in 82 functions recounted from the kept xrefs;
  `sha256sum -c p45m-manifest.sha256` OK; the tool's hash matches. The one `[C]` is a full-table data join and is scoped
  (the column-to-table mapping stays `[I]`); no leads, no foreign names. Fixes: (1) the hit-table count: four reads
  (one in `MissileEndHit`) and one damage read, not "five hit-table sites" (skills/0002 summary and § 5, the P0 notes
  entry); (2) skills/0002 § 3 states that the missile crit chain is not the melee build's (order 337, 141, mastery;
  337 drawn at 0); (3) quests/0001's `+0x96` open question struck as answered (`Range`), and the § 7 timer row names the
  column. Merge: `re/symbols.csv` kept one copy of the two shared rows (no duplicate address or name), this log's tail
  kept both sides. **Ruling (the creation crit draws):** a new owner-seed event, "missile creation", in the combat
  spec's draw order, separate from the melee chain; § C's `[C]` chaining stands for the run's paths with an `[I]` note
  that a player's weapon-share missile inserts 1–3 draws at its creation; monster archers draw too (337 at 0), so B2
  and the monster chain are scoped to melee. Written into
  [the spec-writer's entry](../backlog/archive/2026-10-20-reverser-spec-writer-missile-path-inputs-for-drlg-collision-combat-econ.md).
  For Phase 2: "missile create" is an event kind that draws on the owner's seed and needs its 20 chained pairs; log the
  owner's and the missile's seeds at creation and at the hit. **P1.3 may start once this lane is in `main`** and picks
  up: the tier-A missiles' numbered do/hit/damage functions (`firebolt`, `bomb in air`, `plaguejavelin` and their
  sub-missiles and explosions), skill do 30 (`0x005C37C0`) run with a missile as its unit (do 14), the re-seed sites
  (`0x005A9820`, `0x005ACDF0`, `0x005AC073` and rng/0002's others), `0x006505C0`, `0x00620C10`, `0x005A43B0`,
  `0x00645F00`, the step direction `0x0064FC60` and the missile pass's place in the frame (`0x00540F60`…) for the log
  windows, `MissileEndHit`'s reachability, the P0 notes entry's remainder and P1.1's list above, and the boundary
  recommendation. Review request
  [closed](../backlog/archive/2026-10-20-reverser-architect-lane-p45m-review-plan-0045-p1-2-missiles.md); the
  [p49r names entry](../backlog/archive/2026-10-20-architect-reverser-plan-0045-p1-2-reuse-the-p49r-missile.md) closed.
- **2026-10-20 — P1.2's spec inputs folded, for review (spec-writer, `lane/msw`).** The
  [reverser's entry](../backlog/archive/2026-10-20-reverser-spec-writer-missile-path-inputs-for-drlg-collision-combat-econ.md)
  and the P1.2 ruling are closed, all `[I]` from skills/0002, with nothing raised.
  [combat/README § B](../specs/combat/README.md#b-draw-order-per-event):
  - B4 "missile creation" is a new event on the owner's seed: a diagram plus pseudocode for the weapon-share test and
    the 337 (always), 141, mastery chain; a `SrcMissDmg` missile draws on its source's seed.
  - B3 gives the to-hit roll on the owner's seed and `BuildDamage`'s seven `RangeB` in order.
  - B2 and § C's monster chain are scoped to melee, with notes on the archers' creation draws.
  - § C's `[C]` stands, with an `[I]` note on the player's creation draws. That note does not name them as the cause
    of the 213 resynchronisations: Phase 2 tests it.
  - The "draws that do not happen" note is scoped, and the phase (3) open question is rewritten.

  Elsewhere:
  - [combat/damage](../specs/combat/damage.md) step 3 notes that missiles do not use it.
  - [rng/seeds](../specs/rng/seeds.md) classifies the pierce count's local seed (`RNG_SeedInit` from stat 328) and
    narrows the re-seed open question.
  - [items/economy](../specs/items/economy.md) H3 gives the `useAmmo` gates; the gates question is struck and
    `SkillWeaponWear` stays `[L]`.
  - [drlg/collision](../specs/drlg/collision.md) § F gets the missile side of `0x40`: do 3 writes it, `HitUnit`
    unmarks it, `CollideType` 7 is unused. **drlg/collision is held by plan 0038 Phase 3 (waits H5b+H5d).** This
    lane only adds the 0045 input: no 0038 row was re-tagged, and C2's `[L]` stands.
  - Wiki: economy updated (which shots use ammunition, the stale arrows item dropped); levels and monsters get a
    `based_on` bump only; combat not edited (no contradiction).

  Tags:

  | Spec | Before | After |
  |---|---|---|
  | combat/README | {C: 36, I: 22, L: 5} | {C: 36, I: 35, L: 5} |
  | damage | {C: 34, I: 28, L: 4} | {C: 34, I: 29, L: 4} |
  | rng/seeds | {C: 79, I: 10, L: 4} | {C: 79, I: 11, L: 4} |
  | drlg/collision | {C: 110, I: 60, L: 9} | {C: 110, I: 61, L: 9} |
  | items/economy | {C: 125, I: 83, L: 12} | {C: 125, I: 84, L: 12} |

  The live open-question counts are unchanged. Review:
  [request](../backlog/archive/2026-10-20-spec-writer-architect-review-lane-msw-missile-creation-draws-in-combat.md).
- **2026-10-20 — `lane/msw` reviewed (architect): accept with fixes.** Every new statement checked against skills/0002
  §§ 2–6 and 9 and skills/0001 § 6: B4's weapon-share test, the 337 (always) / 141 / mastery order and the first-success
  stop, the `SrcMissDmg` source branch with no weapon, the creation order (`SUnitCreate`, callback, damage block, pierce),
  B3's to-hit on the owner's seed and `BuildDamage`'s seven `RangeB` in order, the do-3 writer and the `HitUnit` unmark,
  and the 33 `useAmmo` sites (the six monster sites and both `0x005D88B0` calls re-read in objdump on the pinned
  `Game.exe`, the two other `0x005A35D0` calls push 0). The P1.2 ruling holds: B4 is its own owner-seed event, not
  damage step 3's chain; § C's `[C]` is unchanged with an `[I]` note that does not claim the 213 resyncs; B2 and the
  monster chain are melee. The diagrams match the text; the struck economy question has no tag; the wiki has no tags or
  anchors. No tag moved, so the five specs keep status `reviewed` and their tag counts. Fixes (7): (1) combat A3 "the
  critical chance" is fixed at creation → "the critical strike's result"; (2) the B4 entry-point row names
  `sub_0059F900_MissileInitDamage` between `MissileCreate` and the damage block; (3) "Draws that do not happen" `[C]`
  scoped to what the run checked (B1, B2 and the player's side of B3), not all of B3, whose missile draws are `[I]`;
  (4) `CritChain`'s mastery local renamed `mc` (it shadowed the missile `m`); (5) drlg/collision § F: the `HitUnit` unmark
  is scoped to a missile ending through `HitUnit`, a do-1 free without the hit function not followed; (6) rng/seeds: the
  "client/server base-stat pair" now cites rng/0002 (it came from there, not from skills/0002); (7) economy H3's
  "on its paying path" is spelt out: `SKILLS_SrvDo` with `pay` set and a player or monster unit (skills/0001 § 6's
  `if (pay) { if (actor) … decquant … }`), the use acting only for a player. **Rulings:** (a) skills/0002 § 2's "four
  monster functions" listing five was the finding's miscount: five functions, six sites, verified in objdump; fixed in
  the finding with a review note, no backlog entry (the spec says "a few" and stands). (b) `decquant`'s reading is
  right, only the wording was vague (fix 7). (c) drlg/collision stays held by plan 0038 Phase 3; the lane re-tagged no
  0038 row. Review request
  [closed](../backlog/archive/2026-10-20-spec-writer-architect-review-lane-msw-missile-creation-draws-in-combat.md).
- **2026-10-20 — Phase 1 batch P1.3 landed for review (reverser, `lane/p45h`, static).**
  [skills/0003-handlers](../findings/skills/0003-handlers.md): the progressive entries 36–41 and 143 (missile and calc
  picked by the charge count; **37, 39, 41 and 143 step the attacker's seed once at entry**, 38 draws `RangeB` on it
  and runs an area hit; 39 and 41 on local seeds) and `0x00571AA0` (a client message `0xA3`); the 31 stat-event
  handlers with their registrations (18 by ItemStatCost, 11 by Skills `auraeventfunc`; 11 and 12 unused) and their
  draws; the item-cast helpers; **state 52 is applied inside `COMBAT_ToHitRoll`'s success branch**
  (`sub_0057D810_PreventHealHook`, no draw); the event-9 handler `0x005C01D0` is handler 28 (heal after kill, no draw);
  `SrvStart` in do 83 and 109, `PayCost` in start 26 (Blade Fury); all 15 `EType` stores at packet `+0x65`; the tier-A
  start, do and missile functions; skill do 30 with a missile as unit; the re-seed census of rng/0002's server sites
  (missiles and stack seeds, except Armageddon's do 146 which re-seeds the caster); summons and the pet limit
  (`PetType` `group`, `petmax`); `PathDirection` and its table, the frame pass (missiles before players and
  monsters); `MissileEndHit` and `0x00645390` unreferenced; `repeat`, `leftskill`, `weapsel` client-side,
  `TgtPlaceCheck` a monster AI test, the ally test never refusing from `StartUsedSkill`. 55 `[I]`, 6 `[L]`, no `[C]`.
  **Correction** to skills/0002: hit function 22 is `0x005ADD20`; the `CallDoFunc` caller `0x005ACFC0` is hit **23**
  (unused on stock data; symbol renamed `sub_005ACFC0_MissHit23CallDo`); carried into its summary, § 8, Functions table
  and open questions (the P1.2 log line above stays as history). Dated notes in skills/0001 and combat/0001. 118 symbol
  rows, `re/types/skills.h`, `tools/skills_handlers_scan.py` (sha256 `39b09e52…`) with kept outputs
  (`workspace/logs/skills/p45h-manifest.sha256`: `handlers-scan.txt` `6c2a2739…`, `handlers-rows.txt` `dd52e147…`).
  **Boundary recommendation** for Phase 2 in [skills/0003 § 14](../findings/skills/0003-handlers.md#14-boundary-recommendation-for-phase-2)
  (event entry points, value oracles, modelled set, log windows, chaining kinds), for the review's ruling. Backlog:
  review request [to the architect](../backlog/archive/2026-10-20-reverser-architect-lane-p45h-review-plan-0045-p1-3-handlers.md),
  inputs [to the spec-writer](../backlog/archive/2026-10-20-reverser-spec-writer-skills-0003-handlers-inputs-for-combat-rng-seeds.md),
  column anchors [to the archivist](../backlog/2026-10-20-reverser-archivist-skills-columns-anchored-by-skills-0003.md);
  closed: [the P0 notes entry](../backlog/archive/2026-10-20-architect-reverser-plan-0045-p0-review-notes-for-p1-1.md)
  and [the state-52/event-9 entry](../backlog/archive/2026-10-17-reverser-reverser-a-read-which-call-applies-the.md).
  Open: `Unit+0x38`, a new missile's first frame, the unit filter for a missile unit, the fifth unit-event list.
- **2026-10-20 — `lane/p45h` reviewed (architect): accept with fixes.** Checked on the pinned `Game.exe` in objdump:
  the inline step on the unit's seed (`EDX`, `+0x20`/`+0x24`) at `0x005D4E80` (37) and `0x005D4F50` (143), before the
  record test; 38's `sub_0056E170_SkillRollPhys` (`RangeB(unit seed, max − min)` at `0x0056E1C4`) then
  `SKILLS_RollElemDamage` (`RangeB` at `0x0056E132`, type 10's extra draws in `0x0056C8E0`, skills/0001); handler 7's
  inline step at `0x005BF9CF` on its unit (`low & 0x7F` against 64/32/128) and handler 21's `RangeB(seed, 100)` at
  `0x005C0603`; Armageddon's `RNG_SeedInit(caster +0x20, SkillEntry+0x18)` at `0x005C8688` then `RNG_Range(1 000 000)`
  at `0x005C8694` stored back by `0x00644560`, the caster being the do function's `EDX`; state 52: `COMBAT_ToHitRoll`'s
  success branch (`cmp esi,edi; jge`) calls `0x0057D810` at `0x0057DB80`, whose only calls are `UnitGetStat` and
  `STATE_ApplyTimed` (no LCG constant, no RNG call, `ret` at `0x0057D899`); `MissileEndHit` and `0x00645390`: no
  `call`/`jmp` rel32 to either and no 4-byte occurrence in the file (an independent scan, not the lane's tool); the
  hit table `0x0073C840` holds `0x005ADD20` at index 22 and `0x005ACFC0` at 23, and Missiles' only 22 is row 233
  `fistoftheheavensdelay`, no row uses 23. Kept outputs pass `sha256sum -c`, the tool's hash matches, no foreign
  names, tags honest (55 `[I]`, now 7 `[L]` under *Open questions*, no `[C]`). Merge: this log's tail kept both sides
  (`lane/msw`'s entries first); `re/symbols.csv` has no duplicate address or name, the rename
  `sub_005ACFC0_MissHit22CallDo` → `sub_005ACFC0_MissHit23CallDo` leaves no reference to the old name. Fixes (4),
  written into the findings: (1) skills/0003 § 13's reading listed the attacker's `do…` handlers as 7, 14–16, 20 and
  31 among the defender's: 8 and 9 run on the `do…` events, 31 is the killer's `kill` handler, 3 the defender's;
  (2) § 1 and § 13: 38's area defence rolls draw on each area unit's seed, not the attacker's, and 38's `RangeB`
  argument is named; (3) skills/0002 § 8's "row 233 holds 0 and entry 0 is null" inside the hit-23 bullet struck (row
  233 does not use hit 23); (4) a new open question: `SkillEntry+0x18` at Armageddon's first period (the setter
  `0x00644560` has 85 call sites, unfollowed), on which the caster's seed after that period depends.
  **Tier A is fixed** (the Phase 1 review ruling the phase's *Done when* calls for): the 26 rows of
  [Skills § Dispatch](../tables/Skills.md#families-and-the-tier-a-candidates) as the Phase 0 review accepted them; the
  monster skills are those the Phase 2 sessions' attackers use through `MonSkillAttackDo` (skills/0001 § 13), named in
  the run record, their numbered functions value oracles unless a tier-A row shares them. Summon functions other than
  do 31 and 114 (golems, revive, valkyrie, spirits) are plan 0046's; the pet limit (`PetAdd`) is this plan's.
  **Ruling: the Phase 2 design** (on skills/0003 § 14):
  1. **Entry points logged** (entry and exit seeds of every seed the event touches): `SKILLS_SrvStart`,
     `SKILLS_SrvDo`; `COMBAT_PrgFinisher` with the attacker's seed before the peek, after **each** `srvprgfunc` entry
     and after the last, and the charge count; `sub_0059FA30_MissileCreate` (owner's and new missile's seeds, class,
     start, target, velocity, callback); `sub_005ADBB0_MissileDoFrame` inside the window of item 4 only;
     `MISSILE_HitUnit` (owner's, missile's and unit's seeds, result); `UNIT_DispatchEvent` (event id, each record's
     function number, the handler unit's seed before and after each record); `sub_0057D810_PreventHealHook`;
     `sub_0056D940_SpawnOwnedMonster` and `sub_00575D90_PetAdd`; the § 9 re-seed sites tier A reaches (the value
     passed to `RNG_SeedInit`). `sub_005C8520_SkillDo146Armageddon` is not tier A: it is logged (caster's seed before
     and after, `SkillEntry+0x18` before and after) whenever it fires, no session is required to cast it, and its
     claim stays `[I]`; an Armageddon period ends the caster's chain like any resynchronisation.
  2. **Value oracles** (logged, named in the record, taken as given): as § 14 lists (the do function's frame, the
     AI's choice, numbered functions outside tier A with their exit seeds, the path planner's points and cell list,
     the unit filter and `ForUnitsInRange`'s unit order as the list the callback ran on, the pet removed), plus: the
     skill an item event casts when it is outside tier A (handlers 20, 21, 30 model their chance step and take the
     cast as an oracle), handler 31's spawn (monsters/spawn's), `0x005CDD30`'s frame-list test, and Armageddon's first
     `SkillEntry+0x18`.
  3. **`tools/skills.py` models** what § 14 lists, scoped: the tier-A start, do and missile functions; the
     `srvprgfunc` entries tier A reaches (Fists of Fire: 143, 38, 39) checked, the others (36, 37, 40, 41) modelled
     and left `[I]` if unreached; the stat-event handlers registered on stock data (11 and 12 are not), each checked
     where a session reaches it; state 52; `PathDirection` with `g_PathDirTable` read from the pinned image at run
     time (never written to the repository); the velocity step and the creation-time damage.
  4. **Missile log window**: creation, hit and end events for every missile whose owner or hit unit is the logged
     character or its target; per-frame positions only for the first 300 missiles of the run, at most 30 per
     session, chosen at creation by guid and followed to removal (the breakpoint conditioned on that set); the record
     states the window and the log sizes (ADR-0014 § Log volume). The frame on which a new missile first steps
     (skills/0003's open question on `sub_005415E0`) is a required measurement of the window, stated in game frames.
  5. **Chaining (ADR-0014), at least 20 chained pairs each**: skill start, skill do, the progressive finisher
     (attacker's seed, finisher exit to the next event), missile creation (owner's seed, P1.2's critical draws),
     missile frame (the missile's own seed, consecutive frames of one missile in the window, from the rows that draw:
     do 5 `meteorfire` among them), missile hit (missile's and defender's seeds), stat-event handler (the handler
     unit's seed, over at least three drawing handlers), summon (the spawn's seed, monsters/spawn's chain). State 52
     and the item-cast helpers draw nothing: they need no pairs, their absence is checked by the to-hit and handler
     exit assertions around them. Armageddon's re-seed needs none (not tier A). A kind short of 20 keeps its
     draw-order claims at `[I]`.
  **Combat spec routing:** combat/README § A1 ("the finisher peeks `att.seed`") and § B, delivery § A and its open
  question on the `srvprgfunc` entries, and README's phase-(3) open question are now stale: the entries are read and
  37, 39, 41 and 143 step the attacker's seed and 38 draws two or three `RangeB` on it plus a defence roll per area
  unit. The finisher's own step stays a peek; § C's `[C]` stands (the run dropped finisher events by rule and had
  none). Written into [the spec-writer's entry](../backlog/archive/2026-10-20-reverser-spec-writer-skills-0003-handlers-inputs-for-combat-rng-seeds.md)
  as an `[I]` fold, ahead of Phase 3. **Status:** Phase 1's static batches P1.1–P1.3 are complete; Phase 1 closes when
  Phase 1b (community cross-check, no Ghidra) lands, which may run now beside anything. **Phase 2 is ready** to start
  once both harness slots are free (plan 0044·P2 holds them now); Phase 1b must land before Phase 2's last session
  batch, since its contradicted cases are Phase 2 cases. **Plan 0046 Phase 0 (archivist) may start**: its gate (P1.3
  reviewed, the machinery named, tier A fixed) is met. Review request
  [closed](../backlog/archive/2026-10-20-reverser-architect-lane-p45h-review-plan-0045-p1-3-handlers.md).
- **2026-10-20 — skills/0003 folded into combat and rng/seeds (spec-writer, `lane/cfix2`), for review.** All `[I]`,
  ahead of Phase 3, from [skills/0003](../findings/skills/0003-handlers.md) §§ 1, 2, 3, 9, 12, 13 as fixed by the P1.3
  review: [combat/README](../specs/combat/README.md) A1, B1, new B5 (the finisher's `srvprgfunc` entries: 37, 39, 41,
  143 one step on the attacker's seed at entry, 38 two or three draws after delivering the queued hit, its area
  units' defence rolls on their own seeds) and B6 (the drawing stat-event handlers by unit), an `[I]` note under § C's
  unchanged `[C]`, the phase-(3) open question rewritten; [combat/delivery](../specs/combat/delivery.md) new A3
  (pseudocode) and E5 (handler table, 28 heal after kill with no draw), two open questions struck, one `[L]` added;
  [combat/to-hit](../specs/combat/to-hit.md) A6 (state 52); [combat/damage](../specs/combat/damage.md) D1 (15 `EType`
  stores at `+0x65`); [rng/seeds](../specs/rng/seeds.md) the re-seed sites, its open question struck, the
  Armageddon first-period `[L]` added; wiki/randomness rewritten where it said the sites were unread. Tags: README
  I 35 → 42, delivery I 39 → 53 and L 4 → 3, seeds I 11 → 12; damage and to-hit unchanged. Entry
  [closed](../backlog/archive/2026-10-20-reverser-spec-writer-skills-0003-handlers-inputs-for-combat-rng-seeds.md);
  review request [to the architect](../backlog/2026-10-20-spec-writer-architect-review-lane-cfix2-skills-0003-fold-into-combat.md).
