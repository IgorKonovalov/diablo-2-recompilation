# 0038 — Inferred-claims sweep: raising `[I]` to `[C]` in the reviewed specs

> **Status:** approved (2026-10-16, by the owner, to run unattended)
> **Created:** 2026-10-16
> **Owner skill(s):** architect (Phase 0), reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0008-two-client-harness, 0010-forced-path-runs, 0011-harness-slots, 0013-forced-path-runs-cell-level, 0014-scope-game-simulation

## TL;DR

**Question:** which `[I]` claims in the reviewed specs can one more harness run, a new check over logs we already
have, or a static second source raise to `[C]`, and in what batches?

Every first-scope research-map row is `reviewed`. The reviewed specs hold **1 526 `[I]`** statements, against
2 531 `[C]`. Each plan raised what its own run reached and left the rest at `[I]`, so the remaining `[I]`s were never
looked at side by side. Many are cheap to raise:
- a branch the plan's run missed but an existing recipe reaches in another difficulty;
- a claim whose values are already in a kept log but had no check;
- a writer whose reader is already `[C]`.

When this plan is done:
- `docs/plans/0038-inventory/` classifies every `[I]` of every reviewed spec, with its route to `[C]` or the reason it
  stays `[I]`;
- the static batches have added second sources to the findings, and the harness batches have logged one
  `run:<date>-sweep-<batch>` record each, with 0 mismatches;
- the specs are re-tagged and their counts updated, and the research map shows the new counts.

This plan adds no subsystem and changes no spec status. It is not a simulation plan, so ADR-0014's block on the next
simulation plan does not apply to it.

## Context

- **Research map:** every Core, Enabler and Creation-path row is `reviewed`. The Simulation band has one row,
  `combat/formulas`, owned by [plan 0037](0037-combat-formulas.md), which starts after [plan 0036](done/0036-human-wiki-readme.md)
  closes.
- **`[I]` counts of the reviewed specs on 2026-10-16** (front matter, `main` at `32a1a6e`):

  | Band | Spec: `I` |
  |---|---|
  | Core | items/tc 76, items/quality 36, items/affixes 45, items/uniques-sets 52, items/properties 35, monsters/pool 29, monsters/README 1, monsters/spawn 64, monsters/special 91, monsters/stats 54, drlg/README 18, drlg/room-tiles 46, drlg/preset 44, drlg/maze 26, drlg/outdoor 22, drlg/warps 31, objects 64, rng 8 |
  | Enablers | save/d2s 144, data/excel 100, data/calc 67, data/strings 39, data/README 5, rng/seeds 17, drlg/collision 55 |
  | Creation paths | items/cube 82, items/sockets-runewords 77, items/quest-drops 83, items/vendors 37, hirelings 39, player/creation 39 |

  `items/README` and `save/README` are `draft` and out of scope. `player/README` has no tags.
- **What keeps a claim at `[I]` today**, read from the plan logs and their reviews:
  - the run did not reach the branch: another difficulty, classic, a player count, a rare roll;
  - the values sit behind a boundary oracle whose model came later (ADR-0004). For example, the items/tc runs predate
    the quality model of plan 0010;
  - the claim's code reads a cell a forced run edited (ADR-0013);
  - it needs two clients (ADR-0008 is still `proposed`);
  - it needs owner play;
  - it belongs to a later simulation phase (ADR-0014);
  - the write side of something whose read side is confirmed (save/d2s, the merc header).
- **Rulings this plan relies on:**
  - Re-analysing a run's kept logs with a new check counts as that run's corroboration when it is recorded as a dated
    addendum to the run record (architect, 2026-10-15, backlog: static sweep review, ruling (a)).
  - A reviewed spec does not need every detail run-confirmed. A targeted run for the remaining `[I]` is optional work
    (plan 0023 Phase 3 review, 2026-10-15). This plan is that optional work, prioritised.
