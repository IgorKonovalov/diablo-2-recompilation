# 0052 — Monster AI: the AI tick, target and skill choice, and the path request it makes (ADR-0014 phase 5)

> **Status:** approved (owner, 2026-10-27; scoping answers in the [plans README](README.md) owner decisions: questions 1–7 as recommended, question 8 the whole AI table)
> **Created:** 2026-10-25
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0011-harness-slots, 0013-forced-path-runs-cell-level, 0014-scope-game-simulation, 0015-emulated-reproduction, 0016-pipelined-simulation-phases, 0020-skills-phase-in-two-plans, 0021-observed-boundaries-in-emulation

## TL;DR

**Question:** on each frame a monster (or a summon, or a hireling) is active, what does its AI do: when does it
think, which target does it pick, which mode or skill does it choose, which path request does it make, and which draws
does it make on which seed? This is phase (5) of [ADR-0014](../adrs/0014-scope-game-simulation.md), the last one,
after animation and frame timing (phase (4), plan [0050](0050-animation-frame-timing.md)). When it is done:
- `docs/tables/MonAI.md` (the AI index) and the gate survey `ai` list every AI a stock row uses;
- `docs/findings/ai/` names the AI tick, the shared machinery and every AI function a stock row reaches, each with
  its draws per seed;
- `tools/ai.py` reproduces AI decisions per event, and the **331 monster gaps** that plan 0045's runs left between two
  skill events of a monster (171 in run:2026-10-25-skills, 160 in run:2026-10-27-skills) are walked again with the AI's
  draws modelled;
- `docs/specs/monsters/ai/` (research-map row `monsters/ai`) is reviewed in two parts: the machinery and the tier
  (P3a), then the catalogue entries (P3b).

