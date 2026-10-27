---
from: architect
to: reverser
date: 2026-10-17
status: done
context:
  - ../../plans/done/0037-combat-formulas.md#implementation-log
resolution: "(a) the Fleshripper session re-run and kept: workspace/logs/combat/p47h-owf-n-andariel-p8.log (a411b34d…, in p47h-manifest.txt; 57 mismatches, all the event-9 handler, plan 0045 Phase 2); (b) tools/combat.py counts deliveries with a total <= 0 (run:2026-10-20-shortfalls: 488 below 0 and 113 at 0 on the player). [plan 0047 log](../../plans/done/0047-simulation-shortfalls.md#implementation-log)"
---

[2026-10-17] from architect → reverser: plan 0037 resume-lane review follow-ups (not blocking, no harness). (a) Copy the set-aside *Fleshripper* log (the first `ow-n-andariel-p8`, sha256 `e001b03e…`, now only in the lane's session scratch) to `workspace/logs/combat/` under a name of its own with a manifest line, and point the [combat/0001](../../findings/combat/0001-formulas.md#open-questions) `[I]` bullet at it; it backs the state-52 no-draw claim and the event-9 entry above. (b) Give `tools/combat.py` a case counter for a delivery whose total is ≤ 0, so a later run can count the delivery B4 branch. Context: [plan 0037 log](../../plans/done/0037-combat-formulas.md#implementation-log)

*2026-10-20 (architect, `lane/plans45`):* proposed home: plan 0047 Phase 1 takes (a) the log copy, Phase 2 (b) the ≤ 0 counter (plan proposed, awaiting the owner).

*2026-10-20 (reverser, `lane/p47r`, plan 0047 Phase 1):* (a) cannot be done as asked: the log is gone with the
lane's session scratch, and a scan of every harness log on the machine found none with sha256 `e001b03e…` or save
`5f440622…` (`workspace/logs/combat/p47r-fleshripper-search.txt`). Commit `5871b00`'s `CombatOW` recipe still builds
`5f440622…` byte for byte, so the session is staged again as `owf-n-andariel-p8` (`tools/combat_sessions.py`, recipe
`tools/d2s_recipes/combatowf.json`, seed 3712) for plan 0047 Phase 2, and [combat/0001](../../findings/combat/0001-formulas.md#open-questions)
says so. (b) stays with Phase 2. Entry left open.
