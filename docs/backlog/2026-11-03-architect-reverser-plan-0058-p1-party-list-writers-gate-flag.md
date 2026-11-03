---
from: architect
to: reverser
date: 2026-11-03
status: open
context:
  - ../plans/0058-party-and-player-count.md
  - ../findings/player/0002-party.md
resolution: ""
---

From the lane/r58a review (plan 0058 Phase 1); none blocks Phase 2, where the spec states each as not read. Static: (1) the writers of the party list at game +0x1D2C: what makes two players one party, and whether a list can hold nine (player/0002 § 2 and the cap's reach); (2) the unnamed caller at 0x005408CB of sub_005405A0_PartyForEachInLevel; (3) the meaning of the kill gate's flag, bit 26 of unit +0xC4, at its 9 writers (0x00541FB1, 0x0056D8A4, 0x0057449B, 0x005CB042, 0x005CB089, 0x005CB4B8, 0x005F7FF0, 0x005F9DE6, 0x005FD1DF), since it decides when a kill gives no experience. Live, optional, with the next two-client session and not a slot of its own: a partied credited player far from the victim (its mercenary kills beyond the bound) with the other member near it, which separates both corrections on the game's own logs; a dead killer with a living member in range; a player killing a player. Both [C]s stand without it (ruling in the plan 0058 log). tools/mp_check.py xpshare already counts apart pairs.
