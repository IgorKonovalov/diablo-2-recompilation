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
  `combat/formulas`, owned by [plan 0037](done/0037-combat-formulas.md), which starts after [plan 0036](done/0036-human-wiki-readme.md)
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

- **2026-10-16 — Batch S1b reviewed (architect, `lane/s1b`): accept with fixes.** `main` (`1f8a87e`) was already in the
  branch, so the merge was a no-op and there were no conflicts.
  - **Checks rerun** (read-only, `systemd-run --user --scope -p MemoryMax=4G python3 -I`; no game, wine, slot or
    Ghidra): `sweep_s1b.py all` (sha256 `f0df814a…`) exits 0 in 58 s. Every `S1B` line gives the counts the ledgers
    and addenda cite: arch (DS1 counterfactuals 1 751 and 564, `patchstring` 3 964, 41 + 4 d2exp `.bin`, 6 tie files
    with 0 differing), compile (90 written, 88 identical, `monstats` record 707 `NameStr` 11154/5382, 15 + 4 code-list
    `.bin` written, the 4 loader-less tables unwritten), survey (848 353 cells both sides, 0 unexplained), tc (9 390
    calls, 0 failed), items (4 999 pairs), strings (4 264 lines, 0 mismatches), calc (44 529 evaluations by pool), static
    (every pin ok), rng (852/852/852, 16 sites outside the walks, 9 unreferenced bodies), seeds (876 + 3 552 predicted).
    `test_sweep_s1b.py`: 6 tests OK. Gate green.
  - **Addresses read with objdump or r2** (pinned image, sha256 `631066c1…`): the room dispatch (`[edi+4] ← eax` at
    0x0066B479; type 2 → `call 0x666630` at 0x0066B498, type 1 → `call 0x67d6d0` at 0x0066B4A8); `OutRoomAlloc` calls
    0x0040B430 (pool allocator: file/line arguments, fatal on null); `imul eax, eax, 0x1a8` at 0x0063366D and the inline
    monstats read at 0x005A3D3E–0x005A3D46; `TC_Alloc` `add eax, 0x10; imul eax, eax, 0x2c` (0x00653FB8, 0x00653FBB) and
    `imul 0x2c` at 0x00653FDC; `TC_GetByIndex` `cmp eax, [0x96c5f0]` at 0x00654E0F, `imul 0x2c` at 0x00654E17,
    `add ecx, 0x2c` at 0x00654E4E; the gem store `mov [esi+edx+0x2c], ax` at 0x00637225, the rune store `+0x82` at
    0x00639C6E, the rare-name loop (0x006341EA `lea edx, [esi+ecx+0x26]`, 0x006341FA store `+0xc`, 0x00634202
    `add esi, 0x48`); `g_SeedOverride` `0xFFFFFFFF` at 0x00731004 and its one write at 0x0052C326; the calc counts 4 at
    0x00745848 and 0x0074465C; `SUnitCreate` `je` at 0x00555304, `lea edx, [edi+0xd0]` at 0x00555306; the client creator
    `cmp edi, 1` at 0x0046675C, `call 0x466360` at 0x00466796, `call 0x465fd0` at 0x004667D6; the `g_MonStatsLink`
    compile callback 0x00659990 referenced by the instruction at 0x00659A55 (its bytes at 0x00659A58, as the sweep prints).
  - **Rulings on the lane's points.**
    - (1) **run:2026-10-15-cube-saves is accepted as runtime evidence** (rule 3) for what the pinned compiler does under
      `-direct -txt`: it ran the pinned `game.exe`, and the record states the setup (one loose probe `cubemain.txt`,
      every other table from the archives). It backs claims about the compile path, the cell converters and what the
      shipped `.bin` files are (88 of 90 byte-identical). It does not back by itself a claim about the stock `.bin` load
      path, which `-txt` bypasses; where a ledger states load-time behaviour it pairs the compile with the logs (row 41's TC
      numbering, for example), and data/README row 1's loose-file half adds the forced runs' loose `.bin`. The kept output
      in `workspace/runtime/game-cubeprobe/` had no hash anywhere, and a later compile in that directory would overwrite
      it, so the review pinned it: `workspace/logs/sweep-s1b-cubeprobe-manifest.txt` (91 files, `97ca5c7a…098b7caa`),
      cited in data/0001 § Plan 0038 batch S1b. The archivist's dated addendum to the record stays requested (backlog).
    - (2) **The forced runs may be cited for the excel directory (data-excel row 10).** ADR-0013 admits a forced run for
      a claim whose code reads none of the edited cells. Path construction in `DATATBLS_OpenExcelFile` reads no cell,
      and the edit changes no path, so the forced runs show the loose `.bin` at `data/global/excel/` being loaded. The
      non-forced compile run (the probe `.txt` read from, and 90 `.bin` written to, the same directory) is the stock-path
      log the ADR asks for.
    - (3) **Counterfactual data roots are accepted as the second source for the archive order** (rule 2, data behaviour
      over runtime logs). The merged tree explains every logged line, and putting the other archive's copies in place
      breaks 1 751 / 564 preset rooms and 3 964 string lines. They decide each pair only where the pair's copies differ:
      d2exp over d2data on the 89 DS1 files, patch_d2 over d2exp on 10 DS1 files and `patchstring.tbl`. The record-size
      argument on the 41 d2exp `.bin` is data-only and supports the order; it does not decide it. Ties have no
      observable (6 shared files, 0 differ), so the tie rule (row 19) goes to d-none as filed. That is right.
    - (4) **objdump closures are accepted for "no draw"**, extending the S4b ruling, on one condition: the ledger must
      account for the closure's indirect calls. The lane gave 532 indirect calls, 359 through the import table, and
      left 173 unexplained. The review counted them: 121 call a register last loaded from the import table in the same
      body, and the 52 left all lie under the pool allocator 0x0040B430 (12 of them reached first through the fatal
      paths in the item-data closure). None of those callers is passed a seed pointer. Review notes with that split were
      added to rng/0002 rows 3 and 15. Both rows stay raised, with that residue as the closure's stated limit. Outside
      the evidence, a review count showed that in the seed-tree logs all 132 type-2 rooms reach `RRESEED` with their
      creation seed unchanged, which is runtime support for row 3's preset half. It is filed for the sweep (backlog) and
      not cited.
    - (5) **Routed remainders:** accepted as filed. data/README 1 and data-excel 30 become H3b pieces (§ 5 row
      updated). data-calc 19 (hover marker) and rng-seeds 11 (`SUNITPRE` caller `ra`) are Phase 2 leftover pieces in the
      backlog. The S1e c-emu remainders were already batched. **data-excel 28 → d-none is accepted.**
  - **Ledgers checked against the rules.** Each of the 47 raises names a second source that is independent of the
    Ghidra reading (logs, compile output, objdump pins with raw-scan counts, emulator outputs). Each of the 28
    raised-in-part rows states its remainder with a class. No `[L]` was added. The 20 symbols I → C each rest on a
    raised row (the two room allocators on rng/seeds 3 under ruling 4). The `Lilith` provenance sentence is untagged
    and makes no behavioural claim, which is acceptable.
  - **Fixes (on `lane/s1b`):** rng/0002 rows 3 and 15, the indirect-call accounting (ruling 4); data/0001 § Plan 0038
    batch S1b, the compile-directory manifest (ruling 1); inventory § 2.4 (S1b row in the moves table, a-logs 320,
    d-none 274), § 2.6 (S1b heading as reviewed, the routing, the combined totals), § 5 (S1b 75 of 76, tiers 7/52/16;
    H3b pieces), § 7 (S1b done).
  - **Final:** 76 statements: **47 raised, 28 raised in part, 0 shortfall, 1 reclassified**, as filed. **Totals now:**
    static 569, harness 539, c-emu awaiting S1f 4, blocked 402 (d-none 274), deferred 2, raised 10, which is 1 526.
  - **Next:** merge `lane/s1b` (owner). Phase 3 for data and rng follows the spec-writer entry; the archivist entry
    asks for the cube-saves addendum; the reverser follow-ups are in the backlog.
- **2026-10-16 — Batch H4b checkpoint, in progress (reverser, `lane/h4b`, slot 4; stopped for a machine reboot).** No
  session was run and slot 4 was never launched (saves directory empty, no aside). There is no run record yet; the
  run id stays `run:<date>-sweep-monsters-b` and is dated when its first session runs.
  - **Committed:** `tools/gdb/mon-extra.py`, the logger extension (new tags only: `SIK` skill list after the
    MonStatsInit skill loop `0x00574137`, `HSK`, `AURS` at UModAura's `UnitSkillAdd` calls `0x005A17AF`/`0x005A175C`,
    `RS0`/`RS1`/`RS2`/`RSX` SpecialMonRestore, `MR0`/`MRH`/`MRX` MinionRestore, `MMS0` MonMakeSpecial, `HWT` the
    `0x0066E37E` write, `CTAB`/`CMA`/`CMH`/`CNB`/`CNS`/`CNT` client names with the name text, and `H4B_WATCH`
    watchpoints `WCH` on the UniqueTitle pointer, region `+0x2DC`/`+0x2E0` and Levels `+0x2F`). It parses, but it is
    **not yet sourced by `tools/gdb/mon-stats.gdb` and not yet run**; the checker `tools/sweep_h4b.py` is not written.
    No existing logger or checker was changed, so there is nothing to regression-check yet.
  - **Static readings made (to be written into monsters/0001 and 0003 with the batch):**
    - pool 1: `sub_00530930_GameCreateA` has no reference in the image: `tools/xrefscan.py 0x00530930` (rel32 and
      absolute) and `tools/ghidra.sh xrefs` both find none. Proposed **d-none** (no caller), not d-2c.
    - special 2/74: the caller `0x00583050` is entry 20 of the shrine-function table (12-byte rows from
      `0x006E1850`; row 20 at `0x006E1940`), Shrines code 20 *Warping Shrine* ("nearest monster becomes unique",
      rarity 3, LevelMin 3): it finds a monster near the shrine (`0x0065A800` with callback `0x00582750`) and jumps to
      `MonMakeSpecial`. Stock play reaches it only by operating that shrine (`objop`), which the batch has not tried.
    - SpecialMonRestore (`0x005A4440`) writes the saved name seed **after** its `SpecialModsApply` (`0x005A4569`) and,
      when a saved mod is 30, calls `UModAura` a second time (`0x005A457E`); MinionRestore runs the handlers with
      flag 0 over mods 1–4 and all nine list bytes (`0x005A4800`–`0x005A483C`).
    - spawn 43/44: the tentacle branch `0x005B2570` (one unit-seed step, start `low % 6`, offsets `0x006E2CF0`
      (o·6 + j)·8, j ← (j + 5) % 6, o = ¬(seed.hi bit 2) & 1 read at `0x005B2883`) is not modelled; 14 `MMT` blocks
      in kept logs (`collision-s2/s3-2026-normal-a3`, `monspecial-s3-2103-hell`, `monspecial-s8-2108-classic-nightmare`)
      can check a model.
    - spawn 3: kept logs already hold `MK0` mask `0x1C0` (448) for tentacle class 259 and mask 0 for spawnCol 3
      barricades (class 435 in `berserkf-310x`, `monstats-s8/s10`, …): raisable by a check over kept and new logs.
    - special 15/16/18: `objects-s13-2313-hell` (classic hell) holds `MTI` result 1 for class 80 (`sandleaper`) with
      `lightning` absent from the `MPK` candidates; re-run `tools/monspawn.py check` on it to cite.
  - **Remaining (for the resuming lane):** wire `mon-extra.py` into `mon-stats.gdb`; write `tools/sweep_h4b.py`
    (SIK against MonStats `Skill1..8` u16 `+0x170 + 2k`, `Sk1lvl..` u8 `+0x198 + k`, plus DifficultyLevels
    `MonsterSkillBonus`; AURS against `g_UModAuraTable`; client names against `tools/tbl.py` GameStrings; restore lines;
    the tentacle model; spawnCol masks; watch summary); regression-check on kept monstats logs; then the sessions
    (seeded with `monpool.py pool`): Act IV (doomknight2/3 in 106–108, willowisp3 in 105), Act II sandleaper levels
    41/42/44, Act III 77/86/87 willowisp and Kurast tentacles, Act V barricades, three difficulties, and the
    `/players 8` `MercNova` session (camels, Align 1 merc). The 43 rows (47 if the S3a review adds rows, § 2.6) are all
    still open.
