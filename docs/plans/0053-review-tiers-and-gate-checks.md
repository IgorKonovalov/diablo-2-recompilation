# 0053 — Review tiers and gate checks for the mechanical fix categories

> **Status:** approved (owner, 2026-10-27; ADR-0023 accepted as a trial)
> **Created:** 2026-10-27
> **Owner skill(s):** archivist (phases 0–1), architect (phases 2 and 4), human (phase 3)
> **Related ADRs:** [0023-review-tiers-and-gate-first-fixes](../adrs/0023-review-tiers-and-gate-first-fixes.md) (accepted, trial), [0006-docs-gate](../adrs/0006-docs-gate.md)

## TL;DR

This plan answers how to cut the cost of reviews (30.9% of agent tokens, 172 runs at a 150k mean) without weakening
what reaches `docs/specs/`. When it is done:

- `tools/gate.py` has four new checks for the mechanical fix categories: miscount, stale cross-reference and
  bookkeeping splice.
- The architect skill has a Tier B lane check beside the full review.
- The ledger has ten Tier B checks and two audits, measured against the full reviews they replaced.
- ADR-0023 is accepted or withdrawn on those numbers.

## Context

The evidence is in ADR-0023 § Context. Of 708 categorised fixes, 134 are mechanical (miscount 53, stale
cross-reference 50, wrong anchor 27, bookkeeping splice 4). The new checks below target the copies that drift:

- **E15 (miscount, stale cross-reference):** the research map repeats each spec's status, tag counts and `updated:`
  date.
- **E16 (stale cross-reference):** the plans index repeats each plan's `Status:`, and each index states a next free
  number.
- **W7 (miscount):** batch and recount tables carry totals.
- **E14 (bookkeeping splice):** merges splice table rows.

Most wrong-anchor fixes are semantic: a real symbol that is not what the sentence claims. E1 already checks the rest,
so this plan adds nothing for that category.

Phases 0 and 1 do not depend on ADR-0023 being accepted, because the checks pay for themselves under either review
model. Phases 2–4 start only once the owner accepts the ADR as proposed (status `accepted (trial)`).

## Phases

### Phase 0 — Measure the candidate checks on the current tree
- **Owner skill:** archivist
- **What:** prototype E14–E16 and W7 as a dry run (a `--candidate` flag or a scratch module under `tools/gate/`),
  list every hit on `main`, and classify each hit as a true or a false positive.
- **Outputs:** a dated entry in this plan's Implementation log with per-check hit counts, the false positives and
  their causes, and the value sets found (spec `status:` values against the map's status words).
- **Done when:** each check has a hit count and a false-positive count. Each false positive has either a rule change
  proposed below or a reason the check should be dropped.

### Phase 1 — Implement the checks
- **Owner skill:** archivist
- **What:** add the rules below to `tools/gate.py`, with fixtures under `tools/gate/fixtures/` and tests beside the
  existing ones.
- **Rules** (the architect copies them into `references/evidence-rules.md` § Mechanical checks in the Phase 1
  review commit; until then they are this text):

  | # | Rule | Applies to |
  |---|---|---|
  | E14 | Outside code blocks, every row of a markdown table has as many cells as its header row. Escaped `\|` and pipes inside code spans don't split cells. | every tracked `.md` except `tools/gate/fixtures/` |
  | E15 | For each spec linked from a research-map row's Status cell: the status words before ` · ` (bold stripped) equal the spec's `status:` under the mapping Phase 0 found. A `C n / I n / L n` group after the link and before the next link equals the spec's `tags:`. An `updated YYYY-MM-DD` after the link equals `updated:`. | `docs/specs/README.md` |
  | E16 | In `docs/plans/README.md`, each row's Status cell starts with the linked plan's `Status:` value (first word). The link points under `done/` if and only if that value is `done` or `abandoned`. In `docs/plans/README.md` and `docs/adrs/README.md`, the "Next free number" is greater than every number in use in that directory, `done/` included. | those two indexes |

  | # | Heuristic (warning) | Applies to |
  |---|---|---|
  | W7 | A table row whose first cell is `Total` (bold allowed): each numeric cell (spaces, narrow spaces and commas as separators) equals the sum of the numeric cells above it in that column, back to the header or the previous `Total` row. | specs, findings, plans |

- **Outputs:** `tools/gate.py` with E14–E16 and W7, fixtures, tests, and the module docstring updated. `main` is green
  under the new errors: the lane fixes the hits in files it owns, and files the rest as backlog entries to the owning
  lane (architect: the research map and the indexes). Until those land, their checks stay at warning level, with the
  reason in the commit message.
- **Done when:** `python3 -I tools/gate.py` passes on the lane tip. Each new rule has a fixture that fails and one that
  passes. The hit counts on the tip match Phase 0's counts minus the fixes, and the log shows the arithmetic.

### Phase 2 — Tier B in the skills and the ledger
- **Owner skill:** architect
- **What:** once ADR-0023 is `accepted (trial)`, fix the Phase 1 backlog entries addressed to the architect, raise any
  warning-level E14–E16 back to error, and write the lane check.
- **Outputs:**
  - `references/lane-check.md`: the Tier B steps from ADR-0023, the diff command, the escalation list, a scope limit
    (no reads outside the diff except the anchors spot-checked and `review-fixes.md`), and the verdict format.
  - `SKILL.md` Mode 3: which tier applies to which lane kind, the promotion re-check of imported `[C]`, and the audit
    rule.
  - `docs/plans/metrics.md`: a new Kind `architect-check`; an audit row is an `architect-review` whose Fixes cell
    begins `audit of <lane>:`.
  - The orchestrator's lane-model memory note, pointed at the tiers.
- **Done when:** a Tier B check can be started from the skill alone, with no other instructions, and the gate is green
  with E14–E16 at error.

### Phase 3 — Trial: ten Tier B checks and two audits
- **Owner skill:** human (the orchestrator, with the owner's go)
- **What:** route the next ten non-spec lanes through Tier B on Sonnet, batching where the diffs are disjoint, and give
  the fifth and tenth a Tier A audit as well.
- **Outputs:** ledger rows for every check and audit.
- **Done when:** ten `architect-check` rows and two audit rows exist, each with tokens, verdict and fixes by category.

### Phase 4 — Evaluate and settle ADR-0023
- **Owner skill:** architect
- **What:** compare the trial with the full reviews of the same lane kinds.
- **Outputs:** an evaluation entry in this log, ADR-0023's status set to `accepted` or `superseded`/withdrawn with the
  reason, and the plan closed.
- **Done when:** the entry gives:
  - mean tokens per Tier B check, against the 150k full-review mean for the same kinds (`metrics.py summary --by kind`);
  - the reject-grade problems the audits found that the checks missed;
  - the fixes the next spec promotions made to imported `[C]` statements.

  The decision follows the ADR's audit rule.

## Open questions

- Does E15 need its own format for map rows that link several specs, or does Phase 0 show a shape every row already
  follows?
- Should the Tier A promotion re-check use a gate helper, such as a list of a finding's statements changed since a
  commit, rather than `git log -L` by hand? This is deferred until Phase 4 shows what the re-check costs.
- Wrong anchor (27 fixes) gets no check here. A warning for a bare `0x00XXXXXX` in a spec with no symbol row would
  find unnamed addresses, not wrong ones. It is left out unless Phase 0 shows otherwise.

## Implementation log

_(lanes append dated entries as phases land)_
