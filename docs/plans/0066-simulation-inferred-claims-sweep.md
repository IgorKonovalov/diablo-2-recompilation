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
  session (a-logs, b, c-emu) by default. Harness batches (a-run) run only for clusters where one session raises at
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
- **What:** raise the (a-logs), (b) and (c-emu) rows batch by batch:
  - (a-logs): a new check over kept logs, recorded as a dated addendum to the run;
  - (b): a static second source;
  - (c-emu): an emulated reproduction under ADR-0015, ADR-0021 and ADR-0029.
- **Outputs:** findings addenda, `re/symbols.csv`, checks in `tools/`; the inventory rows updated per batch.
- **Done when:** every row of these classes is raised or moved to another class with a reason, each batch reviewed.
  Review: Tier B per batch (the audit rule applies).

### Phase 2 — Harness batches
- **Owner skill:** reverser (harness; at most two slots, never slot 0)
- **What:** the (a-run) batches that pass the size threshold, grouped by recipe and logger as 0038 Phase 2 did, through
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
  emulation route may cover most of them in one batch. Decided at the Phase 0 review.

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
