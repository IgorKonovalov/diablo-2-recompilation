# 0066 — Inferred-claims sweep 2: the simulation and game-rules specs

> **Status:** approved (2026-11-10, by the owner, as recommended: question 1 (b), plan 0038 closed; question 2, 20 claims per session; Phase 1 go and question 3 (c) given by the owner 2026-11-10 evening)
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
  **Answered 2026-11-10 (owner): (c).** The bestiary tour becomes a monsters/ai harness sub-plan, drafted once S1b's
  checker is accepted; the other 491 harness rows are recorded as (a-run, deferred) at Phase 1's close.

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

### 2026-11-10 — Owner decisions (evening)

- **Phase 1: go.** The 36 static batches run as reverser-static lanes, two at a time, Tier B per batch (audit every
  fifth). S1a and S1b first, since the bestiary tour needs S1b's checker.
- **Question 3: (c).** A monsters/ai harness sub-plan for the bestiary tour (H1a to H1d, H1g, H1h; about 214
  statements in about 12 launches), drafted by the architect after S1b is accepted. The other 491 harness rows are
  deferred with their routes kept.

### 2026-11-10 — Phase 1, batch S1a (reverser-static, `lane/n66a`)

- **Done.** The 17 statements of S1a checked over the kept rev 4 (21) and rev 6 (17) AI logs, no game. Record: the dated
  addendum *plan 0066 batch S1a* under run:2026-11-04-ai-r5 in [findings/ai/experiments.md](../findings/ai/experiments.md);
  outputs in `workspace/logs/ai/sweep2-s1a/` (`manifest.sha256`), inputs in `workspace/logs/ai/manifest-sweep2-s1a-inputs.sha256`.
  Tools (`2172cedd`): `tools/ai_resume_flip.py` gains `--key row|think|rowthink`, `--thinks` and a `FREEPAST` line (the
  default output reproduces `review-p52c/flip-rows-full.txt` for rows 13 and 21 byte for byte); new `tools/ai_move_refusal.py`
  for row 516. Every resumed decision flipped (`--cap 1000000`), not a sample.
- **Result (inventory rows):** raised 10 (19, 22, 25, 55, 141, 149, 157, 164, 326, 506: sentence H1's rule met on their own
  think's decisions); raised in part 2 (503: S11's 66 fork-free of 134; 516: refusals with flags 0, 4 and 7, while `Walk(t, 1)`,
  "no idle", flag 1's `0x40` and which bit brings the draw stay `[I]`); moved 5: 76 (row 23: 8 mismatches and one two-way
  site, 0x005F356C, that separates none of its 21 decisions) a-logs → a-run (H1g); 169, 350 (rows 70 and 118: no fork-free
  decision) and 197, 200 (rows 78 and 79: the fork-free decisions have no call past the first) a-logs → b (H1h). S1a holds 12
  statements now; totals a-logs 716, a-run 348, b 362 (inventory README § 1, § 3).
- **Surprise.** The catalogue `r` lines' "an unknown value deciding N of M later steps" counts calls with several offers, not
  branch steps on an unknown, so it does not pick the fork-free rows: rows 70 and 118 say 0 and fork in every decision. The
  inventory helper's S1a selection rested on that figure; S1m to S1z (machinery tier cases) may hold the same.
- **Ready for Phase 3 (spec-writer), monsters/ai/catalogue at `b5999f5e` line numbers:** 152 (R3r), 187 (R4r), 220 (R5r),
  483 (R15r, think 0x005F1800 only), 1272 (R52r), 1352 (R63r), 1404 (R65r), 1456 (R68r), 3117 (R96r), 4604 (S12r) to `[C]`
  under sentence H1, each a row of README H1's table (decisions, calls past the first, two-way sites as in the addendum);
  4583 (S11r) and 4687 (the refused-move note) split, the raised half `[C]`, the rest `[I]` as the inventory rows say. No
  symbol is raised (H1 raises none; `MonAiMove` is not a boundary).
- **Review:** Tier B (plan Phase 1), with the audit rule. Judgment calls to check: (1) S11 and S12 counted by think across
  rows (`--key think`), not by row; (2) row 23 moved rather than raised on the rev 6 logs alone, since 0x005F356C fails the
  rule over all 500 fork-free decisions; (3) 516's raised half names the helper's logged word, with the helper-to-flags map
  kept `[I]` (three code reads).

### 2026-11-10 — Phase 1, batch S1b (reverser-static, `lane/n66c`)

