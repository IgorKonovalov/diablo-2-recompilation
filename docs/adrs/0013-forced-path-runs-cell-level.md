# ADR-0013 — Forced-path runs: "a table the path reads" is decided cell by cell

> **Status:** accepted
> **Date:** 2026-10-16
> **Supersedes:** [ADR-0010](0010-forced-path-runs.md) (its decision paragraph; everything else in it stands)
> **Related plan(s):** 0019-items-uniques-sets, 0024-items-properties, 0027-backlog-sweep-3, 0032-items-quest-drops

## Context

[ADR-0010](0010-forced-path-runs.md) lets a run edit one **decision table** to make a rare stock path common, and
"never a table that the path itself reads". Read at table level, that clause rules out most of the forced runs the
project has made, because the edited table is usually also read somewhere on or near the forced path:

- [run:2026-10-15-berserk-forced](../findings/monsters/experiments.md#run2026-10-15-berserk-forced) edited 13 MonUMod
  cells (row 0 `constants`, the champion chance, and the `cpick` cells of rows 16, 36, 37 and 38). MonUMod is also read
  by the mod handlers, through their own row's `constants`. The `berserk` handler (`0x005A1280`) reads no MonUMod cell
  at all: −75 and 300 are immediates, and its only table input is DifficultyLevels `ChampionDamageBonus`, which was
  stock.
- [run:2026-10-14-uniques-forced](../findings/items/experiments.md#run2026-10-14-uniques-forced),
  [run:2026-10-14-props-forced](../findings/items/experiments.md#run2026-10-14-props-forced) and
  [run:2026-10-15-items-chain-forced](../findings/items/experiments.md#run2026-10-15-items-chain-forced) edited ItemRatio cells.
  ItemRatio is read by the quality roll, which sits on the same creation path as the builders, the property
  writers and the ethereal roll (`0x00556CA0`). None of those three reads an ItemRatio cell: every reference to
  `g_pItemRatio` lies in its loader and `ITEMRATIO_Select` (`0x00637874`–`0x006379B5`).

Every review so far has ruled **cell by cell**: a claim may rest on the forced run when the code the claim describes
reads none of the edited cells. That is how the berserk handler and the ethereal roll were confirmed on 2026-10-16,
and how plan 0027 ruled that the MonUMod row 0 edit "taints no claim"
([plan 0027 log](../plans/done/0027-backlog-sweep-3.md#implementation-log)). The same reading also produced the
opposite verdict where it should: in
[run:2026-10-15-uniques-tcnamed-forced](../findings/items/experiments.md#run2026-10-15-uniques-tcnamed-forced) the
edited TreasureClassEx cells name the unique that the claim is about. That makes them the claim's own input, so those
claims went back to `[I]`.

The written rule and the rulings therefore disagree. A later reviewer applying ADR-0010 literally could revert every
`[C]` above, and a lane cannot tell in advance which reading a review will apply.

## Decision

A forced-path run edits cells of one table, given as a single loose `.bin` under `-direct` as ADR-0010 requires, and
the run record lists every changed cell (old → new) with `excel_bin.py bindiff` showing no other change. A claim may
cite the run as `[C]` evidence only when **the code the claim describes reads none of the edited cells**. That code
runs from the point where the edited cells have made their decision to the claim's output. Its reads of the edited
table are recorded per claim, from the Phase 1 reading, as the row and column (or field offset) of each read:

- A read of a fixed row is that row's cell.
- A read whose row index comes from data or a loop counts as a read of that column in **every** row.
- If the reads cannot be bounded, the whole table counts as read.

A claim whose code reads an edited cell, or whose subject the edited cells name, stays `[I]`. The rest of ADR-0010
is unchanged:

- the `-forced` run id;
- the stock companion run;
- no frequencies or "how often" claims;
- nothing about the decision cells' own effect or the code that reads them;
- a claim only edited data can reach stays `[I]`.

## Consequences

### Positive

- The rule now says what the reviews already do. The `[C]` raised on the berserk handler, the ethereal roll, the
  property writers and the unique and set builders rest on a written rule instead of a series of rulings.
- The test is mechanical once Phase 1 has recorded the reads. A reviewer compares two lists of cells, the edited ones
  from `bindiff` and the claim's reads from the finding.
- More rare paths can be forced. A table that is both the decision table and an input elsewhere is no longer off
  limits, as long as the forced claim's own reads miss the edit.

### Negative

- Phase 1 must record cell-level reads (column offsets, fixed or variable row) for every function a forced run will
  back. A finding that names only the table is not enough, and the claim stays `[I]` until the reads are written down.
- Proving a negative ("this function reads no ItemRatio cell") rests on a static reading of every path through the
  function and its callees. A missed indirect read (a callback, a pointer kept from an earlier lookup) would wrongly
  allow a `[C]`. The review must check the callees, not only the function body.
- An edited cell can still change state the claim reads indirectly. For example, a different mod drawn earlier can
  change a stat the handler later reads. The claim's inputs must be shown stock at the point of entry, by the logger
  or by the model's entry assertions (ADR-0004), not only by the absence of a table read.

### Neutral

- No existing `[C]` changes. Every current citation of a `-forced` run was ruled on this reading.
- ADR-0010's context, its alternatives and its other consequences stay the record of why forced runs exist.
- Tool-built saves on stock tables (ADR-0003 inputs, such as the level-up, vendor and mercenary saves) are not
  forced-path runs and need no `-forced` id. They support `[C]` for code that reads the built state as input, and
  nothing about how a character reaches that state, as the plan 0031, 0033 and 0034 reviews ruled.

## Alternatives considered

**Keep the table-level reading.** It lost because it voids the berserk, ItemRatio and property confirmations although
none of that code reads an edited cell. Those paths would then need hundreds of stock sessions, the cost ADR-0010
was written to avoid.

**Allow any edit outside the claim's own function.** It lost because it ignores the callees and data-indexed reads. A
builder that indexes an edited column through a row id taken from data would pass, although its output depends on the
edit.

**Decide case by case in reviews with no written rule.** It lost because lanes need to know before a run whether its
evidence will count, and the TC-named reversal shows the cost of finding out at review.
