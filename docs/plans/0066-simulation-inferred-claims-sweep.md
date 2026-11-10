# 0066 — Inferred-claims sweep 2: the simulation and game-rules specs

> **Status:** approved (2026-11-10, by the owner, as recommended: question 1 (b), plan 0038 closed; question 2, 20 claims per session; not started: the owner starts it)
> **Created:** 2026-11-10
> **Owner skill(s):** architect, reverser, spec-writer
> **Related ADRs:** 0004-boundary-oracles-in-reproduction, 0013-forced-path-runs-cell-level, 0014-scope-game-simulation, 0015-emulated-reproduction, 0021-observed-boundaries-in-emulation, 0022-scope-server-frame, 0023-review-tiers-and-gate-first-fixes, 0028-case-and-process-in-experiment-records

## TL;DR

**Question:** which `[I]` claims in the simulation and game-rules specs can now be raised to `[C]` by one more harness
run, a new check over kept logs, a static second source or an emulated reproduction? Which stay `[I]`, and why?
[Plan 0038](done/0038-inferred-claims-sweep.md) asked this for the creation specs. ADR-0022 named this sweep as its
"recommended companion plan" and deferred it until the server frame was composed, because most simulation `[I]`s are
draw-order claims that the frame order decides. `sim/frame` is now reviewed (plan 0055), so the deferral no longer
holds. When this plan is done, `docs/plans/0066-inventory/` classifies every `[I]` of the specs in scope, the cheap
classes are raised, and the specs are re-tagged.

## Context

- **Scope: 2 626 `[I]`** in the specs' front matter on 2026-11-10 (`main` at `95a9ea30`):

  | Group | Files | `I` |
  |---|---|---|
  | monsters/ai | 3 | 690 |
  | skills | 4 | 428 |
  | quests | 3 | 414 |
  | items/economy, use, inventory | 3 | 254 |
  | combat | 5 | 203 |
  | anim | 3 | 191 |
  | sim/frame | 1 | 127 |
  | path | 2 | 116 |
  | stats | 3 | 99 |
  | drlg/lifecycle | 1 | 78 |
  | player/party | 1 | 26 |

  `net/messages` is out of scope (not yet reviewed; plan 0061). The creation specs stay plan 0038's.
- **Method:** plan 0038's, unchanged: its classes (a-logs, a-run, b, c, c-emu, d-none, d-edit, d-sim, d-2c, d-owner),
  its inventory layout and its batch rules. Two things are new since 0038 started:
  - the frame corpus (`tools/frame_corpus.py`) and the golden traces make (a-logs) re-checks cheaper;
  - the runner library (`tools/harness_runner.py`) runs several cases per launch (ADR-0028).
- **Relation to plan 0038.** 0038 is approved and held, with harness batches and Phase 3 clusters still open. Running
  both together would double the harness load. Owner question 1 below decides the order.
- **Size control.** 2 626 is 1.7 times 0038's starting count. The plan raises only the classes that need no new
  session (a-logs, c, c-emu) by default. Harness batches (a-run) run only for clusters where one session raises at
  least 20 claims, a threshold the Phase 0 review may move.

## Phases

### Phase 0 — Inventory
- **Owner skill:** architect
- **What:** classify every `[I]` of the specs in scope, one inventory file per spec in `docs/plans/0066-inventory/`.
  Each row gives the statement's line, its class, the route to `[C]` (the log, the run, the second source, the emulation
  boundary) or the reason it stays `[I]`, and its batch id. The totals table goes in the inventory's README. Clusters by
  group may run as parallel architect lanes, each with no slot.
