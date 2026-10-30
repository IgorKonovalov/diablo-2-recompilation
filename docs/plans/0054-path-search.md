# 0054 — Path search: the planner behind every path request, its points, its draws and its use of the collision grid (ADR-0014 phase 5, second part)

> **Status:** approved (owner, 2026-10-30: "approve as recommended", all eight scoping questions answered as recommended); drafted 2026-10-30 (architect, `lane/plans54`)
> **Created:** 2026-10-30
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0011-harness-slots, 0014-scope-game-simulation, 0015-emulated-reproduction, 0016-pipelined-simulation-phases, 0021-observed-boundaries-in-emulation, 0022-scope-server-frame

## TL;DR

**Question:** given a path request (the unit, its path type `0..16`, the type's flags, the target unit or point, the
stop distance, the byte at path `+0x90`), what does `PathPlan` compute: which planner runs, which cells of the
collision grid it reads and under which mask, which points it writes into the path, what it returns, which fallback
the caller then takes, and which draws it makes on which seed? Plan [0052](0052-monster-ai.md) stops at the AI's
**request** and treats the search behind it as a boundary (owner, 2026-10-27, its question 1); this plan is that
boundary's own plan, drafted on unpause as 0052's P1.1 review ruled. When it is done:
- `docs/tables/PathTypes.md` lists the 17 slots of `g_PathPlanFuncs` (`0x006EB6D8`) and of the flags table
  (`0x006EB690`) read from the pinned image, and the excel columns that feed a request (unit size, missile and skill
  columns);
- `docs/findings/path/` names `PathPlan`, every planner a slot reaches and the search's internals, with a **request
  register**: each of `PathPlan`'s 68 call sites with its owner (AI, mode machine, player move, missile, skill, object)
  and the types it passes;
- the planners are reproduced in emulation (ADR-0015, ADR-0021) over declared collision images built from
  `tools/collision.py`'s predicted grids, and per event in the harness;
- **the value oracle "the path planner's points"** of [skills/README](../specs/skills/README.md) and
  [skills/missiles](../specs/skills/missiles.md) is retired, and missiles H1's measured but unexplained **20 and 38
  steps** (Firestorm sub-missiles and class-195 missiles, 450 of 450 creations) are walked draw by draw;
- `docs/specs/path/search.md` (research-map row `path/search`) is reviewed.

## Context

- **The owner's ruling.** Plan 0052's question 1 (answered 2026-10-27): pathing gets its own plan, 0052 stops at the
  request. The P1.1 review (`lane/r52`) deferred this draft to the unpause because the AI's path types draw nothing
  and so gate nothing in 0052. No scope ADR is needed: ADR-0014 puts pathing in phase (5).
- **What is known** ([ai/0001 § 8](../findings/ai/0001-machinery.md#8-the-path-request), all `[I]`):
  - the type → planner and flags table for all 17 types: `PathPlanSearch` (0, 16), `PathPlanType1` (1),
    `PathPlanGreedy` (2, 5, 6, 13), `PathPlanGreedyNear` (7), `PathPlanKnockback` (8), `PathPlanOnePoint` (9),
    `PathPlanType15` (15), three unnamed slots (3, 11, 12) and the straight planner `PathPlanStraight` for 4, 10 and
    14 (to unit, random walk `PathPlanRandomWalk`, spiral `PathPlanSpiral`);
  - **the draws:** an RNG call graph over `PathPlan` and the seven distinct slot functions finds four RNG functions:
    the random walk (type 10, unit seed) and three under `PathSearchRun`, which step a seed only for type 16, whose two
    setters have no reference in the image. The slots of types 3, 11 and 12 were not roots: their draws are unfollowed;
  - the AI's types are 1, 2, 5, 6, 7, 13 and 15 (plus 0 after a get-hit and 8 for knockback from the mode machine);
    `MonMovePlan` falls back to type 15 when 2, 7, 9 or 13 leaves no point; `PathPlan` runs only after
    `PathTargetNotTown` (drlg/lifecycle H5);
  - the search context is large (a seed at `ctx+0x36FD4`), which bears on the emulation image (P1.1).
- **Who waits on it.**
  - [skills/missiles](../specs/skills/missiles.md) H1 and the value-oracle rows of skills/README and skills/missiles:
    path types 7 and 10 in missile creation and do functions; the 20 or 38 steps on `Init(path x + arg)` are "not read:
    the path planner is a value oracle".
  - [anim/movement](../specs/anim/movement.md) G1 (reviewed, plan 0050): the step, the snap and the collision walk
    draw nothing; "the replan and the target revalidation reach the planner, whose draws (the random-walk type among
    them) are phase (5)'s". The per-frame step stays anim/movement's.
  - Plan 0052's P2 checks, at every plan exit from an AI site, that the unit seed is unchanged; a changed seed is a
    mismatch **routed to this plan** (P1.1 review ruling 3). Its H5 (town-follow) leaves "whether a stock town's
    geometry admits such a route" to this plan.
  - Plan 0046's catalogue entries that plan a path (movement skills, missiles with a path type) keep the planner as a
    boundary until this plan's spec is reviewed; ADR-0022's frame plan ([0055](0055-server-frame.md)) does the same.
- **Dependencies met:** [drlg/collision](../specs/drlg/collision.md) reviewed (the grid, `PATH_PatternFromSize`
  `[C]`, `PATH_MonTestMask`), and `tools/collision.py` predicts room grids; 0052·P1.1 reviewed (the request kinds);
  0050·P3 reviewed (anim/movement, the consumer of the points). ADR-0016's harness gate (the previous phase's spec
  reviewed) is met by 0050·P3; this plan's own P1 reviews gate its P2.
