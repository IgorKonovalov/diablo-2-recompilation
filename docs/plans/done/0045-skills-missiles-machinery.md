# 0045 — Skills and missiles, the machinery: dispatch, packets, missiles, event handlers (ADR-0014 phase 3, part 1)

> **Status:** done (closed 2026-10-27). Approved 2026-10-20 (owner); Phase 2 done 2026-10-27 (parts 1 and 2 accepted
> with fixes); Phase 3 accepted with fixes 2026-10-27 (the skills spec reviewed); Phase 4 (wiki) accepted with fixes
> 2026-10-27
> **Created:** 2026-10-20
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0007-fetched-leads-only, 0011-harness-slots, 0013-forced-path-runs-cell-level, 0014-scope-game-simulation, 0015-emulated-reproduction, 0016-pipelined-simulation-phases, 0020-skills-phase-in-two-plans

## TL;DR

**Question:** when a unit uses a skill, what does the server do, frame by frame, until the skill's effects are
resolved: which checks let it start, which function runs on which frame, which damage packet it builds, which
missiles it creates and how they move, collide and hit, which stat-event handlers fire, which units it summons, and
which seeds it draws on? This is phase (3) of [ADR-0014](../../adrs/0014-scope-game-simulation.md), part 1 under
[ADR-0020](../../adrs/0020-skills-phase-in-two-plans.md). When it is done:
- the Missiles table and the dispatch columns of Skills are documented, with a survey;
- `docs/findings/skills/0001-dispatch.md` and `docs/findings/skills/0002-missiles.md` name the machinery;
- `tools/skills.py` reproduces skill-use, missile and event-handler events of a run per event;
- `docs/specs/skills/` (overview, `dispatch`, `missiles`) is reviewed, and the skill and missile oracles of
  [combat](../../specs/combat/README.md), [stats/states](../../specs/stats/states.md), [data/calc](../../specs/data/calc.md),
  [rng/seeds](../../specs/rng/seeds.md) and [items/economy](../../specs/items/economy.md) are replaced where the kept logs
  hold what the model needs.

