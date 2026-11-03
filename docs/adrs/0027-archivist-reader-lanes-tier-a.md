# ADR-0027 — Archivist reader lanes take the full review (amends 0023)

> **Status:** accepted (owner, 2026-11-03)
> **Date:** 2026-11-03
> **Related plan(s):** [0052-monster-ai](../plans/0052-monster-ai.md), [0053-review-tiers-and-gate-checks](../plans/done/0053-review-tiers-and-gate-checks.md)

## Context

ADR-0023 routes `archivist` lanes to the Tier B check. Its audit rule sends a lane kind back to Tier A only after two
reject-grade misses in five audits. On 2026-11-03 two archivist lanes linked findings' code readers into table docs and
both were audited. `lane/a63`'s audit found 7 fixes its check had missed (misread 4, omission 2, stale cross-reference
1). `lane/a64`'s found 6 (under-claim 3, misread 2, omission 1). The a64 check had been told to compare bullets with
their finding paragraphs, and it read about 24, yet the audit still found these. None was reject-grade, so the audit
rule did not fire. A table reader statement condenses a finding's scope (rows, slots, conditions), and later lanes cite
the table rather than the finding, so a misread there spreads.

## Decision

An **archivist reader lane** takes Tier A, the full review of the architect skill's Mode 3, on Opus, in place of the
Tier B check. It is an archivist lane whose diff adds or changes a statement in `docs/tables/` or `docs/formats/` taken
from a finding: a code reader, a column's meaning, or a tag.

Other archivist lanes keep Tier B: extraction, inventory, parsers and their tests (`RECIPE_BASES` rows included), and
table facts read from the data alone. A lane that does both is a reader lane. All other routing, and the audit rule,
stay as ADR-0023 and ADR-0024 state them. A reader lane does not count toward the every-fifth audit sample.

## Consequences

- A reader lane's review costs more than a check. On 2026-11-03 the a63 and a64 audits used 124 678 and 156 301 tokens,
  the checks 83 351 and 115 710. Dropping the check for these lanes offsets part of it.
- The misses of this kind should reach the review, not a later reader of the table.
- `references/lane-check.md`, the architect skill's § Tiers and the lane-models routing change with this ADR.