- **Done.** The 61 statements of S1b checked with a new block-model checker over the 38 kept AI logs (21 rev 4, 17 rev 6),
  no game. Tool: `tools/ai_model_check.py` with `tools/test_ai_model_check.py` (`ceeac566`, `f2373e64`): one model per
  catalogue entry, transcribed from the spec block at `b5999f5e` (not from `ai_resume.py` or a decompile), fed the logged
  boundary returns as ADR-0004 oracles and compared call by call (callee, the block's argument words, seed, control words,
  `+0xC4`, pointed-to blocks, the exit seed); unknown values fork and forked decisions support nothing; controls: each
  branch and store reversed alone (a store also against the unit's next decision), `<=` for `<` in draws and compares,
  axis swaps for rows 78/79, a signed remainder for row 43. It takes `--logs LIST` and `--rows`, so the bestiary-tour
  logs (question 3 (c)) plug in. Record: the dated addendum *plan 0066 batch S1b* under run:2026-11-04-ai-r5 in
  [findings/ai/experiments.md](../findings/ai/experiments.md); outputs in `workspace/logs/ai/sweep2-s1b/`
  (`manifest.sha256`), inputs as S1a's (`manifest-sweep2-s1a-inputs.sha256`).
- **Result (inventory rows):** 0 mismatches in 28 of the 29 modelled thinks (row 23: 8, the rev 4 logger limit). Raised 43:
  row 44 (R12's block) whole; 42 in part, each on its taken, separated arms with the rest `[I]` as the row says (17, 18, 20,
  23, 24, 45, 49, 51, 68, 93, 94, 114, 115, 138, 140, 147, 148, 150, 152, 153, 156, 161, 162, 165, 167, 193, 198, 199, 320,
  321, 323, 324, 335, 369, 370, 388, 485, 486, 498, 501, 504, 505). Moved 18: 21, 50, 70, 71, 139, 151, 336, 489 a-logs →
  a-run (H1g); 12, 113, 163, 168, 195, 347, 348, 466, 467, 500 a-logs → b (H1h) (reasons in the rows: no logged call, no
  fork-free case, no decision, under the floor, or row 23's mismatches). S1b holds 43 statements now; totals a-logs 698,
  a-run 356, b 372 (inventory README § 1, § 3), taken against `main` at `d3d79c89`, which has not changed the inventory
  since this lane's base `e1878e23`.
- **Surprises.** (1) The blocks, read against instructions at the plan 0052 reviews, held on every compared call; the
  checker's teeth are its flips (every raised branch fails alone) and the exit seed. (2) R23's loop sentence "step x and y
  one away from U's position; if at it, both + 1" has two readings; one decision separates them ("an equal axis is not
  stepped" matches), recorded as a lead since row 23 moved. (3) Most rows that fork for `ai_resume.py` do not fork for the
  block model, because the block does not branch on the words the interpreter needs (row 70's `p`, S11's speeds): rows 70
  and 118's `r` lines stay where S1a put them, but row 70's block is raised in part.
- **Ready for Phase 3 (spec-writer), monsters/ai/catalogue at `b5999f5e` line numbers:** 392 (R12's block) to `[C]`
  whole; split, the raised half `[C]` and the rest `[I]` as each inventory row says: 140, 147 (R3), 164 (R4), 200, 215
  (R5), 399 (R12a), 450, 477 (R15), 613 (R19), 850, 877 (R26), 1053, 1065 (R43), 1233, 1267 (R52), 1337, 1347 (R63), 1365,
  1395, 1396, 1399 (R65), 1435, 1450 (R68), 1463 (R69), 1482 (R70), 1726 (R78), 1759, 1769 (R79), 3055, 3067 (R95), 3081,
  3112 (R96), 3176 (R114), 3450, 3465 (R124), 3615 (R130), 4438, 4451 (R99), 4547 (S10), 4567 (S11's think), 4592, 4602
  (S12). The block lines carry one `[I]` for the whole think, so Phase 3 adds a `[C]` bullet per block naming the logged
  paths (the addendum's list) rather than re-tagging the block. No symbol is raised (the blocks raise no role or name).
- **Review:** Tier B (plan Phase 1), with the audit rule. Judgment calls to check: (1) the floor of 30 fork-free decisions
  from the batch row (H1's 50 is for `r` lines), so rows 43 (32), 114 (31) and 130 (33) count, row 100 (4) does not;
  (2) positions for rows 43, 63, 78 and 79 are the AID line's `x`, `y` and the target's, the logger's words for
  `UnitGetPos`, held by the axis controls; (3) a branch with no equal pair keeps its `<` against `≤` inferred, which makes
  rows 19 and 69 "in part"; (4) the calling conventions in `CONV` come from the emulation families and machinery § B, and
  any wrong one would have failed its calls.
