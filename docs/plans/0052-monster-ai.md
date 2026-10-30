# 0052 — Monster AI: the AI tick, target and skill choice, and the path request it makes (ADR-0014 phase 5)

> **Status:** approved (owner, 2026-10-27; scoping answers in the [plans README](README.md) owner decisions: questions 1–7 as recommended, question 8 the whole AI table); paused after P1.1 (owner ruling, 2026-10-27); **unpaused 2026-10-30 (owner): P1.2 running** (`lane/r52b`, static); the path search plan and ADR-0022's plan being drafted (`lane/plans54`)
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
the seeds it touched) in the harness. The path search gets its own plan, drafted when the project unpauses (deferred at the P1.1 review: the AI's path types draw nothing, so it gates nothing here). The skill
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
    catalogue function, the mode's frames before 0050·P3, the path result) and the per-event log windows. *Folded in at
    the `lane/a52` review:* `MonAiEntryGet`'s two branches, with the word its three callers pass as `EDX`, who sets
    it, what `0x00623470` tests for 10–12, and the row count of the **second table at `0x0073D358`** (MonAI § The
    second table); the `+0`, `+4` and `+C` words of a row of either table; rows 0 and 1 (and the second table's rows
    0 and 1) as catalogue entries of this batch; whether any path gives a unit an AI other than its record's (row 143,
    the hirelings, revived and converted monsters).
  - **P1.2 onward, the catalogue:** the per-AI functions in the twelve batches of § The catalogue batches below (set at the P1.1 review from Phase 0's 13 and
    P1.1's 9–11, with the second table's rows),
    each AI's decision tree with its `aip` reads, its draws and its calls; **the summons batch** (PetType AIs, the
    necromancer and druid summons, H3's owner pair) and **the hirelings batch** (`MERCAI_PickSkill` and the four
    hireling classes' AIs) per § Scoping questions 4; the boss AIs in two batches (bosses-A, bosses-B; ruled at the P1.1 review);
    H5 and H6 answered where a batch reaches them. *Folded in at the `lane/a52` review:* the summons batch takes row 143
    (row 106's `+8` word, its own `+4`, no record) and the five summon records with a skill at `Sk lvl` 0
    (`bloodgolem`, `bonewall`, `chargeboltsentry`, `infernosentry`, `druidhawk`), and `shadowmaster`'s `aip8` = 279 in
    Normal only; the hirelings batch says which skill list the one AI row 61 uses (`roguehire` and `act2hire` also
    name MonStats skills); every batch reads the `aip` slots per record where its AI's records disagree (13 rows,
    MonStats § AI columns), and the batch holding 50 `Mephisto` and 146 `UberMephisto` reads `aidist`.
- **The P1.1 review** ruled the tier (18 AIs, Phase 2), the floors of Phase 2 (unchanged) and the boundary, and set
  the batches below. The path search plan is deferred to the unpause (implementation log, the P1.1 review entry).

#### The catalogue batches (P1.2 onward; set at the P1.1 review, owner question 8)

**Status: running from 2026-10-30** (owner, unpause): P1.2, the first batch, on `lane/r52b` (static); the later batches follow one per static lane at a time. (Paused after the P1.1 review, 2026-10-27, owner ruling.)
Every one of the 148 rows of `g_MonAiTable` and the 18 rows of `g_MonAiStateRows` (`0x0073D358`, ai/0001 § 3) is in
exactly one batch, P1.1 included. Rows are grouped by the think functions' address ranges and families (ai/0001
§ 13), cut at about 18 rows; *tier* marks the Phase 2 tier AIs a batch holds. The order is the run order: the
batches holding the tier come first, since Phase 2 waits for their review.

