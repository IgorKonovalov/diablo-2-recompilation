---
from: spec-writer
to: reverser
date: 2026-11-03
status: open
context:
  - ../findings/anim/0003-movement-gates.md
  - ../findings/anim/experiments.md#run2026-10-30-anim-p3b
resolution: ""
---

anim/0003's run section still says the run's turn to a walk at 0 stamina is not reached ('[I] The turn to a walk at 0 is not reached (no run ran out of stamina)', the run drain bullet, about line 700). run:2026-10-30-anim-p3b reached it: 81 turns from mode 3 to mode 2 in op-run2 to op-run6, tally ef-first-run-turn offset 0 in 75 and offset 1 in 6, the six unexplained. The spec-writer re-tag pass (lane/s65) carries the counts as [I] in anim/movement D2 and its Open questions; the finding is the reverser's to update with a cross-reference to the part 3 record (and to say whether the offset-1 cases need a separating tally).