- **2026-10-16 — Batch H4b done (reverser, `lane/h4b`, slot 1).** `main` (`e556014`, S3a) merged into the lane first;
  S3a's four rows taken, so the batch is 47 statements. run:2026-10-16-sweep-monsters-b: nine sessions (s1–s9; s5 split
  into two games, s5a/s5b) on slot 1, record in [monsters/experiments.md](../findings/monsters/experiments.md#run2026-10-16-sweep-monsters-b).
  - **Tools:** `tools/gdb/mon-extra.py` wired into `tools/gdb/mon-stats.gdb` (MinionRestore tags renamed `MNR*`, new
    `PMA0`/`PMAV`/`PMAX` for every MonPlace case and `RTK0`/`RTK1` for the tick on every room, an `OBJP` waypoint helper
    for the pilot); new checker `tools/sweep_h4b.py`; `tools/monspawn.py` models the tentaclehead branch and predicts
    `SpawnClassCellTest` in the presets window; `tools/monstats.py` stores the doomknight draw in appearance byte 10 (its
    73 false mismatches on s2 gone). No change of count on the kept logs apart from the new checks.
  - **Checks:** `sweep_h4b.py check` bad = 0 in all eleven parts (2 678 skill lists, 10 auras, 70 names, 11 + 31
    restores, 39 MonPlace calls, 4 785 ticks, 63 `HWT` writes, watchpoints); on the 39 kept logs 16 tentacle heads / 81
    limbs and 595 `spawnCol` 1/3 masks; `monstats.py check` 0 mismatches on every log apart from s5a (3 `LIVE` values of a
    hireling loaded from its save) and s5b (DRLG models on a second game in one process); `monpool.py check` 154/154 (s9).
  - **Outcome (47):** 35 raised, 9 raised in part (special 27, 65, 74; stats 13, 14; spawn 42), 1 shortfall (stats 40,
    no `willowisp` special), 2 reclassified (pool 1 d-none: `GameCreateA` has no caller; special 2 d-owner: only the
    Shrines code-20 function reaches `MonMakeSpecial`). Sections "Plan 0038 batch H4b" in monsters/0001–0004 and
    hirelings/0001.
  - **Corrections for the spec-writer** (backlog): a restored aura special gets two auras; `PresetFallenVariant` keys on
    the BaseId; Izual's name comes from the fixed-name branch; spawn 42's 528 is stock-reachable (filed "stays d-edit").
  - **Symbols:** `SpecialMonRestore`, `MinionRestore`, `PresetFallenVariant`, `UNameTablesFree` I → C; new
    `sub_005B2570_TentacleMinionsSpawn` (C).
  - **Next:** architect review of H4b (backlog), then merge. H4a may follow (same logger family; `mon-stats.gdb` now
    sources `mon-extra.py`).
- **2026-10-16 — Batch H4b reviewed (architect, on `lane/h4b`): accept with fixes.** `main` (`f59929e`, S1b) merged
  into the lane first (conflicts in the backlog and this log only, both sides kept; the backlog's unstruck copy of the
  S3a → H4b entry dropped for the lane's struck one).
  - **Re-run.** The nine log hashes, the session 5 split (byte-identical to the whole) and the five tool hashes of the
    record match the files. `sweep_h4b.py check` on the nine logs reproduces `workspace/logs/h4b/sweep-check.txt` line
    for line (bad = 0 in all eleven parts). `monstats.py check` (chaining `monspawn.py`): 0 mismatches on s1+s2 (17 810
    checks), s3 (3 860), s4 (3 823; guard `lo ≥ hi` 38), s6+s7 (8 198) and s5b (52); s5a+s8 1 721 checks with the 3
    recorded `LIVE` mismatches; the chained `monspawn.py` 0 on every group but s5b (1). `monspawn.py check` on the two
    kept Act V logs: 0 mismatches, 71 class-528 tests. `monpool.py check` on s9: 154/154. Read with objdump: the
    doomknight writes, the `MonMakeSpecial` jump and shrine-table entry 20, the tentacle call and `o`, the `HWT` write;
    the aura, champion-word and client-handler tables read from the file match the ledger.
  - **Rulings.** (1) **pool 1 → d-none** accepted: the raw scan finds no rel32 and no absolute reference to
    `0x00530930` (re-run at the review). (2) **special 2 → d-owner** accepted: the one reference is the Shrines code-20
    function (`0x006E1940` → `0x00583050`, read at the review). An `objop` on such a shrine is a stock action, so the row
    is not d-none; H4a may try it if a seed places one (§ 5), else the owner. (3) **Kept logs re-read** (spawn 3, 43, 44,
    the 528 half of spawn 42): accepted as H4b raises, a-logs in effect, as at S3a; each cites the kept runs. (4) **H4a
    and `mon-stats.gdb`**: H4a may use the logger as it stands. Conditions: its record gives the `mon-extra.py` sha256;
    `H4B_WATCH` and `MONSPAWN_WATCH` together arm at most four debug registers; any H4a edit to `mon-extra.py` or the
    other sourced files adds tags only and is regression-checked by re-running `sweep_h4b.py check` (summary unchanged)
    and `monstats.py check` on the nine H4b logs before a slot is taken. (5) **The s5a limit** (3 `LIVE` values of a
    hireling loaded from its save: stats 7, 12, 13 at level 30) is a model scope limit, not a contradiction: hirelings 34
    and stats 23 rest on the `SI0`/`SI1` record at `MonPlayerBonus`, which the checker reproduces. (6) **The s5b limit**
    (the DRLG models on a second game in one process; 1 `monspawn` mismatch): s5b may support only per-creation records
    that need no DRLG model, which is all it is cited for. A later session should not start a second game in one process
    unless the log is used that way; a reset in `tools/drlg.py` is a tool follow-up (backlog).
  - **Fixes.** monsters/0003: special 65 headed "raised in part" (it has a remainder, as the lane's own count says);
    special 20's "6 rows below level 20" half was met in no H4b log (every `AUR` has `lvl` ≥ 20), so the review re-ran
    `sweep_h4b.py aura` on the 25 kept logs with `AUR` lines (84 lines, 3 below 20 with `n` 6, bad = 0) and cited them;
    special 27's remainder split into d-none (clamp at 99, row 7) and an H4a piece (clamp at 1); the `MonMakeSpecial`
    open question answered. monsters/0002: spawn 42 also cites session 3's 2 class-528 tests. monsters/experiments: a
    review note. Inventory § 2.4 (H4b row, totals), § 2.6 (H4b section, combined totals), § 5 (H4b 45 of 47, tiers
    22/1/22; H4a and H5d pieces), § 7 (H4b done).
  - **Ledgers checked against the rules.** Each raise names runtime evidence next to the reading (new logger lines,
    watchpoints, reproduced models on new and kept logs); each part raise names its remainder. The 5 symbols (4 I → C,
    1 new C) each rest on a raised row. No `[L]` added. The shortfall (stats 40) is honest: no `willowisp` special met.
  - **Final:** 47 statements: **35 raised, 9 raised in part, 1 shortfall, 2 reclassified** (pool 1 d-none, special 2
    d-owner), as filed. **Totals now:** static 569, harness 537, c-emu awaiting S1f 4, blocked 404 (d-none 275, d-owner
    10), deferred 2, raised 10: 1 526.
  - **Next:** merge `lane/h4b` (owner). H4a may start (pieces in § 5); the spec-writer entry (four corrections) is for
    Phase 3; follow-ups in the backlog.

- **2026-10-16 — Batch S2c done (reverser, `lane/s2c`, static; no slot, no game).** 86 statements (items/affixes 3,
  cube 20, properties 3, quality 1, quest-drops 16, sockets-runewords 27, uniques-sets 1, vendors 15): **49 raised, 26
  raised in part, 1 contradicted, 10 reclassified** (a-run 5: cube 17, 51, 58 → H6a, quest-drops 48 → H4a, sockets 42 →
  H2b; b 2: sockets 35 → H6b; d-none 3: cube 20, 24, sockets 36 L442; proposed in
  [inventory § 2.6](0038-inventory/README.md#26-moves-made-by-the-batch-reviews), § 5 and § 7 updated, pending review).
  - **Tools:** `tools/sweep_s2c.py` (`logs`, `static`, `tables`, `cube`, `sockets`, `vendors`, `quests`, `props`,
    `all`) and `tools/test_sweep_s2c.py` (5 tests). The second tool is GNU objdump through S4b's walker, plus a small
    evaluator (`emu`) that runs a compare-and-jump-table dispatch for one register value through the objdump
    instructions: it settles NPC_MenuAction's two class lists, the store-record and list-builder switches and the
    cube's PlayerOp switch for every input value.
  - **New check case:** the cube's output placement, modelled with tools/player.py's inventory spot search on the
    3 × 4 cube grid: 100 logged cells, 0 mismatches (cube 45).
  - **Logs** (sha256 checked; manifest `workspace/logs/sweep-s2c-manifest.txt`, `5820525c…9280ba`): run:2026-10-15-cube,
    -sockets, -vendors, run:2026-10-16-quest-drops with its owner-played addendum (119 logs), the stock drop logs of
    `tools/tc_sweep.py`, and run:2026-10-16-player. Every existing checker still reproduces its run: `cube.py` 182,
    `sockets.py` 351, `questdrops.py` 0 mismatches, `vendors.py` 0 mismatches.
  - **Corrections for Phase 3** (spec-writer backlog entry): the cow portal's spot search draws nothing (cube L776,
    contradicted; the portal object draws 171–173 steps); objects 28 and 30 use record words 16 and 29, not
    `g_QuestDescs`' 32 and 41 (quest-drops A1); `NPCSTORE_Reset` is reached from Baal's death through a dropped client
    in game types 1 and 2 (vendors L73); the gem-group row count is 422 (sockets L306); Baal's death also draws the
    quest seed (quest-drops L649); a crafted pick of 0 is reachable at output ilvl ≤ 5 on four bases (cube L681).
  - **Ledgers:** "Plan 0038 batch S2c" sections of items/0002, 0004, 0005, 0006, 0007, 0008, 0009 and 0010; addenda
    under six runs. **Symbols:** `sub_00560200_InvPlaceItem` and `NPCSTORE_FindRec` I → C. Gate green. Review requested
    (backlog).


- **2026-10-16 — Batch S2c reviewed (architect, on `lane/s2c`): accept with fixes.** `main` (`7df5039`: S1b, H4b,
  plans 0039–0044) merged into the lane first. Conflicts were in the backlog, this log and inventory § 2.6, § 5 (H3b,
  H4a, H4b) and § 7 (S1b, S2c ranks). Both sides were kept. H4a now holds S2c's quest-drops 48 and H4b's pieces
  (32 statements, 0/14/18). No backlog entry appeared twice.
  - **Re-run.** `systemd-run --user --scope -p MemoryMax=4G python3 -I tools/sweep_s2c.py all` exits 0 in 43 s with
    the counts the ledgers cite. Examples: 182 transmutes reproduced; 100 placements, 0 mismatches; cow spot search 0
    steps against the portal's 171/173/171; 4 656 stock and 4 550 gamble `CFX` lines; 337 gem and rune transfers; 422
    `hasinv`/`gemsockets` rows. The log manifest keeps its sha256 `5820525c…`. `tools/test_sweep_s2c.py`: 5 tests OK.
    `sweep_s2c.py` sha256 is `832373fd…`.
  - **Read with objdump at the review.** The pinned image's sha256 matches the inventory. Checked:
    - the op switch at 0x005666C1–0x005666D1 (`sub 1; cmp 0xd; ja 0x566a42; jmp [eax*4+0x566aa8]`);
    - the cow portal's pushes 0x27/0x3C before 0x00594228;
    - the single `g_CubeAllRows` read at 0x00566658;
    - `NPCSTORE_FindRec`'s `16i + i` stride and its 0x40 bound;
    - Baal's death: `QUESTS_GetSeed` then `RNG_RandLoHi` at 0x0058E05C, then `0x0052E2A0`, whose `Game+0x6A` test
      admits types 1 and 2 only (single player is 3, items/uniques-sets inputs);
    - the imbue branch's `push 1; push 3` before `GetState` at 0x00579FB1;
    - `ItemRollQualityCreate`'s `cmp ax,1; sbb; and −100; add 100`;
    - `StaffPlaced`'s two `SetState(rec, 10, 0/13)` sites;
    - the `UNIT_SetMode` call before `ItemCopy`'s insert at 0x0055A41C;
    - `InvSpotFindBySize`'s size dispatch.
  - **Rulings.**
    - (1) **`emu` accepted as a second tool for switch claims.** It is a separate evaluator over the independent
      objdump decoding, like S4b's walker. Its results are taken only where a raise names the switch it ran.
      Weakness: a flag-setting instruction it does not model (`test`, `and`, `or`, shifts, `inc`/`dec`) leaves
      the previous compare's flags in place. The review re-ran `static dispatch` with a strict copy that clears the
      flags on those instructions. The traced paths contain none of them, and the output was identical. The tool fix
      is a follow-up (backlog); no row depends on it.
    - (2) **Operand raises accepted under S4b ruling 1** (sock 3 and 41, vend 7 and 8, cube 6 and 13, qd 41). Each
      claim is fully decided by constants in the instruction stream or the image, so there is no data-dependent
      path. Each is read in Ghidra and objdump. Some also have other support: sock 3 and qd 41 cite logs (the reader
      inserts, the 17 imbues), vend 7 has vend 9's logged records, and cube 6 has drlg/0008's trace of the same call.
    - (3) **The cube placement model accepted; `InvPlaceItem` I → C.**
      - The search is tools/player.py's, which run:2026-10-16-player confirmed on partly filled 10 × 4 pages, so the
        model has its own runtime check outside the cube.
      - The cube adds 100 cells, 0 mismatches.
      - Scope: the player branch on an empty grid, which is the only state a cube output meets (G2). The ledger now
        names the four size wrappers and the non-player fallbacks (review note).
      - `NPCSTORE_FindRec` I → C accepted on vend 7 (operands) with vend 9 (the logged records).
    - (4) **Single decisive cases.** A single case is enough when the claim is a branch that the input decides
      deterministically, the code that decides it is read, and the case is reproduced.
      - The S2b **aff 27** remainder is accepted on this basis. The low builder's class test is read, and the Token
        of Absolution is reproduced through the fallback. aff 27 is now raised in full.
      - **qd 37** is accepted the same way: straight-line code, and the logged return addresses are the two constant
        `SetState` sites (qd 14 likewise).
      - **sock 14** is split. The logged case is `[C]`. Its general reason ("the client unit lacks bit 11 until the
        item is identified") has no code reading behind it. That remainder goes to H6b as a piece.
    - (5) **"In part" remainders.** The rows' original routes were S2c's own, so "keeping the route" leaves most
      remainders with nowhere to go. Each remainder is now one of:
      - a harness piece named in § 5 (H6a: cube 49, aff 14; H6b: sock 14, 46; H6c: vend 22, 26; H6e1: qd 38; H2b:
        sock 44);
      - a static leftover in the backlog (qd 8, 10, 19);
      - d-none or d-edit as its ledger says;
      - `[I]` with no further route, listed in § 2.6.
      The rows stay counted as S2c; no class moves.
    - (6) **Totals recomputed once** over the nine reviewed batches (77 moves). The lane's line was taken against the
      S4b totals.
  - **Fixes.**
    - items/0007: sock 14 → raised in part, with its remainder; tally corrected.
    - items/0005: aff 27 accepted (note).
    - items/0008: cube 45 review note; two open questions struck as answered (the spot search draws nothing; the
      placement cell).
    - Inventory § 2.6: S2c heading as reviewed, the remainders' routes, the combined totals. § 2.4 adds an S2c row and
      a new "All, now". § 5 adds the pieces to H2b, H6a, H6b, H6c and H6e1. § 7 marks S2c done.
  - **Final:** 86 statements: **48 raised, 27 raised in part, 1 contradicted, 10 reclassified**. The lane filed 49
    and 26; sock 14 was split. **Totals now:** static 559, harness 544, c-emu awaiting S1f 4, blocked 407 (d-none 278),
    deferred 2, raised 10: 1 526.
  - **Next:** merge `lane/s2c` (owner). The spec-writer entry (six corrections, plus sock 14's split) is for Phase 3;
    the follow-ups are in the backlog.
- **2026-10-16 — Phase 3, first clusters re-tagged (spec-writer, `lane/p38s`, from `main` `7df5039`).** A spec
  qualifies when every batch that carries its statements is accepted (inventory § 5 with the § 2.6 moves; the S1f
  candidates and deferred rows are not batches). With S2a, S4a, H5c, S2b, S3a, S4b, S1b and H4b accepted, four specs
  qualify; monsters/stats, player/creation and data/calc are left to `lane/p37s`.
  - **rng/seeds** (S1b, H5c): {C 62, I 16, L 5} → **{C 76, I 7, L 6}**. Raised rows 1, 2, 3, 4, 5, 7, 10, 15; split
    8, 9, 11, 14, 16 along their ledger remainders; row 6 contradicted: step note 2 now states the command-line parse
    `[C]` (no negative value arrives, ≥ 2³¹ saturates at `0x7FFFFFFF`) and the `D2.ini` route is an *Open questions*
    `[L]`. Rows 13 and 17 (d-none) stay `[I]`.
  - **monsters/README** (S3a): {C 14, I 1, L 0} → **{C 15, I 0, L 0}**.
  - **drlg/README** (S4a, S4b, H5c): {C 60, I 18, L 0} → **{C 75, I 6, L 0}**. Raised rows 1, 5 (×2), 6, 8, 9, 10, 11,
    15, 16, 17; split 2 (`0x0066B030`), 3 (the mask row into checked and unchecked level types), 7 and 14 (one −1, no
    record, theme: no stock case); row 4's tag mention reworded away; rows 12 and 13 stay `[I]`, 12 restated as having
    no stock observable.
  - **drlg/room-tiles** (S4a, S4b, H5c): {C 89, I 46, L 0} → **{C 116, I 26, L 0}**. Raised rows 1, 2, 8, 10, 13, 16,
    17, 18, 19, 21, 23, 24, 25, 31, 33 (×4), 34, 38; split 5, 7, 12, 26, 27, 29, 32. § Release and re-activation is
    rewritten from H5c, with the nested `RoomTilesRelease` call, the logic-record free on every call and the
    `LevelUnloadCheck` `+0x2C` clear. Not raised: the 11 merge-remap statements (rows 4, 14, 15, 28, 30, 37; H5c
    shortfall, S1f candidates) and rows 9 and 20 (S4b shortfall; step note 3 now cites the 1280 replayed `(10, 0, 0)`
    cases as unraised). d-none rows 3 and 35 restated (no key above 28 candidates).
  - **Backlog:** annotated as partly done the S4a corrections entry ((d)), the step-note-2 entry, the H5c review entry
    ((c), rng/seeds half) and the S4b corrections entry ((e), the room-tiles and drlg/README parts); none is complete,
    so none is struck. New entry to the architect with the four specs' old and new counts.
  - **Commits:** one per cluster (rng/seeds, monsters/README, drlg/README, drlg/room-tiles), then backlog and this
    log. Gate green; the wiki's W4 `based_on` warnings for levels and randomness follow from the new `updated:` dates.
  - **Waiting** (missing batches): items/tc H2a, H2b, H2c, H6d; items/quality H2a; items/affixes H2b;
    items/uniques-sets H2b, H6d; items/properties H2b, H2c; items/cube H6a; items/sockets-runewords H6b; items/vendors
    H6c; items/quest-drops H6d, H6e1, H6e2; save/d2s S1a, S1e, H1a, H1b; data/excel and data/strings S1e, H3b;
    data/README H3b; rng S1e; monsters/pool S3b, H4a; monsters/spawn S3b, H4a (and H5d's piece for spawn 42);
    monsters/special S3b, H4a; hirelings S3b, H1a, H1b, H6f; drlg/preset and drlg/maze H5a, H5e; drlg/outdoor H5e;
    drlg/warps H5a; drlg/collision H5b, H5d; objects H5b, H6e2.
  - **Next:** architect review of `lane/p38s` (backlog), spot-checking five raised statements.
- **2026-10-16 — Phase 3, first clusters reviewed (architect, on `lane/p38s`): accept with fixes.** `main`
  (`18ef280`: S2c and the plan 0037 Phase 3 combat spec) merged into the lane first; the backlog and this log kept both
  sides, no duplicate entries. Counts as filed: rng/seeds {C 76, I 7, L 6}, monsters/README {C 15, I 0, L 0},
  drlg/README {C 75, I 6, L 0}, drlg/room-tiles {C 116, I 26, L 0}; the fixes change no tag.
  - **Spot-checks** (each raised statement against its batch section and the accepted review): rng/seeds row 1
    (`g_SeedOverride` `0xFFFFFFFF`: the `.data` dword read with objdump) and row 11's split (rng/0002 § S1b, remainder
    "which of the five ran" kept `[I]`); step note 2's contradiction (rng/0002 § H5c; `cmp al, 0x2d` at `0x00405784`
    read with objdump); monsters/README's game-seed step (monsters/0002 § S3a, 10 782 `SUnitCreate` calls); drlg/README's
    `LevelInit` callers (drlg/0003 § H5c: 23, 28, 1, 16, 123; `0x0066B030` kept `[I]`), the `LvlSubRoll` split (§ S4a,
    1636 calls, the one-−1 half no stock case), the 56-function picture (§ S4b row 17); room-tiles § Release (drlg/0002
    § H5c, drlg/0005 § S4a row 44). All match. Anchors `0x0061A9D7`, `0x0066F1D4` and the symbols cited read as stated.
  - **Splits follow the ledgers' remainders:** rng/seeds 8, 9, 11, 14, 16; drlg/README 2, 3, 7, 14; room-tiles 5 (the
    DS1-load order and `RoomActivateA`, re-activation taken by H5c), 7 (the "0" cell), 12/26 (Def 108), 27 (level 133), 29
    (`0x40000` and the animation `0x8`), 32 (no-entry room). No `[C]` beyond its ledger.
  - **Ruling (merge remap).** The 11 room-tiles merge statements (rows 4, 14, 15, 28, 30, 37) stay `[I]` as H5c
    shortfalls. S1f is a proposal, not an accepted batch, and § 2.6 already classes them "a-run, shortfall; S1f
    candidates". They move only on the H5c review's backlog (b) static answer (then stated as unreachable on stock data)
    or an accepted S1f. The spec's *Open questions* names both routes, correctly.
  - **Ruling (§ Release and re-activation).** Agrees with drlg/0002 § H5c (1516 releases, 626 with `EDX` ≠ 0, 539
    unbuilt, 890 nested pairs, 235 re-activations, 183/52 k) and drlg/0005 § S4a row 44. **Fix:** the text said every
    call "first" frees the logic record; objdump of `0x0066F1B9`–`0x0066F1E1` gives the order active-room free (when
    `EDX` = 0 and `+0x30` is set, where the call nests), `+0x30` ← 0, logic-record free, then the built test. Restated
    in that order, and `+0x64` = 0 scoped to the 374 calls whose logger recorded it, citing drlg/0005 § S4a.
  - **Fix (step 3a).** Raising 3a to `[C]` (row 8, candidate order) covered the "at most 40" cap, which is d-none and
    `[I]` in § Constants: the line now says the cap is inferred only. No tag added.
  - **Ruling (wiki W4, levels and randomness).** ADR-0012 lets a plan's spec phase leave the staleness warning for a
    later sweep, and the stale hedges on both pages understate the specs; they go to the spec-writer's refresh
    (backlog). One paragraph could not wait: randomness's seed range stated the contradicted reading (negative decimals,
    every value but 0 and all-ones) and W4 does not flag it, because rng/seeds' `updated:` did not change. Rewritten at
    the review to the command-line rule and the `D2.ini` open question, with its entry in the not-confirmed list. The
    W4 warnings stay until the refresh.
  - **Research map:** rng/seeds, monsters overview, drlg/README and room-tiles counts updated.
  - **Follow-ups (backlog):** spec-writer, the wiki refresh of levels and randomness; reverser, drlg/0002 § H5c's
    "every call makes first" wording to the release order above.
  - **Next:** merge `lane/p38s` (owner). The next Phase 3 clusters wait for the batches listed above.
- **2026-10-16 — Phase 3 wiki refresh (spec-writer, `lane/wiki1`, from `main` `191e5ad`).** The review's W4 follow-up
  (ADR-0012). [wiki/levels](../wiki/levels.md) and [wiki/randomness](../wiki/randomness.md) restated to the re-tagged
  drlg/README, drlg/room-tiles and rng/seeds: hedges for statements now `[C]` dropped and replaced by the run that
  confirms them, statements still `[I]` kept as "read from the code" (one −1 `SubType`/`SubTheme`, mask values of
  types 22/27/28/30, the 40 cap, the `(10, 0, 0)` fallback, a room with no tiles, three on-demand creators, which
  player-creation paths run, the lookup's (0, 0) return), and the `D2.ini` route listed as not run. `based_on:` bumped
  to drlg/README and drlg/room-tiles 2026-10-16. The wiki index's coverage paragraph, which said combat formulas had
  not started, now links the reviewed combat spec and says no page exists (plan 0037 asked for none). Gate W4 on
  wiki pages: 3 warnings before, 0 after. Review requested (backlog).
- **2026-10-16 — Phase 3 wiki refresh review (architect, `lane/wiki1`).** Verdict: **accept with fixes**, applied on
  the lane. Every changed statement of [wiki/levels](../wiki/levels.md) and [wiki/randomness](../wiki/randomness.md) was
  checked against the re-tagged drlg/README (step notes 2 and 8, § Inputs), drlg/room-tiles (step notes 3 and 12,
  § Constants, § Release and re-activation, *Open questions*) and rng/seeds (step notes 3d, 4, 6, 7a, 7b, *Open
  questions*): the counts (188/59, 145 rooms of levels 111/112/117, 1 852 097 and 781 380, 1516/235/183/52, 50 586,
  42 act creations, 346/29/5 callers, 2066 and 5, 558, 252 and 24 565) and the `[C]`/`[I]` splits match, and no
  sentence adds a claim. **Fixes:** (1) the `(10, 0, 0)` fallback tile was "never seen in the game" in both mentions;
  room-tiles step note 3 and drlg/0002 § S4a say only run:2026-10-11-drlg-roomk lacked it, while replays of the logged
  games took it 1280 times with k matching (not a raised claim). Restated as read from the code with that replay
  noted, not counted as confirmation. (2) randomness: the `InitOne` sentence had become a continuation of the new
  "Not run at all" bullet; moved back into the read-from-code bullet. (3) levels: "which callers set it" → "ask for
  it" (the callers pass `EDX`; the release sets the bit), and the room-tiles bullet now names both unread points.
  (4) Spec, found by the review: [drlg/README *Open questions*](../specs/drlg/README.md#open-questions) still listed
  the `LvlSubRoll` −1 branch and the outdoor cell position as code-read only, against step note 8 (`[C]` since this
  phase); struck as settled, the one-−1 case left `[I]` in the step note. No tag changes, counts as filed. Also
  reflowed levels L67. Gate W4 on the wiki: 0. **Ruling, combat page:** the combat spec gets a wiki page. ADR-0012
  covers every reviewed row, and the 0037 P3 review's "wiki: not part of this plan" left it with no owner. It goes
  under plan 0037 as **Phase 4** (added, spec-writer), after the 0037 re-tag that follows the resume lane, so it is
  written once on the final tags and plan 0037 does not close without it; plan 0041 P3 then keeps it in step. The
  wiki index paragraph now says the plan writes one. Backlog entry to the spec-writer filed.
  - **Next:** merge `lane/wiki1` (owner).

- **2026-10-16 — Batch S3b done (reverser, `lane/s3b`, static; no slot, no game).** 17 statements (hirelings 2, player/creation
  3, monsters/pool 2, spawn 6, special 1, stats 3): **12 raised, 3 raised in part, 0 shortfall, 2 reclassified** (a-run 2:
  player/creation 16 → H6g, spawn 41 → H5d; proposed in [inventory § 2.6](0038-inventory/README.md#26-moves-made-by-the-batch-reviews),
  § 5 and § 7 updated, pending review). By spec: hirelings 1/1/0/0, player/creation 2/0/0/1, pool 1/1/0/0, spawn 5/0/0/1,
  special 1/0/0/0, stats 2/1/0/0.
  - **Tools:** `tools/sweep_s3b.py` (`logs`, `hire`, `player`, `pool`, `spawn`, `special`, `stats`, `all`; exits 0) and
    `tools/test_sweep_s3b.py` (6 tests). The second tool is GNU objdump through S4b's decoder, with a call-path enumerator
    for the room-update bodies. The ledgers cite each check's `S3B` line.
  - **Logs** (sha256 checked; manifest `workspace/logs/sweep-s3b-manifest.txt`, `ea8e196b…1298`): run:2026-10-13-mon-spawn,
    -10-14-mon-special, -10-15-mon-stats (through `mon_sweep.py`'s records) and run:2026-10-15-objects (S4b manifest), 55
    logs. `tools/hirelings.py check` re-run on run:2026-10-16-hirelings: 0 mismatches. Also used: the pinned game's `-txt`
    compile of run:2026-10-15-cube-saves (`monstats2.bin` byte-identical).
  - **Correction for Phase 3:** monsters/stats F3, the `druidhawk` Normal MonProp row is reachable by a Druid's Raven
    (stats 30's remainder, an H4a piece). New `[I]` readings: `RegionActClass`'s ranges and cache, the three
    `RoomUpdateOne` callers, `SKILLS_AddSkill`'s monster exception. All are in the spec-writer entry.
  - **Ledgers:** the "Plan 0038 batch S3b" sections of hirelings/0001, player/0001 and monsters/0001–0004; addenda under five
    runs. **Symbols:** 5 I → C. Gate green. Review requested (backlog), and archivist and spec-writer entries filed.

- **2026-10-16 — Batch S3b reviewed (architect, on `lane/s3b`): accept with fixes.** `main` (`191e5ad`: S2c, H4b, 0037
  Phase 3, 0039 Phase 0, the 0038 Phase 3 re-tag) merged into the lane first. Conflicts were in the backlog, this log and
  inventory § 5 (H4a) and § 7 (S2c and S3b ranks; H2b and H5d). Both sides were kept. H4a now holds S2c's quest-drops 48,
  H4b's pieces and S3b's pieces (32 statements, 0/14/18). No backlog entry appeared twice.
  - **Re-run.** `systemd-run --user --scope -p MemoryMax=4G python3 -I tools/sweep_s3b.py all` exits 0 in 8 s with the
    counts the ledgers cite: 55 logs, sha256 equal; 120 hireling rows, 7 326 walks, `hirelings.py check` 0 mismatches;
    12 `AddSkill` sites, `ExpRatio` shift {11: 70, 10: 30}; `+0x025` 609/609, counterfactual 13; 2 barrel spawns;
    4 154 passes on one game pointer per log; 1 844 handler calls, 0 on a live minion; 2 reversed HP rows.
    `python3 -I tools/test_sweep_s3b.py`: 6 tests OK. `sweep_s3b.py` sha256 is `950ecbc2…`.
  - **Read with objdump at the review.** The pinned image's sha256 matches the inventory. Checked:
    - `HIRELING_LoadTable`'s `cmp word [rec], 0x64; sbb; add 1; shl 8` at 0x0065623E;
    - `MonStats2CompList`'s `cmp eax, 0xF` (0x0065712C) and the 254 cap and byte store at `+0x25` (0x00657183–0x00657190);
    - `XP_ApplyExpRatio`'s `sar edx, cl; add edx, eax; sar ebx, cl` on `0x7FFFFFFF` (0x0057E3B9–0x0057E3C5);
    - `ExpMaxLevel`'s read of `[g_pExperience + 4c]` (0x00611854);
    - `SKILLS_AddSkill`'s monster test `cmp [unit], 1` (0x00647256) before the `+0x28` store;
    - the `+0x2E` read and `+0x2BE` write of the region build (0x00547A99, 0x00547A9D) and the tick's `+0x2E` compare;
    - `MonPropRec`'s single `DataTables + 0xC30` operand (0x005734AC);
    - the HP draw 0x00573F83–0x00573F99 and `RNG_RangeB`'s `test esi, esi; jg` (0x0045C3E3);
    - `MonLvlStats` (0x006538A0): four compares, none between the two HP fields;
    - the callers of 0x005A0120 and 0x005A0380 (six sites).
  - **Rulings.**
    - (1) **stats 19 and 45: the composition is accepted.** Both pieces are `[C]` (the draw for every logged draw, the
      `n ≤ 0` branch by run:2026-10-11-rng-emu), and the review read what joins them. The draw is straight-line code,
      and `MonLvlStats` writes `minHp` and `maxHp` each on its own, never comparing them. So a reversed range reaches
      `RNG_RangeB` by the same instructions as a logged draw, and only `n` differs (S4b's invariance ruling). The
      `mephistospirit` visit stays in H4a as an optional corroboration; no row depends on it. The ledger records the
      joining code (review note).
    - (2) **pool 9 on the game's own compile is accepted.** This is the S1b ruling for the compile path:
      run:2026-10-15-cube-saves ran the pinned compiler, and its `monstats2.bin` is byte-identical, so every `+0x025`
      byte is that compiler's output. The rule then holds 609/609 against a counterfactual at 13. The cap is d-none.
    - (3) **pool 23 on one uncached evaluation is accepted** under the S2c review's ruling 4. The input decides the
      branch, the code is read in two tools, and the case is reproduced. The review added a second counterfactual: the
      same walk over level 29's whole `mon` list gives class 172, not the logged 384, so the spawn reads the region's
      pool and not the level's list. The raise covers the pool read only; the range bases and the cache stay `[I]`.
    - (4) **objdump is accepted as the second tool** for claims decided by the instruction stream: reference counts,
      operand searches and call-path enumeration (spawn 1, 2, 7, 50, 52; stats 30's single reader; hirelings 8's
      writer/reader pair). This extends S4b ruling 1. Limit: a displacement or reference search cannot see a field
      reached through a different base (spawn 50/52's `+0x2BE`) or through a computed call. Each raise that rests on
      such a search also has runtime support: spawn 2 has the game pointer in 55 logs, spawn 50/52 the run's
      watchpoints, hirelings 8 the 72 + 723 reproduced calls.
    - (5) **special 43 is split: raised in part.** The statement also says the copied list is "what other code reads".
      Naming the five call sites of 0x005A0120 does not show what the four that are not the packet builder do. The
      list can also change after the copy (mod 22). The remainder stays `[I]`, with a static leftover (backlog). The
      packet half (writer, reader, client reader `[C]`, 0 handler calls on 538 live minions) stands.
    - (6) **player/creation 16 → a-run H6g is accepted.** A static route cannot show a branch that no stock creation
      reaches. Stock play reaches it by the skill-point path, which is an observable with a cheap recipe in H6g's own
      family (`player.gdb`). Spawn 41 → H5d is accepted the same way (sizes 0 and 1 reachable; other sizes d-none).
  - **Fixes.**
    - monsters/0003: special 43 → raised in part, with its remainder.
    - monsters/0004: stats 19/45 review note (the joining code); stats 30's remainder worded as an H4a piece (the row
      stays S3b), not "reclassified".
    - monsters/0001: pool 23 review note (the second counterfactual, the raise's scope).
    - Inventory § 2.6: S3b heading as reviewed, special 43's remainder, the combined totals. § 2.4 adds an S3b row and
      a new "All, now". § 5 makes the `mephistospirit` piece optional in H4a. § 7 marks S3b done.
    - Backlog: the spec-writer entry gains (f) for special 43's split.
  - **Final:** 17 statements: **11 raised, 4 raised in part, 0 shortfall, 2 reclassified** (by spec: hirelings 1/1/0/0,
    player/creation 2/0/0/1, pool 1/1/0/0, spawn 5/0/0/1, special 0/1/0/0, stats 2/1/0/0). The lane filed 12 and 3;
    special 43 was split. Symbols: the 5 I → C stand (`RoomUpdateOne` on spawn 1/7, `RegionActClass` on pool 23's pool
    read, `ExpMaxLevel` on player/creation 21, `MonStats2CompList` on pool 9, `g_HirelingFirstById` on hirelings 8).
    **Totals now** (recomputed once over ten reviews, 79 moves; the lane counted against the H4b totals): static 557,
    harness 546, c-emu awaiting S1f 4, blocked 407 (d-none 278), deferred 2, raised 10: 1 526.
  - **Follow-ups (backlog):** reverser, special 43's static leftover (the four callers of 0x005A0120); reverser, three
    `sweep_s3b.py` tool items (no row depends on them).
  - **Next:** merge `lane/s3b` (owner). The spec-writer entry (five corrections and additions, plus (f)) is for Phase 3.

- **2026-10-16 — Batch S1a done (reverser, `lane/s1a`, static; no slot, no game, no Ghidra).** 56 statements, all
  save/d2s: **39 raised, 15 raised in part, 0 shortfall, 2 reclassified** (117 and 124, c → b, H1b; proposed in
  [inventory § 2.6](0038-inventory/README.md#26-moves-made-by-the-batch-reviews), § 5 and § 7 updated, pending review).
  - **Tool:** `tools/sweep_s1a.py` (`logs`, `corpus`, `survey`, `writes`, `reads`, `pairs`, `calc`, `props`, `static`,
    `all`; exits 0 in 9 s; sha256 `c07086a3…`) and `tools/test_sweep_s1a.py` (5 tests). Report
    `workspace/logs/sweep-s1a-all.txt`, log manifest `workspace/logs/sweep-s1a-manifest.txt` (91 logs, `18318973…1676`).
    The second tool is GNU objdump through `tools/sweep_s4b.py` (38 pinned instructions).
  - **Corpus:** 146 game-written saves (144 full, 2 stubs), each admitted by a logged `WDONE` buffer (100) or a hash in
    its run record (46); 1 853 items, 652 property lists, 77 ids; `tools/d2s.py roundtrip` byte-exact on all.
  - **Second sources:** the round trip (bit-exact writer), 200 logged writes and 104 logged loads (run:2026-10-12-d2s-io and
    run:2026-10-16-player), 64 built/written pairs, the calc run's skill levels and hotkey casts, props-forced and the
    player model's 269 saved starting items, a data check of 127 affix ids against the affix tables with three failing
    counterfactuals, the game's own `itemstatcost.bin` compile, and objdump pins of the writer/reader pairs.
  - **For Phase 3 and other lanes:** the reader's class-affix version rule (≤ 88 → 0, 89 → +1); the prefix test is "above
    the base" (base 747, the `MagicSuffix` record count, where d2s.md says 748); the serialiser's non-save arguments
    (bit 25 set, bit 22 cleared); the `gf` clamp observed at its top bound (stat 8, Hell level-up saves; the player
    record's "stat 6" corrected by an addendum).
  - **Ledger:** "Plan 0038 batch S1a" in [save/0001](../findings/save/0001-d2s-io.md#plan-0038-batch-s1a-2026-10-16);
    addenda under run:2026-10-12-d2s-io, -10-14-props-forced, -10-16-calc and -10-16-player. **Symbols:** 11 I → C.
    Gate green. Review requested (backlog). Nothing merged.

- **2026-10-16 — Batch S1a reviewed (architect, on `lane/s1a`): accept with fixes.** `main` merged twice into the lane
  (S3b and plan 0041 Phase 0 at `c1d705c`, then plan 0039 P1a at `cf9c3ab`); the inventory, plan-log and backlog
  conflicts kept both sides, and the totals are recomputed once below.
  - **Re-runs:** `sweep_s1a.py all` under `systemd-run --user --scope -p MemoryMax=4G`, exit 0 in about 5 s, every count
    the ledger cites reproduced (corpus 146 = 100 `WDONE` + 46 recorded, 2 left out; survey 1 853 items, 652 lists, 77
    ids, 127/127 affix ids with counterfactuals 9/46/124 unmatched; round trip 0 diffs over 144 saves; writes 200, loads
    104, pairs 64, calc 5 073 cast-path evaluations, props 3 reproduced; 38 objdump pins). `test_sweep_s1a.py` 5 tests OK.
  - **Anchors read with objdump:** rows 8 (`push 0x14f`, 0x00568FCE), 11 (`push 0x1ff`, 0x005696BA, 0x00631245), 12, 15
    (the sign extension 0x00411041–0x00411062), 16 (0x0041109A), 76 (0x00631312–0x0063131B), 85 (`imul 0xe4`, `[eax+0x23]`),
    87 (writer 0x006303D5–0x00630417, reader 0x0062CE2A–0x0062CE57), 101 (0x00630688–0x0063068F, 0x0063055B–0x0063055F,
    0x006305A7), the serialiser's arguments (0x00631321–0x0063134D), the set-list loop (0x0062D8BB–0x0062D8F0). All
    match, with one wording fix: row 12's operands are `push 0x10; push 0x4d4a`, in that order.
  - **Rulings on the lane's points:** (1) **corpus rule accepted.** A save counts when its sha256 equals a logged write
    buffer or a hash its run record gives as game-written; both are reviewed records. The props-forced save is admitted
    under ADR-0013, and so are the `qit*` item samples of run:2026-10-11-d2s-samples, which the lane did not flag: they
    were written under an edited `charstats.txt` and `cubemain.txt` (`-direct -txt`). The edited cells decide which items
    exist, not how they are written; no row rests on either set alone (rows 92–96 also have the 269 player-model items).
    Ledger note added. (2) **Rows 15 and 87 accepted on rule 1.** A writer/reader pair is evidence rule 1 and needs no
    stock observable; both were read in objdump at the review. The ledger already says no stock save reaches them; Phase 3
    keeps that sentence next to the `[C]`. (3) **Row 32 accepted.** The caller filter only decides which evaluations must
    be hotkeyed skills, so a wrong classification can only add failures. The mapping rests on the field recipe pressing
    F1–F8 in order and the casts following slot order (Sorceress and Druid 8 of 8). Ledger note added. (4) **Rows 98 and
    99 accepted.** One loop reads every set list with the same body (`1 << i`, state `[0x006E90B8 + 4i]`), and the
    runeword list is that loop's extra pass with state 171. Bits 2–4 differ from the observed bits only in the index (S4b
    invariance ruling). Ledger note added. (5) **Row 71's order accepted.** The non-final serialiser passes of the same
    200 writes walk the list with the hand items first while the file has them last. That counterfactual shows the
    writer reorders. The cursor item and refusal stay `[I]` as filed. (6) **The 53 empty lists need an entry.** The
    lane's characterisation was wrong: 48 are magic items at ilvl 1 with non-zero affix ids, the ring, amulet, jewel and
    charm the edited CharStats gives at creation (40 in the samples, 8 in d2s-io's written saves). The other 5 are rare
    cube outputs at ilvl 99 (run:2026-10-15-cube-saves). Affix ids with no stats in a game-written save is a creation
    behaviour a reimplementer must reproduce, so it goes to the reverser (backlog). No S1a row depends on it: rows 101
    and 137 check only the 85 items with a list.
  - **Fixes on the lane:** the ledger's corpus note, row 12 operands, rows 32, 98, 99 and 87 review notes (87: the
    reader's per-version base adjustment for item versions 72–88, 0x0062CDC4–0x0062CE10, `[I]`, d-edit with row 130),
    the corrected 53-item note. Symbols: `BITBUF_ReadSigned` (row 15) and `BITBUF_ReadUnsigned` (a frame and a `jmp` to
    `BITBUF_Read`) also I → C, 13 in all. Inventory § 2.6 entry marked reviewed and moved after P1a; § 2.4 gains the P1a
    and S1a rows.
  - **Final:** 39 raised, 15 raised in part, 0 shortfall, 2 reclassified (117 and 124, c → b, H1b), as filed.
  - **Totals now** (recomputed once over the eleven batch reviews and plan 0039 P1a, 92 moves; the lane counted against
    the S2c totals): static 555, harness 537, c-emu awaiting S1f 4, blocked 418 (d-none 278, d-edit 80), deferred 2,
    raised 10: 1 526.
  - **Follow-ups (backlog):** reverser, the 53 items with affix ids and no stats; reverser, `sweep_s1a.py` items (the
    empty-list breakdown and a pin for the set-list loop). The spec-writer entry gains (f) and (g) below it.
  - **Next:** merge `lane/s1a` (owner). The save/d2s Phase 3 re-tag waits for its other batches (H1a, H1b, S1e).

- **2026-10-16 — Batch H5e done (reverser, `lane/h5e`, slot 1).** run:2026-10-16-sweep-mazes, 6 sessions (s1–s6,
  Normal, expansion, map seeds 45, 9, 1557, 312, 5005, 6006; seeds 45, 9 and 312 chosen offline with the outdoor
  model), recorded in [drlg/experiments.md](../findings/drlg/experiments.md#run2026-10-16-sweep-mazes). Logger
  `tools/gdb/sweep-mazes.gdb` (no new breakpoint); checker `tools/sweep_h5e.py logs`: gen 153 567 checks, 0 mismatches;
  `sweep_h5e.py scan` for the seeds. Two bookkeeping fixes in `tools/drlg.py gen` (reused room address; rebuilt level
  object's rect); regression on the kept maze (206 937), acts-3-5 (155 215) and outdoor (572 211) logs, 0 mismatches.
  Sections "Plan 0038 batch H5e" in drlg/0004, 0006 and 0008; `re/symbols.csv`: `sub_006664A0_PresetCentreMonster` I → C.
  - **22 statements: 18 raised, 2 raised in part, 2 shortfall.**
    - Raised: maze 6 (×2: tomb 70 at 18 rooms, Kaa 71 at 12), 10 (×8: caves 11, 12 and 10 from kept logs; crypts
      21–24; Jail 31; tombs 55, 56, 59, 60, 66–68, 70, 71; Lair 63, 64; Dungeon 87, 89; Baal 128, 130; lava 126, 127),
      11 (×2), 12; outdoor 20 (prisons' scan); preset 2, 12, 13 (centre monster, 4 lists), 14 (`Def` 3, 28, 300).
    - In part: outdoor 13 (BridgeFind on the 12×7 Blood Moor and the columns-outer scan raised; the non-square half
      proposed d-none), 14 (failed search raised; 5/6 endpoints and an exhausted pool not reached).
    - Shortfall: outdoor 7 (vertex merge), 11 (waypoint with no free cell): none in the logs or the offline scan.
  - **New reading:** a `LevelInit` rebuild of the same level object enters the maze window with the rect its previous
    placement wrote (level 28's Barracks rect); the window is unchanged (drlg/0006).
  - Review requested (backlog). Slot 1 stopped, saves restored, no session left running.
- **2026-10-16 — Batch H5e reviewed (architect, on `lane/h5e`): accept with fixes.** `main` (`1423daa`: S3b, S1a, plan
  0039 P1a, 0041 and 0042 Phase 0, the wiki) merged into the lane first. Conflicts were in the backlog, this log,
  inventory § 2.6, and drlg/0004 and 0008 (new sections on both sides). Both sides were kept, with `main`'s first. The
  backlog has no duplicate entries.
  - **Re-run.** The six log hashes match the manifest, and the eight tool hashes of the record match the files.
    `test_sweep_h5e.py` passes (4 tests). `sweep_h5e.py logs` gives 153 567 checks and 0 mismatches, with the recorded
    counters. `sweep_h5e.py scan 1 601 0,1,2` matches the record line for line (52 200 windows, 0 errors). The changed
    `drlg.py gen` on the kept run:2026-10-12-drlg-gen + run:2026-10-15-drlg-maze list gives 206 937 checks and 0
    mismatches, with 8 rebuilds. The pre-fix `drlg.py` (`f59929e`) gives 1 mismatch on s1 and 6 on s2. Read with r2:
    `MazeSpecialsTomb`'s level tests.
  - **Rulings.** (1) **The two `drlg.py gen` fixes** are accepted. Both are model bookkeeping, not behaviour, and the
    regression holds. The reused-address fix drops a list only when a new room is linked at that address. The review
    found it also clears three false `RoomPresetUnits` mismatches in s2: rooms that levels 103 and 2 had before. The
    record said "one, in s1", and now gives four. (2) **The rebuilt-level reading** stays `[C]`, with a code anchor at
    `LevelInit`, the logged MZA rect and the windows reproduced. Only level 28's three s2 rebuilds tell the readings
    apart: in the other rebuilds the placed rect equals the act's. The finding is reworded to say so. "8 + 11" is a
    count, not 19 pieces of evidence. (3) **Level 10 on kept logs** is accepted, as kept logs were at S3a and H4b. The
    review re-ran it: `od-s2` and `a35-s1` give 4 windows (Normal and Nightmare), all matched. **Tombs 69 and 72**: the
    lane's untagged sentence is now an `[I]` static line in drlg/0006. The finisher tests the tomb levels only as the
    range 66–72 and against the act's true-tomb and Kaa fields, and all three roles were built. Maze row 10 stays raised.
    (4) **Outdoor 7, 11 and 14's remainder** stay a shortfall (a-run). No more seeds: a static reachability question
    goes to the reverser (backlog). If it shows a branch unreachable, that remainder goes d-none at its review.
    Otherwise it names the seed condition for `sweep_h5e.py scan`. (5) **Levels 31, 126 and 127 on the server copy only**
    are accepted. A maze window carries every level-seed draw and the seed after it, so the client copy would repeat the
    same build. **Outdoor 13's non-square half → d-none** is accepted on the evidence, which the lane stated too broadly.
    "Levels `SizeX/Y` 80" is no argument, since the Blood Moor is also 80 in Levels and 12×7 in cells. What holds: only
    the Blood Moor is non-square among levels 2–7, and flag `0x20` was never set on it (1 800 scan windows, the lane's
    seeds 1–2 999, and the review's seeds 1–100 by level). Whether its outline can set `0x20` joins the static
    question.
  - **Fixes (on `lane/h5e`).** drlg/0006: the level-10 re-run cited; the tombs 69/72 static line (`[I]`); the rebuilt-level
    `[C]` worded to level 28's three windows. drlg/0004: the four false mismatches. drlg/0008: the d-none reason.
    experiments.md: the mismatch count corrected, and a review note. Inventory § 2.4 (H5e row, no moves), § 2.6 (H5e as
    reviewed, combined totals), § 5 and § 7 (H5e done).
  - **Ledgers checked against the rules.** Each raise names its windows and logs, next to a code anchor. Each part raise
    names its remainder. The 1 symbol I → C (`PresetCentreMonster`) rests on preset 12 and 13, which are raised; the
    gating `Def` 4–7 is read in the caller (drlg/0004 step 4a), and `Def` 5 and 7 were met. Spot-checked anchors
    (`0x0067FC20`, `0x00680200`, `0x006817D0`, `0x0067E240`, `0x00672BE0`, `0x00672DC0`, `0x006424A0`, `0x006663C0`)
    resolve in `re/symbols.csv` as `C`. No `[L]` added. The gate is green.
  - **Final:** 22 statements: **18 raised, 2 raised in part, 2 shortfall, 0 reclassified**, as filed. **Totals now**
    (recomputed once over the twelve batch reviews and P1a; H5e moves nothing): static 555, harness 537, c-emu awaiting
    S1f 4, blocked 418 (d-none 278, d-edit 80, d-sim 28, d-2c 14, d-owner 10, d-0032 8), deferred 2, raised 10: 1 526.
  - **Follow-ups (backlog).** To the reverser: the static reachability question (outdoor 7, 11, 14, and 13's Blood Moor
    `0x20`), and two `sweep_h5e.py` counters (the rebuilds that tell the readings apart; scan counters by level). To the
    spec-writer: three additions to the lane's Phase 3 entry.
  - **Next:** the owner merges `lane/h5e`. H5a takes the next slot in the family (§ 7).

- **2026-10-17 — Phase 3, second round (spec-writer, `lane/p38s2`, from `main` `8f8c0bc`).** Accepted since the first
  round: S2c, S3b, S1a, H4b, H5e. Of the specs not yet re-tagged (combat excluded, plan 0037 open), only drlg/outdoor
  has every batch carrying its statements accepted (S4a, S4b, H5e; inventory § 5 with the § 2.6 moves).
  - **drlg/outdoor** (S4a, S4b, H5e): {C 170, I 22, L 3} → **{C 180, I 19, L 3}**. Raised rows 1 (no draw; the 0x268
    size stays `[I]`), 3, 5, 6, 19, 20; split 13 (BridgeFind on the Blood Moor and the columns-outer scan `[C]`; the
    non-square half `[I]`, carried in *Open questions* as pending the static reachability question), 14 (the failed
    search `[C]`; 5/6 endpoints and the exhausted pool `[I]`), 16 (41, 45, 46 `[C]`; 134 and the fatal `SpecialArea`
    `[I]`). Not raised: 7 and 11 (H5e shortfalls; they cite the 52 200-window scan), 8 (S4a shortfall, its reason
    stated). d-none 10 reworded (the double visit cannot change the result); the other d-none rows (2, 4, 9, 12, 15,
    17, 18, 21) unchanged. *Open questions*: the unreached-branches entry narrowed to the static question; the `+0xC`
    and dead-function entry closed from plan 0039 P1a (both `[I]` in the body).
  - **Folded on their own** (plan 0039 Phase 2 items, no 0038 re-tag; this plan's change is first, as 0039's rule asks):
    drlg/room-tiles {C 116, I 26, L 0} → **{C 118, I 31, L 0}** (step 9c and note 9: the merge-remap branches are
    unreachable on stock data, and the 11 d-edit rows stay `[I]`; notes 2, 6 and 9: the `"0"` load, no DS1 cut two ways,
    `0x40000`); drlg/warps {C 91, I 30, L 5} → **{C 91, I 34, L 2}** (F1 and the 133 → 17 note, § G units, E1's > 9
    question). No warps row is raised; its cluster waits for H5a.
  - **Backlog:** struck the H5c review entry ((c), warps half, the last open part). Annotated as partly done: the S4a
    corrections entry ((c)), the P1a Phase 2 entry ((a), (d), (f)), the reverser's H5e entry (outdoor part) and the H5e
    review additions ((c)). New entry to the architect with the three specs' old and new counts.
  - **Commits:** drlg/outdoor, drlg/room-tiles, drlg/warps, then backlog and this log. Gate green; W4 warns for the
    levels and randomness wiki pages.
  - **Waiting** (missing batches): items/tc H2a, H2b, H2c, H6d; items/quality H2a; items/affixes H2b;
    items/uniques-sets H2b, H6d; items/properties H2b, H2c; items/cube H6a; items/sockets-runewords H2b, H6b;
    items/vendors H6c; items/quest-drops H4a, H6d, H6e1, H6e2; save/d2s S1e, H1a, H1b; data/excel and data/strings
    S1e, H3b; data/calc S1e; data/README H3b; rng S1e; monsters/pool H4a; monsters/spawn H4a, H5d; monsters/special
    H4a; monsters/stats H4a; hirelings H1a, H1b, H6f; player/creation H1a, H6g; drlg/preset, drlg/maze and drlg/warps
    H5a; drlg/collision H5b, H5d; objects H5b, H6e2.
  - **Next:** architect review of `lane/p38s2` (backlog).

- **2026-10-17 — Phase 3 second round review (architect, `lane/p38s2`): accept with fixes.** `main` had not moved
  (`8f8c0bc`), so there was no merge.
  - **drlg/outdoor raises and splits against the ledgers.** Every raise matches an accepted ledger line: row 1 and 6
    (drlg/0008 § S4a; the 0x268 size stays `[I]` as S4a says), 3, 5 and 19 (§ S4b) and 20 (§ H5e). The splits follow the
    remainders of § 2.6: 13 (BridgeFind and the columns-outer scan `[C]`, the non-square half `[I]` in the body with the
    open question as 678 (c) asked), 14 (the failed search `[C]`; 5/6 endpoints and the exhausted pool `[I]`) and 16
    (41/45/46 waypoint `[C]` per S4a; 134, the fatal `SpecialArea` and the 45 shrine pass `[I]`, which S4a's line does
    not cover). The 7, 8 and 11 shortfalls stay `[I]`, and row 10's wording matches S4a's reclassification. The P1a `+0xC`
    and dead-code lines are `[I]` as drlg/0008 § P1a has them.
  - **Counts recounted** in the file: outdoor {C 180, I 19, L 3}, room-tiles {C 118, I 31, L 0}, warps {C 91, I 35, L 2}
    after the fix below. There is no `[L]` above *Open questions* in any of the three. Gate green.
  - **Anchors (objdump, pinned `Game.exe`).** `0x0066C39B` `cmp [eax+0x1D0], 0x85`; `0x0066B7D5` `mov [eax+0xC], 0`;
    `0x0066E754` `test al, 1` → `0x0066E781` `test [ebp+0x14], 0x80` (flag before bit 7); `0x0056D181` `[ebp+0x14]`
    (the 4th stack argument); `0x006753E1` `lea edx, [edi+0x40]` (grid3 allocation); `0x0066FC2A` → `GridCellOp`. All
    resolve as cited.
  - **Ruling: folding plan 0039 P1a outside a full re-tag is acceptable.** Plan 0039 Phase 2 anticipated it, and its
    merge-order rule was kept. No room-tiles or warps inventory row changes class or tag: the 11 merge rows stay `[I]` as
    d-edit, and warps rows 15 and 17 stay `[I]`. The new statements are `[I]` code readings with finding anchors, or
    `[C]` only where P1a gives the second source (the 2077-DS1 survey, and the H5c logs merge by merge). The warps and
    room-tiles re-tags count their rows from the inventory and do not count the front-matter delta, so the P1a `[I]`s
    added here are not inventory rows.
  - **Fix applied:** warps F1 pseudocode. FindRoom's line said "srcRoom gets a warp node" for every case, while the
    caller bullet and drlg/0007 § P1a have no node and every room within 6 tiles appended when `Warp` = −1. The case is
    added as an `[I]` comment line (fn:sub_0066BE80_WarpPairRoomFind, fn:sub_0066BDA0_RoomNearListAppend), and the
    front matter is now `I` 35.
  - **Research map:** the drlg/overview (room-tiles), drlg/outdoor and drlg/warps rows now carry the new counts and
    states. This also clears the stale warps row noted in inventory item 9.
  - **Follow-ups:** spec-writer, the wiki refresh (W4 on levels and randomness, and three stale *open questions*
    bullets in levels), in the backlog. The outdoor shortfalls are already with the reverser in the H5e static
    reachability entry. The warps re-tag waits for H5a.
  - **Next:** the owner merges `lane/p38s2`.
- **2026-10-17 — Phase 3 second round wiki follow-up (spec-writer, `lane/wiki3`, from `main` `fc84933`).** The
  round-2 review's W4 follow-up. [levels](../wiki/levels.md): `based_on:` bumped for drlg/outdoor, drlg/room-tiles and
  drlg/warps (2026-10-17); § Pairing gains a paragraph on the near-list append (code-read: the stairs room's near list
  rebuilt within 6 tiles, the paired room appended and the list re-sorted; a seam slot appends every destination room
  within 6 tiles and makes no link; nothing marked on the destination; no pairing call for a room of level 133).
  *What is not known yet*: *Outdoor* now says the prisons' fallback scan, a failed road search and `BridgeFind` on
  the non-square Blood Moor are reached, the back-up is unreached, and the other four branches were not met in the
  52 200-window scan with stock reachability open, plus the swapped cliff-cave scan; no other code opens a portal to
  133–136. *Room tiles*: the merge branches are unreachable on stock data (2077 DS1s, logs merge by merge) and kept as
  the edited-data reading; the `"0"` DT1 name outcome is not determinable statically. *Warps*: `Offset`/`ExitWalk`
  subtiles and `Select` screen pixels (code-read); more than nine points not seen in 1452 builds (max 8, level 46)
  and not given by slot counts, one slot's cells in two rooms not excluded. [randomness](../wiki/randomness.md):
  re-read against drlg/room-tiles; the round's changes (merge branches, `0x40000`, `"0"` names, DS1 views) touch
  nothing it says, so only `based_on:` is bumped. Gate W4: 4 warnings before (levels 3, randomness 1), 0 after.
  - **Next:** architect review (backlog).

- **2026-10-17 — Review: Phase 3 second round wiki follow-up (architect, `lane/wiki3` at `3a27713`, `main` `4d31287`
  merged in first).** **Accept with fixes**, applied on the lane. Every changed statement was traced to the
  2026-10-17 specs at the same strength. *Outdoor*: the three reached branches are `[C]` (outdoor L6 prisons map seed
  312, H6 failed search map seed 45, H2 `BridgeFind` 564 of 1 800 Blood Moor windows) and are stated as observed; the
  back-up stands apart from the 52 200-window sentence, as in the spec (the scan covers the vertex merge, the waypoint
  pass and the road branches only); the portal sentence matches the `[C]` on all 12 `PortalObjectCreate` call sites; the
  cliff-cave case keeps "of levels 2–7" and the 1 800 Blood Moor windows. *Room tiles*: "unreachable on the shipped
  data" rests on step note 9's `[C]` (2077 DS1s, 2043 `LvlPrest` + 34 `LvlSub`) and the per-merge log `[C]` (1797
  wall, 406 shadow, 43 floor); the branches themselves stay a code reading, as the wiki says; the `"0"` outcome matches
  "not determinable statically". *Warps*: units said as code-read (§ G `[I]`); the nine-point sentence matches E1
  (1452 builds of 93 levels, max 8 at level 46, 7 slots at most in the data, one slot's cells in two rooms not
  excluded) without promoting E1's `[I]`. § Pairing: every clause is F1 `[I]` and is said "by the code".
  randomness: the room-tiles round touches neither its k ranges nor the 2066/5 activation counts; date bump only is
  right. Links and anchors resolve (E8), `based_on:` dates equal the specs' `updated:` (W4 0), gate fast tier green.
  **Fixes:** (1) § Pairing "within 6 tiles" (twice) → "less than 6 tiles away" (F1: a gap below 6 tiles on both axes,
  the room itself included). (2) § Pairing: the linked glossary *near list* is the active room's; the paragraph is about
  the DRLG room's `+0x08` list, so a parenthesis now says the active room's list is filtered from it. (3) *Room tiles*:
  "no checked shipped room has one" now names what the check leaves out (outdoor anchors, maze specials outside the
  rotation ranges), as room-tiles *Open questions* does. No follow-ups.
  - **Next:** merge `lane/wiki3` (owner).

- **2026-10-17 — Batch H5a done (reverser, `lane/h5a`, slot 1).** run:2026-10-17-sweep-links, 9 sessions (s1–s9,
  Normal, expansion, map seeds 82, 52, 58, 90, 4, 17, 5, 68, 2, chosen offline with `tools/sweep_h5a.py scan`),
  recorded in [drlg/experiments.md](../findings/drlg/experiments.md#run2026-10-17-sweep-links). Waypoint hops only
  (`d2pilot.py wpchain`): each act's town builds the act, the Outer Cloister builds levels 27 and 28. Logger
  `tools/gdb/sweep-links.gdb`: `drlg-maze.gdb` plus the new `tools/gdb/drlg-links.py` (LNKP/LNKC after every pick and
  check of `LevelLinkBuild`, LNKW the Act1B widened test, LNKT/LNKU `LevelSeamsByTouch`'s `RectTouch`). Checker
  `tools/sweep_h5a.py logs`: gen 99 288 checks, 0 mismatches; the 128 logged builds replayed from their act seed with the
  unchanged model, every pick and check equal, 0 mismatches. `tools/drlg.py` unchanged, so no regression run. Sections
  "Plan 0038 batch H5a" in drlg/0004, 0006 and 0007; `re/symbols.csv`: `MazeFindWest` I → C.
  - **21 statements: 16 raised, 5 reclassified (d-none), 0 in part, 0 shortfall.**
    - Raised: maze 4, 5 (`FindWest`, map seed 58, through level 27's create-time index 2), 15 (Barracks `k` 0 and 2,
      six windows); warps 3 (×10: every pick choice ended a logged build, except `0x00676450` (0, 1), (2, 0), placed and
      logged but never kept), 5 (Burial Grounds reject, 6), 6 (Rogue-table rejects, 30), 8 (the widening's axis, 72).
    - Reclassified d-none (proposed): warps 5's widening deciding a check, 9 and 12 and preset 22 (level 27's index 2
      from side 1), 11 (`RectTouch` false branches and `t` = 0). Each rests on the code and an exhaustive scan of the
      builder's inputs (inventory § 2.6).
  - **New reading:** the Barracks takes level 27's create-time index when Black Marsh ends on side 0, so `FindWest` is
    reachable (drlg/0006 corrects § 7 step 1).
  - Review requested (backlog), with the spec-writer's Phase 3 entry. Slot 1 stopped, saves restored, no session left
    running.

- **2026-10-17 — Review: batch H5a (architect, `lane/h5a` at `6121fe6`; `main` merged in first, up to `b873f46`).**
  **Accept with fixes**, applied on the lane.
  - **Re-runs.** `sha256sum -c workspace/logs/sweep-links-manifest.sha256`: 9 OK, and the manifest's own hash is
    `911656ec…05fca1fb` as recorded. The tool hashes equal the record (`sweep-links.gdb` `d2001bfc…`, `drlg-links.py`
    `6ee05477…`, `drlg.py` `b38b91a6…`, `sweep_h5a.py` `a88405a8…`); `tools/drlg.py` and the existing gdb files are
    unchanged against `main`. `python3 -I tools/test_sweep_h5a.py`: 9 tests OK. `sweep_h5a.py logs`: 128 builds
    replayed, event sequences equal, gen 99 288 checks, 0 mismatches, every counter as recorded. `sweep_h5a.py scan 1
    301 0,1,2 0 82,52`: identical to the record (16 pairs per difficulty, 3 600 widened accepts, `RectTouch` 4 500 / 900
    edges, (0, 1) and (2, 0) tried 387 and 249, final 0, no model error). `drlg.py gen` alone on s3 (15 797 checks), s9
    (7 884) and s2 (17 751): 0 mismatches.
  - **Logger addresses (objdump, pinned `Game.exe`).** LNKP `0x00677388` is the `test eax, eax` after `call edx` (the
    pick, `EDI` = entry), with the seed copy at `[ebp−0x204]`/`[ebp−0x200]` taken from the act seed at `0x0067730E`;
    LNKC `0x006773C5` after `call eax` (the check); LNKW `0x00676F30` is the restore `add [esi+0x14], ebx` right after
    the widened `RectGapTest` (`+0xC` −200, `+0x14` +200 before it); LNKT `0x00677606` is the one `call 0x0066B880`
    (`push −1` at `0x006775FE`), LNKU `0x0067760B` the `test` after it. All resolve as the logger header says.
  - **Ruling 1, the five d-none: stand.** The review re-derived them without map seeds: an enumeration of every draw
    value (8 per draw) through the unchanged model, tables `0x006F0840` and `0x006F0DE0`, 64 leaves per difficulty.
    Black Marsh's first choice is `seq[0] & 3` in all 64 (entries 0–2 are two anchors and `LinkPickFixed`), its
    outcomes are 0 → 0, 1 → 1, 2 → 3, 3 → 3 at every difficulty with no backtrack and no widened reject, and every Act
    V seam pair shares an edge. The shared `r` is read in the code: the picks step only the copy, and the level-27
    draw at `0x006774D6` is the act seed's next step (`and al, 1; neg al; sbb eax, eax; add eax, 2` = `2 − (r & 1)`);
    the model that assumes no act-seed step between the copy and that draw predicted all 10 logged `LK27` draws and
    the seed after. `r & 3` = 1 forces `r & 1` = 1, so index 2 from side 1 has no input on stock data. `RectTouch`: one
    call, `push −1`, no stored pointer to `0x0066B880` in the file; its false branch and `t` = 0 have no stock input.
    `[I]` is the right tag for all five (code and an exhaustive input set, no run of the branch).
  - **Ruling 2, `0x00676450` (0, 1) and (2, 0): raised.** The B2 rule ("a build ended on it") existed because only
    `LNK1` rects were logged; `LNKP` logs the same rect at the pick's return, replayed against the model (6 each). The
    claim raised is the position, not that the choice is ever kept. The Rogue table cannot keep them: its 16 nonzero
    entries (`0x006F1158`: 0, 1, 9, 19, 21, 24, 30, 31, 33, 39, 41, 53, 54, 56, 62, 63) have residues mod 8 of 0, 1, 3,
    5, 6, 7, and the index is `d + 4f + 8·dir[a] + 32·flip[a]` (`0x00676E7B`–`0x00676EA1`). The spec says both.
  - **Ruling 3, FindWest by the create-time index: accepted.** Map seed 58 (s3) reached index 2 with Black Marsh on
    side 0 (no draw, no write): two level-28 windows, probes, level draws and rect equal to the model. Second source:
    `g_BarracksFinders` `0x006F0468` holds `0x00672460`, `0x006724A0`, `0x00672420`, and there is no direct call to
    `0x00672420`. `MazeFindWest` I → C stands. The § 7 correction is in drlg/0006's H5a section; step 1 now points to it.
    It also gives preset row 23 (`other v`, S4a) a run for `v` = 0; `v` = 2 is never kept (Black Marsh 2 → 3).
  - **Ruling 4, the new logger file: accepted.** "No logger change" in § 5 was a scheduling estimate. The batch adds one
    file of read-only breakpoints, loaded beside the unchanged `drlg-gen.py`/`drlg-maze.py`/`pilot.py`, and gen is
    0 mismatches on every log. § 5 and § 7 now say so.
  - **Ruling 5, the s2 retry: no effect.** The first `wpchain` call's 1,6 hop never registered, so no build or window
    is missing or doubled: s2 has 18 `LNK0` like s1 and s3, and gen and the replay pass on it. It is recorded under
    Deviations, which is enough.
  - **Ledger.** 21 statements: maze 4, 5, 15; warps 3 (×10), 5 (Burial Grounds half), 6, 8 raised (16); warps 5
    (widening half), 9, 11, 12 and preset 22 d-none (5). Every `[C]` line names its windows or logs next to a code
    anchor; no `[L]` added. Spot-checked anchors `0x006772C0`, `0x006775C0`, `0x0066B880`, `0x00676DD0`, `0x00676EB0`,
    `0x00672420`, `0x006F0468`, `0x006F1158` resolve in `re/symbols.csv` (all `C`).
  - **Fixes applied:** drlg/0007 § H5a says its counts are over both act objects (distinct: 15 Rogue-table rejects,
    3 Burial Grounds, 36 widened tests, 24 `RectTouch` tests); drlg/0006 § 7 step 1 and its trailing line point to the
    correction; inventory § 2.6 verdict and totals, § 5 and § 7 rows; the research map's warps row and the plans
    index queue.
  - **Totals** (recomputed once over the thirteen batch reviews and P1a): static 555, harness 532, c-emu awaiting S1f 4,
    blocked 423 (d-none 283, d-edit 80, d-sim 28, d-2c 14, d-owner 10, d-0032 8), deferred 2, raised 10: 1 526.
  - **Phase 3:** drlg/maze, drlg/preset and drlg/warps now have every batch accepted (S4a, S4b, H5c, H5e, H5a): all
    three clusters qualify for the re-tag. The spec-writer's H5a entry, the H5e entries and the review additions below
    are its inputs.
  - **Follow-ups (backlog):** to the spec-writer, additions to the lane's Phase 3 entry. None to the reverser.
  - **Next:** the owner merges `lane/h5a`; then the Phase 3 round for the three drlg clusters.

- **2026-10-17 — Phase 3, third round (spec-writer, `lane/p38s3`, from `main` `590e323`).** H5a's acceptance completes
  the batches of drlg/maze, drlg/preset and drlg/warps (S4a, S4b, H5c, H5e, H5a; inventory § 2.6). Template: the
  round-2 outdoor re-tag.
  - **drlg/maze** {C 105, I 26, L 3} → **{C 122, I 11, L 2}**. Raised rows 1, 3 (S4a), 4, 5 (`FindWest`), 15 (Barracks
    `k` 0 and 2) (H5a), 6, 11, 12 (H5e), 7, 16 (S4a), 9 (S4b). Split: 2 (one caller `[C]`; the fatal `[I]`, no stock
    case), 8 (failed candidates `[C]`; no room able `[I]`), 10 (the F cells `[C]`; 133 and 135 no stock build, tombs 69
    and 72 on the static reading, `[I]`). Unchanged d-none: 13 (now citing P1a's 408 000-build sample), 14. The G2
    comment now says `k` is the index the link builder left (drawn on Black Marsh sides 1 and 3, else the create-time
    index), with its own `[C]` note; the rebuilt-level rect `[C]` (H5e review (a)). P1a folded at `[I]`: the dead
    `MazeRoomAdd`/`0x00670E70`, the fatal sweep, the tomb redraw. *Open questions*: the unreached-paths entry narrowed
    to the no-room attach; the fatal entry kept; the dead-code entry closed.
  - **drlg/preset** {C 98, I 44, L 2} → **{C 134, I 24, L 2}**. Raised 27 rows (1, 7, 9, 10, 16,
    20, 23–26, 28, 30, 38, 40 S4a; 3, 11, 21, 34, 37, 39, 41 S4b; 31, 32 H5c; 2, 12, 13, 14 H5e). Split: 5 (path attach
    and `MapId` `[C]`; the skip, the path drop and the unused `MapId` branches `[I]`, no stock case, per S4a's survey),
    6 (`ValidId` stays `[I]`, c-emu), 8 (`action` below version 15 `[I]`), 29, 33, and 18 (`id = 573` has no logged unit,
    `[I]`; split here, not in the ledger). d-none 22 written as not reachable on stock data with the static argument
    (step 7 note 2); `v` = 0 cites run:2026-10-17-sweep-links, `v` = 2 never kept `[I]` (note 5). 27 reworded:
    `RoomIsOutdoors` reads `0x80000` (`[I]`). The bit-0x40 object marks are drlg/warps' waypoint bits (step 6 note 3,
    column note 5, Boundaries). Folded at `[I]`: plan 0039 P1a (the `Outdoors` callers, level 17's points) and plan
    0040 (d) (the server detach, no second dispatch). *Open questions*: four entries closed or narrowed.
  - **drlg/warps** {C 91, I 35, L 2} → **{C 104, I 16, L 1}**. Raised rows 1 (×2, H5c), 3 (×10), 5's Burial Grounds half,
    6, 8 (H5a), 7 (S4b), 13, 18 (S4a), 16, 19 (H5c). `0x00676450` (0, 1) and (2, 0) are `[C]` for position with the
    never-kept note (Rogue residues 0, 1, 3, 5, 6, 7), and the B2 rule reads "a build ended on it, or the placed rect
    was logged at the pick's return". Split: 14 along `Position` (S4a; backlog 582 (a)). d-none 5's widening half, 9, 11
    reworded `[I]` not reachable on stock data; 12 as a new C1 `[I]` note. Distinct counts quoted (15 Rogue rejects, 3
    Burial Grounds, 36 widened tests, 24 `RectTouch` tests). *Open questions* L621 struck, the d-none reasons kept.
  - **drlg/README**: step note 6 and the act-setup paragraph say level 27's index is drawn only on Black Marsh sides 1
    and 3 (reverser's H5a entry); wording only, counts unchanged.
  - **Backlog:** struck the H5e Phase 3 entry, the H5e review additions, the H5a entry and the H5a review additions;
    annotated as partly done the S4a corrections ((a)), the S4b corrections ((b), (c), (e)), the P1a fold ((c), (e)) and
    plan 0040 ((d)). New: review request to the architect with the three specs' counts; W4 wiki follow-up for levels.
  - **Commits:** drlg/maze, drlg/preset, drlg/warps (with drlg/README), then backlog and this log. Gate green; W4 warns
    for levels on drlg/README, maze and preset.
  - **Next:** architect review of `lane/p38s3` (backlog).
- **2026-10-17 — Phase 3 third round review (architect, `lane/p38s3` at `1940298`): accept with fixes.** `main`
  (`cc59597`: plan 0037 P3/P4 and its close) merged into the lane first; the one conflict was the backlog, both sides
  kept, deduplicated by entry text with the struck copies kept (the plan 0037 P3 entry struck from `main`, the H5e
  review additions struck from the lane).
  - **Raises and splits against the ledgers.** Every raise matches an accepted line of drlg/0004, 0006 or 0007 (S4a,
    S4b, H5c, H5e, H5a sections) and inventory § 2.6. drlg/maze: 1, 3, 7, 16 (S4a), 9 (S4b), 6, 10, 11, 12 (H5e), 4, 5,
    15 (H5a); splits 2 (S4b: one caller `[C]`, fatal remainder), 8 (S4a review's named remainder), 10 (133, 135 and the
    H5e review's tombs 69/72 static line). drlg/preset: the 27 raises as logged; 5 (S4a: path attach and `MapId` `[C]`,
    skip d-none), 6 (S4b; `ValidId` c-emu), 8, 29, 33 (S4b remainders), 21/34/37 (S4b in part, the remainder an owner
    rewording, now done), 27 left `[I]` as S4b's contradiction. drlg/warps: 1, 16, 19 (H5c), 7 (S4b), 13, 18 (S4a),
    3 (×10), 5's Burial Grounds half, 6, 8 (H5a); 14 split along `Position` (S4a shortfall); 20 stays (S4b shortfall).
    The P1a and plan 0040 (d) folds are `[I]` as drlg/0004 § P1a, drlg/0006 § P1a and drlg/0009 § 8 have them.
  - **Counts recounted** in the files: maze {C 122, I 11, L 2}, preset {C 134, I 24, L 2}, warps {C 104, I 16, L 1},
    drlg/README {C 75, I 6, L 0}. No `[L]` above *Open questions* in any. Gate green (W4 for levels only, filed).
  - **Anchors (objdump, pinned `Game.exe`, sha256 `631066c1…`).** `0x00673B19` `call 0x61F490` (`LvlMazeByLevel`'s one
    caller); `0x006774D6`–`0x006774F0` the act-seed step then `and al, 1; neg al; sbb eax, eax; add eax, 2`, written at
    `0x006774F9` (the `v` = 3 path just before it: `not eax; and eax, 1`); `0x006775FE` `push −1` → `0x00677606`
    `call 0x66B880`; `0x00676E44` `cmp [eax], edx` and `0x00676E5F` `cmp eax, 0x6F0848` (15 slots of 16 bytes);
    `0x00676E7B`–`0x00676EA1` index `d + 4f + 8·dir[a] + 32·flip[a]`; `0x00642ED7`/`0x00642EDC` `cmp edi, eax; je`
    (the tomb redraw); `0x0067252A`–`0x0067253C` `r ← (r + 1) mod 4`; `0x0055596C` `call 0x666120` (`PtrMove`);
    `0x006F0470` holds `0x00672420`; `0x0066BA80`–`0x0066BA83` `mov eax, [ecx+0x28]; and eax, 0x80000`. All resolve as cited.
  - **Ruling 1, preset 18: the split stands, but it is the S4a review's, not new.** The S4a review's fixes list
    "preset 18: id 573" among the raised-in-part rows, so the `id = 573` remainder was in the accepted ledger; the lane's
    log line "split here, not in the ledger" is corrected by this entry. The ledger in drlg/0004 § S4a still reads
    "raised" with "no unit with id 573 was met"; the review's fix list overrides it, as § 2.6 does for class moves.
  - **Ruling 2, the extra `[I]` on unused `MapId` and path branches: accepted.** S4a raised the statements whole on the
    branches taken; the survey over the 2043 DS1s shows the others are never taken, which is the d-none argument of the
    skip half, not a corroboration of their behaviour. Tagging them `[I]` beside the `[C]` is the S2a/S4a raised-in-part
    standard. The repetition (pseudocode comments and step note 6) counts each once per tag, as elsewhere.
  - **Ruling 3, warps *Open questions* L621 untagged and struck: accepted.** The H5a review asked to keep only what
    stays `[I]` with its d-none reason. A no-stock-case branch is not an open question (nothing left to look for), and
    an `[L]` with no lead behind it would be wrong; the three remainders are `[I]` in the body (B3, C1, C3). Fix below:
    the struck entry said every choice and validator path was reached, which is too broad.
  - **d-none rewordings against the H5a review's static arguments.** warps B3 (the widening: table outcome fixed by the
    difficulty and the first draws of Black Marsh and Dark Wood, 16 pairs, 3 600 widened accepts, 36 logged), C1 (the
    shared `r`, `r & 3` = 1 forcing `r & 1` = 1, outcomes 0→0, 1→1, 2→3, 3→3, the draw at `0x006774D6` after the copy),
    C3 (one call, `push −1`, no stored pointer, four seam forms, 5 400 tests, 24 distinct logged) and preset step 7
    notes 2 and 5 (`v` = 2 never kept) state the review's arguments with nothing added. All are `[I]`, as ruled.
  - **Commit subject.** `25ab5dd`'s subject lists "dispatch" among the raised rows; row 18 (the dispatch) was split
    (`[C]` for the logged branches, `id = 573` `[I]`), as its body and this log say. History is not rewritten; this
    entry is the correction.
  - **Fixes applied:** drlg/warps *Open questions*: the struck entry now says every pick choice was placed and logged
    (all but `0x00676450` (0, 1) and (2, 0) also kept) and every validator path but the widened reject was taken (no tag
    change). Research map: the warps row worded the same way.
  - **Follow-ups (backlog):** to the reverser, a static survey for preset 18's `id = 573` (not blocking). The W4 wiki
    follow-up for levels is already filed (spec-writer).
  - **Next:** the owner merges `lane/p38s3`.
- **2026-10-17 — Phase 3 third round wiki follow-up (spec-writer, `lane/wiki4`, from `main` `04bc872`).** The
  round-3 W4 follow-up. [levels](../wiki/levels.md): `based_on:` bumped for drlg/README, drlg/maze and drlg/preset
  (2026-10-17); re-read against drlg/warps too. § Laying out the act: rejects are overlaps, the Rogue side table (15
  logged) and the Burial Grounds side test (3 logged), no back-up in runs or the offline scan; every pick choice
  reached (nine chosen map seeds), Rogue `(0, 1)`/`(2, 0)` placed and never kept; the Act1B widening never decides a
  check (code plus scan). Level 27: drawn only on Black Marsh sides 1 and 3, else the create-time index; indices 0, 1, 2
  built; side-1 index 2 and side 2 not reachable on stock data (code plus enumeration). § Preset levels: the override
  sentence scoped to sides 1 and 3. § Maze levels: tomb ×3/×2 confirmed, no tomb with both by the code; every § F row
  built but 133/135 (no stock build) and tombs 69/72 (role reading); the no-room attach unreached; the Barracks side
  from `k` 0/1/2, all built. § Which seed: server/client agreement confirmed (888 pairs alike, 4 differing). § Units the
  game adds: centre monster and all six river types confirmed. § Pairing: the caller confirmed (695 activations); the
  near-list paragraph stays code-read. *What is not known yet*: maze (no-room attach, the sampled fatal), preset (no
  stock case list, the `Outdoors` reader, the server path detach, client detach and `action` unknown) and warps (the
  three no-stock-case paths) rewritten. Gate W4: 3 warnings before, 0 after.
  - **Next:** architect review (backlog).
- **2026-10-17 — Review: Phase 3 third round wiki follow-up (architect, `lane/wiki4` at `9324f8b`, `main` `8d03310`
  merged in first).** **Accept with fixes**, applied on the lane. Every changed statement was traced to the 2026-10-17
  drlg/README, maze, preset and warps at the same strength. § Laying out the act: the three reject kinds are B3 `[C]`
  (51 overlaps, 15 Rogue side-table, 3 Burial Grounds); no back-up in runs or the offline scan is B1 `[C]`; Rogue
  `(0, 1)`/`(2, 0)` placed and never kept is B2 `[C]`; the Act1B widening is B3 `[C]` for the test and `[I]` for "never
  decides", said as code plus scan. Level 27: drawn only on Black Marsh sides 1 and 3 (warps C1 `[C]`, preset step 7,
  drlg/README step note 6), indices 0, 1, 2 built (C1, maze G2 `[C]`), side-1 index 2 and side 2 not reachable (C1
  `[I]`), said as the code's reading. § Preset levels: the scoped override matches step note 6. § Maze levels: tomb
  ×3/×2 and 18/12 rooms are C1 `[C]`, distinct tombs C1 `[I]` "by the code"; the § F rows, 133/135 and tombs 69/72
  match the table tags and F3 `[I]`; the no-room attach is D2 `[I]` (0 of 337); the Barracks `k` 0/1/2 → east, south,
  west matches G2 `[C]` (finders East, South, West). § Which seed: 888/4 is preset step 2 note 4 `[C]`. § Units the
  game adds: step 4 notes 1, 2 `[C]` (map seeds 45 and 9; six `Def`s). § Pairing: F1 `[C]` (695 calls). *What is not
  known yet*: maze, preset and warps bullets match the three specs' *Open questions* (the 408 000-build sample, the
  `Outdoors` reader and server detach `[I]` said "by the code"). Links and anchors resolve, `based_on:` equals the
  specs' `updated:` (W4 0), gate fast tier green. **Fixes:** (1) the reject sentence said each reject's next choice "was
  then accepted"; B1 says a later choice of the entry was accepted (a Rogue reject can follow another), reworded.
  (2) The nine chosen map seeds were said to "end on every choice", against the next sentence and B2: they end on
  every choice but two, which were placed and logged. (3) *Preset units* no-stock-case list gains the Black Marsh
  ending on side 2 (preset step 7 note 5, `v` = 2). No follow-ups.
  - **Next:** merge `lane/wiki4` (owner).


- **2026-10-17 — Batch S1e done (reverser, `lane/s1e`, static; no slot, no game; Ghidra copy `workspace/ghidra-s1e`).**
  74 statements (data/calc 43, data/excel 13, data/strings 12, rng 2, save/d2s 4), all class (c-emu): **69 raised, 1
  raised in part, 4 not raised** (data-calc 13's L305 and 14 → d-edit, data-excel 43 and 44 → d-none; proposed in
  [inventory § 2.6](0038-inventory/README.md#26-moves-made-by-the-batch-reviews), pending review). By spec (raised /
  in part / not raised): data/calc 41/0/2, data/excel 10/1/2, data/strings 12/0/0, rng 2/0/0, save/d2s 4/0/0.
  - **Method:** ADR-0015 emulated reproduction, [run:2026-10-17-sweep-emu](../findings/data/experiments.md#run2026-10-17-sweep-emu)
    (and an addendum to run:2026-10-11-rng-emu): 28 643 emulated calls in ten families plus the two SSE2-flag reruns,
    all bit-exact against `tools/` models, each family with a negative control that fails (`neg` > 0).
  - **Tools:** `re/ghidra_scripts/EmuTrace.java` (`tools/ghidra.sh emutrace`): per-case memory and registers, dumps, a
    step limit, and a **trace of every data access outside the stack, the spec and the case memory**, so condition 2's
    read set is enumerated by the tool (ADR-0015 Negative: "EmuCall.java does not yet fail on a read outside the spec").
    `tools/sweep_s1e.py` (`cases`, `check`, `static`, `manifest`, `all`; `all` exits 0, report
    `workspace/logs/sweep-s1e-all.txt` `3293ae63…`, files manifest `94c19392…`) and `tools/test_sweep_s1e.py` (10 tests).
  - **Read sets:** every traced access of every family falls in a declared range: `.text` jump tables, `.rdata` tables
    (no write permission), four `.data` tables with no store in `.text` (objdump scan), and three runtime-written
    globals handled by the spec: the security cookie (no output depends on it), `__locale_changed` (its one writer sits
    in an uncalled `setlocale`), and the CRT SSE2 flag (both values run, identical outputs).
  - **Findings for Phase 3 and other lanes:** (1) **contradicted:** `LNG_GetLanguageCode` falls back to entry 0 only for
    ids ≥ 14; id 13 reads the 0x18 bytes after the table, whose "pointers" are 0x4D/0x42/0x54, so a `use` byte of 13
    crashes the string-table load (data/0002 § S1e; spec data/excel I1, data/strings A1). (2) The compiler fails on
    consecutive unary minus (`- -5`), which the spec's quirk list does not name. (3) Under SLEIGH, `idiv` of
    `INT32_MIN ÷ −1` returns 0 instead of trapping: a tool limit to keep in mind for any later emulated division.
    (4) `TC_ParseItemCell` cannot be emulated (every resolved cell reallocates the TC's entries).
  - **S1f:** the lane proposes 15 statements (11 rows) with declarable read sets and recommends that S1f run; the other
    16 candidates keep their classes (inventory § 2.6, S1e entry).
  - **Symbols:** 13 I → C (`CALC_Push`, `CALC_Pop`, `sub_00627B40_ItemCalcVar`, `sub_00631530_ItemCalcCell`,
    `EXCEL_AddCode`, `EXCEL_FindName`, `STR_ToLowerN`, `LNG_GetLanguageCode`, `g_LanguageTable`, `RNG_RangePow2Plus`,
    `BITBUF_WriteClamped`, `BITFIELD_Set`, `BITFIELD_Clear`); 5 added (`sub_0040F590_ReturnEcx`, `CRT_setlocale`,
    `g_pctype`, `g_LocaleChanged`, `g_Sse2Available`). Gate green. Review requested (backlog). Nothing merged.

- **2026-10-17 — Batch S1e reviewed (architect, on `lane/s1e` at `39d1c65`): accept with fixes.** `main` (`04bc872`:
  H5a, plan 0040 P1, plan 0037's close, P3 rounds 2 and 3, plan 0043 P0) merged into the lane at `2d5484d`; the plan-log
  and backlog conflicts kept both sides (one duplicate backlog entry dropped, its struck copy kept), and the totals are
  recomputed once below.
  - **Re-runs:** the manifest matches its 53 files; `sweep_s1e.py static` (53 of 53 pins, writer scan,
    `clamp_sequence_equal=1`) and `test_sweep_s1e.py` (10 tests) re-run identically. Under
    `GHIDRA_PROJ_DIR=workspace/ghidra-s1e`, heap 3 GB, `MemoryMax=4G`: the kept `lang` and `calcvar` cases gave `.out`
    files byte-identical to the lane's (182/182 and 5 000/5 000, undeclared 0). `cases` regenerates every family
    identically except `eval`, whose `skillsvar` skill index came from Python's unseeded module generator; fixed in the
    tool, `eval` regenerated twice (identical) and run: 6 000/6 000, neg 196, undeclared 0. A corrupted output gave
    `bad=2, undeclared=1`. Recorded in run:2026-10-17-sweep-emu (review re-run).
  - **Anchors read with objdump:** `sub_0040F590_ReturnEcx` (`mov eax, ecx; ret`); the divide (`test esi, esi; je` at
    0x006C0EC6, `cdq; idiv esi` at 0x006C0ECE); the ternary (0x006C0F2C); the compile limits (`cmp eax, 0x40` at
    0x006C1B7A, `cmp ecx, 0x40` at 0x006C1942); `dm78` (0x0064651F); the SSE2 flag's writer (0x0069A8C5, after
    `cpuid`); `__locale_changed`'s writer (0x006926F7, `mov dword [0x96dfe4], 1`, in a section with no file bytes, so 0
    at load); `LNG_GetLanguageIndex`'s clamp (0x005251A1) and `LNG_GetLanguageCode` whole; the entry-13 writers
    (0x005257E0–0x005258E7); `TC_AddEntry` → `TC_GrowEntries` → 0x0040B4B0; `CalcPoolAppend`'s growth loop; the clamp
    and its inlined copy operand by operand; `mana`'s `shl eax, cl`; `AffixCandAdd`, `MONSTATS_ValidId` and `MulDiv`'s
    calls (for S1f). All match the ledgers, with the wording fixes below.
  - **Rulings on the lane's points:**
    (1) **`EmuTrace.java` is the condition-2 check ADR-0015's Negative section asked for, with the writer scan beside
    it.** The trace enumerates every data access outside the stack, the spec and the case memory, and `check` fails on
    one outside the family's declared ranges (the review's corrupted output showed it), so an unaccounted read can no
    longer pass unseen. Condition 2's other half, that each declared image range is written by no code at run time,
    still rests on the static writer scan (`sweep_s1e.py static`), and the trace is blind to whatever the spec or case
    lines write, which is why ruling 3 applies to every spec write on an image address. New emulated runs use
    `emutrace`; `EmuCall.java`, `EmuFastcall.java` and `EmuCalcFunc.java` stay in the tree, frozen, so run:2026-10-16-
    calc-emu and run:2026-10-11-rng-emu can be re-run as recorded. No ADR change: ADR-0015 already admits a mechanical
    check, and its Negative bullet records the state on 2026-10-16.
    (2) **Image functions as probes are accepted.** Passing `sub_0040F590_ReturnEcx` as the variable reader, or a
    scratch function table of stock entries under made-up argc values, is a choice of arguments: data, no instruction
    patched, every callee run emulated (condition 1), synthetic inputs admitted (condition 4). The `[C]` covers
    `CALC_Eval`'s map under those arguments. A claim about a stock table's contents (which function sits at which index,
    with which argc) rests on the stock-table cases (row 20) or a static table read, never on the scratch table. A probe
    function is admitted only when its own code is short enough to read whole and is cited (two instructions here).
    (3) **The memory spec may set a global the code writes at run time, under one of three justifications, named in
    the finding:** (a) no output depends on it (the security cookie: XORed in and out, random per family); (b) every
    value it can hold at run time is run and the outputs compared (the SSE2 flag, 0 and 1: `memcpy`'s two paths gave
    identical outputs); (c) its run-time value is fixed by a writer scan (`__locale_changed`: 0 at load, one writer in
    `setlocale`, which has no caller and no pointer). Without one of these the claim is conditional on the value set,
    and says so. Inputs set by the spec on purpose (the language id, the already-read flag, `g_pDataTables`) are
    arguments in this sense and need no justification beyond the claim's own domain.
    (4) **The `LNG_GetLanguageCode` contradiction is accepted, narrowed.** `[C]` for the map: an unmatched id below 14
    reads entry 13, the 0x18 bytes after the table (also plain in objdump: loop bound `cmp edx, 0x730524`, then `cmp
    ecx, 0xe; jl`). Entry 13's low words are not image constants: 0x00525832–0x005258E7 write each as the default
    letter or the single character of string 0x14D1–0x14D3, so the values read there, and the fault, are `[I]`; no
    store touches the high words, which are 0 in the image, so each "pointer" is below 0x10000 in any run. The `use`
    byte of 13 crashing the load is `[I]`, d-edit. data/0002 review note added; spec-writer addition filed.
    (5) **data-excel 43, 44 → d-none accepted.** The allocator is reached unconditionally (above); the lookups the two
    claims rest on are `[C]`, the test order stays a code reading.
    (6) **S1f runs: 15 statements in 11 rows, as proposed** (inventory § 2.6 S1f table, § 5, § 7 rank 11). The two
    conditional rows (pool 27, uniques-sets 44) are kept only if their claimed branches are reached with no case
    stopping at the allocator, an import or the fatal path; that rule applies to every S1f row, as do capacity above
    every case for growable pools and ruling 3 for spec writes. S1f starts after `lane/s1e` merges (same findings).
    (7) **No ADR note for `idiv`.** Condition 5 already leaves faults out of emulated evidence; that SLEIGH returns 0
    for `INT32_MIN ÷ −1` instead of trapping is a tool fact, the kind of thing a case writer must know so that it never
    counts such a case as a match. It goes to the reverser's tooling notes (backlog), with the other EmuTrace notes.
    It does not change a decision, so nothing goes to the owner.
  - **Fixes on the lane:** `tools/sweep_s1e.py` (the `eval` writer's unseeded draw; `rnd_skill` now takes the
    generator); run record review re-run note; data/0002 row 51 review note (run-time-written entry 13, `[C]` for the
    index map only); data/0005 row 31 condition-5 citation (`shl eax, cl` masks the count; `sar eax, 8`); data/0004 row
    64 (pool growth not reached); data/0003 rows 20, 35 (the not-xlated cache miss not reached; the index 0 set after
    it); save/0001 the inlined clamp copy is not a plain register renaming, read equivalent at the review. Inventory
    § 2.6 S1e entry marked reviewed, with the S1f table; § 5 S1e row (record and tool named) and S1f row; § 7 S1e done,
    S1f rank 11; concurrency line. No tag in the ledgers changes; 69 raised, 1 in part, 4 not raised stand.
  - **Final:** 74 statements: **69 raised, 1 raised in part, 4 not raised, 3 reclassified** (data-calc 14 → d-edit;
    data-excel 43, 44 → d-none). **Totals now** (recomputed once over the fourteen batch reviews and P1a, with S1f
    created): static 567 (S1f 15 included), harness 532, c-emu awaiting a batch 0, blocked 415 (d-none 282, d-edit 73,
    d-sim 28, d-2c 14, d-owner 10, d-0032 8), deferred 2, raised 10: 1 526. Before S1f's creation the S1e moves alone
    give static 552, blocked 426 (d-none 285, d-edit 81).
  - **Follow-ups (backlog):** to the reverser, the EmuTrace tooling notes and the S1f batch; to the spec-writer,
    additions to the lane's S1e Phase 3 entry.
  - **Next:** the owner merges `lane/s1e`; then S1f (static, the lane's Ghidra copy may be reused).
- **2026-10-17 — cross-plan note from the plan 0039 Phase 2 review (architect).** Two statements of this plan's ledger
  were touched by plan 0039 Phase 2 (`lane/p39s`): items/cube **cube 45** (G4, the output cell) is already stated
  `[C]` in the spec from the accepted S2c raise, so the items/cube Phase 3 round counts it as applied; drlg/collision
  § G2 gained the S4a edge-point text (rows 43–44) at `[I]`, and the drlg/collision Phase 3 round raises it with the
  other G2 statements of those rows. save/d2s I4 gained a `[C]` note on the merged affix ids that cites S1a rows 87
  and 101; the I3/I4 pseudocode re-tag stays with the save/d2s round.

- **2026-10-17 — Batch S1f done (reverser, `lane/s1f`, static; no slot, no game; Ghidra copy `workspace/ghidra-s1f`).**
  15 statements in 11 rows, all class (c-emu): **15 raised, 0 in part, 0 not raised, 0 reclassified** (pending
  review). By spec: drlg/preset 1 (row 6, second statement), monsters/stats 2 (rows 9, 11), monsters/pool 1 (row 27,
  conditional, kept), items/affixes 2 (rows 6, 12), items/uniques-sets 1 (row 44, conditional, kept), data/calc 2
  (rows 8, 33), data/excel 6 (row 65's five statements, row 69).
  - **Method:** ADR-0015 emulated reproduction, [run:2026-10-17-sweep-emu2](../findings/data/experiments.md#run2026-10-17-sweep-emu2):
    eight families of `tools/sweep_s1f.py` (`validid`, `muldiv`, `candadd`, `pickaffix`, `calcvar2`, `parsetxt2` with
    both SSE2 flag values, `varroll`, `setpick`), 18 800 emulated calls plus 300 SSE reruns, all bit-exact against the
    models, each family with a negative control that fails (`neg` 65 to 1 948) and no undeclared traced access; a
    corrupted output fails the checker (`bad=2`, `undeclared=1`).
  - **Review conditions.** (a) `EmuTrace.java` gains `guard <addr>`: every S1f spec guards the fatal path (0x00408090,
    0x00408A60, 0x00681E09) and the allocator entries (0x0040B4B0, 0x0040B430, 0x0040B480), the `guardctl` family shows
    both kinds stop a case, and no S1f case stopped. Pool 27 and uniques-sets 44 are kept: their claimed branches never
    reach either (the fatal path is on NULL arguments only; `ItemApplyProps` mode 4 runs to its end on property-less
    set rows). (b) The itemscode pool (capacity 0x10000, at most 178 bytes used) does not grow; `EXCEL_AddCode` is not
    reached. (c) The spec writes on image addresses are listed per finding with their ruling-3 justification; DataTables
    fields are now written one per field read, so a read of any other field is traced.
  - **Findings for Phase 3:** (1) `MulDiv`'s 64-bit branches return the **low 32 bits** of the quotient (65 wide cases
    wrap; EDX holds the high half), and a negative `c` always takes the truncate-first branch once `a > 0x100000` or `b > 0x10000` (review fix). (2) uniques-sets 44's
    "non-positive total": a total of exactly 0 returns before `Range`; only a negative one reaches `RNG_RangeB` (0, no
    draw), after which the walk may pick or fail. (3) data/excel J3: the absent defaults are written at the field's
    width (u8 for 5, 7, 0x0C, 0x10; u16 for 0x0E, 0x11; u32 for 8, 0x0A, 0x12). (4) `ITEMS_BuildSetPick`'s 256-pair stack
    list has no count test (`[I]`; stock has 127 rows). (5) Pool 27's loop, once past 0, has no bound on its draws
    (`[I]`).
  - **Tools:** `tools/sweep_s1f.py` (`cases`, `check`, `static`, `manifest`, `all`; `all` exits 0, report
    `workspace/logs/sweep-s1f-all.txt` `e108a769…`, manifest `a1e058cc…`, 38 files), `tools/test_sweep_s1f.py` (7
    tests), `EmuTrace.java` `guard`. The S1e review follow-up (a) is done: [tooling.md § emutrace](../../.claude/skills/reverser/references/tooling.md)
    (syntax, untraced ranges and ruling 3, persistence, import stops, seeded writers, SLEIGH limits, frozen `Emu*`
    scripts); (b) and (c) of that entry remain.
  - **Symbols:** 6 I → C (`MONSTATS_ValidId`, `sub_00451FE0_MonStats2Rec`, `EXCEL_MapColumns`,
    `sub_0046ACE0_MissileRec`, `sub_004A89D0_SkillDescRec`, `SKILLS_LevelBands`); 1 added (`CRT_alldiv` 0x00684240).
    Left at I for their owners although these runs reach them: `ITEMS_UnitIsType`, `ITEMS_GetRecord`, `ITEMS_GetSeed`,
    `sub_0065FEC0_ItemApplyProps` (items). Gate green. Review requested (backlog). Nothing merged.
- **2026-10-17 — Batch S1f reviewed (architect, on `lane/s1f` at `48d5169`): accept with fixes.** `main` was merged into
  the lane twice (`ea8a3a8`, then `e40beb4` for plan 0039 P1c and the lane ledger); conflicts in the backlog, this log,
  `re/symbols.csv` (`MonStats2Rec` kept at C, `STATES_GetRecord` added from main), drlg/0004 and inventory § 2.6 kept
  both sides; the backlog has no duplicate entry; no address or name is duplicated.
  - **Re-runs:** the manifest matches its 38 files; `sweep_s1f.py static` (65/65 pins, 0 stores) and
    `test_sweep_s1f.py` (7 tests) re-run identically; `cases` regenerates every kept input byte for byte. Under
    `GHIDRA_PROJ_DIR=workspace/ghidra-s1f`, heap 3 GB, `MemoryMax=4G`, own `-log`: `muldiv`, `setpick` and
    `pickaffix` gave `.out` files byte-identical to the lane's (4 000, 3 000, 500 matches; undeclared 0, stopped 0). A
    corrupted `setpick` output gave `bad=2, undeclared=1`, and a case rewritten as a guard stop gave `stopped=1`.
    Recorded in run:2026-10-17-sweep-emu2 (review re-run), with the anchors read in objdump; all match the ledgers.
  - **Rulings on the lane's points:**
    (1) **`guard` is accepted as the mechanical check of condition (a)**, together with the static call closures
    (`sweep_s1f.py static` lists, per family, which reached functions call the fatal path or an allocator) and
    EmuTrace's existing stop on any pc outside the image's code (imports). A case reaching a guarded entry is a `STOP`,
    which `check` counts as `stopped` and fails (shown at the review); `guardctl` shows one fatal and one allocator
    entry stopping a real case; the other four guards are the same set lookup. The guard tests the pc at an entry, so
    it covers calls and jumps to it, not an inlined copy: the closure scan is what names the entries, and a family
    whose closure reaches an allocator not on the list must add it.
    (2) **Row 12 on the whole `ITEMS_PickMagicAffix` is accepted, and is the right unit**: the weight sum is the
    caller's, so `AffixCandAdd` alone could not show it. The `[C]` covers the pick with `applyProps` 0 (candidate
    filter, weight sum, draw, walk); the property path is not reached and makes no claim here. A wrapped total
    (`W + 1 ≤ 0`) was not reached and stays a code reading.
    (3) **Data-excel 65 L648 stands as filed**: `ItemCalcCell` is the real callback for the item calc columns and an
    admitted probe under S1e ruling 2 for the dispatch; the `[C]` covers "called with ECX 0, the record in EDX and the
    field offset as the first stack argument" (read in objdump at 0x006BE003–0x006BE01A); the length, row and column
    arguments, and the NULL-callback skip at 0x006BDFFF, stay code readings.
    (4) **One dword per field read is accepted and becomes the rule for new memory specs** that fill a scratch
    structure read through an image pointer: it puts every other field's read in the trace, which closes part of the
    "untraced spec range" gap of S1e ruling 3 for those structures. S1e's whole-page specs stand. Tooling note filed.
    (5) **Yes, `tools/ghidra.sh` takes a per-lane log path.** `workspace/` is shared by every worktree, so the fixed
    `ghidra-last.log` is truncated and read across lanes (`check_log` and the symbol commands' greps). Filed to the
    reverser: an env variable defaulting to a name derived from `GHIDRA_PROJ_DIR`.
  - **Conditional rows:** pool 27 and uniques-sets 44 are kept. Both claimed branches are reached (192 negative-`tries`
    cases and 93 stops at exactly 0; 1 878 zero totals, 458 negative totals, 134 failed walks) with no case stopped;
    `guardctl`'s NULL-seed case shows the varroll fatal path is the argument check only.
  - **Phase 3 precision notes:** MulDiv's low 32 bits on wrap is `[C]` (EAX only is returned after `call 0x684240`; 65
    wide quotients). The negative-`c` remark is corrected: it holds inside the large-argument branches (`a > 0x100000`,
    or `b > 0x10000`); with both small a negative `c` takes the 32-bit branch. Uniques-sets 44's split (zero total
    exits at `test esi, esi; je` 0x005C26B9 before `RNG_RangeB`; a negative total reaches it) read in objdump and
    stands. The `[I]` observations stand as `[I]`: the 256-pair list has no count (`sub esp, 0x814`, no compare in
    0x005C2675–0x005C26AD), and pool 27's loop has no bound once past 0.
  - **Fixes on the lane (3: omission 2, stale cross-reference 1):** the spec-writer entry's (b) and this log's
    Findings (1) give the negative-`c` rule its branch condition; the spec-writer entry gains (f), data/0005's `[C]`
    for `MISS_GetElemMin`/`Max`, which the lane's list left out (also (g), the NULL-callback skip, and (h), the clusters
    below); inventory § 5's S1f row named `sweep_s1e.py` families for `sweep_s1f.py`. Inventory § 2.6 S1f entry marked
    reviewed with the review paragraph, § 5 and § 7 rows updated; `docs/plans/metrics.md` lane row filled.
  - **Final:** 15 statements, **15 raised**, 0 in part, 0 not raised, 0 reclassified. **Totals** (recomputed once
    after both merges; neither merge moved a class, plan 0039 P1c's d-none remainder stays counted as S4a): static 567
    (S1f's 15 included), harness 532, c-emu awaiting a batch 0, blocked 415 (d-none 282, d-edit 73, d-sim 28, d-2c 14,
    d-owner 10, d-0032 8), deferred 2, raised 10: 1 526.
  - **Phase 3 clusters that qualify now:** data/calc (S1b, S1e, S1f) and rng/README (S1b, S1e); rng/seeds was done at
    the first round. drlg/preset, whose batches were all accepted by the third round, takes its S1f statement (L154).
    Not yet: data/excel, data/strings and data/README wait for H3b (and data/excel for the plan 0039 P1c fold);
    monsters/stats and monsters/pool for H4a; items/affixes for H2b; items/uniques-sets for H2b and H6d. Their S1f
    lines wait with them.
  - **Follow-ups (backlog):** to the reverser, the per-lane Ghidra log and the one-field-per-read tooling note; to the
    spec-writer, (f)–(h) added to the lane's S1f Phase 3 entry. Ghidra copy `workspace/ghidra-s1f` can go when the lane
    merges.
  - **Next:** merge `lane/s1f`; then a Phase 3 round for data/calc, rng/README and drlg/preset's S1f line.
- **2026-10-17 — Phase 3, fourth round (spec-writer, `lane/p38s4`, from `main` `2783aee`).** The S1f review's
  qualifying clusters: data/calc (S1b, S1e, S1f) and rng/README (S1b, S1e), every batch accepted (inventory § 2.6, § 5,
  § 7). drlg/preset's S1f line (L154, `MONSTATS_ValidId`) is left for a later pass while `lane/p39s2` edits that spec;
  data/excel, data/strings and data/README wait for H3b. Template: the round-3 re-tag.
  - **data/calc** {C 77, I 66, L 3} → **{C 129, I 17, L 3}**. Raised: rows 1, 2, 6, 7 (S1b: the missile and item
    callers by `ra2` plus the call sites read as code; the two function tables by the logs and the image); 4, 5, 9, 10
    (×7), 11, 12, 13 (15 of 16), 15, 16, 20, 31 (6 of 7), 36–40 (S1e, run:2026-10-17-sweep-emu); 8, 33 (S1f,
    run:2026-10-17-sweep-emu2). Split: 18 (`EvalItem`: offset test and the user `[C]`; the used item `[I]`, d-none), 19
    (drinking `[C]`; hover `[I]`, a Phase 2 leftover piece). Kept `[I]`: 13's L305 and 14 (the `INT32_MIN ÷ −1` fault,
    d-edit; step note 4g says emulation cannot show a fault), 31's `blvl` and 23–27, 34 (d-sim), 32 (deferred, its
    table row now without codes 45–48). Row 3 (meta prose, d-none) is gone with the rewritten paragraph. Restated
    with the raises: the reimplementation note on failed compiles (now `[C]`, `- -5` added). Corrections: `- -5` in
    § C (S1e (c)); 4g kept `[I]` (S1e (d)); the `m1rn`–`m3rn` out-of-range cases (S1e (e)); `manashift & 31` on `usmc`,
    `mps` and `mana` and `mana`'s arithmetic `>> 8` (S1e review (b)), with a reimplementation note; a new § G1 `[C]`
    bullet on `MISS_GetElemMin`/`Max` (S1f review (f)) and a `[C]` table row for codes 45–48. Not written here: S1f
    (b), the `MulDiv` negative-`c` rule (monsters/stats A1; data/calc calls `MulDiv` with `c = 100` only), and (g),
    the NULL-callback skip (data/excel J3). *Open questions*: the not-reached entry narrowed to the fault, five
    unit-state codes and hover.
  - **rng/README** {C 22, I 8, L 1} → **{C 28, I 4, L 1}**. Raised: rows 4 (no table read), 7 (unguarded forms) (S1b);
    3, 5 (`RangePow2Plus`, for the code only; S1e, the run:2026-10-11-rng-emu addendum). Split: row 2's two statements
    (the entry-points row and paragraph): 846 sites inside functions `[C]` by the objdump walk, 6 on Ghidra's reading
    `[I]`. Kept `[I]` (d-none): rows 1, 6, `RangePow2Plus` has no caller; step note 4 gains the S1b observation (14
    sites in 9 bodies with no static reference) at the same tag (S1b entry (b)). Evidence lists the S1b/S1e sections.
  - **Research map:** the data/calc row and the rng row rewritten whole. **Wiki:** [game-data](../wiki/game-data.md)
    § Calc formulas and *What is not known yet* restated, `based_on` data/calc 2026-10-17 (W4 1 → 0);
    [randomness](../wiki/randomness.md) § The generator and *What is not known yet* restated (same `updated:` date, so
    no W4 flag; changed under review fix 7).
  - **Backlog:** annotated as partly done the S1b entry ((b), (d) for data/calc and rng), the S1e entry ((a) for
    data/calc and rng, (c), (d), (e)), the S1e review additions ((b)) and the S1f entry ((a) for data/calc, (f)). New:
    review request to the architect with both specs' counts.
  - **Commits:** `4dc605a` data/calc (with the map row and game-data), `f8b9c76` rng/README (with the map row and
    randomness), then backlog and this log. Gate green (fast tier, W4 0).
  - **Next:** architect review of `lane/p38s4` (backlog).
- **2026-10-17 — Phase 3 round 4 review (architect, `lane/p38s4`): accept with fixes.** `main` (`1083b92`, ADR-0018)
  merged first; `docs/backlog.md` kept both sides and `tools/backlog.py migrate` moved the review request to its file
  (closed); the research-map conflict took the lane's `rng` row and `main`'s `items/tc` and `items/quality` rows.
  - **Checked.** Front matter recounted by script: data/calc {C 129, I 17, L 3}, rng/README {C 28, I 4, L 1}, no `[L]`
    above *Open questions* in either. data/calc: 47 ledger raises (S1b rows 1, 2, 6, 7; S1e rows 4, 5, 9, 10 ×7, 11, 12,
    13 (15 of 16, L305 kept with row 14 as d-edit), 15, 16, 20, 31 (6 of 7, `blvl` kept d-sim), 36–40; S1f rows 8, 33),
    the splits of rows 18 and 19 (S1b remainders: the used item d-none, hover a Phase 2 leftover), the `m2eo m2ey me3o
    me3y` table row and the `MISS_GetElemMin`/`Max` bullet (S1f review (f)), the `manashift` note, and the failed-compile
    note merged into one `[C]` give C +52 and I −49 with row 3's removal; row 3 (a tag in meta prose, d-none) goes with
    its paragraph, which now states the callers' evidence instead, so nothing claimed is lost. rng: rows 3, 4, 5, 7 raised;
    row 2's two statements split 846 `[C]` / 6 `[I]` exactly as rng/0001 § S1b gives them (objdump decode of the 852
    and the call walk: 836 + 10 after `int3` padding); rows 1, 6 and the 9 unreferenced bodies stay `[I]` (no observable),
    the weaker tag, accepted. Anchors re-read in objdump: the `call 0x0064B7C0` before 0x0064B1A4/0x0064B274 and
    `call 0x00627C20` before 0x005BEE04/0x005BEF16; `mov cl, [edi+0x188]; shl eax, cl` (0x0064663E, 0x0064667A,
    0x006468AA) and `sar eax, 8` (0x00646642, and `mps`'s at 0x0064667E: the pseudocode convention already makes a
    signed `>>` arithmetic); `lea edx, [esi−0x2B]`/`[esi−0x2C]` with `imul 0x55555556` (0x006468BE, 0x00646910);
    the zero test and `cdq; idiv` (0x006C0EC6, 0x006C0ECE); `cmp eax, 0x40` (0x006C1B77); the `CALC_Eval` call at
    0x00627C7A; `RNG_RangePow2Plus`'s body; `MONSTATS_ValidId`'s two signed `jl`. Map rows (21 record-only codes in
    S1e, 25 of 30 with S1f) and both wiki pages read against the specs. Gate green.
  - **Rulings.** (1) S1f (b), the `MulDiv` negative-`c` rule, belongs to monsters/stats A1 only and waits for that
    spec's round after H4a; data/calc's one `MulDiv` call passes `c = 100`, so it states nothing more. (2) S1f (g), the
    NULL-callback skip (0x006BDFFC–0x006BE001, re-read here), rests on review text only: data/excel J3 may state it
    `[I]` only after the reverser adds the line to data/0004 § S1f (backlog entry filed), or may leave it out.
    (3) drlg/preset L154 (S1f's `MONSTATS_ValidId`) is done at this review, since `lane/p39s2` has merged: `[C]` by
    run:2026-10-17-sweep-emu2 with the two signed compares cited; preset {C 135, I 25} → **{C 136, I 24, L 2}**, map row
    rewritten; the levels wiki is unaffected (same `updated:` date, no statement of the check). The drlg/preset cluster's
    re-tag is now complete.
  - **Fixes (2, overclaim).** game-data *What is not known yet*: hovering "was seen" to evaluate nothing → "is not shown"
    (the spec keeps it `[I]`); randomness: the 852 multiplier copies "each the same instruction" → "each loaded into a
    register by one `mov`" (registers differ).
  - **Backlog:** review request closed; the S1f Phase 3 entry annotated with the rulings; new: reverser, the
    NULL-callback finding line. Ledger row added in [metrics](metrics.md) (2: overclaim 2).
  - **Next:** merge `lane/p38s4`. Phase 3 continues per cluster as H4a, H2b, H6d and H3b are accepted.
- **2026-10-17 — Batch H6d done (reverser, `lane/h6d` from `main` `4d31287`, slot 2).** run:2026-10-17-sweep-quest-b6,
  19 sessions (5 failed starts or routes among them, all logged and listed), recorded in
  [items/experiments.md](../findings/items/experiments.md#run2026-10-17-sweep-quest-b6). Logger `tools/gdb/quests.gdb`
  with new `quests.py` lines `QME`, `MMR`, `BG0`, `BGR`, `GLD` and `OOP` (tags only). New checker `tools/sweep_h6d.py`
  (`logs`, `static`, `copies`) with `tools/test_sweep_h6d.py` (8 tests). New session runner `tools/h6d_sessions.py`.
  Pilot additions (`hunt --pet`, `--summon-key`, `--goal`, `objop --pdef-any`, Warriv). Six recipes.
  - **Checks:** `sweep_h6d.py logs` 0 bad over the 19 logs; `questdrops.py` 0 mismatches; `tc.py replay` 1 322 + 66
    classic calls, 0 failed; `items_chain.py affixes` 1 153 creations, 0 failed; `monpool.py check` 8 607/8 607.
  - **17 statements: 5 raised, 9 raised in part, 2 shortfall, 1 reclassified.**
    - Raised: qd 18 (Warriv's report: bit 1 cleared and bit 0 set, written save, quest TC in the next game), qd 22
      (gems in Normal, Nightmare, Hell and classic), qd 27 ×2 (Baal's gold: `RandLoHi` reproduced, one pile, stat 14),
      tc 26 (the quest TC replaces the column for a hireling's and a Hydra's kill).
    - In part: qd 11 ×4 and tc 27 (hireling and summon resolved to the owner, the unresolved killer passed to the TC
      walk; the `exp`-state branch remains), qd 13 (Baal's order and mode-0 record; MonModeRecord read statically for
      every class; Diablo remains), qd 16 ×3 (Baal fresh and done; Diablo remains).
    - Shortfall: qd 25 ×2 (the Nightmare forge was not reached in three sessions; the boundary is already `[C]` from
      the owner's Hell session).
    - Reclassified: us 21 → b, H1a (the services' copies make no creation record; the restore flag comes only from the
      version-`0x47` item-list reader). Proposed in [inventory § 2.6](0038-inventory/README.md#26-moves-made-by-the-batch-reviews).
  - Fewer than half of the rows are raised outright, because two targets need routes the scripted pilot lacks: the
    Chaos Sanctuary's seals and the River of Flame crossing on map seed 3811. An owner-played addendum (Diablo fresh and
    done, the Nightmare forge) is proposed in the run record.
  - **Also:** a correction to S2c's qd 49 refinement (Baal's death does create items: the gold piles); the backlog's
    `PlayerFindItemByCode` cursor-branch question answered statically (items/0010 § H6d).
  - **Symbols:** `QUESTS_MonsterDeathEvent`, `QUESTS_PlayerRecord`, `sub_005A78A0_MonModeRecord`,
    `sub_00595C60_A1Q6_NpcMessage`, `sub_0058DF20_A5Q6_BaalDeath`, `sub_0055B030_DropGold` and
    `sub_0055A090_DropGoldAmount` I → C; new `sub_0058F090_MonsterOwnerRef` (C).
  - Review requested (backlog). Slot 2 stopped, its saves restored, no session left running.