The boundary: **the machinery and a named tier A of skills** are in this plan. What each of the remaining numbered
skill and missile functions does is plan [0046](../0046-skills-function-catalogue.md). Which skill a monster chooses,
and when, is phase (5) (an input here); the frame on which an animation reaches its action frame is phase (4) (a
logged input here, stated in game frames; phases renumbered by the owner's 2026-10-20 swap, plans 0050 and 0052).

## Context

- **The gate is open.** Phase (2) is [plan 0041](0041-stats-and-states.md), closed 2026-10-17 with
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
  [combat § Inputs](../../specs/combat/README.md), its open question "Owed to phase (3)".
- **Open questions this plan answers by name:**
  - the prevent-heal state 52 (stat 117, *Fleshripper*): which call applies it between `COMBAT_ToHitRoll` and the
    defence roll ([combat/0001](../../findings/combat/0001-formulas.md) *Open questions*; backlog
    `2026-10-17-reverser-reverser-a-read-which-call-applies-the.md`);
  - the event-9 (kill) handler at `0x005C01D0` that runs inside delivery before `AD1` and explains the 101 remaining
    mismatches of the set-aside *Fleshripper* session (same entry; backlog
    `2026-10-17-architect-reverser-plan-0037-resume-lane-review-follow.md` (a) for the log copy);
  - the skill and missile re-seed sites of `+0x20` (`0x005ACDF0`, `0x005C9290`, `0x005D40F0`, `0x005D5BF0`, the call
    at `0x005AC073`, the shared `0x00645390`) and the eight register-held server seeds of
    [rng/0002 § Plan 0039 batch P1a](../../findings/rng/0002-seed-tree.md#plan-0039-batch-p1a-2026-10-16), routed here by
    the research map and [rng/seeds](../../specs/rng/seeds.md) *Open questions*;
  - the reader of the missile `0x40` collision mark ([drlg/collision](../../specs/drlg/collision.md) *Open questions*);
  - stats/states' Holy Shield, progressive charges and timed self-states, the damaging aura's hit (`AuraHitDo`,
    `SKILLS_RollElemDamage`; one `RNG_RangeB` per hit, already `[C]` on 746 chained pairs), the aura request's
    `+0x48` and `SKILLS_ForUnitsInRange`'s monster exclusion flag ([stats/states](../../specs/stats/states.md)
    *Open questions*);
  - items/economy's `PLAYER_UseAmmo` gates and `SkillWeaponWear` ([items/economy](../../specs/items/economy.md)
    *Open questions*);
  - data/calc's BearSmite cast and `MISS_CalcVar` 19–27 ([data/calc](../../specs/data/calc.md) *Open questions*);
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
  ([harness-play](../../../.claude/skills/reverser/references/harness-play.md), "no targeted spells"). Tier A below is
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
  - [Skills](../../tables/Skills.md) § Dispatch: `srvstfunc`, `srvdofunc`, `srvprgfunc1..3`, `prgcalc1..3`,
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
    the `pettype` limit, the created unit's seed and its hand-off to [monsters/spawn](../../specs/monsters/spawn.md) and
    [monsters/stats](../../specs/monsters/stats.md);
  - **monster skill use:** `MonSkillAttackDo` and the `MonAttackStats` formulas (the stats it writes), with the AI's
    choice as an input;
  - **the re-seed sites** of rng/0002 Q15: which skills re-seed `+0x20` or another object's seed, from what;
  - **ammunition and wear:** `PLAYER_UseAmmo`'s gates and `SkillWeaponWear`;
  - **from Phase 0's survey** (added 2026-10-20, archivist): the 50 Skills rows that name a server missile and have no
    `srvdofunc` (6 Magic Arrow, 36 Fire Bolt, 251 Fire Trauma, …): which code creates their missile; the progressive
    rows 254 Tiger Strike and 265 Cobra Strike, with `prgdam` and no `srvprgfunc`; Missiles row 568's server hit
    function 64 948 (the `.txt` cell `*12`): bounds test, out-of-table call or unreached
    ([Skills § Dispatch](../../tables/Skills.md#dispatch-plan-0045-phase-0), [Missiles](../../tables/Missiles.md#encodings-particular-to-this-table));
  - **tier A**, the skills Phase 2 reproduces, fixed at this phase's review from the survey: the general rows
    (Attack, Kick, Throw, Left Hand Throw, Left Hand Swing); per class at least two skills the pilot can cast
    (self-centred, directional, melee or summon; for example Nova, Frost Nova, Static Field, Teleport, Fire Bolt;
    Bash, Howl; Jab, Multiple Shot; Raise Skeleton, Bone Armor; the Paladin's Holy Fire and Holy Shield; a Druid and
    an Assassin pair); every function family with ten or more stock rows represented once; the monster skills of the
    combat logs' attackers. **Phase 0 review ruling (2026-10-20):** the 26 candidate rows of
    [Skills § Dispatch](../../tables/Skills.md#families-and-the-tier-a-candidates) are this phase's starting list: the
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

#### Phase 2 part 2 — the models and sessions part 1 lacked (ruled at the part 1 review, 2026-10-27)
- **Owner skill:** reverser (agent-driven; slot 2, and slot 1 too when H1 is between batches; never with 0044·P2)
- **Why:** run:2026-10-25-skills (part 1) holds 0 mismatches over 335 618 checks, but the *Done when* above is not
  met: the skill-use floor (1 840 do events, 1 409 in tier-A rows, for 2 000), seven tier-A rows under 30 and three
  with no session, the request refusals (`SKILLS_CanUse` not logged), the handler fires and state 52, the summoned
  unit's seed and stats, `MonAttackStats`, the end of a missile at a hit and pierce uses, the re-seed sites other
  than `0x005C9290`, cases C2 and C4. Each needs a model, a breakpoint or a pilot change, not more of part 1's sessions.
- **Start:** part 1's tools (`tools/skills.py` `1b297c24…`, logger rev 3, `tools/skills_sessions.py`); part 1's logs
  stay kept and unchanged, and the floors below count part 1's events with part 2's.
- **What:** (1) a `SKILLS_CanUse` breakpoint (its return code) and refusal sessions; (2) a stat-event handler model;
  (3) a `MonAttackStats` model; (4) the summoned unit's seed and stats to the monsters/stats boundary; (5) a walking
  Blaze session (C4) and an area with `spike1`–`spike4` monsters (C2); (6) sessions for the short rows (the pilot's
  Kick, Left Hand Throw and Left Hand Swing, or the lane says it cannot and the review substitutes a row of the same
  family, as Phase 1's tier-A rule); (7) `CHAIN.caster` adds the caster's own logged draws between two skill events
  (the `THR` rolls first) and reports each remaining resync with the lines between, as the review's `caster-gaps.txt`
  does; (8) the oracle-replacement audit re-run for the handler fires once (2) exists.
- **Done when:** `run:YYYY-MM-DD-skills` (part 2) reproduces with **0 mismatches** and, with part 1, the floors of
  Phase 2's *Done when* are met or named short with counts, in particular: 2 000 skill uses, 30 per tier-A row; the
  mana, delay and town refusals with `CanUse`'s code (about 30 each, rare-branch); 300 handler fires over at least
  five event kinds, event 9 among them, and the state-52 apply; 100 summons with the created unit's seed and stats;
  200 `MonAttackStats` calls predicted; 100 hit ends with a unit and 50 pierce uses at a hit; 50 re-seeds at the Q15
  sites other than `0x005C9290` or each site named unreached; C2 and C4 created at a level above 1; the 304 caster
  resyncs of part 1 re-checked with (7): every player resync attributed to a modelled draw or listed with its lines,
  the monster resyncs left to plan 0052 (monster AI, proposed) when the AI is what remains; the handler audit's result named.

### Phase 3 — Spec: skills
- **Owner skill:** spec-writer
- **Start:** after the Phase 2 part 1 review (2026-10-27), in parallel with Phase 2 part 2: the statements part 2
  targets are written `[I]` and re-tagged from part 2's reviewed raises; the Phase 3 review waits for part 2's.
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
  Recorded in [ADR-0020](../../adrs/0020-skills-phase-in-two-plans.md) § Neutral.
- **Client-only skills.** Client missiles (`cltmissile*`) and the skill description tables are presentation and stay
  out.
- **Two clients.** Party auras and player-against-player skills stay `[I]` (plan 0044 if it stages them).

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-20 — Drafted (architect, `lane/plans45`).** Status `proposed`, with ADR-0020 (proposed).
- **2026-10-20 — Approved (owner, via the orchestrator).** Plans 0045–0049 and ADR-0020 approved as proposed; the run
  order of the [plans index](../README.md#run-order-unattended-queue-set-2026-10-20-plans-00380049) is the current queue.
- **2026-10-20 — Phase 0 landed (archivist, `lane/p45a`).** [Missiles](../../tables/Missiles.md) (new): the layout is
  complete, 146 fields over the 420-byte record, `excel_bin.py diff` 99 864 cells, 0 mismatches (the partial
  layout of plan 0035 held the seven calc fields only); every column with offset, width, observed values, grouped as
  the plan names them (function numbers, motion, collision, damage, links, params, presentation); the server function
  numbers printed per number. [PetType](../../tables/PetType.md) (new): layout complete (224 B, 400 cells, 0
  mismatches), the 20 rows with the 31 Skills rows that name them. [Skills § Dispatch](../../tables/Skills.md#dispatch-plan-0045-phase-0):
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
  [reverser, the fields three findings left unnamed](../../backlog/archive/2026-10-20-archivist-reverser-missiles-fields-named-by-the-table-doc.md);
  review request [to the architect](../../backlog/archive/2026-10-20-archivist-architect-lane-p45a-review-plan-0045-phase-0.md).
- **2026-10-20 — Phase 0 reviewed (architect): accept with fixes.** `gate.py --full=excel_layout,skills` and
  `test_gate.py` rerun green after merging `main`; both baselines equal the surveys' output. Anchors spot-checked
  against `re/symbols.csv` and the findings (`MISS_CalcVar`, `MISS_GetDamMin`, `MISS_GetElemLen`, `UNIT_GetSizeX`,
  `PATH_SetMarkMask`, `PermPortalAtUnit`, `SKILLS_CalcVar` `pets`; combat/0001 for `srvstfunc` 42, `srvdofunc` 7 and
  67, `COMBAT_PrgFinisher`, the knockback roll); meanings default to `[L]`, raised only where a finding or data/calc
  anchors them. Fixes (3): the plan names 18 tier-A rows, not 17 (this log and the survey's comment); Skills §
  Families: "the first 22 rows" of the 26; PetType row 17's sentry wording. Tier A: ruling in Phase 1's tier-A
  bullet (all 26 accepted, Meteor and Amplify Damage on the attack-click condition). Notes for P1.1/P1.2:
  [backlog to the reverser](../../backlog/archive/2026-10-20-architect-reverser-plan-0045-p0-review-notes-for-p1-1.md).
- **2026-10-20 — Phase 1 batch P1.1 landed for review (reverser, `lane/p45r`, static).**
  [skills/0001-dispatch](../../findings/skills/0001-dispatch.md): the request (client packets 0x05–0x11, `PLRMSG_SkillAtXY`
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
  [reverser's entry](../../backlog/archive/2026-10-20-reverser-spec-writer-combat-finisher-peek-and-conversion-writer.md)
  closed: [combat/delivery § A](../../specs/combat/delivery.md#a-queue-and-delivery) A2 says the finisher peeks the
  attacker's seed (`[I]`, ruling (2)), with a reimplementation note and a new `[L]` for the `srvprgfunc` entries and
  `0x00571AA0`; [combat/damage § D](../../specs/combat/damage.md#d-conversion) D1 names the skill hit builders as the
  conversion writers (`[I]`), the old `[L]` struck and a narrower one added; combat/README and
  [wiki/combat](../../wiki/combat.md) follow. Tags: delivery {C: 52, I: 38, L: 3} → {C: 52, I: 39, L: 4}, damage
  {C: 34, I: 27, L: 4} → {C: 34, I: 28, L: 5}, README unchanged. Open questions: delivery 3 → 4 live, damage 4 live
  (one struck, one added). No combat or rng call-order table listed the finisher as a draw. Review:
  [request](../../backlog/archive/2026-10-20-spec-writer-architect-review-lane-cfix-combat-finisher-peek-and-conversi.md).
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
  [skills/0002-missiles](../../findings/skills/0002-missiles.md): `MissileCreate` and its 0x5C-byte request (97 call sites
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
  [to the architect](../../backlog/archive/2026-10-20-reverser-architect-lane-p45m-review-plan-0045-p1-2-missiles.md), the Missiles
  columns [to the archivist](../../backlog/archive/2026-10-20-reverser-archivist-missiles-columns-anchored-by-skills-0002.md), the
  collision, combat and economy inputs
  [to the spec-writer](../../backlog/archive/2026-10-20-reverser-spec-writer-missile-path-inputs-for-drlg-collision-combat-econ.md);
  [the archivist's fields entry](../../backlog/archive/2026-10-20-archivist-reverser-missiles-fields-named-by-the-table-doc.md)
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
  [the spec-writer's entry](../../backlog/archive/2026-10-20-reverser-spec-writer-missile-path-inputs-for-drlg-collision-combat-econ.md).
  For Phase 2: "missile create" is an event kind that draws on the owner's seed and needs its 20 chained pairs; log the
  owner's and the missile's seeds at creation and at the hit. **P1.3 may start once this lane is in `main`** and picks
  up: the tier-A missiles' numbered do/hit/damage functions (`firebolt`, `bomb in air`, `plaguejavelin` and their
  sub-missiles and explosions), skill do 30 (`0x005C37C0`) run with a missile as its unit (do 14), the re-seed sites
  (`0x005A9820`, `0x005ACDF0`, `0x005AC073` and rng/0002's others), `0x006505C0`, `0x00620C10`, `0x005A43B0`,
  `0x00645F00`, the step direction `0x0064FC60` and the missile pass's place in the frame (`0x00540F60`…) for the log
  windows, `MissileEndHit`'s reachability, the P0 notes entry's remainder and P1.1's list above, and the boundary
  recommendation. Review request
  [closed](../../backlog/archive/2026-10-20-reverser-architect-lane-p45m-review-plan-0045-p1-2-missiles.md); the
  [p49r names entry](../../backlog/archive/2026-10-20-architect-reverser-plan-0045-p1-2-reuse-the-p49r-missile.md) closed.
- **2026-10-20 — P1.2's spec inputs folded, for review (spec-writer, `lane/msw`).** The
  [reverser's entry](../../backlog/archive/2026-10-20-reverser-spec-writer-missile-path-inputs-for-drlg-collision-combat-econ.md)
  and the P1.2 ruling are closed, all `[I]` from skills/0002, with nothing raised.
  [combat/README § B](../../specs/combat/README.md#b-draw-order-per-event):
  - B4 "missile creation" is a new event on the owner's seed: a diagram plus pseudocode for the weapon-share test and
    the 337 (always), 141, mastery chain; a `SrcMissDmg` missile draws on its source's seed.
  - B3 gives the to-hit roll on the owner's seed and `BuildDamage`'s seven `RangeB` in order.
  - B2 and § C's monster chain are scoped to melee, with notes on the archers' creation draws.
  - § C's `[C]` stands, with an `[I]` note on the player's creation draws. That note does not name them as the cause
    of the 213 resynchronisations: Phase 2 tests it.
  - The "draws that do not happen" note is scoped, and the phase (3) open question is rewritten.

  Elsewhere:
  - [combat/damage](../../specs/combat/damage.md) step 3 notes that missiles do not use it.
  - [rng/seeds](../../specs/rng/seeds.md) classifies the pierce count's local seed (`RNG_SeedInit` from stat 328) and
    narrows the re-seed open question.
  - [items/economy](../../specs/items/economy.md) H3 gives the `useAmmo` gates; the gates question is struck and
    `SkillWeaponWear` stays `[L]`.
  - [drlg/collision](../../specs/drlg/collision.md) § F gets the missile side of `0x40`: do 3 writes it, `HitUnit`
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
  [request](../../backlog/archive/2026-10-20-spec-writer-architect-review-lane-msw-missile-creation-draws-in-combat.md).
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
  [closed](../../backlog/archive/2026-10-20-spec-writer-architect-review-lane-msw-missile-creation-draws-in-combat.md).
- **2026-10-20 — Phase 1 batch P1.3 landed for review (reverser, `lane/p45h`, static).**
  [skills/0003-handlers](../../findings/skills/0003-handlers.md): the progressive entries 36–41 and 143 (missile and calc
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
  **Boundary recommendation** for Phase 2 in [skills/0003 § 14](../../findings/skills/0003-handlers.md#14-boundary-recommendation-for-phase-2)
  (event entry points, value oracles, modelled set, log windows, chaining kinds), for the review's ruling. Backlog:
  review request [to the architect](../../backlog/archive/2026-10-20-reverser-architect-lane-p45h-review-plan-0045-p1-3-handlers.md),
  inputs [to the spec-writer](../../backlog/archive/2026-10-20-reverser-spec-writer-skills-0003-handlers-inputs-for-combat-rng-seeds.md),
  column anchors [to the archivist](../../backlog/archive/2026-10-20-reverser-archivist-skills-columns-anchored-by-skills-0003.md);
  closed: [the P0 notes entry](../../backlog/archive/2026-10-20-architect-reverser-plan-0045-p0-review-notes-for-p1-1.md)
  and [the state-52/event-9 entry](../../backlog/archive/2026-10-17-reverser-reverser-a-read-which-call-applies-the.md).
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
  [Skills § Dispatch](../../tables/Skills.md#families-and-the-tier-a-candidates) as the Phase 0 review accepted them; the
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
     exit assertions around them. *(Scoped at the P1b review, 2026-10-20: the `ItemTarget` 2 helper `0x005FD850`
     draws 2 to 20 steps; see ruling 3 there.)* Armageddon's re-seed needs none (not tier A). A kind short of 20 keeps its
     draw-order claims at `[I]`.
  **Combat spec routing:** combat/README § A1 ("the finisher peeks `att.seed`") and § B, delivery § A and its open
  question on the `srvprgfunc` entries, and README's phase-(3) open question are now stale: the entries are read and
  37, 39, 41 and 143 step the attacker's seed and 38 draws two or three `RangeB` on it plus a defence roll per area
  unit. The finisher's own step stays a peek; § C's `[C]` stands (the run dropped finisher events by rule and had
  none). Written into [the spec-writer's entry](../../backlog/archive/2026-10-20-reverser-spec-writer-skills-0003-handlers-inputs-for-combat-rng-seeds.md)
  as an `[I]` fold, ahead of Phase 3. **Status:** Phase 1's static batches P1.1–P1.3 are complete; Phase 1 closes when
  Phase 1b (community cross-check, no Ghidra) lands, which may run now beside anything. **Phase 2 is ready** to start
  once both harness slots are free (plan 0044·P2 holds them now); Phase 1b must land before Phase 2's last session
  batch, since its contradicted cases are Phase 2 cases. **Plan 0046 Phase 0 (archivist) may start**: its gate (P1.3
  reviewed, the machinery named, tier A fixed) is met. Review request
  [closed](../../backlog/archive/2026-10-20-reverser-architect-lane-p45h-review-plan-0045-p1-3-handlers.md).
- **2026-10-20 — skills/0003 folded into combat and rng/seeds (spec-writer, `lane/cfix2`), for review.** All `[I]`,
  ahead of Phase 3, from [skills/0003](../../findings/skills/0003-handlers.md) §§ 1, 2, 3, 9, 12, 13 as fixed by the P1.3
  review: [combat/README](../../specs/combat/README.md) A1, B1, new B5 (the finisher's `srvprgfunc` entries: 37, 39, 41,
  143 one step on the attacker's seed at entry, 38 two or three draws after delivering the queued hit, its area
  units' defence rolls on their own seeds) and B6 (the drawing stat-event handlers by unit), an `[I]` note under § C's
  unchanged `[C]`, the phase-(3) open question rewritten; [combat/delivery](../../specs/combat/delivery.md) new A3
  (pseudocode) and E5 (handler table, 28 heal after kill with no draw), two open questions struck, one `[L]` added;
  [combat/to-hit](../../specs/combat/to-hit.md) A6 (state 52); [combat/damage](../../specs/combat/damage.md) D1 (15 `EType`
  stores at `+0x65`); [rng/seeds](../../specs/rng/seeds.md) the re-seed sites, its open question struck, the
  Armageddon first-period `[L]` added; wiki/randomness rewritten where it said the sites were unread. Tags: README
  I 35 → 42, delivery I 39 → 53 and L 4 → 3, seeds I 11 → 12; damage and to-hit unchanged. Entry
  [closed](../../backlog/archive/2026-10-20-reverser-spec-writer-skills-0003-handlers-inputs-for-combat-rng-seeds.md);
  review request [to the architect](../../backlog/archive/2026-10-20-spec-writer-architect-review-lane-cfix2-skills-0003-fold-into-combat.md).
- **2026-10-20 — `lane/cfix2` reviewed (architect): accept with fixes.** Every changed statement checked against
  skills/0003 §§ 1, 2, 3, 9, 12, 13 (as fixed by the P1.3 review) and skills/0001 §§ 11, 12 (`SKILLS_AddElemToPacket`'s
  type-10 `RNG_Step`); § C's `[C]` is unchanged; struck open questions carry no tag; the B5 sequence diagram and the
  delivery flowchart agree with the text after fix (2). Rulings on the two points, on the pinned `Game.exe` in objdump:
  (a) `COMBAT_DefenceRoll` takes the defender at `[ebp+0x8]`, `isMissile` at `[ebp+0xC]` (passed to `AvoidRoll`) and
  `useBlock` at `[ebp+0x10]` (the melee site `0x0057ECE1` pushes 1, 0, def; the missile site `0x005AD7FF` pushes
  phys ≠ 0, 1, def), so `AreaHitUnit`'s `push 0; push 1; push ebx` (`0x0056BA06`–`0x0056BA0D`) is
  `DefenceRoll(u, isMissile: true, useBlock: false)`: entry 38's area units cannot block and roll avoid, not dodge;
  (b) handler 21 returns before its draw when the stat is ≤ 0 (`0x005C05C3`–`0x005C05C8`), the packet is null or its result lacks
  bit `0x4` (`0x005C05F1`–`0x005C05F9`); the `RangeB` at `0x005C0603` comes after, so the finding's order is right.
  Fixes (9), written into the specs: (1) B5's "a Monk's charge-up skills" is the Assassin's; (2) README B1's note and
  `[I]` sentence and delivery's flowchart said the entries draw between the build and the delivery: when 38 runs it
  delivers first, so its draws and later entries' follow the delivery's; (3) A3 and B5 name `DefenceRoll`'s arguments
  (ruling a); (4) E5 row 21 states its gates (ruling b); (5) A3's 38 delivers only when the unit has a target
  (`UNIT_GetTargetUnit`, `0x005D3EBF`–`0x005D3ED0`); (6) § C's `[I]` paragraph adds the entries' missile creation
  draws (B4); (7) to-hit A6's anchor widened to `0x0057D891`, the `STATE_ApplyTimed` call; (8) rng/seeds: `0x005A9820`
  re-seeds the parent missile from `SubX + elapsed`, split from hit 58 and do 34; (9) rng/seeds: the item site
  `0x005C276A` (version-0 set builder) added, the one register-seed site outside skill and missile code. combat/README,
  delivery, to-hit, damage and rng/seeds **stay reviewed** (only `[I]` added, anchored; no tag count changed by the
  fixes). Review request [closed](../../backlog/archive/2026-10-20-spec-writer-architect-review-lane-cfix2-skills-0003-fold-into-combat.md).
- **2026-10-20 — Phase 1b landed for review (reverser, `lane/p45b`, no Ghidra, no harness).** Community cross-check of
  [skills/0001](../../findings/skills/0001-dispatch.md#leads-used), [skills/0002](../../findings/skills/0002-missiles.md#leads-used),
  [skills/0003](../../findings/skills/0003-handlers.md#leads-used) and [combat/0001](../../findings/combat/0001-formulas.md#leads-used),
  each page fetched and read in the session after the findings were written (ADR-0007); none shows code.
  - **Sources**: four new in [sources](../../sources.md): `arreat-summit-skill-basics`, `arreat-summit-casting-delays` and
    `arreat-summit-skill-trees` (LoD, 1.13-era pages), and `purediablo-piercing` (2023, Resurrected-era, no patch named).
    Two re-fetched: `d2dfg-blizzard` (§ Missiles.txt, § skills.txt, § pettype.txt; a Resurrected data guide) and
    `arreat-summit-amazon-passive` (§ Pierce). Tried and not used: diablowiki.net "Pierce" and three PureDiablo d2wiki
    pages (HTTP 403), the Fextralife D2R "Pierce" page (nothing the findings cover), a Blizzard D2R forum thread
    (anecdotal, about Diablo Clone).
  - **Verdicts** (evidence-rules' four words; *version-different* kept as a detail marker, used by none): 61 claims.
    27 held, 25 held with refinement, 5 contradicted, 4 not covered. skills/0001: 23 claims (9 / 13 / 0 / 1);
    skills/0002: 25 (12 / 9 / 4 / 0); skills/0003: 12 (5 / 3 / 1 / 3); combat/0001: 1 (`KnockBack`, held). No source
    covers the rng specs' claims (seeds and draw order), so none was compared there. Agreement promoted nothing.
  - **Quick re-reads** (objdump only, recorded): `tools/skills_crosscheck_reread.py` (sha256 `8361a4c1…`), kept outputs
    `workspace/logs/skills/p45b-manifest.sha256` (`p45b-reread.txt` `427ca8d7…`, code windows R1–R7; `p45b-rows.txt`
    `cbf9c64a…`, the stock-row values compared). Every contradicted reading stands as written: R1 velocity, R2 range,
    R3 acceleration, R4 summon level.
  - **Gaps the leads exposed** (noted in the findings, dated, no tag change). (a) The `ItemTarget` 2 helper
    `0x005FD850` steps the seed at `+0x20` of its unit 2–20 times (item Teleport), so skills/0003 § 2's "no draw"
    misses a path: noted in skills/0001 § 10 and skills/0003 § 2, open question in skills/0001. (b)
    `COMBAT_PrgFinisher` has six direct callers, not one: the five others are finishing moves (start 25; do 42, 50,
    52), noted in skills/0001 § 12. (c) What removes pets when `petmax` falls: open question in skills/0003.
  - **Phase 2 required cases** from the contradicted claims, all reachable on stock data
    ([backlog](../../backlog/2026-10-20-reverser-reverser-plan-0045-p1b-contradicted-cases.md)):
    - **C1** Raise Skeleton's summon level is `min(max(L · 3/4 + skill level, 1), L)`, against "generated at the
      caster's level" (src:arreat-summit-skill-trees). Case: a Necromancer with character level L above 4 × the skill
      level; log the summon's stat 12.
    - **C2** Missile velocity is `((VelLev · lvl) / 8 + Vel) << 8`, against `Vel` + `VelLev` per level beyond 1
      (src:d2dfg-blizzard). Case: a `spike1`–`spike4` monster missile; log its creation velocity and request level.
    - **C3** `Accel` is added on every fifth path step, against "per frame" (src:d2dfg-blizzard). Case: Nova, Frost
      Nova or Howl missiles (tier A) in the position window, one followed past its fifth step.
    - **C4** Range is `LevRange · lvl + Range`, against `LevRange` per caster level beyond 1 (src:d2dfg-blizzard).
      Case: one of the 32 `LevRange` rows. None is in tier A (`blaze`, `firewallmaker`, …), so this case needs the
      review's ruling.
    - **C5** A missed `ToHit` piercing missile ends at that unit, against "keeps traveling but doesn't deal any damage"
      (src:purediablo-piercing). Case: a `Pierce` arrow with a pierce stat above 0 whose to-hit fails; log the free
      and stat 328.
  - Review: [request](../../backlog/archive/2026-10-20-reverser-architect-lane-p45b-review-plan-0045-p1b-cross-check.md).
- **2026-10-20 — `lane/p45b` reviewed (architect): accept with fixes.** Checked: the four new and two re-fetched
  [sources](../../sources.md) rows follow the registry (title and author, URL, sections used, game version stated or "no
  patch named", fetched date and plan, "prose only, no code", used-for links; short quoted phrases only), and none
  points at decompiled code; the comparison was blind (every verdict compares a section written at P1.1–P1.3, the
  lane added only dated notes, an `[I]` re-read and two `[L]` open questions, and raised no tag); the verdicts use
  evidence-rules' four words, recounted from the four *Leads used* sections: 61 (27 / 25 / 5 / 4; skills/0001 9 / 13
  / 0 / 1, skills/0002 12 / 9 / 4 / 0, skills/0003 5 / 3 / 1 / 3, combat/0001 1 held). Kept outputs: `sha256sum -c
  p45b-manifest.sha256` passes in `workspace/logs/skills/` (both files), and the tool's sha256 is `8361a4c1…` as cited.
  Spot-checks on the pinned `Game.exe` (sha256 `631066c1…`, objdump): **C2** `0x0059FB1B`–`0x0059FB3B` is
  `((VelLev · [esi+0x30]) / 8` (signed, `cdq; and edx,7; sar 3`) `+ Vel) << 8`; **C3** `0x006502E6`–`0x00650320`
  adds `Accel` to `+0x7C` only when the counter `+0x8C` reaches 5, caps at `+0x84` (and zeroes `Accel`), floors at 0,
  resets the counter; **C5** `MISSILE_HitUnit` takes the pierce charge (`0x005AE029`, `MissilePierceUse`) before the
  to-hit roll (`0x005AE06F`), and a failed roll returns 2 at `0x005AE0C7` whatever the pierce result, unless an
  `AlwaysExplode` hit function returns bit 2. R6's count holds over the whole image: six `call 0x5D5220`. `ITEMSKILL_Cast`
  calls helper 2 at `0x005FDB9F` (3 at `0x005FDBE1`, 4 at `0x005FDBF3`), so the gap is on the item-cast path.
  **Fixes (2), written into the docs:** (1) skills/0001's `ItemTarget` verdict linked skills/0003 § 3 for the "no
  draw" sentence that is § 2's; (2) sources' `arreat-summit-amazon-passive` row ran its re-fetch note into the previous
  sentence without a full stop. **Rulings:**
  1. **C4: add a non-tier-A cast.** No tier-A row has `LevRange`, so no tier-A creation can tell `lvl` from `lvl − 1`.
     Phase 2 adds **Blaze** (`blaze`, `LevRange` 25) at a skill level of at least 2, about 30 creations, the stored
     range and the request level logged. Blaze is not added to tier A: its do function is a value oracle (design item
     2's "numbered functions outside tier A"), and only C4 and the shared creation code are checked on it. Fire Wall
     (`LevRange` 2) is the fallback if the pilot cannot cast Blaze.
  2. **C2: accepted as a monster-session case.** A session whose attackers include a `spike1`–`spike4` user, about 30
     creations, the creation velocity and the request level logged, the row named in the record; it rides on the 200
     monster skill uses already required. If no reachable monster of the session uses a `VelLev` row, C2 is a named
     shortfall and the formula stays `[I]`.
  3. **The two gaps.** (a) The `ItemTarget` helpers are machinery, but which unit helper 2 is given and whether 3 and
     4 draw are reads of the item callers of skills: **moved to plan 0046 Phase 1's item, shrine and object batch**,
     filed back to this plan's spec as that batch's *Done when* says. Not a Phase 2 case: no stock item event cast of
     an `ItemTarget` 2–4 skill is shown reachable. Phase 2 does not assume the helpers draw-free: an item cast of an
     `ItemTarget` 2–4 skill, if a session meets one, is logged with the given unit's seed before and after the helper
     and checked against helper 2's 2–20 steps as `[I]`; otherwise the record names it. Design item 5 is scoped above.
     combat/delivery E5 ("an item cast draws nothing of its own", from `lane/cfix2`, now on main) is wrong for
     `ItemTarget` 2: routed to the spec-writer
     ([entry](../../backlog/archive/2026-10-20-architect-spec-writer-combat-delivery-e5-item-target-2-draws.md)). (b) The
     finisher's five other callers (start 25 Dragon Claw, do 42 Dragon Talon, 50 Dragon Tail, 52 Dragon Flight) are
     Assassin finishing moves, none in tier A: **moved to plan 0046 Phase 1's Assassin batch**, which reads each
     function's path into `COMBAT_PrgFinisher` (this plan models the finisher through `SKILL_AttackDo` only). (c) Pet
     removal when `petmax` falls (a skill shrine wearing off): stays `[L]` in skills/0003's *Open questions*;
     **moved to plan 0046 Phase 1's item, shrine and object batch** (the shrine path), and Phase 3 lists it under
     *Open questions*.
  4. **Verdict vocabulary:** the four evidence-rules words stand. *version-different* may be added to a
     `contradicted` detail only after the Phase 2 case confirms the 1.14d reading and the source names another
     version; it never replaces the verdict word. None is used now.
  The cases entry ([reverser](../../backlog/2026-10-20-reverser-reverser-plan-0045-p1b-contradicted-cases.md)) stays open
  for Phase 2, with rulings 1 and 2 appended. **Phase 1 is closed** (P1.1, P1.2, P1.3 and P1b reviewed): Phase 2 waits
  only for both harness slots (plan 0044·P2 holds them). Review request
  [closed](../../backlog/archive/2026-10-20-reverser-architect-lane-p45b-review-plan-0045-p1b-cross-check.md).
- **2026-10-20 — combat/delivery E5 item-cast correction (spec-writer, `lane/e5fix`), for review.** From the P1b
  review's gap (a): [combat/delivery § E5](../../specs/combat/delivery.md#e-the-stat-events-crushing-blow-open-wounds-freeze)'s
  "an item cast draws nothing of its own" scoped to `ItemTarget` blank or 1 (`[I]`); a new `[I]` bullet for the
  `ItemTarget` 2 helper `0x005FD850` (2 to 20 steps on the given unit's seed, [skills/0001 § 10](../../findings/skills/0001-dispatch.md#10-item-granted-skills));
  one `[L]` open question for helper 2's unit and helpers 3 and 4 (plan 0046 Phase 1, item batch). combat/README B6,
  rng/seeds and wiki/combat hold no such claim: unchanged. Tags: delivery I 53 → 54, L 3 → 4; open questions 4 live
  of 7. Entry [closed](../../backlog/archive/2026-10-20-architect-spec-writer-combat-delivery-e5-item-target-2-draws.md);
  review request [to the architect](../../backlog/archive/2026-10-20-spec-writer-architect-review-lane-e5fix-combat-delivery-e5-item-target.md).
- **2026-10-20 — `lane/e5fix` review (architect): accept with fixes (1).** Checked on the pinned `Game.exe`: the call
  at `0x005FDB9F` (`ecx` = `ebx`, `edx` = `esi`), the loop `0x005FD900`–`0x005FD98A` (two inline steps per try on the
  seed at `edx+0x20`, `0xCCCCCCCD`/`shr 5` = ÷ 40, `− 0x14` on the path x and y, 10-try cap, success on a 0 from
  `0x0064D870`); Skills `ItemTarget` holds 2 only on Teleport (3 Corpse Explosion, Poison Explosion; 4 Bone Spirit,
  Fist of the Heavens; 1 one row); `0x005FDCA0`, `0x005FDD60`, `0x005FDA80`, `0x0064D870` resolve in `re/symbols.csv`.
  Fix (omission): the bullet now says the helper returns 0 with no room (`sub_00620BB0_UnitGetRoom`, 0 steps) or after
  10 failed tries, and `ITEMSKILL_Cast` then skips `SKILLS_SrvDo` (`je` at `0x005FDBA6`). Helpers 2–4 have no symbol
  rows: added to plan 0046 Phase 1's item, shrine and object batch. combat/delivery stays `reviewed`, tags
  {C 52, I 54, L 4} recounted. Review request closed.
- **2026-10-21 — From plan 0047's Phase 2 review (architect).** Two items for Phase 2. (1) The *Fleshripper* session's
  log is kept: `workspace/logs/combat/p47h-owf-n-andariel-p8.log` (`a411b34d…`, in `p47h-manifest.txt`; save
  `CombatOWF` `77807e00…`, seed 3712, Normal Andariel), so the oracle replacement's condition ("once its log is under
  `workspace/logs/combat/` with a manifest hash") is met. `tools/combat.py` (`bd80126a…`) gives 57 mismatches over 633
  events, all `expected AD1, got EVH`, each at an `EVH` line of the event-9 handler `0x005C01D0` (not the 101 of the
  lost log: another save build and seed). (2) A monster's own `MonAttackStats` inside its attack: `sandraider2` in mode
  14 (return `0x005CAED8`) calls it for mode 8 in 6 of 14 such events over 71 combat logs, and the build uses its
  output ([combat/0001 § 16](../../findings/combat/0001-formulas.md#16-plan-0047-phase-2-the-shortfalls-run2026-10-20-shortfalls),
  `[I]`); which events call it is unread and belongs with this plan's monster skill uses with `MonAttackStats`
  predicted. ([0047 log](0047-simulation-shortfalls.md#implementation-log), Phase 2 review rulings 4 and 6.)
- **2026-10-21 — Phase 2 started, paused at the owner's request (reverser, `lane/p45h`).** No session run, no slot
  used (slot 2 never launched, no aside taken), no Ghidra. Done: the logger `tools/gdb/skills.gdb` and
  `tools/gdb/skills.py` (rev 1, **untested**: never run against the game) with the entry points of the Phase 1 review
  ruling 1: `SKILLS_SrvStart`/`SrvDo` (SST/SDO), `PayCost`, `SetDelayState` (EAX the delay, EDI the unit),
  `MissileCreate` (MC, with the creation crit's mastery return at `0x0064A8F0`, the SUnitCreate parent seed at
  `0x00552E2F`/`0x00552E55`, the Firestorm re-seed callback `0x005C9290`/`0x005C92F4`), `MissileDoFrame` windowed at
  `0x005ADC97`/`0x005ADCA9` (gdb condition on `$skw0..7`, 30 missiles a session), `MISSILE_HitUnit`, `BuildDamage`
  (args `[esp+4]` missile, `+8` unit, `+0xC` packet; all its stats read from the missile, masteries 329–332/357 via
  `MulDiv`, the pct block only with a unit), boundaries `MISSILE_ApplyDamage`, `COMBAT_MeleeHitTest`,
  `DeliverQueued`, `ApplyDamage` (entry asserted, exit taken), the to-hit and defence stubs, `UNIT_DispatchEvent`
  handler calls, `PreventHealHook`, `STATE_ApplyTimed`, `RollElemDamage`'s `RangeB` (`0x0056E132`), the finisher and
  its two `srvprgfunc` call sites (`0x005D53F8`, `0x005D544C`), `SpawnOwnedMonster`, `SummonSetLevel`, `PetAdd`,
  Armageddon, `MonAttackStats`; exits matched by ESP at the functions' `ret` addresses (objdump of the pinned image).
  **Next (resume):**
  1. Smoke-test the logger on slot 2 (one short dev session, `dev-` log name under `workspace/logs/skills/`): a
     tier-A Sorceress recipe `tools/d2s_recipes/skills-sor.json` (stock uniques; Nova, Frost Nova, Static Field,
     Teleport, Fire Bolt, Meteor, Blaze ≥ 2 for C4; hotkeys F1..F6), entered with `enter-normal.steps`, driven by
     `d2pilot.py explore --melee --melee-button 3 --curse-keys F1,F2,…` (right-click casts on the nearest monster).
     `saves.py --slot 2 aside p45h` first, `slots.py stop 2` and `restore p45h` after.
  2. Write `tools/skills.py` (`check`, `manifest`): parse spans by `n`/`k`; per-seed observation ledger (inside an
     event every gap is a modelled draw or a boundary exit, across events a chained pair or a named resync); models:
     MC (unit seed `init(step(parent).low)` or the callback's `init(path+0x10 + arg)`, velocity
     `((VelLev·lvl)/8+Vel)<<8 ·75/100`, range `LevRange·lvl+Range`, activate, crit draws 337/141/mastery, pierce count
     from `init(b328)`), MH (to-hit, pierce use, BuildDamage's `RangeB` order and packet), MF (accel every fifth step,
     `(dir·((v·0x400)>>6))>>12`, remaining −1), handler draws per skills/0003 § 3, SL (C1 level), PAY (cost and
     `minmana` floor, ignored failure), DLY. `tools/test_skills.py` on hand-built lines.
  3. `tools/skills_sessions.py` (recipes per class for the 26 tier-A rows, sessions table, run) on the
     `stats_sessions.py` pattern; then the dev session, then `run:YYYY-MM-DD-skills` and the oracle re-checks.
- **2026-10-21 — Phase 2 resumed, paused again at the owner's request (reverser, `lane/p45h`).** Development only:
  no kept run, no claim raised, no finding edited. Slot 2 only, stopped (`slots.py stop 2`), saves restored, no aside
  left; no Ghidra. Done:
  - **Logger smoke-tested** and fixed: `tools/gdb/skills.py` rev 2 (`43a81216…`). Rev 1's `SL0` read `ECX` as the
    summon, but `ECX` is the game and the summon is the first stack argument; rev 2 logs the summon's stat 12 before
    and after. Every other tag fired as designed in six dev sessions.
  - **`tools/skills.py`** (`7d7417a2…`, `check`, `manifest`) models PAY (cost, `minmana` floor, refusal, a non-player's
    1), MC (velocity, accel/max, range, frames left, activate, skill/level, the missile seed from the game-seed step,
    the callback re-seed, the owner's 1–3 critical draws and stat 141, the pierce count from `Init(b328)`), MF (the
    fifth-step acceleration, the position step, frames left, seed), BD (the seven `RangeB` draws on the missile seed,
    the mastery `MulDiv`, the drawn fields, the physical percent and the critical doubling, lengths), THR's roll, a
    missed to-hit ending the missile with one pierce used (C5), SL (C1), SST/SDO caster seeds for the rows with no own
    draws, and the chaining (game seed between creations of one SrvDo, the caster's seed across skill events).
    `tools/test_skills.py` has 7 tests on hand-built lines, all passing.
  - **`tools/skills_sessions.py`** (`f5777a25…`, `build`, `list`, `run`) with recipes `tools/d2s_recipes/skills-{sor,
    ama,amaj,nec,dru,bar,pal,ass}.json` (clvl 80/85, stock items; built into `workspace/logs/skills/saves/`) and 18
    run sessions (`sor-1..4`, `ama-1..2`, `amaj-1..2`, `nec-1..2`, `dru-1..2`, `bar-1..2`, `pal-1..2`, `ass-1..2`).
    `tools/d2pilot.py` gains `--keys-cycle` (explore `--curse-keys` taken in turn over all clicks, not per monster).
  - **Dev logs** (kept, `workspace/logs/skills/dev-p45h-manifest.sha256` `caeabe2e…`; checker output
    `dev-p45h-check.txt` `94f85172…`): `dev-p45h-a-sor-smoke`, `-b-sor-smoke2`, `-c-nec-1`, `-c-pal-1`, `-c-ass-1`,
    `-c-amaj-1` (the last aborted mid-explore for this pause). Over the six: 10 901 creations with velocity, range, seed
    and owner draws all matching, 3 123 motion steps (108 accelerating, 18 fifth steps), 147 builds, 534 payments,
    40 physical packets, 72 pierce counts, 4 missed to-hits (1 with a pierce left), 3 Raise Skeleton summons (rev 1:
    no SL check), 9 887 game-seed chained pairs, 908 caster chained pairs; **7 mismatches, all `MF.seed`**, each in a
    frame where the missile hit a unit: the checker does not yet add the nested `MH`'s `BD`/`MA` draws on the
    missile seed. One unread observation: Raise Skeleton (do 31) steps the caster's seed once after
    `SpawnOwnedMonster` returns (3 of 3), where skills/0003 § 5 reads "none"; the site is not located.
  **Next (resume):**
  1. Fix `MF.seed` to allow the draws of an `MH` nested in the frame (the `BD` count plus the `MA` boundary exit).
  2. Locate the Raise Skeleton caster draw (between `SP1` and `SDO1`: `0x005C4430`, `SummonInitStats`, `0x005C40D0`
     or `0x005B1900`; static reading or one more logged exit), and correct skills/0003 § 5.
  3. Run `run:2026-10-2x-skills`: `skills_sessions.py build`, then `run --slot 2 --tag p45h --saves
     workspace/logs/skills/saves --run <run>` over the 18 sessions (about 3–4 min each); check, manifest, then the
     oracle re-checks (run:2026-10-16-combat, run:2026-10-17-stats, the *Fleshripper* log) under `MemoryMax=4G`.
  4. Shortfalls to expect and name: Kick, Left Hand Throw, Left Hand Swing (no session), `srvprgfunc` 36, 37, 40, 41,
     summons by Raven (no SL check yet with rev 2), the C2 `spike` monster missiles and the C4 `LevRange` rows (Blaze
     reaches C4), event-9 handler fires, state 52, the re-seed sites.
  5. Write the run record in `skills/experiments.md`, the per-claim raises in skills/0001–0003 (review-fixes 8, 12,
     14), the symbols raised, the review request and this log's entry.
  **Usage:** this resume 216 000 tokens and about 100 tool calls over about 75 min, on top of the first part's
  287 603 / 64 / 9 min.
- **2026-10-25 — Phase 2 run logged, paused at the owner's request (reverser, `lane/p45h`).** Not for review yet.
  Slot 2 only, stopped (`slots.py stop 2`), saves restored (no aside left); no Ghidra (objdump only). Done:
  - Resume items 1–3: `MF.seed` allows a nested hit's draws (`MF.hitseed`); the Raise Skeleton caster draw located
    (do 31 → `sub_005C4430_SummonClassRoll` → `0x005C4300`'s inline step at `0x005C4384`, class 363 at skill level > 2;
    class 364 via `0x005C4180`), logger rev 3 (`RSK0`/`RSK1`), skills/0003 § 5 corrected; `0x005C9290`'s re-seed is
    stepped 20 or 38 times by its path calls (§ 9 corrected; the checker's first `MC.cbseed` was wrong, fixed).
  - **run:2026-10-25-skills**: 18 sessions, **0 mismatches** over 335 618 checks (`tools/skills.py` `1b297c24…`,
    manifest `2026-10-25-skills-manifest.sha256` `8b01d216…`); record in skills/experiments.md, raises in
    skills/0002 § 11 and skills/0003 § 15 (with the Answer, Leads and Functions edits), 9 symbols raised to C, 4 new.
    The oracle replacement: `skills.py audit`, none replaceable (named).
  **Next (resume):** (1) skills/0001: a run section for `PAY` (1 334 player payments; no floor, no refusal for cost
  reached) and the chaining (caster 3 155 pairs), raise `SKILLS_PayCost` per review-fix 14; (2) re-read the new
  sections against review-fixes 1, 4, 8, 10, 12 (the C1/RSK raises rest on 8 cases each: say so or keep `[I]`);
  (3) the shortfalls are named in the record (handlers, state 52, MonAttackStats, summon seeds, C2, C4, rows under 30,
  Kick/LHT/LHS): decide whether a second run (slot 1 too, a walking Blaze, a `spike` monster area, a handler model)
  precedes the review; (4) gate, the review request (`tools/backlog.py new --from reverser --to architect`), the
  ledger row.
- **2026-10-27 — Phase 2 part 1 written up, review requested (reverser, `lane/p45h`).** `main` merged first (one
  conflict, this log's 0047 link, now `done/`; backlog archive: nothing to move). No session run, no slot launched
  (slot 2 idle, no aside), no Ghidra. Done:
  - [skills/0001 § 17](../../findings/skills/0001-dispatch.md#17-plan-0045-phase-2-the-run-run2026-10-25-skills): the
    payment raised in part (1 334 player payments, 259 no-cost, 205 non-player; floor, refusal, blood mana, charges
    unreached), no draw in the cost and delay steps of the checked events, the caster's chaining (3 155 of 3 459
    pairs, 304 unattributed gaps of 1–33 steps); Answer, § 7 and § 15 notes; `SKILLS_PayCost` raised to C in
    `re/symbols.csv` and the Functions table (review-fix 14).
  - Review-fixes pass over skills/0001 § 17, 0002 § 11 and 0003 § 15: the RSK and C1 raises headed "raised in part",
    with their 8 cases named as one input each and what they separate (fix 10: the C1 case separates the lead's 86 and
    a rounded-up 3/4, not the clamps); nine unanchored `[I]` remainders given their `run:` anchor (fix 7, gate W1).
  - **No second run before the review.** A rerun with the current checker would only add events to the seven tier-A
    rows under 30; the other shortfalls (request refusals, handlers and state 52, `MonAttackStats`, summon seeds and
    stats, hit ends and pierce uses, re-seed sites, C2, C4) need new models, a `CanUse` breakpoint or pilot changes.
    Proposed as Phase 2 part 2 in the review request, for the architect's ruling.
  - Review request: [backlog](../../backlog/archive/2026-10-27-reverser-architect-review-lane-p45h-plan-0045-phase-2-run.md).
- **2026-10-27 — Phase 2 part 1 review (architect, `lane/p45h` at `c167c4f`, `main` merged first): accept with
  fixes.** Static, objdump only, no slot, no Ghidra.
  - **Re-checked.** The manifest `2026-10-25-skills-manifest.sha256` (`8b01d216…`, 48 files) passes `sha256sum -c`
    from `workspace/logs/skills`; `tools/skills.py` `1b297c24…` re-run under `MemoryMax=4G` gives `check.txt`
    (`17555e43…`), `check.json` (`5619ca23…`), `tally.txt` (`b82c4040…`) and `audit.txt` (`96816fa4…`) byte for byte;
    the check table sums to 335 618 ok, 0 mismatches; `tools/test_skills.py` 8 of 8. Logger rev 3 (`12e30fe5…`),
    `skills.gdb` (`92420a1c…`) and `skills_sessions.py` (`f5777a25…`) match the record; `d2pilot.py`'s `b1db3063…` is
    the lane's revision at `157c296` (main's H4a merge changed it since: part 2 names its own). Counts recomputed from
    the kept outputs: `PAY` 1 334 + 259 + 205 = 1 798; `CHAIN.caster` 3 155 + 304 resyncs = 3 459, the resync
    distribution sums to 304 over 1–33 steps; BD 39 + 720 + 19 = 778; SL 8 + 207 = 215; delay states 30 + 221 + 26 = 277.
    Anchors (objdump): `0x005C4C7A` is `call 0x5C4430` with `0x005C4C7F` its return; `0x005C4384` is the inline LCG
    step (`mov ecx,0x6AC690C5`, `mul`, `adc` into the seed's `+0x24`); `SKILLS_PayCost` `0x0056BFE0` returns 1 at once
    for a null unit or a unit whose type word is not 0 (the players-only branch). The symbol raises (`SKILLS_PayCost`,
    the 0002 § 11 and 0003 § 15 rows: `0x0059F940`, `0x0064A850`, `0x005C4430`, `0x005C9290` spot-checked) are `C` in
    `re/symbols.csv` with the finding holding the claim (review-fix 14). The "raised in part" heads (RSK, C1, the
    payment) say what the one input separates (review-fixes 8, 10).
  - **Fixes (made here):** (1) *miscount:* the record's "2 708 do events and 2 508 start events" are 1 840 and 1 688
    (the logs' `SDO0`/`SST0` lines, the tally's rows summed); corrected in skills/experiments. (2) *omission:* with
    them the 2 000 skill-use floor is short (1 409 do events in tier-A rows), named neither in the record nor in the
    request's point (a); named in the record and in part 2. (3) *misread:* skills/0001 § 17's "what draws in those
    304 gaps … is not logged by this run": the run logs the caster's own to-hit rolls (`THR`, the owner's next draw,
    checked 269 times), and **87 of the 133 player gaps step exactly as many times as that unit's `THR` lines between
    the events**; 31 more find the player a hit's defender (combat/0001's defence draws on the defender's seed), 4 hold
    fewer `THR` than steps, 1 other, 10 no line naming the unit; of the 171 monster gaps 146 hold `MonAttackStats`
    calls (each leaving the seed unchanged) and 25 none. Review aid kept: `workspace/logs/skills/2026-10-25-skills-review/`
    (`caster_gaps.py` `fb547873…`, `caster-gaps.txt` `67be8e5f…`, the re-check outputs; `manifest.sha256`
    `9b1d157b…`, `sha256sum -c` passes there). The bullet rewritten with this sort at `[I]` (a count that matches is
    not a draw-for-draw check), the § 15 note and the record's chaining line likewise.
  - **Ruling (a): a Phase 2 part 2, no second run of part 1's kind.** Agreed: a rerun with the current checker would
    only add events to the short rows. Part 2 is written above (*Phase 2 part 2*) with its *Done when*; it counts part
    1's events toward the floors. **Part 1 is accepted** as the reproduction of what it checked: every raise in skills/0001
    § 17, 0002 § 11 and 0003 § 15 stands as split (the fixes above change no tag).
  - **Ruling (b): the oracle-replacement record meets that item for the packet and aura oracles, not yet for the
    handler fires.** Verified on the kept logs: run:2026-10-16-combat's `MS0` lines carry the missile's seed (`mi.s`)
    but no missile stat list before `"o"`, and its `BD0`/`BD1` lines carry the attacker's and defender's seeds
    (`sa`/`sd`), not the missile's; run:2026-10-17-stats' aura runs have no `REL` line (`s1017-pal-oasis.log`: 0). So
    "none replaceable" is the logs' limit there, as the item allows. The 3 461 handler fires are "not replaceable"
    because the tool has no handler model, which is this tool's shortfall, not the logs': the audit re-runs for them
    in part 2 once the handler model exists (part 2, item 8).
  - **Ruling (c): accepted as an observation; part 2 attributes the player resyncs, the monster ones may stay open.**
    The `[C]` bullet states only the measured chaining (3 155 of 3 459, every resync on the stream within 4 096 steps),
    which holds. Part 2's checker adds the caster's own logged draws between skill events (`THR` first) and re-checks
    part 1's 304; every player resync left is attributed to a modelled draw (the defence rolls of combat/0001) or listed
    with its lines. The monster resyncs, where `MonAttackStats` leaves the seed unchanged, point at the AI, which is
    out of this plan (plan 0052, monster AI, proposed); they stay open there and in the spec's *Open questions*.
  - **Gates.** Part 1's acceptance is the acceptance plan 0050's approval waits for: **0050 is in effect, and 0050·P0,
    P1 and P1b are open** (data and static work, which take the action frame as part 1 logs it). **0045·P3 may start
    now** (spec-writer), the statements part 2 targets written `[I]`, re-tagged from part 2's reviewed raises; **the
    0045·P3 review waits for part 2's review**, so 0050·P2, 0046·P2 and 0052's approvability, all gated on that
    review, stay closed. Part 2 takes harness slot 2 (slot 1 too when free), never beside 0044·P2.
  - **Ledger:** 3 fixes: miscount 1, omission 1, misread 1. Reverser review-fixes 2 and 4 gain Seen lines.
  - **Backlog:** review request closed.
  - **Next:** merge `lane/p45h`; 0045·P3 (spec-writer) and 0050·P0 (archivist) and P1/P1b (static) as the run order
    places them; Phase 2 part 2 (reverser, harness) when slot 2 is scheduled.
- **2026-10-27 — Phase 3 written, review requested (spec-writer, `lane/s45p3`).** In parallel with Phase 2 part 2
  (`lane/p45k`), as the part 1 review allowed; no Ghidra, no harness. New, `status: draft`:
  [skills/README](../../specs/skills/README.md) `{C: 16, I: 24, L: 3}`, [skills/dispatch](../../specs/skills/dispatch.md)
  `{C: 35, I: 185, L: 11}`, [skills/missiles](../../specs/skills/missiles.md) `{C: 42, I: 88, L: 6}` (93 / 297 / 20 in
  all; 20 open questions, every `[L]` under *Open questions*). The *Done when* items: a sequence diagram per event kind
  (dispatch § A, missiles § A, the README's event table), the start checks as a decision order (dispatch § C), the
  packet as pseudocode with its widths (dispatch § I, missiles § F), the missile's life as a state diagram with its
  per-frame motion (missiles, D3–D4), the handler table (dispatch § K), worked examples from run:2026-10-25-skills
  (Raise Skeleton's level 84 and its one caster step; Firestorm's `0x005C9290` seeds). Statements that part 2 targets
  (refusals, handlers and state 52, `MonAttackStats`, summon seeds and stats, hit ends and pierce uses, re-seed sites,
  C2, C4, the short rows, the resyncs) stay at the findings' tags for the re-tag pass. Updated: combat/README (the
  phase (3) open question struck in part and rewritten), stats/states (the self-states question struck, one `[L]`
  kept), items/economy H6 (Impale's wear; the draw under the weapon tests; one `[L]` struck), rng/seeds
  (`0x005C9290` `[C]`); wiki economy and randomness edited, three `based_on` bumps; glossary four terms. Not edited:
  table docs (plan 0051's `lane/p51b`), data/calc, monsters/spawn, monsters/stats, drlg/collision (no new answer;
  drlg/collision held by 0038 P3). One count queried in the request: the eleven rows' do counts in skills/0003 § 15
  sum to 947, not the 1 269 cited. Review:
  [request](../../backlog/archive/2026-10-27-spec-writer-architect-review-lane-s45p3-plan-0045-phase-3-skills.md); it waits for
  part 2's review.
- **2026-10-27 — Phase 2 part 2 written up, review requested (reverser, `lane/p45k`).** Slot 2 only (slot 1 held by
  `lane/h5d`), stopped after every session (`slots.py stop 2`), saves restored, no aside left; no Ghidra (objdump only;
  nothing deferred to Ghidra). `main` merged (`f979d04d`, no conflict). Done:
  - **Logger** `tools/gdb/skills.py` rev 4 (`5459da8a…`): `SKILLS_CanUse` at the request (`CU0`/`CUL`/`CU1`), the
    handler's stat, other unit and packet on `EVH`, `MonAttackStats`' elemental stats, the summon's stats, `THR`/`DRR`
    outside the spans; rev 5 (`e28d1344…`, from the fourth session on): the client's per-frame `CanUse` at its changes
    of code (the request handlers received no refused request: the client refuses first).
  - **Checker** `tools/skills.py` (`c09f9419…`; tests 12 passing): models of `MonAttackStats`, the stat-event handlers,
    the state-52 hook, `CanUse`'s codes, the summon's seed and stats (through `tools/monstats.py`), the end of a
    damaging hit, and `CHAIN.caster` walking the unit's own logged draws (ruling (c)); the handler audit (ruling (b)).
  - **run:2026-10-27-skills**: 15 sessions, recipes `skills-barh.json` (new: the handler items, Kick, Left Hand Throw,
    Left Hand Swing by the Attack alternation) and `skills-sorlow.json` (new: low mana); 0 mismatches, part 1's 18 logs
    re-checked with 0. Record: [skills/experiments § run:2026-10-27-skills](../../findings/skills/experiments.md#run2026-10-27-skills);
    raises in skills/0001 § 18, 0002 § 12, 0003 § 16 and monsters/0004 § 9 (a new `[I]` reading: El2/El3 take El1's
    bounds by the mask `0x40 + e`); four symbols raised to C.
  - **The floors with part 1:** met for skill uses, handlers, state 52, summons, `MonAttackStats`, hit ends and pierce
    uses, C4, the handler audit (3 461 of 3 461 fires) and the 304 resyncs (player ones attributed or listed, monster
    ones to plan 0052). **Short, named:** the request refusals (the client filter; delay 76 and mana 8 at the client's
    check, town 0), C2 (22 `spike2` at level 1), the re-seed sites other than `0x005C9290` (named unreached), 70 Raise
    Skeleton (12 do events).
  - The orchestrator's count note on skills/0001 § 17 and 0003 § 15 answered: "1 269 do / 1 142 start" are the
    `SDO.seed`/`SST.seed` totals over 18 and 15 rows, not the eleven rows' (947/828); corrected in both.
  - Review request: [backlog](../../backlog/archive/2026-10-27-reverser-architect-review-lane-p45k-plan-0045-phase-2-part.md);
    table links for the archivist: [backlog](../../backlog/archive/2026-10-27-reverser-archivist-plan-0045-phase-2-part-2-table-readings.md).
- **2026-10-27 — `lane/p45k` reviewed (architect): accept with fixes. Phase 2 is done.** `main` merged first
  (`4638beca`, no conflict; `backlog.py archive` clean). Checked against the kept outputs, objdump only (no harness, no
  Ghidra): `tools/skills.py` hashes `c09f9419…`, `tools/gdb/skills.py` `e28d1344…`; its 12 tests pass;
  `sha256sum -c 2026-10-27-skills-manifest.sha256` (`08b79a9b…`, 49 files) OK; `check` re-run under
  `systemd-run --user --scope -p MemoryMax=4G` over part 2's 15 logs and part 1's 18 gives `check.txt`, `check.json`,
  `gaps.txt`, `part1-check.txt`, `part1-check.json` and `part1-gaps.txt` byte for byte (0 mismatches in every row),
  and `tally-both.txt` and `audit.txt` likewise. Recounted from them: 3 183 do / 2 985 start events, the 26 tier-A rows
  2 375 (Raise Skeleton 12, every other ≥ 30); `CU` 1 340 (code 8 76, code 1 8, code 6 1); `EVH` 1 303 over events
  1, 2, 5, 6, 9, 11, event 9 328, the per-handler counts of skills/0003 § 16 summing to 1 303; `PH` 918, state 52 86;
  `SP` 219 (207 + 12); `MAS.stats` 26 425, `MAS.seed` 26 955 (26 439 modelled + 516 before a list); the caster walk
  90 of part 1's 133 player resyncs (the ten attributed rows), part 1's 43 = 31 + 11 + 1, monster 171 = 131 + 33 + 7,
  part 2's 308 = 45 + 103 + 160; the count basis of skills/0001 § 17 and 0003 § 15 (947 + 106 + 208 + 8 = 1 269,
  828 + 106 + 208 = 1 142, the eleven rows' do counts summing to 947). Anchors on the pinned image: `MonAttackStats`
  calls `STATLIST_Clear` at `0x005A4FB3`; `[ebp−0x30] = 0xFFFFFF42 − rec` (`0x005A51D7`), `ebx = rec + 0xFE` stepping by
  1 per `e` (`0x005A542C`), `ecx = [ebp−0x30] + ebx` = `0x40 + e` (`0x005A525C`) pushed as `MonLvlStats`' fifth
  argument, which `0x006538A0` tests bit by bit at `[ebp+0x18]` (`0x01` … `0x80`): El2/El3 take El1's block plus HP/AC,
  as monsters/0004 § 9 reads (`[I]`, rightly). `SKILLS_CanUse`'s ten `ret 8`s, the four request call sites
  (`0x00549B0A`, `0x00549B44`, `0x00549BC1`, `0x00549C0C`), the client call at `0x004D9FC5`; `SKILLS_ManaOk`'s
  `add edi,eax` at `0x00647589`, the `max(lvl − 1, 0)` clamp and the `setge` (a cost equal to the mana passes);
  `0x00645390` has no call and no absolute reference in the image; `0x005AC073` calls `RNG_SeedInit` inside
  `0x005AC040`, whose address is stored at `0x005AC14B` and `0x005AC525`. The four symbol raises fit review-fix 14.
  - **Fixes (3):** (1) skills/0001's Answer bullet for part 2 gave, inside its `[C]`, the client filter as the reason
    no refused request reached the server; § 18 holds that reason `[I]`: reworded (overclaim). (2) The research map's
    `skills/dispatch` and `skills/missiles` rows still said "Phase 2 and the spec not started": Phase 2 done, the spec
    drafted on `lane/s45p3` (stale cross-reference; the part 1 review's miss, architect review-fixes 8). (3) skills/0002
    § 12's `VelLev` remainder now names the `spike1` route of ruling (b) (stale cross-reference: the remainder said a
    level-1 spike cannot separate, which holds for `spike2` only). Plans index row updated; review-fixes Seen lines
    (reverser 12, architect 8).
  - **Ruling (a): accepted as a named shortfall.** The codes are `SKILLS_CanUse`'s own: the client calls the same
    function on its copy of the player (`0x004D9FC5`), so codes 1, 6 and 8 and their order are `[C]` from those 214
    client changes with the 1 126 request calls, and the request at `f + d` passing is a server observation. What a
    stock client never reaches is the server's handling of a refused request (`PLRMSG_*`'s branch on a non-zero code,
    `sub_00549A60_NoManaMsg`) and `SKILLS_SrvStart`'s `InTown` test: they stay `[I]` from the code reading, and the
    client filter itself stays `[I]` (the sending code not read). No forged-request test now: it needs plan 0044's
    two-client harness or a patched client, and a reimplementation of a stock-client game does not depend on it. The
    spec states the server path at `[I]` and says a stock client sends no refused request (`[I]`, with the run).
  - **Ruling (b): no Nightmare/Hell quill-rat session.** C2 is named short and `VelLev` stays `[I]` with the
    contradicted lead under the spec's *Open questions*. The lane's "a level-1 spike cannot separate" holds for
    `spike2`–`spike4` (`VelLev` 7, 6, 4) but not `spike1` (`VelLev` 8: `(8 · 1) / 8 = 1`, velocity 11 against the
    lead's 10); `quillrat1` (its `MissA2` is `spike1`, a table reading) is in the Blood Moor's pool in every difficulty.
    Carried as an opportunistic check, no session of its own:
    [backlog](../../backlog/2026-10-27-architect-reverser-plan-0045-c2-vellev-by-a-blood-moor.md).
  - **Ruling (c): Raise Skeleton at 12 accepted.** The summon family's floor is met by the 207 Ravens (seed, life,
    defence with a 20–32 range that separates), as Phase 1's tier-A substitution rule allows; do 31's class draw and
    level formula keep their `[C]` at 12 of 12 with the scoping already in skills/0003 § 15 (one input, the clamps not
    binding). The spec gives the count.
  - **Gates.** Phase 2 is done (part 1 and part 2 accepted). **The 0045·P3 review of `lane/s45p3` may start now**, once
    this lane is merged into `main`. Before it, or as its first fixes if it starts first, the spec-writer merges `main`
    into `lane/s45p3` and re-tags from part 2's reviewed raises: in skills/dispatch, `SKILLS_CanUse`'s codes 0, 1, 6, 8
    and their order, the equal-cost pass and the delay test only for a row with `delay` `[C]` (codes 2–5, 7, charges,
    blood mana `[I]`), the delay state's end at `f + d` `[C]`, the client filter `[I]` (ruling (a)); `MonAttackStats`'
    21/22/19 by the mode's `A1`/`A2`/`S1` columns and its `El` rolls as its only draws `[C]`, the list clear and El2/El3
    with El1's bounds `[I]`; the handlers' draws column `[C]` for the handlers skills/0003 § 16 lists, heal and mana after
    kill (the cap; life's addition) `[C]`, open wounds' roll `[C]`, state 52 by stat 117 with no draw `[C]`; the summon's
    seed, life and defence `[C]`; Kick, Left Hand Throw, Left Hand Swing and the five rows now over 30 `[C]`; the
    caster chaining (90 of 133, 45 of 148 attributed) `[C]`, the rest listed `[I]`; the 1 269/1 142 basis of its point 1
    (the seed-check totals; the eleven rows 947 do / 828 start). In skills/missiles, `LevRange · lvl + Range` `[C]`
    (C4, the lead resolved contradicted), the end of a damaging hit and the pierce use for rows with no hit function
    `[C]`, `VelLev` `[I]` (ruling (b)), the re-seed sites other than `0x005C9290` named unreached `[I]`. And the targets
    its request left unedited: monsters/stats (`MonAttackStats`, the summon's seed and stats) and monsters/spawn (the
    summons), from monsters/0004 § 9 and skills/0003 § 16; combat and stats/states for state 52. 0045·P3's acceptance
    then opens 0050·P2, 0046·P2 and 0052's approvability.
  - Review request closed; ledger: the lane row filled (verdict, fixes 3: overclaim 1, stale cross-reference 2), the
    review row added with its usage "—". Gate E13 from `main`: the context links of two 2026-10-27 spec-writer entries
    `0038…#log` pointed at no heading, now `#implementation-log`.
- **2026-10-27 — Phase 3 re-tag pass from part 2's reviewed raises (spec-writer, `lane/s45p3`).** `main` merged
  twice (`07b2fca0`: part 2 accepted at `7386da27`, the plan log and ledger conflicts kept both sides; `797b1bf8`:
  `lane/sfx` landed at `450accc9`, the ledger conflict kept both sides; `backlog.py archive` clean). No Ghidra, no
  harness. The re-tags the part 2 review lists, each raise naming run:2026-10-27-skills:
  - **skills/dispatch:** `SKILLS_CanUse`'s codes 0, 1, 6, 8 and their order, the equal-cost pass, the delay test only
    for a row with `delay` `[C]` (codes 2–5, 7, `startmana`, charges, blood mana `[I]`); no refused request reached the
    server in the run `[C]`, a stock client sending none and the server path `[I]` (ruling (a)); the delay's end at
    `f + d` `[C]`, the per-frame refusal up to it and the client's frame `[I]`; `MonAttackStats`' 21/22/19 by
    `A1`/`A2`/`S1` and its `El` rolls as its only draws `[C]`, the list clear and El2/El3 with El1's bounds `[I]`; the
    handler table's draws column `[C]` for 5–9, 13, 15–17, 19–22, 28, 29, heal and mana after a kill (the cap, life's
    addition) `[C]`, open wounds' roll `[C]`, the 3 461-fire audit `[C]`; state 52 by stat 117, no draw `[C]`; the
    summon's seed, life and defence `[C]` (219), the summon level and do 31's step at 12 of 12; Kick, Left Hand Throw,
    Left Hand Swing and the five rows now over 30 `[C]`, Raise Skeleton at 12; the caster chaining (90 of 133, 45 of
    148) `[C]`, the rest listed `[I]`; § O and E4 on the corrected basis (1 269/1 142 the per-row seed-check totals,
    the eleven rows 947 do / 828 start). Six open questions struck, five remainders written `[L]`.
  - **skills/missiles:** `LevRange · lvl + Range` `[C]` (C4, the lead contradicted); the end of a damaging hit and the
    pierce use for rows with no hit function `[C]`, the rest `[I]`; `VelLev` `[I]` with the contradicted lead under
    *Open questions* (ruling (b)); the re-seed sites other than `0x005C9290` named unreached `[I]`.
  - **skills/README:** the entry, event and branch tables, B2 (chaining) and B4 (handlers) re-tagged; the part 2
    open question struck.
  - **Not edited by the first draft, now:** monsters/stats (F3: the summon's seed, life and defence `[C]`; H1: stats
    21/22/19 and the modes' columns `[C]`, the part 2 draws `[C]`, the list clear and El2/El3 `[I]`; the open question
    split), monsters/spawn (J3: a skill summon's creation `[C]`, on `main`'s text after `lane/sfx`), combat/README (B6:
    the handlers' draws and state 52 `[C]`; two open questions rewritten whole), stats/states (B2: state 52 and open
    wounds' state 62 `[C]`, the hook's type and class tests `[I]`).
  - Counts: skills/README `{C: 16, I: 24, L: 3}` → `{C: 23, I: 25, L: 2}`, skills/dispatch `{C: 35, I: 185, L: 11}` →
  `{C: 72, I: 187, L: 10}`, skills/missiles `{C: 42, I: 88, L: 6}` → `{C: 46, I: 90, L: 6}`, monsters/stats
  `{C: 130, I: 47, L: 5}` → `{C: 134, I: 50, L: 5}`, monsters/spawn `{C: 136, I: 44, L: 5}` → `{C: 137, I: 45, L: 5}`,
  combat/README `{C: 39, I: 42, L: 5}` → `{C: 41, I: 42, L: 5}`, stats/states `{C: 51, I: 53, L: 6}` →
  `{C: 52, I: 54, L: 6}`. Wiki: combat (a monster's attack stats) and stats-and-states (prevent heal) edited, a `based_on`
    line added to each; every `based_on` date of the edited specs is 2026-10-27, so W4 stays clear.
  - Review: the [request](../../backlog/archive/2026-10-27-spec-writer-architect-review-lane-s45p3-plan-0045-phase-3-skills.md)
    has a dated addendum; no new request filed. Gate E9 (on `main`'s gate) flagged two first-draft sequence diagrams
    (dispatch A3, missiles A) for a `;` inside a message, which Mermaid reads as a separator: replaced by a comma.
- **2026-10-27 — `lane/s45p3` reviewed (architect): accept with fixes. Phase 3 is done.** `main` merged first
  (`51345d5d`: `lane/h1b` landed at `2b087d2c`, the ledger conflict kept both sides; `backlog.py archive` clean). Static,
  objdump on the pinned image only (no harness, no Ghidra). Checked against *Done when*: a sequence diagram per event
  kind (dispatch A1 request/start/do/cost, A3 finisher/handler/summon, state 52 added here; missiles § A
  create/frame/hit/end; a monster's start and do, A2, are the same events and stay prose), the `SKILLS_CanUse` order
  as a flowchart (dispatch § C), the packet (dispatch I1–I2) and `MISSILE_BuildDamage` (missiles F1) as pseudocode with
  widths, the missile's life as a state diagram with D3–D4's per-frame motion, the 31-handler table (dispatch § K, ids
  1–31, 11/12 and 14–16 grouped), and the two worked examples (Raise Skeleton's 84 and its step; Firestorm's
  `0x005C9290` seeds), both from run:2026-10-25-skills. Every `[C]` checked against skills/0001 §§ 17–18, 0002 §§ 11–12,
  0003 §§ 15–16 and monsters/0004 § 9 and the two Phase 2 rulings: refusals `[C]` only for codes 0, 1, 6, 8 (and their
  order) from the 1 340 calls, the server's handling of a refused request, the client filter, codes 2–5 and 7 `[I]`;
  `VelLev` `[I]` with the lead under *Open questions*; Raise Skeleton at 12; the 1 269 / 1 142 basis as corrected. No
  `[L]` outside *Open questions* (gate E5); the front-matter counts match (E6); every `fn:`/`data:` anchor resolves (E1).
  Objdump: `SKILLS_SrvDo`'s bound `cmp ax,0xBF` at `0x0056F911` and `SrvStart`'s `0x5B` at `0x0056F75D`;
  `MissileDoFrame`'s `movsx` and its count `[0x0073C71C]` at `0x005ADBFB`; stat 328 (`push 0x148`) at `0x00549D4A`;
  `SKILLS_RollElemDamage`'s `RangeB(max − min)` at `0x0056E12A`–`0x0056E132`; `PreventHealHook` at `0x0057DB80` with
  state `0x34`, `0x1D4C0` frames and stat `0x1F` (`0x0057D879`–`0x0057D891`); `SummonSetLevel`'s signed `÷ 4`
  (`cdq; and edx,3; add; sar 2`, `0x005C4A02`–`0x005C4A0A`) and its clamps; `SkillWeaponWear`'s two exclusive branches,
  each one inline step (`0x005DAA70`, `0x005DAABC`), as items/economy H6 now has it; do 31's `call 0x5C4430` at
  `0x005C4C7A`; `MISSILE_BuildDamage`'s seven pairs in the order F1 gives (stats `0x30`/`0x31` … `0x13C`/`0x13D` with
  masteries `0x149`, `0x165`, `0x14A`, `0x14B`, `0x14C`, `0x149`).
  - **Fixes (9, made here):** (1) *misread:* missiles F1 read the mastery as `stat(owner, mastery)`; the code reads it
    on the missile (`STATS_GetUnitStat` at `0x005A895F`, as for the bounds), as `tools/skills.py`'s `bd` does: fixed,
    the `[C]` note says so. (2) *omission:* F1 had no swap of an inverted pair (`0x005A894B`, physical `0x005A89EB`)
    and tested the bounds after the mastery: rewritten, one new `[I]` bullet (missiles I 90 → 92 with the inline swap
    tag); the finding gap filed for the reverser
    ([backlog](../../backlog/archive/2026-10-27-architect-reverser-skills-0002-builddamage-pair-swap-and-unit.md)). (3)
    *misread:* missiles § A drew the creation callback after the critical chain and the pierce count; H2 and B1 run it
    before the damage block: moved. (4) *wrong anchor:* the three gate W1 warnings (missiles D4's `v < 0`, F1's pair
    order and stat 180 inline tags) carried no anchor: anchored (the ruling on the W1 warnings). (5) *other:* the
    overview's two "B4" bullets: the finisher one is B5. (6) *omission:* the overview's conventions now link `MulDiv`
    (monsters/stats § A) for dispatch I4, M2 and missiles F1. (7) *omission:* state 52 had no diagram: a note in
    dispatch A3. (8) *under-claim:* dispatch § O's Raise Skeleton row cited part 1's run only; 12 of 12 over both runs.
    (9) *overclaim:* the glossary's pet limit removed "the oldest" pet; the code removes the first of its list.
    Promotion bookkeeping (not counted): the three skills specs and the overview's file table `reviewed`;
    combat/README's and stats/states' "plan 0045 Phase 3, draft" made current.
  - **Ruling (a): "tier A lives here."** Accepted. The tier-A start, do and missile functions are specified once, in
    dispatch § O and missiles § G, and the plan 0046 boundary reproductions they cite stand as `[C]` up to their calls.
    When the `skills/catalogue` spec (0046·P3) is written it links those sections for the tier-A rows and does not
    restate them; the research map's catalogue row says so.
  - **Ruling (b): the specs the plan named that got no edit.** After the re-tag pass, two remain unedited, rightly:
    data/calc (no 0045 finding answers `MISS_CalcVar` 19–27 or a monster's `BearSmite` cast; its open question stays
    `[L]` there) and drlg/collision (its § F missile-side `0x40` paragraph already holds what skills/0002 and missiles D7
    give: collide type 7 the only missile reader, used by no stock row; nothing new to add). monsters/spawn,
    monsters/stats, combat and stats/states carry part 2's statements (checked: J3, F3, H1, B6, B2 within skills/0003 § 16
    and monsters/0004 § 9's scope).
  - **Ruling (c): the counts.** Part 2 re-checked § 11's creation, motion and build checks over more events (19 667
    creations, 3 340 builds, 124 missed to-hits); the spec states part 1's counts with part 1's anchor, which is
    correct; no change asked.
  - **Final counts:** skills/README `{C: 23, I: 25, L: 2}`, skills/dispatch `{C: 72, I: 187, L: 10}`, skills/missiles
    `{C: 46, I: 92, L: 6}`; monsters/stats `{C: 134, I: 50, L: 5}`, monsters/spawn `{C: 137, I: 45, L: 5}`,
    combat/README `{C: 41, I: 42, L: 5}` (combat's five summed C 240 / I 191 / L 24), stats/states `{C: 52, I: 54, L: 6}`,
    items/economy `{C: 125, I: 85, L: 11}`, rng/seeds `{C: 81, I: 14, L: 4}`. Research-map rows rewritten: skills/dispatch
    and skills/missiles `reviewed`; combat, stats/states, monsters/spawn, monsters/stats, rng/seeds and items/economy
    (the last stale since 2026-10-20: `I 83 / L 12`) with their counts; skills/catalogue, anim/timing and monsters/ai
    with the gates below.
  - **Gates.** **Phase 3 is done; this acceptance opens 0050·P2** (harness, one slot, before 0046·P2 per the run order),
    **0046·P2** (one slot) and **plan 0052's approvability**: the owner approves 0052, after the architect's re-draft,
    which is not part of this review
    ([backlog](../../backlog/archive/2026-10-27-architect-architect-plan-0052-re-draft-and-what-follows.md), with the owner's
    2026-10-27 "propose what follows 0052"). **0045·P4 (the wiki page `docs/wiki/skills.md`) may start** (spec-writer).
  - Review request closed
    ([archive](../../backlog/archive/2026-10-27-spec-writer-architect-review-lane-s45p3-plan-0045-phase-3-skills.md));
    review-fixes Seen lines (spec-writer 3, 4, 8, 9; architect 8). Ledger: the lane row filled (verdict, fixes 9:
    overclaim 1, under-claim 1, misread 2, omission 3, wrong anchor 1, other 1), the re-tag pass row's usage filled
    from the orchestrator, the review row added with its usage "—".
- **2026-10-27 — Phase 4 written, review requested (spec-writer, `lane/s45p4`).** Branched from `main` at
  `c62d9e39`; no Ghidra, no harness. New: [wiki/skills](../../wiki/skills.md) (ADR-0012), `based_on` skills/README,
  skills/dispatch and skills/missiles at `2026-10-27`; 22 sections, each linking its spec section; three diagrams (the
  event chain, the missile's life, the draw order of one missile with the creation callback before the critical
  roll); two worked examples from run:2026-10-25-skills (Raise Skeleton's 84, Firestorm's re-seeds) and one made-up
  cost; *What is not known yet* from the three specs' open questions. Linked from the wiki index (reading-order row
  12; rows 13–15 renumbered; the *What the wiki does not cover* sentences on 0045 and 0046 rewritten whole) and from
  wiki/combat, wiki/stats-and-states and wiki/randomness (links, and the "still to come" phrases they replace; no
  `based_on` bump needed). Review:
  [request](../../backlog/archive/2026-10-27-spec-writer-architect-review-lane-s45p4-plan-0045-phase-4-wiki.md). Ledger row added
  with usage "—".
- **2026-10-27 — `lane/s45p4` reviewed (architect): accept with fixes. Phase 4 is done; the plan is closed.** `main`
  merged first (alone; the ledger conflict kept both sides; `backlog.py archive` a no-op). Every statement of
  [wiki/skills](../../wiki/skills.md) checked against the section of skills/README, dispatch or missiles it links: the
  tags, the conditions and every number (1 340, 1 126, 85, 1 142/1 269, 251 of 277, 1 334, 258, 205, 1 303, 3 461,
  154 of 156, 82 of 120, 86 of 918, 219, 207, 26 425, 21, 31 391, 21 860, 271, 984/30 407, 1 066, 493, 11 413, 37, 105
  and 7, 778, 19, 3 876 = 130 + 276 + 3 470, 450, 3 155 of 3 459, 304, 90 of 133, 45 of 148, 43 and 103, 32/36/30, 48,
  23 delay rows); 22 sections, counted. The made-up cost (`mana` 8, `lvlmana` 1, `manashift` 8, level 5:
  `(1 × 4 + 8) << 8` = 3 072, 12 mana) is labelled made up and matches dispatch F1. The three diagrams illustrate only:
  the event chain is the overview's, the missile's life restates § D and § E (one edge completed, fix 8), and the
  draw order keeps missiles § A's order with the creation callback before the critical roll. The index row and the
  edits to combat, stats-and-states and randomness are links and the stale phrases they replace; combat's rewritten
  "Skills and missiles" bullet matches combat/README's struck phase-3 open question ("Specified in skills/dispatch §
  I and skills/missiles"), and the open remainder it names is the skills page's.
  - **Fixes (9, made here, all on wiki/skills):** (1) *overclaim:* "five uses with exactly as much mana … went
    through": dispatch C4's 5 are `SKILLS_CanUse` calls, some of them the client's check: "five checks … returned 0".
    (2) *overclaim:* Kick "builds a fixed hit": "fixed" is not in § O, whose builder fields are the reading
    (`[I]` the build); now the builder's values, read from the code, and the 32 events' seed result confirmed
    (ruling (b)). (3) *misread:* § I's `Kick` damage, set beside Kick's start hit, read as the damage Kick's hit
    carries; § O's builder takes the row's `MinDam`: scoped to "a row flagged `Kick`", with the start function's
    `MinDam` named. (4) *omission:* the 3 461 earlier fires include the *Fleshripper* log (dispatch K2). (5)
    *overclaim:* "this chain is not the melee build's" stated flat in a confirmed bullet (combat/README B4 `[I]`): read
    from the code. (6) *overclaim:* the direction table inside the confirmed motion sentence (missiles D4's `dir` is
    `[I]`): split out. (7) *misread:* `k` "the sub-missile's index" for the monster's class-195 missiles too; H1 gives
    the callback's argument, the index for Firestorm: so worded. (8) *omission:* the state diagram's end of life lacked
    D3's step that does not move. (9) *overclaim:* "applies the elemental mastery to both bounds" inside the 778-build
    confirmed sentence: moved to the code reading (ruling (a)).
  - **Ruling (a): missiles § F1's two bullets.** They disagree in strength: the `[C]` bullet carries "the mastery
    `MulDiv` (the missile's own mastery stat)", and the pseudocode's `[C]` header covers the `k` line untagged, while
    the `[I]` bullet gives the same reading at `[I]`. A mastery of 0 adds nothing, and nothing in skills/0002 § 6 says
    any of the 778 builds had a non-zero mastery on the missile, so the run does not separate the step: the `[I]` is
    the right strength. The spec is to be reconciled once `lane/rbd` (the reverser folding the pair swap and the
    missile-mastery reading into skills/0002 § 6) merges, taking its tags; if the finding leaves open whether a missile
    carries its owner's masteries, that becomes an `[L]`. The page already takes the weaker tag (fix 9), so it does not
    wait. Filed for the spec-writer
    ([backlog](../../backlog/archive/2026-10-27-architect-spec-writer-skills-missiles-f1-mastery-and-dispatch-i4-kick.md)).
  - **Ruling (b): Kick's wording.** The page may say what § O and § I say, at their tags: Kick's start function
    builds its hit from its row's values (a set result and hit class, `MinDam` as physical damage), read from the code;
    in 32 uses the caster's seed did not move at the start and the do added no draw, confirmed; the strength-and-
    dexterity damage is the skill-damage function's for a row flagged `Kick`, read from the code, and is not said to be
    what Kick's start hit carries. Two spec points go to the same entry: dispatch I4 gives ÷ 4 for both bounds where
    [Skills § `Kick`](../../tables/Skills.md) gives `GetPhysMax` ÷ 3 (`[I]`); and which damage Kick's start hit carries,
    to the reverser if skills/0003 § 5 does not settle it.
  - **Close.** All phases done (P0, P1.1–P1.3, P1b, P2 parts 1 and 2, P3, P4): status `done`, moved to `done/`, its
    links and the links to it rewritten (other plans, ADR-0020, the backlog entries, the table docs, the skills
    overview, the research map, the review-fixes files); plans README row and run order; research-map rows
    `skills/dispatch` and `skills/missiles` name the wiki page. Review request closed
    ([archive](../../backlog/archive/2026-10-27-spec-writer-architect-review-lane-s45p4-plan-0045-phase-4-wiki.md));
    review-fixes Seen lines (spec-writer 1, 3, 9). Ledger: the lane row filled (verdict, fixes 9: overclaim 5, misread
    2, omission 2; usage from the orchestrator), the review row added with its usage "—".
- **2026-10-27 — after the close: the P3 review's reverser entry, folded by `lane/rbd` and reviewed (architect,
  accept with fixes; the review is in the [plan 0038 log](../0038-inferred-claims-sweep.md#implementation-log)).**
  The [entry](../../backlog/archive/2026-10-27-architect-reverser-skills-0002-builddamage-pair-swap-and-unit.md)'s
  two points are in skills/0002 § 6: every bound and the mastery are read on the missile, and each bound is tested
  `> 0` before an inverted pair is swapped and the mastery applied, all `[I]` (objdump confirms `0x005A8914`–`0x005A8993`
  and the physical pair at `0x005A89C4`–`0x005A89FD`). `tools/skills.py` `bd` swaps (`test_bd_swap`); the re-check of
  both runs' 33 logs, re-run byte for byte at the review, gives 4 118 builds and 0 mismatches with no inverted pair,
  so the swap rests on the code alone. No logged `MH0` list holds a mastery stat (0 of 54 655), so whether a missile
  carries its owner's masteries is an `[L]` open question in the finding. Rulings: the mastery leaves F1's `[C]`
  bullet; `MISSILE_BuildDamage` and `MissileElemRoll` are C in `re/symbols.csv` on the drawn fields (rule 14),
  which moves no spec tag. The spec-writer entry for F1 is released with what to write
  ([entry](../../backlog/archive/2026-10-27-architect-spec-writer-skills-missiles-f1-mastery-and-dispatch-i4-kick.md)).
- **2026-10-27 — after the close: the F1 and I4 entry written by `lane/sf2` (spec-writer; logged in the
  [plan 0038 log](../0038-inferred-claims-sweep.md#implementation-log)).** Missiles F1's mastery left the `[C]`
  bullet, which now cites both runs' 4 118 builds; the mastery's carrier is an `[L]`. Dispatch I4 is restated per
  bound (the `Kick` minimum `÷ 4` `[C]`, the maximum `÷ 3` `[I]`); which damage Kick's start hit carries is an `[L]`,
  routed to the reverser ([entry](../../backlog/2026-10-27-spec-writer-reverser-kick-start-hit-damage.md)).
