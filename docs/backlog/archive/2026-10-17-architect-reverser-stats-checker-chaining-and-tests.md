---
from: architect
to: reverser
date: 2026-10-17
status: done
context:
  - ../../plans/done/0041-stats-and-states.md#implementation-log
  - ../../findings/stats/experiments.md#run2026-10-17-stats
resolution: "Done 2026-10-20 (reverser, lane/p47r, plan 0047 Phase 1): (a) aura chained pairs reported (746, keyed by the caster unit; 115 breaks, 4 drawing runs with no next run); (b) the aura grid's gaps keyed per log (all 50); (c) tools/test_stats.py 15 tests (wells, recharge shrines, the negative stat-74 tick and the floor, the set blocks, two written logs for the per-log reset, gaps and chaining); (d) the full Trang-Oul's 180 lists predicted, no block left unchecked (values << ValShift, the state block by func 24 with the compiled param), so the remainder is gone; (e) oracle-player prints a consistency count. Re-check over the 18 logs: 0 mismatches, [stats experiments](../../findings/stats/experiments.md#run2026-10-17-stats)."
---

Plan 0041 P2 review (2026-10-17), tool items for `tools/stats.py`, no game run needed (the 18 kept logs of run:2026-10-17-stats are the test set): (a) report the ADR-0014 chained pairs of the aura kind (the next AU0 of the same caster entering on the previous AU1's exit; the review counted 746 with a scratch pass, the record cites it) beside the 865 exit-asserted runs; (b) key the aura grid's gaps per log (the report shows negative cross-log gaps that change with the check order); (c) unit tests for the well and recharge-shrine predictions, the negative stat-74 tick and the per-log reset of open events (`test_stats.py` has none); (d) predict the stat blocks of a full set whose blocks include `state` or `oskill` (the 180 full Trang-Oul's lists) and check those, leaving only the two property blocks unchecked; (e) `oracle-player`: say "consistent" rather than "replaceable", or establish the no-linked-child precondition from the log or the recipe and its item requirements, not from the compared value. Re-run the check over the 18 logs after the change and update the record's counts.

*2026-10-20 (architect, `lane/plans45`):* proposed home: plan 0047 Phase 1 (plan proposed, awaiting the owner).
