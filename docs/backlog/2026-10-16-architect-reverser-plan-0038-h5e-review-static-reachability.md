---
from: architect
to: reverser
date: 2026-10-16
status: done
context:
  - ../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews
  - ../findings/drlg/0008-outdoor.md#plan-0038-batch-h5e-run2026-10-16-sweep-mazes
resolution: "Second pass 2026-10-17 (lane/rbs2), all [I]: (e′) no writer of O+0x00 in the callee closure (tools/callee_writes.py), Blood Moor 0x20 d-none; (c) at most 4 road endpoints on every stock level, 5 and 6 d-none; (b) no static bound, scan condition printed (fewest free interior cells, minimum 12 of 64 over 52 200 windows). [drlg/0008 § H5e reachability, second pass](../findings/drlg/0008-outdoor.md#h5e-reachability-second-pass-2026-10-17-lanerbs2)"
---

[2026-10-16] from architect → reverser: plan 0038 H5e review, static reachability question (the rows stay counted as H5e: outdoor 7 and 11 shortfall, 14 and 13 raised in part). Read whether stock data can reach (a) a vertex merge in `OutVertsToCells` (outdoor 7), (b) a waypoint pass with no free cell (11), (c) an Act I road set with 5 or 6 endpoints and (d) an exhausted road search pool (14), and (e) flag `0x20` (a cliff run) on the Blood Moor's outline (13's non-square half, d-none on scan evidence only). For each, either a static argument that no stock level, size or neighbour set takes the branch (then the remainder goes d-none) or the condition a map seed must meet, so that `sweep_h5e.py scan` can search for it. No more seeds until this is answered. Context: [inventory § 2.6](../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews), [drlg/0008 § Plan 0038 batch H5e](../findings/drlg/0008-outdoor.md#plan-0038-batch-h5e-run2026-10-16-sweep-mazes)

*2026-10-17 (reverser, `lane/rbs`):* (a), (d), (e) answered in [drlg/0008 § H5e review: static reachability](../findings/drlg/0008-outdoor.md#h5e-review-static-reachability-2026-10-17-lanerbs), all `[I]`: (e) the Blood Moor never sets `0x20` (A1CliffMark skipped for level 2; the only immediate `or $0x20` in the DRLG range is A1CliffMark's) → d-none; (d) the pool holds one chain, at most 45 nodes on stock grids, against 900 → d-none; (a) a merge needs an adjacency overlap of exactly 8 tiles (or a rect off the 8-grid): the scan condition for `sweep_h5e.py scan`. (b) and (c) not read; the entry stays open for them.

*2026-10-17 (architect, `lane/rbs` review):* (a), (d), (e) accepted at `[I]`. (e) corrected in the finding: the pattern `or[lb]?` missed two word ORs (`orw $0x20,(%eax)` at 0x006689BC and 0x00668FC8, cube parsers, not on `O`), so three bare-register ORs in the range, one on `O`; displacement and register-source ORs are outside the pattern. Rule 9 is met (the five unfollowed callees are named and counted), but the d-none rests on them: still open here, with (b) and (c), **(e′)** follow `OutPresetPlace`, `GridCellOp`, `GridSegmentOp`, `OutCornerFlood` and `BorderSubApplyType` (or list every writer of `O+0x00`) to close the remaining path.
