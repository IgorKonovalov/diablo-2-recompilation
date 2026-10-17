# ADR-0016 — Pipelined simulation phases: a phase's table and static work may start once the previous phase's run is accepted

> **Status:** accepted (owner, 2026-10-16)
> **Date:** 2026-10-16
> **Amends:** [ADR-0014](0014-scope-game-simulation.md) (the sentence "A later phase's plan is written only once the earlier phase's spec is reviewed")
> **Related plan(s):** [0037-combat-formulas](../plans/done/0037-combat-formulas.md) (phase 1), [0041-stats-and-states](../plans/done/0041-stats-and-states.md) (phase 2)

## Context

[ADR-0014](0014-scope-game-simulation.md) opens game simulation in five phases and gates each one: "A later phase's
plan is written only once the earlier phase's spec is reviewed." The gate keeps a phase from building on a boundary
the earlier phase has not settled. Each phase oracles the next one's inputs, and the spec review is where those
oracles are fixed.

On 2026-10-16 plan 0037 (phase 1, combat formulas) has its Phase 0 table docs, its Phase 1/1b static finding and its
Phase 2 run accepted (run:2026-10-16-combat, 15 358 events, 0 mismatches). Its spec (Phase 3) and a one-slot resume of
two Phase 2 shortfalls remain. The boundary phase 2 needs is already in the accepted finding: combat/0001's *Boundary
recommendation* lists every stat a combat event reads as a value oracle (stats 0, 2, 12, 16–25, 31–46 and more), and
the Phase 2 review kept that list. The spec will restate it; it will not move it.

Meanwhile the queue is thin. Plan 0038's static batches are nearly drained (S2c in flight; S3b, S1a, S1e and a
possible S1f left), and the archivist has no table phase queued at all. Phase 2 (stats and states) has the largest
table and static load of any phase so far (ItemStatCost's `op` columns, States, the passive and aura columns of Skills,
the stat-list code), and none of it depends on how the combat spec is worded.

## Decision

A simulation phase's plan may be written and approved once the **previous phase's Phase 2 run is accepted**. Its
table phase (P0) and its static phases (P1 and the community cross-check P1b) may then run at once. Its harness phase
(P2) starts only after the **previous phase's spec is reviewed**, because the P2 boundary (which inputs stay value
oracles and which are now modelled) is ruled against that spec. If the previous spec's review changes a boundary the
new plan's P1 relied on, the architect re-rules the new plan's P2 boundary at its P1 review, or in a dated amendment
to the plan if P1 was already reviewed. Pipelining reaches **one phase ahead** only: phase *n + 2*'s plan waits for
phase *n + 1*'s P2 to be accepted. ADR-0014's other rules (the phase list, the per-event evidence, the chaining
floors, the reordering of phases 3–5 by plan) are unchanged.

## Consequences

### Positive

- The archivist and the static reverser lanes get phase 2 work now, while 0037·P3 is written and reviewed.
- The kept combat logs are ready as phase 2's test set (ADR-0014 § Evidence) as soon as phase 2's model exists.
- The harness gate, the expensive part, stays where ADR-0014 put it.

### Negative

- **Rework risk.** If 0037·P3's review moves an input across the boundary (a stat the spec decides is computed in
  combat rather than read), phase 2's P1 may have read code it no longer needs or missed code it does. The re-ruling
  at its P1 review bounds the damage to one amendment, but static work can be wasted.
- **Two open simulation plans at once.** Reviews of 0037·P3 and 0041·P1 may land together, and two specs (combat and
  stats) will cite one another before either is reviewed. Cross-references between unreviewed specs must stay
  `[I]` until both are reviewed.
- **The research map's simulation band grows faster than it closes.** A reader sees two `not started` or
  `findings in progress` rows where ADR-0014 meant to show one.

### Neutral

- The gate is still per phase. Pipelining does not let a later phase oracle what the previous phase's spec has not
  stated.
- Plans outside the five phases (for example those under ADR-0017, if accepted) are not affected.

## Alternatives considered

**Keep ADR-0014's gate as written.** It lost because it leaves the archivist and one static lane idle for the length
of 0037·P3 and its review, while the input boundary phase 2 needs has already been accepted with the P2 run.

**Pipeline the harness phase as well.** It lost because a harness run of phase 2 against a combat boundary the spec
has not fixed could produce `[C]` claims on the wrong side of it; the runs are the expensive, non-repeatable part
(ADR-0014 § Negative, "No session is repeatable").

**Pipeline two phases ahead.** It lost because phase 3 (skills and missiles) takes phase 2's aggregation as its input,
and that model does not exist before phase 2's run.
