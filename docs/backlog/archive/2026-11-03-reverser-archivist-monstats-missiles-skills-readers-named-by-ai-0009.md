---
from: reverser
to: archivist
date: 2026-11-03
status: done
context:
  - ../../findings/ai/0009-batch8.md
resolution: "MonStats MissS1, aip slots of row 114, count guards; Missiles Range; Skills Param5 linked from ai/0009 [tables/MonStats.md](../../tables/MonStats.md)"
---

Link the readers found by [ai/0009](../../findings/ai/0009-batch8.md) from the table docs: MonStats MissS1 (+0x03E: row 85 HighPriest commands S1 only when it is > 0 and the target is nearer than that missile's Range - 2; § 2.3, [I]); Missiles Range (+0x096: the same bound, read through MissileRec; § 2.3, [I]); Skills Param5 (+0x158: row 115 SiegeBeast stomps with Skill1 only inside dist < Param5 of its Skill1; § 2.12, [I]); MonStats aip slots per row as § 2 reads them (row 114 reads aip1..aip7 and not aip8, which settles the reanimatedhorde6 slot disagreement of MonStats § AI columns for that row; § 1, [I]); the MonStats count guards of rows 82, 83 and the imp callback (classes 96, 334, 492; [C] for rows 82 and 83 by run:2026-11-03-ai-cat-emu-8, § 2.1, § 2.2). No column meaning changes; links only.
