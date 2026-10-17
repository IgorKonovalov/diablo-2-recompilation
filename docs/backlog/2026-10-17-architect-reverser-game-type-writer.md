---
from: architect
to: reverser
date: 2026-10-17
status: done
context:
  - ../findings/items/0011-economy.md#open-questions
  - ../findings/monsters/0001-level-pool.md
resolution: "lane/rbs2 2026-10-17, [I]: one writer, GameCreate at 0x00530CFF, from the client's game-create message (type 0x67) byte built from g_ClientGameMode: 0 → 3, 6 → 1, 8 → 2, else 0; the network names of 6 and 8 stay [L]. [items/0011 § The writer of game+0x6A](../findings/items/0011-economy.md#the-writer-of-game0x6a-2026-10-17-lanerbs2)"
---

from the plan 0043 P1 review (2026-10-17): find the writer(s) of `game+0x6A` (the byte `PLAYER_DeathGoldLoss` tests against 3 at 0x0053587F) and name what each value means, so that the single-player death rule of items/0011 § 6 rests on the writer and not only on monsters/0001's logged value. Static, any 0039-style batch; not blocking plan 0043 P2.
