---
from: reverser
to: reverser
date: 2026-10-17
status: done
context:
  - ../../findings/combat/0001-formulas.md#open-questions
resolution: "Both read in plan 0045 P1.3 (lane/p45h), [skills/0003 § 3](../../findings/skills/0003-handlers.md#3-the-stat-event-handlers): (a) COMBAT_ToHitRoll's success branch calls sub_0057D810_PreventHealHook, which applies state 52 with no draw; (b) 0x005C01D0 is stat-event handler 28 (heal after kill), no draw, so tools/combat.py needs no draw for it; the Fleshripper re-check stays with plan 0045 Phase 2 and the log copy with the plan 0037 follow-up entry. combat/0001's open questions carry dated notes."
---

[2026-10-17] from reverser → reverser (combat follow-up, no harness): (a) read which call applies the prevent-heal state 52 (stat 117) between `COMBAT_ToHitRoll` and `COMBAT_DefenceRoll` in the melee path; (b) read the event-9 (kill) stat-event handler at `0x005C01D0`, which runs inside the delivery before `AD1` with *Fleshripper*/*Dracul's Grasp* (101 mismatches in the set-aside session, workspace scratch of `lane/h37r`), and model it in `tools/combat.py` if it draws. Context: [combat/0001 § Open questions](../../findings/combat/0001-formulas.md#open-questions)

*2026-10-20 (architect, `lane/plans45`):* proposed home: plan 0045 Phase 1 (P1.3, handlers) reads both (a) state 52's call and (b) the event-9 handler; 0045·P2 re-checks the Fleshripper session (plan proposed, awaiting the owner).
