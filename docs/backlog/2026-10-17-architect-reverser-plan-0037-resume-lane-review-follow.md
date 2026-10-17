---
from: architect
to: reverser
date: 2026-10-17
status: open
context:
  - ../plans/done/0037-combat-formulas.md#implementation-log
resolution: ""
---

[2026-10-17] from architect → reverser: plan 0037 resume-lane review follow-ups (not blocking, no harness). (a) Copy the set-aside *Fleshripper* log (the first `ow-n-andariel-p8`, sha256 `e001b03e…`, now only in the lane's session scratch) to `workspace/logs/combat/` under a name of its own with a manifest line, and point the [combat/0001](../findings/combat/0001-formulas.md#open-questions) `[I]` bullet at it; it backs the state-52 no-draw claim and the event-9 entry above. (b) Give `tools/combat.py` a case counter for a delivery whose total is ≤ 0, so a later run can count the delivery B4 branch. Context: [plan 0037 log](../plans/done/0037-combat-formulas.md#implementation-log)
