# ADR-0010 — Forced-path runs: an edited decision table may drive a rare stock path

> **Status:** accepted
> **Date:** 2026-10-14
> **Related plan(s):** 0019-items-uniques-sets (Phase 2); later item plans (0021 affixes, quest drops, vendors)

## Context

Plan 0019 Phase 2 must reproduce the unique and set builders over at least 30 builds of each. On stock data the
builders run only when the quality roll returns unique or set. Thirty-one agent-driven Hell sessions with magic find
458 (Eldritch, the Act V superunique farmed for this) created 304 items: 1 unique build and 3 set builds
([plan 0019 log](../plans/0019-items-uniques-sets.md#implementation-log)). The target would take about 450 sessions.
Magic find is not the limit: its unique bonus has diminishing returns (458 → about 161 % effective, 608 → about 177 %),
and the unique and set outcomes stay rare among all quality outcomes.

Until now, runs on edited data were refused as evidence. The rulings on `sparsePopulate` (plan 0014), the
`champion` = 0 rows (plan 0018) and the TC-named disabled unique (plan 0019, case (d)) concerned claims that **only**
edited data could reach. A run on edited data could not support a claim about the stock game in those cases, because
the edited data was the very input the claim was about.

The builders are a different case. Their path is reachable on stock data, and was reached in run evidence above, but
it is rare. What decides whether the path runs is one table, ItemRatio, read by the quality roll that
[items/quality](../specs/items/quality.md) already specifies at review grade. The builders themselves read UniqueItems,
SetItems, the item bases, the item seed and the item level, none of which the quality roll edits. The loader reads a
loose file only under `-direct`, and `-txt` is a separate switch
([data/0001](../findings/data/0001-excel-loader.md), [data/0002](../findings/data/0002-mpq-precedence.md)), so one
table can be replaced while every other table loads from the stock archives.

## Decision

A reproduction may use a **forced-path run** to reach a stock code path that is rare on stock data. The run edits
only a **decision table**, the table whose cells choose whether the path runs, and never a table that the path itself
reads. The edit is a single loose `.bin` under `-direct` (no `-txt`), in a copy of the game directory that holds no
other loose data file. The run record states the edited table, every changed cell (old → new) and why the path still
receives stock inputs, and it shows that the other tables are the stock ones (the loaded files' hashes or the logger's
table checks). A forced-path run corroborates (`[C]`) claims about the forced path: its filters, draws, seed use,
fallbacks and outputs. It corroborates nothing about the decision table's own effect or about the code that reads it.
Those claims keep their evidence from stock runs. The run id ends in `-forced` (`run:YYYY-MM-DD-<slug>-forced`), and every
`[C]` that rests on it cites it by that id. A forced-path run never stands alone for a plan: the plan also logs the
path on stock data at least once where stock play reaches it, and the model checks both runs with 0 mismatches. A claim
that only edited data can reach stays `[I]`, under the earlier rulings, whatever this ADR allows.

## Consequences

### Positive

- Rare stock paths (unique and set builders, the fallback chains, a repeated unique, a ladder row in single player)
  can be reproduced in hours instead of hundreds of sessions.
- The boundary is mechanical: the edited table is named, its cells listed, and the path's own inputs are stock.
- The same rule serves later item plans whose paths are rare on drops (affix edge cases, quest drops).

### Negative

- The forced run's distribution is not the game's. Frequencies, ratios and "how often" claims can never come from it,
  and a careless finding could still cite it for one. The review must check every citation of a `-forced` run.
- Whether a table is a pure decision table is a judgment. If the forced path also reads the edited table (for example
  a builder that re-reads ItemRatio), the run is invalid for that claim. Phase 1 must show the path's reads first.
- It adds a tool step: writing a valid `.bin` for the edited table, and checking that the game loaded it.

### Neutral

- The earlier rulings stand: a claim only edited data can reach still has no Phase 2 case.
- ADR-0004 boundary oracles are unchanged and combine with this: the forced run may still treat out-of-scope callees
  as oracles.

## Alternatives considered

**A smaller stock-only target** (about 5 uniques and 5 sets plus the required cases). It lost because even that needs
dozens of sessions at the measured yield, and several required cases (a repeated unique, a ladder row) need specific
uniques that stock drops may not produce at all.

**Owner play.** Owner sessions found rare monsters fast, but item quality is a per-drop roll that no route improves,
so play time does not change the yield by an order of magnitude.

**Gambling or other creation paths.** These reach the builders on stock data, but through other callers with their own
quality logic. They belong to their own plans, and their yields for uniques are no better.

**Editing `-direct -txt` text tables.** It lost because `-txt` recompiles every table from text, and three item
tables have text forms that differ from the live `.bin` in record format; the run would no longer load stock data
for the path.
