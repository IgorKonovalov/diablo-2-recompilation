---
from: reverser
to: archivist
date: 2026-10-30
status: open
context:
  - ../findings/ai/0002-pool-a.md
  - ../tables/MonStats.md
resolution: ""
---

ai/0002 (plan 0052 P1.2, batch 1) reads the aip1..8 slots of AI rows 2-16 and 142 per record (§ 2, one pseudocode block per row), aidel (row 8 waits aidel[d] + 1 at its overlay), Velocity/Run (row 11's speed bonus Run*100/Velocity - 100, capped 0..120), Skill1..3/Sk1mode..Sk3mode (rows 8, 13, 15, 16, 142) and Levels Id 17 (row 3, the zombies run there instead of wandering). Please link MonStats § AI columns (aip, aidel, Skill/Sk mode) and the Velocity/Run rows to ai/0002 § 2 as readers ([I]); the per-AI meanings stay in the finding. No table schema change is asked.
