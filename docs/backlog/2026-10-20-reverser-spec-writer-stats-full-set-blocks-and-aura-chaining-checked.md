---
from: reverser
to: spec-writer
date: 2026-10-20
status: open
context:
  - ../findings/stats/0001-aggregate.md
  - ../findings/stats/experiments.md#run2026-10-17-stats
  - ../plans/0047-simulation-shortfalls.md#implementation-log
resolution: ""
---

Plan 0047 Phase 1 (lane/p47r), for the stats specs: the re-check of run:2026-10-17-stats with the new tools/stats.py (0 mismatches) predicts the 180 full Trang-Oul's wearer lists too, so the *unchecked remainder* is gone and [stats/0001](../findings/stats/0001-aggregate.md) raises the full-block statement to [C] (values stored << ValShift: mana 100 -> 25 600; the state block, func 24, writes stat 98 with the compiled param monsterset 176 and value 1; review pending). Places that repeat the old remainder: docs/specs/stats/README.md (the boundary table's *unchecked remainder* row), docs/specs/stats/aggregate.md J4 and its [L] open question on the full Trang-Oul's blocks, docs/wiki/stats-and-states.md (the 180 lists). The 746 chained aura pairs that README and states.md cite from the review's scratch pass are now a checker count (aura_chained_pairs 746, keyed by the caster unit; 115 breaks; 4 drawing runs with no next run in their log): the citation can name tools/stats.py. Take after the architect's review of plan 0047 Phase 1.
