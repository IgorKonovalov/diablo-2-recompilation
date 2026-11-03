---
from: reverser
to: architect
date: 2026-11-03
status: open
context:
  - ../findings/anim/experiments.md
  - ../plans/0050-animation-frame-timing.md
resolution: ""
---

Review request: plan 0050 Phase 2 part 3 (lane/p50g), run:2026-10-30-anim-p3 plus run:2026-10-30-anim-p3b (record in docs/findings/anim/experiments.md). Closing check over 131 logs: 0 mismatches. The five short get-hit rates reached 30 or more (Amazon 179/215 at 40/33, Necromancer 179 at 32, Druid 173/208 at 35/32). Named short: Druid throws 29 of 30, player knockbacks 0 (Blood Raven never seen in three Hell sessions), run turned to a walk at 0 stamina 81 events (75 at offset 0, 6 at offset 1, an unexplained offset-1 case), P1b-2, P1b-14, P1b-15 not played, P1b-13 13 player slow windows. A spec-writer re-tag pass follows the review (K3, M3, open questions of the timing, movement and combat specs).
