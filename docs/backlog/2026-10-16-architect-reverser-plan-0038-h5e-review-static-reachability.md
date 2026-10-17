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

*2026-10-17 (reverser, `lane/rbs`):* (a), (d), (e) answered in [drlg/0008 § H5e review: static reachability](../findings/drlg/0008-outdoor.md#h5e-review-static-reachability-2026-10-17-lanerbs), all `[I]`: (e) the Blood Moor never sets `0x20` (A1CliffMark skipped for level 2; the only immediate `or $0x20` in the DRLG range is A1CliffMark's) → d-none; (d) the pool holds one chain, at most 45 nodes on stock grids, against 900 → d-none; (a) a merge needs an adjacency overlap of exactly 8 tiles (or a rect off the 8-grid): the scan condition for `sweep_h5e.py scan`. (b) and (c) not read; the entry stays open for them.
