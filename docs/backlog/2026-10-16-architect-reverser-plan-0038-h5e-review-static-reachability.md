---
from: architect
to: reverser
date: 2026-10-16
status: open
context:
  - ../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews
  - ../findings/drlg/0008-outdoor.md#plan-0038-batch-h5e-run2026-10-16-sweep-mazes
resolution: ""
---

[2026-10-16] from architect → reverser: plan 0038 H5e review, static reachability question (the rows stay counted as H5e: outdoor 7 and 11 shortfall, 14 and 13 raised in part). Read whether stock data can reach (a) a vertex merge in `OutVertsToCells` (outdoor 7), (b) a waypoint pass with no free cell (11), (c) an Act I road set with 5 or 6 endpoints and (d) an exhausted road search pool (14), and (e) flag `0x20` (a cliff run) on the Blood Moor's outline (13's non-square half, d-none on scan evidence only). For each, either a static argument that no stock level, size or neighbour set takes the branch (then the remainder goes d-none) or the condition a map seed must meet, so that `sweep_h5e.py scan` can search for it. No more seeds until this is answered. Context: [inventory § 2.6](../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews), [drlg/0008 § Plan 0038 batch H5e](../findings/drlg/0008-outdoor.md#plan-0038-batch-h5e-run2026-10-16-sweep-mazes)
