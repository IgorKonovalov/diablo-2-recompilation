---
from: spec-writer
to: architect
date: 2026-10-27
status: done
context:
  - ../../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../../specs/objects/README.md
resolution: "Research-map objects row rewritten at the lane/s38o review: C 189 / I 62 / L 4 (the lane's 188 / 56 / 4 plus the review's fixes), updated 2026-10-27; wiki/objects and wiki/seed-to-world based_on 2026-10-27."
---

Plan 0038 Phase 3 (`lane/s38o`), the **objects** cluster (batches S4a, S4b, H5b, H6e2, all accepted): old and new
`{C, I, L}` for the research-map row and the wiki's `based_on` dates (gate W4).

| Spec | Old | New | `updated:` |
|---|---|---|---|
| [objects](../../specs/objects/README.md) | {C 139, I 72, L 5} | **{C 188, I 56, L 4}** | 2026-10-21 → 2026-10-27 |

- **Research map:** the objects row still gives the old counts; rewrite it whole (spec-writer rule 6).
- **Wiki (W4, done on this lane):** [wiki/objects](../../wiki/objects.md) is refreshed (gate order, groups, caps, the
  forced conversion, handler 1's sizes, `InitFn` 57/58 and the monster-creating handlers, the level-25 chest, the
  operates of 1, 26, 48 and 68, the chest tier and `ilvl`, traps and their level remap, the quest objects, the
  not-known list) and lists `objects/README.md 2026-10-27`; [wiki/seed-to-world](../../wiki/seed-to-world.md) needed the
  date only (no statement there changes).
- **Beyond the inventory rows:** § K's event-7 route `[C]` for classes 268 and 367 (items/quest-drops row qd 1's
  raise, restated here by rule 8), and § J3's tier and tier-as-`ilvl` `[C]` (the S2a tc 64 entry, its last part); the
  § J3 `[L]` on the cut is struck.
- **Not reflected, with the reason:** none of the cluster's accepted raises is left out. Kept `[I]` as the ledgers rule:
  H5b shortfalls rows 6 (windows inside an operate), 19 (well cap), 35 (582), 39 (class 397), 46 (trap types 8, 9), 49
  (bookshelves' quest test); S4b row 25 (shortfall, rewritten with the nine monster-creating `InitFn`s); row 20 and the
  `0x804` and `PreOperate` halves (d-none, restated as no stock case); row 5 (deferred); the d-none and d-sim rows; and
  the remainders each batch section names. items/quest-drops' H6e2 parts wait for H6e1 (that entry annotated, left open).
