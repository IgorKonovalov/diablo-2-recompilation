---
from: architect
to: reverser
date: 2026-11-03
status: open
context:
  - ../plans/done/0058-party-and-player-count.md
  - ../findings/player/0002-party.md
resolution: ""
---

From the lane/r58a review (plan 0058 Phase 1); none blocks Phase 2, where the spec states each as not read. Static: (1) the writers of the party list at game +0x1D2C: what makes two players one party, and whether a list can hold nine (player/0002 § 2 and the cap's reach); (2) the unnamed caller at 0x005408CB of sub_005405A0_PartyForEachInLevel; (3) the meaning of the kill gate's flag, bit 26 of unit +0xC4, at its 9 writers (0x00541FB1, 0x0056D8A4, 0x0057449B, 0x005CB042, 0x005CB089, 0x005CB4B8, 0x005F7FF0, 0x005F9DE6, 0x005FD1DF), since it decides when a kill gives no experience. Live, optional, with the next two-client session and not a slot of its own: a partied credited player far from the victim (its mercenary kills beyond the bound) with the other member near it, which separates both corrections on the game's own logs; a dead killer with a living member in range; a player killing a player. Both [C]s stand without it (ruling in the plan 0058 log). tools/mp_check.py xpshare already counts apart pairs.

*2026-11-10 (plan 0063 Phase 2a, `lane/n63r`):* the static part is answered in
[player/0002 § 10](../findings/player/0002-party.md#10-plan-0063-phase-2a-the-list-writers-the-fourth-caller-and-bit-26-lanen63r-2026-11-10):
(1) a party is made or joined only by the accept action (8) after an invite (6), in `sub_005A5A30_PartyActAccept`.
`sub_00540320_PartyAddMember` has no cap, but a game admits at most 8 clients (game `+0x8C`, 0x00539A4E,
0x0053F051), so a list cannot hold nine. (2) 0x005408CB is in `sub_00540890_PartyLevelSumInLevel`, which the image
never references. (3) Bit 26 has 9 sets, 0 clears and 2 reads. It marks a monster whose death gives no experience
(released and replaced pets, eggs, spawned minions), and the inactive-room save carries it; no writer sets it on a
player. **Live remainder (optional, unchanged):** the two-client cases (a far credited player with a near member, a
dead killer, a player killing a player). The entry stays open for them.