- **Done when:** every `[I]` of the scope has one row. The totals per spec and class match the specs' front matter
  (gate W7 on the totals). The batch list names each static and harness batch with its claims and its estimated
  sessions. Review: Tier A (the owner's go for Phases 1 and 2 comes with it).

### Phase 1 — Static batches
- **Owner skill:** reverser (static; no slot)
- **What:** raise the (a-logs), (c) and (c-emu) rows batch by batch:
  - (a-logs): a new check over kept logs, recorded as a dated addendum to the run;
  - (c): a static second source;
  - (c-emu): an emulated reproduction under ADR-0015, ADR-0021 and ADR-0029.
- **Outputs:** findings addenda, `re/symbols.csv`, checks in `tools/`; the inventory rows updated per batch.
- **Done when:** every row of these classes is raised or moved to another class with a reason, each batch reviewed.
  Review: Tier B per batch (the audit rule applies).

### Phase 2 — Harness batches
- **Owner skill:** reverser (harness; at most two slots, never slot 0)
- **What:** the (a-run) and (b) batches that pass the size threshold (owner question 3), grouped by recipe and logger as 0038 Phase 2 did, through
  the runner library.
- **Outputs:** one `run:<date>-sweep2-<batch>` record per batch; findings addenda.
- **Done when:** each scheduled batch has its run with 0 mismatches or named contradictions. The rows below the
  threshold are recorded as (a-run, deferred). Review: Tier B per batch.

### Phase 3 — Re-tag
- **Owner skill:** spec-writer
- **What:** re-tag the specs cluster by cluster as their batches are accepted, update the front-matter counts and the
  research-map rows, and route any contradiction to its spec's text.
- **Done when:** every raised row is re-tagged, `python3 -I tools/gate.py --full` is green, and the inventory's final
  totals are recorded. Review: Tier A per cluster; the last review closes the plan.

## Open questions

- **Owner question 1, order with 0038.** (a) Finish 0038 first, then this plan. (b) Close 0038 where it stands (its
  remaining rows recorded as deferred) and run this plan. (c) Run both, one harness slot each. The architect recommends
  (b): the simulation `[I]`s are now the larger and less examined set, and 0038's open rows are mostly harness rows it
  has already ranked.
- **Owner question 2, threshold.** 20 claims per session for a harness batch, or another number.
- Whether `monsters/ai` (690) gets its own sub-plan. Its catalogue rows are many small, similar claims, and an
  emulation route may cover most of them in one batch. Decided at the Phase 0 review: not for the static part (S1a to
  S1o fit Phase 1); the harness part follows owner question 3.
- **Owner question 3, the threshold revisited (Phase 0 review).** No harness batch reaches 20 claims per session: the 31
  batches hold 705 statements over about 256 estimated sessions (0.2 to 11 per session, 2.8 on average). At the ledger
  means (reverser-harness about 342k tokens per lane, a Tier B check about 83k), Phase 2 in full is about 31 lanes, about
  13M tokens, roughly 19k per claim against about 10k per claim for Phase 1 (36 static lanes and their checks). The options:
  (a) keep 20 per session: Phase 2 does not run, the 705 rows are recorded as deferred at Phase 1's close;
  (b) lower it to 5 per session: H1b, H1d, H1e and H1h run (137 statements, about 17 sessions, 4 lanes, about 1.7M tokens);
  (c) count runner launches (ADR-0028) instead of sessions, which only the monsters/ai "bestiary tour" has estimated
  (H1a to H1d, H1g and H1h, about 214 statements in about 12 launches, about 3 lanes, about 1.3M tokens), the tour run
  as a monsters/ai harness sub-plan after Phase 1's S1 batches build its checker;
  (d) run all of Phase 2 (about 13M tokens).
  The architect recommends (c): it takes the one cluster where many statements share a recipe, at about Phase 1's cost
  per claim, and it waits for the S1b checker the tour needs; the other 491 rows stay deferred with their routes kept.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

### 2026-11-10 — Phase 0, inventory (architect, `lane/n66i`)

- **Done.** [`0066-inventory/`](0066-inventory/README.md) has one file per in-scope spec (29) and a README. Every one of
  the 2 626 `[I]` has a row (2 618 spec lines; rows carry the line number and a count), and each file's *Count* sums to
  its spec's front matter at `b5999f5e`. None of the 29 specs changed since `95a9ea30`. The row skeletons came from a
  script; the classes, routes and batches came from the architect (player/party, the assembly) and eight helper copies,
  one per cluster.
- **Result:** Phase 1 static 1 605 statements (a-logs 722, c 388, c-emu 495) in 36 batches; Phase 2 harness 699 (a-run
  346, b 353) in 31 batches; blocked 322 (d-2c 59, d-owner 67, d-edit 23, d-none 173).
- **Surprise: the threshold empties Phase 2.** No harness batch reaches 20 claims per session (0.2 to 11, about 2.7 on
  average over about 256 estimated sessions). The inventory README § 2 gives the review three options: keep it (Phase 2
  does not run), count runner launches instead of sessions (a monsters/ai "bestiary tour" estimated at about 214
  statements in 12 launches), or a monsters/ai harness sub-plan (this plan's open question).
- **Judgment calls recorded in the inventory README § Conventions and § 5:** this plan's Phase 1 bullet reads "(b): a
  static second source", but 0038's (b) is a session with a new piece and (c) is the static source; the inventory keeps
  0038's meanings (Phase 1 = a-logs, c, c-emu; Phase 2 = a-run, b), and the review is asked to correct the bullet. No
  value tier (batches ordered by claims per session). Guards and unreached branches routed to c-emu where the read set
  looks declarable; OS-clock frame functions as c-emu pending a ruling.
- **Next:** the Tier A review of Phase 0, with the owner's go for Phases 1 and 2. Phase 1 and Phase 2 have not started.

### 2026-11-10 — Phase 0 review (architect, Tier A): accept with fixes

- **Done when, checked by script:** every `[I]` of the 29 specs has one row (2 626; each file's rows cover exactly its
  spec's `[I]` lines and sum to its front matter); the README totals equal the files' sums; every batch's *Stmts* equals
  its rows; no row sits in a batch of the other phase. The batch list now gives *Sessions* 0 for the static batches.
- **Sample:** 50 rows in 21 specs (22 a-logs, 11 c, 11 c-emu, 6 a-run, b and d-none), with the kept logs opened for the
  22 a-logs rows. Errors: a-logs 1 of 22 wrong (5 %) and 2 partial; c 0 of 11; c-emu 0 of 11 at row level, but two
  batch-level method errors outside the random draw (R2 and R3 below); a-run, b, d 0 of 6.
- **Rulings** (inventory README § 5 *Review rulings*): R1 Phase 1 = a-logs, c, c-emu and Phase 2 = a-run, b, the plan
  text corrected; R2 no declared callee return in an emulation (ADR-0021 § Alternatives), S2be and S5fe restated;
  R3 the OS clock is not c-emu (ADR-0029), sim/frame 3, 13, 17, 19, 54 to (b) in H7b; R4 the two quoted tags stay
  d-none until Phase 3 rewords them; R5 S1n → S1ne, S5f → S5fe; R6 the log check; R7 no monsters/ai sub-plan for the
  static part.
- **Moves:** progression 172 a-logs → a-run (H3a); sim/frame 3, 13, 17, 19, 54 c-emu → b (H7b). Totals now a-logs
  721, a-run 347, b 358, c 388, c-emu 490, d 322; Phase 1 1 599 statements in 36 batches, Phase 2 705 in 31.
- **Owner question 3** (the threshold) is open above, with the architect's recommendation (c).
- **Next:** Phase 1 can start on the owner's go, S batches in any order (S1a to S1o before a bestiary sub-plan, if the
  owner takes (c)). Fixes: misread 4, omission 3, other 2.
