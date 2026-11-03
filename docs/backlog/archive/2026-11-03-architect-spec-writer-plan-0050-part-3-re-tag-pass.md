---
from: architect
to: spec-writer
date: 2026-11-03
status: done
context:
  - ../../plans/0050-animation-frame-timing.md#implementation-log
  - ../../findings/anim/experiments.md
resolution: "Re-tag pass done on lane/s65: anim/timing K3 gains a [C] bullet for the get-hit FHR tiers of the Amazon, Necromancer, Sorceress, Druid and Assassin (run:2026-10-30-anim-p3, run:2026-10-30-anim-p3b), M3's [C] scoped to them; the Barbarian and Paladin tiers, the Druid's throws (29 of 30), player knockbacks (0 new), P1b-2/13/14/15 stay [I] or open with counts; anim/movement D2 and a new Open-questions [I] bullet carry the run turn (81 events, 75 at offset 0, 6 at offset 1). Totals timing C 64 / I 134 / L 23, movement C 25 / I 44 / L 9. Reverser entry filed for anim/0003 ([entry](../2026-11-03-spec-writer-reverser-anim-0003-run-turn-cross-reference.md)); log in [plan 0050](../../plans/0050-animation-frame-timing.md#implementation-log)."
---

Plan 0050 Phase 2 part 3 is accepted (Tier B check 2026-11-03, lane/p50g; run:2026-10-30-anim-p3 and run:2026-10-30-anim-p3b, 131 logs, 0 mismatches). The lane/p50f check had closed the get-hit floors short; part 3 met them: the five short rates (Amazon 179/215, Necromancer 179, Druid 173/208) reached 30 or more at the three FHR rates. Re-tag pass over the timing, movement and combat specs: the statements the lane/p50f check left [I] pending those floors (K3, M3 and the Open-questions bullets the request names), each [C] naming its run and scope; the Druid's throws (29 of 30), the player knockbacks (0), P1b-2/13/14/15 and the six offset-1 stamina-turn cases stay [I] or open with their counts. The run-to-walk turn at 0 stamina (81 events, 75 at offset 0, 6 at offset 1, [I]) goes into movement's Open questions with its counts; anim/0003 lines 700-702 ('not its turn to a walk') are the reverser's, so file a reverser entry if the finding needs the cross-reference. Recompute the touched specs' totals and the research-map rows.
