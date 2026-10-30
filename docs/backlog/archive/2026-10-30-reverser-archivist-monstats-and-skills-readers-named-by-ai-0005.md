---
from: reverser
to: archivist
date: 2026-10-30
status: done
context:
  - ../../findings/ai/0005-pool-d.md
  - ../../tables/MonStats.md
  - ../../tables/Skills.md
resolution: "MonStats.md gains Readers named by the pool-D batch (aip1..aip8 by row, Velocity/Run for row 70, Skill2/4/6 modes for rows 73/74, the unread skills of rows 64/76/78/79); Skills.md aurastate and auratargetstate gain the row 73/74 readers [MonStats](../../tables/MonStats.md), [ai/0005](../../findings/ai/0005-pool-d.md)"
---

From [ai/0005](../../findings/ai/0005-pool-d.md) (plan 0052 P1.2 batch 4), readers to link in the table docs: MonStats aip1..aip8 per row as § 2 of the finding gives them (row 64's aip2 as both the approach distance and, by its low byte, the walk-stop; row 65's aip2 as the revive filter 0..3 and aip3 compared with a squared distance; row 66's aip1 the brood size and aip2 the delay with Idle(25*aip2); row 76's aip1 the spawn stock and aip2 the spawn interval in frames; row 74's aip3 a curse timer in frames); MonStats Velocity (+0x32) and Run (+0x34) read by sub_005FA380_AiFingerMage (the same Run*100/Velocity - 100 clamped 0..120 override parameter as the vampire and the zealot, § 2.7); MonStats Skill2/Sk2mode by sub_005FAB80_AiAbyssKnight, Skill4/Sk4mode and Skill6/Sk6mode by sub_005FAF00_AiOblivionKnight (§§ 2.10, 2.11); Skills aurastate (+0x080) read by sub_005FAB80_AiAbyssKnight (no self-cast of Skill2 while the unit has it) and Skills auratargetstate (+0x082) by sub_005FAF00_AiOblivionKnight (no Skill4 curse on a target that has it, admitted only when > 0). Rows 64 (SkeletonRaise), 76 (Nest) and 78/79 (Skill2) carry skills their think functions do not read (§ 1, § 2.16). All [I]. Not blocking.
