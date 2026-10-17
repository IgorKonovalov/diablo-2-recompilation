---
based_on: [process]
---

# How we know

The other wiki pages explain how Diablo II: Lord of Destruction 1.14d builds levels, fills them, decides what
drops and resolves a hit. This page explains why those explanations can be trusted, and how far. It is about the
project's method, not about the game, so it restates decisions, rules and plan records rather than specs:
[ADR-0001](../adrs/0001-target-toolchain-evidence-sources.md) (target, evidence, sources),
[ADR-0003](../adrs/0003-runtime-experiments.md) (runtime experiments),
[ADR-0004](../adrs/0004-boundary-oracles-in-reproduction.md) (reproduction across a callee),
[ADR-0006](../adrs/0006-docs-gate.md) (the docs gate), [ADR-0007](../adrs/0007-fetched-leads-only.md) (leads),
[ADR-0008](../adrs/0008-two-client-harness.md) (two clients in one game),
[ADR-0010](../adrs/0010-forced-path-runs.md) and [ADR-0013](../adrs/0013-forced-path-runs-cell-level.md) (forced-path
runs), [ADR-0011](../adrs/0011-harness-slots.md) (harness slots), [ADR-0012](../adrs/0012-human-wiki.md) (this wiki),
[ADR-0014](../adrs/0014-scope-game-simulation.md) (game simulation and its evidence),
[ADR-0015](../adrs/0015-emulated-reproduction.md) (emulated reproduction),
[ADR-0018](../adrs/0018-backlog-one-file-per-entry.md) (the backlog), the
[evidence rules](../../.claude/skills/architect/references/evidence-rules.md), and the records of
[plan 0038](../plans/0038-inferred-claims-sweep.md) (the inferred-claims sweep) and
[plan 0041](../plans/done/0041-stats-and-states.md) (stats and states). Where this page and those texts disagree, they
win.

## One binary, read directly

