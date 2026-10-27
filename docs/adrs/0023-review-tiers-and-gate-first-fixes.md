# ADR-0023 — Review tiers: a full review at spec promotion, a diff-scoped check for the rest, and the gate takes the mechanical fixes

> **Status:** accepted (trial; owner, 2026-10-27; settled by plan 0053 Phase 4)
> **Date:** 2026-10-27
> **Related plan(s):** [0053-review-tiers-and-gate-checks](../plans/0053-review-tiers-and-gate-checks.md)

## Context

The owner's weekly token limit runs out in about a day while several lanes run. The [lane run ledger](../plans/metrics.md)
(`python3 -I tools/metrics.py summary`, 2026-10-27) records 362 runs and 83.6M agent tokens. Architect reviews are the
largest kind: 172 runs, 25.8M tokens (30.9%), 150k mean. That is more than reverser-static (22.3M) and close to twice
the deliverable lane, spec-writer (10.8M). Every lane gets the same full Mode 3 review, whatever it produced.

The verdicts show the reviews rarely change what lands. Of the review and lane verdicts in the ledger, 306 are
"accept with fixes", 10 are "accept", and none is a reject. The 708 fixes counted by category are mostly about
judgement: overclaim 218, omission 153, misread 119, under-claim 34. A smaller part, 134 (19%), is mechanical:
miscount 53, stale cross-reference 50, wrong anchor 27, bookkeeping splice 4. Many of those 134 are copies that have
drifted, which the gate (ADR-0006) can compare without judgement. Examples: the research map repeats each spec's
status, tag counts and `updated:` date; the plans index repeats each plan's `Status:`; batch tables carry totals.

A full review is what keeps an `[I]` reading from reaching the deliverable as `[C]`. That protection matters where a
claim enters `docs/specs/`. A findings, harness, archivist or wiki lane's output reaches a spec only through a
spec-writer lane, and that lane's review can re-check the claims it imports.

## Decision

Reviews come in two tiers, and the gate takes the fixes a script can see.

**Tier A, the full review**, is architect Mode 3 as it stands: a fresh agent on the strongest model. It applies to:

- every spec-writer lane;
- every change to an ADR or the evidence rules;
- every lane a Tier B check escalates;
- the audit sample below.

At a spec promotion, a Tier A review also re-checks every `[C]` the spec imports from a finding statement that was
written or raised since that finding's last Tier A review. It finds those statements with `git log -L` or the
ledger's tier column.

**Tier B, the lane check**, covers findings (reverser-static, reverser-harness), archivist and wiki lanes. It runs on
Sonnet and reads only `git diff main...<lane>`, the lane's review request, and that lane's `review-fixes.md`. It
checks:

1. every new or raised `[C]` names its corroboration in the statement;
2. three anchors from the diff, spot-checked;
3. the lane's `review-fixes.md` rules;
4. that the review request's items are all answered.

Its verdict is `accept`, `accept with fixes` or `escalate`. It escalates on any reject-grade problem, a raised tag it
cannot follow, a symbol clash, or a change to a spec. One check may cover up to three lanes whose diffs touch
disjoint files.

**Audit.** Every fifth Tier B lane also gets a Tier A review. The ledger logs both. If a Tier A audit finds a
reject-grade problem the check missed in two of any five audits of one lane kind, that kind goes back to Tier A until
the architect writes a new rule.

**Gate first.** New gate checks (plan 0053) take the mechanical categories. Neither tier counts or repairs what the
gate checks.

## Consequences

### Positive

- About 120 of the 172 reviews are of non-spec lanes. Each of those moves from a 150k full review to a Sonnet check
  confined to the diff. Plan 0053 measures the saving; the ADR assumes no figure.
- Review effort goes where the deliverable is made: the spec promotion re-checks the claims it imports.
- The research map, the plans index and batch totals stop drifting, because the gate compares each copy with its
  source on every commit.

### Negative

- **A finding's `[C]` is weaker between lanes.** After a Tier B check, a raised `[C]` has been read once, by a
  smaller model, without context outside the diff. A later reverser lane that builds on it can stack work on an
  overclaim, the most common fix category (218 of 708). The promotion re-check catches it before the deliverable, but
  only after other work may rest on it.
- Diff-scoped reading misses omissions (153 fixes, the second category), which by nature lie outside the diff. Some of
  them will now first surface at promotion, or not at all.
- The Tier A promotion review grows, because it re-checks imported `[C]` statements. Specs that import many raised
  findings cost more to promote.
- The process has more rules: a tier per lane kind, an audit count, an escalation list, a ledger tier.

### Neutral

- The evidence rules do not change. `[C]`, `[I]` and `[L]` keep their definitions and minimum evidence. What changes
  is who checks a tag, and when, before it reaches a spec.
- ADR-0006 stands: the gate proves anchors and copies, not claims.

## Alternatives considered

**Keep full reviews for every lane, on Sonnet.** This lost because overclaim and misread, 337 of the 708 fixes, need
the strongest reading. A uniform downgrade weakens the review of the deliverable too.

**Drop reviews of non-spec lanes entirely and rely on the promotion review.** This lost because findings and harness
lanes also write `re/symbols.csv` and the backlog, which other lanes use at once. A wrong symbol or a misrouted request
spreads before any promotion.

**Gate checks alone, with reviews unchanged.** This lost because the mechanical categories are only 19% of fixes. A
review still reads everything to find the rest, so its token cost barely falls.
