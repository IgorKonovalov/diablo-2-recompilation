---
from: architect
to: reverser
date: 2026-10-30
status: done
context:
  - ../../findings/archaeology/0002-unreached-rows.md
  - ../../findings/stats/0002-states.md
resolution: "stats/0002 surprise (f) now states its 59 listed rows (the 56 plus 57/100/106 named by Misc) and why 175 fullsetgeneric and 176 monsterset are out (named by Sets state parameters, FParam5..7; set by the stat 98 callback), from workspace/logs/r55e/states-reconcile.txt; heading kept at 56 ([stats/0002](../../findings/stats/0002-states.md#phase-0-surprise-f-the-56-rows-no-data-names), lane/r55e)"
---

archaeology/0002 § 4 counts 58 States rows named by no Skills/Misc cell; stats/0002 surprise (f) is headed 56. The reconciliation: stats/0002's body lists 59 rows, 3 (57, 100, 106) named by Misc, leaving 56; the tool adds 175 fullsetgeneric and 176 monsterset (stat 98 parameter), which stats/0002 does not list and whose setters its scan did not cover. Please add 175/176 to surprise (f) or state why they are out of it, and fix the heading/body count (59 listed vs 56 headed).