Everything is checked against exactly one program: the 1.14d `Game.exe`, pinned by its sha256 hash in the
[inventory](../inventory.md). In 1.14d every library the older versions shipped separately is merged into that one
file, so there is one binary to study and nothing to map between versions
([ADR-0001](../adrs/0001-target-toolchain-evidence-sources.md#decision)). Other versions (1.09, 1.10, 1.13) are out of
scope.

The project reads the program's machine code with a decompiler and writes down what it finds, in its own words.
Two kinds of outside material are treated differently
([sources policy](../adrs/0001-target-toolchain-evidence-sources.md#decision)):

- **Community documentation** (file guides, articles, forum posts) may be used as a *lead*: a hint about where to
  look. Each one used is registered in [`docs/sources.md`](../sources.md), and a lead is a document fetched and read
  in the same session, never something recalled from memory ([ADR-0007](../adrs/0007-fetched-leads-only.md)).
  Agreement with the community never counts as proof, because much community knowledge comes from older versions;
  disagreement must be settled by the project's own evidence.
- **Decompiled or reconstructed game source written by others** is never read, copied or paraphrased.

## Three levels of confidence

Every statement about behaviour in a spec carries an *anchor* (where in the program, which table column, or which
recorded experiment it rests on) and one of three confidence tags
([evidence rules § Tags](../../.claude/skills/architect/references/evidence-rules.md#tags)). The wiki never shows the
tags themselves; it says in words when something is not settled.

| Level | What it means | How the wiki says it |
|---|---|---|
| **Confirmed** | the code was read **and** something independent agrees with it | stated plainly |
| **Inferred** | the code was read and understood, but nothing independent has checked it yet | "read from the code but not yet confirmed by a run", or similar |
| **Lead** | a hint with no anchor in the program yet | only as an open question: "unknown", "not yet found" |

An independent check is one of four things
([evidence rules § Tags](../../.claude/skills/architect/references/evidence-rules.md#tags)):

1. **a second code path**, for example the code that writes a value and the code that reads it agree;
2. **data behaviour**: the explanation fits every row of a game data table;
3. **a runtime experiment**: the game was run and the value was observed;
4. **bit-exact reproduction**: a small program written by the project, given the same inputs, produces exactly the
   same outputs as the game. The game's side of the comparison is either the running game or, under strict
   conditions, the game's own code run in an emulator (below).

In a spec, a lead may appear only under *Open questions*. Specs state confirmed and inferred behaviour; inferred
behaviour is the project's best reading of the code, and it is marked so that a reader knows it has not been
cross-checked. Confidence can also go down: when new evidence contradicts a claim, the claim is demoted and the
contradiction is recorded
([evidence rules § Promotion](../../.claude/skills/architect/references/evidence-rules.md#promotion)).

## Runs: watching the game play

A *run* is a recorded experiment on the real game
([ADR-0003](../adrs/0003-runtime-experiments.md#decision)). The unmodified program runs under wine on a separate,
hidden display, with the game's [seed](../glossary.md) fixed by the game's own `-seed` switch. A debugger stops at
chosen places in the code, prints values, and lets the game continue; it never changes game memory. Each run has a
record that says exactly how to repeat it. Several runs can go on at once, each in its own numbered *slot* (its own
hidden display and its own copy of the game's settings and saves); a slot changes nothing about what a run proves
([ADR-0011](../adrs/0011-harness-slots.md#decision)).

A run counts as evidence only when the project's own model reproduces the logged values from the recorded inputs,
or when the record states the observed values that the claim depends on. Because the game is deterministic for a
given seed, two runs with the same seed give the same values (once memory addresses, which vary, are masked), and
the model is checked against every logged value: "0 mismatches over N cases" is the usual form of a run result in
the specs.

A run has limits that the specs inherit
([ADR-0003 § Negative](../adrs/0003-runtime-experiments.md#negative)): a breakpoint only sees code the run actually
reaches, so behaviour that needs a rare situation (a particular quest state, a multiplayer party, a rare drop) stays
inferred until a run reaches it.

Some code paths are too rare on the stock data to reach in reasonable time. A *forced-path run* edits a few cells of
one table so that the rare path is taken, and lists every changed cell
([ADR-0010](../adrs/0010-forced-path-runs.md#decision), [ADR-0013](../adrs/0013-forced-path-runs-cell-level.md#decision)).
Such a run confirms only behaviour whose code reads none of the edited cells, never "how often" something happens,
and the plan also logs the same path at least once on stock data wherever ordinary play reaches it.

## Bit-exact reproduction and boundary oracles

The strongest check is a reproduction: the spec's algorithm, written as a small program, fed the logged inputs of a
run, must produce every output and every random-number state the game produced. Random draws come from per-object
[seeds](../glossary.md), so a single missing or extra draw shows up immediately as a mismatch.

Game code calls other game code. The treasure-class resolver, for example, calls the item quality roll in the middle
of its own loop, on the same seed. Rather than wait for every callee to be specified, a reproduction may treat a
named callee as a [boundary oracle](../glossary.md)
([ADR-0004](../adrs/0004-boundary-oracles-in-reproduction.md#decision)): the run logs the seed on entry and exit of
every call to it, the model checks that it arrives with exactly the logged entry seed, and then takes the logged exit
seed and result as given. That confirms the code around the oracle, and nothing inside it. The callee's own plan
later replays the same logs with the oracle replaced by its model.

## Emulated reproduction: one function, run on its own

Some code is never reached by ordinary play in a session of reasonable length: an edge of the arithmetic, an unused
table column, an error branch. For such code the project can run **the game's own machine code, one function at a
time, inside Ghidra's emulator**, and compare it bit for bit with the project's model
([ADR-0015](../adrs/0015-emulated-reproduction.md#decision)). No instruction is patched; the project only writes the
memory the function starts from. Because the inputs are chosen, they can be random as well as stock rows. Each
branch a claim covers must be driven by at least one case, and each family of cases has a *negative control*: a
deliberately wrong model or output that the checker must reject, to show the comparison can fail.

Two safeguards were added while the inferred-claims sweep used the method, on 2026-10-17:

- **A trace of every memory read.** The emulator script lists every data access outside the stack and the memory the
  project supplied, and each one must be accounted for in the record, normally as constant data that no game code
  writes while playing. A read the record cannot account for voids the claims that depend on it
  ([ADR-0015 § Decision](../adrs/0015-emulated-reproduction.md#decision);
  batch S1e, [run:2026-10-17-sweep-emu](../findings/data/experiments.md#run2026-10-17-sweep-emu): 28 643 emulated
  calls in ten families, all bit-exact, each negative control failing as it should, by the
  [plan 0038 log](../plans/0038-inferred-claims-sweep.md#implementation-log)).
- **Guard stops.** The script stops any case that reaches the entry of the game's fatal-error path or of its memory
  allocator, and the checker counts such a stop as a failure, so no confirmed claim rests on a case that left the
  function's declared world
  (batch S1f, [run:2026-10-17-sweep-emu2](../findings/data/experiments.md#run2026-10-17-sweep-emu2): 18 800 emulated
  calls in eight families, none stopped; at the review, a case rewritten to hit a guard did fail, by the
  [plan 0038 log](../plans/0038-inferred-claims-sweep.md#implementation-log)).

What emulation **can** confirm: what a function does with its arguments, the bytes it reads and its seeds, that is,
its return value, the bytes it writes, the seeds' exit states, and so how many random draws it makes. What it
**cannot** confirm ([ADR-0015 § Decision and § Negative](../adrs/0015-emulated-reproduction.md#negative)):

- what the game's memory actually holds at those offsets while playing: what each offset *means* (which table
  column, which field) needs its own evidence;
- who calls the function, when, and on which live seed in play: that still needs a run;
- crashes and processor faults, x87 floating-point results, calls into the operating system, and code that rewrites
  itself;
- a mistake in the emulator's own model of an instruction, which the decompiler, built from the same model, would
  share. Where a claim turns on an unusual instruction, the record also cites a second disassembler. One such limit
  is already known: the emulator returns 0 for one overflowing division that the real processor traps on
  ([plan 0038 log, batch S1e](../plans/0038-inferred-claims-sweep.md#implementation-log)).

## Simulation: one event at a time, counted in frames

Combat, stats and states run every game frame, on many units at once, and under wine the frame on which something
happens depends on timing, so a whole play session cannot be replayed frame for frame
([ADR-0014](../adrs/0014-scope-game-simulation.md#context)). Simulation claims are therefore checked **one event at a
time** ([ADR-0014 § Decision](../adrs/0014-scope-game-simulation.md#decision)). An event is one call of a named entry
point, for example one attack resolved against one target, or one damage-over-time tick. For each event the run logs,
at that boundary, the inputs the formula reads, the state of every seed it draws on at entry and at exit, and its
outputs; the model predicts every draw and output and must arrive at the logged exit seed.

- **Chained pairs.** An event's entry seed may be taken from the log, since the draws before it may belong to code
  not yet specified (another monster's AI, say). To rule out hidden draws, every event kind needs *chained* events:
  two in a row on one seed, where the second one's entry is checked against the first one's predicted exit. A kind
  with no chained pair keeps its draw order inferred.
- **Value oracles.** The stat values an event reads (a unit's defence, its resistances) are logged and taken as
  given. A confirmed combat claim covers the formula from those inputs to the outputs, not how the inputs came to be;
  a later plan that models the stats re-checks the kept logs with its model in their place, where the logs hold what
  the model needs.
- **Game frames.** Every timing claim is in game frames, as the server's frame counter reads them. Nothing is said
  about wall-clock time. Only what the server decides counts as evidence; a number shown on the character screen is
  presentation.
- **"No draw" shown by the seeds.** The code reading for the stats and states plan found no random draw in any of its
  event kinds. Plan 0041 turned that into a check: the run logs the game seed and the acting unit's seed on entry and
  exit of every event, and a kind whose seeds stay unchanged over at least 20 events has its "no draw" confirmed. A
  kind that moves a seed is re-read and must then meet the chaining minimum
  ([plan 0041, Phase 2, amended 2026-10-17](../plans/done/0041-stats-and-states.md)). In its run one kind did move a seed
  (a damaging aura draws once per hit) and was checked through chained pairs instead. The specs of that plan are not
  reviewed yet, so no wiki page restates them.

The first simulation plan, combat formulas, checked 40 655 logged events in 40 logs with 0 mismatches
([plan index, plan 0037](../plans/README.md); record:
[run:2026-10-16-combat](../findings/combat/experiments.md#run2026-10-16-combat)).

## Two clients in one game

Some behaviour exists only with a second player in the same game: a party, the party count some drops depend on,
player against player. The game refuses to run twice in one wine session, so a multiplayer
experiment runs two copies in separate prefixes on separate hidden displays, joined in a TCP/IP game over the
machine's own loopback address ([ADR-0008 § Decision](../adrs/0008-two-client-harness.md#decision)). Only the host is
watched by the debugger. Every resolver call logged in the first trial ran in the host's process, so the host sees
the server side; a claim about the joiner's own client state would need its own decision.

While hosting, the game listens on its network port on every interface. The owner accepted the method on one
condition: before any hosting run, the lane makes sure that port cannot be reached from outside the machine (a
firewall rule, or a confirmed existing block) and records how in the run record. Host and joiner use two numbered
slots, never the owner's ([ADR-0008, status](../adrs/0008-two-client-harness.md)). The condition is met: on
2026-10-17 the owner's firewall listing showed the port dropped on every interface but the machine's own, and before
each hosting session the lane re-reads the firewall state and asks the owner again only if it changed
([plan 0044 log](../plans/0044-multiplayer-branches.md#implementation-log)). Until a two-client run reaches
them, multiplayer branches stay "read from the code"
([ADR-0003 § Negative](../adrs/0003-runtime-experiments.md#negative)); plan 0044 is the plan that will run them.

## "Not reachable on stock data"

Some inferred claims may never be confirmed by a run, because nothing in the shipped data makes the game take that
branch: dead code, or a safety check stock data never fails. The sweep of inferred claims classes these as *no
observable* (`d-none` in its inventory) and records the reason, so that a spec's remaining inferred statements are
explained ([plan 0038 § Classes](../plans/0038-inferred-claims-sweep.md#classes)). Such a statement stays inferred:
the class says why no run will reach it; it does not confirm the code reading.

Ruling a branch out takes more than not having seen it. It takes a **bound**: a static argument about what can reach
the branch, completed, where the argument alone leaves cases open, by an exhaustive scan or enumeration of all of
them. A sample of seeds is not
a bound, however large, because the next seed might be the one. The outdoor generator's vertex merge (statement 7 of
the outdoor inventory) shows the difference
([inventory § 2.6, the `lane/rbs3` and `lane/rbs4` blocks](../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews);
[drlg/0008, the layout bound](../findings/drlg/0008-outdoor.md#h5e-reachability-a-the-layout-bound-2026-10-17-lanerbs4)):

- A scan of 600 map seeds met the merge's condition in 0 of 52 200 windows. That is a sample, so it moved nothing.
- How an act's levels are laid out depends on random draws, but in Acts I, II, IV and V each of those draws is only
  ever used through a mask of a few bits. Enumerating every combination of those bits covers every layout any seed
  can give, and more; the condition was met 0 times, in all three difficulties. For those four acts that is a bound,
  so that half of the statement became "no observable".
- Act III's jungle layout draws ranged values and restarts, so it is not enumerated this way. Its half keeps only
  the 600-seed sample and stays a shortfall (below). A ruling for the whole statement would have claimed Act III on a
  sample.

## Shortfalls and named open questions

Not every run reaches everything its plan hoped for. When a case is not reached, the record says so: a **shortfall**
is named with its count and its reason, the claim stays inferred, and the plan is not blocked by it
([plan 0038 § Phase 2](../plans/0038-inferred-claims-sweep.md#phase-2--harness-batches)). For example, the stats and
states run met 7 shrines and 5 wells, below the plan's target of 50 operates and below the floor of 20 events per
kind for the "no draw" check, and its review accepted them as a named shortfall ([plan 0041 log, Phase 2 review](../plans/done/0041-stats-and-states.md)).

Gaps in knowledge are written down, not filled. A spec's *Open questions* section holds what is unknown and every
lead; a gap one lane needs another to close becomes a backlog entry, one file per request, closed with a link to the
answer ([ADR-0018](../adrs/0018-backlog-one-file-per-entry.md#decision)). The wiki repeats each page's open questions
under *What is not known yet*.

## The inferred-claims sweep

Each plan confirmed what its own run reached and left the rest inferred. On 2026-10-16 the reviewed specs held
1 526 inferred statements against 2 531 confirmed ones, never looked at side by side
([plan 0038 § TL;DR](../plans/0038-inferred-claims-sweep.md#tldr)). Plan 0038 lists every one of them, classes it by
its route to confirmation (a new check over logs already kept, one more session with an existing recipe, a new
recipe, a static second source, an emulated run) or by the reason it is blocked (two clients, owner play, a later
simulation phase, edited data only, an owner addendum of an earlier plan, no observable), and works through the routes in batches.

*Raising* an inferred claim means adding the independent check it lacked and naming it in the statement
([evidence rules § Promotion](../../.claude/skills/architect/references/evidence-rules.md#promotion)). A batch's
claims are raised in the findings first; once the architect accepts the batch, the spec-writer re-tags the spec
statements that rest on them, demotes any the batch contradicted, and updates the counts
([plan 0038 § Phase 3](../plans/0038-inferred-claims-sweep.md#phase-3--re-tag-the-specs)). The wiki pages are then
refreshed from the re-tagged specs, so a sentence that said "not yet confirmed by a run" may lose that hedge.

## What "reviewed" means

The work is split into four lanes: an **archivist** (game files, table and format documentation, parsers), a
**reverser** (reading the program and running experiments, writing *findings*), a **spec-writer** (turning findings
and table docs into specs) and an **architect** (plans, decisions, and reviews). A spec is drafted from findings only:
the spec-writer never investigates and never fills a gap with plausible behaviour; a gap becomes an open question.

Nothing a lane produces counts until the architect has reviewed it with fresh eyes: that anchors resolve, that each
confirmed statement names its independent check, that no lead sits in the body, and that the text does not read like
someone else's decompiled code ([ADR-0001](../adrs/0001-target-toolchain-evidence-sources.md#decision)). The review of
a harness batch re-runs its checker on the batch's logs
([plan 0038 § Phase 2](../plans/0038-inferred-claims-sweep.md#phase-2--harness-batches)), and the reviews of the
emulated batches re-ran kept cases and got byte-identical outputs
([plan 0038 log](../plans/0038-inferred-claims-sweep.md#implementation-log)). Most work is accepted *with fixes*: an
overclaim narrowed, a count corrected, a stale cross-reference updated. The fixes are counted by kind in a
[ledger](../plans/metrics.md), and the kinds that keep recurring become rules each lane checks before it asks for
review. Only after review does the [research map](../specs/README.md) mark a spec `reviewed`.

A mechanical gate ([ADR-0006](../adrs/0006-docs-gate.md#decision)) checks on every commit that touches the
documentation that anchors and links resolve and that tag counts add up; it proves that references exist, not that
claims are right, so it never replaces the review.

## How this wiki relates to the specs

The wiki makes no claims of its own ([ADR-0012](../adrs/0012-human-wiki.md#decision)). Every page lists, at its top,
the reviewed specs it restates and the date of the spec version it was written from, and every section links the
spec sections it explains. If a page and a spec disagree, the spec is right and the page is fixed. The wiki covers
reviewed specs only, it is not published, and it leaves out addresses, anchors and code.

To go deeper from any wiki page: follow the section's link into the spec; the spec's *Evidence* section names the
findings; a finding names the runs it rests on, whose records are in the `experiments.md` file of each findings
directory (for example [the item experiments](../findings/items/experiments.md)).
