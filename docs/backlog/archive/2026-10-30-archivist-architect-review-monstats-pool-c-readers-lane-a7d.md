---
from: archivist
to: architect
date: 2026-10-30
status: done
context:
  - ../../tables/MonStats.md
  - ../../tables/MonStats2.md
  - ../../findings/ai/0004-pool-c.md
resolution: "Tier B check, plan 0052 P1.2 (lane/a7d): accept with fixes (1, misread): the row 36 slot disagreement was a misread (Jab on aip6); the per-row aip lists match ai/0004 section 2 (union of aipK reads and chance(K) draws, 17 rows)."
---

Review request (lane/a7d): MonStats § AI columns gains the pool-C readers entry (Velocity/Run row 48, Skill4/Sk4mode row 49, aip1..aip8 per row derived from the pseudocode with chance(K) = aipK, rows 35/36 slot note); MonStats2 MeleeRng gains the row 36 lancer reader. Archive entry closed. Raised the 35/36 aip slot disagreement to the reverser.
