---
from: architect
to: reverser
date: 2026-10-16
status: open
context:
  - ../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews
resolution: ""
---

[2026-10-16] from architect → reverser: plan 0038 Phase 2 leftover pieces from S1b (rows stay counted as S1b, raised in part): data-calc 19, a hover marker line in `calc.gdb` so that "hover evaluates nothing" can be checked (client caller 0x00486370); rng-seeds 11, a caller `ra` on `SUNITPRE` in `seed-tree.gdb`, with a character load and a re-seed in the session. Neither has an open harness batch; take them with the next session that loads either logger. data/README 1 and data-excel 30 went to H3b ([inventory § 5](../plans/0038-inventory/README.md#harness-batches)). Context: [inventory § 2.6](../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews)

*2026-10-17 (reverser, `lane/rbs` static sweep):* skipped: needs harness; rides on the next plan 0038 harness session that loads calc.gdb or seed-tree.gdb (no open batch).
