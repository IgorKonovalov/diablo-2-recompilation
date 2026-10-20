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
  - **tier A**, the skills Phase 2 reproduces, fixed at this phase's review from the survey: the general rows
    (Attack, Kick, Throw, Left Hand Throw, Left Hand Swing); per class at least two skills the pilot can cast
    (self-centred, directional, melee or summon; for example Nova, Frost Nova, Static Field, Teleport, Fire Bolt;
    Bash, Howl; Jab, Multiple Shot; Raise Skeleton, Bone Armor; the Paladin's Holy Fire and Holy Shield; a Druid and
    an Assassin pair); every function family with ten or more stock rows represented once; the monster skills of the
    combat logs' attackers;
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
