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

### 2026-11-10 — Phase 1, batch S1e, paused (reverser-static, `lane/n66e`): resume note

- **Paused at the owner's request** before the kept run. No inventory row, total or finding is changed yet; the batch
  Status in the inventory README § 4 still reads `scheduled`.
- **Done.** New tool `tools/ai_s1e_emu.py` (this commit): 24 emulation families, one shared memory spec and one cases file,
  so one `tools/ghidra.sh emuboundary` launch (about 30 s) runs all 5 760 cases. **No callee is an observed boundary.** Every
  callee runs whole on the declared image: `UnitDistSq`, the stat getters with `0x00624F60`'s search, `UnitAlignGet`,
  `AlignSame02`, `UnitsHostile` with the player relation list, `MonsterOwner`/`GameFindUnit`, the state tests,
  `AiShadowSkillFits` on its declared paths, and `AiUnitSearch` kind 1 with `AiSearchNearRooms` for Mephisto's pick.
  This follows ruling R2. Each model names its tests. Every test is reversed alone, and every ordered compare has its
  strictness switched alone; the check prints the cases each control separates and lists any it leaves unseparated.
  Development runs in session scratch only (not kept), with the last tool revision but its tags: 5 760 of 5 760 match,
  0 stopped, 0 unaccounted traced reads (only `g_BitMask32`, `g_UnitHashOffsets`, `g_AiSearchKinds` and the two
  `.text` jump and byte tables at 0x005EB7D8 and 0x005EAD34). Unseparated: three controls, each inherent: `trkind`
  `hi<=lo~` (the call is always `RandLoHi(0, 3)`; `randlohi` separates it); `shroll` `v18<lo~` (an equal value written
  back); `genspawn` `count>453` and `count>453~` (the first `*out` store is overwritten on every path).
- **Findings to carry into the rows (from the development runs; re-check on the kept run):** (1) the weighted pick
  0x005FC130 with sum ≤ 0 takes `r = 0` with no draw and still scans: 27 of 240 cases return a `k` (a positive
  prefix), against catalogue line 3917's "if sum ≤ 0: the fallback". (2) `AiGenSpawnPickClass` with n = 0 draws
  nothing, still tests entry 0 (2 cases take its class), and otherwise ends at 496/−1 (36), not 453; its first store
  is dead (line 3593 block). (3) `AiLifePct` 0x005DD280 is `push ecx; call UnitLifePct; ret`. The two return the same
  value on 240 of 240 images, so lines 53 and 4689's "two different readers" is one map behind two calling
  conventions. (4) Mephisto's pick draws only when the search found a candidate (`blk[3]` ≠ 0; 166 cases with no
  draw); line 2697 implies a draw always. (5) `AiWoundedNearCb`'s "not dying" is `MonIsDeathMode`, which is 0 for
  every player; ties replace (`≤`). (6) `AiShadowSkillRoll` draws 0, 1 or 3 times, not "three per tried skill", and
  never reads its fourth argument (melee comes from `ctx+0x18` in Fits).
- **Row plan (catalogue rows, per the analysis):** raised whole: 15, 172, 194, 242, 332, 360. Raised in part, with the
  remainder named: 3 (the remainder follows machinery's `Ovr`, `Head`/`Pop`/`Push`, `UseSkillK`, `DelayE`, `State` and
  rchance≡chance); 31 (the think's `aip(1)`, the 7 tries and the wrap's stock reach); 66, 72, 135, 154, 182, 314 (the
  think's frame or initial block words); 196 (the caller set and `MonRegionsBuild`'s −1 store go to c, S1f); 229 (the
  bonus-level branch 0x00644180 and Fits' undeclared paths); 288 (the "one caller" claim goes to c, S1f); 356 (row
  128's push and the name of state 141 go to c); 385 and 420 (with the corrections above); 518 (which rows call which:
  c). Moved: 421 c-emu → d-owner. Its reason: `AiPlayerThreatScore` and `AiBaalThreatScore` call `InMeleeRange` first
  and `AiLineClear` later, both reaching `COLL_LineTest` 0x0064E260's room walk. R2 leaves no c-emu route, and both
  callers are Diablo's and Baal's.