**Boundary (recommended, § Scoping questions 1).** The AI's **path request** (its kind, its target, its flags) is this
plan's; the path search behind it is a **boundary**: an observed boundary under
[ADR-0021](../adrs/0021-observed-boundaries-in-emulation.md) in emulation, a logged ADR-0004 oracle (its exit state and
the seeds it touched) in the harness. The path search gets its own plan, drafted at this plan's P1.1 review. The skill
use the AI commands is [skills/dispatch](../specs/skills/dispatch.md)'s (reviewed); the mode's frames are phase (4)'s
(plan 0050, reviewed before this plan's harness phase); the per-skill functions plan 0046 has not specified are
boundary oracles under ADR-0004 (ADR-0020).

## Context

- **The gate.** ADR-0020 lets phase (5)'s plan follow plan 0045's reviewed spec. The `lane/s45p3` review accepted it on
  2026-10-27 (`skills/README`, `skills/dispatch`, `skills/missiles` reviewed), so this plan is **approvable now**, by the
  owner (the reading was confirmed by the owner on 2026-10-25). Its **harness phase (P2) starts only once phase (4)'s spec
  (0050·P3) is reviewed** (ADR-0016), since the AI's mode choices are timed by phase (4)'s model. Plan 0046 never gates
  it (ADR-0020).
- **Size.** MonStats `AI` takes 146 distinct values ([MonStats](../tables/MonStats.md), `+0x01E`, the `monai:AI` index);
  `g_MonAiTable` (`0x0073CA18`) holds 148 rows of 16 bytes, the AI function at slot `+8`, reached through
  `sub_005B15D0_MonAiEntryGet` ([items/0001](../findings/items/0001-tc-resolution.md)). Each AI reads `aip1..8` per
  difficulty and `aidel`, `aidist` (MonStats `+0x04F`–`+0x056`). Hirelings have their own skill choice
  (`MERCAI_PickSkill` `0x005E4D30`, out of [hirelings](../specs/hirelings/README.md)' scope); summons use the PetType
  rows ([PetType](../tables/PetType.md)). This is a catalogue as long as plan 0046's, plus the machinery.
- **Code already named** (`re/symbols.csv`, all `I`): `sub_005DDFC0_MonAiSetMode`, `sub_005DEAD0_MonAiUseSkill`,
  `sub_005DE190_MonAiPathOverride`, `sub_005A6260_AiPathOverrideSet`, `sub_005A6290_MonPathPlanType`,
  `sub_005DD220_AiCtlFlagTest`, `sub_005DD250_AiCtlTeleportFlagSet`, `sub_005F72D0_AiZakarumPriest`, the inactive save and
  restore `sub_00541FE0_InactiveMonAiSave` / `sub_00541E20_InactiveMonAiRestore` ([drlg/lifecycle](../specs/drlg/lifecycle.md));
  the path entry points the boundary will sit on: `sub_00649970_PathPlan`, `sub_006492F0_PathPlanToUnit`,
  `sub_00649760_PathPlanStraight`, `sub_00554850_SUnitPathCreate`, `PATH_DynamicCreate`, `sub_006505E0_PathFollowUnit`,
  `sub_00650840_PathStep`; the speed and step plan 0050 reads (`sub_00648690_PathSetSpeed`,
  `sub_006502D0_PathVelocityStep`).
- **Handed over by plans 0045, 0046 and 0050** (each an item of P1 or P2 below):
  - **H1. The monster gaps.** Between two skill events of one monster, its seed lay 1 to 33 steps further on in 331
    gaps of plan 0045's runs; of part 1's 171, 146 hold `MonAttackStats` calls that leave the seed unchanged, so the
    steps lie elsewhere, the AI's among the candidates ([skills/dispatch § P1](../specs/skills/dispatch.md#p-draws-and-seeds-per-event-kind),
    [skills/0001 § 17–18](../findings/skills/0001-dispatch.md#18-plan-0045-phase-2-part-2-the-run-run2026-10-27-skills)).
    The kept logs and their gap lists are this plan's first test set.
  - **H2. The AI's command as the input of skills/dispatch M1.** `MonAiUseSkill` (mode < 16) sets the used skill,
    `Unit+0xC4 |= 0x40` and the mode; which skill, which target and when is this plan's
    ([skills/dispatch § M](../specs/skills/dispatch.md#m-monster-skill-use)); a monster's bit 6 is set by its AI, so its
    do runs only through the attack-frame handler and the mode-14 case (dispatch's *Reimplementation notes*).
  - **H3. The summon's owner skill damage.** `sub_0056E050_MonOwnerSkillDamage` adds the owner's `SkillDamage` skill
    terms to a summon's attack stats; which unit's level it reads is register-passed and unresolved, and the 2 218
    `MonAttackStats` calls of the Raven class (419) are not modelled by plan 0045's checker (dispatch § M2). It is read
    in the summons batch and checked on the kept logs.
  - **H4. What ends an every-frame monster mode** (anim/0001 *Open questions*: the ignored return 2 of `*mv` attack and
    skill modes, and the generic S3, row 10, whose frame function nothing scheduled runs). Per the plan 0050 P1.1
    review ruling (b) it stays anim/0001's for 0050·P2 to log, and **comes to this plan only if those logs show the
    AI command ends the mode**. P1.1 reads the AI's side statically either way (cheap: it is `MonAiSetMode`'s path);
    the ownership is ruled at the 0050·P2 review.
  - **H5. drlg/lifecycle's AI questions:** the town-follow case (whether a hostile pool monster's path can enter a
    town room, the `MonAiPathOverride` calls not followed) and the teleport targets (the unique mod's
    `UModTeleportTry` `0x005B11F0`, the Zakarum priests through `0x005FD470`) ([drlg/lifecycle *Open questions*](../specs/drlg/lifecycle.md#open-questions)).
  - **H6. Which monster uses which skill, and when** (plan 0046 *Open questions*; skills/0001 § 13 and skills/0003
    § 14 take it as an input); `TgtPlaceCheck`, which plan 0045 named a monster AI test (skills/0003 § 12).
- **Research map row:** `monsters/ai` (Simulation band), added with the first draft. Wiki owner: Phase 4.

## Phases

Data first, then code, then spec. Phase numbers follow plans 0045 and 0050.

### Phase 0 — The AI index and the AI columns
- **Owner skill:** archivist
- **What:** how MonStats `AI` becomes the table index (the `monai` name list: where it lives, its order, the two rows
  of `g_MonAiTable` no stock row names); per AI, the MonStats rows that use it with `aip1..8` per difficulty, `aidel`,
  `aidist` and the skill columns (`Skill1..8`, `Sk1mode..Sk8mode`, `Sk1lvl..Sk8lvl`); PetType's AI-relevant columns for
  the summons; Hireling's skill-choice columns (`DefaultChance`, `Chance_k`, `ChancePerLvl_k`, `Mode_k`); the not-loaded
  `Aiparms.txt` read as a lead for parameter names only (data/excel B1: no loader).
- **Outputs:** `docs/tables/MonAI.md`; MonStats, PetType and Hireling docs linked; `tools/ai_survey.py` (gate survey
  `ai`); the batch table for Phase 1 (AIs grouped by shared code once P1.1 names it, by stock row count until then).
- **Done when:** every AI a stock row uses is listed once with its rows; the survey matches; meanings `[L]` until
  anchored; the gate is green.

### Phase 1 — The AI machinery, then the AI catalogue
- **Owner skill:** reverser (static; at most one Ghidra per batch, batches one at a time per lane, two lanes at most)
- **What and done when:** each batch names its functions with addresses, `[I]` or better, its draws listed per seed,
  and emulates (ADR-0015, ADR-0021) every pure decision it can declare a memory image for.
  - **P1.1 the machinery:** the AI tick (who calls the AI function, per frame or by `aidel`, and the per-unit order the
    caller takes), the AI state on the unit and its save and restore (lifecycle's pair), target search (range,
    `aidist`, the filters, `TgtPlaceCheck`), `MonAiSetMode` and `MonAiUseSkill` (H2), the path request: its kinds
    (`MonPathPlanType`, the override pair), its arguments and the call site of each planner entry, and **whether the
    planner draws, on which seed** (if it does, the harness oracle must log its exit seed); leader and minion following;
    the draws of each and their seeds; H4's AI side; the **tier proposal** for Phase 2 (below) and the batch list for
    P1.2 onward from Phase 0's table; **the boundary recommendation** (what the AI takes as oracles: the skill's
    catalogue function, the mode's frames before 0050·P3, the path result) and the per-event log windows.
  - **P1.2 onward, the catalogue:** the per-AI functions in batches from P1.1's list (an estimate: eight to twelve),
    each AI's decision tree with its `aip` reads, its draws and its calls; **the summons batch** (PetType AIs, the
    necromancer and druid summons, H3's owner pair) and **the hirelings batch** (`MERCAI_PickSkill` and the four
    hireling classes' AIs) per § Scoping questions 4; the boss AIs (the act bosses and Baal's minions) in one batch;
    H5 and H6 answered where a batch reaches them.
- **The P1.1 review** rules the tier, the floors of Phase 2 and the boundary, and the architect then drafts the path
  search plan (§ Scoping questions 1) from P1.1's path request kinds.

### Phase 1b — Community cross-check
- **Owner skill:** reverser (no Ghidra)
- **What:** register boss and monster behaviour descriptions (the leads policy, ADR-0007) and compare them blind with
  P1's readings; a verdict per compared claim.
- **Done when:** each compared claim has a verdict; every `contradicted` claim reachable on stock data is a required
  case of Phase 2; agreement promotes nothing. May run beside any P1 batch; lands before Phase 2's last session batch.

### Phase 2 — Per-event reproduction
- **Owner skill:** reverser (harness; **one slot** from 1–2, given in the prompt; a second only when no plan 0038 batch
  or 0046·P2 session needs it)
- **Starts when:** 0050·P3 is reviewed (ADR-0016), and P1.1 and the batches holding the tier are reviewed.
- **What:** `tools/ai.py` (model and `check`), `tools/gdb/ai.gdb` and its handler. One event is one AI decision: the
  AI function's call for one unit (inputs: the unit, its AI state, its `aip` row, the targets the search reads, the
  frame; outputs: the mode or skill commanded, the target, the path request; the draws; entry and exit seeds). The
  breakpoints filter to monsters within the logged character's rooms and cap each kind, as ADR-0014 § Log volume.
- **Done when** (minimums are estimates, confirmed at the P1.1 review): `run:YYYY-MM-DD-ai` reproduces with
  **0 mismatches** over
  - 1 500 AI decisions over the **tier** (an estimate: 12 to 16 AIs that cover most pool rows of the five acts, one
    leader with minions, one ranged and one caster AI, one resurrecting AI, a superunique and an act boss, one summon
    and one hireling), at least 50 per tier AI;
  - **chaining (ADR-0014):** for every decision kind that draws, at least 20 chained pairs on one seed (an AI decision
    followed by the same unit's next decision or skill start with nothing between), and the chain **AI decision →
    `SKILLS_SrvStart`** on one monster seed at least 20 times; a kind with none keeps its draw-order claims at `[I]`;
  - **the oracle replacement (H1):** the 331 monster gaps of run:2026-10-25-skills and run:2026-10-27-skills walked
    again with the AI's draws modelled where the logs hold its inputs; the record names how many close and why the
    rest do not (the logs held no AI line);
  - H3's 2 218 Raven `MonAttackStats` calls modelled with the owner pair, from the kept logs;
  - a catalogue sample: one AI per P1 batch outside the tier, at least 20 decisions each, where the pilot can stage
    it; the rest stay at their batch's emulated `[C]` or `[I]`;
  - the Phase 1b cases, and H4 and H5's cases if the reviews moved them here.

  Rare-branch minimums may fall short, named in the record with their counts; their claims stay `[I]`.

### Phase 3 — Spec: monster AI, in two parts
- **Owner skill:** spec-writer
- **P3a — machinery and tier:** `docs/specs/monsters/ai/README.md` (overview, the tick, the AI state, the event
  kinds and their seeds) and `machinery.md` (target search, the command, the path request, following), with each tier
  AI's entry; skills/dispatch § M, monsters/spawn and stats, drlg/lifecycle and hirelings updated where the AI was an
  input. **Its review is phase (5)'s reviewed spec** for any later gate (§ Scoping questions 7).
- **P3b — catalogue:** `docs/specs/monsters/ai/catalogue.md`, one entry per stock AI (its `aip` meanings, its decision
  tree, its draws), the tier entries linked, not repeated.
- **Done when (each part):** the spec follows the template; every statement tagged; the tick and each tier AI's
  decision as pseudocode with its draw order; the architect's review passes. Specs edited by two plans merge one at a
  time, the earlier plan's first.

### Phase 4 — Wiki page: monster AI
- **Owner skill:** spec-writer
- **What:** `docs/wiki/monster-ai.md` (ADR-0012) over the reviewed spec, after P3b; the monsters and skills pages
  cross-linked.
- **Done when:** `based_on` dates current (gate W4); no claim of its own; the architect's review passes.

## Scoping questions for the owner

The owner answers these with the approval. Each carries the architect's recommendation; the phases above are drafted
on the recommendations, and an answer that differs changes the phase it names.

1. **Pathing: its own plan?** *Recommendation: yes, as the owner leans.* This plan stops at the path request; the
   search (its kinds, its cost, its draws, its use of the collision grid) gets its own plan, drafted at the P1.1
   review once the request kinds are named. It sits beside [drlg/collision](../specs/drlg/collision.md) (reviewed), is
   a pure function of the grid and the endpoints, and is a good emulation target; its static phases fill the static
   lanes while this plan's P2 waits on 0050·P3. No ADR is needed: ADR-0014 puts pathing in this phase, and the gate a
   second plan would touch is the one ADR-0022 (proposed) sets for itself (question 7). *If no:* P1 gains a pathing
   batch after P1.1 and P2 a movement-window kind; the estimate grows by about a third.
2. **One plan or two for the AI?** *Recommendation: one plan, with the spec in two parts.* Unlike phase (3), nothing
   waits on the AI catalogue: a later scope needs the machinery and the AIs a scene holds, which P3a gives. So no
   ADR-0020-style split; the catalogue is batches of P1 and the entries of P3b. *If two:* the architect drafts an ADR
   amending ADR-0014 for phase (5), as ADR-0020 did for phase (3).
3. **The injected logger.** *Recommendation: let the architect draft its ADR at the P1.1 review only if the boundary
   recommendation shows that capped per-event breakpoints cannot keep the logs bounded* (the AI runs every few frames
   on every active monster). It is ADR-0014's reserve and needs the owner's acceptance; the ADR-0022 proposal may need
   the same tool for frame windows, so one ADR would serve both.
4. **Hirelings and summons.** *Recommendation: in this plan,* as two P1 batches and one tier entry each. Plan 0045's
   logs already hold 219 summons and the Raven class's 2 218 attack-stat calls (H3), and the hirelings spec leaves
   `MERCAI_PickSkill` out; a follow-up plan would re-read the same machinery.
5. **Harness slots.** *Recommendation: one slot* (lane H2, after 0050·P2), a second only when no plan 0038 batch or
   0046·P2 session needs it. No two-client case is required; party and hostile branches stay `[I]` from the code.
6. **The gate's reading.** *Confirmed (owner, 2026-10-25):* approvable at the review of 0045's spec (ADR-0020); the
   harness after 0050·P3's review (ADR-0016). Added in this draft: P2 also waits for P1.1 and the tier batches to be
   reviewed.
7. **What follows this plan.** *Recommendation:* [ADR-0022](../adrs/0022-scope-server-frame.md) (proposed), the server
   frame composed: its plan's tables and static reading start once this plan's P1.1 is reviewed, its harness once P3a
   is reviewed. The owner decides it before this plan's P2 starts (plans README, *Planning after 0052*).
8. **Catalogue coverage.** *Recommendation:* every AI a stock MonStats, PetType or Hireling row reaches gets a
   catalogue entry; an AI table row no stock row names is listed with its address and read only if it shares code with
   a stock AI (as plan 0046 did for unreferenced functions).

## Resources and limits

- **Harness:** at most **two harness lanes** at once across all plans, on **slots 1 and 2** (slot 0 is the owner's).
  Phase 2 takes one (question 5).
- **Static:** at most **two static lanes** and at most **two headless Ghidra** at once, `-Xmx3G` each. P1 holds one
  Ghidra per batch; P0 and P1b need none. While plan 0050·P1.3 holds static lane A, P1.1 runs in lane B.
- **Replays:** the re-walk of the 331 gaps and any heavy replay run under `systemd-run --user --scope -p MemoryMax=4G`.
- **Rotation:** lanes past about 4 h checkpoint, write a resume note and stop; a fresh lane resumes on the same branch.
- **Estimate** (an estimate, not a measured figure): P0 one lane run; P1 nine to thirteen lane runs (P1.1 and the
  catalogue batches); P1b one; P2 two to three lane runs of 10–20 sessions; P3 two; P4 one. Larger than plan 0046
  without pathing; the pathing plan comes on top.

## Open questions

- **Per-unit order within a frame.** The order in which the tick visits units decides which unit's draws come first on
  a shared seed (the game seed of a summon or a drop). P1.1 names the caller and its loop; a model of the whole frame
  is beyond this plan (ADR-0022, proposed).
- **The planner's draws.** If the path search draws on the unit seed, the gaps of H1 cannot all close before the path
  search plan models it; P2 then counts the gaps whose only unmodelled span is a planner call.
- The town-follow case (H5) may stay a named shortfall: whether a stock town's geometry admits such a route is the
  path search plan's.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-25 — First draft (architect, `lane/plans50`).** Status `proposed`, held until 0045·P3 is reviewed;
  scoping questions for the owner listed.
- **2026-10-25 — Owner ruling (via the orchestrator).** The gate's reading confirmed (approvable at 0045·P3's review,
  ADR-0020); status stays `proposed` until then; the scoping questions stay open until the re-draft, with the owner
  leaning towards pathing as its own part; movement speed stays in plan 0050.
- **2026-10-27 — Re-drafted at its gate (architect, `lane/plans52`).** 0045·P3 accepted with fixes (`lane/s45p3`), so
  the plan is approvable. Re-drafted on the architect's recommendations: the path request is this plan's and the path
  search a boundary with its own plan, drafted at the P1.1 review; one plan, the spec in two parts (P3a's review is
  phase (5)'s reviewed spec); hirelings and summons in; one slot. Folded in what plans 0045, 0046 and 0050 handed over
  (H1–H6): the 331 monster gaps as Phase 2's oracle replacement, `MonAiUseSkill` as dispatch M1's input, the Raven
  owner pair, anim/0001's ignored return 2 and generic S3 (conditional, per the plan 0050 P1.1 ruling (b)), lifecycle's
  town-follow and teleport targets. P2 keeps its gate on 0050·P3's review (ADR-0016) and adds its own P1.1 and tier
  reviews. Eight scoping questions for the owner, the seventh on ADR-0022 (proposed), what follows. Status stays
  `proposed`: the owner approves.
- 2026-10-27 — **Approved by the owner.** Questions 1–7 answered as recommended; ADR-0022 accepted. Question 8 differs: the catalogue covers **the whole AI table**, every row whether or not a stock MonStats, PetType or Hireling row names it. The architect revises P1's catalogue batches and P3b to match, at the latest at the P1.1 review. P0 and P1.1 may start.
