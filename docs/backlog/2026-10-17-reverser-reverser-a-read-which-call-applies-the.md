---
from: reverser
to: reverser
date: 2026-10-17
status: open
context:
  - ../findings/combat/0001-formulas.md#open-questions
resolution: ""
---

[2026-10-17] from reverser → reverser (combat follow-up, no harness): (a) read which call applies the prevent-heal state 52 (stat 117) between `COMBAT_ToHitRoll` and `COMBAT_DefenceRoll` in the melee path; (b) read the event-9 (kill) stat-event handler at `0x005C01D0`, which runs inside the delivery before `AD1` with *Fleshripper*/*Dracul's Grasp* (101 mismatches in the set-aside session, workspace scratch of `lane/h37r`), and model it in `tools/combat.py` if it draws. Context: [combat/0001 § Open questions](../findings/combat/0001-formulas.md#open-questions)