- **Not a dependency:** plan 0052's catalogue and P3, plan 0046, plan 0055. This plan gates none of them; each treats
  an unspecified planner call as a boundary (ADR-0004, ADR-0021).
- **Research map row:** `path/search` (Simulation band), added with this draft. Wiki owner: Phase 4.

## Phases

Data first, then code, then spec.

### Phase 0 — The path types and the request columns
- **Owner skill:** archivist (no Ghidra, no slot)
- **What:** the 17 rows of `g_PathPlanFuncs` and the flags table read from the pinned image (planner address, flags
  word, as MonAI.md read `g_MonAiTable`); the excel columns that a request reads, each linked to its table doc: the unit
  size columns that `PATH_PatternFromSize` takes (MonStats2, the player and object equivalents), the missile columns
  that choose a path type or its parameter, and the skill columns of the movement skills; the stock rows that reach
  types 7 and 10 through a missile (the H1 cases).
- **Outputs:** `docs/tables/PathTypes.md`; the table docs linked; `tools/path_survey.py` (gate survey `path`).
- **Done when:** all 17 slots listed with address and flags, matching the survey; meanings `[L]` until P1 anchors them;
  the gate is green.

### Phase 1 — The planners, in three batches
- **Owner skill:** reverser (static; one Ghidra per batch, batches one at a time per lane, two lanes at most)
- **What and done when:** each batch names its functions with addresses at `[I]` or better, lists its draws per seed,
  and emulates (ADR-0015, ADR-0021) every planner it reads over declared images, with negative and site controls as in
  run:2026-10-27-ai-emu; a family that cannot be emulated says why.
  - **P1.1 `PathPlan` and the request register.** `PathPlan`'s entry (its checks, `PathTargetNotTown`, the slot call,
    the flags' uses, its return), the path record's fields a planner reads and writes (the point list and its capacity,
    `+0x90`, `+0x93`, `+0x94`, the target), `PathPlanToUnit`, `SUnitPathCreate`, `PATH_DynamicCreate`, and the
    consumers of the result as far as anim/movement's reviewed step (`PathAimNextPoint`, `PathReplan`); **the request
    register**: all 68 call sites of `PathPlan` by owner and type; **the emulation image**: how a declared image is
    built from predicted room grids (`tools/collision.py`) and the unit marks (`PATH_SetMarkMask`), and how large the
    search context is; the log design for Phase 2 (one line per plan: entry, the points, the return, entry and exit
    seed; the volume estimate).
  - **P1.2 the search.** `PathPlanSearch` and `PathSearchRun` (types 0 and 16): the node store in the context, the
    cost and the heuristic, the neighbour order and the tie-break, the limits (node count, distance), how the found
    route is reduced to the path's points, and `PathSearchDirDraw` and the other draws under type 16 (unreachable, read
    because they share the code). `PathPlanType1` and `PathPlanType15` if P1.1 finds they call the search.
  - **P1.3 the short planners.** `PathPlanGreedy`, `PathPlanGreedyNear` (its `dx² + dy² < 325` switch to type 1),
    `PathPlanKnockback`, `PathPlanOnePoint`, the three unnamed slots (3, 11, 12, with their draws now followed),
    `PathPlanStraight` with its three modes, `PathPlanSpiral` and `PathPlanRandomWalk`; **missiles H1**: which of the
    callback's three path calls steps the seed, and why 20 for a Firestorm sub-missile and 38 for class 195, emulated.
