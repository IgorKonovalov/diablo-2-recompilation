# ADR-0024 — The lane check reads the touched documents and the findings they touch (amends 0023)

> **Status:** accepted (owner, 2026-10-30); proposed by the architect 2026-10-30 (plan 0053 Phase 4)
> **Date:** 2026-10-30
> **Related plan(s):** [0053-review-tiers-and-gate-checks](../plans/done/0053-review-tiers-and-gate-checks.md)

## Context

Plan 0053 Phase 4 evaluated the ADR-0023 trial. Eleven Tier B checks cost 70 868 tokens each on average. Tier A
reviews of the same lane kinds cost 146 247 on average (128 runs). No audit found a reject-grade problem, so ADR-0023's
audit rule keeps Tier B.

The two audits (lane/h6gs, reverser-static; lane/a7b, archivist) found 9 fixes that their checks missed. The checks had
found 2 fixes in the same lanes. Seven of the nine misses come from the scope limit:

- 4 stale cross-references sat outside the diff hunks. Three were in a document the diff touched (MonAI.md § The AI
  table, § Batches and the open questions). One was in a finding the diff contradicted (quests/0001's arming bullet).
- 2 were disagreements with another finding that the lane "routed" or wrote around, with no backlog entry (ai/0001's
  state-row overcount; the corrected `anc` session and the J2 wording).
- 1 problem the check saw inside the diff and left as a nit (two missing register sites).

The other two misses (the altar operate's step-4 exit, the grant's step-0 call) needed the disassembly. That is beyond
Tier B by design. They wait for the promotion re-check.

ADR-0023 § Decision limits Tier B to "only `git diff main...<lane>`, the lane's review request, and that lane's
`review-fixes.md`". The first two kinds of miss cannot be caught inside that limit.

## Decision

A Tier B check keeps its four checks and adds two bounded passes and two rules.

**Touched-document pass.** For each file the diff changes under `docs/findings/`, `docs/tables/`, `docs/formats/` or
`docs/wiki/`, the check lists the subjects of the changed lines: symbol names, addresses, field offsets, and row or
state numbers. It runs `grep -n` over the whole file for each subject and reads the paragraph around each hit. A
sentence that the diff makes stale is a fix (stale cross-reference). Plan logs, the ledger and backlog files are exempt.

**Touched-findings pass.** For the same subjects, the check runs `grep -rn` over `docs/findings/` and reads the hit
paragraphs in findings the diff does not change. A statement the diff contradicts or narrows needs a correction or a
backlog entry.

**Routing rule.** If the diff corrects, narrows or contradicts a statement in a document the lane does not own, the
diff must hold a backlog entry addressed to that document's owner. A route with no entry is an omission fix, and the
check files the entry itself.

**No silent nits.** Every problem the check sees is either a fix or a listed item in the verdict.

Each pass reads at most 20 subjects. The check takes the subjects on raised `[C]` statements first. A lane with more
subjects than that escalates to Tier A.

The two rules need no reads outside ADR-0023's scope, so `lane-check.md` has carried them since plan 0053 Phase 4
was settled. The two passes entered `lane-check.md` on acceptance (2026-10-30, checks 7 and 8). ADR-0023's tiers, audit rate and
two-in-five rule are unchanged. The next two audits measure the amended check: the
tokens of each check, and the fixes that the check missed by category.

## Consequences

### Positive

- The amended check targets 7 of the 9 trial misses: the 4 stale cross-references, the 2 unrouted disagreements and
  the nit.
- Disagreements between findings get an owner while the lane that found them is fresh, not at a later promotion.

### Negative

- Each check costs more. The passes are greps plus range reads. The estimate is 15k to 25k tokens, so a check costs
  about 85k to 95k against 146k at Tier A. With the audits, a lane costs about 110k to 120k against 146k. The saving
  falls from about 36% to about 20%. The next two audits test this estimate.
- The scope limit becomes a judgement ("the subjects of the changed lines"), which a Sonnet check may apply unevenly.
- The two misses that needed the disassembly stay out of reach until a promotion or an audit.

### Neutral

- The evidence rules, the tiers and the gate checks are unchanged.

## Alternatives considered

**Keep ADR-0023's scope and accept the misses.** This lost because none of the misses is caught later as a matter of
course. A stale sentence in a findings or table doc reaches a spec only if a promotion imports it. An unrouted
disagreement has no owner at all.

**Return the non-spec lanes to Tier A.** This lost because the audit rule did not trigger: no miss was reject-grade.
Tier A also costs about twice as much per lane as the amended check is expected to.

**Read every touched document whole.** This lost on cost. Some touched documents are thousands of lines long (plan
0038's log, the large findings). Greps for the changed subjects find the same stale sentences for a fraction of the
reading.
