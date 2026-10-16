---
based_on: [process]
---

# How we know

The other wiki pages explain how Diablo II: Lord of Destruction 1.14d builds levels, fills them and decides what
drops. This page explains why those explanations can be trusted, and how far. It is about the project's method, not
about the game, so it restates decisions and rules rather than specs: [ADR-0001](../adrs/0001-target-toolchain-evidence-sources.md)
(target, evidence, sources), [ADR-0003](../adrs/0003-runtime-experiments.md) (runtime experiments),
[ADR-0004](../adrs/0004-boundary-oracles-in-reproduction.md) (reproduction across a callee),
[ADR-0006](../adrs/0006-docs-gate.md) (the docs gate), [ADR-0007](../adrs/0007-fetched-leads-only.md) (leads),
[ADR-0010](../adrs/0010-forced-path-runs.md) and [ADR-0013](../adrs/0013-forced-path-runs-cell-level.md) (forced-path
runs), [ADR-0012](../adrs/0012-human-wiki.md) (this wiki) and the
[evidence rules](../../.claude/skills/architect/references/evidence-rules.md). Where this page and those texts
disagree, they win.

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
   same outputs as the game.

In a spec, a lead may appear only under *Open questions*. Specs state confirmed and inferred behaviour; inferred
behaviour is the project's best reading of the code, and it is marked so that a reader knows it has not been
cross-checked.

## Runs: watching the game play

A *run* is a recorded experiment on the real game
([ADR-0003](../adrs/0003-runtime-experiments.md#decision)). The unmodified program runs under wine on a separate,
hidden display, with the game's [seed](../glossary.md) fixed by the game's own `-seed` switch. A debugger stops at
chosen places in the code, prints values, and lets the game continue; it never changes game memory. Each run has a
record that says exactly how to repeat it.

A run counts as evidence only when the project's own model reproduces the logged values from the recorded inputs,
or when the record states the observed values that the claim depends on. Because the game is deterministic for a
given seed, two runs with the same seed give the same values (once memory addresses, which vary, are masked), and the model is checked against every logged value:
"0 mismatches over N cases" is the usual form of a run result in the specs.

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

## What "reviewed" means

The work is split into four lanes: an **archivist** (game files, table and format documentation, parsers), a
**reverser** (reading the program and running experiments, writing *findings*), a **spec-writer** (turning findings
and table docs into specs) and an **architect** (plans, decisions, and reviews). A spec is drafted from findings only:
the spec-writer never investigates and never fills a gap with plausible behaviour; a gap becomes an open question.

Before a spec counts, the architect reviews it with fresh eyes: that anchors resolve, that each confirmed statement
names its independent check, that no lead sits in the body, and that the text does not read like someone else's
decompiled code ([ADR-0001](../adrs/0001-target-toolchain-evidence-sources.md#decision)). Only then does the
[research map](../specs/README.md) mark the spec `reviewed`. A mechanical gate
([ADR-0006](../adrs/0006-docs-gate.md#decision)) checks on every commit that touches the documentation that anchors and links resolve and that tag
counts add up; it proves that references exist, not that claims are right, so it never replaces the review.

## How this wiki relates to the specs

The wiki makes no claims of its own ([ADR-0012](../adrs/0012-human-wiki.md#decision)). Every page lists, at its top,
the reviewed specs it restates and the date of the spec version it was written from, and every section links the
spec sections it explains. If a page and a spec disagree, the spec is right and the page is fixed. The wiki covers
reviewed specs only, it is not published, and it leaves out addresses, anchors and code.

To go deeper from any wiki page: follow the section's link into the spec; the spec's *Evidence* section names the
findings; a finding names the runs it rests on, whose records are in the `experiments.md` file of each findings
directory (for example [the item experiments](../findings/items/experiments.md)).
