---
from: reverser
to: architect
date: 2026-11-16
status: done
context:
  - ../../plans/0066-simulation-inferred-claims-sweep.md
  - ../../findings/anim/experiments.md
resolution: "Tier B check: accept with fixes (9); merged to main 2026-11-16."
---

Tier B check of plan 0066 Phase 2 batch H6d (lane/n66h6): 19 rows, 11 sessions on slot 1, logger rev 7, checker tools/anim_h6d.py, 0 mismatches in 189882 checks. Judgment calls to check: (1) prediction 4 failed (floors reached by monsters) and the rows were raised on it; (2) rows 80/81/84/91/129 and movement 5/15 left not raised for want of a stock case, not forced; (3) timing 90's left-hand half kept [I] (the linked hand inferred from stat 68); (4) timing 44 raised in part (no monster mid-mode record change met); (5) timing 62 and movement 22/23 not attempted; (6) the first sp-bar-dw launch demoted to dev3 because the checker saw it before the kept batch.