| # | Batch | Table rows | State rows | n | Tier AIs |
|---:|---|---|---|---:|---|
| — | P1.1 (done) | 0 `None`, 1 `Idle` | 0 (zero row), 1 | 2 + 2 | — |
| 1 | pool-A (acts I–II, `0x005EFB80`–`0x005F1DE0`) | 2–16, 142 `ClawViperEx` | — | 16 | 2, 6, 9, 13 |
| 2 | pool-B (acts II–III, `0x005F20A0`–`0x005F53E0`) | 17–30 | — | 14 | 20, 21, 22, 28, 29, 30 |
| 3 | pool-C (ranged, maggots, the Zakarum, nests) | 33, 35–40, 43, 45–49, 52, 56, 57, 63 | — | 17 | 35, 37 |
| 4 | pool-D (`SkeletonMage` to the traps) | 64–66, 68–80, 87, 92 | — | 18 | 64 |
| 5 | summons (PetType, necromancer, druid, assassin; H3's owner pair) | 67, 84, 86, 101–112, 143 | 7 | 16 + 1 | 67 |
| 6 | hirelings (`MERCAI_PickSkill` `0x005E4D30`) | 61 | 4, 5, 6 | 1 + 3 | 61 |
| 7 | bosses-A (Andariel to Izual, Blood Raven, Griswold, Uber Izual and Mephisto) | 34, 44, 50, 53, 55, 59, 90, 144, 146 | — | 9 | 34 |
| 8 | pool-E (towers, turrets, javelins and blowguns, Venom Lords, the siege) | 82, 83, 85, 89, 93–98, 113–115 | — | 13 | 89 |
| 9 | pool-F (act V minions, `0x005E1B60`–`0x005E36F0`) | 116–125 | 15 (`WhipChangeClass`), 16 (`ImpAttach`) | 10 + 2 | 125 |
| 10 | pool-G (act V rest, the Ancients, Baal's minions) | 126, 127, 129–134, 136, 137, 139, 141 | — | 12 | — |
| 11 | bosses-B (Diablo, Nihlathak, the Baal rows, Uber Diablo and Baal) | 51, 128, 135, 138, 140, 145, 147 | — | 7 | — |
| 12 | towns, NPCs and the state rows | 31, 32, 41, 42, 54, 58, 60, 62, 81, 88, 91, 99, 100 | 2, 3, 8–14, 17 | 13 + 10 | — |

- Sums: table rows 2 + 16 + 14 + 17 + 18 + 16 + 1 + 9 + 13 + 10 + 12 + 7 + 13 = 148; state rows 2 + 1 + 3 + 2 + 10
  = 18.
- Against Phase 0's 13 (MonAI § Batches): its `machinery` is P1.1; rest-1 … rest-9 are regrouped by code range; the
  bosses split in two (16 boss rows, many long functions, too many for one lane run); row 117 `SuicideMinion` moves
  from the summons to pool-F with state row 15, which `WhipChangeClass` (the `Overseer`'s whip, row 120) sets; state
  row 16 goes with `Imp` (122), whose `ImpAttach` sets it.
- Against P1.1's 9–11 (ai/0001 § 13): its B6 (34 rows) splits into pool-F, pool-G and bosses-B; Blood Raven (59)
  stays with the bosses, as MonAI places it; state rows 2, 3, 8–14 and 17, and the five unresolved register-passed
  `MonAiInit` sites (ai/0001 § 3), go to batch 12, which names their setters.
- Each batch carries the P1.2 items above that fall in its rows (row 143 and the `Sk lvl` 0 records to batch 5; the
  hireling skill list to batch 6; `aidist` with rows 50 and 146 to batch 7; per-record `aip` reads everywhere) and
  the catalogue's action helpers (`0x005DF850`, `0x005DF990`, `0x005DFA00`, `0x005DFBF0`) with the first batch whose
  AI calls each.
- P3b's entries follow this list: one per table row and one per state row.

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
  - 1 500 AI decisions over the **tier** (**18 AIs, ruled at the P1.1 review:** the 16 of ai/0001 § 13 plus 89 `Megademon` and
    125 `BloodLord`, so acts IV and V hold a tier AI; 836 of 1 753 pool slots; at first an estimate of 12 to 16 AIs
    that cover most pool rows of the five acts, one
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
- **P3b — catalogue:** `docs/specs/monsters/ai/catalogue.md`, one entry per AI row (question 8: the 148 rows of
  `g_MonAiTable` and the rows of the second table P1.1 names, stock-named or not) (its `aip` meanings, its decision
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
- **2026-10-27 — Phase 0 landed for review (archivist, `lane/a52`, from `main` fcce5b4d; no Ghidra, no harness).**
  New [MonAI](../tables/MonAI.md), the AI index of **every row of the AI table** (question 8): 148 rows, the `.bin`
  record its own index and MonStats `AI` its row index (`[C]`, 0 mismatches; layout `monai` added, `excel_layout`
  baseline regenerated, 74 tables), each row with its MonStats records, its `g_MonAiTable` row read from the pinned
  image (four words, `+8` the AI function `[I]` by items/0001, the others `[L]`) and its reach marks (pool,
  superunique, summon, hireling). **146 rows are named by a stock MonStats record, 2 by none** (0 `None`, 143
  `ShadowMasterNoInit`); 16 rows are reached by a summon (Skills `summon` with a `pettype`, or a PetType `mclass`), 1
  by the hirelings (61 `Hireable`, all four classes and `act5hire1`), 63 by a pool class, 44 by a superunique, and 60
  only through links the index does not mark (presets, minions, spawns). MonStats § AI columns (`AI`, `aidel`,
  `aidist`, `aip1..8`, the skill columns, `switchai`, `threat`), PetType § AI of the summons and Hireling § AI of the
  hirelings (the `DefaultChance`, `Chance_k`, `ChancePerLvl_k`, `Mode_k` values per kind) added and linked;
  `Aiparms.txt` read as a lead only (19 sections, 16 matched to an AI row). `tools/ai_survey.py` (`index`, `rows`,
  `hire`, `aiparms`, `md`, `batches`, `summary`), gate survey `ai` (new baseline), `tools/test_ai_survey.py` (8 tests).
  Meanings `[L]` except where anim/0001, items/0001, monsters/0004 and hirelings/0001 anchor them. The **batch
  proposal** (MonAI § Batches, by record count): 13 batches covering all 148 rows, machinery (rows 0–1 with P1.1),
  rest-1 … rest-9, bosses (16 AIs), summons (15, with row 143), hirelings (1, with `MERCAI_PickSkill`); the plan's
  estimate was eight to twelve. For P1, to fold into its *Done when* at the review:
  1. **P1.1:** the `+0`, `+4`, `+C` words of a table row (`+0` takes 0, 1, 2, 4, 5; `+4` set in 19 rows, `+C` in 11,
     some shared, MonAI § The AI table in the image); rows 0 and 1, whose `+8` words lie apart from the rest; whether
     any path gives a unit an AI other than its record's (row 143, hirelings, revived monsters).
  2. **Summons batch:** row 143 holds row 106's `+8` word with its own `+4` and no record; five summon records have a
     skill at `Sk lvl` 0, which the creation reader skips (`bloodgolem`, `bonewall`, `chargeboltsentry`,
     `infernosentry`, `druidhawk`); `shadowmaster` sets `aip8` = 279 (Shadow Master) in Normal only.
  3. **Hirelings batch:** one AI row for all hirelings; `roguehire` and `act2hire` also name MonStats skills
     (RogueMissile, Jab) beside their Hireling skills, and which list the AI uses is open.
  4. **Every catalogue batch:** in 13 AI rows the records disagree on which `aip` slots they set, so an entry reads per
     record; `aidist` is set only on `mephisto` and `ubermephisto` (0 / 40 / 46).
  Review request [to the architect](../backlog/archive/2026-10-27-archivist-architect-review-lane-a52-plan-0052-phase-0.md).
- **2026-10-27 — `lane/a52` review (architect): Phase 0 accepted with fixes (2: misread 1, omission 1).** Phase 0's
  *Done when* is met: every AI a stock row uses is listed once with its records, the meanings are `[L]` except where a
  finding anchors them, the survey matches its baseline, and the gate is green. Reran with `python3 -I`:
  `ai_survey.py summary` gives the `ai` baseline, `test_ai_survey.py` passes 8 of 8, and `ai_survey.py md` reproduces
  the index block. From the doc's index: 148 rows, each in exactly one of the 13 batches; the records sum to 734; the
  marks give P 63, U 44, S 16, H 1 and no mark 60. The `excel_layout` baseline changes only `tables` 73→74,
  `records`/`cells` +148 and the new `monai_cells=148 monai_bad=0`. Objdump against the pinned image (sha256 as in
  the inventory): rows 0–3, 110, 143–147 and the zero row at `0x0073D358` are as MonAI states; `MonAiEntryGet`'s
  `AI` < 148 test is at `0x005B1628`. Fixes:
  1. *misread* (MonAI § Row identity and § The AI table in the image, MonStats § AI columns). The lane wrote "the
     bound 148 is `MonAiEntryGet`'s, so no index past 147 reaches a row", but items/0001 gives that path only "with
     `EDX` = 0". With `EDX` ≠ 0 the function returns `0x0073D358 + 16·EDX`, and `0x0073D358` is the lane's "row
     after the last". Corrected: a MonStats `AI` out of range gives row 0, on that branch only.
  2. *omission* (MonAI § The second table, § Batches, § Open questions). The second table: rows 0–17 have the
     four-word shape. Seven of them reuse a first-table `+8` word (`Idle`, `Hireable` with its `+C`,
     `GoodNpcRanged`, `NecroPet`, `SuicideMinion`, and rows 10 and 17 share one), and ten hold functions no `monai`
     row has. These bytes are `[C]`, the branch is `[I]`, and the row count and the role are `[L]`, routed to P1.1.
  **Rulings.** (a) **The generated 148-row index is acceptable** under "describe, don't dump". It is a derived
  research index: a join of the name key to the records that use it, with aggregates and image addresses, the same
  shape as Skills § Function index. The only whole column of a game table it reproduces is the name list of a
  table that holds nothing else. It stays generated between its markers and gives no per-record values (`aip`
  values, skill levels, chances): those stay in the `rows` output. Hireling § AI of the hirelings, with four kind
  rows, is short and illustrative. (b) **Tags hold.** The image bytes are `[C]` as data. `+8` is the AI function
  `[I]` by items/0001. `+0`, `+4` and `+C` are `[L]` with no finding reading them, and appear in § The AI table in
  the image as leads and under Open questions. `Aiparms.txt` and the `*aip` comments are § Leads only. (c) **13
  batches are accepted** against the plan's estimate of eight to twelve. The estimate was labelled an estimate,
  question 8 adds the unnamed and the one-record rows, and P1.1 regroups by shared code. The second table's rows
  are not yet batched. (d) **Rows 0 and 143 are placed correctly.** Row 0 goes with P1.1: its `+8` word lies beside
  `Idle`'s, and the out-of-range fallback lands on it. Row 143 goes with the summons, since it holds row 106's `+8`
  word. Both get catalogue entries (P3b now reads "one entry per AI row"). (e) **Reading the image table stays in
  the archivist lane.** Reading a hash-pinned image at an address already in `re/symbols.csv` and printing the
  words as data is extraction (precedent: `tools/ds1.py` reads `g_Ds1ObjectIds`). Naming a word's meaning is the
  reverser's. The `tbl_*` keys stay. Once P1.1 names the second table, an archivist request adds it to the survey.
  (f) **The log's four items are folded** into P1.1's and P1.2's text above, with the second table. The architect's
  revision of the batches for question 8 stays due at the P1.1 review. (g) The lane relied on the commit hook. The
  review ran `python3 -I tools/gate.py` (green).
- **2026-10-27 — P1.1 checkpoint (reverser, static lane B, `lane/r52`; paused by the owner for a session reload).**
  Committed: [ai/0001](../findings/ai/0001-machinery.md) (§§ 1–13 drafted: the AI tick `sub_005B1740_MonAiEvent` =
  monster event kind 2, run by `MonEventsRun`'s slot pass in `GameRunUnitEvents` ← `GameTick` ←
  `sub_0052FC20_ServerGamesFrame` / `sub_005645E0_GameTickAlt`, plus nine direct calls from mode ends; the 30 kind-2
  queue sites; `g_MonAiTable` 148 × `{searchKind, init, think, alt}` and the **second table `g_MonAiStateRows`
  (0x0073D358, 18 state rows indexed by `AiCtl.state`, who sets each state)**, covered in § 3; `AiCtl`/`MonPathCtl`/
  `AiCtx`/`MonCmd` in `re/types/ai.h`; target search and the ten target lists at `Game+0x10F8`; the command and move
  helpers; the path request (AI types 1, 2, 5, 6, 7, 13, 15; the planner draws only for 10 and 16, unreached); draws;
  hireling and summon entries; H4/H5 AI side; the unit lists for ADR-0022; tier proposal, batch list, boundary
  recommendation and the log-volume estimate (capped breakpoints suffice)), [ai/experiments](../findings/ai/experiments.md)
  run:2026-10-27-ai-emu (1 314 emulated cases, 0 mismatches), 84 `re/symbols.csv` rows (all `I`),
  `tools/ai_machinery_scan.py`, `tools/ai_emu.py`, kept outputs `workspace/logs/r52/` (manifest 40 lines), the
  drlg/0009 § 11 correction (the nine "register" override calls). `main` merged at `db8162b3`.
  **Resume note — next:** (1) re-read § 3 against `docs/tables/MonAI.md` (now on `main`) and align the state-row
  wording with the archivist's table; check who passes `EDX` to `MonAiEntryGet` at 0x005B1663 (the event's row-kind
  switch) and 0x005B0E81 (MonAiInit's old-state lookup) and state it; (2) run the review-fixes checklist over ai/0001
  (counts recounted from the kept files, Functions-table tags); (3) the ledger row in `docs/plans/metrics.md`
  (usage "—"); (4) the review request to the architect (`python3 -I tools/backlog.py new --from reverser --to
  architect --slug "plan 0052 P1.1 review"`). No Ghidra needed for (1)–(4) except an optional re-check of 0x005B1663.
- **2026-10-27 — P1.1 review request (reverser, static lane B, `lane/r52`, resumed after the checkpoint).** The
  resume note's four items are done. `main` merged at `a2d31a99`; `python3 -I tools/gate.py` green (no error; the six
  E14 warnings are in items/ and rng/ findings this lane does not touch).
  - **Who passes `EDX` to `MonAiEntryGet`** ([ai/0001 § 3](../findings/ai/0001-machinery.md#3-the-ai-table-and-its-dispatch),
    `[I]`): three direct calls in two functions, no dword reference (`entryget-callers.txt`). 0x005B1663
    (`MonAiTargetByKind`) passes the stored `AiCtl.state` (`[[ctx+0x00]]`, 0x005B1655–0x005B165D), so the row kind
    comes from the state row when the state is non-zero; 0x005B0E81 (`MonAiInit`) the current state before the store;
    0x005B0EBE the new state. § 4's row-kind bullet and the Answer bullet carry it. `MonAiInit`'s `< 18` test is
    signed: a negative state would index below the state rows; no immediate caller passes one, five register callers
    stay unresolved.
  - **Review-fixes pass** (rules 1–15 over the lane's diff; corrections carried into each section that repeats them):
    rule 2 recounts from kept files: the setters of `AiCtl.state` were "7 calls pass a register" and are 21 immediate
    and 12 register calls (`aiinit-pushes.txt`, `aiinit-regstates.txt`), adding the curse path `CurseApplyCb` →
    0x005C34B0 (states 10, 12, 11 by `auratargetstate` 23, 27, 56; new row `sub_005C34B0_CurseSetAiState`, I) and the
    state-0 returns of five state-row functions and three other sites; the table rows with an `init`/`alt` were "21 / 14" and are 19 / 11
    (`ai-rows.txt`, as MonAI.md has them); the machinery RNG graph has 94 roots, not "92 and the tick"; the planner
    graph has 8 roots, not "the 17 entries" (the slots of types 3, 11, 12 are not roots and are written as unfollowed,
    rule 9; no AI path requests them); the tier share is 44.7 %, not 44.8 % (784 of 1 753); "66 cancel" now has its
    kept output (`aicancel-pushes.txt`). Rule 14: the five emulated maps' Functions-table tags read "I (map `[C]`, § 12)"
    to match `re/symbols.csv` (the emulation raises no row). Rule 7: two W1 lines anchored. Rules 5 and 3: no address or
    name of the lane's 85 `re/symbols.csv` rows collides with `main`'s after the merge.
  - **Kept outputs:** six new files under `workspace/logs/r52/` (`entryget-callers.txt`, `entryget-windows.txt`,
    `aiinit-pushes.txt`, `aiinit-windows.txt`, `aiinit-regstates.txt`, `aicancel-pushes.txt`), from
    `tools/sweep_rbs3.py` (`callers`, `window`, `pushes`); manifest 46 lines, `sha256sum -c` passes from that directory.
  - **Backlog:** [archivist](../backlog/archive/2026-10-27-reverser-archivist-monai-second-table-named-by-ai-0001.md) (link
    MonAI.md's second table and its open question to ai/0001 § 3; the survey reads the state rows, ruling (e));
    the [review request](../backlog/archive/2026-10-27-reverser-architect-plan-0052-p1-1-review.md).
  - **To rule on.** (1) The tier proposal (16 AIs, § 13). (2) The batch list for P1.2 onward (§ 13; the architect's
    revision for question 8 was due at this review). (3) The boundary (§ 13: the command at `MonSetMode`, the path
    plan exit, the catalogue's action helpers). (4) **The injected-logger ADR is not needed** (owner question 3 asked
    for it only if capped per-event breakpoints cannot keep the logs bounded). The case, from ai/0001 § 13: the AI
    runs once per AI event, not every frame (§§ 1–2: kind-2 events at `T + aidel`, 10–25 frames when idle, or a mode
    end), so one decision is 4–5 lines (9 at most: entry, search result, command, plan exit, exit seed), and the
    draws of the forced-target and state-146 tests fall inside the entry and exit seeds and need no line. About 15–60
    events a second near one player, uncapped 10 000–20 000 lines a minute; with ADR-0014's room filter and a cap of
    200 decisions per AI row and 3 000 per session, at most about 15 000 lines per session, the size of plan 0045's
    runs (13 335 missile-frame lines in one). The path planner draws nothing for the AI's types (§ 8), so no line
    inside the planner is needed. What would change the answer: a P2 case that needs every frame of every monster
    (that is ADR-0022's frame window, a separate question) or a think function that loops over many units with a draw
    each, which the catalogue would find. All of this is an estimate (`[I]`), from the static reading.
- **2026-10-27 — P1.1 review, the planning rulings (architect, `lane/r52`).** The finding itself passed its Tier B
  lane check (accept, 0 fixes, `6590e220`) and is not re-reviewed here; these are the four points the review request
  leaves to the architect.
  1. **Tier: amended to 18 AIs.** The 16 of ai/0001 § 13 meet each kind the Phase 2 text asks for (ranged
     `CorruptArcher`, `SkeletonBow`; casters `SkeletonMage`, `Vampire`; resurrecting `GreaterMummy`, `FallenShaman`,
     the leader with minions and Bishibosh's class, so also the superunique; `Andariel`; `NecroPet`; `Hireable`), but
     none of the twelve pool AIs is an act IV or act V one, and the plan asks for "the five acts". Added: 89
     `Megademon` (22 slots, 10 levels) and 125 `BloodLord` (30 slots, 15 levels), the act IV and act V pool AIs with
     the most slots in `ai-pool.txt` that the tier did not hold. 836 of 1 753 slots (47.7 %); reaching 50 % is not a
     goal. **Floors unchanged:** 1 500 decisions, at least 50 per tier AI (900 for 18 leaves room), the chaining and
     H1 floors as written.
  2. **Batches: twelve, written into § The catalogue batches** (all 148 table rows and all 18 state rows, each once).
     P1.1's grouping by code range is kept where it held 9–18 rows; its B6 (34 rows) is split, the bosses go into two
     batches, and row 117 and state rows 15 and 16 follow the AIs whose code sets those states. The tier batches run
     first. **P1.2 is next on unpause**, not ready to start: the project is paused after this roster (owner ruling).
     Estimate: P1 thirteen lane runs (P1.1 and twelve batches), the top of the plan's nine to thirteen.
  3. **Boundary: accepted as recommended, with two conditions.** The decision's claim ends at (a) `MonSetMode`'s entry
     from an AI site (the command block is the output; the mode's frames are phase (4)'s) and the skill start behind
     `MonAiUseSkill` (skills/dispatch, plan 0046's oracles); (b) `PathPlan`'s exit; (c) the action helpers' calls of
     `COMBAT_ApplyDamage`, `MissileCreate` and the spawn functions. *Conditions:* the harness logs the unit seed at
     entry and exit of each of the three, so the think function's own draws are separated from the mode start's
     (anim/0001 § 11) and from the skill start's; and § 8's prediction that the plan leaves the seed unchanged for the
     AI's types is **checked**, not assumed: any changed seed at a plan exit is a mismatch, routed to the path search
     plan. The helpers' own code up to those calls is the catalogue's (it is read, not oracled). In emulation the same
     three are ADR-0021 boundaries. The path search plan is **deferred to the unpause**: it gates nothing here.
  4. **Injected-logger ADR: not needed (accepted).** The case is an `[I]` estimate from static reading, and it holds
     on what the reading shows: one decision per AI event, 4–9 lines, capped at 200 decisions per AI row and 3 000
     per session, about 15 000 lines, the size of plan 0045's runs. The question **reopens**, with the architect
     drafting the ADR for the owner, if any one of these happens: (a) P2's first session logs more than twice the
     estimate (30 000 lines) under the caps, or the breakpoints move the frame timing the run checks (a mismatch traced
     to the logger); (b) a catalogue batch finds a think function that loops over many units with a draw or a logged
     input each, so one decision needs lines per unit; (c) a plan exit shows the unit seed changed for an AI path type,
     so lines inside the planner are needed; (d) the caps leave a tier AI under its 50 decisions over the planned
     sessions; (e) a P2 case needs every frame of every monster, which is ADR-0022's frame window and is ruled in that
     plan, not here. P2's record states the measured lines per session against the estimate.
  **Index:** the plans README row and the architect and static-lane run-order rows changed only where these rulings
  change them (the batch count, the path search plan and ADR-0022's plan deferred to the unpause). Review request
  closed.
- **2026-10-30 — Unpaused (owner; architect, `lane/unp`).** [Plans README](README.md) § Owner decisions (2026-10-30).
  **P1.2 runs** (`lane/r52b`, static lane, the first catalogue batch of § The catalogue batches); the later batches
  follow in their order, one per static lane at a time. The path search plan and ADR-0022's plan are drafted now
  (`lane/plans54`, architect). P2's gate is unchanged (0050·P3's review passed; its own P1.1 and tier reviews).
- **2026-10-30 — P1.2 catalogue batch 1 (pool-A) for review (reverser, static, `lane/r52b`, from `main` 8b33ab84).**
  [ai/0002](../findings/ai/0002-pool-a.md): the sixteen think functions of rows 2–16 and 142 and row 15's `alt`, each
  with its `aip` reads per record, its `AiCtl+0x14/+0x18/+0x1C` words, its draws in order (all on the acting unit's
  seed; 0–6 per decision) and its command, plus the helpers first read here (`MonAiMoveToUnitDist`,
  `MonAiRunToUnitStop`, the `AiCtl+0x20` parameter list, `UnitDistSq`, the room's ring of the last four dead monsters
  that row 6 scans). [C] by emulation (run:2026-10-30-ai-cat-emu-1, `tools/ai_cat_emu.py`, 2 400 cases, 0 mismatches,
  every control failing every case it separates; a development run kept under `emu/dev/`): the decision maps of rows 2,
  3, 4, 5, 7, 9, 12, 14, 16 and 142 up to their first callee. [I]: rows 6 `Fallen`, 8, 10, 11, 13 `FallenShaman` and
  15 (a callee with an undeclarable read set before the first draw), and everything after a boundary. Tier AIs in the
  batch: 2 and 9 emulated, 6 and 13 static only. P1.1 review reopen condition (b) not met: the three unit walks (rows
  6, 8, 13) draw nothing per unit. 30 `re/symbols.csv` rows (all I); `re/types/ai.h` `AiParam`, `re/types/lifecycle.h`
  `DungeonRoomLife+0x14/+0x38`. Kept outputs `workspace/logs/r52b/` (manifest 8 lines; `emu/` 31, `emu/dev/` 31; each
  passes from its directory). Backlog: the [review request](../backlog/archive/2026-10-30-reverser-architect-plan-0052-p1-2-batch-1-review.md),
  [archivist](../backlog/archive/2026-10-30-reverser-archivist-monstats-aip-and-levels-id-readers-named-by.md) (MonStats and
  Levels readers). Next: batch 2 (pool-B, rows 17–30).
- **2026-10-30 — P1.2 catalogue batch 2 (pool-B) for review (reverser, static, `lane/r52c`, from `main` 9edf83d8).**
  [ai/0003](../findings/ai/0003-pool-b.md): the fourteen think functions of rows 17–30 and row 29's `alt`, each with its
  `aip` reads per record, its `AiCtl+0x14/+0x18/+0x1C` words, its draws in order (all on the acting unit's seed; 0–6 per
  decision) and its command, plus the helpers first read here (four search callbacks, the vulture's take-off and
  landing, `MonAiMoveToPoint` and its no-stop twin, `AiCtlSetVar`, `AlignSame02`). [C] by emulation
  (run:2026-10-30-ai-cat-emu-2, `tools/ai_cat_emu2.py`, 2 400 cases, 0 mismatches, every control failing every case it
  separates; a development run kept under `emu/dev-1/` with its tool copy): the decision maps of rows 17, 18, 19, 20,
  21, 22, 24 and 27 up to their first callee, `AiCtl+0x14/+0x18` and the unit-search blocks included; row 30's record
  test and row 29's `alt` (no draw before their boundaries). [I]: rows 23, 25, 26, 28, 29's think and 30 past its record
  test (`UnitDistSq`/`UnitGetRoom`, `UnitLifePct` or `MonAiFindHostile` before the first draw), and everything after a
  boundary. Tier AIs in the batch: 20, 21, 22 emulated, 28, 29, 30 static only (30's record test emulated). P1.1 review
  reopen condition (b) not met: the four search callbacks draw nothing, row 25's loop over the wisps it found draws
  nothing per wisp. No call of the action helpers (`0x005DF850`, `0x005DF990`, `0x005DFA00`, `0x005DFBF0`) in the batch
  (`grep -c 'call   0x5df850\|call   0x5df990\|call   0x5dfa00\|call   0x5dfbf0' b2-asm.txt`: 0). 25 `re/symbols.csv` rows (all I). Kept outputs `workspace/logs/r52c/` (manifest 7 lines; `emu/` 31,
  `emu/dev-1/` 32; each passes from its directory). Backlog: the
  [review request](../backlog/archive/2026-10-30-reverser-architect-plan-0052-p1-2-batch-2-review.md),
  [archivist](../backlog/2026-10-30-reverser-archivist-monstats-and-itemstatcost-readers-named-by-ai-0003.md)
  (MonStats, ItemStatCost and States readers). Next: batch 3 (pool-C).
- **2026-10-30 — P1.2 batch 2 Tier B check (architect, `lane/r52c`): accept with fixes (1).** Fix: omission, the search callbacks' "draw nothing" gains its scope (direct calls of `AiSameBaseNearCb`, callees not followed). Rulings: the five unemulated rows stay `[I]` for the batch's done-when (as batch 1); P1.1 reopen condition (b) not met; the three open questions stand (the dance tables and the opposite-word parameter record to the writer read, the stat 80 grant to Phase 2). Gate green. Review request closed.
- **2026-10-30 — `lane/a7b` Tier A audit (architect; ADR-0023 audit sample, plan 0053 Phase 3) of the Tier B check
  (44a12049, accept, 0 fixes): accept with fixes (5).** `main` (66b96ae8) merged into the lane first (one ledger
  conflict, both sides kept in merge order). The full review re-ran `tools/ai_survey.py states` on the pinned image:
  every byte count in MonAI § The second table holds (`+0` 7/10/1, `+4` in 3, 11, 16, `+C` in 4, `+8` 17 set and 16
  distinct, five words shared with `g_MonAiTable`, twelve not); the lane's "five, not seven" is right. Anchors read
  with objdump: `cmp ebx,0x12; jge` at 0x005B0E4D, `edx = [[esi]]` before the call at 0x005B1663, the two curse calls
  0x005C3520/0x005C352E and 0x005E817B. The 49 `RECIPE_BASES` rows were matched by script against
  `2026-10-27-anim-p2-manifest-ckpt2.sha256` (49 of its 52 saves, 49 distinct hashes, 0 mismatches; the other three,
  `AnimSorMon`, `sp/AnimAssBos`, `sp/AnimPalChg`, equal existing rows) and `tools/test_d2s.py` passes (60 tests): that
  part is clean. Fixes, all in `docs/tables/MonAI.md`:
  - Omission 1 (archivist rule 6): the register-site list named 10 of the 12 sites; added state 11's function
    0x005E817B (`eax` = 0) and the curse path's twin 0x005C352E, with the sites' addresses and the two pointer loads
    that pass the current state. The Tier B check saw the first as a nit and left it.
  - Stale cross-reference 3 (archivist rule 4, outside the diff, in the same doc): § The AI table in the image still said
    only `+8` has a meaning from a finding while the lane's new text uses `+0` as the row kind (ai/0001 § 3 names all
    four, `[I]`); § Batches still said the state rows are in no batch and P1.1 adds them (this plan's § The catalogue
    batches places all 18); the first and third *Open questions* still asked what `+0`/`+4`/`+C` are and whether any
    path overrides the record's row, which ai/0001 § 3 answers in part (narrowed to row 143 and to a first-table row
    other than the record's).
  - Omission 1 (routing): the lane found ai/0001 § 3's "seven state rows reuse a first-table think word" overcounts
    (states 10 and 17 share a word with each other only) and wrote around it with no entry to the finding's owner;
    filed [reverser](../backlog/2026-10-30-architect-reverser-ai-0001-state-rows-reusing-a-first-table.md).
  **What the Tier B check missed:** all five, none reject-grade (no `[C]` without its source, no wrong address). The
  misses are of one kind: text outside the diff that the diff makes stale, and a disagreement with a finding left
  unrouted; a diff-scoped check reads neither unless rule 4's "re-read the findings a column touches" is run over the
  whole doc. Gate GREEN after the fixes.
