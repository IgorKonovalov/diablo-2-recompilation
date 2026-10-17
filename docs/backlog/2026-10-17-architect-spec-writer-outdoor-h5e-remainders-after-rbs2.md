---
from: architect
to: spec-writer
date: 2026-10-17
status: open
context:
  - ../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews
  - ../findings/drlg/0008-outdoor.md#h5e-reachability-second-pass-2026-10-17-lanerbs2
resolution: ""
---

drlg/outdoor wording after the `lane/rbs2` review (inventory § 2.6, the `lane/rbs2` block). No tag changes; the rows stay `[I]`, and the spec should now say why there is no stock case. L693 (row 13): the swapped cliff-cave scan's non-square half has no stock case because the Blood Moor's `0x20` stays clear: no writer of `O+0x00` between the cliff-mark skip and the test at 0x0068023B (drlg/0008 (e), (e′)). L866 (row 14): roads with 5 or 6 endpoints have no stock case, at most 4 (drlg/0008 (c)), and neither does an exhausted pool, at most 45 nodes against 900 ((d)). The failed search keeps its raise. L535 (row 11) and L285 (row 7) are unchanged: shortfalls with a scan condition. Do this in the next drlg/outdoor Phase 3 pass; not blocking.
