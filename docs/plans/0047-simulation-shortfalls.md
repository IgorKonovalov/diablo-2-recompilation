# 0047 — Simulation shortfalls: the named remainders of the combat, stats and travel runs

> **Status:** approved 2026-10-20 (owner)
> **Created:** 2026-10-20
> **Owner skill(s):** reverser, spec-writer
> **Related ADRs:** 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0011-harness-slots, 0013-forced-path-runs-cell-level, 0014-scope-game-simulation, 0017-scope-quests-travel-economy

## TL;DR

**Question:** do the branches that the reviewed combat, stats and travel specs read from the code, but whose runs fell
short of their minimums, behave as read? This is not a new subsystem: it reaches the **named shortfalls** of
run:2026-10-16-combat, run:2026-10-17-stats and plan 0042's travel runs with sessions built for them, on the existing
loggers and checkers, and re-tags the specs. When it is done, each shortfall below is reproduced to its minimum, or
named again with the reason it cannot be staged on stock data.

## Context

- **Why now.** The combat and stats specs are reviewed and their loggers and checkers are kept
  (`tools/combat.py`, `tools/gdb/combat.gdb`, `tools/stats.py`, `tools/gdb/stats.gdb`). Each shortfall is a missing
  *case*, not a missing reading: one harness slot closes them while plan 0045 is in its static phases, and the
  checkers' outstanding tool items land first.
- **The shortfalls**, as the specs name them:
  - [combat § Open questions](../specs/combat/README.md) (run:2026-10-16-combat, 40 655 events): crushing blow on a
    champion (0 labelled; the community "1/8 on champions" lead is contradicted in
    [combat/0001](../findings/combat/0001-formulas.md)); the resistance cap for cold (27), lightning (17), magic (0);
    magic immunity (0); the negative absorbed amount (4); evade, weapon block, dodge, avoid (0); freeze and flat
    absorb (0); the negative total that leaves life unchanged (25, under the floor of about 30); the mode-2 (walking)
    exception of the block `÷ 3` (no walking player attacked). **Conversion and pierce** are skill and missile
    effects: they move to plan [0045](0045-skills-missiles-machinery.md) Phase 2, not here.
  - [stats/states § Open questions](../specs/stats/states.md) (run:2026-10-17-stats): shrines and wells (12 operates
    against 50: the combat and stamina shrines, the re-arm, a cure by a well); an aura state's end (9 on and off
    events against 50); a different-state `group` clear; the 256 floor; open wounds on the player; the curse
    resistance cut and `attract`. The research map adds the expiries (123 of 300).
  - Plan [0042](0042-quests-travel.md) Phase 2 part 3 (run:2026-10-19-quests3, accepted with fixes 2026-10-20 at the
    `lane/p42r` review, its shortfalls final): **waypoint activation from mode 0** (0 of 20; the walk never reached an unvisited field
    waypoint, and field waypoints were first logged in mode 1 or 2 after a waypoint arrival), with the `Sync` 0
    object-seed draw. This plan takes it only **after 0042 closes**, and only if that close leaves it a shortfall.
- **The backlog it absorbs:**
  `2026-10-17-architect-reverser-stats-shrine-well-and-aura-end-addendum.md` (the stats addendum),
  `2026-10-17-architect-reverser-stats-checker-chaining-and-tests.md` (tool items for `tools/stats.py`, no game),
  `2026-10-17-architect-reverser-plan-0037-resume-lane-review-follow.md` ((a) the *Fleshripper* log copy into
  `workspace/logs/combat/` with a manifest hash, which plan 0045's oracle replacement needs; (b) the ≤ 0 counter).
- **Not here:** the event-9 handler and the state-52 call (read by plan 0045 Phase 1); objects' trap fires of types
  5, 7, 8 and 9 and the `fire` count (plan 0038's H5b and H5d batches, which load the objects logger); two-client
  cases (plan 0044).

## Phases

### Phase 1 — Tools and staging
- **Owner skill:** reverser
- **What:** land the checker items, copy the set-aside log, and write the session recipes.
- **Outputs:** `tools/stats.py` with the chaining and test items of the backlog entry and its tests; the *Fleshripper*
  log under `workspace/logs/combat/` with its manifest; `tools/combat_sessions.py` and `tools/stats_sessions.py`
  sessions for the cases below, with tool-built saves (stock items, ADR-0013 § Neutral) where a stat is needed
  (cold, lightning and magic resistances at the cap, a magic-immune target, dodge, avoid and evade on an Amazon, a
  weapon-blocking Assassin or a shield-less two-weapon character, a freeze item, flat absorb items); for the
  waypoint case (if it applies), a static reading of how `InitFn` 17 creates a waypoint in mode 0 and a route a
  fresh character can walk.
- **Done when:** the stats checker's tests pass (`python3 -I tools/test_stats.py` or its successor) and its chaining
  report matches the 18 kept logs; the log copy is hashed in the manifest; every case below has a session or a written
  reason it cannot be staged; the architect's review accepts the case list.

### Phase 2 — The runs
- **Owner skill:** reverser (agent-driven; **one slot**, given in the prompt)
- **What:** run the sessions on the existing loggers and checkers.
- **Done when:** `run:YYYY-MM-DD-shortfalls` reproduces with **0 mismatches** under `tools/combat.py` and
  `tools/stats.py`, and reaches, each to **30** unless stated or named again as a shortfall with its count and reason:
  - combat: crushing blow on champions (Nightmare or Hell); the resistance caps for cold, lightning and magic; magic
    immunity; the negative absorbed amount; evade, weapon block, dodge and avoid; freeze; flat absorb; the negative
    total that leaves life unchanged; a walking player's block;
  - stats: 50 shrine or well operates over the combat and stamina shrines, the re-arm and a well's cure; 50 aura on
    and off events; 300 expiries in total with the kept run; 20 different-state `group` clears; open wounds on the
    player; the curse resistance cut;
  - travel (after 0042 closes, if still short): 20 waypoint activations from mode 0, with the object-seed draw
    chained (ADR-0014).

### Phase 3 — Re-tag
- **Owner skill:** spec-writer
- **What:** re-tag combat, stats/states and (if run) quests/travel from the run; narrow their open questions.
- **Done when:** each raised statement cites the run; the shortfall bullets are rewritten with the new counts; the
  wiki pages' `based_on` dates are refreshed if a page states a changed count; the gate is green; the architect's
  review passes.

## Resources and limits

- **Static:** Phase 1 needs no Ghidra for the tools; the waypoint reading takes a static lane for under an hour.
- **Harness:** Phase 2 takes **one slot from 1–2**; at most two games at once across all plans; not while plan 0045·P2
  or plan 0044·P2 holds both slots.
- **Character risk.** A death ends a session (ADR-0003): Hell champion sessions use the harness-play survival rules.
- **Rotation:** past about 4 h the lane checkpoints and a fresh lane resumes.
- **Estimate** (an estimate): one Phase 1 lane, one or two Phase 2 lane runs.

## Open questions

- **Magic cap and immunity.** Whether a stock monster or item set reaches the magic-resistance cap without a skill
  (phase 3) is part of Phase 1's case list.
- **Walking player's block.** It needs a player hit while in mode 2; the pilot may not be able to hold that mode
  under attack, in which case it stays `[I]`.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-20 — Drafted (architect, `lane/plans45`).** Status `proposed`.
- **2026-10-20 — Approved (owner, via the orchestrator).** Plans 0045–0049 and ADR-0020 approved as proposed; the run
  order of the [plans index](README.md#run-order-unattended-queue-set-2026-10-20-plans-00380049) is the current queue.