- **Next (a fresh lane on `lane/n66e`):**
  1. `python3 -I tools/ai_s1e_emu.py cases --dir workspace/logs/ai/sweep2-s1e`, then the Ghidra run under
     `systemd-run --user --scope -p MemoryMax=4G` with `GHIDRA_PROJ_DIR=…/workspace/ghidra-n66e GHIDRA_HEADLESS_MAXMEM=3G`
     into `s1e.out`, then `check > check.txt` and `manifest --write`.
  2. Write the run record `run:2026-11-10-sweep2-s1e` in `docs/findings/ai/experiments.md` (setup, procedure, the
     check's lines, the unseparated three, the corrections).
  3. Update the 22 rows in `docs/plans/0066-inventory/monsters-ai-catalogue.md`: rows 3, 15, 31, 66, 72, 135, 154,
     172, 182, 194, 196, 229, 242, 288, 314, 332, 356, 360, 385, 420, 421, 518. Their spec lines at `b5999f5e`: 53,
     115, 289, 598, 687, 1220, 1397, 1560, 1643, 1736, 1747, 2031, 2277, 2697, 2960, 3164, 3359, 3380, 3593, 3916,
     3921, 4689.
  4. Update that file's *Totals by class* (421 → d-owner), the S1e row of the README § 4, § 1, § 3 and the
     totals, against the merged `main`. Lane n66f edits the same totals rows.
  5. Write the log entry (Tier B review) and the list of statements ready for re-tagging.

### 2026-11-15 — Phase 1, batch S1e (reverser-static, `lane/n66e`): done, 22 of 22 settled

- **Done.** The kept run [run:2026-11-15-sweep2-s1e](../findings/ai/experiments.md#run2026-11-15-sweep2-s1e): `tools/ai_s1e_emu.py`
  as committed at `9d00a53b` (`6d0287cd…`, unchanged), one `tools/ghidra.sh emuboundary` launch on
  `workspace/ghidra-n66e` (`-Xmx3G`, `MemoryMax=4G` scope), 24 families, 5 760 cases, 5 760 matching, 0 stopped, 0
  unaccounted traced reads; 244 controls, 240 failing every case they separate, 4 with no observable (`trkind`
  `hi<=lo~`, `shroll` `v18<lo~`, `genspawn` `count>453` and `count>453~`). Outputs in `workspace/logs/ai/sweep2-s1e/`
  (`check.txt` `86d920a6…`, `manifest.sha256` `77befdea…`, 12 lines, passes from there); `cases` regenerates the case
  file byte for byte, `check` reproduces `check.txt`. The development runs of 2026-11-10 were not kept and nothing rests on
  them. The six findings of the resume note held on the kept run, each read again by objdump.
- **Rows (22): raised 5, raised in part 16, moved 1** (332 moved from whole to in part at the Tier B check). Raised: 15
  (`MonAiEntryGet`), 172 (`AiRegurgitatorCb`), 194 (the
  R78 block), 242 (`AiShadowMasterCb`), 360 (`AiMinionCountCb`). In part, the remainder named in each
  row: 332 (`AiImpNearCb`, its `count > 492 ? 492 : −1` guard), 3 (machinery's helpers), 31, 66, 72, 135, 154, 182, 314 (the think's frame, block words or later reads), 196 (the
  caller set and `MonRegionsBuild`'s −1 store → c, S1f), 229 (`AiShadowSkillFits` past its declared paths and the
  bonus-level branch 0x00644180), 288 (the one caller → c, S1f), 356 (row 128's push and state 141's name → c, S1f), 385
  (the dead first store, no observable), 420 (the inline copies → c, S1f), 518 (which rows call which → c, S1f). Moved: 421
  c-emu → d-owner, as the resume note gave: the threat scores reach `COLL_LineTest` 0x0064E260's room walk through
  `InMeleeRange` and `AiLineClear`, R2 leaves no emulation route, and only Diablo and Baal call them. **Owner decision:**
  none is needed now; 421 waits for owner play of Diablo or Baal, like the other d-owner rows.
- **Corrections (six; the spec's text is Phase 3's).** (1) 0x005FC130 with sum ≤ 0 still scans with `r = 0` (27 of 240
  return a `k`; line 3917). (2) `AiGenSpawnPickClass` with n = 0 tests entry 0 with no draw; its first store is dead (line
  3593 block). (3) `AiLifePct` is `UnitLifePct` behind `ECX` (lines 58, 4689 and quirks Q515). (4) Mephisto's pick takes its first
  draw only after a find (line 2697). (5) `AiWoundedNearCb`'s ties replace and "not dying" is 0 for players (line 687). (6)
  `AiShadowSkillRoll` draws 0, 1 or 3 times and never reads `melee` (line 2031). Dated notes in ai/0002, 0003, 0006,
  0008, 0011 and 0012 (rule 20); the spec copies routed by [backlog](../backlog/2026-11-15-reverser-spec-writer-plan-0066-s1e-corrections-for-phase-3.md).
- **Symbols:** none raised. The run is an ADR-0015/0021 emulation over a declared image, which confirms maps, not names
  (review-fixes rule 14).
- **Totals** recomputed from the 29 inventory files against `main` `389cb19d` (merged at `0f30ab21`): a-logs 674, a-run
  358, b 389, c 389, c-emu 489, d 327 (d-owner 68), sum 2 626; Phase 1 1 552, Phase 2 747 (inventory README § 1, § 3,
  § 4; the catalogue file's *Totals by class*: c-emu 21, d-owner 62). S1f's row names the five remainders routed to it.
- **Ready for Phase 3 (spec-writer), monsters/ai/catalogue at `b5999f5e` line numbers.** Whole, `[C]` with the run as
  anchor: 115 (S0), 1560 (R71b), 1736 (the R78 block), 2277 (R106b), 3380 (R121a). Split, the raised half
  `[C]` and the rest `[I]` as each row says: 53 (Notation: `LifePct`, `UnitLifePct`, `O`, `St3or19`), 289 (R8b), 3164 (R113b, its `count > 492` guard `[I]`), 598
  (R18a), 687 (R23b, with correction 5), 1220 (R49b), 1397 (R65c), 1643 (R74b), 1747 (R78b), 2031 (the R105 block, with
  correction 6), 2697 (R50c, with correction 4), 2960 (R85b), 3359 (R120b), 3593 (the R129 block, with correction 2),
  3916 (the pick, with correction 1), 4689 (with correction 3). 3921 stays `[I]` (d-owner).
- **Left.** Nothing in S1e. The c remainders wait in S1f.
- **Review:** Tier B (plan Phase 1), with the audit rule. Judgment calls to check: (1) the callbacks' rows raised in part
  where the block words come from the think (the callback's map is the whole claim tested; the initial words and frame
  offsets are the think's and stay `[I]`); (2) row 31's "search kind 1 walks the near rooms' unit lists" counted as met
  through family `mephpick`, the same `AiUnitSearch` code run whole for another callback; (3) the four controls with no
  observable taken as inherent rather than as gaps (each named in the run record); (4) correction 1's Diablo inline read
  statically and left `[I]`, routed to S1f rather than run; (5) row 385's dead store kept `[I]` inside a raised-in-part row
  rather than moved to d-none.

### 2026-11-15 — Phase 1, batch S1e, Tier B check (architect, `lane/n66e`): accept with fixes (3)

- **Verdict: accept with fixes.** Fixes (3): overclaim 2, stale cross-reference 1. All three written on the branch.
  (1) overclaim: row 332 (`AiImpNearCb`, line 3164) was raised whole, but its statement holds the guard `count > 492 ? 492 :
  −1`, and the check lists no control for it (`base492` reverses the compare of the base, not the count test; the
  model's `want` is computed with `ms_count` and no `e.c`). The row is raised in part, the guard stays `[I]`: the batch
  is 5 raised, 16 in part, 1 moved (catalogue row, README § 4, this log's Rows and Ready lists, the run record's `imp`
  bullet). (2) overclaim: correction 4 read "Mephisto's pick draws only when the search found a candidate" (run
  record, this log, the backlog entry, ai/0008's note, row 288's "166 cases with no draw"). The kept tags give 166 cases
  with no first draw and 190 with `blk[5]` 0; the second draw is gated on `blk[5]`, which a player searcher sets (4 and
  43 cases), so "no draw at all" holds only with `blk[5]` 0, which for Mephisto rests on the `[I]` one-caller claim.
  Reworded in all five places. (3) stale cross-reference: ai/0006's Functions row for `AiShadowSkillRoll` still read
  "three `Range` draws" under correction 6; it now says 0, 1 or 3 and points to the note.
- **Checked clean.** `sha256sum -c manifest.sha256` passes (12 lines); the hashes the record names match (`check.txt`
  `86d920a6`, manifest `77befdea`, `s1e.out` `c0c12a75`, `s1e.cases` `01e0f560`, tool `6d0287cd`). The check's 24 family
  lines each read 240 of 240, `bad=0 stopped=0`, every control `passed` 0; 244 controls, 4 unseparated (`trkind` `hi<=lo~`,
  `shroll` `v18<lo~`, `genspawn` `count>453` and `~`), as the record says, and each of the four is named in the row that
  touches it. The record's per-family counts (taken, drawn, 166, 88, 27, 125, 63, 36, 2, 76, 115, 49, 64, 22) agree with
  the TAGS lines. Every raised row carries the run anchor and every raised-in-part row has a "Stays `[I]`" clause (row 3,
  31, 66, 72, 135, 154, 182, 196, 229, 288, 314, 332, 356, 385, 420, 518). Totals recounted: the catalogue's c-emu 21 and
  d-owner 62; the sum of the 29 files' *Totals by class* is a-logs 674, a-run 358, b 389, c 389, c-emu 489, d-2c 59,
  d-owner 68, d-edit 23, d-none 177 = 2 626; Phase 1 1 552, Phase 2 747, blocked 327. Against `main` the lane moved c-emu 490
  → 489, d-owner 67 → 68 (the one row 421). Six corrections in the findings and the backlog entry match the batch entry
  (backlog entry front matter and routes read; Q515 and L58/L4689 routed). No `[L]` added. Gate green.
- **The five judgment calls.** (1) accepted, with fix 1: the callback map is the claim tested, the think's initial block
  words stay `[I]`. (2) accepted: `AiUnitSearch` runs whole with kind 1 in `mephpick`, and row 8's search passes the same kind;
  the room-list walk is one code path. (3) accepted: each of the four is named, and none carries a claim the row states
  `[C]` (`hi<=lo~` is separated in `randlohi`, 12). (4) accepted: the Diablo inline pick is read-only `[I]` and the remainder
  is in S1f's row. (5) accepted: the dead store is `[I]` in a raised-in-part row; moving it to d-none would be a ruling for
  the owner only if the count test mattered to a reimplementer, and it does not (every exit stores again).
- **For Tier A or the owner.** Nothing needs the owner. Tier A: this is the Tier B lane counted for the audit rule; the
  audit sample is the architect's to draw. For the Phase 3 spec-writer, the six corrections reach the spec through the
  backlog entry; 3164 is now a split row.

### 2026-11-10 — Phase 1 batch S2b, paused (reverser-static, `lane/n66f`): resume note

- **Paused on the owner's request** before any row was settled: no inventory row, total or finding is changed yet. Kept
  on the branch: the new check tool `tools/skills_s2b.py` (development revision, uncommitted outputs only; its docstring
  lists the sections FRAME, MH, DMG, MA, BDO, MC, SKL, OWN). It reads the 45 S2a logs in `workspace/logs/skills`
  (`2026-10-25-skills-*.log 2026-10-27-skills-*.log 2026-10-30-skills-catalogue-cat-*.log`) with `tools/skills.py`'s
  parser; a full pass takes a few minutes under `systemd-run --user --scope -p MemoryMax=4G`. Its last complete
  output (before the FRAME end-call split was added) gave 0 breaks; nothing is hashed or kept yet. The resuming lane
  runs it once, keeps the output as `workspace/logs/skills/2026-11-1x-s2b-check.txt` under a new
  `…-s2b-manifest.sha256`, and quotes every count below from that file, not from this note (review-fixes rule 2).
- **What the development passes showed** (to be re-read from the kept output), with the row call each supports:
  - FRAME: `MF0`'s row number equals Missiles `pSrvDoFunc` in every windowed frame (do 1: 20 860, 3: 4 605, 5: 7 096,
    23: 480); every frame returning 1 is followed by the missile's frame at frame + 1 (31 804); do 1: 823 missiles end
    at range spent with frames run = frames left at creation, the frame returning the end call's 2; 65 end calls with
    left > 0 (the new split tells the step's end, before the decrement, from a crossed cell's, after it); 230 unit hits
    in do-1 frames, all at left < activate (none at =); **no do-1 frame returned 2 without a hit call** → missiles rows
    37, 97 (own-cell free) move a-logs → b (H2a). Rows catalogue 1, missiles 3, 20, 33, 34: raise in part / whole (3)
    from these.
  - MH: end calls of rows without a hit function 80 600: no build, missile seed unchanged, result 2; hit-function rows
    5 610: result 2, seed moved in 419, 386 builds inside (no unit on the call); unit calls without a hit function:
    `BD0 → MA0` 16 858, `THR → BD0 → MA0` 594, `THR` miss 718 — no filter ever refused one; pierce used by a
    CollideKill row kept the missile 130 of 130; hit-function unit calls: 1 048 of 1 209 table-predicted builds not made
    (separates "replace" from an OR, not from an AND: keep "replaces" `[I]`). Stat 19: 0 of 101 777 player-missile hits,
    flag 0x1000 on 0 of 92 094 player creations. Rows missiles 4, 24, 50, 52, 53, 89: raise in part (hit-function
    remainders → b H2a, as README 2).
  - DMG: missile seed steps once between `BD1` and `MA0` for `pSrvDmgFunc` 3 (13 486 of 13 486), none for rows without
    a damage function (4 118) → catalogue 2 in part. MA: KnockBack 0 → no step (17 608); 33 → one step and packet
    `+0x04` bit 3 iff roll < 33 (5 of 5); `DRR` inside on the defender (85) → missiles 57, 88 in part (state 54, stat 120
    → b).
  - BDO: two-draw builds 143 (run25 19, run27 43, catalogue 81), every one separating its pair: phys→fire 108,
    phys→poison 34, fire→cold 1 → missiles 59, 64 in part (stat 180 is not in the logger's stat list).
  - MC: SrvDo srvmissile creations 579 match B2/B3 (line 0x21, monster with stat 19 0x1021 and +0x48 = it (113), lob
    0x420 (104; no lob owner had stat 19, so B3's "no to-hit flag" is not separated)); MCB lines 618 of 618 with +0x54 =
    0x005C9290, EDX = +0x58, ECX = the new missile, after SU0/SU1 (missiles 84 in part); Firestorm 221 of 221 do events:
    one plain creation then callback args 0, 1 (missiles 92; calc1 3 only); Multiple Shot 36 of 36: 21 creations,
    groups 9/2/10 (0x10820/0x820/0x10820), targets stepped by one vector (catalogue 44); class 408: 24 of 36 inside an
    end call of class 407 (mhit 38), 12 after `cat-a5-1`'s MH cap (catalogue 100, missiles 86 in part, remainder
    a-run H2b); Meteor 347 creations flags 1, no target, velocity 0 — no return address on `MC0`, so missiles 2 →
    c (S2c) and missiles 1, 22 in part.
  - SKL: Amplify Damage 24 do events with STA, one per unit, state 9 = auratargetstate, one length (catalogue 48 in
    part); Holy Fire 35 do events, one REL on the caster, its first draw, one fire value across 2–15 units in 17
    (catalogue 54 in part); Bash's st 32: 73 of 86 starts one REL on the caster (catalogue 59 in part, st 39 → b).
    **R4 (catalogue 103), contradicted in part:** "the other logged monster rows none" fails for rows 339, 340, 342, 345
    (92 do events, one step each, inside their srvmissile creation) and row 167 (9 steps in 1 of 11, no logged line);
    do 109's one step lies inside `COMBAT_MeleeHitTest` (361), its four = hit test 1 + REL 1 + 2 unlogged (634); the 42
    nested restarts draw nothing; do 132's step lies inside its creation (198).
  - OWN: 1 356 hit rolls on the owner's stream from the creation's exit (113 with owner lines between, 56 more with
    unlogged draws) → missiles 90 in part (remainder d-none, a pointer to dispatch § P).
  - Not needing the tool: missiles 30 (C4's `MC.pierce` in `2026-10-25-skills-check.txt` + S2a's S328, 1 660 pairs:
    raise), 31 and 96 (run:2026-11-03-frame-order `workspace/logs/p55a/check/check.txt` `106aa180…`, by-set table:
    in part, objects and the fifth list → b H7b), 54, 55 (THR logs the chance only → b H2a), 56 (no STA of state 86 in
    the 45 logs → b H2a), 91 (outputs: in part, the 0x40 marks → b H2a).
- **Next (the resuming lane):** finish `tools/skills_s2b.py` (it ran clean; rerun after the FRAME split), keep its
  output with a manifest, write the addendum under run:2026-10-27-skills in `docs/findings/skills/experiments.md`
  (after the S2a part 2 addendum, about line 411) with pointer lines under run:2026-10-25-skills (about line 549) and
  run:2026-10-30-skills-catalogue (about line 154), settle the 38 rows in `0066-inventory/skills-catalogue.md` and
  `skills-missiles.md` (rows listed in inventory README § 4, S2b), update the S2b status cell and the totals, and file
  the R4 contradiction for Phase 3.
- **Review:** Tier B at the batch's end.

### 2026-11-15 — Phase 1 batch S2b (reverser-static, `lane/n66f`): done, 38 of 38 settled

- **Done.** Resumed from the note above, after merging `main` `f9b82bd4`. `tools/skills_s2b.py` (`114b0f7d…`, the
  revision committed at the pause, unchanged) over the 45 kept skills logs, under a 4 GB scope: kept output
  `workspace/logs/skills/2026-11-15-s2b-check.txt` (`180157a2…`, 218 lines, 0 breaks) and the `STA` state census
  `2026-11-15-s2b-sta-states.txt` (`d11872d5…`), both under `2026-11-15-s2b-manifest.sha256` (passes from that
  directory). Record: the addendum in [skills experiments, run:2026-10-27-skills](../findings/skills/experiments.md#addendum-2026-11-15-plan-0066-batch-s2b-the-missile-lines-of-the-three-kept-skills-runs-lanen66f),
  with pointer lines under run:2026-10-25-skills and run:2026-10-30-skills-catalogue; a dated
  [skills/0002 § 13](../findings/skills/0002-missiles.md#13-plan-0066-batch-s2b-the-missile-lines-re-checked-2026-11-15-lanen66f);
  `sub_005AE1F0_MissileMoveCollide` raised to `C` in `re/symbols.csv` and skills/0002's Functions table (its frame return
  compared with the nested end call in 888 frames, review-fixes rule 14). No Ghidra, no session.
- **Rows** (each with a dated S2b note in its *Route* cell): **raised** 3 (catalogue 44; missiles 3, 30); **raised in
  part** 29 (catalogue 1, 2, 48, 54, 59, 100, 103; missiles 1, 4, 20, 22, 24, 31, 33, 34, 50, 52, 53, 57, 59, 64, 84,
  86, 88, 89, 90, 91, 92, 96), the `[C]` part and the remainder's class and batch in each row; **moved** 6: missiles 2
  a-logs → c (S2c: `MC0` has no return address, so no line names `MissileCreateAt`), missiles 37, 97 → b (H2a: no
  own-cell free logged), 54, 55 → b (H2a: `THR` carries the chance, not its terms), 56 → b (H2a: no state 86 line).
  S2b holds 32 statements.
- **Totals** recomputed from the 29 inventory files against `main` `f9b82bd4`: a-logs 668, a-run 358, b 394, c 390,
  c-emu 490, d 326 (2 626); Phase 1 1 548, Phase 2 752 (inventory README § 1, § 3, § 4: S2b 32, S2c 69, H2a 37 at
  ~3.7 claims per session; the missiles file's *Totals by class*).
- **Contradicted in part (catalogue row 103, § R4), for Phase 3.** R4's "the other logged monster rows none" fails:
  the `srvmissile` rows 339, 340, 342 and 345 (do 0) step the caster once in 92 of 92 do events, inside their
  creation, and row 167 (do 91) nine times in 1 of 11 with no logged line inside. The run's own kept
  `2026-10-30-skills-catalogue-check.txt` (`2bd2b4fb…`, lines 215, 234–237) already printed both, so this is a
  transcription miss in the spec, not a new behaviour: Phase 3 rewords R4 (add the five rows; the one step of the
  `srvmissile` rows is inside the creation, where § P's chain places the critical roll) and no owner decision is
  needed. The sources of the unlogged steps (row 167's nine, do 129's one, do 109's two) stay `[I]` (b, H2a).
- **Ready for re-tagging (Phase 3, spec-writer)**, spec lines at `b5999f5e`, match by text: whole, skills/catalogue
  row 44 (line 585) and skills/missiles rows 3 (46), 30 (317); split, the `[C]` half each row's note names, catalogue
  rows 1, 2, 48, 54, 59, 100, 103 and missiles rows 1, 4, 20, 22, 24, 31, 33, 34, 50, 52, 53, 57, 59, 64, 84, 86, 88,
  89, 90, 91, 92, 96. Missiles F1's "separated only by the 19 two-draw builds" (row 64) becomes 143.
- **Left.** Nothing in S2b. The moved rows wait in S2c and H2a as their notes say.
- **Review:** Tier B (plan 0066 Phase 1). Judgment calls to check: (1) missiles row 3 raised whole: the do entry is
  shown by `MF0`'s row number and the frame's return against D3's end branches, not by a logged call target; (2)
  catalogue row 44 raised whole on one `(n, calc3)` = (21, 2) for the group sizes, the stepping shown over eight
  vectors; (3) missiles row 30 raised with no new tool, from two kept outputs (C4's `MC.pierce` and S2a's stat-328
  rise); (4) missiles rows 54, 55, 56 moved to b rather than kept a-logs, as no logged line holds the terms; (5) row
  89's remainder routed d-none (the hit functions' draws are the catalogue's), rows 4, 50, 52, 53 to b (H2a); (6) the
  58 `DMG` packets of rows without a damage function whose words change between the build and `COMBAT_ApplyDamage`
  (monster owners, `2026-11-15-s2b-check.txt` DMG) are left unexplained and no row rests on them.

### 2026-11-15 — S2b lane check (architect, Tier B, `lane/n66f`): accept with fixes (4)

- **Verdict:** accept with fixes, 4 (overclaim 2, omission 1, stale cross-reference 1). Manifest passes `sha256sum -c`;
  the R4 counts (92 = 42 + 12 + 8 + 30; row 167 one of 11; do 109 361 and 634; do 129 62 of 347; the 14 other rows 0)
  match the kept `2026-11-15-s2b-check.txt` and `2026-10-30-skills-catalogue-check.txt` lines 215, 234–237
  (`2bd2b4fb…`); the 38 rows (3 + 29 + 6), the inventory totals (2 626; Phase 1 1 548, Phase 2 752) and the § 4 S2b, S2c
  and H2a cells agree against this branch's base; no `[L]` is added; every in-part row names its remainder's class and
  batch.
- **Fixes:** (1) overclaim: row 3 and the `MissileMoveCollide` raise: the log holds the do row number only, and the link
  from table entry 1 to `0x005AE1F0` is the thunk `0x005B0BC0`, still `[I]` in skills/0004; the scope is now stated in
  the row and in skills/0002 § 13; (2) overclaim: row 44 is one `(n, calc3)` = (21, 2), so its raise is the stepping, not
  the group-size formula at other pairs, stated in the row; (3) omission: the R4 contradiction had no backlog entry,
  filed to the spec-writer (`2026-11-15-architect-spec-writer-plan-0066-s2b-r4-caster-steps-reword`); (4) the symbol
  raise's text in skills/0002's Functions table and § 13 now agrees with the scope in (1).
- **For Tier A:** row 3 and the symbol raise to `C` on frame behaviour with the thunk still `[I]`; row 30's raise from two
  kept outputs with no new tool.

### 2026-11-15 — S2b Tier A ruling (architect, `lane/n66f`): accept with fixes (1)

Targeted ruling on the three points the Tier B check left, not a full re-review.

- **(1) Missiles row 3 and the `MissileMoveCollide` raise: the `C` stands.** `MF0` (0x005ADC97) and `MF1` (0x005ADCA9)
  bracket the indexed do call, so the logged result is the return of whatever table entry 1 reaches. The anchor is the
  static chain (Missiles `pSrvDoFunc` 1 → `g_MissileSrvDoFuncs[1]` = `0x005B0BC0` → `jmp 0x005AE1F0`); the corroboration
  is independent runtime behaviour that follows `sub_005AE1F0`'s own code order: the step's end before the decrement
  (65), the range's after it (823, frames run = frames left at creation), result = the nested end call's, `MissileDoFrame`
  freeing on 2 (the consumer agrees). That is evidence rule 3 plus reverser review-fixes 14. The thunk's `[I]` was only
  "not yet corroborated"; the same run corroborates that link, so a `C` callee behind an `I` jump was the inconsistency.
  **Fix (1, stale tag):** `sub_005B0BC0_MissDo01Thunk` raised to `C` in `re/symbols.csv` (evidence skills/0002) and in
  skills/0004's Functions table; skills/0002 § 13 and the row 3 note now state the chain and the ruling. The do-table
  statements of skills/0004 (entries 1–18) keep their `[I]`.
- **(2) Missiles row 30: the raise stands.** Both halves are kept and hashed (manifests pass) and were each accepted as `[C]`
  already: `MC.pierce` 1 066 ok / 0 in `2026-10-25-skills-check.txt` (the count from the local `Init(stat 328)` seed, the
  game seed checked unchanged in 31 391 creations), and S328 in `2026-11-10-s2a-check.txt` (1 660 separating pairs where
  the rise equals the requests between, 59 365 with no request and no rise). The row's sentence is their composition, so
  no new tool is needed.
- **(3) Missiles rows 31 and 96 (the brief's "84" is the callback row, which rests on `2026-11-15-s2b-check.txt` MC, not
  on p55a): confirmed.** `workspace/logs/p55a/check/check.txt` re-hashed `106aa180…`; its *separating pairs by set*
  section prints `mis-ef → mon-slot` 21, `mis-ef → mon-ef` 11, `mis-ef → plr-slot` 7, `mis-ef+mis-slot →
  plr-ef..mon-slot(4)` 7, and no pair with a missile set second other than the drain (87); the 7 object pairs (3 + 2 + 2)
  hold no missile. The rows' `[C]` part and their H7b remainder stand as written.
- **Verdict:** accept with fixes, 1 (stale tag 1). Merged `main` (S1e) into `lane/n66f`; the inventory totals recomputed
  from the 29 files' *Totals by class*: a-logs 668, a-run 358, b 394, c 390, c-emu 489, d 327 (d-2c 59, d-owner 68,
  d-edit 23, d-none 177), 2 626; Phase 1 1 547, Phase 2 752 (inventory README § 1 and § 3).

### 2026-11-15 — Phase 1 batch S3a, part 1 of 2 (reverser-static, `lane/n66g`): checker built and run; resume note

- **Done.** New check tool `tools/quests_s3a.py` (`6531b66c…`, stdlib, read-only; imports `tools/quests.py`'s model,
  which stays unchanged at `b6dfb1a3…`, the hashed checker behind the three runs' kept outputs) over the 54 kept logs:
  the 45 of run:2026-10-17-quests, run:2026-10-18-quests2 and run:2026-10-19-quests3, `p47h-x-wpact5r-0` and the 8 of
  `p47b-run.lst`, with their installed and written saves. Kept output `workspace/logs/quests/sweep2-s3a/s3a-check.txt`
  (`9134a7c7…`, `SUMMARY mismatches=4 checks=4070 logs=54`, the 4 being the C4 contradiction below) and
  `s3a-static.txt` (`dd50e017…`: one `E8` call to `QUESTS_TimersRun`, at 0x0052D920; `g_ItemUseFns` rows 0–2) under
  `sweep2-s3a/manifest.sha256` (passes from that directory); inputs in
  `workspace/logs/quests/manifest-sweep2-s3a-inputs.sha256` (`510c8807…`, 128 lines: 54 logs, 74 saves; passes from
  `workspace/logs/quests/`); development outputs in `sweep2-s3a/dev/` (`manifest-dev.sha256`). No game, no Ghidra.
- **Not done yet (part 2):** the inventory rows' notes, the totals, the findings addenda (quests experiments under the
  three runs; quests/0001 and 0002), `re/symbols.csv` raises, `tools/test_quests_s3a.py`, the Tier B request.
- **Contradicted (for Phase 3 and the review), from the kept check:**
  1. progression C4 (row 49): the first-join restore map is per quest, not the one map C4 gives. Quest 13 (word 14)
     maps b2 → (+0x0B, +0x0C) = (1, 2), b3 → (5, 5), b4 → (6, 5) (0x0059D557–0x0059D5A3; x-talk2 logged +0x0B = 5 for
     b3); quest 19 (word 21) does not restore on b4 (0x005BB4BC–0x005BB4C9; x-talk3, x-talk3b, h-talk3 logged
     +0x0B = 0). The 4 mismatches.
  2. travel Outputs (row 86, "quest event 3 for every level change"): every same-act level change is followed by one e3
     (0x00543BB7) naming the old and new level (341: 101 waypoint, 115 warp, 122 portal, 3 resurrection; a portal used
     in a town raises one more inside the use), but none of the 87 act changes (40 by NPC, 47 by waypoint) raises an e3.
     Progression word 4's "the e3 level-40 branch then finds state 7" (an act change into 40) needs a re-read.
  3. progression row 196 (the five Khalim items removed at completion): x-orb's written save lost `qf2 ` but kept
     `qey qhr qbr` (no `qf1 ` held). Read `0x005BB850` before filing it: the pass may remove only some codes, or the
     `0x005678A0(1)` test may hold.
- **Row decisions reached (part 2 writes them into the rows; spec lines at `b5999f5e`):**
  - *Raised whole:* progression 8, 18, 98, 130, 231, 262 (site 0x00588491: the spec's 0x00588496 is the return),
    304 (call 0x0058E4CB); travel 2, 8, 9, 10, 11, 12.
  - *Raised in part* (the `[C]` part first; the remainder's route after "/"): progression 4 (cadence; the caller by the
    raw scan, objdump to confirm / c), 7 (ids, tables / the "NPC-introduction" role), 13 (Set/Clear: 430 QS and 38 QC
    next-old pairs / GetState → c S3c), 16 (ClearSteps at the rewards of words 1, 20, 25, 35, not 2, 4, 6, 9, 27; the
    other bits kept / the 2–11 clear: no QK met a step bit → a-run H3a), 34 (order, inits, rows 7/29 and 24's +0xE0 /
    callbacks and private data), 39 (e10: 0x00543CA2, force 1, act filter 0, 32 / "after the item loop", "+0x0C" →
    H3f), 42 (e10 32, re-dispatched e0 at 0x005457D4 28, e4 force 0 in 7 `due` / e5 → H3f), 56 (the reward halves /
    the completing half → H3b), 58 (222 talks: e0, e11s with 28 re-dispatched e0, e2 / the store order, the client's
    pick), 63 (e0, e2, e3, e10, e11 by the logged NPCs / kills, operates, item events → H3b, H3f), 65 (24 589 equal
    pairs, 56 after a QGS, 3 in brackets, 0 elsewhere / the player-seed half), 75 (c-talk1 +1, x/h-talk1 +1 beside a
    level-up's +1 / the timer → H3b), 125 and 184 (the talk half: 0xFD, 0x1D2 / first join and 0x1D1 → a-run H3a), 132,
    141 (the clear / "no setter" → c S3c), 182, 190 (first join 48/6 / the reporter half → b H3c), 210 (2 / the arm
    without b13 → c S3c), 237 (+2 in x/h/c-talk4), 260 (one class-511 unit per game in 6 logs / the InitFn and no
    draw), 305 (object 40's callbacks / quest 31's state move: the one 0x4E46 met the quest switched off → a-run H3a),
    307 (orb broken → pass / whole orb, level 101 → a-run H3a), 312 (155 and 210 pass sides / refusals, 367 → H3e), 313
    (the operator's path, joiner w18 b0 clear / first-joiner path → a-run H3a, game-wide → d-2c), 322 (QGS sites inside
    their events / created units); travel 3, 4 (g_ItemUseFns[2].use = 0x005BE290; check Misc pSpell 2 for tsc, tbk),
    5, 6, 7, 17, 20 (size 3 step 1 with the walk 62 moved; size 2 step 1 62 moved / step 5 and the walk: all in place,
    the walk-free control agrees in 62), 22, 34 (code 0: 148, and 7 level-0 packets with no level change / codes 1–3
    → H3e), 35 (type 0, 106 field arrivals / 133–136), 37, 38, 58, 63 (e3 iff in town, 122), 69 (114 UnitInteract warps
    within 4.5 / refusals; one warp from 0x00582027 at 8.1), 70 (gate iff destination in the set, 115), 71 (100's pass),
    83, 84 (check word 10 in x-meshif), 85; README 1, 2.
  - *Moved:* progression 54, 67 (Warriv message 1 never reported), 151 (no 0xBA), 152, 200, 201 (check the fired
    variants in the kept `quests2-check.txt`: 0x251 with b7 set and 0x24D with b8 clear seem never met), 217 (the orb
    wrote w18 b0, b13; w21 had b0 and no b4), 270, 271, 272, 301 (progression already ≥ 5d + 5 in every save) → a-run
    H3a; 55 → b H3c (no line at `QUESTS_NpcHasQuest`); 57 (7 TMX, all return 1) → b H3b; 276 → b H3f (the bonus list is
    not saved); 225, 308 → b H3e; 243 → d-none (the classic client has no message 0x4E20); 96: check x-act's word 4 and
    the e3 into 40, likely a-run H3a; travel 48 (ActStale fires on 145 of 206 town departures and 16 times not after
    one: needs a `TownLevelLeave` line), 67, 68 → b H3e; travel 19, 60 (no separating case) → c-emu (a step-5 and walk
    emulation of `COLL_FindFreeNear`; a batch for the architect to name). Contradicted: progression 49, travel 86 (above).
- **Resume (part 2, a fresh lane on `lane/n66g`):** re-run `tools/quests_s3a.py check $(cat
  workspace/logs/quests/sweep2-s3a/s3a-logs.lst)` (byte-identical to `s3a-check.txt`), confirm the open items above
  (row 96, 196's read, 200/201's variants, Misc pSpell, T84's word 10, row 4's objdump count), add a test file, write
  the rows, the totals (merge `main` first), the addenda, the symbol raises (review-fixes rule 14), and the log entry
  with the Tier B request.

### 2026-11-15 — Phase 1 batch S3a, part 2 of 2 (reverser-static, `lane/n66g`): done, 87 of 87 settled

- **Done.** Resumed from the note above after merging `main` `f56ab708` (S1e, S2b) at `973cb300`. `tools/quests_s3a.py`
  revision 1 (`6531b66c…`) re-run over `s3a-logs.lst`: byte-identical to `s3a-check.txt` (`9134a7c7…`, `SUMMARY
  mismatches=4 checks=4070 logs=54`). Revision 2 (`cd33719e…`) adds notes only and `static` reads; its check output
  `s3a-check-r2.txt` (`f3116c95…`) keeps every revision 1 line, with `s3a-static-r2.txt` (`f1996df1…`) and
  `s3a-objdump.txt` (`2670cffb…`) under `workspace/logs/quests/sweep2-s3a/manifest-r2.sha256` (`d4862ce0…`, passes from
  that directory); development outputs in `dev2/` (`manifest-dev2.sha256`). New `tools/test_quests_s3a.py` (5 tests,
  OK). Record: the [S3a addendum](../findings/quests/experiments.md#addendum-2026-11-15-plan-0066-batch-s3a-the-kept-quest-logs-re-checked-lanen66g)
  under run:2026-10-19-quests3, with pointer lines under the other two runs and the p47 travel sessions;
  [quests/0001 § 18](../findings/quests/0001-progression.md#18-plan-0066-batch-s3a-the-kept-quest-logs-re-checked-2026-11-15-lanen66g)
  and [quests/0002 § 16](../findings/quests/0002-travel.md#16-plan-0066-batch-s3a-the-travel-lines-re-checked-2026-11-15-lanen66g).
  No game, no Ghidra.
- **Open items of part 1, settled:** row 4's caller: one `E8` at 0x0052D920 by objdump as by the raw scan, no absolute
  reference; row 196: `0x005BB850` is called only through `PartyForEach` when `UnitPartyId` ≠ 0xFFFF
  (0x005BBB30–0x005BBB49), and the operate removes the operator's `qf2 ` itself (0x005BBA23), so x-orb's save is
  explained and part 1's contradiction 3 is withdrawn; rows 200/201: word 19's writes are 0x251 with b7 clear (x-talk3,
  h-talk3) and 0x24D with b8 set (h-talk3) only; travel 4: Misc's `pSpell` 2 rows are `tbk` and `tsc` only; travel 84:
  x-meshif wrote word 10 b0, b13 beside word 15's (0x005468FB, 0x00546905); row 96: every word 4 = 0 joiner wrote b14
  on the waypoint act change (row 95's path) and x-act's joiner had w4 b0.
- **Rows** (each with a dated S3a note in its *Route* cell): **raised** 13 (progression 4, 8, 18, 98, 130, 262, 304;
  travel 2, 8, 9, 10, 11, 12); **raised in part** 51 (progression 7, 13, 16, 34, 39, 42, 56, 58, 63, 65, 75, 125, 132,
  141, 182, 184, 190, 196, 210, 231, 237, 260, 270, 272, 305, 307, 312, 313, 322; travel 3, 4, 5, 6, 7, 17, 20, 22, 34,
  35, 37, 38, 58, 63, 69, 70, 71, 83, 84, 85; README 1, 2), the `[C]` part and the remainder's class and batch in each;
  **moved** 21: progression 54, 67, 96, 151, 152, 200, 201, 217, 271, 301 → a-run (H3a), 55 → b (H3c), 57 → b (H3b),
  225, 308 → b (H3e), 276 → b (H3f), 243 → d-none; travel 48, 67, 68 → b (H3e), 19, 60 → c-emu (S3e, proposed);
  **contradicted** 2 (progression 49, travel 86). S3a holds 66 statements.
- **Contradictions** (Phase 3; backlog to the spec-writer):
  1. progression C4 (row 49): the first-join restore is per quest. Quest 13 restores b3 as `+0x0B` = 5 and quest 19
     does not restore on b4 (the 4 `MISMATCH` lines); as read, quest 13 maps b2 → (1, 2), b3 → (5, 5), b4 → (6, 5)
     (0x0059D557–0x0059D5A3) ([backlog](../backlog/2026-11-15-reverser-spec-writer-plan-0066-s3a-contradictions.md)).
  2. travel Outputs (row 86): an e3 follows every same-act level change (341 of 341) and none of the 87 act changes
     (40 by NPC, 47 by waypoint); progression word 4's "the e3 level-40 branch then finds state 7" is re-read with it
     ([backlog](../backlog/2026-11-15-reverser-spec-writer-plan-0066-s3a-travel-e3.md)).
  3. In part, found in part 2: word 37's entry levels (rows 270, 272): the code tests 113 or 114 for b3
     (0x00589DAB–0x00589DB3) and 121 to 124 for b14 (0x00589EBB–0x00589EC4); the logs met 113 (3) and 123 (2), the
     two levels the spec's lists drop (in the first backlog entry).
- **Symbols** (review-fixes rule 14): `QUESTRECORD_SetState`, `QUESTRECORD_ClearState` (next-old pairs),
  `COLL_FindFreeNear` (1 102 results reproduced), `ITEMUSE_TownPortal` (the field branch's pair and `+0x48`, 62) and
  `sub_0054B830_NpcTravelMove` (40 other-act calls) raised to `C` in `re/symbols.csv` (5 rows) and in the Functions
  tables of save/0002, drlg/0005 and quests/0002; quests/0001's Functions row of `QUESTS_TimersRun`/`TimerAdd` set to
  `C`, as `re/symbols.csv` already had it.
- **Totals** recomputed from the 29 inventory files' rows against `main` `f56ab708`: a-logs 647, a-run 368, b 402,
  c 390, c-emu 491, d 328 (d-2c 59, d-owner 68, d-edit 23, d-none 178), 2 626; Phase 1 1 528, Phase 2 770 (inventory
  README § 1, § 3, § 4: S3a 66; S3e 2, proposed; H3a 37, H3b 55, H3c 29, H3e 34, H3f 35; the quests files' *Totals by
  class*).
- **New batch proposed (§ 4): S3e**, `COLL_FindFreeNear` step 5 and the walk (travel 19, 60), c-emu: the function run
  on the pinned image over a declared collision grid (the logged `FF0` inputs and room maps), with cases built so that
  the step-5 ring and the walk back each change the found cell, compared with `quests_s3a.py`'s `free_near_walk`.
- **Ready for re-tagging (Phase 3, spec-writer)**, spec lines at `b5999f5e`, match by text: whole, progression rows 4
  (line 36), 8 (74), 18 (141), 98 (583), 130 (772), 262 (1386), 304 (1553) and travel rows 2 (29), 8 (35), 9 (73), 10
  (74), 11 (75), 12 (76); split, the `[C]` half each row's note names, progression rows 7, 13, 16, 34, 39, 42, 56, 58,
  63, 65, 75, 125, 132, 141, 182, 184, 190, 196, 210, 231, 237, 260, 270, 272, 305, 307, 312, 313, 322, travel rows 3,
  4, 5, 6, 7, 17, 20, 22, 34, 35, 37, 38, 58, 63, 69, 70, 71, 83, 84, 85 and README rows 1, 2; rewritten, progression
  row 49 (C4) and travel row 86, with rows 270 and 272's level lists.
- **Review:** Tier B (plan 0066 Phase 1). Judgment calls to check: (1) rows 4 and 8 raised whole: the tick = frame // 20
  at 14 timer lines (frames 567 to 7 500) with the increment inside the pass (0x00543E2D) is what separates "every 20th
  frame" from "every frame", not the run frames alone; (2) rows 141 and 262: x-newchar's first join (record not ready)
  logged no clear and its second used the e14 callback; 262 raised whole on "each game's join clears", 141 in part;
  (3) row 196 raised in part on a static read of the party gate plus the save, remainder d-2c; (4) rows 270 and 272
  filed as contradicted in part from the code reads and five logged writes; (5) rows 182 and 231 in part (the per-NPC
  flags are not logged), where part 1 had 231 whole; (6) travel 19 and 60 to c-emu with S3e proposed; (7) remainder
  routes part 1 left unstated, set here: progression 7 → d-none, 34, 49 (other quests), 260 → c (S3c), 58, 63, 65 → b
  (H3c), travel 3, 6, 17, 83 → b (H3e), 7 → c (S3c); (8) row 63's game-seed steps inside 14 reward e11s are left
  unattributed (H3c); (9) row 313's first-joiner path: 45 joiners had w18 b0 but none warped into 100.

### 2026-11-15 — Phase 1 batch S3a, Tier B lane check (architect-check, `lane/n66g`)

- **Verdict:** accept with fixes, 4 (misread 1, tool not kept 1, miscount 1, omission 1). Merged `main` `7b7f20e9`
  (plan 0069 Phase 1a) into `lane/n66g`; the only conflict was the inventory README (totals, two bullets), resolved.
- **Fixes.**
  1. *Misread:* rows 270 and 272 were filed "contradicted in part". The spec already holds `[C]` rows for "e3 entering
     level 123" (b14) and "e3 entering level 113" (b3), and its `[I]` rows ("entering 121, 122 or 124", "entering 114")
     name the levels the logs did not meet; the code tests (121 to 124, 113 or 114) agree with them. Nothing is raised
     and nothing is contradicted: both rows moved a-logs → a-run (H3a, as row 271), the item dropped from quests/0001
     § 18, the experiments addendum and the backlog entry (which now holds one contradiction, C4). S3a 66 → 64
     statements, 21 → 23 moved, raised in part 51 → 49; H3a 37 → 39; the progression file's totals a-logs 73 → 71,
     a-run 38 → 40; the log entry above keeps the lane's text (history), this entry corrects it.
  2. *Tool not kept:* `manifest-r2.sha256` failed `sha256sum -c`: `s3a-check-r2.txt` had been rewritten (860 lines, with
     the `P152`/`P217`/`P270-P272` write notes the rows cite) after the manifest was made for the 720-line output, and
     `tools/quests_s3a.py` had been edited since (`ef1e8339…`, not the `cd33719e…` cited). The manifest now lists the
     860-line output (`abfacb18…`; re-run from the current tool, byte-identical; manifest `e462dd3a…`); the 720-line
     output (`f3116c95…`) is kept as `dev2/s3a-check-r2-dev3.txt` and added to `manifest-dev2.sha256`; the hashes and
     the line count are corrected in the experiments addendum. All three manifests and the inputs manifest pass.
  3. *Miscount:* the catalogue file's *Totals by class* still read a-run 202, b 94 after plan 0069 Phase 1a's 30 moves
     (its README row had 172, 124). Corrected; with fix 1's two moves the totals are recomputed below.
  4. *Omission:* travel row 85 raised in part with no run anchor ("as row 58"); `s3a-check.txt` T58, T58/T85 added.
- **Totals** recomputed from the 29 files' *Totals by class* after merging `main` `7b7f20e9`: a-logs 645, a-run 340, b
  432, c 390, c-emu 491, d 328 (d-2c 59, d-owner 68, d-edit 23, d-none 178), 2 626; Phase 1 1 526, Phase 2 772 (inventory
  README § 1, § 3, § 4).
- **Judgment calls.** (1) Rows 4 and 8 raised whole: accepted. The 7 adds and 7 runs show tick = frame // 20 at frames
  that are not multiples of 20 (so the tick is not the frame count), the increment is inside the pass and the one
  caller is 0x0052D920 by two tools; that separates "every 20th frame" from "every frame". (2) Rows 262 and 141:
  accepted; 262's claim is the two callbacks' clears (53 at e13, one at e14), 141's remainder is the "no setter" half.
  (3) Row 196 in part: accepted, with the counterfactual ("had the pass run ...") read as the code's own branch, not
  logged; one solo game, the party half stays d-2c. (4) Rows 270, 272: not a contradiction (fix 1). (5)–(9): accepted as
  stated (rows 182 and 231 in part; travel 19 and 60 moved; the remainder routes; row 63's steps unattributed; row 313).
  Checked against the kept output: 4 `MISMATCH`, 341 same-act changes (3 p41, 61 + 61 portal, 115 warp, 101 wptr), 122
  portal uses, 87 act changes (40 by NPC, 47 by waypoint), 115 gate checks, 430 and 38 next-old pairs, 222 talks with 28
  re-dispatched e0, 32 e10, 24 589 / 56 / 3 seed observations. The rev 2 output keeps every rev 1 line (no `<` line in
  `diff`); `python3 -I tools/test_quests_s3a.py`: 5 tests OK. The 9 e3 lines the T86 act-change note lists for
  waypoint changes name the next same-act change (old level = the act change's new level), not the act change.
- **Symbols:** the 5 raises agree between `re/symbols.csv` and the Functions tables (save/0002 two rows, drlg/0005's
  `C / I` row, quests/0002 two rows, quests/0001's timer row); no other table lists them at `I`.
- **S3e: for Tier A / architect ruling.** The plan's Phase 1 rules do not let a lane add a batch (the plan names batches
  for the owner, e.g. H1h `proposed`); S3e's § 4 row is well formed (2 statements, travel 19 and 60, c-emu, method
  ADR-0015/0021/0029, status `proposed`, matching `quests-travel.md`'s 2 c-emu rows) and stays `proposed`.

### 2026-11-15 — Phase 1, batches S4a and S4b (reverser-static, `lane/n66h`): done, 41 of 41 settled

- **Done.** Both batches in one lane, no game, no Ghidra. New tool `tools/sweep2_s4ab.py` (`a82294bc…`; sections `static`,
  `tables`, `econ`, `price`, `use`), run once under a 4 GB scope: `workspace/logs/n66h/check.txt` (`11b81eef…`, 293 lines,
  `S4 total bad=0`), `manifest.sha256` (`78f02ccc…`) passing from `workspace/logs/n66h`; development outputs in `dev/` with
  their own manifest. Second tools: r2 and the raw-byte scan (`tools/xrefscan.py`) where `tools/economy_scan.py` (objdump)
  or Ghidra read first; objdump (`tools/sweep_s4b.py`'s walker) where Ghidra read first. Inputs: the 38 economy and economy2
  claim logs, the three kept inventory-2 logs, the 12 H2a logs, each under its run's manifest. Record:
  [items/experiments § Addendum 2026-11-15](../findings/items/experiments.md#addendum-2026-11-15-plan-0066-batches-s4a-and-s4b-new-checks-over-the-kept-economy-and-inventory-logs-and-static-second-sources-lanen66h)
  under run:2026-10-17-economy, with pointer lines under run:2026-10-19-economy2 and run:2026-11-04-inventory-2; dated notes in
  items/0011 § 5 and skills/0002 § 2. Every row's *Route* cell carries its dated S4a or S4b note.
- **S4a (22): raised 10, raised in part 12, moved 0.** Raised: 2 (the NPC class tests, r2), 6 (`PLAYER_GoldCap`, r2 and the
  at-cap branch at L 30), 24 (`cost mult` ≤ 896 over 357 rows), 39 and 86 (one item per `ItemRepairAll`; repair-all's 21
  calls return inside `RepairCost`), 44 (depth 6 through 0x0055C5C0, each edge in r2), 45 (the 22 repair sites, 1 in 651
  quest functions), 57 (the gold-drop callers, Baal's included), 67 (`NpcHealDead` unreferenced), 81 (the +2 is the nested
  drop's). In part, the remainder and its home in each row: 3 (client inputs → d-none), 21 (quality 9 → d-none), 40 (the
  charge branch → a-run H4a), 49 (the over-cap branch → a-run H4b), 53 (`mul=` 1536, 2048 → a-run H4a; the order → d-none),
  60 ("written once" → b H4b), 65 (the cost sent → b H4b), 68 (melee-only, combat/delivery's own rows), 75 (the
  `magicarrow` test, `UseAmmo`'s gate, the monster sites' functions → a-run H4a), 77 (`calc2`/`calc3` → b H4b), 78 (the
  none-queued test → a-run H4a; the signed division, non-positive `r` only → d-none; Tier B fix), 84 (charges after a use → a-run H4a).
- **S4b (19): raised 15, raised in part 4, moved 0.** Raised: 1, 2 (the handlers, logged and read), 5 (do 113's two calls),
  11 (178 `PKT` lines at the table's rows, return address 0x0054D81A), 13 and 64 (the return read by neither frame), 17 and
  59 (the gate's pushes 0, 0, 1, no draw past 0x0057EFF2, the seed unchanged 175 of 175), 29, 30, 31, 58 (no draw in the
  three bodies), 41 (no `GroupClear` under kind 3), 53 (`key`'s row and `KeyConsume`'s two callers), 56 (the three getters,
  no abs32 pointer). In part: 9 (FIFO, clients, the lock → c, S7f, sim/frame row 27), 28 (which side of `ItemUse` → b H4c),
  35 (the non-player branch → b H4c), 57 (the client rule → d-none).
- **Contradicted in part: economy row 40** (F1, line 485): the "13 `nodurability` crossbows of a `Repair` type" are 12
  crossbows and the Phase Blade `7cr` (`swor`). A label, not a behaviour: Phase 3 rewords it, and the archivist corrects
  ItemTypes.md line 181 (backlog [`2026-11-15-reverser-spec-writer+archivist-plan-0066-s4a-s4b-corrections`](../backlog/2026-11-15-reverser-spec-writer+archivist-plan-0066-s4a-s4b-corrections.md),
  which also carries skills/0002's monster `useAmmo` sites). No owner decision is needed.
- **Symbols:** `PLAYER_GoldCap`, `sub_0055B060_PlayerGiveGold`, `sub_0054B1E0_Pkt20UseInvItem`, `sub_0054B560_Pkt26UseBeltItem`
  raised to `C` in `re/symbols.csv` and in items/0011's and items/0012's Functions tables (review-fixes 14).
- **Totals** recomputed from the 29 inventory files' *Totals by class* after merging `main` `684332ee`: a-logs 645, a-run 340,
  b 432, c 390, c-emu 491, d-2c 59, d-owner 68, d-edit 23, d-none 178 = 2 626; Phase 1 1 526, Phase 2 772, blocked 328. No
  row moved, so README § 1 and § 3 are unchanged; § 4's S4a and S4b rows record the outcome.
- **Ready for Phase 3 (spec-writer), spec lines at `b5999f5e`, match by text.** items/economy whole: 63, 134, 326, 473,
  523, 535, 632, 718, 851, 985; split (the `[C]` half each row's note names): 71, 276, 483 (with the correction), 564, 587,
  677, 715, 767, 806, 819, 825, 875. items/use whole: 36, 37, 40, 129, 137, 152, 289, 293, 296, 402, 488, 494 (its
  "indirect callers and table pointers are unfollowed" becomes "no abs32 pointer to any of them"), 503, 504, 534; split: 115,
  282, 357, 495. Economy 535's "642 quest functions" is 651 by today's symbols, one site either way.
- **Review:** Tier B (plan 0066 Phase 1). Judgment calls to check: (1) row 6 raised whole on two tools' reading of
  `imul eax, eax, 0x2710` plus the at-cap equality at one level (L 30), the other levels only bounded; (2) row 17's raise
  rests on the operands and the reach from 0x0057EFF2, not on the unchanged seed, which a draw gated on state 42 would give
  as well (review-fixes 10); (3) rows 3, 21, 57 and 78 route a remainder to d-none (client display, quality 9 with no stock
  source, client rule, a positive `r` only) rather than to a harness batch; (4) row 75's six monster sites: the values
  raised, the functions left `[I]` because skills/0002's five entries do not hold them; (5) row 45 raised with today's 651
  quest functions where the spec says 642 (the filter is the same; `re/symbols.csv` grew); (6) row 60's "written once" kept
  `[I]` although the only other `+0x6A` byte store is a client record copy, since a displacement search cannot see a store
  through another base (0038 S3b ruling 4's limit); (7) four symbol raises, two of them handlers whose identity (entry =
  table row, opcode's packet) rather than return the run checks.

### 2026-11-15 — Phase 1, batches S4a and S4b: Tier B lane check (`lane/n66h`): accept with fixes (3)

- **Verdict:** accept with fixes, 3 (overstated tag 2, misrouted remainder 1). Gate green. `main` `684332ee` already merged,
  nothing moved; totals recomputed from the 29 files' *Totals by class*: 2 626 (a-logs 645, a-run 340, b 432, c 390, c-emu 491,
  d-2c 59, d-owner 68, d-edit 23, d-none 178), unchanged.
- **Mechanical.** `manifest.sha256` and `dev/manifest-dev.sha256` pass `sha256sum -c`; `tools/sweep2_s4ab.py` (`a82294bc…`) rerun
  under a 4 GB scope is byte-identical to `check.txt`; the three price controls fail as stated (196, 375 and 1 135 mismatch
  lines, all in their one quality; stock 0). The contradiction: the parsed Weapons, Armor and Misc tables give 13 `nodurability`
  bases of a `Repair` type, 12 of type `xbow` and 1 of type `swor`. The backlog entry is well formed. The four symbol rows agree
  between `re/symbols.csv` and the Functions tables.
- **Fixes.** (1) items/0011's `PlayerGiveGold` row said "drop the overflow" under `C`, where the over-cap split is row 49's
  `[I]` remainder: scoped. (2) items/0012's two handler rows carried the length and fields ("13 bytes: guid, x, y") under `C`
  where the run checks the entry, opcode and return only (use.md § B keeps them `[I]`): scoped. (3) Row 78's remainder was
  routed whole to d-none: the none-queued test is reachable on stock (a second loss inside one interval), so it goes to a-run
  H4a; only the signed division for a non-positive `r` is d-none (stock `rep-dur` values in the affix, unique and rune tables
  are all positive).
- **Judgment calls.** (1) row 6 accepted: the cap's form is code (two tools) and the equality at L 30 runs it; the other levels
  are bounded only, as the row says. (2) row 17 accepted: the second source is objdump's read of the pushes and of the test at
  0x0057EEFB (`cmp [ebp+0xc], 0; je 0x0057EFF2`, no draw before it or from it), the unchanged seed only agrees. (3) rows 3, 21
  and 57 d-none accepted as presentation or no stock source (precedent stats-states 18, items/0010 qd 42 "no stock quality 9
  item", items/0008's disabled tempered rows); row 3 and 57 are client presentation, reachable but out of the spec's scope: for
  Tier A to confirm that reading of d-none. (4)–(7) accepted.

### 2026-11-15 — S3e and d-none for client presentation: architect rulings (`lane/n66r`)

Two targeted rulings left by the S3a and S4a/S4b Tier B checks, not a review.

- **Ruling 1, S3e is folded into S7e.** A Phase 1 lane does not add batches, and a two-statement batch is not worth a lane
  of its own. Travel 19 and 60 are the same method family as S7e: `COLL_FindFreeNear` (0x0064DEA0) is already emulated by
  the ground-emu cases (run:2026-11-04-ground-emu, size 1, step 1, mask 0x801) that S7e names. The fold adds step 5 and
  the mask 0xC01 walk back, on cases built so that the ring and the walk each change the found cell, compared with
  `tools/quests_s3a.py`'s `free_near_walk`. § 4: the S3e row is removed and S7e goes from 61 to 63 statements. Phase 1
  now has 36 batches, not 37. `quests-travel.md` rows 19 and 60 now carry batch S7e, and the remainders of rows 20 and 22
  point to S7e. Classes are unchanged, so the totals stay at 2 626. findings/quests/0002-travel.md line 694 still says
  "S3e, proposed". The S7e lane updates it with its addendum, since the file belongs to the reverser.
- **Ruling 2, client presentation stays in d-none with its own label.** d-none's "no observable on stock" does not fit a
  client-only presentation claim: stock play reaches it and a client logger could observe it. d-edit fits worse, because
  stock data reaches the claim. The plan still runs no batch for it, because the specs cover the simulation and not the
  client. So the claim stays in the d-none column, with no new column and no change to the totals, but its *Route* cell
  begins `out of scope: client presentation`. The label covers the client half only. A server clause in the same line
  keeps its own route. In Phase 3 the line stays `[I]` or becomes a scope note. The rule is written in the inventory
  README's class table and in a note under § Conventions. It was applied to stats-states 18 (the precedent, a d-none
  row) and to economy 3's remainder. In row 3, "the server's call decides" is a server claim and does not take the label.
  Economy 57 is raised whole and has no d-none remainder, so the S4a check named it by mistake. Economy 21 (quality 9)
  and 53 (`mul=` multiples of 256) are true no-stock-source cases and stay plain d-none. quests/progression 11 and
  stats-states 26 are reading notes and also stay plain d-none. Totals unchanged: a-logs 645, a-run 340, b 432, c 390,
  c-emu 491, d-2c 59, d-owner 68, d-edit 23, d-none 178 = 2 626.

### 2026-11-15 — Phase 1 batch S5a, part 1 of 2 (reverser-static, `lane/n66j`): 70 of 81 settled; resume note

- **Done.** No game, no Ghidra. New tool `tools/sweep2_s5a.py` (`104ce037…`; sections `combat`, `skills`, `handlers`),
  run under a 4 GB scope: `workspace/logs/n66j/check-combat.txt` (`8301a8c5…`, 422 lines, `S5a total bad=0 checker=0`),
  `check-skills.txt` (`c17d62f4…`), `check-handlers.txt` (`f51b54c2…`), `manifest.sha256` (`f7ddd85e…`) passing from
  `workspace/logs/n66j`; development outputs in `dev/` with their own manifest. The `combat` section reruns
  `tools/combat.py`'s Checker unchanged on `c37r-run2.lst`, `p47h-run.lst` (with its recorded `--no-shield-log`) and
  `p47b-run.lst` (74 logs, 0 mismatches) and adds nine checks and the counters. Second tool r2 for `MonSkillAttackDo`'s
  calls and `COMBAT_QueueHit`'s copy. Record:
  [combat/experiments § Addendum 2026-11-15](../findings/combat/experiments.md#addendum-2026-11-15-plan-0066-batch-s5a-part-1-new-checks-over-the-kept-combat-and-skills-logs-lanen66j)
  under run:2026-10-16-combat. Every settled row's *Route* cell carries its dated S5a note; the 11 others say "not
  settled in part 1".
- **Raised 26:** README 1, 11 (c, r2 call order), 2, 13, 19, 20, 24, 26 (skills/missiles C2, C4, E1, F1 already `[C]`
  on the same runs: re-tags), 17, 37; to-hit 1, 29, 32, 33; damage 21, 28; reductions 11, 20, 24, 25; delivery 5, 27,
  30, 45, 59, 67.
- **Raised in part 27**, the remainder and its home in each Route cell: README 4 (zeroing → c), 12 and 39 (CB divisor
  10, P 25 → S5e), 14, 18, 21, 34 (crit steps 2–3, frozen weapon terms → S5fe), 27 (the finisher loop → S5fe), 30
  (handlers 3, 30, 31 → H5b), 32 (→ S5fe and H5b), 40 (→ d-2c); to-hit 10 (→ S5e), 16 (range test → H5b), 17 and 30
  (undelivered bits → H5b), 31 (three draws → S5e); damage 6, 9, 13, 14, 15, 34 (→ S5e); delivery 4, 23, 24 (→ H5b),
  49, 64 (→ H5b).
- **Moved 17:** to b (H5b) 14 — README 36, to-hit 18, reductions 6, delivery 2, 3, 25, 32–37, 56, 58: `STA` is
  logged at `STATE_ApplyTimed` only, so the kept logs hold none of the stun, cold, freeze, poison, shatter or burning
  states; the evaded result word is never delivered; `MS0` has no missile stats; no delivery had kill handlers. To
  c-emu (S5e) 3 — damage 3, 22 (the unarmed clamp, never reached), 10 (no build had an event-3 handler).
- **Not settled (part 2) 11:** README 5 (the flag bits), 15 and delivery 57 (a durability and get-hit draw model:
  the kept DU/GH seed steps are in `check-combat.txt`), README 35, 38, damage 1, 29, 30, 33 and player/party 12 (the
  `MonAttackStats` output model), delivery 28 (`manahit`: 493 monster attacks with stats 62/63 set, `check-combat.txt`).
- **New, not a contradiction:** 537 missile deliveries carry result bit 0x4000 (0x4001), which to-hit C1's list does
  not name. Backlog [`2026-11-15-reverser-spec-writer+reverser-plan-0066-s5a-result-bit-0x4000`](../backlog/2026-11-15-reverser-spec-writer+reverser-plan-0066-s5a-result-bit-0x4000.md)
  (with combat/README line 433's stale "no two-client run yet").
- **Totals** after `main` `aa6ceb9c` (the lane's base; nothing to merge): a-logs 628, a-run 340, b 446, c 390, c-emu
  494, d-2c 59, d-owner 68, d-edit 23, d-none 178 = 2 626; Phase 1 1 512, Phase 2 786, blocked 328. § 1, § 4 (S5a,
  S5e 49 → 52, H5b 11 → 25) and the six files' *Totals by class* updated.
- **Symbols:** none raised; no run here compares a logged return of a named function not already `C`.
- **Judgment calls for the review:** (1) README 1 and 11 raised by r2's call read alone (class c inside an a-logs
  row), since no log can tell `MonSkillAttackDo`'s hits from the plain attack's; (2) the re-tag raises (README 2, 13,
  19, 20, 24, 26) stand on skills/missiles' reviewed `[C]` on the same runs, with this lane's own counts where its tool
  reads them; (3) damage 21 raised whole on the owner's step asserted at `MSX` (7 734) plus `MonCritDouble`'s melee
  `[C]`, the doubled missile packet itself not compared; (4) to-hit 29's separating count is the 6 838 phys-0 events
  in logs whose player blocked other missiles, not a per-event block chance; (5) H5b grows to 25 with rows that need
  new logger lines (still deferred under the threshold).
- **Resume note.** Part 2 (same lane or a fresh one on `lane/n66j`): the 11 rows above, then **S5b** (24 rows, not
  started). Rerun `tools/sweep2_s5a.py combat …` as recorded to get the DU/GH and stat-62/63 counters; the MAS model
  reads MonStats/MonLvl as monsters/stats § H states and compares `MAS1` stats over the 19 780 `mas` events.

### 2026-11-15 — Phase 1, batches S4c and S4d, paused (reverser-static, `lane/n66i`): resume note

- **Paused** at the owner's reboot, early: no row is settled and no inventory row, finding, symbol or total is changed.
  No game, no Ghidra was started (no process to stop).
- **Tool state.** New `tools/sweep2_s4cd.py` (development, not yet run, no kept output): sections `invlogs` (rows 3, 8,
  29/61, 31, 85/88 over the four kept logs of run:2026-11-04-inventory and -inventory-2) and `invstatic` (rows 2, 4,
  5/6, 16, 18, 21, 35/60, 76/93–95, 78, 79/80/90/100, 82, 97: r2 and the raw-byte scan of `tools/xrefscan.py` beside the
  objdump `static.txt` of run:2026-11-04-inventory-emu and -ground-emu; the objdump walker of `tools/sweep_s4b.py` and
  r2's LCG search beside Ghidra's `rcg-summary.txt`). Not yet written: `stlogs`, `ststatic`, `tables` (S4d, and S4c
  rows 54, 71).
- **Leads found while reading (provisional, not checked by a kept output):** the packet table rows of 0x17..0x25 and
  0x63 by r2 equal the spec's § D handlers; the page sizes at 0x0074479C and 0x007447B4 read 13 × 1 and 16 × 1; the
  objdump walker finds no draw in the direct closures of 0x00555DA0, 0x0066A670, 0x00558A10, 0x00641530, 0x0063C600,
  0x0063B950, and one `RNG_RangeB` call (0x00624563) under 0x00558AA0, as Ghidra; at A1's three sites the third push
  is loaded from `[reg + 0x70]` (whether each base is the game is not yet traced: likely a remainder); the cursor item
  is not on Inventory `+0x0C`'s list, so mode 4 is seen only at `IPG` of a 0x17 drop. Remainder homes planned: H4d for
  the inventory rows, H4e for the stats rows.
- **Resume (a fresh lane on `lane/n66i`):** finish the tool (S4d sections over `s1017-run.lst` and `p47h-run.lst`,
  under `systemd-run --user --scope -p MemoryMax=4G`; Misc `autobelt`, Sets params, Skills `aurastat`, States bits;
  `g_ShrineEffects` by r2; xrefs of `STATE_ApplyTimed`, `STATE_GroupClear`; `PlayerSwapWeapons` by r2), run it once into
  `workspace/logs/n66i/` with a manifest, add `tools/test_sweep2_s4cd.py`, then the rows, the addenda (items and stats
  experiments), the symbol raises, `main` merged before the totals, and the log entry with the Tier B request.

### 2026-11-15 — Phase 1, batch S4c done and S4d part 1 of 2 (reverser-static, `lane/n66i`): 39 of 73 settled; resume note for S4d part 2

- **Done.** No game, no Ghidra. `tools/sweep2_s4cd.py` finished for S4c and S4d's static rows (`271e96c8…`; sections
  `invlogs`, `invstatic`, `ststatic`, `tables`; `tools/test_sweep2_s4cd.py`, 8 tests), run once under a 4 GB scope:
  `workspace/logs/n66i/check.txt` (`fdf66219…`, 337 lines, `S4 total bad=0`), `manifest.sha256` passing from
  `workspace/logs/n66i`; development outputs in `dev/` with their own manifest. Second tools: r2 (`pD`, `pxw`, `p8`, its own
  `/x` search for the multiplier, 852 sites equal to objdump's) and the raw-byte scan where Ghidra or objdump read first;
  objdump's walker over Ghidra's closure lists, every image body walked. A call's stack arguments by r2, walking back from
  the call and skipping an inner call's pops. Inputs: the four kept inventory logs under their manifests; the excel `.txt`
  tables; `expfield.d2`'s header. Records:
  [items/experiments § Addendum 2026-11-15 (S4c)](../findings/items/experiments.md#addendum-2026-11-15-plan-0066-batch-s4c-new-checks-over-the-kept-inventory-logs-and-static-second-sources-lanen66i)
  under run:2026-11-04-inventory, pointer lines under -ground-emu and -inventory-2;
  [stats/experiments § Addendum 2026-11-15 (S4d part 1)](../findings/stats/experiments.md#addendum-2026-11-15-plan-0066-batch-s4d-part-1-of-2-static-second-sources-and-full-table-checks-lanen66i)
  under run:2026-10-17-stats; dated notes in items/0013 § 1 and stats/0002 § 7. Every settled row's *Route* cell carries its
  dated note.
- **S4c (29): raised 21, raised in part 7, contradicted in part 1, moved 0.** Raised: 2, 3, 4, 5, 6, 8, 16, 21, 35, 54, 76,
  78, 79, 80, 82 (with a refinement: the `RNG_` calls, now scanned, add `NPC_MenuAction`'s `RNG_RangeB` at 0x0057A3CC), 90,
  93, 94, 95, 97, 100. In part, the remainder and its home: 18 (the 13 server calls' field reads → c, S4e), 29 and 31 (the
  handlers' refusals, none met → c-emu, S4e), 61 (the cursor cleared, not logged → c-emu, S4e), 71 (ownership → d-2c),
  85 ("sent to every player" → d-2c), 88 (a held item's `+0x24` → a-run, H4d).
- **Contradicted in part: inventory row 60** (§ G, line 360): the `0x22` handler returns 3 for an owned item, not 0 (the
  stub leaves the `&len` out word at 5; 0x0054B3BD–0x0054B3CB, r2 and objdump). The drain discards it: no outcome changes,
  "no split on the server" stands.
- **S4d part 1 (10 of 44): raised 4, raised in part 5, contradicted in part 1, moved 0.** Raised: states 16, 34, 42, 51.
  In part: aggregate 34 (the counts of the logged chains → a-logs, part 2), aggregate 38 (a name in two tables → d-edit),
  states 5 (`UNIT_HasState`'s types, `STATE_Set`'s bit 3 → c, part 2), states 14 (the elemental appliers' list shape → c,
  part 2), states 31 (the stop at a blank and the unwritten 0 → d-none: no stock row has a stat after a blank).
- **Contradicted in part: states row 46** (line 467): the remove callback's closure reaches 122 drawing functions through
  `PetLimitRefresh` (0x0056E960 → `PetLimit` → `PetRemove` → `PetUnitRelease` → `MonSetMode` → `MonAttackStats`); the group
  clear, death purge and mode drop hold none. Whether an expiry takes the path stays `[I]` (→ c, part 2). Backlog for both
  contradictions: [`2026-11-15-reverser-spec-writer-plan-0066-s4c-s4d-corrections`](../backlog/2026-11-15-reverser-spec-writer-plan-0066-s4c-s4d-corrections.md).
- **Symbols:** none raised. The run compares call sites, arguments, bytes and table cells, not a logged return of a named
  function (review-fixes 14's scope); judgment call (6) below.
- **Totals** recomputed from the 29 inventory files' *Totals by class* after merging `main` `82eaa099`: a-logs 645, a-run 340, b 432,
  c 390, c-emu 491, d-2c 59, d-owner 68, d-edit 23, d-none 178 = 2 626. No row moved class (remainders are noted in the
  *Route* cells, as S4a/S4b did), so README § 1 and § 3 are unchanged; § 4's S4c and S4d rows record the outcome.
- **Ready for Phase 3 (spec-writer), items/inventory lines at `b5999f5e`, match by text.** Whole: 42, 43, 44, 75, 76, 78,
  136, 206, 242, 322, 567, 570, 576, 577, 579 (reworded for the `RNG_` scan), 643, 655, 656, 657, 661, 692. Split: 139,
  236, 238, 360 (with the correction), 365, 483, 620, 640. stats/states whole: 193, 418, 447, 532; split: 93, 181, 397,
  467 (with the correction); stats/aggregate split: 448, 520.
- **Resume (S4d part 2, a fresh lane on `lane/n66i`):** 34 rows: aggregate 2–4, 6, 8–13, 16–17, 19, 23–26, 29, 31–32,
  36–37, 39, 41–42 (a-logs), 5 (flag `0x4`'s writer and reader), 40 (the `aura` bit's readers); stats/README 1; states 13,
  17, 23, 32, 37, 41 (a-logs); and the part-2 remainders of aggregate 34, states 5, 14, 46. Add a `stlogs` section to
  `tools/sweep2_s4cd.py` over `workspace/logs/stats/s1017-run.lst` and `p47h-run.lst` (557 MB: one pass per log, under
  `systemd-run --user --scope -p MemoryMax=4G`), reusing `tools/stats.py`'s parsers (TREE, LNK/ULK with `ra2`, STA1, EQR,
  SCB, PAS, TK, ISC); write the kept output under a new name (`check-part2.txt`), not over `check.txt`.
- **Review:** Tier B (plan 0066 Phase 1), for S4c whole and S4d part 1. Judgment calls to check: (1) rows 29, 31, 61's
  handler remainders routed to S4e's emulation family rather than a harness batch; (2) row 18's field-read remainder to c,
  S4e; (3) row 16 raised with "the game" as the functions' first argument by the handler and `InvPlaceItem` signatures,
  not traced further; (4) the closures checked over Ghidra's own lists, so a function both tools miss (an indirect call) stays
  outside, as the lines say; (5) the two contradictions rest on two tools' reading of one path with no case (row 60's return
  is discarded; states 46's path is reachable code, not a logged draw); (6) no symbol raised: candidates would be
  `g_ShrineEffects` (its 10 entries read by r2 equal to the spec) and `sub_0055E9A0_UnstackStub`; (7) states 31's remainder
  to d-none, where the seven stock rows with a stat or calc alone are written by other skill functions.

### 2026-11-15 — Phase 1, batch S4d part 2 of 2 (reverser-static, `lane/n66i`): done, S4d 44 of 44 settled

- **Done.** No game, no Ghidra. `main` `aa6ceb9c` merged first (merge `8a511842`, no conflict). `tools/sweep2_s4cd.py`
  (`59d67950…`) gains `ststatic2` (objdump next to r2 or the raw bytes) and `stlogs` (one pass per log of
  `s1017-run.lst` and `p47h-run.lst` through `tools/stats.py`'s checker, `85e14b94…`, with observers and two model
  controls); `tools/test_sweep2_s4cd.py` 13 tests; `all` still reproduces part 1's `check.txt` byte for byte. One kept
  run under `systemd-run --user --scope -p MemoryMax=4G` (57 s): `workspace/logs/n66i/check-part2.txt` (`a2cbf09c…`,
  105 lines, `S4 total bad=0`; the checker 0 mismatches over both runs), `manifest-part2.sha256` passing from
  `workspace/logs/n66i`; development outputs under `dev/manifest-dev-part2.sha256`. Record:
  [stats/experiments § Addendum S4d part 2](../findings/stats/experiments.md#addendum-2026-11-15-plan-0066-batch-s4d-part-2-of-2-new-checks-over-the-kept-stats-logs-and-static-second-sources-lanen66i);
  dated notes in stats/0001 § 1 and § 9, stats/0002 § 1 and § 2. Every row's *Route* cell carries its note.
- **S4d part 2 (34): raised 12, raised in part 13, raised in part and contradicted in part 4, contradicted in part 2, not
  raised 3, moved 0.** Raised: aggregate 3, 5, 6, 8, 12, 19, 32, 39; states 13, 32, 37, 41. In part, the remainder and its
  home: aggregate 10 (`+0x0C`, `+0x38` → c, S4e), 11 (`AddStat`'s removal at 0 → c-emu, S4e), 16 (op 7 → c-emu, S4e),
  17 (the stat-point addition → c, S4e), 23 (107, 126, the item events → c, S4e), 25 and 26 (refusal, gem mods, broken,
  the dual-wield re-link → a-run, H4e), 31 (ethereal → c, S4e), 36 (func 0 → c, S4e), 37 (the lookup → c, S4e), 40 (each
  reader's effect → c, S4e); states 17 (the dead branch, one bit left on → a-run, H4e), 23 (mode 4 with the bonus →
  a-run, H4e). Not raised: aggregate 9 (no `exp` state logged → a-run, H4e), 13 (no `bl` 11/12, no `DMG` → c, S4e), 24 (no
  clamp write → a-run, H4e).
- **Contradicted in part (5):** aggregate 2 and stats/README 1 (the pickup unlinks without `ITEMS_DetachFromOwner`, 260
  cases), aggregate 4 (the unit list's `0x2` is the drop-on-mode marker), aggregate 41 (the refresh's closure reaches 122
  drawing functions; no seed moved in 972 windows), aggregate 29 and 42 (136 the commonest gap in 22 of 28 logs, not
  every session); and states 5's remainder (`UNIT_HasState` answers for types 0, 1, 3: missiles, not objects). Backlog:
  items 3–7 added to [`2026-11-15-reverser-spec-writer-plan-0066-s4c-s4d-corrections`](../backlog/2026-11-15-reverser-spec-writer-plan-0066-s4c-s4d-corrections.md).
- **Part-1 remainders:** aggregate 34 raised (the swap's direct calls touch `bl` 4 and 5 only, 76 swaps); states 5
  contradicted in part, its `+0xC8` half raised; states 14 (the poison lists' shape raised; burn, cold, freeze → c, S4e)
  and 46 (`PetLimitRefresh` on every player expiry, 149 freeing expiries drew nothing; a pet's release → c, S4e) keep a
  remainder.
- **Symbols:** none raised (judgment call 13).
- **Totals** after merging `main` `aa6ceb9c` (merge `8a511842`), from the 29 files' *Totals by class*: a-logs 645,
  a-run 340, b 432, c 390, c-emu 491, d-2c 59, d-owner 68, d-edit 23, d-none 178 = 2 626, unchanged: no row moved class
  (remainders in the *Route* cells, as S4a–S4d part 1). README § 4's S4d row records the outcome.
- **Ready for Phase 3 (spec-writer), stats lines at `b5999f5e`, match by text.** stats/aggregate whole: 82, 91, 92, 94,
  133, 325, 438, 532; split: 51, 90, 122, 128, 301, 306, 372, 383, 389, 425, 431, 448, 511, 516, 536, 544, 593 (the
  contradictions with their correction); stats/README split: 54; stats/states whole: 178, 400, 429, 443; split: 93, 181,
  206, 298, 467.
- **Review:** Tier B for S4c and S4d whole, requested by a dated paragraph on
  [`2026-11-15-reverser-architect-review-plan-0066-s4c-s4d-part1`](../backlog/archive/2026-11-15-reverser-architect-review-plan-0066-s4c-s4d-part1.md).
  Judgment calls of part 2: (8) the flag rows (aggregate 4, 6, 9, 41) count only lists the apply made: a refresh returns
  the list it found (0x0056EACC), 2 993 such returns left out; (9) the controls of rows 16 and 17 are counted per checked
  write, where the stock model matched every write; op 8/9's control differs on every write, which separates but says
  nothing beyond "own is non-zero"; (10) the pickup path filed a contradiction of the entry-point rows rather than a
  refinement of H2; (11) aggregate 29/42's "every session" filed contradicted in part on a count of all gaps, bursts
  included (the spec's count is not kept); (12) aggregate 5 raised with the setter list incomplete (7 register-argument
  `STATLIST_Alloc` calls untraced), as the claim is the flag's meaning; (13) no symbol raised: the run compares fields,
  flags and call chains, and `SKILLS_RefreshPassive`'s logged return (row 39) is compared with the list's own 351, not a
  model; (14) agg 41's contradiction rests on the walker's closure with r2's LCG sites agreeing, no case, as states 46.

### 2026-11-15 — Phase 1, batch S6a part 1 (reverser-static, `lane/n66k`): 73 of 76 settled; resume note for S6a part 2 and S6b

- **Done.** No game, no Ghidra. `main` is `712c49e6`, the lane's base (nothing to merge). New tool `tools/sweep2_s6ab.py`
  (`f223ad12…`; sections `logs`, `static`): one pass per log of the 131 logs of `2026-10-30-anim-p3b-all4.lst`, running
  `tools/anim.py`'s `Checker` unchanged as the control (its `CHECK anim` line equals the kept
  `2026-10-30-anim-p3b-check.txt`'s) and 22 observers on the same lines; `static` reads the classified return sites
  with r2 and the int3-padding entry, and `GetHitRoll`'s callers from the raw bytes. One kept run each under
  `systemd-run --user --scope -p MemoryMax=4G` (50 s): `workspace/logs/n66k/check.txt` (`0b8f36b7…`, 52 lines,
  `S6 total bad=0 control_bad=0`) and `static.txt` (`d0e848ac…`), `manifest.sha256` (`50f61c5e…`) passing from
  `workspace/logs/n66k`; development outputs under `dev/manifest-dev.sha256`. Record:
  [anim/experiments § Addendum S6a](../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k)
  under run:2026-10-30-anim-p3b; dated notes in anim/0001 § 7.1 and the `MonAttackFrame` bullet, anim/0003 § 6.2.
  Every settled row's *Route* cell carries its S6a note.
- **S6a part 1 (73 of 76): raised 16, raised in part 44, contradicted in part 1, not raised 12, moved 0.** Raised: 1, 2,
  3, 7, 13, 25, 42, 51, 53, 58, 60, 97, 100, 106, 109, 132 (3, 51 and 53 by run:2026-10-30-frame-emu-2's `tick`, `run`
  and `qat` families, an emulation already kept). In part, with the remainder's home in each *Route* cell: 4, 5, 6, 8,
  21, 22, 23, 24, 29, 36, 38, 39, 46, 54, 56, 57, 59, 61, 62, 63, 73, 76, 77, 79, 88, 92, 95, 96, 98, 101, 104, 107,
  108, 110, 112, 114, 117, 119, 124, 125, 126, 127, 128, 130. Not raised, the log lacks the separating case: 12 and
  115 (no request in `(E, E + 5]`), 26 (no chained object pair), 35 and 52 (kinds 2 and 12 dispatched unlogged), 43
  (no re-scan separates), 44 (no window crosses a rate change), 49 (no step past the record), 85 (the stat source),
  120 (missile hits), 122 (no `PlayerModeAllowed` draw), 133 (no frozen dispatch).
- **Contradicted in part: timing row 75** (§ I2, line 550): a code-2 event of a no-skill A1 or A2 strikes no hit (2 248
  of 2 248 dispatches), code 1 in 18 160 of 18 637; the test that drops code 2 is not read (→ c, S6c). Backlog
  [`2026-11-15-reverser-spec-writer-plan-0066-s6a-corrections`](../backlog/2026-11-15-reverser-spec-writer-plan-0066-s6a-corrections.md),
  with three Phase 3 notes (row 38's `RescheduleSkip` `+0x44 = (T − p) << 8`, row 117's "none of its refusals is
  reached" against all4's 781 refusals, row 42's 9 restarts by this rule against the spec's 15).
- **Symbols:** `sub_00553C70_RescheduleSkip`, `sub_00553DC0_RescheduleAt` (their logged lists against E3: 819, 74) and
  `sub_0057EDD0_PlrModeLeaveOk` (26 574 logged returns against M4's block, 781 refusals) raised to `C` in
  `re/symbols.csv` and in anim/0001's and anim/0003's Functions tables (review-fixes 14).
- **Totals** from the 29 files' *Totals by class* at `712c49e6`: a-logs 645, a-run 340, b 432, c 390, c-emu 491, d-2c
  59, d-owner 68, d-edit 23, d-none 178 = 2 626, unchanged: no row moved class (remainders in the *Route* cells, as S4a–S4d).
  README § 4's S6a row records part 1.
- **Ready for Phase 3 (spec-writer), anim/timing lines at `b5999f5e`, match by text.** Whole: 43, 44, 47, 54, 128,
  228, 366, 430, 438, 488, 490, 725, 739, 798, 830, 981. Split (the `[C]` half each row's note names): 50, 51, 52, 97,
  187, 193, 199, 219, 245, 319, 328, 335, 387, 448, 486, 487, 489, 494, 497, 504, 541, 554, 561, 579, 657, 686, 708,
  721, 730, 741, 775, 805, 826, 836, 853, 866, 887, 896, 945, 953, 958, 961, 971, 977; 550 with the correction.
- **Resume (part 2, a fresh lane on `lane/n66k`):** S6a rows 78 (`MonModeStartNeutral`'s requeue: open the plan 0052 ai
  logs' `AIN` lines, as the route says), 103 (`replay-skills` over the plan 0045 skills logs and the `PDS` kind-0 codes
  1 and 2), 105 (the `check --review` `rv-req` tallies); then S6b's 31 rows (movement 1–3, 7, 9–11, 15, 21, 23, 26, 27,
  29–32, 34–36, 38–42, 44; README 1–3, 9, 10, 12): add observers to `tools/sweep2_s6ab.py` (SR st 67 at run starts,
  the path speed per mode, PS0 windows' frames per point and ends, DR0 in town, the op-run2–6 turn pairs, knockback
  windows' first point and advance count, slow windows), keep the part-1 `check.txt` byte for byte (write part 2 as
  `check-part2.txt`), and reuse this run's `two-clocks`, `player-mode-end` and `start-sequence` counts for README 1, 2,
  9, 10, 12 where they cover them.
- **Review:** Tier B (plan 0066 Phase 1), requested by
  [`2026-11-15-reverser-architect-review-plan-0066-s6a-part1`](../backlog/archive/2026-11-15-reverser-architect-review-plan-0066-s6a-part1.md).
  Judgment calls to check: (1) rows 3, 51, 53 raised by citing an emulation run already kept and reviewed, with no new
  check of this lane; (2) "a unit's mode set" is attributed to the next unit lines in its frame (MSET's return is
  `SUNIT_SetMode`'s, one level up), so the caller identities (`PlayerModeEnd`, `MonSetMode`, the start functions) stay
  `[I]` in rows 4, 5, 39, 56, 63, 73; (3) rows 101 and 125–127 raised in part on records with the worked example's
  frames, speed and event (`SOSC1HS`, `SOSCSTF`, `PAGH1HS`), not the `HTH` records named; (4) row 75's contradiction
  rests on "no `GH` line of that attacker in the dispatch frame", where `COMBAT_GetHit` is logged on misses too
  (result 0), and the reason is not read; (5) K2 and K3 checked only where the rate is plain (no floor, cap or wrap)
  and K3 only for cast, get-hit and block; (6) the town of a player set is the last pilot `PLR` level, 262 sets between
  two levels left out; (7) row 6's player `kill` branch (33 hits with no mode-0 set) and row 92's two 75/95/100
  monsters are left in the remainder, not filed as contradictions.

### 2026-11-15 — Phase 1, batch S6a part 2 and batch S6b (reverser-static, `lane/n66k`): done, S6a 76 of 76 and S6b 31 of 31 settled

- **Done.** No game, no Ghidra. Merged `main` `c48797e7` first (clean, `d0e5df0c`). `tools/sweep2_s6ab.py`
  (`0ab4596e…`) gains sections `logs2` (one pass per log of the 131 logs of `2026-10-30-anim-p3b-all4.lst`: the
  `Checker` control unchanged, then 15 part 2 observers on the same lines) and `ai78` (the plan 0052 ai logs); its
  `logs` section reproduces part 1's `check.txt` byte for byte. One kept run each under `systemd-run --user --scope -p
  MemoryMax=4G` (logs2 46 s): `workspace/logs/n66k/check-part2.txt` (`8a0baffc…`, 130 lines, `S6b total bad=94
  control_bad=0`: the 74 unexplained stat-67 units and 20 longer point segments, both in remainders) and `ai78.txt`
  (`9c066151…`); `manifest-part2.sha256` (`9d65825c…`) passes from `workspace/logs/n66k`; development outputs under
  `dev/manifest-dev2.sha256`. Record:
  [anim/experiments § Addendum S6a part 2 and S6b](../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-part-2-and-batch-s6b-new-tallies-over-the-same-131-logs-lanen66k).
  Every settled row's *Route* cell carries its note.
- **S6a part 2 (3 rows):** 78 not raised (the ai logs date a neutral start only at an AI command, where the think's
  delay decides: 12 of 12 next decisions off `aidel`), 103 not raised (no kept tally separates codes 3/4 or the bit-6
  re-run → c, S6c), 105 raised in part (the request-to-start tallies for get-hit, block, S2–S4; the client's rule →
  d-none). **S6a whole (76): raised 16, raised in part 45, contradicted in part 1, not raised 14, moved 0.**
- **S6b (31): raised 11, raised in part 18, not raised 2, moved 0.** Raised: movement 1, 9, 27, 30, 34, 39, 41, 42, 44;
  README 2, 9. In part (remainder's home in each cell): movement 2, 3, 7, 10, 11, 21, 23, 26, 29, 31, 32, 35, 38, 40;
  README 1, 3, 10, 12. Not raised: movement 15 (no `Velocity`-0 classic S1–S4 call logged → c-emu, S6e) and 36 (the
  logger's `ss` lacks Slows Target's state 24 → a-run, deferred). No contradiction.
- **Backlog:** two items added to
  [`2026-11-15-reverser-spec-writer-plan-0066-s6a-corrections`](../backlog/2026-11-15-reverser-spec-writer-plan-0066-s6a-corrections.md):
  (5) a lead on monsters/stats § G's `fanatic` (stat 67 175, not 195, at `Velocity` 4, 2 units), (6) movement D2's open
  question answered (the 6 offset-1 turns are later phase-11 sets).
- **Symbols:** none raised. The run compares stat values and rate-call outputs, not a function's logged return
  (review-fixes 14's scope); `RunVelocityStat`, `PathPlanKnockback` and `MonModeVelocity` stay as they are.
- **Totals** from the 29 files' *Totals by class* after merging `c48797e7`: a-logs 645, a-run 340, b 432, c 390,
  c-emu 491, d-2c 59, d-owner 68, d-edit 23, d-none 178 = 2 626, unchanged (remainders in the *Route* cells).
  README § 4's S6a and S6b rows record the outcome.
- **Ready for Phase 3 (spec-writer), anim/movement and anim/README lines at `b5999f5e`, match by text.** Movement
  whole: 38, 115, 246, 260, 293, 330, 341, 343, 374; split: 41, 73, 99, 118, 122, 208, 221, 237, 259, 269, 277, 298,
  325, 338. README whole: 51, 113; split: 49, 79, 117, 134. Timing split: 794.
- **Review:** Tier B, the existing request
  [`2026-11-15-reverser-architect-review-plan-0066-s6a-part1`](../backlog/archive/2026-11-15-reverser-architect-review-plan-0066-s6a-part1.md),
  annotated to cover S6a whole and S6b. Judgment calls to check: (1) the knockback point's attacker position is the
  last pilot `PLR` line before the hit (575 of 576 match; the 1 left as a possibly stale position, not a
  contradiction); (2) the 74 monsters whose neutral stat 67 fits no mod model are left in row 11's remainder, not
  filed against monsters/stats; (3) "after the creation frame" defines a monster's post-mod rate calls; (4) row 26's
  converse (653 windowed sets to neutral with no step in the frame) is tallied, not explained, and the claim raised
  is the end on arrival only; (5) row 30 raised on the 75 drain turns with the 6 others explained by line order and
  phase, not by a code read of `PlrModeMoveFrame`; (6) rows 78 and 103 kept not raised instead of routed to a session.

### 2026-11-15 — Phase 1 batch S5a, part 2 of 2 (reverser-static, `lane/n66j`): done, S5a 81 of 81 settled; S5b not started, resume note

- **Done.** No game, no Ghidra. New tool `tools/sweep2_s5a2.py` (`946081ff…`), which reruns part 1's `sweep2_s5a.py`
  (`104ce037…`, unchanged: Checker 0 mismatches, its nine checks 0 bad) and adds a `MonAttackStats` output model, the
  durability and get-hit draw models, result-bit and build checks and the `manahit` drain; run under a 4 GB scope on
  the same three run lists: `workspace/logs/n66j/check-combat-p2.txt` (`d5a594af…`, 214 lines, `S5a2 total bad=0
  checker=0 part1-bad=0`), the r2 reads in `p2/`, `manifest-p2.sha256` (`77a83aae…`) passing from `workspace/logs/n66j`;
  six development outputs in `p2/dev/` with their own manifest (one later unkept revision's output, with a counter
  bug, was overwritten by the kept run and is not cited). Record:
  [combat/experiments § S5a part 2](../findings/combat/experiments.md#addendum-2026-11-15-plan-0066-batch-s5a-part-2-the-monattackstats-output-model-and-the-deliverys-boundary-draws-lanen66j);
  dated pointer bullets in combat/0001 § 12 and monsters/0004 § 9. Every row's *Route* cell carries its part-2 note.
- **Raised 4:** README 38 and player/party 12 (the expansion player-count bonus: `b` 16 at `/players 3`, 600 of 600
  separating; 56 at `/players 8`, 1 679 of 1 798; 0 in Normal at `n` ≥ 2, 5 216 of 6 444; the table read with r2);
  damage 1 and 29 (`MonAttackStats`' stats 19/21/22 in 19 750 of 19 750 calls, 1 030 `El` writes).
- **Raised in part 7**, remainder and home in each Route cell: README 5 (flag `0x2`, results `0x1`, `0x2`, `0x4`,
  `0x2000`; the other bits → H5b), README 15 and delivery 57 (the `DU` step counts 9 680 and the player defender's
  get-hit 25 669; roll values, the one `0x005CAED8` case, the monster defender's state tests → H5b), README 35 (the
  classic factors, 562 separating; `Align` = 1 → S5e), damage 30 (the `El` mode match; "the new mode" → H5b), damage 33
  (types 1, 2, 4, 5; the others never applied → H5b), delivery 28 (the `256·v` drain, 226 of 226, 138 separating;
  `El` type 7 → H5b, the `v << 22` wrap d-none on stock data). None of these remainders was added to H5b's or S5e's rows.
- **Also found:** `El2` applies with `El1`'s bounds (the mask `0x40 + e`) in 57 compared applications whose own cells
  differ (monsters/stats H1's code reading; `El3` not met); `b` scales the `El` length too (154 of 154 separating). For
  Phase 3 with the S5a rows.
- **S5a whole:** 81 rows, raised 30, raised in part 34, moved 17 (14 to b H5b, 3 to c-emu S5e). README § 4's S5a row
  updated.
- **Totals** after merging `main` `712c49e6` (merge `5cadc51d`), from the 29 files' *Totals by class*: a-logs 628,
  a-run 340, b 446, c 390, c-emu 494, d-2c 59, d-owner 68, d-edit 23, d-none 178 = 2 626, unchanged by part 2 (no row
  moved class); Phase 1 1 512, Phase 2 786, blocked 328.
- **Symbols:** none raised. `MonAttackStats` and `GetHitRoll` are already `C`; `sub_005A4F20_PlayerDmgBonus` and
  `g_PlayerDmgBonus` stay `I` (their return is not logged, only its effect at `n` 3 and 8; the `n` ≥ 9 branch is
  unmet); `COMBAT_DurabilityLoss` and `COMBAT_GetHit` stay `I` (step counts only; the roll values and the monster
  branch are not compared).
- **Judgment calls for the review:** (1) README 38 and player/party 12 raised whole on two logged player counts plus
  r2's read of the table for the others, the `8n − 16` branch being outside the row's `n` < 9; (2) a hireling's
  `MonAttackStats` checked against an offset learned at its first call (its MonStats cells give 0), so the alignment
  test that withholds `b` is not separated and stays `[I]`; (3) the `El` stats compared only for units whose first
  logged call held none (295 writes on enchanted minions excluded); (4) the get-hit model on a monster defender kept
  one-way (never more steps, 9 509), since states 1, 21, 54 are not in these logs; (5) the mode-change half of damage 30
  kept a counter (10 842 of 10 979 next-`EV0` modes equal), not a check.
- **Resume note (S5b).** S5b (24 rows, README § 4) is not started. A fresh lane on `lane/n66j` (after merging `main`):
  its rows are static second-tool reads, r2 `axt` and call or store scans (stat-id immediates, callers, writers of
  packet fields, `UNIT_AddEvent`) and full-table checks of Skills `ItemEffect`, `srvprgfunc`/`prgstack`, States
  `meleeonly` and ItemStatCost `itemeventfunc1`, recorded as a findings/combat/0001 addendum with run id
  `2026-xx-xx-sweep2-s5b`. README 4's zeroing remainder (part 1) uses the same method. Part 1 already read
  `srvprgfunc1`–`3` over Skills.txt (combat/experiments S5a part 1, last bullet), which S5b's `srvprgfunc` row can cite.

### 2026-11-15 — Phase 1, batch S5b (reverser-static, `lane/n66j`): done, 24 of 24 settled

- **Done.** No game, no Ghidra. Merged `main` `c48797e7` first (merge `c6c26e16`, no conflict). New tool
  `tools/sweep2_s5b.py` (`4ad860dd…`; sections `callers`, `stats`, `stores`, `tables`, `closures`): the raw-byte
  call/pointer scan of `tools/xrefscan.py`, r2 for every asserted instruction, the reduction and handler tables and
  the LCG byte search, the objdump listing for bodies, closures and store scans, and full-table checks of States,
  Skills, ItemStatCost, Events and MonStats. Run under a 4 GB scope: `workspace/logs/n66j/s5b/check-s5b.txt`
  (`3b8c2822…`, 2 517 lines, 29 checks, `S5b total bad=0`) and `totals-s5b.txt`, `manifest-s5b.sha256`
  (`30f6ea65…`) passing from `workspace/logs/n66j/s5b`; fourteen development outputs in `dev/` with their own
  manifest. Record: [combat/0001 § 18](../findings/combat/0001-formulas.md#18-plan-0066-batch-s5b-static-second-sources-run2026-11-15-sweep2-s5b)
  under [run:2026-11-15-sweep2-s5b](../findings/combat/experiments.md#run2026-11-15-sweep2-s5b). Every row's *Route*
  cell carries its dated S5b note; README § 4's S5b row updated.
- **Raised 17:** README 3, 8; to-hit 2, 4, 19; damage 2, 19 (with a correction), 27, 32; reductions 1; delivery 1,
  20, 26, 38, 54, 65, 66.
- **Raised in part 7**, the remainder and its home in each Route cell (none added to a batch's rows): to-hit 13 (the
  two formulas: the shrine half b, the client half d-none, out of scope: client presentation), to-hit 21 (four
  register-mask sets → c), damage 17 (the non-zero entry formula, d-none), delivery 21 (the entries' draws → S5fe),
  delivery 29 (`UnitKilled` → `MonDeathEvent` through the pointer at 0x006E2260 → c), delivery 50 (game-code indirect
  calls; handlers 19 and 27 reach draws through `STATE_ApplyTimed`'s queue path → S5fe), delivery 51 (`A1PathSearch`'s
  callback calls → c).
- **Also:** README 4's S5a remainder (the callers' zeroing) raised: 33 `memset(&packet, 0, 0x70)`, do 67 with `EAX` 0,
  three pointer packets traced to them; README 4 is raised whole and S5a reads raised 31, in part 33, moved 17.
- **Found, for Phase 3:** to-hit's stat list lacks 350/351 (Holy Shield's state-101 list in `UNIT_GetDefense`);
  damage's lacks 31 (stat 120's defence step); `MeleeHitTest`'s callers are start and do functions (32 sites, 30
  functions); the only stock event-3 handler is Shiver Armor's (Skills 50 `auraevent1`, handler 3), which draws, so
  damage step 8's "thorns-like … none logged with a draw" needs that; 292 `firegolem` is the one stock `noRatio`
  class with an El attack (damage E's min = max = 0); a fourth `ToHitRoll` caller sits in an unreferenced function at
  0x005A88E0.
- **Totals** after merging `main` `c48797e7` (`totals-s5b.txt`, from the 29 files' *Totals by class*): a-logs 628,
  a-run 340, b 446, c 390, c-emu 494, d-2c 59, d-owner 68, d-edit 23, d-none 178 = 2 626, unchanged (no row moved
  class); Phase 1 1 512, Phase 2 786, blocked 328.
- **Symbols:** none added or raised (no logged return compared; the unnamed 0x005A88E0 and the helper entry
  `0x005D8B10` left unnamed).
- **Judgment calls for the review:** (1) a second tool's re-read of the same sites (r2 next to the Ghidra reading,
  with the raw-byte scan for exhaustiveness) taken as the second source for README 8, to-hit 19, delivery 26 and 38,
  as the rows' routes say; (2) damage 19 filed raised with a correction rather than contradicted: the spec's list is
  right about the defender's stat events, its "thorns-like … no draw" is the logs' scope, and skills/0003 § 3 already
  gives handler 3's draw (review-fixes rule 18); (3) the "no writer" raises (damage 17, 27) rest on frame-base store
  scans (a store to `[ebp − (X − off)]` for a `lea` base `X`) plus pointer stores in 97 direct callees, not on a data
  flow of the packet pointer; (4) delivery 50 and 51 keep `[I]` over unresolved game-code indirect calls (review-fixes
  rule 19) though the closures, with callbacks as edges, hold no draw; (5) delivery 65's "no test of the return"
  walks every path after each call to a full `EAX` write or a call whose callee writes `EAX` first.
- **Next:** S5b closes the combat static batches but S5e and S5fe (emulation). Tier B request
  [`2026-11-15-reverser-architect-review-plan-0066-s5a-part1`](../backlog/archive/2026-11-15-reverser-architect-review-plan-0066-s5a-part1.md)
  extended to S5a + S5b.

### 2026-11-15 — Phase 1, batch S6c (reverser-static, `lane/n66l`): done, 35 of 35 settled; S6e not started (resume note)

- **Done.** No game, no Ghidra. `main` `ccb26b81` is the lane's base (nothing to merge). New tool
  `tools/sweep2_s6c.py` (`6cc8ebc1…`, section `static`): raw-byte xrefs decoded by r2, r2 table dumps and range reads,
  `tools/sweep_s4b.py`'s objdump call-graph walker over the Ghidra RngCallGraph roots and stops, and full-table checks
  through `tools/anim_survey.py`, each against the kept plan 0050 first-tool output (`p50a-anim-scan.txt`,
  `p50b-setrate-xrefs.txt`, `p50b-setrate-callees.txt`, `p50d-calls.txt`, `p50a-rng-machine.txt`, `p50a-rng-modes.txt`).
  One kept run under `systemd-run --user --scope -p MemoryMax=4G`: `workspace/logs/n66l/s6c/check.txt` (`8665c322…`,
  114 lines, 26 checks, `S6C total bad=0`; a second run gives the same bytes), `manifest.sha256` (`6e2b20c2…`, passes
  from that directory); development outputs under `workspace/logs/n66l/dev/manifest-dev.sha256`. Record:
  [anim/experiments § Static addendum S6c](../findings/anim/experiments.md#static-addendum-2026-11-15-plan-0066-batch-s6c-second-tools-over-the-code-image-lanen66l);
  dated notes in anim/0001 (after the record table), anim/0002 § 5, anim/0003 (the walk base, § 8). Every settled
  row's *Route* cell carries its S6c note.
- **S6c (35): raised 12, raised in part 22, contradicted in part 1, not raised 0, moved 0.** Raised: timing 50, 55,
  65, 68, 71, 72, 94, 121; movement 12, 18, 37; README 5. In part (remainder in each cell): timing 14, 15, 27, 28, 31,
  37, 47, 48, 64, 66, 69, 70, 74, 86, 93, 131; movement 16, 19, 20, 25; README 6, 7. Contradicted in part: timing 67
  (§ I2 table, line 532: the GH and BL frame slot is 0x005A6DE0, `UNIT_CancelEvents(0, 0)`, not "—"). Two remainders go
  to S6e: timing 86's negative-`s` arithmetic and movement 19's step arithmetic (c-emu).
- **S6a remainders routed to S6c:** timing 4 (`g_PlayerEventFuncs[1]` = `PlayerModeEnd`), 39 (the schedule's 6 call
  sites and their cancel-first order), 56 (`PlrModeStartNeutral` for modes 1 and 5), 63 (the get-hit, block and skill
  start order) and 73 (`MonSetMode`'s order, the state-54 fatal, the mode-3 test) raised; 5's in part (each logged
  start being `MonSetMode`'s needs `SUNIT_AnimInit`'s callers, not scanned). Not taken here (no static route found in
  this lane's budget, cells unchanged): timing 6 and 107 (the town return and the kill branch), 75 (the code-2 drop: the
  frame function gets no code, `MonModeFrameEvent` passes only ECX and EDX, 0x005A7BD2–0x005A7BD6, so the drop is
  below `MON_MeleeHit` or in its gates, unread), 85 (the stat accessor), 103 (`+0xC4` bit 6's writers); movement 21, 26,
  35; README 12.
- **Backlog:** [`2026-11-15-reverser-spec-writer-plan-0066-s6c-corrections`](../backlog/2026-11-15-reverser-spec-writer-plan-0066-s6c-corrections.md)
  (the contradiction and five refinements: S4/DD frame slot and S3's `ret` end, `MonSetMode`'s `MonModeVelocity` and
  second `UNIT_SetUsedSkill`, the ten chart rows with no case, `MonStatsSpeeds` writing `i` back, `HandsRefresh`'s draws
  under the mode end).
- **Symbols:** two new `I` rows, `sub_005A6DE0_MonFrameCancelEvents` and `sub_005A7B30_MonModeNullRecord`, in
  `re/symbols.csv` and anim/0001's Functions table. None raised: the batch compares static reads, not logged returns
  (review-fixes 14's scope).
- **Totals** from the 29 files' *Totals by class* at `ccb26b81`: a-logs 645, a-run 340, b 432, c 390, c-emu 491,
  d-2c 59, d-owner 68, d-edit 23, d-none 178 = 2 626, unchanged: no row moved class (remainders in the *Route* cells).
  README § 4's S6c row records the outcome.
- **Ready for Phase 3 (spec-writer), lines at `b5999f5e`, match by text.** Timing whole: 414, 455, 530, 533, 536, 537,
  700, 927; split: 136, 141, 237, 243, 263, 324, 401, 407, 529, 531, 534, 535, 546, 644, 694, 979; 532 with the
  correction; S6a rows now whole: 50, 335, 486, 504, 541. Movement whole: 131 (with the refinement), 182, 313; split:
  151, 198, 202, 231. README whole: 89; split: 90, 101.
- **Review:** Tier B (plan Phase 1). Judgment calls to check: (1) "client" for the sites below 0x00520000 is left to the
  symbol names, `[I]`, so rows 14 and 93 are in part; (2) timing 67 filed as a contradiction (a scheduled mode's slot
  runs) while 69 and 70 (schedule 0, never queued) are refinements; (3) movement 12 raised on two tools reading the
  guard plus the full table, not moved to d-none; (4) movement 37 raised with `PathPlan` stopped, the replan's draws
  being movement G1's `[C]` replan line; (5) README 6 in part over `HandsRefresh`'s draws, filed as a refinement, not a
  contradiction.
- **Resume note for S6e (a fresh lane; S6e not started).** 34 rows (timing 9–11, 16–20, 30, 32–34, 40, 41, 45, 80–84,
  87, 89–91, 129; movement 4–6, 8, 13, 14, 22, 24, 43) plus the remainders routed to S6e: timing 21, 23, 24, 29, 36, 43,
  44, 46, 49, 61, 62, 86, 88, 96, 98, 128, 130; movement 2, 15, 19, 23, 31. Method as S1e's (`tools/ai_s1e_emu.py`, one
  `tools/ghidra.sh emuboundary` launch over all families, one memory spec, every test reversed alone as a control; R2:
  no declared callee return). Start from `tools/anim_rates.py`'s p50b emulation (`workspace/logs/anim/p50b-emu`,
  `bonus` and `advance` families) and `tools/animdata.py`. Families, cheapest first: `ANIMDATA_Find`/`Lookup` (absent
  and the 29 duplicate names), `UNIT_AnimAtEnd`, `UNIT_AnimStartFrame`, the advance with a start frame ≠ 0,
  `SUNIT_ScheduleModeEvents` (`UnitQueueEvent` an observed boundary; r = 0, no step, events past 0x90),
  `UNIT_AnimSetRate`'s edges (floors 15/25, block 1, cap, wrap, no path; `UNIT_AnimSetRecord`, `WeaponListsRelink2`
  and `PathSetSpeed` must run whole or the row returns to b), the four rate-class predicates, `HumanAttackFrames`,
  `MonStatsSpeeds`, `PathStepCollide` (0x0064FF90's room read: declare or return to b), `PathVelocityStep`'s wrap.
  The inventory README § 5 (anim) suggests splitting S6e into rate/schedule and animdata/seq/path if it runs long.
  Ghidra project `workspace/ghidra-n66l` is in place.

### 2026-11-16 — Phase 1, batch S6e part 1 of 2 (reverser-static, `lane/n66l`): 9 of 34 settled; resume note for part 2

- **Done.** `main` `7a3ef52e` merged into the branch at `8580cdcb` (plan-log keep-both). New tool
  `tools/anim_s6e_emu.py` (`5362890f…`), one `tools/ghidra.sh emuboundary` launch on `workspace/ghidra-n66l` (`-Xmx3G`,
  `MemoryMax=4G`), no observed boundary and no declared callee return (R2): every callee runs, the event queue and
  its pool among them. Four families, 11 624 cases, 0 mismatches, 0 stops, 0 unaccounted reads or writes; 65 controls,
  59 separating with `passed` 0, 6 with no observable (each named in the record). Record:
  [run:2026-11-16-sweep2-s6e](../findings/anim/experiments.md#run2026-11-16-sweep2-s6e); `workspace/logs/n66l/s6e/run/`
  (`check.txt` `fca5054c…`, `manifest.sha256` `0539fe07…`, 12 lines, passes from there; `cases` regenerates the case
  file byte for byte); development run under `workspace/logs/n66l/s6e/dev/` (`manifest-dev.sha256`), not cited. Dated
  notes in anim/0001 §§ 2, 7, 8 and anim/0002 § 3.
- **Rows settled (9): raised 6, raised in part 3.** Raised: timing 10 (the `0x90` scan bound), 17 (B2, with a
  refinement), 32 (`r = 0`), 33 (the bound and the full table), 34 (the `t = T` bump), 41 (F2). In part: 16 (none for
  an absent name; the fallback's values stay the loader's), 19 (the earlier record wins; the block order and the
  loaded file stay `[I]`), 89 (the predicates and the tables; the column names of the bytes read stay `[I]`).
  **Remainders raised:** timing 21 (the schedule's bound), 36 and 96 (E2's `k_f ≤ N` drop and no-step case, 1 115
  closed-form cases, 128 and 104 separating).
- **Corrections (refinements, the spec's text is Phase 3's):** (1) `ANIMDATA_Find`'s length fatal is inside the record
  loop: a long name in an empty block returns none; (2) monster SQ (14) is skill-dependent in both monster tables,
  which J3 does not list; (3) `AnimRateIsMove` and `AnimRateIsAttack` are fatal for unit types other than 0 and 1. Routed by
  [backlog](../backlog/2026-11-16-reverser-spec-writer-plan-0066-s6e-part-1-corrections.md); anim/0001 § 2's "fails
  fatally on a name … longer than 8" carries the dated refinement (rule 20; the spec's copy, timing line 157, is item 1).
- **Symbols:** none raised (an ADR-0015/0021 emulation over a declared image, review-fixes 14).
- **Totals** from the 29 files' *Totals by class* after the merge of `main` `7a3ef52e`: a-logs 628, a-run 340, b 446,
  c 390, c-emu 494, d-2c 59, d-owner 68, d-edit 23, d-none 178 = 2 626; no row moved class.
- **Ready for Phase 3 (spec-writer), timing lines at `b5999f5e`, match by text.** Whole: 105, 156 (with correction 1),
  286, 290, 296, 355. Split: 154 (the none branch `[C]`, the fallback's values `[I]`), 174 (the earlier record `[C]`,
  the block order and the loaded file `[I]`), 660 (the predicates' maps and the tables `[C]`, with correction 2; the
  column names `[I]`); remainder halves now `[C]`: 187 (the `0x90` bound), 319 and 721 (the `≤ N` clause and no-step
  case).
- **Review:** Tier B, together with S6c (the request is extended). Judgment calls: (1) row 33 raised on the emulated
  bound plus a full-table read of the one record over 0x90 frames and the bytes past it; (2) row 17 raised whole with
  the loop-placement refinement (every test B2 names is separated; the record-name fatal, which B2 does not state, is
  unseparated on stock); (3) the six unseparated controls taken as inherent (equal table columns; no stock 8-character
  record name; no queued frame at `T`); (4) row 9 left for part 2 rather than filed not raised (the fallback's values
  need the loader or `ANIMDATA_Lookup` run whole).
- **Resume note for S6e part 2 (a fresh lane on `lane/n66l`).** 25 rows left: timing 9, 11, 18, 20, 30, 40, 45,
  80–84, 87, 90, 91, 129; movement 4–6, 8, 13, 14, 22, 24, 43; and the remainders routed to S6e: timing 23, 24, 29,
  43, 44, 46, 49, 61, 62, 86, 88, 98, 128, 130; movement 2, 15, 19, 23, 31. Extend `tools/anim_s6e_emu.py` with new
  families (keep part 1's families and seeds unchanged, write the new run to `workspace/logs/n66l/s6e/run2/`, one
  launch). Cheapest first: `MonStatsSpeeds` 0x00650F00 (m13, m14), `HumanAttackFrames` 0x0062A710 (t91),
  `PathVelocityStep` 0x006502D0 (m24), `PlrToMonMode` 0x00645190 (t20), `UNIT_AnimStartFrame` with
  `SkillSrcDamWeapon` 0x00623990 declared (t30; then the advance with a start frame ≠ 0, t40, and the schedule with
  S ≠ 0), `ANIMDATA_Lookup` with `COMPOSIT_BuildCofName` (t9, t16's rest, t18 via `COMPOSIT_WeaponClass`),
  `PathStepCollide` (0x0064FF90's room read declared, m22, m43), `UnitSeqRecord` (t45); last `UNIT_AnimSetRate`
  (19 callees: 0x00620F00, 0x00621360, 0x006213D0, 0x00621740, 0x00623C80, 0x00625480, 0x00629BB0, 0x0062A4E0,
  0x00639DF0, 0x0063A7B0, 0x0063BDE0, 0x00645270, 0x00646170, 0x00648690 and the predicates; t11, t80–84, t87, t90,
  t129, m4–6, m8), which may not fit and returns its rows to b if `UNIT_AnimSetRecord`, `WeaponListsRelink2` and
  `PathSetSpeed` cannot run whole. Control loops need a step cap (a reversed loop test runs away; see the tool).
  Ghidra project `workspace/ghidra-n66l` stays in place.