- The P1.1 review rules the batch cut of P1.2 and P1.3 (it may merge or split them on the register), the emulation
  image and the Phase 2 floors.

### Phase 1b — Community cross-check
- **Owner skill:** reverser (no Ghidra)
- **What:** register community descriptions of pathing (monsters stuck on corners, the pathing of charge-like and
  teleport skills, the random-walk missiles) under the leads policy, and compare them blind with P1's readings; a
  verdict per compared claim.
- **Done when:** each compared claim has a verdict; every `contradicted` claim reachable on stock data is a required
  case of Phase 2; agreement promotes nothing. Optional if P1.1 finds no registered source with a comparable claim.

### Phase 2 — Per-event reproduction
- **Owner skill:** reverser (harness; **one slot** from 1–2, given in the prompt)
- **Starts when:** P1.1 and the batch holding each type's planner are reviewed.
- **What:** `tools/path.py` (model and `check`), `tools/gdb/path.gdb` and its handler. One event is one `PathPlan`
  call: inputs the unit, the request fields, the rooms near the unit (by room id, their grids predicted) and the unit
  marks inside the search's bounds (as P1.1 designs them); outputs the points, the return and the exit seed. Filtered
  to the logged character's rooms and capped per type and per session (ADR-0014 § Log volume).
- **Done when** (estimates, confirmed at the P1.1 review): `run:YYYY-MM-DD-path` reproduces with **0 mismatches** over
  - 2 000 plans in all, at least 100 per type that a stock caller reaches, over player moves, monster AI requests and
    missile paths, in at least three acts (a town, an outdoor level and a maze level);
  - **missiles H1:** the 450 creations of run:2026-10-25-skills re-walked from the kept logs with the planner's draws
    modelled (the 442 Firestorm and 8 class-195 cases), and at least 50 new type-10 plans with their draws chained to
    the next event on the missile seed;
  - **the AI's no-draw prediction:** for each AI type, at least 50 plan exits with the unit seed unchanged (shared with
    0052·P2's check where its logs already hold them);
  - the replans of anim/movement G1 (at least 50, the target revalidation among them);
  - the Phase 1b cases, and drlg/lifecycle H5's town-follow case if a stock town admits the route (else a named
    shortfall with the geometry that excludes it).

  Rare types may fall short, named in the record with their counts; their claims stay `[I]` or at their emulated `[C]`.

### Phase 3 — Spec: the path search
- **Owner skill:** spec-writer
- **What:** `docs/specs/path/README.md` (the request, the types, the dispatch, the draws per type) and
  `docs/specs/path/search.md` (each planner as pseudocode with its cell reads and draw order); skills/README and
  skills/missiles (the value-oracle rows retired, H1 rewritten), anim/movement G1, monsters/ai's request (if P3a has
  landed) and drlg/collision cross-linked.
- **Done when:** the spec follows the template; every statement tagged; every planner a stock caller reaches as
  pseudocode; the architect's review passes. Specs edited by two plans merge one at a time, the earlier plan's first.

### Phase 4 — Wiki page: pathing
- **Owner skill:** spec-writer
- **What:** `docs/wiki/pathing.md` (ADR-0012) over the reviewed spec; the monsters, skills and movement pages linked.
- **Done when:** `based_on` dates current (gate W4); no claim of its own; the architect's review passes.

## Scoping questions for the owner

The owner answers these with the approval. Each carries the architect's recommendation; the phases above are drafted on
the recommendations, and an answer that differs changes the phase it names.

1. **Coverage: every planner slot, or only the types a stock caller reaches?** *Recommendation: every slot,* as the
   owner chose for the AI table (0052 question 8). The 17 slots map to about twelve functions, the unreached ones
   (16 above all) share code with reached ones, and reading them costs a fraction of a batch. A slot no caller reaches
   is specified from the code (`[I]`) and named as unreached.
