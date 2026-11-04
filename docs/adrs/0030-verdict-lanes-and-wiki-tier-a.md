# ADR-0030 — Verdict lanes and wiki lanes take the full review (amends 0023)

> **Status:** accepted (owner, 2026-11-04)
> **Date:** 2026-11-04
> **Related plan(s):** [0057-quirks-catalogue](../plans/done/0057-quirks-catalogue.md)

## Context

ADR-0023's audit rule counts reject-grade misses only. The five Tier A audits of 2026-11-03 and 2026-11-04 found fixes
their Sonnet checks had passed: `lane/a63` 7, `lane/a64` 6, `lane/r52l` 6, `lane/r57b` 10, `lane/w57` 15. One was
reject-grade: `lane/r57b`'s row 11 held a reversed verdict with a wrong address under it, and the check accepted it.
`lane/w57`'s check recounted every number on the page and still passed wording that read emulation as seen in the game.
Both kinds turn on what a sentence claims, read against its source, and a diff-scoped check does not read that closely.

## Decision

Two more lane kinds take Tier A, the full review of the architect skill's Mode 3, on Opus, in place of the Tier B check:

- A **verdict lane**: one whose finding gives claim-by-claim verdicts against a source outside the code, such as a
  community cross-check or a list of community-known bugs.
- A **wiki lane**: one that writes or rewrites a page's statements under `docs/wiki/`. A lane that only moves a
  `based_on` date, or a link, stays Tier B.

Other routing stays as ADR-0023, ADR-0024 and ADR-0027 state it. These lanes do not count toward the every-fifth audit.
The audit rule itself is unchanged.

## Consequences

- These lanes cost more to review. On the 2026-11-03 and 2026-11-04 audits the Tier A runs were 124 678 to 260 691 tokens,
  against 74 507 to 115 710 for the checks; dropping the check offsets part of it.
- `references/lane-check.md`, the architect skill's § Tiers and the lane-models routing change with this ADR.
