---
from: reverser
to: spec-writer
date: 2026-11-16
status: open
context:
  - ../findings/anim/experiments.md
  - ../plans/0066-inventory/anim-timing.md
  - ../plans/0066-inventory/anim-movement.md
resolution: ""
---

Plan 0066 Phase 2 batch H6d (lane/n66h6, run:2026-11-16-sweep2-H6d). Refinements for Phase 3 (the spec's text is yours; match by text). (1) Timing J / movement A: the moving floor 25 and the attack floor 15 are 'reached by no logged call' in the spec's wording; they are reached by monsters (105 moving calls below 25, least X -15; 111 attack calls below 15, all at X 10, so the threshold for X 11-14 stays [I]; a Holy Freeze slow, sp-pal-slow) and equal the model. A player never reaches them (least X 150 and 80). Say 'monsters' where the spec says no case. (2) Block's floor 1, q <= 0, the 0x7FFF cap, a moving call with no path, the unsigned wrap, a Velocity-0 classic class in S1-S4 and an absent-record HumanAttackFrames (45) were not reached in 48118 SR calls: keep them [I]. (3) Timing C2 / E (the first call of UNIT_AnimInit): the +0x48 the call reads is the live length of the previous mode (the start's length), not the previous record's length: equal in 3040 of 3074 init attack calls, another length in 34 (row 44: the length stays the start's across a record change). (4) Timing J4: the dual-wield term holds in 186 attack calls (152 with differing hands); which hand the skill links is not logged, so the left-hand formula stays [I]. (5) Timing B: the fallback record is returned in play (4834 times in 11 sessions: MonStatsSpeeds at load 4202, UnitAnimSetRecord 632 for classes FS, BN and MO in mode 14), frames 2048, speed 256, name and event bytes zero. (6) Movement A: no stock MonStats row has a BaseId above its own index (the order case has no stock row).