- **Excluded:** the plan 0032 owner-played addendum (backlog entry 2026-10-16, "plan 0032 Phase 2 owner-played
  addendum"): Mephisto with his quest done, the Countess in four states, the Cow King and the Hell Hellforge, in
  [run:2026-10-16-quest-drops](../findings/items/experiments.md#run2026-10-16-quest-drops). Those rows are listed
  in the inventory as class (d), with a link to that entry, and no batch takes them.
- **Owned by plan 0037:** claims that plan 0037 already targets are class (d) with the plan named. These are
  monsters/stats § H, the attack rating term of player/creation, and the `ToHitCalc` open question of data/calc.
- **Harness limits:**
  - At most **two harness lanes at once** across all plans. On 2026-10-15, systemd-oomd killed every lane when RAM
    and swap passed 90 % ([tooling § Runtime harness](../../.claude/skills/reverser/references/tooling.md)).
  - Slot 0 is the owner's.
  - Slots follow [ADR-0011](../adrs/0011-harness-slots.md): the prompt gives each lane its slots, and the lane never
    touches another slot.
  - 0037·P2 takes at most two slots and goes first.
- Play rules: [harness-play](../../.claude/skills/reverser/references/harness-play.md). Recipes live in
  `tools/d2s_recipes/`, loggers and steps files in `tools/gdb/`.

## Classes

Phase 0 sorts each `[I]` statement into one class.

| Class | Meaning | Who raises it |
|---|---|---|
| **(a-logs)** | A kept log in `workspace/logs/` already holds the values. A new or extended check reproduces them. No session needed. | reverser, static batch (no slot) |
| **(a-run)** | One more session with an **existing** recipe, logger and checker reaches it, for example another difficulty, classic, `/players N` or a longer hunt | reverser, harness batch |
| **(b)** | It needs a **new** recipe, logger line, pilot action or checker case, still on stock data with one client. A forced run is a (b) case and needs the ADR-0013 read list first. | reverser, harness batch |
| **(c)** | A **static second source** is enough: a second code path that agrees (evidence rule 1), or data behaviour over every row (rule 2) | reverser, static batch |
| **(d)** | **Blocked.** Sub-reasons: `d-2c` two clients (ADR-0008 `proposed`), `d-owner` owner play, `d-sim` a later ADR-0014 phase or plan 0037, `d-edit` only edited data reaches it (ADR-0010/0013), `d-0032` the plan 0032 owner addendum, `d-none` no observable (dead code, a guard stock data never fails) | nobody in this plan; reasons recorded |

**Value tier**, used to order the batches:
- **T1:** on the main path of the original three areas: the stock drop chain, level population, level build, and
  the seeds feeding them.
- **T2:** an enabler or creation path in normal play: save, data, calc, strings, cube, sockets, vendors, quests,
  hirelings, player.
- **T3:** a rare or error branch on any path.

A batch's priority is its count of T1 rows first, then its count of T2 rows.

## Phases

### Phase 0 — Inventory of the `[I]` claims
- **Owner skill:** architect.
  - *Why this lane:* the output is a routing list that decides which lane and batch takes each claim. It makes no
    claim of its own, so it is planning work in `docs/plans/`.
  - *Why not the spec-writer:* it owns neither `docs/plans/` nor `docs/findings/`, and it does not investigate.
  - Classifying a row means reading the spec, its finding, the run records and
    [tooling](../../.claude/skills/reverser/references/tooling.md). The architect reads them and analyses no binary.
  - Up to four architect copies may run in parallel, one per cluster, each writing only its own files: (0a) items,
    (0b) save, data and rng, (0c) monsters, hirelings and player, (0d) drlg and objects.
- **What:** list every `[I]` statement of every reviewed spec, classify it, give it a value tier, and assign every
  (a-logs), (a-run), (b) and (c) row to a batch.
- **Where the output goes:** `docs/plans/0038-inventory/`, one file per spec plus a `README.md`.
  - *Why not a findings index:* findings are the reverser's evidence records, and an inventory is not evidence. It
    is a work list that dies with the plan.
  - It moves to `docs/plans/done/` with the plan. Its relative links are rewritten at the move.
- **Outputs:**
  - `docs/plans/0038-inventory/<subsystem>-<spec>.md`, for example `items-tc.md` or `save-d2s.md`.
    - One table, with columns: `#`, spec section (link), the claim in at most 15 words, the finding anchor, class,
      route, tier, batch, count.
    - The route is the recipe and logger, the new piece needed, the second code path or table, or the `d-` reason.
    - Consecutive statements of one section that share class, route and batch may share a row, with their number
      in *count*.
    - The file records the spec commit it was read at.
  - `docs/plans/0038-inventory/README.md`, which holds:
    - the totals per spec and class;
    - the **batch list**, with each batch's rows, tier counts, recipe and logger, the subsystem whose
      `experiments.md` gets the record, and its run id;
    - the **priority order**;
    - every batch over the size cap split, and every batch under 10 rows merged or deferred with a reason.
- **Done when:**
  - every reviewed spec listed above has its file, and each file's *count* column sums to that spec's front-matter
    `I` at the recorded commit (a spec without `[I]` gets one line saying so);
  - every row has exactly one class, and a (d) row has its sub-reason;
  - no (a-run) or (b) row duplicates the plan 0032 addendum or a plan 0037 case;
  - the batch list respects the caps below;
  - a forced-run batch, if any, names the claims, the table and the cells it would edit, and the finding sections
    where the ADR-0013 read lists must stand before the run;
  - the gate is green;
  - **the architect's review of Phase 0 accepts the batch list.** No Phase 1 or Phase 2 batch starts before then.
    The review may move rows between classes and batches.

### Phase 1 — Static batches (second sources and re-checks of kept logs)
- **Owner skill:** reverser (static: Ghidra, r2 and `tools/` checkers over `workspace/logs/`; no game, no slot)
- **What:** raise the (c) and (a-logs) rows of one cluster per batch.
  - A (c) row is raised by naming the second code path or the full-table data behaviour.
  - An (a-logs) row is raised by a new check over kept logs, recorded as a dated addendum to the original run
    record (ruling 2026-10-15 (a)).
  - Batches may run in parallel copies, each on its own Ghidra copy and branch.
- **Expected batches.** Phase 0 fixes the final list and may split any of these.
  - **S1:** save/d2s, data/excel, data/strings, data/calc, data/README, rng, rng/seeds. Examples: writer and reader
    pairs of the save, `ValShift`/`Save Bits` behaviour over all ItemStatCost rows, lookups that every table row
    exercises.
  - **S2:** items/tc, quality, affixes, uniques-sets, properties, sockets-runewords, cube, vendors, quest-drops.
    Example: kept items logs re-run with the plan 0010 quality model in place of the oracle, under the ADR-0004
    oracle switch.
  - **S3:** monsters/pool, spawn, special, stats, README, hirelings, player/creation.
  - **S4:** drlg/README, room-tiles, preset, maze, outdoor, warps, collision, objects.
- **Size cap:** at most 100 rows (counted statements) per static batch.
- **Outputs:**
  - in each touched finding, a dated section "Plan 0038 batch S*n*" listing each raised claim with its second source
    or check, and each row that failed, with the reason;
  - the run-record addenda;
  - `re/symbols.csv` confidence changes;
  - `tools/` checker extensions;
  - a backlog review request to the architect.
- **Done when** (per batch):
  - every assigned row is either raised in its finding, with the second source or check named in the statement and
    the check rerunnable from the addendum, or returned to the inventory with a new class and a reason;
  - every existing checker the batch touched still reports 0 mismatches on its original run's logs;
  - the gate is green;
  - the architect's review accepts it. The review spot-checks three raised claims per finding: the second path
    re-read, or the check re-run.

### Phase 2 — Harness batches
- **Owner skill:** reverser (harness, agent-driven per harness-play, with one-client sessions on stock data)
- **What:** raise the (a-run) and (b) rows, one batch at a time. A batch is grouped by **recipe and logger**, so that
  one session covers many claims.
- **Slots and queue:**
  - At most two slots per batch. Never slot 0. The prompt gives the slots.
  - **Harness lanes across all plans are never more than two.** 0037·P2 has priority:
    - while it holds two slots, no 0038 batch runs;
    - while it holds one slot, one 0038 batch may run on one slot;
    - before 0037·P2 starts and after it ends, 0038 batches may use both.
  - Batches run in the Phase 0 priority order. Two batches may run at once only when they share no recipe save,
    logger file or checker under edit.
- **Rules every batch follows:**
  - **ADR-0003:** the record is reproducible from itself: command lines, steps and plan files, recipe hashes, slot
    per session, log paths and a hashed manifest.
  - **ADR-0004:** each oracle is named, its entry seed asserted, and a missing exit is a failure.
  - **ADR-0013:** a `-forced` run only for rows Phase 0 marked as forced. The cell-level read lists must be in the
    finding before the run. A stock companion session must cover the path wherever stock play reaches it. A claim
    whose code reads an edited cell, or whose subject an edited cell names, stays `[I]`, and nothing about
    frequencies is raised.
  - Tool-built saves on stock tables are ADR-0003 inputs, not forced runs (ADR-0013 § Neutral). They back the code
    that reads the built state, never how a character reaches it.
- **Expected batches, in expected priority order.** Phase 0 confirms, splits, merges or reorders them; the run ids
  are `run:<date>-sweep-<slug>`.

  | Batch | Slug | Specs | Recipe and logger family | Record in |
  |---|---|---|---|---|
  | H1 | `d2s` | save/d2s | `d2s-io.gdb`; saves written and reloaded across character kinds (expansion and classic, mercenary alive and dead, every item flag the bitstream branches on) | `findings/save/experiments.md` |
  | H2 | `items` | items/tc, quality, affixes, uniques-sets, properties | `tc-drops.gdb` and `items-chain.gdb` with `tc.py replay` and `items_chain.py`; Normal, Nightmare and Hell, classic, `/players` 1–8, champion and unique kills | `findings/items/experiments.md` |
  | H3 | `calc` | data/calc | `calc.gdb` and `calc-field.gdb`; the callers and opcodes the plan 0035 run did not reach on stock data | `findings/data/experiments.md` |
  | H4 | `monsters` | monsters/pool, spawn, special, stats | `mon-spawn`, `mon-special` and `mon-stats` loggers; the difficulties, classic and player counts each spec left `[I]` | `findings/monsters/experiments.md` |
  | H5 | `drlg` | drlg/*, objects | `drlg-gen`, `drlg-roomk`, `collision` and `objects` loggers; unreached levels and branches, including the casket group and orientation-2 shrine from the plan 0023 ruling | `findings/drlg/experiments.md`; the objects findings cite it, or Phase 0 splits an H5b with its own record in `findings/objects/experiments.md` |
  | H6 | `creation` | cube, sockets-runewords, vendors, quest-drops (minus addendum), hirelings, player/creation, data/strings | the plan 0029–0034 `.plan` recipes and `d2pilot.py npc`; the classic, multi-difficulty and level-up cases those runs left `[I]` | Phase 0 names one record per split (H6a, H6b, …) |

- **Size cap:**
  - at most 60 rows (counted statements) and 20 sessions per batch;
  - one logger family per batch, plus the existing checkers it re-runs;
  - a batch Phase 0 sizes above the cap is split, with a letter suffix and its own run id.
- **Done when** (per batch; the same list for each):
  - `run:<date>-sweep-<slug>` is recorded in the named `experiments.md` with ADR-0003 content and the slot of each
    session;
  - the batch's checker or checkers report **0 mismatches** over every session log, and every existing checker of
    that logger family reports 0 mismatches on the new logs (no regression);
  - every assigned row is in one of three states:
    - **raised:** the finding has a dated section "Plan 0038 batch H*n*" that lists the claim with the check that
      reproduces it and the count of cases;
    - **shortfall:** recorded with its count and reason, and the row stays `[I]`, not blocking;
    - **reclassified:** returned to the inventory with a new class and a reason;
  - each raised claim reached by **one stock case or more** is logged, and no frequency claim is raised;
  - `re/symbols.csv` confidence is updated;
  - the gate is green;
  - the architect's review re-runs the checker on the batch logs and accepts.
  - If a batch raises **fewer than half** its rows, the record says why. This does not block the batch, and the
    architect may cancel the batches still waiting in that family.

### Phase 3 — Re-tag the specs
- **Owner skill:** spec-writer
- **What:**
  - Raise each spec statement whose finding claim a Phase 1 or Phase 2 batch raised and the architect accepted. The
    statement names the new corroboration (`run:` or second source).
  - Demote any statement a batch contradicted, with its *Open questions* entry.
  - Update the front-matter counts.
- **Order:**
  - This phase may run per cluster once all of that cluster's batches are accepted.
  - It does not start before plan 0036 Phase 2 lands, because that phase writes the wiki over these specs.
  - Specs that 0037·P3 also edits (monsters/stats, player/creation, data/calc) are merged one at a time with it,
    whichever lands first.
- **Outputs:**
  - the re-tagged specs;
  - `updated:` dates;
  - a backlog entry to the architect with each spec's old and new `{C, I, L}`, for the research-map rows and the
    wiki's `based_on` dates (W4).
- **Done when:**
  - every raised or demoted finding claim of an accepted batch is reflected in its spec, or listed in the backlog
    entry with the reason it is not;
  - every spec's E6 counts match;
  - no `[L]` leaves *Open questions*;
  - the gate is green;
  - the architect's review accepts. The review spot-checks five raised statements against their batch sections.

## Open questions

- **ADR-0008** two-client rows (`d-2c`) stay blocked while the ADR is `proposed`. Phase 0's count of them tells the
  owner what accepting it would unlock.
- **`d-owner` rows.** Owner-play rows other than the plan 0032 addendum are listed only. If they are many, the
  architect proposes one owner addendum at the close, as plan 0032 did.
- **`d-none` rows**, such as guards that stock data never fails, may never reach `[C]`. Phase 0 counts them so that
  the specs' remaining `[I]` is explained.
- **Plan 0037 interaction.** If 0037·P1 reads code that a static batch also needs, such as the stat accessors, the
  two lanes share the finding through the backlog and do not each re-read it.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-16 — Drafted and approved (architect).** Written in the architect worktree `lane/p38` from `main` at
  `32a1a6e`. The owner chose the sweep on 2026-10-16 and approved it to run unattended. Phase 0 and the Phase 1
  static batches may run at any time. Phase 2 batches take the slots plan 0037 Phase 2 leaves free, and never more
  than two harness lanes run at once.
- **2026-10-16 — Phase 0 inventory complete (architect, `lane/c38`).** The four cluster lanes (`lane/i38a`–`i38d`) wrote
  31 per-spec files at `main` `e1c807a`, and each file's counts sum to its spec's `I` (1 526 in all).
  [0038-inventory/README.md](0038-inventory/README.md) adds the totals, the reconciled batch list, the priority order
  and the caps.
  - **Batches:** 10 static (S1a, S1b, S1e, S2a–S2c, S3a, S3b, S4a, S4b; 634 statements) and 21 harness (H1a … H6g;
    522 statements, including the forced H2c).
  - **Not batched:** 359 blocked (d-none 239, d-edit 66, d-sim 24, d-2c 14, d-owner 8, d-0032 8), 10 already raised
    on `lane/rbl`, 1 deferred.
  - **ADR-0015** adds a route, (c-emu). It relabels the 42 S1e rows and reclassifies 32 statements of data/calc,
    data/excel and data/strings (3 from b, 21 d-edit, 8 d-none). 27 more are listed as candidates for the review.
  - **Ids reconciled:** 0c's H6a/H6b → H6f/H6g, the 0c and 0d shares → H1a/H1b and H6e2, H5r merged into H5c, H3a
    dissolved.
  - **H1b** also loads `questrewards`/`questrewardsh` to re-pin them in `tools/test_d2s.py`.
  - **Forced candidates:** two, both in H2c, left for the review to rule on.
  - **Per-spec files:** items-tc's two broken table rows and its forced-note row numbers fixed, and objects 47's stale
    route fixed.
  - **Gate:** green. **Next:** the architect's Phase 0 review (backlog); no batch starts before it.
- **2026-10-16 — Phase 0 reviewed (architect, `lane/c38`): accept with fixes.** Phase 1 and Phase 2 may start.
  - **Checks.** A script summed every per-spec file's *Count* column against its spec's front-matter `I` at `e1c807a`
    and at `551bee9`: all 32 files match (1 526). Every row has one class, and every (d) row its sub-reason; the
    clusters write the classes in two notations (`(b)`, `d (d-none)` against `b`, `d-none`), which is cosmetic. A
    second script rebuilt each § 5 batch's statement count from the files' rows: all 31 match once the § 2 moves are
    applied. Caps hold. The gate is green.
  - **Sampled 22 rows** across the four clusters. The a-logs facts hold in the kept logs: 184 `TCR stype=2` lines and
    247 `TCEND count=6` lines (items-tc 4, 7), 62 991 monster-stat checks (monsters-stats 2), 378 Logicals floods
    (drlg-collision 6), 548 re-created objects (objects 7), the logged weapon set (save/d2s 24), and `MPR` lines in
    the 32 `monpool*` logs (monsters-pool 3). The (c) rows sampled name a real second path or full-table check
    (items-tc 5, items-uniques-sets 3, save/d2s 7, drlg-preset 3, monsters-spawn 1). The (c-emu) rows sampled
    (data-calc 31, data-excel 16, data-strings 4) read table records or scratch images that the memory spec sets, so
    they meet ADR-0015 conditions 1, 2 and 4 in principle. The a-run and b rows sampled (drlg-maze 6, monsters-special
    10, hirelings 9, items-tc 2) name an existing or new recipe that fits their class.
  - **Fixes (8 statements moved, [inventory § 2.5](0038-inventory/README.md#25-moves-made-by-the-phase-0-review)).**
    monsters-stats 42 and 46 → d-sim, because plan 0037 Phase 1 reads the hireable-boss damage percent. objects 5 →
    deferred, because it needs two subsystems' restore models. properties 12 (L403, L416) and 21 → d-edit (ruling 2).
  - **Rulings.**
    - (1) Classic throwables: admitted. The counter and the `lsd` code read no TreasureClassEx cell.
    - (2) TC-named uniques: funcs 12, 23 and 24 admitted; func 36 (*Hellfire Torch*, no stock path) and
      *Wraithflight* d-edit.
    - (3) H5c stays first; its logger edits are made off-slot. H3b stays (b), with the `d2run.py` start mode as its
      first piece; failure is a shortfall, not d-none.
    - (4) Batch list accepted. A one-client TCP/IP host is one client. The 27 emulation candidates are left for an S1f
      proposal at the S1e review.
    - Conditions and the full reasoning are in [inventory § 6–7](0038-inventory/README.md#6-forced-run-candidates-ruled-at-the-review).
  - **Totals now:** 634 statements in 10 static batches, 516 in 21 harness batches (H2c 7), 2 deferred, 10 raised and
    364 blocked (d-none 239, d-edit 69, d-sim 26, d-2c 14, d-owner 8, d-0032 8).
  - **First batches.** Static: S4a ∥ S2a, then S2b (after S2a) ∥ S3a. Harness, with two lanes free until 0037·P2
    starts: H5c ∥ H4b, then H5e → H5a and H4a.
- **2026-10-16 — Batch S2a done (reverser, `lane/s2a`, static).** 65 statements (items/tc 47, items/quality 18): 32
  raised, 22 raised in part, 3 shortfall, 8 reclassified (d-none 4, (b) 4). Second sources: a replay with counts of the
  166 kept stock logs of 11 item runs (9390 calls, 9390 reproduced; 9184 with the quality roll modelled), counterfactual
  models that must fail where a rule decides, full-table checks, a raw-byte xref scan next to Ghidra's, and the
  tc-champion input save for the Andariel sighting. Ledgers in
  [items/0001](../findings/items/0001-tc-resolution.md#plan-0038-batch-s2a-2026-10-16) and
  [items/0002](../findings/items/0002-quality-roll.md#plan-0038-batch-s2a-2026-10-16); addenda under the 11 runs; tools
  `tc_sweep.py`, `xrefscan.py`. Surprises: the classic skip and scan-off-the-end are unobservable for any loaded table;
  the chest drop passes its tier as `ilvl`; the `Countess` TCs are the only stock case of the negative-`Picks` stop
  (classic). The tc 64 addendum waits for the objects run record (S4 cluster). Review requested (backlog).
- **2026-10-16 — Batch S2a reviewed (architect, `lane/s2a`): accept with fixes.**
  - **Checks rerun** (read-only, `python3 -I`, no game or slot):
    - `tc_sweep.py logs`: 166 of 166 sha256 match the records, and the batch manifest hashes to the cited `850698f9…`.
    - `replay`: 9390 of 9390 calls reproduced (9184 with the roll modelled, 206 with the oracle).
    - `cf`, `tables`, `drops`, `chest` (59/59) and `b6save` (base 834) print the counts the ledgers cite.
    - `xrefscan.py` finds the call sites the ledgers name. `test_tc_sweep.py` runs 6 tests, all OK.
    - No regression: `tc.py replay` on tc-run2, tc-party-2 and tc-quality-3 (classic, roll modelled), and
      `quality.py check` on tc-quality-1 and tc-champion-1, give their original counts with 0 failed.
    - Gate green.
  - **Rows spot-checked end to end** (18): tc 3, 4, 5, 7, 13, 16, 23, 25, 28, 29, 39, 57, 61/62, 64; quality 1, 10, 14,
    26, 35 (QROW per difficulty 439/981/187), 18.
  - **Second sources.** Every raise rests on one of these:
    - a replay of kept logs, which is that run's corroboration (owner ruling 2026-10-15) and is recorded as an
      addendum under each of the 11 runs; the addenda add to the records and change none of their results;
    - a full-table check (rule 2);
    - a writer/reader pair (tc 12);
    - a second xref method (a raw rel32 and absolute-address scan next to Ghidra's), for the "only caller" claims
      tc 5 and quality 1.
  - **Counterfactual replays are not evidence by themselves.**
    - A switch that fails is a sensitivity check. It shows that the logs decide the rule: nomax 4, nopop 630,
      autoweight 1235, A2 `version` 158 and sub-TC 28, q-equiv 33, q-floor 35. The evidence is still the replay.
    - A switch that passes is only a consistency check: notail, the NoDrop variants, noskip, cumexp, q-type2 and the
      A2 unique/set clause. The lane used these correctly to keep remainders `[I]` or to reclassify. The exception is
      tc 50, whose claim is itself the equivalence.
  - **Fixes (on `lane/s2a`):**
    - tc 33, 40 and 48 move from raised to **raised in part**. Each spec block (D1–D5, E2, G1) also holds lines that no
      call reached: the fatals, `0xFFFF`, the classic skip and the run off the end. For E2, the `cumexp` and `noskip`
      models reproduce the same 801 calls.
    - tc 69 now says that the 53-bit precision rests on the logged control word, because the 24- and 64-bit models
      also match.
    - The 8 reclassified rows are recorded in
      [inventory § 2.6](0038-inventory/README.md#26-moves-made-by-the-batch-reviews): d-none tc 13, 15, 41, 74; (b)
      tc 34 ×2 → H2a and tc 58, 68 → H2b. § 5 and § 7 are updated to match.
  - **Symbols.** The six I → C moves are justified. The resolver, `TC_DropByIndex` and `MONSTER_DropItems` are
    reproduced over 9390 calls in three difficulties, classic and expansion. `MONSTATS_GetRecord` is the base-TC lookup
    of all 9265 monster calls. `TC_AddEntry`/`TC_SetEntryProb` rest on the writer/reader layout, and the A2 switches
    show that the classic-sum rule decides the logged calls.
  - **Rulings on the lane's points.**
    - (1) tc 64 stays a shortfall. A `run:` corroboration needs its addendum in the objects run record (ADR-0003),
      which waits for S4a to merge. The new `[I]` (the chest passes its tier as the resolver's `ilvl`) completes the
      2026-10-16 chest-tier ruling: that ruling fixed the tier's input, and this claim fixes where the tier goes. The
      backlog entry routes both halves.
    - (2) The reclassifications are accepted as filed.
    - (3) Phase 3 splits "in part" statements along the remainder each ledger line names.
    - (4) tc 69's warning stays `[I]`, d-none.
    - (5) Passed to S2b.
  - **Final:** 65 statements: **29 raised, 25 raised in part, 3 shortfall, 8 reclassified**. By spec, items/tc has
    20/18/1/8 and items/quality 9/7/2/0.
  - **Next:** merge `lane/s2a`, then S2b may start.
- **2026-10-16 — Phase 1 batch S4a done (reverser, `lane/s4a`, static; no slot, no game).** 89 statements: **75 raised**,
  **2 shortfall**, **12 reclassified**. Each finding has a dated section "Plan 0038 batch S4a" (drlg/0002–0008,
  objects/0001), and the drlg and objects run records have dated addenda. The checks are `tools/sweep_s4a.py` (29
  checks over the kept logs, built on the existing models; no checker changed) and `tools/test_sweep_s4a.py`.
  - **Shortfalls:** outdoor 8 (no logged insert separates the `LevelAdjInsert` quirk from a full compare) and warps 14
    (only `Position` levels take the slot-33 point; for `Position` 0 the point is `LevelWaypointRoom`'s waypoint-object
    tile, now `[C]`, so the statement needs splitting).
  - **Reclassified:**
    - room-tiles 4, 14, 28, 37 (8 statements) → a-run H5c: no remap through rows 0–5 was logged;
    - warps 16 → b H5c: a `RoomNeighboursEnsure` logger line is needed;
    - outdoor 10, drlg/README 12 and one of preset 5's three statements → d-none.
  - **Partial raises:** the remainder stays `[I]` and is named in each section.
  - **New code readings:** the neighbour merge's edge points and `RegionRelabel`'s arguments, the barrier grid's
    near-room source, and `RoomTilesRelease` freeing the logic record (`sub_0066C6E0_LogicRecordFree`). These close the
    two drlg/0005 open questions.
  - **Regression:** `drlg.py gen`/`roomk`, `collision.py check`, `objects.py check` and `maze_replay.py` give their
    recorded counts with 0 mismatches. `re/symbols.csv`: 24 rows raised to C, 1 added. Gate green. Review requested
    (backlog).
- **2026-10-16 — Batch S4a reviewed (architect, `lane/s4a`): accept with fixes.** `main` (`b349849`, S2a and plan 0037
  Phase 1) merged into the branch first; the plan log and backlog conflicts were appends, both kept.
  - **Checks rerun** (read-only, `python3 -I`, no game or slot): `sweep_s4a.py` `logic`, `barrier`, `flood`, `nww`,
    `objects`, `pick`, `l27`, `adj`, `r0`, `orpath`, `expansion`, `lsr`, `pcopies` each print the counts their ledgers
    cite, and exit 0. `test_sweep_s4a.py`: 9 tests OK. `drlg.py roomk` on the six roomk logs: 520 activations, 11 734
    checks, 0 mismatches. Gate green; `re/symbols.csv` has no duplicate address or name.
  - **Addresses read with r2:**
    - `LOGIC_NeighbourMerge` calls `LOGIC_EdgeMerge` with `ECX` = x and `EAX` = `R+0x38` and `R+0x38 + R+0x40`, then
      `ECX` = `R+0x34` and `R+0x34 + R+0x3C`, as the ledger reads them.
    - `RoomTilesRelease` calls `0x0066C6E0` at `0x0066F1D4`, and that function ends with `[esi+0x64] ← 0`.
    - `0x006678E2` and `0x00667A35` call `0x00667620`, and `0x0061B752` and `0x0061B343` call `0x00667890`. The
      pointer scans find nothing.
    - `0x00620ACF` is the return from `COLL_RectOrWH` inside `UNIT_CollMarkRect`.
  - **Rulings on the lane's points.**
    - (1) A code reading new in the batch, anchored by address in the finding, plus a model built on it that reproduces
      every logged record is evidence rule 4, which backs `[C]`. Examples: 1475 LG0 barrier grids, 1475 LG2 merges and
      4478 SN grids. The two sources are independent: the reading came from the disassembly, and the logs came from the
      game. Runs that change one value and must then fail are sensitivity checks, not the evidence. They show that the
      logs decide the value: 28 of 30 flood-rule entries and 16 orientations, 200 comparisons without the release, 781 380
      tiles with file-order candidates, 26 517 and 4168 without `KillEdge` and `FillBlanks`, 3019 with the second room
      moved, and the 3789 dumps that an overwrite stamp would change. Runs that change a value and still pass (`adj`
      full compare, `placefar` exclusive bounds) are consistency checks. The lane used them correctly, to keep a
      shortfall and to reclassify. Maze 3 is the S2a tc 50 exception: its claim is the invariance itself.
    - (2) Collision 29 stays raised in part (missiles). The 85 item marks show that items are marked at creation
      through `UNIT_CollMarkRect` (1 × 1, `0x200`). They do not show whether `UNIT_CollMark`'s type-4 branch is reached
      at all. In Phase 3, the spec keeps F1's type-4 line `[I]` and adds the creation path, citing
      run:2026-10-15-objects (spec-writer entry (b)).
    - (3) The `(10, 0, 0)` note is spec-writer entry (d). It is not an S4a row, and the step note's "never occurred"
      is true of the run it names.
    - (4) H5c conflicts are predicted with `git merge-tree`: drlg/0002, 0003, 0004, 0007 and this log, all
      append-at-the-same-place conflicts. There are also four semantic points: `tools/drlg.py` `Model` changes under
      `sweep_s4a.py`, `+0x64` in the release compare, the 9 inherited statements with their new logger line, and
      cross-citations. They are set out in a backlog entry to the H5c lane.
    - (5) 11 734 is the count since plan 0027 Phase 2 (`a14c875`, recorded in plan 0027's log and the room-tiles
      spec). The addendum now says so.
  - **Fixes (on `lane/s4a`).**
    - **18 raises recounted as raised in part**, following the S2a standard. In each, the named part stays `[I]` and
      the rest is `[C]`:
      - collision 6 and 42 (one statement each): rule entries (3, −1), (4, −1) and the rows of orientations 4, 13, 15;
      - collision 13: entry flag `0x80`;
      - collision 20: the door `0x804`;
      - collision 29: items and type 5;
      - collision 31: sizes 3 and above;
      - collision 32: the player's size;
      - preset 18: id 573;
      - drlg/README 7 and 14: one −1, no record and the theme (d-none parts);
      - room-tiles 5: the DS1 load against `RoomNeighboursEnsure`, re-activation and `RoomActivateA` (now written in
        drlg/0002);
      - room-tiles 12 and 26: Def 108;
      - maze 8: no room takes the special;
      - outdoor 1: the record size;
      - outdoor 16: level 134 and the fatal branch;
      - objects 28: the InitFns not reached;
      - objects 47: the chests and Wirt's body (H6e2).
    - The pick ledger now states its 4224 uncompared entries (no model choice, or no single TL line).
    - The 12 reclassified statements are in [inventory § 2.6](0038-inventory/README.md#26-moves-made-by-the-batch-reviews).
      § 5 and § 7 now give H5c 41 statements (T1 33) and the `RoomNeighboursEnsure` line.
  - **Symbols.** The 24 I → C moves follow the raises. `COLL_SizeMark`, `g_LogicFloodRules`, `g_LogicFloodOrientRow`
    and `UNIT_GetSizeX` are confirmed on their core with the remainders above. `RoomTilesRelease` and `LevelPointFind`
    rightly stay I.
  - **Final:** 89 statements: **57 raised, 18 raised in part, 2 shortfall (outdoor 8, warps 14), 12 reclassified**
    (8 a-run and 1 b to H5c, 3 d-none). Static batches now hold 614 statements, harness batches 529 and blocked rows 371.
  - **Next:** merge `lane/s4a`. S4b may then start, and S2a's tc 64 objects addendum can be written. H5c reconciles
    before its next session (backlog).
- **2026-10-16 — Phase 2 batch H5c in progress (reverser, `lane/h5c`, slot 4).** Logger edits made and
  regression-checked off-slot first (roomk, gen, collision and seed-tree checkers on their kept logs: same checks,
  0 mismatches). Sessions 1–5 of run:2026-10-16-sweep-roomk ([drlg/experiments.md](../findings/drlg/experiments.md#run2026-10-16-sweep-roomk)):
  roomk 60 898, gen 74 961, monspawn 83 374, collision 7 505 checks and seedtree 90 962/90 962, 0 mismatches. Draft
  "Plan 0038 batch H5c" sections in drlg/0002, 0003, 0004, 0007 and rng/0002. The slot was yielded to an owner session;
  sessions 6 on (tomb levels, a warp, level 74, Act IV outdoors, `-seed -2147483648`) wait for the resume.
- **2026-10-16 — Batch H5c done (reverser, `lane/h5c`, slot 4).** run:2026-10-16-sweep-roomk, 11 sessions (s1–s11;
  one yield to an owner session between s5 and s6), recorded in
  [drlg/experiments.md](../findings/drlg/experiments.md#run2026-10-16-sweep-roomk) with the logger revision per
  session. Checkers: `drlg.py roomk` 87 223 checks on all eleven logs; `gen` 99 339, monspawn 150 095, collision 14 456
  and `seedtree` 117 395/117 395 on the nine with an applied `-seed`; 0 mismatches. Kept-log regressions before the first
  session and after the S4a merge: same counts, 0 mismatches. Sections "Plan 0038 batch H5c" in drlg/0002, 0003, 0004,
  0007 and rng/0002; `re/symbols.csv`: six functions I → C, `sub_0066B4C0_RoomReleaseWrap` added.
  - **41 statements** (32 of the batch plus 9 returned by S4a): **24 raised, 5 raised in part, 1 contradicted, 11
    shortfall.**
    - Raised: drlg/README 1, 5 (×2), 10; preset 31, 32; room-tiles 1, 2, 27 (the 133 part is d-none), 31, 33 (×4), 38;
      warps 1 (×2), 16, 19; rng/seeds 2, 4, 5, 7, 10.
    - In part: drlg/README 2 (`sub_0066B030` not reached), 3 (level type 31 only here; 16 and 21 from
      run:2026-10-14-collision; 22, 27, 28, 30 not reached); rng/seeds 8 (three of six callers), 9 (the counts; no
      room without entries), 14 (the seed; ClientRoomAt is never asked for (0, 0)).
    - Contradicted: rng/seeds 6. The parser cuts a switch's value at the next `-`, so `-seed -2147483648` gives no
      override; `2147483648` saturates at `0x7FFFFFFF`. Phase 3 rewrites step note 2 (backlog).
    - Shortfall: room-tiles 15 (×2), 30 (no orientation-3 merge) and the S4a rows room-tiles 4 (×2), 14 (×2), 28 (×3),
      37 (no merge through rows 0–5, row −2 or the 8/9 edge rule, in 11 490 merges over seven walled levels).
  - **Corrections found:** `RoomTilesRelease` nests on the same room (the outer call changes nothing); 
    `RoomNeighboursEnsure` also runs after `LevelUnloadCheck` clears a room's `+0x2C`.
- **2026-10-16 — Batch H5c reviewed (architect, `lane/h5c`): accept with fixes.** `main` (`39ad54e`: the plan 0032
  owner-played addendum and the `lane/swb` spec pass) merged into the branch first; the backlog conflict was an append, both kept.
  - **Checks rerun** (read-only, `python3 -I`, no game or slot):
    - The manifest hashes to the cited `f86acdbf…4d2b97`, and all 11 logs match it.
    - `drlg.py roomk` on the eleven logs: 2071 activations, 87 223 checks, 0 mismatches. Every count the ledgers cite
      is in its coverage lines.
    - On the nine logs with an applied `-seed`: `drlg.py gen` 99 339 checks, `collision.py check` monspawn 150 095 and
      collision 14 456, `rng.py seedtree` 117 395/117 395 (per log, summed). All 0 mismatches.
    - No regression: `roomk` on the six run:2026-10-11-drlg-roomk logs gives 11 734 / 0. `seedtree` on the twelve
      `run-*.log` gives 5 976 / 5 976. The gate is green.
  - **Logger revisions.** The checker skips a line a session lacks, and the counts respect that:
    - `r64` comes from s7–s11 only (374 calls);
    - RNE/WPL come from s6–s11 (695 calls);
    - s1's PresetLevelBuild lines are reported as "act copy not logged" and are not attributed to a copy.
    - One count did not respect it: the town-callback count of drlg/0003 included one s1 build. Fixed below.
  - **Addresses read with r2:**
    - **The parser.** `0x00405710` copies a switch's text until `-` or NUL (`cmp al, 0x2d` at `0x00405784`).
      `GAME_InitSeeds` takes the override path only when `g_SeedOverride` (`0x00731004`) ≠ −1, and
      `ApplySeedOption` passes only non-zero values. So `-seed -2147483648` (passed as two argv items, `d2run.py`
      L259) leaves no override, as the s9 `GAME override=0` line shows.
    - **The nested release.** `RoomTilesRelease` with `EDX` 0 and `+0x30` ≠ 0 calls `0x0061A910` (`0x0066F1CA`).
      That function calls the wrapper `0x0066B4C0` at `0x0061A9D7`. The wrapper writes `+0x30` ← 0 and `+0x60` ← arg
      & 1, then calls `RoomTilesRelease` again with `EDX` = (`act+0x50` = 0), only while `0x100000` is set.
    - **`+0x2C`.** `LevelUnloadCheck` frees `[room+8]` and zeroes `+0x08` and `+0x2C` at `0x006431BD`/`0x006431C0`.
      All three callers of `RoomNeighboursEnsure` test `+0x2C` = 0 first: `0x0061B190`, `0x0061B39B`, `0x0061B760`.
    - Both changed readings are anchored. Each is a new code reading that the logs confirm (S4a ruling 1).
  - **Contradiction.** rng/seeds 6 is a correction, not a raise. It is counted on its own, and inventory § 2.6 records
    it. The old `[I]` in rng/0002 (L39) was left unmarked. It now carries a strike and a "Contradicted" note, scoped to
    the command line: the `D2.ini` route was not run. The spec-writer entry for step note 2 stands.
  - **Symbols.** The six I → C moves are justified: `WarpExitPos`, `LevelUnload`, `LevelRoomStateRestore`,
    `RoomNeighboursEnsure`, `RoomTileFree` and `RoomTilesRelease`. So is the new `RoomReleaseWrap` at C. Each rests
    on the reading plus a reproduction of every logged call (1516 field-by-field releases, 188 unloads, 191 restores,
    695 ensures, 4 exits). `RoomTilesRelease`, kept `[I]` at the S4a review, now has the release compare that review
    lacked.
  - **New at the review (backlog to the reverser and the spec-writer).**
    - `RoomNeighboursEnsure` skips `WarpPairLink` for a room of level 133 (`cmp [level+0x1D0], 0x85` at `0x0066C39B`).
    - drlg/0007 § 2's 133 → 17 bullet says the pairing code "does not test the level". That is contradicted for this
      caller.
    - Level 133 is unreachable, so the F1 raise stands for the levels run, but the spec must state the exception.
  - **Fixes (on `lane/h5c`):**
    - **room-tiles 27: raised → in part.** Its level-133 part is d-none, which is the S4a standard for drlg/README 7
      and 14.
    - drlg/0003: the client town callbacks are 15 builds, not 16. One s1 build whose act copy was not logged is
      excluded. The second exit `0x006681F0` is seen on one build (the s1 and s2 loggers lack it).
    - drlg/0002: the release bullet now says that the logic-record free runs on every call, unbuilt rooms included
      (`0x0066F1D4`).
    - rng/0002: the activation-flag counts are labelled as the nine sessions'. The eleven-log counts are added.
    - The run record says "twelve `run-*.log`", not eleven (5 976 is the sum over twelve).
    - The old rng/0002 `[I]` is marked contradicted (above).
  - **Rulings on the lane's points.**
    - (1) The logger revisions are handled correctly. The per-session table in the record is the standard for later
      batches.
    - (2) Excluding s9 and s10 from the seed-dependent checkers is correct. Their `-seed` was not applied as the
      header says, which is the finding itself. `roomk`, which needs no map seed, covers them.
    - (3) Both changed readings are accepted as anchored corrections. The `+0x2C` refinement rests on 1 logged case
      plus the code at `0x006431C0`. Phase 3 writes it into drlg/warps F1 (the existing entry).
    - (4) **The merge remap stays `[I]`, as a shortfall, and becomes an S1f candidate.**
      - **No forced run.** ADR-0013 asks whether the edit would be read by the code described. Yes, it would. A
        remap needs a bit-2 wall cell without bit 7 against a neighbour entry without flag `0x1`. The only way to
        force one is to edit the wall cells: DS1 walls or the LvlSub/LvlPrest rows that place them. `RoomCellBuild`
        and `Bit2TileMerge` read exactly those cells, so the result could never back `[C]`.
      - **No owner session.** No stock location is known to remap. 50 586 merges across S4a's 42 logs and seven
        walled levels never reached one. An owner playing without a target would not do better than the agent-driven
        walks.
      - **Route.** Bit2TileMerge's remap block is a function of the room, neighbour and entry fields, the cell word
        and two `.rdata` tables. ADR-0015 emulation fits it best. The row −2 and 8/9 edge returns leave before any
        callee; the remap result reaches `PickTile`; the orientation-3 branch allocates through `AddWall`. The S1e
        lane decides whether the read set is declarable and proposes S1f. Before that, a static question for the
        reverser decides whether the spec may call the path unreachable on stock data: does any stock outdoor border
        produce a wall entry with neither flag `0x1` nor cell bit 7?
    - (5) **S4a's 9 returned statements are fairly closed.** warps 16 is raised on the new RNE/WPL lines (695 calls,
      725 marks, 12 pairings), with the `+0x2C` refinement. The 8 room-tiles statements are a fair shortfall: H5c ran
      the route S4a set (walled levels, counted with the same `Model` through `drlg.py roomk`, since `sweep_s4a.py
      roomk` takes fixed sets). It also showed that the 111/112/117 cells are `RoomCellBuild`'s level branch, not the
      edge rule. Three walled-level attempts in a row with no remap is a sound stopping point.
  - **Final:** 41 statements: **23 raised, 6 raised in part, 1 contradicted, 11 shortfall**. By spec:
    - drlg/README: 4 raised, 2 in part;
    - preset: 2 raised;
    - room-tiles: 8 raised, 1 in part, 11 shortfall;
    - warps: 4 raised;
    - rng/seeds: 5 raised, 3 in part, 1 contradicted.
  - **Next:** merge `lane/h5c`. H5e, then H5a, may take slot 4. The S1e lane adds the 11 merge statements to its S1f
    review (inventory § 2.6).


- **2026-10-16 — Batch S2b done (reverser, `lane/s2b`, static).** 58 statements (items/affixes 19, items/properties 13,
  items/uniques-sets 26): **32 raised, 16 raised in part, 1 shortfall, 9 reclassified** (d-none 6, b 2 → H2b,
  a-run 1 → H2b; [inventory § 2.6](0038-inventory/README.md#26-moves-made-by-the-batch-reviews), § 5 and § 7 updated).
  - **New check:** `ITEMS_RollStaffMods` is modelled (`affixes.staff_mods`, re-read in r2), which removes the last
    ADR-0004 oracle of the affix chain. It predicts:
    - 105 stock exit seeds;
    - every join seed of the logs without the affix lines;
    - the stat-107 entries at `LX`.

    The default of every checker stays the oracle.
  - **Second sources:**
    - the 148 stock logs of five item runs and the 122 ItemRatio-only forced logs (ADR-0013, read list in
      items/0004 S2b row 3), sha256 checked;
    - full-table checks;
    - raw scans of the image next to Ghidra's references, r2 instruction scans for the "not read" claims, and two
      Ghidra call-graph closures.
  - **Counterfactuals** are reported as sensitivity only.
  - **Corrections for Phase 3:**
    - mode 6 of `PROP_ApplyBlock` is the runeword path, not the set bonus (properties 1);
    - the `op` columns are read by the stat evaluation on the creation path (properties 2);
    - the candidate maximum is 188 type-eligible rows, not 165 (affixes 15);
    - "+1 fallback not reached" is out of date: it is reached 7 times in IR.
  - **Ledgers:** [items/0004](../findings/items/0004-uniques-sets.md#plan-0038-batch-s2b-2026-10-16),
    [items/0005](../findings/items/0005-affixes.md#plan-0038-batch-s2b-2026-10-16) and
    [items/0006](../findings/items/0006-properties.md#plan-0038-batch-s2b-2026-10-16); addenda under 8 runs.
  - **Tools:** `tools/items_sweep.py`, `tools/test_items_sweep.py`; `--staff model` in `affixes.py` and
    `items_chain.py`; `props.FLOOR_CF` and `affixes.PICK_CF`, off by default.
  - **Symbols:** `ITEMS_RollStaffMods` and `sub_005C0F90_StaffModsRoll` I → C. Review requested (backlog).
- **2026-10-16 — Batch S2b reviewed (architect, `lane/s2b`): accept with fixes.** `main` (`39ad54e`: S4a, the plan
  0032 owner-played addendum, `lane/swb`) merged into the branch first. The conflicts in the plan log, the backlog,
  items/experiments and inventory § 2.6 were appends, and both sides were kept. The branch's stale copy of the S2a
  tc 64 backlog entry was dropped for main's newer one.
  - **Checks rerun** (read-only, `python3 -I` under a 4 GB memory cap, one at a time; no game, wine, slot or Ghidra):
    - `items_sweep.py logs`: 148 stock and 122 IR logs match their manifests, and the batch manifest hashes to the
      cited `870bc2ee…3f082f1`.
    - `staff`, `cf`, `scan`, `tables` and `static --closure …` print, line for line, the kept `sweep-s2b-*.txt`
      reports. `staff`: 0 failed, and 75 + 3 + 27 = 105 stock exit seeds.
    - `affixes.py check` on the 51 affixes logs gives 3 102 reproduced, 0 failed, with the oracle (the default) and with
      `--staff model` alike. `test_items_sweep.py`: 11 tests OK.
    - Gate green. `re/symbols.csv`: 1 814 rows, no duplicate address or name.
  - **Rows spot-checked** (14): aff 3, 7/16, 15, 27, 28, 30 (I2–I6), 34; prop 1, 18 (L450); us 3, 6/28, 20, 32, 33.
  - **Addresses read with r2:**
    - `ITEMRATIO_Select` is called at 0x00556FD9 and 0x005586DB.
    - `push 6` at 0x006600FC, then a call of `PROP_ApplyBlock` at 0x006600FE (`RUNEWORD_Apply`).
    - `or` at 0x005565B6 and `and` at 0x005660EB, both on `[… + 0x1B24]`; `lea` at 0x00530A53.
    - Writes of `g_UniqueCandidates` at 0x00556902 and 0x00556909.
    - The staff-mods `js` at 0x005C1121 and the ilvl 36 compare at 0x005C100A.
  - **Rulings on the lane's points.**
    - (1) **ItemRatio-only forced runs.** They are admitted under ADR-0013 for every claim the lane cites them for.
      us 3's read list holds:
      - the raw scan finds `g_pItemRatio`/`g_nItemRatio` only in the loader and `ITEMRATIO_Select`;
      - the two call sites above are the drop roll and `sub_00556F60`'s drawing body;
      - the closure under `ItemCreateByQuality` reaches `ITEMRATIO_Select` only through that body.

      The inputs these claims read (the base, the record's flag, the tables) are stock at entry. What counts is not the
      number of cases but whether a case **decides** the claim against the alternative reading:
      - one case is enough where the alternative would give a different output for certain: aff 34's q5 skip (a pick
        would move the seed), us 33's repeat (a once-per-game test forbids it), the two us 6/28 set-29 omissions, the
        7 prop 18 fallbacks, and the deterministic integer outputs of aff 27 (`M` 16 and the four 75 % damage stats,
        two of them at their floors);
      - one case is **not** enough where a wrong reading would match it by chance: aff 28's durability value
        `M/2 + RangeB(unit seed, M/2)` = 15 matches about one time in eight under another seed or range form. aff 28 (2
        statements) moves to **raised in part**: "not on the item seed" is `[C]` (55 asserted seeds, 52 stock), and
        the `RangeB` draw on the unit seed stays `[I]`.

      Stock counts were not stated on every IR-only line. "Stock: none" is now written on aff 27, aff 34, prop 18
      (L450), us 6/28 and us 33. As ADR-0013 requires, no frequency claim rests on IR. Phase 3 writes "the fallback is
      reached" (prop 18), never how often.
    - (2) **The r2 instruction scan for "not read"** (aff 3, us 4) is a second source in the sense of S2a's raw xref
      ruling, under two conditions:
      - the function set is closed over the code that holds the record (the callees that take it are listed);
      - the patterns cover every base the record is addressed through.

      us 4 met both (the `EBX` = record + 0x2C cursor is in the pattern list). aff 3 did not:
      `ITEMS_PickMagicAffix` walks the records with `ESI` = record + 0x60 (0x005C16D0), so a read of `levelreq` would
      appear as `[esi + 5]`, which the patterns missed. At the review I listed every non-stack memory operand of the
      seven functions, with its width, and none overlaps the not-read bytes. The cursor reads are `[esi − 0xC]`, `− 8`,
      `− 4`, `+ 0`, `+ 4`, `+ 6` (`classspecific`, byte), `+ 0x22` and `− 0x3E`. A pattern set for the cursor is
      added to `NOT_READ` (151 instructions, 0 matches). aff 3 stays raised.
    - (3) **The staff-mods model is accepted as evidence rule 4.** It asserts 105 stock entry seeds, predicts their
      exit seeds, and predicts the 107 entries of 4 stock and 39 IR items. This is the replacement of the ADR-0004 oracle
      on the recorded logs, as that ADR intended. The oracle can stay the checkers' default.
      - `ITEMS_RollStaffMods` and `sub_005C0F90_StaffModsRoll` I → C are justified on their core. The remainders are
        named in aff 30.
      - `count-ge` passes, so it is only a consistency check. aff 30 (I2–I6) therefore also keeps `[I]` on the strictness
        of every threshold at its boundary value except the classic tier stop: the 90/70/30 count thresholds, the
        80/30/10 tier offsets, the 90/60 level thresholds and the ilvl 36/24/18/11 thresholds. No flip was run on these
        except `count-ge`.
    - (4) **The Phase 3 corrections are accepted.** I re-read mode 6 in r2 (above), and `tables` prints 188/135.
      Phase 3 takes them from the backlog entry, and also the aff 28 split and the aff 30 threshold remainder.
    - (5) Items found in passing go to their batches: the record quality 7 → 4 chain to H2b with uniques-sets 7 and
      35, and the cube low build to S2c.
  - **Fixes (on `lane/s2b`):**
    - aff 28 ×2 moved to raised in part;
    - remainders added to aff 27 and aff 30 (I2–I6);
    - "Stock: none" on the five IR-only lines;
    - the aff 3 cursor note and the `NOT_READ` cursor entry in `tools/items_sweep.py`;
    - the items/0005 header and tally;
    - inventory § 2.6: the S2b heading, and the totals recomputed after S4a. The lane's 617/523/374 predate S4a;
      static is now 605, harness 532 (H2b 24, H5c 41), and 377 rows are blocked (d-none 252).
  - **Final:** 58 statements: **30 raised, 18 raised in part, 1 shortfall (us 12), 9 reclassified** (d-none 6; b 2 and
    a-run 1 → H2b). By spec, items/affixes has 9/8/0/2, items/properties 7/4/0/2 and items/uniques-sets 14/6/1/5.
  - **Next:** merge `lane/s2b`. Phase 3 for items/affixes, properties and uniques-sets follows the spec-writer entry.

- **2026-10-16 — Batch S3a done (reverser, `lane/s3a`, static).** 69 statements (monsters/pool 13, spawn 23, special 14,
  stats 10, README 1; hirelings 3; player/creation 5): **21 raised, 18 raised in part, 0 shortfall, 30 reclassified**
  (d-none 18, a-run 4 → H4a 2 and H4b 2, b 2 → H4b, c-emu 3 for the S1f proposal, d-owner 1, d-sim 2; recorded in
  [inventory § 2.6](0038-inventory/README.md#26-moves-made-by-the-batch-reviews), § 5 and § 7 updated for the review). Second
  sources: re-analysis of the 168 kept logs of seven runs (sha256 against the records) with the existing checkers at 0
  mismatches, a new model of `MonRegionFindAdd` that reproduces 4568 creations and 1145 region snapshots, counts from the
  raw lines (guards, the `0x80` bypass, the special count, group walks, stub checksums), writer/reader pairs read in r2
  (the stub checksum, the hire table) and full-table checks. Ledgers in the "Plan 0038 batch S3a" sections of
  [monsters/0001](../findings/monsters/0001-level-pool.md#plan-0038-batch-s3a-2026-10-16),
  [0002](../findings/monsters/0002-room-population.md#plan-0038-batch-s3a-2026-10-16),
  [0003](../findings/monsters/0003-special-monsters.md#plan-0038-batch-s3a-2026-10-16),
  [0004](../findings/monsters/0004-stats.md#plan-0038-batch-s3a-2026-10-16),
  [hirelings/0001](../findings/hirelings/0001-hirelings.md#plan-0038-batch-s3a-2026-10-16) and
  [player/0001](../findings/player/0001-creation.md#plan-0038-batch-s3a-2026-10-16); addenda under the seven runs; tools
  `mon_sweep.py`, `test_mon_sweep.py`. Surprises: two `[C]`/`[I]` statements are wrong and corrected in monsters/0004 (a
  `SetBoss` champion-pack member walks its MonStats minions with flag 0; the velocity bonus is 100 for `Velocity` ≤ 8, not
  ≤ 9); every creation-time stat-7 rescale is at full life, so the x87 rows have no observable before combat. Review
  requested (backlog).
- **2026-10-16 — Batch S3a reviewed (architect, `lane/s3a`): accept with fixes.** `main` merged into the branch twice
  (`b349849` → `39ad54e`, then `3f58dc5` with H5c); the plan log, backlog and inventory § 2.6 conflicts were appends, both
  sides kept, S4a and H5c first.
  - **Checks rerun** (read-only, each under `systemd-run --user --scope -p MemoryMax=4G python3 -I`, one at a time; no
    game, wine or slot): `mon_sweep.py logs` (168 logs, every sha256 equal to its record; batch manifest `274ed527…f37b`
    reproduced), `pool`, `spawn`, `special`, `stats`, `hire`, `player` and `tables` each exit 0 and print the counts the
    ledgers cite. Rows checked against the output: pool 4, 10, 11, 13, 17, 22, 27 (the `tries ≤ 0` cf passes, as filed);
    README 1 (10 782 = 1786 + 4428 + 4568); spawn 15, 17, 21, 37, 46 (342 and 542 passes), 54 (399); special 3, 23, 28
    (64 and 621 walks), 39, 73; stats 25 (354/8), 36, 38 (76 calls); hirelings 4, 19, 26; player 7, 10, 13, 14, 26.
    `test_mon_sweep.py`: 9 tests OK (run as a script; `-m unittest` under `-I` does not find the module). Gate green;
    `re/symbols.csv` has no duplicate address or name.
  - **Addresses read with r2** (pinned image, sha256 `631066c1…`):
    - `sub_00547BC0_MonRegionFindAdd`: the class is the word at `unit+4`; `class − 0xC3` indexes a byte table at
      `0x00547CB8` whose zero entries (indices 0, 1, 99, 101) jump to the `return 0` at `0x00547C0A`, so classes 0xC3,
      0xC4, 0x126 and 0x128; the entry walk compares the word at `+0x14 + 0x34·i` for `i < byte [+0x12]`; `i ≥ 13`
      returns 0 (`0x00547C43`); `byte [MonStats2 + 0xEC] ≤ 2` (`0x00547C87`) jumps to `mov eax, esi`, the next slot
      unwritten; otherwise the slot gets the class, `+0x12` is raised and `0x005BDB20` is called with `unit+0x20`, the
      slot and 3. The lane's reading holds in every branch.
    - `sub_005A1910_UModFast`: `0x800 cdq; idiv esi` at `0x005A1951` (signed), `− 0x80`, `≤ 10 → 10`, `≥ 100 → 100`,
      then `AddStat(67)`; `Velocity` ≤ 0 adds nothing. So 99 at 9, as corrected.
    - `MonSpawnTry` at `0x005B2ED6`–`0x005B2EED`: `MonPostCreateMods` (`0x005B21B0`), then `0x005B1CF0`, then
      `test bl, 0x40` and `MinionsSpawn` (`0x005B2830`, its only call site) when the flag is clear. That is the code path of
      the `SetBoss` correction.
    - Stub checksum: `D2S_Checksum(0x0077AC10, 0x14F)` at `0x0043C71A`, stored at `0x0077AC1C` (= stub `+0x0C`) at
      `0x0043C731`; `D2S_ReadHeader` zeroes `+0x0C` at `0x0056A0DF` and calls the same function at `0x0056A0E6`. Box test
      `0x0054ED25`–`0x0054ED2F` and the hire stride `shl ecx, 4` at `0x00576177` as cited.
  - **Rulings on the lane's points.**
    - (1) The `MonRegionFindAdd` reading is anchored (above) and new to the batch; the model built on it reproduces the
      unit seed and every appended set in 4568 creations and the region in 1145 snapshots. That is evidence rule 4, as
      ruled for S4a. The `cf no append` (553 fail) is a sensitivity check, and a review cf that appends regardless of
      `TotalPieces` fails 673, so the logs decide the `TotalPieces` > 2 condition and the unwritten-slot return. The
      13-entry bound was not met (the largest snapshotted region holds 10 entries), so **pool 22 is raised in part**,
      remainder that bound; the four excluded classes are new `[I]` claims, already in the spec-writer entry.
    - (2) Both corrections in monsters/0004 hold: the velocity bonus by r2 (above) and 76 logged calls; the `SetBoss`
      member's minion walks by the `MinionsSpawn` call site (above) and 64 walks whose units are exactly those minions.
      The corrections were written as dated notes and the old text kept, which is the addenda rule.
    - (3) The 30 reclassifications are accepted. The guard rows are d-none by the plan's definition (a guard stock data
      never fails), with spawn 45 rightly split out as reachable. The header mentions (spawn 8, 13, 29, 32, 34; special
      41) carry no claim; d-none is accepted on condition that Phase 3 rewords them with their blocks rather than keep an
      `[I]` mention. The 3 c-emu rows (pool 27, stats 9, 11) meet ADR-0015 condition 2 on their face (`MonVariantRoll`
      reads the entry, its MonStats2 record and the seed; `MulDiv` is pure) and wait unbatched for the S1f proposal,
      which now lists 41 candidates (27 + H5c's 11 + 3).
    - (4) H4b already runs with its 43-row list; the four S3a rows it should pick up (pool 8, spawn 6, spawn 45, special
      65) and their two logger pieces are in a backlog entry to the H4b lane. H4a's two (special 34, 48) wait for H4a.
  - **Fixes (on `lane/s3a`).**
    - pool 22 recounted as raised in part (above); monsters/0001's header and the `MonRegionFindAdd` symbol row note it.
      The symbol stays C on its core, as S4a ruled for its symbols.
    - special 64's remainder also names the open-quest side: all logged characters had every quest done, so the logs
      exclude only a test that a done quest fails.
    - Inventory § 2.6: the S3a section moved after H5c's and titled as reviewed; the table header lost in the first
      merge restored; the net effect recomputed after S4a and H5c, with the 3 c-emu rows counted apart.
  - **Final:** 69 statements: **20 raised, 19 raised in part, 0 shortfall, 30 reclassified** (d-none 18; a-run 4 → H4a 2,
    H4b 2; b 2 → H4b; c-emu 3 for S1f; d-owner 1; d-sim 2). By spec: monsters/pool 4/6/0/3, spawn and README 7/0/0/17,
    special 4/5/0/5, stats 2/3/0/5, hirelings 0/3/0/0, player/creation 3/2/0/0. Static batches now hold 584 statements,
    harness batches 535 (H4a 31, H4b 47, H5c 41), 3 are c-emu awaiting S1f and 392 are blocked.
  - **Next:** merge `lane/s3a` (owner). The spec-writer entry (the two corrections, the FindAdd consumers) is for Phase 3.

- **2026-10-16 — Batch S4b in progress (reverser, `lane/s4b`, static; no slot, no game).** Committed so far: the checks
  `tools/sweep_s4b.py` (objdump call-graph walker as the second tool next to Ghidra; checks `rng`, `initfn`,
  `operate`, `portal`, `grid3`, `defs`, `callers`, `scans`, `data`, `dt1`, `temple`, `chestroom`) and
  `tools/test_sweep_s4b.py`. The S2a tc 64 item is also in: the addendum under run:2026-10-15-objects, and the chest tier
  arithmetic in items/0001 § 2, now `[C]`. `re/symbols.csv`: 4 rows I → C, 2 added. The per-finding ledgers, the
  inventory moves and the review request follow.
- **2026-10-16 — Batch S4b done (reverser, `lane/s4b`, static; no slot, no game).** 44 statements: **19 raised, 13 raised
  in part, 7 shortfall, 5 reclassified** (proposed in inventory § 2.6, pending review). The ledgers are the "Plan 0038
  batch S4b" sections of drlg/0002–0008 and objects/0001. The second tool is GNU objdump, walked by `tools/sweep_s4b.py`;
  Ghidra's `rngcallgraph` and xrefs were rerun on the `ghidra-s4b` copy.
  - **Shortfalls (7):** collision 2 (no client build in any log), warps 20, preset 36, room-tiles 9 and 20 (data flow,
    or exact lists for the `LevelId`-0 records), and two contradictions recorded as corrections: objects 25 (nine InitFns
    create monsters) and preset 27 (the `Outdoors` bit has a reader).
  - **Reclassified (5):** collision 4 and room-tiles 3, 35 → d-none; collision 39 → a-run H5b; preset 6's second
    statement → c-emu (S1f).
  - **S2a tc 64:** done. items/0001 § 2 holds the tier arithmetic `[C]`, and the addendum is under
    run:2026-10-15-objects.
  - **Symbols:** 4 I → C, 2 added. Gate green. Review requested (backlog).

- **2026-10-16 — Batch S4b reviewed (architect, `lane/s4b`): accept with fixes.** `main` (`e556014`: S2b, S3a and H5c)
  merged into the branch first. The conflicts were appends: H5c's sections after S4b's in drlg/0002, 0003, 0004 and
  0007; the plan log, the backlog and inventory § 2.6 with main's entries first. In the backlog, the struck copies of
  duplicated entries were kept, and the S2a tc 64 entry keeps the lane's struck (a) plus main's "(b) done" note.
  - **Checks rerun** (read-only, under `systemd-run --user --scope -p MemoryMax=4G python3 -I`; no game, wine, slot or
    Ghidra): `sweep_s4b.py all` exits 0, and every `S4B` line gives the counts the ledgers cite (rng 56/56 and 4/4
    drawing functions, 98 and 11 sites, 852/852 LCG operands; initfn contra 9; operate 7 + 7; portal 12; dt1 28; data
    81, 1091, 2274 − 2 unparsed; temple 0 mismatches; chestroom 59/59). `tc_sweep.py chest`: 59 reproduced, 0 failed.
    `test_sweep_s4b.py`: 4 tests OK. Gate green.
  - **Addresses read with r2 or objdump** (pinned image, sha256 `631066c1…`):
    - `LevelIsTown`: `lea eax, [ecx − 1]; cmp eax, 0x6C; ja → 0`, byte table at `0x006426C8`, jump table at
      `0x006426C0` whose entry 0 returns 1. The zero bytes are at ids 1, 40, 75, 103 and 109.
    - `RoomIsOutdoors` (`0x0066BA70`): type 1 returns 1, type 2 returns `[room + 0x28] & 0x80000`. The caller
      `0x00460EEA` calls `0x0061AA40`.
    - The preset rewrite guards `cmp edi, [… + 0xA80]; jge` at `0x00665CC0` and `0x00665CFC`. `MONSTATS_ValidId` is
      8 instructions (the lane wrote 7) and reads only `nMonStats`.
    - The Burial Grounds table at `0x006F0750` lies in `.rdata` (read-only), and its anchors are as filed. The loop
      skips the checked slot (`cmp ebx, edi`). Slot 2 shares slot 4's anchor; the claim is only about slots 5–14.
    - The `SUnitPathCreate` switch (`0x005548B7`, table `0x00554A18`): types 0, 1 and 3 call `0x00649D00`
      (`PATH_DynamicCreate`), type 2 calls `OBJECTS_GetRecord`.
    - `g_ObjGoreLimit`: one occurrence of the address bytes in the image (`0x00552793`, operand of `0x00552791`).
    - `OBJECTS_GetRecord`: `imul eax, eax, 0x1C0` at `0x00640EC8`.
    - Call sites, counted by objdump: `PresetInstanceCreate` 3, `PresetSetFile` 1, `PortalObjectCreate` 12,
      `TileCollisionUpdate` 3, `DUNGEON_RoomCreate` 1, `LvlMazeByLevel` 1, all at the addresses cited.
    - `+0x780`/`+0x784` in all of `.text`: besides the three cited operands there are only stack frames
      (`[ebp − 0x784]`) and two `push 0x780` allocation sizes. LvlTypes records are `0x788` bytes, addressed by
      `imul …, 0x788`, so no cursor reaches `Act` or `Expansion` through another displacement.
  - **Rulings on the lane's points.**
    - (1) **objdump as the second tool is accepted**, as S2a's raw xref scan was, for caller, operand and RNG-walk claims.
      It decodes the image independently of Ghidra's analysis, and the walk is a separate implementation. Its function
      counts differ from Ghidra's by design. The drlg/0003 row 17 accounting was short by 9: these are Ghidra functions
      whose entries the walk reached inside another body by a tail jump. The corrected sum is 757 + 104 + 19 + 9 = 889.
      The room walk adds up the same way (536 − 5 entries only the walk lists + 104 + 18 + 4 = 657). The RNG function and site
      sets are equal in both walks, which is the claim.
    - (2) **The two contradictions are handled correctly.** They are recorded as dated corrections with the old text kept,
      not raised, and the spec-writer and archivist entries carry them to Phase 3 and the table docs. Objects row 25's
      new `[I]` (the nine InitFns draw as monster spawns) needs a run to raise it; H5b or H4a may meet it.
    - (3) **The bit-0x40 marks belong to drlg/warps.** Accepted: the scan's `0x30000` room bits are warps D1's.
    - (4) **Preset 6's first statement** is raised on the invariance (the S2a tc 50 exception): the guards read above make
      the rewrite unreachable for those ids, and the logged instance lists hold such units unchanged. Accepted.
    - (5) **S2a tc 64 is accepted as `[C]`.** The review recomputed the tier distances of the 59 calls. `v = a + t` occurs
      in 14 calls and `v = a + 2t` in 5, so the logs decide both compares' strictness. `b ≥ a` holds for every act,
      difficulty and game type (30 cases), so `|b − a|` has no stock observable. That remainder is written into
      items/0001 § 2. The 4 symbols I → C (`ObjectChestDrop`, `LevelMonLvl`, `TC_GetChestTC`, `LevelIsTown`) stand on
      their cores.
    - (6) **The five reclassifications are accepted.** collision 4 is d-none on the switch above; room-tiles 3 and 35 are
      d-none because `dt1` counts duplicate files as the game would; collision 39 goes to a-run H5b, which has not
      started (§ 5 recipe updated); preset 6 (second statement) is a c-emu candidate.
  - **Fixes (on `lane/s4b`):**
    - drlg/0003 row 17: the function accounting.
    - objects/0001 row 1: the spec now names 109 functions after the `lane/swb` merge; the same 10 operands.
    - drlg/0004 row 6 and inventory § 2.6: 8 instructions.
    - items/0001 § 2: the boundary and `|b − a|` note.
    - Inventory § 2.6: the S4b heading as reviewed and its net effect. The totals are recomputed once over all six
      reviews, because the S2b and S3a lines were each computed without the other. The § 2.4 table of moves was added,
      and § 5 and § 7 were updated (S2a 57, S4a 77, S3a 39, S4b 39 with tiers recomputed from the returned rows; H5b 33).
  - **Final:** 44 statements: **19 raised, 13 raised in part, 7 shortfall, 5 reclassified**, as filed. **Totals now:**
    static 570, harness 539, c-emu awaiting S1f 4, blocked 401 (d-none 273), deferred 2, raised 10, which is 1 526.
    S1f has 42 candidates.
  - **Next:** merge `lane/s4b` (owner). Phase 3 for drlg and objects follows the spec-writer entry, and the archivist
    entry fixes LvlPrest and LvlTypes.

- **2026-10-16 — Batch S1b done (reverser, `lane/s1b`, static; no slot, no game).** 76 statements (data/README 1,
  data/calc 6, data/excel 54, data/strings 6, rng 4, rng/seeds 5): **47 raised, 28 raised in part, 0 shortfall, 1
  reclassified** (data-excel 28 → d-none; proposed in [inventory § 2.6](0038-inventory/README.md#26-moves-made-by-the-batch-reviews),
  pending review). By spec (raised / in part / shortfall / reclassified): data/README 0/1/0/0, data/calc 3/3/0/0,
  data/excel 34/19/0/1, data/strings 5/1/0/0, rng 2/2/0/0, rng/seeds 3/2/0/0.
  - **Tool:** `tools/sweep_s1b.py` (checks `logs`, `arch`, `compile`, `survey`, `tc`, `items`, `strings`, `calc`,
    `static`, `rng`, `seeds`; `all` exits 0) and `tools/test_sweep_s1b.py` (6 tests). Report
    `workspace/logs/sweep-s1b-all.txt`, log manifest `workspace/logs/sweep-s1b-manifest.txt` (`d06d2aac…c9506fb`, 299 logs).
    The second tool is GNU objdump through `tools/sweep_s4b.py` and the raw scan; Ghidra was not needed.
  - **Second sources:** the pinned game's own `-direct -txt` compile (run:2026-10-15-cube-saves: 88 of 90 written `.bin`
    byte-identical to the shipped ones), counterfactual data roots for the archive order (d2data's and d2exp's DS1
    copies give 1 751 and 564 mismatches on the preset logs, d2exp's `patchstring.tbl` 3 964 on the strings run; 41 d2exp
    `.bin` have another record size), 4 999 logged (item code, index) pairs, the 9 390 stock TC calls replayed with the
    model's TC array, the strings and calc runs per caller, and 91 objdump-pinned instructions with raw-scan counts.
  - **Findings for Phase 3 and other lanes:** the data/0004 `Lilith` question is answered (the game compiles 11154; the
    shipped `monstats.bin` came from other string tables); the route premise of data-excel 30 fails (all 15 code-list
    `.bin` ship in d2exp or patch_d2); 14 LCG sites lie in 9 functions with no static reference (rng/0001); `not used` is
    not a duplicate key (data-strings 33 rests on the 3 logged duplicates and the full-table walk).
  - **Symbols:** 20 I → C. Gate green. Review requested (backlog). Nothing merged.
