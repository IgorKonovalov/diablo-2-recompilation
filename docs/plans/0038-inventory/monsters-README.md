# Plan 0038 inventory: monsters/README

- **Spec:** [monsters/README.md](../../specs/monsters/README.md), read at `main` `e1c807a` (last change to the spec: `02aa5b0`).
- **Front matter `I`:** 1; the *count* column sums to 1.
- **Finding:** [monsters/0002](../../findings/monsters/0002-room-population.md) (sections given as `§n`; other subsystems' findings named in full).
- **Cluster:** 0c (monsters, hirelings, player). Classes, tiers and batches as in [plan 0038](../0038-inferred-claims-sweep.md#classes).
- Guard rows marked (a-logs) with "0 → d-none" are re-read first: a guard the later logs never took is reclassified d-none by the batch, not raised.

| # | Spec section | Claim | Finding anchor | Class | Route | Tier | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | [Data flow](../../specs/monsters/README.md#data-flow) | Each server monster is seeded by one game-seed draw | §5, SUnitCreate 0x00555230 | a-logs | MU lines of run:2026-10-13-mon-spawn (unit seed = 2 steps after `Init(step(game).low)` on 914 of 916 creations); addendum | T1 | S3a | 1 |

**Totals by class:** a-logs 1 (sum 1).
