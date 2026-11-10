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

### 2026-11-10 — Phase 1 batch S2a, part 1 of 2 (reverser-static, `lane/n66b`): 80 of 100 settled; resume note

- **Done.** New check tool `tools/skills_s2a.py` (`f3084824…`, stdlib, read-only; it reuses `tools/skills.py`'s parser)
  over the 45 kept logs of run:2026-10-25-skills, run:2026-10-27-skills and run:2026-10-30-skills-catalogue, unchanged:
  `workspace/logs/skills/2026-11-10-s2a-check.txt` (`f69b8ec8…`, 680 lines, 0 breaks) under
  `2026-11-10-s2a-manifest.sha256` (`sha256sum -c` passes from that directory). Record: the dated addendum in
  [skills experiments, run:2026-10-27-skills](../findings/skills/experiments.md#addendum-2026-11-10-plan-0066-batch-s2a-new-checks-over-the-three-kept-skills-runs-lanen66b),
  with pointer lines under the other two runs. The route said "new `tools/skills.py` checks"; they are a separate
  tool, so the hashed checker behind the three runs' kept outputs is unchanged.
- **Rows.** 80 settled in [skills-README](0066-inventory/skills-README.md) and [skills-dispatch](0066-inventory/skills-dispatch.md),
  each with a dated note in its *Route* cell: **raised** 11 (README 1, 25; dispatch 7, 8, 9, 10, 61, 90, 173, 175, 191),
  **raised in part** 56 (the `[C]` part and the remainder's class
  and batch named in the row), **moved** 13 (README 5 and dispatch 12, 106, 188 to d-none; dispatch 72, 87, 99, 100,
  101, 140, 147, 192 to b in H2a; 21 to c in S2c). Totals in § 1, the two files' *Totals by class* and the § 4 rows
  of S2a (now 87), S2c (68) and H2a (27) follow the moves; the reviewer recomputes them against `main` at the merge
  (n66a moves other rows of the same tables).
- **Contradicted in part (route to Phase 3 and a reverser read):** 566 monster starts in mode 14 (skills 158, 160,
  167, 176, 181, 327) enter `SKILLS_SrvStart` from `StartUsedSkill` with `Unit+0xC4` bit 6 **clear**, while all 1 460
  starts in modes 4, 5, 7, 8, 9 have it set. dispatch's entry table (monster modes 4, 5, 7, 8, 9, row 4) misses mode
  14, and skills/README § C's "a monster reaches the start and do through its AI with bit 6 set" (README row 16) holds
  for modes 4 to 9 only. The mode-14 start path (who commands it, who clears the bit) is unread: a reverser read of
  `sub_005A75C0_MonModeStartSkill` and the sequence mode start is the follow-up.
- **Ready for re-tagging (Phase 3, spec-writer),** by inventory row (each row gives its spec line at `b5999f5e`;
  dispatch.md has since moved by 2 to 89 lines (plan 0068), so match by text): whole, README rows 1, 25 and dispatch
  rows 7, 8, 9, 10, 61, 90, 173, 175, 191; the `[C]` half each note names, README rows 12, 15, 16 and dispatch rows
  1, 2, 4, 5, 6, 25, 26, 27, 29, 31, 43, 44, 45, 50–55, 63, 68, 70, 75, 79, 80, 82, 85, 102, 104, 105, 109, 139, 141,
  145, 148, 159–172, 177, 179, 186, 187 (the split goes into the spec text; the remainder keeps `[I]`).
- **Resume note (part 2, a fresh lane on `lane/n66b`).** 20 rows left, still `a-logs`/S2a with no S2a note:
  - skills-README rows **2** (hit-function rows' `MH` ends against the catalogue's hit models), **22** (outputs: the
    `0x40` cell marks and ammunition/durability), **23** (frame pass order, run:2026-11-03-frame-order);
  - skills-dispatch rows **11** and **150** (the ai.gdb `MonAiUseSkill` lines, run:2026-11-03-ai and the
    `2026-11-04-h1-*` combined logs in `workspace/logs/skills/`), **59** (item-cast MC positions against the doubled
    point: the `MC0` 0x5C-byte block's points, `tools/skills.py mc()` for the layout), **86** (I2: the `REL` seed and
    `min` against the packet's elemental field at the next `AD0`/`DQ0`), **103** (the 48 entry-39 creations' class
    against Fists of Fire's `srvmissilec`), **107** (K1's newest-first order: likely b, the registration order is not
    logged), **114, 115, 116, 118, 121, 125, 126, 132** (handler effects: `EV STA in handler` and `EV deltas` of the
    kept output already give thorns' `sv << 8` against the attacker's life, slow's state 24 for 750 frames with stat
    67, rest in peace's absence of an STA 172 line, knockback and stupidity with no effect line → b), **137** (`PH0`
    between `THR` and `DRR`), **155** (the economy `UA0`/`UA1` lines of run:2026-10-17-economy), **176** (whether the
    tick re-queues: the 89 zero-step tick pairs).
  - Extend `tools/skills_s2a.py` as a new revision and keep its output under a new name (do not overwrite
    `2026-11-10-s2a-check.txt`); add the rows' notes as above, update the S2a status cell and the totals.
- **Review:** Tier B (plan 0066 Phase 1), at the end of part 2.

### 2026-11-10 — Phase 1 batch S2a, part 2 of 2 (reverser-static, `lane/n66b`): done, 100 of 100 settled

- **Done.** The last 20 rows. `tools/skills_s2a.py` revision 2 (`a7395fa3…`) adds `check2` (the 45 skills logs), `ai`
  (the 86 ai.gdb logs of run:2026-11-03-ai, `-2`, `-3`) and `ua` (the 35 economy.gdb logs of run:2026-10-17-economy);
  `check` is unchanged and reproduces part 1's `2026-11-10-s2a-check.txt` (`f69b8ec8…`). Kept outputs
  `workspace/logs/skills/2026-11-10-s2a-check2.txt` (`29ad2680…`), `2026-11-10-s2a-ai.txt` (`8816d536…`),
  `2026-11-10-s2a-ua.txt` (`3c3c8c6c…`) under `2026-11-10-s2a-part2-manifest.sha256` (passes from that directory), 0
  breaks. Record: the part-2 addendum in [skills experiments](../findings/skills/experiments.md#addendum-2026-11-10-plan-0066-batch-s2a-part-2-handler-effects-the-ai-command-ammunition-lanen66b);
  a dated note in [skills/0003 § 16](../findings/skills/0003-handlers.md#16-plan-0045-phase-2-part-2-the-run-run2026-10-27-skills);
  `sub_005BF960_StatEv07Knockback` raised to `C` in `re/symbols.csv` (its return compared with the model in 246 calls,
  review-fixes rule 14).
- **Rows (part 2).** Raised 3 (dispatch 11, 116, 176); raised in part 10 (README 22, 23; dispatch 86, 103, 107, 115,
  125, 137, 150, 155), the `[C]` part and the remainder's class and batch in each row; moved 7: README 2, dispatch 59,
  118, 126, 132 a-logs → b (H2a), dispatch 114, 121 a-logs → a-run (H2b). **Whole batch:** raised 14, raised in part
  66, moved 20 (4 → d-none, 13 → b in H2a, 2 → a-run in H2b, 1 → c in S2c); S2a holds 80 statements.
- **Totals** recomputed from the 29 inventory files after `main` `e1878e23` (S1a merged, at `00a05e0a`): a-logs 696,
  a-run 350, b 375, c 389, c-emu 490, d 326 (sum 2 626); Phase 1 1 575, Phase 2 725 (inventory README § 1, § 3; the two
  files' *Totals by class*; § 4 rows S2a 80, H2a 32 at ~3.2 claims per session, H2b 14 at ~1.0).
- **Contradicted in part, for Phase 3 and the reverser.** (1) Mode 14: besides part 1's 566 starts entering `SrvStart`
  with bit 6 clear, the AI command (`MonAiUseSkill`) returns with bit 6 clear in 176 of 176 mode-14 calls (set at the
  call in 70), while modes 4, 5, 7, 8, 9 return with it set (174). dispatch's entry table (row 4), § E2, § M1 (row 150)
  and skills/README § C (row 16) need rewording for mode 14. Backlog
  [2026-11-10-reverser-reverser-skills-mode-14-start-bit-6](../backlog/2026-11-10-reverser-reverser-skills-mode-14-start-bit-6.md)
  asks for the read. (2) Slow (dispatch § K row 19, inventory row 125): the logged `STATE_ApplyTimed` block carries
  stat 67 = −v, which the row does not name.
- **Ready for re-tagging (Phase 3, spec-writer), parts 1 and 2 together,** by inventory row (spec lines at `b5999f5e`;
  dispatch.md has moved since, so match by text). **Whole** to `[C]`: skills/README rows 1, 25; skills/dispatch rows 7,
  8, 9, 10, 11, 61, 90, 116, 173, 175, 176, 191 (14). **Split** (the `[C]` half each row's note names goes into the spec
  text, the remainder keeps `[I]`): README rows 12, 15, 16, 22, 23; dispatch rows 1, 2, 4, 5, 6, 25, 26, 27, 29, 31,
  43, 44, 45, 50–55, 63, 68, 70, 75, 79, 80, 82, 85, 86, 102, 103, 104, 105, 107, 109, 115, 125, 137, 139, 141, 145,
  148, 150, 155, 159–172, 177, 179, 186, 187 (66). The rewordings of (1) and (2) above go with them.
- **Left.** Nothing in S2a. The moved rows wait in H2a, H2b, S2c and d-none as their notes say.
- **Review:** Tier B (plan 0066 Phase 1), for the whole batch (parts 1 and 2). Judgment calls to check: (1) the
  ai.gdb run's 86 logs include relaunched sessions ("fresh:" logs beside the launch logs, both in the run's manifests),
  counted as logged; (2) row 23 (frame pass order) raised in part from the kept frame-order check's pair table with no
  new run; (3) row 86's one-draw claim rests on the 11 rolls with no other line before the event's exit; (4) the
  remainders routed to b rather than d-none where a logger line would reach them (rows 2, 59, 118, 126, 132).

### 2026-11-10 — Sub-plan 0069 drafted (architect, `lane/n69a`)

- Sub-plan [0069](0069-monster-ai-bestiary-tour.md) drafted for question 3 (c): the bestiary tour over H1a to H1d, H1g
  and H1h (237 statements at `4fb8b55f`), `proposed`, for the owner.

### 2026-11-10 — Phase 1, batches S1c and S1d (reverser-static, `lane/n66d`)

- **Done.** Both batches over kept logs, no game, no Ghidra (r2/objdump reads of call sites only). Tools (`cd663109`):
  `tools/ai_model_check.py` revision 2 (`de9bb5ed…`) adds R44's and S13's blocks, transcribed from the spec at
  `b5999f5e`; revision 1's 32 entries reproduce S1b's `model-check.txt` byte for byte. New `tools/ai_first_check.py`
  (`e4eb1802…`): first-boundary hand maps (README G5) that run the block models to their first logged call and compare
  the call site too, the sites read from the code (the think's one call to the callee, or the emulated family's site for
  R99 and R130). Outputs in `workspace/logs/ai/sweep2-s1cd/` (`s1c-model-check.txt` `fb54d78f…`, `s1d-first-check.txt`
  `f41b2f45…`, `manifest.sha256` passes from there); the 74 input logs in `manifest-sweep2-s1cd-inputs.sha256`. Record:
  the addenda *plan 0066 batch S1c* and *S1d* under run:2026-11-04-r72 in [findings/ai/experiments.md](../findings/ai/experiments.md),
  with pointer lines under run:2026-11-03-ai, run:2026-11-03-ai-3 and run:2026-11-04-ai-r5. `tools/ai.py` is unchanged
  (the route named it; it is the hashed checker behind those runs' kept outputs).
- **S1c (6 rows): raised in part 6, moved 0.** R44: 309 decisions, all fork-free, 0 mismatches, 310 calls past the first,
  every branch failing alone; the grant, `UseSkill1` and the `aip` 0 true sides stay `[I]` (rows 280, 281, 283). S13:
  160 decisions, all fork-free, 0 mismatches, 988 calls past the first, the arms and counts of S13d by a second
  transcription; S13f's list stays `[I]` (rows 507, 508, 509).
- **S1d (16 rows): raised 11, raised in part 1, moved 4.** Raised (0 mismatches, all fork-free, the site control failing
  every decision): rows 38 (R10, 209 = 49 + 160 state 13), 43 (R11, 17), 75 (R23, 1 062), 96 (R26, 119), 130 (R48, 321),
  136 (R49, 74), 144 (R56, 16), 325 (R96, 179), 389 (R130, 119, four outcomes), 487 (R99, 468, two outcomes), 490 (R100,
  16). In part: 54 (R15: the think's 177 of 181; the alt's 4 fork on the kind-14 record's `+0x18`). Moved a-logs → b
  (H1h): 13 (R1: the think lies outside the logger's windows), 349 (R118: `StatListFindFlag` decides before any call),
  460 (R32: the home record's words), 468 (R54: `AiNearestPlayer`'s search returns outside the windows). S1d holds 12
  statements now, H1h 39.
- **Totals** recomputed from the 29 inventory files against `main` `4fb8b55f` (S1a, S1b, S2a merged): a-logs 674, a-run
  358, b 389, c 389, c-emu 490, d 326 (2 626); Phase 1 1 553, Phase 2 747 (inventory README § 1, § 3, § 4; the
  catalogue file's *Totals by class*).
- **Ready for Phase 3 (spec-writer), monsters/ai/catalogue at `b5999f5e` line numbers.** Whole, the `l` line restated as
  "[C] First boundary: N decisions compared (…), 0 mismatches, k first-call outcomes" with the hand map named (README
  G5): 327 (R10l, both thinks), 381 (R11l), 692 (R23l), 881 (R26l), 1185 (R48l), 1223 (R49l), 1304 (R56l), 3116 (R96l),
  3627 (R130l), 4455 (R99l), 4467 (R100l). Split, the raised half `[C]` and the rest `[I]` as each inventory row says:
  482 (R15l: the think; the alt stays `[I]`), 2613, 2615, 2625 (R44 steps 1, 2 and R44b's tail), 4613, 4621, 4622 (S13's
  `AiPathSkillStep`, think and RunHome lines). As in S1b, the block lines carry one `[I]` for the think, so Phase 3 adds a
  `[C]` bullet for R44 naming the logged paths; S13d already is that bullet for S13 and gains the second transcription
  as an anchor. No symbol is raised (no logged return is compared with a model; the maps raise no name).
- **Left.** Nothing in S1c or S1d. The moved rows wait in H1h as their notes say.
- **Review:** Tier B (plan Phase 1), with the audit rule. Judgment calls to check: (1) a one-decision arm raised in part
  (R44's walk, rows 281 and 283; S13's accepted RunHome, row 509), where the arm's call words and the exit seed are
  compared and its test fails it when reversed, though R44n had kept "step 2's walk is one decision" `[I]`; (2) the
  first boundary of a hand map is its first call of a logger boundary function, so R10's is `UnitGetRoom` inside step 1
  (`MonPlayerBonus` is not logged), and single-outcome rows confirm the call and its words only (README G3); (3) S13's
  path count is the given word read from the fires, as `ai_s13_check.py` took it, so its equal pairs separate nothing;
  (4) the S1d maps live in a new tool rather than `tools/ai.py`, to keep the kept first-boundary outputs reproducible.

### 2026-11-10 — S1c and S1d review (architect, Tier A, the audit of the fifth Tier B lane): accept with fixes

- **Re-run** (no game, under `systemd-run --user --scope -p MemoryMax=3G`, from `workspace/logs/ai`): both inputs
  manifests pass (`manifest-sweep2-s1cd-inputs.sha256`, 74 logs: 31 + 21 + 17 + 5; `sweep2-s1cd/manifest.sha256`); S1c
  `--rows R44,S13` and the whole S1d command reproduce `s1c-model-check.txt` and `s1d-first-check.txt` byte for byte;
  revision 2 with S1b's 32 names reproduces `sweep2-s1b/model-check.txt` byte for byte. S13's count read from the fires is
  4 for both units that fire, H1b's file word.
- **Independence.** `m_r44`, `m_s13` and the six new heads follow the blocks at `b5999f5e` step for step (R10's
  `MonPlayerBonus(G, &pb, UnitGetRoom(U), U)`, R11, R48's call-free step 1, R49, R56, R15's alt); nothing in them is
  absent from the block. Sites spot-checked by objdump: the one call before 0x005F0B2C, 0x005F6ECB, 0x005F8FB1 and
  0x005E7F5C in each think.
- **Ruling 1 (one-decision arms, rows 281, 283, 509): not an overclaim.** Plan 0038's ruling on single decisive cases
  holds: the branch is decided by logged input, the block is read, and the case reproduces words no wrong reading meets by
  chance (`Ovr(13, 0, 0)`, `Walk(t, 7)`; `PathOvrSet(1, 0, 0)`, `RunToPoint(home)`), with the arm's test failing reversed.
  H1's sentence is "on the logged paths only" and its table already names the one not-melee decision. What one case
  cannot separate stays `[I]` as the rows say (the draw's `<` against `aip(5)` 0). R44n's "step 2's walk is one decision"
  (row 284, d-owner) remains a true scope note.
- **Ruling 2 (R10's first boundary `UnitGetRoom`): sound.** It is the argument of `MonPlayerBonus` and the think's first
  call in code order (objdump: no call before 0x005F0B27), so the map runs no callee and uses no return: ADR-0004 and
  ruling R2 hold. The note "`MonPlayerBonus` is not logged" is a side remark, not the reason.
- **Fix (1 overclaim).** S13: step 2's two tests (the record found, its words non-zero) do not fail alone; their flips stop
  at the unmodelled push and refill in 160 of 160 (`FLIP 2.home!=0`, `2.words!=0`). Row 508 and the S1c addendum said
  every branch failed alone; both now keep those two tests `[I]`.
- **Totals** recomputed from the 29 files: a-logs 674, a-run 358, b 389, c 389, c-emu 490, d 326, sum 2 626; H1h 39.
- **Audit:** a Tier B check would have missed the fix (it shows only in the kept output's flip lines, not in the diff);
  it is not reject-grade, so no miss counts against the lane kind.
