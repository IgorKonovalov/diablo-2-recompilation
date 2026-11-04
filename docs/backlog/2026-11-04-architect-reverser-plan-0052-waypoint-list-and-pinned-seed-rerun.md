---
from: architect
to: reverser
date: 2026-11-04
status: open
context:
  - ../findings/ai/0017-phase2-second-run.md
  - ../findings/ai/experiments.md
resolution: ""
---

[2026-11-04] from architect → reverser: lane/p52b review (plan 0052 Phase 2). The Act IV waypoint click left the character in the town in 14 of 35 launches of run:2026-11-03-ai-3, 1 of 3 of run:2026-11-04-ai-3p and 4 of 7 development launches of the checkpoint: about 40 % of launches lost. This is a tool fault, not the stage-check entry (2026-11-03-architect-reverser-plan-0056-p4-stage-check-in-the-library): that gate decides whether a shared process may switch cases, and here the check caught every failure and the fresh rerun held. (1) Find why tools/d2pilot.py's wp gives up (the 8 s wait for p.menu_open() after one click at --wp-x, --wp-y, d2pilot.py line 732: is the character still walking, or the object not yet targetable after the town loads?) and fix it, with a retry that does not need a new process; name the cause in the record. (2) A case with a pinned map seed loses it on a rerun: harness_runner's launch number moved d-duriel from 3364 to 3365, where the route's positions no longer hold. A rerun of such a case must keep the seed. Done when: a kept batch shows the failure rate below 1 launch in 10 or the record names the cause that stops it, and a no-game test holds the seed on a rerun. The next plan 0052 lane run does it before its batch.
