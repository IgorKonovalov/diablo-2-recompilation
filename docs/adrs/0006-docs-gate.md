# ADR-0006 — A mechanical docs gate: strict checks on what can be checked, review for the rest

> **Status:** accepted
> **Date:** 2026-10-11
> **Related plan(s):** 0007-docs-gate

## Context

The evidence rules (ADR-0001, `references/evidence-rules.md`) are enforced only by the architect's
review. Several of them are mechanical, and a reviewer checks them by hand and by sampling: whether
an anchor's name and address match `re/symbols.csv` (the review spot-checks three per document),
whether every `src:` id is in `docs/sources.md`, whether `[L]` stays under *Open questions*, and
whether a spec's front-matter `tags:` counts are true. Nothing checks that relative links resolve,
or that a parser still reads every file the way its format doc says once someone edits it.

A prototype run on 2026-10-11 found the repository already clean on the strict rules: all 322
`fn:`/`data:` anchors in `docs/specs/` and `docs/findings/` resolve to a matching name and address,
no spec has an `[L]` outside *Open questions*, and every spec's front-matter tag counts match its
body. A gate can therefore start strict, with no grandfathered failures.

There is a second reason. Handing approved plans to an unattended driver (the conductor used in
sibling projects) is under consideration, and such a driver is only as safe as the gate it runs
between sessions. That decision is not taken here. This ADR only makes sure a gate exists first.

"Every behavioural claim carries a tag" can't be checked mechanically: deciding what is a claim is
the reviewer's judgement.

## Decision

We add one command, `python3 -I tools/gate.py`, with two tiers. The **fast tier** (the default)
reads only tracked files under `docs/` and `re/` and fails on any **error**: an anchor that doesn't
resolve (`fn:`/`data:` against `re/symbols.csv` by name *and* address, `src:` against
`docs/sources.md`, `run:` against an `experiments.md` heading, `tbl:` and `fmt:` against an existing
`docs/tables/`/`docs/formats/` file, `struct:` against `re/types/`), a malformed or duplicated
`re/symbols.csv` row, an `[L]` in a spec outside *Open questions*, front-matter `tags:` counts that
disagree with the body, or a relative link (file or `#heading`) that doesn't resolve. Heuristics,
such as a `[C]` line with no anchor or a table row whose `Tag` cell is empty, are **warnings**: they
print and never fail. The **full tier** (`--full`) also reruns the parsers' `survey` commands against
`workspace/` and compares their summary counts with baselines in `tools/gate/baselines/`. When the
workspace is absent it reports `SKIPPED` and doesn't fail, unless `--require-workspace` is given.
The gate runs from a Claude Code PreToolUse hook on `git commit` when the commit stages anything
under `docs/` or `re/`, and a red fast tier denies the commit. The architect owns the rule list, in
`evidence-rules.md` § Mechanical checks. The archivist owns the code, under `tools/`.

## Consequences

### Positive
- The review stops sampling anchors and reads for substance: honest tags, reimplementability,
  sources policy.
- A renamed symbol in `re/symbols.csv` can't silently orphan a spec. The commit that renames it is
  denied until the references follow.
- A parser change that drops or misreads files shows up as a count diff in the full tier.

### Negative
- **A green gate looks like more than it is.** It proves anchors resolve, not that they're right, and
  says nothing about untagged claims. The review stays mandatory for every promotion, and the gate
  output never stands in for a verdict.
- **The hook can block a commit mid-work.** A lane that renames a symbol has to fix every reference
  in the same commit. This is intended, but it costs a session some friction.
- **Baselines need maintenance.** A deliberate parser change that alters a count also updates the
  baseline in the same commit, with the reason in the commit message.
- The full tier depends on one machine's `workspace/`. It's a local regression check, not CI.

### Neutral
- Baselines hold derived counts only (files read, records, blocks, errors), never strings, values or
  bytes from game files. They're of the same kind as the sizes in `docs/inventory.md`.
- The hook covers agent commits only. A human committing from a shell can run the gate by hand.

## Alternatives considered

**Detect untagged claims heuristically and fail on them.** Lost because any rule for "this sentence
is a claim" has false positives in prose, tables and pseudocode, and a gate people learn to work
around is worse than none. The heuristics stay as warnings.

**A git `pre-commit` hook under a checked-in `.githooks/`.** Lost because it is opt-in per clone
(`core.hooksPath`) and silently absent in a fresh worktree. The Claude hook is wired in the tracked
`.claude/settings.json`, like the other enforcement hooks, so it's present in every checkout where
agents work.

**Keep enforcement in review only.** Lost because the review already samples what a script checks
exhaustively in under a second, and an unattended driver, if one is ever adopted, needs a gate
anyway.

**Put survey baselines in `workspace/`.** Lost because they'd then be untracked, so a baseline
change would leave no history and no commit message explaining it. Counts aren't game data.
