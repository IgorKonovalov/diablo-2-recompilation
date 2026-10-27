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
  - *(added 2026-10-20, owner: plan 0039 closed)* The **data/excel cluster** also folds plan 0039's remainder:
    P1b (a), P1c (a) and the 11 data/excel W1 warnings (backlog
    `2026-10-17-reverser-spec-writer-gate-w1-a-c-i-statement.md`), after H3b.
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
  - Candidate for that addendum (`lane/h2c` review, 2026-10-21): items/properties 15, func 24, an H2c shortfall still
    counted as harness. An owner-played Hell Hellforge session on the H2c tcn game copy (`Haphesto (H)` names *Tomb
    Reaver*, the only stock-droppable func-24 carrier) would log it; the pilot reached the room in none of four tries.
  - Candidate (H4a, filed 2026-10-25; ruled a candidate at the `lane/h4a` review, 2026-10-25, not routed to the owner
    now): monsters/special 9, 10, 25, 31, 38, 50's thief half and
    monsters/spawn 11, H4a shortfalls still counted as harness. An owner-played Chaos Sanctuary session (`UniqNova`,
    Nightmare, seed 4907, `tools/gdb/mon-h4a-obj.gdb`) that opens seal 394 and kills the three seal bosses logs Lord
    De Seis and the closed gate; the pilot logged seal 394 but found no hop towards it.
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
    cube outputs at ilvl 99 (run:2026-10-15-cube-saves; *corrected at the `lane/p49r` review, plan 0049:* recipe inputs
    built by `tools/d2s.py`, not cube outputs). Affix ids with no stats in a game-written save is a creation
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
  - **Checks:** `sweep_h6d.py logs` 0 bad over the 19 logs; `questdrops.py` 0 mismatches; `tc.py replay` 1 322
    calls (66 of them classic; "1 322 + 66" in the draft, review fix), 0 failed; `items_chain.py affixes` 1 153 creations, 0 failed; `monpool.py check` 8 607/8 607.
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

- **2026-10-17 — Batch H6d review (architect, `lane/h6d`): accept with fixes.** `main` merged into the lane first, twice:
  `cf1d6e1` (148 commits past the lane's base `4d31287`), then `f33ee6d` (plan 0043 P1/1b, no conflict). Conflicts kept both sides: the backlog archive (then
  `tools/backlog.py migrate`; one stale copy of the plan 0043 archivist follow-up, closed on `main`, was migrated as a
  new open file by the merge and was removed), items/0001, 0004 and 0010 (main's P1b, P1c and S1f sections, then
  H6d's), this log, the inventory and `re/symbols.csv` (H6d's `C` rows replace `main`'s `I` rows of the same names at
  the same addresses; no duplicate address). `tools/d2pilot.py`: `main`'s `upkeep(args, p, st)` with the lane's
  `not args.pet` gate.
  - **Re-runs.** Manifest: 19 of 19 OK. `sweep_h6d.py logs` and `static` byte-identical to the lane's reports;
    `copies` (LZ0 15, PZ 15, no `IC0`) and `test_sweep_h6d.py` (8) re-run; `questdrops.py check` on the 19 logs
    (MemoryMax 4G) 0 mismatches; `tc.py replay` on sessions 6, 9, 12, 17, 18: 493 calls, 0 failed, each B6 test
    reproduced, the same counts as the lane's. objdump spot-checks: `MonModeRecord` whole (0x005A78A0–0x005A79B0, the
    five jump targets, the default `shl eax, 4; add eax, 0x006E2260`), `MonsterOwnerRef` (0x0058F090), the death
    event's owner lookup (0x00543A8C–0x00543AB2), Warriv's `QUESTRECORD` clear and set (0x00595D92, 0x00595D9C),
    Baal's gold loop (`imul 0x1770`, `+0x5DC`, `+0xBB8`, the `0xFFFF` clamp, the loop over `ctx+0x88`, the flag at
    0x0058DFA6), `DropGoldAmount`'s `cmp eax, 0x77359400` (0x0055A0F3) and `ITEMS_CreateForStore` call (0x0055A188),
    `PlayerFindItemByCode`'s five tests, and the `ItemCreateFromOldRec` store (0x00530FDA) and its callers.
  - **Ruling 1 (qd 18 and the Hydra kill on session 6's written save).** Accepted. The save is the game's own write
    (a *Save and Exit*), not a tool-built state, and the claim's three links are each logged: Warriv's clear and set
    in session 6, the written word (`d2s.py questbits`, re-run at the review on the kept file), and the loaded word
    `0x0019` that `B6P` reads in session 9 before the quest TC. The save was left in the lane's session scratch; it and
    the six built saves are now kept in `workspace/logs/h6d/saves/` with `quest-b6-saves.sha256` (fix, tool not kept).
  - **Ruling 2 (qd 22, one map seed).** Raised as filed, for the code path: the statement is "the same in every
    difficulty and game type", and the six kills ran it in four states with the draws reproduced and the ilvl
    following the difficulty (12, 49, 75). It says nothing about pick frequencies, which D1 does not claim. The
    statement's second clause, the per-player callbacks for "the killer's Act I party", is a party case the run cannot
    separate; Phase 3 keeps that clause `[I]` or splits it (fix to the spec-writer entry, overclaim).
  - **Ruling 3 (qd 13's Diablo half on the static read).** The kill order for Baal is `[C]` as filed. The static
    sentence "no class gets a special mode-0 record" is a new code reading whose run covered two of the five jump
    targets (Andariel's default, Baal's 0x005A7991). It is now `[I]`; Diablo's block (0x005A7977) was not run, so his
    record and order stay `[I]` with the static read as their support (fix, overclaim; the "five case blocks" wording
    made four blocks and a default).
  - **Ruling 4 (us 21 → b, H1a).** Accepted with a reach condition. The service copies make no creation record
    (`copies` re-run). The restore flag's only constant store is in `ItemCreateFromOldRec`, whose two calls sit in
    helpers `0x00531040` and `0x00531390`, called only from `sub_00533350_ItemListReadV71` (four calls, no stored
    pointer; the draft put the calls in the reader itself, fix, wrong anchor). H1a first shows a version-71 load
    reaches `0x00533350`; if the loader refuses that version first, the row goes to d-none with the refusal as the
    reason, recorded at H1a's review.
  - **Ruling 5 (the LvlWarp numbering note).** Known and documented: [LvlWarp](../tables/LvlWarp.md) header and
    § Row identity (88 records, the `Expansion` marker not loaded; `Id` equals the record index only up to 71) and
    [excel-bin](../formats/excel-bin.md) (the 30 marker rows). Nothing goes to the archivist; the run record's
    session 16 row now cites both.
  - **Ruling 6 (the owner-played addendum).** The Diablo remainders of qd 13 and qd 16 are recorded as **d-owner
    candidates** (inventory § 2.6; the rows stay counted as H6d, no totals change): the pilot reached the Chaos
    Sanctuary but cannot open the seals, and one owner pair (Diablo fresh, Diablo done) would close both. qd 25 stays a
    shortfall: its boundary is already `[C]` from the owner's Hell session, and a Nightmare equality would add a second
    case of the same compare. The forge session is not requested.
  - **Raises judged.** qd 11 ×4 and tc 27 in part (the `exp`-state branch and the party remain); tc 26, qd 18, qd 22,
    qd 27 ×2 raised; qd 16 ×3 in part (Baal both states). qd 27's single draw decides: the model reproduces the value
    and the seed after it from the logged quest seed, which a wrong reading would not match by chance. The S2c qd 49
    correction (Baal's gold piles are items) stands. The `PlayerFindItemByCode` answer agrees with plan 0039 P1b's
    § B12, which answered the same entry first on `main`; the H6d paragraph now says so and uses `main`'s names
    (`INV_GetCursorItem`, `ITEMS_GetCode`, `INV_GetFirstItem`, `INV_GetNextItem`), and the spec-writer entry's item
    (g) points at the P1b fold.
  - **Fixes (8).** Miscount 2: `tc.py replay` 1 388 → 1 322 (the classic 66 counted twice; finding, record, log);
    "harness batches hold the same 537" → 532. Misread 1: `MonsterOwnerRef` returns the GUID from `+0x2C` and the type
    from `+0x30` of the record MonsterData `+0x28` points to (the draft swapped them; finding body and *Functions*
    row). Wrong anchor 1: the `ItemCreateFromOldRec` calls lie in two helpers of the V71 reader. Overclaim 2: qd 13's
    static sentence `[C]` → `[I]`; qd 22's party clause kept out of the spec-writer's `[C]`. Tool not kept 1: the
    saves. Stale cross-reference 1: the `PlayerFindItemByCode` paragraph and entry (g) against P1b.
  - **Totals** (recomputed once after the merge): H6d moves one b row to H1a (46). **Static 567, harness 532, c-emu
    0, blocked 415** (d-none 282, d-edit 73, d-sim 28, d-2c 14, d-owner 10, d-0032 8), **deferred 2, raised 10:
    1 526.**
  - **Phase 3 clusters.** None newly qualifies. H6d's three clusters still wait: items/tc on H2a, H2b and H2c;
    items/uniques-sets on H2b and now H1a (us 21); items/quest-drops on H4a, H6e1 and H6e2. The H6d raises are banked in
    the spec-writer's entry for those rounds.
  - **Symbols.** The seven I → C stand (each name's function ran under a logged line: `QME`, `B6P`, `MMR`, Warriv's
    `QC`/`QS`, `BG0`, `GLD`); `sub_0058F090_MonsterOwnerRef` (C) is new and its address is not named on `main`.
  - **Backlog:** review request closed; the spec-writer entry annotated with rulings 2 and 3 and the (g) pointer; the
    H1a piece annotated with the reach condition. New: the human (owner) entry for the Diablo pair, d-owner candidates.
    Ledger rows added in [metrics](metrics.md).

- **2026-10-17 — `lane/rbs` review (architect, static backlog sweep): accept with fixes.** `main` (`fc3e89b`) merged
  first, clean; `tools/backlog.py migrate` changed nothing; `re/symbols.csv` untouched by the lane, no duplicates.
  - **Checked.** Tests: `test_sweep_s2c` (6), `test_sweep_h5e` (4), `test_sweep_s4a` (9) pass; `test_d2s` has one
    failure that `main` has too (two recipes with no base, from e2d42b1; backlog). Every hash in
    `workspace/logs/sweep-rbs-manifest.txt` re-taken: the four outputs and the tool versions match. `state_setters.py`
    re-run on a fresh objdump dump (same sha256 `b1e133a0…`): 659 sites, 391 resolved, 27 rows set or cleared and
    7 none, the per-row setters and test-site counts as in the stats/0002 table. `d2sio.py check` re-run over the 23
    logs (manifest hashes checked): 13 268 comparisons, 0 mismatches; the parent version gives 10. Sets params: 35
    stores of EBX = 0x006336A0 in `sub_00634DC0_LoadSetTables` (16 from 0x00634EAE to 0x00635779), and over the
    stock tables (case-folded) 44 skill ∩ state names, 0 montype ∩ state, montype ∩ skill = {`mosquito`}. Anchors read
    in objdump: 0x006336A0–0x00633727 (the `-`/digit test, skills 0x0096C7CC, montype 0x0096C868, states 0x0096BCF0,
    the 0 store), 0x00634DD7, 0x006BDFFC–0x006BE001, 0x00680170, 0x006807F3–0x0068080A, 0x0068023B, 0x00681454,
    0x0068086F, 0x0045F5AA–0x0045F5AD, 0x005D22F0–0x005D22FE, 0x00579B64. `tools/ghidra.sh` read: the default
    project `workspace/ghidra` keeps `ghidra-last.log`; `bash -n` clean.
  - **Rulings.** (1) 0041 (e) `[I]` accepted; the archivist entry stands. (2) The 34 States rows: 27 placed `[I]`,
    7 `[L]` in the finding, accepted. (3) room-tiles 20 raised `[C]`, 9 raised in part (fatal branch `[I]`): a draw in
    any of the 1 280 fallbacks would move the room's k (rule 10 met); recorded in inventory § 2.6 and the per-spec file,
    no class moves, totals unchanged. (4) The NULL-callback `[I]` line meets ruling 2 of the p38s4 review; data/excel J3
    may cite it. (5) `GHIDRA_LOG` and the tooling.md rules accepted. (6) The d2sio clamp accepted. (7) The S2c flag clobber
    accepted, extended (fixes). (8) The H5e counters accepted. (9) 0037 close: fire at the cap 2 115 `[C]` run (count
    re-read in the kept output); "never `boss`" `[I]`, consistent with combat/delivery E2 and the combat wiki. (10) H5e
    (a), (d), (e) accepted at `[I]`, entry kept open. On (e) and rule 9: the five unfollowed callees are named and
    counted, so the rule is met, but the d-none rests on them; they become item (e′) of the open entry. (11) The
    harness skips are accepted: each names the harness batch it rides on.
  - **Fixes (5).** *Miscount 1:* drlg/0008 (e)'s pattern `or[lb]?` missed `orw $0x20,(%eax)` at 0x006689BC and
    0x00668FC8 (cube parsers): three lines in the range, eight in `.text`. The text also scopes what the pattern does not
    cover (11 displacement forms in the range, register sources). *Tool not kept 2:* the `state_setters.py` and
    `d2sio.py check` outputs are now under `workspace/logs/` with manifest lines, cited in stats/0002 and save/0001.
    *Omission 1:* `sweep_s2c.py emu` now also clears flags on `call` and on a memory `cmp`/`sub`/`add`; three negative
    cases were added and the `static` output is unchanged. *Wrong anchor 1:* `PropParamCell`'s range ends at
    0x00633727, not at the next function's 0x00633730.
  - **Backlog.** The review request is closed. The H5e reachability and S2c tool entries are annotated. New entries:
    reverser, *static sweep, remaining* (the checkpoint list plus (e′)); reverser, the `test_d2s.py` recipe bases.
    The spec-writer's room-tiles re-tag entry (filed by the lane) stands. Ledger rows are in [metrics](metrics.md).
  - **Next:** merge `lane/rbs`.

- **2026-10-17 — Phase 3, room-tiles after the `lane/rbs` re-rule (spec-writer, `lane/sw5`, from `main` `3e169e4`).**
  Every batch carrying drlg/room-tiles rows is accepted (S4a, S4b, H5c, inventory § 5; the `lane/rbs` re-rule of rows
  9 and 20 and the plan 0039 P1a d-edit ruling of the 11 merge rows, § 2.6; no S1f row is left), so this lane completes
  the re-tag begun in the first round.
  - **drlg/room-tiles** {C 118, I 31, L 0} → **{C 120, I 32, L 0}**. Raised row 20 (step note 3, the `(10, 0, 0)`
    fallback makes no draw: 1 280 replayed picks, k matched). Split row 9: step 3b's fallback `[C]`, the `else fatal`
    line `[I]` (met in no log). From the plan 0040 Phase 1 amendment (and the reverser's 0040 entry (a)): the nested
    release call's `EDX` leaves the `[C]` bullet and a new `[I]` bullet states the wrapper's negation of the DUNGEON
    act's `+0x50`, the nested inner `EDX` 0 and `0x200000` as "released by the server" with no reader (drlg/0009 § 4).
    *Open questions*: the fallback entry struck, the `0x200000`/`EDX` entry narrowed to whether the 626 are exactly
    the server releases. No inventory row changes class.
  - **Wiki:** [levels](../wiki/levels.md) restated (the fallback confirmed, its fatal branch and the release flag
    read from the code); [randomness](../wiki/randomness.md) states neither and is unchanged. W4 0.
  - **Backlog:** closed the room-tiles re-rule entry and the plan 0040 Phase 1 amendment; annotated the reverser's
    plan 0040 entry ((a) done; (b), (c) remain). New entry to the architect with the old and new counts.
  - **Commits:** `e476530` (spec and research map), `5b59759` (wiki), then backlog and this log. Gate green.
  - **Next:** architect review of `lane/sw5` (backlog).

- **2026-10-17 — Review of `lane/sw5` (architect): accept with fixes.** Main `3e169e4` merged (already up to date).
  - **Checked.** The raise and split against [drlg/0002 § S4b](../findings/drlg/0002-room-build-draws.md#plan-0038-batch-s4b-2026-10-16)
    (rows 9 and 20 re-ruled) and the `lane/rbs` review ruling (3): row 20 `[C]` in step note 3, row 9 split in step 3b
    (fallback `[C]`, `else fatal` `[I]`), step note 3 carrying the same split; the release `[I]` bullet against
    [drlg/0009 § 4](../findings/drlg/0009-room-lifecycle.md#4-release) and the plan 0040 Phase 1 amendment (worded
    `[I]`, as the amendment allows). Front matter recounted by script: {C 120, I 32, L 0}, against {C 118, I 31, L 0}
    at `3e169e4` (+1 `[C]` step 3b, +1 `[C]` step note 3, +1 `[I]` release bullet); no `[L]` above *Open questions*.
    Research-map row rewritten whole, counts match. The three changed [levels](../wiki/levels.md) passages read
    against the spec. Anchors read in objdump on the pinned `Game.exe`: 0x0066B4C0–0x0066B4EB (the built test at
    0x0066B4C9, `test edx, edx` 0x0066B4DE, `sete al` 0x0066B4E0, call `RoomTilesRelease`), 0x0061A9D0 (`mov edx,
    [esi+0x50]`) and the call at 0x0061A9D7, 0x0066F232 (`or [esi+0x28], 0x200000`), 0x0066D868–0x0066D8A3 (the
    `(10, 0, 0)` lookup with cap `0x28`, the fatal at 0x0066D87B–0x0066D892). `re/symbols.csv` holds the five
    functions cited. Gate green.
  - **Fixes (3).** *Wrong anchor 1:* the spec cited `sete` at 0x0066B4DE, which is `test edx, edx`; now both
    instructions (0x0066B4DE, 0x0066B4E0). *Omission 1:* the fatal branch's `[I]` (step 3b and step note 3) gains its
    instruction range 0x0066D877–0x0066D892. *Overclaim 1:* the levels wiki's "nothing reads that flag" scoped to "no
    code that reads that flag was found" (the spec says no reader was found).
  - **Backlog.** The review request is closed. New entries: spec-writer, the 626 question once `lane/p40h` (plan 0040
    Phase 2, which logged `0x200000` set on 2 440 server releases and clear on 8 277 client ones) is accepted and
    merged; reverser, drlg/0009 § 4's `sete` anchor. Ledger rows are in [metrics](metrics.md) (usage unknown).
  - **Next:** merge `lane/sw5`.

- **2026-10-17 — `lane/rbs2` review (architect, static backlog sweep, second pass): accept with fixes.** `main`
  (`33d6d37`) merged first, clean (`72681d5`). `re/symbols.csv`: the lane's 12 rows are all new, with no duplicate
  address or name.
  - **Checked.** Every output in `workspace/logs/sweep-rbs2-manifest.txt` re-run and compared:
    - `callee_writes.py`, both runs on a fresh objdump dump: sha256 `f778470f…` and `15b51a4b…`, as kept. The dump's own
      hash differs because objdump's header names the input path. Totals 46 / 2 532 / 12 / 13 / 21; 204 write lines
      under `--all-writes`.
    - `sweep_h5e.py stampdefs 4 0 1 2 3`: `a45d047f…`, as kept.
    - `scan 1 601`: identical except the kept file's first line, the `systemd-run` banner.
    - `test_sweep_h5e`: 6 tests pass.

    Anchors read in objdump:
    - 0x006807F0–0x00680874 (no store between the skip and the call to 0x00680200);
    - 0x00680219–0x0068023B (`O` = `L+0x14`, the test on `(%esi)`);
    - `g_GridOps` (0x00749BAC: the six stubs 0x0067C420–0x0067C470), and `GridCellOp` (no bounds check);
    - `OutBorderSubApply`'s context (`memset` 0x38, the five callbacks, `+0x24` and `+0x28` null-tested at 0x0066F47D
      and 0x0066F5F2);
    - `BorderSubRecord`'s wildcard 62 (0x0066F9B5), `BorderSubStamp`'s `OutPresetPlace(…, file 0, 1)` (0x0066F62D);
    - 0x00530CFF (`mov %al,0x6a(%edi)` from `[ebp+8]`), 0x0053F16B–0x0053F17A (message `+0x11`), 0x00477CB0–0x00477CDF
      (the 0 → 3, 6 → 1, 8 → 2 map), 0x0044D630;
    - 0x0054C590 → 0x005350B0 (the `+0x4C` clear); `g_SrvPacketTable` entry 0x006E0F58;
    - 0x00554292 (`PlayerPairFlags(8)`), and `SkillUnitFilter`'s bit order;
    - the four `QuestsPlayerJoin` sites and their pushes (1 at 0x0056A06C and 0x0053266D, 0 at 0x005344E9 and
      0x0053458B), and 0x005345E2–0x00534607.

    Ten of the 31 new quests anchors were sampled (0x00598640, 0x005987D0, 0x00598780, 0x005B36A0, 0x0059CB20,
    0x00592E90, 0x0059EDC0, 0x00589937, 0x00599C10, 0x005B3E60): each one is the function or site that its section's
    table or text describes. `save.h` offsets are recounted: `+0x38`, `+0x60` and `+0x160`. Gate green; W1 is 12 on the
    merged tree.
  - **Rulings.**
    - (1) **(e′) d-none stands at `[I]`.** The closure is mechanical and kept, every indirect site is resolved, and
      every stopped call is named and counted, so rule 9 is met. The caveat, an unchecked grid index landing on `O`,
      stays written as a caveat. Nothing on the path is shown to compute such an index, and the tag stays `[I]`
      partly for that reason. It does not reopen the half.
    - (2) **(c) is complete once one more writer class is stated.** `OutBorderBuild`'s own border pieces are placed
      with file −1, and the rotation gives `(c + 1) mod Files` with `Files` = 3 for Defs 4–7, so they never take
      index 3. The finding left this out; it is added (fixes). With it, 5 and 6 endpoints are d-none at `[I]`.
    - (3) **(b) stays a shortfall** with its printed scan condition.
    - (4) **Bucketing** (inventory § 2.6, the `lane/rbs2` block):
      - outdoor 13's half keeps d-none, its condition met;
      - outdoor 14's remainder (5 or 6 endpoints from (c), the pool from (d) of the first pass) becomes d-none
        (remainder);
      - rows 11 and 7 stay a-run shortfalls.

      No class moves. The totals are recomputed once and are unchanged: static 567, harness 532, blocked 415
      (d-none 282), deferred 2, raised 10, 1 526 in all.
    - (5) The game-type writer, the `rejoin` flows with the double join, the `+0x4C` clear, the MP25 prediction and the
      12 symbols are accepted at `[I]`. The network names of modes 6 and 8 stay `[L]`.
    - (6) The `test_d2s.py` revert is right: the entry stays open for lane/arc5.
  - **Fixes (2).**
    - *Omission 1:* drlg/0008 (c)'s openings bullet now states the border-piece rotation (0x00675987, 0x00675B28,
      0x00675B45, 0x00675D19; `Files` 3 for Defs 4–7, read at the review) and the explicit indices on other Defs.
    - *Other 1:* the template placeholder line is removed from the review request.
  - **Backlog.** The review request is closed. The *static sweep, remaining* entry is annotated: H5e done, and a new
    item to print the H5e (a) vertex-merge condition in the scan (row 7 waits on it). New spec-writer entries:
    drlg/outdoor L693 and L866 wording; the quests and economy readings for plans 0042 and 0043 Phase 3. Ledger rows
    are in [metrics](metrics.md) (usage "—").
  - **Next:** merge `lane/rbs2`.

- **2026-10-17 — `lane/rbs3` review (architect, static backlog sweep, third pass): accept with fixes.** `main`
  (`78b96a9`) merged first, clean. `re/symbols.csv`: the lane's 5 rows are new, with no duplicate address or name.
  - **Checked.** Every output in `workspace/logs/sweep-rbs3-manifest.txt` re-run and compared:
    - `sweep_rbs3.py` `flagreads`, `callers`, `pushes`, `writes`; `xrefscan.py 0x005A01B0`; `sweep_s1e.py static`;
      `sweep_s3b.py pool`, `special`, `stats`; `sweep_s1a.py static`: all ten byte-identical (sha256 as kept), every
      tool hash as in the manifest.
    - The MonPlace output: identical (`01db978a…`) once its `#` header lines are echoed between the listed commands;
      the manifest line lists the commands only.
    - `rooms.py check` (under `MemoryMax=4G`) and `sweep_h5e.py scan 1 601`: identical except the `systemd-run`
      banner. 0 mismatches over 2 215 807 checks; condition met 0, ring merge 0, 125 seams, minimum overlap 24 (5 seams).
    - `test_rooms.py`, `test_sweep_h5e.py`: pass. Gate green.

    Anchors read in objdump: `sub_006483A0` whole (MonIsNpc at 0x006483B6, the room from `[esi+0xC]` = the planner's
    lookup at 0x00649AC5, `neg/sbb/add 1` after `RoomIsTown` at 0x00648417); `PathPlan` 0x006499AE (`0x40000`),
    0x00649AD9, 0x00649AEE (third argument), 0x00649C7B (clear, return 0); 0x005FBFB7's pushes (`EDI` third, 0 after the
    loop at 0x005FBF71); 0x005A454E/0x005A4558 and `SpecialModsApply` 0x005A2123, 0x005A214D (`push 1`), 0x005A215A
    (`push 0`); `MonMarkSpecial` (`EDX` = 8 at 0x005A034A, the `or` at 0x005A0375 on every monster with data);
    `ChampionMemberMark` 0x005A48EB–0x005A4905; `MonMakeSpecial` 0x005A495E (`cmp ecx, ecx`) to 0x005A4978;
    `SpecialMonPlace` 0x005A0B56–0x005A0B61; `COMBAT_ApplyDamage` 0x0057C709–0x0057C732; the MonPlace switch
    0x0054E76F–0x0054E782 and 0x0054EAFE (returns `ESI`, 0 since 0x0054E62A), 0x0054EAB1, the navi spawn at 0x0054E919
    (class `0x10A`), the tentacle step 0x0054E789–0x0054E7BB; the `sete` pair 0x0066B4DE/0x0066B4E0.
  - **Rulings.**
    - (1) **Town-follow: a shortfall still**, ruled in the [plan 0040 log](done/0040-drlg-room-lifecycle.md#implementation-log)
      (post-close entry). No harness addendum or owner-play candidate until the static remainder is read; a harness
      case, if one follows, is a plan 0038 harness batch.
    - (2) **Dead champion "not saved on stock data": `[I]`** (plan 0040 log). The run cannot separate it.
    - (3) **(c): § 6 corrected by the lane; "flag-1 handlers through `SpecialModsApply`" raised to `[C]`** at the review
      (the code and the run's 15 champion restores; flag 0 gives 15 mismatches). drlg/lifecycle repeats the old
      wording: spec-writer.
    - (4) **MonPlace: the scope stands** ("place nothing" in `PresetMonSpawn`). The review counted the readers: both
      callers of `PresetUnitDispatch` (`PresetUnitSpawn`, `RoomInactiveUnitsRestore`) reach the switch, so the first
      spawn and the restore of a kept group preset place nothing there; four other callers of `PresetMonSpawn` are
      unfollowed, now named in monsters/0003 § 7 (rule 9). They go to the static queue.
    - (5) **Outdoor 7 stays an a-run shortfall** (inventory § 2.6, the `lane/rbs3` block): 0 of 52 200 windows is a
      scan of 600 seeds, not a bound on the seed-dependent layout, as with row 11. A static bound on the layout's
      level offsets would make it d-none. No class moves; totals recomputed once after merging `main`, unchanged:
      static 567, harness 532, blocked 415 (d-none 282), deferred 2, raised 10, 1 526 in all.
    - (6) The S3b leftover, the S3b, S1e (c) and S1a (b) tool follow-ups, the five symbols at `I` and the
      harness-play partial-log rule are accepted.
  - **Fixes (4).**
    - *Under-claim 1:* drlg/0009 § 11.1 (c) split: `SpecialMonRestore`'s flag-1 handlers through `SpecialModsApply`
      `[C]` (run:2026-10-17-lifecycle as second source); the `minions` 0 stays `[I]`.
    - *Overclaim 1:* "flag 0 shows outside stat 12 on every minion restore" → "would show (not looked for)"; the closed
      0040 P2 follow-ups entry annotated to match.
    - *Stale cross-reference 1:* drlg/0009 § 11's stat-12 bullet still called the flag-0 result "§ 6's"; now "§ 6's first
      reading (corrected in § 11.1 (c))".
    - *Omission 1:* monsters/0003 § 7 names `PresetUnitDispatch`'s two callers and `PresetMonSpawn`'s four other callers
      (`sweep_rbs3.py callers 0x0054E600 0x005557D0`).
  - **Backlog.** The review request is closed. The *static sweep, remaining* entry is annotated. New reverser entry:
    [rbs3 review static remainders](../backlog/archive/2026-10-17-architect-reverser-rbs3-review-static-remainders.md)
    (town-follow remainder, outdoor 7 layout bound, MonPlace readers, the optional unit-seed search). The lane's
    spec-writer entry is annotated with the lifecycle rewording. Ledger rows are in [metrics](metrics.md) (usage "—").
  - **Next:** merge `lane/rbs3`.

- **2026-10-17 — Phase 3, the `lane/rbs3` readings and the outdoor H5e reasons (spec-writer, `lane/sw6`, from `main`
  `925d060`).** Two spec-writer entries that need no new evidence: the reverser's rbs3 lifecycle and MonPlace readings
  (with the `lane/rbs3` review's annotation) and the architect's outdoor H5e remainders after `lane/rbs2`.
  - **drlg/lifecycle** {C 78, I 70, L 8} → **{C 80, I 73, L 7}**. From drlg/0009 § 11.1 as the review ruled:
    `SpecialMonRestore`'s flag-1 handlers through `SpecialModsApply` (0x005A4558) `[C]` (the run's 15 champion
    restores), its pushed 0 the `minions` argument `[I]`, `MinionRestore`'s own flag 0 `[I]` ("would show outside
    stat 12", not looked for). The dead-champion rule restated from § 11.1 (b), still `[I]`; the `[C]` "No logged dead
    champion was saved" unchanged. Open questions: town-follow kept `[L]` with § 11.1 (a); the `0x08` and flag-1
    questions struck; the minion-flag half kept.
  - **monsters/special** {C 106, I 92, L 3} → **{C 106, I 94, L 3}**: every MonPlace row from the `PresetMonSpawn`
    switch `[I]` at the review's scope (first spawn and restore through `PresetUnitDispatch`, four other callers
    unfollowed); the restore flag split in § J; the S3b mod-list readers in E1.
  - **drlg/preset** {C 137, I 23, L 2} → **{C 137, I 25, L 2}**: the `place_group` pointer in § 6 and the
    reimplementation note, same scope.
  - **drlg/outdoor** {C 180, I 19, L 3} → **{C 180, I 19, L 2}**: H2's swapped cliff-cave scan and H6's 5/6 endpoints
    and exhausted pool say why there is no stock case (drlg/0008 (c) with the border-piece rotation, (d), (e), (e′));
    rows stay `[I]`; two answered open questions struck. Rows 7 and 11 unchanged. No inventory row changes class.
  - **Wiki:** [levels](../wiki/levels.md) and [monsters](../wiki/monsters.md) restated; W4 0.
  - **Backlog:** both entries closed. Review request:
    [sw6 review](../backlog/archive/2026-10-17-spec-writer-architect-sw6-rbs3-readings-and-outdoor-h5e-review.md). The
    rbs2 quests/economy readings entry is left for the 0042 and 0043 Phase 3 passes.
  - **Commits:** `c210e90` (specs and research map), `e99c773` (wiki), then backlog and this log. Gate green.
  - **Next:** architect review of `lane/sw6` (backlog).
- **2026-10-17 — `lane/sw6` review (architect): accept with fixes.** Main (`7e15a1b`) merged into the lane first. Each
  restated statement checked against its source at the same strength: drlg/0009 § 11.1 (a)–(c) and the `lane/rbs3`
  ruling annotation (lifecycle H2b, H2c, § F, § H, open questions), monsters/0003 § 7's switch bullet (special § H,
  preset § 6), monsters/0003 § S3b (special E1), drlg/0008 (c), (d), (e), (e′) with the rbs2 review (outdoor H2, H6).
  special § H follows the newer switch bullet for 19–21 and 27; it agrees with [MonPlace](../tables/MonPlace.md) row
  for row (both kept row 24's "class 0"; fix 2). Anchors spot-checked with objdump: 0x005A454E `push $0x0`, 0x005A4558 `call 0x5a2120`, 0x005A2123
  `cmpl $0x0,0x10(%ebp)`, 0x005A214D `push $0x1`, 0x005A4811 and 0x005A4830 `push $0x0`, 0x005A0CE7 the flag test,
  0x0054E76F–0x0054E775 (`index − 2`, bound `0x1E`), the byte table `0x0054EB30` (rows 6, 7, 9, 12–16, 19–21 → 8),
  0x006807F3–0x0068080A (the 2/3/17 skip), 0x0068023B `test $0x20,%al`. All resolve. No `[L]` above *Open questions*
  in the four specs; the wiki statements keep their hedges; research-map rows whole. **Scope addition (E1):** accepted;
  it was in the reverser entry's third bullet, and the review completes it (fix 1).
  - **Fixes (4):**
    1. *under-claim*: special E1 kept "the copied list is what the server sends" `[I]`; the S3b review raised it
       (`[C]`, S3b spec-writer entry (f)). Split: `[C]` for the handlers never called and the packet, `[I]` for the
       boss handlers' flag 0 and the other readers.
    2. *stale cross-reference*: special § H's fixed-class bullet kept "24 class 0" from monsters/0003 § 7's stale
       bullet. Dropped, and an `[L]` open question added: objdump at the review gives rows 24 and 26 the group case,
       which returns 0 outside Normal (0x0054EAA8–0x0054EAB9), never the fixed-class table; the finding has not taken
       this in (reverser follow-up annotated).
    3. *omission*: outdoor H2 listed the closure's writes as "the seed, stack slots, allocations and grid cells"; (e′)
       also names the level's rotation list, the BorderSub context and the LvlSub record's grid view.
    4. *other*: research-map special row's "five fixed-class rows" (the fixed-class table is rows 17–32) → "five rows
       placed at the point"; row rewritten whole with the new counts.
  - **Counts after the review:** monsters/special **{C 107, I 94, L 4}**; drlg/lifecycle {C 80, I 73, L 7}, drlg/preset
    {C 137, I 25, L 2}, drlg/outdoor {C 180, I 19, L 2} as filed. Gate green.
  - **Backlog:** the review request closed; the S3b spec-writer entry annotated ((f) applied, (a)–(e) remain); the
    monsters/0003 § 7 reconcile entry (reverser) annotated with the rows 24/26 objdump lead. Ledger rows added.
- **2026-10-17 — `lane/rbs4` review (architect, static backlog sweep, fourth pass): accept with fixes.** `main`
  (`af90ea8`) merged into the lane first (clean; `backlog.py migrate` moved nothing). Request:
  [rbs4 review](../backlog/archive/2026-10-17-reverser-architect-review-lane-rbs4-static-sweep-pass-4.md).
  - **Re-runs.** Every `sweep-rbs4-*` output re-run against `workspace/logs/sweep-rbs4-manifest.txt`: `layouts` (under
    `MemoryMax=4G`, 5 min) byte-identical, and `dwords`, both `tree`, both `stackfield`, both `regarg` and the
    `xrefscan` loop identical; `sweep_rbs3.py pushes 0x00648CF0 2` identical but for two caller names `lane/rbs4` added
    (`MonPathPlanType`); `pushes 0x0054E600 4` gives the five calls. Tool hashes match the manifest. Ten outputs echo
    their command on line 1; the `xrefscan` loop (`xref-pathcb`) prints per-address headers and its command is in the
    manifest only. Counts recounted from the outputs: override calls 94 immediate + 9 not (five through `+0x0D`/`+0x02`),
    setter 9, `PathSetType` 51, `MonCmdInit` 49, `MonSetMode` 54, `UnitTeleport` 20 in 19 functions, 288 seams with
    minimum 24 on 15.
  - **Layout bound method checked.** `_Probe` turns any draw used other than by `& 1/3/7` or `~` into a fatal stop, and
    every `step()` in `drlg.act_links` (link picks, `_cyc`, the `0x00676C00`/`0x0067D830` sides, level 27) is masked; the
    enumeration of independent draws is a superset of the LCG's reachable layouts, so 0 met is a bound for Acts I, II, IV
    and V.
  - **Anchors read in objdump:** `PathRoomUpdate` 0x0064FAD0 whole (in-room test, `RoomAtSubtile` 0x00463740 at
    0x0064FB1B and 0x0064FB31, the `0x40000` give-up at 0x0064FB3C, the room relink 0x0064FB54–0x0064FB7F; no town
    call); `SkillTeleportDo` 0x005CA360 whole (the caster's room → level → Levels `+0x04`, 0 refuses, 2 adds the
    `0x804` line test 0x005CA3AE, then `UnitTeleport` 0x005CA3C9); `MonAiPathOverride` 0x005DE190 (1 → 7, two calls of
    0x005A6260 passing `EDX`); 0x005ACB1F–0x005ACB43 (the id from 0x006444A0 in `EDI`); `MonMovePlan` 0x005A63FB, 0x005A6429
    (100), 0x005A6443 (101 → 13); `PathSetType` 0x00648D65 (`and 0xFFF800FF`, bits 8–18); `UnitTeleport` 0x00554F00/0x00554F14
    (room at the point) and 0x00554F32 (`0x1C09`); `MonSetMode` 0x005A7D22–0x005A7D2F; 0x005AA1F0–0x005AA1F7 (Missiles
    `+0x4C` within `[0, nMonStats)`); `MonIdFromKind` 0x00659B80 (kind 0 adds 0x0096C70C and `+0xA80`, kind 2 `+0xA80`);
    0x0058A6F6 (`push 2`); the bound check 0x0054E76F. Three cited addresses were mid-instruction (fixes).
  - **Rulings.**
    - (1) **Town-follow: a plan 0038 harness batch, H7a (`lifecycle`)**, recorded in the
      [plan 0040 log](done/0040-drlg-room-lifecycle.md#implementation-log) (post-close entry) and inventory § 5 and § 7.
      The `lane/rbs3` ruling made a found route the trigger, and § 11.2 found two. Recipe (b) first, after an offline
      geometry check (seed and points, or a recorded "no stock layout allows it"); recipe (c) only after a static read
      shows an AI teleport target in a town room. Not owner play: both are scripted `rooms.gdb` sessions. The `0x400`
      drop (plan 0040 close follow-ups (2)) rides on the same batch. Until H7a runs the case stays a named shortfall;
      the lifecycle spec's open question is routed to the spec-writer.
    - (2) **Outdoor 7: split** (inventory § 2.6, `lane/rbs4` block): d-none for Acts I, II, IV and V on the bound;
      Act III an a-run shortfall on its sample. A whole-row d-none would claim Act III on a sample, and "d-none outside
      Act III" with Act III kept a-run is this split. No class moves (one statement, counted as H5e, as outdoor 13's
      half); totals recomputed once after the merge, unchanged: static 567, harness 532, blocked 415 (d-none 282),
      deferred 2, raised 10, 1 526 in all.
    - (3) **MonPlace rows 33–35: accepted `[I]`.** The bound check at 0x0054E76F is caller-independent; the four other
      callers pass SuperUnique ids (kind 2), a MonStats row (bounded at 0x005AA1F7) or an unfollowed skill value
      (0x005ACB43), named and counted.
    - (4) **Symbols:** the 17 new rows are clean (no address or name duplicated after the merge). Of the five raises,
      `DrlgRefAdd` (inside `DrlgRefMove`'s replay, 634 982 callbacks) and `DrlgStatusRecompute` (the status rule on all
      of them) are supported whole. `RoomsDeactivate` (level-120 half unreached), `InactiveMonstersRestore` and
      `RoomInactiveUnitsRestore` (kept units, `0x400` records, the level-108 rule, a boss-less minion unreached) are
      supported **in part**: `C` in `re/symbols.csv` for the role, the remainders written `[I]` (fix 3).
  - **Fixes (5).**
    - *Wrong anchor 2:* drlg/0009 § 11.2 (b) `RoomAtSubtile` 0x0064FB0B → 0x0064FB1B and the relink 0x0064FB4B–0x0064FB80
      → 0x0064FB54–0x0064FB7F; § 11.2 (c) 0x00554EC9 (inside the assert's `push`) → 0x00554F00/0x00554F14.
    - *Overclaim 1:* the five-raise paragraph in drlg/0009 § Functions now heads three of them "raised in part" and names
      the unreached restore and release branches; the `RoomsDeactivate` row reads "C in part (level-120 half I)".
    - *Stale cross-reference 1:* the function tables of objects/0001 (`RoomsDeactivate`, `InactiveMonstersRestore`) and
      monsters/0002 (`RoomInactiveUnitsRestore`), which `re/symbols.csv` cites as evidence, still said `I`; now "C in
      part", pointing at drlg/0009.
    - *Other 1:* § 11.2 (c)'s "That byte is 1 in the towns" read as if the destination's byte mattered; reworded: the
      test reads the caster's level (0x005CA37C–0x005CA395), never the target's.
  - **Backlog.** The review request is closed; plan 0040 close follow-ups closed ((1) done, (2) to H7a); the *static
    sweep, remaining* entry annotated. New: spec-writer
    [rbs4 town-follow and outdoor 7](../backlog/archive/2026-10-17-architect-spec-writer-rbs4-town-follow-and-outdoor-7.md);
    reverser [rbs4 review static remainders](../backlog/archive/2026-10-17-architect-reverser-rbs4-review-static-remainders.md)
    (H7a geometry prep, the teleport-target read, optional unfollowed calls). Ledger rows in [metrics](metrics.md)
    (usage "—").
  - **Next:** merge `lane/rbs4`.

- **2026-10-17 — Wiki refresh of the index and *How we know* (spec-writer, `lane/wiki6`, from `main` `407758a`).**
  The two pages W4 cannot see as stale (ADR-0012). [wiki/README](../wiki/README.md): plans 0037 and 0040 closed, room
  lifecycle on the Levels page, the open-plan list from the plan index, the Levels and How-we-know table rows.
  [wiki/how-we-know](../wiki/how-we-know.md) (`based_on: [process]`): emulated reproduction (ADR-0015, batches S1e
  and S1f), simulation per event and the plan 0041 seed-invariance rule (ADR-0014), two clients (ADR-0008), d-none
  bounds and the outdoor 7 split, shortfalls and open questions, this sweep, the review loop; ADR list gains 0008,
  0011, 0014, 0015, 0018. No spec changed. Commit `2b8a67f`; gate green. Review request:
  [wiki6 review](../backlog/archive/2026-10-17-spec-writer-architect-wiki6-index-and-how-we-know-review.md).
  - **Next:** architect review of `lane/wiki6`.
- **2026-10-17 — `lane/wiki6` reviewed (architect, on the lane at `b2aa52d`; `main` `407758a` already merged): accept
  with fixes.** Every number checked against its source at the same strength: 28 643 calls in ten families (S1e
  entry) and 18 800 in eight, none stopped, the guard-stop failure shown at the S1f review; 40 655 events in 40 logs
  (plan index, 0037); 1 526 `[I]` against 2 531 `[C]` (§ TL;DR); 600 seeds and 0 of 52 200 windows, the Acts I, II,
  IV, V enumeration as a bound and Act III as a sample (inventory § 2.6 `lane/rbs4` block, drlg/0008 H5e (a));
  7 shrines and 5 wells against 50 operates and the floor of 20 (plan 0041 P2 review ruling 1); the seed-invariance
  rule (plan 0041 P2 amendment) and Sanctuary's draw taking the chaining minimum (ruling 5); ADR-0008, 0011, 0014 and
  0015 restated without overreach; the open-plan wording matches the plan index but for 0044. Gate green.
  **Fixes (6), applied on the lane:**
  (1) *stale cross-reference:* wiki/README's 0044 bullet said the two-client run waits until the port is shown
  closed; the owner's `ufw` check was recorded on 2026-10-17 ([plan 0044 log](done/0044-multiplayer-branches.md#implementation-log),
  `78b96a9`), so it now waits only for two free slots. The plan index row of 0044 updated likewise (architect's file).
  (2) *stale cross-reference:* how-we-know's two-client section gains the met condition and the per-session re-read.
  (3) *overclaim:* "a bound: a static argument plus an exhaustive scan" made every d-none ruling need a scan; most rest
  on the static argument alone, so the scan is now "where the argument alone leaves cases open".
  (4) *overclaim:* "inputs can be random, so each branch is driven by at least one case" stated as a consequence what
  ADR-0015 (4) sets as a requirement; reworded as a requirement.
  (5) *omission:* ADR-0015 (5)'s self-modifying code added to what emulation cannot confirm.
  (6) *omission:* the sweep's blocked reasons gain the plan 0032 owner addendum (`d-0032`, § Classes).
  Request closed; ledger rows in [metrics](metrics.md) (usage "—").
  - **Next:** merge `lane/wiki6`.

- **2026-10-17 — H7a (`lifecycle`) started; stopped early for a machine shutdown (reverser, `lane/h7a`, harness slot 2).**
  Not done; no review request, no finding section and no inventory § 2.6 entry yet. Run id **run:2026-10-17-h7a-lifecycle**,
  logs `workspace/logs/rooms/h7a-*.log`, manifest `workspace/logs/h7a-lifecycle-manifest.sha256` (logger
  `tools/gdb/rooms.gdb` unchanged, `726e3453…`; save `ObjNova` `d54d5dc3…`).
  **Done so far.**
  - *Recipe (b), offline geometry* (`tools/townfollow_geom.py scan`, new): per act, the town's free cells under mask
    `0x3C01`, the openings onto other levels and, for every pair of outside cells next to an opening (within the
    100-sub-tile window), shortest distance with and without town cells (4- and 8-connected). On the partial scans
    (`dev-townfollow-geom-h7a-partial3.txt`, 80 layouts from the kept logs; the full run was stopped at the shutdown,
    partial kept as `…partial4.txt`): **0 door pairs with a strictly shorter or equal-length route through a town
    cell**, in every town seen (Rogue Encampment 34 layouts with the Blood Moor logged, Lut Gholein 7, Kurast Docks 3,
    Harrogath 2). The camp's interior (≈14 900 free cells) touches the Blood Moor only at its 15–17-cell gate (other
    openings are 1-cell or small separate pockets), so a Blood Moor route never gains by entering it. Points to (b) being
    a shortfall; the full scan must finish first. `partial1/2` are development outputs (acts not separated: wrong).
  - *Recipe (c), static:* withdrawn on reading. Monsters teleport with skill 184 (`MonTeleport`, `srvdofunc` 98 →
    0x005CCC80, no town test itself). The unique mod's AI `0x005B11F0` (the only reader of AI flag `0x20`) refuses a
    point whose room is a town room (0x005B133C); the Zakarum priests' AI (0x005F72D0) checks the point through
    `0x005FD470`, which for skill 184 refuses a town room (0x005FD59C). Unfollowed: `UberIzual` (no town in its levels)
    and 154 register-skill calls of `0x005DEAD0`. Draft text in the lane scratch is lost at shutdown: rewrite from these
    anchors; kept outputs `workspace/logs/sweep-h7a-*.txt`; tables via `tools/sweep_h7a.py skills`. Seven new `I`
    symbols already in `re/symbols.csv`.
  - *The `0x400` drop:* new session kind `rec400` in `tools/rooms_sessions.py` (visits the rooms of saved `0x400` records).
    Sessions h-barb (4031), h-barb2 (4033), h-barb3 (4034, killed at the shutdown during its cycle-2 return; partial log
    kept and part of the record up to its last line). **4 records** (class 522 `act5barb1`, flags `0x540`, alignment 2,
    mode 2, `+0xD0` 8), **4 restores, all dropped with no creation** (`tools/sweep_h7a.py rec400`). `rooms.py check`:
    h-barb 0 mismatches / 96 414 checks, h-barb2 0 / 209 891; h-barb3 not checked yet. h-barb had one wanderer gate draw
    pass (level 111, `+0x78` = 1, `MonWndr` 0: no roll, but the case does not separate the two tests).
  **Left:** rerun the full geometry scan (≈1 h, under `MemoryMax=4G`); `rooms.py check` on h-barb3; write drlg/0009
  § 11.3 (geometry, (c), the drop: alignment-2 half only, alignment 1 unreached), the experiments record, inventory
  § 2.6 entry (pending review), the review request and the spec-writer entry. **Gotchas:** `CB` lines of
  `tools/gdb/collision.py` have no `z`/`lid` (now skipped); towns of different acts share coordinates (cells keyed by
  act); the Frigid Highlands arrival is (3764, 5094) on every seed tried.
- **2026-10-18 — H7a (`lifecycle`) done; review requested (reverser, `lane/h7a`, harness slot 2).** Resumed from the
  entry above; `main` (`c0c99f6`) merged first. Run **run:2026-10-17-h7a-lifecycle**
  ([drlg/0009 § 11.3](../findings/drlg/0009-room-lifecycle.md#113-plan-0038-batch-h7a-run2026-10-17-h7a-lifecycle),
  [experiments](../findings/drlg/experiments.md#run2026-10-17-h7a-lifecycle)); manifest
  `workspace/logs/h7a-lifecycle-manifest.sha256` (logs, check outputs, geometry and scan outputs). No new session
  today: the three sessions of 2026-10-17 are the record.
  - **Checks:** `rooms.py check` on h-barb, h-barb2, h-barb3: **4 mismatches / 675 849 checks** (h-barb 0 / 96 414,
    h-barb2 0 / 209 891, h-barb3 4 / 369 544). The 4 are one kind: the monster record's `+0xC4` carries bit `0x2000`
    that the save-test line lacked (record copied at 0x00542498, after the state and timer removal; open question).
  - **Raised:** the `0x400` drop, alignment-2 half (4 records, no creation, no game-seed draw), raised in part
    (alignment 1 unreached); the expired-item drop at the restore (5 records, h-barb3), not in § 11's list.
  - **Corrected (reading):** the expiry sweep `0x00542AC0` runs at `frame % 1500 = 0` from 0x0052D310, not every 20
    frames.
  - **Town-follow:** recipe (b) a recorded shortfall. The full geometry scan (`townfollow_geom.py scan`, 568 logs, 106
    layouts, ≈40 min under `MemoryMax=4G`) gives 0 shorter or tied routes through a town; each town's interior meets its
    neighbour at one gate. Recipe (c) withdrawn on the static read. Recount at the resume: `MonAiUseSkill` has 171
    calls, 159 with the skill in a register, 152 of them outside the two AIs read (the checkpoint said 154).
  - **Tools:** `townfollow_geom.py summary` (new mode, per-town table of a scan output); `sweep_h7a.py`,
    `rooms_sessions.py` `rec400` unchanged since the checkpoint.
  - **Backlog:** review request
    [2026-10-18-reverser-architect-review-h7a-lifecycle](../backlog/archive/2026-10-18-reverser-architect-review-h7a-lifecycle.md);
    spec-writer entry
    [2026-10-18-reverser-spec-writer-h7a-lifecycle-spec-updates](../backlog/archive/2026-10-18-reverser-spec-writer-h7a-lifecycle-spec-updates.md);
    the `lane/rbs4` static-remainders entry closed ((1), (2) answered; (3) deferred).
  - **Inventory:** § 2.6 entry (pending review), no row moves, totals unchanged at 1 526.
  - **Left:** the alignment-1 `0x400` record, the `+0xC4` bit-`0x2000` writer (a breakpoint at 0x0064C08B), the
    unfollowed 152 register-skill calls and the § 11.2 optional counts (the closed `lane/rbs4` entry's (3)).
- **2026-10-18 — H7a (`lifecycle`) review (architect, `lane/h7a` at `36e34dd`, `main` `c0c99f6` merged): accept with
  fixes.** Read: [drlg/0009 § 11.3](../findings/drlg/0009-room-lifecycle.md#113-plan-0038-batch-h7a-run2026-10-17-h7a-lifecycle)
  and its open questions, the [experiments record](../findings/drlg/experiments.md#run2026-10-17-h7a-lifecycle), the
  manifest, inventory § 2.6, the seven new symbols, the spec-writer entry and the closed `lane/rbs4` entry. Anchors checked
  in the pinned `Game.exe` with r2: 0x0052D310 (`mov ecx, 0x5DC; idiv; test edx` then 0x00558B90 and 0x00542AC0 for
  `esi` 0..4), 0x0052D96C (the call), 0x00542AF0–0x00542AFF (expiry non-zero and `frame > expiry`), 0x00542498 (the
  record's `+0xC4` read), 0x005425F7–0x0054260B (`0x400`, `0x100`, sign of `al`), 0x0064C07E–0x0064C08B (the
  `0x2000` store after 0x0061AB60), 0x005B132E–0x005B133C and 0x005FD58C–0x005FD5A9 (room at the point, `RoomIsTown`,
  then mask `0x3C01`). The geometry counts recomputed from the kept summary (pairs 93 944 and 94 124, 43 camp layouts
  with the Blood Moor, 21 with a second run); the manifest checks 23 / 23 after fix 1; symbols: no duplicate address or
  name; gate green.
  - **Ruling (a), the 4 mismatches: accepted as explained.** Each differs from its save-test line by exactly `0x2000` in
    `+0xC4` (`0x300200E`/`0x300000E`, `0x8200E`/`0x8000E`), the record reads `+0xC4` at 0x00542498 after the state and
    timer removal, and the restore does not copy the bit back. The `[C]` covers only "the record's `+0xC4` is the unit's
    value at 0x00542498, not at the save test"; which call sets the bit stays an open question (the breakpoint at
    0x0064C08B is not needed before the spec update). The checker keeps the exact comparison, so a later run reports
    them the same way.
  - **Ruling (b), the sweep period: the correction stands, as `[I]`.** The reading is direct (one `idiv` by 1 500, one
    `test edx`), and the run excludes the 20-frame reading (five records still present at frame 19 158 with expiries
    18 720 and 18 324) without confirming 1 500, since no sweep pass fell between an expiry and its restore. `[I]` is
    the right tag; the source of the old "20" was the quest-timer tick 0x00543E10 at `frame % 20` beside it in § 1.
  - **Ruling (c), recipe (b): the shortfall is accepted on the sample.** The text already scopes it (106 kept layouts,
    not every map seed; shortest routes only), and the per-town gate structure explains the zero rather than just
    counting it. The town-follow case stays a named shortfall of plan 0040 Phase 2; no further harness batch for it in
    plan 0038. Recipe (c)'s withdrawal stands on the two AIs read; the 152 register-skill calls are an unfollowed
    remainder, not a route.
  - **Raises accepted:** the `0x400` drop's alignment-2 half `[C]` (raised in part; no creation and an unchanged game
    seed, which a wrong reading could not match by chance), the expired-item drop at the restore `[C]` (5 records).
    No inventory row moves; totals unchanged at **1 526** (static 567, harness 532, c-emu 0, blocked 415, deferred 2,
    raised 10), against `main` `c0c99f6`.
  - **Fixes (made here):** (1) *other:* the manifest mixed two path bases (21 lines relative to `workspace/logs/`, 2
    with a `workspace/logs/` prefix), so `sha256sum -c` failed from either directory; normalised, and the record says
    where to run it. (2) *tool not kept:* the record cited `townfollow_geom.py` `86e98cc4…`, the scan's revision; the
    `summary` mode behind the per-town table is `eec3d7c6…` (additions only); both now cited. (3) *omission:* the
    `0x400` alignment-1 half and the unfollowed static counts (152 register-skill calls, 9 `MonAiPathOverride`, 19
    `UnitTeleport`) added to drlg/0009's open questions, out of plan 0038. (4) *other:* the `lane/rbs4` entry's
    resolution said "(3) deferred" with no home; now "out of plan 0038", kept under drlg/0009's open questions, and the
    log's "Left" line no longer points at the closed entry. Status lines (drlg/0009 header, the town-follow open
    question, inventory § 2.6) set to accepted.
  - **Ledger:** 4 fixes: tool not kept 1, omission 1, other 2. Rule 11 of the reverser's review-fixes recurred
    (fix 4) and rule 6 gains the manifest check (fix 1); both cite this review.
  - **Backlog:** review request closed; the spec-writer entry
    [2026-10-18-reverser-spec-writer-h7a-lifecycle-spec-updates](../backlog/archive/2026-10-18-reverser-spec-writer-h7a-lifecycle-spec-updates.md)
    released.
  - **Next:** merge `lane/h7a`; the spec-writer updates drlg/lifecycle from the released entry.
- **2026-10-19 — H5b (`objects`) started; stopped early at the usage limit (reverser, `lane/h5b`, harness slot 1).**
  Resume note. run:2026-10-19-h5b-objects, nothing filed yet: no finding section, run record, inventory entry or review
  request.
  - **Tools (committed, no claim rests on them yet):**
    - `tools/gdb/objects.py` gains trap lines `TF`/`TFQ` (OBJ_TrapFire and its queue call), `TE0` (OBJ_TrapEvent) and
      `TT0`/`TTX` (the trap function's entry and return), plus `f` (frame) on `OO0`.
    - `tools/gdb/objects-h5b.gdb` is objects.gdb plus vendors.py, so objop, wpchain and npc get the OBJS lines.
    - `tools/objects.py` gains the trap chain model (frame + 35, the OBJ_TrapEvent remap, the fires of
      OBJTRAP_ObjectCreate, MonsterSpawn's one draw), OperateFn 26/48/68 models, windows inside no-draw operates,
      and counters for door marks, size-0 objects and 0x27 rect tests. The old 29 logs still give 150 338 checks,
      0 mismatches.
    - `tools/d2pilot.py` gains `--loot-fns` and `--loot-trap`.
    - New `tools/h5b_sessions.py` (sessions cata, jail, jail2, cave, cata2, cotd, arcane, flayer, harro, tower; built-in
      watchdog) and `tools/sweep_h5b.py` (`static`, `logs`).
  - **Logs kept** (`workspace/logs/h5b/`, save ObjNova `d54d5dc3…`):
    - `run-2026-10-19-h5b-s1-3901-cata.log` (Catacombs 2, complete). It was logged before the TE0 room fix; the
      checker falls back to the unit's level.
    - `…-3902-jail.log` (Jail 1–2), stopped mid-session at the limit. Keep it as a record or dev log.
  - **Found, not yet written up (all need the finding text):**
    - (a) OBJ_TrapEvent (0x005817A0) remaps the trap type to g_ObjTrapFns[2]: type 8 in levels ≥ 75, type 3 in
      levels < 40 other than 25, types 1 and 4 in levels < 40. The cata log has one case: type 4 in level 35 ran
      0x005824B0.
    - (b) OBJTRAP_ObjectCreate makes class 162, then class **160** at x+1 when that is still in the room, and sets
      sparkle 2 on both. objects/0001 § 13.6 says 162 twice; this needs a correction.
    - (c) The old 29 logs already hold 514 WHTest rect tests that returned 0x27 unmasked, all predicted. That
      contradicts the "not reached" of drlg/0005 § 14 and collision row 27, so the row is raisable.
    - (d) The same logs hold 13 compared door 0x400 marks (classes 13 and 14, no BlocksVis, no BlockMissile). No stock
      door has BlockMissile without BlocksVis, so the 0x804 half is a d-none candidate (collision 37, objects 23).
    - (e) No ObjGroup shrine member has Orientation 2, and OBJ_PlaceByOrientation's only caller is the shrine handler,
      so objects 20 is a d-none candidate (`sweep_h5b.py static`).
    - (f) Class 523 (size 0, HasCollision) stands in Harrogath's townwest.ds1. The `harro` session covers collision 39.
    - (g) cata reached one handler-1 follower walk after a class of another size (objects 13, 51).
    - (h) Flayer Dungeon (shrine group 66, ObjPrb 80, no health member) is the target for the forced conversion and
      the caps.
  - **Left:** run cata2, jail2, cave, cotd, arcane, flayer, harro and tower
    (`python3 -I tools/h5b_sessions.py run --slot 1 --tag h5b --saves workspace/scratch-h5b/saves --run
    run-2026-10-19-h5b <s>`). Then the checker over all logs, the finding sections (objects/0001, drlg/0005), the run
    record in `findings/objects/experiments.md`, the manifest, inventory § 2.6, the symbols, the review request and the
    spec-writer entry.
  - **Gotchas:**
    - An object's room is its static path `+0x2C` → `+0x00`; `uroom()` returns 0 for objects.
    - `explore` ends when the level is done, and `--persist` does not continue it.
    - Bookshelves were created but not looted, so jail2 adds objop.
  - Slot 1 stopped, saves restored, no background process left.
- **2026-10-20 — H5b (`objects`) done; review requested (reverser, `lane/h5b`, harness slot 1).** Resumed from the
  entry above. Run **run:2026-10-19-h5b-objects**
  ([objects/0001 § Plan 0038 batch H5b](../findings/objects/0001-object-population.md#plan-0038-batch-h5b-run2026-10-19-h5b-objects),
  [drlg/0005 § Plan 0038 batch H5b](../findings/drlg/0005-collision.md#plan-0038-batch-h5b-run2026-10-19-h5b-objects),
  [experiments](../findings/objects/experiments.md#run2026-10-19-h5b-objects)); manifest
  `workspace/logs/h5b-manifest.sha256` (85 lines: logs, check and sweep outputs, the 29 + 7 older logs re-checked).
  - **Sessions:** 20 today (cata2, jail2, cave, cotd, jail3, cave2, cotd2, flayer, tower, harro, arcane, traps1, cave3,
    flayer2, flayer3, ice, traps2, cave4, traps3, traps4) plus the 2 of 2026-10-19: 22 logs.
  - **Checks:** `objects.py check` on the 22 logs: **234 315 checks, 1 failure** (a logger error in the cave log, no
    model mismatch); the 29 logs of run:2026-10-15-objects: 150 314, 0 mismatches; `collision.py check` on
    run:2026-10-14-collision: 0 mismatches.
  - **Raised (10 rows):** collision 27, 39; objects 13, 16, 17, 40, 45, 50, 51, 52.
  - **Raised in part (11):** collision 37; objects 3, 4, 15, 23, 26, 27, 36, 38, 41, 42 (remainders in the finding).
  - **Shortfall (7):** objects 6, 19, 20, 35, 39, 46, 49. Proposed d-none: objects 20, the `0x804` halves of collision
    37 and objects 23, objects 38's PreOperate half (inventory § 2.6 entry, pending review).
  - **Corrected:** objects/0001 § 13.6, the second trap fire is class 160. New readings: `OBJ_TrapEvent`'s level remap
    (`[I]`, one case `[C]`); the theme table's enabled flag (theme 3 drawn 4 times, no run).
  - **Tools:** `objects.py` (theme enable flag, monster-creating InitFns as oracles, counters), `collision.py`
    (near lists after a DRLG room's re-activation), `d2pilot.py objop` (`--obj-mem`, `--trap-types`, `--goal`, status
    lines), `h5b_sessions.py` (sessions, watchdog race). Symbols: 5 trap functions added, 6 raised to `C`.
  - **Backlog:** review request
    [2026-10-20-reverser-architect-review-h5b-objects](../backlog/archive/2026-10-20-reverser-architect-review-h5b-objects.md);
    spec-writer entry
    [2026-10-20-reverser-spec-writer-h5b-objects-spec-updates](../backlog/archive/2026-10-20-reverser-spec-writer-h5b-objects-spec-updates.md).
  - **Left:** trap types 8 and 9, the well cap and the shrine cap's `= 10` half, the class-397 operate (the pilot
    never reached the chest), a window inside a portal-like operate, quest 13's 582 object, `InitFn` 54/55/62/68/69/79.
  - Slot 1 stopped, saves restored (aside removed, harness idle), no background process left.
- **2026-10-20 — Review of `lane/h5b`, batch H5b (`objects`) (architect): accept with fixes.** `main` (`f8de60b`)
  merged first (one conflict, this log, both sides kept; `backlog.py archive` moved nothing; `re/symbols.csv` has no
  duplicate address or name). Re-run under `systemd-run --user --scope -p MemoryMax=4G`: `sha256sum -c
  h5b-manifest.sha256` passes from `workspace/logs/` (85 lines); the tool hashes match the record; `objects.py check`
  on the 22 logs gives the kept `check-h5b.txt` byte for byte (234 315 checks, 1 failure), on the 29 older logs the kept
  `check-old29.txt` up to line order (150 314, 0); `sweep_h5b.py static` and `logs` and `collision.py check` on
  run:2026-10-14-collision (0 mismatches) match. Spot-checks with objdump: `OBJ_TrapEvent`'s three tests
  (`0x005817CB` type 8 and level ≥ 75, `0x00581816` type 3, level < 40 and ≠ 25, `0x00581849` types 1 and 4, level
  < 40), each jumping through `0x00732CF4`, entry 2 of `g_ObjTrapFns` (table read from the image: the ten entries of the
  finding, count 10 at `0x00732D14`); `OBJTRAP_ObjectCreate` passes class `0xA2` then `0xA0`; the four trap functions
  load MonStats 330, 326, 329, 369; `OBJ_TrapFire` queues event 4 at frame `+ 0x23` (`0x00582595`); `g_ObjThemeFns`
  entries 0 and 3 are `{0, 0}`; `UNIT_GetCollMask`'s door branch (`0x806`, else `0x400` or `0x804` by `BlockMissile`);
  `0x00552C32` is the only reference to `0x00550A30`. The six symbols raised to `C` each have the code reading and the
  run's matched entries.
  - **Rulings.** (a) **d-none, all four proposals**: objects 20 (one call site, member `Orientation`, none 2 in 88
    slots), the `0x804` halves of collision 37 and objects 23 (the branch needs a door with `BlocksVis` 0 and
    `BlockMissile` set; none of the 7 has it), objects 38's PreOperate half. Inventory § 2.6. (b) **The near-list change
    in `tools/collision.py` is a model fix with evidence, not fitting**: it was made for a diagnosed failure (a stale
    active room in a neighbour's near list), is conditioned on the same level, DRLG room, rect and an unreused
    pointer, and two simpler variants were rejected by a second test of the same log (line 25087). Re-checked here with
    the pre-fix `collision.py`: the H5b logs give the same 734 unmasked `0x27` results and only flayer3's one mismatch
    more, and the 29 older logs are identical, so collision 27's raise does not rest on the fix and stands. On
    run:2026-10-14-collision the fix fires 3 999 times and changes nothing, so it is not discriminated there; the game's
    unlink stays `[I]` and an open question of drlg/0005 (the free path, `0x0052D240`'s callees), as filed. (c) **The
    cave log is accepted, not re-run**: the failure is a logger read (`MemoryError` at `0x65`, line 22353), not a model
    disagreement; the checker resyncs and the rest of the log matches; no raised claim rests on that log alone (`InitFn`
    57 also in cave2 and cave4). Reported as "1 logger error, 0 model mismatches". (d) **The oracle change is
    accepted**: the nine `InitFn`s create monsters (S4b row 25), which the objects checker does not model, so a creation
    would fail on the room and game seeds. The oracle still counts every `OD` inside it (none for the nine; `InitFn`
    46's 1 306 show the counter live), and the 24 checks it drops are `InitFn` 18's 3 runs in the older logs, which
    matched before; recorded in the experiments record. A scope reduction, not a fit.
  - **Fixes (made here):** (1) *misread:* row 39's bullet listed cave3 among the sessions that created chest 397; cave3
    never activated its room (0 `InitFn` 57 lines); now cave, cave2, cave4. (2) *omission:* row 35 (the 582 quest
    object) was in the ledger's shortfalls with no statement in the finding; a shortfall bullet added to H5b.3.
    (3) *omission:* the record did not say what the oracle change removed or that it keeps the `OD` counter; added,
    with the review's re-run and the pre-fix counterfactual (experiments record, drlg/0005's near-list bullet). The
    d-none wording ("Proposed") set to the ruling in objects/0001 and drlg/0005.
  - **Totals** (inventory § 2.6, § 5, after merging `main`): **static 567, harness 531, c-emu 0, blocked 416** (d-none
    283), **deferred 2, raised 10: 1 526**. H5b: 32 statements (33 filed; 1 to d-none).
  - **Phase 3:** frees no cluster. drlg/collision still waits for H5d, objects for H6e2.
  - **Ledger:** 3 fixes: misread 1, omission 2 ([metrics](metrics.md)).
  - **Backlog:** review request
    [2026-10-20-reverser-architect-review-h5b-objects](../backlog/archive/2026-10-20-reverser-architect-review-h5b-objects.md)
    closed; the spec-writer entry
    [2026-10-20-reverser-spec-writer-h5b-objects-spec-updates](../backlog/archive/2026-10-20-reverser-spec-writer-h5b-objects-spec-updates.md)
    released (it is applied with the objects and drlg/collision Phase 3 rounds, when H6e2 and H5d are accepted).
- **2026-10-20 — Batch order and the 0039 fold (owner decisions, via the orchestrator; architect, `lane/plans45`).**
  (1) The remaining harness batches run **core and enabler first**: H5b (in flight) → H2a → H2b → H2c → H4a → H5d →
  H1b → H1a → H3b, then H6e2 → H6e1 → H6b → H6a → H6c → H6f → H6g; the family rules of
  [inventory § 7](0038-inventory/README.md#7-priority-order) hold. (2) Plan 0039 is closed; its data/excel fold is a
  Phase 3 item of the data/excel cluster (Phase 3 *Order*). The lane H2 queue is in the
  [plans index](README.md#run-order-unattended-queue-set-2026-10-20-plans-00380049).
- **2026-10-20 — Phase 3, the drlg/lifecycle cluster (spec-writer, `lane/p38s5`, from `main` `c4b4539`).** First
  spec-writer item of the 2026-10-20 queue. Two entries: the released H7a spec updates and the `lane/rbs4` town-follow
  and outdoor 7 entry. Each restated statement checked against
  [drlg/0009 § 11.2, § 11.3](../findings/drlg/0009-room-lifecycle.md#113-plan-0038-batch-h7a-run2026-10-17-h7a-lifecycle)
  and the `lane/h7a` review rulings, and drlg/0008's H5e (a) layout bound.
  - **drlg/lifecycle** {C 80, I 73, L 7} → **{C 85, I 75, L 8}**. Raised `[C]` (run:2026-10-17-h7a-lifecycle): the
    `0x400` drop's alignment-2 half (H2 line and a § H bullet), the expired-item drop (H4 line, `[I]` → `[C]`, and a
    bullet), the record's `+0xC4` as read at 0x00542498 (§ G, ruling (a)'s wording). New `[I]`: the 1 500-frame expiry
    sweep from 0x0052D310 in § A (ruling (b); the A1 line annotated), the alignment-1 half on the H2 line, the
    0x0064C040 store of bit `0x2000`. New `[L]`: which call sets that bit. Open questions: town-follow restated from
    § 11.2 and § 11.3 (H7a its route; still a named shortfall of plan 0040 Phase 2), the unreached-branches bullet
    rewritten (the 20-frame sweep struck).
  - **drlg/outdoor** {C 180, I 19, L 2} unchanged: row 7's C5 bullet and its shortfall bullet split by act (no stock
    case in Acts I, II, IV, V by the layout bound, `[I]`; Act III on the 600-seed sample). No inventory row moves.
  - **Wiki:** [levels](../wiki/levels.md) restated (town-follow, expired item, vertex merge); levels, monsters and
    objects `based_on` dates set to 2026-10-20.
  - **Backlog:** both entries closed; review request
    [p38s5 review](../backlog/archive/2026-10-20-spec-writer-architect-p38s5-drlg-lifecycle-review.md).
  - **Next:** architect review of `lane/p38s5`.
- **2026-10-20 — Review of `lane/p38s5`, the drlg/lifecycle cluster (architect): accept with fixes.** `main` merged
  first (clean; `backlog.py archive` moved nothing). Read: the full spec, wiki and plan diff against
  [drlg/0009 § 11.3](../findings/drlg/0009-room-lifecycle.md#113-plan-0038-batch-h7a-run2026-10-17-h7a-lifecycle),
  the `lane/h7a` rulings above and drlg/0008's
  [H5e (a) layout bound](../findings/drlg/0008-outdoor.md#h5e-reachability-a-the-layout-bound-2026-10-17-lanerbs4).
  Tag counts recomputed by script: drlg/lifecycle {C 85, I 75, L 8} (5 raised, 3 new `[I]`, 1 removed, 1 new `[L]`),
  drlg/outdoor unchanged {C 180, I 19, L 2}. Anchors resolve in `re/symbols.csv` (0x005424F0, 0x00541AC0, 0x0052D870,
  0x005421A0, 0x005B11F0, 0x005F72D0, 0x00554EA0, 0x005CA360, 0x0064FAD0, 0x006772C0).
  - **Spot-checks.** The `0x400` bullet matches § 11.3 (3) (4 records, class 522, flags `0x540`, `+0xD0` = 8, no
    creation, seed unchanged; alignment 1 kept `[I]`). The `+0xC4` bullet carries ruling (a)'s wording, and which call
    sets bit `0x2000` sits under *Open questions*. The § A sweep bullet is `[I]` per ruling (b), with the run's
    exclusion of the 20-frame reading and no confirmation of 1 500. The outdoor C5 split follows H5e (a), Act III on the
    sample. The wiki levels paragraphs carry no tags and say "read from the code" where the spec has `[I]`.
  - **Fixes (made here):** (1) *overclaim:* the town-follow open question and the wiki said each town's interior meets
    its neighbour "at one gate"; § 11.3 (1) has one more run of 1 or 2 cells on 21 camp layouts; both scoped.
    (2) *other:* outdoor's *Branches no log reached* bullet rewrapped (two over-long lines). Research-map rows for
    drlg/lifecycle and drlg/outdoor rewritten whole (counts, date, the H7a raises, the Act split).
  - **Ledger:** 2 fixes: overclaim 1, other 1 ([metrics](metrics.md)).
  - **Backlog:** review request
    [p38s5 review](../backlog/archive/2026-10-20-spec-writer-architect-p38s5-drlg-lifecycle-review.md) closed.
- **2026-10-20 — Phase 3, qualification check (spec-writer, `lane/p38s6`, from `main` `0adbb2e`).** No cluster
  qualifies; nothing is re-tagged. Accepted batches: S1a, S1b, S1e, S1f, S2a, S2b, S2c, S3a, S3b, S4a, S4b, H4b, H5a,
  H5c, H5e, H6d, H7a. Every spec whose batches are all among them is already re-tagged: rng/seeds, monsters/README,
  drlg/README and drlg/room-tiles (`lane/p38s`), drlg/outdoor (`lane/p38s2`), drlg/maze, drlg/preset and drlg/warps
  (`lane/p38s3`), data/calc and rng/README (`lane/p38s4`), drlg/lifecycle (`lane/p38s5`); player/README has no tags.
  Checked against the *Batch* column of each per-spec inventory file and inventory § 5 with the § 2.6 moves. The open
  spec-writer entries for done clusters hold only parts for waiting ones (S4a (b) collision; S4b (a) objects, (d)
  collision, (f) items/tc).
  - **Waiting** (missing batches): items/tc H2a, H2b, H2c; items/quality H2a; items/affixes H2b; items/uniques-sets
    H2b, H1a (us 21); items/properties H2b, H2c; items/sockets-runewords H2b, H6b; items/cube H6a; items/vendors H6c;
    items/quest-drops H4a, H6e1, H6e2; save/d2s H1a, H1b; data/excel H3b (and the plan 0039 fold); data/strings and
    data/README H3b; monsters/pool, monsters/special and monsters/stats H4a; monsters/spawn H4a, H5d; hirelings H1a,
    H1b, H6f; player/creation H1a, H6g; drlg/collision H5b, H5d; objects H5b, H6e2.
  - **Backlog:** unchanged; no review request (no spec changed).
  - **Next:** the next Phase 3 round after H5b's review (objects still waits for H6e2, drlg/collision for H5d), then per
    cluster as H2a–H2c, H4a and the rest are accepted.
- **2026-10-20 — Batch H2a paused (reverser, `lane/h2a`): harness part done, write-up left; resume note.** Slot 2
  was yielded to plan 0044 Phase 2 at the orchestrator's request. Slot 2 is stopped, its saves directory restored to
  empty (`aside: none`), no driver or gdb left.
  - **Done:** run:2026-10-20-sweep-items-tc, 12 sessions on slot 2, recorded in
    [findings/items/experiments.md](../findings/items/experiments.md#run2026-10-20-sweep-items-tc) with the logger
    (`tools/gdb/tc-h2a.gdb`), driver (`tools/h2a_sessions.py`), pilot `corpse` command, recipe `h2afind.json`, checker
    `tools/sweep_h2a.py` (+ 9 tests), the `tools/quality.py` clamp counterfactual keys and `tools/tc.py`'s skip of the
    H2a tags. Logs, manifest and every check output are in `workspace/logs/h2a/` (`check/`). All checkers 0
    mismatches: `sweep_h2a.py logs` 0 bad, `tc.py replay` 873/873, `quality.py` 720/720, `uniques.py` 1022/1022.
  - **Proposed row states (lane's reading, for the write-up):** tc 1, 2, 11, 34 (2), 37, 45, 47, 59, 71 raised; tc 22
    raised in part (bit 17: 113 skips, collision: 2 skips; `bonewall` fatal unreached); tc 60 raised in part
    (gold find 202 products, `mul=` 1 product; the type-equivalence half is d-none: `gld` is the only item record of
    or equivalent to type 4; signedness unseparated by positive values); tc 70 raised in part (types 2 and 3; type 1
    and the outside-1–3 half unreached); quality 20 raised in part (owner from the AI block for 363/352/271, 130
    rolls; gone owner and killer type ≥ 2: 0 cases in 8 753 rolls); quality 22 and 23 raised (the D6 clamp acts in 667
    rolls of the S2a set and the H2a logs; no clamp breaks 138, clamp after the ratio breaks 206). That is 13 raised and
    4 raised in part of 17 rows (18 statements with tc 34's two).
  - **Left (static, no slot needed):** the "Plan 0038 batch H2a" sections of items/0001 and items/0002 with the row
    ledger and anchors; the rule-12 carries into 0001 § S2a tc 34 and the TCP/IP open question, and into 0002 § Answer
    (the clamp "never acted"), § magic-find unexercised parts and the clamp open question; `re/symbols.csv` confidence
    (MonDeathDrop, MonDeathEvent, MonDropNoNoDrop, CorpseFindItem, DropGoldFind I → C); inventory § 2.6 entry; the
    review request to the architect; gate. No further session is needed for the filed rows; an optional champion kill
    (an `Act N Citem` `mul=` gold) would add `mul=` cases.
- **2026-10-20 — Batch H2a filed (reverser, `lane/h2a`, write-up resumed from the note above; `main` `5a7feb3`
  merged).** Static only: no slot, no Ghidra. Every count re-taken from the kept logs and check outputs in
  `workspace/logs/h2a/` (manifest passes), not from the note.
  - **Ledger** ([items/0001 § Plan 0038 batch H2a](../findings/items/0001-tc-resolution.md#plan-0038-batch-h2a-2026-10-20),
    [items/0002 § Plan 0038 batch H2a](../findings/items/0002-quality-roll.md#plan-0038-batch-h2a-2026-10-20)):
    15 rows, 17 statements: **12 raised** (tc 1, 2, 11, 34 L361, 37, 45, 47, 59, 71; quality 22 ×2, 23), **5 raised in
    part** (tc 22, 34 L388, 60, 70; quality 20), 0 shortfall. The note's "13 raised, 4 in part of 17 rows (18
    statements)" miscounted: tc 34's L388 carries the `Picks = 0` half (d-none, row 13), so it is in part (rule 8).
  - **New checks** (additions only; run record addendum): `quality.py` counterfactual `before-mf` (D6 before magic find
    breaks 9 + 129 rolls, which raises quality 23's MF-before-minimum half), `sweep_h2a.py goldtypes` (only `gld` is of
    type 4 by any route: tc 60's equivalence half d-none), and a per-log clamp split (the clamp acts in the affixes,
    uniques, props and items-chain runs, never in the plan 0010 runs).
  - **Corrections carried (rule 12):** items/0002 Answer, § 4 order, § 7, the Reproduction note, the clamp open question
    and the header (the clamp "never acted" → acts in 667 rolls, decides 138); items/0001 header, Answer (negative-Picks
    stop), Functions table, § 3 (bit 17), § 8 (gold), S2a tc 34 and tc 51, and the TCP/IP `/players` open question
    (answered).
  - **Symbols:** `MonDeathEvent`, `MonDeathDrop`, `MonDropNoNoDrop`, `CorpseFindItem`, `DropGoldFind` I → C.
  - **Inventory:** [§ 2.6 H2a](0038-inventory/README.md#26-moves-made-by-the-batch-reviews), no class moves; totals
    as after the H5b review (static 567, harness 531, blocked 416, deferred 2, raised 10: 1 526).
  - **Backlog:** review request
    [2026-10-20-reverser-architect-review-h2a-items-tc-quality](../backlog/archive/2026-10-20-reverser-architect-review-h2a-items-tc-quality.md);
    spec-writer entry
    [2026-10-20-reverser-spec-writer-h2a-items-tc-quality-spec-updates](../backlog/archive/2026-10-20-reverser-spec-writer-h2a-items-tc-quality-spec-updates.md)
    (to be released with the review).
  - **Next:** architect review of `lane/h2a`; then H2b.
- **2026-10-20 — Review of `lane/h2a`, batch H2a (items: tc and quality; architect): accept with fixes.** `main` merged
  first (already up to date at `5a7feb3`; `backlog.py archive` moved nothing). Read: the plan, inventory, items/0001,
  items/0002, experiments and backlog diffs, the logger, `tools/quality.py`'s diff and `sweep_h2a.py clamp`/`killers`.
  - **Re-run** (from the worktree, `systemd-run --user --scope -p MemoryMax=4G python3 -I …`): `sha256sum -c` passes on
    `items-tc-manifest.sha256` (12 logs), `items-tc-saves.sha256` (from `saves/`), the H6d manifest (19) and the S2a
    manifest (195). `tc.py replay` 873 calls, 873 reproduced, 0 failed (B6 in the three Andariel kills);
    `quality.py check` 720/720; `uniques.py check` 1022/1022; `sweep_h2a.py logs` 0 bad; `clamp` over the H2a logs, the
    193 S2a logs and the two MF-100 logs, `goldtypes` and `static` byte-identical to `check-sweep_h2a.txt`,
    `check-clamp-h2a-r2.txt`, `check-clamp-s2a-r2.txt`, `check-clamp-s2a-mf100-r2.txt`, `check-goldtypes.txt`,
    `check-static.txt`, `check-quality-r2.txt`, `check-uniques.txt`; `test_sweep_h2a.py` 9 OK. The cited check-output
    and tool hashes match the files (`d2pilot.py` `f7e805d9…` is the run's revision, `43df448`; the merge of H5b changed it
    after).
  - **Symbols** (two sources each, spot-checked with objdump and r2 on the pinned image): `call 0x5A6830` at 0x005A7027
    and all 973 `MDD0` returns at 0x005A702C; the dword at 0x006E2260 is 0x005A6FF0 (`MonDeathEvent`, no `call rel32`);
    the dword at 0x007323D0 is 0x005D8780 (`g_SkillDoFuncs` 0x007322B0 + 72 × 4) and all 31 `CFI` return to 0x0056F96A;
    `call 0x5A8000` at 0x005D888F; `call 0x5589A0` at 0x0055AF59 and all 705 `GF0` return to 0x0055AF5E. The five I → C
    stand.
  - **Rulings.** (a) *Row count:* the § 5 row lists 13 tc and 4 quality statements on 15 rows (tc 34 and quality 22 two
    each): 17 statements, 12 raised and 5 in part, as filed; the resume note's 13 + 4 of 18 was its miscount, corrected
    by the lane before filing. (b) *tc 34 (L361), how it is decided:* 0x0055AB35 is the join of every exit of the entry
    scan (the classic path at 0x0055AAD8 and 0x0055AAEB, the expansion loop's exits and fall-through at
    0x0055AB00–0x0055AB33), and the logger's `SEL` there prints misses too, so a reading without the `jge 0x0055AF73`
    at 0x0055AAC4 would log a `SEL` after `NEG roll=1 total=1`; there is none, and the 62 other negative picks each
    show one (the control). The stop's frame end is the same either way, which is why only the missing line decides;
    not by chance (rule 10). Raised. (c) *Rule 8, tc 34 (L388):* the step note carries two claims; the stop half is
    `[C]`, the `Picks = 0` half is tc 13's statement (d-none since S2a), so L388 is raised in part and stays counted as
    H2a (no class move, as the H5b halves). (d) *Clamp correction (rule 12):* carried in items/0002 (header, Answer,
    § 4, § 7, unexercised parts, the plan 0010 run note, open question); the plan 0010 run record in experiments.md
    (its own run, still true) needs none. It was not carried to the specs' open questions or the wiki: fix 1. "Acts"
    counts the rolls with the pre-clamp chance at or below the minimum; the evidence for the raise is the 138 it
    decides. (e) *Tool additions:* `quality.py`'s `clamp_ratio` refactor and `before-mf` key leave the game's roll
    unchanged (`check-quality-r2.txt` = `check-quality.txt`, the uniques check unchanged); `goldtypes` is a full-table
    check. Accepted as additions. `before-mf` breaking the same 9 + 129 as `off` is a result, not a tool fault: it
    still separates "minimum after magic find" from "before". (f) *quality 20, the aborted H6d log:* the 5 hireling
    rolls of `failed/quest-b6-s2-3811-andy-warriv.log` (`QOMF omf=100`, so the owner term is non-zero) count: the log
    is a kept development log (reverser rule 6), hashed in the H6d manifest and in its run list, made by the same logger;
    the session failed on navigation, not on the logger. Per log the 39 are 5 + 3 + 4 + 7 + 7 + 4 + 9 over seven H6d
    logs; without the 5 the raise stands (34 + 6 + 85).
  - **Fixes (made here):** (1) *omission:* the spec-writer entry gained (m)–(o): items/quality's `[L]` clamp open
    question (L638), items/tc's `[L]` `game.type` / TCP/IP `/players` open question (L968–L970) and the wiki items page
    (L177–L179, L220, L542, L548), each contradicted by the corrections. Entry released.
  - **Totals** (once, after the rulings, against `main` `5a7feb3`): unchanged, **static 567, harness 531, c-emu 0,
    blocked 416** (d-none 283, d-edit 73, d-sim 28, d-2c 14, d-owner 10, d-0032 8), **deferred 2, raised 10: 1 526**
    ([§ 2.6](0038-inventory/README.md#26-moves-made-by-the-batch-reviews)); H2a marked done in § 5.
  - **Phase 3 clusters freed:** items/quality (waited on H2a only) is ready for its re-tag round; items/tc still waits
    on H2b and H2c.
  - **Ledger:** 1 fix: omission 1 ([metrics](metrics.md)).
  - **Backlog:** review request
    [h2a review](../backlog/archive/2026-10-20-reverser-architect-review-h2a-items-tc-quality.md) closed; spec-writer entry
    [h2a spec updates](../backlog/archive/2026-10-20-reverser-spec-writer-h2a-items-tc-quality-spec-updates.md) released.
- **2026-10-20 — Phase 3, the items/quality cluster (spec-writer, `lane/p38s7`, from `main` `f32742c`).** The cluster
  waited on H2a only (accepted above). Inputs: the items/quality parts of the released H2a spec-updates entry ((j)–(m)
  and the quality lines of (o)) and the items/quality note of the S2a tc 64 entry ((b), unblocked by S4b's raise in
  items/0001 § 2). Each raise checked against
  [items/0002 § Plan 0038 batch H2a](../findings/items/0002-quality-roll.md#plan-0038-batch-h2a-2026-10-20) and the
  review's rulings (d) and (f). The plan 0049 M3 notes folded by `lane/p49s` are kept as they were.
  - **items/quality** {C 64, I 42, L 2} → **{C 69, I 39, L 1}**. Raised `[C]`: the D6 line and its step note
    (quality 22, "the clamp acts": 667 rolls, decides 138, no unique case), the D4–D7 order note (quality 23). Split:
    M3, a monster killer owned by a player `[C]` (quality 20 in part, 130 rolls), the missing-owner, plain or minion
    killer and type ≥ 2 cases staying `[I]`; C1, the chest tier as `ilvl` `[C]` (S2a (b), run:2026-10-15-objects), its
    consequence for the odds `[I]`. Open questions: the `*Min` clamp `[L]` struck.
  - **Wiki:** [items](../wiki/items.md) step 3 of *One test*, the MF paragraph and the *Quality* line of the untested
    list restated; `based_on` for quality already 2026-10-20.
  - **Waiting** (missing batches): items/tc H2b, H2c; items/affixes H2b; items/uniques-sets H2b, H1a (us 21);
    items/properties H2b, H2c; items/sockets-runewords H2b, H6b; items/cube H6a; items/vendors H6c; items/quest-drops
    H4a, H6e1, H6e2; save/d2s H1a, H1b; data/excel H3b (and the plan 0039 fold); data/strings and data/README H3b;
    monsters/pool, monsters/special and monsters/stats H4a; monsters/spawn H4a, H5d; hirelings H1a, H1b, H6f;
    player/creation H1a, H6g; drlg/collision H5d; objects H6e2.
  - **Backlog:** the H2a spec-updates entry and the S2a tc 64 entry annotated (done in part; their items/tc and objects
    parts wait); review request
    [p38s7 review](../backlog/archive/2026-10-20-spec-writer-architect-p38s7-items-quality-review.md).
  - **Next:** architect review of `lane/p38s7`; items/tc after H2b and H2c.
- **2026-10-20 — Review of `lane/p38s7`, Phase 3 items/quality cluster (spec-writer; architect): accept with fixes.**
  `main` merged first (already up to date at `f32742c`; `backlog.py archive` moved nothing). Read: the spec, wiki,
  backlog and plan diffs against
  [items/0002 § Plan 0038 batch H2a](../findings/items/0002-quality-roll.md#plan-0038-batch-h2a-2026-10-20), the
  `lane/h2a` rulings (d) and (f) and [items/0001 § 2](../findings/items/0001-tc-resolution.md#2-entry-points).
  - **Raises.** D6 line and step note: 667 = 39 + 628, by test rare 622 (37 + 585), set 646 (38 + 608), magic 13
    (2 + 11), decides 138 (9 + 129), 7 199 = 720 + 6 479; the unique minimum reached by none; the plan 0010 runs'
    "no chance near a minimum" kept as scoped (ruling (d)). D4–D7: after D7 206 (7 + 199), before D5 138 (9 + 129).
    M3: 130 rolls (85 + 39 + 6, the 5 `failed/` hireling rolls counted per ruling (f)); remainder `[I]` scoped to the
    8 753 rolls. C1: two sources hold, the code at 0x00585CD2 and run:2026-10-15-objects (59 of 59 `TCR ilvl` = the
    modelled tier, items/0001 § 2 `[C]` since S4b); the consequence for `d` split `[I]`. All stand.
  - **Anchors** spot-checked in `re/symbols.csv`: `ITEMS_DropMagicFind` 0x005585D0, `sub_0058F0D0_MonsterOwner`,
    `sub_00585B90_ObjectChestDrop`; the six cited run ids exist in the experiments files.
  - **Counts** by script over the body, struck text removed: {C 64, I 42, L 2} → {C 69, I 39, L 1} (+3 raised, +1 M3,
    +1 C1 in place with a new `[I]`). The struck clamp open question carries no live tag. The two annotated entries'
    remaining parts (items/tc (a)–(i), (n), the `/players` lines of (o); items/tc § J and objects § J3) are correct.
  - **Fixes (made here):** (1) *overclaim:* wiki step 3 said the clamp decided 138 rolls "in the rare, set and magic
    tests"; the finding splits by test only the rolls that reach the minimum, not the 138: restated. (2) *omission:* the
    wiki's untested *Quality* line names a monster killer with no player owner, but the spec's open questions did not
    list it: the M3 remainder (no player owner; an object or missile killer) added to the `[L]` *Not exercised* bullet
    (no count change) and the object or missile killer to the wiki line.
  - **Research map:** the items/quality row rewritten whole (C 69 / I 39 / L 1, the H2a raises).
  - **Ledger:** 2 fixes: overclaim 1, omission 1 ([metrics](metrics.md)).
  - **Backlog:** review request
    [p38s7 review](../backlog/archive/2026-10-20-spec-writer-architect-p38s7-items-quality-review.md) closed; the H2a
    spec-updates and S2a tc 64 entries stay open for items/tc and objects.
- **2026-10-20 — Batch H2b resumed (reverser, `lane/h2b`, head `db28349`).** The lane's first agent stopped after
  three tools-only checkpoints (`bd65fae`, `67d28a5`, `db28349`: logger `tools/gdb/h2b.py` and `items-h2b.gdb`,
  `tools/h2b_sessions.py`, `tools/sweep_h2b.py` with 10 tests, cube recipes `h2bjewel`/`h2bthrow`). Kept sessions so
  far (slot 2, `workspace/logs/h2b/`): `classic-a`, `throw`, `jewel`, `hell-a` (death at `/players 8` after 147 s, kept
  and recorded as a death), `hell-b` (`/players 1`, cut off; to be checked before use), two dev logs. Still to do:
  sessions hell-c, hell-d, classic-jail, classic-cat (cap 20); the full check set; the five findings' ledgers, run
  record, manifest, § 2.6 entry, review request, spec-writer entry and symbol raises. Nothing below this note's
  checkpoint is claimed yet.
- **2026-10-20 — Batch H2b paused at the owner's request (reverser, `lane/h2b`).** Slot 2 stopped and its saves
  directory restored (empty, no aside); no game, driver, pilot or gdb of the lane left running.
  - **Sessions so far** (run:2026-10-20-sweep-items-chain, `workspace/logs/h2b/`, 16 launches of the 20 allowed):
    kept 12 logs (`items-chain-run.lst`, `items-chain-manifest.sha256` `eddc187f…`, `sha256sum -c` from
    `workspace/logs/h2b`): `classic-a`, `-b`, `-c` (classic Normal outdoor sweeps, 163, 177 and 201 creations),
    `classic-jail` (pilot stalled in the Jail after 69 s, 23 creations), `classic-cat` (no cast in the Catacombs, 0
    creations), `hell-a` (died at `/players 8` after 147 s), `hell-c`, `hell-d` (Eldritch at `/players 1`, 34 and 63
    creations), `jewel` (17 transmutes), `throw` (9 transmutes), and the new expansion Normal sweeps `exp-cold` and
    `exp-stony`. Development logs in `dev/` (`items-chain-dev-manifest.sha256` `ced144d2…`): `dev1` classic-a, `dev2` and
    `dev3` hell-b (both cut off; `dev3` by the first agent's stop), and **`dev4` classic-d (map seed 3914): gdb aborted
    with `i387-tdep.c:1057: internal-error: i387_supply_xsave: Assertion 'regs != NULL' failed` (log line 1200), a gdb
    18.1 thread race under Wine; a tool failure, not a model mismatch.** No kept log has `internal-error:`.
  - **Checks so far** (spot runs, outputs not kept yet): `sweep_h2b.py logs` 0 bad on every kept log; `uniques.py`
    203/203, `quality.py` 185/185 and `tc.py replay` 181/181 on the first four logs; `cube.py check` of
    run:2026-10-15-cube's two rare logs reproduces (4 rare jewels at count 3, 10 other rares).
  - **Tools since the resume note:** `sweep_h2b.py` `tors` rule reads `SOKM` (the tors test at 0x00556BEC is reached only
    past `ItemMaxSockets` > 0, 0x00556B96) with an expansion control, 3 new tests (13 OK); `h2b_sessions.py` sessions
    `exp-cold`, `exp-stony`. Readings re-checked with objdump: the `ItemCreate` record-seed branch 0x00558E47, `GS1`
    after the `ItemSeedInit` call 0x0055532A, the `SetSockets` switch table 0x0062BDDC, the jewel branch 0x005C1C74,
    C5a/R1 0x0065E62D/0x0065E71D, `MBF` 0x0055667D, the classic `version ≥ 100` refusal 0x00558DBC (`game+0x70` = 0),
    the type-11 call (exact type test at 0x00557DE7).
  - **Early results (to be re-taken from kept check outputs):** classic body armour now reached the tors test 5 times
    (`classic-b` 1, `classic-c` 4, all q 2) with no socket draw (prop 20); `throw`: 9 of 9 rare → magic → superior,
    18 empty name scans, 11 empty magic candidate lists; `jewel`: 9 at count 3, 8 at 4.
  - **Left:** re-run map seed 3914 (or another classic outdoor session) for the gdb crash; the full check set
    (`scratchpad/h2b2/checks.sh`, which now refuses a kept log with `internal-error:`); the five findings' ledgers
    (drafts for items/0001, 0004 and 0005 in `scratchpad/h2b2/s000N.md`, the first agent's in `sec000N.md`, all to be
    re-counted from the kept outputs); run record and manifest; corrections (rule 12) into items/0005 § 5 (tests (a)
    "refused no row in the run"), § 6, items/0006 § 6 (sockets), items/0007 § 7, items/0001 § 8; inventory § 2.6;
    symbol raises; review request; spec-writer entry.
- **2026-10-20 — Batch H2b filed (reverser, `lane/h2b`, resumed from the pause note above).** One more launch on slot
  2: classic-d re-run on map seed 3914 (123 creations, Black Marsh explored after 305 s, no `internal-error:`), then
  slot 2 stopped and its saves directory restored (empty, no aside). `grep -l "internal-error:"` over the kept and dev
  logs: only `dev/dev4` (the aborted classic-d). 17 launches of the 20 allowed, 13 kept logs. Every count re-taken from
  the full check set in `workspace/logs/h2b/check/` (manifest passes), not from the note or the drafts.
  - **Ledger** ([items/0001](../findings/items/0001-tc-resolution.md#plan-0038-batch-h2b-2026-10-20),
    [0004](../findings/items/0004-uniques-sets.md#plan-0038-batch-h2b-2026-10-20),
    [0005](../findings/items/0005-affixes.md#plan-0038-batch-h2b-2026-10-20),
    [0006](../findings/items/0006-properties.md#plan-0038-batch-h2b-2026-10-20),
    [0007](../findings/items/0007-sockets-runewords.md#plan-0038-batch-h2b-2026-10-20)): 18 rows, 25 statements:
    **14 raised** (tc 68; us 9, 39; aff 5, 13 ×2, 17, 19 ×2, 21 ×3; prop 20 ×2), **5 raised in part** (tc 58, us 7,
    us 35, aff 24, sock 42), **1 shortfall** (prop 24), **5 reclassified d-none** (us 10, prop 7 ×3, aff 20). S2c's
    sock 44 piece met in part; the H2c companion found no func 12, 23 or 24 slot.
  - **Checks** (run:2026-10-20-sweep-items-chain): `sweep_h2b.py logs` 0 bad, `tc.py replay` 1 118/1 118,
    `items_chain.py both` and `uniques.py` 1 043/1 043, `quality.py` 1 022/1 022, `cube.py` 26/26 and the 2026-10-15
    rare logs 14/14, 13 tests OK.
  - **Corrections carried (rule 12):** items/0005 § 3 tests (a) and the Phase 2 not-reached list; items/0004 Answer and
    not-reached list; items/0007 Answer and § 7's clamp bullets; items/0006 § 6 tors; items/0001 § 8 item seed.
  - **Symbols:** `sub_00558D90_ItemCreate`, `sub_0055A550_DropCreateItem` I → C.
  - **Inventory:** [§ 2.6 H2b](0038-inventory/README.md#26-moves-made-by-the-batch-reviews), three rows (5 statements)
    proposed a-run → d-none; totals against `main` `9ef5f84`: static 567, harness 526, blocked 414 (d-none 288),
    deferred 2, raised 17: 1 526. `main` is not merged into the lane (the merge was refused by the session's permission
    layer); the review merges it.
  - **Backlog:** review request
    [2026-10-20-reverser-architect-review-h2b-items-chain](../backlog/archive/2026-10-20-reverser-architect-review-h2b-items-chain.md);
    spec-writer entry
    [2026-10-20-reverser-spec-writer-h2b-items-chain-spec-updates](../backlog/archive/2026-10-20-reverser-spec-writer-h2b-items-chain-spec-updates.md)
    (to be released with the review).
  - **Next:** architect review of `lane/h2b`; then H2c.
- **2026-10-20 — Review of `lane/h2b`, batch H2b (items: affixes, tc, uniques-sets, properties, sockets-runewords;
  architect): accept with fixes (5).** `main` (`9ef5f84`) merged into `lane/h2b` first: one conflict, the end of
  inventory § 2.6 (the plan 0044 Phase 3 block and the H2b block, kept in that order); the plan log merged clean;
  `backlog.py archive` run after it. Read: the plan log entries, the run record, the five findings' H2b sections and
  corrections, the inventory § 2.6 block, `re/symbols.csv`, the backlog entries, and the check outputs.
  - **Re-checked** (worktree, `systemd-run --user --scope -p MemoryMax=4G`): `sha256sum -c` passes on
    `items-chain-manifest.sha256` (13 logs), `items-chain-saves.sha256` (from `saves/`) and the dev manifest (from
    `dev/`); every cited check-output hash and the tool hashes match the files (`tc.py` `36892d1a…` is the lane's
    revision; `main`'s `f26df35d…` replays the same 1 118 calls with 0 failed, kept as `check/review/`). The tails of
    `check-tc.txt`, `-items_chain`, `-uniques`, `-quality`, `-cube`, `-static`, `-rareboth`, `-tests` agree with the
    record; the per-log sweep is 0 bad in all 13. The ledger recounts to 18 rows, 25 statements (14 + 5 + 1 + 5).
  - **Each raise against a reading it rules out:** us 9, tc 58 and tc 68 by the `GS0`–`GS4` seed model (a record seed
    would show `GS3` and other seeds); us 39 by `GQJ`/`GQX` (any builder step on the game or unit seed would break the
    993/1 043 counts); aff 5 and aff 19 by 21 jewel counts (the general table matches each with odds ≤ 3/8); aff 17 by
    `MBF` after exactly the 9 empty builds of 80; prop 20 by the expansion `tors` control (the draw is unconditional
    past the tors test, 0x00556C0F); aff 24 and us 35 by the logged `{S, 666}` resets. aff 13 and aff 21: the lane's
    control ("candidates at version 101") does not separate C5a/R1 from the rows' version gate; the review's control at
    version 1 with the refusal removed finds 30–37 candidates per side, 0 with it (fix 1). The three d-none moves hold;
    the review added a byte search of the pinned image (no `elx` code).
  - **Rulings.** (a) The three d-none moves accepted (§ 2.6, harness 531 → 526, d-none 283 → 288). (b) prop 20 raised
    as filed. (c) us 7 in part as filed: the fallback reached is not the one the statement names. (d) sock 44's S2c
    piece in part as filed. (e) The rule-12 corrections are in place in items/0001 § 8, 0004 Answer and *Not reached*,
    0005 § 3 and *Not reached*, 0006 § 6, 0007 Answer and § 7. (f) Symbols: the two raises stand; the five candidates
    are raised too (`ItemSeedInit`, `ItemFallbackSuperior`, `ItemRollSockets`, `ItemMaxSockets`, `ITEMS_SetSockets`),
    each by its logged output against a model, with the evidence column moved to the finding that holds the `[C]`
    statement and the Functions tables of items/0002, 0003, 0004, 0006 and rng/0002 updated (fix 3).
  - **Fixes applied (5):** (1, 2) overclaim: aff 13's and aff 21's controls replaced by the version-1 control
    (`check/review/c5a_control.txt`; items/0005, run record *Review checks*). (3) overclaim: sock 42's `[C]` scoped to
    the cap's steps; every one of the 34 requests lay in `1..cap`, so `max(n, 1)` and the clamp of the write join the
    remainder (items/0007 sock 42, the Answer note, § 7's order note, the § 2.6 bullet, the spec-writer entry's (r)).
    (4) under-claim: the five symbols above. (5) other: the dev manifest's path in the run record.
  - **Totals** (recomputed once after the merge, § 2.6): **static 567, harness 526, c-emu awaiting a batch 0, blocked
    414** (d-none 288, d-edit 73, d-sim 28, d-2c 7, d-owner 10, d-0032 8), **deferred 2, raised 17: 1 526.** § 5 marks
    H2b done.
  - **Backlog:** review request
    [2026-10-20-reverser-architect-review-h2b-items-chain](../backlog/archive/2026-10-20-reverser-architect-review-h2b-items-chain.md)
    closed; the spec-writer entry
    [2026-10-20-reverser-spec-writer-h2b-items-chain-spec-updates](../backlog/archive/2026-10-20-reverser-spec-writer-h2b-items-chain-spec-updates.md)
    released (open, for the Phase 3 re-tag of items/tc, uniques-sets, affixes, properties and sockets-runewords).
  - **Next:** H2c (forced), after the H2b merge.
- **2026-10-20 — Phase 3, the items/affixes cluster (spec-writer, `lane/s38h2b`, from `main` `33484f8`).** The cluster
  waited on H2b only (accepted above; S2b, S2c and S1f were accepted earlier; aff 14's level-window remainder is an H6a
  piece, its row counted as S2c). Inputs: the affixes parts of the H2b spec-updates entry ((h)–(n)), the S2b
  corrections entry ((c), (f)), the S2c corrections entry ((h)) and the S1f entry ((a)), each raise checked against
  the "Plan 0038 batch S2b, S2c, S1f, H2b" sections of [items/0005](../findings/items/0005-affixes.md) and the reviews.
  - **items/affixes** {C 112, I 46, L 4} → **{C 152, I 27, L 4}**. Raised: aff 2, 3, 5, 8–11, 12 and 6 (S1f), 13 ×2,
    15 (188/135 correction), 17, 19 ×2, 21 ×3, 22, 30 L600, 35, 37. Split along their remainders: aff 1, 4, 14, 24, 27,
    28 ×2, 30 I1 and I2–I6, 34. Restated `[I]`: aff 7/16 (C5b split from C5a), 20 (E5). aff 27: G3's armour and throw
    lines kept `[I]` pending a ruling (review request). Stale oracle wording of § I closed.
  - **Wiki:** [items](../wiki/items.md) affix paragraphs and the untested *Affixes* line; `based_on` 2026-10-20.
  - **Waiting** (missing batches): items/tc H2c; items/uniques-sets H1a (us 21); items/properties H2c;
    items/sockets-runewords H6b; items/cube H6a; items/vendors H6c; items/quest-drops H4a, H6e1, H6e2; save/d2s H1a,
    H1b; data/excel H3b (and the plan 0039 fold); data/strings and data/README H3b; monsters/pool, monsters/special and
    monsters/stats H4a; monsters/spawn H4a, H5d; hirelings H1a, H1b, H6f; player/creation H1a, H6g; drlg/collision
    H5d; objects H6e2.
  - **Backlog:** the H2b spec-updates, S2b corrections, S2c corrections and S1f entries annotated (done in part);
    review request
    [s38h2b review](../backlog/archive/2026-10-20-spec-writer-architect-s38h2b-items-affixes-review.md).
  - **Next:** architect review of `lane/s38h2b`; the remaining items clusters after H2c, H1a and H6b.
- **2026-10-20 — Review of `lane/s38h2b`, Phase 3 items/affixes cluster (architect): accept with fixes (4).** `main`
  had not moved past the lane's base (`33484f8`), so no merge. Read: the spec diff against the S2b, S2c, S1f, Plan 0048
  Phase 1 and H2b sections of [items/0005](../findings/items/0005-affixes.md), the H2b review above, the inventory row
  27 and § 2.6, the wiki diff and the four annotated backlog entries. Anchors spot-checked in `re/symbols.csv`
  (`ITEMS_GetBaseType`, `ITEMS_RareNameTypeOk`, `sub_00557380_ItemFallbackMagic`, `sub_005C0D00_AffixCandAdd`,
  `RNG_RangeB`, the stackable and throwable accessors): all resolve.
  - **Against the reviewed H2b ledger:** aff 13's and aff 21's controls are the review's version-1 ones (30–35 affix
    and 18–37 name candidates per side, from `tkf` 32/35, `tax` 30/34, `tkf` 36/19, `tax` 37/18), not the lane's
    version-101 control; sock 42 is not in this cluster. aff 15's 188/135, aff 19's 21 jewels (13 at 3, 8 at 4), aff
    17's 9/71, aff 24's split (the `{S, 666}` reset `[C]`, the discard and E5 `[I]`) and every S2b/S2c/S1f raise match
    their ledgers, remainders kept `[I]`.
  - **Ruling (aff 27):** the lane's weaker reading stands. The S2c review's "raised in full" accepted the false return
    only; G3's armour and throw-damage lines were never logged, so aff 27 stays raised in part with those lines `[I]`
    (no class moves; the row stays counted as S2b). A dated note in items/0005 § S2c corrects the sentence.
  - **Cluster readiness:** confirmed. items/affixes waited on H2b only (aff 14's window remainder is an H6a piece, the
    row counted as S2c); items/tc and items/properties wait H2c, items/uniques-sets H1a (us 21), items/sockets-runewords
    H6b.
  - **Fixes applied (4):** (1) overclaim: C5a and R1 test `stackable or Throwable`, but every logged base (all 18
    classic throwing weapons) is both, so each half alone is split out `[I]` (spec C5a, R1 note; items/0005 aff 13 note).
    (2) overclaim: C4i's "still passes every other test" reworded to "a forced row that passes every other test", the
    `[C]` part of S2c aff 14. (3) omission: the wiki's untested *Affixes* line names the throw-damage cut with the
    armour cut. (4) other: G4's "both lines" anchor reads "the call and the return". Research map row rewritten whole
    (C 152 / I 28 / L 4).
  - **Counts** (gate E6, script over the body): items/affixes **{C 152, I 28, L 4}**.
  - **Backlog:** review request
    [s38h2b review](../backlog/archive/2026-10-20-spec-writer-architect-s38h2b-items-affixes-review.md) closed; the H2b
    spec-updates, S2b, S2c and S1f entries stay open (done in part, their other clusters pending).
  - **Next:** merge `lane/s38h2b`; the remaining items clusters after H2c, H1a and H6b.
- **2026-10-21 — H2c paused at the owner's request (reverser, `lane/h2c`, from `main` `baff91c`).** Slot 2 is stopped
  and its saves directory restored (empty, no aside). No game, driver, pilot or gdb of the lane is left running.
  Nothing below is claimed yet: no statement is raised, no § 2.6 entry, no review request.
  - **Read lists first (ADR-0013), committed before any session** (`fc6c7a6`):
    - [items/0001 § 8](../findings/items/0001-tc-resolution.md#8-item-pick-and-hand-off-0x0055ac5f0x0055af59), the
      throwable re-pick;
    - [items/0006 § 4](../findings/items/0006-properties.md#4-the-handlers-per-func), funcs 12, 23 and 24;
    - [items/0004 § 6](../findings/items/0004-uniques-sets.md#6-a-tc-cell-that-names-a-unique-or-a-set-item), the
      TC-named boundary.
    - `tools/sweep_h2c.py reads` gives 0 TC reads in every claim closure (`workspace/logs/h2c/check/check-reads.txt`;
      re-take it with the final tool revision).
    - Correction carried: § 8's excerpt named `ITEMS_GetByCode('lsd ')`; the call is `sub_00633680_ItemIndexByCode`.
  - **Edited tables** (`excel_edit.py`, then `excel_bin.py diff` 0 mismatches and `bindiff` with only the listed
    cells, `workspace/logs/h2c/edit-*.txt` and `bindiff.txt`). Every edit is a loose `treasureclassex.bin` under
    `-direct` in its own game copy. The stock files are untouched. Hashes are in `workspace/logs/h2c/h2c-tables.sha256`
    (`a047db79…`):
    - stock `d6d1b457…`;
    - **throw A** `12f4dd47…` (`game-forced-h2c-throw`): rec 42 `Act 1 Junk` Item1..3 → `tkf`, `tax`, `jav`
      (3 cells);
    - **throw B** `2160c76b…` (`game-forced-h2c-throw2`): the same plus `Picks` 1 → 2 (4 cells). It was added after
      throw-a, because no classic monster TC reaches Junk twice in one call, so A cannot show a twelfth throwable.
    - **tcn** `ad171f79…` (`game-forced-h2c-tcn`), 8 cells: recs 777/822 `Act 5 (H) Super A/Ax` Item1/2 →
      *Ormus' Robes*, *Ethereal Edge*; rec 716 `Haphesto (H)` Item1..4 → *Tomb Reaver*, *Shadowkiller*,
      *Ghostflame*, *Ormus' Robes*. *Tomb Reaver* (lvl 86) is the only stock-droppable func-24 carrier, and
      Eldritch's drops are ilvl 84, so it needs Hephasto (ilvl 88).
    - The excel directories for the checkers are `workspace/runtime/excel-forced-h2c-{throw,throw2,tcn}`.
  - **Sessions** (slot 2, `tools/h2c_sessions.py`, logger `tools/gdb/items-h2c.gdb` = the items-h2b set plus
    `tools/gdb/h2c.py`). There are 10 launches, 8 kept logs (`workspace/logs/h2c/h2c-run.lst`; manifest
    `h2c-manifest.sha256` `12d400ec…`, `sha256sum -c` from `workspace/logs/h2c` passes). No log has `internal-error:`
    or `LOGERR`.
    - Run run:2026-10-21-throw-forced, classic Normal sweeps on `UniqClassic`:
      - throw-a, variant A, Cold Plains;
      - throw-b and throw-c, variant B, Stony Field and Dark Wood. Throw-c ended at a level change after 132 s.
      - Checks: `sweep_h2c.py logs` 0 failed. There are 100 resolver calls with a throwable, 937 refunds and
        141 Long Swords: 45 calls of 10 refunds + 1 `lsd`, 48 calls of 10 + 2, and 7 calls of 1 stock refund.
        Every refund is at counter 0–9, every `lsd` at 10 or 11, and the `lsd` index is 31 (the weapons row), the
        `CPRE` item each time. No classic creation is of a throwable type.
      - `tc.py replay` with the matching excel directory: 183/183, 108/108 and 86/86.
      - Stock control for "classic only": H2b's expansion logs create 13 throwable-type items with no refund
        (`sweep_h2c.py control`).
    - Run run:2026-10-21-tcnamed-props-forced, Hell, `UniqNova`:
      - tcn-a and tcn-b, Eldritch at `/players 1`. Each makes one *Ormus' Robes* (func 12: `WR` param = the roll in
        36..60, value = par 3) and one *Ethereal Edge* (func 23: entry not ethereal, `ItemHasDurability` 1, made
        ethereal, `r` 1). `sweep_h2c.py logs` 0 failed. On tcn-a, `props.py check`, `uniques.py check` and
        `items_chain.py both` give 41/41, and `tc.py replay` gives 67/67.
      - Hephasto: heph-c, -d and -e met no Hephasto. Heph-d died chasing a lightning-immune Doom Knight. In heph-c and
        heph-e, explore `--to-pdef 853,854` stopped with "no target" short of the Hellforge.
      - Dev logs in `workspace/logs/h2c/dev/` (`h2c-dev-manifest.sha256` `6e9d0d98…`): heph-a and heph-b, whose
        waypoint row was wrong (River of Flame is row 3 of Act IV's three-row list), so no creation.
    - Saves are the H2b ones, copied to `workspace/logs/h2c/saves/` (`h2c-saves.sha256`, the same hashes as
      `items-chain-saves.sha256`).
  - **Next (resume):**
    1. Merge `main`.
    2. Optional, one or two more launches:
       - tcn-c (Eldritch, queued in `h2c_sessions.py`) for a third func 12/23 pair;
       - for func 24, either a Hephasto session that reaches the Hellforge (owner play, or a pilot path fix), or file
         prop 15 as a **shortfall** (no func-24 carrier met; *Tomb Reaver* is the only stock carrier, ilvl ≥ 86).
    3. The full check set into `workspace/logs/h2c/check/`, under `systemd-run --user --scope -p MemoryMax=4G`, with
       outputs hashed. Use the excel directory per variant:
       - `sweep_h2c.py reads`, `logs` (throw and tcn sets) and `control` (H2b list);
       - `tc.py replay` per log;
       - `items_chain.py both`, `uniques.py check`, `props.py check` and `quality.py check` on every kept log.
    4. The write-up. None of it is drafted yet, so draft it in place:
       - the two run records in `docs/findings/items/experiments.md`;
       - the "Plan 0038 batch H2c" ledgers in items/0001 and items/0006.
       - Proposed rows:
         - tc 10 ×2 raised (the bound of 10 and `lsd`);
         - tc 55 raised (type only, after the quality roll, first 10 refund, later ones `lsd`, classic only, with
           the expansion control);
         - tc 56 raised in part (the `version ≥ 100` half is d-none);
         - props 12 (L390) raised;
         - props 14 raised;
         - props 15 shortfall unless a carrier is met.
    5. The § 2.6 H2c block with totals against `main`, the spec-writer entry, the symbols (`PROP_Func12_SkillRand`,
       `PROP_Func23_Ethereal` I → C if raised), and the review request (`backlog.py new`; stage before commit).
- **2026-10-21 — Batch H2c filed (reverser, `lane/h2c`, resumed from the pause note above).** `main` (`3d1cc99`)
  merged into the lane first, no conflict. Two more launches on slot 2: tcn-c (Eldritch, one more *Ormus' Robes* and
  *Ethereal Edge*) and heph-f, the one pilot attempt at the Hellforge (`explore --persist 25`), which died at hop 19 in
  the River of Flame. Slot 2 then stopped and its saves directory restored (empty, no aside). 12 launches, 10 kept
  logs, 2 dev logs; no log has `internal-error:`. Every count re-taken from the full check set in
  `workspace/logs/h2c/check/` (`run-checks.sh`, under `MemoryMax=4G` scopes, re-run once with the same hashes).
  - **Ledger** ([items/0001](../findings/items/0001-tc-resolution.md#plan-0038-batch-h2c-2026-10-21),
    [items/0006](../findings/items/0006-properties.md#plan-0038-batch-h2c-2026-10-21)): 6 rows, 7 statements:
    **4 raised** (tc 10 ×2, tc 55, prop 12 L390), **2 raised in part** (tc 56: the `version ≥ 100` half d-none;
    prop 14: func 23's two skips not reached), **1 shortfall** (prop 15: no Hephasto, so no func-24 slot).
    The pause note's "props 14 raised" is filed in part (rule 8).
  - **Checks** (run:2026-10-21-throw-forced, run:2026-10-21-tcnamed-props-forced): `sweep_h2c.py reads` 0 TC reads,
    `logs` 0 failed (1 078 `THR`, 937 refunds, 141 Long Swords; 3 func-12 and 3 func-23 entries, 0 func-24),
    `tc.py replay` 677/677, `items_chain.py both`, `uniques.py`, `props.py` 580/580, `quality.py` 1 496/1 496.
  - **Tools since the pause:** `sweep_h2c.py` gains the order test of `THR` against the pick's `QOUT`;
    `h2c_sessions.py` gains heph-f (`explore` options passed separately).
  - **Corrections carried (rule 12):** items/0001 § 8 throwable bullet and the Functions table; items/0006 § 4 table
    rows of funcs 12 and 23 and the funcs-12-and-36 bullet.
  - **Symbols:** `ITEMTYPES_IsThrowable`, `PROP_Func12_SkillRand`, `PROP_Func23_Ethereal` I → C.
  - **Inventory:** [§ 2.6 H2c](0038-inventory/README.md#26-moves-made-by-the-batch-reviews), no class move; totals
    against `main` `3d1cc99`: static 567, harness 526, blocked 414 (d-none 288), deferred 2, raised 17: 1 526.
  - **Backlog:** review request
    [2026-10-21-reverser-architect-review-lane-h2c-plan-0038-batch-h2c-forced](../backlog/archive/2026-10-21-reverser-architect-review-lane-h2c-plan-0038-batch-h2c-forced.md);
    spec-writer entry
    [2026-10-21-reverser-spec-writer-h2c-forced-throwables-and-tc-named-props-spec](../backlog/archive/2026-10-21-reverser-spec-writer-h2c-forced-throwables-and-tc-named-props-spec.md)
    (to be released with the review).
  - **Next:** architect review of `lane/h2c`; then items/tc and items/properties clusters (Phase 3).
- **2026-10-21 — Review of `lane/h2c`, batch H2c forced (items/tc, items/properties; architect): accept with fixes
  (3).** `main` had moved to `20c33d7` (`lane/srng`: plan 0046, rng/seeds, the ledger; no inventory row); the merge of
  `main` into the lane was refused by the session's permission layer, so the orchestrator's merge takes it (the ledger
  rows of `lane/srng` sit at the end of `docs/plans/metrics.md` beside the H2c rows; keep both). Read: the pause and
  filing entries, both run records, the H2c sections and corrections of items/0001, 0004 and 0006, the inventory
  § 2.6 H2c block and § 6 rulings 1 and 2, `re/symbols.csv`, the two backlog entries, `tools/sweep_h2c.py` (`logs` and
  `control`), and the check outputs.
  - **Re-checked** (worktree): `sha256sum -c` passes on `h2c-manifest.sha256` (10 logs and the list),
    `h2c-tables.sha256` (stock and the three variants), `h2c-check.sha256` (from `check/`, nine outputs) and the dev
    manifest; the cited hashes of `run-checks.sh`, the run list, the manifest and every tool match the files. The
    ledger recounts from `check-logs.txt`: 497 + 581 = 1 078 `THR`, 452 + 485 = 937 refunds, 45 + 96 = 141 `lsd`, 47 + 53
    = 100 calls (93 at the bound, 7 of one refund); 3 `E12`, 3 `E23`, 0 `E24`. 6 rows, 7 statements (4 + 2 + 1).
  - **Each raise against a reading it rules out:** tc 10 by the counter sequence (`sweep_h2c.py` fails a refund at ≥ 10,
    an `lsd` below 10, a non-0,1,2… sequence and an `lsd` after other than 10 refunds; 93 calls at the bound); tc 55 by
    the per-thread order `QOUT` (same item, seed stepped) → `THR`; prop 12 by the swapped param/value (37–39 against
    3); prop 14 by the logged entry state and `props.py`'s final lists.
  - **Rulings.** (a) prop 14 in part, as filed: three make-branch entries, neither skip reached (rule 8). (b) tc 55's
    order evidence is admitted: the `THR` breakpoint follows its own item's `QOUT` in every one of 1 078 picks with no
    `PICK` between, each after a roll that stepped the seed, and the replay holds the seed chain of all 377 calls; the
    order test is the cited revision `75a9d18a…`. The upgrade draws (H5) between them stay unexercised (ratio words 4
    and 5 are 0), and "`type` not `type2`" stays the code reading: no stock item separates them (review check; fix 3).
    (c) The "classic only" control is admitted as stock-data behaviour of the expansion branch: every one of the 329
    expansion creations of H2b's logs follows its `QOUT` directly, so the 13 throwable-type ones were picked, rolled and
    created with neither refund nor `lsd` (review check in the run record). The `THR` lines' flag 0 is tautological at
    0x0055AE9C (after the expansion test) and is not the control. (d) prop 15 stays an H2c **shortfall**, counted as
    harness, as H2b's prop 24; no further pilot attempt is asked of the reverser. The open route is an owner-played
    Hellforge session (Hell, `Haphesto (H)` edited as tcn) or a pilot that reaches rooms 853/854; it goes to plan
    0038's open questions with the H7a-style shortfalls, not to d-owner by this review. (e) `sub_00633680_ItemIndexByCode`
    raised I → C (fix 2). (f) Totals stand: no class move, `main`'s new commits touch no inventory row: **static 567,
    harness 526, c-emu awaiting a batch 0, blocked 414** (d-none 288, d-edit 73, d-sim 28, d-2c 7, d-owner 10,
    d-0032 8), **deferred 2, raised 17: 1 526.** § 5 marks H2c done.
  - **Fixes applied (3):** (1) overclaim: prop 14's "no draw and no stat write" read "no `PROP_WriteStat` call";
    `ITEMS_MakeEthereal` scales a weapon's base stats, which `props.py`'s final-list check covers (items/0006 prop 14,
    the spec-writer entry (e)). (2) under-claim: `sub_00633680_ItemIndexByCode` I → C, `lsd ` → 31 logged 141 times and
    created as that index each time (`re/symbols.csv` evidence moved to items/0001; items/0001 Functions table row and
    H2c Symbols line; items/0011 table row). (3) omission: tc 55's `type` against `type2` not separated, stated in
    items/0001 tc 55 and the spec-writer entry (b). Promoted: reverser review-fixes rule 14 (symbols the run checks,
    seen at H2b and H2c).
  - **Backlog:** review request
    [2026-10-21-reverser-architect-review-lane-h2c-plan-0038-batch-h2c-forced](../backlog/archive/2026-10-21-reverser-architect-review-lane-h2c-plan-0038-batch-h2c-forced.md)
    closed; the spec-writer entry
    [2026-10-21-reverser-spec-writer-h2c-forced-throwables-and-tc-named-props-spec](../backlog/archive/2026-10-21-reverser-spec-writer-h2c-forced-throwables-and-tc-named-props-spec.md)
    released (open, for the Phase 3 re-tag of items/tc and items/properties).
  - **Next:** merge `lane/h2c` (with `main` and `backlog.py archive`); the items/tc and items/properties clusters
    (Phase 3), which waited on H2c.
- **2026-10-21 — Phase 3, the items/tc and items/properties clusters (spec-writer, `lane/s38h2c`, from `main`
  `f805cdf`).** Both clusters waited on H2c only (accepted above); this round folds every accepted batch of the two:
  items/tc S2a, S4b (tc 64), H6d, H2a, H2b and H2c; items/properties S2b, S2c (prop 19), H2b and H2c. Each raise was
  checked against the "Plan 0038 batch …" sections of [items/0001](../findings/items/0001-tc-resolution.md) and
  [items/0006](../findings/items/0006-properties.md) and the reviews.
  - **items/tc** {C 49, I 81, L 6} → **{C 119, I 60, L 5}**. Raised: S2a tc 3–5, 7, 12, 16, 18, 21, 24, 25, 28, 32,
    35, 36, 39, 50, 52, 61, 62, 66; tc 64 (§ J with the tier arithmetic and the `ilvl` hand-off); H2a tc 1, 2, 11, 34
    L361, 37, 45, 47, 59, 71; H2b tc 68; H6d tc 26; H2c tc 10 ×2, 55. Split along their remainders: tc 14, 19, 22, 23,
    27, 29–31, 33, 34 L388, 38, 40, 42, 48, 49, 51, 56–58, 60, 67, 69, 70, 72, 73. Restated as no stock case: tc 13, 15,
    41, 74. tc 55's `type`-not-`type2` reading kept `[I]` (H2c fix 3). *Open questions:* the chest-cut `[L]` struck,
    the classic/Hell `[L]` narrowed to the edited-cell cases, `game.type` to value 1.
  - **items/properties** {C 130, I 35, L 2} → **{C 152, I 22, L 3}**. Raised: S2b prop 1 and 2 (with their two
    corrections), 4 ×2, 5, 6, 8, 9, 16, 18 L450; S2c prop 19 L535, L549; H2b prop 20 ×2; H2c prop 12. Split: prop 1's
    vendors sentence, 18 L454, 19 L573, 14 (func 23: make branch `[C]` with "no `PROP_WriteStat` call", skips `[I]`),
    the funcs-12-and-36 bullet (func 36 `[I]`). Kept `[I]`: prop 7 ×3 (no stock case), 23, 24 (shortfall), 21. prop 15
    (func 24) is an `[L]` of its own under *Open questions*, with the Hellforge route.
  - **Wiki:** [items](../wiki/items.md) and [objects](../wiki/objects.md) restated; `based_on` 2026-10-21.
  - **Backlog:** the H2c, H2a and S2b-corrections entries closed; the H2b, H6d, S4b and S2a tc 64 entries annotated
    (done in part). Review request
    [s38h2c review](../backlog/archive/2026-10-21-spec-writer-architect-s38h2c-items-tc-properties-review.md) (one ruling asked:
    prop 9 stated `[C]` whole; one mismatch noted: objects § J3 still `[I]` on the chest `ilvl` hand-off).
  - **Waiting** (missing batches): items/uniques-sets H1a (us 21); items/sockets-runewords H6b; items/cube H6a;
    items/vendors H6c; items/quest-drops H4a, H6e1, H6e2; and the non-items clusters as listed above.
  - **Next:** architect review of `lane/s38h2c`.
- **2026-10-21 — Review of `lane/s38h2c`, Phase 3 items/tc and items/properties clusters (architect): accept with
  fixes (4).** `main` had not moved past the lane's base (`f805cdf`), so no merge. Read: the spec diffs of items/tc and
  items/properties against the "Plan 0038 batch S2a, H6d, H2a, H2b, H2c" sections of
  [items/0001](../findings/items/0001-tc-resolution.md) (with tc 64's S4b line and § 2's chest arithmetic) and the
  "S2b, S2c, H2b, H2c" sections of [items/0006](../findings/items/0006-properties.md), the reviews above, inventory
  § 2.6, both wiki diffs, objects § J3 and the seven touched backlog entries. Every `fn:`/`data:` anchor of both specs
  resolves in `re/symbols.csv` (script); spot-checked `TC_GetByIndex`, `ITEMTYPES_IsThrowable`,
  `sub_00633680_ItemIndexByCode`, `ITEMS_UnitIsType`, `PROP_ApplyBlockByVersion`, `RUNEWORD_Apply`, `ITEMS_IsEthereal`,
  `DRLG_ActFromLevelId`, `g_SkillDoFuncs`.
  - **Scope ruling:** a fair reading, not scope creep. Phase 3 runs "per cluster once all of that cluster's batches are
    accepted", so a cluster's round folds every accepted raise of the cluster; items/tc and items/properties both
    waited on H2c, and `lane/s38h2b` did the same for items/affixes. plan 0044's tc 43, 44 and 46 were already applied
    (§ 2.6, *raised by plan 0044*).
  - **Against the ledgers:** the raised and in-part lists match each tally line: S2a 20 raised and 18 in part (tc 3–5,
    7, 12, 16, 18, 21, 24, 25, 28, 32, 35, 36, 39, 50, 52, 61, 62, 66; 14, 19, 23, 29–31, 33, 38, 40, 42, 48, 49, 51,
    57, 67, 69, 72, 73), tc 13, 15, 41, 74 restated as no stock case; H6d 26 / 27; H2a 9 / 4; H2b 68 / 58; H2c tc 10 ×2,
    55 / 56; tc 64 by S4b with J1 equal to items/0001 § 2 (both boundaries, 14 and 5 calls); S2b 7 raised (prop 4 ×2,
    5, 6, 8, 16, 18 L450), prop 1 and 2 rewritten with their corrections (the remainder was the rewording), 18 L454
    split, 23 and 24 kept `[I]`; S2c prop 19 ×2 / L573; H2b prop 20 ×2, prop 7 ×3 no stock case, 24 shortfall; H2c
    prop 12 / 14, prop 15 an `[L]` with its route. H2c rulings (b) and (c) are stated as ruled. Counts (gate E6):
    items/tc **{C 119, I 60, L 5}**, items/properties **{C 152, I 22, L 3}**, unchanged by the fixes.
  - **Rulings.** (a) prop 9 `[C]` whole stands: its S2b remainder (what `add func` 1 and 2 do when worn) was answered
    by plan 0041 (stats/aggregate § J, `[C]` by run:2026-10-17-stats), which the next B3 note states; a dated note in
    items/0006 prop 9 records it; the row's class does not move. (b) objects § J3 against items/tc § J: the objects
    spec stays `[I]` until the objects round (routing of 2026-10-20 in the S2a tc 64 entry, which stays open for it);
    the objects wiki takes the weaker tag meanwhile (fix 1). items/quality C1 and items/tc § J state the hand-off `[C]`
    on the same accepted evidence, so the items wiki keeps it. (c) prop 19 without a spec-writer entry: admitted. The
    S2c review accepted prop 19 as filed, and Phase 3's input is the accepted ledger; the S2c corrections entry never
    listed it, so it needs no annotation. (d) Backlog: the three closed entries (H2c, H2a, S2b corrections) have
    nothing owed: H2a's (j)–(m) and the quality lines of (o) were done by `lane/p38s7`, S2b's (c) and the affixes half
    of (f) by `lane/s38h2b`. The four annotated ones (H2b, H6d, S4b, S2a tc 64) still owe parts to other clusters.
  - **Fixes applied (4):** (1) overclaim: the objects wiki stated the chest tier's cut and the tier-as-`ilvl` hand-off
    confirmed while objects § J3 still tags both `[I]`; restated as read from the code there, naming the treasure class
    spec's check. (2) stale cross-reference: the objects wiki's untested line still said the cut was not written down;
    rewritten. (3) misread: the items wiki said the classic skip of an expansion-only entry "cannot happen" with stock
    tables; it happens and changes nothing (tc E2 note), reworded with the `version` reject. (4) overclaim: tc A2 note's
    "reached by no classic call" scoped to the log set. Research map: the items/tc and items/properties rows rewritten
    whole; the items/affixes row corrected to I 28 (the `lane/s38h2b` review's count had not reached the row).
  - **Promoted:** spec-writer rule 1 extended to two specs that disagree; architect rule 3 cites the affixes row.
  - **Backlog:** review request
    [s38h2c review](../backlog/archive/2026-10-21-spec-writer-architect-s38h2c-items-tc-properties-review.md) closed.
  - **Next:** merge `lane/s38h2c`; the remaining items clusters after H1a, H6a, H6b, H6c, H4a, H6e1 and H6e2.
- **2026-10-21 — H4a (`monsters-a`) paused at the owner's request (reverser, `lane/h4a`, harness slot 1, from `main`
  `1d0262a`).** Slot 1 is stopped and its saves directory restored (empty, no aside). No game, driver, pilot, gdb or
  wait loop of the lane is left running. Nothing below is claimed yet: no statement is raised, no § 2.6 entry, no review
  request.
  - **Tools** (committed): `tools/gdb/mon-h4a.gdb` = `mon-stats.gdb` unchanged plus `tools/gdb/mon-h4a.py` (tags only:
    `SUC`/`SUCR` at every call of `SuperUniqueSpawn`'s tail cases 0x005A4BFE–0x005A4E43 with the pushed arguments,
    `SURD` after Radament's `Range(us, 5)`, `GQ` at the Chaos Sanctuary gate 0x0054EC27; pilot helpers `MON` and
    `OBJS`); `tools/gdb/mon-h4a-obj.gdb` adds `tools/gdb/objects.py` (seals, `OOX`). `MONSPAWN_WATCH` and `H4B_WATCH`
    empty in every session. H4b review condition (4): `sweep_h4b.py check` on the nine H4b logs gives the summary of
    `workspace/logs/h4b/sweep-check.txt` line for line, `monstats.py check` 0 mismatches on every group
    (`workspace/logs/h4a/check/regress-*.txt`). Checker `tools/sweep_h4a.py` (`su`, `tails`, `handlers`, `gate`, `boss`,
    `names`, `wander`); runner `tools/h4a_sessions.py`.
  - **Sessions** (slot 1, `UniqNova` `2c793a3d…`, expansion Nightmare, `workspace/logs/h4a/`; manifest
    `h4a-manifest-paused.sha256`; no log has `internal-error:`): raven (4901, Burial Grounds not reached), raven2 (4807,
    Blood Raven: mod 12 name 3111, `SI2` 43), tree (4902, Treehead, null row 13), andy (4903, Andariel name 3021), radament
    (4904, tail 10 reproduced, r = 0), council (4905, tails 26/27/29), durance (4906, Bremm's aura twice, Mephisto name
    3062), foothills (4908, no Siege Boss), nihl (4909, wrong waypoint row: Glacial Trail), shenk (4815, tail 42: escorts
    20 × 453, quest hook 31, `0x545B50`, state 118), nihl2 (4910, tail 60: 20 × 458, hook 34). `monstats.py check` 0
    mismatches on the first nine (`check/monstats-h4a-part1.txt`). Dev logs in `dev/`: raven-nowp (no waypoint click),
    chaos and chaos2 (no object lines: no seal found), chaos3 and chaos4 (seals not clicked), chaos5-paused (stopped by the
    pause after one seal was opened). Kept-log checks: `check/check-kept.txt` over the 63 logs of
    `check/kept-logs.lst` (bad 0: placed-bit refusals 3, Feature Creep's aura twice 2, Siege Boss escorts, null rows 10
    and 13); `check/monstats-monequip-kept.txt`; static `check/static-wanderer.txt`, `check/static-gate.txt`.
  - **Drafts** (not committed; `workspace/logs/h4a/drafts/`): ledger sections of monsters/0001 (pool 12), 0004 (stats 7,
    18, 21) and items/0010 (qd 48) as `findings-drafts.diff`; the monsters/0003 section head.
  - **Next (resume):**
    1. Merge `main`; `python3 -I tools/saves.py --slot 1 aside h4a` (slot 1 only).
    2. Chaos Sanctuary: `h4a_sessions.py run … chaos5` (seed 4907, `mon-h4a-obj.gdb`; objop `--obj-near 6` clicked one
       seal, later clicks at d 4–6 brought no `OOX`: try `--obj-near 3` or `--obj-dy`, or owner play). Needed for special
       9, 10, 25, 31, 38, 50 (thief half), 56 and spawn 11 (`GQ` 1 after the seal bosses die); the doomknight3 piece.
    3. Optional: Ancients (special 59, b; likely a shortfall), Diablo's name (243).
    4. Full check set into `workspace/logs/h4a/check/` under `MemoryMax=4G` (`sweep_h4a.py check` on all session logs,
       `monstats.py check`), hashed; then the write-up: run record run:2026-10-21-sweep-monsters-a in monsters/experiments,
       "Plan 0038 batch H4a" ledgers in monsters/0001–0004 and items/0010 (apply the drafts), § 2.6 H4a block and totals
       against `main`, symbols (`sub_005B24E0_EscortSpawn`, `QUESTS_HookMonster` call args if raised), review request.
       Proposed so far: raised pool 12, qd 48, stats 7, 18, special 30, 35, 48 (kept logs), 50 (aura half), 51, 54, 55,
       58, 60, 68; in part stats 21, special 34 (rows 10, 13), 46, 52, 69 (156, 242, 256); spawn 5 and 49 by the static
       read of 0x00731B2C/0x00731B30 (S2c ruling 2); shortfall spawn 47, 48 (no `WRL`), special 59.
- **2026-10-21 — H4a (`monsters-a`) paused again at the owner's request (reverser, `lane/h4a`, harness slot 1, after
  merging `main` `fafcd32`).** Slot 1 is stopped and its saves directory restored (empty, no aside). No game, driver,
  pilot, gdb or wait loop of the lane is left running. Still nothing is claimed: no statement raised, no § 2.6 entry,
  no review request.
  - **Found:** chaos5-paused had opened two seals, not one (`OO0`/`OOX` for 392 and 393, both in wing 859); its later
    objops re-clicked those two, so the misses were not a click-distance problem. The other wings' seals never
    appeared because `explore --to-pdef` stops at a wing's edge.
  - **Tools** (this commit): `d2pilot.py objop --skip-operated` (an object whose unit has an `OO0` line is never
    targeted again); `h4a_sessions.py` sessions chaos6 (each wing an `objop --to-pdef W --pdef-any --skip-operated`
    and a sweep) and chaos7 (the same with `--obj-near 6` and 300 s per wing).
  - **Sessions** (dev logs, `workspace/logs/h4a/dev/`; manifest `h4a-manifest-paused2.sha256`): chaos6 (stopped by
    the lane: `--obj-near 4` left it 4.2 sub-tiles from seal 392 with no hop), chaos7-paused (stopped by this pause:
    seals 392, 393, 395 and 396 opened; `SU0` and the tail calls `QUESTS_HookMonster(23, 36 | 38, room, 0, 1)` then
    `0x005A4850(22, 1, …)` for the Infector of Souls (36) and the Grand Vizier (38); seal 394 (Lord De Seis) not yet
    opened, no `GQ` with `eax` 1).
  - **Checks so far:** `sweep_h4a.py check` on the eleven kept session logs, bad 0 in every part
    (`check/sweep-check-part1.txt`); `static-wanderer.txt` now also holds the objdump scan for every instruction naming
    0x00731B2C–0x00731B3F (three readers, no writer) and r2's `px 16 @ 0x00731B2C` (second tool).
  - **Drafts** (not committed; `workspace/logs/h4a/drafts/`): `findings-drafts.diff` (0001, 0004, items/0010; applies
    cleanly on this commit), `sec0003-body.md` (monsters/0003 rows 30/50/51, 34, 35/68, 48, 54, 55, 58, 60, 69),
    `sec0002.md` (spawn 5/49 raised by the operand route, 47/48 shortfall, `{SPAWN11}` to fill), `exp.md` (the run
    record with `{…}` holes), and the spec texts at `1d0262a` the L-numbers come from.
  - **Next (resume):**
    1. `python3 -I tools/saves.py --slot 1 aside h4a`; run `h4a_sessions.py run --slot 1 --tag h4a --saves
       workspace/runtime/h4a-chars --run h4a chaos7` (about 30 min: 5 min into 108, 4 wings × 320 s, sweep, explore,
       hunt 243). It needs seal 394 for Lord De Seis (special 9, 10, 25, 31, 38, 50 thief half), the three seal bosses
       killed for `GQ` 1 (spawn 11); tails 36–38 (special 56) are already seen in the dev log. If seal 394 is not
       reached, file those rows as shortfalls with an owner-play route.
    2. Full checks into `workspace/logs/h4a/check/` (`sweep_h4a.py check` on all kept session logs including chaos7,
       `monstats.py check` on chaos7), hashed; then fill the drafts, write § 2.6 (no class moves expected; totals
       against `main`: static 567, harness 526, blocked 414 at `fafcd32`), symbols (`sub_005B24E0_EscortSpawn` I → C,
       rule 14), the review request and the plan-log entry. The H4b pieces met: Blood Raven's client name (special 66).
  - **Usage:** this resume 0 h 50 min, about 95 tool calls, about 190 k tokens; with the earlier part about 620 k
    tokens, 325 tool calls, 190 min.
- **2026-10-25 — H4a (`monsters-a`) filed (reverser, `lane/h4a`, harness slot 1, after merging `main` `e3ac907`).**
  run:2026-10-21-sweep-monsters-a: twelve kept sessions (session chaos7 added on this resume, 41 min, seed 4907), nine
  development logs; manifests `h4a-manifest.sha256` and `h4a-manifest-dev.sha256` (`workspace/logs/h4a/`). Slot 1 is
  stopped and its saves directory restored (empty, no aside); nothing of the lane is left running.
  - **chaos7:** seals 392, 393, 395 and 396 operated; tails 36 (Infector of Souls) and 38 (Grand Vizier) logged; seal
    394 logged at (7773, 5155), no hop found towards it, so no Lord De Seis, no closed gate, no Diablo. Also met: one
    wanderer roll (level 108; 82 ≥ 3, no spawn), 63 `doomknight3` creations (H4b's stats 14 piece).
  - **Tools:** `tools/sweep_h4a.py wander` now models every tick pair (one step; the roll on low & 0x7FFF = 0 with
    `MonWndr`; the roll's step and the ≥ 3 branch); `check/run-checks.sh` runs the whole check set (with the aura
    control and the class-312 bytes) under `MemoryMax=4G`. Checks: `sweep_h4a.py check` bad 0 on the twelve logs and
    the 63 kept logs; `monstats.py` 0 mismatches on all twelve; the chained models' mismatches on three logs listed in
    the record.
  - **Ledger (32 statements):** raised 16 (pool 12; qd 48; stats 7, 18; spawn 5, 49; special 30, 35, 48, 50 aura half,
    51, 54, 55, 58, 60, 68); raised in part 8 (stats 21; spawn 47, 48 with a correction; special 34, 46, 52, 56, 69);
    shortfall 8 (spawn 11; special 9, 10, 25, 31, 38, 50 thief half, 59). Sections "Plan 0038 batch H4a" in
    monsters/0001–0004 and items/0010; inventory § 2.6 H4a block; totals unchanged (1 526).
  - **Symbols:** `sub_005B24E0_EscortSpawn` I → C.
  - **Backlog:** review request
    [2026-10-25-reverser-architect-review-lane-h4a-plan-0038-batch-h4a](../backlog/archive/2026-10-25-reverser-architect-review-lane-h4a-plan-0038-batch-h4a.md);
    spec-writer entry
    [2026-10-25-reverser-spec-writer-h4a-monsters-a-raises-and-the-spawn-48](../backlog/archive/2026-10-25-reverser-spec-writer-h4a-monsters-a-raises-and-the-spawn-48.md)
    (to be released with the review).
  - **Next:** architect review of `lane/h4a`.
  - **Usage:** this resume about 1 h 50 min, about 110 tool calls; with the earlier parts about 300 min. (Measured by
    the orchestrator: this resume 240 197 tokens, 141 tool uses, 64 min; the earlier parts about 620 k tokens, 325 tool
    uses, 190 min; architect review.)
- **2026-10-25 — `lane/h4a` review (architect): accept with fixes.** H4a (`monsters-a`, 32 statements), reviewed after
  merging `main` `9e221ed` into the lane. Checks re-run on the review side (`check/run-checks.sh` into scratch, under
  `MemoryMax=4G`): the five outputs byte-identical to the kept ones; `h4a-manifest.sha256` and
  `h4a-manifest-dev.sha256` pass; the cited tool hashes match. objdump spot reads of the pinned `Game.exe` for spawn 5,
  47–49 and 11, pool 12, special 34, 54 and the class-312 piece (list in inventory § 2.6, H4a review paragraph).
  - **Fixes (4):** special 54 raised → raised in part (only r = 0 met: the `+ r` of the `skeleton5` count is not
    separated; overclaim); pool 12's "six of the 25 `boss` classes met" → five (miscount); pool 12 and qd 48 now state
    that their `(H)` half rests on the branch and Andariel's hell creation (omission); monsters/0004's H4b section, the
    class-312 remainder marked met (stale cross-reference). The plan-log usage line carries the measured figures.
  - **Rulings.** (a) The seven De Seis and gate rows (special 9, 10, 25, 31, 38, 50's thief half; spawn 11) stay
    harness shortfalls counted as H4a; they are a candidate for the plan's `d-owner` addendum at the close (Open
    questions, with H2c's prop 15), not routed to the owner now (the owner dropped plan 0042's comparable session on
    2026-10-25); a pilot that reaches seal 394 is the other route. (b) spawn 47 and 48 raised in part as filed; spawn 48
    is a correction of the note (the roll fired once), its remainder the same as 47's; `sweep_h4a.py wander`'s 11 969
    ticks are the gate's control (no unrolled zero-low tick, no roll elsewhere). (c) The aura control holds: SuperUniques
    rows 36, 42 and 60 have no fixed 30 (`Mod1`–`Mod3` 6/27, 5, none) and get one `AUR`; row 28 (`Mod1` 30) gets two; with
    the two kept-log cases the fixed side has three. (d) The chained-model mismatches (council DRLG room tiles 3, nihl2
    `monspawn` 1 for class 526's mod 22, chaos7 collision `0x1000` 2 + 10) touch no H4a row and get one reverser entry,
    [2026-10-25-architect-reverser-h4a-chained-model-mismatches-council-nihl2](../backlog/archive/2026-10-25-architect-reverser-h4a-chained-model-mismatches-council-nihl2.md).
    (e) Class 312's piece raises stats 14 and 13's remainder: both rows raised whole, still counted as H4b (a Phase 3
    note, no class move). (f) stats 7, 18 and 21 may rest on run:2026-10-20-chain's reviewed check (kept, hashed, cited
    by its own output and re-run here). (g) `sub_005B24E0_EscortSpawn` C stands (rule 14: return 1 and the 20 units
    compared, twice).
  - **Ledger:** raised 15, raised in part 9, shortfall 8. Totals unchanged and recounted against `main` `9e221ed`:
    static 567, harness 526, c-emu 0, blocked 414, deferred 2, raised 17: 1 526.
  - **Backlog:** review request closed (archive); spec-writer entry
    [2026-10-25-reverser-spec-writer-h4a-monsters-a-raises-and-the-spawn-48](../backlog/archive/2026-10-25-reverser-spec-writer-h4a-monsters-a-raises-and-the-spawn-48.md)
    released with the review's changes.
  - **Next:** the Phase 3 re-tag of the H4a rows (spec-writer); the next harness batch per the run order.
- **2026-10-25, reverser, `lane/h5d` (batch H5d, `collision`, 17 statements): paused at the owner's request (usage
  limit), resume note.**
  - **Done (tools only, no claim yet):** `tools/gdb/collision.py` gains unwindowed before/after line pairs (TCB0/TCB1
    at `TileCollisionUpdate`, IM0/IM1 for item marks at `0x0064954C` / `0x00620ACA`, PN0/PN1 for patterns 3 and 4,
    SCT0/SCT1 at `SpawnClassCellTest` with every caller and flag, LPP0/LPP1 at `0x0066AC40`); `tools/collision.py`
    checks each pair (the new tags join `COLL_TAGS`; output on the H5b cata log unchanged). New logger
    `tools/gdb/collision-h5d.gdb` and driver `tools/h5d_sessions.py` (sessions tomb, tomb2, frigid, steppes, jail,
    throne, arcane). Save `workspace/runtime/h5d-chars/UniqNova.d2s` rebuilt from `uniqnova.json` (sha256 `2c793a3d…`,
    same as h4a/h5e). One session (tomb) was stopped at launch: its 21-line log is kept as
    `workspace/logs/h5d/dev-run-2026-10-25-h5d-s1-1557-tomb.log` (development, no claim rests on it).
  - **Leads from the kept logs (to recount with a kept command):** entry flag `0x80` occurs in CB dumps of levels 109,
    111, 112, 117 (18 kept logs, e.g. `h4a/h4a-s1-4908-foothills.log`), already compared cell for cell (row 8: count
    the entries whose `0x04` OR changes a cell); `TileCollisionUpdate` applied in modelled rooms in the H5b, chain-p2
    and h4a logs (rows 1, 9, 11); Arcane 74 (Position 1) reached in `h5b/…-3904-arcane.log`, 625 lookups each one step
    (row 46's first half); the 528 piece of row 45 is H4b's (monsters/0002 § H4b). `suckernest1` (334–337) has no stock
    creation source in any table (pools, MonPreset, minion, superunique, skill columns): propose d-none after a code
    check. 298's flag 0 comes from the AI callers of `0x005FD350` (`0x005F9F9D` pushes 0).
  - **Next:** test the logger on one session (tomb), then the session list; `tools/sweep_h5d.py` (static 334 check,
    kept-log counts), manifest, findings in drlg/0005 and monsters/0002, the § 2.6 entry against current main,
    symbols, the review request, the spec-writer entry. Slot 1 stopped and restored.
- **2026-10-27 — H5d (`collision`) filed (reverser, `lane/h5d`, harness slot 1, after merging `main` `0e3f501`).**
  run:2026-10-27-sweep-collision: nine kept sessions (tomb, tomb-r2, tomb2, frigid, steppes, jail, throne, arcane,
  rogue; expansion Normal, `UniqNova`), record in
  [drlg experiments](../findings/drlg/experiments.md#run2026-10-27-sweep-collision), evidence in the "Plan 0038 batch
  H5d" sections of [drlg/0005](../findings/drlg/0005-collision.md#plan-0038-batch-h5d-run2026-10-27-sweep-collision) and
  [monsters/0002](../findings/monsters/0002-room-population.md#plan-0038-batch-h5d-run2026-10-27-sweep-collision).
  - **Merge of `main`:** first at the resume (`cf25f22`, H4a's merge: no H5d row or tool touched; the plan log's
    conflict kept both sides), then `3fa5209` and `0e3f501` before filing; backlog `archive` run after each.
  - **Ledger (17):** raised 11 (collision 5, 8, 19, 24, 30 ×2, 36, 45's 228, 298-flag-0 and 528; spawn 41), raised in
    part 3 (collision 1, 21 with a correction of the NPC rule, 46), shortfall 2 (collision 9, 11), proposed d-none 1
    (collision 45's 334). Inventory § 2.6 H5d block; totals (proposed) static 567, harness 525, blocked 415, deferred 2,
    raised 17: 1 526.
  - **Design changes on the way:** a second waypoint hop from the waypoint the character stands on did not open the
    list (first tomb session), so each session takes one hop from the starting town; a rogue session (Rogue
    Encampment cows, pattern 4) was added; no Act III session (334 proposed d-none instead). Rows 5 and 8 rest on kept
    logs.
  - **Backlog:** review request
    [h5d review](../backlog/archive/2026-10-27-reverser-architect-review-lane-h5d-plan-0038-batch-h5d.md); spec-writer entry
    [h5d raises](../backlog/archive/2026-10-27-reverser-spec-writer-h5d-collision-raises-and-the-monisnpc-correction.md) (released
    with the review); the H4b follow-ups entry annotated with the H5d piece.
  - **Next:** the H5d review. Slot 1 stopped, saves restored (empty, no aside).
- **2026-10-27 — `lane/h5d` review (architect): accept with fixes.** H5d (`collision`, 17 statements), reviewed at
  `c19f55f` with `main` `0e3f501` already merged (the merge was a no-op; backlog `archive` clean). Checks re-run on the
  review side (`check/run-checks.sh` into scratch, under `MemoryMax=4G`, and `sweep_h5d.py static`): the seven outputs
  byte-identical to the kept ones; `h5d-manifest.sha256` and `h5d-manifest-dev.sha256` pass and hash as cited; the
  eight cited tool hashes match. objdump spot reads of the pinned `Game.exe` (list in inventory § 2.6, H5d review
  paragraph), no Ghidra.
  - **Fixes (6):** collision 21's `npc` half `[I]`: the five stock `npc` rows without `inTown` (406, 527, 537–539) all
    have `interact`, so an `inTown`-only reading also scores 0 mismatches on the 38 338 marks (overclaim); drlg/0005
    § 5's *Pattern from size* rewritten to the corrected rule instead of the old rule plus a note, with the summary line
    and an open question (stale cross-reference); spawn 41 raised → raised in part, its "others" half (`0xFFFF`) d-none
    (overclaim); the record's 318 pattern-5 creations → 360 (miscount); the rogue `objects.py` mismatch was not a second
    click: the waypoint left its creation in mode 1 (arrival by waypoint) and was in mode 2 at its one operate, no
    logged line between (misread); collision 5's 260 and 263 named as not met, and the Functions-table row of
    `COLL_RectOrWH` / `COLL_RectClearWH` scoped to C / I (omission, counted once).
  - **Rulings.** (a) **Collision 21's correction stands** (`MonIsNpc` = `npc` or `inTown`, else `+0xC4` bit 31, read
    at 0x0063E89A–0x0063E8BD): the `[C]` is the `inTown` half, separated by 254 marks; the `npc` half and the `+0xC4`
    branch stay `[I]` (only an edited row, d-edit, separates the `npc` half). Raised in part, as filed. (b) Rows 5 and 8
    rest on kept logs, a-logs in effect, counted as H5d raises (the H4b precedent); row 5 adds 43 live mask-0 tests,
    row 8 the 1 044 cells only the `0x04` OR explains, with the model exact cell for cell. (c) **Collision 46 stays raised
    in part**: with one match per lookup every operand picks the same point, so only the step (one seed draw per
    lookup, and none on zero matches) is `[C]`; the operand stays `[I]`, counted as H5d. (d) **Collision 45's 334
    statement → d-none**, and no Act III session is owed: no table names a class 334–337 as a creation, and the one code
    path that passes 334 (the `MosquitoNest` AI, 0x005E02E8–0x005E0322) runs only on classes 334–337 and calls
    `SpawnClassCellTest` then `MonAiUseSkill`. (e) **Spawn 42 is raised in part** (206, 228, 298, 528 `[C]`; 334 d-none),
    still counted as H4b, a Phase 3 note (as stats 21 at H4a). (f) The rogue mismatch touches no H5d row but is a model
    gap that will recur on every waypoint arrival: its own reverser entry,
    [2026-10-27-architect-reverser-h5d-objects-py-waypoint-mode-after-arrival](../backlog/2026-10-27-architect-reverser-h5d-objects-py-waypoint-mode-after-arrival.md).
    The two "log ends" mismatches are session cuts, no entry. (g) The seven symbols I → C stand (rule 14: each return or
    cell effect logged and compared); `MonIsNpc` stays I, and `COLL_RectClearWH` stays I.
  - **Ledger:** raised 10, raised in part 4, shortfall 2, d-none 1. Totals against `main` `0e3f501`: static 567,
    harness 525, c-emu 0, blocked 415 (d-none 289), deferred 2, raised 17: 1 526.
  - **Backlog:** review request closed (archive); spec-writer entry
    [2026-10-27-reverser-spec-writer-h5d-collision-raises-and-the-monisnpc-correction](../backlog/archive/2026-10-27-reverser-spec-writer-h5d-collision-raises-and-the-monisnpc-correction.md)
    released with the review's changes; the H4b follow-ups entry
    [2026-10-16-architect-reverser-plan-0038-h4b-review-follow-ups](../backlog/archive/2026-10-16-architect-reverser-plan-0038-h4b-review-follow-ups.md)
    closed (its last piece, H5d's, is settled); the new reverser entry above.
  - **Next:** the Phase 3 re-tag of the H5d rows (spec-writer); the next harness batch per the run order.
- **2026-10-27 — Phase 3, the monsters cluster (spec-writer, `lane/s38m`, from `main` `0e3f501`, `main` `0848879` merged
  in after H5d's acceptance).** The cluster's batches, S3a, S3b, S1f, H4b, H4a and H5d (inventory § 5 with the § 2.6
  moves), are all accepted, so monsters/pool, spawn, special and stats qualify; monsters/README was done in round 1.
  - **monsters/pool** {C 81, I 29, L 3} → **{C 99, I 19, L 3}**: the later game-seed draws (rng/0002 via rng/seeds 7a),
    `monLvl` unread (H4b watchpoints), classic normal `mon` (H4b) and level (S3a), the `+0x025` compiler (S3b; the 254 cap
    `[I]`), the set caps (S3a), the other `boss` classes (H4a), `MonLvl` row, the bonuses, the gate, the picks,
    `MonRegionFindAdd` (S3a; its other returns `[I]`), `RegionActClass` (S3b; ranges and cache `[I]`), `tries = 0` (S1f).
  - **monsters/stats** {C 110, I 58, L 4} → **{C 130, I 47, L 5}**: `SetStat`/`AddStat`, the champion part, `MonTypeFlag`,
    the `Align` skip, the velocity bonus corrected to ≤ 8 (S3a); the skill list and bonus, `doomknight2`, `Align` 1/2 (H4b);
    the reversed HP range, the MonProp reader and rows, `druidhawk` reachable (S3b); `MulDiv` (S1f); `doomknight3` and
    `MonEquipInit` (H4a). The flag-0 walk corrected for `SetBoss` pack members.
  - **monsters/special** {C 107, I 95, L 3} → **{C 149, I 70, L 4}**: the always-run mods, null rows met, aura `n`, flag-0
    return, the group walk, the unique-pick remainder, `MonPostCreateMods`, the quest test (S3a); the aura table and levels,
    the `sandleaper` exclusion, the client tables and names, `UniqueTitle`, the restores with the two-aura correction,
    MonPlace cases with the `BaseId` correction (H4b); the second aura call, the tails by record, rows 10/12/13, the placed
    bit, Blood Raven's and three fixed names (H4a). Lord De Seis's rows stay `[I]` with an *Open questions* entry.
  - **monsters/spawn** {C 112, I 64, L 4} → **{C 136, I 43, L 5}**: `RoomUpdateOne`, the client, `MonWndr` (S3b); the box
    rectangle, the special count, the `0x80` bypass, `/players`, classic passes (S3a); the tick, the `spawnCol` masks, the
    hidden-warp writer, `tentaclehead` minions, `PartyMin` = `PartyMax`, `MonSpcWalk`, `evilhut` (H4b); the wanderer list
    and the roll's no-spawn branch (H4a, correcting "never fired"); sizes 0 and 1 and `sarcophagus` (H5d). The Chaos
    Sanctuary gate's closed state stays `[I]` with an *Open questions* entry. The d-none header mentions are reworded.
  - **Backlog:** closed the S3a two-statements entry and the H4b corrections entry; annotated the H4a, S3b, S1f and H5d
    entries; review request with the four specs' old and new counts, the corrections and what is left to other clusters
    ([2026-10-27-spec-writer-architect-review-lane-s38m-plan-0038-phase-3-monsters](../backlog/archive/2026-10-27-spec-writer-architect-review-lane-s38m-plan-0038-phase-3-monsters.md)).
  - **Commits:** the four specs in one commit, then backlog, this log and the ledger. Gate green; W4 warns for the
    monsters and seed-to-world wiki pages.
  - **Next:** architect review of `lane/s38m`.
- **2026-10-27 — Review of `lane/s38m`, Phase 3 monsters cluster (architect): accept with fixes (6).** `main` had not
  moved past `0848879`, already merged into the lane, so the merge was a no-op; `backlog.py archive` moved nothing. Read:
  the four spec diffs (`0848879..cc329ea`) against the S3a, H4b, S3b, S1f, H4a and H5d sections of
  [monsters/0001](../findings/monsters/0001-level-pool.md), [0002](../findings/monsters/0002-room-population.md),
  [0003](../findings/monsters/0003-special-monsters.md) and [0004](../findings/monsters/0004-stats.md), the per-spec
  inventory rows, inventory § 2.2 (pool 5 and 24 by rng/0002) and § 2.6 (the S3a, H4b, S3b, S1f, H4a and H5d moves and
  their review fixes), the touched backlog entries and the lane's log entry.
  - **Done when, item by item.** Every raised, in-part and contradicted row of the six batches for these four specs is
    in the text or listed in the request with its reason; the d-none, d-owner, d-sim and shortfall rows keep `[I]`, the guard ones reworded with their counts.
    E6: pool {C 99, I 19, L 3}, spawn {C 136, I 43, L 5}, special {C 149, I 70, L 4}, stats {C 130, I 47, L 5}, recounted
    by script and unchanged by the fixes. Every `[L]` is under *Open questions*. Every raise names its `run:` or second
    source. The review fixes of the batches are carried: H5d's spawn 41 (sizes 0 and 1 `[C]`, `0xFFFF` `[I]`) and spawn
    42 (206, 228, 298, 528 `[C]`, 334 `[I]`) raised in part; H4a's special 54 `[C]` at r = 0 only with the `+ r` `[I]`;
    pool 12's "five" `boss` classes; S3a's pool 22 recounted in part; S3b's special 43 split (already in E1); S3b ruling
    1's composition for stats 19 and 45. The six contradicted statements are corrected in the text.
  - **Anchors.** All 642 `fn:`/`data:` anchors of the four specs resolve in `re/symbols.csv` (script). objdump of the
    pinned image: `MonStats2CompList`'s list-15 test, count skip, cap and store (0x0065712C–0x00657190); the placed-bit
    refusal (`Stacks` at 0x005A4A09, bit test 0x005A4A1E, `jne` 0x005A4A25); the doomknight draws and stores
    (0x00573D68–0x00573DAC); Radament's `Range(5)` and `add ebx, 2` (0x005A4CD1–0x005A4CE0); `PresetFallenVariant`'s
    `BaseId` read and its 0x13 / 0x3A compares (0x0054E2C7–0x0054E2E9); the tick's `test eax, 0x7FFF`, `+0x78` and
    Levels `+0x2E` tests (0x0054F089–0x0054F0AA); `WandererSpawn`'s act bound and pair reads (0x0054EF59–0x0054EF78);
    `UModFast`'s `idiv` (0x005A1951).
  - **Spot-checks** (the five offered, then the sections listed): pool C1 (H4b), stats A1 `MulDiv` (S1f), special G5 (H4a special
    48), special I4 (H4b special 72), spawn K's class list (H4a spawn 5/49) hold against their sections. Also pool B4,
    the `+0x025` sum and cap split, the caps, E's classic and `boss` lines, `MonLvl` row and clamp split, the bonuses,
    the gate, the picks, `MonRegionFindAdd`, `RegionActClass`, pool 27; stats B3, B7, B10, B12, C1, D4, F3, G, G1, G3;
    special B1, B4, C1, C3, the mod table's split rows, G1 and the tails, H's MonPlace cases, I1–I4, J; spawn A1, B,
    C1, E3, H2, H3, H5, I1, K. Six fixes below; the rest hold.
  - **Rulings.** (a) Scope: a fair reading. Phase 3 runs per cluster once its batches are accepted, so the round folds
    every accepted move of S3a, S3b, S1f, H4b, H4a and H5d for these specs, and pool 5 and 24 by inventory § 2.2. (b) The
    new spawn § B bullet ("the Chaos Sanctuary test was met 91 times, all with byte 0, each followed by an open gate") is
    admitted: it records what H4a logged on the open side, which the gate's fall-through already gives, and spawn 11's
    closed state stays `[I]` as the shortfall says. (c) stats C1's `camel`: the H4b review raised stats 23 whole and made
    the camel an optional H4a piece, so the `[C]` sentence that names the camel unmet stands. (d) The items left to other
    clusters are accepted as listed: drlg/lifecycle H2b's restore wording (H4b special 74's correction), items/quest-drops
    48 (H4a), player/creation D1 (S3b (d)), drlg/collision's H5d parts. (e) Plan 0037 is closed (`done/`), so the
    one-at-a-time rule for monsters/stats has nothing to wait for. (f) The wiki refresh (W4 on wiki/monsters and
    wiki/seed-to-world) goes to a spec-writer follow-up entry.
  - **Fixes applied (6):** (1) overclaim: pool § Consumers' `MonRegionFindAdd` `[C]` stated "raising `nEntries` but not
    `nPool`" and the call's arguments, which the S3a raise does not list (they are the model's reading); moved to the
    `[I]` bullet. (2) stale cross-reference: pool's *game seed is shared* note still said "unit proxies" for draw 3, which
    rng/0002 names the store (`NPCSTORE_CtlCreate`); reworded. (3) misread: stats B12 said each run:2026-10-20-chain
    creation came "with its two items"; one item each, two in all. (4) misread: special § H's `[I]` bullet listed level
    6's `PresetFallenVariant` results among the unlogged ones; level 6 is the logged case, removed from the list. (5)
    omission: spawn's `spawnCol` 1 and 3 mask row cited only the H4b run for counts that are mostly kept-log calls (157 of
    159, 438 of 451); the kept runs named and the counts split. (6) overclaim: spawn K1's header put the whole gate under
    `[C]`, while its bullet keeps the mask width and the room `+0x78` test `[I]`; the header now says so.
  - **Research map:** the monsters/pool, spawn, special and stats rows rewritten whole with the new counts and dates.
  - **Backlog:** review request
    [s38m review](../backlog/archive/2026-10-27-spec-writer-architect-review-lane-s38m-plan-0038-phase-3-monsters.md)
    closed; new spec-writer entry
    [wiki refresh after the monsters cluster](../backlog/archive/2026-10-27-architect-spec-writer-wiki-refresh-after-the-plan-0038-phase-3.md).
  - **Ledger:** the lane row's usage filled from the orchestrator (412 899 tokens, 109 tools, 26 min), verdict and fixes:
    overclaim 2, misread 2, stale cross-reference 1, omission 1; the review row's usage left "—".
  - **Next:** merge `lane/s38m`; the wiki refresh; the remaining Phase 3 clusters as their batches are accepted.
- **2026-10-27 — Phase 3, the drlg/collision cluster (spec-writer, `lane/s38n`, from `main` `0848879`; `main` `4fe6362`
  merged after the spec commit).** Readiness, from the per-spec inventory files' *Batch* column, § 5 and the § 2.6 moves:
  drlg/collision's batches are S4a, S4b, H5b and H5d, all accepted (H5d on 2026-10-27); no collision row is in H6e2. The
  other clusters still wait: save/d2s H1a, H1b; data/excel H3b (and the plan 0039 fold); data/strings and data/README H3b;
  items/uniques-sets H1a (us 21); items/cube H6a; items/sockets-runewords H6b; items/vendors H6c; items/quest-drops H6e1,
  H6e2; hirelings H1a, H1b, H6f; player/creation H1a, H6g; objects H6e2. The monsters cluster is merged (`lane/s38m`).
  - **drlg/collision** {C 111, I 61, L 9} → **{C 157, I 35, L 7}**, `updated:` 2026-10-27. Raised from S4a: rows 6, 7, 12, 13,
    15–18, 20 (`BlocksVis` half), 29 (missiles), 31 (sizes 1, 2), 32 (all but the player), 33, 38, 41, 42 ×2, 43, 44, 47, 49;
    S4b: 10 split, 26 restated with the 240 / 124 counts (its correction (d)), 4 restated as no stock input; H5b: 27, 37 (`0x400`),
    39; H5d: 5, 8, 19, 24, 30 ×2, 36, 45 (228, 298 flag 0, 528), in part 1, 21 and 46. **Correction** (H5d (a)/(f)): F2's
    pattern upgrade is for `npc` or `inTown` with `interact` clear; the `inTown` half `[C]`, the `npc` half and the `+0xC4`
    branch `[I]`. Kept `[I]`: rows 2, 9, 11 (shortfalls), the d-none statements (3, 4, 25, 37's `0x804`, 45's 334) and the
    named remainders. *Open questions*: three `[L]` struck (sizes 0/1, `SpawnClassCellTest`, NPC patterns), one new (the
    `npc` half and `+0xC4`), the `Position` levels narrowed to the operand.
  - **Backlog:** closed the S4a corrections entry and the H5d entry (its monsters parts on `lane/s38m`); annotated the S4b
    corrections ((a) waits for objects) and H5b entries (objects waits for H6e2). New: the counts entry to the architect
    [s38n counts](../backlog/archive/2026-10-27-spec-writer-architect-s38n-drlg-collision-counts-for-the-research-map.md) (research
    map; W4 on wiki/levels and wiki/monsters, proposed for the open wiki refresh entry) and the review request
    [s38n review](../backlog/archive/2026-10-27-spec-writer-architect-s38n-review-drlg-collision-phase-3.md).
  - **Next:** architect review of `lane/s38n`; objects after H6e2.
- **2026-10-27 — `lane/s38n` review (architect): accept with fixes.** Phase 3, the drlg/collision cluster, reviewed at
  `58fdde0` (`9e5c05a` the spec, `17c7346` the merge of `main`); `main` `8b8f4ec` was already in the lane (merge a no-op;
  backlog `archive` clean). The spec diff was read against the S4a, S4b, H5b and H5d sections of
  [drlg/0005](../findings/drlg/0005-collision.md), the inventory rows and the H5d review's rulings. objdump of the pinned
  `Game.exe`, no Ghidra: `MonIsNpc` 0x0063E89A–0x0063E8C5 (`+0x0D` tested against `.rdata` 0x006CE268 = 1, then
  0x006CE270 = 4, then `+0xC4` bit 31); `MonSpawnTry`'s ring branch 0x005B2B7E–0x005B2BA6 (`spawnCol` = 1, then 258–263
  and 153); the three `TileCollisionUpdate` calls 0x0066E822, 0x0066E8B6, 0x0066E916 (return 0x0066E91B); the item
  `RectOrWH` call 0x00620ACA and `UNIT_CollMark`'s `SizeMark` call 0x0064954C; the `SpawnClassCellTest` calls the spec
  gives as call sites (0x005B2D90, 0x005F6AE5, 0x005F9F9D, 0x005E62BC; the finding gives their return addresses, + 5).
  Counts by script over the body: {C 157, I 35, L 7}, as filed and unchanged by the fixes; no `[L]` before *Open questions*.
  - **Fixes (3):** (1) omission: the Constants row of the `spawnCol` 1 and 3 masks anchored its 271 and 837 calls to
    run:2026-10-27-sweep-collision alone, while they are counted over the 1 330 kept logs and the nine sessions (the
    `lane/s38m` fix 5 again, in this spec); bit 2's `0x80` writer anchored the same way. Both now name the kept runs and
    say where they were counted. (2) overclaim: bit 13's row named its writers "NPCs with `interact` clear" inside the row's
    `[C]`, while F2 keeps the `npc` half and the `+0xC4` branch `[I]`; the cell now says patterns 3 and 4 and points to F2
    for who takes them. (3) misread: "exercised since", "reached since" and "seen since" a 2026-10-27 or 2026-10-19 run for
    the `0x01C0`/`0` masks (C2's open question), the door `0x400` and grid `0x04` (open questions): the earlier runs' logs
    held them, the later run counted them; reworded.
  - **Rulings.** (a) **Readiness: drlg/collision did not wait on H6e2.** The inventory's
    [drlg-collision](0038-inventory/drlg-collision.md) *Batch* column holds S4a (20 rows), S4b (5), H5b (2), H5d (12) and —
    (10), no H6 batch; H6e2's row in inventory § 5 lists quest-drops 1, 30, 33–35 and objects 48 only. The orchestrator's
    prompt and `lane/s38m`'s annotation were wrong; the objects cluster is the one that waits on H6e2. (b) **Every raise
    names its `run:`** and stays within the batch reviews: collision 21 is `[C]` for the `inTown` half only, with the `npc`
    half and `+0xC4` `[I]` and one `[L]` under *Open questions*; collision 46 has only the step `[C]` (one draw per lookup,
    none on zero matches, H5d (c)), the operand `[I]`; 45's 334 is `[I]` with the no-stock-source bullet (d-none). (c) The
    split statements are honest: the `TileCollisionUpdate` entry row and § B (the call `[C]`, the write `[I]`), G3 (the
    entries the floods read `[C]`; (3, −1), (4, −1) and orientations 4, 13, 15 `[I]`), bits 1 and 2 (the writers only `[C]`,
    the readers named; point to check (3) stands), bit 11 and the door row (`BlocksVis`, `0x400` `[C]`; `0x804` `[I]`), F1 and
    F3 (missiles and sizes 1, 2 `[C]`), the player's size `[I]`. (d) The B-section bullet's 0x0066E91B is the return address
    of the re-pick call at 0x0066E916 (objdump); point to check (2) stands. (e) Every accepted raise, in-part and
    correction of the four batches is reflected, and the kept `[I]` (rows 2, 9, 11, the d-none rows 3, 4, 25, 37's `0x804`,
    45's 334) are listed in the counts entry. (f) **Wiki:** wiki/levels (§ *The collision grid and logic regions* and the
    *Collision* bullet of its untested list are stale) and wiki/monsters (date only) are folded into the open wiki refresh
    entry, annotated.
  - **Research map:** the drlg/collision row rewritten whole (C 157 / I 35 / L 7, updated 2026-10-27).
  - **Ledger:** the lane row's usage filled from the orchestrator (267 684 tokens, 85 tools, 17 min), verdict and fixes:
    omission 1, overclaim 1, misread 1; the review row added with usage "—".
  - **Backlog:** review request and counts entry closed (archive); the wiki refresh entry annotated.
  - **Next:** merge `lane/s38n`; the wiki refresh (now with wiki/levels); objects after H6e2.

- **2026-10-27 — The wiki refresh after the monsters and drlg/collision clusters (spec-writer, `lane/swk`, from
  `main` `e88e8e2`).** [wiki/monsters](../wiki/monsters.md) and [wiki/levels](../wiki/levels.md) are refreshed over the
  re-tagged monsters/pool, spawn, special and stats and drlg/collision, and
  [wiki/seed-to-world](../wiki/seed-to-world.md)'s stats date is bumped. The six corrections are carried at the specs'
  tags, the raised statements are said as confirmed, and the kept `[I]` parts are said in words. wiki/levels'
  § *The collision grid and logic regions* and its *Collision* bullet are rewritten whole. W4 is clear (0 of 60); the
  gate is green. The specs `lane/s45p3` holds and the economy and randomness pages are untouched.
  - **Backlog:** the refresh entry is closed
    ([archive](../backlog/archive/2026-10-27-architect-spec-writer-wiki-refresh-after-the-plan-0038-phase-3.md)), and
    the review request is filed
    ([swk review](../backlog/archive/2026-10-27-spec-writer-architect-review-lane-swk-wiki-refresh-after-plan-0038.md)). It also
    notes that drlg/lifecycle § I lags spawn § K on the wanderer roll.
  - **Next:** architect review of `lane/swk`.
- **2026-10-27 — `lane/swk` review (architect): accept with fixes (4).** `main` merged into the lane first (already up to
  date; `backlog.py archive` a no-op). Every changed statement on wiki/monsters, wiki/levels and wiki/seed-to-world was
  checked against the spec section it restates (pool C1 and E; spawn A, B, D, E, I and K; special B4, C, G, G5, H and J;
  stats B7, B10, A1, F3, G3 and the `Align` bullet; collision G1–G3 and I2; lifecycle § I).
  - **Fixes (on the pages):** (1) wiki/levels *Wanderers*: "that draw passes 1 time in 32 768" moved into the code-read
    sentence, with the one pass unable to tell the mask's width (spawn K and lifecycle I1 keep it `[I]`). (2) wiki/monsters
    *Wanderers*: the "1 in 32 768" and the `MonWndr` condition said by the code with the no-player test, since the one
    pass came in a `MonWndr` level and lifecycle I1 keeps that test `[I]` (rule 1, weaker tag). (3) wiki/monsters' stats
    paragraph: the emulation's "overflow included" scoped to all but the one faulting input (stats A1). (4) "three were
    logged" made "three such classes" (special C: classes 59, 397 and 645).
  - **Rulings.** (a) **`Rarity` 0:** the page's weaker wording is right. spawn D's `[C]` covers a case no run met (no stock
    region holds a `Rarity` 0 entry; the run confirms the walk, not that outcome), so spawn D is reconciled down to pool's
    `[I]`, not pool up:
    [entry](../backlog/archive/2026-10-27-architect-spec-writer-spawn-d-rarity-0-tag-to-pool.md). (b) **drlg/lifecycle § I** is
    stale against spawn § K (the roll's draw and no-spawn branch are `[C]` on run:2026-10-21-sweep-monsters-a); it was not
    filed, so it is filed now together with spawn K1's header, which leaves the `MonWndr` ≠ 0 test under `[C]` although
    the one pass cannot separate it (the `lane/s38m` review missed this):
    [entry](../backlog/archive/2026-10-27-architect-spec-writer-lifecycle-i-and-spawn-k-wanderer-gate-reconcile.md). (c) The
    edits beyond the entry (wiki/levels' *Wanderers* paragraph and the room-lifecycle bullet citing spawn § K) are within
    rule 7 and stand, with fix (1). (d) "By the formula" (`fast`/`fanatic` at `Velocity` 8 and 9, stats G3 `[I]`) and "by
    the code" (`druidhawk`, stats F3 `[I]`; `Rarity` 0) match the specs' tags. (e) The `based_on` dates equal each spec's
    `updated` (pool, spawn, special, stats, collision 2026-10-27; the rest unchanged), and spawn is rightly added to
    wiki/levels.
  - **Ledger:** the lane row's usage filled from the orchestrator (233 468 tokens, 61 tools, 11 min), verdict and fixes:
    overclaim 3, other 1; the review row added with usage "—".
  - **Backlog:** review request closed (archive); two spec-writer entries filed.
  - **Next:** merge `lane/swk`; the two spec-writer entries, then a `based_on` bump on the three pages.
- **2026-10-27 — `lane/sfx` (spec-writer): the two entries from the `lane/swk` review.**
  - **monsters/spawn § D:** the `Rarity` 0 bullet split: the walk's stop rule stays `[C]` (run:2026-10-13-mon-spawn), "a
    `Rarity` 0 entry is never picked" is `[I]`, read from that walk and from `raritySum` not wrapping, with pool's "no
    stock region has one". **§ K1:** the Levels `MonWndr` ≠ 0 test (0x0054F0AA) added to the header's `[I]` list and the
    `[I]` bullet (the pass came in a `MonWndr` 1 level; no logged tick passed the mask in a `MonWndr` 0 level); the
    `[C]` bullet that `MonWndr` has no other reader is unchanged. Tags C 136 / I 43 / L 5 → C 136 / I 44 / L 5.
  - **drlg/lifecycle § I:** I1's roll draw and its `mod 100` ≥ 3 return `[C]` on run:2026-10-21-sweep-monsters-a (the
    region `+0x2C4` test split onto its own `[I]` line); the gate line's mask width marked `[I]`; the "no gate draw
    passed" bullet replaced by a `[C]` bullet for the Chaos Sanctuary pass and an `[I]` bullet for what it does not
    separate (mask width, `+0x78`, `MonWndr`, `+0x2C4`, the spawn). Made stale and fixed (rule 7): the Constants rows for
    the gate and the roll, and the open question, now "the wanderer spawn was never reached". Tags C 92 / I 77 / L 8 →
    C 96 / I 80 / L 8; `updated` 2026-10-21 → 2026-10-27.
  - **Wiki:** `based_on` for drlg/lifecycle bumped to 2026-10-27 on wiki/levels, wiki/monsters, wiki/seed-to-world and
    wiki/objects (which also lists it; its text has no wanderer statement); spawn was already 2026-10-27. No page text
    changed: the pages already take the weaker tags.
  - **Research map** (architect's): the spawn row's counts become C 136 / I 44 / L 5 and the lifecycle row's
    C 96 / I 80 / L 8, updated 2026-10-27.
  - **Backlog:** both entries closed (archive); review request filed.
  - **Next:** architect review of `lane/sfx`.
- **2026-10-27 — `lane/sfx` review (architect): accept with fixes (1).** Head `cc76e71e`; `main` merged first (already up to
  date), `backlog.py archive` a no-op.
  - **Checked.** The new `[C]` statements against run:2026-10-21-sweep-monsters-a: `h4a-manifest.sha256` (42 files) and
    `check/kept-logs.sha256` (63 kept logs) pass `sha256sum -c`; session chaos7's `RTK0` at line 97549 (level 108, room
    seed `9408b966:5d98f482`) steps to `d17d0000:3dbe6f3a`, the `WRL` seed; one more step gives `c2ef6f3a:57603f25`, low
    mod 100 = 82, equal to the `RTK1` seed, so two room draws; `sweep-check.txt`'s `wander` line (7 184 ticks, 7 183 one
    step, 1 roll, bad 0). objdump of 0x0054EFF0–0x0054F0C9: the roll's step, `mul 0x51EB851F; shr edx, 5; imul 0x64`
    (unsigned mod), `cmp ecx, 3; jge` at 0x0054F02B, `cmp [eax+0x2C4], 3; jge` at 0x0054F041; the tick's `test eax,
    0x7FFF` at 0x0054F089, `cmp [esi+0x78], 0` at 0x0054F096, `cmp byte [eax+0x2E], 0` at 0x0054F0AA. The counts match
    the gate (spawn C 136 / I 44 / L 5; lifecycle C 96 / I 80 / L 8 before the fix). No `[L]` outside *Open questions*
    in either spec.
  - **Fix (1, applied):** lifecycle's Constants row *wanderer list* raised to `[C]` on the H4a operand read (objdump and
    r2; the three readers 0x0054EF64, 0x0054EF71, 0x0054EF92 are the only instructions naming 0x00731B2C–0x00731B3B,
    re-counted here, and the bytes `0e010000 00010000 00000000 00000000` re-read), with spawn § K's anchor. Lifecycle
    C 96 / I 80 / L 8 → C 97 / I 79 / L 8.
  - **Rulings.** (a) The flagged mismatch: reconciled up, not filed (fix above); spawn's `[C]` was ruled at the H4a review
    on the S2c operand route and nothing in lifecycle's row needs more. (b) Spawn D's split and K1's `MonWndr` test move
    match the `lane/swk` rulings. (c) The two archived entries' `#log` → `#implementation-log` stand; no other entry,
    open or archived, nor `docs/backlog.md`, links plan 0038 at `#log`. (d) The research map's spawn and lifecycle rows
    rewritten (counts, updated date, the `lane/sfx` clauses; lifecycle's "the wanderer roll and spawn" open now "the
    wanderer spawn").
  - **Ledger:** the lane row filled (verdict, fix 1: under-tag 1, usage from the orchestrator); review row added, usage
    "—". Seen lines: spec-writer review-fixes rule 8, architect review-fixes rule 3.
  - **Backlog:** review request closed (archive).
  - **Next:** merge `lane/sfx`.

- **2026-10-27 — H1b (`d2s-play`) rotated at about 4 h (reverser, `lane/h1b`, harness slot 1, from `main`
  `0e3f501`).** Slot 1 is stopped and its saves directory restored (empty, no aside); no game, driver, pilot, gdb or
  wait loop of the lane is left running. Sessions and checks are done; the write-up is not. Nothing is claimed yet: no
  statement raised, no § 2.6 entry, no review request.
  - **Tools** (this commit): logger `tools/gdb/d2s-h1b.py` (sha256 `8a27dc8c…`; sourced after `d2s-io.py`, unchanged,
    and `pilot.py` by `tools/gdb/d2s-h1b.gdb`, `bcd53b34…`; `d2s-h1b-hire.gdb`, `05c0b954…`, adds the hirelings
    loggers): who saves (`PSV2`, `SVCL`, `SVCB`, `SHUT`, `AUTO`), the join chain (`JCH`), section cursors of
    `D2S_WriteSave`/`D2S_ReadSaveV92` (`WSEC`/`RSEC`), hotkeys (`HOTK`/`HREF`), graphics bytes (`GFX`), the
    mercenary header write and read (`MHW0`–`MHW2`, `MHWD`, `MRX`, `M5726`), `D2S_LoadFinish` (`LFG`, `LFB`, `LFS`,
    `LFX0`/`LFX`, `LFE`), item stats (`RIST`, `SBX`), runeword (`RWW`, `RWR`), bit 13 (`B13S`, `B13C`, `SETF`, `GOLD`,
    `COPY`, the watchpoint `WTCH`). **Two revisions were used:** revision 1 (the committed file without `h1b_full`,
    `h1b_wskl` and their `full`/`WSKL` lines) for sessions dead, tcpip, shut, hell-r3, hire, rw, qr, qrh; revision 2
    (committed) for rt-r2, drop, qr-r2, qrh-r2. The checker skips the property groups where `full` is absent. Runner
    `tools/h1b_sessions.py` (`d11afb5c…`), steps `tools/gdb/h1b-tcpip-host.steps`, checker `tools/sweep_h1b.py`
    (`c0063a8b…`; runs `d2sio.py check` first), recipes `h1bsor`, `h1bdead`, `h1bweak`, `h1bhire` (on
    `smpsor-l50.d2s`), pinned in `tools/test_d2s.py` with `questrewards`/`questrewardsh` (the backlog pin request).
    `test_d2s.py` RecipeTest pins pass; `test_every_recipe_has_a_base` and `test_mp_saves_check` fail on `main` too
    (other lanes' mp recipes), not touched here.
  - **Sessions** (slot 1, run:2026-10-27-sweep-d2s-play, `workspace/logs/h1b/`; manifests `h1b-manifest.sha256`
    `18f92562…` (12 logs, the check output, the six input saves) and `h1b-manifest-dev.sha256` `122aca67…` (dev logs
    in `dev/`: rt (revision 1, no `WSKL`: its two d2sio left/right-mouse mismatches per swapped write are the d2sio
    model's, see below), hell and hell-r2 (no death: the pilot stood, then stopped at the 1-point life orb), drop
    27110 (waypoint row 1 is the town)). Kept: rt-r2 (27101, swap `w`, 75 s autosave control, reload), dead (27102,
    tool-built dead Desert merc id 7 name 20), tcpip (27103, one-client TCP/IP host), shut (27104, Alt+F4 in game),
    hell-r3 (27105, death in Hell River of Flame with the Rogue killed in play; corpse; reload), hire (27106, Kashya
    hire), qr/qr-r2 (27107), qrh/qrh-r2 (27108), rw (27109, sample `qitbarb`'s runeword), drop (27111, City of the
    Damned, three drops). Check: `systemd-run --user --scope -p MemoryMax=4G python3 -I tools/sweep_h1b.py check
    workspace/merged/data/global/excel $(ls workspace/logs/h1b/*.log)` → `check/sweep-h1b-check.txt`: **2 502 H1B
    comparisons, 0 failing**; every d2sio part 0 mismatches except the left/right mouse words of swapped writes
    (superseded by the `WSKL` group: the writer reads the unit's current skill, `0x00620190`/`0x006201D0`, not player
    data `+0x74`/`+0x70`, which a swap leaves 0) and hell-r3's `RITEM` count (25 = 14 loaded + 11 `ItemCopy`
    recreations of the corpse items at the death, matched by 11 `COPY` lines).
  - **Findings so far (for the ledger; cite the check file):**
    - who saves: SP `PLRSAVE_Save` from `0x0052CA5F`/`0x0052C940` (Save and Exit, Alt+F4) and **`0x0057FD88`, the
      death path, in single player** (hell-r3: the write before the respawn, status word `0x0F28`, bit 3 set); game type
      3 + host callback 0 → file in every SP write; TCP/IP game type 2 → `0x00532340` (`SVCL`), no file by the server;
      host callback `0x00883D50` 0 in every session; `AutosaveTick` called throughout (up to 3 000 calls) and never
      saved; `SaveAllOnShutdown` entered once per game exit (ret `0x0044F2FE` SP, `0x0044D052` TCP/IP) and never saved
      (its game list at `0x00882D38` already empty). Join chain SP: `ClientAddPlayerToGame`←`0x005301E9`,
      `PlayerLoad`←`0x00539809`, `PLRSAVE_ReadFile`←`0x005344E0`, `D2S_ReadSave`←`0x0053447A`; TCP/IP: no
      `PLRSAVE_ReadFile`, `D2S_ReadSave`←`0x00534563`.
    - sections: every write's final-pass cursors = the file's sections; the scratch pass sizes = final; reader order
      and offsets as the finding; `D2S_ReadMercHeader` at the merc offset without moving the cursor; `0x005726C0(1)`
      exactly when a merc was made; the all-zero header (hire read 1) → no merc, load continues.
    - header: weapon set bit 0 written 1 after `w` and read back into client `+0x45C`; swap A/B = player data
      `+0x84`/`+0x80` (values 54/48 after the swap, 42/43 before) written and read; hotkeys with the `0x8000` flag
      (slot 2 `left:Teleport` → `0x8036`), item refs 0 only; graphics/colour bytes = the image after `0x0063E510`
      (non-`0xFF` bytes present); merc header seed/name/id/exp/dead = sources in tool-built (12345/3/0, 54321/20/7),
      hired (2573073805/0/1, exp 52424400) and killed-in-play (bit 16 from the dead test, merc mode 12) cases.
    - `D2S_LoadFinish`: gold 900 000 > 800 000 → 0, bank 3 000 000 > 2 500 000 → 0, 500 000 kept; stamina = max; 6/8
      restored; 67–69 = 100; stat 30 = `EXP_GetThreshold(class, L)` = experience.txt row L (level 80 → 742 730 244 with
      experience 750 000 000 in dead, so it is not the experience; level 1 → 500): the threshold of level L + 1, as the
      spec's "table at level + 1" counting the MaxLvl row.
    - items: maxhp/maxmana full stat = file << 8 (5 → 1280, 1 → 256) and written back >> 8; stat 326 = 1 after group
      57 (Septic dagger); group 52 (Ginther's Rift 50/120); rebuilt 21–24 and 68 = weapons.txt (an ethereal `lsd`:
      the ×3/2 branch met; no low-quality item); stat 356 = file 0 and 2 (qr-r2, qrh-r2); runeword 20639 read into
      `+0x38` and written from `Runes +0x82`.
    - corpse: one corpse, 12 bytes, 11 equipped items (mode 1), written and read; no mode 3/5 item in any save
      (rows 77/78 → d-none per their route). bit 13: three drops set at create (`0x00558EA8`, params `+0x2C` 0), each
      cleared on the ground (mode 3) by `UnitFrameReset` (ret `0x0053B049`) inside the tick's `ActUnitsFrameReset`
      call; no gold-pile (`DropGoldPile`) and no pickup of a saved item; `ItemCopy`'s clears seen 11 times (death);
      the watchpoint armed (`WTCH0`) but logged **no hit**, not even the logged `SetFlag` writes: row 110's "only
      through `ITEMS_SetFlag`" has no working control → shortfall.
    - Proposed ledger (48): raised 4, 21, 25, 33 (2), 34 (2), 35, 37, 39 (2), 40, 41, 42, 43, 55, 56, 57, 108, 111,
      112, 113, 125, 127, hirelings 24; in part 2 (no-callback half), 6 (death caller and no-autosave; 0x0052E2A0 not
      reached), 18 (file and client branches), 31 (item refs 0 only), 48 (name reset unreachable: the builder refuses a
      name past `+0x116`), 60 (negative gold), 72 (count ≥ 2 refusal, the first u32), 73 (no golem item), 83 (gold and
      realm), 88 (`0xFFFF`), 102 (low quality), 115 (copy seen, socketed copy not), 116 (no pickup of an item with the
      bit), 118 (no negative value: arithmetic not separated); shortfall 1, 3, 19, 110, 114, 117 (no separating case:
      rule 10), 124 (the builder refuses a lone follower: archivist entry); d-none 77, 78. Recount before filing.
    - S1a pieces met (rows stay S1a): hired merc (20), swapped weapon set (24), left-button hotkey (32), group 52
      (123/130/138 in part). Not met: cursor item (71), automagic class item (86/103), lone `fire-min` (128).
  - **Next (resume):** (1) optional: rerun dead, tcpip, shut, hell, hire, rw under logger revision 2 so every kept log
    has one tool revision (or record revision 1 by its diff); (2) write run:2026-10-27-sweep-d2s-play in
    `findings/save/experiments.md`, the "Plan 0038 batch H1b" sections in save/0001 and hirelings/0001, the inventory
    § 2.6 H1b block with totals against `main`, symbols (rule 14: `D2S_WriteMercHeader`, `D2S_ReadMercHeader`,
    `D2S_LoadFinish`, `D2S_WriteCorpses`, `D2S_ReadCorpses`, `D2S_ReadMercItems` I → C), the archivist entry for a
    lone-follower builder key, the review request and the metrics row ("—").
- **2026-10-27 — H1b (`d2s-play`) filed (reverser, `lane/h1b`, harness slot 1; resume after the rotation).** Merged
  `main` `e88e8e2` first (the plan log conflicted, both sides kept; `backlog.py archive` a no-op).
  - **Revision 1, decided:** of the eight revision-1 logs, only rw lost a check a row needs (the write-side runeword
    field = `Runes +0x82`, gated on `full` in `sweep_h1b.py`); the property groups of the others are met on the four
    revision-2 logs, and no in-part remainder depends on the revision. So rw was rerun under revision 2 (rw-r2, seed
    27109, about 5 min, slot 1 stopped and its saves restored after), and revision 1 is recorded by its diff in the run
    record; the other seven are not rerun. Check re-run on the 13 logs: **2 798 comparisons, 0 failing**
    (`check/sweep-h1b-check-r2.txt` `f44b92e0…`, manifest `h1b-manifest-r2.sha256` `f0e88782…`; the first check and
    its manifest kept as they were).
  - **Recount:** the rotation note's "three drops" is five (ids 27–31, `check` B13S/B13C 5); `AutosaveTick`'s counts are
    the logger's sample (call 1 and every 500th), up to 6 500. The ledger the caller relayed (28 / 16 / 7 / 2) did not
    sum to 48; the row list recounts to **raised 25, raised in part 14, shortfall 7, proposed d-none 2: 48** (save-d2s
    45 + hirelings 1 + rows 117, 124).
  - **Filed:** run:2026-10-27-sweep-d2s-play in `findings/save/experiments.md`; "Plan 0038 batch H1b" sections in
    save/0001 and hirelings/0001 (hirelings § F and the summary's header sentence now `[C]`; two save/0001 open
    questions annotated); inventory § 2.6 H1b block, totals against `main`: **static 567, harness 523, c-emu 0, blocked
    417** (d-none 291), **deferred 2, raised 17: 1 526**; symbols I → C (rule 14): `D2S_WriteMercHeader`,
    `D2S_ReadMercHeader`, `D2S_LoadFinish`, `D2S_WriteCorpses`, `D2S_ReadCorpses`, `D2S_ReadMercItems`.
  - **Backlog:** archivist entry
    [2026-10-27-reverser-archivist-h1b-d2s-build-test-state-keys-for-a](../backlog/archive/2026-10-27-reverser-archivist-h1b-d2s-build-test-state-keys-for-a.md)
    (lone follower, merc name past range); spec-writer entry
    [2026-10-27-reverser-spec-writer-h1b-save-d2s-and-hirelings-raises](../backlog/archive/2026-10-27-reverser-spec-writer-h1b-save-d2s-and-hirelings-raises.md)
    (held for the review); review request
    [2026-10-27-reverser-architect-review-lane-h1b-plan-0038-batch-h1b](../backlog/archive/2026-10-27-reverser-architect-review-lane-h1b-plan-0038-batch-h1b.md).
  - **Next:** the `lane/h1b` review.
- **2026-10-27 — `lane/h1b` review (architect): accept with fixes (6).** `main` `3c90008` was merged into the lane
  first (`1fdab87`; the plan log and the ledger conflicted, both sides were kept; `backlog.py archive` was a no-op).
  Re-checked with no harness and no Ghidra. `h1b-manifest.sha256` and `h1b-manifest-r2.sha256` pass from
  `workspace/logs/h1b`. `h1b-manifest-dev.sha256` passes from `workspace/logs/h1b/dev` only (fix 4). The check rerun
  under `systemd-run --user --scope -p MemoryMax=4G` (`sweep_h1b.py`, which runs `d2sio.py check` on each log) gives
  **2 798 comparisons, 0 failing**, byte-identical to `check/sweep-h1b-check-r2.txt` (`f44b92e0…`). objdump confirms
  the anchors: the 13 logged return addresses (0x005301E9, 0x00539809, 0x005344E0, 0x0053447A, 0x00534563,
  0x0052CA5F, 0x0052C940, 0x0057FD88, 0x00558EA8, 0x0055335C, 0x0053B049, 0x0044F2FE, 0x0044D052) each follow a call
  to the named function, and the reader calls are at 0x0056B313/0x0056B32D/0x0056B343. The ledger recounts to the
  inventory: 42 H1b rows of 45 statements, plus rows 117 and 124 and hirelings 24, give 48 = 25 + 14 + 7 + 2.
  - **Fixes:** (1) row 4's chain skipped a frame on each path: 0x005344E0 is inside `sub_005344B0_PlayerLoadFromFile`
    and 0x00534563 inside `sub_00534520_PlayerLoadFromClient`, each called once from `PlayerLoad` (0x005345DB,
    0x005345FB). The logged returns stay `[C]`; the two links are `[I]`. (2) Row 2's `[C]` is scoped to the outcome.
    `AutosaveTick` first tests `0x00730FFC` (0x0052D353), then the per-client time tests, then the callback
    (0x0052D3D9), and the logger breaks only at the entry, so the gate that stopped the save is not shown. (3)
    `D2S_WriteMercItems` was raised I → C (rule 14, on the same evidence as `D2S_ReadMercItems`, row 73), which makes
    seven symbols in all. (4) The record states the dev manifest's directory. (5) The record names every save copy
    the reruns overwrote (rt-r2, qr-r2, qrh-r2, rw-r2 and drop 27111 each wrote under the session name without the
    suffix). (6) Row 1's "game list already empty" is a reading, because the `SHUT` line logs only the return and the
    callback.
  - **Rulings:** (a) the seven revision-1 logs are accepted as they stand. Revision 1 drops only `full` and `WSKL`, and
    every check those gate (stats 7/9, 326, 52/53, 356, the runeword write, the swap source) is met on revision-2
    logs. No remainder of a row raised in part is met by an item that only a revision-1 log holds. (b) The rw-r2
    overwrite is accepted: no check and no claim reads a copy. The runner should key copies on the log name (reverser
    entry item 3; reverser review-fixes rule 6, Seen). (c) The single-player death save at 0x0057FD88 does not
    contradict "no single-player autosave". It is an event save from the death path the spec already lists, and with
    callback 0 it is unconditional (0x0057FD4B–0x0057FD62). The spec's "Nothing was written during play in the runs"
    holds for run:2026-10-12-d2s-io only (spec-writer entry). (d) Rows 1, 3 and 19 stay **shortfalls, not d-2c**: a
    one-client TCP/IP host counts as one client (§ 3's six-row bullet is settled), and d-2c needs a second client to be
    what reaches the code. For rows 3 and 19, the only writer of the host callback `0x00883D50`, 0x0052C0E0, has no
    call, jump or absolute or RVA pointer in the image (objdump). If Ghidra xrefs agree, rows 3 and 19 and the callback
    halves of rows 2 and 18 become d-none
    ([2026-10-27-architect-reverser-h1b-review-host-callback-setter-and-d2sio-model](../backlog/archive/2026-10-27-architect-reverser-h1b-review-host-callback-setter-and-d2sio-model.md)).
    (e) Row 110's shortfall is right. The watchpoint armed on drop 27's flags missed a clear that `B13C` logged, so it
    was not live, and no absence is claimed under it. Rows 111–113 rest on breakpoints, not on the watch. (f) Row 39's
    tightened read half stands. The tool-built dead mercenary has no source of deadness but header bit 16, and each
    read of it gave a mode-12 mercenary with the dead test 1; hell-r3's read 1, with the bit clear, gave a living
    Rogue. (g) Stat 30 `nextexp` is right: it is the experience.txt row whose `Level` is L, which is index L + 1
    counting `MaxLvl`, because `EXP_GetThreshold` reads dword `class + 8·L + 8` (0x00611814). Level 1 → 500 rules out L
    + 1, and dead's 750 000 000 rules out the experience. The spec-writer entry asks for unambiguous wording. (h) Rows
    77 and 78 move to **d-none** by their own route, and row 56's raise stands (`D2S_ReadMercHeader`'s `eax` is passed
    untested, 0x0056B318–0x0056B32A, into the `D2S_ReadMercItems` call at 0x0056B32D). (i) The d2sio mismatches are explained. A d2sio model fix is filed (reverser entry item 2), not
    blocking. (j) **H1a may start**: the family rule H1b → H1a is met.
  - **Totals** (against `main` `3c90008`, no inventory change since `e88e8e2`): **static 567, harness 523, c-emu 0,
    blocked 417** (d-none 291, d-edit 73, d-sim 28, d-2c 7, d-owner 10, d-0032 8), **deferred 2, raised 17: 1 526**,
    inventory § 2.6 H1b block.
  - **Ledger:** the resume row's usage was filled from the orchestrator (212 206 tokens, 100 tools, 22 min), with the
    verdict and 6 fixes: overclaim 2, omission 2, under-claim 1, other 1. The review row was added with usage "—".
  - **Backlog:** the review request was closed (archive). The spec-writer entry
    [2026-10-27-reverser-spec-writer-h1b-save-d2s-and-hirelings-raises](../backlog/archive/2026-10-27-reverser-spec-writer-h1b-save-d2s-and-hirelings-raises.md)
    was **released**, with four points added. The reverser entry above was filed. The archivist entry is unchanged.
  - **Next:** merge `lane/h1b`; then H1a (`d2s-load`).
- **2026-10-27 — H6e2 (`quest-items`) started; rotated at the first checkpoint (reverser, `lane/h6e2`, harness slot 1,
  from `main` `3c90008`; `main` `2637b08` merged at the checkpoint).** Run id run:2026-10-27-sweep-quest-items, record in
  [items experiments](../findings/items/experiments.md#run2026-10-27-sweep-quest-items), evidence so far in
  [items/0010 § Plan 0038 batch H6e2](../findings/items/0010-quest-drops.md#plan-0038-batch-h6e2-run2026-10-27-sweep-quest-items).
  - **Built:** logger `tools/gdb/quest-items.gdb` + `tools/gdb/quest-items.py` (object operates with record words,
    object event 7 and its targets, `GiveItem`, the chest gold, `ObjectChestDrop`, `PlayerFindItemByCode` with its
    stat-356 reads, `ItemQuestGate` with its result and tail, the orifice); session driver `tools/h6e2_sessions.py`
    (13 sessions listed: gate-done, gate-fresh, radament, cube, cube-held, staff, staff-nm, heart, brain, eye, tome,
    inifuss, tristram); checker `tools/sweep_h6e2.py check` (chest, object, event7, dup, gate models); four recipes
    `tools/d2s_recipes/quest-h6e2-*.json`; saves in `workspace/scratch-h6e2/saves/`.
  - **So far:** one kept session (`gate-done`, by hand): item-move gate 8 cases, 0 mismatches (qd 35 raised in part
    when filed; the word identities, `xyz`/`g33`/`tr2` and the unique branch still open). Static reads for the checker,
    all `[I]`: a chest opens once (mode test `0x00545850`); the Act II chest callbacks; **a correction** to E1 for the
    three Khalim chests (gold first, then the parts, then the chest drop; each counts a player holding neither the part
    nor `qf2`); the Wirt / Inifuss / Malus / tome gates; the gate's ground-pickup route; `j34`/`mss` requested at
    quality 2 come back quality 7 (kept log 3356). Kept logs usable as a-logs for the write-up: `leg`
    (`economy2-s1-4506-wirt.log`), `j34` and `mss` (`quests-s3-3356-meph-normal.log`), the orifice's StaffPlaced bits
    (`quests-s3-3364-duriel-normal.log`, `QS` returns 0x0059DDA1 / 0x0059DDB9).
  - **Resume note.** (1) The scripted Act II descent stalled on map seed 3811: `descend` sees the Sewers Level 2
    down-stairs 9 sub-tiles away and finds no path; clicks on their label did not take them; the pilot also read the
    orbs as 0.00 through that session (a direct read later gave 0.75 / 0.79) and `wpchain` ran to its 120 s timeout
    after arriving. Next agent: try H4a's map seeds (radament 4904) or another seed per session, check `Pilot.hp()` once
    after the waypoint, and give `wpchain` a shorter timeout. (2) Then run, in this order (cheapest first): `tristram`
    (QuestAllDone: leg, the gold piles' event 7 for the qd 1 backtrace, the second click), `inifuss`, `cube`,
    `cube-held`, `radament` (ass, tr1), `staff`, `staff-nm` (the questdiffcheck duplicate), `heart` (sewer lever event 7,
    the Khalim order), `brain`, `eye`, `tome`; a `gate-fresh` hand session as in the record (drop one item, Alt, click its
    label, one at a time; walking off ended the first). (3) `sweep_h6e2.py`'s chest model already has the Khalim order;
    the altar (`vip`) gate is unmodelled (prints a mismatch if met); Malus, tome and Inifuss assume the quest object's
    `+0x09` is set. (4) The backlog entry on `objects.py`'s waypoint mode was not hit (no `objects.py` run yet). Slot 1
    stopped, saves restored (empty, no aside). Four launches so far (one kept, three development logs); the cap is ~20.
- **2026-10-27 — `lane/r1h` filed (reverser, static, Ghidra lane copy, no slot): the `lane/h1b` review's reverser
  entry, rulings (d) and (i).** Branched from `main` `2b087d2c`.
  - **Setter:** `tools/ghidra.sh findptr` (new: `re/ghidra_scripts/FindPointer.java`) and a raw byte scan both find
    nothing that reaches `sub_0052C0E0_SetHostSaveCallback` (0x0052C0E0) or `sub_00534630_PlrSaveWrapper` (0x00534630).
    The six channels are references of any type, the VA or RVA at any alignment in every initialized block,
    immediates, raw relative branches, exports and fall-through. Each channel found its control in the same run.
    The setter's two stores are the only writes of `0x00883D50` (Ghidra 38 READ + 2 WRITE; objdump 41 instructions,
    the extra one a read in undisassembled code at 0x0052BFC0). The callback lies in zero-filled `.data`. Both
    symbols were added (I). The absence is `[I]`: a target computed at run time is not excluded.
    [save/0001 § Plan 0038 r1h](../findings/save/0001-d2s-io.md#plan-0038-r1h-the-host-callback-setter-and-the-d2sio-model-2026-10-27).
  - **Proposed class moves** (inventory § 2.6 H1b block): rows 3 and 19 go shortfall → **d-none**. The callback
    halves of rows 2 and 18 are d-none as halves, and those rows stay raised in part. H1b becomes raised 25, in part
    14, shortfall 5, d-none 4: 48. Totals against `main` `2b087d2c`: **static 567, harness 521, c-emu 0, blocked 419**
    (d-none 293), **deferred 2, raised 17: 1 526**.
  - **d2sio:** `tools/d2sio.py` `2ac6e9f1…` → `29561293…`: the mouse words are compared with `WSKL` (fallback:
    player data, labelled), and a load's items stop at `LFIN2`, with the later `RITEM` lines compared with
    `COPY`/`COPY2`. `tools/sweep_h1b.py` `c0063a8b…` → `b2d9ac1a…`: the explaining wrapper is removed. The re-check
    on the 13 kept logs, run under `MemoryMax=4G`, gives **2 798 H1B comparisons, 0 failing, 0 d2sio mismatches**
    (`workspace/logs/r1h/sweep-h1b-check-r1h.txt` `c39fd4bd…`; manifest `r1h-manifest.sha256` `94f2b304…`). The
    run:2026-10-12-d2s-io logs are unchanged apart from the added `later=` field. `tools/h1b_sessions.py` now keys
    its copies on the log stem (entry item 3).
  - **Backlog:** the reverser entry was closed (archive). Review request: [2026-10-27-reverser-architect-review-lane-r1h-host-callback-setter-and-d2sio](../backlog/archive/2026-10-27-reverser-architect-review-lane-r1h-host-callback-setter-and-d2sio.md).
  - **Next:** the `lane/r1h` review.
- **2026-10-27 — `lane/r1h` review (architect): accept with fixes (3).** Merged `main` `2637b081` into the lane first
  (ledger conflict kept both sides).
  - **Checks:** `sha256sum -c r1h-manifest.sha256` passes for all 7 files (manifest `94f2b304…`). The re-check under
    `systemd-run --user --scope -p MemoryMax=4G` (`tools/d2sio.py` `29561293…`, `tools/sweep_h1b.py` `b2d9ac1a…`, 13
    logs) is byte-identical to `sweep-h1b-check-r1h.txt` (`c39fd4bd…`): 2 798 comparisons, 0 failing, every D2SIO line
    0. **Negative control:** the replaced `d2sio.py` (`2ac6e9f1…`, git `2b087d2c`) fails rt-r2 with 4 mismatches
    (`mouse[0]`/`mouse[1]` file 42/43, player data 0, two writes) and hell-r3 with 1 (`RITEM count` 25 against the
    file's 14; the label prints the runtime count first, a cosmetic slip older than this lane). The new one gives 0 on
    both, with hell-r3 at 1 034 comparisons (the added `COPY` comparison). objdump agrees on the writes and reads.
    There are 41 instructions naming `0x00883D50`, the only stores 0x0052C0EC and 0x0052C0FF. `0x00883D54` is stored
    only at 0x0052C0F1 and 0x0052C105. The `rep stos` at 0x005306B8 zeroes 0x400 dwords from `0x00882D38`, so it ends
    at `0x00883D37`. The death branch's `je` at 0x0057FD52 skips the status test when the callback is 0. The setter
    follows `ret 8` and `int3` at 0x0052C0DC–0x0052C0DF. The `.data` raw size ends at RVA `0x0034D000`. An independent
    raw scan (VA, RVA, `E8`/`E9`/`0F 8x`/`EB`/`7x`; control `PLRSAVE_Save`'s 8 calls) finds nothing for 0x0052C0E0,
    0x00534630 or 0x0052BFC0 (`workspace/logs/r1h/review/`, manifest `review-manifest.sha256` `d7aca001…`).
  - **`FindPointer.java`** is correct for what it claims. The rel8 displacement is sign-extended (a Java `byte`), the
    rel32 by `(int)`. The pointer scan runs before the executable-only `continue`, so data blocks are searched. The
    script is read-only (no transaction), and it adds one `ghidra.sh` subcommand, so it is backward-safe. Its limits
    were not written down: `fall` sees only disassembled instructions, `rel` does not decode `E0`–`E3` or
    `66`-prefixed branches and skips each executable block's last 4 bytes, and no channel sees a computed target.
  - **Fixes:** (1) save/0001: 0x0052BFC0's "callers unfollowed" now carries the raw scan (nothing reaches it) and its
    gate (`0x00883D54`, set only by the setter). (2) save/0001: the computed-target residual names the nearest
    indexed store. 0x0052C134 writes `[0x00882D34 + 4·id]` (`id` 16-bit; `0x00883D50` is `id` 0x407) only into a slot
    holding −1, which only 0x0052C1E1 stores, for allocator ids 1..0x400. The other `.data` indexed stores below the
    callback are named as what the `[I]` still stands on. (3) `FindPointer.java`'s header states its limits (comment
    only; no output changes). The proposals are also written as accepted in save/0001 and inventory § 2.6 (rule 3).
  - **Rulings:** (a) the four moves are accepted. Rows 3 and 19 go shortfall → d-none, and the callback halves of rows 2
    and 18 are d-none as halves, with both rows still H1b, raised in part. (b) The unfollowed read at 0x0052BFCF does
    not change ruling (d). "Nothing reaches the code" is about the callback-gated paths, and that read is one of them,
    gated on `0x00883D54`, which only the setter writes. Nothing reaches 0x0052BFC0 either. (c) d-none with an `[I]`
    absence fits the class rules. d-none raises nothing, its definition includes dead code, and its reason may be a
    reading (tc 41, outdoor 10). The reason is recorded with its residual, and a caller of 0x0052C0E0, found any way,
    moves rows 3 and 19 back to (b). (d) The symbols stay I (no logged return, rule 14 scope).
  - **Totals** (against `main` `2637b081`; `lane/p50b` changed no inventory row): H1b raised 25, raised in part 14,
    shortfall 5, d-none 4: 48. **static 567, harness 521, c-emu 0, blocked 419** (d-none 293, d-edit 73, d-sim 28,
    d-2c 7, d-owner 10, d-0032 8), **deferred 2, raised 17: 1 526**, as the lane filed them.
  - **Backlog:** review request closed. **Next:** merge `lane/r1h`; H1a (`d2s-load`) as before.
- **2026-10-27 — H3b (`data-load`) filed (reverser, `lane/h3b`, harness slot 2, after merging `main` `2637b08`).**
  run:2026-10-27-sweep-data-load: seven program runs (stock, `-txt`, loose files, `-direct`, `-direct -txt`, and `-direct`
  with a loose `use` byte of 0x0B and of 0x0E; expansion Normal, `H3bRare`), record in
  [data experiments](../findings/data/experiments.md#run2026-10-27-sweep-data-load), evidence in the "Plan 0038 batch
  H3b" sections of [data/0001](../findings/data/0001-excel-loader.md#plan-0038-batch-h3b-run2026-10-27-sweep-data-load),
  [data/0002](../findings/data/0002-mpq-precedence.md#plan-0038-batch-h3b-run2026-10-27-sweep-data-load),
  [data/0003](../findings/data/0003-string-tables.md#plan-0038-batch-h3b-run2026-10-27-sweep-data-load),
  [data/0004](../findings/data/0004-cell-converters.md#plan-0038-batch-h3b-run2026-10-27-sweep-data-load) and
  [player/0001](../findings/player/0001-creation.md#plan-0038-batch-h3b-run2026-10-27-sweep-data-load).
  - **Ruling 3's start mode works:** `tools/d2run.py --early` stops the game once `game.exe` is mapped (0.50–0.57 s
    after launch in the kept runs) and attaches then; built and tested off-slot on a stopped dummy process, then with
    probe runs on slot 2 (kept in `dev/`). Loggers used with it need `set displaced-stepping off`. The 9 startup rows
    are no shortfall.
  - **Ledger (25):** raised 18 (data/README 2, 3, 4; data/excel 1–7, 17, 18, 20, 24, 25, 27, 50; data/strings 29),
    raised in part 7 (data/README 5 and data/excel 8, with a correction: `TC_GetByName` is dead code, its half a d-none
    remainder; data/excel 71 with a refinement, 74; data/strings 2, 6, 22), shortfall 0. S1b remainders: data/README 1
    raised, data/excel 30 raised in part with a correction (`hitclass.bin` read whole by the character-graphics loader).
    No class move; inventory § 2.6 H3b block; totals static 567, harness 523, blocked 417, deferred 2, raised 17: 1 526.
  - **Design changes on the way:** three runs were added to the plan's piece list (dtxt, rus, clamp), which separate
    `-direct -txt`'s load of the written files, the language byte read and its clamp; the loose files stay in the
    slot's prefix (`h3b_sessions.py stage` / `unstage`), and the checker re-creates them by `stage` (`--written` for the
    files the dtxt run wrote).
  - **Backlog:** review request
    [h3b review](../backlog/archive/2026-10-27-reverser-architect-review-lane-h3b-plan-0038-batch-h3b.md); spec-writer entry
    [h3b raises](../backlog/archive/2026-10-27-reverser-spec-writer-h3b-data-load-raises-and-corrections.md) (held for the
    review).
  - **Next:** the H3b review. Slot 2 stopped, saves restored (empty, no aside), staged directories removed.
- **2026-10-27 — H3b review (architect, `lane/h3b`): accept with fixes (9).** Merged `main` `550d2dcc` into the lane
  first (`30352c97`). The plan log, inventory and ledger conflicts kept both sides. `backlog.py archive` had nothing to move.
  - **Checks:** `sha256sum -c` passes for `h3b-manifest.sha256` (`0b75400a…`, 88 files) and `h3b-manifest-dev.sha256`
    (`73e35bff…`, from `dev/`). After `h3b_sessions.py stage --slot 2`, `sweep_h3b.py check` re-run under
    `systemd-run --user --scope -p MemoryMax=4G` (the tool hashes of `check/tools-at-check.sha256`) is byte-identical
    to `check/check-h3b.txt` (`3cd7cecf…`, `TOTAL bad=0`), then `unstage`. `tbl.py check` gives the kept 7 `CHECK` lines.
    The outputs and a hash list of the 25 screenshots the kept manifest left out are in `workspace/logs/h3b/review/`
    (`review-manifest.sha256` `a26cb23e…`). objdump confirms the anchors. Callers 0x0044B937 (`DATATBLS_LoadAll`), 0x004359F2,
    0x0044B911, 0x00441B91 (`STRTABLE_LoadAll`), 0x00435C8D, 0x0044B976 (`STRTABLE_Unload`), 0x00434331
    (`MPQ_OpenVideoArchives`), 0x004345D7, 0x00504485 and 0x006122CC (`FILE_LoadWhole`), 0x0048C5F8/0x0048C6DB, 0x004DBA9E/0x0063EC2D
    (`ITEMS_GetByCode`). The handler call at 0x0044DA0C returns to 0x0044DA0E. The `-txt` gates are at 0x006127DF and 0x00617745. 0x0065A33B lies
    in `TC_BuildChestTable` (0x0065A2C0), called from `TC_LoadAll` at 0x0065A3B5. Nothing calls or jumps to 0x00654DD0,
    and its VA and RVA occur nowhere in the file as bytes. The `sounds` 2-byte call is at 0x00659C16, skipped by the `je` at 0x00659BC1
    when `g_DataTblsCompileTxt` is 0. The levels writers are at 0x0061DB05/0x0061DB20/0x0061DB40.
  - **Shared tree:** in `workspace/runtime/game`, `game.exe` (`631066c1…`), `binkw32.dll`, `ijl11.dll`, `smackw32.dll`
    and `d2.lng` match `docs/inventory.md`. The `d2data`, `d2exp` and LoD `patch_d2` reference archives it links to
    match `docs/formats/installer.md`. Nothing there or in the reference tree is newer than 2026-10-12 except the
    directory entry (the crash folder's removal) and the game's own `BnetLog.txt`/`default.key`. No `BlizzardError/` is
    left. No stopped game: `slots.py status` shows slot 2 idle, and the only game running is another lane's on slot 1.
    The `--early` code can leave a stopped game when gdb never resumes it. The driver's `--after` timeout and
    `wineserver -k` end it, but only after up to `--after` seconds. Rule recorded in the reverser tooling reference:
    check `slots.py status` after such a run and `slots.py stop` a game left in state `T`. Probes that may crash go in
    a `--game-dir` inside the slot's prefix. Crash folders are kept in `dev/`, not deleted.
  - **Fixes (9):** (1) *overclaim:* the language clamp (values above 13 → 0) rested on a made-up `use` byte 0x0E that
    no shipped file holds. Data/strings 29 and data/excel 50 become raised in part, the clamp half `[I]`, d-edit
    (data/0003). (2) *wrong anchor:* the `EXCEL_FindName` return 0x0065A33B is `TC_BuildChestTable`'s, not
    `TC_LoadAll`'s (data/0001, spec-writer entry). (3) *omission:* the 18th `-txt`-only call's address and gate
    (data/0001 § B1 note and H3b bullet). (4) *omission:* the levels `+0x033..+0x035` writers and their 25-slot bound
    (data/0004). (5) *under-claim:* `DRLG_LoadLevels` C in data/0001's Functions table (rule 14). (6) *miscount:* the
    filed totals predated the `lane/r1h` moves. (7) *tool not kept:* the record said the probes were kept in `dev/`.
    Their logs and the crash files were not kept, and the record now says so. (8) *tool not kept:* the screenshots
    were outside the manifest. They are now hashed in `review/shots-h3b.sha256`. (9) *omission:* the 45 logged
    chest-name lookups give S1b row 42 G1's post-pass half an observable. Its d-none label is struck, and the store
    stays `[I]` (data/0001 row 42 and § H3b). Also fixed: tooling.md's "first breakpoint" (the probes ended at the
    second), and the record now says `check/tbl-check-h3b.txt` holds the `CHECK` lines only.
  - **Rulings:** (a) Ruling 3's start mode, `d2run.py --early`, is accepted as built. Its stop needs only the image
    mapped, it touches only descendants of the launcher (so a concurrent slot's game is safe), and the logger's
    `XATT` line is the per-run check. The stopped-game and shared-directory rules go to tooling.md. (b) `TC_GetByName` is dead code, d-none as a remainder of
    data/README 5 and data/excel 8, both raised in part. The absence is `[I]` (a computed target is not excluded), as
    in the `lane/r1h` ruling. Phase 3 rewrites the entry rows to name the real callers and keeps `TC_GetByName` as a
    note. (c) Excel 30's correction stands. `hitclass.bin`'s whole read at every start is the character-graphics
    loader's, and the `sounds` call is the 18th `-txt`-only call. (d) Levels `+0x033..+0x035` go into J4 (spec-writer
    entry). (e) The `CYR` correction to data/0003 § Language stands. `0B` is the shipped `Use_rus`, which the
    install's Russian launcher script copies with `-direct`, so the rus run is stock-reachable. The exit test stays
    `[I]`. (f) Of the three runs beyond the piece list, **dtxt** counts (it separates excel 27's `-direct -txt` half),
    **rus** counts (stock-reachable, the byte read's 11), and **clamp** is kept as seen, not counted (ADR-0010: a claim
    only edited data reaches stays `[I]`). The `.bin` padding and the `.tbl` variants of the loose and direct runs taint no
    claim, because the claims are about which source `FindFile` picks, a stock path. (g) The 18 symbols I → C stand.
    `TC_GetByName` stays I.
  - **Ledger:** H3b raised 16, raised in part 9, shortfall 0: 25. No class moves. Totals against `main` `550d2dcc`:
    **static 567, harness 521, c-emu 0, blocked 419** (d-none 293, d-edit 73, d-sim 28, d-2c 7, d-owner 10, d-0032 8),
    **deferred 2, raised 17: 1 526** (inventory § 2.6 H3b block). Lane row usage filled from the orchestrator (530 156
    tokens, 235 tools, 61 min). Review row added, usage "—".
  - **Phase 3:** with H3b accepted, the **data/excel**, **data/strings** and **data/README** clusters are ready for
    their re-tag round. Their batches are S1b, S1e and H3b, all accepted. The data/excel round also folds plan 0039's
    remainder (P1b (a), P1c (a), the 11 data/excel W1).
  - **Backlog:** the review request was closed. The spec-writer entry
    [h3b raises](../backlog/archive/2026-10-27-reverser-spec-writer-h3b-data-load-raises-and-corrections.md) was **released**,
    with the TC caller list, the clamp half, the addresses and the G1 post-pass note added.
  - **Next:** merge `lane/h3b`; then H6e2 (plan order), and the data clusters' Phase 3 round.
- **2026-10-27 — `lane/rbd` (reverser, static, objdump only, no slot, no Ghidra): the H4a chained-model mismatches and
  skills/0002 § 6.** Filed from head `daac96a5` (the lane added no entry of its own here; this one records it). The
  three H4a groups of the [backlog entry](../backlog/archive/2026-10-25-architect-reverser-h4a-chained-model-mismatches-council-nihl2.md)
  were resolved without a session: council is entry bit `0x400`, the client wall fade's mark, on a near room's walls
  ([drlg/0002 § Lane rbd](../findings/drlg/0002-room-build-draws.md#lane-rbd-entry-bit-0x400-on-a-neighbours-walls-2026-10-27));
  nihl2 is `MonPostCreateBoss`'s mod 22 for `BaseId` 526, and behind it superunique tail 60's escorts
  ([monsters/0003 § Lane rbd](../findings/monsters/0003-special-monsters.md#lane-rbd-monpostcreateboss-and-the-h4a-chained-models-2026-10-27));
  chaos7 is the logger's `CM` window, closed at the two seal superuniques' placements
  ([experiments addendum](../findings/monsters/experiments.md#addendum-2026-10-27-lanerbd-the-chained-models-re-checked)).
  The twelve H4a logs go rc 0 and the 63 kept logs are unchanged. The skills/0002 § 6 entry (from the plan 0045 P3
  review) is logged in [plan 0045](done/0045-skills-missiles-machinery.md#implementation-log).
- **2026-10-27 — `lane/rbd` review (architect): accept with fixes (6).** Merged `main` `7cd4f991` into the lane first
  (`349463a4`). The ledger conflict kept both sides. `backlog.py archive` had nothing to move.
  - **Checks:** `sha256sum -c` passes for `check-rbd/rbd-manifest.sha256` (`f34f23c5…`, 9 files) and
    `skills/rbd/rbd-manifest.sha256` (`3c6bdf04…`, 3 files). Under `systemd-run --user --scope -p MemoryMax=4G`,
    `run-monstats.sh` and `run-regress.sh` re-run with the lane's tools and with `main` `7cd4f991`'s
    (`git archive`, a `workspace` link beside them) give the four kept outputs byte for byte: `monstats-h4a-rbd.txt`
    (12 × rc 0), `monstats-h4a-main-control.txt` (council, nihl2, chaos7 rc 1), `regress-kept-rbd.txt` and
    `regress-kept-main-control.txt` (identical, one rc 1 each). `main`'s chain tools have not changed since the
    lane's control at `550d2dcc`. `skills.py check` on the 33 skills logs reproduces `rbd-skills-check.txt` and its JSON
    byte for byte (BD.seed 4 118, 0 mismatches). `test_skills.py`: 13 tests pass, `test_bd_swap` among them. objdump
    confirms the anchors: `MissileElemRoll`'s max-then-min reads, the `jg` tests at `0x005A8925`/`0x005A8940`, the swap
    at `0x005A894B`–`0x005A8951` (`EAX` still the minimum), the mastery read on `EBX` at `0x005A895F`, the physical
    swap at `0x005A89EB`, `RangeB`'s `jg` at `0x0045C3E5`; `MISSILE_HitUnit`'s `mov edi, edx` at `0x005ADF1C` and
    `push edi` before `0x005AE150`; `MonSpawnTry`'s `test bl, 2` at `0x005B2ECF`, the unconditional
    `MonPostCreateBoss` call at `0x005B2EDF` and `test bl, 0x40` at `0x005B2EE4`; the jump table (254 indices, 17
    targets, 235 to `0x005B2058`) and the `BaseId` 526 compare at `0x005B2002`, which runs quest hook 34 then
    `ModAppendApply(22, 1)`; tail 60's `LevelClassVariant(453)` and `EscortSpawn(…, 1, 10, 20, 0x40)` at
    `0x005A4DDD`–`0x005A4DFB`; and a whole-`.text` scan finds exactly the two `or [esi+0x14], 0x400` and two
    `and …, 0xFFFFFBFF` sites (none in byte form). The chaos7 window lines are as stated: `PX` at 34508 and
    `CMRX` at 50604, the last window lines before `SU0` 34913 and 50798.
  - **Fixes (6, made here):** (1) *under-claim (rule 14):* `sub_005B1CF0_MonPostCreateBoss` (its 526 case compared
    at `SMPX`) and `sub_0063EC70_LevelClassVariant` (453 → 458, logged and chained) raised to C in `re/symbols.csv` and
    monsters/0003's Functions table; `MISSILE_BuildDamage` and `sub_005A8910_MissileElemRoll`, whose drawn fields the
    4 118 builds compare, raised to C, the first's evidence moved to skills/0002 (combat/0001's and skills/0002's
    tables updated). (2) *tool not kept:* `rbd-manifest-dev.sha256` sat in `check-rbd/`, where it fails, while the
    record said it passes from `check-rbd/dev/`: moved there, now passing, the record says so. (3) *omission:* the kept
    log `h4b-s5b-4801-normal-merc-game2`'s 12 roomk mismatches under both tool sets are the **known, recorded**
    failure of run:2026-10-16-sweep-monsters-b's *Deviations and limits* (a second game in one process; its DT1 lists
    are those already loaded); the record now links it. No backlog entry is needed. (4) *omission:* tail 60's `[C]`
    read as a new raise; H4a's `sweep_h4a.py` had already reproduced the tail's calls (special § G row 60 rests on it).
    The bullet now says what the lane adds (the chained placement, its 20 requests compared with `MT0`, flags
    included) and that no tag moves. (5) *omission:* the window rule's limits were not stated: it ignores the thread,
    where the logger keeps one window per thread, and the logger's RW0 line is conditional while its window close is
    not. Written into the record with why both errors fail loudly. (6) *omission:* the lane filed no entry in this
    log; the entry above records it.
  - **Rulings:** (a) **The chaos7 change is legitimate modelling under ADR-0004, not a fit after the fact.** The
    logged `CM` marks are the oracle the collision model takes; outside the logger's window there is no oracle, and
    the model falls back on its own prediction, which ADR-0004 prefers ("a boundary oracle never replaces in-scope
    code"). The window rule is the logger's own breakpoint set, read from `tools/gdb/collision.py`, not tuned to the two
    mismatches; a logged `CM` inside a window called closed is a mismatch, and so is a missing one inside a window
    called open. The applied marks are not confirmed by themselves: the 211 later `CollisionTest` returns with the unit
    bit (142 and 69 in the two `SU` windows), logged unwindowed, are what checks them, and they all match. No claim
    rests on the unlogged marks alone. (b) **The `[C]` raises stay within the logs.** Mod 22 is `[C]` for `BaseId` 526
    alone (one unit, and the model without it fails); the rest of the case table and the flag-2 gate stay `[I]` (590
    flag-2 requests, none compared). Tail 60 keeps its `[C]` with no tag move. `0x400` on near-room walls only is `[C]`
    for the council log (33 entries over 151 dumps, none on an own room), not a claim about other logs; its writer is
    `[I]` (immediate forms only, a computed store not excluded). (c) **Tail 60 is a symbol matter, not a spec one:**
    `LevelClassVariant` C here, § G row 60 unchanged. (d) **No H4a ledger outcome or inventory total changes.** None of
    the three groups sat on an H4a row (the H4a review's ruling d stands); row 60 (H4a) was already raised, and the
    526 piece belongs to special § J's `[I]` bullet, a remainder of S3a's row 73 that the spec-writer splits in Phase 3
    with no class move. Totals stand at the H3b review's 1 526 (`main` `7cd4f991` adds no inventory change).
  - **Spec-writer:** the entry [skills/missiles F1 and dispatch I4](../backlog/archive/2026-10-27-architect-spec-writer-skills-missiles-f1-mastery-and-dispatch-i4-kick.md)
    is **released** with what to write (the mastery out of F1's `[C]`, the `k` lines `[I]` inline, the `[L]` open
    question, the swap's order, both runs' 4 118 builds). The lane's entry
    [MonPostCreateBoss and 0x400](../backlog/archive/2026-10-27-reverser-spec-writer-postcreateboss-table-and-entry-bit-0x400.md)
    is **released** with the § J split and the scope of the `0x400` `[C]`.
  - **Backlog:** the review request was closed. Review-fixes Seen lines: reverser 6 and 14.
  - **Ledger:** the lane row filled (verdict, fixes 6: under-claim 1, tool not kept 1, omission 4; usage from the
    orchestrator: 301 043 tokens, 196 tools, 33 min); the review row added, usage "—".
  - **Next:** merge `lane/rbd`; the two spec-writer entries may start.
- **2026-10-27 — Phase 3, the data/excel, data/strings and data/README clusters (spec-writer, `lane/s38d`, from `main`
  `41500789`).** Their batches are S1b, S1e, S1f (data/excel 65, 69) and H3b, all accepted; the data/excel round also folds
  plan 0039 P1b (a), P1c (a) and the 11 data/excel W1 warnings.
  - **Counts:** [data/README](../specs/data/README.md) {C 3, I 5, L 0} → **{C 9, I 2, L 0}**;
    [data/excel](../specs/data/excel.md) {C 42, I 100, L 8} → **{C 144, I 45, L 2}**;
    [data/strings](../specs/data/strings.md) {C 60, I 42, L 3} → **{C 88, I 29, L 3}**; `updated:` 2026-10-27.
  - **Applied:** the H3b entry (the TC entry rows name `EXCEL_FindName`'s callers, `TC_GetByName` an `[I]` dead-code note;
    the language clamp `[I]`; levels `+0x033..+0x035` in J4; the `CYR` exit; the `hitclass.bin` read and the `sounds` call;
    the G1 post-pass lookups `[C]`, the store `[I]`), the S1b, S1e and S1f lines of these specs (the id-13 correction
    among them, as the S1e review's addition (a) words it), plan 0039 P1b (a) and P1c (a). W1 for data/excel is 0.
  - **Wiki:** [wiki/game-data](../wiki/game-data.md) `based_on` dates for the three specs set to 2026-10-27 and its stale
    paragraphs restated (W4 clear).
  - **Backlog:** closed the H3b, W1, P1b, P1c and S1b entries; the S1e corrections, S1e review additions and S1f entries
    annotated (save/d2s and items/uniques-sets parts open). Counts entry
    [s38d counts](../backlog/archive/2026-10-27-spec-writer-architect-s38d-data-clusters-counts-for-the-research-map.md), review
    request [s38d review](../backlog/archive/2026-10-27-spec-writer-architect-s38d-review-data-clusters-phase-3.md). Ledger row
    added, usage "—".
  - **Next:** the `lane/s38d` review.
- **2026-10-27 — `lane/s38d` review (architect): accept with fixes (10).** Merged `main` `65893010` into the lane first
  (`8dd2e248`; the ledger conflict kept both sides, `backlog.py archive` had nothing to move).
  - **Checks:** every new `[C]` occurrence of data/excel (106 on changed lines) was listed by script against the old
    file, and over 70 of them, all the entry rows, constants, A–J pseudocode headers and step notes, were traced to their
    batch's raise: H3b rows 1–8, 17, 18, 20, 24, 25, 27, 50 (byte), 71, 74 and the excel 30 remainder (data/0001,
    data/0002, data/0004, player/0001 § H3b); S1b rows 9–14, 19, 21, 23, 26, 29, 31, 33–35, 38, 41, 42, 45–49, 55, 57,
    61–63, 67, 68, 72, 73, 75–78; S1e rows 16, 36, 37, 40, 51, 52, 53, 56, 60, 64, 66; S1f rows 65, 69; plan 0039 P1b
    Q3's data count. The H3b review's fixes hold: the clamp `[I]` in excel I1 and strings § H, data/strings 29 and
    data/excel 50 raised in part (byte `[C]`, clamp `[I]`), `TC_GetByName` an `[I]` dead-code note in both entry
    tables, the entry rows naming `EXCEL_FindName`'s real callers. data/strings' 28 new `[C]` and data/README's 6 were
    read whole against data/0003 § S1b, S1e, H3b and data/0002 § S1b, H3b. objdump confirms 0x0063366D (`imul 0x1a8`),
    0x00653FB8/0x00653FDC/0x00654E17, 0x006BD26C/0x006BD27A, 0x005251A1, 0x005252AA/0x005252B2, 0x0061DB05/0x0061DB20/
    0x0061DB40, 0x00659BC1/0x00659C16, 0x006127DF, 0x006BD7FE, 0x006BDFFF, 0x006BDE20 (`movsx`), 0x006BDD82/0x006BDDE7,
    0x00524E0C, 0x0065A3B5, 0x004345D7, the signed `jle` at 0x0041B95B and the inline byte compare 0x00524CA4–0x00524CC6.
    The shipped `levels.bin` has at most 10 leading non-negative slots in `mon`, 8 in `nmon` and `umon` (scratch read).
  - **Fixes (10):** (1) *overclaim:* `AddCode`'s growth by 64 under E2's `[C]` header and in the E2 note; every emulated
    insert had room (data/0001 § S1e), so the growth is `[I]` (block comment and its own note). (2) *overclaim:* J4's
    levels writers stated `[C]` with their bound of 25; no stock record reaches it, so the bound is `[I]`, the counts and
    the first-negative stop `[C]`. (3) *overclaim:* A2's "signed compare" under `[C]`; every priority is positive, `[I]`.
    (4) *overclaim:* A3's "or no archive is open" under `[C]`; the finding keeps it `[I]` and no lookup ran before the
    first open. (5) *overclaim:* D1's "the file buffers are freed" under `[C]`, not logged, `[I]`. (6) *overclaim:*
    data/strings E2 "exact, case-sensitive `strcmp`" `[C]`; the match is `[C]`, its case-sensitivity `[I]` (point 3).
    (7) *overclaim:* data/strings' reimplementation note tagged the fallbacks' "matter only to an install without
    `d2exp.mpq` or to edited tables" `[C]`; S1e keeps the stock unreachability `[I]`, now split. (8) *omission:* J4's `[I]`
    remainder now names "no reader" of the padding bytes, which a dump cannot show. (9) *overclaim:* wiki/game-data's
    "with `-direct -txt` every table came from the freshly written files"; the 5 character-graphics reads before the
    write went to the archives, now "every table read after the compile". (10) *overclaim:* three wiki sentences stated
    flat against an `[I]` (spec-writer rule 1): the short name that is both a code and a TC name, the string match's
    case-sensitivity and the no-archive case, each now "read from the code".
  - **Rulings:** (1) data/excel 28's reword stands. "The `patch_d2` `.txt` edits are not live" is not a supported
    statement lost: S1b's compile gives the shipped `.bin` byte for byte from the top-ranked `.txt` for all five tables,
    so the `.txt` holds no record-level edit that could be live or not; the sentence was at best vacuous. Its removal
    from B1, the reimplementation notes and the wiki is right, and it does not touch the parked 1.14b/1.14d `patch_d2`
    question. (2) The Constants priorities row `[C]` stands on H3b: its runs log every `MPQ_OpenArchive` call with its
    priority argument (5000, 3000, 1000 as A1), and the list after every open equals A2's model, which supersedes S1b
    row 11's d-none for the numbers (that d-none was for want of an observable, and H3b supplied one). (3) The
    case-sensitivity disagreement is aligned down, not filed: data/0003's hash bullet (plan 0028) tags the match `[C]`
    over 9 456 searches, but S1b row 57 found no logged key held only under another case, so the run cannot separate a
    case-sensitive from a case-folding compare. data/strings E2 now states the match `[C]` and the case `[I]`, as
    data/excel I3 does, and data/0003 carries a dated review note. (4) The E2 duplicate note (rule `[C]`, "never fires on
    stock data" `[I]`) is right. (5) The `[C]` count rise is honest: the restated evidence bullets carry claims of their
    own (counts, call sequences, the TC-lookup absence in play), each traced to the batch named, and the split rows keep
    each remainder at its batch's tag. No restatement raised a tag beyond its source; the fixes above are sub-steps of
    block headers the batches never reached. (6) Plan 0039's remainder is fully folded: P1b (a) (G2, the post-pass, the
    u16 list in § D) and P1c (a) (H3's every-reader scan `[I]`); no plan 0039 entry is left open.
  - **Counts:** data/README {C 9, I 2, L 0} (unchanged); data/excel {C 144, I 51, L 2}; data/strings {C 88, I 31, L 3}.
    Research-map rows `data/excel` (with the overview) and `data/strings` rewritten whole. The wiki's `based_on` dates
    stay 2026-10-27.
  - **Backlog:** the review request and the counts entry closed. The S1e review additions ((d), save/d2s), S1e
    corrections (save/d2s) and S1f (items/uniques-sets) entries stay open for their other specs.
  - **Ledger:** lane row usage filled from the orchestrator (354 593 tokens, 110 tools, 29 min); verdict and fixes
    filled. Review row added, usage "—". Spec-writer review-fixes rules 1 and 2 have new Seen lines.
  - **Next:** merge `lane/s38d`. The data clusters' Phase 3 round is done.
- **2026-10-27 — H1a (`d2s-load`) filed (reverser, `lane/h1a`, harness slot 2, from `main` `550d2dcc`, `main`
  `ee8273b7` merged in).** Slot 2 is stopped and its saves directory restored (empty, no aside); no game, driver, gdb
  or watcher of the lane is left.
  - **Method:** the character screen lists only files that pass its own header tests (`0x0043C8A0`) and takes the
    game's status from the listed file, so the runner (`tools/h1a_sessions.py`) lets the screen read a listed file,
    then copies the case file over it and presses OK: the server reads the case's bytes. 5 kept sessions (main, order,
    stub7, name15, mercmf) and the S1b piece on tool-built saves (`tools/h1a_saves.py`, 37 cases), logger
    `tools/gdb/d2s-h1a.gdb` (the H1b logger plus `d2s-h1a.py`), checker `tools/sweep_h1a.py` (runs `d2sio.py check`
    first). `d2sio.py` gained the file-only code model (4, 6, 5, 7), the error-map table, `context=`, `UNPARSED` and
    `UNTERMINATED`; the H1b logs re-check byte-identical (2 798, 0 failing) and the 2026-10-12 logs keep `main`'s totals.
  - **Check:** **410 comparisons over 38 cases, 0 failing**; every `d2sio.py` part 0 mismatches (`workspace/logs/h1a/check/sweep-h1a-check.txt`, manifest `h1a-manifest.sha256`).
  - **Ledger (46):** raised 32, raised in part 4, shortfall 8, proposed d-none 2 (player-creation 20, 34: no class-7
    player is ever made; both class-7 loads halt at line 1210). Halves proposed d-none: save-d2s 139's `gf` half, 50's
    ladder test. Totals against `main` `ee8273b7`: **static 567, harness 519, c-emu 0, blocked 421** (d-none 295),
    **deferred 2, raised 17: 1 526** (inventory § 2.6 H1a block).
  - **New readings (for the spec-writer entry):** `D2S_ReadSave`'s 9 is unmapped; a waypoint record with marker 0 or
    `0x0101` is zeroed with its marker and `WAYPOINT_Save` restores `0x0102`; a set id with no record drops the item,
    not the load; a unique id ≥ the count is −1, written `0xFFF`; for a version ≤ 95 the current durability is 8 bits;
    `0x29` bounds the old stat form; class 7 halts.
  - **S1b piece:** the CalcSor session ran as staged (`rng.py seedtree` 1 884/1 884; `calc.py hover` 7 `CH` lines, 0 hover evaluations, 8 drink evaluations; `calc.py check` 52/52). data-calc 19's hover half and rng-seeds 11's caller 0x00569F53 are met (notes in data/0005 and rng/0002); the rows stay S1b for the review. The 2026-10-16 entry is closed (archive).
  - **Symbols** (rule 14): eleven readers I → C (filed as "ten"; corrected at the review); four functions added (I).
  - **Backlog:** archivist [2026-10-27-reverser-archivist-h1a-d2s-legacy-layouts-and-parser-gaps](../backlog/archive/2026-10-27-reverser-archivist-h1a-d2s-legacy-layouts-and-parser-gaps.md);
    spec-writer [2026-10-27-reverser-spec-writer-h1a-save-d2s-player-creation-raises](../backlog/2026-10-27-reverser-spec-writer-h1a-save-d2s-player-creation-raises.md)
    (held for the review); review request [2026-10-27-reverser-architect-review-lane-h1a-plan-0038-batch-h1a](../backlog/archive/2026-10-27-reverser-architect-review-lane-h1a-plan-0038-batch-h1a.md).
  - **Next:** the `lane/h1a` review.
- **2026-10-27 — `lane/h1a` review (architect): accept with fixes (5).** H1a (`d2s-load`, 46 statements), reviewed at
  `8cba78ac` after merging `main` `6ad383c4` into the lane (`87b7f916`; conflicts in this log and player/0001, both
  appends, kept both sides; `backlog.py archive` moved nothing). Static review, objdump on the pinned image
  (`631066c1…`), no Ghidra, no harness.
  - **Re-checks:** `sha256sum -c` of `h1a-manifest.sha256` (141 lines) and `h1a-manifest-dev.sha256` (12) from
    `workspace/logs/h1a`: all OK. `systemd-run --user --scope -p MemoryMax=4G python3 -I tools/sweep_h1a.py check …`
    on the five kept logs: **410 comparisons over 38 cases, 0 failing**, byte-identical to `check/sweep-h1a-check.txt`
    once systemd's "Running as unit" line is dropped. `d2sio.py` regression: `sweep_h1b.py check` on the 13 H1b logs
    with the lane's tools (`d2sio.py` `523991f2…`) equals `main`'s (r1h revision `29561293…`) once ` context=None` is
    dropped (2 798 comparisons, 0 failing), and is byte-identical to `check/sweep-h1b-recheck-h1a.txt`; the five
    2026-10-12 logs give the same totals with both revisions (826, 4, 4, 125, 662; 0 mismatches).
  - **Anchors checked with objdump:** `D2S_ReadSave`'s two returns of 9 (0x0053433C fewer than 8 bytes, 0x0053435A
    magic; ≤ 91 sent to the legacy reader at 0x00534364); the list filter `0x0043C8A0` (8 bytes, magic, version ≤ 91
    with 0x82 bytes and ≥ 71, else 0x14F bytes); `D2S_ReadHeader`'s class test `cmp al, 7; ja` (0x0056A172), then
    `SUnitCreate` (0x0056A22C) and `PlayerUnitInit` (0x0056A23B), which calls `sub_00553180` at 0x00569F38; its
    null-unit test pushes `0x4BA` = 1210 (0x00553187), matching both `Crash.txt` stacks (0x0056A240 for the full save,
    0x00569FB8 for the stub); `D2S_CheckStatus`'s callback test at 0x00569DBC (`0x00883D54`, whose only writers are in
    0x0052C0E0, with no reference to it in the image) guarding the ladder bit test (`test bl, 0x40`, codes 25, 26);
    `WAYPOINT_Load` (marker 0 or `0x0101` → `0x0102` stored at 0x00661086 then overwritten by the zero dword at
    0x0066108B) and `WAYPOINT_Save` (0x006610EB); the unique id bound (`cmp eax, [ecx+0xC28]; jl`, else −1,
    0x0062D0F1); the set-id branch (0x0062D18E → 0x0062D1A3); stat 72's 8-bit width for an item version ≤ 0x5F
    (0x0062D425, 0x0062D759; `0x5B20` = 72 × `0x144`); `EXP_GetThreshold`'s clamp (0x00611806–0x0061180F) and its 13
    callers.
  - **Rulings:**
    1. **The swap is a stock-path observation**, not a forced-path run: no table, memory or code is edited; the
       server's reader runs on the stock image with a real file's bytes and a client state the stock character screen
       made from another real file, so the raises stand under ADR-0013 § Neutral as what the reader does with those
       bytes. It bypasses one check, the client's list filter (`0x0043C8A0`), and no server check. No raised statement
       rests on a non-stock path, but the codes only a changed file reaches in single player (`D2S_ReadSave`'s 9, the
       version code 7, the `D2S_CheckStatus` mismatch codes 8 to 14) get a reach note in the spec, `[I]`.
    2. **Player-creation 20 and 34 → d-none, accepted** with a reach condition: class 7 passes the header and halts at
       the null-unit test (1210) both ways in, so no class-7 player exists. The clamp's other out-of-range input is the
       −1 of the callers' inlined null-unit test (0x005342DE, 0x00535A0A, 0x0056B13D); no run or reading shows a null
       unit there, and a null-unit call found at any caller moves row 20 back to (b).
    3. **Row 50's ladder half → d-none, accepted.** It runs only with `0x00883D54` set, and the `lane/r1h` ruling
       (the setter 0x0052C0E0 has no caller, `findptr` 0) holds; re-checked here (no `0x0052C0E0`-family pointer in the
       file). The same reach condition as rows 3 and 19 applies. The classic progression bounds (4, 8) stay the row's
       `[I]` remainder (a classic save was in reach; not a d-none).
    4. **Row 139's `gf` half → d-none, accepted** (no `ItemStatCost` row with `CSvBits` has a `CSvParam`).
    5. **The legacy rows (hirelings 3, 30, 33; player-creation 1; items-uniques-sets 21) stay shortfalls**, not d-edit:
       a version 71 or 87 save is what an older game wrote, a real input (ADR-0003, ADR-0013 § Neutral), and the gap is
       a builder and a format doc (archivist entry). If the archivist's work shows `sub_00534020_ReadSaveLegacy`
       refuses every legacy layout, they become d-none. Save-d2s 10, 17 and 126 stay shortfalls too.
    6. **S1b leftovers** (counted as S1b): data-calc 19 **in part → raised**. All 7 `CH` lines carry `+0xB4` = 0
       (word `+0xB6` `0x1506`), so 0x00486370 returns at 0x0048638B before the jump table (0x004863E4) that holds its
       three evaluation sites, while the drinks' 8 `CE` lines show the logger live; scoped to the potions hovered.
       rng-seeds 11 stays raised in part (0x00569F4B run-confirmed; four callers unhit, H5c route).
    7. **The new readings are accepted as filed**, each `[C]` on its case and logged lines: `D2S_ReadSave`'s 9
       returned unmapped; the waypoint marker reset and `WAYPOINT_Save`'s restore; the set-id item drop with the load
       going on; the unique id ≥ count read as −1 and written `0xFFF`; stat 72 in 8 bits for an item version ≤ 95;
       `0x29` bounding the old stat form.
    8. **Symbols:** the eleven I → C meet rule 14 (each has a logged return or output compared with the model:
       `RSV`, `PLD`, `RCST`, `RQW`, `RWP`, `RSTV`/`RSTL`, `RIX`, the written waypoint marker); the four added stay I.
  - **Fixes applied (5):** (1) miscount: "ten readers" for the eleven raised (save/0001 change log, this log).
    (2) under-claim (rule 14): `QUESTRECORD_LoadBytes` raised in `re/symbols.csv` but left I in save/0002's Functions
    table and § bullet; both now cite row 62. (3) omission: the swap's reach note named codes 9 and 7 only; save/0001
    § Plan 0038 batch H1a gains a *Scope* paragraph (ruling 1) and the spec-writer entry's (i) widened. (4) omission:
    rows 20/34's d-none without the −1 input; the reach condition is in save/0001 and player/0001. (5) omission:
    data-calc 19's hover note left "for the review to re-tag" without the gate; data/0005 names it (ruling 6).
  - **Ledger (46, as filed):** raised 32, raised in part 4, shortfall 8, d-none 2. **Totals** (against `main`
    `6ad383c4`; `lane/h3b`, `lane/a3f` and `lane/rbd` merged since the lane's base, none moving a row after the r1h
    totals): **static 567, harness 519, c-emu awaiting a batch 0, blocked 421** (d-none 295, d-edit 73, d-sim 28,
    d-2c 7, d-owner 10, d-0032 8), **deferred 2, raised 17: 1 526.** Inventory § 2.6 H1a review block; § 5 marks H1a
    done (and H1b, H3b, H4a, H5c, H5d, H7a, accepted earlier but left unmarked).
  - **Phase 3 ready:** **save/d2s** (S1a, S1e, H1b, H1a) and **items/uniques-sets** (S2b, S2c, S1f, H2b, H6d, H1a).
    Not ready: hirelings (H6f, 22 rows open) and player/creation (H6g, 15 rows open). Research-map rows of the two
    ready specs updated.
  - **Backlog:** review request closed; the spec-writer entry
    [2026-10-27-reverser-spec-writer-h1a-save-d2s-player-creation-raises](../backlog/2026-10-27-reverser-spec-writer-h1a-save-d2s-player-creation-raises.md)
    **released** with (i) widened and (j), (k) added (the rulings and the S1b re-tags); the archivist entry stays open.
    Review-fixes Seen lines: reverser 2, 4 and 14; architect 8.
  - **Ledger rows:** the lane row filled (verdict, fixes 5: under-claim 1, miscount 1, omission 3; usage from the
    orchestrator: 533 080 tokens, 290 tools, 52 min); the review row added, usage "—".
  - **Next:** merge `lane/h1a`; the save/d2s and items/uniques-sets Phase 3 re-tags may start.
- **2026-10-27 — `lane/sf2` (spec-writer, no slot, no Ghidra, no harness): the two entries released at the
  `lane/rbd` review.** (1) [skills/missiles § F1](../specs/skills/missiles.md#f-the-packet-at-the-hit-missile_builddamage):
  the mastery taken out of the `[C]` bullet, which now cites both runs (4 118 builds over 33 logs, 0 mismatches; the
  778-build breakdown kept as run:2026-10-25-skills's); the `k ←` and `if k ≠ 0` lines `[I]` inline at `0x005A895F`;
  a new `[I]` bullet on the mastery (0 of 54 655 `MH0` lists hold one); the `[I]` bullet gives the order *test both
  bounds > 0, swap, mastery, draw* and no inverted pair in either run; the `[L]` on a missile carrying its owner's
  masteries. [Dispatch § I4](../specs/skills/dispatch.md#i-the-skill-packet) restated per bound: the `Kick`-clear,
  `SrcDam` 0 formula and the `Kick` minimum `÷ 4` `[C]` (emulated inside hit 43, skills/0007 § 3), the `Kick` maximum
  `÷ 3` `[I]`, the weapon share `[I]`; skills/0003 § 5 does not say whether start 2 reads `MinDam` itself or calls
  `GetPhysMin/Max`, nor the table doc the `Kick` row's `MinDam`, so which damage Kick's start hit carries is an `[L]`
  open question and a [reverser entry](../backlog/archive/2026-10-27-spec-writer-reverser-kick-start-hit-damage.md).
  (2) [monsters/special § J](../specs/monsters/special.md#j-other-entry-paths-and-pre-existing-mods): the post-create
  helpers and the flag-2 gate `[I]`, `MonPostCreateBoss`'s case table by `BaseId` (one tag per row, 13 `[I]`; the 526
  row `[C]` for mod 22, `[I]` for its hook) and a `[C]` bullet for Nihlathak's 22, scoped to `BaseId` 526; § G row 60
  keeps its tag and cites the chained placement. [drlg/room-tiles](../specs/drlg/room-tiles.md) 9d's note: `0x400`,
  the client wall fade's mark, its writer `[I]`, on a near room's walls only `[C]` for the council log alone.
  Tags: missiles C 46, I 92 → 95, L 6 → 7; dispatch C 72 → 73, I 187 → 189, L 10 → 11; special C 149 → 151, I 70 → 86,
  L 4; room-tiles C 121 → 122, I 34 → 35, L 0 (`updated:` 2026-10-27). Wiki: skills (F1, I4, two open items);
  `based_on` of levels, randomness and seed-to-world bumped for room-tiles. Both entries closed;
  [review request](../backlog/archive/2026-10-27-spec-writer-architect-review-lane-sf2-missiles-f1-dispatch-i4-special.md)
  filed; ledger row added, usage "—".
- **2026-10-27 — `lane/sf2` review (architect): accept with fixes (3).** Merged `main` `94738360` into the lane first
  (`a74f768d`; the plan log and ledger conflicts kept both sides, `backlog.py archive` had nothing to move).
  - **Checks:** each change read against the released entries, the `lane/rbd` review's instructions and skills/0002
    § 6, skills/0007 §§ 2–3, skills/0003 § 5, monsters/0003 § Lane rbd and drlg/0002 § Lane rbd. The four front
    matters match a script count (gate E6 rule, backticked tags included). Every `[L]` sits under *Open questions*.
    objdump confirms `MissileElemRoll`'s max-then-min reads and `jg` tests (`0x005A8925`, `0x005A8940`), the swap at
    `0x005A894B`–`0x005A8951`, the mastery skip on −1 (`0x005A8956`), its read at `0x005A895F` and the two `MulDiv`
    adds ending at `0x005A8982`; `GetPhysMin`'s `Kick` branch (`str + dex − 20` for type 0, else `3 · stat 12`,
    floor 1, `÷ 4 << 8`, `0x00647BF0`–`0x00647C48`), the `SrcDam` call at `0x00647C61`, `MinDam` `+0x1A8` and the
    `HitShift` shift (`0x00647CB4`, `0x00647CF1`); `GetPhysMax`'s `Kick` call `KickDamage(0)` at `0x00647D41` and
    `KickDamage`'s `÷ 4`/`÷ 3` (`0x00644C70`, `0x00644C7A`); the wall fade's `test eax, 0x408` at `0x004DF086`; start 2's
    reads at `0x0056CB54`/`0x0056CB5A`.
  - **Fixes (3, made here):** (1) *overclaim:* dispatch I4's `[C]` bullet named `GetPhysMin/Max`'s callers (summons,
    missiles, do functions), which ADR-0015 (3) leaves outside an emulated map; moved to the `SrcDam` `[I]` bullet, and
    wiki/skills says the callers are read from the code. (2) *under-claim:* the `[L]` asked whether start 2 reads
    `MinDam` itself or calls `GetPhysMin/Max`; skills/0003 § 5's reading gives the former and objdump shows it
    (`0x0056CB54`–`0x0056CB71`, no call). The I4 `[I]` bullet now says the start hit carries the row's `MinDam`; the
    `[L]` is narrowed to the `Kick` row's values, the logged hits and the `Kick` branch's callers; wiki/skills and the
    [reverser entry](../backlog/archive/2026-10-27-spec-writer-reverser-kick-start-hit-damage.md) annotated (counts unchanged).
    (3) *wrong anchor:* the `SrcDam` share cited `0x00647CA6`–`0x00647CF1` (bands, synergy, shift); now
    `0x00647C4D`–`0x00647CA3` and the add at `0x00647CBA`.
  - **Rulings:** (a) **The I4 `[C]` raise is within the ADR-0015 map.** skills/0007 § 2 lists `SKILLS_GetPhysMin/Max`
    and `SKILLS_LevelBands` as emulated inside `heal9d` (1 500 cases, 0 mismatches), with the `SrcDam` and kick-damage
    calls as boundaries; the `Kick`-clear, `SrcDam` 0 formula and the `Kick` minimum are computed wholly before either
    boundary, and § 3 already states both `[C]`. The spec's `[I]` was an under-claim (spec-writer rule 8); the raise
    stands as a map from the row, the level and the owner's stats to the value. It does not cover the callers (fix 1),
    the column meanings beyond skills/0002 § 1's layout, or the maximum past `KickDamage` (kept `[I]`). (b) **Special's
    I + 16 is honest splitting.** 15 new claims (the two helper bullets, 12 table rows and the 526 row's hook) and one
    backticked mention (`` `[I]` `` in the Nihlathak bullet), which the gate counts as elsewhere in the specs. Each row
    is a distinct `BaseId` case with its own mods, as in § G's per-row table; no claim was duplicated. (c) missiles F1
    and room-tiles 9d follow the `lane/rbd` rulings (mastery out of the `[C]`; the `0x400` `[C]` scoped to the council
    log, its writer `[I]`).
  - **Counts (final):** skills/missiles C 46 / I 95 / L 7; skills/dispatch C 73 / I 189 / L 11; monsters/special
    C 151 / I 86 / L 4; drlg/room-tiles C 122 / I 35 / L 0. No inventory row or total moves (1 526 stand).
  - **Bookkeeping:** research-map rows for the four specs rewritten; review-fixes Seen lines: spec-writer 2, 8 and 9;
    the review request closed; the reverser entry stays open. Ledger: the lane row filled (verdict, fixes 3: overclaim
    1, under-claim 1, wrong anchor 1; usage from the orchestrator: 133 323 tokens, 62 tools, 13 min); the review row
    added, usage "—".
  - **Next:** merge `lane/sf2`; the reverser entry on Kick's row values may start.
- **2026-10-27 — H6e2 (`quest-items`) filed (reverser, `lane/h6e2`, harness slot 1; resumed from checkpoint 1,
  `main` `147e5ca3` merged).** Run id run:2026-10-27-sweep-quest-items, record in
  [items experiments](../findings/items/experiments.md#run2026-10-27-sweep-quest-items), evidence in
  [items/0010 § Plan 0038 batch H6e2](../findings/items/0010-quest-drops.md#plan-0038-batch-h6e2-run2026-10-27-sweep-quest-items).
  - **Resume, per the note:** the Act II and III sessions start in the Act IV town (three `-a4` recipes, header act
    bytes 131; H4a's fixed waypoint click), each on its own map seed (radament on 4904); `wpchain` limit 45 s; the orb
    read checked once after the first waypoint (0.75 / 0.79). On 4904 the Sewers stairs took two tries, as in H4a.
    Where a route failed twice (the staff chest on 4912, the brain chest on 4914) the pilot's other moves were used
    (`explore --to-pdef … --pdef-any` before the objop; then a full explore and `objop --obj-mem`); the staff chest was
    reached on map seed 4916, the brain chest not. 15 launches at the resume, 19 in all; 11 kept sessions.
  - **Check:** `sweep_h6e2.py check` over the 11 kept logs: chest 6, object 2, event7 19, dup 8, gate 8, death 3
    (listed); **0 mismatches** (`check-final.txt` `d4ce6d6d…`, manifest `manifest-final.sha256`).
  - **Ledger (24): raised 3, raised in part 14, shortfall 7** (inventory § 2.6 H6e2 block). Highlights: object event 7's
    route `[C]` for classes 268 and 367 (qd 1, in part); E1 met for `box`, `tr1`, `msf` and **corrected** for the Khalim
    chests (gold first; met on `qhr`); a held cube refuses `box`, a Normal staff in Nightmare does not stop `msf` (qd 34
    in part); Wirt's body row raised (leg, then 18 event-7 piles, `RandLoHi(10, 20)` = 18 on the logged seed). Shortfalls:
    `bkd`, `hdm`, `vip`, `bbb`, `g33`, `g34`/`xyz`, `qf1` (launch cap; the tome's warp led to the Disused Fane). No class
    move; totals unchanged: static 567, harness 519, c-emu 0, blocked 421, deferred 2, raised 17: 1 526.
  - **Answered:** the checkpoint's open question on `j34`/`mss` quality 7 is items/0004's us 13 (the base `unique`
    override); `ass` shows it too.
  - **Symbols (rule 14), I → C:** `QUESTS_ObjectEvent`, `sub_00594630_A1Q4_WirtGold`, `sub_00583E70_WirtLegDrop`,
    `sub_00593AF0_A1Q4_InifussDrop`, `sub_00599C10_A2Q2_ScrollChest`, `sub_00599CF0_A2Q2_StaffChest`,
    `sub_00599DF0_A2Q2_CubeChest`, `sub_005B8860_A3Q2_HeartChest`, `sub_00585970_DropItemCodeAt`,
    `sub_00558110_PlayerFindItemByCode`, `sub_0055CC90_ItemQuestGate`.
  - **Backlog:** review request
    [2026-10-27-reverser-architect-review-lane-h6e2-plan-0038-batch-h6e2](../backlog/archive/2026-10-27-reverser-architect-review-lane-h6e2-plan-0038-batch-h6e2.md)
    filed; spec-writer entry
    [2026-10-27-reverser-spec-writer-h6e2-quest-items-raises-and-the-khalim-chest](../backlog/archive/2026-10-27-reverser-spec-writer-h6e2-quest-items-raises-and-the-khalim-chest.md)
    filed, held until the review. Slot 1 stopped, saves restored (empty, no aside).
  - **Next:** the `lane/h6e2` review; then H6e1.
- **2026-10-27 — `lane/rk` (reverser, static: objdump, `tools/xrefscan.py`, the kept skills logs rescanned under
  `MemoryMax=4G`; no Ghidra, no harness): the [Kick start-hit entry](../backlog/archive/2026-10-27-spec-writer-reverser-kick-start-hit-damage.md)
  answered** in [skills/0003 § 5](../findings/skills/0003-handlers.md#5-tier-a-start-and-do-functions)'s 2026-10-27
  note and two Answer bullets. (2) `[C]` the stock `Kick` row has `MinDam` 0, `MaxDam` 0, the bands 0 and `HitShift`
  8, so start 2's physical is 0. (3) `[C]` run:2026-10-27-skills: Kick's 32 start and 32 do events (all `barh`), 25 do
  spans reaching `COMBAT_ApplyDamage` with result 9, physical 0, hit class 1 (`tools/kick_hits.py`, new; `bad=0`),
  where `GetPhysMin`'s `Kick` branch would give at least 49 920; run:2026-10-25-skills has no Kick. That the start
  stores `MinDam << HitShift` rather than nothing stays `[I]` (the code's), and the 7 deliveries with no `ApplyDamage`
  are not read. (4) `[I]` the `Kick` branch (`+0x05 & 0x02`; rows 1, 255, 270, 275) is reached through the new
  `sub_005D54B0_SkillKickPhysDamage` by Dragon Talon (start 24, do 42), Dragon Tail (start 27) and Dragon Flight
  (do 52), through no direct call of Kick's start 2 or do 2 (review fix 2); `GetPhysMax`'s branch is `sub_00644C20`'s only call; 15 variable-id call sites unfollowed.
  Kept: `workspace/logs/rk/rk-manifest.sha256` (9 files). Entries: [spec-writer](../backlog/archive/2026-10-27-reverser-spec-writer-dispatch-i4-kick-start-hit-answered.md)
  (dispatch I4's `[L]`), [architect review](../backlog/archive/2026-10-27-reverser-architect-review-lane-rk-kick-start-hit-damage.md).
  Ledger row added, usage "—".
  - **Review (architect, 2026-10-27): accept with fixes (2).** Checked: `sha256sum -c` of `rk-manifest.sha256` (9 OK);
    `tools/kick_hits.py` rerun under `systemd-run --user --scope -p MemoryMax=4G`, byte-identical (`774d0573…`, exit 0),
    and a negative control (a scratch `skills.bin` with the Kick row's `MinDam` 195, model 49 920: `bad=25`, exit 1);
    the Kick row re-dumped (identical; `MinDam`, `MaxDam`, the ten bands 0, `HitShift` 8, `DmgSymPerCalc` raw −1, the
    `.txt` cells blank but `HitShift`); objdump of start 2 (`0x0056CB42`–`0x0056CB80`: flags `+0x00` 2, result
    `+0x04` 9, `[esi+0x1A4]`/`[esi+0x1A8]`, `shl`, phys `+0x08`, hit class `+0x60` 1, `ResolveAndQueue(…, 0x80)`, no
    other call but the record fetch and the memset), `GetPhysMin`'s branch (`0x00647BF0`–`0x00647C48`; the byte at
    `0x006CE26C` is 0x02; `cdq`/`and 3`/`sar 2` rounds toward zero) and `sub_005D54B0` (its id and level from
    `[ebp+0x14]`/`[ebp+0x18]`); `tools/xrefscan.py` gives the 18 + 18 sites, the 3 `sub_005D54B0` calls (in
    `0x005D5880`, start 27 `0x005D7090`, do 52 `0x005D7850`), `0x005D5880`'s 2 (start 24, do 42) and
    `0x00644C20`'s 1, all as listed; the two `push 0x75` sites push the id; MonStats: only `shadowwarrior` and
    `shadowmaster` hold a `Kick`-bit skill (Dragon Flight). Kept: `workspace/logs/rk/review/` (`review-manifest.sha256`, 5 files).
    Fixes: (1) *omission:* the `[C]` separation leaned on "at least 49 920" without saying that the packet at
    `ApplyDamage`'s entry is already reduced (`ResolveAndQueue` runs `ApplyReductions` on a hit; combat/delivery A1),
    so a 100 % physical resistance would also give 0; the bullet now names the 9 target classes (`MonStats` 15, 19,
    20, 28, 44, 53, 58, 165, 170), Normal, `ResDm` 0, and the negative control (`kick-targets.txt`,
    `kick-hits-neg.txt`). (2) *overclaim:* "Kick itself never reaches it" in the Answer bullet, this log and the
    spec-writer entry: the scan covers start 2's and do 2's direct calls only (do 2 calls `0x0057D690` and others,
    whose calls are unfollowed); now scoped to the direct calls, and the run's 25 zero physicals named as the
    observation that no path added the branch's damage to those deliveries.
  - **Rulings:** (a) **Part 3's `[C]` is honestly scoped** once fix 1 is in: the run observes physical 0 at
    `ApplyDamage` on 25 deliveries, which no reading giving ≥ 195 life points before reductions could match on these
    targets; it does not separate `MinDam << HitShift` from no physical (both 0 on the stock row), and the lane keeps
    that `[I]` on the code and leaves `sub_0056CAF0` I (the start's store is not logged; reviewer rule 14 does not
    apply). (b) **The 7 do events without `ApplyDamage` need no entry.** They contradict nothing: each calls
    `DeliverQueued` with the do's target, and `DeliverQueued`'s gates (melee range, the queued result's bit `0x1`, a
    living attacker; combat/delivery A2 `[I]`) are the candidates, none logged; the § 5 `[I]` bullet now names them.
    A future combat run that logs the queue entry reads them; that is combat/delivery's A2, not Kick's damage.
    (c) Part 2 `[I]` stands: the branch callers are a static `call`-operand scan with 15 variable-id sites named and
    unfollowed (reverser rule 9 satisfied). (d) The spec-writer entry is released with fix 2 applied.
  - **Bookkeeping:** review-fixes Seen lines: reverser 9 and 10. The review request closed; the
    [spec-writer entry](../backlog/archive/2026-10-27-reverser-spec-writer-dispatch-i4-kick-start-hit-answered.md) released.
    Ledger: the lane row filled (accept with fixes, 2: omission 1, overclaim 1; usage from the orchestrator: 171 207
    tokens, 79 tools, 12 min); the review row added, usage "—".
  - **Next:** merge `lane/rk`; the spec-writer entry on dispatch I4 may start.
- **2026-10-27 — `lane/h6e2` review (architect): H6e2 (`quest-items`) accept with fixes (3).** `main` `507a6f5c`
  (`lane/rk`) merged into the lane first (plan log and ledger conflicts kept both sides; `backlog.py archive`: nothing
  to move). Static review: no Ghidra, no harness.
  - **Checked.** The four manifests pass `sha256sum -c` from `workspace/logs/h6e2/` (21 + 2 kept, 10 + 3 dev lines; 11
    kept logs and 8 dev logs, 19 launches). `sweep_h6e2.py check` rerun under `systemd-run --user --scope -p
    MemoryMax=4G` over the 11 kept logs: byte-identical to `check-final.txt` (`d4ce6d6d…`): chest 6, object 2, event7
    19, dup 8, gate 8, gold 45, death 3, 0 mismatches. The chest `k` recomputed from the four logged seeds (9, 5, 9, 8)
    and Wirt's `low32(0x91FDB5F0 · 0x6AC690C5 + 0x29A) mod 10 + 10 = 18`. objdump on the pinned `game.exe`
    (`631066c1…`): `WirtGold` 0x00594651–0x0059469A (`QUESTS_GetSeed`, `RNG_RandLoHi(seed, 10, 20)` with lo in `edx` and
    hi 0x14 on the stack, the count at `+0x8C` set once behind the `+0x90` flag, one `DropItemAtUnit` per event);
    `HeartChest` 0x005B8867 mode test, 0x005B8878 seed, 0x005B88BC `gld ` loop, callback 0x005B8810 (`qhr ` and `qf2 `),
    0x005B8911 the part, 0x005B8931 `ObjectChestDrop`; the thunk `0x00581A10: jmp 0x005449E0`; the `call eax` at
    0x00586B19; the callers at 0x005411BF and 0x00541568; the cube and staff callbacks (0x005997C8, 0x0059977B /
    0x0059978D); the stat-356 compare at 0x005581D2; the gate call at 0x00563631. The orifice a-log
    `quests-s3-3364-duriel-normal.log` hashes to its manifest line (`90e8b37f…`) and holds both `QS` writes.
  - **Fixes.** (1) misread: the Inifuss tree's `bks` was filed "created … quality 2" from the `QDI` argument; the next
    `ICQ` line shows quality 7 (rq 2), the base `unique` override (`bks` has `unique` 1); items/0010's tree bullet, the
    death bullet's After, the answered open question and the spec-writer entry now say so (`box`, `qhr`, `leg`, `unique`
    0, came back at 2). (2) tool not kept: the 24 screenshots of eight kept sessions were outside every manifest;
    hashed into `manifest-shots-final.sha256` (`2f8f0b14…`, 24 lines), noted in the run record. (3) other: items/0010
    § 5's `[I]` chest bullet carried a `[C]` sentence; the correction is now an italic note pointing at the H6e2 section,
    where the tags are.
  - **Rulings.** (a) **Wirt's gold** stays counted **raised** under H6e2, no class move (the `lane/p49r` precedent for
    quest-drops 10 and 19): plan 0043 raised it first on map seed 4506; this run met it on seed 3811, an independent
    quest seed. Phase 3 adds the anchor; objects § L's Wirt's body row, still `[I]` there, is the one raised.
    (b) **The Khalim E1 correction** stands: the code order (gold, part, chest drop) is read and met on the heart chest;
    the eye and brain chests have the same shape and stay `[I]`. (c) **The 18 piles** are `RNG_RandLoHi(questSeed, 10,
    20)` = 10 + (LCG mod 10) on the logged seed, one quest-seed draw at the first event, none at the leg. (d) **The `-a4`
    recipes** (header act bytes 131 = `0x80 | 3` in all three difficulties) are ADR-0003 tool-built inputs (ADR-0013 §
    Neutral; the vendor saves set the act byte the same way): none of the checked code reads the start act, and the
    quest seed and record words are logged at each operate. They support `[C]` for the scripts, nothing about how a
    character reaches Act IV. (e) **The failed routes** are recorded honestly (the brain chest as an open question, the
    two warps in the run record). The warps are a pilot limitation, not a model bug: `descend` takes the first warp of a
    LvlWarp row, and rows 51 and 61 serve two levels each; routed with the brain-chest question to a reverser entry,
    [2026-10-27-architect-reverser-d2pilot-descend-by-destination-and-the-brain-chest](../backlog/archive/2026-10-27-architect-reverser-d2pilot-descend-by-destination-and-the-brain-chest.md).
    (f) **The 11 symbols I → C** stand (rule 14: each one's logged call compared with the checker's model); the
    call-site-only frames stay I. (g) **The quality 7 answer** stands as `[I]` After (items/0004 us 13), now with `bks`.
    (h) **`test_d2s.py`** fails `test_every_recipe_has_a_base` after the merge, on `lane/h3b`'s `h3brare` alone (merged
    into `main` before `lane/a2t`, whose branch lacked it); H6e2's seven recipes have rows. Not H6e2's: routed,
    [2026-10-27-architect-archivist-test-d2s-h3brare-recipe-base](../backlog/archive/2026-10-27-architect-archivist-test-d2s-h3brare-recipe-base.md),
    with the base and the save hash the review rebuilt (`ce57d8f7…`, as the H3b record).
  - **Totals** recounted against `main` `507a6f5c` after merging it (`lane/rk` moved no inventory row): unchanged,
    static 567, harness 519, c-emu 0, blocked 421, deferred 2, raised 17: 1 526. H6e2's ledger: raised 3, raised in part
    14, shortfall 7: 24 (rows: quest-drops 1 + 16 + 1 + 1 + 1, objects 48 × 4).
  - **Readiness.** **objects** is ready for the Phase 3 re-tag (S4a, S4b, H5b, H6e2 all accepted; research-map row
    updated). items/quest-drops still waits on H6e1.
  - **Bookkeeping:** inventory § 2.6 H6e2 block marked accepted with the ruling, § 5 "(done)"; review-fixes Seen lines:
    reverser 6 and 13. The review request closed; the
    [spec-writer entry](../backlog/archive/2026-10-27-reverser-spec-writer-h6e2-quest-items-raises-and-the-khalim-chest.md)
    released (with the `bks` and Wirt points). Ledger: both lane rows filled (usage from the orchestrator: 331 873 tokens,
    178 tools, 39 min to checkpoint 1; 307 855 tokens, 200 tools, 107 min for the resume; accept with fixes, 3: misread 1,
    tool not kept 1, other 1, on the resume row); the review row added, usage "—".
  - **Next:** merge `lane/h6e2`; then H6e1.
- **2026-10-27 — `lane/sk` (spec-writer, no slot, no Ghidra, no harness): the entry released at the `lane/rk`
  review.** [Dispatch § I4](../specs/skills/dispatch.md#i-the-skill-packet): Kick's start hit restated from
  skills/0003 § 5's anchored instructions (`[I]`: `MinDam << HitShift`, hit class 1, no `GetPhysMin/Max` call); the
  stock row's `HitShift` 8 and `MinDam` 0, so physical 0 `[C]` (tbl:Skills.txt); the 25 logged deliveries with
  physical 0 `[C]`, scoped to the packet after `ResolveAndQueue`'s reductions, Normal and the 9 target classes with
  `ResDm` 0; the store against no physical and the 7 do events without `ApplyDamage` `[I]` (combat/delivery A2); the
  `Kick` branch's callers `[I]` (Dragon Talon, Tail and Flight; the Assassin's `str + dex − 20`, the shadow warrior's
  and shadow master's `3 · level`; no direct call of Kick's start 2 or do 2). The `[L]` struck. Tags: dispatch C 73 →
  75, I 189 → 191, L 11 → 10. Wiki: skills (two paragraphs, one open item removed). Entry closed;
  [review request](../backlog/archive/2026-10-27-spec-writer-architect-review-lane-sk-dispatch-i4-kick.md) filed; ledger row
  added, usage "—".
  - **Review (architect, 2026-10-27): accept with fixes (2).** Checked each I4 bullet against skills/0003 § 5's
    2026-10-27 note and the `lane/rk` rulings: the start-2 store `[I]` (instructions `0x0056CB42`–`0x0056CB80`), the
    stock row `[C]` (tbl:Skills.txt), the 25 deliveries `[C]` scoped as ruled (post-reduction packet, Normal, the 9
    classes with `ResDm` 0), the store against no physical and the 7 do events `[I]` (ruling (b), combat/delivery A2),
    the callers `[I]` scoped to direct calls with the 15 variable-id sites (ruling (c), review fix 2); § O's note; the
    anchors in `re/symbols.csv` (`0x0056CAF0`, `0x005D54B0`, `0x00644C20`, `0x0057C1E0`, `0x0057C6C0`, `0x0057D4F0`,
    `0x00647BC0`, `0x00647D00`). Wiki: the two Kick paragraphs say "read from the code" for the store and callers,
    "confirmed" for the 25 hits with their scope; the open item removed. Fixes: (1) *wrong anchor:* start 2's bullet
    anchored `0x0056CB54`–`0x0056CB71` while restating the memset, result, flags, hit class and `ResolveAndQueue`; now
    `0x0056CB42`–`0x0056CB80`. (2) *omission:* the tables-used list lacked `MaxDam` and MonStats `ResDm`, `Skill1`,
    now cited in § I; added. Counts unchanged (C 75 / I 191 / L 10).
  - **Bookkeeping:** research-map row for skills/dispatch rewritten (counts, the `lane/sk` clause, the stale `Kick`
    `MinDam` `[L]` clause removed); review-fixes Seen line: spec-writer 9. The review request closed. Ledger: the lane
    row filled (accept with fixes, 2: wrong anchor 1, omission 1; usage from the orchestrator: 87 940 tokens, 26 tools,
    12 min); the review row added, usage "—".
  - **Next:** merge `lane/sk`.
- **2026-10-27 — `lane/a3r` review (architect): accept.** The `tools/` diff is the one `h3brare` `RECIPE_BASES` row; a scratch rebuild of `h3brare.json` (`52aa64e8…`) on `smpsor-l50.d2s` gives `ce57d8f7…6317`, the H3b record's save hash (data/experiments); `test_d2s.py` 47 tests OK; the [review request](../backlog/archive/2026-10-27-archivist-architect-review-lane-a3r-test-d2s-h3brare-row.md) closed; ledger lane row filled (usage from the orchestrator), review row usage "—".
- **2026-10-27 — Phase 3, the save/d2s and items/uniques-sets clusters (spec-writer, `lane/s38s`, from `main`
  `cb3a7014`).** Their batches are save/d2s S1a, S1e, H1b (with the r1h moves) and H1a, and items/uniques-sets S2b,
  S2c, S1f, H2b, H6d and H1a, all accepted.
  - **Counts:** [save/d2s](../specs/save/d2s.md) {C 91, I 149, L 3} → **{C 239, I 67, L 3}**;
    [items/uniques-sets](../specs/items/uniques-sets.md) {C 71, I 55, L 4} → **{C 100, I 38, L 4}**; `updated:` 2026-10-27.
  - **Applied:** every raised row with its `run:` or second source, raised-in-part rows split along their remainders;
    the H1a new readings (`D2S_ReadSave`'s unmapped 9, the length test first and the test order, the waypoint marker
    reset and `WAYPOINT_Save`'s restore, a bad set id dropping the item, a bad unique id read −1 and written `0xFFF`,
    stat 72 in 8 bits for item version ≤ 95, the `0x29` count bounding the old stat form, class 7 halting); H1a ruling
    1 as one `[I]` reach note; rows 20/34's −1 reach condition as an `[I]` note under the class-7 `[C]`; the d-none
    halves (row 50's ladder, row 139's `gf`, rows 3/19 and the callback halves of 2/18 per r1h) and the legacy
    shortfalls `[I]`; H1b ruling (c) (the death save `[C]`, "Nothing was written during play" scoped to
    run:2026-10-12-d2s-io) and (g) (stat 30's wording); the S1a entry's (b)–(g), the S1e (a)/(f) and review (d) lines,
    S1f (a)/(c), H2b (c)–(g) and H6d (i).
  - **Wiki:** [saves](../wiki/saves.md), [characters](../wiki/characters.md) and [items](../wiki/items.md) `based_on`
    dates set to 2026-10-27 (W4 clear); saves and items restated, characters waits on player/creation and hirelings.
  - **Backlog:** closed the S1a corrections, S1e corrections, S1e review additions and S1f entries; annotated H1b
    (hirelings, H6f), H1a (player/creation H6g, hirelings H6f, (k)), H6d (quest-drops) and H2b (sockets-runewords).
    Counts entry [s38s counts](../backlog/archive/2026-10-27-spec-writer-architect-s38s-save-d2s-and-uniques-sets-counts-for.md),
    review request [s38s review](../backlog/archive/2026-10-27-spec-writer-architect-s38s-review-save-d2s-and-uniques-sets-phase.md).
    Ledger row added, usage "—".
  - **Not touched (waiting):** hirelings (H6f) and player/creation (H6g): the H1b and H1a rows hirelings 3, 24, 30,
    32, 33 and player-creation 1, 8, 9, 11, 20, 34, and the H1a entry's (k) (data/calc L417, rng/seeds L362).
  - **Next:** the `lane/s38s` review.
- **2026-10-27 — `lane/s38s` review (architect): accept with fixes (9).** Phase 3 of the save/d2s and
  items/uniques-sets clusters, reviewed at `3f4ffcf7` after merging `main` `507a6f5c` into the lane (`c95617d8`;
  conflicts in this log and the ledger, both appends, kept both sides; `backlog.py archive` moved nothing). Static
  review: objdump on the pinned image, the kept check outputs read (`workspace/logs/h1a/check/sweep-h1a-check.txt`,
  `workspace/logs/r1h/sweep-h1b-check-r1h.txt`), no Ghidra, no harness.
  - **Trace.** save/d2s's new `[C]` (148, plus 1 here) traced, more than a third of them, to the ledger lines of these rows in save/0001 § S1a (rows 5, 7, 8, 11–16, 20,
    45, 51, 58, 61–64, 66, 69–71, 74–76, 79, 84–87, 93, 94, 96–101, 109, 119–121, 123, 131), § S1e (82, 122, 129, 133),
    § H1b (rows 2, 4, 6, 18, 21, 25, 31, 33–43, 48, 55–57, 60, 72, 73, 83, 88, 102, 108, 111–113, 115, 116, 118, 125,
    127) and § H1a (rows 9, 22, 23, 26–30, 36, 38, 44, 46, 47, 49, 50, 52–54, 59, 62, 65, 68, 80, 90, 91, 105–107, 132,
    139, 140; player-creation 8, 9, 11), each within its review's scope; uniques-sets's new `[C]` (29) traced to the lines of
    items/0004 § S2b (us 3, 4, 5, 6/28, 13, 15, 20, 23, 24, 27, 29, 32, 33, 34, 36, 40, 42), S2c (us 1), S1f (us 44)
    and H2b (us 7, 9, 35, 39). The H1a new readings each have a `CASE` line in the kept check (`short`, `magic`,
    `hdrshort`, `fields`, `wpbad`, `setbad`, `uniqbad`, `v94`, `v94s12`, `slots8`, `class7`, `stub7`). The second-source
    bullets restate their rows' evidence and raise no claim beyond the rows' scope; no inflation by restatement.
  - **Rulings:**
    1. **Rows 20/34 and the class-7 halt.** No conflict. The halt (class 7 passes the class test, the game stops at
       `sub_00553180`'s null-unit test, 1210) is player-creation row 11, raised by H1a on `RCST`/`RMAP` and the two
       crash reports, so a spec states it `[C]`. Rows 20 and 34 are the readings that need a class-7 player (the
       experience column, the starting kit); the halt shows none exists, so they are d-none and stay `[I]`. The spec's
       class-7 bullet now cites row 11; inventory § 2.6 states the distinction under the s38s block.
    2. **The cross-spec tag on the wiki.** Spec-writer rule 1 is for specs that disagree on the evidence. The header
       test order (player-creation 8, H1a) and the merc header's write side (hirelings 24, H1b) are accepted ledger
       raises that player/creation A2 and hirelings F8 have not yet absorbed (H6g, H6f). A page follows the spec that
       carries the raise and links its section; the lagging specs take it in their own rounds. wiki/saves stands;
       wiki/characters, which left both "read from the code", now follows save/d2s D3 and § D (rule 1 scoped in
       spec-writer review-fixes).
    3. **H1b ruling (c)** is applied as filed: § Entry points states the death save `[C]` as an event save, and
       "Nothing was written during play" is scoped to run:2026-10-12-d2s-io. The wiki's "in one case: a death" is
       scoped to what was logged (fix 6).
    4. **The S1a pieces H1b met.** A piece may not be raised without a ledger line; this review gives two of them
       one, since H1b's kept check compares them: **row 24** (the swapped set's write: `weapon_set bit 0` equal to the
       logged `+0x45C` in rt-r2's four writes) and **group 52** (`group 52 stats 52/53 = file` on `9cr`, three reads,
       one of them of the game-written file) → rows 24, 123 and 138 raised, row 130's group-52 remainder met. **Row
       32's `& 0xFFF` mask** stays `[I]` (the H1b hotkey check compares the written words, not the read), and **row
       20's pet-type-7 test** stays `[I]` (no other pet type separates it). S1a's ledger: raised 42, in part 12,
       returned 2. Totals unchanged (static 567, harness 519, c-emu 0, blocked 421, deferred 2, raised 17: 1 526).
    5. **H1a's stat-72 width reads the save version**, not the item's: `ITEMS_ReadFull` tests its version argument
       (`cmp [ebp+0x1C], 0x5F; ja`, 0x0062D425, 0x0062D759), the `v94` items kept item version 101, and every version
       test of the reader reads the same argument. The `lane/h1a` review's "item version ≤ 0x5F" is corrected here and
       in save/0001 § H1a.
  - **Fixes applied (9):** (1) wrong anchor: a `{P}` token as J's `ValShift` run anchor. (2) misread: I5's "item
    version ≤ 95", and the Tables row, I3's 72–88 note and J2's 1.09 line, now "save version" (ruling 5). (3)–(5)
    overclaim: version 95 inside F2's and I5's `[C]` (only 94 and 96 loaded; `cmp eax, 0x5E` at 0x0056A627 for F2),
    `WAYPOINT_Save`'s 0x0101 case inside E2's `[C]` block, Outputs' "at most 8 KiB" inside a `[C]` bullet. (6)
    overclaim: wiki/saves "in one case: a death". (7) stale cross-reference: wiki/characters' stub-order and saved-merc
    paragraphs. (8) under-claim: rows 24 and group 52 (ruling 4) in the header table, J1, J, the reimplementation note
    and wiki/saves. (9) other: the class-7 bullet's row citation (ruling 1). Also wiki/saves: the stat-72 wording and
    "the size and version tests were not told apart".
  - **Counts:** [save/d2s](../specs/save/d2s.md) **{C 240, I 68, L 3}** (from the lane's {239, 67, 3}: C +1 group 52;
    I −3 for rows 24, the J1 line and the reimplementation note, +4 for the 95 boundaries, the 0x0101 case and
    Outputs); [items/uniques-sets](../specs/items/uniques-sets.md) **{C 100, I 38, L 4}** as filed. Research-map rows
    rewritten whole; both clusters' Phase 3 is done.
  - **Wiki:** saves, characters and items checked against the specs; saves and characters fixed (fixes 6–8), items
    stands.
  - **Backlog:** the review request and the counts entry closed. The H1b, H1a, H6d and H2b spec-writer entries stay
    open for hirelings (H6f), player/creation (H6g), quest-drops and sockets-runewords. Review-fixes Seen lines:
    spec-writer 1 (with the scope), 2, 3, 7 and 9; architect 2 and 3.
  - **Ledger rows:** the lane row filled (accept with fixes, 9: overclaim 4, misread 1, under-claim 1, wrong anchor 1,
    stale cross-reference 1, other 1; usage from the orchestrator: 457 804 tokens, 114 tools, 33 min); the review row
    added, usage "—".
  - **Next:** merge `lane/s38s`; hirelings (H6f) and player/creation (H6g) take the H1a/H1b raises left for them.
- **2026-10-27 — `lane/rdp` review (architect, static, no Ghidra, no harness): accept with fixes (4).** The answer to
  the `lane/h6e2` review's reverser entry: `d2pilot.py farm --descend ROW --descend-to LEVEL` and `--all-copies`
  (opt-in), the RL `lid` key in `tools/gdb/pilot.py`, the `eye4c`/`tome4c`/`brain4c` recipes (not run), and
  items/0010 § The brain chest in level 91.
  - **Checks:** `sha256sum -c manifest-rdp.sha256` from `workspace/logs/rdp/` passes (2 lines);
    `test_d2pilot_descend.py` 10 tests OK; `rdp_brain91.py` over `brain4` and `brain4b`, rerun under `MemoryMax=4G`,
    gives `50e0f953…`, byte-identical to the kept `brain91.txt`.
  - **Rulings:**
    1. **Backward compatible.** Without `--descend-to` and `--all-copies` the pilot's state and choices are unchanged:
       the pre-lane `d2pilot.py` (`1e61473c`) and the lane's, replayed over all 19 kept H6e2 logs, give equal `rl`,
       `lptr`, `active`, `wrp`, `warps`, `pos` and `lid_of`, equal `frontier()` for every level, and equal warp cells
       (old comprehension against `descend_cells(st, lid, {row})`) for all 67 (level, row) pairs. The default path's
       messages are the same strings (`dest` None: the old format, no suffix). WRP lines carried `room` since the
       logger's first version (`3c02956c`), so `wrp_room` cannot fail on an old log. The kept recipes of
       `h6e2_sessions.py` are untouched.
    2. **The RL `lid` key breaks no reader.** RL consumers in `tools/` (`d2pilot.py`, `drlg.py`, `monspawn.py`,
       `sweep_s4a.py`, `outdoor_replay.py`, `rdp_brain91.py`) read the line by key; none compares whole dicts or key
       sets. `PRL` (the renamed tag under `drlg-*.gdb` and `sweep-*.gdb`) has no Python reader.
    3. **"Why the pilot stopped" stays `[C]`**: it is our tool's own code (one `lptr` per level, overwritten at each
       `RRESEED`) replayed over the logs (`test_brain_frontier_copies`). **The copy bullet stays `[C]`** on two
       sources: the DS1 data and the logs' 0/0 match (29 and 47 objects). What it does not reach, that the chest is
       listed once its room activates in the matching copy, is a prediction: now `[I]` under the bullet, the struck
       open question "answered in part", and an open question added (fix 1).
    4. **"`OBJS` filters neither class nor distance" stays `[C]`**: `tools/gdb/vendors.py` (read here) walks the 128
       heads at server game `+0x1520`, chain `+0xE4`, ≤ 512 per head, and keeps every unit with a path record
       (`+0x2C` non-zero), one line per 2 s at most; the logs' exact match is the second source. No objdump needed:
       the walk is our logger, not game code.
    5. **"Which copy is the server's" stays `[I]`**; the repository already holds the server/client pair and its flag
       (drlg/0004 row 10, room `+0x28` & `0x40000`), now cited, and the pilot logger does not log `+0x28` (fix 2).
    6. **The chest on every seed** stays `[I]` (one of six files by `Range(seed, Files)`; creation from the DS1 unit
       not re-read). The `g_Ds1ObjectIds` 115 → 406 mapping is read from the pinned exe and reproduced over 2 362 units
       (drlg/0004 row 5); its symbol row's `I` is about the role, not the bytes.
    7. **The three reruns: an H6e2 follow-up**, not H6f or H6g. They are H6e2's failed routes (eye and brain chests,
       the tome), on H6e2's save (`a4/QuestFreshT`) and map seeds 4913–4915; H6f (hirelings) and H6g (player/creation)
       share neither. One short harness lane, three sessions; `brain4c` decides ruling 3's `[I]`. The follow-up may add
       room `+0x28` to the RL line first (one key, as `lid`), so `brain4c` also names the copy (ruling 5). Not blocking
       the objects cluster's Phase 3.
  - **Fixes applied (4):** (1) overclaim: the "Answered" strike and the copy bullet's unstated remainder (ruling 3).
    (2) omission: drlg/0004 row 10 cited in "Which copy is which" (ruling 5). (3) miscount: "four of the six
    positions are corners" for five files (four distinct positions). (4) stale cross-reference: `brain_mem`'s
    docstring in `tools/h6e2_sessions.py` still said `OBJS` lists only the objects near the player (annotated; the
    recipe unchanged).
  - **Backlog:** the review request closed. Review-fixes Seen lines: reverser 2, 4 and 12; architect 4 (the
    `lane/h6e2` review passed "near the player" unread).
  - **Ledger rows:** the lane row filled (accept with fixes, 4: overclaim 1, miscount 1, omission 1, stale
    cross-reference 1; usage from the orchestrator: 196 386 tokens, 79 tools, 18 min); the review row added, usage "—".
  - **Next:** merge `lane/rdp`; file the H6e2 follow-up (eye4c, tome4c, brain4c) when a harness slot is free.
- **2026-10-27 — Phase 3, the objects cluster (spec-writer, `lane/s38o`, from `main` `1e61473c`).** Batches S4a, S4b,
  H5b and H6e2, all accepted; each restated statement checked against its section of
  [objects/0001](../findings/objects/0001-object-population.md) (§ Plan 0038 batch S4a, S4b, H5b) or
  [items/0010 § Plan 0038 batch H6e2](../findings/items/0010-quest-drops.md#plan-0038-batch-h6e2-run2026-10-27-sweep-quest-items)
  and the four reviews' rulings.
  - **objects** {C 139, I 72, L 5} → **{C 188, I 56, L 4}** (recounted with the gate's tag reader). Raised: rows 1, 2,
    8, 9, 11, 13/51, 14, 16, 17, 22, 37, 40, 45, 50, the 52 timing (its types 8/9 draw kept `[I]`), 47 for the
    Hellforge, 48 Wirt's body; row 7 adds S4a's 190 restores beside the lifecycle `[C]`. Split along the ledgers'
    remainders: 3/15 (the `> roomCount ÷ 8` half; `= 10` and the well cap `[I]`), 4 (trap types 1–7 modelled, 8/9
    `[I]`), 23 (`0x400` door, zero size; `0x804` no stock case), 26 (57, 58; 79 `[I]`), 27 (47, 66, 25, 71 reached),
    28 (13 reached `InitFn`s), 36/38 (level 25; whole byte and the `PreOperate` half `[I]`), 41/42 (the branches
    reached), 43 (the survey; the indirect routes `[I]`), 48's chests (Act II chests and the Khalim heart chest in the
    corrected order, eye and brain `[I]`), item objects (`leg`, `bks`; `bks` created at 7) and orifice (the bits).
    Restated, not raised: row 20 and the d-none halves as no stock case, row 25 with the nine monster-creating
    `InitFn`s (S4b (a)), the H5b shortfalls (6, 19, 35, 39, 46, 49) in *Open questions*. Beyond the inventory: § K's
    event-7 route for classes 268 and 367 (qd 1, rule 8) and § J3's tier and `ilvl` (S2a tc 64 (b)), striking the
    tier-cut `[L]`. K2 is rewritten from H5b.1 (the remap, the function table, class **160** second).
  - **Wiki:** [objects](../wiki/objects.md) refreshed and its `based_on` set to 2026-10-27; [seed-to-world](../wiki/seed-to-world.md)
    date only.
  - **Backlog:** closed the [H5b spec updates](../backlog/archive/2026-10-20-reverser-spec-writer-h5b-objects-spec-updates.md),
    the [S4b corrections](../backlog/archive/2026-10-16-reverser-spec-writer-plan-0038-s4b-corrections-for-phase.md) and the
    [S2a tc 64](../backlog/archive/2026-10-16-architect-reverser+spec-writer-plan-0038-s2a-tc-64-and.md) entries; annotated the
    [H6e2 entry](../backlog/archive/2026-10-27-reverser-spec-writer-h6e2-quest-items-raises-and-the-khalim-chest.md) (objects done,
    quest-drops waits for H6e1); filed the [counts entry](../backlog/archive/2026-10-27-spec-writer-architect-s38o-objects-counts-for-the-research-map.md)
    and the [review request](../backlog/archive/2026-10-27-spec-writer-architect-s38o-review-objects-phase-3.md). Ledger row
    added, usage "—".
  - **Next:** architect review of `lane/s38o`.
- **2026-10-27 — `lane/s38o` review (architect): accept with fixes (8).** Phase 3 of the objects cluster, reviewed at
  `1b8846cc` after merging `main` `af36891d` into the lane (`4b50aa08`; conflicts in this log and the ledger, both
  appends, kept both sides; `backlog.py archive` moved nothing). Static review: objdump on the pinned image
  (`631066c1…`), the 29 objects logs grepped, `tools/objects.py` read, no Ghidra, no harness.
  - **Trace.** Of the 50 new `[C]`, more than 35 traced to their batch lines within the reviews' scopes: S4a rows 7, 8,
    9, 11, 14, 28, 37, 47; S4b rows 1, 2, 22, 43 and row 25's restatement (`[I]` kept); H5b.1 (the remap's reached case,
    the 35-frame queue, the trap monsters, 162 then 160), H5b.2 (handler 1's sizes, the cap's `÷ 8` half, the forced
    conversion, theme 3), H5b.3 (the `0x400` door, the zero size, `InitFn` 57, 58 and the quest `InitFn`s, the level-25
    chest), H5b.4 (`OperateFn` 1, 26, 48, 68 on the branches taken); the S2a tc 64 entry (b) under the S4b review's
    ruling (5) for J3's tier and `ilvl`; items/0010 § H6e2 (qd 1's route, the three Act II chests, the heart chest,
    Wirt's body, `leg`, `bks`, the orifice bits). The H6e2 rulings are applied: Wirt's row raised, the Khalim order `[C]`
    on the heart chest only, `bks` created at 7 with the override `[I]`. K2's rewrite follows H5b.1 and the 160
    correction; no `162` twice is left in specs or wiki.
  - **Steps under `[C]` headers no run reached** (fixed): C1's `ThemeRoll = 1` return (no theme runs, C2), E2's
    `else 84`, K2's `t ≥ 10` returns, the types 8/9 refusal in `OBJ_TrapFire` and the type-1 half of the `{1, 4}` remap,
    each now tagged `[I]` inline (the type-4 half `[C]`).
  - **Rulings on the lane's points.**
    1. **H5b.2's "before any draw".** objdump: `OBJPOP_Shrine` steps the room seed (0x00552B9A–0x00552BBA) before
       `HealthShrineDue` (0x00552BC5) and the cap test (0x00552BF7), and `tools/objects.py` `pop_2` draws `P100` before
       the cap, so the seeds that matched after the two cap returns confirm the draw. E2's order and § E's count stand;
       the finding means "before any placement draw". The spec's *Constants* row, which copied the finding's words, is
       fixed; the finding's wording goes to the reverser
       ([entry](../backlog/archive/2026-10-27-architect-reverser-h5b-shrine-cap-wording.md)). No code question.
    2. **7 against 4 super chests.** The 29 logs hold 7 `OPU0` lines with id 580 at 7 distinct positions (sessions 3:
       three in level 79; 13: level 44; 29: two in level 62; 30: level 4), each run through the checker's 580 model, so
       S4a's 7 counts creations, not re-creations or windows twice. The run record's "super chests (DS1 580) 4, all
       sparkle" is its first summary line, a different count; § I's 580 row now cites the 7 and names the 4, and
       wiki/objects says "seven recorded super chests", not "sparkle".
    3. **Row 52's split** is accepted (spec-writer rule 2): the queue and the 35 frames `[C]`, the types 8/9 draw `[I]`,
       and the remap note `[C]` for type 4 in level 35 only.
    4. **Row 7's second `[C]`** is accepted as a separate statement: it confirms the save test on another run and on the
       populated objects with the level flag, which the lifecycle bullet does not cover. B4's header now names both runs.
    5. **The raises beyond the inventory rows are allowed.** § K's event-7 route restates items/quest-drops qd 1's accepted
       H6e2 raise (spec-writer rule 8), and § J3's tier and `ilvl` are the S2a tc 64 raise accepted at the S4b review
       (5); neither goes past its batch's scope (the route for classes 268 and 367 only; the `|b − a|` and return-1
       guards `[I]`).
    6. **wiki/items-other-paths' chest order** waits for items/quest-drops' H6e1 round, as the H6e2 entry records; the
       page follows quest-drops § E1, which has not taken the correction yet, and wiki/objects already states it.
  - **Fixes (8):** the four steps above (overclaim 3); wiki/objects' "sparkle chests" (overclaim 1); B4's header
    without run:2026-10-15-objects (under-claim 1); *Constants*' "before any draw" (misread 1); § I's 580 row "4"
    (miscount 1); K2's `OBJ_TrapFire` without its code-pointer check and the `sub_00553380_UnitSetEvent(object, 13)`
    after the queue (0x005825A4; omission 1).
  - **Counts:** objects **{C 189, I 62, L 4}** (recounted with the gate's `RE_TAG`; the lane's 188 / 56 plus the review's
    1 `[C]` and 6 `[I]`), `updated:` 2026-10-27; research-map row rewritten whole. wiki/objects and wiki/seed-to-world
    checked against the spec (seed-to-world states nothing that moved).
  - **Bookkeeping:** review-fixes Seen lines, spec-writer 2, 3, 4 and 5. The review request and the counts entry closed;
    the reverser wording entry filed. Ledger: the lane row filled (accept with fixes, 8: overclaim 4, under-claim 1,
    misread 1, miscount 1, omission 1; usage from the orchestrator: 297 611 tokens, 122 tools, 18 min); the review row
    added, usage "—".
  - **Next:** merge `lane/s38o`; objects is done for plan 0038 Phase 3.
- **2026-10-27 — `lane/a71` (archivist, no slot, no Ghidra, no harness, from `main` `44cfbcb5`): the H1a parser gaps.**
  Work of the [H1a archivist entry](../backlog/archive/2026-10-27-reverser-archivist-h1a-d2s-legacy-layouts-and-parser-gaps.md).
  - **Built** (`tools/d2s.py`, every change off by default): an extended reader and writer (`parse(…, extended=True)`,
    `encode_item(…, ver)`) and the build keys `save_version` 93..96, `stat_slots`, `skill_count` and the item key
    `realm`: the old stat form for ≤ 94, stat 72 in 8 bits for ≤ 95, header `0x2A` skill bytes, realm data (two
    words, three above 93) and an ear's realm bit after its name. Version 92 and the legacy versions are refused.
    `tools/test_d2s.py` `ExtendedTest`: 8 tests; the file runs 55 tests OK.
  - **Proof of byte identity:** the 259 `RECIPE_BASES` recipes rebuilt into the scratchpad before and after give the
    same sha256; `d2s.py roundtrip` on the 18 sample and owner saves stays 205 items, 0 diffs; `sweep_h1a.py check` on
    the five H1a logs prints its kept output byte for byte.
  - **Against the run:** `build` with the new keys reproduces the H1a inputs `v94`, `v94s12` and `skills29` byte for
    byte, and the extended reader reads `items` and all 16 game-written H1a saves to their last byte, re-encoding
    every item unchanged (the written realm words `[0x11223344, 0x55667788, 0]`).
  - **Documented** ([d2s.md](../formats/d2s.md)): § Realm data, § Versions 92..95 (the version tests the findings
    name, the old stat form `[C]`), § Legacy versions (71..91) (what the findings give, and the list of what they do
    not), the character-screen list rule, and the H1a `[C]`s for `0x029`, `0x02A`, ears, personalized names.
  - **Not done:** the version 71/87 layouts and a legacy builder, version 92's property overrides, the completeness of
    the version-test list, the old-form mask width outside `0x029` = 12, 16, and the reader side of the ear's realm
    bit: reverser entry [2026-10-27-archivist-reverser-d2s-legacy-and-v92-readers-static-reading](../backlog/archive/2026-10-27-archivist-reverser-d2s-legacy-and-v92-readers-static-reading.md).
    So the legacy rows (hirelings 3, 30, 33; player-creation 1; items-uniques-sets 21) and save-d2s 126 stay
    shortfalls under ruling 5. The H1a entry is annotated and stays open for the legacy builder.
  - **Backlog:** review request [2026-10-27-archivist-architect-review-lane-a71-d2s-versions-93-95-realm](../backlog/archive/2026-10-27-archivist-architect-review-lane-a71-d2s-versions-93-95-realm.md). Ledger row added, usage "—".
  - **Next:** the `lane/a71` review.
- **2026-10-27 — `lane/a71` review (architect): accept with fixes (5).** From the lane's head `5558db55` with `main`
  `af36891d` merged in (`fe4285dc`; the log and ledger conflicts kept both sides). Static, scratchpad builds only, no
  Ghidra, no harness.
  - **Checks:** the 259 `RECIPE_BASES` recipes rebuilt with `main`'s `tools/d2s.py` and the lane's give the same 259
    sha256; `dump` on the 20 sample and owner files (two of them stubs) and on the 38 H1a saves prints the same with both
    tools (the refusals included); `roundtrip` on the 18 full saves 205 items, 0 diffs; `tools/h1a_saves.py` regenerates `v94`,
    `v94s12`, `skills29` and `items` byte for byte against `workspace/runtime/h1a/`, and `ExtendedTest` builds the three
    from the new keys byte for byte; `tools/sweep_h1a.py check` on the five H1a logs prints the kept
    `sweep-h1a-check.txt` byte for byte; `python3 -I tools/test_d2s.py` 55 tests OK. Fourteen anchors spot-checked
    in `re/symbols.csv` (`D2S_ReadSave`, `D2S_ReadHeader`, `D2S_ReadStats`, `D2S_ReadSkills`, `ITEMS_WriteFull`, the
    two character-list functions and the seven legacy readers): all resolve. The legacy section's six bullets each
    trace to save/0001, player/0001, hirelings/0001 § 7, rng/0002, data/0001 P1b or items/0004; none states a layout.
    The refusals hold: 92 (reader and builder), < 92 and > 96 (builder), `stat_slots` outside 9..16 (both readings of
    the mask width give 2 bytes there), a stat at or above `0x029`, a cut-off skill byte, version-96 trailer items in
    another version, and realm-word counts that do not fit the version. No game data in the diff.
  - **Fixes** ([d2s.md](../formats/d2s.md)): (1) under-claim: "the version tested for stat 72 is the save's" `[I]` →
    `[C]` with the `[ebp+0x1C]` test, as save/0001 row 68's `lane/s38s` review note and the spec give it (the `v94`
    items' version 101 separates it); 95 itself `[I]`. (2) overclaim: the `realm` field row's version test (third word
    above 93) was under the row's `[C]`; now `[C]` for 96, the test `[I]`. (3) misread: § Realm data said the field
    "closes every item record"; an extended item's `defense`, `maxdur`, … follow it. (4) misread: § Versions 92..95's
    "the findings name no other" version test, where save/0001 names the class-affix base tests at ≤ 88 / 89 and the
    72–88 jump table; scoped to tests a 92..96 file can meet. (5) stale cross-reference: the open question "branches no
    sample exercises" still listed ears, personalized names and realm data, which the lane raised to `[C]`.
  - **Rulings:**
    1. **The default path is unchanged**: every new behaviour sits behind `extended`, `ver` or a new recipe key, and
       the evidence above shows the 96 reader, writer and builder byte-identical.
    2. **The ear's realm bit and the `+0x20` write condition stay `[I]`** on the reverser's addresses
       (0x0062B277 → 0x0062B2E2 → 0x0062B341, 0x0062B341–0x0062B387), which are in the reverser's H1a archivist entry,
       not yet in save/0001; the reverser entry (e) asks for the read side, and its answer should record both in
       save/0001. The tool's extended form taking the bit is a test state, labelled as such.
    3. **Ruling 5 holds: the H1a legacy rows (hirelings 3, 30, 33; player-creation 1; items-uniques-sets 21) and
       save-d2s 126 stay shortfalls**, not d-none. The character screen lists a version 71..91 file of `0x82` bytes and
       a 92 file (`0x0043C8A0`), and `D2S_ReadSave` sends < 92 to the legacy reader (`v91`, `[C]`), so the code is
       reachable by a file the stock game shows; what is missing is a layout to build, which the findings do not give.
       They move only on the reverser entry
       [2026-10-27-archivist-reverser-d2s-legacy-and-v92-readers-static-reading](../backlog/archive/2026-10-27-archivist-reverser-d2s-legacy-and-v92-readers-static-reading.md):
       (a) for the legacy rows (d-none only if every legacy layout is refused), (b) for 126.
    4. The H1a archivist entry stays open for the legacy builder, as the lane left it.
  - **Bookkeeping:** review request closed
    ([archive](../backlog/archive/2026-10-27-archivist-architect-review-lane-a71-d2s-versions-93-95-realm.md));
    ledger: the lane row's usage filled from the orchestrator (230 283 tokens, 72 tools, 20 min), verdict and fixes
    filled, the review row added with usage "—"; archivist review-fixes rules 1 and 4 gain `lane/a71` Seen lines.
  - **Next:** merge `lane/a71`; the reverser takes the legacy and version-92 readers entry.
- **2026-10-27 — `lane/rlg` (reverser, static, no slot, no harness, no emulation, from `main` `1f8c0858`): the d2s
  legacy and version-92 readers.** Work of the archivist entry
  [2026-10-27-archivist-reverser-d2s-legacy-and-v92-readers-static-reading](../backlog/archive/2026-10-27-archivist-reverser-d2s-legacy-and-v92-readers-static-reading.md)
  (`lane/a71` review rulings 2–3). Ghidra on the lane copy `workspace/ghidra-rlg` (decompile only, `-Xmx3G`), objdump,
  and `tools/rlg_static.py` (kept output `workspace/logs/rlg/static.txt`, manifest `rlg-manifest.sha256`,
  `RLG_STATIC hits=73 functions=42`).
  - **Written** ([save/0001 § Plan 0038 lane/rlg](../findings/save/0001-d2s-io.md#plan-0038-lanerlg-the-legacy-and-version-92-readers-static-2026-10-27),
    all `[I]`): (a) the version 71..91 layout: the `0x82`-byte header and its tests and codes, the ten sections in
    order with their tags and lengths, the 3-byte stat mask, the version-71 item record's four forms, the mercenary's
    two forms, the hotkey tail; no checksum or size test; failures after the skills do not fail the load. (b) version
    92: the 1.09 columns for every width including the fixed fields, no param in the generic path, the ≤ 92 per-id
    encodings, the fold into stat 127, a set item's `Sets` id. (c) the 92..96 version tests: 68 of 73 compares are
    version tests, 29 met by 92..96 with a version-dependent result; 93..95 differ from 96 in the stat form, stat 72 and
    the third realm word only. (d) the old-form mask is ⌈`0x029`/8⌉ bytes. (e) the reader takes an ear's realm bit
    after the name; the writer writes realm data only when item data `+0x20` ≠ 0. save/0002 § 1 gains the legacy
    quest reader. 17 symbols added (I).
  - **Ruling 3:** no legacy version is refused, so hirelings 3, 30, 33, player-creation 1 and items-uniques-sets 21
    stay shortfalls; none is proposed to move. Save-d2s 126 likewise (the layout is now given).
  - **Backlog:** the entry closed; archivist entry
    [2026-10-27-reverser-archivist-d2s-legacy-layouts-for-a-builder](../backlog/archive/2026-10-27-reverser-archivist-d2s-legacy-layouts-for-a-builder.md);
    review request [2026-10-27-reverser-architect-review-lane-rlg-d2s-legacy-and-v92-readers](../backlog/archive/2026-10-27-reverser-architect-review-lane-rlg-d2s-legacy-and-v92-readers.md).
    Ledger row added, usage "—".
  - **Next:** the `lane/rlg` review; then the archivist's legacy builder.
- **2026-10-27 — H5b.2 shrine-cap wording (reverser, `lane/rsw`).** The `lane/s38o` review's ruling 1 is carried into
  objects/0001 § H5b.2: the shrine cap returned "before any placement draw (after the handler's `P100(S)` draw)", with
  a dated correction naming the room-seed step at 0x00552B9A–0x00552BBA, `OBJRGN_HealthShrineDue` at 0x00552BC5 and
  the cap call at 0x00552BF7 (objdump of 0x00552B50–0x00552C10). No other finding repeats the wording; no tag, symbol
  or spec change. The entry is closed
  ([archive](../backlog/archive/2026-10-27-architect-reverser-h5b-shrine-cap-wording.md)); review requested
  ([entry](../backlog/archive/2026-10-27-reverser-architect-rsw-review.md)).
- **2026-10-27 — `lane/rsw` review (architect): accept with fixes (1).** objdump of 0x00552B50–0x00552C10 on the pinned `Game.exe` matches the correction (seed step 0x00552B9A–0x00552BBA, `HealthShrineDue` 0x00552BC5, cap call 0x00552BF7), the wording matches objects/README *Constants* and E2, and the grep finds no other copy; fix (omission): the note now also cites the `% 100` test at 0x00552BDB–0x00552BF0 (skipped when the health shrine is due); request closed ([entry](../backlog/archive/2026-10-27-reverser-architect-rsw-review.md)).
- **2026-10-27 — `lane/rlg` review (architect): accept with fixes (4).** `sha256sum -c` passes on
  `rlg-manifest.sha256`, and a rerun of `python3 -I tools/rlg_static.py` gives a byte-identical `static.txt`
  (`RLG_STATIC hits=73 functions=42`). objdump of the pinned `Game.exe` matches the version dispatch (0x00534330–0x00534390),
  the header's length test and `0x47`..`0x60` accept (0x00532717–0x005327B8, 0x00532BA9), the quest, waypoint, NPC and
  stats tags, offsets and lengths (`Woo!`/6/`0x12A`, `WS`/`0x50`, `0x7701`/`0x34`, `gf` values at `+0x05`), the
  swallowed item, corpse and mercenary returns (0x00534246–0x00534283 → 0x0053429A), the 25-byte version-71 records (195
  bits, `mov eax, 0x19` at 0x0053322A and 0x0053332C), the mercenary's two forms, the hotkey tail's ≥ 73 and ≥ 82 tests,
  the version-92 width index (`ebx` = 1 below 93, 0x0062D2F1; `+0x19 + ebx`, `+0x24 + 4·flag`), the `(n + 7) / 8` mask
  (0x0056A643–0x0056A659), the ear's jump into the realm tail (0x0062AA91 → 0x0062AB1A, `> 0x56` at 0x0062ABFF) and the
  writer's second-word test (0x0062B341–0x0062B387). The 73 compares recount as 5 + 29 + 39.
  - **Fixes:** (1) misread: `D2S_ReadSave` sends every version 0..91 to the legacy reader (an unsigned `jbe`), so 0..70
    fail the header's version test with 1 (9 on the host path); the finding said that case is never sent. Corrected in
    § (a), the Answer bullet and the archivist entry. (2) omission: the header's left and right skills are returned to
    the caller and applied after the skills section, only when non-zero (0x005341EC–0x00534210); the header table now
    says so. (3) omission: the per-version base-adjustment constants a 72..88 builder needs (`0x295`/`0x4EE` for 72, 73,
    80..82; `0x2A2`/`0x4F1` for 83, 84; `0x2A3`/`0x4F2` for 85..87; `0x2D9`/`0x5A0` for 88; none for 74..79) added from
    0x0062CDDC–0x0062CE10, and the H1a row 87 note's "72–88" scoped. (4) stale cross-reference: "the ItemStatCost table
    doc" and Data touched's "no table doc yet" now link `docs/tables/ItemStatCost.md`, whose record layout gives `+0x028` = 0.
  - **Rulings.** (1) The claims stay `[I]`. The one `[C]`, H1a's `v91` returning 14, is cited as the run's observation,
    and the attribution to the `+0x20` length test (0x00532751 → 0x00532788) is kept `[I]`. The elimination holds: every
    other `mov eax, 0xe` of the legacy chain lies in the item, corpse and mercenary readers, whose returns are swallowed.
    (2) The layout is precise enough for the archivist to build versions 71, 87 and 92 from it, with the three additions
    above. The archivist entry is annotated, and it says that the archivist, not this lane, updates d2s.md § Legacy
    versions, § Versions 92..95 and `tools/d2s.py`. The lane's d2s.md edits are link repoints only. (3) Ruling 3, the
    d-none question: no refusal of 71..91 is found, so hirelings 3, 30, 33, player-creation 1, items-uniques-sets 21
    and save-d2s 126 stay shortfalls and wait for the builder. No row moves class. The 0..70 refusal moves none: no row
    needs a version below 71. (4) The 17 symbols stay I; none was checked by a run.
  - **Backlog:** review request closed. The archivist builder entry stays open, annotated. Ledger: the lane row was
    filled with the orchestrator's usage (425 490 tokens, 131 tools, 36 min) and the fixes. The review row was added
    with usage "—".
- **2026-10-27 — H6e1 (`quest-npc`) filed (reverser, `lane/h6e1`, harness slot 1, from `main` `147e5ca3`; `main`
  `44cfbcb5` merged).** Run id run:2026-10-27-sweep-quest-npc, record in
  [items experiments](../findings/items/experiments.md#run2026-10-27-sweep-quest-npc), evidence in
  [items/0010 § Plan 0038 batch H6e1](../findings/items/0010-quest-drops.md#plan-0038-batch-h6e1-run2026-10-27-sweep-quest-npc).
  - **Built:** logger `tools/gdb/quest-npc.gdb` + `tools/gdb/quest-npc.py` (`QUESTS_GiveItem`, the three service tests
    step by step, the consumed cursor item, the shared tail), session driver `tools/h6e1_sessions.py` (H6e2's loop, a
    `qs` command for `quest_sessions.py act`), `d2pilot.py npc --try` (the refusal cases tried in the service box) and
    a 7-sub-tile margin around the town waypoint for walking clicks, checker `tools/sweep_h6e1.py check|static`, six
    recipes `tools/d2s_recipes/quest-h6e1-*.json` (rows in `tools/test_d2s.py`, 47 tests OK).
  - **Sessions:** 17 launches, 14 kept (three given-item games, two imbues, nine Larzuk/Anya games, one a chain of
    three on the saves the game wrote), 3 development logs. H6e2's habits held: the town waypoint walk and `wpchain`
    returned in seconds; no Act II/III descents were needed. Two new traps, recorded in the run: a walking click near
    Harrogath's waypoint opens its menu (fixed by the margin), and Save and Exit writes 0 into the act bytes of the
    difficulties not played, so a chained game starts in the Rogue Encampment (the driver takes the waypoint first).
  - **Check:** `sweep_h6e1.py check` over the 14 kept logs: 69 service-test calls, 9 sockets, 2 imbues, 18 consumed
    cursor items, 18 tails, 20 given items, 3 Anya draws; **0 mismatches** (`check-final.txt` `66868cc2…`).
  - **Ledger (22): raised 11, raised in part 11, shortfall 0** (inventory § 2.6 H6e1 block). Highlights: every given
    item by NPC and difficulty through the store path, Qual-Kehk's count on all three bit states, Anya's table and
    draw; the imbue's clvl 5 / 6 bound and the ethereal flag; every Larzuk branch but quality 9 and the bound-1 draw;
    the three tests' refusals in code order. Corrections: `tr2` and `g34` are created at quality 7 (base `unique`).
    Refinements: the throwable test is skipped for every tested item (unit `+0xC8` bit 25); an imbued item is
    repaired when created identified. Malah's potion was not given (her talk table offers it in quest state 4 only).
    No class move; totals unchanged: static 567, harness 519, c-emu 0, blocked 421, deferred 2, raised 17: 1 526.
  - **S2c piece (qd 38):** met, 18 consumed items, each the player's cursor item; qd 38 stays counted as S2c.
  - **Symbols (rule 14), I → C:** `QUESTS_GiveItem`, `A1Q4`/`A3Q3`/`A3Q4`/`A5Q2`/`A5Q3_NpcMessage`, the three
    service tests, `CursorItemConsume`, `ItemRepairAll`, `ItemIdentifyAttach`, `ITEMS_GetType`, `ITEMS_GetCode`,
    `ITEMS_GetQuality`; new `sub_0062A270_ItemHoldsItem`, `sub_0062A2B0_ItemCompactSave` (C) and
    `sub_00578610_PlayerCursorItemIs` (I).
  - **Backlog:** review request
    [2026-10-27-reverser-architect-review-lane-h6e1-plan-0038-batch-h6e1](../backlog/archive/2026-10-27-reverser-architect-review-lane-h6e1-plan-0038-batch-h6e1.md)
    filed; spec-writer entry
    [2026-10-27-reverser-spec-writer-h6e1-quest-npc-raises-and-the-given-item](../backlog/archive/2026-10-27-reverser-spec-writer-h6e1-quest-npc-raises-and-the-given-item.md)
    filed, held until the review. Slot 1 stopped, saves restored (empty, no aside).
  - **Next:** the `lane/h6e1` review; items/quest-drops is then ready for its Phase 3 re-tag.
- **2026-10-27 — `lane/h6e1` review (architect): H6e1 (`quest-npc`) accept with fixes (7).** `main` merged into the
  lane twice: `1573a48f` first, then `92b811df` (`lane/rlg`). Both times the plan log and ledger conflicts kept both
  sides, and `backlog.py archive` had nothing to move. `tools/d2pilot.py` auto-merged. `lane/rdp`'s `--descend-to` and
  `--all-copies` are kept, and so are this lane's `npc --try` and the town-waypoint margin (`wp_avoid`, set in `cmd_npc`
  only, so `clickable` is unchanged for every other command). The merged file is `3ba03df5…`. The kept sessions ran
  `3d6d4f20…`, and no claim depends on the difference. Static review: no Ghidra, no harness.
  - **Checked.** The three manifests pass `sha256sum -c` from `workspace/logs/h6e1/` (30, 85 and 12 lines): 14 kept logs
    and 3 development launches, plus dev4's pilot output with no game. `sweep_h6e1.py check` (`8e9e74c3…`) was rerun
    after each merge under `systemd-run --user --scope -p MemoryMax=4G` over the 14 kept logs. Both outputs are
    byte-identical to `check-final.txt` (`66868cc2…`, 0 mismatches). After the merges, `tools/test_d2pilot_descend.py`
    gives 10 tests OK and `tools/test_d2s.py` 55 OK, with the six H6e1 `RECIPE_BASES` rows rebuilt. From the logs: 69
    `CAN` calls (imbue 20 + 2, personalize 13 + 7, socket 18 + 9), every one with `+0xC8` = `0x02000000` client side and
    `0x06000000` server side. objdump on the pinned `game.exe`: `ItemCanImbue` 0x0062C590–0x0062C692 (bit 25 at
    0x0062C5FF–0x0062C60B skips the 0x0062C60E call; quest byte, `leg `, `0x0062A270`, `0x800`, qualities 4–9 in that
    order); the client box test 0x004BFD1F–0x004BFD9B (154 / 0x1FF / 0x200 to the three tests); `CursorItemConsume`'s
    `INV_GetCursorItem` compare 0x0055EEB8–0x0055EEC0; `QUESTS_GiveItem`'s ilvl-0 → clvl at 0x005466D6–0x005466E2,
    `ITEMS_CreateForStore` (kind 4, noEthereal 1) at 0x005466FB, durability 0x0054670B–0x0054671A; the pre-switch
    override 0x005574E3–0x00557567 (`ItemBaseIsUnique` at 0x0055753E → 7); Malah's talk table 0x00589B90–0x00589BD4
    (state `+0x0C` = 4, no `ice`, `+0xD8` = 0, message 3); `ItemRepairAll` 0x005761C0–0x005762A3 and its gate
    `sub_0062E660_ItemCanRepair` 0x0062E660–0x0062E693. The 22 rows re-summed from the inventory (`items-quest-drops.md`,
    13 rows: 3 + 3 + 3 + 1 + 1 + 1 + 2 + 1 + 1 + 3 + 1 + 1 + 1). The given-items save chain checked on the saves the game
    wrote: after each game only the difficulty just played keeps its act byte (`[132,0,0]`, `[0,132,0]`, `[0,0,132]`).
  - **Fixes.** (1) overclaim: the imbue-repair `[C]` rested on this run's imbued `cap`, which separates nothing: it is
    unidentified **and** ethereal (`0x00482000`), at 7 of 7. The bullet is re-anchored. The leg (61 → 66) is the
    identified case, and run:2026-10-19-economy2's unidentified, non-ethereal `cap` (10 of 12 kept) is the other. The
    gate `ItemCanRepair` (0x005761CB) and its ethereal refusal are added as `[I]`, with an open question. Carried into
    § 6's note, the Answer summary, the ledger row qd 44 and the spec-writer entry. (2) under-claim (rule 14):
    `ITEMS_CheckFlags` and `sub_00628110_ItemGetFlags` stayed I. Their logged returns separate (0x0062C653,
    0x0062C81E, 0x0062C72F: 0 and the flag; 0x0062C739: the flag word, `0x1800010` refused), the same basis as the
    lane's `ITEMS_GetQuality`. Both are raised. `ITEMS_GetSockets` returns 0 every time and stays I. (3) under-claim:
    qd 38 stayed "S2c, raised in part" although H6e1's `CIC`/`CICR` line meets its remainder. It is now S2c, raised
    (the `lane/s38s` precedent); items/0010's S2c entry, its tally and the inventory are updated. (4) omission (rule
    14): `ITEMS_GetType`, `ITEMS_GetCode` and `ITEMS_GetQuality` were raised in `re/symbols.csv` but left I in
    items/0001, 0003 and 0006, and had no row in items/0010's Functions table. Rows were added (with `CheckFlags`,
    `ItemGetFlags`, and `ItemCanRepair` I), and the owner tables now say C. (5) miscount: the request said 14 symbol
    raises for the 15 the lane made. The review's total is 17 I → C and 3 new. (6) omission: `tkf` ×2 passed
    `ItemCanImbue` but was missing from its "accepted" cell. (7) stale cross-reference: items/0011 Phase 2b said
    "never: the imbued item is built unidentified". It now carries a note giving the leg as the counter-case. items/0010's
    `ItemMagicStockable` row said I where `re/symbols.csv` says C (items/0009).
  - **Rulings.** (a) **"Shortfall 0" is honest.** Each of the 11 rows raised in part has a `[C]` half that the kept
    check compares on separating cases. Their remainders are states that single-player stock play does not reach
    (game type ≠ 3 for Anya's clvl halves; gold, ears, flag `0x1000`, quality 9; sockets already present with flag `0x800` clear), or
    paths this run did not reach. Malah's `ice` (qd 32, 46) needs her quest object in state 4. qd 45 L686 needs the
    Ancients and Nihlathak. qd 50's scripted half belongs to other runs. Those halves stay `[I]` in Phase 3. Nothing is
    routed: no batch is left in the family, and the state-4 question stays in items/0010's open questions. (b) **The
    quality-7 correction stands** as `[C]`. `xyz` separates `unique` from `quest`: it is a `ques` item with quest 19 and
    `unique` 0, and it kept quality 2, while `tr2` (quest 32) and `g34` (quest 19), both `unique` 1, came back 7 (`ICQ`
    rq 2). (c) **The throwable refinement stands**, scoped to the 22 logged imbue tests (no 0x0062C613 step, `tkf` ×2
    accepted). What sets bit 25 is an open question; "a throwable is refused" stays `[I]`. (d) **The act-byte trap**
    is a harness note, not a save claim: the game writes the act byte of the difficulty it played and 0 for the others.
    The recipes' three active bytes are ADR-0003 tool inputs that no checked code reads. (e) **The symbols:** 17 I → C
    (15 by the lane, plus two by this review) and 3 new (2 C, `PlayerCursorItemIs` I). Each raise is backed by a
    logged return the checker compares on separating cases. `ItemTypeThrowable`, `ItemCanRepair`, `ITEMS_GetSockets`
    and `INV_GetCursorItem` stay I.
  - **Totals** recounted against `main` `92b811df` after the merges: unchanged, static 567, harness 519, c-emu 0,
    blocked 421, deferred 2, raised 17: 1 526 (qd 38's move has no class change). H6e1's ledger: raised 11, raised in
    part 11, shortfall 0: 22. S2c's quest-drops tally: raised 13, raised in part 2, reclassified 1.
  - **Readiness.** **items/quest-drops is ready for its Phase 3 re-tag**: S2c, H6d, H6e2 and H6e1 are all accepted, and
    no other batch holds one of its rows. Research-map row updated. Spec-writer entry
    [2026-10-27-reverser-spec-writer-h6e1-quest-npc-raises-and-the-given-item](../backlog/archive/2026-10-27-reverser-spec-writer-h6e1-quest-npc-raises-and-the-given-item.md)
    released, and the review request closed. The inventory § 5 marks H6e1 done.
- **2026-10-27 — `lane/a72` (archivist, no slot, no Ghidra, no harness, from `main` `92b811df`): the d2s legacy
  builder.** Work of the reverser's [builder entry](../backlog/archive/2026-10-27-reverser-archivist-d2s-legacy-layouts-for-a-builder.md),
  from [save/0001 § Plan 0038 lane/rlg](../findings/save/0001-d2s-io.md#plan-0038-lanerlg-the-legacy-and-version-92-readers-static-2026-10-27)
  with the review's three additions (0..70 refused with 1, the header skills applied after the skills section, the
  72..88 base adjustment with 74..79 unadjusted).
  - **Built** (`tools/d2s.py`, opt-in only): `save_version` 92 (the version-96 file with items in the 1.09 widths and
    adds, no generic param, the ≤ 92 per-id encodings of stats 83, 107, 126, 188, 195/198/201, a set item's `Sets`
    id), 87 (the legacy layout: `0x82`-byte header, the quest/waypoint/NPC bytes, `gf` with the 3-byte mask, `if`,
    items in the 92 form with the ≤ 89 widths, an empty corpse list, the `0x12`-byte mercenary and its list, the
    hotkey tail) and 71 (version-71 records by classic index or code, the `JM`/seed/name mercenary, no tail); the keys
    `legacy_new_char`, item `v71` and item `item_props`; `parse_legacy` and the extended parser's 92 read them back.
    Refused where the finding reads a step but gives no writer layout: magic, rare, crafted and class-affix items at
    87; stats 23, 24, 93, 96, 99, 102, 105 at 87; stat 204, the remapped and folded ids at ≤ 92.
  - **Proof of byte identity:** the 259 `RECIPE_BASES` recipes rebuilt into the scratchpad before and after give the
    same sha256 (the five new `leg*` recipes added on top). `tools/test_d2s.py`: 60 tests OK (`LegacyTest` 5 new;
    `ExtendedTest`'s refusals of 92 and 87 moved to 91 and 70; `RecipeTest` reads legacy builds with `parse_legacy`).
  - **Documented** ([d2s.md](../formats/d2s.md)): § Legacy versions (71..91) from the finding, § Versions 92..95 (the
    complete version-test list, the ≤ 92 rows, the version-92 property encodings, the ⌈`0x029`/8⌉ mask), the version
    row, the ear's realm bit on reading, § Legacy builder (with the builder's own choices listed as such) and Open
    questions. All layout statements `[I]`; one data `[C]` (the 1.09 columns: 57 of the 247 saved records differ).
  - **Recipes staged, not run:** `leg87merc` (hirelings 3, 33), `leg87new` (player-creation 1), `leg71merc`
    (hirelings 30, 33), `leg71uniq` (items-uniques-sets 21), `leg92props` (save-d2s 126); `RECIPE_BASES` base
    `smpsor-l50.d2s`, no pinned hash. The rows stay shortfalls until a harness load.
  - **Backlog:** builder entry closed; the H1a archivist entry annotated (all five parts done); review request
    [2026-10-27-archivist-architect-review-lane-a72-d2s-legacy-builder](../backlog/archive/2026-10-27-archivist-architect-review-lane-a72-d2s-legacy-builder.md).
    Ledger row added, usage "—".
  - **Next:** the `lane/a72` review; then a harness lane for the `leg*` recipes.
- **2026-10-27 — `lane/a72` review (architect): accept with fixes (6).** `main` (`dcf6c210`, H6e1) merged into the
  lane first (the log and metrics conflicts kept both sides; `tools/test_d2s.py` auto-merged; `backlog.py archive`
  moved nothing). **Default path:** the 265 non-`leg` recipes of `RECIPE_BASES` (the 259 and H6e1's six) built in the
  scratchpad by `main`'s `tools/d2s.py` and the lane's give the same 265 sha256, and `dump` of 27 of them (every tenth)
  prints the same text under both tools. `tools/test_d2s.py`: 60 tests OK, before and after the fixes. The five `leg*`
  recipes build and `parse_legacy` / the extended parser read each to its last byte; `dump` refuses them, as the usage
  says (the commands read as before). Every layout statement of d2s.md § Legacy versions, § Versions 92..95 and
  § Legacy builder was compared with save/0001 § Plan 0038 lane/rlg and its review fixes: all `[I]` as the finding's,
  none stronger; the three review additions are there (0..70 refused with 1 after the length test, 9 on the host
  path; the header's left and right skills applied after the skills section, non-zero only; the 72..88 base
  adjustment). The `[C]` data count recounts over `itemstatcost.txt` (359 rows): 247 with a `Save Bits`, 57 of them
  with a different 1.09 width or add (blank as 0), 5 of those 57 with no 1.09 width (`item_pierce_cold/fire/ltng/pois`,
  `questitemdifficulty`); the three examples hold. No game data is dumped (offsets, counts and three illustrative
  `ItemStatCost` values only).
  - **Fixes:** (1) omission: the base-adjustment row left out "89 and above: none" (the finding's default case).
    (2) omission: the version-92 encodings table left out stat 326 = 1 after the 57 group and ids 0, 2 "set as is (no
    `ValShift`, no param)". (3) omission: the version-71 list left out that a corpse's list places modes 0, 1, 6 only
    (13 otherwise), that a failed top-level item is skipped with its socketed records then read as top-level items,
    and that a failed socketed item or any corpse failure ends the list. (4) other: the `[C]` count read as 57 + 5;
    the 5 are among the 57. (5) overclaim: three builder choices were written as layout, not listed as choices: the
    version-71 mode taken from the current `location`, the `if` section's 30 bytes as the count of
    `0x00646140(class)` (the finding gives the function, not its value), and stat 134's ≤ 89 field as 16 bits of 0;
    now in the choices bullet and Open questions. (6) omission: `leg71uniq` could not separate what items-uniques-sets
    21 needs: The Gnasher and Civerb's Ward are both row 0, the builder's default file index, and every record's unit
    and item seeds were equal. The recipe now adds Deathspade (unique row 1) and Civerb's Icon (set row 1), and gives
    Civerb's Ward distinct seeds (`v71` `unit_seed` 1234567, `item_seed` 7654321); it builds (835 bytes, 6 items) and
    reads back.
  - **Rulings.** (1) Accept with the fixes applied in the review commit. (2) **The builder choices are marked as
    choices** (§ Legacy builder's "not from the findings" bullet and Open questions), and no `[I]` layout statement
    rests on one. They stay choices after any load: a load that accepts a file shows only that the reader did not
    refuse those bytes, not what the game writes there. (3) **What a session must observe** for a `leg*` load to raise
    anything despite the choices: (a) the reader path and its return, logged (the legacy reader's return, or
    `D2S_ReadSaveV92`'s for 92, and `NewCharLegacy` for `leg87new`), since a legacy file has no checksum; (b) for the
    sections 7–10, which fail silently, the game's version-96 write-back compared field by field with the build:
    every built item with its code, quality, unique or set row, seeds and position; the mercenary's seed, name,
    hireling Id and converted experience; hotkey slots 8–15 and the swap skills. "The character loaded" raises nothing
    past the skills section, and a missing item means the read stopped there. (c) A statement is raised only by a
    separating value: one the write-back puts in the slot the finding names, which another reading would have put
    elsewhere or dropped (distinct swap A and B, distinct left and right skills, distinct unit and item seeds, a
    non-zero unique or set row). A value set by a builder choice raises the finding's statement about that field only
    if it separates in this way, and never the choice itself as a format fact. (d) Bytes the server does not read
    (legacy header `+0x1E`, `+0x24`, `+0x26`/`+0x36`, `+0x59`..`+0x7D`, the mercenary record's `+0x01`, hotkey bytes
    2–5, the corpse's 12 bytes) raise nothing. (e) A refusal or a short read refutes the finding only once the choices
    touching that section are ruled out by a second build that varies them. (4) The H1a archivist entry's five parts are
    done ((1), (2), (3), (5) at `lane/a71`, (4) and version 92 here): closed. The six rows stay H1a shortfalls (b), no
    class move, totals unchanged. (5) **Route:** a new harness batch **H1c** (`d2s-legacy`, reverser-harness, run id
    `sweep-d2s-legacy`, H1a's `d2s-io.gdb` logger) loads the five recipes under ruling 3. It has its own row in
    [inventory § 5](0038-inventory/README.md#harness-batches) and is in the H1 family (H1a and H1b are done), so it may
    pair with a batch of any other family.
  - **Backlog:** review request closed; the H1a archivist entry
    [2026-10-27-reverser-archivist-h1a-d2s-legacy-layouts-and-parser-gaps](../backlog/archive/2026-10-27-reverser-archivist-h1a-d2s-legacy-layouts-and-parser-gaps.md)
    closed. Ledger: the lane row was filled with the orchestrator's usage (255 234 tokens, 82 tools, 22 min) and the
    fixes. The review row was added with usage "—".
- **2026-10-27 — `lane/h6e2f` (reverser, harness slot 1, no Ghidra): the H6e2 follow-up** (the `lane/rdp` review's
  ruling 7). `eye4c`, `tome4c` and `brain4c` run as staged in `tools/h6e2_sessions.py`, 3 launches, 3 kept, under
  run:2026-10-27-sweep-quest-items (addendum *Follow-up* in items/experiments). First, additively, `tools/gdb/pilot.py`'s
  RL line gains `f28` (room `+0x28`; rdp ruling 5).
  - **Outcomes:** `eye4c` reached the Spider Cavern (85) with `--descend-to 85` and opened the eye chest (`qey`, gold 5
    first); `tome4c` reached the Ruined Temple (94) and the tome made `bbb`; `brain4c`'s `explore --all-copies`
    activated both level-91 copies, the brain chest was listed at (10014, 11879) and opened (`qbr`, gold 7 first).
    Check over the 14 kept logs: chest 8, object 3, event7 19, dup 8, gate 8, gold 57, death 6; 0 mismatches.
  - **Ledger** ([items/0010 § H6e2](../findings/items/0010-quest-drops.md#plan-0038-batch-h6e2-run2026-10-27-sweep-quest-items)):
    the Khalim order `[C]` for all three chests (qd 33 and objects 48 chests: only `vip` and the held-part refusal
    stay); `qey`, `qbr` met; `bbb` shortfall → raised in part; three more `j34` kills; H6e2 now raised 3, in part 15,
    shortfall 6. Brain chest: listed and opened once its room is active `[C]`; which copy the listing follows `[I]`
    (`brain4c` names the copies by `0x40000` but had the room active in both). Three symbols I → C. `bkd`, `hdm` not
    routed (shortfall). Inventory § 2.6 follow-up paragraph; totals unchanged (1 526) against `main` `1573a48f`.
  - **Backlog:** the spec-writer H6e2 entry annotated; review requested
    ([entry](../backlog/archive/2026-10-27-reverser-architect-h6e2f-review.md)). Ledger row added, usage "—".
- **2026-10-27 — `lane/h6e2f` review (architect): accept with fixes (2).** `main` (`dcf6c210`) merged into the lane
  first (plan log, metrics and items experiments conflicts kept both sides; `backlog.py archive` moved nothing). All
  seven `workspace/logs/h6e2/` manifests pass `sha256sum -c` there (`manifest-followup.sha256`: 18 lines, the three
  logs, their pilot outputs, four outputs, 8 screenshots). Under `systemd-run --user --scope -p MemoryMax=4G`,
  `sweep_h6e2.py check` over the 14 kept logs is byte-identical to `check-followup.txt` (`fe0f034f…`; chest 8, object 3,
  event7 19, dup 8, gate 8, gold 57, death 6, 0 mismatches), and `h6e2f_copies.py`, its `--warps 76 51` mode and
  `rdp_brain91.py` reproduce `copies-followup.txt`, `warps-eye4c.txt` and `brain91-4c.txt` byte for byte.
  `test_d2pilot_descend.py`: 10 tests OK.
  - **objdump** (pinned `game.exe` `631066c1…`): the eye chest calls `QUESTS_GetSeed` at 0x005B8958 (return 0x005B895D),
    computes `k = 5 + low32(lo·0x6AC690C5 + hi) mod 5` (0x005B895F–0x005B8987) and loops `DropItemCodeAt('gld ', 2)`
    at 0x005B899C (return 0x005B89A1) `k` times, then `QUESTS_FindById(16)`, the `GameForEachUnit` callback 0x005B8770,
    `DropItemAtUnit` at 0x005B89F1 (return 0x005B89F6) and `ObjectChestDrop` at 0x005B8A11 (return 0x005B8A16). The
    brain chest is the same at +0xE0 (0x005B8A38, 0x005B8A7C, 0x005B8AD1, 0x005B8AF1; returns as filed). The tome calls
    no `QUESTS_GetSeed`; its `DropItemAtUnit` is at 0x005B7AF3 (return 0x005B7AF8), after the word test via
    `QUESTRECORD_GetState` (0x005B7AB2). The returns match the logged `QGS`/`QDC`/`QDI`/`OCD` returns.
  - **Rulings.** (1) The Khalim order `[C]` for the eye and brain chests stands: the checker models `k` from the logged
    `QGS` seed, and three seeds give three different `k` (5, 7, 8; recomputed here), which a wrong count or order could
    not match by chance (rule 10). The held-part refusals (no session held a part or `qf2`) and the tome's word-17
    refusal and used-tome half stay `[I]`; `bbb`'s quality 7 is After `[I]`. (2) `qey`, `qbr` met; `bbb` shortfall →
    raised in part; H6e2 raised 3, in part 15, shortfall 6: 24; no class move. (3) The three symbols I → C stand
    (rule 14: each one's logged returns compared with the checker's model). (4) **Fix 1 (overclaim):** the brain
    chest's `[C]` was "listed and opened once its room is active"; in `brain4` the chest's room activated in the fully
    activated copy (line 7337) and the chest was never listed, so the `[C]` is scoped to "with its room active in both
    copies" (items/0010 bullet, its sub-bullet, the open question, inventory § 2.6). (5) "Which copy the listing
    follows" stays `[I]`: an order match (the `0x40000` copy activates first in `brain4c`; the fully activated copy
    activates first in `brain4`/`brain4b`), not a flag read in a log that separates the copies. **Fix 2 (tool not
    kept):** the first-`RRESEED` lines it cites were in no kept output; `tools/h6e2f_copies.py --first` (`566a0531…`,
    default output unchanged) writes them, with each copy's first RL line, to `copies-review.txt` (`33c41b9c…`,
    `manifest-review.sha256` `6b4d3ac4…`). They match the finding (0-based lines, now said); the build order (the
    listing copy built first in `brain4`/`brain4b`, the copy without `0x40000` built first in `brain4c`) is added to
    the `[I]` as a second order. (6) The RL `f28` key breaks
    no reader: `d2pilot.LogState`, `rdp_brain91.py` and `h6e2f_copies.py` read RL keys by name, and the pilot's RL is
    renamed `PRL` wherever `drlg-gen.py`'s RL (which already carries `f28`) shares a log. (7) The `eye4c` descent was
    correct, not lucky: `descend_cells` drops a warp whose known destination is not the target and keeps only unknown
    ones; the row-51 warp at (5235, 4591) had destination 84 from its first WRP line, and the development `eye4` log of
    the same seed took that very warp (WRP room rect (1040, 912) + (35, 31)) and arrived in 84 (PLR line 2276), so the
    skip was right. The first try timed out because no unknown-destination warp was logged within 240 s; the recipe's
    `until` step explored and retried, and the second try's warp at (5055, 4071) resolved to 85 and arrived there
    (line 11527). (8) Totals against `main` `dcf6c210`: unchanged, 1 526.
  - **Readiness.** items/quest-drops' Phase 3 can start (S2c, H6d, H6e2 with this follow-up, H6e1 all accepted).
    **objects needs a small follow-up re-tag** of § L: the Khalim chests' row (`[C]` for all three chests, the held-part
    refusal `[I]`) and the item-objects row (`bbb` joins `leg` and `bks` as `[C]`, its quality 7 `[I]`; `hdm` stays
    `[I]`). The brain chest's listing is not stated in the objects spec. The spec-writer H6e2 entry is annotated.
    Request closed ([archive](../backlog/archive/2026-10-27-reverser-architect-h6e2f-review.md)); ledger rows filled.
- **2026-10-27 — Phase 3, the items/quest-drops cluster and the objects § L follow-up (spec-writer, `lane/s38q`,
  from `main` `fd841611`).** Batches S2c, H6d, H6e2 (with `lane/h6e2f`) and H6e1, and H4a's qd 48, all accepted; each
  restated statement checked against its section of
  [items/0010](../findings/items/0010-quest-drops.md) (§ Plan 0038 batch S2c, H4a, H6d, H6e2, H6e1) and the reviews'
  rulings.
  - **items/quest-drops** {C 86, I 86, L 2} → **{C 159, I 76, L 2}** (recounted with the gate's tag reader).
    Raised: S2c qd 7, 9, 14, 19, 20, 28, 31, 37, 38, 41, 47, 49 and qd 8's map and its correction (objects 28 and 30
    store 16 and 29), qd 21's monster and object sources; H6d qd 18, 22, 27 and the `[C]` halves of 11 (the hireling
    and the Hydra, B7, the death event's owner), 13 (the records reached, Baal's order) and 16 (Baal); H4a qd 48;
    H6e2 qd 1 (event 7 for 268 and 367), the quest-item rows' creations, E1 for `box`, `tr1`, `msf`, a new E1b for the
    three Khalim chests (gold first), qd 34's two difficulty cases, qd 35's pickup cases; H6e1's 11 raised rows and the
    `[C]` halves of its 11 in part (the given items, the service tests' refusals in code order and the throwable skip,
    Larzuk's branches, the imbue's `ilvl > 5` bound and ethereal flag, the shared tail, the imbue repair when
    identified). The quality column is the asked quality (seven bases come back 7). Kept `[I]` as the ledgers rule:
    the `exp`-state branch, Diablo, the Nightmare forge, the H6e2 shortfalls and refusal halves, Malah's `ice`, the
    server refusal lines (the client refuses first), the d-2c, d-0032 and d-none rows.
  - **objects § L:** the Khalim chests' row `[C]` for all three chests (heart 8, eye 5, brain 7 piles first), the
    held-part refusal `[I]`; the item-objects row adds `bbb` to `[C]` (word 17 clear, one item, no draw), its 7 as the
    override, the word-17 refusal and `hdm` `[I]`. Counts unchanged {C 189, I 62, L 4}.
  - **items/economy F7:** the imbue's repair qualified (the identified leg repaired, the unidentified `cap` not), as
    the H6e1 entry asked; counts unchanged.
  - **Wiki:** [items-other-paths](../wiki/items-other-paths.md) quest section refreshed, `based_on` quest-drops
    2026-10-27; [objects](../wiki/objects.md) and [economy](../wiki/economy.md) text refreshed (dates unchanged).
  - **Backlog:** closed the [H6d](../backlog/archive/2026-10-17-reverser-spec-writer-plan-0038-h6d-for-the-phase.md),
    [H4a](../backlog/archive/2026-10-25-reverser-spec-writer-h4a-monsters-a-raises-and-the-spawn-48.md),
    [H6e1](../backlog/archive/2026-10-27-reverser-spec-writer-h6e1-quest-npc-raises-and-the-given-item.md) and
    [H6e2](../backlog/archive/2026-10-27-reverser-spec-writer-h6e2-quest-items-raises-and-the-khalim-chest.md) entries;
    annotated the [S2c entry](../backlog/2026-10-16-reverser-spec-writer-plan-0038-s2c-corrections-for-phase.md) ((b),
    (c) done; (a), (d)–(g) wait for cube, vendors, sockets-runewords); filed the
    [counts entry](../backlog/archive/2026-10-27-spec-writer-architect-s38q-quest-drops-counts-for-the-research-map.md) and the
    [review request](../backlog/archive/2026-10-27-spec-writer-architect-s38q-review-quest-drops-phase-3.md). Ledger row
    added, usage "—".
  - **Next:** architect review of `lane/s38q`.
- **2026-10-27 — `lane/s38q` review (architect): Phase 3 of items/quest-drops and the objects § L follow-up, accept
  with fixes (7).** `main` (`fd841611`) was already the lane's base: the merge was empty and `backlog.py archive` moved
  nothing. Static review: objdump on the pinned `game.exe`, no Ghidra, no harness.
  - **Checked.** The diff restates 73 net `[C]` (+78, −5) and −10 `[I]` (+51, −61); the front matter matched the
    gate's reader. Traced to the accepted ledgers within their reviews' scopes, more than a third of the new `[C]`:
    S2c qd 7, 8 (both A1 bullets), 9, 14, 19, 20, 21, 28, 37, 38, 41, 47, 49; H6d qd 11 (the hireling and the Hydra, the
    death event's owner), 13 (the records reached), 16 (Baal), 18, 22, 27; H4a qd 48 (five of 25 classes; the finding's
    "five more" is four more plus Andariel, as the spec says); H6e2 qd 1, 30 (every `[C]` cell of § E's table against
    the finding's ledger), 33 (E1 and E1b), 34, 35; H6e1 qd 2, 4, 5, 32, 39, 40, 42–46, 50, 51. objdump: Baal's
    word-40 test and flag at 0x0058DF9A–0x0058DFA6 and `QUESTS_GetSeed` → `RNG_RandLoHi` at 0x0058E052/0x0058E05C; the
    imbue's single quest test `GetState(rec, 3, 1)` at 0x00579FA3–0x00579FB1; the `boss` branch 0x00573E23–0x00573E40
    (expansion word, `d` > 0, the class's flag byte); the tail's `ItemRepairAll` then `ItemIdentifyAttach` at
    0x0057A0F9/0x0057A103 and `ItemCanRepair` first in `ItemRepairAll` (0x005761CB) with its `0x10` and `0x400000`
    tests (0x0062E679–0x0062E691); the heart chest's mode call then `QUESTS_GetSeed` first (0x005B8867, 0x005B8878),
    E1b's order. Every `fn:` spot-checked resolves in `re/symbols.csv`.
  - **Fixes.** (1) overclaim: D1's `[C]` said "every difficulty and game type" for the four states H6d ran; scoped to
    them (the H6d ruling). (2) overclaim: the duplicates `[C]` carried `ItemInitStats`' stat-356 write, which no run
    reads back (the held Normal staff came from the tool-built `QuestMsfN`); the sentence moved to the `[I]` bullet.
    (3)–(5) overclaim (rule 2): pseudocode lines no run reached under raised headers got inline `[I]`: B6a's `else
    none` (every logged non-player killer was a monster), D6's `d > 0` and the one-pile split, F1's personal-name
    line (F1's header now scoped "but the refusal and the personal name", with the H6e1 anchor for the `ilvl > 5`
    bound and the ethereal flag). (6) overclaim: wiki/items-other-paths put Alkor's `xyz` (Normal) and Meshif's `g34`
    (Nightmare) under "confirmed in all three difficulties"; scoped. (7) stale cross-reference: the struck pile
    question still said "Baal's gold itself stays unrun". items/quest-drops is now **{C 159, I 80, L 2}**.
  - **Rulings.** (1) **The operate slots stand `[C]`.** Slots 33, 12, 28, 39–41 and 57–59 are on H6e2's compared `QOW`
    lines, inside `[C]` finding bullets the `lane/h6e2` and `lane/h6e2f` reviews accepted, and the sentence is part of
    inventory row 1's original statement (`QUESTS_ObjectOperate` dispatches by class). It is reflected with row 1,
    which stays raised in part (the other classes); the altar, Malus and orifice slots stay `[I]`. No inventory move.
    (2) **§ E's `g34`/`xyz` row is a legitimate cross-batch raise, and the inventory now reflects it.** H6e1's checker
    compares both gifts (`QGV` → `CF0` → `QGC`, 0 mismatches) in the logged word-20 states; a met piece with a compared
    line moves at the review that finds it (the `lane/s38s` and `lane/h6e1` precedents). Inventory § 2.6: qd 30's
    `g34`/`xyz` line H6e2 shortfall → **raised in part** (counted H6e2, no class change); H6e2's ledger is **raised 3,
    raised in part 16, shortfall 5: 24**; items/0010's H6e2 ledger row annotated. (3) **The brain-chest scope holds.**
    No spec or wiki states the chest's listing or which copy it follows; objects § L and quest-drops E1b state the
    operate order only, which `brain4c` met with the room active in both copies. (4) The quality-7 split (point 3),
    S2c (c) as H6d corrected it (point 4), qd 20 (point 5), D7's split (point 6) and economy F7 (point 7) stand as
    filed. The Reimplementation notes' two new `[C]` restate E1/E1b and § E's `[C]` at the same scope; not inflation.
  - **Research map.** The items/quest-drops row rewritten whole (C 159 / I 80 / L 2, Phase 3 done); the objects row's
    stale "Khalim heart chest (eye and brain `[I]`)" rewritten for the three chests and `bbb`.
  - **Totals** (recomputed once, against `main` `fd841611`): unchanged, **static 567, harness 519, c-emu awaiting a
    batch 0, blocked 421** (d-none 295, d-edit 73, d-sim 28, d-2c 7, d-owner 10, d-0032 8), **deferred 2, raised 17:
    1 526.**
  - **Bookkeeping.** Review-fixes Seen lines: spec-writer 2 and 7, architect 8. The review request and the counts
    entry closed. Ledger: the lane row filled (usage from the orchestrator: 315 288 tokens, 93 tools, 23 min; accept
    with fixes, 7: overclaim 6, stale cross-reference 1); the review row added, usage "—".
- **2026-10-27 — H6b (`sockets`) filed (reverser, `lane/h6b`, harness slot 1, from `main` `dcf6c210`; `main`
  `fd841611` merged).** Run id run:2026-10-27-sweep-sockets, record in
  [items experiments](../findings/items/experiments.md#run2026-10-27-sweep-sockets), evidence in
  [items/0007 § Plan 0038 batch H6b](../findings/items/0007-sockets-runewords.md#plan-0038-batch-h6b-run2026-10-27-sweep-sockets).
  - **Built:** logger `tools/gdb/h6b.gdb` + `tools/gdb/h6b.py` (the child's x/y, the cursor at the `p5` test, the
    stat-list link branch, both replenish timers, the reader's runeword store, `ItemCopy`, the client test step by
    step), session driver `tools/h6b_sessions.py` (H6e1's loop; `write` lays out the recipes and plans with
    `socket_sessions.py`), checker `tools/sweep_h6b.py logs|static`, the already-applied branch of `RUNEWORD_Apply` in
    `tools/sockets.py` (the old run still reproduces), a `"forced_sockets"` test-state key in `tools/d2s.py`, four
    recipes `tools/d2s_recipes/sock-h6b-*.json` (rows in `tools/test_d2s.py`, 60 tests OK after the merge).
  - **Sessions:** 10 launches, 5 kept (the game-written *Steel* sample loaded; a level-1 Barbarian making runewords
    in two games; the client refusals and an identify; Malah's trade and Anya's personalize in Harrogath), 5
    development (the same five, the logger before its `UIS` lines). The Act V game started in Harrogath (act bytes
    132), so no waypoint was needed; nothing was saved.
  - **Checks:** `sockets.py check` 35 inserts and 37 client verdicts reproduced, 0 failed (`check-sockets.txt`
    `815bdd9b…`); `sweep_h6b.py logs` 773 counted checks, 0 bad (`check-sweep_h6b.txt` `64d81481…`); regression on
    run:2026-10-15-sockets 351 and 357, 0 failed.
  - **Ledger (25): raised 9, raised in part 9, shortfall 7** (inventory § 2.6 H6b block). Fewer than half raised: the
    UI states 10/11 need a player trade; func 24 and the ranged `par`-0 func 17 lines are on `server` rows only; the
    link's enable-bit branch and a broken filler do not occur on the socket path; the golem reader, the other reader
    sites and 0x00563441 need a golem, a corpse or version-71 save, or a trade. A correction: the cursor slot is
    already empty at the `p5` test (the place routine removes the child first). New: the copier passes the copy itself
    as the insert's player and inserts into a parent in mode 4; the timers also run at every item load and creation;
    the client copy of a runeword made by an insert holds the Name index while the server's field stays 0.
  - **S2c pieces:** sockets 14 (the client flags before and after identifying) and 46 (the reader's store, the client
    copy) met; both rows stay counted as S2c.
  - **Symbols (rule 14), I → C:** `sub_00558530_ItemReplenishDurTimer`, `sub_00629900_ItemBaseHasInv`.
  - No class move filed (proposals for the review in the § 2.6 block); totals unchanged: static 567, harness 519,
    c-emu 0, blocked 421, deferred 2, raised 17: 1 526.
  - **Next:** the `lane/h6b` review.
- **2026-10-27 — `lane/h6b` review (architect): accept with fixes (6).** First, `main` was merged into the lane: it
  was already up to date at `fd841611`, and `backlog.py archive` was a no-op. The review re-checked the run with no
  harness and no Ghidra:
  - `manifest-run.sha256`, `manifest-shots.sha256` and `dev/manifest-dev.sha256` pass from their own directories.
  - The four procedure commands were rerun under `systemd-run --user --scope -p MemoryMax=4G`. Each output is
    byte-identical to the kept one: `check-sockets.txt` `815bdd9b…` (35 inserts, 37 client verdicts, 0 failed),
    `check-sweep_h6b.txt` `64d81481…` (773 checks, 0 bad), `check-static.txt` `589f34e3…` and the regression
    `7c94a139…` (351 and 357).
  - `main`'s `sockets.py` gives the same regression output. On this run's logs it fails at one insert only, the
    *Steel* re-insert.
  - `tools/d2s.py`: the 270 existing recipes build byte-identically with `main`'s tool and the lane's, and
    `"forced_sockets"` is read only when it is given (one recipe uses it). `test_d2s.py` gives 60 OK.
  - objdump confirms the anchors: the copier's pushes 0, 1, 0, 0 and `EDX` = `edi` at 0x0055A3F9–0x0055A41C; the corpse
    reader's `push 1` at 0x0053397D; `NPC_SellItem`'s skip at 0x00579736; the `p5` test at 0x005627CB–0x005627DE;
    `InvPlaceSocketed`'s remove at 0x0063B26E, and `0x0063AAF0` clearing `inv+0x20` (0x0063AB61); the 252 timer's
    `idiv` at 0x00558561; `RUNEWORD_Apply`'s `push 0x40; push 0xAB` at 0x006600BC, and the callee
    `0x00625790` → `0x00625650`; the link branches of `0x00627910`.

  **Rulings.**
  1. **sock 10's `"forced_sockets"` is a tool-built save on stock tables (ADR-0013 § Neutral).** It is neither a
     forced-path run (no table is edited) nor a stock path (no game-written save has bit 11 on a ring or on gloves).
     It backs `[C]` for the code that reads the built state: the client test's order, and its refusal at `hasinv` and
     at `ItemMaxSockets` on a target with bit 11. The two raises stand on that scope, and Phase 3 states that no stock
     item reaches either refusal. It raises nothing about how an item gets bit 11. The `lane/h3b` `use`-byte ruling
     does not bind here: that byte was an edited table, and this is a save. The broken cap (sock 12) is a state stock
     play reaches.
  2. **The `sockets.py` "already applied" branch is modelling, not fitting.** The branch is the code's own test
     (0x006600BC–0x006600CB, read `[I]` since plan 0029). Only the case it describes takes it: `main`'s tool fails
     only the *Steel* re-insert, and the old run gives byte-identical output under both tools. And it asserts six
     equalities; it skips none. One part was a misread (fix 1): the model tested the pushed `0x40`, which the callee
     does not read.
  3. **The sock 17 L237 correction stands, re-scoped.** `[C]`: the slot was empty at the test in the 29 inserts with
     `p5` 1. `[I]`: why it is empty (`0x0063AAF0`). The statement stays a shortfall, not d-none: an insert whose child
     is not the player's cursor item with `p5` 1 is not ruled out (the copier's "player" is the copy).
  4. **"Fewer than half raised" is honest** (9 of 25), and every reason holds except one. sock 1's version-71 sites
     have had a builder route since `lane/a72` (fix 5), so that piece goes to H1c, not to a class. After the moves,
     3 shortfalls remain.
  5. **Class moves** (inventory § 2.6): sock 9 → d-2c (`[I]`: the immediate stores sit in the trade routine; two
     table-copied stores are unfollowed); sock 29 → d-none, on the socket path only; sock 38 L482 and L507 → d-none.
     sock 18's 253 half and sock 38 L481's ranged half are labelled d-none for Phase 3. Their statements stay counted
     here, raised in part (the H2b precedent, tc 58).
  6. **Symbols:** both raises stand under rule 14 (`ItemBaseHasInv` against the table in 39 calls; the 252 timer's
     logged schedule against its formula). `sub_00558580_ItemReplenishQtyTimer` stays I: its two schedules outside an
     insert are not compared by the checker.
  7. **S2c rows:** sock 46 → raised (both remainder parts compared); sock 14 stays raised in part.

  **Fixes:**
  1. *Misread:* the already-applied test does not read `0x40`. `tools/sockets.py` is now `af5c8279`, and both
     outputs are unchanged. items/0007 § 5 and sock 35 carry the note.
  2. *Stale cross-reference:* "ADR-0010 § built states" becomes ADR-0013 § Neutral, in items/0007 sock 10 and the run
     record.
  3. *Miscount:* the UI word has seven register stores, not six, and five resolve to constants (sock 9).
  4. *Omission:* the two 253-timer schedules outside an insert. The truncation is the read `idiv` (sock 18, and the
     Functions table).
  5. *Omission:* sock 1's version-71 route. The piece goes on H1c's § 5 row.
  6. *Overclaim:* sock 17 L237's reason sat inside the `[C]`.

  **Bookkeeping:**
  - H6b's ledger: raised 9, raised in part 9, shortfall 3, reclassified 4: 25.
  - Totals, recounted against `main` `fd841611`: **static 567, harness 515, c-emu 0, blocked 425** (d-none 298,
    d-2c 8), **deferred 2, raised 17: 1 526.**
  - § 5 marks H6b done, and the research-map row says the spec is ready.
  - **Phase 3 ready: items/sockets-runewords** (S2c, H2b and H6b, all accepted).
  - No H6b spec-writer entry existed, so the review filed one:
    [2026-10-27-architect-spec-writer-h6b-sockets-raises-for-the-phase-3-re](../backlog/archive/2026-10-27-architect-spec-writer-h6b-sockets-raises-for-the-phase-3-re.md).
  - The S2c harness-pieces entry stays open for H6a and H6c.
  - Review request closed; the lane's ledger row is filled.
- **2026-10-27 — Phase 3, the items/sockets-runewords cluster (spec-writer, `lane/s38k`, from `main` `ad8b8cd0`).**
  Batches S2c, H2b and H6b, all accepted; each restated statement checked against its section of
  [items/0007](../findings/items/0007-sockets-runewords.md) (§ Plan 0038 batch S2c, H2b, H6b) and the reviews'
  rulings.
  - **items/sockets-runewords** {C 80, I 83, L 7} → **{C 128, I 84, L 7}** (recounted with the gate's tag reader).
    Raised: S2c sock 2 (the drop roll, cube and Larzuk callers), 3, 4 (`itype1..3`), 5, 6 (the shared index), 8, 19,
    20, 25 (with the 422 correction), 26 (Pul, Ith, Sol, Ohm), 27, 28 ×2, 32, 34, 36 L472, 41, 43 (no quality switch),
    44, 45, 46, 47 (the count and the re-insert); H2b sock 42 (F1's cap steps and order) and sock 44's piece; H6b sock
    1 (the copier, its own unit as the player), 10 ×2 (built states, with the no-stock note `[I]`), 12 L173, 13 in
    part, 14's piece (two cases), 16 ×2, 17 L291 (`p4`, `p6`, `p7`) and L237's empty slot, 18 (the 252 timer, and the
    timers outside the insert, scoped to the run), 21, 35 ×2 (the test by state alone; the `0x40` an `[I]` note),
    38 L481 (*Leaf*), L490, L505 in part. Kept `[I]` as the ledgers rule: sock 1 L284 and the golem and other reader
    sites, sock 9 (d-2c), 12 L174, 17's clear and its reason, 18's 253 half, 29 (d-none), 38's ranged half, L482 and
    L507, and the S2c and H2b remainders. Pseudocode lines no run reached got inline `[I]` (B1, B2, B5–B6, C1, D1,
    D3, E1, E4, F1, F2). Open questions: the child-level question struck; the `p5` question added.
  - **items/properties F6** (rule 8): the no-clamp half for qualities 2 and 3 `[C]` (H2b sock 44); {C 152, I 22,
    L 3} → {C 153, I 22, L 3}.
  - **Wiki:** [items-other-paths](../wiki/items-other-paths.md) socketing section refreshed, `based_on`
    sockets-runewords 2026-10-27; [items](../wiki/items.md) `based_on` properties 2026-10-27 (no text change).
  - **Backlog:** closed the [H6b entry](../backlog/archive/2026-10-27-architect-spec-writer-h6b-sockets-raises-for-the-phase-3-re.md)
    and the [H2b entry](../backlog/archive/2026-10-20-reverser-spec-writer-h2b-items-chain-spec-updates.md) ((r)–(s),
    its last open items); annotated the [S2c entry](../backlog/2026-10-16-reverser-spec-writer-plan-0038-s2c-corrections-for-phase.md)
    ((e), (g) done; (a), (d), (f) wait for cube and vendors); filed the
    [counts entry](../backlog/archive/2026-10-27-spec-writer-architect-s38k-sockets-runewords-counts-for-the-research-map.md) and the
    [review request](../backlog/archive/2026-10-27-spec-writer-architect-s38k-review-sockets-runewords-phase-3.md). Ledger row
    added, usage "—".
  - **Next:** architect review of `lane/s38k`.
- **2026-10-27 — `lane/s38k` review (architect): Phase 3 of items/sockets-runewords and items/properties F6, accept
  with fixes (8).** `main` (`ad8b8cd0`) was already the lane's base: the merge was empty and `backlog.py archive` moved
  nothing. Static review: objdump on the pinned `game.exe`, no Ghidra, no harness.
  - **Checked.** The diff restates +48 net `[C]` (+56, −8) and +1 `[I]`; the front matter matched the gate's reader.
    Traced to the accepted ledgers within their reviews' scopes, more than a third of the new `[C]`: S2c sock 2 (the
    creation callers, the forced count kept `[I]`), 3, 4, 5, 6, 8, 19, 20, 25 (422), 26, 27, 28 ×2, 32, 34, 36 L472,
    41, 43, 45, 47; H2b sock 42 (F1's header scoped "but the marked lines", the write clamp `[I]` as the `lane/h2b`
    review ruled) and sock 44's piece; H6b sock 1 (copier rows and bullets only; golem, version-71, corpse and
    0x00563441 `[I]`), 10 ×2 (the built-state scope and the no-stock note `[I]`, ruling 1 of the H6b review), 12 L173,
    14's piece, 16 ×2, 17 L291 and L237 (the empty slot `[C]`, the clear and its reason `[I]`, the H6b split), 18, 21,
    35 ×2 (E1's test by state alone `[C]`, the `0x40` an `[I]` note), 38 L481 (*Leaf* only), L490, 46. The d-none
    halves (sock 29's toggle and `0x100` child, sock 38's ranged func 17, L482, L507, the 253 schedule at an insert) and
    sock 9 (d-2c) stay `[I]` with their reasons. Inline `[I]` sits on every unreached pseudocode line of B1, B2, B5–B6,
    C1, D1, D3, E1, E2, E4 and F1–F2. objdump: `sub_00625790_UnitFindStatList` passes only the list and the state to
    `0x00625650` when the state is non-zero (0x006257AC–0x006257B5), so L438's `0x40` correction holds; the timers'
    13 direct call sites; `NPC_SellItem`'s `VENDOR_IsPermanent` branch (0x0057972F–0x00579736) over the copy call
    0x00579747 (`push 1`, the same form as Anya's 0x0057A52E). Every `fn:` spot-checked resolves in `re/symbols.csv`.
    Restatement inflation: the new *Entry points* bullets restate their table rows with the evidence, the pattern the
    section already used for the packet and reader rows; not inflation.
  - **Fixes.** (1) overclaim: the Malah-sale `[I]` said "a sale is not a copier case"; `NPC_SellItem` copies with the
    second word 1 when `VENDOR_IsPermanent` is false, so the bullet is scoped to the logged sale. (2) misread: A1's
    UI-state bullet said the two immediates are the only stores of 10 and 11; two register stores copy the slot table
    at 0x007BC9E4 (unfollowed, the H6b review); the bullet also had no tag of its own (its `[I]` was in backticks) and
    now carries `[I]`. (3) overclaim: "on these items the client copy got the socketed flag only once identified" for
    two items, one of them never identified; scoped to the skull cap, on the spec and on wiki/items-other-paths.
    (4) overclaim: "no game-written save has bit 11 on a ring or on gloves" (no save survey behind it) replaced by the
    creation-path reason. (5) under-claim (rule 8): B5's 253 timer call was `[I]` though sock 18's ledger raises the
    call ("the 252 then the 253 timer"); B5's line `[C]`, E4b split (the read `[C]`, `v` = 0 at all four; the schedule
    `[I]`). (6) overclaim (rule 7): the Reimplementation notes kept "no runeword can form" in a classic game and "clamp
    by quality only at creation" inside `[C]` bullets after D1's and F1's splits; each split, the second half `[I]`.
    (7) omission: wiki/items-other-paths' handler-branch sentence left out the branches no stock runeword line uses
    (funcs 8 and 11). (8) miscount: A1's built-state note counted a backticked `` `[C]` `` as a tag; reworded.
    items/sockets-runewords is now **{C 129, I 85, L 7}**; items/properties **{C 153, I 22, L 3}**.
  - **Rulings.** (1) **F6 stands.** H2b's sock 44 piece is a compared `[C]` (the cap after the quality switch equal to
    `min(p, 6)` in all 34 calls, 21 above 3); a constant raised in one spec is raised in every spec that states it
    (spec-writer rule 8), and "only qualities 2 and 3 reach it from here" stays `[I]`. (2) **E4's timers outside the
    insert stand `[C]`, scoped to the run's 300 entries.** The `RPE` lines are logged entries, not a model's
    prediction, and objdump gives the second source: 11 of the 13 direct calls of the two timers lie outside the insert
    (the bullet now lists them). "Every item load and creation" is not claimed; the two outside 253 schedules stay
    `[I]` (not compared, the H6b fix 4). (3) **The code-read splits stand as filed** (sock 6's `+0x084`, sock 4's
    `itype4..6`/`etype`, the group ≥ 3 fatal line, sock 34's classic-legal sentence, sock 36's mode-6 sentence, sock
    46's `0xFFFF`, sock 47's `hasinv`, sock 20's update queue, sock 21's ethereal and version test, sock 26's Zod):
    each `[I]` part is the remainder its ledger names. (4) **The Malah-sale bullet may stay without an inventory row.**
    It is a new `[I]` statement carried from the H6b ledger (sock 1), not a re-tag; it adds one `[I]` and moves no
    inventory class. Scoped by fix (1). (5) The open-question changes stand: the child-level question is answered by
    B1's `[C]`; the `p5` `[L]` is the finding's H6b question.
  - **Research map.** The items/sockets-runewords row rewritten whole (C 129 / I 85 / L 7, Phase 3 done); the
    items/properties row rewritten (C 153, updated 2026-10-27, F6).
  - **Totals** (recomputed once, against `main` `ad8b8cd0`): unchanged, **static 567, harness 515, c-emu 0, blocked
    425** (d-none 298, d-2c 8), **deferred 2, raised 17: 1 526.**
  - **Bookkeeping.** Review-fixes Seen lines: spec-writer 2, 3, 7 and 8; architect 2. The review request and the counts
    entry closed. Ledger: the lane row filled (usage from the orchestrator: 244 114 tokens, 83 tools, 20 min; accept
    with fixes, 8: overclaim 4, misread 1, under-claim 1, omission 1, miscount 1); the review row added, usage "—".
- **2026-10-27 — H6a (`cube`) filed (reverser, `lane/h6a`, harness slot 1, from `main` `fd841611`).** Run id
  run:2026-10-27-sweep-cube, record in [items experiments](../findings/items/experiments.md#run2026-10-27-sweep-cube),
  evidence in [items/0008 § Plan 0038 batch H6a](../findings/items/0008-cube.md#plan-0038-batch-h6a-run2026-10-27-sweep-cube).
  - **Built:** logger revision r4 of `tools/gdb/cube.py` (the packet-to-transmute chain, `UnitSetEvent`, the runeword
    strip, the two quest hooks, the crafted builder's null-record read, the children's list owners), session driver
    `tools/h6a_sessions.py` (`cube_sessions.py`'s layouts, a step's rune inserts, the Act IV act byte, the crash
    session's own game directory), checker `tools/sweep_h6a.py check|static|tables`, `tools/cube.py` extended (`uns`,
    `rep` broken and stackable, `qty=`, the copy's children, placement bit 0), eight recipes
    `tools/d2s_recipes/cube-h6a-*.json` (rows in `tools/test_d2s.py`, 60 tests OK).
  - **Sessions:** 8 launches, all kept, no development log; Normal, expansion and classic, in town. The tooling
    lessons applied: the Act IV start by act byte 131 (`-a4` recipes); no walking, so the Harrogath margin,
    `--descend-to` and `--all-copies` were not needed; no Save and Exit, so the act-byte zeroing did not arise. The
    faulting session ran in a symlink game copy inside slot 1's prefix; its crash folder is in `workspace/logs/h6a/dev/`.
  - **Check:** `sweep_h6a.py check` over the 8 logs: 26 transmutes reproduced, 27 call chains, 23 `UnitSetEvent`
    calls, **0 mismatches** (`check-final.txt` `15e54b63…`); regressions: `tools/cube.py check` on run:2026-10-15-cube
    182 reproduced, 0 failed; `sweep_s2c.py cube` byte-identical.
  - **Ledger (29): raised 22, raised in part 4, reclassified 2 (cube 16, 44 → d-none), shortfall 1 (cube 51)**
    (inventory § 2.6 H6a block). Totals against `main` `fd841611`: static 567, harness 517, c-emu 0, blocked 423,
    deferred 2, raised 17: 1 526.
  - **S2c pieces:** cube 49 case (b) met (the game faults at 0x005C2460), case (a) d-none; aff 14's level-window half
    met. Both stay counted as S2c, raised in part.
  - **Symbols (rule 14), I → C:** `g_SrvPacketTable`, `SrvPacketDispatch`, `Pkt4FButton`, `PktInteractButton`,
    `PlayerGetInteract`, `CubeButton`, `ItemRemoveRuneword`, `ItemRepairBroken`, `QuestStaffMade`,
    `QuestKhalimWillMade`; new `sub_0055F590_ItemInvNonEmpty` (I).
  - **Backlog:** review request
    [2026-10-27-reverser-architect-review-lane-h6a-plan-0038-batch-h6a](../backlog/archive/2026-10-27-reverser-architect-review-lane-h6a-plan-0038-batch-h6a.md)
    filed; spec-writer entry
    [2026-10-27-reverser-spec-writer-h6a-cube-raises-for-the-phase-3-re](../backlog/archive/2026-10-27-reverser-spec-writer-h6a-cube-raises-for-the-phase-3-re.md)
    held until the review; the S2c-pieces entry annotated (H6a parts done). Slot 1 stopped, saves restored (empty, no
    aside).
- **2026-10-27 — `lane/h6a` review (architect): accept with fixes (7).** Static review after merging `main`
  `ad8b8cd0` (`lane/h6b`, `lane/s38q`; bookkeeping conflicts kept both sides; `backlog.py archive` moved nothing). The
  three manifests pass `sha256sum -c`; under `systemd-run --user --scope -p MemoryMax=4G`, `sweep_h6a.py check`,
  `static` and `tables` reproduce `check-final.txt`, `static.txt` and `tables.txt` byte for byte, `tools/cube.py check`
  on run:2026-10-15-cube reproduces `regress-cube-run.txt` (182, 0 failed), `sweep_s2c.py cube` is byte-identical,
  `test_d2s.py` 60 OK. Anchors objdumped (no Ghidra): the dispatcher's `call eax` at 0x0054D818 (return 0x0054D81A),
  `UnitSetEvent(…, 4)` at 0x00566439, the faulting `mov eax, [eax+0x5C]` at 0x005C2460 after `MAGICAFFIX_GetRecord`,
  InvPlaceItem's `ItemInvNonEmpty` → `ITEMS_SetFlag(item, 1, 1)` at 0x00560385–0x00560393, the cow tests (word 26 at
  0x00594199, word 40 at 0x005941BE, `cmp eax, 1` on the level at 0x005941DD), the `rep` block 0x00566289–0x0056630C,
  ItemCopy's child loop and CubeModApply's `MakeEthereal` call (0x00660280).

  **Rulings:**
  1. **Built states** (ADR-0013 § Neutral) each back only the code that reads them: `dur` 5 and the broken sword
     (`0x100`, 72 = 0) the `rep` branches; the wand's stat-204 entry the refill; the knives' quantity the stackable
     `rep`/`qty=` steps; the ethereal *Gull*'s flag the copy's `ItemInitStats` and the mod line's `MakeEthereal` (not a
     game-made ethereal item's other stats, e.g. its durability); the socketed *Greyform* and the gemmed swords the
     copy's child loop, `uns` and the placement bit; the magic and rare builder items the input tests; the clvl-1
     character with ilvl-1 inputs the crafted builder at output ilvl 1 (cube 49 (b) is the code path, not a claim on
     how a game reaches that ilvl); the quest bits and act byte 131 the cow and quest tests. *Steel* was formed by the
     game's insert, not built. No raise rests on how a game reaches a built state.
  2. **The crash session.** It ran in `workspace/wineprefix-1/drive_c/h6a-game`, a directory of symlinks to the shared
     game files plus its own `BnetLog.txt`; its crash folder is in `dev/` (`manifest-dev.sha256` passes). The shared
     game directory is untouched: `game.exe`, the three DLLs and `d2.lng` re-hash to `docs/inventory.md`'s values
     (`game.exe` `631066c1…`), and the 11 MPQs it links re-hash to their recorded values (`docs/formats/`). Its own
     `BlizzardError` folder holds two reports from 10:17 and 10:20, before H6a's first session (14:37): not this lane's.
  3. **The d-none moves** stand, re-counted from the tables with `python3 -I` at review: cube 16, 0 of 389 inputs
     with `eth` (4 with `noe`); cube 44, no output with `rem` (`uns` row 141 only); cube 49 (a), 0 of 40 194 crafted
     cases (203 row-base pairs × 99 × 2), with a looser filter that can only add empty sides. The prefix groups
     (101 and up) and the suffix groups (1 and up) are disjoint, so a first pick is never emptied by the other side.
  4. **Refinements.** The ethereal upgrade stands `[C]`: `IIS1` logs the plain `9dg` values (6–18) between the copy's
     `ItemInitStats` and the mod line, `CMODX` the ×3/2 (9–27); `MakeEthereal` sits inside `CubeModApply` (0x00660280),
     which the loop calls once per line, so "after each line" follows. `ItemCopy`'s two extra steps are `[C]` for one
     child; "per child" is `[I]` (fix 5). The runeword copy's 20639 is `0x509F`, H6b's *Steel* value; the path is
     `[I]` with the reader's anchor (fix 7). `InvPlaceItem` bit 0 is raised to `[C]` (fix 6).
  5. **Raises.** 18 of the 22 have a separating case: every chain return address, event 4 / 20 / none, `xmg` and `umg`
     against a plain class test, `9dg` → `7dg` against the ubercode, *Steel* against the gemmed sword, `IIS1` against
     `CMODX`, the damaged and broken paths, `qty=` with the `sock` flag clear against run:2026-10-15-cube's `sock=1`,
     the two hooks against 18 other outputs, level 103 against level 1, classic word 26 against word 40. Four do not
     (fixes 1–4). cube 15 stays raised: its `[I]` was "for a higher tier" alone.
  6. **Symbols:** the 10 raises stand under rule 14 (logged returns, flags and quest words compared with the model).
     `sub_0055F590_ItemInvNonEmpty` stays I (its return is not logged); `ITEMS_SetFlag` and `sub_00553380_UnitSetEvent`
     stay I.

  **Fixes** (each written into items/0008 § Plan 0038 batch H6a, the run record and the spec-writer entry):
  1. *Overclaim:* cube 39 L491 → raised in part: which stat 73 the repair reads (evaluated, `STATS_GetUnitStat` at
     0x005662F1, or base) is not separated (24 both), nor the 255 side of the stackable `min`.
  2. *Overclaim:* cube 39 L524 → raised in part: one charge entry cannot separate "every stat-204 entry"; stock items
     with 2–4 exist.
  3. *Overclaim:* cube 40 L528 → raised in part: max stack 160 < 255; a 200-stack throwing weapon with *Dense* reaches
     the 255 side on stock data.
  4. *Overclaim:* cube 58 L968 → raised in part: "only" is aff 14's unseparated half (d-none part, checked: the 8
     stock forced ids pass every other C4 test).
  5. *Overclaim:* "two more steps per child" from one child: `[C]` for one, per child `[I]` from the loop at
     0x0055A3A0–0x0055A468.
  6. *Under-claim:* `InvPlaceItem` bit 0 `[C]`: the two row-141 copies, socketed with no child, kept `0x880810`.
  7. *Omission:* the runeword copy's name id without the serialiser path (0x0062D1EA, items/0007 H6b).

  **Bookkeeping:**
  - H6a's ledger: **raised 18, raised in part 8, reclassified 2, shortfall 1: 29.**
  - Totals, recounted against `main` `ad8b8cd0`: **static 567, harness 513, c-emu 0, blocked 427** (d-none 300,
    d-2c 8), **deferred 2, raised 17: 1 526.**
  - § 5 marks H6a done; the research-map row says the spec is ready.
  - **Phase 3 ready: items/cube** (S2c and H6a, both accepted).
  - The spec-writer entry is released, corrected:
    [2026-10-27-reverser-spec-writer-h6a-cube-raises-for-the-phase-3-re](../backlog/archive/2026-10-27-reverser-spec-writer-h6a-cube-raises-for-the-phase-3-re.md).
  - The S2c harness-pieces entry stays open for H6c.
  - Review request closed; the lane's ledger row is filled.
- **2026-10-27 — Phase 3, the items/cube cluster (spec-writer, `lane/s38c`, from `main` `7995eefc`).** Batches S2c
  and H6a, both accepted; each restated statement checked against its section of
  [items/0008](../findings/items/0008-cube.md) (§ Plan 0038 batch S2c, H6a) and the `lane/h6a` review's rulings and
  fixes.
  - **items/cube** {C 119, I 82, L 4} → **{C 167, I 87, L 3}** (recounted with the gate's tag reader; diff +59 / −11
    `[C]`, +50 / −45 `[I]`, +2 / −3 `[L]`). Raised from S2c: cube 6, 8, 10, 12, 13, 21, 22, 29, 47 (case 8; the
    fallback `[I]`), 49 (the survey), 52, 55 (L776 corrected: the spot search draws nothing, the portal object draws;
    L829 in part), 56. From H6a, each naming run:2026-10-27-sweep-cube: cube 1 (L48; L54's `0x18` half), 7 ×3, 15, 17
    (`exc`; `eli` split to f″ `[I]`), 25 (L331; L349's classic half `[I]`), 32 (in part), 36, 38 ×2, 39 (L495; L491,
    L524 in part, fixes 1–2), 40 (L496, L971; L528 in part, fix 3), 43 ×3, 53 ×2, 54 (the classic word-26 test moved
    into L1 in the code's order, the old L3 removed), 58 (in part, fix 4). Refinements: K4 (a copied child's two
    game-seed steps, `[C]` for one, `[I]` per child, fix 5) with § M; K3's name id `0x509F` (`[C]`; the path `[I]`,
    fix 7); G4's flags bit 0 `[C]` (fix 6); E3 and F2's ethereal upgrade (plain values, then `MakeEthereal` ×3/2,
    `[C]`, ruling 4). S2c piece cube 49 (b) `[C]` at 0x005C2460, (a) `[I]`. Kept `[I]` with their no-stock reasons
    (ruling 3): cube 16, 20, 24, 44, 49 (a), 51 (shortfall). Pseudocode lines no run reached got inline `[I]` (A3c–A3e,
    B3, B4, C2, E3–E5, F1, F3–F5, H4, I1, J2–J3, K4). Open questions: the ethereal upgrade struck; the cow portal
    narrowed to the portal object's draws; the not-reached list rewritten.
  - **items/affixes C4i** (rule 8): the forced row's level-window skip `[C]` (H6a cube 58, S2c aff 14's piece),
    "only" `[I]`; the open question narrowed; {C 152, I 28, L 4} → {C 153, I 28, L 4}.
  - **Wiki:** [items-other-paths](../wiki/items-other-paths.md) cube section refreshed, `based_on` cube 2026-10-27;
    [items](../wiki/items.md) `based_on` affixes 2026-10-27 (one open-question line).
  - **Backlog:** closed the [H6a entry](../backlog/archive/2026-10-27-reverser-spec-writer-h6a-cube-raises-for-the-phase-3-re.md);
    annotated the [S2c entry](../backlog/2026-10-16-reverser-spec-writer-plan-0038-s2c-corrections-for-phase.md)
    ((a), (f) done; (d) waits for vendors, H6c); filed the
    [counts entry](../backlog/archive/2026-10-27-spec-writer-architect-s38c-cube-counts-for-the-research-map.md) and the
    [review request](../backlog/archive/2026-10-27-spec-writer-architect-s38c-review-cube-phase-3.md). Ledger row added, usage "—".
  - **Next:** architect review of `lane/s38c`.
- **2026-10-27 — `lane/s38c` review (architect): Phase 3 of items/cube and items/affixes C4i, accept with fixes (4).**
  `main` (`7995eefc`) was already the lane's base: the merge was empty and `backlog.py archive` moved nothing. Static
  review: objdump on the pinned `game.exe`, no Ghidra, no harness.
  - **Checked.** The diff restates +48 net `[C]` (+59, −11) on items/cube and +1 on items/affixes; the front matter
    matched the gate's reader. Traced to the accepted ledgers within their reviews' scopes, more than a third of the
    new `[C]`: S2c cube 6 (the `COW_LEVEL` row), 8 (the chained callees), 10 and 12 (A4's line, row and note), 13 (A3a),
    21 (B3's split), 22 (B5's bindings), 29 (`+0x28`/`+0x2A`), 47 (case 8; the fallback `[I]`), 49 (the survey), 52
    (K3's round trip), 55 (L2, M and the oracles bullet: 0 steps at the spot search, 171 / 173 / 171 at the portal
    object), 56 (L3); H6a cube 1 (the entry row and packet bullet; `0x17` and type ≠ 4 a separate `[I]`), 7 (the
    constants row, G3, the L refusal), 15 (a′), 17 (f′, `eli` split to f″ `[I]`), 25 (C2 `eli`; the classic gate `[I]`),
    32 (E3–E4 with `uns`; `rem` `[I]`), 36 (F1, K3's `0x509F`; the path `[I]`), 38 (E3, F2), 39 and 40 (F3–F5 with the
    stat-73 reading, entries past the first, the `qty` side and the 255 side inline `[I]`, fixes 1–3 of the H6a review),
    43 (G4's two hooks; the other writes an `[I]` note), 53 (L1a), 54 (L1), 58 (the window half; "only" `[I]` in both
    specs), and the refinements (K4 and § M `[C]` for one child, `[I]` per child; G4's bit 0; I4 (b) at 0x005C2460).
    The d-none moves (cube 16, 44, 49 (a)) stay `[I]` with their no-stock reasons, and cube 20, 24 and 51 likewise.
    objdump: `CUBE_CowPortalOpen` 0x00594140–0x00594260 tests `Game+0x70` at 0x00594181, then in a classic game word 26
    (call 0x00594199, result 0x0059419E; set skips to 0x005941CB, clear refuses at 0x005941A5), in an expansion game
    word 40 (0x005941BE) and never word 26, so the reordered L1 holds; level 39 and class 60 pushed before 0x00594228;
    the found flag at 0x0059420F and the portal result at 0x0059422F both refuse; `UnitSetEvent` 20 at 0x00594253.
    Also `ItemInvNonEmpty` → `ITEMS_SetFlag(it, 1, 1)` at 0x00560385–0x00560393, the event-4 call 0x00566439, the
    faulting `mov eax, [eax+0x5C]` at 0x005C2460, `MakeEthereal` inside `CubeModApply` at 0x00660280, ItemCopy's own
    `ItemCreateFromSave` at 0x0055A31C, the `STATS_GetUnitStat(73)` / `GetUnitBaseStat(72)` pair at
    0x005662F1/0x005662FD, the quest-byte test at `+0x12A` then `hst` and `qf2` at 0x005664A8–0x005664D4. Every `fn:`
    spot-checked (15) resolves in `re/symbols.csv`. Inline `[I]` sits on the unreached lines of A3, B3–B4, C2, E3–E5,
    F1, F3–F5, G5, H4, I1, I4, J2–J3 and K4 (but L2's refusal, fix 1). Restatement inflation: the new A4, G3, L1–L2
    and Reimplementation notes restate their raised rows and lines at the same scope (the `lane/s38k` and `lane/s38q`
    precedent); not inflation.
  - **Fixes.** (1) overclaim (rule 2): L2's "if either fails: refuse" sat under the portal line's raised `[C]` with no
    failure logged; inline `[I]` (0x0059420F, 0x0059422F). (2) wrong anchor: the Reimplementation note naming rows 72,
    83, 84 and 90 as able to fault cited only the row-83 fault; S2c cube 49's survey added, the fault scoped to row 83.
    (3) wrong anchor: L1's "an expansion game word 40" cited only the H6a classic sessions; 0x005941BE and
    run:2026-10-15-cube added. (4) overclaim: wiki/items-other-paths put the crafted pick of 0 "at output ilvl 5 or
    below" for all three bases; scoped (staff 1, boots up to 5, gloves up to 3) and the low-level condition stated as
    the character's and the input's. items/cube is now **{C 167, I 88, L 3}**; items/affixes **{C 153, I 28, L 4}**.
  - **Rulings.** (1) **The H6a rulings are carried as filed.** Built states are named once in *Evidence* as backing the
    code that reads them; the I4 survey's "only a low-level character" is the output-ilvl formula's condition, not a
    claim on how a game reaches the built clvl-1 case. The d-none moves (16, 44, 49 (a)) stay `[I]`; the four in-part
    overclaims (39 L491, L524, 40 L528, 58) keep their remainders inline `[I]`; ItemCopy's child steps are `[C]` for one
    child and `[I]` per child (K4, § M, the Reimplementation note); `InvPlaceItem` bit 0 `[C]`; the ethereal upgrade
    `[C]` and its open question struck; 49 (b)'s fault `[C]` on the code path, with the crash report as the second
    source. (2) **§ L's reorder stands**: the classic word-26 test belongs inside L1 at the code's position, and the old
    L3 had no address of its own. (3) **§ M's `useitem` row may say `[C]` for one child**: the child steps sit inside
    `ItemCopy`, and the E3–E4 children statement covers both call sites as the H6a ledger raised it (cube 32). (4) The
    open-question changes stand: the ethereal question answered by E3/F2, the cow question narrowed to the portal
    object's draws, the not-reached list split by stock reachability.
  - **Research map.** The items/cube row rewritten whole (C 167 / I 88 / L 3, Phase 3 done); the items/affixes row's
    counts and date moved, C4i's raise named.
  - **Bookkeeping.** Review-fixes Seen lines: spec-writer 2 and 9. The review request and the counts entry closed; the
    S2c entry stays open for (d) (vendors, H6c). Ledger: the lane row filled (usage from the orchestrator: 235 263
    tokens, 78 tools, 23 min; accept with fixes, 4: overclaim 2, wrong anchor 2); the review row added, usage "—".
- **2026-10-27 — H6c (`vendors`) filed (reverser, `lane/h6c`, harness slot 1, from `main` `ad8b8cd0`; `main`
  `a105ae13` merged at `e21e840a`; the entry named `ffa5b957`, corrected at the review).** Run id run:2026-10-27-sweep-vendors, record in
  [items experiments](../findings/items/experiments.md#run2026-10-27-sweep-vendors), evidence in
  [items/0009 § Plan 0038 batch H6c](../findings/items/0009-vendors.md#plan-0038-batch-h6c-run2026-10-27-sweep-vendors).
  - **Built:** logger `tools/gdb/h6c.gdb` (`vendors.gdb`'s files) + `tools/gdb/h6c.py` (the town-leave call site, the
    level-up note, the interaction set and clear, the hireling build's caller, each stock item's tab, placement and
    cell, the inventories at builds, opens and windows, the creation record at IC0, purchases and sales), session driver
    `tools/h6c_sessions.py` (H6b's loop; `BUY:`/`GBUY` tokens resolved from the log for `economy_sessions.py act`),
    checker `tools/sweep_h6c.py logs|pairs|hb|fails|static`, a `tools/vendors.py` branch (an `ITEMS_CreateForStore`
    call outside a build, a gold pile at 0x0055A18D, counted and skipped; run:2026-10-15-vendors unchanged), four
    recipes `tools/d2s_recipes/vend-h6c-*.json` (rows in `tools/test_d2s.py`).
  - **Sessions:** 8 launches, 6 kept (Normal clvl 1 in Act I: gamble windows, sales, purchases, a reopen, the walk out;
    Normal clvl 30 from Act IV: Drognan's reopens around an act change, a level-up and a town entry; Hell clvl 99 in
    Act V: Larzuk, Anya, Malah, Asheara at ilvl 104, gamble windows, a sale and purchases; two Larzuk rebuild loops,
    one ended by a death in the Frigid Highlands; Nightmare clvl 19: six Fara builds at ilvl 24), 2 development logs.
    Lessons: the tab of a store page is page + 1 (the trade window's labels); the Act IV start and H4a's fixed waypoint
    click reach Lut Gholein reliably where the Lut Gholein start did not; an in-act waypoint in Hell without Energy
    Shield killed the character at arrival; a stale rebuild needs a pause of 240 s before the act change.
  - **Check:** `vendors.py check` over the 6 kept logs: 17 stock builds, 40 gamble windows, 1 646 creations through
    the item chain, **0 mismatches**; `sweep_h6c.py logs`: **9 616 counted checks, 0 bad**.
  - **Ledger (13): raised 7, raised in part 2, shortfall 4** (inventory § 2.6 H6c block). Corrections and refinements:
    Asheara's hirelings are built at the interaction start, so the trade-first order is never taken (vend 14);
    `PlayerInteractEnd` runs at a player unit's free and reaches `NpcStorePlayerLeave` only with an interaction open,
    met in run:2026-10-20-two-clients's kept logs (vend 2); the 32-failure test sits only after normal copies and
    permanent items (vend 5, at most 27 failures in 17 builds). Proposed d-2c: vendors 29 and 32. No class move filed;
    totals unchanged: static 567, harness 513, c-emu 0, blocked 427, deferred 2, raised 17: 1 526.
  - **S2c pieces:** vend 22 (tab and cell) met, its cell search `[I]`; vend 26 (`+0x18`, `+0x28`) met, proposed raised.
    The S2c harness-pieces entry is annotated: every piece has run.
  - **Symbols (rule 14), I → C:** `VENDOR_IsPermanent`, `sub_00576F50_StoreItemSold`, `sub_0062E880_ItemStorePage`;
    new `sub_00554120_PlayerSetInteract`, `sub_00554190_PlayerClearInteract` (I).
  - **Backlog:** review request
    [2026-10-27-reverser-architect-review-lane-h6c-plan-0038-batch-h6c](../backlog/archive/2026-10-27-reverser-architect-review-lane-h6c-plan-0038-batch-h6c.md)
    filed. Slot 1 stopped, saves restored (empty, no aside).
  - **Next:** the `lane/h6c` review; items/vendors is then ready for its Phase 3 re-tag (S2c and H6c).
- **2026-10-27 — `lane/h6c` review (architect): accept with fixes (6).** `main` `a105ae13` was already merged into
  the lane (`e21e840a`); the merge was empty. Static review: objdump on the pinned `game.exe` (`631066c1…`), no Ghidra,
  no harness.
  - **Checked.** `manifest-run.sha256` (23 lines), `manifest-shots.sha256` (62) and `dev/manifest-dev.sha256` (25, not
    listing itself) pass; the ten procedure commands, rerun under `systemd-run --user --scope -p MemoryMax=4G`, give
    byte-identical outputs: `vendors.py check` 0 mismatches (17 builds, 40 windows, 1 646 creations), `sweep_h6c.py
    logs` 9 616 checks 0 bad, the run:2026-10-15-vendors regression 0 mismatches. run:2026-10-20-two-clients's
    manifest passes; its host logs hold 7 `PIEND` (return 0x005555CB) and 2 `PLEAVE` (0x00555562): Kashya's (class
    150, `MLV`) and Akara's (148, `BS0`). objdump: `PlayerInteractEnd` 0x00555500–0x00555569 (the `+0x6C` test, the unit
    found by `+0x68`/`+0x64`, type 1 → `NpcStorePlayerLeave` at 0x0055555D, type 2 → 0x00585550); the 32-failure tests
    at 0x00576AA3 and 0x00576BE5 and none in 0x00576B25–0x00576B4D; `NpcInteractStart` → `HIRE_SendList` at 0x00572CFF,
    whose `+0x21` test at 0x005767D5 guards the build 0x005767EB; `NPC_OpenStore`'s 0x00578BD3 test and the class list
    (150, 515, 198, 252) before 0x00578BFF; `NpcInteractRemove`'s 0x00572FAF; `GambleEnsure`'s id scan
    0x00578AFC–0x00578B18; `VENDOR_IsPermanent`'s difficulty clause 0x00576EF0–0x00576F10 (`hp4`, `hp5`, `mp4`, `mp5`);
    `PlayerSetInteract`/`ClearInteract` 0x00554120/0x00554190; `ItemStorePage` 0x0062E880; the gold call 0x0055A188.
    `vendors.py lists`: `hp5` in no permanent list, so the Hell refusal separates the clause. The four `vend-h6c-*`
    recipes have their `RECIPE_BASES` rows and build to the recorded hashes; `test_d2s.py`'s one failure is `main`'s
    134 `anim-*` recipes without rows (the archivist lane's fix, not this one's).
  - **Fixes.** (1) other (tool): `tools/vendors.py`'s new branch skipped every `ITEMS_CreateForStore` call outside a
    build whatever its caller; narrowed to the return 0x0055A18D (`sub_0055A090_DropGoldAmount`), any other caller
    staying a mismatch (`a0ec05e4…`; both checks' outputs unchanged, `workspace/logs/h6c/review/manifest-review.sha256`
    `4ac7f16e…`). (2) misread: "a gold pile dropped when a sale's gold passes the level cap" named a cause for the 4
    piles that the logs do not show (one at the `larz` death's arrival, two after refused sales, one after a copied
    sale); the cause struck, the call site kept. (3) misread: `VendH6cLvl` was "the experience one point short of a
    threshold"; it is clvl 30 one point under clvl 32's threshold and over clvl 31's, so vend 18's level-up is one event
    of two levels (one `LUN`, level 32); written into vend 18 and the run record, with the note queue's read
    (0x00536850–0x005368DF) that the level gained is not read. (4) omission (rule 4): vend 14's "never taken" had no
    read beyond the six runs; the writes of store `+0x21` added (only 0x005770C5, rebuilt at once at 0x005770C9;
    `NPCSTORE_Reset` writes `+0x20` alone, 0x00536D24), `[I]`, in the ledger and the body's correction. (5) stale
    cross-reference (rule 3): the totals were said to be against `main` `ffa5b957`; the lane had merged `a105ae13`
    (the numbers are the same). (6) omission: `PlayerSetInteract`'s row left out that it writes only while `+0x6C` is
    0 (0x00554133). Also vend 5's refinement gained the read that both tests jump to the epilogue 0x00576B74.
  - **Rulings.** (a) **vend 2's raise stands.** Rescanning a reviewed run's kept logs (plan 0044, done), with its
    manifest checked first and the lines its own logger wrote (`PIEND`, `PLEAVE`), is a legitimate source: the class
    of the row was b because no vendor log of a player's free with an interaction open existed in H6c's plan, not
    because only a new run could carry it. The row stays counted as H6c; the raise rests on the two `PLEAVE` and this
    run's `PIEND` without one; the flag test between them stays `[I]`. (b) **vendors 29 and 32 move to d-2c.** With
    one player every close and menu Escape logs `NIR` and `ICLR`, and the skip at 0x00572FAF needs a second entry in
    the NPC's list. A d-edit route (a gamble action sent with the window open) would be a forged client, not stock
    behaviour. (c) **The built states stand as ADR-0013 § Neutral inputs**, backing only the code that reads them;
    the clvl-30 save's state is not one a character reaches by play, and vend 18 says so (fix 3). (d) **The
    `vendors.py` branch is modelling, once narrowed** (fix 1): the skipped call is a different caller of the same
    function, identified by its return address, outside the store model's scope like the `ICB` lines it already
    skips; the regression is unchanged and the 4 calls are counted in `check-vendors.txt`. (e) **The `larz` session is
    kept for its Larzuk build and the in-act leave only**: both precede the death, no ledger line uses a later line,
    and the gold pile its death produced is one of the 4 skipped calls. (f) **vend 14's correction and vend 5's
    refinement stand** as filed, with fix 4 and the epilogue read. (g) The S2c pieces: vendors 26 is raised (it stays
    counted as S2c; the S2c tally in items/0009 now 9 raised, 6 in part); vendors 22 stays raised in part with the
    cell search as its remainder.
  - **Ledger: raised 7, raised in part 2, reclassified 2, shortfall 2** (13). Totals recounted once against `main`
    `a105ae13`: **static 567, harness 511, c-emu awaiting a batch 0, blocked 429** (d-none 300, d-edit 73, d-sim 28,
    d-2c 10, d-owner 10, d-0032 8), **deferred 2, raised 17: 1 526** (inventory § 2.6 H6c block, § 3, § 5).
  - **Phase 3 ready:** items/vendors (S2c and H6c, both accepted). The spec-writer entry
    [2026-10-27-architect-spec-writer-h6c-items-vendors-phase-3-retag](../backlog/2026-10-27-architect-spec-writer-h6c-items-vendors-phase-3-retag.md)
    filed (no H6c entry existed); the research map's items/vendors row says so.
  - **Bookkeeping.** Review-fixes Seen lines: reverser 3, 4 and 9. The review request and the S2c
    harness-pieces entry closed (every piece has run). Ledger: the lane row filled (usage from the orchestrator:
    606 857 tokens, 273 tools, 129 min; accept with fixes, 6: misread 2, omission 2, stale cross-reference 1, other 1);
    the review row added, usage "—".
- **2026-10-27 — H6f (`hirelings`) filed (reverser, `lane/h6f`, harness slot 2, from `main` `ffa5b957`; `main`
  `a105ae13` merged before filing).** Run id run:2026-10-27-sweep-hirelings, record in
  [hirelings experiments](../findings/hirelings/experiments.md#run2026-10-27-sweep-hirelings), evidence in
  [hirelings/0001 § Plan 0038 batch H6f](../findings/hirelings/0001-hirelings.md#plan-0038-batch-h6f-run2026-10-27-sweep-hirelings).
  - **Built:** logger `tools/gdb/h6f.gdb` (`hirelings.gdb`'s four loggers unchanged plus `tools/gdb/h6f.py`: the hire
    gates, refusal tail and `PayGold`, the free mercenary, `MERC_Create`'s table write, the saved mercenary's name clamp
    and dead branch, `PETS_OnDeath`, `MERC_Resurrect`, the kill award, `MERC_CapExpGain`, `MERC_AddExp`, the client's
    name string), session driver `tools/h6f_sessions.py write|plan|run` (15 recipes `tools/d2s_recipes/h6f-*.json`,
    pinned in `tools/test_d2s.py`; the stash and the 1057 seed chosen offline by `plan`), checker
    `tools/sweep_h6f.py check` (runs `tools/hirelings.py check` first). `tools/d2pilot.py`: the `kashyares` menu and the
    `RESX` done alias. `tools/hirelings.py`: a hire counted by `MERC_Init`, not by `HIRE_Hire`'s `EAX` (the function
    returns no value); its output on the 48 logs of run:2026-10-16-hirelings is byte-identical to `main`'s.
  - **Sessions:** 19 launches on slot 2 (cap 20), 15 kept, 4 development (the classic Greiz attempts: from the Act II
    start the pilot found neither Greiz nor the waypoint, and from the waypoint it walked into the sewer twice). Tooling
    lessons applied: `-a4` starts (act byte 131) and per-act starts (128–130), no Save and Exit (so no act-byte
    zeroing), `--descend-to`/`--all-copies` not needed (no descent), the Harrogath margin on the town walks; built
    states named per recipe in the run record (each backs only the code that reads it); no crash-prone probe, so no game
    copy; heavy checks under `MemoryMax=4G`. Slot 2 stopped and its saves directory restored (empty, no aside).
  - **Check:** `sweep_h6f.py check` over the 15 kept logs: **603 comparisons, 0 failing**, `hirelings.py check` 0
    mismatches (16 hires, 13 tables, 6 loads), `monpool.py check` 4 613 of 4 613 (`check/check-final.txt` `943f181f…`).
  - **Ledger (23): raised 12, raised in part 8, shortfall 1, reclassified 2** (inventory § 2.6 H6f block). Highlights:
    the free mercenary at Kashya (the pick, no payment, `RebuildIfEmpty` after it); the stash paying the rest and the
    gold refusal 0x6AE; the level floor (12 floor-bound rolls); a level-up between the list and the hire; 1057 → 11021 at
    both client sites; the saved mercenary's cap 99, name reset and dead branch; `PETS_OnDeath` at a load and three
    deaths in play; resurrection at Kashya; `MERC_AddExp` adding 2·gain only below the owner's level, with the cap
    binding at L 3 and 4. The stock client offers no hire line at Kashya below 8 or at Qual-Kehk with their quests
    open, so the server's two quest refusals are never sent (d-none parts). Proposed moves: rows 1 and 9 → d-none (the
    interaction start always builds first); row 29 stays a shortfall with a d-2c proposal. Totals against `main`
    `a105ae13`: **static 567, harness 511, c-emu 0, blocked 429** (d-none 302), **deferred 2, raised 17: 1 526**.
  - **Symbols (rule 14), I → C:** `HIRE_GiveFreeMerc`, `MERC_AddExp`, `MERC_CapExpGain`, `PETS_OnDeath`,
    `MERC_Resurrect`, `MERC_ResurrectCost`, `sub_00576D90_PayGold`, `sub_004B5C60_ClientHireListDraw`,
    `sub_004B1090_ClientMercInit` (9).
  - **Backlog:** review request
    [2026-10-27-reverser-architect-review-lane-h6f-plan-0038-batch-h6f](../backlog/archive/2026-10-27-reverser-architect-review-lane-h6f-plan-0038-batch-h6f.md);
    spec-writer entry
    [2026-10-27-reverser-spec-writer-h6f-hirelings-raises](../backlog/archive/2026-10-27-reverser-spec-writer-h6f-hirelings-raises.md),
    held until the review. Ledger row added with usage "—".
  - **Next:** the `lane/h6f` review; hirelings is then ready for its Phase 3 re-tag.
- **2026-10-27 — `lane/h6f` review (architect): H6f (`hirelings`) accept with fixes (6); ledger as filed.** `main`
  `a105ae13` had not moved since the lane merged it (`lane/h6c` and `lane/a4t` unmerged; `lane/h6c` does not touch
  `tools/d2pilot.py`), so there was nothing to merge; `tools/test_d2pilot_descend.py` 10 OK. Static only (objdump of
  the pinned image), no harness, no Ghidra.
  - **Rechecked.** `manifest-final.sha256`, `manifest-shots.sha256` and `dev/manifest-dev.sha256` pass `sha256sum -c`;
    under `MemoryMax=4G`, `sweep_h6f.py check` (603, 0 failing), `monpool.py check` and `hirelings.py check` on the 48
    run:2026-10-16-hirelings logs reproduce `check/check-final.txt` `943f181f…`, `check/monpool.txt` `d65e5fbf…` and
    `check/regress-hire-run.txt` `637d34c4…` byte for byte. **The byte-identity claim holds:** `main`'s
    `tools/hirelings.py`, run from a `git archive` of `main`'s `tools/`, gives the same bytes on the 48 logs, and on
    the 15 H6f logs one mismatch (`qk`, "paid 0, price 2650": the refused hire counted by `EAX`), which is why the
    change is needed. The anchors re-read: 0x00572C10–0x00572D04 (`NpcInteractStart`'s early exits and the
    `HIRE_SendList` call), 0x005767D5–0x005767EB, 0x00578BD3–0x00578C04, 0x0056AAA0–0x0056AABB, 0x0057E3F0–0x0057E474,
    0x0057E860–0x0057E983, 0x0057EA28–0x0057EA46, 0x0057728F–0x005772AD, 0x005773B0–0x005773CB, 0x005395BF–0x00539637,
    0x00611830. The 9 symbol raises and the Functions table agree. Recount against `a105ae13`: **static 567, harness
    511, c-emu 0, blocked 429** (d-none 302), **deferred 2, raised 17: 1 526**; 23 statements, 12 / 8 / 1 / 2.
    `tools/test_d2s.py`: 59 of 60 pass; the failure is `test_every_recipe_has_a_base` for the 134 `anim-*` recipes
    only (`lane/a4t` adds them); H6f's 15 recipes have rows, and their hashes pass.
  - **Rulings.**
    - (1) **Rows 1 and 9 → d-none, accepted.** `NpcInteractStart` returns before `HIRE_SendList` only on its refusals
      and for a player already interacting (0x00572C98 loop), so the first interaction always builds; `NPC_OpenStore`'s
      build at 0x00578BFF needs `+0x21` 0, which no stock sequence leaves at a trade.
    - (2) **Rows 17, 18 and 21: the refusal halves are d-none, not d-2c**, on a condition. A second stock client
      filters its own menu the same way, so two clients add nothing, and a hand-made packet is outside the stock
      boundary. But the d-none rests on the client's test matching the server's gates in every state, which is
      unread: three states were observed (Kashya at 3 and 7, Qual-Kehk). That is an untraced gap, filed
      ([entry](../backlog/2026-10-27-architect-reverser-h6f-review-client-hire-line-and-merc-create.md) (1)); if a state
      shows the line that the server refuses, the refusals become a harness piece. Phase 3 states them as `[I]`
      server checks the stock client did not send.
    - (3) **Row 29 stays a shortfall; the d-2c proposal is not accepted.** The third caller,
      `sub_005394A0_PlayerPlaceInAct`, walks a list at `+0x60` of its `EDX` argument and calls `MERC_Create`
      (0x00539637); what fills that list is unread, so "a client joining a game" is a guess. Filed (same entry, (2)).
    - (4) **Row 27 stands raised on its built state.** Under ADR-0013's Neutral rule a tool-built save on stock tables
      backs `[C]` for the code that reads the built field, here `D2S_ReadMercHeader`'s clamp (`first + name > last →
      first`), and nothing about how a stock game would write such a name. The widths are not separated by name 50 and
      go to `[I]` with the wrap bound (fix 1).
    - (5) **Row 25 stays in part.** `2·gain` is `[C]` (6 additions at different gains; `lea ecx, [esi + ebx·2]`
      at 0x0057E8CE), and so is the cap's `min` (4 capped at L 3 and 4, 35 below). The bound is
      `ExpMaxLevel(0) − 1` (class 0's `MaxLvl`, 98 on stock data), tested before the experience write, so a mercenary
      at that level gains nothing; it and the loop's bound are the `[I]` remainder (fix 2).
    - (6) **The `floor` screenshots:** not a tool gap. The session was launched with `--shots workspace/logs/h6f/shots`
      instead of its own directory, so later sessions overwrote its images; its menu count is the pilot's line in the
      hashed driver output, and `lvlup` and `qk`'s kept screenshots show the same two-line menus. The record now says
      so (fix 5).
    - (7) `tools/d2pilot.py`: the run used `638f3c51…` (as recorded); the branch's `043e46d7…` is the same change on
      `main`'s later revision.
  - **Fixes (6), applied in hirelings/0001 and experiments:** (1) *overclaim:* the name clamp's u16 add and unsigned
    compare moved from the `[C]` bullet to an `[I]` reading, with the wrap bound (Rogue: 62 124 fits, 62 125 wraps to 0
    and is kept); (2) *misread:* `MERC_AddExp`'s 98 written as `ExpMaxLevel(0) − 1`, tested before the write, in the
    H6f section, § 6's levelling note and the Functions table, whose row still said "levels up while below the
    owner's level"; (3) *overclaim:* `MERC_CapExpGain`'s "unsigned" to `[I]` (no negative gain or difference logged);
    (4) *overclaim:* § 7's "found no other call in single player" and the row 29 section reworded to the unread
    trigger, with ruling 3; (5) *omission:* the `floor` session's `--shots` path and the driver line its menu count
    rests on; (6) *omission:* the client-test gap behind ruling 2 left unfiled (filed, with row 29's).
  - **Bookkeeping.** Inventory § 2.6 review paragraph and § 5 marks H6f done. Review-fixes Seen lines: reverser 9,
    10, 12 and 15. The review request closed; the spec-writer entry
    [2026-10-27-reverser-spec-writer-h6f-hirelings-raises](../backlog/archive/2026-10-27-reverser-spec-writer-h6f-hirelings-raises.md)
    released with the rulings. Ledger: the lane row filled (usage from the orchestrator: 492 169 tokens, 210 tools,
    73 min; accept with fixes, 6: overclaim 3, misread 1, omission 2); the review row added, usage "—".
  - **Readiness.** **hirelings is ready for Phase 3** on every row but 3, 30 and 33, which wait on H1c and stay `[I]`
    in this pass (the sockets precedent: Phase 3 ran with sock 1's piece routed to H1c); a small re-tag follows H1c's
    acceptance. The conditional d-none parts and row 29 are `[I]` in the spec until the reverser entry is answered.
- **2026-10-27 — Phase 3, the hirelings cluster (spec-writer, `lane/s38h`, from `main` `fcce5b4d`).** Batches S3a,
  S3b, H4b, H1b, H1a and H6f, all accepted; each restated statement checked against its section of
  [hirelings/0001](../findings/hirelings/0001-hirelings.md) and the `lane/h6f` review's rulings and fixes. A partial
  pass on the sockets precedent: rows 3, 30 and 33 stay `[I]` for H1c.
  - **hirelings** {C 95, I 39, L 6} → **{C 137, I 41, L 7}** (recounted with the gate's tag reader; line diff +43 / −1
    `[C]`, +32 / −30 `[I]`, +2 / −1 `[L]`). Raised: S3a rows 4 (the layout; the 0x450 bound `[I]`), 19 (the slot; the
    refusals `[I]`), 26 (the empty header; one-field zeros `[I]`); S3b 7, 8 (the fatal branches `[I]`); H4b 34; H1b
    24 (F8); H1a 32 (§ H items); H6f 5, 6, 10, 14, 15, 16, 20, 27 (the clamp only, built state; the u16 add and unsigned
    compare `[I]` with the wrap bound, fix 1), 28 ×2, 31, 37, and in part 2 and 35 (Act I, expansion), 17, 18 and 21
    (the reads and passes; the two refusals `[I]` server checks the stock client did not send, ruling 2), 23 (no
    classic Greiz hire), 25 (a new levelling block G2–G7: `2·gain`, the owner test, the cap's `min` and the `·86 >> 8`
    share `[C]`; `M = ExpMaxLevel(0) − 1`, tested before the write, and the loop bound `[I]`, fix 2; the cap's unsigned
    width `[I]`, fix 3), 36 (Kashya and Qual-Kehk). Rows 1 and 9 written as no stock case (C2: the skip `[C]`, the
    reach `[I]`, ruling 1); row 29 an `[I]` shortfall with the unread `+0x60` list (H12, ruling 3, fix 4). New:
    `HIRE_Hire` returns no value. Inline `[I]` on lines no case reached (A1, A2, D1, D5, E2, F1, F2, G4, G5, G7, H12,
    H13). Open questions: the not-reached list struck and rewritten; one `[L]` added for the reverser entry's two reads.
  - **Wiki:** the hireling sections of [characters](../wiki/characters.md) refreshed, `based_on` hirelings 2026-10-27.
    wiki/saves still lists hirelings 2026-10-20 (W4 warning; `lane/wiki`'s page, left).
  - **Map and README:** the research-map row rewritten whole; the root README's hirelings row 2026-10-27.
  - **Backlog:** closed the [H6f entry](../backlog/archive/2026-10-27-reverser-spec-writer-h6f-hirelings-raises.md) and
    the [H1b entry](../backlog/archive/2026-10-27-reverser-spec-writer-h1b-save-d2s-and-hirelings-raises.md); annotated
    the [H1a entry](../backlog/2026-10-27-reverser-spec-writer-h1a-save-d2s-player-creation-raises.md) (hirelings 32
    done; 3, 30, 33 for H1c); filed the
    [counts entry](../backlog/2026-10-27-spec-writer-architect-s38h-hirelings-counts-for-the-research-map.md) and the
    [review request](../backlog/2026-10-27-spec-writer-architect-s38h-review-hirelings-phase-3.md). Ledger row added,
    usage "—".
  - **Next:** architect review of `lane/s38h`; the H1c re-tag of rows 3, 30 and 33 after H1c.
