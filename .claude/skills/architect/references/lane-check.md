# Lane check (Tier B, ADR-0023)

A diff-scoped check of a non-spec lane, run on Sonnet. It replaces the full Mode 3 review for the lane kinds below
and is defined by [ADR-0023](../../../../docs/adrs/0023-review-tiers-and-gate-first-fixes.md) (accepted; settled by
[plan 0053](../../../../docs/plans/done/0053-review-tiers-and-gate-checks.md) Phase 4), amended by
[ADR-0024](../../../../docs/adrs/0024-lane-check-touched-documents-and-routing.md) (accepted by the owner 2026-10-30:
the two bounded passes below). This page is enough to run one:
the caller gives a worktree path and a lane branch, nothing else.

## Which lanes

| Lane kind (ledger `Kind`) | Tier |
|---|---|
| `reverser-static`, `reverser-harness`, `archivist`, `wiki` | B, this check |
| `spec-writer`, any change to `docs/adrs/` or `evidence-rules.md`, any lane this check escalates, the audit sample | A, the full review (`SKILL.md` Mode 3) |

The orchestrator picks the tier; a check that finds the lane is Tier A by this table stops and escalates.

## Inputs, and the scope limit

Read only these:

1. The diff: `git -C <wt> diff --stat main...<lane>`, then `git -C <wt> diff main...<lane> -- <path>` file by file.
2. The lane's review request: the newest dated entry of the plan's *Implementation log* (it is in the diff).
3. `.claude/skills/<lane skill>/references/review-fixes.md`.
4. For the three anchor spot-checks only: `grep` of `re/symbols.csv`, or the cited lines of the cited finding or
   table doc (a range read, never the whole file).

5. For the two bounded passes only (§ The checks, 7 and 8): `grep -n` over each touched document and `grep -rn` over
   `docs/findings/` for the changed lines' subjects, then the paragraph around each hit (a range read).

Nothing else: no other findings, specs, plans or the research map. Run the gate in the worktree,
`python3 -I tools/gate.py --no-warnings | tail`. Neither tier counts or repairs what the gate checks (E1–E16, W1–W7:
anchors, tag counts, the research map, the plans index, `Total` rows, table cells); a red gate is a lane fix, named
as such.

## The checks

1. **Corroboration.** Every `[C]` the diff adds or raises (a `+` line holding `[C]`, or a `[I]`/`[L]` → `[C]` change)
   names its second source in the statement: a `run:` id, an emulation, a table cell, a second function. "The
   decompile says so" is `[I]` (`evidence-rules.md` § Tags). Read the statement's own wording, not only the tag.
2. **Three anchors.** Pick three `fn:`/`data:`/`0x00XXXXXX` anchors from the diff, ideally on raised statements, and
   check that the named symbol is what the sentence says it is (its `re/symbols.csv` row, signature and evidence
   column, or the finding line it cites). The gate already proves they resolve; this check is about meaning.
3. **The lane's `review-fixes.md`.** Go through every rule and look for its fault in the diff.
4. **The request answered.** Each item the review request (or the plan phase's *Done when*) lists is answered in the
   diff, or explicitly routed (a backlog entry, a later phase).
5. **Every disagreement routed.** When the diff corrects, narrows or contradicts a statement in a document the lane
   does not own (another finding, a table doc, a spec), the diff holds a backlog entry to that document's owner. A
   route named in the text ("routed to …", "left to the spec-writer") with no entry, or a finding written around
   in silence, is an omission fix: file the entry (`python3 -I tools/backlog.py new`). Both trial audits found one
   (plan 0053 Phase 4).
6. **No silent nits.** Every problem you see is either a fix or a listed item in the verdict, never noted and left.

7. **Touched-document pass** (ADR-0024). For each file the diff changes under `docs/findings/`, `docs/tables/`,
   `docs/formats/` or `docs/wiki/`, list the subjects of the changed lines: symbol names, addresses, field offsets, row
   or state numbers. `grep -n` the whole file for each subject and read the paragraph around each hit. A sentence the
   diff makes stale is a fix (stale cross-reference). Plan logs, the ledger and backlog files are exempt.
8. **Touched-findings pass** (ADR-0024). For the same subjects, `grep -rn` over `docs/findings/` and read the hit
   paragraphs in findings the diff does not change. A statement the diff contradicts or narrows needs a correction in
   the diff or a backlog entry to its owner (check 5); a missing one is an omission fix, and the check files the entry.

Each pass reads at most **20 subjects**: take the subjects of raised `[C]` statements first. A lane with more subjects
than that escalates to Tier A. The next two audits measure the amended check: the tokens of each check and the fixes it
missed, by category.

## Escalate (Tier A takes over)

Stop and return `escalate` with the reason on any of these:

- a reject-grade problem: a `[C]` with no second source that the lane builds on, a wrong address under a claim, text
  that reads like transliterated third-party code, a `src:` id not in `docs/sources.md`;
- a raised tag whose evidence the check cannot follow inside its scope;
- more than 20 subjects for the passes of checks 7 and 8;
- a symbol clash: a `re/symbols.csv` row renamed, or one name on two addresses, or two names on one;
- any change under `docs/specs/`, `docs/adrs/` or `evidence-rules.md`;
- a lane that is Tier A by the table above.

One check may cover up to three lanes whose diffs touch disjoint files; give each its own verdict.

## Verdict format

In conversation, not as a file:

```
lane/<name> (Tier B check, <plan> <phase>): accept | accept with fixes (n) | escalate (<reason>)
Fixes (n): <category> k, ... (<one clause per fix>)
Checked: [C] added or raised n; anchors <a>, <b>, <c>; review-fixes rules 1..m; request items 1..k; disagreements routed d; passes 7/8 subjects s, hits read h
Gate: GREEN|RED, errors e, warnings w
```

Categories are those of [`docs/plans/metrics.md`](../../../../docs/plans/metrics.md) § Fix categories. Write a fix into
the document it changes when it is small and inside the lane's files; otherwise list it for the lane. The orchestrator
appends the ledger row with Kind `architect-check` (`python3 -I tools/metrics.py append`).
