# 0052 — Monster AI: the AI tick, target and skill choice, and the path request it makes (ADR-0014 phase 5)

> **Status:** approved (owner, 2026-10-27; scoping answers in the [plans README](README.md) owner decisions: questions 1–7 as recommended, question 8 the whole AI table); paused after P1.1 (owner ruling, 2026-10-27); **unpaused 2026-10-30 (owner): P1.2 running** (`lane/r52b`, static); the path search plan and ADR-0022's plan being drafted (`lane/plans54`)
> **Created:** 2026-10-25
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0011-harness-slots, 0013-forced-path-runs-cell-level, 0014-scope-game-simulation, 0015-emulated-reproduction, 0016-pipelined-simulation-phases, 0020-skills-phase-in-two-plans, 0021-observed-boundaries-in-emulation

## TL;DR

**Question:** on each frame a monster (or a summon, or a hireling) is active, what does its AI do: when does it
think, which target does it pick, which mode or skill does it choose, which path request does it make, and which draws
does it make on which seed? This is phase (5) of [ADR-0014](../adrs/0014-scope-game-simulation.md), the last one,
after animation and frame timing (phase (4), plan [0050](done/0050-animation-frame-timing.md)). When it is done:
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

### Phase 1c — The Uber event
- **Owner skill:** reverser (static; one Ghidra, emulation as P1's batches)
- **Starts when:** batch 12 is reviewed. It does not gate Phase 2 and holds no tier AI. Added by the owner, 2026-11-03.
- **What:** what drives Uber Diablo, Uber Baal and Uber Mephisto, whose think functions (rows 145, 146, 147) only
  return (ai/0008, ai/0012 § 2.10): the event handlers on levels 133 to 136, the spawns and minion counts, the helpers with
  no static reference from the AI table (`0x005E9DD0`, `0x005FD0F0`, `0x005F7F10`, `0x005DD140`), Baal's class-709 teleport,
  and the 37 class and 3 state immediates of the batch 11 scan that lie outside the AI ranges.
- **Done when:** each named helper has a caller or is stated as unreferenced after a kept scan; the driver of each of the
  three bosses is named with its address at `[I]` or better, or stated as not found with what was searched; what can be
  emulated is, with controls, as in P1; any case that needs the game is listed for a later harness or owner-play session.
- **Spec:** the result goes into P3b's entries for rows 145 to 147: [monsters/special § J](../specs/monsters/special.md#j-other-entry-paths-and-pre-existing-mods)'s statement and limits, by link, at `[I]`, community statements only as leads under *Open questions* (the `lane/s66` review).

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
    rest do not (the logs held no AI line) (**`lane/p52d` review, 2026-11-04:** the 331 cannot be re-walked, as their logs
    hold no AI line and a replay does not reproduce them; 41 of 49 new gaps close, [ai/0018](../findings/ai/0018-phase2-third-run.md) § 6);
  - H3's 2 218 Raven `MonAttackStats` calls modelled with the owner pair, from the kept logs;
  - a catalogue sample: one AI per P1 batch outside the tier, at least 20 decisions each, where the pilot can stage
    it; the rest stay at their batch's emulated `[C]` or `[I]`;
  - the Phase 1b cases, and H4 and H5's cases if the reviews moved them here;
  - **the state log (required, `lane/r52l` audit):** the AI log records `AiCtl.state` per decision over stock play, with a
    live control: states 10, 11, 12 and 13 observed in the same window (a `Dim Vision` or `Cloak` target, `Terror` or a
    fleeing monster, `Taunt`, The Countess), and the record names the window covered (frames, levels, difficulties). A
    "no setter" row of ai/0013 § 3 (2, 3, 8, 9, 14, 17; 4 and 7 meet the same scan) moves past `[I]` only on that log; until
    then P3b does not call them dead;

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
  [archivist](../backlog/archive/2026-10-30-reverser-archivist-monstats-and-itemstatcost-readers-named-by-ai-0003.md)
  (MonStats, ItemStatCost and States readers). Next: batch 3 (pool-C).
- **2026-10-30 — P1.2 batch 2 Tier B check (architect, `lane/r52c`): accept with fixes (1).** Fix: omission, the search callbacks' "draw nothing" gains its scope (direct calls of `AiSameBaseNearCb`, callees not followed). Rulings: the five unemulated rows stay `[I]` for the batch's done-when (as batch 1); P1.1 reopen condition (b) not met; the three open questions stand (the dance tables and the opposite-word parameter record to the writer read, the stat 80 grant to Phase 2). Gate green. Review request closed.
- **2026-10-30 — `lane/a7c` Tier B check (architect): accept with fixes (4).** Fixes: misread 1 (the vampire `aip5` value list read `4, 6-9` as bare numbers; they are the records `vampire4`, `vampire6..9`), omission 2 (the flee parameter's state 2 condition; `d` in the stat 80 grant undefined), overclaim 1 (the `Velocity` > 0 guard is in the reverser's request, not in ai/0003 § 2.12: kept with a note, routed to the reverser). The per-row `aip` lists in MonStats checked against ai/0003 § 2 for rows 17-30: all 14 match (row 28 has no `aip6`, row 27 `aip2..6`). No `[C]` added; anchors `sub_005F2A00_AiGreaterMummyCb`, `sub_005F4A70_AiVampire`, `UNIT_HasState` match their rows. Whole-document re-read of MonStats, ItemStatCost, States and the d2s.md corpse paragraph: nothing else stale. Gate green. Review request closed.
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
    filed [reverser](../backlog/archive/2026-10-30-architect-reverser-ai-0001-state-rows-reusing-a-first-table.md).
  **What the Tier B check missed:** all five, none reject-grade (no `[C]` without its source, no wrong address). The
  misses are of one kind: text outside the diff that the diff makes stale, and a disagreement with a finding left
  unrouted; a diff-scoped check reads neither unless rule 4's "re-read the findings a column touches" is run over the
  whole doc. Gate GREEN after the fixes.
- **2026-10-30 — P1.2 catalogue batch 3 (pool-C) for review (reverser, static, `lane/r52d`, from `main` 66b96ae8).**
  [ai/0004](../findings/ai/0004-pool-c.md): the seventeen think functions of rows 33, 35–40, 43, 45–49, 52, 56, 57 and
  63 and row 52's `alt`, each with its `aip` reads per record, its `AiCtl+0x14/+0x18/+0x1C` words, its draws in order
  (all on the acting unit's seed; 0–6 per decision) and its command, plus the pieces first read here
  (`MonAiStepAwayXY`, the nest init shared with row 129's, the priest's heal callback, `PathSetFacing` and the trap's
  facing tables). [C] by emulation (run:2026-10-30-ai-cat-emu-3, `tools/ai_cat_emu3.py`, 3 360 cases, 0 mismatches,
  every control failing every case it separates; development runs kept under `emu/dev-1/` and `emu/dev-2/` with their
  tool copies): the decision maps of rows 33, 36, 38, 39, 40, 43, 45, 46, 47, 52, 57 and 52's `alt` up to their first
  callee, `AiCtl+0x14/+0x18/+0x1C` and `Unit+0xC4` included; rows 37 and 63 their draw-free state and timer tests only.
  Left [I]: rows 35 and 37 past `FindHostile`, 48 and 49 (`UnitLifePct` first), 56 (`MonsterOwner`'s `GameFindUnit`
  first), and everything after a boundary. Tier AIs in the batch: 35 static only, 37 its state test emulated. P1.1
  review reopen condition (b) not met: the one search callback (`AiZakarumHealCb`) draws nothing by its body and direct
  calls (its callees not followed). No call of the action helpers (`grep -c` in `b3-asm.txt`: 0). 23 `re/symbols.csv`
  rows (all I). Kept outputs `workspace/logs/r52d/` (manifest 10 lines, with the lane check's nest and sarcophagus control; `emu/` 57, `emu/dev-1/` 58, `emu/dev-2/` 58; each
  passes from its directory). Backlog: the
  [review request](../backlog/archive/2026-10-30-reverser-architect-plan-0052-p1-2-batch-3-review.md),
  [archivist](../backlog/archive/2026-10-30-reverser-archivist-monstats-and-monstats2-readers-named-by-ai-0004.md) (MonStats and
  MonStats2 readers). Next: batch 4 (pool-D).
- **2026-10-30 — P1.2 catalogue batch 4 (pool-D) for review (reverser, static, `lane/r52e`, from `main` d4996fb8; `main` 08f54ba0 merged before filing).**
  [ai/0005](../findings/ai/0005-pool-d.md): the eighteen think functions of rows 64–66, 68–80, 87 and 92 and row 65's
  `alt`, each with its `aip` reads per record, its `AiCtl+0x14/+0x18/+0x1C` words, its draws in order (all on the
  acting unit's seed; 0–5 per decision) and its command, plus the pieces first read here (three search callbacks, the
  vile mother's skill placer 0x005F9E30, the trap arrows' region kind 0x005FB650 with its one `RNG_RandLoHi` draw per
  level region). [C] by emulation (run:2026-10-30-ai-cat-emu-4, `tools/ai_cat_emu4.py`, 4 560 cases, 0 mismatches;
  the `le`, `d0`, new `cmp` (strictness of every non-draw compare, each met at equality in some case) and `r4`
  controls and the site control fail every case they separate; a development run kept under `emu/dev-1/` with its
  tool copy): the decision maps of rows 66, 69, 71, 72, 75, 76, 77, 78, 79, 80, 87 and 92 up to their first callee
  (row 66's return included), row 65's skill-sign test, and the entry calls of rows 64, 65's `alt`, 68, 70, 73 and 74.
  Left [I]: everything after a boundary, so rows 64, 65, 68, 70, 73 and 74 past their entry call (`FindHostile`,
  `SkillFindByOwner`/`HasState`, `MONSTATS_GetClassChainPos`, `UnitLifePct`, `AiUnitSearch`). Tier AI in the batch:
  64, its entry call only (Phase 2's logs). P1.1 review reopen condition (b) not met: the three search callbacks
  have no draw in their bodies and no RNG entry among their direct calls (callees not followed). No call of the
  action helpers (`grep -c` in `b4-asm.txt`: 0). Found: rows 65 and 75 write the `MonHelpBlock` block's `+0x0C`/`+0x10`
  in opposite orders (open question). 24 `re/symbols.csv` rows (all I). Kept outputs `workspace/logs/r52e/` (manifest
  8 lines; `emu/` 77, `emu/dev-1/` 78; each passes from its directory). Backlog: the
  [review request](../backlog/archive/2026-10-30-reverser-architect-plan-0052-p1-2-batch-4-review.md),
  [archivist](../backlog/archive/2026-10-30-reverser-archivist-monstats-and-skills-readers-named-by-ai-0005.md) (MonStats and
  Skills readers). Next: batch 5 (summons).
- **2026-10-30 — P1.2 batch 4 Tier B check (architect, `lane/r52e`): accept with fixes (2).** Fixes: omission, the
  opposite word orders of rows 65 and 75 are two writer/reader pairs already held by the findings (row 30 `Fetish` reads
  type `+0x10`/guid `+0x0C`, row 14 `QuillRat` the reverse; ai/0003, ai/0002 § 2.12), written into ai/0005's summary,
  § 2.18 and open question 1, and into ai/0003's matching open question and `re/types/ai.h` `AiParam` (no defect, no
  Tier A); stale cross-reference, the −1 of the region's `+0x2D4` is written by `MonRegionsBuild` for every region
  (monsters/0001 § 2), now cited in § 2.17 and open question 2. Rulings: (1) rows 64, 65, 68, 70, 73, 74 past their
  entry call stay `[I]` for the batch's done-when (as batches 1–3); (2) P1.1 reopen condition (b) not met (callbacks
  scoped to direct calls); (3) the `cmp` control and the `EDGES` count stand as the substitute controls for the
  draw-free maps, with the `==` and sign tests stated uncontrolled; (4) the remaining open questions stand (row 71's
  state 1, the `MonsterData+0x0E` gate on the dkmag records, the `+0x54` writer, the group's class). Gate green.
  Review request closed.
- **2026-10-30 — P1.2 catalogue batch 5 (summons) for review (reverser, static, `lane/r52f`, from `main` 08f54ba0; `main` f3005398 merged before the run's totals).**
  [ai/0006](../findings/ai/0006-summons.md): the 23 init and think entries of rows 67, 84, 86, 101–112 and 143 and
  state row 7 (15 think, 8 init), each with its `aip` reads, its `AiCtl+0x14/+0x18/+0x1C` words, its draws in order
  (all on the acting unit's seed) and its command, plus 18 helpers first read here (the pet guard 0x005E45D0 and the
  pet mover 0x005E3EA0 shared by the followers, the sentries' charge, the shadow skill helpers, two search callbacks)
  and `SkillLevelClamped` (0x00644AA0). **H3 answered statically `[I]`:** `MonOwnerSkillDamage` reads the owner for
  every term (`SkillDamagePair(ESI skill, EDI owner)`: the owner's clamped level in the summon's `SkillDamage` skill,
  then `PhysMin`/`PhysMax >> 8` and `ToHit` at the owner); the Raven attacks by `SetModeAtUnit(4, t)`, so each of
  H3's Raven calls carries that pair; the 2 218 calls stay P2's. [C] by emulation (run:2026-10-30-ai-cat-emu-5,
  `tools/ai_cat_emu5.py`, 23 families, 5 520 cases, 0 mismatches; `le`, `d0`, `cmp`, the new `u16` (Skill1 unsigned)
  and the site control fail every case they separate; `EDGES` per family; a development run under `emu/dev-1/` with its
  tool copy): full maps of row 84 (init and think), 86, the inits of 101/104, 102, 107 and 110/111, row 102's Skill1
  bound, 106/143's skill-list test and 108's class dispatch; the entry calls of the other followers. Left [I]: every
  follower past `MonsterOwner` (a guid lookup), so the tier AI 67 past its entry call (Phase 2's logs). Found: rows 105
  and 106 read `aip8`'s three cells as three parameters (`shadowmaster`'s 279 in Normal only is the summon skill id).
  P1.1 review reopen condition (b) not met (the two callbacks draw nothing by their bodies and direct calls; row 106's
  loops run over skills). No call of the action helpers. 42 `re/symbols.csv` rows (all I). Kept outputs
  `workspace/logs/r52f/` (manifest 11 lines; `emu/` 93, `emu/dev-1/` 94; each passes from its directory). Backlog: the
  [review request](../backlog/archive/2026-10-30-reverser-architect-plan-0052-p1-2-batch-5-review.md),
  [archivist](../backlog/archive/2026-10-30-reverser-archivist-monstats-and-skills-readers-named-by-ai-0006.md) (MonStats and
  Skills readers). Next: batch 6 (hirelings).
- **2026-10-30 — P1.2 batch 5 Tier B check (architect, `lane/r52f`): accept (0 fixes).** Checked: 42 `[C]` lines, each
  naming run:2026-10-30-ai-cat-emu-5 and the case family, with the meaning readings kept in the `[I]` bullets beside them;
  anchors `MonOwnerSkillDamage` 0x0056E050 (objdump: `MonsterOwner` result `eax` moved to `edi` at 0x0056E0A9, `SkillDamagePair`
  called at 0x0056E0AB, `SkillLevelClamped(edi, esi)` at 0x0056E006), `SkillLevelClamped` 0x00644AA0 (unit at `[ebp+8]`) and
  the 42 `re/symbols.csv` rows (42 I); the manifest passes. Rulings: (1) rows 67 and the other followers stay `[I]` past
  their entry call for the batch's done-when (as batches 1-4); (2) the H3 owner pair stays `[I]` (objdump; the
  summon's own level is not read) and agrees with skills/0001 § 18 and skills/experiments (`MAS.seed`/`MAS.stats`): both
  only say the Raven class has a `SkillDamage` owner pair the checker does not model, and none names the unit whose level
  it reads, so no disagreement and no route; the plan's H3 "unresolved" is answered here for Phase 2. Check 8: no finding
  states a contradicting `aip8` or owner-level reading. Gate green. Review request closed.
- **2026-10-30 — P1.2 catalogue batch 8 (pool-E) checkpoint (reverser, static, `lane/r52h`, from `main` 53705a30; owner pause, token budget).**
  Nothing filed for review yet; no finding, symbol row or tool committed. Done: symbols replayed into the project copy
  `workspace/ghidra-r52h`, then the scratch signatures (`b8-scratch.py` → `b8-sym-scratch.csv`, a reading aid, not
  symbol rows); objdump of `0x005E0100`–`0x005E1C00` and `0x005E3700`–`0x005E3B00` (`b8-asm-a.txt`, `b8-asm-b.txt`);
  Ghidra decompiles of `0x005E0160`–`0x005E1B60` and `0x005E3840`–`0x005E3A00` (`b8-dec-a.c`, `b8-dec-b.c`), all under
  `workspace/logs/r52h/` (no manifest yet). Read from the decompiles so far (to be re-read from objdump, all `[I]`): the
  thirteen think functions are rows 82 `0x005E0160`, 83 `0x005E0260`, 85 `0x005E0490`, 94 `0x005E0980`, 89 `0x005E0C80`,
  93 `0x005E0F60`, 95 `0x005E1080`, 96 `0x005E1250`, 114 `0x005E1540`, 113 `0x005E1860`, 115 `0x005E1900`, 97
  `0x005E3840`, 98 `0x005E3890`; no row of the batch has a `+4` or `+C` word (MonAI § The AI table in the image). Three
  helpers in the range: `0x005E0430` (row 85's search callback, a living same-side monster below 76 % life, nearest by
  life), `0x005E1720` (rows 113/115's search callback, a class-chain test on MonStats row 492, no owner, a `+0x14` of −1)
  and `0x005E17E0` (writes the found guid into the AI control's `+0x14`); `0x005E3900` is batch 5's
  `AiPetCrowdCb` (`lane/r52f`), `0x005E3930` not yet placed. Draw shapes seen: 82, 83, 93, 94 and 113 draw nothing
  before their boundaries; 85 inline steps, `RNG_Range` and one `RNG_RangePow2(seed, 4)` (a direction pick into
  `0x006E337C`); 89 (tier) starts with the `Skill1` sign test then `SkillFindByOwner` (entry-like, as row 65); 95
  starts with `MonAiFindHostile` (entry); 96 reads `AiParamsHead` (kinds 1 and 14) before `MonAiFindHostile`; 114 sets
  `Unit+0xC4 |= 0xE`; 115 starts with `UnitGetOwner` (entry). **Next steps:** (1) read rows 97 and 98 (`b8-dec-b.c`)
  and place `0x005E3930`; (2) re-read every function from objdump (register and stack arguments, call sites), count
  draws with a `b8-draws.py` (copy of r52e's `b4-draws.py`, range list changed); (3) `b8-rows.txt` from
  `python3 -I tools/ai_survey.py rows workspace/merged/data/global/excel <row>` for the 13 rows (the `aip` slots per
  record); (4) `tools/ai_cat_emu8.py` from `ai_cat_emu4.py`/`ai_cat_emu5.py` (`le`, `d0`, `cmp`, `u16` where `Skill1`/
  `Skill2` is bounded, site control, `EDGES`), families per think function, `AiParamsHead`, the position getters and
  `RNG_RangePow2` run on the image; a dev run under `emu/dev-1/`, then the kept run run:2026-10-30-ai-cat-emu-8 inside
  `systemd-run --user --scope -p MemoryMax=4G`; (5) `docs/findings/ai/0009-batch8.md`, symbol rows, merge `main`,
  ledger row, review request.
- **2026-11-03 — P1.2 catalogue batch 8 (pool-E) for review (reverser, static, `lane/r52h`, resumed from the 2026-10-30 checkpoint; `main` dda63dfd merged before the run's totals).**
  [ai/0009](../findings/ai/0009-batch8.md): the thirteen think functions of rows 82, 83, 85, 89, 93–98 and 113–115
  (no `init`, no `alt`; row 83 kind 0, the others kind 1), each with its `aip` reads per record, its
  `AiCtl+0x14/+0x18/+0x1C` words, its draws in order (all on the acting unit's seed: 22 inline steps, 8 `RNG_Range`,
  one `RNG_RangePow2`; 0–7 per decision) and its command, plus three helpers first read here (row 85's heal search
  callback 0x005E0430, the siege imp callback 0x005E1720 and the imp host setter 0x005E17E0). `0x005E3930` placed: the
  hireling think's helper (five calls in 0x005E5446–0x005E561C), batch 6's, unnamed. [C] by emulation
  (run:2026-11-03-ai-cat-emu-8, `tools/ai_cat_emu8.py`, 13 families, 3 120 cases, 0 mismatches, 0 stopped, no
  unaccounted traced read; row 85's corner table 0x006E337C read from the image at all four rows; `le`, `d0`, `cmp`,
  `u16` and the site control fail every case they separate; `EDGES` per family; a development run under `emu/dev-1/`
  with its tool copy): the maps of rows 82, 83, 85, 93, 94, 96, 97, 98 and 114 to their first callee, row 89's
  skill-sign test, the entry calls of 95, 113 and 115. Left [I]: everything after a boundary, so the tier AI 89 past
  `SkillFindByOwner`/`HasState` (Phase 2's logs). Found: row 113 calls `Idle(aip1)` twice when its imp search succeeds;
  the imp callback tests the searcher's owner; row 114 does not read `aip8` (the `reanimatedhorde6` disagreement).
  P1.1 review reopen condition (b) not met (the callbacks and the host setter draw nothing by their bodies and direct
  calls). No call of the action helpers. 16 `re/symbols.csv` rows (all I). Kept outputs `workspace/logs/r52h/`
  (manifest 11 lines; `emu/` 53, `emu/dev-1/` 54; each passes from its directory). Backlog: the
  [review request](../backlog/archive/2026-11-03-reverser-architect-plan-0052-p1-2-batch-8-review.md),
  [archivist](../backlog/archive/2026-11-03-reverser-archivist-monstats-missiles-skills-readers-named-by-ai-0009.md) (MonStats,
  Missiles and Skills readers). Next: the remaining batches (6, 7, 9–12).
- **2026-10-30 — P1.2 batches 6 (hirelings) and 7 (bosses-A) checkpoint (reverser, static, `lane/r52g`, from `main`
  11102c87; owner pause for the token budget). Not for review yet.** Done: read with the Ghidra copy `ghidra-r52g` (symbols
  replayed from `re/symbols.csv`, then the scratch `__fastcall` signatures `b67-sym-scratch.csv`, a reading aid) and objdump
  (`b67-asm.txt`: the batches' ranges 0x005E3930–0x005E3EA0, 0x005E4D30–0x005E5710, 0x005E7AC0–0x005E7D30,
  0x005E5AC0–0x005E5B70, 0x005E6300–0x005E6800, 0x005F5830–0x005F5A20, 0x005F67B0–0x005F6A10, 0x005F7700–0x005F81D0,
  0x005F85C0–0x005F8F80); multiplier sites, RNG calls and callees per function counted by `b67-draws.py` (`b67-draws.txt`);
  stock records `b67-rows.txt`. Functions found: row 61 think 0x005E52D0 and `alt` 0x005E5280 (state row 4's pair), states
  5 0x005E7AC0 and 6 0x005E7C10, `MERCAI_PickSkill` 0x005E4D30, the hireling's fight step 0x005E5050 (its one caller row
  61, 0x005E55BB) and follow step 0x005E3930 (only row 61's five calls, kinds 0, 1, 3), 0x005E3900 (a callback that
  0x005E3930 and batch 5's 0x005E3EA0 push; left unnamed for batch 5); rows 34 0x005F5830, 44 0x005F67B0, 50 0x005F78B0
  (a five-way state dispatch at 0x005F7B36, its table 0x005F7EF0, and the target pick 0x005F77C0 with callback
  0x005F7700), 53 0x005F85C0, 55 0x005F89B0 (calls 0x005B4390, the A4Q1 quest step), 59 init 0x005E6300 and think
  0x005E6320, 90 0x005E5AC0, 144 0x005F8C80, 146 0x005F81C0 (`ret 4` alone); 0x005F7F10 (spawns one of classes 725–730
  with state 184) and 0x005F8010 (a weighted pick over the eight player slots at `G+0x10F8`) have no call, jump, push or
  data-word reference in the image. **Emulated, development run only:** `tools/ai_cat_emu6.py`, 18 families, 4 320
  cases, all matching, every `le`/`d0`/`cmp` control failing every case it separates, site control 0
  (`workspace/logs/r52g/emu/dev-1/`, `check.txt`, manifest 74 lines with the tool copy `ai_cat_emu6.py.rev`, passes from
  that directory); lane outputs `workspace/logs/r52g/manifest-ckpt1.sha256` (12 lines). No finding written yet, no
  symbol rows yet. **Next (a fresh lane on `lane/r52g`):** (1) run the kept run `run:2026-10-30-ai-cat-emu-6` into
  `workspace/logs/r52g/emu/` (`cases`, the 18 `emuboundary` calls under `systemd-run --user --scope -p MemoryMax=4G`,
  `check > check.txt`, `manifest --write`), never over `dev-1/`; (2) write ai/0007 (batch 6: row 61, states 4–6,
  `MERCAI_PickSkill` with the Hireling `Skill1..6`/`Chance`/`ChancePerLvl`/`DefaultChance`/`Mode` reads, the fight and
  follow steps) and ai/0008 (batch 7, `aidist` read by the hostile search only, ai/0001 § 6: no think function of rows 50
  and 146 reads MonStats `+0x52..+0x54`) per batch 4's layout, with the family table, `EDGES` counts and uncontrolled
  edges from the kept `check.txt`; (3) about 20 `re/symbols.csv` rows (all I); (4) one review request for both
  batches. Readings to carry: row 61's distance bands from `AiCtl+0x14` (17–19: `2v`, `v`, `v>>1`; else 24, 16, 5),
  owner mode 2/6 walk and 3 run; `MERCAI_PickSkill` draws `low mod (total + 1)` (a power of two takes the mask) and the
  fallback by class (271 MonStats `Skill1`, 338/359/560/561 A1 in melee range, else `Idle(10)`); the fight step's
  `v14 + 40 + 2·level` capped 95 (98 for classes 338, 560, 561), one draw, and `aip1` = 0 as the ranged branch;
  Mephisto's melee test is `draw <= aip1` (state 2, else 3); in the target pick, the block's `+0x14` is set only for a
  searcher of type 0, so a second draw against `aip3` happens only when a player searches.
- **2026-11-03 — P1.2 catalogue batches 6 (hirelings) and 7 (bosses-A) for review (reverser, static, `lane/r52g`,
  resumed from the 2026-10-30 checkpoint; `main` dda63dfd merged before the run).** [ai/0007](../findings/ai/0007-hirelings.md):
  row 61 `Hireable` and state row 4 (think 0x005E52D0, `alt` 0x005E5280, also row 128's `+C`), states 5 (0x005E7AC0,
  also row 60's think) and 6 (0x005E7C10), the fight step 0x005E5050, the follow step 0x005E3930 and
  `MERCAI_PickSkill`: the owner test, the `v14` distance bands, the crowding draw, the hit chance and its `v14` writes,
  the weighted pick over the Hireling row's `Skill`/`Chance`/`ChancePerLvl`/`Mode` onto `DefaultChance` and the class
  fallback; the plan's skill-list question answered `[I]` (the Hireling row's list; MonStats `Skill1` only for the
  rogue's fallback and state 5). [ai/0008](../findings/ai/0008-bosses-a.md): the ten entries of rows 34, 44, 50, 53,
  55, 59 (init and think), 90, 144, 146, Mephisto's target pick 0x005F77C0 and callback 0x005F7700, the jump table
  0x005F7EF0, `A4Q1_IzualSeen` 0x005B4390, and the unreferenced 0x005F7F10 and 0x005F8010; `aidist` not read by rows
  50/146's functions (`b67-aidist.txt`, 0 reads), so it is the machinery's search's only. [C] by emulation
  (run:2026-10-30-ai-cat-emu-6, `tools/ai_cat_emu6.py`, 18 families, 4 320 cases, 0 mismatches; `le`, `d0`, `cmp` and
  the site control fail every case they separate; `EDGES` per family; kept run in `workspace/logs/r52g/emu/`, not over
  `dev-1/`): full maps of 34 (tier), 90, 59's init, 146, Duriel without `Skill4`, Izual with `v14` ≠ 0, the pick's class
  bounds, the fight step's class dispatch, states 5 and 6 to `RoomIsTown`, Summoner and UberIzual to their first stat or
  state call; entry calls of 61 (tier), its `alt`, the follow step, 50, its pick (with its block) and 59's think. P1.1
  review reopen condition (b) not met (Mephisto's pick callback draws nothing by its body and direct calls). 22
  `re/symbols.csv` rows (21 func, 1 data, all I). Kept outputs `workspace/logs/r52g/` (manifest 22 lines; `emu/` 73,
  `emu/dev-1/` 74; each passes from its directory). Backlog: the
  [review request](../backlog/archive/2026-11-03-reverser-architect-plan-0052-p1-2-batches-6-7-review.md),
  [archivist](../backlog/archive/2026-11-03-reverser-archivist-hireling-chance-columns-read-by-ai-0007.md) (Hireling chance
  columns). Next: batch 8 (pool-E).

- **2026-11-03 — Table readers for ai/0006, ai/0007 and ai/0009 (archivist, `lane/a63`; three backlog entries closed).**
  [MonStats](../tables/MonStats.md): two reader blocks (summons batch: `aip8` of rows 105/106/143, `SkillDamage` at the owner's
  level; pool-E batch: `MissS1`, row 114 reads `aip1`..`aip7` not `aip8`, count guards of rows 82, 83 and the imp
  callback) and the `aip` row, the `SkillDamage` bullet (the owner's level now `[I]`), the `aip8` and `ai_aip_slots_differ`
  bullets. [Skills](../tables/Skills.md): `calc4`, `aitype`, `aibonus`, `Param2`, `Param5` rows. [Missiles](../tables/Missiles.md):
  `Range`. [Hireling](../tables/Hireling.md): `DefaultChance`, `Chance1..6`, `ChancePerLvl1..6`, `Mode1..6` and the formula
  now `[I]` (ai/0007 § 2.4); its open question struck. Tags are the findings' own; no column meaning changed.
- **2026-11-03 — P1.2 catalogue batch 9 (pool-F) for review (reverser, static, `lane/r52i`, from `main` dda63dfd; `main` 00c53f7f merged before the run's totals).**
  [ai/0010](../findings/ai/0010-batch9.md): the ten think functions of rows 116–125 (all row kind 1), row 122's init
  0x005E2FD0 (row 121's init is `AiNestInit`), state row 15 (row 117's think 0x005E1D30) and state row 16 (init
  0x005E2CD0, think 0x005E2D80), each with its `aip` reads per record, its `AiCtl+0x14/+0x18/+0x1C` words, its draws in
  order (all on the acting unit's seed: 37 multiplier loads, 2 of them in state row 14's function, and 9 `RNG_Range`;
  0–6 per decision) and its command, plus what is first read here: the callbacks 0x005E26D0 (row 120's minion search,
  also pushed by row 128) and 0x005E2B70 (row 121's minion count), 0x005DE830 (the overseer's stored hostile),
  0x00541860 (the AI-control getter) and the **action helper 0x005DF850** (`UseSkill` at a random point within `r` of
  the unit, two inline draws; three calls here, two in row 128). **State rows answered `[I]`:** 15 is set by
  `WhipChangeClass` (0x005D1EC0) after Overseer Whip's class change of a `minion1`-based target, so a whipped minion
  runs row 117's think; 16 by `ImpAttach` (0x005D19A4, 0x005D19B9) when an imp's Imp Teleport reaches a tower or a
  beast; state 16's think returns to state 0 itself (0x005E2FB4). **The imp host word** (batch 8's open item): read by
  row 122's think (0x005E30AB, 0x005E30C6), set −1 by its init, at 0x005E3194 and by state 16's detach; `AiImpNearCb`
  reads it through 0x00541860. [C] by emulation (run:2026-11-03-ai-cat-emu-9, `tools/ai_cat_emu9.py`, 13 families,
  3 120 cases, 0 mismatches, 0 stopped, 21 traced reads all accounted (`g_UnitHashOffsets`, state 16's slot table
  0x006E34E0); `le`, `d0`, `cmp`, `u16`, the new `own` (row 122's slots read from its own record instead of the records
  492–495) and the site control fail every case they separate; `EDGES` and `TAGS` per family; development runs under
  `emu/dev-1/` and `emu/dev-2/` with their tool copies): full maps of 117/state 15, 123, the tier AI 125, row 122's
  and state 16's inits; the maps of 116, 118, 119, 120 (to its minion search), 121 and 122 (the helper inside) to their
  first boundary; row 124's skill-sign test; state 16's think to `HasState(U, 143)`. Left [I]: everything after a
  boundary. Found: row 122 reads none of its own `aip` slots (the records `imp1`..`imp4` are a shared parameter table,
  which explains MonStats' row-122 slot disagreement), and its far fire-missile band lies inside the near one, so the
  second test is dead for stock data; state 16's think discards two `Range` results (only when `v1C ≠ 0`, which its
  init never writes); row 121 gives no command once spent; row 123 attacks with a null target; row 125 uses `Skill1`
  with the constant mode 5 and no sign test. P1.1 review reopen condition (b) not met (the callbacks and 0x005DE830
  draw nothing by their bodies and direct calls). State row 14's think 0x005E2610 lies in the range, read in passing,
  left unnamed for batch 12. 18 `re/symbols.csv` rows (all I). Kept outputs `workspace/logs/r52i/` (manifest 14 lines;
  `emu/` 53, `emu/dev-1/` 54, `emu/dev-2/` 54; `emu-recheck/` 52, the kept cases re-run under `lane/r55e`'s fixed
  `EmuBoundary.java` after merging `main` fd2ca68a, outputs byte-identical; each passes from its directory). Backlog: the
  [review request](../backlog/archive/2026-11-03-reverser-architect-plan-0052-p1-2-batch-9-review.md),
  [archivist](../backlog/archive/2026-11-03-reverser-archivist-monstats-skills-readers-named-by-ai-0010.md) (MonStats and
  Skills readers). Next: batch 10 (pool-G).
- **2026-11-03 — P1.2 catalogue batch 10 (pool-G) for review (reverser, static, `lane/r52j`, from `main` 7fddf41d; `main` 3960ea23 (batch 9) merged before the run, `main` c7d3ee1d before filing).**
  [ai/0011](../findings/ai/0011-batch10.md): the twelve think functions of rows 126, 127, 129–134, 136, 137, 139 and
  141, the inits of rows 127 and 134 (`ret 4` alone) and 129 (`AiNestInit`, `v3C = −1`), row 133's class jump to the
  three Ancient thinks (0x005EEB70, 0x005EEDA0, 0x005EF010), each with its `aip` reads per record (rows 130 and 139
  read slots that differ per record), its AI-control words, its draws in order (all on the acting unit's seed: 21
  inline steps and 14 `RNG_Range`; 0–8 per decision) and its command, plus the helpers first read here: row 129's
  class pick 0x005E6020 (`genericSpawn`), row 126's catapult probe 0x005EDF70, the Ancients' target pick 0x005E8F20
  (also Diablo's) and callback 0x005EEB10, row 134's wave step 0x005EF210, row 137's callback 0x005EFA50, and the tables
  0x006E3514 and 0x006E3528. No call of the four action helpers. [C] by emulation (run:2026-11-03-ai-cat-emu-10,
  `tools/ai_cat_emu10.py`, 15 families, 3 600 cases, 0 mismatches, 0 stopped, no unaccounted traced read; `le`, `d0`,
  `cmp`, `u16`, the new `abs` and `self` and the site control fail every case they separate; `EDGES` per family; a
  development run under `emu/dev-1/` with its tool copy): the maps of 126, 127, 129, 130, 132, 134 (to its search), 136,
  137 (to its search), 139, 141 and the three inits to their first boundary or return, row 133's class jump with each
  class think's quest test, row 131's entry call. Left [I]: everything after a boundary (the Ancients past the pick, the
  throne's waves, the A5Q2 paths of row 131). Found: row 134 idles a negative count during its waits; row 129's
  `SetMode(0)` after a failed pick is unreachable (the pick returns 1 on every path); `ancientbarb2` admits a state
  equal to the States count, row 134 does not. P1.1 review reopen condition (b) not met. No tier AI. 26
  `re/symbols.csv` rows (24 func, 2 data, all I). Kept outputs `workspace/logs/r52j/` (manifest 16 lines; `emu/` 61,
  `emu/dev-1/` 62; each passes from its directory). Backlog: the
  [review request](../backlog/archive/2026-11-03-reverser-architect-plan-0052-p1-2-batch-10-review.md),
  [archivist](../backlog/archive/2026-11-03-reverser-archivist-monstats-skills-readers-named-by-ai-0011.md) (MonStats and
  Skills readers). Next: batches 11 (bosses-B) and 12 (towns, NPCs, the state rows).
- **2026-11-03 — Readers of batches 9 and 10 linked (archivist, `lane/a64`).** [MonStats](../tables/MonStats.md) gains two reader
  blocks under § AI columns, "pool-F" ([ai/0010](../findings/ai/0010-batch9.md)) and "pool-G" ([ai/0011](../findings/ai/0011-batch10.md)):
  the `aip` slots read per row (row 122's from the records `imp1`..`imp4`, which settles its entry of the 13 differing rows as a
  shared parameter table; row 133's per Ancient), the `Skill`/`SkMode` reads with the finding's sign tests, row 124's skill level
  (`Sk1lvl`), the constant-skill rows and the count guards; the `genericSpawn` row has its reader (row 129's class pick, `[I]`).
  [Skills](../tables/Skills.md) `aurastate` and `auratargetstate` gain the rows 133 and 134 readers. All `[I]` as the findings give;
  `[C]` only for the maps to their first boundary, scoped in each block. Both archivist entries closed.

- 2026-11-03 (`lane/r66`): two reverser cross-references closed. [hirelings/0001](../findings/hirelings/0001-hirelings.md) points its three "named only" / "out of scope" places at [ai/0007](../findings/ai/0007-hirelings.md) § 2.4 (`[I]`, 0x005E4D30) and re-verdicts the d2dfg-blizzard skill-choice claim held with refinement `[I]`; [skills/0001](../findings/skills/0001-dispatch.md) § 13 carries ai/0006's H3 answer for the owner's level (`[I]`). No tag raised.
- **2026-11-03 — P1.2 catalogue batch 11 (bosses-B) for review (reverser, static, `lane/r52k`, from `main` eda954d8; `main` 26e00331 merged before the run, `main` 908ad0f9 before filing).**
  [ai/0012](../findings/ai/0012-batch11.md): the think functions of rows 51, 128, 135, 138, 140, 145 and 147, row 128's init
  (`ret 4`), the shared `alt`s 0x005E8480 (rows 51, 147) and 0x005FCF30 (rows 135, 140, 145) with their home-point restore,
  and what is first read here: Diablo's decision 0x005E8810 (three 17-word weight tables over sixteen actions, jump table
  0x005E9704), his pick callback 0x005E8EB0, batch 10's scorer 0x005E8530 (the threat score), Baal's pick 0x005FBDD0 with score
  0x005FBB00 and callback 0x005FC000, his decision 0x005FC630 with the tables 0x005FC1C0, 0x005FC300, 0x005FC450 and the
  area-skill tests 0x005FC0C0, 0x005FC070, his action 0x005FCB60 (jump table 0x005FCEF0), the clone spawn 0x005FC860 with its
  callback 0x005FC830, row 138's callback 0x005EF5E0 and the quest step 0x0058BC40. `aip` per record: only rows 128 and 138 read
  any (`b11-aip.txt`, 7 reads); no `aidist` read. Draws all on the acting unit's seed (18 multiplier loads, 4 of them in
  unreferenced functions, no RNG entry call). Of the action helpers only 0x005DF850, twice, by row 128. [C] by emulation
  (run:2026-11-03-ai-cat-emu-11, `tools/ai_cat_emu11.py`, 20 families, 4 800 cases, 0 mismatches, 0 stopped, 20 traced reads all
  accounted; `le`, `d0`, `cmp`, `u16`, the new `abs` and `uns` and the site control fail every case they separate; `EDGES` and
  `TAGS` per family; development runs under `emu/dev-1/` (`result=FAIL`, first-model errors named in ai/0012 § 4) and
  `emu/dev-2/`, each with its tool copy): full maps of the callbacks, the weighted pick 0x005FC130, rows 145 and 147 and row 128's
  init; Baal's action for every `k` to each first callee; both decisions, rows 51, 135, 138, 140, the `alt`s and row 128 through
  its quest step to their first boundary; the three Baal tables at their first call. Left [I]: everything after a boundary
  (Diablo's switch, the weight edits and picks, both scores, Nihlathak's body, the clone spawn). Found: row 145's and 147's thinks
  are `ret 4` as row 146's, with the Uber spawn helpers 0x005E9DD0, 0x005FD0F0 and 0x005F7F10 and the counter 0x005DD140 unreferenced
  and Baal's class-709 teleport unreached (what drives the Uber bosses stays open); Diablo's portal prison passes `(NULL, guid, 2)`;
  Baal's portal flag zeroes a weight already 0; two of ai/0001 § 3's unresolved `MonAiInit` sites (0x005E84D8, 0x005FCF88) pass the
  current state. P1.1 review reopen condition (b) not met (callbacks and scores draw nothing by their bodies and direct calls). The
  H6d Diablo owner pair concerns his death record and quest TC, not this AI: untouched. 32 `re/symbols.csv` rows (30 func, 2 data, all
  I). Kept outputs `workspace/logs/r52k/` (manifest 21 lines; `emu/` 81, `emu/dev-1/` and `emu/dev-2/` 82 each; each passes from its
  directory). Backlog: the [review request](../backlog/archive/2026-11-03-reverser-architect-plan-0052-p1-2-batch-11-review.md),
  [archivist](../backlog/archive/2026-11-03-reverser-archivist-monstats-skills-readers-named-by-ai-0012.md) (MonStats `threat`, Skills
  `attackrank` and slot readers). Next: batch 12 (towns, NPCs and the state rows).
- **2026-11-03 — Owner decision: the Uber event is a phase of this plan (Phase 1c).** The batch 11 check found it had no
  home; the architect recommended a phase here, and the owner accepted ("as recommended"). Phase 1c follows batch 12's
  review and gates nothing.
- **2026-11-03 — P1.2 catalogue batch 12 (towns, NPCs and the state rows), the last, for review (reverser, static, `lane/r52l`, from `main` c34cb3cb; `main` a292a88f merged before filing).**
  [ai/0013](../findings/ai/0013-batch12.md): the thinks of rows 31, 32, 41, 42, 54, 58, 62, 81, 88, 91, 99, 100 (row 60 is batch 6's), state rows 2, 3, 8–14, 17 with the `init`s of 3 and 11, and the town chain first read here: `AiNpcSaveHome` 0x005E6800, `AiNpcNearPlayer` 0x005E68F0, `AiNpcScriptStep` 0x005E6AE0, `AiNpcPathPick` 0x005E7080 with `g_NpcPathActions` 0x00741D74 (DS1 path actions 1–5, `AiCtl+0x38`), `AiPathSkillStep` 0x005E5B70, `AiNearestPlayer` 0x005DDF20. Row 62 and state 8 are the same code; states 10 and 17 differ by search kind only; `aip` only in state 13 (`corruptrogue3`, four sites, `b12-aip.txt`); no `aidist`; none of the four action helpers. **Setters:** 10 `CloakAreaCb`, `CurseSetAiState`; 11 `MonFleeFrom`, `CurseSetAiState`; 12 `CurseSetAiState`; 13 `SuperUniqueSpawn`, The Countess only; **2, 3, 8, 9, 14, 17 none** (`[I]`, scope in ai/0013 § 3). **The five register sites** are all `alt`s passing the current state; `SpawnOwnedMonster`'s block word is 0 at all 15 callers; the restore replays the saved state. **Catalogue recount** (`b12-recount.txt`): 148 table rows and 18 state rows, each in one batch, each with its `init`, think and `alt` words in its finding; rows left short: none. [C] by emulation (run:2026-11-03-ai-cat-emu-12, `tools/ai_cat_emu12.py`, 41 families, 9 840 cases, 0 mismatches, 0 stopped, 18 traced reads all accounted; `le`, `cmp`, `u16`, the new `lo8` and `arg` and the site control fail every case they separate, `d0` separates none; `EDGES` per family; development run `emu/dev-1/`, `result=FAIL`, first-model errors named in ai/0013 § 5). Left [I]: everything after a boundary, `AiNpcNearPlayer`'s body and row 54's and 58's near branches (past `AiUnitSearch`), the 25 quest callees. P1.1 review reopen condition (b) not met. 48 `re/symbols.csv` rows (46 func, 2 data, all I; the finding's commit subject says 49, a miscount); `re/types/ai.h` names `AiCtl+0x38`; ai/0001 § 3 gains a dated note. Kept outputs `workspace/logs/r52l/` (manifest 26 lines; `emu/` 165, `emu/dev-1/` 166; each passes from its directory). Backlog: the [review request](../backlog/archive/2026-11-03-reverser-architect-plan-0052-p1-2-batch-12-review.md), [archivist](../backlog/archive/2026-11-03-reverser-archivist-monstats-skills-readers-named-by-ai-0013.md). Next: the catalogue's review closes P1.2.
- **2026-11-03 — `lane/r52l` Tier A audit (architect; ADR-0023 audit sample) of the Tier B check (Sonnet, accept, 0 fixes): accept with fixes (6).** Read against `objdump` of the pinned image: state 13 0x005E5C50 whole (its 4 `aip` sites, `aip3` +0x62, `aip2` +0x5C twice, `aip1` +0x56, `corruptrogue3`'s row), `CurseSetAiState` 0x005C34B0–0x005C3535 with its map (+0x82: 23 → 10, 27 → 12, 56 → 11, else 0), `MonFleeFrom`'s 0x005DDE10, `SuperUniqueSpawn` 0x005A4BE4–0x005A4C1A (word 6 only, The Countess; row 10 `CorruptRogue` has no `alt`, so `MonAiInit` takes the state), all seven `alt` sites, `MonAiInit` and `MonAiEntryGet`, `SpawnOwnedMonster`'s 15 callers, rows 42, 62, 88, 99, states 2, 8, 9, 10/17, 11, 14, `AiPathSkillStep`, `AiNpcPathPick`, `AiNpcScriptStep`, acts 1, 4, `AiNearestPlayer` with its callback. Every § 2 statement read holds. Row 62 and state 8: the same 91 bytes but three displacements, all three resolving to one callee; rows 10 and 17 differ in the kind word alone (raw table). Kept outputs against claims: manifests pass, `check.txt`'s sums are the finding's, the recount is 148 + 18. **Fixes (ledger: overclaim 1, misread 1, omission 1, wrong anchor 1, miscount 1, tool not kept 1):** overclaim, § 5's and the Answer's `[C]` said the five path actions' records were met, where `SITES` shows acts 1 and 3 ending at `Ovr` or a return, act 2's `R4` met at distance 0 only, acts 4 and 5 at `MonModeAllowed`, scoped, and experiments' *Left `[I]`*; misread, `AiCtlListsFree` also frees the parameter records and the control (0x0058F865), renamed `sub_0058F810_AiCtlFree` here (a row of this lane, `re/symbols.csv`, `re/types/ai.h`, the finding); omission, the whole-struct scope gap the check named and left: a kept scan settles the fixed-size copy (`workspace/logs/r52l/aud/`: one allocator caller, zeroed; 8 of 239 `rep movs` and 3 of 186 `memcpy` calls at 0x40 bytes, none on a control; 61 loads of the pointer shape, no store at offset 0), and § 3 states what stays open; wrong anchor, the kept `src@` of 0x005E817B and 0x005F8240 and `OWNED` 0x005C5CB5 print a textual last write, not the value, § 3 now reads each; miscount, the open question's "three" of four callees; tool not kept, `corruptrogue3`'s `aip` values and `Skill1` had no kept output (the 13 rows of `b12-rows.txt` do not hold it), now `aud/aud-ctlcopy.txt` `STOCK`. **Rulings:** the six rows stay `[I]`, the check's ruling stands, and § Phase 2's *Done when* now requires the `AiCtl.state` log with states 10–13 as its live control and the window named; 4 and 7 are noted with them. The review request's four questions: (1) as that ruling; (2) and (3) stand as filed. The recount tests presence not depth, as the finding says; P3b's entries are as deep as each batch's § Emulation. **Audit of `lane/r52l`:** the check missed 6 by the categories above; reject-grade missed: no (the overclaim is a scope on one `[C]` clause, every `[I]` reading under it holds). **P1.2's catalogue is complete; Phase 1c may start** (its *Starts when* is this review). Backlog: the [review request](../backlog/archive/2026-11-03-reverser-architect-plan-0052-p1-2-batch-12-review.md) closed.
- **2026-11-03 — Phase 1b: the community cross-check (`lane/r52m`, reverser, no Ghidra; `main` a292a88f).** Finding
  [ai/0014](../findings/ai/0014-community-cross-check.md): 67 claims compared with ai/0001–0012 (ai/0013 read from the
  `lane/r52l` copy, 65af21bd; it held no comparable claim beyond the Imp row of ai/0010), verdicts **35 held, 23 held with
  refinement, 6 not covered, 3 contradicted** (counted with `awk -F'|' '/^\| C[0-9][0-9] \|/{gsub(/[* ]/,"",$5); print $5}'
  docs/findings/ai/0014-community-cross-check.md | sort | uniq -c`). Sources registered in `docs/sources.md`:
  `arreat-summit-boss-pages` (15 pages), `arreat-summit-bestiary` (23), `arreat-summit-summon-skills` (3),
  `d2mods-monstats-guide`, `wue-d2-ai-slides`, `arreat-summit-hirelings` re-fetched; `diablowiki-d2-monsters` (HTTP 403) and
  `lurker-monster-ai-threads` (HTTP 409) registered as not read. "The AI Compendium" was not found. No page held code.
  Compared: the machinery (AI column, `aip` cells, Imp, Scarab), the boss pages (skill lists, Duriel's attack choice,
  Diablo's prison, Baal's teleport and clone, the curse split), 28 monster behaviours and skill lists of the tiers and
  catalogue, minion warp and revive, hireling follow and skills. **Not compared:** monsters whose pages hold only stats
  or flavour (Wraith, Bat Demon, Baboon, Skeleton Mage, Skeleton Archer, Finger Mage, Vile Child, most of the 148 rows),
  the Über drivers (rows 145–147 return; Phase 1c), the despawn of minions, summon target weights, the skills' own effects
  and tables (Smite, Jab, trap shot counts), and every page behind HTTP 403 or 409. Agreement promoted nothing.
  **Required cases for the Phase 2 lane** (every `contradicted` claim, all reachable on stock data):
  **P1b-1** Duriel's melee decision (C10, C11): row 44 (MonStats 211; 708 only if the Über event can be staged),
  Normal, at least 300 melee decisions; the page predicts Smite 33, Jab 50, A1 17 percent, the code's two independent
  draws give 33, 33.5, 33.5 (`aip2` 33, `aip3` 50, `aip4` 0); log the command per decision. **P1b-2** a champion corpse
  for a Greater Mummy (C40): row 22, a champion mummy dying within `aip5` of the Greater Mummy in the same near rooms,
  with a unique corpse as control; log the callback's `corpse` slot (0x005F2A00–0x005F2B03) and `MonSkillTargetOk`'s
  verdict (0x005FD470), and whether Resurrect2 is commanded. Phase 1b is done once the architect accepts; the two cases
  join Phase 2's "Phase 1b cases" line. Backlog: the review request (reverser to architect).
- **2026-11-03 — Phase 2, first lane run (`lane/p52a`, reverser, harness, slot 2; also plan 0056's Phase 3 pilot).**
  Tools: `tools/gdb/ai.gdb` + `tools/gdb/ai.py` (rev 3), `tools/ai.py` (model and `check`; models imported from
  `tools/ai_cat_emu*.py`, five hand maps), `tools/test_ai.py` (12 no-game tests), `tools/ai_sessions.py` on the runner
  library, recipe `tools/d2s_recipes/ai-nec.json`. Record: [experiments.md run:2026-11-03-ai](../findings/ai/experiments.md),
  finding [ai/0015](../findings/ai/0015-phase2-first-run.md) (19 symbol rows `I` → `C`: `MonAiEvent` and 18 think
  functions; the compared decisions' first boundaries only). **Counts:** 31 kept case logs in 10 launches, 14 645
  decisions (12 614 compared, **0 mismatches** at the first boundary; 15 not comparable, rev 2 window; 2 016 in rows with no model), 17 679 more
  events that end before the think call. Per tier AI (decisions): Skeleton 357, Fallen 1 393, Wraith 70, FallenShaman
  363, Scarab 180, Mummy 168, GreaterMummy 71, Vampire 279, BatDemon 115, Fetish 130, Andariel 64, CorruptArcher 95,
  SkeletonBow 278, Hireable 5 697, SkeletonMage 226, NecroPet 184, Megademon 98, BloodLord 55: **all 18 at least 50**,
  9 823 over the tier against 1 500. Chaining: 12 368 decision pairs on one seed, at least 20 drawing pairs for
  every tier AI but Fetish (2) and Andariel (5) (short, counted); decision → `SKILLS_SrvStart` 899 starts inside the
  event, 899 exit with the event's exit seed (the floor of 20 on one monster seed met on monsters: FallenShaman 155,
  Vampire 35, GreaterMummy 37, Scarab 13, Andariel 15…). `PathPlan` seed unchanged on 9 618 plan calls (types 2, 5, 6, 7,
  13, 15; the review's condition (b) checked). **State record** (coordinator message, required item): `AiCtl.state` is
  logged at every event: 0 at all 32 324, no state 10–13 event, so the window has no live control and does not test the
  "no setter" reading of state rows 2, 3, 8, 9, 14, 17 ; it needs a window with a curse (Amplify Damage,
  Terror) or `MonFleeFrom` on a monster. **Catalogue sample:** compared with models, at least 20 decisions, batches 1–4,
  8, 9 (e.g. Zombie 135, Swarm 71, Pinhead 202, Frog 200, Vile Mother 71, Arcane Tower 24, Frozen Horror 95); batches 10
  (row 130, 85) and 12 (rows 32, 54, 99) logged without a model. **Pilot figures (plan 0056 Phase 3):** 19 launches
  (10 in the kept batches, 9 development), 31 kept sessions = 31 kept cases (3 case runs not kept: two stayed in the town,
  one first try), 10 launches that were dev or rerun (9 development, 1 rerun) = 53 % (63 % counting the two fresh comparison launches 5203 and 5204 as reruns), launches per kept case 10/31 = 0.32
  (0.61 with development), harness wall 3.6 min per kept session as first stated, withdrawn by [plan 0056 Phase 4](done/0056-harness-runner-efficiency.md#implementation-log): 3.0 (the four batches, 92.3 min) and 3.5 (all 19 launches, 108.1 min) harness, 4.5 by the baseline's lane wall (139 min), tokens about 17 k per kept session (530 967 measured over 31); two cases (`a1-jail`, `a2-halls`) re-run in fresh processes, 385 and
  522 decisions, 0 mismatches. **Short against the Done-when, with counts:** the 331 monster gaps of the H1 oracle
  replacement (0 close: the kept skills logs hold 0 `AID`/`AIB` lines; needs a session with both loggers), H3's 2 218
  Raven `MonAttackStats` calls (not modelled), the Phase 1b cases P1b-1 (Duriel, 0 of 300 melee decisions; needs Tal
  Rasha's tomb route) and P1b-2 (Greater Mummy corpse callback, not staged), the state control above, the catalogue
  sample for batches 5, 7, 10, 11 and 12 (unmodelled rows logged), Fetish and Andariel chained pairs below 20, and the
  decision tree past each first boundary (the log keeps the first eight boundary calls without their results).
  **Resume note for the next lane run:** (1) log boundary results (a return line per `AIB`) and run a resumable model, so
  the claim goes past the first boundary; (2) stage P1b-1 (`/players` 1, Normal, Duriel in Tal Rasha's tomb, at least
  300 melee decisions, `MSM0` already logs the command) and P1b-2; (3) a state-control window (Amplify Damage or Terror on
  a monster; `MonFleeFrom`); (4) re-walk the H1 gaps with `tools/gdb/ai.gdb` loaded beside the skills logger; (5) Raven;
  (6) Fetish and Andariel at `/players 8` for more drawing pairs. The case table of `tools/ai_sessions.py` and the
  library's cap (8 games or 40 min per launch) hold; the Act IV waypoint click needs one retry in about 1 of 10 runs.
- **2026-11-03 — Phase 2, second lane run, CHECKPOINT (`lane/p52b`, reverser, harness, slot 2, rotated at about 360 k tokens; no kept session; `main` 8e26c91a merged).**
  Finding [ai/0017](../findings/ai/0017-phase2-second-run.md), record [experiments.md run:2026-11-03-ai-2](../findings/ai/experiments.md). **Done (mandatory item 1 and
  the machinery of item 2):** `tools/ai.py check` prints the outcome mix per (row, think) and `--controls` runs live negative controls (`c0fd95ec`); over the 31 kept logs of
  run:2026-11-03-ai (`check-mix-2026-11-03-ai.txt`): ten tier AIs with one predicted first boundary (6, 28, 29, 30, 35, 37, 61, 64, 67, 89), eight with two to five; the wrong
  maps fail (call site shifted: 12 629 of 12 629; Fallen's mode test inverted: 1 393 of 1 393; the melee flag flipped: 2 114 of 12 620, none of the ten one-outcome rows), so the
  0 of ai/0015 stays a first-callee claim for those ten. Logger rev 4 logs each boundary's result (`AIR`, 2 285 armed return sites, `tools/ai_retsites.py`) and 48 boundary
  calls per decision; `tools/ai_resume.py` runs the think function from its entry over the pinned game.exe with logged inputs and resumes at each boundary with the logged
  result (unknown values fork; an unfollowed path is a `stop`, not a mismatch): on four **development** logs 1 313 decisions, 1 028 resumed to the end, 0 mismatches,
  14 485 boundary calls matched, 13 173 after the first; controls (known branches reversed, seed off by one step) fail 1 200 and 1 312 of 1 313. 18 + 14 no-game tests.
  This backlog entry is answered: [the separation line](../backlog/archive/2026-11-03-architect-reverser-plan-0056-p4-separation-line-in-tools-ai.md). **Not done (state):**
  the kept batch with rev 4 and the model over it, so no claim past the first boundary is `[C]` yet; the staged variety sessions (branches each map leaves unseen: not recorded);
  the state control window (recipes `ai-nec-curse.json`, `ai-barb.json` build; no session: states 10, 11, 12 not observed, the "no setter" rows stay `[I]` with no window named);
  P1b-1 (no route yet: Duriel's lair is level 73, reached by the staff in the orifice of the one real Tal Rasha tomb of seven; the old driver of plan 0032's sessions is not in
  `tools/`) and P1b-2; H1; H3; Fetish and Andariel at `/players 8`; the catalogue sample; the 3.6 min figure item (the coordinator ruled it: 4.5 min by lane wall stands, 3.0 and
  3.5 harness). **Launch 5202's rule 5 lapse** is now noted in the first run's record. **Resume note for the next lane run:** (1) run the kept batch of the tier AIs with
  `tools/ai_sessions.py run --fresh` (every case its own process; the first-try waypoint click left the case in the town in 4 of 7 development launches, so budget reruns, seed 5601
  failed twice) and run `tools/ai_resume.py check --controls` over the case logs, then record per tier AI the matched boundary calls past the first, the stops with reasons, the
  `ambiguous_steps` and which branches of each map stay unseen; the cap and the `call esi` stops (row 32) are the known ones; (2) the state window: Necromancer `AiNecC` (Dim Vision
  F1, Terror F2, `d2pilot explore --melee --melee-button 3 --curse-keys F1,F2 --keys-cycle`) and Barbarian `AiBar` (Howl, Taunt), the logger already records `AiCtl.state`
  at every event (`st` of AID and AIN); (3) P1b-1 needs a Duriel route (read the plan 0032 Duriel sessions' routing, experiments of items/ lines 2028 on; level 73), P1b-2 the
  Greater Mummy case; (4) H1 with `tools/gdb/ai.gdb` loaded beside the skills logger; (5) Raven; (6) `/players 8`. `workspace/runtime` copies: none; slot 2 is stopped and its saves restored.

- **2026-11-03 — `lane/r52n`, Phase 1c, the Uber event, for review.** [ai/0016](../findings/ai/0016-uber-event.md), [run:2026-11-03-ai-uber](../findings/ai/experiments.md#run2026-11-03-ai-uber): ten families, 3 629 cases, 0 mismatches. **Drivers:** no Uber-specific driver and no creator of classes 704, 705, 709 found, for all three bosses; the generic `MonAiEvent` (0x005B1740) with kind-1 search is what would run, and past the sight pause the think queues no next event. **Helpers:** 0x005E9DD0, 0x005FD0F0, 0x005F7F10, 0x005DD140 unreferenced after the kept scan (`.reloc`, raw rel32, exports, RVA words, nine live controls). **Levels 133–136:** no event handler; the readers are the preset filter, portal, waypoint and town-portal gates, DRLG tests. **The 37 sites:** 20 class tests, 12 not classes, 5 fields; 3 state setters plus one client reader. **Baal's 709 arm:** no stock caller. **Counts:** one unit per helper call, no caller; `demonhole` 3 spawns. Dated notes in ai/0008, ai/0012, archaeology/0002; one refinement, no contradiction. Game cases G1–G5 listed for a later session. Merged `main` c3df75a9 before filing. Backlog: the [review request](../backlog/archive/2026-11-03-reverser-architect-plan-0052-phase-1c-uber-event-review.md).
- **2026-11-03 — `lane/s66`, the Uber spec wording, for review.** Closes the Tier B check's spec entry. [monsters/special](../specs/monsters/special.md): § J holds the reading `[I]` (no Uber-specific driver and no creator of classes 704, 705, 709 found in this image, the search and its limits, a property of the pinned `Game.exe`, no claim about other builds or the realm), the Constants row, step code and § C3 give the class-704 arm as mapped by emulation with reach in play unread, note n12 says there is no Uber event to port, and *Open questions* gains two `[L]` (realm-only; classes 706–708). [monsters/stats](../specs/monsters/stats.md) scopes the hpregen note. [quirks](../specs/quirks/README.md) Q445 restates n12 `[I]`. Totals: special C 151 / I 91 / L 6, stats C 135 / I 51 / L 5, quirks C 340 / I 105 / L 0. No tag raised: ai/0016's emulated `[C]` maps stay for a re-tag. **Part (c) of the entry is carried, not done:** `docs/specs/monsters/ai/catalogue.md` does not exist yet, so P3b's entries for rows 145 to 147 take special § J's statement and limits, by link, when they are written. Wiki: monsters reconciled, combat and seed-to-world dates moved with nothing stale.
- **2026-11-03 — `lane/s66` review (architect, Tier A): accept with fixes, 4.** Read against [ai/0016](../findings/ai/0016-uber-event.md), its scan limits and its reimplementer reading. The negative is stated as this image's property, `[I]`, with the limits; realm-only is `[L]` under *Open questions* alone; Q445 holds one version; `lane/s66`'s date moves are legitimate (combat and seed-to-world restate nothing the stats note changed). Anchors spot-checked against `re/symbols.csv` (11 resolve); the 704 arm's call read at `0x005A175C` in the kept `c1-asm.txt`; `sha256sum -c` of the run's manifest passes, 42 of 42. **Rulings on the lane's four points.** (1) **Raised.** The class-704 arm is `[C]` to `UnitSkillAdd(unit, 123, 20, 1)`, by run:2026-11-03-ai-uber, in the Constants row, the step code and § C3. The `aura` family holds 71 cases of class 704 with a non-zero flag, all at the declared call site with those arguments, the site control passing none; the tag ends at that call and is scoped to what the cases are: a unit with no stat list, so level 1 (20 is an immediate at `0x005A1753`). The local seed, `PlayerSetSkill`, the return and reach stay outside it. The lane's prompt was the orchestrator's, so this under-tag is not the lane's and is not counted. (2) **The narrowing is right and the reverser entry is needed.** ai/0016 § 2's sentence names three classes; its `DATA` view looks for those three alone, and `c1-sites` does not classify the 706–708 operands that `c1-classes` lists, some of them `push`es in quest functions. The entry now says so and names the operands. (3) **Part (c) carried to P3b: fine.** Nothing can hold it until `monsters/ai/catalogue.md` exists; special § J and n12 hold it now. A log sentence alone would not reach P3b, so Phase 1c's *Spec* line now names the statement, its limits and the leads rule. (4) **Applied here.** [items/quest-drops](../specs/items/quest-drops.md) D7's "stock play never reaches it" rested on the portal reading alone, which says nothing of a unit made another way: it now adds the creator search and its limits, "on this reading", `[I]` kept; `updated`, the map row and wiki/items-other-paths' `based_on` moved, nothing on that page stale. **Fixes to the lane's text, by category:** overclaim 2 (wiki/monsters' "nothing that drives them" against the generic driver of § J, with n12 and Q445's "no driver" brought to "no Uber-specific driver"; the same page's "nothing has watched for one in play", for a statement about the helpers), misread 1 (§ J's driver bullet dropped the no-target path and the sight pause), omission 1 (n12's list of the class-gated code read as complete without the combat test, the heal hook and the client name build of ai/0016 § 2). The raise, D7, the reverser entry's detail and the map rows are rulings and review bookkeeping, not counted. **Routed:** the rest of ai/0016's emulated `[C]` maps and drlg/preset's flat "unreachable" to [spec-writer](../backlog/archive/2026-11-03-architect-spec-writer-ai-0016-remaining-emulated-maps.md); those lines are the lane's prompt too, so not counted. **Totals:** monsters/special C 154 / I 90 / L 6, monsters/stats C 135 / I 51 / L 5, quirks C 340 / I 105 / L 0, items/quest-drops C 159 / I 80 / L 2. Ledger, for the orchestrator's row: `accept with fixes`, `4: overclaim 2, misread 1, omission 1`.
- **2026-11-03 — `lane/a66` (archivist, no game, no Ghidra): the readers of [ai/0012](../findings/ai/0012-batch11.md) and [ai/0013](../findings/ai/0013-batch12.md) linked into the table docs; Tier A review requested (ADR-0027).** Both backlog entries closed. [MonStats](../tables/MonStats.md) gains two reader blocks in § AI columns (boss-B batch, 8 bullets; batch 12, 7 bullets) and cell pointers on `threat` (2 rows), `interact`, `Velocity`, `Run`, `aip1`..`aip8`, `Skill1..8` and `aidist`; [Skills](../tables/Skills.md) `attackrank`, `aurastate` and `auratargetstate`; [SuperUniques](../tables/SuperUniques.md) one spawn-path step (record 6 sets state 13); [MonAI](../tables/MonAI.md) one bullet (the setters of the state rows). Every tag is the finding's; the one `[C]` is the sign test of Baal's `Skill6`/`Skill7` and of `AiPathSkillStep`'s `Skill1`, each inside a `[C]` map whose `u16` control separates cases (6 for `bact`, 7 for `h5b70`; the tool copies read the words unsigned), with the zero edge of the curses and the bounds of `Skill1` left `[I]`. Points the review should look at: (1) row 140 never reaches Baal's action 14 (its decisions 7, 9, 14, 15 become 2), so `baalclone`'s `Skill5` has no reader in its own think, which narrows the entry's "`Skill5`..`Skill7` for rows 135/140"; (2) row 128's `Skill1` teleport goes through the action helper with the node's id and `+0x08` word, so `Sk1mode` has no reader there; (3) ai/0013 names `aidist` as `+0x50`, which is `aidel(N)` (`aidist` is `+0x52`), so its "none seen" does not cover `aidist`; (4) the entry's remark that The Countess's other AI row is not read by state 13's code is not in the finding and was not carried; (5) the callback of `AiNearestPlayer` and the state 10/17 think test `interact` on a record the finding does not name for the callback, written as such.
- **2026-11-03 — `lane/a66` Tier A review (ADR-0027, the first of an archivist reader lane): accept with fixes, 16.** Every bullet read against its finding paragraph, with the addresses in the diff checked against objdump of the pinned image (79 of 80 are instruction boundaries, the 80th the mask data word) and the stock values recomputed. **Fixes, all in the review commit:** overclaim 3 (negative `Skill7` `[C]`; negative `Skill1` `[C]`; "`aip1`..`aip3` read only by state 13's think", true of batch 12's ranges only); misread 4 (Baal's teleport point measured from the target, where it is 25 subtiles from the unit; Diablo's action 5 sentence setting the next decision on the state 12 path, where only the cast does; states 10/17 doing `Ring(3)` and idling, where the two exclude each other, 0x005E809C; "`threat` 1, the table's minimum", where 144 blank records store 0 and also score 0); omission 6 (Baal's no-target and `SpawnPosPick` reruns; action 15's two guards; `Skill8`'s `aurastate >= 0` and fall-through in MonStats; state 13's tests before its draw; the helper's `mode` word for row 128's teleport; row 10's own read of the Countess's slots); wrong anchor 2 (0x005E93AE is the `push 2`, not the test; "the control is 0 and `MonAiInit` returns" is ai/0001 § 3); stale cross-reference 1 (the `Skill1..8` cell naming row 138, which has no skill). MonAI's setter bullet carries the scan's limits and does not call the rows dead: no fix. **Rulings.** (1) Split. ai/0012 is explicit enough for `bact` (§ 2.9's `[C]` lists action 8's outcomes, § 4 exempts Baal's curses from the tests with no control), but enumerating the tool's cases shows all 6 hold a negative `Skill6` and none separates `Skill7`, so `Skill6` stays `[C]` and `Skill7` is lowered to `[I]`. ai/0013 never says what `h5b70`'s `u16` reads (ai/0011 names its rows 130 and 141), so a reader needs the tool: lowered to `[I]`, although the 7 cases do show the refusal. Both [routed](../backlog/archive/2026-11-03-architect-reverser-a66-review-finding-notes-ai-0012-0013.md). The lesson for the lane: a control's count names no test; a tag raised from one needs the cases enumerated. (2) ai/0013 is wrong: `aidist` is `+0x52`..`+0x54` (`mov al,[ecx+eax*1+0x52]`, 0x005DD8B0; ai/0001 § 6, ai/0008, MonStats) and `+0x50` is `aidel(N)`. Corrected with a dated note; `b12-aip.py` tests neither offset and the kept asm holds none of the three displacements, so the table now says that. ai/0012's claim stands (`b11-aip.py` scans `+0x52` up). (3) Correct: row 140 maps 7, 9, 14 and 15 to 2 before the only call that could pass 14 (0x005FD2DB-0x005FD306; the other callers are row 135 and two reruns with `k` = 0), so `baalclone`'s `Skill5` has no reader in its think; the narrowing stands, `[I]`. (4) Right to leave it out, but the table's "not carried" sentence was process, not schema, and is gone: the record's row 10 think 0x005F0B00 reads those same slots (ai/0002 § 2.9), which is the fact a reader needs and which makes the entry's wording misleading. (5) Yes, [routed](../backlog/archive/2026-11-03-architect-reverser-a66-review-finding-notes-ai-0012-0013.md), not blocking: a reimplementer needs both. The objdump pointers are in the entry; the table keeps "the finding does not say" until the notes land. ai/0013 also gains a dated clarification of states 10/17. **Compared with the earlier archivist audits (observation only):** `lane/a63` 7 and `lane/a64` 6 were counted after a Tier B check on other batches, so 16 here is not a like measure. On the briefing: rule 7 helped where a bullet states its branches (`threat`, the curses, `interact`, `Skills` `aurastate`), and the lane raised five of its own review points, all five real. It did not stop the failure: seven of the 16 are still a rule shortened or run together (actions 5, 8, 14, 15, `Skill8`, state 13, states 10/17), in the longest bullets.
- **2026-11-03 — P1c remainder in the specs (spec-writer, `lane/s67`).** The entry from the `lane/s66` review closed: monsters/special § J, `MonPostCreateBoss`'s first call for the six bases `[C]` (C 161 / I 91 / L 6), the later mods `[I]`; items/quest-drops D7, the death handler's class map and the drop's flags and first call `[C]` (C 162 / I 80 / L 2), the `std` copies `[I]`; drlg/preset, the level 133–136 filters `[C]` up to the first `PresetUnitSpawn` (C 139 / I 25 / L 2), and its flat "unreachable" note scoped to the portal reading and the absence of a code path found. Each names run:2026-11-03-ai-uber, ends at its first callee and states no reach. Not touched: drlg/maze's own flat "133–136 are unreachable" (outside the entry).
- **2026-11-03 — `lane/a66` Tier A review (ADR-0027, the first of an archivist reader lane): accept with fixes, 16.** Every bullet read against its finding paragraph, with the addresses in the diff checked against objdump of the pinned image (79 of 80 are instruction boundaries, the 80th the mask data word) and the stock values recomputed. **Fixes, all in the review commit:** overclaim 3 (negative `Skill7` `[C]`; negative `Skill1` `[C]`; "`aip1`..`aip3` read only by state 13's think", true of batch 12's ranges only); misread 4 (Baal's teleport point measured from the target, where it is 25 subtiles from the unit; Diablo's action 5 sentence setting the next decision on the state 12 path, where only the cast does; states 10/17 doing `Ring(3)` and idling, where the two exclude each other, 0x005E809C; "`threat` 1, the table's minimum", where 144 blank records store 0 and also score 0); omission 6 (Baal's no-target and `SpawnPosPick` reruns; action 15's two guards; `Skill8`'s `aurastate >= 0` and fall-through in MonStats; state 13's tests before its draw; the helper's `mode` word for row 128's teleport; row 10's own read of the Countess's slots); wrong anchor 2 (0x005E93AE is the `push 2`, not the test; "the control is 0 and `MonAiInit` returns" is ai/0001 § 3); stale cross-reference 1 (the `Skill1..8` cell naming row 138, which has no skill). MonAI's setter bullet carries the scan's limits and does not call the rows dead: no fix. **Rulings.** (1) Split. ai/0012 is explicit enough for `bact` (§ 2.9's `[C]` lists action 8's outcomes, § 4 exempts Baal's curses from the tests with no control), but enumerating the tool's cases shows all 6 hold a negative `Skill6` and none separates `Skill7`, so `Skill6` stays `[C]` and `Skill7` is lowered to `[I]`. ai/0013 never says what `h5b70`'s `u16` reads (ai/0011 names its rows 130 and 141), so a reader needs the tool: lowered to `[I]`, although the 7 cases do show the refusal. Both [routed](../backlog/archive/2026-11-03-architect-reverser-a66-review-finding-notes-ai-0012-0013.md). The lesson for the lane: a control's count names no test; a tag raised from one needs the cases enumerated. (2) ai/0013 is wrong: `aidist` is `+0x52`..`+0x54` (`mov al,[ecx+eax*1+0x52]`, 0x005DD8B0; ai/0001 § 6, ai/0008, MonStats) and `+0x50` is `aidel(N)`. Corrected with a dated note; `b12-aip.py` tests neither offset and the kept asm holds none of the three displacements, so the table now says that. ai/0012's claim stands (`b11-aip.py` scans `+0x52` up). (3) Correct: row 140 maps 7, 9, 14 and 15 to 2 before the only call that could pass 14 (0x005FD2DB-0x005FD306; the other callers are row 135 and two reruns with `k` = 0), so `baalclone`'s `Skill5` has no reader in its think; the narrowing stands, `[I]`. (4) Right to leave it out, but the table's "not carried" sentence was process, not schema, and is gone: the record's row 10 think 0x005F0B00 reads those same slots (ai/0002 § 2.9), which is the fact a reader needs and which makes the entry's wording misleading. (5) Yes, [routed](../backlog/archive/2026-11-03-architect-reverser-a66-review-finding-notes-ai-0012-0013.md), not blocking: a reimplementer needs both. The objdump pointers are in the entry; the table keeps "the finding does not say" until the notes land. ai/0013 also gains a dated clarification of states 10/17. **Compared with the earlier archivist audits (observation only):** `lane/a63` 7 and `lane/a64` 6 were counted after a Tier B check on other batches, so 16 here is not a like measure. On the briefing: rule 7 helped where a bullet states its branches (`threat`, the curses, `interact`, `Skills` `aurastate`), and the lane raised five of its own review points, all five real. It did not stop the failure: seven of the 16 are still a rule shortened or run together (actions 5, 8, 14, 15, `Skill8`, state 13, states 10/17), in the longest bullets.
- **2026-11-03 — `lane/r67` (reverser, objdump only, no Ghidra, no game), two entries closed, for review.** [ai/0012 § 4](../findings/ai/0012-batch11.md): the "Baal's curses" exemption narrowed to `Skill6`; the `u16` control's 6 cases all hold a negative `Skill6`, and none reaches the `Skill7` test (0x005FCD3C), which stays `[I]`; docstring of `tools/ai_cat_emu11.py` follows, a docstring-only revision with the cases unchanged. [ai/0013](../findings/ai/0013-batch12.md): § 5 names `h5b70`'s control, `Skill1`'s sign test (0x005E5BCA–0x005E5BD3), `[C]` to the boundary; § 2.1 `AiNearestPlayerCb` tests the searcher's record, `[C]` as a map on the kept `hcb` run, and the review's null-searcher path does not exist (0x00620BB8, 0x005DC388, before 0x005DDEB4); § 2.5 state 11's widths `[I]`, no run reaches them; the § Data touched anchors for `Velocity` and `Run` corrected. [ai/0016 § 2](../findings/ai/0016-uber-event.md): classes 706–708, `[I]`: no site passes one as an immediate class to a spawn function. 54 operand rows are classified (34 frame slots, 3 fields, 3 string ids, 8 lines, 6 class tests), with raw, data, spawn-call, table and string passes and a live control. Limits: run-time, file, packet and indirect classes are not seen. Kept: `workspace/logs/r67/` (`manifest.sha256`, 7 lines). Entries to the archivist and the spec-writer.
- **2026-11-03 — `lane/a68` (archivist, no game, no Ghidra): the MonStats sentences made stale by [ai/0013](../findings/ai/0013-batch12.md)'s `lane/r67` notes, for review (ADR-0027).** § Readers named by batch 12 and the `interact`, `Velocity` and `Run` rows of the column table: (1) `interact`: the callback reads **the searcher's** class record, `[C]` as a map to the first boundary (`hcb`; not covered: every callee), the clear-bit paths for a class out of range or a null record `[I]`, a null searcher takes no path at 0x005DDEB4 `[I]`; the bit's role stays `[I]`, the meaning `[L]`. (2) `Skill1`: the refusal of a negative value raised `[I]` to `[C]` for the map `h5b70` only (the sign test 0x005E5BCA–0x005E5BD3; the 7 separated cases end at the return); the cast, the Skills-count bound and the class-in-range test stay `[I]`. (3) `Velocity`/`Run`: the load widths of state 11 written whole as `[I]` (`Velocity` `movzx` but acts as s16 with a signed `jle`, divisor `movsx`; `Run` `movsx`; signed `idiv`, signed compare and clamp, so a negative `Run` gives `p = 0`); stock values do not separate the widths and no run reaches the loads; the u16 layout is unchanged. Entry closed.
- **2026-11-03 — `lane/a66` Tier A review (ADR-0027, the first of an archivist reader lane): accept with fixes, 16.** Every bullet read against its finding paragraph, with the addresses in the diff checked against objdump of the pinned image (79 of 80 are instruction boundaries, the 80th the mask data word) and the stock values recomputed. **Fixes, all in the review commit:** overclaim 3 (negative `Skill7` `[C]`; negative `Skill1` `[C]`; "`aip1`..`aip3` read only by state 13's think", true of batch 12's ranges only); misread 4 (Baal's teleport point measured from the target, where it is 25 subtiles from the unit; Diablo's action 5 sentence setting the next decision on the state 12 path, where only the cast does; states 10/17 doing `Ring(3)` and idling, where the two exclude each other, 0x005E809C; "`threat` 1, the table's minimum", where 144 blank records store 0 and also score 0); omission 6 (Baal's no-target and `SpawnPosPick` reruns; action 15's two guards; `Skill8`'s `aurastate >= 0` and fall-through in MonStats; state 13's tests before its draw; the helper's `mode` word for row 128's teleport; row 10's own read of the Countess's slots); wrong anchor 2 (0x005E93AE is the `push 2`, not the test; "the control is 0 and `MonAiInit` returns" is ai/0001 § 3); stale cross-reference 1 (the `Skill1..8` cell naming row 138, which has no skill). MonAI's setter bullet carries the scan's limits and does not call the rows dead: no fix. **Rulings.** (1) Split. ai/0012 is explicit enough for `bact` (§ 2.9's `[C]` lists action 8's outcomes, § 4 exempts Baal's curses from the tests with no control), but enumerating the tool's cases shows all 6 hold a negative `Skill6` and none separates `Skill7`, so `Skill6` stays `[C]` and `Skill7` is lowered to `[I]`. ai/0013 never says what `h5b70`'s `u16` reads (ai/0011 names its rows 130 and 141), so a reader needs the tool: lowered to `[I]`, although the 7 cases do show the refusal. Both [routed](../backlog/archive/2026-11-03-architect-reverser-a66-review-finding-notes-ai-0012-0013.md). The lesson for the lane: a control's count names no test; a tag raised from one needs the cases enumerated. (2) ai/0013 is wrong: `aidist` is `+0x52`..`+0x54` (`mov al,[ecx+eax*1+0x52]`, 0x005DD8B0; ai/0001 § 6, ai/0008, MonStats) and `+0x50` is `aidel(N)`. Corrected with a dated note; `b12-aip.py` tests neither offset and the kept asm holds none of the three displacements, so the table now says that. ai/0012's claim stands (`b11-aip.py` scans `+0x52` up). (3) Correct: row 140 maps 7, 9, 14 and 15 to 2 before the only call that could pass 14 (0x005FD2DB-0x005FD306; the other callers are row 135 and two reruns with `k` = 0), so `baalclone`'s `Skill5` has no reader in its think; the narrowing stands, `[I]`. (4) Right to leave it out, but the table's "not carried" sentence was process, not schema, and is gone: the record's row 10 think 0x005F0B00 reads those same slots (ai/0002 § 2.9), which is the fact a reader needs and which makes the entry's wording misleading. (5) Yes, [routed](../backlog/archive/2026-11-03-architect-reverser-a66-review-finding-notes-ai-0012-0013.md), not blocking: a reimplementer needs both. The objdump pointers are in the entry; the table keeps "the finding does not say" until the notes land. ai/0013 also gains a dated clarification of states 10/17. **Compared with the earlier archivist audits (observation only):** `lane/a63` 7 and `lane/a64` 6 were counted after a Tier B check on other batches, so 16 here is not a like measure. On the briefing: rule 7 helped where a bullet states its branches (`threat`, the curses, `interact`, `Skills` `aurastate`), and the lane raised five of its own review points, all five real. It did not stop the failure: seven of the 16 are still a rule shortened or run together (actions 5, 8, 14, 15, `Skill8`, state 13, states 10/17), in the longest bullets.
- **2026-11-04 — Phase 2, second lane run, kept batch (`lane/p52b`, reverser, harness, slot 2; `main` merged at its head of the day; tools `e0e45d03`).** Finding [ai/0017](../findings/ai/0017-phase2-second-run.md) §§ 6 to 12, record [run:2026-11-03-ai-3](../findings/ai/experiments.md) (and run:2026-11-04-ai-3p). **Kept:** 23 sessions (21 + 2 for P1b-2), 46 launches in all (14 first tries left the character in the town). **First boundary:** 7 539 decisions, 6 272 compared, **0 mismatches** (first callee, call site, registers, stack words, seed, control words; not a branch inside the think function; 1 265 decisions in rows with no model and 2 truncated at a log's end excluded; the 2 mismatches of the first output were truncations, now `unlogged`, tested); controls site 6 272 of 6 272, fallen 814 of 814, melee 1 187 of 6 272. Eleven one-outcome tier AIs; the melee Barbarian, the curse casters and `/players 8` gave none a second first-boundary outcome. **Past the first boundary:** `tools/ai_resume.py` 7 135 resumed, **112 mismatches** (96 in the five melee and curse logs; rows 23: 66, 64: 25, 95: 9, 79: 6, 37: 4, 78: 1, 32: 1), 292 stopped (g_pDataTables read at 0x00744304 in rows 12, 22, 43, 68, 73: 205 decisions, GreaterMummy 26 of 27; `call esi` row 32: 80; return site not armed 4; log ends inside the decision 3), 72 183 calls matched, 64 689 after the first; tier rows with 0 mismatches and the stops are in the finding's § 7 table. **Not explained; no claim past the first boundary is `[C]`.** **State control:** states 10 (38 decisions), 11 (98 decisions, 41 events) and 12 (56 decisions) live in `s-necro-curse` and `s-barb-howl`; states 1 to 9 and 13 to 17 (2, 3, 8, 9, 14, 17 among them) absent over the 21 sessions, 7 539 decisions and 10 721 events, `[C]` for the window, "no setter" `[I]`. **P1b-2:** a built state (flags 4 and 8 written at the callback 0x005F2A00): 4 of 17 champion-flag corpses reached `MonSkillTargetOk`, 2 accepted and commanded (mode 14), 2 refused, 0 of 16 unique-flag. **G4:** 0 hits on the seven helpers in 23 launches, control 0x005B1CF0 live in 23, 0x005A3250 in 2 (`tools/ai_g4.py`). **P1b-1 (Duriel): not done**: route facts from the plan 0032 session 3364 log, `AiDur`, case `d-duriel`; the one development attempt did not enter a tomb (the runner moved the seed to 3365 on the rerun); a case for owner play (finding § 12). **Short:** H1, H3, catalogue sample, the 112 mismatches, GreaterMummy's resume. **Resume note:** (1) find the cause of the row 23, 64, 95, 79 and 37 mismatches (the logger's inputs under a curse or a melee player, `+0xC4` and `c0` changes by opaque callees); (2) record `g_pDataTables` values for the row 22 resume; (3) P1b-1 by owner play (`AiDur`, the staff, Tal Rasha's tomb of seven, the portal, melee Duriel, `ai-g4.gdb`); (4) H1, H3, the catalogue sample. Backlog: the review request (reverser to architect); the G4 entry closed. Usage row in `metrics.md`.
- **2026-11-04 — `lane/p52b` review (architect, Tier A): accept with fixes, 11.** Read against objdump of the pinned image and the kept logs; `tools/ai_resume.py` reproduced the kept 112 line for line. **The 112 are not game behaviour:** 104 are faults of the resume model and 8 a logger limit, and no finding's reading of the game is contradicted (ai/0017 § 7's dated table; `tools/ai_resume_review.py`, `review-p52b/`). By cause: a think's own argument slot protected, so a search's output distance was dropped (rows 64, 95, 37: 38); `Unit+0xC4` changing inside an opaque callee (row 23: 41, row 32: 1), with 17 more where a call inside the command was also logged as the think's; an over-wide forget that lost the control pointer (row 79: 5), with 2 more that also miss one `RNG_RandLoHi` draw (rows 79, 78); the boundary breakpoints left off by the 600-call limit (row 23: 8, `[I]`, next batch tells). All 112 have state 0 and `s-necro-curse` has none, so curses are not a cause and no input is missing. The fixes over the 21 logs: 7 444 resumed, 8 mismatches (cluster F alone), 87 stopped (row 32's `call esi` 80, a return site not armed 4, a log's end 3), 72 865 calls matched, 65 332 after the first; the controls still fail: reversed branches 7 290 of 7 539 (rows 15 and 54 not separated), a seed one step off 7 529 of 7 539. The lane's tags held: it kept all of this `[I]`, and nothing past the first boundary was claimed. **Fixes, all in the review commit:** overclaim 3 (P1b-2's `[C]`; the state control's "no skill in the window sets any state"; "a unique one does not" without Radament's `+0x18`), misread 3 (row 19 Swarm filed as Scarab, so "all 18 tier AIs have decisions" where Scarab has none; the `g_pDataTables` stop filed as a logger gap, where the operand parser stops and the word is `ms2`; `UseSeqSkill` for `sub_00620C10_UnitSetPathTargetUnit`), miscount 1 (G4's control counts are floors), omission 2 (P1b-1's objective would have lost the session to `AI_CAP_ROW` 200; state 13 and the window's frames and caps, which the Done-when asks), wrong anchor 1 (the state word at `AiCtl+0x14`, which is `+0x00`), tool not kept 1 (`resume-tier-*.txt` has no tool in the record; the next lane prints it). **Rulings.** (1) **State control: the window's scope holds only as narrowed.** Absence is `[C]` as a statement about the logged lines of the 21 sessions (Normal, 34 980 frames, 27 caps); "no setter" stays `[I]`, and other stages (the curses not cast, Nightmare, Hell) are outside it. **The Done-when's state item stays open:** state 13 needs The Countess in a logged window. (2) **P1b-2: not allowed as evidence for `[C]`.** ADR-0003 says a breakpoint never writes game memory; ADR-0010 and ADR-0013 admit table cells through a loose `.bin`, and even by analogy keep `[I]` a claim whose code reads the edited value. Lowered to `[I]`, recorded as a deviation and stated as forced. Plan 0012's F1 predates those ADRs and is no rule. No new ADR: the stock route exists, a `-forced` run of MonUMod's champion cells as run:2026-10-15-berserk-forced did, with natural champions, which is step 5 below. C40's case stays open, and the 2 accepted and 2 refused are a lead for it. (3) **G4: adequate for what it says.** The 2 live controls show the breakpoint mechanism fires in each launch; the 7 silent siblings show the window does not reach that family, so it adds nothing about Uber sessions. `[C]` for the window, wording scoped, the static statement `[I]`; the entry stays closed. (4) **Run ids stand:** `-ai-2` the checkpoint, `-ai-3` the kept batch, no collision and no rename, since manifests name them. **Waypoint failures go to a tool fix**, [a new entry](../backlog/archive/2026-11-04-architect-reverser-plan-0052-waypoint-list-and-pinned-seed-rerun.md), not the stage-check entry: that gate worked; the click is what fails, and a rerun also moved `d-duriel` off its pinned seed. (5) **The Duriel objective was not specific enough; [this entry](../backlog/2026-11-04-architect-human-plan-0052-p1b-1-duriel-melee-owner-play.md) is, and can be handed over.** It adds the caps, the seed, the build, the route, no attacks, and the stop rule. (6) **`g_pDataTables` logging is not needed.** **First-boundary floors:** run 1's count, rechecked at this lane's head (14 645, 12 614 compared, 0 mismatches, all 18 at least 50), stays the first-boundary floor. Its rev 3 logs have no `AIR` lines and cannot be resumed, so the past-the-first claim needs its own 50 per tier AI on rev 4 or later logs; short today: Scarab 0, Andariel 9, BatDemon 20, CorruptArcher 22, BloodLord 22, GreaterMummy 27, Vampire 43. **Done-when, what remains:** met: the first-boundary floor, decision → `SKILLS_SrvStart`. Open: chaining for Fetish (2) and Andariel (5), H1, H3, the catalogue sample (batches 5, 7, 10, 11, 12), P1b-1, P1b-2's stock case, state 13. H4 and H5's cases: named by the review that moved them, not re-ruled here. **The next run, in order:** (1) no game: merge `main`; fold fixes P, B, C, N, E, D into `tools/ai_resume.py` with a no-game test each, retire `tools/ai_resume_review.py` once its fixes are in (keeping it runnable against the kept `e0e45d03` revision is not needed: its outputs are hashed), print the tier table with the real rows, and rerun `check --controls` over the 21 logs under new output names; `[C]` past the first boundary is proposed only for rows that then have 0 mismatches and at least 50 decisions, as new statements for review. (2) No game: H3, Raven's 2 218 calls from the kept logs; models for the logged rows of batches 5, 7, 10, 11, 12 where the logs suffice. (3) Tools: logger rev 5: skip lines between `MSM0` and `MSM1`; on the 600-call limit write a marker line and treat the decision as a stop, so nothing is lost silently; the waypoint and pinned-seed entry. (4) One kept batch on rev 5: Scarab (the first run's stage), Andariel, BatDemon, CorruptArcher, BloodLord, GreaterMummy and Vampire to 50 each; The Countess beside a curse case for state 13; Fetish and Andariel at `/players 8` for the chained pairs; H1 with the skills logger beside this one. (5) P1b-2 as `run:…-forced`: list the cells, record the reads of the callback and `MonSkillTargetOk` per ADR-0013, no memory write, a stock companion. (6) P1b-1: the owner entry, whenever the owner has the time; its log is checked by the then current tools. Backlog: review request closed; the two entries above.
- **2026-11-04 — Phase 2, third lane run (`lane/p52c`, reverser, no game; rotated at about 250k tokens).** Steps 1 and 2's H3 and step 3's logger rev 5 of the `lane/p52b` review's order are done; the maps of step 2 and the two backlog entries of step 3 are not. The six fixes are in `tools/ai_resume.py` with a test each, and `tools/ai_resume_review.py` is retired. run:2026-11-04-ai-resume: 7 444 of 7 539 resumed, 8 mismatches (row 23, cluster F), 87 stopped, equal to the review's check. Proposed `[C]` past the first boundary: rows 6, 13, 21, 30, 37, 61, 64, 67, 89, with their outcome mix in [ai/0017 § 13](../findings/ai/0017-phase2-second-run.md); Skeleton and Wraith pass the floor with no call past the first and are not proposed. H3 is met for one owner level: 2 218 calls, 101 separating. Catalogue sample: still short, since the logs hold no non-tier row of batches 5, 7 and 11, batch 10 only in rev 3 logs, and batch 12's rows say little (§ 13). Logger rev 5 has not run in a game. Resume note: ai/0017 § 14. The specs `monsters/stats.md` and `skills/dispatch.md` still say the Raven calls are not modelled: the spec-writer's after this review.
- **2026-11-04 — `lane/p52c` review (architect, Tier A): accept with fixes, 13.** The six fixes, the zero diff and the tool revision hold; the nine rows do not, as filed. Read against objdump of the pinned image and the kept logs. **Fixes, all in the review commit:** overclaim 3 (the nine rows' `[C]` on "a call the code can make"; H3's "owner" in sessions with one player; the two symbol rows without the scope), omission 5 (no count of the decisions an unknown value decided; Fallen's 21 620 of 24 738 later calls at one call site; `sar 8` and the pair's place in H3's remainder; rows 15 and 54 alone, batch 12 "says little" where row 54 cannot fail; [the spec route](../backlog/archive/2026-11-04-architect-spec-writer-plan-0052-h3-pair-retires-spec-statements.md)), stale cross-reference 3 (the finding's status line; "No symbol is raised" under two raises; ai/0006's H3 bullet and skills/0001 § 13 left at the old note), tool not kept 1 (the retired script's last revision), other 1 (the ledger row's cells). **Rulings.** (1) **The nine rows: a consistency check as filed, a reproduction for part of it.** Membership in the set of offered calls cannot fail at a fork, so it is not evidence-rules form 4's "identical outputs". Measured by `tools/ai_resume_flip.py` (run:2026-11-04-ai-resume-flip; the all-at-once control says little either way: row 15 is "not separated" and alone 15 of its 16 sites fail a decision): rows 13, 21, 30, 89 have no branch on an unknown value in any resumed decision, rows 37 and 64 in 81 of 86 and 79 of 91, and rows 6, 61, 67 have one in every decision (0 of 814, 0 of 2 061, 0 of 53). No new evidence form and no ADR: a fork-free decision is form 4 with ADR-0004's boundary oracles. **The sentence `[C]` supports, for those 861 decisions only:** *in each of these decisions no branch the model ran depended on an unknown value; with the logged inputs and the logged results of the boundary calls as oracles, the game's code gives exactly one sequence of boundary calls, it equals the logged one in callee, call site and every word the model knows, and the code then returns with no further call.* Logged paths only; no role, no symbol, no catalogue reading raised. Mummy stands at one call past the first, and Fetish with 243 of 316 on one path: narrow, stated, not wrong, since all their two-way sites fail alone (4 of 4, 7 of 7). Skeleton, Wraith and BloodLord are fork-free too, with no call past the first: nothing to claim there. **Rows 6, 61, 67 and the other 5 and 12 of rows 37 and 64 stay `[I]` past the first boundary** with their first-boundary `[C]`; Fallen's known sites fail 30 of 42 (19 of 22 two-way, sample 60), Hireable's 32 of 36, so the check is not empty, but it does not say which call. (2) **H3: `[C]` stands, narrowed; the raises stand, scoped.** I recomputed the block (21, 23, 385), the base 19 of 1 123 in all 101 first calls and the seed in all 2 320 calls. Three independent values on 101 units with no other source (MonLvl terms 0, no 21 or 22 before) meet reverser rule 14's "a consumer agrees" though the return itself is not logged. Not separated, `[I]`: which unit is the owner (one player), `SkillLevelClamped`'s clamp, the bands, `sar 8` (no remainder), the pair's place before the classic and player adjustments, the Kick, SrcDam, DmgSymPerCalc and ToHitCalc branches, classes 420, 421, 428; `SKILLS_GetPhysMin`, `GetPhysMax`, `GetToHit`, `SkillLevelClamped` stay `I`. **It retires:** monsters/stats.md's "the 2 218 calls of the Raven class 419 are not modelled"; skills/dispatch.md's same clause in M2's remainder, its "Which unit's level is read is register-passed and not resolved", and its Open question `[L]` on that (the spec-writer's, routed). (3) **Row 23's 8 and the 600-call suspicion stay `[I]`** until a rev 5 run shows `AIL` with `pend` 0 on such a decision. (4) **The catalogue sample stays short as named.** No batch 12 row counts: row 54 cannot fail (0 of 3 sites, one offered call at none of its 125), row 99 has no call past the first, row 32 has a fork in all 199, row 100 has 4. Row 130 can count at the first boundary once its map lands, as its rev 3 logs need no `AIR` lines. (5) **Nothing rests on logger rev 5:** read, not run; no tag cites it, and over rev 4 logs its parser and stop change no output. (6) **The run keeps its revision.** `bf720f11` is named, the five tools are unchanged to the head, a rerun at the head is byte-identical (`review-p52c/rerun-*.txt`), and the review's `RROW`, `RSTOP`, `RMISMATCH`, `RTOTAL`, `RCONTROL` lines equal `check-fixed.txt`; four sampled reverts (fixes C, B, N and the limit's stop) each fail their test. Retiring `tools/ai_resume_review.py` is accepted, its last revision `8707b4e1` now named beside its outputs. **The promotion rule for the next rows, past the first boundary:** 0 mismatches, at least 50 resumed decisions with no unknown-value branch (`ai_resume_flip.py`'s census), at least one call past the first, and every two-way site failing at least one decision alone; the sentence above, per row. **The next run, in order, on rev 5, one `run:` id for the stock batch.** No game first: (a) [the waypoint and pinned-seed entry](../backlog/archive/2026-11-04-architect-reverser-plan-0052-waypoint-list-and-pinned-seed-rerun.md), which Scarab needs: seeds 5201 and 5301 gave row 20 85 and 95 decisions, and -ai-3's `a2-oasis-3` 0; (b) the new cases: `a1-countess` (none exists), Fetish at `/players 8` (`stage` has no `players` argument yet), and a `.gdb` loading the skills logger beside this one (`GDB` in `tools/ai_sessions.py` loads neither). (1) **Far Oasis first, as the logger's check:** `a2-oasis` on 5201 and 5301, Scarab to **50**; stop and fix if a first-boundary mismatch or an `AIB` between `MSM0` and `MSM1` appears. `s-barb-flayer` and `s-barb-oasis` beside it for row 23: count `AIL` to settle cluster F. (2) **`/players 8`, each a fresh process:** `a1-andariel-p8` held long enough for Andariel to **50** (41 more) and **20** chained pairs; Fetish, **20** chained pairs. (3) **The thin rows to 50:** BatDemon 30 more, CorruptArcher 28, GreaterMummy 23, BloodLord 28, Vampire 7 (rev 4 decisions count only rerun with the then current tool). BloodLord's floor adds nothing past the first unless a call appears there. (4) **State 13:** The Countess in `a1-countess`, beside `s-necro-curse` and `s-barb-howl` in this batch, with no breakpoint write and no `AI_P1B2`: at least one state 13 decision, its record naming the window's frames, levels, difficulty and caps; "no setter" stays `[I]`. (5) **H1,** the skills recipes of run:2026-10-25-skills and run:2026-10-27-skills under both loggers: the record says how many of the gaps close and why the rest do not; 331 gaps or a named shortfall. (6) **P1b-2, `run:…-forced`, its own id after the stock batch: not ready today.** `tools/gdb/ai-p1b2.py` only has its writing mode. Ready means a mode that writes nothing; MonUMod row 0's champion chance alone in a loose `.bin` with `bindiff`; the reads of MonUMod by the callback 0x005F2A00..0x005F2B03 and `MonSkillTargetOk` recorded per claim before the session (ADR-0013: a claim whose code reads an edited cell stays `[I]`, and no frequency); natural champions; a stock companion. Not ready when the batch ends: it stays this plan's open case. (7) P1b-1: the owner entry. **Not scheduled:** logging the words that fork rows 6, 61, 67 (0x005F0367, 0x005E5353, 0x005E48DE) could lift them to the sentence above, at a log volume nobody has measured; those rows stay `[I]` past the first boundary and it remains in this plan's Phase 2. Backlog: review request closed; the spec route above. The review's own ledger row: verdict accept with fixes (13); overclaim 3, omission 5, stale cross-reference 3, tool not kept 1, other 1.
- **2026-11-04 — Owner decisions.** ADR-0029 accepted: the `drop` statements of items/0014 and quests/travel B1, and frame/0003's `timers`, may rise once a reverser lane keeps the lock-slot scan the ADR requires, with no re-run of the emulation. Forced Uber cases G1, G2, G3 and G5 stay named shortfalls, and the owner may take them as owner play. P1b-1 (Duriel) stays open for owner play, later.
- **2026-11-04 — Phase 2, fourth lane run (`lane/p52d`, reverser, harness, slot 1; stopped at about 250k tokens, "rotated"; no ledger row).** Finding [ai/0018](../findings/ai/0018-phase2-third-run.md), records run:2026-11-04-ai-wp and run:2026-11-04-ai-r5 (and run:2026-11-04-h1), tools `9412f1c1`, `c3e282f4`, `e1fd1181` and the review-ready commit after them. **No game first, committed before any game:** a pinned map seed is kept on a rerun (`PINNED`, `launch_seed`; test `tools/test_ai_sessions.py`), `a1-countess`, a `players` argument to `stage` (`a3-flayer-p8`), `tools/gdb/ai-skills.gdb`. **The waypoint:** the cause is the black screen of a game's first seconds read as the open list by `Pilot.menu_open` (4 of the first 12 probe launches failed; the trace shows the dark share 1.00 at the first click in the 2 that carry it); fixed by `wp_click_until_open` (12 of 12 probe launches after it); a second cause, a click that lands behind the waypoint, failed 5 first attempts (3 as filed; corrected at the review) of the 18 launches of the kept batch and the runner's retry rescued all 5; 0 launches stayed in the town, so the entry's Done-when holds and it is closed, with the hover reading named in the resolution. **The kept batch on logger rev 6** (run:2026-11-04-ai-r5): the first rev 5 Far Oasis logs had 36 first-boundary mismatches (Scarab, `GameFindUnit` at 0x0058F0FF hidden inside a pending `MonsterOwner`): a logger fault, fixed as rev 6; the same stage then 0 over 321. 17 launches, first boundary 6 524 decisions, 0 mismatches, controls fail as required; resumed 6 438, 0 mismatches, 86 stopped. **Rows against the promotion rule:** met by 28 Vampire (56), 29 BatDemon (215), 35 CorruptArcher (111), 382 decisions, proposed as new `[C]` statements for review (the sentence in ai/0018 § 4, per row); not met by 20 Scarab (one two-way site fails none); under the floor: 22 (35), 34 (42), 125 (16). **Short:** Andariel 42 of 50 and 2 chained pairs of 20, Fetish at `/players 8` 11 pairs of 20 (the predictions were wrong), GreaterMummy, BloodLord; state 13 (two Countess launches, descent stopped at levels 24 and 23, states 0 only); H1 (the replay does not reproduce the gaps; 0 of 42 gaps closed by the span rule; 187 of 244 decision exits 0 steps from the next observation, lead only). P1b-2 not run (it needs a `-forced` mode that writes nothing; `tools/gdb/ai-p1b2.py` has only its writing mode) and Duriel not launched, as ordered. **Resume note:** (1) a hover wait before the waypoint click, and a fallback for the Countess descent (`--descend 9` fails at levels 23 and 24), then State 13; (2) Andariel and Fetish chained pairs, GreaterMummy, BloodLord to 50; (3) H1: why the walk closes none where 187 links are 0 steps (the first `MAS0` after a decision may be another monster's); (4) review of rows 28, 29, 35. Slot 1 stopped and its saves restored.
- **2026-11-04 — `lane/p52d` review (architect, Tier A): accept with fixes, 16.** Read against objdump of the pinned image and the kept logs; both manifests pass; `ai.py`, `ai_resume.py` and `ai_resume_flip.py` at the head are byte-identical to the kept `r5/` outputs, and `ai.py` over the 21 rev 4 logs to its kept check. Nothing uncommitted; the resume note could be followed, and its H1 step is answered below. **Fixes, all in the review commit:** misread 2 (H1's "0 of 42 close" and "a `MAS0` after the decision": the `MAS0` lies inside `AID`..`AIX`, so the first walk failed by construction; the order's "41 more" and "23 more" counted on rev 6 alone, which called Andariel, GreaterMummy and Fetish short), miscount 4 (5 first attempts, not 3; Vampire's 21 + 35, not 36; 334 `AIL` of 17 logs, not 18; 36 of 101, not 91, with a run id that does not exist, in the logger's comment), overclaim 3 ("black in 4 of 12" where 2 were measured; "cannot be walked" from 6 of 21 sessions; "no result depends on sound" past the sound pair's one walk), omission 5 (the 4 `BD.elem` mismatches in sor-3's kept check, a `n` collision between the two loggers; what the two zeros test; the open-span `AIB` lines of the other logs; the second Countess launch unchecked and the window's frames; ADR-0028's case list and the launches not kept), tool not kept 1 (the probe logs and 4 dev-rev5 files in no manifest), other 1 (no test could see `run()` lose `launch_seed`: reverting it passed).
**Rulings.** (1) **Rev 6: not a mismatch explained away; the 0 stands.** The order said stop and fix, the lane stopped, kept the first check (`dev-rev5-check-oasis.txt`) and left its predictions as written. The 36 are exactly the rev 5 decisions with `MonsterOwner` at 0x005F258A (29 and 7, all with a non-zero return); `ai_resume.py` passes Scarab 101 of 101 on those same logs; rev 3 logged the line; no model changed; and rev 6 can add only that one (function, site). Its words held in all 43 decisions on the new logs, 24 from a seed that did not exist at the fix. **As a hold-out:** the 15 other launches are one; 5201 and 5301 are a repeat of the logger, different games on the same seeds. `tools/gdb/ai.py` and `skills.py` write no memory or register (rule 17; read and grepped). (2) **The rows: 28 (56 decisions), 29 (215), 35 (111) meet the rule whole**: 0 mismatches; 56 resumed is 56 with no unknown-value branch, and likewise 215 and 111 (`FLIP` lines, census over every resumed decision); 168, 526 and 226 calls past the first; two-way sites 15 of 15, 8 of 8, 10 of 10, every site in the row sampled, so "fails at least one" is not weakened by the 60-decision sample. **The sentence, per row, for those decisions and logged paths only, in the rev 6 logs:** *in each of these decisions no branch the model ran depended on an unknown value; with the logged inputs and the logged results of the boundary calls as oracles, the game's code gives exactly one sequence of boundary calls, it equals the logged one in callee, call site and every word the model knows, and the code then returns with no further call.* No role, symbol or catalogue reading is raised; the first-boundary maps of the three stay `[I]`, and their first call is one outcome. AIL lines in rows 28 and 35 (2, 9) have `pend` 1, so the limit lost none of the think's own calls. **Added by this review: rows 22 (62) and 34 (51) meet it too, on the rev 4 and rev 6 logs together**, as the order's counting allowed (the lane read it as rev 6 only): 98 calls past the first, 9 of 9; and 2 calls past the first, 5 of 5, narrow. The same sentence, in those logs. BloodLord stays out: 38, no call past the first. **Scarab: right to refuse.** 0x005F283F clears `AiCtl+0x14` and returns with no call after it, so no comparison of calls can see it; the rule is not amended for it, and row 20 stays `[I]` past the first boundary. (3) **Waypoint: the cause holds as `[I]`, and the entry stays closed on the corrected count.** All 12 after the fix opened at click 1 with a dark first sample, so this is no retry's luck; the measured failures are 2, and the fake-pilot tests hold the rule. 0 of 18 launches lost meets the entry; 5 of 18 first attempts is its second cause, a reading, and costs one retry, so no run is ordered. The pinned-seed half now has a test that fails on the revert. (4) **First boundary, outcome mix.** 3 313 of 4 476 compared decisions are in 16 thinks with one first call: they confirm that call and its words, no branch. Resumed: 3 055 of 6 438 are fork-free; 42 304 of 46 564 later calls are in decisions a fork could not fail. Both zeros stand and now say so. **The 2 `AIB` after a lost `MSM1` do not trip the Far Oasis stop:** they are 6 in 18 logs, each after the command's `AIR`, so outside the command; the order's words did not foresee it, and rev 5's `on_ret` does. (5) **Row 23: `[I]` holds.** 256 resumed, 0 mismatches, and of 334 `AIL` (17 logs) none with `pend` 0, but only 2 are row 23's, so the suspicion is untested rather than refuted. (6) **Predictions and thin rows.** `/players 8` was wrong as filed and stays recorded as wrong. Across the three batches Fetish has 22 drawing pairs, met; Andariel 8; BatDemon 1 of 300. (7) **H1: the shortfall as filed was not honest about its cause, through a tool fault; the correction is the result.** 41 of the 49 new gaps close, all row 13, with all 91 decisions reproduced and 0 steps to the last boundary line. 8 stop at an `AD0`, as attacker, unexamined. The 331 are 330 of classes 58 and 59, 257 at `MAS0` and 70 at `AD0`, the same shape. **`tools/ai_h1.py`'s 187 of 244 is a count and no more**, and the `[I]` is kept as that. **Done-when: met for what logs can give, by ruling.** The 15 unrun sessions are not needed: a replay gives new gaps, not those. (8) **Parsers and tools.** The `SST0`/`SST1` split and the AI span change no earlier output: main's `skills.py` and this one are byte-identical over 15 older logs, and `ai.py` over the 21. `ADR-0028` holds now, its case list added; `-ns` reworded. 
**Phase 2 against its Done-when.** Met: 1 500 over the tier at the first boundary (9 823 tier decisions, 9 808 compared, all 18 at 50 or more; [corrected at the `lane/s52a` review] 14 645 is every logged row); decision → `SKILLS_SrvStart`; H3 (scoped, `lane/p52c`); chaining except the two below; H1 as ruled. Past the first boundary, 50 per tier AI on rev 4 or later logs: met but for BloodLord (38, no call past the first there). **Short, by name, their claims `[I]`:** chaining Andariel 8 of 20, BatDemon 1 drawing pair; the catalogue sample, batches 5, 7, 10, 11, 12 (`lane/p52c` ruling 4, not re-measured); state 13 (10 and 11 here, 12 in run:2026-11-03-ai-3, a live control, so "no setter" stays `[I]` and P3b does not call those states dead); P1b-1 Duriel (owner entry), P1b-2 (not ready, C40 stays open), the Uber forced cases (owner entry). This plan's log names no H4 or H5 case moved here. **Recommendation: no further harness batch; P3a next.** At about 500k with review, a run could buy 12 Andariel pairs and 12 BloodLord decisions that add no call past the first, on a Countess route that has failed twice and needs pilot work first. None of it changes what P3a states, since the Done-when lets those fall short with their claims `[I]`. **Next in this plan: merge this lane, then P3a (spec-writer, `docs/specs/monsters/ai/`)**, carrying each short above as `[I]` or under Open questions, with C10 and C11's community disagreement listed there as the evidence rules require. P3b follows; P1b-2 is not built unless the owner asks. **Owner decision, recommended and not blocking P3a:** one owner-played session for P1b-1, Duriel (the entry's 10 to 15 minutes), and if convenient The Countess at `/players 1`, which gives state 13. If not played, C10, C11 and state 13 stay `[I]`. The owner should also know that H1's Done-when is ruled met on new gaps rather than the 331. Backlog: no review request was filed, and none is open for this lane. The review's own ledger row: verdict accept with fixes (16); misread 2, miscount 4, overclaim 3, omission 5, tool not kept 1, other 1.
- **2026-11-04 — `lane/s70` (spec-writer): H3's retirements in the specs.** [The entry](../backlog/archive/2026-11-04-architect-spec-writer-plan-0052-h3-pair-retires-spec-statements.md) resolved, from [ai/0017 § 13](../findings/ai/0017-phase2-second-run.md#13-third-part-2026-11-04-lanep52c-the-fixed-model-the-tier-table-h3-logger-rev-5) and ai/0006's H3 bullet. monsters/stats § H1 and skills/dispatch § M2 lose the "not modelled" clause and carry two new bullets each: `[C]` the 2 218 calls of class 419 with the pair of skill 221 at level 20, sessions with one player; `[I]` what those calls do not separate, as the `lane/p52c` review listed it. skills/dispatch's "register-passed and not resolved" is gone and its M2 bullet states the condition and the pair from ai/0006; its `[L]` is struck, and the other `[L]`, monsters/stats' and combat/README's owed terms are scoped to the pair past that one level. wiki/skills rewritten to match. Past-the-first-boundary statements of ai/0017 § 13 stay out, as the entry says. Tags: monsters/stats C 135→136, I 54→55, L 5; skills/dispatch C 76→77, I 194→195, L 8→7. No raise beyond the entry's scope. For review.
- **2026-11-04 — `lane/s70` review (architect, Tier A): accept with fixes, 11 over both plans, 3 of them here (plan 0054's log has the count and why the branch is squashed).** The H3 half holds. **Recounted** with `tools/ai_h3.py` over the two kept logs: 2 320 calls, 2 218 with a list, 102 without, 101 first calls and 2 117 later ones, 0 seed differences, every alternative failing all 101, one owner level (20). **The modes:** the lane is right. The logged calls are in modes 0, 1, 2 and 4 only, and MonLvl alone gives 0 for all three stats, so they don't separate. M2's condition and pair read against 0x0056E000–0x0056E0B3 as [ai/0006](../findings/ai/0006-summons.md)'s H3 bullet has them, and at `[I]`, its tag; the bullet's list of what isn't separated is ai/0017 § 13's. **The struck `[L]`** asked which unit's level is read: answered, by the code reading only, `EDI` from `MonsterOwner`, and the sentence says so. A second player, a second level and the other three classes stay under the other `[L]`s, and nothing past the first boundary came in. **ADR-0030:** wiki/skills' rewrite read as Tier A: scoped to one level and one player, "never" inside the read-from-the-code sentence; it dropped the to-hit from that sentence (fixed). wiki/combat's date: the page says nothing of the pair, so no claim moved. **Missed by the lane, fixed:** wiki/monsters still listed a monster skill's extra damage as read from the code only, twice. **Fixes here, 3:** omission 1, stale cross-reference 2. Tags unchanged from the lane: monsters/stats C 136, I 55, L 5; skills/dispatch C 77, I 195, L 7. Not merged by this review. `audit: n/a, Tier A.`
- **2026-11-04 — Phase 3a (`lane/s52a`, spec-writer), first commit.** Written: [monsters/ai](../specs/monsters/ai/README.md) (the tick, the AI's clock, the table and its dispatch, the AI state, the event kinds and their seeds, § G the first boundary, § H past it) and [monsters/ai/machinery](../specs/monsters/ai/machinery.md) (target search, the command, the path request, following, the helpers' draws, and § T: each of the 18 tier AIs as pseudocode with its draw order). Tags: C 38 / I 52 / L 10 and C 26 / I 112 / L 8. Cross-links: skills/dispatch (§ M1, § P, the monster gaps' `[L]`), skills/README, monsters/stats, monsters/spawn (one new `[I]` bullet in *Outputs*), monsters/README, drlg/lifecycle (the 9 override calls resolved, restore's AI), hirelings (`MERCAI_PickSkill`), path/overview (E3 and the request), anim/README, the glossary. Row `monsters/ai` set to draft spec as the lane's prompt listed it; the rows of monsters/spawn and hirelings take the new dates and counts (gate E15). **The evidence carries as ruled:** first boundary `[C]` at its floors (14 645, 12 614 compared); a hand map's equality `[C]`, the map itself `[I]` (§ G5); the sentence quoted once, § H1, for rows 13, 21, 30, 89, 28, 29, 35, 22, 34 and the 81 and 79 of 37 and 64; rows 6, 61, 67 and the other 5 and 12 stay `[I]` past the first; the outcome mix stated (§ G3, H2). No role, symbol or catalogue reading raised. **Short, by name, `[I]` or under Open questions:** chaining Andariel, BatDemon; BloodLord; the catalogue sample; state 13; P1b-1 with C10 and C11; P1b-2 and C40; Uber forced cases; Row 23's limit; H1's 8 and the 330 of 331. **New backlog:** [the entry](../backlog/archive/2026-11-04-spec-writer-reverser-plan-0052-row-28-vampire-draw-order.md) to the reverser: row 28's prose hides two draw orders and `T56`'s arguments, row 29's alt, the range in `MonAiFindTarget`, `MonAiMove`'s refusal with flag 2 clear; none blocks. **Numbers:** recounted against the kept `check-run-*`, `resume-run-*`, `flip-*`, `census.txt`. For review: leave open. Read first: README § G and § H, then machinery § A2, § B6, § T28.
- **2026-11-04 — `lane/s52a`, a count for the review.** The spec's § G1 does not repeat "14 645 over the tier". 14 645 is every logged row (run:2026-11-03-ai: 10 374 + 2 240 compared, 2 016 no model, 15 not comparable). The 18 tier AIs' own decisions in the same record sum to 9 823, so 12 614 compared holds about 2 800 outside the tier, and [ai/0015](../findings/ai/0015-phase2-first-run.md)'s "for 13 tier AIs … 10 374 decisions" and the Done-when's "14 645, all 18 at 50 or more" read wider than the record. The floor itself holds: all 18 are at 50 or more, and 9 823 is over 1 500. Not edited here, as the finding and the plan's ruling are not this lane's. Wiki `based_on` dates of characters, levels, monsters and saves moved to the new dates of hirelings and monsters/spawn: those two specs gained links and one AI `[I]` bullet, no claim the pages restate.
- **2026-11-04 — `lane/s52a` review (architect, Tier A): accept with fixes, 22.** Read against objdump of the pinned image, ai/0015, ai/0017 § 13, ai/0018 and the kept logs. H1's sentence is quoted exactly, with its scope per row; rows 6, 61, 67 and Scarab stay `[I]` past the first; G3's and H2's outcome mixes and every number of §§ A, E6, G, H recount against their findings; no role, symbol or catalogue reading raised; `src:` and `run:` resolve; diagrams hold nothing the text lacks; the cross-links, the map row and the `based_on` moves moved no claim. **What the lane missed lies in the prose it restated:** the pseudocode entries hold where read (rows 6, 13, 29, 35, and `Ring`, `T56`, `StepAway`, `UseSkill`, `Idle`, `Delay` against instructions, no error of order), but prose sentences of ai/0001 (and one of ai/0006) were wrong or short and carried into the spec; no earlier review of those findings caught them. **Fixes, all in the review commit, each written into the finding too (ai/0001, ai/0003, ai/0006, ai/0015):** misread 6: A2's and E4's flag `0x40` backwards (the code forces the line test **on**: 0x005DD836, 0x005DD965), B6's "`AiCtl` bit 0" (flag 1 sets `0x40`, 0x005DEC03), A3's confusion alignment (it flips and restores; the `1` is the flag argument), F3's `UnitSetEvent(0)` (16, before the flag), F4's "found point" (a unit, target and distance), a type-3 forced target called "an object". Omission 10: T28's block (flag 5); A2's range as the start of best, list 9's lack of one and `rec+0x24`'s write; B6's returns, the override clear and `Walk(t, 0)` on refusal; D2 storing only non-zero words (so a later `Ovr(0, 0, d)` keeps an earlier parameter: this changes the plan); E1's refused step and override type 7; A4's decoy; A6's `+0xC4` bit `0x04`; C4's cancel; T6's mode as read at entry; T67's searches made as the owner. Miscount 1: D5's "6 once", 5 or 6 twice (0x005ECBD7). Under-claim 3: row 23, the code's side of C10 and C11, the code's side of C40. Overclaim 1: "the map" in § T's `[C]` lines now stated to the first callee. Other 1: `re/types/ai.h`'s flag comment, which follows the 0x40 fix. **Rulings on the lane's flags.** (1) **The floor's scope:** the lane is right. 14 645 and 12 614 are every logged row; the tier is 9 823, 9 808 compared, Scarab's 15 aside. ai/0015's sentence and this plan's Phase 2 line are corrected, with 7 568 of the 10 374 emulated decisions in the tier and 2 806 outside. **Phase 2's floor is met on the tier's real count, all 18 at 50 or more (minimum 55), and P3a's Done-when is met.** (2) **Hand maps: fair, and what the `lane/p52d` ruling said.** The equality `[C]`, the map as a rule `[I]`, rows 6, 13, 28, 29's think, 35; the per-AI table's closing paragraph keeps a one-outcome row from reading as a branch. (3) **Short items as `[L]`:** state 13, chaining, BloodLord, the catalogue sample, H1's remainder, P1b-2's question and the Uber cases are right: each asks what a run would show, and the code reading sits at `[I]` in its own statement (E5, E7, A3, H4, A5). **`[I]`, not `[L]`:** row 23 (the `lane/p52c` and `lane/p52d` rulings said `[I]`), the code's side of C40 (`[I]`), and of C10 and C11 (the map `[C]` by `duriel`, the frequencies `[I]`), split from their open questions. C10 and C11's community disagreement stays stated and unresolved under Open questions, as the rules allow. (4) **The research-map row edit:** fine as ordered; the row now carries this review. (5) **Row 28: the prose was not implementable, and it does not block.** Its two draw orders and `T56`'s arguments decide a Vampire's seed, and P3a's Done-when asks for each tier AI's draw order, so filed as it stood the entry would have blocked promotion for that row. The instructions answer it in a few lines, so the review read them (0x005F4A70–0x005F4FCC), wrote the compact block into ai/0003 § 2.12 and T28, and ran the block as written over the kept logs (`tools/ai_t28_check.py`, run:2026-11-04-ai-t28): 100 decisions, 99 compared, 0 mismatches, controls failing where the arms are reached. **That check is the lane's scrutiny for a claim settled at review; it does not cover** step 2's melee arm, the fleeing arm or `Skills`, which no log reaches and stay `[I]`. The entry's other three (the alt's `v14`, A2's range, `MonAiMove` with flag 2 clear) are answered from the same reading. The entry is closed; the four `[L]` it held are gone. **Reimplementable:** the tick, the state, the search, the command and all 18 thinks can now be written from the spec, draw for draw, with these limits named: a callee's body is its own spec, row 67 and `AiHireFollow` remain code reading past the first, and § A5's walkers and callbacks are summarised (kinds 3 to 12, by role); P3b or a reimplementer that needs a kind's callback reads ai/0001. **`drlg/lifecycle`'s 9 calls:** "resolved" is honest. All 103 and 9 sites recounted over the image; none passes 4, 10 or 14. **ADR-0022, plan 0055:** see that plan's Phase 2b. **Promotion:** monsters/ai and monsters/ai/machinery `reviewed`, row `monsters/ai` set. Tags C 39 / I 55 / L 9 and C 28 / I 114 / L 4. Next in this plan: P3b (`lane/s52b`, branched from before these fixes: it must merge this review before it reads A2, B6 or T28), then P4. The review's own ledger row: verdict accept with fixes (22); overclaim 1, under-claim 3, misread 6, miscount 1, omission 10, other 1. No backlog entry is routed.
- **2026-11-04 — P3b, resume note (`lane/s52b`, spec-writer; rotated at about 250k tokens; no ledger row).** `docs/specs/monsters/ai/catalogue.md` holds every heading (148 rows, 18 state rows), each row's table shape and logged count; **written:** rows 0, 1, states 0, 1 and batches 1 to 9 (states 4–7, 15, 16). **To write, 42 entries, each marked `<!-- body R<n> -->` or `<!-- body S<n> -->`:** batch 10 (rows 126, 127, 129–134, 136, 137, 139, 141, from [ai/0011](../findings/ai/0011-batch10.md)), batch 11 (51, 128, 135, 138, 140, 145, 147, from [ai/0012](../findings/ai/0012-batch11.md), with [ai/0016](../findings/ai/0016-uber-event.md) for the Uber rows), batch 12 (31, 32, 41, 42, 54, 58, 60 (alias of state 5), 62, 81, 88, 91, 99, 100, states 2, 3, 8–14, 17, from [ai/0013](../findings/ai/0013-batch12.md); state 14's reading is also in ai/0010 § 2.15). **Next row: 126.** **Merged:** the P3a review at be832eb9 (the name `lane/s52a` did not resolve here, so by its commit); `machinery.md` A2, A3, B6, D2, E1, E4, F and T67 were re-read and rows 5, 7 and 119 corrected. **Owed before any new row, by the coordinator's instruction:** prose-only entries in ai/0001 to ai/0013 passed earlier reviews and were wrong, so read the anchored instructions (objdump of the pinned image) for the entries here that rest on prose and decide a draw or a branch, and route what cannot be settled: **rows 25, 105, 106, 108, 110, 111, 112 have not had this check**, and batches 10 to 12 need it as they are written. Then: read [ai/0014](../findings/ai/0014-community-cross-check.md) for each row's disagreement under Open questions (Duriel's is in); the glossary; backlog entries for row 94's two tables, row 25's offset tables and row 106's scoring terms (filed by nobody yet; ADR-0031 applies to the tables); remove the "started" state of the tag counts by recounting. The `l` and `r` lines come from the `ROW` and `RROW` lines of `workspace/logs/ai/check-run-2026-11-03-ai.txt`, `check-run-2026-11-03-ai-3.txt`, `r5/check-run-2026-11-04-ai-r5.txt`, `resume-run-2026-11-04-p52c.txt` and `r5/resume-run-2026-11-04-ai-r5.txt`, already expanded in the file; state rows' own decisions (0x005E8020, 0x005E8140, 0x005E8340) are not yet counted under S10, S17, S11, S12, and need adding from those `RROW` lines. Row entry form: `aip` line, block with `[I]` and anchors, lettered bullets, the emulated `[C]` with family and controls.
- **2026-11-04 — Phase 3b (`lane/s52b`, spec-writer, second run): the AI catalogue, written whole, for review.** [monsters/ai/catalogue](../specs/monsters/ai/catalogue.md): 148 rows and 18 state rows, each once by script; none left marked to write; tags C 330 / I 496 / L 19. **The owed check, rows that rest on prose read against their anchored instructions:** row 25 corrected (the place guard, the five-wisp origin, the waits and zero entries, state 1's fall-through into a second draw, A1's argument); 105 corrected (`AiPetGuard`'s return, the idles, the "other" skill of a skill-0 pick); 106 corrected, most of it (the "five best" is a rising list with no cap of five, the pick's `& 3` walk, the pending sequence's source at `+0x2E` = 19, the second `AiPetGuard`, the target's order, `AiShadowUseSkill`); 108 corrected (the teleport's point, the wolf's reversed test, Fenris not "as the wolf"); 110 and 111 corrected (`≥ aip(5)`, the guard before the stats, classes 426 life and 427 mana, no target's idle); 112 corrected (the moves at 100, the owner-less branch, `m` from one call). Dated corrections are in [ai/0003 § 2.9](../findings/ai/0003-pool-b.md) and [ai/0006 §§ 2.7, 2.10, 2.11, 2.12](../findings/ai/0006-summons.md). T28: the catalogue's one mention is a link; machinery's T28a was read against 0x005F4BC0–0x005F4C09 and agrees. **Batches 10 to 12:** the prose-only entries (rows 131, 134, 137, 31, 32's chain, 54, 58, 81, 91, 99; states 3, 12, 13) were read against their instructions and agree: no correction filed; each entry says so. Row 134's "bit 1" is the mask 1, as the entry writes it. These checks are this lane's reading of cited anchors, for the reviewer to repeat where it matters. **Own decisions:** S10 632 and S17 the same 632, unsplit; S11 134, 68 of 260 later steps deciding on an unknown; S12 56. **Community sweep:** ai/0014's 67 claims by row under Open questions, each `[L]`, agreement raising nothing. **New backlog to the reverser, none blocking:** [row 25's offset tables](../backlog/archive/2026-11-04-spec-writer-reverser-plan-0052-row-25-offset-tables.md), [row 94's tables](../backlog/archive/2026-11-04-spec-writer-reverser-plan-0052-row-94-tables.md), [row 106's scoring terms](../backlog/archive/2026-11-04-spec-writer-reverser-plan-0052-row-106-scoring-terms.md). **Short, by name:** the catalogue sample, as the ruling leaves it; row 106's scores; state 13. Read first: R106, R108 and R25, then the correction paragraphs; R51 and R135's tables are the finding's, restated. Glossary: `aip`, AI catalogue, town chain, threat score. For review: leave the map row to the architect.
- **2026-11-04 — `lane/r71` (reverser, objdump only, no Ghidra, no game), three entries closed, for review.** [ai/0019](../findings/ai/0019-row-tables-and-scoring.md): row 106's per-`aitype` terms, targets, skips and draws, its locals and the `EType` map; row 94's `STEP` by rule and `SWEEP` listed; row 25's `A5` listed, `B5` by rule, `A` and `B` by shape only, event 12 by stats/states C1. Check [run:2026-11-04-r71-sm](../findings/ai/experiments.md#run2026-11-04-r71-sm): the pseudocode against the think's instructions, 6 000 cases, 0 mismatches, 98 of 99 controls failing (the 99th cannot). New gate survey `ai_const`. No log tests these rows (0 decisions). Corrections to catalogue R106 and ai/0006 § 2.11 in the finding's § 5; the [spec-writer's entry](../backlog/2026-11-04-reverser-spec-writer-ai-0019-row-106-94-25-readings-to.md) carries them; [the architect's](../backlog/archive/2026-11-04-reverser-architect-r71-wisp-tables-a-b-adr-0031-call.md) holds the `A`/`B` call.
- **2026-11-04 — `lane/r71` review (architect, Tier A, ADR-0031 ruling): accept with fixes, 11.** Read against objdump of the pinned image: the think's score whole (0x005EBDF8–0x005EC634), its callback, `AiStateGroupHeld`, `Use`'s first test, both jump tables and the byte map, `RNG_Range`, row 94's reads, row 25's readers and grant, `UNIT_ExpireTimedLists`, `STATLIST_Alloc`, `StatListSetEnd`, `STATLIST_LinkToUnit`. **Row 106's terms are right as filed:** every case's terms, target, skips, widths and draws, the truncating base, the `EType` map, the list's offsets and the pick; no term moved. Stock `aitype`s recounted by name: 1, 2, 3, 4, 5, 10, 11, 12, 13, 32 rows. Check re-run: the kept output's lines recur, trace `492df4f5669fd9b1`, 0 mismatches; manifest passes. `A`, `B` and all rules recomputed; `summary` prints no values; symbols new to `main`, no clash in name or address; the five corrections hold and are dated. **Fixes, in the review commit:** overclaim 2 (`RNG_Range` "executed": it is a stub on the `Seed` class the model shares, in § 1.6, the record and the docstring; "cannot fail" of a control tested upward only, where `p_hi − 1` fails 4 and `use1_held − 1` fails none, resting on its instruction). Misread 1 (the wrap paragraph's "only": case 4's `4·acc + 3` and the sign cases). Omission 6 (the `melee` word; the callback's whole gate; the stock `EType` bytes with `stun` reading nothing; row 25's reach; a listing no gate compared with the image, so `doc_missing` and `doc_mismatches` join `ai_const`; the spec-writer's entry, which left out row 143 and the Open-questions lines). Tool not kept 1 (the rotation counts, in no kept output: `rulescan`). Other 1 (the template line left in both new entries). **Ruling 1, ADR-0031: `A` and `B` listed, and this is the architect's reading, not the owner's.** The bounded search found no rule (`tools/ai_const_survey.py rulescan`; the best forms give 11 of 28 rows, and "the next wisp's point, except" is a description by cases). The ADR's test is "only where no exact rule gives it", for a constant a reimplementation needs, and these two fail without it: row 25's `A` gates a draw. Its words on size don't reach them: each is 56 values, smaller than all four tables it keeps (64, 64, 75, 75; the owner kept 278 for one family of planners), its Consequences say a later lane "has a test to apply, not a size to argue about", and "112 for one function" is a measure it doesn't use. The lane's other option, the reimplementer reads them from their own image, is the alternative the ADR rejected by name. So it needs no stretch, the owner need not be asked, **and no squash is needed: `SWEEP` stays, and so do `A5`, `A`, `B`.** A ceiling on a function's total would be a new rule, and that one is the owner's. They are told in the report before any push, since a pushed listing can't be withdrawn. **Which stock class uses row 25:** eight records, classes 118–121, 639–641 and 733. Spawn columns name 118, 120 and 639–641, and one superunique has class 120; 119, 121 and 733 are named by neither. So the row is reachable on stock data. **Ruling 2, the evidence: `[I]` is right, and the check is the right tool for what it claims.** It is not ADR-0015's case: condition (1) forbids a stub, ADR-0021 rejected a synthesised return by name, these cases run on past every call, and the emulator named is Ghidra's. It guards the transcription and raises nothing. The same interpreter over a kept batch's logged returns (ADR-0004, `tools/ai_resume.py`) is the route to `[C]`. 98 of 99 fail; `p_hi + 1` cannot, as a chance of 101 is a chance of 100 against `Range(100)`. All 6 one-way branches are named, and each reason holds at its instruction: 0x005EBADC and 0x005EBF5F a null record no synthetic table gives, 0x005EBB4B dead after the `sub`, 0x005EC550 dead as `k` ≥ 1, 0x005EC5CA `t` non-zero since `Idle(25)`, 0x005EC612 the stub's. **Ruling 3, the logs:** 0 over 160 logs recounted, for the 13 classes too, row 2's 1 530 showing the logger live; the batch holds 64 of the 148 rows. That is coverage and says nothing about reach; the finding now says so, with the data. **Event 12's statement is true:** the list is flag 2, its end at `+0x18`, linked on the `+0x3C` chain, so C1's walk frees it at that frame. **Promoted:** nothing here; ai/0019 is reviewed, and its readings reach the catalogue by [the spec-writer's entry](../backlog/2026-11-04-reverser-spec-writer-ai-0019-row-106-94-25-readings-to.md), rewritten so that a spec lane can work from it alone. `ai_const` was shown to fail on a changed baseline key and on one altered listed value in a copy. No ledger row here; verdict and counts above are for the orchestrator.