2. **Callers: monster AI only, or every server-side request?** *Recommendation: every server-side caller* (player
   moves, the mode machine, missiles, skills, objects, the AI), through P1.1's register. The request logic stays its own
   plan's (0052 for the AI, 0046 for a catalogue function); the player's move request, which no other plan owns, is
   this plan's.
3. **Evidence: emulation first?** *Recommendation: yes.* A planner is a pure function of the grid, the marks and the
   request, the case ADR-0015 was written for; P1's emulation over predicted grids gives `[C]` per planner family, and
   Phase 2's one short slot ties the predicted grids and marks to the live ones. *If harness only:* the log must carry
   the cells each search reads, and Phase 2 grows to two or three lane runs.
4. **Other units on the grid.** *Recommendation: in.* The unit marks change every frame and decide many routes; P1.1
   designs how they are declared (emulation) and logged (harness). If they cannot be logged within ADR-0014's volume
   rules, the record names the plans whose marks were a logged snapshot instead of a model.
5. **The client's own planner.** *Recommendation: out* (ADR-0014 § Time, ADR-0022: no client prediction). Where the
   client calls the same functions, the spec says so from the static reading and claims nothing more.
6. **Row and place.** *Recommendation:* row `path/search`, spec under `docs/specs/path/`; the request stays in
   monsters/ai (and in each caller's spec), the per-frame step in anim/movement.
7. **Harness.** *Recommendation: one slot,* one lane run (two at most). When 0052·P2 runs at the same time, its plan-exit
   line may carry the points, so both plans read the same sessions.
8. **Run order.** *Recommendation:* this plan's P0 after plan 0055's P0 in the archivist's queue; its P1 batches in static
   lane B after plan 0055's P1 and before 0052's later catalogue batches (lane A keeps 0052's catalogue, the tier
   batches first); P2 when a slot is free. Nothing waits on this plan, so it fills gaps (the joint question is 0055's
   question 7).

## Resources and limits

- **Static:** at most **two static lanes** and **two headless Ghidra** at once across all plans, `-Xmx3G` each. P1 holds
  one Ghidra per batch, and its emulation runs in that copy; P0 and P1b need none.
- **Emulation images:** the search context and a few rooms' grids per case; families run in batches small enough for
  `-Xmx3G` (P1.1 states the case size).
- **Harness:** at most **two harness lanes** at once, on **slots 1 and 2** (slot 0 is the owner's); Phase 2 takes one.
- **Replays:** the H1 re-walk and any heavy replay under `systemd-run --user --scope -p MemoryMax=4G`.
- **Rotation:** lanes past about 4 h checkpoint, write a resume note and stop; a fresh lane resumes on the same branch.
- **Estimate** (not measured): P0 one lane run; P1 three to four; P1b one (optional); P2 one to two; P3 one; P4 one.

## Open questions

- **The unit marks' volume.** If the marks inside a search's bounds are too many to log per plan, Phase 2 may need the
  injected logger that plan 0052 question 3 and ADR-0022 hold in reserve; P1.1's estimate decides whether to raise it.
- **The three unfollowed slots** (3, 11, 12): whether any draws is P1.3's first item; if one does and a stock caller
  reaches it, Phase 2 adds it to its chained-draw floor.
- **The type-16 setters** (no reference in the image): a wine run that breaks on them would settle whether anything
  reaches them (ai/0001 *Open questions*); it costs one break line in Phase 2's sessions.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-30 — Drafted (architect, `lane/plans54`).** Status `draft`; drafted on unpause as plan 0052's P1.1 review
  ruled; eight scoping questions for the owner.
- **2026-10-30 — Approved (owner; recorded by the architect, `lane/appr`).** "Approve as recommended": all eight
  scoping questions answered as recommended (every planner slot; every server-side caller; emulation first; unit marks
  in; the client's planner out; row `path/search` under `docs/specs/path/`; one harness slot; run order as question 8).
  Run order ([plans README](README.md#run-order-set-2026-10-25-plans-00380052)): P0 in the archivist's queue after
  0055·P0; P1 in static lane B after 0055·P1, before 0052's later catalogue batches; P2 when a slot is free. Status
  `approved`.
