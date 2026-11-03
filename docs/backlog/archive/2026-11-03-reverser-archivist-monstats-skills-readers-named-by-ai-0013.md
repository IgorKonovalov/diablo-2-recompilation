---
from: reverser
to: archivist
date: 2026-11-03
status: done
context:
  - ../../findings/ai/0013-batch12.md
resolution: "Linked in MonStats (interact, aip1..aip3 and Skill1 of state 13, Velocity and Run of state 11, new batch 12 reader block), Skills (auratargetstate), SuperUniques (+0x08 record 6) and MonAI (setters of the state rows); [MonStats](../../tables/MonStats.md#ai-columns-plan-0052-phase-0), [SuperUniques](../../tables/SuperUniques.md), [MonAI](../../tables/MonAI.md)"
---

Table readers of plan 0052 P1.2 batch 12 for the schema docs, none blocking. MonStats `interact` (`+0x0D` bit 1): the mask word 0x006CE26C tested at 0x005DDEDF (`AiNearestPlayerCb`) and 0x005E8063 (state 10/17's think). MonStats `aip1`, `aip2`, `aip3`: 0x005E5FD1, 0x005E5FBB and 0x005E5FFD, 0x005E5F97, state 13's think (The Countess's, `corruptrogue3`, not read for its other AI row 10 by this code). MonStats `Skill1` (`+0x170`): 0x005E5BCA, `AiPathSkillStep`. MonStats `Velocity`, `Run`: 0x005E81DA, 0x005E81E3, state 11. Skills `auratargetstate`: the state map 23, 27, 56 of `CurseSetAiState` (0x005C34DF–0x005C3503). SuperUniques `+0x08`: the case word 6 of `SuperUniqueSpawn` sets AI state 13 (0x005A4BF7, 0x005A4C1A). MonAI § The second table may add: state rows 2, 3, 8, 9, 14, 17 have no setter in the image, ai/0013 § 3, `[I]`.
