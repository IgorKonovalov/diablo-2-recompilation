---
from: spec-writer
to: reverser
date: 2026-11-04
status: done
context:
  - ../../findings/items/0014-ground-items.md
  - ../../findings/items/0016-harness-inventory-run2.md
  - ../../plans/done/0060-item-use-inventory.md
resolution: "Plan 0063 Phase 2b (lane/n63s): tools/inventory_check.py spots on the three kept logs (118 searches, 0 mismatches; 90 in 6 chain spots, 28 drops at 24 positions). Raised live [C]: the offset start (30 spots), the item bit (8), the walk mask 0x801 (6), the ring order through ring 3; raised in part: the walk tested at all (one chain spot); fixedbase, the start pos, rings 4+ not raised. Spec § J routed to plan 0063 Phase 3. [items/0016](../../findings/items/0016-harness-inventory-run2.md#plan-0063-phase-2b-the-ground-searchs-live-raise-2026-11-10-lanen63s)"
---

From plan 0060 Phase 3 (`lane/s60`). Not blocking. The `lane/s60` review settled the wording items against the instructions and logs and wrote them as dated corrections in items/0013 to items/0016; one item is left.

The `lane/p60b` check allows a reverser raise of the live start offset, item bit, walk mask and ring order through ring 3: not done. The spec's rows ([items/inventory § J](../../specs/items/inventory.md#j-the-ground-drops-cell)) carry the emulated `[C]` with the live counts beside them, and rise with the finding. Take the spots from the logs, not the check's "four": 90 of the 118 searches are a player's chains at six spots, 28 are `DropCreateItem` drops at 24 positions.

**2026-11-04, `lane/r70` (reverser): left open.** The raise needs no game, but it is a data job this lane did not do: the live separation counts per statement (start offset when the room holds the cell, item bit, walk mask, ring order through ring 3) and the per-spot independence tally (90 of 118 searches in six chain spots, 28 `DropCreateItem` drops at 24 positions) have to be recomputed from the kept `check-*.txt` and the three logs with `tools/inventory_check.py` controls, then written as a finding with the second source named. Not started; the spec's rows keep the emulated `[C]` with the live counts beside them.

**2026-11-04, plan 0060 closed (`lane/w60` review).** Optional and no longer tied to that plan, which closed without it: a data job for any later static lane. The spec's rows stand as they are until then.
