---
from: spec-writer
to: reverser
date: 2026-11-16
status: open
context:
  - ../plans/0066-simulation-inferred-claims-sweep.md
  - ../findings/anim/experiments.md
  - ../specs/monsters/stats.md
resolution: ""
---

Routed from item 5 of the closed entry [2026-11-15-reverser-spec-writer-plan-0066-s6a-corrections](archive/2026-11-15-reverser-spec-writer-plan-0066-s6a-corrections.md) (plan 0066 Phase 3, `lane/n66v`). monsters/stats § G's `fanatic` row reads "champion part; AddStat(67, clamp(2048 ÷ Velocity − 128, 10, 100))", but the two `fanatic` units logged at `Velocity` 4 carry stat 67 = 175 at neutral (75 + the clamp only), not 195 (75 + 20 + 100) (`check-part2.txt` `mon-stat67`, run:2026-10-30-anim-p3b, the S6b addendum). Please read `UModFanatic` (0x005A11F0): does its "champion part" exclude the champion's + 20 to stat 67, or do the logged units differ (another write after it)? The spec-writer then words monsters/stats § G to match. anim/timing J5 and anim/movement A3 now state only the logged 175.
