---
from: architect
to: reverser
date: 2026-10-30
status: done
context:
  - ../../plans/README.md
  - ../../findings/ai/0001-machinery.md
resolution: "Answered 2026-10-30 (lane/rfix), [I], static scan tools/light_radius_scan.py (workspace/logs/rfix/light-radius-scan.txt): none found server-side. MonAiFindTarget and its four candidate functions call no stat getter; no getter call in the image takes stat 89 as an immediate id (1 418 calls, 215 with a register id unresolved); the item lightradius byte (+0x12F) has one reader, sub_0063EBD0_MonComponentLightRadius, called only from client code (0x0046096C, 0x004AE26C). The server's one visibility term is state 146 invis in AiHostileCandidate (0x005DC9CB), plus the AncientStatue think on itself (0x005EEAC0). [ai/0001 § 6](../../findings/ai/0001-machinery.md#6-target-search)"
---

Monster awareness residual (owner request of 2026-10-30, topic 5 of the planning batch; dropped as a plan because plan 0052 covers it: the target search `sub_005DD7F0_MonAiFindTarget` in ai/0001 § 6, the whole AI table including the town and NPC rows, and room activation in drlg/lifecycle). One question is left: does any server-side code read a unit's light radius (stat 89 `lightradius`, the item `lightradius` column at `+0x12F` of Weapons/Armor/Misc) or a visibility or stealth value when a monster searches for or keeps a target? Answer from the code (`[I]`) inside a plan 0052 catalogue batch or the next static slot: the readers of stat 89 server-side, and whether `MonAiFindTarget`'s distance test takes any light or visibility term. If none, say so in ai/0001 § 6 and close.
