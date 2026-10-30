---
from: architect
to: reverser
date: 2026-10-30
status: open
context:
  - ../findings/archaeology/0002-unreached-rows.md
  - ../findings/stats/0002-states.md
resolution: ""
---

archaeology/0002 § 4 counts 58 States rows named by no Skills/Misc cell; stats/0002 surprise (f) is headed 56. The reconciliation: stats/0002's body lists 59 rows, 3 (57, 100, 106) named by Misc, leaving 56; the tool adds 175 fullsetgeneric and 176 monsterset (stat 98 parameter), which stats/0002 does not list and whose setters its scan did not cover. Please add 175/176 to surprise (f) or state why they are out of it, and fix the heading/body count (59 listed vs 56 headed).
