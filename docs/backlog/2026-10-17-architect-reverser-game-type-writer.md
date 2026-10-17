---
from: architect
to: reverser
date: 2026-10-17
status: open
context:
  - ../findings/items/0011-economy.md#open-questions
  - ../findings/monsters/0001-level-pool.md
resolution: ""
---

from the plan 0043 P1 review (2026-10-17): find the writer(s) of `game+0x6A` (the byte `PLAYER_DeathGoldLoss` tests against 3 at 0x0053587F) and name what each value means, so that the single-player death rule of items/0011 § 6 rests on the writer and not only on monsters/0001's logged value. Static, any 0039-style batch; not blocking plan 0043 P2.
