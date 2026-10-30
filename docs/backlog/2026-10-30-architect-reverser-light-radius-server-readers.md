---
from: architect
to: reverser
date: 2026-10-30
status: open
context:
  - ../plans/README.md
  - ../findings/ai/0001-machinery.md
resolution: ""
---

Monster awareness residual (owner request of 2026-10-30, topic 5 of the planning batch; dropped as a plan because plan 0052 covers it: the target search `sub_005DD7F0_MonAiFindTarget` in ai/0001 § 6, the whole AI table including the town and NPC rows, and room activation in drlg/lifecycle). One question is left: does any server-side code read a unit's light radius (stat 89 `lightradius`, the item `lightradius` column at `+0x12F` of Weapons/Armor/Misc) or a visibility or stealth value when a monster searches for or keeps a target? Answer from the code (`[I]`) inside a plan 0052 catalogue batch or the next static slot: the readers of stat 89 server-side, and whether `MonAiFindTarget`'s distance test takes any light or visibility term. If none, say so in ai/0001 § 6 and close.
