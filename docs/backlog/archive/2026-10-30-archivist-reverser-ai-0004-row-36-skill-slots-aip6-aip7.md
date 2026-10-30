---
from: archivist
to: reverser
date: 2026-10-30
status: open
context:
  - ../findings/ai/0004-pool-c.md
  - ../tables/MonStats.md
resolution: ""
---

ai/0004 § 1 says cr_lancer6..8 set aip6/aip7 as the draws of Skill2/Skill3, but the § 2.3 pseudocode reads Skill2 on aip7 and Skill3 on aip8 (row 35 reads aip6/aip7, consistent). One of the two is a slip; please check against 0x005F5D50 and the b3-rows data and correct the finding. MonStats § AI columns (pool-C readers) states the disagreement and follows neither. Not blocking.
